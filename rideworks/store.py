"""SQLite source evidence and immutable originals for the bounded P1-01 slice."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
from uuid import uuid4

from .errors import IntegrityError, RideWorksError
from .fit import MAPPING_VERSION, PARSER_VERSION, decode_fit, packaging_for

SCHEMA = """
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS activities (
    activity_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    activity_id TEXT NOT NULL REFERENCES activities(activity_id),
    kind TEXT NOT NULL,
    association_basis TEXT NOT NULL,
    original_basename TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    packaging TEXT NOT NULL CHECK(packaging IN ('plain', 'gzip')),
    content_format TEXT NOT NULL,
    stored_path TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sources_activity ON sources(activity_id);
CREATE TABLE IF NOT EXISTS extractions (
    extraction_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE REFERENCES sources(source_id),
    parser_name TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    mapping_version TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    power_present INTEGER NOT NULL,
    heart_rate_present INTEGER NOT NULL,
    power_origin TEXT NOT NULL,
    heart_rate_origin TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    extraction_id TEXT PRIMARY KEY REFERENCES extractions(extraction_id) ON DELETE CASCADE,
    start_time TEXT,
    timestamp TEXT,
    sport TEXT,
    sub_sport TEXT,
    total_elapsed_time REAL,
    total_timer_time REAL,
    total_distance REAL,
    total_ascent INTEGER,
    avg_power INTEGER,
    max_power INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    avg_cadence INTEGER
);
CREATE TABLE IF NOT EXISTS records (
    extraction_id TEXT NOT NULL REFERENCES extractions(extraction_id) ON DELETE CASCADE,
    record_index INTEGER NOT NULL,
    source_order INTEGER NOT NULL,
    timestamp TEXT,
    power INTEGER,
    heart_rate INTEGER,
    PRIMARY KEY(extraction_id, record_index)
);
CREATE TABLE IF NOT EXISTS laps (
    extraction_id TEXT NOT NULL REFERENCES extractions(extraction_id) ON DELETE CASCADE,
    source_order INTEGER NOT NULL,
    start_time TEXT,
    timestamp TEXT,
    total_elapsed_time REAL,
    total_timer_time REAL,
    PRIMARY KEY(extraction_id, source_order)
);
CREATE TABLE IF NOT EXISTS events (
    extraction_id TEXT NOT NULL REFERENCES extractions(extraction_id) ON DELETE CASCADE,
    source_order INTEGER NOT NULL,
    timestamp TEXT,
    event TEXT,
    event_type TEXT,
    timer_trigger TEXT,
    PRIMARY KEY(extraction_id, source_order)
);
PRAGMA user_version = 1;
COMMIT;
"""

SUMMARY_UNITS = {
    "total_elapsed_time": "s", "total_timer_time": "s", "total_distance": "m",
    "total_ascent": "m", "avg_power": "W", "max_power": "W",
    "avg_heart_rate": "bpm", "max_heart_rate": "bpm", "avg_cadence": "rpm",
}


def resolve_data_dir(data_dir=None) -> Path:
    """Resolve once; default does not depend on the working directory."""
    selected = data_dir if data_dir is not None else os.environ.get("RIDEWORKS_DATA_DIR", "~/.rideworks")
    return Path(selected).expanduser().resolve()


def _now():
    return datetime.now(timezone.utc).isoformat()


def artifact_integrity(path: Path) -> tuple[str, int]:
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Store:
    def __init__(self, data_dir=None):
        self.data_dir = resolve_data_dir(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.originals = self.data_dir / "originals"
        self.originals.mkdir(exist_ok=True, mode=0o700)
        self.staging = self.data_dir / ".staging"
        self.staging.mkdir(exist_ok=True, mode=0o700)
        self.connection = sqlite3.connect(self.data_dir / "rideworks.sqlite3", isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA synchronous = FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.close()
            raise RideWorksError(f"Unsupported RideWorks schema version: {version}")
        if version == 0:
            self.connection.executescript(SCHEMA)
        _sync_directory(self.data_dir)

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def _transaction(self, *, write=False):
        # Serialize import/re-extraction and file placement across store instances.
        self.connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def _verify(self, source):
        path = self.data_dir / source["stored_path"]
        try:
            actual = artifact_integrity(path)
        except OSError as exc:
            raise IntegrityError("Established original artifact is missing or unreadable") from exc
        if actual != (source["sha256"], source["byte_size"]):
            raise IntegrityError("Established original artifact hash/size mismatch")
        return path

    def _persist_extraction(self, source_id, digest, parsed):
        extraction_id = str(uuid4())
        count = len(parsed.records)
        power = sum(r.power is not None for r in parsed.records)
        hr = sum(r.heart_rate is not None for r in parsed.records)
        self.connection.execute(
            "INSERT INTO extractions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (extraction_id, source_id, "fitdecode", PARSER_VERSION, MAPPING_VERSION,
             _now(), digest, count, power, hr, "unknown", "unknown"),
        )
        self._insert_rows("sessions", extraction_id, [parsed.session])
        self._insert_rows("records", extraction_id, parsed.records)
        self._insert_rows("laps", extraction_id, parsed.laps)
        self._insert_rows("events", extraction_id, parsed.events)
        return extraction_id

    def _insert_rows(self, table, extraction_id, rows):
        if not rows:
            return
        # table/column names come exclusively from the internal typed classes.
        columns = list(asdict(rows[0]))
        names = ", ".join(["extraction_id", *columns])
        placeholders = ", ".join("?" for _ in range(len(columns) + 1))
        self.connection.executemany(
            f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
            [(extraction_id, *asdict(row).values()) for row in rows],
        )

    def import_fit(self, input_path) -> dict:
        input_path = Path(input_path)
        staged = None
        created_original = None
        try:
            with self._transaction(write=True):
                with tempfile.NamedTemporaryFile(dir=self.staging, delete=False) as target:
                    staged = Path(target.name)
                    digest, size = hashlib.sha256(), 0
                    with input_path.open("rb") as supplied:
                        for block in iter(lambda: supplied.read(1024 * 1024), b""):
                            target.write(block)
                            digest.update(block)
                            size += len(block)
                    target.flush()
                    os.fsync(target.fileno())
                digest = digest.hexdigest()
                existing = self.connection.execute(
                    "SELECT * FROM sources WHERE sha256 = ?", (digest,),
                ).fetchone()
                if existing is not None:
                    self._verify(existing)
                    extraction = self.connection.execute(
                        "SELECT extraction_id FROM extractions WHERE source_id = ?",
                        (existing["source_id"],),
                    ).fetchone()
                    if extraction is None:
                        raise IntegrityError("Established Source has no current extraction")
                    return self._result("already_imported", existing["activity_id"],
                                        existing["source_id"], extraction[0])
                packaging = packaging_for(staged)
                parsed = decode_fit(staged, packaging)
                extension = "fit.gz" if packaging == "gzip" else "fit"
                relative = f"originals/{digest}.{extension}"
                destination = self.data_dir / relative
                try:
                    # Exclusive creation; never replace an established original.
                    os.link(staged, destination)
                    created_original = destination
                    _sync_directory(self.originals)
                except FileExistsError:
                    # A crash may have left an unreferenced original. Reuse only
                    # identical verified bytes; never silently overwrite it.
                    if artifact_integrity(destination) != (digest, size):
                        raise IntegrityError("Existing original path has conflicting bytes")
                if artifact_integrity(destination) != (digest, size):
                    raise IntegrityError("Stored original failed integrity verification")
                activity_id, source_id, created = str(uuid4()), str(uuid4()), _now()
                self.connection.execute("INSERT INTO activities VALUES (?, ?)", (activity_id, created))
                self.connection.execute(
                    "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (source_id, activity_id, "file_fit", "direct_import", input_path.name,
                     size, digest, packaging, "FIT", relative, created),
                )
                extraction_id = self._persist_extraction(source_id, digest, parsed)
                result = self._result("imported", activity_id, source_id, extraction_id)
            return result
        except BaseException:
            if created_original is not None:
                # Rollback has occurred. Reacquire the write lock before checking
                # references so another process cannot establish a Source here.
                with self._transaction(write=True):
                    referenced = self.connection.execute(
                        "SELECT 1 FROM sources WHERE stored_path = ?", (relative,),
                    ).fetchone()
                    if referenced is None:
                        created_original.unlink(missing_ok=True)
                        _sync_directory(self.originals)
            raise
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)

    def reextract(self, source_id) -> dict:
        with self._transaction(write=True):
            source = self.connection.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
            if source is None:
                raise RideWorksError("Source not found")
            path = self._verify(source)
            parsed = decode_fit(path, source["packaging"])
            self.connection.execute("DELETE FROM extractions WHERE source_id = ?", (source_id,))
            extraction_id = self._persist_extraction(source_id, source["sha256"], parsed)
            return self._result("reextracted", source["activity_id"], source_id, extraction_id)

    def _result(self, status, activity_id, source_id, extraction_id):
        return dict(status=status, activity_id=activity_id, source_id=source_id,
                    extraction_id=extraction_id, data_dir=str(self.data_dir))

    def _source_evidence(self, source):
        extraction = self.connection.execute(
            "SELECT * FROM extractions WHERE source_id = ?", (source["source_id"],),
        ).fetchone()
        if extraction is None:
            raise IntegrityError("Source has no current extraction")
        key = extraction["extraction_id"]
        summary = dict(self.connection.execute("SELECT * FROM sessions WHERE extraction_id = ?", (key,)).fetchone())
        availability = {}
        for signal in ("power", "heart_rate"):
            present, total = extraction[f"{signal}_present"], extraction["record_count"]
            availability[signal] = dict(
                status="observed_absent" if present == 0 else "present" if present == total else "present_with_missing",
                total=total, present=present, missing=total - present,
                origin=extraction[f"{signal}_origin"],
            )
        evidence = dict(source=dict(source), extraction=dict(extraction), summary=summary,
                        availability=availability)
        for table, order in (("records", "record_index"), ("laps", "source_order"), ("events", "source_order")):
            evidence[table] = [dict(row) for row in self.connection.execute(
                f"SELECT * FROM {table} WHERE extraction_id = ? ORDER BY {order}", (key,),
            )]
        return evidence

    def get_activity(self, activity_id) -> dict:
        """Consistent snapshot including every Source's current typed evidence."""
        with self._transaction():
            activity = self.connection.execute("SELECT * FROM activities WHERE activity_id = ?", (activity_id,)).fetchone()
            if activity is None:
                raise RideWorksError("Activity not found")
            sources = self.connection.execute(
                "SELECT * FROM sources WHERE activity_id = ? ORDER BY imported_at, source_id", (activity_id,),
            ).fetchall()
            return dict(activity=dict(activity), sources=[self._source_evidence(s) for s in sources])

    def list_activities(self) -> list[dict]:
        """List only activities with one current Phase 1 FIT Source/session.

        No source ranking or new evidence-selection policy. Ambiguous activities
        are omitted rather than choosing among multiple FIT Sources.
        """
        with self._transaction():
            return [dict(row) for row in self.connection.execute("""
                SELECT a.activity_id, s.start_time, s.sport, s.sub_sport,
                       s.total_distance, s.total_elapsed_time
                FROM activities a
                JOIN sources f ON f.activity_id = a.activity_id
                JOIN extractions e ON e.source_id = f.source_id
                JOIN sessions s ON s.extraction_id = e.extraction_id
                WHERE f.kind = 'file_fit' AND f.content_format = 'FIT'
                  AND (SELECT count(*) FROM sources c
                       WHERE c.activity_id = a.activity_id
                       AND c.kind = 'file_fit' AND c.content_format = 'FIT') = 1
                ORDER BY s.start_time DESC, a.activity_id
            """)]

    def get_source(self, source_id) -> dict:
        with self._transaction():
            source = self.connection.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
            if source is None:
                raise RideWorksError("Source not found")
            return self._source_evidence(source)

    def inspect(self, activity_id) -> dict:
        snapshot = self.get_activity(activity_id)
        compact_sources = []
        for evidence in snapshot["sources"]:
            compact = {k: evidence[k] for k in ("source", "extraction", "summary", "availability")}
            compact["lap_count"] = len(evidence["laps"])
            compact["event_count"] = len(evidence["events"])
            compact_sources.append(compact)
        return dict(activity=snapshot["activity"], sources=compact_sources,
                    summary_units=SUMMARY_UNITS, timestamp_timezone="UTC")
