#!/usr/bin/env python3
"""
Password Hash Migration Utility
Helps migrate from SHA256 to bcrypt password hashing

WARNING: SHA256 hashes cannot be converted to bcrypt.
Users must reset their passwords or migrate on next login.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.password import hash_password, check_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PasswordMigration:
    """Migrate password hashes from SHA256 to bcrypt"""
    
    def __init__(self):
        """Initialize password migration"""
        logger.info("✅ Password migration utility initialized")
    
    def is_sha256_hash(self, password_hash: str) -> bool:
        """
        Check if a hash is SHA256 format
        
        SHA256 hashes are 64 hex characters
        Bcrypt hashes start with $2b$ and are 60 characters
        """
        if not isinstance(password_hash, str):
            return False
        
        # Bcrypt hashes start with $2b$, $2a$, or $2y$
        if password_hash.startswith('$2'):
            return False
        
        # SHA256 is 64 hex characters
        if len(password_hash) == 64:
            try:
                # Try to interpret as hex
                int(password_hash, 16)
                return True
            except ValueError:
                return False
        
        return False
    
    def verify_sha256_password(self, password: str, sha256_hash: str) -> bool:
        """
        Verify a password against a SHA256 hash
        
        This is used during migration to verify old passwords
        """
        if not self.is_sha256_hash(sha256_hash):
            return False
        
        computed_hash = hashlib.sha256(password.encode()).hexdigest()
        return computed_hash == sha256_hash
    
    def migrate_password_on_login(self, password: str, old_hash: str) -> Optional[str]:
        """
        Migrate password hash when user logs in
        
        This function:
        1. Verifies password against old SHA256 hash
        2. If valid, creates new bcrypt hash
        3. Returns new hash for storage
        
        Args:
            password: Plain text password from user
            old_hash: Old SHA256 hash from database
        
        Returns:
            New bcrypt hash if password is valid, None otherwise
        """
        if not self.is_sha256_hash(old_hash):
            # Not an old hash, return None
            return None
        
        # Verify password against old hash
        if not self.verify_sha256_password(password, old_hash):
            logger.warning("Password verification failed against old hash")
            return None
        
        # Password is valid, create new bcrypt hash
        new_hash = hash_password(password)
        logger.info("✅ Password verified and migrated to bcrypt")
        return new_hash
    
    def create_migration_strategy(self) -> Dict[str, Any]:
        """
        Create a migration strategy document
        
        Returns:
            Dictionary with migration strategy
        """
        strategy = {
            'approach': 'migrate_on_login',
            'description': 'Migrate passwords when users log in',
            'steps': [
                '1. User attempts to log in with password',
                '2. Check if stored hash is SHA256 format',
                '3. If SHA256, verify password against SHA256 hash',
                '4. If valid, create new bcrypt hash',
                '5. Store new bcrypt hash in database',
                '6. User is logged in successfully',
                '7. Old SHA256 hash is replaced'
            ],
            'alternative': {
                'approach': 'force_password_reset',
                'description': 'Require all users to reset passwords',
                'steps': [
                    '1. Mark all SHA256 hashes as needing reset',
                    '2. Send password reset emails to all users',
                    '3. Users reset passwords (creates bcrypt hashes)',
                    '4. Remove old SHA256 hashes after reset period'
                ]
            },
            'recommendation': 'Use migrate_on_login for better UX, or force_password_reset for faster migration'
        }
        
        return strategy
    
    def generate_migration_code(self) -> str:
        """
        Generate example code for login migration
        
        Returns:
            Python code example for login migration
        """
        code = '''# Example: Login function with password migration

from backend.utils.password import hash_password, check_password
from migrate_password_hashes import PasswordMigration

def login_user(email: str, password: str):
    """Login user with automatic password migration"""
    migration = PasswordMigration()
    
    # Get user from database
    user = get_user_by_email(email)
    if not user:
        return {'error': 'Invalid credentials'}
    
    stored_hash = user.password_hash
    
    # Check if using old SHA256 hash
    if migration.is_sha256_hash(stored_hash):
        # Verify against old hash
        if migration.verify_sha256_password(password, stored_hash):
            # Migrate to bcrypt
            new_hash = hash_password(password)
            # Update database
            user.password_hash = new_hash
            db.session.commit()
            logger.info(f"Migrated password hash for user {email}")
        else:
            return {'error': 'Invalid password'}
    else:
        # Use new bcrypt verification
        if not check_password(password, stored_hash):
            return {'error': 'Invalid password'}
    
    # Create session/token and return
    return {'success': True, 'user_id': user.id}
'''
        return code


def main():
    """Main execution"""
    print("🔑 Password Hash Migration Utility\n")
    print("=" * 60)
    print("WARNING: SHA256 hashes cannot be converted to bcrypt!")
    print("Users must reset passwords or migrate on next login.")
    print("=" * 60 + "\n")
    
    migration = PasswordMigration()
    
    # Show migration strategy
    print("📋 Migration Strategy:\n")
    strategy = migration.create_migration_strategy()
    
    print(f"Recommended Approach: {strategy['approach']}")
    print(f"Description: {strategy['description']}\n")
    print("Steps:")
    for step in strategy['steps']:
        print(f"  {step}")
    
    print("\n" + "=" * 60)
    print("💡 Example Usage:\n")
    
    # Example: Test migration
    test_password = "test_password_123"
    old_sha256 = hashlib.sha256(test_password.encode()).hexdigest()
    
    print(f"Old SHA256 hash: {old_sha256[:20]}...")
    print(f"Is SHA256 format: {migration.is_sha256_hash(old_sha256)}")
    
    # Verify old password
    if migration.verify_sha256_password(test_password, old_sha256):
        print("✅ Old password verification works")
        
        # Migrate
        new_bcrypt = migration.migrate_password_on_login(test_password, old_sha256)
        if new_bcrypt:
            print(f"✅ New bcrypt hash: {new_bcrypt[:30]}...")
            
            # Verify new hash works
            if check_password(test_password, new_bcrypt):
                print("✅ New bcrypt hash verification works")
    
    print("\n" + "=" * 60)
    print("📝 Generated Migration Code:\n")
    print(migration.generate_migration_code())
    print("=" * 60)


if __name__ == '__main__':
    main()
