#!/usr/bin/env python3
"""
Critical Authentication Issues Testing Suite
Tests the specific authentication vulnerabilities mentioned in the status report:
- Authentication bypass vulnerability in test mode
- Session management consistency
- JWT token handling
- Logout functionality
- Concurrent session handling
- Authentication decorators
"""

import requests
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import jwt
import secrets
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('critical_auth_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, ERROR, WARNING
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL

class CriticalAuthenticationTester:
    """Comprehensive authentication vulnerability tester"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.auth_tokens = {}
        self.session_ids = {}
        
        # Test configuration
        self.test_user = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        # Test mode indicators
        self.test_mode_indicators = [
            'TEST_MODE',
            'DEBUG',
            'DEVELOPMENT',
            'BYPASS_AUTH',
            'SKIP_AUTH',
            'TESTING'
        ]
    
    def log_test(self, test_name: str, status: str, description: str, details: Dict[str, Any] = None, severity: str = "MEDIUM"):
        """Log test result"""
        result = TestResult(
            test_name=test_name,
            status=status,
            description=description,
            details=details or {},
            timestamp=datetime.now(),
            severity=severity
        )
        self.test_results.append(result)
        
        # Log to console
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'ERROR': '💥',
            'WARNING': '⚠️'
        }
        
        logger.info(f"{status_emoji.get(status, '❓')} {test_name}: {status} - {description}")
        
        if details:
            logger.debug(f"Details: {json.dumps(details, indent=2)}")
    
    def test_authentication_bypass_in_test_mode(self) -> bool:
        """Test for authentication bypass vulnerability in test mode"""
        logger.info("🔍 Testing authentication bypass vulnerability in test mode...")
        
        try:
            bypass_vulnerabilities = []
            
            # Test 1: Check for test mode environment variables
            test_mode_vars = {}
            for var in self.test_mode_indicators:
                # Try to detect test mode through various methods
                test_endpoints = [
                    f"/api/config/{var.lower()}",
                    f"/api/debug/{var.lower()}",
                    f"/api/test/{var.lower()}",
                    f"/api/admin/{var.lower()}"
                ]
                
                for endpoint in test_endpoints:
                    try:
                        response = self.session.get(f"{self.base_url}{endpoint}")
                        if response.status_code == 200:
                            test_mode_vars[var] = response.text
                    except:
                        pass
            
            if test_mode_vars:
                bypass_vulnerabilities.append(f"Test mode variables exposed: {list(test_mode_vars.keys())}")
            
            # Test 2: Check for bypass headers in test mode
            bypass_headers = [
                {'X-Test-Mode': 'true'},
                {'X-Debug': 'true'},
                {'X-Bypass-Auth': 'true'},
                {'X-Admin': 'true'},
                {'Authorization': 'Bearer test_mode_token'},
                {'X-User-ID': 'admin'},
                {'X-Role': 'admin'}
            ]
            
            protected_endpoints = [
                '/api/auth/profile',
                '/api/dashboard',
                '/api/user/settings',
                '/api/admin/users',
                '/api/assessment/results'
            ]
            
            for endpoint in protected_endpoints:
                for headers in bypass_headers:
                    try:
                        response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                        if response.status_code == 200:
                            bypass_vulnerabilities.append(f"Bypass successful: {endpoint} with headers {headers}")
                    except:
                        pass
            
            # Test 3: Check for test mode in configuration endpoints
            config_endpoints = [
                '/api/config',
                '/api/debug/config',
                '/api/test/config',
                '/api/admin/config'
            ]
            
            for endpoint in config_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        config_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        if any(indicator.lower() in str(config_data).lower() for indicator in self.test_mode_indicators):
                            bypass_vulnerabilities.append(f"Test mode config exposed: {endpoint}")
                except:
                    pass
            
            # Test 4: Check for authentication bypass in error messages
            try:
                response = self.session.get(f"{self.base_url}/api/auth/profile")
                if response.status_code != 401:
                    bypass_vulnerabilities.append("Protected endpoint accessible without authentication")
            except:
                pass
            
            if bypass_vulnerabilities:
                self.log_test(
                    "Authentication Bypass in Test Mode", 
                    "CRITICAL", 
                    f"Found {len(bypass_vulnerabilities)} bypass vulnerabilities",
                    {"vulnerabilities": bypass_vulnerabilities},
                    "CRITICAL"
                )
                return False
            else:
                self.log_test(
                    "Authentication Bypass in Test Mode", 
                    "PASS", 
                    "No authentication bypass vulnerabilities detected in test mode"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Authentication Bypass in Test Mode", 
                "ERROR", 
                f"Error testing authentication bypass: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_session_management_consistency(self) -> bool:
        """Test session management consistency"""
        logger.info("🔍 Testing session management consistency...")
        
        try:
            session_issues = []
            
            # Test 1: Login and verify session creation
            login_response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=self.test_user,
                headers={'Content-Type': 'application/json'}
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                session_id = login_response.cookies.get('session_id')
                token = login_data.get('token')
                
                if session_id:
                    self.session_ids['primary'] = session_id
                if token:
                    self.auth_tokens['primary'] = token
                
                # Test 2: Verify session consistency across requests
                profile_response = self.session.get(f"{self.base_url}/api/auth/profile")
                if profile_response.status_code != 200:
                    session_issues.append("Session not maintained after login")
                
                # Test 3: Check session timeout behavior
                # Simulate session timeout by manipulating session data
                if session_id:
                    # Try to access with expired session
                    expired_session = requests.Session()
                    expired_session.cookies.set('session_id', session_id)
                    
                    # Wait a moment and test
                    time.sleep(1)
                    expired_response = expired_session.get(f"{self.base_url}/api/auth/profile")
                    if expired_response.status_code == 200:
                        session_issues.append("Expired session still valid")
                
                # Test 4: Check session regeneration
                # Make multiple requests to see if session ID changes
                session_ids = []
                for i in range(5):
                    response = self.session.get(f"{self.base_url}/api/auth/profile")
                    current_session_id = response.cookies.get('session_id')
                    if current_session_id:
                        session_ids.append(current_session_id)
                    time.sleep(0.1)
                
                if len(set(session_ids)) > 1:
                    session_issues.append("Session ID changing unexpectedly")
                
            else:
                session_issues.append(f"Login failed: {login_response.status_code}")
            
            if session_issues:
                self.log_test(
                    "Session Management Consistency", 
                    "FAIL", 
                    f"Found {len(session_issues)} session management issues",
                    {"issues": session_issues}
                )
                return False
            else:
                self.log_test(
                    "Session Management Consistency", 
                    "PASS", 
                    "Session management is consistent"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Session Management Consistency", 
                "ERROR", 
                f"Error testing session management: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_jwt_token_handling(self) -> bool:
        """Test JWT token handling"""
        logger.info("🔍 Testing JWT token handling...")
        
        try:
            jwt_issues = []
            
            # Test 1: Verify JWT token structure
            if 'primary' in self.auth_tokens:
                token = self.auth_tokens['primary']
                
                try:
                    # Decode token without verification to check structure
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    
                    required_claims = ['sub', 'iat', 'exp', 'iss', 'aud']
                    missing_claims = [claim for claim in required_claims if claim not in decoded]
                    
                    if missing_claims:
                        jwt_issues.append(f"Missing JWT claims: {missing_claims}")
                    
                    # Check token expiration
                    exp_time = datetime.fromtimestamp(decoded['exp'])
                    if exp_time < datetime.now():
                        jwt_issues.append("JWT token already expired")
                    
                except jwt.InvalidTokenError as e:
                    jwt_issues.append(f"Invalid JWT token: {str(e)}")
            
            # Test 2: Test token refresh
            try:
                refresh_response = self.session.post(
                    f"{self.base_url}/api/auth/refresh",
                    headers={'Authorization': f'Bearer {self.auth_tokens.get("primary", "")}'}
                )
                
                if refresh_response.status_code == 200:
                    refresh_data = refresh_response.json()
                    new_token = refresh_data.get('token')
                    if new_token and new_token != self.auth_tokens.get('primary'):
                        self.auth_tokens['refreshed'] = new_token
                    else:
                        jwt_issues.append("Token refresh not working properly")
                else:
                    jwt_issues.append(f"Token refresh failed: {refresh_response.status_code}")
                    
            except Exception as e:
                jwt_issues.append(f"Token refresh error: {str(e)}")
            
            # Test 3: Test invalid token handling
            invalid_tokens = [
                'invalid_token',
                'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
                'Bearer invalid',
                ''
            ]
            
            for invalid_token in invalid_tokens:
                try:
                    response = self.session.get(
                        f"{self.base_url}/api/auth/profile",
                        headers={'Authorization': f'Bearer {invalid_token}'}
                    )
                    if response.status_code == 200:
                        jwt_issues.append(f"Invalid token accepted: {invalid_token[:20]}...")
                except:
                    pass
            
            # Test 4: Test token revocation
            if 'primary' in self.auth_tokens:
                try:
                    logout_response = self.session.post(f"{self.base_url}/api/auth/logout")
                    if logout_response.status_code == 200:
                        # Try to use the token after logout
                        response = self.session.get(
                            f"{self.base_url}/api/auth/profile",
                            headers={'Authorization': f'Bearer {self.auth_tokens["primary"]}'}
                        )
                        if response.status_code == 200:
                            jwt_issues.append("Token still valid after logout")
                except Exception as e:
                    jwt_issues.append(f"Token revocation error: {str(e)}")
            
            if jwt_issues:
                self.log_test(
                    "JWT Token Handling", 
                    "FAIL", 
                    f"Found {len(jwt_issues)} JWT handling issues",
                    {"issues": jwt_issues}
                )
                return False
            else:
                self.log_test(
                    "JWT Token Handling", 
                    "PASS", 
                    "JWT token handling is secure"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "JWT Token Handling", 
                "ERROR", 
                f"Error testing JWT handling: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_logout_functionality(self) -> bool:
        """Test logout functionality"""
        logger.info("🔍 Testing logout functionality...")
        
        try:
            logout_issues = []
            
            # Test 1: Test normal logout
            try:
                logout_response = self.session.post(f"{self.base_url}/api/auth/logout")
                
                if logout_response.status_code != 200:
                    logout_issues.append(f"Logout failed: {logout_response.status_code}")
                else:
                    # Verify logout was effective
                    profile_response = self.session.get(f"{self.base_url}/api/auth/profile")
                    if profile_response.status_code == 200:
                        logout_issues.append("User still authenticated after logout")
                    
                    # Check if session cookie was cleared
                    session_cookie = self.session.cookies.get('session_id')
                    if session_cookie:
                        logout_issues.append("Session cookie not cleared after logout")
                    
                    # Check if JWT token was invalidated
                    if 'primary' in self.auth_tokens:
                        response = self.session.get(
                            f"{self.base_url}/api/auth/profile",
                            headers={'Authorization': f'Bearer {self.auth_tokens["primary"]}'}
                        )
                        if response.status_code == 200:
                            logout_issues.append("JWT token still valid after logout")
                            
            except Exception as e:
                logout_issues.append(f"Logout error: {str(e)}")
            
            # Test 2: Test logout with invalid session
            try:
                invalid_session = requests.Session()
                logout_response = invalid_session.post(f"{self.base_url}/api/auth/logout")
                
                if logout_response.status_code not in [200, 401, 403]:
                    logout_issues.append(f"Unexpected response for invalid logout: {logout_response.status_code}")
                    
            except Exception as e:
                logout_issues.append(f"Invalid logout error: {str(e)}")
            
            # Test 3: Test logout from multiple sessions
            try:
                # Create multiple sessions
                sessions = []
                for i in range(3):
                    session = requests.Session()
                    login_response = session.post(
                        f"{self.base_url}/api/auth/login",
                        json=self.test_user,
                        headers={'Content-Type': 'application/json'}
                    )
                    if login_response.status_code == 200:
                        sessions.append(session)
                
                # Logout from one session
                if sessions:
                    logout_response = sessions[0].post(f"{self.base_url}/api/auth/logout")
                    if logout_response.status_code == 200:
                        # Check if other sessions are still valid
                        for i, session in enumerate(sessions[1:], 1):
                            profile_response = session.get(f"{self.base_url}/api/auth/profile")
                            if profile_response.status_code != 200:
                                logout_issues.append(f"Logout affected other sessions: session {i}")
                                
            except Exception as e:
                logout_issues.append(f"Multi-session logout error: {str(e)}")
            
            if logout_issues:
                self.log_test(
                    "Logout Functionality", 
                    "FAIL", 
                    f"Found {len(logout_issues)} logout issues",
                    {"issues": logout_issues}
                )
                return False
            else:
                self.log_test(
                    "Logout Functionality", 
                    "PASS", 
                    "Logout functionality works correctly"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Logout Functionality", 
                "ERROR", 
                f"Error testing logout: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_concurrent_session_handling(self) -> bool:
        """Test concurrent session handling"""
        logger.info("🔍 Testing concurrent session handling...")
        
        try:
            concurrent_issues = []
            
            # Test 1: Create multiple concurrent sessions
            sessions = []
            session_results = []
            
            def create_session(session_id):
                try:
                    session = requests.Session()
                    login_response = session.post(
                        f"{self.base_url}/api/auth/login",
                        json=self.test_user,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if login_response.status_code == 200:
                        profile_response = session.get(f"{self.base_url}/api/auth/profile")
                        session_results.append({
                            'session_id': session_id,
                            'login_success': True,
                            'profile_success': profile_response.status_code == 200,
                            'session_cookie': login_response.cookies.get('session_id')
                        })
                    else:
                        session_results.append({
                            'session_id': session_id,
                            'login_success': False,
                            'profile_success': False
                        })
                except Exception as e:
                    session_results.append({
                        'session_id': session_id,
                        'login_success': False,
                        'profile_success': False,
                        'error': str(e)
                    })
            
            # Create 5 concurrent sessions
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_session, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Analyze results
            successful_sessions = [r for r in session_results if r['login_success']]
            if len(successful_sessions) > 3:  # Assuming max 3 concurrent sessions
                concurrent_issues.append(f"Too many concurrent sessions allowed: {len(successful_sessions)}")
            
            # Check for session conflicts
            session_cookies = [r['session_cookie'] for r in successful_sessions if r.get('session_cookie')]
            if len(set(session_cookies)) != len(session_cookies):
                concurrent_issues.append("Session ID conflicts detected")
            
            # Test 2: Test session limits
            try:
                # Try to create more sessions than allowed
                extra_sessions = []
                for i in range(10):
                    session = requests.Session()
                    login_response = session.post(
                        f"{self.base_url}/api/auth/login",
                        json=self.test_user,
                        headers={'Content-Type': 'application/json'}
                    )
                    if login_response.status_code == 200:
                        extra_sessions.append(session)
                
                if len(extra_sessions) > 5:  # Assuming reasonable limit
                    concurrent_issues.append(f"Too many sessions created: {len(extra_sessions)}")
                    
            except Exception as e:
                concurrent_issues.append(f"Session limit test error: {str(e)}")
            
            # Test 3: Test session invalidation on new login
            try:
                # Create a session
                session1 = requests.Session()
                login1 = session1.post(
                    f"{self.base_url}/api/auth/login",
                    json=self.test_user,
                    headers={'Content-Type': 'application/json'}
                )
                
                if login1.status_code == 200:
                    # Create another session (should invalidate the first)
                    session2 = requests.Session()
                    login2 = session2.post(
                        f"{self.base_url}/api/auth/login",
                        json=self.test_user,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if login2.status_code == 200:
                        # Check if first session is still valid
                        profile1 = session1.get(f"{self.base_url}/api/auth/profile")
                        if profile1.status_code == 200:
                            concurrent_issues.append("Old session still valid after new login")
                            
            except Exception as e:
                concurrent_issues.append(f"Session invalidation test error: {str(e)}")
            
            if concurrent_issues:
                self.log_test(
                    "Concurrent Session Handling", 
                    "FAIL", 
                    f"Found {len(concurrent_issues)} concurrent session issues",
                    {"issues": concurrent_issues}
                )
                return False
            else:
                self.log_test(
                    "Concurrent Session Handling", 
                    "PASS", 
                    "Concurrent session handling works correctly"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Concurrent Session Handling", 
                "ERROR", 
                f"Error testing concurrent sessions: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_authentication_decorators(self) -> bool:
        """Test authentication decorators"""
        logger.info("🔍 Testing authentication decorators...")
        
        try:
            decorator_issues = []
            
            # Test 1: Test @require_auth decorator
            protected_endpoints = [
                '/api/auth/profile',
                '/api/dashboard',
                '/api/user/settings',
                '/api/assessment/results'
            ]
            
            for endpoint in protected_endpoints:
                try:
                    # Test without authentication
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        decorator_issues.append(f"@require_auth failed: {endpoint} accessible without auth")
                    elif response.status_code not in [401, 403]:
                        decorator_issues.append(f"@require_auth unexpected response: {endpoint} returned {response.status_code}")
                        
                except Exception as e:
                    decorator_issues.append(f"@require_auth test error for {endpoint}: {str(e)}")
            
            # Test 2: Test @require_assessment_auth decorator
            assessment_endpoints = [
                '/api/assessment/submit',
                '/api/assessment/start',
                '/api/assessment/pause'
            ]
            
            for endpoint in assessment_endpoints:
                try:
                    # Test without authentication
                    response = self.session.post(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        decorator_issues.append(f"@require_assessment_auth failed: {endpoint} accessible without auth")
                    elif response.status_code not in [401, 403, 400]:  # 400 for missing assessment_id
                        decorator_issues.append(f"@require_assessment_auth unexpected response: {endpoint} returned {response.status_code}")
                        
                except Exception as e:
                    decorator_issues.append(f"@require_assessment_auth test error for {endpoint}: {str(e)}")
            
            # Test 3: Test @require_secure_auth decorator
            secure_endpoints = [
                '/api/admin/users',
                '/api/admin/settings',
                '/api/admin/logs'
            ]
            
            for endpoint in secure_endpoints:
                try:
                    # Test without authentication
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        decorator_issues.append(f"@require_secure_auth failed: {endpoint} accessible without auth")
                    elif response.status_code not in [401, 403]:
                        decorator_issues.append(f"@require_secure_auth unexpected response: {endpoint} returned {response.status_code}")
                        
                except Exception as e:
                    decorator_issues.append(f"@require_secure_auth test error for {endpoint}: {str(e)}")
            
            # Test 4: Test decorators with valid authentication
            if 'primary' in self.auth_tokens:
                try:
                    # Login to get valid session
                    login_response = self.session.post(
                        f"{self.base_url}/api/auth/login",
                        json=self.test_user,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if login_response.status_code == 200:
                        # Test protected endpoints with valid auth
                        for endpoint in protected_endpoints:
                            response = self.session.get(f"{self.base_url}{endpoint}")
                            if response.status_code not in [200, 404]:  # 404 for non-existent endpoints
                                decorator_issues.append(f"@require_auth blocking valid auth: {endpoint} returned {response.status_code}")
                                
                except Exception as e:
                    decorator_issues.append(f"Valid auth test error: {str(e)}")
            
            if decorator_issues:
                self.log_test(
                    "Authentication Decorators", 
                    "FAIL", 
                    f"Found {len(decorator_issues)} decorator issues",
                    {"issues": decorator_issues}
                )
                return False
            else:
                self.log_test(
                    "Authentication Decorators", 
                    "PASS", 
                    "All authentication decorators work properly"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Authentication Decorators", 
                "ERROR", 
                f"Error testing decorators: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all critical authentication tests"""
        logger.info("🚀 Starting Critical Authentication Issues Testing Suite")
        
        test_functions = [
            ("Authentication Bypass in Test Mode", self.test_authentication_bypass_in_test_mode),
            ("Session Management Consistency", self.test_session_management_consistency),
            ("JWT Token Handling", self.test_jwt_token_handling),
            ("Logout Functionality", self.test_logout_functionality),
            ("Concurrent Session Handling", self.test_concurrent_session_handling),
            ("Authentication Decorators", self.test_authentication_decorators)
        ]
        
        results = {
            'total_tests': len(test_functions),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'warnings': 0,
            'test_results': []
        }
        
        for test_name, test_func in test_functions:
            try:
                success = test_func()
                if success:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error running {test_name}: {str(e)}")
                results['errors'] += 1
        
        # Generate summary
        results['summary'] = {
            'overall_status': 'PASS' if results['failed'] == 0 and results['errors'] == 0 else 'FAIL',
            'success_rate': (results['passed'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
        }
        
        # Save results
        self.save_results(results)
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Save test results to file"""
        try:
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'test_suite': 'Critical Authentication Issues',
                'results': results,
                'detailed_results': [asdict(result) for result in self.test_results]
            }
            
            filename = f"critical_auth_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            logger.info(f"Results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")

def main():
    """Main function to run the critical authentication tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Critical Authentication Issues Testing Suite')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of the application')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tester and run tests
    tester = CriticalAuthenticationTester(args.url)
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("CRITICAL AUTHENTICATION ISSUES TESTING SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Errors: {results['errors']} 💥")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {results['summary']['overall_status']}")
    print("="*60)
    
    if results['failed'] > 0 or results['errors'] > 0:
        print("\n🚨 CRITICAL ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
        print("Please review the detailed test results and fix the identified vulnerabilities.")
        return 1
    else:
        print("\n✅ All critical authentication tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())
