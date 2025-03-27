"""Module for loading activity stream data from Strava."""

import time
import os
import sys
import datetime
from flask import Flask

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strava.models import db, Activity, FTPHistory
from power_metrics import PowerCalculator

class StreamLoader:
    """Handles loading activity stream data from Strava."""
    
    def __init__(self, app, strava_client, job_id):
        """
        Initialize the stream loader.
        
        Args:
            app: Flask application instance
            strava_client: StravaClient instance
            job_id: ID of the current sync job
        """
        self.app = app
        self.strava_client = strava_client
        self.job_id = job_id
    
    def load_missing_streams(self, limit=0, activity_type=None, after_date=None):
        """
        Load stream data for activities that don't have power metrics.
        
        Args:
            limit: Maximum number of activities to process (0 = no limit)
            activity_type: Optional filter for activity type
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.app.app_context():
            print(f"🔄 Loading missing streams (Job ID: {self.job_id})...")
            self.strava_client.update_job_progress(self.job_id, "Finding activities needing streams")
            
            ## Query for activities without power data
            #query = Activity.query.filter(Activity.normalized_power.is_(None))
            # Query for activities without power data OR with zero best_10m_power despite having moving time
            query = Activity.query.filter(
                db.or_(
                    Activity.normalized_power.is_(None),
                    db.and_(
                        Activity.best_10m_power.is_(None),
                        Activity.moving_time > 0
                    )
                )
            )
            print(f"  Found {query.count()} activities without power metrics")
            
            # Filter by activity type if specified
            if activity_type:
                query = query.filter(Activity.name.like(f'%{activity_type}%'))
                print(f"  Filtering by activity type: {activity_type} found {query.count()} activities")
                
            # Get most recent activities first
            if after_date:
                query = query.filter(Activity.start_date >= after_date)
                print(f"  Filtering by date: after {after_date} found {query.count()} activities")
            
            # Apply limit if specified
            if limit > 0:
                query = query.limit(limit)
                print(f"  Limiting to {limit} activities")
                
            activities = query.all()
            
            if not activities:
                print("❌ No activities found that need streams")
                return False
                
            print(f"✅ Found {len(activities)} activities that need streams (Job ID: {self.job_id})")
            self.strava_client.update_job_progress(self.job_id, f"Processing {len(activities)} activities")
            
            # Process activities
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            for act in activities:
                try:
                    print(f"Processing activity {act.id}: {act.name} ({act.start_date})")
                    
                    # Skip very old activities (before 2013) to avoid 404 errors
                    if act.start_date.year < 2013:
                        print(f"⚠️ Skipping activity from {act.start_date.year} (too old)")
                        skipped_count += 1
                        continue
                    

                    # Fetch stream data from Strava API
                    stream_data = self.strava_client.fetch_activity_stream(act.strava_id)
                    
                    if not stream_data:
                        print(f"❌ No stream data for activity {act.id}")
                        error_count += 1
                        continue
                    
                    # Check if there's power data
                    if 'watts' not in stream_data or not stream_data['watts']:
                        print(f"⚠️ No power data in stream for activity {act.id}")
                        skipped_count += 1
                        continue
                    
                    # Calculate power metrics
                    power_metrics = PowerCalculator.calculate_power_intervals(stream_data)
                    
                    if not power_metrics:
                        print(f"❌ Failed to calculate power metrics for activity {act.id}")
                        error_count += 1
                        continue
                        
                    # Update activity with power metrics
                    self._update_activity_power_metrics(act, power_metrics, stream_data)
                    updated_count += 1
                    
                    # Commit every 5 activities to avoid large transactions
                    if updated_count % 5 == 0:
                        db.session.commit()
                        print(f"✅ Committed {updated_count} activities so far")
                    
                    # Throttle API requests
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Error processing activity {act.id}: {str(e)}")
                    error_count += 1
                    # Reset session if needed
                    db.session.rollback()
            
            # Commit any remaining changes
            try:
                if updated_count % 5 != 0 and updated_count > 0:
                    db.session.commit()
                
                print(f"✅ Stream loading completed (Job ID: {self.job_id})")
                print(f"  Updated: {updated_count} activities")
                print(f"  Skipped: {skipped_count} activities")
                print(f"  Errors: {error_count} activities")
                self.strava_client.update_job_progress(self.job_id, f"Updated {updated_count} activities")
                return updated_count > 0
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Database error: {str(e)}")
                return False
    
    def _update_activity_power_metrics(self, activity, power_metrics, stream_data):
        """
        Update activity with calculated power metrics.
        
        Args:
            activity: Activity object
            power_metrics: Power metrics dictionary
            stream_data: Stream data used for calculations
        """
        print(f"✅ Updating power metrics for activity {activity.id}")
        try:
            # Convert all values to float with explicit type casting
            activity.best_10m_power = float(power_metrics['best_10m_power'])
            activity.best_20m_power = float(power_metrics['best_20m_power']) 
            activity.best_30m_power = float(power_metrics['best_30m_power'])
            activity.best_45m_power = float(power_metrics['best_45m_power'])
            activity.best_1hr_power = float(power_metrics['best_1hr_power'])
            activity.max_power = float(power_metrics['max_power'])
            activity.normalized_power = float(power_metrics['normalized_power'])
            
            # Calculate intensity factor
            ftp = float(self.get_ftp_for_date(activity.start_date.date()))
            if ftp > 0:
                activity.intensity_factor = float(power_metrics['normalized_power'] / ftp)
            else:
                activity.intensity_factor = 0.0
            
            # Calculate variability index
            if 'watts' in stream_data and stream_data['watts']:
                avg_watts = sum(stream_data['watts']) / len(stream_data['watts'])
                if avg_watts > 0:
                    activity.variability_index = float(power_metrics['normalized_power'] / avg_watts)
                else:
                    activity.variability_index = 1.0
            else:
                activity.variability_index = 1.0
                
        except Exception as e:
            print(f"❌ Error updating activity metrics: {str(e)}")
            raise
    
    def get_ftp_for_date(self, activity_date):
        """
        Get FTP for a given date.
        
        Args:
            activity_date: Date to get FTP for
            
        Returns:
            int: FTP value
        """
        with self.app.app_context():
            ftp_record = FTPHistory.query.filter(FTPHistory.date <= activity_date).order_by(FTPHistory.date.desc()).first()
            return ftp_record.ftp if ftp_record else 200  # Default to 200 if no FTP record
