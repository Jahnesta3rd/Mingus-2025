"""
Communication System Configuration
Dedicated configuration for MINGUS communication system
"""

import os
from datetime import timedelta
from config.base import Config


class CommunicationConfig(Config):
    """Communication-specific configuration"""
    
    # =====================================================
    # CELERY CONFIGURATION
    # =====================================================
    
    # Celery broker and backend
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Celery task configuration
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
    
    # Celery task routes for communication system
    CELERY_TASK_ROUTES = {
        'backend.tasks.mingus_celery_tasks.send_critical_financial_alert': {
            'queue': 'sms_critical',
            'routing_key': 'sms.critical'
        },
        'backend.tasks.mingus_celery_tasks.send_payment_reminder': {
            'queue': 'sms_daily',
            'routing_key': 'sms.daily'
        },
        'backend.tasks.mingus_celery_tasks.send_weekly_checkin': {
            'queue': 'sms_daily',
            'routing_key': 'sms.daily'
        },
        'backend.tasks.mingus_celery_tasks.send_milestone_reminder': {
            'queue': 'sms_daily',
            'routing_key': 'sms.daily'
        },
        'backend.tasks.mingus_celery_tasks.send_monthly_report': {
            'queue': 'email_reports',
            'routing_key': 'email.reports'
        },
        'backend.tasks.mingus_celery_tasks.send_career_insights': {
            'queue': 'email_education',
            'routing_key': 'email.education'
        },
        'backend.tasks.mingus_celery_tasks.send_educational_content': {
            'queue': 'email_education',
            'routing_key': 'email.education'
        },
        'backend.tasks.mingus_celery_tasks.send_onboarding_sequence': {
            'queue': 'email_education',
            'routing_key': 'email.education'
        },
        'backend.tasks.mingus_celery_tasks.monitor_queue_depth': {
            'queue': 'analytics',
            'routing_key': 'analytics.monitoring'
        },
        'backend.tasks.mingus_celery_tasks.track_delivery_rates': {
            'queue': 'analytics',
            'routing_key': 'analytics.tracking'
        },
        'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {
            'queue': 'analytics',
            'routing_key': 'analytics.engagement'
        },
        'backend.tasks.mingus_celery_tasks.process_failed_messages': {
            'queue': 'optimization',
            'routing_key': 'optimization.failed'
        },
        'backend.tasks.mingus_celery_tasks.optimize_send_timing': {
            'queue': 'optimization',
            'routing_key': 'optimization.timing'
        }
    }
    
    # Celery beat schedule for communication tasks
    CELERY_BEAT_SCHEDULE = {
        'monitor-queue-depth': {
            'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
            'schedule': 300.0,  # Every 5 minutes
            'options': {'queue': 'analytics'}
        },
        'track-delivery-rates': {
            'task': 'backend.tasks.mingus_celery_tasks.track_delivery_rates',
            'schedule': 600.0,  # Every 10 minutes
            'options': {'queue': 'analytics'}
        },
        'analyze-user-engagement': {
            'task': 'backend.tasks.mingus_celery_tasks.analyze_user_engagement',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'analytics'}
        },
        'process-failed-messages': {
            'task': 'backend.tasks.mingus_celery_tasks.process_failed_messages',
            'schedule': 1800.0,  # Every 30 minutes
            'options': {'queue': 'optimization'}
        },
        'optimize-send-timing': {
            'task': 'backend.tasks.mingus_celery_tasks.optimize_send_timing',
            'schedule': 7200.0,  # Every 2 hours
            'options': {'queue': 'optimization'}
        },
        'send-weekly-checkins': {
            'task': 'backend.tasks.mingus_celery_tasks.send_weekly_checkin',
            'schedule': 604800.0,  # Every week (7 days)
            'options': {'queue': 'sms_daily'}
        },
        'send-monthly-reports': {
            'task': 'backend.tasks.mingus_celery_tasks.send_monthly_report',
            'schedule': 2592000.0,  # Every month (30 days)
            'options': {'queue': 'email_reports'}
        }
    }
    
    # =====================================================
    # SMS CONFIGURATION (TWILIO)
    # =====================================================
    
    # Twilio API credentials
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    TWILIO_WEBHOOK_SECRET = os.environ.get('TWILIO_WEBHOOK_SECRET')
    
    # Twilio configuration
    TWILIO_API_VERSION = '2010-04-01'
    TWILIO_TIMEOUT = int(os.environ.get('TWILIO_TIMEOUT', 30))  # 30 seconds
    TWILIO_MAX_RETRIES = int(os.environ.get('TWILIO_MAX_RETRIES', 3))
    TWILIO_RETRY_DELAY = int(os.environ.get('TWILIO_RETRY_DELAY', 5))  # 5 seconds
    
    # SMS rate limits
    SMS_RATE_LIMITS = {
        'critical': int(os.environ.get('SMS_CRITICAL_RATE_LIMIT', 500)),    # per minute
        'normal': int(os.environ.get('SMS_NORMAL_RATE_LIMIT', 100)),        # per minute
        'daily': int(os.environ.get('SMS_DAILY_RATE_LIMIT', 10000)),        # per day
        'hourly': int(os.environ.get('SMS_HOURLY_RATE_LIMIT', 1000))        # per hour
    }
    
    # SMS cost tracking
    SMS_COST_PER_MESSAGE = float(os.environ.get('SMS_COST_PER_MESSAGE', 0.05))  # $0.05 per SMS
    SMS_COST_PER_MMS = float(os.environ.get('SMS_COST_PER_MMS', 0.10))  # $0.10 per MMS
    
    # SMS message limits
    SMS_MAX_LENGTH = 160  # Standard SMS length
    SMS_MAX_LENGTH_UNICODE = 70  # Unicode SMS length
    SMS_MAX_SEGMENTS = 10  # Maximum segments for long messages
    
    # =====================================================
    # EMAIL CONFIGURATION (RESEND)
    # =====================================================
    
    # Resend API credentials
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
    RESEND_FROM_NAME = os.environ.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
    RESEND_WEBHOOK_SECRET = os.environ.get('RESEND_WEBHOOK_SECRET')
    
    # Resend configuration
    RESEND_TIMEOUT = int(os.environ.get('RESEND_TIMEOUT', 30))  # 30 seconds
    RESEND_MAX_RETRIES = int(os.environ.get('RESEND_MAX_RETRIES', 3))
    RESEND_RETRY_DELAY = int(os.environ.get('RESEND_RETRY_DELAY', 5))  # 5 seconds
    
    # Email rate limits
    EMAIL_RATE_LIMITS = {
        'critical': int(os.environ.get('EMAIL_CRITICAL_RATE_LIMIT', 1000)),  # per minute
        'normal': int(os.environ.get('EMAIL_NORMAL_RATE_LIMIT', 200)),       # per minute
        'daily': int(os.environ.get('EMAIL_DAILY_RATE_LIMIT', 50000)),       # per day
        'hourly': int(os.environ.get('EMAIL_HOURLY_RATE_LIMIT', 5000))       # per hour
    }
    
    # Email cost tracking
    EMAIL_COST_PER_MESSAGE = float(os.environ.get('EMAIL_COST_PER_MESSAGE', 0.001))  # $0.001 per email
    
    # Email configuration
    EMAIL_MAX_RECIPIENTS = int(os.environ.get('EMAIL_MAX_RECIPIENTS', 100))  # Max recipients per email
    EMAIL_MAX_ATTACHMENT_SIZE = int(os.environ.get('EMAIL_MAX_ATTACHMENT_SIZE', 10485760))  # 10MB
    
    # =====================================================
    # COMMUNICATION COST TRACKING
    # =====================================================
    
    COMMUNICATION_COSTS = {
        'sms': SMS_COST_PER_MESSAGE,
        'email': EMAIL_COST_PER_MESSAGE,
        'daily_budget': float(os.environ.get('COMMUNICATION_DAILY_BUDGET', 100.0)),  # $100 daily budget
        'monthly_budget': float(os.environ.get('COMMUNICATION_MONTHLY_BUDGET', 3000.0)),  # $3000 monthly budget
        'alert_threshold': float(os.environ.get('COMMUNICATION_ALERT_THRESHOLD', 0.8))  # 80% of budget
    }
    
    # =====================================================
    # USER COMMUNICATION LIMITS
    # =====================================================
    
    USER_COMMUNICATION_LIMITS = {
        'daily_max': int(os.environ.get('USER_DAILY_COMM_LIMIT', 5)),       # Max 5 communications per day
        'hourly_max': int(os.environ.get('USER_HOURLY_COMM_LIMIT', 2)),     # Max 2 communications per hour
        'weekly_max': int(os.environ.get('USER_WEEKLY_COMM_LIMIT', 20)),    # Max 20 communications per week
        'monthly_max': int(os.environ.get('USER_MONTHLY_COMM_LIMIT', 80)),  # Max 80 communications per month
        'sms_daily_max': int(os.environ.get('USER_SMS_DAILY_LIMIT', 3)),    # Max 3 SMS per day
        'email_daily_max': int(os.environ.get('USER_EMAIL_DAILY_LIMIT', 2)) # Max 2 emails per day
    }
    
    # =====================================================
    # COMMUNICATION TIMING PREFERENCES
    # =====================================================
    
    COMMUNICATION_TIMING = {
        'business_hours_start': int(os.environ.get('BUSINESS_HOURS_START', 9)),   # 9 AM
        'business_hours_end': int(os.environ.get('BUSINESS_HOURS_END', 17)),      # 5 PM
        'timezone_default': os.environ.get('DEFAULT_TIMEZONE', 'UTC'),
        'weekend_communications': os.environ.get('WEEKEND_COMMUNICATIONS', 'false').lower() == 'true',
        'holiday_communications': os.environ.get('HOLIDAY_COMMUNICATIONS', 'false').lower() == 'true',
        'quiet_hours_start': int(os.environ.get('QUIET_HOURS_START', 22)),        # 10 PM
        'quiet_hours_end': int(os.environ.get('QUIET_HOURS_END', 8)),             # 8 AM
        'timezone_aware': True
    }
    
    # =====================================================
    # COMMUNICATION RETRY CONFIGURATION
    # =====================================================
    
    COMMUNICATION_RETRY_CONFIG = {
        'max_retries': int(os.environ.get('COMM_MAX_RETRIES', 3)),
        'retry_delay': int(os.environ.get('COMM_RETRY_DELAY', 300)),  # 5 minutes
        'exponential_backoff': os.environ.get('COMM_EXPONENTIAL_BACKOFF', 'true').lower() == 'true',
        'retry_jitter': float(os.environ.get('COMM_RETRY_JITTER', 0.1)),  # 10% jitter
        'retry_on_failure': True,
        'retry_on_timeout': True,
        'retry_on_rate_limit': True
    }
    
    # =====================================================
    # COMMUNICATION ANALYTICS CONFIGURATION
    # =====================================================
    
    COMMUNICATION_ANALYTICS = {
        'track_delivery_rates': True,
        'track_open_rates': True,
        'track_click_rates': True,
        'track_conversion_rates': True,
        'track_bounce_rates': True,
        'track_unsubscribe_rates': True,
        'analytics_retention_days': int(os.environ.get('COMM_ANALYTICS_RETENTION', 365)),
        'enable_ab_testing': os.environ.get('COMM_AB_TESTING', 'true').lower() == 'true',
        'ab_test_sample_size': int(os.environ.get('COMM_AB_TEST_SAMPLE_SIZE', 1000)),
        'track_user_engagement': True,
        'track_financial_impact': True,
        'enable_real_time_tracking': True
    }
    
    # =====================================================
    # COMMUNICATION COMPLIANCE SETTINGS
    # =====================================================
    
    COMMUNICATION_COMPLIANCE = {
        'tcpa_compliance': True,
        'gdpr_compliance': True,
        'can_spam_compliance': True,
        'require_explicit_consent': True,
        'opt_out_required': True,
        'consent_audit_trail': True,
        'data_retention_days': int(os.environ.get('COMM_DATA_RETENTION', 2555)),  # 7 years
        'privacy_policy_url': os.environ.get('PRIVACY_POLICY_URL', 'https://mingusapp.com/privacy'),
        'terms_of_service_url': os.environ.get('TERMS_OF_SERVICE_URL', 'https://mingusapp.com/terms'),
        'unsubscribe_url': os.environ.get('UNSUBSCRIBE_URL', 'https://mingusapp.com/unsubscribe'),
        'preference_center_url': os.environ.get('PREFERENCE_CENTER_URL', 'https://mingusapp.com/preferences')
    }
    
    # =====================================================
    # COMMUNICATION WEBHOOK CONFIGURATION
    # =====================================================
    
    COMMUNICATION_WEBHOOKS = {
        'twilio_webhook_url': os.environ.get('TWILIO_WEBHOOK_URL', '/webhooks/twilio'),
        'resend_webhook_url': os.environ.get('RESEND_WEBHOOK_URL', '/webhooks/resend'),
        'webhook_timeout': int(os.environ.get('WEBHOOK_TIMEOUT', 30)),  # 30 seconds
        'webhook_retries': int(os.environ.get('WEBHOOK_RETRIES', 3)),
        'webhook_secret_validation': True,
        'webhook_rate_limiting': True,
        'webhook_logging': True
    }
    
    # =====================================================
    # COMMUNICATION MONITORING AND ALERTING
    # =====================================================
    
    COMMUNICATION_MONITORING = {
        'enable_delivery_monitoring': True,
        'enable_cost_monitoring': True,
        'enable_rate_limit_monitoring': True,
        'enable_performance_monitoring': True,
        'delivery_rate_threshold': float(os.environ.get('DELIVERY_RATE_THRESHOLD', 0.95)),  # 95%
        'cost_threshold_alert': float(os.environ.get('COST_THRESHOLD_ALERT', 50.0)),  # $50
        'rate_limit_alert_threshold': float(os.environ.get('RATE_LIMIT_ALERT_THRESHOLD', 0.8)),  # 80%
        'performance_threshold_ms': int(os.environ.get('PERFORMANCE_THRESHOLD_MS', 5000)),  # 5 seconds
        'alert_channels': ['email', 'slack'],  # Alert notification channels
        'alert_recipients': os.environ.get('ALERT_RECIPIENTS', 'alerts@mingusapp.com').split(',')
    }
    
    # =====================================================
    # COMMUNICATION TEMPLATES AND CONTENT
    # =====================================================
    
    COMMUNICATION_TEMPLATES = {
        'enable_template_engine': True,
        'template_cache_enabled': True,
        'template_cache_ttl': 3600,  # 1 hour
        'default_language': 'en',
        'supported_languages': ['en', 'es', 'fr'],
        'template_variables': {
            'app_name': 'MINGUS',
            'app_url': 'https://mingusapp.com',
            'support_email': 'support@mingusapp.com',
            'support_phone': '+1-800-MINGUS-1'
        }
    }
    
    # =====================================================
    # COMMUNICATION SECURITY SETTINGS
    # =====================================================
    
    COMMUNICATION_SECURITY = {
        'enable_content_filtering': True,
        'enable_spam_protection': True,
        'enable_rate_limiting': True,
        'enable_ip_whitelisting': False,
        'enable_encryption': True,
        'enable_audit_logging': True,
        'max_message_size': 1024 * 1024,  # 1MB
        'allowed_file_types': ['.pdf', '.jpg', '.png', '.txt'],
        'blocked_content_patterns': [
            r'\b(spam|scam|phishing)\b',
            r'\b(credit\s*card\s*number|ssn|password)\b'
        ]
    }
    
    # =====================================================
    # COMMUNICATION TESTING AND DEVELOPMENT
    # =====================================================
    
    COMMUNICATION_TESTING = {
        'enable_test_mode': os.environ.get('COMM_TEST_MODE', 'false').lower() == 'true',
        'test_phone_numbers': os.environ.get('TEST_PHONE_NUMBERS', '+1234567890').split(','),
        'test_email_addresses': os.environ.get('TEST_EMAIL_ADDRESSES', 'test@mingusapp.com').split(','),
        'enable_mock_services': os.environ.get('COMM_MOCK_SERVICES', 'false').lower() == 'true',
        'enable_debug_logging': os.environ.get('COMM_DEBUG_LOGGING', 'false').lower() == 'true',
        'enable_performance_profiling': os.environ.get('COMM_PERFORMANCE_PROFILING', 'false').lower() == 'true'
    }


# Environment-specific configurations
class DevelopmentCommunicationConfig(CommunicationConfig):
    """Development environment communication configuration"""
    DEBUG = True
    CELERY_ALWAYS_EAGER = True
    COMMUNICATION_TESTING = {
        **CommunicationConfig.COMMUNICATION_TESTING,
        'enable_test_mode': True,
        'enable_mock_services': True,
        'enable_debug_logging': True
    }


class ProductionCommunicationConfig(CommunicationConfig):
    """Production environment communication configuration"""
    DEBUG = False
    CELERY_ALWAYS_EAGER = False
    COMMUNICATION_TESTING = {
        **CommunicationConfig.COMMUNICATION_TESTING,
        'enable_test_mode': False,
        'enable_mock_services': False,
        'enable_debug_logging': False
    }


class TestingCommunicationConfig(CommunicationConfig):
    """Testing environment communication configuration"""
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    COMMUNICATION_TESTING = {
        **CommunicationConfig.COMMUNICATION_TESTING,
        'enable_test_mode': True,
        'enable_mock_services': True,
        'enable_debug_logging': True
    } 