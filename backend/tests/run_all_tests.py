#!/usr/bin/env python3
"""
Comprehensive test runner for backend testing and validation

This script runs all backend tests including:
- Unit tests for validation
- Integration tests for API endpoints
- Security tests
- Performance tests

Usage:
    python run_all_tests.py [--verbose] [--coverage] [--unit-only] [--integration-only]
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
        return True
    else:
        print(f"\n❌ {description} - FAILED")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run all backend tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('--security-only', action='store_true', help='Run only security tests')
    parser.add_argument('--validation-only', action='store_true', help='Run only validation tests')
    
    args = parser.parse_args()
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Build pytest command
    pytest_cmd = ['pytest']
    
    if args.verbose:
        pytest_cmd.append('-v')
    else:
        pytest_cmd.append('-q')
    
    if args.coverage:
        pytest_cmd.extend(['--cov=backend', '--cov-report=html', '--cov-report=term'])
    
    # Determine which tests to run
    if args.unit_only:
        test_paths = [str(test_dir / 'unit')]
    elif args.integration_only:
        test_paths = [str(test_dir / 'integration')]
    elif args.security_only:
        test_paths = [str(test_dir / 'integration' / 'test_security.py')]
    elif args.validation_only:
        test_paths = [str(test_dir / 'unit' / 'test_validation.py')]
    else:
        # Run all tests
        test_paths = [str(test_dir)]
    
    pytest_cmd.extend(test_paths)
    
    # Convert to string for shell execution
    cmd = ' '.join(pytest_cmd)
    
    print("\n" + "="*70)
    print("MINGUS BACKEND TEST SUITE")
    print("="*70)
    print(f"Test Directory: {test_dir}")
    print(f"Command: {cmd}")
    print("="*70 + "\n")
    
    # Run tests
    success = run_command(cmd, "Backend Test Suite")
    
    if args.coverage:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    # Print summary
    print("\n" + "="*70)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
