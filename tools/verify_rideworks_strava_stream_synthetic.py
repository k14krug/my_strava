#!/usr/bin/env python3
"""Normal Settings sync adds a synthetic gap/missing/zero chart; no live API calls."""
from datetime import datetime,timezone
from io import BytesIO
import json
from pathlib import Path
import sys
import threading
import argparse
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.performance import performance_history,rebuild_performance
from rideworks.settings import Settings
from rideworks.store import Store
from rideworks.strava import ApiClient,TokenFile
from rideworks.strava_api import apply_observations,normalize
from rideworks.strava_streams import persist
from rideworks.web import create_server
from verify_rideworks_strava_settings_ui import fixture,browser
from verify_rideworks_strava_stream_ui import verify as verify_chart


def verify(root,session):
    observations,current,original=fixture(root)
    now=int(datetime.now(timezone.utc).timestamp())
    payload={key:dict(data=data,original_size=5,resolution='high',series_type='time') for key,data in
             [('time',[0,1,2,8,9]),('watts',[0,120,None,140,0]),('heartrate',[None,0,100,None,105]),
              ('cadence',[0,80,None,85,0]),('moving',[False,True,True,True,False])]}
    with Store(root) as store:
        apply_observations(store,[normalize(observations[0])],42,now-10)
        persist(store,1,payload);rebuild_performance(store)  # Synthetic fixture setup only.
    TokenFile(root).save(dict(access_token='synthetic-only-access',refresh_token='synthetic-only-refresh',
                             expires_at=now+7200,athlete_id=42,scope='activity:read_all'))
    requests=[]
    class Response(BytesIO):status=200;headers={}
    class FakeHTTP:
        def open(self,request,timeout):
            path=urlsplit(request.full_url).path;requests.append(path)
            result=payload if path.endswith('/streams') else observations
            return Response(json.dumps(result).encode())
    def factory(data_dir):return Settings(data_dir,credentials=lambda:('123','synthetic-only-secret'),client_factory=lambda creds:ApiClient(creds,opener=FakeHTTP()))
    with create_server(root,8774,settings_factory=factory) as server:
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            browser('''async(page)=>{
              const base='http://127.0.0.1:8774';const check=(v,m)=>{if(!v)throw new Error(m);};
              await page.goto(base+'/settings');await page.getByRole('button',{name:'Sync now',exact:true}).click();
              check((await page.locator('#strava-outcome').textContent())==='1 new · 0 enriched · 1 unchanged','Metadata result');
              check((await page.locator('body').textContent()).includes('Graphs added for 1'),'Normal sync stream result');
              await page.getByRole('link',{name:'View Activities',exact:true}).click();
              await page.locator('.activity-row').first().click();await page.waitForSelector('.chart-power');
              const power=await page.locator('.chart-power').getAttribute('d');
              check((power.match(/M/g)||[]).length===2,'Power line bridged a missing value/gap');
              check(await page.locator('.chart-power').getAttribute('data-api-points')==='4','Zero watts dropped');
              check(await page.locator('.chart-hr').getAttribute('data-api-points')==='3','HR missing/zero changed');
              await page.goto(base+'/settings');
              check(await page.locator('.performance-update').count()===0,'Automatic Performance convergence');
              check((await page.locator('#performance-sync-outcome').textContent()).includes('Performance updated'),'Sync outcome');return true;
            }''',session)
        finally:server.shutdown();thread.join()
    with Store(root) as store:
        only=store.connection.execute("SELECT activity_id FROM strava_api_activities WHERE external_id='2'").fetchone()[0]
        assert performance_history(store)['pending']==0
        assert sum(path.endswith('/streams') for path in requests)==1
        links=dict(newest='/activities/'+only,overlap='/activities/'+current['activity_id'],api_only=['/activities/'+only])
    result=verify_chart(root,links,session)
    return result|dict(normal_settings_sync_enriches_new=True,sequential_stream_requests=1,zero_missing_gap_paths_verified=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--synthetic-dir',type=Path,required=True)
    parser.add_argument('--session',default='rideworks-strava-004');args=parser.parse_args()
    print(json.dumps(verify(args.synthetic_dir,args.session),indent=2))
