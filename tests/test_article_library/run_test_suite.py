#!/usr/bin/env python3
"""
Mingus Article Library Test Suite Runner

Comprehensive test runner for the Mingus article library system.
This script runs all test categories and generates detailed reports.
"""

import os
import sys
import subprocess
import argparse
import time
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    
    print(f"Duration: {duration:.2f} seconds")
    print(f"Exit Code: {result.returncode}")
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return {
        'command': command,
        'description': description,
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'duration': duration
    }

def run_unit_tests():
    """Run unit tests"""
    return run_command(
        "python -m pytest tests/test_article_library/unit/ -v --tb=short --cov=backend --cov-report=term-missing",
        "Unit Tests"
    )

def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "python -m pytest tests/test_article_library/integration/ -v --tb=short",
        "Integration Tests"
    )

def run_api_tests():
    """Run API tests"""
    return run_command(
        "python -m pytest tests/test_article_library/api/ -v --tb=short",
        "API Tests"
    )

def run_database_tests():
    """Run database tests"""
    return run_command(
        "python -m pytest tests/test_article_library/database/ -v --tb=short",
        "Database Tests"
    )

def run_security_tests():
    """Run security tests"""
    return run_command(
        "python -m pytest tests/test_article_library/security/ -v --tb=short",
        "Security Tests"
    )

def run_performance_tests():
    """Run performance tests"""
    return run_command(
        "python -m pytest tests/test_article_library/performance/ -v --tb=short -m performance",
        "Performance Tests"
    )

def run_frontend_tests():
    """Run frontend tests"""
    return run_command(
        "python -m pytest tests/test_article_library/frontend/ -v --tb=short",
        "Frontend Tests"
    )

def run_e2e_tests():
    """Run end-to-end tests"""
    return run_command(
        "python -m pytest tests/test_article_library/e2e/ -v --tb=short",
        "End-to-End Tests"
    )

def run_all_tests():
    """Run all test categories"""
    return run_command(
        "python -m pytest tests/test_article_library/ -v --tb=short --cov=backend --cov-report=html --cov-report=term-missing",
        "All Tests"
    )

def generate_test_report(results):
    """Generate a comprehensive test report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results if r['returncode'] == 0),
            'failed': sum(1 for r in results if r['returncode'] != 0),
            'total_duration': sum(r['duration'] for r in results)
        },
        'results': results
    }
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*80}")
    print(f"Total Test Categories: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Total Duration: {report['summary']['total_duration']:.2f} seconds")
    print(f"Timestamp: {report['timestamp']}")
    
    # Print detailed results
    print(f"\n{'='*80}")
    print("DETAILED RESULTS")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅ PASSED" if result['returncode'] == 0 else "❌ FAILED"
        print(f"{status} | {result['description']} | {result['duration']:.2f}s")
        
        if result['returncode'] != 0:
            print(f"  Error: {result['stderr'][:200]}...")
    
    return report

def save_report(report, output_file):
    """Save the test report to a file"""
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved to: {output_file}")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Mingus Article Library Test Suite Runner')
    parser.add_argument('--category', choices=[
        'unit', 'integration', 'api', 'database', 'security', 
        'performance', 'frontend', 'e2e', 'all'
    ], default='all', help='Test category to run')
    parser.add_argument('--report', default='test_report.json', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("Mingus Article Library Test Suite")
    print("=" * 50)
    print(f"Running tests for category: {args.category}")
    print(f"Report will be saved to: {args.report}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test categories
    test_categories = {
        'unit': run_unit_tests,
        'integration': run_integration_tests,
        'api': run_api_tests,
        'database': run_database_tests,
        'security': run_security_tests,
        'performance': run_performance_tests,
        'frontend': run_frontend_tests,
        'e2e': run_e2e_tests,
        'all': run_all_tests
    }
    
    # Run tests
    if args.category == 'all':
        # Run all categories individually
        results = []
        for category_name, category_func in test_categories.items():
            if category_name != 'all':
                result = category_func()
                results.append(result)
    else:
        # Run specific category
        results = [test_categories[args.category]()]
    
    # Generate and save report
    report = generate_test_report(results)
    save_report(report, args.report)
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        print(f"\n❌ Test suite completed with {report['summary']['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n✅ Test suite completed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
