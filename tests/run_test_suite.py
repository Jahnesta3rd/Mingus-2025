#!/usr/bin/env python3
"""
Comprehensive Test Runner for Job Recommendation Engine
Executes all test categories with reporting, coverage, and monitoring
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import coverage
import pytest
from pathlib import Path


class TestSuiteRunner:
    """Comprehensive test suite runner with reporting and monitoring"""
    
    def __init__(self, args):
        """Initialize the test runner"""
        self.args = args
        self.start_time = datetime.now()
        self.results = {
            'summary': {},
            'test_categories': {},
            'performance_metrics': {},
            'coverage_data': {},
            'errors': []
        }
        
        # Test categories
        self.test_categories = {
            'unit': {
                'pattern': 'test_job_recommendation_engine.py',
                'description': 'Unit tests for core components',
                'timeout': 300  # 5 minutes
            },
            'integration': {
                'pattern': 'test_integration_workflow.py',
                'description': 'Integration tests for complete workflows',
                'timeout': 600  # 10 minutes
            },
            'performance': {
                'pattern': 'test_performance_benchmarks.py',
                'description': 'Performance benchmarks and load testing',
                'timeout': 900  # 15 minutes
            },
            'user_acceptance': {
                'pattern': 'test_user_scenarios.py',
                'description': 'User acceptance tests for target demographic',
                'timeout': 600  # 10 minutes
            },
            'data_generation': {
                'pattern': 'test_data_generation.py',
                'description': 'Mock data generation utilities',
                'timeout': 300  # 5 minutes
            }
        }
        
        # Setup coverage
        self.cov = coverage.Coverage(
            source=['backend'],
            omit=[
                '*/tests/*',
                '*/migrations/*',
                '*/__pycache__/*',
                '*/venv/*',
                '*/env/*'
            ]
        )

    def run_all_tests(self):
        """Run all test categories"""
        print("=" * 80)
        print("MINGUS JOB RECOMMENDATION ENGINE - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target Demographic: African American professionals 25-35")
        print(f"Test Environment: {self.args.environment}")
        print()
        
        # Start coverage measurement
        if self.args.coverage:
            self.cov.start()
        
        # Run each test category
        for category, config in self.test_categories.items():
            if self.args.categories and category not in self.args.categories:
                continue
                
            print(f"Running {category.upper()} tests...")
            print(f"Description: {config['description']}")
            
            try:
                result = self.run_test_category(category, config)
                self.results['test_categories'][category] = result
                
                if result['success']:
                    print(f"✅ {category.upper()} tests PASSED")
                else:
                    print(f"❌ {category.upper()} tests FAILED")
                    self.results['errors'].append(f"{category}: {result['error']}")
                
                print(f"Duration: {result['duration']:.2f}s")
                print(f"Tests: {result['tests_run']} passed, {result['tests_failed']} failed")
                print()
                
            except Exception as e:
                error_msg = f"Error running {category} tests: {str(e)}"
                print(f"❌ {error_msg}")
                self.results['errors'].append(error_msg)
                self.results['test_categories'][category] = {
                    'success': False,
                    'error': str(e),
                    'duration': 0,
                    'tests_run': 0,
                    'tests_failed': 0
                }
        
        # Stop coverage measurement
        if self.args.coverage:
            self.cov.stop()
            self.cov.save()
            self.results['coverage_data'] = self.get_coverage_report()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        if self.args.output:
            self.save_results()
        
        # Print final report
        self.print_final_report()
        
        return self.results['summary']['overall_success']

    def run_test_category(self, category: str, config: Dict) -> Dict:
        """Run a specific test category"""
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            f'tests/{config["pattern"]}',
            '-v',
            '--tb=short'
        ]
        
        # Add category-specific options
        if category == 'performance':
            cmd.extend(['-m', 'performance'])
        elif category == 'integration':
            cmd.extend(['-m', 'integration'])
        elif category == 'user_acceptance':
            cmd.extend(['-m', 'user_acceptance'])
        
        # Add coverage options
        if self.args.coverage:
            cmd.extend(['--cov=backend', '--cov-report=term-missing'])
        
        # Add output options
        if self.args.verbose:
            cmd.append('-s')
        
        # Run the tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config['timeout'],
                cwd=os.getcwd()
            )
            
            duration = time.time() - start_time
            
            # Parse results
            success = result.returncode == 0
            output = result.stdout
            error_output = result.stderr
            
            # Extract test statistics
            tests_run = 0
            tests_failed = 0
            
            for line in output.split('\n'):
                if 'passed' in line and 'failed' in line:
                    # Parse pytest summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            tests_run = int(parts[i-1])
                        elif part == 'failed':
                            tests_failed = int(parts[i-1])
                            break
                    break
            
            return {
                'success': success,
                'duration': duration,
                'tests_run': tests_run,
                'tests_failed': tests_failed,
                'output': output,
                'error_output': error_output,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Timeout after {config["timeout"]} seconds',
                'duration': config['timeout'],
                'tests_run': 0,
                'tests_failed': 0,
                'output': '',
                'error_output': 'Test execution timed out',
                'return_code': -1
            }

    def get_coverage_report(self) -> Dict:
        """Get coverage report data"""
        try:
            # Generate coverage report
            self.cov.report()
            
            # Get coverage data
            coverage_data = {
                'summary': self.cov.report(),
                'missing': self.cov.get_missing(),
                'statements': self.cov.get_data().measured_files()
            }
            
            return coverage_data
            
        except Exception as e:
            return {
                'error': str(e),
                'summary': 'Coverage report generation failed'
            }

    def generate_summary(self):
        """Generate test summary"""
        total_tests = 0
        total_failed = 0
        total_duration = 0
        successful_categories = 0
        
        for category, result in self.results['test_categories'].items():
            if result['success']:
                successful_categories += 1
            
            total_tests += result['tests_run']
            total_failed += result['tests_failed']
            total_duration += result['duration']
        
        total_categories = len(self.results['test_categories'])
        overall_success = successful_categories == total_categories and len(self.results['errors']) == 0
        
        self.results['summary'] = {
            'overall_success': overall_success,
            'total_categories': total_categories,
            'successful_categories': successful_categories,
            'total_tests': total_tests,
            'total_failed': total_failed,
            'total_duration': total_duration,
            'success_rate': (successful_categories / total_categories) if total_categories > 0 else 0,
            'test_success_rate': ((total_tests - total_failed) / total_tests) if total_tests > 0 else 0
        }

    def save_results(self):
        """Save test results to file"""
        results_file = self.args.output
        
        # Add metadata
        self.results['metadata'] = {
            'timestamp': self.start_time.isoformat(),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'environment': self.args.environment,
            'python_version': sys.version,
            'args': vars(self.args)
        }
        
        # Save to JSON
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"Results saved to: {results_file}")

    def print_final_report(self):
        """Print final test report"""
        print("=" * 80)
        print("TEST SUITE SUMMARY")
        print("=" * 80)
        
        summary = self.results['summary']
        
        # Overall status
        if summary['overall_success']:
            print("🎉 ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        
        print()
        
        # Statistics
        print(f"Test Categories: {summary['successful_categories']}/{summary['total_categories']} passed")
        print(f"Total Tests: {summary['total_tests']} run, {summary['total_failed']} failed")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Test Success Rate: {summary['test_success_rate']:.1%}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print()
        
        # Category breakdown
        print("Category Breakdown:")
        for category, result in self.results['test_categories'].items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {category:20} {status:8} {result['tests_run']:3} tests, {result['duration']:6.2f}s")
        
        print()
        
        # Coverage report
        if self.args.coverage and 'coverage_data' in self.results:
            print("Coverage Report:")
            coverage_data = self.results['coverage_data']
            if 'summary' in coverage_data:
                print(f"  {coverage_data['summary']}")
            else:
                print(f"  Coverage report: {coverage_data.get('error', 'Available')}")
        
        print()
        
        # Errors
        if self.results['errors']:
            print("Errors:")
            for error in self.results['errors']:
                print(f"  ❌ {error}")
            print()
        
        # Performance metrics
        if self.results['performance_metrics']:
            print("Performance Metrics:")
            for metric, value in self.results['performance_metrics'].items():
                print(f"  {metric}: {value}")
            print()
        
        # Recommendations
        print("Recommendations:")
        if summary['overall_success']:
            print("  ✅ All tests passed - system is ready for deployment")
        else:
            print("  ⚠️  Some tests failed - review and fix issues before deployment")
        
        if summary['test_success_rate'] < 0.95:
            print("  ⚠️  Test success rate below 95% - investigate failures")
        
        if summary['total_duration'] > 1800:  # 30 minutes
            print("  ⚠️  Test suite took longer than 30 minutes - consider optimization")
        
        print()
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def run_performance_monitoring(self):
        """Run performance monitoring during tests"""
        if not self.args.monitor:
            return
        
        print("Starting performance monitoring...")
        
        # Monitor system resources
        import psutil
        
        cpu_usage = []
        memory_usage = []
        
        def monitor_resources():
            while True:
                cpu_usage.append(psutil.cpu_percent())
                memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(5)
        
        # Start monitoring in background
        import threading
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()
        
        # Store monitoring data
        self.results['performance_metrics'] = {
            'avg_cpu_usage': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
            'max_cpu_usage': max(cpu_usage) if cpu_usage else 0,
            'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            'max_memory_usage': max(memory_usage) if memory_usage else 0
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Comprehensive Test Runner for Job Recommendation Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_test_suite.py

  # Run specific categories
  python run_test_suite.py --categories unit integration

  # Run with coverage and monitoring
  python run_test_suite.py --coverage --monitor --verbose

  # Run performance tests only
  python run_test_suite.py --categories performance --output results.json

  # Run in production environment
  python run_test_suite.py --environment production
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['unit', 'integration', 'performance', 'user_acceptance', 'data_generation'],
        help='Specific test categories to run'
    )
    
    parser.add_argument(
        '--environment',
        default='testing',
        choices=['testing', 'staging', 'production'],
        help='Test environment'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Monitor system performance during tests'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for test results (JSON)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,  # 30 minutes
        help='Overall timeout for test suite (seconds)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.categories and not all(cat in ['unit', 'integration', 'performance', 'user_acceptance', 'data_generation'] for cat in args.categories):
        parser.error("Invalid test category specified")
    
    # Create test runner
    runner = TestSuiteRunner(args)
    
    try:
        # Run tests
        success = runner.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error running test suite: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main() 