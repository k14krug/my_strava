"""One bounded, sequential Strava-export import workflow.

The ZIP is never extracted. Only CSV and explicitly referenced activity bytes
are read/preserved. Reports use row indexes and fixed categories, avoiding
private paths, activity titles or parser exception contents.
"""
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import zipfile

from .errors import RideWorksError


class AssociationError(RideWorksError):
    pass


class ExportError(RideWorksError):
    pass


TEXT_FIELDS = {'Activity ID', 'Activity Name', 'Activity Type', 'Sport Type', 'Activity Date', 'Filename'}
NUMERIC_FIELDS = {
    'Elapsed Time': 'source_unspecified', 'Moving Time': 'source_unspecified',
    'Distance': 'source_unspecified', 'Elevation Gain': 'source_unspecified',
    'Average Watts': 'W', 'Max Watts': 'W', 'Average Power': 'W',
    'Weighted Average Power': 'W', 'Power Count': 'count',
    'Average Heart Rate': 'bpm', 'Max Heart Rate': 'bpm',
    'Average Cadence': 'rpm', 'Max Cadence': 'rpm',
}


def safe_member(name):
    # POSIX archive/member semantics, including on a non-POSIX input producer.
    if not name or '\\' in name or '\x00' in name or re.match(r'^[A-Za-z]:', name):
        raise ExportError('Unsafe export member/reference')
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ('', '.', '..') for part in name.split('/')):
        raise ExportError('Unsafe export member/reference')
    return path


class ExportInput:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.zip = None

    def __enter__(self):
        try:
            if self.path.is_dir():
                self.root = self.path.resolve()
                csvs = list(self.root.rglob('activities.csv'))
                if len(csvs) != 1:
                    raise ExportError('Expected exactly one activities.csv')
                self.csv_member = csvs[0].relative_to(self.root).as_posix()
                self._disk_path(self.csv_member)
            else:
                self.zip = zipfile.ZipFile(self.path)
                self.members = {}
                for info in self.zip.infolist():
                    name = info.filename.rstrip('/') if info.is_dir() else info.filename
                    safe_member(name)
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise ExportError('Symlink ZIP members are unsupported')
                    if name in self.members:
                        raise ExportError('Duplicate/ambiguous ZIP member')
                    self.members[name] = info
                csvs = [name for name, info in self.members.items()
                        if not info.is_dir() and PurePosixPath(name).name == 'activities.csv']
                if len(csvs) != 1:
                    raise ExportError('Expected exactly one activities.csv')
                self.csv_member = csvs[0]
            self.prefix = PurePosixPath(self.csv_member).parent
            return self
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            if self.zip is not None:
                self.zip.close()
            raise ExportError('Unreadable/invalid Strava export container') from exc
        except BaseException:
            if self.zip is not None:
                self.zip.close()
            raise

    def __exit__(self, *_):
        if self.zip is not None:
            self.zip.close()

    def _disk_path(self, member):
        relative = safe_member(member)
        path = self.root / str(relative)
        for candidate in (path, *path.parents):
            if candidate == self.root:
                break
            if candidate.is_symlink():
                raise ExportError('Symlink export members are unsupported')
        if not path.resolve().is_relative_to(self.root):
            raise ExportError('Export reference escapes input root')
        return path

    def validate_reference(self, reference):
        member = (self.prefix / safe_member(reference)).as_posix()
        if self.zip is None:
            self._disk_path(member)
        return member

    def read(self, member):
        try:
            if self.zip is not None:
                return self.zip.read(member)
            return self._disk_path(member).read_bytes()
        except (OSError, KeyError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as exc:
            raise ExportError('Export member missing/unreadable') from exc


def _date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
    except ValueError:
        pass
    for fmt in ('%b %d, %Y, %I:%M:%S %p', '%B %d, %Y, %I:%M:%S %p'):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            pass
    return None


def read_rows(payload):
    try:
        reader = csv.reader(io.StringIO(payload.decode('utf-8-sig'), newline=''), strict=True)
        columns = next(reader)
        positions = {}
        for field in TEXT_FIELDS:
            matches = [i for i, col in enumerate(columns) if col.strip() == field]
            if len(matches) > 1:
                raise ExportError('Ambiguous CSV identity/reference columns')
            if matches:
                positions[field] = matches[0]
        if not {'Activity ID', 'Filename'} <= positions.keys():
            raise ExportError('Required Activity ID/Filename columns are unavailable')
        rows, ids, references = [], set(), set()
        for row_index, values in enumerate(reader, 1):
            if len(values) != len(columns):
                raise ExportError('Malformed-width CSV row')
            def field(name):
                if name not in positions:
                    return None
                value = values[positions[name]]
                return value if value.strip() else None
            external_id = (field('Activity ID') or '').strip()
            if not re.fullmatch(r'[0-9]+', external_id) or external_id in ids:
                raise ExportError('Missing/invalid/duplicate Strava activity ID')
            ids.add(external_id)
            filename = field('Filename')
            if filename:
                safe_member(filename)
                if filename in references:
                    raise ExportError('Ambiguous CSV file relationship')
                references.add(filename)
            structured = []
            for index, column in enumerate(columns):
                if column.strip() not in NUMERIC_FIELDS:
                    continue
                raw = values[index]
                numeric = None
                status = 'missing' if not raw.strip() else 'present'
                if status == 'present':
                    try:
                        numeric = float(raw)
                        if not math.isfinite(numeric):
                            raise ValueError
                    except ValueError:
                        status, numeric = 'unparsed', None
                structured.append(dict(column=column, column_index=index, raw_value=raw,
                                       value=numeric, status=status, unit=NUMERIC_FIELDS[column.strip()], origin='source'))
            text_evidence = [dict(column=column, column_index=i, raw_value=values[i])
                             for i, column in enumerate(columns) if column.strip() in TEXT_FIELDS]
            date_text = field('Activity Date')
            evidence = dict(fields=structured, identity_fields=text_evidence,
                            date_parsed=_date(date_text),
                            date_timezone='explicit_offset' if _date(date_text) and datetime.fromisoformat(_date(date_text)).tzinfo else 'unknown',
                            numeric_policy='Repeated columns retained by position; unspecified source units are not inferred')
            digest = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
            rows.append(dict(row_index=row_index, external_id=external_id, title=field('Activity Name'),
                             activity_type=field('Activity Type'), sport_type=field('Sport Type'),
                             date_text=date_text, filename=filename, row_sha256=digest, evidence=evidence))
        return rows
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise ExportError('Invalid UTF-8 activities.csv') from exc


def import_export(store, path):
    with ExportInput(path) as export:
        payload = export.read(export.csv_member)
        rows = read_rows(payload)
        # Validate all path/identity relationships before any durable import.
        for row in rows:
            if row['filename']:
                row['member'] = export.validate_reference(row['filename'])
        snapshot = store.preserve_export_snapshot(payload)
        # Report local Activities left without an established export identity.
        # Do not inspect time/name/distance to guess which row should absorb them.
        preexisting_unassociated = {r[0] for r in store.connection.execute('''
            SELECT activity_id FROM activities WHERE NOT EXISTS (
                SELECT 1 FROM strava_export_sources s WHERE s.activity_id = activities.activity_id)
        ''')}
        report = dict(csv_rows_seen=len(rows), activities_created=0, existing_activities_reused=0,
                      existing_activities_enriched=0, csv_sources_created=0, csv_sources_reused=0,
                      csv_only_activities=sum(not row['filename'] for row in rows),
                      referenced_artifacts_attempted=0, artifacts_imported=0, artifacts_reused=0,
                      format_counts={}, failures=[], unresolved_associations=[])
        formats = Counter()
        for row in rows:
            artifact, artifact_sha, file_failure = None, None, None
            if row['filename']:
                report['referenced_artifacts_attempted'] += 1
                try:
                    artifact = export.read(row['member'])
                    artifact_sha = hashlib.sha256(artifact).hexdigest()
                except ExportError:
                    file_failure = 'artifact_unreadable'
            try:
                attached = store.attach_export_row(snapshot, row['row_index'], row, artifact_sha)
            except AssociationError:
                report['unresolved_associations'].append(dict(row_index=row['row_index'], category='conflicting_established_identities'))
                continue
            except (RideWorksError, sqlite3.Error, OSError):
                report['failures'].append(dict(row_index=row['row_index'], category='csv_source_persistence_failed'))
                continue
            report['activities_created' if attached['activity_created'] else 'existing_activities_reused'] += 1
            report['csv_sources_created' if attached['csv_source_created'] else 'csv_sources_reused'] += 1
            enriched = not attached['activity_created'] and attached['csv_source_created']
            if artifact is not None:
                try:
                    result = store.import_file(row['filename'], activity_id=attached['activity_id'],
                                               association_basis='explicit_strava_csv_file_reference', artifact_bytes=artifact)
                    report['artifacts_imported' if result['status'] == 'imported' else 'artifacts_reused'] += 1
                    enriched |= not attached['activity_created'] and result['status'] == 'imported'
                    source = store.connection.execute('SELECT content_format, packaging FROM sources WHERE source_id = ?',
                                                      (result['source_id'],)).fetchone()
                    label = source['content_format'] + ('.GZ' if source['packaging'] == 'gzip' else '')
                    formats[label] += 1
                except (RideWorksError, OSError, EOFError, sqlite3.Error):
                    file_failure = 'artifact_parse_or_persistence_failed'
            if enriched:
                report['existing_activities_enriched'] += 1
            if file_failure:
                report['failures'].append(dict(row_index=row['row_index'], category=file_failure))
        report['format_counts'] = dict(sorted(formats.items()))
        for activity_id in sorted(preexisting_unassociated):
            if store.connection.execute('SELECT 1 FROM strava_export_sources WHERE activity_id = ?', (activity_id,)).fetchone() is None:
                report['unresolved_associations'].append(dict(activity_id=activity_id,
                    category='preexisting_activity_without_established_export_relationship'))
        report['status'] = 'completed_with_failures' if report['failures'] or report['unresolved_associations'] else 'completed'
        return report
