"""
Test MINGUS Celery Tasks System
Validates all SMS and Email communication tasks with proper mocking and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

# Celery imports
from celery.result import AsyncResult

# MINGUS imports
from backend.tasks.mingus_celery_tasks import (
    send_critical_financial_alert, send_payment_reminder, send_weekly_checkin,
    send_milestone_reminder, send_monthly_report, send_career_insights,
    send_educational_content, send_onboarding_sequence,
    monitor_queue_depth, track_delivery_rates, analyze_user_engagement,
    process_failed_messages, optimize_send_timing,
    validate_user_preferences, track_communication_cost, log_delivery_status,
    handle_failed_delivery, generate_personalized_content
)
from backend.models.communication_preferences import (
    CommunicationPreferences, ConsentRecord, CommunicationDeliveryLog,
    AlertType, CommunicationChannel, ConsentStatus
)
from backend.models.user import User


class TestMingusCeleryTasks(unittest.TestCase):
    """Test cases for MINGUS Celery tasks system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user_123"
        self.test_user = User(
            id=self.user_id,
            email="test@example.com",
            full_name="Test User",
            phone_number="+1234567890"
        )
        
        # Mock database session
        self.mock_db = Mock()
        
        # Mock external services
        self.mock_twilio_client = Mock()
        self.mock_resend_client = Mock()
        self.mock_redis_client = Mock()
        
    def tearDown(self):
        """Clean up after tests"""
        pass

    # ============================================================================
    # SMS TASK TESTS
    # ============================================================================
    
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.track_communication_cost')
    @patch('backend.tasks.mingus_celery_tasks.log_delivery_status')
    def test_send_critical_financial_alert_success(self, mock_log, mock_cost, mock_validate, mock_twilio, mock_db):
        """Test successful critical financial alert sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        self.mock_twilio_client.messages.create.return_value = mock_message
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_critical_financial_alert(
            user_id=self.user_id,
            alert_data={
                "template": "Critical: {message}",
                "message": "Overdraft detected",
                "urgency": "high"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_validate.assert_called_once()
        mock_twilio.return_value.messages.create.assert_called_once()
        mock_cost.assert_called_once()
        mock_log.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_critical_financial_alert_user_not_found(self, mock_validate, mock_db):
        """Test critical alert when user not found"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (False, "User not found")
        
        # Execute task
        result = send_critical_financial_alert(
            user_id="nonexistent_user",
            alert_data={"template": "Test", "message": "Test"}
        )
        
        # Assertions
        self.assertFalse(result)
        mock_validate.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.handle_failed_delivery')
    def test_send_critical_financial_alert_twilio_error(self, mock_handle, mock_validate, mock_twilio, mock_db):
        """Test critical alert with Twilio error"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio error
        self.mock_twilio_client.messages.create.side_effect = Exception("Twilio error")
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_critical_financial_alert(
            user_id=self.user_id,
            alert_data={"template": "Test", "message": "Test"}
        )
        
        # Assertions
        self.assertFalse(result)
        mock_handle.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_payment_reminder_success(self, mock_validate, mock_twilio, mock_db):
        """Test successful payment reminder sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        self.mock_twilio_client.messages.create.return_value = mock_message
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_payment_reminder(
            user_id=self.user_id,
            payment_data={
                "template": "Reminder: {bill_name} due {due_date} - ${amount}",
                "bill_name": "Electric Bill",
                "due_date": "2025-01-15",
                "amount": "125.50"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_twilio.return_value.messages.create.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_weekly_checkin_success(self, mock_validate, mock_twilio, mock_db):
        """Test successful weekly checkin sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        self.mock_twilio_client.messages.create.return_value = mock_message
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_weekly_checkin(
            user_id=self.user_id,
            checkin_data={
                "template": "Weekly check-in: {message}",
                "message": "How's your financial wellness?",
                "wellness_score": 85
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_twilio.return_value.messages.create.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_milestone_reminder_success(self, mock_validate, mock_twilio, mock_db):
        """Test successful milestone reminder sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        self.mock_twilio_client.messages.create.return_value = mock_message
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_milestone_reminder(
            user_id=self.user_id,
            milestone_data={
                "template": "🎉 {milestone_name} achieved! {message}",
                "milestone_name": "Emergency Fund Goal",
                "message": "You've saved $5,000!",
                "goal_amount": 5000
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_twilio.return_value.messages.create.assert_called_once()

    # ============================================================================
    # EMAIL TASK TESTS
    # ============================================================================
    
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.track_communication_cost')
    @patch('backend.tasks.mingus_celery_tasks.log_delivery_status')
    def test_send_monthly_report_success(self, mock_log, mock_cost, mock_validate, mock_resend, mock_db):
        """Test successful monthly report sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend response
        mock_response = Mock()
        mock_response.id = "test_email_id"
        self.mock_resend_client.emails.send.return_value = mock_response
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_monthly_report(
            user_id=self.user_id,
            report_data={
                "subject": "Your Monthly Financial Report",
                "html_content": "<h1>Monthly Report</h1><p>Your financial summary...</p>"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_validate.assert_called_once()
        mock_resend.return_value.emails.send.assert_called_once()
        mock_cost.assert_called_once()
        mock_log.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.handle_failed_delivery')
    def test_send_monthly_report_resend_error(self, mock_handle, mock_validate, mock_resend, mock_db):
        """Test monthly report with Resend error"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend error
        self.mock_resend_client.emails.send.side_effect = Exception("Resend error")
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_monthly_report(
            user_id=self.user_id,
            report_data={"subject": "Test", "html_content": "<p>Test</p>"}
        )
        
        # Assertions
        self.assertFalse(result)
        mock_handle.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_career_insights_success(self, mock_validate, mock_resend, mock_db):
        """Test successful career insights sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend response
        mock_response = Mock()
        mock_response.id = "test_email_id"
        self.mock_resend_client.emails.send.return_value = mock_response
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_career_insights(
            user_id=self.user_id,
            career_data={
                "subject": "Career Opportunities for You",
                "html_content": "<h1>Career Insights</h1><p>New opportunities...</p>"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_resend.return_value.emails.send.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_educational_content_success(self, mock_validate, mock_resend, mock_db):
        """Test successful educational content sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend response
        mock_response = Mock()
        mock_response.id = "test_email_id"
        self.mock_resend_client.emails.send.return_value = mock_response
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_educational_content(
            user_id=self.user_id,
            education_data={
                "subject": "Financial Education: Investment Basics",
                "html_content": "<h1>Investment Basics</h1><p>Learn about...</p>",
                "topic": "Investment Basics",
                "difficulty": "beginner"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_resend.return_value.emails.send.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    def test_send_onboarding_sequence_success(self, mock_validate, mock_resend, mock_db):
        """Test successful onboarding sequence sending"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend response
        mock_response = Mock()
        mock_response.id = "test_email_id"
        self.mock_resend_client.emails.send.return_value = mock_response
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_onboarding_sequence(
            user_id=self.user_id,
            onboarding_data={
                "subject": "Welcome to MINGUS!",
                "html_content": "<h1>Welcome!</h1><p>Get started with...</p>",
                "sequence_step": 1,
                "total_steps": 5
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_resend.return_value.emails.send.assert_called_once()

    # ============================================================================
    # MONITORING TASK TESTS
    # ============================================================================
    
    @patch('backend.tasks.mingus_celery_tasks.redis_client')
    def test_monitor_queue_depth_success(self, mock_redis):
        """Test successful queue depth monitoring"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis_client
        self.mock_redis_client.llen.return_value = 50
        
        # Execute task
        result = monitor_queue_depth()
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.mock_redis_client.llen.assert_called()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.communication_analytics_service')
    def test_track_delivery_rates_success(self, mock_analytics, mock_db):
        """Test successful delivery rate tracking"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 100
        self.mock_db.query.return_value = mock_query
        
        # Execute task
        result = track_delivery_rates()
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('delivery_rate', result)
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.communication_analytics_service')
    def test_analyze_user_engagement_success(self, mock_analytics, mock_db):
        """Test successful user engagement analysis"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 10
        self.mock_db.query.return_value = mock_query
        
        # Execute task
        result = analyze_user_engagement()
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('engagement_by_hour', result)
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.send_critical_financial_alert')
    def test_process_failed_messages_success(self, mock_send, mock_db):
        """Test successful failed message processing"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock failed message
        mock_failed_message = Mock()
        mock_failed_message.user_id = self.user_id
        mock_failed_message.channel = CommunicationChannel.SMS
        mock_failed_message.alert_type = 'critical_financial'
        mock_failed_message.id = 'test_message_id'
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_failed_message]
        self.mock_db.query.return_value = mock_query
        
        # Execute task
        result = process_failed_messages()
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('processed_count', result)
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.redis_client')
    def test_optimize_send_timing_success(self, mock_redis, mock_db):
        """Test successful send timing optimization"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_redis.return_value = self.mock_redis_client
        
        # Mock engagement analytics
        mock_analytics = Mock()
        mock_analytics.engagement_by_hour = {9: 10, 10: 15, 11: 8}
        
        # Mock database queries
        mock_query = Mock()
        mock_query.all.return_value = [mock_analytics]
        self.mock_db.query.return_value = mock_query
        
        # Execute task
        result = optimize_send_timing()
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('optimized_users', result)

    # ============================================================================
    # HELPER FUNCTION TESTS
    # ============================================================================
    
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    def test_validate_user_preferences_success(self, mock_db):
        """Test successful user preference validation"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock user and preferences
        mock_preferences = Mock()
        mock_preferences.sms_enabled = True
        
        mock_consent = Mock()
        mock_consent.consent_status = ConsentStatus.GRANTED
        
        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value.first.return_value = self.test_user
        
        pref_query = Mock()
        pref_query.filter.return_value.first.return_value = mock_preferences
        
        consent_query = Mock()
        consent_query.filter.return_value.first.return_value = mock_consent
        
        self.mock_db.query.side_effect = [user_query, pref_query, consent_query]
        
        # Execute function
        can_send, reason = validate_user_preferences(
            self.user_id, CommunicationChannel.SMS, AlertType.CRITICAL_FINANCIAL
        )
        
        # Assertions
        self.assertTrue(can_send)
        self.assertEqual(reason, "Valid")
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    def test_validate_user_preferences_user_not_found(self, mock_db):
        """Test user preference validation when user not found"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = user_query
        
        # Execute function
        can_send, reason = validate_user_preferences(
            "nonexistent_user", CommunicationChannel.SMS, AlertType.CRITICAL_FINANCIAL
        )
        
        # Assertions
        self.assertFalse(can_send)
        self.assertEqual(reason, "User not found")
        
    @patch('backend.tasks.mingus_celery_tasks.redis_client')
    def test_track_communication_cost_success(self, mock_redis):
        """Test successful communication cost tracking"""
        # Setup mocks
        mock_redis.return_value = self.mock_redis_client
        
        # Execute function
        track_communication_cost(
            self.user_id, CommunicationChannel.SMS, 'critical_financial', True
        )
        
        # Assertions
        self.mock_redis_client.hincrby.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    def test_log_delivery_status_success(self, mock_db):
        """Test successful delivery status logging"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Execute function
        log_delivery_status(
            self.user_id, CommunicationChannel.SMS, 'critical_financial',
            'test_message_id', 'delivered'
        )
        
        # Assertions
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.log_delivery_status')
    @patch('backend.tasks.mingus_celery_tasks.communication_analytics_service')
    def test_handle_failed_delivery_success(self, mock_analytics, mock_log):
        """Test successful failed delivery handling"""
        # Execute function
        handle_failed_delivery(
            self.user_id, CommunicationChannel.SMS, 'critical_financial', 'Test error'
        )
        
        # Assertions
        mock_log.assert_called_once()
        mock_analytics.return_value.track_delivery_metrics.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    def test_generate_personalized_content_success(self, mock_db):
        """Test successful personalized content generation"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value.first.return_value = self.test_user
        self.mock_db.query.return_value = user_query
        
        # Execute function
        result = generate_personalized_content(
            self.user_id,
            "Hello {user_name}, your balance is ${balance}",
            {"balance": "1,234.56"}
        )
        
        # Assertions
        self.assertIn("Test User", result)
        self.assertIn("1,234.56", result)
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    def test_generate_personalized_content_user_not_found(self, mock_db):
        """Test personalized content generation when user not found"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        
        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = user_query
        
        template = "Hello {user_name}, your balance is ${balance}"
        
        # Execute function
        result = generate_personalized_content(
            "nonexistent_user", template, {"balance": "1,234.56"}
        )
        
        # Assertions
        self.assertEqual(result, template)  # Should return original template

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.twilio_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.track_communication_cost')
    @patch('backend.tasks.mingus_celery_tasks.log_delivery_status')
    @patch('backend.tasks.mingus_celery_tasks.communication_analytics_service')
    def test_full_sms_workflow_integration(self, mock_analytics, mock_log, mock_cost, mock_validate, mock_twilio, mock_db):
        """Test full SMS workflow integration"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_twilio.return_value = self.mock_twilio_client
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        self.mock_twilio_client.messages.create.return_value = mock_message
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_critical_financial_alert(
            user_id=self.user_id,
            alert_data={
                "template": "Critical: {message}",
                "message": "Overdraft detected",
                "urgency": "high"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_validate.assert_called_once()
        mock_twilio.return_value.messages.create.assert_called_once()
        mock_cost.assert_called_once()
        mock_log.assert_called_once()
        mock_analytics.return_value.track_delivery_metrics.assert_called_once()
        
    @patch('backend.tasks.mingus_celery_tasks.get_db_session')
    @patch('backend.tasks.mingus_celery_tasks.resend_client')
    @patch('backend.tasks.mingus_celery_tasks.validate_user_preferences')
    @patch('backend.tasks.mingus_celery_tasks.track_communication_cost')
    @patch('backend.tasks.mingus_celery_tasks.log_delivery_status')
    @patch('backend.tasks.mingus_celery_tasks.communication_analytics_service')
    def test_full_email_workflow_integration(self, mock_analytics, mock_log, mock_cost, mock_validate, mock_resend, mock_db):
        """Test full email workflow integration"""
        # Setup mocks
        mock_db.return_value = self.mock_db
        mock_validate.return_value = (True, "Valid")
        mock_resend.return_value = self.mock_resend_client
        
        # Mock Resend response
        mock_response = Mock()
        mock_response.id = "test_email_id"
        self.mock_resend_client.emails.send.return_value = mock_response
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_user
        
        # Execute task
        result = send_monthly_report(
            user_id=self.user_id,
            report_data={
                "subject": "Your Monthly Financial Report",
                "html_content": "<h1>Monthly Report</h1><p>Your financial summary...</p>"
            }
        )
        
        # Assertions
        self.assertTrue(result)
        mock_validate.assert_called_once()
        mock_resend.return_value.emails.send.assert_called_once()
        mock_cost.assert_called_once()
        mock_log.assert_called_once()
        mock_analytics.return_value.track_delivery_metrics.assert_called_once()

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_validate_user_preferences_database_error(self):
        """Test user preference validation with database error"""
        with patch('backend.tasks.mingus_celery_tasks.get_db_session') as mock_db:
            mock_db.side_effect = Exception("Database error")
            
            # Execute function
            can_send, reason = validate_user_preferences(
                self.user_id, CommunicationChannel.SMS, AlertType.CRITICAL_FINANCIAL
            )
            
            # Assertions
            self.assertFalse(can_send)
            self.assertIn("Database error", reason)
            
    def test_track_communication_cost_redis_error(self):
        """Test communication cost tracking with Redis error"""
        with patch('backend.tasks.mingus_celery_tasks.redis_client') as mock_redis:
            mock_redis.return_value.hincrby.side_effect = Exception("Redis error")
            
            # Execute function (should not raise exception)
            try:
                track_communication_cost(
                    self.user_id, CommunicationChannel.SMS, 'critical_financial', True
                )
            except Exception as e:
                self.fail(f"track_communication_cost raised exception: {e}")
                
    def test_log_delivery_status_database_error(self):
        """Test delivery status logging with database error"""
        with patch('backend.tasks.mingus_celery_tasks.get_db_session') as mock_db:
            mock_db.return_value.add.side_effect = Exception("Database error")
            
            # Execute function (should not raise exception)
            try:
                log_delivery_status(
                    self.user_id, CommunicationChannel.SMS, 'critical_financial',
                    'test_message_id', 'delivered'
                )
            except Exception as e:
                self.fail(f"log_delivery_status raised exception: {e}")


if __name__ == '__main__':
    unittest.main() 