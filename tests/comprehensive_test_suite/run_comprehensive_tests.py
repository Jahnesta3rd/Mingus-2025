#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner

Main test runner script that orchestrates all test suites with proper reporting,
coverage analysis, and CI/CD integration.
"""

import os
import sys
import subprocess
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ComprehensiveTestRunner:
    """Main test runner for comprehensive test suite"""
    
    def __init__(self, args):
        self.args = args
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'coverage': {},
            'performance': {},
            'security': {},
            'summary': {}
        }
        self.failed_tests = []
        self.passed_tests = []
    
    def run_backend_tests(self):
        """Run backend API tests"""
        print("\n" + "="*60)
        print("RUNNING BACKEND API TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_backend_api.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        if self.args.coverage:
            cmd.extend(['--cov=backend', '--cov-report=html', '--cov-report=term'])
        
        if self.args.parallel:
            cmd.extend(['-n', 'auto'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['backend'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Backend tests PASSED")
            self.passed_tests.append('backend')
        else:
            print("❌ Backend tests FAILED")
            self.failed_tests.append('backend')
            print(result.stdout)
            print(result.stderr)
    
    def run_mathematical_accuracy_tests(self):
        """Run mathematical accuracy tests"""
        print("\n" + "="*60)
        print("RUNNING MATHEMATICAL ACCURACY TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_mathematical_accuracy.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        if self.args.coverage:
            cmd.extend(['--cov=backend.services.assessment_scoring_service', '--cov-report=term'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['mathematical_accuracy'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Mathematical accuracy tests PASSED")
            self.passed_tests.append('mathematical_accuracy')
        else:
            print("❌ Mathematical accuracy tests FAILED")
            self.failed_tests.append('mathematical_accuracy')
            print(result.stdout)
            print(result.stderr)
    
    def run_frontend_tests(self):
        """Run frontend component tests"""
        print("\n" + "="*60)
        print("RUNNING FRONTEND COMPONENT TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_frontend_components.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        if self.args.coverage:
            cmd.extend(['--cov=frontend', '--cov-report=html', '--cov-report=term'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['frontend'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Frontend tests PASSED")
            self.passed_tests.append('frontend')
        else:
            print("❌ Frontend tests FAILED")
            self.failed_tests.append('frontend')
            print(result.stdout)
            print(result.stderr)
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        print("\n" + "="*60)
        print("RUNNING END-TO-END TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_e2e_workflows.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        if self.args.parallel:
            cmd.extend(['-n', '2'])  # Limit parallel execution for E2E tests
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['e2e'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ E2E tests PASSED")
            self.passed_tests.append('e2e')
        else:
            print("❌ E2E tests FAILED")
            self.failed_tests.append('e2e')
            print(result.stdout)
            print(result.stderr)
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("\n" + "="*60)
        print("RUNNING PERFORMANCE TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_performance.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['performance'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Performance tests PASSED")
            self.passed_tests.append('performance')
        else:
            print("❌ Performance tests FAILED")
            self.failed_tests.append('performance')
            print(result.stdout)
            print(result.stderr)
    
    def run_security_tests(self):
        """Run security tests"""
        print("\n" + "="*60)
        print("RUNNING SECURITY TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_security.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['security'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Security tests PASSED")
            self.passed_tests.append('security')
        else:
            print("❌ Security tests FAILED")
            self.failed_tests.append('security')
            print(result.stdout)
            print(result.stderr)
    
    def run_analytics_tests(self):
        """Run analytics verification tests"""
        print("\n" + "="*60)
        print("RUNNING ANALYTICS VERIFICATION TESTS")
        print("="*60)
        
        start_time = time.time()
        
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_analytics.py',
            '-v',
            '--tb=short',
            '--durations=10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        self.results['test_suites']['analytics'] = {
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ Analytics tests PASSED")
            self.passed_tests.append('analytics')
        else:
            print("❌ Analytics tests FAILED")
            self.failed_tests.append('analytics')
            print(result.stdout)
            print(result.stderr)
    
    def run_coverage_analysis(self):
        """Run coverage analysis"""
        if not self.args.coverage:
            return
        
        print("\n" + "="*60)
        print("RUNNING COVERAGE ANALYSIS")
        print("="*60)
        
        # Run coverage for backend
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/',
            '--cov=backend',
            '--cov=frontend',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-report=json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse coverage results
        if result.returncode == 0:
            # Extract coverage percentage from output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'TOTAL' in line and '%' in line:
                    coverage_percentage = line.split()[-1].replace('%', '')
                    self.results['coverage']['overall'] = float(coverage_percentage)
                    break
        
        print(result.stdout)
    
    def run_performance_benchmarks(self):
        """Run performance benchmarks"""
        print("\n" + "="*60)
        print("RUNNING PERFORMANCE BENCHMARKS")
        print("="*60)
        
        # Test income comparison performance
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_performance.py::TestDatabaseQueryPerformance::test_income_comparison_performance_target',
            '-v',
            '--tb=short'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.results['performance']['income_comparison'] = 'PASSED (45ms target met)'
        else:
            self.results['performance']['income_comparison'] = 'FAILED (45ms target exceeded)'
        
        # Test page load performance
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_performance.py::TestPageLoadPerformance::test_landing_page_load_speed',
            '-v',
            '--tb=short'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.results['performance']['page_load'] = 'PASSED (3s target met)'
        else:
            self.results['performance']['page_load'] = 'FAILED (3s target exceeded)'
    
    def run_security_scan(self):
        """Run security scan"""
        print("\n" + "="*60)
        print("RUNNING SECURITY SCAN")
        print("="*60)
        
        # Run security tests and collect results
        cmd = [
            'pytest',
            'tests/comprehensive_test_suite/test_security.py',
            '-v',
            '--tb=short',
            '--json-report'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse security results
        security_issues = []
        if result.returncode != 0:
            security_issues.append("Security tests failed")
        
        self.results['security']['issues'] = security_issues
        self.results['security']['scan_completed'] = True
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("GENERATING COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        # Calculate summary statistics
        total_suites = len(self.results['test_suites'])
        passed_suites = len(self.passed_tests)
        failed_suites = len(self.failed_tests)
        
        total_duration = sum(suite['duration'] for suite in self.results['test_suites'].values())
        
        self.results['summary'] = {
            'total_suites': total_suites,
            'passed_suites': passed_suites,
            'failed_suites': failed_suites,
            'success_rate': (passed_suites / total_suites * 100) if total_suites > 0 else 0,
            'total_duration': total_duration,
            'end_time': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print(f"Total Test Suites: {total_suites}")
        print(f"Passed: {passed_suites}")
        print(f"Failed: {failed_suites}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")
        
        if self.args.coverage and 'coverage' in self.results:
            print(f"Coverage: {self.results['coverage'].get('overall', 'N/A')}%")
        
        # Print performance results
        if self.results['performance']:
            print(f"\n⚡ PERFORMANCE RESULTS")
            for test, result in self.results['performance'].items():
                print(f"{test}: {result}")
        
        # Print security results
        if self.results['security']:
            print(f"\n🔒 SECURITY RESULTS")
            if self.results['security']['issues']:
                print("Security issues found:")
                for issue in self.results['security']['issues']:
                    print(f"  - {issue}")
            else:
                print("No security issues found")
        
        # Save report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return overall success
        return len(self.failed_tests) == 0
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print(f"Start Time: {self.results['start_time']}")
        print(f"Coverage Analysis: {'Enabled' if self.args.coverage else 'Disabled'}")
        print(f"Parallel Execution: {'Enabled' if self.args.parallel else 'Disabled'}")
        
        # Run test suites
        self.run_backend_tests()
        self.run_mathematical_accuracy_tests()
        self.run_frontend_tests()
        self.run_e2e_tests()
        self.run_performance_tests()
        self.run_security_tests()
        self.run_analytics_tests()
        
        # Run additional analysis
        self.run_coverage_analysis()
        self.run_performance_benchmarks()
        self.run_security_scan()
        
        # Generate report
        success = self.generate_report()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n❌ {len(self.failed_tests)} TEST SUITE(S) FAILED: {', '.join(self.failed_tests)}")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive Test Suite Runner')
    parser.add_argument('--coverage', action='store_true', help='Enable coverage analysis')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel test execution')
    parser.add_argument('--suite', choices=['backend', 'frontend', 'e2e', 'performance', 'security', 'analytics', 'mathematical'], 
                       help='Run specific test suite only')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(args)
    
    if args.suite:
        # Run specific suite only
        if args.suite == 'backend':
            runner.run_backend_tests()
        elif args.suite == 'frontend':
            runner.run_frontend_tests()
        elif args.suite == 'e2e':
            runner.run_e2e_tests()
        elif args.suite == 'performance':
            runner.run_performance_tests()
        elif args.suite == 'security':
            runner.run_security_tests()
        elif args.suite == 'analytics':
            runner.run_analytics_tests()
        elif args.suite == 'mathematical':
            runner.run_mathematical_accuracy_tests()
        
        runner.generate_report()
        return 0 if len(runner.failed_tests) == 0 else 1
    else:
        # Run all tests
        return runner.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
