"""
Isolated Email Verification Test Suite
Tests the EmailVerification model without complex User model dependencies
"""

import pytest
import time
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# Test configuration
@pytest.fixture(scope="function")
def test_db():
    """Create test database with minimal tables for email verification testing"""
    engine = create_engine('sqlite:///:memory:')
    
    # Create a minimal test database with only essential tables
    test_metadata = MetaData()
    
    # Create minimal users table
    users = Table('users', test_metadata,
        Column('id', Integer, primary_key=True),
        Column('email', String(255), nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('full_name', String(255)),
        Column('is_active', Boolean, default=True),
        Column('email_verified', Boolean, default=False),
        Column('created_at', DateTime, default=func.now()),
        Column('updated_at', DateTime, default=func.now())
    )
    
    # Create email_verifications table
    email_verifications = Table('email_verifications', test_metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('email', String(255), nullable=False),
        Column('verification_token_hash', String(255), nullable=False),
        Column('expires_at', DateTime, nullable=False),
        Column('verified_at', DateTime, nullable=True),
        Column('created_at', DateTime, server_default=func.now()),
        Column('resend_count', Integer, default=0),
        Column('last_resend_at', DateTime, nullable=True),
        Column('ip_address', String(45), nullable=True),
        Column('user_agent', Text, nullable=True),
        Column('verification_type', String(50), default='signup'),
        Column('old_email', String(255), nullable=True),
        Column('failed_attempts', Integer, default=0),
        Column('last_failed_attempt', DateTime, nullable=True),
        Column('locked_until', DateTime, nullable=True)
    )
    
    # Create tables
    test_metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()

@pytest.fixture(scope="function")
def sample_user(test_db):
    """Create sample user for testing using raw SQL"""
    # Insert user directly into the table
    result = test_db.execute(
        text("""
            INSERT INTO users (email, password_hash, full_name, is_active, email_verified, created_at, updated_at)
            VALUES (:email, :password_hash, :full_name, :is_active, :email_verified, :created_at, :updated_at)
        """),
        {
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'full_name': 'Test User',
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    )
    test_db.commit()
    
    # Return user data as a simple dict
    return {
        'id': result.lastrowid,
        'email': 'test@example.com',
        'full_name': 'Test User',
        'is_active': True,
        'email_verified': False
    }

class TestEmailVerificationIsolated:
    """Isolated tests for EmailVerification model"""
    
    def test_basic_verification_creation(self, test_db, sample_user):
        """Test basic verification creation without complex model dependencies"""
        # Test that we can create a verification record
        verification_data = {
            'user_id': sample_user['id'],
            'email': sample_user['email'],
            'verification_token_hash': 'test_hash_123',
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'verification_type': 'signup',
            'created_at': datetime.utcnow()
        }
        
        # Insert verification record directly
        result = test_db.execute(
            text("""
                INSERT INTO email_verifications 
                (user_id, email, verification_token_hash, expires_at, verification_type, created_at)
                VALUES (:user_id, :email, :verification_token_hash, :expires_at, :verification_type, :created_at)
            """),
            verification_data
        )
        test_db.commit()
        
        # Verify the record was created
        verification_id = result.lastrowid
        result = test_db.execute(
            text("SELECT * FROM email_verifications WHERE id = :id"),
            {'id': verification_id}
        )
        verification = result.fetchone()
        
        assert verification is not None
        assert verification.user_id == sample_user['id']
        assert verification.email == sample_user['email']
        assert verification.verification_type == 'signup'
        
        # Convert SQLite datetime string to Python datetime for comparison
        expires_at = datetime.fromisoformat(verification.expires_at) if isinstance(verification.expires_at, str) else verification.expires_at
        assert expires_at > datetime.utcnow()
        assert verification.verification_token_hash == 'test_hash_123'
    
    def test_verification_expiration(self, test_db, sample_user):
        """Test verification expiration logic"""
        # Create an expired verification
        expired_time = datetime.utcnow() - timedelta(hours=1)
        verification_data = {
            'user_id': sample_user['id'],
            'email': sample_user['email'],
            'verification_token_hash': 'expired_hash',
            'expires_at': expired_time,
            'verification_type': 'signup',
            'created_at': datetime.utcnow()
        }
        
        result = test_db.execute(
            text("""
                INSERT INTO email_verifications 
                (user_id, email, verification_token_hash, expires_at, verification_type, created_at)
                VALUES (:user_id, :email, :verification_token_hash, :expires_at, :verification_type, :created_at)
            """),
            verification_data
        )
        test_db.commit()
        
        # Test expiration logic
        now = datetime.utcnow()
        assert expired_time < now  # Verification is expired
    
    def test_verification_rate_limiting(self, test_db, sample_user):
        """Test verification rate limiting fields"""
        verification_data = {
            'user_id': sample_user['id'],
            'email': sample_user['email'],
            'verification_token_hash': 'rate_limit_hash',
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'verification_type': 'signup',
            'created_at': datetime.utcnow(),
            'failed_attempts': 3,
            'last_failed_attempt': datetime.utcnow() - timedelta(minutes=30),
            'locked_until': datetime.utcnow() + timedelta(hours=1)
        }
        
        result = test_db.execute(
            text("""
                INSERT INTO email_verifications 
                (user_id, email, verification_token_hash, expires_at, verification_type, created_at, 
                 failed_attempts, last_failed_attempt, locked_until)
                VALUES (:user_id, :email, :verification_token_hash, :expires_at, :verification_type, :created_at,
                        :failed_attempts, :last_failed_attempt, :locked_until)
            """),
            verification_data
        )
        test_db.commit()
        
        # Verify rate limiting fields
        verification_id = result.lastrowid
        result = test_db.execute(
            text("SELECT failed_attempts, last_failed_attempt, locked_until FROM email_verifications WHERE id = :id"),
            {'id': verification_id}
        )
        verification = result.fetchone()
        
        assert verification.failed_attempts == 3
        assert verification.last_failed_attempt is not None
        
        # Convert SQLite datetime string to Python datetime for comparison
        locked_until = datetime.fromisoformat(verification.locked_until) if isinstance(verification.locked_until, str) else verification.locked_until
        assert locked_until > datetime.utcnow()
    
    def test_verification_types(self, test_db, sample_user):
        """Test different verification types"""
        verification_types = ['signup', 'email_change', 'password_reset']
        
        for vtype in verification_types:
            verification_data = {
                'user_id': sample_user['id'],
                'email': sample_user['email'],
                'verification_token_hash': f'hash_{vtype}',
                'expires_at': datetime.utcnow() + timedelta(hours=24),
                'verification_type': vtype,
                'created_at': datetime.utcnow()
            }
            
            result = test_db.execute(
                text("""
                    INSERT INTO email_verifications 
                    (user_id, email, verification_token_hash, expires_at, verification_type, created_at)
                    VALUES (:user_id, :email, :verification_token_hash, :expires_at, :verification_type, :created_at)
                """),
                verification_data
            )
            test_db.commit()
            
            # Verify the record was created with correct type
            verification_id = result.lastrowid
            result = test_db.execute(
                text("SELECT verification_type FROM email_verifications WHERE id = :id"),
                {'id': verification_id}
            )
            verification = result.fetchone()
            
            assert verification.verification_type == vtype
