#!/usr/bin/env python3
"""
CORS Security Test Script
Tests for CORS bypass vulnerabilities and validates security configuration
"""

import requests
import json
import sys
import argparse
from urllib.parse import urljoin

def test_cors_preflight(host, port, endpoint="/", use_https=False):
    """Test CORS preflight request"""
    protocol = "https" if use_https else "http"
    base_url = f"{protocol}://{host}:{port}"
    test_url = urljoin(base_url, endpoint)
    
    print(f"🔍 Testing CORS preflight for: {test_url}")
    
    # Test 1: Basic CORS preflight with malicious origin
    headers = {
        "Origin": "https://malicious-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    try:
        # Disable SSL verification for local testing
        response = requests.options(
            test_url, 
            headers=headers, 
            timeout=10,
            verify=False if use_https else True
        )
        print(f"✅ Preflight response status: {response.status_code}")
        print(f"📋 CORS headers found:")
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
            "Access-Control-Max-Age": response.headers.get("Access-Control-Max-Age")
        }
        
        for header, value in cors_headers.items():
            print(f"   {header}: {value}")
            
        # Check for vulnerabilities
        vulnerabilities = []
        
        # For malicious origins, NO CORS headers is actually SECURE behavior
        if cors_headers["Access-Control-Allow-Origin"] == "*":
            vulnerabilities.append("❌ CORS_ALLOW_ORIGIN_WILDCARD - Allows any origin")
        
        if cors_headers["Access-Control-Allow-Credentials"] == "true" and cors_headers["Access-Control-Allow-Origin"] == "*":
            vulnerabilities.append("❌ CREDENTIALS_WITH_WILDCARD - Credentials allowed with wildcard origin")
            
        # Missing CORS headers for malicious origins is SECURE, not a vulnerability
        if not cors_headers["Access-Control-Allow-Origin"]:
            print("✅ SECURE: No CORS headers for malicious origin - prevents cross-origin access")
            
        if cors_headers["Access-Control-Allow-Methods"] and "DELETE" in cors_headers["Access-Control-Allow-Methods"]:
            vulnerabilities.append("⚠️  DELETE_METHOD_ALLOWED - DELETE method allowed (potential risk)")
            
        if vulnerabilities:
            print("\n🚨 CORS VULNERABILITIES DETECTED:")
            for vuln in vulnerabilities:
                print(f"   {vuln}")
        else:
            print("\n✅ No CORS vulnerabilities detected")
            
        return vulnerabilities
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return ["Request failed"]

def test_cors_actual_request(host, port, endpoint="/", use_https=False):
    """Test actual CORS request"""
    protocol = "https" if use_https else "http"
    base_url = f"{protocol}://{host}:{port}"
    test_url = urljoin(base_url, endpoint)
    
    print(f"\n🔍 Testing actual CORS request for: {test_url}")
    
    # Test with malicious origin
    headers = {
        "Origin": "https://malicious-site.com",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            test_url, 
            headers=headers, 
            timeout=10,
            verify=False if use_https else True
        )
        print(f"✅ Actual request response status: {response.status_code}")
        
        # Check if the response includes the malicious origin in CORS headers
        if "Access-Control-Allow-Origin" in response.headers:
            origin = response.headers["Access-Control-Allow-Origin"]
            if origin == "https://malicious-site.com":
                print("❌ CORS_ORIGIN_REFLECTION - Server reflects the request origin")
                return ["CORS_ORIGIN_REFLECTION"]
            elif origin == "*":
                print("❌ CORS_WILDCARD_ORIGIN - Server allows any origin")
                return ["CORS_WILDCARD_ORIGIN"]
            else:
                print(f"✅ CORS origin properly restricted to: {origin}")
        else:
            print("✅ SECURE: No CORS headers for malicious origin - prevents cross-origin access")
            
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return ["Request failed"]

def test_cors_bypass_techniques(host, port, endpoint="/", use_https=False):
    """Test various CORS bypass techniques"""
    protocol = "https" if use_https else "http"
    base_url = f"{protocol}://{host}:{port}"
    test_url = urljoin(base_url, endpoint)
    
    print(f"\n🔍 Testing CORS bypass techniques for: {test_url}")
    
    bypass_techniques = [
        {
            "name": "Null Origin",
            "headers": {"Origin": "null"}
        },
        {
            "name": "Protocol Relative Origin",
            "headers": {"Origin": "//malicious-site.com"}
        },
        {
            "name": "Subdomain Bypass",
            "headers": {"Origin": "https://subdomain.yourdomain.com"}
        },
        {
            "name": "Port Bypass",
            "headers": {"Origin": "https://yourdomain.com:8080"}
        },
        {
            "name": "Path Traversal Origin",
            "headers": {"Origin": "https://yourdomain.com.evil.com"}
        }
    ]
    
    vulnerabilities = []
    
    for technique in bypass_techniques:
        try:
            response = requests.options(
                test_url, 
                headers=technique["headers"], 
                timeout=10,
                verify=False if use_https else True
            )
            print(f"🔍 Testing: {technique['name']}")
            
            if "Access-Control-Allow-Origin" in response.headers:
                origin = response.headers["Access-Control-Allow-Origin"]
                if origin == technique["headers"]["Origin"] or origin == "*":
                    print(f"   ❌ {technique['name']} bypass successful")
                    vulnerabilities.append(f"{technique['name']}_BYPASS")
                else:
                    print(f"   ✅ {technique['name']} properly blocked")
            else:
                print(f"   ✅ {technique['name']} - No CORS headers (SECURE)")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {technique['name']} test failed: {e}")
            
    return vulnerabilities

def test_legitimate_origin(host, port, endpoint="/", use_https=False):
    """Test CORS with legitimate origin to ensure it works"""
    protocol = "https" if use_https else "http"
    base_url = f"{protocol}://{host}:{port}"
    test_url = urljoin(base_url, endpoint)
    
    print(f"\n🔍 Testing CORS with legitimate origin: {test_url}")
    
    # Test with legitimate origin
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    try:
        response = requests.options(
            test_url, 
            headers=headers, 
            timeout=10,
            verify=False if use_https else True
        )
        print(f"✅ Legitimate origin preflight status: {response.status_code}")
        
        if "Access-Control-Allow-Origin" in response.headers:
            origin = response.headers["Access-Control-Allow-Origin"]
            print(f"✅ CORS headers present for legitimate origin: {origin}")
            return []
        else:
            print("❌ No CORS headers for legitimate origin - CORS not working")
            return ["CORS_NOT_WORKING"]
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return ["Request failed"]

def generate_security_report(vulnerabilities):
    """Generate a security report"""
    print(f"\n📊 CORS SECURITY REPORT")
    print("=" * 50)
    
    if not vulnerabilities:
        print("✅ No CORS vulnerabilities detected")
        print("✅ CORS configuration appears secure")
        return
        
    print(f"🚨 {len(vulnerabilities)} CORS vulnerabilities detected:")
    for vuln in vulnerabilities:
        print(f"   • {vuln}")
        
    print("\n🔧 RECOMMENDATIONS:")
    print("   1. Update Flask-CORS to version 6.0.0+")
    print("   2. Implement strict origin validation")
    print("   3. Disable wildcard origins")
    print("   4. Implement proper CORS policy")
    print("   5. Add security headers")

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="CORS Security Test Script")
    parser.add_argument("--host", default="localhost", help="Host to test (default: localhost)")
    parser.add_argument("--port", type=int, default=5001, help="Port to test (default: 5001)")
    parser.add_argument("--endpoint", default="/", help="Endpoint to test (default: /)")
    parser.add_argument("--https", action="store_true", help="Use HTTPS instead of HTTP")
    parser.add_argument("--test", choices=["preflight", "actual", "bypass", "legitimate", "all"], 
                       default="all", help="Type of test to run (default: all)")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting CORS Security Test on {args.host}:{args.port}")
    print(f"🔒 Protocol: {'HTTPS' if args.https else 'HTTP'}")
    print(f"🎯 Endpoint: {args.endpoint}")
    print(f"🧪 Test Type: {args.test}")
    print("=" * 60)
    
    # Suppress SSL warnings for local testing
    if args.https:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    all_vulnerabilities = []
    
    # Run selected tests
    if args.test in ["preflight", "all"]:
        vulns = test_cors_preflight(args.host, args.port, args.endpoint, args.https)
        all_vulnerabilities.extend(vulns)
    
    if args.test in ["actual", "all"]:
        vulns = test_cors_actual_request(args.host, args.port, args.endpoint, args.https)
        all_vulnerabilities.extend(vulns)
    
    if args.test in ["bypass", "all"]:
        vulns = test_cors_bypass_techniques(args.host, args.port, args.endpoint, args.https)
        all_vulnerabilities.extend(vulns)
    
    if args.test in ["legitimate", "all"]:
        vulns = test_legitimate_origin(args.host, args.port, args.endpoint, args.https)
        all_vulnerabilities.extend(vulns)
    
    # Generate report
    generate_security_report(all_vulnerabilities)
    
    # Exit with error code if vulnerabilities found
    if all_vulnerabilities:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
