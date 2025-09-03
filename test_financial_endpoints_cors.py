#!/usr/bin/env python3
"""
Test CORS on Sensitive Financial Endpoints
Properly validates that malicious origins are blocked while legitimate origins work.
"""

import requests
import sys
from typing import Dict

def test_financial_endpoint_cors(endpoint: str, base_url: str = "http://localhost:5001") -> Dict:
    """Test CORS security for a specific financial endpoint"""
    
    test_results = {
        "endpoint": endpoint,
        "malicious_origin_blocked": False,
        "legitimate_origin_allowed": False,
        "security_status": "UNKNOWN"
    }
    
    print(f"\n🔍 Testing: {endpoint}")
    print("-" * 50)
    
    # Test 1: Malicious origin (should be BLOCKED)
    print("🚨 Testing malicious origin (should be BLOCKED):")
    try:
        response = requests.options(
            f"{base_url}{endpoint}",
            headers={
                "Origin": "https://yourdomain.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10,
            allow_redirects=True
        )
        
        # Check if CORS headers are present
        has_cors_headers = "Access-Control-Allow-Origin" in response.headers
        
        if not has_cors_headers:
            print("   ✅ https://yourdomain.com → BLOCKED (SECURE)")
            test_results["malicious_origin_blocked"] = True
        else:
            print("   ❌ https://yourdomain.com → ALLOWED (CRITICAL SECURITY ISSUE)")
            test_results["malicious_origin_blocked"] = False
            
    except Exception as e:
        print(f"   ⚠️  Request failed: {e}")
        test_results["malicious_origin_blocked"] = False
    
    # Test 2: Legitimate origin (should be ALLOWED)
    print("\n✅ Testing legitimate origin (should be ALLOWED):")
    try:
        response = requests.options(
            f"{base_url}{endpoint}",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10,
            allow_redirects=True
        )
        
        # Check if CORS headers are present
        has_cors_headers = "Access-Control-Allow-Origin" in response.headers
        
        if has_cors_headers:
            print("   ✅ http://localhost:3000 → ALLOWED (FUNCTIONAL)")
            test_results["legitimate_origin_allowed"] = True
        else:
            print("   ❌ http://localhost:3000 → BLOCKED (FUNCTIONALITY ISSUE)")
            test_results["legitimate_origin_allowed"] = False
            
    except Exception as e:
        print(f"   ⚠️  Request failed: {e}")
        test_results["legitimate_origin_allowed"] = False
    
    # Determine security status
    if test_results["malicious_origin_blocked"] and test_results["legitimate_origin_allowed"]:
        test_results["security_status"] = "SECURE"
        print(f"\n   🎯 Security Status: ✅ SECURE")
    elif test_results["malicious_origin_blocked"] and not test_results["legitimate_origin_allowed"]:
        test_results["security_status"] = "PARTIALLY_SECURE"
        print(f"\n   🎯 Security Status: ⚠️  PARTIALLY SECURE (functionality issue)")
    elif not test_results["malicious_origin_blocked"]:
        test_results["security_status"] = "VULNERABLE"
        print(f"\n   🎯 Security Status: ❌ VULNERABLE (security issue)")
    else:
        test_results["security_status"] = "UNKNOWN"
        print(f"\n   🎯 Security Status: ❓ UNKNOWN")
    
    return test_results

def main():
    """Main test function"""
    print("🚀 Testing CORS Security on Sensitive Financial Endpoints")
    print("=" * 80)
    print("This test validates that:")
    print("  • Malicious origins are BLOCKED (security)")
    print("  • Legitimate origins are ALLOWED (functionality)")
    print()
    
    # Financial endpoints to test
    financial_endpoints = [
        '/api/financial/forecast',
        '/api/financial/balance', 
        '/api/payments/history',
        '/api/user/profile'
    ]
    
    # Test each endpoint
    all_results = []
    secure_endpoints = 0
    total_endpoints = len(financial_endpoints)
    
    for endpoint in financial_endpoints:
        result = test_financial_endpoint_cors(endpoint)
        all_results.append(result)
        
        if result["security_status"] == "SECURE":
            secure_endpoints += 1
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("📊 CORS SECURITY TEST SUMMARY")
    print("=" * 80)
    print(f"Endpoints Tested: {total_endpoints}")
    print(f"Secure Endpoints: {secure_endpoints}")
    print(f"Security Score: {secure_endpoints}/{total_endpoints}")
    
    # Detailed results
    print(f"\n🔍 DETAILED RESULTS:")
    for result in all_results:
        status_icon = "✅" if result["security_status"] == "SECURE" else "❌"
        print(f"   {status_icon} {result['endpoint']}: {result['security_status']}")
    
    # Security assessment
    print(f"\n🔒 SECURITY ASSESSMENT:")
    if secure_endpoints == total_endpoints:
        print("   ✅ ALL endpoints are SECURE")
        print("   ✅ CORS bypass vulnerabilities: NONE")
        print("   ✅ Malicious origins properly blocked")
        print("   ✅ Legitimate origins working correctly")
        print("\n🎉 CORS Security Test: PASSED")
        sys.exit(0)
    else:
        print("   ❌ Some endpoints have security issues")
        print("   ❌ CORS bypass vulnerabilities: PRESENT")
        print("   ⚠️  Immediate action required")
        print("\n🚨 CORS Security Test: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
