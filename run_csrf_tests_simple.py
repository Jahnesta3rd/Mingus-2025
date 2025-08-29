#!/usr/bin/env python3
"""
Simplified CSRF Protection Testing Runner
========================================

This script provides a simple way to run CSRF protection tests
with clear instructions for different scenarios.

Author: Security Testing Team
Date: January 2025
"""

import os
import sys
import json
import argparse
from datetime import datetime

def check_app_running(base_url):
    """Check if the application is running"""
    try:
        import requests
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_demo_mode():
    """Run the demo mode to show capabilities"""
    print("🎭 Running CSRF Protection Testing in Demo Mode")
    print("=" * 60)
    
    try:
        from demo_csrf_testing import main as demo_main
        demo_main()
        return True
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        return False

def run_live_tests(base_url, secret_key, timeout=30, concurrent=5):
    """Run tests against a live application"""
    print(f"🚀 Running CSRF Protection Tests against: {base_url}")
    print("=" * 60)
    
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
        
    except Exception as e:
        print(f"❌ Error running live tests: {e}")
        return None

def show_instructions():
    """Show instructions for running tests"""
    print("\n📖 CSRF Protection Testing Instructions")
    print("=" * 60)
    
    print("\n1. 🎭 DEMO MODE (No application required):")
    print("   python run_csrf_tests_simple.py --demo")
    print()
    
    print("2. 🚀 LIVE TESTING (Application must be running):")
    print("   # First, start your Flask application:")
    print("   cd backend")
    print("   python app.py")
    print()
    print("   # Then run the tests:")
    print("   python run_csrf_tests_simple.py \\")
    print("     --base-url http://localhost:5001 \\")
    print("     --secret-key your-secret-key")
    print()
    
    print("3. 🔧 ADVANCED CONFIGURATION:")
    print("   python run_csrf_tests_simple.py \\")
    print("     --base-url https://your-app.com \\")
    print("     --secret-key your-secret-key \\")
    print("     --timeout 60 \\")
    print("     --concurrent 10")
    print()
    
    print("4. 📊 VIEW RESULTS:")
    print("   - JSON report: csrf_protection_test_report_YYYYMMDD_HHMMSS.json")
    print("   - Summary report: csrf_test_summary_YYYYMMDD_HHMMSS.md")
    print()
    
    print("5. 🔍 TROUBLESHOOTING:")
    print("   - Ensure your application is running and accessible")
    print("   - Check that the base URL is correct")
    print("   - Verify the secret key matches your application's configuration")
    print("   - Check network connectivity and firewall settings")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Simplified CSRF Protection Testing')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    parser.add_argument('--base-url', help='Base URL of the application')
    parser.add_argument('--secret-key', help='Secret key for CSRF token generation')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--concurrent', type=int, default=5, help='Number of concurrent requests')
    parser.add_argument('--check-app', action='store_true', help='Check if application is running')
    
    args = parser.parse_args()
    
    # Check if application is running
    if args.check_app and args.base_url:
        print(f"🔍 Checking if application is running at: {args.base_url}")
        if check_app_running(args.base_url):
            print("✅ Application is running and accessible!")
        else:
            print("❌ Application is not running or not accessible")
            print("Please start your Flask application first:")
            print("cd backend && python app.py")
        return
    
    # Run demo mode
    if args.demo:
        run_demo_mode()
        return
    
    # Run live tests
    if args.base_url and args.secret_key:
        # Check if app is running
        if not check_app_running(args.base_url):
            print("❌ Application is not running or not accessible")
            print(f"Please ensure your application is running at: {args.base_url}")
            print("\nTo start your application:")
            print("cd backend")
            print("python app.py")
            return
        
        # Run tests
        report = run_live_tests(args.base_url, args.secret_key, args.timeout, args.concurrent)
        
        if report:
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
    
    # Show instructions if no valid arguments
    show_instructions()

if __name__ == '__main__':
    sys.exit(main())
