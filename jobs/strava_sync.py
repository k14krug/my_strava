import os
import sys
import time
import requests
import datetime
import argparse
from dotenv import load_dotenv
from flask import Flask
# 🔹 Add project root to Python path (for cron & manual execution)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models import db, Activity, TrainingLoad, FTPHistory

# Load environment variables
load_dotenv()

# Strava API Configuration
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_API_URL = "https://www.strava.com/api/v3/activities"

# Flask App Setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mariadb+mariadbconnector://strava_user:admin14@localhost/strava_app_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def get_new_access_token():
    """Obtain a fresh access token using the refresh token"""
    print("🔄 Requesting new access token...")
    try:
        response = requests.post(STRAVA_AUTH_URL, data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        })
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"❌ Strava Auth Error: {str(e)}")
        return None

def get_access_token():
    """Get a valid access token"""
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")
    if access_token:
        # Test if token is still valid
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            test_response = requests.get(STRAVA_API_URL, headers=headers, params={"per_page": 1})
            if test_response.status_code == 200:
                return access_token
        except requests.exceptions.RequestException:
            pass
    return get_new_access_token()

def check_rate_limits(headers):
    """Check rate limits from response headers"""
    if not headers:
        return True
        
    usage = headers.get("X-RateLimit-Usage", "0,0").split(",")
    if len(usage) != 2:
        return True
        
    try:
        fifteen_min_usage = int(usage[0])
        daily_usage = int(usage[1])
        
        # Basic rate limit checking
        if fifteen_min_usage > 180:  # 90% of 200
            print("⚠️ Approaching 15-minute rate limit")
            time.sleep(60)
        if daily_usage > 1800:  # 90% of 2000
            print("❌ Approaching daily rate limit")
            return False
    except ValueError:
        pass
        
    return True

def fetch_activities():
    """Fetch activities from Strava"""
    access_token = get_access_token()
    if not access_token:
        return []
        
    headers = {"Authorization": f"Bearer {access_token}"}
    last_activity = Activity.query.order_by(Activity.start_date.desc()).first()
    after_timestamp = int(last_activity.start_date.timestamp()) if last_activity else 0
    
    activities = []
    page = 1
    while True:
        try:
            response = requests.get(STRAVA_API_URL, headers=headers, params={
                "per_page": 200,
                "after": after_timestamp,
                "page": page
            })
            
            if not check_rate_limits(response.headers):
                break
                
            response.raise_for_status()
            page_activities = response.json()
            if not page_activities:
                break
                
            activities.extend(page_activities)
            page += 1
            time.sleep(2)  # Basic rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {str(e)}")
            break
            
    return activities

def save_activities():
    """Save activities to database"""
    with app.app_context():
        try:
            # Get existing activity IDs
            existing_ids = {a.strava_id for a in Activity.query.with_entities(Activity.strava_id).all()}
            
            # Fetch new activities with error handling
            try:
                activities = fetch_activities()
                if not activities:
                    print("❌ No new activities found")
                    return
            except Exception as fetch_error:
                print(f"❌ Failed to fetch activities: {str(fetch_error)}")
                return False

            # Create new activity objects
            new_activities = [
                Activity(
                    strava_id=act["id"],
                    name=act["name"],
                    distance=act["distance"],
                    moving_time=act["moving_time"],
                    elapsed_time=act["elapsed_time"],
                    total_elevation_gain=act["total_elevation_gain"],
                    average_speed=act["average_speed"],
                    max_speed=act["max_speed"],
                    start_date=datetime.datetime.strptime(act["start_date"], "%Y-%m-%dT%H:%M:%SZ"),
                )
                for act in activities if act["id"] not in existing_ids
            ]
            
            # Save with transaction handling
            try:
                db.session.bulk_save_objects(new_activities)
                db.session.commit()
                print(f"✅ Saved {len(new_activities)} new activities")
                return True
            except Exception as db_error:
                db.session.rollback()
                print(f"❌ Database Error: {str(db_error)}")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error in save_activities: {str(e)}")
            return False

def get_ftp_for_date(activity_date):
    """Get FTP for a given date"""
    ftp_record = FTPHistory.query.filter(FTPHistory.date <= activity_date).order_by(FTPHistory.date.desc()).first()
    return ftp_record.ftp if ftp_record else 200

def sync_training_load():
    """Sync training load data"""
    with app.app_context():
        activities = Activity.query.order_by(Activity.start_date).all()
        if not activities:
            print("❌ No activities found")
            return
            
        training_loads = []
        for act in activities:
            ftp = get_ftp_for_date(act.start_date.date())
            np = act.average_speed * 0.75 * ftp  # Simplified normalized power calculation
            intensity_factor = (np / ftp) if np else 0.75
            tss = round((act.moving_time / 3600 * np * intensity_factor) / ftp * 100, 2)
            
            training_loads.append({
                "date": act.start_date.date(),
                "tss": tss,
                "ctl": 0,  # Initialize CTL
                "atl": 0,  # Initialize ATL
                "tsb": 0   # Initialize TSB
            })
            
        # Calculate CTL, ATL, TSB
        if len(training_loads) > 0:
            training_loads[0]["ctl"] = training_loads[0]["tss"] / 42
            training_loads[0]["atl"] = training_loads[0]["tss"] / 7
            training_loads[0]["tsb"] = training_loads[0]["ctl"] - training_loads[0]["atl"]
            
            for i in range(1, len(training_loads)):
                prev = training_loads[i-1]
                curr = training_loads[i]
                curr["ctl"] = prev["ctl"] + (curr["tss"] - prev["ctl"]) / 42
                curr["atl"] = prev["atl"] + (curr["tss"] - prev["atl"]) / 7
                curr["tsb"] = curr["ctl"] - curr["atl"]
            
        # Save training loads
        existing_loads = {tl.date: tl for tl in TrainingLoad.query.all()}
        for load in training_loads:
            if load["date"] in existing_loads:
                tl = existing_loads[load["date"]]
                tl.tss = load["tss"]
                tl.ctl = load["ctl"]
                tl.atl = load["atl"]
                tl.tsb = load["tsb"]
            else:
                tl = TrainingLoad(
                    date=load["date"],
                    tss=load["tss"],
                    ctl=load["ctl"],
                    atl=load["atl"],
                    tsb=load["tsb"]
                )
                print(f"Adding Training Load: Date={tl.date}, TSS={tl.tss}, CTL={tl.ctl}, ATL={tl.atl}, TSB={tl.tsb}")
                db.session.add(tl)
                
        try:
            # Print that we are committing the new training load and print key info about it.
            for load in training_loads:
                print(f"Committing Training Load: Date={load['date']}, TSS={load['tss']}, CTL={load['ctl']}, ATL={load['atl']}, TSB={load['tsb']}")
            print
            db.session.commit()
            print("✅ Training load synced successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Sync Strava activities and training load")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run in scheduled mode (default: 6 hour intervals)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Sync interval in hours (default: 6)"
    )
    
    args = parser.parse_args()
    
    if args.schedule:
        while True:
            print("🔄 Starting sync...")
            save_activities()
            sync_training_load()
            print(f"✅ Sync complete. Sleeping for {args.interval} hours...")
            time.sleep(args.interval * 3600)
    else:
        print("🔄 Starting manual sync...")
        save_activities()
        sync_training_load()
        print("✅ Sync complete!")

if __name__ == "__main__":
    main()
