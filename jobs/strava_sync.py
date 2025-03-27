"""Main entry point for Strava synchronization utilities.

Command-line Usage:
-----------------

1. Sync Activities:
   python strava_sync.py activities [options]
   
   Options:
     --after-date YYYY-MM-DD  : Only 
        activities on or after this date
     --update-training        : Recalculate training load metrics after loading activities

2. Load Stream Data:
   python strava_sync.py streams [options]
   
   Options:
     --limit N                : Process only N activities (0 = no limit)
     --after-date YYYY-MM-DD  : Only process activities on or after this date
     --update-training        : Recalculate training load metrics after loading streams
     --activity-type TYPE     : Only process activities with names containing this text

3. Update Training Load:
   python strava_sync.py training
   
   This command has no additional options and will recalculate all training metrics
   (CTL, ATL, TSB) based on existing activity data.

Examples:
--------
# Fetch new activities from January 2025 onward and update training load
python strava_sync.py activities --after-date 2025-01-01 --update-training

# Process stream data for up to 10 recent activities
python strava_sync.py streams --limit 10 --update-training

# Only process Zwift activities
python strava_sync.py streams --activity-type Zwift

# Recalculate all training load metrics
python strava_sync.py training
"""

import argparse
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the modules
from jobs.jobs_config import create_app
from jobs.activity_loader import ActivityLoader
from jobs.stream_loader import StreamLoader
from jobs.training_load import TrainingLoadCalculator
from jobs.strava_client import StravaClient
from jobs.segment_loader import SegmentLoader


def main():
    """Main entry point for Strava sync utilities."""
    parser = argparse.ArgumentParser(description="Strava data synchronization utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Activities command
    activities_parser = subparsers.add_parser("activities", help="Sync basic activity data")
    activities_parser.add_argument("--after-date", help="Load activities after this date (YYYY-MM-DD)")
    activities_parser.add_argument("--update-training", action="store_true", help="Update training load after loading activities")
    
    # Streams command
    streams_parser = subparsers.add_parser("streams", help="Load activity streams")
    streams_parser.add_argument("--update-training", action="store_true", help="Update training load after loading streams")
    streams_parser.add_argument("--limit", type=int, default=0, help="Limit number of streams to process")
    streams_parser.add_argument("--after-date", help="Load streams for activities after this date (YYYY-MM-DD)")
    streams_parser.add_argument("--activity-type", help="Only process activities with names containing this text")
    
    # Training load command
    training_parser = subparsers.add_parser("training", help="Recalculate training load metrics")
    
    # Segments command
    segments_parser = subparsers.add_parser("segments", help="Load segment data")
    segments_parser.add_argument("--update-training", action="store_true", help="Update training load after loading segments")
    segments_parser.add_argument("--limit", type=int, default=0, help="Limit number of segments to process")
    segments_parser.add_argument("--after-date", help="Load segments for activities after this date (YYYY-MM-DD)")
    segments_parser.add_argument("--activity-type", help="Only process segments from activities with names containing this text")
    
    # Add job-id parameter to the main parser so it's available for all commands
    parser.add_argument("--job-id", help="Job ID for tracking progress (if not provided, a new job will be created)")
    
    # Initialize the system
    args = parser.parse_args()
    app = create_app()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run within application context
    with app.app_context():
        strava_client = StravaClient()
        
        # Use provided job ID or create new one
        job_id = args.job_id if args.job_id else strava_client.start_job(args.command)
        print(f"🚀 Starting {args.command} job (ID: {job_id})")
        
        try:
            # Process the command
            if args.command == "activities":
                after_timestamp = 0
                if args.after_date:
                    after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
                    after_timestamp = int(after_date.timestamp())
                    print(f"🔍 Loading activities after {args.after_date}")
                else:
                    print("🔍 Loading activities using the default activity")
                
                # Create activity loader and run it
                activity_loader = ActivityLoader(app, strava_client, job_id)
                loaded = activity_loader.load_activities(after_timestamp)
                
                # Update training load if requested
                if loaded and args.update_training:
                    print("🔄 Updating training load metrics...")
                    training_calc = TrainingLoadCalculator(app)
                    training_calc.sync_training_load()
            
            elif args.command == "streams":
                # Create stream loader and run it
                after_date = None
                if args.after_date:
                    after_date = datetime.strptime(args.after_date, "%Y-%m-%d").date()
                    print(f"🔍 Loading streams for activities after {args.after_date}")
                    
                stream_loader = StreamLoader(app, strava_client, job_id)
                loaded = stream_loader.load_missing_streams(limit=args.limit, activity_type=args.activity_type, after_date=after_date)
                
                # Update training load if requested
                if loaded and args.update_training:
                    print("🔄 Updating training load metrics...")
                    training_calc = TrainingLoadCalculator(app)
                    training_calc.sync_training_load()
            
            elif args.command == "training":
                # Recalculate training load metrics
                print("🔄 Recalculating training load metrics...")
                training_calc = TrainingLoadCalculator(app)
                training_calc.sync_training_load()
            
            elif args.command == "segments":
                # Create segment loader and run it
                after_date = None
                if args.after_date:
                    after_date = datetime.strptime(args.after_date, "%Y-%m-%d").date()
                    print(f"🔍 Loading segments for activities after {args.after_date}")
                    
                segment_loader = SegmentLoader(app, strava_client, job_id)
                loaded = segment_loader.load_missing_segments(limit=args.limit, activity_type=args.activity_type, after_date=after_date)
                
                # Update training load if requested
                if loaded and args.update_training:
                    print("🔄 Updating training load metrics...")
                    training_calc = TrainingLoadCalculator(app)
                    training_calc.sync_training_load()
        
            # Report API usage
            usage = strava_client.get_api_usage()
            print(f"📊 API Usage: {usage['short_term']['used']}/{usage['short_term']['limit']} (15-min), {usage['daily']['used']}/{usage['daily']['limit']} (daily)")
            
            # Only update job status if we didn't receive a job ID (we created it here)
            if not args.job_id:
                strava_client.end_job(job_id, True, message=f"Completed {args.command} sync")
            print(f"✅ {args.command} job completed successfully (ID: {job_id})")
            
        except Exception as e:
            # Only update job status if we didn't receive a job ID (we created it here)
            if not args.job_id:
                strava_client.end_job(job_id, False, str(e), "Job failed")
            print(f"❌ Job {job_id} failed: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
