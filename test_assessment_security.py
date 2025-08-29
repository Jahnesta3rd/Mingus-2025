"""
Test Assessment Security Implementation
Comprehensive tests for CSRF protection and security headers
"""

import pytest
import json
import time
import secrets
from unittest.mock import Mock, patch
from flask import Flask, session, request
from backend.security.csrf_protection import CSRFProtection, require_csrf_token
from backend.security.security_headers import SecurityHeaders, configure_secure_cookies
from backend.security.assessment_security_integration import (
    AssessmentSecurityIntegration,
    secure_assessment_endpoint,
    secure_assessment_submission
)

@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for testing
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def csrf_protection(app):
    """Create CSRF protection instance"""
    return CSRFProtection(app.config['SECRET_KEY'])

@pytest.fixture
def security_headers(app):
    """Create security headers instance"""
    return SecurityHeaders(app)

class TestCSRFProtection:
    """Test CSRF protection functionality"""
    
    def test_generate_csrf_token(self, csrf_protection):
        """Test CSRF token generation"""
        token = csrf_protection.generate_csrf_token("test-session-id")
        
        # Token should have 3 parts: session_id:timestamp:signature
        parts = token.split(':')
        assert len(parts) == 3
        assert parts[0] == "test-session-id"
        assert parts[1].isdigit()  # timestamp should be numeric
        
        # Signature should be 64 characters (SHA256 hex)
        assert len(parts[2]) == 64
    
    def test_validate_csrf_token_valid(self, csrf_protection):
        """Test valid CSRF token validation"""
        session_id = "test-session-id"
        token = csrf_protection.generate_csrf_token(session_id)
        
        # Token should be valid
        assert csrf_protection.validate_csrf_token(token, session_id) == True
    
    def test_validate_csrf_token_invalid_session(self, csrf_protection):
        """Test CSRF token validation with wrong session ID"""
        session_id = "test-session-id"
        token = csrf_protection.generate_csrf_token(session_id)
        
        # Token should be invalid with different session ID
        assert csrf_protection.validate_csrf_token(token, "different-session-id") == False
    
    def test_validate_csrf_token_expired(self, csrf_protection):
        """Test expired CSRF token validation"""
        session_id = "test-session-id"
        
        # Create token with old timestamp
        old_timestamp = str(int(time.time()) - 7200)  # 2 hours ago
        token_data = f"{session_id}:{old_timestamp}"
        signature = csrf_protection._generate_signature(token_data)
        token = f"{token_data}:{signature}"
        
        # Token should be invalid (expired)
        assert csrf_protection.validate_csrf_token(token, session_id) == False
    
    def test_validate_csrf_token_malformed(self, csrf_protection):
        """Test malformed CSRF token validation"""
        # Test with invalid token format
        assert csrf_protection.validate_csrf_token("invalid-token", "test-session-id") == False
        assert csrf_protection.validate_csrf_token("part1:part2", "test-session-id") == False
        assert csrf_protection.validate_csrf_token("", "test-session-id") == False
        assert csrf_protection.validate_csrf_token(None, "test-session-id") == False

class TestSecurityHeaders:
    """Test security headers functionality"""
    
    def test_add_security_headers(self, app, client):
        """Test security headers are added to responses"""
        security_headers = SecurityHeaders(app)
        
        @app.route('/test')
        def test_endpoint():
            return {'message': 'test'}
        
        response = client.get('/test')
        
        # Check basic security headers
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-Frame-Options') == 'DENY'
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
        assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
        
        # Check CSP header
        csp = response.headers.get('Content-Security-Policy')
        assert csp is not None
        assert 'default-src' in csp
        assert 'script-src' in csp
        assert 'style-src' in csp
    
    def test_configure_secure_cookies(self, app):
        """Test secure cookie configuration"""
        configure_secure_cookies(app)
        
        # Check cookie configuration
        assert app.config['SESSION_COOKIE_SECURE'] == True
        assert app.config['SESSION_COOKIE_HTTPONLY'] == True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Strict'
        assert app.config['SESSION_COOKIE_NAME'] == 'mingus_session'
        assert app.config['PERMANENT_SESSION_LIFETIME'] == 3600
    
    def test_remove_server_info(self, app, client):
        """Test server information is removed from headers"""
        security_headers = SecurityHeaders(app)
        
        @app.route('/test')
        def test_endpoint():
            response = app.make_response({'message': 'test'})
            response.headers['Server'] = 'TestServer'
            response.headers['X-Powered-By'] = 'TestFramework'
            return response
        
        response = client.get('/test')
        
        # Server information should be removed
        assert 'Server' not in response.headers
        assert 'X-Powered-By' not in response.headers

class TestAssessmentSecurityIntegration:
    """Test assessment security integration"""
    
    def test_init_assessment_security(self, app):
        """Test assessment security integration initialization"""
        integration = AssessmentSecurityIntegration(app)
        
        assert integration.csrf_protection is not None
        assert integration.security_headers is not None
        # The app attribute is set by init_assessment_security function, not the class
        # So we test the integration object directly
        assert integration.app == app
    
    def test_secure_assessment_endpoint_decorator(self, app, client):
        """Test secure assessment endpoint decorator"""
        integration = AssessmentSecurityIntegration(app)
        
        @app.route('/test-assessment', methods=['GET', 'POST'])
        @secure_assessment_endpoint
        def test_assessment():
            return {'message': 'test'}
        
        # GET request should work without CSRF token
        response = client.get('/test-assessment')
        assert response.status_code == 200
        
        # POST request should require CSRF token
        response = client.post('/test-assessment')
        assert response.status_code == 403
        assert b'CSRF token required' in response.data
    
    def test_secure_assessment_submission_decorator(self, app, client):
        """Test secure assessment submission decorator"""
        integration = AssessmentSecurityIntegration(app)
        
        @app.route('/test-submission/<assessment_type>', methods=['POST'])
        @secure_assessment_submission
        def test_submission(assessment_type):
            return {'message': 'test'}
        
        # Test with missing CSRF token but valid JSON
        response = client.post('/test-submission/financial-health', 
                             json={'responses': {'question1': 'answer1'}})
        assert response.status_code == 403
        
        # Test with missing responses
        with app.test_request_context('/test-submission/financial-health'):
            with app.test_client() as test_client:
                # Mock session
                with test_client.session_transaction() as sess:
                    sess['session_id'] = 'test-session'
                
                # Generate CSRF token with the same session ID
                token = integration.csrf_protection.generate_csrf_token('test-session')
                
                response = test_client.post('/test-submission/financial-health', 
                                          headers={'X-CSRFToken': token},
                                          json={})
                assert response.status_code == 400
                assert b'Missing assessment responses' in response.data

class TestCSRFEndpoints:
    """Test CSRF token endpoints"""
    
    def test_csrf_token_generation_endpoint(self, app, client):
        """Test CSRF token generation endpoint"""
        integration = AssessmentSecurityIntegration(app)
        
        # Test token generation
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
        
        response = client.get('/api/security/csrf-token')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'csrf_token' in data
        assert 'expires_in' in data
        assert 'token_id' in data
        
        # Validate generated token
        token = data['csrf_token']
        assert integration.csrf_protection.validate_csrf_token(token, 'test-session')
    
    def test_csrf_token_validation_endpoint(self, app, client):
        """Test CSRF token validation endpoint"""
        integration = AssessmentSecurityIntegration(app)
        
        # Set up session
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
        
        # Generate valid token
        token = integration.csrf_protection.generate_csrf_token('test-session')
        
        # Test valid token
        response = client.post('/api/security/csrf-token/validate',
                             json={'csrf_token': token})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['valid'] == True
        
        # Test invalid token
        response = client.post('/api/security/csrf-token/validate',
                             json={'csrf_token': 'invalid-token'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['valid'] == False

class TestSecurityMonitoring:
    """Test security monitoring endpoints"""
    
    def test_security_headers_validation_endpoint(self, app, client):
        """Test security headers validation endpoint"""
        integration = AssessmentSecurityIntegration(app)
        
        response = client.get('/api/security/monitoring/headers/validate')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'validation_results' in data
        assert 'headers' in data
        
        # Check validation results
        validation = data['validation_results']
        assert 'missing_headers' in validation
        assert 'present_headers' in validation
        assert 'is_secure' in validation
    
    def test_csrf_status_endpoint(self, app, client):
        """Test CSRF status endpoint"""
        integration = AssessmentSecurityIntegration(app)
        
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
        
        response = client.get('/api/security/monitoring/csrf/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'active_tokens' in data
        assert 'max_tokens' in data
        assert 'token_lifetime' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
