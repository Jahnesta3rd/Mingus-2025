#!/usr/bin/env python3
"""
Quick Environment Variable Fix Script
Fixes common issues identified by the environment validator
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path

def generate_secure_key(length=32):
    """Generate a secure random key"""
    return secrets.token_urlsafe(length)

def fix_jwt_secret_key():
    """Fix missing JWT_SECRET_KEY"""
    print("🔐 Fixing JWT_SECRET_KEY...")
    
    # Generate a secure JWT secret key
    jwt_key = generate_secure_key(32)
    
    # Check if we have a .env file to update
    env_file = Path('.env')
    if env_file.exists():
        # Read current .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Check if JWT_SECRET_KEY already exists
        if 'JWT_SECRET_KEY=' in content:
            # Update existing JWT_SECRET_KEY
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('JWT_SECRET_KEY='):
                    lines[i] = f'JWT_SECRET_KEY={jwt_key}'
                    break
            
            # Write updated content
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Updated JWT_SECRET_KEY in .env file")
        else:
            # Add JWT_SECRET_KEY to .env file
            with open('.env', 'a') as f:
                f.write(f'\nJWT_SECRET_KEY={jwt_key}\n')
            
            print(f"✅ Added JWT_SECRET_KEY to .env file")
    else:
        # Create new .env file with JWT_SECRET_KEY
        with open('.env', 'w') as f:
            f.write(f'JWT_SECRET_KEY={jwt_key}\n')
        
        print(f"✅ Created .env file with JWT_SECRET_KEY")
    
    return jwt_key

def fix_secret_key():
    """Fix weak SECRET_KEY"""
    print("🔐 Fixing SECRET_KEY...")
    
    # Generate a secure Flask secret key
    secret_key = generate_secure_key(32)
    
    # Check if we have a .env file to update
    env_file = Path('.env')
    if env_file.exists():
        # Read current .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Check if SECRET_KEY already exists
        if 'SECRET_KEY=' in content:
            # Update existing SECRET_KEY
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('SECRET_KEY='):
                    lines[i] = f'SECRET_KEY={secret_key}'
                    break
            
            # Write updated content
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Updated SECRET_KEY in .env file")
        else:
            # Add SECRET_KEY to .env file
            with open('.env', 'a') as f:
                f.write(f'\nSECRET_KEY={secret_key}\n')
            
            print(f"✅ Added SECRET_KEY to .env file")
    else:
        # Create new .env file with SECRET_KEY
        with open('.env', 'w') as f:
            f.write(f'SECRET_KEY={secret_key}\n')
        
        print(f"✅ Created .env file with SECRET_KEY")
    
    return secret_key

def fix_field_encryption_key():
    """Fix missing FIELD_ENCRYPTION_KEY"""
    print("🔐 Fixing FIELD_ENCRYPTION_KEY...")
    
    # Generate a secure encryption key
    encryption_key = generate_secure_key(32)
    
    # Check if we have a .env file to update
    env_file = Path('.env')
    if env_file.exists():
        # Read current .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Check if FIELD_ENCRYPTION_KEY already exists
        if 'FIELD_ENCRYPTION_KEY=' in content:
            # Update existing FIELD_ENCRYPTION_KEY
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('FIELD_ENCRYPTION_KEY='):
                    lines[i] = f'FIELD_ENCRYPTION_KEY={encryption_key}'
                    break
            
            # Write updated content
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Updated FIELD_ENCRYPTION_KEY in .env file")
        else:
            # Add FIELD_ENCRYPTION_KEY to .env file
            with open('.env', 'a') as f:
                f.write(f'\nFIELD_ENCRYPTION_KEY={encryption_key}\n')
            
            print(f"✅ Added FIELD_ENCRYPTION_KEY to .env file")
    else:
        # Create new .env file with FIELD_ENCRYPTION_KEY
        with open('.env', 'w') as f:
            f.write(f'FIELD_ENCRYPTION_KEY={encryption_key}\n')
        
        print(f"✅ Created .env file with FIELD_ENCRYPTION_KEY")
    
    return encryption_key

def fix_production_settings():
    """Fix production environment settings"""
    print("🚀 Fixing production environment settings...")
    
    # Check if we have a .env file to update
    env_file = Path('.env')
    if env_file.exists():
        # Read current .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Define production settings to fix
        production_fixes = {
            'FLASK_ENV': 'production',
            'DEBUG': 'false',
            'FLASK_DEBUG': 'false',
            'SESSION_COOKIE_SECURE': 'true',
            'SESSION_COOKIE_SAMESITE': 'Strict'
        }
        
        lines = content.split('\n')
        updated = False
        
        for var, value in production_fixes.items():
            if f'{var}=' in content:
                # Update existing variable
                for i, line in enumerate(lines):
                    if line.startswith(f'{var}='):
                        lines[i] = f'{var}={value}'
                        updated = True
                        print(f"✅ Updated {var} to {value}")
                        break
            else:
                # Add new variable
                lines.append(f'{var}={value}')
                updated = True
                print(f"✅ Added {var}={value}")
        
        if updated:
            # Write updated content
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
    else:
        print("⚠️  No .env file found. Create one first with the fix functions above.")

def create_gitignore():
    """Create or update .gitignore to exclude .env files"""
    print("📁 Creating/updating .gitignore...")
    
    gitignore_content = """# Environment variables
.env
.env.local
.env.production
.env.staging

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Temporary files
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ Created/updated .gitignore file")

def main():
    """Main function to fix environment issues"""
    print("🚀 Environment Variable Fix Script")
    print("=" * 50)
    
    try:
        # Fix critical security issues
        jwt_key = fix_jwt_secret_key()
        secret_key = fix_secret_key()
        encryption_key = fix_field_encryption_key()
        
        # Fix production settings
        fix_production_settings()
        
        # Create/update .gitignore
        create_gitignore()
        
        print("\n" + "=" * 50)
        print("🎉 Environment issues fixed successfully!")
        print("\n📋 Summary of changes:")
        print(f"  ✅ JWT_SECRET_KEY: {jwt_key[:8]}...{jwt_key[-8:]}")
        print(f"  ✅ SECRET_KEY: {secret_key[:8]}...{secret_key[-8:]}")
        print(f"  ✅ FIELD_ENCRYPTION_KEY: {encryption_key[:8]}...{encryption_key[-8:]}")
        print("  ✅ Production settings configured")
        print("  ✅ .gitignore updated")
        
        print("\n💡 Next steps:")
        print("  1. Review the generated .env file")
        print("  2. Update with your actual API keys and database URLs")
        print("  3. Test your application")
        print("  4. Run the environment validator again")
        
        print("\n⚠️  IMPORTANT:")
        print("  - Keep your .env file secure and never commit it to version control")
        print("  - Update placeholder values with your actual production credentials")
        print("  - Test thoroughly before deploying to production")
        
    except Exception as e:
        print(f"\n❌ Error fixing environment issues: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

