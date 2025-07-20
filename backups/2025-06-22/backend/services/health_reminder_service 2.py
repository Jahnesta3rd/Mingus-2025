import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from backend.models.user import User
from backend.models.user_health_checkin import UserHealthCheckin
from backend.models.health_spending_correlation import HealthSpendingCorrelation
from backend.models import db_session

logger = logging.getLogger(__name__)

class ReminderType(Enum):
    DASHBOARD = "dashboard"
    EMAIL = "email"
    GENTLE_NUDGE = "gentle_nudge"
    STREAK_MOTIVATION = "streak_motivation"

class ReminderStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    RESPONDED = "responded"
    IGNORED = "ignored"

@dataclass
class ReminderData:
    user_id: int
    reminder_type: ReminderType
    message: str
    priority: int  # 1-5, higher = more urgent
    scheduled_time: datetime
    sent_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    status: ReminderStatus = ReminderStatus.PENDING

@dataclass
class UserReminderPreferences:
    user_id: int
    email_enabled: bool = True
    dashboard_enabled: bool = True
    preferred_day: str = "wednesday"  # day of week
    preferred_time: str = "10:00"  # HH:MM
    max_reminders_per_week: int = 1
    reminder_tone: str = "friendly"  # friendly, professional, motivational

class HealthReminderService:
    """Service for managing health check-in reminders and notifications."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_pending_checkins(self, days_threshold: int = 7) -> List[Dict]:
        """
        Identify users who haven't completed their health check-in this week.
        
        Args:
            days_threshold: Number of days since last check-in to trigger reminder
            
        Returns:
            List of user data with reminder information
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            # Get users who haven't checked in recently
            pending_users = []
            
            users = db_session.query(User).all()
            for user in users:
                # Get their latest check-in
                latest_checkin = db_session.query(UserHealthCheckin)\
                    .filter(UserHealthCheckin.user_id == user.id)\
                    .order_by(UserHealthCheckin.created_at.desc())\
                    .first()
                
                needs_reminder = False
                days_since_checkin = None
                
                if not latest_checkin:
                    needs_reminder = True
                    days_since_checkin = 999  # New user
                elif latest_checkin.created_at < cutoff_date:
                    needs_reminder = True
                    days_since_checkin = (datetime.utcnow() - latest_checkin.created_at).days
                
                if needs_reminder:
                    # Check if we've already sent a reminder this week
                    if not self._has_recent_reminder(user.id):
                        pending_users.append({
                            'user_id': user.id,
                            'user_email': user.email,
                            'user_name': user.name,
                            'days_since_checkin': days_since_checkin,
                            'last_checkin_date': latest_checkin.created_at if latest_checkin else None,
                            'checkin_streak': self._get_checkin_streak(user.id),
                            'preferences': self._get_user_preferences(user.id)
                        })
            
            self.logger.info(f"Found {len(pending_users)} users needing check-in reminders")
            return pending_users
            
        except Exception as e:
            self.logger.error(f"Error checking pending check-ins: {e}")
            return []
    
    def send_checkin_reminders(self, reminder_type: ReminderType = ReminderType.DASHBOARD) -> Dict:
        """
        Send check-in reminders to users who need them.
        
        Args:
            reminder_type: Type of reminder to send
            
        Returns:
            Summary of reminder sending results
        """
        try:
            pending_users = self.check_pending_checkins()
            results = {
                'total_users': len(pending_users),
                'reminders_sent': 0,
                'errors': 0,
                'details': []
            }
            
            for user_data in pending_users:
                try:
                    reminder_data = self._create_reminder_data(user_data, reminder_type)
                    
                    if reminder_type == ReminderType.EMAIL:
                        success = self._send_email_reminder(reminder_data)
                    elif reminder_type == ReminderType.DASHBOARD:
                        success = self._create_dashboard_reminder(reminder_data)
                    elif reminder_type == ReminderType.GENTLE_NUDGE:
                        success = self._create_gentle_nudge(reminder_data)
                    elif reminder_type == ReminderType.STREAK_MOTIVATION:
                        success = self._create_streak_motivation(reminder_data)
                    else:
                        success = False
                    
                    if success:
                        results['reminders_sent'] += 1
                        self._track_reminder_sent(reminder_data)
                    else:
                        results['errors'] += 1
                    
                    results['details'].append({
                        'user_id': user_data['user_id'],
                        'success': success,
                        'reminder_type': reminder_type.value
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error sending reminder to user {user_data['user_id']}: {e}")
                    results['errors'] += 1
            
            self.logger.info(f"Reminder sending complete: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in send_checkin_reminders: {e}")
            return {'error': str(e)}
    
    def calculate_optimal_reminder_time(self, user_id: int) -> datetime:
        """
        Calculate the optimal time to send a reminder based on user behavior.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Optimal datetime for sending reminder
        """
        try:
            # Get user's check-in history
            checkins = db_session.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.created_at.desc())\
                .limit(10)\
                .all()
            
            if not checkins:
                # New user - use default time
                return self._get_default_reminder_time()
            
            # Analyze check-in patterns
            weekday_counts = {}
            hour_counts = {}
            
            for checkin in checkins:
                weekday = checkin.created_at.strftime('%A').lower()
                hour = checkin.created_at.hour
                
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # Find most common weekday and hour
            optimal_weekday = max(weekday_counts, key=weekday_counts.get)
            optimal_hour = max(hour_counts, key=hour_counts.get)
            
            # Convert to next occurrence
            optimal_time = self._get_next_occurrence(optimal_weekday, optimal_hour)
            
            self.logger.info(f"Optimal reminder time for user {user_id}: {optimal_time}")
            return optimal_time
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal reminder time: {e}")
            return self._get_default_reminder_time()
    
    def track_reminder_effectiveness(self, days_back: int = 30) -> Dict:
        """
        Track and analyze reminder effectiveness.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Analytics on reminder success rates
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get reminder tracking data (this would come from a reminder_tracking table)
            # For now, we'll simulate the analysis
            
            analytics = {
                'total_reminders_sent': 0,
                'reminders_responded': 0,
                'response_rate': 0.0,
                'avg_response_time_hours': 0.0,
                'by_reminder_type': {},
                'by_user_segment': {},
                'trends': []
            }
            
            # Simulate some analytics data
            analytics['total_reminders_sent'] = 150
            analytics['reminders_responded'] = 89
            analytics['response_rate'] = 89 / 150 * 100
            
            analytics['by_reminder_type'] = {
                'dashboard': {'sent': 80, 'responded': 65, 'rate': 81.25},
                'email': {'sent': 50, 'responded': 20, 'rate': 40.0},
                'gentle_nudge': {'sent': 20, 'responded': 4, 'rate': 20.0}
            }
            
            self.logger.info(f"Reminder effectiveness analytics: {analytics}")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error tracking reminder effectiveness: {e}")
            return {'error': str(e)}
    
    def get_user_reminder_status(self, user_id: int) -> Dict:
        """
        Get current reminder status for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Current reminder status and information
        """
        try:
            # Get latest check-in
            latest_checkin = db_session.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.created_at.desc())\
                .first()
            
            # Get user preferences
            preferences = self._get_user_preferences(user_id)
            
            # Calculate if reminder is needed
            needs_reminder = False
            days_since_checkin = None
            
            if latest_checkin:
                days_since_checkin = (datetime.utcnow() - latest_checkin.created_at).days
                needs_reminder = days_since_checkin >= 7
            else:
                needs_reminder = True
                days_since_checkin = 999
            
            # Get check-in streak
            streak = self._get_checkin_streak(user_id)
            
            # Get potential insights preview
            insights_preview = self._get_insights_preview(user_id)
            
            return {
                'needs_reminder': needs_reminder,
                'days_since_checkin': days_since_checkin,
                'checkin_streak': streak,
                'preferences': preferences,
                'insights_preview': insights_preview,
                'last_checkin_date': latest_checkin.created_at if latest_checkin else None,
                'next_optimal_reminder': self.calculate_optimal_reminder_time(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user reminder status: {e}")
            return {'error': str(e)}
    
    def _has_recent_reminder(self, user_id: int, days: int = 7) -> bool:
        """Check if user has received a reminder recently."""
        # This would check a reminder_tracking table
        # For now, return False to allow reminders
        return False
    
    def _get_checkin_streak(self, user_id: int) -> int:
        """Calculate user's current check-in streak."""
        try:
            checkins = db_session.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.created_at.desc())\
                .all()
            
            if not checkins:
                return 0
            
            streak = 0
            current_date = datetime.utcnow().date()
            
            for i, checkin in enumerate(checkins):
                checkin_date = checkin.created_at.date()
                expected_date = current_date - timedelta(weeks=i)
                
                # Allow for 1 day variance
                if abs((checkin_date - expected_date).days) <= 1:
                    streak += 1
                else:
                    break
            
            return streak
            
        except Exception as e:
            self.logger.error(f"Error calculating check-in streak: {e}")
            return 0
    
    def _get_user_preferences(self, user_id: int) -> UserReminderPreferences:
        """Get user's reminder preferences."""
        # This would come from a user_preferences table
        # For now, return default preferences
        return UserReminderPreferences(
            user_id=user_id,
            email_enabled=True,
            dashboard_enabled=True,
            preferred_day="wednesday",
            preferred_time="10:00",
            max_reminders_per_week=1,
            reminder_tone="friendly"
        )
    
    def _create_reminder_data(self, user_data: Dict, reminder_type: ReminderType) -> ReminderData:
        """Create reminder data for a user."""
        message = self._generate_reminder_message(user_data, reminder_type)
        priority = self._calculate_reminder_priority(user_data)
        scheduled_time = self.calculate_optimal_reminder_time(user_data['user_id'])
        
        return ReminderData(
            user_id=user_data['user_id'],
            reminder_type=reminder_type,
            message=message,
            priority=priority,
            scheduled_time=scheduled_time
        )
    
    def _generate_reminder_message(self, user_data: Dict, reminder_type: ReminderType) -> str:
        """Generate personalized reminder message."""
        name = user_data.get('user_name', 'there')
        streak = user_data.get('checkin_streak', 0)
        days_since = user_data.get('days_since_checkin', 7)
        
        if reminder_type == ReminderType.DASHBOARD:
            if streak > 0:
                return f"Hey {name}! You're on a {streak}-week check-in streak. Keep it going with this week's health check-in!"
            else:
                return f"Hi {name}! It's been {days_since} days since your last health check-in. Ready to track your wellness?"
        
        elif reminder_type == ReminderType.EMAIL:
            return f"Hi {name},\n\nIt's time for your weekly health check-in! Your insights are waiting.\n\nBest regards,\nThe Mingus Team"
        
        elif reminder_type == ReminderType.GENTLE_NUDGE:
            return f"Quick wellness check, {name}? Just 2 minutes to unlock your health-finance insights."
        
        elif reminder_type == ReminderType.STREAK_MOTIVATION:
            if streak > 0:
                return f"🔥 {streak}-week streak! Don't break the chain - complete your check-in now!"
            else:
                return f"Start your wellness journey today, {name}! Your first check-in awaits."
        
        return f"Time for your health check-in, {name}!"
    
    def _calculate_reminder_priority(self, user_data: Dict) -> int:
        """Calculate reminder priority (1-5)."""
        days_since = user_data.get('days_since_checkin', 7)
        streak = user_data.get('checkin_streak', 0)
        
        if days_since >= 14:
            return 5  # High priority
        elif days_since >= 10:
            return 4
        elif days_since >= 7:
            return 3
        elif streak > 0:
            return 2  # Lower priority for active users
        else:
            return 1
    
    def _get_insights_preview(self, user_id: int) -> Dict:
        """Get preview of insights user would unlock."""
        # This would analyze their data and show potential insights
        return {
            'stress_spending_correlation': 0.73,
            'potential_savings': 150,
            'wellness_trend': 'improving',
            'next_insight': 'Your activity level correlates strongly with reduced impulse spending'
        }
    
    def _send_email_reminder(self, reminder_data: ReminderData) -> bool:
        """Send email reminder (placeholder)."""
        # This would integrate with your email service
        self.logger.info(f"Email reminder sent to user {reminder_data.user_id}: {reminder_data.message}")
        return True
    
    def _create_dashboard_reminder(self, reminder_data: ReminderData) -> bool:
        """Create dashboard notification (placeholder)."""
        # This would create a notification in the database
        self.logger.info(f"Dashboard reminder created for user {reminder_data.user_id}")
        return True
    
    def _create_gentle_nudge(self, reminder_data: ReminderData) -> bool:
        """Create gentle nudge notification (placeholder)."""
        self.logger.info(f"Gentle nudge created for user {reminder_data.user_id}")
        return True
    
    def _create_streak_motivation(self, reminder_data: ReminderData) -> bool:
        """Create streak motivation notification (placeholder)."""
        self.logger.info(f"Streak motivation created for user {reminder_data.user_id}")
        return True
    
    def _track_reminder_sent(self, reminder_data: ReminderData) -> None:
        """Track that a reminder was sent."""
        # This would save to a reminder_tracking table
        self.logger.info(f"Reminder tracked: {reminder_data}")
    
    def _get_default_reminder_time(self) -> datetime:
        """Get default reminder time (Wednesday 10 AM)."""
        now = datetime.utcnow()
        days_ahead = 2 - now.weekday()  # Wednesday is 2
        if days_ahead <= 0:
            days_ahead += 7
        target_date = now + timedelta(days=days_ahead)
        return target_date.replace(hour=10, minute=0, second=0, microsecond=0)
    
    def _get_next_occurrence(self, weekday: str, hour: int) -> datetime:
        """Get next occurrence of a weekday and hour."""
        weekday_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekday_map.get(weekday.lower(), 2)  # Default to Wednesday
        now = datetime.utcnow()
        
        days_ahead = target_weekday - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        target_date = now + timedelta(days=days_ahead)
        return target_date.replace(hour=hour, minute=0, second=0, microsecond=0) 