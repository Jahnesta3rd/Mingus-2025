#!/usr/bin/env python3
"""
Data Migration Utility
Migrates data from old base64 "encryption" to proper Fernet encryption

WARNING: Old data was never actually encrypted (just base64 encoded).
This script helps identify and re-encrypt that data.
"""

import os
import sys
import base64
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.encryption import EncryptionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigration:
    """Migrate encrypted data from old to new encryption"""
    
    def __init__(self):
        """Initialize migration with new encryption service"""
        try:
            self.encryption_service = EncryptionService()
            logger.info("✅ Encryption service initialized")
        except ValueError as e:
            logger.error(f"❌ Failed to initialize encryption service: {e}")
            logger.error("   Make sure ENCRYPTION_KEY is set in .env file")
            sys.exit(1)
    
    def is_old_encryption(self, data: str) -> bool:
        """
        Check if data uses old base64 "encryption"
        
        Old format: "encrypted_<base64>"
        """
        if not isinstance(data, str):
            return False
        
        # Check for old prefix
        if data.startswith("encrypted_"):
            try:
                # Try to decode as base64
                encoded = data[10:]  # Remove "encrypted_" prefix
                base64.b64decode(encoded)
                return True
            except:
                return False
        
        return False
    
    def decode_old_encryption(self, old_data: str) -> str:
        """
        Decode old base64 "encryption"
        
        WARNING: This was never actually encrypted!
        """
        if not self.is_old_encryption(old_data):
            return old_data
        
        try:
            encoded = old_data[10:]  # Remove "encrypted_" prefix
            decoded = base64.b64decode(encoded).decode('utf-8')
            return decoded
        except Exception as e:
            logger.error(f"Failed to decode old encryption: {e}")
            return old_data
    
    def migrate_string(self, old_data: str) -> Optional[str]:
        """
        Migrate a single string from old to new encryption
        
        Returns:
            New encrypted string, or None if migration failed
        """
        if not self.is_old_encryption(old_data):
            # Already using new encryption or not encrypted
            return None
        
        try:
            # Decode old "encryption"
            plaintext = self.decode_old_encryption(old_data)
            
            # Encrypt with new service
            new_encrypted = self.encryption_service.encrypt(plaintext)
            
            logger.debug(f"Migrated string: {len(old_data)} -> {len(new_encrypted)} bytes")
            return new_encrypted
        
        except Exception as e:
            logger.error(f"Failed to migrate string: {e}")
            return None
    
    def migrate_dict(self, data: Dict[str, Any], fields_to_migrate: List[str] = None) -> Dict[str, Any]:
        """
        Migrate a dictionary, re-encrypting specified fields
        
        Args:
            data: Dictionary to migrate
            fields_to_migrate: List of field names to migrate (None = all string fields)
        
        Returns:
            Migrated dictionary
        """
        migrated = data.copy()
        migrated_count = 0
        
        # If no fields specified, check all string values
        if fields_to_migrate is None:
            fields_to_migrate = [k for k, v in data.items() if isinstance(v, str)]
        
        for field in fields_to_migrate:
            if field not in data:
                continue
            
            value = data[field]
            if not isinstance(value, str):
                continue
            
            if self.is_old_encryption(value):
                new_value = self.migrate_string(value)
                if new_value:
                    migrated[field] = new_value
                    migrated_count += 1
                    logger.info(f"  ✅ Migrated field: {field}")
        
        if migrated_count > 0:
            logger.info(f"Migrated {migrated_count} field(s) in dictionary")
        
        return migrated
    
    def scan_database_for_old_encryption(self, db_path: str = None) -> Dict[str, Any]:
        """
        Scan database for old encryption patterns
        
        This is a helper to identify what needs migration.
        Actual migration should be done through your ORM/database layer.
        """
        logger.info("Scanning for old encryption patterns...")
        logger.warning("⚠️  This is a placeholder. Implement based on your database schema.")
        logger.warning("   Check tables/collections that store encrypted data.")
        
        # Example: SQLite database scan
        if db_path and Path(db_path).exists():
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            results = {
                'tables_scanned': len(tables),
                'old_encryption_found': [],
                'migration_needed': []
            }
            
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col_id, col_name, col_type, not_null, default_val, pk in columns:
                    if col_type.upper() in ('TEXT', 'VARCHAR', 'STRING'):
                        # Sample a few rows
                        cursor.execute(f"SELECT {col_name} FROM {table_name} LIMIT 10")
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            if row[0] and self.is_old_encryption(str(row[0])):
                                results['old_encryption_found'].append({
                                    'table': table_name,
                                    'column': col_name
                                })
                                break
            
            conn.close()
            return results
        
        return {'error': 'Database path not provided or not found'}


def main():
    """Main migration execution"""
    print("🔄 Data Encryption Migration Utility\n")
    print("=" * 60)
    print("WARNING: Old 'encryption' was just base64 encoding!")
    print("This script helps migrate to proper Fernet encryption.")
    print("=" * 60 + "\n")
    
    migration = DataMigration()
    
    # Example usage
    print("Example: Migrating test data...\n")
    
    # Test old encryption format
    old_encrypted = "encrypted_" + base64.b64encode("sensitive data".encode()).decode()
    print(f"Old format: {old_encrypted[:50]}...")
    
    # Migrate
    new_encrypted = migration.migrate_string(old_encrypted)
    if new_encrypted:
        print(f"✅ Migrated to new format: {new_encrypted[:50]}...")
        
        # Verify it works
        decrypted = migration.encryption_service.decrypt(new_encrypted)
        print(f"✅ Decryption test: {decrypted}")
    else:
        print("❌ Migration failed")
    
    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("1. Identify all database tables/collections with encrypted data")
    print("2. Run migration script for each table")
    print("3. Verify migrated data can be decrypted")
    print("4. Remove old encrypted data after verification")
    print("=" * 60)


if __name__ == '__main__':
    main()
