#!/usr/bin/env python3
"""
Comprehensive Tests for Enhanced Security System
Tests JWT security, brute force protection, and session management
"""

import pytest
import time
import jwt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask, request, g

# Import security components
from backend.security.secure_jwt_manager import SecureJWTManager, JWTConfig
from backend.security.brute_force_protection import BruteForceProtection, BruteForceConfig
from backend.security.secure_session_manager import SecureSessionManager, SessionConfig
from backend.middleware.enhanced_auth import require_auth, require_assessment_auth
from backend.config.security_config import SecurityConfig

@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['REDIS_HOST'] = 'localhost'
    app.config['REDIS_PORT'] = 6379
    
    with app.app_context():
        yield app

@pytest.fixture
def jwt_config():
    """Create JWT configuration for testing"""
    return JWTConfig(
        secret_key='test-secret-key',
        algorithm='HS256',
        expiration_hours=1,
        issuer='mingus-app',
        audience='mingus-users',
        require_ip_validation=True,
        require_user_agent_validation=True
    )

@pytest.fixture
def brute_force_config():
    """Create brute force configuration for testing"""
    return BruteForceConfig(
        max_login_attempts=3,
        login_lockout_duration=60,
        login_window_size=300,
        max_assessment_attempts=5,
        assessment_lockout_duration=120,
        assessment_window_size=600,
        progressive_lockout_enabled=True,
        redis_host='localhost',
        redis_port=6379,
        redis_db=1
    )

@pytest.fixture
def session_config():
    """Create session configuration for testing"""
    return SessionConfig(
        session_timeout=3600,
        session_refresh_threshold=300,
        require_ip_validation=True,
        require_user_agent_validation=True,
        redis_host='localhost',
        redis_port=6379,
        redis_db=2
    )

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('redis.Redis') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 0
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.incr.return_value = 1
        mock_client.expire.return_value = True
        mock_client.ttl.return_value = -1
        mock_client.sadd.return_value = 1
        mock_client.smembers.return_value = set()
        mock_client.scard.return_value = 0
        mock_client.srem.return_value = 1
        mock_client.keys.return_value = []
        yield mock_client

@pytest.fixture
def jwt_manager(jwt_config, mock_redis):
    """Create JWT manager for testing"""
    with patch('backend.security.secure_jwt_manager.current_app') as mock_app:
        mock_app.config = {'JWT_SECRET_KEY': 'test-secret-key'}
        return SecureJWTManager(jwt_config)

@pytest.fixture
def brute_force_protection(brute_force_config, mock_redis):
    """Create brute force protection for testing"""
    return BruteForceProtection(brute_force_config)

@pytest.fixture
def session_manager(session_config, mock_redis):
    """Create session manager for testing"""
    with patch('backend.security.secure_session_manager.current_app') as mock_app:
        mock_app.config = {'JWT_SECRET_KEY': 'test-secret-key'}
        return SecureSessionManager(session_config, 'test-secret-key')

class TestSecureJWTManager:
    """Test secure JWT manager functionality"""
    
    def test_create_secure_token(self, jwt_manager):
        """Test creating a secure JWT token"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            token = jwt_manager.create_secure_token('test-user-id')
            
            assert token is not None
            assert isinstance(token, str)
            
            # Decode token to verify payload
            payload = jwt.decode(token, jwt_manager.config.secret_key, algorithms=['HS256'])
            assert payload['sub'] == 'test-user-id'
            assert payload['iss'] == 'mingus-app'
            assert payload['aud'] == 'mingus-users'
            assert 'jti' in payload
            assert payload['ip'] == '127.0.0.1'
            assert 'user_agent_hash' in payload
    
    def test_validate_secure_token_success(self, jwt_manager):
        """Test successful token validation"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create token
            token = jwt_manager.create_secure_token('test-user-id')
            
            # Validate token
            result = jwt_manager.validate_secure_token(token)
            
            assert result['valid'] is True
            assert result['payload']['sub'] == 'test-user-id'
    
    def test_validate_secure_token_ip_mismatch(self, jwt_manager):
        """Test token validation with IP mismatch"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create token
            token = jwt_manager.create_secure_token('test-user-id')
            
            # Change IP address
            mock_request.remote_addr = '192.168.1.1'
            
            # Validate token
            result = jwt_manager.validate_secure_token(token)
            
            assert result['valid'] is False
            assert result['reason'] == 'IP address mismatch'
    
    def test_validate_secure_token_user_agent_mismatch(self, jwt_manager):
        """Test token validation with user agent mismatch"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create token
            token = jwt_manager.create_secure_token('test-user-id')
            
            # Change user agent
            mock_request.headers.get.return_value = 'different-user-agent'
            
            # Validate token
            result = jwt_manager.validate_secure_token(token)
            
            assert result['valid'] is False
            assert result['reason'] == 'User agent mismatch'
    
    def test_validate_secure_token_expired(self, jwt_manager):
        """Test token validation with expired token"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create token with short expiration
            jwt_manager.config.expiration_hours = 0.0001  # Very short expiration
            token = jwt_manager.create_secure_token('test-user-id')
            
            # Wait for token to expire
            time.sleep(0.1)
            
            # Validate token
            result = jwt_manager.validate_secure_token(token)
            
            assert result['valid'] is False
            assert result['reason'] == 'Token expired'
    
    def test_revoke_token(self, jwt_manager):
        """Test token revocation"""
        with patch('backend.security.secure_jwt_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create token
            token = jwt_manager.create_secure_token('test-user-id')
            
            # Revoke token
            result = jwt_manager.revoke_token(token)
            
            assert result is True
            
            # Try to validate revoked token
            validation_result = jwt_manager.validate_secure_token(token)
            assert validation_result['valid'] is False
            assert validation_result['reason'] == 'Token revoked'

class TestBruteForceProtection:
    """Test brute force protection functionality"""
    
    def test_record_failed_attempt(self, brute_force_protection, mock_redis):
        """Test recording failed login attempts"""
        mock_redis.incr.return_value = 1
        mock_redis.get.return_value = '0'
        
        result = brute_force_protection.record_failed_attempt('test@example.com', 'login')
        
        assert result['locked'] is False
        assert result['attempts'] == 1
        assert result['remaining_attempts'] == 2
    
    def test_account_lockout(self, brute_force_protection, mock_redis):
        """Test account lockout after multiple failed attempts"""
        # Simulate multiple failed attempts
        mock_redis.incr.side_effect = [1, 2, 3]
        mock_redis.get.return_value = '2'
        
        # Record failed attempts
        for i in range(3):
            result = brute_force_protection.record_failed_attempt('test@example.com', 'login')
        
        # Check if account is locked
        assert result['locked'] is True
        assert result['attempts'] == 3
        assert 'lockout_duration' in result
    
    def test_is_locked_out(self, brute_force_protection, mock_redis):
        """Test checking if account is locked out"""
        mock_redis.exists.return_value = 1
        
        is_locked = brute_force_protection.is_locked_out('test@example.com', 'login')
        
        assert is_locked is True
    
    def test_record_successful_attempt(self, brute_force_protection, mock_redis):
        """Test recording successful login attempt"""
        mock_redis.delete.return_value = 2
        
        brute_force_protection.record_successful_attempt('test@example.com', 'login')
        
        # Verify that Redis delete was called
        assert mock_redis.delete.called
    
    def test_assessment_submission_protection(self, brute_force_protection, mock_redis):
        """Test assessment submission protection"""
        mock_redis.exists.return_value = 0
        mock_redis.get.return_value = '0'
        
        result = brute_force_protection.check_assessment_submission_protection('user123', 'assessment456')
        
        assert result['allowed'] is True
        assert result['attempts'] == 0

class TestSecureSessionManager:
    """Test secure session manager functionality"""
    
    def test_create_secure_session(self, session_manager, mock_redis):
        """Test creating a secure session"""
        with patch('backend.security.secure_session_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            session_id = session_manager.create_secure_session('test-user-id', 'test-token')
            
            assert session_id is not None
            assert isinstance(session_id, str)
    
    def test_validate_session_success(self, session_manager, mock_redis):
        """Test successful session validation"""
        with patch('backend.security.secure_session_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create session
            session_id = session_manager.create_secure_session('test-user-id', 'test-token')
            
            # Mock session data in Redis
            session_data = {
                'session_id': session_id,
                'user_id': 'test-user-id',
                'created_at': time.time(),
                'last_activity': time.time(),
                'expires_at': time.time() + 3600,
                'ip_address': '127.0.0.1',
                'user_agent': 'test-user-agent',
                'user_agent_hash': session_manager._hash_user_agent('test-user-agent'),
                'is_active': True,
                'remember_me': False,
                'token': 'test-token',
                'metadata': {}
            }
            
            mock_redis.get.return_value = session_manager._session_to_json(session_data)
            
            # Validate session
            result = session_manager.validate_session(session_id)
            
            assert result['valid'] is True
            assert result['session_data']['user_id'] == 'test-user-id'
    
    def test_validate_session_ip_mismatch(self, session_manager, mock_redis):
        """Test session validation with IP mismatch"""
        with patch('backend.security.secure_session_manager.request') as mock_request:
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-user-agent'
            
            # Create session
            session_id = session_manager.create_secure_session('test-user-id', 'test-token')
            
            # Mock session data with different IP
            session_data = {
                'session_id': session_id,
                'user_id': 'test-user-id',
                'created_at': time.time(),
                'last_activity': time.time(),
                'expires_at': time.time() + 3600,
                'ip_address': '192.168.1.1',  # Different IP
                'user_agent': 'test-user-agent',
                'user_agent_hash': session_manager._hash_user_agent('test-user-agent'),
                'is_active': True,
                'remember_me': False,
                'token': 'test-token',
                'metadata': {}
            }
            
            mock_redis.get.return_value = session_manager._session_to_json(session_data)
            
            # Validate session
            result = session_manager.validate_session(session_id)
            
            assert result['valid'] is False
            assert result['reason'] == 'IP address mismatch'

class TestEnhancedAuthentication:
    """Test enhanced authentication middleware"""
    
    def test_require_auth_decorator(self, app):
        """Test require_auth decorator"""
        with app.test_request_context('/test', headers={'Authorization': 'Bearer invalid-token'}):
            @require_auth
            def protected_route():
                return "success"
            
            # Test with invalid token
            result = protected_route()
            assert result.status_code == 401
    
    def test_require_assessment_auth_decorator(self, app):
        """Test require_assessment_auth decorator"""
        with app.test_request_context('/test', 
                                    headers={'Authorization': 'Bearer invalid-token'},
                                    json={'assessment_id': 'test-assessment'}):
            @require_assessment_auth
            def protected_assessment_route():
                return "success"
            
            # Test with invalid token
            result = protected_assessment_route()
            assert result.status_code == 401

class TestSecurityConfiguration:
    """Test security configuration"""
    
    def test_security_config_validation(self):
        """Test security configuration validation"""
        issues = SecurityConfig.validate_config()
        
        # Should have at least one issue (JWT secret)
        assert len(issues) > 0
        assert any("JWT_SECRET_KEY" in issue for issue in issues)
    
    def test_environment_specific_configs(self):
        """Test environment-specific configurations"""
        from backend.config.security_config import get_security_config
        
        # Test development config
        dev_config = get_security_config('development')
        assert dev_config.JWT_SECRET_KEY == 'dev-secret-key-change-in-production'
        assert dev_config.MFA_ENABLED is False
        
        # Test production config
        prod_config = get_security_config('production')
        assert prod_config.MFA_ENABLED is True
        assert prod_config.SUSPICIOUS_ACTIVITY_DETECTION is True
        
        # Test testing config
        test_config = get_security_config('testing')
        assert test_config.JWT_SECRET_KEY == 'test-secret-key'
        assert test_config.ACTIVITY_LOGGING is False

if __name__ == '__main__':
    pytest.main([__file__])
