"""Client for interacting with the Strava API."""

import time
import requests
import os
import threading
from .jobs_config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, STRAVA_AUTH_URL, STRAVA_API_URL
from dotenv import load_dotenv, set_key
from datetime import datetime, timedelta, timezone


class StravaClient:
    """Client for interacting with the Strava API."""
    
    def __init__(self):
        """Initialize the Strava client."""
        # Load environment variables
        load_dotenv(override=True)
        
        # Get configuration from environment
        self.client_id = os.getenv("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        self.refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
        
        # Job tracking state
        self._jobs = {}
        self._api_usage = {
            'short_term': {'used': 0, 'limit': 100},
            'daily': {'used': 0, 'limit': 1000}
        }
        self._lock = threading.Lock()
        
        # Ensure environment variables are loaded correctly
        if not self.client_id or not self.client_secret or not self.refresh_token:
            print("❌ Missing required environment variables for Strava API")
            raise ValueError("Missing required environment variables for Strava API")
        
        # Try to load saved token data
        self.access_token = os.getenv("STRAVA_ACCESS_TOKEN")
        self.token_expires_at = int(os.getenv("STRAVA_TOKEN_EXPIRES_AT", "0"))
    
    def get_access_token(self, force_refresh=False):
        """Get a valid access token, refreshing if necessary.
        
        Args:
            force_refresh: Force refresh even if the token is not expired
        """
        current_time = int(time.time())
        
        # Return existing token if it's still valid and not forcing refresh
        if not force_refresh and self.access_token and self.token_expires_at > current_time + 60:
            return self.access_token
            
        # Request new token
        print("🔄 Requesting new access token...")
        try:
            response = requests.post(
                "https://www.strava.com/oauth/token",
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token
                }
            )
            response.raise_for_status()
            token_data = response.json()
            print("Token data received:", token_data)
            
            self.access_token = token_data['access_token']
            self.token_expires_at = token_data['expires_at']
            
            # Save tokens to .env file
            self._save_tokens_to_env()
            
            expires_in = self.token_expires_at - current_time
            print(f"✅ Access token obtained (expires in {expires_in} seconds)")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get access token: {str(e)}")
            if e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            return None
    
    def _save_tokens_to_env(self):
        """Save access token and expiration to .env file."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        
        # Update values in .env file
        set_key(env_path, "STRAVA_ACCESS_TOKEN", self.access_token)
        set_key(env_path, "STRAVA_TOKEN_EXPIRES_AT", str(self.token_expires_at))
        
        print("✅ Saved token information to .env file")
    
    def check_rate_limits(self, headers):
        """Check API rate limits and wait if necessary."""
        try:
            # Default values if headers are missing or invalid
            default_limits = {
                'usage_short': 0,
                'limit_short': 100,
                'usage_daily': 0,
                'limit_daily': 1000,
                'read_usage_short': 0,
                'read_limit_short': 100,
                'read_usage_daily': 0,
                'read_limit_daily': 1000
            }
            
            # Update API usage tracking
            with self._lock:
                usage = self._parse_rate_limit_header(headers.get("X-RateLimit-Usage"))
                if usage:
                    self._api_usage['short_term']['used'] = usage[0]
                    self._api_usage['daily']['used'] = usage[1]
            
            # Parse rate limit headers with validation
            def parse_header(header, default):
                try:
                    if not header or not isinstance(header, str):
                        return default
                    parts = header.split(",")
                    if len(parts) != 2:
                        return default
                    return [int(part) for part in parts]
                except (ValueError, TypeError):
                    return default
            
            usage = parse_header(headers.get("X-RateLimit-Usage"), [default_limits['usage_short'], default_limits['usage_daily']])
            limits = parse_header(headers.get("X-RateLimit-Limit"), [default_limits['limit_short'], default_limits['limit_daily']])
            read_usage = parse_header(headers.get("X-ReadRateLimit-Usage"), [default_limits['read_usage_short'], default_limits['read_usage_daily']])
            read_limits = parse_header(headers.get("X-ReadRateLimit-Limit"), [default_limits['read_limit_short'], default_limits['read_limit_daily']])
            
            # Extract values
            usage_short, usage_daily = usage
            limit_short, limit_daily = limits
            read_usage_short, read_usage_daily = read_usage
            read_limit_short, read_limit_daily = read_limits
            
            print(f"Short-term usage: {usage_short}/{limit_short}")
            print(f"Daily usage: {usage_daily}/{limit_daily}")
            print(f"Read short-term usage: {read_usage_short}/{read_limit_short}")
            print(f"Read daily usage: {read_usage_daily}/{read_limit_daily}")
            
            # Check if we're near any limits
            if usage_short >= limit_short - 2 or read_usage_short >= read_limit_short - 2:
                print(f"⚠️ Short-term rate limit nearly reached: {usage_short}/{limit_short} or {read_usage_short}/{read_limit_short}")
                try:
                    reset_time = int(headers.get("X-RateLimit-Reset", "15"))
                    print(f"Waiting {reset_time} seconds before continuing...")
                    time.sleep(reset_time)
                    return False
                except (ValueError, TypeError):
                    print("⚠️ Invalid reset time, waiting 15 seconds")
                    time.sleep(15)
                    return False
            
            if usage_daily >= limit_daily or read_usage_daily >= read_limit_daily:
                print(f"❌ Daily rate limit reached: {usage_daily}/{limit_daily} or {read_usage_daily}/{read_limit_daily}")
                
                # Calculate time until midnight UTC
                now = datetime.now(timezone.utc)
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                seconds_until_midnight = (tomorrow - now).total_seconds()
                
                print(f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Next reset at UTC midnight: {tomorrow.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Waiting {int(seconds_until_midnight)} seconds until daily reset at midnight UTC...")
                
                # Add a small buffer (30 seconds) to ensure we're past midnight
                time.sleep(int(seconds_until_midnight) + 30)
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error checking rate limits: {str(e)}")
            # Default to True to allow the request to proceed
            return True
    
    def fetch_activities(self, after_timestamp=0):
        """Fetch activities from Strava API."""
        token = self.get_access_token()
        if not token:
            return []
            
        headers = {"Authorization": f"Bearer {token}"}
        activities = []
        page = 1
        max_token_refresh_attempts = 3
        token_refresh_attempts = 0
        
        while True:
            try:
                print(f"Fetching page {page} of activities...")
                response = requests.get(
                    STRAVA_API_URL, 
                    headers=headers, 
                    params={
                        "per_page": 200,
                        "after": after_timestamp,
                        "page": page
                    }
                )
                
                if response.status_code == 401:
                    if token_refresh_attempts >= max_token_refresh_attempts:
                        print("❌ Maximum token refresh attempts reached")
                        return []
                    print("❌ Unauthorized Activities access - refreshing token")
                    token = self.get_access_token()
                    if not token:
                        return []
                    headers["Authorization"] = f"Bearer {token}"
                    token_refresh_attempts += 1
                    continue
                
                if not self.check_rate_limits(response.headers):
                    break
                    
                response.raise_for_status()
                page_activities = response.json()
                if not page_activities:
                    print(f"No activities found on page {page}")
                    break
                    
                print(f"Found {len(page_activities)} activities on page {page}")
                activities.extend(page_activities)
                page += 1
                time.sleep(2)  # Basic rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"❌ API Error: {str(e)}")
                break
                
        return activities
    
    def get_segment_efforts(self, activity_id):
        """Fetch segment efforts for an activity from Strava API.
        
        Args:
            activity_id: ID of the activity to get segment efforts for
            
        Returns:
            List of segment effort objects or None if error occurs
        """
        token = self.get_access_token()
        if not token:
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        max_retries = 3
        retry_delay = 2
        max_token_refresh_attempts = 3
        token_refresh_attempts = 0
        
        for attempt in range(max_retries):
            try:
                print(f"Fetching segment efforts for activity {activity_id}")
                response = requests.get(
                    f"{STRAVA_API_URL}/{activity_id}",
                    headers=headers
                )
                if response.status_code == 401:
                    if token_refresh_attempts >= max_token_refresh_attempts:
                        print("❌ Maximum token refresh attempts reached")
                        return None
                    print("❌ Unauthorized access - refreshing token")
                    token = self.get_access_token(force_refresh=True)
                    if not token:
                        return None
                    headers["Authorization"] = f"Bearer {token}"
                    token_refresh_attempts += 1
                    continue
                
                # Check rate limits
                if not self.check_rate_limits(response.headers):
                    continue
                    
                response.raise_for_status()
                activity_data = response.json()
            
                # Extract segment efforts from activity data
                segment_efforts = activity_data.get('segment_efforts', [])
                print(f"Found {len(segment_efforts)} segment efforts in activity {activity_id}")
                return segment_efforts
                
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 429:
                        print(f"❌ API Error (attempt {attempt + 1}/{max_retries}): Too Many Requests")
                        try:
                            reset_time = int(e.response.headers.get("X-RateLimit-Reset", retry_delay))
                            print(f"Waiting for {reset_time} seconds before retrying...")
                            time.sleep(reset_time)
                        except (ValueError, TypeError, AttributeError):
                            time.sleep(retry_delay)
                        retry_delay *= 2
                    elif e.response.status_code == 404:
                        print(f"❌ Activity {activity_id} not found (404)")
                        return None
                    else:
                        print(f"❌ API Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            return None
                else:
                    print(f"❌ API Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        return None
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        return None

    def start_job(self, job_type):
        """Start tracking a new job."""
        from strava.models import Job, db
        from datetime import datetime
        import uuid
        
        # Generate a job ID
        job_id = f"{job_type}_{int(time.time())}"
        
        try:
            # Create a new job record in the database
            job = Job(
                id=job_id,
                job_type=job_type,
                status="running",
                start_time=datetime.utcnow(),
                message="Job started"
            )
            db.session.add(job)
            db.session.commit()
            
            # Also keep in memory for backward compatibility
            with self._lock:
                self._jobs[job_id] = {
                    'type': job_type,
                    'status': 'running',
                    'start_time': time.time(),
                    'end_time': None,
                    'success': None,
                    'error': None,
                    'message': None
                }
                
            return job_id
        except Exception as e:
            print(f"❌ Error creating job: {str(e)}")
            # Fallback to in-memory only
            with self._lock:
                self._jobs[job_id] = {
                    'type': job_type,
                    'status': 'running',
                    'start_time': time.time(),
                    'end_time': None,
                    'success': None,
                    'error': None,
                    'message': None
                }
            return job_id

    def end_job(self, job_id, success, error=None, message=None):
        """Mark a job as completed."""
        from strava.models import Job, db
        from datetime import datetime
        
        try:
            # Update the job record in the database
            job = Job.query.get(job_id)
            if job:
                job.status = "completed"
                job.end_time = datetime.utcnow()
                job.success = success
                job.message = message
                db.session.commit()
                print(f"✅ Updated job {job_id} status in database")
            else:
                print(f"❌ Job {job_id} not found in database")
                
            # Also update in-memory for backward compatibility
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update({
                        'status': 'completed',
                        'end_time': time.time(),
                        'success': success,
                        'error': error,
                        'message': message
                    })
        except Exception as e:
            print(f"❌ Error updating job: {str(e)}")
            # Fallback to in-memory only
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update({
                        'status': 'completed',
                        'end_time': time.time(),
                        'success': success,
                        'error': error,
                        'message': message
                    })

    def get_job_status(self, job_id):
        """Get the current status of a job."""
        from strava.models import Job
        
        try:
            # Get the job record from the database
            job = Job.query.get(job_id)
            if job:
                # Convert database record to dictionary format
                return {
                    'type': job.job_type,
                    'status': job.status,
                    'start_time': job.start_time.timestamp() if job.start_time else None,
                    'end_time': job.end_time.timestamp() if job.end_time else None,
                    'success': job.success,
                    'message': job.message
                }
            
            # Fallback to in-memory job tracking if not in database
            with self._lock:
                return self._jobs.get(job_id)
        except Exception as e:
            print(f"❌ Error getting job status: {str(e)}")
            # Fallback to in-memory job tracking
            with self._lock:
                return self._jobs.get(job_id)

    def update_job_progress(self, job_id, progress, message=None):
        """Update the progress of a job."""
        from strava.models import Job, db
        
        try:
            # Update the job record in the database
            job = Job.query.get(job_id)
            if job and message:
                job.message = message
                db.session.commit()
                
            # Also update in-memory for backward compatibility
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]['progress'] = progress
                    if message:
                        self._jobs[job_id]['message'] = message
                    return True
            return False
        except Exception as e:
            print(f"❌ Error updating job progress: {str(e)}")
            # Fallback to in-memory only
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]['progress'] = progress
                    if message:
                        self._jobs[job_id]['message'] = message
                    return True
                return False

    def get_api_usage(self):
        """Get current API usage statistics.
        
        Returns:
            Dictionary with short_term and daily usage stats
        """
        with self._lock:
            return {
                'short_term': dict(self._api_usage['short_term']),
                'daily': dict(self._api_usage['daily'])
            }

    def _parse_rate_limit_header(self, header):
        """Parse rate limit header into used/limit values."""
        try:
            if not header or not isinstance(header, str):
                return None
            parts = header.split(",")
            if len(parts) != 2:
                return None
            return [int(part) for part in parts]
        except (ValueError, TypeError):
            return None

    def fetch_activity_stream(self, activity_id):
        """Fetch activity stream data from Strava."""
        token = self.get_access_token()
        if not token:
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        max_retries = 3
        retry_delay = 2
        max_token_refresh_attempts = 3
        token_refresh_attempts = 0
        
        for attempt in range(max_retries):
            try:
                print(f"Fetching stream data for activity {activity_id}...")
                response = requests.get(
                    f"{STRAVA_API_URL}/{activity_id}/streams",
                    headers=headers,
                    params={"keys": "time,watts,velocity_smooth,heartrate,cadence,altitude,distance"}
                )
                
                if response.status_code == 401:
                    if token_refresh_attempts >= max_token_refresh_attempts:
                        print("❌ Maximum token refresh attempts reached")
                        return []
                    print("❌ Unauthorized Activities access - refreshing token")
                    token = self.get_access_token(force_refresh=True)  # Force a refresh regardless of expiration
                    if not token:
                        return []
                    headers["Authorization"] = f"Bearer {token}"
                    token_refresh_attempts += 1
                    continue
                
                # Check rate limits
                if not self.check_rate_limits(response.headers):
                    continue
                    
                response.raise_for_status()
                
                # Parse and validate stream data
                stream_data = response.json()
                
                # Handle list format streams (this is actually the standard format)
                if isinstance(stream_data, list):
                    print(f"Converting list format streams for activity {activity_id}")
                    converted_data = {}
                    
                    # Check if we have power data in the streams
                    has_power = False
                    
                    for stream in stream_data:
                        if isinstance(stream, dict) and 'type' in stream and 'data' in stream:
                            # Filter out None values from the data array before storing
                            if stream['data'] and isinstance(stream['data'], list):
                                # Replace None values with zeros
                                valid_data = [value if value is not None else 0 for value in stream['data']]
                                converted_data[stream['type']] = valid_data
                                
                                if stream['type'] == 'watts' and valid_data and len(valid_data) > 0:
                                    has_power = True
                                    # Calculate average only on non-None values
                                    data_sum = sum(valid_data)
                                    data_len = len(valid_data)
                                    avg_power = data_sum / data_len if data_len > 0 else 0
                                    print(f"✅ Found power data: {len(valid_data)} points, avg={avg_power:.1f}W")
                            else:
                                # Handle empty data array
                                converted_data[stream['type']] = []
                    
                    # Make sure we have all required data
                    if has_power and 'time' in converted_data and 'watts' in converted_data:
                        return converted_data
                    else:
                        if 'time' not in converted_data:
                            print("⚠️ Missing time data in stream")
                        if 'watts' not in converted_data:
                            print("⚠️ Missing power data in stream")
                        elif not has_power:
                            print("⚠️ Power data array is empty or contains only zeros")
                        return None
                else:
                    print(f"⚠️ Unexpected stream data format for activity {activity_id}")
                    return None
                
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 429:
                        print(f"❌ Stream API Error (attempt {attempt + 1}/{max_retries}): Too Many Requests")
                        # Extract rate limit reset time from headers if available
                        try:
                            reset_time = int(e.response.headers.get("X-RateLimit-Reset", retry_delay))
                            print(f"Waiting for {reset_time} seconds before retrying...")
                            time.sleep(reset_time)
                        except (ValueError, TypeError, AttributeError):
                            # If we can't get the reset time, use exponential backoff
                            print(f"Waiting for {retry_delay} seconds before retrying...")
                            time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    elif e.response.status_code == 404:
                        # Activity not found - no need to retry
                        print(f"❌ Activity {activity_id} not found (404)")
                        return None
                    else:
                        print(f"❌ Stream API Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            return None
                else:
                    print(f"❌ Stream API Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        return None
            except Exception as e:
                print(f"❌ Unexpected error in fetch_activity_stream: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        return None  # Return None if all attempts fail
