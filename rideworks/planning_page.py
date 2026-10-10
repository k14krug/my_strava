"""Home, rolling Plan and a narrow, evidence-aware Activity Review panel."""
from datetime import date
from html import escape
import json
from urllib.parse import urlencode

from .goals import query_zone
from .planning import CATEGORIES, activity_context, plan
from .web import detail_rows, local_time, shell


def hidden(name,value):
    return f'<input type="hidden" name="{name}" value="{escape(str(value),quote=True)}">'


def ride_content(rec):
    return f'''<h3 class="recommended-type">{escape(rec['category'])}</h3><p class="recommended-target">{escape(rec['duration'])} · {escape(rec['power'])}</p><p class="recommended-reason">{escape(rec['reason'])}</p>'''


def today_card(data,nonce=None,*,compact=False):
    rec=data['days'][0]; zone=data['timezone']
    provisional='<p class="plan-caveat">Provisional based on available history.</p>' if data['provisional'] else ''
    if compact:
        controls=f'<a href="/plan?{urlencode({"plan_tz":zone})}">View Plan</a>'
    else:
        base=hidden('nonce',nonce)+hidden('tz',zone)+hidden('day',data['today'])
        choices=''.join(f'<option value="{value}"{" selected" if data["legs"]==value else ""}>{label}</option>' for value,label in [('unknown','Not reported'),('normal','Normal'),('heavy','Unusually heavy')])
        controls=f'''<form method="post" action="/plan/feedback" class="plan-feedback">{base}<label for="plan-legs">Legs today</label><select name="legs" id="plan-legs">{choices}</select><button type="submit">Update</button></form>'''
        if not data['today_actual']:
            controls+=f'<form method="post" action="/plan/intent" class="plan-intent">{base}{hidden("category",rec["category"])}<button type="submit">I plan to do this</button></form>'
        if data['intent']:
            intended=json.loads(data['intent']['recommendation_json'])['recommendation']['category']
            controls+=f'<p class="plan-intent-note">Recorded intent: {escape(intended)} · confirmed {local_time(data["intent"]["confirmed_at"],compact=True)}. This remains separate if today’s suggestion changes.</p>'
        else:
            controls+='<p class="plan-intent-note">No recorded intent. A suggestion does not mean you accepted it.</p>'
    actual=''
    if data['today_actual']:
        links='; '.join(f'<a href="/activities/{r["activity_id"]}">{escape(r["classification"]["category"])}</a>' for r in data['today_actual'])
        actual=f'<p class="plan-actual">Recorded today: {links}. Additional riding is optional.</p>'
    display_date=date.fromisoformat(data['today']).strftime('%a, %b %d' if compact else '%a, %b %d, %Y')
    return f'''<section class="panel next-recommended" data-recommended-day="{data['today']}" aria-labelledby="next-recommended-heading"><h2 id="next-recommended-heading">{'Next Recommended Ride' if compact else 'Today’s ride'} · <time datetime="{data['today']}">{display_date}</time></h2>{ride_content(rec)}{provisional}{actual}{controls}</section>'''


def correction_form(ride,nonce,zone,*,back='plan'):
    category=ride['classification']['category']
    options='<option value="automatic">Use source inference</option>'+''.join(f'<option value="{escape(c,quote=True)}"{" selected" if category==c and ride["classification"]["confidence"]=="rider confirmed" else ""}>{escape(c)}</option>' for c in CATEGORIES)
    identity=ride['activity_id']
    return f'''<form method="post" action="/plan/classification" class="plan-correction">{hidden('nonce',nonce)}{hidden('tz',zone)}{hidden('activity_id',identity)}{hidden('back',back)}<label for="category-{identity}">Correct actual category</label><select id="category-{identity}" name="category">{options}</select><button type="submit">Save category</button></form>'''


def plan_page(store,query='',nonce=''):
    zone=query_zone(query,'plan_tz')
    if zone is None:
        return shell('Plan','<header><h1>Plan</h1></header><section class="panel" data-calendar-timezone="plan_tz"><p>Enable JavaScript to use your rider-local dates.</p></section>',active='plan')
    data=plan(store,zone.key)
    latest=data['latest_hard']
    last=f'<a href="/activities/{latest["activity_id"]}">{escape(latest["classification"]["category"])}</a> · {latest["day"]} · {escape(latest["classification"]["confidence"])}' if latest else 'No classified hard session in available history.'
    freshness='Synced today; completed prior dates without rides may count as assumed rest for planning.' if data['fresh'] else 'Sync is stale or unknown; today’s suggestion is provisional. Refresh from Settings before quality work.'
    sync=local_time(data['sync_at'],compact=True) if data['sync_at'] else 'Never'
    cards=[]
    # Today is shown once at the top, with its hard number if applicable.
    for rec in data['days']:
        number=f' · Hard day #{rec["hard_number"]}' if rec['hard_number'] else ''
        if rec['offset']==0:
            today_number=f'<p class="plan-hard-number">Today{number}</p>'
            continue
        relative='Tomorrow' if rec['offset']==1 else f'In {rec["offset"]} days'
        explicit=date.fromisoformat(rec['day']).strftime('%a, %b %d, %Y')
        cards.append(f'''<li class="plan-day{" plan-hard" if rec['hard'] else ""}" data-plan-day="{rec['day']}" data-hard-number="{rec['hard_number'] or ''}"><div class="plan-date"><strong>{relative}{number}</strong><time datetime="{rec['day']}">{explicit}</time><span>Conditional projection</span></div><div>{ride_content(rec)}</div></li>''')
    history=[]
    for ride in reversed(data['history']):
        c=ride['classification']
        history.append(f'''<article class="plan-history-row"><p><time>{ride['day']}</time> · <a href="/activities/{ride['activity_id']}">{escape(ride['title'])}</a></p><p><strong>{escape(c['category'])}</strong> · {escape(c['confidence'])}</p><p>{escape(c['reason'])}</p>{correction_form(ride,nonce,zone.key)}</article>''')
    recent=''.join(f'<li><time>{r["day"]}</time> — {escape(r["state"])}</li>' for r in data['recent_days'])
    payload={k:v for k,v in data.items() if k!='history'}
    from .home import safe_json
    return shell('Plan',f'''<header data-calendar-timezone="plan_tz"><h1>Plan</h1><p>Today through the next three hard recommendations · {escape(zone.key)}</p></header><div class="plan-workspace">{today_number}{today_card(data,nonce)}
<section class="panel plan-context"><h2>Actual training context</h2><p>Latest actual hard training: {last}</p><p>{data['recent_hard_dates']} actual hard dates in the current rolling seven · last successful sync: {sync}</p><p>{freshness} <a href="/settings">Settings / Sync now</a></p><p>{'Legs not reported: quality work is conditional on normal legs during warmup.' if data['legs']=='unknown' else 'Leg feedback applies only to today; future dates assume recovery and normal legs.'}</p><p>Current FTP goal: toward 195 W, eventually above 200 W. Approximate coaching targets are current context, not historical zones or a readiness diagnosis.</p>{'<p>Undated or timezone-unknown activity evidence remains excluded from date-based rotation.</p>' if data['undated'] else ''}</section>
<section aria-labelledby="rotation-heading"><h2 id="rotation-heading">Upcoming rotation</h2><p class="plan-rotation-help">Projections assume the suggested hard rides occur and legs recover. Actual rides, skipped dates, sync and corrections recompute this rotation. Review uncertain classifications before relying on hard-day spacing.</p><ol class="plan-days">{''.join(cards)}</ol></section>
<details class="panel plan-history"><summary>Recent actual rides · inspect or correct classification</summary>{''.join(history) or '<p>No completed cycling rides yet.</p>'}</details>
<details class="panel plan-help"><summary>How recommendations differ from actual training</summary><p>A recommendation is a suggestion. “I plan to do this” records a separate, dated intent before a ride; it never changes activity evidence. Skipping a suggested day is not a failed workout. Future projections are not completed rides and do not contribute stress to Training State.</p><p>Race titles are hints; only your confirmation establishes a race category. Source inference describes observed power patterns against dated FTP, never HR stress alone. Short efforts suggest VO2; sustained efforts suggest threshold; correct these when you know the actual workout. Missing power can hide harder effort.</p><p>Two recovery calendar dates follow hard training. Missing prior dates are assumed rest for planning only when covered by successful sync; today is still unfinished. A hard day is generally eligible after these two dates, subject to the two-hard-dates-per-seven target and normal legs. Threshold is the initial structured choice for the FTP goal; recent threshold work suggests VO2 next. This is a working heuristic.</p><ul>{recent}</ul>{detail_rows([('Planner',data['version']),('Classification',data['classifier']),('As of',data['as_of']),('Current dated FTP',str(data['current_ftp'].get('value'))+' W'),('FTP provenance',data['current_ftp'].get('status')),('Total displayed dates',len(data['days']))])}</details>
<script type="application/json" id="plan-data">{safe_json(payload)}</script><script src="/static/planning.js" defer></script></div>''',active='plan')


def activity_panel(store,activity_id,nonce):
    context=activity_context(store,activity_id); c=context['classification']; intent=context['intent']
    message='No recorded intent. No prior recommendation is assigned retrospectively to this ride.'
    if intent:
        rec=json.loads(intent['recommendation_json'])['recommendation']; intended=rec['category']
        if c['confidence']=='uncertain' or c['category'] in ('Uncertain','Hard (type uncertain)'):
            outcome='Actual stimulus is uncertain; confirm its category before comparing.'
        elif c['category']==intended:
            outcome='Actual category aligns with the confirmed intended stimulus; interval completion is not established by category alone.'
        else:
            outcome='Actual category differs from the confirmed intent. The recorded ride informs the next rotation; this is not a failed workout.'
        message=f'Recorded date-level cycling intent: {escape(intended)} · confirmed {local_time(intent["confirmed_at"],compact=True)}. {outcome} This date-level context does not establish a unique activity match.'
    # The review page obtains browser timezone before exposing correction controls.
    correction=correction_form(dict(activity_id=activity_id,classification=c),nonce,'',back='activity') if context.get('cycling',True) else ''
    return f'''<section class="panel activity-plan-context" aria-labelledby="activity-plan-heading"><h2 id="activity-plan-heading">Workout context</h2><p>Actual: <strong>{escape(c['category'])}</strong> · {escape(c['confidence'])}</p><p>{escape(c['reason'])}</p><p>{message}</p>{correction}<p><a href="/plan">View Plan</a></p><script src="/static/planning.js" defer></script></section>'''
