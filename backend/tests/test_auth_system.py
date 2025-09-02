#!/usr/bin/env python3
"""
Comprehensive Test Suite for MINGUS Authentication System
Tests email verification, password reset, and token management
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash

from backend.services.auth_service import AuthService
from backend.models.auth_tokens import AuthToken
from backend.models.email_verification import EmailVerification
from backend.models.user import User
from backend.services.resend_email_service import resend_email_service

class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory for testing"""
        return MagicMock()
    
    @pytest.fixture
    def auth_service(self, mock_session_factory):
        """AuthService instance for testing"""
        return AuthService(mock_session_factory)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user data"""
        return {
            'id': 1,
            'email': 'test@example.com',
            'full_name': 'Test User',
            'is_active': True,
            'email_verified': False
        }
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.add.return_value = None
        session.commit.return_value = None
        session.rollback.return_value = None
        session.close.return_value = None
        return session
    
    def test_generate_secure_token(self, auth_service):
        """Test secure token generation"""
        token1 = auth_service._generate_secure_token()
        token2 = auth_service._generate_secure_token()
        
        assert len(token1) >= 32
        assert len(token2) >= 32
        assert token1 != token2
    
    def test_hash_token(self, auth_service):
        """Test token hashing"""
        token = "test_token_123"
        hash1 = auth_service._hash_token(token)
        hash2 = auth_service._hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 != token
    
    def test_validate_token_format(self, auth_service):
        """Test token format validation"""
        # Valid tokens
        assert auth_service._validate_token_format("valid_token_32_chars_long_enough")
        assert auth_service._validate_token_format("a" * 32)
        
        # Invalid tokens
        assert not auth_service._validate_token_format("")
        assert not auth_service._validate_token_format(None)
        assert not auth_service._validate_token_format("short")
        assert not auth_service._validate_token_format("a" * 31)
    
    @patch('backend.services.auth_service.datetime')
    def test_create_email_verification_new(self, mock_datetime, auth_service, mock_session):
        """Test creating new email verification"""
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
        expected_expiry = datetime(2025, 1, 2, 12, 0, 0)
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        success, message, token = auth_service.create_email_verification(
            user_id=1, 
            email="test@example.com"
        )
        
        assert success is True
        assert "sent successfully" in message
        assert token is not None
        assert len(token) >= 32
        
        # Verify session operations
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('backend.services.auth_service.datetime')
    def test_create_email_verification_existing_can_resend(self, mock_datetime, auth_service, mock_session):
        """Test updating existing verification when resend is allowed"""
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
        
        # Mock existing verification that can be resent
        existing_verification = MagicMock()
        existing_verification.can_resend.return_value = True
        existing_verification.resend_count = 2
        existing_verification.increment_resend_count = MagicMock()
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_verification
        
        success, message, token = auth_service.create_email_verification(
            user_id=1, 
            email="test@example.com"
        )
        
        assert success is True
        assert "resent successfully" in message
        assert token is not None
        
        # Verify methods were called
        existing_verification.increment_resend_count.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_create_email_verification_existing_cannot_resend(self, auth_service, mock_session):
        """Test handling when resend is not allowed"""
        # Mock existing verification that cannot be resent
        existing_verification = MagicMock()
        existing_verification.can_resend.return_value = False
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_verification
        
        success, message, token = auth_service.create_email_verification(
            user_id=1, 
            email="test@example.com"
        )
        
        assert success is False
        assert "wait before requesting" in message
        assert token is None
    
    def test_create_email_verification_max_resend_reached(self, auth_service, mock_session):
        """Test handling when max resend attempts reached"""
        # Mock existing verification at max resend count
        existing_verification = MagicMock()
        existing_verification.can_resend.return_value = True
        existing_verification.resend_count = 5  # Max attempts
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_verification
        
        success, message, token = auth_service.create_email_verification(
            user_id=1, 
            email="test@example.com"
        )
        
        assert success is False
        assert "Maximum resend attempts reached" in message
        assert token is None
    
    def test_verify_email_success(self, auth_service, mock_session):
        """Test successful email verification"""
        # Mock verification record
        verification = MagicMock()
        verification.is_expired.return_value = False
        verification.is_verified.return_value = False
        verification.mark_verified = MagicMock()
        
        # Mock user
        user = MagicMock()
        user.email_verified = False
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [verification, user]
        
        success, message, user_id = auth_service.verify_email("valid_token")
        
        assert success is True
        assert "verified successfully" in message
        assert user_id == verification.user_id
        
        # Verify methods were called
        verification.mark_verified.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_verify_email_invalid_token(self, auth_service, mock_session):
        """Test email verification with invalid token"""
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        success, message, user_id = auth_service.verify_email("invalid_token")
        
        assert success is False
        assert "Invalid verification token" in message
        assert user_id is None
    
    def test_verify_email_expired_token(self, auth_service, mock_session):
        """Test email verification with expired token"""
        verification = MagicMock()
        verification.is_expired.return_value = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = verification
        
        success, message, user_id = auth_service.verify_email("expired_token")
        
        assert success is False
        assert "expired" in message
        assert user_id is None
    
    def test_verify_email_already_verified(self, auth_service, mock_session):
        """Test email verification when already verified"""
        verification = MagicMock()
        verification.is_expired.return_value = False
        verification.is_verified.return_value = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = verification
        
        success, message, user_id = auth_service.verify_email("already_verified_token")
        
        assert success is False
        assert "already verified" in message
        assert user_id is None
    
    def test_resend_verification_email_success(self, auth_service, mock_session):
        """Test successful verification email resend"""
        # Mock user
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.email_verified = False
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Mock create_email_verification
        with patch.object(auth_service, 'create_email_verification') as mock_create:
            mock_create.return_value = (True, "Verification email sent successfully", "new_token")
            
            success, message = auth_service.resend_verification_email("test@example.com")
            
            assert success is True
            assert "sent successfully" in message
    
    def test_resend_verification_email_user_not_found(self, auth_service, mock_session):
        """Test resend when user not found"""
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        success, message = auth_service.resend_verification_email("nonexistent@example.com")
        
        # Should return success to avoid user enumeration
        assert success is True
        assert "If the email exists" in message
    
    def test_resend_verification_email_already_verified(self, auth_service, mock_session):
        """Test resend when email already verified"""
        user = MagicMock()
        user.email_verified = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        
        success, message = auth_service.resend_verification_email("verified@example.com")
        
        assert success is False
        assert "already verified" in message
    
    def test_create_password_reset_token_success(self, auth_service, mock_session):
        """Test successful password reset token creation"""
        user = MagicMock()
        user.id = 1
        user.is_active = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Mock no existing tokens
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        success, message, token = auth_service.create_password_reset_token("test@example.com")
        
        assert success is True
        assert "sent successfully" in message
        assert token is not None
        assert len(token) >= 32
    
    def test_create_password_reset_token_user_not_found(self, auth_service, mock_session):
        """Test password reset when user not found"""
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        success, message, token = auth_service.create_password_reset_token("nonexistent@example.com")
        
        # Should return success to avoid user enumeration
        assert success is True
        assert "If the email exists" in message
        assert token is None
    
    def test_create_password_reset_token_user_inactive(self, auth_service, mock_session):
        """Test password reset when user is inactive"""
        user = MagicMock()
        user.is_active = False
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        
        success, message, token = auth_service.create_password_reset_token("inactive@example.com")
        
        assert success is False
        assert "not active" in message
        assert token is None
    
    def test_create_password_reset_token_existing_token(self, auth_service, mock_session):
        """Test password reset when token already exists"""
        user = MagicMock()
        user.id = 1
        user.is_active = True
        
        # Mock existing unused token
        existing_token = MagicMock()
        existing_token.used_at = None
        existing_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        mock_session.query.return_value.filter.return_value.first.return_value = existing_token
        
        success, message, token = auth_service.create_password_reset_token("test@example.com")
        
        assert success is False
        assert "already requested" in message
        assert token is None
    
    def test_validate_password_reset_token_success(self, auth_service, mock_session):
        """Test successful password reset token validation"""
        # Mock token
        auth_token = MagicMock()
        auth_token.is_expired.return_value = False
        auth_token.is_used.return_value = False
        auth_token.user_id = 1
        
        # Mock user
        user = MagicMock()
        user.is_active = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [auth_token, user]
        
        success, message, user_id = auth_service.validate_password_reset_token("valid_token")
        
        assert success is True
        assert "valid" in message
        assert user_id == 1
    
    def test_validate_password_reset_token_invalid(self, auth_service, mock_session):
        """Test password reset token validation with invalid token"""
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        success, message, user_id = auth_service.validate_password_reset_token("invalid_token")
        
        assert success is False
        assert "Invalid reset token" in message
        assert user_id is None
    
    def test_validate_password_reset_token_expired(self, auth_service, mock_session):
        """Test password reset token validation with expired token"""
        auth_token = MagicMock()
        auth_token.is_expired.return_value = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = auth_token
        
        success, message, user_id = auth_service.validate_password_reset_token("expired_token")
        
        assert success is False
        assert "expired" in message
        assert user_id is None
    
    def test_validate_password_reset_token_used(self, auth_service, mock_session):
        """Test password reset token validation with used token"""
        auth_token = MagicMock()
        auth_token.is_expired.return_value = False
        auth_token.is_used.return_value = True
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = auth_token
        
        success, message, user_id = auth_service.validate_password_reset_token("used_token")
        
        assert success is False
        assert "already been used" in message
        assert user_id is None
    
    def test_reset_password_success(self, auth_service, mock_session):
        """Test successful password reset"""
        # Mock token
        auth_token = MagicMock()
        auth_token.is_expired.return_value = False
        auth_token.is_used.return_value = False
        auth_token.user_id = 1
        auth_token.mark_used = MagicMock()
        
        # Mock user
        user = MagicMock()
        user.is_active = True
        user.password_hash = "old_hash"
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [auth_token, user]
        
        success, message = auth_service.reset_password("valid_token", "NewPassword123!")
        
        assert success is True
        assert "reset successfully" in message
        
        # Verify methods were called
        auth_token.mark_used.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_reset_password_weak_password(self, auth_service, mock_session):
        """Test password reset with weak password"""
        success, message = auth_service.reset_password("valid_token", "weak")
        
        assert success is False
        assert "at least 8 characters" in message
    
    def test_cleanup_expired_tokens(self, auth_service, mock_session):
        """Test cleanup of expired tokens"""
        # Mock expired tokens
        expired_auth_tokens = [MagicMock(), MagicMock()]
        expired_verifications = [MagicMock()]
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            expired_auth_tokens, expired_verifications
        ]
        
        cleaned_count = auth_service.cleanup_expired_tokens()
        
        assert cleaned_count == 3  # 2 auth tokens + 1 verification
        mock_session.commit.assert_called_once()
    
    def test_get_user_verification_status_success(self, auth_service, mock_session):
        """Test getting user verification status"""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.email_verified = False
        
        verification = MagicMock()
        verification.is_expired.return_value = False
        verification.can_resend.return_value = True
        verification.resend_count = 2
        
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [user, verification]
        
        status = auth_service.get_user_verification_status(1)
        
        assert status['user_id'] == 1
        assert status['email'] == "test@example.com"
        assert status['email_verified'] is False
        assert status['verification_status']['has_verification'] is True
        assert status['verification_status']['resend_count'] == 2
    
    def test_get_user_verification_status_user_not_found(self, auth_service, mock_session):
        """Test getting verification status for non-existent user"""
        auth_service.SessionLocal.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        status = auth_service.get_user_verification_status(999)
        
        assert 'error' in status
        assert status['error'] == 'User not found'


class TestAuthTokensModel:
    """Test cases for AuthToken model"""
    
    def test_generate_token(self):
        """Test token generation"""
        token1 = AuthToken.generate_token()
        token2 = AuthToken.generate_token()
        
        assert len(token1) >= 32
        assert len(token2) >= 32
        assert token1 != token2
    
    def test_hash_token(self):
        """Test token hashing"""
        token = "test_token_123"
        hash1 = AuthToken.hash_token(token)
        hash2 = AuthToken.hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64
        assert hash1 != token
    
    def test_is_expired(self):
        """Test token expiration check"""
        # Future token
        future_token = AuthToken()
        future_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        assert not future_token.is_expired()
        
        # Expired token
        expired_token = AuthToken()
        expired_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert expired_token.is_expired()
    
    def test_is_used(self):
        """Test token usage check"""
        # Unused token
        unused_token = AuthToken()
        unused_token.used_at = None
        assert not unused_token.is_used()
        
        # Used token
        used_token = AuthToken()
        used_token.used_at = datetime.utcnow()
        assert used_token.is_used()
    
    def test_mark_used(self):
        """Test marking token as used"""
        token = AuthToken()
        token.used_at = None
        
        token.mark_used()
        
        assert token.used_at is not None
        assert isinstance(token.used_at, datetime)


class TestEmailVerificationModel:
    """Test cases for EmailVerification model"""
    
    def test_is_expired(self):
        """Test verification expiration check"""
        # Future verification
        future_verification = EmailVerification()
        future_verification.expires_at = datetime.utcnow() + timedelta(hours=1)
        assert not future_verification.is_expired()
        
        # Expired verification
        expired_verification = EmailVerification()
        expired_verification.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert expired_verification.is_expired()
    
    def test_is_verified(self):
        """Test verification status check"""
        # Unverified
        unverified = EmailVerification()
        unverified.verified_at = None
        assert not unverified.is_verified()
        
        # Verified
        verified = EmailVerification()
        verified.verified_at = datetime.utcnow()
        assert verified.is_verified()
    
    def test_mark_verified(self):
        """Test marking verification as verified"""
        verification = EmailVerification()
        verification.verified_at = None
        
        verification.mark_verified()
        
        assert verification.verified_at is not None
        assert isinstance(verification.verified_at, datetime)
    
    def test_can_resend(self):
        """Test resend capability check"""
        # Never sent
        never_sent = EmailVerification()
        never_sent.last_resend_at = None
        assert never_sent.can_resend()
        
        # Sent recently (within 5 minutes)
        recent_sent = EmailVerification()
        recent_sent.last_resend_at = datetime.utcnow() - timedelta(minutes=3)
        assert not recent_sent.can_resend()
        
        # Sent long ago (more than 5 minutes)
        old_sent = EmailVerification()
        old_sent.last_resend_at = datetime.utcnow() - timedelta(minutes=10)
        assert old_sent.can_resend()
    
    def test_increment_resend_count(self):
        """Test resend counter increment"""
        verification = EmailVerification()
        verification.resend_count = 0
        verification.last_resend_at = None
        
        verification.increment_resend_count()
        
        assert verification.resend_count == 1
        assert verification.last_resend_at is not None
        assert isinstance(verification.last_resend_at, datetime)


class TestAuthIntegration:
    """Integration tests for authentication system"""
    
    @pytest.fixture
    def app(self):
        """Flask app fixture"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Test client fixture"""
        return app.test_client()
    
    def test_verify_email_endpoint_integration(self, client):
        """Test email verification endpoint integration"""
        # This would test the actual Flask endpoint
        # Implementation depends on your app structure
        pass
    
    def test_password_reset_endpoint_integration(self, client):
        """Test password reset endpoint integration"""
        # This would test the actual Flask endpoint
        # Implementation depends on your app structure
        pass


if __name__ == '__main__':
    pytest.main([__file__])
