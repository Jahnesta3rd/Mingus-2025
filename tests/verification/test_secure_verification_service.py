"""
Integration Tests for Secure Verification Service
Tests the complete verification flow with security measures
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.services.secure_verification_service import SecureVerificationService

class TestSecureVerificationService:
    """Test suite for SecureVerificationService"""
    
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
    def mock_request(self):
        """Mock Flask request object"""
        request = Mock()
        request.remote_addr = "192.168.1.1"
        request.headers = {
            "X-Forwarded-For": "203.0.113.1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        return request
    
    @pytest.fixture
    def verification_service(self, mock_db_session):
        """Create SecureVerificationService instance"""
        return SecureVerificationService(mock_db_session)
    
    def test_get_client_ip(self, verification_service, mock_request):
        """Test client IP extraction"""
        # Test X-Forwarded-For header
        ip = verification_service.get_client_ip(mock_request)
        assert ip == "203.0.113.1"
        
        # Test X-Real-IP header
        mock_request.headers = {"X-Real-IP": "198.51.100.1"}
        ip = verification_service.get_client_ip(mock_request)
        assert ip == "198.51.100.1"
        
        # Test direct remote address
        mock_request.headers = {}
        ip = verification_service.get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_user_agent(self, verification_service, mock_request):
        """Test user agent extraction"""
        user_agent = verification_service.get_user_agent(mock_request)
        assert "Mozilla" in user_agent
        
        # Test missing user agent
        mock_request.headers = {}
        user_agent = verification_service.get_user_agent(mock_request)
        assert user_agent == "Unknown"
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_send_verification_code_success(self, mock_security_class, verification_service, mock_request):
        """Test successful verification code sending"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.validate_phone_number.return_value = True
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        mock_security.detect_sim_swap_attack.return_value = False
        mock_security.should_require_captcha.return_value = False
        mock_security.generate_secure_code.return_value = "123456"
        mock_security.hash_verification_code.return_value = ("hash", "salt")
        mock_security.calculate_risk_score.return_value = 0.1
        
        # Mock database operations
        mock_result = Mock()
        mock_result.id = "verification_123"
        verification_service.db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = verification_service.send_verification_code(
            mock_request, "user123", "+11234567890"
        )
        
        assert result["success"] is True
        assert "verification_id" in result
        assert result["risk_score"] == 0.1
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_send_verification_code_rate_limited(self, mock_security_class, verification_service, mock_request):
        """Test rate limiting in verification code sending"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (False, 60)
        
        result = verification_service.send_verification_code(
            mock_request, "user123", "+11234567890"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "rate_limit"
        assert result["retry_after"] == 60
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_send_verification_code_invalid_phone(self, mock_security_class, verification_service, mock_request):
        """Test invalid phone number handling"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.validate_phone_number.return_value = False
        
        result = verification_service.send_verification_code(
            mock_request, "user123", "invalid_phone"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "phone_invalid"
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_send_verification_code_sim_swap_detected(self, mock_security_class, verification_service, mock_request):
        """Test SIM swap attack detection"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.validate_phone_number.return_value = True
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        mock_security.detect_sim_swap_attack.return_value = True
        
        result = verification_service.send_verification_code(
            mock_request, "user123", "+11234567890"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "sim_swap_detected"
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_send_verification_code_captcha_required(self, mock_security_class, verification_service, mock_request):
        """Test CAPTCHA requirement"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.validate_phone_number.return_value = True
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        mock_security.detect_sim_swap_attack.return_value = False
        mock_security.should_require_captcha.return_value = True
        
        result = verification_service.send_verification_code(
            mock_request, "user123", "+11234567890"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "captcha_required"
        assert result["captcha_required"] is True
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_verify_code_success(self, mock_security_class, verification_service, mock_request):
        """Test successful code verification"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        mock_security.verify_code_hash.return_value = True
        
        # Mock database response
        mock_verification = Mock()
        mock_verification.id = "verification_123"
        mock_verification.verification_code_hash = "hash"
        mock_verification.salt = "salt"
        mock_verification.code_expires_at = datetime.utcnow() + timedelta(minutes=5)
        mock_verification.attempts = 0
        mock_verification.status = "pending"
        mock_verification.resend_count = 1
        mock_verification.ip_address = "192.168.1.1"
        mock_verification.user_agent = "test_agent"
        mock_verification.captcha_verified = True
        mock_verification.risk_score = 0.1
        
        verification_service._get_latest_verification = Mock(return_value=mock_verification)
        
        result = verification_service.verify_code(
            mock_request, "user123", "+11234567890", "123456"
        )
        
        assert result["success"] is True
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_verify_code_rate_limited(self, mock_security_class, verification_service, mock_request):
        """Test rate limiting in code verification"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (False, 60)
        
        result = verification_service.verify_code(
            mock_request, "user123", "+11234567890", "123456"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "rate_limit"
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_verify_code_invalid(self, mock_security_class, verification_service, mock_request):
        """Test invalid code verification"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        mock_security.verify_code_hash.return_value = False
        
        # Mock database response
        mock_verification = Mock()
        mock_verification.id = "verification_123"
        mock_verification.verification_code_hash = "hash"
        mock_verification.salt = "salt"
        mock_verification.code_expires_at = datetime.utcnow() + timedelta(minutes=5)
        mock_verification.attempts = 0
        mock_verification.status = "pending"
        mock_verification.resend_count = 1
        mock_verification.ip_address = "192.168.1.1"
        mock_verification.user_agent = "test_agent"
        mock_verification.captcha_verified = True
        mock_verification.risk_score = 0.1
        
        verification_service._get_latest_verification = Mock(return_value=mock_verification)
        
        result = verification_service.verify_code(
            mock_request, "user123", "+11234567890", "654321"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "invalid_code"
        assert result["remaining_attempts"] == 2
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_verify_code_expired(self, mock_security_class, verification_service, mock_request):
        """Test expired code verification"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        
        # Mock database response with expired code
        mock_verification = Mock()
        mock_verification.code_expires_at = datetime.utcnow() - timedelta(minutes=5)
        
        verification_service._get_latest_verification = Mock(return_value=mock_verification)
        
        result = verification_service.verify_code(
            mock_request, "user123", "+11234567890", "123456"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "expired_code"
    
    @patch('backend.services.secure_verification_service.VerificationSecurity')
    def test_verify_code_max_attempts(self, mock_security_class, verification_service, mock_request):
        """Test maximum attempts reached"""
        # Mock security service
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        mock_security.check_rate_limit.return_value = (True, None)
        mock_security.sanitize_phone_number.return_value = "+11234567890"
        
        # Mock database response with max attempts
        mock_verification = Mock()
        mock_verification.attempts = 3  # Max attempts reached
        mock_verification.code_expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        verification_service._get_latest_verification = Mock(return_value=mock_verification)
        
        result = verification_service.verify_code(
            mock_request, "user123", "+11234567890", "123456"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "max_attempts"
    
    def test_store_secure_verification_attempt(self, verification_service):
        """Test storing verification attempt with security context"""
        # Mock database response
        mock_result = Mock()
        mock_result.id = "verification_123"
        verification_service.db_session.execute.return_value.fetchone.return_value = mock_result
        
        verification_id = verification_service._store_secure_verification_attempt(
            user_id="user123",
            phone_number="+11234567890",
            code_hash="hash",
            salt="salt",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            ip_address="192.168.1.1",
            user_agent="test_agent",
            captcha_verified=True
        )
        
        assert verification_id == "verification_123"
        verification_service.db_session.execute.assert_called()
        verification_service.db_session.commit.assert_called()
    
    def test_get_latest_verification(self, verification_service):
        """Test getting latest verification with security context"""
        # Mock database response
        mock_result = Mock()
        mock_result.id = "verification_123"
        mock_result.user_id = "user123"
        mock_result.phone_number = "+11234567890"
        mock_result.verification_code_hash = "hash"
        mock_result.salt = "salt"
        mock_result.code_sent_at = datetime.utcnow()
        mock_result.code_expires_at = datetime.utcnow() + timedelta(minutes=10)
        mock_result.attempts = 0
        mock_result.status = "pending"
        mock_result.resend_count = 1
        mock_result.ip_address = "192.168.1.1"
        mock_result.user_agent = "test_agent"
        mock_result.captcha_verified = True
        mock_result.risk_score = 0.1
        
        verification_service.db_session.execute.return_value.fetchone.return_value = mock_result
        
        verification = verification_service._get_latest_verification("user123", "+11234567890")
        
        assert verification["id"] == "verification_123"
        assert verification["user_id"] == "user123"
        assert verification["phone_number"] == "+11234567890"
        assert verification["ip_address"] == "192.168.1.1"
        assert verification["captcha_verified"] is True
        assert verification["risk_score"] == 0.1
    
    def test_update_verification_risk_score(self, verification_service):
        """Test updating verification risk score"""
        verification_service._update_verification_risk_score("verification_123", 0.8)
        
        verification_service.db_session.execute.assert_called()
        verification_service.db_session.commit.assert_called()
    
    def test_mark_verification_success(self, verification_service):
        """Test marking verification as successful"""
        verification_service._mark_verification_success("verification_123")
        
        verification_service.db_session.execute.assert_called()
        verification_service.db_session.commit.assert_called()
    
    def test_increment_attempt_count(self, verification_service):
        """Test incrementing attempt count"""
        verification_service._increment_attempt_count("verification_123")
        
        verification_service.db_session.execute.assert_called()
        verification_service.db_session.commit.assert_called()
    
    def test_get_security_summary(self, verification_service):
        """Test getting security summary for user"""
        # Mock database response
        mock_result = Mock()
        mock_result.user_id = "user123"
        mock_result.total_verifications = 5
        mock_result.successful_verifications = 3
        mock_result.failed_verifications = 2
        mock_result.unique_ips = 2
        mock_result.unique_phones = 1
        mock_result.last_verification = datetime.utcnow()
        mock_result.avg_risk_score = 0.3
        
        verification_service.db_session.execute.return_value.fetchone.return_value = mock_result
        
        summary = verification_service.get_security_summary("user123")
        
        assert summary["user_id"] == "user123"
        assert summary["total_verifications"] == 5
        assert summary["successful_verifications"] == 3
        assert summary["failed_verifications"] == 2
        assert summary["unique_ips"] == 2
        assert summary["unique_phones"] == 1
        assert summary["avg_risk_score"] == 0.3 