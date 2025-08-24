#!/usr/bin/env python3
"""
Update .env file with new strong secrets
Safely updates existing .env file with new cryptographically strong secrets
"""

import os
import re
from datetime import datetime

def read_production_secrets():
    """Read the generated production secrets"""
    secrets = {}
    try:
        with open('production_secrets.txt', 'r') as f:
            content = f.read()
            
        # Extract secrets using regex
        secret_patterns = {
            'SECRET_KEY': r'SECRET_KEY=([^\n]+)',
            'JWT_SECRET_KEY': r'JWT_SECRET_KEY=([^\n]+)',
            'FIELD_ENCRYPTION_KEY': r'FIELD_ENCRYPTION_KEY=([^\n]+)',
            'SESSION_SECRET': r'SESSION_SECRET=([^\n]+)',
            'CSRF_SECRET': r'CSRF_SECRET=([^\n]+)',
            'SUPABASE_JWT_SECRET': r'SUPABASE_JWT_SECRET=([^\n]+)',
            'STRIPE_WEBHOOK_SECRET': r'STRIPE_WEBHOOK_SECRET=([^\n]+)',
            'TWILIO_AUTH_TOKEN': r'TWILIO_AUTH_TOKEN=([^\n]+)',
            'RESEND_API_KEY': r'RESEND_API_KEY=([^\n]+)',
            'PLAID_SECRET': r'PLAID_SECRET=([^\n]+)',
            'ENCRYPTION_KEY': r'ENCRYPTION_KEY=([^\n]+)',
            'SIGNING_KEY': r'SIGNING_KEY=([^\n]+)'
        }
        
        for key, pattern in secret_patterns.items():
            match = re.search(pattern, content)
            if match:
                secrets[key] = match.group(1)
                
        return secrets
    except FileNotFoundError:
        print("❌ production_secrets.txt not found. Run generate_production_secrets.py first.")
        return None
    except Exception as e:
        print(f"❌ Error reading production secrets: {e}")
        return None

def backup_env_file():
    """Create a backup of the current .env file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'.env.backup_{timestamp}'
    
    try:
        with open('.env', 'r') as src:
            with open(backup_filename, 'w') as dst:
                dst.write(src.read())
        print(f"✅ Created backup: {backup_filename}")
        return backup_filename
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def update_env_file(secrets):
    """Update .env file with new secrets"""
    try:
        # Read current .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        # Update each secret
        updated_content = content
        updated_count = 0
        
        for secret_name, secret_value in secrets.items():
            # Pattern to match the secret in .env file
            pattern = rf'^{secret_name}=.*$'
            replacement = f'{secret_name}={secret_value}'
            
            if re.search(pattern, updated_content, re.MULTILINE):
                updated_content = re.sub(pattern, replacement, updated_content, flags=re.MULTILINE)
                updated_count += 1
                print(f"   ✅ Updated {secret_name}")
            else:
                # Add new secret if it doesn't exist
                updated_content += f'\n{replacement}'
                updated_count += 1
                print(f"   ➕ Added {secret_name}")
        
        # Write updated content back to .env file
        with open('.env', 'w') as f:
            f.write(updated_content)
        
        print(f"\n✅ Successfully updated {updated_count} secrets in .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main function to update .env file with new secrets"""
    print("🔐 Updating .env file with new strong secrets")
    print("=" * 50)
    
    # Read production secrets
    print("1. Reading production secrets...")
    secrets = read_production_secrets()
    if not secrets:
        return False
    
    print(f"   ✅ Found {len(secrets)} secrets to update")
    
    # Create backup
    print("2. Creating backup of current .env file...")
    backup_file = backup_env_file()
    if not backup_file:
        return False
    
    # Update .env file
    print("3. Updating .env file with new secrets...")
    success = update_env_file(secrets)
    
    if success:
        print("\n🎉 .env file updated successfully!")
        print("=" * 50)
        print("📋 Updated Secrets:")
        for secret_name in secrets.keys():
            print(f"   - {secret_name}")
        
        print(f"\n📁 Backup created: {backup_file}")
        print("\n⚠️  IMPORTANT:")
        print("   1. Test your application with the new secrets")
        print("   2. Keep the backup file for rollback if needed")
        print("   3. Never commit the .env file to version control")
        print("   4. Store production_secrets.txt securely")
        
        return True
    else:
        print("\n❌ Failed to update .env file")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 