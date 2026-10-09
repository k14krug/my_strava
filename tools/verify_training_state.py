#!/usr/bin/env python3
"""Independent SQL/Decimal checks of the P4-01 private census/context outputs."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_rideworks_dashboard import source_rows


def fingerprint(db):
    result = {}
    for table, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        digest = hashlib.sha256(); count = 0
        # All columns for stable ordering, including tables with compound PKs.
        columns = len(db.execute(f'SELECT * FROM {table} LIMIT 0').description)
        order = ','.join(str(i + 1) for i in range(columns))
        for row in db.execute(f'SELECT * FROM {table} ORDER BY {order}'):
            digest.update((json.dumps(tuple(row), separators=(',', ':')) + '\n').encode()); count += 1
        result[table] = dict(rows=count, sha256=digest.hexdigest())
    return result


def verify(data_dir, input_dir, compare_dir, zone, live_dir=None):
    db = sqlite3.connect((data_dir.resolve() / 'rideworks.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    rows = json.loads((input_dir / 'activities.json').read_text())
    census = json.loads((input_dir / 'census.json').read_text())
    contexts = json.loads((compare_dir / 'daily-private.json').read_text())
    raw = json.loads((input_dir / 'raw-inventory.json').read_text())
    independent = {r['activity_id']: r for r in source_rows(db)}
    assert len(independent) == len(rows)
    eligible = {identity: json.loads(result) for identity, result in db.execute("SELECT activity_id,result_json FROM performance_history WHERE policy='virtual-power-evidence-v2'")}
    counts = Counter(); day_hours = {}; day_work = {}; day_missing = Counter(); day_rides = Counter()
    work_checked = stress_checked = 0
    for r in rows:
        identity = r['activity_id']; check = independent[identity]
        assert check['kind'] == r['kind']
        stamp = check['stamp']
        day = stamp.astimezone(zone).date() if stamp and stamp.tzinfo else stamp.date() if stamp else None
        assert (str(day) if day else None) == r['day']
        assert eligible[identity]['eligible'] == r['eligible']
        counts[r['kind']] += 1
        # Duration independently selected from typed source summaries/XML/API.
        durations = []
        for record in db.execute('''SELECT s.total_elapsed_time,f.content_format,x.context_json
          FROM sources f JOIN extractions e USING(source_id) JOIN sessions s USING(extraction_id)
          LEFT JOIN xml_context x USING(extraction_id) WHERE f.activity_id=? ORDER BY f.imported_at,f.source_id''', (identity,)):
            value = record[0]
            if value is None and record[1] == 'TCX' and record[2]:
                laps = json.loads(record[2]).get('lap_summaries', [])
                if len(laps) == 1:
                    value = laps[0].get('total_time_seconds')
            if value is not None:
                durations.append(value)
        for payload, in db.execute('''SELECT s.evidence_json FROM strava_api_sources s
          JOIN strava_api_activities a ON a.current_source_id=s.source_id
          WHERE s.activity_id=? ORDER BY s.imported_at DESC,s.source_id DESC''', (identity,)):
            value = json.loads(payload).get('elapsed_time')
            if value is not None:
                durations.append(value)
        duration = durations[0] if durations else None
        assert duration == r['duration']
        if r['kind'] in ('Ride', 'Virtual Ride') and day is not None:
            key = str(day); day_rides[key] += 1
            day_missing[key] += duration is None
            day_hours[key] = day_hours.get(key, Decimal(0)) + (Decimal(str(duration)) / 3600 if duration is not None else Decimal(0))
        if r['eligible']:
            saved = eligible[identity]
            if saved.get('extraction_id'):
                stream = list(db.execute('SELECT timestamp,power FROM records WHERE extraction_id=? ORDER BY record_index', (saved['extraction_id'],)))
                powers = [x[1] for x in stream]
                stamps = [datetime.fromisoformat(x[0]) if x[0] else None for x in stream]
                contiguous = bool(stamps and stamps[0] is not None and all(t == stamps[0] + timedelta(seconds=i) for i, t in enumerate(stamps)))
            else:
                source_id = saved['api_evidence']['stream_source_id']
                stream = json.loads(db.execute('SELECT evidence_json FROM strava_stream_sources WHERE source_id=?', (source_id,)).fetchone()[0])
                offsets = stream['time']['data']; powers = stream['watts']['data']
                contiguous = len(offsets) == len(powers) and offsets == list(range(offsets[0], offsets[0] + len(offsets)))
            complete = contiguous and len(powers) >= 30 and all(type(p) is int and p >= 0 for p in powers)
            assert complete == (r['recorded_power_work_kj'] is not None)
            if complete:
                expected_work = Decimal(sum(powers)) / 1000
                assert abs(expected_work - Decimal(str(r['recorded_power_work_kj']))) < Decimal('1e-9')
                work_checked += 1
                key = str(day); day_work[key] = day_work.get(key, Decimal(0)) + expected_work
            if r['stress'] is not None:
                matching = [v for v in raw['state_candidates'] if v.get('source_id') == r['power_source_id'] and v.get('message') == 'session' and v['field'] == 'threshold_power' and v['value'] == r['ftp']]
                assert len(matching) == 1 and r['ftp_scope'] == 'this_source_session_only'
                # Direct Decimal enumeration is independent of rolling-sum code.
                fourth = sum((Decimal(sum(powers[i:i+30])) / 30) ** 4 for i in range(len(powers)-29)) / (len(powers)-29)
                npower = fourth.sqrt().sqrt()
                stress = Decimal(len(powers)) / 3600 * (npower / Decimal(r['ftp'])) ** 2 * 100
                assert abs(stress - Decimal(str(r['stress']))) < Decimal('1e-9')
                stress_checked += 1
        elif r['recorded_power_work_kj'] is not None or r['stress'] is not None:
            raise AssertionError('Excluded evidence used as eligible load')
    for row in census['by_type']:
        assert counts[row['kind']] == row['activities']
    for i, d in enumerate(contexts):
        assert d['rides'] == day_rides[d['day']]
        assert d['missing_duration'] == day_missing[d['day']]
        assert abs(Decimal(str(d['known_elapsed_hours'])) - day_hours.get(d['day'], Decimal(0))) < Decimal('1e-10')
        for n in (7, 42):
            window = contexts[max(0, i + 1 - n):i + 1]
            expected = sum((day_hours.get(w['day'], Decimal(0)) for w in window), Decimal(0))
            assert abs(Decimal(str(d[f'known_hours{n}'])) - expected) < Decimal('1e-9')
            assert d[f'missing_duration{n}'] == sum(day_missing[w['day']] for w in window)
            expected_work = sum((day_work.get(w['day'], Decimal(0)) for w in window), Decimal(0))
            assert abs(Decimal(str(d[f'known_work_kj{n}'])) - expected_work) < Decimal('1e-7')
    snapshot = fingerprint(db)
    preserved = None
    if live_dir:
        live = sqlite3.connect((live_dir.resolve() / 'rideworks.sqlite3').as_uri() + '?mode=ro', uri=True)
        preserved = snapshot == fingerprint(live); live.close()
        assert preserved, 'Live store changed since snapshot; investigate rather than assert preservation'
    result = dict(activities_verified=len(rows), daily_rows_verified=len(contexts),
        rolling_decimal_comparisons=4 * len(contexts), production_tables_compared=len(snapshot),
        recorded_work_results_verified=work_checked, isolated_source_threshold_stress_verified=stress_checked,
        live_tables_unchanged=preserved, current_ftp_applied_backwards=False,
        physiological_loads_fabricated=0, integrity=db.execute('PRAGMA integrity_check').fetchone()[0],
        foreign_key_violations=len(list(db.execute('PRAGMA foreign_key_check'))))
    db.close(); return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--comparison-dir', type=Path, required=True)
    parser.add_argument('--live-dir', type=Path)
    parser.add_argument('--timezone', default='America/Los_Angeles')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.data_dir, args.input_dir, args.comparison_dir, ZoneInfo(args.timezone), args.live_dir)
    args.output.write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result))
