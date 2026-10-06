"""Owner-approved v2 eligibility and shared sync convergence; synthetic inputs only."""
import json
from unittest import TestCase
from unittest.mock import patch

import test_rideworks_strava as fixture
from test_rideworks_strava_streams import comparison, stream
from rideworks.errors import RideWorksError
from rideworks.performance import POLICY, performance_history, rebuild_performance
from rideworks.recent_context import recent_context
from rideworks.strava import ApiClient, sync
from rideworks.strava_api import apply_observations, normalize
from rideworks.strava_streams import persist
from rideworks.web import Application


class ApiPerformanceTests(TestCase):
    observation=fixture.StravaTests.observation
    def setUp(self):
        fixture.StravaTests.setUp(self)
        self.item=self.observation(identity=2,seconds=3600)
        apply_observations(self.store,[normalize(self.item)],321,self.now-1)
        self.only=self.store.connection.execute("SELECT activity_id FROM strava_api_activities WHERE external_id='2'").fetchone()[0]
        self.payload=dict(time=stream(list(range(1201))),watts=stream([120]*1200+[121]),heartrate=stream([100]*1201))

    def result(self):return next(r for r in performance_history(self.store)['results'] if r['activity_id']==self.only)
    def saved(self):return [tuple(r) for r in self.store.connection.execute('SELECT * FROM performance_history ORDER BY activity_id,policy')]
    def api(self,payload=None):persist(self.store,2,payload if payload is not None else self.payload)
    def summary(self,**changes):
        self.item.update(changes);apply_observations(self.store,[normalize(self.item)],321,self.now)

    def test_strict_api_result_provenance_exact_calculation_and_six_week_context(self):
        self.api();native=self.store.get_source(self.native['source_id']);rebuild_performance(self.store)
        r=self.result();expected=comparison.independent_best(self.payload['time']['data'],self.payload['watts']['data'])
        self.assertTrue(r['eligible']);self.assertEqual(r['policy'],POLICY)
        self.assertEqual((r['average_watts'],r['rounded_watts'],r['start_offset']),
                         (expected['average_watts'],expected['rounded_watts'],expected['start_elapsed']))
        self.assertIsNone(r['source_id']);self.assertIsNone(r['extraction_id']);self.assertNotIn('start_record_index',r)
        e=r['api_evidence'];self.assertEqual(e['evidence_kind'],'Strava API stream');self.assertTrue(e['device_watts'])
        self.assertEqual(e['summary_source_id'],e['related_summary_source_id']);self.assertTrue(e['observation_sha256'])
        self.assertEqual(self.store.get_source(self.native['source_id']),native)
        self.assertEqual(recent_context(self.store,self.only)['prior']['activity_id'],self.native['activity_id'])
        before=self.saved();html=Application(self.store.data_dir).get('/activities/'+self.only)[2].decode()
        self.assertIn('Compared with previous 6 weeks',html);self.assertIn('Current API stream Source ID',html)
        self.assertNotIn('Trusted Performance',html);self.assertEqual(self.saved(),before)

    def test_device_confirmation_resolution_full_length_and_pairing_reasons(self):
        for value in (False,None):
            self.summary(device_watts=value);self.api();rebuild_performance(self.store)
            self.assertEqual(self.result()['reason'],'api_device_watts_not_confirmed')
        self.summary(device_watts=True)
        cases=[(self.payload|dict(watts=stream([120]*1201,resolution='medium')),'api_stream_not_high_resolution'),
               (self.payload|dict(time=stream(list(range(1201)),original_size=1300)),'api_stream_not_full_length'),
               (self.payload|dict(watts=stream([120]*1200)),'api_stream_length_mismatch'),
               (dict(time=stream(list(range(1201))),heartrate=stream([100]*1201)),'api_power_stream_unavailable')]
        for payload,reason in cases:
            self.api(payload);rebuild_performance(self.store);self.assertEqual(self.result()['reason'],reason)
            self.assertEqual(performance_history(self.store)['pending'],0)

    def test_timing_and_incomplete_windows_are_ineligible_without_repairs(self):
        for offsets,powers,reason in [([0]*1200,[120]*1200,'api_stream_invalid_timing'),
            (list(range(1199))+[1197],[120]*1200,'api_stream_invalid_timing'),
            (list(range(0,2400,2)),[120]*1200,'no_complete_timestamp_contiguous_window'),
            (list(range(1200)),[120]*1199+[None],'no_complete_power_window'),
            (list(range(1199)),[120]*1199,'activity_shorter_than_required')]:
            self.api(dict(time=stream(offsets),watts=stream(powers)));rebuild_performance(self.store)
            self.assertEqual(self.result()['reason'],reason)
        self.api(dict(time=stream(list(range(1200))),watts=stream([0]*1200)));rebuild_performance(self.store)
        self.assertEqual(self.result()['rounded_watts'],0)

    def test_current_summary_and_stream_changes_stale_results_and_require_new_pair(self):
        self.api();rebuild_performance(self.store)
        old=self.result()['api_evidence']['stream_source_id']
        changed=json.loads(json.dumps(self.payload));changed['watts']['data'][0]=500
        self.api(changed);self.assertEqual(performance_history(self.store)['stale'],1)
        rebuild_performance(self.store);self.assertNotEqual(self.result()['api_evidence']['stream_source_id'],old)
        self.summary(name='Changed synthetic summary');self.assertEqual(performance_history(self.store)['pending'],1)
        rebuild_performance(self.store);self.assertEqual(self.result()['reason'],'api_stream_summary_not_current')
        self.api(changed);rebuild_performance(self.store);self.assertTrue(self.result()['eligible'])
        self.summary(sport_type='Ride');self.api();rebuild_performance(self.store)
        self.assertEqual(self.result()['reason'],'outdoor_ride_excluded')

    def test_file_power_precedence_ineligible_file_not_rescued_and_no_overlap_duplicate(self):
        apply_observations(self.store,[normalize(self.observation())],321,self.now)
        persist(self.store,1,dict(time=stream(list(range(1200))),watts=stream([500]*1200)))
        self.api();rebuild_performance(self.store)
        overlap=next(r for r in performance_history(self.store)['results'] if r['activity_id']==self.native['activity_id'])
        self.assertEqual(overlap['rounded_watts'],120);self.assertNotIn('api_evidence',overlap)
        self.assertEqual(sum(p['activity_id']==self.native['activity_id'] for p in performance_history(self.store)['points']),1)
        persist(self.store,1,dict(time=stream(list(range(1200))),watts=stream([501]*1200)))
        self.assertEqual(performance_history(self.store)['pending'],0)  # Corroborating API changes do not stale file power.
        self.store.connection.execute('DELETE FROM records WHERE extraction_id=? AND record_index=1199',(self.native['extraction_id'],))
        self.store.connection.execute('UPDATE extractions SET record_count=1199,power_present=1199,heart_rate_present=1199 WHERE extraction_id=?',(self.native['extraction_id'],))
        rebuild_performance(self.store)
        overlap=next(r for r in performance_history(self.store)['results'] if r['activity_id']==self.native['activity_id'])
        self.assertEqual(overlap['reason'],'activity_shorter_than_required');self.assertNotIn('api_evidence',overlap)

    def test_file_without_any_retained_power_can_use_api_fallback(self):
        apply_observations(self.store,[normalize(self.observation())],321,self.now)
        self.store.connection.execute('UPDATE records SET power=NULL WHERE extraction_id=?',(self.native['extraction_id'],))
        self.store.connection.execute('UPDATE extractions SET power_present=0 WHERE extraction_id=?',(self.native['extraction_id'],))
        self.store.connection.execute('UPDATE sessions SET avg_power=NULL,max_power=NULL WHERE extraction_id=?',(self.native['extraction_id'],))
        persist(self.store,1,self.payload);rebuild_performance(self.store)
        overlap=next(r for r in performance_history(self.store)['results'] if r['activity_id']==self.native['activity_id'])
        self.assertTrue(overlap['eligible']);self.assertIn('api_evidence',overlap);self.assertIsNone(overlap['extraction_id'])

    def test_multiple_current_api_identities_are_explicitly_ineligible(self):
        self.api();apply_observations(self.store,[normalize(self.observation(identity=3,seconds=3601))],321,self.now)
        other=self.store.connection.execute("SELECT activity_id FROM strava_api_activities WHERE external_id='3'").fetchone()[0]
        self.store.connection.execute("UPDATE strava_api_activities SET activity_id=? WHERE external_id='3'",(self.only,))
        self.store.connection.execute("UPDATE strava_api_sources SET activity_id=? WHERE external_id='3'",(self.only,))
        self.store.connection.execute('DELETE FROM activities WHERE activity_id=?',(other,))
        persist(self.store,3,self.payload);rebuild_performance(self.store)
        self.assertEqual(self.result()['reason'],'api_current_source_ambiguous')
        self.assertEqual(performance_history(self.store)['pending'],0)

    def test_policy_migration_with_no_new_data_then_unchanged_sync_skips_rebuild(self):
        # A v1 file-only baseline; no API streams were eligible under the old policy.
        self.store.connection.execute('DELETE FROM performance_history')
        self.store.connection.execute("DELETE FROM strava_api_activities WHERE external_id='2'")
        self.store.connection.execute('DELETE FROM strava_api_sources WHERE activity_id=?',(self.only,))
        self.store.connection.execute('DELETE FROM activities WHERE activity_id=?',(self.only,))
        with patch('rideworks.performance.POLICY','virtual-native-power-v1'):rebuild_performance(self.store)
        v1=[tuple(r) for r in self.store.connection.execute("SELECT * FROM performance_history WHERE policy='virtual-native-power-v1'")]
        http=fixture.FakeHTTP(fixture.Response([]));client=ApiClient(fixture.CREDS,opener=http)
        with patch('rideworks.performance.rebuild_performance',wraps=rebuild_performance) as rebuilt:
            r=sync(self.store,client,now=self.now);self.assertEqual(rebuilt.call_count,1)
        self.assertEqual(r['performance_update'],'updated');self.assertEqual(performance_history(self.store)['pending'],0)
        self.assertEqual([tuple(r) for r in self.store.connection.execute("SELECT * FROM performance_history WHERE policy='virtual-native-power-v1'")],v1)
        http.responses.append(fixture.Response([]))
        with patch('rideworks.performance.rebuild_performance',side_effect=AssertionError('Unnecessary rebuild')):
            self.assertEqual(sync(self.store,client,now=self.now+1)['performance_update'],'current')
        self.assertEqual(client.stream_requests,0)

    def test_shared_sync_enriches_converges_failure_preserves_checkpoint_and_later_sync_retries(self):
        http=fixture.FakeHTTP(fixture.Response([self.item]),fixture.Response(self.payload))
        client=ApiClient(fixture.CREDS,opener=http);before=self.saved()
        with patch('rideworks.performance.evaluate',side_effect=RideWorksError('private-synthetic-error')):
            r=sync(self.store,client,now=self.now)
        self.assertEqual(r['performance_update'],'incomplete');self.assertEqual(self.saved(),before)
        self.assertEqual(self.store.connection.execute('SELECT successful_at FROM strava_sync_state').fetchone()[0],self.now)
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM strava_stream_sources').fetchone()[0],1)
        self.assertGreater(performance_history(self.store)['pending'],0)
        html=Application(self.store.data_dir).get('/settings')[2].decode()
        self.assertIn('Performance update incomplete',html);self.assertIn('Retry Performance update',html)
        self.assertNotIn('private-synthetic-error',html)
        http.responses.append(fixture.Response([self.item]))
        r=sync(self.store,client,now=self.now+1)
        self.assertEqual(r['performance_update'],'updated');self.assertEqual(r['stream_fetches'],0)
        self.assertEqual(performance_history(self.store)['pending'],0)
        self.assertNotIn('class="performance-update"',Application(self.store.data_dir).get('/settings')[2].decode())

    def test_changed_summary_sync_refetches_streams_before_v2_convergence(self):
        self.api();rebuild_performance(self.store)
        self.item['name']='Later summary'
        http=fixture.FakeHTTP(fixture.Response([self.item]),fixture.Response(self.payload))
        r=sync(self.store,ApiClient(fixture.CREDS,opener=http),now=self.now)
        self.assertEqual(r['stream_fetches'],1);self.assertEqual(r['performance_update'],'updated')
        self.assertTrue(self.result()['eligible']);self.assertEqual(self.result()['api_evidence']['summary_source_id'],self.result()['api_evidence']['related_summary_source_id'])
