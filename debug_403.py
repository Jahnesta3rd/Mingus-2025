#!/usr/bin/env python3
"""
Debug script to identify what's causing 403 errors
"""

import requests
import sys

def test_endpoint(url, headers=None):
    """Test an endpoint and show detailed response"""
    try:
        print(f"\nTesting: {url}")
        print(f"Headers: {headers or 'None'}")
        
        r = requests.get(url, headers=headers or {}, timeout=5)
        
        print(f"Status Code: {r.status_code}")
        print(f"Response Headers:")
        for key, value in r.headers.items():
            if 'cors' in key.lower() or 'access-control' in key.lower():
                print(f"  {key}: {value}")
        
        print(f"Response Body: {r.text[:200]}")
        
        if r.status_code == 403:
            print("❌ 403 Forbidden - Request blocked")
            return False
        elif r.status_code == 200:
            print("✅ 200 OK - Request successful")
            return True
        else:
            print(f"⚠️ Status {r.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    base_url = "http://localhost:5000"
    
    print("="*70)
    print("403 Error Debugging")
    print("="*70)
    
    # Test 1: No headers
    test_endpoint(f"{base_url}/health")
    
    # Test 2: With Origin header
    test_endpoint(f"{base_url}/health", headers={'Origin': 'http://localhost:3000'})
    
    # Test 3: With all CORS headers
    test_endpoint(f"{base_url}/health", headers={
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    })
    
    print("\n" + "="*70)
