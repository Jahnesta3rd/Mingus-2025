"""
Performance tests for job security features
Tests load, stress, and performance benchmarks
"""

import unittest
import time
import threading
import concurrent.futures
import statistics
import psutil
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend.ml.job_security_predictor import JobSecurityPredictor
from backend.integrations.financial_planning_integration import FinancialPlanningIntegration
from backend.integrations.goal_setting_integration import GoalSettingIntegration
from backend.integrations.recommendations_integration import RecommendationsIntegration


class TestLoadPerformance(unittest.TestCase):
    """Test load and performance characteristics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = JobSecurityPredictor()
        self.financial_integration = FinancialPlanningIntegration()
        self.goal_integration = GoalSettingIntegration()
        self.recommendations_integration = RecommendationsIntegration()
        
        # Create test data
        self.test_user_data = self._create_test_user_data()
        self.test_company_data = self._create_test_company_data()
        self.test_market_data = self._create_test_market_data()
        
        # Performance thresholds
        self.single_prediction_threshold = 1.0  # seconds
        self.batch_prediction_threshold = 5.0   # seconds for 10 predictions
        self.memory_threshold = 100 * 1024 * 1024  # 100MB
        self.cpu_threshold = 80  # 80% CPU usage
    
    def _create_test_user_data(self):
        """Create test user data"""
        return {
            'id': 1,
            'age': 32,
            'years_experience': 8,
            'education_level': 'bachelor',
            'skills': ['python', 'data_analysis', 'project_management'],
            'current_salary': 85000,
            'tenure_months': 36,
            'performance_rating': 4.5,
            'department': 'engineering',
            'role_level': 'senior'
        }
    
    def _create_test_company_data(self):
        """Create test company data"""
        return {
            'company_id': 'COMP001',
            'company_name': 'TechCorp',
            'industry': 'technology',
            'size': 'medium',
            'location': 'San Francisco, CA',
            'financial_health': 'strong',
            'revenue_growth': 0.25,
            'profit_margin': 0.18,
            'employee_count': 750
        }
    
    def _create_test_market_data(self):
        """Create test market data"""
        return {
            'industry_growth_rate': 0.12,
            'unemployment_rate': 0.035,
            'job_market_health': 'strong',
            'skill_demand': {
                'python': 'very_high',
                'data_analysis': 'very_high',
                'project_management': 'high'
            }
        }
    
    def test_single_prediction_performance(self):
        """Test single prediction performance"""
        # Measure single prediction time
        start_time = time.time()
        
        result = self.predictor.predict_comprehensive(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        execution_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(execution_time, self.single_prediction_threshold)
        self.assertIsNotNone(result)
        self.assertIn('overall_risk_score', result)
        
        print(f"Single prediction time: {execution_time:.3f} seconds")
    
    def test_batch_prediction_performance(self):
        """Test batch prediction performance"""
        batch_size = 10
        batch_data = []
        
        # Create batch data
        for i in range(batch_size):
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            user_data['current_salary'] = 75000 + (i * 5000)
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            batch_data.append((user_data, company_data, self.test_market_data))
        
        # Measure batch processing time
        start_time = time.time()
        
        results = []
        for user_data, company_data, market_data in batch_data:
            result = self.predictor.predict_comprehensive(user_data, company_data, market_data)
            results.append(result)
        
        execution_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(execution_time, self.batch_prediction_threshold)
        self.assertEqual(len(results), batch_size)
        
        print(f"Batch prediction time ({batch_size} predictions): {execution_time:.3f} seconds")
        print(f"Average time per prediction: {execution_time/batch_size:.3f} seconds")
    
    def test_concurrent_prediction_performance(self):
        """Test concurrent prediction performance"""
        num_threads = 5
        predictions_per_thread = 2
        total_predictions = num_threads * predictions_per_thread
        
        def make_predictions(thread_id):
            """Make predictions for a thread"""
            results = []
            for i in range(predictions_per_thread):
                user_data = self.test_user_data.copy()
                user_data['id'] = thread_id * 100 + i
                user_data['current_salary'] = 75000 + (thread_id * 1000) + (i * 500)
                
                company_data = self.test_company_data.copy()
                company_data['company_id'] = f'COMP{thread_id:02d}{i:02d}'
                
                result = self.predictor.predict_comprehensive(
                    user_data, company_data, self.test_market_data
                )
                results.append(result)
            return results
        
        # Measure concurrent processing time
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_predictions, i) for i in range(num_threads)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        execution_time = time.time() - start_time
        
        # Verify performance
        self.assertEqual(len(all_results), total_predictions)
        self.assertLess(execution_time, self.batch_prediction_threshold * 2)  # Allow some overhead
        
        print(f"Concurrent prediction time ({total_predictions} predictions, {num_threads} threads): {execution_time:.3f} seconds")
    
    def test_memory_usage_performance(self):
        """Test memory usage performance"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run multiple predictions to test memory usage
        for i in range(20):
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            result = self.predictor.predict_comprehensive(
                user_data, company_data, self.test_market_data
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verify memory usage
        self.assertLess(memory_increase, self.memory_threshold)
        
        print(f"Memory increase after 20 predictions: {memory_increase / (1024*1024):.2f} MB")
    
    def test_cpu_usage_performance(self):
        """Test CPU usage performance"""
        # Monitor CPU usage during predictions
        cpu_percentages = []
        
        for i in range(10):
            # Get CPU usage before prediction
            cpu_before = psutil.cpu_percent(interval=0.1)
            
            # Make prediction
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            result = self.predictor.predict_comprehensive(
                user_data, company_data, self.test_market_data
            )
            
            # Get CPU usage after prediction
            cpu_after = psutil.cpu_percent(interval=0.1)
            cpu_percentages.append(max(cpu_before, cpu_after))
        
        # Verify CPU usage
        max_cpu = max(cpu_percentages)
        avg_cpu = statistics.mean(cpu_percentages)
        
        self.assertLess(max_cpu, self.cpu_threshold)
        
        print(f"CPU usage - Max: {max_cpu:.1f}%, Average: {avg_cpu:.1f}%")
    
    def test_integration_performance(self):
        """Test performance of integration modules"""
        # Test financial planning integration
        start_time = time.time()
        
        financial_plan = self.financial_integration.get_job_security_adjusted_financial_plan(
            1, self.test_user_data, self.test_company_data
        )
        
        financial_time = time.time() - start_time
        
        # Test goal setting integration
        start_time = time.time()
        
        goals = self.goal_integration.create_job_security_aware_goals(
            1, self.test_user_data, self.test_company_data
        )
        
        goals_time = time.time() - start_time
        
        # Test recommendations integration
        start_time = time.time()
        
        recommendations = self.recommendations_integration.get_personalized_recommendations(
            1, self.test_user_data, self.test_company_data
        )
        
        recommendations_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(financial_time, 2.0)  # 2 seconds threshold
        self.assertLess(goals_time, 2.0)
        self.assertLess(recommendations_time, 2.0)
        
        print(f"Integration performance:")
        print(f"  Financial planning: {financial_time:.3f} seconds")
        print(f"  Goal setting: {goals_time:.3f} seconds")
        print(f"  Recommendations: {recommendations_time:.3f} seconds")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        # This would test actual database operations
        # For now, test with mock data
        
        # Simulate database queries
        query_times = []
        
        for i in range(10):
            start_time = time.time()
            
            # Simulate user lookup
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            
            # Simulate company lookup
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            # Simulate market data lookup
            market_data = self.test_market_data.copy()
            
            query_time = time.time() - start_time
            query_times.append(query_time)
        
        # Verify query performance
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        self.assertLess(avg_query_time, 0.1)  # 100ms average
        self.assertLess(max_query_time, 0.5)  # 500ms max
        
        print(f"Database query performance:")
        print(f"  Average query time: {avg_query_time*1000:.2f} ms")
        print(f"  Max query time: {max_query_time*1000:.2f} ms")
    
    def test_api_response_time_performance(self):
        """Test API response time performance"""
        # This would test actual API endpoints
        # For now, test with mock API calls
        
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            
            # Simulate API call
            result = self.predictor.predict_comprehensive(
                self.test_user_data,
                self.test_company_data,
                self.test_market_data
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Verify API performance
        self.assertLess(avg_response_time, 1.0)  # 1 second average
        self.assertLess(p95_response_time, 1.5)  # 1.5 seconds 95th percentile
        self.assertLess(p99_response_time, 2.0)  # 2 seconds 99th percentile
        
        print(f"API response time performance:")
        print(f"  Average: {avg_response_time*1000:.2f} ms")
        print(f"  95th percentile: {p95_response_time*1000:.2f} ms")
        print(f"  99th percentile: {p99_response_time*1000:.2f} ms")
    
    def test_stress_test_performance(self):
        """Test stress test performance"""
        # Run many predictions under stress
        num_predictions = 50
        start_time = time.time()
        
        results = []
        for i in range(num_predictions):
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            user_data['current_salary'] = 75000 + (i * 1000)
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            try:
                result = self.predictor.predict_comprehensive(
                    user_data, company_data, self.test_market_data
                )
                results.append(result)
            except Exception as e:
                print(f"Error in prediction {i}: {e}")
        
        execution_time = time.time() - start_time
        
        # Verify stress test results
        success_rate = len(results) / num_predictions
        self.assertGreater(success_rate, 0.95)  # 95% success rate
        self.assertLess(execution_time, 30.0)  # 30 seconds for 50 predictions
        
        print(f"Stress test results:")
        print(f"  Success rate: {success_rate*100:.1f}%")
        print(f"  Total time: {execution_time:.3f} seconds")
        print(f"  Average time per prediction: {execution_time/len(results):.3f} seconds")
    
    def test_scalability_performance(self):
        """Test scalability performance"""
        # Test with different data sizes
        data_sizes = [1, 5, 10, 20, 50]
        execution_times = []
        
        for size in data_sizes:
            start_time = time.time()
            
            for i in range(size):
                user_data = self.test_user_data.copy()
                user_data['id'] = i + 1
                
                company_data = self.test_company_data.copy()
                company_data['company_id'] = f'COMP{i:03d}'
                
                result = self.predictor.predict_comprehensive(
                    user_data, company_data, self.test_market_data
                )
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
        
        # Verify scalability (should be roughly linear)
        for i in range(1, len(data_sizes)):
            time_ratio = execution_times[i] / execution_times[i-1]
            data_ratio = data_sizes[i] / data_sizes[i-1]
            
            # Time increase should be roughly proportional to data increase
            # Allow some overhead (within 50% of expected ratio)
            expected_ratio = data_ratio
            tolerance = 0.5
            
            self.assertLess(time_ratio, expected_ratio * (1 + tolerance))
        
        print(f"Scalability test results:")
        for i, size in enumerate(data_sizes):
            print(f"  {size} predictions: {execution_times[i]:.3f} seconds")


if __name__ == '__main__':
    unittest.main() 