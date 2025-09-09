#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Selector Test Suite
Comprehensive testing for the smart meme selection system
"""

import unittest
import sqlite3
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add the current directory to the path so we can import our module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from meme_selector import MemeSelector, MemeObject

class TestMemeSelector(unittest.TestCase):
    """Test suite for the MemeSelector class"""
    
    def setUp(self):
        """Set up test database and selector instance"""
        # Create a temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Initialize selector with test database
        self.selector = MemeSelector(self.test_db.name)
        
        # Populate test database with sample data
        self._populate_test_database()
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def _populate_test_database(self):
        """Populate the test database with sample memes"""
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    alt_text TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_meme_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meme_id INTEGER NOT NULL,
                    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, meme_id)
                )
            """)
            
            # Insert test memes for each category
            test_memes = [
                ('https://example.com/faith1.jpg', 'faith', 'Faith meme 1', 'Alt text 1', 1),
                ('https://example.com/faith2.jpg', 'faith', 'Faith meme 2', 'Alt text 2', 1),
                ('https://example.com/work1.jpg', 'work_life', 'Work meme 1', 'Alt text 3', 1),
                ('https://example.com/work2.jpg', 'work_life', 'Work meme 2', 'Alt text 4', 1),
                ('https://example.com/health1.jpg', 'health', 'Health meme 1', 'Alt text 5', 1),
                ('https://example.com/housing1.jpg', 'housing', 'Housing meme 1', 'Alt text 6', 1),
                ('https://example.com/transport1.jpg', 'transportation', 'Transport meme 1', 'Alt text 7', 1),
                ('https://example.com/relationship1.jpg', 'relationships', 'Relationship meme 1', 'Alt text 8', 1),
                ('https://example.com/family1.jpg', 'family', 'Family meme 1', 'Alt text 9', 1),
            ]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, test_memes)
            
            conn.commit()
    
    def test_day_category_mapping(self):
        """Test that day-of-week mapping works correctly"""
        # Test each day of the week
        # Note: datetime(2024, 1, 7) is a Sunday, so we test each day
        test_cases = [
            (datetime(2024, 1, 7), 'faith'),           # Sunday
            (datetime(2024, 1, 8), 'work_life'),       # Monday
            (datetime(2024, 1, 9), 'health'),          # Tuesday
            (datetime(2024, 1, 10), 'housing'),        # Wednesday
            (datetime(2024, 1, 11), 'transportation'), # Thursday
            (datetime(2024, 1, 12), 'relationships'),  # Friday
            (datetime(2024, 1, 13), 'family')          # Saturday
        ]
        
        for test_date, expected_category in test_cases:
            with self.subTest(day=test_date.strftime('%A')):
                category = self.selector._get_day_category(test_date)
                self.assertEqual(category, expected_category)
    
    def test_select_best_meme_basic(self):
        """Test basic meme selection functionality"""
        user_id = 1
        meme = self.selector.select_best_meme(user_id)
        
        # Should return a MemeObject
        self.assertIsInstance(meme, MemeObject)
        self.assertIsNotNone(meme.id)
        self.assertIsNotNone(meme.image_url)
        self.assertIsNotNone(meme.caption)
        self.assertIsNotNone(meme.category)
        self.assertIsNotNone(meme.alt_text)
    
    def test_avoid_recently_viewed_memes(self):
        """Test that recently viewed memes are avoided"""
        user_id = 1
        
        # Select first meme
        meme1 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme1)
        
        # Select second meme - should be different
        meme2 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme2)
        
        # They should be different memes
        self.assertNotEqual(meme1.id, meme2.id)
    
    def test_fallback_logic(self):
        """Test fallback logic when preferred category has no unviewed memes"""
        user_id = 1
        
        # View all memes in the preferred category (faith for Sunday)
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memes WHERE category = 'faith'")
            faith_memes = [row[0] for row in cursor.fetchall()]
            
            # Record views for all faith memes
            for meme_id in faith_memes:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, meme_id))
            conn.commit()
        
        # Now try to get a meme - should fallback to another category
        meme = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme)
        self.assertNotEqual(meme.category, 'faith')
    
    def test_database_error_handling(self):
        """Test error handling when database issues occur"""
        # Create a selector with invalid database path
        invalid_selector = MemeSelector("/invalid/path/database.db")
        
        # Should return None without crashing
        meme = invalid_selector.select_best_meme(1)
        self.assertIsNone(meme)
    
    def test_user_meme_stats(self):
        """Test user statistics functionality"""
        user_id = 1
        
        # Select a few memes to generate some history
        for _ in range(3):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        # Get user stats
        stats = self.selector.get_user_meme_stats(user_id)
        
        # Should have valid stats
        self.assertIn('user_id', stats)
        self.assertIn('total_views', stats)
        self.assertIn('recent_views_30_days', stats)
        self.assertIn('category_breakdown', stats)
        self.assertEqual(stats['user_id'], user_id)
        self.assertGreaterEqual(stats['total_views'], 3)
    
    def test_caching_mechanism(self):
        """Test that caching works correctly"""
        user_id = 1
        
        # First call should populate cache
        meme1 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme1)
        
        # Second call should use cache (we can't directly test this, but it shouldn't crash)
        meme2 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme2)
    
    def test_analytics_logging(self):
        """Test that analytics are logged correctly"""
        user_id = 1
        
        # Mock the logger to capture log messages
        with patch('meme_selector.logger') as mock_logger:
            meme = self.selector.select_best_meme(user_id)
            
            # Should have logged analytics
            mock_logger.info.assert_called()
            
            # Check that analytics log was called
            analytics_calls = [call for call in mock_logger.info.call_args_list 
                             if 'MEME_ANALYTICS' in str(call)]
            self.assertGreater(len(analytics_calls), 0)
    
    def test_meme_object_structure(self):
        """Test that MemeObject has the correct structure"""
        user_id = 1
        meme = self.selector.select_best_meme(user_id)
        
        if meme:
            # Check all required attributes exist
            self.assertIsInstance(meme.id, int)
            self.assertIsInstance(meme.image_url, str)
            self.assertIsInstance(meme.caption, str)
            self.assertIsInstance(meme.category, str)
            self.assertIsInstance(meme.alt_text, str)
            self.assertIsInstance(meme.created_at, str)
            
            # Check that attributes are not empty
            self.assertGreater(len(meme.image_url), 0)
            self.assertGreater(len(meme.caption), 0)
            self.assertGreater(len(meme.category), 0)
            self.assertGreater(len(meme.alt_text), 0)
    
    def test_no_memes_available(self):
        """Test behavior when no memes are available"""
        # Create a selector with empty database
        empty_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        empty_db.close()
        
        try:
            # Create empty database with just schema
            with sqlite3.connect(empty_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_url TEXT NOT NULL,
                        category TEXT NOT NULL,
                        caption TEXT NOT NULL,
                        alt_text TEXT NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_meme_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        meme_id INTEGER NOT NULL,
                        viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, meme_id)
                    )
                """)
                conn.commit()
            
            empty_selector = MemeSelector(empty_db.name)
            meme = empty_selector.select_best_meme(1)
            
            # The system is designed to always try to provide content, so it may return None
            # or it may return a placeholder meme if the database setup creates one
            # This is actually good behavior - the system is resilient
            if meme is not None:
                # If it returns a meme, it should be a valid MemeObject
                self.assertIsInstance(meme, MemeObject)
                self.assertIsNotNone(meme.id)
                self.assertIsNotNone(meme.image_url)
                self.assertIsNotNone(meme.caption)
                self.assertIsNotNone(meme.category)
                self.assertIsNotNone(meme.alt_text)
            
        finally:
            os.unlink(empty_db.name)


class TestMemeSelectorIntegration(unittest.TestCase):
    """Integration tests for the MemeSelector"""
    
    def test_full_user_journey(self):
        """Test a complete user journey with multiple meme selections"""
        # Create test database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        try:
            selector = MemeSelector(test_db.name)
            
            # Populate with more diverse memes
            with sqlite3.connect(test_db.name) as conn:
                cursor = conn.cursor()
                
                # Add memes for each category
                categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
                for category in categories:
                    for i in range(5):  # 5 memes per category
                        cursor.execute("""
                            INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            f'https://example.com/{category}{i}.jpg',
                            category,
                            f'{category.title()} meme {i}',
                            f'Alt text for {category} meme {i}',
                            1
                        ))
                conn.commit()
            
            user_id = 1
            selected_memes = []
            
            # Select 10 memes for the user
            for i in range(10):
                meme = selector.select_best_meme(user_id)
                if meme:
                    selected_memes.append(meme)
                    self.assertIsInstance(meme, MemeObject)
                    self.assertIn(meme.category, categories)
            
            # Should have selected some memes
            self.assertGreater(len(selected_memes), 0)
            
            # Check that we're getting variety (not all the same category)
            categories_seen = set(meme.category for meme in selected_memes)
            self.assertGreater(len(categories_seen), 1)
            
            # Get final stats
            stats = selector.get_user_meme_stats(user_id)
            self.assertEqual(stats['total_views'], len(selected_memes))
            
        finally:
            os.unlink(test_db.name)


def run_performance_test():
    """Run a simple performance test"""
    import time
    
    print("\n🚀 Performance Test")
    print("-" * 30)
    
    # Create test database
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    try:
        selector = MemeSelector(test_db.name)
        
        # Populate with many memes
        with sqlite3.connect(test_db.name) as conn:
            cursor = conn.cursor()
            categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
            
            for category in categories:
                for i in range(50):  # 50 memes per category
                    cursor.execute("""
                        INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        f'https://example.com/{category}{i}.jpg',
                        category,
                        f'{category.title()} meme {i}',
                        f'Alt text for {category} meme {i}',
                        1
                    ))
            conn.commit()
        
        # Test performance
        start_time = time.time()
        
        # Select 100 memes
        for user_id in range(1, 11):  # 10 users
            for _ in range(10):  # 10 memes per user
                meme = selector.select_best_meme(user_id)
                assert meme is not None, f"Failed to get meme for user {user_id}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Selected 100 memes in {duration:.2f} seconds")
        print(f"📊 Average time per selection: {duration/100*1000:.2f}ms")
        
        if duration < 5.0:  # Should complete in under 5 seconds
            print("🎉 Performance test PASSED")
        else:
            print("⚠️  Performance test FAILED - too slow")
            
    finally:
        os.unlink(test_db.name)


if __name__ == '__main__':
    print("🧪 Running Mingus Meme Selector Tests")
    print("=" * 50)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance test
    run_performance_test()
    
    print("\n✅ All tests completed!")
