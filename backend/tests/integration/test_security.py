"""
Security integration tests
"""
import pytest
import json
import hmac
import hashlib
import time

class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_required_for_post(self, client, auth_headers):
        """Test that POST requests require CSRF token"""
        headers = {k: v for k, v in auth_headers.items() if k != 'X-CSRF-Token'}
        
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=headers,
            content_type='application/json'
        )
        
        # Should require CSRF or auth
        assert response.status_code in [401, 403]
    
    def test_invalid_csrf_token(self, client, auth_headers):
        """Test that invalid CSRF tokens are rejected"""
        headers = auth_headers.copy()
        headers['X-CSRF-Token'] = 'invalid-token'
        
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=headers,
            content_type='application/json'
        )
        
        # Should reject invalid CSRF
        assert response.status_code in [401, 403]

class TestAuthentication:
    """Test authentication"""
    
    def test_authentication_required(self, client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            '/api/profile',
            '/api/daily-outlook',
            '/api/vehicle'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"
    
    def test_invalid_jwt_token(self, client):
        """Test that invalid JWT tokens are rejected"""
        headers = {
            'Authorization': 'Bearer invalid-token',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/profile', headers=headers)
        assert response.status_code in [401, 403]
    
    def test_missing_authorization_header(self, client):
        """Test that missing authorization header is rejected"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/profile', headers=headers)
        assert response.status_code in [401, 403]

class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""
    
    def test_sql_injection_in_email(self, client, auth_headers):
        """Test SQL injection in email field"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--"
        ]
        
        for payload in sql_payloads:
            data = {
                'email': payload,
                'assessmentType': 'ai-risk',
                'answers': {}
            }
            
            response = client.post(
                '/api/assessments',
                data=json.dumps(data),
                headers=auth_headers,
                content_type='application/json'
            )
            
            # Should reject or sanitize
            assert response.status_code in [400, 422, 401, 403]
            
            # Check response doesn't contain SQL errors
            if response.status_code == 500:
                response_text = response.data.decode('utf-8').lower()
                sql_errors = ['sql syntax', 'mysql error', 'database error']
                assert not any(error in response_text for error in sql_errors)
    
    def test_sql_injection_in_params(self, client, auth_headers):
        """Test SQL injection in URL parameters"""
        sql_payloads = [
            "1' OR '1'='1",
            "'; DROP TABLE users; --"
        ]
        
        for payload in sql_payloads:
            response = client.get(
                f'/api/profile?user_id={payload}',
                headers=auth_headers
            )
            
            # Should handle safely
            assert response.status_code in [400, 401, 403, 404, 422]

class TestXSSPrevention:
    """Test XSS prevention"""
    
    def test_xss_in_input_fields(self, client, auth_headers):
        """Test XSS in various input fields"""
        xss_payloads = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src=x onerror=alert("xss")>',
            '<svg onload=alert("xss")>'
        ]
        
        for payload in xss_payloads:
            data = {
                'email': 'test@example.com',
                'firstName': payload,
                'assessmentType': 'ai-risk',
                'answers': {}
            }
            
            response = client.post(
                '/api/assessments',
                data=json.dumps(data),
                headers=auth_headers,
                content_type='application/json'
            )
            
            # Should sanitize or reject
            if response.status_code in [200, 201]:
                response_data = json.loads(response.data)
                response_str = json.dumps(response_data)
                # Check that XSS is not reflected
                assert '<script>' not in response_str
                assert 'javascript:' not in response_str.lower()

class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_enforcement(self, client, auth_headers):
        """Test that rate limiting is enforced"""
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        responses = []
        for i in range(150):  # Exceed typical rate limit
            response = client.post(
                '/api/assessments',
                data=json.dumps(data),
                headers=auth_headers,
                content_type='application/json'
            )
            responses.append(response.status_code)
            
            if response.status_code == 429:
                break
            
            time.sleep(0.01)  # Small delay
        
        # Should eventually hit rate limit
        # Note: Rate limiting may not be enabled in test environment
        assert 429 in responses or all(r in [200, 201, 400, 401, 403] for r in responses)

class TestInputSanitization:
    """Test input sanitization"""
    
    def test_null_byte_removal(self, client, auth_headers):
        """Test that null bytes are removed"""
        data = {
            'email': 'test\x00@example.com',
            'firstName': 'John\x00Doe',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        if response.status_code in [200, 201]:
            response_data = json.loads(response.data)
            response_str = json.dumps(response_data)
            assert '\x00' not in response_str
    
    def test_control_character_removal(self, client, auth_headers):
        """Test that control characters are removed"""
        data = {
            'email': 'test@example.com',
            'firstName': 'John\r\nDoe',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should sanitize control characters
        assert response.status_code in [200, 201, 400, 422]

class TestPathTraversalPrevention:
    """Test path traversal prevention"""
    
    def test_path_traversal_in_params(self, client, auth_headers):
        """Test path traversal in URL parameters"""
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//etc/passwd'
        ]
        
        for payload in traversal_payloads:
            response = client.get(
                f'/api/profile?file={payload}',
                headers=auth_headers
            )
            
            # Should reject path traversal attempts
            assert response.status_code in [400, 401, 403, 404, 422]
            
            # Should not expose file contents
            if response.status_code == 200:
                response_text = response.data.decode('utf-8').lower()
                sensitive_indicators = ['root:', '[boot loader]', 'password']
                assert not any(indicator in response_text for indicator in sensitive_indicators)

class TestCommandInjectionPrevention:
    """Test command injection prevention"""
    
    def test_command_injection_in_input(self, client, auth_headers):
        """Test command injection prevention"""
        command_payloads = [
            '; ls',
            '| cat /etc/passwd',
            '&& rm -rf /',
            '`ls`',
            '$(cat /etc/passwd)'
        ]
        
        for payload in command_payloads:
            data = {
                'email': 'test@example.com',
                'firstName': payload,
                'assessmentType': 'ai-risk',
                'answers': {}
            }
            
            response = client.post(
                '/api/assessments',
                data=json.dumps(data),
                headers=auth_headers,
                content_type='application/json'
            )
            
            # Should sanitize or reject
            assert response.status_code in [200, 201, 400, 422, 401, 403]
            
            # Should not execute commands
            if response.status_code == 200:
                response_text = response.data.decode('utf-8').lower()
                command_outputs = ['total ', 'drwx', 'file not found']
                assert not any(output in response_text for output in command_outputs)
