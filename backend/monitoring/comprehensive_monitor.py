"""
Comprehensive Performance Monitoring System for Flask Financial Application
Integrates Flask, PostgreSQL, Redis, Celery monitoring with real-time metrics
"""

import time
import json
import threading
import logging
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import os
import sqlite3
from contextlib import contextmanager

# Flask imports
from flask import Flask, request, g, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# Redis imports
import redis
from redis.exceptions import RedisError

# Celery imports
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure

# Database monitoring
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

@dataclass
class DatabaseMetric:
    """Database performance metric"""
    query: str
    duration: float
    timestamp: datetime
    table: Optional[str] = None
    rows_affected: Optional[int] = None
    connection_pool_size: Optional[int] = None
    active_connections: Optional[int] = None
    slow_query: bool = False

@dataclass
class RedisMetric:
    """Redis performance metric"""
    operation: str
    key: str
    duration: float
    timestamp: datetime
    memory_usage: Optional[int] = None
    hit_rate: Optional[float] = None
    connection_pool_size: Optional[int] = None

@dataclass
class APIMetric:
    """API performance metric"""
    endpoint: str
    method: str
    duration: float
    timestamp: datetime
    status_code: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None

@dataclass
class CoreWebVital:
    """Core Web Vital metric"""
    metric_name: str  # LCP, FID, CLS, TTFB, etc.
    value: float
    timestamp: datetime
    page_url: str
    user_id: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None

@dataclass
class SystemMetric:
    """System performance metric"""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    network_io: Dict[str, int]
    timestamp: datetime

@dataclass
class CeleryMetric:
    """Celery task performance metric"""
    task_name: str
    duration: float
    timestamp: datetime
    success: bool
    queue_name: Optional[str] = None
    worker_name: Optional[str] = None
    retries: int = 0

class ComprehensivePerformanceMonitor:
    """
    Comprehensive performance monitoring system for Flask financial application
    Integrates monitoring for:
    - Flask application performance
    - PostgreSQL database queries
    - Redis cache operations
    - Celery task execution
    - Core Web Vitals
    - System resources
    """
    
    def __init__(self, app: Optional[Flask] = None, config: Optional[Dict[str, Any]] = None):
        self.app = app
        self.config = config or self._default_config()
        
        # Metrics storage
        self.db_metrics: List[DatabaseMetric] = []
        self.redis_metrics: List[RedisMetric] = []
        self.api_metrics: List[APIMetric] = []
        self.web_vitals: List[CoreWebVital] = []
        self.system_metrics: List[SystemMetric] = []
        self.celery_metrics: List[CeleryMetric] = []
        
        # Performance thresholds
        self.thresholds = self.config['performance_thresholds']
        
        # Memory management
        self.max_metrics_per_type = self.config['max_metrics_per_type']
        self.cleanup_interval = self.config['cleanup_interval_seconds']
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Database connection monitoring
        self.db_connections = {}
        self.redis_connections = {}
        
        # Start monitoring threads
        self._start_monitoring_threads()
        
        # Initialize Flask integration if app provided
        if app:
            self.init_app(app)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for comprehensive monitoring"""
        return {
            'performance_thresholds': {
                'slow_query_threshold_ms': 1000,
                'slow_api_threshold_ms': 2000,
                'slow_redis_threshold_ms': 100,
                'slow_celery_threshold_ms': 5000,
                'memory_usage_max_percent': 85,
                'cpu_usage_max_percent': 80,
                'disk_usage_max_percent': 90,
            },
            'max_metrics_per_type': 10000,
            'cleanup_interval_seconds': 3600,  # 1 hour
            'system_monitoring_interval': 60,  # 1 minute
            'database_monitoring_interval': 30,  # 30 seconds
            'redis_monitoring_interval': 30,  # 30 seconds
            'metrics_retention_days': 30,
            'enable_sql_logging': True,
            'enable_redis_logging': True,
            'enable_celery_logging': True,
            'enable_web_vitals': True,
        }
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        # System monitoring thread
        self.system_thread = threading.Thread(
            target=self._system_monitoring_worker, 
            daemon=True
        )
        self.system_thread.start()
        
        # Cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker, 
            daemon=True
        )
        self.cleanup_thread.start()
        
        logger.info("Performance monitoring threads started")
    
    def init_app(self, app: Flask):
        """Initialize Flask application monitoring"""
        self.app = app
        
        # Register Flask middleware
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        # Register error handlers
        app.register_error_handler(Exception, self._handle_exception)
        
        # Initialize database monitoring
        self._init_database_monitoring(app)
        
        # Initialize Redis monitoring
        self._init_redis_monitoring(app)
        
        # Initialize Celery monitoring
        self._init_celery_monitoring(app)
        
        logger.info("Flask application monitoring initialized")
    
    def _init_database_monitoring(self, app: Flask):
        """Initialize database performance monitoring"""
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            logger.warning("SQLAlchemy not found, database monitoring disabled")
            return
        
        db = app.extensions['sqlalchemy'].db
        
        # Monkey patch SQLAlchemy to capture query metrics
        original_execute = db.engine.execute
        
        def monitored_execute(*args, **kwargs):
            start_time = time.time()
            try:
                result = original_execute(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Extract query information
                query = str(args[0]) if args else "Unknown"
                table = self._extract_table_from_query(query)
                
                metric = DatabaseMetric(
                    query=query,
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    table=table,
                    rows_affected=getattr(result, 'rowcount', None),
                    slow_query=duration > self.thresholds['slow_query_threshold_ms']
                )
                
                self._add_db_metric(metric)
                
                # Log slow queries
                if metric.slow_query:
                    logger.warning(f"Slow database query detected: {duration:.2f}ms - {query}")
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Database query failed after {duration:.2f}ms: {e}")
                raise
        
        db.engine.execute = monitored_execute
        logger.info("Database performance monitoring initialized")
    
    def _init_redis_monitoring(self, app: Flask):
        """Initialize Redis performance monitoring"""
        if not hasattr(app, 'extensions') or 'cache' not in app.extensions:
            logger.warning("Flask-Cache not found, Redis monitoring disabled")
            return
        
        cache = app.extensions['cache']
        
        # Monitor Redis operations through Flask-Cache
        original_get = cache.get
        original_set = cache.set
        original_delete = cache.delete
        
        def monitored_get(key):
            start_time = time.time()
            try:
                result = original_get(key)
                duration = (time.time() - start_time) * 1000
                
                metric = RedisMetric(
                    operation='get',
                    key=key,
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    slow_query=duration > self.thresholds['slow_redis_threshold_ms']
                )
                
                self._add_redis_metric(metric)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Redis get operation failed after {duration:.2f}ms: {e}")
                raise
        
        def monitored_set(key, value, timeout=None):
            start_time = time.time()
            try:
                result = original_set(key, value, timeout)
                duration = (time.time() - start_time) * 1000
                
                metric = RedisMetric(
                    operation='set',
                    key=key,
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    slow_query=duration > self.thresholds['slow_redis_threshold_ms']
                )
                
                self._add_redis_metric(metric)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Redis set operation failed after {duration:.2f}ms: {e}")
                raise
        
        def monitored_delete(key):
            start_time = time.time()
            try:
                result = original_delete(key)
                duration = (time.time() - start_time) * 1000
                
                metric = RedisMetric(
                    operation='delete',
                    key=key,
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    slow_query=duration > self.thresholds['slow_redis_threshold_ms']
                )
                
                self._add_redis_metric(metric)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Redis delete operation failed after {duration:.2f}ms: {e}")
                raise
        
        cache.get = monitored_get
        cache.set = monitored_set
        cache.delete = monitored_delete
        logger.info("Redis performance monitoring initialized")
    
    def _init_celery_monitoring(self, app: Flask):
        """Initialize Celery performance monitoring"""
        if not hasattr(app, 'extensions') or 'celery' not in app.extensions:
            logger.warning("Celery not found, task monitoring disabled")
            return
        
        # Register Celery signal handlers
        @task_prerun.connect
        def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extras):
            g.celery_start_time = time.time()
        
        @task_postrun.connect
        def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extras):
            if hasattr(g, 'celery_start_time'):
                duration = (time.time() - g.celery_start_time) * 1000
                
                metric = CeleryMetric(
                    task_name=task.name if task else 'unknown',
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    success=state == 'SUCCESS',
                    queue_name=getattr(task, 'queue', None),
                    worker_name=getattr(task, 'worker', None),
                    slow_query=duration > self.thresholds['slow_celery_threshold_ms']
                )
                
                self._add_celery_metric(metric)
        
        @task_failure.connect
        def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extras):
            if hasattr(g, 'celery_start_time'):
                duration = (time.time() - g.celery_start_time) * 1000
                
                metric = CeleryMetric(
                    task_name=sender.name if sender else 'unknown',
                    duration=duration,
                    timestamp=datetime.utcnow(),
                    success=False,
                    queue_name=getattr(sender, 'queue', None),
                    worker_name=getattr(sender, 'worker', None)
                )
                
                self._add_celery_metric(metric)
        
        logger.info("Celery performance monitoring initialized")
    
    def _before_request(self):
        """Flask before_request handler for API monitoring"""
        g.start_time = time.time()
        g.request_data = {
            'method': request.method,
            'endpoint': request.endpoint,
            'url': request.url,
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr,
            'request_size': request.content_length
        }
    
    def _after_request(self, response):
        """Flask after_request handler for API monitoring"""
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            
            metric = APIMetric(
                endpoint=g.request_data['endpoint'],
                method=g.request_data['method'],
                duration=duration,
                timestamp=datetime.utcnow(),
                status_code=response.status_code,
                user_agent=g.request_data['user_agent'],
                ip_address=g.request_data['ip_address'],
                request_size=g.request_data['request_size'],
                response_size=len(response.get_data())
            )
            
            self._add_api_metric(metric)
            
            # Log slow API calls
            if duration > self.thresholds['slow_api_threshold_ms']:
                logger.warning(f"Slow API call detected: {duration:.2f}ms - {g.request_data['method']} {g.request_data['endpoint']}")
        
        return response
    
    def _teardown_request(self, exception=None):
        """Flask teardown_request handler"""
        pass
    
    def _handle_exception(self, exception):
        """Flask exception handler"""
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            
            metric = APIMetric(
                endpoint=g.request_data.get('endpoint', 'error'),
                method=g.request_data.get('method', 'UNKNOWN'),
                duration=duration,
                timestamp=datetime.utcnow(),
                status_code=500,
                user_agent=g.request_data.get('user_agent'),
                ip_address=g.request_data.get('ip_address'),
                request_size=g.request_data.get('request_size'),
                response_size=0
            )
            
            self._add_api_metric(metric)
    
    def _extract_table_from_query(self, query: str) -> Optional[str]:
        """Extract table name from SQL query"""
        query_lower = query.lower()
        
        # Simple table extraction logic
        if 'from ' in query_lower:
            parts = query_lower.split('from ')[1].split()
            if parts:
                return parts[0].strip('`"[]')
        
        if 'update ' in query_lower:
            parts = query_lower.split('update ')[1].split()
            if parts:
                return parts[0].strip('`"[]')
        
        if 'insert into ' in query_lower:
            parts = query_lower.split('insert into ')[1].split()
            if parts:
                return parts[0].strip('`"[]')
        
        return None
    
    def _add_db_metric(self, metric: DatabaseMetric):
        """Add database metric with thread safety"""
        with self.lock:
            self.db_metrics.append(metric)
            if len(self.db_metrics) > self.max_metrics_per_type:
                self.db_metrics.pop(0)
    
    def _add_redis_metric(self, metric: RedisMetric):
        """Add Redis metric with thread safety"""
        with self.lock:
            self.redis_metrics.append(metric)
            if len(self.redis_metrics) > self.max_metrics_per_type:
                self.redis_metrics.pop(0)
    
    def _add_api_metric(self, metric: APIMetric):
        """Add API metric with thread safety"""
        with self.lock:
            self.api_metrics.append(metric)
            if len(self.api_metrics) > self.max_metrics_per_type:
                self.api_metrics.pop(0)
    
    def _add_celery_metric(self, metric: CeleryMetric):
        """Add Celery metric with thread safety"""
        with self.lock:
            self.celery_metrics.append(metric)
            if len(self.celery_metrics) > self.max_metrics_per_type:
                self.celery_metrics.pop(0)
    
    def add_web_vital(self, metric: CoreWebVital):
        """Add Core Web Vital metric"""
        with self.lock:
            self.web_vitals.append(metric)
            if len(self.web_vitals) > self.max_metrics_per_type:
                self.web_vitals.pop(0)
    
    def _system_monitoring_worker(self):
        """Background worker for system metrics collection"""
        while True:
            try:
                # CPU and memory
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                metric = SystemMetric(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_available=memory.available,
                    disk_usage_percent=disk.percent,
                    network_io={
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv
                    },
                    timestamp=datetime.utcnow()
                )
                
                with self.lock:
                    self.system_metrics.append(metric)
                    if len(self.system_metrics) > self.max_metrics_per_type:
                        self.system_metrics.pop(0)
                
                # Check thresholds and log warnings
                if cpu_percent > self.thresholds['cpu_usage_max_percent']:
                    logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
                if memory.percent > self.thresholds['memory_usage_max_percent']:
                    logger.warning(f"High memory usage: {memory.percent:.1f}%")
                
                if disk.percent > self.thresholds['disk_usage_max_percent']:
                    logger.warning(f"High disk usage: {disk.percent:.1f}%")
                
                time.sleep(self.config['system_monitoring_interval'])
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _cleanup_worker(self):
        """Background worker for metrics cleanup"""
        while True:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=self.config['metrics_retention_days'])
                
                with self.lock:
                    # Clean up old metrics
                    self.db_metrics = [m for m in self.db_metrics if m.timestamp > cutoff_date]
                    self.redis_metrics = [m for m in self.redis_metrics if m.timestamp > cutoff_date]
                    self.api_metrics = [m for m in self.api_metrics if m.timestamp > cutoff_date]
                    self.web_vitals = [m for m in self.web_vitals if m.timestamp > cutoff_date]
                    self.system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_date]
                    self.celery_metrics = [m for m in self.celery_metrics if m.timestamp > cutoff_date]
                
                logger.info("Metrics cleanup completed")
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self.lock:
            return {
                'database': {
                    'total_queries': len(self.db_metrics),
                    'slow_queries': len([m for m in self.db_metrics if m.slow_query]),
                    'avg_duration': sum(m.duration for m in self.db_metrics) / len(self.db_metrics) if self.db_metrics else 0,
                    'recent_queries': [asdict(m) for m in self.db_metrics[-10:]]
                },
                'redis': {
                    'total_operations': len(self.redis_metrics),
                    'slow_operations': len([m for m in self.redis_metrics if m.slow_query]),
                    'avg_duration': sum(m.duration for m in self.redis_metrics) / len(self.redis_metrics) if self.redis_metrics else 0,
                    'recent_operations': [asdict(m) for m in self.redis_metrics[-10:]]
                },
                'api': {
                    'total_requests': len(self.api_metrics),
                    'slow_requests': len([m for m in self.api_metrics if m.duration > self.thresholds['slow_api_threshold_ms']]),
                    'avg_response_time': sum(m.duration for m in self.api_metrics) / len(self.api_metrics) if self.api_metrics else 0,
                    'status_codes': self._get_status_code_distribution(),
                    'recent_requests': [asdict(m) for m in self.api_metrics[-10:]]
                },
                'celery': {
                    'total_tasks': len(self.celery_metrics),
                    'successful_tasks': len([m for m in self.celery_metrics if m.success]),
                    'failed_tasks': len([m for m in self.celery_metrics if not m.success]),
                    'avg_duration': sum(m.duration for m in self.celery_metrics) / len(self.celery_metrics) if self.celery_metrics else 0,
                    'recent_tasks': [asdict(m) for m in self.celery_metrics[-10:]]
                },
                'web_vitals': {
                    'total_metrics': len(self.web_vitals),
                    'recent_metrics': [asdict(m) for m in self.web_vitals[-10:]]
                },
                'system': {
                    'total_metrics': len(self.system_metrics),
                    'current_cpu': self.system_metrics[-1].cpu_percent if self.system_metrics else 0,
                    'current_memory': self.system_metrics[-1].memory_percent if self.system_metrics else 0,
                    'current_disk': self.system_metrics[-1].disk_usage_percent if self.system_metrics else 0,
                    'recent_metrics': [asdict(m) for m in self.system_metrics[-10:]]
                },
                'thresholds': self.thresholds,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _get_status_code_distribution(self) -> Dict[str, int]:
        """Get distribution of HTTP status codes"""
        distribution = defaultdict(int)
        for metric in self.api_metrics:
            distribution[str(metric.status_code)] += 1
        return dict(distribution)
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        summary = self.get_metrics_summary()
        
        if format.lower() == 'json':
            return json.dumps(summary, indent=2, default=str)
        elif format.lower() == 'csv':
            return self._export_csv(summary)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self, summary: Dict[str, Any]) -> str:
        """Export metrics summary to CSV format"""
        # Implementation for CSV export
        # This is a simplified version - you might want to expand this
        lines = []
        lines.append("Metric Type,Total Count,Slow Count,Average Duration")
        
        for metric_type, data in summary.items():
            if isinstance(data, dict) and 'total_queries' in data:
                lines.append(f"{metric_type},{data.get('total_queries', 0)},{data.get('slow_queries', 0)},{data.get('avg_duration', 0):.2f}")
        
        return "\n".join(lines)
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.db_metrics.clear()
            self.redis_metrics.clear()
            self.api_metrics.clear()
            self.web_vitals.clear()
            self.system_metrics.clear()
            self.celery_metrics.clear()
        
        logger.info("All metrics reset")

# Global instance
comprehensive_monitor = ComprehensivePerformanceMonitor()

# Decorator for monitoring specific functions
def monitor_performance(operation_type: str = 'custom'):
    """Decorator to monitor performance of specific functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Create appropriate metric based on operation type
                if operation_type == 'database':
                    metric = DatabaseMetric(
                        query=f"{func.__name__}()",
                        duration=duration,
                        timestamp=datetime.utcnow(),
                        slow_query=duration > comprehensive_monitor.thresholds['slow_query_threshold_ms']
                    )
                    comprehensive_monitor._add_db_metric(metric)
                elif operation_type == 'redis':
                    metric = RedisMetric(
                        operation=func.__name__,
                        key='custom',
                        duration=duration,
                        timestamp=datetime.utcnow(),
                        slow_query=duration > comprehensive_monitor.thresholds['slow_redis_threshold_ms']
                    )
                    comprehensive_monitor._add_redis_metric(metric)
                elif operation_type == 'api':
                    metric = APIMetric(
                        endpoint=func.__name__,
                        method='CUSTOM',
                        duration=duration,
                        timestamp=datetime.utcnow(),
                        status_code=200,
                        slow_query=duration > comprehensive_monitor.thresholds['slow_api_threshold_ms']
                    )
                    comprehensive_monitor._add_api_metric(metric)
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Function {func.__name__} failed after {duration:.2f}ms: {e}")
                raise
        
        return wrapper
    return decorator
