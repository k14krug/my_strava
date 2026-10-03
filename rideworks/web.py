"""Small loopback-only browser boundary; no retired application imports."""

from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from .analysis import analyze_activity
from .errors import RideWorksError
from .store import Store, resolve_data_dir

STATIC = Path(__file__).with_name('static')
ASSETS = {'style.css': 'text/css', 'review.js': 'text/javascript', 'mark.svg': 'image/svg+xml'}


def duration(seconds):
    if seconds is None:
        return 'Unavailable'
    total = int(float(seconds) + 0.5)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f'{hours}:{minutes:02}:{secs:02}' if hours else f'{minutes}:{secs:02}'


def distance(metres):
    return 'Unavailable' if metres is None else f'{metres / 1609.344:.2f} mi'


def ascent(metres):
    return 'Unavailable' if metres is None else f'{int(metres / 0.3048 + 0.5):,} ft'


def sensor(value, unit):
    return 'Unavailable' if value is None else f'{value} {unit}'


def label(summary):
    if summary.get('sub_sport') == 'virtual_activity':
        return 'Virtual Ride'
    if summary.get('sport') == 'cycling':
        return 'Ride'
    return (summary.get('sport') or 'Activity').replace('_', ' ').title()


def local_time(timestamp):
    if timestamp is None:
        return 'Date unavailable'
    # A labeled UTC fallback stays understandable without JavaScript.
    return (f'<time datetime="{escape(timestamp, quote=True)}" data-local-time>'
            f'{escape(timestamp)} (UTC source time)</time>')


def shell(title, content):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · RideWorks</title><link rel="icon" href="/static/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/style.css"><script src="/static/review.js" defer></script></head>
<body><aside class="sidebar"><a class="brand" href="/" aria-label="RideWorks Activities"><img src="/static/mark.svg" alt="" width="58" height="38"><span>RideWorks</span></a>
<nav aria-label="Main"><a class="active" href="/" aria-current="page"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M4 12h16M4 19h16"/></svg>Activities</a></nav></aside>
<main>{content}</main></body></html>'''


def activities_page(store):
    rows = store.list_activities()
    if not rows:
        body = '''<section class="panel empty"><h2>Import your first ride</h2><p>Preserve a FIT or FIT.GZ file with the RideWorks import command, then reload this page.</p>
<pre>python -m rideworks --data-dir &lt;data-dir&gt; import-fit &lt;activity.fit.gz&gt;</pre><p>Use the same data directory when starting the server.</p></section>'''
    else:
        items = []
        for row in rows:
            items.append(f'''<li><a class="activity-row" href="/activities/{escape(row['activity_id'])}"><div><h2>{escape(label(row))}</h2><p>{local_time(row['start_time'])}</p></div><div class="list-metrics"><span>{distance(row['total_distance'])}</span><span>{duration(row['total_elapsed_time'])} elapsed</span><span class="open-ride">Open ride →</span></div></a></li>''')
        body = '<ul class="activity-list panel">' + ''.join(items) + '</ul>'
    return shell('Activities', '<header><h1>Activities</h1><p>Your imported rides</p></header>' + body)


def metric(name, value):
    return f'<div class="metric"><div>{escape(name)}</div><strong>{escape(value)}</strong></div>'


def detail_rows(rows):
    return '<dl>' + ''.join(f'<div><dt>{escape(str(k))}</dt><dd>{escape(str(v)) if v is not None else "Unavailable"}</dd></div>' for k, v in rows) + '</dl>'


def chart_payload(analysis):
    """Whitelist display evidence only; preserve every native row/value/order."""
    return [{key: record[key] for key in ('record_index', 'timestamp', 'power', 'heart_rate')}
            for record in analysis['native_records']]


def review_page(analysis):
    summary = analysis['source_summary']['values']
    source, extraction = analysis['source'], analysis['extraction']
    best = analysis['best_20_minute_power']
    activity_id = analysis['activity']['activity_id']
    title = label(summary)
    subtype = (summary.get('sub_sport') or summary.get('sport') or 'Type unavailable').replace('_', ' ').title()
    cards = ''.join(metric(name, value) for name, value in [
        ('Elapsed duration', duration(summary.get('total_elapsed_time'))),
        ('Distance', distance(summary.get('total_distance'))),
        ('Average power', sensor(summary.get('avg_power'), 'W')),
        ('Average heart rate', sensor(summary.get('avg_heart_rate'), 'bpm')),
    ])
    summary_rows = [
        ('Elapsed duration', duration(summary.get('total_elapsed_time'))),
        ('Timer duration', duration(summary.get('total_timer_time'))),
        ('Distance', distance(summary.get('total_distance'))),
        ('Ascent', ascent(summary.get('total_ascent'))),
        ('Average power', sensor(summary.get('avg_power'), 'W')),
        ('Maximum power', sensor(summary.get('max_power'), 'W')),
        ('Average heart rate', sensor(summary.get('avg_heart_rate'), 'bpm')),
        ('Maximum heart rate', sensor(summary.get('max_heart_rate'), 'bpm')),
        ('Average cadence', sensor(summary.get('avg_cadence'), 'rpm')),
    ]
    source_rows = [('Activity ID', activity_id), ('Source ID', source['source_id']),
                   ('Original basename', source['original_basename']), ('Artifact SHA-256', source['sha256']),
                   ('Artifact byte size', source['byte_size']), ('Packaging', source['packaging']),
                   ('Content format', source['content_format']),
                   ('Parser', extraction['parser_name']), ('Parser version', extraction['parser_version']),
                   ('Mapping version', extraction['mapping_version']),
                   ('Current extraction ID', extraction['extraction_id']),
                   ('Source start time (UTC)', summary.get('start_time'))]
    for signal, name in [('power', 'Power'), ('heart_rate', 'Heart rate')]:
        a = analysis['availability'][signal]
        source_rows.extend([(f'{name} availability', a['status']),
                            (f'{name} samples', f"{a['present']} present / {a['missing']} missing / {a['total']} total"),
                            (f'{name} origin', a['origin'])])
    best_rows = [('Origin', 'RideWorks-calculated'), ('Method/version', best['method']),
                 ('Status', best['status']), ('Unavailable reason', best['reason'])] if not best['eligible'] else [
        ('Origin', 'RideWorks-calculated'), ('Method/version', best['method']),
        ('Native samples in window', best['sample_count']),
        ('Record indices (start inclusive / end exclusive)', f"{best['start_record_index']} / {best['end_exclusive_record_index']}"),
        ('Window start (UTC)', best['start_timestamp']), ('Window end, exclusive (UTC)', best['end_exclusive_timestamp']),
        ('Unrounded average', sensor(best['average_watts'], 'W')), ('Eligible windows', best['eligible_window_count'])]
    window_text = 'No eligible complete 20-minute window.'
    if best['eligible']:
        start = summary.get('start_time')
        if start is not None:
            offset = (datetime.fromisoformat(best['start_timestamp']) - datetime.fromisoformat(start)).total_seconds()
            window_text = f"{duration(offset)}–{duration(offset + best['duration_seconds'])} elapsed · {best['sample_count']:,} native samples"
        else:
            window_text = f"{best['sample_count']:,} native samples · window timestamps in calculation details"
    records = chart_payload(analysis)
    # Avoid closing the JSON script element with any source text. Never embed
    # private file/store paths, coordinates, or a raw application snapshot.
    payload = json.dumps(records, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c').replace('&', '\\u0026')
    return shell(title, f'''<header><a class="back" href="/">Activities /</a><h1>{escape(title)}</h1><p>{local_time(summary.get('start_time'))}<span class="meta-separator">·</span>{escape(subtype)}<span class="meta-separator">·</span>FIT source</p></header>
<section class="metrics" aria-label="FIT session source summary">{cards}</section>
<div class="review-layout"><div class="review-main"><section class="panel chart-panel" aria-labelledby="chart-title">
<div class="panel-heading"><h2 id="chart-title">Ride power &amp; heart rate</h2><div class="legend"><span><i class="power-swatch"></i>Power · W</span><span><i class="hr-swatch"></i>Heart rate · bpm</span></div></div>
<div id="ride-chart" data-record-count="{len(records)}" data-start-time="{escape(summary.get('start_time') or '', quote=True)}"><svg id="chart-svg" role="img" aria-label="Native power and heart rate over elapsed ride time"></svg></div>
<div id="sample-readout" role="status" aria-live="polite">Inspect the chart for native sample values. Keyboard: focus the chart, then use arrow keys.</div>
<p class="chart-note">{len(records):,} native records · elapsed ride time · missing samples remain gaps</p>
<noscript>Enable JavaScript to review the native chart and display dates in your local timezone.</noscript></section>
<section class="panel best-panel"><div><h2>Best 20-minute power</h2><p>RideWorks-calculated</p></div><strong class="best-value">{sensor(best['rounded_watts'], 'W')}</strong><p class="window-context">{escape(window_text)}</p>
<details><summary>Calculation details</summary>{detail_rows(best_rows)}<p>Complete 1,200-sample windows with one-second timestamps and no missing power. Earliest window wins a tie; whole watts round half up. No repaired or estimated samples.</p></details></section>
<details class="panel provenance"><summary>Source &amp; provenance</summary><p>Ride summary values are FIT session source evidence. Sensor origins remain unknown; presence does not establish measurement origin.</p>{detail_rows(source_rows)}</details></div>
<aside class="panel ride-summary"><h2>Ride summary</h2><p class="source-caption">FIT session source evidence</p>{detail_rows(summary_rows)}</aside></div>
<script id="native-records" type="application/json">{payload}</script>''')


class Application:
    """Read-only routes; each request gets its own short-lived Store snapshot."""
    def __init__(self, data_dir=None):
        self.data_dir = resolve_data_dir(data_dir)
        with Store(self.data_dir):
            pass

    def get(self, target):
        path = urlsplit(target).path
        if path.startswith('/static/'):
            name = path.removeprefix('/static/')
            if name in ASSETS:
                return 200, ASSETS[name], (STATIC / name).read_bytes()
        with Store(self.data_dir) as store:
            if path == '/':
                return 200, 'text/html', activities_page(store).encode()
            if path.startswith('/activities/'):
                activity_id = path.removeprefix('/activities/')
                try:
                    # Stable UUID routes; never interpolate a route into SQL.
                    if str(UUID(activity_id)) != activity_id:
                        raise ValueError
                except ValueError:
                    return self.not_found()
                if not any(row['activity_id'] == activity_id for row in store.list_activities()):
                    return self.not_found()
                try:
                    html = review_page(analyze_activity(store, activity_id))
                except RideWorksError:
                    return 422, 'text/html', shell('Evidence unavailable', '<header><h1>Evidence unavailable</h1><p>This activity cannot currently be reviewed from a single usable FIT Source.</p></header>').encode()
                return 200, 'text/html', html.encode()
        return self.not_found()

    @staticmethod
    def not_found():
        return 404, 'text/html', shell('Activity not found', '<header><h1>Activity not found</h1><p>Return to <a href="/">Activities</a> to open an imported ride.</p></header>').encode()


def create_server(data_dir=None, port=8765):
    app = Application(data_dir)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                status, content_type, body = app.get(self.path)
            except Exception as exc:
                # HTTP errors must not leak private paths, SQL or tracebacks.
                # Let KeyboardInterrupt/SystemExit propagate (not Exception).
                print(f'RideWorks request failed ({type(exc).__name__})', flush=True)
                status, content_type, body = 500, 'text/html', shell('Unable to load activity', '<h1>Unable to load activity</h1><p>RideWorks could not read the current evidence.</p>').encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type + ('; charset=utf-8' if content_type.startswith('text/') else ''))
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return HTTPServer(('127.0.0.1', port), Handler)


def serve(data_dir=None, port=8765):
    with create_server(data_dir, port) as server:
        print(f'RideWorks: http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nRideWorks stopped.', flush=True)
