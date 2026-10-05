#!/usr/bin/env python3
"""Accepted browser regressions and recent-context HTTP process restart."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic,sleep

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store
from tools.verify_rideworks_browser import get, require, verify as verify_browser
from tools.verify_rideworks_recent_context import saved_rows


def verify(data_dir,representative,port):
    with Store(data_dir) as store:before=saved_rows(store)
    accepted=verify_browser(data_dir,representative,port)
    links=json.loads(Path('output/playwright/p2-04-review-links.json').read_text())
    previous=None
    for _ in range(2):
        process=subprocess.Popen([sys.executable,'-m','rideworks','--data-dir',str(data_dir),'serve','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=monotonic()+10
            while True:
                try:status,html=get(port,links['representative']);break
                except OSError:
                    require(process.poll() is None and monotonic()<deadline,'Recent-context server failed to start');sleep(.05)
            require(status==200 and process.poll() is None,'Recent-context verification process does not own route/port')
            require('id="recent-current-watts">120 W' in html,'Current result changed')
            require(f'id="recent-prior-watts">{links["representative_prior_watts"]} W' in html,'Prior result differs')
            require(f'href="{links["prior"]}"' in html,'Prior link differs')
            require('id="recent-performance" href="/performance"' in html,'Performance link missing')
            for key in ('no_prior','outdoor'):
                code,case=get(port,links[key]);require(code==200,'Unavailable review failed')
                require('data-recent-status="unavailable"' in case,'Unavailable case promoted to trusted context')
                require('id="recent-prior-activity"' not in case,'Unavailable case fabricates prior Activity')
            panel=html.split('<section class="recent-context"',1)[1].split('</section>',1)[0]
            for token in ('native_records','stored_path','latitude','longitude',str(data_dir.resolve())):
                require(token not in panel,'Comparison exposes native/runtime evidence')
            if previous is not None:require(panel==previous,'Recent context changed after process restart')
            previous=panel
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    with Store(data_dir) as store:require(saved_rows(store)==before,'HTTP startup/render changed persisted Performance history')
    return dict(result='passed',recent_context_process_restart=True,persisted_history_unchanged=True,
                available_unavailable_outdoor_verified=True,no_native_comparison_payload=True,
                accepted_browser_and_activity_regression=accepted)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--representative',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8770);args=parser.parse_args()
    print(json.dumps(verify(args.data_dir,args.representative,args.port),indent=2))
