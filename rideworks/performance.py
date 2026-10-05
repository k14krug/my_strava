"""Specific versioned Virtual Ride native-power history; no source ranking."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json

from .analysis import BEST_20_METHOD, WINDOW_SAMPLES, best_20_minute_power
from .errors import IntegrityError
from .history import presentation

POLICY = 'virtual-native-power-v1'


def _check_extractions(store):
    if store.connection.execute('''SELECT 1 FROM sources s LEFT JOIN extractions e
        ON e.source_id=s.source_id WHERE e.extraction_id IS NULL LIMIT 1''').fetchone():
        raise IntegrityError('File Source has no current extraction; performance stopped')


def classification(snapshot):
    evidence = sorted(snapshot['sources'], key=lambda e: (e['source']['imported_at'], e['source']['source_id']))
    csv = [e for e in evidence if e['source']['kind'] == 'strava_export'
           and (e['summary'].get('activity_type') or '').strip()]
    api = [e for e in evidence if e['source']['kind']=='strava_api' and e['source']['is_current']
           and (e['summary'].get('activity_type') or '').strip()]
    if api or csv:
        latest = (api or csv)[-1]
        return dict(activity_type=latest['summary']['activity_type'].strip(),
                    source_ids=[latest['source']['source_id']], basis='latest_strava_type')
    types = []
    for e in evidence:
        if e['source']['kind'] in ('strava_export','strava_api'):
            continue
        summary = e['summary']
        kind = ('Virtual Ride' if summary.get('sub_sport') == 'virtual_activity' else
                'Ride' if (summary.get('sport') or '').casefold() in ('cycling', 'biking') else
                summary.get('sport'))
        if kind:
            types.append((kind, e['source']['source_id']))
    kinds = {kind for kind, _ in types}
    return dict(activity_type=next(iter(kinds)) if len(kinds) == 1 else None,
                source_ids=[source for _, source in types],
                basis='conflicting_native_classification' if len(kinds) > 1 else 'native_session')


def input_signature(snapshot):
    """All current candidate identities matter, including newly competing files.

    Metadata is small; including classification/date evidence also invalidates
    changed observation selection without a generalized dependency graph.
    """
    inputs = sorted((dict(source_id=e['source']['source_id'],
                          imported_at=e['source']['imported_at'],
                          extraction=e['extraction'], summary=e['summary'],
                          **({'is_current':e['source']['is_current']} if e['source']['kind']=='strava_api' else {}))
                     for e in snapshot['sources']), key=lambda e: e['source_id'])
    return sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def evaluate(store, snapshot):
    activity_id = snapshot['activity']['activity_id']
    cohort = classification(snapshot)
    result = dict(activity_id=activity_id, policy=POLICY, method=BEST_20_METHOD,
                  duration_seconds=WINDOW_SAMPLES, classification=cohort,
                  status='ineligible', reason=None, eligible=False,
                  source_id=None, extraction_id=None, candidates=[])
    kind = cohort['activity_type']
    if kind != 'Virtual Ride':
        result['reason'] = ('outdoor_ride_excluded' if kind == 'Ride' else
                            'ambiguous_classification' if cohort['basis'] == 'conflicting_native_classification'
                            else 'non_virtual_activity' if kind else 'classification_unavailable')
        return result
    files = [e for e in snapshot['sources'] if e['source']['kind'] not in ('strava_export','strava_api')]
    eligible = []
    for metadata in files:
        source, extraction = metadata['source'], metadata['extraction']
        if not extraction or not extraction.get('extraction_id'):
            raise IntegrityError('Performance candidate has no current extraction')
        candidate = dict(source_id=source['source_id'], extraction_id=extraction['extraction_id'],
                         content_format=source['content_format'], eligible=False, reason='no_native_power')
        counts = store.connection.execute('SELECT COUNT(*), COUNT(power) FROM records WHERE extraction_id=?',
                                           (extraction['extraction_id'],)).fetchone()
        if tuple(counts) != (extraction['record_count'], extraction['power_present']):
            raise IntegrityError('Native record counts do not match current extraction')
        if extraction['power_present']:
            native = store.get_source(source['source_id'])
            records = native['records']
            if len(records) != extraction['record_count'] or sum(r['power'] is not None for r in records) != extraction['power_present']:
                raise IntegrityError('Native record counts do not match current extraction')
            # Naive timestamps are known unsupported timing, not guessed UTC.
            # Malformed timestamps/negative or invalid power remain fatal defects.
            try:
                timestamps = [datetime.fromisoformat(r['timestamp']) for r in records if r['timestamp'] is not None]
            except (ValueError, TypeError) as exc:
                raise IntegrityError('Invalid timestamp in current native extraction') from exc
            if any(r['power'] is not None and (not isinstance(r['power'], int) or r['power'] < 0) for r in records):
                raise IntegrityError('Unexpected native power in performance candidate')
            if any(t.tzinfo is None for t in timestamps):
                candidate['reason'] = 'native_timestamp_timezone_unknown'
            else:
                best = best_20_minute_power(records, activity_id=activity_id,
                                           source_id=source['source_id'], extraction_id=extraction['extraction_id'])
                candidate.update(eligible=best['eligible'], reason=best['reason'])
                if best['eligible']:
                    eligible.append(best | dict(content_format=source['content_format']))
        result['candidates'].append(candidate)
    if len(eligible) > 1:
        result['reason'] = 'multiple_eligible_native_sources'
    elif eligible:
        result.update(eligible[0])
        result.update(status='eligible', eligible=True, reason=None)
    else:
        reasons = {c['reason'] for c in result['candidates']}
        result['reason'] = (next(iter(reasons)) if len(reasons) == 1 else
                            'no_eligible_native_source' if reasons else 'no_native_file_source')
    return result


def rebuild_performance(store):
    """One serialized snapshot, atomic replacement; fatal failure preserves history."""
    totals, kinds, formats = Counter(), Counter(), Counter()
    calculated_at = datetime.now(timezone.utc).isoformat()
    with store._transaction(write=True):
        _check_extractions(store)
        snapshots = store.activity_history()
        rows = []
        for snapshot in snapshots:
            result = evaluate(store, snapshot)
            kind = result['classification']['activity_type']
            kinds[kind or 'Unknown'] += 1
            totals[result['reason'] or 'eligible'] += 1
            if result['eligible']:
                formats[result['content_format']] += 1
            rows.append((result['activity_id'], WINDOW_SAMPLES, POLICY, BEST_20_METHOD,
                         result['source_id'], result['extraction_id'], input_signature(snapshot),
                         calculated_at, json.dumps(result, sort_keys=True)))
        store.connection.execute('DELETE FROM performance_history WHERE duration_seconds = ? AND policy = ?',
                                 (WINDOW_SAMPLES, POLICY))
        store.connection.executemany('INSERT INTO performance_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', rows)
    return dict(status='completed', evaluated=len(snapshots), virtual_candidates=kinds['Virtual Ride'],
                outdoor_activities=kinds['Ride'], non_cycling_activities=sum(v for k, v in kinds.items() if k not in ('Ride', 'Virtual Ride')),
                eligible=totals['eligible'], ineligible_by_reason={k: v for k, v in sorted(totals.items()) if k != 'eligible'},
                eligible_source_formats=dict(formats), policy=POLICY, method=BEST_20_METHOD,
                duration_seconds=WINDOW_SAMPLES)


def performance_history(store):
    """Current metadata/results only. Changed inputs are explicitly stale, never plotted."""
    with store._transaction():
        _check_extractions(store)
        snapshots = {s['activity']['activity_id']: s for s in store.activity_history()}
        saved = store.connection.execute('SELECT * FROM performance_history WHERE duration_seconds = ? AND policy = ? AND method = ?',
                                         (WINDOW_SAMPLES, POLICY, BEST_20_METHOD)).fetchall()
        results, points = [], []
        stale = 0
        for record in saved:
            snapshot = snapshots[record['activity_id']]
            if input_signature(snapshot) != record['input_signature']:
                stale += 1
                continue
            result = json.loads(record['result_json'])
            result['calculated_at'] = record['calculated_at']
            row = presentation(snapshot)
            result['date_available'] = row['date_key'] is not None
            results.append(result)
            if result['eligible'] and row['date_key'] is not None:
                points.append(dict(activity_id=row['activity_id'], title=row['title'], start_time=row['start_time'],
                                   date_day=row['date_day'], date_key=row['date_key'], absolute_time=row['absolute_time'],
                                   average_watts=result['average_watts'], rounded_watts=result['rounded_watts'],
                                   source_id=result['source_id'], extraction_id=result['extraction_id'],
                                   content_format=result['content_format'], classification=result['classification'],
                                   start_timestamp=result['start_timestamp'], end_exclusive_timestamp=result['end_exclusive_timestamp']))
        points.sort(key=lambda p: (p['date_key'], p['activity_id']))
        return dict(points=points, results=results, evaluated=len(snapshots), current=len(results),
                    pending=len(snapshots) - len(results), stale=stale,
                    missing_dates=sum(r['eligible'] and not r['date_available'] for r in results),
                    policy=POLICY, method=BEST_20_METHOD)
