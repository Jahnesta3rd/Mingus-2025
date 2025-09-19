#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location Test Runner
Comprehensive test runner for Optimal Location feature testing
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import test modules
from test_optimal_location_service import TestOptimalLocationService, TestOptimalLocationServiceIntegration
from test_optimal_location_api import TestOptimalLocationAPI, TestOptimalLocationAPIIntegration
from test_optimal_location_integration import TestOptimalLocationIntegration
from test_optimal_location_performance import TestOptimalLocationPerformance

class OptimalLocationTestRunner:
    """Comprehensive test runner for Optimal Location feature"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self):
        """Run all Optimal Location tests"""
        print("=" * 60)
        print("MINGUS OPTIMAL LOCATION FEATURE - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.start_time = time.time()
        
        # Test categories
        test_categories = [
            ('Backend Service Tests', self._run_backend_tests),
            ('API Endpoint Tests', self._run_api_tests),
            ('Integration Tests', self._run_integration_tests),
            ('Performance Tests', self._run_performance_tests)
        ]
        
        # Run each test category
        for category_name, test_function in test_categories:
            print(f"\n{'=' * 40}")
            print(f"RUNNING {category_name.upper()}")
            print(f"{'=' * 40}")
            
            try:
                result = test_function()
                self.test_results[category_name] = result
                self._print_category_results(category_name, result)
            except Exception as e:
                print(f"ERROR in {category_name}: {e}")
                self.test_results[category_name] = {
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'success_rate': 0.0,
                    'execution_time': 0.0
                }
        
        self.end_time = time.time()
        self._print_final_summary()
        self._save_test_report()
        
        return self.test_results
    
    def _run_backend_tests(self):
        """Run backend service tests"""
        test_suite = unittest.TestSuite()
        
        # Add unit tests
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationService))
        
        # Add integration tests
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationServiceIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(test_suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'execution_time': 0.0  # Will be calculated by the runner
        }
    
    def _run_api_tests(self):
        """Run API endpoint tests"""
        test_suite = unittest.TestSuite()
        
        # Add unit tests
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationAPI))
        
        # Add integration tests
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationAPIIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(test_suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'execution_time': 0.0
        }
    
    def _run_integration_tests(self):
        """Run integration tests"""
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(test_suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'execution_time': 0.0
        }
    
    def _run_performance_tests(self):
        """Run performance tests"""
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(TestOptimalLocationPerformance))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(test_suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'execution_time': 0.0
        }
    
    def _print_category_results(self, category_name, result):
        """Print results for a test category"""
        print(f"\n{category_name} Results:")
        print(f"  Tests run: {result['tests_run']}")
        print(f"  Failures: {result['failures']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Success rate: {result['success_rate']:.1f}%")
        
        if result['failures'] > 0 or result['errors'] > 0:
            print(f"  Status: ❌ FAILED")
        else:
            print(f"  Status: ✅ PASSED")
    
    def _print_final_summary(self):
        """Print final test summary"""
        total_time = self.end_time - self.start_time
        
        print(f"\n{'=' * 60}")
        print("FINAL TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total execution time: {total_time:.2f} seconds")
        print()
        
        total_tests = sum(result['tests_run'] for result in self.test_results.values())
        total_failures = sum(result['failures'] for result in self.test_results.values())
        total_errors = sum(result['errors'] for result in self.test_results.values())
        overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total tests run: {total_tests}")
        print(f"Total failures: {total_failures}")
        print(f"Total errors: {total_errors}")
        print(f"Overall success rate: {overall_success_rate:.1f}%")
        print()
        
        # Category breakdown
        print("Category Breakdown:")
        for category, result in self.test_results.items():
            status = "✅ PASSED" if result['failures'] == 0 and result['errors'] == 0 else "❌ FAILED"
            print(f"  {category}: {result['tests_run']} tests, {result['success_rate']:.1f}% success - {status}")
        
        print()
        if total_failures == 0 and total_errors == 0:
            print("🎉 ALL TESTS PASSED! Optimal Location feature is ready for production.")
        else:
            print("⚠️  Some tests failed. Please review the results and fix issues before deployment.")
    
    def _save_test_report(self):
        """Save detailed test report to file"""
        report = {
            'test_suite': 'Optimal Location Feature',
            'execution_time': self.end_time - self.start_time,
            'timestamp': datetime.now().isoformat(),
            'results': self.test_results,
            'summary': {
                'total_tests': sum(result['tests_run'] for result in self.test_results.values()),
                'total_failures': sum(result['failures'] for result in self.test_results.values()),
                'total_errors': sum(result['errors'] for result in self.test_results.values()),
                'overall_success_rate': ((sum(result['tests_run'] for result in self.test_results.values()) - 
                                        sum(result['failures'] for result in self.test_results.values()) - 
                                        sum(result['errors'] for result in self.test_results.values())) / 
                                       sum(result['tests_run'] for result in self.test_results.values()) * 100) 
                                      if sum(result['tests_run'] for result in self.test_results.values()) > 0 else 0
            }
        }
        
        # Save report
        report_path = Path(__file__).parent / 'reports' / f'optimal_location_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed test report saved to: {report_path}")


def run_specific_test_category(category: str):
    """Run a specific test category"""
    runner = OptimalLocationTestRunner()
    
    if category.lower() == 'backend':
        return runner._run_backend_tests()
    elif category.lower() == 'api':
        return runner._run_api_tests()
    elif category.lower() == 'integration':
        return runner._run_integration_tests()
    elif category.lower() == 'performance':
        return runner._run_performance_tests()
    else:
        print(f"Unknown test category: {category}")
        print("Available categories: backend, api, integration, performance")
        return None


def run_frontend_tests():
    """Run frontend tests (requires Node.js environment)"""
    print("Running frontend tests...")
    
    # Check if we're in the frontend directory
    frontend_dir = Path(__file__).parent.parent / 'frontend'
    if not frontend_dir.exists():
        print("Frontend directory not found. Please run from project root.")
        return False
    
    # Change to frontend directory
    import subprocess
    import os
    
    original_dir = os.getcwd()
    try:
        os.chdir(frontend_dir)
        
        # Run Jest tests
        result = subprocess.run(['npm', 'test', '--', '--coverage', '--watchAll=false'], 
                              capture_output=True, text=True)
        
        print("Frontend test output:")
        print(result.stdout)
        
        if result.stderr:
            print("Frontend test errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running frontend tests: {e}")
        return False
    finally:
        os.chdir(original_dir)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Optimal Location feature tests')
    parser.add_argument('--category', choices=['backend', 'api', 'integration', 'performance', 'all'], 
                       default='all', help='Test category to run')
    parser.add_argument('--frontend', action='store_true', help='Also run frontend tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.category == 'all':
        runner = OptimalLocationTestRunner()
        runner.run_all_tests()
    else:
        result = run_specific_test_category(args.category)
        if result:
            print(f"\n{args.category.title()} Tests Results:")
            print(f"  Tests run: {result['tests_run']}")
            print(f"  Failures: {result['failures']}")
            print(f"  Errors: {result['errors']}")
            print(f"  Success rate: {result['success_rate']:.1f}%")
    
    if args.frontend:
        print("\n" + "=" * 60)
        print("RUNNING FRONTEND TESTS")
        print("=" * 60)
        success = run_frontend_tests()
        if success:
            print("✅ Frontend tests passed")
        else:
            print("❌ Frontend tests failed")
