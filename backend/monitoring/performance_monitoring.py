#!/usr/bin/env python3
"""
Mingus Application - Performance Monitoring Module
Comprehensive monitoring and metrics for Daily Outlook system performance
"""

import time
import logging
import json
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
from flask import request, g

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('mingus_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('mingus_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
CACHE_HITS = Counter('mingus_cache_hits_total', 'Cache hits', ['cache_type'])
CACHE_MISSES = Counter('mingus_cache_misses_total', 'Cache misses', ['cache_type'])
DAILY_OUTLOOK_LOAD_TIME = Histogram('mingus_daily_outlook_load_seconds', 'Daily outlook load time')
BALANCE_SCORE_CALCULATION_TIME = Histogram('mingus_balance_score_calculation_seconds', 'Balance score calculation time')
ACTIVE_USERS = Gauge('mingus_active_users', 'Number of active users')
CACHE_SIZE = Gauge('mingus_cache_size_bytes', 'Cache size in bytes')
DATABASE_CONNECTIONS = Gauge('mingus_database_connections', 'Database connections')
MEMORY_USAGE = Gauge('mingus_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('mingus_cpu_usage_percent', 'CPU usage percentage')

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class SystemHealth:
    """System health status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    metrics: Dict[str, Any]
    alerts: List[str]
    recommendations: List[str]

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    
    Features:
    - Real-time performance metrics
    - System health monitoring
    - Alert generation
    - Performance trend analysis
    - User experience metrics
    """
    
    def __init__(self, redis_client, db_session, prometheus_port: int = 8000):
        """
        Initialize performance monitor
        
        Args:
            redis_client: Redis client for metrics storage
            db_session: Database session
            prometheus_port: Port for Prometheus metrics server
        """
        self.redis = redis_client
        self.db = db_session
        self.prometheus_port = prometheus_port
        
        # Metrics storage
        self.metrics_buffer = deque(maxlen=10000)
        self.alert_thresholds = {
            'daily_outlook_load_time': 0.5,  # 500ms
            'balance_score_calculation_time': 0.2,  # 200ms
            'cache_hit_rate': 0.95,  # 95%
            'memory_usage': 0.8,  # 80%
            'cpu_usage': 0.8,  # 80%
            'error_rate': 0.05  # 5%
        }
        
        # Performance statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'active_users': 0,
            'system_load': 0.0,
            'memory_usage': 0.0
        }
        
        # Alert system
        self.active_alerts = []
        self.alert_history = deque(maxlen=1000)
        
        # Start monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start performance monitoring"""
        try:
            # Start Prometheus metrics server
            start_http_server(self.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
            
            # Start background monitoring tasks
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("Performance monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Error starting performance monitoring: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Update Prometheus metrics
                self._update_prometheus_metrics()
                
                # Store metrics in Redis
                self._store_metrics_in_redis()
                
                # Sleep for monitoring interval
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_bytes = memory.used
            memory_usage_percent = memory.percent
            MEMORY_USAGE.set(memory_usage_bytes)
            
            # System load
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            
            # Update statistics
            self.stats['cpu_usage'] = cpu_percent
            self.stats['memory_usage'] = memory_usage_percent
            self.stats['system_load'] = load_avg
            
            # Store metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name='system_metrics',
                value=cpu_percent,
                tags={'metric_type': 'cpu_usage'},
                metadata={
                    'memory_usage_percent': memory_usage_percent,
                    'system_load': load_avg
                }
            )
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _check_alerts(self):
        """Check for performance alerts"""
        try:
            # Check daily outlook load time
            if hasattr(self, 'daily_outlook_load_times'):
                avg_load_time = sum(self.daily_outlook_load_times) / len(self.daily_outlook_load_times)
                if avg_load_time > self.alert_thresholds['daily_outlook_load_time']:
                    self._create_alert(
                        'daily_outlook_slow',
                        f'Daily outlook load time is {avg_load_time:.2f}s (threshold: {self.alert_thresholds["daily_outlook_load_time"]}s)',
                        'warning'
                    )
            
            # Check cache hit rate
            if self.stats['cache_hit_rate'] < self.alert_thresholds['cache_hit_rate']:
                self._create_alert(
                    'cache_hit_rate_low',
                    f'Cache hit rate is {self.stats["cache_hit_rate"]:.2%} (threshold: {self.alert_thresholds["cache_hit_rate"]:.2%})',
                    'warning'
                )
            
            # Check memory usage
            if self.stats['memory_usage'] > self.alert_thresholds['memory_usage']:
                self._create_alert(
                    'memory_usage_high',
                    f'Memory usage is {self.stats["memory_usage"]:.1%} (threshold: {self.alert_thresholds["memory_usage"]:.1%})',
                    'critical'
                )
            
            # Check CPU usage
            if self.stats['cpu_usage'] > self.alert_thresholds['cpu_usage']:
                self._create_alert(
                    'cpu_usage_high',
                    f'CPU usage is {self.stats["cpu_usage"]:.1%} (threshold: {self.alert_thresholds["cpu_usage"]:.1%})',
                    'critical'
                )
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create a performance alert"""
        alert = {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now(),
            'resolved': False
        }
        
        # Add to active alerts if not already present
        if not any(a['type'] == alert_type and not a['resolved'] for a in self.active_alerts):
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            
            logger.warning(f"Performance alert: {message}")
    
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics"""
        try:
            # Update gauge metrics
            ACTIVE_USERS.set(self.stats['active_users'])
            MEMORY_USAGE.set(self.stats['memory_usage'])
            CPU_USAGE.set(self.stats['cpu_usage'])
            
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
    
    def _store_metrics_in_redis(self):
        """Store metrics in Redis for persistence"""
        try:
            # Store recent metrics
            if self.metrics_buffer:
                metrics_data = [asdict(metric) for metric in list(self.metrics_buffer)[-100:]]
                self.redis.setex(
                    'performance_metrics:recent',
                    3600,  # 1 hour TTL
                    json.dumps(metrics_data, default=str)
                )
            
            # Store statistics
            self.redis.setex(
                'performance_stats',
                300,  # 5 minutes TTL
                json.dumps(self.stats, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error storing metrics in Redis: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        try:
            # Update Prometheus metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Update statistics
            self.stats['total_requests'] += 1
            if 200 <= status_code < 400:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
            
            # Update average response time
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['total_requests'] - 1) + duration) 
                / self.stats['total_requests']
            )
            
            # Store request metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name='api_request',
                value=duration,
                tags={
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': str(status_code)
                },
                metadata={}
            )
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error recording request metrics: {e}")
    
    def record_daily_outlook_load(self, load_time: float, user_id: int):
        """Record daily outlook load time"""
        try:
            DAILY_OUTLOOK_LOAD_TIME.observe(load_time)
            
            # Store in buffer for alert checking
            if not hasattr(self, 'daily_outlook_load_times'):
                self.daily_outlook_load_times = deque(maxlen=100)
            self.daily_outlook_load_times.append(load_time)
            
            # Store metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name='daily_outlook_load',
                value=load_time,
                tags={'user_id': str(user_id)},
                metadata={}
            )
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error recording daily outlook load time: {e}")
    
    def record_balance_score_calculation(self, calculation_time: float, user_id: int):
        """Record balance score calculation time"""
        try:
            BALANCE_SCORE_CALCULATION_TIME.observe(calculation_time)
            
            # Store metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name='balance_score_calculation',
                value=calculation_time,
                tags={'user_id': str(user_id)},
                metadata={}
            )
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error recording balance score calculation time: {e}")
    
    def record_cache_operation(self, cache_type: str, hit: bool):
        """Record cache operation"""
        try:
            if hit:
                CACHE_HITS.labels(cache_type=cache_type).inc()
            else:
                CACHE_MISSES.labels(cache_type=cache_type).inc()
            
            # Update cache hit rate
            total_cache_operations = self.stats.get('cache_hits', 0) + self.stats.get('cache_misses', 0)
            if total_cache_operations > 0:
                self.stats['cache_hit_rate'] = self.stats.get('cache_hits', 0) / total_cache_operations
            
        except Exception as e:
            logger.error(f"Error recording cache operation: {e}")
    
    def get_performance_metrics(self, time_range: str = '1h') -> Dict[str, Any]:
        """
        Get performance metrics for a time range
        
        Args:
            time_range: Time range ('1h', '24h', '7d')
            
        Returns:
            Dictionary containing performance metrics
        """
        try:
            # Calculate time cutoff
            time_cutoffs = {
                '1h': datetime.now() - timedelta(hours=1),
                '24h': datetime.now() - timedelta(days=1),
                '7d': datetime.now() - timedelta(days=7)
            }
            
            cutoff = time_cutoffs.get(time_range, time_cutoffs['1h'])
            
            # Filter metrics by time range
            recent_metrics = [
                metric for metric in self.metrics_buffer
                if metric.timestamp >= cutoff
            ]
            
            # Calculate aggregated metrics
            metrics_by_type = defaultdict(list)
            for metric in recent_metrics:
                metrics_by_type[metric.metric_name].append(metric.value)
            
            # Calculate statistics
            aggregated_metrics = {}
            for metric_type, values in metrics_by_type.items():
                if values:
                    aggregated_metrics[metric_type] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'p95': sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]
                    }
            
            return {
                'time_range': time_range,
                'metrics': aggregated_metrics,
                'system_stats': self.stats,
                'active_alerts': len([a for a in self.active_alerts if not a['resolved']]),
                'total_alerts': len(self.alert_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        try:
            # Determine overall health status
            critical_alerts = [a for a in self.active_alerts if a['severity'] == 'critical' and not a['resolved']]
            warning_alerts = [a for a in self.active_alerts if a['severity'] == 'warning' and not a['resolved']]
            
            if critical_alerts:
                status = 'unhealthy'
            elif warning_alerts:
                status = 'degraded'
            else:
                status = 'healthy'
            
            # Generate recommendations
            recommendations = []
            if self.stats['cache_hit_rate'] < 0.9:
                recommendations.append("Consider increasing cache TTL or implementing cache warming")
            if self.stats['memory_usage'] > 0.7:
                recommendations.append("Consider scaling memory or optimizing memory usage")
            if self.stats['cpu_usage'] > 0.7:
                recommendations.append("Consider scaling CPU or optimizing processing")
            
            return SystemHealth(
                status=status,
                timestamp=datetime.now(),
                metrics=self.stats,
                alerts=[a['message'] for a in self.active_alerts if not a['resolved']],
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return SystemHealth(
                status='unhealthy',
                timestamp=datetime.now(),
                metrics={},
                alerts=[f"Health check failed: {e}"],
                recommendations=["Check system logs for errors"]
            )
    
    def resolve_alert(self, alert_id: str):
        """Resolve a performance alert"""
        try:
            for alert in self.active_alerts:
                if alert['id'] == alert_id:
                    alert['resolved'] = True
                    alert['resolved_at'] = datetime.now()
                    logger.info(f"Resolved alert: {alert['message']}")
                    break
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        try:
            return list(self.alert_history)[-limit:]
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []
    
    def export_metrics(self, format: str = 'json') -> str:
        """
        Export metrics in specified format
        
        Args:
            format: Export format ('json', 'prometheus')
            
        Returns:
            Exported metrics string
        """
        try:
            if format == 'json':
                return json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': [asdict(metric) for metric in self.metrics_buffer],
                    'stats': self.stats,
                    'alerts': self.active_alerts
                }, default=str)
            elif format == 'prometheus':
                # This would generate Prometheus format
                return "# Prometheus metrics export not implemented"
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return "{}"
    
    def close(self):
        """Close performance monitor"""
        try:
            if hasattr(self, 'monitoring_thread'):
                self.monitoring_thread.join(timeout=5)
            
            logger.info("Performance monitor closed")
            
        except Exception as e:
            logger.error(f"Error closing performance monitor: {e}")

# Decorator for automatic performance monitoring
def monitor_performance(metric_name: str = None):
    """
    Decorator for automatic performance monitoring
    
    Args:
        metric_name: Custom metric name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            metric_name_actual = metric_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                
                # Record successful execution
                duration = time.time() - start_time
                if hasattr(g, 'performance_monitor'):
                    g.performance_monitor.record_request(
                        'POST',  # Assume POST for function calls
                        metric_name_actual,
                        200,
                        duration
                    )
                
                return result
                
            except Exception as e:
                # Record failed execution
                duration = time.time() - start_time
                if hasattr(g, 'performance_monitor'):
                    g.performance_monitor.record_request(
                        'POST',
                        metric_name_actual,
                        500,
                        duration
                    )
                
                raise e
        
        return wrapper
    return decorator

# Global performance monitor instance
performance_monitor = None

def initialize_performance_monitoring(redis_client, db_session, prometheus_port: int = 8000):
    """Initialize global performance monitor"""
    global performance_monitor
    performance_monitor = PerformanceMonitor(redis_client, db_session, prometheus_port)
    return performance_monitor

def get_performance_monitor():
    """Get global performance monitor instance"""
    return performance_monitor
