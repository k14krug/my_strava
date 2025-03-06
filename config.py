import os

class Config:
    """Base configuration shared across environments."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    DB_NAME = os.getenv('DB_NAME', 'x')  # Default to dev
    DB_USER = os.getenv('DB_USER', 'x')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'x')
    DB_HOST = os.getenv('DB_HOST', 'localhost')

    SQLALCHEMY_DATABASE_URI = f"mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False

    @classmethod
    def init_app(cls, app):
        """Ensure required environment variables are set for production."""
        if not os.getenv('SECRET_KEY'):
            raise ValueError("No SECRET_KEY set for production")
        if not os.getenv('DB_NAME'):
            raise ValueError("No DB_NAME set for production")

# Dictionary to easily load configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # Default to development
}
