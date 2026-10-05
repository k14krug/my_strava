"""Read-time recent comparison from current trusted Performance evidence only."""
from datetime import datetime, timedelta

from .analysis import BEST_20_METHOD, WINDOW_SAMPLES
from .performance import POLICY, performance_history


def _trusted(result):
    return (result['eligible'] and result['policy'] == POLICY
            and result['method'] == BEST_20_METHOD
            and result['duration_seconds'] == WINDOW_SAMPLES
            and result['classification']['activity_type'] == 'Virtual Ride')


def select_recent_context(history, activity_id):
    """Select in (t - 42 days, t); no raw stream reads or materialization.

    ``history`` is the accepted current metadata/result boundary. Its stale
    input suppression applies to current and prior results alike.
    """
    results = {r['activity_id']: r for r in history['results']}
    result = results.get(activity_id)
    context = dict(activity_id=activity_id, available=False, reason=None,
                   current=None, prior=None, window_start=None, window_end=None,
                   policy=POLICY, method=BEST_20_METHOD,
                   duration_seconds=WINDOW_SAMPLES, pending_history=history['pending'])
    if result is None:
        context['reason'] = 'performance_rebuild_required'
        return context
    if not _trusted(result):
        context['reason'] = result['reason'] or 'not_trusted_performance_result'
        return context
    current = next((p for p in history['points'] if p['activity_id'] == activity_id), None)
    context['current'] = current or result
    if current is None:
        context['reason'] = 'activity_date_unavailable'
        return context
    if not current['absolute_time']:
        context['reason'] = 'activity_timezone_unknown'
        return context
    end = datetime.fromisoformat(current['start_time'])
    start = end - timedelta(days=42)
    context.update(window_start=start.isoformat(), window_end=end.isoformat())
    candidates = []
    for point in history['points']:
        prior_result = results.get(point['activity_id'])
        if (point['activity_id'] == activity_id or not point['absolute_time']
                or prior_result is None or not _trusted(prior_result)):
            continue
        stamp = datetime.fromisoformat(point['start_time'])
        if start < stamp < end:
            candidates.append((point, stamp))
    prior = min(candidates, key=lambda item: (-item[0]['average_watts'], item[1],
                                              item[0]['activity_id']), default=None)
    if prior is None:
        context['reason'] = 'no_qualifying_prior_result'
    else:
        context.update(available=True, prior=prior[0])
    return context


def recent_context(store, activity_id):
    return select_recent_context(performance_history(store), activity_id)
