#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Database Test Script
Tests the meme database schema and demonstrates usage patterns
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class MemeDatabase:
    """Database manager for the meme splash page feature"""
    
    def __init__(self, db_path: str = "mingus_memes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with schema and sample data"""
        with sqlite3.connect(self.db_path) as conn:
            # Read and execute the schema file
            with open('meme_database_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute the schema (SQLite handles multiple statements)
            conn.executescript(schema_sql)
            conn.commit()
            print(f"✅ Database initialized: {self.db_path}")
    
    def get_random_meme_by_category(self, category: str) -> Optional[Dict]:
        """Get a random active meme from a specific category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM memes 
                WHERE category = ? AND is_active = 1 
                ORDER BY RANDOM() 
                LIMIT 1
            """, (category,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_unviewed_memes_for_user(self, user_id: int, category: Optional[str] = None) -> List[Dict]:
        """Get memes not yet viewed by a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT m.* FROM memes m 
                    LEFT JOIN user_meme_history umh ON m.id = umh.meme_id AND umh.user_id = ?
                    WHERE m.is_active = 1 AND m.category = ? AND umh.id IS NULL
                    ORDER BY m.created_at DESC
                """, (user_id, category))
            else:
                cursor.execute("""
                    SELECT m.* FROM memes m 
                    LEFT JOIN user_meme_history umh ON m.id = umh.meme_id AND umh.user_id = ?
                    WHERE m.is_active = 1 AND umh.id IS NULL
                    ORDER BY m.created_at DESC
                """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def record_meme_view(self, user_id: int, meme_id: int) -> bool:
        """Record that a user viewed a specific meme"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, meme_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False  # Already viewed
    
    def get_user_engagement_stats(self, user_id: int) -> Dict[str, int]:
        """Get engagement statistics for a user by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.category, COUNT(*) as view_count 
                FROM user_meme_history umh 
                JOIN memes m ON umh.meme_id = m.id 
                WHERE umh.user_id = ? 
                GROUP BY m.category
            """, (user_id,))
            
            return dict(cursor.fetchall())
    
    def get_all_categories(self) -> List[str]:
        """Get all available meme categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category FROM memes 
                WHERE is_active = 1 
                ORDER BY category
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def get_meme_stats(self) -> Dict:
        """Get overall statistics about memes in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total memes
            cursor.execute("SELECT COUNT(*) FROM memes WHERE is_active = 1")
            total_memes = cursor.fetchone()[0]
            
            # Memes by category
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM memes 
                WHERE is_active = 1 
                GROUP BY category 
                ORDER BY category
            """)
            by_category = dict(cursor.fetchall())
            
            # Total views
            cursor.execute("SELECT COUNT(*) FROM user_meme_history")
            total_views = cursor.fetchone()[0]
            
            return {
                'total_memes': total_memes,
                'by_category': by_category,
                'total_views': total_views
            }

def test_database():
    """Test the meme database functionality"""
    print("🧪 Testing Mingus Meme Database")
    print("=" * 50)
    
    # Initialize database
    db = MemeDatabase()
    
    # Test 1: Get all categories
    print("\n📂 Available Categories:")
    categories = db.get_all_categories()
    for category in categories:
        print(f"  - {category}")
    
    # Test 2: Get random memes from each category
    print("\n🎲 Random Memes by Category:")
    for category in categories:
        meme = db.get_random_meme_by_category(category)
        if meme:
            print(f"\n{category.upper()}:")
            print(f"  Caption: {meme['caption']}")
            print(f"  Alt Text: {meme['alt_text']}")
    
    # Test 3: Simulate user interactions
    print("\n👤 Simulating User Interactions:")
    test_user_id = 1
    
    # Get unviewed memes for user
    unviewed = db.get_unviewed_memes_for_user(test_user_id)
    print(f"  Unviewed memes for user {test_user_id}: {len(unviewed)}")
    
    # Record some views
    if unviewed:
        for i, meme in enumerate(unviewed[:3]):  # View first 3
            success = db.record_meme_view(test_user_id, meme['id'])
            print(f"  Viewed meme {meme['id']} ({meme['category']}): {'✅' if success else '❌'}")
    
    # Test 4: Get user engagement stats
    print("\n📊 User Engagement Statistics:")
    stats = db.get_user_engagement_stats(test_user_id)
    for category, count in stats.items():
        print(f"  {category}: {count} views")
    
    # Test 5: Overall database stats
    print("\n📈 Database Statistics:")
    db_stats = db.get_meme_stats()
    print(f"  Total active memes: {db_stats['total_memes']}")
    print(f"  Total views: {db_stats['total_views']}")
    print("  Memes by category:")
    for category, count in db_stats['by_category'].items():
        print(f"    {category}: {count}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    test_database()
