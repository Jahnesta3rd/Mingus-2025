"""
Unit Tests for Email Service

Tests include:
- Email sending functionality
- Email template rendering
- Email automation triggers
- Email validation
- Email delivery tracking
- Error handling
- Rate limiting
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.email_automation_service import EmailAutomationService
from backend.services.ai_calculator_email_service import AICalculatorEmailService

class TestEmailAutomationService(unittest.TestCase):
    """Test suite for EmailAutomationService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_DEFAULT_SENDER': 'noreply@example.com',
            'EMAIL_RATE_LIMIT': 100,
            'EMAIL_RATE_LIMIT_WINDOW': 3600
        }
        
        self.email_service = EmailAutomationService(self.mock_config)
        
        self.test_user_data = {
            'id': 'test_user_123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        self.test_assessment_data = {
            'id': 'test_assessment_123',
            'user_id': 'test_user_123',
            'assessment_type': 'job_risk',
            'data': {
                'current_salary': 75000,
                'field': 'software_development',
                'experience_level': 'mid'
            },
            'results': {
                'overall_score': 0.65,
                'risk_level': 'medium',
                'recommendations': ['Learn AI skills', 'Network more']
            }
        }
    
    def test_initialization(self):
        """Test EmailAutomationService initialization"""
        self.assertIsNotNone(self.email_service)
        self.assertEqual(self.email_service.config, self.mock_config)
        self.assertIsNotNone(self.email_service.mail)
    
    @patch('backend.services.email_automation_service.Mail')
    def test_send_assessment_email(self, mock_mail):
        """Test sending assessment completion email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        # Test sending assessment email
        result = self.email_service.send_assessment_email(
            self.test_user_data,
            self.test_assessment_data
        )
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Assessment Complete', message.subject)
        self.assertIn('Test', message.body)
    
    @patch('backend.services.email_automation_service.Mail')
    def test_send_payment_confirmation(self, mock_mail):
        """Test sending payment confirmation email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        payment_data = {
            'amount': 29.99,
            'currency': 'usd',
            'transaction_id': 'txn_test_123',
            'subscription_tier': 'premium'
        }
        
        # Test sending payment confirmation
        result = self.email_service.send_payment_confirmation(
            self.test_user_data,
            payment_data
        )
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Payment Confirmation', message.subject)
        self.assertIn('29.99', message.body)
    
    @patch('backend.services.email_automation_service.Mail')
    def test_send_analytics_report(self, mock_mail):
        """Test sending analytics report email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        analytics_data = {
            'completion_rate': 0.85,
            'average_score': 0.72,
            'total_assessments': 150,
            'insights': ['High engagement on mobile', 'Peak usage on Tuesdays']
        }
        
        # Test sending analytics report
        result = self.email_service.send_analytics_report(
            self.test_user_data,
            analytics_data
        )
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Analytics Report', message.subject)
        self.assertIn('85%', message.body)
    
    def test_email_template_rendering(self):
        """Test email template rendering"""
        # Test assessment email template
        template_data = {
            'user_name': 'Test User',
            'assessment_type': 'Job Risk Assessment',
            'score': 0.75,
            'risk_level': 'Medium',
            'recommendations': ['Learn AI skills', 'Network more']
        }
        
        rendered_template = self.email_service._render_assessment_template(template_data)
        
        self.assertIsInstance(rendered_template, str)
        self.assertIn('Test User', rendered_template)
        self.assertIn('Job Risk Assessment', rendered_template)
        self.assertIn('75%', rendered_template)
        self.assertIn('Medium', rendered_template)
        self.assertIn('Learn AI skills', rendered_template)
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        self.assertTrue(self.email_service._validate_email('test@example.com'))
        self.assertTrue(self.email_service._validate_email('user.name@domain.co.uk'))
        
        # Invalid emails
        self.assertFalse(self.email_service._validate_email('invalid-email'))
        self.assertFalse(self.email_service._validate_email('test@'))
        self.assertFalse(self.email_service._validate_email('@example.com'))
        self.assertFalse(self.email_service._validate_email(''))
        self.assertFalse(self.email_service._validate_email(None))
    
    def test_email_rate_limiting(self):
        """Test email rate limiting"""
        user_id = 'test_user_123'
        
        # Should allow first email
        self.assertTrue(self.email_service._check_rate_limit(user_id))
        
        # Should allow multiple emails within limit
        for i in range(10):
            self.assertTrue(self.email_service._check_rate_limit(user_id))
        
        # Mock rate limit exceeded
        with patch.object(self.email_service, '_get_user_email_count', return_value=101):
            self.assertFalse(self.email_service._check_rate_limit(user_id))
    
    @patch('backend.services.email_automation_service.Mail')
    def test_email_error_handling(self, mock_mail):
        """Test email error handling"""
        # Mock mail to raise exception
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.side_effect = Exception("SMTP Error")
        
        # Should handle error gracefully
        result = self.email_service.send_assessment_email(
            self.test_user_data,
            self.test_assessment_data
        )
        
        self.assertFalse(result)
    
    def test_email_content_sanitization(self):
        """Test email content sanitization"""
        # Test HTML sanitization
        html_content = '<script>alert("xss")</script><p>Hello World</p>'
        sanitized = self.email_service._sanitize_html(html_content)
        
        self.assertNotIn('<script>', sanitized)
        self.assertIn('<p>Hello World</p>', sanitized)
        
        # Test text sanitization
        text_content = 'Hello\nWorld\r\nTest'
        sanitized_text = self.email_service._sanitize_text(text_content)
        
        self.assertNotIn('\r\n', sanitized_text)
        self.assertIn('\n', sanitized_text)
    
    def test_email_automation_triggers(self):
        """Test email automation triggers"""
        # Test assessment completion trigger
        trigger_data = {
            'event_type': 'assessment_completed',
            'user_id': 'test_user_123',
            'assessment_id': 'test_assessment_123',
            'timestamp': datetime.utcnow()
        }
        
        with patch.object(self.email_service, 'send_assessment_email', return_value=True):
            result = self.email_service.handle_automation_trigger(trigger_data)
            self.assertTrue(result)
        
        # Test payment processed trigger
        payment_trigger = {
            'event_type': 'payment_processed',
            'user_id': 'test_user_123',
            'payment_id': 'test_payment_123',
            'amount': 29.99,
            'timestamp': datetime.utcnow()
        }
        
        with patch.object(self.email_service, 'send_payment_confirmation', return_value=True):
            result = self.email_service.handle_automation_trigger(payment_trigger)
            self.assertTrue(result)
        
        # Test unknown trigger
        unknown_trigger = {
            'event_type': 'unknown_event',
            'user_id': 'test_user_123',
            'timestamp': datetime.utcnow()
        }
        
        result = self.email_service.handle_automation_trigger(unknown_trigger)
        self.assertFalse(result)
    
    def test_email_delivery_tracking(self):
        """Test email delivery tracking"""
        email_id = 'test_email_123'
        
        # Track email sent
        self.email_service._track_email_sent(email_id, 'test@example.com', 'assessment_completed')
        
        # Check tracking data
        tracking_data = self.email_service._get_email_tracking(email_id)
        self.assertIsNotNone(tracking_data)
        self.assertEqual(tracking_data['recipient'], 'test@example.com')
        self.assertEqual(tracking_data['type'], 'assessment_completed')
        self.assertIsInstance(tracking_data['sent_at'], datetime)
    
    def test_email_batch_processing(self):
        """Test email batch processing"""
        batch_data = [
            {
                'user': self.test_user_data,
                'assessment': self.test_assessment_data,
                'type': 'assessment_completed'
            },
            {
                'user': self.test_user_data,
                'assessment': self.test_assessment_data,
                'type': 'assessment_completed'
            }
        ]
        
        with patch.object(self.email_service, 'send_assessment_email', return_value=True):
            results = self.email_service.process_email_batch(batch_data)
            
            self.assertEqual(len(results), 2)
            self.assertTrue(all(results))
    
    def test_email_template_variables(self):
        """Test email template variable substitution"""
        template = "Hello {{name}}, your {{assessment_type}} score is {{score}}%"
        variables = {
            'name': 'Test User',
            'assessment_type': 'Job Risk',
            'score': 75
        }
        
        rendered = self.email_service._render_template(template, variables)
        expected = "Hello Test User, your Job Risk score is 75%"
        
        self.assertEqual(rendered, expected)
    
    def test_email_attachment_handling(self):
        """Test email attachment handling"""
        # Test PDF attachment
        pdf_data = b'%PDF-1.4\n...'
        attachment = self.email_service._create_pdf_attachment(pdf_data, 'report.pdf')
        
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.filename, 'report.pdf')
        self.assertEqual(attachment.content_type, 'application/pdf')
        
        # Test CSV attachment
        csv_data = 'name,email,score\nTest,test@example.com,75'
        attachment = self.email_service._create_csv_attachment(csv_data, 'data.csv')
        
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.filename, 'data.csv')
        self.assertEqual(attachment.content_type, 'text/csv')

class TestAICalculatorEmailService(unittest.TestCase):
    """Test suite for AICalculatorEmailService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_DEFAULT_SENDER': 'noreply@example.com'
        }
        
        self.email_service = AICalculatorEmailService(self.mock_config)
        
        self.test_user_data = {
            'id': 'test_user_123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_initialization(self):
        """Test AICalculatorEmailService initialization"""
        self.assertIsNotNone(self.email_service)
        self.assertEqual(self.email_service.config, self.mock_config)
    
    @patch('backend.services.ai_calculator_email_service.Mail')
    def test_send_welcome_email(self, mock_mail):
        """Test sending welcome email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        # Test sending welcome email
        result = self.email_service.send_welcome_email(self.test_user_data)
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Welcome', message.subject)
        self.assertIn('Test', message.body)
    
    @patch('backend.services.ai_calculator_email_service.Mail')
    def test_send_assessment_reminder(self, mock_mail):
        """Test sending assessment reminder email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        # Test sending reminder
        result = self.email_service.send_assessment_reminder(
            self.test_user_data,
            'job_risk'
        )
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Reminder', message.subject)
        self.assertIn('Job Risk Assessment', message.body)
    
    @patch('backend.services.ai_calculator_email_service.Mail')
    def test_send_upgrade_prompt(self, mock_mail):
        """Test sending upgrade prompt email"""
        # Mock the mail instance
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance
        mock_mail_instance.send.return_value = True
        
        # Test sending upgrade prompt
        result = self.email_service.send_upgrade_prompt(
            self.test_user_data,
            'premium'
        )
        
        self.assertTrue(result)
        mock_mail_instance.send.assert_called_once()
        
        # Verify email content
        call_args = mock_mail_instance.send.call_args
        message = call_args[0][0]
        
        self.assertEqual(message.recipients[0], 'test@example.com')
        self.assertIn('Upgrade', message.subject)
        self.assertIn('Premium', message.body)
    
    def test_email_scheduling(self):
        """Test email scheduling functionality"""
        # Schedule welcome email
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        email_id = self.email_service.schedule_email(
            'welcome',
            self.test_user_data,
            scheduled_time
        )
        
        self.assertIsNotNone(email_id)
        
        # Get scheduled emails
        scheduled_emails = self.email_service.get_scheduled_emails()
        self.assertGreater(len(scheduled_emails), 0)
        
        # Cancel scheduled email
        result = self.email_service.cancel_scheduled_email(email_id)
        self.assertTrue(result)
    
    def test_email_analytics(self):
        """Test email analytics tracking"""
        # Track email sent
        self.email_service.track_email_sent('welcome', 'test@example.com')
        
        # Track email opened
        self.email_service.track_email_opened('welcome', 'test@example.com')
        
        # Track email clicked
        self.email_service.track_email_clicked('welcome', 'test@example.com', 'upgrade_link')
        
        # Get analytics
        analytics = self.email_service.get_email_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('sent_count', analytics)
        self.assertIn('open_rate', analytics)
        self.assertIn('click_rate', analytics)

if __name__ == '__main__':
    unittest.main()
