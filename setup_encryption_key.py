#!/usr/bin/env python3
"""
Setup Encryption Key
Generates and sets ENCRYPTION_KEY in .env file
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    return Fernet.generate_key().decode()

def update_env_file(env_path: str, encryption_key: str):
    """Update .env file with encryption key"""
    env_file = Path(env_path)
    
    if not env_file.exists():
        print(f"⚠️  .env file not found at {env_path}")
        print(f"Creating new .env file from env.example...")
        # Try to copy from env.example
        example_file = Path('env.example')
        if example_file.exists():
            env_file.write_text(example_file.read_text())
        else:
            print("❌ env.example not found. Please create .env manually.")
            return False
    
    # Read current .env
    content = env_file.read_text()
    
    # Check if ENCRYPTION_KEY already exists
    lines = content.split('\n')
    updated = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('ENCRYPTION_KEY='):
            # Update existing key
            new_lines.append(f'ENCRYPTION_KEY={encryption_key}')
            updated = True
            print(f"✅ Updated existing ENCRYPTION_KEY")
        else:
            new_lines.append(line)
    
    if not updated:
        # Add new key after Security Configuration section
        found_section = False
        for i, line in enumerate(new_lines):
            if '# Security Configuration' in line:
                found_section = True
            elif found_section and line.strip().startswith('CSRF_SECRET_KEY='):
                # Insert after CSRF_SECRET_KEY
                new_lines.insert(i + 1, f'ENCRYPTION_KEY={encryption_key}')
                updated = True
                print(f"✅ Added ENCRYPTION_KEY to .env file")
                break
        
        if not updated:
            # Just append at the end
            new_lines.append(f'ENCRYPTION_KEY={encryption_key}')
            print(f"✅ Added ENCRYPTION_KEY to end of .env file")
    
    # Write back to file
    env_file.write_text('\n'.join(new_lines))
    return True

def main():
    """Main execution"""
    print("🔐 Setting up encryption key...\n")
    
    # Generate key
    print("Generating new Fernet encryption key...")
    encryption_key = generate_encryption_key()
    print(f"✅ Generated encryption key: {encryption_key[:20]}...\n")
    
    # Update .env file
    env_path = '.env'
    if update_env_file(env_path, encryption_key):
        print(f"\n✅ Successfully updated {env_path}")
        print("\n⚠️  IMPORTANT:")
        print("   - Keep this key secure and never commit it to version control")
        print("   - Store a backup of this key in a secure location")
        print("   - Use the same key in all environments (dev/staging/prod)")
        print("   - If you lose this key, encrypted data cannot be decrypted")
        print(f"\n📋 Your ENCRYPTION_KEY: {encryption_key}")
    else:
        print(f"\n❌ Failed to update {env_path}")
        print(f"\n📋 Manually add this to your .env file:")
        print(f"ENCRYPTION_KEY={encryption_key}")

if __name__ == '__main__':
    main()
