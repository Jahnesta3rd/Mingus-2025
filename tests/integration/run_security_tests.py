#!/usr/bin/env python3
"""
MINGUS Security Integration Test Runner
======================================

A convenient script to run security integration tests with various options
for testing, debugging, and performance analysis.

Usage:
    python run_security_tests.py [options]

Examples:
    # Run all security tests
    python run_security_tests.py

    # Run only security integration tests
    python run_security_tests.py --security-only

    # Run only compliance tests
    python run_security_tests.py --compliance-only

    # Run with performance benchmarking
    python run_security_tests.py --benchmark

    # Run with coverage reporting
    python run_security_tests.py --coverage

    # Run specific test class
    python run_security_tests.py --class TestSecuritySystemIntegration

    # Run specific test method
    python run_security_tests.py --method test_end_to_end_payment_security_workflow

    # Run with verbose output and debugging
    python run_security_tests.py --verbose --debug
"""

import argparse
import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description):
    """Run a command and handle errors gracefully"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        end_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"✅ {description} completed successfully")
        print(f"⏱️  Duration: {end_time - start_time:.2f} seconds")
        print(f"{'='*60}\n")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n{'='*60}")
        print(f"❌ {description} failed with exit code {e.returncode}")
        print(f"{'='*60}\n")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest',
        'psutil',
        'cryptography',
        'pytest-cov',
        'pytest-benchmark'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements-testing.txt")
        return False
    
    print("✅ All dependencies are available")
    return True

def run_security_tests(args):
    """Run security integration tests"""
    test_file = "tests/integration/test_security_integration.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd = ["python", "-m", "pytest", test_file]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.debug:
        cmd.extend(["-s", "--tb=long"])
    
    if args.benchmark:
        cmd.append("--benchmark-only")
    
    if args.coverage:
        cmd.extend(["--cov=security", "--cov-report=html"])
    
    if args.class_name:
        cmd.extend(["-k", args.class_name])
    
    if args.method_name:
        cmd.extend(["-k", args.method_name])
    
    return run_command(cmd, "Security Integration Tests")

def run_compliance_tests(args):
    """Run compliance workflow tests"""
    test_file = "tests/integration/test_compliance_workflow.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd = ["python", "-m", "pytest", test_file]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.debug:
        cmd.extend(["-s", "--tb=long"])
    
    if args.benchmark:
        cmd.append("--benchmark-only")
    
    if args.coverage:
        cmd.extend(["--cov=security", "--cov-report=html"])
    
    if args.class_name:
        cmd.extend(["-k", args.class_name])
    
    if args.method_name:
        cmd.extend(["-k", args.method_name])
    
    return run_command(cmd, "Compliance Workflow Tests")

def run_all_tests(args):
    """Run all integration tests"""
    test_dir = "tests/integration/"
    
    if not os.path.exists(test_dir):
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    cmd = ["python", "-m", "pytest", test_dir]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.debug:
        cmd.extend(["-s", "--tb=long"])
    
    if args.benchmark:
        cmd.append("--benchmark-only")
    
    if args.coverage:
        cmd.extend(["--cov=security", "--cov-report=html"])
    
    if args.class_name:
        cmd.extend(["-k", args.class_name])
    
    if args.method_name:
        cmd.extend(["-k", args.method_name])
    
    return run_command(cmd, "All Integration Tests")

def run_performance_benchmarks():
    """Run performance benchmarking tests"""
    print("🚀 Running Performance Benchmarks...")
    
    # Security performance benchmarks
    security_cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_security_integration.py::TestSecurityPerformanceBenchmarks",
        "--benchmark-only", "-v"
    ]
    
    if not run_command(security_cmd, "Security Performance Benchmarks"):
        return False
    
    # Compliance performance benchmarks
    compliance_cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_compliance_workflow.py::TestCompliancePerformanceBenchmarks",
        "--benchmark-only", "-v"
    ]
    
    return run_command(compliance_cmd, "Compliance Performance Benchmarks")

def generate_test_report():
    """Generate comprehensive test report"""
    print("📊 Generating Test Report...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "--junitxml=test-results.xml",
        "--cov=security",
        "--cov-report=xml",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]
    
    return run_command(cmd, "Test Report Generation")

def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(
        description="MINGUS Security Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_security_tests.py

  # Run only security tests with verbose output
  python run_security_tests.py --security-only --verbose

  # Run compliance tests with performance benchmarking
  python run_security_tests.py --compliance-only --benchmark

  # Run specific test class
  python run_security_tests.py --class TestSecuritySystemIntegration

  # Run with coverage and generate report
  python run_security_tests.py --coverage --report
        """
    )
    
    # Test selection options
    parser.add_argument(
        "--security-only",
        action="store_true",
        help="Run only security integration tests"
    )
    
    parser.add_argument(
        "--compliance-only",
        action="store_true",
        help="Run only compliance workflow tests"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarking tests"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    # Test execution options
    parser.add_argument(
        "--class",
        dest="class_name",
        help="Run tests from specific class (e.g., TestSecuritySystemIntegration)"
    )
    
    parser.add_argument(
        "--method",
        dest="method_name",
        help="Run specific test method"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print header
    print("🔒 MINGUS Security Integration Test Runner")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies check failed. Please install missing packages.")
        sys.exit(1)
    
    # Determine what to run
    success = True
    
    if args.benchmark:
        success = run_performance_benchmarks()
    elif args.report:
        success = generate_test_report()
    elif args.security_only:
        success = run_security_tests(args)
    elif args.compliance_only:
        success = run_compliance_tests(args)
    elif args.class_name or args.method_name:
        # Run specific tests from both files
        success = run_security_tests(args) and run_compliance_tests(args)
    else:
        # Run all tests by default
        success = run_all_tests(args)
    
    # Final status
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("📁 Check coverage reports in htmlcov/ directory")
        print("📊 Check benchmark results in .benchmarks/ directory")
    else:
        print("💥 Some tests failed. Check output above for details.")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
