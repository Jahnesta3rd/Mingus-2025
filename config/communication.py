"""
Communication System Configuration
Dedicated configuration for MINGUS communication system
"""

import os
from datetime import timedelta
from config.base import Config
from config.secure_config import get_secure_config


class CommunicationConfig(Config):
    """Communication-specific configuration using secure configuration management"""
    
    def __init__(self):
        """Initialize communication configuration with secure config manager"""
        super().__init__()
        self._load_communication_config()
    
    def _load_communication_config(self):
        """Load communication-specific configuration"""
        # =====================================================
        # CELERY CONFIGURATION
        # =====================================================
        
        # Celery broker and backend
        self.CELERY_BROKER_URL = self.secure_config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.CELERY_RESULT_BACKEND = self.secure_config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        
        # Celery task configuration
        self.CELERY_ALWAYS_EAGER = self.secure_config.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true'
        self.CELERY_TASK_SERIALIZER = self.secure_config.get('CELERY_TASK_SERIALIZER', 'json')
        self.CELERY_ACCEPT_CONTENT = [self.secure_config.get('CELERY_ACCEPT_CONTENT', 'json')]
        self.CELERY_RESULT_SERIALIZER = self.secure_config.get('CELERY_RESULT_SERIALIZER', 'json')
        self.CELERY_TIMEZONE = self.secure_config.get('CELERY_TIMEZONE', 'UTC')
        self.CELERY_ENABLE_UTC = True
        self.CELERY_TASK_TRACK_STARTED = True
        self.CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
        self.CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
        self.CELERY_WORKER_PREFETCH_MULTIPLIER = 1
        self.CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
        self.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
        self.CELERY_RESULT_EXPIRES = 3600  # 1 hour
        self.CELERY_TASK_IGNORE_RESULT = False
        self.CELERY_TASK_EAGER_PROPAGATES = True
        
        # Celery queue configuration
        self.CELERY_TASK_DEFAULT_QUEUE = self.secure_config.get('CELERY_TASK_DEFAULT_QUEUE', 'default')
        self.CELERY_TASK_DEFAULT_EXCHANGE = self.secure_config.get('CELERY_TASK_DEFAULT_EXCHANGE', 'default')
        self.CELERY_TASK_DEFAULT_ROUTING_KEY = self.secure_config.get('CELERY_TASK_DEFAULT_ROUTING_KEY', 'default')
        
        # Celery task routes for communication system
        self.CELERY_TASK_ROUTES = {
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
        self.CELERY_BEAT_SCHEDULE = {
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
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER')
        self.TWILIO_WEBHOOK_SECRET = self.secure_config.get('TWILIO_WEBHOOK_SECRET')
        
        # Twilio configuration
        self.TWILIO_API_VERSION = '2010-04-01'
        self.TWILIO_TIMEOUT = int(self.secure_config.get('TWILIO_TIMEOUT', '30'))  # 30 seconds
        self.TWILIO_MAX_RETRIES = int(self.secure_config.get('TWILIO_MAX_RETRIES', '3'))
        self.TWILIO_RETRY_DELAY = int(self.secure_config.get('TWILIO_RETRY_DELAY', '5'))  # 5 seconds
        
        # SMS rate limits
        self.SMS_RATE_LIMITS = {
            'critical': int(self.secure_config.get('SMS_CRITICAL_RATE_LIMIT', '500')),    # per minute
            'normal': int(self.secure_config.get('SMS_NORMAL_RATE_LIMIT', '100')),        # per minute
            'daily': int(self.secure_config.get('SMS_DAILY_RATE_LIMIT', '10000')),        # per day
            'hourly': int(self.secure_config.get('SMS_HOURLY_RATE_LIMIT', '1000'))        # per hour
        }
        
        # SMS cost tracking
        self.SMS_COST_PER_MESSAGE = float(self.secure_config.get('SMS_COST_PER_MESSAGE', '0.05'))  # $0.05 per SMS
        self.SMS_COST_PER_MMS = float(self.secure_config.get('SMS_COST_PER_MMS', '0.10'))  # $0.10 per MMS
        
        # SMS message limits
        self.SMS_MAX_LENGTH = 160  # Standard SMS length
        self.SMS_MAX_LENGTH_UNICODE = 70  # Unicode SMS length
        self.SMS_MAX_SEGMENTS = 10  # Maximum segments for long messages
        
        # =====================================================
        # EMAIL CONFIGURATION (RESEND)
        # =====================================================
        
        # Resend API credentials
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.RESEND_FROM_NAME = self.secure_config.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        self.RESEND_WEBHOOK_SECRET = self.secure_config.get('RESEND_WEBHOOK_SECRET')
        
        # Resend configuration
        self.RESEND_TIMEOUT = int(self.secure_config.get('RESEND_TIMEOUT', '30'))  # 30 seconds
        self.RESEND_MAX_RETRIES = int(self.secure_config.get('RESEND_MAX_RETRIES', '3'))
        self.RESEND_RETRY_DELAY = int(self.secure_config.get('RESEND_RETRY_DELAY', '5'))  # 5 seconds
        
        # Email rate limits
        self.EMAIL_RATE_LIMITS = {
            'critical': int(self.secure_config.get('EMAIL_CRITICAL_RATE_LIMIT', '1000')),  # per minute
            'normal': int(self.secure_config.get('EMAIL_NORMAL_RATE_LIMIT', '200')),       # per minute
            'daily': int(self.secure_config.get('EMAIL_DAILY_RATE_LIMIT', '50000')),       # per day
            'hourly': int(self.secure_config.get('EMAIL_HOURLY_RATE_LIMIT', '5000'))       # per hour
        }
        
        # Email cost tracking
        self.EMAIL_COST_PER_MESSAGE = float(self.secure_config.get('EMAIL_COST_PER_MESSAGE', '0.001'))  # $0.001 per email
        
        # Email configuration
        self.EMAIL_MAX_RECIPIENTS = int(self.secure_config.get('EMAIL_MAX_RECIPIENTS', '100'))  # Max recipients per email
        self.EMAIL_MAX_ATTACHMENT_SIZE = int(self.secure_config.get('EMAIL_MAX_ATTACHMENT_SIZE', '10485760'))  # 10MB
        
        # =====================================================
        # COMMUNICATION COST TRACKING
        # =====================================================
        
        self.COMMUNICATION_COSTS = {
            'sms': self.SMS_COST_PER_MESSAGE,
            'email': self.EMAIL_COST_PER_MESSAGE,
            'daily_budget': float(self.secure_config.get('COMMUNICATION_DAILY_BUDGET', '100.0')),  # $100 daily budget
            'monthly_budget': float(self.secure_config.get('COMMUNICATION_MONTHLY_BUDGET', '3000.0')),  # $3000 monthly budget
            'alert_threshold': float(self.secure_config.get('COMMUNICATION_ALERT_THRESHOLD', '0.8'))  # 80% of budget
        }
        
        # =====================================================
        # USER COMMUNICATION LIMITS
        # =====================================================
        
        self.USER_COMMUNICATION_LIMITS = {
            'daily_max': int(self.secure_config.get('USER_DAILY_COMM_LIMIT', '5')),       # Max 5 communications per day
            'hourly_max': int(self.secure_config.get('USER_HOURLY_COMM_LIMIT', '2')),     # Max 2 communications per hour
            'weekly_max': int(self.secure_config.get('USER_WEEKLY_COMM_LIMIT', '20')),    # Max 20 communications per week
            'monthly_max': int(self.secure_config.get('USER_MONTHLY_COMM_LIMIT', '80')),  # Max 80 communications per month
            'sms_daily_max': int(self.secure_config.get('USER_SMS_DAILY_LIMIT', '3')),    # Max 3 SMS per day
            'email_daily_max': int(self.secure_config.get('USER_EMAIL_DAILY_LIMIT', '2')) # Max 2 emails per day
        }
        
        # =====================================================
        # COMMUNICATION TIMING PREFERENCES
        # =====================================================
        
        self.COMMUNICATION_TIMING = {
            'business_hours_start': int(self.secure_config.get('BUSINESS_HOURS_START', '9')),   # 9 AM
            'business_hours_end': int(self.secure_config.get('BUSINESS_HOURS_END', '17')),      # 5 PM
            'timezone_default': self.secure_config.get('DEFAULT_TIMEZONE', 'UTC'),
            'weekend_communications': self.secure_config.get('WEEKEND_COMMUNICATIONS', 'false').lower() == 'true',
            'holiday_communications': self.secure_config.get('HOLIDAY_COMMUNICATIONS', 'false').lower() == 'true',
            'quiet_hours_start': int(self.secure_config.get('QUIET_HOURS_START', '22')),        # 10 PM
            'quiet_hours_end': int(self.secure_config.get('QUIET_HOURS_END', '8')),             # 8 AM
            'timezone_aware': True
        }
        
        # =====================================================
        # COMMUNICATION RETRY CONFIGURATION
        # =====================================================
        
        self.COMMUNICATION_RETRY_CONFIG = {
            'max_retries': int(self.secure_config.get('COMM_MAX_RETRIES', '3')),
            'retry_delay': int(self.secure_config.get('COMM_RETRY_DELAY', '300')),  # 5 minutes
            'exponential_backoff': self.secure_config.get('COMM_EXPONENTIAL_BACKOFF', 'true').lower() == 'true',
            'retry_jitter': float(self.secure_config.get('COMM_RETRY_JITTER', '0.1')),  # 10% jitter
            'retry_on_failure': True,
            'retry_on_timeout': True,
            'retry_on_rate_limit': True
        }
        
        # =====================================================
        # COMMUNICATION ANALYTICS CONFIGURATION
        # =====================================================
        
        self.COMMUNICATION_ANALYTICS = {
            'track_delivery_rates': True,
            'track_open_rates': True,
            'track_click_rates': True,
            'track_conversion_rates': True,
            'track_bounce_rates': True,
            'track_unsubscribe_rates': True,
            'analytics_retention_days': int(self.secure_config.get('COMM_ANALYTICS_RETENTION', '365')),
            'enable_ab_testing': self.secure_config.get('COMM_AB_TESTING', 'true').lower() == 'true',
            'ab_test_sample_size': int(self.secure_config.get('COMM_AB_TEST_SAMPLE_SIZE', '1000')),
            'track_user_engagement': True,
            'track_financial_impact': True,
            'enable_real_time_tracking': True
        }
        
        # =====================================================
        # COMMUNICATION COMPLIANCE SETTINGS
        # =====================================================
        
        self.COMMUNICATION_COMPLIANCE = {
            'tcpa_compliance': True,
            'gdpr_compliance': True,
            'can_spam_compliance': True,
            'require_explicit_consent': True,
            'opt_out_required': True,
            'consent_audit_trail': True,
            'data_retention_days': int(self.secure_config.get('COMM_DATA_RETENTION', '2555')),  # 7 years
            'privacy_policy_url': self.secure_config.get('PRIVACY_POLICY_URL', 'https://mingusapp.com/privacy'),
            'terms_of_service_url': self.secure_config.get('TERMS_OF_SERVICE_URL', 'https://mingusapp.com/terms'),
            'unsubscribe_url': self.secure_config.get('UNSUBSCRIBE_URL', 'https://mingusapp.com/unsubscribe'),
            'preference_center_url': self.secure_config.get('PREFERENCE_CENTER_URL', 'https://mingusapp.com/preferences')
        }
        
        # =====================================================
        # COMMUNICATION WEBHOOK CONFIGURATION
        # =====================================================
        
        self.COMMUNICATION_WEBHOOKS = {
            'twilio_webhook_url': self.secure_config.get('TWILIO_WEBHOOK_URL', '/webhooks/twilio'),
            'resend_webhook_url': self.secure_config.get('RESEND_WEBHOOK_URL', '/webhooks/resend'),
            'webhook_timeout': int(self.secure_config.get('WEBHOOK_TIMEOUT', '30')),  # 30 seconds
            'webhook_retries': int(self.secure_config.get('WEBHOOK_RETRIES', '3')),
            'webhook_secret_validation': True,
            'webhook_rate_limiting': True,
            'webhook_logging': True
        }
        
        # =====================================================
        # COMMUNICATION MONITORING AND ALERTING
        # =====================================================
        
        self.COMMUNICATION_MONITORING = {
            'enable_delivery_monitoring': True,
            'enable_cost_monitoring': True,
            'enable_rate_limit_monitoring': True,
            'enable_performance_monitoring': True,
            'delivery_rate_threshold': float(self.secure_config.get('DELIVERY_RATE_THRESHOLD', '0.95')),  # 95%
            'cost_threshold_alert': float(self.secure_config.get('COST_THRESHOLD_ALERT', '50.0')),  # $50
            'rate_limit_alert_threshold': float(self.secure_config.get('RATE_LIMIT_ALERT_THRESHOLD', '0.8')),  # 80%
            'performance_threshold_ms': int(self.secure_config.get('PERFORMANCE_THRESHOLD_MS', '5000')),  # 5 seconds
            'alert_channels': ['email', 'slack'],  # Alert notification channels
            'alert_recipients': self.secure_config.get('ALERT_RECIPIENTS', 'alerts@mingusapp.com').split(',')
        }
        
        # =====================================================
        # COMMUNICATION TEMPLATES AND CONTENT
        # =====================================================
        
        self.COMMUNICATION_TEMPLATES = {
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
        
        self.COMMUNICATION_SECURITY = {
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
        
        self.COMMUNICATION_TESTING = {
            'enable_test_mode': self.secure_config.get('COMM_TEST_MODE', 'false').lower() == 'true',
            'test_recipients': self.secure_config.get('COMM_TEST_RECIPIENTS', 'test@example.com').split(','),
            'enable_mock_services': self.secure_config.get('COMM_MOCK_SERVICES', 'false').lower() == 'true',
            'enable_dry_run': self.secure_config.get('COMM_DRY_RUN', 'false').lower() == 'true',
            'test_message_prefix': '[TEST] ',
            'enable_debug_logging': self.secure_config.get('COMM_DEBUG_LOGGING', 'false').lower() == 'true'
        }


class DevelopmentCommunicationConfig(CommunicationConfig):
    """Development environment communication configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.CELERY_ALWAYS_EAGER = True
        self.COMMUNICATION_TESTING = {
            'enable_test_mode': True,
            'test_recipients': ['dev@mingusapp.com'],
            'enable_mock_services': True,
            'enable_dry_run': True,
            'test_message_prefix': '[DEV] ',
            'enable_debug_logging': True
        }


class ProductionCommunicationConfig(CommunicationConfig):
    """Production environment communication configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.CELERY_ALWAYS_EAGER = False
        self.COMMUNICATION_TESTING = {
            'enable_test_mode': False,
            'test_recipients': [],
            'enable_mock_services': False,
            'enable_dry_run': False,
            'test_message_prefix': '',
            'enable_debug_logging': False
        }


class TestingCommunicationConfig(CommunicationConfig):
    """Testing environment communication configuration"""
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.CELERY_ALWAYS_EAGER = True
        self.COMMUNICATION_TESTING = {
            'enable_test_mode': True,
            'test_recipients': ['test@mingusapp.com'],
            'enable_mock_services': True,
            'enable_dry_run': True,
            'test_message_prefix': '[TEST] ',
            'enable_debug_logging': True
        } 