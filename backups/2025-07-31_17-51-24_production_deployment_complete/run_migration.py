#!/usr/bin/env python3
"""
MINGUS Data Migration Runner
============================

Simple script to run the data migration with different options.

Usage:
    python run_migration.py                    # Run full migration
    python run_migration.py --dry-run         # Test migration without actual data transfer
    python run_migration.py --validate-only   # Validate data only
    python run_migration.py --help            # Show help

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import argparse
from pathlib import Path
from data_migration import MigrationConfig, DatabaseMigrator


def check_database_files():
    """Check if all required SQLite database files exist."""
    required_files = [
        'mingus.db',
        'business_intelligence.db',
        'cache.db',
        'performance_metrics.db',
        'alerts.db'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required database files: {', '.join(missing_files)}")
        print("Please ensure all SQLite database files are in the current directory.")
        return False
    
    print("✅ All required database files found")
    return True


def check_postgres_connection():
    """Check PostgreSQL connection."""
    try:
        from models import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("Please check your DATABASE_URL environment variable.")
        return False


def main():
    """Main migration runner function."""
    parser = argparse.ArgumentParser(
        description="MINGUS Data Migration Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_migration.py                    # Run full migration
  python run_migration.py --dry-run         # Test without actual migration
  python run_migration.py --validate-only   # Validate data only
  python run_migration.py --batch-size 500  # Use smaller batch size
  python run_migration.py --no-backup       # Skip backup creation
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run migration in test mode without actual data transfer'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate data only without migration'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Number of records to process per batch (default: 1000)'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation before migration'
    )
    
    parser.add_argument(
        '--no-rollback',
        action='store_true',
        help='Skip rollback command generation'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--postgres-url',
        help='PostgreSQL connection URL (overrides DATABASE_URL environment variable)'
    )
    
    args = parser.parse_args()
    
    print("🚀 MINGUS Data Migration Runner")
    print("=" * 50)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    if not check_database_files():
        sys.exit(1)
    
    if not check_postgres_connection():
        sys.exit(1)
    
    # Configuration
    print("\n⚙️  Configuring migration...")
    
    config = MigrationConfig(
        sqlite_databases={
            'mingus': 'mingus.db',
            'business_intelligence': 'business_intelligence.db',
            'cache': 'cache.db',
            'performance_metrics': 'performance_metrics.db',
            'alerts': 'alerts.db'
        },
        postgres_url=args.postgres_url or os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production'),
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        dry_run=args.dry_run,
        validate_only=args.validate_only,
        log_level=args.log_level,
        log_file='migration.log',
        create_backup=not args.no_backup,
        backup_dir='migration_backups',
        enable_rollback=not args.no_rollback,
        rollback_file='rollback_commands.sql'
    )
    
    # Display configuration
    print(f"📊 Migration Configuration:")
    print(f"   Batch Size: {config.batch_size}")
    print(f"   Max Workers: {config.max_workers}")
    print(f"   Dry Run: {config.dry_run}")
    print(f"   Validate Only: {config.validate_only}")
    print(f"   Create Backup: {config.create_backup}")
    print(f"   Enable Rollback: {config.enable_rollback}")
    print(f"   Log Level: {config.log_level}")
    
    if config.dry_run:
        print("\n🧪 DRY RUN MODE - No actual data will be migrated")
    elif config.validate_only:
        print("\n🔍 VALIDATION ONLY MODE - Data will be validated but not migrated")
    else:
        print("\n⚠️  PRODUCTION MODE - Data will be migrated to PostgreSQL")
    
    # Confirmation
    if not config.dry_run and not config.validate_only:
        response = input("\n❓ Do you want to proceed with the migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            sys.exit(0)
    
    # Run migration
    print("\n🚀 Starting migration...")
    print("=" * 50)
    
    try:
        migrator = DatabaseMigrator(config)
        success = migrator.run_migration()
        
        if success:
            print("\n✅ Migration completed successfully!")
            
            # Display summary
            stats = migrator.stats
            print(f"\n📊 Migration Summary:")
            print(f"   Total Records: {stats.total_records}")
            print(f"   Processed: {stats.processed_records}")
            print(f"   Successful: {stats.successful_records}")
            print(f"   Failed: {stats.failed_records}")
            print(f"   Success Rate: {stats.success_rate:.1f}%")
            print(f"   Duration: {stats.duration:.1f} seconds")
            
            if migrator.errors:
                print(f"\n⚠️  Errors encountered: {len(migrator.errors)}")
                print("Check the migration log for details.")
            
            print(f"\n📄 Migration report saved to: migration_report_{migrator.migration_id}.json")
            
            if config.enable_rollback:
                print(f"🔄 Rollback commands saved to: {config.rollback_file}")
            
            if config.create_backup:
                print(f"💾 Backups saved to: {config.backup_dir}/{migrator.migration_id}/")
            
            sys.exit(0)
        else:
            print("\n❌ Migration completed with errors!")
            print("Check the migration log for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 