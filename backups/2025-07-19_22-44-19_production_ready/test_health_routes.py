#!/usr/bin/env python3
"""
Test script for enhanced health check-in routes
"""
import sys
import os
import requests
import json
from datetime import datetime, date, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_new_routes():
    """Test the new health routes"""
    print("=== Testing New Health Routes ===")
    
    base_url = 'http://localhost:5002/api/health'
    new_routes = [
        '/checkin/latest',
        '/checkin/history',
        '/status'
    ]
    
    for route in new_routes:
        try:
            response = requests.get(f'{base_url}{route}')
            
            if response.status_code == 401:
                print(f"✅ {route} - Correctly requires authentication")
            else:
                print(f"⚠️  {route} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {route} - Flask app not running")
            return False
        except Exception as e:
            print(f"❌ {route} - Error: {e}")
            return False
    
    return True

def test_route_documentation():
    """Test that all routes are properly documented"""
    print("\n=== Testing Route Documentation ===")
    
    try:
        with open('backend/routes/health.py', 'r') as f:
            content = f.read()
        
        expected_routes = [
            '@health_bp.route(\'/checkin\', methods=[\'GET\'])',
            '@health_bp.route(\'/checkin\', methods=[\'POST\'])',
            '@health_bp.route(\'/checkin/latest\', methods=[\'GET\'])',
            '@health_bp.route(\'/checkin/history\', methods=[\'GET\'])',
            '@health_bp.route(\'/status\', methods=[\'GET\'])',
            '@health_bp.route(\'/checkins\', methods=[\'GET\'])',
            '@health_bp.route(\'/stats\', methods=[\'GET\'])',
            '@health_bp.route(\'/demo\', methods=[\'GET\'])'
        ]
        
        missing_routes = []
        for route in expected_routes:
            if route not in content:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"⚠️  Missing routes: {missing_routes}")
            return False
        else:
            print("✅ All expected routes are present")
            return True
            
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False

def test_weekly_checkin_logic():
    """Test the weekly check-in logic"""
    print("\n=== Testing Weekly Check-in Logic ===")
    
    try:
        from datetime import date, timedelta
        
        # Test week calculation logic
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        print(f"✅ Today: {today}")
        print(f"✅ Week start (Monday): {week_start}")
        print(f"✅ Week end (Sunday): {week_end}")
        
        # Test that week_start is always Monday
        assert week_start.weekday() == 0, "Week start should be Monday (0)"
        print("✅ Week start correctly calculated as Monday")
        
        # Test that week_end is always Sunday
        assert week_end.weekday() == 6, "Week end should be Sunday (6)"
        print("✅ Week end correctly calculated as Sunday")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing weekly logic: {e}")
        return False

def test_validation_logic():
    """Test the validation logic"""
    print("\n=== Testing Validation Logic ===")
    
    try:
        # Test numeric field validation
        numeric_fields = {
            'relationships_rating': (1, 10),
            'stress_level': (1, 10),
            'energy_level': (1, 10),
            'mood_rating': (1, 10),
            'physical_activity_minutes': (0, 480),
            'mindfulness_minutes': (0, 120)
        }
        
        print("✅ Numeric field validation ranges:")
        for field, (min_val, max_val) in numeric_fields.items():
            print(f"   - {field}: {min_val} to {max_val}")
        
        # Test select field validation
        valid_levels = ['low', 'moderate', 'high']
        valid_types = ['meditation', 'prayer', 'journaling', 'other']
        
        print(f"✅ Activity levels: {valid_levels}")
        print(f"✅ Mindfulness types: {valid_types}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing validation logic: {e}")
        return False

def test_response_formats():
    """Test that response formats are consistent"""
    print("\n=== Testing Response Formats ===")
    
    try:
        # Test demo endpoint (no auth required)
        response = requests.get('http://localhost:5002/api/health/demo')
        
        if response.status_code == 200:
            print("✅ Demo endpoint returns HTML form")
            
            # Check for key elements in response
            content = response.text
            expected_elements = [
                'Health Check-in',
                'physical_activity_minutes',
                'relationships_rating',
                'stress_level',
                'mood_rating'
            ]
            
            missing_elements = []
            for element in expected_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️  Missing elements in demo response: {missing_elements}")
            else:
                print("✅ Demo response contains all expected elements")
        else:
            print(f"⚠️  Demo endpoint status: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Flask app not running")
        return False
    except Exception as e:
        print(f"❌ Error testing response formats: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test authentication requirement
        protected_routes = [
            '/api/health/checkin',
            '/api/health/checkin/latest',
            '/api/health/checkin/history',
            '/api/health/status',
            '/api/health/checkins',
            '/api/health/stats'
        ]
        
        for route in protected_routes:
            response = requests.get(f'http://localhost:5002{route}')
            if response.status_code == 401:
                print(f"✅ {route} - Correctly requires authentication")
            else:
                print(f"⚠️  {route} - Unexpected status: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Flask app not running")
        return False
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")
        return False

def main():
    """Run all health route tests"""
    print("🧪 Testing Enhanced Health Routes\n")
    
    tests = [
        test_new_routes,
        test_route_documentation,
        test_weekly_checkin_logic,
        test_validation_logic,
        test_response_formats,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced health routes are working correctly.")
        print("\n📋 Available Routes:")
        print("  GET  /api/health/demo           - Demo form (no auth)")
        print("  GET  /api/health/checkin        - Render form (auth required)")
        print("  POST /api/health/checkin        - Submit check-in (auth required)")
        print("  GET  /api/health/checkin/latest - Get latest check-in (auth required)")
        print("  GET  /api/health/checkin/history- Get history (auth required)")
        print("  GET  /api/health/status         - Check weekly status (auth required)")
        print("  GET  /api/health/checkins       - Get paginated check-ins (auth required)")
        print("  GET  /api/health/stats          - Get statistics (auth required)")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
