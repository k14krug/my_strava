"""Synthetic calendar/evidence/goal acceptance, with explicit expected values."""
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlencode

from fit_fixture import make_fit
from rideworks import store as store_module
from rideworks.dashboard import dashboard, goal_progress, mileage
from rideworks.goals import annual_goal, browser_zone, set_annual_goal, target_miles
from rideworks.history import presentation
from rideworks.performance import rebuild_performance
from rideworks.settings import Settings
from rideworks.store import Store
from rideworks.strava_api import apply_observations, normalize
from rideworks.web import Application


def activity(identity, stamp, metres, kind='Virtual Ride', origin='file'):
    dt = datetime.fromisoformat(stamp) if stamp else None
    return dict(activity_id=identity, start_time=stamp, activity_type=kind,
                absolute_time=bool(dt and dt.tzinfo), date_key=stamp,
                distance=metres, distance_source={'context':'Strava API summary' if origin=='api' else 'FIT session'})


class CalendarTests(TestCase):
    def test_cycling_distance_provenance_zero_and_missing_evidence(self):
        rows=[activity('1','2026-02-01T12:00:00+00:00',1609.344),
              activity('2','2026-02-02T12:00:00+00:00',3218.688,'Ride','api'),
              activity('3','2026-02-02T12:00:00+00:00',0,'Biking','api'),
              activity('4','2026-02-02T12:00:00+00:00',999,'Run'),
              activity('5','2026-02-02T12:00:00',None),activity('6',None,999)]
        result=mileage(rows,'America/Los_Angeles',as_of=datetime(2026,2,2,20,tzinfo=timezone.utc))
        ytd=result['ytd'];self.assertEqual(ytd['miles'],3)
        self.assertEqual((ytd['file_count'],ytd['api_count'],ytd['contributing_activities']),(1,2,3))
        self.assertEqual((ytd['file_miles'],ytd['api_miles']),(1,2))
        self.assertEqual((ytd['distance_unavailable'],ytd['date_unavailable_excluded']),(1,1))
        self.assertEqual(result['diagnostics']['excluded_noncycling'],1)
        self.assertEqual(result['diagnostics']['timezone_unknown'],1)

    def test_browser_local_year_edge_and_unknown_source_date(self):
        rows=[activity('1','2026-01-01T00:30:00+00:00',1609.344),
              activity('2','2026-01-01T01:00:00',1609.344)]
        now=datetime(2026,1,1,12,tzinfo=timezone.utc)
        la=mileage(rows,'America/Los_Angeles',as_of=now)
        tokyo=mileage(rows,'Asia/Tokyo',as_of=now)
        self.assertEqual(la['ytd']['miles'],1);self.assertEqual(tokyo['ytd']['miles'],2)
        self.assertEqual(la['diagnostics']['timezone_unknown'],1)
        self.assertEqual(rows[0]['start_time'],'2026-01-01T00:30:00+00:00')

    def test_seven_day_and_previous_boundaries_include_today_and_leap_day(self):
        rows=[activity(str(i),stamp,1609.344) for i,stamp in enumerate([
            '2024-02-17T00:00:00+00:00','2024-02-23T23:59:59+00:00',
            '2024-02-24T00:00:00+00:00','2024-02-29T12:00:00+00:00',
            '2024-03-01T12:00:00+00:00','2024-03-01T23:00:00+00:00'])]
        result=mileage(rows,'UTC',as_of=datetime(2024,3,1,18,tzinfo=timezone.utc))
        self.assertEqual(result['last7']['miles'],3);self.assertEqual(result['prior7']['miles'],2)
        self.assertEqual(result['last7']['start'],'2024-02-24')
        self.assertEqual(result['prior7']['end_exclusive'],'2024-02-24')
        self.assertEqual(result['diagnostics']['future_excluded'],1)
        self.assertEqual(len(result['weeks']),12)
        self.assertEqual(result['weeks'][-1]['start'],'2024-02-26')
        self.assertEqual(result['weeks'][-1]['miles'],2)

    def test_dst_uses_calendar_days_and_empty_or_unavailable_distance(self):
        rows=[activity('1','2026-03-08T08:00:00+00:00',1609.344),
              activity('2','2026-03-02T08:00:00+00:00',1609.344)]
        result=mileage(rows,'America/Los_Angeles',as_of=datetime(2026,3,9,6,tzinfo=timezone.utc))
        self.assertEqual(result['today'],'2026-03-08');self.assertEqual(result['last7']['miles'],2)
        self.assertEqual(mileage([],'UTC',as_of=datetime(2026,3,9,tzinfo=timezone.utc))['last7']['miles'],0)
        missing=mileage([activity('1','2026-03-09T00:00:00+00:00',None)],'UTC',as_of=datetime(2026,3,9,tzinfo=timezone.utc))
        self.assertIsNone(missing['last7']['miles'])

    def test_goal_leap_year_pace_percent_remaining_and_over_target(self):
        result=goal_progress(2024,'2024-02-29',80,'366')
        self.assertEqual((result['calendar_days_elapsed'],result['calendar_days_in_year']),(60,366))
        self.assertEqual(result['target_to_date'],60);self.assertEqual(result['pace_difference'],20)
        self.assertAlmostEqual(result['percent'],100*80/366);self.assertEqual(result['remaining_miles'],286)
        over=goal_progress(2026,'2026-12-31',400,'365')
        self.assertEqual(over['remaining_miles'],0);self.assertGreater(over['percent'],100)
        self.assertIsNone(goal_progress(2026,'2026-01-01',0,None))
        self.assertIsNone(goal_progress(2026,'2026-01-01',None,'365'))

    def test_timezone_validation_and_absolute_as_of_required(self):
        for name in ('','No/Such_Zone','../etc/passwd','a'*129):
            with self.assertRaises(ValueError):browser_zone(name)
        with self.assertRaises(ValueError):mileage([],'UTC',as_of=datetime(2026,1,1))


class DashboardTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'data');self.addCleanup(self.store.close)
        self.settings=Settings(self.store.data_dir,credentials=lambda:None)
        self.app=Application(self.store.data_dir,settings_factory=lambda root:self.settings)

    def post(self,**fields):
        fields={'nonce':self.settings.nonce,'tz':'America/Los_Angeles',**fields}
        return self.settings.post('/settings/annual-goal',urlencode(fields).encode(),'http://127.0.0.1:8765')

    def test_goal_unset_set_update_clear_restart_and_no_default(self):
        year=datetime.now(timezone.utc).astimezone(browser_zone('America/Los_Angeles')).year
        set_annual_goal(self.store,year-1,'80')
        self.assertIsNone(annual_goal(self.store,year))
        html=self.app.get('/?home_tz=America%2FLos_Angeles')[2].decode()
        self.assertIn('Set annual goal',html);self.assertNotIn('2,500',html)
        self.assertEqual(self.post(target_miles='1234.50')[0],303)
        self.assertEqual(annual_goal(self.store,year)['target_miles'],'1234.50')
        with Store(self.store.data_dir) as restarted:self.assertEqual(annual_goal(restarted,year)['target_miles'],'1234.50')
        self.assertEqual(self.post(target_miles='1500')[0],303)
        self.assertEqual(annual_goal(self.store,year)['target_miles'],'1500')
        self.assertEqual(self.post(clear='1')[0],303);self.assertIsNone(annual_goal(self.store,year))
        self.assertEqual(annual_goal(self.store,year-1)['target_miles'],'80')

    def test_failed_goal_write_rolls_back_and_does_not_claim_sync_failure(self):
        self.post(target_miles='123')
        before=[tuple(r) for r in self.store.connection.execute('SELECT * FROM annual_mileage_goals')]
        self.store.connection.executescript("""CREATE TRIGGER synthetic_goal_failure AFTER UPDATE ON annual_mileage_goals
            BEGIN SELECT RAISE(FAIL,'private synthetic database error'); END;""")
        response=self.post(target_miles='456')
        self.assertEqual(response[0],500)
        self.assertIn(b'previous target is retained',response[2])
        self.assertNotIn(b'private synthetic',response[2]);self.assertNotIn(b'Sync',response[2])
        self.assertEqual(before,[tuple(r) for r in self.store.connection.execute('SELECT * FROM annual_mileage_goals')])

    def test_goal_validation_does_not_change_saved_target(self):
        self.post(target_miles='123')
        for value in ('','0','-1','NaN','inf','1e3','100000.01','9'*33,' 123','1,234','123 '):
            with self.subTest(value=value):self.assertEqual(self.post(target_miles=value)[0],400)
        rows=self.store.connection.execute('SELECT target_miles FROM annual_mileage_goals').fetchall()
        self.assertEqual([r[0] for r in rows],['123'])
        self.assertEqual(target_miles('100000'),Decimal('100000'))

    def test_goal_nonce_origin_duplicate_fields_and_get_method(self):
        original=self.settings.nonce
        body=urlencode(dict(nonce=original,tz='UTC',target_miles='100')).encode()
        self.assertEqual(self.settings.post('/settings/annual-goal',body,'https://evil.invalid')[0],403)
        self.assertEqual(self.settings.post('/settings/annual-goal',body,'http://127.0.0.1:8765')[0],303)
        self.assertEqual(self.settings.post('/settings/annual-goal',body,'http://127.0.0.1:8765')[0],403)
        bad=urlencode(dict(nonce=self.settings.nonce,tz='UTC',target_miles='100')).encode()+b'&target_miles=200'
        self.assertEqual(self.settings.post('/settings/annual-goal',bad,'http://127.0.0.1:8765')[0],403)
        self.assertEqual(self.post(tz='unknown',target_miles='100')[0],400)
        self.assertEqual(self.app.get('/settings/annual-goal')[0],404)
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM annual_mileage_goals').fetchone()[0],1)

    def test_goal_uses_browser_current_year_near_utc_boundary(self):
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None):return datetime(2026,1,1,0,30,tzinfo=timezone.utc)
        with patch('rideworks.settings.datetime',Clock):
            self.post(target_miles='100')
            self.post(tz='Asia/Tokyo',target_miles='200')
            html=self.app.get('/settings?tz=America%2FLos_Angeles')[2].decode()
        self.assertIn('goal · 2025',html)
        self.assertEqual(annual_goal(self.store,2025)['target_miles'],'100')
        self.assertEqual(annual_goal(self.store,2026)['target_miles'],'200')

    def test_home_browser_route_and_old_filter_redirect_preserve_query(self):
        self.assertIn('<h1>Home</h1>',self.app.get('/')[2].decode())
        self.assertIn('browser timezone',self.app.get('/?home_tz=bad')[2].decode())
        html=self.app.get('/?home_tz=UTC')[2].decode()
        for heading in ('YTD mileage goal','Last 7 Days','Current 42-day best','Latest eligible 20-minute ride','Mileage Progress','20-minute Performance'):
            self.assertIn(heading,html)
        self.assertIn('href="/activities"',html);self.assertIn('href="/" class="active"',html)
        self.assertIn('No cycling Activities yet.',html);self.assertIn('Unavailable',html)
        browser=self.app.get('/activities')[2].decode();self.assertIn('action="/activities"',browser)
        for query in ('q=foo','type=all&sort=oldest&page=2&tz=Asia%2FTokyo','tz=UTC','from=2026-01-01'):
            self.assertEqual(self.app.get('/?'+query)[0],303)
            self.assertEqual(self.app.legacy_browser_target('/?'+query),'/activities?'+query)

    def test_actual_file_distance_precedence_api_fallback_and_metadata_only(self):
        raw=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())-631065600
        path=self.root/'synthetic.fit';path.write_bytes(make_fit(distance=1609.344,session_start_time=raw,
            session_timestamp=raw+2,timestamps=(raw,raw+1,raw+2),lap_start_time=raw,lap_timestamp=raw+2,
            event_timestamps=(raw,raw+2)))
        native=self.store.import_fit(path)
        native_start=self.store.get_source(native['source_id'])['summary']['start_time']
        export=self.root/'export';export.mkdir()
        import csv
        with (export/'activities.csv').open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['Activity ID','Activity Name','Activity Type','Activity Date','Filename'])
            writer.writerow(['1','Synthetic overlap','Virtual Ride',native_start,'synthetic.fit'])
        (export/'synthetic.fit').write_bytes(path.read_bytes())
        self.store.import_strava_export(export)
        # Explicit established API identity for a controlled overlap, not a matching heuristic.
        for identity,stamp,metres in ((1,native_start,99999),(2,'2026-01-01T00:00:00Z',3218.688)):
            item=normalize(dict(id=identity,name='Synthetic ride',type='Ride',sport_type='VirtualRide',start_date=stamp,distance=metres,elapsed_time=2))
            apply_observations(self.store,[item],42,1790000000)
        overlap=self.store.connection.execute("SELECT activity_id FROM strava_api_activities WHERE external_id='1'").fetchone()[0]
        self.assertEqual(overlap,native['activity_id'])
        rows=[presentation(s) for s in self.store.activity_history()]
        self.assertEqual(next(r for r in rows if r['activity_id']==overlap)['distance'],1609.34)
        result=mileage(rows,'UTC',as_of=datetime(2026,10,6,tzinfo=timezone.utc))
        self.assertAlmostEqual(result['ytd']['miles'],2+1609.34/1609.344)
        self.assertEqual((result['ytd']['file_count'],result['ytd']['api_count']),(1,1))
        rebuild_performance(self.store)
        statements=[];self.store.connection.set_trace_callback(statements.append)
        with patch.object(Store,'get_source',side_effect=AssertionError('Raw file read')):
            value=dashboard(self.store,'UTC',as_of=datetime(2026,10,6,tzinfo=timezone.utc))
        self.assertFalse(any('FROM records' in s or 'evidence_json' in s for s in statements))
        self.assertEqual(value['performance']['pending'],0)

    def test_schema6_atomic_migration_preserves_all_existing_tables(self):
        old=self.root/'schema6'
        with Store(old) as store:
            store.connection.execute('DROP TABLE annual_mileage_goals');store.connection.execute('PRAGMA user_version=6')
        broken=store_module.MIGRATION_7.replace('PRAGMA user_version = 7;','INSERT INTO nonexistent VALUES(1);')
        with patch.object(store_module,'MIGRATION_7',broken),self.assertRaises(sqlite3.Error):Store(old)
        with sqlite3.connect(old/'rideworks.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],6)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='annual_mileage_goals'").fetchone())
        with Store(old) as migrated:
            self.assertEqual(migrated.connection.execute('PRAGMA user_version').fetchone()[0],7)
            self.assertEqual(migrated.connection.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_annual_goal_migration_waits_for_completed_stream_migration(self):
        old=self.root/'schema5'
        with patch.object(store_module,'MIGRATION_6',''):
            with Store(old) as stopped:
                self.assertEqual(stopped.connection.execute('PRAGMA user_version').fetchone()[0],5)
                self.assertIsNone(stopped.connection.execute("SELECT name FROM sqlite_master WHERE name='annual_mileage_goals'").fetchone())
        with Store(old) as migrated:
            self.assertEqual(migrated.connection.execute('PRAGMA user_version').fetchone()[0],7)

    def test_no_deferred_metrics_and_pending_banner_on_home(self):
        path=self.root/'synthetic.fit';path.write_bytes(make_fit());self.store.import_fit(path)
        html=self.app.get('/?home_tz=UTC')[2].decode()
        self.assertIn('Performance update incomplete',html)
        self.assertIn('Retry Performance update',html)
        for text in ('Fitness Score','Training Load','Next Workout','Power Curve','AI Insights','Current FTP'):
            self.assertNotIn(text,html)
        rebuild_performance(self.store)
        self.assertNotIn('class="performance-update"',self.app.get('/?home_tz=UTC')[2].decode())
