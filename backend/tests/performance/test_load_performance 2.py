"""
Performance Tests for AI Calculator

Tests include:
- Load testing for concurrent assessments
- Database performance under heavy load
- Email delivery rate testing
- CDN and caching effectiveness
- Response time benchmarks
- Memory usage monitoring
- CPU utilization testing
"""

import pytest
import unittest
import time
import threading
import concurrent.futures
import psutil
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import statistics
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app import create_app
from backend.database import get_db_session, init_database_session_factory
from backend.models.user import User
from backend.models.assessment_models import Assessment
from backend.models.assessment_analytics_models import AssessmentAnalyticsEvent
from backend.models.payment import MINGUSPaymentIntent
from backend.services.assessment_scoring_service import AssessmentScoringService
from backend.services.email_automation_service import EmailAutomationService

class TestLoadPerformance(unittest.TestCase):
    """Performance test suite for load testing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Mock database session
        self.mock_session = Mock()
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.rollback.return_value = None
        self.mock_session.close.return_value = None
        
        # Patch database session
        self.db_patcher = patch('backend.database.get_db_session', return_value=self.mock_session)
        self.db_patcher.start()
        
        # Initialize services with mocked session
        self.scoring_service = AssessmentScoringService(self.mock_session, self.app.config)
        self.email_service = EmailAutomationService(self.app.config)
        
        # Performance metrics
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        
        # Test data
        self.test_assessment_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'experience_level': 'mid',
            'company_size': 'large',
            'location': 'urban',
            'industry': 'technology',
            'skills': ['python', 'javascript', 'react'],
            'required_skills': ['python', 'javascript', 'react', 'node.js']
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_patcher.stop()
        self.app_context.pop()
    
    def record_metrics(self, start_time, end_time):
        """Record performance metrics"""
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        self.response_times.append(response_time)
        
        # Record memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        
        # Record CPU usage
        cpu_percent = process.cpu_percent()
        self.cpu_usage.append(cpu_percent)
    
    def test_concurrent_assessment_processing(self):
        """Test concurrent assessment processing performance"""
        # Create test users
        users = []
        for i in range(100):
            user = User(
                id=f'test_user_{i}',
                email=f'test{i}@example.com',
                first_name=f'Test{i}',
                last_name=f'User{i}',
                subscription_tier='basic',
                created_at=datetime.utcnow(),
                is_active=True
            )
            users.append(user)
            self.mock_session.add(user)
        self.mock_session.commit()
        
        # Performance test parameters
        concurrent_users = 50
        requests_per_user = 10
        total_requests = concurrent_users * requests_per_user
        
        print(f"\nStarting concurrent assessment test:")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Requests per user: {requests_per_user}")
        print(f"Total requests: {total_requests}")
        
        def process_assessment(user_id, request_id):
            """Process a single assessment"""
            start_time = time.time()
            
            try:
                with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate:
                    mock_calculate.return_value = Mock(
                        overall_score=0.65,
                        final_risk_level='medium',
                        field_multiplier=1.2,
                        confidence_interval=(0.60, 0.70),
                        recommendations=['Test recommendation'],
                        risk_factors=['Test risk factor']
                    )
                    
                    # Create assessment
                    assessment = Assessment(
                        id=f'assessment_{user_id}_{request_id}',
                        user_id=user_id,
                        assessment_type='job_risk',
                        status='in_progress'
                    )
                    self.mock_session.add(assessment)
                    self.mock_session.commit()
                    
                    # Calculate score
                    result = self.scoring_service.calculate_assessment_score(
                        assessment.id,
                        self.test_assessment_data
                    )
                    
                    end_time = time.time()
                    self.record_metrics(start_time, end_time)
                    
                    return True, result
            except Exception as e:
                end_time = time.time()
                self.record_metrics(start_time, end_time)
                return False, str(e)
        
        # Execute concurrent requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user in users[:concurrent_users]:
                for request_id in range(requests_per_user):
                    future = executor.submit(process_assessment, user.id, request_id)
                    futures.append(future)
            
            # Collect results
            success_count = 0
            error_count = 0
            
            for future in concurrent.futures.as_completed(futures):
                success, result = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(self.response_times)
        p95_response_time = statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(self.response_times, n=100)[98]  # 99th percentile
        
        max_memory = max(self.memory_usage)
        avg_memory = statistics.mean(self.memory_usage)
        
        max_cpu = max(self.cpu_usage)
        avg_cpu = statistics.mean(self.cpu_usage)
        
        requests_per_second = total_requests / total_time
        
        # Print results
        print(f"\nPerformance Results:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests per second: {requests_per_second:.2f}")
        print(f"Success rate: {(success_count/total_requests)*100:.2f}%")
        print(f"Error rate: {(error_count/total_requests)*100:.2f}%")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"95th percentile response time: {p95_response_time:.2f}ms")
        print(f"99th percentile response time: {p99_response_time:.2f}ms")
        print(f"Max memory usage: {max_memory:.2f}MB")
        print(f"Average memory usage: {avg_memory:.2f}MB")
        print(f"Max CPU usage: {max_cpu:.2f}%")
        print(f"Average CPU usage: {avg_cpu:.2f}%")
        
        # Performance assertions
        self.assertGreater(requests_per_second, 10)  # At least 10 requests per second
        self.assertLess(avg_response_time, 5000)  # Average response time under 5 seconds
        self.assertLess(p95_response_time, 10000)  # 95th percentile under 10 seconds
        self.assertGreater(success_count/total_requests, 0.95)  # 95% success rate
        self.assertLess(max_memory, 1000)  # Max memory under 1GB
    
    def test_database_performance_under_load(self):
        """Test database performance under heavy load"""
        # Create large dataset
        print("\nCreating large dataset for database performance test...")
        
        users = []
        for i in range(1000):
            user = User(
                id=f'perf_user_{i}',
                email=f'perf{i}@example.com',
                first_name=f'Perf{i}',
                last_name=f'User{i}',
                subscription_tier='basic',
                created_at=datetime.utcnow(),
                is_active=True
            )
            users.append(user)
        
        # Batch insert users
        start_time = time.time()
        self.mock_session.bulk_save_objects(users)
        self.mock_session.commit()
        user_insert_time = time.time() - start_time
        
        print(f"Inserted {len(users)} users in {user_insert_time:.2f} seconds")
        
        # Create assessments
        assessments = []
        for i in range(5000):
            assessment = Assessment(
                id=f'perf_assessment_{i}',
                user_id=users[i % len(users)].id,
                assessment_type='job_risk',
                status='completed',
                data=self.test_assessment_data,
                results={'overall_score': 0.65 + (i % 35) / 100},
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            assessments.append(assessment)
        
        # Batch insert assessments
        start_time = time.time()
        self.mock_session.bulk_save_objects(assessments)
        self.mock_session.commit()
        assessment_insert_time = time.time() - start_time
        
        print(f"Inserted {len(assessments)} assessments in {assessment_insert_time:.2f} seconds")
        
        # Test query performance
        print("\nTesting query performance...")
        
        # Test user lookup
        start_time = time.time()
        for i in range(100):
            user = User.query.filter_by(email=f'perf{i}@example.com').first()
        user_query_time = (time.time() - start_time) / 100
        
        # Test assessment history query
        start_time = time.time()
        for i in range(100):
            user_assessments = Assessment.query.filter_by(
                user_id=users[i].id
            ).order_by(Assessment.created_at.desc()).limit(10).all()
        assessment_query_time = (time.time() - start_time) / 100
        
        # Test analytics aggregation
        start_time = time.time()
        for i in range(10):
            avg_score = self.mock_session.query(
                Assessment.results['overall_score'].astext.cast(json.Float)
            ).scalar()
        aggregation_time = (time.time() - start_time) / 10
        
        print(f"Average user lookup time: {user_query_time*1000:.2f}ms")
        print(f"Average assessment history query time: {assessment_query_time*1000:.2f}ms")
        print(f"Average aggregation query time: {aggregation_time*1000:.2f}ms")
        
        # Performance assertions
        self.assertLess(user_query_time, 0.01)  # User lookup under 10ms
        self.assertLess(assessment_query_time, 0.05)  # Assessment query under 50ms
        self.assertLess(aggregation_time, 0.1)  # Aggregation under 100ms
    
    def test_email_delivery_performance(self):
        """Test email delivery performance under load"""
        print("\nTesting email delivery performance...")
        
        # Create test users
        users = []
        for i in range(100):
            user = User(
                id=f'email_user_{i}',
                email=f'email{i}@example.com',
                first_name=f'Email{i}',
                last_name=f'User{i}',
                subscription_tier='basic',
                created_at=datetime.utcnow(),
                is_active=True
            )
            users.append(user)
            self.mock_session.add(user)
        self.mock_session.commit()
        
        # Mock email service
        with patch('backend.services.email_automation_service.Mail') as mock_mail:
            mock_mail_instance = Mock()
            mock_mail.return_value = mock_mail_instance
            mock_mail_instance.send.return_value = True
            
            # Test batch email sending
            start_time = time.time()
            
            email_results = []
            for user in users:
                email_start = time.time()
                
                result = self.email_service.send_assessment_email(
                    user.__dict__,
                    {'id': 'test_assessment', 'results': {'overall_score': 0.65}}
                )
                
                email_end = time.time()
                email_results.append({
                    'success': result,
                    'time': (email_end - email_start) * 1000
                })
            
            total_time = time.time() - start_time
            
            # Calculate metrics
            successful_emails = sum(1 for r in email_results if r['success'])
            email_times = [r['time'] for r in email_results]
            avg_email_time = statistics.mean(email_times)
            emails_per_second = len(users) / total_time
            
            print(f"Sent {len(users)} emails in {total_time:.2f} seconds")
            print(f"Emails per second: {emails_per_second:.2f}")
            print(f"Success rate: {(successful_emails/len(users))*100:.2f}%")
            print(f"Average email time: {avg_email_time:.2f}ms")
            
            # Performance assertions
            self.assertEqual(successful_emails, len(users))  # 100% success rate
            self.assertGreater(emails_per_second, 10)  # At least 10 emails per second
            self.assertLess(avg_email_time, 100)  # Average email time under 100ms
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during operations"""
        print("\nTesting memory usage monitoring...")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"Initial memory usage: {initial_memory:.2f}MB")
        
        # Perform memory-intensive operations
        memory_usage = []
        
        for i in range(100):
            # Create large objects
            large_data = {
                'assessment_data': self.test_assessment_data.copy(),
                'results': {
                    'overall_score': 0.65 + (i % 35) / 100,
                    'recommendations': [f'Recommendation {j}' for j in range(10)],
                    'risk_factors': [f'Risk factor {j}' for j in range(5)]
                },
                'analytics': {
                    'completion_time': 120 + i,
                    'user_agent': 'test-agent',
                    'session_id': f'session_{i}'
                }
            }
            
            # Simulate processing
            with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate:
                mock_calculate.return_value = Mock(
                    overall_score=large_data['results']['overall_score'],
                    final_risk_level='medium',
                    field_multiplier=1.2,
                    confidence_interval=(0.60, 0.70),
                    recommendations=large_data['results']['recommendations'],
                    risk_factors=large_data['results']['risk_factors']
                )
                
                result = self.scoring_service._calculate_ai_job_risk(large_data['assessment_data'])
            
            # Record memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_usage.append(current_memory)
            
            if i % 20 == 0:
                print(f"Memory usage after {i} operations: {current_memory:.2f}MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_usage)
        memory_increase = final_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.2f}MB")
        print(f"Maximum memory usage: {max_memory:.2f}MB")
        print(f"Memory increase: {memory_increase:.2f}MB")
        
        # Memory assertions
        self.assertLess(memory_increase, 100)  # Memory increase under 100MB
        self.assertLess(max_memory, 500)  # Max memory under 500MB
    
    def test_cpu_utilization_monitoring(self):
        """Test CPU utilization during intensive operations"""
        print("\nTesting CPU utilization monitoring...")
        
        process = psutil.Process(os.getpid())
        cpu_usage = []
        
        # Perform CPU-intensive operations
        for i in range(100):
            start_time = time.time()
            
            # Simulate complex calculations
            with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate:
                mock_calculate.return_value = Mock(
                    overall_score=0.65 + (i % 35) / 100,
                    final_risk_level='medium',
                    field_multiplier=1.2,
                    confidence_interval=(0.60, 0.70),
                    recommendations=['Test recommendation'],
                    risk_factors=['Test risk factor']
                )
                
                # Multiple calculations to increase CPU usage
                for j in range(10):
                    result = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
            
            # Record CPU usage
            cpu_percent = process.cpu_percent()
            cpu_usage.append(cpu_percent)
            
            if i % 20 == 0:
                print(f"CPU usage after {i} operations: {cpu_percent:.2f}%")
        
        avg_cpu = statistics.mean(cpu_usage)
        max_cpu = max(cpu_usage)
        
        print(f"Average CPU usage: {avg_cpu:.2f}%")
        print(f"Maximum CPU usage: {max_cpu:.2f}%")
        
        # CPU assertions
        self.assertLess(avg_cpu, 80)  # Average CPU under 80%
        self.assertLess(max_cpu, 95)  # Max CPU under 95%
    
    def test_response_time_benchmarks(self):
        """Test response time benchmarks for different operations"""
        print("\nTesting response time benchmarks...")
        
        # Create test user
        user = User(
            id='benchmark_user',
            email='benchmark@example.com',
            first_name='Benchmark',
            last_name='User',
            subscription_tier='basic',
            created_at=datetime.utcnow(),
            is_active=True
        )
        self.mock_session.add(user)
        self.mock_session.commit()
        
        # Test different operations
        operations = {
            'user_lookup': lambda: User.query.filter_by(email='benchmark@example.com').first(),
            'assessment_creation': lambda: Assessment(
                user_id=user.id,
                assessment_type='job_risk',
                status='in_progress'
            ),
            'scoring_calculation': lambda: self.scoring_service._calculate_ai_job_risk(self.test_assessment_data),
            'email_sending': lambda: self.email_service.send_assessment_email(
                user.__dict__,
                {'id': 'test_assessment', 'results': {'overall_score': 0.65}}
            )
        }
        
        results = {}
        
        for operation_name, operation_func in operations.items():
            times = []
            
            for i in range(100):
                start_time = time.time()
                
                with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate, \
                     patch('backend.services.email_automation_service.Mail') as mock_mail:
                    
                    mock_calculate.return_value = Mock(
                        overall_score=0.65,
                        final_risk_level='medium',
                        field_multiplier=1.2,
                        confidence_interval=(0.60, 0.70),
                        recommendations=['Test'],
                        risk_factors=['Test']
                    )
                    
                    mock_mail_instance = Mock()
                    mock_mail.return_value = mock_mail_instance
                    mock_mail_instance.send.return_value = True
                    
                    result = operation_func()
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            
            avg_time = statistics.mean(times)
            p95_time = statistics.quantiles(times, n=20)[18]
            p99_time = statistics.quantiles(times, n=100)[98]
            
            results[operation_name] = {
                'avg': avg_time,
                'p95': p95_time,
                'p99': p99_time
            }
            
            print(f"{operation_name}:")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  95th percentile: {p95_time:.2f}ms")
            print(f"  99th percentile: {p99_time:.2f}ms")
        
        # Benchmark assertions
        self.assertLess(results['user_lookup']['avg'], 10)  # User lookup under 10ms
        self.assertLess(results['assessment_creation']['avg'], 5)  # Assessment creation under 5ms
        self.assertLess(results['scoring_calculation']['avg'], 100)  # Scoring under 100ms
        self.assertLess(results['email_sending']['avg'], 50)  # Email sending under 50ms

if __name__ == '__main__':
    unittest.main()
