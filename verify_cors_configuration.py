#!/usr/bin/env python3
"""
Comprehensive CORS Configuration Verification

Tests CORS configuration including:
- Preflight (OPTIONS) requests
- CORS headers in responses
- Allowed origins verification
- Allowed methods verification
- Allowed headers verification
- Credentials support
- Exposed headers
- Unauthorized origin blocking

Usage:
    python verify_cors_configuration.py [--base-url http://localhost:5000]
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class CORSTestResult:
    """CORS test result"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    message: str
    details: Dict[str, Any]
    timestamp: str

class CORSVerifier:
    """Comprehensive CORS configuration verifier"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[CORSTestResult] = []
        
        # Expected CORS configuration (from app.py)
        self.expected_origins = [
            'http://localhost:3000',
            'http://localhost:5173',
            'http://127.0.0.1:3000'
        ]
        self.expected_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.expected_headers = [
            'Content-Type',
            'Authorization',
            'X-CSRF-Token',
            'X-Requested-With'
        ]
        self.expected_exposed_headers = ['X-CSRF-Token']
        self.supports_credentials = True
        
        # Test unauthorized origins
        self.unauthorized_origins = [
            'http://evil.com',
            'https://attacker.com',
            'http://localhost:9999',
            'http://192.168.1.100:3000',
        ]
    
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None, category: str = "CORS General"):
        """Log test result"""
        result = CORSTestResult(
            test_name=test_name,
            status=status,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
        
        status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_color}{status_symbol} {test_name}{Colors.RESET}: {message}")
        if details:
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                print(f"    {Colors.CYAN}{key}{Colors.RESET}: {value}")
    
    # ============================================================================
    # CORS PREFLIGHT (OPTIONS) TESTS
    # ============================================================================
    
    def test_cors_preflight(self):
        """Test CORS preflight (OPTIONS) requests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing CORS Preflight Requests (OPTIONS)...{Colors.RESET}")
        
        test_endpoints = [
            '/api/assessments',
            '/api/vehicle',
            '/api/profile',
            '/health',
        ]
        
        for origin in self.expected_origins:
            for endpoint in test_endpoints[:2]:  # Test first 2 endpoints per origin
                try:
                    response = requests.options(
                        f"{self.base_url}{endpoint}",
                        headers={
                            'Origin': origin,
                            'Access-Control-Request-Method': 'POST',
                            'Access-Control-Request-Headers': 'Content-Type,Authorization'
                        }
                    )
                    
                    headers = response.headers
                    
                    # Check Access-Control-Allow-Origin
                    acao = headers.get('Access-Control-Allow-Origin')
                    if acao == origin or acao == '*':
                        self.log_result(
                            f"Preflight: {origin} → {endpoint}",
                            "PASS",
                            "Access-Control-Allow-Origin header present",
                            {"header_value": acao, "status_code": response.status_code}
                        )
                    else:
                        self.log_result(
                            f"Preflight: {origin} → {endpoint}",
                            "FAIL",
                            f"Access-Control-Allow-Origin missing or incorrect",
                            {"expected": origin, "actual": acao, "status_code": response.status_code}
                        )
                    
                    # Check Access-Control-Allow-Methods
                    acam = headers.get('Access-Control-Allow-Methods')
                    if acam:
                        methods = [m.strip() for m in acam.split(',')]
                        missing_methods = [m for m in self.expected_methods if m not in methods]
                        if not missing_methods:
                            self.log_result(
                                f"Preflight Methods: {origin} → {endpoint}",
                                "PASS",
                                "All expected methods allowed",
                                {"methods": methods}
                            )
                        else:
                            self.log_result(
                                f"Preflight Methods: {origin} → {endpoint}",
                                "WARN",
                                f"Some methods missing",
                                {"allowed": methods, "missing": missing_methods}
                            )
                    else:
                        self.log_result(
                            f"Preflight Methods: {origin} → {endpoint}",
                            "FAIL",
                            "Access-Control-Allow-Methods header missing",
                            {}
                        )
                    
                    # Check Access-Control-Allow-Headers
                    acah = headers.get('Access-Control-Allow-Headers')
                    if acah:
                        headers_list = [h.strip() for h in acah.split(',')]
                        missing_headers = [h for h in self.expected_headers if h not in headers_list]
                        if not missing_headers:
                            self.log_result(
                                f"Preflight Headers: {origin} → {endpoint}",
                                "PASS",
                                "All expected headers allowed",
                                {"headers": headers_list}
                            )
                        else:
                            self.log_result(
                                f"Preflight Headers: {origin} → {endpoint}",
                                "WARN",
                                f"Some headers missing",
                                {"allowed": headers_list, "missing": missing_headers}
                            )
                    else:
                        self.log_result(
                            f"Preflight Headers: {origin} → {endpoint}",
                            "FAIL",
                            "Access-Control-Allow-Headers header missing",
                            {}
                        )
                    
                    # Check Access-Control-Allow-Credentials
                    acac = headers.get('Access-Control-Allow-Credentials')
                    if self.supports_credentials:
                        if acac == 'true':
                            self.log_result(
                                f"Preflight Credentials: {origin} → {endpoint}",
                                "PASS",
                                "Credentials support enabled",
                                {}
                            )
                        else:
                            self.log_result(
                                f"Preflight Credentials: {origin} → {endpoint}",
                                "WARN",
                                "Credentials support may not be enabled",
                                {"header_value": acac}
                            )
                    
                    # Check Max-Age
                    acma = headers.get('Access-Control-Max-Age')
                    if acma:
                        self.log_result(
                            f"Preflight Max-Age: {origin} → {endpoint}",
                            "PASS",
                            "Preflight caching configured",
                            {"max_age": acma}
                        )
                    
                except Exception as e:
                    self.log_result(
                        f"Preflight: {origin} → {endpoint}",
                        "WARN",
                        f"Error testing preflight: {str(e)}",
                        {"error": str(e)}
                    )
    
    # ============================================================================
    # CORS ACTUAL REQUEST TESTS
    # ============================================================================
    
    def test_cors_actual_requests(self):
        """Test CORS headers in actual requests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing CORS Headers in Actual Requests...{Colors.RESET}")
        
        test_endpoints = [
            {'method': 'GET', 'endpoint': '/health'},
            {'method': 'GET', 'endpoint': '/api/status'},
        ]
        
        for origin in self.expected_origins:
            for endpoint_config in test_endpoints:
                method = endpoint_config['method']
                endpoint = endpoint_config['endpoint']
                
                try:
                    if method == 'GET':
                        response = requests.get(
                            f"{self.base_url}{endpoint}",
                            headers={'Origin': origin}
                        )
                    elif method == 'POST':
                        response = requests.post(
                            f"{self.base_url}{endpoint}",
                            headers={'Origin': origin},
                            json={}
                        )
                    else:
                        continue
                    
                    headers = response.headers
                    
                    # Check Access-Control-Allow-Origin
                    acao = headers.get('Access-Control-Allow-Origin')
                    if acao == origin or acao == '*':
                        self.log_result(
                            f"CORS Header: {origin} → {method} {endpoint}",
                            "PASS",
                            "Access-Control-Allow-Origin header present",
                            {"header_value": acao}
                        )
                    else:
                        self.log_result(
                            f"CORS Header: {origin} → {method} {endpoint}",
                            "FAIL",
                            f"Access-Control-Allow-Origin missing or incorrect",
                            {"expected": origin, "actual": acao}
                        )
                    
                    # Check Access-Control-Expose-Headers
                    aceh = headers.get('Access-Control-Expose-Headers')
                    if aceh:
                        exposed = [h.strip() for h in aceh.split(',')]
                        if 'X-CSRF-Token' in exposed:
                            self.log_result(
                                f"CORS Exposed Headers: {origin} → {endpoint}",
                                "PASS",
                                "X-CSRF-Token is exposed",
                                {"exposed_headers": exposed}
                            )
                        else:
                            self.log_result(
                                f"CORS Exposed Headers: {origin} → {endpoint}",
                                "WARN",
                                "X-CSRF-Token may not be exposed",
                                {"exposed_headers": exposed}
                            )
                    else:
                        self.log_result(
                            f"CORS Exposed Headers: {origin} → {endpoint}",
                            "WARN",
                            "Access-Control-Expose-Headers header missing",
                            {}
                        )
                    
                    # Check Access-Control-Allow-Credentials
                    acac = headers.get('Access-Control-Allow-Credentials')
                    if self.supports_credentials:
                        if acac == 'true':
                            self.log_result(
                                f"CORS Credentials: {origin} → {endpoint}",
                                "PASS",
                                "Credentials support enabled",
                                {}
                            )
                        else:
                            self.log_result(
                                f"CORS Credentials: {origin} → {endpoint}",
                                "WARN",
                                "Credentials support may not be enabled",
                                {"header_value": acac}
                            )
                    
                except Exception as e:
                    self.log_result(
                        f"CORS Header: {origin} → {method} {endpoint}",
                        "WARN",
                        f"Error testing CORS: {str(e)}",
                        {"error": str(e)}
                    )
    
    # ============================================================================
    # UNAUTHORIZED ORIGIN BLOCKING TESTS
    # ============================================================================
    
    def test_unauthorized_origins(self):
        """Test that unauthorized origins are blocked"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Unauthorized Origin Blocking...{Colors.RESET}")
        
        test_endpoint = '/health'
        
        for origin in self.unauthorized_origins:
            try:
                # Test preflight
                preflight_response = requests.options(
                    f"{self.base_url}{test_endpoint}",
                    headers={
                        'Origin': origin,
                        'Access-Control-Request-Method': 'GET',
                    }
                )
                
                acao = preflight_response.headers.get('Access-Control-Allow-Origin')
                
                if acao is None or (acao != origin and acao != '*'):
                    self.log_result(
                        f"Unauthorized Origin Blocked: {origin}",
                        "PASS",
                        "Unauthorized origin correctly blocked",
                        {"status_code": preflight_response.status_code}
                    )
                elif acao == '*':
                    self.log_result(
                        f"Unauthorized Origin Blocked: {origin}",
                        "FAIL",
                        "Wildcard CORS allows unauthorized origin",
                        {"header_value": acao}
                    )
                else:
                    self.log_result(
                        f"Unauthorized Origin Blocked: {origin}",
                        "FAIL",
                        "Unauthorized origin is allowed",
                        {"header_value": acao}
                    )
                
                # Test actual request
                actual_response = requests.get(
                    f"{self.base_url}{test_endpoint}",
                    headers={'Origin': origin}
                )
                
                acao_actual = actual_response.headers.get('Access-Control-Allow-Origin')
                
                if acao_actual is None or (acao_actual != origin and acao_actual != '*'):
                    self.log_result(
                        f"Unauthorized Origin Blocked (Actual): {origin}",
                        "PASS",
                        "Unauthorized origin correctly blocked in actual request",
                        {}
                    )
                elif acao_actual == '*':
                    self.log_result(
                        f"Unauthorized Origin Blocked (Actual): {origin}",
                        "FAIL",
                        "Wildcard CORS allows unauthorized origin in actual request",
                        {}
                    )
                else:
                    self.log_result(
                        f"Unauthorized Origin Blocked (Actual): {origin}",
                        "FAIL",
                        "Unauthorized origin is allowed in actual request",
                        {}
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Unauthorized Origin Blocked: {origin}",
                    "WARN",
                    f"Error testing unauthorized origin: {str(e)}",
                    {"error": str(e)}
                )
    
    # ============================================================================
    # CORS CONFIGURATION VERIFICATION
    # ============================================================================
    
    def test_cors_configuration_values(self):
        """Test CORS configuration values match expected"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Verifying CORS Configuration Values...{Colors.RESET}")
        
        # Test with one allowed origin
        origin = self.expected_origins[0]
        
        try:
            response = requests.options(
                f"{self.base_url}/health",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': ','.join(self.expected_headers)
                }
            )
            
            headers = response.headers
            
            # Verify methods
            acam = headers.get('Access-Control-Allow-Methods', '')
            methods = [m.strip().upper() for m in acam.split(',')]
            expected_methods_upper = [m.upper() for m in self.expected_methods]
            
            missing = [m for m in expected_methods_upper if m not in methods]
            extra = [m for m in methods if m not in expected_methods_upper]
            
            if not missing and not extra:
                self.log_result(
                    "CORS Methods Configuration",
                    "PASS",
                    "Methods match expected configuration",
                    {"methods": methods}
                )
            else:
                self.log_result(
                    "CORS Methods Configuration",
                    "WARN",
                    "Methods don't match expected configuration",
                    {"expected": expected_methods_upper, "actual": methods, "missing": missing, "extra": extra}
                )
            
            # Verify headers
            acah = headers.get('Access-Control-Allow-Headers', '')
            headers_list = [h.strip() for h in acah.split(',')]
            expected_headers_upper = [h.upper() for h in self.expected_headers]
            headers_list_upper = [h.upper() for h in headers_list]
            
            missing_headers = [h for h in expected_headers_upper if h not in headers_list_upper]
            extra_headers = [h for h in headers_list_upper if h not in expected_headers_upper]
            
            if not missing_headers:
                self.log_result(
                    "CORS Headers Configuration",
                    "PASS",
                    "All expected headers are allowed",
                    {"headers": headers_list, "extra": extra_headers if extra_headers else None}
                )
            else:
                self.log_result(
                    "CORS Headers Configuration",
                    "WARN",
                    "Some expected headers may be missing",
                    {"expected": self.expected_headers, "actual": headers_list, "missing": missing_headers}
                )
            
            # Verify credentials
            acac = headers.get('Access-Control-Allow-Credentials')
            if self.supports_credentials:
                if acac == 'true':
                    self.log_result(
                        "CORS Credentials Configuration",
                        "PASS",
                        "Credentials support is enabled",
                        {}
                    )
                else:
                    self.log_result(
                        "CORS Credentials Configuration",
                        "WARN",
                        "Credentials support may not be enabled",
                        {"header_value": acac}
                    )
            
        except Exception as e:
            self.log_result(
                "CORS Configuration Values",
                "WARN",
                f"Error verifying configuration: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # CORS WITH CREDENTIALS TESTS
    # ============================================================================
    
    def test_cors_with_credentials(self):
        """Test CORS behavior with credentials"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing CORS with Credentials...{Colors.RESET}")
        
        origin = self.expected_origins[0]
        
        try:
            # Test preflight with credentials
            response = requests.options(
                f"{self.base_url}/health",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Credentials': 'true'
                }
            )
            
            acao = response.headers.get('Access-Control-Allow-Origin')
            acac = response.headers.get('Access-Control-Allow-Credentials')
            
            # When credentials are used, origin cannot be '*'
            if acac == 'true':
                if acao == origin:
                    self.log_result(
                        "CORS Credentials with Specific Origin",
                        "PASS",
                        "Credentials work with specific origin (not wildcard)",
                        {"origin": acao}
                    )
                elif acao == '*':
                    self.log_result(
                        "CORS Credentials with Specific Origin",
                        "FAIL",
                        "Wildcard origin cannot be used with credentials",
                        {"origin": acao}
                    )
                else:
                    self.log_result(
                        "CORS Credentials with Specific Origin",
                        "WARN",
                        "Unexpected origin value with credentials",
                        {"origin": acao}
                    )
            else:
                self.log_result(
                    "CORS Credentials Support",
                    "WARN",
                    "Credentials support may not be enabled",
                    {"header_value": acac}
                )
                
        except Exception as e:
            self.log_result(
                "CORS Credentials Test",
                "WARN",
                f"Error testing credentials: {str(e)}",
                {"error": str(e)}
            )
    
    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================
    
    def run_all_tests(self):
        """Run all CORS verification tests"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}MINGUS CORS Configuration Verification{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}Expected Configuration:{Colors.RESET}")
        print(f"  Origins: {', '.join(self.expected_origins)}")
        print(f"  Methods: {', '.join(self.expected_methods)}")
        print(f"  Headers: {', '.join(self.expected_headers)}")
        print(f"  Credentials: {self.supports_credentials}")
        print(f"  Exposed Headers: {', '.join(self.expected_exposed_headers)}")
        print()
        
        # Run all test categories
        self.test_cors_preflight()
        self.test_cors_actual_requests()
        self.test_unauthorized_origins()
        self.test_cors_configuration_values()
        self.test_cors_with_credentials()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CORS VERIFICATION SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.RESET}")
        
        # Group by category
        categories = {}
        for result in self.results:
            # Extract category from test name or use default
            category = "CORS General"
            if "Preflight" in result.test_name:
                category = "CORS Preflight"
            elif "Header" in result.test_name:
                category = "CORS Headers"
            elif "Unauthorized" in result.test_name or "Blocked" in result.test_name:
                category = "CORS Security"
            elif "Config" in result.test_name:
                category = "CORS Config"
            elif "Credentials" in result.test_name:
                category = "CORS Credentials"
            
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0, 'failed': 0, 'warn': 0}
            categories[category]['total'] += 1
            if result.status == "PASS":
                categories[category]['passed'] += 1
            elif result.status == "FAIL":
                categories[category]['failed'] += 1
            else:
                categories[category]['warn'] += 1
        
        print(f"\n{Colors.BOLD}Results by Category:{Colors.RESET}")
        for category, stats in categories.items():
            print(f"\n  {Colors.BOLD}{category}:{Colors.RESET}")
            print(f"    Total: {stats['total']}")
            print(f"    {Colors.GREEN}Passed: {stats['passed']}{Colors.RESET}")
            print(f"    {Colors.RED}Failed: {stats['failed']}{Colors.RESET}")
            print(f"    {Colors.YELLOW}Warnings: {stats['warn']}{Colors.RESET}")
        
        # List failed tests
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in failed_tests:
                print(f"  ❌ {result.test_name}: {result.message}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cors_verification_results_{timestamp}.json"
        
        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'expected_configuration': {
                'origins': self.expected_origins,
                'methods': self.expected_methods,
                'headers': self.expected_headers,
                'exposed_headers': self.expected_exposed_headers,
                'supports_credentials': self.supports_credentials
            },
            'summary': {
                'total': len(self.results),
                'passed': len([r for r in self.results if r.status == "PASS"]),
                'failed': len([r for r in self.results if r.status == "FAIL"]),
                'warnings': len([r for r in self.results if r.status == "WARN"]),
            },
            'results': [asdict(r) for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"\n{Colors.CYAN}Results saved to: {filename}{Colors.RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CORS Configuration Verification')
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL of the backend API (default: http://localhost:5000)'
    )
    
    args = parser.parse_args()
    
    verifier = CORSVerifier(base_url=args.base_url)
    verifier.run_all_tests()

if __name__ == '__main__':
    main()
