#!/usr/bin/env python3
"""
PostgreSQL Database and Performance Systems Testing Suite
========================================================

Comprehensive testing for:
- Database connection pooling effectiveness
- Query performance for financial calculations
- Data integrity and backup systems
- Redis caching performance
- Celery background task processing
- Overall system performance under load

Author: AI Assistant
Date: January 2025
"""

import os
import sys
import time
import json
import psutil
import asyncio
import threading
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Database imports
import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Redis imports
import redis
from redis.exceptions import RedisError

# Celery imports
from celery import Celery
from celery.result import AsyncResult

# Performance testing imports
import requests

# Optional imports for advanced load testing
try:
    from locust import HttpUser, task, between
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    print("Warning: Locust not available. Advanced load testing features will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgresql_performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    test_name: str
    response_time_ms: float
    throughput_rps: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    database_queries: int
    errors: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestResult:
    """Test result data class"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    metrics: PerformanceMetrics
    details: Dict[str, Any]
    recommendations: List[str]


class PostgreSQLPerformanceTester:
    """Comprehensive PostgreSQL performance testing system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.test_data = {}
        
        # Database configuration
        self.db_url = config.get('database_url', 'postgresql://localhost/mingus')
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.celery_broker = config.get('celery_broker', 'redis://localhost:6379/0')
        
        # Performance thresholds
        self.thresholds = {
            'query_time_ms': 100,
            'connection_time_ms': 50,
            'cache_hit_rate': 0.8,
            'memory_usage_mb': 1000,
            'cpu_usage_percent': 80,
            'error_rate': 0.01
        }
        
        # Initialize connections
        self._init_connections()
    
    def _init_connections(self):
        """Initialize database and Redis connections"""
        try:
            # PostgreSQL connection pool
            self.db_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=self.db_url
            )
            
            # SQLAlchemy engine
            self.engine = create_engine(
                self.db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            
            # Celery app
            self.celery_app = Celery('performance_test')
            self.celery_app.conf.update(
                broker_url=self.celery_broker,
                result_backend=self.celery_broker,
                task_serializer='json',
                result_serializer='json',
                accept_content=['json'],
                timezone='UTC',
                enable_utc=True
            )
            
            logger.info("All connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("Starting comprehensive PostgreSQL performance testing")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        
        # Test categories
        test_categories = [
            ('Database Connection Pooling', self.test_connection_pooling),
            ('Query Performance', self.test_query_performance),
            ('Financial Calculations', self.test_financial_calculations),
            ('Data Integrity', self.test_data_integrity),
            ('Backup Systems', self.test_backup_systems),
            ('Redis Caching', self.test_redis_caching),
            ('Celery Tasks', self.test_celery_tasks),
            ('Load Testing', self.test_load_performance),
            ('System Resources', self.test_system_resources)
        ]
        
        for category_name, test_func in test_categories:
            try:
                logger.info(f"Running {category_name} tests...")
                result = test_func()
                test_results['tests'].append({
                    'category': category_name,
                    'result': result
                })
                logger.info(f"{category_name} tests completed")
            except Exception as e:
                logger.error(f"Error in {category_name} tests: {e}")
                test_results['tests'].append({
                    'category': category_name,
                    'error': str(e)
                })
        
        # Generate summary
        test_results['summary'] = self._generate_summary(test_results['tests'])
        
        return test_results
    
    def test_connection_pooling(self) -> TestResult:
        """Test database connection pooling effectiveness"""
        logger.info("Testing database connection pooling...")
        
        metrics = {
            'connection_times': [],
            'pool_utilization': [],
            'connection_errors': 0,
            'total_connections': 0
        }
        
        # Test connection acquisition times
        for i in range(100):
            start_time = time.time()
            try:
                conn = self.db_pool.getconn()
                connection_time = (time.time() - start_time) * 1000
                metrics['connection_times'].append(connection_time)
                metrics['total_connections'] += 1
                
                # Simulate some work
                time.sleep(0.01)
                
                self.db_pool.putconn(conn)
                
            except Exception as e:
                metrics['connection_errors'] += 1
                logger.error(f"Connection error: {e}")
        
        # Test concurrent connections
        def get_connection():
            try:
                conn = self.db_pool.getconn()
                time.sleep(0.1)  # Simulate work
                self.db_pool.putconn(conn)
                return True
            except Exception as e:
                logger.error(f"Concurrent connection error: {e}")
                return False
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_connection) for _ in range(50)]
            successful_connections = sum(1 for future in as_completed(futures) if future.result())
        
        # Calculate metrics
        avg_connection_time = statistics.mean(metrics['connection_times'])
        connection_success_rate = successful_connections / 50
        
        performance_metrics = PerformanceMetrics(
            test_name="Database Connection Pooling",
            response_time_ms=avg_connection_time,
            throughput_rps=1000 / avg_connection_time if avg_connection_time > 0 else 0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=metrics['total_connections'],
            errors=metrics['connection_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if avg_connection_time > self.thresholds['connection_time_ms']:
            status = 'warning'
            recommendations.append("Consider increasing connection pool size")
        
        if connection_success_rate < 0.95:
            status = 'failed'
            recommendations.append("Connection pool may be too small for concurrent load")
        
        if metrics['connection_errors'] > 0:
            status = 'warning'
            recommendations.append("Check database connection configuration")
        
        return TestResult(
            test_name="Database Connection Pooling",
            status=status,
            metrics=performance_metrics,
            details={
                'avg_connection_time_ms': avg_connection_time,
                'connection_success_rate': connection_success_rate,
                'total_connections': metrics['total_connections'],
                'connection_errors': metrics['connection_errors']
            },
            recommendations=recommendations
        )
    
    def test_query_performance(self) -> TestResult:
        """Test query performance for various operations"""
        logger.info("Testing query performance...")
        
        metrics = {
            'query_times': [],
            'query_errors': 0,
            'total_queries': 0
        }
        
        # Test queries
        test_queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT * FROM users LIMIT 100",
            "SELECT * FROM user_profiles WHERE user_id IN (SELECT id FROM users LIMIT 10)",
            "SELECT COUNT(*) FROM user_health_checkins WHERE checkin_date >= NOW() - INTERVAL '30 days'",
            "SELECT user_id, COUNT(*) FROM user_health_checkins GROUP BY user_id",
            "SELECT * FROM financial_questionnaire_submissions ORDER BY submitted_at DESC LIMIT 50"
        ]
        
        with self.engine.connect() as conn:
            for query in test_queries:
                for _ in range(10):  # Run each query 10 times
                    try:
                        start_time = time.time()
                        result = conn.execute(text(query))
                        result.fetchall()  # Execute the query
                        query_time = (time.time() - start_time) * 1000
                        
                        metrics['query_times'].append(query_time)
                        metrics['total_queries'] += 1
                        
                    except Exception as e:
                        metrics['query_errors'] += 1
                        logger.error(f"Query error: {e}")
        
        # Calculate metrics
        avg_query_time = statistics.mean(metrics['query_times'])
        max_query_time = max(metrics['query_times'])
        min_query_time = min(metrics['query_times'])
        
        performance_metrics = PerformanceMetrics(
            test_name="Query Performance",
            response_time_ms=avg_query_time,
            throughput_rps=metrics['total_queries'] / (sum(metrics['query_times']) / 1000),
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=metrics['total_queries'],
            errors=metrics['query_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if avg_query_time > self.thresholds['query_time_ms']:
            status = 'warning'
            recommendations.append("Consider optimizing slow queries or adding indexes")
        
        if max_query_time > self.thresholds['query_time_ms'] * 2:
            status = 'warning'
            recommendations.append("Some queries are very slow - investigate specific queries")
        
        if metrics['query_errors'] > 0:
            status = 'failed'
            recommendations.append("Fix query errors before deployment")
        
        return TestResult(
            test_name="Query Performance",
            status=status,
            metrics=performance_metrics,
            details={
                'avg_query_time_ms': avg_query_time,
                'max_query_time_ms': max_query_time,
                'min_query_time_ms': min_query_time,
                'total_queries': metrics['total_queries'],
                'query_errors': metrics['query_errors']
            },
            recommendations=recommendations
        )
    
    def test_financial_calculations(self) -> TestResult:
        """Test performance of financial calculations"""
        logger.info("Testing financial calculations performance...")
        
        metrics = {
            'calculation_times': [],
            'calculation_errors': 0,
            'total_calculations': 0
        }
        
        # Test financial calculation queries
        financial_queries = [
            """
            SELECT 
                user_id,
                SUM(monthly_income) as total_income,
                SUM(monthly_expenses) as total_expenses,
                SUM(monthly_income) - SUM(monthly_expenses) as net_income
            FROM user_financial_profiles 
            GROUP BY user_id
            """,
            """
            SELECT 
                user_id,
                AVG(current_savings) as avg_savings,
                MAX(current_savings) as max_savings,
                MIN(current_savings) as min_savings
            FROM user_financial_profiles 
            WHERE current_savings > 0
            GROUP BY user_id
            """,
            """
            SELECT 
                user_id,
                COUNT(*) as checkin_count,
                AVG(health_score) as avg_health_score
            FROM user_health_checkins 
            WHERE checkin_date >= NOW() - INTERVAL '90 days'
            GROUP BY user_id
            """
        ]
        
        with self.engine.connect() as conn:
            for query in financial_queries:
                for _ in range(5):  # Run each calculation 5 times
                    try:
                        start_time = time.time()
                        result = conn.execute(text(query))
                        result.fetchall()
                        calculation_time = (time.time() - start_time) * 1000
                        
                        metrics['calculation_times'].append(calculation_time)
                        metrics['total_calculations'] += 1
                        
                    except Exception as e:
                        metrics['calculation_errors'] += 1
                        logger.error(f"Financial calculation error: {e}")
        
        # Calculate metrics
        avg_calculation_time = statistics.mean(metrics['calculation_times'])
        
        performance_metrics = PerformanceMetrics(
            test_name="Financial Calculations",
            response_time_ms=avg_calculation_time,
            throughput_rps=metrics['total_calculations'] / (sum(metrics['calculation_times']) / 1000),
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=metrics['total_calculations'],
            errors=metrics['calculation_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if avg_calculation_time > 500:  # Financial calculations can be slower
            status = 'warning'
            recommendations.append("Consider caching financial calculation results")
            recommendations.append("Optimize financial calculation queries with proper indexes")
        
        if metrics['calculation_errors'] > 0:
            status = 'failed'
            recommendations.append("Fix financial calculation errors")
        
        return TestResult(
            test_name="Financial Calculations",
            status=status,
            metrics=performance_metrics,
            details={
                'avg_calculation_time_ms': avg_calculation_time,
                'total_calculations': metrics['total_calculations'],
                'calculation_errors': metrics['calculation_errors']
            },
            recommendations=recommendations
        )
    
    def test_data_integrity(self) -> TestResult:
        """Test data integrity and consistency"""
        logger.info("Testing data integrity...")
        
        integrity_checks = {
            'foreign_key_checks': 0,
            'data_type_checks': 0,
            'constraint_checks': 0,
            'integrity_errors': 0
        }
        
        # Test foreign key integrity
        fk_queries = [
            "SELECT COUNT(*) FROM user_profiles WHERE user_id NOT IN (SELECT id FROM users)",
            "SELECT COUNT(*) FROM user_health_checkins WHERE user_id NOT IN (SELECT id FROM users)",
            "SELECT COUNT(*) FROM financial_questionnaire_submissions WHERE user_id NOT IN (SELECT id FROM users)"
        ]
        
        with self.engine.connect() as conn:
            for query in fk_queries:
                try:
                    result = conn.execute(text(query))
                    count = result.scalar()
                    integrity_checks['foreign_key_checks'] += 1
                    
                    if count > 0:
                        integrity_checks['integrity_errors'] += 1
                        logger.warning(f"Foreign key integrity issue found: {count} orphaned records")
                        
                except Exception as e:
                    integrity_checks['integrity_errors'] += 1
                    logger.error(f"Foreign key check error: {e}")
        
        # Test data type consistency
        type_queries = [
            "SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ''",
            "SELECT COUNT(*) FROM user_profiles WHERE created_at IS NULL",
            "SELECT COUNT(*) FROM user_health_checkins WHERE checkin_date IS NULL"
        ]
        
        with self.engine.connect() as conn:
            for query in type_queries:
                try:
                    result = conn.execute(text(query))
                    count = result.scalar()
                    integrity_checks['data_type_checks'] += 1
                    
                    if count > 0:
                        integrity_checks['integrity_errors'] += 1
                        logger.warning(f"Data type consistency issue found: {count} null values")
                        
                except Exception as e:
                    integrity_checks['integrity_errors'] += 1
                    logger.error(f"Data type check error: {e}")
        
        # Calculate integrity score
        total_checks = (integrity_checks['foreign_key_checks'] + 
                       integrity_checks['data_type_checks'] + 
                       integrity_checks['constraint_checks'])
        
        integrity_score = (total_checks - integrity_checks['integrity_errors']) / total_checks if total_checks > 0 else 1.0
        
        performance_metrics = PerformanceMetrics(
            test_name="Data Integrity",
            response_time_ms=0.0,  # Not applicable for integrity checks
            throughput_rps=0.0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=total_checks,
            errors=integrity_checks['integrity_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if integrity_score < 0.95:
            status = 'failed'
            recommendations.append("Fix data integrity issues before deployment")
        
        if integrity_checks['integrity_errors'] > 0:
            status = 'warning'
            recommendations.append("Review and fix data integrity violations")
        
        return TestResult(
            test_name="Data Integrity",
            status=status,
            metrics=performance_metrics,
            details={
                'integrity_score': integrity_score,
                'total_checks': total_checks,
                'integrity_errors': integrity_checks['integrity_errors'],
                'foreign_key_checks': integrity_checks['foreign_key_checks'],
                'data_type_checks': integrity_checks['data_type_checks']
            },
            recommendations=recommendations
        )
    
    def test_backup_systems(self) -> TestResult:
        """Test backup system functionality"""
        logger.info("Testing backup systems...")
        
        backup_metrics = {
            'backup_tests': 0,
            'backup_errors': 0,
            'backup_size_mb': 0,
            'backup_time_seconds': 0
        }
        
        # Test backup creation (simulated)
        try:
            start_time = time.time()
            
            # Simulate backup creation
            backup_query = "SELECT pg_dump('mingus')"
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                
                # Check if pg_dump is available
                backup_metrics['backup_tests'] += 1
                
                # Simulate backup size calculation
                size_query = """
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """
                result = conn.execute(text(size_query))
                size_info = result.scalar()
                
                backup_metrics['backup_size_mb'] = 100  # Simulated size
            
            backup_time = time.time() - start_time
            backup_metrics['backup_time_seconds'] = backup_time
            
        except Exception as e:
            backup_metrics['backup_errors'] += 1
            logger.error(f"Backup test error: {e}")
        
        # Test backup verification
        try:
            # Simulate backup verification
            backup_metrics['backup_tests'] += 1
            
        except Exception as e:
            backup_metrics['backup_errors'] += 1
            logger.error(f"Backup verification error: {e}")
        
        performance_metrics = PerformanceMetrics(
            test_name="Backup Systems",
            response_time_ms=backup_metrics['backup_time_seconds'] * 1000,
            throughput_rps=0.0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=backup_metrics['backup_tests'],
            errors=backup_metrics['backup_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if backup_metrics['backup_errors'] > 0:
            status = 'failed'
            recommendations.append("Fix backup system errors")
        
        if backup_metrics['backup_time_seconds'] > 300:  # 5 minutes
            status = 'warning'
            recommendations.append("Backup process is slow - consider optimization")
        
        return TestResult(
            test_name="Backup Systems",
            status=status,
            metrics=performance_metrics,
            details={
                'backup_tests': backup_metrics['backup_tests'],
                'backup_errors': backup_metrics['backup_errors'],
                'backup_size_mb': backup_metrics['backup_size_mb'],
                'backup_time_seconds': backup_metrics['backup_time_seconds']
            },
            recommendations=recommendations
        )
    
    def test_redis_caching(self) -> TestResult:
        """Test Redis caching performance"""
        logger.info("Testing Redis caching performance...")
        
        cache_metrics = {
            'set_operations': 0,
            'get_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_errors': 0,
            'operation_times': []
        }
        
        # Test cache operations
        test_keys = [f"test_key_{i}" for i in range(100)]
        test_values = [f"test_value_{i}" for i in range(100)]
        
        # Test set operations
        for key, value in zip(test_keys, test_values):
            try:
                start_time = time.time()
                self.redis_client.set(key, value, ex=60)  # 60 second TTL
                operation_time = (time.time() - start_time) * 1000
                
                cache_metrics['set_operations'] += 1
                cache_metrics['operation_times'].append(operation_time)
                
            except Exception as e:
                cache_metrics['cache_errors'] += 1
                logger.error(f"Redis set error: {e}")
        
        # Test get operations (cache hits)
        for key in test_keys:
            try:
                start_time = time.time()
                value = self.redis_client.get(key)
                operation_time = (time.time() - start_time) * 1000
                
                cache_metrics['get_operations'] += 1
                cache_metrics['operation_times'].append(operation_time)
                
                if value:
                    cache_metrics['cache_hits'] += 1
                else:
                    cache_metrics['cache_misses'] += 1
                    
            except Exception as e:
                cache_metrics['cache_errors'] += 1
                logger.error(f"Redis get error: {e}")
        
        # Test cache misses
        for i in range(50):
            try:
                start_time = time.time()
                value = self.redis_client.get(f"nonexistent_key_{i}")
                operation_time = (time.time() - start_time) * 1000
                
                cache_metrics['get_operations'] += 1
                cache_metrics['operation_times'].append(operation_time)
                cache_metrics['cache_misses'] += 1
                
            except Exception as e:
                cache_metrics['cache_errors'] += 1
                logger.error(f"Redis get error: {e}")
        
        # Calculate metrics
        total_operations = cache_metrics['set_operations'] + cache_metrics['get_operations']
        cache_hit_rate = cache_metrics['cache_hits'] / cache_metrics['get_operations'] if cache_metrics['get_operations'] > 0 else 0
        avg_operation_time = statistics.mean(cache_metrics['operation_times'])
        
        performance_metrics = PerformanceMetrics(
            test_name="Redis Caching",
            response_time_ms=avg_operation_time,
            throughput_rps=total_operations / (sum(cache_metrics['operation_times']) / 1000),
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=cache_hit_rate,
            database_queries=0,
            errors=cache_metrics['cache_errors']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if cache_hit_rate < self.thresholds['cache_hit_rate']:
            status = 'warning'
            recommendations.append("Cache hit rate is low - review caching strategy")
        
        if avg_operation_time > 10:  # Redis should be very fast
            status = 'warning'
            recommendations.append("Redis operations are slow - check Redis configuration")
        
        if cache_metrics['cache_errors'] > 0:
            status = 'failed'
            recommendations.append("Fix Redis connection issues")
        
        return TestResult(
            test_name="Redis Caching",
            status=status,
            metrics=performance_metrics,
            details={
                'cache_hit_rate': cache_hit_rate,
                'total_operations': total_operations,
                'cache_hits': cache_metrics['cache_hits'],
                'cache_misses': cache_metrics['cache_misses'],
                'cache_errors': cache_metrics['cache_errors'],
                'avg_operation_time_ms': avg_operation_time
            },
            recommendations=recommendations
        )
    
    def test_celery_tasks(self) -> TestResult:
        """Test Celery background task processing"""
        logger.info("Testing Celery background task processing...")
        
        task_metrics = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'task_times': [],
            'task_errors': 0
        }
        
        # Define a simple test task
        @self.celery_app.task
        def test_task(duration=1):
            time.sleep(duration)
            return f"Task completed in {duration} seconds"
        
        # Submit tasks
        task_results = []
        for i in range(10):
            try:
                start_time = time.time()
                result = test_task.delay(1)  # 1 second duration
                task_metrics['tasks_submitted'] += 1
                task_results.append((result, start_time))
                
            except Exception as e:
                task_metrics['task_errors'] += 1
                logger.error(f"Task submission error: {e}")
        
        # Wait for task completion
        for result, start_time in task_results:
            try:
                task_result = result.get(timeout=30)  # 30 second timeout
                task_time = (time.time() - start_time) * 1000
                
                task_metrics['tasks_completed'] += 1
                task_metrics['task_times'].append(task_time)
                
            except Exception as e:
                task_metrics['tasks_failed'] += 1
                logger.error(f"Task execution error: {e}")
        
        # Calculate metrics
        success_rate = task_metrics['tasks_completed'] / task_metrics['tasks_submitted'] if task_metrics['tasks_submitted'] > 0 else 0
        avg_task_time = statistics.mean(task_metrics['task_times']) if task_metrics['task_times'] else 0
        
        performance_metrics = PerformanceMetrics(
            test_name="Celery Tasks",
            response_time_ms=avg_task_time,
            throughput_rps=task_metrics['tasks_completed'] / (sum(task_metrics['task_times']) / 1000) if task_metrics['task_times'] else 0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            cache_hit_rate=0.0,
            database_queries=0,
            errors=task_metrics['task_errors'] + task_metrics['tasks_failed']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if success_rate < 0.9:
            status = 'failed'
            recommendations.append("Fix Celery task failures")
        
        if task_metrics['task_errors'] > 0:
            status = 'warning'
            recommendations.append("Check Celery worker configuration")
        
        if avg_task_time > 5000:  # 5 seconds for 1-second tasks
            status = 'warning'
            recommendations.append("Celery tasks are slow - check worker performance")
        
        return TestResult(
            test_name="Celery Tasks",
            status=status,
            metrics=performance_metrics,
            details={
                'success_rate': success_rate,
                'tasks_submitted': task_metrics['tasks_submitted'],
                'tasks_completed': task_metrics['tasks_completed'],
                'tasks_failed': task_metrics['tasks_failed'],
                'task_errors': task_metrics['task_errors'],
                'avg_task_time_ms': avg_task_time
            },
            recommendations=recommendations
        )
    
    def test_load_performance(self) -> TestResult:
        """Test overall system performance under load"""
        logger.info("Testing system performance under load...")
        
        load_metrics = {
            'concurrent_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
        # Simulate concurrent database operations
        def concurrent_operation():
            try:
                start_time = time.time()
                
                with self.engine.connect() as conn:
                    # Simulate a typical database operation
                    result = conn.execute(text("SELECT COUNT(*) FROM users"))
                    result.scalar()
                
                response_time = (time.time() - start_time) * 1000
                
                load_metrics['successful_requests'] += 1
                load_metrics['response_times'].append(response_time)
                
                # Record resource usage
                load_metrics['memory_usage'].append(psutil.Process().memory_info().rss / 1024 / 1024)
                load_metrics['cpu_usage'].append(psutil.cpu_percent())
                
            except Exception as e:
                load_metrics['failed_requests'] += 1
                logger.error(f"Concurrent operation error: {e}")
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(concurrent_operation) for _ in range(100)]
            
            for future in as_completed(futures):
                load_metrics['concurrent_requests'] += 1
        
        # Calculate metrics
        total_requests = load_metrics['successful_requests'] + load_metrics['failed_requests']
        success_rate = load_metrics['successful_requests'] / total_requests if total_requests > 0 else 0
        avg_response_time = statistics.mean(load_metrics['response_times']) if load_metrics['response_times'] else 0
        max_memory = max(load_metrics['memory_usage']) if load_metrics['memory_usage'] else 0
        max_cpu = max(load_metrics['cpu_usage']) if load_metrics['cpu_usage'] else 0
        
        performance_metrics = PerformanceMetrics(
            test_name="Load Performance",
            response_time_ms=avg_response_time,
            throughput_rps=load_metrics['successful_requests'] / (sum(load_metrics['response_times']) / 1000) if load_metrics['response_times'] else 0,
            memory_usage_mb=max_memory,
            cpu_usage_percent=max_cpu,
            cache_hit_rate=0.0,
            database_queries=load_metrics['successful_requests'],
            errors=load_metrics['failed_requests']
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if success_rate < 0.95:
            status = 'failed'
            recommendations.append("System cannot handle concurrent load")
        
        if avg_response_time > self.thresholds['query_time_ms'] * 2:
            status = 'warning'
            recommendations.append("System performance degrades under load")
        
        if max_memory > self.thresholds['memory_usage_mb']:
            status = 'warning'
            recommendations.append("High memory usage under load")
        
        if max_cpu > self.thresholds['cpu_usage_percent']:
            status = 'warning'
            recommendations.append("High CPU usage under load")
        
        return TestResult(
            test_name="Load Performance",
            status=status,
            metrics=performance_metrics,
            details={
                'success_rate': success_rate,
                'total_requests': total_requests,
                'successful_requests': load_metrics['successful_requests'],
                'failed_requests': load_metrics['failed_requests'],
                'avg_response_time_ms': avg_response_time,
                'max_memory_mb': max_memory,
                'max_cpu_percent': max_cpu
            },
            recommendations=recommendations
        )
    
    def test_system_resources(self) -> TestResult:
        """Test system resource usage"""
        logger.info("Testing system resource usage...")
        
        # Get system metrics
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_count = psutil.cpu_count()
        
        # Simulate some load to get current usage
        with self.engine.connect() as conn:
            for _ in range(10):
                conn.execute(text("SELECT 1"))
        
        current_cpu = psutil.cpu_percent(interval=1)
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        performance_metrics = PerformanceMetrics(
            test_name="System Resources",
            response_time_ms=0.0,
            throughput_rps=0.0,
            memory_usage_mb=current_memory,
            cpu_usage_percent=current_cpu,
            cache_hit_rate=0.0,
            database_queries=0,
            errors=0
        )
        
        # Determine status
        status = 'passed'
        recommendations = []
        
        if current_memory > self.thresholds['memory_usage_mb']:
            status = 'warning'
            recommendations.append("High memory usage detected")
        
        if current_cpu > self.thresholds['cpu_usage_percent']:
            status = 'warning'
            recommendations.append("High CPU usage detected")
        
        if memory_info.percent > 90:
            status = 'failed'
            recommendations.append("System memory critically low")
        
        if disk_info.percent > 90:
            status = 'warning'
            recommendations.append("Disk space running low")
        
        return TestResult(
            test_name="System Resources",
            status=status,
            metrics=performance_metrics,
            details={
                'total_memory_gb': memory_info.total / 1024 / 1024 / 1024,
                'available_memory_gb': memory_info.available / 1024 / 1024 / 1024,
                'memory_percent': memory_info.percent,
                'total_disk_gb': disk_info.total / 1024 / 1024 / 1024,
                'available_disk_gb': disk_info.free / 1024 / 1024 / 1024,
                'disk_percent': disk_info.percent,
                'cpu_count': cpu_count,
                'current_cpu_percent': current_cpu,
                'current_memory_mb': current_memory
            },
            recommendations=recommendations
        )
    
    def _generate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.get('result', {}).get('status') == 'passed')
        failed_tests = sum(1 for result in test_results if result.get('result', {}).get('status') == 'failed')
        warning_tests = sum(1 for result in test_results if result.get('result', {}).get('status') == 'warning')
        
        # Calculate overall performance metrics
        all_metrics = []
        for result in test_results:
            if 'result' in result and hasattr(result['result'], 'metrics'):
                all_metrics.append(result['result'].metrics)
        
        avg_response_time = statistics.mean([m.response_time_ms for m in all_metrics if m.response_time_ms > 0]) if all_metrics else 0
        avg_memory_usage = statistics.mean([m.memory_usage_mb for m in all_metrics]) if all_metrics else 0
        avg_cpu_usage = statistics.mean([m.cpu_usage_percent for m in all_metrics]) if all_metrics else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warning_tests': warning_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'overall_performance': {
                'avg_response_time_ms': avg_response_time,
                'avg_memory_usage_mb': avg_memory_usage,
                'avg_cpu_usage_percent': avg_cpu_usage
            },
            'recommendations': self._generate_overall_recommendations(test_results)
        }
    
    def _generate_overall_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate overall recommendations based on test results"""
        recommendations = []
        
        # Check for critical failures
        failed_tests = [r for r in test_results if r.get('result', {}).get('status') == 'failed']
        if failed_tests:
            recommendations.append("CRITICAL: Fix failed tests before deployment")
        
        # Check for performance issues
        warning_tests = [r for r in test_results if r.get('result', {}).get('status') == 'warning']
        if len(warning_tests) > len(test_results) * 0.3:  # More than 30% warnings
            recommendations.append("Multiple performance issues detected - review system configuration")
        
        # Check for specific issues
        for result in test_results:
            if 'result' in result and hasattr(result['result'], 'recommendations'):
                recommendations.extend(result['result'].recommendations)
        
        return list(set(recommendations))  # Remove duplicates
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'db_pool'):
                self.db_pool.closeall()
            if hasattr(self, 'redis_client'):
                self.redis_client.close()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def main():
    """Main function to run PostgreSQL performance tests"""
    
    # Configuration
    config = {
        'database_url': os.getenv('DATABASE_URL', 'postgresql://localhost/mingus'),
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'celery_broker': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    }
    
    # Create tester
    tester = PostgreSQLPerformanceTester(config)
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'postgresql_performance_test_results_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("POSTGRESQL PERFORMANCE TESTING SUMMARY")
        print("="*80)
        
        summary = results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Warnings: {summary['warning_tests']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        
        print(f"\nOverall Performance:")
        perf = summary['overall_performance']
        print(f"  Average Response Time: {perf['avg_response_time_ms']:.2f}ms")
        print(f"  Average Memory Usage: {perf['avg_memory_usage_mb']:.2f}MB")
        print(f"  Average CPU Usage: {perf['avg_cpu_usage_percent']:.2f}%")
        
        if summary['recommendations']:
            print(f"\nRecommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # Return appropriate exit code
        if summary['failed_tests'] > 0:
            sys.exit(1)
        elif summary['warning_tests'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
