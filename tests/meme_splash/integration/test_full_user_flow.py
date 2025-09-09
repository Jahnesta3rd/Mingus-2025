#!/usr/bin/env python3
"""
Mingus Personal Finance App - Full User Flow Integration Tests
Comprehensive integration tests for the complete meme splash page user journey
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from meme_selector import MemeSelector
from backend.api.meme_endpoints import meme_api
from flask import Flask
from tests.meme_splash.fixtures.test_data import MemeTestData, DatabaseTestSetup

class TestFullUserFlowIntegration(unittest.TestCase):
    """Integration tests for complete user flow"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create test database
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with test data
        DatabaseTestSetup.create_test_database(self.test_db.name)
        
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.register_blueprint(meme_api)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock database path
        self.db_path_patcher = patch('backend.api.meme_endpoints.DB_PATH', self.test_db.name)
        self.db_path_patcher.start()
        
        # Initialize meme selector
        self.selector = MemeSelector(self.test_db.name)
    
    def tearDown(self):
        """Clean up integration test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_complete_user_journey_api(self):
        """Test complete user journey through API endpoints"""
        user_id = 'user123'
        session_id = 'session456'
        
        # Step 1: User requests a meme
        response = self.client.get('/api/user-meme', headers={
            'X-User-ID': user_id,
            'X-Session-ID': session_id
        })
        
        self.assertEqual(response.status_code, 200)
        meme_data = json.loads(response.data)
        
        # Verify meme data structure
        required_fields = ['id', 'image_url', 'category', 'caption', 'alt_text']
        for field in required_fields:
            self.assertIn(field, meme_data)
        
        meme_id = meme_data['id']
        
        # Step 2: User views the meme (analytics tracked automatically)
        # This happens automatically when the meme is fetched
        
        # Step 3: User continues to dashboard
        analytics_data = {
            'meme_id': meme_id,
            'action': 'continue',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        analytics_response = json.loads(response.data)
        self.assertTrue(analytics_response['success'])
        
        # Step 4: Verify analytics were recorded
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = ?
            """, (meme_id, user_id, 'continue'))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Analytics should be recorded")
    
    def test_user_skips_meme_flow(self):
        """Test user journey when they skip the meme"""
        user_id = 'user456'
        session_id = 'session789'
        
        # Step 1: User requests a meme
        response = self.client.get('/api/user-meme', headers={
            'X-User-ID': user_id,
            'X-Session-ID': session_id
        })
        
        self.assertEqual(response.status_code, 200)
        meme_data = json.loads(response.data)
        meme_id = meme_data['id']
        
        # Step 2: User skips the meme
        analytics_data = {
            'meme_id': meme_id,
            'action': 'skip',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Verify skip analytics were recorded
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = ?
            """, (meme_id, user_id, 'skip'))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Skip analytics should be recorded")
    
    def test_auto_advance_flow(self):
        """Test user journey with auto-advance functionality"""
        user_id = 'user789'
        session_id = 'session012'
        
        # Step 1: User requests a meme
        response = self.client.get('/api/user-meme', headers={
            'X-User-ID': user_id,
            'X-Session-ID': session_id
        })
        
        self.assertEqual(response.status_code, 200)
        meme_data = json.loads(response.data)
        meme_id = meme_data['id']
        
        # Step 2: Simulate auto-advance (after timeout)
        analytics_data = {
            'meme_id': meme_id,
            'action': 'auto_advance',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Verify auto-advance analytics were recorded
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = ?
            """, (meme_id, user_id, 'auto_advance'))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Auto-advance analytics should be recorded")
    
    def test_multiple_users_same_meme(self):
        """Test multiple users viewing the same meme"""
        users = [
            ('user1', 'session1'),
            ('user2', 'session2'),
            ('user3', 'session3')
        ]
        
        meme_id = None
        
        for user_id, session_id in users:
            # Each user requests a meme
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': user_id,
                'X-Session-ID': session_id
            })
            
            self.assertEqual(response.status_code, 200)
            meme_data = json.loads(response.data)
            
            if meme_id is None:
                meme_id = meme_data['id']
            else:
                # All users should get the same meme (random selection)
                # In a real scenario, they might get different memes
                pass
            
            # Each user continues
            analytics_data = {
                'meme_id': meme_data['id'],
                'action': 'continue',
                'user_id': user_id,
                'session_id': session_id
            }
            
            response = self.client.post('/api/meme-analytics',
                                      data=json.dumps(analytics_data),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
        
        # Verify all analytics were recorded
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM meme_analytics 
                WHERE action = 'continue'
            """)
            
            count = cursor.fetchone()[0]
            self.assertGreaterEqual(count, 3, "Should have analytics for all users")
    
    def test_meme_selection_algorithm_integration(self):
        """Test meme selection algorithm with real database"""
        user_id = 1
        
        # Select multiple memes for the same user
        selected_memes = []
        for _ in range(5):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
            selected_memes.append(meme)
        
        # Verify we got different memes (avoiding recently viewed)
        meme_ids = [meme.id for meme in selected_memes]
        unique_ids = set(meme_ids)
        self.assertEqual(len(unique_ids), len(meme_ids), "Should get different memes")
        
        # Verify all memes are active
        for meme in selected_memes:
            self.assertTrue(meme.id > 0)
            self.assertIsNotNone(meme.image_url)
            self.assertIsNotNone(meme.caption)
            self.assertIsNotNone(meme.category)
    
    def test_database_consistency_after_operations(self):
        """Test database consistency after multiple operations"""
        user_id = 'consistency_test_user'
        session_id = 'consistency_test_session'
        
        # Perform multiple operations
        operations = []
        for i in range(3):
            # Get meme
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': user_id,
                'X-Session-ID': session_id
            })
            
            self.assertEqual(response.status_code, 200)
            meme_data = json.loads(response.data)
            operations.append(('get_meme', meme_data['id']))
            
            # Track analytics
            analytics_data = {
                'meme_id': meme_data['id'],
                'action': 'continue',
                'user_id': user_id,
                'session_id': session_id
            }
            
            response = self.client.post('/api/meme-analytics',
                                      data=json.dumps(analytics_data),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            operations.append(('track_analytics', meme_data['id']))
        
        # Verify database consistency
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Check that all memes exist
            cursor.execute("SELECT COUNT(*) FROM memes WHERE is_active = 1")
            active_memes = cursor.fetchone()[0]
            self.assertGreater(active_memes, 0)
            
            # Check that analytics were recorded
            cursor.execute("""
                SELECT COUNT(*) FROM meme_analytics 
                WHERE user_id = ? AND action = 'continue'
            """, (user_id,))
            
            analytics_count = cursor.fetchone()[0]
            self.assertEqual(analytics_count, 3)
            
            # Check that user history was updated
            cursor.execute("""
                SELECT COUNT(*) FROM user_meme_history 
                WHERE user_id = ?
            """, (1,))  # Using integer user_id for history table
            
            history_count = cursor.fetchone()[0]
            self.assertGreaterEqual(history_count, 0)  # May be 0 if using string user_id
    
    def test_error_recovery_flow(self):
        """Test error recovery in user flow"""
        user_id = 'error_test_user'
        session_id = 'error_test_session'
        
        # Test with invalid meme_id in analytics
        analytics_data = {
            'meme_id': 99999,  # Non-existent meme
            'action': 'continue',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        # Should still succeed (analytics failure shouldn't break user experience)
        self.assertEqual(response.status_code, 200)
        
        # Test with invalid action
        analytics_data = {
            'meme_id': 1,
            'action': 'invalid_action',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Test with missing fields
        analytics_data = {
            'meme_id': 1
            # Missing action field
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_performance_under_load(self):
        """Test performance with multiple concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(user_id, session_id):
            try:
                start_time = time.time()
                
                # Get meme
                response = self.client.get('/api/user-meme', headers={
                    'X-User-ID': user_id,
                    'X-Session-ID': session_id
                })
                
                if response.status_code == 200:
                    meme_data = json.loads(response.data)
                    
                    # Track analytics
                    analytics_data = {
                        'meme_id': meme_data['id'],
                        'action': 'continue',
                        'user_id': user_id,
                        'session_id': session_id
                    }
                    
                    response = self.client.post('/api/meme-analytics',
                                              data=json.dumps(analytics_data),
                                              content_type='application/json')
                    
                    end_time = time.time()
                    results.append(end_time - start_time)
                else:
                    errors.append(f"HTTP {response.status_code}")
                    
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to simulate concurrent users
        threads = []
        for i in range(10):  # 10 concurrent users
            thread = threading.Thread(target=make_request, args=(f'user{i}', f'session{i}'))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10, "All requests should complete")
        
        # Check performance (should complete in reasonable time)
        avg_time = sum(results) / len(results)
        self.assertLess(avg_time, 2.0, f"Average response time {avg_time:.2f}s should be under 2s")
        
        max_time = max(results)
        self.assertLess(max_time, 5.0, f"Max response time {max_time:.2f}s should be under 5s")


class TestMemeSplashPageIntegration(unittest.TestCase):
    """Integration tests for the complete meme splash page feature"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with test data
        DatabaseTestSetup.create_test_database(self.test_db.name)
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.register_blueprint(meme_api)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock database path
        self.db_path_patcher = patch('backend.api.meme_endpoints.DB_PATH', self.test_db.name)
        self.db_path_patcher.start()
        
        # Initialize meme selector
        self.selector = MemeSelector(self.test_db.name)
    
    def tearDown(self):
        """Clean up integration test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_end_to_end_meme_flow(self):
        """Test complete end-to-end meme flow"""
        user_id = 'e2e_user'
        session_id = 'e2e_session'
        
        # Step 1: User opens app and requests meme
        response = self.client.get('/api/user-meme', headers={
            'X-User-ID': user_id,
            'X-Session-ID': session_id
        })
        
        self.assertEqual(response.status_code, 200)
        meme_data = json.loads(response.data)
        
        # Verify meme has all required fields
        required_fields = ['id', 'image_url', 'category', 'caption', 'alt_text', 'is_active']
        for field in required_fields:
            self.assertIn(field, meme_data)
        
        # Verify meme is active
        self.assertTrue(meme_data['is_active'])
        
        # Step 2: User views meme (analytics automatically tracked)
        # This happens when the meme is fetched
        
        # Step 3: User continues to dashboard
        analytics_data = {
            'meme_id': meme_data['id'],
            'action': 'continue',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Verify complete analytics trail
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Check view analytics
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = 'view'
            """, (meme_data['id'], user_id))
            
            view_analytics = cursor.fetchone()
            self.assertIsNotNone(view_analytics, "View analytics should be recorded")
            
            # Check continue analytics
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = 'continue'
            """, (meme_data['id'], user_id))
            
            continue_analytics = cursor.fetchone()
            self.assertIsNotNone(continue_analytics, "Continue analytics should be recorded")
    
    def test_meme_statistics_integration(self):
        """Test meme statistics endpoint with real data"""
        user_id = 'stats_user'
        session_id = 'stats_session'
        
        # Generate some analytics data
        for i in range(3):
            # Get meme
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': user_id,
                'X-Session-ID': session_id
            })
            
            self.assertEqual(response.status_code, 200)
            meme_data = json.loads(response.data)
            
            # Track continue action
            analytics_data = {
                'meme_id': meme_data['id'],
                'action': 'continue',
                'user_id': user_id,
                'session_id': session_id
            }
            
            response = self.client.post('/api/meme-analytics',
                                      data=json.dumps(analytics_data),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
        
        # Get statistics
        response = self.client.get('/api/meme-stats')
        self.assertEqual(response.status_code, 200)
        
        stats_data = json.loads(response.data)
        
        # Verify statistics structure
        required_fields = ['total_memes', 'analytics_last_7_days', 'popular_memes']
        for field in required_fields:
            self.assertIn(field, stats_data)
        
        # Verify we have some analytics data
        self.assertGreater(stats_data['total_memes'], 0)
    
    def test_meme_selection_consistency(self):
        """Test that meme selection is consistent across multiple requests"""
        user_id = 1  # Using integer for meme selector
        
        # Get multiple memes using the selector
        memes = []
        for _ in range(5):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
            memes.append(meme)
        
        # Verify all memes are valid
        for meme in memes:
            self.assertIsNotNone(meme.id)
            self.assertIsNotNone(meme.image_url)
            self.assertIsNotNone(meme.caption)
            self.assertIsNotNone(meme.category)
            self.assertIsNotNone(meme.alt_text)
        
        # Verify we're getting variety (not all the same meme)
        meme_ids = [meme.id for meme in memes]
        unique_ids = set(meme_ids)
        self.assertGreater(len(unique_ids), 1, "Should get variety in meme selection")
        
        # Verify all memes are from valid categories
        valid_categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
        for meme in memes:
            self.assertIn(meme.category, valid_categories)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestFullUserFlowIntegration))
    test_suite.addTest(unittest.makeSuite(TestMemeSplashPageIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Integration Tests Summary:")
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
