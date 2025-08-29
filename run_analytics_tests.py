#!/usr/bin/env python3
"""
Analytics and Insights Testing Runner
====================================

This script runs the comprehensive analytics and insights testing suite for the MINGUS application.

Usage:
    python run_analytics_tests.py [options]

Options:
    --quick          Run quick tests only (reduced data set)
    --full           Run full test suite (default)
    --report-only    Generate report from existing test data
    --verbose        Enable verbose output
    --save-results   Save detailed results to files
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_analytics_and_insights_features import AnalyticsTestSuite, TEST_CONFIG

def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive analytics and insights testing suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_analytics_tests.py                    # Run full test suite
    python run_analytics_tests.py --quick           # Run quick tests
    python run_analytics_tests.py --verbose         # Run with verbose output
    python run_analytics_tests.py --save-results    # Save detailed results
        """
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (reduced data set)'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full test suite (default)'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from existing test data'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed results to files'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='analytics_test_results',
        help='Output directory for test results (default: analytics_test_results)'
    )
    
    return parser

def setup_test_environment(args):
    """Setup test environment and configuration"""
    print("🔧 Setting up test environment...")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Modify test configuration based on arguments
    if args.quick:
        TEST_CONFIG['test_user_count'] = 20
        TEST_CONFIG['test_days'] = 7
        print("⚡ Quick test mode: Reduced data set")
    else:
        print("🐌 Full test mode: Complete data set")
    
    # Setup logging
    if args.verbose:
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return output_dir

def run_analytics_tests(args, output_dir):
    """Run the analytics testing suite"""
    print("\n🚀 Starting Analytics and Insights Testing Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Initialize test suite
        test_suite = AnalyticsTestSuite()
        
        # Run tests
        results = test_suite.run_all_tests()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Generate additional reports if requested
        if args.save_results:
            save_detailed_results(results, output_dir)
        
        # Print execution summary
        print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
        
        return results, execution_time
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return None, time.time() - start_time

def save_detailed_results(results, output_dir):
    """Save detailed test results to files"""
    print(f"\n💾 Saving detailed results to {output_dir}...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save main results
    results_file = output_dir / f"analytics_test_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate individual test reports
    for test_name, test_result in results.items():
        if test_result.get('status') == 'PASSED':
            # Save detailed metrics for passed tests
            metrics_file = output_dir / f"{test_name}_metrics_{timestamp}.json"
            with open(metrics_file, 'w') as f:
                json.dump(test_result, f, indent=2, default=str)
    
    # Generate summary report
    summary_file = output_dir / f"test_summary_{timestamp}.md"
    generate_summary_report(results, summary_file, timestamp)
    
    print(f"✅ Results saved to {output_dir}")

def generate_summary_report(results, summary_file, timestamp):
    """Generate a markdown summary report"""
    with open(summary_file, 'w') as f:
        f.write("# Analytics and Insights Testing Summary Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Test Run ID:** {timestamp}\n\n")
        
        # Overall summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get('status') == 'PASSED')
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        f.write("## Overall Results\n\n")
        f.write(f"- **Total Tests:** {total_tests}\n")
        f.write(f"- **Passed:** {passed_tests} ✅\n")
        f.write(f"- **Failed:** {failed_tests} ❌\n")
        f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")
        
        # Detailed results
        f.write("## Test Results\n\n")
        for test_name, result in results.items():
            status = "✅ PASSED" if result.get('status') == 'PASSED' else "❌ FAILED"
            f.write(f"### {test_name.replace('_', ' ').title()}\n")
            f.write(f"**Status:** {status}\n\n")
            
            if result.get('error'):
                f.write(f"**Error:** {result['error']}\n\n")
            else:
                # Add key metrics
                for key, value in result.items():
                    if key != 'status' and isinstance(value, (int, float, str)):
                        f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        if failed_tests > 0:
            f.write("### Issues to Address\n")
            for test_name, result in results.items():
                if result.get('status') == 'FAILED':
                    f.write(f"- **{test_name.replace('_', ' ').title()}:** {result.get('error', 'Unknown error')}\n")
            f.write("\n")
        
        f.write("### Next Steps\n")
        f.write("- Review failed tests and implement fixes\n")
        f.write("- Analyze performance metrics for optimization opportunities\n")
        f.write("- Consider expanding test coverage for edge cases\n")
        f.write("- Monitor analytics data quality and accuracy\n")

def print_final_summary(results, execution_time):
    """Print final test summary"""
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    if results:
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get('status') == 'PASSED')
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Execution Time: {execution_time:.2f} seconds")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test_name, result in results.items():
                if result.get('status') == 'FAILED':
                    print(f"  - {test_name.replace('_', ' ').title()}: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        
        # Exit with appropriate code
        return 0 if failed_tests == 0 else 1
    else:
        print("❌ Test execution failed")
        return 1

def main():
    """Main function"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    print("🎯 MINGUS Analytics and Insights Testing Suite")
    print("=" * 60)
    
    # Setup environment
    output_dir = setup_test_environment(args)
    
    # Run tests
    results, execution_time = run_analytics_tests(args, output_dir)
    
    # Print final summary
    exit_code = print_final_summary(results, execution_time)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
