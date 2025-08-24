#!/usr/bin/env python3
"""
Secure Key Generator for MINGUS Application
Generates secure random keys for development and production environments.
"""

import os
import sys
import argparse
import secrets
import hashlib
import base64
import json
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import re

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.secure_config import SecureConfigManager

class SecureKeyGenerator:
    """Secure key generator for the MINGUS application"""
    
    def __init__(self, env_file: str = None):
        """Initialize the secure key generator"""
        self.env_file = env_file
        self.generated_keys = {}
        
        # Initialize secure config manager
        try:
            self.secure_config = SecureConfigManager(env_file)
        except Exception as e:
            print(f"Warning: Could not initialize secure config manager: {e}")
            self.secure_config = None
    
    def generate_all_keys(self, environment: str = 'development') -> Dict[str, str]:
        """Generate all required keys for the specified environment"""
        print(f"Generating secure keys for {environment} environment...")
        
        keys = {}
        
        # Flask and Django keys
        keys['SECRET_KEY'] = self._generate_flask_secret_key()
        keys['DJANGO_SECRET_KEY'] = self._generate_django_secret_key()
        keys['FIELD_ENCRYPTION_KEY'] = self._generate_encryption_key()
        keys['CONFIG_ENCRYPTION_KEY'] = self._generate_encryption_key()
        
        # JWT and session keys
        keys['SUPABASE_JWT_SECRET'] = self._generate_jwt_secret()
        keys['SESSION_ENCRYPTION_KEY'] = self._generate_encryption_key()
        
        # API keys (mock for development)
        if environment == 'development':
            keys['STRIPE_TEST_SECRET_KEY'] = self._generate_stripe_test_key()
            keys['STRIPE_TEST_PUBLISHABLE_KEY'] = self._generate_stripe_publishable_key()
            keys['PLAID_SANDBOX_CLIENT_ID'] = self._generate_plaid_client_id()
            keys['PLAID_SANDBOX_SECRET'] = self._generate_plaid_secret()
            keys['TWILIO_ACCOUNT_SID'] = self._generate_twilio_account_sid()
            keys['TWILIO_AUTH_TOKEN'] = self._generate_twilio_auth_token()
            keys['RESEND_API_KEY'] = self._generate_resend_api_key()
        
        # Webhook secrets
        keys['STRIPE_WEBHOOK_SECRET'] = self._generate_webhook_secret()
        keys['PLAID_WEBHOOK_SECRET'] = self._generate_webhook_secret()
        keys['RESEND_WEBHOOK_SECRET'] = self._generate_webhook_secret()
        
        # Database encryption keys
        keys['DATABASE_ENCRYPTION_KEY'] = self._generate_encryption_key()
        keys['BACKUP_ENCRYPTION_KEY'] = self._generate_encryption_key()
        
        # Cache and session keys
        keys['REDIS_ENCRYPTION_KEY'] = self._generate_encryption_key()
        keys['CACHE_ENCRYPTION_KEY'] = self._generate_encryption_key()
        
        # Monitoring and logging keys
        keys['LOGGING_ENCRYPTION_KEY'] = self._generate_encryption_key()
        keys['METRICS_ENCRYPTION_KEY'] = self._generate_encryption_key()
        
        self.generated_keys = keys
        return keys
    
    def _generate_flask_secret_key(self) -> str:
        """Generate a secure Flask secret key"""
        return secrets.token_urlsafe(32)
    
    def _generate_django_secret_key(self) -> str:
        """Generate a secure Django secret key"""
        # Django secret keys are typically 50 characters
        return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for _ in range(50))
    
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return secrets.token_urlsafe(32)
    
    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(32)
    
    def _generate_stripe_test_key(self) -> str:
        """Generate a mock Stripe test secret key"""
        return f"sk_test_{secrets.token_hex(24)}"
    
    def _generate_stripe_publishable_key(self) -> str:
        """Generate a mock Stripe publishable key"""
        return f"pk_test_{secrets.token_hex(24)}"
    
    def _generate_plaid_client_id(self) -> str:
        """Generate a mock Plaid client ID"""
        return secrets.token_hex(12)  # 24 characters
    
    def _generate_plaid_secret(self) -> str:
        """Generate a mock Plaid secret"""
        return secrets.token_hex(15)  # 30 characters
    
    def _generate_twilio_account_sid(self) -> str:
        """Generate a mock Twilio account SID"""
        return f"AC{secrets.token_hex(16)}"  # 34 characters total
    
    def _generate_twilio_auth_token(self) -> str:
        """Generate a mock Twilio auth token"""
        return secrets.token_hex(16)  # 32 characters
    
    def _generate_resend_api_key(self) -> str:
        """Generate a mock Resend API key"""
        return f"re_{secrets.token_hex(20)}"  # 42 characters total
    
    def _generate_webhook_secret(self) -> str:
        """Generate a secure webhook secret"""
        return secrets.token_urlsafe(32)
    
    def validate_key_strength(self, key: str, key_type: str) -> Dict[str, Any]:
        """Validate the strength of a generated key"""
        validation = {
            'key_type': key_type,
            'length': len(key),
            'unique_chars': len(set(key)),
            'entropy_ratio': len(set(key)) / len(key),
            'has_uppercase': bool(re.search(r'[A-Z]', key)),
            'has_lowercase': bool(re.search(r'[a-z]', key)),
            'has_digits': bool(re.search(r'\d', key)),
            'has_special': bool(re.search(r'[^A-Za-z0-9]', key)),
            'is_strong': True,
            'issues': []
        }
        
        # Check minimum length
        min_lengths = {
            'SECRET_KEY': 32,
            'DJANGO_SECRET_KEY': 50,
            'FIELD_ENCRYPTION_KEY': 32,
            'CONFIG_ENCRYPTION_KEY': 32,
            'default': 32
        }
        
        min_length = min_lengths.get(key_type, min_lengths['default'])
        if len(key) < min_length:
            validation['is_strong'] = False
            validation['issues'].append(f"Too short: {len(key)} chars (minimum {min_length})")
        
        # Check entropy
        if validation['entropy_ratio'] < 0.3:
            validation['is_strong'] = False
            validation['issues'].append(f"Low entropy: {validation['entropy_ratio']:.2f}")
        
        # Check for weak patterns
        weak_patterns = [
            (r'^dev-', 'Development prefix'),
            (r'^test-', 'Test prefix'),
            (r'^password$', 'Common password'),
            (r'^secret$', 'Common secret'),
            (r'^key$', 'Common key'),
            (r'^123456', 'Sequential numbers'),
            (r'^admin', 'Admin prefix'),
            (r'^default', 'Default prefix'),
            (r'^changeme', 'Change me'),
            (r'^temp', 'Temporary'),
            (r'^demo', 'Demo'),
        ]
        
        for pattern, description in weak_patterns:
            if re.search(pattern, key.lower()):
                validation['is_strong'] = False
                validation['issues'].append(f"Weak pattern: {description}")
                break
        
        return validation
    
    def validate_all_keys(self) -> Dict[str, Dict[str, Any]]:
        """Validate all generated keys"""
        validations = {}
        
        for key_name, key_value in self.generated_keys.items():
            validations[key_name] = self.validate_key_strength(key_value, key_name)
        
        return validations
    
    def save_to_env_file(self, output_file: str = '.env.generated', include_comments: bool = True):
        """Save generated keys to an environment file"""
        print(f"Saving generated keys to {output_file}...")
        
        with open(output_file, 'w') as f:
            if include_comments:
                f.write("# =====================================================\n")
                f.write("# MINGUS APPLICATION - GENERATED SECURE KEYS\n")
                f.write("# =====================================================\n")
                f.write(f"# Generated on: {datetime.now().isoformat()}\n")
                f.write("# WARNING: These are development keys. Use different keys in production!\n")
                f.write("# =====================================================\n\n")
            
            for key_name, key_value in self.generated_keys.items():
                if include_comments:
                    f.write(f"# {key_name}: Secure random key\n")
                f.write(f"{key_name}={key_value}\n")
                if include_comments:
                    f.write("\n")
        
        print(f"Keys saved to {output_file}")
    
    def save_to_json(self, output_file: str = 'generated_keys.json'):
        """Save generated keys to a JSON file"""
        print(f"Saving generated keys to {output_file}...")
        
        data = {
            'generated_at': datetime.now().isoformat(),
            'environment': 'development',
            'keys': self.generated_keys,
            'validations': self.validate_all_keys()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Keys saved to {output_file}")
    
    def print_key_summary(self):
        """Print a summary of generated keys"""
        print("\n" + "="*80)
        print("GENERATED SECURE KEYS SUMMARY")
        print("="*80)
        
        validations = self.validate_all_keys()
        
        for key_name, key_value in self.generated_keys.items():
            validation = validations[key_name]
            status = "✅ STRONG" if validation['is_strong'] else "⚠️  WEAK"
            
            print(f"\n{key_name}:")
            print(f"  Status: {status}")
            print(f"  Length: {validation['length']} characters")
            print(f"  Entropy: {validation['entropy_ratio']:.2f}")
            print(f"  Preview: {key_value[:16]}...")
            
            if validation['issues']:
                print(f"  Issues: {', '.join(validation['issues'])}")
        
        # Summary statistics
        strong_keys = sum(1 for v in validations.values() if v['is_strong'])
        total_keys = len(validations)
        
        print(f"\n" + "="*80)
        print(f"SUMMARY: {strong_keys}/{total_keys} keys are strong")
        
        if strong_keys == total_keys:
            print("🎉 All generated keys meet security requirements!")
        else:
            print("⚠️  Some keys may need regeneration for better security.")
        
        print("="*80)
    
    def update_existing_env_file(self, env_file: str = '.env'):
        """Update an existing .env file with generated keys"""
        if not Path(env_file).exists():
            print(f"Environment file {env_file} does not exist. Creating new file...")
            self.save_to_env_file(env_file)
            return
        
        print(f"Updating existing environment file {env_file}...")
        
        # Read existing file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Create a map of existing keys
        existing_keys = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                existing_keys[key] = value
        
        # Update with generated keys
        updated_keys = existing_keys.copy()
        for key_name, key_value in self.generated_keys.items():
            updated_keys[key_name] = key_value
        
        # Write updated file
        with open(env_file, 'w') as f:
            for line in lines:
                if line.strip() and not line.strip().startswith('#') and '=' in line:
                    key = line.split('=', 1)[0]
                    if key in updated_keys:
                        f.write(f"{key}={updated_keys[key]}\n")
                    else:
                        f.write(line)
                else:
                    f.write(line)
            
            # Add any new keys that weren't in the original file
            for key_name, key_value in self.generated_keys.items():
                if key_name not in existing_keys:
                    f.write(f"\n# Generated secure key\n{key_name}={key_value}\n")
        
        print(f"Updated {env_file} with generated keys")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='MINGUS Application Secure Key Generator')
    parser.add_argument('--env-file', '-e', default='.env', help='Environment file to read from')
    parser.add_argument('--output', '-o', default='.env.generated', help='Output file for generated keys')
    parser.add_argument('--environment', '--env', default='development', 
                       choices=['development', 'testing', 'production'],
                       help='Target environment')
    parser.add_argument('--update-existing', '-u', action='store_true', 
                       help='Update existing .env file instead of creating new one')
    parser.add_argument('--json', '-j', action='store_true', 
                       help='Also save keys to JSON file')
    parser.add_argument('--no-comments', action='store_true', 
                       help='Skip comments in output file')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate existing keys, don\'t generate new ones')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = SecureKeyGenerator(args.env_file)
    
    if args.validate_only:
        # Validate existing keys
        if generator.secure_config:
            print("Validating existing keys...")
            existing_keys = {}
            for key in ['SECRET_KEY', 'FIELD_ENCRYPTION_KEY', 'DJANGO_SECRET_KEY']:
                value = generator.secure_config.get(key)
                if value:
                    existing_keys[key] = value
            
            if existing_keys:
                generator.generated_keys = existing_keys
                generator.print_key_summary()
            else:
                print("No existing keys found to validate.")
        else:
            print("Could not initialize secure config manager for validation.")
    else:
        # Generate new keys
        keys = generator.generate_all_keys(args.environment)
        
        # Print summary
        generator.print_key_summary()
        
        # Save keys
        if args.update_existing:
            generator.update_existing_env_file(args.env_file)
        else:
            generator.save_to_env_file(args.output, not args.no_comments)
        
        if args.json:
            generator.save_to_json()
        
        print(f"\n✅ Secure key generation complete!")
        print(f"📁 Keys saved to: {args.output}")
        if args.json:
            print(f"📄 JSON summary saved to: generated_keys.json")
        
        if args.environment == 'development':
            print("\n⚠️  REMINDER: These are development keys. Use different keys in production!")

if __name__ == '__main__':
    main() 