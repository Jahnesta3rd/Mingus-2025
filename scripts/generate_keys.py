#!/usr/bin/env python3
"""
Key Generation Script for Mingus Application
Generates secure encryption keys for the financial profile feature
"""

import secrets
import base64
import os
from cryptography.fernet import Fernet

def generate_secret_key():
    """Generate a secure Flask secret key"""
    return secrets.token_urlsafe(32)

def generate_django_secret_key():
    """Generate a secure Django secret key"""
    return secrets.token_urlsafe(32)

def generate_field_encryption_key():
    """Generate a 32-character hex key for django-encrypted-model-fields"""
    return secrets.token_hex(16)

def generate_encryption_key():
    """Generate a secure encryption key for custom encryption"""
    return Fernet.generate_key().decode()

def generate_all_keys():
    """Generate all required keys for the application"""
    print("=" * 60)
    print("MINGUS APPLICATION - SECURE KEY GENERATOR")
    print("=" * 60)
    print()
    
    # Generate keys
    secret_key = generate_secret_key()
    django_secret_key = generate_django_secret_key()
    field_encryption_key = generate_field_encryption_key()
    encryption_key = generate_encryption_key()
    
    # Display keys
    print("🔐 GENERATED SECURE KEYS")
    print("-" * 40)
    print(f"SECRET_KEY={secret_key}")
    print(f"DJANGO_SECRET_KEY={django_secret_key}")
    print(f"FIELD_ENCRYPTION_KEY={field_encryption_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    
    # Create .env file content
    env_content = f"""# =====================================================
# MINGUS APPLICATION ENVIRONMENT VARIABLES
# =====================================================
# Generated on: {os.popen('date').read().strip()}
# WARNING: Keep these keys secure and never commit to version control

# =====================================================
# SECURITY & ENCRYPTION
# =====================================================

# Flask Secret Key (required)
SECRET_KEY={secret_key}

# Django Secret Key (for django-encrypted-model-fields compatibility)
DJANGO_SECRET_KEY={django_secret_key}

# Field Encryption Key (32-character key for django-encrypted-model-fields)
FIELD_ENCRYPTION_KEY={field_encryption_key}

# General Encryption Key (for custom encryption)
ENCRYPTION_KEY={encryption_key}

# SSL/HTTPS Settings
SECURE_SSL_REDIRECT=True

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

# Supabase Database URL (with SSL)
DATABASE_URL=your-supabase-url-with-ssl

# Database Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# =====================================================
# SUPABASE CONFIGURATION
# =====================================================

# Supabase Project URL
SUPABASE_URL=https://your-project.supabase.co

# Supabase Anon Key
SUPABASE_KEY=your-supabase-anon-key

# Supabase Service Role Key (for admin operations)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Supabase JWT Secret
SUPABASE_JWT_SECRET=your-jwt-secret

# =====================================================
# APPLICATION SETTINGS
# =====================================================

# Debug Mode (set to False in production)
DEBUG=False

# Log Level
LOG_LEVEL=INFO

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_STORAGE_URL=memory://

# Cache Settings
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# =====================================================
# EMAIL CONFIGURATION
# =====================================================

# SMTP Server
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true

# Email Credentials
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# =====================================================
# FILE UPLOAD SETTINGS
# =====================================================

# Upload Folder
UPLOAD_FOLDER=uploads

# =====================================================
# CORS SETTINGS
# =====================================================

# Allowed Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://localhost:3000

# =====================================================
# FEATURE FLAGS
# =====================================================

# Enable/Disable Features
ENABLE_ONBOARDING=True
ENABLE_USER_PROFILES=True
ENABLE_ENCRYPTION=True
ENABLE_AUDIT_LOGGING=True
BYPASS_AUTH=False

# =====================================================
# PRODUCTION SETTINGS
# =====================================================

# Port (default: 5002)
PORT=5002
"""
    
    # Save to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ SUCCESS: Generated .env file with secure keys")
        print("📁 File saved as: .env")
        print()
    except Exception as e:
        print(f"❌ ERROR: Could not save .env file: {e}")
        print("📋 Copy the keys above manually to your .env file")
        print()
    
    # Security reminders
    print("🔒 SECURITY REMINDERS")
    print("-" * 40)
    print("1. ✅ Never commit .env file to version control")
    print("2. ✅ Use different keys for development, staging, and production")
    print("3. ✅ Rotate keys regularly in production")
    print("4. ✅ Store production keys securely (AWS Secrets Manager, etc.)")
    print("5. ✅ Keep backup copies of keys in secure location")
    print("6. ✅ Monitor for any unauthorized access")
    print()
    
    print("🚀 NEXT STEPS")
    print("-" * 40)
    print("1. Update your Supabase configuration in .env")
    print("2. Set up your database URL with SSL")
    print("3. Configure email settings if needed")
    print("4. Test the application with new keys")
    print("5. Deploy with production keys")
    print()
    
    print("=" * 60)
    print("Key generation complete! 🎉")
    print("=" * 60)

def verify_keys():
    """Verify that the generated keys are valid"""
    print("🔍 VERIFYING KEY VALIDITY")
    print("-" * 40)
    
    # Test secret key generation
    try:
        secret_key = generate_secret_key()
        assert len(secret_key) >= 32
        print("✅ SECRET_KEY: Valid (32+ characters)")
    except Exception as e:
        print(f"❌ SECRET_KEY: Invalid - {e}")
    
    # Test Django secret key
    try:
        django_key = generate_django_secret_key()
        assert len(django_key) >= 32
        print("✅ DJANGO_SECRET_KEY: Valid (32+ characters)")
    except Exception as e:
        print(f"❌ DJANGO_SECRET_KEY: Invalid - {e}")
    
    # Test field encryption key
    try:
        field_key = generate_field_encryption_key()
        assert len(field_key) == 32
        print("✅ FIELD_ENCRYPTION_KEY: Valid (32 hex characters)")
    except Exception as e:
        print(f"❌ FIELD_ENCRYPTION_KEY: Invalid - {e}")
    
    # Test encryption key
    try:
        enc_key = generate_encryption_key()
        Fernet(enc_key.encode())  # Test if valid Fernet key
        print("✅ ENCRYPTION_KEY: Valid (Fernet compatible)")
    except Exception as e:
        print(f"❌ ENCRYPTION_KEY: Invalid - {e}")
    
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_keys()
    else:
        generate_all_keys() 