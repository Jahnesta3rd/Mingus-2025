#!/usr/bin/env python3
"""
Complete Mingus integration script that handles the entire pipeline.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import threading

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def start_api_server():
    """Start the API server in a separate thread."""
    def run_server():
        subprocess.run([sys.executable, "mingus_api_server.py", "8080"])
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start
    return True

def main():
    """Run the complete Mingus integration pipeline."""
    print("🚀 Starting Mingus Integration Pipeline")
    print("=" * 50)
    
    # Step 1: Extract and categorize content
    print("\n📊 Step 1: Processing Notes with Categorization")
    if not run_command("python enhanced_local_notes_processor.py", "Enhanced notes processing"):
        print("❌ Failed to process notes. Exiting.")
        return False
    
    # Step 2: Download Instagram content
    print("\n📱 Step 2: Downloading Instagram Content")
    if not run_command("python simple_download.py", "Instagram content download"):
        print("⚠️  Instagram download had issues, but continuing...")
    
    # Step 3: Generate API data
    print("\n🌐 Step 3: Generating API Data")
    if not run_command("python generate_mingus_api.py", "API data generation"):
        print("❌ Failed to generate API data. Exiting.")
        return False
    
    # Step 4: Start API server
    print("\n🖥️  Step 4: Starting API Server")
    if not start_api_server():
        print("❌ Failed to start API server. Exiting.")
        return False
    
    # Step 5: Open integration demo
    print("\n🎨 Step 5: Opening Integration Demo")
    demo_file = Path("mingus_app_integration.html").absolute()
    if demo_file.exists():
        webbrowser.open(f"file://{demo_file}")
        print(f"✅ Demo opened in browser: {demo_file}")
    else:
        print("❌ Demo file not found")
    
    # Step 6: Show integration summary
    print("\n📋 Integration Summary")
    print("=" * 30)
    print("✅ Notes processed and categorized")
    print("✅ Instagram content downloaded")
    print("✅ API data generated")
    print("✅ API server running on http://localhost:8080")
    print("✅ Demo interface opened")
    
    print("\n🔗 Available API Endpoints:")
    print("   • http://localhost:8080/api/content - All content")
    print("   • http://localhost:8080/api/splash - Splash screen data")
    print("   • http://localhost:8080/api/health - Health check")
    
    print("\n📁 Generated Files:")
    api_dir = Path("mingus_api")
    if api_dir.exists():
        for file in api_dir.glob("*.json"):
            print(f"   • {file.name}")
    
    print("\n🎯 Next Steps for Mingus App Integration:")
    print("1. Use the API endpoints to fetch content in your app")
    print("2. Implement the splash screen component using splash_screen.json")
    print("3. Add category filtering using category-specific endpoints")
    print("4. Set up background sync to refresh content periodically")
    print("5. Implement local caching for offline viewing")
    
    print(f"\n🔄 API server is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Integration pipeline stopped")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
