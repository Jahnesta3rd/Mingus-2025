"""
Production Configuration for MINGUS Application
Optimized for production with security, performance, and monitoring
"""

import os
import logging
from datetime import timedelta
from config.base import Config

class ProductionConfig(Config):
    """Production configuration with security and performance optimizations"""
    
    # =====================================================
    # BASIC FLASK CONFIGURATION
    # =====================================================
    
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required for production")
    
    # =====================================================
    # DATABASE CONFIGURATION
    # =====================================================
    
    # Database settings for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required for production")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'echo': False,
        'echo_pool': False,
        'connect_args': {
            'sslmode': 'require',
            'application_name': 'mingus_production',
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', 10)),
            'options': '-c statement_timeout=300000 -c idle_in_transaction_session_timeout=300000'
        }
    }
    
    # =====================================================
    # REDIS AND CELERY CONFIGURATION
    # =====================================================
    
    # Redis settings for production
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    
    # Celery settings for production
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
    
    if not CELERY_BROKER_URL:
        raise ValueError("CELERY_BROKER_URL environment variable is required for production")
    
    # Production-specific Celery settings
    CELERY_ALWAYS_EAGER = False
    CELERY_WORKER_DISABLE_RATE_LIMITS = False
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = False
    
    # =====================================================
    # MOCK SERVICES CONFIGURATION
    # =====================================================
    
    # Mock services disabled in production
    MOCK_TWILIO = False
    MOCK_RESEND = False
    MOCK_SUPABASE = False
    
    # =====================================================
    # RATE LIMITING CONFIGURATION
    # =====================================================
    
    # Rate limiting - strict for production
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100/minute')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    
    # Specific rate limits for production
    RATELIMIT_API = os.environ.get('RATELIMIT_API', '60/minute')
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH', '10/minute')
    RATELIMIT_SMS = os.environ.get('RATELIMIT_SMS', '5/minute')
    RATELIMIT_EMAIL = os.environ.get('RATELIMIT_EMAIL', '20/minute')
    RATELIMIT_UPLOAD = os.environ.get('RATELIMIT_UPLOAD', '5/minute')
    
    # =====================================================
    # LOGGING CONFIGURATION
    # =====================================================
    
    # Logging settings for production
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/mingus_production.log')
    LOG_MAX_SIZE = int(os.environ.get('LOG_MAX_SIZE', 50 * 1024 * 1024))  # 50MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))
    
    # Disable SQL query logging in production
    LOG_SQL_QUERIES = False
    
    # Production log files
    CELERY_LOG_FILE = os.environ.get('CELERY_LOG_FILE', 'logs/celery_production.log')
    API_LOG_FILE = os.environ.get('API_LOG_FILE', 'logs/api_production.log')
    AUTH_LOG_FILE = os.environ.get('AUTH_LOG_FILE', 'logs/auth_production.log')
    ERROR_LOG_FILE = os.environ.get('ERROR_LOG_FILE', 'logs/errors_production.log')
    
    # =====================================================
    # DEBUG AND DEVELOPMENT TOOLS
    # =====================================================
    
    # Debug tools disabled in production
    DEBUG_TB_ENABLED = False
    ENABLE_DEBUG_TOOLBAR = False
    ENABLE_PROFILER = False
    ENABLE_SQL_LOGGING = False
    ENABLE_REQUEST_LOGGING = False
    ENABLE_RESPONSE_LOGGING = False
    ENABLE_PERFORMANCE_MONITORING = True
    
    # =====================================================
    # TESTING HELPERS
    # =====================================================
    
    # Testing helpers disabled in production
    BYPASS_AUTH = False
    SKIP_EMAIL_VERIFICATION = False
    SKIP_PHONE_VERIFICATION = False
    ENABLE_TEST_DATA = False
    
    # =====================================================
    # SECURITY SETTINGS (STRICT FOR PRODUCTION)
    # =====================================================
    
    # Security settings - strict for production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    
    # CORS settings for production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Security headers
    SECURITY_HEADERS = {
        'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains; preload',
        'X_CONTENT_TYPE_OPTIONS': 'nosniff',
        'X_FRAME_OPTIONS': 'DENY',
        'X_XSS_PROTECTION': '1; mode=block',
        'REFERRER_POLICY': 'strict-origin-when-cross-origin',
        'CONTENT_SECURITY_POLICY': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';"
    }
    
    # =====================================================
    # EMAIL CONFIGURATION
    # =====================================================
    
    # Email settings for production
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Enable email sending in production
    MAIL_SUPPRESS_SEND = False
    
    # =====================================================
    # SMS CONFIGURATION
    # =====================================================
    
    # Twilio settings for production
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        raise ValueError("Twilio credentials are required for production")
    
    # Disable mock SMS in production
    TWILIO_MOCK_SMS = False
    
    # =====================================================
    # RESEND EMAIL CONFIGURATION
    # =====================================================
    
    # Resend settings for production
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY is required for production")
    
    # Disable mock emails in production
    RESEND_MOCK_EMAILS = False
    
    # =====================================================
    # SUPABASE CONFIGURATION
    # =====================================================
    
    # Supabase settings for production
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        raise ValueError("Supabase credentials are required for production")
    
    # Disable mock Supabase in production
    SUPABASE_MOCK_MODE = False
    
    # =====================================================
    # CACHE CONFIGURATION
    # =====================================================
    
    # Cache settings for production
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/2')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'mingus_prod')
    
    # =====================================================
    # SESSION CONFIGURATION
    # =====================================================
    
    # Session settings for production
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'redis')
    SESSION_REDIS = os.environ.get('SESSION_REDIS', 'redis://localhost:6379/3')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # =====================================================
    # FILE UPLOAD CONFIGURATION
    # =====================================================
    
    # File upload settings for production
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    
    # =====================================================
    # FEATURE FLAGS
    # =====================================================
    
    # Feature flags for production
    FEATURE_FLAGS = {
        'enable_analytics': os.environ.get('ENABLE_ANALYTICS', 'true').lower() == 'true',
        'enable_notifications': os.environ.get('ENABLE_NOTIFICATIONS', 'true').lower() == 'true',
        'enable_social_features': os.environ.get('ENABLE_SOCIAL_FEATURES', 'false').lower() == 'true',
        'enable_premium_features': os.environ.get('ENABLE_PREMIUM_FEATURES', 'true').lower() == 'true',
        'enable_beta_features': os.environ.get('ENABLE_BETA_FEATURES', 'false').lower() == 'true',
    }
    
    # =====================================================
    # MONITORING AND METRICS
    # =====================================================
    
    # Monitoring settings for production
    ENABLE_METRICS = True
    STATSD_HOST = os.environ.get('STATSD_HOST', 'localhost')
    STATSD_PORT = int(os.environ.get('STATSD_PORT', 8125))
    STATSD_PREFIX = os.environ.get('STATSD_PREFIX', 'mingus.prod')
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING = True
    PERFORMANCE_MONITORING_INTERVAL = int(os.environ.get('PERFORMANCE_MONITORING_INTERVAL', 60))
    
    # =====================================================
    # APPLICATION INITIALIZATION
    # =====================================================
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with production-specific settings"""
        super().init_app(app)
        
        # Configure logging
        cls._configure_logging(app)
        
        # Configure security
        cls._configure_security(app)
        
        # Configure rate limiting
        cls._configure_rate_limiting(app)
        
        # Configure monitoring
        cls._configure_monitoring(app)
        
        # Validate production requirements
        cls._validate_production_requirements(app)
        
        log = logging.getLogger(__name__)
        log.info("Production configuration initialized")
    
    @classmethod
    def _configure_logging(cls, app):
        """Configure production logging"""
        import logging.handlers
        import os
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # File handler for production logs
        file_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(cls.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log handler
        error_handler = logging.handlers.RotatingFileHandler(
            cls.ERROR_LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # API request logging
        api_logger = logging.getLogger('api')
        api_file_handler = logging.handlers.RotatingFileHandler(
            cls.API_LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        api_file_handler.setFormatter(file_formatter)
        api_logger.addHandler(api_file_handler)
        
        # Authentication logging
        auth_logger = logging.getLogger('auth')
        auth_file_handler = logging.handlers.RotatingFileHandler(
            cls.AUTH_LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        auth_file_handler.setFormatter(file_formatter)
        auth_logger.addHandler(auth_file_handler)
    
    @classmethod
    def _configure_security(cls, app):
        """Configure security settings for production"""
        # Configure security headers
        if 'TALISMAN' in app.extensions:
            app.extensions['TALISMAN'].force_https = True
            app.extensions['TALISMAN'].strict_transport_security = True
            app.extensions['TALISMAN'].content_security_policy = cls.SECURITY_HEADERS['CONTENT_SECURITY_POLICY']
        
        app.logger.info("Security settings configured for production")
    
    @classmethod
    def _configure_rate_limiting(cls, app):
        """Configure rate limiting for production"""
        app.logger.info(f"Rate limiting enabled with default: {cls.RATELIMIT_DEFAULT}")
    
    @classmethod
    def _configure_monitoring(cls, app):
        """Configure monitoring for production"""
        if cls.ENABLE_METRICS:
            app.logger.info("Metrics collection enabled")
        
        if cls.ENABLE_PERFORMANCE_MONITORING:
            app.logger.info("Performance monitoring enabled")
    
    @classmethod
    def _validate_production_requirements(cls, app):
        """Validate that all required production settings are present"""
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'CELERY_BROKER_URL',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'RESEND_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables for production: {', '.join(missing_vars)}")
        
        app.logger.info("All production requirements validated") 