#!/usr/bin/env python3
"""Aggregate local HTTP/restart acceptance; real-browser checks remain separate.

Personal input, runtime state and expected titles stay local. Output contains no
Activity IDs, private titles, source paths or HTML/native evidence snapshots.
"""
import argparse
from collections import Counter
from hashlib import sha256
from html import escape, unescape
from http.client import HTTPConnection
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic, sleep
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rideworks.history import PAGE_SIZE, presentation
from rideworks.store import Store


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def get(port, route):
    connection = HTTPConnection('127.0.0.1', port, timeout=30)
    try:
        connection.request('GET', route)
        response = connection.getresponse()
        return response.status, response.read().decode()
    finally:
        connection.close()


def links(html):
    return re.findall(r'class="activity-row" href="(/activities/[^"]+)"', html)


def verify(data_dir, representative, port):
    with Store(data_dir) as store:
        history = store.activity_history()
        rows = [presentation(s) for s in history]
        counts = Counter(r['activity_type'] for r in rows)
        require(len(rows) == 1434, 'Unexpected history population')
        require(counts == {'Virtual Ride':1264, 'Ride':146, 'Run':22, 'Walk':1, 'Rowing':1}, 'Unexpected type population')
        digest = sha256(representative.read_bytes()).hexdigest()
        seed = next((r for r in rows if any(e['source'].get('sha256') == digest for e in r['sources'])), None)
        require(seed is not None and seed['title_source'] is not None, 'Representative title enrichment unavailable')
        samples = {'FIT': seed}
        for fmt in ('TCX', 'GPX'):
            samples[fmt] = next(r for r in rows if any(e['source']['content_format'] == fmt for e in r['sources']))
        samples['CSV-only'] = next(r for r in rows if all(e['source']['kind'] == 'strava_export' for e in r['sources']))
        require(store.connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Store integrity failure')
        require(not store.connection.execute('PRAGMA foreign_key_check').fetchall(), 'Store foreign key failure')
    root = Path(__file__).resolve().parents[1]
    before = None
    for restart in range(2):
        child = subprocess.Popen([sys.executable, '-m', 'rideworks', '--data-dir', str(data_dir.resolve()),
                                  'serve', '--port', str(port)], cwd=root,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = monotonic() + 10
            while True:
                try:
                    status, html = get(port, '/activities')
                    break
                except OSError:
                    require(child.poll() is None and monotonic() < deadline, 'Verification server failed to start')
                    sleep(.05)
            require(status == 200 and len(links(html)) == PAGE_SIZE, 'Root is not a bounded page')
            require('1–30 of 1,410 matching activities · 1,434 in history' in html, 'Default cycling counts incorrect')
            first = links(html)
            metadata = {f"/activities/{r['activity_id']}":r for r in rows}
            require(all(metadata[url]['activity_type'] in ('Ride','Virtual Ride') for url in first), 'Noncycling default result')
            dates = [metadata[url]['date_key'] for url in first]
            require(dates == sorted(dates, reverse=True), 'Default is not newest-first')
            next_url = unescape(re.search(r'rel="next" href="([^"]+)"', html).group(1))
            _, second = get(port, next_url)
            require(not set(first) & set(links(second)), 'Second page overlaps first')
            require('Page 2 of 47' in second and 'rel="prev"' in second, 'Pagination unavailable')
            require(links(get(port, '/activities')[1]) == first, 'Returning to root changes page')
            for kind, count in [('all',1434), ('Ride',146), ('Virtual Ride',1264), ('Run',22)]:
                status, filtered = get(port, '/activities?type=' + quote(kind))
                require(status == 200 and f'of {count:,} matching activities' in filtered, 'Type filter count incorrect')
                if kind == 'Run':
                    require(all(metadata[url]['activity_type']=='Run' for url in links(filtered)), 'Noncycling filter incorrect')
            search_route = '/activities?type=all&q=' + quote(seed['title'].swapcase())
            _, searched = get(port, search_route)
            seed_url = '/activities/' + seed['activity_id']
            require(seed_url in links(searched) and escape(seed['title']) in searched, 'Source-title search failed')
            day = seed['date_day']
            _, dated = get(port, '/activities?type=all&from=' + day + '&to=' + day + '&tz=UTC')
            require(links(dated) and all(metadata[url]['date_day']==day for url in links(dated)), 'Date range incorrect')
            for sort, key in [('duration','duration'), ('distance','distance'), ('oldest','date_key')]:
                route = '/activities?type=all&sort=' + sort
                _, sorted_html = get(port, route)
                known = [metadata[url][key] for url in links(sorted_html) if metadata[url][key] is not None]
                require(known == sorted(known, reverse=sort!='oldest'), 'Alternate sort incorrect')
                require(links(get(port, route)[1]) == links(sorted_html), 'Sort is not deterministic')
            route_results = {}
            for fmt, row in samples.items():
                status, review = get(port, '/activities/' + row['activity_id'])
                require(status == 200 and f'<h1>{escape(row["title"])}</h1>' in review, 'Stable route/title failed')
                if fmt == 'FIT':
                    require('118 W' in review and '120 W' in review and 'id="native-records"' in review,
                            'Representative rich review changed')
                    require('Source-supplied Strava-export evidence' in review, 'Rich title provenance missing')
                else:
                    require('Detailed RideWorks review unavailable' in review and 'id="native-records"' not in review,
                            'Thin review fabricated analysis')
                for private in (str(data_dir), str(data_dir.resolve()), 'stored_path', 'latitude', 'longitude'):
                    require(private not in review, 'Private runtime/location evidence exposed')
                route_results[fmt] = 'rich' if fmt == 'FIT' else 'thin'
            snapshot = dict(first_page=first, second_page=links(second), search=links(searched),
                            dates=links(dated), routes=route_results)
            require(child.poll() is None, 'Verification process did not own the server port')
            if restart:
                require(snapshot == before, 'History browser changed across process restart')
            before = snapshot
        finally:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    return dict(result='passed', activity_count=len(rows), cycling_count=1410, type_counts=dict(counts),
                page_size=PAGE_SIZE, cycling_pages=47, all_pages=48,
                query_filters_verified=True, source_title_search_and_display_verified=True,
                format_routes=route_results, process_restart_verified=True,
                representative_fit_average_watts=118, representative_best20_display_watts=120,
                privacy_checks_passed=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--representative', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    print(json.dumps(verify(args.data_dir, args.representative, args.port), indent=2))
