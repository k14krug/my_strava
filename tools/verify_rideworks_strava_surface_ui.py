#!/usr/bin/env python3
"""Live post-export reachability/order and explicit rebuild; publishes aggregates only."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import threading
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.history import browse, presentation
from rideworks.performance import performance_history
from rideworks.store import Store
from rideworks.web import create_server
from verify_rideworks_strava_settings_ui import browser


def verify(data_dir,baseline,port,session):
    with Store(baseline) as accepted, Store(data_dir) as store:
        original_ids={r[0] for r in accepted.connection.execute('SELECT activity_id FROM activities')}
        cutoff=max(r['date_key'] for r in browse(accepted)['rows'] if r['date_key'])
        new=[presentation(s) for s in store.activity_history() if s['activity']['activity_id'] not in original_ids]
        assert len(new)==7 and all(r['absolute_time'] and r['date_key']>cutoff for r in new)
        assert all(all(e['source']['kind']=='strava_api' for e in r['sources']) for r in new)
        overlaps=store.connection.execute('''SELECT a.activity_id FROM strava_api_activities a
            JOIN strava_export_sources e ON e.external_id=a.external_id''').fetchall()
        assert len(overlaps)==4 and all(r[0] in original_ids for r in overlaps)
        assert not store.connection.execute('''SELECT 1 FROM strava_api_activities a
            JOIN strava_export_sources e ON e.external_id=a.external_id WHERE a.activity_id!=e.activity_id''').fetchall()
        counts=browse(store);assert counts['total']==1441 and counts['count']==1417
        newest={r['activity_id'] for r in counts['rows'][:7]}
        assert newest=={r['activity_id'] for r in new}
        pending=performance_history(store)['pending'];assert pending==11
        private=[dict(route='/activities/'+r['activity_id'], instant=r['start_time']) for r in new]
    result={}
    base=f'http://127.0.0.1:{port}'
    def run(code):
        return browser('async(page)=>{const base='+json.dumps(base)+";const check=(v,m)=>{if(!v)throw new Error(m);};"+code+'}',session)
    with create_server(data_dir,port) as server:
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            for zone in ('America/Los_Angeles','Asia/Tokyo'):
                rows=[r|dict(day=datetime.fromisoformat(r['instant']).astimezone(ZoneInfo(zone)).date().isoformat(),
                             display=datetime.fromisoformat(r['instant']).astimezone(ZoneInfo(zone)).strftime('%b %-d, %Y, %-I:%M %p')) for r in private]
                run('''
                  const context=await page.context().browser().newContext({timezoneId:ZONE,locale:'en-US'});
                  const local=await context.newPage();try{
                    await local.goto(base+'/?tz='+encodeURIComponent(ZONE));await local.waitForSelector('.activity-row time');
                    const links=await local.locator('.activity-row').evaluateAll(elements=>elements.map(e=>e.getAttribute('href')));
                    check(ROWS.every(r=>links.slice(0,7).includes(r.route)),'Live new Activities missing from newest top seven');
                    for(const row of ROWS){
                      const item=local.locator('a.activity-row[href="'+row.route+'"]');
                      check(await item.locator('time').getAttribute('data-local-day')===row.day,'Live local calendar date');
                      check((await item.locator('time').textContent()).replaceAll('\\u202f',' ')===row.display,'Live local Date display');
                      await item.click();await local.waitForSelector('.review-unavailable');
                      check(await local.locator('#ride-chart,.best-value').count()===0,'API summaries became native analysis');
                      check(await local.locator('.performance-update').count()===1,'Review reminder missing');
                      await local.goBack();await local.waitForSelector('.activity-row');
                    }
                    await local.goto(base+'/?sort=oldest&tz='+encodeURIComponent(ZONE));await local.waitForSelector('.activity-row');
                    const old=await local.locator('.activity-row').evaluateAll(elements=>elements.map(e=>e.getAttribute('href')));
                    check(ROWS.every(r=>!old.includes(r.route)),'Live newest Activity appears on oldest first page');
                  }finally{await context.close();}return true;
                '''.replace('ZONE',json.dumps(zone)).replace('ROWS',json.dumps(rows)))
            run('''
              await page.goto(base+'/settings');check(await page.locator('.performance-update').count()===1,'Restart reminder missing');
              const notice=await page.locator('.performance-update').textContent();check(notice.includes('11 Activities'),'Affected count');
              await page.getByRole('button',{name:'Rebuild Performance',exact:true}).click({timeout:180000});
              await page.waitForURL(base+'/settings',{timeout:180000});
              check(await page.locator('.performance-update').count()===0,'Explicit live rebuild did not clear reminder');
              check((await page.locator('#strava-notice').textContent()).includes('1,441 Activities evaluated'),'Live rebuild result');
              await page.screenshot({path:'output/playwright/p2-05-live-rebuild-result.png',fullPage:true});
              for(const path of ['/','/performance',FIRST]){
                await page.goto(base+path);check(await page.locator('.performance-update').count()===0,'Resolved reminder remains');
              }return true;
            '''.replace('FIRST',json.dumps(private[0]['route'])))
            with Store(data_dir) as store:
                state=performance_history(store);assert state['pending']==0 and len(state['points'])==1022
                assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
                result=dict(status='passed',new_api_only_activities=7,all_absolute_dates=True,all_non_null_date_keys=True,
                            all_post_baseline=True,newest_top_seven_are_new=True,individually_browser_reachable=7,
                            los_angeles_tokyo_display_and_sort=True,cycling_count=1417,activity_count=1441,
                            established_id_overlap_enrichments=4,overlap_duplicates=0,
                            pending_before_explicit_rebuild=pending,pending_after_explicit_rebuild=0,
                            rebuild_evaluated=state['evaluated'],current_eligible_performance=len(state['points']),
                            reminder_cleared_all_pages=True,integrity=True,foreign_keys=True)
        finally:
            server.shutdown();thread.join()
    # Process/server restart independently proves the resolved reminder stays gone.
    from rideworks.web import Application
    assert b'Performance update needed' not in Application(data_dir).get('/settings')[2]
    return result|dict(resolved_reminder_stays_gone_after_restart=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8774);parser.add_argument('--session',default='rideworks-p2-05')
    args=parser.parse_args();print(json.dumps(verify(args.data_dir,args.baseline,args.port,args.session),indent=2))
