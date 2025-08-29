#!/usr/bin/env python3
"""
Subscription System Test Runner
==============================

This script runs comprehensive tests for the MINGUS subscription system.
It handles test setup, execution, and reporting.

Usage:
    python run_subscription_tests.py [options]

Options:
    --tier <tier>          Test specific tier (budget, mid, professional, all)
    --category <category>  Test specific category (signup, payment, webhook, security, all)
    --verbose              Enable verbose output
    --report-only          Generate report from existing results
    --save-results         Save detailed test results
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_subscription_system import SubscriptionSystemTester

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'subscription_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run MINGUS subscription system tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_subscription_tests.py --tier all --category all
  python run_subscription_tests.py --tier budget --category signup
  python run_subscription_tests.py --verbose --save-results
        """
    )
    
    parser.add_argument(
        '--tier',
        choices=['budget', 'mid', 'professional', 'all'],
        default='all',
        help='Test specific subscription tier (default: all)'
    )
    
    parser.add_argument(
        '--category',
        choices=['signup', 'payment', 'webhook', 'security', 'all'],
        default='all',
        help='Test specific category (default: all)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed test results to file'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from existing results file'
    )
    
    parser.add_argument(
        '--results-file',
        type=str,
        help='Path to existing results file for report generation'
    )
    
    return parser.parse_args()

def filter_tests_by_tier(tester, tier):
    """Filter tests based on tier selection"""
    if tier == 'all':
        return tester
    
    tier_tests = {
        'budget': [
            'Budget Tier Signup',
            'Payment Processing Success',
            'Subscription Upgrade',
            'Payment Failure Handling',
            'Invoice Generation',
            'Subscription Created Webhook',
            'Webhook Signature Verification'
        ],
        'mid': [
            'Mid-Tier Signup',
            'Payment Processing Success',
            'Subscription Upgrade',
            'Subscription Downgrade',
            'Payment Failure Handling',
            'Invoice Generation',
            'Subscription Updated Webhook',
            'Webhook Signature Verification'
        ],
        'professional': [
            'Professional Tier Signup',
            'Payment Processing Success',
            'Subscription Downgrade',
            'Payment Failure Handling',
            'Invoice Generation',
            'Subscription Cancelled Webhook',
            'Webhook Signature Verification'
        ]
    }
    
    # Filter test methods based on tier
    filtered_tester = SubscriptionSystemTester()
    filtered_tester.results = []
    
    for test_name in tier_tests.get(tier, []):
        # Find corresponding test method
        test_method_name = test_name.lower().replace(' ', '_').replace('-', '_')
        if hasattr(tester, f'test_{test_method_name}'):
            test_method = getattr(tester, f'test_{test_method_name}')
            filtered_tester.run_test(test_method, test_name)
    
    return filtered_tester

def filter_tests_by_category(tester, category):
    """Filter tests based on category selection"""
    if category == 'all':
        return tester
    
    category_tests = {
        'signup': [
            'Budget Tier Signup',
            'Mid-Tier Signup',
            'Professional Tier Signup'
        ],
        'payment': [
            'Payment Processing Success',
            'Payment Confirmation Webhook',
            'Payment Failure Handling',
            'Payment Failure Webhook',
            'Invoice Generation',
            'Invoice Email Delivery'
        ],
        'webhook': [
            'Payment Confirmation Webhook',
            'Payment Failure Webhook',
            'Subscription Created Webhook',
            'Subscription Updated Webhook',
            'Subscription Cancelled Webhook'
        ],
        'security': [
            'Webhook Signature Verification',
            'Payment Method Validation',
            'Customer Data Encryption'
        ]
    }
    
    # Filter test methods based on category
    filtered_tester = SubscriptionSystemTester()
    filtered_tester.results = []
    
    for test_name in category_tests.get(category, []):
        # Find corresponding test method
        test_method_name = test_name.lower().replace(' ', '_').replace('-', '_')
        if hasattr(tester, f'test_{test_method_name}'):
            test_method = getattr(tester, f'test_{test_method_name}')
            filtered_tester.run_test(test_method, test_name)
    
    return filtered_tester

def generate_markdown_report(report_data, output_file=None):
    """Generate a markdown report from test results"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown_content = f"""# MINGUS Subscription System Test Report

**Generated:** {timestamp}

## 📊 Executive Summary

- **Total Tests:** {report_data['summary']['total_tests']}
- **Passed:** {report_data['summary']['passed_tests']}
- **Failed:** {report_data['summary']['failed_tests']}
- **Success Rate:** {report_data['summary']['success_rate']:.1f}%
- **Average Duration:** {report_data['summary']['average_duration']:.2f}s

## 📈 Category Breakdown

"""
    
    for category, stats in report_data['categories'].items():
        status_emoji = "✅" if stats['success_rate'] >= 90 else "⚠️" if stats['success_rate'] >= 70 else "❌"
        markdown_content += f"### {category.title()} {status_emoji}\n"
        markdown_content += f"- **Tests:** {stats['passed']}/{stats['total']}\n"
        markdown_content += f"- **Success Rate:** {stats['success_rate']:.1f}%\n\n"
    
    markdown_content += "## 📋 Detailed Results\n\n"
    
    for result in report_data['detailed_results']:
        status_emoji = "✅" if result['success'] else "❌"
        markdown_content += f"### {status_emoji} {result['test_name']}\n"
        markdown_content += f"- **Status:** {'PASSED' if result['success'] else 'FAILED'}\n"
        markdown_content += f"- **Duration:** {result['duration']:.2f}s\n"
        markdown_content += f"- **Message:** {result['message']}\n"
        
        if result['details']:
            markdown_content += "- **Details:**\n"
            for key, value in result['details'].items():
                markdown_content += f"  - {key}: {value}\n"
        
        markdown_content += "\n"
    
    if report_data['recommendations']:
        markdown_content += "## 💡 Recommendations\n\n"
        for rec in report_data['recommendations']:
            markdown_content += f"- {rec}\n"
        markdown_content += "\n"
    
    # Overall assessment
    success_rate = report_data['summary']['success_rate']
    if success_rate >= 95:
        markdown_content += "## 🎉 Overall Assessment\n\n**EXCELLENT** - System is ready for production!\n"
    elif success_rate >= 90:
        markdown_content += "## ✅ Overall Assessment\n\n**GOOD** - System is ready for production with minor improvements.\n"
    elif success_rate >= 80:
        markdown_content += "## ⚠️ Overall Assessment\n\n**FAIR** - System needs improvements before production.\n"
    else:
        markdown_content += "## ❌ Overall Assessment\n\n**POOR** - System needs significant work before production.\n"
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        print(f"📄 Markdown report saved to: {output_file}")
    
    return markdown_content

def main():
    """Main function"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.report_only:
            # Generate report from existing results
            if not args.results_file:
                print("❌ Error: --results-file is required when using --report-only")
                return 1
            
            if not os.path.exists(args.results_file):
                print(f"❌ Error: Results file not found: {args.results_file}")
                return 1
            
            with open(args.results_file, 'r') as f:
                report_data = json.load(f)
            
            # Generate markdown report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            markdown_file = f"subscription_test_report_{timestamp}.md"
            generate_markdown_report(report_data, markdown_file)
            
            return 0
        
        # Run tests
        logger.info("🚀 Starting MINGUS Subscription System Tests")
        logger.info(f"Tier: {args.tier}, Category: {args.category}")
        
        # Initialize tester
        tester = SubscriptionSystemTester()
        
        # Run comprehensive tests
        if args.tier == 'all' and args.category == 'all':
            report = tester.run_comprehensive_tests()
        else:
            # Filter tests based on arguments
            if args.tier != 'all':
                tester = filter_tests_by_tier(tester, args.tier)
            
            if args.category != 'all':
                tester = filter_tests_by_category(tester, args.category)
            
            report = tester.generate_test_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SUBSCRIPTION SYSTEM TEST RESULTS")
        print("=" * 60)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Average Duration: {summary['average_duration']:.2f}s")
        
        print("\n📈 CATEGORY BREAKDOWN:")
        for category, stats in report['categories'].items():
            status_emoji = "✅" if stats['success_rate'] >= 90 else "⚠️" if stats['success_rate'] >= 70 else "❌"
            print(f"  {status_emoji} {category.title()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save results if requested
        if args.save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"subscription_test_results_{timestamp}.json"
            
            with open(results_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n📄 Detailed results saved to: {results_filename}")
        
        # Generate markdown report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        markdown_file = f"subscription_test_report_{timestamp}.md"
        generate_markdown_report(report, markdown_file)
        
        # Return exit code based on success rate
        if summary['success_rate'] >= 90:
            print("\n✅ Subscription system is ready for production!")
            return 0
        else:
            print("\n❌ Subscription system needs attention before production!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Test runner failed: {str(e)}")
        print(f"\n💥 Test runner failed: {str(e)}")
        return 1
    finally:
        # Cleanup
        if 'tester' in locals():
            tester.cleanup()

if __name__ == "__main__":
    exit(main())
