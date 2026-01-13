#!/usr/bin/env python3
"""
Migration: Add password_hash field to users table
This migration adds the password_hash column to support user authentication
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

def get_db_path():
    """Get database path from environment or use default"""
    db_path = os.environ.get('DATABASE_URL', 'mingus_app.db')
    # Remove sqlite:/// prefix if present
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    return db_path

def migrate():
    """Add password_hash column to users table"""
    db_path = get_db_path()
    
    print(f"Connecting to database: {db_path}")
    
    try:
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
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✅ password_hash column already exists. Migration not needed.")
            return True
        print(f"❌ Error during migration: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
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
