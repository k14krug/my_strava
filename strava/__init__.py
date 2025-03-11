# strava_app/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config

# Load environment variables from .env (if available)
load_dotenv()

# Import the config dictionary from config.py
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Redirect if user isn't logged in

@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by ID."""
    from .models import User  # Avoid circular import issues
    return User.query.get(int(user_id))

def create_app():
    """Factory function to create the Flask app with the correct configuration."""
    app = Flask(__name__)

    # Determine the current environment (default to development)
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])

    # Call init_app() if defined (only applies to production)
    if hasattr(config[env], 'init_app'):
        config[env].init_app(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    # Register Blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .sync.routes import sync_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(sync_bp, url_prefix='/sync')

    with app.app_context():
        db.create_all()

    return app
