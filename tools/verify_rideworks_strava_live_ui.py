#!/usr/bin/env python3
"""Explicit live Settings/restart/rerun check on a disposable, already connected store.

No OAuth login automation. Reports only aggregates; source IDs/titles/paths and tokens
stay local. Run only after the Owner authorizes the store's Strava connection.
"""
import argparse
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import sys
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rideworks.config import strava_credentials
from rideworks.performance import performance_history
from rideworks.settings import Settings
from rideworks.store import Store
from rideworks.strava import TokenFile, sync
from rideworks.web import create_server
from prepare_rideworks_strava_review import saved
from verify_rideworks_strava_settings_ui import browser


def verify(data_dir, baseline, port, session):
    private = TokenFile(data_dir).read()
    credentials = strava_credentials()
    secrets = [private['access_token'], private['refresh_token'], credentials[1]]
    with Store(baseline) as accepted, Store(data_dir) as store:
        expected = saved(accepted.connection)
        before = saved(store.connection)
        # The live store can add Activities; every accepted row must remain intact.
        for table in expected:
            if table != 'activities':
                assert expected[table] == before[table], 'Accepted historical table changed'
        originals = {tuple(row) for row in accepted.connection.execute('SELECT * FROM activities')}
        assert originals.issubset({tuple(row) for row in store.connection.execute('SELECT * FROM activities')})
        api_before = [tuple(row) for row in store.connection.execute('SELECT * FROM strava_api_sources ORDER BY source_id')]
    original_files = {p.name:(p.stat().st_size, p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    assert original_files == {p.name:(p.stat().st_size, p.stat().st_mtime_ns) for p in (baseline/'originals').iterdir()}, 'Accepted originals differ'
    settings = Settings(data_dir)
    observed_initial = settings.state()
    reports = []
    def guarded_sync(store, client):
        def deny_native(action, table, *args):
            if action == sqlite3.SQLITE_READ and table in ('records', 'laps', 'events'):
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        store.connection.set_authorizer(deny_native)
        try:
            with (patch.object(Store, 'import_strava_export', side_effect=AssertionError('Archive reprocessing')),
                 patch.object(Store, 'reextract', side_effect=AssertionError('Source reparse')),
                 patch('rideworks.performance.rebuild_performance', side_effect=AssertionError('Implicit rebuild'))):
                result = sync(store, client)
                reports.append(result)
                return result
        finally:
            store.connection.set_authorizer(lambda *args: sqlite3.SQLITE_OK)
    base = f'http://127.0.0.1:{port}'
    for iteration in range(2):
        with patch('rideworks.settings.sync', side_effect=guarded_sync), create_server(data_dir, port) as server:
            thread = threading.Thread(target=server.serve_forever); thread.start()
            try:
                code = '''async(page)=>{
                  const base=BASE;const check=(v,m)=>{if(!v)throw new Error(m);};
                  await page.goto(base+'/settings');
                  check(await page.locator('#strava-connection').textContent()==='Connected','Restart lost authorization');
                  check(await page.locator('#strava-credentials').textContent()==='Configured','Credentials unavailable');
                  check(await page.locator('#strava-last-sync time').count()===1,'Successful-sync time missing');
                  await page.getByRole('button',{name:'Sync now',exact:true}).click();
                  await page.waitForSelector('#strava-outcome');
                  check(await page.locator('#strava-connection').textContent()==='Connected','Live sync lost connection');
                  check(!page.url().includes('code='),'Callback code URL');
                  check(await page.evaluate(()=>localStorage.length===0&&sessionStorage.length===0),'Browser storage');
                  await page.screenshot({path:'output/playwright/p2-05-live-settings-rerun.png',fullPage:true});
                  await page.getByRole('link',{name:'Activities',exact:true}).click();
                  await page.waitForSelector('.activity-row');
                  check(await page.locator('.activity-row').count()===30,'Activities page unavailable');
                  return {connected_after_restart:true,sync_completed:true,activities_available_without_restart:true,no_browser_secrets:true};
                }'''.replace('BASE', json.dumps(base))
                # The CLI prints code internally; capture it locally, never forward it.
                browser(code, session)
                connection = HTTPConnection('127.0.0.1', port, timeout=5)
                try:
                    connection.request('GET', '/settings')
                    response = connection.getresponse(); markup = response.read().decode()
                    current_token = TokenFile(data_dir).read()
                    private_values = secrets + [current_token['access_token'], current_token['refresh_token']]
                    assert response.status == 200 and all(value not in markup for value in private_values), 'Private value in Settings markup'
                finally:
                    connection.close()
            finally:
                server.shutdown(); thread.join()
        assert len(reports) == iteration+1, 'Live sync did not complete'
        assert reports[-1]['new_activities'] == 0 and reports[-1]['new_observations'] == 0, 'Live rerun changed observations; report for review'
    with Store(data_dir) as store:
        assert before == saved(store.connection), 'Historical rows changed during rerun'
        assert api_before == [tuple(row) for row in store.connection.execute('SELECT * FROM strava_api_sources ORDER BY source_id')], 'Observations changed during rerun'
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
        counts = dict(activities=store.connection.execute('SELECT COUNT(*) FROM activities').fetchone()[0],
                      api_observations=store.connection.execute('SELECT COUNT(*) FROM strava_api_sources').fetchone()[0])
        history = performance_history(store)
    assert original_files == {p.name:(p.stat().st_size, p.stat().st_mtime_ns) for p in (data_dir/'originals').iterdir()}
    return dict(status='passed',mode='live_already_authorized_settings_manual_rerun',
                observed_initial_web_result=observed_initial,reruns=reports,**counts,
                connected_after_server_restart=True,activities_available_without_restart=True,
                browser_privacy=True,no_native_reads_during_sync=True,no_archive_reprocessing=True,
                no_hidden_performance_rebuild=True,historical_tables_and_originals_unchanged=True,
                new_observations_on_rerun=0,integrity=True,foreign_keys=True,
                current_eligible_performance=len(history['points']),performance_pending=history['pending'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8774)
    parser.add_argument('--session', default='rideworks-p2-05')
    args = parser.parse_args()
    print(json.dumps(verify(args.data_dir, args.baseline, args.port, args.session), indent=2))
