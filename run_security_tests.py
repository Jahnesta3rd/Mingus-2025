#!/usr/bin/env python3
"""
MINGUS Application - Comprehensive Security Test Suite
====================================================

This script runs all security tests for the MINGUS application to validate:
1. CSRF protection on all financial endpoints
2. JWT authentication and authorization
3. Authentication bypass vulnerability fixes
4. User profile security and data protection
5. Session management security

Author: MINGUS Security Team
Date: January 2025
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the tests directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests', 'security'))

try:
    from test_csrf_protection import CSRFProtectionTester
    from test_jwt_authentication import JWTAuthenticationTester
    from test_auth_bypass_fix import AuthBypassTester
    from test_user_profile_security import UserProfileSecurityTester
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    print("Make sure all test files are in the tests/security/ directory")
    sys.exit(1)

class ComprehensiveSecurityTester:
    """Comprehensive security test suite runner"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.start_time = datetime.now()
        self.test_results = {}
        self.overall_status = "PENDING"
        
        # Initialize test suites
        self.csrf_tester = CSRFProtectionTester(base_url)
        self.jwt_tester = JWTAuthenticationTester(base_url)
        self.auth_bypass_tester = AuthBypassTester(base_url)
        self.profile_tester = UserProfileSecurityTester(base_url)
    
    def run_csrf_tests(self):
        """Run CSRF protection tests"""
        print("\n🔒 Running CSRF Protection Tests")
        print("=" * 40)
        
        try:
            results = self.csrf_tester.run_tests()
            self.test_results['csrf_protection'] = {
                'status': 'COMPLETED',
                'results': results,
                'passed': len([r for r in results if r.get('status') == 'PASS']),
                'total': len(results)
            }
            print(f"✅ CSRF tests completed: {self.test_results['csrf_protection']['passed']}/{self.test_results['csrf_protection']['total']} passed")
        except Exception as e:
            self.test_results['csrf_protection'] = {
                'status': 'ERROR',
                'error': str(e),
                'passed': 0,
                'total': 0
            }
            print(f"❌ CSRF tests failed: {e}")
    
    def run_jwt_tests(self):
        """Run JWT authentication tests"""
        print("\n🔐 Running JWT Authentication Tests")
        print("=" * 40)
        
        try:
            results = self.jwt_tester.run_tests()
            self.test_results['jwt_authentication'] = {
                'status': 'COMPLETED',
                'results': results,
                'passed': len([r for r in results if r.get('status') == 'PASS']),
                'total': len(results)
            }
            print(f"✅ JWT tests completed: {self.test_results['jwt_authentication']['passed']}/{self.test_results['jwt_authentication']['total']} passed")
        except Exception as e:
            self.test_results['jwt_authentication'] = {
                'status': 'ERROR',
                'error': str(e),
                'passed': 0,
                'total': 0
            }
            print(f"❌ JWT tests failed: {e}")
    
    def run_auth_bypass_tests(self):
        """Run authentication bypass vulnerability tests"""
        print("\n🚨 Running Authentication Bypass Tests")
        print("=" * 40)
        
        try:
            results = self.auth_bypass_tester.run_tests()
            critical_issues = len([r for r in results if r.get('status') == 'CRITICAL'])
            self.test_results['auth_bypass'] = {
                'status': 'COMPLETED',
                'results': results,
                'passed': len([r for r in results if r.get('status') == 'PASS']),
                'total': len(results),
                'critical': critical_issues
            }
            print(f"✅ Auth bypass tests completed: {self.test_results['auth_bypass']['passed']}/{self.test_results['auth_bypass']['total']} passed, {critical_issues} critical issues")
        except Exception as e:
            self.test_results['auth_bypass'] = {
                'status': 'ERROR',
                'error': str(e),
                'passed': 0,
                'total': 0,
                'critical': 0
            }
            print(f"❌ Auth bypass tests failed: {e}")
    
    def run_profile_security_tests(self):
        """Run user profile security tests"""
        print("\n👤 Running User Profile Security Tests")
        print("=" * 40)
        
        try:
            results = self.profile_tester.run_tests()
            critical_issues = len([r for r in results if r.get('status') == 'CRITICAL'])
            self.test_results['profile_security'] = {
                'status': 'COMPLETED',
                'results': results,
                'passed': len([r for r in results if r.get('status') == 'PASS']),
                'total': len(results),
                'critical': critical_issues
            }
            print(f"✅ Profile security tests completed: {self.test_results['profile_security']['passed']}/{self.test_results['profile_security']['total']} passed, {critical_issues} critical issues")
        except Exception as e:
            self.test_results['profile_security'] = {
                'status': 'ERROR',
                'error': str(e),
                'passed': 0,
                'total': 0,
                'critical': 0
            }
            print(f"❌ Profile security tests failed: {e}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🚀 MINGUS Comprehensive Security Test Suite")
        print("=" * 50)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        print("=" * 50)
        
        # Run all test suites
        self.run_csrf_tests()
        self.run_jwt_tests()
        self.run_auth_bypass_tests()
        self.run_profile_security_tests()
        
        # Calculate overall results
        self.calculate_overall_status()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
        
        return self.overall_status == "PASS"
    
    def calculate_overall_status(self):
        """Calculate overall test status"""
        total_passed = 0
        total_tests = 0
        total_critical = 0
        
        for test_suite, results in self.test_results.items():
            if results['status'] == 'COMPLETED':
                total_passed += results['passed']
                total_tests += results['total']
                total_critical += results.get('critical', 0)
        
        if total_tests == 0:
            self.overall_status = "ERROR"
        elif total_critical > 0:
            self.overall_status = "CRITICAL"
        elif total_passed == total_tests:
            self.overall_status = "PASS"
        else:
            self.overall_status = "FAIL"
        
        self.overall_stats = {
            'total_passed': total_passed,
            'total_tests': total_tests,
            'total_critical': total_critical,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
    
    def generate_comprehensive_report(self):
        """Generate comprehensive security test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = f"""
🔒 MINGUS COMPREHENSIVE SECURITY TEST REPORT
==========================================

📊 EXECUTIVE SUMMARY
- Test Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- Duration: {duration.total_seconds():.2f} seconds
- Target URL: {self.base_url}
- Overall Status: {self.overall_status}

📈 OVERALL STATISTICS
- Total Tests: {self.overall_stats['total_tests']}
- Passed: {self.overall_stats['total_passed']} ✅
- Failed: {self.overall_stats['total_tests'] - self.overall_stats['total_passed']} ❌
- Critical Issues: {self.overall_stats['total_critical']} 🚨
- Success Rate: {self.overall_stats['success_rate']:.1f}%

📋 TEST SUITE RESULTS
"""
        
        # Add results for each test suite
        for test_suite, results in self.test_results.items():
            suite_name = test_suite.replace('_', ' ').title()
            
            if results['status'] == 'COMPLETED':
                critical_text = f", {results.get('critical', 0)} critical" if results.get('critical', 0) > 0 else ""
                report += f"""
✅ {suite_name}
   Status: {results['status']}
   Results: {results['passed']}/{results['total']} passed{critical_text}
"""
            else:
                report += f"""
❌ {suite_name}
   Status: {results['status']}
   Error: {results.get('error', 'Unknown error')}
"""
        
        # Add critical findings section
        if self.overall_stats['total_critical'] > 0:
            report += f"""

🚨 CRITICAL SECURITY ISSUES FOUND
================================
"""
            for test_suite, results in self.test_results.items():
                if results['status'] == 'COMPLETED' and results.get('critical', 0) > 0:
                    critical_tests = [r for r in results['results'] if r.get('status') == 'CRITICAL']
                    for test in critical_tests:
                        report += f"""
❌ {test.get('test', 'Unknown Test')}
   Message: {test.get('message', 'No message')}
   Details: {test.get('details', 'No details')}
"""
        
        # Add security recommendations
        report += f"""

🔧 SECURITY RECOMMENDATIONS
==========================
"""
        
        if self.overall_status == "CRITICAL":
            report += """
🚨 IMMEDIATE ACTION REQUIRED:
- Critical security vulnerabilities found
- Do not deploy to production until fixed
- Review authentication and authorization systems
- Implement proper CSRF protection
- Ensure all endpoints require authentication
"""
        elif self.overall_status == "FAIL":
            report += """
⚠️  SECURITY IMPROVEMENTS NEEDED:
- Some security tests failed
- Review failed test results
- Implement missing security measures
- Consider additional security hardening
"""
        else:
            report += """
✅ SECURITY STATUS GOOD:
- All critical security tests passed
- Application appears secure for deployment
- Continue regular security testing
- Monitor for new vulnerabilities
"""
        
        # Add detailed test results
        report += f"""

�� DETAILED TEST RESULTS
=======================
"""
        
        for test_suite, results in self.test_results.items():
            if results['status'] == 'COMPLETED':
                suite_name = test_suite.replace('_', ' ').title()
                report += f"\n{suite_name}:\n"
                for test in results['results']:
                    status_icon = "✅" if test.get('status') == 'PASS' else "❌" if test.get('status') == 'FAIL' else "🚨" if test.get('status') == 'CRITICAL' else "⚠️"
                    report += f"  {status_icon} {test.get('test', 'Unknown')}: {test.get('message', 'No message')}\n"
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'comprehensive_security_test_report_{timestamp}.txt'
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Comprehensive report saved to: {filename}")
        print(report)
        
        return report
    
    def save_json_report(self):
        """Save test results as JSON for programmatic access"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'security_test_results_{timestamp}.json'
        
        json_data = {
            'timestamp': self.start_time.isoformat(),
            'base_url': self.base_url,
            'overall_status': self.overall_status,
            'overall_stats': self.overall_stats,
            'test_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"📊 JSON results saved to: {filename}")
        return filename

def main():
    """Main function to run comprehensive security tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive security tests for MINGUS application')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of the application')
    parser.add_argument('--json', action='store_true', help='Save results as JSON')
    parser.add_argument('--suite', choices=['csrf', 'jwt', 'auth_bypass', 'profile', 'all'], 
                       default='all', help='Run specific test suite')
    
    args = parser.parse_args()
    
    tester = ComprehensiveSecurityTester(args.url)
    
    if args.suite == 'all':
        success = tester.run_all_tests()
    elif args.suite == 'csrf':
        tester.run_csrf_tests()
        success = True
    elif args.suite == 'jwt':
        tester.run_jwt_tests()
        success = True
    elif args.suite == 'auth_bypass':
        tester.run_auth_bypass_tests()
        success = True
    elif args.suite == 'profile':
        tester.run_profile_security_tests()
        success = True
    
    if args.json:
        tester.save_json_report()
    
    # Return appropriate exit code
    if tester.overall_status == "CRITICAL":
        return 2  # Critical security issues
    elif tester.overall_status == "FAIL":
        return 1  # Some tests failed
    elif tester.overall_status == "ERROR":
        return 3  # Test execution errors
    else:
        return 0  # All tests passed

if __name__ == "__main__":
    exit(main())
