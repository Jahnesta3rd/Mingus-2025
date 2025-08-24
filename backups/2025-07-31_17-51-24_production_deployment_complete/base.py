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
    
    # =====================================================
    # POSTGRESQL DATABASE CONFIGURATION
    # =====================================================
    
    # Database connection settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Connection pooling for production workloads
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # 1 hour
        'pool_pre_ping': True,
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true',
        'echo_pool': os.environ.get('DB_ECHO_POOL', 'false').lower() == 'true',
        
        # PostgreSQL-specific optimizations
        'connect_args': {
            'application_name': 'mingus_app',
            'options': '-c timezone=utc -c statement_timeout=30000',  # 30 second timeout
            'sslmode': os.environ.get('DB_SSL_MODE', 'prefer'),
            'ssl_cert': os.environ.get('DB_SSL_CERT'),
            'ssl_key': os.environ.get('DB_SSL_KEY'),
            'ssl_ca': os.environ.get('DB_SSL_CA'),
            'ssl_crl': os.environ.get('DB_SSL_CRL'),
        }
    }
    
    # Database performance settings
    DB_STATEMENT_TIMEOUT = int(os.environ.get('DB_STATEMENT_TIMEOUT', 30000))  # 30 seconds
    DB_IDLE_IN_TRANSACTION_TIMEOUT = int(os.environ.get('DB_IDLE_TIMEOUT', 60000))  # 60 seconds
    DB_LOCK_TIMEOUT = int(os.environ.get('DB_LOCK_TIMEOUT', 10000))  # 10 seconds
    
    # Database monitoring and logging
    DB_ENABLE_QUERY_LOGGING = os.environ.get('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
    DB_SLOW_QUERY_THRESHOLD = float(os.environ.get('DB_SLOW_QUERY_THRESHOLD', 1.0))  # 1 second
    DB_ENABLE_CONNECTION_MONITORING = os.environ.get('DB_ENABLE_CONNECTION_MONITORING', 'true').lower() == 'true'
    
    # Database backup and maintenance
    DB_BACKUP_ENABLED = os.environ.get('DB_BACKUP_ENABLED', 'true').lower() == 'true'
    DB_BACKUP_SCHEDULE = os.environ.get('DB_BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
    DB_BACKUP_RETENTION_DAYS = int(os.environ.get('DB_BACKUP_RETENTION_DAYS', 30))
    DB_BACKUP_LOCATION = os.environ.get('DB_BACKUP_LOCATION', 'backups/database/')
    
    # Database security settings
    DB_ENABLE_ROW_LEVEL_SECURITY = os.environ.get('DB_ENABLE_RLS', 'true').lower() == 'true'
    DB_ENABLE_AUDIT_LOGGING = os.environ.get('DB_ENABLE_AUDIT', 'true').lower() == 'true'
    DB_AUDIT_LOG_RETENTION_DAYS = int(os.environ.get('DB_AUDIT_RETENTION', 90))
    
    # Database connection health checks
    DB_HEALTH_CHECK_INTERVAL = int(os.environ.get('DB_HEALTH_CHECK_INTERVAL', 300))  # 5 minutes
    DB_HEALTH_CHECK_TIMEOUT = int(os.environ.get('DB_HEALTH_CHECK_TIMEOUT', 10))  # 10 seconds
    DB_MAX_RETRY_ATTEMPTS = int(os.environ.get('DB_MAX_RETRY_ATTEMPTS', 3))
    DB_RETRY_DELAY = int(os.environ.get('DB_RETRY_DELAY', 5))  # 5 seconds
    
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
    
    # Database-specific logging
    DB_LOG_LEVEL = os.environ.get('DB_LOG_LEVEL', 'WARNING')
    DB_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DB_LOG_FILE = os.environ.get('DB_LOG_FILE', 'logs/database.log')
    
    # Supabase settings (for existing functionality)
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://wiemjrvxlqkpbsukdqnb.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
    
    # =====================================================
    # STRIPE PAYMENT CONFIGURATION
    # =====================================================
    
    # Stripe API keys
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Stripe configuration
    STRIPE_API_VERSION = os.environ.get('STRIPE_API_VERSION', '2023-10-16')
    STRIPE_DEBUG = os.environ.get('STRIPE_DEBUG', 'false').lower() == 'true'
    
    # Stripe subscription price IDs (configure these in your Stripe dashboard)
    STRIPE_PRICE_IDS = {
        'budget_monthly': os.environ.get('STRIPE_BUDGET_MONTHLY_PRICE_ID'),
        'budget_yearly': os.environ.get('STRIPE_BUDGET_YEARLY_PRICE_ID'),
        'mid_tier_monthly': os.environ.get('STRIPE_MID_TIER_MONTHLY_PRICE_ID'),
        'mid_tier_yearly': os.environ.get('STRIPE_MID_TIER_YEARLY_PRICE_ID'),
        'professional_monthly': os.environ.get('STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID'),
        'professional_yearly': os.environ.get('STRIPE_PROFESSIONAL_YEARLY_PRICE_ID'),
    }
    
    # Stripe webhook events to handle
    STRIPE_WEBHOOK_EVENTS = [
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
        'invoice.payment_succeeded',
        'invoice.payment_failed',
        'payment_intent.succeeded',
        'payment_intent.payment_failed',
        'customer.created',
        'customer.updated',
        'customer.deleted',
        'payment_method.attached',
        'payment_method.detached',
        'invoice.created',
        'invoice.finalized',
        'invoice.payment_action_required'
    ]
    
    # Stripe payment settings
    STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'usd')
    STRIPE_PAYMENT_METHOD_TYPES = ['card', 'bank_account']
    STRIPE_AUTOMATIC_PAYMENT_METHODS = ['card', 'link']
    
    # Stripe subscription settings
    STRIPE_TRIAL_DAYS = int(os.environ.get('STRIPE_TRIAL_DAYS', 7))
    STRIPE_GRACE_PERIOD_DAYS = int(os.environ.get('STRIPE_GRACE_PERIOD_DAYS', 3))
    STRIPE_PAYMENT_BEHAVIOR = os.environ.get('STRIPE_PAYMENT_BEHAVIOR', 'default_incomplete')
    STRIPE_PAYMENT_SETTINGS = {
        'payment_method_types': STRIPE_PAYMENT_METHOD_TYPES,
        'save_default_payment_method': 'on_subscription',
        'automatic_payment_methods': {
            'enabled': True,
            'allow_redirects': 'never'
        }
    }
    
    # Stripe billing settings
    STRIPE_BILLING_CYCLE_ANCHOR = 'now'
    STRIPE_PRORATION_BEHAVIOR = 'create_prorations'
    STRIPE_COLLECTION_METHOD = 'charge_automatically'
    
    # Stripe security settings
    STRIPE_ENABLE_3D_SECURE = os.environ.get('STRIPE_ENABLE_3D_SECURE', 'true').lower() == 'true'
    STRIPE_REQUIRE_CAPTURE = os.environ.get('STRIPE_REQUIRE_CAPTURE', 'false').lower() == 'true'
    STRIPE_SETUP_FUTURE_USAGE = 'off_session'
    
    # Stripe compliance and tax settings
    STRIPE_AUTOMATIC_TAX = {
        'enabled': os.environ.get('STRIPE_AUTOMATIC_TAX_ENABLED', 'false').lower() == 'true'
    }
    STRIPE_TAX_BEHAVIOR = 'exclusive'
    STRIPE_TAX_CODE = 'txcd_99999999'  # General tax code
    
    # Stripe notification settings
    STRIPE_EMAIL_NOTIFICATIONS = {
        'invoice_payment_succeeded': True,
        'invoice_payment_failed': True,
        'customer_subscription_created': True,
        'customer_subscription_updated': True,
        'customer_subscription_deleted': True
    }
    
    # Email settings
    EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'resend').lower()
    
    # Resend settings
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
    RESEND_FROM_NAME = os.environ.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
    
    # SMTP settings (fallback)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Frontend URL
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://mingusapp.com')

    # Twilio SMS settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # MINGUS Support settings
    MINGUS_SUPPORT_PHONE = os.environ.get('MINGUS_SUPPORT_PHONE', '+1-800-MINGUS-1')
    MINGUS_SUPPORT_EMAIL = os.environ.get('MINGUS_SUPPORT_EMAIL', 'support@mingusapp.com')

    # Redis settings (for SMS rate limiting & tracking)
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    
    # =====================================================
    # CELERY & COMMUNICATION SYSTEM CONFIGURATION
    # =====================================================
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_ALWAYS_EAGER = os.environ.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_RESULT_EXPIRES = 3600  # 1 hour
    CELERY_TASK_IGNORE_RESULT = False
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # Celery queue configuration
    CELERY_TASK_DEFAULT_QUEUE = 'default'
    CELERY_TASK_DEFAULT_EXCHANGE = 'default'
    CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'
    
    # Celery task routes
    CELERY_TASK_ROUTES = {
        'backend.tasks.mingus_celery_tasks.*': {
            'queue': 'mingus_tasks',
            'routing_key': 'mingus_tasks'
        },
        'backend.tasks.communication_tasks.*': {
            'queue': 'communication_tasks',
            'routing_key': 'communication_tasks'
        }
    }
    
    # Celery beat schedule
    CELERY_BEAT_SCHEDULE = {
        'monitor-queue-depth': {
            'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
            'schedule': 300.0,  # Every 5 minutes
        },
        'track-delivery-rates': {
            'task': 'backend.tasks.mingus_celery_tasks.track_delivery_rates',
            'schedule': 600.0,  # Every 10 minutes
        },
        'analyze-user-engagement': {
            'task': 'backend.tasks.mingus_celery_tasks.analyze_user_engagement',
            'schedule': 3600.0,  # Every hour
        },
        'process-failed-messages': {
            'task': 'backend.tasks.mingus_celery_tasks.process_failed_messages',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'optimize-send-timing': {
            'task': 'backend.tasks.mingus_celery_tasks.optimize_send_timing',
            'schedule': 7200.0,  # Every 2 hours
        }
    }
    
    # Communication service configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    TWILIO_WEBHOOK_SECRET = os.environ.get('TWILIO_WEBHOOK_SECRET')
    
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
    RESEND_FROM_NAME = os.environ.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
    RESEND_WEBHOOK_SECRET = os.environ.get('RESEND_WEBHOOK_SECRET')
    
    # Communication rate limits
    SMS_RATE_LIMITS = {
        'critical': int(os.environ.get('SMS_CRITICAL_RATE_LIMIT', 500)),    # per minute
        'normal': int(os.environ.get('SMS_NORMAL_RATE_LIMIT', 100)),        # per minute
        'daily': int(os.environ.get('SMS_DAILY_RATE_LIMIT', 10000)),        # per day
        'hourly': int(os.environ.get('SMS_HOURLY_RATE_LIMIT', 1000))        # per hour
    }
    
    EMAIL_RATE_LIMITS = {
        'critical': int(os.environ.get('EMAIL_CRITICAL_RATE_LIMIT', 1000)),  # per minute
        'normal': int(os.environ.get('EMAIL_NORMAL_RATE_LIMIT', 200)),       # per minute
        'daily': int(os.environ.get('EMAIL_DAILY_RATE_LIMIT', 50000)),       # per day
        'hourly': int(os.environ.get('EMAIL_HOURLY_RATE_LIMIT', 5000))       # per hour
    }
    
    # Communication cost tracking
    COMMUNICATION_COSTS = {
        'sms': float(os.environ.get('SMS_COST_PER_MESSAGE', 0.05)),         # $0.05 per SMS
        'email': float(os.environ.get('EMAIL_COST_PER_MESSAGE', 0.001)),    # $0.001 per email
        'daily_budget': float(os.environ.get('COMMUNICATION_DAILY_BUDGET', 100.0)),  # $100 daily budget
        'monthly_budget': float(os.environ.get('COMMUNICATION_MONTHLY_BUDGET', 3000.0))  # $3000 monthly budget
    }
    
    # Communication frequency limits per user
    USER_COMMUNICATION_LIMITS = {
        'daily_max': int(os.environ.get('USER_DAILY_COMM_LIMIT', 5)),       # Max 5 communications per day
        'hourly_max': int(os.environ.get('USER_HOURLY_COMM_LIMIT', 2)),     # Max 2 communications per hour
        'weekly_max': int(os.environ.get('USER_WEEKLY_COMM_LIMIT', 20)),    # Max 20 communications per week
        'monthly_max': int(os.environ.get('USER_MONTHLY_COMM_LIMIT', 80))   # Max 80 communications per month
    }
    
    # Communication timing preferences
    COMMUNICATION_TIMING = {
        'business_hours_start': int(os.environ.get('BUSINESS_HOURS_START', 9)),   # 9 AM
        'business_hours_end': int(os.environ.get('BUSINESS_HOURS_END', 17)),      # 5 PM
        'timezone_default': os.environ.get('DEFAULT_TIMEZONE', 'UTC'),
        'weekend_communications': os.environ.get('WEEKEND_COMMUNICATIONS', 'false').lower() == 'true',
        'holiday_communications': os.environ.get('HOLIDAY_COMMUNICATIONS', 'false').lower() == 'true'
    }
    
    # Communication retry configuration
    COMMUNICATION_RETRY_CONFIG = {
        'max_retries': int(os.environ.get('COMM_MAX_RETRIES', 3)),
        'retry_delay': int(os.environ.get('COMM_RETRY_DELAY', 300)),  # 5 minutes
        'exponential_backoff': os.environ.get('COMM_EXPONENTIAL_BACKOFF', 'true').lower() == 'true',
        'retry_jitter': float(os.environ.get('COMM_RETRY_JITTER', 0.1))  # 10% jitter
    }
    
    # Communication analytics configuration
    COMMUNICATION_ANALYTICS = {
        'track_delivery_rates': True,
        'track_open_rates': True,
        'track_click_rates': True,
        'track_conversion_rates': True,
        'analytics_retention_days': int(os.environ.get('COMM_ANALYTICS_RETENTION', 365)),
        'enable_ab_testing': os.environ.get('COMM_AB_TESTING', 'true').lower() == 'true',
        'ab_test_sample_size': int(os.environ.get('COMM_AB_TEST_SAMPLE_SIZE', 1000))
    }
    
    # Communication compliance settings
    COMMUNICATION_COMPLIANCE = {
        'tcpa_compliance': True,
        'gdpr_compliance': True,
        'can_spam_compliance': True,
        'require_explicit_consent': True,
        'opt_out_required': True,
        'consent_audit_trail': True,
        'data_retention_days': int(os.environ.get('COMM_DATA_RETENTION', 2555))  # 7 years
    }
    
    # Communication webhook configuration
    COMMUNICATION_WEBHOOKS = {
        'twilio_webhook_url': os.environ.get('TWILIO_WEBHOOK_URL', '/webhooks/twilio'),
        'resend_webhook_url': os.environ.get('RESEND_WEBHOOK_URL', '/webhooks/resend'),
        'webhook_timeout': int(os.environ.get('WEBHOOK_TIMEOUT', 30)),  # 30 seconds
        'webhook_retries': int(os.environ.get('WEBHOOK_RETRIES', 3)),
        'webhook_secret_validation': True
    }
    
    # Communication monitoring and alerting
    COMMUNICATION_MONITORING = {
        'enable_delivery_monitoring': True,
        'enable_cost_monitoring': True,
        'enable_rate_limit_monitoring': True,
        'delivery_rate_threshold': float(os.environ.get('DELIVERY_RATE_THRESHOLD', 0.95)),  # 95%
        'cost_threshold_alert': float(os.environ.get('COST_THRESHOLD_ALERT', 50.0)),  # $50
        'rate_limit_alert_threshold': float(os.environ.get('RATE_LIMIT_ALERT_THRESHOLD', 0.8))  # 80%
    }
    
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
    
    # =====================================================
    # DATABASE MONITORING & PERFORMANCE
    # =====================================================
    
    # Database performance monitoring
    DB_PERFORMANCE_MONITORING = {
        'enable_query_monitoring': True,
        'enable_connection_monitoring': True,
        'enable_slow_query_logging': True,
        'slow_query_threshold_ms': 1000,
        'max_connections_warning': 80,
        'connection_timeout_warning_ms': 5000,
        'enable_metrics_collection': True,
        'metrics_retention_hours': 24,
    }
    
    # Database maintenance
    DB_MAINTENANCE = {
        'enable_auto_vacuum': True,
        'enable_auto_analyze': True,
        'vacuum_threshold': 50,  # Percentage of dead tuples
        'analyze_threshold': 10,  # Percentage of table changes
        'maintenance_window_start': '02:00',  # 2 AM UTC
        'maintenance_window_duration': 60,  # 1 hour
    }
    
    # Database backup configuration
    DB_BACKUP_CONFIG = {
        'enable_automated_backups': True,
        'backup_frequency_hours': 24,
        'backup_retention_days': 30,
        'backup_compression': True,
        'backup_encryption': True,
        'backup_verification': True,
        'backup_location': 'backups/database/',
        'backup_filename_pattern': 'mingus_backup_{timestamp}.sql.gz',
    }
    
    # Database security configuration
    DB_SECURITY_CONFIG = {
        'enable_ssl_connections': True,
        'require_ssl': os.environ.get('DB_REQUIRE_SSL', 'true').lower() == 'true',
        'ssl_cert_verification': True,
        'enable_connection_encryption': True,
        'enable_query_encryption': False,  # Handled at application level
        'max_failed_connections': 5,
        'connection_ban_duration_minutes': 30,
    } 