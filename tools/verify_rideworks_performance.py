#!/usr/bin/env python3
"""Independent full-population analytical verification; aggregate output only.

Run on a disposable history copy. This verifier does not call production best-20
or cohort classification as an oracle. Contiguous-run segmentation and prefix
sums independently enumerate all valid windows, with Decimal rounding.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store


def independent_best(records):
    runs, run = [], []
    previous = None
    for r in records:
        stamp = datetime.fromisoformat(r['timestamp']) if r['timestamp'] else None
        valid = stamp is not None and stamp.tzinfo is not None and r['power'] is not None
        if not valid or (run and stamp - previous != timedelta(seconds=1)):
            if run: runs.append(run)
            run = []
        if valid: run.append(r)
        previous = stamp
    if run: runs.append(run)
    best, best_sum, windows = None, None, 0
    for run in runs:
        prefix = [0]
        for record in run: prefix.append(prefix[-1] + record['power'])
        for i in range(len(run) - 1199):
            total = prefix[i+1200] - prefix[i]
            windows += 1
            if best_sum is None or total > best_sum:
                first, last = run[i], run[i+1199]
                mean = Decimal(total) / Decimal(1200)
                best_sum = total
                best = dict(average_watts=float(mean), rounded_watts=int(mean.quantize(Decimal('1'),rounding=ROUND_HALF_UP)),
                            start_record_index=first['record_index'], end_exclusive_record_index=last['record_index']+1,
                            start_timestamp=first['timestamp'],
                            end_exclusive_timestamp=(datetime.fromisoformat(first['timestamp'])+timedelta(seconds=1200)).isoformat(),
                            sample_count=1200)
    if best is not None: best['eligible_window_count']=windows
    return best


def independent_type(snapshot):
    ordered=sorted(snapshot['sources'],key=lambda e:(e['source']['imported_at'],e['source']['source_id']))
    csv=[e for e in ordered if e['source']['kind']=='strava_export' and (e['summary'].get('activity_type') or '').strip()]
    if csv:
        return csv[-1]['summary']['activity_type'].strip(), [csv[-1]['source']['source_id']]
    known=[]
    for e in ordered:
        if e['source']['kind']=='strava_export': continue
        s=e['summary']; sport=(s.get('sport') or '').casefold()
        value='Virtual Ride' if s.get('sub_sport')=='virtual_activity' else 'Ride' if sport in ('biking','cycling') else s.get('sport')
        if value: known.append((value,e['source']['source_id']))
    types={kind for kind,_ in known}
    return (next(iter(types)) if len(types)==1 else None), [source for _,source in known]


def stable_rows(store):
    return [dict(activity_id=r['activity_id'], input_signature=r['input_signature'], result=json.loads(r['result_json']))
            for r in store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id')]


def independent_presentation(points):
    """Compare heap presentation against a direct scan at every entry/expiry."""
    from rideworks.performance_view import performance_view
    now = datetime.now(timezone.utc)
    view = performance_view(points, as_of=now)
    stamps = {i: datetime.fromisoformat(p['start_time']) for i, p in enumerate(points)
              if p['absolute_time']}
    times = sorted({t + timedelta(days=d) for t in stamps.values() for d in (0, 42)
                    if t + timedelta(days=d) <= now} | {now})
    steps = iter(view['rolling'])
    upcoming = next(steps, None)
    actual = None
    def winner(indexes):
        return min(indexes, key=lambda i: (-points[i]['average_watts'],
                   points[i]['date_key'], points[i]['activity_id']), default=None)
    for t in times:
        while upcoming and datetime.fromisoformat(upcoming['at']) <= t:
            actual = upcoming['index']
            upcoming = next(steps, None)
        expected = winner(i for i, stamp in stamps.items() if t-timedelta(days=42) < stamp <= t)
        assert actual == expected, 'Rolling presentation differs from direct window scan'
    assert view['summaries']['current'] == actual
    assert view['summaries']['lifetime'] == winner(range(len(points)))
    assert view['summaries']['latest'] == max(range(len(points)),
           key=lambda i: (points[i]['date_key'], points[i]['activity_id']), default=None)
    # Current archive clock is not a leap-day boundary. Compute the independent
    # one-year calendar cutoff without using production month arithmetic.
    try: year_start = now.replace(year=now.year-1)
    except ValueError: year_start = now.replace(year=now.year-1, day=28)
    assert view['summaries']['year'] == winner(i for i, stamp in stamps.items() if year_start <= stamp <= now)
    return dict(result='passed', independently_checked_event_times=len(times),
                rolling_changes=len(view['rolling']), all_four_summaries_verified=True,
                exact_42_day_expiry=True, raw_comparison=True,
                unknown_activity_timezones=view['unknown_timezones'])


def verify(data_dir, representative):
    from rideworks.performance import performance_history, rebuild_performance
    with Store(data_dir) as store:
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert store.connection.execute('PRAGMA foreign_key_check').fetchall()==[]
        snapshots=store.activity_history()
        saved={r['activity_id']:r for r in stable_rows(store)}
        assert len(snapshots)==len(saved)==1434
        reasons, types, formats = Counter(), Counter(), Counter()
        native_disagreements=0
        means=[]
        representative_digest=sha256(representative.read_bytes()).hexdigest()
        seed_seen=False
        for snapshot in snapshots:
            activity_id=snapshot['activity']['activity_id']; result=saved[activity_id]['result']
            kind, identities=independent_type(snapshot)
            types[kind]+=1
            assert result['classification']['activity_type']==kind
            assert result['classification']['source_ids']==identities
            assert result['policy']=='virtual-native-power-v1' and result['method']=='best-average-power-v1'
            assert result['duration_seconds']==1200
            files=[e for e in snapshot['sources'] if e['source']['kind']!='strava_export']
            if kind!='Virtual Ride':
                assert not result['eligible']
            else:
                candidates=[]
                for e in files:
                    native=e['summary']
                    if (native.get('sport') or '').casefold() in ('cycling','biking') and native.get('sub_sport')!='virtual_activity':
                        native_disagreements+=1
                    source=e['source']; records=store.get_source(source['source_id'])['records']
                    # Production excludes an entire source with unknown-zone records.
                    naive=any(r['timestamp'] and datetime.fromisoformat(r['timestamp']).tzinfo is None for r in records)
                    best=None if naive else independent_best(records)
                    if best is not None: candidates.append((e,best))
                assert result['eligible']==(len(candidates)==1)
                if result['eligible']:
                    evidence,best=candidates[0]
                    assert result['source_id']==evidence['source']['source_id']
                    assert result['extraction_id']==evidence['extraction']['extraction_id']
                    for key,value in best.items(): assert result[key]==value, 'Independent window mismatch'
                    formats[evidence['source']['content_format']]+=1
                    means.append(best['average_watts'])
                    if evidence['source']['sha256']==representative_digest:
                        assert best['rounded_watts']==120
                        assert len(store.get_source(evidence['source']['source_id'])['records'])==3621
                        seed_seen=True
                elif len(candidates)>1:
                    assert result['reason']=='multiple_eligible_native_sources'
            reasons[result['reason'] or 'eligible']+=1
        assert types['Virtual Ride']==1264 and types['Ride']==146 and seed_seen
        history=performance_history(store)
        assert history['pending']==0 and history['missing_dates']==0
        assert len(history['points'])==len(means)
        assert all(p['classification']['activity_type']=='Virtual Ride' for p in history['points'])
        assert sum(reasons.values())==1434
        initial=stable_rows(store); points=history['points']
        rebuild_report=rebuild_performance(store)
        assert stable_rows(store)==initial, 'Rebuild changed analytical results'
        assert performance_history(store)['points']==points
        span=[points[0]['date_day'],points[-1]['date_day']]
        presentation=independent_presentation(points)
    with Store(data_dir) as restarted:
        assert stable_rows(restarted)==initial
        assert performance_history(restarted)['points']==points
    return dict(result='passed', independently_evaluated=1434, independently_verified_eligible=len(means),
                virtual_candidates=types['Virtual Ride'], outdoor_activities=types['Ride'],
                outdoor_eligible=0, non_cycling_eligible=0, classification_native_disagreements=native_disagreements,
                counts_by_status_reason=dict(sorted(reasons.items())), eligible_source_formats=dict(formats),
                raw_average_range_watts=[min(means),max(means)], eligible_date_span=span,
                representative_display_watts=120, representative_records=3621,
                all_source_extraction_identities_verified=True, exact_ties_verified=True,
                no_summary_substitution=True, idempotent_rebuild=True, restart_preserved=True,
                sqlite_integrity=True, foreign_keys=True, presentation=presentation, rerun_report=rebuild_report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--representative',type=Path,required=True)
    args=parser.parse_args()
    # Failure output never identifies a private Activity or source title.
    try: print(json.dumps(verify(args.data_dir,args.representative),indent=2))
    except Exception as exc:
        print(f'Independent performance verification failed ({type(exc).__name__})',file=sys.stderr)
        raise SystemExit(1)
