"""
Authentication Integration Tests
Comprehensive tests for authentication API endpoints and frontend integration
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

class TestAuthIntegration:
    """Test authentication integration between frontend and backend"""
    
    def test_user_registration_success(self, client, test_validation_schemas):
        """Test successful user registration"""
        registration_data = test_validation_schemas['user_registration']
        
        response = client.post('/api/v1/auth/register', 
                             json=registration_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Verify response structure
        assert data['success'] == True
        assert data['message'] == 'User registered successfully'
        assert 'data' in data
        assert 'user' in data['data']
        assert 'tokens' in data['data']
        
        # Verify user data
        user_data = data['data']['user']
        assert user_data['email'] == registration_data['email']
        assert user_data['full_name'] == registration_data['full_name']
        assert 'id' in user_data
        assert 'created_at' in user_data
        
        # Verify tokens
        tokens = data['data']['tokens']
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'expires_in' in tokens
        assert tokens['expires_in'] == 3600
    
    def test_user_registration_validation_errors(self, client):
        """Test user registration with validation errors"""
        invalid_data = {
            'email': 'invalid-email',
            'password': 'weak',
            'full_name': ''
        }
        
        response = client.post('/api/v1/auth/register',
                             json=invalid_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        assert 'validation_errors' in data['details']
        
        # Check specific validation errors
        errors = data['details']['validation_errors']
        error_fields = [error['field'] for error in errors]
        assert 'email' in error_fields
        assert 'password' in error_fields
        assert 'full_name' in error_fields
    
    def test_user_registration_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        duplicate_data = {
            'email': test_user.email,
            'password': 'SecurePass123!',
            'full_name': 'Another User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=duplicate_data,
                             content_type='application/json')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'UserAlreadyExistsError'
        assert 'User already exists' in data['message']
    
    def test_user_login_success(self, client, test_user, test_validation_schemas):
        """Test successful user login"""
        login_data = {
            'email': test_user.email,
            'password': 'SecurePass123!',
            'remember_me': True
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Login successful'
        assert 'data' in data
        assert 'user' in data['data']
        assert 'tokens' in data['data']
        
        # Verify user data
        user_data = data['data']['user']
        assert user_data['email'] == test_user.email
        assert user_data['full_name'] == test_user.full_name
        assert 'id' in user_data
        
        # Verify tokens
        tokens = data['data']['tokens']
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'expires_in' in tokens
        # Remember me should give longer expiration
        assert tokens['expires_in'] == 86400  # 24 hours
    
    def test_user_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = client.post('/api/v1/auth/login',
                             json=invalid_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'AuthenticationError'
        assert 'Invalid email or password' in data['message']
    
    def test_user_login_disabled_account(self, client, app, db_session):
        """Test login with disabled account"""
        with app.app_context():
            from backend.services.auth_service import AuthService
            auth_service = AuthService()
            
            # Create disabled user
            user = auth_service.create_user(
                email='disabled@example.com',
                password='SecurePass123!',
                full_name='Disabled User'
            )
            user.is_active = False
            db_session.commit()
            
            login_data = {
                'email': 'disabled@example.com',
                'password': 'SecurePass123!'
            }
            
            response = client.post('/api/v1/auth/login',
                                 json=login_data,
                                 content_type='application/json')
            
            assert response.status_code == 403
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'AccountDisabledError'
            assert 'account has been disabled' in data['message']
    
    def test_token_refresh_success(self, client, test_user, app):
        """Test successful token refresh"""
        with app.app_context():
            from flask_jwt_extended import create_refresh_token
            refresh_token = create_refresh_token(identity=test_user.id)
            
            response = client.post('/api/v1/auth/refresh',
                                 headers={'Authorization': f'Bearer {refresh_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] == True
            assert data['message'] == 'Token refreshed successfully'
            assert 'data' in data
            assert 'access_token' in data['data']
            assert 'expires_in' in data['data']
    
    def test_token_refresh_invalid_token(self, client):
        """Test token refresh with invalid token"""
        response = client.post('/api/v1/auth/refresh',
                             headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert 'Invalid refresh token' in data['message']
    
    def test_user_logout_success(self, client, auth_headers):
        """Test successful user logout"""
        response = client.post('/api/v1/auth/logout',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Logout successful'
    
    def test_user_logout_unauthorized(self, client):
        """Test logout without authentication"""
        response = client.post('/api/v1/auth/logout')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'UnauthorizedError'
    
    def test_get_user_profile_success(self, client, auth_headers, test_user):
        """Test successful profile retrieval"""
        response = client.get('/api/v1/auth/profile',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Profile retrieved successfully'
        assert 'data' in data
        
        profile_data = data['data']
        assert profile_data['id'] == test_user.id
        assert profile_data['email'] == test_user.email
        assert profile_data['full_name'] == test_user.full_name
        assert profile_data['is_active'] == True
        assert 'created_at' in profile_data
        assert 'preferences' in profile_data
    
    def test_get_user_profile_unauthorized(self, client):
        """Test profile retrieval without authentication"""
        response = client.get('/api/v1/auth/profile')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'UnauthorizedError'
    
    def test_update_user_profile_success(self, client, auth_headers, test_user):
        """Test successful profile update"""
        update_data = {
            'full_name': 'Updated Test User',
            'phone_number': '+1234567891'
        }
        
        response = client.put('/api/v1/auth/profile',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Profile updated successfully'
        assert 'data' in data
        
        updated_data = data['data']
        assert updated_data['full_name'] == update_data['full_name']
        assert updated_data['phone_number'] == update_data['phone_number']
        assert 'updated_at' in updated_data
    
    def test_update_user_profile_validation_errors(self, client, auth_headers):
        """Test profile update with validation errors"""
        invalid_data = {
            'full_name': '',  # Empty name
            'phone_number': 'invalid-phone'  # Invalid phone format
        }
        
        response = client.put('/api/v1/auth/profile',
                            json=invalid_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        assert 'validation_errors' in data['details']
    
    def test_password_reset_request_success(self, client, test_user):
        """Test successful password reset request"""
        reset_data = {
            'email': test_user.email
        }
        
        with patch('backend.services.auth_service.AuthService.send_password_reset_email') as mock_send:
            mock_send.return_value = True
            
            response = client.post('/api/v1/auth/password/reset',
                                 json=reset_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] == True
            assert 'Password reset email sent' in data['message']
            
            # Verify email was sent
            mock_send.assert_called_once_with(test_user.email)
    
    def test_password_reset_request_nonexistent_email(self, client):
        """Test password reset request with nonexistent email"""
        reset_data = {
            'email': 'nonexistent@example.com'
        }
        
        with patch('backend.services.auth_service.AuthService.send_password_reset_email') as mock_send:
            mock_send.return_value = False
            
            response = client.post('/api/v1/auth/password/reset',
                                 json=reset_data,
                                 content_type='application/json')
            
            # Should still return success to prevent email enumeration
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] == True
            assert 'Password reset email sent' in data['message']
    
    def test_password_update_success(self, client, auth_headers, test_user):
        """Test successful password update"""
        password_data = {
            'current_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!'
        }
        
        response = client.post('/api/v1/auth/password/update',
                             json=password_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Password updated successfully'
    
    def test_password_update_wrong_current_password(self, client, auth_headers):
        """Test password update with wrong current password"""
        password_data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass456!'
        }
        
        response = client.post('/api/v1/auth/password/update',
                             json=password_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert 'Current password is incorrect' in data['message']
    
    def test_email_verification_success(self, client, auth_headers, test_user, app):
        """Test successful email verification"""
        with app.app_context():
            from backend.services.auth_service import AuthService
            auth_service = AuthService()
            
            # Create verification token
            verification_token = auth_service.create_email_verification_token(test_user.id)
            
            verify_data = {
                'verification_token': verification_token
            }
            
            response = client.post('/api/v1/auth/verify-email',
                                 json=verify_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] == True
            assert data['message'] == 'Email verified successfully'
    
    def test_email_verification_invalid_token(self, client, auth_headers):
        """Test email verification with invalid token"""
        verify_data = {
            'verification_token': 'invalid_token'
        }
        
        response = client.post('/api/v1/auth/verify-email',
                             json=verify_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert 'Email verification failed' in data['message']
    
    def test_check_auth_success(self, client, auth_headers, test_user):
        """Test successful authentication check"""
        response = client.get('/api/v1/auth/check-auth',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Authentication valid'
        assert 'data' in data
        
        auth_data = data['data']
        assert auth_data['user_id'] == test_user.id
        assert auth_data['email'] == test_user.email
        assert auth_data['is_active'] == True
    
    def test_check_auth_invalid_token(self, client):
        """Test authentication check with invalid token"""
        response = client.get('/api/v1/auth/check-auth',
                            headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert 'Authentication failed' in data['message']
    
    def test_rate_limiting_on_registration(self, client):
        """Test rate limiting on registration endpoint"""
        registration_data = {
            'email': 'rate_limit_test@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Rate Limit Test User'
        }
        
        # Make multiple registration attempts
        responses = []
        for i in range(6):  # Exceed the 5 requests per 5 minutes limit
            data = registration_data.copy()
            data['email'] = f'rate_limit_test_{i}@example.com'
            
            response = client.post('/api/v1/auth/register',
                                 json=data,
                                 content_type='application/json')
            responses.append(response)
        
        # The 6th request should be rate limited
        assert responses[-1].status_code == 429
        data = json.loads(responses[-1].data)
        
        assert data['success'] == False
        assert data['error'] == 'RateLimitError'
        assert 'Rate limit exceeded' in data['message']
        
        # Check rate limit headers
        assert 'X-RateLimit-Limit' in responses[-1].headers
        assert 'X-RateLimit-Remaining' in responses[-1].headers
        assert 'X-RateLimit-Reset' in responses[-1].headers
        assert 'Retry-After' in responses[-1].headers
    
    def test_rate_limiting_on_login(self, client, test_user):
        """Test rate limiting on login endpoint"""
        login_data = {
            'email': test_user.email,
            'password': 'SecurePass123!'
        }
        
        # Make multiple login attempts
        responses = []
        for i in range(11):  # Exceed the 10 requests per 5 minutes limit
            response = client.post('/api/v1/auth/login',
                                 json=login_data,
                                 content_type='application/json')
            responses.append(response)
        
        # The 11th request should be rate limited
        assert responses[-1].status_code == 429
        data = json.loads(responses[-1].data)
        
        assert data['success'] == False
        assert data['error'] == 'RateLimitError'
        assert 'Rate limit exceeded' in data['message']
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options('/api/v1/auth/register')
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    def test_security_headers(self, client, auth_headers):
        """Test security headers are present"""
        response = client.get('/api/v1/auth/profile',
                            headers=auth_headers)
        
        assert response.status_code == 200
        
        # Check security headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'
    
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "test@",
        "@example.com",
        "test.example.com",
        "test@.com",
        "test@example.",
        ""
    ])
    def test_email_validation_various_formats(self, client, invalid_email):
        """Test email validation with various invalid formats"""
        registration_data = {
            'email': invalid_email,
            'password': 'SecurePass123!',
            'full_name': 'Test User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=registration_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        
        # Check that email validation error is present
        errors = data['details']['validation_errors']
        email_errors = [e for e in errors if e['field'] == 'email']
        assert len(email_errors) > 0
    
    @pytest.mark.parametrize("weak_password", [
        "weak",
        "123456",
        "password",
        "qwerty",
        "abc123",
        "Password",  # No numbers or special chars
        "password123",  # No uppercase or special chars
        "PASSWORD123",  # No lowercase or special chars
        "Pass123"  # Too short
    ])
    def test_password_strength_validation(self, client, weak_password):
        """Test password strength validation"""
        registration_data = {
            'email': 'password_test@example.com',
            'password': weak_password,
            'full_name': 'Test User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=registration_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        
        # Check that password validation error is present
        errors = data['details']['validation_errors']
        password_errors = [e for e in errors if e['field'] == 'password']
        assert len(password_errors) > 0 