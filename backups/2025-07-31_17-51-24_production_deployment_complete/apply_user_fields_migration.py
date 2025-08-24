#!/usr/bin/env python3
"""
Script to apply the comprehensive user fields migration
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection from environment variables"""
    try:
        # Try to get connection details from environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'mingus_app')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # If no password in env, try to get from file
        if not db_password:
            password_file = os.getenv('DB_PASSWORD_FILE', '')
            if password_file and os.path.exists(password_file):
                with open(password_file, 'r') as f:
                    db_password = f.read().strip()
        
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def check_migration_status(connection, migration_name):
    """Check if migration has already been applied"""
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM migration_log 
            WHERE migration_name = %s
        """, (migration_name,))
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0
    except Exception as e:
        logger.warning(f"Could not check migration status: {e}")
        return False

def apply_migration(connection, migration_file):
    """Apply the migration file"""
    try:
        # Read migration file
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        cursor = connection.cursor()
        
        # Split SQL into individual statements
        statements = migration_sql.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.error(f"Error executing statement: {statement[:50]}... - {e}")
                    raise
        
        cursor.close()
        logger.info("Migration applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply migration: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting comprehensive user fields migration...")
    
    # Get database connection
    connection = get_database_connection()
    if not connection:
        logger.error("Could not establish database connection")
        sys.exit(1)
    
    migration_name = "012_add_comprehensive_user_fields"
    migration_file = "migrations/012_add_comprehensive_user_fields.sql"
    
    try:
        # Check if migration already applied
        if check_migration_status(connection, migration_name):
            logger.info(f"Migration {migration_name} has already been applied")
            return
        
        # Check if migration file exists
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            sys.exit(1)
        
        # Apply migration
        logger.info(f"Applying migration: {migration_name}")
        success = apply_migration(connection, migration_file)
        
        if success:
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main() 