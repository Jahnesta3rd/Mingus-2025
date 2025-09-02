#!/usr/bin/env python3
"""
CSP Testing Suite for Mingus Financial App
Comprehensive testing of Content Security Policy implementation
"""

import os
import sys
import json
import requests
import unittest
import subprocess
from typing import Dict, List, Optional
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

class CSPTestSuite:
    """Comprehensive CSP testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.violations = []
        
    def run_all_tests(self) -> Dict:
        """Run all CSP tests"""
        print("🔍 Starting CSP Test Suite...")
        print("=" * 60)
        
        # Test CSP headers
        self.test_csp_headers()
        
        # Test resource loading
        self.test_resource_loading()
        
        # Test third-party integrations
        self.test_third_party_integrations()
        
        # Test inline content handling
        self.test_inline_content()
        
        # Test violation reporting
        self.test_violation_reporting()
        
        # Test browser compatibility
        self.test_browser_compatibility()
        
        # Generate report
        return self.generate_report()
    
    def test_csp_headers(self):
        """Test CSP header presence and configuration"""
        print("📋 Testing CSP Headers...")
        
        try:
            response = requests.get(self.base_url)
            
            # Check for CSP header
            csp_header = response.headers.get('Content-Security-Policy')
            csp_report_only = response.headers.get('Content-Security-Policy-Report-Only')
            
            if csp_header:
                self.test_results.append({
                    'test': 'CSP Header Present',
                    'status': 'PASS',
                    'details': f'CSP header found: {csp_header[:100]}...'
                })
                
                # Validate CSP directives
                self._validate_csp_directives(csp_header)
            else:
                self.test_results.append({
                    'test': 'CSP Header Present',
                    'status': 'FAIL',
                    'details': 'No CSP header found'
                })
            
            # Check other security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Referrer-Policy',
                'Permissions-Policy'
            ]
            
            for header in security_headers:
                if header in response.headers:
                    self.test_results.append({
                        'test': f'{header} Header',
                        'status': 'PASS',
                        'details': f'{header}: {response.headers[header]}'
                    })
                else:
                    self.test_results.append({
                        'test': f'{header} Header',
                        'status': 'WARN',
                        'details': f'{header} header not found'
                    })
                    
        except Exception as e:
            self.test_results.append({
                'test': 'CSP Headers',
                'status': 'ERROR',
                'details': f'Error testing headers: {str(e)}'
            })
    
    def _validate_csp_directives(self, csp_header: str):
        """Validate CSP directive configuration"""
        required_directives = [
            'default-src',
            'script-src',
            'style-src',
            'img-src',
            'connect-src'
        ]
        
        for directive in required_directives:
            if directive in csp_header:
                self.test_results.append({
                    'test': f'CSP {directive}',
                    'status': 'PASS',
                    'details': f'{directive} directive present'
                })
            else:
                self.test_results.append({
                    'test': f'CSP {directive}',
                    'status': 'WARN',
                    'details': f'{directive} directive missing'
                })
        
        # Check for unsafe directives
        unsafe_patterns = [
            "'unsafe-inline'",
            "'unsafe-eval'",
            "data:",
            "blob:"
        ]
        
        for pattern in unsafe_patterns:
            if pattern in csp_header:
                self.test_results.append({
                    'test': f'CSP Security - {pattern}',
                    'status': 'WARN',
                    'details': f'Unsafe pattern found: {pattern}'
                })
    
    def test_resource_loading(self):
        """Test loading of various resource types"""
        print("📦 Testing Resource Loading...")
        
        # Test internal resources
        internal_resources = [
            '/static/css/style.css',
            '/static/js/app.js',
            '/favicon.ico',
            '/api/health'
        ]
        
        for resource in internal_resources:
            try:
                response = requests.get(urljoin(self.base_url, resource))
                if response.status_code == 200:
                    self.test_results.append({
                        'test': f'Internal Resource: {resource}',
                        'status': 'PASS',
                        'details': f'Successfully loaded {resource}'
                    })
                else:
                    self.test_results.append({
                        'test': f'Internal Resource: {resource}',
                        'status': 'WARN',
                        'details': f'Resource returned {response.status_code}'
                    })
            except Exception as e:
                self.test_results.append({
                    'test': f'Internal Resource: {resource}',
                    'status': 'ERROR',
                    'details': f'Error loading {resource}: {str(e)}'
                })
    
    def test_third_party_integrations(self):
        """Test third-party service integrations"""
        print("🔗 Testing Third-Party Integrations...")
        
        # Test Stripe integration
        self._test_stripe_integration()
        
        # Test Google Analytics
        self._test_google_analytics()
        
        # Test Supabase integration
        self._test_supabase_integration()
    
    def _test_stripe_integration(self):
        """Test Stripe payment integration"""
        try:
            # Test Stripe script loading
            stripe_test_url = urljoin(self.base_url, '/payment/test')
            response = requests.get(stripe_test_url)
            
            if response.status_code == 200:
                # Check for Stripe-related content
                if 'stripe' in response.text.lower():
                    self.test_results.append({
                        'test': 'Stripe Integration',
                        'status': 'PASS',
                        'details': 'Stripe integration detected'
                    })
                else:
                    self.test_results.append({
                        'test': 'Stripe Integration',
                        'status': 'WARN',
                        'details': 'Stripe integration not found'
                    })
            else:
                self.test_results.append({
                    'test': 'Stripe Integration',
                    'status': 'SKIP',
                    'details': 'Payment endpoint not available'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Stripe Integration',
                'status': 'ERROR',
                'details': f'Error testing Stripe: {str(e)}'
            })
    
    def _test_google_analytics(self):
        """Test Google Analytics integration"""
        try:
            response = requests.get(self.base_url)
            
            # Check for Google Analytics scripts
            if 'googletagmanager.com' in response.text or 'google-analytics.com' in response.text:
                self.test_results.append({
                    'test': 'Google Analytics',
                    'status': 'PASS',
                    'details': 'Google Analytics integration detected'
                })
            else:
                self.test_results.append({
                    'test': 'Google Analytics',
                    'status': 'INFO',
                    'details': 'Google Analytics not configured'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Google Analytics',
                'status': 'ERROR',
                'details': f'Error testing GA: {str(e)}'
            })
    
    def _test_supabase_integration(self):
        """Test Supabase integration"""
        try:
            response = requests.get(self.base_url)
            
            # Check for Supabase scripts
            if 'supabase' in response.text.lower():
                self.test_results.append({
                    'test': 'Supabase Integration',
                    'status': 'PASS',
                    'details': 'Supabase integration detected'
                })
            else:
                self.test_results.append({
                    'test': 'Supabase Integration',
                    'status': 'INFO',
                    'details': 'Supabase not found in page'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Supabase Integration',
                'status': 'ERROR',
                'details': f'Error testing Supabase: {str(e)}'
            })
    
    def test_inline_content(self):
        """Test inline script and style handling"""
        print("📝 Testing Inline Content...")
        
        try:
            response = requests.get(self.base_url)
            content = response.text
            
            # Check for inline scripts
            inline_scripts = content.count('<script>') + content.count('<script ')
            if inline_scripts > 0:
                self.test_results.append({
                    'test': 'Inline Scripts',
                    'status': 'WARN',
                    'details': f'Found {inline_scripts} inline script tags'
                })
            else:
                self.test_results.append({
                    'test': 'Inline Scripts',
                    'status': 'PASS',
                    'details': 'No inline scripts found'
                })
            
            # Check for inline styles
            inline_styles = content.count('<style>') + content.count('style="')
            if inline_styles > 0:
                self.test_results.append({
                    'test': 'Inline Styles',
                    'status': 'INFO',
                    'details': f'Found {inline_styles} inline style elements'
                })
            else:
                self.test_results.append({
                    'test': 'Inline Styles',
                    'status': 'PASS',
                    'details': 'No inline styles found'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Inline Content',
                'status': 'ERROR',
                'details': f'Error testing inline content: {str(e)}'
            })
    
    def test_violation_reporting(self):
        """Test CSP violation reporting"""
        print("🚨 Testing Violation Reporting...")
        
        try:
            # Test violation report endpoint
            violation_url = urljoin(self.base_url, '/csp-violation-report')
            
            # Create test violation
            test_violation = {
                'csp-report': {
                    'document-uri': self.base_url,
                    'violated-directive': 'script-src',
                    'original-policy': 'script-src \'self\'',
                    'blocked-uri': 'https://malicious-site.com/script.js',
                    'source-file': 'https://example.com/page.html',
                    'line-number': 42
                }
            }
            
            response = requests.post(violation_url, json=test_violation)
            
            if response.status_code == 200:
                self.test_results.append({
                    'test': 'Violation Reporting',
                    'status': 'PASS',
                    'details': 'Violation report endpoint working'
                })
            else:
                self.test_results.append({
                    'test': 'Violation Reporting',
                    'status': 'WARN',
                    'details': f'Violation endpoint returned {response.status_code}'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Violation Reporting',
                'status': 'ERROR',
                'details': f'Error testing violation reporting: {str(e)}'
            })
    
    def test_browser_compatibility(self):
        """Test CSP compatibility across browsers"""
        print("🌐 Testing Browser Compatibility...")
        
        # Test with different user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        for user_agent in user_agents:
            try:
                headers = {'User-Agent': user_agent}
                response = requests.get(self.base_url, headers=headers)
                
                if 'Content-Security-Policy' in response.headers:
                    self.test_results.append({
                        'test': f'Browser Compatibility - {user_agent[:50]}...',
                        'status': 'PASS',
                        'details': 'CSP header present'
                    })
                else:
                    self.test_results.append({
                        'test': f'Browser Compatibility - {user_agent[:50]}...',
                        'status': 'WARN',
                        'details': 'CSP header missing'
                    })
                    
            except Exception as e:
                self.test_results.append({
                    'test': f'Browser Compatibility - {user_agent[:50]}...',
                    'status': 'ERROR',
                    'details': f'Error testing: {str(e)}'
                })
    
    def run_selenium_tests(self):
        """Run Selenium-based CSP tests"""
        print("🤖 Running Selenium Tests...")
        
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # Enable CSP violation logging
            chrome_options.add_experimental_option('perfLoggingPrefs', {
                'enableNetwork': True,
                'enablePage': True,
            })
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Navigate to the application
                driver.get(self.base_url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check for CSP violations in console
                logs = driver.get_log('browser')
                csp_violations = [log for log in logs if 'CSP' in log['message']]
                
                if csp_violations:
                    self.test_results.append({
                        'test': 'Selenium CSP Violations',
                        'status': 'WARN',
                        'details': f'Found {len(csp_violations)} CSP violations in browser console'
                    })
                    
                    for violation in csp_violations[:3]:  # Show first 3 violations
                        self.violations.append(violation['message'])
                else:
                    self.test_results.append({
                        'test': 'Selenium CSP Violations',
                        'status': 'PASS',
                        'details': 'No CSP violations detected in browser console'
                    })
                
                # Test page functionality
                self._test_page_functionality(driver)
                
            finally:
                driver.quit()
                
        except WebDriverException as e:
            self.test_results.append({
                'test': 'Selenium Tests',
                'status': 'SKIP',
                'details': f'Selenium not available: {str(e)}'
            })
        except Exception as e:
            self.test_results.append({
                'test': 'Selenium Tests',
                'status': 'ERROR',
                'details': f'Error running Selenium tests: {str(e)}'
            })
    
    def _test_page_functionality(self, driver):
        """Test basic page functionality with CSP enabled"""
        try:
            # Test if page loads without errors
            page_title = driver.title
            if page_title:
                self.test_results.append({
                    'test': 'Page Load',
                    'status': 'PASS',
                    'details': f'Page loaded successfully: {page_title}'
                })
            
            # Test if JavaScript is working
            js_result = driver.execute_script("return document.readyState;")
            if js_result == 'complete':
                self.test_results.append({
                    'test': 'JavaScript Execution',
                    'status': 'PASS',
                    'details': 'JavaScript execution working'
                })
            else:
                self.test_results.append({
                    'test': 'JavaScript Execution',
                    'status': 'WARN',
                    'details': f'Page not fully loaded: {js_result}'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Page Functionality',
                'status': 'ERROR',
                'details': f'Error testing page functionality: {str(e)}'
            })
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        print("=" * 60)
        
        # Count results by status
        status_counts = {}
        for result in self.test_results:
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = status_counts.get('PASS', 0)
        failed_tests = status_counts.get('FAIL', 0)
        warning_tests = status_counts.get('WARN', 0)
        error_tests = status_counts.get('ERROR', 0)
        
        # Calculate score
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'errors': error_tests,
                'score': round(score, 2)
            },
            'results': self.test_results,
            'violations': self.violations,
            'recommendations': self._generate_recommendations()
        }
        
        # Print summary
        print(f"📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warning_tests}")
        print(f"   🔥 Errors: {error_tests}")
        print(f"   📊 Score: {score}%")
        
        # Print recommendations
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for missing CSP header
        csp_header_tests = [r for r in self.test_results if 'CSP Header' in r['test']]
        if any(r['status'] == 'FAIL' for r in csp_header_tests):
            recommendations.append("Implement Content-Security-Policy header")
        
        # Check for unsafe directives
        unsafe_tests = [r for r in self.test_results if 'Unsafe pattern' in r['details']]
        if unsafe_tests:
            recommendations.append("Review and remove unsafe CSP directives")
        
        # Check for inline scripts
        inline_script_tests = [r for r in self.test_results if 'Inline Scripts' in r['test']]
        if any(r['status'] == 'WARN' for r in inline_script_tests):
            recommendations.append("Move inline scripts to external files or use nonces")
        
        # Check for violations
        if self.violations:
            recommendations.append(f"Investigate {len(self.violations)} CSP violations")
        
        # Check for missing security headers
        missing_headers = [r for r in self.test_results if r['status'] == 'WARN' and 'Header' in r['test']]
        if missing_headers:
            recommendations.append("Implement missing security headers")
        
        return recommendations

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSP Test Suite for Mingus Financial App')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--selenium', action='store_true', help='Run Selenium tests')
    parser.add_argument('--output', help='Output file for test results')
    
    args = parser.parse_args()
    
    # Initialize test suite
    test_suite = CSPTestSuite(args.url)
    
    # Run tests
    report = test_suite.run_all_tests()
    
    # Run Selenium tests if requested
    if args.selenium:
        test_suite.run_selenium_tests()
        report = test_suite.generate_report()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Test results saved to {args.output}")
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
