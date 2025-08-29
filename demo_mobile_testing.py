#!/usr/bin/env python3
"""
MINGUS Mobile Demographic Testing - Demo Script
==============================================

This script demonstrates how to run a quick mobile test to validate
the testing suite works correctly.

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_mobile_testing():
    """Run a demonstration of the mobile testing suite."""
    
    print("🚀 MINGUS Mobile Demographic Testing - Demo")
    print("=" * 50)
    print("This demo will run a quick test to validate the testing suite.")
    print("=" * 50)
    
    try:
        # Import the testing modules
        from test_mobile_demographic_experience import (
            MobileDemographicTester, 
            DeviceProfile
        )
        
        print("✅ Successfully imported testing modules")
        
        # Initialize tester with a demo URL (won't actually test)
        print("\n🔧 Initializing tester...")
        tester = MobileDemographicTester("https://example.com")
        print("✅ Tester initialized successfully")
        
        # Show device profiles
        print("\n📱 Available device profiles:")
        for profile in DeviceProfile:
            device_specs = tester.device_profiles[profile]
            print(f"  • {profile.value}: {device_specs['viewport'][0]}x{device_specs['viewport'][1]} viewport")
        
        # Show target specifications
        print("\n🎯 Target specifications for your demographic:")
        for key, value in tester.target_specs.items():
            print(f"  • {key}: {value}")
        
        # Demonstrate test structure
        print("\n🧪 Test structure:")
        test_types = [
            "Mobile Performance Test",
            "Touch Interactions Test", 
            "Offline Functionality Test",
            "Mobile Payment Processing Test",
            "Screen Adaptation Test",
            "Budget Device Performance Test"
        ]
        
        for test_type in test_types:
            print(f"  • {test_type}")
        
        print("\n✅ Demo completed successfully!")
        print("\nTo run actual tests:")
        print("1. Start your MINGUS application")
        print("2. Run: python run_mobile_demographic_tests.py --quick")
        print("3. Or run specific tests: python run_mobile_demographic_tests.py --tests performance --devices budget_android")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nInstall dependencies with:")
        print("pip install -r requirements-mobile-demographic-testing.txt")
        return False
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return False


def check_dependencies():
    """Check if basic dependencies are available."""
    print("🔧 Checking dependencies...")
    
    required_modules = [
        'selenium',
        'psutil', 
        'requests',
        'json',
        'time',
        'datetime'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing modules: {', '.join(missing_modules)}")
        print("Install with: pip install -r requirements-mobile-demographic-testing.txt")
        return False
    
    print("✅ All basic dependencies available")
    return True


def main():
    """Main demo function."""
    print("Starting MINGUS Mobile Testing Demo...")
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    # Run demo
    if demo_mobile_testing():
        print("\n🎉 Demo completed successfully!")
        return 0
    else:
        print("\n💥 Demo failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
