#!/usr/bin/env python3
"""
Test script for MINGUS Article Library Integration
Verifies that the article library is properly integrated with the Flask application
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_article_library_integration():
    """Test the article library integration"""
    
    print("🧪 Testing MINGUS Article Library Integration")
    print("=" * 50)
    
    # Base URL for testing
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/api/health",
        "/api/articles/status",
        "/api/articles/config",
        "/api/articles",
        "/api/articles/topics",
        "/api/articles/filters"
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Success: {response.status_code}")
                data = response.json()
                
                # Pretty print the response for key endpoints
                if endpoint == "/api/health":
                    print("📊 Health Check Results:")
                    print(f"   Status: {data.get('status', 'unknown')}")
                    print(f"   Database: {data.get('database', 'unknown')}")
                    if 'article_library' in data:
                        al = data['article_library']
                        print(f"   Article Library: {al.get('status', 'unknown')}")
                        print(f"   Article Count: {al.get('article_count', 0)}")
                    
                    if 'features' in data:
                        print("   Features:")
                        for feature, enabled in data['features'].items():
                            status = "✅" if enabled else "❌"
                            print(f"     {status} {feature}")
                
                elif endpoint == "/api/articles/status":
                    print("📊 Article Library Status:")
                    if 'article_library' in data:
                        al = data['article_library']
                        for key, value in al.items():
                            status = "✅" if value else "❌"
                            print(f"   {status} {key}: {value}")
                
                elif endpoint == "/api/articles/config":
                    print("⚙️ Article Library Configuration:")
                    if 'config' in data:
                        config = data['config']
                        for section, settings in config.items():
                            print(f"   📁 {section}:")
                            if isinstance(settings, dict):
                                for key, value in settings.items():
                                    if key in ['api_key', 'mac_email_address', 'mac_email_app_password']:
                                        value = '***' if value else 'Not set'
                                    print(f"     {key}: {value}")
                            else:
                                print(f"     {settings}")
                
                results.append({
                    'endpoint': endpoint,
                    'status': 'success',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                })
                
            elif response.status_code == 404:
                print(f"⚠️ Not Found: {response.status_code}")
                results.append({
                    'endpoint': endpoint,
                    'status': 'not_found',
                    'status_code': response.status_code
                })
                
            elif response.status_code == 401:
                print(f"🔒 Unauthorized: {response.status_code}")
                results.append({
                    'endpoint': endpoint,
                    'status': 'unauthorized',
                    'status_code': response.status_code
                })
                
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                
                results.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'status_code': response.status_code
                })
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Flask application not running")
            results.append({
                'endpoint': endpoint,
                'status': 'connection_error',
                'error': 'Flask application not running'
            })
            break
            
        except requests.exceptions.Timeout:
            print("⏰ Timeout: Request took too long")
            results.append({
                'endpoint': endpoint,
                'status': 'timeout',
                'error': 'Request timeout'
            })
            
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            results.append({
                'endpoint': endpoint,
                'status': 'error',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 Integration Test Summary")
    print("=" * 50)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 All tests passed! Article library integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the Flask application logs for details.")
    
    # Print detailed results
    print("\n📊 Detailed Results:")
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_icon} {result['endpoint']}: {result['status']}")
        if 'response_time' in result:
            print(f"      Response time: {result['response_time']:.3f}s")
    
    return successful == total

def test_environment_configuration():
    """Test environment configuration"""
    
    print("\n🔧 Testing Environment Configuration")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY',
        'OPENAI_API_KEY'
    ]
    
    optional_vars = [
        'MAC_EMAIL_ADDRESS',
        'MAC_EMAIL_APP_PASSWORD',
        'ENABLE_ARTICLE_LIBRARY',
        'ENABLE_AI_RECOMMENDATIONS',
        'ENABLE_CULTURAL_PERSONALIZATION'
    ]
    
    print("📋 Required Environment Variables:")
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Not set")
            missing_required.append(var)
    
    print("\n📋 Optional Environment Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️ {var}: Not set (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        print("Please set these variables in your .env file")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def main():
    """Main test function"""
    
    print("🚀 MINGUS Article Library Integration Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test environment configuration
    env_ok = test_environment_configuration()
    
    if not env_ok:
        print("\n❌ Environment configuration test failed. Please fix the issues above.")
        sys.exit(1)
    
    # Test Flask application integration
    integration_ok = test_article_library_integration()
    
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    
    if env_ok and integration_ok:
        print("🎉 All tests passed! Article library is ready for use.")
        print("\n📚 Next steps:")
        print("   1. Start the Flask application: python backend/app_article_library.py")
        print("   2. Access the article library at: http://localhost:5000/api/articles")
        print("   3. Check health status at: http://localhost:5000/api/health")
        print("   4. View configuration at: http://localhost:5000/api/articles/config")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
