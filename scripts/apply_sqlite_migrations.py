#!/usr/bin/env python3
"""
SQLite Migration Script for Mingus Application
Applies database migrations to SQLite database
"""

import sqlite3
import os
import sys
from pathlib import Path

def get_db_path():
    """Get the SQLite database path"""
    # Check if we're in the project root
    db_path = Path("instance/mingus.db")
    if db_path.exists():
        return str(db_path)
    
    # Check if we're in a subdirectory
    for parent in Path.cwd().parents:
        db_path = parent / "instance" / "mingus.db"
        if db_path.exists():
            return str(db_path)
    
    raise FileNotFoundError("Could not find mingus.db database file")

def apply_migration(conn, migration_file):
    """Apply a single migration file"""
    print(f"Applying migration: {migration_file}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Split SQL into individual statements
    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
    
    for statement in statements:
        if statement:
            try:
                conn.execute(statement)
                print(f"  ✓ Executed: {statement[:50]}...")
            except sqlite3.Error as e:
                print(f"  ✗ Error executing: {statement[:50]}...")
                print(f"    Error: {e}")
                # Continue with other statements
                continue
    
    conn.commit()
    print(f"  ✓ Migration completed: {migration_file}")

def main():
    """Main migration function"""
    try:
        db_path = get_db_path()
        print(f"Using database: {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create migrations table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get list of migration files
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            print("No migrations directory found")
            return
        
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.name.startswith(("001_", "002_"))
        ])
        
        print(f"Found {len(migration_files)} migration files")
        
        # Get already applied migrations
        applied = set()
        cursor = conn.execute("SELECT filename FROM migrations")
        for row in cursor.fetchall():
            applied.add(row['filename'])
        
        # Apply new migrations
        for migration_file in migration_files:
            if migration_file.name not in applied:
                apply_migration(conn, migration_file)
                
                # Record migration as applied
                conn.execute(
                    "INSERT INTO migrations (filename) VALUES (?)",
                    (migration_file.name,)
                )
                conn.commit()
                print(f"  ✓ Recorded migration: {migration_file.name}")
            else:
                print(f"  ⏭ Skipping already applied migration: {migration_file.name}")
        
        print("\nMigration process completed!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 