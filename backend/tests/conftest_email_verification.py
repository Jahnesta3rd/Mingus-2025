"""
Email Verification Test Configuration
Provides fixtures and configuration for comprehensive email verification testing
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Any, Generator

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Import models and services
from models.email_verification import EmailVerification
from models.user import User
from models.audit import AuditLog
from services.email_verification_service import EmailVerificationService
from services.resend_email_service import ResendEmailService

# Test configuration
@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'MAIL_SUPPRESS_SEND': True,
        'STRIPE_TEST_MODE': True,
        'CELERY_ALWAYS_EAGER': True,
        'CACHE_TYPE': 'simple',
        'REDIS_URL': 'redis://localhost:6379/1',
        'EMAIL_VERIFICATION_EXPIRY_HOURS': '24',
        'MAX_EMAIL_RESEND_ATTEMPTS': '5',
        'EMAIL_RESEND_COOLDOWN_HOURS': '1',
        'EMAIL_VERIFICATION_SECRET': 'test-verification-secret'
    })
    
    # Initialize extensions
    db = SQLAlchemy(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

@pytest.fixture(scope="function")
def db_session(app):
    """Database session fixture"""
    from ..database import db
    
    with app.app_context():
        # Create a new session for each test
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create a session factory bound to this connection
        session_factory = db.session.session_factory
        session = session_factory(bind=connection)
        
        yield session
        
        # Rollback and close
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def mock_email_service():
    """Mock email service with comprehensive responses"""
    with patch('backend.services.email_verification_service.ResendEmailService') as mock:
        service = mock.return_value
        service.send_verification_email.return_value = {
            'success': True,
            'message_id': 'msg_test_123',
            'delivered_at': datetime.utcnow()
        }
        service.send_email_change_verification.return_value = {
            'success': True,
            'message_id': 'msg_test_456',
            'delivered_at': datetime.utcnow()
        }
        service.send_verification_reminder.return_value = {
            'success': True,
            'message_id': 'msg_test_789',
            'delivered_at': datetime.utcnow()
        }
        yield service

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for rate limiting tests"""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        yield mock_redis

@pytest.fixture(scope="function")
def mock_metrics():
    """Mock metrics collection service"""
    with patch('backend.services.email_verification_service.metrics_client') as mock:
        mock.increment.return_value = None
        mock.timing.return_value = None
        mock.gauge.return_value = None
        yield mock

@pytest.fixture(scope="function")
def mock_audit():
    """Mock audit logging service"""
    with patch('backend.services.email_verification_service.audit_service') as mock:
        mock.log_event.return_value = True
        mock.record_user_action.return_value = True
        yield mock

@pytest.fixture(scope="function")
def mock_notification():
    """Mock notification service"""
    with patch('backend.services.email_verification_service.notification_service') as mock:
        mock.send_rate_limit_notification.return_value = True
        mock.send_security_alert.return_value = True
        yield mock

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create test user"""
    user = User(
        id='test_user_123',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        subscription_tier='basic',
        created_at=datetime.utcnow(),
        is_active=True,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_verification(db_session, test_user):
    """Create test verification"""
    verification = EmailVerification(
        user_id=test_user.id,
        email=test_user.email,
        verification_token_hash='test_hash_123',
        expires_at=datetime.utcnow() + timedelta(hours=24),
        verification_type='signup',
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()
    return verification

@pytest.fixture(scope="function")
def test_data_factory():
    """Factory for generating test data"""
    def create_test_user(user_id, email, **kwargs):
        return User(
            id=user_id,
            email=email,
            first_name=f'Test{user_id}',
            last_name=f'User{user_id}',
            subscription_tier=kwargs.get('subscription_tier', 'basic'),
            created_at=kwargs.get('created_at', datetime.utcnow()),
            is_active=kwargs.get('is_active', True),
            email_verified=kwargs.get('email_verified', False)
        )
    
    def create_test_verification(user_id, email, **kwargs):
        return EmailVerification(
            user_id=user_id,
            email=email,
            verification_token_hash=f'hash_{user_id}',
            expires_at=kwargs.get('expires_at', datetime.utcnow() + timedelta(hours=24)),
            verification_type=kwargs.get('verification_type', 'signup'),
            created_at=kwargs.get('created_at', datetime.utcnow()),
            old_email=kwargs.get('old_email', None),
            ip_address=kwargs.get('ip_address', None),
            user_agent=kwargs.get('user_agent', None)
        )
    
    return {
        'create_user': create_test_user,
        'create_verification': create_test_verification
    }

@pytest.fixture(scope="function")
def mock_celery():
    """Mock Celery tasks"""
    with patch('backend.celery_app.celery.send_task') as mock_send_task:
        mock_send_task.return_value = Mock(id='task_123')
        yield mock_send_task

@pytest.fixture(scope="function")
def test_client(app):
    """Test client fixture"""
    return app.test_client()

@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Authentication headers fixture"""
    return {
        'Authorization': f'Bearer test_token_{test_user.id}',
        'Content-Type': 'application/json'
    }

# Performance testing fixtures
@pytest.fixture(scope="function")
def load_test_data():
    """Generate load test data"""
    return {
        'concurrent_users': 100,
        'requests_per_user': 10,
        'test_duration': 300,  # 5 minutes
        'ramp_up_time': 60,    # 1 minute
        'target_response_time': 2000  # 2 seconds
    }

# Security testing fixtures
@pytest.fixture(scope="function")
def malicious_inputs():
    """Malicious input data for security testing"""
    return {
        'sql_injection': [
            "'; DROP TABLE users; --",
            "' OR 1=1; --",
            "'; SELECT * FROM users WHERE id=1; --"
        ],
        'xss': [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src="x" onerror="alert(\'xss\')">'
        ],
        'template_injection': [
            '{{ 7 * 7 }}',
            '{{ config.items() }}',
            '{{ request.environ }}'
        ],
        'path_traversal': [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd'
        ]
    }

@pytest.fixture(scope="function")
def rate_limit_scenarios():
    """Rate limiting test scenarios"""
    return {
        'normal_user': {
            'requests_per_minute': 5,
            'burst_limit': 10,
            'expected_result': 'allowed'
        },
        'suspicious_user': {
            'requests_per_minute': 50,
            'burst_limit': 100,
            'expected_result': 'rate_limited'
        },
        'malicious_user': {
            'requests_per_minute': 500,
            'burst_limit': 1000,
            'expected_result': 'blocked'
        }
    }

# Email template testing fixtures
@pytest.fixture(scope="function")
def email_templates():
    """Sample email templates for testing"""
    return {
        'verification': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verify Your Email</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>Please verify your email address by clicking the link below:</p>
            <a href="{{ verification_url }}">Verify Email</a>
            <p>This link will expire in {{ expiry_hours }} hours.</p>
        </body>
        </html>
        """,
        'email_change': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Confirm Email Change</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>You requested to change your email address to: {{ new_email }}</p>
            <p>Please confirm this change by clicking the link below:</p>
            <a href="{{ verification_url }}">Confirm Email Change</a>
        </body>
        </html>
        """
    }

@pytest.fixture(scope="function")
def test_emails():
    """Test email addresses for various scenarios"""
    return {
        'valid': [
            'test@example.com',
            'user.name@domain.co.uk',
            'test+tag@example.org',
            '123@numbers.com'
        ],
        'invalid': [
            'invalid-email',
            '@example.com',
            'test@',
            'test@.com',
            'test..test@example.com'
        ],
        'edge_cases': [
            'a@b.c',  # Minimal valid email
            'test@example.com' + 'a' * 100,  # Very long
            'test@' + 'a' * 64 + '.com',  # Long domain
            'test' + 'a' * 64 + '@example.com'  # Long local part
        ]
    }

# Database testing fixtures
@pytest.fixture(scope="function")
def temp_db_file():
    """Create temporary database file for migration testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture(scope="function")
def test_db_engine(temp_db_file):
    """Create test database engine"""
    from sqlalchemy import create_engine
    engine = create_engine(f'sqlite:///{temp_db_file}')
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()

# Integration testing fixtures
@pytest.fixture(scope="function")
def mock_external_services():
    """Mock all external services"""
    with patch('backend.services.email_verification_service.ResendEmailService') as mock_resend, \
         patch('backend.services.email_verification_service.redis_client') as mock_redis, \
         patch('backend.services.email_verification_service.metrics_client') as mock_metrics:
        
        # Configure mock responses
        mock_resend.return_value.send_verification_email.return_value = {
            'success': True, 'message_id': 'msg_123'
        }
        mock_redis.incr.return_value = 1
        mock_redis.get.return_value = None
        mock_metrics.increment.return_value = None
        
        yield {
            'resend': mock_resend,
            'redis': mock_redis,
            'metrics': mock_metrics
        }

# Test data generators
def generate_test_users(count: int = 10) -> List[Dict[str, Any]]:
    """Generate test user data"""
    users = []
    for i in range(count):
        users.append({
            'id': f'test_user_{i}',
            'email': f'test{i}@example.com',
            'first_name': f'Test{i}',
            'last_name': f'User{i}',
            'subscription_tier': 'basic' if i % 3 == 0 else 'premium' if i % 3 == 1 else 'enterprise',
            'created_at': datetime.utcnow() - timedelta(days=i),
            'email_verified': i % 2 == 0
        })
    return users

def generate_test_verifications(count: int = 50) -> List[Dict[str, Any]]:
    """Generate test verification data"""
    verification_types = ['signup', 'email_change', 'password_reset']
    
    verifications = []
    for i in range(count):
        verifications.append({
            'id': i + 1,
            'user_id': f'test_user_{i % 10}',
            'email': f'test{i}@example.com',
            'verification_token_hash': f'hash_{i}',
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'verification_type': verification_types[i % len(verification_types)],
            'created_at': datetime.utcnow() - timedelta(hours=i),
            'verified_at': datetime.utcnow() if i % 3 == 0 else None,
            'resend_count': i % 6,
            'failed_attempts': i % 5
        })
    return verifications

# Fixture for test data
@pytest.fixture(scope="session")
def test_data():
    """Comprehensive test data fixture"""
    return {
        'users': generate_test_users(100),
        'verifications': generate_test_verifications(500)
    }

# Markers for test categorization
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "rate_limiting: marks tests as rate limiting tests"
    )
    config.addinivalue_line(
        "markers", "templates: marks tests as template tests"
    )
    config.addinivalue_line(
        "markers", "migrations: marks tests as migration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if 'test_email_verification_comprehensive' in item.nodeid:
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.integration)
        elif 'test_email_verification_rate_limiting' in item.nodeid:
            item.add_marker(pytest.mark.rate_limiting)
            item.add_marker(pytest.mark.security)
        elif 'test_email_verification_templates' in item.nodeid:
            item.add_marker(pytest.mark.templates)
            item.add_marker(pytest.mark.security)
        elif 'test_email_verification_migrations' in item.nodeid:
            item.add_marker(pytest.mark.migrations)
            item.add_marker(pytest.mark.performance)
        
        # Add markers based on test class names
        if 'TestEmailVerificationPerformance' in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif 'TestEmailVerificationSecurity' in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif 'TestEmailVerificationIntegration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif 'TestEmailVerificationModel' in item.nodeid:
            item.add_marker(pytest.mark.unit)
