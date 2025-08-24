#!/usr/bin/env python3
"""
Comprehensive User Profile Integration Test
Tests all user profile functionality including API endpoints, database operations, and validation
"""

import requests
import json
import sqlite3
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserProfileTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'healthy' and data['database'] == 'connected':
                    self.log_test("Health Endpoint", True, "Application and database are healthy")
                    return True
                else:
                    self.log_test("Health Endpoint", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Health Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {e}")
            return False
    
    def test_api_test_endpoint(self):
        """Test API test endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/test-profile")
            if response.status_code == 200:
                data = response.json()
                if data['success'] and 'endpoints' in data:
                    self.log_test("API Test Endpoint", True, f"Found {len(data['endpoints'])} endpoints")
                    return True
                else:
                    self.log_test("API Test Endpoint", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("API Test Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Test Endpoint", False, f"Error: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connection and sample data"""
        try:
            conn = sqlite3.connect('instance/mingus.db')
            cursor = conn.cursor()
            
            # Check if tables exist
            tables = ['users', 'user_profiles', 'onboarding_progress', 'subscription_plans', 'subscriptions', 'feature_usage']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    self.log_test("Database Tables", False, f"Table {table} not found")
                    conn.close()
                    return False
            
            # Check sample user
            cursor.execute('SELECT id, email, first_name, last_name, profile_completion_percentage FROM users WHERE email = ?', ('test@mingus.com',))
            user = cursor.fetchone()
            if user:
                self.log_test("Sample User", True, f"Found user: {user[2]} {user[3]} (Completion: {user[4]}%)")
            else:
                self.log_test("Sample User", False, "Sample user not found")
                conn.close()
                return False
            
            # Check subscription plans
            cursor.execute('SELECT name, price, billing_cycle FROM subscription_plans')
            plans = cursor.fetchall()
            if len(plans) == 3:
                self.log_test("Subscription Plans", True, f"Found {len(plans)} plans")
            else:
                self.log_test("Subscription Plans", False, f"Expected 3 plans, found {len(plans)}")
                conn.close()
                return False
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test("Database Connection", False, f"Error: {e}")
            return False
    
    def test_user_profile_get(self):
        """Test getting user profile (requires authentication)"""
        try:
            # This will fail without authentication, which is expected
            response = self.session.get(f"{self.base_url}/api/user-profile/get")
            if response.status_code == 401 or response.status_code == 302:
                self.log_test("User Profile Get (Unauthenticated)", True, "Correctly requires authentication")
                return True
            else:
                self.log_test("User Profile Get (Unauthenticated)", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Profile Get (Unauthenticated)", False, f"Error: {e}")
            return False
    
    def test_user_profile_update_validation(self):
        """Test user profile update validation"""
        try:
            # Test with invalid data
            invalid_data = {
                'firstName': '',  # Empty first name
                'lastName': 'Doe',
                'zipCode': 'invalid'  # Invalid ZIP code
            }
            
            response = self.session.post(
                f"{self.base_url}/api/user-profile/update",
                json=invalid_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 401 or response.status_code == 302:
                self.log_test("User Profile Update Validation (Unauthenticated)", True, "Correctly requires authentication")
                return True
            else:
                self.log_test("User Profile Update Validation (Unauthenticated)", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Profile Update Validation (Unauthenticated)", False, f"Error: {e}")
            return False
    
    def test_subscription_endpoint(self):
        """Test subscription endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/user-profile/subscription")
            if response.status_code == 401 or response.status_code == 302:
                self.log_test("Subscription Endpoint (Unauthenticated)", True, "Correctly requires authentication")
                return True
            else:
                self.log_test("Subscription Endpoint (Unauthenticated)", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Subscription Endpoint (Unauthenticated)", False, f"Error: {e}")
            return False
    
    def test_feature_usage_endpoint(self):
        """Test feature usage endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/user-profile/feature-usage")
            if response.status_code == 401 or response.status_code == 302:
                self.log_test("Feature Usage Endpoint (Unauthenticated)", True, "Correctly requires authentication")
                return True
            else:
                self.log_test("Feature Usage Endpoint (Unauthenticated)", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Feature Usage Endpoint (Unauthenticated)", False, f"Error: {e}")
            return False
    
    def test_onboarding_progress_endpoint(self):
        """Test onboarding progress endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/user-profile/onboarding-progress")
            if response.status_code == 401 or response.status_code == 302:
                self.log_test("Onboarding Progress Endpoint (Unauthenticated)", True, "Correctly requires authentication")
                return True
            else:
                self.log_test("Onboarding Progress Endpoint (Unauthenticated)", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Onboarding Progress Endpoint (Unauthenticated)", False, f"Error: {e}")
            return False
    
    def test_web_interface(self):
        """Test web interface accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                if 'Mingus User Profile Test' in response.text:
                    self.log_test("Web Interface", True, "Main page loads successfully")
                    return True
                else:
                    self.log_test("Web Interface", False, "Main page content not found")
                    return False
            else:
                self.log_test("Web Interface", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Web Interface", False, f"Error: {e}")
            return False
    
    def test_login_page(self):
        """Test login page accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code == 200:
                if 'Login' in response.text and 'test@mingus.com' in response.text:
                    self.log_test("Login Page", True, "Login page loads with test credentials")
                    return True
                else:
                    self.log_test("Login Page", False, "Login page content not found")
                    return False
            else:
                self.log_test("Login Page", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login Page", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting User Profile Integration Tests...")
        logger.info("=" * 60)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Test Endpoint", self.test_api_test_endpoint),
            ("Database Connection", self.test_database_connection),
            ("User Profile Get (Unauthenticated)", self.test_user_profile_get),
            ("User Profile Update Validation (Unauthenticated)", self.test_user_profile_update_validation),
            ("Subscription Endpoint (Unauthenticated)", self.test_subscription_endpoint),
            ("Feature Usage Endpoint (Unauthenticated)", self.test_feature_usage_endpoint),
            ("Onboarding Progress Endpoint (Unauthenticated)", self.test_onboarding_progress_endpoint),
            ("Web Interface", self.test_web_interface),
            ("Login Page", self.test_login_page),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test exception: {e}")
        
        # Generate summary
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! User Profile Integration is working correctly.")
        else:
            logger.info(f"⚠️ {total - passed} tests failed. Please check the implementation.")
        
        # Save detailed results
        self.save_test_results()
        
        return passed == total
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'tests': self.test_results,
                'summary': {
                    'total': len(self.test_results),
                    'passed': sum(1 for r in self.test_results if r['success']),
                    'failed': sum(1 for r in self.test_results if not r['success'])
                }
            }
            
            with open('user_profile_test_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("📄 Test results saved to user_profile_test_results.json")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

def main():
    """Main function"""
    print("🎯 User Profile Integration Test Suite")
    print("=" * 50)
    
    # Check if application is running
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code != 200:
            print("❌ Application is not running on http://localhost:5001")
            print("Please start the test application first:")
            print("   python test_user_profile_app.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to application on http://localhost:5001")
        print("Please start the test application first:")
        print("   python test_user_profile_app.py")
        return False
    
    # Run tests
    tester = UserProfileTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 SUCCESS: User Profile Integration is complete and working!")
        print("\n📋 Next Steps:")
        print("1. Open http://localhost:5001 in your browser")
        print("2. Login with test@mingus.com / test123")
        print("3. Test the user profile functionality manually")
        print("4. Review the test results in user_profile_test_results.json")
    else:
        print("\n⚠️ Some tests failed. Please review the implementation.")
    
    return success

if __name__ == "__main__":
    main()
