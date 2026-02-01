#!/usr/bin/env python3
"""
Mingus Check-in Notification Service

Handles weekly check-in reminders and engagement notifications:
- Scheduled reminders (Sunday 6pm, Monday 10am, Monday 7pm)
- Streak-at-risk and achievement notifications
- Insight and achievement notifications
Uses existing EmailService and FCM for push; respects user preferences and quiet hours.
"""

import os
import logging
from datetime import datetime, date, time, timedelta, timezone
from typing import Dict, Any, Optional, List

import pytz
import requests

from backend.models.database import db
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin, WellnessCheckinStreak
from backend.models.notification_models import (
    UserNotificationPreferences,
    PushSubscription,
    NotificationDelivery,
    NotificationType,
    NotificationChannel,
    DeliveryStatus,
)
from backend.services.email_service import EmailService
from backend.services.wellness_score_service import WellnessScoreCalculator

logger = logging.getLogger(__name__)

# Default quiet hours: 10pm–8am (don't send unless urgent)
DEFAULT_QUIET_START = time(22, 0)   # 10:00 PM
DEFAULT_QUIET_END = time(8, 0)      # 8:00 AM

# Reminder schedule in user local time: (day_of_week, hour, minute), Sunday=6, Monday=0
REMINDER_SCHEDULE = [
    (6, 18, 0),   # Sunday 6:00 PM
    (0, 10, 0),   # Monday 10:00 AM
    (0, 19, 0),   # Monday 7:00 PM
]

CHECKIN_NOTIFICATION_TEMPLATES = {
    'checkin_first': {
        'title': "Time for your weekly check-in! 🌟",
        'body': "How was your week? Take 5 minutes to reflect.",
        'action': "Start Check-in",
    },
    'checkin_reminder': {
        'title': "Don't forget your weekly check-in 📋",
        'body': "A quick check-in helps you track wellness and spending.",
        'action': "Start Check-in",
    },
    'checkin_second': {
        'title': "Your weekly check-in is waiting ✨",
        'body': "Reflect on your week and keep your streak going.",
        'action': "Start Check-in",
    },
    'streak_at_risk': {
        'title': "🔥 {streak}-week streak at risk!",
        'body': "Complete your check-in to keep your streak alive.",
        'action': "Save My Streak",
    },
    'new_insight': {
        'title': "New insight unlocked! 💡",
        'body': "We found a pattern in your data: {insight_title}",
        'action': "View Insight",
    },
    'achievement': {
        'title': "🏆 Achievement unlocked!",
        'body': "{achievement_name}",
        'action': "View",
    },
}


class CheckinNotificationService:
    """
    Service for check-in reminders and wellness engagement notifications.
    Sends via push (FCM) and/or email based on user preferences; respects quiet hours.
    """

    def __init__(self):
        self.email_service = EmailService()
        self.fcm_server_key = os.getenv('FCM_SERVER_KEY')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        self.base_url = os.getenv('FRONTEND_BASE_URL', 'https://app.mingus.com')

    @staticmethod
    def get_week_ending_today() -> date:
        return WellnessScoreCalculator.get_week_ending_date(date.today())

    def schedule_weekly_reminders(self, user_id: str) -> None:
        """
        Schedule reminders for Sunday 6pm, Monday 10am, Monday 7pm (user local time).
        Only schedules if check-in not completed for current week.
        Actual sending is done by Celery beat + hourly check_and_send_reminders task.
        """
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                logger.warning(f"schedule_weekly_reminders: user not found {user_id}")
                return
            week_ending = self.get_week_ending_today()
            existing = WeeklyCheckin.query.filter_by(
                user_id=user.id, week_ending_date=week_ending
            ).first()
            if existing and existing.completed_at is not None:
                return  # Already completed this week
            # Scheduling is implicit: Celery beat runs check_and_send_reminders hourly
            # and that task decides who gets which reminder at what time. No DB storage
            # of scheduled jobs required for this design.
            logger.info(f"Scheduled weekly reminders for user {user_id} (week {week_ending})")
        except Exception as e:
            logger.error(f"Error scheduling weekly reminders for {user_id}: {e}")
            raise

    def send_checkin_reminder(
        self, user_id: str, reminder_type: str
    ) -> None:
        """
        reminder_type: 'first', 'second', 'streak_at_risk'
        Checks if check-in already completed before sending.
        Increments reminder_count on current-week check-in record if it exists.
        Sends via push and/or email per user preferences.
        """
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                logger.warning(f"send_checkin_reminder: user not found {user_id}")
                return
            week_ending = self.get_week_ending_today()
            existing = WeeklyCheckin.query.filter_by(
                user_id=user.id, week_ending_date=week_ending
            ).first()
            if existing and existing.completed_at is not None:
                return  # Already completed
            if not self._should_send_notification(user.id, "checkin_reminder", urgent=False):
                return
            template_key = {
                'first': 'checkin_first',
                'second': 'checkin_reminder',
                'streak_at_risk': 'streak_at_risk',
            }.get(reminder_type, 'checkin_first')
            template = CHECKIN_NOTIFICATION_TEMPLATES.get(
                template_key, CHECKIN_NOTIFICATION_TEMPLATES['checkin_first']
            )
            title = template['title']
            body = template['body']
            if reminder_type == 'streak_at_risk':
                streak = WellnessCheckinStreak.query.filter_by(user_id=user.id).first()
                current = (streak.current_streak or 0) if streak else 0
                title = title.format(streak=current)
            action = template.get('action', 'Start Check-in')
            self._deliver(user, title, body, action, notification_type='checkin_reminder')
            self._increment_reminder_count(user.id, week_ending)
        except Exception as e:
            logger.error(f"Error sending check-in reminder to {user_id}: {e}")
            raise

    def send_streak_at_risk_notification(self, user_id: str, current_streak: int) -> None:
        """
        Urgent notification when streak > 2 and deadline approaching.
        "🔥 Don't break your 5-week streak! Check in now."
        """
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                logger.warning(f"send_streak_at_risk_notification: user not found {user_id}")
                return
            week_ending = self.get_week_ending_today()
            existing = WeeklyCheckin.query.filter_by(
                user_id=user.id, week_ending_date=week_ending
            ).first()
            if existing and existing.completed_at is not None:
                return
            if current_streak < 2:
                return
            if not self._should_send_notification(user.id, "streak_at_risk", urgent=True):
                return
            template = CHECKIN_NOTIFICATION_TEMPLATES['streak_at_risk']
            title = template['title'].format(streak=current_streak)
            body = template['body']
            action = template.get('action', 'Save My Streak')
            self._deliver(user, title, body, action, notification_type='streak_at_risk')
            self._increment_reminder_count(user.id, week_ending)
        except Exception as e:
            logger.error(f"Error sending streak-at-risk notification to {user_id}: {e}")
            raise

    def send_insight_notification(self, user_id: str, insight_title: str) -> None:
        """
        Notify when new significant insight is discovered.
        "New insight unlocked! We found a pattern in your data."
        """
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                logger.warning(f"send_insight_notification: user not found {user_id}")
                return
            if not self._should_send_notification(user.id, "new_insight", urgent=False):
                return
            template = CHECKIN_NOTIFICATION_TEMPLATES['new_insight']
            title = template['title']
            body = template['body'].format(insight_title=insight_title or "Your wellness–spending link")
            action = template.get('action', 'View Insight')
            self._deliver(user, title, body, action, notification_type='new_insight')
        except Exception as e:
            logger.error(f"Error sending insight notification to {user_id}: {e}")
            raise

    def send_achievement_notification(self, user_id: str, achievement_name: str) -> None:
        """
        Celebrate milestones, e.g. "🏆 Achievement unlocked: 4-week meditation streak!"
        """
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                logger.warning(f"send_achievement_notification: user not found {user_id}")
                return
            if not self._should_send_notification(user.id, "achievement", urgent=False):
                return
            template = CHECKIN_NOTIFICATION_TEMPLATES['achievement']
            title = template['title']
            body = template['body'].format(achievement_name=achievement_name)
            action = template.get('action', 'View')
            self._deliver(user, title, body, action, notification_type='achievement')
        except Exception as e:
            logger.error(f"Error sending achievement notification to {user_id}: {e}")
            raise

    def _should_send_notification(
        self, user_id: int, notification_type: str, urgent: bool = False
    ) -> bool:
        """
        Check user preferences: channels (push/email), quiet hours (in user local time).
        Urgent notifications (e.g. streak_at_risk) can bypass quiet hours.
        """
        try:
            prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
            if not prefs:
                return True  # No prefs => allow
            if not urgent:
                tz_name = prefs.timezone or 'UTC'
                try:
                    tz = pytz.timezone(tz_name)
                    now_utc = datetime.now(timezone.utc)
                    local_now = now_utc.astimezone(tz).time()
                except Exception:
                    local_now = datetime.now(timezone.utc).time()
                quiet_start = prefs.quiet_hours_start or DEFAULT_QUIET_START
                quiet_end = prefs.quiet_hours_end or DEFAULT_QUIET_END
                if quiet_start > quiet_end:  # e.g. 22:00–08:00
                    in_quiet = local_now >= quiet_start or local_now < quiet_end
                else:
                    in_quiet = quiet_start <= local_now < quiet_end
                if in_quiet:
                    return False
            if prefs.push_enabled or prefs.email_enabled:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking notification preferences for user {user_id}: {e}")
            return True

    def _deliver(
        self,
        user: User,
        title: str,
        body: str,
        action_label: str,
        notification_type: str = 'checkin_reminder',
    ) -> None:
        """Send via push (FCM) and/or email based on user preferences."""
        prefs = UserNotificationPreferences.query.filter_by(user_id=user.id).first()
        push_ok = prefs is None or prefs.push_enabled
        email_ok = prefs is None or prefs.email_enabled
        action_url = f"{self.base_url}/dashboard"
        if push_ok:
            self._send_push(user.id, title, body, action_url, action_label)
        if email_ok:
            self._send_email(user, title, body, action_url, action_label)
        self._record_delivery(user.id, title, body, action_url, notification_type)

    def _send_push(
        self,
        user_id: int,
        title: str,
        body: str,
        action_url: str,
        action_label: str,
    ) -> bool:
        """Send FCM push notification to user's devices."""
        if not self.fcm_server_key:
            logger.debug("FCM_SERVER_KEY not set; skipping push")
            return False
        try:
            subs = (
                PushSubscription.query.filter_by(user_id=user_id, is_active=True).all()
            )
            if not subs:
                logger.debug(f"No push subscriptions for user {user_id}")
                return False
            for sub in subs:
                # FCM legacy HTTP: subscription can be a device token
                # If your app uses Web Push (VAPID), use the existing NotificationService
                # Here we assume FCM device tokens stored in endpoint or a dedicated column
                token = getattr(sub, 'fcm_token', None) or sub.endpoint
                payload = {
                    'to': token,
                    'notification': {
                        'title': title,
                        'body': body,
                        'click_action': action_url,
                        'sound': 'default',
                    },
                    'data': {
                        'url': action_url,
                        'action': action_label,
                        'type': 'checkin_reminder',
                    },
                }
                headers = {
                    'Authorization': f'key={self.fcm_server_key}',
                    'Content-Type': 'application/json',
                }
                import requests
                resp = requests.post(
                    self.fcm_url, json=payload, headers=headers, timeout=10
                )
                if resp.status_code != 200:
                    logger.warning(f"FCM send failed for user {user_id}: {resp.status_code} {resp.text}")
                else:
                    logger.info(f"FCM push sent to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending FCM push to user {user_id}: {e}")
            return False

    def _send_email(
        self,
        user: User,
        title: str,
        body: str,
        action_url: str,
        action_label: str,
    ) -> bool:
        """Send check-in reminder email via EmailService."""
        try:
            first_name = getattr(user, 'first_name', None) or 'there'
            subject = f"🌟 {title}"
            text_content = f"{title}\n\nHi {first_name},\n\n{body}\n\n{action_label}: {action_url}\n\n— Mingus"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">{title}</h2>
                    <p>Hi {first_name},</p>
                    <p>{body}</p>
                    <p><a href="{action_url}" style="background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">{action_label}</a></p>
                    <p style="color: #6B7280; font-size: 14px;">— Mingus</p>
                </div>
            </body>
            </html>
            """
            return self.email_service._send_email(
                user.email, subject, html_content, text_content
            )
        except Exception as e:
            logger.error(f"Error sending check-in email to user {user.id}: {e}")
            return False

    def _record_delivery(
        self,
        user_id: int,
        title: str,
        body: str,
        action_url: str,
        notification_type: str,
    ) -> None:
        """Record notification delivery for analytics (optional)."""
        try:
            delivery = NotificationDelivery(
                user_id=user_id,
                notification_id=f"checkin_{notification_type}_{datetime.now(timezone.utc).isoformat()}",
                notification_type=NotificationType.REMINDER,
                channel=NotificationChannel.EMAIL,  # or PUSH; we send both, record once
                title=title,
                message=body,
                action_url=action_url,
                scheduled_time=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc),
                status=DeliveryStatus.SENT,
            )
            db.session.add(delivery)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to record notification delivery: {e}")
            db.session.rollback()

    def _increment_reminder_count(self, user_id: int, week_ending: date) -> None:
        """Increment reminder_count on current week's check-in record if it exists (e.g. draft)."""
        try:
            checkin = WeeklyCheckin.query.filter_by(
                user_id=user_id, week_ending_date=week_ending
            ).first()
            if checkin:
                checkin.reminder_count = (checkin.reminder_count or 0) + 1
                db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to increment reminder_count: {e}")
            db.session.rollback()

    def get_users_due_for_reminder(
        self, now: datetime
    ) -> List[Dict[str, Any]]:
        """
        Returns list of { user_id (str), reminder_slot: 'sunday_6pm'|'monday_10am'|'monday_7pm' }
        for users who have not completed the current week's check-in.
        Uses UTC now; for production, convert to user timezone per user.
        """
        week_ending = self.get_week_ending_today()
        # Users who have a check-in for this week with completed_at set are excluded
        completed_user_ids = db.session.query(WeeklyCheckin.user_id).filter(
            WeeklyCheckin.week_ending_date == week_ending,
            WeeklyCheckin.completed_at.isnot(None),
        ).distinct().all()
        completed_ids = {u[0] for u in completed_user_ids}
        # All users with at least one check-in ever (engaged) — or all users; scope as needed
        users = User.query.filter(User.id.notin_(completed_ids)).all()
        result = []
        for user in users:
            # Determine which reminder slot (if any) matches current time in user TZ
            prefs = UserNotificationPreferences.query.filter_by(user_id=user.id).first()
            tz_name = prefs.timezone if prefs else 'UTC'
            try:
                tz = pytz.timezone(tz_name)
                local_now = now.astimezone(tz) if getattr(now, 'tzinfo', None) else pytz.UTC.localize(now).astimezone(tz)
            except Exception:
                local_now = now
            weekday = local_now.weekday()  # 0=Mon, 6=Sun
            hour = local_now.hour
            if weekday == 6 and hour == 18:
                result.append({'user_id': user.user_id, 'reminder_slot': 'sunday_6pm'})
            elif weekday == 0 and hour == 10:
                result.append({'user_id': user.user_id, 'reminder_slot': 'monday_10am'})
            elif weekday == 0 and hour == 19:
                result.append({'user_id': user.user_id, 'reminder_slot': 'monday_7pm'})
        return result
