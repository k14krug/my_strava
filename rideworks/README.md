# RideWorks local FIT evidence

P1-01 uses Python 3.10+, standard-library SQLite, and `fitdecode==0.11.0`.
It runs independently of the retired Strava application and its dependencies.
From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m rideworks import-fit /path/to/activity.fit.gz
.venv/bin/python -m rideworks inspect <activity-id>
.venv/bin/python -m rideworks reextract <source-id>
```

The installed `rideworks` command provides the same interface. Place the optional
`--data-dir /path/to/private-data` before the subcommand. Directory precedence is
explicit argument, `RIDEWORKS_DATA_DIR`, then `~/.rideworks`. Relative explicit
paths resolve at invocation; the default is independent of the working directory.
Originals and the SQLite database are private runtime data; keep them out of Git.

A successful import returns independently generated Activity and Source UUIDs
and the current extraction UUID. Reimporting identical received bytes verifies
the established original and returns those same identities. Different bytes,
including different gzip packaging, create a separate Activity in this phase.
Filename suffixes do not establish packaging or FIT validity. Original basenames
are retained for inspection; external paths are not persisted.

`Store(data_dir)` is a context manager. `import_fit(path)` and
`reextract(source_id)` return identity/status dictionaries. `get_activity(id)`
returns `activity` metadata and a `sources` list; `get_source(id)` returns one
Source snapshot containing `source`, `extraction`, `summary`, `records`, `laps`,
`events`, and `availability`. These methods use a consistent database read
transaction. `inspect(id)` omits records and detailed lap/event rows.

The physical tables have typed columns, with each normalized row linked to its
extraction and thus to its Source. Activity contains identity and creation time
only. Multiple Sources can reference an Activity; association/reconciliation
of different artifacts is deferred. Source owns one current extraction. A
successful re-extraction replaces that extraction transactionally and changes
its UUID, allowing later calculations to detect stale inputs. Old extraction
snapshots are not retained in P1-01.

Records preserve `record_index` (zero-based record ordinal) and `source_order`
(zero-based decoder frame ordinal, including headers and definitions). Retrieve
in record order, retaining duplicates, backward times, gaps and nulls. Timestamps
are ISO 8601 UTC strings; missing timestamps are null. Device-relative timestamps
are rejected instead of guessed into calendar time. Source summary units are
seconds, metres, watts, bpm and rpm as specified by `SUMMARY_UNITS`.
Elapsed and timer time remain separate. The decoder's default processor supplies
UTC date-time decoding and FIT source units; the presentation-unit processor is
not used. See the upstream [processor source](https://github.com/polyvertex/fitdecode/blob/master/fitdecode/processors.py).

Power/HR availability includes total, present and missing counts, with statuses
`present`, `present_with_missing` or `observed_absent`. Origin is independently
`unknown`; field presence does not prove measurement. Other record signals are
not extracted, and remain recoverable from the original. No application analysis
metrics are calculated here.

Import copies received bytes to managed staging, hashes and parses that copy,
and places exact bytes under `originals/<sha256>.fit[.gz]` using exclusive file
creation. Files and directory entries are synchronized before the database
transaction commits. Mutations serialize with a SQLite write transaction.
Failed imports roll back all metadata and safely remove newly created
unreferenced originals. A crash may leave an unreferenced original/staging file;
an identical original is reused only after integrity verification. Established
originals are never silently overwritten or repaired. Re-extraction verifies
stored integrity before decoding and leaves the prior current extraction intact
on decoder or database failure.

Only one FIT file with one activity session is supported. Chained FIT files,
multiple sessions, non-activity file types, malformed gzip/FIT, and invalid CRCs
fail clearly. Exact originals enable later extraction of fields omitted here.

Verification:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/verify_rideworks_import.py --input "$P1_01_INPUT" --work-dir /tmp
```

Set `P1_01_INPUT` to the local-only representative `21538875902.fit.gz`. The
acceptance utility uses and removes a disposable copy and disposable store,
runs CLI commands from a different working directory, and emits only compact
facts. It never modifies the supplied file. Run with assertions enabled.
