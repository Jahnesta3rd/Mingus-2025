"""
Development configuration
"""

import os
from .base import Config

class DevelopmentConfig(Config):
    """Development configuration class"""
    
    DEBUG = True
    TESTING = False
    
    # Database settings for development
    DATABASE_URL = "sqlite:///instance/mingus.db"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CREATE_TABLES = True
    
    # CORS settings for development
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5002',
        'http://127.0.0.1:5002',
        'https://wiemjrvxlqkpbsukdqnb.supabase.co',
        'https://accounts.google.com'  # Add Google OAuth domain
    ]
    
    # Session settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # More permissive for OAuth
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Logging settings for development
    LOG_LEVEL = 'DEBUG'
    
    # Security settings for development
    WTF_CSRF_ENABLED = False  # Disable CSRF for API testing
    
    # Feature flags for development
    ENABLE_ONBOARDING = True
    ENABLE_USER_PROFILES = True
    BYPASS_AUTH = True  # Enable auth bypass for development
    
    # Development-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    
    # Supabase settings (keep existing for compatibility)
    SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8"
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1MDE5NywiZXhwIjoyMDYyMzI2MTk3fQ.pzTybRahJYGjD_y2OrLnhpAX5xq-ylJbd7r4K5xNGCM"
    SUPABASE_JWT_SECRET = "counJW9WSebZaLdlxu2e8+OBsrvgXNYcgsHravbNQrQKy6i/uyfFAL0Ne9QozcrosrXuzbudxltljMCWKpB9hg=="
    
    # Flask-Mail example (optional)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Any other app-specific config
"""
Development configuration
"""

from .base import Config

class DevelopmentConfig(Config):
    """Development configuration class"""
    
    DEBUG = True
    TESTING = False
    
    # Database settings for development
    DATABASE_URL = "sqlite:///instance/mingus.db"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CREATE_TABLES = True
    
    # CORS settings for development
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5002',
        'http://127.0.0.1:5002',
        'https://wiemjrvxlqkpbsukdqnb.supabase.co',
        'https://accounts.google.com'  # Add Google OAuth domain
    ]
    
    # Session settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # More permissive for OAuth
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Logging settings for development
    LOG_LEVEL = 'DEBUG'
    
    # Security settings for development
    WTF_CSRF_ENABLED = False  # Disable CSRF for API testing
    
    # Feature flags for development
    ENABLE_ONBOARDING = True
    ENABLE_USER_PROFILES = True
    BYPASS_AUTH = True  # Enable auth bypass for development
    
    # Development-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    
    # Supabase settings (keep existing for compatibility)
    SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8"
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1MDE5NywiZXhwIjoyMDYyMzI2MTk3fQ.pzTybRahJYGjD_y2OrLnhpAX5xq-ylJbd7r4K5xNGCM"
    SUPABASE_JWT_SECRET = "counJW9WSebZaLdlxu2e8+OBsrvgXNYcgsHravbNQrQKy6i/uyfFAL0Ne9QozcrosrXuzbudxltljMCWKpB9hg=="
    
    # Flask-Mail example (optional)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Any other app-specific config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key') 