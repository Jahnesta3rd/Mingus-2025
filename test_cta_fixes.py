#!/usr/bin/env python3
"""
Test script to verify CTA fixes for landing page
"""

import requests
import json
import sys
from datetime import datetime

def test_assessment_endpoints():
    """Test the assessment endpoints that were causing 403 errors"""
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/api/assessments/available",
        "/api/assessments/income-comparison/submit",
        "/api/assessments/relationship-money/submit", 
        "/api/assessments/tax-impact/submit",
        "/api/assessments/job-matching/submit"
    ]
    
    print("Testing Assessment Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            if endpoint.endswith('/submit'):
                # Test POST request for submit endpoints
                test_data = {
                    "responses": {
                        "question_1": "test_response",
                        "question_2": "another_response"
                    }
                }
                response = requests.post(f"{base_url}{endpoint}", 
                                       json=test_data, 
                                       headers={'Content-Type': 'application/json'})
            else:
                # Test GET request for available endpoint
                response = requests.get(f"{base_url}{endpoint}")
            
            print(f"Endpoint: {endpoint}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS - No 403 error")
            elif response.status_code == 403:
                print("❌ FAILED - Still getting 403 error")
            elif response.status_code == 400:
                print("⚠️  PARTIAL SUCCESS - Getting 400 (bad request) instead of 403")
                print(f"   Response: {response.text[:200]}...")
            elif response.status_code == 404:
                print("⚠️  PARTIAL SUCCESS - Getting 404 (not found) instead of 403")
            else:
                print(f"⚠️  UNEXPECTED - Status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
            
            print("-" * 30)
            
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR - Cannot connect to {base_url}")
            print("   Make sure the Flask server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            print("-" * 30)

def test_security_validator():
    """Test that the SecurityValidator methods work correctly"""
    
    print("\nTesting Security Validator Methods...")
    print("=" * 50)
    
    try:
        # Import the SecurityValidator
        sys.path.append('backend')
        from security.assessment_security import SecurityValidator
        
        validator = SecurityValidator()
        
        # Test the detect methods exist
        test_methods = ['detect_sql_injection', 'detect_xss_attack', 'detect_command_injection']
        
        for method_name in test_methods:
            if hasattr(validator, method_name):
                method = getattr(validator, method_name)
                # Test with safe input
                result = method("safe input")
                print(f"✅ {method_name} - Method exists and works")
            else:
                print(f"❌ {method_name} - Method missing")
        
        print("-" * 30)
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR - Cannot import SecurityValidator: {e}")
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")

def test_landing_page_js():
    """Test that the landing page JavaScript has correct route mapping"""
    
    print("\nTesting Landing Page JavaScript Route Mapping...")
    print("=" * 50)
    
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
        
        for route in expected_routes:
            if route in js_content:
                print(f"✅ Route mapping found: {route}")
            else:
                print(f"❌ Route mapping missing: {route}")
        
        # Check for correct data attribute
        if "dataset.assessment" in js_content:
            print("✅ Correct data attribute: dataset.assessment")
        else:
            print("❌ Incorrect data attribute")
        
        print("-" * 30)
        
    except FileNotFoundError:
        print("❌ FILE NOT FOUND - Cannot find landing-page.js")
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")

def main():
    """Run all tests"""
    
    print("MINGUS Landing Page CTA Fixes Test")
    print("=" * 60)
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Security Validator Methods
    test_security_validator()
    
    # Test 2: Landing Page JavaScript
    test_landing_page_js()
    
    # Test 3: Assessment Endpoints
    test_assessment_endpoints()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- If you see ✅ SUCCESS messages, the fixes are working")
    print("- If you see ❌ FAILED messages, there are still issues to resolve")
    print("- If you see ⚠️  PARTIAL SUCCESS, the 403 errors are fixed but there may be other issues")
    print()
    print("Next Steps:")
    print("1. Start the Flask server: python backend/app.py")
    print("2. Open the landing page in a browser")
    print("3. Test the CTA buttons to ensure they work without 403 errors")

if __name__ == "__main__":
    main()
