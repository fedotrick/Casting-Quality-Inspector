"""Configuration management for the quality control system."""

import os
import secrets
from pathlib import Path
from typing import List

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use existing environment variables
    pass


class Config:
    """Base configuration."""
    
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR', './sessions')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'qc_'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5004,http://127.0.0.1:5004').split(',')
    CORS_ALLOW_CREDENTIALS = True
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOWED_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    
    # Database paths
    DATABASE_PATH = Path(os.getenv('DATABASE_PATH', 'data/quality_control.db'))
    FOUNDRY_DB_PATH = Path(os.getenv('FOUNDRY_DB_PATH', r'C:\Users\1\Telegram\MetalFusionX\foundry.db'))
    ROUTE_CARDS_DB_PATH = Path(os.getenv('ROUTE_CARDS_DB_PATH', r'C:\Users\1\Telegram\FoamFusionLab\data\маршрутные_карты.db'))
    
    # Admin credentials (from environment)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Security settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16 MB max file upload
    
    # Application settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5004))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv('LOG_FILE', 'logs/application.log'))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration."""
        warnings = []
        
        # Warn if using default secret key
        if not os.getenv('SECRET_KEY'):
            warnings.append("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY in environment for production!")
        
        # Warn if SESSION_COOKIE_SECURE is False
        if not cls.SESSION_COOKIE_SECURE and not cls.DEBUG:
            warnings.append("WARNING: SESSION_COOKIE_SECURE is False. Enable for production with HTTPS!")
        
        # Warn if default admin credentials exist
        if not cls.ADMIN_USERNAME or not cls.ADMIN_PASSWORD:
            warnings.append("WARNING: ADMIN_USERNAME and ADMIN_PASSWORD not set. Default admin will be created!")
        
        return warnings


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_PATH = Path(':memory:')


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
