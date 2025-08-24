#!/usr/bin/env python3
"""
Migration script to add UserAssessmentScores table for Be-Do-Have gatekeeping
"""
import sqlite3
import os
import sys
from datetime import datetime

def create_user_assessment_scores_table(db_path):
    """Create the user_assessment_scores table"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create user_assessment_scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_assessment_scores (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                be_score INTEGER DEFAULT 0,
                do_score INTEGER DEFAULT 0,
                have_score INTEGER DEFAULT 0,
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assessment_version TEXT DEFAULT '1.0',
                total_questions INTEGER DEFAULT 0,
                completion_time_minutes INTEGER DEFAULT 0,
                be_level TEXT DEFAULT 'Beginner' CHECK (be_level IN ('Beginner', 'Intermediate', 'Advanced')),
                do_level TEXT DEFAULT 'Beginner' CHECK (do_level IN ('Beginner', 'Intermediate', 'Advanced')),
                have_level TEXT DEFAULT 'Beginner' CHECK (have_level IN ('Beginner', 'Intermediate', 'Advanced')),
                confidence_score REAL DEFAULT 0.0,
                is_valid BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_user_id ON user_assessment_scores(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_assessment_date ON user_assessment_scores(assessment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_created_at ON user_assessment_scores(created_at)')
        
        # Create trigger for updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_user_assessment_scores_updated_at
            AFTER UPDATE ON user_assessment_scores
            FOR EACH ROW
            BEGIN
                UPDATE user_assessment_scores SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        
        conn.commit()
        print("✅ Created user_assessment_scores table successfully")
        
    except Exception as e:
        print(f"❌ Error creating user_assessment_scores table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_sample_assessment_data(db_path):
    """Create sample assessment data for testing"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get a sample user ID
        cursor.execute("SELECT id FROM users LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("⚠️  No users found in database. Skipping sample assessment data.")
            return
        
        user_id = result[0]
        
        # Create sample assessment with the test scores from the user's request
        import uuid
        assessment_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_assessment_scores (
                id, user_id, be_score, do_score, have_score,
                be_level, do_level, have_level, confidence_score,
                assessment_version, total_questions, completion_time_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id, user_id, 75, 45, 30,
            'Intermediate', 'Beginner', 'Beginner', 0.85,
            '1.0', 30, 15
        ))
        
        conn.commit()
        print(f"✅ Created sample assessment data for user {user_id}")
        print(f"   BE Score: 75 (Intermediate)")
        print(f"   DO Score: 45 (Beginner)")
        print(f"   HAVE Score: 30 (Beginner)")
        
    except Exception as e:
        print(f"❌ Error creating sample assessment data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting UserAssessmentScores migration...")
    
    # Database path
    db_path = "instance/mingus.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        sys.exit(1)
    
    try:
        # Create the table
        create_user_assessment_scores_table(db_path)
        
        # Create sample data
        create_sample_assessment_data(db_path)
        
        print("✅ UserAssessmentScores migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
