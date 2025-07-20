"""
Performance Tests for Income Comparison Feature
Tests performance and scalability of comparison calculations
"""

import unittest
import sys
import os
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.data.income_data_manager import IncomeDataManager
from backend.routes.income_analysis import IncomeComparator

class TestIncomeComparisonPerformance(unittest.TestCase):
    """Performance tests for income comparison feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.income_manager = IncomeDataManager()
        self.comparator = IncomeComparator(self.income_manager)
        
        # Test user profiles for performance testing
        self.test_profiles = [
            {'income': 45000, 'race': 'african_american', 'age': 25, 'education': 'high_school', 'location': 'Atlanta'},
            {'income': 55000, 'race': 'african_american', 'age': 28, 'education': 'bachelors', 'location': 'Houston'},
            {'income': 65000, 'race': 'african_american', 'age': 32, 'education': 'bachelors', 'location': 'Washington DC'},
            {'income': 75000, 'race': 'african_american', 'age': 35, 'education': 'masters', 'location': 'Dallas'},
            {'income': 85000, 'race': 'african_american', 'age': 38, 'education': 'masters', 'location': 'New York City'},
            {'income': 95000, 'race': 'african_american', 'age': 40, 'education': 'masters', 'location': 'Chicago'},
            {'income': 105000, 'race': 'african_american', 'age': 42, 'education': 'masters', 'location': 'Philadelphia'},
            {'income': 115000, 'race': 'african_american', 'age': 45, 'education': 'masters', 'location': 'Charlotte'},
            {'income': 125000, 'race': 'african_american', 'age': 48, 'education': 'masters', 'location': 'Miami'},
            {'income': 135000, 'race': 'african_american', 'age': 50, 'education': 'masters', 'location': 'Baltimore'},
        ]
    
    def test_single_comparison_performance(self):
        """Test performance of single comparison calculation"""
        user = self.test_profiles[4]  # Mid-range profile
        
        # Warm up
        for _ in range(3):
            self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
        
        # Test single comparison performance
        start_time = time.time()
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        single_time = time.time() - start_time
        
        # Should complete within 50ms for web application
        self.assertLess(single_time, 0.05, f"Single comparison took {single_time:.3f}s, should be < 0.05s")
        
        # Verify result is complete
        self.assertIsNotNone(result)
        self.assertIn('national', result)
        self.assertIn('age_group', result)
        self.assertIn('education_level', result)
        self.assertIn('location', result)
        self.assertIn('summary', result)
    
    def test_multiple_comparisons_performance(self):
        """Test performance of multiple sequential comparisons"""
        start_time = time.time()
        
        results = []
        for user in self.test_profiles:
            result = self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
            results.append(result)
        
        total_time = time.time() - start_time
        avg_time = total_time / len(self.test_profiles)
        
        # Should average less than 30ms per comparison
        self.assertLess(avg_time, 0.03, f"Average time per comparison: {avg_time:.3f}s, should be < 0.03s")
        
        # Total time should be reasonable
        self.assertLess(total_time, 0.5, f"Total time for {len(self.test_profiles)} comparisons: {total_time:.3f}s")
        
        # Verify all results are complete
        for i, result in enumerate(results):
            self.assertIsNotNone(result, f"Result {i} is None")
            self.assertIn('national', result, f"Result {i} missing national comparison")
    
    def test_concurrent_comparisons_performance(self):
        """Test performance under concurrent load"""
        def run_comparison(user):
            return self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
        
        # Test with different thread counts
        thread_counts = [1, 2, 4, 8]
        
        for thread_count in thread_counts:
            with self.subTest(threads=thread_count):
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = [executor.submit(run_comparison, user) for user in self.test_profiles]
                    results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                avg_time = total_time / len(self.test_profiles)
                
                # Should handle concurrent requests efficiently
                self.assertLess(avg_time, 0.05, 
                              f"Average time with {thread_count} threads: {avg_time:.3f}s")
                
                # Verify all results are complete
                for i, result in enumerate(results):
                    self.assertIsNotNone(result, f"Concurrent result {i} is None")
                    self.assertIn('national', result, f"Concurrent result {i} missing national comparison")
    
    def test_data_manager_performance(self):
        """Test performance of data manager operations"""
        # Test data loading performance
        start_time = time.time()
        data_manager = IncomeDataManager()
        load_time = time.time() - start_time
        
        # Should load quickly
        self.assertLess(load_time, 0.1, f"Data manager load time: {load_time:.3f}s")
        
        # Test data retrieval performance
        start_time = time.time()
        for _ in range(100):
            data_manager.get_income_data('african_american', location='Atlanta')
        retrieval_time = time.time() - start_time
        avg_retrieval_time = retrieval_time / 100
        
        # Should retrieve data quickly
        self.assertLess(avg_retrieval_time, 0.001, 
                       f"Average data retrieval time: {avg_retrieval_time:.6f}s")
        
        # Test quality validation performance
        start_time = time.time()
        quality_report = data_manager.validate_data_quality()
        validation_time = time.time() - start_time
        
        # Should validate quickly
        self.assertLess(validation_time, 0.1, f"Quality validation time: {validation_time:.3f}s")
        self.assertIsNotNone(quality_report)
    
    def test_memory_usage_performance(self):
        """Test memory usage under load"""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run many comparisons
        results = []
        for _ in range(100):
            user = self.test_profiles[4]  # Mid-range profile
            result = self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
            results.append(result)
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        self.assertLess(memory_increase, 50, 
                       f"Memory increase: {memory_increase:.1f}MB, should be < 50MB")
        
        # Verify results are still valid
        for result in results:
            self.assertIsNotNone(result)
            self.assertIn('national', result)
    
    def test_web_application_scenarios(self):
        """Test performance for typical web application scenarios"""
        # Scenario 1: User submits form
        def simulate_form_submission():
            user = self.test_profiles[2]
            start_time = time.time()
            
            # Simulate form processing
            result = self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
            
            processing_time = time.time() - start_time
            return processing_time, result
        
        # Test multiple form submissions
        submission_times = []
        for _ in range(10):
            processing_time, result = simulate_form_submission()
            submission_times.append(processing_time)
            
            # Verify result is complete
            self.assertIsNotNone(result)
            self.assertIn('national', result)
            self.assertIn('summary', result)
        
        # Average processing time should be fast
        avg_processing_time = sum(submission_times) / len(submission_times)
        self.assertLess(avg_processing_time, 0.05, 
                       f"Average form processing time: {avg_processing_time:.3f}s")
        
        # Max processing time should be reasonable
        max_processing_time = max(submission_times)
        self.assertLess(max_processing_time, 0.1, 
                       f"Max form processing time: {max_processing_time:.3f}s")
    
    def test_edge_case_performance(self):
        """Test performance with edge cases"""
        edge_cases = [
            {'income': 25000, 'race': 'african_american', 'age': 25, 'education': 'high_school', 'location': 'Atlanta'},
            {'income': 250000, 'race': 'african_american', 'age': 45, 'education': 'masters', 'location': 'New York City'},
            {'income': 60000, 'race': 'invalid_race', 'age': 30, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 60000, 'race': 'african_american', 'age': 30, 'education': 'bachelors', 'location': 'invalid_location'},
        ]
        
        for i, edge_case in enumerate(edge_cases):
            with self.subTest(edge_case=i):
                start_time = time.time()
                
                try:
                    result = self.comparator.comprehensive_comparison(
                        edge_case['income'], edge_case['race'], edge_case['age'],
                        edge_case['education'], edge_case['location']
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # Should handle edge cases quickly
                    self.assertLess(processing_time, 0.05, 
                                  f"Edge case {i} processing time: {processing_time:.3f}s")
                    
                    # Should return some result
                    self.assertIsNotNone(result)
                    self.assertIn('national', result)
                    
                except Exception as e:
                    # Should not crash, but may log errors
                    self.fail(f"Edge case {i} caused unexpected exception: {str(e)}")
    
    def test_caching_performance(self):
        """Test performance impact of caching"""
        user = self.test_profiles[3]
        
        # First call (no cache)
        start_time = time.time()
        result1 = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        first_call_time = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        result2 = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        second_call_time = time.time() - start_time
        
        # Second call should be faster (if caching is working)
        self.assertLessEqual(second_call_time, first_call_time * 1.5, 
                           f"Second call should be faster: {second_call_time:.3f}s vs {first_call_time:.3f}s")
        
        # Results should be identical
        self.assertEqual(result1['national']['median_income'], result2['national']['median_income'])
        self.assertEqual(result1['national']['percentile_rank'], result2['national']['percentile_rank'])
    
    def test_scalability_performance(self):
        """Test scalability with increasing load"""
        # Test with different numbers of concurrent users
        user_counts = [1, 5, 10, 20, 50]
        
        for user_count in user_counts:
            with self.subTest(users=user_count):
                start_time = time.time()
                
                # Simulate concurrent users
                with ThreadPoolExecutor(max_workers=min(user_count, 10)) as executor:
                    futures = []
                    for _ in range(user_count):
                        user = self.test_profiles[4]  # Mid-range profile
                        future = executor.submit(
                            self.comparator.comprehensive_comparison,
                            user['income'], user['race'], user['age'],
                            user['education'], user['location']
                        )
                        futures.append(future)
                    
                    # Wait for all to complete
                    results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                avg_time = total_time / user_count
                
                # Performance should degrade gracefully
                if user_count <= 10:
                    self.assertLess(avg_time, 0.05, 
                                  f"Average time with {user_count} users: {avg_time:.3f}s")
                else:
                    self.assertLess(avg_time, 0.1, 
                                  f"Average time with {user_count} users: {avg_time:.3f}s")
                
                # All results should be complete
                for i, result in enumerate(results):
                    self.assertIsNotNone(result, f"Result {i} is None")
                    self.assertIn('national', result, f"Result {i} missing national comparison")
    
    def test_data_quality_performance(self):
        """Test performance of data quality validation"""
        # Test quality validation performance
        start_time = time.time()
        quality_report = self.income_manager.validate_data_quality()
        validation_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(validation_time, 0.1, f"Quality validation time: {validation_time:.3f}s")
        
        # Should return comprehensive report
        self.assertIsNotNone(quality_report)
        self.assertIn('overall_quality', quality_report)
        self.assertIn('issues', quality_report)
        self.assertIn('recommendations', quality_report)
        
        # Test multiple validations
        validation_times = []
        for _ in range(10):
            start_time = time.time()
            self.income_manager.validate_data_quality()
            validation_times.append(time.time() - start_time)
        
        avg_validation_time = sum(validation_times) / len(validation_times)
        self.assertLess(avg_validation_time, 0.05, 
                       f"Average validation time: {avg_validation_time:.3f}s")

if __name__ == '__main__':
    unittest.main() 