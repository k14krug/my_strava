"""Small loopback-only browser boundary; no retired application imports."""

from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit
from uuid import UUID

from .analysis import analyze_activity
from .errors import RideWorksError
from .history import SORTS, browse, presentation
from .store import Store, resolve_data_dir

STATIC = Path(__file__).with_name('static')
ASSETS = {'style.css': 'text/css', 'review.js': 'text/javascript', 'performance.js': 'text/javascript', 'mark.svg': 'image/svg+xml'}


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


def activity_title(summary):
    """Explicit fallback only: source type plus fixed English UTC source date.

    No current FIT source-name evidence is persisted by Phase 1. This does not
    establish a durable title/reconciliation policy or claim an original name.
    """
    timestamp = summary.get('start_time')
    if timestamp is None:
        return f'{label(summary)} — date unavailable'
    date = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
    month = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[date.month - 1]
    return f'{label(summary)} — {month} {date.day}, {date.year}'


def icon(name):
    paths = {
        'duration': '<circle cx="12" cy="13" r="8"/><path d="M12 9v5l3 2M9 2h6M12 2v3"/>',
        'distance': '<path d="m6 3-3 18M18 3l3 18M12 3v3m0 4v4m0 4v3"/>',
        'power': '<path d="m14 2-9 12h6l-1 8 9-13h-6Z"/>',
        'heart': '<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-5 5 3 11 8 15 5-4 13-10 8-15Z"/>',
        'summary': '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4m8-4v4M4 10h16"/>',
    }
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>'


def local_time(timestamp, *, compact=False):
    if timestamp is None:
        return 'Date unavailable'
    # A labeled UTC fallback stays understandable without JavaScript.
    compact_attr = ' data-compact-time' if compact else ''
    return (f'<time datetime="{escape(timestamp, quote=True)}" data-local-time{compact_attr}>'
            f'{escape(timestamp)} (UTC source time)</time>')


def shell(title, content, *, active='activities'):
    def nav_state(name):
        return ' class="active" aria-current="page"' if active == name else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · RideWorks</title><link rel="icon" href="/static/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/style.css"><script src="/static/review.js" defer></script></head>
<body><div class="app-header"><a class="brand" href="/" aria-label="RideWorks Activities"><img src="/static/mark.svg" alt="" width="44" height="28"><span>RideWorks</span></a></div>
<aside class="sidebar"><nav aria-label="Main"><a href="/"{nav_state('activities')}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 3v17h17M6 15l5-6 4 3 5-6"/></svg>Activities</a><a href="/performance"{nav_state('performance')}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 3v17h17M6 16l4-5 4 2 6-9"/></svg>Performance</a></nav></aside>
<main>{content}</main></body></html>'''


def browser_time(row, *, compact=False):
    if row['absolute_time']:
        return local_time(row['start_time'], compact=compact)
    if row['start_time']:
        return f"{escape(row['start_time'].replace('T', ' '))} · timezone unknown"
    return escape(row['date_text']) + ' · source date text · timezone unknown' if row['date_text'] else 'Date unavailable'


def activities_page(store, query_string=''):
    result = browse(store, query_string)
    rows, query = result['rows'], result['query']
    def options(choices, current):
        return ''.join(f'<option value="{escape(value, quote=True)}"{" selected" if value == current else ""}>{escape(text)}</option>'
                       for value, text in choices)
    controls = f'''<form class="history-filters panel" action="/" method="get" aria-label="Filter activities">
<input type="hidden" name="tz" value="{escape(query.timezone_name, quote=True)}">
<label class="search-filter">Title search<input type="search" name="q" value="{escape(query.q, quote=True)}" placeholder="Search activity names" maxlength="200"></label>
<label>Activity type<select name="type">{options([('cycling', 'Cycling'), ('all', 'All activities')] + [(t, t) for t in result['type_choices']], query.activity_type)}</select></label>
<label>From<input type="date" name="from" value="{query.after}"></label>
<label>To<input type="date" name="to" value="{query.before}"></label>
<label>Sort<select name="sort">{options(list(SORTS.items()), query.sort)}</select></label>
<div class="filter-actions"><button type="submit">Apply</button><a href="/">Reset</a></div>
</form><p class="date-filter-note">Dates and filters use your local timezone. Timezone-unknown source dates stay as supplied.</p><noscript>Enable JavaScript to use your browser's local dates for absolute timestamps.</noscript>'''
    if query.message:
        controls += f'<p class="query-message" role="status">{escape(query.message)}</p>'
    if not result['total']:
        body = '''<section class="panel empty"><h2>Import your first ride</h2><p>Preserve a FIT or FIT.GZ file with the RideWorks import command, then reload this page.</p>
<pre>python -m rideworks --data-dir &lt;data-dir&gt; import-fit &lt;activity.fit.gz&gt;</pre><p>Use the same data directory when starting the server.</p></section>'''
    elif not rows:
        body = '<section class="panel empty"><h2>No matching activities</h2><p>Try a different title, type or date range.</p><p><a href="/">Reset filters</a></p></section>'
    else:
        items = []
        for row in rows:
            origin = f'<p class="title-origin">{escape(row["title_origin"])}</p>' if row['title_source'] is None else ''
            types = row['activity_type'] + (f" · {row['subtype']}" if row['subtype'] and row['subtype'] != row['activity_type'] else '')
            duration_context = row['duration_source']['context'] if row['duration_source'] else 'Duration unavailable'
            distance_context = row['distance_source']['context'] if row['distance_source'] else 'Distance unavailable'
            items.append(f'''<li><a class="activity-row" href="/activities/{escape(row['activity_id'])}"><div class="row-identity"><h2>{escape(row['title'])}</h2>{origin}</div><div class="row-date">{browser_time(row, compact=True)}</div><span class="row-type">{escape(types)}</span><div class="list-metrics"><span title="{escape(distance_context, quote=True)}">{distance(row['distance'])}</span><span title="{escape(duration_context, quote=True)}">{duration(row['duration'])}</span><span class="open-ride" aria-hidden="true">→</span></div></a></li>''')
        columns = '<div class="activity-columns" aria-hidden="true"><span>Title</span><span>Date</span><span>Type</span><div class="list-metrics"><span>Distance</span><span>Duration</span><span></span></div></div>'
        body = columns + '<ul class="activity-list panel">' + ''.join(items) + '</ul>'
    count = result['count']
    first = result['start'] + 1 if count else 0
    last = result['start'] + len(rows)
    context = f'<p class="result-count" role="status">{first:,}–{last:,} of {count:,} matching activities · {result["total"]:,} in history</p>'
    previous = f'<a rel="prev" href="{escape(query.url(result["page"] - 1), quote=True)}">← Previous</a>' if result['page'] > 1 else '<span aria-disabled="true">← Previous</span>'
    following = f'<a rel="next" href="{escape(query.url(result["page"] + 1), quote=True)}">Next →</a>' if result['page'] < result['pages'] else '<span aria-disabled="true">Next →</span>'
    navigation = f'<nav class="pagination" aria-label="Activity pages">{previous}<span>Page {result["page"]} of {result["pages"]}</span>{following}</nav>'
    return shell('Activities', '<header><h1>Activities</h1></header>' + controls + context + body + navigation)


def metric(name, value, symbol):
    return f'<div class="metric"><div>{icon(symbol)}<span>{escape(name)}</span></div><strong>{escape(value)}</strong></div>'


def detail_rows(rows):
    return '<dl>' + ''.join(f'<div><dt>{escape(str(k))}</dt><dd>{escape(str(v)) if v is not None else "Unavailable"}</dd></div>' for k, v in rows) + '</dl>'


def chart_payload(analysis):
    """Whitelist display evidence only; preserve every native row/value/order."""
    return [{key: record[key] for key in ('record_index', 'timestamp', 'power', 'heart_rate')}
            for record in analysis['native_records']]


def review_page(analysis, metadata=None):
    summary = analysis['source_summary']['values']
    source, extraction = analysis['source'], analysis['extraction']
    best = analysis['best_20_minute_power']
    activity_id = analysis['activity']['activity_id']
    title = metadata['title'] if metadata else activity_title(summary)
    title_origin = metadata['title_origin'] if metadata else 'Derived title'
    subtype = (summary.get('sub_sport') or summary.get('sport') or 'Type unavailable').replace('_', ' ').title()
    cards = ''.join(metric(name, value, symbol) for name, value, symbol in [
        ('Elapsed duration', duration(summary.get('total_elapsed_time')), 'duration'),
        ('Distance', distance(summary.get('total_distance')), 'distance'),
        ('Average power', sensor(summary.get('avg_power'), 'W'), 'power'),
        ('Average heart rate', sensor(summary.get('avg_heart_rate'), 'bpm'), 'heart'),
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
    source_rows = [('Activity ID', activity_id), ('Displayed title', title),
                   ('Title origin', 'Derived fallback; source activity name unavailable'),
                   ('Title basis', 'FIT activity type + source start date (UTC); fixed English month names'),
                   ('Source ID', source['source_id']),
                   ('Original basename', source['original_basename']), ('Artifact SHA-256', source['sha256']),
                   ('Artifact byte size', source['byte_size']), ('Packaging', source['packaging']),
                   ('Content format', source['content_format']),
                   ('Parser', extraction['parser_name']), ('Parser version', extraction['parser_version']),
                   ('Mapping version', extraction['mapping_version']),
                   ('Current extraction ID', extraction['extraction_id']),
                   ('Source start time (UTC)', summary.get('start_time'))]
    if metadata and metadata['title_source']:
        title_source = metadata['title_source']['source']
        source_rows[2:4] = [('Title origin', 'Source-supplied Strava-export evidence'),
                            ('Title Source ID', title_source['source_id']),
                            ('Title display policy', 'Latest non-empty imported Strava-export title; observations retained')]
    if metadata and metadata['type_source'] and metadata['type_source']['source']['kind'] == 'strava_export':
        source_rows += [('Displayed type origin', 'Strava-export source evidence'),
                        ('Type Source ID', metadata['type_source']['source']['source_id'])]
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
    type_text = metadata['activity_type'] if metadata and metadata['type_source'] and metadata['type_source']['source']['kind'] == 'strava_export' else (summary.get('sport') or 'Unavailable').replace('_', ' ').title()
    if metadata and metadata['subtype']:
        subtype = metadata['subtype']
    return shell(title, f'''<header><div class="breadcrumb"><a href="/">Activities</a><span>/</span>Ride details</div><div class="ride-heading"><h1>{escape(title)}</h1><span class="title-origin">{escape(title_origin)}</span></div><p class="ride-meta">{local_time(summary.get('start_time'))}<span class="meta-separator">·</span>Type: {escape(type_text)}<span class="meta-separator">·</span>Subtype: {escape(subtype)}<span class="meta-separator">·</span>FIT source</p></header>
<section class="metrics" aria-label="FIT session source summary">{cards}</section>
<div class="review-layout"><div class="review-main"><section class="panel chart-panel" aria-labelledby="chart-title">
<div class="panel-heading"><h2 id="chart-title">Ride power &amp; heart rate</h2><div class="legend"><span><i class="power-swatch"></i>Power · W</span><span><i class="hr-swatch"></i>Heart rate · bpm</span></div></div>
<div id="ride-chart" data-record-count="{len(records)}" data-start-time="{escape(summary.get('start_time') or '', quote=True)}"><svg id="chart-svg" role="img" aria-label="Native power and heart rate over elapsed ride time" aria-describedby="chart-help"></svg></div>
<div id="sample-readout" role="status" aria-live="polite">Move over the chart to inspect power and heart rate.</div>
<div class="chart-footer"><span>{len(records):,} recorded samples · elapsed time</span><span id="chart-help">Focus chart + arrow keys to inspect</span></div>
<noscript>Enable JavaScript to review the native chart and display dates in your local timezone.</noscript></section>
<section class="panel best-panel"><div><h2>{icon('power')}Best 20-minute power</h2><p>RideWorks-calculated</p></div><strong class="best-value">{sensor(best['rounded_watts'], 'W')}</strong><p class="window-context">{escape(window_text)}</p>
<details><summary>Calculation details</summary>{detail_rows(best_rows)}<p>Complete 1,200-sample windows with one-second timestamps and no missing power. Earliest window wins a tie; whole watts round half up. No repaired or estimated samples.</p></details></section>
<details class="panel provenance"><summary>Source &amp; provenance</summary><p>Ride summary values are FIT session source evidence. Sensor origins remain unknown; presence does not establish measurement origin.</p>{detail_rows(source_rows)}</details></div>
<aside class="panel ride-summary"><h2>{icon('summary')}Ride summary</h2><p class="source-caption">FIT session source evidence</p>{detail_rows(summary_rows)}</aside></div>
<script id="native-records" type="application/json">{payload}</script>''')


def thin_review_page(row):
    sources = []
    for evidence in row['sources']:
        source, summary = evidence['source'], evidence['summary']
        csv = source['kind'] == 'strava_export'
        name = 'Strava-export metadata' if csv else f"{source['content_format']} source evidence"
        values = [('Source ID', source['source_id'])]
        if csv:
            values += [('Title', summary.get('title')), ('Activity type', summary.get('activity_type')),
                       ('Sport type', summary.get('sport_type')), ('Source date text', summary.get('date_text'))]
            values += [(f"{f['column']} (column {f['column_index'] + 1}; {f['unit'].replace('source_unspecified', 'units unspecified')})", f['raw_value'] or None)
                       for f in summary.get('fields', []) if f['status'] != 'missing']
            note = 'CSV summaries are source metadata. Where units are unspecified, values are shown as supplied. Native streams are unavailable from this source.'
        else:
            values += [('Source start time', summary.get('start_time')),
                       ('Elapsed duration', duration(summary.get('total_elapsed_time'))),
                       ('Timer duration', duration(summary.get('total_timer_time'))),
                       ('Distance', distance(summary.get('total_distance')))]
            extraction = evidence['extraction']
            values += [('Parser', extraction['parser_name']), ('Parser version', extraction['parser_version']),
                       ('Mapping version', extraction['mapping_version']), ('Native records preserved', extraction['record_count'])]
            for signal, label_text in [('power', 'Power'), ('heart_rate', 'Heart rate')]:
                a = evidence['availability'][signal]
                values += [(f'{label_text} availability', a['status']), (f'{label_text} origin', a['origin'])]
            for i, lap in enumerate(evidence.get('xml_context', {}).get('lap_summaries', []), 1):
                values += [(f'Lap {i} source duration', duration(lap.get('total_time_seconds'))),
                           (f'Lap {i} source distance', distance(lap.get('distance_m'))),
                           (f'Lap {i} average power', sensor(lap.get('avg_power'), 'W')),
                           (f'Lap {i} maximum power', sensor(lap.get('max_power'), 'W')),
                           (f'Lap {i} average heart rate', sensor(lap.get('avg_heart_rate'), 'bpm')),
                           (f'Lap {i} maximum heart rate', sensor(lap.get('max_heart_rate'), 'bpm'))]
            note = 'Native source evidence is preserved. Detailed RideWorks review is not yet supported for this evidence. Signal presence does not establish measurement origin.'
        sources.append(f'<details class="panel provenance" open><summary>{escape(name)}</summary><p>{escape(note)}</p>{detail_rows(values)}</details>')
    return shell(row['title'], f'''<header><div class="breadcrumb"><a href="/">Activities</a><span>/</span>Activity details</div><h1>{escape(row['title'])}</h1><p class="title-origin">{escape(row['title_origin'])}</p><p class="ride-meta">{browser_time(row)} · Type: {escape(row['activity_type'])} · Subtype: {escape(row['subtype'] or 'Unavailable')}</p></header>
<section class="panel review-unavailable"><h2>Detailed RideWorks review unavailable</h2><p>This activity does not currently have a single supported FIT analysis source. Available source evidence is shown below; no charts or best-20 result are substituted.</p></section>
<section class="thin-sources" aria-label="Associated source evidence">{''.join(sources)}</section>''')


def performance_page(store):
    from .performance import performance_history
    from .performance_view import performance_view
    history = performance_history(store)
    points = history['points']
    view = performance_view(points)
    def safe_json(value):
        return json.dumps(value, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    def summary_card(key, label):
        index = view['summaries'][key]
        if index is None:
            return f'<article class="performance-card" data-summary="{key}"><h2>{label}</h2><strong>Unavailable</strong><p>No qualifying result in this period</p></article>'
        point = points[index]
        age = view['ages_days'].get(str(index))
        freshness = f"{age} days ago" if age is not None else 'Timezone unknown'
        return f'''<article class="performance-card" data-summary="{key}" data-point-index="{index}"><h2>{label}</h2>
<strong>{point['rounded_watts']} <span>W</span></strong><p class="performance-card-date">{browser_time(point, compact=True)}</p>
<a href="/activities/{point['activity_id']}" title="{escape(point['title'], quote=True)}">{escape(point['title'])}</a><p class="performance-freshness">{freshness}</p></article>'''
    if points:
        cards = ''.join(summary_card(key, label) for key, label in [('current','Current 42-day best'),
                        ('latest','Latest eligible ride'),('year','Best in last 12 months'),('lifetime','Lifetime best')])
        chart = f'''<div class="performance-workspace">
<div class="performance-modes" role="tablist" aria-label="Performance mode">
<button type="button" role="tab" aria-selected="false" data-mode="current">Current</button>
<button type="button" role="tab" aria-selected="true" data-mode="trend">Trend</button>
<button type="button" role="tab" aria-selected="false" data-mode="history">History</button></div>
<section class="performance-summary" aria-label="Trusted power summaries">{cards}</section>
<section class="panel performance-chart-panel"><div class="performance-chart-heading"><div><h2 id="performance-chart-title">Rolling 42-day best</h2><p id="performance-chart-caption">Strongest qualifying ride in each trailing 42-day window</p></div>
<div class="performance-ranges" role="group" aria-label="Time range"><button type="button" data-range="3mo">3 mo</button><button type="button" data-range="6mo">6 mo</button><button type="button" data-range="1yr" aria-pressed="true">1 yr</button><button type="button" data-range="3yr">3 yr</button><button type="button" data-range="all">All</button></div></div>
<div class="performance-evidence-control" role="group" aria-label="Chart evidence"><button type="button" data-evidence="trend" aria-pressed="true">Trend only</button><button type="button" data-evidence="rides">Trend + rides</button><span id="performance-visible-count"></span></div>
<div id="performance-current" hidden></div>
<svg id="performance-chart" role="img" tabindex="0" aria-label="20-minute power history in watts. Arrow keys inspect results; Enter opens the selected Activity."></svg>
<p id="performance-chart-empty" hidden>No eligible evidence in this period. Choose a longer range.</p>
<div class="performance-selection"><p id="performance-selection-label">Selected result</p><div id="performance-readout" aria-live="polite"><time id="performance-date"></time><a id="performance-activity"></a><strong id="performance-watts"></strong></div>
<details id="performance-point-details"><summary>Selected result provenance</summary><dl id="performance-point-context"></dl></details></div>
<p class="chart-footer" id="performance-chart-help">Hover or use arrow keys to inspect. Click a result or press Enter to open the Activity.</p>
<noscript>Enable JavaScript to view the chart and use Performance modes.</noscript></section>
<details class="panel performance-evidence"><summary>Eligible ride results <span id="performance-evidence-count"></span></summary>
<div class="performance-evidence-table"><table><thead><tr><th>Date</th><th>Activity</th><th>Best 20 min</th></tr></thead><tbody id="performance-rides"></tbody></table></div>
<div class="performance-evidence-pages"><button type="button" id="performance-rides-prev">Previous</button><span id="performance-rides-page"></span><button type="button" id="performance-rides-next">Next</button></div></details></div>'''
    else:
        message = ('Performance history has not been rebuilt yet.' if history['current'] == 0 else
                   'No current ride result qualifies for the trusted 20-minute history.')
        chart = f'<section class="panel empty"><h2>20-minute power history</h2><p>{message}</p></section>'
    notices = []
    if history['pending']:
        notices.append(f"{history['pending']:,} Activities need a performance rebuild; changed inputs are not plotted.")
    if history['missing_dates']:
        notices.append(f"{history['missing_dates']:,} eligible results lack a supported Activity date and are not plotted.")
    if view['unknown_timezones']:
        notices.append(f"{view['unknown_timezones']:,} results have source dates with unknown timezones: available in History, unavailable for exact timed-window summaries.")
    return shell('Performance', f'''<header><h1>Performance</h1><p class="performance-count">20-minute power · {len(points):,} eligible ride results · Virtual Ride native power</p></header>{chart}
<p class="performance-notice">{escape(' '.join(notices))}</p>
<details class="panel performance-policy"><summary>Eligibility &amp; method</summary>
<p>Virtual Ride native source power is eligible for this Phase 2 history. Native power presence does not establish that it was measured. Outdoor Ride power is excluded because its evidence quality is suspect.</p>
<p>RideWorks calculates the highest average over exactly 1,200 consecutive records with one-second timestamps and complete power. Zero watts count; missing power, gaps and duplicate or backward timestamps invalidate affected windows. No interpolation, resampling or repair occurs. Exact ties choose the earliest window; display rounds whole watts half up.</p>
<p>The trend retains the strongest qualifying result in the trailing 42 days, changing when a ride enters or leaves the window. A result expires exactly 42 days after its Activity start. Gaps mean there is no qualifying result; the line is demonstrated evidence rather than an estimated daily performance series. Time ranges end at the page's current time; annual peaks use displayed calendar years within the selected range.</p>
<p>Method: best-average-power-v1 · Policy: virtual-native-power-v1. One eligible native file Source must support each Activity result. Multiple eligible Sources are ambiguous and excluded. CSV and source summaries never substitute for native power. Ineligible or missing results are not plotted as zero.</p>
</details><script id="performance-points" type="application/json">{safe_json(points)}</script><script id="performance-view" type="application/json">{safe_json(view)}</script><script src="/static/performance.js" defer></script>''', active='performance')


class Application:
    """Read-only routes; each request gets its own short-lived Store snapshot."""
    def __init__(self, data_dir=None):
        self.data_dir = resolve_data_dir(data_dir)
        with Store(self.data_dir):
            pass

    def get(self, target):
        url = urlsplit(target)
        path = url.path
        if path.startswith('/static/'):
            name = path.removeprefix('/static/')
            if name in ASSETS:
                return 200, ASSETS[name], (STATIC / name).read_bytes()
        with Store(self.data_dir) as store:
            if path == '/':
                return 200, 'text/html', activities_page(store, url.query).encode()
            if path == '/performance':
                return 200, 'text/html', performance_page(store).encode()
            if path.startswith('/activities/'):
                activity_id = path.removeprefix('/activities/')
                try:
                    # Stable UUID routes; never interpolate a route into SQL.
                    if str(UUID(activity_id)) != activity_id:
                        raise ValueError
                except ValueError:
                    return self.not_found()
                snapshots = store.activity_history(activity_id)
                if not snapshots:
                    return self.not_found()
                metadata = presentation(snapshots[0])
                fit_sources = [e for e in snapshots[0]['sources'] if e['source']['kind'] == 'file_fit']
                if len(fit_sources) != 1:
                    return 200, 'text/html', thin_review_page(metadata).encode()
                try:
                    html = review_page(analyze_activity(store, activity_id), metadata)
                except RideWorksError:
                    html = thin_review_page(metadata)
                return 200, 'text/html', html.encode()
        return self.not_found()

    @staticmethod
    def not_found():
        return 404, 'text/html', shell('Activity not found', '<header><h1>Activity not found</h1><p>Return to <a href="/">Activities</a> to open an imported ride.</p></header>').encode()


def create_server(data_dir=None, port=8765, *, debug=False):
    app = Application(data_dir)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            started = perf_counter()
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
            if debug:
                print(f'RideWorks request: GET {status} ({(perf_counter() - started) * 1000:.1f} ms)', flush=True)

        def log_message(self, *_):
            pass

    return HTTPServer(('127.0.0.1', port), Handler)


def serve(data_dir=None, port=8765, *, debug=False):
    with create_server(data_dir, port, debug=debug) as server:
        print(f'RideWorks: http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)', flush=True)
        if debug:
            print('Request diagnostics enabled (FLASK_DEBUG); no debugger or reloader.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nRideWorks stopped.', flush=True)
