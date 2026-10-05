#!/usr/bin/env python3
"""Aggregate browser verification using local-only review links and Chromium."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.web import recent_context_panel, shell


def synthetic_cases(base):
    """Render the production panel with synthetic equal/sub-watt evidence."""
    cases=[]
    for current,prior,current_display,prior_display,expected in [
        (120,120,120,120,'Same displayed watts'),
        (120.4,119.6,120,120,'Same displayed watts'),
        (120.51,120.49,121,120,'1 W above'),
        (119.49,119.51,119,120,'1 W below')]:
        def point(identity,raw,display):
            return dict(activity_id=identity,source_id='synthetic-source-'+identity,
                        extraction_id='synthetic-extraction-'+identity,average_watts=raw,
                        rounded_watts=display,absolute_time=True,
                        start_time=('2024-01-02' if identity=='current' else '2024-01-01')+'T00:00:00+00:00',
                        title='Synthetic ride')
        context=dict(current=point('current',current,current_display),prior=point('prior',prior,prior_display),
                     activity_id='current',policy='virtual-native-power-v1',method='best-average-power-v1',
                     duration_seconds=1200,window_start='2023-12-20T00:00:00+00:00',
                     window_end='2024-01-02T00:00:00+00:00',reason=None,pending_history=0)
        html=shell('Synthetic comparison verification',recent_context_panel(context))
        html=html.replace('<head>','<head><base href="'+base+'/">')
        cases.append(dict(html=html,current=current_display,prior=prior_display,expected=expected,
                          current_raw=current,prior_raw=prior))
    return cases


def verify(port,session):
    links=json.loads(Path('output/playwright/p2-04-review-links.json').read_text())
    base=f'http://127.0.0.1:{port}'
    code=Path(__file__).with_suffix('.js').read_text().replace('BASE_URL',json.dumps(base)).replace('REVIEW_LINKS',json.dumps(links)).replace('SYNTHETIC_CASES',json.dumps(synthetic_cases(base)))
    result=subprocess.run(['npx','--offline','--yes','--package','@playwright/cli','playwright-cli','-s='+session,'run-code',code],capture_output=True,text=True)
    if result.returncode or '### Error' in result.stdout:
        Path('output/playwright/p2-04-verification-error.log').write_text(result.stdout+result.stderr)
        raise RuntimeError('Chromium failed; inspect ignored output/playwright/p2-04-verification-error.log')
    return json.loads(result.stdout.split('### Result\n',1)[1].split('### Ran Playwright code',1)[0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8769)
    parser.add_argument('--session',default='rideworks-p2-04');args=parser.parse_args()
    print(json.dumps(verify(args.port,args.session),indent=2))
