#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Splash Page Performance Tests
Comprehensive performance testing for meme loading, database operations, and optimization
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import time
import threading
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc
from unittest.mock import patch

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from meme_selector import MemeSelector
from backend.api.meme_endpoints import meme_api
from flask import Flask
from tests.meme_splash.fixtures.test_data import MemeTestData, DatabaseTestSetup, PerformanceTestData

class TestMemePerformance(unittest.TestCase):
    """Performance tests for meme splash page functionality"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with performance test data
        DatabaseTestSetup.create_test_database(self.test_db.name, include_performance_data=True)
        
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
        
        # Performance benchmarks
        self.benchmarks = PerformanceTestData.BENCHMARKS
    
    def tearDown(self):
        """Clean up performance test environment"""
        self.db_path_patcher.stop()
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_meme_selection_performance(self):
        """Test performance of meme selection algorithm"""
        user_id = 1
        num_selections = 100
        
        start_time = time.time()
        
        # Perform multiple meme selections
        memes = []
        for _ in range(num_selections):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
            memes.append(meme)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_selections
        
        # Performance assertions
        self.assertLess(total_time, 10.0, f"Total time {total_time:.2f}s should be under 10s for {num_selections} selections")
        self.assertLess(avg_time, self.benchmarks['meme_selection_time'], 
                       f"Average selection time {avg_time:.3f}s should be under {self.benchmarks['meme_selection_time']}s")
        
        print(f"✅ Meme Selection Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_selections} selections")
        print(f"   - Average time: {avg_time:.3f}s per selection")
        print(f"   - Selections per second: {num_selections / total_time:.1f}")
    
    def test_database_query_performance(self):
        """Test performance of database queries"""
        user_id = 1
        num_queries = 50
        
        # Test recently viewed memes query
        start_time = time.time()
        
        for _ in range(num_queries):
            recent_memes = self.selector._get_recently_viewed_memes(user_id, 30)
            self.assertIsInstance(recent_memes, list)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_queries
        
        self.assertLess(avg_time, self.benchmarks['database_query_time'],
                       f"Average query time {avg_time:.3f}s should be under {self.benchmarks['database_query_time']}s")
        
        print(f"✅ Database Query Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_queries} queries")
        print(f"   - Average time: {avg_time:.3f}s per query")
        print(f"   - Queries per second: {num_queries / total_time:.1f}")
    
    def test_api_endpoint_performance(self):
        """Test performance of API endpoints"""
        num_requests = 50
        
        # Test GET /api/user-meme
        start_time = time.time()
        
        for i in range(num_requests):
            response = self.client.get('/api/user-meme', headers={
                'X-User-ID': f'user{i}',
                'X-Session-ID': f'session{i}'
            })
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_requests
        
        self.assertLess(avg_time, self.benchmarks['api_response_time'],
                       f"Average API response time {avg_time:.3f}s should be under {self.benchmarks['api_response_time']}s")
        
        print(f"✅ API Endpoint Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_requests} requests")
        print(f"   - Average time: {avg_time:.3f}s per request")
        print(f"   - Requests per second: {num_requests / total_time:.1f}")
    
    def test_concurrent_user_performance(self):
        """Test performance with concurrent users"""
        num_users = 20
        requests_per_user = 5
        
        def user_workflow(user_id):
            """Simulate a user workflow"""
            results = []
            for _ in range(requests_per_user):
                start_time = time.time()
                
                # Get meme
                response = self.client.get('/api/user-meme', headers={
                    'X-User-ID': f'user{user_id}',
                    'X-Session-ID': f'session{user_id}'
                })
                
                if response.status_code == 200:
                    meme_data = response.get_json()
                    
                    # Track analytics
                    analytics_data = {
                        'meme_id': meme_data['id'],
                        'action': 'continue',
                        'user_id': f'user{user_id}',
                        'session_id': f'session{user_id}'
                    }
                    
                    response = self.client.post('/api/meme-analytics',
                                              json=analytics_data)
                
                end_time = time.time()
                results.append(end_time - start_time)
            
            return results
        
        # Run concurrent users
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_workflow, i) for i in range(num_users)]
            all_results = []
            
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        avg_time = statistics.mean(all_results)
        median_time = statistics.median(all_results)
        p95_time = statistics.quantiles(all_results, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(all_results, n=100)[98]  # 99th percentile
        
        # Performance assertions
        self.assertLess(avg_time, 1.0, f"Average response time {avg_time:.3f}s should be under 1s")
        self.assertLess(p95_time, 2.0, f"95th percentile {p95_time:.3f}s should be under 2s")
        self.assertLess(p99_time, 3.0, f"99th percentile {p99_time:.3f}s should be under 3s")
        
        print(f"✅ Concurrent User Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_users} users, {requests_per_user} requests each")
        print(f"   - Average response time: {avg_time:.3f}s")
        print(f"   - Median response time: {median_time:.3f}s")
        print(f"   - 95th percentile: {p95_time:.3f}s")
        print(f"   - 99th percentile: {p99_time:.3f}s")
        print(f"   - Total requests: {len(all_results)}")
        print(f"   - Requests per second: {len(all_results) / total_time:.1f}")
    
    def test_memory_usage_performance(self):
        """Test memory usage during operations"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations
        num_operations = 1000
        for i in range(num_operations):
            meme = self.selector.select_best_meme(i % 100 + 1)  # Cycle through users
            self.assertIsNotNone(meme)
            
            # Force garbage collection every 100 operations
            if i % 100 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory assertions
        self.assertLess(memory_increase, self.benchmarks['max_memory_increase_mb'],
                       f"Memory increase {memory_increase:.2f}MB should be under {self.benchmarks['max_memory_increase_mb']}MB")
        
        print(f"✅ Memory Usage Performance:")
        print(f"   - Initial memory: {initial_memory:.2f}MB")
        print(f"   - Final memory: {final_memory:.2f}MB")
        print(f"   - Memory increase: {memory_increase:.2f}MB")
        print(f"   - Operations performed: {num_operations}")
        print(f"   - Memory per operation: {memory_increase / num_operations * 1024:.2f}KB")
    
    def test_database_connection_performance(self):
        """Test database connection and query performance"""
        num_connections = 100
        
        start_time = time.time()
        
        for _ in range(num_connections):
            with sqlite3.connect(self.test_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memes WHERE is_active = 1")
                count = cursor.fetchone()[0]
                self.assertGreater(count, 0)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_connections
        
        self.assertLess(avg_time, 0.01, f"Average connection time {avg_time:.3f}s should be under 0.01s")
        
        print(f"✅ Database Connection Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_connections} connections")
        print(f"   - Average time: {avg_time:.3f}s per connection")
        print(f"   - Connections per second: {num_connections / total_time:.1f}")
    
    def test_analytics_tracking_performance(self):
        """Test performance of analytics tracking"""
        num_analytics = 200
        
        start_time = time.time()
        
        for i in range(num_analytics):
            analytics_data = {
                'meme_id': (i % 10) + 1,
                'action': 'continue',
                'user_id': f'user{i}',
                'session_id': f'session{i}'
            }
            
            response = self.client.post('/api/meme-analytics',
                                      json=analytics_data)
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_analytics
        
        self.assertLess(avg_time, 0.1, f"Average analytics time {avg_time:.3f}s should be under 0.1s")
        
        print(f"✅ Analytics Tracking Performance:")
        print(f"   - Total time: {total_time:.2f}s for {num_analytics} analytics")
        print(f"   - Average time: {avg_time:.3f}s per analytics")
        print(f"   - Analytics per second: {num_analytics / total_time:.1f}")
    
    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        # Create a larger dataset
        large_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        large_db.close()
        
        try:
            # Set up large database
            DatabaseTestSetup.create_test_database(large_db.name, include_performance_data=True)
            
            # Add more data
            with sqlite3.connect(large_db.name) as conn:
                cursor = conn.cursor()
                
                # Add more memes
                for i in range(1000, 2000):
                    cursor.execute("""
                        INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        f'https://example.com/large_meme_{i}.jpg',
                        'faith',
                        f'Large dataset meme {i}',
                        f'Alt text for large meme {i}',
                        1
                    ))
                
                conn.commit()
            
            # Test selector with large dataset
            large_selector = MemeSelector(large_db.name)
            
            start_time = time.time()
            
            # Select memes from large dataset
            for i in range(50):
                meme = large_selector.select_best_meme(i + 1)
                self.assertIsNotNone(meme)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 50
            
            self.assertLess(avg_time, 0.2, f"Average selection time {avg_time:.3f}s should be under 0.2s with large dataset")
            
            print(f"✅ Large Dataset Performance:")
            print(f"   - Total time: {total_time:.2f}s for 50 selections")
            print(f"   - Average time: {avg_time:.3f}s per selection")
            print(f"   - Dataset size: 2000+ memes")
            
        finally:
            if os.path.exists(large_db.name):
                os.unlink(large_db.name)
    
    def test_caching_performance(self):
        """Test performance impact of caching"""
        user_id = 1
        
        # First run (cold cache)
        start_time = time.time()
        
        for _ in range(10):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        cold_cache_time = time.time() - start_time
        
        # Second run (warm cache)
        start_time = time.time()
        
        for _ in range(10):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        warm_cache_time = time.time() - start_time
        
        # Cache should improve performance
        print(f"✅ Caching Performance:")
        print(f"   - Cold cache time: {cold_cache_time:.3f}s")
        print(f"   - Warm cache time: {warm_cache_time:.3f}s")
        print(f"   - Performance improvement: {((cold_cache_time - warm_cache_time) / cold_cache_time * 100):.1f}%")
    
    def test_stress_test(self):
        """Stress test with high load"""
        num_threads = 50
        requests_per_thread = 20
        
        def stress_workflow(thread_id):
            """Stress test workflow"""
            results = []
            for i in range(requests_per_thread):
                start_time = time.time()
                
                try:
                    # Get meme
                    response = self.client.get('/api/user-meme', headers={
                        'X-User-ID': f'stress_user_{thread_id}_{i}',
                        'X-Session-ID': f'stress_session_{thread_id}_{i}'
                    })
                    
                    if response.status_code == 200:
                        meme_data = response.get_json()
                        
                        # Track analytics
                        analytics_data = {
                            'meme_id': meme_data['id'],
                            'action': 'continue',
                            'user_id': f'stress_user_{thread_id}_{i}',
                            'session_id': f'stress_session_{thread_id}_{i}'
                        }
                        
                        response = self.client.post('/api/meme-analytics',
                                                  json=analytics_data)
                    
                    end_time = time.time()
                    results.append({
                        'success': True,
                        'time': end_time - start_time,
                        'status_code': response.status_code
                    })
                    
                except Exception as e:
                    end_time = time.time()
                    results.append({
                        'success': False,
                        'time': end_time - start_time,
                        'error': str(e)
                    })
            
            return results
        
        # Run stress test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_workflow, i) for i in range(num_threads)]
            all_results = []
            
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        success_rate = len(successful_requests) / len(all_results) * 100
        
        if successful_requests:
            avg_time = statistics.mean([r['time'] for r in successful_requests])
            max_time = max([r['time'] for r in successful_requests])
        else:
            avg_time = 0
            max_time = 0
        
        # Stress test assertions
        self.assertGreater(success_rate, 95, f"Success rate {success_rate:.1f}% should be over 95%")
        self.assertLess(avg_time, 2.0, f"Average response time {avg_time:.3f}s should be under 2s")
        self.assertLess(max_time, 10.0, f"Max response time {max_time:.3f}s should be under 10s")
        
        print(f"✅ Stress Test Results:")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Total requests: {len(all_results)}")
        print(f"   - Successful requests: {len(successful_requests)}")
        print(f"   - Failed requests: {len(failed_requests)}")
        print(f"   - Success rate: {success_rate:.1f}%")
        print(f"   - Average response time: {avg_time:.3f}s")
        print(f"   - Max response time: {max_time:.3f}s")
        print(f"   - Requests per second: {len(all_results) / total_time:.1f}")


class TestMemePerformanceBenchmarks(unittest.TestCase):
    """Benchmark tests to establish performance baselines"""
    
    def setUp(self):
        """Set up benchmark test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Set up database with benchmark data
        DatabaseTestSetup.create_test_database(self.test_db.name, include_performance_data=True)
        self.selector = MemeSelector(self.test_db.name)
    
    def tearDown(self):
        """Clean up benchmark test environment"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_benchmark_meme_selection(self):
        """Benchmark meme selection performance"""
        user_id = 1
        num_selections = 1000
        
        start_time = time.time()
        
        for _ in range(num_selections):
            meme = self.selector.select_best_meme(user_id)
            self.assertIsNotNone(meme)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_selections
        
        print(f"📊 Meme Selection Benchmark:")
        print(f"   - Selections: {num_selections}")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Average time: {avg_time:.3f}s")
        print(f"   - Selections per second: {num_selections / total_time:.1f}")
        
        # Benchmark thresholds
        self.assertLess(avg_time, 0.05, "Average selection time should be under 50ms")
        self.assertGreater(num_selections / total_time, 100, "Should handle over 100 selections per second")
    
    def test_benchmark_database_operations(self):
        """Benchmark database operations"""
        num_operations = 500
        
        start_time = time.time()
        
        for i in range(num_operations):
            with sqlite3.connect(self.test_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memes WHERE is_active = 1 LIMIT 1")
                result = cursor.fetchone()
                self.assertIsNotNone(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_operations
        
        print(f"📊 Database Operations Benchmark:")
        print(f"   - Operations: {num_operations}")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Average time: {avg_time:.3f}s")
        print(f"   - Operations per second: {num_operations / total_time:.1f}")
        
        # Benchmark thresholds
        self.assertLess(avg_time, 0.01, "Average database operation should be under 10ms")
        self.assertGreater(num_operations / total_time, 500, "Should handle over 500 operations per second")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add performance tests
    test_suite.addTest(unittest.makeSuite(TestMemePerformance))
    test_suite.addTest(unittest.makeSuite(TestMemePerformanceBenchmarks))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Performance Tests Summary:")
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
