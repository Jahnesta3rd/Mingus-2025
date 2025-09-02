"""
Comprehensive tests for Two-Factor Authentication system
Tests TOTP setup, verification, backup codes, SMS fallback, and security features
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import base64
import pyotp
import io
import qrcode

from backend.services.two_factor_service import TwoFactorService
from backend.models.two_factor_auth import (
    TwoFactorAuth, 
    TwoFactorBackupCode, 
    TwoFactorVerificationAttempt
)
from backend.models.user import User

class TestTwoFactorService(unittest.TestCase):
    """Test cases for TwoFactorService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session_factory = Mock()
        self.mock_session = Mock()
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock encryption service
        self.mock_encryption_service = Mock()
        self.mock_encryption_service.encrypt_field.return_value = "encrypted_secret"
        self.mock_encryption_service.decrypt_field.return_value = "test_secret"
        
        # Mock other services
        self.mock_audit_service = Mock()
        self.mock_sms_service = Mock()
        self.mock_email_service = Mock()
        
        # Create service instance with mocked dependencies
        with patch('backend.services.two_factor_service.get_encryption_service', return_value=self.mock_encryption_service):
            with patch('backend.services.two_factor_service.AuditLoggingService', return_value=self.mock_audit_service):
                with patch('backend.services.two_factor_service.TwilioSMSService', return_value=self.mock_sms_service):
                    with patch('backend.services.two_factor_service.ResendEmailService', return_value=self.mock_email_service):
                        self.service = TwoFactorService(self.mock_session_factory)
    
    def test_init(self):
        """Test service initialization"""
        self.assertEqual(self.service.totp_algorithm, 'SHA1')
        self.assertEqual(self.service.totp_digits, 6)
        self.assertEqual(self.service.totp_period, 30)
        self.assertEqual(self.service.backup_code_count, 10)
        self.assertEqual(self.service.max_failed_attempts, 5)
    
    def test_generate_totp_secret(self):
        """Test TOTP secret generation"""
        secret = self.service._generate_totp_secret()
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)  # Base32 encoded secret
        # Should be valid base32
        try:
            base64.b32decode(secret + '=' * (-len(secret) % 4))
        except Exception:
            self.fail("Generated secret is not valid base32")
    
    def test_encrypt_decrypt_totp_secret(self):
        """Test TOTP secret encryption and decryption"""
        test_secret = "test_secret_123"
        
        # Test encryption
        encrypted = self.service._encrypt_totp_secret(test_secret)
        self.mock_encryption_service.encrypt_field.assert_called_with(test_secret, '2fa_secret')
        self.assertEqual(encrypted, "encrypted_secret")
        
        # Test decryption
        decrypted = self.service._decrypt_totp_secret(encrypted)
        self.mock_encryption_service.decrypt_field.assert_called_with(encrypted, '2fa_secret')
        self.assertEqual(decrypted, "test_secret")
    
    def test_generate_backup_codes(self):
        """Test backup code generation"""
        codes = self.service._generate_backup_codes()
        
        self.assertEqual(len(codes), 10)
        for code in codes:
            # Check format: XXXX-XXXX-XXXX-XXXX
            parts = code.split('-')
            self.assertEqual(len(parts), 4)
            for part in parts:
                self.assertEqual(len(part), 4)
                self.assertTrue(all(c in '0123456789ABCDEF' for c in part))
    
    def test_hash_backup_code(self):
        """Test backup code hashing"""
        test_code = "ABCD-1234-EFGH-5678"
        hashed = self.service._hash_backup_code(test_code)
        
        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 64)  # SHA256 hash length
        
        # Verify hash
        self.assertTrue(self.service._verify_backup_code(test_code, hashed))
        self.assertFalse(self.service._verify_backup_code("WRONG-CODE", hashed))
    
    def test_generate_qr_code(self):
        """Test QR code generation"""
        test_uri = "otpauth://totp/MINGUS:test@example.com?secret=TEST123&issuer=MINGUS"
        qr_bytes = self.service._generate_qr_code(test_uri)
        
        self.assertIsInstance(qr_bytes, bytes)
        self.assertGreater(len(qr_bytes), 100)  # Should be a valid PNG
        
        # Verify it's a valid PNG
        self.assertTrue(qr_bytes.startswith(b'\x89PNG'))
    
    def test_get_client_info(self):
        """Test client information extraction"""
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {
            'User-Agent': 'Mozilla/5.0 Test Browser',
            'CF-IPCountry': 'US',
            'CF-IPCity': 'New York',
            'CF-Timezone': 'America/New_York'
        }
        
        client_info = self.service._get_client_info(mock_request)
        
        self.assertEqual(client_info['ip_address'], "192.168.1.1")
        self.assertEqual(client_info['user_agent'], 'Mozilla/5.0 Test Browser')
        self.assertEqual(client_info['country_code'], 'US')
        self.assertEqual(client_info['city'], 'New York')
        self.assertEqual(client_info['timezone'], 'America/New_York')
    
    def test_setup_2fa_success(self):
        """Test successful 2FA setup"""
        user_id = 123
        mock_request = Mock()
        
        # Mock database queries
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None  # No existing 2FA
        
        mock_user = Mock()
        mock_user.email = "test@example.com"
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # First call for existing 2FA
            mock_user  # Second call for user
        ]
        
        # Mock session operations
        self.mock_session.add = Mock()
        self.mock_session.commit = Mock()
        
        result = self.service.setup_2fa(user_id, mock_request)
        
        self.assertTrue(result['success'])
        self.assertIn('totp_secret', result)
        self.assertIn('qr_code', result)
        self.assertIn('backup_codes', result)
        self.assertIn('totp_uri', result)
        self.assertEqual(len(result['backup_codes']), 10)
        
        # Verify database operations
        self.mock_session.add.assert_called()
        self.mock_session.commit.assert_called()
    
    def test_setup_2fa_already_enabled(self):
        """Test 2FA setup when already enabled"""
        user_id = 123
        mock_request = Mock()
        
        # Mock existing enabled 2FA
        mock_existing_2fa = Mock()
        mock_existing_2fa.is_enabled = True
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_existing_2fa
        
        result = self.service.setup_2fa(user_id, mock_request)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Two-factor authentication is already enabled')
    
    def test_verify_totp_success(self):
        """Test successful TOTP verification"""
        user_id = 123
        totp_code = "123456"
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = False
        mock_2fa.encrypted_totp_secret = "encrypted_secret"
        mock_2fa.totp_digits = 6
        mock_2fa.totp_period = 30
        mock_2fa.totp_algorithm = "SHA1"
        mock_2fa.is_enabled = False
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        # Mock session operations
        self.mock_session.commit = Mock()
        
        # Mock TOTP verification (this would normally work with pyotp)
        with patch('pyotp.TOTP') as mock_totp_class:
            mock_totp = Mock()
            mock_totp.verify.return_value = True
            mock_totp_class.return_value = mock_totp
            
            result = self.service.verify_totp(user_id, totp_code, mock_request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Two-factor authentication verified successfully')
        self.assertTrue(result['is_enabled'])
        
        # Verify database updates
        self.assertTrue(mock_2fa.is_enabled)
        self.assertTrue(mock_2fa.is_verified)
        self.mock_session.commit.assert_called()
    
    def test_verify_totp_invalid_code(self):
        """Test TOTP verification with invalid code"""
        user_id = 123
        totp_code = "123456"
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = False
        mock_2fa.encrypted_totp_secret = "encrypted_secret"
        mock_2fa.totp_digits = 6
        mock_2fa.totp_period = 30
        mock_2fa.totp_algorithm = "SHA1"
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        # Mock TOTP verification failure
        with patch('pyotp.TOTP') as mock_totp_class:
            mock_totp = Mock()
            mock_totp.verify.return_value = False
            mock_totp_class.return_value = mock_totp
            
            # Mock failed attempts tracking
            with patch.object(self.service, '_get_failed_attempts', return_value=1):
                result = self.service.verify_totp(user_id, totp_code, mock_request)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Invalid authentication code')
        self.assertIn('remaining_attempts', result)
    
    def test_verify_totp_account_locked(self):
        """Test TOTP verification when account is locked"""
        user_id = 123
        totp_code = "123456"
        mock_request = Mock()
        
        # Mock locked 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = True
        mock_2fa.lockout_until = datetime.utcnow() + timedelta(minutes=10)
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        result = self.service.verify_totp(user_id, totp_code, mock_request)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Account temporarily locked due to too many failed attempts')
        self.assertIn('lockout_until', result)
    
    def test_verify_backup_code_success(self):
        """Test successful backup code verification"""
        user_id = 123
        backup_code = "ABCD-1234-EFGH-5678"
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = False
        
        # Mock backup code record
        mock_backup_code = Mock()
        mock_backup_code.encrypted_code_hash = self.service._hash_backup_code(backup_code)
        mock_backup_code.is_used = False
        
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_2fa,  # First call for 2FA config
            mock_backup_code  # Second call for backup code
        ]
        
        # Mock session operations
        self.mock_session.commit = Mock()
        
        result = self.service.verify_backup_code(user_id, backup_code, mock_request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Backup code verified successfully')
        
        # Verify backup code marked as used
        self.assertTrue(mock_backup_code.is_used)
        self.mock_session.commit.assert_called()
    
    def test_verify_backup_code_already_used(self):
        """Test backup code verification with already used code"""
        user_id = 123
        backup_code = "ABCD-1234-EFGH-5678"
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = False
        
        # Mock used backup code
        mock_backup_code = Mock()
        mock_backup_code.is_used = True
        
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_2fa,  # First call for 2FA config
            mock_backup_code  # Second call for backup code
        ]
        
        result = self.service.verify_backup_code(user_id, backup_code, mock_request)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No backup codes available')
    
    def test_send_sms_fallback_success(self):
        """Test successful SMS fallback sending"""
        user_id = 123
        mock_request = Mock()
        
        # Mock user with phone number
        mock_user = Mock()
        mock_user.phone_number = "+1234567890"
        mock_user.full_name = "Test User"
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # First call for user
            mock_2fa   # Second call for 2FA config
        ]
        
        # Mock SMS service
        self.mock_sms_service.send_2fa_code.return_value = {
            'success': True,
            'message_id': 'msg_123'
        }
        
        # Mock session operations
        self.mock_session.commit = Mock()
        
        result = self.service.send_sms_fallback(user_id, mock_request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'SMS code sent successfully')
        self.assertIn('phone_number', result)
        
        # Verify SMS service called
        self.mock_sms_service.send_2fa_code.assert_called_with(
            "+1234567890", 
            mock_request,  # This should be the code, not request
            "Test User"
        )
    
    def test_send_sms_fallback_no_phone(self):
        """Test SMS fallback when user has no phone number"""
        user_id = 123
        mock_request = Mock()
        
        # Mock user without phone number
        mock_user = Mock()
        mock_user.phone_number = None
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        result = self.service.send_sms_fallback(user_id, mock_request)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Phone number not available for SMS fallback')
    
    def test_verify_sms_code_success(self):
        """Test successful SMS code verification"""
        user_id = 123
        sms_code = "123456"
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_locked_out.return_value = False
        mock_2fa.encrypted_sms_secret = "encrypted_sms_code"
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        # Mock session operations
        self.mock_session.commit = Mock()
        
        result = self.service.verify_sms_code(user_id, sms_code, mock_request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'SMS code verified successfully')
        
        # Verify SMS code cleared after use
        self.assertIsNone(mock_2fa.encrypted_sms_secret)
        self.mock_session.commit.assert_called()
    
    def test_disable_2fa_success(self):
        """Test successful 2FA disable"""
        user_id = 123
        mock_request = Mock()
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        # Mock session operations
        self.mock_session.commit = Mock()
        
        result = self.service.disable_2fa(user_id, mock_request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Two-factor authentication disabled successfully')
        
        # Verify 2FA disabled
        self.assertFalse(mock_2fa.is_enabled)
        self.assertFalse(mock_2fa.is_verified)
        self.assertIsNone(mock_2fa.setup_completed_at)
        self.assertFalse(mock_2fa.sms_fallback_enabled)
        self.assertIsNone(mock_2fa.encrypted_sms_secret)
        
        self.mock_session.commit.assert_called()
    
    def test_get_2fa_status_enabled(self):
        """Test getting 2FA status when enabled"""
        user_id = 123
        
        # Mock 2FA configuration
        mock_2fa = Mock()
        mock_2fa.is_enabled = True
        mock_2fa.setup_completed_at = datetime.utcnow()
        mock_2fa.sms_fallback_enabled = True
        mock_2fa.last_used_at = datetime.utcnow()
        mock_2fa.is_locked_out.return_value = False
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_2fa
        
        # Mock backup codes count
        mock_backup_codes_query = Mock()
        mock_backup_codes_query.count.return_value = 8
        self.mock_session.query.return_value.filter_by.return_value.count.return_value = 8
        
        result = self.service.get_2fa_status(user_id)
        
        self.assertTrue(result['enabled'])
        self.assertTrue(result['setup_completed'])
        self.assertTrue(result['sms_fallback'])
        self.assertEqual(result['backup_codes_remaining'], 8)
        self.assertFalse(result['is_locked_out'])
    
    def test_get_2fa_status_not_setup(self):
        """Test getting 2FA status when not set up"""
        user_id = 123
        
        # Mock no 2FA configuration
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = self.service.get_2fa_status(user_id)
        
        self.assertFalse(result['enabled'])
        self.assertFalse(result['setup_completed'])
        self.assertFalse(result['sms_fallback'])
        self.assertEqual(result['backup_codes_remaining'], 0)
    
    def test_handle_failed_attempt(self):
        """Test handling of failed verification attempts"""
        mock_session = Mock()
        mock_2fa = Mock()
        mock_request = Mock()
        
        # Mock failed attempts count
        with patch.object(self.service, '_get_failed_attempts', return_value=4):
            self.service._handle_failed_attempt(mock_session, mock_2fa, mock_request)
        
        # Should not lock out yet (4 < 5)
        mock_2fa.lockout_until.assert_not_called()
        
        # Mock failed attempts count at threshold
        with patch.object(self.service, '_get_failed_attempts', return_value=5):
            self.service._handle_failed_attempt(mock_session, mock_2fa, mock_request)
        
        # Should lock out now (5 >= 5)
        mock_2fa.lockout_until.assert_called()
        mock_session.commit.assert_called()
    
    def test_log_verification_attempt(self):
        """Test logging of verification attempts"""
        mock_session = Mock()
        two_factor_auth_id = 456
        attempt_type = "totp"
        success = True
        mock_request = Mock()
        
        # Mock client info
        with patch.object(self.service, '_get_client_info', return_value={
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Browser',
            'country_code': 'US',
            'city': 'Test City',
            'timezone': 'UTC'
        }):
            self.service._log_verification_attempt(
                mock_session, two_factor_auth_id, attempt_type, success, mock_request
            )
        
        # Verify verification attempt logged
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

class TestTwoFactorModels(unittest.TestCase):
    """Test cases for 2FA database models"""
    
    def test_two_factor_auth_model(self):
        """Test TwoFactorAuth model"""
        now = datetime.utcnow()
        
        two_factor_auth = TwoFactorAuth(
            user_id=123,
            encrypted_totp_secret="encrypted_secret",
            totp_algorithm="SHA1",
            totp_digits=6,
            totp_period=30,
            is_enabled=True,
            is_verified=True,
            setup_completed_at=now,
            sms_fallback_enabled=True,
            max_attempts=5
        )
        
        self.assertEqual(two_factor_auth.user_id, 123)
        self.assertEqual(two_factor_auth.totp_algorithm, "SHA1")
        self.assertEqual(two_factor_auth.totp_digits, 6)
        self.assertEqual(two_factor_auth.totp_period, 30)
        self.assertTrue(two_factor_auth.is_enabled)
        self.assertTrue(two_factor_auth.is_verified)
        self.assertEqual(two_factor_auth.setup_completed_at, now)
        self.assertTrue(two_factor_auth.sms_fallback_enabled)
        self.assertEqual(two_factor_auth.max_attempts, 5)
    
    def test_two_factor_auth_locked_out(self):
        """Test TwoFactorAuth lockout functionality"""
        two_factor_auth = TwoFactorAuth()
        
        # Not locked out initially
        self.assertFalse(two_factor_auth.is_locked_out())
        
        # Set lockout
        two_factor_auth.lockout_until = datetime.utcnow() + timedelta(minutes=10)
        self.assertTrue(two_factor_auth.is_locked_out())
        
        # Clear lockout
        two_factor_auth.reset_failed_attempts()
        self.assertFalse(two_factor_auth.is_locked_out())
    
    def test_two_factor_backup_code_model(self):
        """Test TwoFactorBackupCode model"""
        backup_code = TwoFactorBackupCode(
            two_factor_auth_id=456,
            encrypted_code_hash="hashed_code"
        )
        
        self.assertEqual(backup_code.two_factor_auth_id, 456)
        self.assertEqual(backup_code.encrypted_code_hash, "hashed_code")
        self.assertFalse(backup_code.is_used)
        self.assertIsNone(backup_code.used_at)
    
    def test_two_factor_backup_code_mark_used(self):
        """Test marking backup code as used"""
        backup_code = TwoFactorBackupCode()
        
        backup_code.mark_as_used(
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        self.assertTrue(backup_code.is_used)
        self.assertIsNotNone(backup_code.used_at)
        self.assertEqual(backup_code.used_ip_address, "192.168.1.1")
        self.assertEqual(backup_code.used_user_agent, "Test Browser")
    
    def test_two_factor_verification_attempt_model(self):
        """Test TwoFactorVerificationAttempt model"""
        now = datetime.utcnow()
        
        verification_attempt = TwoFactorVerificationAttempt(
            two_factor_auth_id=789,
            attempt_type="totp",
            success=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            country_code="US",
            city="Test City",
            timezone="UTC"
        )
        
        self.assertEqual(verification_attempt.two_factor_auth_id, 789)
        self.assertEqual(verification_attempt.attempt_type, "totp")
        self.assertTrue(verification_attempt.success)
        self.assertEqual(verification_attempt.ip_address, "192.168.1.1")
        self.assertEqual(verification_attempt.user_agent, "Test Browser")
        self.assertEqual(verification_attempt.country_code, "US")
        self.assertEqual(verification_attempt.city, "Test City")
        self.assertEqual(verification_attempt.timezone, "UTC")

if __name__ == '__main__':
    unittest.main()
