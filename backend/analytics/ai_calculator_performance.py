"""
AI Calculator Performance Monitoring Service
Monitor calculator load times, error rates, database performance, and payment processing.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from contextlib import contextmanager

import requests
from sqlalchemy import text, func, and_, or_, desc
from sqlalchemy.orm import Session
import statsd

from backend.database import get_db_session
from backend.models.analytics import AnalyticsEvent
from backend.analytics.ai_calculator_analytics import EventType

logger = logging.getLogger(__name__)

# Initialize StatsD client
statsd_client = statsd.StatsClient(
    host='localhost',
    port=8125,
    prefix='mingus.ai_calculator.performance'
)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_name: str
    metric_value: float
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ErrorMetric:
    """Error metric data structure"""
    error_type: str
    error_message: str
    timestamp: datetime
    frequency: int
    severity: str
    context: Optional[Dict[str, Any]] = None

class AICalculatorPerformanceMonitor:
    """Performance monitoring service for AI calculator"""
    
    def __init__(self):
        self.db_session = get_db_session()
        self.monitoring_active = False
        self.metrics_buffer = []
        self.error_buffer = []
        self.performance_thresholds = {
            'calculator_load_time': 3.0,  # seconds
            'database_query_time': 1.0,   # seconds
            'api_response_time': 2.0,     # seconds
            'error_rate_threshold': 0.05,  # 5%
            'memory_usage_threshold': 0.8, # 80%
            'cpu_usage_threshold': 0.7     # 70%
        }
    
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        try:
            self.monitoring_active = True
            
            # Start background monitoring threads
            threading.Thread(target=self._monitor_system_resources, daemon=True).start()
            threading.Thread(target=self._monitor_database_performance, daemon=True).start()
            threading.Thread(target=self._monitor_calculator_performance, daemon=True).start()
            
            logger.info("AI Calculator performance monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting performance monitoring: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        try:
            self.monitoring_active = False
            logger.info("AI Calculator performance monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping performance monitoring: {e}")
    
    @contextmanager
    def track_calculator_load_time(self, session_id: Optional[str] = None):
        """Track calculator load time"""
        start_time = time.time()
        try:
            yield
        finally:
            load_time = time.time() - start_time
            self._record_performance_metric(
                'calculator_load_time',
                load_time,
                {'session_id': session_id} if session_id else {}
            )
            
            # Alert if load time exceeds threshold
            if load_time > self.performance_thresholds['calculator_load_time']:
                self._alert_performance_issue('calculator_load_time', load_time)
    
    @contextmanager
    def track_database_query(self, query_name: str, session_id: Optional[str] = None):
        """Track database query performance"""
        start_time = time.time()
        try:
            yield
        finally:
            query_time = time.time() - start_time
            self._record_performance_metric(
                'database_query_time',
                query_time,
                {
                    'query_name': query_name,
                    'session_id': session_id
                } if session_id else {'query_name': query_name}
            )
            
            # Alert if query time exceeds threshold
            if query_time > self.performance_thresholds['database_query_time']:
                self._alert_performance_issue('database_query_time', query_time, {'query_name': query_name})
    
    @contextmanager
    def track_api_response_time(self, endpoint: str, session_id: Optional[str] = None):
        """Track API response time"""
        start_time = time.time()
        try:
            yield
        finally:
            response_time = time.time() - start_time
            self._record_performance_metric(
                'api_response_time',
                response_time,
                {
                    'endpoint': endpoint,
                    'session_id': session_id
                } if session_id else {'endpoint': endpoint}
            )
            
            # Alert if response time exceeds threshold
            if response_time > self.performance_thresholds['api_response_time']:
                self._alert_performance_issue('api_response_time', response_time, {'endpoint': endpoint})
    
    def track_error(self, error_type: str, error_message: str, 
                   severity: str = 'medium', session_id: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> None:
        """Track calculator errors"""
        try:
            error_metric = ErrorMetric(
                error_type=error_type,
                error_message=error_message,
                timestamp=datetime.utcnow(),
                frequency=1,
                severity=severity,
                context=context or {}
            )
            
            # Add session_id to context if provided
            if session_id:
                error_metric.context['session_id'] = session_id
            
            self._record_error_metric(error_metric)
            
            # Send to StatsD
            statsd_client.incr(f'errors.{error_type}')
            
            # Alert for high severity errors
            if severity in ['high', 'critical']:
                self._alert_error(error_metric)
                
        except Exception as e:
            logger.error(f"Error tracking error metric: {e}")
    
    def track_email_delivery(self, email_type: str, success: bool, 
                           delivery_time: Optional[float] = None) -> None:
        """Track email delivery performance"""
        try:
            # Track delivery success/failure
            if success:
                statsd_client.incr(f'email.{email_type}.delivered')
            else:
                statsd_client.incr(f'email.{email_type}.failed')
            
            # Track delivery time if provided
            if delivery_time:
                self._record_performance_metric(
                    'email_delivery_time',
                    delivery_time,
                    {'email_type': email_type, 'success': str(success)}
                )
            
            # Track email open rates (would need email service integration)
            # This is a placeholder for actual email tracking
            
        except Exception as e:
            logger.error(f"Error tracking email delivery: {e}")
    
    def track_payment_processing(self, payment_method: str, success: bool,
                               processing_time: Optional[float] = None,
                               amount: Optional[float] = None) -> None:
        """Track payment processing performance"""
        try:
            # Track payment success/failure
            if success:
                statsd_client.incr(f'payment.{payment_method}.success')
            else:
                statsd_client.incr(f'payment.{payment_method}.failed')
            
            # Track processing time
            if processing_time:
                self._record_performance_metric(
                    'payment_processing_time',
                    processing_time,
                    {'payment_method': payment_method, 'success': str(success)}
                )
            
            # Track payment amounts
            if amount:
                statsd_client.gauge(f'payment.{payment_method}.amount', amount)
            
        except Exception as e:
            logger.error(f"Error tracking payment processing: {e}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get performance metrics
            metrics = self._get_performance_metrics(start_time, end_time)
            
            # Get error metrics
            errors = self._get_error_metrics(start_time, end_time)
            
            # Calculate summary statistics
            summary = {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_hours': hours
                },
                'performance_metrics': {
                    'avg_calculator_load_time': self._calculate_average(metrics, 'calculator_load_time'),
                    'avg_database_query_time': self._calculate_average(metrics, 'database_query_time'),
                    'avg_api_response_time': self._calculate_average(metrics, 'api_response_time'),
                    'p95_calculator_load_time': self._calculate_percentile(metrics, 'calculator_load_time', 95),
                    'p95_database_query_time': self._calculate_percentile(metrics, 'database_query_time', 95),
                    'p95_api_response_time': self._calculate_percentile(metrics, 'api_response_time', 95)
                },
                'error_metrics': {
                    'total_errors': len(errors),
                    'error_rate': self._calculate_error_rate(errors, start_time, end_time),
                    'errors_by_type': self._group_errors_by_type(errors),
                    'errors_by_severity': self._group_errors_by_severity(errors)
                },
                'system_metrics': self._get_system_metrics(),
                'alerts': self._get_recent_alerts(start_time, end_time)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def _monitor_system_resources(self) -> None:
        """Monitor system resources in background"""
        while self.monitoring_active:
            try:
                # Monitor CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self._record_performance_metric('cpu_usage', cpu_percent, {})
                
                # Monitor memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self._record_performance_metric('memory_usage', memory_percent, {})
                
                # Monitor disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self._record_performance_metric('disk_usage', disk_percent, {})
                
                # Alert if thresholds exceeded
                if cpu_percent > self.performance_thresholds['cpu_usage_threshold'] * 100:
                    self._alert_performance_issue('cpu_usage', cpu_percent)
                
                if memory_percent > self.performance_thresholds['memory_usage_threshold'] * 100:
                    self._alert_performance_issue('memory_usage', memory_percent)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                time.sleep(60)
    
    def _monitor_database_performance(self) -> None:
        """Monitor database performance in background"""
        while self.monitoring_active:
            try:
                # Monitor database connection pool
                with self.track_database_query('health_check'):
                    self.db_session.execute(text('SELECT 1'))
                
                # Monitor slow queries
                slow_queries = self._get_slow_queries()
                for query in slow_queries:
                    self._alert_performance_issue('slow_database_query', query['execution_time'], query)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring database performance: {e}")
                time.sleep(300)
    
    def _monitor_calculator_performance(self) -> None:
        """Monitor calculator-specific performance in background"""
        while self.monitoring_active:
            try:
                # Monitor calculator completion rates
                completion_rate = self._calculate_completion_rate()
                self._record_performance_metric('calculator_completion_rate', completion_rate, {})
                
                # Monitor average session duration
                avg_session_duration = self._calculate_avg_session_duration()
                self._record_performance_metric('avg_session_duration', avg_session_duration, {})
                
                # Monitor error rates
                error_rate = self._calculate_error_rate_recent()
                self._record_performance_metric('error_rate', error_rate, {})
                
                # Alert if error rate exceeds threshold
                if error_rate > self.performance_thresholds['error_rate_threshold']:
                    self._alert_performance_issue('high_error_rate', error_rate)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring calculator performance: {e}")
                time.sleep(300)
    
    def _record_performance_metric(self, metric_name: str, metric_value: float, tags: Dict[str, str]) -> None:
        """Record performance metric"""
        try:
            metric = PerformanceMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                timestamp=datetime.utcnow(),
                tags=tags
            )
            
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Send to StatsD
            statsd_client.gauge(f'performance.{metric_name}', metric_value)
            
            # Flush buffer if it gets too large
            if len(self.metrics_buffer) > 1000:
                self._flush_metrics_buffer()
                
        except Exception as e:
            logger.error(f"Error recording performance metric: {e}")
    
    def _record_error_metric(self, error_metric: ErrorMetric) -> None:
        """Record error metric"""
        try:
            # Add to buffer
            self.error_buffer.append(error_metric)
            
            # Flush buffer if it gets too large
            if len(self.error_buffer) > 100:
                self._flush_error_buffer()
                
        except Exception as e:
            logger.error(f"Error recording error metric: {e}")
    
    def _alert_performance_issue(self, issue_type: str, value: float, context: Optional[Dict[str, Any]] = None) -> None:
        """Alert on performance issues"""
        try:
            alert = {
                'type': 'performance_issue',
                'issue_type': issue_type,
                'value': value,
                'threshold': self.performance_thresholds.get(issue_type, 0),
                'timestamp': datetime.utcnow().isoformat(),
                'context': context or {}
            }
            
            # Log alert
            logger.warning(f"Performance alert: {alert}")
            
            # Send to monitoring system (e.g., PagerDuty, Slack)
            self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")
    
    def _alert_error(self, error_metric: ErrorMetric) -> None:
        """Alert on errors"""
        try:
            alert = {
                'type': 'error_alert',
                'error_type': error_metric.error_type,
                'error_message': error_metric.error_message,
                'severity': error_metric.severity,
                'timestamp': error_metric.timestamp.isoformat(),
                'context': error_metric.context
            }
            
            # Log alert
            logger.error(f"Error alert: {alert}")
            
            # Send to monitoring system
            self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error creating error alert: {e}")
    
    def _send_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to monitoring system"""
        try:
            # This would integrate with your alerting system
            # For now, just log
            logger.info(f"Alert sent: {alert}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _flush_metrics_buffer(self) -> None:
        """Flush metrics buffer to database"""
        try:
            # This would store metrics in database
            # For now, just clear buffer
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
    
    def _flush_error_buffer(self) -> None:
        """Flush error buffer to database"""
        try:
            # This would store errors in database
            # For now, just clear buffer
            self.error_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing error buffer: {e}")
    
    def _get_performance_metrics(self, start_time: datetime, end_time: datetime) -> List[PerformanceMetric]:
        """Get performance metrics from database"""
        try:
            # This would query from database
            # For now, return buffer contents
            return [m for m in self.metrics_buffer if start_time <= m.timestamp <= end_time]
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return []
    
    def _get_error_metrics(self, start_time: datetime, end_time: datetime) -> List[ErrorMetric]:
        """Get error metrics from database"""
        try:
            # This would query from database
            # For now, return buffer contents
            return [e for e in self.error_buffer if start_time <= e.timestamp <= end_time]
            
        except Exception as e:
            logger.error(f"Error getting error metrics: {e}")
            return []
    
    def _calculate_average(self, metrics: List[PerformanceMetric], metric_name: str) -> float:
        """Calculate average for a metric"""
        try:
            relevant_metrics = [m.metric_value for m in metrics if m.metric_name == metric_name]
            return sum(relevant_metrics) / len(relevant_metrics) if relevant_metrics else 0.0
        except Exception as e:
            logger.error(f"Error calculating average: {e}")
            return 0.0
    
    def _calculate_percentile(self, metrics: List[PerformanceMetric], metric_name: str, percentile: int) -> float:
        """Calculate percentile for a metric"""
        try:
            relevant_metrics = sorted([m.metric_value for m in metrics if m.metric_name == metric_name])
            if not relevant_metrics:
                return 0.0
            
            index = int((percentile / 100) * len(relevant_metrics))
            return relevant_metrics[index] if index < len(relevant_metrics) else relevant_metrics[-1]
        except Exception as e:
            logger.error(f"Error calculating percentile: {e}")
            return 0.0
    
    def _calculate_error_rate(self, errors: List[ErrorMetric], start_time: datetime, end_time: datetime) -> float:
        """Calculate error rate"""
        try:
            # This would calculate based on total requests vs errors
            # For now, return simple ratio
            return len(errors) / 1000.0  # Assume 1000 requests per hour
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    def _group_errors_by_type(self, errors: List[ErrorMetric]) -> Dict[str, int]:
        """Group errors by type"""
        try:
            grouped = {}
            for error in errors:
                grouped[error.error_type] = grouped.get(error.error_type, 0) + 1
            return grouped
        except Exception as e:
            logger.error(f"Error grouping errors by type: {e}")
            return {}
    
    def _group_errors_by_severity(self, errors: List[ErrorMetric]) -> Dict[str, int]:
        """Group errors by severity"""
        try:
            grouped = {}
            for error in errors:
                grouped[error.severity] = grouped.get(error.severity, 0) + 1
            return grouped
        except Exception as e:
            logger.error(f"Error grouping errors by severity: {e}")
            return {}
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _get_recent_alerts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            # This would query from database
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def _get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow database queries"""
        try:
            # This would query database for slow queries
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    def _calculate_completion_rate(self) -> float:
        """Calculate calculator completion rate"""
        try:
            # This would calculate from actual data
            # For now, return estimated value
            return 0.75
        except Exception as e:
            logger.error(f"Error calculating completion rate: {e}")
            return 0.0
    
    def _calculate_avg_session_duration(self) -> float:
        """Calculate average session duration"""
        try:
            # This would calculate from actual data
            # For now, return estimated value
            return 180.0  # 3 minutes
        except Exception as e:
            logger.error(f"Error calculating average session duration: {e}")
            return 0.0
    
    def _calculate_error_rate_recent(self) -> float:
        """Calculate recent error rate"""
        try:
            # This would calculate from actual data
            # For now, return estimated value
            return 0.02  # 2%
        except Exception as e:
            logger.error(f"Error calculating recent error rate: {e}")
            return 0.0

# Global performance monitor instance
ai_calculator_performance = AICalculatorPerformanceMonitor()
