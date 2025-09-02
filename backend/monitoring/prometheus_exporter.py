"""
Prometheus Metrics Exporter
Converts application performance metrics to Prometheus format
"""

import time
import threading
from typing import Dict, Any, List
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, HistogramMetricFamily

from .comprehensive_monitor import comprehensive_monitor

class PrometheusMetricsExporter:
    """
    Prometheus metrics exporter for Flask financial application
    Exports metrics in Prometheus format for integration with monitoring systems
    """
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or REGISTRY
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Flask API metrics
        self.flask_requests_total = Counter(
            'flask_requests_total',
            'Total number of Flask requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.flask_request_duration_seconds = Histogram(
            'flask_request_duration_seconds',
            'Flask request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # Database metrics
        self.database_queries_total = Counter(
            'database_queries_total',
            'Total number of database queries',
            ['table', 'slow_query'],
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['table'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Number of active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.database_connections_idle = Gauge(
            'database_connections_idle',
            'Number of idle database connections',
            ['database'],
            registry=self.registry
        )
        
        # Redis metrics
        self.redis_operations_total = Counter(
            'redis_operations_total',
            'Total number of Redis operations',
            ['operation', 'slow_operation'],
            registry=self.registry
        )
        
        self.redis_operation_duration_seconds = Histogram(
            'redis_operation_duration_seconds',
            'Redis operation duration in seconds',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
            registry=self.registry
        )
        
        self.redis_memory_usage_bytes = Gauge(
            'redis_memory_usage_bytes',
            'Redis memory usage in bytes',
            registry=self.registry
        )
        
        self.redis_hit_rate = Gauge(
            'redis_hit_rate',
            'Redis cache hit rate (0-1)',
            registry=self.registry
        )
        
        # Celery metrics
        self.celery_tasks_total = Counter(
            'celery_tasks_total',
            'Total number of Celery tasks',
            ['task_name', 'queue_name', 'success'],
            registry=self.registry
        )
        
        self.celery_task_duration_seconds = Histogram(
            'celery_task_duration_seconds',
            'Celery task duration in seconds',
            ['task_name', 'queue_name'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        self.celery_workers_active = Gauge(
            'celery_workers_active',
            'Number of active Celery workers',
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_percent = Gauge(
            'system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_percent = Gauge(
            'system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_memory_available_bytes = Gauge(
            'system_memory_available_bytes',
            'System available memory in bytes',
            registry=self.registry
        )
        
        self.system_disk_percent = Gauge(
            'system_disk_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        self.system_network_bytes_sent = Counter(
            'system_network_bytes_sent',
            'Total network bytes sent',
            registry=self.registry
        )
        
        self.system_network_bytes_received = Counter(
            'system_network_bytes_received',
            'Total network bytes received',
            registry=self.registry
        )
        
        # Web Vitals metrics
        self.web_vitals_lcp = Histogram(
            'web_vitals_lcp_seconds',
            'Largest Contentful Paint in seconds',
            ['page_url', 'device_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0],
            registry=self.registry
        )
        
        self.web_vitals_fid = Histogram(
            'web_vitals_fid_seconds',
            'First Input Delay in seconds',
            ['page_url', 'device_type'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
            registry=self.registry
        )
        
        self.web_vitals_cls = Histogram(
            'web_vitals_cls',
            'Cumulative Layout Shift',
            ['page_url', 'device_type'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
            registry=self.registry
        )
        
        self.web_vitals_ttfb = Histogram(
            'web_vitals_ttfb_seconds',
            'Time to First Byte in seconds',
            ['page_url', 'device_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )
        
        # Business metrics
        self.financial_transactions_total = Counter(
            'financial_transactions_total',
            'Total number of financial transactions',
            ['transaction_type', 'status'],
            registry=self.registry
        )
        
        self.financial_transaction_amount = Histogram(
            'financial_transaction_amount',
            'Financial transaction amounts',
            ['transaction_type'],
            buckets=[10, 100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            ['user_type'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        self.error_rate = Gauge(
            'error_rate',
            'Error rate percentage',
            ['error_type'],
            registry=self.registry
        )
    
    def update_metrics(self):
        """Update all Prometheus metrics from the comprehensive monitor"""
        try:
            # Update Flask API metrics
            self._update_flask_metrics()
            
            # Update database metrics
            self._update_database_metrics()
            
            # Update Redis metrics
            self._update_redis_metrics()
            
            # Update Celery metrics
            self._update_celery_metrics()
            
            # Update system metrics
            self._update_system_metrics()
            
            # Update web vitals metrics
            self._update_web_vitals_metrics()
            
        except Exception as e:
            # Log error but don't fail the metrics update
            print(f"Error updating Prometheus metrics: {e}")
    
    def _update_flask_metrics(self):
        """Update Flask API metrics"""
        with comprehensive_monitor.lock:
            api_metrics = comprehensive_monitor.api_metrics.copy()
        
        for metric in api_metrics:
            # Update request counter
            self.flask_requests_total.labels(
                method=metric.method,
                endpoint=metric.endpoint,
                status_code=str(metric.status_code)
            ).inc()
            
            # Update duration histogram
            self.flask_request_duration_seconds.labels(
                method=metric.method,
                endpoint=metric.endpoint
            ).observe(metric.duration / 1000.0)  # Convert ms to seconds
    
    def _update_database_metrics(self):
        """Update database metrics"""
        with comprehensive_monitor.lock:
            db_metrics = comprehensive_monitor.db_metrics.copy()
        
        for metric in db_metrics:
            # Update query counter
            self.database_queries_total.labels(
                table=metric.table or 'unknown',
                slow_query=str(metric.slow_query).lower()
            ).inc()
            
            # Update duration histogram
            self.database_query_duration_seconds.labels(
                table=metric.table or 'unknown'
            ).observe(metric.duration / 1000.0)  # Convert ms to seconds
    
    def _update_redis_metrics(self):
        """Update Redis metrics"""
        with comprehensive_monitor.lock:
            redis_metrics = comprehensive_monitor.redis_metrics.copy()
        
        for metric in redis_metrics:
            # Update operation counter
            self.redis_operations_total.labels(
                operation=metric.operation,
                slow_operation=str(metric.slow_query).lower()
            ).inc()
            
            # Update duration histogram
            self.redis_operation_duration_seconds.labels(
                operation=metric.operation
            ).observe(metric.duration / 1000.0)  # Convert ms to seconds
    
    def _update_celery_metrics(self):
        """Update Celery metrics"""
        with comprehensive_monitor.lock:
            celery_metrics = comprehensive_monitor.celery_metrics.copy()
        
        for metric in celery_metrics:
            # Update task counter
            self.celery_tasks_total.labels(
                task_name=metric.task_name,
                queue_name=metric.queue_name or 'default',
                success=str(metric.success).lower()
            ).inc()
            
            # Update duration histogram
            self.celery_task_duration_seconds.labels(
                task_name=metric.task_name,
                queue_name=metric.queue_name or 'default'
            ).observe(metric.duration / 1000.0)  # Convert ms to seconds
    
    def _update_system_metrics(self):
        """Update system metrics"""
        with comprehensive_monitor.lock:
            system_metrics = comprehensive_monitor.system_metrics.copy()
        
        if system_metrics:
            latest = system_metrics[-1]
            
            # Update current system metrics
            self.system_cpu_percent.set(latest.cpu_percent)
            self.system_memory_percent.set(latest.memory_percent)
            self.system_memory_available_bytes.set(latest.memory_available)
            self.system_disk_percent.set(latest.disk_usage_percent)
            
            # Update network counters (these are cumulative)
            # Note: In a real implementation, you'd want to track deltas
            self.system_network_bytes_sent.inc(latest.network_io.get('bytes_sent', 0))
            self.system_network_bytes_received.inc(latest.network_io.get('bytes_recv', 0))
    
    def _update_web_vitals_metrics(self):
        """Update Core Web Vitals metrics"""
        with comprehensive_monitor.lock:
            web_vitals = comprehensive_monitor.web_vitals.copy()
        
        for vital in web_vitals:
            device_type = vital.device_type or 'unknown'
            
            if vital.metric_name.upper() == 'LCP':
                self.web_vitals_lcp.labels(
                    page_url=vital.page_url,
                    device_type=device_type
                ).observe(vital.value)
            
            elif vital.metric_name.upper() == 'FID':
                self.web_vitals_fid.labels(
                    page_url=vital.page_url,
                    device_type=device_type
                ).observe(vital.value)
            
            elif vital.metric_name.upper() == 'CLS':
                self.web_vitals_cls.labels(
                    page_url=vital.page_url,
                    device_type=device_type
                ).observe(vital.value)
            
            elif vital.metric_name.upper() == 'TTFB':
                self.web_vitals_ttfb.labels(
                    page_url=vital.page_url,
                    device_type=device_type
                ).observe(vital.value)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        # Update metrics before generating
        self.update_metrics()
        
        # Generate Prometheus format
        return generate_latest(self.registry)
    
    def get_metrics_content_type(self) -> str:
        """Get the content type for Prometheus metrics"""
        return CONTENT_TYPE_LATEST

# Global exporter instance
prometheus_exporter = PrometheusMetricsExporter()

# Flask route handler for Prometheus metrics
def prometheus_metrics():
    """Flask route handler for Prometheus metrics endpoint"""
    from flask import Response
    
    try:
        metrics = prometheus_exporter.get_metrics()
        return Response(
            metrics,
            mimetype=prometheus_exporter.get_metrics_content_type()
        )
    except Exception as e:
        return Response(
            f"Error generating metrics: {str(e)}",
            status=500,
            mimetype='text/plain'
        )

# Background metrics updater
class BackgroundMetricsUpdater:
    """Background thread for updating Prometheus metrics"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background metrics updater"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the background metrics updater"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _update_loop(self):
        """Background loop for updating metrics"""
        while self.running:
            try:
                prometheus_exporter.update_metrics()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Error in background metrics update: {e}")
                time.sleep(60)  # Wait longer on error

# Global background updater
background_updater = BackgroundMetricsUpdater()

def start_background_updater():
    """Start the background metrics updater"""
    background_updater.start()

def stop_background_updater():
    """Stop the background metrics updater"""
    background_updater.stop()
