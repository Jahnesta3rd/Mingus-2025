#!/usr/bin/env python3
"""
Example: Running Comprehensive Tests for MINGUS Application
Demonstrates how to use the performance and compliance testing framework
"""

import os
import sys
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the test runner
from tests.run_comprehensive_test_suite import ComprehensiveTestRunner


def run_basic_example():
    """Run basic comprehensive testing example"""
    print("🧪 MINGUS Comprehensive Testing Example")
    print("=" * 50)
    
    # Initialize test runner
    runner = ComprehensiveTestRunner(output_dir="example_test_reports")
    
    # Run complete test suite
    print("🔄 Running complete test suite...")
    report = runner.generate_comprehensive_report()
    
    # Display results
    print("\n📊 Test Results Summary:")
    print("-" * 30)
    
    executive = report['executive_summary']
    print(f"Overall Status: {executive['overall_status']}")
    print(f"Performance Status: {executive['performance_status']}")
    print(f"Compliance Status: {executive['compliance_status']}")
    print(f"Total Tests: {executive['total_tests']}")
    print(f"Tests Passed: {executive['total_passed']}")
    print(f"Tests Failed: {executive['total_failed']}")
    
    # Display performance metrics
    print("\n🚀 Performance Metrics:")
    print("-" * 25)
    perf_metrics = report['performance_testing'].get('performance_metrics', {})
    if perf_metrics:
        print(f"Average Execution Time: {perf_metrics.get('average_execution_time', 0):.2f}s")
        print(f"Max Memory Usage: {perf_metrics.get('memory_usage', {}).get('max_mb', 0):.2f}MB")
        print(f"Max CPU Usage: {perf_metrics.get('cpu_usage', {}).get('max_percent', 0):.1f}%")
        print(f"Average Response Time: {perf_metrics.get('response_times', {}).get('average_ms', 0):.2f}ms")
    
    # Display compliance status
    print("\n🔒 Compliance Status:")
    print("-" * 20)
    compliance_status = report['compliance_testing'].get('compliance_status', {})
    for regulation, status in compliance_status.items():
        compliant = "✅ COMPLIANT" if status.get('compliant') else "❌ NON-COMPLIANT"
        percentage = status.get('compliance_percentage', 0)
        print(f"{regulation.upper()}: {compliant} ({percentage:.1f}%)")
    
    # Display recommendations
    print("\n💡 Recommendations:")
    print("-" * 18)
    recommendations = report.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print(f"\n📁 Test reports saved to: example_test_reports/")


def run_performance_only_example():
    """Run performance testing only example"""
    print("🚀 Performance Testing Example")
    print("=" * 40)
    
    # Initialize test runner
    runner = ComprehensiveTestRunner(output_dir="performance_example_reports")
    
    # Run performance tests only
    print("🔄 Running performance tests...")
    results = runner.run_performance_tests()
    
    # Display performance results
    print(f"\n📊 Performance Test Results:")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    
    # Display detailed metrics
    metrics = results.get('performance_metrics', {})
    if metrics:
        print(f"\n📈 Performance Metrics:")
        print(f"Average Execution Time: {metrics.get('average_execution_time', 0):.2f}s")
        print(f"Max Memory Usage: {metrics.get('memory_usage', {}).get('max_mb', 0):.2f}MB")
        print(f"Max CPU Usage: {metrics.get('cpu_usage', {}).get('max_percent', 0):.1f}%")
        print(f"Average Throughput: {metrics.get('average_throughput', 0):.2f} ops/sec")
    
    print(f"\n📁 Performance reports saved to: performance_example_reports/")


def run_compliance_only_example():
    """Run compliance testing only example"""
    print("🔒 Compliance Testing Example")
    print("=" * 40)
    
    # Initialize test runner
    runner = ComprehensiveTestRunner(output_dir="compliance_example_reports")
    
    # Run compliance tests only
    print("🔄 Running compliance tests...")
    results = runner.run_compliance_tests()
    
    # Display compliance results
    print(f"\n📊 Compliance Test Results:")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    
    # Display compliance status by regulation
    compliance_status = results.get('compliance_status', {})
    if compliance_status:
        print(f"\n📋 Compliance Status by Regulation:")
        for regulation, status in compliance_status.items():
            compliant = "✅ COMPLIANT" if status.get('compliant') else "❌ NON-COMPLIANT"
            percentage = status.get('compliance_percentage', 0)
            tests_passed = status.get('tests_passed', 0)
            tests_total = status.get('tests_total', 0)
            print(f"{regulation.upper()}: {compliant}")
            print(f"  Tests: {tests_passed}/{tests_total} ({percentage:.1f}%)")
            
            # Show violations if any
            violations = status.get('violations', [])
            if violations:
                print(f"  Violations: {', '.join(violations[:3])}")
            print()
    
    print(f"\n📁 Compliance reports saved to: compliance_example_reports/")


def run_custom_thresholds_example():
    """Run tests with custom thresholds example"""
    print("⚙️ Custom Thresholds Example")
    print("=" * 35)
    
    # Initialize test runner with custom thresholds
    runner = ComprehensiveTestRunner(output_dir="custom_thresholds_reports")
    
    # Customize performance thresholds
    runner.performance_thresholds.update({
        'single_operation': 0.5,      # More strict: 0.5s instead of 1.0s
        'memory_usage_mb': 300,       # More strict: 300MB instead of 500MB
        'cpu_usage_percent': 70,      # More strict: 70% instead of 80%
        'response_time_ms': 1500      # More strict: 1.5s instead of 2.0s
    })
    
    print("🔄 Running tests with custom thresholds...")
    print(f"Custom thresholds:")
    print(f"  Single operation: {runner.performance_thresholds['single_operation']}s")
    print(f"  Memory usage: {runner.performance_thresholds['memory_usage_mb']}MB")
    print(f"  CPU usage: {runner.performance_thresholds['cpu_usage_percent']}%")
    print(f"  Response time: {runner.performance_thresholds['response_time_ms']}ms")
    
    # Run tests
    report = runner.generate_comprehensive_report()
    
    # Display results
    executive = report['executive_summary']
    print(f"\n📊 Results with Custom Thresholds:")
    print(f"Overall Status: {executive['overall_status']}")
    print(f"Performance Status: {executive['performance_status']}")
    
    # Show if any tests failed due to stricter thresholds
    perf_results = report['performance_testing']
    if perf_results.get('tests_failed', 0) > 0:
        print(f"\n⚠️ {perf_results['tests_failed']} performance tests failed with stricter thresholds")
        print("Consider adjusting thresholds or optimizing performance")
    
    print(f"\n📁 Custom threshold reports saved to: custom_thresholds_reports/")


def main():
    """Main function to run examples"""
    print("🎯 MINGUS Comprehensive Testing Examples")
    print("=" * 50)
    
    while True:
        print("\nChoose an example to run:")
        print("1. Basic Comprehensive Testing")
        print("2. Performance Testing Only")
        print("3. Compliance Testing Only")
        print("4. Custom Thresholds Testing")
        print("5. Run All Examples")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            run_basic_example()
        elif choice == '2':
            run_performance_only_example()
        elif choice == '3':
            run_compliance_only_example()
        elif choice == '4':
            run_custom_thresholds_example()
        elif choice == '5':
            print("\n🔄 Running all examples...")
            run_basic_example()
            print("\n" + "="*50)
            run_performance_only_example()
            print("\n" + "="*50)
            run_compliance_only_example()
            print("\n" + "="*50)
            run_custom_thresholds_example()
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter a number between 1-6.")
        
        if choice in ['1', '2', '3', '4', '5']:
            input("\nPress Enter to continue...")


if __name__ == '__main__':
    main() 