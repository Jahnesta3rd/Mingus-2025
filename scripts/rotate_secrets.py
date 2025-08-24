#!/usr/bin/env python3
"""
Secret Rotation Script for MINGUS Application
============================================

This script securely rotates configuration secrets and provides backup functionality
for the secure configuration system.

Usage:
    python scripts/rotate_secrets.py [--env-file .env] [--backup] [--force] [--secrets SECRET1,SECRET2]

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import argparse
import json
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.secure_config import (
    SecureConfigManager, 
    SecurityConfig, 
    SecurityLevel,
    ConfigValidationError,
    SecretRotationError
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecretRotator:
    """Secure secret rotation manager"""
    
    def __init__(self, env_file: Optional[str] = None, backup_dir: str = 'backups/secrets'):
        """
        Initialize secret rotator
        
        Args:
            env_file: Path to environment file
            backup_dir: Directory for backups
        """
        self.env_file = env_file
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.security_config = SecurityConfig(
            enable_encryption=True,
            enable_audit_logging=True,
            security_level=SecurityLevel.HIGH
        )
        
        # Load environment variables from file if specified
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)
        
        # Initialize secure config manager
        try:
            self.config_manager = SecureConfigManager(env_file, self.security_config)
        except ConfigValidationError as e:
            logger.error(f"Failed to initialize secure config manager: {e}")
            raise
    
    def _load_env_file(self, env_file: str):
        """Load environment variables from file"""
        logger.info(f"Loading environment variables from {env_file}")
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
    
    def get_rotatable_secrets(self) -> List[str]:
        """Get list of secrets that can be rotated"""
        rotatable_secrets = []
        
        for key, rule in self.config_manager._validation_rules.items():
            if rule.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                rotatable_secrets.append(key)
        
        return rotatable_secrets
    
    def backup_current_secrets(self) -> str:
        """
        Backup current secrets to a timestamped file
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'secrets_backup_{timestamp}.json'
        
        logger.info(f"Creating backup: {backup_file}")
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'env_file': self.env_file,
            'secrets': {}
        }
        
        # Backup current secrets
        for secret_key in self.get_rotatable_secrets():
            value = self.config_manager.get(secret_key)
            if value:
                backup_data['secrets'][secret_key] = value
        
        # Write backup file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Backup created successfully: {backup_file}")
        return str(backup_file)
    
    def rotate_secret(self, secret_key: str, force: bool = False) -> str:
        """
        Rotate a specific secret
        
        Args:
            secret_key: Secret key to rotate
            force: Force rotation even if secret is strong
            
        Returns:
            New secret value
        """
        logger.info(f"Rotating secret: {secret_key}")
        
        # Check if secret exists
        current_value = self.config_manager.get(secret_key)
        if not current_value:
            raise SecretRotationError(f"Secret {secret_key} not found")
        
        # Check if secret needs rotation (unless forced)
        if not force and not self._is_weak_secret(current_value):
            logger.info(f"Secret {secret_key} appears strong. Use --force to rotate anyway.")
            return current_value
        
        try:
            # Rotate the secret
            new_secret = self.config_manager.rotate_secret(secret_key)
            logger.info(f"Successfully rotated {secret_key}")
            return new_secret
            
        except SecretRotationError as e:
            logger.error(f"Failed to rotate {secret_key}: {e}")
            raise
    
    def rotate_multiple_secrets(self, secret_keys: List[str], force: bool = False) -> Dict[str, str]:
        """
        Rotate multiple secrets
        
        Args:
            secret_keys: List of secret keys to rotate
            force: Force rotation even if secrets are strong
            
        Returns:
            Dictionary of rotated secrets
        """
        results = {}
        
        for secret_key in secret_keys:
            try:
                new_secret = self.rotate_secret(secret_key, force)
                results[secret_key] = new_secret
            except SecretRotationError as e:
                logger.error(f"Failed to rotate {secret_key}: {e}")
                results[secret_key] = f"ERROR: {e}"
        
        return results
    
    def rotate_all_secrets(self, force: bool = False) -> Dict[str, str]:
        """
        Rotate all rotatable secrets
        
        Args:
            force: Force rotation even if secrets are strong
            
        Returns:
            Dictionary of all rotated secrets
        """
        all_secrets = self.get_rotatable_secrets()
        return self.rotate_multiple_secrets(all_secrets, force)
    
    def _is_weak_secret(self, secret: str) -> bool:
        """Check if a secret is weak"""
        if not secret:
            return True
        
        # Check for common weak patterns
        weak_patterns = [
            'dev-', 'test-', 'default-', 'password', 'secret', 'key',
            '123456', 'abcdef', 'changeme', 'temporary'
        ]
        
        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                return True
        
        # Check entropy (simplified)
        if len(set(secret)) < len(secret) * 0.5:
            return True
        
        return False
    
    def update_env_file(self, rotated_secrets: Dict[str, str]) -> bool:
        """
        Update environment file with rotated secrets
        
        Args:
            rotated_secrets: Dictionary of rotated secrets
            
        Returns:
            True if successful, False otherwise
        """
        if not self.env_file or not Path(self.env_file).exists():
            logger.warning("No environment file specified or file doesn't exist")
            return False
        
        try:
            # Read current file
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
            
            # Update secrets
            updated_lines = []
            updated_secrets = set()
            
            for line in lines:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    
                    if key in rotated_secrets:
                        # Update the secret
                        new_value = rotated_secrets[key]
                        if not new_value.startswith('ERROR:'):
                            updated_lines.append(f"{key}={new_value}\n")
                            updated_secrets.add(key)
                            logger.info(f"Updated {key} in {self.env_file}")
                        else:
                            # Keep original value if rotation failed
                            updated_lines.append(line)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Write updated file
            with open(self.env_file, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info(f"Updated {len(updated_secrets)} secrets in {self.env_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update environment file: {e}")
            return False
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """
        Get status of all rotatable secrets
        
        Returns:
            Status dictionary
        """
        status = {
            'rotatable_secrets': [],
            'weak_secrets': [],
            'strong_secrets': [],
            'missing_secrets': []
        }
        
        for secret_key in self.get_rotatable_secrets():
            value = self.config_manager.get(secret_key)
            
            if not value:
                status['missing_secrets'].append(secret_key)
            elif self._is_weak_secret(value):
                status['weak_secrets'].append(secret_key)
            else:
                status['strong_secrets'].append(secret_key)
            
            status['rotatable_secrets'].append(secret_key)
        
        return status
    
    def print_rotation_status(self):
        """Print current rotation status"""
        status = self.get_rotation_status()
        
        print("\n" + "="*80)
        print("MINGUS APPLICATION - SECRET ROTATION STATUS")
        print("="*80)
        
        print(f"\n📊 Rotatable Secrets: {len(status['rotatable_secrets'])}")
        print(f"🟢 Strong Secrets: {len(status['strong_secrets'])}")
        print(f"🔴 Weak Secrets: {len(status['weak_secrets'])}")
        print(f"❌ Missing Secrets: {len(status['missing_secrets'])}")
        
        if status['weak_secrets']:
            print(f"\n⚠️  Weak Secrets (recommended to rotate):")
            for secret in status['weak_secrets']:
                print(f"  - {secret}")
        
        if status['missing_secrets']:
            print(f"\n❌ Missing Secrets:")
            for secret in status['missing_secrets']:
                print(f"  - {secret}")
        
        if status['strong_secrets']:
            print(f"\n🟢 Strong Secrets:")
            for secret in status['strong_secrets']:
                print(f"  - {secret}")
        
        print("\n" + "="*80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Rotate MINGUS application secrets')
    parser.add_argument('--env-file', default='.env', help='Path to environment file')
    parser.add_argument('--backup', action='store_true', help='Create backup before rotation')
    parser.add_argument('--force', action='store_true', help='Force rotation of strong secrets')
    parser.add_argument('--secrets', help='Comma-separated list of secrets to rotate')
    parser.add_argument('--all', action='store_true', help='Rotate all rotatable secrets')
    parser.add_argument('--status', action='store_true', help='Show rotation status only')
    parser.add_argument('--backup-dir', default='backups/secrets', help='Backup directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be rotated without doing it')
    
    args = parser.parse_args()
    
    try:
        # Initialize rotator
        rotator = SecretRotator(args.env_file, args.backup_dir)
        
        # Show status only
        if args.status:
            rotator.print_rotation_status()
            return
        
        # Determine which secrets to rotate
        if args.all:
            secrets_to_rotate = rotator.get_rotatable_secrets()
        elif args.secrets:
            secrets_to_rotate = [s.strip() for s in args.secrets.split(',')]
        else:
            # Default to weak secrets only
            status = rotator.get_rotation_status()
            secrets_to_rotate = status['weak_secrets']
        
        if not secrets_to_rotate:
            print("No secrets to rotate.")
            return
        
        # Show what will be rotated
        print(f"\n🔄 Secrets to rotate: {', '.join(secrets_to_rotate)}")
        
        if args.dry_run:
            print("Dry run mode - no changes will be made")
            return
        
        # Create backup if requested
        backup_file = None
        if args.backup:
            backup_file = rotator.backup_current_secrets()
        
        # Perform rotation
        print(f"\n🔄 Rotating {len(secrets_to_rotate)} secrets...")
        rotated_secrets = rotator.rotate_multiple_secrets(secrets_to_rotate, args.force)
        
        # Show results
        print(f"\n✅ Rotation Results:")
        for secret_key, new_value in rotated_secrets.items():
            if new_value.startswith('ERROR:'):
                print(f"  ❌ {secret_key}: {new_value}")
            else:
                print(f"  ✅ {secret_key}: Rotated successfully")
        
        # Update environment file
        if rotator.update_env_file(rotated_secrets):
            print(f"\n📝 Environment file updated: {args.env_file}")
        else:
            print(f"\n⚠️  Environment file not updated. Manual update required.")
        
        # Show new status
        print(f"\n📊 New Rotation Status:")
        rotator.print_rotation_status()
        
        if backup_file:
            print(f"\n💾 Backup created: {backup_file}")
        
        print(f"\n🔐 Remember to restart the application after secret rotation!")
        
    except Exception as e:
        logger.error(f"Secret rotation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 