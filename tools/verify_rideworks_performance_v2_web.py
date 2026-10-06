#!/usr/bin/env python3
"""One live Settings sync on an already-current v2 store; aggregate output only."""
import argparse
import json
from pathlib import Path
import sys
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rideworks.config import strava_credentials
from rideworks.performance import performance_history
from rideworks.settings import Settings
from rideworks.store import Store
from rideworks.strava import ApiClient, sync
from rideworks.web import create_server
from compare_rideworks_strava_streams import fingerprint
from verify_rideworks_strava_settings_ui import browser


def verify(data_dir, session):
    with Store(data_dir) as store:
        before = fingerprint(store.connection)
        history = performance_history(store)
        assert len(history['points']) == 1027 and history['pending'] == 0
    client = ApiClient(strava_credentials())
    observed = []

    def capture(store, api):
        result = sync(store, api)
        observed.append(result)
        return result

    server = create_server(data_dir, 0, settings_factory=lambda root: Settings(
        root, client_factory=lambda credentials: client))
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    code = '''async(page)=>{
      const base=BASE; const check=(v,m)=>{if(!v)throw new Error(m);};
      await page.unrouteAll({behavior:'wait'}); await page.goto(base+'/settings');
      check(await page.locator('#strava-connection').textContent()==='Connected','Live connection');
      await page.getByRole('button',{name:'Sync now',exact:true}).click();
      await page.waitForURL(base+'/settings');
      check((await page.locator('#performance-sync-outcome').textContent()).includes('Performance is current'),'Live sync convergence');
      check(await page.locator('.performance-update').count()===0,'Routine update banner');
      await page.goto(base+'/performance');
      check(JSON.parse(await page.locator('#performance-points').textContent()).length===1027,'Live cohort');
      check(await page.locator('.performance-update').count()===0,'Current Performance banner');
      return true;
    }'''.replace('BASE', json.dumps(base))
    try:
        with patch('rideworks.settings.sync', side_effect=capture), patch(
                'rideworks.performance.rebuild_performance', side_effect=AssertionError('Unnecessary live web rebuild')):
            assert browser(code, session)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    assert len(observed) == 1
    result = observed[0]
    assert result['performance_update'] == 'current' and result['new_observations'] == 0
    assert result['pages_requested'] == 1 and client.stream_requests == 0
    with Store(data_dir) as store:
        after = fingerprint(store.connection)
        assert all(before[k] == after[k] for k in before if k != 'strava_sync_state')
        assert performance_history(store) == history
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
    assert Settings(data_dir).state()['performance_update'] == 'current'
    return dict(status='passed', real_settings_sync=True, sync=result, unnecessary_rebuild_skipped=True,
                stream_gets=0, performance_and_source_tables_unchanged=True,
                outcome_persisted_for_restart=True, eligible=1027, pending=0,
                no_exception_banner=True, integrity=True, foreign_keys=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--session', default='rideworks-strava-004')
    args = parser.parse_args()
    try:
        result = verify(args.data_dir, args.session)
    except Exception as error:
        print('Live web verification stopped ('+type(error).__name__+'); inspect ignored browser evidence locally.', file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))
