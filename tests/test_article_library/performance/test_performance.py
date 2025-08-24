"""
Performance Tests for Article Library

Tests for performance, scalability, and load handling in the Mingus article library system.
"""

import pytest
import time
import concurrent.futures
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

class TestSearchPerformance:
    """Test search performance and response times"""
    
    @pytest.mark.performance
    def test_search_response_time(self, client, auth_headers, performance_benchmark):
        """Test search endpoint response time"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            response = client.get(
                '/api/articles/search?query=salary&page=1&per_page=10',
                headers=auth_headers
            )
            
            performance_benchmark.assert_faster_than(1.0)  # Should complete in under 1 second
            assert response.status_code == 200
    
    @pytest.mark.performance
    def test_large_search_query_performance(self, client, auth_headers, performance_benchmark):
        """Test performance with large search queries"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Large search query
            large_query = 'finance OR money OR wealth OR investment OR career OR salary OR negotiation OR strategy OR planning OR management OR budget OR saving OR spending OR debt OR credit OR loan OR mortgage OR insurance OR retirement OR estate OR tax OR business OR entrepreneurship OR side hustle OR passive income OR real estate OR stocks OR bonds OR mutual funds OR ETFs OR cryptocurrency OR blockchain OR fintech OR digital banking OR mobile payments OR peer to peer lending OR crowdfunding OR angel investing OR venture capital OR private equity OR hedge funds OR commodities OR forex OR options OR futures OR derivatives OR structured products OR annuities OR life insurance OR health insurance OR disability insurance OR long term care insurance OR umbrella insurance OR professional liability insurance OR cyber insurance OR identity theft protection OR credit monitoring OR fraud protection OR financial planning OR retirement planning OR estate planning OR tax planning OR insurance planning OR investment planning OR debt management OR credit repair OR bankruptcy OR foreclosure OR short sale OR deed in lieu OR loan modification OR refinancing OR consolidation OR settlement OR negotiation OR mediation OR arbitration OR litigation OR legal advice OR financial advice OR investment advice OR tax advice OR legal services OR financial services OR investment services OR banking services OR credit services OR insurance services OR real estate services OR business services OR consulting services OR coaching services OR mentoring services OR networking services OR professional development OR continuing education OR certification OR licensing OR accreditation OR compliance OR regulation OR oversight OR governance OR risk management OR internal controls OR audit OR review OR assessment OR evaluation OR monitoring OR reporting OR disclosure OR transparency OR accountability OR responsibility OR ethics OR integrity OR trust OR confidence OR credibility OR reputation OR brand OR marketing OR advertising OR promotion OR publicity OR public relations OR media relations OR investor relations OR customer relations OR employee relations OR vendor relations OR partner relations OR stakeholder relations OR community relations OR government relations OR regulatory relations OR industry relations OR trade relations OR international relations OR diplomatic relations OR political relations OR economic relations OR social relations OR cultural relations OR environmental relations OR sustainability OR corporate social responsibility OR philanthropy OR charitable giving OR volunteering OR community service OR social impact OR social enterprise OR social innovation OR social entrepreneurship OR social finance OR impact investing OR sustainable investing OR responsible investing OR ethical investing OR green investing OR clean energy OR renewable energy OR energy efficiency OR energy conservation OR energy management OR energy policy OR energy regulation OR energy market OR energy trading OR energy finance OR energy investment OR energy technology OR energy innovation OR energy infrastructure OR energy security OR energy independence OR energy diversification OR energy transition OR energy transformation OR energy revolution OR energy evolution OR energy future OR energy outlook OR energy forecast OR energy projection OR energy scenario OR energy planning OR energy strategy'
            
            performance_benchmark.start()
            
            response = client.get(
                f'/api/articles/search?query={large_query}&page=1&per_page=10',
                headers=auth_headers
            )
            
            performance_benchmark.assert_faster_than(2.0)  # Should complete in under 2 seconds
            assert response.status_code == 200
    
    @pytest.mark.performance
    def test_multiple_filter_performance(self, client, auth_headers, performance_benchmark):
        """Test performance with multiple filters"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            response = client.get(
                '/api/articles/search?query=test&primary_phase=DO&difficulty_level=Intermediate&demographic_relevance_min=7&cultural_sensitivity_min=6&income_impact_potential_min=7&actionability_score_min=6&professional_development_value_min=7&target_income_range=$40K-$60K&career_stage=Mid-career&domain=nerdwallet.com&page=1&per_page=10',
                headers=auth_headers
            )
            
            performance_benchmark.assert_faster_than(1.5)  # Should complete in under 1.5 seconds
            assert response.status_code == 200
    
    @pytest.mark.performance
    def test_pagination_performance(self, client, auth_headers, performance_benchmark):
        """Test performance with different page sizes"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test different page sizes
            page_sizes = [10, 25, 50, 100]
            
            for page_size in page_sizes:
                performance_benchmark.start()
                
                response = client.get(
                    f'/api/articles/search?query=test&page=1&per_page={page_size}',
                    headers=auth_headers
                )
                
                # Response time should scale reasonably with page size
                max_time = min(2.0, 0.5 + (page_size / 100))  # Linear scaling with reasonable bounds
                performance_benchmark.assert_faster_than(max_time)
                assert response.status_code == 200

class TestConcurrentAccessPerformance:
    """Test performance under concurrent access"""
    
    @pytest.mark.performance
    def test_concurrent_search_requests(self, client, auth_headers, performance_benchmark):
        """Test handling multiple concurrent search requests"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            def make_search_request():
                return client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
            
            # Test with different numbers of concurrent requests
            concurrent_requests = [5, 10, 20]
            
            for num_requests in concurrent_requests:
                performance_benchmark.start()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
                    futures = [executor.submit(make_search_request) for _ in range(num_requests)]
                    responses = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                # All requests should complete successfully
                assert all(response.status_code == 200 for response in responses)
                
                # Total time should be reasonable
                performance_benchmark.assert_faster_than(5.0)  # Should complete in under 5 seconds
    
    @pytest.mark.performance
    def test_concurrent_article_access(self, client, auth_headers, sample_articles, performance_benchmark):
        """Test concurrent access to article details"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            
            def make_article_request():
                return client.get(f'/api/articles/{article_id}', headers=auth_headers)
            
            performance_benchmark.start()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_article_request) for _ in range(10)]
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            assert all(response.status_code == 200 for response in responses)
            performance_benchmark.assert_faster_than(3.0)
    
    @pytest.mark.performance
    def test_concurrent_user_interactions(self, client, auth_headers, sample_articles, performance_benchmark):
        """Test concurrent user interactions (read, bookmark, rate)"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            
            def make_read_request():
                return client.post(
                    f'/api/articles/{article_id}/read',
                    data='{"read_duration_minutes": 10, "completion_percentage": 85}',
                    headers=auth_headers
                )
            
            def make_bookmark_request():
                return client.post(
                    f'/api/articles/{article_id}/bookmark',
                    data='{"notes": "Test bookmark"}',
                    headers=auth_headers
                )
            
            def make_rating_request():
                return client.post(
                    f'/api/articles/{article_id}/rate',
                    data='{"rating": 4, "feedback": "Test rating"}',
                    headers=auth_headers
                )
            
            performance_benchmark.start()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                futures = []
                # Mix of different interaction types
                for _ in range(5):
                    futures.append(executor.submit(make_read_request))
                for _ in range(5):
                    futures.append(executor.submit(make_bookmark_request))
                for _ in range(5):
                    futures.append(executor.submit(make_rating_request))
                
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            assert all(response.status_code == 200 for response in responses)
            performance_benchmark.assert_faster_than(4.0)

class TestDatabasePerformance:
    """Test database query performance"""
    
    @pytest.mark.performance
    def test_large_dataset_search_performance(self, client, auth_headers, performance_benchmark):
        """Test search performance with large dataset"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Mock large dataset
            with patch('backend.routes.articles.Article') as mock_article:
                # Simulate 10,000 articles
                mock_article.query.filter.return_value.paginate.return_value = MagicMock(
                    items=[MagicMock() for _ in range(10)],
                    total=10000,
                    page=1,
                    per_page=10,
                    pages=1000
                )
                
                performance_benchmark.start()
                
                response = client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
                
                performance_benchmark.assert_faster_than(1.0)
                assert response.status_code == 200
    
    @pytest.mark.performance
    def test_complex_query_performance(self, client, auth_headers, performance_benchmark):
        """Test performance of complex database queries"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            response = client.get(
                '/api/articles/recommendations?primary_phase=DO&exclude_read=true&limit=10&algorithm=collaborative',
                headers=auth_headers
            )
            
            performance_benchmark.assert_faster_than(2.0)
            assert response.status_code == 200
    
    @pytest.mark.performance
    def test_aggregation_query_performance(self, client, auth_headers, performance_benchmark):
        """Test performance of aggregation queries"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            response = client.get('/api/articles/statistics', headers=auth_headers)
            
            performance_benchmark.assert_faster_than(1.5)
            assert response.status_code == 200

class TestCachePerformance:
    """Test caching performance and effectiveness"""
    
    @pytest.mark.performance
    def test_cached_search_performance(self, client, auth_headers, performance_benchmark):
        """Test search performance with caching"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # First request (cache miss)
            performance_benchmark.start()
            response1 = client.get(
                '/api/articles/search?query=cached&page=1&per_page=10',
                headers=auth_headers
            )
            first_request_time = performance_benchmark.stop()
            
            # Second request (cache hit)
            performance_benchmark.start()
            response2 = client.get(
                '/api/articles/search?query=cached&page=1&per_page=10',
                headers=auth_headers
            )
            second_request_time = performance_benchmark.stop()
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Cached request should be faster
            assert second_request_time < first_request_time
    
    @pytest.mark.performance
    def test_cache_invalidation_performance(self, client, auth_headers, performance_benchmark):
        """Test cache invalidation performance"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test cache invalidation after article update
            performance_benchmark.start()
            
            # Simulate article update that invalidates cache
            with patch('backend.routes.articles.invalidate_article_caches') as mock_invalidate:
                response = client.put(
                    '/api/articles/test-id/progress',
                    data='{"progress_percentage": 50}',
                    headers=auth_headers
                )
            
            performance_benchmark.assert_faster_than(1.0)
            assert response.status_code == 200

class TestMemoryPerformance:
    """Test memory usage and garbage collection"""
    
    @pytest.mark.performance
    def test_memory_usage_with_large_results(self, client, auth_headers):
        """Test memory usage with large result sets"""
        import psutil
        import os
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Make multiple requests with large result sets
            for _ in range(10):
                response = client.get(
                    '/api/articles/search?query=test&page=1&per_page=100',
                    headers=auth_headers
                )
                assert response.status_code == 200
            
            # Get final memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes
    
    @pytest.mark.performance
    def test_memory_leak_prevention(self, client, auth_headers):
        """Test that there are no memory leaks"""
        import psutil
        import os
        import gc
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Make many requests
            for _ in range(50):
                response = client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
                assert response.status_code == 200
            
            # Force garbage collection
            gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory should not increase significantly after GC
            assert memory_increase < 50 * 1024 * 1024  # 50MB in bytes

class TestNetworkPerformance:
    """Test network and I/O performance"""
    
    @pytest.mark.performance
    def test_response_size_optimization(self, client, auth_headers):
        """Test that response sizes are optimized"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get(
                '/api/articles/search?query=test&page=1&per_page=10',
                headers=auth_headers
            )
            
            # Response size should be reasonable
            response_size = len(response.data)
            assert response_size < 100 * 1024  # Less than 100KB
    
    @pytest.mark.performance
    def test_compression_effectiveness(self, client, auth_headers):
        """Test response compression effectiveness"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Request with compression
            headers_with_compression = auth_headers.copy()
            headers_with_compression['Accept-Encoding'] = 'gzip, deflate'
            
            response = client.get(
                '/api/articles/search?query=test&page=1&per_page=10',
                headers=headers_with_compression
            )
            
            # Check if compression is being used
            content_encoding = response.headers.get('Content-Encoding')
            if content_encoding:
                assert content_encoding in ['gzip', 'deflate']

class TestLoadTesting:
    """Test system behavior under load"""
    
    @pytest.mark.performance
    def test_sustained_load_performance(self, client, auth_headers, performance_benchmark):
        """Test performance under sustained load"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            # Make sustained requests for 30 seconds
            end_time = time.time() + 30
            request_count = 0
            
            while time.time() < end_time:
                response = client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
                assert response.status_code == 200
                request_count += 1
                time.sleep(0.1)  # 10 requests per second
            
            # Should handle sustained load
            assert request_count >= 250  # At least 250 requests in 30 seconds
            performance_benchmark.assert_faster_than(35.0)  # Total time should be reasonable
    
    @pytest.mark.performance
    def test_peak_load_handling(self, client, auth_headers, performance_benchmark):
        """Test handling of peak load"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            performance_benchmark.start()
            
            # Simulate peak load with many concurrent requests
            def make_request():
                return client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(make_request) for _ in range(100)]
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Should handle peak load gracefully
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= 90  # At least 90% success rate
            
            performance_benchmark.assert_faster_than(10.0)  # Should complete in reasonable time

class TestScalabilityTests:
    """Test system scalability"""
    
    @pytest.mark.performance
    def test_scalability_with_data_size(self, client, auth_headers, performance_benchmark):
        """Test how performance scales with data size"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test with different simulated data sizes
            data_sizes = [1000, 10000, 100000]
            
            for size in data_sizes:
                with patch('backend.routes.articles.Article') as mock_article:
                    mock_article.query.filter.return_value.paginate.return_value = MagicMock(
                        items=[MagicMock() for _ in range(10)],
                        total=size,
                        page=1,
                        per_page=10,
                        pages=size // 10
                    )
                    
                    performance_benchmark.start()
                    
                    response = client.get(
                        '/api/articles/search?query=test&page=1&per_page=10',
                        headers=auth_headers
                    )
                    
                    # Performance should scale reasonably with data size
                    max_time = min(3.0, 0.5 + (size / 50000))  # Linear scaling with reasonable bounds
                    performance_benchmark.assert_faster_than(max_time)
                    assert response.status_code == 200
    
    @pytest.mark.performance
    def test_scalability_with_concurrent_users(self, client, auth_headers, performance_benchmark):
        """Test how performance scales with concurrent users"""
        # Test with different numbers of concurrent users
        user_counts = [10, 50, 100]
        
        for user_count in user_counts:
            performance_benchmark.start()
            
            def make_request(user_id):
                headers = auth_headers.copy()
                with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
                    mock_get_user_id.return_value = f'user-{user_id}'
                    return client.get(
                        '/api/articles/search?query=test&page=1&per_page=10',
                        headers=headers
                    )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(make_request, i) for i in range(user_count)]
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Success rate should remain high
            success_count = sum(1 for r in responses if r.status_code == 200)
            success_rate = success_count / user_count
            assert success_rate >= 0.9  # At least 90% success rate
            
            # Performance should scale reasonably
            max_time = min(15.0, 2.0 + (user_count / 20))  # Linear scaling with reasonable bounds
            performance_benchmark.assert_faster_than(max_time)
