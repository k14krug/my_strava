from datetime import datetime
import logging
from typing import Optional

from sqlalchemy.orm import Session

from strava.models import db, Segment, Activity, SegmentEffort
from jobs.strava_client import StravaClient
from jobs.jobs_config import create_app

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SegmentLoader:
    """Loader for fetching and processing Strava segment data."""

    def __init__(self, app, strava_client: StravaClient):
        """Initialize the segment loader.
        
        Args:
            app: Flask application instance
            strava_client: Strava API client
        """
        self.app = app
        self.strava_client = strava_client

    def load_missing_segments(
        self,
        limit: int = 0,
        activity_type: Optional[str] = None,
        after_date: Optional[datetime] = None
    ) -> bool:
        """Load segment data for activities that don't have segments processed.
        
        Args:
            limit: Maximum number of activities to process (0 = no limit)
            activity_type: Only process activities of this type
            after_date: Only process activities after this date
            
        Returns:
            bool: True if any segments were loaded, False otherwise
        """
        print(f"Loading missing segments for data range after {after_date}")
        with self.app.app_context():
            loaded = False
            
            # Get activities that need segment processing
            query = db.session.query(Activity)
            
            if after_date:
                query = query.filter(Activity.start_date >= after_date)
                
            if activity_type:
                query = query.filter(Activity.name.ilike(f'%{activity_type}%'))
                
            # Ensure earliest activities come first
            query = query.order_by(Activity.start_date.asc())
            
            if limit > 0:
                query = query.limit(limit)
                
            activities = query.all()
            
            if not activities:
                logger.info("No activities found for segment processing")
                return False
                
            # Process each activity
            for activity in activities:
                if self._process_activity_segments(activity):
                    loaded = True
                    
            return loaded

    def _process_activity_segments(self, activity: Activity) -> bool:
        """Process segments for a single activity.
        
        Args:
            activity: Activity to process segments for
            
        Returns:
            bool: True if segments were processed, False otherwise
        """
        logger.info(f"Processing segments for activity {activity.strava_id} {activity.start_date} ({activity.name})")
        
        # Check if the activity already has segment efforts in the database
        existing_effort = db.session.query(SegmentEffort).filter_by(activity_id=activity.id).first()
        if existing_effort:
            logger.info(f"Activity {activity.strava_id} already has segment efforts loaded. Skipping API call.")
            return True

        try:
            # Only call the API if no segment efforts exist
            segment_efforts = self.strava_client.get_segment_efforts(activity.strava_id)
            if not segment_efforts:
                logger.info(f"No segment efforts found for activity {activity.strava_id}")
                return False

            logger.info(f"Found {len(segment_efforts)} segment efforts for activity {activity.strava_id}")

            # Process each segment effort
            for effort in segment_efforts:
                try:
                    self._process_segment_effort(activity, effort)
                except Exception as e:
                    logger.error(f"Error processing segment effort: {str(e)}")
                    logger.debug(f"Segment effort data: {effort}")
                    continue

            return True

        except Exception as e:
            logger.error(f"Error processing segments for activity {activity.id}: {str(e)}")
            logger.debug(f"Activity details: {activity.to_dict()}")
            return False

    def _process_segment_effort(
        self,
        activity: Activity,
        effort: dict
    ) -> None:
        """Process a single segment effort.
        
        Args:
            activity: Parent activity
            effort: Segment effort data from Strava API
        """
        segment_data = effort['segment']
        
        # Check if segment already exists
        segment = db.session.query(Segment).filter_by(strava_id=segment_data['id']).first()
        
        if not segment:
            # Create new segment record
            segment = Segment(
                strava_id=segment_data['id'],
                name=segment_data['name'],
                activity_type=segment_data['activity_type'],
                distance=segment_data['distance'],
                average_grade=segment_data['average_grade'],
                maximum_grade=segment_data['maximum_grade'],
                elevation_high=segment_data['elevation_high'],
                elevation_low=segment_data['elevation_low'],
                start_latlng=segment_data['start_latlng'],
                end_latlng=segment_data['end_latlng'],
                climb_category=segment_data['climb_category'],
                city=segment_data['city'],
                state=segment_data['state'],
                country=segment_data['country'],
                private=segment_data['private'],
                hazardous=segment_data['hazardous'],
                created_at=datetime.utcnow()
                #updated_at=datetime.utcnow()
            )
            db.session.add(segment)
            db.session.commit()
        
        # Convert start_date to datetime object
        start_date = datetime.strptime(effort['start_date'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Create a new SegmentEffort instance
        segment_effort = SegmentEffort(
            activity_id=activity.id,
            segment_id=segment.id,
            elapsed_time=effort['elapsed_time'],
            moving_time=effort['moving_time'],
            start_date=start_date,
            distance=effort['distance'],
            average_watts=effort.get('average_watts'),
            average_heartrate=effort.get('average_heartrate'),
            max_heartrate=effort.get('max_heartrate'),
            kom_rank=effort.get('kom_rank'),
            pr_rank=effort.get('pr_rank')
        )
        
        db.session.add(segment_effort)
        db.session.commit()