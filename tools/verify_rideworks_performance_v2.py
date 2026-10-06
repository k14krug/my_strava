#!/usr/bin/env python3
"""Bounded STRAVA-004 live sync/v2 verification; private inputs, aggregate output."""
import argparse
from collections import Counter
from datetime import datetime,timedelta
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.config import strava_credentials
from rideworks.performance import POLICY,performance_history,rebuild_performance
from rideworks.recent_context import recent_context
from rideworks.store import Store
from rideworks.strava import ApiClient,sync
from rideworks.strava_streams import api_only_candidates
from compare_rideworks_strava_streams import fingerprint,independent_best as api_best
from verify_rideworks_performance import independent_best as native_best,independent_presentation


def verify(data_dir,baseline):
    assert not baseline.exists(),'Use a fresh ignored baseline; authorization is never copied'
    baseline.mkdir(parents=True,mode=0o700)
    client=ApiClient(strava_credentials())
    with Store(data_dir) as store:
        with sqlite3.connect(baseline/'rideworks.sqlite3') as backup:store.connection.backup(backup)
        before=fingerprint(store.connection)
        old_rows=[tuple(r) for r in store.connection.execute("SELECT * FROM performance_history WHERE policy='virtual-native-power-v1' ORDER BY activity_id")]
        old={r['activity_id']:json.loads(r['result_json']) for r in store.connection.execute("SELECT * FROM performance_history WHERE policy='virtual-native-power-v1'")}
        eligible={k:r for k,r in old.items() if r['eligible']}
        assert len(old)==1441 and len(eligible)==1022
        assert store.connection.execute('SELECT COUNT(*) FROM performance_history WHERE policy=?',(POLICY,)).fetchone()[0]==0
        originals={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in store.originals.iterdir()}
        candidates=api_only_candidates(store);assert len(candidates)==7
        guard=[patch.object(Store,'reextract',side_effect=AssertionError('source reparse')),
               patch.object(Store,'import_strava_export',side_effect=AssertionError('archive reimport')),
               patch.object(Store,'import_file',side_effect=AssertionError('file import'))]
        for p in guard:p.start()
        try:
            with patch('rideworks.performance.rebuild_performance',wraps=rebuild_performance) as rebuild:
                first=sync(store,client)
                assert rebuild.call_count==1 and first['performance_update']=='updated'
            first_requests=client.stream_requests
            with patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('Unnecessary second rebuild')):
                second=sync(store,client)
            assert second['performance_update']=='current' and second['stream_fetches']==0
        finally:
            for p in reversed(guard):p.stop()
        history=performance_history(store)
        assert len(history['points'])==1027 and history['pending']==0
        current={r['activity_id']:r for r in history['results']}
        checked=0
        keys=('source_id','extraction_id','method','duration_seconds','eligible','status','reason','content_format',
              'average_watts','rounded_watts','sample_count','eligible_window_count','start_record_index',
              'end_exclusive_record_index','start_timestamp','end_exclusive_timestamp')
        for identity,prior in eligible.items():
            result=current[identity]
            assert all(result[k]==prior[k] for k in keys),'File-backed v1 calculation/provenance changed'
            records=[dict(r) for r in store.connection.execute('SELECT record_index,timestamp,power FROM records WHERE extraction_id=? ORDER BY record_index',(prior['extraction_id'],))]
            expected=native_best(records)
            assert expected is not None and all(result[k]==v for k,v in expected.items()),'Independent file oracle differs'
            assert 'api_evidence' not in result
            checked+=1
        api_eligible=0;reasons=Counter();six_week_checked=0
        for candidate in candidates:
            identity=candidate['activity_id'];result=current[identity]
            stream=next(s for s in store.strava_stream_evidence(identity) if s['is_current'])
            streams=stream['streams'];offsets=streams['time']['data']
            watts=streams.get('watts',{}).get('data',[None]*len(offsets))
            expected=api_best(offsets,watts)
            if result['eligible']:
                assert expected is not None and result['classification']['activity_type']=='Virtual Ride'
                assert result['api_evidence']['device_watts'] is True
                assert result['api_evidence']['summary_source_id']==stream['summary_source_id']
                assert result['source_id'] is None and result['extraction_id'] is None
                assert result['average_watts']==expected['average_watts'] and result['rounded_watts']==expected['rounded_watts']
                assert result['start_offset']==expected['start_elapsed'] and result['end_exclusive_offset']==expected['end_exclusive_elapsed']
                assert result['eligible_window_count']==expected['eligible_window_count']
                api_eligible+=1
                context=recent_context(store,identity)
                point=next(p for p in history['points'] if p['activity_id']==identity)
                end=datetime.fromisoformat(point['start_time']);start=end-timedelta(days=42)
                prior=[p for p in history['points'] if p['activity_id']!=identity and p['absolute_time'] and start<datetime.fromisoformat(p['start_time'])<end]
                winner=min(prior,key=lambda p:(-p['average_watts'],datetime.fromisoformat(p['start_time']),p['activity_id']),default=None)
                assert winner is not None and context['prior']['activity_id']==winner['activity_id']
                assert context['window_start']==start.isoformat() and context['window_end']==end.isoformat()
                six_week_checked+=1
            else:
                assert expected is None and 'watts' not in streams
                reasons[result['reason']]+=1
        assert api_eligible==5 and sum(reasons.values())==2
        assert len({p['activity_id'] for p in history['points']})==1027
        overlaps=store.connection.execute('SELECT a.activity_id FROM strava_api_activities a JOIN strava_export_sources e ON e.external_id=a.external_id').fetchall()
        assert len(overlaps)==4 and all('api_evidence' not in current[r[0]] and current[r[0]]['eligible'] for r in overlaps)
        assert [tuple(r) for r in store.connection.execute("SELECT * FROM performance_history WHERE policy='virtual-native-power-v1' ORDER BY activity_id")]==old_rows
        after=fingerprint(store.connection)
        native_tables=[k for k in before if not k.startswith(('strava_api_','strava_stream_')) and k not in ('performance_history','strava_sync_state')]
        assert all(before[k]==after[k] for k in native_tables),'File/export evidence changed'
        assert originals=={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in store.originals.iterdir()}
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
        presentation=independent_presentation(history['points'])
    with Store(data_dir) as restarted:
        assert performance_history(restarted)==history
    return dict(status='passed',policy=POLICY,v1_rows_preserved=len(old_rows),file_backed_results_unchanged=checked,
                independent_native_results_verified=checked,independent_api_results_verified=api_eligible,
                api_current_ineligible=sum(reasons.values()),api_ineligible_by_reason=dict(reasons),
                eligible=1027,pending=0,overlaps_file_backed_without_duplicates=4,
                six_week_comparisons_independently_verified=six_week_checked,
                first_sync=first,second_sync=second,stream_requests_first_sync=first_requests,
                stream_requests_second_sync=client.stream_requests-first_requests,rate_limits=client.rate,
                native_export_tables_unchanged=True,originals_unchanged=True,no_reimports_or_reextraction=True,
                restart=True,integrity=True,foreign_keys=True,presentation=presentation)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True);args=parser.parse_args()
    try:result=verify(args.data_dir,args.baseline)
    except Exception as error:
        print('Performance-v2 verification stopped ('+type(error).__name__+'); inspect local evidence without publishing identifiers.',file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result,indent=2))
