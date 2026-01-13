#!/usr/bin/env python3
"""
Manual Encryption Key Generator
Generates a Fernet key without requiring cryptography to be installed first
Uses secrets module to generate a secure key
"""

import secrets
import base64

def generate_fernet_key():
    """
    Generate a Fernet-compatible key
    Fernet keys are 32 bytes, base64 URL-safe encoded
    """
    # Generate 32 random bytes
    key_bytes = secrets.token_bytes(32)
    
    # Encode as base64 URL-safe (Fernet format)
    key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
    
    return key

if __name__ == '__main__':
    key = generate_fernet_key()
    print("=" * 60)
    print("🔐 Encryption Key Generated")
    print("=" * 60)
    print(f"\nENCRYPTION_KEY={key}\n")
    print("=" * 60)
    print("\n⚠️  IMPORTANT:")
    print("   1. Add this key to your .env file:")
    print(f"      ENCRYPTION_KEY={key}")
    print("   2. Keep this key secure and backed up")
    print("   3. Never commit it to version control")
    print("   4. Use the same key across all environments")
    print("=" * 60)
