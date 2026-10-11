#!/usr/bin/env python3
"""Create a source-neutral visual preview, never in an existing real store."""
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store
from rideworks.strava_api import apply_observations,normalize
from rideworks.planning import set_classification


def main():
    p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True)
    p.add_argument('--before-ride',action='store_true')
    a=p.parse_args()
    if (a.data_dir/'rideworks.sqlite3').exists():p.error('Preview requires a new empty directory.')
    today=datetime.now(timezone.utc).astimezone(ZoneInfo('America/Los_Angeles')).date()
    entries=[(-6,'Synthetic race candidate',3600,155,None),(-3,'Synthetic VO2 session',2700,130,'VO2'),
             (0,'Synthetic recovery ride',2400,94,'Recovery')]
    if a.before_ride:entries=entries[:-1]
    with Store(a.data_dir) as s:
        for i,(offset,title,seconds,watts,category) in enumerate(entries,9000):
            stamp=datetime.combine(today+timedelta(days=offset),datetime.min.time(),tzinfo=timezone.utc)+timedelta(hours=16)
            source=normalize(dict(id=i,name=title,type='Ride',sport_type='VirtualRide',start_date=stamp.isoformat(),
                                  moving_time=seconds,elapsed_time=seconds,average_watts=watts,workout_type=None))
            apply_observations(s,[source],999,int(datetime.now(timezone.utc).timestamp()))
            identity=s.connection.execute('SELECT activity_id FROM strava_api_activities WHERE external_id=?',(str(i),)).fetchone()[0]
            if category:set_classification(s,identity,category)
        s.connection.execute('INSERT OR REPLACE INTO strava_sync_state VALUES(1,?,?)',('999',int(datetime.now(timezone.utc).timestamp())))
        from rideworks.performance import rebuild_performance
        rebuild_performance(s)
    print('Synthetic preview created; no personal activity data was used.')


if __name__=='__main__':main()
