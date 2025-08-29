# Test Edit: Confirming file modification permissions for config directory.
"""
Base configuration for Flask application
"""

import os
from datetime import timedelta
from .secure_config import get_secure_config, SecurityConfig, SecurityLevel

class Config:
    """Base configuration class using secure configuration management"""
    
    def __init__(self):
        """Initialize configuration with secure config manager"""
        self.secure_config = get_secure_config()
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from secure config manager"""
        self.SECRET_KEY = self.secure_config.get('SECRET_KEY')
        self.DEBUG = self.secure_config.get('DEBUG', 'false').lower() == 'true'
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(self.secure_config.get('DB_POOL_SIZE', '20')),
            'pool_recycle': int(self.secure_config.get('DB_POOL_RECYCLE', '3600')),
            'pool_pre_ping': True,
            'max_overflow': int(self.secure_config.get('DB_MAX_OVERFLOW', '30'))
        }
        
        # Session configuration
        self.SESSION_COOKIE_SECURE = self.secure_config.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = self.secure_config.get('SESSION_COOKIE_SAMESITE', 'Strict')
        self.PERMANENT_SESSION_LIFETIME = timedelta(hours=int(self.secure_config.get('SESSION_LIFETIME_HOURS', '24')))
        
        # CORS configuration
        cors_origins = self.secure_config.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
        
        # Logging configuration
        self.LOG_LEVEL = self.secure_config.get('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = self.secure_config.get('LOG_FORMAT', '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}')
        self.LOG_ROTATION = self.secure_config.get('LOG_ROTATION', '1 day')
        self.LOG_RETENTION = self.secure_config.get('LOG_RETENTION', '30 days')
        self.LOG_FILE = self.secure_config.get('LOG_FILE', 'logs/mingus.log')
        
        # Email configuration
        self.MAIL_SERVER = self.secure_config.get('MAIL_SERVER', 'smtp.gmail.com')
        self.MAIL_PORT = int(self.secure_config.get('MAIL_PORT', '587'))
        self.MAIL_USE_TLS = self.secure_config.get('MAIL_USE_TLS', 'true').lower() == 'true'
        self.MAIL_USERNAME = self.secure_config.get('MAIL_USERNAME')
        self.MAIL_PASSWORD = self.secure_config.get('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = self.secure_config.get('MAIL_DEFAULT_SENDER', 'noreply@mingusapp.com')
        
        # Redis configuration
        self.REDIS_URL = self.secure_config.get('REDIS_URL', 'redis://localhost:6379/0')
        
        # Rate limiting configuration
        self.RATELIMIT_ENABLED = self.secure_config.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
        self.RATELIMIT_STORAGE_URL = self.secure_config.get('RATELIMIT_STORAGE_URL', 'memory://')
        self.RATELIMIT_DEFAULT = self.secure_config.get('RATELIMIT_DEFAULT', '100 per minute')
        self.RATELIMIT_STRATEGY = self.secure_config.get('RATELIMIT_STRATEGY', 'fixed-window')
        
        # API configuration
        self.API_TITLE = self.secure_config.get('API_TITLE', 'Mingus Personal Finance API')
        self.API_VERSION = self.secure_config.get('API_VERSION', 'v1')
        self.API_DESCRIPTION = self.secure_config.get('API_DESCRIPTION', 'API for Mingus personal finance application')
        
        # Security configuration
        self.SECURE_SSL_REDIRECT = self.secure_config.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
        self.SECURE_HSTS_SECONDS = int(self.secure_config.get('SECURE_HSTS_SECONDS', '31536000'))
        self.SECURE_HSTS_INCLUDE_SUBDOMAINS = self.secure_config.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'true').lower() == 'true'
        self.SECURE_HSTS_PRELOAD = self.secure_config.get('SECURE_HSTS_PRELOAD', 'true').lower() == 'true'
        self.SECURE_CONTENT_TYPE_NOSNIFF = self.secure_config.get('SECURE_CONTENT_TYPE_NOSNIFF', 'true').lower() == 'true'
        self.SECURE_BROWSER_XSS_FILTER = self.secure_config.get('SECURE_BROWSER_XSS_FILTER', 'true').lower() == 'true'
        self.SECURE_FRAME_DENY = self.secure_config.get('SECURE_FRAME_DENY', 'true').lower() == 'true'
        
        # Encryption configuration
        self.FIELD_ENCRYPTION_KEY = self.secure_config.get('FIELD_ENCRYPTION_KEY')
        self.ENCRYPTION_ALGORITHM = self.secure_config.get('ENCRYPTION_ALGORITHM', 'AES-256-GCM')
        
        # Audit logging configuration
        self.AUDIT_LOG_ENABLED = self.secure_config.get('AUDIT_LOG_ENABLED', 'true').lower() == 'true'
        self.AUDIT_LOG_RETENTION_DAYS = int(self.secure_config.get('AUDIT_LOG_RETENTION_DAYS', '2555'))  # 7 years
        
        # Feature flags
        self.ENABLE_ONBOARDING = self.secure_config.get('ENABLE_ONBOARDING', 'true').lower() == 'true'
        self.ENABLE_USER_PROFILES = self.secure_config.get('ENABLE_USER_PROFILES', 'true').lower() == 'true'
        self.ENABLE_ENCRYPTION = self.secure_config.get('ENABLE_ENCRYPTION', 'true').lower() == 'true'
        self.ENABLE_AUDIT_LOGGING = self.secure_config.get('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true'# Port configuration
        self.PORT = int(self.secure_config.get('PORT', '5002'))
        
        # Supabase configuration
        self.SUPABASE_URL = self.secure_config.get('SUPABASE_URL')
        self.SUPABASE_KEY = self.secure_config.get('SUPABASE_KEY')
        self.SUPABASE_SERVICE_ROLE_KEY = self.secure_config.get('SUPABASE_SERVICE_ROLE_KEY')
        self.SUPABASE_JWT_SECRET = self.secure_config.get('SUPABASE_JWT_SECRET')
        
        # Stripe configuration
        self.STRIPE_ENVIRONMENT = self.secure_config.get('STRIPE_ENVIRONMENT', 'test')
        self.STRIPE_TEST_SECRET_KEY = self.secure_config.get('STRIPE_TEST_SECRET_KEY')
        self.STRIPE_TEST_PUBLISHABLE_KEY = self.secure_config.get('STRIPE_TEST_PUBLISHABLE_KEY')
        self.STRIPE_LIVE_SECRET_KEY = self.secure_config.get('STRIPE_LIVE_SECRET_KEY')
        self.STRIPE_LIVE_PUBLISHABLE_KEY = self.secure_config.get('STRIPE_LIVE_PUBLISHABLE_KEY')
        
        # Plaid configuration
        self.PLAID_ENVIRONMENT = self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox')
        self.PLAID_SANDBOX_CLIENT_ID = self.secure_config.get('PLAID_SANDBOX_CLIENT_ID')
        self.PLAID_SANDBOX_SECRET = self.secure_config.get('PLAID_SANDBOX_SECRET')
        self.PLAID_PRODUCTION_CLIENT_ID = self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID')
        self.PLAID_PRODUCTION_SECRET = self.secure_config.get('PLAID_PRODUCTION_SECRET')
        
        # Email provider configuration
        self.EMAIL_PROVIDER = self.secure_config.get('EMAIL_PROVIDER', 'resend')
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.RESEND_FROM_NAME = self.secure_config.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        
        # SMS configuration
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER')
        
        # Celery configuration
        self.CELERY_BROKER_URL = self.secure_config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.CELERY_RESULT_BACKEND = self.secure_config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        
        # Cache configuration
        self.CACHE_TYPE = self.secure_config.get('CACHE_TYPE', 'simple')
        self.CACHE_DEFAULT_TIMEOUT = int(self.secure_config.get('CACHE_DEFAULT_TIMEOUT', '300'))
        
        # File upload configuration
        self.MAX_CONTENT_LENGTH = int(self.secure_config.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
        self.UPLOAD_FOLDER = self.secure_config.get('UPLOAD_FOLDER', 'uploads')
        
        # Static files configuration
        self.STATIC_FOLDER = self.secure_config.get('STATIC_FOLDER', 'static')
        self.STATIC_URL_PATH = self.secure_config.get('STATIC_URL_PATH', '/static')
        
        # Template configuration
        self.TEMPLATE_FOLDER = self.secure_config.get('TEMPLATE_FOLDER', 'templates')
        
        # Performance monitoring
        self.ENABLE_PERFORMANCE_MONITORING = self.secure_config.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        self.ENABLE_ERROR_TRACKING = self.secure_config.get('ENABLE_ERROR_TRACKING', 'true').lower() == 'true'
        self.ENABLE_USAGE_ANALYTICS = self.secure_config.get('ENABLE_USAGE_ANALYTICS', 'true').lower() == 'true' 