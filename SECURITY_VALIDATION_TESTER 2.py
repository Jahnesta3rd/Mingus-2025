#!/usr/bin/env python3
"""
MINGUS Application - Security Validation Tester
Comprehensive security testing for production readiness
"""

import asyncio
import aiohttp
import time
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class SecurityTestResult:
    """Security test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class SecurityValidator:
    """Comprehensive security validation for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[SecurityTestResult] = []
        self.auth_token = None
        
    async def run_security_validation(self) -> Dict[str, Any]:
        """Run comprehensive security validation"""
        print("🔒 MINGUS Application - Security Validation")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Authentication Security
        await self.test_authentication_security()
        
        # 2. CSRF Protection
        await self.test_csrf_protection()
        
        # 3. Rate Limiting
        await self.test_rate_limiting()
        
        # 4. Input Validation
        await self.test_input_validation()
        
        # 5. Security Headers
        await self.test_security_headers()
        
        # 6. Session Security
        await self.test_session_security()
        
        # 7. Data Protection
        await self.test_data_protection()
        
        # 8. API Security
        await self.test_api_security()
        
        return self.generate_security_report()
    
    async def test_authentication_security(self):
        """Test authentication security measures"""
        print("\n🔐 Testing Authentication Security...")
        
        try:
            # Test password strength requirements
            weak_passwords = ["123", "password", "123456", "qwerty"]
            for password in weak_passwords:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.base_url}/api/auth/register", json={
                        "email": f"test{time.time()}@example.com",
                        "password": password,
                        "first_name": "Test",
                        "last_name": "User"
                    }) as response:
                        if response.status == 400:
                            self.results.append(SecurityTestResult(
                                test_name="Password Strength Validation",
                                status="passed",
                                details={"password": password, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Password strength validation is working correctly"]
                            ))
                            print(f"  ✅ Password '{password}' correctly rejected")
                        else:
                            self.results.append(SecurityTestResult(
                                test_name="Password Strength Validation",
                                status="failed",
                                details={"password": password, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Implement stronger password requirements"]
                            ))
                            print(f"  ❌ Password '{password}' was accepted (should be rejected)")
            
            # Test account lockout
            async with aiohttp.ClientSession() as session:
                for i in range(6):  # Try 6 failed logins
                    async with session.post(f"{self.base_url}/api/auth/login", json={
                        "email": "nonexistent@example.com",
                        "password": "wrongpassword"
                    }) as response:
                        if i >= 5 and response.status == 429:  # Rate limited after 5 attempts
                            self.results.append(SecurityTestResult(
                                test_name="Account Lockout Protection",
                                status="passed",
                                details={"attempts": i+1, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Account lockout is working correctly"]
                            ))
                            print(f"  ✅ Account lockout triggered after {i+1} attempts")
                            break
                else:
                    self.results.append(SecurityTestResult(
                        test_name="Account Lockout Protection",
                        status="warning",
                        details={"attempts": 6, "status_code": "no_lockout"},
                        timestamp=datetime.now(),
                        recommendations=["Implement account lockout after failed login attempts"]
                    ))
                    print(f"  ⚠️ Account lockout not triggered after 6 attempts")
                    
        except Exception as e:
            print(f"  ❌ Authentication Security Test: ERROR - {str(e)}")
    
    async def test_csrf_protection(self):
        """Test CSRF protection mechanisms"""
        print("\n🛡️ Testing CSRF Protection...")
        
        try:
            # Test CSRF token requirement
            async with aiohttp.ClientSession() as session:
                # Try to make a POST request without CSRF token
                async with session.post(f"{self.base_url}/api/financial/budget", json={
                    "name": "test_budget",
                    "amount": 1000.00
                }) as response:
                    if response.status in [400, 403]:
                        self.results.append(SecurityTestResult(
                            test_name="CSRF Token Requirement",
                            status="passed",
                            details={"endpoint": "/api/financial/budget", "status_code": response.status},
                            timestamp=datetime.now(),
                            recommendations=["CSRF protection is working correctly"]
                        ))
                        print(f"  ✅ CSRF protection active - request rejected")
                    else:
                        self.results.append(SecurityTestResult(
                            test_name="CSRF Token Requirement",
                            status="failed",
                            details={"endpoint": "/api/financial/budget", "status_code": response.status},
                            timestamp=datetime.now(),
                            recommendations=["Implement CSRF protection for all state-changing operations"]
                        ))
                        print(f"  ❌ CSRF protection not active - request accepted")
                
                # Test CSRF token endpoint
                async with session.get(f"{self.base_url}/api/csrf/token") as response:
                    if response.status == 200:
                        token_data = await response.json()
                        if "csrf_token" in token_data:
                            self.results.append(SecurityTestResult(
                                test_name="CSRF Token Generation",
                                status="passed",
                                details={"endpoint": "/api/csrf/token", "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["CSRF token generation is working correctly"]
                            ))
                            print(f"  ✅ CSRF token generation working")
                        else:
                            self.results.append(SecurityTestResult(
                                test_name="CSRF Token Generation",
                                status="failed",
                                details={"endpoint": "/api/csrf/token", "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Fix CSRF token generation endpoint"]
                            ))
                            print(f"  ❌ CSRF token not in response")
                    else:
                        self.results.append(SecurityTestResult(
                            test_name="CSRF Token Generation",
                            status="failed",
                            details={"endpoint": "/api/csrf/token", "status_code": response.status},
                            timestamp=datetime.now(),
                            recommendations=["Implement CSRF token generation endpoint"]
                        ))
                        print(f"  ❌ CSRF token endpoint not working")
                        
        except Exception as e:
            print(f"  ❌ CSRF Protection Test: ERROR - {str(e)}")
    
    async def test_rate_limiting(self):
        """Test rate limiting mechanisms"""
        print("\n⏱️ Testing Rate Limiting...")
        
        try:
            # Test authentication endpoint rate limiting
            async with aiohttp.ClientSession() as session:
                rate_limit_requests = []
                for i in range(10):
                    async with session.post(f"{self.base_url}/api/auth/login", json={
                        "email": "test@example.com",
                        "password": "wrongpassword"
                    }) as response:
                        rate_limit_requests.append(response.status)
                        if response.status == 429:
                            break
                
                rate_limited = any(status == 429 for status in rate_limit_requests)
                if rate_limited:
                    self.results.append(SecurityTestResult(
                        test_name="Authentication Rate Limiting",
                        status="passed",
                        details={"requests_made": len(rate_limit_requests), "rate_limited": True},
                        timestamp=datetime.now(),
                        recommendations=["Rate limiting is working correctly"]
                    ))
                    print(f"  ✅ Rate limiting active after {len(rate_limit_requests)} requests")
                else:
                    self.results.append(SecurityTestResult(
                        test_name="Authentication Rate Limiting",
                        status="warning",
                        details={"requests_made": len(rate_limit_requests), "rate_limited": False},
                        timestamp=datetime.now(),
                        recommendations=["Implement rate limiting for authentication endpoints"]
                    ))
                    print(f"  ⚠️ Rate limiting not detected after {len(rate_limit_requests)} requests")
                    
        except Exception as e:
            print(f"  ❌ Rate Limiting Test: ERROR - {str(e)}")
    
    async def test_input_validation(self):
        """Test input validation and sanitization"""
        print("\n🔍 Testing Input Validation...")
        
        try:
            # Test SQL injection attempts
            sql_injection_payloads = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "1; INSERT INTO users VALUES ('hacker', 'password'); --"
            ]
            
            async with aiohttp.ClientSession() as session:
                for payload in sql_injection_payloads:
                    async with session.post(f"{self.base_url}/api/auth/login", json={
                        "email": payload,
                        "password": "test"
                    }) as response:
                        if response.status in [400, 422]:
                            self.results.append(SecurityTestResult(
                                test_name="SQL Injection Protection",
                                status="passed",
                                details={"payload": payload, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["SQL injection protection is working correctly"]
                            ))
                            print(f"  ✅ SQL injection payload rejected: {payload[:20]}...")
                        else:
                            self.results.append(SecurityTestResult(
                                test_name="SQL Injection Protection",
                                status="failed",
                                details={"payload": payload, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Implement proper input validation and parameterized queries"]
                            ))
                            print(f"  ❌ SQL injection payload accepted: {payload[:20]}...")
            
            # Test XSS attempts
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "';alert('xss');//"
            ]
            
            for payload in xss_payloads:
                async with session.post(f"{self.base_url}/api/auth/register", json={
                    "email": f"test{time.time()}@example.com",
                    "password": "TestPassword123!",
                    "first_name": payload,
                    "last_name": "User"
                }) as response:
                    if response.status in [400, 422]:
                        self.results.append(SecurityTestResult(
                            test_name="XSS Protection",
                            status="passed",
                            details={"payload": payload, "status_code": response.status},
                            timestamp=datetime.now(),
                            recommendations=["XSS protection is working correctly"]
                        ))
                        print(f"  ✅ XSS payload rejected: {payload[:20]}...")
                    else:
                        self.results.append(SecurityTestResult(
                            test_name="XSS Protection",
                            status="failed",
                            details={"payload": payload, "status_code": response.status},
                            timestamp=datetime.now(),
                            recommendations=["Implement proper input sanitization and output encoding"]
                        ))
                        print(f"  ❌ XSS payload accepted: {payload[:20]}...")
                        
        except Exception as e:
            print(f"  ❌ Input Validation Test: ERROR - {str(e)}")
    
    async def test_security_headers(self):
        """Test security headers configuration"""
        print("\n🛡️ Testing Security Headers...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    headers = dict(response.headers)
                    
                    # Check for required security headers
                    required_headers = {
                        "X-Frame-Options": "DENY",
                        "X-Content-Type-Options": "nosniff",
                        "X-XSS-Protection": "1; mode=block",
                        "Strict-Transport-Security": "max-age=31536000",
                        "Content-Security-Policy": "default-src 'self'"
                    }
                    
                    headers_present = 0
                    for header, expected_value in required_headers.items():
                        if header in headers:
                            headers_present += 1
                            print(f"  ✅ {header}: {headers[header]}")
                        else:
                            print(f"  ❌ {header}: Missing")
                    
                    if headers_present >= 4:
                        self.results.append(SecurityTestResult(
                            test_name="Security Headers",
                            status="passed",
                            details={"headers_present": headers_present, "total_headers": len(required_headers)},
                            timestamp=datetime.now(),
                            recommendations=["Security headers are properly configured"]
                        ))
                    else:
                        self.results.append(SecurityTestResult(
                            test_name="Security Headers",
                            status="failed",
                            details={"headers_present": headers_present, "total_headers": len(required_headers)},
                            timestamp=datetime.now(),
                            recommendations=["Implement missing security headers"]
                        ))
                        
        except Exception as e:
            print(f"  ❌ Security Headers Test: ERROR - {str(e)}")
    
    async def test_session_security(self):
        """Test session security configuration"""
        print("\n🍪 Testing Session Security...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    headers = dict(response.headers)
                    
                    # Check for secure session cookies
                    set_cookie = headers.get("Set-Cookie", "")
                    session_secure = "Secure" in set_cookie
                    session_httponly = "HttpOnly" in set_cookie
                    session_samesite = "SameSite" in set_cookie
                    
                    if session_secure and session_httponly and session_samesite:
                        self.results.append(SecurityTestResult(
                            test_name="Session Security",
                            status="passed",
                            details={"secure": session_secure, "httponly": session_httponly, "samesite": session_samesite},
                            timestamp=datetime.now(),
                            recommendations=["Session security is properly configured"]
                        ))
                        print(f"  ✅ Session cookies are secure")
                    else:
                        self.results.append(SecurityTestResult(
                            test_name="Session Security",
                            status="failed",
                            details={"secure": session_secure, "httponly": session_httponly, "samesite": session_samesite},
                            timestamp=datetime.now(),
                            recommendations=["Configure secure session cookies with Secure, HttpOnly, and SameSite flags"]
                        ))
                        print(f"  ❌ Session cookies are not secure")
                        
        except Exception as e:
            print(f"  ❌ Session Security Test: ERROR - {str(e)}")
    
    async def test_data_protection(self):
        """Test data protection measures"""
        print("\n🔐 Testing Data Protection...")
        
        try:
            # Test sensitive data exposure
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as response:
                    if response.status == 200:
                        response_text = await response.text()
                        
                        # Check for sensitive information in response
                        sensitive_patterns = [
                            "password", "secret", "key", "token", "api_key",
                            "database", "connection", "config", "debug"
                        ]
                        
                        exposed_data = []
                        for pattern in sensitive_patterns:
                            if pattern.lower() in response_text.lower():
                                exposed_data.append(pattern)
                        
                        if not exposed_data:
                            self.results.append(SecurityTestResult(
                                test_name="Sensitive Data Exposure",
                                status="passed",
                                details={"exposed_patterns": exposed_data},
                                timestamp=datetime.now(),
                                recommendations=["No sensitive data exposed in responses"]
                            ))
                            print(f"  ✅ No sensitive data exposed")
                        else:
                            self.results.append(SecurityTestResult(
                                test_name="Sensitive Data Exposure",
                                status="failed",
                                details={"exposed_patterns": exposed_data},
                                timestamp=datetime.now(),
                                recommendations=["Remove sensitive data from API responses"]
                            ))
                            print(f"  ❌ Sensitive data exposed: {exposed_data}")
                            
        except Exception as e:
            print(f"  ❌ Data Protection Test: ERROR - {str(e)}")
    
    async def test_api_security(self):
        """Test API security measures"""
        print("\n🔌 Testing API Security...")
        
        try:
            # Test unauthorized access to protected endpoints
            protected_endpoints = [
                "/api/user/profile",
                "/api/financial/dashboard",
                "/api/financial/budget",
                "/api/financial/goals"
            ]
            
            async with aiohttp.ClientSession() as session:
                for endpoint in protected_endpoints:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 401:
                            self.results.append(SecurityTestResult(
                                test_name="API Authorization",
                                status="passed",
                                details={"endpoint": endpoint, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["API authorization is working correctly"]
                            ))
                            print(f"  ✅ {endpoint}: Properly protected")
                        else:
                            self.results.append(SecurityTestResult(
                                test_name="API Authorization",
                                status="failed",
                                details={"endpoint": endpoint, "status_code": response.status},
                                timestamp=datetime.now(),
                                recommendations=["Implement proper API authorization"]
                            ))
                            print(f"  ❌ {endpoint}: Not properly protected")
                            
        except Exception as e:
            print(f"  ❌ API Security Test: ERROR - {str(e)}")
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine security status
        if failed_tests == 0 and warning_tests <= 2:
            security_status = "SECURE"
        elif failed_tests <= 2:
            security_status = "NEEDS ATTENTION"
        else:
            security_status = "VULNERABLE"
        
        return {
            "summary": {
                "security_status": security_status,
                "security_score": round(security_score, 1),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                    "recommendations": r.recommendations
                }
                for r in self.results
            ],
            "recommendations": self.generate_security_recommendations(),
            "production_readiness": self.assess_security_readiness()
        }
    
    def generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status == "failed"]
        if failed_tests:
            recommendations.append("🚨 CRITICAL: Address failed security tests before production")
            for test in failed_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        warning_tests = [r for r in self.results if r.status == "warning"]
        if warning_tests:
            recommendations.append("⚠️ WARNING: Review security warnings")
            for test in warning_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        if not failed_tests and not warning_tests:
            recommendations.append("✅ All security tests passed - ready for production")
        
        return recommendations
    
    def assess_security_readiness(self) -> Dict[str, Any]:
        """Assess security readiness for production"""
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        # Security readiness criteria
        readiness_criteria = {
            "authentication_secure": any("Authentication" in r.test_name and r.status == "passed" for r in self.results),
            "csrf_protection_active": any("CSRF" in r.test_name and r.status == "passed" for r in self.results),
            "rate_limiting_enabled": any("Rate Limiting" in r.test_name and r.status == "passed" for r in self.results),
            "input_validation_working": any("Input Validation" in r.test_name and r.status == "passed" for r in self.results),
            "security_headers_present": any("Security Headers" in r.test_name and r.status == "passed" for r in self.results),
            "session_security_configured": any("Session Security" in r.test_name and r.status == "passed" for r in self.results),
            "data_protection_active": any("Data Protection" in r.test_name and r.status == "passed" for r in self.results),
            "api_authorization_working": any("API Security" in r.test_name and r.status == "passed" for r in self.results)
        }
        
        readiness_score = sum(readiness_criteria.values()) / len(readiness_criteria) * 100
        
        if readiness_score >= 90 and failed_tests == 0:
            readiness_status = "SECURE"
        elif readiness_score >= 70 and failed_tests <= 2:
            readiness_status = "NEEDS MINOR FIXES"
        else:
            readiness_status = "NOT SECURE"
        
        return {
            "readiness_status": readiness_status,
            "readiness_score": round(readiness_score, 1),
            "criteria": readiness_criteria,
            "blocking_issues": failed_tests,
            "recommendations": [
                "Address all failed security tests",
                "Implement missing security measures",
                "Review and update security configurations",
                "Conduct regular security audits"
            ]
        }

async def main():
    """Main function to run security validation"""
    print("🔒 MINGUS Application - Security Validation")
    print("=" * 60)
    
    # Initialize security validator
    security_validator = SecurityValidator()
    
    # Run security validation
    report = await security_validator.run_security_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🔒 SECURITY VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Security Status: {report['summary']['security_status']}")
    print(f"Security Score: {report['summary']['security_score']}%")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Warnings: {report['summary']['warning_tests']}")
    
    print("\n🚀 SECURITY READINESS")
    print("=" * 60)
    readiness = report['production_readiness']
    print(f"Readiness Status: {readiness['readiness_status']}")
    print(f"Readiness Score: {readiness['readiness_score']}%")
    print(f"Blocking Issues: {readiness['blocking_issues']}")
    
    print("\n📋 SECURITY RECOMMENDATIONS")
    print("=" * 60)
    for recommendation in report['recommendations']:
        print(recommendation)
    
    # Save detailed report
    report_file = f"security_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on security readiness
    if readiness['readiness_status'] == "SECURE":
        print("\n🎉 MINGUS Application is SECURE for production deployment!")
        return 0
    else:
        print(f"\n⚠️ MINGUS Application needs security improvements before production deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
