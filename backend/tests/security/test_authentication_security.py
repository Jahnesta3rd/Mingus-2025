"""
Authentication Security Validation Tests for MINGUS Financial Application
======================================================================

This module provides comprehensive authentication security testing:
1. Authentication bypass vulnerability tests
2. MFA integration with JWT system tests
3. RBAC with financial operations tests
4. Authentication failure handling tests
5. Session management security tests
6. Password security validation tests

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
from backend.auth.mfa_manager import MFAManager
from backend.auth.rbac_manager import RBACManager
from backend.auth.session_manager import SessionManager
from backend.auth.password_manager import PasswordManager
from backend.middleware.auth import require_auth
from backend.utils.auth_decorators import admin_required

class TestAuthenticationSecurity:
    """Test authentication security controls"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
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
    def mfa_manager(self, app):
        """Create MFA manager instance"""
        return MFAManager(app)
    
    @pytest.fixture
    def rbac_manager(self, app):
        """Create RBAC manager instance"""
        return RBACManager(app)
    
    @pytest.fixture
    def session_manager(self, app):
        """Create session manager instance"""
        return SessionManager(app)
    
    @pytest.fixture
    def password_manager(self, app):
        """Create password manager instance"""
        return PasswordManager(app)

class TestAuthenticationBypassPrevention:
    """Test authentication bypass prevention"""
    
    def test_no_authentication_bypass_possible(self, client):
        """Test that no authentication bypasses are possible"""
        # Test protected endpoints without authentication
        protected_endpoints = [
            '/api/payments/create',
            '/api/financial/data',
            '/api/goals/create',
            '/api/budget/update',
            '/api/subscription/create',
            '/api/billing/invoice',
            '/api/admin/users',
            '/api/compliance/audit'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require authentication"
    
    def test_invalid_jwt_token_rejection(self, client, jwt_manager):
        """Test that invalid JWT tokens are rejected"""
        invalid_tokens = [
            'invalid_token',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
            'expired_token',
            'malformed_token',
            ''
        ]
        
        for token in invalid_tokens:
            response = client.get('/api/financial/data', 
                                headers={'Authorization': f'Bearer {token}'})
            assert response.status_code in [401, 403], f"Invalid token {token} should be rejected"
    
    def test_expired_jwt_token_rejection(self, client, jwt_manager):
        """Test that expired JWT tokens are rejected"""
        # Create expired token
        expired_payload = {
            'user_id': 'test_user',
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
            'iat': int(time.time()) - 7200,  # Issued 2 hours ago
            'role': 'user'
        }
        
        expired_token = jwt.encode(expired_payload, 'test-jwt-secret', algorithm='HS256')
        
        response = client.get('/api/financial/data', 
                            headers={'Authorization': f'Bearer {expired_token}'})
        assert response.status_code in [401, 403], "Expired token should be rejected"
    
    def test_malformed_jwt_token_rejection(self, client):
        """Test that malformed JWT tokens are rejected"""
        malformed_tokens = [
            'Bearer invalid',
            'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9',
            'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature',
            'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdCJ9.invalid',
            'NotBearer token'
        ]
        
        for token in malformed_tokens:
            response = client.get('/api/financial/data', 
                                headers={'Authorization': token})
            assert response.status_code in [401, 403], f"Malformed token should be rejected: {token}"

class TestMFAIntegration:
    """Test MFA integration with JWT system"""
    
    def test_mfa_required_for_financial_operations(self, client, mfa_manager):
        """Test that MFA is required for financial operations"""
        # Mock user without MFA
        with patch('backend.auth.mfa_manager.MFAManager.is_mfa_enabled') as mock_mfa:
            mock_mfa.return_value = False
            
            # Test financial endpoints
            financial_endpoints = [
                '/api/payments/create',
                '/api/financial/data',
                '/api/goals/create',
                '/api/budget/update'
            ]
            
            for endpoint in financial_endpoints:
                response = client.post(endpoint, 
                                     headers={'Authorization': 'Bearer valid_token'},
                                     json={'data': 'test'})
                assert response.status_code in [401, 403], f"MFA should be required for {endpoint}"
    
    def test_mfa_token_validation(self, client, mfa_manager):
        """Test MFA token validation"""
        # Test valid MFA token
        with patch('backend.auth.mfa_manager.MFAManager.validate_mfa_token') as mock_validate:
            mock_validate.return_value = True
            
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': 'Bearer valid_token',
                                     'X-MFA-Token': 'valid_mfa_token'
                                 },
                                 json={'amount': 1000})
            
            assert response.status_code == 200, "Valid MFA token should be accepted"
        
        # Test invalid MFA token
        with patch('backend.auth.mfa_manager.MFAManager.validate_mfa_token') as mock_validate:
            mock_validate.return_value = False
            
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': 'Bearer valid_token',
                                     'X-MFA-Token': 'invalid_mfa_token'
                                 },
                                 json={'amount': 1000})
            
            assert response.status_code in [401, 403], "Invalid MFA token should be rejected"
    
    def test_mfa_bypass_prevention(self, client, mfa_manager):
        """Test that MFA cannot be bypassed"""
        # Test without MFA token
        response = client.post('/api/payments/create',
                             headers={'Authorization': 'Bearer valid_token'},
                             json={'amount': 1000})
        
        assert response.status_code in [401, 403], "MFA token should be required"
        
        # Test with empty MFA token
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': 'Bearer valid_token',
                                 'X-MFA-Token': ''
                             },
                             json={'amount': 1000})
        
        assert response.status_code in [401, 403], "Empty MFA token should be rejected"

class TestRBACWithFinancialOperations:
    """Test RBAC with financial operations"""
    
    def test_user_role_financial_access(self, client, rbac_manager):
        """Test user role access to financial operations"""
        # Test regular user access
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/financial/data',
                                headers={'Authorization': 'Bearer user_token'})
            
            assert response.status_code == 200, "User should have access to own financial data"
    
    def test_admin_role_financial_access(self, client, rbac_manager):
        """Test admin role access to financial operations"""
        # Test admin access to all financial data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/admin/financial/all',
                                headers={'Authorization': 'Bearer admin_token'})
            
            assert response.status_code == 200, "Admin should have access to all financial data"
    
    def test_unauthorized_financial_access(self, client, rbac_manager):
        """Test unauthorized access to financial operations"""
        # Test user trying to access another user's data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/financial/data/other_user',
                                headers={'Authorization': 'Bearer user_token'})
            
            assert response.status_code in [401, 403], "User should not access other user's data"
    
    def test_payment_processing_permissions(self, client, rbac_manager):
        """Test payment processing permissions"""
        # Test user payment processing
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.post('/api/payments/create',
                                 headers={'Authorization': 'Bearer user_token'},
                                 json={'amount': 1000})
            
            assert response.status_code == 200, "User should be able to process own payments"
        
        # Test unauthorized payment processing
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.post('/api/payments/create',
                                 headers={'Authorization': 'Bearer user_token'},
                                 json={'amount': 1000})
            
            assert response.status_code in [401, 403], "Unauthorized payment processing should be rejected"

class TestAuthenticationFailureHandling:
    """Test authentication failure handling"""
    
    def test_authentication_failure_logging(self, client):
        """Test that authentication failures are logged"""
        with patch('backend.auth.security_logger.log_security_event') as mock_log:
            response = client.get('/api/financial/data',
                                headers={'Authorization': 'Bearer invalid_token'})
            
            assert response.status_code in [401, 403]
            mock_log.assert_called()
    
    def test_authentication_failure_rate_limiting(self, client):
        """Test authentication failure rate limiting"""
        # Simulate multiple failed authentication attempts
        for i in range(10):
            response = client.get('/api/financial/data',
                                headers={'Authorization': 'Bearer invalid_token'})
            assert response.status_code in [401, 403]
        
        # Should be rate limited after multiple failures
        response = client.get('/api/financial/data',
                            headers={'Authorization': 'Bearer invalid_token'})
        assert response.status_code in [401, 403, 429]  # 429 for rate limited
    
    def test_authentication_failure_alerting(self, client):
        """Test authentication failure alerting"""
        with patch('backend.auth.security_alerting.send_security_alert') as mock_alert:
            # Simulate multiple failed attempts
            for i in range(5):
                response = client.get('/api/financial/data',
                                    headers={'Authorization': 'Bearer invalid_token'})
            
            # Should trigger security alert
            mock_alert.assert_called()

class TestSessionManagementSecurity:
    """Test session management security"""
    
    def test_session_fixation_prevention(self, client, session_manager):
        """Test session fixation prevention"""
        # Create initial session
        response1 = client.get('/api/auth/login')
        session_id_1 = response1.headers.get('Set-Cookie', '').split('sessionid=')[1].split(';')[0]
        
        # Login and verify session ID changes
        response2 = client.post('/api/auth/login',
                               json={'email': 'test@example.com', 'password': 'password'})
        session_id_2 = response2.headers.get('Set-Cookie', '').split('sessionid=')[1].split(';')[0]
        
        assert session_id_1 != session_id_2, "Session ID should change after login"
    
    def test_session_timeout(self, client, session_manager):
        """Test session timeout"""
        # Create session
        response = client.post('/api/auth/login',
                              json={'email': 'test@example.com', 'password': 'password'})
        
        # Wait for session to expire (mock time)
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() + 3600  # 1 hour later
            
            response = client.get('/api/financial/data')
            assert response.status_code in [401, 403], "Expired session should be rejected"
    
    def test_concurrent_session_handling(self, client, session_manager):
        """Test concurrent session handling"""
        # Create multiple sessions for same user
        session1 = client.post('/api/auth/login',
                              json={'email': 'test@example.com', 'password': 'password'})
        
        session2 = client.post('/api/auth/login',
                              json={'email': 'test@example.com', 'password': 'password'})
        
        # Both sessions should be valid
        assert session1.status_code == 200
        assert session2.status_code == 200

class TestPasswordSecurity:
    """Test password security"""
    
    def test_password_hashing_security(self, password_manager):
        """Test password hashing security"""
        password = 'test_password_123'
        
        # Hash password
        hashed = password_manager.hash_password(password)
        
        # Verify hash is secure
        assert hashed != password, "Password should be hashed"
        assert len(hashed) > 50, "Hash should be sufficiently long"
        assert '$' in hashed, "Hash should use proper format"
    
    def test_password_verification(self, password_manager):
        """Test password verification"""
        password = 'test_password_123'
        hashed = password_manager.hash_password(password)
        
        # Verify correct password
        assert password_manager.verify_password(password, hashed), "Correct password should verify"
        
        # Verify incorrect password
        assert not password_manager.verify_password('wrong_password', hashed), "Incorrect password should not verify"
    
    def test_password_strength_validation(self, password_manager):
        """Test password strength validation"""
        weak_passwords = [
            '123',
            'password',
            '12345678',
            'qwerty',
            'abc123'
        ]
        
        for weak_password in weak_passwords:
            assert not password_manager.validate_password_strength(weak_password), f"Weak password should be rejected: {weak_password}"
        
        strong_passwords = [
            'StrongP@ssw0rd123!',
            'MySecure#Pass2024',
            'Complex$Password99'
        ]
        
        for strong_password in strong_passwords:
            assert password_manager.validate_password_strength(strong_password), f"Strong password should be accepted: {strong_password}"

class TestAuthenticationIntegration:
    """Test authentication system integration"""
    
    def test_jwt_mfa_rbac_integration(self, client, jwt_manager, mfa_manager, rbac_manager):
        """Test JWT, MFA, and RBAC working together"""
        # Mock all components working together
        with patch('backend.auth.jwt_handler.JWTManager.validate_token') as mock_jwt:
            with patch('backend.auth.mfa_manager.MFAManager.validate_mfa_token') as mock_mfa:
                with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_rbac:
                    mock_jwt.return_value = {'user_id': 'test_user', 'role': 'user'}
                    mock_mfa.return_value = True
                    mock_rbac.return_value = True
                    
                    response = client.post('/api/payments/create',
                                         headers={
                                             'Authorization': 'Bearer valid_token',
                                             'X-MFA-Token': 'valid_mfa_token'
                                         },
                                         json={'amount': 1000})
                    
                    assert response.status_code == 200, "All authentication components should work together"
    
    def test_authentication_failure_cascade(self, client):
        """Test authentication failure cascade"""
        # Test JWT failure
        response = client.post('/api/payments/create',
                             headers={'Authorization': 'Bearer invalid_token'},
                             json={'amount': 1000})
        assert response.status_code in [401, 403], "JWT failure should block request"
        
        # Test MFA failure
        with patch('backend.auth.jwt_handler.JWTManager.validate_token') as mock_jwt:
            mock_jwt.return_value = {'user_id': 'test_user', 'role': 'user'}
            
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': 'Bearer valid_token',
                                     'X-MFA-Token': 'invalid_mfa_token'
                                 },
                                 json={'amount': 1000})
            assert response.status_code in [401, 403], "MFA failure should block request"
        
        # Test RBAC failure
        with patch('backend.auth.jwt_handler.JWTManager.validate_token') as mock_jwt:
            with patch('backend.auth.mfa_manager.MFAManager.validate_mfa_token') as mock_mfa:
                mock_jwt.return_value = {'user_id': 'test_user', 'role': 'user'}
                mock_mfa.return_value = True
                
                response = client.post('/api/payments/create',
                                     headers={
                                         'Authorization': 'Bearer valid_token',
                                         'X-MFA-Token': 'valid_mfa_token'
                                     },
                                     json={'amount': 1000})
                assert response.status_code in [401, 403], "RBAC failure should block request"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
