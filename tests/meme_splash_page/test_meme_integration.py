"""
Integration tests for Meme Splash Page feature
Tests the complete user flow from login to dashboard with meme interactions.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from backend.services.meme_service import MemeService
from backend.models.meme_models import Meme, UserMemePreferences, UserMemeHistory
from backend.models.user import User


class TestMemeIntegration:
    """Integration tests for meme splash page feature"""

    def test_complete_user_flow_with_meme(self, test_client, db_session, sample_user, sample_memes):
        """Test complete user flow from login to dashboard with meme interaction"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-integration',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # Mock authentication
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Step 1: User logs in and gets redirected to meme splash
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'meme' in data
            assert data['meme']['id'] is not None

            # Step 2: User views the meme (analytics tracked)
            meme_id = data['meme']['id']
            analytics_data = {
                'meme_id': meme_id,
                'interaction_type': 'viewed',
                'time_spent_seconds': 15,
                'source_page': 'meme_splash'
            }
            
            response = test_client.post(
                '/api/meme-analytics',
                json=analytics_data,
                content_type='application/json'
            )
            assert response.status_code == 200

            # Step 3: User continues to dashboard
            continue_data = {
                'meme_id': meme_id,
                'interaction_type': 'continued',
                'source_page': 'meme_splash'
            }
            
            response = test_client.post(
                '/api/meme-analytics',
                json=continue_data,
                content_type='application/json'
            )
            assert response.status_code == 200

            # Step 4: Verify analytics were recorded
            meme_service = MemeService(db_session)
            stats = meme_service.get_user_meme_stats(sample_user.id)
            assert stats['total_interactions'] >= 2

    def test_user_flow_with_skip(self, test_client, db_session, sample_user, sample_memes):
        """Test user flow when user skips the meme"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-skip',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Get meme
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            meme_id = data['meme']['id']

            # User skips meme
            skip_data = {
                'meme_id': meme_id,
                'interaction_type': 'skipped',
                'source_page': 'meme_splash'
            }
            
            response = test_client.post(
                '/api/meme-analytics',
                json=skip_data,
                content_type='application/json'
            )
            assert response.status_code == 200

            # Verify skip was recorded
            meme_service = MemeService(db_session)
            stats = meme_service.get_user_meme_stats(sample_user.id)
            assert 'skip' in stats['interactions_by_type']

    def test_user_flow_with_opt_out(self, test_client, db_session, sample_user, sample_memes):
        """Test user flow when user opts out of memes"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-opt-out',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # User opts out
            opt_out_data = {
                'memes_enabled': False,
                'opt_out_reason': 'user_requested'
            }
            
            response = test_client.put(
                '/api/user-meme-preferences/123',
                json=opt_out_data,
                content_type='application/json'
            )
            assert response.status_code == 200

            # Verify opt-out was recorded
            meme_service = MemeService(db_session)
            updated_prefs = meme_service.get_user_preferences(sample_user.id)
            assert updated_prefs.memes_enabled is False
            assert updated_prefs.opt_out_reason == 'user_requested'

            # User should not get memes after opt-out
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['meme'] is None

    def test_frequency_limits_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test that frequency limits work in integration"""
        # Setup user preferences with daily frequency
        prefs = UserMemePreferences(
            id='prefs-frequency',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily',
            last_meme_shown_at=datetime.utcnow() - timedelta(hours=1)  # Recent
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # First request should return no meme due to frequency limit
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['meme'] is None

            # Update last shown to be old enough
            prefs.last_meme_shown_at = datetime.utcnow() - timedelta(hours=25)
            db_session.commit()

            # Second request should return a meme
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['meme'] is not None

    def test_category_preferences_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test that category preferences work in integration"""
        # Setup user preferences with specific categories
        prefs = UserMemePreferences(
            id='prefs-categories',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['tuesday_health'],  # Only health category
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            if data['meme']:
                assert data['meme']['category'] == 'tuesday_health'

    def test_analytics_tracking_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test that analytics tracking works end-to-end"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-analytics',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Get meme
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            meme_id = data['meme']['id']

            # Track multiple interactions
            interactions = [
                {'interaction_type': 'viewed', 'time_spent_seconds': 10},
                {'interaction_type': 'liked', 'time_spent_seconds': 5},
                {'interaction_type': 'shared', 'time_spent_seconds': 3}
            ]

            for interaction in interactions:
                analytics_data = {
                    'meme_id': meme_id,
                    'source_page': 'meme_splash',
                    **interaction
                }
                
                response = test_client.post(
                    '/api/meme-analytics',
                    json=analytics_data,
                    content_type='application/json'
                )
                assert response.status_code == 200

            # Verify all interactions were recorded
            meme_service = MemeService(db_session)
            stats = meme_service.get_user_meme_stats(sample_user.id)
            assert stats['total_interactions'] >= len(interactions)

            # Verify meme engagement was updated
            meme = meme_service.get_meme_by_id(meme_id)
            assert meme.view_count > 0
            assert meme.like_count > 0
            assert meme.share_count > 0

    def test_error_recovery_integration(self, test_client, db_session, sample_user):
        """Test error recovery in integration scenarios"""
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Test with database error
            with patch('backend.routes.meme_routes.MemeService') as mock_service:
                mock_service.side_effect = Exception("Database connection failed")
                
                response = test_client.get('/api/user-meme/123')
                assert response.status_code == 500

            # Test recovery after error
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200

    def test_concurrent_user_requests(self, test_client, db_session, sample_user, sample_memes):
        """Test handling of concurrent user requests"""
        import threading
        import queue

        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-concurrent',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        results = queue.Queue()

        def make_request():
            with patch('backend.routes.meme_routes.session') as mock_session:
                mock_session.get.return_value = sample_user.id
                
                response = test_client.get('/api/user-meme/123')
                results.put(response.status_code)

        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        # All requests should succeed
        assert all(code == 200 for code in status_codes)

    def test_data_consistency_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test data consistency across multiple operations"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-consistency',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Get initial preferences
            response = test_client.get('/api/user-meme-preferences/123')
            assert response.status_code == 200
            initial_data = json.loads(response.data)

            # Update preferences
            update_data = {
                'preferred_categories': ['tuesday_health', 'wednesday_home'],
                'frequency_setting': 'weekly'
            }
            
            response = test_client.put(
                '/api/user-meme-preferences/123',
                json=update_data,
                content_type='application/json'
            )
            assert response.status_code == 200

            # Get updated preferences
            response = test_client.get('/api/user-meme-preferences/123')
            assert response.status_code == 200
            updated_data = json.loads(response.data)

            # Verify consistency
            assert updated_data['preferences']['preferred_categories'] == ['tuesday_health', 'wednesday_home']
            assert updated_data['preferences']['frequency_setting'] == 'weekly'

    def test_performance_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test performance characteristics in integration"""
        import time

        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-performance',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Measure response time for meme request
            start_time = time.time()
            response = test_client.get('/api/user-meme/123')
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Response should be reasonably fast (under 1 second)
            assert response_time < 1.0

            # Measure response time for preferences request
            start_time = time.time()
            response = test_client.get('/api/user-meme-preferences/123')
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Response should be reasonably fast (under 1 second)
            assert response_time < 1.0

    def test_security_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test security aspects in integration"""
        # Test unauthorized access
        response = test_client.get('/api/user-meme/123')
        assert response.status_code == 401

        # Test access to other user's data
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = 999  # Different user ID
            
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 403

        # Test SQL injection attempts
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id
            
            # Try to inject SQL in user ID
            response = test_client.get('/api/user-meme/123; DROP TABLE memes; --')
            assert response.status_code == 404  # Should handle gracefully

    def test_rate_limiting_integration(self, test_client, db_session, sample_user):
        """Test rate limiting in integration"""
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Make many requests quickly
            responses = []
            for i in range(100):
                response = test_client.get('/api/user-meme/123')
                responses.append(response.status_code)

            # Check if rate limiting kicked in
            rate_limited = any(code == 429 for code in responses)
            assert rate_limited, "Rate limiting should be active"

    def test_caching_integration(self, test_client, db_session, sample_user, sample_memes):
        """Test caching behavior in integration"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-caching',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # First request
            response1 = test_client.get('/api/user-meme/123')
            assert response1.status_code == 200
            data1 = json.loads(response1.data)

            # Second request (should use cache)
            response2 = test_client.get('/api/user-meme/123')
            assert response2.status_code == 200
            data2 = json.loads(response2.data)

            # Results should be the same (cached)
            assert data1['meme']['id'] == data2['meme']['id']
