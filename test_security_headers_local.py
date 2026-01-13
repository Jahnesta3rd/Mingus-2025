#!/usr/bin/env python3
"""
Test security headers using Flask test client (no server needed)
"""

import sys
sys.path.insert(0, '.')

from app import app

def test_security_headers():
    """Test that security headers are present on responses"""
    print("=" * 70)
    print("Testing Security Headers with Flask Test Client")
    print("=" * 70)
    print()
    
    with app.test_client() as client:
        # Test /health endpoint
        print("Testing /health endpoint...")
        response = client.get('/health')
        print(f"Status Code: {response.status_code}")
        print()
        
        # Check security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': None,  # Just check if present
        }
        
        print("Security Headers:")
        print("-" * 70)
        all_present = True
        for header_name, expected_value in security_headers.items():
            header_value = response.headers.get(header_name)
            if header_value:
                status = "✅"
                if expected_value and header_value != expected_value:
                    status = "⚠️"
                    print(f"{status} {header_name}: {header_value} (expected: {expected_value})")
                else:
                    print(f"{status} {header_name}: {header_value}")
            else:
                status = "❌"
                all_present = False
                print(f"{status} {header_name}: MISSING")
        
        print("-" * 70)
        print()
        
        if all_present:
            print("✅ All security headers are present!")
        else:
            print("❌ Some security headers are missing")
        
        print()
        print("=" * 70)
        return all_present

if __name__ == '__main__':
    try:
        success = test_security_headers()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
