#!/usr/bin/env python3
"""
Communication Features Test Runner
Sets up environment and runs comprehensive communication tests
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

def setup_environment():
    """Setup test environment variables"""
    # Set default test values if not already set
    if not os.getenv('TEST_EMAIL'):
        os.environ['TEST_EMAIL'] = 'test@example.com'
    
    if not os.getenv('TEST_PHONE'):
        os.environ['TEST_EMAIL'] = '+1234567890'
    
    # Set test mode
    os.environ['TESTING_MODE'] = 'true'
    
    # Disable actual API calls in test mode (optional)
    os.environ['MOCK_EXTERNAL_APIS'] = 'true'

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    requirements_file = "requirements-communication-testing.txt"
    if Path(requirements_file).exists():
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    else:
        print(f"⚠️ Requirements file {requirements_file} not found")
    
    return True

def run_tests(test_type="all", verbose=False, save_report=True):
    """Run communication tests"""
    print("🚀 Starting Communication Features Test Suite")
    print("=" * 60)
    
    # Import and run test suite
    try:
        from test_communication_features import CommunicationFeaturesTestSuite
        
        # Initialize test suite
        test_suite = CommunicationFeaturesTestSuite()
        
        # Run tests based on type
        if test_type == "email":
            print("📧 Running Email Tests Only")
            test_suite.test_email_delivery()
            test_suite.test_email_templates()
        elif test_type == "sms":
            print("📱 Running SMS Tests Only")
            test_suite.test_sms_notifications()
        elif test_type == "routing":
            print("🔄 Running Routing Tests Only")
            test_suite.test_communication_routing()
        elif test_type == "integration":
            print("🔗 Running Integration Tests Only")
            test_suite.test_integration_scenarios()
        else:
            print("🔄 Running All Communication Tests")
            report = test_suite.run_all_tests()
            
            if save_report:
                # Save report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"communication_test_report_{timestamp}.json"
                
                import json
                with open(report_filename, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                print(f"\n📄 Detailed report saved to: {report_filename}")
                
                # Print summary
                summary = report['summary']
                print(f"\n📊 SUMMARY:")
                print(f"Total Tests: {summary['total_tests']}")
                print(f"Successful: {summary['successful_tests']}")
                print(f"Failed: {summary['failed_tests']}")
                print(f"Success Rate: {summary['overall_success_rate']:.1f}%")
                
                return summary['failed_tests'] == 0
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import test suite: {e}")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def run_performance_tests():
    """Run performance tests for communication services"""
    print("⚡ Running Performance Tests")
    
    try:
        # Import performance test module
        from test_communication_features import CommunicationFeaturesTestSuite
        
        test_suite = CommunicationFeaturesTestSuite()
        
        # Run performance-focused tests
        print("📊 Testing Email Performance...")
        start_time = datetime.now()
        test_suite.test_email_delivery()
        email_duration = (datetime.now() - start_time).total_seconds()
        
        print("📊 Testing SMS Performance...")
        start_time = datetime.now()
        test_suite.test_sms_notifications()
        sms_duration = (datetime.now() - start_time).total_seconds()
        
        print("📊 Testing Routing Performance...")
        start_time = datetime.now()
        test_suite.test_communication_routing()
        routing_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⚡ PERFORMANCE RESULTS:")
        print(f"Email Tests: {email_duration:.2f}s")
        print(f"SMS Tests: {sms_duration:.2f}s")
        print(f"Routing Tests: {routing_duration:.2f}s")
        print(f"Total: {email_duration + sms_duration + routing_duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MINGUS Communication Features Test Runner")
    parser.add_argument(
        "--test-type", 
        choices=["all", "email", "sms", "routing", "integration", "performance"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't save detailed report"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before running tests"
    )
    parser.add_argument(
        "--setup-env",
        action="store_true",
        help="Setup test environment variables"
    )
    
    args = parser.parse_args()
    
    # Setup environment if requested
    if args.setup_env:
        setup_environment()
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            return 1
    
    # Run tests
    if args.test_type == "performance":
        success = run_performance_tests()
    else:
        success = run_tests(
            test_type=args.test_type,
            verbose=args.verbose,
            save_report=not args.no_report
        )
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
