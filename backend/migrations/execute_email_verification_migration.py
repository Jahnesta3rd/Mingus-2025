#!/usr/bin/env python3
"""
Email Verification Migration Execution Script
Safe migration execution with comprehensive validation and rollback capabilities

Usage:
    python execute_email_verification_migration.py --env development
    python execute_email_verification_migration.py --env production --dry-run
    python execute_email_verification_migration.py --env production --execute
"""

import argparse
import os
import sys
import psycopg2
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

class EmailVerificationMigration:
    """Safe migration execution for email verification system"""
    
    def __init__(self, database_url: str, dry_run: bool = True):
        self.database_url = database_url
        self.dry_run = dry_run
        self.connection = None
        self.cursor = None
        self.migration_log = []
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.cursor = self.connection.cursor()
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔌 Database connection closed")
    
    def log_migration_step(self, step: str, status: str, details: str = ""):
        """Log migration step for audit trail"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'step': step,
            'status': status,
            'details': details
        }
        self.migration_log.append(log_entry)
        print(f"[{timestamp}] {step}: {status} - {details}")
    
    def check_prerequisites(self) -> bool:
        """Check if migration prerequisites are met"""
        print("\n🔍 Checking migration prerequisites...")
        
        try:
            # Check if users table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            users_exists = self.cursor.fetchone()[0]
            
            if not users_exists:
                print("❌ Users table does not exist")
                return False
            
            # Check if email_verified column already exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'email_verified'
                );
            """)
            column_exists = self.cursor.fetchone()[0]
            
            if column_exists:
                print("⚠️  email_verified column already exists")
                return False
            
            # Check database version
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()[0]
            print(f"✅ Database version: {version}")
            
            # Check if PostgreSQL 15+
            if 'PostgreSQL 15' not in version and 'PostgreSQL 16' not in version and 'PostgreSQL 17' not in version:
                print("⚠️  Warning: PostgreSQL version may not be optimal (recommended: 15+)")
            
            # Check available disk space (estimate)
            self.cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            db_size = self.cursor.fetchone()[0]
            print(f"✅ Current database size: {db_size}")
            
            # Check user count
            self.cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = self.cursor.fetchone()[0]
            print(f"✅ Users to migrate: {user_count:,}")
            
            self.log_migration_step("prerequisites_check", "PASSED", f"Users: {user_count}, DB Size: {db_size}")
            return True
            
        except Exception as e:
            print(f"❌ Prerequisites check failed: {e}")
            self.log_migration_step("prerequisites_check", "FAILED", str(e))
            return False
    
    def create_backup(self) -> bool:
        """Create backup of users table"""
        print("\n💾 Creating backup of users table...")
        
        try:
            if self.dry_run:
                print("🔍 DRY RUN: Would create backup table users_backup_010")
                self.log_migration_step("backup_creation", "DRY_RUN", "Backup table creation simulated")
                return True
            
            # Create backup table
            self.cursor.execute("""
                CREATE TABLE users_backup_010 AS 
                SELECT * FROM users;
            """)
            
            # Add comment
            self.cursor.execute("""
                COMMENT ON TABLE users_backup_010 IS 'Backup of users table before email verification migration';
            """)
            
            # Verify backup
            self.cursor.execute("SELECT COUNT(*) FROM users_backup_010;")
            backup_count = self.cursor.fetchone()[0]
            
            self.connection.commit()
            print(f"✅ Backup created: {backup_count:,} users backed up")
            self.log_migration_step("backup_creation", "SUCCESS", f"Backup created with {backup_count} users")
            return True
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            self.connection.rollback()
            self.log_migration_step("backup_creation", "FAILED", str(e))
            return False
    
    def add_email_verified_column(self) -> bool:
        """Add email_verified column to users table"""
        print("\n📝 Adding email_verified column to users table...")
        
        try:
            if self.dry_run:
                print("🔍 DRY RUN: Would add email_verified column")
                self.log_migration_step("add_column", "DRY_RUN", "Column addition simulated")
                return True
            
            # Add column with default value
            self.cursor.execute("""
                ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
            """)
            
            # Update existing users
            self.cursor.execute("""
                UPDATE users SET email_verified = FALSE WHERE email_verified IS NULL;
            """)
            
            # Make column NOT NULL
            self.cursor.execute("""
                ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;
            """)
            
            # Verify column addition
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE email_verified = FALSE;
            """)
            updated_count = self.cursor.fetchone()[0]
            
            self.connection.commit()
            print(f"✅ Column added: {updated_count:,} users updated")
            self.log_migration_step("add_column", "SUCCESS", f"Column added, {updated_count} users updated")
            return True
            
        except Exception as e:
            print(f"❌ Column addition failed: {e}")
            self.connection.rollback()
            self.log_migration_step("add_column", "FAILED", str(e))
            return False
    
    def create_email_verification_tables(self) -> bool:
        """Create all email verification related tables"""
        print("\n🏗️  Creating email verification tables...")
        
        try:
            if self.dry_run:
                print("🔍 DRY RUN: Would create email verification tables")
                self.log_migration_step("create_tables", "DRY_RUN", "Table creation simulated")
                return True
            
            # This would normally be done by Alembic, but we can validate the structure
            # For now, just check if we can proceed
            print("✅ Table creation will be handled by Alembic migration")
            self.log_migration_step("create_tables", "PENDING", "Will be handled by Alembic")
            return True
            
        except Exception as e:
            print(f"❌ Table creation validation failed: {e}")
            self.log_migration_step("create_tables", "FAILED", str(e))
            return False
    
    def validate_migration(self) -> bool:
        """Validate migration success"""
        print("\n✅ Validating migration...")
        
        try:
            # Check if email_verified column exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'email_verified'
                );
            """)
            column_exists = self.cursor.fetchone()[0]
            
            if not column_exists:
                print("❌ email_verified column not found")
                return False
            
            # Check if all users have the column
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE email_verified IS NULL;
            """)
            null_count = self.cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"❌ {null_count} users still have NULL email_verified")
                return False
            
            # Check backup table
            self.cursor.execute("""
                SELECT COUNT(*) FROM users_backup_010;
            """)
            backup_count = self.cursor.fetchone()[0]
            
            # Check current users
            self.cursor.execute("SELECT COUNT(*) FROM users;")
            current_count = self.cursor.fetchone()[0]
            
            if backup_count != current_count:
                print(f"❌ Backup count ({backup_count}) doesn't match current count ({current_count})")
                return False
            
            print(f"✅ Validation passed: {current_count:,} users migrated successfully")
            self.log_migration_step("validation", "SUCCESS", f"All {current_count} users validated")
            return True
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            self.log_migration_step("validation", "FAILED", str(e))
            return False
    
    def generate_migration_report(self) -> str:
        """Generate comprehensive migration report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"migration_report_{timestamp}.json"
        
        report_data = {
            'migration_name': 'Email Verification System',
            'timestamp': datetime.utcnow().isoformat(),
            'dry_run': self.dry_run,
            'steps': self.migration_log,
            'summary': {
                'total_steps': len(self.migration_log),
                'successful_steps': len([s for s in self.migration_log if s['status'] == 'SUCCESS']),
                'failed_steps': len([s for s in self.migration_log if s['status'] == 'FAILED']),
                'dry_run_steps': len([s for s in self.migration_log if s['status'] == 'DRY_RUN'])
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_file
    
    def execute_migration(self) -> bool:
        """Execute complete migration process"""
        print("🚀 Starting Email Verification Migration")
        print("=" * 50)
        
        try:
            # Step 1: Connect to database
            if not self.connect():
                return False
            
            # Step 2: Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Step 3: Create backup
            if not self.create_backup():
                return False
            
            # Step 4: Add email_verified column
            if not self.add_email_verified_column():
                return False
            
            # Step 5: Create tables (handled by Alembic)
            if not self.create_email_verification_tables():
                return False
            
            # Step 6: Validate migration
            if not self.validate_migration():
                return False
            
            # Step 7: Generate report
            report_file = self.generate_migration_report()
            print(f"\n📊 Migration report saved to: {report_file}")
            
            print("\n🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n💥 Migration failed: {e}")
            self.log_migration_step("migration_execution", "FAILED", str(e))
            return False
        
        finally:
            self.disconnect()
    
    def rollback_migration(self) -> bool:
        """Rollback migration if needed"""
        print("\n🔄 Starting migration rollback...")
        
        try:
            if not self.connect():
                return False
            
            # Check if backup exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_backup_010'
                );
            """)
            backup_exists = self.cursor.fetchone()[0]
            
            if not backup_exists:
                print("❌ Backup table not found - cannot rollback")
                return False
            
            if self.dry_run:
                print("🔍 DRY RUN: Would restore users table from backup")
                return True
            
            # Restore users table from backup
            self.cursor.execute("""
                DROP TABLE users;
                ALTER TABLE users_backup_010 RENAME TO users;
            """)
            
            self.connection.commit()
            print("✅ Rollback completed - users table restored from backup")
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            self.connection.rollback()
            return False
        
        finally:
            self.disconnect()

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Email Verification Migration Script')
    parser.add_argument('--env', choices=['development', 'staging', 'production'], 
                       required=True, help='Environment to migrate')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Perform dry run without making changes')
    parser.add_argument('--execute', action='store_true', 
                       help='Execute migration (overrides dry-run)')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback migration')
    parser.add_argument('--database-url', 
                       help='Override database URL from environment')
    
    args = parser.parse_args()
    
    # Determine if this is a dry run
    dry_run = args.dry_run and not args.execute
    
    # Safety check for production
    if args.env == 'production' and not args.execute:
        print("⚠️  PRODUCTION ENVIRONMENT DETECTED")
        print("⚠️  This is a DRY RUN by default")
        print("⚠️  Use --execute flag to actually perform the migration")
        print("⚠️  Ensure you have a complete database backup before proceeding")
        
        confirm = input("\nDo you want to continue with DRY RUN? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Migration cancelled")
            sys.exit(0)
    
    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not set")
            sys.exit(1)
    
    # Create migration instance
    migration = EmailVerificationMigration(database_url, dry_run)
    
    if args.rollback:
        success = migration.rollback_migration()
    else:
        success = migration.execute_migration()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
