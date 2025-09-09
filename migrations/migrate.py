#!/usr/bin/env python3
"""
Database Migration Script for Mingus Meme Splash Page
Handles safe database migrations with rollback capabilities
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migrations/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path='mingus_memes.db'):
        self.db_path = db_path
        self.migrations_dir = Path('migrations')
        self.backup_dir = Path('database_backups')
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """Create a backup of the current database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'mingus_memes_backup_{timestamp}.db'
        
        try:
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def get_migration_files(self):
        """Get all migration files in order"""
        migration_files = []
        for file in sorted(self.migrations_dir.glob('*.sql')):
            if file.name.startswith(('001_', '002_', '003_')):
                migration_files.append(file)
        return migration_files
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create migrations table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('SELECT migration_name FROM migrations ORDER BY applied_at')
        applied = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return applied
    
    def apply_migration(self, migration_file):
        """Apply a single migration"""
        migration_name = migration_file.stem
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read migration SQL
            with open(migration_file, 'r') as f:
                sql_content = f.read()
            
            # Execute migration
            cursor.executescript(sql_content)
            
            # Record migration as applied
            cursor.execute(
                'INSERT INTO migrations (migration_name) VALUES (?)',
                (migration_name,)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Applied migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_name}: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def rollback_migration(self, migration_name):
        """Rollback a specific migration"""
        # This is a simplified rollback - in production you'd want more sophisticated rollback logic
        logger.warning(f"Rollback requested for {migration_name}")
        logger.warning("Manual rollback required - please restore from backup")
        return False
    
    def migrate(self, create_backup=True):
        """Run all pending migrations"""
        if create_backup:
            backup_path = self.create_backup()
            logger.info(f"Backup created at: {backup_path}")
        
        applied_migrations = self.get_applied_migrations()
        migration_files = self.get_migration_files()
        
        pending_migrations = []
        for migration_file in migration_files:
            if migration_file.stem not in applied_migrations:
                pending_migrations.append(migration_file)
        
        if not pending_migrations:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        for migration_file in pending_migrations:
            if not self.apply_migration(migration_file):
                logger.error(f"Migration failed: {migration_file.stem}")
                return False
        
        logger.info("All migrations completed successfully")
        return True
    
    def check_database_health(self):
        """Check database integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check database integrity
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                logger.info("Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity check failed: {result[0]}")
                return False
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus Meme Database Migrator')
    parser.add_argument('--db-path', default='mingus_memes.db', help='Database file path')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--check-health', action='store_true', help='Only check database health')
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator(args.db_path)
    
    if args.check_health:
        if migrator.check_database_health():
            print("✅ Database is healthy")
            return 0
        else:
            print("❌ Database health check failed")
            return 1
    
    # Run migrations
    if migrator.migrate(create_backup=not args.no_backup):
        print("✅ Migrations completed successfully")
        return 0
    else:
        print("❌ Migrations failed")
        return 1

if __name__ == '__main__':
    exit(main())
