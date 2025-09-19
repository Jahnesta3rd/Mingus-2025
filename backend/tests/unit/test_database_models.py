"""
Unit Tests for Database Models

Tests include:
- Model validations
- Field constraints
- Relationship integrity
- Data type validations
- Unique constraints
- Foreign key relationships
- Model methods
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

from backend.models import (
    User, UserProfile
)
from backend.models.assessment_models import Assessment
from backend.models.assessment_analytics_models import AssessmentAnalyticsEvent as AssessmentAnalytics
from backend.models.subscription import Subscription, PaymentMethod, BillingHistory
from backend.models.communication_preferences import CommunicationPreferences

class TestUserModel(unittest.TestCase):
    """Test suite for User model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_user_data = {
            'id': 'test_user_123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'subscription_tier': 'basic',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
    
    def test_user_creation(self):
        """Test user creation with valid data"""
        user = User(**self.valid_user_data)
        
        self.assertEqual(user.id, 'test_user_123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.subscription_tier, 'basic')
        self.assertTrue(user.is_active)
        self.assertIsInstance(user.created_at, datetime)
    
    def test_user_email_validation(self):
        """Test email validation"""
        # Valid email
        user = User(**self.valid_user_data)
        self.assertIsInstance(user.email, str)
        self.assertIn('@', user.email)
        
        # Invalid email should raise validation error
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        with self.assertRaises(Exception):
            User(**invalid_data)
    
    def test_user_subscription_tier_validation(self):
        """Test subscription tier validation"""
        valid_tiers = ['basic', 'premium', 'enterprise']
        
        for tier in valid_tiers:
            data = self.valid_user_data.copy()
            data['subscription_tier'] = tier
            user = User(**data)
            self.assertEqual(user.subscription_tier, tier)
        
        # Invalid tier should raise validation error
        invalid_data = self.valid_user_data.copy()
        invalid_data['subscription_tier'] = 'invalid_tier'
        
        with self.assertRaises(Exception):
            User(**invalid_data)
    
    def test_user_relationships(self):
        """Test user relationships"""
        user = User(**self.valid_user_data)
        
        # Test assessments relationship
        self.assertIsInstance(user.assessments, list)
        
        # Test analytics relationship
        self.assertIsInstance(user.analytics, list)
        
        # Test payments relationship
        self.assertIsInstance(user.payments, list)

class TestAssessmentModel(unittest.TestCase):
    """Test suite for Assessment model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_assessment_data = {
            'id': 'test_assessment_123',
            'user_id': 'test_user_123',
            'assessment_type': 'job_risk',
            'data': {
                'current_salary': 75000,
                'field': 'software_development',
                'experience_level': 'mid'
            },
            'created_at': datetime.utcnow(),
            'status': 'completed'
        }
    
    def test_assessment_creation(self):
        """Test assessment creation with valid data"""
        assessment = Assessment(**self.valid_assessment_data)
        
        self.assertEqual(assessment.id, 'test_assessment_123')
        self.assertEqual(assessment.user_id, 'test_user_123')
        self.assertEqual(assessment.assessment_type, 'job_risk')
        self.assertEqual(assessment.status, 'completed')
        self.assertIsInstance(assessment.data, dict)
        self.assertIsInstance(assessment.created_at, datetime)
    
    def test_assessment_type_validation(self):
        """Test assessment type validation"""
        valid_types = ['job_risk', 'relationship_impact', 'income_comparison']
        
        for assessment_type in valid_types:
            data = self.valid_assessment_data.copy()
            data['assessment_type'] = assessment_type
            assessment = Assessment(**data)
            self.assertEqual(assessment.assessment_type, assessment_type)
        
        # Invalid type should raise validation error
        invalid_data = self.valid_assessment_data.copy()
        invalid_data['assessment_type'] = 'invalid_type'
        
        with self.assertRaises(Exception):
            Assessment(**invalid_data)
    
    def test_assessment_status_validation(self):
        """Test assessment status validation"""
        valid_statuses = ['pending', 'in_progress', 'completed', 'failed']
        
        for status in valid_statuses:
            data = self.valid_assessment_data.copy()
            data['status'] = status
            assessment = Assessment(**data)
            self.assertEqual(assessment.status, status)
        
        # Invalid status should raise validation error
        invalid_data = self.valid_assessment_data.copy()
        invalid_data['status'] = 'invalid_status'
        
        with self.assertRaises(Exception):
            Assessment(**invalid_data)
    
    def test_assessment_data_validation(self):
        """Test assessment data validation"""
        # Valid JSON data
        assessment = Assessment(**self.valid_assessment_data)
        self.assertIsInstance(assessment.data, dict)
        
        # Invalid data should raise validation error
        invalid_data = self.valid_assessment_data.copy()
        invalid_data['data'] = "invalid_json_string"
        
        with self.assertRaises(Exception):
            Assessment(**invalid_data)
    
    def test_assessment_relationships(self):
        """Test assessment relationships"""
        assessment = Assessment(**self.valid_assessment_data)
        
        # Test user relationship
        self.assertEqual(assessment.user_id, 'test_user_123')
        
        # Test analytics relationship
        self.assertIsInstance(assessment.analytics, list)

class TestAssessmentAnalyticsModel(unittest.TestCase):
    """Test suite for AssessmentAnalytics model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_analytics_data = {
            'id': 'test_analytics_123',
            'assessment_id': 'test_assessment_123',
            'user_id': 'test_user_123',
            'event_type': 'assessment_completed',
            'event_data': {
                'completion_time': 120,
                'score': 0.75,
                'risk_level': 'medium'
            },
            'created_at': datetime.utcnow(),
            'session_id': 'test_session_123'
        }
    
    def test_analytics_creation(self):
        """Test analytics creation with valid data"""
        analytics = AssessmentAnalytics(**self.valid_analytics_data)
        
        self.assertEqual(analytics.id, 'test_analytics_123')
        self.assertEqual(analytics.assessment_id, 'test_assessment_123')
        self.assertEqual(analytics.user_id, 'test_user_123')
        self.assertEqual(analytics.event_type, 'assessment_completed')
        self.assertIsInstance(analytics.event_data, dict)
        self.assertIsInstance(analytics.created_at, datetime)
    
    def test_analytics_event_type_validation(self):
        """Test analytics event type validation"""
        valid_event_types = [
            'assessment_started', 'assessment_completed', 'payment_processed',
            'email_sent', 'user_registered', 'subscription_upgraded'
        ]
        
        for event_type in valid_event_types:
            data = self.valid_analytics_data.copy()
            data['event_type'] = event_type
            analytics = AssessmentAnalytics(**data)
            self.assertEqual(analytics.event_type, event_type)
        
        # Invalid event type should raise validation error
        invalid_data = self.valid_analytics_data.copy()
        invalid_data['event_type'] = 'invalid_event'
        
        with self.assertRaises(Exception):
            AssessmentAnalytics(**invalid_data)
    
    def test_analytics_event_data_validation(self):
        """Test analytics event data validation"""
        # Valid event data
        analytics = AssessmentAnalytics(**self.valid_analytics_data)
        self.assertIsInstance(analytics.event_data, dict)
        
        # Empty event data should be allowed
        empty_data = self.valid_analytics_data.copy()
        empty_data['event_data'] = {}
        analytics = AssessmentAnalytics(**empty_data)
        self.assertEqual(analytics.event_data, {})
    
    def test_analytics_relationships(self):
        """Test analytics relationships"""
        analytics = AssessmentAnalytics(**self.valid_analytics_data)
        
        # Test assessment relationship
        self.assertEqual(analytics.assessment_id, 'test_assessment_123')
        
        # Test user relationship
        self.assertEqual(analytics.user_id, 'test_user_123')

class TestSubscriptionModel(unittest.TestCase):
    """Test suite for Subscription model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_subscription_data = {
            'id': 'test_subscription_123',
            'user_id': 'test_user_123',
            'tier': 'premium',
            'status': 'active',
            'start_date': datetime.utcnow(),
            'end_date': datetime.utcnow() + timedelta(days=30),
            'amount': 29.99,
            'currency': 'usd',
            'auto_renew': True
        }
    
    def test_subscription_creation(self):
        """Test subscription creation with valid data"""
        subscription = Subscription(**self.valid_subscription_data)
        
        self.assertEqual(subscription.id, 'test_subscription_123')
        self.assertEqual(subscription.user_id, 'test_user_123')
        self.assertEqual(subscription.tier, 'premium')
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.amount, 29.99)
        self.assertEqual(subscription.currency, 'usd')
        self.assertTrue(subscription.auto_renew)
    
    def test_subscription_tier_validation(self):
        """Test subscription tier validation"""
        valid_tiers = ['basic', 'premium', 'enterprise']
        
        for tier in valid_tiers:
            data = self.valid_subscription_data.copy()
            data['tier'] = tier
            subscription = Subscription(**data)
            self.assertEqual(subscription.tier, tier)
        
        # Invalid tier should raise validation error
        invalid_data = self.valid_subscription_data.copy()
        invalid_data['tier'] = 'invalid_tier'
        
        with self.assertRaises(Exception):
            Subscription(**invalid_data)
    
    def test_subscription_status_validation(self):
        """Test subscription status validation"""
        valid_statuses = ['active', 'cancelled', 'expired', 'pending']
        
        for status in valid_statuses:
            data = self.valid_subscription_data.copy()
            data['status'] = status
            subscription = Subscription(**data)
            self.assertEqual(subscription.status, status)
        
        # Invalid status should raise validation error
        invalid_data = self.valid_subscription_data.copy()
        invalid_data['status'] = 'invalid_status'
        
        with self.assertRaises(Exception):
            Subscription(**invalid_data)
    
    def test_subscription_date_validation(self):
        """Test subscription date validation"""
        # Valid dates
        subscription = Subscription(**self.valid_subscription_data)
        self.assertIsInstance(subscription.start_date, datetime)
        self.assertIsInstance(subscription.end_date, datetime)
        self.assertLess(subscription.start_date, subscription.end_date)
        
        # Invalid dates (end before start) should raise validation error
        invalid_data = self.valid_subscription_data.copy()
        invalid_data['start_date'] = datetime.utcnow() + timedelta(days=30)
        invalid_data['end_date'] = datetime.utcnow()
        
        with self.assertRaises(Exception):
            Subscription(**invalid_data)
    
    def test_subscription_amount_validation(self):
        """Test subscription amount validation"""
        # Valid amount
        subscription = Subscription(**self.valid_subscription_data)
        self.assertGreater(subscription.amount, 0)
        
        # Zero amount should raise validation error
        invalid_data = self.valid_subscription_data.copy()
        invalid_data['amount'] = 0
        
        with self.assertRaises(Exception):
            Subscription(**invalid_data)
        
        # Negative amount should raise validation error
        invalid_data['amount'] = -10
        
        with self.assertRaises(Exception):
            Subscription(**invalid_data)

class TestPaymentMethodModel(unittest.TestCase):
    """Test suite for PaymentMethod model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_payment_method_data = {
            'id': 'test_payment_method_123',
            'customer_id': 'test_customer_123',
            'payment_method_type': 'card',
            'payment_method_id': 'pm_test_123',
            'is_default': True,
            'created_at': datetime.utcnow()
        }
    
    def test_payment_method_creation(self):
        """Test payment method creation with valid data"""
        payment_method = PaymentMethod(**self.valid_payment_method_data)
        
        self.assertEqual(payment_method.id, 'test_payment_method_123')
        self.assertEqual(payment_method.customer_id, 'test_customer_123')
        self.assertEqual(payment_method.payment_method_type, 'card')
        self.assertEqual(payment_method.payment_method_id, 'pm_test_123')
        self.assertTrue(payment_method.is_default)
    
    def test_payment_method_type_validation(self):
        """Test payment method type validation"""
        valid_types = ['card', 'bank_transfer', 'paypal', 'apple_pay']
        
        for method_type in valid_types:
            data = self.valid_payment_method_data.copy()
            data['payment_method_type'] = method_type
            payment_method = PaymentMethod(**data)
            self.assertEqual(payment_method.payment_method_type, method_type)
        
        # Invalid type should raise validation error
        invalid_data = self.valid_payment_method_data.copy()
        invalid_data['payment_method_type'] = 'invalid_type'
        
        with self.assertRaises(Exception):
            PaymentMethod(**invalid_data)

class TestCommunicationPreferencesModel(unittest.TestCase):
    """Test suite for CommunicationPreferences model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_preferences_data = {
            'id': 'test_preferences_123',
            'user_id': 'test_user_123',
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'marketing_emails': True,
            'assessment_reminders': True,
            'payment_notifications': True,
            'frequency': 'weekly',
            'timezone': 'UTC',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def test_preferences_creation(self):
        """Test preferences creation with valid data"""
        preferences = CommunicationPreferences(**self.valid_preferences_data)
        
        self.assertEqual(preferences.id, 'test_preferences_123')
        self.assertEqual(preferences.user_id, 'test_user_123')
        self.assertTrue(preferences.email_enabled)
        self.assertFalse(preferences.sms_enabled)
        self.assertTrue(preferences.push_enabled)
        self.assertTrue(preferences.marketing_emails)
        self.assertTrue(preferences.assessment_reminders)
        self.assertTrue(preferences.payment_notifications)
        self.assertEqual(preferences.frequency, 'weekly')
        self.assertEqual(preferences.timezone, 'UTC')
    
    def test_preferences_frequency_validation(self):
        """Test preferences frequency validation"""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']
        
        for frequency in valid_frequencies:
            data = self.valid_preferences_data.copy()
            data['frequency'] = frequency
            preferences = CommunicationPreferences(**data)
            self.assertEqual(preferences.frequency, frequency)
        
        # Invalid frequency should raise validation error
        invalid_data = self.valid_preferences_data.copy()
        invalid_data['frequency'] = 'invalid_frequency'
        
        with self.assertRaises(Exception):
            CommunicationPreferences(**invalid_data)
    
    def test_preferences_boolean_validation(self):
        """Test preferences boolean field validation"""
        # Test boolean fields
        preferences = CommunicationPreferences(**self.valid_preferences_data)
        
        self.assertIsInstance(preferences.email_enabled, bool)
        self.assertIsInstance(preferences.sms_enabled, bool)
        self.assertIsInstance(preferences.push_enabled, bool)
        self.assertIsInstance(preferences.marketing_emails, bool)
        self.assertIsInstance(preferences.assessment_reminders, bool)
        self.assertIsInstance(preferences.payment_notifications, bool)
    
    def test_preferences_timezone_validation(self):
        """Test preferences timezone validation"""
        valid_timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']
        
        for timezone in valid_timezones:
            data = self.valid_preferences_data.copy()
            data['timezone'] = timezone
            preferences = CommunicationPreferences(**data)
            self.assertEqual(preferences.timezone, timezone)
        
        # Invalid timezone should raise validation error
        invalid_data = self.valid_preferences_data.copy()
        invalid_data['timezone'] = 'invalid_timezone'
        
        with self.assertRaises(Exception):
            CommunicationPreferences(**invalid_data)

if __name__ == '__main__':
    unittest.main()
