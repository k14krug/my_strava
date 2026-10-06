#!/usr/bin/env python3
"""Aggregate Chromium output; synthetic review routes remain in ignored local artifacts."""
import argparse
import json
from pathlib import Path
import subprocess


def verify(port,session):
    links=json.loads(Path('output/playwright/p2-05-synthetic-links.json').read_text())
    code=Path(__file__).with_suffix('.js').read_text().replace('BASE_URL',json.dumps(f'http://127.0.0.1:{port}')).replace('REVIEW_LINKS',json.dumps(links))
    result=subprocess.run(['npx','--offline','--yes','--package','@playwright/cli','playwright-cli','-s='+session,'run-code',code],capture_output=True,text=True)
    if result.returncode or '### Error' in result.stdout:
        Path('output/playwright/p2-05-verification-error.log').write_text(result.stdout+result.stderr)
        raise RuntimeError('Chromium failed; inspect ignored output/playwright/p2-05-verification-error.log')
    return json.loads(result.stdout.split('### Result\n',1)[1].split('### Ran Playwright code',1)[0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8773)
    parser.add_argument('--session',default='rideworks-p2-05');args=parser.parse_args()
    print(json.dumps(verify(args.port,args.session),indent=2))
