"""
Test Enhanced Communication Preferences System
Validates all communication preference management, consent handling, and compliance features
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, time
import uuid

from backend.services.communication_preference_service import CommunicationPreferenceService
from backend.models.communication_preferences import (
    CommunicationPreferences, SMSConsent, ConsentRecord, AlertTypePreference,
    DeliveryLog, OptOutHistory, UserEngagementMetrics, CommunicationPolicy,
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus, UserSegment
)
from backend.models.user import User


class TestCommunicationPreferencesEnhanced(unittest.TestCase):
    """Test cases for enhanced communication preferences system"""
    
    def setUp(self):
        self.service = CommunicationPreferenceService()
        self.user_id = 123
        self.test_user = User(
            id=self.user_id,
            email="test@example.com",
            full_name="Test User",
            phone_number="+1234567890"
        )
        
    def tearDown(self):
        pass

    # ============================================================================
    # PREFERENCE MANAGEMENT TESTS
    # ============================================================================
    
    def test_get_user_communication_prefs(self):
        """Test getting user communication preferences"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.id = "test_id"
            mock_preferences.user_id = self.user_id
            mock_preferences.sms_enabled = True
            mock_preferences.email_enabled = True
            mock_preferences.preferred_sms_time = time(9, 0)
            mock_preferences.preferred_email_time = time(18, 0)
            mock_preferences.preferred_email_day = 1
            mock_preferences.alert_types_sms = {"critical_financial": True}
            mock_preferences.alert_types_email = {"critical_financial": True}
            mock_preferences.frequency_preference = FrequencyType.WEEKLY
            mock_preferences.user_segment = UserSegment.NEW_USER
            mock_preferences.created_at = datetime.utcnow()
            mock_preferences.updated_at = datetime.utcnow()
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            # Test
            result = self.service.get_user_communication_prefs(self.user_id)
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result['user_id'], self.user_id)
            self.assertTrue(result['sms_enabled'])
            self.assertTrue(result['email_enabled'])
            self.assertEqual(result['preferred_sms_time'], '09:00')
            self.assertEqual(result['preferred_email_time'], '18:00')
            self.assertEqual(result['preferred_email_day'], 1)
            self.assertEqual(result['frequency_preference'], 'weekly')
            self.assertEqual(result['user_segment'], 'new_user')
    
    def test_get_user_communication_prefs_not_found(self):
        """Test getting preferences when user not found"""
        with patch.object(self.service, 'db') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result = self.service.get_user_communication_prefs(self.user_id)
            
            self.assertIsNone(result)
    
    def test_update_user_preferences(self):
        """Test updating user preferences"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing preferences
            mock_preferences = Mock()
            mock_preferences.sms_enabled = True
            mock_preferences.email_enabled = True
            mock_preferences.updated_at = datetime.utcnow()
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            # Test data
            update_data = {
                'sms_enabled': False,
                'preferred_sms_time': '10:00',
                'frequency_preference': 'daily'
            }
            
            # Test
            result = self.service.update_user_preferences(self.user_id, update_data)
            
            # Assertions
            self.assertTrue(result)
            self.assertFalse(mock_preferences.sms_enabled)
            self.assertEqual(mock_preferences.preferred_sms_time, time(10, 0))
            self.assertEqual(mock_preferences.frequency_preference, FrequencyType.DAILY)
            mock_db.commit.assert_called_once()
    
    def test_update_user_preferences_create_new(self):
        """Test updating preferences when none exist"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock no existing preferences
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock create_default_preferences
            with patch.object(self.service, '_create_default_preferences') as mock_create:
                mock_preferences = Mock()
                mock_create.return_value = mock_preferences
                
                update_data = {'sms_enabled': False}
                
                # Test
                result = self.service.update_user_preferences(self.user_id, update_data)
                
                # Assertions
                self.assertTrue(result)
                mock_create.assert_called_once_with(self.user_id)
                mock_db.add.assert_called_once_with(mock_preferences)
                mock_db.commit.assert_called_once()

    # ============================================================================
    # CONSENT MANAGEMENT TESTS
    # ============================================================================
    
    def test_check_consent_for_message_type_sms_success(self):
        """Test SMS consent checking - success case"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                self.test_user,  # User query
                Mock(sms_enabled=True, alert_types_sms={"critical_financial": True}),  # Preferences query
                Mock(consent_granted=True, opted_out=False),  # SMS consent query
                None  # Opt-out history query
            ]
            
            result, reason = self.service.check_consent_for_message_type(
                self.user_id, "critical_financial", CommunicationChannel.SMS
            )
            
            self.assertTrue(result)
            self.assertEqual(reason, "Consent verified")
    
    def test_check_consent_for_message_type_sms_disabled(self):
        """Test SMS consent checking - SMS disabled"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                self.test_user,  # User query
                Mock(sms_enabled=False)  # Preferences query
            ]
            
            result, reason = self.service.check_consent_for_message_type(
                self.user_id, "critical_financial", CommunicationChannel.SMS
            )
            
            self.assertFalse(result)
            self.assertEqual(reason, "SMS communications disabled")
    
    def test_check_consent_for_message_type_email_success(self):
        """Test email consent checking - success case"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                self.test_user,  # User query
                Mock(email_enabled=True, alert_types_email={"critical_financial": True}),  # Preferences query
                Mock(consent_status=ConsentStatus.GRANTED),  # Email consent query
                None  # Opt-out history query
            ]
            
            result, reason = self.service.check_consent_for_message_type(
                self.user_id, "critical_financial", CommunicationChannel.EMAIL
            )
            
            self.assertTrue(result)
            self.assertEqual(reason, "Consent verified")
    
    def test_check_consent_for_message_type_user_not_found(self):
        """Test consent checking when user not found"""
        with patch.object(self.service, 'db') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result, reason = self.service.check_consent_for_message_type(
                self.user_id, "critical_financial", CommunicationChannel.SMS
            )
            
            self.assertFalse(result)
            self.assertEqual(reason, "User not found")

    # ============================================================================
    # OPT-OUT MANAGEMENT TESTS
    # ============================================================================
    
    def test_handle_opt_out_request_sms(self):
        """Test handling SMS opt-out request"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.sms_enabled = True
            mock_preferences.alert_types_sms = {"critical_financial": True}
            mock_preferences.updated_at = datetime.utcnow()
            
            # Mock SMS consent
            mock_sms_consent = Mock()
            mock_sms_consent.opted_out = False
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_preferences,  # Preferences query
                mock_sms_consent   # SMS consent query
            ]
            
            # Test
            result = self.service.handle_opt_out_request(
                self.user_id, CommunicationChannel.SMS, "critical_financial", "User request"
            )
            
            # Assertions
            self.assertTrue(result)
            self.assertFalse(mock_preferences.sms_enabled)
            self.assertFalse(mock_preferences.alert_types_sms["critical_financial"])
            self.assertTrue(mock_sms_consent.opted_out)
            mock_db.add.assert_called_once()  # OptOutHistory record
            mock_db.commit.assert_called_once()
    
    def test_handle_opt_out_request_email(self):
        """Test handling email opt-out request"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.email_enabled = True
            mock_preferences.alert_types_email = {"critical_financial": True}
            mock_preferences.updated_at = datetime.utcnow()
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            # Test
            result = self.service.handle_opt_out_request(
                self.user_id, CommunicationChannel.EMAIL, "critical_financial", "User request"
            )
            
            # Assertions
            self.assertTrue(result)
            self.assertFalse(mock_preferences.email_enabled)
            self.assertFalse(mock_preferences.alert_types_email["critical_financial"])
            mock_db.add.assert_called_once()  # OptOutHistory record
            mock_db.commit.assert_called_once()

    # ============================================================================
    # OPTIMAL SEND TIME TESTS
    # ============================================================================
    
    def test_get_optimal_send_time_sms(self):
        """Test getting optimal SMS send time"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.preferred_sms_time = time(9, 0)
            mock_preferences.timezone = "UTC"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            with patch('backend.services.communication_preference_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 1, 27, 8, 0)  # 8 AM
                
                result = self.service.get_optimal_send_time(self.user_id, CommunicationChannel.SMS)
                
                # Should be today at 9 AM
                expected_time = datetime(2025, 1, 27, 9, 0)
                self.assertEqual(result, expected_time)
    
    def test_get_optimal_send_time_sms_passed_today(self):
        """Test getting optimal SMS send time when it has passed today"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.preferred_sms_time = time(9, 0)
            mock_preferences.timezone = "UTC"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            with patch('backend.services.communication_preference_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 1, 27, 10, 0)  # 10 AM
                
                result = self.service.get_optimal_send_time(self.user_id, CommunicationChannel.SMS)
                
                # Should be tomorrow at 9 AM
                expected_time = datetime(2025, 1, 28, 9, 0)
                self.assertEqual(result, expected_time)
    
    def test_get_optimal_send_time_email(self):
        """Test getting optimal email send time"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.preferred_email_time = time(18, 0)
            mock_preferences.preferred_email_day = 1  # Tuesday
            mock_preferences.timezone = "UTC"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            with patch('backend.services.communication_preference_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 1, 27, 10, 0)  # Monday 10 AM
                
                result = self.service.get_optimal_send_time(self.user_id, CommunicationChannel.EMAIL)
                
                # Should be Tuesday at 6 PM
                expected_time = datetime(2025, 1, 28, 18, 0)
                self.assertEqual(result, expected_time)

    # ============================================================================
    # SMS CONSENT TESTS
    # ============================================================================
    
    def test_grant_sms_consent_new(self):
        """Test granting new SMS consent"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock no existing consent
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock user
            mock_user = Mock()
            mock_user.phone_number = None
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                None,  # SMS consent query
                mock_user  # User query
            ]
            
            with patch.object(self.service, '_validate_phone_number', return_value=True):
                result = self.service.grant_sms_consent(
                    self.user_id, "+1234567890", "web_form", "192.168.1.1", "test-agent"
                )
                
                # Assertions
                self.assertIsNotNone(result)
                self.assertTrue(result.consent_granted)
                self.assertEqual(result.phone_number, "+1234567890")
                self.assertEqual(result.consent_source, "web_form")
                self.assertEqual(result.ip_address, "192.168.1.1")
                self.assertEqual(result.user_agent, "test-agent")
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
    
    def test_grant_sms_consent_update_existing(self):
        """Test updating existing SMS consent"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing consent
            mock_consent = Mock()
            mock_consent.consent_granted = False
            mock_consent.opted_out = True
            
            # Mock user
            mock_user = Mock()
            mock_user.phone_number = "+1234567890"
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_consent,  # SMS consent query
                mock_user      # User query
            ]
            
            with patch.object(self.service, '_validate_phone_number', return_value=True):
                result = self.service.grant_sms_consent(
                    self.user_id, "+1234567890", "web_form"
                )
                
                # Assertions
                self.assertTrue(mock_consent.consent_granted)
                self.assertFalse(mock_consent.opted_out)
                self.assertIsNotNone(mock_consent.consent_granted_at)
                mock_db.commit.assert_called_once()
    
    def test_grant_sms_consent_invalid_phone(self):
        """Test granting SMS consent with invalid phone number"""
        with patch.object(self.service, '_validate_phone_number', return_value=False):
            with self.assertRaises(ValueError):
                self.service.grant_sms_consent(
                    self.user_id, "invalid", "web_form"
                )
    
    def test_verify_phone_number_success(self):
        """Test successful phone number verification"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock SMS consent with valid code
            mock_consent = Mock()
            mock_consent.verification_code = "123456"
            mock_consent.verification_expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_consent
            
            result = self.service.verify_phone_number(self.user_id, "123456")
            
            self.assertTrue(result)
            self.assertTrue(mock_consent.phone_verified)
            self.assertIsNotNone(mock_consent.verified_at)
            self.assertIsNone(mock_consent.verification_code)
            mock_db.commit.assert_called_once()
    
    def test_verify_phone_number_invalid_code(self):
        """Test phone verification with invalid code"""
        with patch.object(self.service, 'db') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result = self.service.verify_phone_number(self.user_id, "invalid")
            
            self.assertFalse(result)

    # ============================================================================
    # DELIVERY LOGGING TESTS
    # ============================================================================
    
    def test_log_delivery(self):
        """Test logging delivery"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.id = "pref_id"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            result = self.service.log_delivery(
                self.user_id, AlertType.CRITICAL_FINANCIAL, CommunicationChannel.SMS, "msg_123", "delivered"
            )
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result.user_id, self.user_id)
            self.assertEqual(result.alert_type, AlertType.CRITICAL_FINANCIAL)
            self.assertEqual(result.channel, CommunicationChannel.SMS)
            self.assertEqual(result.message_id, "msg_123")
            self.assertEqual(result.status, "delivered")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    # ============================================================================
    # ENGAGEMENT AND COMPLIANCE TESTS
    # ============================================================================
    
    def test_get_user_engagement_summary(self):
        """Test getting user engagement summary"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock engagement metrics
            mock_metrics = Mock()
            mock_metrics.total_messages_sent = 100
            mock_metrics.total_messages_opened = 80
            mock_metrics.total_messages_clicked = 40
            mock_metrics.total_messages_responded = 20
            mock_metrics.sms_engagement_rate = 85
            mock_metrics.email_engagement_rate = 75
            mock_metrics.push_engagement_rate = 60
            mock_metrics.alert_type_engagement = {"critical_financial": 90}
            mock_metrics.optimal_send_times = {"monday": {"9": 85}}
            mock_metrics.current_frequency = "weekly"
            mock_metrics.recommended_frequency = "daily"
            mock_metrics.last_engagement_at = datetime.utcnow()
            mock_metrics.engagement_trend = "increasing"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_metrics
            
            result = self.service.get_user_engagement_summary(self.user_id)
            
            # Assertions
            self.assertEqual(result['total_messages_sent'], 100)
            self.assertEqual(result['total_messages_opened'], 80)
            self.assertEqual(result['sms_engagement_rate'], 85)
            self.assertEqual(result['current_frequency'], "weekly")
            self.assertEqual(result['engagement_trend'], "increasing")
    
    def test_get_compliance_report(self):
        """Test getting compliance report"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock SMS consent
            mock_sms_consent = Mock()
            mock_sms_consent.consent_granted = True
            mock_sms_consent.consent_granted_at = datetime.utcnow()
            mock_sms_consent.phone_verified = True
            mock_sms_consent.opted_out = False
            
            # Mock email consent
            mock_email_consent = Mock()
            mock_email_consent.consent_status = ConsentStatus.GRANTED
            mock_email_consent.granted_at = datetime.utcnow()
            mock_email_consent.revoked_at = None
            
            # Mock opt-outs
            mock_opt_out = Mock()
            mock_opt_out.channel = CommunicationChannel.SMS
            mock_opt_out.alert_type = AlertType.MARKETING_CONTENT
            mock_opt_out.opted_out_at = datetime.utcnow()
            mock_opt_out.reason = "User request"
            
            # Mock delivery logs
            mock_delivery = Mock()
            mock_delivery.alert_type = AlertType.CRITICAL_FINANCIAL
            mock_delivery.channel = CommunicationChannel.SMS
            mock_delivery.status = "delivered"
            mock_delivery.sent_at = datetime.utcnow()
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_sms_consent,  # SMS consent query
                mock_email_consent  # Email consent query
            ]
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                [mock_opt_out],  # Opt-outs query
                [mock_delivery]  # Delivery logs query
            ]
            
            result = self.service.get_compliance_report(self.user_id)
            
            # Assertions
            self.assertTrue(result['sms_consent']['granted'])
            self.assertEqual(result['email_consent']['status'], 'granted')
            self.assertEqual(len(result['opt_outs']), 1)
            self.assertEqual(len(result['recent_deliveries']), 1)

    # ============================================================================
    # HELPER FUNCTION TESTS
    # ============================================================================
    
    def test_validate_phone_number_valid(self):
        """Test phone number validation with valid number"""
        valid_numbers = [
            "+1234567890",
            "1234567890",
            "+1-234-567-8900",
            "+44 20 7946 0958"
        ]
        
        for phone in valid_numbers:
            result = self.service._validate_phone_number(phone)
            self.assertTrue(result, f"Phone number {phone} should be valid")
    
    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid number"""
        invalid_numbers = [
            "123",
            "abc",
            "+123",
            "123-456-789"
        ]
        
        for phone in invalid_numbers:
            result = self.service._validate_phone_number(phone)
            self.assertFalse(result, f"Phone number {phone} should be invalid")
    
    def test_get_smart_defaults_new_user(self):
        """Test smart defaults for new user"""
        defaults = self.service._get_smart_defaults(UserSegment.NEW_USER)
        
        self.assertTrue(defaults['sms_enabled'])
        self.assertTrue(defaults['email_enabled'])
        self.assertEqual(defaults['frequency_preference'], FrequencyType.WEEKLY)
        self.assertFalse(defaults['alert_types_sms']['marketing_content'])
        self.assertFalse(defaults['alert_types_email']['marketing_content'])
    
    def test_get_smart_defaults_premium_subscriber(self):
        """Test smart defaults for premium subscriber"""
        defaults = self.service._get_smart_defaults(UserSegment.PREMIUM_SUBSCRIBER)
        
        self.assertTrue(defaults['sms_enabled'])
        self.assertTrue(defaults['email_enabled'])
        self.assertEqual(defaults['frequency_preference'], FrequencyType.DAILY)
        self.assertTrue(defaults['alert_types_sms']['marketing_content'])
        self.assertTrue(defaults['alert_types_email']['marketing_content'])
    
    def test_get_smart_defaults_at_risk_user(self):
        """Test smart defaults for at-risk user"""
        defaults = self.service._get_smart_defaults(UserSegment.AT_RISK_USER)
        
        self.assertTrue(defaults['sms_enabled'])
        self.assertFalse(defaults['email_enabled'])
        self.assertEqual(defaults['frequency_preference'], FrequencyType.DAILY)
        self.assertFalse(defaults['alert_types_sms']['marketing_content'])
        self.assertFalse(defaults['alert_types_email']['marketing_content'])

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    def test_full_preference_workflow(self):
        """Test complete preference management workflow"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user
            mock_user = Mock()
            mock_user.phone_number = "+1234567890"
            
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.id = "pref_id"
            mock_preferences.sms_enabled = True
            mock_preferences.email_enabled = True
            mock_preferences.alert_types_sms = {"critical_financial": True}
            mock_preferences.alert_types_email = {"critical_financial": True}
            
            # Mock SMS consent
            mock_sms_consent = Mock()
            mock_sms_consent.consent_granted = True
            mock_sms_consent.opted_out = False
            
            # Mock engagement metrics
            mock_metrics = Mock()
            mock_metrics.total_messages_sent = 50
            mock_metrics.sms_engagement_rate = 80
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_user,        # User query
                mock_preferences, # Preferences query
                mock_sms_consent, # SMS consent query
                None,            # Opt-out history query
                mock_metrics     # Engagement metrics query
            ]
            
            # Test workflow
            # 1. Get preferences
            prefs = self.service.get_user_communication_prefs(self.user_id)
            self.assertIsNotNone(prefs)
            
            # 2. Check consent
            can_send, reason = self.service.check_consent_for_message_type(
                self.user_id, "critical_financial", CommunicationChannel.SMS
            )
            self.assertTrue(can_send)
            
            # 3. Log delivery
            delivery = self.service.log_delivery(
                self.user_id, AlertType.CRITICAL_FINANCIAL, CommunicationChannel.SMS, "msg_123"
            )
            self.assertIsNotNone(delivery)
            
            # 4. Get engagement summary
            engagement = self.service.get_user_engagement_summary(self.user_id)
            self.assertEqual(engagement['total_messages_sent'], 50)
    
    def test_consent_workflow_with_opt_out(self):
        """Test consent workflow with opt-out"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.sms_enabled = True
            mock_preferences.alert_types_sms = {"critical_financial": True}
            mock_preferences.updated_at = datetime.utcnow()
            
            # Mock SMS consent
            mock_sms_consent = Mock()
            mock_sms_consent.opted_out = False
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_preferences, # Preferences query
                mock_sms_consent  # SMS consent query
            ]
            
            # Test opt-out
            result = self.service.handle_opt_out_request(
                self.user_id, CommunicationChannel.SMS, "critical_financial", "User request"
            )
            self.assertTrue(result)
            
            # Verify opt-out was processed
            self.assertFalse(mock_preferences.sms_enabled)
            self.assertFalse(mock_preferences.alert_types_sms["critical_financial"])
            self.assertTrue(mock_sms_consent.opted_out)

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_update_preferences_database_error(self):
        """Test updating preferences with database error"""
        with patch.object(self.service, 'db') as mock_db:
            mock_preferences = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            mock_db.commit.side_effect = Exception("Database error")
            
            result = self.service.update_user_preferences(self.user_id, {'sms_enabled': False})
            
            self.assertFalse(result)
            mock_db.rollback.assert_called_once()
    
    def test_grant_sms_consent_database_error(self):
        """Test granting SMS consent with database error"""
        with patch.object(self.service, 'db') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.commit.side_effect = Exception("Database error")
            
            with patch.object(self.service, '_validate_phone_number', return_value=True):
                with self.assertRaises(Exception):
                    self.service.grant_sms_consent(
                        self.user_id, "+1234567890", "web_form"
                    )
                
                mock_db.rollback.assert_called_once()
    
    def test_log_delivery_database_error(self):
        """Test logging delivery with database error"""
        with patch.object(self.service, 'db') as mock_db:
            mock_preferences = Mock()
            mock_preferences.id = "pref_id"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            mock_db.commit.side_effect = Exception("Database error")
            
            with self.assertRaises(Exception):
                self.service.log_delivery(
                    self.user_id, AlertType.CRITICAL_FINANCIAL, CommunicationChannel.SMS
                )
            
            mock_db.rollback.assert_called_once()


if __name__ == '__main__':
    unittest.main() 