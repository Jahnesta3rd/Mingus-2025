#!/usr/bin/env python3
"""
MINGUS Mobile Demographic Test Runner
====================================

Easy-to-use test runner for mobile demographic testing suite.
Provides various options for testing different aspects of the mobile experience.

Usage:
    python run_mobile_demographic_tests.py [options]

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from typing import List, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_mobile_demographic_experience import (
    MobileDemographicTester, 
    DeviceProfile, 
    NetworkCondition
)


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'selenium',
        'psutil',
        'requests',
        'dataclasses',
        'json'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall dependencies with:")
        print("pip install -r requirements-mobile-demographic-testing.txt")
        return False
    
    return True


def check_chrome_driver():
    """Check if Chrome driver is available."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Chrome driver not available: {e}")
        print("\nInstall Chrome driver with:")
        print("pip install webdriver-manager")
        return False


def start_local_server():
    """Start local development server if needed."""
    print("🔧 Checking if local server is running...")
    
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Local server is running")
            return True
    except:
        pass
    
    print("⚠️  Local server not detected")
    print("Make sure your MINGUS application is running on http://localhost:5000")
    print("Or set MINGUS_BASE_URL environment variable to your server URL")
    
    return False


def run_specific_tests(tester: MobileDemographicTester, test_types: List[str], device_profiles: List[DeviceProfile]):
    """Run specific types of tests."""
    results = []
    
    for device_profile in device_profiles:
        print(f"\n📱 Testing device profile: {device_profile.value}")
        
        for test_type in test_types:
            print(f"  🔍 Running {test_type}...")
            
            if test_type == "performance":
                result = tester.test_mobile_performance(device_profile)
            elif test_type == "touch":
                result = tester.test_touch_interactions(device_profile)
            elif test_type == "offline":
                result = tester.test_offline_functionality(device_profile)
            elif test_type == "payment":
                result = tester.test_mobile_payment_processing(device_profile)
            elif test_type == "adaptation":
                result = tester.test_screen_adaptation(device_profile)
            elif test_type == "budget":
                result = tester.test_budget_device_performance(device_profile)
            else:
                print(f"  ⚠️  Unknown test type: {test_type}")
                continue
            
            results.append(result)
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} {test_type}")
    
    return results


def generate_summary_report(results: List, output_format: str = "json"):
    """Generate summary report in specified format."""
    if not results:
        print("⚠️  No test results to report")
        return
    
    # Calculate summary statistics
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result.passed)
    failed_tests = total_tests - passed_tests
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    # Group by device profile
    device_stats = {}
    for result in results:
        device = result.device_profile
        if device not in device_stats:
            device_stats[device] = {"passed": 0, "total": 0}
        device_stats[device]["total"] += 1
        if result.passed:
            device_stats[device]["passed"] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("📊 MOBILE DEMOGRAPHIC TESTING SUMMARY")
    print("="*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {success_rate:.1%}")
    
    print("\n📱 Device Performance:")
    for device, stats in device_stats.items():
        device_success_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {device}: {stats['passed']}/{stats['total']} tests passed ({device_success_rate:.1%})")
    
    # Show critical issues
    all_issues = []
    for result in results:
        all_issues.extend(result.issues)
    
    if all_issues:
        unique_issues = list(set(all_issues))
        print(f"\n⚠️  Critical Issues Found ({len(unique_issues)}):")
        for issue in unique_issues[:5]:  # Show first 5
            print(f"  • {issue}")
    
    # Show recommendations
    all_recommendations = []
    for result in results:
        all_recommendations.extend(result.recommendations)
    
    if all_recommendations:
        unique_recommendations = list(set(all_recommendations))
        print(f"\n💡 Recommendations ({len(unique_recommendations)}):")
        for rec in unique_recommendations[:5]:  # Show first 5
            print(f"  • {rec}")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == "json":
        import json
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "test_date": datetime.now().isoformat()
            },
            "device_statistics": device_stats,
            "critical_issues": list(set(all_issues)),
            "recommendations": list(set(all_recommendations)),
            "detailed_results": [result.__dict__ for result in results]
        }
        
        report_filename = f"mobile_demographic_summary_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
    
    return success_rate


def main():
    """Main function for the test runner."""
    parser = argparse.ArgumentParser(
        description="MINGUS Mobile Demographic Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests on all device profiles
  python run_mobile_demographic_tests.py

  # Run only performance tests
  python run_mobile_demographic_tests.py --tests performance

  # Test only budget devices
  python run_mobile_demographic_tests.py --devices budget_android budget_iphone

  # Run specific test types on specific devices
  python run_mobile_demographic_tests.py --tests performance touch --devices budget_android

  # Use custom server URL
  python run_mobile_demographic_tests.py --url https://your-mingus-app.com
        """
    )
    
    parser.add_argument(
        "--tests",
        nargs="+",
        choices=["performance", "touch", "offline", "payment", "adaptation", "budget"],
        default=["performance", "touch", "offline", "payment", "adaptation", "budget"],
        help="Types of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--devices",
        nargs="+",
        choices=["budget_android", "budget_iphone", "mid_android", "mid_iphone", "older_device"],
        default=["budget_android", "budget_iphone", "older_device"],
        help="Device profiles to test (default: budget and older devices)"
    )
    
    parser.add_argument(
        "--url",
        default=os.getenv("MINGUS_BASE_URL", "http://localhost:5000"),
        help="Base URL for testing (default: http://localhost:5000)"
    )
    
    parser.add_argument(
        "--output",
        choices=["json", "html", "console"],
        default="json",
        help="Output format for reports (default: json)"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip dependency and server checks"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests (fewer viewport sizes, faster timeouts)"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("🚀 MINGUS Mobile Demographic Experience Testing Suite")
    print("=" * 60)
    print("Testing mobile experience for target demographic:")
    print("- African American professionals aged 25-45")
    print("- Income range: $40K-$80K")
    print("- Budget/older mobile devices")
    print("- Mobile-first usage patterns")
    print("=" * 60)
    
    # Check dependencies and setup
    if not args.skip_checks:
        print("\n🔧 Checking dependencies...")
        if not check_dependencies():
            return 1
        
        print("\n🔧 Checking Chrome driver...")
        if not check_chrome_driver():
            return 1
        
        print("\n🔧 Checking server availability...")
        if not start_local_server():
            print("⚠️  Continuing anyway - make sure your server is accessible")
    
    # Convert device names to DeviceProfile enums
    device_profiles = []
    for device_name in args.devices:
        try:
            device_profile = DeviceProfile(device_name)
            device_profiles.append(device_profile)
        except ValueError:
            print(f"⚠️  Unknown device profile: {device_name}")
    
    if not device_profiles:
        print("❌ No valid device profiles specified")
        return 1
    
    # Initialize tester
    print(f"\n🎯 Initializing tester for: {args.url}")
    tester = MobileDemographicTester(args.url)
    
    # Adjust settings for quick mode
    if args.quick:
        print("⚡ Quick mode enabled - running faster tests")
        tester.target_specs["max_page_load_time"] = 5.0  # More lenient
        tester.target_specs["max_first_paint"] = 2.0
    
    try:
        # Run tests
        print(f"\n🧪 Running tests: {', '.join(args.tests)}")
        print(f"📱 Device profiles: {', '.join([d.value for d in device_profiles])}")
        
        start_time = time.time()
        results = run_specific_tests(tester, args.tests, device_profiles)
        end_time = time.time()
        
        # Generate report
        print(f"\n📊 Generating report (took {end_time - start_time:.1f}s)...")
        success_rate = generate_summary_report(results, args.output)
        
        # Return appropriate exit code
        if success_rate >= 0.8:
            print("\n✅ Mobile experience meets target demographic requirements!")
            return 0
        else:
            print("\n❌ Mobile experience needs improvement for target demographic.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
