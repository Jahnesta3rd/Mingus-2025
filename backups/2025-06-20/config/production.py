"""
Production configuration
"""

from .base import Config
import os

class ProductionConfig(Config):
    """Production configuration class"""
    
    DEBUG = False
    TESTING = False
    
    # Database settings for production
    DATABASE_URL = os.environ.get('DATABASE_URL')  # Must be set in production
    CREATE_TABLES = False  # Don't auto-create tables in production
    
    # CORS settings for production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Session settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Security settings for production
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Logging settings for production
    LOG_LEVEL = 'INFO'
    
    # Feature flags for production
    ENABLE_ONBOARDING = True
    ENABLE_USER_PROFILES = True
    BYPASS_AUTH = False  # Disable auth bypass in production
    
    # Production-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    # Rate limiting for production
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')
    
    # Cache settings for production
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')
    
    # Email settings for production
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') 