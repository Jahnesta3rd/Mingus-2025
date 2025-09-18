#!/usr/bin/env python3
"""
Database migration script to add assessment tables
Adds assessment system tables to the existing database
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """Get the main database path"""
    # Try to find the main database
    possible_paths = [
        'app.db',
        'mingus_memes.db',
        'database/app.db',
        'data/app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If no existing database found, create app.db
    return 'app.db'

def migrate_assessment_tables():
    """Add assessment tables to existing database"""
    
    db_path = get_db_path()
    print(f"📊 Using database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create assessments table
        print("🔧 Creating assessments table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                first_name TEXT,
                phone TEXT,
                assessment_type TEXT NOT NULL,
                answers TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create assessment analytics table
        print("🔧 Creating assessment_analytics table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                action TEXT NOT NULL,
                question_id TEXT,
                answer_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                user_agent TEXT,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')
        
        # Create lead magnet results table
        print("🔧 Creating lead_magnet_results table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_magnet_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                email TEXT NOT NULL,
                assessment_type TEXT NOT NULL,
                score INTEGER,
                risk_level TEXT,
                recommendations TEXT,
                results_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')
        
        # Add indexes for performance
        print("🔧 Adding performance indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessments_email ON assessments(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(assessment_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_assessment_id ON assessment_analytics(assessment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_action ON assessment_analytics(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lead_magnet_assessment_id ON lead_magnet_results(assessment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lead_magnet_type ON lead_magnet_results(assessment_type)')
        
        # Add data retention policy (optional)
        print("🔧 Adding data retention policy...")
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS cleanup_old_assessments
            AFTER INSERT ON assessments
            BEGIN
                DELETE FROM assessments 
                WHERE created_at < datetime('now', '-1 year');
            END
        ''')
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%assessment%'")
        tables = cursor.fetchall()
        
        print(f"✅ Successfully created {len(tables)} assessment tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Show table schemas
        print("\n📋 Table schemas:")
        for table in tables:
            print(f"\n{table[0]}:")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        
        print(f"\n🎉 Database migration completed successfully!")
        print(f"📊 Database: {db_path}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_migration():
    """Verify that migration was successful"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if all required tables exist
        required_tables = ['assessments', 'assessment_analytics', 'lead_magnet_results']
        
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} records")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        print(f"✅ Indexes: {len(indexes)} created")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting Assessment Tables Migration")
    print("=" * 50)
    
    try:
        migrate_assessment_tables()
        print("\n🔍 Verifying migration...")
        if verify_migration():
            print("\n✅ Migration verification successful!")
            sys.exit(0)
        else:
            print("\n❌ Migration verification failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
