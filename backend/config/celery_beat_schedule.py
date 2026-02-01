#!/usr/bin/env python3
"""
Celery Beat Schedule Configuration for Mingus Gas Price Service

Defines periodic tasks for gas price updates and maintenance.
"""

from celery.schedules import crontab

# Gas Price Service Periodic Tasks
GAS_PRICE_BEAT_SCHEDULE = {
    # Daily gas price update at 6:00 AM UTC
    'update-daily-gas-prices': {
        'task': 'backend.tasks.gas_price_tasks.update_daily_gas_prices',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM UTC daily
        'options': {
            'queue': 'gas_price_queue',
            'priority': 5,
        }
    },
    
    # Health check every 2 hours
    'gas-price-health-check': {
        'task': 'backend.tasks.gas_price_tasks.health_check_gas_price_service',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
        'options': {
            'queue': 'gas_price_queue',
            'priority': 3,
        }
    },
    
    # Cleanup old data weekly on Sunday at 2:00 AM UTC
    'cleanup-gas-price-data': {
        'task': 'backend.tasks.gas_price_tasks.cleanup_old_gas_price_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2:00 AM UTC
        'args': (30,),  # Keep 30 days of data
        'options': {
            'queue': 'gas_price_queue',
            'priority': 2,
        }
    },
    
    # Task monitoring every 30 minutes
    'monitor-gas-price-tasks': {
        'task': 'backend.tasks.gas_price_tasks.monitor_gas_price_tasks',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'queue': 'gas_price_queue',
            'priority': 1,
        }
    },
}

# Daily Outlook Service Periodic Tasks
DAILY_OUTLOOK_BEAT_SCHEDULE = {
    # Daily outlook generation at 5:00 AM UTC
    'generate-daily-outlooks': {
        'task': 'backend.tasks.daily_outlook_tasks.generate_daily_outlooks_batch',
        'schedule': crontab(hour=5, minute=0),  # 5:00 AM UTC daily
        'options': {
            'queue': 'daily_outlook_queue',
            'priority': 5,
        }
    },
    
    # Daily outlook notifications at 6:45 AM UTC (weekdays) and 8:30 AM UTC (weekends)
    'send-daily-outlook-notifications': {
        'task': 'backend.tasks.daily_outlook_tasks.send_daily_outlook_notifications',
        'schedule': crontab(hour=6, minute=45),  # 6:45 AM UTC daily (handles timezone conversion in task)
        'options': {
            'queue': 'daily_outlook_queue',
            'priority': 4,
        }
    },
    
    # Content performance optimization weekly on Sunday at 3:00 AM UTC
    'optimize-content-performance': {
        'task': 'backend.tasks.daily_outlook_tasks.optimize_content_performance',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM UTC
        'options': {
            'queue': 'daily_outlook_queue',
            'priority': 3,
        }
    },
    
    # Daily outlook health check every 4 hours
    'daily-outlook-health-check': {
        'task': 'backend.tasks.daily_outlook_tasks.health_check_daily_outlook_tasks',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {
            'queue': 'daily_outlook_queue',
            'priority': 2,
        }
    },
}

# Check-in Notification Periodic Tasks
NOTIFICATION_BEAT_SCHEDULE = {
    # Hourly: check all users and send check-in reminders at Sunday 6pm, Monday 10am, Monday 7pm (user TZ)
    'check-and-send-reminders': {
        'task': 'backend.tasks.notification_tasks.check_and_send_reminders',
        'schedule': crontab(minute=0),  # Every hour at :00
        'options': {
            'queue': 'notification_queue',
            'priority': 5,
        }
    },
}

# Additional periodic tasks for the broader Mingus application
MINGUS_BEAT_SCHEDULE = {
    # Add other periodic tasks here as needed
    # Example:
    # 'update-user-recommendations': {
    #     'task': 'backend.tasks.recommendation_tasks.update_user_recommendations',
    #     'schedule': crontab(hour=1, minute=0),  # 1:00 AM UTC daily
    # },
}

# Combined beat schedule
CELERY_BEAT_SCHEDULE = {
    **GAS_PRICE_BEAT_SCHEDULE,
    **DAILY_OUTLOOK_BEAT_SCHEDULE,
    **NOTIFICATION_BEAT_SCHEDULE,
    **MINGUS_BEAT_SCHEDULE,
}
