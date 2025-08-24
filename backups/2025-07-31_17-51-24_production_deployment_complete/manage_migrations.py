#!/usr/bin/env python3
"""
Migration Management Script for MINGUS Application
Provides easy commands for managing Alembic migrations
"""

import argparse
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from backend.app import create_app


class MigrationManager:
    """Manages database migrations for the MINGUS application"""
    
    def __init__(self, environment='development'):
        self.environment = environment
        self.alembic_cfg = Config("alembic.ini")
        self.setup_environment()
    
    def setup_environment(self):
        """Setup environment variables and configuration"""
        # Set Flask environment
        os.environ['FLASK_ENV'] = self.environment
        
        # Create Flask app to get database URL
        app = create_app(self.environment)
        with app.app_context():
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            if database_url:
                self.alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    def init_migrations(self):
        """Initialize Alembic migrations"""
        print("🔧 Initializing Alembic migrations...")
        try:
            command.init(self.alembic_cfg, 'migrations')
            print("✅ Migrations initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing migrations: {e}")
            return False
        return True
    
    def create_migration(self, message):
        """Create a new migration"""
        print(f"📝 Creating migration: {message}")
        try:
            command.revision(self.alembic_cfg, message=message, autogenerate=True)
            print("✅ Migration created successfully!")
        except Exception as e:
            print(f"❌ Error creating migration: {e}")
            return False
        return True
    
    def upgrade_database(self, revision='head'):
        """Upgrade database to specified revision"""
        print(f"⬆️  Upgrading database to revision: {revision}")
        try:
            command.upgrade(self.alembic_cfg, revision)
            print("✅ Database upgraded successfully!")
        except Exception as e:
            print(f"❌ Error upgrading database: {e}")
            return False
        return True
    
    def downgrade_database(self, revision):
        """Downgrade database to specified revision"""
        print(f"⬇️  Downgrading database to revision: {revision}")
        try:
            command.downgrade(self.alembic_cfg, revision)
            print("✅ Database downgraded successfully!")
        except Exception as e:
            print(f"❌ Error downgrading database: {e}")
            return False
        return True
    
    def show_current(self):
        """Show current database revision"""
        print("📊 Current database revision:")
        try:
            command.current(self.alembic_cfg)
        except Exception as e:
            print(f"❌ Error showing current revision: {e}")
            return False
        return True
    
    def show_history(self):
        """Show migration history"""
        print("📜 Migration history:")
        try:
            command.history(self.alembic_cfg)
        except Exception as e:
            print(f"❌ Error showing history: {e}")
            return False
        return True
    
    def stamp_database(self, revision):
        """Stamp database with revision without running migrations"""
        print(f"🏷️  Stamping database with revision: {revision}")
        try:
            command.stamp(self.alembic_cfg, revision)
            print("✅ Database stamped successfully!")
        except Exception as e:
            print(f"❌ Error stamping database: {e}")
            return False
        return True
    
    def show_migration(self, revision):
        """Show specific migration details"""
        print(f"📋 Migration details for revision: {revision}")
        try:
            command.show(self.alembic_cfg, revision)
        except Exception as e:
            print(f"❌ Error showing migration: {e}")
            return False
        return True
    
    def show_heads(self):
        """Show current heads"""
        print("🎯 Current migration heads:")
        try:
            command.heads(self.alembic_cfg)
        except Exception as e:
            print(f"❌ Error showing heads: {e}")
            return False
        return True
    
    def edit_migration(self, revision):
        """Edit a migration file"""
        print(f"✏️  Opening migration for editing: {revision}")
        try:
            command.edit(self.alembic_cfg, revision)
            print("✅ Migration opened for editing!")
        except Exception as e:
            print(f"❌ Error editing migration: {e}")
            return False
        return True
    
    def merge_migrations(self, revisions, message=None):
        """Merge multiple migration heads"""
        if not message:
            message = f"Merge {', '.join(revisions)}"
        
        print(f"🔀 Merging migrations: {', '.join(revisions)}")
        try:
            command.merge(self.alembic_cfg, revisions, message=message)
            print("✅ Migrations merged successfully!")
        except Exception as e:
            print(f"❌ Error merging migrations: {e}")
            return False
        return True
    
    def check_migrations(self):
        """Check for migration issues"""
        print("🔍 Checking migrations...")
        try:
            command.check(self.alembic_cfg)
            print("✅ Migrations check passed!")
        except Exception as e:
            print(f"❌ Migration check failed: {e}")
            return False
        return True
    
    def list_migrations(self):
        """List all migrations"""
        print("📋 All migrations:")
        try:
            # Get migrations directory
            migrations_dir = Path("migrations/versions")
            if migrations_dir.exists():
                for migration_file in sorted(migrations_dir.glob("*.py")):
                    print(f"  - {migration_file.stem}")
            else:
                print("  No migrations found")
        except Exception as e:
            print(f"❌ Error listing migrations: {e}")
            return False
        return True
    
    def backup_database(self):
        """Backup database before migration"""
        print("💾 Creating database backup...")
        try:
            # Get database URL from config
            database_url = self.alembic_cfg.get_main_option("sqlalchemy.url")
            
            if database_url.startswith('postgresql://'):
                # PostgreSQL backup
                backup_file = f"backups/database/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                
                # Extract connection details
                import re
                match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
                if match:
                    user, password, host, port, database = match.groups()
                    
                    # Create backup command
                    backup_cmd = [
                        'pg_dump',
                        f'--host={host}',
                        f'--port={port}',
                        f'--username={user}',
                        f'--dbname={database}',
                        '--verbose',
                        '--clean',
                        '--no-owner',
                        '--no-privileges',
                        f'--file={backup_file}'
                    ]
                    
                    # Set password environment variable
                    env = os.environ.copy()
                    env['PGPASSWORD'] = password
                    
                    subprocess.run(backup_cmd, env=env, check=True)
                    print(f"✅ Database backed up to: {backup_file}")
                else:
                    print("❌ Could not parse database URL")
                    return False
            else:
                print("⚠️  Database backup not implemented for this database type")
                return True
                
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return False
        return True
    
    def restore_database(self, backup_file):
        """Restore database from backup"""
        print(f"🔄 Restoring database from: {backup_file}")
        try:
            # Get database URL from config
            database_url = self.alembic_cfg.get_main_option("sqlalchemy.url")
            
            if database_url.startswith('postgresql://'):
                # PostgreSQL restore
                import re
                match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
                if match:
                    user, password, host, port, database = match.groups()
                    
                    # Create restore command
                    restore_cmd = [
                        'psql',
                        f'--host={host}',
                        f'--port={port}',
                        f'--username={user}',
                        f'--dbname={database}',
                        '--verbose',
                        f'--file={backup_file}'
                    ]
                    
                    # Set password environment variable
                    env = os.environ.copy()
                    env['PGPASSWORD'] = password
                    
                    subprocess.run(restore_cmd, env=env, check=True)
                    print("✅ Database restored successfully!")
                else:
                    print("❌ Could not parse database URL")
                    return False
            else:
                print("⚠️  Database restore not implemented for this database type")
                return True
                
        except Exception as e:
            print(f"❌ Error restoring database: {e}")
            return False
        return True


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description="Manage Alembic migrations for MINGUS.")
    parser.add_argument('--env', default='development', 
                       choices=['development', 'production', 'testing'],
                       help='Environment (development, production, testing)')
    parser.add_argument('--action', required=True,
                       choices=['init', 'create', 'upgrade', 'downgrade', 'current', 
                               'history', 'stamp', 'show', 'heads', 'edit', 'merge', 
                               'check', 'list', 'backup-db', 'restore-db'],
                       help='Migration action to perform')
    parser.add_argument('--message', help='Migration message (for create action)')
    parser.add_argument('--revision', default='head', help='Revision identifier')
    parser.add_argument('--revisions', nargs='+', help='Revision identifiers for merge')
    parser.add_argument('--backup-file', help='Backup file path (for restore action)')
    
    args = parser.parse_args()
    
    # Create migration manager
    manager = MigrationManager(args.env)
    
    # Perform requested action
    if args.action == 'init':
        success = manager.init_migrations()
    elif args.action == 'create':
        if not args.message:
            print("❌ Message is required for create action")
            sys.exit(1)
        success = manager.create_migration(args.message)
    elif args.action == 'upgrade':
        success = manager.upgrade_database(args.revision)
    elif args.action == 'downgrade':
        success = manager.downgrade_database(args.revision)
    elif args.action == 'current':
        success = manager.show_current()
    elif args.action == 'history':
        success = manager.show_history()
    elif args.action == 'stamp':
        success = manager.stamp_database(args.revision)
    elif args.action == 'show':
        success = manager.show_migration(args.revision)
    elif args.action == 'heads':
        success = manager.show_heads()
    elif args.action == 'edit':
        success = manager.edit_migration(args.revision)
    elif args.action == 'merge':
        if not args.revisions:
            print("❌ Revisions are required for merge action")
            sys.exit(1)
        success = manager.merge_migrations(args.revisions, args.message)
    elif args.action == 'check':
        success = manager.check_migrations()
    elif args.action == 'list':
        success = manager.list_migrations()
    elif args.action == 'backup-db':
        success = manager.backup_database()
    elif args.action == 'restore-db':
        if not args.backup_file:
            print("❌ Backup file is required for restore action")
            sys.exit(1)
        success = manager.restore_database(args.backup_file)
    else:
        print(f"❌ Unknown action: {args.action}")
        sys.exit(1)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main() 