"""
Error monitoring and alerting system for the Mingus financial application.
Provides comprehensive error tracking, performance monitoring, and alerting capabilities.
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis not available, using in-memory storage")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, system metrics will be limited")


class ErrorSeverity(Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts that can be triggered."""
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_EVENT = "security_event"
    FINANCIAL_TRANSACTION_FAILURE = "financial_transaction_failure"
    DATABASE_CONNECTION_ISSUE = "database_connection_issue"
    EXTERNAL_SERVICE_FAILURE = "external_service_failure"
    MEMORY_USAGE_HIGH = "memory_usage_high"
    CPU_USAGE_HIGH = "cpu_usage_high"
    DISK_SPACE_LOW = "disk_space_low"


@dataclass
class ErrorEvent:
    """Represents an error event for monitoring."""
    timestamp: datetime
    error_type: str
    error_class: str
    error_message: str
    severity: ErrorSeverity
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    environment: str = "unknown"


@dataclass
class PerformanceMetric:
    """Represents a performance metric for monitoring."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Represents an alert that has been triggered."""
    timestamp: datetime
    alert_type: AlertType
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class ErrorTracker:
    """Tracks errors and provides analytics."""
    
    def __init__(self, window_size: int = 3600, max_events: int = 10000):
        self.window_size = window_size  # seconds
        self.max_events = max_events
        self.error_events: deque = deque(maxlen=max_events)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        self.user_error_counts: Dict[str, int] = defaultdict(int)
        self.ip_error_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # Initialize Redis if available
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed: {e}")
                self.redis_client = None
    
    def record_error(self, error_event: ErrorEvent):
        """Record an error event for monitoring."""
        with self.lock:
            # Add to in-memory storage
            self.error_events.append(error_event)
            
            # Update counters
            self.error_counts[error_event.error_type] += 1
            self.severity_counts[error_event.severity] += 1
            
            if error_event.user_id:
                self.user_error_counts[error_event.user_id] += 1
            
            if error_event.ip_address:
                self.ip_error_counts[error_event.ip_address] += 1
            
            # Store in Redis if available
            if self.redis_client:
                self._store_error_in_redis(error_event)
            
            # Clean up old events
            self._cleanup_old_events()
    
    def _store_error_in_redis(self, error_event: ErrorEvent):
        """Store error event in Redis for persistence."""
        try:
            # Store error event
            error_key = f"error:{error_event.timestamp.timestamp()}:{error_event.error_type}"
            error_data = {
                'timestamp': error_event.timestamp.isoformat(),
                'error_type': error_event.error_type,
                'error_class': error_event.error_class,
                'error_message': error_event.error_message,
                'severity': error_event.severity.value,
                'user_id': error_event.user_id or '',
                'request_id': error_event.request_id or '',
                'ip_address': error_event.ip_address or '',
                'environment': error_event.environment
            }
            
            # Store with expiration
            self.redis_client.hmset(error_key, error_data)
            self.redis_client.expire(error_key, self.window_size)
            
            # Update counters in Redis
            self.redis_client.hincrby('error_counts', error_event.error_type, 1)
            self.redis_client.hincrby('severity_counts', error_event.severity.value, 1)
            
            if error_event.user_id:
                self.redis_client.hincrby('user_error_counts', error_event.user_id, 1)
            
            if error_event.ip_address:
                self.redis_client.hincrby('ip_error_counts', error_event.ip_address, 1)
                
        except Exception as e:
            print(f"Failed to store error in Redis: {e}")
    
    def _cleanup_old_events(self):
        """Remove events older than the window size."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_size)
        
        # Remove old events from in-memory storage
        while self.error_events and self.error_events[0].timestamp < cutoff_time:
            old_event = self.error_events.popleft()
            
            # Update counters
            self.error_counts[old_event.error_type] = max(0, self.error_counts[old_event.error_type] - 1)
            self.severity_counts[old_event.severity] = max(0, self.severity_counts[old_event.severity] - 1)
            
            if old_event.user_id:
                self.user_error_counts[old_event.user_id] = max(0, self.user_error_counts[old_event.user_id] - 1)
            
            if old_event.ip_address:
                self.ip_error_counts[old_event.ip_address] = max(0, self.ip_error_counts[old_event.ip_address] - 1)
    
    def get_error_rate(self, error_type: str = None, window_seconds: int = None) -> float:
        """Calculate error rate for a specific type or overall."""
        if window_seconds is None:
            window_seconds = self.window_size
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        with self.lock:
            if error_type:
                # Count specific error type
                count = sum(1 for event in self.error_events 
                          if event.timestamp >= cutoff_time and event.error_type == error_type)
            else:
                # Count all errors
                count = sum(1 for event in self.error_events 
                          if event.timestamp >= cutoff_time)
            
            # Calculate rate per second
            return count / window_seconds if window_seconds > 0 else 0
    
    def get_error_summary(self, window_seconds: int = None) -> Dict[str, Any]:
        """Get summary of errors in the specified window."""
        if window_seconds is None:
            window_seconds = self.window_size
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        with self.lock:
            recent_events = [event for event in self.error_events 
                           if event.timestamp >= cutoff_time]
            
            summary = {
                'total_errors': len(recent_events),
                'error_rate_per_second': len(recent_events) / window_seconds if window_seconds > 0 else 0,
                'error_types': defaultdict(int),
                'severity_distribution': defaultdict(int),
                'top_users': defaultdict(int),
                'top_ips': defaultdict(int),
                'time_distribution': defaultdict(int)
            }
            
            for event in recent_events:
                summary['error_types'][event.error_type] += 1
                summary['severity_distribution'][event.severity.value] += 1
                
                if event.user_id:
                    summary['top_users'][event.user_id] += 1
                
                if event.ip_address:
                    summary['top_ips'][event.ip_address] += 1
                
                # Group by hour
                hour = event.timestamp.replace(minute=0, second=0, microsecond=0)
                summary['time_distribution'][hour.isoformat()] += 1
            
            # Convert defaultdict to regular dict
            summary['error_types'] = dict(summary['error_types'])
            summary['severity_distribution'] = dict(summary['severity_distribution'])
            summary['top_users'] = dict(summary['top_users'])
            summary['top_ips'] = dict(summary['top_ips'])
            summary['time_distribution'] = dict(summary['time_distribution'])
            
            return summary


class PerformanceMonitor:
    """Monitors application performance metrics."""
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=10000)
        self.lock = threading.Lock()
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True
                )
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed: {e}")
                self.redis_client = None
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self.lock:
            self.metrics.append(metric)
            
            if self.redis_client:
                self._store_metric_in_redis(metric)
    
    def _store_metric_in_redis(self, metric: PerformanceMetric):
        """Store metric in Redis for persistence."""
        try:
            metric_key = f"metric:{metric.timestamp.timestamp()}:{metric.metric_name}"
            metric_data = {
                'timestamp': metric.timestamp.isoformat(),
                'metric_name': metric.metric_name,
                'value': str(metric.value),
                'unit': metric.unit,
                'tags': str(metric.tags),
                'metadata': str(metric.metadata)
            }
            
            self.redis_client.hmset(metric_key, metric_data)
            self.redis_client.expire(metric_key, 86400)  # 24 hours
            
        except Exception as e:
            print(f"Failed to store metric in Redis: {e}")
    
    def get_metric_average(self, metric_name: str, window_seconds: int = 300) -> float:
        """Calculate average value for a metric in the specified window."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        with self.lock:
            recent_metrics = [metric for metric in self.metrics 
                            if metric.timestamp >= cutoff_time and metric.metric_name == metric_name]
            
            if not recent_metrics:
                return 0.0
            
            total_value = sum(metric.value for metric in recent_metrics)
            return total_value / len(recent_metrics)
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system performance metrics."""
        metrics = {}
        
        if PSUTIL_AVAILABLE:
            try:
                # CPU usage
                metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                metrics['memory_percent'] = memory.percent
                metrics['memory_available_gb'] = memory.available / (1024**3)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                metrics['disk_percent'] = disk.percent
                metrics['disk_free_gb'] = disk.free / (1024**3)
                
                # Network I/O
                network = psutil.net_io_counters()
                metrics['network_bytes_sent'] = network.bytes_sent
                metrics['network_bytes_recv'] = network.bytes_recv
                
            except Exception as e:
                print(f"Failed to get system metrics: {e}")
        
        return metrics


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self, error_tracker: ErrorTracker, performance_monitor: PerformanceMonitor):
        self.error_tracker = error_tracker
        self.performance_monitor = performance_monitor
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertType, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Alert thresholds
        self.thresholds = {
            'error_rate_threshold': 0.1,  # 10% error rate
            'memory_usage_threshold': 80.0,  # 80% memory usage
            'cpu_usage_threshold': 80.0,  # 80% CPU usage
            'disk_usage_threshold': 90.0,  # 90% disk usage
            'response_time_threshold': 2.0,  # 2 seconds
        }
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def add_alert_handler(self, alert_type: AlertType, handler: Callable):
        """Add a handler for a specific alert type."""
        self.alert_handlers[alert_type].append(handler)
    
    def trigger_alert(self, alert: Alert):
        """Trigger an alert and notify handlers."""
        with self.lock:
            self.alerts.append(alert)
            
            # Notify handlers
            for handler in self.alert_handlers[alert.alert_type]:
                try:
                    handler(alert)
                except Exception as e:
                    print(f"Alert handler failed: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop that checks for alert conditions."""
        while True:
            try:
                self._check_error_rate_alerts()
                self._check_performance_alerts()
                self._check_system_alerts()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_error_rate_alerts(self):
        """Check if error rates exceed thresholds."""
        error_rate = self.error_tracker.get_error_rate()
        
        if error_rate > self.thresholds['error_rate_threshold']:
            alert = Alert(
                timestamp=datetime.utcnow(),
                alert_type=AlertType.ERROR_RATE_THRESHOLD,
                severity=ErrorSeverity.HIGH,
                message=f"Error rate {error_rate:.2f} exceeds threshold {self.thresholds['error_rate_threshold']}",
                context={'current_rate': error_rate, 'threshold': self.thresholds['error_rate_threshold']}
            )
            self.trigger_alert(alert)
    
    def _check_performance_alerts(self):
        """Check if performance metrics exceed thresholds."""
        # Check response time
        avg_response_time = self.performance_monitor.get_metric_average('response_time', 300)
        if avg_response_time > self.thresholds['response_time_threshold']:
            alert = Alert(
                timestamp=datetime.utcnow(),
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=ErrorSeverity.MEDIUM,
                message=f"Average response time {avg_response_time:.2f}s exceeds threshold {self.thresholds['response_time_threshold']}s",
                context={'current_avg': avg_response_time, 'threshold': self.thresholds['response_time_threshold']}
            )
            self.trigger_alert(alert)
    
    def _check_system_alerts(self):
        """Check if system metrics exceed thresholds."""
        system_metrics = self.performance_monitor.get_system_metrics()
        
        # Check memory usage
        if 'memory_percent' in system_metrics and system_metrics['memory_percent'] > self.thresholds['memory_usage_threshold']:
            alert = Alert(
                timestamp=datetime.utcnow(),
                alert_type=AlertType.MEMORY_USAGE_HIGH,
                severity=ErrorSeverity.MEDIUM,
                message=f"Memory usage {system_metrics['memory_percent']:.1f}% exceeds threshold {self.thresholds['memory_usage_threshold']}%",
                context={'current_usage': system_metrics['memory_percent'], 'threshold': self.thresholds['memory_usage_threshold']}
            )
            self.trigger_alert(alert)
        
        # Check CPU usage
        if 'cpu_percent' in system_metrics and system_metrics['cpu_percent'] > self.thresholds['cpu_usage_threshold']:
            alert = Alert(
                timestamp=datetime.utcnow(),
                alert_type=AlertType.CPU_USAGE_HIGH,
                severity=ErrorSeverity.MEDIUM,
                message=f"CPU usage {system_metrics['cpu_percent']:.1f}% exceeds threshold {self.thresholds['cpu_usage_threshold']}%",
                context={'current_usage': system_metrics['cpu_percent'], 'threshold': self.thresholds['cpu_usage_threshold']}
            )
            self.trigger_alert(alert)
        
        # Check disk usage
        if 'disk_percent' in system_metrics and system_metrics['disk_percent'] > self.thresholds['disk_usage_threshold']:
            alert = Alert(
                timestamp=datetime.utcnow(),
                alert_type=AlertType.DISK_SPACE_LOW,
                severity=ErrorSeverity.HIGH,
                message=f"Disk usage {system_metrics['disk_percent']:.1f}% exceeds threshold {self.thresholds['disk_usage_threshold']}%",
                context={'current_usage': system_metrics['disk_percent'], 'threshold': self.thresholds['disk_usage_threshold']}
            )
            self.trigger_alert(alert)
    
    def get_active_alerts(self, severity: ErrorSeverity = None) -> List[Alert]:
        """Get active (unacknowledged) alerts."""
        with self.lock:
            if severity:
                return [alert for alert in self.alerts if not alert.acknowledged and alert.severity == severity]
            else:
                return [alert for alert in self.alerts if not alert.acknowledged]
    
    def acknowledge_alert(self, alert_index: int, acknowledged_by: str):
        """Acknowledge an alert."""
        with self.lock:
            if 0 <= alert_index < len(self.alerts):
                alert = self.alerts[alert_index]
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()


class MingusMonitoring:
    """Main monitoring class that coordinates all monitoring components."""
    
    def __init__(self, app_name: str = "mingus"):
        self.app_name = app_name
        self.error_tracker = ErrorTracker()
        self.performance_monitor = PerformanceMonitor()
        self.alert_manager = AlertManager(self.error_tracker, self.performance_monitor)
        
        # Initialize default alert handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default alert handlers."""
        
        def log_alert(alert: Alert):
            """Log alerts to console and file."""
            print(f"ALERT [{alert.severity.value.upper()}] {alert.alert_type.value}: {alert.message}")
            
            # Log to file
            try:
                from ..logging.logger import get_logger
                logger = get_logger('mingus.monitoring')
                logger.warning(f"Alert triggered: {alert.message}", extra={
                    'extra_fields': {
                        'alert_type': alert.alert_type.value,
                        'severity': alert.severity.value,
                        'context': alert.context
                    }
                })
            except Exception as e:
                print(f"Failed to log alert: {e}")
        
        # Register default handler for all alert types
        for alert_type in AlertType:
            self.alert_manager.add_alert_handler(alert_type, log_alert)
    
    def record_error(self, error_type: str, error_class: str, error_message: str,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        """Record an error for monitoring."""
        error_event = ErrorEvent(
            timestamp=datetime.utcnow(),
            error_type=error_type,
            error_class=error_class,
            error_message=error_message,
            severity=severity,
            environment=os.getenv('FLASK_ENV', 'unknown'),
            **kwargs
        )
        
        self.error_tracker.record_error(error_event)
    
    def record_performance_metric(self, metric_name: str, value: float, 
                                unit: str = None, **kwargs):
        """Record a performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            value=value,
            unit=unit or 'count',
            tags=kwargs.get('tags', {}),
            metadata=kwargs.get('metadata', {})
        )
        
        self.performance_monitor.record_metric(metric)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the application."""
        error_summary = self.error_tracker.get_error_summary(300)  # Last 5 minutes
        system_metrics = self.performance_monitor.get_system_metrics()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Determine overall health
        if error_summary['total_errors'] > 10 or any(alert.severity == ErrorSeverity.CRITICAL for alert in active_alerts):
            health_status = "critical"
        elif error_summary['total_errors'] > 5 or any(alert.severity == ErrorSeverity.HIGH for alert in active_alerts):
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            'status': health_status,
            'timestamp': datetime.utcnow().isoformat(),
            'error_summary': error_summary,
            'system_metrics': system_metrics,
            'active_alerts_count': len(active_alerts),
            'uptime': self._get_uptime()
        }
    
    def _get_uptime(self) -> str:
        """Get application uptime."""
        try:
            import psutil
            process = psutil.Process()
            uptime_seconds = time.time() - process.create_time()
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "unknown"


# Global monitoring instance
_monitoring_instance = None


def init_monitoring(app_name: str = "mingus") -> MingusMonitoring:
    """Initialize the monitoring system."""
    global _monitoring_instance
    
    if _monitoring_instance is None:
        _monitoring_instance = MingusMonitoring(app_name)
    
    return _monitoring_instance


def get_monitoring() -> MingusMonitoring:
    """Get the global monitoring instance."""
    if _monitoring_instance is None:
        raise RuntimeError("Monitoring not initialized. Call init_monitoring() first.")
    
    return _monitoring_instance
