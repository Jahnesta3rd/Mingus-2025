"""
Celery Configuration for MINGUS Communication System
Comprehensive Celery setup with Flask integration, task routing, and monitoring
"""

import os
import logging
from datetime import timedelta
from typing import Dict, Any, Optional

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def create_celery_app(flask_app=None) -> Celery:
    """
    Create and configure Celery application with Flask integration
    
    Args:
        flask_app: Flask application instance (optional)
    
    Returns:
        Configured Celery application
    """
    
    # Create Celery app
    celery_app = Celery(
        'mingus_communication',
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        include=[
            'backend.tasks.mingus_celery_tasks',
            'backend.tasks.communication_tasks',
            'backend.tasks.analytics_tasks',
            'backend.tasks.monitoring_tasks'
        ]
    )
    
    # Configure Celery
    celery_app.conf.update(
        # Basic Configuration
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Task Configuration
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        task_ignore_result=False,
        task_eager_propagates=True,
        
        # Worker Configuration
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_disable_rate_limits=False,
        worker_hijack_root_logger=False,
        
        # Queue Configuration
        task_default_queue='mingus_tasks',
        task_default_exchange='mingus_exchange',
        task_default_routing_key='mingus.tasks',
        
        # Result Configuration
        result_expires=timedelta(hours=24),
        result_persistent=True,
        
        # Broker Configuration
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        broker_connection_max_retries=10,
        broker_pool_limit=10,
        broker_heartbeat=10,
        
        # Redis Specific Configuration
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'fanout_prefix': True,
            'fanout_patterns': True,
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
            'retry_on_timeout': True,
        },
        
        # Result Backend Configuration
        result_backend_transport_options={
            'retry_policy': {
                'timeout': 5.0
            },
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
        },
        
        # Task Routing Configuration
        task_routes={
            # Communication Tasks
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
            
            # Email Tasks
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
            
            # Analytics Tasks
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
                'routing_key': 'analytics.analysis'
            },
            'backend.tasks.mingus_celery_tasks.process_failed_messages': {
                'queue': 'optimization',
                'routing_key': 'optimization.failed'
            },
            'backend.tasks.mingus_celery_tasks.optimize_send_timing': {
                'queue': 'optimization',
                'routing_key': 'optimization.timing'
            },
            
            # Legacy Tasks (for backward compatibility)
            'backend.tasks.communication_tasks.*': {
                'queue': 'communication_tasks',
                'routing_key': 'communication.tasks'
            },
            'backend.tasks.analytics_tasks.*': {
                'queue': 'analytics',
                'routing_key': 'analytics.tasks'
            },
            'backend.tasks.monitoring_tasks.*': {
                'queue': 'monitoring',
                'routing_key': 'monitoring.tasks'
            }
        },
        
        # Queue Configuration
        task_queues={
            'sms_critical': {
                'exchange': 'mingus_exchange',
                'routing_key': 'sms.critical',
                'queue_arguments': {'x-max-priority': 10}
            },
            'sms_daily': {
                'exchange': 'mingus_exchange',
                'routing_key': 'sms.daily',
                'queue_arguments': {'x-max-priority': 10}
            },
            'email_reports': {
                'exchange': 'mingus_exchange',
                'routing_key': 'email.reports',
                'queue_arguments': {'x-max-priority': 10}
            },
            'email_education': {
                'exchange': 'mingus_exchange',
                'routing_key': 'email.education',
                'queue_arguments': {'x-max-priority': 10}
            },
            'analytics': {
                'exchange': 'mingus_exchange',
                'routing_key': 'analytics.*',
                'queue_arguments': {'x-max-priority': 10}
            },
            'optimization': {
                'exchange': 'mingus_exchange',
                'routing_key': 'optimization.*',
                'queue_arguments': {'x-max-priority': 10}
            },
            'communication_tasks': {
                'exchange': 'mingus_exchange',
                'routing_key': 'communication.tasks',
                'queue_arguments': {'x-max-priority': 10}
            },
            'monitoring': {
                'exchange': 'mingus_exchange',
                'routing_key': 'monitoring.tasks',
                'queue_arguments': {'x-max-priority': 10}
            },
            'mingus_tasks': {
                'exchange': 'mingus_exchange',
                'routing_key': 'mingus.tasks',
                'queue_arguments': {'x-max-priority': 10}
            }
        },
        
        # Task Annotations (Rate Limiting, Retries, etc.)
        task_annotations={
            # SMS Tasks
            'backend.tasks.mingus_celery_tasks.send_critical_financial_alert': {
                'rate_limit': '500/m',  # 500 per minute
                'max_retries': 3,
                'default_retry_delay': 60,
                'priority': 1
            },
            'backend.tasks.mingus_celery_tasks.send_payment_reminder': {
                'rate_limit': '100/m',  # 100 per minute
                'max_retries': 3,
                'default_retry_delay': 300,
                'priority': 3
            },
            'backend.tasks.mingus_celery_tasks.send_weekly_checkin': {
                'rate_limit': '50/m',   # 50 per minute
                'max_retries': 2,
                'default_retry_delay': 600,
                'priority': 5
            },
            'backend.tasks.mingus_celery_tasks.send_milestone_reminder': {
                'rate_limit': '100/m',  # 100 per minute
                'max_retries': 2,
                'default_retry_delay': 300,
                'priority': 4
            },
            
            # Email Tasks
            'backend.tasks.mingus_celery_tasks.send_monthly_report': {
                'rate_limit': '1000/m', # 1000 per minute
                'max_retries': 2,
                'default_retry_delay': 1800,
                'priority': 5
            },
            'backend.tasks.mingus_celery_tasks.send_career_insights': {
                'rate_limit': '500/m',  # 500 per minute
                'max_retries': 2,
                'default_retry_delay': 1800,
                'priority': 6
            },
            'backend.tasks.mingus_celery_tasks.send_educational_content': {
                'rate_limit': '500/m',  # 500 per minute
                'max_retries': 2,
                'default_retry_delay': 1800,
                'priority': 7
            },
            'backend.tasks.mingus_celery_tasks.send_onboarding_sequence': {
                'rate_limit': '200/m',  # 200 per minute
                'max_retries': 3,
                'default_retry_delay': 900,
                'priority': 2
            },
            
            # Analytics Tasks
            'backend.tasks.mingus_celery_tasks.monitor_queue_depth': {
                'rate_limit': '10/m',   # 10 per minute
                'max_retries': 2,
                'default_retry_delay': 300,
                'priority': 8
            },
            'backend.tasks.mingus_celery_tasks.track_delivery_rates': {
                'rate_limit': '30/m',   # 30 per minute
                'max_retries': 2,
                'default_retry_delay': 300,
                'priority': 8
            },
            'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {
                'rate_limit': '5/m',    # 5 per minute
                'max_retries': 2,
                'default_retry_delay': 600,
                'priority': 9
            },
            'backend.tasks.mingus_celery_tasks.process_failed_messages': {
                'rate_limit': '20/m',   # 20 per minute
                'max_retries': 3,
                'default_retry_delay': 300,
                'priority': 6
            },
            'backend.tasks.mingus_celery_tasks.optimize_send_timing': {
                'rate_limit': '5/m',    # 5 per minute
                'max_retries': 2,
                'default_retry_delay': 1800,
                'priority': 9
            }
        },
        
        # Beat Schedule (Periodic Tasks)
        beat_schedule={
            # Queue Monitoring (every 5 minutes)
            'monitor-queue-depth': {
                'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
                'schedule': crontab(minute='*/5'),
                'options': {'queue': 'analytics'}
            },
            
            # Delivery Rate Tracking (every 10 minutes)
            'track-delivery-rates': {
                'task': 'backend.tasks.mingus_celery_tasks.track_delivery_rates',
                'schedule': crontab(minute='*/10'),
                'options': {'queue': 'analytics'}
            },
            
            # User Engagement Analysis (every hour)
            'analyze-user-engagement': {
                'task': 'backend.tasks.mingus_celery_tasks.analyze_user_engagement',
                'schedule': crontab(minute=0, hour='*'),
                'options': {'queue': 'analytics'}
            },
            
            # Failed Message Processing (every 15 minutes)
            'process-failed-messages': {
                'task': 'backend.tasks.mingus_celery_tasks.process_failed_messages',
                'schedule': crontab(minute='*/15'),
                'options': {'queue': 'optimization'}
            },
            
            # Send Timing Optimization (every 6 hours)
            'optimize-send-timing': {
                'task': 'backend.tasks.mingus_celery_tasks.optimize_send_timing',
                'schedule': crontab(minute=0, hour='*/6'),
                'options': {'queue': 'optimization'}
            },
            
            # Weekly Check-ins (every Monday at 9 AM)
            'weekly-checkins': {
                'task': 'backend.tasks.mingus_celery_tasks.send_weekly_checkin',
                'schedule': crontab(minute=0, hour=9, day_of_week=1),
                'options': {'queue': 'sms_daily'}
            },
            
            # Monthly Reports (1st of month at 8 AM)
            'monthly-reports': {
                'task': 'backend.tasks.mingus_celery_tasks.send_monthly_report',
                'schedule': crontab(minute=0, hour=8, day_of_month=1),
                'options': {'queue': 'email_reports'}
            },
            
            # Career Insights (every Tuesday and Thursday at 10 AM)
            'career-insights': {
                'task': 'backend.tasks.mingus_celery_tasks.send_career_insights',
                'schedule': crontab(minute=0, hour=10, day_of_week='2,4'),
                'options': {'queue': 'email_education'}
            },
            
            # Educational Content (every Wednesday at 2 PM)
            'educational-content': {
                'task': 'backend.tasks.mingus_celery_tasks.send_educational_content',
                'schedule': crontab(minute=0, hour=14, day_of_week=3),
                'options': {'queue': 'email_education'}
            }
        },
        
        # Worker Configuration
        worker_concurrency=int(os.environ.get('CELERY_WORKER_CONCURRENCY', 4)),
        worker_max_tasks_per_child=int(os.environ.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000)),
        worker_prefetch_multiplier=int(os.environ.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1)),
        worker_disable_rate_limits=os.environ.get('CELERY_WORKER_DISABLE_RATE_LIMITS', 'false').lower() == 'true',
        
        # Logging Configuration
        worker_hijack_root_logger=False,
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        
        # Security Configuration
        security_key=os.environ.get('CELERY_SECURITY_KEY'),
        security_certificate=os.environ.get('CELERY_SECURITY_CERTIFICATE'),
        security_cert_store=os.environ.get('CELERY_SECURITY_CERT_STORE'),
        
        # Monitoring Configuration
        event_queue_expires=60.0,
        event_queue_ttl=5.0,
        event_queue_maxsize=10000,
        
        # Result Backend Configuration
        result_expires=timedelta(hours=24),
        result_persistent=True,
        result_compression='gzip',
        
        # Task Result Configuration
        task_ignore_result=False,
        task_store_errors_even_if_ignored=True,
        task_always_eager=os.environ.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true',
        
        # Broker Connection Configuration
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        broker_connection_max_retries=10,
        broker_pool_limit=10,
        broker_heartbeat=10,
        broker_connection_timeout=30,
        broker_connection_retry_delay=0.2,
        
        # Redis Specific Configuration
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'fanout_prefix': True,
            'fanout_patterns': True,
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
            'retry_on_timeout': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            'socket_keepalive_idle': 1,
            'socket_keepalive_interval': 1,
            'socket_keepalive_count': 5,
        },
        
        # Result Backend Transport Options
        result_backend_transport_options={
            'retry_policy': {
                'timeout': 5.0
            },
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            'socket_keepalive_idle': 1,
            'socket_keepalive_interval': 1,
            'socket_keepalive_count': 5,
        }
    )
    
    # Flask Integration
    if flask_app:
        # Store Flask app in Celery config
        celery_app.conf.update(
            flask_app=flask_app,
            flask_app_context=True
        )
        
        # Initialize Flask app context
        class FlaskTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with flask_app.app_context():
                    return super().__call__(*args, **kwargs)
        
        celery_app.Task = FlaskTask
    
    return celery_app


def configure_celery_for_environment(environment: str = None) -> Dict[str, Any]:
    """
    Configure Celery settings based on environment
    
    Args:
        environment: Environment name (development, testing, production)
    
    Returns:
        Environment-specific configuration
    """
    
    if not environment:
        environment = os.environ.get('FLASK_ENV', 'development')
    
    base_config = {
        'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        'timezone': 'UTC',
        'enable_utc': True,
    }
    
    if environment == 'development':
        return {
            **base_config,
            'task_always_eager': False,
            'worker_concurrency': 2,
            'worker_prefetch_multiplier': 1,
            'task_ignore_result': False,
            'result_expires': timedelta(hours=1),
            'broker_connection_retry_on_startup': True,
            'worker_log_level': 'DEBUG',
            'task_track_started': True,
        }
    
    elif environment == 'testing':
        return {
            **base_config,
            'task_always_eager': True,
            'worker_concurrency': 1,
            'worker_prefetch_multiplier': 1,
            'task_ignore_result': True,
            'result_expires': timedelta(minutes=30),
            'broker_connection_retry_on_startup': False,
            'worker_log_level': 'INFO',
            'task_track_started': False,
        }
    
    elif environment == 'production':
        return {
            **base_config,
            'task_always_eager': False,
            'worker_concurrency': int(os.environ.get('CELERY_WORKER_CONCURRENCY', 8)),
            'worker_prefetch_multiplier': int(os.environ.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1)),
            'task_ignore_result': False,
            'result_expires': timedelta(hours=24),
            'broker_connection_retry_on_startup': True,
            'worker_log_level': 'INFO',
            'task_track_started': True,
            'worker_max_tasks_per_child': int(os.environ.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000)),
            'broker_pool_limit': int(os.environ.get('CELERY_BROKER_POOL_LIMIT', 10)),
            'broker_heartbeat': int(os.environ.get('CELERY_BROKER_HEARTBEAT', 10)),
        }
    
    else:
        return base_config


def get_celery_config() -> Dict[str, Any]:
    """
    Get current Celery configuration
    
    Returns:
        Current Celery configuration dictionary
    """
    from celery import current_app
    
    if current_app:
        return current_app.conf
    else:
        return {}


def validate_celery_config() -> Dict[str, Any]:
    """
    Validate Celery configuration
    
    Returns:
        Validation results
    """
    import redis
    from celery import current_app
    
    validation_results = {
        'broker_connection': False,
        'result_backend_connection': False,
        'queues': [],
        'workers': [],
        'errors': []
    }
    
    try:
        # Test broker connection
        if current_app:
            broker_url = current_app.conf.broker_url
            if broker_url.startswith('redis://'):
                redis_client = redis.from_url(broker_url)
                redis_client.ping()
                validation_results['broker_connection'] = True
            else:
                validation_results['errors'].append(f"Unsupported broker: {broker_url}")
        
        # Test result backend connection
        if current_app:
            result_backend = current_app.conf.result_backend
            if result_backend.startswith('redis://'):
                redis_client = redis.from_url(result_backend)
                redis_client.ping()
                validation_results['result_backend_connection'] = True
            else:
                validation_results['errors'].append(f"Unsupported result backend: {result_backend}")
        
        # Check queues
        if current_app:
            for queue_name in current_app.conf.task_queues.keys():
                validation_results['queues'].append({
                    'name': queue_name,
                    'status': 'configured'
                })
        
    except Exception as e:
        validation_results['errors'].append(f"Configuration validation failed: {str(e)}")
    
    return validation_results


# Global Celery app instance
celery_app = None


def get_celery_app() -> Celery:
    """
    Get the global Celery application instance
    
    Returns:
        Celery application instance
    """
    global celery_app
    if celery_app is None:
        celery_app = create_celery_app()
    return celery_app


def init_celery_app(flask_app=None) -> Celery:
    """
    Initialize the global Celery application
    
    Args:
        flask_app: Flask application instance (optional)
    
    Returns:
        Initialized Celery application
    """
    global celery_app
    celery_app = create_celery_app(flask_app)
    return celery_app


# Export main functions and classes
__all__ = [
    'create_celery_app',
    'configure_celery_for_environment',
    'get_celery_config',
    'validate_celery_config',
    'get_celery_app',
    'init_celery_app',
    'celery_app'
] 