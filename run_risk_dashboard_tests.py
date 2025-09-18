#!/usr/bin/env python3
"""
Risk Dashboard Test Runner

Simple script to run the comprehensive test suite for the risk-based success metrics dashboard.
"""

import sys
import os
import subprocess
from datetime import datetime

def run_tests():
    """Run the risk dashboard test suite"""
    print("🎯 Risk-Based Success Metrics Dashboard - Test Runner")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('test_risk_dashboard.py'):
        print("❌ Error: test_risk_dashboard.py not found in current directory")
        print("Please run this script from the project root directory")
        return False
    
    # Check if backend directory exists
    if not os.path.exists('backend'):
        print("❌ Error: backend directory not found")
        print("Please run this script from the project root directory")
        return False
    
    try:
        # Run the test suite
        print("🧪 Running comprehensive test suite...")
        print("-" * 40)
        
        result = subprocess.run([
            sys.executable, 'test_risk_dashboard.py'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check return code
        if result.returncode == 0:
            print("\n🎉 All tests completed successfully!")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏰ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'sqlite3',
        'json',
        'datetime',
        'unittest',
        'tempfile',
        'os',
        'sys'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        return False
    
    print("✅ All required dependencies are available")
    return True

def main():
    """Main test runner function"""
    print("Risk Dashboard Test Runner")
    print("=" * 30)
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again")
        return 1
    
    print()
    
    # Run tests
    success = run_tests()
    
    print("\n" + "=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎉 Test suite completed successfully!")
        return 0
    else:
        print("⚠️  Test suite completed with issues")
        return 1

if __name__ == '__main__':
    sys.exit(main())
