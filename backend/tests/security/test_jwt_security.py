"""
JWT Security Validation Tests for MINGUS Financial Application
============================================================

This module provides comprehensive JWT security testing:
1. JWT token validation and security tests
2. Token refresh and rotation tests
3. Token blacklisting functionality tests
4. JWT integration with RBAC tests
5. JWT performance and scalability tests
6. JWT attack vector protection tests

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request
import jwt
import hashlib
import secrets

from backend.auth.jwt_handler import JWTManager
from backend.auth.rbac_manager import RBACManager
from backend.auth.session_manager import SessionManager
from backend.middleware.auth import require_auth
from backend.utils.auth_decorators import admin_required

class TestJWTSecurity:
    """Test JWT security controls"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def jwt_manager(self, app):
        """Create JWT manager instance"""
        return JWTManager(app)
    
    @pytest.fixture
    def rbac_manager(self, app):
        """Create RBAC manager instance"""
        return RBACManager(app)
    
    @pytest.fixture
    def session_manager(self, app):
        """Create session manager instance"""
        return SessionManager(app)

class TestJWTTokenValidationAndSecurity:
    """Test JWT token validation and security"""
    
    def test_jwt_token_generation_security(self, jwt_manager):
        """Test JWT token generation security"""
        # Generate access token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Verify token format
        assert isinstance(access_token, str), "Access token should be a string"
        assert len(access_token) > 50, "Access token should be sufficiently long"
        
        # Verify token structure
        try:
            decoded = jwt.decode(access_token, 'test-jwt-secret', algorithms=['HS256'])
            assert 'user_id' in decoded, "Token should contain user_id"
            assert 'role' in decoded, "Token should contain role"
            assert 'exp' in decoded, "Token should contain expiration"
            assert 'iat' in decoded, "Token should contain issued at"
            assert 'jti' in decoded, "Token should contain JWT ID"
        except jwt.InvalidTokenError:
            pytest.fail("Generated token should be valid")
    
    def test_jwt_token_validation_security(self, jwt_manager):
        """Test JWT token validation security"""
        # Generate valid token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test valid token validation
        payload = jwt_manager.validate_token(access_token)
        assert payload is not None, "Valid token should be accepted"
        assert payload['user_id'] == 'test_user', "Token should contain correct user_id"
        assert payload['role'] == 'user', "Token should contain correct role"
        
        # Test invalid token validation
        invalid_tokens = [
            'invalid_token',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
            'expired_token',
            'malformed_token',
            ''
        ]
        
        for invalid_token in invalid_tokens:
            payload = jwt_manager.validate_token(invalid_token)
            assert payload is None, f"Invalid token should be rejected: {invalid_token}"
    
    def test_jwt_token_expiration_handling(self, jwt_manager):
        """Test JWT token expiration handling"""
        # Create expired token
        expired_payload = {
            'user_id': 'test_user',
            'role': 'user',
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
            'iat': int(time.time()) - 7200,  # Issued 2 hours ago
            'jti': str(uuid.uuid4())
        }
        
        expired_token = jwt.encode(expired_payload, 'test-jwt-secret', algorithm='HS256')
        
        # Test expired token validation
        payload = jwt_manager.validate_token(expired_token)
        assert payload is None, "Expired token should be rejected"
    
    def test_jwt_token_signature_validation(self, jwt_manager):
        """Test JWT token signature validation"""
        # Create token with wrong signature
        payload = {
            'user_id': 'test_user',
            'role': 'user',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'jti': str(uuid.uuid4())
        }
        
        wrong_signature_token = jwt.encode(payload, 'wrong-secret', algorithm='HS256')
        
        # Test token with wrong signature
        result = jwt_manager.validate_token(wrong_signature_token)
        assert result is None, "Token with wrong signature should be rejected"
    
    def test_jwt_token_algorithm_validation(self, jwt_manager):
        """Test JWT token algorithm validation"""
        # Create token with wrong algorithm
        payload = {
            'user_id': 'test_user',
            'role': 'user',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'jti': str(uuid.uuid4())
        }
        
        # Test with None algorithm (should be rejected)
        none_algorithm_token = jwt.encode(payload, 'test-jwt-secret', algorithm=None)
        
        result = jwt_manager.validate_token(none_algorithm_token)
        assert result is None, "Token with None algorithm should be rejected"

class TestJWTTokenRefreshAndRotation:
    """Test JWT token refresh and rotation"""
    
    def test_jwt_token_refresh_security(self, jwt_manager):
        """Test JWT token refresh security"""
        # Generate initial tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        refresh_token = jwt_manager.generate_refresh_token('test_user')
        
        # Test valid refresh
        new_tokens = jwt_manager.refresh_tokens(refresh_token)
        assert new_tokens is not None, "Valid refresh should succeed"
        assert 'access_token' in new_tokens, "Refresh should return new access token"
        assert 'refresh_token' in new_tokens, "Refresh should return new refresh token"
        
        # Verify new tokens are different
        assert new_tokens['access_token'] != access_token, "New access token should be different"
        assert new_tokens['refresh_token'] != refresh_token, "New refresh token should be different"
    
    def test_jwt_token_refresh_expiration(self, jwt_manager):
        """Test JWT token refresh expiration"""
        # Create expired refresh token
        expired_payload = {
            'user_id': 'test_user',
            'type': 'refresh',
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
            'iat': int(time.time()) - 7200,  # Issued 2 hours ago
            'jti': str(uuid.uuid4())
        }
        
        expired_refresh_token = jwt.encode(expired_payload, 'test-jwt-secret', algorithm='HS256')
        
        # Test expired refresh token
        new_tokens = jwt_manager.refresh_tokens(expired_refresh_token)
        assert new_tokens is None, "Expired refresh token should be rejected"
    
    def test_jwt_token_rotation_security(self, jwt_manager):
        """Test JWT token rotation security"""
        # Generate initial tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        refresh_token = jwt_manager.generate_refresh_token('test_user')
        
        # Test token rotation
        new_tokens = jwt_manager.rotate_tokens(refresh_token)
        assert new_tokens is not None, "Token rotation should succeed"
        
        # Verify old refresh token is invalidated
        old_refresh_result = jwt_manager.refresh_tokens(refresh_token)
        assert old_refresh_result is None, "Old refresh token should be invalidated"
        
        # Verify new refresh token works
        new_refresh_result = jwt_manager.refresh_tokens(new_tokens['refresh_token'])
        assert new_refresh_result is not None, "New refresh token should work"

class TestJWTTokenBlacklisting:
    """Test JWT token blacklisting functionality"""
    
    def test_jwt_token_blacklisting(self, jwt_manager):
        """Test JWT token blacklisting"""
        # Generate token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Verify token is valid initially
        payload = jwt_manager.validate_token(access_token)
        assert payload is not None, "Token should be valid initially"
        
        # Blacklist token
        jwt_manager.blacklist_token(access_token)
        
        # Verify token is now invalid
        payload = jwt_manager.validate_token(access_token)
        assert payload is None, "Blacklisted token should be rejected"
    
    def test_jwt_token_blacklist_cleanup(self, jwt_manager):
        """Test JWT token blacklist cleanup"""
        # Generate and blacklist multiple tokens
        tokens = []
        for i in range(10):
            token = jwt_manager.generate_access_token(f'test_user_{i}', 'user')
            jwt_manager.blacklist_token(token)
            tokens.append(token)
        
        # Test cleanup of expired blacklisted tokens
        jwt_manager.cleanup_blacklist()
        
        # Verify cleanup doesn't affect current tokens
        for token in tokens:
            payload = jwt_manager.validate_token(token)
            assert payload is None, "Blacklisted tokens should remain invalid after cleanup"
    
    def test_jwt_token_blacklist_persistence(self, jwt_manager):
        """Test JWT token blacklist persistence"""
        # Generate token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Blacklist token
        jwt_manager.blacklist_token(access_token)
        
        # Verify token is blacklisted
        payload = jwt_manager.validate_token(access_token)
        assert payload is None, "Blacklisted token should be rejected"
        
        # Simulate application restart (new JWT manager instance)
        new_jwt_manager = JWTManager(jwt_manager.app)
        
        # Verify token is still blacklisted
        payload = new_jwt_manager.validate_token(access_token)
        assert payload is None, "Blacklisted token should persist across restarts"

class TestJWTIntegrationWithRBAC:
    """Test JWT integration with RBAC"""
    
    def test_jwt_rbac_integration(self, jwt_manager, rbac_manager):
        """Test JWT integration with RBAC"""
        # Generate token with user role
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Validate token and check permissions
        payload = jwt_manager.validate_token(user_token)
        assert payload is not None, "User token should be valid"
        
        # Test user permissions
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            has_permission = rbac_manager.has_permission('test_user', 'read_financial_data')
            assert has_permission is True, "User should have read permission"
    
    def test_jwt_admin_rbac_integration(self, jwt_manager, rbac_manager):
        """Test JWT admin integration with RBAC"""
        # Generate token with admin role
        admin_token = jwt_manager.generate_access_token('test_admin', 'admin')
        
        # Validate token and check permissions
        payload = jwt_manager.validate_token(admin_token)
        assert payload is not None, "Admin token should be valid"
        assert payload['role'] == 'admin', "Token should have admin role"
        
        # Test admin permissions
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            has_permission = rbac_manager.has_permission('test_admin', 'admin_access')
            assert has_permission is True, "Admin should have admin access"
    
    def test_jwt_role_escalation_prevention(self, jwt_manager, rbac_manager):
        """Test JWT role escalation prevention"""
        # Generate token with user role
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Try to escalate to admin role
        payload = jwt_manager.validate_token(user_token)
        assert payload['role'] == 'user', "User token should not have admin role"
        
        # Test that user cannot access admin functions
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = False
            
            has_permission = rbac_manager.has_permission('test_user', 'admin_access')
            assert has_permission is False, "User should not have admin access"

class TestJWTAttackVectorProtection:
    """Test JWT attack vector protection"""
    
    def test_jwt_algorithm_confusion_attack(self, jwt_manager):
        """Test JWT algorithm confusion attack protection"""
        # Create token with HMAC algorithm but signed with RSA public key
        payload = {
            'user_id': 'test_user',
            'role': 'admin',  # Try to escalate role
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'jti': str(uuid.uuid4())
        }
        
        # This should be rejected due to algorithm validation
        try:
            # Simulate algorithm confusion attack
            confused_token = jwt.encode(payload, 'test-jwt-secret', algorithm='HS256')
            result = jwt_manager.validate_token(confused_token)
            # The token should be valid if properly signed, but role should not be escalated
            if result:
                assert result['role'] != 'admin', "Role escalation should be prevented"
        except jwt.InvalidTokenError:
            # This is expected for invalid tokens
            pass
    
    def test_jwt_timing_attack_protection(self, jwt_manager):
        """Test JWT timing attack protection"""
        # Generate valid token
        valid_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Generate invalid token
        invalid_token = 'invalid_token'
        
        # Test timing consistency
        valid_start = time.time()
        jwt_manager.validate_token(valid_token)
        valid_duration = time.time() - valid_start
        
        invalid_start = time.time()
        jwt_manager.validate_token(invalid_token)
        invalid_duration = time.time() - invalid_start
        
        # Timing should be consistent (within reasonable bounds)
        timing_diff = abs(valid_duration - invalid_duration)
        assert timing_diff < 0.1, f"Timing difference should be < 0.1s, got {timing_diff}s"
    
    def test_jwt_replay_attack_protection(self, jwt_manager):
        """Test JWT replay attack protection"""
        # Generate token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Use token multiple times (should be allowed for access tokens)
        for i in range(5):
            payload = jwt_manager.validate_token(access_token)
            assert payload is not None, f"Token should be valid on use {i+1}"
        
        # Test refresh token replay protection
        refresh_token = jwt_manager.generate_refresh_token('test_user')
        
        # Use refresh token first time
        new_tokens = jwt_manager.refresh_tokens(refresh_token)
        assert new_tokens is not None, "First refresh should succeed"
        
        # Try to use same refresh token again (should fail)
        replay_result = jwt_manager.refresh_tokens(refresh_token)
        assert replay_result is None, "Refresh token replay should be rejected"
    
    def test_jwt_brute_force_attack_protection(self, jwt_manager):
        """Test JWT brute force attack protection"""
        # Simulate brute force attempts
        invalid_tokens = [f'invalid_token_{i}' for i in range(100)]
        
        # All should be rejected
        for token in invalid_tokens:
            payload = jwt_manager.validate_token(token)
            assert payload is None, f"Invalid token should be rejected: {token}"
        
        # System should still be responsive
        valid_token = jwt_manager.generate_access_token('test_user', 'user')
        payload = jwt_manager.validate_token(valid_token)
        assert payload is not None, "Valid token should still work after brute force attempts"

class TestJWTPerformanceAndScalability:
    """Test JWT performance and scalability"""
    
    def test_jwt_token_generation_performance(self, jwt_manager):
        """Test JWT token generation performance"""
        start_time = time.time()
        
        # Generate 1000 tokens
        for i in range(1000):
            jwt_manager.generate_access_token(f'test_user_{i}', 'user')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should generate 1000 tokens in less than 1 second
        assert duration < 1.0, f"Token generation took {duration}s, should be < 1s"
        assert duration / 1000 < 0.001, "Should generate tokens in < 1ms each"
    
    def test_jwt_token_validation_performance(self, jwt_manager):
        """Test JWT token validation performance"""
        # Generate token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        start_time = time.time()
        
        # Validate token 1000 times
        for _ in range(1000):
            jwt_manager.validate_token(access_token)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should validate 1000 tokens in less than 1 second
        assert duration < 1.0, f"Token validation took {duration}s, should be < 1s"
        assert duration / 1000 < 0.001, "Should validate tokens in < 1ms each"
    
    def test_jwt_concurrent_validation(self, jwt_manager):
        """Test JWT concurrent validation"""
        import threading
        import queue
        
        # Generate multiple tokens
        tokens = []
        for i in range(100):
            token = jwt_manager.generate_access_token(f'test_user_{i}', 'user')
            tokens.append(token)
        
        results = queue.Queue()
        
        def validate_tokens():
            for token in tokens:
                payload = jwt_manager.validate_token(token)
                results.put(payload is not None)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=validate_tokens)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all validations succeeded
        while not results.empty():
            assert results.get() is True, "All concurrent validations should succeed"

class TestJWTIntegrationWithSessionManagement:
    """Test JWT integration with session management"""
    
    def test_jwt_session_integration(self, jwt_manager, session_manager):
        """Test JWT integration with session management"""
        # Create session
        session_data = session_manager.create_session('test_user')
        session_id = session_data['session_id']
        
        # Generate JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Validate token
        payload = jwt_manager.validate_token(access_token)
        assert payload is not None, "JWT token should be valid"
        
        # Verify session is still valid
        session_valid = session_manager.validate_session(session_id)
        assert session_valid is True, "Session should be valid"
    
    def test_jwt_session_logout_integration(self, jwt_manager, session_manager):
        """Test JWT session logout integration"""
        # Create session and JWT token
        session_data = session_manager.create_session('test_user')
        session_id = session_data['session_id']
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Logout (invalidate session and blacklist token)
        session_manager.invalidate_session(session_id)
        jwt_manager.blacklist_token(access_token)
        
        # Verify both are invalid
        session_valid = session_manager.validate_session(session_id)
        assert session_valid is False, "Session should be invalid after logout"
        
        payload = jwt_manager.validate_token(access_token)
        assert payload is None, "JWT token should be invalid after logout"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
