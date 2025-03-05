# wsgi.py
from strava import create_app

app = create_app()  # Unpack and use only the Flask app