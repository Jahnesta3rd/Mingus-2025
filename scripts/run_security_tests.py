#!/usr/bin/env python3
"""
Security Test Runner for CI/CD Pipeline
Runs comprehensive security tests and generates reports for compliance
"""

import os
import sys
import subprocess
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SecurityTestRunner:
    """Comprehensive security test runner for CI/CD pipeline"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default security test configuration"""
        return {
            'test_paths': [
                'tests/security/',
                'tests/test_comprehensive_security_suite.py'
            ],
            'output_formats': ['xml', 'html', 'json'],
            'fail_on_critical': True,
            'generate_reports': True,
            'coverage_threshold': 80,
            'timeout_minutes': 30,
            'parallel_jobs': 4,
            'verbose': True
        }
    
    def run_security_tests(self) -> bool:
        """Run all security tests and return success status"""
        print("🔒 Starting Comprehensive Security Test Suite")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        try:
            # Run different types of security tests
            test_results = {
                'input_validation': self._run_input_validation_tests(),
                'jwt_security': self._run_jwt_security_tests(),
                'rate_limiting': self._run_rate_limiting_tests(),
                'csrf_protection': self._run_csrf_protection_tests(),
                'security_headers': self._run_security_headers_tests(),
                'penetration_tests': self._run_penetration_tests(),
                'data_protection': self._run_data_protection_tests(),
                'static_analysis': self._run_static_analysis(),
                'dependency_scanning': self._run_dependency_scanning()
            }
            
            self.test_results = test_results
            self.end_time = datetime.now()
            
            # Generate comprehensive report
            if self.config['generate_reports']:
                self._generate_security_report()
            
            # Check for critical failures
            critical_failures = self._check_critical_failures()
            
            if critical_failures and self.config['fail_on_critical']:
                print(f"❌ Critical security test failures detected: {len(critical_failures)}")
                for failure in critical_failures:
                    print(f"   - {failure}")
                return False
            
            print("✅ All security tests completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Security test execution failed: {str(e)}")
            return False
    
    def _run_input_validation_tests(self) -> Dict[str, Any]:
        """Run input validation security tests"""
        print("\n🔍 Running Input Validation Security Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestInputValidation',
            '--tb=short',
            '-v',
            '--junit-xml=reports/input_validation_results.xml',
            '--html=reports/input_validation_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_jwt_security_tests(self) -> Dict[str, Any]:
        """Run JWT security tests"""
        print("🔐 Running JWT Security Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestJWTSecurity',
            '--tb=short',
            '-v',
            '--junit-xml=reports/jwt_security_results.xml',
            '--html=reports/jwt_security_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_rate_limiting_tests(self) -> Dict[str, Any]:
        """Run rate limiting tests"""
        print("⏱️  Running Rate Limiting Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestRateLimiting',
            '--tb=short',
            '-v',
            '--junit-xml=reports/rate_limiting_results.xml',
            '--html=reports/rate_limiting_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_csrf_protection_tests(self) -> Dict[str, Any]:
        """Run CSRF protection tests"""
        print("🛡️  Running CSRF Protection Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestCSRFProtection',
            '--tb=short',
            '-v',
            '--junit-xml=reports/csrf_protection_results.xml',
            '--html=reports/csrf_protection_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_security_headers_tests(self) -> Dict[str, Any]:
        """Run security headers tests"""
        print("📋 Running Security Headers Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestSecurityHeaders',
            '--tb=short',
            '-v',
            '--junit-xml=reports/security_headers_results.xml',
            '--html=reports/security_headers_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_penetration_tests(self) -> Dict[str, Any]:
        """Run penetration testing scenarios"""
        print("⚔️  Running Penetration Testing Scenarios...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestPenetrationScenarios',
            '--tb=short',
            '-v',
            '--junit-xml=reports/penetration_tests_results.xml',
            '--html=reports/penetration_tests_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # Longer timeout for penetration tests
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_data_protection_tests(self) -> Dict[str, Any]:
        """Run data protection tests"""
        print("🔒 Running Data Protection Tests...")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/test_comprehensive_security_suite.py::TestDataProtection',
            '--tb=short',
            '-v',
            '--junit-xml=reports/data_protection_results.xml',
            '--html=reports/data_protection_report.html',
            '--self-contained-html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _run_static_analysis(self) -> Dict[str, Any]:
        """Run static code analysis for security vulnerabilities"""
        print("🔍 Running Static Code Analysis...")
        
        # Run bandit for Python security analysis
        bandit_cmd = [
            sys.executable, '-m', 'bandit',
            '-r', 'backend/',
            '-f', 'json',
            '-o', 'reports/bandit_results.json'
        ]
        
        try:
            bandit_result = subprocess.run(bandit_cmd, capture_output=True, text=True, timeout=300)
            
            # Parse bandit results
            if bandit_result.returncode == 0:
                try:
                    with open('reports/bandit_results.json', 'r') as f:
                        bandit_data = json.load(f)
                    
                    # Check for high severity issues
                    high_severity_issues = [
                        issue for issue in bandit_data.get('results', [])
                        if issue.get('issue_severity') == 'HIGH'
                    ]
                    
                    return {
                        'success': len(high_severity_issues) == 0,
                        'stdout': bandit_result.stdout,
                        'stderr': bandit_result.stderr,
                        'returncode': bandit_result.returncode,
                        'high_severity_issues': len(high_severity_issues),
                        'total_issues': len(bandit_data.get('results', []))
                    }
                except (json.JSONDecodeError, FileNotFoundError):
                    return {
                        'success': False,
                        'stdout': bandit_result.stdout,
                        'stderr': bandit_result.stderr,
                        'returncode': bandit_result.returncode,
                        'error': 'Failed to parse bandit results'
                    }
            else:
                return {
                    'success': False,
                    'stdout': bandit_result.stdout,
                    'stderr': bandit_result.stderr,
                    'returncode': bandit_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Static analysis timed out'
            }
    
    def _run_dependency_scanning(self) -> Dict[str, Any]:
        """Run dependency vulnerability scanning"""
        print("📦 Running Dependency Vulnerability Scan...")
        
        # Run safety for Python dependency scanning
        safety_cmd = [
            sys.executable, '-m', 'safety',
            'check',
            '--json',
            '--output', 'reports/safety_results.json'
        ]
        
        try:
            safety_result = subprocess.run(safety_cmd, capture_output=True, text=True, timeout=300)
            
            # Parse safety results
            if safety_result.returncode == 0:
                try:
                    with open('reports/safety_results.json', 'r') as f:
                        safety_data = json.load(f)
                    
                    # Check for vulnerabilities
                    vulnerabilities = safety_data.get('vulnerabilities', [])
                    high_severity_vulns = [
                        vuln for vuln in vulnerabilities
                        if vuln.get('severity') == 'HIGH'
                    ]
                    
                    return {
                        'success': len(high_severity_vulns) == 0,
                        'stdout': safety_result.stdout,
                        'stderr': safety_result.stderr,
                        'returncode': safety_result.returncode,
                        'high_severity_vulns': len(high_severity_vulns),
                        'total_vulns': len(vulnerabilities)
                    }
                except (json.JSONDecodeError, FileNotFoundError):
                    return {
                        'success': False,
                        'stdout': safety_result.stdout,
                        'stderr': safety_result.stderr,
                        'returncode': safety_result.returncode,
                        'error': 'Failed to parse safety results'
                    }
            else:
                return {
                    'success': False,
                    'stdout': safety_result.stdout,
                    'stderr': safety_result.stderr,
                    'returncode': safety_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Dependency scanning timed out'
            }
    
    def _check_critical_failures(self) -> List[str]:
        """Check for critical security test failures"""
        critical_failures = []
        
        for test_type, result in self.test_results.items():
            if not result.get('success', False):
                critical_failures.append(f"{test_type}: {result.get('error', 'Test failed')}")
        
        return critical_failures
    
    def _generate_security_report(self):
        """Generate comprehensive security test report"""
        print("\n📊 Generating Security Test Report...")
        
        # Create reports directory
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Generate summary report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (self.end_time - self.start_time).total_seconds(),
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results.values() if r.get('success', False)),
                'failed_tests': sum(1 for r in self.test_results.values() if not r.get('success', False)),
                'critical_failures': self._check_critical_failures()
            }
        }
        
        # Save JSON report
        with open('reports/security_test_summary.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(report_data)
        
        # Generate markdown report
        self._generate_markdown_report(report_data)
        
        print(f"📄 Reports generated in: {reports_dir.absolute()}")
    
    def _generate_html_report(self, report_data: Dict[str, Any]):
        """Generate HTML security test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
        .failure {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
        .critical {{ background-color: #f8d7da; border: 2px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Security Test Report</h1>
        <p>Generated: {report_data['timestamp']}</p>
        <p>Duration: {report_data['duration_seconds']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p>Total Tests: {report_data['summary']['total_tests']}</p>
        <p>Passed: {report_data['summary']['passed_tests']}</p>
        <p>Failed: {report_data['summary']['failed_tests']}</p>
        <p>Critical Failures: {len(report_data['summary']['critical_failures'])}</p>
    </div>
    
    <div class="test-results">
        <h2>🧪 Test Results</h2>
"""
        
        for test_type, result in report_data['test_results'].items():
            status_class = 'success' if result.get('success', False) else 'failure'
            if not result.get('success', False):
                status_class = 'critical'
            
            html_content += f"""
        <div class="test-result {status_class}">
            <h3>{test_type.replace('_', ' ').title()}</h3>
            <p>Status: {'✅ PASSED' if result.get('success', False) else '❌ FAILED'}</p>
            {f'<p>Error: {result.get("error", "Unknown error")}</p>' if not result.get('success', False) else ''}
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open('reports/security_test_report.html', 'w') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]):
        """Generate markdown security test report"""
        markdown_content = f"""# Security Test Report

**Generated:** {report_data['timestamp']}  
**Duration:** {report_data['duration_seconds']:.2f} seconds

## Summary

- **Total Tests:** {report_data['summary']['total_tests']}
- **Passed:** {report_data['summary']['passed_tests']}
- **Failed:** {report_data['summary']['failed_tests']}
- **Critical Failures:** {len(report_data['summary']['critical_failures'])}

## Test Results

"""
        
        for test_type, result in report_data['test_results'].items():
            status_icon = "✅" if result.get('success', False) else "❌"
            markdown_content += f"### {test_type.replace('_', ' ').title()}\n"
            markdown_content += f"**Status:** {status_icon} {'PASSED' if result.get('success', False) else 'FAILED'}\n"
            
            if not result.get('success', False):
                markdown_content += f"**Error:** {result.get('error', 'Unknown error')}\n"
            
            markdown_content += "\n"
        
        if report_data['summary']['critical_failures']:
            markdown_content += "## Critical Failures\n\n"
            for failure in report_data['summary']['critical_failures']:
                markdown_content += f"- {failure}\n"
        
        with open('reports/security_test_report.md', 'w') as f:
            f.write(markdown_content)


def main():
    """Main entry point for security test runner"""
    parser = argparse.ArgumentParser(description='Run comprehensive security tests')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--fail-on-critical', action='store_true', default=True,
                       help='Fail deployment if critical security tests fail')
    parser.add_argument('--generate-reports', action='store_true', default=True,
                       help='Generate security test reports')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with command line arguments
    config['fail_on_critical'] = args.fail_on_critical
    config['generate_reports'] = args.generate_reports
    config['verbose'] = args.verbose
    
    # Create and run security test runner
    runner = SecurityTestRunner(config)
    success = runner.run_security_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
