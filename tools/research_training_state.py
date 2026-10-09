#!/usr/bin/env python3
"""P4-01 research only. Read a private store copy; emit private evidence + safe census.

No production writes, network access, FTP inference or unknown-to-zero substitution.
The output directory contains PRIVATE data and must never be committed wholesale.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

import fitdecode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store
from rideworks.history import presentation
from rideworks.performance import performance_history, classification

VERSION = 'p4-01-research-v1'
STATE = re.compile(r'ftp|threshold|weight|resting|(?:^|_)zones?(?:_|$)|default_max|maximum_heart_rate', re.I)
STATE_MESSAGES = {'user_profile', 'zones_target', 'hr_zone', 'power_zone', 'weight_scale', 'sport'}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + '\n')


def snapshot_store(source, destination):
    """Copy only database-referenced originals; never copy OAuth credential files."""
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    live = sqlite3.connect((source.resolve() / 'rideworks.sqlite3').as_uri() + '?mode=ro', uri=True)
    target = sqlite3.connect(destination / 'rideworks.sqlite3')
    try:
        live.backup(target)
        target.row_factory = sqlite3.Row
        for table in ('sources', 'export_snapshots'):
            for record in target.execute(f'SELECT * FROM {table}'):
                row = dict(record)
                verified_bytes(source, row)
                path = destination / row['stored_path']
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / row['stored_path'], path)
                verified_bytes(destination, row)
    finally:
        live.close(); target.close()


def readonly_store(directory):
    """Use the accepted read boundary without Store's initialization/migrations."""
    store = Store.__new__(Store)
    store.data_dir = directory.resolve()
    store.connection = sqlite3.connect((store.data_dir / 'rideworks.sqlite3').as_uri() + '?mode=ro', uri=True)
    store.connection.row_factory = sqlite3.Row
    store.connection.execute('PRAGMA query_only=ON')
    if store.connection.execute('PRAGMA user_version').fetchone()[0] != 7:
        raise ValueError('Research expects accepted schema 7; no migration is permitted')
    return store


def verified_bytes(root, row):
    path = (root / row['stored_path']).resolve()
    if root.resolve() not in path.parents:
        raise ValueError('Artifact outside supplied store')
    payload = path.read_bytes()
    if len(payload) != row['byte_size'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
        raise ValueError('Original artifact integrity mismatch')
    return gzip.decompress(payload) if row.get('packaging') == 'gzip' else payload


def raw_inventory(store):
    """All retained originals, including fields omitted by production extraction."""
    candidates, work, csv_fields = [], [], []
    messages, field_names, formats = Counter(), Counter(), Counter()
    artifacts = [dict(r) for r in store.connection.execute('SELECT * FROM sources ORDER BY source_id')]
    for i, source in enumerate(artifacts):
        payload = verified_bytes(store.data_dir, source)
        fmt = source['content_format']; formats[fmt] += 1
        base = dict(activity_id=source['activity_id'], source_id=source['source_id'],
                    artifact_sha256=source['sha256'], format=fmt)
        if fmt == 'FIT':
            with fitdecode.FitReader(io.BytesIO(payload), check_crc=fitdecode.CrcCheck.RAISE) as reader:
                for order, frame in enumerate(reader):
                    if not isinstance(frame, fitdecode.FitDataMessage):
                        continue
                    messages[frame.name] += 1
                    for field in frame.fields:
                        if field.value is None:
                            continue
                        field_names[frame.name + '.' + field.name] += 1
                        if STATE.search(field.name) or frame.name in STATE_MESSAGES:
                            candidates.append(base | dict(message=frame.name, field=field.name,
                                value=field.value, units=field.units, source_order=order,
                                origin='source_supplied_origin_unverified', effective_interval=None))
                        if frame.name == 'session' and field.name == 'total_work':
                            work.append(base | dict(value=field.value, units=field.units,
                                                   origin='source_summary', field='session.total_work'))
        elif fmt in ('TCX', 'GPX'):
            root = ET.fromstring(payload.lstrip())
            for element in root.iter():
                name = element.tag.split('}')[-1]
                field_names[fmt + '.' + name] += 1
                # No coordinates, titles, or arbitrary text enter the report.
                if element.text and element.text.strip() and STATE.search(name):
                    candidates.append(base | dict(message=fmt, field=name, value=element.text.strip(),
                        units=element.attrib.get('unit'), origin='source_supplied_origin_unverified',
                        effective_interval=None))
        else:
            raise ValueError('Unsupported original format')
        if (i + 1) % 100 == 0:
            print(f'Inspected {i + 1}/{len(artifacts)} originals', flush=True)
    for source in store.connection.execute('SELECT * FROM export_snapshots'):
        payload = verified_bytes(store.data_dir, dict(source))
        reader = csv.reader(io.StringIO(payload.decode('utf-8-sig')))
        headers = next(reader)
        values = [[] for _ in headers]
        for row_number, row in enumerate(reader, 1):
            if len(row) != len(headers):
                raise ValueError('CSV shape changed')
            for index, value in enumerate(row):
                if value.strip():
                    values[index].append(value)
                    if STATE.search(headers[index]) and headers[index] not in ('Weighted Average Power', 'Weather Ozone'):
                        candidates.append(dict(format='CSV', snapshot_sha256=source['sha256'],
                            row_index=row_number, field=headers[index], column_index=index, value=value,
                            units='source_unspecified', origin='source_supplied_origin_unverified',
                            effective_interval=None))
        csv_fields = [dict(field=h, column_index=i, present=len(values[i]),
                           distinct=len(set(values[i]))) for i, h in enumerate(headers)]
    # All retained API observations, not merely current links. Record field names;
    # no credentials are stored here and no endpoint is invoked.
    api_fields = Counter()
    for table in ('strava_api_sources', 'strava_stream_sources'):
        for row in store.connection.execute(f'SELECT source_id,activity_id,evidence_json FROM {table}'):
            for name, value in json.loads(row['evidence_json']).items():
                if value is not None:
                    api_fields[table + '.' + name] += 1
                    if STATE.search(name):
                        candidates.append(dict(format='API', source_id=row['source_id'],
                            activity_id=row['activity_id'], field=name, value=value,
                            origin='source_supplied_origin_unverified', effective_interval=None))
    return dict(version=VERSION, formats=dict(formats), messages=dict(messages),
                field_names=dict(field_names), state_candidates=candidates, work=work,
                csv_fields=csv_fields, api_fields=dict(api_fields),
                verified_artifacts=len(artifacts) + store.connection.execute('SELECT count(*) FROM export_snapshots').fetchone()[0])


def contiguous_power(times, values):
    """Strict research whole-record-envelope check; never repair or fill gaps."""
    if len(times) != len(values) or len(values) < 30:
        return 'too_short_or_unpaired'
    if any(type(p) not in (int, float) or not math.isfinite(p) or p < 0 for p in values):
        return 'missing_or_invalid_power'
    if any(t is None for t in times) or any(b - a != 1 for a, b in zip(times, times[1:])):
        return 'non_contiguous_timing'
    return None


def normalized_power(values):
    """30 complete one-second samples, fourth-power mean, no padded warmup."""
    if len(values) < 30 or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Complete nonnegative power is required')
    total = sum(values[:30]); fourths = [(total / 30) ** 4]
    for index in range(30, len(values)):
        total += values[index] - values[index - 30]
        fourths.append((total / 30) ** 4)
    return (math.fsum(fourths) / len(fourths)) ** .25


def power_stress(values, ftp):
    if ftp is None:
        return None
    if not math.isfinite(ftp) or ftp <= 0:
        raise ValueError('Positive date-effective FTP required')
    return len(values) / 3600 * (normalized_power(values) / ftp) ** 2 * 100


def curves(loads, *, seed=None):
    """Industry 1/tau recursion vs complete-window rolling means.

    None is unknown. Once unknown, an EWMA stays unknown without a new explicitly
    justified seed; rolling means recover when the unknown leaves their window.
    A no-activity day is not automatically rest; callers must establish its zero.
    """
    ctl, atl = (seed, seed)
    result = []
    for i, load in enumerate(loads):
        if load is not None and (not math.isfinite(load) or load < 0):
            raise ValueError('Invalid daily load')
        balance = ctl - atl if ctl is not None and atl is not None else None
        ctl = ctl + (load - ctl) / 42 if load is not None and ctl is not None else None
        atl = atl + (load - atl) / 7 if load is not None and atl is not None else None
        item = dict(load=load, ctl=ctl, atl=atl, tsb=balance)
        for n in (7, 42):
            window = loads[max(0, i + 1 - n):i + 1]
            item[f'mean{n}'] = math.fsum(window) / n if len(window) == n and all(x is not None for x in window) else None
        result.append(item)
    return result


def census(store, raw, zone):
    history = performance_history(store)
    if history['pending']:
        raise ValueError('Accepted Performance history is not current; do not rebuild live data')
    performance = {r['activity_id']: r for r in history['results']}
    work = defaultdict(list)
    thresholds = defaultdict(list)
    for value in raw['state_candidates']:
        if (value.get('message') == 'session' and value['field'] == 'threshold_power'
                and value.get('units') == 'watts' and type(value['value']) in (int, float)
                and value['value'] > 0):
            thresholds[value['source_id']].append(value)
    for w in raw['work']:
        if w['units'] == 'J' and type(w['value']) in (int, float) and w['value'] >= 0:
            work[w['activity_id']].append(w)
    rows = []
    for snapshot in store.activity_history():
        shown = presentation(snapshot); identity = shown['activity_id']; p = performance[identity]
        kind = classification(snapshot)['activity_type']
        files = [e for e in snapshot['sources'] if e['source']['kind'] not in ('strava_api', 'strava_export')]
        api = [e for e in snapshot['sources'] if e['source']['kind'] == 'strava_api' and e['source']['is_current']]
        streams = [e for e in store.strava_stream_evidence(identity) if e['is_current']]
        stamp = datetime.fromisoformat(shown['start_time']) if shown['start_time'] else None
        day = stamp.astimezone(zone).date() if stamp and stamp.tzinfo else stamp.date() if stamp else None
        native_power = any(e['extraction']['power_present'] for e in files)
        hr_stream = any(e['extraction']['heart_rate_present'] for e in files)
        api_power = any(any(v is not None for v in e['streams'].get('watts', {}).get('data', [])) for e in streams)
        api_hr = any(any(v is not None for v in e['streams'].get('heartrate', {}).get('data', [])) for e in streams)
        hr_summary = any(e['summary'].get('avg_heart_rate') is not None for e in files)
        hr_summary |= any(any(l.get('avg_heart_rate') is not None for l in e.get('xml_context', {}).get('lap_summaries', [])) for e in files)
        hr_summary |= any(e['summary']['values'].get('average_heartrate') is not None for e in api)
        csv_hr = any(any(f['column'] == 'Average Heart Rate' and f['status'] == 'present' for f in e['summary']['fields'])
                     for e in snapshot['sources'] if e['source']['kind'] == 'strava_export')
        api_work = [e for e in api if e['summary']['values'].get('kilojoules') is not None]
        timers = [dict(source_id=e['source']['source_id'], seconds=e['summary']['total_timer_time'])
                  for e in files if e['summary'].get('total_timer_time') is not None]
        timed_envelopes = []
        for e in files:
            first, last, count = store.connection.execute('SELECT min(timestamp),max(timestamp),count(timestamp) FROM records WHERE extraction_id=?', (e['extraction']['extraction_id'],)).fetchone()
            if first and last and count >= 2:
                a, b = datetime.fromisoformat(first), datetime.fromisoformat(last)
                if a.tzinfo is not None and b.tzinfo is not None and b > a:
                    timed_envelopes.append(dict(source_id=e['source']['source_id'],
                        seconds=(b - a).total_seconds(), status='recorded_span_not_session_duration'))
        r = dict(activity_id=identity, day=str(day) if day else None, year=str(day.year) if day else 'unknown',
            kind=kind, absolute_date=shown['absolute_time'], duration=shown['duration'],
            duration_source=shown['duration_source'], native_power=bool(native_power), api_power=api_power,
            hr_stream=bool(hr_stream or api_hr), hr_summary=bool(hr_summary), csv_hr_summary=csv_hr,
            known_work=bool(work[identity] or api_work), source_work=work[identity],
            api_work_kj=[e['summary']['values']['kilojoules'] for e in api_work],
            eligible=bool(p['eligible']), reason=p['reason'], power_source=p.get('content_format'),
            best20=p.get('average_watts'), whole_power_reason='not_performance_eligible',
            power_source_id=p.get('source_id') or p.get('api_evidence', {}).get('stream_source_id'),
            ftp=None, ftp_effective_date=None, ftp_provenance=None, stress=None,
            ftp_scope=None, stress_status='unavailable')
        r.update(file_timer_evidence=timers, recorded_time_spans=timed_envelopes,
                 race_title_hint=bool(re.search(r'\brace\b', shown['title'], re.I)))
        r['recorded_power_work_kj'] = None
        if p['eligible']:
            if p['extraction_id']:
                records = store.connection.execute('SELECT timestamp,power FROM records WHERE extraction_id=? ORDER BY record_index', (p['extraction_id'],)).fetchall()
                times = [datetime.fromisoformat(x[0]).timestamp() if x[0] else None for x in records]
                values = [x[1] for x in records]
            else:
                observed = next(e for e in streams if e['source_id'] == p['api_evidence']['stream_source_id'])
                times = observed['streams']['time']['data']; values = observed['streams']['watts']['data']
            r['whole_power_reason'] = contiguous_power(times, values)
            r['power_samples'] = len(values)
            if r['whole_power_reason'] is None:
                # Half-open one-second sample bins over the recorded envelope;
                # no claim that it covers missing session boundaries or pauses.
                r['recorded_power_work_kj'] = math.fsum(values) / 1000
                supplied = thresholds[p.get('source_id')]
                if len(supplied) == 1:
                    source = next(e for e in files if e['source']['source_id'] == p['source_id'])
                    summary = source['summary']
                    # A source threshold is a supplied session-context candidate,
                    # not measured/tested FTP or authority for adjacent activities.
                    r.update(ftp=supplied[0]['value'], ftp_effective_date=shown['start_time'],
                        ftp_provenance=supplied[0], ftp_scope='this_source_session_only')
                    if summary.get('total_elapsed_time') == summary.get('total_timer_time') == len(values):
                        r.update(stress=power_stress(values, r['ftp']),
                            normalized_power=normalized_power(values),
                            stress_status='candidate_using_source_supplied_session_threshold')
            # A continuous record envelope is not automatically full session coverage.
            r['envelope_seconds'] = times[-1] - times[0] + 1 if times and times[0] is not None and times[-1] is not None else None
        rows.append(r)
    groups = defaultdict(list)
    for r in rows:
        groups[(r['year'], r['kind'])].append(r)
    def counts(group):
        flags = {
            'eligible_power': lambda r: r['eligible'],
            'eligible_file': lambda r: r['eligible'] and r['power_source'] != 'Strava API stream',
            'eligible_api': lambda r: r['eligible'] and r['power_source'] == 'Strava API stream',
            'preserved_power_excluded': lambda r: (r['native_power'] or r['api_power']) and not r['eligible'],
            'hr_stream': lambda r: r['hr_stream'], 'hr_summary': lambda r: r['hr_summary'],
            'csv_hr_summary': lambda r: r['csv_hr_summary'],
            'hr_any': lambda r: r['hr_stream'] or r['hr_summary'] or r['csv_hr_summary'],
            'duration': lambda r: r['duration'] is not None, 'known_work': lambda r: r['known_work'],
            'power_hr_duration_work': lambda r: r['eligible'] and (r['hr_stream'] or r['hr_summary'] or r['csv_hr_summary']) and r['duration'] is not None and r['known_work'],
            'whole_record_envelope': lambda r: r['eligible'] and r['whole_power_reason'] is None,
            'unknown_timezone': lambda r: not r['absolute_date'],
            'session_threshold_candidate': lambda r: r['ftp'] is not None,
            'source_threshold_stress_candidate': lambda r: r['stress'] is not None,
            'file_timer_duration': lambda r: bool(r['file_timer_evidence']),
            'recorded_time_span': lambda r: bool(r['recorded_time_spans']),
            'race_title_hint_unconfirmed': lambda r: r['race_title_hint'],
        }
        overlap = Counter(''.join(str(int(v)) for v in (r['eligible'], r['hr_stream'] or r['hr_summary'] or r['csv_hr_summary'], r['duration'] is not None, r['known_work'])) for r in group)
        return dict(activities=len(group), **{k: sum(f(r) for r in group) for k, f in flags.items()}, overlap_power_hr_duration_work=dict(overlap))
    aggregate = dict(version=VERSION, timezone=str(zone), total=counts(rows),
        cycling=counts([r for r in rows if r['kind'] in ('Ride', 'Virtual Ride')]),
        by_year_type=[dict(year=y, kind=k, **counts(g)) for (y, k), g in sorted(groups.items(), key=lambda x: str(x[0]))],
        by_type=[dict(kind=k, **counts([r for r in rows if r['kind'] == k])) for k in sorted({r['kind'] for r in rows}, key=str)],
        performance_pending=history['pending'],
        eligible_envelope_reasons=dict(Counter(r['whole_power_reason'] or 'contiguous' for r in rows if r['eligible'])),
        raw_formats=raw['formats'], verified_artifacts=raw['verified_artifacts'],
        athlete_state_candidate_fields=dict(Counter(c.get('message', c['format']) + '.' + c['field'] for c in raw['state_candidates'])),
        csv_field_presence=raw['csv_fields'])
    return rows, aggregate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True, help='Private disposable copy, schema 7')
    parser.add_argument('--snapshot-from', type=Path, help='Create --data-dir as a NEW private copy of this store')
    parser.add_argument('--output-dir', type=Path, required=True, help='PRIVATE research outputs')
    parser.add_argument('--timezone', default='America/Los_Angeles')
    parser.add_argument('--reuse-raw', action='store_true', help='Reuse local raw inventory only after all hashes recheck')
    args = parser.parse_args()
    if args.snapshot_from:
        snapshot_store(args.snapshot_from, args.data_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    store = readonly_store(args.data_dir)
    try:
        before = hashlib.sha256((args.data_dir / 'rideworks.sqlite3').read_bytes()).hexdigest()
        raw_path = args.output_dir / 'raw-inventory.json'
        if args.reuse_raw:
            raw = json.loads(raw_path.read_text())
            if raw.get('version') != VERSION or raw.get('database_sha256') != before:
                raise ValueError('Raw inventory is not from this method/database')
            for table in ('sources', 'export_snapshots'):
                for row in store.connection.execute(f'SELECT * FROM {table}'):
                    verified_bytes(args.data_dir, dict(row))
        else:
            raw = raw_inventory(store); raw['database_sha256'] = before; dump(raw_path, raw)
        rows, aggregate = census(store, raw, ZoneInfo(args.timezone))
        integrity = store.connection.execute('PRAGMA integrity_check').fetchone()[0]
        foreign_keys = list(store.connection.execute('PRAGMA foreign_key_check'))
        after = hashlib.sha256((args.data_dir / 'rideworks.sqlite3').read_bytes()).hexdigest()
        if before != after or integrity != 'ok' or foreign_keys:
            raise ValueError('Read-only/integrity invariant failed')
        aggregate['integrity'] = dict(database_unchanged=True, integrity_check=integrity, foreign_key_violations=len(foreign_keys))
        dump(args.output_dir / 'activities.json', rows)
        dump(args.output_dir / 'census.json', aggregate)
        print(json.dumps(dict(activities=len(rows), eligible=aggregate['total']['eligible_power'], state_candidate_fields=aggregate['athlete_state_candidate_fields']), sort_keys=True))
    finally:
        store.close()


if __name__ == '__main__':
    main()
