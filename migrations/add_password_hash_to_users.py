#!/usr/bin/env python3
"""
Migration: Add password_hash field to users table
This migration adds the password_hash column to support user authentication
Supports both SQLite and PostgreSQL
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

def migrate():
    """Add password_hash column to users table"""
    database_url = os.environ.get('DATABASE_URL', '')
    
    print(f"Connecting to database...")
    
    try:
        # Check if using PostgreSQL
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse database URL
            parsed = urlparse(database_url)
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/').split('?')[0],
                sslmode='require'
            )
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password_hash'
            """)
            
            if cursor.fetchone():
                print("✅ password_hash column already exists. Migration not needed.")
                conn.close()
                return True
            
            # Add password_hash column
            print("Adding password_hash column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN password_hash TEXT
            """)
            
            conn.commit()
            print("✅ Successfully added password_hash column to users table")
            conn.close()
            return True
            
        else:
            # SQLite database
            import sqlite3
            
            db_path = database_url.replace('sqlite:///', '') if database_url.startswith('sqlite:///') else (database_url or 'mingus_app.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'password_hash' in columns:
                print("✅ password_hash column already exists. Migration not needed.")
                conn.close()
                return True
            
            # Add password_hash column
            print("Adding password_hash column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN password_hash TEXT
            """)
            
            conn.commit()
            print("✅ Successfully added password_hash column to users table")
            conn.close()
            return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate column" in error_msg or "already exists" in error_msg:
            print("✅ password_hash column already exists. Migration not needed.")
            return True
        print(f"❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add password_hash to users table")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
