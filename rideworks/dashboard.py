"""Read-only mileage presentation and accepted Performance snapshots."""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from math import fsum

from .goals import annual_goal, browser_zone
from .history import presentation
from .performance import performance_history
from .performance_view import performance_view
from .recent_context import select_recent_context

CYCLING = ('ride', 'virtual ride', 'cycling', 'biking')
METRES_PER_MILE = 1609.344


def mileage(rows, zone_name, *, as_of=None):
    zone = browser_zone(zone_name)
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError('Dashboard as-of must be an absolute instant.')
    today = as_of.astimezone(zone).date()
    cycling = [r for r in rows if r['activity_type'].casefold() in CYCLING]
    dated = []
    unknown = missing = future = 0
    for row in cycling:
        if row['start_time'] is None:
            missing += 1
            continue
        stamp = datetime.fromisoformat(row['start_time'])
        if row['absolute_time']:
            day = stamp.astimezone(zone).date()
            if stamp > as_of:
                future += 1
                continue
        else:
            day = stamp.date()  # Supported source date; no invented timezone.
            unknown += 1
            if day > today:
                future += 1
                continue
        dated.append((row, day))

    def period(start, end):
        selected = [r for r, day in dated if start <= day < end]
        amounts = {'file': [], 'api': []}
        unavailable = 0
        for row in selected:
            if row['distance'] is None:
                unavailable += 1
            else:
                kind = 'api' if row['distance_source']['context'] == 'Strava API summary' else 'file'
                amounts[kind].append(row['distance'])
        count = sum(len(values) for values in amounts.values())
        return dict(start=start.isoformat(), end_exclusive=end.isoformat(),
                    miles=fsum(v for values in amounts.values() for v in values)/METRES_PER_MILE
                        if count or not unavailable else None,
                    contributing_activities=count, dated_cycling_activities=len(selected),
                    file_count=len(amounts['file']), file_miles=fsum(amounts['file'])/METRES_PER_MILE,
                    api_count=len(amounts['api']), api_miles=fsum(amounts['api'])/METRES_PER_MILE,
                    distance_unavailable=unavailable, date_unavailable_excluded=missing)

    end = today + timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    weeks = [period(monday-timedelta(weeks=i), min(monday-timedelta(weeks=i-1), end))
             for i in range(11, -1, -1)]
    recent = sorted(cycling, key=lambda r:r['activity_id'])
    recent.sort(key=lambda r:(r['date_key'] is not None, r['date_key'] or ''), reverse=True)
    return dict(timezone=zone_name, as_of=as_of.isoformat(), today=today.isoformat(), year=today.year,
                ytd=period(date(today.year,1,1), end), last7=period(today-timedelta(days=6), end),
                prior7=period(today-timedelta(days=13), today-timedelta(days=6)), weeks=weeks,
                recent=recent[:6], diagnostics=dict(cycling_activities=len(cycling),
                    excluded_noncycling=len(rows)-len(cycling), date_unavailable=missing,
                    timezone_unknown=unknown, future_excluded=future,
                    included_classifications=dict(Counter(r['activity_type'] for r in cycling)),
                    excluded_classifications=dict(Counter(r['activity_type'] for r in rows if r['activity_type'].casefold() not in CYCLING))))


def goal_progress(year, today, actual, target):
    if target is None or actual is None:
        return None
    target = float(target)
    day = date.fromisoformat(today)
    days = (date(year+1,1,1)-date(year,1,1)).days
    elapsed = (day-date(year,1,1)).days+1
    expected = target * elapsed / days
    return dict(target_miles=target, actual_miles=actual, percent=100*actual/target,
                remaining_miles=max(0,target-actual), calendar_days_elapsed=elapsed,
                calendar_days_in_year=days, target_to_date=expected, pace_difference=actual-expected)


def dashboard(store, zone_name, *, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    data = mileage([presentation(s) for s in store.activity_history()], zone_name, as_of=as_of)
    goal = annual_goal(store, data['year'])
    data['target_miles'] = goal['target_miles'] if goal else None
    data['goal'] = goal_progress(data['year'], data['today'], data['ytd']['miles'], data['target_miles'])
    history = performance_history(store)
    view = performance_view(history['points'], as_of=as_of)
    selected = {name:history['points'][index] if index is not None else None
                for name,index in view['summaries'].items() if name in ('current','latest')}
    start = view['range_starts']['1yr']
    seed = next((s for s in reversed(view['rolling']) if s['at'] <= start), None)
    series = ([dict(at=start,index=seed['index'])] if seed else []) + [s for s in view['rolling'] if s['at'] > start]
    data['performance'] = dict(policy=history['policy'], method=history['method'], pending=history['pending'],
        **selected, range_start=start, range_end=view['as_of'],
        rolling=[dict(at=s['at'], point=history['points'][s['index']] if s['index'] is not None else None)
                 for s in series],
        recent=select_recent_context(history, selected['latest']['activity_id']) if selected['latest'] else None)
    sync = store.connection.execute('SELECT successful_at FROM strava_sync_state WHERE singleton=1').fetchone()
    data['successful_sync'] = datetime.fromtimestamp(sync[0],timezone.utc).isoformat() if sync and sync[0] else None
    return data
