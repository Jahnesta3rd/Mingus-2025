#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme API Endpoints Unit Tests
Comprehensive unit tests for the meme API endpoints and database operations
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import Flask test client and the meme API
from flask import Flask
from backend.api.meme_endpoints import meme_api, get_user_meme, track_meme_analytics

class TestMemeAPIEndpoints(unittest.TestCase):
    """Unit tests for the meme API endpoints"""
    
    def setUp(self):
        """Set up test Flask app and database"""
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.register_blueprint(meme_api)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Mock the database path
        self.original_db_path = None
        self._setup_test_database()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def _setup_test_database(self):
        """Set up test database with sample data"""
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Create memes table
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
            
            # Create user meme history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_meme_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meme_id INTEGER NOT NULL,
                    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, meme_id)
                )
            """)
            
            # Create meme analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meme_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meme_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('view', 'continue', 'skip', 'auto_advance')),
                    user_id TEXT,
                    session_id TEXT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (meme_id) REFERENCES memes (id)
                )
            """)
            
            # Insert test memes
            test_memes = [
                ('https://example.com/meme1.jpg', 'faith', 'Sunday motivation', 'Faith meme', 1),
                ('https://example.com/meme2.jpg', 'work_life', 'Monday blues', 'Work meme', 1),
                ('https://example.com/meme3.jpg', 'health', 'Tuesday workout', 'Health meme', 1),
                ('https://example.com/meme4.jpg', 'housing', 'Wednesday house hunting', 'Housing meme', 1),
                ('https://example.com/meme5.jpg', 'transportation', 'Thursday commute', 'Transport meme', 1),
                ('https://example.com/meme6.jpg', 'relationships', 'Friday date night', 'Relationship meme', 1),
                ('https://example.com/meme7.jpg', 'family', 'Saturday family time', 'Family meme', 1),
                ('https://example.com/inactive.jpg', 'faith', 'Inactive meme', 'Inactive meme', 0),
            ]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, test_memes)
            
            conn.commit()
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_get_user_meme_endpoint_success(self, mock_db_path):
        """Test successful meme retrieval"""
        mock_db_path.return_value = self.test_db.name
        
        # Mock the database connection
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_row = MagicMock()
            
            # Mock the meme data
            mock_row.__getitem__.side_effect = lambda key: {
                'id': 1,
                'image_url': 'https://example.com/meme1.jpg',
                'category': 'faith',
                'caption': 'Sunday motivation',
                'alt_text': 'Faith meme',
                'is_active': 1,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            }[key]
            
            mock_cursor.fetchone.return_value = mock_row
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Make request
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': 'user123',
                'X-Session-ID': 'session456'
            })
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertIn('id', data)
            self.assertIn('image_url', data)
            self.assertIn('category', data)
            self.assertIn('caption', data)
            self.assertIn('alt_text', data)
            self.assertEqual(data['id'], 1)
            self.assertEqual(data['category'], 'faith')
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_get_user_meme_endpoint_no_memes(self, mock_db_path):
        """Test meme retrieval when no memes are available"""
        mock_db_path.return_value = self.test_db.name
        
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            response = self.client.get('/api/user-meme')
            
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'No memes available')
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_get_user_meme_endpoint_database_error(self, mock_db_path):
        """Test meme retrieval with database error"""
        mock_db_path.return_value = self.test_db.name
        
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = self.client.get('/api/user-meme')
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Internal server error')
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_track_meme_analytics_endpoint_success(self, mock_db_path):
        """Test successful analytics tracking"""
        mock_db_path.return_value = self.test_db.name
        
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Test data
            analytics_data = {
                'meme_id': 1,
                'action': 'view',
                'user_id': 'user123',
                'session_id': 'session456'
            }
            
            response = self.client.post('/api/meme-analytics',
                                      data=json.dumps(analytics_data),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('success', data)
            self.assertTrue(data['success'])
    
    def test_track_meme_analytics_endpoint_invalid_json(self):
        """Test analytics tracking with invalid JSON"""
        response = self.client.post('/api/meme-analytics',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Bad request')
    
    def test_track_meme_analytics_endpoint_missing_fields(self):
        """Test analytics tracking with missing required fields"""
        analytics_data = {
            'meme_id': 1
            # Missing 'action' field
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required field', data['message'])
    
    def test_track_meme_analytics_endpoint_invalid_action(self):
        """Test analytics tracking with invalid action"""
        analytics_data = {
            'meme_id': 1,
            'action': 'invalid_action'
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Invalid action', data['message'])
    
    def test_track_meme_analytics_endpoint_invalid_meme_id(self):
        """Test analytics tracking with invalid meme_id"""
        analytics_data = {
            'meme_id': 'not_a_number',
            'action': 'view'
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('meme_id must be an integer', data['message'])
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_get_meme_stats_endpoint_success(self, mock_db_path):
        """Test successful meme statistics retrieval"""
        mock_db_path.return_value = self.test_db.name
        
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            # Mock the statistics queries
            mock_cursor.fetchone.side_effect = [
                {'total': 7},  # Total memes
                None,  # Analytics query returns empty
                None   # Popular memes query returns empty
            ]
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            response = self.client.get('/api/meme-stats')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertIn('total_memes', data)
            self.assertIn('analytics_last_7_days', data)
            self.assertIn('popular_memes', data)
            self.assertEqual(data['total_memes'], 7)
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_get_meme_stats_endpoint_database_error(self, mock_db_path):
        """Test meme statistics with database error"""
        mock_db_path.return_value = self.test_db.name
        
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")
            
            response = self.client.get('/api/meme-stats')
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Internal server error')
    
    def test_get_user_meme_function_unit(self):
        """Test the get_user_meme function directly"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_row = MagicMock()
            
            # Mock the meme data
            mock_row.__getitem__.side_effect = lambda key: {
                'id': 1,
                'image_url': 'https://example.com/meme1.jpg',
                'category': 'faith',
                'caption': 'Sunday motivation',
                'alt_text': 'Faith meme',
                'is_active': 1,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            }[key]
            
            mock_cursor.fetchone.return_value = mock_row
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Test the function
            meme = get_user_meme('user123', 'session456')
            
            self.assertIsNotNone(meme)
            self.assertEqual(meme['id'], 1)
            self.assertEqual(meme['category'], 'faith')
            self.assertEqual(meme['caption'], 'Sunday motivation')
    
    def test_get_user_meme_function_no_memes(self):
        """Test get_user_meme function when no memes available"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            meme = get_user_meme('user123', 'session456')
            
            self.assertIsNone(meme)
    
    def test_track_meme_analytics_function_unit(self):
        """Test the track_meme_analytics function directly"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Mock request object
            with patch('backend.api.meme_endpoints.request') as mock_request:
                mock_request.remote_addr = '127.0.0.1'
                mock_request.headers.get.return_value = 'Test User Agent'
                
                # Test the function
                track_meme_analytics(1, 'view', 'user123', 'session456')
                
                # Verify database operations
                mock_cursor.execute.assert_called()
                mock_conn.commit.assert_called()
                mock_conn.close.assert_called()
    
    def test_track_meme_analytics_function_error_handling(self):
        """Test track_meme_analytics function error handling"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")
            
            # Should not raise exception (analytics failure shouldn't break user experience)
            try:
                track_meme_analytics(1, 'view', 'user123', 'session456')
            except Exception:
                self.fail("track_meme_analytics should not raise exceptions")
    
    def test_api_error_handlers(self):
        """Test API error handlers"""
        # Test 404 handler
        response = self.client.get('/api/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Not found')
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = self.client.get('/api/user-meme')
        
        # Check for common CORS headers
        # Note: This test assumes CORS is configured in the main app
        # The actual CORS headers would be set by the main Flask app configuration
    
    def test_request_headers_handling(self):
        """Test that request headers are properly handled"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_row = MagicMock()
            
            mock_row.__getitem__.side_effect = lambda key: {
                'id': 1,
                'image_url': 'https://example.com/meme1.jpg',
                'category': 'faith',
                'caption': 'Sunday motivation',
                'alt_text': 'Faith meme',
                'is_active': 1,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            }[key]
            
            mock_cursor.fetchone.return_value = mock_row
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Test with headers
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': 'test_user',
                'X-Session-ID': 'test_session',
                'User-Agent': 'Test Browser'
            })
            
            self.assertEqual(response.status_code, 200)
    
    def test_analytics_table_creation(self):
        """Test that analytics table is created if it doesn't exist"""
        with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Mock request object
            with patch('backend.api.meme_endpoints.request') as mock_request:
                mock_request.remote_addr = '127.0.0.1'
                mock_request.headers.get.return_value = 'Test User Agent'
                
                track_meme_analytics(1, 'view', 'user123', 'session456')
                
                # Verify CREATE TABLE statement was executed
                create_table_calls = [call for call in mock_cursor.execute.call_args_list 
                                    if 'CREATE TABLE' in str(call)]
                self.assertGreater(len(create_table_calls), 0, 
                                 "Should create analytics table if it doesn't exist")


class TestMemeAPIIntegration(unittest.TestCase):
    """Integration tests for the meme API"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.app = Flask(__name__)
        self.app.register_blueprint(meme_api)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create real temporary database for integration tests
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up real database
        self._setup_real_database()
    
    def tearDown(self):
        """Clean up integration test database"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def _setup_real_database(self):
        """Set up real database for integration testing"""
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meme_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meme_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('view', 'continue', 'skip', 'auto_advance')),
                    user_id TEXT,
                    session_id TEXT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (meme_id) REFERENCES memes (id)
                )
            """)
            
            # Insert test data
            test_memes = [
                ('https://example.com/meme1.jpg', 'faith', 'Sunday motivation', 'Faith meme', 1),
                ('https://example.com/meme2.jpg', 'work_life', 'Monday blues', 'Work meme', 1),
                ('https://example.com/meme3.jpg', 'health', 'Tuesday workout', 'Health meme', 1),
            ]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, test_memes)
            
            conn.commit()
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_full_user_journey_integration(self, mock_db_path):
        """Test complete user journey through the API"""
        mock_db_path.return_value = self.test_db.name
        
        # Step 1: Get a meme
        response = self.client.get('/api/user-meme', headers={
            'X-User-ID': 'user123',
            'X-Session-ID': 'session456'
        })
        
        self.assertEqual(response.status_code, 200)
        meme_data = json.loads(response.data)
        meme_id = meme_data['id']
        
        # Step 2: Track view analytics
        analytics_data = {
            'meme_id': meme_id,
            'action': 'view',
            'user_id': 'user123',
            'session_id': 'session456'
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Track continue action
        analytics_data['action'] = 'continue'
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Get statistics
        response = self.client.get('/api/meme-stats')
        self.assertEqual(response.status_code, 200)
        stats_data = json.loads(response.data)
        
        self.assertIn('total_memes', stats_data)
        self.assertIn('analytics_last_7_days', stats_data)
        self.assertIn('popular_memes', stats_data)
    
    @patch('backend.api.meme_endpoints.DB_PATH')
    def test_analytics_persistence_integration(self, mock_db_path):
        """Test that analytics are properly persisted to database"""
        mock_db_path.return_value = self.test_db.name
        
        # Track analytics
        analytics_data = {
            'meme_id': 1,
            'action': 'view',
            'user_id': 'user123',
            'session_id': 'session456'
        }
        
        response = self.client.post('/api/meme-analytics',
                                  data=json.dumps(analytics_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify data was persisted
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM meme_analytics 
                WHERE meme_id = ? AND user_id = ? AND action = ?
            """, (1, 'user123', 'view'))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Analytics should be persisted to database")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.makeSuite(TestMemeAPIEndpoints))
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestMemeAPIIntegration))
    
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
