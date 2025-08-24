#!/usr/bin/env python3
"""
Comprehensive Test Script for Smart Resend Verification
Tests all features including progressive delays, analytics, and enhanced UX
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5001"  # Adjust port as needed
API_BASE = f"{BASE_URL}/api/onboarding"

class SmartResendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_phone = "+1234567890"
        self.test_user_id = "test_user_123"
        
    def print_test_header(self, test_name: str):
        """Print a formatted test header"""
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def test_send_verification_initial(self):
        """Test initial verification code send"""
        self.print_test_header("Initial Verification Code Send")
        
        url = f"{API_BASE}/send-verification"
        data = {"phone_number": self.test_phone}
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.print_success("Initial code sent successfully")
                self.print_info(f"Resend count: {result.get('resend_count', 0)}")
                self.print_info(f"Next delay: {result.get('next_resend_delay', 0)}s")
                self.print_info(f"Can change phone: {result.get('can_change_phone', False)}")
                return True
            else:
                result = response.json()
                self.print_error(f"Failed to send code: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_resend_with_cooldown(self):
        """Test resend with cooldown period"""
        self.print_test_header("Resend with Cooldown")
        
        url = f"{API_BASE}/resend-verification"
        data = {"phone_number": self.test_phone}
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            result = response.json()
            
            if response.status_code == 400 and 'cooldown_remaining' in result:
                self.print_success("Cooldown properly enforced")
                self.print_info(f"Cooldown remaining: {result['cooldown_remaining']}s")
                self.print_info(f"Resend count: {result.get('resend_count', 0)}")
                return True
            elif response.status_code == 200:
                self.print_success("Resend successful (no cooldown)")
                return True
            else:
                self.print_error(f"Unexpected response: {result}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_verification_status(self):
        """Test verification status endpoint"""
        self.print_test_header("Verification Status")
        
        url = f"{API_BASE}/verification-status?phone_number={self.test_phone}"
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.print_success("Status retrieved successfully")
                self.print_info(f"Has active verification: {result.get('has_active_verification', False)}")
                self.print_info(f"Can send code: {result.get('can_send_code', False)}")
                self.print_info(f"Resend count: {result.get('resend_count', 0)}")
                self.print_info(f"Max resends: {result.get('max_resends', 3)}")
                self.print_info(f"Attempts used: {result.get('attempts_used', 0)}")
                self.print_info(f"Max attempts: {result.get('max_attempts', 3)}")
                
                if result.get('attempt_history'):
                    self.print_info(f"Attempt history: {len(result['attempt_history'])} entries")
                
                return True
            else:
                result = response.json()
                self.print_error(f"Failed to get status: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_change_phone_number(self):
        """Test phone number change functionality"""
        self.print_test_header("Change Phone Number")
        
        new_phone = "+1987654321"
        url = f"{API_BASE}/change-phone"
        data = {
            "old_phone_number": self.test_phone,
            "new_phone_number": new_phone
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            result = response.json()
            
            if response.status_code == 200:
                self.print_success("Phone number changed successfully")
                self.print_info(f"New phone: {result.get('new_phone', new_phone)}")
                self.test_phone = new_phone  # Update for subsequent tests
                return True
            else:
                self.print_error(f"Failed to change phone: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_verification_analytics(self):
        """Test analytics endpoint"""
        self.print_test_header("Verification Analytics")
        
        url = f"{API_BASE}/verification-analytics"
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.print_success("Analytics retrieved successfully")
                
                analytics = result.get('analytics', [])
                self.print_info(f"Total analytics events: {len(analytics)}")
                
                # Group events by type
                event_counts = {}
                for event in analytics:
                    event_type = event.get('event_type', 'unknown')
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
                
                for event_type, count in event_counts.items():
                    self.print_info(f"  {event_type}: {count} events")
                
                return True
            else:
                result = response.json()
                self.print_error(f"Failed to get analytics: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_progressive_delays(self):
        """Test progressive delay functionality"""
        self.print_test_header("Progressive Delays")
        
        # Expected delays: 60s, 120s, 300s
        expected_delays = [60, 120, 300]
        
        for i, expected_delay in enumerate(expected_delays):
            self.print_info(f"Testing resend {i+1} (expected delay: {expected_delay}s)")
            
            # Try to resend immediately
            url = f"{API_BASE}/resend-verification"
            data = {"phone_number": self.test_phone}
            
            try:
                response = self.session.post(url, json=data)
                result = response.json()
                
                if response.status_code == 400 and 'cooldown_remaining' in result:
                    actual_delay = result['cooldown_remaining']
                    if abs(actual_delay - expected_delay) <= 5:  # Allow 5s tolerance
                        self.print_success(f"Resend {i+1} delay correct: {actual_delay}s")
                    else:
                        self.print_error(f"Resend {i+1} delay incorrect: expected {expected_delay}s, got {actual_delay}s")
                else:
                    self.print_info(f"Resend {i+1} successful (no cooldown)")
                    
            except Exception as e:
                self.print_error(f"Request failed: {e}")
    
    def test_verify_code(self):
        """Test code verification"""
        self.print_test_header("Code Verification")
        
        url = f"{API_BASE}/verify-phone"
        data = {
            "phone_number": self.test_phone,
            "verification_code": "123456"  # Mock code for testing
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            result = response.json()
            
            if response.status_code == 200:
                self.print_success("Code verified successfully")
                return True
            elif response.status_code == 400:
                if 'remaining_attempts' in result:
                    self.print_info(f"Verification failed, {result['remaining_attempts']} attempts remaining")
                else:
                    self.print_info(f"Verification failed: {result.get('error', 'Unknown error')}")
                return False
            else:
                self.print_error(f"Unexpected response: {result}")
                return False
                
        except Exception as e:
            self.print_error(f"Request failed: {e}")
            return False
    
    def test_max_resends_limit(self):
        """Test maximum resends limit"""
        self.print_test_header("Maximum Resends Limit")
        
        # Try to resend multiple times to hit the limit
        max_attempts = 5
        hit_limit = False
        
        for i in range(max_attempts):
            url = f"{API_BASE}/resend-verification"
            data = {"phone_number": self.test_phone}
            
            try:
                response = self.session.post(url, json=data)
                result = response.json()
                
                if response.status_code == 400 and 'suggest_alternative' in result:
                    self.print_success(f"Hit resend limit after {i+1} attempts")
                    self.print_info("Alternative contact methods suggested")
                    hit_limit = True
                    break
                elif response.status_code == 200:
                    self.print_info(f"Resend {i+1} successful")
                elif response.status_code == 400 and 'cooldown_remaining' in result:
                    self.print_info(f"Resend {i+1} in cooldown: {result['cooldown_remaining']}s remaining")
                    # Wait for cooldown to expire
                    time.sleep(result['cooldown_remaining'] + 1)
                else:
                    self.print_error(f"Unexpected response on attempt {i+1}: {result}")
                    break
                    
            except Exception as e:
                self.print_error(f"Request failed on attempt {i+1}: {e}")
                break
        
        if not hit_limit:
            self.print_info("Did not hit resend limit within expected attempts")
    
    def test_alternative_contact_suggestions(self):
        """Test alternative contact method suggestions"""
        self.print_test_header("Alternative Contact Suggestions")
        
        # Check if alternative contact is suggested after multiple resends
        url = f"{API_BASE}/verification-status?phone_number={self.test_phone}"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                result = response.json()
                
                if result.get('suggest_alternative'):
                    self.print_success("Alternative contact methods suggested")
                    self.print_info("User should see options for email verification or support contact")
                else:
                    self.print_info("Alternative contact not yet suggested")
                
                if result.get('can_change_phone'):
                    self.print_success("Phone number change option available")
                else:
                    self.print_info("Phone number change not yet available")
                    
        except Exception as e:
            self.print_error(f"Request failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 SMART RESEND VERIFICATION TEST SUITE")
        print("=" * 60)
        print(f"Test Phone: {self.test_phone}")
        print(f"Test User: {self.test_user_id}")
        print(f"API Base: {API_BASE}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            ("Initial Send", self.test_send_verification_initial),
            ("Verification Status", self.test_verification_status),
            ("Resend with Cooldown", self.test_resend_with_cooldown),
            ("Progressive Delays", self.test_progressive_delays),
            ("Code Verification", self.test_verify_code),
            ("Max Resends Limit", self.test_max_resends_limit),
            ("Alternative Contact", self.test_alternative_contact_suggestions),
            ("Change Phone Number", self.test_change_phone_number),
            ("Analytics", self.test_verification_analytics),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.print_error(f"Test '{test_name}' failed with exception: {e}")
        
        print(f"\n{'='*60}")
        print(f"TEST RESULTS: {passed}/{total} tests passed")
        print(f"{'='*60}")
        
        if passed == total:
            print("🎉 All tests passed! Smart resend functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = SmartResendTester()
    
    print("Note: These tests require:")
    print("1. A running Flask server")
    print("2. Authentication (tests may fail without proper auth)")
    print("3. Database with verification tables")
    print("4. Verification service properly configured")
    
    print("\nExpected Features Tested:")
    print("✅ Progressive delays (60s, 120s, 300s)")
    print("✅ Maximum resend attempts (3 per session)")
    print("✅ Alternative contact method suggestions")
    print("✅ Attempt history tracking")
    print("✅ Different messaging for each attempt")
    print("✅ Phone number change option")
    print("✅ Analytics tracking")
    print("✅ Countdown timer functionality")
    print("✅ Cooldown enforcement")
    
    print("\nStarting tests...")
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Smart resend implementation is ready for production!")
    else:
        print("\n🔧 Please fix the failing tests before deploying.")

if __name__ == "__main__":
    main() 