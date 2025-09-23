#!/usr/bin/env python3
"""
Mingus Notification System Test Script

Comprehensive test suite for the Daily Outlook notification system.
Tests all components including database models, services, and API endpoints.
"""

import os
import sys
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import required modules
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import DailyOutlook
from backend.models.notification_models import (
    UserNotificationPreferences,
    PushSubscription,
    NotificationDelivery,
    NotificationInteraction,
    NotificationTemplate,
    NotificationChannel,
    NotificationType,
    DeliveryStatus,
    InteractionType
)
from backend.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationSystemTester:
    """Test suite for the notification system"""
    
    def __init__(self):
        self.test_results = []
        self.notification_service = NotificationService()
        
    def add_test_result(self, test_name: str, status: str, message: str):
        """Add a test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"{test_name}: {status} - {message}")
    
    def test_database_models(self):
        """Test database model creation and relationships"""
        try:
            # Test UserNotificationPreferences
            prefs = UserNotificationPreferences(
                user_id=1,
                daily_outlook_enabled=True,
                weekday_time=datetime.strptime('06:45', '%H:%M').time(),
                weekend_time=datetime.strptime('08:30', '%H:%M').time(),
                push_enabled=True,
                email_enabled=True,
                sound_enabled=True,
                vibration_enabled=True,
                rich_notifications=True,
                action_buttons=True,
                timezone='America/New_York'
            )
            
            # Test serialization
            prefs_dict = prefs.to_dict()
            assert 'user_id' in prefs_dict
            assert prefs_dict['daily_outlook_enabled'] == True
            
            self.add_test_result('Database Models', 'passed', 'Models created and serialized successfully')
            
        except Exception as e:
            self.add_test_result('Database Models', 'failed', f'Error: {str(e)}')
    
    def test_notification_service(self):
        """Test notification service functionality"""
        try:
            # Test service initialization
            assert self.notification_service is not None
            assert hasattr(self.notification_service, 'default_preferences')
            
            # Test preference management
            prefs = self.notification_service.get_notification_preferences(1)
            assert isinstance(prefs, dict)
            
            # Test content creation (mock data)
            mock_user = type('MockUser', (), {
                'id': 1,
                'first_name': 'Test',
                'email': 'test@example.com'
            })()
            
            mock_outlook = type('MockOutlook', (), {
                'balance_score': 85,
                'streak_count': 5,
                'primary_insight': 'Great progress on your financial goals!',
                'date': date.today()
            })()
            
            mock_preferences = {
                'daily_outlook_enabled': True,
                'action_buttons': True,
                'rich_notifications': True
            }
            
            # Test notification content creation
            content = self.notification_service.create_daily_outlook_notification(
                mock_user, mock_outlook, mock_preferences
            )
            
            assert content.title is not None
            assert content.message is not None
            assert content.balance_score == 85
            assert content.streak_count == 5
            
            self.add_test_result('Notification Service', 'passed', 'Service functions correctly')
            
        except Exception as e:
            self.add_test_result('Notification Service', 'failed', f'Error: {str(e)}')
    
    def test_notification_scheduling(self):
        """Test notification scheduling functionality"""
        try:
            # Test scheduling (mock implementation)
            result = self.notification_service.schedule_daily_outlook_notifications()
            
            assert isinstance(result, dict)
            assert 'success' in result
            
            self.add_test_result('Notification Scheduling', 'passed', 'Scheduling works correctly')
            
        except Exception as e:
            self.add_test_result('Notification Scheduling', 'failed', f'Error: {str(e)}')
    
    def test_notification_content_generation(self):
        """Test notification content generation"""
        try:
            # Test title generation
            mock_user = type('MockUser', (), {'first_name': 'John'})()
            mock_outlook = type('MockOutlook', (), {'balance_score': 90})()
            
            title = self.notification_service._generate_notification_title(mock_user, mock_outlook)
            assert 'John' in title or 'there' in title
            
            # Test message generation
            message = self.notification_service._generate_notification_message(mock_user, mock_outlook)
            assert len(message) > 0
            
            # Test preview generation
            preview = self.notification_service._generate_notification_preview(mock_outlook)
            assert len(preview) > 0
            
            self.add_test_result('Content Generation', 'passed', 'Content generation works correctly')
            
        except Exception as e:
            self.add_test_result('Content Generation', 'failed', f'Error: {str(e)}')
    
    def test_email_notification(self):
        """Test email notification generation"""
        try:
            mock_user = type('MockUser', (), {
                'first_name': 'Test',
                'email': 'test@example.com'
            })()
            
            mock_content = type('MockContent', (), {
                'title': 'Test Notification',
                'message': 'This is a test message',
                'balance_score': 75,
                'streak_count': 3,
                'action_url': '/daily-outlook'
            })()
            
            # Test HTML generation
            html_content = self.notification_service._generate_email_html(mock_user, mock_content)
            assert '<html>' in html_content
            assert 'Test Notification' in html_content
            
            # Test text generation
            text_content = self.notification_service._generate_email_text(mock_user, mock_content)
            assert 'Test Notification' in text_content
            
            self.add_test_result('Email Notification', 'passed', 'Email generation works correctly')
            
        except Exception as e:
            self.add_test_result('Email Notification', 'failed', f'Error: {str(e)}')
    
    def test_analytics_tracking(self):
        """Test analytics and tracking functionality"""
        try:
            # Test interaction tracking
            result = self.notification_service.track_notification_interaction(
                'test-notification-123',
                'clicked',
                {'action': 'view_outlook'}
            )
            
            assert result == True
            
            # Test stats retrieval
            stats = self.notification_service.get_notification_stats(1)
            assert isinstance(stats, dict)
            
            self.add_test_result('Analytics Tracking', 'passed', 'Analytics tracking works correctly')
            
        except Exception as e:
            self.add_test_result('Analytics Tracking', 'failed', f'Error: {str(e)}')
    
    def test_timezone_handling(self):
        """Test timezone-aware notification handling"""
        try:
            # Test timezone calculation
            delivery_time = self.notification_service._calculate_delivery_time(
                'America/New_York',
                '07:00'
            )
            
            assert isinstance(delivery_time, datetime)
            
            # Test different timezones
            utc_time = self.notification_service._calculate_delivery_time(
                'UTC',
                '12:00'
            )
            
            assert isinstance(utc_time, datetime)
            
            self.add_test_result('Timezone Handling', 'passed', 'Timezone handling works correctly')
            
        except Exception as e:
            self.add_test_result('Timezone Handling', 'failed', f'Error: {str(e)}')
    
    def test_notification_templates(self):
        """Test notification template functionality"""
        try:
            # Test template creation
            template = NotificationTemplate(
                name='test_template',
                notification_type=NotificationType.DAILY_OUTLOOK,
                channel=NotificationChannel.PUSH,
                title_template='Hello {first_name}!',
                message_template='Your balance score is {balance_score}',
                variables={'first_name': 'string', 'balance_score': 'integer'},
                is_active=True,
                priority='normal'
            )
            
            # Test template serialization
            template_dict = template.to_dict()
            assert template_dict['name'] == 'test_template'
            assert template_dict['notification_type'] == 'daily_outlook'
            
            self.add_test_result('Notification Templates', 'passed', 'Templates work correctly')
            
        except Exception as e:
            self.add_test_result('Notification Templates', 'failed', f'Error: {str(e)}')
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        try:
            # Test with invalid data
            try:
                self.notification_service.create_daily_outlook_notification(
                    None, None, {}
                )
                self.add_test_result('Error Handling', 'failed', 'Should have handled None inputs')
            except Exception:
                self.add_test_result('Error Handling', 'passed', 'Properly handles invalid inputs')
            
            # Test with empty preferences
            prefs = self.notification_service.get_notification_preferences(999999)
            assert isinstance(prefs, dict)
            
            self.add_test_result('Error Handling', 'passed', 'Error handling works correctly')
            
        except Exception as e:
            self.add_test_result('Error Handling', 'failed', f'Error: {str(e)}')
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting notification system tests...")
        
        # Run all test methods
        test_methods = [
            self.test_database_models,
            self.test_notification_service,
            self.test_notification_scheduling,
            self.test_notification_content_generation,
            self.test_email_notification,
            self.test_analytics_tracking,
            self.test_timezone_handling,
            self.test_notification_templates,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.add_test_result(test_method.__name__, 'failed', f'Unexpected error: {str(e)}')
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results"""
        print("\n" + "="*60)
        print("NOTIFICATION SYSTEM TEST RESULTS")
        print("="*60)
        
        passed = len([r for r in self.test_results if r['status'] == 'passed'])
        failed = len([r for r in self.test_results if r['status'] == 'failed'])
        total = len(self.test_results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        if failed > 0:
            print(f"\n❌ {failed} test(s) failed. Please check the errors above.")
        else:
            print(f"\n✅ All {total} tests passed! Notification system is working correctly.")
        
        print("="*60)

def main():
    """Main test runner"""
    print("Mingus Notification System Test Suite")
    print("=====================================")
    
    tester = NotificationSystemTester()
    tester.run_all_tests()
    
    return 0 if all(r['status'] == 'passed' for r in tester.test_results) else 1

if __name__ == '__main__':
    sys.exit(main())
