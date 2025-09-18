#!/usr/bin/env python3
"""
Basic Functionality Test for Referral-Gated Job Recommendation System
Simple test to verify core components are working
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_referral_system_basic():
    """Test basic referral system functionality"""
    print("🔧 Testing Referral System (Basic)...")
    
    try:
        from models.referral_models import ReferralSystem
        
        # Create separate test database for each test
        test_db = tempfile.mktemp(suffix='.db')
        referral_system = ReferralSystem(test_db)
        
        # Test 1: Create user
        print("  📝 Creating test user...")
        result = referral_system.create_user(
            user_id="test_user_basic",
            email="test_basic@example.com",
            first_name="Test",
            last_name="User"
        )
        
        if not result['success']:
            print(f"  ❌ User creation failed: {result['error']}")
            return False
        
        print(f"  ✅ User created with referral code: {result['referral_code']}")
        
        # Test 2: Check feature access (should be locked)
        print("  📝 Checking initial feature access...")
        access_check = referral_system.check_feature_access("test_user_basic")
        
        if access_check['unlocked']:
            print("  ❌ Feature should be locked initially")
            return False
        
        print(f"  ✅ Feature correctly locked (referrals needed: {access_check.get('referrals_needed', 0)})")
        
        # Test 3: Get referral progress
        print("  📝 Checking referral progress...")
        progress = referral_system.get_referral_progress("test_user_basic")
        
        if not progress['success']:
            print(f"  ❌ Failed to get referral progress: {progress['error']}")
            return False
        
        if progress['progress']['successful_referrals'] != 0:
            print(f"  ❌ Wrong initial referral count: {progress['progress']['successful_referrals']}")
            return False
        
        print("  ✅ Referral progress correct")
        
        # Cleanup
        os.remove(test_db)
        print("  🧹 Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Referral system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_location_validation():
    """Test location validation functionality"""
    print("\n🌍 Testing Location Validation...")
    
    try:
        from utils.location_utils import LocationValidator
        
        validator = LocationValidator()
        
        # Test ZIP code validation
        print("  📝 Testing ZIP code validation...")
        test_cases = [
            ("12345", True),
            ("90210", True),
            ("10001", True),
            ("12345-6789", True),
            ("1234", False),
            ("abcde", False),
            ("123456", False),
            ("", False)
        ]
        
        for zipcode, expected in test_cases:
            result = validator.validate_zipcode(zipcode)
            if result != expected:
                print(f"  ❌ ZIP code {zipcode} validation failed (expected: {expected}, got: {result})")
                return False
        
        print("  ✅ ZIP code validation working correctly")
        
        # Test distance calculation
        print("  📝 Testing distance calculation...")
        # Distance between New York (40.7128, -74.0060) and Los Angeles (34.0522, -118.2437)
        distance = validator._haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
        
        # Should be approximately 2445 miles
        if not (2000 < distance < 3000):
            print(f"  ❌ Distance calculation seems wrong: {distance} miles")
            return False
        
        print(f"  ✅ Distance calculation working: {distance:.0f} miles")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Location validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_basic():
    """Test basic security functionality"""
    print("\n🔒 Testing Security (Basic)...")
    
    try:
        from security.referral_security import ReferralSecurityManager, sanitize_input
        
        # Create test database
        test_db = tempfile.mktemp(suffix='.db')
        security_manager = ReferralSecurityManager(test_db)
        
        # Test rate limiting
        print("  📝 Testing rate limiting...")
        identifier = "test_rate_limit_basic"
        action = "test_action"
        
        # Should allow first few requests
        for i in range(3):
            if not security_manager.check_rate_limit(identifier, action, limit=10):
                print(f"  ❌ Rate limit too restrictive at request {i+1}")
                return False
        
        print("  ✅ Rate limiting working")
        
        # Test input sanitization
        print("  📝 Testing input sanitization...")
        test_cases = [
            ("<script>alert('xss')</script>Hello", "Hello"),
            ("Normal text", "Normal text"),
            ("<b>Bold text</b>", "Bold text"),
            ("", "")
        ]
        
        for input_text, expected in test_cases:
            sanitized = sanitize_input(input_text)
            if '<script>' in sanitized or 'alert' in sanitized:
                print(f"  ❌ XSS sanitization failed for: {input_text}")
                return False
        
        print("  ✅ Input sanitization working")
        
        # Test secure token generation
        print("  📝 Testing secure token generation...")
        data = "test_data"
        token = security_manager.generate_secure_token(data)
        
        if not security_manager.validate_secure_token(token, data):
            print("  ❌ Secure token validation failed")
            return False
        
        print("  ✅ Secure token generation working")
        
        # Cleanup
        os.remove(test_db)
        print("  🧹 Security test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_forms():
    """Test form validation"""
    print("\n📝 Testing Forms...")
    
    try:
        from forms.referral_forms import (
            ReferralInviteForm, LocationPreferencesForm, 
            CareerPreferencesForm, ZipcodeValidationForm
        )
        
        # Test ReferralInviteForm
        print("  📝 Testing ReferralInviteForm...")
        form_data = {
            'friend_email': 'friend@example.com',
            'friend_name': 'Friend Name',
            'personal_message': 'Check out this great app!'
        }
        
        form = ReferralInviteForm(data=form_data)
        if not form.validate():
            print(f"  ❌ ReferralInviteForm validation failed: {form.errors}")
            return False
        
        print("  ✅ ReferralInviteForm validation working")
        
        # Test LocationPreferencesForm
        print("  📝 Testing LocationPreferencesForm...")
        location_data = {
            'zipcode': '12345',
            'search_radius': 25,
            'commute_preference': 'flexible',
            'remote_ok': True
        }
        
        form = LocationPreferencesForm(data=location_data)
        if not form.validate():
            print(f"  ❌ LocationPreferencesForm validation failed: {form.errors}")
            return False
        
        print("  ✅ LocationPreferencesForm validation working")
        
        # Test CareerPreferencesForm
        print("  📝 Testing CareerPreferencesForm...")
        career_data = {
            'current_salary': 75000,
            'target_salary_increase': 0.25,
            'career_field': 'technology',
            'experience_level': 'mid'
        }
        
        form = CareerPreferencesForm(data=career_data)
        if not form.validate():
            print(f"  ❌ CareerPreferencesForm validation failed: {form.errors}")
            return False
        
        print("  ✅ CareerPreferencesForm validation working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Forms test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_initialization():
    """Test database initialization"""
    print("\n🗄️  Testing Database Initialization...")
    
    try:
        from models.referral_models import ReferralSystem
        
        # Create test database
        test_db = tempfile.mktemp(suffix='.db')
        referral_system = ReferralSystem(test_db)
        
        # Check if database file was created
        if not os.path.exists(test_db):
            print("  ❌ Database file was not created")
            return False
        
        print("  ✅ Database file created")
        
        # Check if tables were created by trying to create a user
        result = referral_system.create_user(
            user_id="db_test_user",
            email="db_test@example.com"
        )
        
        if not result['success']:
            print(f"  ❌ Database tables not properly initialized: {result['error']}")
            return False
        
        print("  ✅ Database tables initialized correctly")
        
        # Cleanup
        os.remove(test_db)
        print("  🧹 Database test cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_basic_tests():
    """Run all basic functionality tests"""
    print("🧪 BASIC FUNCTIONALITY TEST FOR REFERRAL-GATED JOB RECOMMENDATION SYSTEM")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Referral System (Basic)", test_referral_system_basic),
        ("Location Validation", test_location_validation),
        ("Security (Basic)", test_security_basic),
        ("Forms", test_forms)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 80)
    print("📊 BASIC FUNCTIONALITY TEST RESULTS")
    print("=" * 80)
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL BASIC TESTS PASSED!")
        print("🚀 Core functionality is working correctly!")
        print("\n💡 Next steps:")
        print("   1. Run 'python app.py' to start the Flask server")
        print("   2. Test the API endpoints at http://localhost:5000")
        print("   3. Try the referral workflow in the browser")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the errors above.")
        print("\n🔧 Common fixes:")
        print("   - Ensure all required Python packages are installed")
        print("   - Check that all files are in the correct locations")
        print("   - Verify Python path includes the backend directory")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return failed == 0

if __name__ == '__main__':
    success = run_basic_tests()
    sys.exit(0 if success else 1)
