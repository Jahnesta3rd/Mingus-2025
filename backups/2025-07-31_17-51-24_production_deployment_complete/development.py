"""
Development Configuration for MINGUS Application
Optimized for development with mock services, relaxed limits, and debug features
"""

import os
import logging
from datetime import timedelta
from config.base import Config

class DevelopmentConfig(Config):
    """Development configuration with debug features and mock services"""
    
    # =====================================================
    # BASIC FLASK CONFIGURATION
    # =====================================================
    
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # =====================================================
    # DATABASE CONFIGURATION
    # =====================================================
    
    # Database settings for development
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://mingus_user:mingus_password@localhost:5432/mingus_development'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'echo': os.environ.get('DB_ECHO', 'true').lower() == 'true',
        'echo_pool': os.environ.get('DB_ECHO_POOL', 'false').lower() == 'true',
    }
    
    # =====================================================
    # REDIS AND CELERY CONFIGURATION
    # =====================================================
    
    # Redis settings for development
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    
    # Celery settings for development
    CELERY_BROKER_URL = os.environ.get(
        'CELERY_BROKER_URL', 
        f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    )
    CELERY_RESULT_BACKEND = os.environ.get(
        'CELERY_RESULT_BACKEND', 
        f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    )
    
    # Development-specific Celery settings
    CELERY_ALWAYS_EAGER = os.environ.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true'
    CELERY_WORKER_DISABLE_RATE_LIMITS = True
    CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'false').lower() == 'true'
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # =====================================================
    # MOCK SERVICES CONFIGURATION
    # =====================================================
    
    # Mock service flags
    MOCK_TWILIO = os.environ.get('MOCK_TWILIO', 'true').lower() == 'true'
    MOCK_RESEND = os.environ.get('MOCK_RESEND', 'true').lower() == 'true'
    MOCK_SUPABASE = os.environ.get('MOCK_SUPABASE', 'true').lower() == 'true'
    
    # Mock service logging and saving
    MOCK_SERVICES_LOG_TO_FILE = os.environ.get('MOCK_SERVICES_LOG_TO_FILE', 'true').lower() == 'true'
    MOCK_SERVICES_SAVE_TO_FILESYSTEM = os.environ.get('MOCK_SERVICES_SAVE_TO_FILESYSTEM', 'true').lower() == 'true'
    MOCK_SERVICES_DIRECTORY = os.environ.get('MOCK_SERVICES_DIRECTORY', 'data/mock_services')
    
    # =====================================================
    # RATE LIMITING CONFIGURATION
    # =====================================================
    
    # Rate limiting - relaxed for development
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'false').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '1000/minute')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Specific rate limits for development
    RATELIMIT_API = os.environ.get('RATELIMIT_API', '500/minute')
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH', '100/minute')
    RATELIMIT_SMS = os.environ.get('RATELIMIT_SMS', '50/minute')
    RATELIMIT_EMAIL = os.environ.get('RATELIMIT_EMAIL', '100/minute')
    RATELIMIT_UPLOAD = os.environ.get('RATELIMIT_UPLOAD', '10/minute')
    
    # =====================================================
    # LOGGING CONFIGURATION
    # =====================================================
    
    # Logging settings for development
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/mingus_dev.log')
    LOG_MAX_SIZE = int(os.environ.get('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Enable SQL query logging
    LOG_SQL_QUERIES = True
    SQL_QUERY_LOG_FILE = os.environ.get('SQL_QUERY_LOG_FILE', 'logs/sql_queries.log')
    
    # Enable Celery task logging
    CELERY_LOG_FILE = os.environ.get('CELERY_LOG_FILE', 'logs/celery_tasks.log')
    
    # Enable API request/response logging
    API_LOG_FILE = os.environ.get('API_LOG_FILE', 'logs/api_requests.log')
    
    # Enable authentication logging
    AUTH_LOG_FILE = os.environ.get('AUTH_LOG_FILE', 'logs/auth_events.log')
    
    # Enable email logging
    EMAIL_LOG_FILE = os.environ.get('EMAIL_LOG_FILE', 'logs/email_events.log')
    
    # Enable SMS logging
    SMS_LOG_FILE = os.environ.get('SMS_LOG_FILE', 'logs/sms_events.log')
    
    # Enable database logging
    DB_LOG_FILE = os.environ.get('DB_LOG_FILE', 'logs/database_events.log')
    
    # Enable Redis logging
    REDIS_LOG_FILE = os.environ.get('REDIS_LOG_FILE', 'logs/redis_events.log')
    
    # =====================================================
    # DEBUG AND DEVELOPMENT TOOLS
    # =====================================================
    
    # Debug toolbar settings
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = os.environ.get('ENABLE_PROFILER', 'true').lower() == 'true'
    
    # Flask-DebugToolbar panels
    DEBUG_TB_PANELS = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
        'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
    ]
    
    # Development-specific debug settings
    ENABLE_DEBUG_TOOLBAR = True
    ENABLE_PROFILER = os.environ.get('ENABLE_PROFILER', 'true').lower() == 'true'
    ENABLE_SQL_LOGGING = True
    ENABLE_REQUEST_LOGGING = os.environ.get('ENABLE_REQUEST_LOGGING', 'true').lower() == 'true'
    ENABLE_RESPONSE_LOGGING = os.environ.get('ENABLE_RESPONSE_LOGGING', 'true').lower() == 'true'
    ENABLE_PERFORMANCE_MONITORING = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    
    # =====================================================
    # TESTING HELPERS
    # =====================================================
    
    # Testing and development helpers
    BYPASS_AUTH = os.environ.get('BYPASS_AUTH', 'false').lower() == 'true'
    SKIP_EMAIL_VERIFICATION = os.environ.get('SKIP_EMAIL_VERIFICATION', 'true').lower() == 'true'
    SKIP_PHONE_VERIFICATION = os.environ.get('SKIP_PHONE_VERIFICATION', 'true').lower() == 'true'
    ENABLE_TEST_DATA = os.environ.get('ENABLE_TEST_DATA', 'true').lower() == 'true'
    
    # Test user credentials
    TEST_USER_EMAIL = os.environ.get('TEST_USER_EMAIL', 'test@mingus.com')
    TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD', 'testpassword123')
    TEST_USER_PHONE = os.environ.get('TEST_USER_PHONE', '+1234567890')
    
    # =====================================================
    # SECURITY SETTINGS (RELAXED FOR DEVELOPMENT)
    # =====================================================
    
    # Security settings - relaxed for development
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'false').lower() == 'true'
    
    # CORS settings for development
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3001',
        'http://localhost:5000',
        'http://127.0.0.1:5000',
    ]
    
    # =====================================================
    # EMAIL CONFIGURATION
    # =====================================================
    
    # Email settings for development
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))  # MailHog default port
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@mingus.dev')
    
    # Suppress email sending in development
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'true').lower() == 'true'
    
    # =====================================================
    # SMS CONFIGURATION
    # =====================================================
    
    # Twilio settings for development
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'dev_account_sid')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'dev_auth_token')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890')
    
    # Mock SMS settings
    TWILIO_MOCK_SMS = True
    TWILIO_MOCK_LOG_FILE = os.environ.get('TWILIO_MOCK_LOG_FILE', 'logs/mock_twilio.log')
    
    # =====================================================
    # RESEND EMAIL CONFIGURATION
    # =====================================================
    
    # Resend settings for development
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', 'dev_api_key')
    
    # Mock email settings
    RESEND_MOCK_EMAILS = True
    RESEND_MOCK_LOG_FILE = os.environ.get('RESEND_MOCK_LOG_FILE', 'logs/mock_resend.log')
    
    # =====================================================
    # SUPABASE CONFIGURATION
    # =====================================================
    
    # Supabase settings for development
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://dev.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'dev_key')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'dev_service_role_key')
    
    # Mock Supabase settings
    SUPABASE_MOCK_MODE = os.environ.get('SUPABASE_MOCK_MODE', 'true').lower() == 'true'
    SUPABASE_MOCK_DATA_DIR = os.environ.get('SUPABASE_MOCK_DATA_DIR', 'data/mock_supabase')
    
    # =====================================================
    # CACHE CONFIGURATION
    # =====================================================
    
    # Cache settings for development
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'mingus_dev')
    
    # =====================================================
    # SESSION CONFIGURATION
    # =====================================================
    
    # Session settings for development
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', 'data/sessions')
    SESSION_FILE_THRESHOLD = int(os.environ.get('SESSION_FILE_THRESHOLD', 500))
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # =====================================================
    # FILE UPLOAD CONFIGURATION
    # =====================================================
    
    # File upload settings for development
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    
    # =====================================================
    # FEATURE FLAGS
    # =====================================================
    
    # Feature flags for development
    FEATURE_FLAGS = {
        'enable_analytics': os.environ.get('ENABLE_ANALYTICS', 'true').lower() == 'true',
        'enable_notifications': os.environ.get('ENABLE_NOTIFICATIONS', 'true').lower() == 'true',
        'enable_social_features': os.environ.get('ENABLE_SOCIAL_FEATURES', 'true').lower() == 'true',
        'enable_premium_features': os.environ.get('ENABLE_PREMIUM_FEATURES', 'true').lower() == 'true',
        'enable_beta_features': os.environ.get('ENABLE_BETA_FEATURES', 'true').lower() == 'true',
    }
    
    # =====================================================
    # MONITORING AND METRICS
    # =====================================================
    
    # Monitoring settings for development
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'false').lower() == 'true'
    STATSD_HOST = os.environ.get('STATSD_HOST', 'localhost')
    STATSD_PORT = int(os.environ.get('STATSD_PORT', 8125))
    STATSD_PREFIX = os.environ.get('STATSD_PREFIX', 'mingus.dev')
    
    # =====================================================
    # APPLICATION INITIALIZATION
    # =====================================================
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with development-specific settings"""
        super().init_app(app)
        
        # Configure logging
        cls._configure_logging(app)
        
        # Configure mock services
        cls._configure_mock_services(app)
        
        # Configure development tools
        cls._configure_development_tools(app)
        
        # Configure rate limiting
        cls._configure_rate_limiting(app)
        
        # Configure security (relaxed for development)
        cls._configure_security(app)
        
        log = logging.getLogger(__name__)
        log.info("Development configuration initialized")
    
    @classmethod
    def _configure_logging(cls, app):
        """Configure comprehensive logging for development"""
        import logging.handlers
        import os
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(cls.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(cls.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # SQL query logging
        if cls.LOG_SQL_QUERIES:
            sql_logger = logging.getLogger('sqlalchemy.engine')
            sql_logger.setLevel(logging.INFO)
            sql_file_handler = logging.handlers.RotatingFileHandler(
                cls.SQL_QUERY_LOG_FILE,
                maxBytes=cls.LOG_MAX_SIZE,
                backupCount=cls.LOG_BACKUP_COUNT
            )
            sql_file_handler.setFormatter(file_formatter)
            sql_logger.addHandler(sql_file_handler)
        
        # Celery task logging
        celery_logger = logging.getLogger('celery')
        celery_file_handler = logging.handlers.RotatingFileHandler(
            cls.CELERY_LOG_FILE,
            maxBytes=cls.LOG_MAX_SIZE,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        celery_file_handler.setFormatter(file_formatter)
        celery_logger.addHandler(celery_file_handler)
        
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
    def _configure_mock_services(cls, app):
        """Configure mock services for development"""
        if cls.MOCK_TWILIO or cls.MOCK_RESEND or cls.MOCK_SUPABASE:
            # Import mock services
            try:
                from backend.services.mock_services import (
                    mock_twilio, mock_resend, mock_supabase
                )
                
                # Configure mock services
                if cls.MOCK_TWILIO:
                    app.config['TWILIO_SERVICE'] = mock_twilio
                    app.logger.info("Mock Twilio service configured")
                
                if cls.MOCK_RESEND:
                    app.config['RESEND_SERVICE'] = mock_resend
                    app.logger.info("Mock Resend service configured")
                
                if cls.MOCK_SUPABASE:
                    app.config['SUPABASE_SERVICE'] = mock_supabase
                    app.logger.info("Mock Supabase service configured")
                    
            except ImportError as e:
                app.logger.warning(f"Mock services not available: {e}")
    
    @classmethod
    def _configure_development_tools(cls, app):
        """Configure development tools and debug features"""
        if cls.ENABLE_DEBUG_TOOLBAR:
            try:
                from flask_debugtoolbar import DebugToolbarExtension
                toolbar = DebugToolbarExtension(app)
                app.logger.info("Flask-DebugToolbar enabled")
            except ImportError:
                app.logger.warning("Flask-DebugToolbar not available")
        
        if cls.ENABLE_PROFILER:
            try:
                from flask_profiler import Profiler
                profiler = Profiler()
                profiler.init_app(app)
                app.logger.info("Flask-Profiler enabled")
            except ImportError:
                app.logger.warning("Flask-Profiler not available")
    
    @classmethod
    def _configure_rate_limiting(cls, app):
        """Configure rate limiting for development"""
        if not cls.RATELIMIT_ENABLED:
            app.logger.info("Rate limiting disabled for development")
        else:
            app.logger.info(f"Rate limiting enabled with default: {cls.RATELIMIT_DEFAULT}")
    
    @classmethod
    def _configure_security(cls, app):
        """Configure security settings for development"""
        app.logger.info("Security settings configured for development (relaxed)")
        
        # Disable HTTPS redirect for development
        if hasattr(app, 'config') and 'TALISMAN' in app.extensions:
            app.extensions['TALISMAN'].force_https = False 
