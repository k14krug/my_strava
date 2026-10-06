#!/usr/bin/env python3
"""Explicit bounded STRAVA-004 catch-up and accepted-state comparison; aggregate only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.config import strava_credentials
from rideworks.performance import performance_history
from rideworks.store import Store
from rideworks.strava import ApiClient,TokenFile,refreshed_connection
from rideworks.strava_streams import api_only_candidates,enrich,persist
from compare_rideworks_strava_streams import fingerprint


def verify(data_dir,baseline,stage_a_cache):
    with sqlite3.connect(baseline/'rideworks.sqlite3') as database:accepted=fingerprint(database)
    originals={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    client=ApiClient(strava_credentials());token=TokenFile(data_dir)
    with Store(data_dir) as store:
        initial=fingerprint(store.connection)
        assert all(initial[k]==v for k,v in accepted.items()),'Accepted database changed before catch-up'
        prior=performance_history(store);assert len(prior['points'])==1022 and prior['pending']==0
        candidates=api_only_candidates(store);assert len(candidates)==7,'Expected seven known API-only cycling Activities'
        # Persist already fetched research observations without new overlap requests.
        for ordinal in range(1,5):
            saved=json.loads((stage_a_cache/f'overlap-{ordinal}.json').read_text())
            identity=store.connection.execute('SELECT activity_id FROM strava_api_activities WHERE external_id=?',(saved['external_id'],)).fetchone()
            assert identity is not None and identity[0]==saved['activity_id']
            persist(store,saved['external_id'],saved['streams'],retrieved_at=saved['retrieved_at'])
        def guard(action,table,*args):
            return sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_READ and table in ('records','laps','events') else sqlite3.SQLITE_OK
        store.connection.set_authorizer(guard)
        try:
            with token.lock(),patch.object(Store,'reextract',side_effect=AssertionError('source reparse')),patch.object(Store,'import_strava_export',side_effect=AssertionError('archive reimport')),patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('hidden rebuild')):
                current=refreshed_connection(token,client)
                first=enrich(store,client,current['access_token'],[r['external_id'] for r in candidates])
        finally:store.connection.set_authorizer(lambda *args:sqlite3.SQLITE_OK)
        after=fingerprint(store.connection)
        assert all(after[k]==v for k,v in accepted.items()),'Catch-up altered accepted evidence or Performance'
        assert performance_history(store)==prior
        usable=sum(any(s['is_current'] and s['chart_unavailable_reason'] is None for s in store.strava_stream_evidence(r['activity_id'])) for r in candidates)
        sources_before=store.connection.execute('SELECT COUNT(*) FROM strava_stream_sources').fetchone()[0]
    with Store(data_dir) as restarted:
        with token.lock():
            current=refreshed_connection(token,client)
            second=enrich(restarted,client,current['access_token'],[r['external_id'] for r in candidates])
        assert second['stream_fetches']==0 and second['stream_reused']==7,'Idempotent rerun unexpectedly fetched streams'
        assert restarted.connection.execute('SELECT COUNT(*) FROM strava_stream_sources').fetchone()[0]==sources_before
        assert restarted.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not restarted.connection.execute('PRAGMA foreign_key_check').fetchall()
        assert performance_history(restarted)==prior
        choices=sorted(candidates,key=lambda r:r['start_date'],reverse=True)
        overlap=restarted.connection.execute('SELECT activity_id FROM strava_stream_sources WHERE external_id NOT IN (SELECT external_id FROM strava_api_activities WHERE activity_id IN ('+','.join('?' for _ in candidates)+')) LIMIT 1',[r['activity_id'] for r in candidates]).fetchone()[0]
        links=dict(newest='/activities/'+choices[0]['activity_id'],overlap='/activities/'+overlap,
                   api_only=['/activities/'+r['activity_id'] for r in choices])
        (ROOT/'output/playwright/strava-004-review-links.json').write_text(json.dumps(links))
    assert originals=={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    return dict(status='passed',initial=first,restart_rerun=second,known_api_only_candidates=7,
                usable_api_only_graphs=usable,overlap_sources_from_existing_cache=4,stream_source_observations=sources_before,
                schema_version=6,accepted_database_tables_unchanged=True,originals_unchanged=True,
                no_native_reads_during_catchup=True,no_archive_reimports=True,no_hidden_rebuild=True,
                performance_eligible=1022,performance_pending=0,integrity=True,foreign_keys=True,rate_limits=client.rate)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--stage-a-cache',type=Path,required=True)
    args=parser.parse_args()
    try:result=verify(args.data_dir,args.baseline,args.stage_a_cache)
    except Exception as error:
        print('STRAVA-004 verification stopped ('+type(error).__name__+'); inspect locally without publishing private data.',file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result,indent=2))
