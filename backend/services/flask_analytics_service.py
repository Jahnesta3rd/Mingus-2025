"""
Flask Analytics Service
Provides easy-to-use functions for tracking analytics data in Flask applications
"""

import logging
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .analytics_service import AnalyticsService
from ..database import get_db_session

logger = logging.getLogger(__name__)


class FlaskAnalyticsService:
    """
    Flask-specific analytics service for easy integration
    """
    
    def __init__(self):
        """Initialize the Flask analytics service"""
        self.analytics_service = AnalyticsService()
    
    def track_message_sent(self, user_id: int, channel: str, message_type: str, cost: float = 0.0):
        """
        Track when a message is sent
        
        Args:
            user_id: User ID
            channel: Communication channel ("sms" or "email")
            message_type: Type of message (e.g., "low_balance", "weekly_checkin")
            cost: Cost in dollars (default: 0.0)
            
        Returns:
            CommunicationMetrics object or None if failed
        """
        try:
            return self.analytics_service.track_message_sent(
                user_id=user_id,
                channel=channel,
                message_type=message_type,
                cost=cost
            )
        except Exception as e:
            logger.error(f"Failed to track message sent: {e}")
            return None
    
    def track_message_delivered(self, message_id: int, delivery_time: Optional[datetime] = None):
        """
        Track when a message is delivered
        
        Args:
            message_id: Message ID
            delivery_time: When message was delivered (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object or None if failed
        """
        try:
            return self.analytics_service.track_message_delivered(
                message_id=message_id,
                delivery_time=delivery_time
            )
        except Exception as e:
            logger.error(f"Failed to track message delivered: {e}")
            return None
    
    def track_message_opened(self, message_id: int, open_time: Optional[datetime] = None):
        """
        Track when a message is opened
        
        Args:
            message_id: Message ID
            open_time: When message was opened (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object or None if failed
        """
        try:
            return self.analytics_service.track_message_opened(
                message_id=message_id,
                open_time=open_time
            )
        except Exception as e:
            logger.error(f"Failed to track message opened: {e}")
            return None
    
    def track_user_action(self, message_id: int, action_type: str, timestamp: Optional[datetime] = None):
        """
        Track user action taken in response to a message
        
        Args:
            message_id: Message ID
            action_type: Type of action taken (e.g., "viewed_forecast", "updated_budget")
            timestamp: When action was taken (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object or None if failed
        """
        try:
            return self.analytics_service.track_user_action(
                message_id=message_id,
                action_type=action_type,
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(f"Failed to track user action: {e}")
            return None
    
    def track_financial_outcome(self, user_id: int, action: str, impact_amount: float):
        """
        Track financial outcome resulting from user actions
        
        Args:
            user_id: User ID
            action: Action that led to financial outcome (e.g., "bill_paid_on_time", "savings_goal_achieved")
            impact_amount: Dollar amount of the financial impact
            
        Returns:
            FinancialImpactMetrics object or None if failed
        """
        try:
            return self.analytics_service.track_financial_outcome(
                user_id=user_id,
                action=action,
                impact_amount=impact_amount
            )
        except Exception as e:
            logger.error(f"Failed to track financial outcome: {e}")
            return None
    
    def get_user_communication_history(self, user_id: int, limit: int = 100):
        """
        Get communication history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of CommunicationMetrics objects or empty list if failed
        """
        try:
            return self.analytics_service.get_user_communication_history(
                user_id=user_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get user communication history: {e}")
            return []
    
    def get_communication_stats(self, user_id: Optional[int] = None, **filters):
        """
        Get communication statistics
        
        Args:
            user_id: Filter by user ID (optional)
            **filters: Additional filters (message_type, channel, start_date, end_date)
            
        Returns:
            Dictionary with communication statistics or empty dict if failed
        """
        try:
            return self.analytics_service.get_communication_stats(
                user_id=user_id,
                **filters
            )
        except Exception as e:
            logger.error(f"Failed to get communication stats: {e}")
            return {}
    
    def close(self):
        """Close the analytics service"""
        self.analytics_service.close()


# Global instance for easy access
flask_analytics = FlaskAnalyticsService()


# Convenience functions for direct use in Flask routes
def track_message_sent(user_id: int, channel: str, message_type: str, cost: float = 0.0):
    """Convenience function to track message sent"""
    return flask_analytics.track_message_sent(user_id, channel, message_type, cost)


def track_message_delivered(message_id: int, delivery_time: Optional[datetime] = None):
    """Convenience function to track message delivered"""
    return flask_analytics.track_message_delivered(message_id, delivery_time)


def track_message_opened(message_id: int, open_time: Optional[datetime] = None):
    """Convenience function to track message opened"""
    return flask_analytics.track_message_opened(message_id, open_time)


def track_user_action(message_id: int, action_type: str, timestamp: Optional[datetime] = None):
    """Convenience function to track user action"""
    return flask_analytics.track_user_action(message_id, action_type, timestamp)


def track_financial_outcome(user_id: int, action: str, impact_amount: float):
    """Convenience function to track financial outcome"""
    return flask_analytics.track_financial_outcome(user_id, action, impact_amount)


def get_user_communication_history(user_id: int, limit: int = 100):
    """Convenience function to get user communication history"""
    return flask_analytics.get_user_communication_history(user_id, limit)


def get_communication_stats(user_id: Optional[int] = None, **filters):
    """Convenience function to get communication statistics"""
    return flask_analytics.get_communication_stats(user_id, **filters) 