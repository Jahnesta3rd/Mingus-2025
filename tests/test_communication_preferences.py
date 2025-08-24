"""
Test Communication Preferences System
Demonstrates and validates the communication preferences and consent management system
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import uuid

from backend.services.communication_preference_service import CommunicationPreferenceService
from backend.models.communication_preferences import (
    CommunicationPreferences, ConsentRecord, AlertTypePreference,
    CommunicationDeliveryLog, OptOutRecord, UserEngagementMetrics, CommunicationPolicy,
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus
)
from backend.models.user import User


class TestCommunicationPreferences(unittest.TestCase):
    """Test cases for communication preferences system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = CommunicationPreferenceService()
        self.user_id = "test_user_123"
        self.test_user = User(
            id=self.user_id,
            email="test@example.com",
            full_name="Test User",
            phone_number="+1234567890"
        )
    
    def test_create_user_preferences(self):
        """Test creating default user preferences"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                self.test_user,  # User query
                None,  # Preferences query
                None   # Engagement metrics query
            ]
            
            # Test creating preferences
            preferences = self.service.create_user_preferences(self.user_id)
            
            # Verify preferences were created with defaults
            self.assertIsNotNone(preferences)
            self.assertEqual(preferences.user_id, self.user_id)
            self.assertTrue(preferences.sms_enabled)
            self.assertTrue(preferences.email_enabled)
            self.assertFalse(preferences.push_enabled)
            self.assertTrue(preferences.in_app_enabled)
            self.assertEqual(preferences.critical_frequency, FrequencyType.IMMEDIATE)
            self.assertEqual(preferences.daily_frequency, FrequencyType.DAILY)
            self.assertEqual(preferences.weekly_frequency, FrequencyType.WEEKLY)
            self.assertEqual(preferences.monthly_frequency, FrequencyType.MONTHLY)
            self.assertTrue(preferences.financial_alerts_enabled)
            self.assertTrue(preferences.career_content_enabled)
            self.assertTrue(preferences.wellness_content_enabled)
            self.assertFalse(preferences.marketing_content_enabled)
    
    def test_grant_consent(self):
        """Test granting consent for communication"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing preferences
            mock_preferences = Mock()
            mock_preferences.id = str(uuid.uuid4())
            mock_db.query.return_value.filter.return_value.first.return_value = mock_preferences
            
            # Test granting SMS consent
            consent = self.service.grant_consent(
                self.user_id,
                "sms",
                phone_number="+1234567890",
                consent_source="web_form",
                legal_basis="consent",
                purpose="Financial alerts and notifications"
            )
            
            # Verify consent was granted
            self.assertIsNotNone(consent)
            self.assertEqual(consent.user_id, self.user_id)
            self.assertEqual(consent.consent_type, "sms")
            self.assertEqual(consent.consent_status, ConsentStatus.GRANTED)
            self.assertEqual(consent.phone_number, "+1234567890")
            self.assertEqual(consent.consent_source, "web_form")
            self.assertEqual(consent.legal_basis, "consent")
            self.assertIsNotNone(consent.granted_at)
    
    def test_revoke_consent(self):
        """Test revoking consent for communication"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing consent
            mock_consent = Mock()
            mock_consent.consent_status = ConsentStatus.GRANTED
            mock_db.query.return_value.filter.return_value.first.return_value = mock_consent
            
            # Test revoking SMS consent
            success = self.service.revoke_consent(
                self.user_id,
                "sms",
                reason="User requested"
            )
            
            # Verify consent was revoked
            self.assertTrue(success)
            self.assertEqual(mock_consent.consent_status, ConsentStatus.REVOKED)
            self.assertIsNotNone(mock_consent.revoked_at)
    
    def test_check_consent_status(self):
        """Test checking consent status"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing consent
            mock_consent = Mock()
            mock_consent.consent_status = ConsentStatus.GRANTED
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_consent
            
            # Test checking SMS consent status
            status = self.service.check_consent_status(self.user_id, "sms")
            
            # Verify status
            self.assertEqual(status, ConsentStatus.GRANTED)
    
    def test_can_send_message(self):
        """Test checking if message can be sent"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.sms_enabled = True
            mock_preferences.email_enabled = True
            mock_preferences.timezone = "UTC"
            self.service.get_user_preferences = Mock(return_value=mock_preferences)
            
            # Mock consent status
            self.service.check_consent_status = Mock(return_value=ConsentStatus.GRANTED)
            
            # Mock alert type preferences
            mock_alert_pref = Mock()
            mock_alert_pref.sms_enabled = True
            mock_db.query.return_value.filter.return_value.first.return_value = mock_alert_pref
            
            # Mock opt-out check
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Test can send SMS
            can_send, reason = self.service.can_send_message(
                self.user_id,
                AlertType.CRITICAL_FINANCIAL,
                CommunicationChannel.SMS
            )
            
            # Verify result
            self.assertTrue(can_send)
            self.assertEqual(reason, "OK")
    
    def test_process_opt_out(self):
        """Test processing opt-out request"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.sms_enabled = True
            self.service.get_user_preferences = Mock(return_value=mock_preferences)
            
            # Test processing SMS opt-out
            success = self.service.process_opt_out(
                self.user_id,
                CommunicationChannel.SMS,
                AlertType.MARKETING_CONTENT,
                "api"
            )
            
            # Verify opt-out was processed
            self.assertTrue(success)
            self.assertFalse(mock_preferences.sms_enabled)
    
    def test_log_delivery(self):
        """Test logging communication delivery"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.id = str(uuid.uuid4())
            self.service.get_user_preferences = Mock(return_value=mock_preferences)
            
            # Test logging SMS delivery
            delivery_log = self.service.log_delivery(
                self.user_id,
                AlertType.CRITICAL_FINANCIAL,
                CommunicationChannel.SMS,
                message_id="twilio_msg_123",
                subject="Low Balance Alert",
                content_preview="Your account balance is low"
            )
            
            # Verify delivery was logged
            self.assertIsNotNone(delivery_log)
            self.assertEqual(delivery_log.user_id, self.user_id)
            self.assertEqual(delivery_log.alert_type, AlertType.CRITICAL_FINANCIAL)
            self.assertEqual(delivery_log.channel, CommunicationChannel.SMS)
            self.assertEqual(delivery_log.message_id, "twilio_msg_123")
            self.assertEqual(delivery_log.status, "sent")
            self.assertIsNotNone(delivery_log.sent_at)
    
    def test_get_optimal_send_time(self):
        """Test getting optimal send time"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock preferences
            mock_preferences = Mock()
            mock_preferences.preferred_sms_time = "09:00"
            mock_preferences.preferred_email_time = "18:00"
            self.service.get_user_preferences = Mock(return_value=mock_preferences)
            
            # Test SMS optimal time
            sms_time = self.service.get_optimal_send_time(
                self.user_id,
                CommunicationChannel.SMS
            )
            self.assertEqual(sms_time, "09:00")
            
            # Test email optimal time
            email_time = self.service.get_optimal_send_time(
                self.user_id,
                CommunicationChannel.EMAIL
            )
            self.assertEqual(email_time, "18:00")
    
    def test_get_user_engagement_summary(self):
        """Test getting user engagement summary"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock engagement metrics
            mock_metrics = Mock()
            mock_metrics.total_messages_sent = 100
            mock_metrics.total_messages_opened = 75
            mock_metrics.total_messages_clicked = 25
            mock_metrics.total_messages_responded = 10
            mock_metrics.sms_engagement_rate = 80
            mock_metrics.email_engagement_rate = 60
            mock_metrics.last_engagement_at = datetime.utcnow()
            mock_metrics.engagement_trend = "increasing"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_metrics
            
            # Test getting engagement summary
            summary = self.service.get_user_engagement_summary(self.user_id)
            
            # Verify summary
            self.assertEqual(summary['total_messages_sent'], 100)
            self.assertEqual(summary['total_messages_opened'], 75)
            self.assertEqual(summary['total_messages_clicked'], 25)
            self.assertEqual(summary['total_messages_responded'], 10)
            self.assertEqual(summary['engagement_rate'], 110.0)  # (75+25+10)/100 * 100
            self.assertEqual(summary['sms_engagement_rate'], 80)
            self.assertEqual(summary['email_engagement_rate'], 60)
            self.assertEqual(summary['trend'], "increasing")
    
    def test_get_compliance_report(self):
        """Test getting compliance report"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock consent records
            mock_consent = Mock()
            mock_consent.consent_type = "sms"
            mock_consent.consent_status = ConsentStatus.GRANTED
            mock_consent.granted_at = datetime.utcnow()
            mock_consent.verified_at = datetime.utcnow()
            mock_consent.revoked_at = None
            
            # Mock opt-out records
            mock_opt_out = Mock()
            mock_opt_out.channel = CommunicationChannel.EMAIL
            mock_opt_out.alert_type = AlertType.MARKETING_CONTENT
            mock_opt_out.opted_out_at = datetime.utcnow()
            mock_opt_out.method = "email_unsubscribe"
            
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                [mock_consent],  # Consent records
                [mock_opt_out]   # Opt-out records
            ]
            
            # Test getting compliance report
            report = self.service.get_compliance_report(self.user_id)
            
            # Verify report
            self.assertEqual(report['user_id'], self.user_id)
            self.assertEqual(len(report['consents']), 1)
            self.assertEqual(report['consents'][0]['type'], "sms")
            self.assertEqual(report['consents'][0]['status'], "granted")
            self.assertEqual(len(report['opt_outs']), 1)
            self.assertEqual(report['opt_outs'][0]['channel'], "email")
            self.assertEqual(report['opt_outs'][0]['alert_type'], "marketing_content")


class TestCommunicationPreferencesIntegration(unittest.TestCase):
    """Integration tests for communication preferences system"""
    
    def test_full_workflow(self):
        """Test complete user communication preference workflow"""
        service = CommunicationPreferenceService()
        user_id = "integration_test_user"
        
        # Step 1: Create user preferences
        preferences = service.create_user_preferences(user_id)
        self.assertIsNotNone(preferences)
        
        # Step 2: Grant SMS consent
        consent = service.grant_consent(
            user_id,
            "sms",
            phone_number="+1234567890",
            consent_source="web_form"
        )
        self.assertEqual(consent.consent_status, ConsentStatus.GRANTED)
        
        # Step 3: Check if can send SMS
        can_send, reason = service.can_send_message(
            user_id,
            AlertType.CRITICAL_FINANCIAL,
            CommunicationChannel.SMS
        )
        self.assertTrue(can_send)
        
        # Step 4: Log delivery
        delivery_log = service.log_delivery(
            user_id,
            AlertType.CRITICAL_FINANCIAL,
            CommunicationChannel.SMS,
            message_id="test_msg_123"
        )
        self.assertIsNotNone(delivery_log)
        
        # Step 5: Process opt-out
        success = service.process_opt_out(
            user_id,
            CommunicationChannel.SMS,
            method="api"
        )
        self.assertTrue(success)
        
        # Step 6: Check can send after opt-out
        can_send_after, reason_after = service.can_send_message(
            user_id,
            AlertType.CRITICAL_FINANCIAL,
            CommunicationChannel.SMS
        )
        self.assertFalse(can_send_after)


if __name__ == '__main__':
    unittest.main() 