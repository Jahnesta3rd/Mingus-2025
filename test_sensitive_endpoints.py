#!/usr/bin/env python3
"""
Test CORS Security on Sensitive Financial Endpoints
Tests that malicious origins are properly blocked while legitimate origins work
"""

import requests
import sys
import time
from typing import List, Dict

class SensitiveEndpointTester:
    def __init__(self, host: str = "localhost", port: int = 5001):
        self.base_url = f"http://{host}:{port}"
        self.malicious_origins = [
            "https://yourdomain.com",
            "https://malicious-site.com", 
            "https://evil.com",
            "https://attacker.com",
            "null"
        ]
        self.legitimate_origins = [
            "http://localhost:3000",
            "https://mingus.app"
        ]
        
    def test_endpoint_cors(self, endpoint: str) -> Dict:
        """Test CORS security for a specific endpoint"""
        print(f"\n🔍 Testing endpoint: {endpoint}")
        print("=" * 60)
        
        results = {
            "endpoint": endpoint,
            "malicious_origins_blocked": 0,
            "legitimate_origins_allowed": 0,
            "total_tests": 0,
            "security_score": 0.0
        }
        
        # Test malicious origins (should be BLOCKED)
        print("🚨 Testing malicious origins (should be BLOCKED):")
        for origin in self.malicious_origins:
            try:
                response = requests.options(
                    f"{self.base_url}{endpoint}",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type, Authorization"
                    },
                    timeout=10,
                    allow_redirects=True  # Allow redirects to handle HTTPS redirects
                )
                
                # Check if CORS headers are present
                cors_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods", 
                    "Access-Control-Allow-Headers"
                ]
                
                has_cors_headers = any(header in response.headers for header in cors_headers)
                
                if not has_cors_headers:
                    print(f"   ✅ {origin} → BLOCKED (No CORS headers)")
                    results["malicious_origins_blocked"] += 1
                else:
                    print(f"   ❌ {origin} → ALLOWED (CORS headers present) - SECURITY ISSUE!")
                    
                results["total_tests"] += 1
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  {origin} → Request failed: {e}")
                results["total_tests"] += 1
        
        # Test legitimate origins (should be ALLOWED)
        print(f"\n✅ Testing legitimate origins (should be ALLOWED):")
        for origin in self.legitimate_origins:
            try:
                response = requests.options(
                    f"{self.base_url}{endpoint}",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type, Authorization"
                    },
                    timeout=10,
                    allow_redirects=True  # Allow redirects to handle HTTPS redirects
                )
                
                # Check if CORS headers are present
                cors_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods", 
                    "Access-Control-Allow-Headers"
                ]
                
                has_cors_headers = any(header in response.headers for header in cors_headers)
                
                if has_cors_headers:
                    print(f"   ✅ {origin} → ALLOWED (CORS headers present)")
                    results["legitimate_origins_allowed"] += 1
                else:
                    print(f"   ❌ {origin} → BLOCKED (No CORS headers) - FUNCTIONALITY ISSUE!")
                    
                results["total_tests"] += 1
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  {origin} → Request failed: {e}")
                results["total_tests"] += 1
        
        # Calculate security score
        total_malicious = len(self.malicious_origins)
        total_legitimate = len(self.legitimate_origins)
        
        if total_malicious > 0 and total_legitimate > 0:
            malicious_score = results["malicious_origins_blocked"] / total_malicious
            legitimate_score = results["legitimate_origins_allowed"] / total_legitimate
            results["security_score"] = (malicious_score + legitimate_score) / 2
        
        return results
    
    def test_sensitive_endpoints(self, endpoints: List[str]) -> Dict:
        """Test multiple sensitive endpoints"""
        print(f"🚀 Testing CORS Security on Sensitive Financial Endpoints")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"📊 Testing {len(endpoints)} endpoints")
        print("=" * 80)
        
        all_results = []
        overall_score = 0.0
        
        for endpoint in endpoints:
            try:
                result = self.test_endpoint_cors(endpoint)
                all_results.append(result)
                overall_score += result["security_score"]
                
                # Print endpoint summary
                print(f"\n📋 Endpoint Summary: {endpoint}")
                print(f"   Malicious origins blocked: {result['malicious_origins_blocked']}/{len(self.malicious_origins)}")
                print(f"   Legitimate origins allowed: {result['legitimate_origins_allowed']}/{len(self.legitimate_origins)}")
                print(f"   Security score: {result['security_score']:.2%}")
                
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
                all_results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "security_score": 0.0
                })
        
        # Calculate overall security score
        if all_results:
            overall_score = overall_score / len(all_results)
        
        return {
            "overall_score": overall_score,
            "endpoint_results": all_results,
            "total_endpoints": len(endpoints)
        }
    
    def generate_security_report(self, results: Dict):
        """Generate comprehensive security report"""
        print(f"\n📊 CORS SECURITY REPORT")
        print("=" * 80)
        print(f"Overall Security Score: {results['overall_score']:.2%}")
        print(f"Endpoints Tested: {results['total_endpoints']}")
        
        # Categorize endpoints by security level
        secure_endpoints = []
        vulnerable_endpoints = []
        error_endpoints = []
        
        for result in results["endpoint_results"]:
            if "error" in result:
                error_endpoints.append(result["endpoint"])
            elif result["security_score"] >= 0.8:
                secure_endpoints.append(result["endpoint"])
            else:
                vulnerable_endpoints.append(result["endpoint"])
        
        print(f"\n🔒 SECURE Endpoints ({len(secure_endpoints)}):")
        for endpoint in secure_endpoints:
            print(f"   ✅ {endpoint}")
        
        if vulnerable_endpoints:
            print(f"\n🚨 VULNERABLE Endpoints ({len(vulnerable_endpoints)}):")
            for endpoint in vulnerable_endpoints:
                print(f"   ❌ {endpoint}")
        
        if error_endpoints:
            print(f"\n⚠️  ERROR Endpoints ({len(error_endpoints)}):")
            for endpoint in error_endpoints:
                print(f"   ⚠️  {endpoint}")
        
        # Security recommendations
        print(f"\n🔧 SECURITY RECOMMENDATIONS:")
        if results['overall_score'] >= 0.9:
            print("   ✅ Excellent security posture - CORS properly configured")
        elif results['overall_score'] >= 0.7:
            print("   ⚠️  Good security, but some improvements needed")
        else:
            print("   ❌ Critical security issues - immediate action required")
        
        print("   1. Ensure malicious origins receive NO CORS headers")
        print("   2. Verify legitimate origins receive proper CORS headers")
        print("   3. Test with various bypass techniques")
        print("   4. Regular security testing and monitoring")

def main():
    """Main test function"""
    # Define sensitive financial endpoints to test
    sensitive_endpoints = [
        '/api/financial/forecast',
        '/api/financial/balance', 
        '/api/payments/history',
        '/api/user/profile',
        '/api/test',  # This one exists for testing
        '/api/secure'  # This one exists for testing
    ]
    
    # Initialize tester
    tester = SensitiveEndpointTester(host="localhost", port=5001)
    
    # Test all endpoints
    results = tester.test_sensitive_endpoints(sensitive_endpoints)
    
    # Generate report
    tester.generate_security_report(results)
    
    # Exit with appropriate code
    if results['overall_score'] >= 0.8:
        print(f"\n✅ CORS Security Test PASSED (Score: {results['overall_score']:.2%})")
        sys.exit(0)
    else:
        print(f"\n❌ CORS Security Test FAILED (Score: {results['overall_score']:.2%})")
        sys.exit(1)

if __name__ == "__main__":
    main()
