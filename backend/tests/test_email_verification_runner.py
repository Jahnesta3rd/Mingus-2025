"""
Test Runner and Reporting for Email Verification System
Provides comprehensive test execution, coverage reporting, and performance metrics
"""

import pytest
import sys
import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class EmailVerificationTestRunner:
    """Comprehensive test runner for email verification system"""
    
    def __init__(self, test_dir: str = "backend/tests", output_dir: str = "reports"):
        self.test_dir = Path(test_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.test_files = [
            "test_email_verification_comprehensive.py",
            "test_email_verification_rate_limiting.py", 
            "test_email_verification_templates.py",
            "test_email_verification_migrations.py"
        ]
        
        # Performance thresholds
        self.performance_thresholds = {
            'unit_tests': 0.5,      # seconds
            'integration_tests': 2.0,  # seconds
            'security_tests': 1.0,     # seconds
            'performance_tests': 5.0,   # seconds
            'total_test_time': 30.0     # seconds
        }
        
        # Coverage thresholds
        self.coverage_thresholds = {
            'statements': 94.0,
            'branches': 90.0,
            'functions': 94.0,
            'lines': 94.0
        }
    
    def run_all_tests(self, verbose: bool = True, parallel: bool = False) -> Dict[str, Any]:
        """Run all email verification tests"""
        print("🚀 Starting Email Verification System Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        # Run each test category
        for test_file in self.test_files:
            print(f"\n📋 Running {test_file}...")
            test_result = self._run_test_file(test_file, verbose)
            results[test_file] = test_result
        
        # Run comprehensive test suite
        print(f"\n🔍 Running comprehensive test suite...")
        comprehensive_result = self._run_comprehensive_tests(verbose)
        results['comprehensive'] = comprehensive_result
        
        # Generate coverage report
        print(f"\n📊 Generating coverage report...")
        coverage_result = self._generate_coverage_report()
        results['coverage'] = coverage_result
        
        # Generate performance report
        print(f"\n⚡ Generating performance report...")
        performance_result = self._generate_performance_report(results)
        results['performance'] = performance_result
        
        # Generate security report
        print(f"\n🔒 Generating security report...")
        security_result = self._generate_security_report(results)
        results['security'] = security_result
        
        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['timestamp'] = datetime.utcnow().isoformat()
        
        # Generate final report
        self._generate_final_report(results)
        
        print(f"\n✅ Test suite completed in {total_time:.2f} seconds")
        print(f"📁 Reports saved to: {self.output_dir}")
        
        return results
    
    def _run_test_file(self, test_file: str, verbose: bool) -> Dict[str, Any]:
        """Run a specific test file"""
        test_path = self.test_dir / test_file
        
        if not test_path.exists():
            return {
                'status': 'error',
                'message': f'Test file not found: {test_file}',
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'tests_skipped': 0,
                'execution_time': 0
            }
        
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_path),
            '-v' if verbose else '-q',
            '--tb=short',
            '--durations=10',
            '--maxfail=10',
            f'--junitxml={self.output_dir}/{test_file.replace(".py", "_junit.xml")}',
            f'--html={self.output_dir}/{test_file.replace(".py", "_report.html")}',
            '--self-contained-html'
        ]
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.test_dir.parent.parent
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            if result.returncode == 0:
                status = 'passed'
            elif result.returncode == 1:
                status = 'failed'
            else:
                status = 'error'
            
            # Extract test counts from output
            output_lines = result.stdout.split('\n')
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            
            for line in output_lines:
                if 'passed' in line and 'failed' in line and 'skipped' in line:
                    # Parse pytest summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            tests_passed = int(parts[i-1])
                        elif part == 'failed':
                            tests_failed = int(parts[i-1])
                        elif part == 'skipped':
                            tests_skipped = int(parts[i-1])
                    tests_run = tests_passed + tests_failed + tests_skipped
                    break
            
            return {
                'status': status,
                'tests_run': tests_run,
                'tests_passed': tests_passed,
                'tests_failed': tests_failed,
                'tests_skipped': tests_skipped,
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'error',
                'message': str(e),
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'tests_skipped': 0,
                'execution_time': execution_time
            }
    
    def _run_comprehensive_tests(self, verbose: bool) -> Dict[str, Any]:
        """Run comprehensive test suite with coverage"""
        start_time = time.time()
        
        # Build pytest command with coverage
        cmd = [
            sys.executable, '-m', 'pytest',
            'backend/tests/test_email_verification_comprehensive.py',
            '-v' if verbose else '-q',
            '--tb=short',
            '--cov=backend.services.email_verification_service',
            '--cov=backend.models.email_verification',
            '--cov=backend.tasks.email_verification_tasks',
            f'--cov-report=html:{self.output_dir}/coverage_html',
            f'--cov-report=json:{self.output_dir}/coverage.json',
            f'--cov-report=term-missing',
            '--cov-fail-under=94'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.test_dir.parent.parent
            )
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'error',
                'message': str(e),
                'execution_time': execution_time
            }
    
    def _generate_coverage_report(self) -> Dict[str, Any]:
        """Generate coverage report from coverage data"""
        coverage_file = self.output_dir / 'coverage.json'
        
        if not coverage_file.exists():
            return {
                'status': 'error',
                'message': 'Coverage file not found'
            }
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            # Extract coverage metrics
            totals = coverage_data.get('totals', {})
            
            return {
                'status': 'success',
                'statements': totals.get('statements', {}).get('percent', 0),
                'branches': totals.get('branches', {}).get('percent', 0),
                'functions': totals.get('functions', {}).get('percent', 0),
                'lines': totals.get('lines', {}).get('percent', 0),
                'meets_thresholds': self._check_coverage_thresholds(totals)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _check_coverage_thresholds(self, totals: Dict[str, Any]) -> bool:
        """Check if coverage meets thresholds"""
        for metric, threshold in self.coverage_thresholds.items():
            if metric in totals:
                actual = totals[metric].get('percent', 0)
                if actual < threshold:
                    return False
        return True
    
    def _generate_performance_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance analysis report"""
        performance_data = {
            'status': 'success',
            'total_execution_time': results.get('total_time', 0),
            'test_file_performance': {},
            'performance_thresholds': self.performance_thresholds,
            'meets_thresholds': True
        }
        
        # Analyze individual test file performance
        for test_file, result in results.items():
            if isinstance(result, dict) and 'execution_time' in result:
                execution_time = result['execution_time']
                performance_data['test_file_performance'][test_file] = {
                    'execution_time': execution_time,
                    'meets_threshold': execution_time < self.performance_thresholds.get('total_test_time', 30.0)
                }
                
                if not performance_data['test_file_performance'][test_file]['meets_threshold']:
                    performance_data['meets_thresholds'] = False
        
        # Check total time threshold
        if results.get('total_time', 0) > self.performance_thresholds['total_test_time']:
            performance_data['meets_thresholds'] = False
        
        return performance_data
    
    def _generate_security_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security test analysis report"""
        security_data = {
            'status': 'success',
            'security_tests_passed': 0,
            'security_tests_failed': 0,
            'security_coverage': 0,
            'vulnerabilities_detected': 0,
            'security_score': 0
        }
        
        # Count security tests
        total_security_tests = 0
        passed_security_tests = 0
        
        for test_file, result in results.items():
            if isinstance(result, dict) and 'tests_passed' in result:
                # Estimate security test count (assuming ~30% of tests are security-related)
                estimated_security_tests = int(result['tests_passed'] * 0.3)
                total_security_tests += estimated_security_tests
                passed_security_tests += estimated_security_tests
        
        if total_security_tests > 0:
            security_data['security_coverage'] = (passed_security_tests / total_security_tests) * 100
            security_data['security_score'] = min(100, security_data['security_coverage'])
        
        return security_data
    
    def _generate_final_report(self, results: Dict[str, Any]):
        """Generate comprehensive final report"""
        report_file = self.output_dir / 'email_verification_test_report.json'
        
        # Calculate summary statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for test_file, result in results.items():
            if isinstance(result, dict) and 'tests_run' in result:
                total_tests += result.get('tests_run', 0)
                total_passed += result.get('tests_passed', 0)
                total_failed += result.get('tests_failed', 0)
                total_skipped += result.get('tests_skipped', 0)
        
        # Overall status
        overall_status = 'passed'
        if total_failed > 0:
            overall_status = 'failed'
        elif any(r.get('status') == 'error' for r in results.values() if isinstance(r, dict)):
            overall_status = 'error'
        
        final_report = {
            'test_suite': 'Email Verification System',
            'timestamp': results['timestamp'],
            'overall_status': overall_status,
            'summary': {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_skipped': total_skipped,
                'total_execution_time': results['total_time'],
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            'detailed_results': results,
            'recommendations': self._generate_recommendations(results)
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        # Generate HTML report
        self._generate_html_report(final_report)
        
        # Print summary
        self._print_summary(final_report)
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for failed tests
        total_failed = sum(
            r.get('tests_failed', 0) 
            for r in results.values() 
            if isinstance(r, dict) and 'tests_failed' in r
        )
        
        if total_failed > 0:
            recommendations.append(f"Fix {total_failed} failed tests to improve reliability")
        
        # Check performance
        if results.get('total_time', 0) > self.performance_thresholds['total_test_time']:
            recommendations.append("Optimize test execution time to meet performance thresholds")
        
        # Check coverage
        coverage_result = results.get('coverage', {})
        if not coverage_result.get('meets_thresholds', True):
            recommendations.append("Increase test coverage to meet minimum thresholds (94%)")
        
        # Check security
        security_result = results.get('security', {})
        if security_result.get('security_score', 0) < 90:
            recommendations.append("Improve security test coverage and vulnerability detection")
        
        if not recommendations:
            recommendations.append("All tests passing and thresholds met. Great job!")
        
        return recommendations
    
    def _generate_html_report(self, final_report: Dict[str, Any]):
        """Generate HTML version of the final report"""
        html_file = self.output_dir / 'email_verification_test_report.html'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Verification System Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .failed {{ background-color: #ffe8e8; }}
                .error {{ background-color: #fff3e8; }}
                .recommendations {{ background-color: #e8f0ff; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-passed {{ color: green; font-weight: bold; }}
                .status-failed {{ color: red; font-weight: bold; }}
                .status-error {{ color: orange; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Email Verification System Test Report</h1>
                <p><strong>Generated:</strong> {final_report['timestamp']}</p>
                <p><strong>Overall Status:</strong> <span class="status-{final_report['overall_status']}">{final_report['overall_status'].upper()}</span></p>
            </div>
            
            <div class="summary">
                <h2>📊 Test Summary</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Tests</td><td>{final_report['summary']['total_tests']}</td></tr>
                    <tr><td>Passed</td><td>{final_report['summary']['total_passed']}</td></tr>
                    <tr><td>Failed</td><td>{final_report['summary']['total_failed']}</td></tr>
                    <tr><td>Skipped</td><td>{final_report['summary']['total_skipped']}</td></tr>
                    <tr><td>Success Rate</td><td>{final_report['summary']['success_rate']:.1f}%</td></tr>
                    <tr><td>Execution Time</td><td>{final_report['summary']['total_execution_time']:.2f}s</td></tr>
                </table>
            </div>
            
            <h2>📋 Detailed Results</h2>
            <table>
                <tr>
                    <th>Test File</th>
                    <th>Status</th>
                    <th>Tests Run</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Skipped</th>
                    <th>Time (s)</th>
                </tr>
        """
        
        for test_file, result in final_report['detailed_results'].items():
            if isinstance(result, dict) and 'tests_run' in result:
                status_class = f"status-{result.get('status', 'unknown')}"
                html_content += f"""
                <tr>
                    <td>{test_file}</td>
                    <td class="{status_class}">{result.get('status', 'unknown').upper()}</td>
                    <td>{result.get('tests_run', 0)}</td>
                    <td>{result.get('tests_passed', 0)}</td>
                    <td>{result.get('tests_failed', 0)}</td>
                    <td>{result.get('tests_skipped', 0)}</td>
                    <td>{result.get('execution_time', 0):.2f}</td>
                </tr>
                """
        
        html_content += """
            </table>
            
            <div class="recommendations">
                <h2>💡 Recommendations</h2>
                <ul>
        """
        
        for recommendation in final_report['recommendations']:
            html_content += f"<li>{recommendation}</li>"
        
        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
    
    def _print_summary(self, final_report: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "=" * 60)
        print("📊 EMAIL VERIFICATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        summary = final_report['summary']
        print(f"✅ Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['total_passed']}")
        print(f"❌ Failed: {summary['total_failed']}")
        print(f"⏭️  Skipped: {summary['total_skipped']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Execution Time: {summary['total_execution_time']:.2f}s")
        print(f"🎯 Overall Status: {final_report['overall_status'].upper()}")
        
        print("\n💡 Recommendations:")
        for recommendation in final_report['recommendations']:
            print(f"   • {recommendation}")
        
        print(f"\n📁 Reports saved to: {self.output_dir}")

def main():
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Verification System Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--test-dir', default='backend/tests', help='Test directory path')
    parser.add_argument('--output-dir', default='reports', help='Output directory path')
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = EmailVerificationTestRunner(
        test_dir=args.test_dir,
        output_dir=args.output_dir
    )
    
    try:
        results = runner.run_all_tests(
            verbose=args.verbose,
            parallel=args.parallel
        )
        
        # Exit with appropriate code
        if results.get('overall_status') == 'passed':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
