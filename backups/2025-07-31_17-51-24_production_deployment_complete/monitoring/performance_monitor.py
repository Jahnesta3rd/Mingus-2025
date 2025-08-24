"""
Performance Monitoring System for Income Comparison Feature
Ultra-budget optimized monitoring with cost tracking and performance alerts
"""

import time
import json
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CostMetric:
    """Cost tracking metric"""
    service: str
    cost_per_request: float
    requests_count: int
    total_cost: float
    timestamp: datetime
    period: str  # 'hour', 'day', 'month'

@dataclass
class Alert:
    """Performance alert"""
    level: str  # 'info', 'warning', 'error', 'critical'
    message: str
    timestamp: datetime
    metric: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None

class UltraBudgetPerformanceMonitor:
    """
    Ultra-budget performance monitoring system
    Features:
    - In-memory metrics storage
    - Performance thresholds and alerts
    - Cost tracking
    - Memory usage monitoring
    - Automatic cleanup
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.metrics: List[PerformanceMetric] = []
        self.cost_metrics: List[CostMetric] = []
        self.alerts: List[Alert] = []
        
        # Performance thresholds
        self.thresholds = self.config['performance_thresholds']
        
        # Memory management
        self.max_metrics = self.config['max_metrics_stored']
        self.max_alerts = self.config['max_alerts_stored']
        self.cleanup_interval = self.config['cleanup_interval_seconds']
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        logger.info("Ultra-budget performance monitor initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for ultra-budget deployment"""
        return {
            'performance_thresholds': {
                'income_analysis_max_ms': 500,
                'total_response_max_ms': 3000,
                'memory_usage_max_mb': 100,
                'cpu_usage_max_percent': 80,
                'error_rate_max_percent': 5,
            },
            'max_metrics_stored': 1000,
            'max_alerts_stored': 100,
            'cleanup_interval_seconds': 3600,  # 1 hour
            'cost_tracking': {
                'enabled': True,
                'free_tier_limits': {
                    'requests_per_month': 10000,
                    'storage_mb': 100,
                    'compute_hours': 720,  # 30 days * 24 hours
                }
            },
            'alerting': {
                'enabled': True,
                'alert_levels': ['error', 'critical'],
                'notification_methods': ['log']
            }
        }
    
    def record_metric(self, operation: str, duration: float, success: bool = True, 
                     error_message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        with self.lock:
            self.metrics.append(metric)
            
            # Check thresholds and generate alerts
            self._check_thresholds(metric)
            
            # Limit stored metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
        
        logger.debug(f"Recorded metric: {operation} - {duration:.3f}s - {'success' if success else 'failed'}")
    
    def record_cost(self, service: str, cost_per_request: float, requests_count: int = 1):
        """Record cost metric"""
        cost_metric = CostMetric(
            service=service,
            cost_per_request=cost_per_request,
            requests_count=requests_count,
            total_cost=cost_per_request * requests_count,
            timestamp=datetime.now(),
            period='hour'
        )
        
        with self.lock:
            self.cost_metrics.append(cost_metric)
        
        logger.info(f"Recorded cost: {service} - ${cost_metric.total_cost:.4f}")
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """Check performance thresholds and generate alerts"""
        if not self.config['alerting']['enabled']:
            return
        
        # Check income analysis performance
        if metric.operation == 'income_analysis' and metric.duration > self.thresholds['income_analysis_max_ms'] / 1000:
            self._create_alert(
                level='warning' if metric.duration < self.thresholds['income_analysis_max_ms'] * 2 / 1000 else 'error',
                message=f"Income analysis performance degraded: {metric.duration:.3f}s",
                metric='income_analysis_duration',
                value=metric.duration,
                threshold=self.thresholds['income_analysis_max_ms'] / 1000
            )
        
        # Check total response time
        if metric.operation == 'total_response' and metric.duration > self.thresholds['total_response_max_ms'] / 1000:
            self._create_alert(
                level='warning' if metric.duration < self.thresholds['total_response_max_ms'] * 2 / 1000 else 'error',
                message=f"Total response time exceeded threshold: {metric.duration:.3f}s",
                metric='total_response_duration',
                value=metric.duration,
                threshold=self.thresholds['total_response_max_ms'] / 1000
            )
        
        # Check for failures
        if not metric.success:
            self._create_alert(
                level='error',
                message=f"Operation failed: {metric.operation} - {metric.error_message}",
                metric=f"{metric.operation}_failure",
                value=1,
                threshold=0
            )
    
    def _create_alert(self, level: str, message: str, metric: Optional[str] = None, 
                     value: Optional[float] = None, threshold: Optional[float] = None):
        """Create and store an alert"""
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            metric=metric,
            value=value,
            threshold=threshold
        )
        
        with self.lock:
            self.alerts.append(alert)
            
            # Limit stored alerts
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"Alert [{level.upper()}]: {message}")
    
    def get_performance_stats(self, operation: Optional[str] = None, 
                            time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            metrics = self.metrics.copy()
        
        # Filter by operation
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        # Filter by time window
        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        if not metrics:
            return {
                'count': 0,
                'avg_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'success_rate': 0,
                'error_count': 0
            }
        
        # Calculate statistics
        durations = [m.duration for m in metrics]
        success_count = sum(1 for m in metrics if m.success)
        
        return {
            'count': len(metrics),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'success_rate': success_count / len(metrics) * 100,
            'error_count': len(metrics) - success_count
        }
    
    def get_cost_stats(self, service: Optional[str] = None, 
                      period: str = 'day') -> Dict[str, Any]:
        """Get cost statistics"""
        with self.lock:
            cost_metrics = self.cost_metrics.copy()
        
        # Filter by service
        if service:
            cost_metrics = [c for c in cost_metrics if c.service == service]
        
        # Filter by period
        if period == 'hour':
            cutoff_time = datetime.now() - timedelta(hours=1)
        elif period == 'day':
            cutoff_time = datetime.now() - timedelta(days=1)
        elif period == 'month':
            cutoff_time = datetime.now() - timedelta(days=30)
        else:
            cutoff_time = datetime.min
        
        cost_metrics = [c for c in cost_metrics if c.timestamp > cutoff_time]
        
        if not cost_metrics:
            return {
                'total_cost': 0,
                'total_requests': 0,
                'avg_cost_per_request': 0,
                'services': {}
            }
        
        # Calculate cost statistics
        total_cost = sum(c.total_cost for c in cost_metrics)
        total_requests = sum(c.requests_count for c in cost_metrics)
        
        # Group by service
        services = defaultdict(lambda: {'cost': 0, 'requests': 0})
        for metric in cost_metrics:
            services[metric.service]['cost'] += metric.total_cost
            services[metric.service]['requests'] += metric.requests_count
        
        return {
            'total_cost': total_cost,
            'total_requests': total_requests,
            'avg_cost_per_request': total_cost / total_requests if total_requests > 0 else 0,
            'services': dict(services)
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'thread_count': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections()),
                'system_memory_percent': psutil.virtual_memory().percent,
                'system_cpu_percent': psutil.cpu_percent()
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                'memory_usage_mb': 0,
                'cpu_percent': 0,
                'error': str(e)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        # Get recent performance stats
        recent_stats = self.get_performance_stats(time_window=timedelta(hours=1))
        system_stats = self.get_system_stats()
        cost_stats = self.get_cost_stats(period='day')
        
        # Determine health status
        health_status = 'healthy'
        warnings = []
        
        # Check performance
        if recent_stats['avg_duration'] > self.thresholds['income_analysis_max_ms'] / 1000:
            health_status = 'degraded'
            warnings.append(f"High average response time: {recent_stats['avg_duration']:.3f}s")
        
        # Check error rate
        if recent_stats['count'] > 0:
            error_rate = recent_stats['error_count'] / recent_stats['count'] * 100
            if error_rate > self.thresholds['error_rate_max_percent']:
                health_status = 'unhealthy'
                warnings.append(f"High error rate: {error_rate:.1f}%")
        
        # Check memory usage
        if system_stats['memory_usage_mb'] > self.thresholds['memory_usage_max_mb']:
            health_status = 'degraded'
            warnings.append(f"High memory usage: {system_stats['memory_usage_mb']:.1f}MB")
        
        # Check CPU usage
        if system_stats['cpu_percent'] > self.thresholds['cpu_usage_max_percent']:
            health_status = 'degraded'
            warnings.append(f"High CPU usage: {system_stats['cpu_percent']:.1f}%")
        
        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'performance': recent_stats,
            'system': system_stats,
            'costs': cost_stats,
            'warnings': warnings,
            'thresholds': self.thresholds
        }
    
    def get_recent_alerts(self, level: Optional[str] = None, 
                         hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        with self.lock:
            alerts = self.alerts.copy()
        
        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        alerts = [a for a in alerts if a.timestamp > cutoff_time]
        
        # Filter by level
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        # Convert to dict for JSON serialization
        return [asdict(alert) for alert in alerts]
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def _cleanup_worker(self):
        """Background cleanup worker"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days of data
        
        with self.lock:
            # Clean up old metrics
            original_count = len(self.metrics)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
            metrics_removed = original_count - len(self.metrics)
            
            # Clean up old alerts
            original_alert_count = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
            alerts_removed = original_alert_count - len(self.alerts)
            
            # Clean up old cost metrics
            original_cost_count = len(self.cost_metrics)
            self.cost_metrics = [c for c in self.cost_metrics if c.timestamp > cutoff_time]
            costs_removed = original_cost_count - len(self.cost_metrics)
        
        if metrics_removed > 0 or alerts_removed > 0 or costs_removed > 0:
            logger.info(f"Cleanup removed {metrics_removed} metrics, {alerts_removed} alerts, {costs_removed} cost metrics")
    
    def export_metrics(self, filepath: str):
        """Export metrics to file"""
        try:
            with self.lock:
                data = {
                    'metrics': [asdict(m) for m in self.metrics],
                    'cost_metrics': [asdict(c) for c in self.cost_metrics],
                    'alerts': [asdict(a) for a in self.alerts],
                    'exported_at': datetime.now().isoformat()
                }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        with self.lock:
            self.metrics.clear()
            self.cost_metrics.clear()
            self.alerts.clear()
        
        logger.info("All metrics reset")

# Global performance monitor instance
_performance_monitor = None
_monitor_lock = threading.Lock()

def get_performance_monitor(config: Optional[Dict[str, Any]] = None) -> UltraBudgetPerformanceMonitor:
    """Get singleton performance monitor instance"""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = UltraBudgetPerformanceMonitor(config)
    
    return _performance_monitor

def record_metric(operation: str, duration: float, success: bool = True, 
                 error_message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """Convenience function to record a metric"""
    monitor = get_performance_monitor()
    monitor.record_metric(operation, duration, success, error_message, metadata)

def record_cost(service: str, cost_per_request: float, requests_count: int = 1):
    """Convenience function to record cost"""
    monitor = get_performance_monitor()
    monitor.record_cost(service, cost_per_request, requests_count)

# Performance monitoring decorator
def monitor_performance(operation_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                record_metric(operation, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_metric(operation, duration, success=False, error_message=str(e))
                raise
        
        return wrapper
    return decorator

# Cost tracking decorator
def track_cost(service: str, cost_per_request: float):
    """Decorator to track function cost"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            record_cost(service, cost_per_request)
            return result
        return wrapper
    return decorator 