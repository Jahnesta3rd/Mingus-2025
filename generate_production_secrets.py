#!/usr/bin/env python3
"""
Generate Production Secrets for Mingus Application
Creates strong, cryptographically secure secrets for production deployment
"""

import secrets
import string
import os
from datetime import datetime

def generate_strong_secret(length: int = 64) -> str:
    """Generate a cryptographically strong secret of specified length"""
    # Use a combination of letters, digits, and special characters
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_base64_secret(length: int = 64) -> str:
    """Generate a base64-encoded secret (URL-safe)"""
    return secrets.token_urlsafe(length)

def generate_hex_secret(length: int = 64) -> str:
    """Generate a hexadecimal secret"""
    return secrets.token_hex(length // 2)  # token_hex generates 2 chars per byte

def generate_production_secrets():
    """Generate all production secrets"""
    print("🔐 Generating Production Secrets for Mingus Application")
    print("=" * 60)
    
    # Generate secrets with different characteristics
    secrets_data = {
        'SECRET_KEY': generate_strong_secret(64),
        'JWT_SECRET_KEY': generate_base64_secret(64),
        'FIELD_ENCRYPTION_KEY': generate_hex_secret(32),
        'SUPABASE_JWT_SECRET': generate_base64_secret(64),
        'STRIPE_WEBHOOK_SECRET': f"whsec_{generate_hex_secret(32)}",
        'TWILIO_AUTH_TOKEN': generate_strong_secret(32),
        'RESEND_API_KEY': f"re_{generate_hex_secret(32)}",
        'PLAID_SECRET': generate_strong_secret(32),
        'SESSION_SECRET': generate_base64_secret(32),
        'CSRF_SECRET': generate_strong_secret(32),
        'ENCRYPTION_KEY': generate_hex_secret(32),
        'SIGNING_KEY': generate_base64_secret(32)
    }
    
    # Create production secrets file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    secrets_content = f"""# =============================================================================
# MINGUS PRODUCTION SECRETS
# =============================================================================
# Generated: {timestamp}
# 
# ⚠️  CRITICAL SECURITY INFORMATION ⚠️
# 
# These are cryptographically strong secrets for production deployment.
# Store these securely and never commit them to version control.
# 
# Each secret is generated using Python's secrets module for maximum security.
# 
# =============================================================================
# CORE APPLICATION SECRETS
# =============================================================================

# Flask application secret key (64 characters)
SECRET_KEY={secrets_data['SECRET_KEY']}

# JWT token signing secret (64 characters, base64 encoded)
JWT_SECRET_KEY={secrets_data['JWT_SECRET_KEY']}

# Field-level encryption key (32 characters, hex)
FIELD_ENCRYPTION_KEY={secrets_data['FIELD_ENCRYPTION_KEY']}

# Session encryption secret (32 characters, base64)
SESSION_SECRET={secrets_data['SESSION_SECRET']}

# CSRF protection secret (32 characters)
CSRF_SECRET={secrets_data['CSRF_SECRET']}

# =============================================================================
# EXTERNAL SERVICE SECRETS
# =============================================================================

# Supabase JWT secret (64 characters, base64)
SUPABASE_JWT_SECRET={secrets_data['SUPABASE_JWT_SECRET']}

# Stripe webhook secret (with whsec_ prefix)
STRIPE_WEBHOOK_SECRET={secrets_data['STRIPE_WEBHOOK_SECRET']}

# Twilio auth token (32 characters)
TWILIO_AUTH_TOKEN={secrets_data['TWILIO_AUTH_TOKEN']}

# Resend API key (with re_ prefix)
RESEND_API_KEY={secrets_data['RESEND_API_KEY']}

# Plaid secret (32 characters)
PLAID_SECRET={secrets_data['PLAID_SECRET']}

# =============================================================================
# ADDITIONAL SECURITY KEYS
# =============================================================================

# General encryption key (32 characters, hex)
ENCRYPTION_KEY={secrets_data['ENCRYPTION_KEY']}

# Message signing key (32 characters, base64)
SIGNING_KEY={secrets_data['SIGNING_KEY']}

# =============================================================================
# SECURITY NOTES
# =============================================================================
#
# 1. All secrets are cryptographically strong and randomly generated
# 2. Each secret serves a specific security purpose:
#    - SECRET_KEY: Flask application security
#    - JWT_SECRET_KEY: JSON Web Token signing
#    - FIELD_ENCRYPTION_KEY: Database field encryption
#    - SESSION_SECRET: Session data encryption
#    - CSRF_SECRET: Cross-site request forgery protection
#    - SUPABASE_JWT_SECRET: Supabase authentication
#    - STRIPE_WEBHOOK_SECRET: Stripe webhook verification
#    - TWILIO_AUTH_TOKEN: Twilio API authentication
#    - RESEND_API_KEY: Email service authentication
#    - PLAID_SECRET: Financial data API authentication
#    - ENCRYPTION_KEY: General data encryption
#    - SIGNING_KEY: Message integrity verification
#
# 3. Rotate these secrets regularly in production
# 4. Use different secrets for each environment (dev, staging, prod)
# 5. Monitor for any unauthorized access attempts
#
# =============================================================================
"""
    
    # Write secrets to file
    with open('production_secrets.txt', 'w') as f:
        f.write(secrets_content)
    
    # Create .env template with the new secrets
    env_template = f"""# =============================================================================
# MINGUS PRODUCTION ENVIRONMENT
# =============================================================================
# Generated: {timestamp}
# 
# Copy this content to your .env file for production deployment
# 
# =============================================================================
# CORE APPLICATION SECRETS
# =============================================================================

SECRET_KEY={secrets_data['SECRET_KEY']}
JWT_SECRET_KEY={secrets_data['JWT_SECRET_KEY']}
FIELD_ENCRYPTION_KEY={secrets_data['FIELD_ENCRYPTION_KEY']}
SESSION_SECRET={secrets_data['SESSION_SECRET']}
CSRF_SECRET={secrets_data['CSRF_SECRET']}

# =============================================================================
# EXTERNAL SERVICE SECRETS
# =============================================================================

SUPABASE_JWT_SECRET={secrets_data['SUPABASE_JWT_SECRET']}
STRIPE_WEBHOOK_SECRET={secrets_data['STRIPE_WEBHOOK_SECRET']}
TWILIO_AUTH_TOKEN={secrets_data['TWILIO_AUTH_TOKEN']}
RESEND_API_KEY={secrets_data['RESEND_API_KEY']}
PLAID_SECRET={secrets_data['PLAID_SECRET']}

# =============================================================================
# ADDITIONAL SECURITY KEYS
# =============================================================================

ENCRYPTION_KEY={secrets_data['ENCRYPTION_KEY']}
SIGNING_KEY={secrets_data['SIGNING_KEY']}

# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

FLASK_ENV=production
DEBUG=false
TESTING=false

# Security settings
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=86400

# HTTPS enforcement
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here

# =============================================================================
# DATABASE CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

DATABASE_URL=postgresql://username:password@host:5432/mingus_prod
SQLALCHEMY_DATABASE_URI=postgresql://username:password@host:5432/mingus_prod
SQLALCHEMY_TRACK_MODIFICATIONS=false

# =============================================================================
# REDIS CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# =============================================================================
# SUPABASE CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_KEY=your_production_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key

# =============================================================================
# STRIPE CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_SECRET_KEY=sk_live_your_live_secret_key

# =============================================================================
# TWILIO CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

TWILIO_ACCOUNT_SID=your_production_twilio_sid
TWILIO_PHONE_NUMBER=your_production_phone_number

# =============================================================================
# RESEND CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

RESEND_FROM_EMAIL=noreply@yourdomain.com

# =============================================================================
# PLAID CONFIGURATION (UPDATE WITH YOUR VALUES)
# =============================================================================

PLAID_CLIENT_ID=your_plaid_client_id
PLAID_ENV=production

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# =============================================================================
"""
    
    # Write .env template
    with open('.env.production.template', 'w') as f:
        f.write(env_template)
    
    print("✅ Production secrets generated successfully!")
    print()
    print("📁 Files created:")
    print("   - production_secrets.txt (complete secrets with documentation)")
    print("   - .env.production.template (environment template with new secrets)")
    print()
    print("🔐 Generated Secrets Summary:")
    print("   - SECRET_KEY: 64 characters")
    print("   - JWT_SECRET_KEY: 64 characters (base64)")
    print("   - FIELD_ENCRYPTION_KEY: 32 characters (hex)")
    print("   - SESSION_SECRET: 32 characters (base64)")
    print("   - CSRF_SECRET: 32 characters")
    print("   - SUPABASE_JWT_SECRET: 64 characters (base64)")
    print("   - STRIPE_WEBHOOK_SECRET: 32 characters (with whsec_ prefix)")
    print("   - TWILIO_AUTH_TOKEN: 32 characters")
    print("   - RESEND_API_KEY: 32 characters (with re_ prefix)")
    print("   - PLAID_SECRET: 32 characters")
    print("   - ENCRYPTION_KEY: 32 characters (hex)")
    print("   - SIGNING_KEY: 32 characters (base64)")
    print()
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("   1. Store production_secrets.txt securely")
    print("   2. Never commit secrets to version control")
    print("   3. Use different secrets for each environment")
    print("   4. Rotate secrets regularly in production")
    print("   5. Update your .env file with these new secrets")
    print()
    print("📋 Next Steps:")
    print("   1. Copy secrets from production_secrets.txt to your .env file")
    print("   2. Update database and service URLs in .env file")
    print("   3. Test the application with new secrets")
    print("   4. Deploy to production with secure configuration")
    print()
    print("🔒 Security Level: PRODUCTION READY")
    print("=" * 60)

if __name__ == "__main__":
    generate_production_secrets() 