"""
Plaid Security Testing Suite

This module provides comprehensive testing for Plaid security features including
encryption, authentication, webhook validation, and data protection.
"""

import pytest
import unittest
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import cryptography.fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.security.plaid_security_service import PlaidSecurityService
from backend.security.access_control_service import AccessControlService
from backend.security.audit_logging import AuditLoggingService


class TestPlaidSecurityEncryption(unittest.TestCase):
    """Test Plaid security encryption features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_access_token_encryption(self):
        """Test access token encryption and decryption"""
        # Test data
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Encrypt access token
        encrypted_token = self.plaid_security.encrypt_access_token(original_token)
        
        # Verify encryption
        self.assertNotEqual(encrypted_token, original_token)
        self.assertIsInstance(encrypted_token, str)
        self.assertGreater(len(encrypted_token), len(original_token))
        
        # Decrypt access token
        decrypted_token = self.plaid_security.decrypt_access_token(encrypted_token)
        
        # Verify decryption
        self.assertEqual(decrypted_token, original_token)
    
    def test_sensitive_data_encryption(self):
        """Test sensitive data encryption and decryption"""
        # Test sensitive data
        sensitive_data = {
            'account_number': '1234567890',
            'routing_number': '987654321',
            'card_number': '4111111111111111',
            'cvv': '123'
        }
        
        # Encrypt sensitive data
        encrypted_data = self.plaid_security.encrypt_sensitive_data(sensitive_data)
        
        # Verify encryption
        for key, value in sensitive_data.items():
            self.assertNotEqual(encrypted_data[key], value)
            self.assertIsInstance(encrypted_data[key], str)
        
        # Decrypt sensitive data
        decrypted_data = self.plaid_security.decrypt_sensitive_data(encrypted_data)
        
        # Verify decryption
        for key, value in sensitive_data.items():
            self.assertEqual(decrypted_data[key], value)
    
    def test_encryption_key_rotation(self):
        """Test encryption key rotation"""
        # Test data
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Encrypt with current key
        encrypted_token_1 = self.plaid_security.encrypt_access_token(original_token)
        
        # Rotate encryption key
        self.plaid_security.rotate_encryption_key()
        
        # Encrypt with new key
        encrypted_token_2 = self.plaid_security.encrypt_access_token(original_token)
        
        # Verify different encryption results
        self.assertNotEqual(encrypted_token_1, encrypted_token_2)
        
        # Verify both can be decrypted
        decrypted_1 = self.plaid_security.decrypt_access_token(encrypted_token_1)
        decrypted_2 = self.plaid_security.decrypt_access_token(encrypted_token_2)
        
        self.assertEqual(decrypted_1, original_token)
        self.assertEqual(decrypted_2, original_token)
    
    def test_encryption_performance(self):
        """Test encryption performance"""
        import time
        
        # Test data
        test_data = "access-sandbox-" + "x" * 1000  # Large token
        
        # Measure encryption time
        start_time = time.time()
        encrypted_data = self.plaid_security.encrypt_access_token(test_data)
        encryption_time = time.time() - start_time
        
        # Measure decryption time
        start_time = time.time()
        decrypted_data = self.plaid_security.decrypt_access_token(encrypted_data)
        decryption_time = time.time() - start_time
        
        # Verify performance is acceptable
        self.assertLess(encryption_time, 1.0)  # Less than 1 second
        self.assertLess(decryption_time, 1.0)  # Less than 1 second
        self.assertEqual(decrypted_data, test_data)


class TestPlaidSecurityAuthentication(unittest.TestCase):
    """Test Plaid security authentication features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_api_authentication_headers(self):
        """Test API authentication headers"""
        # Test authentication headers
        headers = self.plaid_security.get_authentication_headers()
        
        # Verify required headers
        self.assertIn('PLAID-CLIENT-ID', headers)
        self.assertIn('PLAID-SECRET', headers)
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
        
        # Verify header values are not empty
        self.assertIsNotNone(headers['PLAID-CLIENT-ID'])
        self.assertIsNotNone(headers['PLAID-SECRET'])
        self.assertGreater(len(headers['PLAID-CLIENT-ID']), 0)
        self.assertGreater(len(headers['PLAID-SECRET']), 0)
    
    def test_token_validation(self):
        """Test token validation"""
        # Test valid token
        valid_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        validation_result = self.plaid_security.validate_access_token(valid_token)
        
        self.assertTrue(validation_result['is_valid'])
        self.assertIsNone(validation_result['error'])
        
        # Test invalid token
        invalid_tokens = [
            "",  # Empty token
            "invalid-token",  # Invalid format
            "access-sandbox-",  # Incomplete token
            "access-sandbox-12345678-1234-1234-1234-123456789012" * 10  # Too long
        ]
        
        for invalid_token in invalid_tokens:
            validation_result = self.plaid_security.validate_access_token(invalid_token)
            self.assertFalse(validation_result['is_valid'])
            self.assertIsNotNone(validation_result['error'])
    
    def test_user_authentication(self):
        """Test user authentication for Plaid operations"""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_user.subscription_tier = "premium"
        
        # Test user authentication
        auth_result = self.plaid_security.authenticate_user_for_plaid_operation(
            mock_user.id,
            "get_accounts"
        )
        
        self.assertTrue(auth_result['is_authenticated'])
        self.assertIsNone(auth_result['error'])
        
        # Test unauthorized operation
        auth_result = self.plaid_security.authenticate_user_for_plaid_operation(
            "invalid_user_id",
            "get_accounts"
        )
        
        self.assertFalse(auth_result['is_authenticated'])
        self.assertIsNotNone(auth_result['error'])
    
    def test_rate_limiting(self):
        """Test rate limiting for API calls"""
        user_id = "test_user_id"
        
        # Test rate limiting
        for i in range(10):
            rate_limit_result = self.plaid_security.check_rate_limit(user_id)
            
            if i < 5:  # First 5 calls should succeed
                self.assertTrue(rate_limit_result['allowed'])
            else:  # Subsequent calls should be rate limited
                self.assertFalse(rate_limit_result['allowed'])
                self.assertIn('rate_limit', rate_limit_result['error'])
        
        # Test rate limit reset
        self.plaid_security.reset_rate_limit(user_id)
        rate_limit_result = self.plaid_security.check_rate_limit(user_id)
        self.assertTrue(rate_limit_result['allowed'])


class TestPlaidSecurityWebhookValidation(unittest.TestCase):
    """Test Plaid security webhook validation features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        # Test payload and signature
        payload = json.dumps({
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "INITIAL_UPDATE",
            "item_id": "test_item_id",
            "new_transactions": 1
        })
        
        # Generate valid signature
        valid_signature = self.plaid_security._generate_webhook_signature(payload)
        
        # Test valid signature
        validation_result = self.plaid_security.verify_webhook_signature(
            payload,
            valid_signature
        )
        
        self.assertTrue(validation_result)
        
        # Test invalid signature
        invalid_signature = "invalid_signature"
        validation_result = self.plaid_security.verify_webhook_signature(
            payload,
            invalid_signature
        )
        
        self.assertFalse(validation_result)
    
    def test_webhook_payload_validation(self):
        """Test webhook payload validation"""
        # Test valid webhook payload
        valid_payload = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "INITIAL_UPDATE",
            "item_id": "test_item_id",
            "new_transactions": 1
        }
        
        validation_result = self.plaid_security.validate_webhook_payload(valid_payload)
        
        self.assertTrue(validation_result['is_valid'])
        self.assertIsNone(validation_result['error'])
        
        # Test invalid webhook payload
        invalid_payloads = [
            {},  # Empty payload
            {"webhook_type": "INVALID_TYPE"},  # Invalid webhook type
            {"webhook_code": "INVALID_CODE"},  # Invalid webhook code
            {"item_id": ""},  # Empty item ID
        ]
        
        for invalid_payload in invalid_payloads:
            validation_result = self.plaid_security.validate_webhook_payload(invalid_payload)
            self.assertFalse(validation_result['is_valid'])
            self.assertIsNotNone(validation_result['error'])
    
    def test_webhook_replay_attack_prevention(self):
        """Test webhook replay attack prevention"""
        # Test webhook replay prevention
        webhook_id = "test_webhook_id"
        
        # First webhook should be processed
        replay_result = self.plaid_security.check_webhook_replay(webhook_id)
        self.assertFalse(replay_result['is_replay'])
        
        # Second webhook with same ID should be rejected
        replay_result = self.plaid_security.check_webhook_replay(webhook_id)
        self.assertTrue(replay_result['is_replay'])
        
        # Test webhook ID cleanup
        self.plaid_security.cleanup_old_webhook_ids()
        
        # After cleanup, webhook should be allowed again
        replay_result = self.plaid_security.check_webhook_replay(webhook_id)
        self.assertFalse(replay_result['is_replay'])


class TestPlaidSecurityDataProtection(unittest.TestCase):
    """Test Plaid security data protection features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_data_masking(self):
        """Test data masking for sensitive information"""
        # Test account number masking
        account_number = "1234567890"
        masked_account = self.plaid_security.mask_account_number(account_number)
        
        self.assertNotEqual(masked_account, account_number)
        self.assertEqual(masked_account, "****7890")
        
        # Test routing number masking
        routing_number = "987654321"
        masked_routing = self.plaid_security.mask_routing_number(routing_number)
        
        self.assertNotEqual(masked_routing, routing_number)
        self.assertEqual(masked_routing, "****4321")
        
        # Test card number masking
        card_number = "4111111111111111"
        masked_card = self.plaid_security.mask_card_number(card_number)
        
        self.assertNotEqual(masked_card, card_number)
        self.assertEqual(masked_card, "****1111")
    
    def test_data_anonymization(self):
        """Test data anonymization"""
        # Test user data anonymization
        user_data = {
            "user_id": "test_user_id",
            "email": "test@example.com",
            "name": "John Doe",
            "phone": "123-456-7890"
        }
        
        anonymized_data = self.plaid_security.anonymize_user_data(user_data)
        
        # Verify sensitive fields are anonymized
        self.assertNotEqual(anonymized_data["email"], user_data["email"])
        self.assertNotEqual(anonymized_data["name"], user_data["name"])
        self.assertNotEqual(anonymized_data["phone"], user_data["phone"])
        
        # Verify non-sensitive fields remain unchanged
        self.assertEqual(anonymized_data["user_id"], user_data["user_id"])
    
    def test_data_retention_policy(self):
        """Test data retention policy enforcement"""
        # Test data retention policy
        retention_result = self.plaid_security.check_data_retention_policy("test_user_id")
        
        self.assertIn('retention_policy', retention_result)
        self.assertIn('data_types', retention_result['retention_policy'])
        self.assertIn('retention_periods', retention_result['retention_policy'])
        
        # Test data cleanup
        cleanup_result = self.plaid_security.cleanup_expired_data()
        
        self.assertTrue(cleanup_result['success'])
        self.assertIn('cleaned_records', cleanup_result)
    
    def test_data_access_logging(self):
        """Test data access logging"""
        # Test data access logging
        access_result = self.plaid_security.log_data_access(
            "test_user_id",
            "get_accounts",
            "test_account_id"
        )
        
        self.assertTrue(access_result['success'])
        
        # Verify audit logging was called
        self.mock_audit_service.log_event.assert_called()
        
        # Test access pattern analysis
        pattern_result = self.plaid_security.analyze_access_patterns("test_user_id")
        
        self.assertIn('access_patterns', pattern_result)
        self.assertIn('suspicious_activity', pattern_result)


class TestPlaidSecurityCompliance(unittest.TestCase):
    """Test Plaid security compliance features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_gdpr_compliance(self):
        """Test GDPR compliance features"""
        # Test data portability
        portability_result = self.plaid_security.export_user_data_gdpr("test_user_id")
        
        self.assertTrue(portability_result['success'])
        self.assertIn('data_export', portability_result)
        self.assertIn('format', portability_result['data_export'])
        
        # Test data deletion
        deletion_result = self.plaid_security.delete_user_data_gdpr("test_user_id")
        
        self.assertTrue(deletion_result['success'])
        self.assertEqual(deletion_result['status'], 'deleted')
        
        # Test consent management
        consent_result = self.plaid_security.manage_user_consent("test_user_id", "plaid_data_sharing", True)
        
        self.assertTrue(consent_result['success'])
        self.assertEqual(consent_result['consent_status'], 'granted')
    
    def test_pci_compliance(self):
        """Test PCI compliance features"""
        # Test PCI data handling
        pci_data = {
            "card_number": "4111111111111111",
            "expiry_date": "12/25",
            "cvv": "123"
        }
        
        pci_result = self.plaid_security.handle_pci_data(pci_data)
        
        self.assertTrue(pci_result['success'])
        self.assertIn('encrypted_data', pci_result)
        self.assertIn('token', pci_result)
        
        # Test PCI compliance validation
        compliance_result = self.plaid_security.validate_pci_compliance()
        
        self.assertTrue(compliance_result['is_compliant'])
        self.assertIn('compliance_checks', compliance_result)
    
    def test_sox_compliance(self):
        """Test SOX compliance features"""
        # Test financial data integrity
        financial_data = {
            "account_id": "test_account_1",
            "balance": 1000.00,
            "transactions": [
                {"amount": 100.00, "date": "2024-01-01"},
                {"amount": -50.00, "date": "2024-01-02"}
            ]
        }
        
        sox_result = self.plaid_security.validate_sox_compliance(financial_data)
        
        self.assertTrue(sox_result['is_compliant'])
        self.assertIn('integrity_checks', sox_result)
        self.assertIn('audit_trail', sox_result)
    
    def test_audit_trail_compliance(self):
        """Test audit trail compliance"""
        # Test audit trail generation
        audit_result = self.plaid_security.generate_audit_trail("test_user_id")
        
        self.assertTrue(audit_result['success'])
        self.assertIn('audit_events', audit_result)
        self.assertIn('compliance_report', audit_result)
        
        # Test audit trail validation
        validation_result = self.plaid_security.validate_audit_trail("test_user_id")
        
        self.assertTrue(validation_result['is_valid'])
        self.assertIn('validation_checks', validation_result)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 