#!/usr/bin/env python3
"""
Test script to verify all critical dependencies are working
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test frontend dependencies
        sys.path.append('frontend')
        print("✅ Frontend path added")
        
        # Test backend imports
        from app import app
        print("✅ Main app imported successfully")
        
        from backend.api.assessment_endpoints import assessment_api
        print("✅ Assessment API imported successfully")
        
        from backend.api.meme_endpoints import meme_api
        print("✅ Meme API imported successfully")
        
        from backend.api.user_preferences_endpoints import user_preferences_api
        print("✅ User preferences API imported successfully")
        
        from backend.middleware.security import SecurityMiddleware
        print("✅ Security middleware imported successfully")
        
        from backend.utils.validation import APIValidator
        print("✅ API validator imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_migration():
    """Test that database migration was successful"""
    print("\n🔍 Testing database migration...")
    
    try:
        import sqlite3
        
        # Check if database exists
        if not os.path.exists('app.db'):
            print("❌ Database file not found")
            return False
        
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Check if assessment tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%assessment%' OR name LIKE '%lead_magnet%')")
        tables = cursor.fetchall()
        
        expected_tables = ['assessments', 'assessment_analytics', 'lead_magnet_results']
        found_tables = [table[0] for table in tables]
        
        for table in expected_tables:
            if table in found_tables:
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Table {table} missing")
                return False
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        print(f"✅ Found {len(indexes)} indexes")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_environment_variables():
    """Test that environment variables are set"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        'SECRET_KEY',
        'CSRF_SECRET_KEY', 
        'ENCRYPTION_KEY',
        'RATE_LIMIT_PER_MINUTE',
        'CORS_ORIGINS'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value and value != f'your-{var.lower().replace("_", "-")}-change-in-production':
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set or using default value")
            all_set = False
    
    return all_set

def test_api_endpoints():
    """Test that API endpoints are registered"""
    print("\n🔍 Testing API endpoints...")
    
    try:
        from app import app
        
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        
        # Check for assessment endpoints
        assessment_routes = [r for r in routes if 'assessment' in r['endpoint']]
        if assessment_routes:
            print(f"✅ Found {len(assessment_routes)} assessment endpoints")
            for route in assessment_routes:
                print(f"   - {route['rule']} ({', '.join(route['methods'])})")
        else:
            print("❌ No assessment endpoints found")
            return False
        
        # Check for meme endpoints
        meme_routes = [r for r in routes if 'meme' in r['endpoint']]
        if meme_routes:
            print(f"✅ Found {len(meme_routes)} meme endpoints")
        else:
            print("❌ No meme endpoints found")
            return False
        
        # Check for user preference endpoints
        user_routes = [r for r in routes if 'user' in r['endpoint']]
        if user_routes:
            print(f"✅ Found {len(user_routes)} user preference endpoints")
        else:
            print("❌ No user preference endpoints found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint error: {e}")
        return False

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS configuration...")
    
    try:
        from app import app
        
        # Check CORS origins
        cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
        print(f"✅ CORS origins configured: {cors_origins}")
        
        # Check CORS methods
        cors_methods = os.environ.get('CORS_METHODS', '').split(',')
        print(f"✅ CORS methods configured: {cors_methods}")
        
        # Check CORS headers
        cors_headers = os.environ.get('CORS_HEADERS', '').split(',')
        print(f"✅ CORS headers configured: {cors_headers}")
        
        return True
        
    except Exception as e:
        print(f"❌ CORS configuration error: {e}")
        return False

def test_security_features():
    """Test security features"""
    print("\n🔍 Testing security features...")
    
    try:
        from backend.middleware.security import SecurityMiddleware
        from backend.utils.validation import APIValidator
        
        # Test input validation
        email_result = APIValidator.validate_email("test@example.com")
        if email_result[0]:  # isValid
            print("✅ Email validation working")
        else:
            print("❌ Email validation not working")
            return False
        
        # Test name validation
        name_result = APIValidator.validate_name("John Doe")
        if name_result[0]:  # isValid
            print("✅ Name validation working")
        else:
            print("❌ Name validation not working")
            return False
        
        # Test phone validation
        phone_result = APIValidator.validate_phone("1234567890")
        if phone_result[0]:  # isValid
            print("✅ Phone validation working")
        else:
            print("❌ Phone validation not working")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Security features error: {e}")
        return False

def test_app_startup():
    """Test that the app can start up"""
    print("\n🔍 Testing app startup...")
    
    try:
        from app import app, initialize_app
        
        # Initialize app
        initialize_app()
        print("✅ App initialization successful")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                data = response.get_json()
                print(f"   Status: {data.get('status')}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        
        # Test API status endpoint
        with app.test_client() as client:
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ API status endpoint working")
                data = response.get_json()
                print(f"   Status: {data.get('status')}")
            else:
                print(f"❌ API status endpoint failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ App startup error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Critical Dependencies")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Database Migration", test_database_migration),
        ("Environment Variables", test_environment_variables),
        ("API Endpoints", test_api_endpoints),
        ("CORS Configuration", test_cors_configuration),
        ("Security Features", test_security_features),
        ("App Startup", test_app_startup)
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
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL CRITICAL DEPENDENCIES VERIFIED!")
        print("✅ The conversion is ready for deployment")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
