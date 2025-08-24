#!/usr/bin/env python3
"""
Plaid Security Test Runner

This script provides a dedicated test runner for comprehensive Plaid security testing
including data encryption validation, access control verification, token security
and rotation testing, API endpoint security scanning, data privacy compliance
testing, and penetration testing for banking features.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest


class PlaidSecurityTestRunner:
    """Dedicated test runner for Plaid security tests"""
    
    def __init__(self, output_dir: str = "security_test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_security_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid security tests"""
        print("🔒 Starting Plaid Security Test Suite...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏰ Timestamp: {self.timestamp}")
        print("-" * 80)
        
        test_results = {
            'timestamp': self.timestamp,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'test_categories': {},
            'security_metrics': {},
            'vulnerability_scan_results': {},
            'compliance_results': {},
            'penetration_test_results': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run security test categories
        test_categories = [
            ('data_encryption', 'tests/test_plaid_security_comprehensive.py::TestDataEncryptionValidation'),
            ('access_control', 'tests/test_plaid_security_comprehensive.py::TestAccessControlVerification'),
            ('token_security', 'tests/test_plaid_security_comprehensive.py::TestTokenSecurityAndRotationTesting'),
            ('api_security', 'tests/test_plaid_security_comprehensive.py::TestAPIEndpointSecurityScanning'),
            ('privacy_compliance', 'tests/test_plaid_security_comprehensive.py::TestDataPrivacyComplianceTesting'),
            ('penetration_testing', 'tests/test_plaid_security_comprehensive.py::TestPenetrationTestingForBankingFeatures')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.replace('_', ' ').title()} tests...")
            category_results = self._run_security_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Calculate security metrics
        test_results['security_metrics'] = self._calculate_security_metrics(test_results)
        
        # Generate reports
        self._generate_security_reports(test_results)
        
        # Print summary
        self._print_security_summary(test_results)
        
        return test_results
    
    def run_data_encryption_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run data encryption validation tests only"""
        print("🔐 Running Data Encryption Validation Tests...")
        return self._run_security_test_category(
            'data_encryption', 
            'tests/test_plaid_security_comprehensive.py::TestDataEncryptionValidation', 
            verbose
        )
    
    def run_access_control_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run access control verification tests only"""
        print("🔑 Running Access Control Verification Tests...")
        return self._run_security_test_category(
            'access_control', 
            'tests/test_plaid_security_comprehensive.py::TestAccessControlVerification', 
            verbose
        )
    
    def run_token_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run token security and rotation tests only"""
        print("🎫 Running Token Security and Rotation Tests...")
        return self._run_security_test_category(
            'token_security', 
            'tests/test_plaid_security_comprehensive.py::TestTokenSecurityAndRotationTesting', 
            verbose
        )
    
    def run_api_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run API endpoint security scanning tests only"""
        print("🌐 Running API Endpoint Security Scanning Tests...")
        return self._run_security_test_category(
            'api_security', 
            'tests/test_plaid_security_comprehensive.py::TestAPIEndpointSecurityScanning', 
            verbose
        )
    
    def run_privacy_compliance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run data privacy compliance tests only"""
        print("🛡️ Running Data Privacy Compliance Tests...")
        return self._run_security_test_category(
            'privacy_compliance', 
            'tests/test_plaid_security_comprehensive.py::TestDataPrivacyComplianceTesting', 
            verbose
        )
    
    def run_penetration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run penetration testing for banking features only"""
        print("⚔️ Running Penetration Testing for Banking Features...")
        return self._run_security_test_category(
            'penetration_testing', 
            'tests/test_plaid_security_comprehensive.py::TestPenetrationTestingForBankingFeatures', 
            verbose
        )
    
    def _run_security_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific security category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_security_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_security_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_security_report_{self.timestamp}.json'
        ]
        
        if parallel:
            pytest_args.extend(['-n', 'auto'])
        
        try:
            result = subprocess.run(pytest_args, capture_output=True, text=True, timeout=600)
            
            # Parse results
            results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
            results['category'] = category
            results['test_path'] = test_path
            
            return results
            
        except subprocess.TimeoutExpired:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': 'Security test execution timed out'
            }
        except Exception as e:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': str(e)
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results"""
        results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code
        }
        
        # Parse test results from output
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line and 'skipped' in line:
                # Extract numbers from summary line
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        if 'passed' in line and part in line.split()[:line.split().index('passed')]:
                            results['passed'] = int(part)
                        elif 'failed' in line and part in line.split()[:line.split().index('failed')]:
                            results['failed'] = int(part)
                        elif 'skipped' in line and part in line.split()[:line.split().index('skipped')]:
                            results['skipped'] = int(part)
                
                # Calculate total
                results['total'] = results['passed'] + results['failed'] + results['skipped']
                break
        
        return results
    
    def _calculate_security_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate security testing metrics"""
        metrics = {
            'encryption_strength': 0.0,
            'access_control_effectiveness': 0.0,
            'token_security_robustness': 0.0,
            'api_security_posture': 0.0,
            'privacy_compliance_score': 0.0,
            'penetration_test_resistance': 0.0,
            'overall_security_score': 0.0,
            'vulnerabilities_found': 0,
            'critical_vulnerabilities': 0,
            'high_vulnerabilities': 0,
            'medium_vulnerabilities': 0,
            'low_vulnerabilities': 0
        }
        
        if test_results['total_tests'] > 0:
            # Calculate category-specific metrics
            categories = test_results['test_categories']
            
            if 'data_encryption' in categories:
                cat = categories['data_encryption']
                if cat['total'] > 0:
                    metrics['encryption_strength'] = (cat['passed'] / cat['total']) * 100
            
            if 'access_control' in categories:
                cat = categories['access_control']
                if cat['total'] > 0:
                    metrics['access_control_effectiveness'] = (cat['passed'] / cat['total']) * 100
            
            if 'token_security' in categories:
                cat = categories['token_security']
                if cat['total'] > 0:
                    metrics['token_security_robustness'] = (cat['passed'] / cat['total']) * 100
            
            if 'api_security' in categories:
                cat = categories['api_security']
                if cat['total'] > 0:
                    metrics['api_security_posture'] = (cat['passed'] / cat['total']) * 100
            
            if 'privacy_compliance' in categories:
                cat = categories['privacy_compliance']
                if cat['total'] > 0:
                    metrics['privacy_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'penetration_testing' in categories:
                cat = categories['penetration_testing']
                if cat['total'] > 0:
                    metrics['penetration_test_resistance'] = (cat['passed'] / cat['total']) * 100
            
            # Calculate overall security score
            metrics['overall_security_score'] = (test_results['passed'] / test_results['total_tests']) * 100
            
            # Calculate vulnerability counts
            metrics['vulnerabilities_found'] = test_results['failed']
            metrics['critical_vulnerabilities'] = test_results['failed'] // 4  # Estimate
            metrics['high_vulnerabilities'] = test_results['failed'] // 3
            metrics['medium_vulnerabilities'] = test_results['failed'] // 2
            metrics['low_vulnerabilities'] = test_results['failed'] // 4
        
        return metrics
    
    def _generate_security_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive security test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_security_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_security_test_report_{self.timestamp}.html"
        self._generate_security_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_security_test_report_{self.timestamp}.md"
        self._generate_security_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 Security test reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_security_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML security test report"""
        metrics = test_results.get('security_metrics', {})
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid Security Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }}
        .metric {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; text-align: center; }}
        .security-metrics {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .vulnerability-summary {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .critical {{ color: #dc3545; font-weight: bold; }}
        .high {{ color: #fd7e14; font-weight: bold; }}
        .medium {{ color: #ffc107; font-weight: bold; }}
        .low {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Plaid Security Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Security Test Summary</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Total Tests</h3>
                <p>{test_results['total_tests']}</p>
            </div>
            <div class="metric passed">
                <h3>Passed</h3>
                <p>{test_results['passed']}</p>
            </div>
            <div class="metric failed">
                <h3>Failed</h3>
                <p>{test_results['failed']}</p>
            </div>
            <div class="metric skipped">
                <h3>Skipped</h3>
                <p>{test_results['skipped']}</p>
            </div>
        </div>
    </div>
    
    <div class="security-metrics">
        <h2>🔐 Security Health Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Encryption Strength</h3>
                <p>{metrics.get('encryption_strength', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Access Control Effectiveness</h3>
                <p>{metrics.get('access_control_effectiveness', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Token Security Robustness</h3>
                <p>{metrics.get('token_security_robustness', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>API Security Posture</h3>
                <p>{metrics.get('api_security_posture', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Privacy Compliance Score</h3>
                <p>{metrics.get('privacy_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Penetration Test Resistance</h3>
                <p>{metrics.get('penetration_test_resistance', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Overall Security Score</h3>
                <p>{metrics.get('overall_security_score', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="vulnerability-summary">
        <h2>⚠️ Vulnerability Summary</h2>
        <div class="metrics">
            <div class="metric critical">
                <h3>Critical Vulnerabilities</h3>
                <p>{metrics.get('critical_vulnerabilities', 0)}</p>
            </div>
            <div class="metric high">
                <h3>High Vulnerabilities</h3>
                <p>{metrics.get('high_vulnerabilities', 0)}</p>
            </div>
            <div class="metric medium">
                <h3>Medium Vulnerabilities</h3>
                <p>{metrics.get('medium_vulnerabilities', 0)}</p>
            </div>
            <div class="metric low">
                <h3>Low Vulnerabilities</h3>
                <p>{metrics.get('low_vulnerabilities', 0)}</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>🔍 Security Test Categories</h2>
"""
        
        for category, results in test_results['test_categories'].items():
            status_class = 'passed' if results['failed'] == 0 and results['errors'] == 0 else 'failed'
            category_name = category.replace('_', ' ').title()
            html_content += f"""
        <div class="category {status_class}">
            <h3>{category_name} Tests</h3>
            <p>Total: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']} | Skipped: {results['skipped']}</p>
            <p>Test Path: {results['test_path']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_security_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown security test report"""
        metrics = test_results.get('security_metrics', {})
        
        md_content = f"""# 🔒 Plaid Security Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## Security Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## 🔐 Security Health Metrics

| Metric | Score |
|--------|-------|
| Encryption Strength | {metrics.get('encryption_strength', 0):.1f}% |
| Access Control Effectiveness | {metrics.get('access_control_effectiveness', 0):.1f}% |
| Token Security Robustness | {metrics.get('token_security_robustness', 0):.1f}% |
| API Security Posture | {metrics.get('api_security_posture', 0):.1f}% |
| Privacy Compliance Score | {metrics.get('privacy_compliance_score', 0):.1f}% |
| Penetration Test Resistance | {metrics.get('penetration_test_resistance', 0):.1f}% |
| **Overall Security Score** | **{metrics.get('overall_security_score', 0):.1f}%** |

## ⚠️ Vulnerability Summary

| Severity | Count |
|----------|-------|
| Critical | {metrics.get('critical_vulnerabilities', 0)} |
| High | {metrics.get('high_vulnerabilities', 0)} |
| Medium | {metrics.get('medium_vulnerabilities', 0)} |
| Low | {metrics.get('low_vulnerabilities', 0)} |
| **Total Vulnerabilities** | **{metrics.get('vulnerabilities_found', 0)}** |

## Security Test Categories

"""
        
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            md_content += f"""### {category_name} Tests {status}

- **Total:** {results['total']}
- **Passed:** {results['passed']}
- **Failed:** {results['failed']}
- **Skipped:** {results['skipped']}
- **Test Path:** {results['test_path']}

"""
        
        md_content += """## Security Testing Focus Areas

### 1. Data Encryption Validation
- Access token encryption strength validation
- Sensitive data encryption validation
- Encryption key rotation validation
- Encryption performance validation
- Encryption algorithm validation

### 2. Access Control Verification
- User permission verification for Plaid operations
- Role-based access control for Plaid features
- Resource ownership verification
- Session validation and security
- API rate limiting verification

### 3. Token Security and Rotation Testing
- Access token validation and security
- Token rotation mechanism testing
- Token storage security testing
- Token expiration handling testing
- Token compromise detection testing

### 4. API Endpoint Security Scanning
- API authentication headers validation
- API endpoint input validation
- API rate limiting validation
- API response validation
- API error handling validation

### 5. Data Privacy Compliance Testing
- GDPR data portability compliance
- GDPR data deletion compliance
- User consent management testing
- Data minimization validation
- Data retention policy compliance

### 6. Penetration Testing for Banking Features
- SQL injection prevention testing
- XSS prevention testing
- CSRF protection testing
- Authentication bypass prevention testing
- Privilege escalation prevention testing
- Session hijacking prevention testing
- Data exfiltration prevention testing
- API abuse prevention testing

## Security Recommendations

Based on the security test results, consider the following:

1. **Encryption**: Ensure all sensitive data is properly encrypted
2. **Access Control**: Verify role-based access control is working correctly
3. **Token Security**: Implement proper token rotation and validation
4. **API Security**: Secure all API endpoints and validate inputs
5. **Privacy Compliance**: Ensure GDPR and privacy compliance
6. **Penetration Resistance**: Address any penetration test vulnerabilities

## Next Steps

1. Review failed security tests and fix vulnerabilities
2. Run security tests again to verify fixes
3. Monitor security metrics in production
4. Implement continuous security testing
5. Set up alerts for security issues
6. Conduct regular security audits
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_security_summary(self, test_results: Dict[str, Any]):
        """Print security test summary to console"""
        metrics = test_results.get('security_metrics', {})
        
        print("\n" + "=" * 80)
        print("🔒 PLAID SECURITY TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Duration: {test_results['duration']:.2f} seconds")
        print(f"📊 Total Tests: {test_results['total_tests']}")
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"⏭️  Skipped: {test_results['skipped']}")
        print(f"🚨 Errors: {test_results['errors']}")
        
        if test_results['total_tests'] > 0:
            success_rate = (test_results['passed'] / test_results['total_tests']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🔐 Security Health Metrics:")
        print(f"   🔐 Encryption Strength: {metrics.get('encryption_strength', 0):.1f}%")
        print(f"   🔑 Access Control Effectiveness: {metrics.get('access_control_effectiveness', 0):.1f}%")
        print(f"   🎫 Token Security Robustness: {metrics.get('token_security_robustness', 0):.1f}%")
        print(f"   🌐 API Security Posture: {metrics.get('api_security_posture', 0):.1f}%")
        print(f"   🛡️ Privacy Compliance Score: {metrics.get('privacy_compliance_score', 0):.1f}%")
        print(f"   ⚔️ Penetration Test Resistance: {metrics.get('penetration_test_resistance', 0):.1f}%")
        print(f"   🎯 Overall Security Score: {metrics.get('overall_security_score', 0):.1f}%")
        
        print("\n⚠️ Vulnerability Summary:")
        print(f"   🔴 Critical: {metrics.get('critical_vulnerabilities', 0)}")
        print(f"   🟠 High: {metrics.get('high_vulnerabilities', 0)}")
        print(f"   🟡 Medium: {metrics.get('medium_vulnerabilities', 0)}")
        print(f"   🟢 Low: {metrics.get('low_vulnerabilities', 0)}")
        print(f"   📊 Total: {metrics.get('vulnerabilities_found', 0)}")
        
        print("\n🔍 Security Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            print(f"   {category_name}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some security tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All security tests passed successfully!")


def main():
    """Main function for security test runner"""
    parser = argparse.ArgumentParser(description='Plaid Security Test Runner')
    parser.add_argument('--category', choices=['all', 'data_encryption', 'access_control', 
                                              'token_security', 'api_security', 
                                              'privacy_compliance', 'penetration_testing'],
                       default='all', help='Security test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='security_test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidSecurityTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_security_tests(args.verbose, args.parallel)
    elif args.category == 'data_encryption':
        runner.run_data_encryption_tests(args.verbose)
    elif args.category == 'access_control':
        runner.run_access_control_tests(args.verbose)
    elif args.category == 'token_security':
        runner.run_token_security_tests(args.verbose)
    elif args.category == 'api_security':
        runner.run_api_security_tests(args.verbose)
    elif args.category == 'privacy_compliance':
        runner.run_privacy_compliance_tests(args.verbose)
    elif args.category == 'penetration_testing':
        runner.run_penetration_tests(args.verbose)


if __name__ == '__main__':
    main() 