#!/usr/bin/env python3
"""
Setup script for Secure Financial Session Management System
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'templates']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")
    return True

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print("⚠️  Redis is not available (optional)")
        print("   For enhanced performance, install and start Redis:")
        print("   - Ubuntu/Debian: sudo apt-get install redis-server")
        print("   - macOS: brew install redis")
        print("   - Start: redis-server")
        return False

def check_geoip():
    """Check if GeoIP database is available"""
    geoip_file = Path("GeoLite2-City.mmdb")
    if geoip_file.exists():
        print("✅ GeoIP database found")
        return True
    else:
        print("⚠️  GeoIP database not found (optional)")
        print("   For location tracking, download GeoLite2-City.mmdb")
        print("   from https://dev.maxmind.com/geoip/geoip2/geolite2/")
        return False

def create_database():
    """Create SQLite database and tables"""
    try:
        from secure_financial_app import app, db, User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            db.create_all()
            
            # Create demo user if it doesn't exist
            demo_user = User.query.filter_by(username='demo').first()
            if not demo_user:
                demo_user = User(
                    username='demo',
                    email='demo@example.com',
                    password_hash=generate_password_hash('SecurePass123!'),
                    is_verified=True,
                    security_level='enhanced'
                )
                db.session.add(demo_user)
                db.session.commit()
                print("✅ Demo user created: demo / SecurePass123!")
            else:
                print("✅ Demo user already exists")
        
        print("✅ Database created successfully")
        return True
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🚀 SECURE FINANCIAL SESSION MANAGEMENT SYSTEM")
    print("="*60)
    print("\n📋 Setup completed successfully!")
    print("\n🔑 Demo Credentials:")
    print("   Username: demo")
    print("   Password: SecurePass123!")
    print("\n🌐 To start the application:")
    print("   python secure_financial_app.py")
    print("\n📍 Access the application at:")
    print("   http://localhost:5000")
    print("\n🛡️ Security Features:")
    print("   ✅ 20-minute session timeout")
    print("   ✅ Rate limiting (5 attempts per 15 minutes)")
    print("   ✅ Multi-device session tracking")
    print("   ✅ Session fixation protection")
    print("   ✅ Automatic session cleanup")
    print("   ✅ Location-based monitoring")
    print("\n📚 Documentation:")
    print("   README_SECURE_SESSION.md")
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("🔧 Setting up Secure Financial Session Management System")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)
    
    # Check optional components
    check_redis()
    check_geoip()
    
    # Create database
    if not create_database():
        print("❌ Failed to create database")
        sys.exit(1)
    
    # Print startup information
    print_startup_info()

if __name__ == "__main__":
    main() 