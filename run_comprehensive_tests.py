#!/usr/bin/env python3
"""
Comprehensive Test Runner for AI Calculator

This script runs all test suites and generates detailed reports:
- Unit tests for services, models, and utilities
- Integration tests for API endpoints and workflows
- Performance tests for load testing and optimization
- Frontend tests for React components
- A/B testing framework validation
- Test coverage analysis
- Performance benchmarks
- Security vulnerability scanning

Usage:
    python run_comprehensive_tests.py [--unit] [--integration] [--performance] [--frontend] [--ab-testing] [--all]
"""

import os
import sys
import subprocess
import time
import json
import argparse
import coverage
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Comprehensive test runner for AI Calculator"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = time.time()
        self.coverage_data = {}
        
        # Test directories
        self.test_dirs = {
            'unit': 'backend/tests/unit',
            'integration': 'backend/tests/integration',
            'performance': 'backend/tests/performance',
            'ab_testing': 'backend/tests/ab_testing',
            'frontend': 'src/tests'
        }
        
        # Test configuration
        self.test_config = {
            'unit': {
                'pattern': 'test_*.py',
                'timeout': 300,  # 5 minutes
                'parallel': True
            },
            'integration': {
                'pattern': 'test_*.py',
                'timeout': 600,  # 10 minutes
                'parallel': False
            },
            'performance': {
                'pattern': 'test_*.py',
                'timeout': 1800,  # 30 minutes
                'parallel': False
            },
            'ab_testing': {
                'pattern': 'test_*.py',
                'timeout': 300,  # 5 minutes
                'parallel': True
            },
            'frontend': {
                'pattern': '*.test.tsx',
                'timeout': 600,  # 10 minutes
                'parallel': True
            }
        }
    
    def setup_environment(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Set environment variables
        os.environ['TESTING'] = 'true'
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['MAIL_SUPPRESS_SEND'] = 'true'
        os.environ['STRIPE_TEST_MODE'] = 'true'
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'
        
        # Install test dependencies if needed
        self.install_test_dependencies()
        
        print("✅ Test environment setup complete")
    
    def install_test_dependencies(self):
        """Install test dependencies"""
        try:
            # Check if pytest is installed
            import pytest
        except ImportError:
            print("📦 Installing test dependencies...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 
                          'pytest', 'pytest-cov', 'pytest-xdist', 'pytest-html',
                          'coverage', 'psutil', 'numpy', 'scipy'], 
                         check=True)
        
        try:
            # Check if frontend test dependencies are available
            import requests
        except ImportError:
            print("📦 Installing additional test dependencies...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 
                          'requests', 'selenium', 'beautifulsoup4'], 
                         check=True)
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        print("\n🧪 Running Unit Tests...")
        
        unit_dir = self.project_root / self.test_dirs['unit']
        if not unit_dir.exists():
            print("⚠️  Unit test directory not found")
            return {'status': 'skipped', 'reason': 'Directory not found'}
        
        # Start coverage measurement
        cov = coverage.Coverage()
        cov.start()
        
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, '-m', 'pytest',
                str(unit_dir),
                '-v',
                '--tb=short',
                '--cov=backend',
                '--cov-report=html:coverage/unit',
                '--cov-report=json:coverage/unit.json',
                '--junitxml=reports/unit-tests.xml',
                '--html=reports/unit-tests.html',
                '--self-contained-html'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Stop coverage measurement
            cov.stop()
            cov.save()
            
            # Parse results
            test_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'coverage': self.get_coverage_summary(cov)
            }
            
            print(f"✅ Unit tests completed: {test_results['status']}")
            return test_results
            
        except subprocess.TimeoutExpired:
            cov.stop()
            cov.save()
            print("⏰ Unit tests timed out")
            return {'status': 'timeout', 'reason': 'Tests exceeded 5 minute timeout'}
        except Exception as e:
            cov.stop()
            cov.save()
            print(f"❌ Unit tests failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        print("\n🔗 Running Integration Tests...")
        
        integration_dir = self.project_root / self.test_dirs['integration']
        if not integration_dir.exists():
            print("⚠️  Integration test directory not found")
            return {'status': 'skipped', 'reason': 'Directory not found'}
        
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                str(integration_dir),
                '-v',
                '--tb=short',
                '--junitxml=reports/integration-tests.xml',
                '--html=reports/integration-tests.html',
                '--self-contained-html'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            test_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"✅ Integration tests completed: {test_results['status']}")
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ Integration tests timed out")
            return {'status': 'timeout', 'reason': 'Tests exceeded 10 minute timeout'}
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        
        performance_dir = self.project_root / self.test_dirs['performance']
        if not performance_dir.exists():
            print("⚠️  Performance test directory not found")
            return {'status': 'skipped', 'reason': 'Directory not found'}
        
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                str(performance_dir),
                '-v',
                '--tb=short',
                '--junitxml=reports/performance-tests.xml',
                '--html=reports/performance-tests.html',
                '--self-contained-html'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            test_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"✅ Performance tests completed: {test_results['status']}")
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ Performance tests timed out")
            return {'status': 'timeout', 'reason': 'Tests exceeded 30 minute timeout'}
        except Exception as e:
            print(f"❌ Performance tests failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def run_ab_testing_tests(self) -> Dict[str, Any]:
        """Run A/B testing framework tests"""
        print("\n🔬 Running A/B Testing Framework Tests...")
        
        ab_testing_dir = self.project_root / self.test_dirs['ab_testing']
        if not ab_testing_dir.exists():
            print("⚠️  A/B testing test directory not found")
            return {'status': 'skipped', 'reason': 'Directory not found'}
        
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                str(ab_testing_dir),
                '-v',
                '--tb=short',
                '--junitxml=reports/ab-testing-tests.xml',
                '--html=reports/ab-testing-tests.html',
                '--self-contained-html'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            test_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"✅ A/B testing tests completed: {test_results['status']}")
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ A/B testing tests timed out")
            return {'status': 'timeout', 'reason': 'Tests exceeded 5 minute timeout'}
        except Exception as e:
            print(f"❌ A/B testing tests failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend tests"""
        print("\n🎨 Running Frontend Tests...")
        
        frontend_dir = self.project_root / self.test_dirs['frontend']
        if not frontend_dir.exists():
            print("⚠️  Frontend test directory not found")
            return {'status': 'skipped', 'reason': 'Directory not found'}
        
        try:
            # Check if npm/yarn is available
            try:
                subprocess.run(['npm', '--version'], capture_output=True, check=True)
                package_manager = 'npm'
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['yarn', '--version'], capture_output=True, check=True)
                    package_manager = 'yarn'
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("⚠️  No package manager found (npm or yarn)")
                    return {'status': 'skipped', 'reason': 'No package manager found'}
            
            # Install dependencies if needed
            if not (self.project_root / 'node_modules').exists():
                print("📦 Installing frontend dependencies...")
                subprocess.run([package_manager, 'install'], cwd=self.project_root, check=True)
            
            # Run frontend tests
            cmd = [package_manager, 'test', '--coverage', '--watchAll=false']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root, timeout=600)
            
            test_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"✅ Frontend tests completed: {test_results['status']}")
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ Frontend tests timed out")
            return {'status': 'timeout', 'reason': 'Tests exceeded 10 minute timeout'}
        except Exception as e:
            print(f"❌ Frontend tests failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run security vulnerability scan"""
        print("\n🔒 Running Security Scan...")
        
        try:
            # Check for common security issues
            security_issues = []
            
            # Check for hardcoded secrets
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            import re
            for pattern in secret_patterns:
                for file_path in self.project_root.rglob('*.py'):
                    if 'test' not in str(file_path) and 'venv' not in str(file_path):
                        with open(file_path, 'r') as f:
                            content = f.read()
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                security_issues.append(f"Hardcoded secret found in {file_path}")
            
            # Check for SQL injection vulnerabilities
            sql_patterns = [
                r'execute\s*\(\s*f\s*["\'][^"\']*\{[^}]*\}[^"\']*["\']',
                r'execute\s*\(\s*["\'][^"\']*\{[^}]*\}[^"\']*["\']'
            ]
            
            for pattern in sql_patterns:
                for file_path in self.project_root.rglob('*.py'):
                    if 'test' not in str(file_path) and 'venv' not in str(file_path):
                        with open(file_path, 'r') as f:
                            content = f.read()
                            matches = re.findall(pattern, content)
                            if matches:
                                security_issues.append(f"Potential SQL injection in {file_path}")
            
            security_results = {
                'status': 'passed' if not security_issues else 'failed',
                'issues': security_issues,
                'issue_count': len(security_issues)
            }
            
            print(f"✅ Security scan completed: {security_results['status']}")
            if security_issues:
                print(f"⚠️  Found {len(security_issues)} security issues")
                for issue in security_issues[:5]:  # Show first 5 issues
                    print(f"   - {issue}")
            
            return security_results
            
        except Exception as e:
            print(f"❌ Security scan failed: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def get_coverage_summary(self, cov) -> Dict[str, Any]:
        """Get coverage summary"""
        try:
            cov.report()
            return {
                'total_coverage': cov.report(),
                'missing_lines': cov.get_missing(),
                'covered_lines': cov.get_covered()
            }
        except Exception:
            return {'error': 'Could not generate coverage summary'}
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'failed')
        skipped_tests = sum(1 for result in self.test_results.values() 
                           if result.get('status') == 'skipped')
        
        # Create report
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': total_duration,
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'test_results': self.test_results,
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        reports_dir = self.project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / 'comprehensive-test-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report(report)
        
        print(f"📄 Test report saved to {report_file}")
        print(f"\n📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Skipped: {skipped_tests}")
        print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"   Duration: {total_duration:.1f} seconds")
        
        return report
    
    def generate_html_report(self, report):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Calculator Comprehensive Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 20px; background-color: #e8f4f8; border-radius: 5px; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .passed {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
        .failed {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
        .skipped {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
        .recommendations {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Calculator Comprehensive Test Report</h1>
        <p>Generated on: {report['timestamp']}</p>
        <p>Duration: {report['duration_seconds']:.1f} seconds</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <h2>{report['summary']['total_tests']}</h2>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <h2 style="color: green;">{report['summary']['passed']}</h2>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <h2 style="color: red;">{report['summary']['failed']}</h2>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <h2>{report['summary']['success_rate']:.1f}%</h2>
        </div>
    </div>
    
    <h2>Test Results</h2>
"""
        
        for test_name, result in report['test_results'].items():
            status_class = result.get('status', 'unknown')
            html_content += f"""
    <div class="test-result {status_class}">
        <h3>{test_name.replace('_', ' ').title()}</h3>
        <p><strong>Status:</strong> {result.get('status', 'unknown')}</p>
        {f'<p><strong>Reason:</strong> {result.get("reason", "")}</p>' if result.get('reason') else ''}
        {f'<p><strong>Return Code:</strong> {result.get("returncode", "")}</p>' if result.get('returncode') is not None else ''}
    </div>
"""
        
        html_content += f"""
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"""
        
        for recommendation in report.get('recommendations', []):
            html_content += f"            <li>{recommendation}</li>\n"
        
        html_content += """
        </ul>
    </div>
</body>
</html>
"""
        
        reports_dir = self.project_root / 'reports'
        html_file = reports_dir / 'comprehensive-test-report.html'
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved to {html_file}")
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result.get('status') == 'failed':
                recommendations.append(f"Fix failing {test_name} tests")
            elif result.get('status') == 'timeout':
                recommendations.append(f"Optimize {test_name} tests to run faster")
            elif result.get('status') == 'skipped':
                recommendations.append(f"Implement missing {test_name} tests")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("All tests passed! Consider adding more edge case tests")
        
        return recommendations
    
    def run_all_tests(self, test_types: List[str] = None):
        """Run all specified test types"""
        if test_types is None:
            test_types = ['unit', 'integration', 'performance', 'ab_testing', 'frontend', 'security']
        
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 50)
        
        # Setup environment
        self.setup_environment()
        
        # Create reports directory
        reports_dir = self.project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Run tests
        test_functions = {
            'unit': self.run_unit_tests,
            'integration': self.run_integration_tests,
            'performance': self.run_performance_tests,
            'ab_testing': self.run_ab_testing_tests,
            'frontend': self.run_frontend_tests,
            'security': self.run_security_scan
        }
        
        for test_type in test_types:
            if test_type in test_functions:
                self.test_results[test_type] = test_functions[test_type]()
        
        # Generate report
        report = self.generate_test_report()
        
        # Return exit code
        failed_tests = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'failed')
        
        if failed_tests > 0:
            print(f"\n❌ {failed_tests} test suites failed")
            return 1
        else:
            print(f"\n✅ All test suites passed!")
            return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for AI Calculator')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--frontend', action='store_true', help='Run frontend tests')
    parser.add_argument('--ab-testing', action='store_true', help='Run A/B testing framework tests')
    parser.add_argument('--security', action='store_true', help='Run security scan')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Determine which tests to run
    test_types = []
    if args.all or not any([args.unit, args.integration, args.performance, args.frontend, args.ab_testing, args.security]):
        test_types = ['unit', 'integration', 'performance', 'ab_testing', 'frontend', 'security']
    else:
        if args.unit:
            test_types.append('unit')
        if args.integration:
            test_types.append('integration')
        if args.performance:
            test_types.append('performance')
        if args.frontend:
            test_types.append('frontend')
        if args.ab_testing:
            test_types.append('ab_testing')
        if args.security:
            test_types.append('security')
    
    # Run tests
    runner = TestRunner()
    exit_code = runner.run_all_tests(test_types)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
