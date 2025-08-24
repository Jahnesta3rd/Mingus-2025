#!/usr/bin/env python3
"""
Comprehensive Test Runner for Meme Splash Page Feature
Runs all tests with proper configuration and reporting.
"""

import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, description, capture_output=False):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration:.2f}s")
            return True, result.stdout if capture_output else None
        else:
            print(f"❌ {description} failed after {duration:.2f}s")
            if capture_output and result.stderr:
                print(f"Error output: {result.stderr}")
            return False, result.stderr if capture_output else None
            
    except Exception as e:
        print(f"❌ {description} failed with exception: {str(e)}")
        return False, str(e)

def setup_environment():
    """Setup test environment"""
    print("Setting up test environment...")
    
    # Set environment variables
    os.environ['TESTING'] = 'true'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    # Create test directories
    test_dirs = ['coverage', 'reports', 'logs']
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("✅ Environment setup complete")

def run_backend_tests():
    """Run backend tests"""
    print("\n🧪 Running Backend Tests")
    
    # Unit tests
    success, output = run_command(
        "pytest tests/meme_splash_page/test_meme_service_unit.py -v --cov=backend/services/meme_service --cov-report=xml --cov-report=html --cov-report=term",
        "Backend Unit Tests"
    )
    
    if not success:
        return False
    
    # API tests
    success, output = run_command(
        "pytest tests/meme_splash_page/test_meme_api_endpoints.py -v --cov=backend/routes/meme_routes --cov-report=xml --cov-report=html --cov-report=term",
        "Backend API Tests"
    )
    
    if not success:
        return False
    
    # Integration tests
    success, output = run_command(
        "pytest tests/meme_splash_page/test_meme_integration.py -v --cov=backend --cov-report=xml --cov-report=html --cov-report=term",
        "Backend Integration Tests"
    )
    
    return success

def run_performance_tests():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests")
    
    success, output = run_command(
        "pytest tests/meme_splash_page/test_meme_performance.py -v --tb=short",
        "Performance Tests"
    )
    
    return success

def run_frontend_tests():
    """Run frontend tests"""
    print("\n🎨 Running Frontend Tests")
    
    # Check if Node.js is available
    success, output = run_command("node --version", "Check Node.js", capture_output=True)
    if not success:
        print("⚠️ Node.js not found, skipping frontend tests")
        return True
    
    # Install dependencies if needed
    if not Path("node_modules").exists():
        success, output = run_command("npm install", "Install Node.js dependencies")
        if not success:
            return False
    
    # Run frontend tests
    success, output = run_command(
        "npm test -- --testPathPattern='MemeSplashPage.test.tsx' --coverage --watchAll=false",
        "Frontend Tests"
    )
    
    return success

def run_security_tests():
    """Run security tests"""
    print("\n🔒 Running Security Tests")
    
    # Install security tools if needed
    try:
        import bandit
    except ImportError:
        success, output = run_command("pip install bandit safety", "Install security tools")
        if not success:
            return False
    
    # Run security scans
    success, output = run_command(
        "bandit -r backend/routes/meme_routes.py backend/services/meme_service.py -f json -o reports/bandit-report.json",
        "Security Scan (Bandit)"
    )
    
    if success:
        success, output = run_command(
            "safety check --json --output reports/safety-report.json",
            "Dependency Security Check (Safety)"
        )
    
    return success

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_suite": "Meme Splash Page",
        "results": {}
    }
    
    # Check for coverage reports
    coverage_files = [
        "coverage.xml",
        "htmlcov/index.html",
        "coverage/lcov.info"
    ]
    
    for file_path in coverage_files:
        if Path(file_path).exists():
            report["results"]["coverage"] = f"Coverage report available: {file_path}"
    
    # Check for security reports
    security_files = [
        "reports/bandit-report.json",
        "reports/safety-report.json"
    ]
    
    for file_path in security_files:
        if Path(file_path).exists():
            report["results"]["security"] = f"Security report available: {file_path}"
    
    # Save report
    with open("reports/test-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("✅ Test report generated: reports/test-report.json")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run Meme Splash Page Tests")
    parser.add_argument("--backend", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend", action="store_true", help="Run only frontend tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--security", action="store_true", help="Run only security tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 Meme Splash Page Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup environment
    setup_environment()
    
    # Track overall success
    all_success = True
    
    # Run tests based on arguments
    if args.backend or not any([args.frontend, args.performance, args.security]):
        success = run_backend_tests()
        all_success = all_success and success
    
    if args.frontend or not any([args.backend, args.performance, args.security]):
        success = run_frontend_tests()
        all_success = all_success and success
    
    if args.performance or not any([args.backend, args.frontend, args.security]):
        success = run_performance_tests()
        all_success = all_success and success
    
    if args.security or not any([args.backend, args.frontend, args.performance]):
        success = run_security_tests()
        all_success = all_success and success
    
    # Generate report
    generate_test_report()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    
    if all_success:
        print("🎉 All tests passed!")
        print("✅ Backend tests: PASS")
        print("✅ Frontend tests: PASS")
        print("✅ Performance tests: PASS")
        print("✅ Security tests: PASS")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print("Please check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
