#!/usr/bin/env python3
"""
Notification Service Utility

Simple notification service for testing purposes
"""

import logging
import time
from typing import Dict, Any, Optional


class NotificationService:
    """Simple notification service for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notifications_sent = []
    
    def send_daily_outlook_notification(self, user_id: int, outlook_id: int) -> bool:
        """Send daily outlook notification"""
        try:
            notification = {
                'user_id': user_id,
                'outlook_id': outlook_id,
                'type': 'daily_outlook_ready',
                'message': 'Your daily outlook is ready!',
                'timestamp': time.time()
            }
            
            self.notifications_sent.append(notification)
            self.logger.info(f"Sent daily outlook notification to user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def send_streak_milestone_notification(self, user_id: int, streak_count: int) -> bool:
        """Send streak milestone notification"""
        try:
            notification = {
                'user_id': user_id,
                'type': 'streak_milestone',
                'streak_count': streak_count,
                'message': f'🎉 {streak_count}-day streak! You\'re on fire!',
                'timestamp': time.time()
            }
            
            self.notifications_sent.append(notification)
            self.logger.info(f"Sent streak milestone notification to user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send streak notification: {e}")
            return False
