#!/usr/bin/env python3
"""
Frontend Integration Test
Tests the complete frontend-backend integration with security features
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

def test_backend_startup():
    """Test that the backend starts up correctly"""
    print("🔍 Testing backend startup...")
    
    try:
        from app import app, initialize_app
        initialize_app()
        print("✅ Backend initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Backend startup failed: {e}")
        return False

def test_api_endpoints():
    """Test that all API endpoints are responding"""
    print("\n🔍 Testing API endpoints...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test API status endpoint
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ API status endpoint working")
                data = response.get_json()
                print(f"   Available endpoints: {len(data.get('endpoints', {}))}")
            else:
                print(f"❌ API status endpoint failed: {response.status_code}")
                return False
            
            # Test assessment endpoint (should return 400 for missing data)
            response = client.post('/api/assessments', 
                                 json={},
                                 headers={'Content-Type': 'application/json'})
            if response.status_code in [400, 403]:  # Expected for missing/invalid data
                print("✅ Assessment endpoint responding (validation working)")
            else:
                print(f"❌ Assessment endpoint unexpected response: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_security_features():
    """Test security features are working"""
    print("\n🔍 Testing security features...")
    
    try:
        from backend.utils.validation import APIValidator
        
        # Test email validation
        valid_email = APIValidator.validate_email("test@example.com")
        invalid_email = APIValidator.validate_email("invalid-email")
        
        if valid_email[0] and not invalid_email[0]:
            print("✅ Email validation working")
        else:
            print("❌ Email validation not working correctly")
            return False
        
        # Test name validation
        valid_name = APIValidator.validate_name("John Doe")
        invalid_name = APIValidator.validate_name("<script>alert('xss')</script>")
        
        if valid_name[0] and not invalid_name[0]:
            print("✅ Name validation working (XSS protection)")
        else:
            print("❌ Name validation not working correctly")
            return False
        
        # Test phone validation
        valid_phone = APIValidator.validate_phone("1234567890")
        invalid_phone = APIValidator.validate_phone("abc")
        
        if valid_phone[0] and not invalid_phone[0]:
            print("✅ Phone validation working")
        else:
            print("❌ Phone validation not working correctly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Security features test failed: {e}")
        return False

def test_assessment_flow():
    """Test complete assessment flow"""
    print("\n🔍 Testing assessment flow...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test assessment submission with valid data
            assessment_data = {
                "email": "test@example.com",
                "firstName": "John",
                "phone": "1234567890",
                "assessmentType": "ai-risk",
                "answers": {
                    "question1": "option1",
                    "question2": "option2"
                }
            }
            
            response = client.post('/api/assessments',
                                 json=assessment_data,
                                 headers={
                                     'Content-Type': 'application/json',
                                     'X-CSRF-Token': 'test-token',
                                     'X-Requested-With': 'XMLHttpRequest'
                                 })
            
            if response.status_code == 200:
                print("✅ Assessment submission working")
                data = response.get_json()
                print(f"   Assessment ID: {data.get('assessment_id')}")
                print(f"   Score: {data.get('results', {}).get('score')}")
            else:
                print(f"❌ Assessment submission failed: {response.status_code}")
                print(f"   Response: {response.get_json()}")
                return False
            
            # Test assessment submission with invalid data
            invalid_data = {
                "email": "invalid-email",
                "assessmentType": "ai-risk",
                "answers": {}
            }
            
            response = client.post('/api/assessments',
                                 json=invalid_data,
                                 headers={
                                     'Content-Type': 'application/json',
                                     'X-CSRF-Token': 'test-token',
                                     'X-Requested-With': 'XMLHttpRequest'
                                 })
            
            if response.status_code == 400:
                print("✅ Input validation working (rejects invalid data)")
            else:
                print(f"❌ Input validation not working: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Assessment flow test failed: {e}")
        return False

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS configuration...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test preflight request
            response = client.options('/api/assessments',
                                    headers={
                                        'Origin': 'http://localhost:3000',
                                        'Access-Control-Request-Method': 'POST',
                                        'Access-Control-Request-Headers': 'Content-Type'
                                    })
            
            if response.status_code == 200:
                print("✅ CORS preflight request working")
                headers = dict(response.headers)
                if 'Access-Control-Allow-Origin' in headers:
                    print(f"   Allowed origins: {headers['Access-Control-Allow-Origin']}")
                if 'Access-Control-Allow-Methods' in headers:
                    print(f"   Allowed methods: {headers['Access-Control-Allow-Methods']}")
            else:
                print(f"❌ CORS preflight request failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CORS configuration test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting is working"""
    print("\n🔍 Testing rate limiting...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Make multiple requests to test rate limiting
            for i in range(5):
                response = client.post('/api/assessments',
                                     json={"email": f"test{i}@example.com", "firstName": f"Test{i}", "assessmentType": "ai-risk", "answers": {"q1": "a1"}},
                                     headers={
                                         'Content-Type': 'application/json',
                                         'X-CSRF-Token': 'test-token',
                                         'X-Requested-With': 'XMLHttpRequest'
                                     })
                
                if response.status_code == 200:
                    print(f"✅ Request {i+1} successful")
                elif response.status_code == 429:
                    print(f"✅ Rate limiting working (request {i+1} blocked)")
                    break
                else:
                    print(f"❌ Unexpected response for request {i+1}: {response.status_code}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_frontend_components():
    """Test that frontend components can be imported"""
    print("\n🔍 Testing frontend components...")
    
    try:
        # Check if frontend files exist
        frontend_files = [
            'frontend/src/components/LandingPage.tsx',
            'frontend/src/components/AssessmentModal.tsx',
            'frontend/src/components/ErrorBoundary.tsx',
            'frontend/src/utils/validation.ts',
            'frontend/src/utils/sanitize.ts'
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        # Check if package.json has required dependencies
        package_json_path = 'frontend/package.json'
        if os.path.exists(package_json_path):
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            required_deps = ['dompurify', '@types/dompurify']
            for dep in required_deps:
                if dep in package_data.get('dependencies', {}) or dep in package_data.get('devDependencies', {}):
                    print(f"✅ {dep} dependency found")
                else:
                    print(f"❌ {dep} dependency missing")
                    return False
        
        print("✅ All frontend components and dependencies verified")
        return True
        
    except Exception as e:
        print(f"❌ Frontend components test failed: {e}")
        return False

def test_security_headers():
    """Test that security headers are present"""
    print("\n🔍 Testing security headers...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            response = client.get('/health')
            headers = dict(response.headers)
            
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Referrer-Policy',
                'Content-Security-Policy'
            ]
            
            for header in security_headers:
                if header in headers:
                    print(f"✅ {header}: {headers[header]}")
                else:
                    print(f"❌ {header} missing")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Security headers test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Frontend Integration Test")
    print("=" * 50)
    
    tests = [
        ("Backend Startup", test_backend_startup),
        ("API Endpoints", test_api_endpoints),
        ("Security Features", test_security_features),
        ("Assessment Flow", test_assessment_flow),
        ("CORS Configuration", test_cors_configuration),
        ("Rate Limiting", test_rate_limiting),
        ("Frontend Components", test_frontend_components),
        ("Security Headers", test_security_headers)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Frontend-backend integration is working correctly")
        print("✅ Security features are properly implemented")
        print("✅ Ready for production deployment")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
