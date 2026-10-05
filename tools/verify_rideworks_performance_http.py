#!/usr/bin/env python3
"""Full-history HTTP regression plus Performance process restart; aggregate only."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.performance import performance_history
from rideworks.store import Store
from tools.verify_rideworks_browser import get, require, verify as verify_browser


def verify(data_dir,representative,port):
    browser=verify_browser(data_dir,representative,port)
    with Store(data_dir) as store: expected=performance_history(store)['points']
    previous=None
    for _ in range(2):
        process=subprocess.Popen([sys.executable,'-m','rideworks','--data-dir',str(data_dir),
                                  'serve','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=monotonic()+10
            while True:
                try: status,html=get(port,'/performance'); break
                except OSError:
                    require(process.poll() is None and monotonic()<deadline,'Performance server failed to start')
                    sleep(.05)
            require(status==200,'Performance route failed')
            payload=html.split('<script id="performance-points" type="application/json">')[1].split('</script>')[0]
            points=json.loads(payload)
            require(points==expected,'Performance payload differs from persisted current history')
            require('id="native-records"' not in html,'Performance exposes native streams')
            for token in ('stored_path','latitude','longitude',str(data_dir),str(data_dir.resolve())):
                require(token not in html,'Private runtime/location evidence exposed')
            require(process.poll() is None,'Verification process does not own port')
            if previous is not None: require(points==previous,'Performance changed after process restart')
            previous=points
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    return dict(result='passed',performance_points=len(expected),performance_process_restart=True,
                performance_payload_matches_persistence=True,no_native_streams_or_private_paths=True,
                accepted_browser_and_activity_regression=browser)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',required=True,type=Path)
    parser.add_argument('--representative',required=True,type=Path)
    parser.add_argument('--port',type=int,default=8769)
    args=parser.parse_args()
    print(json.dumps(verify(args.data_dir,args.representative,args.port),indent=2))
