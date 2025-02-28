# strava_app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, User
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Redirect if user isn't logged in

@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by ID."""
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    # You will want a proper secret key for session management
    app.config['SECRET_KEY'] = 'some-secret-key'
    
    # Database config (MariaDB)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://strava_user:admin14@localhost/strava_app_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from auth.routes import auth_bp
    from main.routes import main_bp
    from sync.routes import sync_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(sync_bp, url_prefix='/sync')

    with app.app_context():
        db.create_all()

    return app
