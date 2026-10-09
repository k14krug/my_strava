#!/usr/bin/env python3
"""P4-01 continuation only: dated FTP, native recording segments, separate models.

All outputs are PRIVATE except explicitly whitelisted aggregate/relative-day reports.
No production writes, repaired power, outdoor admission or inferred athlete state.
"""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.research_training_state import readonly_store, normalized_power, dump, curves

VERSION = 'p4-01-dated-ftp-segments-v1'
FTP_SOURCE = 'Owner-provided Strava UI historical FTP setting'


def read_ftp(path, expected_count=66):
    with path.open() as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ['effective_from_date', 'effective_until_date_exclusive', 'ftp_watts']:
            raise ValueError('Unexpected FTP columns')
        rows = list(reader)
    if len(rows) != expected_count:
        raise ValueError('Unexpected FTP row count; request source correction')
    result = []
    for r in rows:
        start = date.fromisoformat(r['effective_from_date'])
        end = date.fromisoformat(r['effective_until_date_exclusive']) if r['effective_until_date_exclusive'] else None
        watts = int(r['ftp_watts'])
        if watts <= 0 or (end is not None and end <= start):
            raise ValueError('Invalid FTP interval/value')
        result.append(dict(start=start, end=end, watts=watts))
    for i, r in enumerate(result):
        if r['end'] != (result[i+1]['start'] if i+1 < len(result) else None):
            raise ValueError('Intervals must be consecutive, strictly increasing and finally open')
    return result


def lookup(history, day):
    if day is None:
        return None
    index = bisect_right([r['start'] for r in history], day) - 1
    return history[index] if index >= 0 else None


def resolved_ftp(history, day, absolute):
    """Use accepted calendar date; unknown timezone gets a +/-1-day sensitivity.

    This is a date ambiguity flag, not an inferred timezone. Withhold normalized
    results when plausible adjacent dates select different source intervals.
    """
    selected = lookup(history, day)
    uncertain = not absolute and day is not None and any(
        lookup(history, day + timedelta(days=delta)) != selected for delta in (-1, 1))
    return selected, uncertain


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def segments(times, powers, intervals=None):
    """One-second half-open sample bins; split at every bad value/time or gap.

    All occurrences of duplicate timestamps are excluded, not arbitrarily deduped.
    Backwards time makes the source unusable. Timer mode includes only bins fully
    inside a proved start/stop pair and splits at each timer restart.
    """
    if len(times) != len(powers):
        raise ValueError('Unpaired stream')
    if any(finite(t) and t % 1 != 0 for t in times):
        return [], 'subsecond_timestamps_unsupported'
    known = [t for t in times if finite(t)]
    if any(b < a for a, b in zip(known, known[1:])):
        return [], 'backwards_timestamps'
    count = Counter(known); result = []; current = []; previous = None; prior_interval = None
    for i, (t, p) in enumerate(zip(times, powers)):
        interval = next((j for j, (a, b) in enumerate(intervals) if a <= t and t+1 <= b), None) if intervals is not None and finite(t) else None
        valid = finite(t) and finite(p) and p >= 0 and count[t] == 1 and (intervals is None or interval is not None)
        if not valid or previous is None or t != previous+1 or interval != prior_interval:
            if current:
                result.append(current)
            current = []
        if valid:
            current.append(i)
        previous = t if valid else None; prior_interval = interval
    if current:
        result.append(current)
    return result, None


def timer_intervals(events):
    intervals = []; active = None; previous = None
    for e in events:
        if e['event'] != 'timer':
            continue
        t = epoch(e['timestamp'])
        if t is None or (previous is not None and t < previous):
            return None, 'invalid_event_time'
        previous = t
        if e['event_type'] == 'start' and active is None:
            active = t
        elif e['event_type'] in ('stop', 'stop_all', 'stop_disable', 'stop_disable_all') and active is not None and t > active:
            intervals.append((active, t)); active = None
        else:
            return None, 'unpaired_or_unsupported_timer_event'
    if active is not None or not intervals:
        return None, 'unclosed_or_missing_timer_events'
    return intervals, None


def epoch(value):
    if not value:
        return None
    stamp = datetime.fromisoformat(value)
    return stamp.timestamp() if stamp.tzinfo is not None else None


def metrics(parts, powers, ftp, minimum):
    selected = [p for p in parts if len(p) >= minimum]
    seconds = sum(map(len, selected))
    work = math.fsum(powers[i] for part in selected for i in part) / 1000
    detail = []
    for part in selected:
        npower = normalized_power([powers[i] for i in part])
        detail.append(dict(first_index=part[0], last_index=part[-1], seconds=len(part), np=npower,
            work_kj=math.fsum(powers[i] for i in part)/1000,
            stress=len(part)/36*(npower/ftp)**2 if ftp is not None else None))
    stress = math.fsum(p['stress'] for p in detail) if detail and ftp is not None else None
    windows = sum(p['seconds']-29 for p in detail)
    pooled_np = (math.fsum(p['np']**4*(p['seconds']-29) for p in detail)/windows)**.25 if windows else None
    return dict(seconds=seconds, work_kj=work, segments=len(detail), stress=stress,
        pooled_np=pooled_np, pooled_stress=seconds/36*(pooled_np/ftp)**2 if windows and ftp else None,
        details=detail)


def source_data(store, saved):
    if saved.get('extraction_id'):
        eid = saved['extraction_id']
        records = list(store.connection.execute('SELECT timestamp,power FROM records WHERE extraction_id=? ORDER BY record_index', (eid,)))
        session = dict(store.connection.execute('SELECT * FROM sessions WHERE extraction_id=?', (eid,)).fetchone())
        events = [dict(r) for r in store.connection.execute('SELECT * FROM events WHERE extraction_id=? ORDER BY source_order', (eid,))]
        return [epoch(r[0]) for r in records], [r[1] for r in records], session, events, None
    sid = saved['api_evidence']['stream_source_id']
    data = json.loads(store.connection.execute('SELECT evidence_json FROM strava_stream_sources WHERE source_id=?', (sid,)).fetchone()[0])
    return data['time']['data'], data['watts']['data'], {}, [], data.get('moving', {}).get('data')


def evaluate(store, original, history):
    saved = {identity: json.loads(payload) for identity, payload in store.connection.execute("SELECT activity_id,result_json FROM performance_history WHERE policy='virtual-power-evidence-v2'")}
    results = []
    for old in original:
        day = date.fromisoformat(old['day']) if old['day'] else None
        selected, uncertain = resolved_ftp(history, day, old['absolute_date'])
        r = dict(old, dated_ftp=selected, ftp_date_uncertain=uncertain, ftp_source=FTP_SOURCE,
            segment_work_kj=None, stress600=None, stress30=None, floor_stress=None,
            matched_work_kj=None, full_timer_stress=None, full_timer_tolerance1_stress=None)
        if old['eligible']:
            times, powers, session, events, moving = source_data(store, saved[old['activity_id']])
            ftp = selected['watts'] if selected is not None and not uncertain else None
            parts, problem = segments(times, powers)
            observed_seconds = sum(map(len, parts))
            m30 = metrics(parts, powers, ftp, 30); m600 = metrics(parts, powers, ftp, 600)
            intervals, timer_error = timer_intervals(events)
            timer_parts, _ = segments(times, powers, intervals) if intervals is not None else ([], None)
            timer_metrics = metrics(timer_parts, powers, ftp, 600)
            active_seconds = sum(b-a for a, b in intervals) if intervals else None
            covered_active = sum(map(len, timer_parts))
            timer_delta = active_seconds-session['total_timer_time'] if active_seconds is not None and session.get('total_timer_time') is not None else None
            boundaries = bool(intervals and epoch(session.get('start_time')) == intervals[0][0]
                and epoch(session.get('timestamp')) is not None and intervals[-1][1] <= epoch(session['timestamp'])
                and finite(session.get('total_elapsed_time'))
                and intervals[-1][1] <= intervals[0][0] + session['total_elapsed_time'])
            complete = bool(boundaries and covered_active == active_seconds and timer_metrics['seconds'] == active_seconds)
            r.update(segment_work_kj=math.fsum(powers[i] for part in parts for i in part)/1000 if parts else None,
                stress600=m600['stress'], stress30=m30['stress'], matched_work_kj=m600['work_kj'] if m600['stress'] is not None else None,
                segment600=m600, segment30=m30, stream_problem=problem,
                sample_count=len(powers), observed_seconds=observed_seconds,
                omitted_short_seconds30=observed_seconds-m30['seconds'], omitted_short_seconds600=observed_seconds-m600['seconds'],
                invalid_power_samples=sum(not finite(p) or p<0 for p in powers),
                duplicate_timestamp_samples=sum(n for n in Counter(t for t in times if finite(t)).values() if n>1),
                missing_timestamp_samples=sum(not finite(t) for t in times),
                discontinuities=sum(finite(a) and finite(b) and b-a!=1 for a,b in zip(times,times[1:])),
                gap_seconds=sum(max(0,b-a-1) for a,b in zip(times,times[1:]) if finite(a) and finite(b)),
                timer=dict(intervals=intervals, error=timer_error, summary_seconds=session.get('total_timer_time'),
                    elapsed_seconds=session.get('total_elapsed_time'), event_active_seconds=active_seconds,
                    delta=timer_delta, covered_active_seconds=covered_active, boundary_verified=boundaries,
                    metrics=timer_metrics, uncovered_active_seconds=active_seconds-covered_active if active_seconds is not None else None),
                api_moving_false_samples=sum(v is False for v in moving) if moving is not None else None,
                api_moving_samples=len(moving) if moving is not None else None)
            if old['whole_power_reason'] is None:
                r['floor_stress'] = m30['stress']
            if complete and timer_delta is not None:
                if abs(timer_delta)<1e-6:
                    r['full_timer_stress'] = timer_metrics['stress']
                if abs(timer_delta)<=1:
                    r['full_timer_tolerance1_stress'] = timer_metrics['stress']
            # A matching sample-count summary alone does not prove timer coverage.
            r['summary_matches_samples'] = session.get('total_timer_time') == len(powers)
        results.append(r)
    return results


METRICS = ('segment_work_kj', 'matched_work_kj', 'stress600', 'stress30', 'floor_stress', 'full_timer_stress')


def daily_models(rows, as_of):
    by_day = defaultdict(list)
    for r in rows:
        if r['kind'] in ('Ride', 'Virtual Ride') and r['day'] and date.fromisoformat(r['day']) <= as_of:
            by_day[date.fromisoformat(r['day'])].append(r)
    start = min(by_day); days = []
    for offset in range((as_of-start).days+1):
        day = start+timedelta(days=offset); group = by_day[day]
        row = dict(day=str(day), rides=len(group), no_record=not group,
            eligible=sum(r['eligible'] for r in group), outdoor=sum(r['kind']=='Ride' for r in group),
            missing_ftp=sum(r['dated_ftp'] is None for r in group),
            best20=max((r['best20'] for r in group if r['eligible']), default=None),
            elapsed_hours=math.fsum(r['duration'] or 0 for r in group)/3600)
        for key in METRICS:
            values = [r[key] for r in group if r[key] is not None]
            row[key] = math.fsum(values) if values else None
            row[key+'_contributors'] = len(values)
            row[key+'_missing'] = len(group)-len(values)
        # Unknown no-record dates are not rest. Even a complete recorded-day
        # total is only a cycling-ledger value; never a whole-athlete load claim.
        row['complete_recorded_day_stress'] = row['full_timer_stress'] if group and row['full_timer_stress_missing']==0 else None
        days.append(row)
    for i, row in enumerate(days):
        for n in (7,42):
            window = days[max(0,i+1-n):i+1]
            row[f'window{n}'] = dict(days=len(window), rides=sum(d['rides'] for d in window),
                no_record_days=sum(d['no_record'] for d in window),
                **{key:dict(subtotal=math.fsum(d[key] for d in window if d[key] is not None) if any(d[key] is not None for d in window) else None,
                    contributors=sum(d[key+'_contributors'] for d in window),
                    missing=sum(d[key+'_missing'] for d in window)) for key in METRICS})
    industry = curves([r['complete_recorded_day_stress'] for r in days])
    for row, line in zip(days, industry):
        row['industry_unknown_seed'] = line
    return days


def coverage(rows):
    cycling = [r for r in rows if r['kind'] in ('Ride','Virtual Ride')]
    groups = dict(cycling=cycling, virtual=[r for r in cycling if r['kind']=='Virtual Ride'],
        outdoor=[r for r in cycling if r['kind']=='Ride'], eligible=[r for r in cycling if r['eligible']],
        complete_envelope=[r for r in cycling if r['eligible'] and r['whole_power_reason'] is None],
        incomplete_envelope=[r for r in cycling if r['eligible'] and r['whole_power_reason'] is not None])
    return {name:dict(denominator=len(group), dated_ftp=sum(r['dated_ftp'] is not None for r in group),
        no_dated_ftp=sum(r['dated_ftp'] is None for r in group), uncertain_ftp_date=sum(r['ftp_date_uncertain'] for r in group),
        **{key:sum(r[key] is not None for r in group) for key in METRICS},
        full_timer_tolerance1=sum(r['full_timer_tolerance1_stress'] is not None for r in group)) for name,group in groups.items()}


def periods(days, history):
    peak = max(range(len(days)), key=lambda i:days[i]['best20'] or -1)
    ends = [('A latest',len(days)-1),('B highest best-20 + seven days',min(len(days)-1,peak+7)),
        ('C greatest elapsed subtotal',max(range(41,len(days)), key=lambda i:sum(d['elapsed_hours'] for d in days[i-41:i+1]))),
        ('D greatest matched 42-day work',max(range(41,len(days)), key=lambda i:days[i]['window42']['matched_work_kj']['subtotal'] or -1))]
    drop = min(range(1,len(history)), key=lambda i:history[i]['watts']/history[i-1]['watts'])
    target = history[drop]['start'] + timedelta(days=20)
    ends.append(('E around largest reported FTP reduction', min(range(len(days)),key=lambda i:abs((date.fromisoformat(days[i]['day'])-target).days))))
    return [dict(label=label, window=days[end]['window42'],
        series=[{k:v for k,v in d.items() if k not in ('day','industry_unknown_seed')}|dict(relative_day=i+1)
            for i,d in enumerate(days[max(0,end-41):end+1])]) for label,end in ends]


def plot(periods, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(13,10),constrained_layout=True)
    for pair,period in zip(axes,[periods[i] for i in (0,3,4)]):
        for ax,key,label in zip(pair,('matched_work_kj','stress600'),('Matched segment work (kJ/day)','Segment stress points/day')):
            series=period['series'];x=[d['relative_day'] for d in series]
            for n,color in [(7,'#234f73'),(42,'#ac792b')]:
                ax.plot(x,[d[f'window{n}'][key]['subtotal']/n if d[f'window{n}'][key]['subtotal'] is not None else math.nan for d in series],label=f'{n}-day subtotal / {n}',color=color)
            missing=[d['relative_day'] for d in series if d[key+'_missing']]
            ax.scatter(missing,[0]*len(missing),marker='x',color='#ad3737',label='Recorded ride omitted')
            no_record=[d['relative_day'] for d in series if d['no_record']]
            ax.scatter(no_record,[0]*len(no_record),marker='o',facecolors='none',edgecolors='#999',label='No recorded ride (not proven rest)')
            ax.set_title(period['label'],loc='left');ax.set_ylabel(label);ax.set_xlabel('Relative day');ax.spines[['right','top']].set_visible(False)
    handles, labels = axes[0,0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncol=2, fontsize=9)
    fig.suptitle('Same dated-FTP segments ≥600 s; partial recorded contributions, never full-history load')
    fig.savefig(output/'anonymized-ftp-model-comparison.png',dpi=150);plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--input-dir',type=Path,required=True)
    p.add_argument('--ftp',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--as-of',type=date.fromisoformat,required=True);p.add_argument('--plots',action='store_true')
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    history=read_ftp(a.ftp);original=json.loads((a.input_dir/'activities.json').read_text())
    before=hashlib.sha256((a.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()
    cached=json.loads((a.input_dir/'raw-inventory.json').read_text())
    if cached['database_sha256']!=before:raise ValueError('Census snapshot mismatch')
    store=readonly_store(a.data_dir)
    try:rows=evaluate(store,original,history)
    finally:store.close()
    if hashlib.sha256((a.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()!=before:raise ValueError('Snapshot mutated')
    days=daily_models(rows,a.as_of);examples=periods(days,history)
    summary=dict(version=VERSION,as_of=str(a.as_of),ftp=dict(rows=len(history),sha256=hashlib.sha256(a.ftp.read_bytes()).hexdigest(),source=FTP_SOURCE,first=str(history[0]['start']),last=str(history[-1]['start']),structurally_valid=True),
        coverage=coverage(rows),by_year={year:coverage([r for r in rows if r['year']==year]) for year in sorted({r['year'] for r in rows})},
        latest={str(n):dict(coverage=coverage([r for r in rows if r['day'] and a.as_of-timedelta(days=n-1)<=date.fromisoformat(r['day'])<=a.as_of]),window=days[-1][f'window{n}']) for n in (7,42)},
        calendar_days=len(days),no_record_days=sum(d['no_record'] for d in days),
        actual_ctl_atl_tsb='unavailable: unknown initial state, missing sessions and unproven rest days',
        periods=[{k:v for k,v in period.items() if k!='series'} for period in examples])
    dump(a.output_dir/'activities-private.json',rows);dump(a.output_dir/'daily-private.json',days)
    dump(a.output_dir/'periods.json',examples);dump(a.output_dir/'summary.json',summary)
    if a.plots:plot(examples,a.output_dir)
    print(json.dumps(dict(coverage=summary['coverage'],latest=summary['latest']),indent=2))


if __name__=='__main__':main()
