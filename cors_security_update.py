#!/usr/bin/env python3
"""
CORS Security Update Script
Addresses CORS bypass vulnerabilities in Flask applications
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def check_flask_cors_version():
    """Check current Flask-CORS version"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", "Flask-CORS"], 
                              capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                version = line.split(':')[1].strip()
                print(f"✅ Current Flask-CORS version: {version}")
                
                # Check if version is 6.0.0+
                version_parts = version.split('.')
                if len(version_parts) >= 2:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    if major >= 6 and minor >= 0:
                        print("✅ Flask-CORS version is already 6.0.0+ (secure)")
                        return True
                    else:
                        print("⚠️  Flask-CORS version is below 6.0.0 (vulnerable)")
                        return False
                return False
    except subprocess.CalledProcessError:
        print("❌ Flask-CORS not installed")
        return False
    except Exception as e:
        print(f"❌ Error checking Flask-CORS version: {e}")
        return False

def update_flask_cors():
    """Update Flask-CORS to secure version"""
    print("\n🔄 Updating Flask-CORS to secure version...")
    
    try:
        # Update to Flask-CORS 6.0.0+
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "Flask-CORS>=6.0.0"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Flask-CORS updated successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update Flask-CORS: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error updating Flask-CORS: {e}")
        return False

def backup_file(file_path):
    """Create backup of file before modification"""
    backup_path = f"{file_path}.backup_{int(time.time())}"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup of {file_path}: {e}")
        return None

def update_app_factory_cors():
    """Update CORS configuration in app_factory.py"""
    file_path = "backend/app_factory.py"
    
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    print(f"\n🔧 Updating CORS configuration in {file_path}")
    
    # Create backup
    backup_path = backup_file(file_path)
    if not backup_path:
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find and update CORS configuration
        old_cors_config = '''    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })'''
        
        new_cors_config = '''    # Initialize CORS with security best practices
    CORS(app, 
         # Origins - only allow specific domains
         origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
         
         # Methods - restrict to only necessary HTTP methods
         methods=["GET", "POST", "PUT"],
         
         # Headers - only allow necessary headers
         allow_headers=["Content-Type", "Authorization"],
         
         # Security settings
         supports_credentials=False,  # Disable credentials for security
         max_age=3600,  # Cache preflight for 1 hour
         
         # Additional security
         vary_header=True,
         send_wildcard=False
    )'''
        
        if old_cors_config in content:
            content = content.replace(old_cors_config, new_cors_config)
            print("✅ CORS configuration updated")
        else:
            print("⚠️  CORS configuration not found in expected format")
            return False
        
        # Write updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ {file_path} updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        # Restore backup
        try:
            shutil.copy2(backup_path, file_path)
            print(f"✅ Restored backup: {file_path}")
        except:
            print(f"❌ Failed to restore backup: {file_path}")
        return False

def update_extensions_cors():
    """Update CORS configuration in extensions.py"""
    file_path = "backend/extensions.py"
    
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    print(f"\n🔧 Updating CORS configuration in {file_path}")
    
    # Create backup
    backup_path = backup_file(file_path)
    if not backup_path:
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add Flask-CORS import if not present
        if "from flask_cors import CORS" not in content:
            # Find the imports section
            import_lines = []
            for line in content.split('\n'):
                if line.startswith('from ') or line.startswith('import '):
                    import_lines.append(line)
                elif line.strip() and not line.startswith('#'):
                    break
            
            # Add CORS import
            if import_lines:
                last_import_index = content.rfind(import_lines[-1])
                insert_index = last_import_index + len(import_lines[-1]) + 1
                content = content[:insert_index] + "\nfrom flask_cors import CORS\n" + content[insert_index:]
                print("✅ Flask-CORS import added")
        
        # Add CORS initialization if not present
        if "CORS(" not in content:
            # Find init_extensions function
            if "def init_extensions(app):" in content:
                # Add CORS initialization
                init_func_start = content.find("def init_extensions(app):")
                init_func_end = content.find("def ", init_func_start + 1)
                if init_func_end == -1:
                    init_func_end = len(content)
                
                init_func = content[init_func_start:init_func_end]
                
                # Add CORS initialization after existing extensions
                if "talisman.init_app(app)" in init_func:
                    new_init = init_func.replace(
                        "talisman.init_app(app)",
                        "talisman.init_app(app)\n    \n    # Initialize CORS with security settings\n    CORS(app, \n         origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),\n         methods=['GET', 'POST', 'PUT'],\n         allow_headers=['Content-Type', 'Authorization'],\n         supports_credentials=False,\n         max_age=3600,\n         vary_header=True,\n         send_wildcard=False\n    )"
                    )
                    content = content.replace(init_func, new_init)
                    print("✅ CORS initialization added")
        
        # Write updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ {file_path} updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        # Restore backup
        try:
            shutil.copy2(backup_path, file_path)
            print(f"✅ Restored backup: {file_path}")
        except:
            print(f"❌ Failed to restore backup: {file_path}")
        return False

def create_cors_security_config():
    """Create CORS security configuration file"""
    config_content = '''# CORS Security Configuration
# This file contains secure CORS settings for the Flask application

# Allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://mingus.app

# Allowed methods
CORS_METHODS=GET,POST,PUT

# Allowed headers
CORS_HEADERS=Content-Type,Authorization

# Security settings
CORS_SUPPORTS_CREDENTIALS=false
CORS_MAX_AGE=3600
CORS_VARY_HEADER=true
CORS_SEND_WILDCARD=false

# Additional security headers
SECURITY_HEADERS_ENABLED=true
X_CONTENT_TYPE_OPTIONS=nosniff
X_FRAME_OPTIONS=DENY
X_XSS_PROTECTION=1; mode=block
'''
    
    config_path = "config/cors_security.env"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        print(f"✅ CORS security configuration created: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create CORS security configuration: {e}")
        return False

def run_security_tests():
    """Run security tests to verify CORS configuration"""
    print("\n🧪 Running CORS security tests...")
    
    try:
        # Test if the security test script exists
        if os.path.exists("cors_security_test.py"):
            result = subprocess.run([
                sys.executable, "cors_security_test.py", "--port", "5002", "--endpoint", "/api/test"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ CORS security tests passed")
                return True
            else:
                print("❌ CORS security tests failed")
                print("Test output:", result.stdout)
                print("Test errors:", result.stderr)
                return False
        else:
            print("⚠️  CORS security test script not found")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CORS security tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running CORS security tests: {e}")
        return False

def main():
    """Main security update function"""
    print("🚀 CORS Security Update Script")
    print("=" * 50)
    print("This script will address CORS bypass vulnerabilities")
    print("by updating Flask-CORS and implementing secure CORS policies.")
    print()
    
    # Check current Flask-CORS version
    if not check_flask_cors_version():
        # Update Flask-CORS
        if not update_flask_cors():
            print("❌ Failed to update Flask-CORS. Exiting.")
            sys.exit(1)
        
        # Verify update
        if not check_flask_cors_version():
            print("❌ Flask-CORS update verification failed. Exiting.")
            sys.exit(1)
    
    # Update application files
    print("\n🔧 Updating application CORS configuration...")
    
    success = True
    
    # Update app_factory.py
    if os.path.exists("backend/app_factory.py"):
        if not update_app_factory_cors():
            success = False
    
    # Update extensions.py
    if os.path.exists("backend/extensions.py"):
        if not update_extensions_cors():
            success = False
    
    # Create CORS security configuration
    if not create_cors_security_config():
        success = False
    
    if not success:
        print("\n❌ Some updates failed. Please check the errors above.")
        sys.exit(1)
    
    print("\n✅ CORS security updates completed successfully!")
    print("\n📋 Summary of changes:")
    print("   • Flask-CORS updated to secure version 6.0.0+")
    print("   • CORS configuration updated with security best practices")
    print("   • Wildcard origins disabled")
    print("   • Credentials support disabled")
    print("   • Restricted HTTP methods")
    print("   • Security headers configured")
    
    print("\n🔒 Security improvements implemented:")
    print("   • CORS bypass vulnerabilities addressed")
    print("   • Origin validation enforced")
    print("   • Method restrictions applied")
    print("   • Header restrictions configured")
    
    print("\n🧪 Next steps:")
    print("   1. Restart your Flask application")
    print("   2. Test CORS functionality with: python cors_security_test.py")
    print("   3. Verify legitimate origins work correctly")
    print("   4. Confirm malicious origins are blocked")
    
    print("\n✅ CORS security update completed successfully!")

if __name__ == "__main__":
    main()
