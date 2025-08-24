#!/usr/bin/env python3
"""
MINGUS Security Headers Testing Utilities
Comprehensive testing suite for banking-grade security headers
"""

import os
import sys
import json
import requests
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.headers import SecurityHeadersMiddleware, SecurityConfig, SecurityHeaders

@dataclass
class SecurityTestResult:
    """Result of a security header test"""
    test_name: str
    passed: bool
    details: Dict[str, Any]
    recommendations: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'

class SecurityHeadersTester:
    """Comprehensive security headers testing utility"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_all_headers(self) -> List[SecurityTestResult]:
        """Run all security header tests"""
        print("🔒 Running comprehensive security headers tests...")
        
        tests = [
            self.test_hsts_header,
            self.test_csp_header,
            self.test_x_content_type_options,
            self.test_x_frame_options,
            self.test_x_xss_protection,
            self.test_referrer_policy,
            self.test_permissions_policy,
            self.test_expect_ct,
            self.test_additional_headers,
            self.test_csp_violations,
            self.test_clickjacking_protection,
            self.test_mime_sniffing_protection,
            self.test_xss_protection,
            self.test_https_enforcement,
            self.test_content_security_policy_strictness
        ]
        
        for test in tests:
            try:
                result = test()
                self.results.append(result)
                self._print_test_result(result)
            except Exception as e:
                error_result = SecurityTestResult(
                    test_name=test.__name__,
                    passed=False,
                    details={'error': str(e)},
                    recommendations=['Fix test implementation'],
                    severity='high'
                )
                self.results.append(error_result)
                self._print_test_result(error_result)
        
        return self.results
    
    def test_hsts_header(self) -> SecurityTestResult:
        """Test HTTP Strict Transport Security header"""
        try:
            response = self.session.get(f"{self.base_url}/", allow_redirects=False)
            hsts_header = response.headers.get('Strict-Transport-Security')
            
            if not hsts_header:
                return SecurityTestResult(
                    test_name="HSTS Header",
                    passed=False,
                    details={'header_present': False},
                    recommendations=[
                        'Add Strict-Transport-Security header',
                        'Set max-age to at least 31536000 (1 year)',
                        'Include includeSubDomains directive'
                    ],
                    severity='critical'
                )
            
            # Parse HSTS header
            directives = {}
            for directive in hsts_header.split(';'):
                directive = directive.strip()
                if '=' in directive:
                    key, value = directive.split('=', 1)
                    directives[key.strip()] = value.strip()
                else:
                    directives[directive] = True
            
            max_age = int(directives.get('max-age', 0))
            include_subdomains = 'includeSubDomains' in directives
            preload = 'preload' in directives
            
            passed = max_age >= 31536000 and include_subdomains
            
            recommendations = []
            if max_age < 31536000:
                recommendations.append('Increase max-age to at least 31536000')
            if not include_subdomains:
                recommendations.append('Add includeSubDomains directive')
            if not preload:
                recommendations.append('Consider adding preload directive')
            
            return SecurityTestResult(
                test_name="HSTS Header",
                passed=passed,
                details={
                    'header_value': hsts_header,
                    'max_age': max_age,
                    'include_subdomains': include_subdomains,
                    'preload': preload
                },
                recommendations=recommendations,
                severity='critical'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="HSTS Header",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='critical'
            )
    
    def test_csp_header(self) -> SecurityTestResult:
        """Test Content Security Policy header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            csp_header = response.headers.get('Content-Security-Policy')
            csp_report_only = response.headers.get('Content-Security-Policy-Report-Only')
            
            if not csp_header and not csp_report_only:
                return SecurityTestResult(
                    test_name="CSP Header",
                    passed=False,
                    details={'header_present': False},
                    recommendations=[
                        'Add Content-Security-Policy header',
                        'Configure strict CSP policy for financial app',
                        'Include report-uri for violation reporting'
                    ],
                    severity='critical'
                )
            
            # Use report-only header if main CSP not present
            csp_value = csp_header or csp_report_only
            is_report_only = bool(csp_report_only and not csp_header)
            
            # Parse CSP directives
            directives = {}
            for directive in csp_value.split(';'):
                directive = directive.strip()
                if ' ' in directive:
                    key, values = directive.split(' ', 1)
                    directives[key.strip()] = values.strip().split(' ')
                else:
                    directives[directive.strip()] = []
            
            # Check for critical directives
            critical_directives = ['default-src', 'script-src', 'style-src']
            missing_directives = [d for d in critical_directives if d not in directives]
            
            # Check for unsafe directives
            unsafe_patterns = ["'unsafe-inline'", "'unsafe-eval'", "data:"]
            unsafe_found = []
            
            for directive, values in directives.items():
                for value in values:
                    if value in unsafe_patterns:
                        unsafe_found.append(f"{directive}: {value}")
            
            passed = len(missing_directives) == 0 and len(unsafe_found) == 0 and not is_report_only
            
            recommendations = []
            if missing_directives:
                recommendations.append(f'Add missing directives: {", ".join(missing_directives)}')
            if unsafe_found:
                recommendations.append(f'Remove unsafe patterns: {", ".join(unsafe_found)}')
            if is_report_only:
                recommendations.append('Switch from report-only to enforced CSP')
            
            return SecurityTestResult(
                test_name="CSP Header",
                passed=passed,
                details={
                    'header_value': csp_value,
                    'is_report_only': is_report_only,
                    'directives': list(directives.keys()),
                    'missing_directives': missing_directives,
                    'unsafe_patterns': unsafe_found
                },
                recommendations=recommendations,
                severity='critical'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="CSP Header",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='critical'
            )
    
    def test_x_content_type_options(self) -> SecurityTestResult:
        """Test X-Content-Type-Options header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('X-Content-Type-Options')
            
            passed = header_value == 'nosniff'
            
            return SecurityTestResult(
                test_name="X-Content-Type-Options",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Set to "nosniff"' if not passed else []],
                severity='high'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="X-Content-Type-Options",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='high'
            )
    
    def test_x_frame_options(self) -> SecurityTestResult:
        """Test X-Frame-Options header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('X-Frame-Options')
            
            passed = header_value in ['DENY', 'SAMEORIGIN']
            
            return SecurityTestResult(
                test_name="X-Frame-Options",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Set to "DENY" or "SAMEORIGIN"' if not passed else []],
                severity='high'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="X-Frame-Options",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='high'
            )
    
    def test_x_xss_protection(self) -> SecurityTestResult:
        """Test X-XSS-Protection header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('X-XSS-Protection')
            
            passed = header_value == '1; mode=block'
            
            return SecurityTestResult(
                test_name="X-XSS-Protection",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Set to "1; mode=block"' if not passed else []],
                severity='medium'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="X-XSS-Protection",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='medium'
            )
    
    def test_referrer_policy(self) -> SecurityTestResult:
        """Test Referrer-Policy header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('Referrer-Policy')
            
            secure_policies = [
                'strict-origin-when-cross-origin',
                'strict-origin',
                'no-referrer-when-downgrade'
            ]
            
            passed = header_value in secure_policies
            
            return SecurityTestResult(
                test_name="Referrer-Policy",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Use secure referrer policy' if not passed else []],
                severity='medium'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Referrer-Policy",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='medium'
            )
    
    def test_permissions_policy(self) -> SecurityTestResult:
        """Test Permissions-Policy header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('Permissions-Policy')
            
            passed = bool(header_value)
            
            return SecurityTestResult(
                test_name="Permissions-Policy",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Add Permissions-Policy header' if not passed else []],
                severity='medium'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Permissions-Policy",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='medium'
            )
    
    def test_expect_ct(self) -> SecurityTestResult:
        """Test Expect-CT header"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('Expect-CT')
            
            # Expect-CT is optional but recommended
            passed = True  # Not critical for basic security
            
            return SecurityTestResult(
                test_name="Expect-CT",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Add Expect-CT header for enhanced security' if not header_value else []],
                severity='low'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Expect-CT",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='low'
            )
    
    def test_additional_headers(self) -> SecurityTestResult:
        """Test additional security headers"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            additional_headers = {
                'X-Download-Options': 'noopen',
                'X-Permitted-Cross-Domain-Policies': 'none',
                'X-DNS-Prefetch-Control': 'off'
            }
            
            missing_headers = []
            for header, expected_value in additional_headers.items():
                if header not in response.headers:
                    missing_headers.append(header)
            
            passed = len(missing_headers) == 0
            
            return SecurityTestResult(
                test_name="Additional Security Headers",
                passed=passed,
                details={'missing_headers': missing_headers},
                recommendations=[f'Add {header} header' for header in missing_headers],
                severity='medium'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Additional Security Headers",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='medium'
            )
    
    def test_csp_violations(self) -> SecurityTestResult:
        """Test CSP violation reporting"""
        try:
            # Test CSP violation reporting endpoint
            violation_data = {
                'csp-report': {
                    'document-uri': f'{self.base_url}/test',
                    'violated-directive': 'script-src',
                    'blocked-uri': 'https://malicious.com/script.js'
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/csp-report",
                json=violation_data,
                headers={'Content-Type': 'application/json'}
            )
            
            passed = response.status_code == 204
            
            return SecurityTestResult(
                test_name="CSP Violation Reporting",
                passed=passed,
                details={'status_code': response.status_code},
                recommendations=['Fix CSP violation reporting endpoint' if not passed else []],
                severity='medium'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="CSP Violation Reporting",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check CSP reporting endpoint'],
                severity='medium'
            )
    
    def test_clickjacking_protection(self) -> SecurityTestResult:
        """Test clickjacking protection"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            # Check X-Frame-Options
            x_frame_options = response.headers.get('X-Frame-Options')
            
            # Check CSP frame-ancestors
            csp_header = response.headers.get('Content-Security-Policy', '')
            has_frame_ancestors = 'frame-ancestors' in csp_header
            
            passed = x_frame_options in ['DENY', 'SAMEORIGIN'] or has_frame_ancestors
            
            return SecurityTestResult(
                test_name="Clickjacking Protection",
                passed=passed,
                details={
                    'x_frame_options': x_frame_options,
                    'has_frame_ancestors': has_frame_ancestors
                },
                recommendations=['Implement clickjacking protection' if not passed else []],
                severity='high'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Clickjacking Protection",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='high'
            )
    
    def test_mime_sniffing_protection(self) -> SecurityTestResult:
        """Test MIME sniffing protection"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('X-Content-Type-Options')
            
            passed = header_value == 'nosniff'
            
            return SecurityTestResult(
                test_name="MIME Sniffing Protection",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Set X-Content-Type-Options to "nosniff"' if not passed else []],
                severity='high'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="MIME Sniffing Protection",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='high'
            )
    
    def test_xss_protection(self) -> SecurityTestResult:
        """Test XSS protection"""
        try:
            response = self.session.get(f"{self.base_url}/")
            header_value = response.headers.get('X-XSS-Protection')
            
            passed = header_value == '1; mode=block'
            
            return SecurityTestResult(
                test_name="XSS Protection",
                passed=passed,
                details={'header_value': header_value},
                recommendations=['Set X-XSS-Protection to "1; mode=block"' if not passed else []],
                severity='high'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="XSS Protection",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='high'
            )
    
    def test_https_enforcement(self) -> SecurityTestResult:
        """Test HTTPS enforcement"""
        try:
            # Test HTTP to HTTPS redirect
            http_url = self.base_url.replace('https://', 'http://')
            response = self.session.get(http_url, allow_redirects=False)
            
            # Check if redirected to HTTPS
            is_redirect = response.status_code in [301, 302, 307, 308]
            redirects_to_https = 'https://' in response.headers.get('Location', '')
            
            passed = is_redirect and redirects_to_https
            
            return SecurityTestResult(
                test_name="HTTPS Enforcement",
                passed=passed,
                details={
                    'status_code': response.status_code,
                    'location': response.headers.get('Location'),
                    'is_redirect': is_redirect,
                    'redirects_to_https': redirects_to_https
                },
                recommendations=['Implement HTTP to HTTPS redirect' if not passed else []],
                severity='critical'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="HTTPS Enforcement",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='critical'
            )
    
    def test_content_security_policy_strictness(self) -> SecurityTestResult:
        """Test CSP policy strictness for financial app"""
        try:
            response = self.session.get(f"{self.base_url}/")
            csp_header = response.headers.get('Content-Security-Policy', '')
            
            # Check for strict CSP requirements
            strictness_checks = {
                'has_default_src': 'default-src' in csp_header,
                'has_script_src': 'script-src' in csp_header,
                'no_unsafe_inline': "'unsafe-inline'" not in csp_header,
                'no_unsafe_eval': "'unsafe-eval'" not in csp_header,
                'has_frame_ancestors': 'frame-ancestors' in csp_header,
                'has_form_action': 'form-action' in csp_header,
                'has_base_uri': 'base-uri' in csp_header
            }
            
            passed = all(strictness_checks.values())
            
            failed_checks = [k for k, v in strictness_checks.items() if not v]
            
            return SecurityTestResult(
                test_name="CSP Policy Strictness",
                passed=passed,
                details={'strictness_checks': strictness_checks},
                recommendations=[f'Fix CSP strictness: {check}' for check in failed_checks],
                severity='critical'
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="CSP Policy Strictness",
                passed=False,
                details={'error': str(e)},
                recommendations=['Check server connectivity'],
                severity='critical'
            )
    
    def _print_test_result(self, result: SecurityTestResult):
        """Print test result with formatting"""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        print(f"{status} {severity_emoji.get(result.severity, '⚪')} {result.test_name}")
        
        if not result.passed and result.recommendations:
            print(f"   Recommendations:")
            for rec in result.recommendations:
                print(f"   - {rec}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        severity_counts = {}
        for result in self.results:
            severity = result.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        critical_failures = [r for r in self.results if not r.passed and r.severity == 'critical']
        high_failures = [r for r in self.results if not r.passed and r.severity == 'high']
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'severity_breakdown': severity_counts,
            'critical_failures': [r.test_name for r in critical_failures],
            'high_failures': [r.test_name for r in high_failures],
            'all_results': [
                {
                    'test_name': r.test_name,
                    'passed': r.passed,
                    'severity': r.severity,
                    'recommendations': r.recommendations
                }
                for r in self.results
            ]
        }

def run_security_tests(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """Run all security tests and return report"""
    tester = SecurityHeadersTester(base_url)
    tester.test_all_headers()
    return tester.generate_report()

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test MINGUS security headers')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--output', help='Output file for JSON report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print(f"🔒 Testing security headers for: {args.url}")
    print("=" * 60)
    
    report = run_security_tests(args.url)
    
    print("\n" + "=" * 60)
    print("📊 SECURITY REPORT SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    
    if report['critical_failures']:
        print(f"\n🔴 CRITICAL FAILURES:")
        for failure in report['critical_failures']:
            print(f"  - {failure}")
    
    if report['high_failures']:
        print(f"\n🟠 HIGH PRIORITY FAILURES:")
        for failure in report['high_failures']:
            print(f"  - {failure}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with error code if critical failures
    if report['critical_failures']:
        sys.exit(1)

if __name__ == "__main__":
    main() 