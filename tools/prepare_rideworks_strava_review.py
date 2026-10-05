#!/usr/bin/env python3
"""Copied-history migration and isolated synthetic sync/browser evidence; no Strava calls."""
import argparse
import csv
from hashlib import sha256
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from fit_fixture import make_fit
from rideworks.store import Store
from rideworks.performance import performance_history,rebuild_performance
from rideworks.strava import ApiClient,TokenFile,sync


def saved(database):
    tables=('activities','sources','extractions','sessions','records','laps','events','strava_export_sources',
            'export_snapshots','export_row_locations','fit_lap_timestamps','xml_context','performance_history')
    result={}
    for table in tables:
        digest=sha256();count=0
        for row in database.execute('SELECT * FROM '+table+' ORDER BY rowid'):
            digest.update(json.dumps(tuple(row),ensure_ascii=True).encode()+b'\n');count+=1
        result[table]=(count,digest.hexdigest())
    return result


def prepare(data_dir,synthetic_dir):
    with sqlite3.connect(data_dir/'rideworks.sqlite3') as database:before=saved(database)
    originals={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    with Store(data_dir) as store:
        assert saved(store.connection)==before
        history=performance_history(store)
        assert history['evaluated']==1434 and history['pending']==0 and len(history['points'])==1022
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
    assert {p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}==originals
    assert not synthetic_dir.exists(),'Use a new isolated synthetic directory; never overwrite a review store'
    now=int(datetime.now(timezone.utc).timestamp())
    with Store(synthetic_dir) as store:
        native=[]
        for offset,watts in [(-172800,180),(-86400,120)]:
            raw=now+offset-631065600
            path=synthetic_dir/f'synthetic-{watts}.fit'
            path.write_bytes(make_fit(powers=[watts]*1200,heart_rates=[100]*1200,timestamps=range(raw,raw+1200),
                                     session_start_time=raw,session_timestamp=raw+1200,elapsed=1200,timer=1200))
            native.append(store.import_fit(path))
        current=native[-1];snapshot=store.get_source(current['source_id']);start=snapshot['summary']['start_time']
        export=synthetic_dir/'synthetic-export';(export/'activities').mkdir(parents=True)
        (export/'activities/synthetic.fit').write_bytes((synthetic_dir/'synthetic-120.fit').read_bytes())
        with (export/'activities.csv').open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['Activity ID','Activity Name','Activity Type','Activity Date','Filename'])
            writer.writerow(['1','Synthetic export title','Virtual Ride',datetime.fromisoformat(start).strftime('%b %d, %Y, %I:%M:%S %p'),'activities/synthetic.fit'])
        store.import_strava_export(export)
        rebuild_performance(store)  # Synthetic fixture setup only; never rebuild real history here.
        history_before=[tuple(r) for r in store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id')]
        TokenFile(synthetic_dir).save(dict(access_token='synthetic-only-access',refresh_token='synthetic-only-refresh',expires_at=now+7200,athlete_id=42,scope='activity:read_all'))
        observations=[dict(id=1,name='Synthetic API enriched ride',type='Ride',sport_type='VirtualRide',start_date=start,
                           elapsed_time=1200,distance=0,average_watts=999),
                      dict(id=2,name='Synthetic API-only ride',type='Ride',sport_type='VirtualRide',
                           start_date=datetime.fromtimestamp(now-3600,timezone.utc).isoformat(),elapsed_time=1200,
                           distance=1000,average_watts=999,start_latlng=[1,2],map={'summary_polyline':'not retained'})]
        class FakeResponse(BytesIO):
            status=200;headers={}
        class FakeHTTP:
            def open(self,request,timeout):
                assert request.full_url.startswith('https://www.strava.com/api/v3/athlete/activities?')
                return FakeResponse(json.dumps(observations).encode())
        client=ApiClient(('123','synthetic-only-client-secret'),opener=FakeHTTP())
        def guard(action,table,*args):
            if action==sqlite3.SQLITE_READ and table in ('records','laps','events'):return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        store.connection.set_authorizer(guard)
        try:
            with patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('hidden rebuild')),patch.object(Store,'import_strava_export',side_effect=AssertionError('archive')),patch.object(Store,'reextract',side_effect=AssertionError('reparse')):
                first=sync(store,client,now=now)
        finally:store.connection.set_authorizer(lambda *args:sqlite3.SQLITE_OK)
        assert first['new_activities']==1 and first['existing_activities_enriched']==1
        assert store.get_source(current['source_id'])==snapshot
        assert [tuple(r) for r in store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id')]==history_before
        api_only=store.connection.execute("SELECT activity_id FROM strava_api_activities WHERE external_id='2'").fetchone()[0]
        snapshot_before=store.activity_history()
    with Store(synthetic_dir) as restarted:
        second=sync(restarted,client,now=now+1)
        assert second['new_activities']==0 and second['new_observations']==0 and second['unchanged_observations']==2
        assert restarted.activity_history()==snapshot_before
        assert restarted.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not restarted.connection.execute('PRAGMA foreign_key_check').fetchall()
    private=ROOT/'output/playwright/p2-05-synthetic-links.json';private.parent.mkdir(parents=True,exist_ok=True)
    private.write_text(json.dumps(dict(rich='/activities/'+current['activity_id'],thin='/activities/'+api_only)))
    return dict(status='passed',live_sync='not_run_by_this_synthetic_verifier',schema_version=5,historical_activities=1434,
                eligible_history=1022,historical_tables_unchanged=True,originals_unchanged=True,integrity=True,foreign_keys=True,
                synthetic=dict(initial=first,restart_rerun=second,activity_count=3,unchanged_native_fit=True,
                               unchanged_persisted_performance=True,no_native_reads_during_sync=True,no_archive_reprocessing=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--synthetic-dir',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.data_dir,args.synthetic_dir),indent=2))
