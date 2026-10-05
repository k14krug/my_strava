#!/usr/bin/env python3
"""Run privacy-safe aggregate acceptance in an existing local Chromium CLI session.

Start RideWorks and a Playwright CLI browser session first. The CLI's private
snapshots/screenshots remain in ignored local artifact directories. Do not
publish its generated code or snapshots: they include private expected titles.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rideworks.history import presentation
from rideworks.store import Store


def verify(data_dir, representative, port, session):
    with Store(data_dir) as store:
        rows = [presentation(s) for s in store.activity_history()]
        digest = sha256(representative.read_bytes()).hexdigest()
        seed = next(r for r in rows if any(e['source'].get('sha256') == digest for e in r['sources']))
        samples = {'FIT': seed}
        for fmt in ('TCX', 'GPX'):
            samples[fmt] = next(r for r in rows if any(e['source']['content_format'] == fmt for e in r['sources']))
        samples['CSV-only'] = next(r for r in rows if all(e['source']['kind'] == 'strava_export' for e in r['sources']))
        samples = {fmt: {'id': row['activity_id'], 'title': row['title'], 'date': row['date_day'],
                         'start': row['start_time'], 'absolute': row['absolute_time']}
                   for fmt, row in samples.items()}
        boundary = next(row for row in rows if row['absolute_time'] and
                        datetime.fromisoformat(row['start_time']).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
                        != row['date_day'])
        boundary = dict(id=boundary['activity_id'], title=boundary['title'], start=boundary['start_time'])
    code = Path(__file__).with_suffix('.js').read_text()
    code = code.replace('SAMPLE_INPUT', json.dumps(samples)).replace('BASE_URL', json.dumps(f'http://127.0.0.1:{port}'))
    code = code.replace('BOUNDARY_INPUT', json.dumps(boundary))
    result = subprocess.run(['npx', '--offline', '--yes', '--package', '@playwright/cli', 'playwright-cli',
                             '-s=' + session, 'run-code', code], capture_output=True, text=True)
    if result.returncode or '### Error' in result.stdout:
        # Never echo the CLI's private generated code, source title or route.
        local_log = Path('output/playwright/p2-02-verification-error.log')
        local_log.parent.mkdir(parents=True, exist_ok=True)
        local_log.write_text(result.stdout + result.stderr)
        raise RuntimeError('Chromium verification failed; inspect ignored output/playwright/p2-02-verification-error.log')
    output = result.stdout.split('### Result\n', 1)[1].split('### Ran Playwright code', 1)[0]
    return json.loads(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--representative', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--session', default='rideworks-p2-02')
    args = parser.parse_args()
    print(json.dumps(verify(args.data_dir, args.representative, args.port, args.session), indent=2))
