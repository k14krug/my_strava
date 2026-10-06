#!/usr/bin/env python3
"""Actual Chromium API chart/source/timing checks; private routes stay local."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys
import threading
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.analysis import analyze_activity
from rideworks.performance import performance_history
from rideworks.store import Store
from rideworks.web import create_server
from verify_rideworks_strava_settings_ui import browser


def verify(data_dir,links,session,port=8774,*,live=False):
    with Store(data_dir) as store:
        baseline=performance_history(store)
        current=next(s for s in store.strava_stream_evidence(links['newest'].split('/')[-1]) if s['is_current'])
        stamp=datetime.fromisoformat(current['start_date'].replace('Z','+00:00'))
        native=analyze_activity(store,links['overlap'].split('/')[-1])
        native_points=len(native['native_records']);best=native['best_20_minute_power']['rounded_watts']
        offsets=current['streams']['time']['data']
        power=current['streams'].get('watts',{}).get('data',[None]*len(offsets))
        hr=current['streams'].get('heartrate',{}).get('data',[None]*len(offsets))
        expected=[dict(sample_index=i,time_offset=t,power=power[i],heart_rate=hr[i]) for i,t in enumerate(offsets)]
        graph_checks=[]
        for route in links['api_only']:
            observed=next(s for s in store.strava_stream_evidence(route.split('/')[-1]) if s['is_current'])
            times=observed['streams']['time']['data']
            watts=observed['streams'].get('watts',{}).get('data',[None]*len(times))
            hearts=observed['streams'].get('heartrate',{}).get('data',[None]*len(times))
            samples=[dict(sample_index=i,time_offset=t,power=watts[i],heart_rate=hearts[i]) for i,t in enumerate(times)]
            graph_checks.append(dict(route=route,count=len(times),first=times[0],last=times[-1],
                power_count=sum(v is not None for v in watts),hr_count=sum(v is not None for v in hearts),
                payload_hash=sha256(json.dumps(samples,separators=(',',':')).encode()).hexdigest()))
    expected_hash=sha256(json.dumps(expected,separators=(',',':')).encode()).hexdigest()
    base=f'http://127.0.0.1:{port}'
    def run(code):
        return browser('async(page)=>{const base='+json.dumps(base)+";const check=(v,m)=>{if(!v)throw new Error(m);};"+code+'}',session)
    def start():
        server=create_server(data_dir,port);thread=threading.Thread(target=server.serve_forever);thread.start();return server,thread
    def stop(server,thread):server.shutdown();thread.join();server.server_close()
    server,thread=start()
    try:
        run('''
          await page.goto(base+NEWEST);await page.waitForSelector('.chart-power',{state:'attached'});
          check(await page.locator('#native-records,.best-value').count()===0,'API evidence became native/best20');
          const text=await page.locator('.source-caption').first().textContent();check(text.includes('Strava API stream evidence'),'Chart label');
          const samples=JSON.parse(await page.locator('#api-stream-samples').textContent());
          check(samples.length===COUNT,'Returned samples dropped/invented');
          const digest=await page.evaluate(async()=>{const samples=JSON.parse(document.querySelector('#api-stream-samples').textContent);
            const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(samples)));
            return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');});
          check(digest===HASH,'Returned source values/order differ in browser payload');
          check(samples[0].time_offset===FIRST&&samples.at(-1).time_offset===LAST,'Returned offsets altered');
          check(await page.locator('.chart-power').getAttribute('data-api-points')===String(POWER_COUNT),'Power samples changed');
          check(await page.locator('.chart-hr').getAttribute('data-api-points')===String(HR_COUNT),'HR samples changed');
          check(await page.locator('[data-native-points]').count()===0,'API points labelled native');
          await page.locator('#chart-svg').focus();await page.keyboard.press('Home');
          check(await page.locator('#sample-readout').getAttribute('data-sample-index')==='0','API inspection origin');
          await page.keyboard.press('End');check(await page.locator('#sample-readout').getAttribute('data-sample-index')===String(COUNT-1),'API inspection final sample');
          await page.locator('.stream-provenance summary').first().click();
          check((await page.locator('.stream-provenance').textContent()).includes('original_size'),'Metadata provenance');
          check((await page.locator('.stream-provenance').textContent()).includes('Retrieved at'),'Retrieval provenance');
          await page.screenshot({path:'output/playwright/strava-004-api-desktop.png',fullPage:true});
          await page.setViewportSize({width:390,height:844});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'API phone overflow');
          await page.screenshot({path:'output/playwright/strava-004-api-phone.png',fullPage:true});
          await page.goto(base+OVERLAP);await page.waitForSelector('.chart-power',{state:'attached'});
          check(await page.locator('#api-stream-samples').count()===0,'FIT graph displaced');
          check(JSON.parse(await page.locator('#native-records').textContent()).length===NATIVE_COUNT,'Native chart changed');
          check(await page.locator('.best-value').textContent()===BEST+' W','FIT best20 changed');
          check(await page.locator('.stream-provenance').count()>=1,'Additional overlap evidence absent');
          check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'FIT phone overflow');return true;
        '''.replace('NEWEST',json.dumps(links['newest'])).replace('OVERLAP',json.dumps(links['overlap']))
          .replace('NATIVE_COUNT',str(native_points)).replace('POWER_COUNT',str(sum(v is not None for v in power)))
          .replace('HR_COUNT',str(sum(v is not None for v in hr))).replace('COUNT',str(len(offsets)))
          .replace('HASH',json.dumps(expected_hash)).replace('FIRST',str(offsets[0])).replace('LAST',str(offsets[-1])).replace('BEST',str(best)))
        for zone in ('America/Los_Angeles','Asia/Tokyo'):
            day=stamp.astimezone(ZoneInfo(zone)).date().isoformat()
            run('''
              const context=await page.context().browser().newContext({timezoneId:ZONE,locale:'en-US'});
              const local=await context.newPage();try{
                await local.goto(base+NEWEST);await local.waitForSelector('.chart-power',{state:'attached'});
                check(await local.locator('.ride-meta time').getAttribute('data-local-day')===DAY,'API chart local date');
                check(!(await local.locator('.ride-meta time').textContent()).includes('GMT'),'Compact chart date suffix');
                await local.locator('#chart-svg').focus();await local.keyboard.press('Home');
                check(!(await local.locator('#sample-readout').textContent()).includes('Invalid Date'),'API absolute mapping');
              }finally{await context.close();}return true;
            '''.replace('ZONE',json.dumps(zone)).replace('NEWEST',json.dumps(links['newest'])).replace('DAY',json.dumps(day)))
        stop(server,thread);server,thread=start()
        run('''
          await page.setViewportSize({width:1448,height:1086});await page.goto(base+NEWEST);await page.waitForSelector('.chart-power',{state:'attached'});
          check(await page.locator('#api-stream-samples').count()===1,'Restart lost API chart');
          await page.goto(base+'/performance');
          check(JSON.parse(await page.locator('#performance-points').textContent()).length===ELIGIBLE,'Trusted cohort changed');
          await page.goto(base+'/settings');check(await page.locator('#strava-connection').textContent()==='Connected','Restart lost connection');
          check(await page.locator('.performance-update').count()===0,'Streams staled Performance');
          for(const graph of GRAPHS){
            await page.goto(base+graph.route);await page.waitForSelector('.chart-power',{state:'attached'});
            check(await page.locator('#native-records,.best-value').count()===0,'API graph claimed native/best20');
            check((await page.locator('.source-caption').first().textContent()).includes('Strava API stream evidence'),'API graph source label');
            const samples=JSON.parse(await page.locator('#api-stream-samples').textContent());
            check(samples.length===graph.count&&samples[0].time_offset===graph.first&&samples.at(-1).time_offset===graph.last,'API graph sample count/offsets');
            const digest=await page.evaluate(async()=>{const samples=JSON.parse(document.querySelector('#api-stream-samples').textContent);
              const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(samples)));
              return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');});
            check(digest===graph.payload_hash,'API graph values/order');
            check(await page.locator('.chart-power').getAttribute('data-api-points')===String(graph.power_count),'API graph power count');
            check(await page.locator('.chart-hr').getAttribute('data-api-points')===String(graph.hr_count),'API graph HR count');
          }
          return true;
        '''.replace('NEWEST',json.dumps(links['newest'])).replace('ELIGIBLE',str(len(baseline['points'])))
          .replace('GRAPHS',json.dumps(graph_checks)))
        with Store(data_dir) as store:
            assert performance_history(store)==baseline
            actual=next(s for s in store.strava_stream_evidence(links['newest'].split('/')[-1]) if s['is_current'])
            assert actual==current
        return dict(status='passed',mode='live' if live else 'synthetic',api_only_charts=len(links['api_only']),
                    complete_browser_payloads_verified=len(graph_checks),
                    source_labels_metadata=True,returned_offsets_and_samples_retained=True,power_hr_points_retained=True,
                    inspection_keyboard=True,no_native_or_trusted_best20_claim=True,fit_precedence_and_best20_unchanged=True,
                    overlap_streams_inspectable=True,los_angeles_tokyo_dates=True,desktop_phone_no_overflow=True,
                    restart_retains_graphs_and_connection=True,trusted_performance_unchanged=True,
                    performance_eligible=len(baseline['points']),performance_pending=baseline['pending'])
    finally:stop(server,thread)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--links',type=Path,default=Path('output/playwright/strava-004-review-links.json'))
    parser.add_argument('--session',default='rideworks-strava-004');parser.add_argument('--live',action='store_true')
    args=parser.parse_args();print(json.dumps(verify(args.data_dir,json.loads(args.links.read_text()),args.session,live=args.live),indent=2))
