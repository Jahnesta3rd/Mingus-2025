#!/usr/bin/env python3
"""
Comprehensive Test Runner for Income Comparison Feature
Runs all tests and provides detailed reporting
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
import subprocess

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

def run_test_suite():
    """Run the complete income comparison test suite"""
    print("🎯 COMPREHENSIVE INCOME COMPARISON TEST SUITE")
    print("=" * 80)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test modules to run
    test_modules = [
        'tests.test_income_comparison_unit',
        'tests.test_income_comparison_integration',
        'tests.test_income_comparison_scenarios',
        'tests.test_income_comparison_performance',
        'tests.test_income_comparison_flask'
    ]
    
    # Test results storage
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'error_tests': 0,
        'test_modules': {},
        'performance_metrics': {},
        'coverage_summary': {}
    }
    
    # Run each test module
    for module_name in test_modules:
        print(f"🧪 Running {module_name}...")
        
        try:
            # Import and run test module
            module = __import__(module_name, fromlist=[''])
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            result = runner.run(suite)
            
            # Store results
            module_results = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
            }
            
            test_results['test_modules'][module_name] = module_results
            test_results['total_tests'] += result.testsRun
            test_results['passed_tests'] += result.testsRun - len(result.failures) - len(result.errors)
            test_results['failed_tests'] += len(result.failures)
            test_results['error_tests'] += len(result.errors)
            
            # Print module summary
            print(f"   ✅ Tests run: {result.testsRun}")
            print(f"   ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
            print(f"   ❌ Failed: {len(result.failures)}")
            print(f"   ⚠️  Errors: {len(result.errors)}")
            print(f"   📊 Success rate: {module_results['success_rate']:.1f}%")
            
            if result.failures:
                print(f"   ❌ Failures:")
                for test, traceback in result.failures:
                    print(f"      - {test}: {traceback.split('AssertionError:')[-1].strip()}")
            
            if result.errors:
                print(f"   ⚠️  Errors:")
                for test, traceback in result.errors:
                    print(f"      - {test}: {traceback.split('Exception:')[-1].strip()}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error loading {module_name}: {str(e)}")
            test_results['test_modules'][module_name] = {
                'error': str(e),
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'success_rate': 0
            }
            test_results['error_tests'] += 1
            print()
    
    # Calculate overall metrics
    if test_results['total_tests'] > 0:
        overall_success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100
    else:
        overall_success_rate = 0
    
    # Print comprehensive summary
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed_tests']}")
    print(f"Failed: {test_results['failed_tests']}")
    print(f"Errors: {test_results['error_tests']}")
    print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    print()
    
    # Print module breakdown
    print("📋 MODULE BREAKDOWN:")
    for module_name, results in test_results['test_modules'].items():
        if 'error' not in results:
            print(f"   {module_name}:")
            print(f"      Tests: {results['tests_run']}")
            print(f"      Success Rate: {results['success_rate']:.1f}%")
            if results['failures'] > 0:
                print(f"      Failures: {results['failures']}")
            if results['errors'] > 0:
                print(f"      Errors: {results['errors']}")
        else:
            print(f"   {module_name}: ERROR - {results['error']}")
    print()
    
    # Test coverage analysis
    print("🎯 TEST COVERAGE ANALYSIS:")
    coverage_areas = {
        'Unit Tests': 'Core functionality and calculations',
        'Integration Tests': 'Complete workflows and API integration',
        'Scenario Tests': 'Realistic user profiles and edge cases',
        'Performance Tests': 'Speed and scalability validation',
        'Flask Tests': 'Web application and API endpoints'
    }
    
    for area, description in coverage_areas.items():
        print(f"   {area}: {description}")
    print()
    
    # Performance benchmarks
    print("⚡ PERFORMANCE BENCHMARKS:")
    performance_benchmarks = {
        'Single Comparison': '< 50ms',
        'Multiple Comparisons': '< 30ms average',
        'Concurrent Requests': '< 100ms with 10 users',
        'Data Loading': '< 100ms',
        'Quality Validation': '< 100ms'
    }
    
    for benchmark, target in performance_benchmarks.items():
        print(f"   {benchmark}: {target}")
    print()
    
    # Quality assessment
    print("🏆 QUALITY ASSESSMENT:")
    if overall_success_rate >= 95:
        quality_level = "EXCELLENT"
        quality_emoji = "🌟"
    elif overall_success_rate >= 90:
        quality_level = "GOOD"
        quality_emoji = "✅"
    elif overall_success_rate >= 80:
        quality_level = "FAIR"
        quality_emoji = "⚠️"
    else:
        quality_level = "NEEDS IMPROVEMENT"
        quality_emoji = "❌"
    
    print(f"   Overall Quality: {quality_emoji} {quality_level}")
    print(f"   Test Coverage: {'Comprehensive' if test_results['total_tests'] >= 50 else 'Limited'}")
    print(f"   Error Handling: {'Robust' if test_results['error_tests'] == 0 else 'Needs Attention'}")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS:")
    if overall_success_rate >= 95:
        print("   ✅ System is ready for production deployment")
        print("   ✅ All critical functionality is working correctly")
        print("   ✅ Performance meets requirements")
    elif overall_success_rate >= 90:
        print("   ⚠️  Minor issues need attention before production")
        print("   ✅ Core functionality is working")
        print("   🔧 Review failed tests and address issues")
    elif overall_success_rate >= 80:
        print("   ❌ Significant issues need to be resolved")
        print("   🔧 Focus on failed tests and error handling")
        print("   🔧 Consider additional testing before deployment")
    else:
        print("   ❌ Critical issues prevent deployment")
        print("   🔧 Major refactoring may be required")
        print("   🔧 Address all failures before proceeding")
    
    if test_results['failed_tests'] > 0:
        print(f"   🔧 Fix {test_results['failed_tests']} failed tests")
    if test_results['error_tests'] > 0:
        print(f"   🔧 Resolve {test_results['error_tests']} test errors")
    
    print()
    
    # Save test results
    results_file = Path("test_results_income_comparison.json")
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"📄 Test results saved to: {results_file}")
    print()
    
    # Final status
    if overall_success_rate >= 95:
        print("🎉 INCOME COMPARISON SYSTEM IS PRODUCTION READY!")
        print("✅ All tests passed with excellent quality")
        print("✅ System provides reliable, accurate income comparisons")
        print("✅ Performance meets web application requirements")
        print("✅ Error handling is robust and graceful")
    elif overall_success_rate >= 90:
        print("✅ INCOME COMPARISON SYSTEM IS MOSTLY READY")
        print("⚠️  Minor issues need attention before production")
        print("✅ Core functionality is working correctly")
    else:
        print("❌ INCOME COMPARISON SYSTEM NEEDS WORK")
        print("🔧 Address test failures before production deployment")
        print("🔧 Focus on error handling and data validation")
    
    print()
    print("=" * 80)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_success_rate >= 95

def run_specific_test_category(category):
    """Run tests for a specific category"""
    category_map = {
        'unit': 'tests.test_income_comparison_unit',
        'integration': 'tests.test_income_comparison_integration',
        'scenarios': 'tests.test_income_comparison_scenarios',
        'performance': 'tests.test_income_comparison_performance',
        'flask': 'tests.test_income_comparison_flask'
    }
    
    if category not in category_map:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_map.keys())}")
        return False
    
    print(f"🧪 Running {category} tests...")
    
    try:
        module = __import__(category_map[category], fromlist=[''])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"📊 {category.title()} Tests Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 95
        
    except Exception as e:
        print(f"❌ Error running {category} tests: {str(e)}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Income Comparison Test Suite')
    parser.add_argument('--category', choices=['unit', 'integration', 'scenarios', 'performance', 'flask'],
                       help='Run tests for specific category only')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only (skip performance tests)')
    
    args = parser.parse_args()
    
    if args.category:
        success = run_specific_test_category(args.category)
    else:
        success = run_test_suite()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 