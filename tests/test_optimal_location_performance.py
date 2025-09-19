#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location Performance Tests
Performance tests for the Optimal Location feature following MINGUS testing patterns
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
import time
import threading
import concurrent.futures
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from backend.api.optimal_location_api import optimal_location_api
from backend.models.database import db
from backend.models.user_models import User
from backend.models.housing_models import (
    HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache
)
from backend.services.optimal_location_service import OptimalLocationService

class TestOptimalLocationPerformance(unittest.TestCase):
    """Performance tests for the Optimal Location feature"""
    
    def setUp(self):
        """Set up performance test environment"""
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Register blueprint
        self.app.register_blueprint(optimal_location_api)
        
        # Initialize database
        db.init_app(self.app)
        
        with self.app.app_context():
            db.create_all()
            self._setup_performance_test_data()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up performance test database"""
        with self.app.app_context():
            db.drop_all()
    
    def _setup_performance_test_data(self):
        """Set up test data for performance testing"""
        # Create test users
        users = [
            User(id=i, email=f'user{i}@example.com', first_name=f'User{i}', last_name='Test', tier='mid_tier')
            for i in range(1, 101)  # 100 users
        ]
        
        db.session.add_all(users)
        db.session.commit()
        
        # Create test housing scenarios
        scenarios = []
        for i in range(1, 1001):  # 1000 scenarios
            user_id = (i % 100) + 1
            scenarios.append(HousingScenario(
                user_id=user_id,
                scenario_name=f'Scenario {i}',
                housing_data={
                    'address': f'{i} Test St',
                    'city': 'New York',
                    'state': 'NY',
                    'zip_code': '10001',
                    'rent': 2000 + (i % 1000),
                    'bedrooms': (i % 3) + 1,
                    'bathrooms': (i % 2) + 1,
                    'property_type': 'apartment'
                },
                commute_data={
                    'estimated_commute_time': 20 + (i % 30),
                    'estimated_distance': 5.0 + (i % 20),
                    'commute_cost_per_month': 150 + (i % 200)
                },
                financial_impact={
                    'monthly_rent': 2000 + (i % 1000),
                    'affordability_score': 60 + (i % 40),
                    'total_monthly_housing_cost': 2200 + (i % 1000),
                    'rent_to_income_ratio': 0.2 + (i % 30) / 100
                },
                career_data={
                    'nearby_job_opportunities': 10 + (i % 40),
                    'average_salary_in_area': 60000 + (i % 40000),
                    'career_growth_potential': 'High' if i % 2 == 0 else 'Medium'
                }
            ))
        
        db.session.add_all(scenarios)
        db.session.commit()
    
    def _get_auth_headers(self, user_id=1):
        """Get authentication headers for testing"""
        return {
            'Authorization': f'Bearer test_token_{user_id}',
            'X-CSRF-Token': 'test_csrf_token_12345',
            'Content-Type': 'application/json'
        }
    
    def test_api_response_time_benchmarks(self):
        """Test API response time benchmarks"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Test housing search response time
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': [
                                    {
                                        'id': f'listing{i}',
                                        'address': f'{i} Test St',
                                        'city': 'New York',
                                        'state': 'NY',
                                        'zip_code': '10001',
                                        'rent': 2000 + i,
                                        'bedrooms': 2,
                                        'bathrooms': 1,
                                        'property_type': 'apartment'
                                    }
                                    for i in range(20)  # 20 listings
                                ]
                            }
                            
                            search_data = {
                                'max_rent': 3000,
                                'bedrooms': 2,
                                'commute_time': 30,
                                'zip_code': '10001'
                            }
                            
                            # Measure response time
                            start_time = time.time()
                            
                            response = self.client.post(
                                '/api/housing/search',
                                data=json.dumps(search_data),
                                headers=self._get_auth_headers()
                            )
                            
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            # Response should be fast (less than 500ms)
                            self.assertLess(response_time, 0.5)
                            self.assertEqual(response.status_code, 200)
                            
                            print(f"Housing search response time: {response_time:.3f}s")
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Test retrieving scenarios with large dataset
                start_time = time.time()
                
                response = self.client.get(
                    '/api/housing/scenarios/1',
                    headers=self._get_auth_headers()
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Response should be fast even with large dataset (less than 1 second)
                self.assertLess(response_time, 1.0)
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertIn('scenarios', data)
                self.assertIn('pagination', data)
                
                print(f"Large dataset retrieval time: {response_time:.3f}s")
                print(f"Retrieved {len(data['scenarios'])} scenarios")
    
    def test_concurrent_user_performance(self):
        """Test performance with concurrent users"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': []
                            }
                            
                            search_data = {
                                'max_rent': 3000,
                                'bedrooms': 2,
                                'commute_time': 30,
                                'zip_code': '10001'
                            }
                            
                            def make_request():
                                return self.client.post(
                                    '/api/housing/search',
                                    data=json.dumps(search_data),
                                    headers=self._get_auth_headers()
                                )
                            
                            # Test with 50 concurrent users
                            num_concurrent_users = 50
                            start_time = time.time()
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                                futures = [executor.submit(make_request) for _ in range(num_concurrent_users)]
                                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
                            
                            end_time = time.time()
                            total_time = end_time - start_time
                            
                            # All requests should succeed
                            for response in responses:
                                self.assertEqual(response.status_code, 200)
                            
                            # Should handle concurrent users efficiently
                            avg_response_time = total_time / num_concurrent_users
                            self.assertLess(avg_response_time, 1.0)
                            
                            print(f"Concurrent users: {num_concurrent_users}")
                            print(f"Total time: {total_time:.3f}s")
                            print(f"Average response time: {avg_response_time:.3f}s")
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization"""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Perform multiple operations
                for i in range(100):
                    response = self.client.get(
                        '/api/housing/scenarios/1',
                        headers=self._get_auth_headers()
                    )
                    self.assertEqual(response.status_code, 200)
                    
                    # Force garbage collection every 10 iterations
                    if i % 10 == 0:
                        gc.collect()
                
                # Get final memory usage
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                # Memory increase should be reasonable (less than 50MB)
                self.assertLess(memory_increase, 50)
                
                print(f"Initial memory: {initial_memory:.2f} MB")
                print(f"Final memory: {final_memory:.2f} MB")
                print(f"Memory increase: {memory_increase:.2f} MB")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Test different query patterns
                query_tests = [
                    {
                        'name': 'Get all scenarios',
                        'endpoint': '/api/housing/scenarios/1',
                        'expected_time': 0.5
                    },
                    {
                        'name': 'Get scenarios with pagination',
                        'endpoint': '/api/housing/scenarios/1?page=1&per_page=10',
                        'expected_time': 0.3
                    },
                    {
                        'name': 'Get scenarios with sorting',
                        'endpoint': '/api/housing/scenarios/1?sort_by=created_at&sort_order=desc',
                        'expected_time': 0.4
                    }
                ]
                
                for test in query_tests:
                    start_time = time.time()
                    
                    response = self.client.get(
                        test['endpoint'],
                        headers=self._get_auth_headers()
                    )
                    
                    end_time = time.time()
                    query_time = end_time - start_time
                    
                    self.assertEqual(response.status_code, 200)
                    self.assertLess(query_time, test['expected_time'])
                    
                    print(f"{test['name']}: {query_time:.3f}s (expected < {test['expected_time']}s)")
    
    def test_external_api_performance(self):
        """Test external API performance"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            # Mock slow external API response
                            def slow_api_response():
                                time.sleep(0.1)  # Simulate 100ms API delay
                                return {
                                    'success': True,
                                    'listings': []
                                }
                            
                            mock_external.get_rental_listings.side_effect = lambda *args, **kwargs: slow_api_response()
                            
                            search_data = {
                                'max_rent': 3000,
                                'bedrooms': 2,
                                'commute_time': 30,
                                'zip_code': '10001'
                            }
                            
                            start_time = time.time()
                            
                            response = self.client.post(
                                '/api/housing/search',
                                data=json.dumps(search_data),
                                headers=self._get_auth_headers()
                            )
                            
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            # Response should still be reasonable even with slow external API
                            self.assertLess(response_time, 1.0)
                            self.assertEqual(response.status_code, 200)
                            
                            print(f"External API response time: {response_time:.3f}s")
    
    def test_caching_performance(self):
        """Test caching performance"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Test commute cost calculation with caching
                commute_data = {
                    'origin_zip': '10001',
                    'destination_zip': '10005',
                    'vehicle_id': 1
                }
                
                with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                    mock_external.calculate_route_distance.return_value = {
                        'success': True,
                        'distance_miles': 15.5,
                        'drive_time_minutes': 30,
                        'traffic_factor': 1.2
                    }
                    
                    with patch('backend.api.optimal_location_api.vehicle_analytics_service') as mock_vehicle:
                        mock_vehicle.calculate_commute_costs.return_value = {
                            'monthly_fuel_cost': 120.0,
                            'total_monthly_cost': 245.0
                        }
                        
                        # First request (should be slower due to external API call)
                        start_time = time.time()
                        
                        response1 = self.client.post(
                            '/api/housing/commute-cost',
                            data=json.dumps(commute_data),
                            headers=self._get_auth_headers()
                        )
                        
                        end_time = time.time()
                        first_request_time = end_time - start_time
                        
                        # Second request (should be faster due to caching)
                        start_time = time.time()
                        
                        response2 = self.client.post(
                            '/api/housing/commute-cost',
                            data=json.dumps(commute_data),
                            headers=self._get_auth_headers()
                        )
                        
                        end_time = time.time()
                        second_request_time = end_time - start_time
                        
                        # Both requests should succeed
                        self.assertEqual(response1.status_code, 200)
                        self.assertEqual(response2.status_code, 200)
                        
                        # Second request should be faster (cached)
                        self.assertLess(second_request_time, first_request_time)
                        
                        print(f"First request time: {first_request_time:.3f}s")
                        print(f"Second request time: {second_request_time:.3f}s")
                        print(f"Cache speedup: {first_request_time / second_request_time:.2f}x")
    
    def test_stress_testing(self):
        """Test system under stress"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': []
                            }
                            
                            search_data = {
                                'max_rent': 3000,
                                'bedrooms': 2,
                                'commute_time': 30,
                                'zip_code': '10001'
                            }
                            
                            # Stress test with many rapid requests
                            num_requests = 1000
                            start_time = time.time()
                            
                            def make_request():
                                return self.client.post(
                                    '/api/housing/search',
                                    data=json.dumps(search_data),
                                    headers=self._get_auth_headers()
                                )
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                                futures = [executor.submit(make_request) for _ in range(num_requests)]
                                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
                            
                            end_time = time.time()
                            total_time = end_time - start_time
                            
                            # Count successful responses
                            successful_responses = sum(1 for response in responses if response.status_code == 200)
                            success_rate = successful_responses / num_requests * 100
                            
                            # Should maintain high success rate under stress
                            self.assertGreater(success_rate, 95)
                            
                            print(f"Stress test: {num_requests} requests")
                            print(f"Total time: {total_time:.3f}s")
                            print(f"Success rate: {success_rate:.1f}%")
                            print(f"Requests per second: {num_requests / total_time:.2f}")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks"""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Perform many operations
                for iteration in range(10):
                    # Get scenarios
                    response = self.client.get(
                        '/api/housing/scenarios/1',
                        headers=self._get_auth_headers()
                    )
                    self.assertEqual(response.status_code, 200)
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Check memory usage every 2 iterations
                    if iteration % 2 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_increase = current_memory - initial_memory
                        
                        # Memory increase should be reasonable
                        self.assertLess(memory_increase, 100)  # Less than 100MB increase
                        
                        print(f"Iteration {iteration}: Memory increase: {memory_increase:.2f} MB")
    
    def test_database_connection_pool_performance(self):
        """Test database connection pool performance"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Test concurrent database operations
                def get_scenarios():
                    return self.client.get(
                        '/api/housing/scenarios/1',
                        headers=self._get_auth_headers()
                    )
                
                # Test with multiple concurrent database operations
                num_concurrent = 50
                start_time = time.time()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                    futures = [executor.submit(get_scenarios) for _ in range(num_concurrent)]
                    responses = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # All requests should succeed
                for response in responses:
                    self.assertEqual(response.status_code, 200)
                
                # Should handle concurrent database operations efficiently
                avg_response_time = total_time / num_concurrent
                self.assertLess(avg_response_time, 1.0)
                
                print(f"Database connection pool test: {num_concurrent} concurrent operations")
                print(f"Total time: {total_time:.3f}s")
                print(f"Average response time: {avg_response_time:.3f}s")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add performance tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Performance Tests Summary")
    print(f"{'='*50}")
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
