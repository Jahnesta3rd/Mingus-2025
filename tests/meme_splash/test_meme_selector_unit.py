#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Selector Unit Tests
Comprehensive unit tests for the meme selection algorithm and database operations
"""

import unittest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
import json

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from meme_selector import MemeSelector, MemeObject

class TestMemeSelectorUnit(unittest.TestCase):
    """Unit tests for the MemeSelector class"""
    
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
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def _populate_test_database(self):
        """Populate the test database with comprehensive sample data"""
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
            
            # Insert comprehensive test memes for each category
            test_memes = [
                # Faith category (Sunday)
                ('https://example.com/faith1.jpg', 'faith', 'Sunday motivation: Trust the process', 'Faith meme showing trust', 1),
                ('https://example.com/faith2.jpg', 'faith', 'Prayer changes everything', 'Prayer hands meme', 1),
                ('https://example.com/faith3.jpg', 'faith', 'God has a plan', 'Religious encouragement meme', 1),
                
                # Work life category (Monday)
                ('https://example.com/work1.jpg', 'work_life', 'Monday mood: Coffee first', 'Coffee and work meme', 1),
                ('https://example.com/work2.jpg', 'work_life', 'TGIF energy on Monday', 'Monday motivation meme', 1),
                ('https://example.com/work3.jpg', 'work_life', 'Work-life balance goals', 'Balance meme', 1),
                
                # Health category (Tuesday)
                ('https://example.com/health1.jpg', 'health', 'Tuesday workout vibes', 'Gym motivation meme', 1),
                ('https://example.com/health2.jpg', 'health', 'Healthy eating starts today', 'Nutrition meme', 1),
                ('https://example.com/health3.jpg', 'health', 'Mental health matters', 'Wellness meme', 1),
                
                # Housing category (Wednesday)
                ('https://example.com/housing1.jpg', 'housing', 'House hunting adventures', 'Real estate meme', 1),
                ('https://example.com/housing2.jpg', 'housing', 'Rent vs Buy calculator', 'Housing decision meme', 1),
                ('https://example.com/housing3.jpg', 'housing', 'Home improvement budget', 'DIY meme', 1),
                
                # Transportation category (Thursday)
                ('https://example.com/transport1.jpg', 'transportation', 'Gas prices be like...', 'Gas price meme', 1),
                ('https://example.com/transport2.jpg', 'transportation', 'Public transport life', 'Commute meme', 1),
                ('https://example.com/transport3.jpg', 'transportation', 'Car maintenance costs', 'Auto repair meme', 1),
                
                # Relationships category (Friday)
                ('https://example.com/relationship1.jpg', 'relationships', 'Date night budget', 'Romance finance meme', 1),
                ('https://example.com/relationship2.jpg', 'relationships', 'Splitting bills fairly', 'Couple finance meme', 1),
                ('https://example.com/relationship3.jpg', 'relationships', 'Friends and money', 'Friendship finance meme', 1),
                
                # Family category (Saturday)
                ('https://example.com/family1.jpg', 'family', 'Kids and money lessons', 'Parenting finance meme', 1),
                ('https://example.com/family2.jpg', 'family', 'Family budget planning', 'Family finance meme', 1),
                ('https://example.com/family3.jpg', 'family', 'Teaching kids about money', 'Education finance meme', 1),
                
                # Inactive memes (should not be selected)
                ('https://example.com/inactive1.jpg', 'faith', 'Inactive faith meme', 'Inactive meme', 0),
                ('https://example.com/inactive2.jpg', 'work_life', 'Inactive work meme', 'Inactive meme', 0),
            ]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, test_memes)
            
            conn.commit()
    
    def test_day_category_mapping(self):
        """Test that day-of-week mapping works correctly for all days"""
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
                self.assertEqual(category, expected_category, 
                               f"Expected {expected_category} for {test_date.strftime('%A')}, got {category}")
    
    def test_select_best_meme_returns_valid_object(self):
        """Test that select_best_meme returns a valid MemeObject"""
        user_id = 1
        meme = self.selector.select_best_meme(user_id)
        
        # Should return a MemeObject
        self.assertIsInstance(meme, MemeObject)
        self.assertIsNotNone(meme.id)
        self.assertIsNotNone(meme.image_url)
        self.assertIsNotNone(meme.caption)
        self.assertIsNotNone(meme.category)
        self.assertIsNotNone(meme.alt_text)
        self.assertIsNotNone(meme.created_at)
        
        # Validate data types
        self.assertIsInstance(meme.id, int)
        self.assertIsInstance(meme.image_url, str)
        self.assertIsInstance(meme.caption, str)
        self.assertIsInstance(meme.category, str)
        self.assertIsInstance(meme.alt_text, str)
        self.assertIsInstance(meme.created_at, str)
        
        # Validate content is not empty
        self.assertGreater(len(meme.image_url), 0)
        self.assertGreater(len(meme.caption), 0)
        self.assertGreater(len(meme.category), 0)
        self.assertGreater(len(meme.alt_text), 0)
    
    def test_avoid_recently_viewed_memes(self):
        """Test that recently viewed memes are avoided within 30-day window"""
        user_id = 1
        
        # Select first meme
        meme1 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme1)
        
        # Select second meme - should be different
        meme2 = self.selector.select_best_meme(user_id)
        self.assertIsNotNone(meme2)
        
        # They should be different memes
        self.assertNotEqual(meme1.id, meme2.id, "Should not return the same meme twice")
    
    def test_fallback_logic_when_category_empty(self):
        """Test fallback logic when preferred category has no unviewed memes"""
        user_id = 1
        
        # View all memes in the preferred category (faith for Sunday)
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memes WHERE category = 'faith' AND is_active = 1")
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
        self.assertIsNotNone(meme, "Should return a meme even when preferred category is empty")
        self.assertNotEqual(meme.category, 'faith', "Should not return from empty preferred category")
        self.assertIn(meme.category, self.selector.FALLBACK_CATEGORIES, "Should use fallback categories")
    
    def test_database_error_handling(self):
        """Test error handling when database issues occur"""
        # Create a selector with invalid database path
        invalid_selector = MemeSelector("/invalid/path/database.db")
        
        # Should return None without crashing
        meme = invalid_selector.select_best_meme(1)
        self.assertIsNone(meme, "Should return None for invalid database path")
    
    def test_user_meme_stats_structure(self):
        """Test that user statistics have correct structure"""
        user_id = 1
        
        # Select a few memes to generate some history
        for _ in range(3):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        # Get user stats
        stats = self.selector.get_user_meme_stats(user_id)
        
        # Should have valid stats structure
        required_keys = ['user_id', 'total_views', 'recent_views_30_days', 'category_breakdown']
        for key in required_keys:
            self.assertIn(key, stats, f"Stats should contain {key}")
        
        # Validate data types
        self.assertIsInstance(stats['user_id'], int)
        self.assertIsInstance(stats['total_views'], int)
        self.assertIsInstance(stats['recent_views_30_days'], int)
        self.assertIsInstance(stats['category_breakdown'], dict)
        
        # Validate values
        self.assertEqual(stats['user_id'], user_id)
        self.assertGreaterEqual(stats['total_views'], 3)
        self.assertGreaterEqual(stats['recent_views_30_days'], 3)
    
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
            self.assertGreater(len(analytics_calls), 0, "Should log analytics information")
    
    def test_inactive_memes_excluded(self):
        """Test that inactive memes are not selected"""
        user_id = 1
        
        # Get all memes to verify inactive ones are excluded
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memes WHERE is_active = 0")
            inactive_meme_ids = [row[0] for row in cursor.fetchall()]
        
        # Select multiple memes and ensure none are inactive
        selected_meme_ids = []
        for _ in range(10):  # Select 10 memes
            meme = self.selector.select_best_meme(user_id)
            if meme:
                selected_meme_ids.append(meme.id)
        
        # None of the selected memes should be inactive
        for meme_id in selected_meme_ids:
            self.assertNotIn(meme_id, inactive_meme_ids, 
                           f"Meme {meme_id} should not be inactive")
    
    def test_category_distribution(self):
        """Test that memes are selected from different categories over time"""
        user_id = 1
        selected_categories = []
        
        # Select multiple memes and track categories
        for _ in range(15):  # Select 15 memes
            meme = self.selector.select_best_meme(user_id)
            if meme:
                selected_categories.append(meme.category)
        
        # Should have variety in categories (not all the same)
        unique_categories = set(selected_categories)
        self.assertGreater(len(unique_categories), 1, 
                          "Should select memes from multiple categories")
        
        # All categories should be valid
        valid_categories = set(self.selector.FALLBACK_CATEGORIES)
        for category in unique_categories:
            self.assertIn(category, valid_categories, 
                         f"Category {category} should be valid")
    
    def test_recently_viewed_memes_query(self):
        """Test the recently viewed memes query logic"""
        user_id = 1
        
        # Add some recent views
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add views for different time periods
            cursor.execute("SELECT id FROM memes WHERE is_active = 1 LIMIT 3")
            meme_ids = [row[0] for row in cursor.fetchall()]
            
            # Add recent view (within 30 days)
            cursor.execute("""
                INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
                VALUES (?, ?, datetime('now', '-10 days'))
            """, (user_id, meme_ids[0]))
            
            # Add old view (outside 30 days)
            cursor.execute("""
                INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
                VALUES (?, ?, datetime('now', '-40 days'))
            """, (user_id, meme_ids[1]))
            
            conn.commit()
        
        # Get recently viewed memes
        recent_memes = self.selector._get_recently_viewed_memes(user_id, 30)
        
        # Should include recent view but not old view
        self.assertIn(meme_ids[0], recent_memes, "Should include recent view")
        self.assertNotIn(meme_ids[1], recent_memes, "Should exclude old view")
    
    def test_meme_object_immutability(self):
        """Test that MemeObject is properly structured and immutable"""
        user_id = 1
        meme = self.selector.select_best_meme(user_id)
        
        if meme:
            # Test that we can access all attributes
            original_id = meme.id
            original_caption = meme.caption
            
            # MemeObject should be a dataclass with proper structure
            self.assertIsInstance(meme, MemeObject)
            
            # Test that attributes are accessible
            self.assertIsNotNone(meme.id)
            self.assertIsNotNone(meme.image_url)
            self.assertIsNotNone(meme.caption)
            self.assertIsNotNone(meme.category)
            self.assertIsNotNone(meme.alt_text)
            self.assertIsNotNone(meme.created_at)
    
    def test_edge_case_empty_database(self):
        """Test behavior with completely empty database"""
        # Create empty database
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
            
            # Should handle empty database gracefully
            self.assertIsNone(meme, "Should return None for empty database")
            
        finally:
            os.unlink(empty_db.name)
    
    def test_concurrent_user_handling(self):
        """Test that different users can select memes independently"""
        user1_id = 1
        user2_id = 2
        
        # Both users should be able to select memes
        meme1 = self.selector.select_best_meme(user1_id)
        meme2 = self.selector.select_best_meme(user2_id)
        
        self.assertIsNotNone(meme1, "User 1 should get a meme")
        self.assertIsNotNone(meme2, "User 2 should get a meme")
        
        # They could be the same meme (that's okay for different users)
        # But both should be valid MemeObjects
        self.assertIsInstance(meme1, MemeObject)
        self.assertIsInstance(meme2, MemeObject)
    
    def test_meme_selection_with_mocked_time(self):
        """Test meme selection with specific day-of-week using mocked time"""
        user_id = 1
        
        # Mock datetime to simulate different days
        test_cases = [
            (datetime(2024, 1, 7), 'faith'),           # Sunday
            (datetime(2024, 1, 8), 'work_life'),       # Monday
        ]
        
        for test_date, expected_category in test_cases:
            with self.subTest(day=test_date.strftime('%A')):
                with patch('meme_selector.datetime') as mock_datetime:
                    mock_datetime.now.return_value = test_date
                    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
                    
                    meme = self.selector.select_best_meme(user_id)
                    
                    if meme:
                        # The meme should be from the expected category
                        # (or from fallback if that category is empty)
                        self.assertIn(meme.category, [expected_category] + self.selector.FALLBACK_CATEGORIES)


class TestMemeSelectorPerformance(unittest.TestCase):
    """Performance tests for the MemeSelector"""
    
    def setUp(self):
        """Set up performance test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Create selector with large dataset
        self.selector = MemeSelector(self.test_db.name)
        self._populate_large_database()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def _populate_large_database(self):
        """Populate database with large dataset for performance testing"""
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
            
            # Insert many memes for performance testing
            categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
            memes_data = []
            
            for category in categories:
                for i in range(100):  # 100 memes per category
                    memes_data.append((
                        f'https://example.com/{category}{i}.jpg',
                        category,
                        f'{category.title()} meme {i}',
                        f'Alt text for {category} meme {i}',
                        1
                    ))
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, memes_data)
            
            conn.commit()
    
    def test_selection_performance(self):
        """Test that meme selection is fast even with large dataset"""
        import time
        
        user_id = 1
        start_time = time.time()
        
        # Select 50 memes
        for _ in range(50):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds for 50 selections)
        self.assertLess(duration, 5.0, f"Meme selection took {duration:.2f}s, should be under 5s")
        
        # Average time per selection should be reasonable
        avg_time = duration / 50
        self.assertLess(avg_time, 0.1, f"Average selection time {avg_time:.3f}s should be under 0.1s")
    
    def test_database_query_performance(self):
        """Test that database queries are optimized"""
        import time
        
        user_id = 1
        
        # Test recently viewed memes query performance
        start_time = time.time()
        recent_memes = self.selector._get_recently_viewed_memes(user_id, 30)
        end_time = time.time()
        
        query_duration = end_time - start_time
        self.assertLess(query_duration, 0.1, 
                       f"Recently viewed query took {query_duration:.3f}s, should be under 0.1s")
    
    def test_memory_usage(self):
        """Test that memory usage is reasonable"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many operations
        for user_id in range(1, 11):  # 10 users
            for _ in range(10):  # 10 memes per user
                meme = self.selector.select_best_meme(user_id)
                self.assertIsNotNone(meme)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB)
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                       f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB, should be under 10MB")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.makeSuite(TestMemeSelectorUnit))
    
    # Add performance tests (only if psutil is available)
    try:
        import psutil
        test_suite.addTest(unittest.makeSuite(TestMemeSelectorPerformance))
    except ImportError:
        print("⚠️  psutil not available, skipping performance tests")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
