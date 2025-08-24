"""
Unit Tests for Verification Security Module
Tests all security features including rate limiting, CAPTCHA, SIM swap detection, etc.
"""

import pytest
import time
import hashlib
import hmac
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.security.verification_security import (
    VerificationSecurity, SecurityEvent, get_backoff_delay
)

class TestVerificationSecurity:
    """Test suite for VerificationSecurity class"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=Session)
        session.execute.return_value.fetchone.return_value = None
        session.execute.return_value.fetchall.return_value = []
        session.commit.return_value = None
        session.rollback.return_value = None
        return session
    
    @pytest.fixture
    def security_service(self, mock_db_session):
        """Create VerificationSecurity instance with mock session"""
        return VerificationSecurity(mock_db_session)
    
    def test_generate_secure_code(self, security_service):
        """Test secure code generation"""
        # Test default length
        code = security_service.generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()
        
        # Test custom length
        code = security_service.generate_verification_code(8)
        assert len(code) == 8
        assert code.isdigit()
        
        # Test uniqueness (generate multiple codes)
        codes = set()
        for _ in range(100):
            code = security_service.generate_verification_code()
            codes.add(code)
        
        # Should have high uniqueness
        assert len(codes) > 95  # Allow for some collisions
    
    def test_hash_verification_code(self, security_service):
        """Test code hashing with salt"""
        code = "123456"
        
        # Test with generated salt
        hash1, salt1 = security_service.hash_verification_code(code)
        assert len(hash1) == 64  # SHA-256 hex length
        assert len(salt1) == 32  # 16 bytes hex encoded
        
        # Test with provided salt
        salt2 = "test_salt_12345678"
        hash2, salt2_out = security_service.hash_verification_code(code, salt2)
        assert salt2_out == salt2
        
        # Test same code with same salt produces same hash
        hash3, _ = security_service.hash_verification_code(code, salt2)
        assert hash2 == hash3
    
    def test_verify_code_hash(self, security_service):
        """Test code hash verification"""
        code = "123456"
        hash_value, salt = security_service.hash_verification_code(code)
        
        # Test correct code
        assert security_service.verify_code_hash(code, hash_value, salt) is True
        
        # Test incorrect code
        assert security_service.verify_code_hash("654321", hash_value, salt) is False
        
        # Test timing attack resistance
        start_time = time.time()
        security_service.verify_code_hash("654321", hash_value, salt)
        incorrect_time = time.time() - start_time
        
        start_time = time.time()
        security_service.verify_code_hash(code, hash_value, salt)
        correct_time = time.time() - start_time
        
        # Times should be similar (within 10ms)
        assert abs(correct_time - incorrect_time) < 0.01
    
    def test_sanitize_phone_number(self, security_service):
        """Test phone number sanitization"""
        # Test US 10-digit numbers
        assert security_service.sanitize_phone_number("1234567890") == "+11234567890"
        assert security_service.sanitize_phone_number("(123) 456-7890") == "+11234567890"
        assert security_service.sanitize_phone_number("123-456-7890") == "+11234567890"
        
        # Test US 11-digit numbers
        assert security_service.sanitize_phone_number("11234567890") == "+11234567890"
        
        # Test international numbers
        assert security_service.sanitize_phone_number("44123456789") == "+44123456789"
        
        # Test invalid numbers
        with pytest.raises(ValueError):
            security_service.sanitize_phone_number("123")  # Too short
        
        with pytest.raises(ValueError):
            security_service.sanitize_phone_number("1234567890123456")  # Too long
    
    def test_validate_phone_number(self, security_service):
        """Test phone number validation"""
        # Valid numbers
        assert security_service.validate_phone_number("+11234567890") is True
        assert security_service.validate_phone_number("+44123456789") is True
        
        # Invalid numbers
        assert security_service.validate_phone_number("123") is False
        assert security_service.validate_phone_number("+0000000000") is False
        assert security_service.validate_phone_number("+1111111111") is False  # Suspicious pattern
    
    def test_is_suspicious_phone_number(self, security_service):
        """Test suspicious phone number detection"""
        # Test sequential digits
        assert security_service._is_suspicious_phone_number("+1111111111") is True
        assert security_service._is_suspicious_phone_number("+1222222222") is True
        
        # Test palindrome
        assert security_service._is_suspicious_phone_number("+1122332211") is True
        
        # Test normal numbers
        assert security_service._is_suspicious_phone_number("+11234567890") is False
        assert security_service._is_suspicious_phone_number("+44123456789") is False
    
    def test_check_rate_limit(self, security_service):
        """Test rate limiting functionality"""
        user_id = "test_user"
        ip_address = "192.168.1.1"
        action = "send_code"
        
        # Test initial attempt (should be allowed)
        allowed, retry_after = security_service.check_rate_limit(action, user_id, ip_address)
        assert allowed is True
        assert retry_after is None
        
        # Test multiple attempts within limit
        for _ in range(4):  # 4 more attempts (total 5, which is the limit)
            allowed, retry_after = security_service.check_rate_limit(action, user_id, ip_address)
            assert allowed is True
            assert retry_after is None
        
        # Test exceeding limit
        allowed, retry_after = security_service.check_rate_limit(action, user_id, ip_address)
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_get_resend_delay(self, security_service):
        """Test progressive delay calculation"""
        # Test progressive delays
        assert security_service.get_resend_delay(0) == 60   # 1st resend
        assert security_service.get_resend_delay(1) == 120  # 2nd resend
        assert security_service.get_resend_delay(2) == 300  # 3rd resend
        assert security_service.get_resend_delay(3) == 300  # Subsequent resends
        assert security_service.get_resend_delay(10) == 300 # Max delay
    
    def test_get_resend_message(self, security_service):
        """Test progressive messaging"""
        assert "new verification code" in security_service.get_resend_message(0)
        assert "Another verification code" in security_service.get_resend_message(1)
        assert "Final verification code" in security_service.get_resend_message(2)
        assert "Final verification code" in security_service.get_resend_message(5)  # Max message
    
    def test_calculate_risk_score(self, security_service):
        """Test risk score calculation"""
        # Test base risk scores
        risk = security_service.calculate_risk_score("send_code", "user1", "192.168.1.1", "+11234567890", {})
        assert 0.0 <= risk <= 1.0
        
        # Test high-risk events
        risk = security_service.calculate_risk_score("sim_swap_detected", "user1", "192.168.1.1", "+11234567890", {})
        assert risk > 0.9
        
        # Test with suspicious IP
        risk = security_service.calculate_risk_score("send_code", "user1", "0.0.0.0", "+11234567890", {})
        assert risk > 0.3
        
        # Test with multiple failures
        details = {"failure_count": 5, "time_since_last": 1}
        risk = security_service.calculate_risk_score("verify_failed", "user1", "192.168.1.1", "+11234567890", details)
        assert risk > 0.5
    
    def test_is_suspicious_ip(self, security_service):
        """Test suspicious IP detection"""
        # Test private IPs
        assert security_service._is_suspicious_ip("192.168.1.1") is True
        assert security_service._is_suspicious_ip("10.0.0.1") is True
        assert security_service._is_suspicious_ip("127.0.0.1") is True
        
        # Test invalid IPs
        assert security_service._is_suspicious_ip("0.0.0.0") is True
        assert security_service._is_suspicious_ip("255.255.255.255") is True
        
        # Test valid public IPs
        assert security_service._is_suspicious_ip("8.8.8.8") is False
        assert security_service._is_suspicious_ip("1.1.1.1") is False
    
    def test_has_malicious_patterns(self, security_service):
        """Test malicious pattern detection"""
        # Test bot user agents
        details = {"user_agent": "python-requests/2.25.1"}
        assert security_service._has_malicious_patterns(details) is True
        
        details = {"user_agent": "curl/7.68.0"}
        assert security_service._has_malicious_patterns(details) is True
        
        # Test rapid requests
        details = {"requests_per_minute": 100}
        assert security_service._has_malicious_patterns(details) is True
        
        # Test normal user agents
        details = {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        assert security_service._has_malicious_patterns(details) is False
    
    @patch('requests.post')
    def test_verify_recaptcha(self, mock_post, security_service):
        """Test reCAPTCHA verification"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        result = security_service._verify_recaptcha("test_token", "192.168.1.1")
        assert result is True
        
        # Mock failed response
        mock_response.json.return_value = {"success": False}
        result = security_service._verify_recaptcha("test_token", "192.168.1.1")
        assert result is False
        
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        result = security_service._verify_recaptcha("test_token", "192.168.1.1")
        assert result is False
    
    def test_should_require_captcha(self, security_service, mock_db_session):
        """Test CAPTCHA requirement logic"""
        # Mock database response for failed attempts
        mock_result = Mock()
        mock_result.failed_count = 5
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = security_service.should_require_captcha("user1", "192.168.1.1")
        assert result is True
        
        # Test with suspicious IP
        mock_result.failed_count = 0
        result = security_service.should_require_captcha("user1", "0.0.0.0")
        assert result is True
    
    def test_log_security_event(self, security_service, mock_db_session):
        """Test security event logging"""
        event = SecurityEvent(
            event_type="test_event",
            user_id="user1",
            ip_address="192.168.1.1",
            user_agent="test_agent",
            phone_number="+11234567890",
            details={"test": "data"},
            risk_score=0.5,
            timestamp=datetime.utcnow()
        )
        
        security_service.log_security_event(event)
        
        # Verify database was called
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_cleanup_old_data(self, security_service, mock_db_session):
        """Test old data cleanup"""
        mock_result = Mock()
        mock_result.rowcount = 100
        mock_db_session.execute.return_value = mock_result
        
        deleted_count = security_service.cleanup_old_data(days=90)
        assert deleted_count == 100
        
        # Verify database was called
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()

class TestSecurityEvent:
    """Test suite for SecurityEvent dataclass"""
    
    def test_security_event_creation(self):
        """Test SecurityEvent creation"""
        event = SecurityEvent(
            event_type="test_event",
            user_id="user1",
            ip_address="192.168.1.1",
            user_agent="test_agent",
            phone_number="+11234567890",
            details={"test": "data"},
            risk_score=0.5,
            timestamp=datetime.utcnow()
        )
        
        assert event.event_type == "test_event"
        assert event.user_id == "user1"
        assert event.ip_address == "192.168.1.1"
        assert event.risk_score == 0.5

def test_get_backoff_delay():
    """Test exponential backoff delay calculation"""
    # Test progressive delays
    assert get_backoff_delay(0) == 1000   # 1 second
    assert get_backoff_delay(1) == 2000   # 2 seconds
    assert get_backoff_delay(2) == 4000   # 4 seconds
    assert get_backoff_delay(3) == 8000   # 8 seconds
    assert get_backoff_delay(4) == 16000  # 16 seconds
    assert get_backoff_delay(5) == 30000  # Max delay (30 seconds)
    assert get_backoff_delay(10) == 30000 # Still max delay 