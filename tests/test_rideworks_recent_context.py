"""Synthetic exact-interval, trust, rendering and read-only comparison tests."""
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fit_fixture import make_fit
from rideworks.performance import POLICY, performance_history, rebuild_performance
from rideworks.recent_context import recent_context, select_recent_context
from rideworks.store import Store
from rideworks.web import Application

BASE = datetime(2024, 3, 1, tzinfo=timezone.utc)


def point(identity, seconds, watts, *, absolute=True):
    stamp = BASE + timedelta(seconds=seconds)
    if not absolute:
        stamp = stamp.replace(tzinfo=None)
    return dict(activity_id=identity, start_time=stamp.isoformat(), absolute_time=absolute,
                date_key=stamp.replace(tzinfo=None).isoformat(), date_day=stamp.date().isoformat(),
                title='Synthetic <prior> & ride', average_watts=watts, rounded_watts=int(watts+.5),
                source_id='source-'+identity, extraction_id='extraction-'+identity)


def history(points):
    return dict(points=points, pending=0, results=[dict(p, eligible=True, reason=None,
                policy=POLICY, method='best-average-power-v1', duration_seconds=1200,
                classification={'activity_type':'Virtual Ride'}) for p in points])


class SelectionTests(unittest.TestCase):
    def test_exact_open_interval_excludes_both_boundaries_current_and_future(self):
        points=[point('current',0,999),point('expired',-42*86400,900),point('inside',-42*86400+1,100),
                point('same-time',0,1000),point('future',1,1000)]
        result=select_recent_context(history(points),'current')
        self.assertEqual(result['prior']['activity_id'],'inside')
        self.assertEqual(result['window_start'],(BASE-timedelta(days=42)).isoformat())
        self.assertEqual(result['window_end'],BASE.isoformat())

    def test_raw_winner_is_not_replaced_by_display_tie(self):
        result=select_recent_context(history([point('a',-200,200.1),point('b',-100,200.2),point('current',0,120)]),'current')
        self.assertEqual(result['prior']['activity_id'],'b')
        self.assertEqual(result['prior']['rounded_watts'],200)

    def test_exact_tie_uses_earliest_time_then_activity_identity(self):
        points=[point('z',-200,200),point('a',-200,200),point('later',-100,200),point('current',0,120)]
        self.assertEqual(select_recent_context(history(points),'current')['prior']['activity_id'],'a')

    def test_zero_prior_is_valid_and_no_baseline_never_uses_old_or_future_result(self):
        current=point('current',0,120)
        self.assertEqual(select_recent_context(history([point('zero',-1,0),current]),'current')['prior']['rounded_watts'],0)
        result=select_recent_context(history([point('old',-43*86400,999),current,point('future',1,999)]),'current')
        self.assertFalse(result['available']); self.assertIsNone(result['prior'])
        self.assertEqual(result['reason'],'no_qualifying_prior_result')

    def test_unknown_prior_timezone_is_excluded_and_current_timezone_unavailable(self):
        result=select_recent_context(history([point('unknown',-1,999,absolute=False),point('current',0,120)]),'current')
        self.assertIsNone(result['prior'])
        result=select_recent_context(history([point('current',0,120,absolute=False)]),'current')
        self.assertEqual(result['reason'],'activity_timezone_unknown'); self.assertIsNone(result['window_start'])

    def test_missing_current_result_needs_rebuild_and_missing_date_stays_unavailable(self):
        self.assertEqual(select_recent_context(history([]),'missing')['reason'],'performance_rebuild_required')
        data=history([point('current',0,120)]);data['points']=[]
        result=select_recent_context(data,'current')
        self.assertEqual(result['reason'],'activity_date_unavailable');self.assertIsNotNone(result['current'])

    def test_ineligible_outdoor_noncycling_and_wrong_versions_cannot_supply_baseline(self):
        for change in [{'eligible':False,'reason':'outdoor_ride_excluded'},
                       {'classification':{'activity_type':'Ride'}}, {'classification':{'activity_type':'Run'}},
                       {'policy':'other'}, {'method':'other'}, {'duration_seconds':60}]:
            with self.subTest(change=change):
                data=history([point('prior',-1,999),point('current',0,120)]);data['results'][0].update(change)
                self.assertIsNone(select_recent_context(data,'current')['prior'])
                data['results'][1].update(change)
                self.assertFalse(select_recent_context(data,'current')['available'])

    def test_pending_prior_is_excluded_and_inputs_are_not_mutated(self):
        data=history([point('prior',-1,999),point('current',0,120)])
        data['results'].pop(0);data['pending']=1;before=copy.deepcopy(data)
        self.assertIsNone(select_recent_context(data,'current')['prior'])
        self.assertEqual(data,before)


class PersistedContextTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'data');self.addCleanup(self.store.close)
        self.app=Application(self.store.data_dir)
        self.prior=self.native(-86400,180);self.current=self.native(0,120)
        rebuild_performance(self.store)

    def native(self, offset, watts):
        stamp=1100000000+offset;path=self.root/'synthetic.fit'
        path.write_bytes(make_fit(powers=[watts]*1200,heart_rates=[100]*1200,timestamps=range(stamp,stamp+1200),
                                  session_start_time=stamp,session_timestamp=stamp+1200,elapsed=1200,timer=1200))
        return self.store.import_fit(path)

    def test_selector_never_loads_native_records_or_mutates_history(self):
        before=list(self.store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id'))
        with patch.object(self.store,'get_activity',side_effect=AssertionError('native scan')), \
             patch.object(self.store,'get_source',side_effect=AssertionError('native scan')), \
             patch.object(self.store,'import_strava_export',side_effect=AssertionError('archive import')), \
             patch.object(self.store,'reextract',side_effect=AssertionError('reparse')), \
             patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('rebuild')):
            result=recent_context(self.store,self.current['activity_id'])
        self.assertEqual(result['prior']['activity_id'],self.prior['activity_id'])
        self.assertEqual(list(self.store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id')),before)

    def test_rich_review_links_values_provenance_and_only_current_native_scan(self):
        calls=[];original=Store.get_activity
        def watched(store,identity):
            calls.append(identity);return original(store,identity)
        with patch.object(Store,'get_activity',watched),patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('rebuild')):
            status,_,body=self.app.get('/activities/'+self.current['activity_id'])
        html=body.decode();self.assertEqual(status,200);self.assertEqual(calls,[self.current['activity_id']])
        self.assertIn('id="recent-current-watts">120 W',html);self.assertIn('id="recent-prior-watts">180 W',html)
        self.assertIn('Compared with previous 6 weeks',html)
        self.assertIn('id="recent-difference">60 W below',html)
        self.assertIn('>Open prior ride</a>',html)
        self.assertIn('href="/activities/'+self.prior['activity_id']+'"',html)
        self.assertIn('id="recent-performance" href="/performance"',html)
        self.assertIn('The current Activity is excluded',html);self.assertIn('Prior window start (exclusive)',html)
        self.assertIn('virtual-native-power-v1',html);self.assertIn('best-average-power-v1',html)

    def test_earliest_ride_shows_unavailable_without_zero_or_fallback(self):
        html=self.app.get('/activities/'+self.prior['activity_id'])[2].decode()
        self.assertIn('id="recent-prior-watts">Unavailable',html)
        self.assertIn('No qualifying prior result',html)
        self.assertNotIn('id="recent-prior-activity"',html)
        self.assertNotIn('id="recent-difference"',html)

    def test_stale_current_and_prior_are_suppressed_without_automatic_rebuild(self):
        self.store.connection.execute('UPDATE sessions SET avg_power=119 WHERE extraction_id=?',(self.prior['extraction_id'],))
        self.assertIsNone(recent_context(self.store,self.current['activity_id'])['prior'])
        self.store.connection.execute('UPDATE sessions SET avg_power=119 WHERE extraction_id=?',(self.current['extraction_id'],))
        html=self.app.get('/activities/'+self.current['activity_id'])[2].decode()
        self.assertIn('requires a Performance rebuild',html);self.assertIn('Best 20-minute power',html)
        self.assertNotIn('id="recent-current-watts"',html)

    def test_outdoor_rich_review_retains_own_best_but_trusted_context_is_unavailable(self):
        self.store.connection.execute("UPDATE sessions SET sub_sport='generic' WHERE extraction_id=?",(self.current['extraction_id'],))
        rebuild_performance(self.store)
        html=self.app.get('/activities/'+self.current['activity_id'])[2].decode()
        self.assertIn('Outdoor Ride power is excluded',html);self.assertIn('class="best-value">120 W',html)
        self.assertNotIn('id="recent-prior-activity"',html)

    def test_thin_ambiguous_review_has_no_fabricated_recent_context(self):
        path=self.root/'other.fit';path.write_bytes(make_fit())
        self.store.import_file(path,activity_id=self.current['activity_id'])
        html=self.app.get('/activities/'+self.current['activity_id'])[2].decode()
        self.assertIn('Detailed RideWorks review unavailable',html);self.assertNotIn('id="recent-context-title"',html)

    def test_prior_title_is_escaped_and_context_uses_no_evaluative_style(self):
        from rideworks.web import recent_context_panel
        context=select_recent_context(history([point('prior',-1,180),point('current',0,120)]),'current')
        html=recent_context_panel(context)
        self.assertIn('Synthetic &lt;prior&gt; &amp; ride',html)
        for term in ('fitness improved','fitness declined','trend-up','trend-down','var(--green)','%'):
            self.assertNotIn(term,html)

    def test_difference_matches_displayed_watts_with_neutral_above_below_and_equal_labels(self):
        from rideworks.web import recent_context_panel
        for current, prior, label in [(125,120,'5 W above'), (120,215,'95 W below'),
                                      (120,120,'Same displayed watts'),
                                      (120.4,119.6,'Same displayed watts'), (120,120.5,'1 W below'),
                                      (120.51,120.49,'1 W above'), (119.49,119.51,'1 W below'),
                                      (120.11916666666667,194.54333333333332,'75 W below')]:
            with self.subTest(current=current,prior=prior):
                context=select_recent_context(history([point('prior',-1,prior),point('current',0,current)]),'current')
                before=copy.deepcopy(context)
                html=recent_context_panel(context)
                self.assertIn('id="recent-difference">'+label,html)
                self.assertIn(str(current),html);self.assertIn(str(prior),html)
                self.assertEqual(context,before)
