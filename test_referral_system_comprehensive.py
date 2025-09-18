#!/usr/bin/env python3
"""
Comprehensive Test Suite for Referral-Gated Job Recommendation System
Tests all components including referral system, location utils, security, and API endpoints
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.referral_models import ReferralSystem
from utils.location_utils import LocationValidator, LocationService
from security.referral_security import ReferralSecurityManager, validate_file_upload, sanitize_input
from integration.mingus_integration import MingusIntegrationManager

class TestReferralSystem(unittest.TestCase):
    """Test the referral system database models and functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.mktemp(suffix='.db')
        self.referral_system = ReferralSystem(self.test_db)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_create_user(self):
        """Test user creation with referral code generation"""
        result = self.referral_system.create_user(
            user_id="test_user_1",
            email="test1@example.com",
            first_name="John",
            last_name="Doe"
        )
        
        self.assertTrue(result['success'])
        self.assertIn('referral_code', result)
        self.assertEqual(len(result['referral_code']), 8)
    
    def test_create_user_with_referral(self):
        """Test user creation with referral from another user"""
        # Create referrer
        referrer_result = self.referral_system.create_user(
            user_id="referrer_1",
            email="referrer@example.com"
        )
        
        # Create referred user
        result = self.referral_system.create_user(
            user_id="referred_1",
            email="referred@example.com",
            referred_by="referrer_1"
        )
        
        self.assertTrue(result['success'])
        
        # Check referral count increased
        progress = self.referral_system.get_referral_progress("referrer_1")
        self.assertEqual(progress['progress']['total_referrals'], 1)
    
    def test_validate_referral(self):
        """Test referral validation process"""
        # Create referrer
        referrer_result = self.referral_system.create_user(
            user_id="referrer_2",
            email="referrer2@example.com"
        )
        
        # Create referral
        result = self.referral_system.create_user(
            user_id="referred_2",
            email="referred2@example.com",
            referred_by="referrer_2"
        )
        
        # Validate referral
        validation_result = self.referral_system.validate_referral(
            result['referral_code'],
            "referred2@example.com"
        )
        
        self.assertTrue(validation_result['success'])
        
        # Check successful referrals count
        progress = self.referral_system.get_referral_progress("referrer_2")
        self.assertEqual(progress['progress']['successful_referrals'], 1)
    
    def test_feature_unlock_after_3_referrals(self):
        """Test feature unlock after 3 successful referrals"""
        # Create referrer
        referrer_result = self.referral_system.create_user(
            user_id="referrer_3",
            email="referrer3@example.com"
        )
        
        # Create 3 referrals and validate them
        for i in range(3):
            result = self.referral_system.create_user(
                user_id=f"referred_3_{i}",
                email=f"referred3_{i}@example.com",
                referred_by="referrer_3"
            )
            
            # Validate referral
            self.referral_system.validate_referral(
                result['referral_code'],
                f"referred3_{i}@example.com"
            )
        
        # Check feature access
        access_check = self.referral_system.check_feature_access("referrer_3")
        self.assertTrue(access_check['unlocked'])
    
    def test_duplicate_user_creation(self):
        """Test handling of duplicate user creation"""
        # Create first user
        self.referral_system.create_user(
            user_id="duplicate_user",
            email="duplicate@example.com"
        )
        
        # Try to create duplicate
        result = self.referral_system.create_user(
            user_id="duplicate_user",
            email="duplicate@example.com"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('already exists', result['error'])

class TestLocationUtils(unittest.TestCase):
    """Test location validation and geocoding functionality"""
    
    def setUp(self):
        self.validator = LocationValidator()
        self.service = LocationService()
    
    def test_zipcode_validation(self):
        """Test ZIP code format validation"""
        # Valid ZIP codes
        valid_zips = ["12345", "12345-6789", "90210", "10001"]
        for zipcode in valid_zips:
            self.assertTrue(self.validator.validate_zipcode(zipcode))
        
        # Invalid ZIP codes
        invalid_zips = ["1234", "123456", "abcde", "12345-", "12345-12345"]
        for zipcode in invalid_zips:
            self.assertFalse(self.validator.validate_zipcode(zipcode))
    
    @patch('requests.get')
    def test_geocoding_success(self, mock_get):
        """Test successful geocoding with mocked API response"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "places": [{
                "place name": "New York",
                "state": "NY",
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "county": "New York County"
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        location_data = self.validator.geocode_zipcode("10001")
        
        self.assertIsNotNone(location_data)
        self.assertEqual(location_data.city, "New York")
        self.assertEqual(location_data.state, "NY")
        self.assertEqual(location_data.latitude, 40.7128)
        self.assertEqual(location_data.longitude, -74.0060)
    
    def test_distance_calculation(self):
        """Test distance calculation between two points"""
        # Test distance between New York and Los Angeles
        distance = self.validator._haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
        self.assertAlmostEqual(distance, 2445, delta=50)  # Approximately 2445 miles
    
    def test_commute_time_estimation(self):
        """Test commute time estimation"""
        # Mock geocoding for two ZIP codes
        with patch.object(self.validator, 'geocode_zipcode') as mock_geocode:
            # Mock location data
            mock_location1 = MagicMock()
            mock_location1.latitude = 40.7128
            mock_location1.longitude = -74.0060
            
            mock_location2 = MagicMock()
            mock_location2.latitude = 40.7589
            mock_location2.longitude = -73.9851
            
            mock_geocode.side_effect = [mock_location1, mock_location2]
            
            commute_estimate = self.validator.get_commute_time_estimate("10001", "10036")
            
            self.assertIsNotNone(commute_estimate)
            self.assertIn('distance_miles', commute_estimate)
            self.assertIn('estimated_time_minutes', commute_estimate)

class TestReferralSecurity(unittest.TestCase):
    """Test security features and fraud prevention"""
    
    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        self.security_manager = ReferralSecurityManager(self.test_db)
    
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        identifier = "test_user"
        action = "test_action"
        
        # Should allow first few requests
        for i in range(5):
            self.assertTrue(self.security_manager.check_rate_limit(identifier, action, limit=10))
        
        # Should block after limit
        for i in range(10):
            self.security_manager.check_rate_limit(identifier, action, limit=10)
        
        # This should be blocked
        self.assertFalse(self.security_manager.check_rate_limit(identifier, action, limit=10))
    
    def test_fraud_detection(self):
        """Test referral fraud detection"""
        # Test self-referral detection
        fraud_result = self.security_manager.detect_referral_fraud(
            "user1", "user1@example.com", "192.168.1.1"
        )
        
        # Should detect self-referral
        self.assertTrue(fraud_result['is_fraud'])
        self.assertEqual(fraud_result['confidence_score'], 1.0)
    
    def test_suspicious_email_detection(self):
        """Test detection of suspicious email patterns"""
        suspicious_emails = [
            "test123@example.com",
            "temp456@example.com",
            "fake789@example.com",
            "user@10minutemail.com"
        ]
        
        for email in suspicious_emails:
            self.assertTrue(self.security_manager._is_suspicious_email(email))
        
        normal_emails = [
            "john.doe@company.com",
            "jane.smith@gmail.com",
            "user@university.edu"
        ]
        
        for email in normal_emails:
            self.assertFalse(self.security_manager._is_suspicious_email(email))
    
    def test_entity_blocking(self):
        """Test IP and user blocking functionality"""
        # Block an IP
        self.security_manager.block_entity("ip", "192.168.1.100", "Suspicious activity")
        
        # Check if blocked
        self.assertTrue(self.security_manager.is_entity_blocked("ip", "192.168.1.100"))
        self.assertFalse(self.security_manager.is_entity_blocked("ip", "192.168.1.101"))
    
    def test_secure_token_generation(self):
        """Test secure token generation and validation"""
        data = "test_data"
        token = self.security_manager.generate_secure_token(data)
        
        # Should be valid
        self.assertTrue(self.security_manager.validate_secure_token(token, data))
        
        # Should be invalid with wrong data
        self.assertFalse(self.security_manager.validate_secure_token(token, "wrong_data"))
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        # Create a mock file
        class MockFile:
            def __init__(self, filename, content, size):
                self.filename = filename
                self.content = content
                self.size = size
            
            def read(self, size=-1):
                return self.content
            
            def seek(self, pos):
                pass
        
        # Valid file
        valid_file = MockFile("test.pdf", b"PDF content", 1024)
        result = validate_file_upload(valid_file, {'pdf'}, 2048)
        self.assertTrue(result['valid'])
        
        # Invalid file type
        invalid_file = MockFile("test.exe", b"Executable content", 1024)
        result = validate_file_upload(invalid_file, {'pdf'}, 2048)
        self.assertFalse(result['valid'])
        
        # File too large
        large_file = MockFile("test.pdf", b"Large content", 4096)
        result = validate_file_upload(large_file, {'pdf'}, 2048)
        self.assertFalse(result['valid'])
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello World"
        sanitized = sanitize_input(malicious_input)
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('alert', sanitized)
        
        # Test length limiting
        long_input = "A" * 2000
        sanitized = sanitize_input(long_input, max_length=100)
        self.assertEqual(len(sanitized), 100)

class TestMingusIntegration(unittest.TestCase):
    """Test integration with existing Mingus features"""
    
    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        self.integration_manager = MingusIntegrationManager()
    
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_financial_planning_integration(self):
        """Test integration with financial planning features"""
        # Mock financial profile
        financial_profile = {
            'annual_income': 75000,
            'current_savings': 10000,
            'student_loans': 25000,
            'credit_card_debt': 5000,
            'monthly_savings_goal': 1000
        }
        
        # Mock job recommendations
        job_recommendations = [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'salary_median': 95000,
                'salary_increase_potential': 0.27
            },
            {
                'title': 'Lead Developer',
                'company': 'Startup Inc',
                'salary_median': 110000,
                'salary_increase_potential': 0.47
            }
        ]
        
        # Test integration
        with patch.object(self.integration_manager, '_get_user_financial_profile', return_value=financial_profile):
            result = self.integration_manager.integrate_with_financial_planning("user1", job_recommendations)
        
        self.assertTrue(result['success'])
        self.assertIn('financial_impact', result)
        self.assertIn('potential_increases', result['financial_impact'])
        self.assertIn('recommendations', result['financial_impact'])
    
    def test_goal_setting_integration(self):
        """Test integration with goal setting functionality"""
        # Mock user goals
        user_goals = [
            {
                'id': 'goal1',
                'title': 'Increase salary by 30%',
                'category': 'financial',
                'target_salary': 100000
            },
            {
                'id': 'goal2',
                'title': 'Work remotely',
                'category': 'career',
                'remote_work': True
            }
        ]
        
        # Mock job recommendations
        job_recommendations = [
            {
                'job_id': 'job1',
                'title': 'Senior Developer',
                'company': 'Remote Corp',
                'salary_median': 105000,
                'location': 'Remote',
                'remote_friendly': True
            }
        ]
        
        # Test integration
        with patch.object(self.integration_manager, '_get_user_goals', return_value=user_goals):
            result = self.integration_manager.integrate_with_goal_setting("user1", job_recommendations)
        
        self.assertTrue(result['success'])
        self.assertIn('goal_integration', result)
        self.assertIn('goal_alignment', result['goal_integration'])

class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints functionality"""
    
    def setUp(self):
        # Set up test Flask app
        from flask import Flask
        from backend.api.referral_gated_endpoints import referral_gated_api
        
        self.app = Flask(__name__)
        self.app.register_blueprint(referral_gated_api)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_career_preview_endpoint(self):
        """Test career preview endpoint"""
        response = self.client.get('/career-preview')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('preview', data)
        self.assertIn('features', data['preview'])
    
    def test_referral_progress_endpoint(self):
        """Test referral progress endpoint"""
        response = self.client.get('/referral-progress?user_id=test_user')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('progress', data)
    
    def test_zipcode_validation_endpoint(self):
        """Test ZIP code validation endpoint"""
        response = self.client.post('/validate-zipcode', 
            json={'zipcode': '10001'},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('location', data)
    
    def test_refer_friend_endpoint(self):
        """Test refer friend endpoint"""
        response = self.client.post('/refer-friend',
            json={
                'user_id': 'test_user',
                'friend_email': 'friend@example.com',
                'friend_name': 'Friend Name'
            },
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('referral_code', data)

class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow"""
    
    def setUp(self):
        self.test_db = tempfile.mktemp(suffix='.db')
        self.referral_system = ReferralSystem(self.test_db)
    
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_complete_referral_workflow(self):
        """Test complete referral workflow from start to feature unlock"""
        # 1. Create referrer user
        referrer_result = self.referral_system.create_user(
            user_id="referrer_workflow",
            email="referrer@workflow.com",
            first_name="Workflow",
            last_name="Tester"
        )
        self.assertTrue(referrer_result['success'])
        
        # 2. Create 3 referrals
        referral_codes = []
        for i in range(3):
            result = self.referral_system.create_user(
                user_id=f"referred_workflow_{i}",
                email=f"referred{i}@workflow.com",
                referred_by="referrer_workflow"
            )
            self.assertTrue(result['success'])
            referral_codes.append(result['referral_code'])
        
        # 3. Validate all referrals
        for i, code in enumerate(referral_codes):
            validation_result = self.referral_system.validate_referral(
                code, f"referred{i}@workflow.com"
            )
            self.assertTrue(validation_result['success'])
        
        # 4. Check feature unlock
        access_check = self.referral_system.check_feature_access("referrer_workflow")
        self.assertTrue(access_check['unlocked'])
        
        # 5. Check progress
        progress = self.referral_system.get_referral_progress("referrer_workflow")
        self.assertEqual(progress['progress']['successful_referrals'], 3)
        self.assertTrue(progress['progress']['feature_unlocked'])

def run_comprehensive_tests():
    """Run all test suites"""
    print("🧪 Starting Comprehensive Test Suite for Referral-Gated Job Recommendation System")
    print("=" * 80)
    
    # Test suites to run
    test_suites = [
        TestReferralSystem,
        TestLocationUtils,
        TestReferralSecurity,
        TestMingusIntegration,
        TestAPIEndpoints,
        TestEndToEndWorkflow
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_suite in test_suites:
        print(f"\n📋 Running {test_suite.__name__}...")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        suite_tests = result.testsRun
        suite_passed = suite_tests - len(result.failures) - len(result.errors)
        suite_failed = len(result.failures) + len(result.errors)
        
        total_tests += suite_tests
        passed_tests += suite_passed
        failed_tests += suite_failed
        
        print(f"   ✅ Passed: {suite_passed}")
        print(f"   ❌ Failed: {suite_failed}")
        print(f"   📊 Total: {suite_tests}")
        
        # Print failures and errors
        if result.failures:
            print("   🔍 Failures:")
            for test, traceback in result.failures:
                print(f"      - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
        
        if result.errors:
            print("   🚨 Errors:")
            for test, traceback in result.errors:
                print(f"      - {test}: {traceback.split('\\n')[-2]}")
    
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    print(f"✅ Total Tests Passed: {passed_tests}")
    print(f"❌ Total Tests Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"🧪 Total Tests Run: {total_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! The referral-gated job recommendation system is working correctly.")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review the failures above.")
    
    return failed_tests == 0

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
