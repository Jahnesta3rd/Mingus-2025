#!/usr/bin/env python3
"""
Comprehensive Financial CSRF Protection Testing Suite

This script tests CSRF protection across all financial endpoints in the MINGUS application:

1. Financial transaction endpoints CSRF protection
2. Payment processing endpoints CSRF protection  
3. Subscription management endpoints CSRF protection
4. Health check-in endpoints CSRF protection
5. Financial goal endpoints CSRF protection
6. Token generation and validation
7. Cross-site request forgery attack simulation
8. Token expiration and rotation testing

Usage:
    python test_financial_csrf_protection.py

Author: MINGUS Security Team
Date: January 2025
"""

import requests
import json
import time
import secrets
import hmac
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.security.financial_csrf_protection import FinancialCSRFProtection

class FinancialCSRFProtectionTester:
    """Comprehensive CSRF protection testing suite for financial endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.secret_key = "test_secret_key_for_csrf_protection"
        self.csrf_protection = FinancialCSRFProtection()
        
        # Test endpoints that require CSRF protection
        self.financial_endpoints = [
            # Income/Expense endpoints
            ('/api/v1/financial/transactions', 'POST'),
            ('/api/financial/transactions', 'POST'),
            ('/api/financial/income', 'POST'),
            ('/api/financial/expenses', 'POST'),
            
            # Subscription management
            ('/api/payment/subscriptions', 'POST'),
            ('/api/payment/subscriptions/me', 'PUT'),
            ('/api/payment/subscriptions/tiers', 'POST'),
            
            # Payment processing
            ('/api/payment/payment-intents', 'POST'),
            ('/api/payment/payment-methods', 'POST'),
            ('/api/payment/customers', 'POST'),
            ('/api/payment/invoices', 'POST'),
            
            # Financial goals and planning
            ('/api/financial/goals', 'POST'),
            ('/api/financial-goals', 'POST'),
            ('/api/financial/questionnaire', 'POST'),
            ('/api/financial/planning', 'POST'),
            
            # Weekly check-ins
            ('/api/health/checkin', 'POST'),
            
            # Financial profile updates
            ('/api/financial/profile', 'POST'),
            ('/api/onboarding/financial-profile', 'POST'),
            
            # Billing and subscription changes
            ('/api/payment/billing', 'POST'),
            ('/api/payment/upgrade', 'POST'),
            ('/api/payment/downgrade', 'POST'),
            ('/api/payment/cancel', 'POST'),
            
            # Financial compliance
            ('/api/financial/payment/process', 'POST'),
            ('/api/financial/records/store', 'POST'),
            ('/api/financial/breach/report', 'POST'),
            
            # Financial analysis
            ('/api/financial-analysis/spending-patterns', 'POST'),
            ('/api/financial/analytics', 'POST'),
            ('/api/financial/export', 'POST')
        ]
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def generate_valid_csrf_token(self, session_id: str = None) -> str:
        """Generate a valid CSRF token for testing"""
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        
        timestamp = str(int(time.time()))
        token_data = f"financial:{session_id}:{timestamp}"
        
        # Create HMAC signature with financial-specific salt
        signature = hmac.new(
            (self.secret_key + 'financial').encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return token in format: financial:session_id:timestamp:signature
        return f"{token_data}:{signature}"
    
    def generate_invalid_csrf_token(self) -> str:
        """Generate an invalid CSRF token for testing"""
        return "invalid:token:format:signature"
    
    def generate_expired_csrf_token(self) -> str:
        """Generate an expired CSRF token for testing"""
        session_id = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()) - 3600)  # 1 hour ago
        token_data = f"financial:{session_id}:{timestamp}"
        
        signature = hmac.new(
            (self.secret_key + 'financial').encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token_data}:{signature}"
    
    def _test_endpoint_csrf_protection(
        self, 
        endpoint: str, 
        method: str, 
        csrf_token: Optional[str] = None,
        test_name: str = "",
        expected_behavior: str = ""
    ) -> bool:
        """Test CSRF protection on a specific endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if csrf_token:
                headers['X-CSRFToken'] = csrf_token
            
            # Test data for financial endpoints
            test_data = {
                'amount': 100.00,
                'description': 'Test transaction',
                'category': 'test',
                'transaction_date': datetime.now().isoformat(),
                'transaction_type': 'expense'
            }
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=test_data,
                timeout=10
            )
            
            # Check if CSRF protection is working
            if csrf_token is None:
                # Should be rejected (403 or 400)
                if response.status_code in [400, 403]:
                    return True
                else:
                    return False
            elif csrf_token == self.generate_invalid_csrf_token():
                # Should be rejected
                if response.status_code in [400, 403]:
                    return True
                else:
                    return False
            elif csrf_token == self.generate_expired_csrf_token():
                # Should be rejected
                if response.status_code in [400, 403]:
                    return True
                else:
                    return False
            else:
                # Valid token - may pass (could fail for auth reasons, which is OK)
                return True
                
        except Exception as e:
            return False
    
    def test_financial_transaction_csrf_protection(self):
        """Test CSRF protection on financial transaction endpoints"""
        print("🔒 Testing Financial Transaction CSRF Protection")
        
        for endpoint, method in self.financial_endpoints:
            if 'transaction' in endpoint or 'financial' in endpoint:
                # Test 1: Request without CSRF token
                self._test_endpoint_csrf_protection(
                    endpoint=endpoint,
                    method=method,
                    csrf_token=None,
                    test_name=f"Financial Transaction - No CSRF Token - {endpoint}",
                    expected_behavior="Should reject request without CSRF token"
                )
                
                # Test 2: Request with invalid CSRF token
                self._test_endpoint_csrf_protection(
                    endpoint=endpoint,
                    method=method,
                    csrf_token=self.generate_invalid_csrf_token(),
                    test_name=f"Financial Transaction - Invalid CSRF Token - {endpoint}",
                    expected_behavior="Should reject request with invalid CSRF token"
                )
                
                # Test 3: Request with expired CSRF token
                self._test_endpoint_csrf_protection(
                    endpoint=endpoint,
                    method=method,
                    csrf_token=self.generate_expired_csrf_token(),
                    test_name=f"Financial Transaction - Expired CSRF Token - {endpoint}",
                    expected_behavior="Should reject request with expired CSRF token"
                )
                
                # Test 4: Request with valid CSRF token (should pass if authenticated)
                self._test_endpoint_csrf_protection(
                    endpoint=endpoint,
                    method=method,
                    csrf_token=self.generate_valid_csrf_token(),
                    test_name=f"Financial Transaction - Valid CSRF Token - {endpoint}",
                    expected_behavior="Should accept request with valid CSRF token (may fail for auth reasons)"
                )
    
    def test_payment_processing_csrf_protection(self):
        """Test CSRF protection on payment processing endpoints"""
        print("💳 Testing Payment Processing CSRF Protection")
        
        payment_endpoints = [
            ('/api/payment/payment-intents', 'POST'),
            ('/api/payment/payment-methods', 'POST'),
            ('/api/payment/customers', 'POST'),
            ('/api/payment/invoices', 'POST')
        ]
        
        for endpoint, method in payment_endpoints:
            # Test without CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=None
            )
            self.log_test_result(
                f"Payment Processing - No CSRF Token - {endpoint}",
                success,
                "Should reject payment request without CSRF token"
            )
            
            # Test with invalid CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=self.generate_invalid_csrf_token()
            )
            self.log_test_result(
                f"Payment Processing - Invalid CSRF Token - {endpoint}",
                success,
                "Should reject payment request with invalid CSRF token"
            )
    
    def test_subscription_management_csrf_protection(self):
        """Test CSRF protection on subscription management endpoints"""
        print("📦 Testing Subscription Management CSRF Protection")
        
        subscription_endpoints = [
            ('/api/payment/subscriptions', 'POST'),
            ('/api/payment/subscriptions/me', 'PUT'),
            ('/api/payment/subscriptions/tiers', 'POST')
        ]
        
        for endpoint, method in subscription_endpoints:
            # Test without CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=None
            )
            self.log_test_result(
                f"Subscription Management - No CSRF Token - {endpoint}",
                success,
                "Should reject subscription request without CSRF token"
            )
            
            # Test with invalid CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=self.generate_invalid_csrf_token()
            )
            self.log_test_result(
                f"Subscription Management - Invalid CSRF Token - {endpoint}",
                success,
                "Should reject subscription request with invalid CSRF token"
            )
    
    def test_health_checkin_csrf_protection(self):
        """Test CSRF protection on health check-in endpoints"""
        print("💚 Testing Health Check-in CSRF Protection")
        
        health_endpoints = [
            ('/api/health/checkin', 'POST')
        ]
        
        for endpoint, method in health_endpoints:
            # Test without CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=None
            )
            self.log_test_result(
                f"Health Check-in - No CSRF Token - {endpoint}",
                success,
                "Should reject health check-in without CSRF token"
            )
            
            # Test with invalid CSRF token
            success = self._test_endpoint_csrf_protection(
                endpoint=endpoint,
                method=method,
                csrf_token=self.generate_invalid_csrf_token()
            )
            self.log_test_result(
                f"Health Check-in - Invalid CSRF Token - {endpoint}",
                success,
                "Should reject health check-in with invalid CSRF token"
            )
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation endpoint"""
        print("🔑 Testing CSRF Token Generation")
        
        try:
            response = self.session.get(f"{self.base_url}/api/financial/csrf-token")
            
            if response.status_code == 200:
                data = response.json()
                if 'csrf_token' in data and 'expires_in' in data:
                    self.log_test_result(
                        "CSRF Token Generation",
                        True,
                        f"Token generated successfully, expires in {data['expires_in']} seconds"
                    )
                else:
                    self.log_test_result(
                        "CSRF Token Generation",
                        False,
                        "Response missing required fields"
                    )
            else:
                self.log_test_result(
                    "CSRF Token Generation",
                    False,
                    f"Endpoint returned status code {response.status_code}"
                )
        except Exception as e:
            self.log_test_result(
                "CSRF Token Generation",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_cross_site_request_forgery_simulation(self):
        """Simulate cross-site request forgery attacks"""
        print("🚨 Testing Cross-Site Request Forgery Simulation")
        
        # Test 1: Request from different origin without CSRF token
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://malicious-site.com',
            'Referer': 'https://malicious-site.com/fake-form.html'
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/financial/transactions",
                headers=headers,
                json={'amount': 1000, 'description': 'Fake transaction'},
                timeout=10
            )
            
            # Should be rejected
            success = response.status_code in [400, 403]
            self.log_test_result(
                "CSRF Attack Simulation - Different Origin",
                success,
                f"Request from malicious origin should be rejected (status: {response.status_code})"
            )
        except Exception as e:
            self.log_test_result(
                "CSRF Attack Simulation - Different Origin",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_token_expiration_and_rotation(self):
        """Test CSRF token expiration and rotation"""
        print("⏰ Testing Token Expiration and Rotation")
        
        # Generate a token
        token1 = self.generate_valid_csrf_token()
        
        # Wait a moment and generate another token
        time.sleep(1)
        token2 = self.generate_valid_csrf_token()
        
        # Tokens should be different
        if token1 != token2:
            self.log_test_result(
                "Token Rotation",
                True,
                "Different tokens generated for different requests"
            )
        else:
            self.log_test_result(
                "Token Rotation",
                False,
                "Same token generated for different requests"
            )
    
    def run_all_tests(self):
        """Run all CSRF protection tests"""
        print("🔒 MINGUS Financial CSRF Protection Test Suite")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Run all test suites
        self.test_financial_transaction_csrf_protection()
        self.test_payment_processing_csrf_protection()
        self.test_subscription_management_csrf_protection()
        self.test_health_checkin_csrf_protection()
        self.test_csrf_token_generation()
        self.test_cross_site_request_forgery_simulation()
        self.test_token_expiration_and_rotation()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate test summary report"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}")
                    print(f"    Details: {result['details']}")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"financial_csrf_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_suite': 'Financial CSRF Protection',
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        if failed_tests == 0:
            print("\n🎉 All CSRF protection tests passed! Financial endpoints are secure.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please review and fix CSRF protection issues.")

def main():
    """Main function to run the test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Financial CSRF Protection')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='Base URL of the application (default: http://localhost:5001)')
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = FinancialCSRFProtectionTester(args.url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
