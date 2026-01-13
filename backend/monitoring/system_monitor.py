#!/usr/bin/env python3
"""
Unified System Resource Monitoring Module
Comprehensive monitoring for CPU, memory, disk, network, and application metrics
"""

import os
import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    memory_total: int
    memory_used: int
    memory_percent: float
    memory_available: int
    disk_total: int
    disk_used: int
    disk_percent: float
    disk_free: int
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    load_avg: Optional[float] = None
    process_count: int = 0
    thread_count: int = 0

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: datetime
    request_count: int
    request_rate: float  # requests per second
    avg_response_time: float
    error_rate: float
    active_connections: int
    cache_hit_rate: float
    database_connections: int
    redis_connections: int

@dataclass
class Alert:
    """System alert"""
    timestamp: datetime
    level: str  # 'warning', 'critical'
    metric: str
    value: float
    threshold: float
    message: str

class SystemResourceMonitor:
    """
    Comprehensive system resource monitoring
    
    Features:
    - Real-time CPU, memory, disk, network monitoring
    - Application metrics tracking
    - Alert generation for resource thresholds
    - Historical metrics storage
    - Performance recommendations
    """
    
    def __init__(
        self,
        monitoring_interval: int = 10,
        alert_thresholds: Optional[Dict[str, float]] = None,
        enable_prometheus: bool = False,
        prometheus_port: int = 9090
    ):
        """
        Initialize system resource monitor
        
        Args:
            monitoring_interval: Seconds between metric collection
            alert_thresholds: Custom alert thresholds
            enable_prometheus: Enable Prometheus metrics export
            prometheus_port: Port for Prometheus server
        """
        self.monitoring_interval = monitoring_interval
        self.enable_prometheus = enable_prometheus
        self.prometheus_port = prometheus_port
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 5.0,  # 5%
            'response_time_ms': 1000.0,  # 1 second
            'cache_hit_rate': 0.70  # 70%
        }
        
        # Metrics storage
        self.metrics_history = deque(maxlen=3600)  # 1 hour at 1-second intervals
        self.system_metrics: Optional[SystemMetrics] = None
        self.application_metrics: Optional[ApplicationMetrics] = None
        
        # Request tracking
        self.request_times = deque(maxlen=1000)
        self.request_errors = deque(maxlen=1000)
        self.request_count = 0
        self.last_request_time = time.time()
        
        # Network baseline
        self.network_baseline = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0
        }
        self._init_network_baseline()
        
        # Alerts
        self.active_alerts: List[Alert] = []
        self.alert_history = deque(maxlen=1000)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Prometheus metrics (if enabled)
        self.prometheus_metrics = {}
        if self.enable_prometheus:
            self._init_prometheus()
    
    def _init_network_baseline(self):
        """Initialize network baseline for delta calculations"""
        try:
            net_io = psutil.net_io_counters()
            self.network_baseline = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            logger.warning(f"Could not initialize network baseline: {e}")
    
    def _init_prometheus(self):
        """Initialize Prometheus metrics"""
        try:
            from prometheus_client import Counter, Histogram, Gauge, start_http_server
            
            self.prometheus_metrics = {
                'cpu_usage': Gauge('system_cpu_usage_percent', 'CPU usage percentage'),
                'memory_usage': Gauge('system_memory_usage_bytes', 'Memory usage in bytes'),
                'memory_percent': Gauge('system_memory_usage_percent', 'Memory usage percentage'),
                'disk_usage': Gauge('system_disk_usage_bytes', 'Disk usage in bytes'),
                'disk_percent': Gauge('system_disk_usage_percent', 'Disk usage percentage'),
                'network_sent': Gauge('system_network_bytes_sent', 'Network bytes sent'),
                'network_recv': Gauge('system_network_bytes_recv', 'Network bytes received'),
                'request_count': Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status']),
                'request_duration': Histogram('app_request_duration_seconds', 'Request duration', ['method', 'endpoint']),
                'error_count': Counter('app_errors_total', 'Total errors', ['type']),
                'cache_hits': Counter('app_cache_hits_total', 'Cache hits'),
                'cache_misses': Counter('app_cache_misses_total', 'Cache misses'),
                'active_connections': Gauge('app_active_connections', 'Active connections'),
                'db_connections': Gauge('app_database_connections', 'Database connections'),
            }
            
            # Start Prometheus HTTP server
            start_http_server(self.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
            
        except ImportError:
            logger.warning("prometheus_client not installed. Prometheus metrics disabled.")
            self.enable_prometheus = False
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus: {e}")
            self.enable_prometheus = False
    
    def start(self):
        """Start monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"System resource monitoring started (interval: {self.monitoring_interval}s)")
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("System resource monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Collect application metrics
                self._collect_application_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Update Prometheus metrics
                if self.enable_prometheus:
                    self._update_prometheus_metrics()
                
                # Store metrics
                self._store_metrics()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval * 2)
    
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Network
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent - self.network_baseline['bytes_sent']
            network_bytes_recv = net_io.bytes_recv - self.network_baseline['bytes_recv']
            network_packets_sent = net_io.packets_sent - self.network_baseline['packets_sent']
            network_packets_recv = net_io.packets_recv - self.network_baseline['packets_recv']
            
            # Load average (Unix only)
            try:
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            except:
                load_avg = None
            
            # Process info
            process_count = len(psutil.pids())
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            self.system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=(disk.used / disk.total * 100) if disk.total > 0 else 0,
                disk_free=disk.free,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                network_packets_sent=network_packets_sent,
                network_packets_recv=network_packets_recv,
                load_avg=load_avg,
                process_count=process_count,
                thread_count=thread_count
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            # Calculate request rate
            current_time = time.time()
            time_diff = current_time - self.last_request_time if self.last_request_time > 0 else 1
            request_rate = self.request_count / time_diff if time_diff > 0 else 0
            
            # Average response time
            avg_response_time = (
                sum(self.request_times) / len(self.request_times)
                if self.request_times else 0
            )
            
            # Error rate (from request errors or error monitor)
            total_requests = len(self.request_times) + len(self.request_errors)
            error_rate = (
                (len(self.request_errors) / total_requests * 100)
                if total_requests > 0 else 0
            )
            
            # Try to get error rate from error monitor if available
            try:
                from backend.monitoring.error_monitor import get_error_monitor
                error_monitor = get_error_monitor()
                error_stats = error_monitor.get_error_stats(hours=1)
                error_count = error_stats.get('total', 0)
                if self.request_count > 0:
                    error_rate = (error_count / self.request_count * 100)
            except:
                pass  # Use request-based error rate if error monitor not available
            
            # Cache hit rate (placeholder - should be from cache manager)
            cache_hit_rate = 0.0  # Will be updated by cache manager
            
            # Connection counts (placeholders - should be from actual connections)
            active_connections = 0
            database_connections = 0
            redis_connections = 0
            
            self.application_metrics = ApplicationMetrics(
                timestamp=datetime.now(),
                request_count=self.request_count,
                request_rate=request_rate,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                active_connections=active_connections,
                cache_hit_rate=cache_hit_rate,
                database_connections=database_connections,
                redis_connections=redis_connections
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    def _check_alerts(self):
        """Check for resource threshold alerts"""
        if not self.system_metrics or not self.application_metrics:
            return
        
        alerts_to_add = []
        
        # CPU alert
        if self.system_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts_to_add.append(Alert(
                timestamp=datetime.now(),
                level='warning' if self.system_metrics.cpu_percent < 90 else 'critical',
                metric='cpu_percent',
                value=self.system_metrics.cpu_percent,
                threshold=self.alert_thresholds['cpu_percent'],
                message=f"High CPU usage: {self.system_metrics.cpu_percent:.1f}%"
            ))
        
        # Memory alert
        if self.system_metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts_to_add.append(Alert(
                timestamp=datetime.now(),
                level='warning' if self.system_metrics.memory_percent < 95 else 'critical',
                metric='memory_percent',
                value=self.system_metrics.memory_percent,
                threshold=self.alert_thresholds['memory_percent'],
                message=f"High memory usage: {self.system_metrics.memory_percent:.1f}%"
            ))
        
        # Disk alert
        if self.system_metrics.disk_percent > self.alert_thresholds['disk_percent']:
            alerts_to_add.append(Alert(
                timestamp=datetime.now(),
                level='warning' if self.system_metrics.disk_percent < 95 else 'critical',
                metric='disk_percent',
                value=self.system_metrics.disk_percent,
                threshold=self.alert_thresholds['disk_percent'],
                message=f"High disk usage: {self.system_metrics.disk_percent:.1f}%"
            ))
        
        # Error rate alert
        if self.application_metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts_to_add.append(Alert(
                timestamp=datetime.now(),
                level='warning' if self.application_metrics.error_rate < 10 else 'critical',
                metric='error_rate',
                value=self.application_metrics.error_rate,
                threshold=self.alert_thresholds['error_rate'],
                message=f"High error rate: {self.application_metrics.error_rate:.1f}%"
            ))
        
        # Response time alert
        if self.application_metrics.avg_response_time > self.alert_thresholds['response_time_ms']:
            alerts_to_add.append(Alert(
                timestamp=datetime.now(),
                level='warning',
                metric='response_time',
                value=self.application_metrics.avg_response_time,
                threshold=self.alert_thresholds['response_time_ms'],
                message=f"Slow response time: {self.application_metrics.avg_response_time:.0f}ms"
            ))
        
        # Add new alerts
        for alert in alerts_to_add:
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            logger.warning(f"ALERT: {alert.message}")
        
        # Remove resolved alerts
        self.active_alerts = [
            a for a in self.active_alerts
            if not self._is_alert_resolved(a)
        ]
    
    def _is_alert_resolved(self, alert: Alert) -> bool:
        """Check if an alert condition is resolved"""
        if not self.system_metrics or not self.application_metrics:
            return False
        
        if alert.metric == 'cpu_percent':
            return self.system_metrics.cpu_percent < alert.threshold * 0.9
        elif alert.metric == 'memory_percent':
            return self.system_metrics.memory_percent < alert.threshold * 0.9
        elif alert.metric == 'disk_percent':
            return self.system_metrics.disk_percent < alert.threshold * 0.9
        elif alert.metric == 'error_rate':
            return self.application_metrics.error_rate < alert.threshold * 0.8
        elif alert.metric == 'response_time':
            return self.application_metrics.avg_response_time < alert.threshold * 0.8
        
        return False
    
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics"""
        if not self.enable_prometheus or not self.system_metrics or not self.application_metrics:
            return
        
        try:
            self.prometheus_metrics['cpu_usage'].set(self.system_metrics.cpu_percent)
            self.prometheus_metrics['memory_usage'].set(self.system_metrics.memory_used)
            self.prometheus_metrics['memory_percent'].set(self.system_metrics.memory_percent)
            self.prometheus_metrics['disk_usage'].set(self.system_metrics.disk_used)
            self.prometheus_metrics['disk_percent'].set(self.system_metrics.disk_percent)
            self.prometheus_metrics['network_sent'].set(self.system_metrics.network_bytes_sent)
            self.prometheus_metrics['network_recv'].set(self.system_metrics.network_bytes_recv)
            self.prometheus_metrics['active_connections'].set(self.application_metrics.active_connections)
            self.prometheus_metrics['db_connections'].set(self.application_metrics.database_connections)
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
    
    def _store_metrics(self):
        """Store metrics in history"""
        if self.system_metrics and self.application_metrics:
            self.metrics_history.append({
                'timestamp': datetime.now().isoformat(),
                'system': asdict(self.system_metrics),
                'application': asdict(self.application_metrics)
            })
    
    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Track HTTP request"""
        self.request_count += 1
        self.last_request_time = time.time()
        
        if status_code >= 400:
            self.request_errors.append({
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'timestamp': datetime.now()
            })
        else:
            self.request_times.append(duration * 1000)  # Convert to milliseconds
        
        # Update Prometheus if enabled
        if self.enable_prometheus:
            try:
                self.prometheus_metrics['request_count'].labels(
                    method=method,
                    endpoint=endpoint,
                    status=str(status_code)
                ).inc()
                self.prometheus_metrics['request_duration'].labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
            except Exception as e:
                logger.debug(f"Error updating Prometheus request metrics: {e}")
    
    def update_cache_metrics(self, hits: int, misses: int):
        """Update cache metrics"""
        if self.application_metrics:
            total = hits + misses
            self.application_metrics.cache_hit_rate = (hits / total) if total > 0 else 0.0
        
        if self.enable_prometheus:
            try:
                self.prometheus_metrics['cache_hits'].inc(hits)
                self.prometheus_metrics['cache_misses'].inc(misses)
            except Exception as e:
                logger.debug(f"Error updating Prometheus cache metrics: {e}")
    
    def update_connection_metrics(self, active: int, db: int, redis: int):
        """Update connection metrics"""
        if self.application_metrics:
            self.application_metrics.active_connections = active
            self.application_metrics.database_connections = db
            self.application_metrics.redis_connections = redis
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'system': asdict(self.system_metrics) if self.system_metrics else None,
            'application': asdict(self.application_metrics) if self.application_metrics else None,
            'alerts': [asdict(a) for a in self.active_alerts],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        if not self.system_metrics or not self.application_metrics:
            return {
                'status': 'unknown',
                'message': 'Metrics not yet collected'
            }
        
        # Determine overall health
        critical_alerts = [a for a in self.active_alerts if a.level == 'critical']
        warning_alerts = [a for a in self.active_alerts if a.level == 'warning']
        
        if critical_alerts:
            status = 'critical'
        elif warning_alerts:
            status = 'degraded'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'alerts': {
                'critical': len(critical_alerts),
                'warning': len(warning_alerts),
                'total': len(self.active_alerts)
            },
            'system': {
                'cpu_percent': self.system_metrics.cpu_percent,
                'memory_percent': self.system_metrics.memory_percent,
                'disk_percent': self.system_metrics.disk_percent
            },
            'application': {
                'request_rate': self.application_metrics.request_rate,
                'error_rate': self.application_metrics.error_rate,
                'avg_response_time_ms': self.application_metrics.avg_response_time
            }
        }
    
    def get_recommendations(self) -> List[str]:
        """Get performance recommendations based on current metrics"""
        recommendations = []
        
        if not self.system_metrics or not self.application_metrics:
            return recommendations
        
        # CPU recommendations
        if self.system_metrics.cpu_percent > 70:
            recommendations.append(
                f"High CPU usage ({self.system_metrics.cpu_percent:.1f}%). "
                "Consider: optimizing queries, adding caching, or scaling horizontally."
            )
        
        # Memory recommendations
        if self.system_metrics.memory_percent > 80:
            recommendations.append(
                f"High memory usage ({self.system_metrics.memory_percent:.1f}%). "
                "Consider: reducing cache size, optimizing data structures, or increasing memory."
            )
        
        # Disk recommendations
        if self.system_metrics.disk_percent > 85:
            recommendations.append(
                f"High disk usage ({self.system_metrics.disk_percent:.1f}%). "
                "Consider: cleaning up logs, archiving old data, or increasing disk space."
            )
        
        # Error rate recommendations
        if self.application_metrics.error_rate > 3:
            recommendations.append(
                f"High error rate ({self.application_metrics.error_rate:.1f}%). "
                "Consider: reviewing error logs, fixing bugs, or improving error handling."
            )
        
        # Response time recommendations
        if self.application_metrics.avg_response_time > 500:
            recommendations.append(
                f"Slow response times ({self.application_metrics.avg_response_time:.0f}ms). "
                "Consider: database query optimization, caching, or code profiling."
            )
        
        # Cache recommendations
        if self.application_metrics.cache_hit_rate < 0.5:
            recommendations.append(
                f"Low cache hit rate ({self.application_metrics.cache_hit_rate*100:.1f}%). "
                "Consider: increasing cache TTL, warming cache, or expanding cache coverage."
            )
        
        return recommendations
