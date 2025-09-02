"""
Database Metrics Monitoring for Mingus Financial Application
Comprehensive metrics collection for connection pools, health monitoring, and performance tracking
Integrates with Prometheus and provides detailed insights for production environments
"""

import os
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager

# Import database systems
from ..database.connection_pool import get_pool_manager, ConnectionPoolManager
from ..database.health_checks import get_health_monitor, DatabaseHealthMonitor

logger = logging.getLogger(__name__)


@dataclass
class DatabaseMetrics:
    """Database performance and health metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Connection pool metrics
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connection_errors: int = 0
    checkout_errors: int = 0
    checkin_errors: int = 0
    
    # Performance metrics
    average_checkout_time: float = 0.0
    average_checkin_time: float = 0.0
    slow_queries: int = 0
    total_checkouts: int = 0
    total_checkins: int = 0
    
    # Health metrics
    pool_health_status: Dict[str, str] = field(default_factory=dict)
    connection_leaks: int = 0
    read_replica_health: Dict[str, bool] = field(default_factory=dict)
    
    # Resource utilization
    pool_utilization: Dict[str, float] = field(default_factory=dict)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


class DatabaseMetricsCollector:
    """
    Collects and aggregates database metrics from various sources
    Provides real-time monitoring and historical trend analysis
    """
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.pool_manager = get_pool_manager()
        self.health_monitor = get_health_monitor()
        
        self._collection_thread = None
        self._stop_collection = threading.Event()
        self._lock = threading.Lock()
        
        # Metrics storage
        self.metrics_history = deque(maxlen=10000)  # Store 10,000 data points
        self.current_metrics = DatabaseMetrics()
        
        # Performance tracking
        self.performance_trends = {
            'checkout_time': deque(maxlen=1000),
            'error_rate': deque(maxlen=1000),
            'utilization': deque(maxlen=1000),
            'connection_count': deque(maxlen=1000)
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'high_utilization': 0.8,  # 80%
            'high_error_rate': 0.05,  # 5%
            'slow_checkout': 2.0,  # 2 seconds
            'connection_leaks': 5,
            'unhealthy_pools': 1
        }
        
        # Alert history
        self.alert_history = deque(maxlen=1000)
        
        # Prometheus metrics (if available)
        self._setup_prometheus_metrics()
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics for monitoring"""
        try:
            from prometheus_client import Counter, Gauge, Histogram, Summary
            
            self.prometheus_metrics = {
                # Connection metrics
                'db_connections_total': Counter(
                    'db_connections_total',
                    'Total database connections',
                    ['pool_name', 'status']
                ),
                'db_connections_active': Gauge(
                    'db_connections_active',
                    'Active database connections',
                    ['pool_name']
                ),
                'db_connections_idle': Gauge(
                    'db_connections_idle',
                    'Idle database connections',
                    ['pool_name']
                ),
                'db_connections_errors': Counter(
                    'db_connections_errors_total',
                    'Total connection errors',
                    ['pool_name', 'error_type']
                ),
                
                # Performance metrics
                'db_checkout_duration': Histogram(
                    'db_checkout_duration_seconds',
                    'Database connection checkout duration',
                    ['pool_name'],
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
                ),
                'db_query_duration': Histogram(
                    'db_query_duration_seconds',
                    'Database query duration',
                    ['pool_name', 'query_type'],
                    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
                ),
                'db_slow_queries': Counter(
                    'db_slow_queries_total',
                    'Total slow queries',
                    ['pool_name']
                ),
                
                # Pool metrics
                'db_pool_size': Gauge(
                    'db_pool_size',
                    'Database connection pool size',
                    ['pool_name']
                ),
                'db_pool_overflow': Gauge(
                    'db_pool_overflow',
                    'Database connection pool overflow',
                    ['pool_name']
                ),
                'db_pool_utilization': Gauge(
                    'db_pool_utilization',
                    'Database connection pool utilization',
                    ['pool_name']
                ),
                
                # Health metrics
                'db_pool_health': Gauge(
                    'db_pool_health',
                    'Database pool health status',
                    ['pool_name', 'status']
                ),
                'db_connection_leaks': Gauge(
                    'db_connection_leaks',
                    'Number of connection leaks',
                    ['pool_name']
                ),
                'db_read_replica_health': Gauge(
                    'db_read_replica_health',
                    'Read replica health status',
                    ['replica_name']
                ),
                
                # System metrics
                'db_memory_usage_bytes': Gauge(
                    'db_memory_usage_bytes',
                    'Database memory usage in bytes'
                ),
                'db_cpu_usage_percent': Gauge(
                    'db_cpu_usage_percent',
                    'Database CPU usage percentage'
                )
            }
            
            self.prometheus_available = True
            logger.info("Prometheus metrics initialized successfully")
            
        except ImportError:
            self.prometheus_available = False
            self.prometheus_metrics = {}
            logger.info("Prometheus client not available, metrics will be collected locally only")
    
    def start_collection(self):
        """Start metrics collection"""
        if self._collection_thread and self._collection_thread.is_alive():
            return
        
        self._stop_collection.clear()
        self._collection_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self._collection_thread.start()
        logger.info("Database metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self._stop_collection.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Database metrics collection stopped")
    
    def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while not self._stop_collection.wait(self.collection_interval):
            try:
                # Collect current metrics
                metrics = self._collect_current_metrics()
                
                # Store in history
                with self._lock:
                    self.metrics_history.append(metrics)
                    self.current_metrics = metrics
                
                # Update performance trends
                self._update_performance_trends(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Update Prometheus metrics
                if self.prometheus_available:
                    self._update_prometheus_metrics(metrics)
                
                # Log summary
                self._log_metrics_summary(metrics)
                
            except Exception as e:
                logger.error(f"Error collecting database metrics: {e}")
    
    def _collect_current_metrics(self) -> DatabaseMetrics:
        """Collect current database metrics"""
        metrics = DatabaseMetrics()
        
        try:
            # Get pool manager metrics
            pool_metrics = self.pool_manager.get_pool_metrics()
            performance_metrics = self.pool_manager.get_performance_metrics()
            pool_health = self.pool_manager.get_pool_health()
            
            # Aggregate connection metrics
            for pool_name, pool_metric in pool_metrics.items():
                metrics.total_connections += pool_metric.total_connections
                metrics.active_connections += pool_metric.active_connections
                metrics.idle_connections += pool_metric.idle_connections
                metrics.connection_errors += pool_metric.connection_errors
                metrics.checkout_errors += pool_metric.checkout_errors
                metrics.checkin_errors += pool_metric.checkin_errors
                
                # Calculate pool utilization
                if pool_metric.total_connections > 0:
                    utilization = pool_metric.active_connections / pool_metric.total_connections
                    metrics.pool_utilization[pool_name] = utilization
                
                # Store pool health status
                if pool_name in pool_health:
                    metrics.pool_health_status[pool_name] = pool_health[pool_name]['status']
            
            # Get performance metrics
            metrics.average_checkout_time = performance_metrics.get('average_checkout_time', 0.0)
            metrics.average_checkin_time = performance_metrics.get('average_checkin_time', 0.0)
            metrics.slow_queries = performance_metrics.get('slow_queries', 0)
            metrics.total_checkouts = performance_metrics.get('total_checkouts', 0)
            metrics.total_checkins = performance_metrics.get('total_checkins', 0)
            
            # Get connection leak information
            leaks = performance_metrics.get('leak_details', [])
            metrics.connection_leaks = len(leaks)
            
            # Get read replica health
            read_replicas = performance_metrics.get('read_replicas', {})
            for replica_name, replica_metrics in read_replicas.items():
                metrics.read_replica_health[replica_name] = replica_metrics.get('is_healthy', False)
            
            # Get system metrics (if available)
            metrics.memory_usage = self._get_memory_usage()
            metrics.cpu_usage = self._get_cpu_usage()
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            metrics.connection_errors += 1
        
        return metrics
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss  # Resident Set Size in bytes
        except ImportError:
            return None
        except Exception:
            return None
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.cpu_percent()
        except ImportError:
            return None
        except Exception:
            return None
    
    def _update_performance_trends(self, metrics: DatabaseMetrics):
        """Update performance trend tracking"""
        timestamp = time.time()
        
        # Update checkout time trend
        if metrics.average_checkout_time > 0:
            self.performance_trends['checkout_time'].append({
                'timestamp': timestamp,
                'value': metrics.average_checkout_time
            })
        
        # Update error rate trend
        if metrics.total_connections > 0:
            error_rate = metrics.connection_errors / metrics.total_connections
            self.performance_trends['error_rate'].append({
                'timestamp': timestamp,
                'value': error_rate
            })
        
        # Update utilization trend
        if metrics.pool_utilization:
            avg_utilization = sum(metrics.pool_utilization.values()) / len(metrics.pool_utilization)
            self.performance_trends['utilization'].append({
                'timestamp': timestamp,
                'value': avg_utilization
            })
        
        # Update connection count trend
        self.performance_trends['connection_count'].append({
            'timestamp': timestamp,
            'value': metrics.total_connections
        })
    
    def _check_alerts(self, metrics: DatabaseMetrics):
        """Check for alert conditions"""
        alerts = []
        
        # Check pool utilization
        for pool_name, utilization in metrics.pool_utilization.items():
            if utilization > self.alert_thresholds['high_utilization']:
                alerts.append({
                    'type': 'high_utilization',
                    'pool': pool_name,
                    'value': utilization,
                    'threshold': self.alert_thresholds['high_utilization'],
                    'message': f"Pool {pool_name} utilization is {utilization:.2%} (threshold: {self.alert_thresholds['high_utilization']:.2%})"
                })
        
        # Check error rate
        if metrics.total_connections > 0:
            error_rate = metrics.connection_errors / metrics.total_connections
            if error_rate > self.alert_thresholds['high_error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'value': error_rate,
                    'threshold': self.alert_thresholds['high_error_rate'],
                    'message': f"Connection error rate is {error_rate:.2%} (threshold: {self.alert_thresholds['high_error_rate']:.2%})"
                })
        
        # Check slow checkout time
        if metrics.average_checkout_time > self.alert_thresholds['slow_checkout']:
            alerts.append({
                'type': 'slow_checkout',
                'value': metrics.average_checkout_time,
                'threshold': self.alert_thresholds['slow_checkout'],
                'message': f"Average checkout time is {metrics.average_checkout_time:.2f}s (threshold: {self.alert_thresholds['slow_checkout']:.2f}s)"
            })
        
        # Check connection leaks
        if metrics.connection_leaks > self.alert_thresholds['connection_leaks']:
            alerts.append({
                'type': 'connection_leaks',
                'value': metrics.connection_leaks,
                'threshold': self.alert_thresholds['connection_leaks'],
                'message': f"Connection leaks detected: {metrics.connection_leaks} (threshold: {self.alert_thresholds['connection_leaks']})"
            })
        
        # Check unhealthy pools
        unhealthy_pools = [name for name, status in metrics.pool_health_status.items() if status != 'healthy']
        if len(unhealthy_pools) >= self.alert_thresholds['unhealthy_pools']:
            alerts.append({
                'type': 'unhealthy_pools',
                'pools': unhealthy_pools,
                'count': len(unhealthy_pools),
                'threshold': self.alert_thresholds['unhealthy_pools'],
                'message': f"Unhealthy pools detected: {', '.join(unhealthy_pools)}"
            })
        
        # Store alerts
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()
            self.alert_history.append(alert)
            
            # Log alert
            log_level = logging.ERROR if alert['type'] in ['high_error_rate', 'connection_leaks', 'unhealthy_pools'] else logging.WARNING
            logger.log(log_level, f"Database alert: {alert['message']}")
    
    def _update_prometheus_metrics(self, metrics: DatabaseMetrics):
        """Update Prometheus metrics"""
        try:
            # Update connection metrics
            for pool_name, pool_metric in self.pool_manager.get_pool_metrics().items():
                self.prometheus_metrics['db_connections_active'].labels(pool_name=pool_name).set(pool_metric.active_connections)
                self.prometheus_metrics['db_connections_idle'].labels(pool_name=pool_name).set(pool_metric.idle_connections)
                self.prometheus_metrics['db_pool_size'].labels(pool_name=pool_name).set(pool_metric.total_connections)
                
                # Update pool utilization
                if pool_name in metrics.pool_utilization:
                    self.prometheus_metrics['db_pool_utilization'].labels(pool_name=pool_name).set(metrics.pool_utilization[pool_name])
                
                # Update pool health
                if pool_name in metrics.pool_health_status:
                    status = metrics.pool_health_status[pool_name]
                    self.prometheus_metrics['db_pool_health'].labels(pool_name=pool_name, status=status).set(1)
            
            # Update error metrics
            self.prometheus_metrics['db_connections_errors'].labels(pool_name='total', error_type='connection').inc(metrics.connection_errors)
            self.prometheus_metrics['db_connections_errors'].labels(pool_name='total', error_type='checkout').inc(metrics.checkout_errors)
            self.prometheus_metrics['db_connections_errors'].labels(pool_name='total', error_type='checkin').inc(metrics.checkin_errors)
            
            # Update performance metrics
            if metrics.slow_queries > 0:
                self.prometheus_metrics['db_slow_queries'].labels(pool_name='total').inc(metrics.slow_queries)
            
            # Update system metrics
            if metrics.memory_usage:
                self.prometheus_metrics['db_memory_usage_bytes'].set(metrics.memory_usage)
            if metrics.cpu_usage:
                self.prometheus_metrics['db_cpu_usage_percent'].set(metrics.cpu_usage)
            
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
    
    def _log_metrics_summary(self, metrics: DatabaseMetrics):
        """Log metrics summary"""
        logger.info(
            f"Database metrics: connections={metrics.total_connections} "
            f"(active={metrics.active_connections}, idle={metrics.idle_connections}), "
            f"errors={metrics.connection_errors}, "
            f"avg_checkout={metrics.average_checkout_time:.3f}s, "
            f"leaks={metrics.connection_leaks}"
        )
    
    def get_current_metrics(self) -> DatabaseMetrics:
        """Get current metrics"""
        with self._lock:
            return self.current_metrics
    
    def get_metrics_history(self, hours: int = 24) -> List[DatabaseMetrics]:
        """Get metrics history for the specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            return [
                metrics for metrics in self.metrics_history
                if metrics.timestamp > cutoff_time
            ]
    
    def get_performance_trends(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric"""
        if metric_name not in self.performance_trends:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        
        return [
            point for point in self.performance_trends[metric_name]
            if point['timestamp'] > cutoff_time
        ]
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts for the specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            current_metrics = self.get_current_metrics()
            
            # Calculate trends
            checkout_trend = self.get_performance_trends('checkout_time', 1)  # Last hour
            error_trend = self.get_performance_trends('error_rate', 1)
            utilization_trend = self.get_performance_trends('utilization', 1)
            
            # Calculate averages
            avg_checkout = sum(point['value'] for point in checkout_trend) / len(checkout_trend) if checkout_trend else 0
            avg_error_rate = sum(point['value'] for point in error_trend) / len(error_trend) if error_trend else 0
            avg_utilization = sum(point['value'] for point in utilization_trend) / len(utilization_trend) if utilization_trend else 0
            
            return {
                'current_metrics': {
                    'total_connections': current_metrics.total_connections,
                    'active_connections': current_metrics.active_connections,
                    'idle_connections': current_metrics.idle_connections,
                    'connection_errors': current_metrics.connection_errors,
                    'slow_queries': current_metrics.slow_queries,
                    'connection_leaks': current_metrics.connection_leaks,
                    'pool_health': current_metrics.pool_health_status,
                    'read_replica_health': current_metrics.read_replica_health
                },
                'performance_trends': {
                    'average_checkout_time': avg_checkout,
                    'average_error_rate': avg_error_rate,
                    'average_utilization': avg_utilization
                },
                'alerts': {
                    'total_alerts': len(self.alert_history),
                    'recent_alerts': len(self.get_alerts(1))  # Last hour
                },
                'collection_info': {
                    'metrics_collected': len(self.metrics_history),
                    'last_collection': current_metrics.timestamp.isoformat(),
                    'collection_interval': self.collection_interval
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {'error': str(e)}


# Global metrics collector instance - lazy initialization
_metrics_collector = None


def get_metrics_collector() -> DatabaseMetricsCollector:
    """Get the global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = DatabaseMetricsCollector()
    return _metrics_collector


def init_metrics_collector(collection_interval: int = 60):
    """Initialize the global metrics collector"""
    global _metrics_collector
    _metrics_collector = DatabaseMetricsCollector(collection_interval)


# Metrics utilities
class MetricsUtils:
    """Utility functions for database metrics"""
    
    @staticmethod
    def start_monitoring(collection_interval: int = 60):
        """Start database metrics monitoring"""
        collector = get_metrics_collector()
        collector.start_collection()
        return collector
    
    @staticmethod
    def stop_monitoring():
        """Stop database metrics monitoring"""
        collector = get_metrics_collector()
        collector.stop_collection()
    
    @staticmethod
    def get_current_metrics() -> Dict[str, Any]:
        """Get current database metrics"""
        try:
            collector = get_metrics_collector()
            metrics = collector.get_current_metrics()
            
            return {
                'timestamp': metrics.timestamp.isoformat(),
                'total_connections': metrics.total_connections,
                'active_connections': metrics.active_connections,
                'idle_connections': metrics.idle_connections,
                'connection_errors': metrics.connection_errors,
                'slow_queries': metrics.slow_queries,
                'connection_leaks': metrics.connection_leaks,
                'pool_health': metrics.pool_health_status,
                'read_replica_health': metrics.read_replica_health,
                'pool_utilization': metrics.pool_utilization,
                'performance': {
                    'average_checkout_time': metrics.average_checkout_time,
                    'average_checkin_time': metrics.average_checkin_time,
                    'total_checkouts': metrics.total_checkouts,
                    'total_checkins': metrics.total_checkins
                }
            }
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    @staticmethod
    def get_metrics_summary() -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            collector = get_metrics_collector()
            return collector.get_metrics_summary()
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    @staticmethod
    def get_performance_trends(metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric"""
        try:
            collector = get_metrics_collector()
            return collector.get_performance_trends(metric_name, hours)
        except Exception as e:
            return [{'error': str(e), 'status': 'failed'}]
    
    @staticmethod
    def get_alerts(hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts for the specified hours"""
        try:
            collector = get_metrics_collector()
            return collector.get_alerts(hours)
        except Exception as e:
            return [{'error': str(e), 'status': 'failed'}]


# Export main functions and classes
__all__ = [
    'DatabaseMetrics',
    'DatabaseMetricsCollector',
    'MetricsUtils',
    'get_metrics_collector',
    'init_metrics_collector'
]
