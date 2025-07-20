"""
Performance Benchmarks for Job Recommendation Engine
Tests processing times, memory usage, concurrency, and scalability
"""

import unittest
import pytest
import time
import json
import tempfile
import os
import psutil
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import gc

from backend.ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from backend.ml.models.resume_parser import AdvancedResumeParser
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for the job recommendation engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = MingusJobRecommendationEngine()
        self.resume_parser = AdvancedResumeParser()
        
        # Sample resumes for testing
        self.sample_resumes = [
            # Entry level
            """
            JUNIOR DATA ANALYST
            StartupCorp | Atlanta, GA | 2022-2023
            - Assisted with data analysis using Excel and basic SQL
            - Created reports and dashboards for team leads
            - Supported marketing campaigns with data insights
            
            EDUCATION
            Morehouse College
            Bachelor of Science in Mathematics
            GPA: 3.6/4.0
            
            SKILLS
            Technical: Excel, SQL (basic), Python (basic), Tableau
            Business: Data Analysis, Reporting, Communication
            """,
            
            # Mid level
            """
            SENIOR MARKETING SPECIALIST
            BrandCorp | Houston, TX | 2020-2023
            - Led digital marketing campaigns with $200K budget
            - Managed team of 2 specialists and achieved 20% growth
            - Developed customer acquisition strategies
            
            MARKETING COORDINATOR
            GrowthCorp | Houston, TX | 2018-2020
            - Executed social media campaigns and email marketing
            - Analyzed campaign performance using Google Analytics
            
            EDUCATION
            Texas Southern University
            Bachelor of Business Administration in Marketing
            GPA: 3.5/4.0
            
            SKILLS
            Technical: Google Analytics, Facebook Ads, Email Marketing, CRM
            Business: Campaign Management, Budget Management, Team Leadership
            """,
            
            # Senior level
            """
            SENIOR DATA ANALYST
            TechCorp Inc. | Atlanta, GA | 2020-2023
            - Led data analysis initiatives using Python, SQL, and Tableau
            - Managed team of 3 analysts and delivered insights to executives
            - Increased revenue by 15% through predictive analytics
            
            DATA ANALYST
            DataFlow Solutions | Atlanta, GA | 2018-2020
            - Performed statistical analysis and created automated reporting
            - Developed SQL queries and maintained data warehouse
            
            EDUCATION
            Georgia Institute of Technology
            Bachelor of Science in Industrial Engineering
            GPA: 3.8/4.0
            
            SKILLS
            Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning
            Business: Project Management, Stakeholder Communication, Strategic Analysis
            """
        ]
        
        # Performance targets
        self.performance_targets = {
            'resume_processing': 2.0,      # 2 seconds max
            'income_comparison': 1.0,      # 1 second max
            'job_search': 5.0,             # 5 seconds max
            'job_selection': 2.0,          # 2 seconds max
            'total_workflow': 8.0,         # 8 seconds max
            'memory_usage': 100,           # 100MB max
            'concurrent_users': 10,        # 10 concurrent users
            'cache_hit_rate': 0.7,        # 70% cache hit rate
            'error_rate': 0.05            # 5% error rate max
        }

    def test_resume_processing_performance(self):
        """Test resume processing performance"""
        processing_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            start_time = time.time()
            
            result = self.resume_parser.parse_resume(resume)
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Verify processing completed successfully
            self.assertIsNotNone(result)
            self.assertIn('field_analysis', str(result))
            self.assertIn('experience_analysis', str(result))
        
        # Calculate statistics
        avg_time = statistics.mean(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        # Verify performance targets
        self.assertLess(avg_time, self.performance_targets['resume_processing'])
        self.assertLess(max_time, self.performance_targets['resume_processing'] * 1.5)
        
        print(f"Resume Processing Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Maximum: {max_time:.3f}s")
        print(f"  Minimum: {min_time:.3f}s")

    def test_income_comparison_performance(self):
        """Test income comparison performance"""
        comparison_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            # Parse resume first
            resume_analysis = self.resume_parser.parse_resume(resume)
            
            # Test income comparison
            start_time = time.time()
            
            current_salary = 60000 + i * 10000  # Different salaries
            target_locations = ['Atlanta', 'Houston']
            
            financial_impact = self.engine._analyze_income_and_financial_impact(
                resume_analysis, current_salary, target_locations
            )
            
            comparison_time = time.time() - start_time
            comparison_times.append(comparison_time)
            
            # Verify comparison completed successfully
            self.assertIsNotNone(financial_impact)
            self.assertGreater(financial_impact.current_salary, 0)
        
        # Calculate statistics
        avg_time = statistics.mean(comparison_times)
        max_time = max(comparison_times)
        
        # Verify performance targets
        self.assertLess(avg_time, self.performance_targets['income_comparison'])
        self.assertLess(max_time, self.performance_targets['income_comparison'] * 1.5)
        
        print(f"Income Comparison Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Maximum: {max_time:.3f}s")

    def test_job_search_performance(self):
        """Test job search performance"""
        search_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            # Parse resume and analyze income
            resume_analysis = self.resume_parser.parse_resume(resume)
            current_salary = 60000 + i * 10000
            target_locations = ['Atlanta', 'Houston']
            
            financial_impact = self.engine._analyze_income_and_financial_impact(
                resume_analysis, current_salary, target_locations
            )
            
            # Test job search
            start_time = time.time()
            
            job_opportunities = self.engine._search_and_match_jobs(
                resume_analysis, financial_impact, target_locations
            )
            
            search_time = time.time() - start_time
            search_times.append(search_time)
            
            # Verify search completed successfully
            self.assertIsNotNone(job_opportunities)
            self.assertGreater(len(job_opportunities), 0)
        
        # Calculate statistics
        avg_time = statistics.mean(search_times)
        max_time = max(search_times)
        
        # Verify performance targets
        self.assertLess(avg_time, self.performance_targets['job_search'])
        self.assertLess(max_time, self.performance_targets['job_search'] * 1.5)
        
        print(f"Job Search Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Maximum: {max_time:.3f}s")

    def test_job_selection_performance(self):
        """Test job selection performance"""
        selection_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            # Complete workflow up to job search
            resume_analysis = self.resume_parser.parse_resume(resume)
            current_salary = 60000 + i * 10000
            target_locations = ['Atlanta', 'Houston']
            
            financial_impact = self.engine._analyze_income_and_financial_impact(
                resume_analysis, current_salary, target_locations
            )
            
            job_opportunities = self.engine._search_and_match_jobs(
                resume_analysis, financial_impact, target_locations
            )
            
            # Test job selection
            start_time = time.time()
            
            career_strategy = self.engine._select_jobs_and_generate_strategy(
                job_opportunities, resume_analysis, financial_impact, 'balanced'
            )
            
            selection_time = time.time() - start_time
            selection_times.append(selection_time)
            
            # Verify selection completed successfully
            self.assertIsNotNone(career_strategy)
            self.assertIsNotNone(career_strategy.conservative_opportunity)
            self.assertIsNotNone(career_strategy.optimal_opportunity)
            self.assertIsNotNone(career_strategy.stretch_opportunity)
        
        # Calculate statistics
        avg_time = statistics.mean(selection_times)
        max_time = max(selection_times)
        
        # Verify performance targets
        self.assertLess(avg_time, self.performance_targets['job_selection'])
        self.assertLess(max_time, self.performance_targets['job_selection'] * 1.5)
        
        print(f"Job Selection Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Maximum: {max_time:.3f}s")

    def test_total_workflow_performance(self):
        """Test complete workflow performance"""
        workflow_times = []
        success_count = 0
        error_count = 0
        
        for i, resume in enumerate(self.sample_resumes):
            try:
                start_time = time.time()
                
                result = self.engine.process_resume_and_recommend_jobs(
                    resume_text=resume,
                    user_id=i + 1,
                    current_salary=60000 + i * 10000,
                    target_locations=['Atlanta', 'Houston'],
                    risk_preference='balanced',
                    enable_caching=False  # Disable caching for consistent testing
                )
                
                workflow_time = time.time() - start_time
                workflow_times.append(workflow_time)
                success_count += 1
                
                # Verify workflow completed successfully
                self.assertTrue(result.success)
                self.assertIsNotNone(result.user_profile)
                self.assertIsNotNone(result.career_strategy)
                self.assertIsNotNone(result.action_plan)
                
            except Exception as e:
                error_count += 1
                print(f"Error in workflow {i}: {str(e)}")
        
        # Calculate statistics
        if workflow_times:
            avg_time = statistics.mean(workflow_times)
            max_time = max(workflow_times)
            min_time = min(workflow_times)
            
            # Verify performance targets
            self.assertLess(avg_time, self.performance_targets['total_workflow'])
            self.assertLess(max_time, self.performance_targets['total_workflow'] * 1.5)
            
            # Verify success rate
            total_requests = success_count + error_count
            success_rate = success_count / total_requests if total_requests > 0 else 0
            self.assertGreater(success_rate, 1 - self.performance_targets['error_rate'])
            
            print(f"Total Workflow Performance:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Maximum: {max_time:.3f}s")
            print(f"  Minimum: {min_time:.3f}s")
            print(f"  Success Rate: {success_rate:.2%}")

    def test_memory_usage_performance(self):
        """Test memory usage performance"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_usage = []
        
        for i in range(10):
            # Process multiple requests
            for j, resume in enumerate(self.sample_resumes):
                result = self.engine.process_resume_and_recommend_jobs(
                    resume_text=resume,
                    user_id=i * 10 + j,
                    current_salary=60000 + j * 10000,
                    target_locations=['Atlanta'],
                    enable_caching=False
                )
                
                self.assertTrue(result.success)
            
            # Measure memory after batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            memory_usage.append(memory_increase)
            
            # Force garbage collection
            gc.collect()
        
        # Calculate statistics
        avg_memory = statistics.mean(memory_usage)
        max_memory = max(memory_usage)
        
        # Verify memory usage targets
        self.assertLess(avg_memory, self.performance_targets['memory_usage'])
        self.assertLess(max_memory, self.performance_targets['memory_usage'] * 1.5)
        
        print(f"Memory Usage Performance:")
        print(f"  Average Increase: {avg_memory:.2f}MB")
        print(f"  Maximum Increase: {max_memory:.2f}MB")

    def test_concurrency_performance(self):
        """Test concurrency performance"""
        def process_request(user_id):
            try:
                resume = self.sample_resumes[user_id % len(self.sample_resumes)]
                
                start_time = time.time()
                
                result = self.engine.process_resume_and_recommend_jobs(
                    resume_text=resume,
                    user_id=user_id,
                    current_salary=60000 + (user_id % 3) * 10000,
                    target_locations=['Atlanta'],
                    enable_caching=False
                )
                
                processing_time = time.time() - start_time
                
                return {
                    'user_id': user_id,
                    'success': result.success,
                    'processing_time': processing_time,
                    'error': None
                }
                
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'processing_time': 0,
                    'error': str(e)
                }
        
        # Test different concurrency levels
        concurrency_levels = [1, 3, 5, 10]
        
        for concurrency in concurrency_levels:
            print(f"\nTesting concurrency level: {concurrency}")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(process_request, i) for i in range(20)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Calculate statistics
            successful_results = [r for r in results if r['success']]
            processing_times = [r['processing_time'] for r in successful_results]
            
            if processing_times:
                avg_time = statistics.mean(processing_times)
                max_time = max(processing_times)
                min_time = min(processing_times)
                
                success_rate = len(successful_results) / len(results)
                
                print(f"  Total Time: {total_time:.3f}s")
                print(f"  Average Processing Time: {avg_time:.3f}s")
                print(f"  Maximum Processing Time: {max_time:.3f}s")
                print(f"  Success Rate: {success_rate:.2%}")
                
                # Verify performance under load
                if concurrency <= self.performance_targets['concurrent_users']:
                    self.assertGreater(success_rate, 0.8)  # 80% success rate
                    self.assertLess(avg_time, self.performance_targets['total_workflow'] * 2)

    def test_caching_performance(self):
        """Test caching performance"""
        # Test cache hit rate
        cache_hits = 0
        cache_misses = 0
        
        # First round - populate cache
        for i, resume in enumerate(self.sample_resumes):
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=resume,
                user_id=i + 100,
                current_salary=60000 + i * 10000,
                target_locations=['Atlanta'],
                enable_caching=True
            )
            
            self.assertTrue(result.success)
            cache_misses += 1
        
        # Second round - should hit cache
        for i, resume in enumerate(self.sample_resumes):
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=resume,
                user_id=i + 100,
                current_salary=60000 + i * 10000,
                target_locations=['Atlanta'],
                enable_caching=True
            )
            
            self.assertTrue(result.success)
            cache_hits += 1
        
        # Calculate cache hit rate
        total_requests = cache_hits + cache_misses
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        
        print(f"Cache Performance:")
        print(f"  Cache Hits: {cache_hits}")
        print(f"  Cache Misses: {cache_misses}")
        print(f"  Hit Rate: {hit_rate:.2%}")
        
        # Verify cache effectiveness
        self.assertGreater(hit_rate, 0.3)  # At least 30% hit rate
        
        # Test cache performance improvement
        cache_times = []
        no_cache_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            # With cache
            start_time = time.time()
            result1 = self.engine.process_resume_and_recommend_jobs(
                resume_text=resume,
                user_id=i + 200,
                current_salary=60000 + i * 10000,
                target_locations=['Atlanta'],
                enable_caching=True
            )
            cache_time = time.time() - start_time
            cache_times.append(cache_time)
            
            # Without cache
            start_time = time.time()
            result2 = self.engine.process_resume_and_recommend_jobs(
                resume_text=resume,
                user_id=i + 300,
                current_salary=60000 + i * 10000,
                target_locations=['Atlanta'],
                enable_caching=False
            )
            no_cache_time = time.time() - start_time
            no_cache_times.append(no_cache_time)
        
        avg_cache_time = statistics.mean(cache_times)
        avg_no_cache_time = statistics.mean(no_cache_times)
        
        print(f"  Average Time with Cache: {avg_cache_time:.3f}s")
        print(f"  Average Time without Cache: {avg_no_cache_time:.3f}s")
        print(f"  Performance Improvement: {((avg_no_cache_time - avg_cache_time) / avg_no_cache_time * 100):.1f}%")

    def test_api_response_time_performance(self):
        """Test API response time performance"""
        from backend.app import create_app
        
        app = create_app('testing')
        client = app.test_client()
        
        response_times = []
        
        for i, resume in enumerate(self.sample_resumes):
            data = {
                'resume_text': resume,
                'current_salary': 60000 + i * 10000,
                'target_locations': ['Atlanta'],
                'risk_preference': 'balanced'
            }
            
            start_time = time.time()
            
            response = client.post(
                '/api/job-recommendation/process-resume',
                json=data,
                headers={'Authorization': 'Bearer test_token'}
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.data)
            self.assertTrue(result['success'])
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"API Response Time Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Maximum: {max_time:.3f}s")
        
        # Verify API performance targets
        self.assertLess(avg_time, self.performance_targets['total_workflow'] * 1.2)  # Allow 20% overhead

    def test_database_performance(self):
        """Test database performance with mocking"""
        with patch('backend.services.intelligent_job_matching_service.Session') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            service = IntelligentJobMatchingService(mock_db)
            
            # Mock database response
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id=1,
                current_salary=75000,
                preferred_locations=['Atlanta']
            )
            
            query_times = []
            
            for i in range(10):
                start_time = time.time()
                
                result = service.find_income_advancement_opportunities(
                    user_id=1,
                    resume_text=self.sample_resumes[0],
                    current_salary=75000,
                    target_locations=['Atlanta']
                )
                
                query_time = time.time() - start_time
                query_times.append(query_time)
                
                self.assertNotIn('error', result)
            
            # Calculate statistics
            avg_time = statistics.mean(query_times)
            max_time = max(query_times)
            
            print(f"Database Query Performance:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Maximum: {max_time:.3f}s")
            
            # Verify database performance
            self.assertLess(avg_time, 1.0)  # Under 1 second for database operations

    def test_scalability_performance(self):
        """Test scalability performance with increasing load"""
        load_levels = [1, 5, 10, 20, 50]
        
        scalability_results = []
        
        for load in load_levels:
            print(f"\nTesting scalability with {load} concurrent requests")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=min(load, 10)) as executor:
                futures = [executor.submit(self._process_single_request, i) for i in range(load)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Calculate metrics
            successful_results = [r for r in results if r['success']]
            processing_times = [r['processing_time'] for r in successful_results]
            
            if processing_times:
                avg_time = statistics.mean(processing_times)
                max_time = max(processing_times)
                success_rate = len(successful_results) / len(results)
                
                scalability_results.append({
                    'load': load,
                    'total_time': total_time,
                    'avg_processing_time': avg_time,
                    'max_processing_time': max_time,
                    'success_rate': success_rate,
                    'throughput': load / total_time if total_time > 0 else 0
                })
                
                print(f"  Total Time: {total_time:.3f}s")
                print(f"  Average Processing Time: {avg_time:.3f}s")
                print(f"  Success Rate: {success_rate:.2%}")
                print(f"  Throughput: {load / total_time:.2f} requests/second")
        
        # Verify scalability characteristics
        if len(scalability_results) >= 2:
            # Throughput should not decrease significantly with moderate load
            moderate_load_results = [r for r in scalability_results if r['load'] <= 20]
            if len(moderate_load_results) >= 2:
                throughputs = [r['throughput'] for r in moderate_load_results]
                throughput_degradation = (max(throughputs) - min(throughputs)) / max(throughputs)
                self.assertLess(throughput_degradation, 0.5)  # Less than 50% degradation

    def _process_single_request(self, user_id):
        """Helper method for processing single request"""
        try:
            resume = self.sample_resumes[user_id % len(self.sample_resumes)]
            
            start_time = time.time()
            
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=resume,
                user_id=user_id,
                current_salary=60000 + (user_id % 3) * 10000,
                target_locations=['Atlanta'],
                enable_caching=False
            )
            
            processing_time = time.time() - start_time
            
            return {
                'user_id': user_id,
                'success': result.success,
                'processing_time': processing_time,
                'error': None
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'success': False,
                'processing_time': 0,
                'error': str(e)
            }

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = []
        
        # Run extended operation
        for cycle in range(5):
            for i, resume in enumerate(self.sample_resumes):
                result = self.engine.process_resume_and_recommend_jobs(
                    resume_text=resume,
                    user_id=cycle * 100 + i,
                    current_salary=60000 + i * 10000,
                    target_locations=['Atlanta'],
                    enable_caching=False
                )
                
                self.assertTrue(result.success)
            
            # Force garbage collection
            gc.collect()
            
            # Measure memory
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            memory_samples.append(memory_increase)
        
        # Check for memory leaks
        if len(memory_samples) >= 3:
            # Memory should not continuously increase
            memory_trend = memory_samples[-1] - memory_samples[0]
            self.assertLess(memory_trend, 50)  # Less than 50MB increase over cycles
        
        print(f"Memory Leak Detection:")
        print(f"  Initial Memory: {initial_memory:.2f}MB")
        print(f"  Final Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB")
        print(f"  Memory Samples: {memory_samples}")

    def test_error_recovery_performance(self):
        """Test performance during error recovery"""
        error_recovery_times = []
        
        for i in range(5):
            # Simulate error condition
            with patch.object(self.engine, '_search_and_match_jobs', side_effect=Exception("Simulated error")):
                start_time = time.time()
                
                try:
                    result = self.engine.process_resume_and_recommend_jobs(
                        resume_text=self.sample_resumes[0],
                        user_id=i + 1000,
                        current_salary=60000,
                        target_locations=['Atlanta'],
                        enable_caching=False
                    )
                except Exception:
                    # Expected error
                    pass
                
                recovery_time = time.time() - start_time
                error_recovery_times.append(recovery_time)
        
        # Calculate statistics
        avg_recovery_time = statistics.mean(error_recovery_times)
        max_recovery_time = max(error_recovery_times)
        
        print(f"Error Recovery Performance:")
        print(f"  Average Recovery Time: {avg_recovery_time:.3f}s")
        print(f"  Maximum Recovery Time: {max_recovery_time:.3f}s")
        
        # Verify error recovery performance
        self.assertLess(avg_recovery_time, 2.0)  # Under 2 seconds for error recovery


if __name__ == '__main__':
    unittest.main() 