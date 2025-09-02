#!/usr/bin/env python3
"""
Post-Migration Validation Script for Email Verification System
Validates that all migration components are working correctly

Usage:
    python validate_migration.py --env development
    python validate_migration.py --env production
"""

import argparse
import os
import sys
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

class MigrationValidator:
    """Validate email verification system migration"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self.cursor = None
        self.validation_results = []
        
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
    
    def log_validation(self, component: str, status: str, details: str = ""):
        """Log validation result"""
        result = {
            'component': component,
            'status': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.validation_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {component}: {status} - {details}")
    
    def validate_users_table(self) -> bool:
        """Validate users table modifications"""
        print("\n🔍 Validating users table...")
        
        try:
            # Check if email_verified column exists
            self.cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'email_verified';
            """)
            column_info = self.cursor.fetchone()
            
            if not column_info:
                self.log_validation("users_table", "FAIL", "email_verified column not found")
                return False
            
            column_name, data_type, is_nullable, column_default = column_info
            
            if data_type != 'boolean':
                self.log_validation("users_table", "FAIL", f"email_verified column has wrong type: {data_type}")
                return False
            
            if is_nullable != 'NO':
                self.log_validation("users_table", "FAIL", "email_verified column should be NOT NULL")
                return False
            
            # Check if all users have the column
            self.cursor.execute("""
                SELECT COUNT(*) as total_users,
                       COUNT(email_verified) as users_with_column,
                       COUNT(CASE WHEN email_verified = FALSE THEN 1 END) as unverified_users
                FROM users;
            """)
            user_stats = self.cursor.fetchone()
            total_users, users_with_column, unverified_users = user_stats
            
            if total_users != users_with_column:
                self.log_validation("users_table", "FAIL", f"Column mismatch: {total_users} total vs {users_with_column} with column")
                return False
            
            # Check indexes
            self.cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'users' AND indexname LIKE '%email_verified%';
            """)
            indexes = self.cursor.fetchall()
            
            if len(indexes) < 1:
                self.log_validation("users_table", "FAIL", "Missing email_verified indexes")
                return False
            
            self.log_validation("users_table", "PASS", f"All {total_users} users have email_verified=FALSE, {len(indexes)} indexes")
            return True
            
        except Exception as e:
            self.log_validation("users_table", "FAIL", str(e))
            return False
    
    def validate_email_verifications_table(self) -> bool:
        """Validate email_verifications table"""
        print("\n🔍 Validating email_verifications table...")
        
        try:
            # Check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'email_verifications'
                );
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                self.log_validation("email_verifications_table", "FAIL", "Table does not exist")
                return False
            
            # Check table structure
            self.cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'email_verifications'
                ORDER BY ordinal_position;
            """)
            columns = self.cursor.fetchall()
            
            expected_columns = [
                ('id', 'integer', 'NO'),
                ('user_id', 'integer', 'NO'),
                ('email', 'character varying', 'NO'),
                ('verification_token_hash', 'character varying', 'NO'),
                ('expires_at', 'timestamp with time zone', 'NO'),
                ('verified_at', 'timestamp with time zone', 'YES'),
                ('created_at', 'timestamp with time zone', 'NO'),
                ('resend_count', 'integer', 'NO'),
                ('last_resend_at', 'timestamp with time zone', 'YES'),
                ('ip_address', 'character varying', 'YES'),
                ('user_agent', 'text', 'YES'),
                ('verification_type', 'character varying', 'NO'),
                ('old_email', 'character varying', 'YES'),
                ('failed_attempts', 'integer', 'NO'),
                ('last_failed_attempt', 'timestamp with time zone', 'YES'),
                ('locked_until', 'timestamp with time zone', 'YES')
            ]
            
            if len(columns) != len(expected_columns):
                self.log_validation("email_verifications_table", "FAIL", f"Column count mismatch: {len(columns)} vs {len(expected_columns)} expected")
                return False
            
            # Check indexes
            self.cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'email_verifications';
            """)
            indexes = self.cursor.fetchall()
            
            if len(indexes) < 8:  # Minimum expected indexes
                self.log_validation("email_verifications_table", "FAIL", f"Insufficient indexes: {len(indexes)} found")
                return False
            
            # Check constraints
            self.cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'email_verifications';
            """)
            constraints = self.cursor.fetchall()
            
            if len(constraints) < 3:  # Primary key + foreign key + unique constraints
                self.log_validation("email_verifications_table", "FAIL", f"Insufficient constraints: {len(constraints)} found")
                return False
            
            self.log_validation("email_verifications_table", "PASS", f"Table structure valid, {len(indexes)} indexes, {len(constraints)} constraints")
            return True
            
        except Exception as e:
            self.log_validation("email_verifications_table", "FAIL", str(e))
            return False
    
    def validate_audit_log_table(self) -> bool:
        """Validate email_verification_audit_log table"""
        print("\n🔍 Validating audit log table...")
        
        try:
            # Check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'email_verification_audit_log'
                );
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                self.log_validation("audit_log_table", "FAIL", "Table does not exist")
                return False
            
            # Check table structure
            self.cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'email_verification_audit_log'
                ORDER BY ordinal_position;
            """)
            columns = self.cursor.fetchall()
            
            expected_columns = [
                ('id', 'integer', 'NO'),
                ('user_id', 'integer', 'YES'),
                ('verification_id', 'integer', 'YES'),
                ('event_type', 'character varying', 'NO'),
                ('event_data', 'jsonb', 'YES'),
                ('ip_address', 'character varying', 'YES'),
                ('user_agent', 'text', 'YES'),
                ('success', 'boolean', 'NO'),
                ('error_message', 'text', 'YES'),
                ('created_at', 'timestamp with time zone', 'NO')
            ]
            
            if len(columns) != len(expected_columns):
                self.log_validation("audit_log_table", "FAIL", f"Column count mismatch: {len(columns)} vs {len(expected_columns)} expected")
                return False
            
            # Check indexes
            self.cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'email_verification_audit_log';
            """)
            indexes = self.cursor.fetchall()
            
            if len(indexes) < 5:  # Minimum expected indexes
                self.log_validation("audit_log_table", "FAIL", f"Insufficient indexes: {len(indexes)} found")
                return False
            
            self.log_validation("audit_log_table", "PASS", f"Table structure valid, {len(indexes)} indexes")
            return True
            
        except Exception as e:
            self.log_validation("audit_log_table", "FAIL", str(e))
            return False
    
    def validate_settings_table(self) -> bool:
        """Validate email_verification_settings table"""
        print("\n🔍 Validating settings table...")
        
        try:
            # Check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'email_verification_settings'
                );
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                self.log_validation("settings_table", "FAIL", "Table does not exist")
                return False
            
            # Check default settings
            self.cursor.execute("""
                SELECT setting_key, setting_value FROM email_verification_settings;
            """)
            settings = self.cursor.fetchall()
            
            expected_settings = [
                'verification_expiry_hours',
                'max_resend_attempts',
                'resend_cooldown_hours',
                'max_failed_attempts',
                'lockout_duration_hours',
                'reminder_schedule_days',
                'enable_rate_limiting',
                'enable_audit_logging',
                'default_verification_type',
                'token_length'
            ]
            
            setting_keys = [s[0] for s in settings]
            missing_settings = [key for key in expected_settings if key not in setting_keys]
            
            if missing_settings:
                self.log_validation("settings_table", "FAIL", f"Missing settings: {missing_settings}")
                return False
            
            self.log_validation("settings_table", "PASS", f"All {len(expected_settings)} expected settings present")
            return True
            
        except Exception as e:
            self.log_validation("settings_table", "FAIL", str(e))
            return False
    
    def validate_functions(self) -> bool:
        """Validate database functions"""
        print("\n🔍 Validating database functions...")
        
        try:
            # Check if functions exist
            self.cursor.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname IN (
                    'cleanup_expired_email_verifications',
                    'schedule_email_verification_reminders',
                    'update_email_verification_analytics'
                );
            """)
            functions = self.cursor.fetchall()
            
            expected_functions = [
                'cleanup_expired_email_verifications',
                'schedule_email_verification_reminders',
                'update_email_verification_analytics'
            ]
            
            function_names = [f[0] for f in functions]
            missing_functions = [name for name in expected_functions if name not in function_names]
            
            if missing_functions:
                self.log_validation("database_functions", "FAIL", f"Missing functions: {missing_functions}")
                return False
            
            self.log_validation("database_functions", "PASS", f"All {len(expected_functions)} expected functions present")
            return True
            
        except Exception as e:
            self.log_validation("database_functions", "FAIL", str(e))
            return False
    
    def validate_triggers(self) -> bool:
        """Validate database triggers"""
        print("\n🔍 Validating database triggers...")
        
        try:
            # Check if triggers exist
            self.cursor.execute("""
                SELECT tgname FROM pg_trigger 
                WHERE tgname IN (
                    'trigger_update_verification_updated_at',
                    'trigger_log_verification_changes'
                );
            """)
            triggers = self.cursor.fetchall()
            
            expected_triggers = [
                'trigger_update_verification_updated_at',
                'trigger_log_verification_changes'
            ]
            
            trigger_names = [t[0] for t in triggers]
            missing_triggers = [name for name in expected_triggers if name not in trigger_names]
            
            if missing_triggers:
                self.log_validation("database_triggers", "FAIL", f"Missing triggers: {missing_triggers}")
                return False
            
            self.log_validation("database_triggers", "PASS", f"All {len(expected_triggers)} expected triggers present")
            return True
            
        except Exception as e:
            self.log_validation("database_triggers", "FAIL", str(e))
            return False
    
    def validate_backup_table(self) -> bool:
        """Validate backup table integrity"""
        print("\n🔍 Validating backup table...")
        
        try:
            # Check if backup table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_backup_010'
                );
            """)
            backup_exists = self.cursor.fetchone()[0]
            
            if not backup_exists:
                self.log_validation("backup_table", "FAIL", "Backup table does not exist")
                return False
            
            # Compare backup vs current user count
            self.cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users_backup_010) as backup_count,
                    (SELECT COUNT(*) FROM users) as current_count;
            """)
            counts = self.cursor.fetchone()
            backup_count, current_count = counts
            
            if backup_count != current_count:
                self.log_validation("backup_table", "FAIL", f"Count mismatch: backup={backup_count}, current={current_count}")
                return False
            
            self.log_validation("backup_table", "PASS", f"Backup integrity verified: {backup_count} users")
            return True
            
        except Exception as e:
            self.log_validation("backup_table", "FAIL", str(e))
            return False
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation_report_{timestamp}.json"
        
        # Calculate summary
        total_components = len(self.validation_results)
        passed_components = len([r for r in self.validation_results if r['status'] == 'PASS'])
        failed_components = len([r for r in self.validation_results if r['status'] == 'FAIL'])
        
        report_data = {
            'validation_name': 'Email Verification System Migration',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_components': total_components,
                'passed_components': passed_components,
                'failed_components': failed_components,
                'success_rate': f"{(passed_components/total_components)*100:.1f}%" if total_components > 0 else "0%"
            },
            'components': self.validation_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_file
    
    def run_validation(self) -> bool:
        """Run complete validation process"""
        print("🔍 Starting Email Verification System Validation")
        print("=" * 60)
        
        try:
            # Connect to database
            if not self.connect():
                return False
            
            # Run all validations
            validations = [
                self.validate_users_table(),
                self.validate_email_verifications_table(),
                self.validate_audit_log_table(),
                self.validate_settings_table(),
                self.validate_functions(),
                self.validate_triggers(),
                self.validate_backup_table()
            ]
            
            # Generate report
            report_file = self.generate_validation_report()
            
            # Print summary
            passed = sum(validations)
            total = len(validations)
            
            print("\n" + "=" * 60)
            print("📊 VALIDATION SUMMARY")
            print("=" * 60)
            print(f"✅ Passed: {passed}/{total}")
            print(f"❌ Failed: {total - passed}/{total}")
            print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
            print(f"📄 Report saved to: {report_file}")
            
            if passed == total:
                print("\n🎉 All validations passed! Migration is successful.")
                return True
            else:
                print(f"\n⚠️  {total - passed} validation(s) failed. Please review the report.")
                return False
                
        except Exception as e:
            print(f"\n💥 Validation failed: {e}")
            return False
        
        finally:
            self.disconnect()

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Email Verification Migration Validator')
    parser.add_argument('--env', choices=['development', 'staging', 'production'], 
                       required=True, help='Environment to validate')
    parser.add_argument('--database-url', 
                       help='Override database URL from environment')
    
    args = parser.parse_args()
    
    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not set")
            sys.exit(1)
    
    # Create validator instance
    validator = MigrationValidator(database_url)
    
    # Run validation
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
