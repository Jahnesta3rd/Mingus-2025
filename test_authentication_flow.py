#!/usr/bin/env python3
"""
MINGUS Authentication Flow Test Suite
=====================================

Comprehensive testing of the complete user registration and authentication flow for Mingus:
- New user signup process
- Email verification (if implemented)
- Login functionality with proper session management
- Password reset flow
- Two-factor authentication (if implemented)
- Authentication bypass vulnerability testing

Author: Security Testing Team
Date: August 27, 2025
"""

import requests
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import sys
import os

class MingusAuthTester:
    """Comprehensive authentication flow tester for Mingus application"""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.current_user = None
        self.auth_tokens = {}
        
        # Test data
        self.test_users = [
            {
                'email': f'testuser{int(time.time())}@example.com',
                'password': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User',
                'phone_number': '+1234567890'
            },
            {
                'email': f'admin{int(time.time())}@example.com',
                'password': 'AdminPass456!',
                'first_name': 'Admin',
                'last_name': 'User',
                'phone_number': '+1234567891'
            }
        ]
        
        # Security test payloads
        self.security_payloads = {
            'sql_injection': [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--",
                "admin'/*",
                "admin'#"
            ],
            'xss': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//"
            ],
            'auth_bypass': [
                {"user_id": "1"},
                {"admin": "true"},
                {"role": "admin"},
                {"authenticated": "true"},
                {"bypass": "true"}
            ]
        }
    
    def log_test(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log test results"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'error': error
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
        if error:
            print(f"  Error: {error}")
    
    def test_endpoint_availability(self) -> bool:
        """Test if authentication endpoints are available"""
        try:
            endpoints = [
                '/api/auth/register',
                '/api/auth/login',
                '/api/auth/logout',
                '/api/auth/profile',
                '/api/auth/check-auth'
            ]
            
            available_endpoints = []
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 405, 401]:  # 405 = method not allowed, 401 = unauthorized
                        available_endpoints.append(endpoint)
                except requests.exceptions.RequestException:
                    pass
            
            if available_endpoints:
                self.log_test("Endpoint Availability", "PASS", f"Found {len(available_endpoints)} endpoints")
                return True
            else:
                self.log_test("Endpoint Availability", "FAIL", "No authentication endpoints found")
                return False
                
        except Exception as e:
            self.log_test("Endpoint Availability", "ERROR", "", str(e))
            return False
    
    def test_user_registration(self) -> bool:
        """Test new user registration process"""
        try:
            user_data = self.test_users[0]
            
            # Test registration with valid data
            registration_data = {
                'email': user_data['email'],
                'password': user_data['password'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'phone_number': user_data['phone_number']
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=registration_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201, 302]:  # Success or redirect
                self.log_test("User Registration", "PASS", f"User registered successfully: {user_data['email']}")
                self.current_user = user_data
                return True
            else:
                self.log_test("User Registration", "FAIL", f"Registration failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", "ERROR", "", str(e))
            return False
    
    def test_registration_validation(self) -> bool:
        """Test registration validation rules"""
        try:
            test_cases = [
                {
                    'name': 'Invalid Email',
                    'data': {
                        'email': 'invalid-email',
                        'password': 'SecurePass123!',
                        'first_name': 'Test',
                        'last_name': 'User'
                    },
                    'expected_status': 400
                },
                {
                    'name': 'Weak Password',
                    'data': {
                        'email': 'test@example.com',
                        'password': 'weak',
                        'first_name': 'Test',
                        'last_name': 'User'
                    },
                    'expected_status': 400
                },
                {
                    'name': 'Missing Required Fields',
                    'data': {
                        'email': 'test@example.com',
                        'password': 'SecurePass123!'
                    },
                    'expected_status': 400
                }
            ]
            
            passed_tests = 0
            for test_case in test_cases:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/auth/register",
                        json=test_case['data'],
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == test_case['expected_status']:
                        passed_tests += 1
                        self.log_test(f"Registration Validation - {test_case['name']}", "PASS")
                    else:
                        self.log_test(f"Registration Validation - {test_case['name']}", "FAIL", 
                                    f"Expected {test_case['expected_status']}, got {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Registration Validation - {test_case['name']}", "ERROR", "", str(e))
            
            return passed_tests == len(test_cases)
            
        except Exception as e:
            self.log_test("Registration Validation", "ERROR", "", str(e))
            return False
    
    def test_user_login(self) -> bool:
        """Test user login functionality"""
        try:
            if not self.current_user:
                self.log_test("User Login", "SKIP", "No user available for login test")
                return False
            
            login_data = {
                'email': self.current_user['email'],
                'password': self.current_user['password']
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 302]:  # Success or redirect
                self.log_test("User Login", "PASS", f"Login successful for {self.current_user['email']}")
                
                # Check for session cookies or tokens
                if 'session' in response.cookies or 'token' in response.cookies:
                    self.log_test("Session Management", "PASS", "Session cookie found")
                else:
                    self.log_test("Session Management", "WARN", "No session cookie found")
                
                return True
            else:
                self.log_test("User Login", "FAIL", f"Login failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Login", "ERROR", "", str(e))
            return False
    
    def test_login_validation(self) -> bool:
        """Test login validation and security"""
        try:
            test_cases = [
                {
                    'name': 'Invalid Credentials',
                    'data': {
                        'email': 'nonexistent@example.com',
                        'password': 'WrongPassword123!'
                    },
                    'expected_status': 401
                },
                {
                    'name': 'Empty Credentials',
                    'data': {
                        'email': '',
                        'password': ''
                    },
                    'expected_status': 400
                },
                {
                    'name': 'SQL Injection Attempt',
                    'data': {
                        'email': "admin'--",
                        'password': 'anything'
                    },
                    'expected_status': 401
                }
            ]
            
            passed_tests = 0
            for test_case in test_cases:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/auth/login",
                        json=test_case['data'],
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == test_case['expected_status']:
                        passed_tests += 1
                        self.log_test(f"Login Validation - {test_case['name']}", "PASS")
                    else:
                        self.log_test(f"Login Validation - {test_case['name']}", "FAIL", 
                                    f"Expected {test_case['expected_status']}, got {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Login Validation - {test_case['name']}", "ERROR", "", str(e))
            
            return passed_tests == len(test_cases)
            
        except Exception as e:
            self.log_test("Login Validation", "ERROR", "", str(e))
            return False
    
    def test_session_management(self) -> bool:
        """Test session management and persistence"""
        try:
            # Test if session persists across requests
            response = self.session.get(f"{self.base_url}/api/auth/check-auth")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    self.log_test("Session Persistence", "PASS", "Session persists across requests")
                    return True
                else:
                    self.log_test("Session Persistence", "FAIL", "Session not authenticated")
                    return False
            else:
                self.log_test("Session Persistence", "FAIL", f"Check auth failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Persistence", "ERROR", "", str(e))
            return False
    
    def test_user_logout(self) -> bool:
        """Test user logout functionality"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/logout")
            
            if response.status_code in [200, 302]:
                self.log_test("User Logout", "PASS", "Logout successful")
                
                # Verify session is cleared
                response = self.session.get(f"{self.base_url}/api/auth/check-auth")
                if response.status_code == 401 or not response.json().get('authenticated', False):
                    self.log_test("Session Clearance", "PASS", "Session properly cleared after logout")
                    return True
                else:
                    self.log_test("Session Clearance", "FAIL", "Session not cleared after logout")
                    return False
            else:
                self.log_test("User Logout", "FAIL", f"Logout failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Logout", "ERROR", "", str(e))
            return False
    
    def test_password_reset_flow(self) -> bool:
        """Test password reset functionality (if implemented)"""
        try:
            # Test password reset request
            reset_data = {
                'email': self.test_users[0]['email']
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/password-reset",
                json=reset_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                self.log_test("Password Reset Request", "PASS", "Password reset request successful")
                return True
            elif response.status_code == 404:
                self.log_test("Password Reset Request", "SKIP", "Password reset endpoint not implemented")
                return True
            else:
                self.log_test("Password Reset Request", "FAIL", f"Password reset failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Password Reset Request", "ERROR", "", str(e))
            return False
    
    def test_two_factor_authentication(self) -> bool:
        """Test two-factor authentication (if implemented)"""
        try:
            # Test 2FA setup
            response = self.session.post(f"{self.base_url}/api/auth/2fa/setup")
            
            if response.status_code in [200, 201]:
                self.log_test("2FA Setup", "PASS", "2FA setup successful")
                return True
            elif response.status_code == 404:
                self.log_test("2FA Setup", "SKIP", "2FA not implemented")
                return True
            else:
                self.log_test("2FA Setup", "FAIL", f"2FA setup failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("2FA Setup", "ERROR", "", str(e))
            return False
    
    def test_authentication_bypass_vulnerability(self) -> bool:
        """Test for authentication bypass vulnerabilities"""
        try:
            # Test various bypass attempts
            bypass_attempts = [
                # Direct access to protected endpoints
                ('/api/auth/profile', 'GET'),
                ('/api/dashboard', 'GET'),
                ('/api/user/settings', 'GET'),
                
                # API endpoints with bypass headers
                ('/api/auth/profile', 'GET', {'X-Admin': 'true'}),
                ('/api/auth/profile', 'GET', {'Authorization': 'Bearer bypass'}),
                ('/api/auth/profile', 'GET', {'X-User-ID': '1'}),
                
                # Parameter manipulation
                ('/api/auth/profile?user_id=1', 'GET'),
                ('/api/auth/profile?admin=true', 'GET'),
                ('/api/auth/profile?bypass=1', 'GET'),
            ]
            
            vulnerable_endpoints = []
            
            for attempt in bypass_attempts:
                try:
                    if len(attempt) == 2:
                        endpoint, method = attempt
                        headers = {}
                    else:
                        endpoint, method, headers = attempt
                    
                    if method == 'GET':
                        response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                    elif method == 'POST':
                        response = self.session.post(f"{self.base_url}{endpoint}", headers=headers)
                    
                    # Check if we got unauthorized access
                    if response.status_code == 200 and 'error' not in response.text.lower():
                        vulnerable_endpoints.append(f"{method} {endpoint}")
                        
                except Exception:
                    pass
            
            if vulnerable_endpoints:
                self.log_test("Authentication Bypass", "CRITICAL", 
                            f"Found {len(vulnerable_endpoints)} potential bypass vulnerabilities")
                for endpoint in vulnerable_endpoints:
                    self.log_test("  - Bypass Found", "CRITICAL", endpoint)
                return False
            else:
                self.log_test("Authentication Bypass", "PASS", "No bypass vulnerabilities detected")
                return True
                
        except Exception as e:
            self.log_test("Authentication Bypass", "ERROR", "", str(e))
            return False
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting on authentication endpoints"""
        try:
            # Test rapid login attempts
            login_data = {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
            
            responses = []
            for i in range(10):  # Make 10 rapid requests
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json=login_data,
                    headers={'Content-Type': 'application/json'}
                )
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay
            
            # Check if rate limiting is in effect
            if 429 in responses:  # 429 = Too Many Requests
                self.log_test("Rate Limiting", "PASS", "Rate limiting is active")
                return True
            else:
                self.log_test("Rate Limiting", "WARN", "Rate limiting may not be active")
                return False
                
        except Exception as e:
            self.log_test("Rate Limiting", "ERROR", "", str(e))
            return False
    
    def test_security_headers(self) -> bool:
        """Test for security headers"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            security_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_test("Security Headers", "WARN", f"Missing headers: {', '.join(missing_headers)}")
                return False
            else:
                self.log_test("Security Headers", "PASS", "All security headers present")
                return True
                
        except Exception as e:
            self.log_test("Security Headers", "ERROR", "", str(e))
            return False
    
    def test_email_verification(self) -> bool:
        """Test email verification flow (if implemented)"""
        try:
            # Test email verification endpoint
            response = self.session.get(f"{self.base_url}/api/auth/verify-email?token=test")
            
            if response.status_code == 404:
                self.log_test("Email Verification", "SKIP", "Email verification not implemented")
                return True
            elif response.status_code in [200, 400]:  # 400 for invalid token
                self.log_test("Email Verification", "PASS", "Email verification endpoint exists")
                return True
            else:
                self.log_test("Email Verification", "FAIL", f"Email verification failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Email Verification", "ERROR", "", str(e))
            return False
    
    def run_comprehensive_test_suite(self) -> Dict[str, any]:
        """Run the complete authentication test suite"""
        print("🔐 MINGUS Authentication Flow Test Suite")
        print("=" * 50)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        # Test execution order
        tests = [
            ("Endpoint Availability", self.test_endpoint_availability),
            ("User Registration", self.test_user_registration),
            ("Registration Validation", self.test_registration_validation),
            ("User Login", self.test_user_login),
            ("Login Validation", self.test_login_validation),
            ("Session Management", self.test_session_management),
            ("Security Headers", self.test_security_headers),
            ("Rate Limiting", self.test_rate_limiting),
            ("Authentication Bypass", self.test_authentication_bypass_vulnerability),
            ("Email Verification", self.test_email_verification),
            ("Password Reset Flow", self.test_password_reset_flow),
            ("Two-Factor Authentication", self.test_two_factor_authentication),
            ("User Logout", self.test_user_logout),
        ]
        
        results = {
            'total_tests': len(tests),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'critical_issues': 0,
            'test_results': []
        }
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['errors'] += 1
                self.log_test(test_name, "ERROR", "", str(e))
        
        # Count results by status
        for result in self.test_results:
            if result['status'] == 'SKIP':
                results['skipped'] += 1
            elif result['status'] == 'CRITICAL':
                results['critical_issues'] += 1
        
        # Generate summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {results['errors']}")
        print(f"Critical Issues: {results['critical_issues']}")
        
        # Show critical issues
        if results['critical_issues'] > 0:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for result in self.test_results:
                if result['status'] == 'CRITICAL':
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # Overall assessment
        if results['critical_issues'] > 0:
            print("\n❌ AUTHENTICATION SYSTEM: CRITICAL ISSUES DETECTED")
            print("   Immediate action required before production deployment")
        elif results['failed'] > 0:
            print("\n⚠️  AUTHENTICATION SYSTEM: ISSUES DETECTED")
            print("   Review and fix issues before production deployment")
        else:
            print("\n✅ AUTHENTICATION SYSTEM: PASSED ALL TESTS")
            print("   Ready for production deployment")
        
        results['test_results'] = self.test_results
        return results

def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MINGUS Authentication Flow Test Suite')
    parser.add_argument('--url', default='http://localhost:5002', 
                       help='Base URL of the MINGUS application')
    parser.add_argument('--output', help='Output file for test results (JSON)')
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = MingusAuthTester(args.url)
    
    # Run comprehensive test suite
    results = tester.run_comprehensive_test_suite()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to: {args.output}")
    
    # Exit with appropriate code
    if results['critical_issues'] > 0:
        sys.exit(1)  # Critical issues found
    elif results['failed'] > 0:
        sys.exit(2)  # Issues found but not critical
    else:
        sys.exit(0)  # All tests passed

if __name__ == "__main__":
    main()
