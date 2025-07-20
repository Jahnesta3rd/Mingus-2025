# Test Edit: Confirming file modification permissions for config directory.
"""
Base configuration for Flask application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mingus')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))
    CREATE_TABLES = True
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'https://localhost:3000',
        'https://127.0.0.1:3000'
    ]
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_MAX_AGE = 3600
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://wiemjrvxlqkpbsukdqnb.supabase.co; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        'Permissions-Policy': (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=(), '
            'ambient-light-sensor=(), '
            'autoplay=(), '
            'encrypted-media=(), '
            'picture-in-picture=()'
        ),
        
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}'
    LOG_ROTATION = '1 day'
    LOG_RETENTION = '30 days'
    
    # Supabase settings (for existing functionality)
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://wiemjrvxlqkpbsukdqnb.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # API settings
    API_TITLE = 'Mingus Personal Finance API'
    API_VERSION = 'v1'
    API_DESCRIPTION = 'API for Mingus personal finance application'
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per minute'
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Input validation limits
    FINANCIAL_VALIDATION_LIMITS = {
        'max_income_per_source': 1000000,  # $1M per income source
        'max_expense_per_item': 100000,    # $100K per expense
        'max_monthly_income': 1000000,     # $1M monthly
        'max_monthly_expenses': 500000,    # $500K monthly
        'max_savings_goal': 10000000,      # $10M savings goal
        'max_debt_amount': 5000000,        # $5M debt
        'min_amount': 0,                   # Minimum amount
        'max_frequency_options': ['weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually']
    }
    
    # =====================================================
    # ENCRYPTION & SECURITY KEYS
    # =====================================================
    
    # Field-level encryption key (32 bytes for AES-256)
    FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY') or (
        'django-insecure-8f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918'
    )
    
    # Django secret key for django-encrypted-model-fields compatibility
    DJANGO_SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or (
        'django-insecure-9e8d7c6b5a4930a9e8d7c6b5a4930a9e8d7c6b5a4930a9e8d7c6b5a4930a9'
    )
    
    # General encryption settings
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or FIELD_ENCRYPTION_KEY
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    
    # SSL/HTTPS settings
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_FRAME_DENY = True
    
    # Audit logging
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_RETENTION_DAYS = 90
    AUDIT_LOG_SENSITIVE_FIELDS = [
        'monthly_income', 'current_savings', 'current_debt', 
        'emergency_fund', 'savings_goal', 'debt_payoff_goal',
        'amount', 'balance', 'minimum_payment'
    ]
    
    # Feature flags
    ENABLE_ONBOARDING = True
    ENABLE_USER_PROFILES = True
    ENABLE_ENCRYPTION = True
    ENABLE_AUDIT_LOGGING = True
    BYPASS_AUTH = False
    
    # Application port
    PORT = int(os.environ.get('PORT', 5002)) 