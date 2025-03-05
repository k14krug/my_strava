import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:password@localhost/strava'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# filepath: /home/kkrug/projects/strava/config.py
import os

class DevelopmentConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mariadb+mariadbconnector://strava_user:admin14@localhost/strava_app_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def init_app(cls, app):
        # Actually read env variables here
        cls.SECRET_KEY = os.environ.get('SECRET_KEY')
        cls.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
        if not cls.SECRET_KEY:
            raise ValueError("No SECRET_KEY set for production")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("No DATABASE_URL set for production")
