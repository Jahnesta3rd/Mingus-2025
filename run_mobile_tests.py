#!/usr/bin/env python3
"""
Mobile Testing Runner
Starts the server and runs mobile tests
"""

import subprocess
import time
import sys
import os
from mobile_landing_page_test import MobileLandingPageTester

def start_server():
    """Start the Flask server"""
    print("🚀 Starting Flask server...")
    
    # Check if we're in the right directory
    if not os.path.exists("app.py") and not os.path.exists("main.py"):
        print("❌ Error: No Flask app found. Please run this from the project root directory.")
        sys.exit(1)
    
    # Try to start the server
    try:
        # Look for common Flask app files
        app_files = ["app.py", "main.py", "run.py"]
        app_file = None
        
        for file in app_files:
            if os.path.exists(file):
                app_file = file
                break
        
        if not app_file:
            print("❌ Error: No Flask app file found.")
            sys.exit(1)
        
        # Start the server in the background
        server_process = subprocess.Popen([
            sys.executable, app_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is running
        try:
            import requests
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running on http://localhost:5000")
                return server_process
            else:
                print(f"⚠️ Server responded with status code: {response.status_code}")
                return server_process
        except requests.exceptions.RequestException:
            print("⚠️ Server may not be fully started yet, but continuing with tests...")
            return server_process
            
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        print("💡 Make sure you have Flask installed: pip install flask")
        sys.exit(1)

def run_mobile_tests():
    """Run the mobile tests"""
    print("\n📱 Starting Mobile Tests...")
    
    try:
        # Create tester instance
        tester = MobileLandingPageTester("http://localhost:5000")
        
        # Run tests
        tester.run_all_tests()
        
        print("\n✅ Mobile tests completed!")
        
    except Exception as e:
        print(f"❌ Error running mobile tests: {str(e)}")
        print("💡 Make sure you have the required dependencies installed:")
        print("   pip install -r requirements-mobile-testing.txt")

def main():
    """Main function"""
    print("🎯 Mobile Landing Page Testing Suite")
    print("=" * 50)
    
    # Check if dependencies are installed
    try:
        import selenium
        import requests
    except ImportError:
        print("❌ Missing dependencies. Please install them first:")
        print("   pip install -r requirements-mobile-testing.txt")
        sys.exit(1)
    
    # Start server
    server_process = start_server()
    
    try:
        # Run tests
        run_mobile_tests()
        
    finally:
        # Clean up server process
        if server_process:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")

if __name__ == "__main__":
    main()
