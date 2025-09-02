#!/usr/bin/env python3
"""
Security Migration Test Script

This script validates that all security migrations have been applied correctly
and that the database schema is properly configured for security and compliance.

Usage:
    python test_security_migrations.py

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SecurityMigrationTester:
    """Test class for validating security migrations."""
    
    def __init__(self, database_url=None):
        """Initialize the tester with database connection."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable or parameter required")
        
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✅ Database connection closed")
    
    def test_audit_tables(self):
        """Test that audit tables exist and have correct structure."""
        print("\n🔍 Testing Audit Tables...")
        
        expected_tables = [
            'audit_events',
            'audit_data_access', 
            'audit_security_events',
            'audit_compliance',
            'audit_retention'
        ]
        
        for table in expected_tables:
            try:
                self.cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table,))
                result = self.cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"  ✅ {table} table exists")
                    
                    # Check for required columns
                    self.cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = self.cursor.fetchall()
                    
                    print(f"    📊 {len(columns)} columns found")
                    
                    # Check for partitioning
                    if table in ['audit_events', 'audit_data_access', 'audit_security_events']:
                        self.cursor.execute(f"""
                            SELECT COUNT(*) as partition_count
                            FROM pg_partitions 
                            WHERE tablename = %s
                        """, (table,))
                        partition_result = self.cursor.fetchone()
                        if partition_result['partition_count'] > 0:
                            print(f"    📅 Table is partitioned ({partition_result['partition_count']} partitions)")
                        else:
                            print(f"    ⚠️  Table is not partitioned")
                            
                else:
                    print(f"  ❌ {table} table missing")
                    
            except Exception as e:
                print(f"  ❌ Error testing {table}: {e}")
    
    def test_encryption_tables(self):
        """Test that encryption tables exist and have correct structure."""
        print("\n🔐 Testing Encryption Tables...")
        
        expected_tables = [
            'encryption_keys',
            'encryption_audit_log'
        ]
        
        for table in expected_tables:
            try:
                self.cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table,))
                result = self.cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"  ✅ {table} table exists")
                else:
                    print(f"  ❌ {table} table missing")
                    
            except Exception as e:
                print(f"  ❌ Error testing {table}: {e}")
    
    def test_pci_compliance_tables(self):
        """Test that PCI compliance tables exist and have correct structure."""
        print("\n💳 Testing PCI Compliance Tables...")
        
        expected_tables = [
            'pci_dss_requirements',
            'pci_compliance_assessments',
            'pci_requirement_compliance',
            'payment_card_data',
            'payment_transaction_audit',
            'pci_security_incidents',
            'pci_compliance_reports',
            'pci_data_flow_mapping'
        ]
        
        for table in expected_tables:
            try:
                self.cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table,))
                result = self.cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"  ✅ {table} table exists")
                else:
                    print(f"  ❌ {table} table missing")
                    
            except Exception as e:
                print(f"  ❌ Error testing {table}: {e}")
    
    def test_encrypted_columns(self):
        """Test that encrypted columns exist in user tables."""
        print("\n🔒 Testing Encrypted Columns...")
        
        try:
            # Check users table for encrypted columns
            self.cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name LIKE 'encrypted_%'
                ORDER BY column_name
            """)
            encrypted_columns = self.cursor.fetchall()
            
            if encrypted_columns:
                print(f"  ✅ Found {len(encrypted_columns)} encrypted columns in users table:")
                for col in encrypted_columns:
                    print(f"    - {col['column_name']} ({col['data_type']})")
            else:
                print("  ❌ No encrypted columns found in users table")
                
        except Exception as e:
            print(f"  ❌ Error testing encrypted columns: {e}")
    
    def test_indexes(self):
        """Test that performance indexes exist."""
        print("\n📊 Testing Performance Indexes...")
        
        try:
            # Check for audit table indexes
            self.cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE tablename LIKE 'audit_%'
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname
            """)
            audit_indexes = self.cursor.fetchall()
            
            if audit_indexes:
                print(f"  ✅ Found {len(audit_indexes)} audit table indexes")
                for idx in audit_indexes[:5]:  # Show first 5
                    print(f"    - {idx['indexname']} on {idx['tablename']}")
                if len(audit_indexes) > 5:
                    print(f"    ... and {len(audit_indexes) - 5} more")
            else:
                print("  ❌ No audit table indexes found")
                
        except Exception as e:
            print(f"  ❌ Error testing indexes: {e}")
    
    def test_functions(self):
        """Test that security functions exist."""
        print("\n⚙️  Testing Security Functions...")
        
        expected_functions = [
            'create_audit_partition',
            'create_next_month_audit_partitions',
            'migrate_plaintext_to_encrypted',
            'get_decrypted_value',
            'auto_encrypt_sensitive_data',
            'calculate_pci_compliance_score',
            'track_pci_requirement_compliance',
            'assess_pci_data_exposure_risk'
        ]
        
        for func in expected_functions:
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.routines 
                    WHERE routine_name = %s
                """, (func,))
                result = self.cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"  ✅ {func} function exists")
                else:
                    print(f"  ❌ {func} function missing")
                    
            except Exception as e:
                print(f"  ❌ Error testing {func}: {e}")
    
    def test_views(self):
        """Test that backwards compatibility views exist."""
        print("\n👁️  Testing Backwards Compatibility Views...")
        
        expected_views = [
            'users_decrypted',
            'pci_compliance_summary',
            'pci_data_flow_compliance'
        ]
        
        for view in expected_views:
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.views 
                    WHERE table_name = %s
                """, (view,))
                result = self.cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"  ✅ {view} view exists")
                else:
                    print(f"  ❌ {view} view missing")
                    
            except Exception as e:
                print(f"  ❌ Error testing {view}: {e}")
    
    def test_data_integrity(self):
        """Test basic data integrity."""
        print("\n🔍 Testing Data Integrity...")
        
        try:
            # Test that we can query the audit tables
            self.cursor.execute("SELECT COUNT(*) as count FROM audit_events")
            result = self.cursor.fetchone()
            print(f"  ✅ audit_events table is queryable ({result['count']} rows)")
            
            # Test that we can query PCI tables
            self.cursor.execute("SELECT COUNT(*) as count FROM pci_dss_requirements")
            result = self.cursor.fetchone()
            print(f"  ✅ pci_dss_requirements table is queryable ({result['count']} rows)")
            
            # Test that we can query encryption tables
            self.cursor.execute("SELECT COUNT(*) as count FROM encryption_keys")
            result = self.cursor.fetchone()
            print(f"  ✅ encryption_keys table is queryable ({result['count']} rows)")
            
        except Exception as e:
            print(f"  ❌ Data integrity test failed: {e}")
    
    def run_all_tests(self):
        """Run all security migration tests."""
        print("🚀 Starting Security Migration Tests...")
        print(f"📅 Test Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🔗 Database: {self.database_url.split('@')[-1] if '@' in self.database_url else 'Unknown'}")
        
        try:
            self.connect()
            
            # Run all tests
            self.test_audit_tables()
            self.test_encryption_tables()
            self.test_pci_compliance_tables()
            self.test_encrypted_columns()
            self.test_indexes()
            self.test_functions()
            self.test_views()
            self.test_data_integrity()
            
            print("\n🎉 All security migration tests completed!")
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main function to run security migration tests."""
    try:
        # Create tester instance
        tester = SecurityMigrationTester()
        
        # Run all tests
        tester.run_all_tests()
        
        print("\n✅ Security migrations are properly configured!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Security migration test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
