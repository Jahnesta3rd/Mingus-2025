#!/usr/bin/env python3
"""
Comprehensive Penetration Testing Suite for MINGUS Application
Tests authentication, financial endpoints, infrastructure, and API security
"""

import requests
import json
import time
import hashlib
import hmac
import base64
import ssl
import socket
import urllib3
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import concurrent.futures
import re
import sys
import os

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, WARN, INFO
    details: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation: str
    evidence: Optional[Dict] = None

class MingusPenetrationTester:
    """Comprehensive penetration testing suite for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.csrf_token = None
        
        # Test credentials
        self.test_credentials = {
            'valid_user': {
                'email': 'test@example.com',
                'password': 'SecurePass123!'
            },
            'invalid_user': {
                'email': 'invalid@example.com',
                'password': 'WrongPassword123!'
            }
        }
        
        # Common attack payloads
        self.xss_payloads = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '<img src=x onerror=alert("XSS")>',
            '"><script>alert("XSS")</script>',
            '"><img src=x onerror=alert("XSS")>'
        ]
        
        self.sql_injection_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "1' OR '1' = '1' #"
        ]
        
        self.csrf_payloads = [
            '<form action="http://localhost:5001/api/payment/subscriptions" method="POST">',
            '<input type="hidden" name="amount" value="1000">',
            '<input type="submit" value="Click me!">',
            '</form>'
        ]
        
        print("🔍 MINGUS Comprehensive Penetration Testing Suite")
        print("=" * 60)
        print(f"Target URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all penetration tests"""
        print("\n🚀 Starting comprehensive penetration testing...")
        
        # 1. Authentication Security Testing
        print("\n🔐 Testing Authentication Security...")
        self.test_authentication_security()
        
        # 2. Financial Endpoint Security Testing
        print("\n💰 Testing Financial Endpoint Security...")
        self.test_financial_endpoint_security()
        
        # 3. Infrastructure Security Testing
        print("\n🏗️ Testing Infrastructure Security...")
        self.test_infrastructure_security()
        
        # 4. API Security Testing
        print("\n🔌 Testing API Security...")
        self.test_api_security()
        
        # Generate comprehensive report
        return self.generate_report()
    
    def test_authentication_security(self):
        """Test authentication security measures"""
        
        # Test 1: Authentication Bypass Attempts
        self.test_authentication_bypass()
        
        # Test 2: Brute Force Attack Resistance
        self.test_brute_force_resistance()
        
        # Test 3: Session Fixation and Hijacking
        self.test_session_security()
        
        # Test 4: Password Reset Functionality
        self.test_password_reset_security()
    
    def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities"""
        
        # Test 1.1: Direct access to protected endpoints without authentication
        protected_endpoints = [
            '/api/user/profile',
            '/api/financial/transactions',
            '/api/payment/subscriptions',
            '/api/admin/users'
        ]
        
        for endpoint in protected_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 200:
                self.add_result(
                    "Authentication Bypass",
                    "Authentication",
                    "FAIL",
                    f"Direct access to {endpoint} without authentication",
                    "CRITICAL",
                    "Implement proper authentication checks on all protected endpoints"
                )
            elif response.status_code == 401:
                self.add_result(
                    "Authentication Bypass",
                    "Authentication",
                    "PASS",
                    f"Protected endpoint {endpoint} properly requires authentication",
                    "LOW",
                    "Good - endpoint is properly protected"
                )
        
        # Test 1.2: Test with invalid/malformed tokens
        invalid_tokens = [
            "invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "Bearer invalid_token",
            ""
        ]
        
        for token in invalid_tokens:
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            response = self.session.get(f"{self.base_url}/api/user/profile", headers=headers)
            
            if response.status_code == 200:
                self.add_result(
                    "Invalid Token Access",
                    "Authentication",
                    "FAIL",
                    f"Access granted with invalid token: {token[:20]}...",
                    "CRITICAL",
                    "Reject all requests with invalid authentication tokens"
                )
            else:
                self.add_result(
                    "Invalid Token Access",
                    "Authentication",
                    "PASS",
                    f"Invalid token properly rejected: {token[:20]}...",
                    "LOW",
                    "Good - invalid tokens are properly rejected"
                )
    
    def test_brute_force_resistance(self):
        """Test brute force attack resistance"""
        
        # Test 2.1: Rapid login attempts
        print("  Testing brute force resistance...")
        
        for i in range(10):
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=self.test_credentials['invalid_user'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 429:
                self.add_result(
                    "Brute Force Protection",
                    "Authentication",
                    "PASS",
                    f"Rate limiting activated after {i+1} failed attempts",
                    "LOW",
                    "Good - rate limiting is working"
                )
                break
            elif i == 9 and response.status_code != 429:
                self.add_result(
                    "Brute Force Protection",
                    "Authentication",
                    "FAIL",
                    "No rate limiting detected after 10 failed login attempts",
                    "HIGH",
                    "Implement rate limiting for login attempts"
                )
        
        # Test 2.2: Account lockout functionality
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json=self.test_credentials['valid_user'],
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 423:
            self.add_result(
                "Account Lockout",
                "Authentication",
                "PASS",
                "Account lockout functionality detected",
                "LOW",
                "Good - account lockout is working"
            )
        else:
            self.add_result(
                "Account Lockout",
                "Authentication",
                "WARN",
                "Account lockout functionality not detected",
                "MEDIUM",
                "Consider implementing account lockout after multiple failed attempts"
            )
    
    def test_session_security(self):
        """Test session fixation and hijacking protection"""
        
        # Test 3.1: Session fixation test
        # Get initial session
        initial_session = self.session.cookies.get('session')
        
        # Attempt to set session ID
        self.session.cookies.set('session', 'fixed_session_id')
        
        response = self.session.get(f"{self.base_url}/api/user/profile")
        
        if response.status_code == 200:
            self.add_result(
                "Session Fixation",
                "Authentication",
                "FAIL",
                "Session fixation vulnerability detected",
                "HIGH",
                "Regenerate session ID after successful authentication"
            )
        else:
            self.add_result(
                "Session Fixation",
                "Authentication",
                "PASS",
                "Session fixation protection detected",
                "LOW",
                "Good - session IDs are properly managed"
            )
        
        # Test 3.2: Session hijacking test
        # Test with different User-Agent
        headers = {'User-Agent': 'Malicious-Bot/1.0'}
        response = self.session.get(f"{self.base_url}/api/user/profile", headers=headers)
        
        if response.status_code == 401:
            self.add_result(
                "Session Hijacking Protection",
                "Authentication",
                "PASS",
                "Session hijacking protection detected (User-Agent validation)",
                "LOW",
                "Good - User-Agent validation is working"
            )
        else:
            self.add_result(
                "Session Hijacking Protection",
                "Authentication",
                "WARN",
                "Session hijacking protection not detected",
                "MEDIUM",
                "Consider implementing User-Agent and IP validation"
            )
    
    def test_password_reset_security(self):
        """Test password reset functionality security"""
        
        # Test 4.1: Password reset enumeration
        test_emails = [
            'admin@example.com',
            'nonexistent@example.com',
            'test@example.com'
        ]
        
        for email in test_emails:
            response = self.session.post(
                f"{self.base_url}/api/auth/password-reset",
                json={'email': email},
                headers={'Content-Type': 'application/json'}
            )
            
            # Check if response reveals whether email exists
            if 'exists' in response.text.lower() or 'found' in response.text.lower():
                self.add_result(
                    "Password Reset Enumeration",
                    "Authentication",
                    "FAIL",
                    f"Email enumeration vulnerability detected for {email}",
                    "MEDIUM",
                    "Use generic response messages for password reset"
                )
            else:
                self.add_result(
                    "Password Reset Enumeration",
                    "Authentication",
                    "PASS",
                    f"Password reset properly handles {email}",
                    "LOW",
                    "Good - no email enumeration vulnerability"
                )
    
    def test_financial_endpoint_security(self):
        """Test financial endpoint security measures"""
        
        # Test 1: CSRF Protection Effectiveness
        self.test_csrf_protection()
        
        # Test 2: SQL Injection Testing
        self.test_sql_injection()
        
        # Test 3: XSS Testing
        self.test_xss_vulnerabilities()
        
        # Test 4: Authorization Testing
        self.test_authorization()
    
    def test_csrf_protection(self):
        """Test CSRF protection effectiveness"""
        
        financial_endpoints = [
            '/api/payment/subscriptions',
            '/api/financial/transactions',
            '/api/payment/payment-intents',
            '/api/financial/goals'
        ]
        
        for endpoint in financial_endpoints:
            # Test without CSRF token
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json={'amount': 100, 'description': 'Test transaction'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 403 and 'csrf' in response.text.lower():
                self.add_result(
                    "CSRF Protection",
                    "Financial Security",
                    "PASS",
                    f"CSRF protection active on {endpoint}",
                    "LOW",
                    "Good - CSRF protection is working"
                )
            elif response.status_code == 200:
                self.add_result(
                    "CSRF Protection",
                    "Financial Security",
                    "FAIL",
                    f"CSRF protection missing on {endpoint}",
                    "CRITICAL",
                    "Implement CSRF protection on all financial endpoints"
                )
            else:
                self.add_result(
                    "CSRF Protection",
                    "Financial Security",
                    "WARN",
                    f"CSRF protection status unclear on {endpoint}",
                    "MEDIUM",
                    "Verify CSRF protection implementation"
                )
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        
        # Test financial forms with SQL injection payloads
        test_endpoints = [
            ('/api/financial/transactions', {'description': 'test'}),
            ('/api/financial/profile', {'email': 'test@example.com'}),
            ('/api/payment/subscriptions', {'tier': 'basic'})
        ]
        
        for endpoint, base_data in test_endpoints:
            for payload in self.sql_injection_payloads:
                # Test in different fields
                for field in ['description', 'email', 'name', 'notes']:
                    if field in base_data:
                        test_data = base_data.copy()
                        test_data[field] = payload
                        
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            json=test_data,
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        # Check for SQL error messages
                        if any(error in response.text.lower() for error in [
                            'sql', 'mysql', 'postgresql', 'oracle', 'syntax error',
                            'unclosed quotation mark', 'incorrect syntax'
                        ]):
                            self.add_result(
                                "SQL Injection",
                                "Financial Security",
                                "FAIL",
                                f"SQL injection vulnerability detected in {endpoint} field {field}",
                                "CRITICAL",
                                "Use parameterized queries and input validation"
                            )
                            break
                else:
                    continue
                break
    
    def test_xss_vulnerabilities(self):
        """Test for XSS vulnerabilities"""
        
        # Test endpoints that might reflect user input
        test_endpoints = [
            '/api/financial/transactions',
            '/api/financial/profile',
            '/api/goals/set'
        ]
        
        for endpoint in test_endpoints:
            for payload in self.xss_payloads:
                test_data = {
                    'description': payload,
                    'notes': payload,
                    'name': payload
                }
                
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=test_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                # Check if payload is reflected in response
                if payload in response.text:
                    self.add_result(
                        "XSS Vulnerability",
                        "Financial Security",
                        "FAIL",
                        f"XSS payload reflected in {endpoint}",
                        "HIGH",
                        "Implement proper input sanitization and output encoding"
                    )
                    break
            else:
                self.add_result(
                    "XSS Protection",
                    "Financial Security",
                    "PASS",
                    f"XSS protection active on {endpoint}",
                    "LOW",
                    "Good - XSS protection is working"
                )
    
    def test_authorization(self):
        """Test authorization for subscription tiers"""
        
        # Test access to premium features without proper subscription
        premium_endpoints = [
            '/api/premium/analytics',
            '/api/premium/export',
            '/api/premium/advisor'
        ]
        
        for endpoint in premium_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 403:
                self.add_result(
                    "Authorization Control",
                    "Financial Security",
                    "PASS",
                    f"Proper authorization control on {endpoint}",
                    "LOW",
                    "Good - authorization is working"
                )
            elif response.status_code == 200:
                self.add_result(
                    "Authorization Control",
                    "Financial Security",
                    "FAIL",
                    f"Authorization bypass on {endpoint}",
                    "HIGH",
                    "Implement proper subscription tier validation"
                )
            else:
                self.add_result(
                    "Authorization Control",
                    "Financial Security",
                    "WARN",
                    f"Authorization status unclear on {endpoint}",
                    "MEDIUM",
                    "Verify authorization implementation"
                )
    
    def test_infrastructure_security(self):
        """Test infrastructure security measures"""
        
        # Test 1: SSL/TLS Configuration
        self.test_ssl_tls_configuration()
        
        # Test 2: Security Headers Validation
        self.test_security_headers()
        
        # Test 3: Server Information Disclosure
        self.test_information_disclosure()
        
        # Test 4: Directory Traversal
        self.test_directory_traversal()
    
    def test_ssl_tls_configuration(self):
        """Test SSL/TLS configuration"""
        
        parsed_url = urlparse(self.base_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        if parsed_url.scheme == 'https':
            try:
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Check certificate validity
                        if cert:
                            self.add_result(
                                "SSL Certificate",
                                "Infrastructure",
                                "PASS",
                                "Valid SSL certificate found",
                                "LOW",
                                "Good - SSL certificate is valid"
                            )
                            
                            # Check for weak ciphers
                            cipher = ssock.cipher()
                            weak_ciphers = ['RC4', 'DES', '3DES', 'MD5']
                            if any(weak in cipher[0] for weak in weak_ciphers):
                                self.add_result(
                                    "Weak Cipher",
                                    "Infrastructure",
                                    "WARN",
                                    f"Weak cipher detected: {cipher[0]}",
                                    "MEDIUM",
                                    "Use strong cipher suites only"
                                )
                            else:
                                self.add_result(
                                    "Cipher Strength",
                                    "Infrastructure",
                                    "PASS",
                                    f"Strong cipher used: {cipher[0]}",
                                    "LOW",
                                    "Good - strong cipher is used"
                                )
                        else:
                            self.add_result(
                                "SSL Certificate",
                                "Infrastructure",
                                "FAIL",
                                "No valid SSL certificate found",
                                "HIGH",
                                "Install valid SSL certificate"
                            )
                            
            except Exception as e:
                self.add_result(
                    "SSL Configuration",
                    "Infrastructure",
                    "FAIL",
                    f"SSL connection failed: {str(e)}",
                    "HIGH",
                    "Fix SSL/TLS configuration"
                )
        else:
            self.add_result(
                "HTTPS Enforcement",
                "Infrastructure",
                "WARN",
                "Application not using HTTPS",
                "MEDIUM",
                "Enforce HTTPS for all connections"
            )
    
    def test_security_headers(self):
        """Test security headers"""
        
        response = self.session.get(self.base_url)
        headers = response.headers
        
        # Test essential security headers
        security_headers = {
            'Strict-Transport-Security': 'HSTS',
            'X-Frame-Options': 'Clickjacking Protection',
            'X-Content-Type-Options': 'MIME Sniffing Protection',
            'X-XSS-Protection': 'XSS Protection',
            'Content-Security-Policy': 'CSP',
            'Referrer-Policy': 'Referrer Policy',
            'Permissions-Policy': 'Permissions Policy'
        }
        
        for header, description in security_headers.items():
            if header in headers:
                value = headers[header]
                if header == 'X-Frame-Options' and value == 'DENY':
                    self.add_result(
                        f"{description}",
                        "Infrastructure",
                        "PASS",
                        f"{header}: {value}",
                        "LOW",
                        "Good - proper security header"
                    )
                elif header == 'Content-Security-Policy' and value:
                    self.add_result(
                        f"{description}",
                        "Infrastructure",
                        "PASS",
                        f"{header} is present",
                        "LOW",
                        "Good - CSP is configured"
                    )
                else:
                    self.add_result(
                        f"{description}",
                        "Infrastructure",
                        "WARN",
                        f"{header}: {value}",
                        "MEDIUM",
                        f"Verify {description} configuration"
                    )
            else:
                self.add_result(
                    f"{description}",
                    "Infrastructure",
                    "FAIL",
                    f"{header} header missing",
                    "MEDIUM",
                    f"Add {description} header"
                )
    
    def test_information_disclosure(self):
        """Test for information disclosure"""
        
        # Test common information disclosure endpoints
        info_endpoints = [
            '/.git/config',
            '/.env',
            '/config.php',
            '/phpinfo.php',
            '/server-status',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        for endpoint in info_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 200:
                # Check for sensitive information
                sensitive_patterns = [
                    r'password\s*=\s*\w+',
                    r'secret\s*=\s*\w+',
                    r'api_key\s*=\s*\w+',
                    r'database_url\s*=\s*\w+',
                    r'admin\s*=\s*\w+'
                ]
                
                for pattern in sensitive_patterns:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        self.add_result(
                            "Information Disclosure",
                            "Infrastructure",
                            "FAIL",
                            f"Sensitive information disclosed in {endpoint}",
                            "HIGH",
                            "Remove or secure sensitive information"
                        )
                        break
                else:
                    self.add_result(
                        "Information Disclosure",
                        "Infrastructure",
                        "WARN",
                        f"Potentially sensitive endpoint accessible: {endpoint}",
                        "MEDIUM",
                        "Review and secure if necessary"
                    )
    
    def test_directory_traversal(self):
        """Test for directory traversal vulnerabilities"""
        
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ]
        
        test_endpoints = [
            '/api/file/',
            '/uploads/',
            '/static/',
            '/images/'
        ]
        
        for endpoint in test_endpoints:
            for payload in traversal_payloads:
                response = self.session.get(f"{self.base_url}{endpoint}{payload}")
                
                if response.status_code == 200:
                    # Check for system file content
                    if 'root:' in response.text or 'Administrator' in response.text:
                        self.add_result(
                            "Directory Traversal",
                            "Infrastructure",
                            "FAIL",
                            f"Directory traversal vulnerability in {endpoint}",
                            "CRITICAL",
                            "Implement proper path validation"
                        )
                        break
            else:
                self.add_result(
                    "Directory Traversal",
                    "Infrastructure",
                    "PASS",
                    f"Directory traversal protection in {endpoint}",
                    "LOW",
                    "Good - path validation is working"
                )
    
    def test_api_security(self):
        """Test API security measures"""
        
        # Test 1: REST API Authentication
        self.test_rest_api_authentication()
        
        # Test 2: Rate Limiting Effectiveness
        self.test_rate_limiting()
        
        # Test 3: Input Validation
        self.test_input_validation()
        
        # Test 4: Error Message Information Disclosure
        self.test_error_disclosure()
    
    def test_rest_api_authentication(self):
        """Test REST API authentication"""
        
        api_endpoints = [
            '/api/user/profile',
            '/api/financial/transactions',
            '/api/assessment/results',
            '/api/admin/users'
        ]
        
        for endpoint in api_endpoints:
            # Test without authentication
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 401:
                self.add_result(
                    "API Authentication",
                    "API Security",
                    "PASS",
                    f"Proper authentication required for {endpoint}",
                    "LOW",
                    "Good - API authentication is working"
                )
            elif response.status_code == 200:
                self.add_result(
                    "API Authentication",
                    "API Security",
                    "FAIL",
                    f"Authentication bypass on {endpoint}",
                    "CRITICAL",
                    "Implement proper API authentication"
                )
            else:
                self.add_result(
                    "API Authentication",
                    "API Security",
                    "WARN",
                    f"Authentication status unclear on {endpoint}",
                    "MEDIUM",
                    "Verify API authentication implementation"
                )
    
    def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        
        # Test rapid API requests
        print("  Testing rate limiting...")
        
        for i in range(20):
            response = self.session.get(f"{self.base_url}/api/assessment/results")
            
            if response.status_code == 429:
                self.add_result(
                    "API Rate Limiting",
                    "API Security",
                    "PASS",
                    f"Rate limiting activated after {i+1} requests",
                    "LOW",
                    "Good - rate limiting is working"
                )
                break
            elif i == 19 and response.status_code != 429:
                self.add_result(
                    "API Rate Limiting",
                    "API Security",
                    "FAIL",
                    "No rate limiting detected after 20 rapid requests",
                    "HIGH",
                    "Implement rate limiting for API endpoints"
                )
    
    def test_input_validation(self):
        """Test input validation"""
        
        # Test various input validation scenarios
        test_cases = [
            {
                'endpoint': '/api/user/profile',
                'data': {'email': 'invalid-email'},
                'field': 'email'
            },
            {
                'endpoint': '/api/financial/transactions',
                'data': {'amount': 'not-a-number'},
                'field': 'amount'
            },
            {
                'endpoint': '/api/assessment/submit',
                'data': {'responses': 'invalid-json'},
                'field': 'responses'
            }
        ]
        
        for test_case in test_cases:
            response = self.session.post(
                f"{self.base_url}{test_case['endpoint']}",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                self.add_result(
                    "Input Validation",
                    "API Security",
                    "PASS",
                    f"Proper validation for {test_case['field']}",
                    "LOW",
                    "Good - input validation is working"
                )
            elif response.status_code == 200:
                self.add_result(
                    "Input Validation",
                    "API Security",
                    "FAIL",
                    f"Missing validation for {test_case['field']}",
                    "MEDIUM",
                    "Implement proper input validation"
                )
            else:
                self.add_result(
                    "Input Validation",
                    "API Security",
                    "WARN",
                    f"Validation status unclear for {test_case['field']}",
                    "MEDIUM",
                    "Verify input validation implementation"
                )
    
    def test_error_disclosure(self):
        """Test for error message information disclosure"""
        
        # Test endpoints that might reveal sensitive information
        test_endpoints = [
            '/api/user/nonexistent',
            '/api/financial/invalid',
            '/api/admin/unauthorized'
        ]
        
        for endpoint in test_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            # Check for sensitive information in error messages
            sensitive_patterns = [
                r'sql.*error',
                r'stack.*trace',
                r'file.*path',
                r'database.*connection',
                r'password.*failed',
                r'secret.*key'
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, response.text, re.IGNORECASE):
                    self.add_result(
                        "Error Disclosure",
                        "API Security",
                        "FAIL",
                        f"Sensitive information in error message: {endpoint}",
                        "MEDIUM",
                        "Use generic error messages in production"
                    )
                    break
            else:
                self.add_result(
                    "Error Disclosure",
                    "API Security",
                    "PASS",
                    f"No sensitive information disclosed in {endpoint}",
                    "LOW",
                    "Good - error messages are secure"
                )
    
    def add_result(self, test_name: str, category: str, status: str, 
                  details: str, severity: str, recommendation: str, 
                  evidence: Optional[Dict] = None):
        """Add test result to results list"""
        result = TestResult(
            test_name=test_name,
            category=category,
            status=status,
            details=details,
            severity=severity,
            recommendation=recommendation,
            evidence=evidence
        )
        self.test_results.append(result)
        
        # Print result immediately
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌',
            'WARN': '⚠️',
            'INFO': 'ℹ️'
        }.get(status, '❓')
        
        print(f"  {status_icon} {test_name}: {details}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == 'PASS'])
        failed_tests = len([r for r in self.test_results if r.status == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r.status == 'WARN'])
        
        # Calculate security score
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by category
        results_by_category = {}
        for result in self.test_results:
            if result.category not in results_by_category:
                results_by_category[result.category] = []
            results_by_category[result.category].append(result)
        
        # Group results by severity
        critical_issues = [r for r in self.test_results if r.severity == 'CRITICAL']
        high_issues = [r for r in self.test_results if r.severity == 'HIGH']
        medium_issues = [r for r in self.test_results if r.severity == 'MEDIUM']
        low_issues = [r for r in self.test_results if r.severity == 'LOW']
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'security_score': round(score, 2),
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'medium_issues': len(medium_issues),
                'low_issues': len(low_issues)
            },
            'results_by_category': results_by_category,
            'results_by_severity': {
                'critical': critical_issues,
                'high': high_issues,
                'medium': medium_issues,
                'low': low_issues
            },
            'recommendations': self.generate_recommendations(),
            'test_details': [vars(r) for r in self.test_results]
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results"""
        recommendations = []
        
        # Critical issues
        critical_issues = [r for r in self.test_results if r.severity == 'CRITICAL']
        if critical_issues:
            recommendations.append("🚨 CRITICAL: Address all critical security issues immediately")
        
        # High issues
        high_issues = [r for r in self.test_results if r.severity == 'HIGH']
        if high_issues:
            recommendations.append("⚠️ HIGH: Prioritize fixing high-severity vulnerabilities")
        
        # Authentication issues
        auth_failures = [r for r in self.test_results if r.category == 'Authentication' and r.status == 'FAIL']
        if auth_failures:
            recommendations.append("🔐 Authentication: Implement proper authentication and session management")
        
        # Financial security issues
        financial_failures = [r for r in self.test_results if r.category == 'Financial Security' and r.status == 'FAIL']
        if financial_failures:
            recommendations.append("💰 Financial Security: Strengthen CSRF protection and input validation")
        
        # Infrastructure issues
        infra_failures = [r for r in self.test_results if r.category == 'Infrastructure' and r.status == 'FAIL']
        if infra_failures:
            recommendations.append("🏗️ Infrastructure: Secure server configuration and headers")
        
        # API security issues
        api_failures = [r for r in self.test_results if r.category == 'API Security' and r.status == 'FAIL']
        if api_failures:
            recommendations.append("🔌 API Security: Implement proper API authentication and rate limiting")
        
        return recommendations
    
    def print_report(self, report: Dict[str, Any]):
        """Print comprehensive security report"""
        
        print("\n" + "=" * 60)
        print("🔒 MINGUS SECURITY PENETRATION TEST REPORT")
        print("=" * 60)
        
        summary = report['summary']
        print(f"\n📊 SECURITY SCORE: {summary['security_score']}%")
        print(f"📈 TEST RESULTS:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⚠️ Warnings: {summary['warnings']}")
        
        print(f"\n🚨 VULNERABILITIES BY SEVERITY:")
        print(f"   🔴 Critical: {summary['critical_issues']}")
        print(f"   🟠 High: {summary['high_issues']}")
        print(f"   🟡 Medium: {summary['medium_issues']}")
        print(f"   🟢 Low: {summary['low_issues']}")
        
        # Print critical and high issues
        if report['results_by_severity']['critical']:
            print(f"\n🔴 CRITICAL ISSUES:")
            for issue in report['results_by_severity']['critical']:
                print(f"   • {issue.test_name}: {issue.details}")
                print(f"     Recommendation: {issue.recommendation}")
        
        if report['results_by_severity']['high']:
            print(f"\n🟠 HIGH PRIORITY ISSUES:")
            for issue in report['results_by_severity']['high']:
                print(f"   • {issue.test_name}: {issue.details}")
                print(f"     Recommendation: {issue.recommendation}")
        
        # Print recommendations
        if report['recommendations']:
            print(f"\n💡 SECURITY RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   {rec}")
        
        print(f"\n" + "=" * 60)
        print("🔍 Penetration testing completed successfully!")
        print("=" * 60)

def main():
    """Main function to run penetration testing"""
    
    # Get target URL from command line or use default
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    # Create tester instance
    tester = MingusPenetrationTester(target_url)
    
    try:
        # Run all tests
        report = tester.run_all_tests()
        
        # Print comprehensive report
        tester.print_report(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"mingus_security_report_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Exit with appropriate code
        if report['summary']['critical_issues'] > 0:
            print("\n❌ CRITICAL SECURITY ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
            sys.exit(1)
        elif report['summary']['high_issues'] > 0:
            print("\n⚠️ HIGH PRIORITY SECURITY ISSUES DETECTED - URGENT ACTION REQUIRED")
            sys.exit(2)
        else:
            print("\n✅ No critical or high priority security issues detected")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Penetration testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during penetration testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
