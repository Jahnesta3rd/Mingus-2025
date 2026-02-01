#!/usr/bin/env python3
"""
Mingus Check-in Notification Celery Tasks

Background tasks for weekly check-in reminders and engagement notifications.
- check_and_send_reminders: runs hourly, checks all users and sends reminders at scheduled times
- send_scheduled_notification: send a single notification to a user by type

Schedule (Celery Beat):
- check_and_send_reminders: every hour (crontab minute=0)
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add backend modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from celery import Celery
from celery.utils.log import get_task_logger

from backend.services.checkin_notification_service import CheckinNotificationService

logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def make_celery(app=None):
    """Create and configure Celery app for notification tasks."""
    celery = Celery(
        app.import_name if app else 'mingus_notification_tasks',
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/2'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        include=['backend.tasks.notification_tasks'],
    )
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        task_soft_time_limit=240,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_routes={
            'backend.tasks.notification_tasks.*': {'queue': 'notification_queue'},
        },
        task_default_queue='notification_queue',
    )
    return celery


celery_app = make_celery()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def check_and_send_reminders(self):
    """
    Runs hourly (via Celery Beat). For each user who has not completed the current
    week's check-in, checks if it's a reminder time in their timezone (Sunday 6pm,
    Monday 10am, Monday 7pm) and sends the appropriate reminder.
    """
    task_id = self.request.id
    celery_logger.info(f"Starting check_and_send_reminders task {task_id}")
    try:
        service = CheckinNotificationService()
        now = datetime.now(timezone.utc)
        due = service.get_users_due_for_reminder(now)
        results = {'sent': 0, 'failed': 0, 'skipped': 0}
        for item in due:
            user_id = item['user_id']
            slot = item['reminder_slot']
            try:
                reminder_type = {
                    'sunday_6pm': 'first',
                    'monday_10am': 'second',
                    'monday_7pm': 'streak_at_risk',
                }.get(slot, 'first')
                service.send_checkin_reminder(user_id, reminder_type)
                results['sent'] += 1
            except Exception as e:
                celery_logger.warning(f"Failed to send reminder to {user_id}: {e}")
                results['failed'] += 1
        celery_logger.info(
            f"check_and_send_reminders completed: sent={results['sent']}, failed={results['failed']}"
        )
        return results
    except Exception as exc:
        celery_logger.error(f"check_and_send_reminders failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def send_scheduled_notification(
    self, user_id: str, notification_type: str, **kwargs
):
    """
    Send a single notification to a user.
    notification_type: 'checkin_first' | 'checkin_second' | 'streak_at_risk' | 'new_insight' | 'achievement'
    kwargs: insight_title (for new_insight), achievement_name (for achievement), current_streak (for streak_at_risk).
    """
    task_id = self.request.id
    celery_logger.info(f"send_scheduled_notification {task_id}: user={user_id} type={notification_type}")
    try:
        service = CheckinNotificationService()
        if notification_type == 'checkin_first':
            service.send_checkin_reminder(user_id, 'first')
        elif notification_type == 'checkin_second':
            service.send_checkin_reminder(user_id, 'second')
        elif notification_type == 'streak_at_risk':
            current_streak = kwargs.get('current_streak')
            if current_streak is None:
                from backend.models.wellness import WellnessCheckinStreak
                from backend.models.user_models import User
                user = User.query.filter_by(user_id=user_id).first()
                if user:
                    row = WellnessCheckinStreak.query.filter_by(user_id=user.id).first()
                    current_streak = (row.current_streak or 0) if row else 0
                else:
                    current_streak = 0
            service.send_streak_at_risk_notification(user_id, current_streak)
        elif notification_type == 'new_insight':
            insight_title = kwargs.get('insight_title', '')
            service.send_insight_notification(user_id, insight_title)
        elif notification_type == 'achievement':
            achievement_name = kwargs.get('achievement_name', '')
            service.send_achievement_notification(user_id, achievement_name)
        else:
            celery_logger.warning(f"Unknown notification_type: {notification_type}")
        return {'ok': True, 'user_id': user_id, 'notification_type': notification_type}
    except Exception as exc:
        celery_logger.error(f"send_scheduled_notification failed: {exc}")
        raise self.retry(exc=exc)
