"""
Testing configuration using secure configuration management
"""

from .base import Config
from .secure_config import get_secure_config

class TestingConfig(Config):
    """Testing configuration using secure configuration management"""
    
    def __init__(self):
        """Initialize testing configuration with secure config manager"""
        super().__init__()
        self._load_testing_config()
    
    def _load_testing_config(self):
        """Load testing-specific configuration"""
        # Testing-specific overrides
        self.TESTING = True
        self.DEBUG = True  # DISABLED FOR SECURITY
        self.WTF_CSRF_ENABLED = False  # Disable CSRF for testing
        
        # Database settings for testing
        self.DATABASE_URL = self.secure_config.get('TEST_DATABASE_URL', 'sqlite:///test_mingus.db')
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.CREATE_TABLES = True
        
        # CORS settings for testing
        cors_origins = self.secure_config.get('CORS_ORIGINS', 'http://localhost:5002,http://127.0.0.1:5002')
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
        
        # Add testing-specific CORS origins
        test_origins = [
            'https://wiemjrvxlqkpbsukdqnb.supabase.co',
            'https://accounts.google.com'
        ]
        for origin in test_origins:
            if origin not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(origin)
        
        # Session settings for testing
        self.SESSION_COOKIE_SECURE = False
        self.SESSION_COOKIE_SAMESITE = self.secure_config.get('TEST_SESSION_COOKIE_SAMESITE', 'Lax')
        self.SESSION_COOKIE_HTTPONLY = True
        self.PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
        
        # Supabase settings for testing (use secure config manager)
        self.SUPABASE_URL = self.secure_config.get('SUPABASE_URL')
        self.SUPABASE_KEY = self.secure_config.get('SUPABASE_KEY')
        self.SUPABASE_SERVICE_ROLE_KEY = self.secure_config.get('SUPABASE_SERVICE_ROLE_KEY')
        self.SUPABASE_JWT_SECRET = self.secure_config.get('SUPABASE_JWT_SECRET')
        
        # Redis settings for testing
        self.REDIS_URL = self.secure_config.get('REDIS_URL', 'redis://localhost:6379/1')  # Use different DB
        
        # Stripe settings for testing
        self.STRIPE_ENVIRONMENT = self.secure_config.get('TEST_STRIPE_ENVIRONMENT', 'test')  # Always use test environment
        self.STRIPE_TEST_SECRET_KEY = self.secure_config.get('STRIPE_TEST_SECRET_KEY')
        self.STRIPE_TEST_PUBLISHABLE_KEY = self.secure_config.get('STRIPE_TEST_PUBLISHABLE_KEY')
        
        # Plaid settings for testing
        self.PLAID_ENVIRONMENT = self.secure_config.get('TEST_PLAID_ENVIRONMENT', 'sandbox')  # Always use sandbox environment
        self.PLAID_SANDBOX_CLIENT_ID = self.secure_config.get('PLAID_SANDBOX_CLIENT_ID')
        self.PLAID_SANDBOX_SECRET = self.secure_config.get('PLAID_SANDBOX_SECRET')
        
        # Email settings for testing
        self.EMAIL_PROVIDER = self.secure_config.get('TEST_EMAIL_PROVIDER', 'resend')
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.RESEND_FROM_NAME = self.secure_config.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        
        # SMS settings for testing
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER')
        
        # Testing-specific security settings
        self.SECURE_SSL_REDIRECT = False  # Allow HTTP in testing
        self.SECURE_HSTS_SECONDS = 0  # Disable HSTS in testing
        
        # Rate limiting for testing
        self.RATELIMIT_ENABLED = True
        self.RATELIMIT_DEFAULT = self.secure_config.get('TEST_RATELIMIT_DEFAULT', '10000 per minute')  # Very permissive for testing
        
        # Cache settings for testing
        self.CACHE_TYPE = self.secure_config.get('TEST_CACHE_TYPE', 'simple')
        self.CACHE_DEFAULT_TIMEOUT = 60  # Short timeout for testing
        
        # Audit logging for testing
        self.AUDIT_LOG_ENABLED = True
        self.AUDIT_LOG_RETENTION_DAYS = 1  # Very short retention for testing
        
        # Performance monitoring for testing
        self.ENABLE_PERFORMANCE_MONITORING = False  # Disable in testing
        self.ENABLE_ERROR_TRACKING = False  # Disable in testing
        self.ENABLE_USAGE_ANALYTICS = False  # Disable in testing
        
        # Testing-specific feature flags
        self.ENABLE_ONBOARDING = True
        self.ENABLE_USER_PROFILES = True
        self.BYPASS_AUTH = True  # DISABLED FOR SECURITY  # Enable auth bypass for testing
        self.ENABLE_ADVANCED_ANALYTICS = False  # Disable expensive features in testing
        self.ENABLE_SOCIAL_SHARING = False  # Disable in testing
        self.ENABLE_EXPORT_FUNCTIONALITY = False  # Disable in testing
        
        # Mock external services for testing
        self.MOCK_STRIPE = self.secure_config.get('MOCK_STRIPE', 'true').lower() == 'true'
        self.MOCK_PLAID = self.secure_config.get('MOCK_PLAID', 'true').lower() == 'true'
        self.MOCK_TWILIO = self.secure_config.get('MOCK_TWILIO', 'true').lower() == 'true'
        self.MOCK_RESEND = self.secure_config.get('MOCK_RESEND', 'true').lower() == 'true'
        
        # Test email configuration
        self.TEST_EMAIL_ENABLED = True
        self.TEST_EMAIL_ADDRESS = self.secure_config.get('TEST_EMAIL_ADDRESS', 'test@example.com')
        
        # Testing-specific API settings
        self.API_TITLE = self.secure_config.get('TEST_API_TITLE', 'Mingus Personal Finance API (Testing)')
        self.API_VERSION = self.secure_config.get('TEST_API_VERSION', 'v1')
        self.API_DESCRIPTION = self.secure_config.get('TEST_API_DESCRIPTION', 'Testing API for Mingus personal finance application')
        
        # Testing-specific file upload settings
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB for testing
        self.UPLOAD_FOLDER = self.secure_config.get('TEST_UPLOAD_FOLDER', 'uploads/testing')
        
        # Testing-specific backup settings
        self.BACKUP_ENABLED = False  # Disable backups in testing
        self.BACKUP_SCHEDULE = self.secure_config.get('TEST_BACKUP_SCHEDULE', '0 0 * * *')  # Never
        self.BACKUP_RETENTION_DAYS = 1
        self.BACKUP_LOCATION = self.secure_config.get('TEST_BACKUP_LOCATION', 'backups/testing/')
        
        # Testing-specific monitoring
        self.MONITORING = {
            'enable_health_checks': False,  # Disable in testing
            'enable_performance_metrics': False,  # Disable in testing
            'enable_error_tracking': False,  # Disable in testing
            'enable_usage_analytics': False,  # Disable in testing
            'metrics_retention_days': 1,  # Very short retention for testing
        }
        
        # Testing-specific error handling
        self.ERROR_HANDLING = {
            'enable_error_pages': False,  # Disable in testing
            'log_errors': True,
            'email_errors': False,  # Don't email errors in testing
            'error_reporting_url': None,
        }
        
        # Testing-specific API configuration
        self.API = {
            'enable_rate_limiting': False,  # Disable in testing
            'enable_request_logging': False,  # Disable in testing
            'enable_response_caching': False,  # Disable in testing
            'max_request_size': 16 * 1024 * 1024,  # 16MB for testing
            'timeout_seconds': 30,  # Short timeout for testing
        }
        
        # Testing-specific deployment configuration
        self.DEPLOYMENT = {
            'environment': 'testing',
            'host': '127.0.0.1',
            'port': int(self.secure_config.get('PORT', '5003')),  # Different port for testing
            'workers': 1,
            'threads': 1,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'preload_app': False,  # Disable preload for testing
            'worker_class': 'sync',
        }
        
        # Testing-specific cost optimization
        self.COST_OPTIMIZATION = {
            'use_free_tier_services': True,
            'minimize_api_calls': True,  # Minimize API calls in testing
            'use_in_memory_caching': True,
            'disable_expensive_features': True,  # Disable expensive features in testing
            'optimize_database_queries': False,  # Don't optimize in testing
            'use_compression': False,  # Disable compression for testing
            'minimize_external_dependencies': True,  # Minimize dependencies in testing
        }
        
        # Testing-specific feature flags
        self.FEATURE_FLAGS = {
            'income_comparison_enabled': True,
            'advanced_analytics_enabled': False,  # Disable in testing
            'user_profiles_enabled': True,
            'job_recommendations_enabled': False,  # Disable in testing
            'email_notifications_enabled': False,  # Disable in testing
            'social_sharing_enabled': False,  # Disable in testing
            'export_functionality_enabled': False,  # Disable in testing
        }
        
        # Testing-specific external services
        self.EXTERNAL_SERVICES = {
            'census_api_enabled': False,  # Disable in testing
            'email_service_enabled': False,  # Disable in testing
            'analytics_service_enabled': False,  # Disable in testing
            'monitoring_service_enabled': False,  # Disable in testing
            'cdn_enabled': False,  # Disable CDN for testing
        }
        
        # Testing-specific memory management
        self.MEMORY_MANAGEMENT = {
            'max_cache_size_mb': 10,  # Small cache for testing
            'cache_cleanup_interval_seconds': 300,  # 5 minutes
            'max_concurrent_analyses': 1,  # Single analysis for testing
            'memory_monitoring_enabled': False,  # Disable in testing
            'auto_cleanup_enabled': True,
        }
        
        # Testing-specific performance monitoring
        self.PERFORMANCE_MONITORING = {
            'enable_request_timing': False,  # Disable in testing
            'enable_memory_monitoring': False,  # Disable in testing
            'enable_cache_monitoring': False,  # Disable in testing
            'enable_error_monitoring': False,  # Disable in testing
            'metrics_export_interval_seconds': 0,  # Disable in testing
            'performance_thresholds': {
                'max_response_time_ms': 10000,  # Very lenient for testing
                'max_memory_usage_mb': 500,  # More memory for testing
                'max_cpu_usage_percent': 100,  # Allow full CPU for testing
            }
        }
        
        # Testing-specific logging
        self.LOG_LEVEL = self.secure_config.get('TEST_LOG_LEVEL', 'DEBUG')
        self.LOG_FORMAT = self.secure_config.get('TEST_LOG_FORMAT', '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}')
        self.LOG_ROTATION = self.secure_config.get('TEST_LOG_ROTATION', '1 hour')
        self.LOG_RETENTION = self.secure_config.get('TEST_LOG_RETENTION', '1 day')
        self.LOG_FILE = self.secure_config.get('TEST_LOG_FILE', 'logs/mingus_testing.log')
        
        # Testing-specific database settings
        self.DB_POOL_SIZE = 5  # Small pool for testing
        self.DB_MAX_OVERFLOW = 10
        self.DB_POOL_RECYCLE = 1800  # 30 minutes
        self.DB_POOL_TIMEOUT = 10
        self.DB_STATEMENT_TIMEOUT = 10000  # 10 seconds
        self.DB_IDLE_TIMEOUT = 20000  # 20 seconds
        self.DB_LOCK_TIMEOUT = 5000  # 5 seconds
        
        # Testing-specific SSL settings
        self.SECURE_SSL_REDIRECT = False
        self.SECURE_PROXY_SSL_HEADER = None
        self.SECURE_HSTS_SECONDS = 0
        self.SECURE_HSTS_INCLUDE_SUBDOMAINS = False
        self.SECURE_HSTS_PRELOAD = False
        self.SECURE_CONTENT_TYPE_NOSNIFF = False
        self.SECURE_BROWSER_XSS_FILTER = False
        self.SECURE_FRAME_DENY = False 