"""
Production Celery Configuration for MINGUS Application
Optimized for high-performance task processing with proper queue management
"""

import os
import multiprocessing
from kombu import Queue, Exchange

# =====================================================
# BROKER AND BACKEND CONFIGURATION
# =====================================================

# Broker settings - production optimized
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Broker connection settings - production values
broker_connection_retry_on_startup = True
broker_connection_max_retries = 10
broker_connection_retry_delay = 5.0
broker_pool_limit = int(os.getenv('CELERY_BROKER_POOL_LIMIT', 20))
broker_heartbeat = int(os.getenv('CELERY_BROKER_HEARTBEAT', 10))

# =====================================================
# WORKER CONFIGURATION
# =====================================================

# Worker processes - production optimized
worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', max(4, multiprocessing.cpu_count())))
worker_prefetch_multiplier = int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', 1))
worker_max_tasks_per_child = int(os.getenv('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000))
worker_disable_rate_limits = os.getenv('CELERY_WORKER_DISABLE_RATE_LIMITS', 'false').lower() == 'true'

# Worker pool settings
worker_pool = os.getenv('CELERY_WORKER_POOL', 'prefork')
worker_pool_restarts = True
worker_pool_restarts_always = False

# =====================================================
# TASK CONFIGURATION
# =====================================================

# Task serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
result_compression = 'gzip'

# Task execution settings - production optimized
task_always_eager = False
task_eager_propagates = True
task_ignore_result = False
task_store_errors_even_if_ignored = True
task_annotations = {
    '*': {
        'rate_limit': '100/m',
        'time_limit': 1800,  # 30 minutes
        'soft_time_limit': 1500,  # 25 minutes
    }
}

# =====================================================
# TASK ROUTING FOR MINGUS
# =====================================================

# Task routing with priorities for MINGUS
task_routes = {
    # SMS Tasks - High Priority
    'backend.tasks.mingus_celery_tasks.send_sms_critical': {
        'queue': 'sms_critical',
        'routing_key': 'sms_critical'
    },
    'backend.tasks.mingus_celery_tasks.send_sms_daily': {
        'queue': 'sms_daily',
        'routing_key': 'sms_daily'
    },
    
    # Email Tasks - Medium Priority
    'backend.tasks.mingus_celery_tasks.send_email_reports': {
        'queue': 'email_reports',
        'routing_key': 'email_reports'
    },
    'backend.tasks.mingus_celery_tasks.send_email_education': {
        'queue': 'email_education',
        'routing_key': 'email_education'
    },
    
    # Analytics Tasks - Lower Priority
    'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {
        'queue': 'analytics',
        'routing_key': 'analytics'
    },
    'backend.tasks.mingus_celery_tasks.track_delivery_rates': {
        'queue': 'analytics',
        'routing_key': 'analytics'
    },
    
    # Monitoring Tasks - System Priority
    'backend.tasks.mingus_celery_tasks.monitor_queue_depth': {
        'queue': 'monitoring',
        'routing_key': 'monitoring'
    },
    
    # Optimization Tasks - Background Priority
    'backend.tasks.mingus_celery_tasks.optimize_send_timing': {
        'queue': 'optimization',
        'routing_key': 'optimization'
    },
    
    # Communication Tasks - Legacy support
    'backend.tasks.communication_tasks.*': {
        'queue': 'communication',
        'routing_key': 'communication'
    },
    'backend.tasks.communication_tasks.send_financial_alert': {
        'queue': 'alerts',
        'routing_key': 'alerts'
    },
}

# =====================================================
# QUEUE CONFIGURATION WITH PRIORITIES
# =====================================================

# Queue definitions with priorities for MINGUS
task_queues = (
    # SMS Queues - Highest Priority (1-2)
    Queue('sms_critical', 
          Exchange('sms_critical'), 
          routing_key='sms_critical',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('sms_daily', 
          Exchange('sms_daily'), 
          routing_key='sms_daily',
          queue_arguments={'x-max-priority': 10}),
    
    # Email Queues - Medium Priority (3-4)
    Queue('email_reports', 
          Exchange('email_reports'), 
          routing_key='email_reports',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('email_education', 
          Exchange('email_education'), 
          routing_key='email_education',
          queue_arguments={'x-max-priority': 10}),
    
    # Analytics Queue - Lower Priority (5-6)
    Queue('analytics', 
          Exchange('analytics'), 
          routing_key='analytics',
          queue_arguments={'x-max-priority': 10}),
    
    # Monitoring Queue - System Priority (7-8)
    Queue('monitoring', 
          Exchange('monitoring'), 
          routing_key='monitoring',
          queue_arguments={'x-max-priority': 10}),
    
    # Optimization Queue - Background Priority (9-10)
    Queue('optimization', 
          Exchange('optimization'), 
          routing_key='optimization',
          queue_arguments={'x-max-priority': 10}),
    
    # Legacy queues for backward compatibility
    Queue('communication', 
          Exchange('communication'), 
          routing_key='communication',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('alerts', 
          Exchange('alerts'), 
          routing_key='alerts',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('batch', 
          Exchange('batch'), 
          routing_key='batch',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('fallback', 
          Exchange('fallback'), 
          routing_key='fallback',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('followup', 
          Exchange('followup'), 
          routing_key='followup',
          queue_arguments={'x-max-priority': 10}),
)

# Default queue
task_default_queue = 'default'
task_default_exchange = 'default'
task_default_routing_key = 'default'

# =====================================================
# RESULT BACKEND CONFIGURATION
# =====================================================

# Result settings - production optimized
result_expires = int(os.getenv('CELERY_RESULT_EXPIRES', 3600))  # 1 hour
result_persistent = True
result_compression = 'gzip'
result_chord_join_timeout = 3600
result_chord_retry_interval = 1

# =====================================================
# LOGGING CONFIGURATION
# =====================================================

# Logging settings - production optimized
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
worker_log_color = False

# Log levels
worker_log_level = os.getenv('CELERY_WORKER_LOG_LEVEL', 'INFO')
worker_redirect_stdouts = True
worker_redirect_stdouts_level = 'WARNING'

# =====================================================
# MONITORING AND METRICS
# =====================================================

# Enable monitoring - production settings
worker_send_task_events = True
task_send_sent_event = True
event_queue_expires = 60
event_queue_ttl = 5.0
event_queue_maxsize = 10000

# Statsd configuration for metrics
statsd_host = os.getenv('STATSD_HOST')
statsd_port = int(os.getenv('STATSD_PORT', 8125))
statsd_prefix = os.getenv('STATSD_PREFIX', 'mingus.celery')

# =====================================================
# SECURITY CONFIGURATION
# =====================================================

# Security settings
security_key = os.getenv('CELERY_SECURITY_KEY')
security_certificate = os.getenv('CELERY_SECURITY_CERTIFICATE')
security_cert_store = os.getenv('CELERY_SECURITY_CERT_STORE')

# =====================================================
# TIMEZONE AND LOCALE
# =====================================================

# Timezone settings
timezone = 'UTC'
enable_utc = True

# =====================================================
# WORKER-SPECIFIC CONFIGURATIONS FOR MINGUS
# =====================================================

# SMS Worker Configuration - High Priority
if os.getenv('CELERY_WORKER_TYPE') == 'sms':
    worker_concurrency = int(os.getenv('SMS_WORKER_CONCURRENCY', 2))
    worker_queues = ['sms_critical', 'sms_daily']
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 500
    task_annotations = {
        '*': {
            'rate_limit': '50/m',
            'time_limit': 300,  # 5 minutes
            'soft_time_limit': 240,  # 4 minutes
        }
    }

# Email Worker Configuration - Medium Priority
elif os.getenv('CELERY_WORKER_TYPE') == 'email':
    worker_concurrency = int(os.getenv('EMAIL_WORKER_CONCURRENCY', 3))
    worker_queues = ['email_reports', 'email_education']
    worker_prefetch_multiplier = 2
    worker_max_tasks_per_child = 750
    task_annotations = {
        '*': {
            'rate_limit': '30/m',
            'time_limit': 600,  # 10 minutes
            'soft_time_limit': 540,  # 9 minutes
        }
    }

# Analytics Worker Configuration - Lower Priority
elif os.getenv('CELERY_WORKER_TYPE') == 'analytics':
    worker_concurrency = int(os.getenv('ANALYTICS_WORKER_CONCURRENCY', 2))
    worker_queues = ['analytics']
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 250
    task_annotations = {
        '*': {
            'rate_limit': '20/m',
            'time_limit': 1800,  # 30 minutes
            'soft_time_limit': 1500,  # 25 minutes
        }
    }

# Monitoring Worker Configuration - System Priority
elif os.getenv('CELERY_WORKER_TYPE') == 'monitoring':
    worker_concurrency = int(os.getenv('MONITORING_WORKER_CONCURRENCY', 1))
    worker_queues = ['monitoring']
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 100
    task_annotations = {
        '*': {
            'rate_limit': '10/m',
            'time_limit': 300,  # 5 minutes
            'soft_time_limit': 240,  # 4 minutes
        }
    }

# Optimization Worker Configuration - Background Priority
elif os.getenv('CELERY_WORKER_TYPE') == 'optimization':
    worker_concurrency = int(os.getenv('OPTIMIZATION_WORKER_CONCURRENCY', 1))
    worker_queues = ['optimization']
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 100
    task_annotations = {
        '*': {
            'rate_limit': '5/m',
            'time_limit': 3600,  # 1 hour
            'soft_time_limit': 3300,  # 55 minutes
        }
    }

# Default Worker Configuration (handles all queues)
else:
    worker_queues = ['default', 'communication', 'alerts', 'batch', 'fallback', 'followup']
    worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', 4))

# =====================================================
# PRODUCTION-SPECIFIC OVERRIDES
# =====================================================

# Production-specific settings
if os.getenv('FLASK_ENV') == 'production':
    # Increase concurrency for production
    worker_concurrency = max(worker_concurrency, 4)
    
    # Enable more detailed logging
    worker_log_level = 'INFO'
    
    # Increase task limits for production
    worker_max_tasks_per_child = max(worker_max_tasks_per_child, 1000)
    
    # Enable task events for monitoring
    worker_send_task_events = True
    task_send_sent_event = True
    
    # Production security settings
    if security_key:
        security_certificate = security_certificate or '/app/ssl/celery.crt'
        security_cert_store = security_cert_store or '/app/ssl/celery_ca.crt'

# =====================================================
# FINAL CONFIGURATION VALIDATION
# =====================================================

# Validate configuration
if worker_concurrency < 1:
    worker_concurrency = 1

if worker_max_tasks_per_child < 1:
    worker_max_tasks_per_child = 100

if worker_prefetch_multiplier < 1:
    worker_prefetch_multiplier = 1

# Log final configuration
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("MINGUS PRODUCTION CELERY CONFIGURATION")
logger.info("=" * 60)
logger.info(f"Worker Type: {os.getenv('CELERY_WORKER_TYPE', 'default')}")
logger.info(f"Concurrency: {worker_concurrency}")
logger.info(f"Queues: {worker_queues}")
logger.info(f"Max Tasks Per Child: {worker_max_tasks_per_child}")
logger.info(f"Prefetch Multiplier: {worker_prefetch_multiplier}")
logger.info(f"Broker URL: {broker_url}")
logger.info(f"Result Backend: {result_backend}")
logger.info("=" * 60) 