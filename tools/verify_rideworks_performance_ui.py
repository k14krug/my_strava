#!/usr/bin/env python3
"""Aggregate Performance acceptance in an existing local Playwright CLI session."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store
from rideworks.performance import performance_history


def verify(data_dir,port,session):
    with Store(data_dir) as store:
        count=len(performance_history(store)['points'])
    code=Path(__file__).with_suffix('.js').read_text().replace('BASE_URL',json.dumps(f'http://127.0.0.1:{port}')).replace('EXPECTED_COUNT',str(count))
    result=subprocess.run(['npx','--offline','--yes','--package','@playwright/cli','playwright-cli',
                           '-s='+session,'run-code',code],capture_output=True,text=True)
    if result.returncode or '### Error' in result.stdout:
        path=Path('output/playwright/p2-03-verification-error.log');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(result.stdout+result.stderr)
        raise RuntimeError('Chromium verification failed; inspect ignored output/playwright/p2-03-verification-error.log')
    return json.loads(result.stdout.split('### Result\n',1)[1].split('### Ran Playwright code',1)[0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8768)
    parser.add_argument('--session',default='rideworks-p2-03')
    args=parser.parse_args()
    print(json.dumps(verify(args.data_dir,args.port,args.session),indent=2))
