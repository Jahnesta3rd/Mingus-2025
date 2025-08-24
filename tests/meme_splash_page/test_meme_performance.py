"""
Performance tests for Meme Splash Page feature
Tests meme loading speed, database query performance, and image optimization.
"""

import pytest
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import psutil
import os
import json

from backend.services.meme_service import MemeService
from backend.models.meme_models import Meme, UserMemePreferences, UserMemeHistory
from backend.models.user import User


class TestMemePerformance:
    """Performance tests for meme splash page feature"""

    def test_meme_loading_speed(self, test_client, db_session, sample_user, sample_memes):
        """Test meme loading speed under normal conditions"""
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

            # Measure response time
            start_time = time.time()
            response = test_client.get('/api/user-meme/123')
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Response should be under 500ms for normal conditions
            assert response_time < 0.5, f"Meme loading took {response_time:.3f}s, expected < 0.5s"

    def test_database_query_performance(self, meme_service, db_session, sample_user, sample_memes):
        """Test database query performance for meme selection"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-db-performance',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # Measure meme selection performance
        start_time = time.time()
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        end_time = time.time()
        
        query_time = end_time - start_time
        
        # Database query should be under 100ms
        assert query_time < 0.1, f"Meme selection query took {query_time:.3f}s, expected < 0.1s"

    def test_concurrent_user_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test performance with multiple concurrent users"""
        # Setup multiple users
        users = []
        for i in range(10):
            user = User(
                id=1000 + i,
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db_session.add(user)
            
            prefs = UserMemePreferences(
                id=f'prefs-concurrent-{i}',
                user_id=user.id,
                memes_enabled=True,
                preferred_categories=['monday_career'],
                frequency_setting='daily'
            )
            db_session.add(prefs)
            users.append(user)
        
        db_session.commit()

        def make_request(user_id):
            with patch('backend.routes.meme_routes.session') as mock_session:
                mock_session.get.return_value = user_id
                
                start_time = time.time()
                response = test_client.get(f'/api/user-meme/{user_id}')
                end_time = time.time()
                
                return {
                    'user_id': user_id,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }

        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, user.id) for user in users]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        response_times = [r['response_time'] for r in results]
        status_codes = [r['status_code'] for r in results]

        # All requests should succeed
        assert all(code == 200 for code in status_codes)
        
        # Average response time should be reasonable
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s, expected < 1.0s"
        
        # 95th percentile should be under 2 seconds
        percentile_95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        assert percentile_95 < 2.0, f"95th percentile response time {percentile_95:.3f}s, expected < 2.0s"

    def test_memory_usage_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test memory usage during meme operations"""
        import gc
        
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-memory',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Make multiple requests
            for i in range(100):
                response = test_client.get('/api/user-meme/123')
                assert response.status_code == 200

        # Force garbage collection
        gc.collect()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (under 50MB)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB, expected < 50MB"

    def test_cache_performance(self, meme_service, db_session, sample_user, sample_memes):
        """Test caching performance benefits"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-cache',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # First request (cache miss)
        start_time = time.time()
        meme1 = meme_service.select_best_meme_for_user(sample_user.id)
        first_request_time = time.time() - start_time

        # Second request (cache hit)
        start_time = time.time()
        meme2 = meme_service.select_best_meme_for_user(sample_user.id)
        second_request_time = time.time() - start_time

        # Cache hit should be faster
        assert second_request_time < first_request_time, "Cache hit should be faster than cache miss"
        
        # Cache hit should be significantly faster (at least 50% improvement)
        speedup = first_request_time / second_request_time
        assert speedup > 1.5, f"Cache speedup was {speedup:.2f}x, expected > 1.5x"

    def test_image_loading_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test image loading performance"""
        import requests
        from unittest.mock import patch

        # Mock image loading to simulate different image sizes
        def mock_image_response(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'fake_image_data' * 1000  # 1KB image
            mock_response.headers = {'content-type': 'image/jpeg'}
            return mock_response

        with patch('requests.get', side_effect=mock_image_response):
            with patch('backend.routes.meme_routes.session') as mock_session:
                mock_session.get.return_value = sample_user.id

                # Measure image loading time
                start_time = time.time()
                response = test_client.get('/api/user-meme/123')
                end_time = time.time()
                
                assert response.status_code == 200
                response_time = end_time - start_time
                
                # Image loading should be under 1 second
                assert response_time < 1.0, f"Image loading took {response_time:.3f}s, expected < 1.0s"

    def test_database_connection_pool_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test database connection pool performance under load"""
        # Setup multiple users
        users = []
        for i in range(50):
            user = User(
                id=2000 + i,
                email=f"loaduser{i}@example.com",
                first_name=f"LoadUser{i}",
                last_name="Test",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db_session.add(user)
            
            prefs = UserMemePreferences(
                id=f'prefs-load-{i}',
                user_id=user.id,
                memes_enabled=True,
                preferred_categories=['monday_career'],
                frequency_setting='daily'
            )
            db_session.add(prefs)
            users.append(user)
        
        db_session.commit()

        def make_request(user_id):
            with patch('backend.routes.meme_routes.session') as mock_session:
                mock_session.get.return_value = user_id
                
                start_time = time.time()
                response = test_client.get(f'/api/user-meme/{user_id}')
                end_time = time.time()
                
                return {
                    'user_id': user_id,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }

        # Make many concurrent requests to test connection pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, user.id) for user in users[:20]]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r['status_code'] == 200 for r in results)
        
        # No requests should timeout
        response_times = [r['response_time'] for r in results]
        assert all(time < 5.0 for time in response_times), "Some requests timed out"

    def test_analytics_tracking_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test analytics tracking performance"""
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-analytics-perf',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Get meme first
            response = test_client.get('/api/user-meme/123')
            assert response.status_code == 200
            data = json.loads(response.data)
            meme_id = data['meme']['id']

            # Measure analytics tracking performance
            analytics_times = []
            for i in range(100):
                analytics_data = {
                    'meme_id': meme_id,
                    'interaction_type': 'viewed',
                    'time_spent_seconds': 10,
                    'source_page': 'meme_splash'
                }
                
                start_time = time.time()
                response = test_client.post(
                    '/api/meme-analytics',
                    json=analytics_data,
                    content_type='application/json'
                )
                end_time = time.time()
                
                assert response.status_code == 200
                analytics_times.append(end_time - start_time)

            # Analytics tracking should be fast
            avg_analytics_time = statistics.mean(analytics_times)
            assert avg_analytics_time < 0.1, f"Average analytics tracking time {avg_analytics_time:.3f}s, expected < 0.1s"

    def test_rate_limiting_performance(self, test_client, db_session, sample_user):
        """Test rate limiting performance impact"""
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Make requests quickly to trigger rate limiting
            start_time = time.time()
            responses = []
            for i in range(60):  # Exceed rate limit
                response = test_client.get('/api/user-meme/123')
                responses.append(response.status_code)
            end_time = time.time()

            total_time = end_time - start_time
            
            # Rate limiting should not significantly slow down requests
            avg_time_per_request = total_time / len(responses)
            assert avg_time_per_request < 0.1, f"Average time per request {avg_time_per_request:.3f}s, expected < 0.1s"

            # Some requests should be rate limited
            rate_limited_count = responses.count(429)
            assert rate_limited_count > 0, "Rate limiting should be active"

    def test_large_dataset_performance(self, meme_service, db_session, sample_user):
        """Test performance with large dataset"""
        # Create many memes
        memes = []
        for i in range(1000):
            meme = Meme(
                id=f'meme-large-{i}',
                image_url=f'https://example.com/meme{i}.jpg',
                category='monday_career',
                caption_text=f'Test meme {i}',
                alt_text=f'Alt text for meme {i}',
                priority=i % 10,
                is_active=True,
                engagement_score=i / 1000.0
            )
            memes.append(meme)
        
        db_session.add_all(memes)
        
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-large-dataset',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # Measure meme selection performance with large dataset
        start_time = time.time()
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        end_time = time.time()
        
        selection_time = end_time - start_time
        
        # Should still be reasonably fast even with large dataset
        assert selection_time < 0.5, f"Meme selection with large dataset took {selection_time:.3f}s, expected < 0.5s"

    def test_cpu_usage_performance(self, test_client, db_session, sample_user, sample_memes):
        """Test CPU usage during meme operations"""
        import psutil
        
        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-cpu',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        process = psutil.Process(os.getpid())
        
        # Get initial CPU usage
        initial_cpu_percent = process.cpu_percent(interval=0.1)

        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = sample_user.id

            # Make many requests
            for i in range(100):
                response = test_client.get('/api/user-meme/123')
                assert response.status_code == 200

        # Get final CPU usage
        final_cpu_percent = process.cpu_percent(interval=0.1)
        
        # CPU usage should be reasonable (under 80% for short burst)
        assert final_cpu_percent < 80, f"CPU usage {final_cpu_percent:.1f}%, expected < 80%"

    def test_disk_io_performance(self, meme_service, db_session, sample_user, sample_memes):
        """Test disk I/O performance for database operations"""
        import psutil
        
        process = psutil.Process(os.getpid())
        
        # Get initial disk I/O
        initial_io = process.io_counters()

        # Setup user preferences
        prefs = UserMemePreferences(
            id='prefs-disk-io',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()

        # Perform many database operations
        for i in range(100):
            meme_service.select_best_meme_for_user(sample_user.id)

        # Get final disk I/O
        final_io = process.io_counters()
        
        # Calculate I/O increase
        read_bytes_increase = final_io.read_bytes - initial_io.read_bytes
        write_bytes_increase = final_io.write_bytes - initial_io.write_bytes
        
        # I/O should be reasonable (under 10MB for 100 operations)
        total_io_mb = (read_bytes_increase + write_bytes_increase) / 1024 / 1024
        assert total_io_mb < 10, f"Total I/O {total_io_mb:.1f}MB, expected < 10MB"
