"""
Development configuration
"""

import os
from .base import Config
from .secure_config import get_secure_config

class DevelopmentConfig(Config):
    """Development configuration class using secure configuration management"""
    
    def __init__(self):
        """Initialize development configuration with secure config manager"""
        super().__init__()
        self._load_development_config()
    
    def _load_development_config(self):
        """Load development-specific configuration"""
        # Development-specific overrides
        self.DEBUG = True  # DISABLED FOR SECURITY
        self.TESTING = False
        
        # Database settings for development
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.CREATE_TABLES = True
        
        # CORS settings for development
        cors_origins = self.secure_config.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5002,http://127.0.0.1:5002')
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
        
        # Add development-specific CORS origins
        dev_origins = [
            'https://wiemjrvxlqkpbsukdqnb.supabase.co',
            'https://accounts.google.com'  # Google OAuth domain
        ]
        for origin in dev_origins:
            if origin not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(origin)
        
        # Session settings for development
        self.SESSION_COOKIE_SECURE = False  # Allow HTTP in development
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = self.secure_config.get('DEV_SESSION_COOKIE_SAMESITE', 'Lax')  # More permissive for OAuth
        self.PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
        
        # Logging settings for development
        self.LOG_LEVEL = self.secure_config.get('DEV_LOG_LEVEL', 'DEBUG')
        
        # Security settings for development
        self.WTF_CSRF_ENABLED = False  # Disable CSRF for API testing
        
        # Feature flags for development
        self.ENABLE_ONBOARDING = True
        self.ENABLE_USER_PROFILES = True
        self.BYPASS_AUTH = False  # Enable auth bypass for development
        
        # Development-specific settings
        self.PRESERVE_CONTEXT_ON_EXCEPTION = False
        self.TRAP_HTTP_EXCEPTIONS = True
        self.TRAP_BAD_REQUEST_ERRORS = True
        
        # Supabase settings (use secure config manager)
        self.SUPABASE_URL = self.secure_config.get('SUPABASE_URL')
        self.SUPABASE_KEY = self.secure_config.get('SUPABASE_KEY')
        self.SUPABASE_SERVICE_ROLE_KEY = self.secure_config.get('SUPABASE_SERVICE_ROLE_KEY')
        self.SUPABASE_JWT_SECRET = self.secure_config.get('SUPABASE_JWT_SECRET')
        
        # Email settings (use secure config manager)
        self.MAIL_SERVER = self.secure_config.get('MAIL_SERVER', 'smtp.gmail.com')
        self.MAIL_PORT = int(self.secure_config.get('MAIL_PORT', '587'))
        self.MAIL_USE_TLS = self.secure_config.get('MAIL_USE_TLS', 'true').lower() == 'true'
        self.MAIL_USERNAME = self.secure_config.get('MAIL_USERNAME')
        self.MAIL_PASSWORD = self.secure_config.get('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = self.secure_config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
        
        # Redis settings for development
        self.REDIS_URL = self.secure_config.get('REDIS_URL', 'redis://localhost:6379/0')
        
        # Stripe settings for development
        self.STRIPE_ENVIRONMENT = self.secure_config.get('STRIPE_ENVIRONMENT', 'test')
        self.STRIPE_TEST_SECRET_KEY = self.secure_config.get('STRIPE_TEST_SECRET_KEY')
        self.STRIPE_TEST_PUBLISHABLE_KEY = self.secure_config.get('STRIPE_TEST_PUBLISHABLE_KEY')
        
        # Plaid settings for development
        self.PLAID_ENVIRONMENT = self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox')
        self.PLAID_SANDBOX_CLIENT_ID = self.secure_config.get('PLAID_SANDBOX_CLIENT_ID')
        self.PLAID_SANDBOX_SECRET = self.secure_config.get('PLAID_SANDBOX_SECRET')
        
        # Email provider settings
        self.EMAIL_PROVIDER = self.secure_config.get('EMAIL_PROVIDER', 'resend')
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.RESEND_FROM_NAME = self.secure_config.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        
        # SMS settings
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER')
        
        # Development-specific security settings
        self.SECURE_SSL_REDIRECT = False  # Allow HTTP in development
        self.SECURE_HSTS_SECONDS = 0  # Disable HSTS in development
        
        # Rate limiting for development
        self.RATELIMIT_ENABLED = True
        self.RATELIMIT_DEFAULT = self.secure_config.get('DEV_RATELIMIT_DEFAULT', '1000 per minute')  # More permissive for development
        
        # Cache settings for development
        self.CACHE_TYPE = self.secure_config.get('DEV_CACHE_TYPE', 'simple')
        self.CACHE_DEFAULT_TIMEOUT = 300
        
        # Audit logging for development
        self.AUDIT_LOG_ENABLED = True
        self.AUDIT_LOG_RETENTION_DAYS = 30  # Shorter retention for development
        
        # Performance monitoring for development
        self.ENABLE_PERFORMANCE_MONITORING = True
        self.ENABLE_ERROR_TRACKING = True
        self.ENABLE_USAGE_ANALYTICS = True
        
        # Development-specific feature flags
        self.ENABLE_ADVANCED_ANALYTICS = True
        self.ENABLE_SOCIAL_SHARING = True
        self.ENABLE_EXPORT_FUNCTIONALITY = True
        
        # Mock external services for development
        self.MOCK_STRIPE = self.secure_config.get('MOCK_STRIPE', 'false').lower() == 'true'
        self.MOCK_PLAID = self.secure_config.get('MOCK_PLAID', 'false').lower() == 'true'
        self.MOCK_TWILIO = self.secure_config.get('MOCK_TWILIO', 'false').lower() == 'true'
        self.MOCK_RESEND = self.secure_config.get('MOCK_RESEND', 'false').lower() == 'true'
        
        # Test configuration
        self.TEST_EMAIL_ENABLED = self.secure_config.get('TEST_EMAIL_ENABLED', 'false').lower() == 'true'
        self.TEST_EMAIL_ADDRESS = self.secure_config.get('TEST_EMAIL_ADDRESS', 'test@example.com')
        
        # Development-specific API settings
        self.API_TITLE = self.secure_config.get('DEV_API_TITLE', 'Mingus Personal Finance API (Development)')
        self.API_VERSION = self.secure_config.get('DEV_API_VERSION', 'v1')
        self.API_DESCRIPTION = self.secure_config.get('DEV_API_DESCRIPTION', 'Development API for Mingus personal finance application')
        
        # Development-specific file upload settings
        self.MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB for development
        self.UPLOAD_FOLDER = self.secure_config.get('DEV_UPLOAD_FOLDER', 'uploads/development')
        
        # Development-specific backup settings
        self.BACKUP_ENABLED = True
        self.BACKUP_SCHEDULE = self.secure_config.get('DEV_BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
        self.BACKUP_RETENTION_DAYS = 7  # Shorter retention for development
        self.BACKUP_LOCATION = self.secure_config.get('DEV_BACKUP_LOCATION', 'backups/development/')
        
        # Development-specific monitoring
        self.MONITORING = {
            'enable_health_checks': True,
            'enable_performance_metrics': True,
            'enable_error_tracking': True,
            'enable_usage_analytics': True,
            'metrics_retention_days': 3,  # Shorter retention for development
        }
        
        # Development-specific error handling
        self.ERROR_HANDLING = {
            'enable_error_pages': True,
            'log_errors': True,
            'email_errors': False,  # Don't email errors in development
            'error_reporting_url': None,
        }
        
        # Development-specific API configuration
        self.API = {
            'enable_rate_limiting': True,
            'enable_request_logging': True,
            'enable_response_caching': True,
            'max_request_size': 32 * 1024 * 1024,  # 32MB for development
            'timeout_seconds': 60,  # Longer timeout for development
        }
        
        # Development-specific deployment configuration
        self.DEPLOYMENT = {
            'environment': 'development',
            'host': '127.0.0.1',
            'port': int(self.secure_config.get('PORT', '5002')),
            'workers': 1,
            'threads': 2,
            'max_requests': 100,
            'max_requests_jitter': 10,
            'preload_app': False,  # Disable preload for development
            'worker_class': 'sync',
        }
        
        # Development-specific cost optimization
        self.COST_OPTIMIZATION = {
            'use_free_tier_services': True,
            'minimize_api_calls': False,  # Allow more API calls in development
            'use_in_memory_caching': True,
            'disable_expensive_features': False,  # Enable all features in development
            'optimize_database_queries': False,  # Don't optimize in development
            'use_compression': False,  # Disable compression for development
            'minimize_external_dependencies': False,  # Allow all dependencies in development
        }
        
        # Development-specific feature flags
        self.FEATURE_FLAGS = {
            'income_comparison_enabled': True,
            'advanced_analytics_enabled': True,  # Enable in development
            'user_profiles_enabled': True,
            'job_recommendations_enabled': True,
            'email_notifications_enabled': True,
            'social_sharing_enabled': True,
            'export_functionality_enabled': True,
        }
        
        # Development-specific external services
        self.EXTERNAL_SERVICES = {
            'census_api_enabled': True,  # Enable in development
            'email_service_enabled': True,
            'analytics_service_enabled': True,
            'monitoring_service_enabled': True,
            'cdn_enabled': False,  # Disable CDN for development
        }
        
        # Development-specific memory management
        self.MEMORY_MANAGEMENT = {
            'max_cache_size_mb': 100,  # Larger cache for development
            'cache_cleanup_interval_seconds': 1800,  # 30 minutes
            'max_concurrent_analyses': 20,  # More concurrent analyses for development
            'memory_monitoring_enabled': True,
            'auto_cleanup_enabled': True,
        }
        
        # Development-specific performance monitoring
        self.PERFORMANCE_MONITORING = {
            'enable_request_timing': True,
            'enable_memory_monitoring': True,
            'enable_cache_monitoring': True,
            'enable_error_monitoring': True,
            'metrics_export_interval_seconds': 60,  # More frequent in development
            'performance_thresholds': {
                'max_response_time_ms': 5000,  # More lenient for development
                'max_memory_usage_mb': 200,  # More memory for development
                'max_cpu_usage_percent': 90,  # More CPU for development
            }
        }
        
        # Article Library Feature Flags (Development)
        self.ENABLE_ARTICLE_LIBRARY = True
        self.ENABLE_AI_RECOMMENDATIONS = True
        self.ENABLE_CULTURAL_PERSONALIZATION = True
        self.ENABLE_ADVANCED_SEARCH = True
        self.ENABLE_SOCIAL_SHARING = True
        self.ENABLE_OFFLINE_READING = False
        self.ENABLE_ARTICLE_ANALYTICS = True 