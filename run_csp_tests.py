#!/usr/bin/env python3
"""
CSP Test Runner for Mingus Financial App
Quick script to run CSP tests and validate implementation
"""

import sys
import os
import subprocess
from pathlib import Path

def run_csp_tests():
    """Run CSP tests and validation"""
    print("🔍 Running CSP Tests for Mingus Financial App")
    print("=" * 60)
    
    # Check if test suite exists
    if not Path("csp_test_suite.py").exists():
        print("❌ CSP test suite not found. Please ensure csp_test_suite.py exists.")
        return False
    
    # Check if Flask app is running
    print("🌐 Checking if Flask app is running...")
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
        else:
            print(f"⚠️  Flask app returned status {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ Flask app is not running. Please start the application first:")
        print("   python secure_financial_app.py")
        return False
    
    # Run CSP tests
    print("\n🧪 Running CSP Test Suite...")
    try:
        result = subprocess.run([
            sys.executable, "csp_test_suite.py",
            "--url", "http://localhost:5000",
            "--output", "csp_test_results.json"
        ], capture_output=True, text=True, check=True)
        
        print("✅ CSP tests completed successfully")
        print(result.stdout)
        
        # Check if results file was created
        if Path("csp_test_results.json").exists():
            print("\n📊 Test results saved to csp_test_results.json")
            
            # Display summary
            import json
            with open("csp_test_results.json", "r") as f:
                results = json.load(f)
            
            summary = results.get('summary', {})
            print(f"\n📈 Test Summary:")
            print(f"   Total Tests: {summary.get('total_tests', 0)}")
            print(f"   ✅ Passed: {summary.get('passed', 0)}")
            print(f"   ❌ Failed: {summary.get('failed', 0)}")
            print(f"   ⚠️  Warnings: {summary.get('warnings', 0)}")
            print(f"   📊 Score: {summary.get('score', 0)}%")
            
            # Show recommendations
            recommendations = results.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
            
            return summary.get('failed', 0) == 0 and summary.get('errors', 0) == 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ CSP tests failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error running CSP tests: {e}")
        return False

def validate_csp_config():
    """Validate CSP configuration"""
    print("\n⚙️  Validating CSP Configuration...")
    
    try:
        from csp_config import validate_csp_config, get_csp_config
        
        # Test all environments
        environments = ['production', 'staging', 'development', 'testing']
        
        for env in environments:
            print(f"\n🔧 Testing {env} configuration...")
            config = get_csp_config(env)
            warnings = validate_csp_config(env)
            
            if warnings:
                print(f"⚠️  Warnings for {env}:")
                for warning in warnings:
                    print(f"   • {warning}")
            else:
                print(f"✅ {env} configuration is valid")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing CSP config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating CSP config: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking Dependencies...")
    
    required_packages = [
        'requests',
        'selenium',
        'flask'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Main test runner"""
    print("🚀 CSP Test Runner for Mingus Financial App")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    # Validate CSP configuration
    if not validate_csp_config():
        print("\n❌ CSP configuration validation failed.")
        sys.exit(1)
    
    # Run CSP tests
    if not run_csp_tests():
        print("\n❌ CSP tests failed.")
        sys.exit(1)
    
    print("\n🎉 All CSP tests passed successfully!")
    print("✅ CSP implementation is working correctly.")
    
    # Provide next steps
    print("\n📋 Next Steps:")
    print("1. Review test results in csp_test_results.json")
    print("2. Address any warnings or recommendations")
    print("3. Deploy with report-only mode first")
    print("4. Monitor violations for 24-48 hours")
    print("5. Switch to enforced mode in production")

if __name__ == "__main__":
    main()
