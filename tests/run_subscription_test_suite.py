#!/usr/bin/env python3
"""
MINGUS Application - Subscription Test Suite Runner
==================================================

Test runner script for the comprehensive MINGUS subscription system tests.
Provides detailed reporting, coverage analysis, and performance metrics.

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import pytest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.subscription_tests import TestSubscriptionSystem


class SubscriptionTestRunner:
    """Test runner for the MINGUS subscription system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the test runner.
        
        Args:
            config: Configuration dictionary for test execution
        """
        self.config = config or {}
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # Test categories and their descriptions
        self.test_categories = {
            'subscription_creation': 'Subscription creation and setup',
            'subscription_lifecycle': 'Subscription lifecycle management',
            'billing_scenarios': 'Billing scenarios and calculations',
            'payment_recovery': 'Payment failure and recovery',
            'webhook_handling': 'Webhook processing and integration',
            'feature_access': 'Feature access control and usage tracking',
            'customer_portal': 'Customer portal functionality',
            'revenue_optimization': 'Revenue optimization features',
            'automated_workflows': 'Automated workflow scenarios',
            'edge_cases': 'Edge cases and error handling',
            'performance': 'Performance and load testing',
            'security': 'Security and compliance testing'
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all subscription system tests."""
        print("🚀 Starting MINGUS Subscription System Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Configure pytest arguments
        pytest_args = [
            'tests/subscription_tests.py',
            '-v',  # Verbose output
            '--tb=short',  # Short traceback format
            '--durations=10',  # Show 10 slowest tests
            '--strict-markers',  # Strict marker checking
            '--disable-warnings',  # Disable warnings
            '--color=yes'  # Colored output
        ]
        
        # Add coverage if requested
        if self.config.get('coverage', False):
            pytest_args.extend([
                '--cov=backend',
                '--cov-report=html:coverage_html',
                '--cov-report=term-missing',
                '--cov-fail-under=80'
            ])
        
        # Add performance profiling if requested
        if self.config.get('profile', False):
            pytest_args.extend([
                '--profile',
                '--profile-svg'
            ])
        
        # Run the tests
        try:
            exit_code = pytest.main(pytest_args)
            self.results['exit_code'] = exit_code
            self.results['success'] = exit_code == 0
        except Exception as e:
            self.results['exit_code'] = 1
            self.results['success'] = False
            self.results['error'] = str(e)
        
        self.end_time = time.time()
        self.results['execution_time'] = self.end_time - self.start_time
        
        return self.results
    
    def run_category_tests(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category."""
        print(f"🎯 Running {category} tests...")
        
        pytest_args = [
            'tests/subscription_tests.py',
            f'Test{category.replace("_", "").title()}',
            '-v',
            '--tb=short'
        ]
        
        start_time = time.time()
        exit_code = pytest.main(pytest_args)
        end_time = time.time()
        
        return {
            'category': category,
            'success': exit_code == 0,
            'exit_code': exit_code,
            'execution_time': end_time - start_time
        }
    
    def run_specific_test(self, test_name: str) -> Dict[str, Any]:
        """Run a specific test by name."""
        print(f"🎯 Running test: {test_name}")
        
        pytest_args = [
            'tests/subscription_tests.py',
            f'::{test_name}',
            '-v',
            '--tb=short'
        ]
        
        start_time = time.time()
        exit_code = pytest.main(pytest_args)
        end_time = time.time()
        
        return {
            'test_name': test_name,
            'success': exit_code == 0,
            'exit_code': exit_code,
            'execution_time': end_time - start_time
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance-focused tests."""
        print("⚡ Running performance tests...")
        
        performance_tests = [
            'test_bulk_subscription_processing',
            'test_concurrent_webhook_processing',
            'test_concurrent_subscription_creation'
        ]
        
        results = {}
        for test_name in performance_tests:
            results[test_name] = self.run_specific_test(test_name)
        
        return results
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-focused tests."""
        print("🔒 Running security tests...")
        
        security_tests = [
            'test_webhook_signature_verification',
            'test_payment_data_encryption',
            'test_audit_logging',
            'test_pci_compliance_validation'
        ]
        
        results = {}
        for test_name in security_tests:
            results[test_name] = self.run_specific_test(test_name)
        
        return results
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        if not self.results:
            return "No test results available."
        
        report = []
        report.append("📊 MINGUS Subscription System Test Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Execution Time: {self.results.get('execution_time', 0):.2f} seconds")
        report.append(f"Overall Status: {'✅ PASSED' if self.results.get('success') else '❌ FAILED'}")
        report.append("")
        
        # Test category summary
        report.append("📋 Test Categories:")
        for category, description in self.test_categories.items():
            report.append(f"  • {category}: {description}")
        
        report.append("")
        
        # Performance metrics
        if 'execution_time' in self.results:
            report.append("⚡ Performance Metrics:")
            report.append(f"  • Total Execution Time: {self.results['execution_time']:.2f} seconds")
            report.append(f"  • Average Test Time: {self.results['execution_time'] / 50:.2f} seconds per test")
        
        report.append("")
        
        # Recommendations
        report.append("💡 Recommendations:")
        if self.results.get('success'):
            report.append("  • All tests passed successfully!")
            report.append("  • The subscription system is ready for production deployment.")
        else:
            report.append("  • Some tests failed. Please review the failures.")
            report.append("  • Check the detailed test output for specific issues.")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None) -> str:
        """Save test results to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"subscription_test_results_{timestamp}.json"
        
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'results': self.results,
            'test_categories': self.test_categories
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        return filename
    
    def print_summary(self):
        """Print a summary of test results."""
        if not self.results:
            print("No test results available.")
            return
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        status = "✅ PASSED" if self.results.get('success') else "❌ FAILED"
        print(f"Overall Status: {status}")
        
        if 'execution_time' in self.results:
            print(f"Execution Time: {self.results['execution_time']:.2f} seconds")
        
        print(f"Exit Code: {self.results.get('exit_code', 'N/A')}")
        
        if 'error' in self.results:
            print(f"Error: {self.results['error']}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description='Run MINGUS subscription system tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_subscription_test_suite.py                    # Run all tests
  python run_subscription_test_suite.py --category billing # Run billing tests only
  python run_subscription_test_suite.py --test test_name   # Run specific test
  python run_subscription_test_suite.py --coverage         # Run with coverage
  python run_subscription_test_suite.py --performance      # Run performance tests
  python run_subscription_test_suite.py --security         # Run security tests
        """
    )
    
    parser.add_argument(
        '--category',
        choices=list(SubscriptionTestRunner({}).test_categories.keys()),
        help='Run tests for a specific category'
    )
    
    parser.add_argument(
        '--test',
        help='Run a specific test by name'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage reporting'
    )
    
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Run tests with performance profiling'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Run performance-focused tests only'
    )
    
    parser.add_argument(
        '--security',
        action='store_true',
        help='Run security-focused tests only'
    )
    
    parser.add_argument(
        '--save-results',
        help='Save test results to specified file'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate and display detailed report'
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    config = {
        'coverage': args.coverage,
        'profile': args.profile
    }
    
    runner = SubscriptionTestRunner(config)
    
    try:
        # Run tests based on arguments
        if args.performance:
            results = runner.run_performance_tests()
        elif args.security:
            results = runner.run_security_tests()
        elif args.category:
            results = runner.run_category_tests(args.category)
        elif args.test:
            results = runner.run_specific_test(args.test)
        else:
            results = runner.run_all_tests()
        
        # Generate and display report
        if args.report:
            report = runner.generate_report()
            print("\n" + report)
        
        # Save results if requested
        if args.save_results:
            filename = runner.save_results(args.save_results)
            print(f"\n💾 Test results saved to: {filename}")
        
        # Print summary
        runner.print_summary()
        
        # Exit with appropriate code
        if isinstance(results, dict) and results.get('success') is False:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 