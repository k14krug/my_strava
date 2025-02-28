#!/usr/bin/env python3

import os
import time
import requests
from dotenv import load_dotenv

# -------------------------------------------------------------------------
#  LOAD ENVIRONMENT VARIABLES
#  Make sure you have STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN
#  in your .env file or environment, e.g.
#  STRAVA_CLIENT_ID=12345
#  STRAVA_CLIENT_SECRET=ABCDEF
#  STRAVA_REFRESH_TOKEN=YourRefreshToken
# -------------------------------------------------------------------------
load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# We'll store token info in module-level globals for simplicity:
ACCESS_TOKEN = None
EXPIRES_AT = 0


def refresh_access_token_if_needed():
    """
    Refresh the Strava access token only if the current token is missing or expired.
    Updates ACCESS_TOKEN, EXPIRES_AT, and (optionally) REFRESH_TOKEN if Strava
    returns a new one.
    """
    global ACCESS_TOKEN, EXPIRES_AT, REFRESH_TOKEN

    # If we have a token and it's not expired, no need to refresh
    if ACCESS_TOKEN and time.time() < EXPIRES_AT:
        return ACCESS_TOKEN

    print("🔑 [Token] Token missing or expired. Refreshing...")

    try:
        resp = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
    except requests.RequestException as e:
        print(f"❌ [Token] Error connecting to Strava: {e}")
        return None

    if resp.status_code == 429:
        print("❌ [Token] Rate-limited (429) when refreshing token.")
        print_rate_limit_headers(resp.headers)
        return None

    # Raise for other 4xx/5xx so we see what happened
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ [Token] HTTP Error: {e}")
        print("Response content:", resp.text)
        return None

    # Parse the JSON
    token_data = resp.json()
    ACCESS_TOKEN = token_data.get("access_token")
    REFRESH_TOKEN = token_data.get("refresh_token")  # Strava might issue a new one
    EXPIRES_AT = token_data.get("expires_at", 0)

    print("✅ [Token] New token acquired.")
    return ACCESS_TOKEN


def print_rate_limit_headers(headers):
    """
    Utility to parse and print Strava's rate-limit headers if present.
    Strava typically includes:
      X-RateLimit-Limit: "shortWindow,daily"
      X-RateLimit-Usage: "shortWindowUsed,dailyUsed"
      X-RateLimit-Reset: secondsUntilReset
    """
    limit_str = headers.get("X-RateLimit-Limit", "N/A")
    usage_str = headers.get("X-RateLimit-Usage", "N/A")
    reset_str = headers.get("X-RateLimit-Reset", "N/A")

    print("📊 [Rate Limits]")
    print(f"  X-RateLimit-Limit: {limit_str}")
    print(f"  X-RateLimit-Usage: {usage_str}")
    print(f"  X-RateLimit-Reset: {reset_str}")


def test_strava_call():
    """
    Make one GET request to /activities (or any endpoint you choose).
    Print out the rate-limit headers and handle 429 if it occurs.
    """
    token = refresh_access_token_if_needed()
    if not token:
        print("❌ [API] No valid access token; cannot continue.")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    endpoint = "https://www.strava.com/api/v3/athlete"  # or /activities, etc.
    params = {"per_page": 1}

    print(f"📡 [API] Requesting {endpoint} with {params}")
    try:
        resp = requests.get(endpoint, headers=headers, params=params)
    except requests.RequestException as e:
        print(f"❌ [API] Error during request: {e}")
        return

    if resp.status_code == 429:
        print("❌ [API] Rate-limited (429) on API call.")
        print_rate_limit_headers(resp.headers)
        return
    elif not resp.ok:
        print(f"❌ [API] HTTP Error: {resp.status_code}")
        print("Response content:", resp.text)
        return
    else:
        print("✅ [API] Call succeeded.")
        # Print the first part of the response JSON for debugging
        try:
            data = resp.json()
            print("Response JSON snippet:", str(data)[:300], "...")
        except Exception:
            print("Response was not JSON:", resp.text)

    # Print out any rate-limit headers on success
    print_rate_limit_headers(resp.headers)


def main():
    print("🚀 [Debug] Starting Strava API debug test...")
    test_strava_call()
    print("✅ [Debug] Done.")


if __name__ == "__main__":
    main()
