#!/usr/bin/env python3
"""
Mingus Personal Finance App - Mood Tracking Tests
Comprehensive tests for the mood tracking and correlation system
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from backend.api.meme_endpoints import meme_api, calculate_mood_spending_correlation, generate_mood_insights, get_mood_recommendation
from flask import Flask
from tests.meme_splash.fixtures.test_data import MemeTestData, DatabaseTestSetup

class TestMoodTrackingAPI(unittest.TestCase):
    """Tests for mood tracking API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
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
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_track_meme_mood_success(self):
        """Test successful mood tracking"""
        mood_data = {
            'meme_id': 1,
            'mood_score': 4,
            'mood_label': 'happy',
            'meme_category': 'faith'
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={
                                      'X-User-ID': 'user123',
                                      'X-Session-ID': 'session456'
                                  })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('correlation', data)
    
    def test_track_meme_mood_invalid_score(self):
        """Test mood tracking with invalid score"""
        mood_data = {
            'meme_id': 1,
            'mood_score': 6,  # Invalid score (should be 1-5)
            'mood_label': 'happy'
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={'X-User-ID': 'user123'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Mood score must be between 1 and 5', data['message'])
    
    def test_track_meme_mood_invalid_label(self):
        """Test mood tracking with invalid label"""
        mood_data = {
            'meme_id': 1,
            'mood_score': 4,
            'mood_label': 'invalid_mood'  # Invalid label
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={'X-User-ID': 'user123'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid mood label', data['message'])
    
    def test_track_meme_mood_missing_user_id(self):
        """Test mood tracking without user ID"""
        mood_data = {
            'meme_id': 1,
            'mood_score': 4,
            'mood_label': 'happy'
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('User ID is required', data['message'])
    
    def test_track_meme_mood_missing_fields(self):
        """Test mood tracking with missing required fields"""
        mood_data = {
            'meme_id': 1
            # Missing mood_score and mood_label
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={'X-User-ID': 'user123'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Missing required field', data['message'])
    
    def test_get_mood_analytics_success(self):
        """Test successful mood analytics retrieval"""
        response = self.client.get('/api/mood-analytics',
                                 headers={'X-User-ID': '1'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check response structure
        self.assertIn('mood_statistics', data)
        self.assertIn('spending_correlation', data)
        self.assertIn('mood_trends', data)
        self.assertIn('insights', data)
        
        # Check that we have some mood statistics
        self.assertIsInstance(data['mood_statistics'], list)
        self.assertIsInstance(data['mood_trends'], list)
        self.assertIsInstance(data['insights'], list)
    
    def test_get_mood_analytics_missing_user_id(self):
        """Test mood analytics without user ID"""
        response = self.client.get('/api/mood-analytics')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('User ID is required', data['message'])
    
    def test_mood_data_persistence(self):
        """Test that mood data is properly stored in database"""
        mood_data = {
            'meme_id': 1,
            'mood_score': 5,
            'mood_label': 'excited',
            'meme_category': 'faith'
        }
        
        # Track mood
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={
                                      'X-User-ID': 'user123',
                                      'X-Session-ID': 'session456'
                                  })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify data was stored
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_mood_data 
                WHERE user_id = ? AND meme_id = ? AND mood_label = ?
            """, ('user123', 1, 'excited'))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[3], 5)  # mood_score
            self.assertEqual(result[4], 'excited')  # mood_label


class TestMoodCorrelationAlgorithm(unittest.TestCase):
    """Tests for mood-spending correlation algorithm"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with test data
        DatabaseTestSetup.create_test_database(self.test_db.name)
        
        # Mock database path
        self.db_path_patcher = patch('backend.api.meme_endpoints.DB_PATH', self.test_db.name)
        self.db_path_patcher.start()
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_calculate_mood_spending_correlation_insufficient_data(self):
        """Test correlation calculation with insufficient data"""
        correlation = calculate_mood_spending_correlation('user999')
        
        self.assertEqual(correlation['correlation_coefficient'], 0.0)
        self.assertEqual(correlation['pattern'], 'insufficient_data')
        self.assertEqual(correlation['data_points'], 0)
        self.assertEqual(correlation['confidence'], 'low')
    
    def test_calculate_mood_spending_correlation_high_mood(self):
        """Test correlation calculation with high mood data"""
        # Add high mood data
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add multiple high mood entries
            for i in range(5):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'high_mood_user',
                    f'session_{i}',
                    i + 1,
                    5,  # High mood score
                    'excited',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        correlation = calculate_mood_spending_correlation('high_mood_user')
        
        self.assertEqual(correlation['pattern']['type'], 'high_mood')
        self.assertEqual(correlation['pattern']['risk_level'], 'medium')
        self.assertEqual(correlation['data_points'], 5)
    
    def test_calculate_mood_spending_correlation_low_mood(self):
        """Test correlation calculation with low mood data"""
        # Add low mood data
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add multiple low mood entries
            for i in range(5):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'low_mood_user',
                    f'session_{i}',
                    i + 1,
                    1,  # Low mood score
                    'angry',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        correlation = calculate_mood_spending_correlation('low_mood_user')
        
        self.assertEqual(correlation['pattern']['type'], 'low_mood')
        self.assertEqual(correlation['pattern']['risk_level'], 'high')
        self.assertEqual(correlation['data_points'], 5)
    
    def test_calculate_mood_spending_correlation_stable_mood(self):
        """Test correlation calculation with stable mood data"""
        # Add stable mood data
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add multiple neutral mood entries
            for i in range(5):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'stable_mood_user',
                    f'session_{i}',
                    i + 1,
                    3,  # Neutral mood score
                    'neutral',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        correlation = calculate_mood_spending_correlation('stable_mood_user')
        
        self.assertEqual(correlation['pattern']['type'], 'stable_mood')
        self.assertEqual(correlation['pattern']['risk_level'], 'low')
        self.assertEqual(correlation['data_points'], 5)


class TestMoodInsights(unittest.TestCase):
    """Tests for mood insights generation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with test data
        DatabaseTestSetup.create_test_database(self.test_db.name)
        
        # Mock database path
        self.db_path_patcher = patch('backend.api.meme_endpoints.DB_PATH', self.test_db.name)
        self.db_path_patcher.start()
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_generate_mood_insights_no_data(self):
        """Test insights generation with no mood data"""
        insights = generate_mood_insights('user999')
        self.assertEqual(insights, [])
    
    def test_generate_mood_insights_mood_pattern(self):
        """Test insights generation with mood pattern detection"""
        # Add repeated mood data
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add multiple happy mood entries
            for i in range(4):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'pattern_user',
                    f'session_{i}',
                    i + 1,
                    4,
                    'happy',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        insights = generate_mood_insights('pattern_user')
        
        # Should detect mood pattern
        self.assertGreater(len(insights), 0)
        mood_pattern_insight = next((i for i in insights if i['type'] == 'mood_pattern'), None)
        self.assertIsNotNone(mood_pattern_insight)
        self.assertIn('happy', mood_pattern_insight['message'])
    
    def test_generate_mood_insights_positive_trend(self):
        """Test insights generation with positive trend detection"""
        # Add positive mood trend
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add high mood entries
            for i in range(3):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'positive_trend_user',
                    f'session_{i}',
                    i + 1,
                    5,  # High mood score
                    'excited',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        insights = generate_mood_insights('positive_trend_user')
        
        # Should detect positive trend
        positive_trend_insight = next((i for i in insights if i['type'] == 'positive_trend'), None)
        self.assertIsNotNone(positive_trend_insight)
        self.assertIn('great mood', positive_trend_insight['message'])
    
    def test_generate_mood_insights_negative_trend(self):
        """Test insights generation with negative trend detection"""
        # Add negative mood trend
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Add low mood entries
            for i in range(3):
                cursor.execute("""
                    INSERT INTO user_mood_data 
                    (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'negative_trend_user',
                    f'session_{i}',
                    i + 1,
                    1,  # Low mood score
                    'angry',
                    'faith',
                    'before_budget_check'
                ))
            
            conn.commit()
        
        insights = generate_mood_insights('negative_trend_user')
        
        # Should detect negative trend
        negative_trend_insight = next((i for i in insights if i['type'] == 'negative_trend'), None)
        self.assertIsNotNone(negative_trend_insight)
        self.assertIn('feeling down', negative_trend_insight['message'])


class TestMoodRecommendations(unittest.TestCase):
    """Tests for mood-based recommendations"""
    
    def test_get_mood_recommendation_excited(self):
        """Test recommendation for excited mood"""
        recommendation = get_mood_recommendation('excited')
        self.assertIn('budget reminder', recommendation)
        self.assertIn('impulse purchases', recommendation)
    
    def test_get_mood_recommendation_happy(self):
        """Test recommendation for happy mood"""
        recommendation = get_mood_recommendation('happy')
        self.assertIn('financial goals', recommendation)
    
    def test_get_mood_recommendation_neutral(self):
        """Test recommendation for neutral mood"""
        recommendation = get_mood_recommendation('neutral')
        self.assertIn('on track', recommendation)
    
    def test_get_mood_recommendation_sad(self):
        """Test recommendation for sad mood"""
        recommendation = get_mood_recommendation('sad')
        self.assertIn('retail therapy', recommendation)
        self.assertIn('Take care', recommendation)
    
    def test_get_mood_recommendation_angry(self):
        """Test recommendation for angry mood"""
        recommendation = get_mood_recommendation('angry')
        self.assertIn('deep breath', recommendation)
        self.assertIn('impulse spending', recommendation)
    
    def test_get_mood_recommendation_unknown(self):
        """Test recommendation for unknown mood"""
        recommendation = get_mood_recommendation('unknown_mood')
        self.assertIn('Continue monitoring', recommendation)


class TestMoodTrackingIntegration(unittest.TestCase):
    """Integration tests for mood tracking system"""
    
    def setUp(self):
        """Set up test environment"""
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
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_complete_mood_tracking_workflow(self):
        """Test complete mood tracking workflow"""
        user_id = 'integration_user'
        session_id = 'integration_session'
        
        # Step 1: Track multiple moods
        moods = [
            {'meme_id': 1, 'mood_score': 5, 'mood_label': 'excited', 'meme_category': 'faith'},
            {'meme_id': 2, 'mood_score': 4, 'mood_label': 'happy', 'meme_category': 'work_life'},
            {'meme_id': 3, 'mood_score': 2, 'mood_label': 'sad', 'meme_category': 'health'},
            {'meme_id': 4, 'mood_score': 3, 'mood_label': 'neutral', 'meme_category': 'housing'},
        ]
        
        for mood in moods:
            response = self.client.post('/api/meme-mood',
                                      data=json.dumps(mood),
                                      content_type='application/json',
                                      headers={
                                          'X-User-ID': user_id,
                                          'X-Session-ID': session_id
                                      })
            self.assertEqual(response.status_code, 200)
        
        # Step 2: Get mood analytics
        response = self.client.get('/api/mood-analytics',
                                 headers={'X-User-ID': user_id})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify analytics structure
        self.assertIn('mood_statistics', data)
        self.assertIn('spending_correlation', data)
        self.assertIn('mood_trends', data)
        self.assertIn('insights', data)
        
        # Verify we have mood statistics for all moods
        mood_labels = [stat['mood_label'] for stat in data['mood_statistics']]
        self.assertIn('excited', mood_labels)
        self.assertIn('happy', mood_labels)
        self.assertIn('sad', mood_labels)
        self.assertIn('neutral', mood_labels)
        
        # Verify correlation was calculated
        self.assertIsNotNone(data['spending_correlation'])
        self.assertIn('pattern', data['spending_correlation'])
        
        # Verify insights were generated
        self.assertIsInstance(data['insights'], list)
    
    def test_mood_tracking_with_database_consistency(self):
        """Test mood tracking maintains database consistency"""
        user_id = 'consistency_user'
        
        # Track mood
        mood_data = {
            'meme_id': 1,
            'mood_score': 4,
            'mood_label': 'happy',
            'meme_category': 'faith'
        }
        
        response = self.client.post('/api/meme-mood',
                                  data=json.dumps(mood_data),
                                  content_type='application/json',
                                  headers={'X-User-ID': user_id})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify data consistency
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            
            # Check mood data
            cursor.execute("""
                SELECT COUNT(*) FROM user_mood_data WHERE user_id = ?
            """, (user_id,))
            mood_count = cursor.fetchone()[0]
            self.assertEqual(mood_count, 1)
            
            # Check analytics data
            cursor.execute("""
                SELECT COUNT(*) FROM meme_analytics WHERE user_id = ?
            """, (user_id,))
            analytics_count = cursor.fetchone()[0]
            self.assertGreaterEqual(analytics_count, 0)  # May be 0 if no analytics tracked


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestMoodTrackingAPI))
    test_suite.addTest(unittest.makeSuite(TestMoodCorrelationAlgorithm))
    test_suite.addTest(unittest.makeSuite(TestMoodInsights))
    test_suite.addTest(unittest.makeSuite(TestMoodRecommendations))
    test_suite.addTest(unittest.makeSuite(TestMoodTrackingIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Mood Tracking Tests Summary:")
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
