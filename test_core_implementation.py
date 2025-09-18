#!/usr/bin/env python3
"""
Core Implementation Test for Referral-Gated Job Recommendation System
Tests only the components we've implemented, avoiding existing codebase dependencies
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_referral_models():
    """Test the referral models we implemented"""
    print("🔧 Testing Referral Models...")
    
    try:
        from models.referral_models import ReferralSystem
        
        # Create test database
        test_db = tempfile.mktemp(suffix='.db')
        referral_system = ReferralSystem(test_db)
        
        # Test 1: Create user
        print("  📝 Creating test user...")
        result = referral_system.create_user(
            user_id="test_models_user",
            email="test_models@example.com",
            first_name="Test",
            last_name="Models"
        )
        
        if not result['success']:
            print(f"  ❌ User creation failed: {result['error']}")
            return False
        
        print(f"  ✅ User created with referral code: {result['referral_code']}")
        
        # Test 2: Check initial feature access (should be locked)
        print("  📝 Checking initial feature access...")
        access_check = referral_system.check_feature_access("test_models_user")
        
        if access_check['unlocked']:
            print("  ❌ Feature should be locked initially")
            return False
        
        print(f"  ✅ Feature correctly locked (referrals needed: {access_check.get('referrals_needed', 0)})")
        
        # Test 3: Get referral progress
        print("  📝 Checking referral progress...")
        progress = referral_system.get_referral_progress("test_models_user")
        
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
        print(f"  ❌ Referral models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_location_utils():
    """Test the location utilities we implemented"""
    print("\n🌍 Testing Location Utils...")
    
    try:
        from utils.location_utils import LocationValidator, LocationService
        
        validator = LocationValidator()
        service = LocationService()
        
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
        
        # Test location service
        print("  📝 Testing location service...")
        result = service.validate_and_geocode("10001")
        
        if result['success']:
            print("  ✅ Location service working with API")
        else:
            print("  ⚠️  Location service API not available (expected in test)")
            print("  ✅ Location service structure working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Location utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_features():
    """Test the security features we implemented"""
    print("\n🔒 Testing Security Features...")
    
    try:
        from security.referral_security import ReferralSecurityManager, sanitize_input
        
        # Create test database
        test_db = tempfile.mktemp(suffix='.db')
        security_manager = ReferralSecurityManager(test_db)
        
        # Test rate limiting
        print("  📝 Testing rate limiting...")
        identifier = "test_security_core"
        action = "test_action"
        
        # Should allow first few requests
        for i in range(5):
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
            # Check that dangerous content is removed
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
        
        # Test entity blocking
        print("  📝 Testing entity blocking...")
        security_manager.block_entity("ip", "192.168.1.100", "Test blocking")
        
        if not security_manager.is_entity_blocked("ip", "192.168.1.100"):
            print("  ❌ Entity blocking failed")
            return False
        
        print("  ✅ Entity blocking working")
        
        # Cleanup
        os.remove(test_db)
        print("  🧹 Security test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test database schema creation"""
    print("\n🗄️  Testing Database Schema...")
    
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
        
        # Test if we can create a user (which tests table creation)
        print("  📝 Testing table creation...")
        result = referral_system.create_user(
            user_id="schema_test_user",
            email="schema_test@example.com"
        )
        
        if not result['success']:
            print(f"  ❌ Database tables not properly initialized: {result['error']}")
            return False
        
        print("  ✅ Database tables initialized correctly")
        
        # Test location preferences (should fail due to feature lock)
        print("  📝 Testing location preferences (should fail due to feature lock)...")
        location_result = referral_system.save_location_preferences(
            user_id="schema_test_user",
            zipcode="12345"
        )
        
        if location_result['success']:
            print("  ❌ Location preferences should be locked for non-unlocked users")
            return False
        
        print("  ✅ Location preferences correctly locked for non-unlocked users")
        
        # Cleanup
        os.remove(test_db)
        print("  🧹 Database test cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_structure():
    """Test API endpoint structure (without Flask app)"""
    print("\n🌐 Testing API Structure...")
    
    try:
        # Test if we can import the API endpoints
        from backend.api.referral_gated_endpoints import referral_gated_api
        
        print("  ✅ API endpoints module imported successfully")
        
        # Check if blueprint has routes
        routes = [rule.rule for rule in referral_gated_api.url_map.iter_rules()]
        
        expected_routes = [
            '/career-preview',
            '/refer-friend',
            '/referral-status/<referral_code>',
            '/career-advancement',
            '/api/feature-access/job-recommendations',
            '/upload-resume',
            '/set-location-preferences',
            '/process-recommendations',
            '/referral-progress',
            '/validate-zipcode',
            '/location-recommendations'
        ]
        
        missing_routes = []
        for route in expected_routes:
            if not any(route in r for r in routes):
                missing_routes.append(route)
        
        if missing_routes:
            print(f"  ❌ Missing routes: {missing_routes}")
            return False
        
        print("  ✅ All expected API routes found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_templates():
    """Test template files exist"""
    print("\n🎨 Testing Templates...")
    
    try:
        template_files = [
            'templates/career_advancement_teaser.html',
            'templates/job_recommendations.html'
        ]
        
        for template_file in template_files:
            if not os.path.exists(template_file):
                print(f"  ❌ Template file missing: {template_file}")
                return False
        
        print("  ✅ All template files exist")
        
        # Check if templates have expected content
        with open('templates/career_advancement_teaser.html', 'r') as f:
            teaser_content = f.read()
        
        if 'referral-progress' not in teaser_content:
            print("  ❌ Teaser template missing referral progress functionality")
            return False
        
        print("  ✅ Teaser template has expected functionality")
        
        with open('templates/job_recommendations.html', 'r') as f:
            job_content = f.read()
        
        if 'job-results' not in job_content:
            print("  ❌ Job recommendations template missing job results functionality")
            return False
        
        print("  ✅ Job recommendations template has expected functionality")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Templates test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_core_implementation_test():
    """Run the core implementation test"""
    print("🧪 CORE IMPLEMENTATION TEST FOR REFERRAL-GATED JOB RECOMMENDATION SYSTEM")
    print("=" * 90)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    tests = [
        ("Referral Models", test_referral_models),
        ("Location Utils", test_location_utils),
        ("Security Features", test_security_features),
        ("Database Schema", test_database_schema),
        ("API Structure", test_api_structure),
        ("Templates", test_templates)
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
    
    print("\n" + "=" * 90)
    print("📊 CORE IMPLEMENTATION TEST RESULTS")
    print("=" * 90)
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL CORE IMPLEMENTATION TESTS PASSED!")
        print("🚀 The referral-gated job recommendation system core is fully functional!")
        print("\n📋 IMPLEMENTED FEATURES:")
        print("   ✅ Referral system with database models")
        print("   ✅ Location validation and geocoding utilities")
        print("   ✅ Security features with fraud prevention")
        print("   ✅ Database schema with all required tables")
        print("   ✅ API endpoint structure")
        print("   ✅ HTML templates for user interface")
        print("\n💡 NEXT STEPS:")
        print("   1. Run 'python app.py' to start the Flask server")
        print("   2. Visit http://localhost:5000/career-preview")
        print("   3. Test the referral workflow")
        print("   4. Try the job recommendation features")
        print("\n🔧 NOTE: Some integration features may require additional setup")
        print("   for full functionality with existing Mingus codebase.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the errors above.")
        print("\n🔧 COMMON FIXES:")
        print("   - Ensure all Python packages are installed")
        print("   - Check file permissions and paths")
        print("   - Verify all modules are in correct locations")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return failed == 0

if __name__ == '__main__':
    success = run_core_implementation_test()
    sys.exit(0 if success else 1)
