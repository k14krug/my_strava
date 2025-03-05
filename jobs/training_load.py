"""Module for calculating and updating training load metrics."""

import time
import os
import sys
import datetime
import math  # <-- add math import if not present
from flask import Flask

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strava.models import db, Activity, TrainingLoad, FTPHistory

class TrainingLoadCalculator:
    """Handles training load calculations and updates."""
    
    def __init__(self, app):
        """
        Initialize the training load calculator.
        
        Args:
            app: Flask application instance
        """
        self.app = app
    
    def estimate_np(self, average_speed, distance, total_elevation_gain):
        """
        Estimate NP based on the regression coefficients from statsmodels.
        Assumes you're using the same units as in your training data.
        """
        speed_cubed = average_speed ** 3
        np_est = (
            29.604638
            + 7.300535 * average_speed
            - 0.002229 * speed_cubed
            + 0.149428 * distance
            + 0.050259 * total_elevation_gain
        )
        return np_est
        
    def sync_training_load(self, after_date=None):
        """
        Calculate and update training load data.
        
        Args:
            after_date: Optional date to calculate training load after
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.app.app_context():
            print("Starting training load sync...")
            
            # Get all activities ordered by date
            query = Activity.query.order_by(Activity.start_date)
            
            # Apply date filter if specified
            if after_date:
                query = query.filter(Activity.start_date >= after_date)
                
            activities = query.all()
            
            if not activities:
                print("❌ No activities found")
                return False
            
            print(f"Found {len(activities)} activities to process")
            
            # Get existing training loads
            existing_loads = {tl.date: tl for tl in TrainingLoad.query.all()}
            print(f"Found {len(existing_loads)} existing training load records")
            
            # Process each activity and calculate training load
            training_loads = []
            activity_count = 0
            power_activity_count = 0
            
            for act in activities:
                activity_count += 1
                if activity_count % 50 == 0:
                    print(f"Processing activity {activity_count}/{len(activities)}...")
                
                # Calculate FTP for this date
                ftp = self.get_ftp_for_date(act.start_date.date())
                
                # Calculate normalized power (use actual or estimate)
                speed_mps = act.average_speed * 0.44704  # Convert to m/s if needed
                np = act.normalized_power if act.normalized_power else self.estimate_np(act.average_speed, act.distance, act.total_elevation_gain)
                if act.normalized_power:
                    power_activity_count += 1
                
                # Calculate intensity factor
                intensity_factor = (np / ftp) if np and ftp else 0.75
                
                # Calculate TSS
                tss = round((act.moving_time / 3600 * np * intensity_factor) / ftp * 100, 2) if np and ftp else 0
                
                # Calculate power metrics
                power_tss = tss if act.normalized_power else 0
                avg_normalized_power = act.normalized_power if act.normalized_power else 0
                max_daily_power = act.max_power if act.max_power else 0
                power_balance = 1.0
                
                # Store date and training load for this activity
                activity_date = act.start_date.date()
                
                # Check if we already have an entry for this date
                existing_entry = next((tl for tl in training_loads if tl["date"] == activity_date), None)
                
                if existing_entry:
                    # Update existing entry with additional load
                    existing_entry["tss"] += tss
                    existing_entry["power_tss"] += power_tss
                    existing_entry["avg_normalized_power"] = max(existing_entry["avg_normalized_power"], avg_normalized_power)
                    existing_entry["max_daily_power"] = max(existing_entry["max_daily_power"], max_daily_power)
                else:
                    # Create new entry
                    training_loads.append({
                        "date": activity_date,
                        "tss": tss,
                        "ctl": 0,  # Initialize CTL
                        "atl": 0,  # Initialize ATL
                        "tsb": 0,  # Initialize TSB
                        "avg_normalized_power": avg_normalized_power,
                        "max_daily_power": max_daily_power,
                        "power_balance": power_balance,
                        "power_tss": power_tss
                    })
                
            print(f"Processed {power_activity_count} activities with power data")
            
            # Calculate CTL, ATL, TSB
            self._calculate_fitness_metrics(training_loads)
            
            # Save training loads to database
            return self._save_training_loads(training_loads, existing_loads)
    
    def _calculate_fitness_metrics(self, training_loads):
        """
        Calculate CTL, ATL, and TSB for training loads.
        
        Args:
            training_loads: List of training load dictionaries
        """
        atl_days = 7  # ATL time constant in days
        atl_decay_variable = 0.9  # ATL decay factor for non-consecutive days
        atl_increase_dampening = 0.7  # dampening factor for ATL increases
        
        if len(training_loads) > 0:
            training_loads.sort(key=lambda x: x["date"])
            
            # Initialize first day
            training_loads[0]["ctl"] = training_loads[0]["tss"] / 42
            training_loads[0]["atl"] = training_loads[0]["tss"] / atl_days
            training_loads[0]["tsb"] = training_loads[0]["ctl"] - training_loads[0]["atl"]
            
            for i in range(1, len(training_loads)):
                prev = training_loads[i-1]
                curr = training_loads[i]
                date_diff = (curr["date"] - prev["date"]).days
                if date_diff == 1:
                    # Consecutive days
                    curr["ctl"] = prev["ctl"] + (curr["tss"] - prev["ctl"]) / 42
                    curr["atl"] = prev["atl"] + atl_increase_dampening * ((curr["tss"] - prev["atl"]) / atl_days)
                else:
                    # Gap in days, applying same exponential decay as in ctl_test.py
                    decayed_ctl = prev["ctl"] * math.exp(- (date_diff - 1) / 42.0)
                    curr["ctl"] = decayed_ctl + (curr["tss"] - decayed_ctl) / 42.0
                    # For ATL, keeping existing decay calculation
                    decay_atl = pow(atl_decay_variable, date_diff)
                    curr["atl"] = prev["atl"] * decay_atl + atl_increase_dampening * (curr["tss"] * (1 - decay_atl) / atl_days)
                curr["tsb"] = curr["ctl"] - curr["atl"]
    
    def _save_training_loads(self, training_loads, existing_loads):
        """
        Save training loads to database.
        
        Args:
            training_loads: List of training load dictionaries
            existing_loads: Dictionary of existing training loads
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("Beginning database update...")
        updates = 0
        inserts = 0
        
        try:
            # Save training loads
            for load in training_loads:
                date = load["date"]
                if date in existing_loads:
                    tl = existing_loads[date]
                    
                    # Update values
                    tl.tss = load["tss"]
                    tl.ctl = load["ctl"] 
                    tl.atl = load["atl"]
                    tl.tsb = load["tsb"]
                    tl.avg_normalized_power = load["avg_normalized_power"]
                    tl.max_daily_power = load["max_daily_power"]
                    tl.power_balance = load["power_balance"]
                    tl.power_tss = load["power_tss"]
                    
                    updates += 1
                else:
                    tl = TrainingLoad(
                        date=date,
                        tss=load["tss"],
                        ctl=load["ctl"],
                        atl=load["atl"],
                        tsb=load["tsb"],
                        avg_normalized_power=load["avg_normalized_power"],
                        max_daily_power=load["max_daily_power"],
                        power_balance=load["power_balance"],
                        power_tss=load["power_tss"]
                    )
                    db.session.add(tl)
                    inserts += 1
            
            #print(f"Committing changes: {updates} updates, {inserts} inserts")
            db.session.commit()
            print(f"✅ Training load synced successfully")
            
            # Verify the changes
            verification = TrainingLoad.query.filter(TrainingLoad.avg_normalized_power > 0).count()
            print(f"Verification: {verification} training load records now have normalized power > 0")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database Error: {str(e)}")
            return False
    
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