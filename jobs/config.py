"""Configuration settings for Strava synchronization."""

import os
from flask import Flask
from dotenv import load_dotenv
from strava.models import db

# Load environment variables
load_dotenv(override=True)

# Strava API Configuration
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_API_URL = "https://www.strava.com/api/v3/activities"

# Flask App Setup
def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "mariadb+mariadbconnector://strava_user:admin14@localhost/strava_app_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app