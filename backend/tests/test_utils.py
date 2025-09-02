"""
Test Utilities for MINGUS
Provides PostgreSQL type compatibility and test helpers
"""

import os
import sys
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def mock_postgresql_types():
    """
    Mock PostgreSQL-specific types for SQLite testing
    """
    # Mock JSONB type
    class MockJSONB:
        def __init__(self, *args, **kwargs):
            pass
        
        def __repr__(self):
            return 'JSONB()'
    
    # Mock UUID type
    class MockUUID:
        def __init__(self, *args, **kwargs):
            pass
        
        def __repr__(self):
            return 'UUID()'
    
    # Mock TIMESTAMP type
    class MockTIMESTAMP:
        def __init__(self, *args, **kwargs):
            pass
        
        def __repr__(self):
            return 'TIMESTAMP()'
    
    return MockJSONB, MockUUID, MockTIMESTAMP

def create_test_user_data():
    """Create test user data for email verification testing"""
    return {
        'id': 1,
        'email': 'test@example.com',
        'full_name': 'Test User',
        'password_hash': 'hashed_password',
        'email_verified': False,
        'created_at': datetime.utcnow()
    }

def create_test_verification_data():
    """Create test verification data for email verification testing"""
    return {
        'user_id': 1,
        'email': 'test@example.com',
        'verification_type': 'signup',
        'expires_at': datetime.utcnow() + timedelta(hours=24),
        'ip_address': '127.0.0.1',
        'user_agent': 'Test Browser'
    }

def mock_database_session():
    """Mock database session for testing"""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()
    mock_session.query = Mock()
    return mock_session

def mock_email_service():
    """Mock email service for testing"""
    mock_service = Mock()
    mock_service.send_verification_email.return_value = {
        'success': True,
        'message_id': 'msg_test_123',
        'delivered_at': datetime.utcnow()
    }
    mock_service.send_email_change_verification.return_value = {
        'success': True,
        'message_id': 'msg_test_456',
        'delivered_at': datetime.utcnow()
    }
    return mock_service
