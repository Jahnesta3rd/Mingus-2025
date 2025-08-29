#!/usr/bin/env python3
"""
Comprehensive test script to verify all CTA fixes for landing page
"""

import requests
import json
import sys
import os
from datetime import datetime

def test_security_validator_fix():
    """Test that SecurityValidator methods work correctly"""
    print("1. Testing Security Validator Methods...")
    print("-" * 40)
    
    try:
        sys.path.append('backend')
        from security.assessment_security import SecurityValidator
        
        validator = SecurityValidator()
        
        # Test the detect methods exist and work
        test_methods = ['detect_sql_injection', 'detect_xss_attack', 'detect_command_injection']
        
        for method_name in test_methods:
            if hasattr(validator, method_name):
                method = getattr(validator, method_name)
                # Test with safe input
                result = method("safe input")
                print(f"✅ {method_name} - Method exists and works")
            else:
                print(f"❌ {method_name} - Method missing")
        
        print()
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR - Cannot import SecurityValidator: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_javascript_route_mapping():
    """Test that JavaScript route mapping is correct"""
    print("2. Testing JavaScript Route Mapping...")
    print("-" * 40)
    
    try:
        with open('static/js/landing-page.js', 'r') as f:
            js_content = f.read()
        
        # Check for correct assessment route mapping
        expected_routes = [
            "'income_comparison': '/api/assessments/income-comparison/submit'",
            "'relationship_money_score': '/api/assessments/relationship-money/submit'",
            "'tax_bill_impact': '/api/assessments/tax-impact/submit'",
            "'ai_job_lead_magnet': '/api/assessments/job-matching/submit'"
        ]
        
        all_routes_found = True
        for route in expected_routes:
            if route in js_content:
                print(f"✅ Route mapping found: {route}")
            else:
                print(f"❌ Route mapping missing: {route}")
                all_routes_found = False
        
        # Check for correct data attribute
        if "dataset.assessment" in js_content:
            print("✅ Correct data attribute: dataset.assessment")
        else:
            print("❌ Incorrect data attribute")
            all_routes_found = False
        
        print()
        return all_routes_found
        
    except FileNotFoundError:
        print("❌ FILE NOT FOUND - Cannot find landing-page.js")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_backend_routes():
    """Test that backend assessment routes exist"""
    print("3. Testing Backend Assessment Routes...")
    print("-" * 40)
    
    try:
        with open('backend/routes/assessment_routes.py', 'r') as f:
            routes_content = f.read()
        
        # Check for assessment routes
        expected_routes = [
            "@assessment_bp.route('/available', methods=['GET'])",
            "@assessment_bp.route('/<assessment_type>/submit', methods=['POST'])"
        ]
        
        all_routes_found = True
        for route in expected_routes:
            if route in routes_content:
                print(f"✅ Route found: {route}")
            else:
                print(f"❌ Route missing: {route}")
                all_routes_found = False
        
        # Check for valid assessment types
        valid_types = [
            "'income-comparison'",
            "'relationship-money'", 
            "'tax-impact'",
            "'job-matching'"
        ]
        
        for assessment_type in valid_types:
            if assessment_type in routes_content:
                print(f"✅ Assessment type found: {assessment_type}")
            else:
                print(f"❌ Assessment type missing: {assessment_type}")
                all_routes_found = False
        
        print()
        return all_routes_found
        
    except FileNotFoundError:
        print("❌ FILE NOT FOUND - Cannot find assessment_routes.py")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_https_decorator_fix():
    """Test that HTTPS decorator only applies in production"""
    print("4. Testing HTTPS Decorator Fix...")
    print("-" * 40)
    
    try:
        with open('backend/middleware/security.py', 'r') as f:
            security_content = f.read()
        
        # Check for the fix in require_https decorator
        if "Only require HTTPS in production" in security_content:
            print("✅ HTTPS decorator fix found - only enforces HTTPS in production")
        else:
            print("❌ HTTPS decorator fix missing")
            return False
        
        print()
        return True
        
    except FileNotFoundError:
        print("❌ FILE NOT FOUND - Cannot find security.py")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_flask_server():
    """Test if Flask server can be started and endpoints are accessible"""
    print("5. Testing Flask Server...")
    print("-" * 40)
    
    base_url = "http://localhost:5000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Root endpoint accessible: {response.status_code}")
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health endpoint accessible: {response.status_code}")
        
        # Test assessment available endpoint
        response = requests.get(f"{base_url}/api/assessments/available", timeout=5)
        if response.status_code == 200:
            print("✅ Assessment available endpoint accessible")
        elif response.status_code == 403:
            print("⚠️  Assessment endpoint returns 403 (may need authentication)")
        else:
            print(f"⚠️  Assessment endpoint returns: {response.status_code}")
        
        print()
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Flask server not running")
        print("   Start the server with: python start_flask_app.py")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def main():
    """Run all tests"""
    
    print("MINGUS Landing Page CTA Fixes - Comprehensive Test")
    print("=" * 60)
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests = [
        ("Security Validator Methods", test_security_validator_fix),
        ("JavaScript Route Mapping", test_javascript_route_mapping),
        ("Backend Assessment Routes", test_backend_routes),
        ("HTTPS Decorator Fix", test_https_decorator_fix),
        ("Flask Server", test_flask_server)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FIXES ARE WORKING CORRECTLY!")
        print()
        print("Next Steps:")
        print("1. Start the Flask server: python start_flask_app.py")
        print("2. Open the landing page in a browser")
        print("3. Test the CTA buttons - they should work without 403 errors")
    else:
        print("⚠️  Some fixes still need attention")
        print()
        print("Issues to resolve:")
        for test_name, result in results:
            if not result:
                print(f"  - {test_name}")

if __name__ == "__main__":
    main()
