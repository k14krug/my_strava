import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Get tokens from .env
client_id = os.getenv("STRAVA_CLIENT_ID")
client_secret = os.getenv("STRAVA_CLIENT_SECRET")
refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
print(f"Using Client ID: {client_id}, Client Secret: {client_secret}, Refresh Token: {refresh_token}")

# Get a fresh access token
print("Getting new access token...")
response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
)

if response.status_code != 200:
    print(f"Error getting token: {response.status_code}")
    print(response.text)
    exit(1)

token_data = response.json()
access_token = token_data['access_token']
print(f"Access token obtained, expires in {token_data['expires_in']} seconds")

# Make a lightweight API call to check status
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "https://www.strava.com/api/v3/athlete",
    headers=headers
)

print(f"\nAPI Response Status: {response.status_code}")

# Check headers for rate limit info
print("\nRate Limit Headers:")
for key, value in response.headers.items():
    if "rate" in key.lower():
        print(f"  {key}: {value}")

# Try a streams API call to one activity
print("\nTrying a streams API call...")
# Get a single activity ID
activity_response = requests.get(
    "https://www.strava.com/api/v3/athlete/activities",
    headers=headers,
    params={"per_page": 1}
)

if activity_response.status_code == 200:
    activities = activity_response.json()
    if activities:
        activity_id = activities[0]["id"]
        print(f"Testing stream API with activity ID: {activity_id}")
        
        stream_response = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            headers=headers,
            params={"keys": "time,watts"}
        )
        
        print(f"Stream API response: {stream_response.status_code}")
        if stream_response.status_code != 200:
            print(stream_response.text)
        
        # Check headers for rate limit info
        print("\nStream API Rate Limit Headers:")
        for key, value in stream_response.headers.items():
            if "rate" in key.lower():
                print(f"  {key}: {value}")
    else:
        print("No activities found to test stream API")
else:
    print(f"Could not get activities: {activity_response.status_code}")