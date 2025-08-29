#!/usr/bin/env python3
"""
Comprehensive CSRF Protection Testing Suite
===========================================

This script tests CSRF protection across the entire MINGUS application:

1. Financial transaction endpoints CSRF protection
2. Form submissions security
3. API endpoint protection
4. State-changing operations security
5. Cross-origin request handling
6. Token validation and rotation

Author: Security Testing Team
Date: January 2025
"""

import os
import sys
import json
import time
import secrets
import hmac
import hashlib
import requests
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import threading
import concurrent.futures

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.security.csrf_protection import CSRFProtection

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, ERROR
    details: str
    timestamp: datetime
    endpoint: str
    method: str
    expected_behavior: str
    actual_behavior: str
    security_impact: str
    recommendations: List[str]

class CSRFProtectionTester:
    """Comprehensive CSRF protection testing suite"""
    
    def __init__(self, base_url: str, secret_key: str):
        self.base_url = base_url.rstrip('/')
        self.secret_key = secret_key
        self.session = requests.Session()
        self.csrf_protection = CSRFProtection(secret_key)
        self.test_results: List[TestResult] = []
        
        # Test configuration
        self.test_config = {
            'timeout': 30,
            'max_retries': 3,
            'concurrent_requests': 5,
            'token_lifetime': 3600,
            'malicious_origins': [
                'https://malicious-site.com',
                'https://evil.com',
                'http://localhost:8080',
                'https://attacker.com'
            ]
        }
        
        # Financial endpoints to test
        self.financial_endpoints = [
            '/api/payment/customers',
            '/api/payment/subscriptions',
            '/api/payment/process-payment',
            '/api/secure/financial-profile',
            '/api/banking/connect-account',
            '/api/banking/transfer-funds',
            '/api/subscription/upgrade',
            '/api/subscription/cancel'
        ]
        
        # State-changing endpoints
        self.state_changing_endpoints = [
            '/api/user/profile',
            '/api/assessment/submit',
            '/api/communication/preferences',
            '/api/banking/disconnect-account',
            '/api/analytics/export-data',
            '/api/admin/user-management'
        ]
        
        # Form submission endpoints
        self.form_endpoints = [
            '/api/onboarding/complete',
            '/api/goals/set',
            '/api/questionnaire/submit',
            '/api/health/update-profile'
        ]
    
    def log_test_result(self, result: TestResult):
        """Log test result and add to results list"""
        self.test_results.append(result)
        
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'ERROR': '⚠️'
        }
        
        print(f"{status_emoji.get(result.status, '❓')} {result.test_name}")
        print(f"   Endpoint: {result.method} {result.endpoint}")
        print(f"   Status: {result.status}")
        print(f"   Details: {result.details}")
        if result.security_impact:
            print(f"   Security Impact: {result.security_impact}")
        print()
    
    def generate_valid_csrf_token(self, session_id: str = None) -> str:
        """Generate a valid CSRF token for testing"""
        return self.csrf_protection.generate_csrf_token(session_id)
    
    def generate_invalid_csrf_token(self) -> str:
        """Generate an invalid CSRF token for testing"""
        return "invalid:token:signature"
    
    def generate_expired_csrf_token(self) -> str:
        """Generate an expired CSRF token for testing"""
        session_id = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()) - 7200)  # 2 hours ago
        token_data = f"{session_id}:{timestamp}"
        
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token_data}:{signature}"
    
    def test_financial_transaction_csrf_protection(self):
        """Test CSRF protection on financial transaction endpoints"""
        print("🔒 Testing Financial Transaction CSRF Protection")
        print("=" * 60)
        
        for endpoint in self.financial_endpoints:
            # Test 1: Request without CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=None,
                test_name=f"Financial Transaction - No CSRF Token - {endpoint}",
                expected_status=403,
                expected_behavior="Should reject request without CSRF token"
            )
            
            # Test 2: Request with invalid CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=self.generate_invalid_csrf_token(),
                test_name=f"Financial Transaction - Invalid CSRF Token - {endpoint}",
                expected_status=403,
                expected_behavior="Should reject request with invalid CSRF token"
            )
            
            # Test 3: Request with expired CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=self.generate_expired_csrf_token(),
                test_name=f"Financial Transaction - Expired CSRF Token - {endpoint}",
                expected_status=403,
                expected_behavior="Should reject request with expired CSRF token"
            )
            
            # Test 4: Request with valid CSRF token (should pass if authenticated)
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=self.generate_valid_csrf_token(),
                test_name=f"Financial Transaction - Valid CSRF Token - {endpoint}",
                expected_status=[200, 201, 401, 403],  # Multiple acceptable responses
                expected_behavior="Should accept request with valid CSRF token (may fail for auth reasons)"
            )
    
    def test_form_submissions_security(self):
        """Test CSRF protection on form submission endpoints"""
        print("📝 Testing Form Submissions CSRF Protection")
        print("=" * 60)
        
        for endpoint in self.form_endpoints:
            # Test form submission without CSRF token
            self._test_form_submission(
                endpoint=endpoint,
                form_data={'test_field': 'test_value'},
                csrf_token=None,
                test_name=f"Form Submission - No CSRF Token - {endpoint}",
                expected_status=403
            )
            
            # Test form submission with invalid CSRF token
            self._test_form_submission(
                endpoint=endpoint,
                form_data={'test_field': 'test_value'},
                csrf_token=self.generate_invalid_csrf_token(),
                test_name=f"Form Submission - Invalid CSRF Token - {endpoint}",
                expected_status=403
            )
            
            # Test form submission with valid CSRF token
            self._test_form_submission(
                endpoint=endpoint,
                form_data={'test_field': 'test_value'},
                csrf_token=self.generate_valid_csrf_token(),
                test_name=f"Form Submission - Valid CSRF Token - {endpoint}",
                expected_status=[200, 201, 401, 403]
            )
    
    def test_api_endpoint_protection(self):
        """Test CSRF protection on general API endpoints"""
        print("🔌 Testing API Endpoint CSRF Protection")
        print("=" * 60)
        
        api_endpoints = [
            '/api/user/profile',
            '/api/assessment/submit',
            '/api/analytics/export',
            '/api/communication/send',
            '/api/admin/users'
        ]
        
        for endpoint in api_endpoints:
            # Test API call without CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=None,
                test_name=f"API Endpoint - No CSRF Token - {endpoint}",
                expected_status=403,
                expected_behavior="Should reject API call without CSRF token"
            )
            
            # Test API call with valid CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=self.generate_valid_csrf_token(),
                test_name=f"API Endpoint - Valid CSRF Token - {endpoint}",
                expected_status=[200, 201, 401, 403],
                expected_behavior="Should accept API call with valid CSRF token"
            )
    
    def test_state_changing_operations(self):
        """Test CSRF protection on state-changing operations"""
        print("🔄 Testing State-Changing Operations CSRF Protection")
        print("=" * 60)
        
        for endpoint in self.state_changing_endpoints:
            # Test state change without CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=None,
                test_name=f"State Change - No CSRF Token - {endpoint}",
                expected_status=403,
                expected_behavior="Should reject state-changing operation without CSRF token"
            )
            
            # Test state change with valid CSRF token
            self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method='POST',
                csrf_token=self.generate_valid_csrf_token(),
                test_name=f"State Change - Valid CSRF Token - {endpoint}",
                expected_status=[200, 201, 401, 403],
                expected_behavior="Should accept state-changing operation with valid CSRF token"
            )
    
    def test_cross_origin_request_handling(self):
        """Test cross-origin request handling and CSRF protection"""
        print("🌐 Testing Cross-Origin Request Handling")
        print("=" * 60)
        
        for origin in self.test_config['malicious_origins']:
            for endpoint in self.financial_endpoints[:3]:  # Test subset for performance
                # Test cross-origin request with CSRF token
                self._test_cross_origin_request(
                    endpoint=endpoint,
                    origin=origin,
                    csrf_token=self.generate_valid_csrf_token(),
                    test_name=f"Cross-Origin Request - {origin} - {endpoint}",
                    expected_behavior="Should handle cross-origin requests appropriately"
                )
    
    def test_token_validation_and_rotation(self):
        """Test CSRF token validation and rotation mechanisms"""
        print("🔄 Testing Token Validation and Rotation")
        print("=" * 60)
        
        # Test token generation
        token1 = self.generate_valid_csrf_token()
        token2 = self.generate_valid_csrf_token()
        
        # Verify tokens are different
        if token1 != token2:
            self.log_test_result(TestResult(
                test_name="Token Generation - Unique Tokens",
                status="PASS",
                details="Generated tokens are unique",
                timestamp=datetime.now(),
                endpoint="/api/csrf/generate",
                method="POST",
                expected_behavior="Each token generation should produce unique tokens",
                actual_behavior="Tokens are unique",
                security_impact="Good - prevents token reuse attacks",
                recommendations=[]
            ))
        else:
            self.log_test_result(TestResult(
                test_name="Token Generation - Unique Tokens",
                status="FAIL",
                details="Generated tokens are identical",
                timestamp=datetime.now(),
                endpoint="/api/csrf/generate",
                method="POST",
                expected_behavior="Each token generation should produce unique tokens",
                actual_behavior="Tokens are identical",
                security_impact="Critical - allows token reuse attacks",
                recommendations=["Fix token generation to ensure uniqueness"]
            ))
        
        # Test token validation
        valid_token = self.generate_valid_csrf_token()
        if self.csrf_protection.validate_csrf_token(valid_token):
            self.log_test_result(TestResult(
                test_name="Token Validation - Valid Token",
                status="PASS",
                details="Valid token passes validation",
                timestamp=datetime.now(),
                endpoint="/api/csrf/validate",
                method="POST",
                expected_behavior="Valid tokens should pass validation",
                actual_behavior="Token validation successful",
                security_impact="Good - proper validation",
                recommendations=[]
            ))
        else:
            self.log_test_result(TestResult(
                test_name="Token Validation - Valid Token",
                status="FAIL",
                details="Valid token fails validation",
                timestamp=datetime.now(),
                endpoint="/api/csrf/validate",
                method="POST",
                expected_behavior="Valid tokens should pass validation",
                actual_behavior="Token validation failed",
                security_impact="Critical - valid tokens rejected",
                recommendations=["Fix token validation logic"]
            ))
        
        # Test invalid token rejection
        invalid_token = self.generate_invalid_csrf_token()
        if not self.csrf_protection.validate_csrf_token(invalid_token):
            self.log_test_result(TestResult(
                test_name="Token Validation - Invalid Token",
                status="PASS",
                details="Invalid token correctly rejected",
                timestamp=datetime.now(),
                endpoint="/api/csrf/validate",
                method="POST",
                expected_behavior="Invalid tokens should be rejected",
                actual_behavior="Invalid token rejected",
                security_impact="Good - proper validation",
                recommendations=[]
            ))
        else:
            self.log_test_result(TestResult(
                test_name="Token Validation - Invalid Token",
                status="FAIL",
                details="Invalid token incorrectly accepted",
                timestamp=datetime.now(),
                endpoint="/api/csrf/validate",
                method="POST",
                expected_behavior="Invalid tokens should be rejected",
                actual_behavior="Invalid token accepted",
                security_impact="Critical - invalid tokens accepted",
                recommendations=["Fix token validation to reject invalid tokens"]
            ))
    
    def test_concurrent_csrf_requests(self):
        """Test CSRF protection under concurrent load"""
        print("⚡ Testing Concurrent CSRF Requests")
        print("=" * 60)
        
        def make_concurrent_request(endpoint: str, csrf_token: str) -> Dict[str, Any]:
            """Make a concurrent request with CSRF token"""
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token
                }
                
                response = self.session.post(
                    urljoin(self.base_url, endpoint),
                    json={'test': 'data'},
                    headers=headers,
                    timeout=self.test_config['timeout']
                )
                
                return {
                    'status_code': response.status_code,
                    'success': response.status_code in [200, 201],
                    'error': None
                }
            except Exception as e:
                return {
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                }
        
        # Generate multiple valid tokens
        tokens = [self.generate_valid_csrf_token() for _ in range(10)]
        endpoint = self.financial_endpoints[0]  # Use first financial endpoint
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.test_config['concurrent_requests']) as executor:
            futures = [
                executor.submit(make_concurrent_request, endpoint, token)
                for token in tokens
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = len(results) - successful_requests
        
        if successful_requests > 0 and failed_requests == 0:
            self.log_test_result(TestResult(
                test_name="Concurrent CSRF Requests",
                status="PASS",
                details=f"All {len(results)} concurrent requests successful",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method="POST",
                expected_behavior="Concurrent requests should be handled properly",
                actual_behavior=f"{successful_requests}/{len(results)} requests successful",
                security_impact="Good - no race conditions detected",
                recommendations=[]
            ))
        else:
            self.log_test_result(TestResult(
                test_name="Concurrent CSRF Requests",
                status="FAIL",
                details=f"{failed_requests}/{len(results)} requests failed",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method="POST",
                expected_behavior="Concurrent requests should be handled properly",
                actual_behavior=f"{successful_requests}/{len(results)} requests successful",
                security_impact="Medium - potential race conditions",
                recommendations=["Investigate concurrent request handling", "Check for race conditions"]
            ))
    
    def _test_endpoint_csrf_protection(self, endpoint: str, method: str, csrf_token: Optional[str], 
                                     test_name: str, expected_status: int, expected_behavior: str):
        """Test CSRF protection on a specific endpoint"""
        try:
            headers = {'Content-Type': 'application/json'}
            
            if csrf_token:
                headers['X-CSRFToken'] = csrf_token
            
            response = self.session.request(
                method=method,
                url=urljoin(self.base_url, endpoint),
                json={'test': 'data'},
                headers=headers,
                timeout=self.test_config['timeout']
            )
            
            # Determine test result
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
            
            if success:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="PASS",
                    details=f"Expected status {expected_status}, got {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method=method,
                    expected_behavior=expected_behavior,
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Good - CSRF protection working as expected",
                    recommendations=[]
                ))
            else:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="FAIL",
                    details=f"Expected status {expected_status}, got {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method=method,
                    expected_behavior=expected_behavior,
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Critical - CSRF protection may be bypassed",
                    recommendations=["Review CSRF protection implementation", "Check endpoint security"]
                ))
                
        except Exception as e:
            self.log_test_result(TestResult(
                test_name=test_name,
                status="ERROR",
                details=f"Request failed: {str(e)}",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method=method,
                expected_behavior=expected_behavior,
                actual_behavior=f"Exception: {str(e)}",
                security_impact="Unknown - request failed",
                recommendations=["Check endpoint availability", "Verify network connectivity"]
            ))
    
    def _test_form_submission(self, endpoint: str, form_data: Dict[str, Any], csrf_token: Optional[str],
                             test_name: str, expected_status: int):
        """Test form submission with CSRF protection"""
        try:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            if csrf_token:
                form_data['csrf_token'] = csrf_token
            
            response = self.session.post(
                url=urljoin(self.base_url, endpoint),
                data=form_data,
                headers=headers,
                timeout=self.test_config['timeout']
            )
            
            success = response.status_code == expected_status
            
            if success:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="PASS",
                    details=f"Form submission status: {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method="POST",
                    expected_behavior="Form submission should respect CSRF protection",
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Good - form CSRF protection working",
                    recommendations=[]
                ))
            else:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="FAIL",
                    details=f"Form submission status: {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method="POST",
                    expected_behavior="Form submission should respect CSRF protection",
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Critical - form CSRF protection may be bypassed",
                    recommendations=["Review form CSRF protection", "Check form validation"]
                ))
                
        except Exception as e:
            self.log_test_result(TestResult(
                test_name=test_name,
                status="ERROR",
                details=f"Form submission failed: {str(e)}",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method="POST",
                expected_behavior="Form submission should respect CSRF protection",
                actual_behavior=f"Exception: {str(e)}",
                security_impact="Unknown - form submission failed",
                recommendations=["Check endpoint availability", "Verify form handling"]
            ))
    
    def _test_cross_origin_request(self, endpoint: str, origin: str, csrf_token: str, 
                                 test_name: str, expected_behavior: str):
        """Test cross-origin request handling"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
                'Origin': origin,
                'Referer': f"{origin}/malicious-page"
            }
            
            response = self.session.post(
                url=urljoin(self.base_url, endpoint),
                json={'test': 'data'},
                headers=headers,
                timeout=self.test_config['timeout']
            )
            
            # Check if request was properly handled
            if response.status_code in [403, 401]:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="PASS",
                    details=f"Cross-origin request properly rejected: {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method="POST",
                    expected_behavior=expected_behavior,
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Good - cross-origin protection working",
                    recommendations=[]
                ))
            elif response.status_code == 200:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="FAIL",
                    details=f"Cross-origin request accepted: {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method="POST",
                    expected_behavior=expected_behavior,
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Critical - cross-origin requests accepted",
                    recommendations=["Implement proper CORS policy", "Review cross-origin protection"]
                ))
            else:
                self.log_test_result(TestResult(
                    test_name=test_name,
                    status="PASS",
                    details=f"Cross-origin request handled: {response.status_code}",
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    method="POST",
                    expected_behavior=expected_behavior,
                    actual_behavior=f"Status code: {response.status_code}",
                    security_impact="Acceptable - request handled appropriately",
                    recommendations=[]
                ))
                
        except Exception as e:
            self.log_test_result(TestResult(
                test_name=test_name,
                status="ERROR",
                details=f"Cross-origin request failed: {str(e)}",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method="POST",
                expected_behavior=expected_behavior,
                actual_behavior=f"Exception: {str(e)}",
                security_impact="Unknown - request failed",
                recommendations=["Check endpoint availability", "Verify CORS configuration"]
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == 'PASS')
        failed_tests = sum(1 for r in self.test_results if r.status == 'FAIL')
        error_tests = sum(1 for r in self.test_results if r.status == 'ERROR')
        
        # Group results by category
        financial_tests = [r for r in self.test_results if 'Financial' in r.test_name]
        form_tests = [r for r in self.test_results if 'Form' in r.test_name]
        api_tests = [r for r in self.test_results if 'API' in r.test_name]
        state_tests = [r for r in self.test_results if 'State' in r.test_name]
        cross_origin_tests = [r for r in self.test_results if 'Cross-Origin' in r.test_name]
        token_tests = [r for r in self.test_results if 'Token' in r.test_name]
        concurrent_tests = [r for r in self.test_results if 'Concurrent' in r.test_name]
        
        # Security recommendations
        all_recommendations = []
        for result in self.test_results:
            all_recommendations.extend(result.recommendations)
        
        unique_recommendations = list(set(all_recommendations))
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'category_breakdown': {
                'financial_transaction_tests': len(financial_tests),
                'form_submission_tests': len(form_tests),
                'api_endpoint_tests': len(api_tests),
                'state_changing_tests': len(state_tests),
                'cross_origin_tests': len(cross_origin_tests),
                'token_validation_tests': len(token_tests),
                'concurrent_request_tests': len(concurrent_tests)
            },
            'security_assessment': {
                'critical_issues': len([r for r in self.test_results if 'Critical' in r.security_impact]),
                'high_issues': len([r for r in self.test_results if 'High' in r.security_impact]),
                'medium_issues': len([r for r in self.test_results if 'Medium' in r.security_impact]),
                'low_issues': len([r for r in self.test_results if 'Low' in r.security_impact])
            },
            'recommendations': unique_recommendations,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'status': r.status,
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'security_impact': r.security_impact,
                    'details': r.details,
                    'recommendations': r.recommendations
                }
                for r in self.test_results
            ],
            'timestamp': datetime.now().isoformat(),
            'test_configuration': self.test_config
        }
        
        return report
    
    def run_all_tests(self):
        """Run all CSRF protection tests"""
        print("🚀 Starting Comprehensive CSRF Protection Testing")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Test Configuration: {json.dumps(self.test_config, indent=2)}")
        print()
        
        start_time = time.time()
        
        # Run all test categories
        self.test_financial_transaction_csrf_protection()
        self.test_form_submissions_security()
        self.test_api_endpoint_protection()
        self.test_state_changing_operations()
        self.test_cross_origin_request_handling()
        self.test_token_validation_and_rotation()
        self.test_concurrent_csrf_requests()
        
        end_time = time.time()
        
        # Generate and display report
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("📊 CSRF Protection Testing Report")
        print("=" * 80)
        
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Passed: {report['test_summary']['passed_tests']} ✅")
        print(f"Failed: {report['test_summary']['failed_tests']} ❌")
        print(f"Errors: {report['test_summary']['error_tests']} ⚠️")
        print(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"Test Duration: {end_time - start_time:.2f} seconds")
        
        print(f"\nSecurity Issues:")
        print(f"  Critical: {report['security_assessment']['critical_issues']}")
        print(f"  High: {report['security_assessment']['high_issues']}")
        print(f"  Medium: {report['security_assessment']['medium_issues']}")
        print(f"  Low: {report['security_assessment']['low_issues']}")
        
        if report['recommendations']:
            print(f"\n🔧 Security Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"csrf_protection_test_report_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        return report

def main():
    """Main function to run CSRF protection tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSRF Protection Testing Suite')
    parser.add_argument('--base-url', required=True, help='Base URL of the application')
    parser.add_argument('--secret-key', required=True, help='Secret key for CSRF token generation')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--concurrent', type=int, default=5, help='Number of concurrent requests')
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = CSRFProtectionTester(args.base_url, args.secret_key)
    
    # Update configuration
    tester.test_config['timeout'] = args.timeout
    tester.test_config['concurrent_requests'] = args.concurrent
    
    # Run tests
    report = tester.run_all_tests()
    
    # Exit with appropriate code
    if report['test_summary']['failed_tests'] > 0 or report['security_assessment']['critical_issues'] > 0:
        print("\n❌ CSRF protection testing found critical issues!")
        sys.exit(1)
    else:
        print("\n✅ CSRF protection testing completed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
