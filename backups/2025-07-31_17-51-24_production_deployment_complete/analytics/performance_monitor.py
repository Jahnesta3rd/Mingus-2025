"""
Performance Monitoring System for Job Recommendation Engine
Real-time monitoring of system performance and optimization
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import deque, defaultdict
import logging
from contextlib import contextmanager

from backend.services.cache_service import CacheService
from backend.analytics.analytics_service import PerformanceMetrics, AnalyticsService

logger = logging.getLogger(__name__)

@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    time_window: int  # seconds
    alert_callback: Optional[Callable] = None

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    query_time: float
    query_count: int
    slow_queries: int
    connection_count: int
    cache_hit_rate: float
    index_usage: Dict[str, float]

@dataclass
class APIMetrics:
    """API performance metrics"""
    endpoint: str
    response_time: float
    status_code: int
    request_size: int
    response_size: int
    error_count: int
    rate_limit_hits: int

class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self, cache_service: CacheService, analytics_service: AnalyticsService):
        """Initialize performance monitor"""
        self.cache_service = cache_service
        self.analytics_service = analytics_service
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Performance data storage
        self.performance_history = deque(maxlen=1000)  # Last 1000 measurements
        self.database_metrics = deque(maxlen=100)
        self.api_metrics = deque(maxlen=500)
        
        # Thresholds for alerts
        self.thresholds = {
            'response_time': PerformanceThreshold(
                metric_name='response_time',
                warning_threshold=5.0,  # 5 seconds
                critical_threshold=8.0,  # 8 seconds
                time_window=300,  # 5 minutes
                alert_callback=self.alert_response_time
            ),
            'memory_usage': PerformanceThreshold(
                metric_name='memory_usage',
                warning_threshold=800,  # 800MB
                critical_threshold=1000,  # 1GB
                time_window=300,
                alert_callback=self.alert_memory_usage
            ),
            'cpu_usage': PerformanceThreshold(
                metric_name='cpu_usage',
                warning_threshold=70.0,  # 70%
                critical_threshold=90.0,  # 90%
                time_window=300,
                alert_callback=self.alert_cpu_usage
            ),
            'error_rate': PerformanceThreshold(
                metric_name='error_rate',
                warning_threshold=0.02,  # 2%
                critical_threshold=0.05,  # 5%
                time_window=300,
                alert_callback=self.alert_error_rate
            ),
            'database_query_time': PerformanceThreshold(
                metric_name='database_query_time',
                warning_threshold=1.0,  # 1 second
                critical_threshold=3.0,  # 3 seconds
                time_window=300,
                alert_callback=self.alert_database_performance
            )
        }
        
        # Query tracking
        self.query_times = deque(maxlen=1000)
        self.slow_queries = deque(maxlen=100)
        
        # API tracking
        self.api_calls = defaultdict(lambda: deque(maxlen=100))
        self.api_errors = defaultdict(int)
        self.rate_limit_hits = defaultdict(int)
        
    def start_monitoring(self, interval: int = 30) -> None:
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Performance monitoring started with {interval}s interval")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current performance metrics
                metrics = self.collect_performance_metrics()
                
                # Store in history
                self.performance_history.append(metrics)
                
                # Send to analytics service
                self.analytics_service.track_performance_metrics(metrics)
                
                # Check thresholds and trigger alerts
                self.check_thresholds(metrics)
                
                # Store in cache for real-time access
                self.store_metrics_in_cache(metrics)
                
                # Wait for next interval
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                time.sleep(interval)
    
    def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        # System metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Calculate average response time from recent measurements
        recent_response_times = list(self.performance_history)[-10:] if self.performance_history else []
        avg_response_time = sum(m.response_time for m in recent_response_times) / len(recent_response_times) if recent_response_times else 0.0
        
        # Calculate database query time
        recent_query_times = list(self.query_times)[-10:] if self.query_times else []
        avg_query_time = sum(recent_query_times) / len(recent_query_times) if recent_query_times else 0.0
        
        # Calculate cache hit rate
        cache_hit_rate = self.calculate_cache_hit_rate()
        
        # Calculate error rate
        error_rate = self.calculate_error_rate()
        
        # Estimate concurrent users (simplified)
        concurrent_users = self.estimate_concurrent_users()
        
        # Calculate API calls per minute
        api_calls_per_minute = self.calculate_api_calls_per_minute()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            response_time=avg_response_time,
            memory_usage=memory_info.used / 1024 / 1024,  # MB
            cpu_usage=cpu_percent,
            database_query_time=avg_query_time,
            cache_hit_rate=cache_hit_rate,
            error_rate=error_rate,
            concurrent_users=concurrent_users,
            api_calls_per_minute=api_calls_per_minute
        )
    
    def track_response_time(self, response_time: float) -> None:
        """Track individual response time"""
        # Add to performance history
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            response_time=response_time,
            memory_usage=0.0,
            cpu_usage=0.0,
            database_query_time=0.0,
            cache_hit_rate=0.0,
            error_rate=0.0,
            concurrent_users=0,
            api_calls_per_minute=0
        )
        
        self.performance_history.append(metrics)
        
        # Check if this is a slow response
        if response_time > self.thresholds['response_time'].warning_threshold:
            self.log_slow_response(response_time)
    
    def track_database_query(self, query: str, execution_time: float) -> None:
        """Track database query performance"""
        self.query_times.append(execution_time)
        
        # Track slow queries
        if execution_time > self.thresholds['database_query_time'].warning_threshold:
            self.slow_queries.append({
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.warning(f"Slow database query detected: {execution_time:.2f}s - {query[:100]}")
    
    def track_api_call(self, endpoint: str, response_time: float, status_code: int, 
                      request_size: int = 0, response_size: int = 0) -> None:
        """Track API call performance"""
        api_metric = APIMetrics(
            endpoint=endpoint,
            response_time=response_time,
            status_code=status_code,
            request_size=request_size,
            response_size=response_size,
            error_count=0,
            rate_limit_hits=0
        )
        
        self.api_metrics.append(api_metric)
        self.api_calls[endpoint].append(response_time)
        
        # Track errors
        if status_code >= 400:
            self.api_errors[endpoint] += 1
        
        # Track rate limit hits
        if status_code == 429:
            self.rate_limit_hits[endpoint] += 1
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring operation performance"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            yield
        except Exception as e:
            # Track error
            self.track_error(operation_name, str(e))
            raise
        finally:
            # Calculate metrics
            execution_time = time.time() - start_time
            memory_used = psutil.virtual_memory().used - start_memory
            
            # Track performance
            self.track_operation_performance(operation_name, execution_time, memory_used)
    
    def track_operation_performance(self, operation_name: str, execution_time: float, memory_used: int) -> None:
        """Track operation-specific performance"""
        operation_metrics = {
            'operation_name': operation_name,
            'execution_time': execution_time,
            'memory_used': memory_used,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in cache
        cache_key = f"operation_metrics:{operation_name}"
        operation_history = self.cache_service.get(cache_key) or []
        operation_history.append(operation_metrics)
        
        # Keep only last 100 operations
        if len(operation_history) > 100:
            operation_history = operation_history[-100:]
        
        self.cache_service.set(cache_key, operation_history, ttl=3600)
        
        # Check for slow operations
        if execution_time > 5.0:  # 5 seconds threshold
            logger.warning(f"Slow operation detected: {operation_name} took {execution_time:.2f}s")
    
    def track_error(self, operation_name: str, error_message: str) -> None:
        """Track error occurrences"""
        error_data = {
            'operation_name': operation_name,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in cache
        error_history = self.cache_service.get('error_history') or []
        error_history.append(error_data)
        
        # Keep only last 100 errors
        if len(error_history) > 100:
            error_history = error_history[-100:]
        
        self.cache_service.set('error_history', error_history, ttl=3600)
        
        logger.error(f"Error in {operation_name}: {error_message}")
    
    def check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check performance thresholds and trigger alerts"""
        for threshold_name, threshold in self.thresholds.items():
            current_value = getattr(metrics, threshold_name, 0.0)
            
            if current_value >= threshold.critical_threshold:
                self.trigger_alert(threshold, current_value, 'critical')
            elif current_value >= threshold.warning_threshold:
                self.trigger_alert(threshold, current_value, 'warning')
    
    def trigger_alert(self, threshold: PerformanceThreshold, current_value: float, severity: str) -> None:
        """Trigger performance alert"""
        alert_data = {
            'metric_name': threshold.metric_name,
            'current_value': current_value,
            'threshold_value': threshold.critical_threshold if severity == 'critical' else threshold.warning_threshold,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'message': f"{threshold.metric_name} exceeded {severity} threshold: {current_value:.2f}"
        }
        
        # Store alert in cache
        alerts = self.cache_service.get('performance_alerts') or []
        alerts.append(alert_data)
        
        # Keep only last 50 alerts
        if len(alerts) > 50:
            alerts = alerts[-50:]
        
        self.cache_service.set('performance_alerts', alerts, ttl=86400)
        
        # Call alert callback if provided
        if threshold.alert_callback:
            try:
                threshold.alert_callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.warning(f"Performance alert: {alert_data['message']}")
    
    def calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would typically query cache statistics
        # For now, return a placeholder value
        return 0.85  # 85% cache hit rate
    
    def calculate_error_rate(self) -> float:
        """Calculate error rate from recent API calls"""
        if not self.api_metrics:
            return 0.0
        
        recent_metrics = list(self.api_metrics)[-100:]  # Last 100 API calls
        error_count = sum(1 for metric in recent_metrics if metric.status_code >= 400)
        
        return error_count / len(recent_metrics) if recent_metrics else 0.0
    
    def estimate_concurrent_users(self) -> int:
        """Estimate number of concurrent users"""
        # This would typically use session data or active connections
        # For now, return a placeholder value
        return 25  # Estimated 25 concurrent users
    
    def calculate_api_calls_per_minute(self) -> int:
        """Calculate API calls per minute"""
        if not self.api_metrics:
            return 0
        
        # Count API calls in the last minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_calls = sum(1 for metric in self.api_metrics 
                          if metric.timestamp > one_minute_ago)
        
        return recent_calls
    
    def store_metrics_in_cache(self, metrics: PerformanceMetrics) -> None:
        """Store current metrics in cache for real-time access"""
        # Store current metrics
        self.cache_service.set('current_performance', {
            'response_time': metrics.response_time,
            'memory_usage': metrics.memory_usage,
            'cpu_usage': metrics.cpu_usage,
            'database_query_time': metrics.database_query_time,
            'cache_hit_rate': metrics.cache_hit_rate,
            'error_rate': metrics.error_rate,
            'concurrent_users': metrics.concurrent_users,
            'api_calls_per_minute': metrics.api_calls_per_minute,
            'timestamp': metrics.timestamp.isoformat()
        }, ttl=300)  # 5 minutes TTL
        
        # Store historical data
        history_key = f"performance_history:{datetime.now().strftime('%Y%m%d_%H')}"
        history_data = self.cache_service.get(history_key) or []
        history_data.append({
            'response_time': metrics.response_time,
            'memory_usage': metrics.memory_usage,
            'cpu_usage': metrics.cpu_usage,
            'timestamp': metrics.timestamp.isoformat()
        })
        
        # Keep only last 60 measurements (1 hour of data)
        if len(history_data) > 60:
            history_data = history_data[-60:]
        
        self.cache_service.set(history_key, history_data, ttl=7200)  # 2 hours TTL
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified time period"""
        summary = {
            'current_metrics': self.cache_service.get('current_performance'),
            'alerts': self.cache_service.get('performance_alerts') or [],
            'slow_queries': list(self.slow_queries)[-10:],  # Last 10 slow queries
            'api_performance': self.get_api_performance_summary(),
            'error_summary': self.get_error_summary(),
            'recommendations': self.get_performance_recommendations()
        }
        
        return summary
    
    def get_api_performance_summary(self) -> Dict[str, Any]:
        """Get API performance summary"""
        if not self.api_metrics:
            return {}
        
        api_summary = {}
        for endpoint in set(metric.endpoint for metric in self.api_metrics):
            endpoint_metrics = [m for m in self.api_metrics if m.endpoint == endpoint]
            
            if endpoint_metrics:
                avg_response_time = sum(m.response_time for m in endpoint_metrics) / len(endpoint_metrics)
                error_count = sum(1 for m in endpoint_metrics if m.status_code >= 400)
                total_calls = len(endpoint_metrics)
                
                api_summary[endpoint] = {
                    'avg_response_time': avg_response_time,
                    'error_rate': error_count / total_calls if total_calls > 0 else 0.0,
                    'total_calls': total_calls,
                    'error_count': error_count
                }
        
        return api_summary
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        error_history = self.cache_service.get('error_history') or []
        
        if not error_history:
            return {}
        
        # Group errors by operation
        error_counts = {}
        for error in error_history:
            operation = error.get('operation_name', 'unknown')
            error_counts[operation] = error_counts.get(operation, 0) + 1
        
        return {
            'total_errors': len(error_history),
            'error_by_operation': error_counts,
            'recent_errors': error_history[-10:]  # Last 10 errors
        }
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        current_metrics = self.cache_service.get('current_performance')
        
        if not current_metrics:
            return recommendations
        
        # Response time recommendations
        if current_metrics.get('response_time', 0) > 5.0:
            recommendations.append("Consider implementing caching for frequently accessed data")
            recommendations.append("Optimize database queries and add indexes")
        
        # Memory usage recommendations
        if current_metrics.get('memory_usage', 0) > 800:
            recommendations.append("Review memory usage and implement garbage collection optimization")
            recommendations.append("Consider scaling up server resources")
        
        # Cache hit rate recommendations
        if current_metrics.get('cache_hit_rate', 0) < 0.8:
            recommendations.append("Increase cache size and optimize cache key strategies")
            recommendations.append("Review cache invalidation policies")
        
        # Error rate recommendations
        if current_metrics.get('error_rate', 0) > 0.02:
            recommendations.append("Investigate and fix error sources")
            recommendations.append("Implement better error handling and retry mechanisms")
        
        return recommendations
    
    def log_slow_response(self, response_time: float) -> None:
        """Log slow response for investigation"""
        slow_response_data = {
            'response_time': response_time,
            'timestamp': datetime.now().isoformat(),
            'stack_trace': self.get_current_stack_trace()
        }
        
        # Store in cache
        slow_responses = self.cache_service.get('slow_responses') or []
        slow_responses.append(slow_response_data)
        
        # Keep only last 50 slow responses
        if len(slow_responses) > 50:
            slow_responses = slow_responses[-50:]
        
        self.cache_service.set('slow_responses', slow_responses, ttl=3600)
        
        logger.warning(f"Slow response detected: {response_time:.2f}s")
    
    def get_current_stack_trace(self) -> str:
        """Get current stack trace for debugging"""
        import traceback
        return traceback.format_stack()
    
    # Alert callback methods
    def alert_response_time(self, alert_data: Dict[str, Any]) -> None:
        """Handle response time alerts"""
        logger.critical(f"CRITICAL: Response time alert - {alert_data['message']}")
        # Could send notifications, scale resources, etc.
    
    def alert_memory_usage(self, alert_data: Dict[str, Any]) -> None:
        """Handle memory usage alerts"""
        logger.critical(f"CRITICAL: Memory usage alert - {alert_data['message']}")
        # Could trigger garbage collection, scale resources, etc.
    
    def alert_cpu_usage(self, alert_data: Dict[str, Any]) -> None:
        """Handle CPU usage alerts"""
        logger.critical(f"CRITICAL: CPU usage alert - {alert_data['message']}")
        # Could scale resources, optimize processes, etc.
    
    def alert_error_rate(self, alert_data: Dict[str, Any]) -> None:
        """Handle error rate alerts"""
        logger.critical(f"CRITICAL: Error rate alert - {alert_data['message']}")
        # Could trigger investigation, rollback changes, etc.
    
    def alert_database_performance(self, alert_data: Dict[str, Any]) -> None:
        """Handle database performance alerts"""
        logger.critical(f"CRITICAL: Database performance alert - {alert_data['message']}")
        # Could optimize queries, add indexes, etc. 