#!/usr/bin/env python3
"""
Daily Outlook Load Testing Suite

Comprehensive load testing for Daily Outlook functionality including:
- Concurrent user access simulation
- Database performance under load
- Cache system stress testing
- Notification delivery scaling
- API endpoint performance under load
- Memory usage monitoring
- Response time analysis
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.models.database import db
from backend.models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
from backend.models.user_models import User
from backend.api.daily_outlook_api import daily_outlook_api
from backend.utils.cache import CacheManager
from backend.utils.notifications import NotificationService


class LoadTestResults:
    """Class to store and analyze load test results"""
    
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.memory_usage = []
        self.cpu_usage = []
        self.start_time = None
        self.end_time = None
    
    def add_response_time(self, response_time):
        self.response_times.append(response_time)
    
    def add_success(self):
        self.success_count += 1
    
    def add_error(self):
        self.error_count += 1
    
    def add_memory_usage(self, memory_mb):
        self.memory_usage.append(memory_mb)
    
    def add_cpu_usage(self, cpu_percent):
        self.cpu_usage.append(cpu_percent)
    
    def get_statistics(self):
        """Get comprehensive statistics from load test results"""
        if not self.response_times:
            return {}
        
        return {
            'total_requests': len(self.response_times),
            'success_rate': self.success_count / (self.success_count + self.error_count) * 100,
            'error_rate': self.error_count / (self.success_count + self.error_count) * 100,
            'avg_response_time': statistics.mean(self.response_times),
            'median_response_time': statistics.median(self.response_times),
            'p95_response_time': self._percentile(self.response_times, 95),
            'p99_response_time': self._percentile(self.response_times, 99),
            'max_response_time': max(self.response_times),
            'min_response_time': min(self.response_times),
            'avg_memory_usage': statistics.mean(self.memory_usage) if self.memory_usage else 0,
            'max_memory_usage': max(self.memory_usage) if self.memory_usage else 0,
            'avg_cpu_usage': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            'max_cpu_usage': max(self.cpu_usage) if self.cpu_usage else 0,
            'total_duration': (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        }
    
    def _percentile(self, data, percentile):
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class TestConcurrentUserAccess:
    """Test suite for concurrent user access simulation"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def test_users(self, app):
        """Create test users for load testing"""
        with app.app_context():
            users = []
            for i in range(100):
                user = User(
                    user_id=f'loadtest_user_{i}',
                    email=f'loadtest{i}@example.com',
                    first_name=f'LoadTest{i}',
                    last_name='User',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            return users
    
    @pytest.fixture
    def test_outlooks(self, app, test_users):
        """Create test outlooks for load testing"""
        with app.app_context():
            outlooks = []
            for user in test_users:
                outlook = DailyOutlook(
                    user_id=user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    primary_insight="Load test outlook",
                    streak_count=5
                )
                db.session.add(outlook)
                outlooks.append(outlook)
            
            db.session.commit()
            return outlooks
    
    def test_concurrent_api_requests(self, client, test_users, test_outlooks):
        """Test concurrent API requests to daily outlook endpoint"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def make_request(user_id):
            """Make a single API request"""
            start_time = time.time()
            try:
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user_id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        end_time = time.time()
                        
                        response_time = end_time - start_time
                        results.add_response_time(response_time)
                        
                        if response.status_code == 200:
                            results.add_success()
                        else:
                            results.add_error()
                            
                        # Monitor system resources
                        process = psutil.Process()
                        results.add_memory_usage(process.memory_info().rss / 1024 / 1024)  # MB
                        results.add_cpu_usage(process.cpu_percent())
                        
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Request failed for user {user_id}: {e}")
        
        # Simulate concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, user.id) for user in test_users[:50]]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for load test results
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.5, f"Average response time too high: {stats['avg_response_time']}s"
        assert stats['p95_response_time'] < 1.0, f"P95 response time too high: {stats['p95_response_time']}s"
        assert stats['max_memory_usage'] < 500, f"Memory usage too high: {stats['max_memory_usage']}MB"
        
        print(f"Load test results: {stats}")
    
    def test_concurrent_action_completions(self, client, test_users, test_outlooks):
        """Test concurrent action completion requests"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def complete_action(user_id):
            """Complete an action for a user"""
            start_time = time.time()
            try:
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user_id):
                    response = client.post('/api/daily-outlook/action-completed',
                                         json={
                                             'action_id': 'test_action',
                                             'completion_status': True,
                                             'completion_notes': 'Load test completion'
                                         })
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    
                    if response.status_code == 200:
                        results.add_success()
                    else:
                        results.add_error()
                        
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Action completion failed for user {user_id}: {e}")
        
        # Simulate concurrent action completions
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(complete_action, user.id) for user in test_users[:30]]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for action completion load test
        assert stats['success_rate'] >= 90, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.3, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Action completion load test results: {stats}")
    
    def test_concurrent_rating_submissions(self, client, test_users, test_outlooks):
        """Test concurrent rating submission requests"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def submit_rating(user_id):
            """Submit a rating for a user"""
            start_time = time.time()
            try:
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user_id):
                    response = client.post('/api/daily-outlook/rating',
                                         json={'rating': 5})
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    
                    if response.status_code == 200:
                        results.add_success()
                    else:
                        results.add_error()
                        
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Rating submission failed for user {user_id}: {e}")
        
        # Simulate concurrent rating submissions
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_rating, user.id) for user in test_users[:25]]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for rating submission load test
        assert stats['success_rate'] >= 90, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.2, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Rating submission load test results: {stats}")


class TestDatabasePerformanceUnderLoad:
    """Test suite for database performance under load"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    def test_concurrent_database_writes(self, app):
        """Test concurrent database write operations"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def create_user_and_outlook(user_id):
            """Create a user and outlook concurrently"""
            start_time = time.time()
            try:
                with app.app_context():
                    # Create user
                    user = User(
                        user_id=f'concurrent_user_{user_id}',
                        email=f'concurrent{user_id}@example.com',
                        first_name=f'Concurrent{user_id}',
                        last_name='User',
                        tier='budget'
                    )
                    db.session.add(user)
                    db.session.flush()  # Get user ID
                    
                    # Create outlook
                    outlook = DailyOutlook(
                        user_id=user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.25'),
                        career_weight=Decimal('0.20'),
                        primary_insight="Concurrent test outlook",
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    results.add_success()
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Database write failed for user {user_id}: {e}")
        
        # Simulate concurrent database writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user_and_outlook, i) for i in range(50)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for database performance
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.1, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Database write load test results: {stats}")
    
    def test_concurrent_database_reads(self, app):
        """Test concurrent database read operations"""
        # First, create test data
        with app.app_context():
            users = []
            for i in range(100):
                user = User(
                    user_id=f'readtest_user_{i}',
                    email=f'readtest{i}@example.com',
                    first_name=f'ReadTest{i}',
                    last_name='User',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Create outlooks
            for user in users:
                outlook = DailyOutlook(
                    user_id=user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    primary_insight="Read test outlook",
                    streak_count=5
                )
                db.session.add(outlook)
            
            db.session.commit()
        
        results = LoadTestResults()
        results.start_time = time.time()
        
        def read_user_data(user_id):
            """Read user data concurrently"""
            start_time = time.time()
            try:
                with app.app_context():
                    # Query user and outlook
                    user = User.query.get(user_id)
                    outlook = DailyOutlook.query.filter_by(user_id=user_id).first()
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    results.add_success()
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Database read failed for user {user_id}: {e}")
        
        # Simulate concurrent database reads
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(read_user_data, user.id) for user in users[:50]]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for database read performance
        assert stats['success_rate'] >= 98, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.05, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Database read load test results: {stats}")
    
    def test_database_connection_pool_stress(self, app):
        """Test database connection pool under stress"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def stress_database_connection(connection_id):
            """Stress test database connection"""
            start_time = time.time()
            try:
                with app.app_context():
                    # Perform multiple operations
                    for i in range(10):
                        # Create temporary data
                        user = User(
                            user_id=f'stress_user_{connection_id}_{i}',
                            email=f'stress{connection_id}_{i}@example.com',
                            first_name=f'Stress{connection_id}_{i}',
                            last_name='User',
                            tier='budget'
                        )
                        db.session.add(user)
                        db.session.flush()
                        
                        # Query data
                        User.query.filter_by(email=user.email).first()
                        
                        # Update data
                        user.first_name = f'Updated{connection_id}_{i}'
                        db.session.commit()
                        
                        # Delete data
                        db.session.delete(user)
                        db.session.commit()
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    results.add_success()
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Database stress test failed for connection {connection_id}: {e}")
        
        # Simulate database connection stress
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(stress_database_connection, i) for i in range(20)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for database stress test
        assert stats['success_rate'] >= 90, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.5, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Database stress test results: {stats}")


class TestCacheSystemStressTesting:
    """Test suite for cache system stress testing"""
    
    def test_cache_set_performance(self):
        """Test cache set performance under load"""
        cache_manager = CacheManager()
        results = LoadTestResults()
        results.start_time = time.time()
        
        def set_cache_data(key_suffix):
            """Set cache data concurrently"""
            start_time = time.time()
            try:
                cache_key = f"load_test_{key_suffix}"
                cache_value = {
                    'data': f'value_{key_suffix}',
                    'timestamp': time.time(),
                    'load_test': True
                }
                
                cache_manager.set(cache_key, cache_value, ttl=3600)
                
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_success()
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Cache set failed for key {key_suffix}: {e}")
        
        # Simulate concurrent cache sets
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(set_cache_data, i) for i in range(1000)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for cache set performance
        assert stats['success_rate'] >= 99, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.01, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Cache set load test results: {stats}")
    
    def test_cache_get_performance(self):
        """Test cache get performance under load"""
        cache_manager = CacheManager()
        
        # First, populate cache
        for i in range(500):
            cache_key = f"get_test_{i}"
            cache_value = {'data': f'value_{i}', 'timestamp': time.time()}
            cache_manager.set(cache_key, cache_value, ttl=3600)
        
        results = LoadTestResults()
        results.start_time = time.time()
        
        def get_cache_data(key_suffix):
            """Get cache data concurrently"""
            start_time = time.time()
            try:
                cache_key = f"get_test_{key_suffix}"
                cached_data = cache_manager.get(cache_key)
                
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                
                if cached_data:
                    results.add_success()
                else:
                    results.add_error()
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Cache get failed for key {key_suffix}: {e}")
        
        # Simulate concurrent cache gets
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(get_cache_data, i) for i in range(500)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for cache get performance
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.005, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Cache get load test results: {stats}")
    
    def test_cache_memory_usage(self):
        """Test cache memory usage under load"""
        cache_manager = CacheManager()
        results = LoadTestResults()
        results.start_time = time.time()
        
        def set_large_cache_data(key_suffix):
            """Set large cache data to test memory usage"""
            start_time = time.time()
            try:
                cache_key = f"memory_test_{key_suffix}"
                # Create large cache value (1MB)
                cache_value = {
                    'data': 'x' * (1024 * 1024),  # 1MB of data
                    'timestamp': time.time(),
                    'load_test': True
                }
                
                cache_manager.set(cache_key, cache_value, ttl=3600)
                
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_success()
                
                # Monitor memory usage
                process = psutil.Process()
                results.add_memory_usage(process.memory_info().rss / 1024 / 1024)  # MB
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Cache memory test failed for key {key_suffix}: {e}")
        
        # Simulate cache memory usage
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(set_large_cache_data, i) for i in range(50)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for cache memory usage
        assert stats['success_rate'] >= 90, f"Success rate too low: {stats['success_rate']}%"
        assert stats['max_memory_usage'] < 1000, f"Memory usage too high: {stats['max_memory_usage']}MB"
        
        print(f"Cache memory test results: {stats}")


class TestNotificationDeliveryScaling:
    """Test suite for notification delivery scaling"""
    
    def test_concurrent_notification_delivery(self):
        """Test concurrent notification delivery"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def send_notification(notification_id):
            """Send notification concurrently"""
            start_time = time.time()
            try:
                # Mock notification service
                with patch('backend.utils.notifications.NotificationService') as mock_notification:
                    mock_instance = Mock()
                    mock_notification.return_value = mock_instance
                    
                    notification_service = NotificationService()
                    notification_service.send_daily_outlook_notification(notification_id, notification_id)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    results.add_response_time(response_time)
                    results.add_success()
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Notification delivery failed for {notification_id}: {e}")
        
        # Simulate concurrent notification delivery
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(send_notification, i) for i in range(100)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for notification delivery
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.1, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Notification delivery load test results: {stats}")
    
    def test_notification_queue_processing(self):
        """Test notification queue processing under load"""
        results = LoadTestResults()
        results.start_time = time.time()
        
        def process_notification_queue(queue_id):
            """Process notification queue concurrently"""
            start_time = time.time()
            try:
                # Mock queue processing
                notifications = [f'notification_{queue_id}_{i}' for i in range(10)]
                
                for notification in notifications:
                    # Simulate notification processing
                    time.sleep(0.001)  # 1ms processing time
                
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_success()
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"Queue processing failed for queue {queue_id}: {e}")
        
        # Simulate concurrent queue processing
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(process_notification_queue, i) for i in range(50)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for queue processing
        assert stats['success_rate'] >= 98, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.05, f"Average response time too high: {stats['avg_response_time']}s"
        
        print(f"Notification queue processing load test results: {stats}")


class TestAPIPerformanceUnderLoad:
    """Test suite for API performance under load"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    def test_api_endpoint_performance(self, client, app):
        """Test API endpoint performance under load"""
        # Create test data
        with app.app_context():
            users = []
            for i in range(200):
                user = User(
                    user_id=f'apiperf_user_{i}',
                    email=f'apiperf{i}@example.com',
                    first_name=f'APIPerf{i}',
                    last_name='User',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Create outlooks
            for user in users:
                outlook = DailyOutlook(
                    user_id=user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    primary_insight="API performance test",
                    streak_count=5
                )
                db.session.add(outlook)
            
            db.session.commit()
        
        results = LoadTestResults()
        results.start_time = time.time()
        
        def test_api_endpoint(user_id):
            """Test API endpoint performance"""
            start_time = time.time()
            try:
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user_id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        # Test multiple endpoints
                        endpoints = [
                            '/api/daily-outlook/',
                            '/api/daily-outlook/history',
                            '/api/daily-outlook/streak'
                        ]
                        
                        for endpoint in endpoints:
                            response = client.get(endpoint)
                            if response.status_code != 200:
                                raise Exception(f"Endpoint {endpoint} failed with status {response.status_code}")
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        results.add_response_time(response_time)
                        results.add_success()
                        
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                results.add_response_time(response_time)
                results.add_error()
                print(f"API endpoint test failed for user {user_id}: {e}")
        
        # Simulate API endpoint load
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(test_api_endpoint, user.id) for user in users[:100]]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future failed: {e}")
        
        results.end_time = time.time()
        stats = results.get_statistics()
        
        # Assertions for API performance
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
        assert stats['avg_response_time'] < 0.2, f"Average response time too high: {stats['avg_response_time']}s"
        assert stats['p95_response_time'] < 0.5, f"P95 response time too high: {stats['p95_response_time']}s"
        
        print(f"API endpoint load test results: {stats}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
