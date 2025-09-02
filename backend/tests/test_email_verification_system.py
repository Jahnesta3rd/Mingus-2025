"""
Comprehensive Tests for Email Verification System
Tests all components including models, services, tasks, and endpoints
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..models.email_verification import EmailVerification
from ..models.user import User
from ..services.email_verification_service import EmailVerificationService
from ..tasks.email_verification_tasks import (
    send_verification_email, send_verification_reminder,
    cleanup_expired_verifications, send_bulk_verification_reminders,
    process_verification_analytics
)

# Test configuration
@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine('sqlite:///:memory:')
    from ..models.base import Base
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()

@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('backend.services.email_verification_service.ResendEmailService') as mock:
        service = mock.return_value
        service.send_verification_email.return_value = True
        service.send_email_change_verification.return_value = True
        service.send_verification_reminder.return_value = True
        yield service

@pytest.fixture
def sample_user(test_db):
    """Create sample user for testing"""
    user = User(
        id=1,
        email='test@example.com',
        full_name='Test User',
        password_hash='hashed_password',
        email_verified=False
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def sample_verification(test_db, sample_user):
    """Create sample verification for testing"""
    verification = EmailVerification(
        user_id=sample_user.id,
        email=sample_user.email,
        verification_token_hash='test_hash',
        expires_at=datetime.utcnow() + timedelta(hours=24),
        verification_type='signup'
    )
    test_db.add(verification)
    test_db.commit()
    return verification

class TestEmailVerificationModel:
    """Test EmailVerification model functionality"""
    
    def test_create_verification(self, test_db):
        """Test creating a new verification record"""
        user_id = 1
        email = 'test@example.com'
        verification_type = 'signup'
        
        verification, token = EmailVerification.create_verification(
            user_id, email, verification_type
        )
        
        assert verification.user_id == user_id
        assert verification.email == email
        assert verification.verification_type == verification_type
        assert verification.expires_at > datetime.utcnow()
        assert token is not None
        assert len(token) > 0
    
    def test_is_expired(self, test_db):
        """Test expiration checking"""
        # Not expired
        verification = EmailVerification(
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert not verification.is_expired
        
        # Expired
        verification.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert verification.is_expired
    
    def test_is_verified(self, test_db):
        """Test verification status checking"""
        # Not verified
        verification = EmailVerification()
        assert not verification.is_verified
        
        # Verified
        verification.verified_at = datetime.utcnow()
        assert verification.is_verified
    
    def test_is_locked(self, test_db):
        """Test lockout status checking"""
        # Not locked
        verification = EmailVerification()
        assert not verification.is_locked
        
        # Locked
        verification.locked_until = datetime.utcnow() + timedelta(hours=1)
        assert verification.is_locked
        
        # Lock expired
        verification.locked_until = datetime.utcnow() - timedelta(hours=1)
        assert not verification.is_locked
    
    def test_can_resend(self, test_db):
        """Test resend capability checking"""
        verification = EmailVerification(
            resend_count=0,
            verified_at=None
        )
        assert verification.can_resend
        
        # Max resends reached
        verification.resend_count = 5
        assert not verification.can_resend
        
        # Already verified
        verification.resend_count = 0
        verification.verified_at = datetime.utcnow()
        assert not verification.can_resend
        
        # Cooldown period
        verification.verified_at = None
        verification.last_resend_at = datetime.utcnow() - timedelta(minutes=30)
        assert not verification.can_resend
    
    def test_verify_token(self, test_db):
        """Test token verification"""
        verification = EmailVerification(
            expires_at=datetime.utcnow() + timedelta(hours=1),
            verified_at=None
        )
        
        # Mock the hash_token method
        with patch.object(verification, 'hash_token', return_value='expected_hash'):
            verification.verification_token_hash = 'expected_hash'
            
            # Valid token
            assert verification.verify_token('valid_token')
            
            # Expired
            verification.expires_at = datetime.utcnow() - timedelta(hours=1)
            assert not verification.verify_token('valid_token')
            
            # Already verified
            verification.expires_at = datetime.utcnow() + timedelta(hours=1)
            verification.verified_at = datetime.utcnow()
            assert not verification.verify_token('valid_token')
    
    def test_record_failed_attempt(self, test_db):
        """Test recording failed attempts"""
        verification = EmailVerification()
        
        # Record failed attempts
        for i in range(4):
            verification.record_failed_attempt()
            assert verification.failed_attempts == i + 1
        
        # 5th attempt should trigger lockout
        verification.record_failed_attempt()
        assert verification.failed_attempts == 5
        assert verification.locked_until is not None
        assert verification.locked_until > datetime.utcnow()
    
    def test_reset_failed_attempts(self, test_db):
        """Test resetting failed attempts"""
        verification = EmailVerification(
            failed_attempts=5,
            last_failed_attempt=datetime.utcnow(),
            locked_until=datetime.utcnow() + timedelta(hours=1)
        )
        
        verification.reset_failed_attempts()
        
        assert verification.failed_attempts == 0
        assert verification.last_failed_attempt is None
        assert verification.locked_until is None
    
    def test_to_dict(self, test_db):
        """Test dictionary conversion"""
        verification = EmailVerification(
            id=1,
            user_id=1,
            email='test@example.com',
            verification_type='signup',
            expires_at=datetime.utcnow() + timedelta(hours=24),
            resend_count=2
        )
        
        data = verification.to_dict()
        
        assert data['id'] == 1
        assert data['user_id'] == 1
        assert data['email'] == 'test@example.com'
        assert data['verification_type'] == 'signup'
        assert data['resend_count'] == 2
        assert 'is_expired' in data
        assert 'is_verified' in data
        assert 'is_locked' in data

class TestEmailVerificationService:
    """Test EmailVerificationService functionality"""
    
    def test_create_verification_new(self, test_db, mock_email_service):
        """Test creating new verification"""
        service = EmailVerificationService()
        user_id = 1
        email = 'test@example.com'
        
        verification, token = service.create_verification(
            user_id, email, 'signup'
        )
        
        assert verification.user_id == user_id
        assert verification.email == email
        assert token is not None
        
        # Check database
        db_verification = test_db.query(EmailVerification).filter_by(user_id=user_id).first()
        assert db_verification is not None
        assert db_verification.email == email
    
    def test_create_verification_existing(self, test_db, mock_email_service, sample_verification):
        """Test updating existing verification"""
        service = EmailVerificationService()
        user_id = sample_verification.user_id
        email = 'new@example.com'
        
        verification, token = service.create_verification(
            user_id, email, 'signup'
        )
        
        assert verification.id == sample_verification.id
        assert verification.email == email
        assert token is not None
        
        # Check database
        test_db.refresh(verification)
        assert verification.email == email
        assert verification.resend_count == 0
    
    def test_verify_email_success(self, test_db, mock_email_service, sample_verification):
        """Test successful email verification"""
        service = EmailVerificationService()
        
        # Mock token verification
        with patch.object(EmailVerification, 'verify_token', return_value=True):
            success, message, user_data = service.verify_email('valid_token')
            
            assert success
            assert 'successfully' in message.lower()
            assert user_data is not None
            
            # Check database
            test_db.refresh(sample_verification)
            assert sample_verification.verified_at is not None
            assert sample_verification.failed_attempts == 0
    
    def test_verify_email_invalid_token(self, test_db, mock_email_service):
        """Test verification with invalid token"""
        service = EmailVerificationService()
        
        success, message, user_data = service.verify_email('invalid_token')
        
        assert not success
        assert 'invalid' in message.lower()
        assert user_data is None
    
    def test_verify_email_expired(self, test_db, mock_email_service, sample_verification):
        """Test verification with expired token"""
        service = EmailVerificationService()
        
        # Make token expired
        sample_verification.expires_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()
        
        success, message, user_data = service.verify_email('valid_token')
        
        assert not success
        assert 'expired' in message.lower()
        assert user_data is None
        
        # Check failed attempt recorded
        test_db.refresh(sample_verification)
        assert sample_verification.failed_attempts == 1
    
    def test_verify_email_locked(self, test_db, mock_email_service, sample_verification):
        """Test verification when account is locked"""
        service = EmailVerificationService()
        
        # Lock account
        sample_verification.locked_until = datetime.utcnow() + timedelta(hours=1)
        test_db.commit()
        
        success, message, user_data = service.verify_email('valid_token')
        
        assert not success
        assert 'locked' in message.lower()
        assert user_data is None
    
    def test_resend_verification_success(self, test_db, mock_email_service, sample_verification):
        """Test successful resend of verification"""
        service = EmailVerificationService()
        
        success, message = service.resend_verification(sample_verification.user_id)
        
        assert success
        assert 'sent successfully' in message.lower()
        
        # Check database
        test_db.refresh(sample_verification)
        assert sample_verification.resend_count == 1
        assert sample_verification.last_resend_at is not None
    
    def test_resend_verification_max_attempts(self, test_db, mock_email_service, sample_verification):
        """Test resend with max attempts reached"""
        service = EmailVerificationService()
        
        # Set max resends
        sample_verification.resend_count = 5
        test_db.commit()
        
        success, message = service.resend_verification(sample_verification.user_id)
        
        assert not success
        assert 'maximum' in message.lower()
    
    def test_resend_verification_cooldown(self, test_db, mock_email_service, sample_verification):
        """Test resend during cooldown period"""
        service = EmailVerificationService()
        
        # Set recent resend
        sample_verification.last_resend_at = datetime.utcnow() - timedelta(minutes=30)
        test_db.commit()
        
        success, message = service.resend_verification(sample_verification.user_id)
        
        assert not success
        assert 'wait' in message.lower()
    
    def test_change_email_verification(self, test_db, mock_email_service, sample_user):
        """Test initiating email change verification"""
        service = EmailVerificationService()
        new_email = 'new@example.com'
        
        success, message = service.change_email_verification(
            sample_user.id, new_email, 'current_password'
        )
        
        assert success
        assert 'sent to new address' in message.lower()
        
        # Check verification created
        verification = test_db.query(EmailVerification).filter_by(
            user_id=sample_user.id,
            verification_type='email_change'
        ).first()
        assert verification is not None
        assert verification.email == new_email
        assert verification.old_email == sample_user.email
    
    def test_get_verification_status(self, test_db, mock_email_service, sample_verification):
        """Test getting verification status"""
        service = EmailVerificationService()
        
        status = service.get_verification_status(sample_verification.user_id)
        
        assert status['user_id'] == sample_verification.user_id
        assert status['email'] == sample_verification.email
        assert status['verification_type'] == sample_verification.verification_type
        assert 'is_expired' in status
        assert 'is_verified' in status
        assert 'is_locked' in status
    
    def test_cleanup_expired_verifications(self, test_db, mock_email_service):
        """Test cleanup of expired verifications"""
        service = EmailVerificationService()
        
        # Create expired verification
        expired_verification = EmailVerification(
            user_id=1,
            email='expired@example.com',
            verification_token_hash='expired_hash',
            expires_at=datetime.utcnow() - timedelta(hours=1),
            verification_type='signup'
        )
        test_db.add(expired_verification)
        test_db.commit()
        
        # Run cleanup
        cleaned_count = service.cleanup_expired_verifications()
        
        assert cleaned_count == 1
        
        # Check database
        verification = test_db.query(EmailVerification).filter_by(
            email='expired@example.com'
        ).first()
        assert verification is None

class TestEmailVerificationTasks:
    """Test Celery tasks functionality"""
    
    @patch('backend.tasks.email_verification_tasks.email_verification_service')
    @patch('backend.tasks.email_verification_tasks.email_service')
    def test_send_verification_email_success(self, mock_email_service, mock_verification_service):
        """Test successful verification email task"""
        mock_verification_service.create_verification.return_value = (
            Mock(id=1, expires_at=datetime.utcnow() + timedelta(hours=24)), 'token'
        )
        mock_email_service.send_verification_email.return_value = True
        
        result = send_verification_email(1, 'test@example.com', 'signup')
        
        assert result['success']
        assert 'sent successfully' in result['message']
        assert result['user_id'] == 1
    
    @patch('backend.tasks.email_verification_tasks.email_verification_service')
    @patch('backend.tasks.email_verification_tasks.email_service')
    def test_send_verification_email_failure(self, mock_email_service, mock_verification_service):
        """Test failed verification email task"""
        mock_verification_service.create_verification.return_value = (
            Mock(id=1, expires_at=datetime.utcnow() + timedelta(hours=24)), 'token'
        )
        mock_email_service.send_verification_email.return_value = False
        
        result = send_verification_email(1, 'test@example.com', 'signup')
        
        assert not result['success']
        assert 'Failed to send' in result['message']
    
    @patch('backend.tasks.email_verification_tasks.email_service')
    def test_send_verification_reminder_success(self, mock_email_service, test_db, sample_user, sample_verification):
        """Test successful reminder email task"""
        mock_email_service.send_verification_reminder.return_value = True
        
        # Set reminder timing
        sample_verification.created_at = datetime.utcnow() - timedelta(days=3)
        test_db.commit()
        
        result = send_verification_reminder(1, 'first')
        
        assert result['success']
        assert 'sent successfully' in result['message']
    
    def test_cleanup_expired_verifications_task(self, test_db):
        """Test cleanup task"""
        # Create expired verification
        expired_verification = EmailVerification(
            user_id=1,
            email='expired@example.com',
            verification_token_hash='expired_hash',
            expires_at=datetime.utcnow() - timedelta(hours=1),
            verification_type='signup'
        )
        test_db.add(expired_verification)
        test_db.commit()
        
        result = cleanup_expired_verifications()
        
        assert result['success']
        assert result['records_cleaned'] == 1
    
    def test_send_bulk_verification_reminders(self, test_db):
        """Test bulk reminder task"""
        # Create users needing reminders
        user1 = User(id=1, email='user1@example.com', full_name='User 1', email_verified=False)
        user2 = User(id=2, email='user2@example.com', full_name='User 2', email_verified=False)
        test_db.add_all([user1, user2])
        
        verification1 = EmailVerification(
            user_id=1, email='user1@example.com', verification_token_hash='hash1',
            expires_at=datetime.utcnow() + timedelta(hours=24), verification_type='signup',
            created_at=datetime.utcnow() - timedelta(days=3)
        )
        verification2 = EmailVerification(
            user_id=2, email='user2@example.com', verification_token_hash='hash2',
            expires_at=datetime.utcnow() + timedelta(hours=24), verification_type='signup',
            created_at=datetime.utcnow() - timedelta(days=7)
        )
        test_db.add_all([verification1, verification2])
        test_db.commit()
        
        with patch('backend.tasks.email_verification_tasks.send_verification_reminder') as mock_task:
            mock_task.delay.return_value = Mock(id='task_id')
            
            result = send_bulk_verification_reminders()
            
            assert result['success']
            assert result['total_users'] == 2
            assert result['success_count'] == 2
    
    def test_process_verification_analytics(self, test_db):
        """Test analytics processing task"""
        # Create test data
        verification1 = EmailVerification(
            user_id=1, email='user1@example.com', verification_token_hash='hash1',
            expires_at=datetime.utcnow() + timedelta(hours=24), verification_type='signup'
        )
        verification2 = EmailVerification(
            user_id=2, email='user2@example.com', verification_token_hash='hash2',
            expires_at=datetime.utcnow() + timedelta(hours=24), verification_type='signup',
            verified_at=datetime.utcnow()
        )
        test_db.add_all([verification1, verification2])
        test_db.commit()
        
        result = process_verification_analytics()
        
        assert result['success']
        assert 'data' in result
        data = result['data']
        assert data['total_verifications'] == 2
        assert data['verified_count'] == 1
        assert data['pending_count'] == 1

class TestEmailVerificationIntegration:
    """Integration tests for the complete system"""
    
    def test_complete_verification_flow(self, test_db, mock_email_service):
        """Test complete verification flow from creation to completion"""
        service = EmailVerificationService()
        
        # 1. Create verification
        verification, token = service.create_verification(
            1, 'test@example.com', 'signup'
        )
        
        assert verification is not None
        assert token is not None
        
        # 2. Verify email
        with patch.object(EmailVerification, 'verify_token', return_value=True):
            success, message, user_data = service.verify_email(token)
            
            assert success
            assert 'successfully' in message.lower()
        
        # 3. Check verification status
        status = service.get_verification_status(1)
        assert status['is_verified']
    
    def test_email_change_verification_flow(self, test_db, mock_email_service, sample_user):
        """Test complete email change verification flow"""
        service = EmailVerificationService()
        new_email = 'new@example.com'
        
        # 1. Initiate email change
        success, message = service.change_email_verification(
            sample_user.id, new_email, 'current_password'
        )
        assert success
        
        # 2. Get verification record
        verification = test_db.query(EmailVerification).filter_by(
            user_id=sample_user.id,
            verification_type='email_change'
        ).first()
        assert verification is not None
        
        # 3. Complete email change
        with patch.object(EmailVerification, 'verify_token', return_value=True):
            success, message = service.complete_email_change(verification.verification_token_hash, sample_user.id)
            assert success
        
        # 4. Check user email updated
        test_db.refresh(sample_user)
        assert sample_user.email == new_email

if __name__ == '__main__':
    pytest.main([__file__])
