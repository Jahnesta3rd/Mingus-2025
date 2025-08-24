#!/usr/bin/env python3
"""
Run Final Production Validation with proper environment setup
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    print("🔧 Loading environment variables...")
    
    # Try to load .env file
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env file")
        
        # Check if critical variables are loaded
        critical_vars = ['SECRET_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
        loaded_vars = 0
        
        for var in critical_vars:
            if os.environ.get(var):
                loaded_vars += 1
                print(f"   ✅ {var}: {'*' * min(len(os.environ.get(var)), 8)}...")
            else:
                print(f"   ⚠️ {var}: Not set")
        
        print(f"📊 Environment variables: {loaded_vars}/{len(critical_vars)} loaded")
        return loaded_vars == len(critical_vars)
    else:
        print("❌ .env file not found")
        return False

def start_test_app():
    """Start the test Flask application"""
    print("🚀 Starting test Flask application...")
    
    try:
        # Start the test app in background
        process = subprocess.Popen([
            sys.executable, 'test_app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for the app to start
        import time
        time.sleep(5)
        
        print("✅ Test Flask application started")
        return process
    except Exception as e:
        print(f"❌ Failed to start test app: {e}")
        return None

def run_validation():
    """Run the final production validation"""
    print("🔍 Running final production validation...")
    
    try:
        result = subprocess.run([
            sys.executable, 'final_production_validation.py'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main():
    """Main function"""
    print("🎯 FINAL PRODUCTION VALIDATION WITH ENVIRONMENT SETUP")
    print("=" * 60)
    print()
    
    # Load environment variables
    env_loaded = load_environment()
    
    if not env_loaded:
        print("⚠️ Environment variables not fully loaded, but continuing...")
    
    # Start test app
    app_process = start_test_app()
    
    if not app_process:
        print("❌ Could not start test application")
        return 1
    
    try:
        # Run validation
        success = run_validation()
        
        if success:
            print("\n🎉 Validation completed successfully!")
        else:
            print("\n⚠️ Validation completed with issues")
        
        return 0 if success else 1
        
    finally:
        # Clean up
        if app_process:
            print("🛑 Stopping test application...")
            app_process.terminate()
            app_process.wait()

if __name__ == "__main__":
    exit(main()) 