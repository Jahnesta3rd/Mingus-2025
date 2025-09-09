#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Splash Page Test Runner
Comprehensive test runner for the meme splash page testing suite
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    start_time = time.time()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"Exit code: {result.returncode}")
        print(f"Duration: {end_time - start_time:.2f} seconds")
        
        if result.stdout:
            print("\n📤 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def run_backend_tests(test_type="all", coverage=False, parallel=False):
    """Run backend tests"""
    base_dir = Path(__file__).parent
    test_dir = base_dir
    
    # Change to test directory
    os.chdir(test_dir)
    
    # Base pytest command
    cmd_parts = ["python", "-m", "pytest", "-v"]
    
    # Add coverage if requested
    if coverage:
        cmd_parts.extend(["--cov=../../../meme_selector", "--cov=../../../backend/api/meme_endpoints", "--cov-report=html", "--cov-report=xml"])
    
    # Add parallel execution if requested
    if parallel:
        cmd_parts.extend(["-n", "auto"])
    
    # Add HTML report
    cmd_parts.extend(["--html=test_report.html", "--self-contained-html"])
    
    # Select test files based on type
    if test_type == "unit":
        cmd_parts.extend(["test_meme_selector_unit.py", "test_meme_api_endpoints.py"])
    elif test_type == "api":
        cmd_parts.extend(["test_meme_api_endpoints.py"])
    elif test_type == "mood":
        cmd_parts.extend(["test_mood_tracking.py"])
    elif test_type == "integration":
        cmd_parts.extend(["integration/test_full_user_flow.py"])
    elif test_type == "performance":
        cmd_parts.extend(["performance/test_meme_performance.py"])
    elif test_type == "all":
        cmd_parts.extend(["."])
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    command = " ".join(cmd_parts)
    return run_command(command, f"Running {test_type} backend tests")

def run_frontend_tests():
    """Run frontend tests"""
    base_dir = Path(__file__).parent.parent.parent
    frontend_dir = base_dir / "frontend"
    
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    # Check if package.json exists
    if not (frontend_dir / "package.json").exists():
        print(f"❌ package.json not found in {frontend_dir}")
        return False
    
    # Install dependencies if node_modules doesn't exist
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        install_cmd = "npm install"
        if not run_command(install_cmd, "Installing frontend dependencies"):
            return False
    
    # Install testing dependencies
    test_deps = [
        "@testing-library/react",
        "@testing-library/jest-dom", 
        "@testing-library/user-event",
        "jest-environment-jsdom"
    ]
    
    for dep in test_deps:
        install_cmd = f"npm install --save-dev {dep}"
        run_command(install_cmd, f"Installing {dep}")
    
    # Run tests
    test_cmd = "npm test -- --coverage --watchAll=false --testPathPattern=MemeSplashPage.test.tsx"
    return run_command(test_cmd, "Running frontend component tests")

def run_all_tests():
    """Run all tests"""
    print("🧪 Running Complete Meme Splash Page Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Backend tests
    print("\n🔧 Backend Tests")
    results["backend_unit"] = run_backend_tests("unit", coverage=True)
    results["backend_integration"] = run_backend_tests("integration")
    results["backend_performance"] = run_backend_tests("performance")
    
    # Frontend tests
    print("\n🎨 Frontend Tests")
    results["frontend"] = run_frontend_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print(f"\nTotal: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ {failed_tests} test suite(s) failed!")
        return False
    else:
        print(f"\n🎉 All test suites passed!")
        return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    dependencies = [
        ("python", "Python interpreter"),
        ("pip", "Python package manager"),
        ("pytest", "Python testing framework"),
        ("node", "Node.js runtime"),
        ("npm", "Node package manager")
    ]
    
    missing_deps = []
    
    for cmd, description in dependencies:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ {description}: {version}")
            else:
                print(f"❌ {description}: Not found")
                missing_deps.append(cmd)
        except FileNotFoundError:
            print(f"❌ {description}: Not found")
            missing_deps.append(cmd)
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install the missing dependencies before running tests.")
        return False
    
    print("\n✅ All dependencies are available!")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing Dependencies")
    print("=" * 30)
    
    # Install Python dependencies
    print("\n🐍 Installing Python dependencies...")
    pip_cmd = "pip install -r requirements-testing\\ 2.txt"
    if not run_command(pip_cmd, "Installing Python testing dependencies"):
        return False
    
    # Install additional Python packages
    additional_packages = [
        "pytest-cov",
        "pytest-html", 
        "pytest-xdist",
        "psutil"
    ]
    
    for package in additional_packages:
        install_cmd = f"pip install {package}"
        if not run_command(install_cmd, f"Installing {package}"):
            return False
    
    print("\n✅ Python dependencies installed successfully!")
    return True

def generate_test_report():
    """Generate a comprehensive test report"""
    print("📊 Generating Test Report")
    print("=" * 30)
    
    base_dir = Path(__file__).parent
    report_file = base_dir / "test_summary_report.md"
    
    with open(report_file, 'w') as f:
        f.write("# Meme Splash Page Test Summary Report\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Test Results\n\n")
        f.write("| Test Suite | Status |\n")
        f.write("|------------|--------|\n")
        
        # Check for test reports
        test_reports = [
            ("Backend Unit Tests", "test_report.html"),
            ("Backend Integration Tests", "integration/integration_report.html"),
            ("Backend Performance Tests", "performance/performance_report.html"),
            ("Frontend Tests", "../frontend/coverage/lcov-report/index.html")
        ]
        
        for test_name, report_path in test_reports:
            full_path = base_dir / report_path
            if full_path.exists():
                f.write(f"| {test_name} | ✅ Completed |\n")
            else:
                f.write(f"| {test_name} | ❌ Not Found |\n")
        
        f.write("\n## Artifacts\n\n")
        f.write("- HTML test reports\n")
        f.write("- Coverage reports\n")
        f.write("- Performance metrics\n")
        f.write("- Test logs\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. Review test reports for any failures\n")
        f.write("2. Check coverage reports for untested code\n")
        f.write("3. Analyze performance metrics\n")
        f.write("4. Address any issues found\n")
    
    print(f"✅ Test report generated: {report_file}")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Meme Splash Page Test Runner")
    parser.add_argument("--type", choices=["all", "unit", "api", "mood", "integration", "performance", "frontend"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        return
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
        return
    
    # Generate report if requested
    if args.report:
        generate_test_report()
        return
    
    # Run tests
    success = False
    
    if args.type == "all":
        success = run_all_tests()
    elif args.type == "frontend":
        success = run_frontend_tests()
    else:
        success = run_backend_tests(args.type, args.coverage, args.parallel)
    
    # Generate report after tests
    if success:
        generate_test_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
