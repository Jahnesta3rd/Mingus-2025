#!/usr/bin/env python3
"""
CSRF Protection Testing Runner
=============================

This script runs comprehensive CSRF protection tests on the MINGUS application.

Usage:
    python run_csrf_tests.py --base-url http://localhost:5000 --secret-key your-secret-key

Author: Security Testing Team
Date: January 2025
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'requests',
        'flask',
        'loguru',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print(f"pip install -r requirements-csrf-testing.txt")
        return False
    
    return True

def get_app_config():
    """Get application configuration for testing"""
    config_file = Path("config/config.json")
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file: {e}")
    
    # Default configuration
    return {
        'base_url': 'http://localhost:5000',
        'secret_key': 'your-secret-key-here',
        'timeout': 30,
        'concurrent_requests': 5
    }

def validate_arguments(config):
    """Validate configuration arguments"""
    if not config.get('base_url'):
        print("❌ Base URL is required")
        return False
    
    if not config.get('secret_key'):
        print("❌ Secret key is required")
        return False
    
    # Validate URL format
    if not config['base_url'].startswith(('http://', 'https://')):
        print("❌ Base URL must start with http:// or https://")
        return False
    
    return True

def run_csrf_tests(base_url, secret_key, timeout=30, concurrent=5):
    """Run the CSRF protection tests"""
    print("🚀 Starting CSRF Protection Testing")
    print("=" * 60)
    
    # Import and run tests
    try:
        from test_csrf_protection import CSRFProtectionTester
        
        # Create tester instance
        tester = CSRFProtectionTester(base_url, secret_key)
        
        # Update configuration
        tester.test_config['timeout'] = timeout
        tester.test_config['concurrent_requests'] = concurrent
        
        # Run all tests
        report = tester.run_all_tests()
        
        return report
        
    except ImportError as e:
        print(f"❌ Error importing test module: {e}")
        return None
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return None

def generate_summary_report(report):
    """Generate a summary report"""
    if not report:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = f"csrf_test_summary_{timestamp}.md"
    
    with open(summary_filename, 'w') as f:
        f.write("# CSRF Protection Testing Summary\n\n")
        f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Test Summary
        f.write("## Test Summary\n\n")
        summary = report['test_summary']
        f.write(f"- **Total Tests:** {summary['total_tests']}\n")
        f.write(f"- **Passed:** {summary['passed_tests']} ✅\n")
        f.write(f"- **Failed:** {summary['failed_tests']} ❌\n")
        f.write(f"- **Errors:** {summary['error_tests']} ⚠️\n")
        f.write(f"- **Success Rate:** {summary['success_rate']:.1f}%\n\n")
        
        # Security Assessment
        f.write("## Security Assessment\n\n")
        security = report['security_assessment']
        f.write(f"- **Critical Issues:** {security['critical_issues']}\n")
        f.write(f"- **High Issues:** {security['high_issues']}\n")
        f.write(f"- **Medium Issues:** {security['medium_issues']}\n")
        f.write(f"- **Low Issues:** {security['low_issues']}\n\n")
        
        # Category Breakdown
        f.write("## Test Categories\n\n")
        categories = report['category_breakdown']
        f.write(f"- **Financial Transaction Tests:** {categories['financial_transaction_tests']}\n")
        f.write(f"- **Form Submission Tests:** {categories['form_submission_tests']}\n")
        f.write(f"- **API Endpoint Tests:** {categories['api_endpoint_tests']}\n")
        f.write(f"- **State-Changing Tests:** {categories['state_changing_tests']}\n")
        f.write(f"- **Cross-Origin Tests:** {categories['cross_origin_tests']}\n")
        f.write(f"- **Token Validation Tests:** {categories['token_validation_tests']}\n")
        f.write(f"- **Concurrent Request Tests:** {categories['concurrent_request_tests']}\n\n")
        
        # Failed Tests
        failed_tests = [r for r in report['detailed_results'] if r['status'] == 'FAIL']
        if failed_tests:
            f.write("## Failed Tests\n\n")
            for test in failed_tests:
                f.write(f"### {test['test_name']}\n")
                f.write(f"- **Endpoint:** {test['method']} {test['endpoint']}\n")
                f.write(f"- **Details:** {test['details']}\n")
                f.write(f"- **Security Impact:** {test['security_impact']}\n")
                if test['recommendations']:
                    f.write("- **Recommendations:**\n")
                    for rec in test['recommendations']:
                        f.write(f"  - {rec}\n")
                f.write("\n")
        
        # Recommendations
        if report['recommendations']:
            f.write("## Security Recommendations\n\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")
    
    print(f"📄 Summary report saved to: {summary_filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='CSRF Protection Testing Runner')
    parser.add_argument('--base-url', help='Base URL of the application')
    parser.add_argument('--secret-key', help='Secret key for CSRF token generation')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--concurrent', type=int, default=5, help='Number of concurrent requests')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("📦 Installing required dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-csrf-testing.txt'])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return 1
    
    # Check dependencies
    if not check_dependencies():
        print("\nTo install dependencies, run:")
        print("python run_csrf_tests.py --install-deps")
        return 1
    
    # Get configuration
    config = get_app_config()
    
    # Override with command line arguments
    if args.base_url:
        config['base_url'] = args.base_url
    if args.secret_key:
        config['secret_key'] = args.secret_key
    if args.timeout:
        config['timeout'] = args.timeout
    if args.concurrent:
        config['concurrent_requests'] = args.concurrent
    
    # Validate arguments
    if not validate_arguments(config):
        return 1
    
    print(f"🔧 Configuration:")
    print(f"   Base URL: {config['base_url']}")
    print(f"   Timeout: {config['timeout']}s")
    print(f"   Concurrent Requests: {config['concurrent_requests']}")
    print()
    
    # Run tests
    report = run_csrf_tests(
        base_url=config['base_url'],
        secret_key=config['secret_key'],
        timeout=config['timeout'],
        concurrent=config['concurrent_requests']
    )
    
    if report:
        # Generate summary report
        generate_summary_report(report)
        
        # Check for critical issues
        if report['test_summary']['failed_tests'] > 0 or report['security_assessment']['critical_issues'] > 0:
            print("\n❌ CSRF protection testing found issues that need attention!")
            return 1
        else:
            print("\n✅ CSRF protection testing completed successfully!")
            return 0
    else:
        print("\n❌ CSRF protection testing failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
