#!/usr/bin/env python3
"""
CORS Security Validation Test
Properly validates CORS security by ensuring malicious origins are blocked
and legitimate origins work correctly.
"""

import requests
import sys
import json
from typing import List, Dict, Tuple

class CORSSecurityValidator:
    def __init__(self, host: str = "localhost", port: int = 5001):
        self.base_url = f"http://{host}:{port}"
        self.test_results = []
        
        # Test origins - malicious should be BLOCKED, legitimate should be ALLOWED
        self.malicious_origins = [
            "https://yourdomain.com",
            "https://malicious-site.com",
            "https://evil.com", 
            "https://attacker.com",
            "https://phishing.com",
            "null",
            "//malicious-site.com",
            "https://subdomain.yourdomain.com",
            "https://yourdomain.com.evil.com"
        ]
        
        self.legitimate_origins = [
            "http://localhost:3000",
            "https://mingus.app"
        ]
        
        # Test endpoints
        self.test_endpoints = [
            "/health",
            "/api/test", 
            "/api/secure",
            "/api/financial/balance"
        ]
    
    def test_cors_preflight(self, endpoint: str, origin: str) -> Dict:
        """Test CORS preflight request for a specific origin and endpoint"""
        try:
            response = requests.options(
                f"{self.base_url}{endpoint}",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization"
                },
                timeout=10,
                allow_redirects=True
            )
            
            # Check for CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
                "Access-Control-Max-Age": response.headers.get("Access-Control-Max-Age")
            }
            
            has_cors_headers = any(value is not None for value in cors_headers.values())
            
            return {
                "endpoint": endpoint,
                "origin": origin,
                "status_code": response.status_code,
                "has_cors_headers": has_cors_headers,
                "cors_headers": cors_headers,
                "success": True
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint,
                "origin": origin,
                "status_code": None,
                "has_cors_headers": False,
                "cors_headers": {},
                "success": False,
                "error": str(e)
            }
    
    def validate_security_rule(self, test_result: Dict, is_malicious: bool) -> Dict:
        """Validate if the test result follows security rules"""
        validation = {
            "rule_followed": False,
            "security_issue": "",
            "severity": "LOW"
        }
        
        if is_malicious:
            # Malicious origins should NOT get CORS headers
            if test_result["has_cors_headers"]:
                validation["rule_followed"] = False
                validation["security_issue"] = "MALICIOUS_ORIGIN_ALLOWED"
                validation["severity"] = "CRITICAL"
            else:
                validation["rule_followed"] = True
                validation["security_issue"] = ""
        else:
            # Legitimate origins SHOULD get CORS headers
            if test_result["has_cors_headers"]:
                validation["rule_followed"] = True
                validation["security_issue"] = ""
            else:
                validation["rule_followed"] = False
                validation["security_issue"] = "LEGITIMATE_ORIGIN_BLOCKED"
                validation["severity"] = "MEDIUM"
        
        return validation
    
    def run_security_tests(self) -> Dict:
        """Run comprehensive CORS security tests"""
        print("🚀 CORS Security Validation Test")
        print("=" * 80)
        print(f"🌐 Testing against: {self.base_url}")
        print(f"📊 Endpoints: {len(self.test_endpoints)}")
        print(f"🚨 Malicious origins: {len(self.malicious_origins)}")
        print(f"✅ Legitimate origins: {len(self.legitimate_origins)}")
        print()
        
        all_results = []
        security_score = 0.0
        total_tests = 0
        passed_tests = 0
        
        # Test each endpoint
        for endpoint in self.test_endpoints:
            print(f"🔍 Testing endpoint: {endpoint}")
            print("-" * 60)
            
            endpoint_results = []
            
            # Test malicious origins (should be BLOCKED)
            print("🚨 Testing malicious origins (should be BLOCKED):")
            for origin in self.malicious_origins:
                result = self.test_cors_preflight(endpoint, origin)
                validation = self.validate_security_rule(result, is_malicious=True)
                
                result["validation"] = validation
                result["is_malicious"] = True
                endpoint_results.append(result)
                
                if validation["rule_followed"]:
                    print(f"   ✅ {origin} → BLOCKED (SECURE)")
                    passed_tests += 1
                else:
                    print(f"   ❌ {origin} → ALLOWED (CRITICAL SECURITY ISSUE)")
                
                total_tests += 1
            
            # Test legitimate origins (should be ALLOWED)
            print(f"\n✅ Testing legitimate origins (should be ALLOWED):")
            for origin in self.legitimate_origins:
                result = self.test_cors_preflight(endpoint, origin)
                validation = self.validate_security_rule(result, is_malicious=False)
                
                result["validation"] = validation
                result["is_malicious"] = False
                endpoint_results.append(result)
                
                if validation["rule_followed"]:
                    print(f"   ✅ {origin} → ALLOWED (FUNCTIONAL)")
                    passed_tests += 1
                else:
                    print(f"   ❌ {origin} → BLOCKED (FUNCTIONALITY ISSUE)")
                
                total_tests += 1
            
            all_results.extend(endpoint_results)
            
            # Endpoint summary
            endpoint_malicious_blocked = sum(1 for r in endpoint_results if r["is_malicious"] and r["validation"]["rule_followed"])
            endpoint_legitimate_allowed = sum(1 for r in endpoint_results if not r["is_malicious"] and r["validation"]["rule_followed"])
            
            print(f"\n📋 Endpoint Summary: {endpoint}")
            print(f"   Malicious origins blocked: {endpoint_malicious_blocked}/{len(self.malicious_origins)}")
            print(f"   Legitimate origins allowed: {endpoint_legitimate_allowed}/{len(self.legitimate_origins)}")
            print()
        
        # Calculate overall security score
        if total_tests > 0:
            security_score = passed_tests / total_tests
        
        return {
            "overall_score": security_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "results": all_results,
            "endpoints_tested": len(self.test_endpoints)
        }
    
    def generate_security_report(self, test_results: Dict):
        """Generate comprehensive security report"""
        print("📊 CORS SECURITY VALIDATION REPORT")
        print("=" * 80)
        print(f"Overall Security Score: {test_results['overall_score']:.2%}")
        print(f"Tests Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
        print(f"Endpoints Tested: {test_results['endpoints_tested']}")
        
        # Analyze results by endpoint
        endpoint_analysis = {}
        for result in test_results["results"]:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_analysis:
                endpoint_analysis[endpoint] = {"malicious": [], "legitimate": []}
            
            if result["is_malicious"]:
                endpoint_analysis[endpoint]["malicious"].append(result)
            else:
                endpoint_analysis[endpoint]["legitimate"].append(result)
        
        print(f"\n🔍 ENDPOINT ANALYSIS:")
        for endpoint, analysis in endpoint_analysis.items():
            malicious_blocked = sum(1 for r in analysis["malicious"] if r["validation"]["rule_followed"])
            legitimate_allowed = sum(1 for r in analysis["legitimate"] if r["validation"]["rule_followed"])
            
            print(f"\n   {endpoint}:")
            print(f"     Malicious origins blocked: {malicious_blocked}/{len(analysis['malicious'])}")
            print(f"     Legitimate origins allowed: {legitimate_allowed}/{len(analysis['legitimate'])}")
        
        # Security issues summary
        security_issues = []
        for result in test_results["results"]:
            if not result["validation"]["rule_followed"]:
                issue = {
                    "endpoint": result["endpoint"],
                    "origin": result["origin"],
                    "issue": result["validation"]["security_issue"],
                    "severity": result["validation"]["severity"]
                }
                security_issues.append(issue)
        
        if security_issues:
            print(f"\n🚨 SECURITY ISSUES DETECTED ({len(security_issues)}):")
            for issue in security_issues:
                print(f"   {issue['severity']}: {issue['endpoint']} - {issue['origin']} ({issue['issue']})")
        else:
            print(f"\n✅ NO SECURITY ISSUES DETECTED")
        
        # Recommendations
        print(f"\n🔧 SECURITY RECOMMENDATIONS:")
        if test_results['overall_score'] >= 0.95:
            print("   ✅ EXCELLENT - CORS security properly configured")
        elif test_results['overall_score'] >= 0.8:
            print("   ⚠️  GOOD - Minor security improvements needed")
        elif test_results['overall_score'] >= 0.6:
            print("   ⚠️  FAIR - Significant security improvements needed")
        else:
            print("   ❌ POOR - Critical security issues require immediate attention")
        
        print("   1. Malicious origins must receive NO CORS headers")
        print("   2. Legitimate origins must receive proper CORS headers")
        print("   3. Regular security testing and monitoring required")
        print("   4. Consider implementing additional security headers")
    
    def export_results(self, test_results: Dict, filename: str = "cors_security_results.json"):
        """Export test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(test_results, f, indent=2)
            print(f"\n💾 Results exported to: {filename}")
        except Exception as e:
            print(f"\n❌ Failed to export results: {e}")

def main():
    """Main test execution"""
    # Initialize validator
    validator = CORSSecurityValidator(host="localhost", port=5001)
    
    # Run security tests
    test_results = validator.run_security_tests()
    
    # Generate report
    validator.generate_security_report(test_results)
    
    # Export results
    validator.export_results(test_results)
    
    # Exit with appropriate code
    if test_results['overall_score'] >= 0.9:
        print(f"\n✅ CORS Security Validation PASSED (Score: {test_results['overall_score']:.2%})")
        sys.exit(0)
    else:
        print(f"\n❌ CORS Security Validation FAILED (Score: {test_results['overall_score']:.2%})")
        sys.exit(1)

if __name__ == "__main__":
    main()
