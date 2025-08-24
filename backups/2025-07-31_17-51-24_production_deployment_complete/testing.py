"""
Testing configuration for MINGUS Application
Optimized for PostgreSQL testing with isolated test database
"""

import os
from .base import Config

class TestingConfig(Config):
    """Testing configuration class"""
    
    DEBUG = False
    TESTING = True
    
    # =====================================================
    # POSTGRESQL DATABASE SETTINGS FOR TESTING
    # =====================================================
    
    # Test database connection
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://mingus_test:mingus_test_password@localhost:5432/mingus_testing')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CREATE_TABLES = True
    
    # Test-specific database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Minimal pool for testing
        'pool_size': int(os.environ.get('TEST_DB_POOL_SIZE', 1)),
        'pool_recycle': int(os.environ.get('TEST_DB_POOL_RECYCLE', 300)),  # 5 minutes
        'pool_pre_ping': True,
        'pool_timeout': int(os.environ.get('TEST_DB_POOL_TIMEOUT', 5)),
        'max_overflow': int(os.environ.get('TEST_DB_MAX_OVERFLOW', 0)),
        'echo': os.environ.get('TEST_DB_ECHO', 'false').lower() == 'true',
        'echo_pool': False,
        
        # Test PostgreSQL settings
        'connect_args': {
            'application_name': 'mingus_test',
            'options': '-c timezone=utc -c statement_timeout=30000',  # 30 second timeout
            'sslmode': 'prefer',  # Less strict SSL for testing
        }
    }
    
    # Test database performance settings
    DB_STATEMENT_TIMEOUT = int(os.environ.get('TEST_DB_STATEMENT_TIMEOUT', 30000))  # 30 seconds
    DB_IDLE_IN_TRANSACTION_TIMEOUT = int(os.environ.get('TEST_DB_IDLE_TIMEOUT', 60000))  # 60 seconds
    DB_LOCK_TIMEOUT = int(os.environ.get('TEST_DB_LOCK_TIMEOUT', 10000))  # 10 seconds
    
    # Test database monitoring
    DB_ENABLE_QUERY_LOGGING = os.environ.get('TEST_DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
    DB_SLOW_QUERY_THRESHOLD = float(os.environ.get('TEST_DB_SLOW_QUERY_THRESHOLD', 0.1))  # 0.1 seconds
    DB_ENABLE_CONNECTION_MONITORING = False
    DB_LOG_LEVEL = 'ERROR'
    
    # Test database backup (disabled)
    DB_BACKUP_ENABLED = False
    DB_BACKUP_SCHEDULE = '0 0 * * *'  # Never
    DB_BACKUP_RETENTION_DAYS = 1
    
    # Test database security (minimal)
    DB_ENABLE_ROW_LEVEL_SECURITY = False
    DB_ENABLE_AUDIT_LOGGING = False
    DB_AUDIT_LOG_RETENTION_DAYS = 1
    
    # Test health checks (minimal)
    DB_HEALTH_CHECK_INTERVAL = int(os.environ.get('TEST_DB_HEALTH_CHECK_INTERVAL', 3600))  # 1 hour
    DB_HEALTH_CHECK_TIMEOUT = int(os.environ.get('TEST_DB_HEALTH_CHECK_TIMEOUT', 5))  # 5 seconds
    DB_MAX_RETRY_ATTEMPTS = int(os.environ.get('TEST_DB_MAX_RETRY_ATTEMPTS', 1))
    DB_RETRY_DELAY = int(os.environ.get('TEST_DB_RETRY_DELAY', 1))  # 1 second
    
    # Test-specific settings
    WTF_CSRF_ENABLED = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SESSION_COOKIE_SECURE = False
    
    # Test logging
    LOG_LEVEL = 'ERROR'
    DB_LOG_LEVEL = 'ERROR'
    DB_LOG_FILE = 'logs/database_test.log'
    
    # Test caching (in-memory)
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 60  # 1 minute
    REDIS_URL = None
    
    # Test rate limiting (disabled)
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '1000 per minute'
    
    # Test feature flags
    ENABLE_ONBOARDING = True
    ENABLE_USER_PROFILES = True
    ENABLE_ENCRYPTION = False  # Disable encryption for faster tests
    ENABLE_AUDIT_LOGGING = False
    BYPASS_AUTH = True
    
    # Test database performance monitoring
    DB_PERFORMANCE_MONITORING = {
        'enable_query_monitoring': False,
        'enable_connection_monitoring': False,
        'enable_slow_query_logging': False,
        'slow_query_threshold_ms': 100,
        'max_connections_warning': 100,
        'connection_timeout_warning_ms': 1000,
        'enable_metrics_collection': False,
        'metrics_retention_hours': 1,
    }
    
    # Test database maintenance (disabled)
    DB_MAINTENANCE = {
        'enable_auto_vacuum': False,
        'enable_auto_analyze': False,
        'vacuum_threshold': 100,
        'analyze_threshold': 100,
        'maintenance_window_start': '00:00',
        'maintenance_window_duration': 0,
    }
    
    # Test database backup configuration (disabled)
    DB_BACKUP_CONFIG = {
        'enable_automated_backups': False,
        'backup_frequency_hours': 24,
        'backup_retention_days': 1,
        'backup_compression': False,
        'backup_encryption': False,
        'backup_verification': False,
        'backup_location': 'backups/database/test/',
        'backup_filename_pattern': 'mingus_test_backup_{timestamp}.sql',
    }
    
    # Test database security configuration (minimal)
    DB_SECURITY_CONFIG = {
        'enable_ssl_connections': False,
        'require_ssl': False,
        'ssl_cert_verification': False,
        'enable_connection_encryption': False,
        'enable_query_encryption': False,
        'max_failed_connections': 100,
        'connection_ban_duration_minutes': 1,
    }
    
    # Test-specific secret key
    SECRET_KEY = 'test-secret-key-for-testing-only'
    
    # Test external services (disabled)
    EXTERNAL_SERVICES = {
        'census_api_enabled': False,
        'email_service_enabled': False,
        'analytics_service_enabled': False,
        'monitoring_service_enabled': False,
        'cdn_enabled': False,
    }
    
    # Test memory management
    MEMORY_MANAGEMENT = {
        'max_cache_size_mb': 10,
        'cache_cleanup_interval_seconds': 60,
        'max_concurrent_analyses': 1,
        'memory_monitoring_enabled': False,
        'auto_cleanup_enabled': False,
    }
    
    # Test performance monitoring (disabled)
    PERFORMANCE_MONITORING = {
        'enable_request_timing': False,
        'enable_memory_monitoring': False,
        'enable_cache_monitoring': False,
        'enable_error_monitoring': False,
        'metrics_export_interval_seconds': 3600,
        'performance_thresholds': {
            'max_response_time_ms': 10000,
            'max_memory_usage_mb': 100,
            'max_cpu_usage_percent': 100,
        }
    }
    
    # Test backup (disabled)
    BACKUP = {
        'enable_automatic_backups': False,
        'backup_interval_hours': 24,
        'backup_retention_days': 1,
        'backup_location': 'backups/test/',
    }
    
    # Test CORS settings
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5002',
        'http://127.0.0.1:5002'
    ]
    
    # Test session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 300  # 5 minutes for tests
    
    # Test Supabase settings (mocked)
    SUPABASE_URL = "https://test.supabase.co"
    SUPABASE_KEY = "test-key"
    SUPABASE_SERVICE_ROLE_KEY = "test-service-role-key"
    SUPABASE_JWT_SECRET = "test-jwt-secret"
    
    # Test email settings (disabled)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'test@example.com'
    
    # Test file upload settings
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB max file size for tests
    UPLOAD_FOLDER = 'uploads/test'
    
    # Test API settings
    API = {
        'enable_rate_limiting': False,
        'enable_request_logging': False,
        'enable_response_caching': False,
        'max_request_size': 1024 * 1024,  # 1MB
        'timeout_seconds': 30,
    }
    
    # Test deployment settings
    DEPLOYMENT = {
        'environment': 'testing',
        'host': '127.0.0.1',
        'port': int(os.environ.get('TEST_PORT', 5001)),
        'workers': 1,
        'threads': 1,
        'max_requests': 100,
        'max_requests_jitter': 10,
        'preload_app': False,
        'worker_class': 'sync',
    }
    
    # Test feature flags
    FEATURE_FLAGS = {
        'income_comparison_enabled': True,
        'advanced_analytics_enabled': False,
        'user_profiles_enabled': True,
        'job_recommendations_enabled': False,
        'email_notifications_enabled': False,
        'social_sharing_enabled': False,
        'export_functionality_enabled': False,
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with testing settings"""
        
        # Set testing-specific configurations
        app.config['PROPAGATE_EXCEPTIONS'] = True
        app.config['TESTING'] = True
        
        # Configure minimal logging for tests
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        
        # Disable CSRF for testing
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Configure test database
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        app.logger.info('Testing configuration initialized successfully') 