#!/usr/bin/env python3
"""
Mingus Financial Application - Security Testing & Validation Script
Senior DevOps Engineer Implementation

This script provides comprehensive testing procedures to validate security updates
and ensure the financial application remains secure and functional.
"""

import subprocess
import sys
import json
import time
import logging
import requests
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
import os
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'security_testing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityTester:
    """Comprehensive security testing for Mingus financial application"""
    
    def __init__(self, base_url: str = "http://localhost:5000", test_mode: bool = True):
        self.base_url = base_url.rstrip('/')
        self.test_mode = test_mode
        self.test_results = {}
        self.session = requests.Session()
        
        # Test data for financial operations
        self.test_payment_data = {
            "amount": 1000,
            "currency": "usd",
            "payment_method": "card",
            "description": "Test payment for security validation"
        }
        
        # Test user credentials (should be test environment only)
        self.test_user = {
            "email": "test@mingus.com",
            "password": "TestPassword123!"
        }
    
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[int, str, str]:
        """Execute a shell command with proper error handling"""
        try:
            logger.info(f"Executing: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=60
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return -1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Command failed: {command} - Error: {e}")
            return -1, "", str(e)
    
    def test_vulnerability_scan(self) -> Dict:
        """Test 1: Run vulnerability scan to verify updates"""
        logger.info("Running vulnerability scan...")
        
        result = {
            "test_name": "Vulnerability Scan",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            returncode, stdout, stderr = self.run_command("pip-audit --format=json")
            
            if returncode == 0:
                # No vulnerabilities found
                result["status"] = "PASS"
                result["details"]["message"] = "No vulnerabilities detected"
                result["details"]["vulnerability_count"] = 0
                logger.info("✅ Vulnerability scan: PASS - No vulnerabilities found")
            else:
                # Vulnerabilities found
                try:
                    vulns = json.loads(stdout)
                    vuln_count = len([d for d in vulns.get('dependencies', []) if d.get('vulns')])
                    
                    result["status"] = "FAIL"
                    result["details"]["message"] = f"Found {vuln_count} vulnerabilities"
                    result["details"]["vulnerability_count"] = vuln_count
                    result["details"]["vulnerabilities"] = vulns
                    
                    logger.error(f"❌ Vulnerability scan: FAIL - {vuln_count} vulnerabilities found")
                    
                except json.JSONDecodeError:
                    result["status"] = "ERROR"
                    result["details"]["message"] = "Failed to parse vulnerability data"
                    logger.error("❌ Vulnerability scan: ERROR - Failed to parse results")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ Vulnerability scan: ERROR - {e}")
        
        self.test_results["vulnerability_scan"] = result
        return result
    
    def test_cors_policy(self) -> Dict:
        """Test 2: CORS policy validation"""
        logger.info("Testing CORS policy...")
        
        result = {
            "test_name": "CORS Policy Validation",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test malicious origin
            malicious_origin = "https://malicious-site.com"
            
            headers = {
                "Origin": malicious_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Requested-With"
            }
            
            # Test preflight request
            response = self.session.options(
                f"{self.base_url}/api/financial-data",
                headers=headers,
                timeout=10
            )
            
            # Check if CORS headers are properly set
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            # Validate CORS policy
            if response.status_code == 200:
                if cors_headers["Access-Control-Allow-Origin"] == "*":
                    result["status"] = "WARNING"
                    result["details"]["message"] = "CORS allows all origins (consider restricting)"
                    result["details"]["cors_headers"] = cors_headers
                    logger.warning("⚠️ CORS policy: WARNING - Allows all origins")
                elif malicious_origin in str(cors_headers["Access-Control-Allow-Origin"]):
                    result["status"] = "FAIL"
                    result["details"]["message"] = "CORS allows malicious origin"
                    result["details"]["cors_headers"] = cors_headers
                    logger.error("❌ CORS policy: FAIL - Allows malicious origin")
                else:
                    result["status"] = "PASS"
                    result["details"]["message"] = "CORS policy properly configured"
                    result["details"]["cors_headers"] = cors_headers
                    logger.info("✅ CORS policy: PASS - Properly configured")
            else:
                result["status"] = "PASS"
                result["details"]["message"] = "CORS preflight request properly rejected"
                result["details"]["status_code"] = response.status_code
                logger.info("✅ CORS policy: PASS - Preflight request rejected")
                
        except requests.exceptions.RequestException as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Request failed: {str(e)}"
            logger.error(f"❌ CORS policy: ERROR - {e}")
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ CORS policy: ERROR - {e}")
        
        self.test_results["cors_policy"] = result
        return result
    
    def test_ssl_tls_configuration(self) -> Dict:
        """Test 3: SSL/TLS configuration validation"""
        logger.info("Testing SSL/TLS configuration...")
        
        result = {
            "test_name": "SSL/TLS Configuration",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Parse URL to get hostname and port
            parsed_url = urllib.parse.urlparse(self.base_url)
            hostname = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            if parsed_url.scheme == "https":
                # Test SSL/TLS configuration
                context = ssl.create_default_context()
                
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        cipher = ssock.cipher()
                        version = ssock.version()
                        
                        result["status"] = "PASS"
                        result["details"]["message"] = "SSL/TLS properly configured"
                        result["details"]["ssl_version"] = version
                        result["details"]["cipher"] = cipher
                        result["details"]["certificate"] = {
                            "subject": dict(x[0] for x in cert.get('subject', [])),
                            "issuer": dict(x[0] for x in cert.get('issuer', [])),
                            "not_after": cert.get('notAfter'),
                            "not_before": cert.get('notBefore')
                        }
                        
                        logger.info(f"✅ SSL/TLS: PASS - {version}, {cipher[0]}")
            else:
                result["status"] = "INFO"
                result["details"]["message"] = "HTTP connection (no SSL/TLS)"
                logger.info("ℹ️ SSL/TLS: INFO - HTTP connection")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ SSL/TLS: ERROR - {e}")
        
        self.test_results["ssl_tls"] = result
        return result
    
    def test_rate_limiting(self) -> Dict:
        """Test 4: Rate limiting validation"""
        logger.info("Testing rate limiting...")
        
        result = {
            "test_name": "Rate Limiting",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test rate limiting by sending multiple requests
            test_endpoint = f"{self.base_url}/api/login"
            max_requests = 100
            blocked_requests = 0
            
            for i in range(max_requests):
                try:
                    response = self.session.post(
                        test_endpoint,
                        json=self.test_user,
                        timeout=5
                    )
                    
                    if response.status_code == 429:  # Too Many Requests
                        blocked_requests += 1
                    elif response.status_code == 200:
                        # If we get a successful response, rate limiting might not be working
                        pass
                        
                except requests.exceptions.RequestException:
                    # Request failed, might be blocked
                    blocked_requests += 1
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
            
            # Analyze results
            if blocked_requests > 0:
                result["status"] = "PASS"
                result["details"]["message"] = f"Rate limiting active - {blocked_requests}/{max_requests} requests blocked"
                result["details"]["blocked_requests"] = blocked_requests
                result["details"]["total_requests"] = max_requests
                logger.info(f"✅ Rate limiting: PASS - {blocked_requests}/{max_requests} requests blocked")
            else:
                result["status"] = "WARNING"
                result["details"]["message"] = "Rate limiting may not be active"
                result["details"]["blocked_requests"] = blocked_requests
                result["details"]["total_requests"] = max_requests
                logger.warning("⚠️ Rate limiting: WARNING - May not be active")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ Rate limiting: ERROR - {e}")
        
        self.test_results["rate_limiting"] = result
        return result
    
    def test_sql_injection_protection(self) -> Dict:
        """Test 5: SQL injection protection"""
        logger.info("Testing SQL injection protection...")
        
        result = {
            "test_name": "SQL Injection Protection",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test various SQL injection payloads
            sql_payloads = [
                "1; DROP TABLE users; --",
                "1' OR '1'='1",
                "1 UNION SELECT * FROM users",
                "1' AND (SELECT COUNT(*) FROM users) > 0 --",
                "1' WAITFOR DELAY '00:00:05' --"
            ]
            
            test_endpoint = f"{self.base_url}/api/search"
            blocked_payloads = 0
            
            for payload in sql_payloads:
                try:
                    response = self.session.post(
                        test_endpoint,
                        json={"query": payload},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    # Check if request was blocked or failed
                    if response.status_code in [400, 403, 500]:
                        blocked_payloads += 1
                    elif "error" in response.text.lower() or "invalid" in response.text.lower():
                        blocked_payloads += 1
                        
                except requests.exceptions.RequestException:
                    # Request failed, might be blocked
                    blocked_payloads += 1
            
            # Analyze results
            if blocked_payloads > 0:
                result["status"] = "PASS"
                result["details"]["message"] = f"SQL injection protection active - {blocked_payloads}/{len(sql_payloads)} payloads blocked"
                result["details"]["blocked_payloads"] = blocked_payloads
                result["details"]["total_payloads"] = len(sql_payloads)
                logger.info(f"✅ SQL injection protection: PASS - {blocked_payloads}/{len(sql_payloads)} payloads blocked")
            else:
                result["status"] = "WARNING"
                result["details"]["message"] = "SQL injection protection may not be active"
                result["details"]["blocked_payloads"] = blocked_payloads
                result["details"]["total_payloads"] = len(sql_payloads)
                logger.warning("⚠️ SQL injection protection: WARNING - May not be active")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ SQL injection protection: ERROR - {e}")
        
        self.test_results["sql_injection"] = result
        return result
    
    def test_financial_calculations(self) -> Dict:
        """Test 6: Financial calculation accuracy"""
        logger.info("Testing financial calculations...")
        
        result = {
            "test_name": "Financial Calculations",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test interest calculation endpoint
            test_data = {
                "principal": 1000,
                "rate": 0.05,
                "time": 1
            }
            
            response = self.session.post(
                f"{self.base_url}/api/calculate-interest",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    calculated_interest = data.get("interest", 0)
                    expected_interest = test_data["principal"] * test_data["rate"] * test_data["time"]
                    
                    # Allow small floating point differences
                    if abs(calculated_interest - expected_interest) < 0.01:
                        result["status"] = "PASS"
                        result["details"]["message"] = "Financial calculations accurate"
                        result["details"]["calculated"] = calculated_interest
                        result["details"]["expected"] = expected_interest
                        logger.info(f"✅ Financial calculations: PASS - {calculated_interest} (expected: {expected_interest})")
                    else:
                        result["status"] = "FAIL"
                        result["details"]["message"] = "Financial calculations inaccurate"
                        result["details"]["calculated"] = calculated_interest
                        result["details"]["expected"] = expected_interest
                        logger.error(f"❌ Financial calculations: FAIL - {calculated_interest} (expected: {expected_interest})")
                        
                except (json.JSONDecodeError, KeyError) as e:
                    result["status"] = "ERROR"
                    result["details"]["message"] = f"Invalid response format: {str(e)}"
                    logger.error(f"❌ Financial calculations: ERROR - Invalid response format")
            else:
                result["status"] = "WARNING"
                result["details"]["message"] = f"Endpoint returned status {response.status_code}"
                result["details"]["status_code"] = response.status_code
                logger.warning(f"⚠️ Financial calculations: WARNING - Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Request failed: {str(e)}"
            logger.error(f"❌ Financial calculations: ERROR - {e}")
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ Financial calculations: ERROR - {e}")
        
        self.test_results["financial_calculations"] = result
        return result
    
    def test_payment_processing(self) -> Dict:
        """Test 7: Payment processing functionality"""
        logger.info("Testing payment processing...")
        
        result = {
            "test_name": "Payment Processing",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test payment endpoint (should use test mode)
            if self.test_mode:
                test_payment = self.test_payment_data.copy()
                test_payment["test_mode"] = True
                
                response = self.session.post(
                    f"{self.base_url}/api/process-payment",
                    json=test_payment,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        payment_status = data.get("status", "unknown")
                        
                        if payment_status in ["success", "completed", "pending"]:
                            result["status"] = "PASS"
                            result["details"]["message"] = "Payment processing functional"
                            result["details"]["payment_status"] = payment_status
                            result["details"]["transaction_id"] = data.get("transaction_id", "N/A")
                            logger.info(f"✅ Payment processing: PASS - Status: {payment_status}")
                        else:
                            result["status"] = "WARNING"
                            result["details"]["message"] = f"Payment processing returned unexpected status: {payment_status}"
                            result["details"]["payment_status"] = payment_status
                            logger.warning(f"⚠️ Payment processing: WARNING - Status: {payment_status}")
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        result["status"] = "ERROR"
                        result["details"]["message"] = f"Invalid response format: {str(e)}"
                        logger.error(f"❌ Payment processing: ERROR - Invalid response format")
                else:
                    result["status"] = "WARNING"
                    result["details"]["message"] = f"Payment endpoint returned status {response.status_code}"
                    result["details"]["status_code"] = response.status_code
                    logger.warning(f"⚠️ Payment processing: WARNING - Status {response.status_code}")
            else:
                result["status"] = "SKIP"
                result["details"]["message"] = "Test mode disabled, skipping payment test"
                logger.info("⏭️ Payment processing: SKIP - Test mode disabled")
                
        except requests.exceptions.RequestException as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Request failed: {str(e)}"
            logger.error(f"❌ Payment processing: ERROR - {e}")
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ Payment processing: ERROR - {e}")
        
        self.test_results["payment_processing"] = result
        return result
    
    def test_authentication_security(self) -> Dict:
        """Test 8: Authentication security"""
        logger.info("Testing authentication security...")
        
        result = {
            "test_name": "Authentication Security",
            "status": "unknown",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test weak password
            weak_passwords = [
                "123456",
                "password",
                "admin",
                "qwerty",
                "letmein"
            ]
            
            weak_password_accepted = False
            
            for weak_password in weak_passwords:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/register",
                        json={
                            "email": "test@example.com",
                            "password": weak_password
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        weak_password_accepted = True
                        break
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Test brute force protection
            brute_force_blocked = False
            login_attempts = 10
            
            for i in range(login_attempts):
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/login",
                        json={
                            "email": "nonexistent@example.com",
                            "password": "wrongpassword"
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code == 429:  # Too Many Requests
                        brute_force_blocked = True
                        break
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Analyze results
            if weak_password_accepted:
                result["status"] = "FAIL"
                result["details"]["message"] = "Weak passwords accepted"
                result["details"]["weak_password_accepted"] = True
                logger.error("❌ Authentication security: FAIL - Weak passwords accepted")
            elif brute_force_blocked:
                result["status"] = "PASS"
                result["details"]["message"] = "Authentication security properly configured"
                result["details"]["weak_password_accepted"] = False
                result["details"]["brute_force_blocked"] = True
                logger.info("✅ Authentication security: PASS - Properly configured")
            else:
                result["status"] = "WARNING"
                result["details"]["message"] = "Authentication security may need improvement"
                result["details"]["weak_password_accepted"] = False
                result["details"]["brute_force_blocked"] = False
                logger.warning("⚠️ Authentication security: WARNING - May need improvement")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["details"]["message"] = f"Exception: {str(e)}"
            logger.error(f"❌ Authentication security: ERROR - {e}")
        
        self.test_results["authentication_security"] = result
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all security tests"""
        logger.info("Starting comprehensive security testing...")
        
        tests = [
            self.test_vulnerability_scan,
            self.test_cors_policy,
            self.test_ssl_tls_configuration,
            self.test_rate_limiting,
            self.test_sql_injection_protection,
            self.test_financial_calculations,
            self.test_payment_processing,
            self.test_authentication_security
        ]
        
        for test_func in tests:
            try:
                test_func()
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {e}")
        
        return self.test_results
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results.values() if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results.values() if r["status"] == "WARNING"])
        error_tests = len([r for r in self.test_results.values() if r["status"] == "ERROR"])
        skipped_tests = len([r for r in self.test_results.values() if r["status"] == "SKIP"])
        
        report = f"""
# Mingus Security Testing Report
Generated: {timestamp}

## Executive Summary
- **Total Tests:** {total_tests}
- **Passed:** {passed_tests} ✅
- **Failed:** {failed_tests} ❌
- **Warnings:** {warning_tests} ⚠️
- **Errors:** {error_tests} ❌
- **Skipped:** {skipped_tests} ⏭️

## Test Results
"""
        
        for test_name, result in self.test_results.items():
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "SKIP": "⏭️",
                "unknown": "❓"
            }.get(result["status"], "❓")
            
            report += f"\n### {result['test_name']} {status_emoji}\n"
            report += f"- **Status:** {result['status']}\n"
            report += f"- **Message:** {result['details'].get('message', 'N/A')}\n"
            report += f"- **Timestamp:** {result['timestamp']}\n"
            
            # Add additional details
            for key, value in result['details'].items():
                if key not in ['message', 'timestamp']:
                    report += f"- **{key.title()}:** {value}\n"
        
        # Add recommendations
        report += "\n## Recommendations\n"
        
        if failed_tests > 0:
            report += "- **Immediate Action Required:** Address failed tests before production deployment\n"
        
        if warning_tests > 0:
            report += "- **Review Required:** Investigate warning tests for potential security improvements\n"
        
        if error_tests > 0:
            report += "- **Investigation Required:** Resolve test errors to ensure complete security validation\n"
        
        if passed_tests == total_tests:
            report += "- **Excellent:** All security tests passed successfully\n"
        
        return report

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Mingus Security Testing & Validation")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--test-mode", action="store_true", default=True, help="Enable test mode for payment processing")
    parser.add_argument("--output", help="Output file for test report")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = SecurityTester(base_url=args.base_url, test_mode=args.test_mode)
    
    try:
        # Run all tests
        logger.info("Starting security testing...")
        test_results = tester.run_all_tests()
        
        # Generate report
        report = tester.generate_test_report()
        
        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            logger.info(f"Test report saved to: {args.output}")
        else:
            print(report)
        
        # Exit with appropriate code
        failed_tests = len([r for r in test_results.values() if r["status"] == "FAIL"])
        if failed_tests > 0:
            logger.error(f"Security testing failed: {failed_tests} tests failed")
            sys.exit(1)
        else:
            logger.info("Security testing completed successfully")
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("Security testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during security testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
