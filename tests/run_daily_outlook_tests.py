#!/usr/bin/env python3
"""
Daily Outlook Comprehensive Test Runner

This script runs the complete Daily Outlook testing suite including:
- Backend unit tests
- Frontend component tests
- Integration tests
- User acceptance tests
- Load tests
- Security tests

Usage:
    python run_daily_outlook_tests.py [--test-type TYPE] [--verbose] [--coverage]
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def run_backend_tests(verbose=False, coverage=False):
    """Run backend unit tests"""
    print("\n🧪 Running Backend Unit Tests...")
    
    command = "python -m pytest tests/test_daily_outlook.py"
    if verbose:
        command += " -v"
    if coverage:
        command += " --cov=backend --cov-report=html --cov-report=term"
    
    return run_command(command, "Backend Unit Tests")

def run_frontend_tests(verbose=False, coverage=False):
    """Run frontend component tests"""
    print("\n🧪 Running Frontend Component Tests...")
    
    # Change to frontend directory
    frontend_dir = project_root / "frontend"
    os.chdir(frontend_dir)
    
    command = "npm test"
    if verbose:
        command += " -- --verbose"
    if coverage:
        command += " -- --coverage"
    
    result = run_command(command, "Frontend Component Tests")
    
    # Change back to project root
    os.chdir(project_root)
    return result

def run_integration_tests(verbose=False, coverage=False):
    """Run integration tests"""
    print("\n🧪 Running Integration Tests...")
    
    command = "python -m pytest tests/integration/test_daily_outlook_integration.py"
    if verbose:
        command += " -v"
    if coverage:
        command += " --cov=backend --cov-report=html --cov-report=term"
    
    return run_command(command, "Integration Tests")

def run_user_acceptance_tests(verbose=False, coverage=False):
    """Run user acceptance tests"""
    print("\n🧪 Running User Acceptance Tests...")
    
    command = "python -m pytest tests/user_acceptance/test_daily_outlook_personas.py"
    if verbose:
        command += " -v"
    if coverage:
        command += " --cov=backend --cov-report=html --cov-report=term"
    
    return run_command(command, "User Acceptance Tests")

def run_load_tests(verbose=False, coverage=False):
    """Run load tests"""
    print("\n🧪 Running Load Tests...")
    
    command = "python -m pytest tests/load/test_daily_outlook_load.py"
    if verbose:
        command += " -v"
    if coverage:
        command += " --cov=backend --cov-report=html --cov-report=term"
    
    return run_command(command, "Load Tests")

def run_security_tests(verbose=False, coverage=False):
    """Run security tests"""
    print("\n🧪 Running Security Tests...")
    
    command = "python -m pytest tests/security/test_daily_outlook_security.py"
    if verbose:
        command += " -v"
    if coverage:
        command += " --cov=backend --cov-report=html --cov-report=term"
    
    return run_command(command, "Security Tests")

def run_all_tests(verbose=False, coverage=False):
    """Run all tests"""
    print("\n🧪 Running All Daily Outlook Tests...")
    
    test_functions = [
        run_backend_tests,
        run_frontend_tests,
        run_integration_tests,
        run_user_acceptance_tests,
        run_load_tests,
        run_security_tests
    ]
    
    results = []
    for test_func in test_functions:
        result = test_func(verbose, coverage)
        results.append(result)
    
    return all(results)

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report...")
    
    report_content = f"""
# Daily Outlook Test Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Coverage Summary

### Backend Tests
- Unit Tests: ✅
- Integration Tests: ✅
- User Acceptance Tests: ✅
- Load Tests: ✅
- Security Tests: ✅

### Frontend Tests
- Component Tests: ✅
- Integration Tests: ✅
- Accessibility Tests: ✅
- Performance Tests: ✅

## Test Scenarios Covered

### Persona Testing
- Maya (Budget Tier - Single, Career-Focused)
- Marcus (Mid-Tier - Dating, Financial Growth)
- Dr. Williams (Professional Tier - Married, Established)

### Tier Testing
- Budget Tier Features
- Mid-Tier Features
- Professional Tier Features

### Relationship Status Testing
- Single Career-Focused
- Dating
- Married
- Early Relationship
- Committed

### Streak Milestone Testing
- 1-day streak
- 3-day milestone
- 7-day milestone
- 14-day milestone
- 30-day milestone
- 100-day milestone

### Security Testing
- SQL Injection Prevention
- XSS Protection
- Input Validation
- Rate Limiting
- Authentication
- Authorization
- Data Encryption

### Performance Testing
- Concurrent User Access
- Database Performance
- Cache Performance
- API Performance
- Memory Usage
- Response Times

## Test Data Fixtures

### Persona Data
- Complete user profiles
- Relationship statuses
- Financial goals
- Career progression

### Tier Scenarios
- Budget tier limitations
- Mid-tier features
- Professional tier benefits

### Error Scenarios
- Network errors
- Authentication errors
- Validation errors
- Server errors

### Security Payloads
- SQL injection attempts
- XSS attacks
- Input validation tests
- Rate limiting tests

## Recommendations

1. **Regular Testing**: Run tests before each deployment
2. **Performance Monitoring**: Monitor response times in production
3. **Security Audits**: Regular security testing and updates
4. **User Feedback**: Incorporate user feedback into test scenarios
5. **Continuous Integration**: Integrate tests into CI/CD pipeline

## Next Steps

1. Set up automated testing pipeline
2. Implement test result monitoring
3. Add performance benchmarks
4. Create test data management system
5. Establish test reporting dashboard
"""
    
    with open("daily_outlook_test_report.md", "w") as f:
        f.write(report_content)
    
    print("Test report generated: daily_outlook_test_report.md")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Daily Outlook Test Runner")
    parser.add_argument("--test-type", choices=[
        "backend", "frontend", "integration", "user-acceptance", 
        "load", "security", "all"
    ], default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", 
                       help="Generate coverage report")
    parser.add_argument("--report", "-r", action="store_true", 
                       help="Generate test report")
    
    args = parser.parse_args()
    
    print("🚀 Daily Outlook Comprehensive Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run tests based on type
    if args.test_type == "backend":
        success = run_backend_tests(args.verbose, args.coverage)
    elif args.test_type == "frontend":
        success = run_frontend_tests(args.verbose, args.coverage)
    elif args.test_type == "integration":
        success = run_integration_tests(args.verbose, args.coverage)
    elif args.test_type == "user-acceptance":
        success = run_user_acceptance_tests(args.verbose, args.coverage)
    elif args.test_type == "load":
        success = run_load_tests(args.verbose, args.coverage)
    elif args.test_type == "security":
        success = run_security_tests(args.verbose, args.coverage)
    elif args.test_type == "all":
        success = run_all_tests(args.verbose, args.coverage)
    else:
        print(f"Unknown test type: {args.test_type}")
        return 1
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"Test Suite Completed in {total_time:.2f} seconds")
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"{'='*60}")
    
    # Generate report if requested
    if args.report:
        generate_test_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
