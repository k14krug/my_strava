"""Cheap presentation summaries of persisted trusted results; no native reads.

The rolling signal is the raw maximum in (t - 42 days, t], tied by earliest
Activity start then ID. Events occur at ride starts and exact 42-day expiry.
An unknown-zone Activity date cannot establish membership in a clock window;
that result remains in source-dated period views and lifetime evidence, explicitly.
"""
from calendar import monthrange
from datetime import datetime, timedelta, timezone
import heapq


def _stamp(point):
    return datetime.fromisoformat(point['start_time']) if point['absolute_time'] else None


def months_before(stamp, count):
    month_index = stamp.year * 12 + stamp.month - 1 - count
    year, month = divmod(month_index, 12)
    month += 1
    return stamp.replace(year=year, month=month, day=min(stamp.day, monthrange(year, month)[1]))


def strongest(points, indexes):
    return min(indexes, key=lambda i: (-points[i]['average_watts'], points[i]['date_key'], points[i]['activity_id']), default=None)


def performance_view(points, *, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError('Performance as-of time must have an established timezone')
    as_of = as_of.astimezone(timezone.utc)
    window = timedelta(days=42)
    timed = [(i, _stamp(p)) for i, p in enumerate(points) if p['absolute_time']]
    timed = [(i, t) for i, t in timed if t <= as_of]
    events = {}
    for i, stamp in timed:
        events.setdefault(stamp, []).append(i)
        if stamp + window <= as_of:
            events.setdefault(stamp + window, [])
    heap, steps = [], []
    stamps = dict(timed)
    previous = object()
    for stamp, arrivals in sorted(events.items()):
        for i in arrivals:
            heapq.heappush(heap, (-points[i]['average_watts'], stamps[i], points[i]['activity_id'], i))
        while heap and heap[0][1] <= stamp - window:
            heapq.heappop(heap)
        selected = heap[0][-1] if heap else None
        if selected != previous:
            steps.append(dict(at=stamp.isoformat(), index=selected))
            previous = selected
    current = strongest(points, [i for i, stamp in timed if as_of - window < stamp <= as_of])
    latest = max(range(len(points)), key=lambda i: (points[i]['date_key'], points[i]['activity_id']), default=None)
    year_cutoff = months_before(as_of, 12)
    year = strongest(points, [i for i, stamp in timed if year_cutoff <= stamp <= as_of])
    lifetime = strongest(points, range(len(points)))
    ages = {str(i): int((as_of - stamp).total_seconds() // 86400) for i, stamp in timed}
    return dict(as_of=as_of.isoformat(), rolling_days=42,
                range_starts={key: months_before(as_of, months).isoformat()
                              for key, months in [('3mo',3),('6mo',6),('1yr',12),('3yr',36)]},
                rolling=steps, summaries=dict(current=current, latest=latest, year=year, lifetime=lifetime),
                ages_days=ages, unknown_timezones=sum(not p['absolute_time'] for p in points))
