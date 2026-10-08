"""Synthetic bounded historical repair and normal GPX-sync regression."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import zipfile

from test_rideworks_export import GPX, csv_bytes, row
from test_rideworks_strava import CREDS, FakeHTTP, Response
from rideworks.dashboard import mileage
from rideworks.history import presentation
from rideworks.performance import performance_history, rebuild_performance
from rideworks.store import Store
from rideworks.strava import ApiClient, TokenFile, sync
from rideworks.strava_api import SyncError, apply_observations, normalize
from rideworks.strava_summary_repair import enrich_summaries


class SummaryRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'data');self.addCleanup(self.store.close)
        self.now=int(datetime(2026,10,8,15,tzinfo=timezone.utc).timestamp())
        self.tokens=TokenFile(self.store.data_dir)
        self.tokens.save(dict(access_token='fake-access',refresh_token='fake-refresh',
                              expires_at=self.now+7200,athlete_id=321,scope='activity:read_all'))

    def fixture(self,count=1,date='2026-02-01T12:00:00'):
        archive=self.root/'export.zip'
        with zipfile.ZipFile(archive,'w') as z:
            rows=[]
            for i in range(count):
                filename=f'activities/ride-{i}.gpx'
                item=row(str(i+1),filename=filename,date=date);item[2]='Ride';rows.append(item)
                z.writestr(filename,GPX.replace(b'<type>cycling</type>',f'<type>cycling</type><name>Synthetic {i}</name>'.encode()))
            z.writestr('activities.csv',csv_bytes(rows))
        self.assertFalse(self.store.import_strava_export(archive)['failures'])
        rebuild_performance(self.store)
        return {r['external_id']:r['activity_id'] for r in self.store.connection.execute('SELECT * FROM strava_export_sources')}

    def observation(self,identity=1,**changes):
        return dict(id=identity,athlete={'id':321},name='Synthetic API Ride',type='Ride',sport_type='Ride',
                    start_date='2026-02-01T20:00:00Z',distance=1609.344,elapsed_time=1800,moving_time=1700,
                    map={'polyline':'private'},description='private',start_latlng=[1,2],photos={'count':5},
                    segment_efforts=[{'private':True}],laps=[{'distance':99}],kudos_count=3)|changes

    def client(self,*responses):
        http=FakeHTTP(*responses);return ApiClient(CREDS,opener=http),http

    def test_eight_sequential_allowlisted_observations_idempotence_and_checkpoint_preserved(self):
        targets=self.fixture(8)
        self.store.connection.execute('INSERT INTO strava_sync_state VALUES(1,?,?)',('321',self.now-86400))
        native=self.store.activity_history();before=list(self.store.connection.execute('SELECT * FROM strava_sync_state'))
        payloads=[self.observation(i) for i in range(1,9)]
        client,http=self.client(*(Response(p) for p in payloads))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((report['status'],report['activity_requests'],report['usable_distances']),('completed',8,8))
        self.assertEqual([r.full_url for r in http.requests],[f'https://www.strava.com/api/v3/activities/{i}' for i in range(1,9)])
        self.assertTrue(all(r.method=='GET' and r.get_header('Authorization')=='Bearer fake-access' for r in http.requests))
        self.assertEqual(client.stream_requests,0)
        self.assertEqual(list(self.store.connection.execute('SELECT * FROM strava_sync_state')),before)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM activities').fetchone()[0],8)
        for old in native:
            new=self.store.activity_history(old['activity']['activity_id'])[0]
            self.assertEqual([s for s in new['sources'] if s['source']['kind']!='strava_api'],old['sources'])
            p=presentation(new);self.assertEqual((p['distance'],p['duration']),(1609.344,1800))
            self.assertEqual(p['distance_source']['context'],'Strava API summary')
            self.assertEqual(p['duration_source']['context'],'Strava API summary')
        persisted=[json.loads(r[0]) for r in self.store.connection.execute('SELECT evidence_json FROM strava_api_sources')]
        for p in persisted:
            self.assertEqual(p,normalize(self.observation(p['id'])))
        self.assertEqual(performance_history(self.store)['pending'],0)
        self.assertFalse(performance_history(self.store)['points'])  # Outdoor policy unchanged.
        client,_=self.client(*(Response(p) for p in payloads))
        repeated=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((repeated['new_observations'],repeated['unchanged_observations']),(0,8))
        self.assertEqual(repeated['performance_update'],'current')

    def test_manifest_bound_identity_and_source_checks_before_requests(self):
        targets=self.fixture();identity=next(iter(targets.values()))
        for invalid in ({},[],{str(i):identity for i in range(1,10)},{'1':identity,'2':identity},
                        {'2':identity},{'1':'not-established'},{'../1':identity}):
            client,http=self.client()
            with self.subTest(invalid=invalid),self.assertRaises(SyncError):enrich_summaries(self.store,client,invalid,now=self.now)
            self.assertFalse(http.requests)
        client,http=self.client()
        with self.assertRaises(SyncError):client.activity_summary('fake','1/streams')
        self.assertFalse(http.requests)

    def test_wrong_response_account_identity_type_and_shape_do_not_persist(self):
        targets=self.fixture()
        for change in ({'athlete':{'id':999}},{'id':2},{'sport_type':'VirtualRide'},
                       {'distance':-1},{'distance':float('inf')},{'start_date':'unknown'}):
            client,http=self.client(Response(self.observation(**change)))
            result=enrich_summaries(self.store,client,targets,now=self.now)
            self.assertEqual((result['status'],result['summaries_retained']),('stopped',0))
            self.assertEqual(len(http.requests),1)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM strava_api_sources').fetchone()[0],0)

    def test_failure_retains_earlier_success_and_converges_without_retry(self):
        targets=self.fixture(3)
        client,http=self.client(Response(self.observation()),HTTPError('https://www.strava.com/',503,'private',{},None))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((report['status'],report['activity_requests'],report['summaries_retained']),('stopped',2,1))
        self.assertEqual(len(http.requests),2)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM strava_api_sources').fetchone()[0],1)
        self.assertEqual(performance_history(self.store)['pending'],0)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM strava_sync_state').fetchone()[0],0)

    def test_missing_distance_is_retained_and_stops_zero_is_usable(self):
        targets=self.fixture(2)
        client,http=self.client(Response(self.observation(distance=None)))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((report['status'],report['summaries_retained'],report['usable_distances']),('stopped',1,0))
        self.assertEqual(len(http.requests),1)
        client,_=self.client(Response(self.observation(distance=0)),Response(self.observation(2)))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((report['status'],report['usable_distances']),('completed',2))

    def test_rotation_and_rate_stop_preserve_success_and_401_clears_tokens(self):
        targets=self.fixture(2);state=self.tokens.read();state['expires_at']=self.now;self.tokens.save(state)
        client,http=self.client(Response(dict(access_token='rotated',refresh_token='newest',expires_at=self.now+7200)),
            Response(self.observation(),{'X-ReadRateLimit-Limit':'100,1000','X-ReadRateLimit-Usage':'100,100'}))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual((report['status'],report['summaries_retained']),('stopped',1))
        self.assertEqual(len(http.requests),2)  # Refresh + first GET; exhausted second GET never sent.
        self.assertEqual(self.tokens.read()['refresh_token'],'newest')
        self.assertEqual(http.requests[-1].get_header('Authorization'),'Bearer rotated')
        client,http=self.client(HTTPError('https://www.strava.com/',401,'private',{},None))
        report=enrich_summaries(self.store,client,targets,now=self.now)
        self.assertEqual(report['status'],'stopped');self.assertFalse(self.tokens.path.exists())

    def test_normal_future_sync_supplies_gpx_distance_duration_without_historical_requests(self):
        targets=self.fixture(date='2026-10-07T12:00:00')
        before=self.store.activity_history()[0];self.assertIsNone(presentation(before)['distance'])
        self.store.connection.execute('INSERT INTO strava_sync_state VALUES(1,?,?)',('321',self.now-86400))
        client,http=self.client(Response([self.observation(start_date='2026-10-07T19:00:00Z')]))
        with patch.object(client,'activity_summary',side_effect=AssertionError('historical detail')):
            report=sync(self.store,client,now=self.now)
        self.assertEqual((report['new_activities'],report['existing_activities_enriched']),(0,1))
        self.assertEqual(len(http.requests),1);self.assertIn('/athlete/activities?',http.requests[0].full_url)
        self.assertEqual((report['stream_fetches'],client.stream_requests),(0,0))
        after=self.store.activity_history()[0];p=presentation(after)
        self.assertEqual((p['distance'],p['duration']),(1609.344,1800))
        self.assertEqual(p['activity_id'],next(iter(targets.values())))
        self.assertEqual([s for s in after['sources'] if s['source']['kind']!='strava_api'],before['sources'])
        aggregate=mileage([p],'America/Los_Angeles',as_of=datetime.fromtimestamp(self.now,timezone.utc))
        self.assertEqual((aggregate['ytd']['miles'],aggregate['ytd']['api_count'],aggregate['ytd']['distance_unavailable']),(1,1,0))
        self.assertEqual(performance_history(self.store)['pending'],0)

    def test_targeted_persistence_rechecks_identity_atomically_and_cannot_advance_checkpoint(self):
        targets=self.fixture();value=normalize(self.observation())
        for mapping,when in ({'1':'wrong'},None),(targets,self.now):
            with self.assertRaises(SyncError):apply_observations(self.store,[value],321,when,established_targets=mapping)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM strava_api_sources').fetchone()[0],0)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM activities').fetchone()[0],1)


if __name__=='__main__':unittest.main()
