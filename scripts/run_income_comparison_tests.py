#!/usr/bin/env python3
"""
Test Runner for Enhanced Income Comparison Calculator
Executes comprehensive test suite and generates detailed reports
"""

import os
import sys
import subprocess
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import django
from django.conf import settings
from django.test.utils import get_runner

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()


class TestRunner:
    """Comprehensive test runner for income comparison calculator"""
    
    def __init__(self, verbose: bool = False, coverage: bool = False):
        self.verbose = verbose
        self.coverage = coverage
        self.test_results = {}
        self.start_time = time.time()
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and return results"""
        print("🚀 Starting Enhanced Income Comparison Calculator Test Suite")
        print("=" * 80)
        
        test_suites = [
            ("API Integration Tests", self.run_api_integration_tests),
            ("ML Prediction Tests", self.run_ml_prediction_tests),
            ("Lead Capture Flow Tests", self.run_lead_capture_tests),
            ("Cultural Content Tests", self.run_cultural_content_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Monitoring Tests", self.run_monitoring_tests)
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 Running {suite_name}...")
            try:
                result = test_func()
                self.test_results[suite_name] = result
                self._print_suite_result(suite_name, result)
            except Exception as e:
                print(f"❌ Error running {suite_name}: {e}")
                self.test_results[suite_name] = {
                    'status': 'error',
                    'error': str(e),
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0
                }
        
        return self.generate_final_report()
    
    def run_api_integration_tests(self) -> Dict[str, Any]:
        """Run API integration tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_bls_api_integration',
            'tests.test_income_comparison.TestIncomeComparison.test_census_api_integration',
            'tests.test_income_comparison.TestIncomeComparison.test_fred_api_integration',
            'tests.test_income_comparison.TestIncomeComparison.test_bea_api_integration',
            'tests.test_income_comparison.TestIncomeComparison.test_api_rate_limiting'
        ]
        
        return self._run_test_modules(test_modules, "API Integration")
    
    def run_ml_prediction_tests(self) -> Dict[str, Any]:
        """Run ML prediction tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_salary_prediction_accuracy',
            'tests.test_income_comparison.TestIncomeComparison.test_prediction_cache_functionality',
            'tests.test_income_comparison.TestIncomeComparison.test_career_path_recommendations',
            'tests.test_income_comparison.TestIncomeComparison.test_prediction_confidence_threshold'
        ]
        
        return self._run_test_modules(test_modules, "ML Predictions")
    
    def run_lead_capture_tests(self) -> Dict[str, Any]:
        """Run lead capture flow tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_progressive_lead_capture_flow',
            'tests.test_income_comparison.TestIncomeComparison.test_lead_scoring_algorithm',
            'tests.test_income_comparison.TestIncomeComparison.test_gamification_badge_unlocking',
            'tests.test_income_comparison.TestIncomeComparison.test_email_sequence_triggering'
        ]
        
        return self._run_test_modules(test_modules, "Lead Capture")
    
    def run_cultural_content_tests(self) -> Dict[str, Any]:
        """Run cultural content tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_cultural_content_generation',
            'tests.test_income_comparison.TestIncomeComparison.test_salary_gap_analysis',
            'tests.test_income_comparison.TestIncomeComparison.test_representation_premium_calculation',
            'tests.test_income_comparison.TestIncomeComparison.test_community_wealth_building_context',
            'tests.test_income_comparison.TestIncomeComparison.test_culturally_aware_recommendations'
        ]
        
        return self._run_test_modules(test_modules, "Cultural Content")
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_performance_under_load',
            'tests.test_income_comparison.TestIncomeComparison.test_error_handling_and_recovery'
        ]
        
        return self._run_test_modules(test_modules, "Performance")
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        test_modules = [
            'tests.test_income_comparison.TestIncomeComparison.test_end_to_end_workflow',
            'tests.test_income_comparison.TestIncomeComparisonAPIs.test_salary_benchmark_endpoint',
            'tests.test_income_comparison.TestIncomeComparisonAPIs.test_salary_prediction_endpoint',
            'tests.test_income_comparison.TestIncomeComparisonAPIs.test_lead_capture_endpoint',
            'tests.test_income_comparison.TestIncomeComparisonAPIs.test_cultural_content_endpoint'
        ]
        
        return self._run_test_modules(test_modules, "Integration")
    
    def run_monitoring_tests(self) -> Dict[str, Any]:
        """Run monitoring tests"""
        # Create a simple test for monitoring functionality
        try:
            from backend.services.monitoring_service import monitoring_service
            
            # Test basic monitoring functionality
            monitoring_service.record_api_request('/test', 'GET', 200, 0.1)
            monitoring_service.record_lead_capture_success('basic', 'atlanta', 'technology')
            monitoring_service.record_salary_prediction('atlanta', 'technology', 'mid')
            
            metrics_summary = monitoring_service.get_metrics_summary()
            
            return {
                'status': 'passed',
                'tests_run': 1,
                'tests_passed': 1,
                'tests_failed': 0,
                'details': {
                    'metrics_collected': len(metrics_summary),
                    'api_requests_recorded': metrics_summary.get('total_api_requests', 0),
                    'lead_captures_recorded': metrics_summary.get('total_lead_captures', 0)
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'tests_run': 1,
                'tests_passed': 0,
                'tests_failed': 1,
                'error': str(e)
            }
    
    def _run_test_modules(self, test_modules: List[str], suite_name: str) -> Dict[str, Any]:
        """Run specific test modules using Django test runner"""
        try:
            # Use Django test runner
            TestRunner = get_runner(settings)
            test_runner = TestRunner(verbosity=2 if self.verbose else 1)
            
            # Run tests
            failures = test_runner.run_tests(test_modules)
            
            # Parse results
            total_tests = len(test_modules)
            passed_tests = total_tests - len(failures) if failures else total_tests
            failed_tests = len(failures) if failures else 0
            
            return {
                'status': 'passed' if failed_tests == 0 else 'failed',
                'tests_run': total_tests,
                'tests_passed': passed_tests,
                'tests_failed': failed_tests,
                'failures': failures if failures else [],
                'details': {
                    'suite_name': suite_name,
                    'execution_time': time.time() - self.start_time
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'tests_run': len(test_modules),
                'tests_passed': 0,
                'tests_failed': len(test_modules),
                'error': str(e)
            }
    
    def _print_suite_result(self, suite_name: str, result: Dict[str, Any]):
        """Print test suite results"""
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        print(f"{status_icon} {suite_name}: {result['tests_passed']}/{result['tests_run']} tests passed")
        
        if result.get('failures'):
            print(f"   Failures: {len(result['failures'])}")
            for failure in result['failures']:
                print(f"   - {failure}")
        
        if result.get('error'):
            print(f"   Error: {result['error']}")
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = sum(result.get('tests_run', 0) for result in self.test_results.values())
        total_passed = sum(result.get('tests_passed', 0) for result in self.test_results.values())
        total_failed = sum(result.get('tests_failed', 0) for result in self.test_results.values())
        
        execution_time = time.time() - self.start_time
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'tests_passed': total_passed,
                'tests_failed': total_failed,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat()
            },
            'test_suites': self.test_results,
            'recommendations': self._generate_recommendations()
        }
        
        self._print_final_report(report)
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        total_failed = sum(result.get('tests_failed', 0) for result in self.test_results.values())
        
        if total_failed > 0:
            recommendations.append("🔧 Fix failing tests before deployment")
        
        # Check specific areas
        for suite_name, result in self.test_results.items():
            if result.get('tests_failed', 0) > 0:
                recommendations.append(f"🔧 Review and fix {suite_name}")
        
        # Performance recommendations
        performance_result = self.test_results.get("Performance Tests", {})
        if performance_result.get('tests_failed', 0) > 0:
            recommendations.append("⚡ Optimize performance bottlenecks")
        
        # API recommendations
        api_result = self.test_results.get("API Integration Tests", {})
        if api_result.get('tests_failed', 0) > 0:
            recommendations.append("🔌 Check external API integrations")
        
        if not recommendations:
            recommendations.append("✅ All tests passed! Ready for deployment")
        
        return recommendations
    
    def _print_final_report(self, report: Dict[str, Any]):
        """Print final test report"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED INCOME COMPARISON CALCULATOR - TEST REPORT")
        print("=" * 80)
        
        summary = report['summary']
        print(f"\n🎯 SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['tests_passed']}")
        print(f"   Failed: {summary['tests_failed']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Execution Time: {summary['execution_time_seconds']:.2f} seconds")
        
        print(f"\n📋 DETAILED RESULTS:")
        for suite_name, result in report['test_suites'].items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"   {status_icon} {suite_name}: {result['tests_passed']}/{result['tests_run']} passed")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            print(f"   {recommendation}")
        
        # Overall status
        overall_status = "✅ ALL TESTS PASSED" if summary['tests_failed'] == 0 else "❌ SOME TESTS FAILED"
        print(f"\n{overall_status}")
        
        if summary['tests_failed'] == 0:
            print("🚀 Ready for production deployment!")
        else:
            print("⚠️  Please fix failing tests before deployment")
    
    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """Save test report to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_reports/income_comparison_test_report_{timestamp}.json"
        
        # Create reports directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Test report saved to: {output_file}")
        return output_file
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis if coverage is enabled"""
        if not self.coverage:
            return {}
        
        try:
            print("\n📊 Running coverage analysis...")
            
            # Run coverage
            cmd = [
                'coverage', 'run', '--source=backend',
                '-m', 'django', 'test', 'tests.test_income_comparison'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Generate coverage report
                coverage_cmd = ['coverage', 'report', '--show-missing']
                coverage_result = subprocess.run(coverage_cmd, capture_output=True, text=True)
                
                return {
                    'coverage_output': coverage_result.stdout,
                    'coverage_error': coverage_result.stderr
                }
            else:
                return {
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'error': str(e)
            }


def main():
    """Main function to run the test suite"""
    parser = argparse.ArgumentParser(description='Run Enhanced Income Comparison Calculator Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run coverage analysis')
    parser.add_argument('--output', '-o', help='Output file for test report')
    parser.add_argument('--suite', '-s', help='Run specific test suite')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(verbose=args.verbose, coverage=args.coverage)
    
    # Run specific suite if specified
    if args.suite:
        suite_methods = {
            'api': runner.run_api_integration_tests,
            'ml': runner.run_ml_prediction_tests,
            'lead': runner.run_lead_capture_tests,
            'cultural': runner.run_cultural_content_tests,
            'performance': runner.run_performance_tests,
            'integration': runner.run_integration_tests,
            'monitoring': runner.run_monitoring_tests
        }
        
        if args.suite in suite_methods:
            print(f"🚀 Running {args.suite} test suite...")
            result = suite_methods[args.suite]()
            runner.test_results[args.suite] = result
            runner._print_suite_result(args.suite, result)
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(suite_methods.keys())}")
            return 1
    else:
        # Run all tests
        report = runner.run_all_tests()
        
        # Save report
        if args.output:
            runner.save_report(report, args.output)
        else:
            runner.save_report(report)
        
        # Run coverage if requested
        if args.coverage:
            coverage_result = runner.run_coverage_analysis()
            if coverage_result:
                print("\n📊 COVERAGE ANALYSIS:")
                if 'coverage_output' in coverage_result:
                    print(coverage_result['coverage_output'])
                elif 'error' in coverage_result:
                    print(f"❌ Coverage error: {coverage_result['error']}")
        
        # Return appropriate exit code
        return 0 if report['summary']['tests_failed'] == 0 else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 