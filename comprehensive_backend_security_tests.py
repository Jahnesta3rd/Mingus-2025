#!/usr/bin/env python3
"""
Comprehensive Backend Security Test Suite for Mingus Application

Tests all critical security aspects:
- Authentication & Authorization (JWT)
- CSRF Protection
- SQL Injection Prevention
- XSS Protection
- Input Validation
- Rate Limiting
- Security Headers
- Session Security
- API Endpoint Security
- Data Protection

Usage:
    python comprehensive_backend_security_tests.py [--base-url http://localhost:5000]
"""

import os
import sys
import json
import time
import hmac
import hashlib
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class SecurityTestResult:
    """Security test result"""
    test_name: str
    category: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    message: str
    details: Dict[str, Any]
    timestamp: str

class ComprehensiveSecurityTester:
    """Comprehensive backend security test suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[SecurityTestResult] = []
        self.session = requests.Session()
        self.test_token = None
        self.csrf_token = None
        
    def log_result(self, test_name: str, category: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        result = SecurityTestResult(
            test_name=test_name,
            category=category,
            status=status,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
        
        status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_color}{status_symbol} {test_name}{Colors.RESET}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {Colors.CYAN}{key}{Colors.RESET}: {value}")
    
    # ============================================================================
    # AUTHENTICATION & AUTHORIZATION TESTS
    # ============================================================================
    
    def test_authentication_required(self):
        """Test that protected endpoints require authentication"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Authentication & Authorization...{Colors.RESET}")
        
        protected_endpoints = [
            '/api/profile',
            '/api/assessments',
            '/api/vehicle',
            '/api/daily-outlook',
            '/api/user-preferences',
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 401:
                    self.log_result(
                        f"Auth Required: {endpoint}",
                        "Authentication",
                        "PASS",
                        "Endpoint correctly requires authentication",
                        {"status_code": response.status_code}
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"Auth Required: {endpoint}",
                        "Authentication",
                        "PASS",
                        "Endpoint correctly requires authentication (403)",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_result(
                        f"Auth Required: {endpoint}",
                        "Authentication",
                        "FAIL",
                        f"Endpoint does not require authentication (status: {response.status_code})",
                        {"status_code": response.status_code, "response": response.text[:200]}
                    )
            except Exception as e:
                self.log_result(
                    f"Auth Required: {endpoint}",
                    "Authentication",
                    "WARN",
                    f"Error testing endpoint: {str(e)}",
                    {"error": str(e)}
                )
    
    def test_invalid_jwt_token(self):
        """Test that invalid JWT tokens are rejected"""
        invalid_tokens = [
            "invalid-token",
            "Bearer invalid",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "",
            None,
        ]
        
        for token in invalid_tokens:
            try:
                headers = {}
                if token:
                    headers['Authorization'] = f"Bearer {token}" if not token.startswith('Bearer') else token
                
                response = self.session.get(
                    f"{self.base_url}/api/profile",
                    headers=headers
                )
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        "Invalid JWT Rejection",
                        "Authentication",
                        "PASS",
                        f"Invalid token correctly rejected: {token[:20] if token else 'None'}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_result(
                        "Invalid JWT Rejection",
                        "Authentication",
                        "FAIL",
                        f"Invalid token was accepted: {token[:20] if token else 'None'}",
                        {"status_code": response.status_code}
                    )
            except Exception as e:
                self.log_result(
                    "Invalid JWT Rejection",
                    "Authentication",
                    "WARN",
                    f"Error testing invalid token: {str(e)}",
                    {"error": str(e)}
                )
    
    def test_authorization_bypass(self):
        """Test for authorization bypass vulnerabilities"""
        # Test accessing other users' data
        test_cases = [
            {
                "name": "User ID Manipulation",
                "endpoint": "/api/profile",
                "params": {"user_id": "1' OR '1'='1"},
            },
            {
                "name": "Path Traversal",
                "endpoint": "/api/profile/../../../etc/passwd",
            },
            {
                "name": "IDOR Attempt",
                "endpoint": "/api/profile/999999",
            },
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}{test_case['endpoint']}",
                    params=test_case.get('params', {})
                )
                
                # Should reject unauthorized access
                if response.status_code in [401, 403, 404]:
                    self.log_result(
                        f"Auth Bypass: {test_case['name']}",
                        "Authorization",
                        "PASS",
                        "Authorization bypass attempt correctly blocked",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_result(
                        f"Auth Bypass: {test_case['name']}",
                        "Authorization",
                        "WARN",
                        f"Potential authorization issue (status: {response.status_code})",
                        {"status_code": response.status_code, "response_preview": response.text[:100]}
                    )
            except Exception as e:
                self.log_result(
                    f"Auth Bypass: {test_case['name']}",
                    "Authorization",
                    "WARN",
                    f"Error testing: {str(e)}",
                    {"error": str(e)}
                )
    
    # ============================================================================
    # CSRF PROTECTION TESTS
    # ============================================================================
    
    def test_csrf_protection(self):
        """Test CSRF protection on state-changing endpoints"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing CSRF Protection...{Colors.RESET}")
        
        csrf_protected_endpoints = [
            {'method': 'POST', 'endpoint': '/api/assessments'},
            {'method': 'POST', 'endpoint': '/api/vehicle'},
            {'method': 'PUT', 'endpoint': '/api/profile'},
            {'method': 'DELETE', 'endpoint': '/api/vehicle/1'},
        ]
        
        for endpoint_config in csrf_protected_endpoints:
            method = endpoint_config['method']
            endpoint = endpoint_config['endpoint']
            
            try:
                # Test without CSRF token
                if method == 'POST':
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                elif method == 'PUT':
                    response = self.session.put(f"{self.base_url}{endpoint}", json={})
                elif method == 'DELETE':
                    response = self.session.delete(f"{self.base_url}{endpoint}")
                else:
                    continue
                
                if response.status_code == 403:
                    self.log_result(
                        f"CSRF Protection: {method} {endpoint}",
                        "CSRF",
                        "PASS",
                        "CSRF protection is active",
                        {"status_code": response.status_code}
                    )
                elif response.status_code == 401:
                    self.log_result(
                        f"CSRF Protection: {method} {endpoint}",
                        "CSRF",
                        "WARN",
                        "Endpoint requires auth (CSRF check may be after auth)",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_result(
                        f"CSRF Protection: {method} {endpoint}",
                        "CSRF",
                        "FAIL",
                        f"CSRF protection may be missing (status: {response.status_code})",
                        {"status_code": response.status_code}
                    )
            except Exception as e:
                self.log_result(
                    f"CSRF Protection: {method} {endpoint}",
                    "CSRF",
                    "WARN",
                    f"Error testing CSRF: {str(e)}",
                    {"error": str(e)}
                )
    
    # ============================================================================
    # SQL INJECTION TESTS
    # ============================================================================
    
    def test_sql_injection(self):
        """Test SQL injection prevention"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing SQL Injection Prevention...{Colors.RESET}")
        
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "' OR 1=1--",
            "' OR '1'='1'--",
            "1' AND '1'='1",
            "'; EXEC xp_cmdshell('dir'); --",
        ]
        
        test_endpoints = [
            {'endpoint': '/api/profile', 'params': {'user_id': None}},
            {'endpoint': '/api/assessments', 'params': {'id': None}},
            {'endpoint': '/api/vehicle', 'params': {'id': None}},
        ]
        
        for endpoint_config in test_endpoints:
            endpoint = endpoint_config['endpoint']
            param_name = list(endpoint_config['params'].keys())[0] if endpoint_config['params'] else None
            
            for payload in sql_injection_payloads[:3]:  # Test first 3 payloads per endpoint
                try:
                    if param_name:
                        params = {param_name: payload}
                        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                    else:
                        # Try in URL path
                        test_endpoint = f"{endpoint}/{quote(payload)}"
                        response = self.session.get(f"{self.base_url}{test_endpoint}")
                    
                    # Check if SQL error is exposed
                    response_text = response.text.lower()
                    sql_error_indicators = [
                        'sql syntax',
                        'mysql error',
                        'postgresql error',
                        'sqlite error',
                        'ora-',
                        'sqlstate',
                        'database error',
                    ]
                    
                    has_sql_error = any(indicator in response_text for indicator in sql_error_indicators)
                    
                    if has_sql_error:
                        self.log_result(
                            f"SQL Injection: {endpoint}",
                            "SQL Injection",
                            "FAIL",
                            f"SQL error exposed in response",
                            {"payload": payload[:50], "status_code": response.status_code}
                        )
                    elif response.status_code in [400, 401, 403, 404, 422]:
                        self.log_result(
                            f"SQL Injection: {endpoint}",
                            "SQL Injection",
                            "PASS",
                            f"SQL injection attempt properly rejected",
                            {"payload": payload[:50], "status_code": response.status_code}
                        )
                    else:
                        self.log_result(
                            f"SQL Injection: {endpoint}",
                            "SQL Injection",
                            "WARN",
                            f"Unexpected response to SQL injection attempt",
                            {"payload": payload[:50], "status_code": response.status_code}
                        )
                except Exception as e:
                    self.log_result(
                        f"SQL Injection: {endpoint}",
                        "SQL Injection",
                        "WARN",
                        f"Error testing SQL injection: {str(e)}",
                        {"error": str(e)}
                    )
    
    # ============================================================================
    # XSS PROTECTION TESTS
    # ============================================================================
    
    def test_xss_protection(self):
        """Test XSS protection"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing XSS Protection...{Colors.RESET}")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            '"><script>alert("XSS")</script>',
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
        ]
        
        # Test XSS in various input fields
        test_data = {
            'name': None,
            'email': None,
            'description': None,
            'message': None,
        }
        
        for field_name, _ in test_data.items():
            for payload in xss_payloads[:2]:  # Test first 2 payloads per field
                try:
                    test_data_copy = {field_name: payload}
                    response = self.session.post(
                        f"{self.base_url}/api/assessments",
                        json=test_data_copy,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    response_text = response.text
                    # Check if payload is reflected unsanitized
                    if payload in response_text and '<script>' in response_text:
                        self.log_result(
                            f"XSS Protection: {field_name}",
                            "XSS",
                            "FAIL",
                            f"XSS payload reflected unsanitized",
                            {"payload": payload[:50], "field": field_name}
                        )
                    elif response.status_code in [400, 401, 403, 422]:
                        self.log_result(
                            f"XSS Protection: {field_name}",
                            "XSS",
                            "PASS",
                            f"XSS payload properly rejected/sanitized",
                            {"payload": payload[:50], "status_code": response.status_code}
                        )
                    else:
                        # Payload might be sanitized
                        sanitized_indicators = ['&lt;', '&gt;', '&amp;', '&quot;']
                        if any(indicator in response_text for indicator in sanitized_indicators):
                            self.log_result(
                                f"XSS Protection: {field_name}",
                                "XSS",
                                "PASS",
                                f"XSS payload appears to be sanitized",
                                {"payload": payload[:50]}
                            )
                        else:
                            self.log_result(
                                f"XSS Protection: {field_name}",
                                "XSS",
                                "WARN",
                                f"Could not verify XSS protection",
                                {"payload": payload[:50], "status_code": response.status_code}
                            )
                except Exception as e:
                    self.log_result(
                        f"XSS Protection: {field_name}",
                        "XSS",
                        "WARN",
                        f"Error testing XSS: {str(e)}",
                        {"error": str(e)}
                    )
    
    # ============================================================================
    # INPUT VALIDATION TESTS
    # ============================================================================
    
    def test_input_validation(self):
        """Test input validation"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Input Validation...{Colors.RESET}")
        
        invalid_inputs = [
            {'email': 'invalid-email'},
            {'email': 'test@'},
            {'email': '@example.com'},
            {'name': 'A' * 1000},  # Too long
            {'phone': '123'},  # Invalid format
            {'age': -1},  # Negative
            {'age': 200},  # Too large
            {'rating': 11},  # Out of range
            {'rating': -1},  # Out of range
        ]
        
        for invalid_input in invalid_inputs[:5]:  # Test first 5
            try:
                response = self.session.post(
                    f"{self.base_url}/api/assessments",
                    json=invalid_input,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 400 or response.status_code == 422:
                    self.log_result(
                        "Input Validation",
                        "Validation",
                        "PASS",
                        f"Invalid input correctly rejected: {list(invalid_input.keys())[0]}",
                        {"status_code": response.status_code, "input": str(invalid_input)[:100]}
                    )
                else:
                    self.log_result(
                        "Input Validation",
                        "Validation",
                        "WARN",
                        f"Invalid input may have been accepted",
                        {"status_code": response.status_code, "input": str(invalid_input)[:100]}
                    )
            except Exception as e:
                self.log_result(
                    "Input Validation",
                    "Validation",
                    "WARN",
                    f"Error testing validation: {str(e)}",
                    {"error": str(e)}
                )
    
    # ============================================================================
    # RATE LIMITING TESTS
    # ============================================================================
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Rate Limiting...{Colors.RESET}")
        
        try:
            # Make rapid requests
            rate_limit_triggered = False
            for i in range(110):  # Exceed typical rate limit
                response = self.session.get(f"{self.base_url}/health")
                if response.status_code == 429:
                    rate_limit_triggered = True
                    break
                time.sleep(0.1)  # Small delay
            
            if rate_limit_triggered:
                self.log_result(
                    "Rate Limiting",
                    "Rate Limiting",
                    "PASS",
                    "Rate limiting is active",
                    {"requests_made": i + 1, "status_code": 429}
                )
            else:
                self.log_result(
                    "Rate Limiting",
                    "Rate Limiting",
                    "WARN",
                    "Rate limiting may not be active or threshold is very high",
                    {"requests_made": 110}
                )
        except Exception as e:
            self.log_result(
                "Rate Limiting",
                "Rate Limiting",
                "WARN",
                f"Error testing rate limiting: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # SECURITY HEADERS TESTS
    # ============================================================================
    
    def test_security_headers(self):
        """Test security headers"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Security Headers...{Colors.RESET}")
        
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Just check if present
            'Content-Security-Policy': None,  # Just check if present
        }
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            for header_name, expected_value in required_headers.items():
                if header_name in headers:
                    header_value = headers[header_name]
                    if expected_value is None:
                        # Just check if present
                        self.log_result(
                            f"Security Header: {header_name}",
                            "Security Headers",
                            "PASS",
                            "Header is present",
                            {"value": header_value[:100]}
                        )
                    elif isinstance(expected_value, list):
                        # Check if value is in allowed list
                        if header_value in expected_value:
                            self.log_result(
                                f"Security Header: {header_name}",
                                "Security Headers",
                                "PASS",
                                f"Header has correct value",
                                {"value": header_value}
                            )
                        else:
                            self.log_result(
                                f"Security Header: {header_name}",
                                "Security Headers",
                                "WARN",
                                f"Header value may not be optimal",
                                {"value": header_value, "expected": expected_value}
                            )
                    elif header_value == expected_value:
                        self.log_result(
                            f"Security Header: {header_name}",
                            "Security Headers",
                            "PASS",
                            "Header has correct value",
                            {"value": header_value}
                        )
                    else:
                        self.log_result(
                            f"Security Header: {header_name}",
                            "Security Headers",
                            "WARN",
                            f"Header value differs from expected",
                            {"value": header_value, "expected": expected_value}
                        )
                else:
                    self.log_result(
                        f"Security Header: {header_name}",
                        "Security Headers",
                        "FAIL",
                        "Header is missing",
                        {}
                    )
        except Exception as e:
            self.log_result(
                "Security Headers",
                "Security Headers",
                "WARN",
                f"Error testing security headers: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # SESSION SECURITY TESTS
    # ============================================================================
    
    def test_session_security(self):
        """Test session security"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Session Security...{Colors.RESET}")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            cookies = response.cookies
            
            # Check for secure cookie flags
            for cookie in cookies:
                cookie_dict = dict(cookie.__dict__)
                cookie_name = cookie.name
                
                # Check HttpOnly flag
                if hasattr(cookie, 'has_nonstandard_attr') and 'HttpOnly' in str(cookie):
                    self.log_result(
                        f"Session Cookie: {cookie_name} HttpOnly",
                        "Session Security",
                        "PASS",
                        "Cookie has HttpOnly flag",
                        {}
                    )
                else:
                    self.log_result(
                        f"Session Cookie: {cookie_name} HttpOnly",
                        "Session Security",
                        "WARN",
                        "Cookie may not have HttpOnly flag",
                        {}
                    )
                
                # Check Secure flag (for HTTPS)
                if 'Secure' in str(cookie):
                    self.log_result(
                        f"Session Cookie: {cookie_name} Secure",
                        "Session Security",
                        "PASS",
                        "Cookie has Secure flag",
                        {}
                    )
                else:
                    self.log_result(
                        f"Session Cookie: {cookie_name} Secure",
                        "Session Security",
                        "WARN",
                        "Cookie may not have Secure flag (required for HTTPS)",
                        {}
                    )
        except Exception as e:
            self.log_result(
                "Session Security",
                "Session Security",
                "WARN",
                f"Error testing session security: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # API ENDPOINT SECURITY TESTS
    # ============================================================================
    
    def test_api_endpoint_security(self):
        """Test API endpoint security"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing API Endpoint Security...{Colors.RESET}")
        
        # Test for information disclosure
        sensitive_endpoints = [
            '/.env',
            '/config.json',
            '/package.json',
            '/.git/config',
            '/admin',
            '/phpinfo.php',
            '/.well-known/security.txt',
        ]
        
        for endpoint in sensitive_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 404:
                    self.log_result(
                        f"Info Disclosure: {endpoint}",
                        "API Security",
                        "PASS",
                        "Sensitive endpoint not accessible",
                        {"status_code": 404}
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"Info Disclosure: {endpoint}",
                        "API Security",
                        "PASS",
                        "Sensitive endpoint properly protected",
                        {"status_code": 403}
                    )
                else:
                    # Check if sensitive information is exposed
                    response_text = response.text.lower()
                    sensitive_indicators = [
                        'password',
                        'secret',
                        'api_key',
                        'database',
                        'connection string',
                    ]
                    
                    has_sensitive_info = any(indicator in response_text for indicator in sensitive_indicators)
                    
                    if has_sensitive_info:
                        self.log_result(
                            f"Info Disclosure: {endpoint}",
                            "API Security",
                            "FAIL",
                            "Sensitive information may be exposed",
                            {"status_code": response.status_code}
                        )
                    else:
                        self.log_result(
                            f"Info Disclosure: {endpoint}",
                            "API Security",
                            "WARN",
                            f"Endpoint accessible but may not expose sensitive info",
                            {"status_code": response.status_code}
                        )
            except Exception as e:
                self.log_result(
                    f"Info Disclosure: {endpoint}",
                    "API Security",
                    "WARN",
                    f"Error testing endpoint: {str(e)}",
                    {"error": str(e)}
                )
    
    # ============================================================================
    # DATA PROTECTION TESTS
    # ============================================================================
    
    def test_data_protection(self):
        """Test data protection measures"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Data Protection...{Colors.RESET}")
        
        # Test that sensitive data is not logged in error messages
        try:
            # Try to trigger an error
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint-12345")
            
            response_text = response.text.lower()
            sensitive_patterns = [
                'password',
                'secret',
                'api_key',
                'token',
                'database',
                'connection',
            ]
            
            exposed_sensitive = [pattern for pattern in sensitive_patterns if pattern in response_text]
            
            if exposed_sensitive:
                self.log_result(
                    "Data Protection: Error Messages",
                    "Data Protection",
                    "WARN",
                    "Sensitive information may be exposed in error messages",
                    {"exposed_patterns": exposed_sensitive}
                )
            else:
                self.log_result(
                    "Data Protection: Error Messages",
                    "Data Protection",
                    "PASS",
                    "No sensitive information exposed in error messages",
                    {}
                )
        except Exception as e:
            self.log_result(
                "Data Protection: Error Messages",
                "Data Protection",
                "WARN",
                f"Error testing data protection: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================
    
    def run_all_tests(self):
        """Run all security tests"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}MINGUS Backend Security Test Suite{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        # Run all test categories
        self.test_authentication_required()
        self.test_invalid_jwt_token()
        self.test_authorization_bypass()
        self.test_csrf_protection()
        self.test_sql_injection()
        self.test_xss_protection()
        self.test_input_validation()
        self.test_rate_limiting()
        self.test_security_headers()
        self.test_session_security()
        self.test_api_endpoint_security()
        self.test_data_protection()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.RESET}")
        
        # Group by category
        categories = {}
        for result in self.results:
            category = result.category
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0, 'failed': 0, 'warn': 0}
            categories[category]['total'] += 1
            if result.status == "PASS":
                categories[category]['passed'] += 1
            elif result.status == "FAIL":
                categories[category]['failed'] += 1
            else:
                categories[category]['warn'] += 1
        
        print(f"\n{Colors.BOLD}Results by Category:{Colors.RESET}")
        for category, stats in categories.items():
            print(f"\n  {Colors.BOLD}{category}:{Colors.RESET}")
            print(f"    Total: {stats['total']}")
            print(f"    {Colors.GREEN}Passed: {stats['passed']}{Colors.RESET}")
            print(f"    {Colors.RED}Failed: {stats['failed']}{Colors.RESET}")
            print(f"    {Colors.YELLOW}Warnings: {stats['warn']}{Colors.RESET}")
        
        # List failed tests
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in failed_tests:
                print(f"  ❌ {result.test_name}: {result.message}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backend_security_test_results_{timestamp}.json"
        
        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'summary': {
                'total': len(self.results),
                'passed': len([r for r in self.results if r.status == "PASS"]),
                'failed': len([r for r in self.results if r.status == "FAIL"]),
                'warnings': len([r for r in self.results if r.status == "WARN"]),
            },
            'results': [asdict(r) for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"\n{Colors.CYAN}Results saved to: {filename}{Colors.RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive Backend Security Test Suite')
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL of the backend API (default: http://localhost:5000)'
    )
    
    args = parser.parse_args()
    
    tester = ComprehensiveSecurityTester(base_url=args.base_url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
