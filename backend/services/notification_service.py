#!/usr/bin/env python3
"""
Mingus Notification Service

Enhanced notification service for Daily Outlook push notifications with:
- Scheduled daily outlook notifications
- Personalized notification content based on user data
- Timezone-aware delivery
- Delivery tracking and analytics
- Rich notifications with action buttons
- Deep linking support
"""

import os
import json
import logging
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Any, Tuple
import pytz
from dataclasses import dataclass
from enum import Enum

# Third-party imports
import requests
from pywebpush import webpush, WebPushException
from sqlalchemy import and_, or_, desc

# Local imports
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import DailyOutlook
from backend.services.email_service import EmailService

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    DAILY_OUTLOOK = "daily_outlook"
    STREAK_MILESTONE = "streak_milestone"
    RECOVERY = "recovery"
    REMINDER = "reminder"

class NotificationChannel(Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"

@dataclass
class NotificationContent:
    title: str
    message: str
    preview: str
    balance_score: int
    streak_count: int
    action_url: str
    notification_type: NotificationType
    priority: str = "normal"
    sound: str = "default"
    badge: Optional[int] = None
    actions: Optional[List[Dict[str, str]]] = None
    deep_link_data: Optional[Dict[str, Any]] = None

@dataclass
class NotificationDelivery:
    user_id: int
    notification_id: str
    channel: NotificationChannel
    scheduled_time: datetime
    delivered_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    delivery_status: str = "pending"
    error_message: Optional[str] = None

class NotificationService:
    """
    Enhanced notification service for Daily Outlook push notifications
    """
    
    def __init__(self):
        self.email_service = EmailService()
        self.vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY')
        self.vapid_claims = {
            "sub": "mailto:notifications@mingus.com"
        }
        
        # FCM configuration
        self.fcm_server_key = os.getenv('FCM_SERVER_KEY')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        
        # APNS configuration
        self.apns_certificate_path = os.getenv('APNS_CERTIFICATE_PATH')
        self.apns_key_id = os.getenv('APNS_KEY_ID')
        self.apns_team_id = os.getenv('APNS_TEAM_ID')
        
        # Default notification preferences
        self.default_preferences = {
            'daily_outlook_enabled': True,
            'weekday_time': '06:45',
            'weekend_time': '08:30',
            'timezone': 'UTC',
            'sound_enabled': True,
            'vibration_enabled': True,
            'rich_notifications': True,
            'action_buttons': True
        }

    def create_daily_outlook_notification(
        self, 
        user: User, 
        outlook: DailyOutlook,
        preferences: Dict[str, Any]
    ) -> NotificationContent:
        """
        Create personalized Daily Outlook notification content
        """
        try:
            # Generate personalized content based on user data and outlook
            title = self._generate_notification_title(user, outlook)
            message = self._generate_notification_message(user, outlook)
            preview = self._generate_notification_preview(outlook)
            
            # Create action buttons for rich notifications
            actions = []
            if preferences.get('action_buttons', True):
                actions = [
                    {
                        "action": "view_outlook",
                        "title": "View Outlook",
                        "icon": "/icons/view-icon.png"
                    },
                    {
                        "action": "quick_action",
                        "title": "Quick Action",
                        "icon": "/icons/action-icon.png"
                    }
                ]
            
            # Deep link data for navigation
            deep_link_data = {
                "screen": "DailyOutlook",
                "params": {
                    "date": outlook.date.isoformat(),
                    "user_id": user.id
                }
            }
            
            return NotificationContent(
                title=title,
                message=message,
                preview=preview,
                balance_score=outlook.balance_score,
                streak_count=outlook.streak_count,
                action_url=f"/daily-outlook/{outlook.date}",
                notification_type=NotificationType.DAILY_OUTLOOK,
                priority="high" if outlook.balance_score < 30 else "normal",
                sound="default",
                badge=1 if outlook.streak_count > 0 else None,
                actions=actions,
                deep_link_data=deep_link_data
            )
            
        except Exception as e:
            logger.error(f"Error creating daily outlook notification for user {user.id}: {e}")
            raise

    def schedule_daily_outlook_notifications(self, target_date: date = None) -> Dict[str, Any]:
        """
        Schedule Daily Outlook notifications for all eligible users
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Scheduling daily outlook notifications for {target_date}")
        
        try:
            # Get users with notification preferences and outlooks
            users_to_notify = self._get_users_for_notification(target_date)
            
            results = {
                'success': True,
                'target_date': target_date.isoformat(),
                'total_users': len(users_to_notify),
                'notifications_scheduled': 0,
                'failed_count': 0,
                'errors': []
            }
            
            for user_data in users_to_notify:
                try:
                    # Get user's outlook for the target date
                    outlook = DailyOutlook.query.filter(
                        and_(
                            DailyOutlook.user_id == user_data['user_id'],
                            DailyOutlook.date == target_date
                        )
                    ).first()
                    
                    if not outlook:
                        logger.warning(f"No outlook found for user {user_data['user_id']} on {target_date}")
                        results['failed_count'] += 1
                        continue
                    
                    # Get user notification preferences
                    preferences = self._get_user_notification_preferences(user_data['user_id'])
                    
                    # Create notification content
                    notification_content = self.create_daily_outlook_notification(
                        user_data['user'], outlook, preferences
                    )
                    
                    # Schedule notification delivery
                    delivery_success = self._schedule_notification_delivery(
                        user_data, notification_content, preferences
                    )
                    
                    if delivery_success:
                        results['notifications_scheduled'] += 1
                    else:
                        results['failed_count'] += 1
                        results['errors'].append(f"Failed to schedule notification for user {user_data['user_id']}")
                        
                except Exception as e:
                    results['failed_count'] += 1
                    error_msg = f"Error scheduling notification for user {user_data['user_id']}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Daily outlook notifications scheduled: {results['notifications_scheduled']} scheduled, "
                       f"{results['failed_count']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error scheduling daily outlook notifications: {e}")
            return {
                'success': False,
                'error': str(e),
                'target_date': target_date.isoformat()
            }

    def send_push_notification(
        self, 
        user_id: int, 
        content: NotificationContent,
        push_subscription: Dict[str, Any]
    ) -> bool:
        """
        Send push notification via Web Push API
        """
        try:
            # Prepare notification payload
            payload = {
                "title": content.title,
                "body": content.message,
                "icon": "/icons/icon-192x192.png",
                "badge": "/icons/badge-72x72.png",
                "tag": "daily-outlook",
                "requireInteraction": True,
                "data": {
                    "url": content.action_url,
                    "notification_type": content.notification_type.value,
                    "balance_score": content.balance_score,
                    "streak_count": content.streak_count,
                    "deep_link": content.deep_link_data
                }
            }
            
            # Add actions for rich notifications
            if content.actions:
                payload["actions"] = content.actions
            
            # Send via Web Push
            webpush(
                subscription_info=push_subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            logger.info(f"Push notification sent to user {user_id}")
            return True
            
        except WebPushException as e:
            logger.error(f"WebPush error for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification to user {user_id}: {e}")
            return False

    def send_email_notification(
        self, 
        user: User, 
        content: NotificationContent
    ) -> bool:
        """
        Send email notification for Daily Outlook
        """
        try:
            # Create email content
            subject = f"🌅 {content.title}"
            
            html_content = self._generate_email_html(user, content)
            text_content = self._generate_email_text(user, content)
            
            # Send email
            success = self.email_service._send_email(
                user.email, subject, html_content, text_content
            )
            
            if success:
                logger.info(f"Email notification sent to user {user.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email notification to user {user.id}: {e}")
            return False

    def track_notification_interaction(
        self, 
        notification_id: str, 
        action: str, 
        action_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track notification interaction (click, dismiss, action taken)
        """
        try:
            # This would update the notification delivery record
            # For now, we'll log the interaction
            logger.info(f"Notification interaction tracked: {notification_id}, action: {action}")
            
            # In a real implementation, this would:
            # 1. Update the notification delivery record
            # 2. Track analytics
            # 3. Update user engagement metrics
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking notification interaction: {e}")
            return False

    def get_notification_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's notification preferences
        """
        try:
            # This would fetch from database
            # For now, return default preferences
            return self.default_preferences.copy()
            
        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return self.default_preferences.copy()

    def update_notification_preferences(
        self, 
        user_id: int, 
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user's notification preferences
        """
        try:
            # This would update the database
            # For now, we'll just log the update
            logger.info(f"Notification preferences updated for user {user_id}: {preferences}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            return False

    def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get notification statistics for a user
        """
        try:
            # This would calculate from database records
            # For now, return mock data
            return {
                'total_sent': 0,
                'total_delivered': 0,
                'total_clicked': 0,
                'click_rate': 0.0,
                'delivery_rate': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats for user {user_id}: {e}")
            return {}

    def _get_users_for_notification(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Get users who should receive notifications for the target date
        """
        try:
            # Get users with outlooks for the target date
            users_with_outlooks = User.query.join(DailyOutlook).filter(
                DailyOutlook.date == target_date
            ).all()
            
            users_to_notify = []
            for user in users_with_outlooks:
                # Get user's timezone and preferences
                user_timezone = getattr(user, 'timezone', 'UTC')
                notification_time = self._get_user_notification_time(user, target_date)
                
                users_to_notify.append({
                    'user_id': user.id,
                    'user': user,
                    'email': user.email,
                    'first_name': user.first_name,
                    'timezone': user_timezone,
                    'notification_time': notification_time
                })
            
            return users_to_notify
            
        except Exception as e:
            logger.error(f"Error getting users for notification: {e}")
            return []

    def _get_user_notification_time(self, user: User, target_date: date) -> str:
        """
        Get the preferred notification time for a user on a specific date
        """
        try:
            # Check if it's a weekday (Monday=0, Sunday=6)
            is_weekday = target_date.weekday() < 5
            
            # Get user preferences (defaults if not set)
            weekday_time = getattr(user, 'weekday_notification_time', '06:45')
            weekend_time = getattr(user, 'weekend_notification_time', '08:30')
            
            return weekday_time if is_weekday else weekend_time
            
        except Exception as e:
            logger.error(f"Error getting notification time for user {user.id}: {e}")
            return '06:45'  # Default fallback

    def _get_user_notification_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's notification preferences
        """
        try:
            # This would fetch from database
            # For now, return default preferences
            return self.default_preferences.copy()
            
        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return self.default_preferences.copy()

    def _schedule_notification_delivery(
        self, 
        user_data: Dict[str, Any], 
        content: NotificationContent,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Schedule notification delivery for a user
        """
        try:
            # Calculate delivery time based on user's timezone and preferences
            delivery_time = self._calculate_delivery_time(
                user_data['timezone'], 
                user_data['notification_time']
            )
            
            # For now, we'll just log the scheduling
            # In a real implementation, this would:
            # 1. Store the notification in the database
            # 2. Schedule the delivery via Celery
            # 3. Handle different notification channels
            
            logger.info(f"Notification scheduled for user {user_data['user_id']} at {delivery_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling notification delivery for user {user_data['user_id']}: {e}")
            return False

    def _calculate_delivery_time(self, timezone: str, notification_time: str) -> datetime:
        """
        Calculate the delivery time in UTC based on user's timezone
        """
        try:
            # Parse notification time
            hour, minute = map(int, notification_time.split(':'))
            
            # Get user's timezone
            user_tz = pytz.timezone(timezone)
            
            # Create datetime in user's timezone
            user_dt = datetime.now(user_tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Convert to UTC
            utc_dt = user_dt.astimezone(pytz.UTC)
            
            return utc_dt
            
        except Exception as e:
            logger.error(f"Error calculating delivery time: {e}")
            # Return current time + 1 hour as fallback
            return datetime.utcnow() + timedelta(hours=1)

    def _generate_notification_title(self, user: User, outlook: DailyOutlook) -> str:
        """
        Generate personalized notification title
        """
        try:
            first_name = user.first_name or "there"
            
            if outlook.balance_score >= 80:
                return f"🌟 Excellent day ahead, {first_name}!"
            elif outlook.balance_score >= 60:
                return f"🌅 Good morning, {first_name}!"
            elif outlook.balance_score >= 40:
                return f"💪 Ready to tackle today, {first_name}?"
            else:
                return f"🌱 New day, new opportunities, {first_name}!"
                
        except Exception as e:
            logger.error(f"Error generating notification title: {e}")
            return "🌅 Your Daily Outlook is Ready!"

    def _generate_notification_message(self, user: User, outlook: DailyOutlook) -> str:
        """
        Generate personalized notification message
        """
        try:
            first_name = user.first_name or "there"
            
            # Base message
            if outlook.streak_count > 0:
                message = f"Good morning {first_name}! You're on a {outlook.streak_count}-day streak! "
            else:
                message = f"Good morning {first_name}! "
            
            # Add insight preview
            if outlook.primary_insight:
                insight_preview = outlook.primary_insight[:100]
                if len(outlook.primary_insight) > 100:
                    insight_preview += "..."
                message += f"Today's insight: {insight_preview}"
            else:
                message += "Your personalized daily outlook is ready with insights and actions."
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating notification message: {e}")
            return "Your personalized daily outlook is ready with insights and actions."

    def _generate_notification_preview(self, outlook: DailyOutlook) -> str:
        """
        Generate notification preview text
        """
        try:
            if outlook.primary_insight:
                return outlook.primary_insight[:150] + ("..." if len(outlook.primary_insight) > 150 else "")
            else:
                return "Your daily insights and actions await!"
                
        except Exception as e:
            logger.error(f"Error generating notification preview: {e}")
            return "Your daily insights and actions await!"

    def _generate_email_html(self, user: User, content: NotificationContent) -> str:
        """
        Generate HTML email content
        """
        try:
            first_name = user.first_name or "there"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{content.title}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; margin: 0;">{content.title}</h1>
                    </div>
                    
                    <div style="background: #F8FAFC; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 10px 0; color: #1F2937;">Good morning, {first_name}!</h2>
                        <p style="margin: 0; color: #6B7280;">{content.message}</p>
                    </div>
                    
                    <div style="background: white; border: 1px solid #E5E7EB; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 15px 0; color: #1F2937;">Today's Balance Score</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="width: 200px; height: 20px; background: #E5E7EB; border-radius: 10px; overflow: hidden;">
                                <div style="width: {content.balance_score}%; height: 100%; background: {'#10B981' if content.balance_score >= 70 else '#F59E0B' if content.balance_score >= 40 else '#EF4444'};"></div>
                            </div>
                            <span style="margin-left: 10px; font-weight: bold; color: #1F2937;">{content.balance_score}/100</span>
                        </div>
                        
                        {f'<p style="margin: 0; color: #6B7280;">Streak: {content.streak_count} days</p>' if content.streak_count > 0 else ''}
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{content.action_url}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                            View Your Daily Outlook
                        </a>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 14px;">
                        <p>This email was sent because you have Daily Outlook notifications enabled.</p>
                        <p><a href="/settings/notifications" style="color: #4F46E5;">Manage your notification preferences</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating email HTML: {e}")
            return f"<html><body><h1>{content.title}</h1><p>{content.message}</p></body></html>"

    def _generate_email_text(self, user: User, content: NotificationContent) -> str:
        """
        Generate plain text email content
        """
        try:
            first_name = user.first_name or "there"
            
            text = f"""
{content.title}

Good morning, {first_name}!

{content.message}

Today's Balance Score: {content.balance_score}/100
{f'Streak: {content.streak_count} days' if content.streak_count > 0 else ''}

View your complete Daily Outlook: {content.action_url}

---
This email was sent because you have Daily Outlook notifications enabled.
Manage your notification preferences: /settings/notifications
            """
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error generating email text: {e}")
            return f"{content.title}\n\n{content.message}\n\nView your Daily Outlook: {content.action_url}"
