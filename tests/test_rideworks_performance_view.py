"""Synthetic presentation-window tests, separate from persisted best-20 analysis."""
import copy
from datetime import datetime, timedelta, timezone
import unittest

from rideworks.performance_view import months_before, performance_view

BASE = datetime(2024, 1, 1, tzinfo=timezone.utc)


def point(day, watts, identity=None, absolute=True):
    stamp = BASE + timedelta(days=day)
    if not absolute: stamp = stamp.replace(tzinfo=None)
    return dict(activity_id=identity or str(day), start_time=stamp.isoformat(),
                date_key=stamp.replace(tzinfo=None).isoformat(), date_day=stamp.date().isoformat(),
                absolute_time=absolute, average_watts=watts, rounded_watts=int(watts + .5))


class PerformanceViewTests(unittest.TestCase):
    def test_rolling_best_expires_at_exactly_42_days_and_preserves_gaps(self):
        points=[point(0,200),point(10,150),point(60,180)]
        view=performance_view(points,as_of=BASE+timedelta(days=110))
        self.assertEqual([(datetime.fromisoformat(s['at'])-BASE).days for s in view['rolling']], [0,42,52,60,102])
        self.assertEqual([s['index'] for s in view['rolling']], [0,1,None,2,None])
        self.assertIsNone(view['summaries']['current'])
        self.assertEqual(view['summaries']['latest'],2)

    def test_new_ride_is_included_old_boundary_excluded_and_zero_is_valid(self):
        points=[point(0,200),point(42,0)]
        view=performance_view(points,as_of=BASE+timedelta(days=42))
        self.assertEqual(view['summaries']['current'],1)
        self.assertEqual(view['rolling'][-1]['index'],1)
        self.assertEqual(points[1]['rounded_watts'],0)

    def test_raw_comparison_and_exact_tie_choose_earliest_activity(self):
        points=[point(0,200.1,'a'),point(1,200.2,'b'),point(2,200.2,'c')]
        view=performance_view(points,as_of=BASE+timedelta(days=3))
        self.assertEqual(view['summaries']['current'],1)
        self.assertEqual(view['summaries']['lifetime'],1)
        self.assertEqual([s['index'] for s in view['rolling']],[0,1])
        self.assertEqual([p['rounded_watts'] for p in points],[200,200,200])

    def test_calendar_ranges_clamp_leap_day_and_month_end(self):
        stamp=datetime(2024,2,29,12,34,tzinfo=timezone.utc)
        self.assertEqual(months_before(stamp,12),datetime(2023,2,28,12,34,tzinfo=timezone.utc))
        self.assertEqual(months_before(datetime(2024,5,31,tzinfo=timezone.utc),3).date().isoformat(),'2024-02-29')
        self.assertEqual(set(performance_view([],as_of=stamp)['range_starts']),{'3mo','6mo','1yr','3yr'})

    def test_summary_year_and_current_restrict_dates_latest_is_recent(self):
        points=[point(0,250),point(370,200),point(390,180)]
        view=performance_view(points,as_of=BASE+timedelta(days=400))
        self.assertEqual(view['summaries'],dict(current=1,latest=2,year=1,lifetime=0))
        self.assertEqual(view['ages_days']['2'],10)

    def test_source_day_unknown_kept_in_lifetime_without_inventing_clock_window(self):
        points=[point(0,150),point(1,250,absolute=False)]
        before=copy.deepcopy(points)
        view=performance_view(points,as_of=BASE+timedelta(days=2))
        self.assertEqual(view['unknown_timezones'],1)
        self.assertEqual(view['summaries'],dict(current=0,latest=1,year=0,lifetime=1))
        self.assertEqual(view['rolling'][0]['index'],0)
        self.assertNotIn('1',view['ages_days'])
        self.assertEqual(points,before)

    def test_heap_matches_independent_direct_window_max_at_all_change_times(self):
        points=[point(i*7,(i*17)%210) for i in range(40)]
        now=BASE+timedelta(days=350)
        view=performance_view(points,as_of=now)
        times=sorted({datetime.fromisoformat(p['start_time'])+timedelta(days=d)
                      for p in points for d in (0,42)})
        for t in times:
            eligible=[i for i,p in enumerate(points) if t-timedelta(days=42)<datetime.fromisoformat(p['start_time'])<=t]
            oracle=min(eligible,key=lambda i:(-points[i]['average_watts'],points[i]['date_key'],points[i]['activity_id']),default=None)
            steps=[s for s in view['rolling'] if datetime.fromisoformat(s['at'])<=t]
            self.assertEqual(steps[-1]['index'] if steps else None,oracle)

    def test_empty_history_and_naive_clock_are_safe(self):
        view=performance_view([],as_of=BASE)
        self.assertEqual(view['rolling'],[])
        self.assertTrue(all(v is None for v in view['summaries'].values()))
        with self.assertRaises(ValueError): performance_view([],as_of=BASE.replace(tzinfo=None))
