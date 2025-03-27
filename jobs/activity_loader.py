"""Module for loading basic activity data from Strava."""

import time
import os
import sys
import datetime
from flask import Flask

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strava.models import db, Activity

class ActivityLoader:
    """Handles loading basic activity data from Strava."""
    
    def __init__(self, app, strava_client, job_id):
        """
        Initialize the activity loader.
        
        Args:
            app: Flask application instance
            strava_client: StravaClient instance
            job_id: ID of the current sync job
        """
        self.app = app
        self.strava_client = strava_client
        self.job_id = job_id
        
    def load_activities(self, after_timestamp=0):
        """
        Load activities from Strava and save to database.
        
        Args:
            after_timestamp: Only load activities after this timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.app.app_context():
            print(f"🔄 Loading activities from Strava (Job ID: {self.job_id})...")
            self.strava_client.update_job_progress(self.job_id, "Fetching activities")
            
            # Fetch activities from Strava API
            activities = self.strava_client.fetch_activities(after_timestamp)
            
            if not activities:
                print("❌ No activities found")
                return False
                
            print(f"✅ Found {len(activities)} activities (Job ID: {self.job_id})")
            self.strava_client.update_job_progress(self.job_id, f"Processing {len(activities)} activities")
            
            # Save activities to database
            return self.save_activities(activities)
    
    def save_activities(self, activities):
        """
        Save activities to database.
        
        Args:
            activities: List of activity dictionaries from Strava API
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.app.app_context():
            try:
                # Get existing activity IDs
                existing_ids = {a.strava_id for a in Activity.query.with_entities(Activity.strava_id).all()}
                
                if not activities:
                    print("❌ No new activities found")
                    return False

                # Create new activity objects
                new_activities = []
                skipped_count = 0
                
                for act in activities:
                    if act["id"] not in existing_ids:
                        try:
                            # Convert values to proper Python types
                            strava_id = int(act["id"])
                            name = str(act["name"])
                            distance_meters = float(act["distance"]) if act["distance"] is not None else 0.0
                            distance_miles = distance_meters * 0.000621371  # Convert meters to miles
                            moving_time = int(act["moving_time"]) if act["moving_time"] is not None else 0
                            elapsed_time = int(act["elapsed_time"]) if act["elapsed_time"] is not None else 0
                            total_elevation_gain = float(act["total_elevation_gain"]) if act["total_elevation_gain"] is not None else 0.0
                            average_speed_mps = float(act["average_speed"]) if act["average_speed"] is not None else 0.0
                            average_speed_mph = average_speed_mps * 2.23694  # Convert meters per second to miles per hour
                            max_speed_mps = float(act["max_speed"]) if act["max_speed"] is not None else 0.0
                            max_speed_mph = max_speed_mps * 2.23694
                            start_date = datetime.datetime.strptime(act["start_date"], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Create activity object with basic fields
                            activity = Activity(
                                strava_id=strava_id,
                                name=name,
                                distance=distance_miles,
                                moving_time=moving_time,
                                elapsed_time=elapsed_time,
                                total_elevation_gain=total_elevation_gain,
                                average_speed=average_speed_mph,
                                max_speed=max_speed_mph,
                                start_date=start_date
                            )
                            
                            new_activities.append(activity)
                            
                        except (ValueError, TypeError) as e:
                            print(f"❌ Data conversion error for activity {act.get('id')}: {str(e)}")
                            skipped_count += 1
                            continue
                    else:
                        skipped_count += 1
                
                # Save with transaction handling
                try:
                    if new_activities:
                        for activity in new_activities:
                            db.session.add(activity)
                            
                        db.session.commit()
                        print(f"✅ Saved {len(new_activities)} new activities (Job ID: {self.job_id})")
                        print(f"  Skipped {skipped_count} existing activities (Job ID: {self.job_id})")
                        self.strava_client.update_job_progress(self.job_id, f"Saved {len(new_activities)} new activities")
                        return True
                    else:
                        print(f"✅ No new activities to save (Job ID: {self.job_id})")
                        print(f"  Skipped {skipped_count} existing activities (Job ID: {self.job_id})")
                        self.strava_client.update_job_progress(self.job_id, "No new activities found")
                        return False
                        
                except Exception as db_error:
                    db.session.rollback()
                    print(f"❌ Database Error: {str(db_error)}")
                    return False
                    
            except Exception as e:
                print(f"❌ Unexpected error in save_activities: {str(e)}")
                return False
