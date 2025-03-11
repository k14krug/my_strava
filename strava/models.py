# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db
#db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the provided password."""
        return check_password_hash(self.password_hash, password)

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.BigInteger, unique=True, nullable=False)  # Strava activity ID
    name = db.Column(db.String(200))
    distance = db.Column(db.Float)  
    moving_time = db.Column(db.Integer)  
    elapsed_time = db.Column(db.Integer) 
    total_elevation_gain = db.Column(db.Float) 
    average_speed = db.Column(db.Float) 
    max_speed = db.Column(db.Float)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Power metrics
    ftp = db.Column(db.Float)  # Functional Threshold Power at time of activity
    best_10m_power = db.Column(db.Integer)
    best_20m_power = db.Column(db.Integer)
    best_30m_power = db.Column(db.Integer)
    best_45m_power = db.Column(db.Integer)
    best_60m_power = db.Column(db.Integer)
    max_power = db.Column(db.Integer)
    normalized_power = db.Column(db.Integer)
    intensity_factor = db.Column(db.Float)
    variability_index = db.Column(db.Float)

    # Relationship
    gps_points = db.relationship('GPSPoint', backref='activity', lazy=True)
    segment_efforts = db.relationship('SegmentEffort', backref='activity', lazy=True)

class GPSPoint(db.Model):
    __tablename__ = 'gps_points'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)  # optional

class Segment(db.Model):
    __tablename__ = 'segments'
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.BigInteger, unique=True, nullable=False)  # Strava segment ID
    name = db.Column(db.String(200))
    activity_type = db.Column(db.String(50))
    distance = db.Column(db.Float)  # store in meters or miles
    average_grade = db.Column(db.Float)
    maximum_grade = db.Column(db.Float)
    elevation_high = db.Column(db.Float)
    elevation_low = db.Column(db.Float)
    start_latlng = db.Column(db.String(100))
    end_latlng = db.Column(db.String(100))
    climb_category = db.Column(db.Integer)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    private = db.Column(db.Boolean)
    hazardous = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    favorite = db.Column(db.Boolean)

class SegmentEffort(db.Model):
    __tablename__ = 'segment_efforts'
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    elapsed_time = db.Column(db.Integer)
    moving_time = db.Column(db.Integer)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    distance = db.Column(db.Float)
    average_watts = db.Column(db.Float)
    average_heartrate = db.Column(db.Float)
    max_heartrate = db.Column(db.Float)
    kom_rank = db.Column(db.Integer)
    pr_rank = db.Column(db.Integer)
    segment = db.relationship('Segment', backref='efforts')

class YearlyDistanceGoal(db.Model):
    __tablename__ = 'yearly_distance_goals'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    distance_goal = db.Column(db.Float, nullable=False)  # store in miles or kilometers
    # Optionally keep track of date added or user ID if multiple users

class FTPHistory(db.Model):
    __tablename__ = "ftp_history"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    ftp = db.Column(db.Integer, nullable=False)

class TrainingLoad(db.Model):
    __tablename__ = "training_load"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    tss = db.Column(db.Float, nullable=False)  # Training Stress Score
    ctl = db.Column(db.Float, nullable=False)  # Chronic Training Load
    atl = db.Column(db.Float, nullable=False)  # Acute Training Load
    tsb = db.Column(db.Float, nullable=False)  # Training Stress Balance (Form)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    # Power metrics
    avg_normalized_power = db.Column(db.Integer)
    max_daily_power = db.Column(db.Integer)
    power_balance = db.Column(db.Float)
    power_tss = db.Column(db.Float)
