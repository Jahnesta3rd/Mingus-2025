# Celery Configuration for MINGUS Communication Tasks

import os
from kombu import Queue

# Broker settings
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Task routing with priorities
task_routes = {
    # SMS Tasks - High Priority
    'backend.tasks.mingus_celery_tasks.send_sms_critical': {'queue': 'sms_critical'},
    'backend.tasks.mingus_celery_tasks.send_sms_daily': {'queue': 'sms_daily'},
    
    # Email Tasks - Lower Priority
    'backend.tasks.mingus_celery_tasks.send_email_reports': {'queue': 'email_reports'},
    'backend.tasks.mingus_celery_tasks.send_email_education': {'queue': 'email_education'},
    
    # Legacy tasks for backward compatibility
    'backend.tasks.communication_tasks.route_and_send_message': {'queue': 'communication'},
    'backend.tasks.communication_tasks.send_financial_alert': {'queue': 'alerts'},
    'backend.tasks.communication_tasks.send_batch_messages': {'queue': 'batch'},
    'backend.tasks.communication_tasks.handle_delivery_fallback': {'queue': 'fallback'},
    'backend.tasks.communication_tasks.check_delivery_status': {'queue': 'monitoring'},
    'backend.tasks.communication_tasks.send_follow_up_email': {'queue': 'followup'},
    
    # New monitoring and analytics tasks
    'backend.tasks.mingus_celery_tasks.monitor_queue_depth': {'queue': 'monitoring'},
    'backend.tasks.mingus_celery_tasks.track_delivery_rates': {'queue': 'analytics'},
    'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {'queue': 'analytics'},
    'backend.tasks.mingus_celery_tasks.process_failed_messages': {'queue': 'fallback'},
    'backend.tasks.mingus_celery_tasks.optimize_send_timing': {'queue': 'optimization'},
}

# Queue definitions with priorities
task_queues = (
    # SMS Queues - High Priority
    Queue('sms_critical', routing_key='sms_critical', queue_arguments={'x-max-priority': 10}),
    Queue('sms_daily', routing_key='sms_daily', queue_arguments={'x-max-priority': 10}),
    
    # Email Queues - Lower Priority
    Queue('email_reports', routing_key='email_reports', queue_arguments={'x-max-priority': 10}),
    Queue('email_education', routing_key='email_education', queue_arguments={'x-max-priority': 10}),
    
    # Legacy queues
    Queue('communication', routing_key='communication', queue_arguments={'x-max-priority': 10}),
    Queue('alerts', routing_key='alerts', queue_arguments={'x-max-priority': 10}),
    Queue('batch', routing_key='batch', queue_arguments={'x-max-priority': 10}),
    Queue('fallback', routing_key='fallback', queue_arguments={'x-max-priority': 10}),
    Queue('monitoring', routing_key='monitoring', queue_arguments={'x-max-priority': 10}),
    Queue('followup', routing_key='followup', queue_arguments={'x-max-priority': 10}),
    
    # New queues
    Queue('analytics', routing_key='analytics', queue_arguments={'x-max-priority': 10}),
    Queue('optimization', routing_key='optimization', queue_arguments={'x-max-priority': 10}),
)

# Task serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
worker_disable_rate_limits = False

# Task execution settings
task_always_eager = False
task_eager_propagates = True
task_ignore_result = False
task_store_errors_even_if_ignored = True

# Result settings
result_expires = 3600  # 1 hour
result_persistent = True

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Task priority
task_queue_max_priority = 10
task_default_priority = 5

# Task time limits
task_soft_time_limit = 300  # 5 minutes
task_time_limit = 600  # 10 minutes

# Beat schedule for periodic tasks
beat_schedule = {
    # Monitoring tasks
    'monitor-queue-depth': {
        'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
        'schedule': 300.0,  # Every 5 minutes
    },
    'track-delivery-rates': {
        'task': 'backend.tasks.mingus_celery_tasks.track_delivery_rates',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'analyze-user-engagement': {
        'task': 'backend.tasks.mingus_celery_tasks.analyze_user_engagement',
        'schedule': 3600.0,  # Every hour
    },
    'process-failed-messages': {
        'task': 'backend.tasks.mingus_celery_tasks.process_failed_messages',
        'schedule': 900.0,  # Every 15 minutes
    },
    'optimize-send-timing': {
        'task': 'backend.tasks.mingus_celery_tasks.optimize_send_timing',
        'schedule': 7200.0,  # Every 2 hours
    },
    
    # Legacy tasks
    'check-delivery-status': {
        'task': 'backend.tasks.communication_tasks.check_delivery_status',
        'schedule': 300.0,  # Every 5 minutes
    },
    'send-batch-messages': {
        'task': 'backend.tasks.communication_tasks.send_batch_messages',
        'schedule': 3600.0,  # Every hour
    },
    'send-follow-up-emails': {
        'task': 'backend.tasks.communication_tasks.send_follow_up_email',
        'schedule': 86400.0,  # Every 24 hours
    },
}

# Task annotations for specific task configurations
task_annotations = {
    # SMS Critical Tasks - High priority, fast execution
    'backend.tasks.mingus_celery_tasks.send_sms_critical': {
        'rate_limit': '50/m',  # 50 per minute
        'time_limit': 30,  # 30 seconds
        'priority': 1,
        'max_retries': 3,
        'default_retry_delay': 60,
    },
    'backend.tasks.mingus_celery_tasks.send_sms_daily': {
        'rate_limit': '100/m',  # 100 per minute
        'time_limit': 60,  # 1 minute
        'priority': 3,
        'max_retries': 2,
        'default_retry_delay': 300,
    },
    
    # Email Tasks - Lower priority, more time
    'backend.tasks.mingus_celery_tasks.send_email_reports': {
        'rate_limit': '20/m',  # 20 per minute
        'time_limit': 120,  # 2 minutes
        'priority': 5,
        'max_retries': 2,
        'default_retry_delay': 600,
    },
    'backend.tasks.mingus_celery_tasks.send_email_education': {
        'rate_limit': '30/m',  # 30 per minute
        'time_limit': 180,  # 3 minutes
        'priority': 7,
        'max_retries': 2,
        'default_retry_delay': 900,
    },
    
    # Monitoring and Analytics Tasks
    'backend.tasks.mingus_celery_tasks.monitor_queue_depth': {
        'rate_limit': '12/m',  # 12 per minute
        'time_limit': 60,  # 1 minute
        'priority': 2,
        'max_retries': 1,
        'default_retry_delay': 300,
    },
    'backend.tasks.mingus_celery_tasks.track_delivery_rates': {
        'rate_limit': '4/m',  # 4 per minute
        'time_limit': 120,  # 2 minutes
        'priority': 4,
        'max_retries': 1,
        'default_retry_delay': 600,
    },
    'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {
        'rate_limit': '2/m',  # 2 per minute
        'time_limit': 300,  # 5 minutes
        'priority': 6,
        'max_retries': 1,
        'default_retry_delay': 1800,
    },
    'backend.tasks.mingus_celery_tasks.process_failed_messages': {
        'rate_limit': '10/m',  # 10 per minute
        'time_limit': 90,  # 1.5 minutes
        'priority': 2,
        'max_retries': 2,
        'default_retry_delay': 300,
    },
    'backend.tasks.mingus_celery_tasks.optimize_send_timing': {
        'rate_limit': '1/m',  # 1 per minute
        'time_limit': 600,  # 10 minutes
        'priority': 8,
        'max_retries': 1,
        'default_retry_delay': 3600,
    },
    
    # Legacy task configurations
    'backend.tasks.communication_tasks.send_financial_alert': {
        'rate_limit': '10/m',  # 10 per minute
        'time_limit': 120,  # 2 minutes
    },
    'backend.tasks.communication_tasks.route_and_send_message': {
        'rate_limit': '100/m',  # 100 per minute
        'time_limit': 60,  # 1 minute
    },
    'backend.tasks.communication_tasks.send_batch_messages': {
        'rate_limit': '10/m',  # 10 per minute
        'time_limit': 300,  # 5 minutes
    },
}

# Security settings
worker_direct = False
worker_send_task_events = True
task_send_sent_event = True

# Monitoring
event_queue_expires = 60
event_queue_ttl = 5.0
event_queue_maxsize = 10000

# Error handling
task_reject_on_worker_lost = True
task_acks_late = True
worker_cancel_long_running_tasks_on_connection_loss = True 