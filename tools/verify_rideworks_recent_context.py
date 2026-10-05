#!/usr/bin/env python3
"""Independent full-history recent-context verification; aggregate output only."""
import argparse
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.analysis import analyze_activity
from rideworks.performance import performance_history
from rideworks.recent_context import recent_context, select_recent_context
from rideworks.store import Store


def saved_rows(store):
    return [tuple(r) for r in store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id')]


def verify(data_dir, representative):
    with Store(data_dir) as store:
        before=saved_rows(store)
        file_state={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
        def authorize(action,table,*args):
            if action in (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE):return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_READ and table in ('records','laps','events'):return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        store.connection.set_authorizer(authorize)
        outcomes={};counts=Counter()
        try:
            with ExitStack() as guard:
                for method in ('get_activity','get_source','import_file','import_fit','import_strava_export','reextract'):
                    guard.enter_context(patch.object(store,method,side_effect=AssertionError('Forbidden data access')))
                guard.enter_context(patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('Forbidden rebuild')))
                history=performance_history(store)
                assert history['evaluated']==1434 and history['pending']==0 and len(history['points'])==1022
                points=history['points'];result_ids={r['activity_id'] for r in history['results'] if r['eligible']}
                assert len(result_ids)==len(points)
                timed={p['activity_id']:datetime.fromisoformat(p['start_time']) for p in points if p['absolute_time']}
                assert len(timed)==len(points), 'Unexpected eligible absolute-time coverage'
                for current in points:
                    end=timed[current['activity_id']];start=end-timedelta(seconds=42*24*60*60)
                    candidates=[p for p in points if p['activity_id']!=current['activity_id']
                                and p['activity_id'] in timed and start<timed[p['activity_id']]<end]
                    candidates.sort(key=lambda p:(-p['average_watts'],timed[p['activity_id']],p['activity_id']))
                    expected=candidates[0] if candidates else None
                    actual=select_recent_context(history,current['activity_id'])
                    assert actual['window_start']==start.isoformat() and actual['window_end']==end.isoformat()
                    assert actual['current']['source_id']==current['source_id']
                    assert actual['current']['extraction_id']==current['extraction_id']
                    assert actual['prior']==expected
                    assert actual['available']==bool(expected)
                    assert actual['reason']==(None if expected else 'no_qualifying_prior_result')
                    if expected:
                        assert expected['activity_id']!=current['activity_id'] and expected['activity_id'] in result_ids
                        counts['with_prior']+=1
                    else:counts['no_prior']+=1
                    outcomes[current['activity_id']]=actual
                for result in history['results']:
                    if not result['eligible']:
                        assert not select_recent_context(history,result['activity_id'])['available']
                        counts['ineligible_checked']+=1
                assert saved_rows(store)==before
        finally:store.connection.set_authorizer(lambda *args: sqlite3.SQLITE_OK)
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
        digest=sha256(representative.read_bytes()).hexdigest()
        snapshots=store.activity_history()
        seed=next(s['activity']['activity_id'] for s in snapshots if any(e['source']['sha256']==digest
                  for e in s['sources'] if e['source']['kind']!='strava_export'))
        analysis=analyze_activity(store,seed)
        assert analysis['best_20_minute_power']['rounded_watts']==120 and len(analysis['native_records'])==3621
        assert analysis['source_summary']['values']['avg_power']==118
        seed_context=outcomes[seed]
        available=next(p['activity_id'] for p in reversed(points) if outcomes[p['activity_id']]['available'])
        first=next(p['activity_id'] for p in points if not outcomes[p['activity_id']]['available'])
        outdoor=next(s['activity']['activity_id'] for s in snapshots
                     if any(r['activity_id']==s['activity']['activity_id'] and r['reason']=='outdoor_ride_excluded' for r in history['results'])
                     and sum(e['source']['kind']=='file_fit' for e in s['sources'])==1)
        links=dict(representative='/activities/'+seed,available='/activities/'+available,no_prior='/activities/'+first,
                   outdoor='/activities/'+outdoor,prior='/activities/'+seed_context['prior']['activity_id'],
                   representative_current_watts=120,representative_prior_watts=seed_context['prior']['rounded_watts'])
        path=Path('output/playwright/p2-04-review-links.json');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(links,indent=2)+'\n')
        assert saved_rows(store)==before
        assert file_state=={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    with Store(data_dir) as restarted:
        assert saved_rows(restarted)==before
        again=performance_history(restarted)
        assert {p['activity_id']:select_recent_context(again,p['activity_id']) for p in again['points']}==outcomes
        assert recent_context(restarted,seed)==seed_context
    return dict(result='passed',evaluated_activities=1434,eligible_evaluated=len(points),with_prior=counts['with_prior'],
                no_prior=counts['no_prior'],ineligible_checked=counts['ineligible_checked'],unknown_eligible_times=0,
                exact_open_42_day_interval=True,current_excluded=True,all_baseline_identities_raw_display_verified=True,
                no_native_baseline_reads=True,no_import_reparse_rebuild=True,persisted_history_unchanged=True,
                originals_unchanged=True,restart_verified=True,sqlite_integrity=True,foreign_keys=True,
                representative_best20_watts=120,representative_fit_average_watts=118,representative_native_records=3621,
                representative_prior_watts=seed_context['prior']['rounded_watts'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--representative',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(verify(args.data_dir,args.representative),indent=2))
    except Exception as exc:
        print(f'Recent-context verification failed ({type(exc).__name__}); private details withheld',file=sys.stderr)
        raise SystemExit(1)
