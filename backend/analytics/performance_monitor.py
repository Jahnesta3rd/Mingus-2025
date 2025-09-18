#!/usr/bin/env python3
"""
Performance Monitoring System for Job Recommendation Engine

This module provides comprehensive system performance monitoring including
API response times, processing metrics, resource usage, error tracking,
and real-time system health monitoring.

Features:
- API performance tracking and analysis
- Processing time monitoring
- System resource usage tracking
- Error rate monitoring and alerting
- Real-time metrics collection
- Performance optimization insights
- Cost per recommendation analysis
"""

import sqlite3
import json
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class APIPerformance:
    """Data class for API performance metrics"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    request_size: int = 0
    response_size: int = 0
    user_id: str = ""
    session_id: str = ""
    error_message: str = ""

@dataclass
class ProcessingMetrics:
    """Data class for processing performance metrics"""
    session_id: str
    process_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    memory_usage: int = 0
    cpu_usage: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: str = ""

@dataclass
class SystemResources:
    """Data class for system resource metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    queue_length: int
    error_rate: float
    response_time_avg: float

@dataclass
class ErrorLog:
    """Data class for error logging"""
    error_type: str
    error_message: str
    stack_trace: str = ""
    user_id: str = ""
    session_id: str = ""
    endpoint: str = ""
    severity: str = "medium"
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for job recommendation engine.
    
    Tracks API performance, processing times, system resources, and errors
    to provide insights for system optimization and health monitoring.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the performance monitoring system"""
        self.db_path = db_path
        self._init_database()
        self._monitoring_active = False
        self._monitor_thread = None
        self._performance_targets = {
            'max_response_time': 2000,  # 2 seconds
            'max_processing_time': 8000,  # 8 seconds
            'max_error_rate': 5.0,  # 5%
            'max_cpu_usage': 80.0,  # 80%
            'max_memory_usage': 85.0  # 85%
        }
        logger.info("PerformanceMonitor initialized successfully")
    
    def _init_database(self):
        """Initialize the analytics database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read and execute the schema
            with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Performance monitoring database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing performance monitoring database: {e}")
            raise
    
    def track_api_performance(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0,
        user_id: str = "",
        session_id: str = "",
        error_message: str = ""
    ) -> bool:
        """
        Track API performance metrics
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            response_time: Response time in milliseconds
            status_code: HTTP status code
            request_size: Request size in bytes
            response_size: Response size in bytes
            user_id: User identifier
            session_id: Session identifier
            error_message: Error message if applicable
            
        Returns:
            bool: Success status
        """
        try:
            performance = APIPerformance(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id,
                session_id=session_id,
                error_message=error_message
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_performance (
                    endpoint, method, response_time, status_code, request_size,
                    response_size, user_id, session_id, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                performance.endpoint, performance.method, performance.response_time,
                performance.status_code, performance.request_size, performance.response_size,
                performance.user_id, performance.session_id, performance.error_message
            ))
            
            conn.commit()
            conn.close()
            
            # Check for performance alerts
            self._check_performance_alerts(performance)
            
            logger.debug(f"Tracked API performance: {endpoint} - {response_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking API performance: {e}")
            return False
    
    @contextmanager
    def track_processing_time(
        self,
        session_id: str,
        process_name: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Context manager for tracking processing time
        
        Args:
            session_id: Session identifier
            process_name: Name of the process
            metadata: Additional metadata
            
        Yields:
            ProcessingMetrics: The metrics object for manual updates
        """
        start_time = datetime.now()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        metrics = ProcessingMetrics(
            session_id=session_id,
            process_name=process_name,
            start_time=start_time,
            end_time=start_time,
            duration=0.0,
            memory_usage=int(start_memory),
            cpu_usage=start_cpu,
            success=True,
            metadata=json.dumps(metadata or {})
        )
        
        try:
            yield metrics
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            logger.error(f"Error in process {process_name}: {e}")
            raise
        finally:
            end_time = datetime.now()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            metrics.end_time = end_time
            metrics.duration = (end_time - start_time).total_seconds()
            metrics.memory_usage = int(end_memory - start_memory)
            metrics.cpu_usage = end_cpu
            
            self._store_processing_metrics(metrics)
    
    def _store_processing_metrics(self, metrics: ProcessingMetrics):
        """Store processing metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processing_metrics (
                    session_id, process_name, start_time, end_time, duration,
                    memory_usage, cpu_usage, success, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.session_id, metrics.process_name, metrics.start_time,
                metrics.end_time, metrics.duration, metrics.memory_usage,
                metrics.cpu_usage, metrics.success, metrics.error_message,
                metrics.metadata
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Stored processing metrics: {metrics.process_name} - {metrics.duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error storing processing metrics: {e}")
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str = "",
        user_id: str = "",
        session_id: str = "",
        endpoint: str = "",
        severity: str = "medium"
    ) -> bool:
        """
        Log system errors with severity classification
        
        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace
            user_id: User identifier
            session_id: Session identifier
            endpoint: API endpoint where error occurred
            severity: Error severity level
            
        Returns:
            bool: Success status
        """
        try:
            error_log = ErrorLog(
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                user_id=user_id,
                session_id=session_id,
                endpoint=endpoint,
                severity=severity
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO error_logs (
                    error_type, error_message, stack_trace, user_id, session_id,
                    endpoint, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                error_log.error_type, error_log.error_message, error_log.stack_trace,
                error_log.user_id, error_log.session_id, error_log.endpoint,
                error_log.severity
            ))
            
            conn.commit()
            conn.close()
            
            # Check for error alerts
            self._check_error_alerts(error_log)
            
            logger.warning(f"Logged error: {error_type} - {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging error: {e}")
            return False
    
    def start_system_monitoring(self, interval: int = 60):
        """
        Start continuous system monitoring
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            logger.warning("System monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started system monitoring with {interval}s interval")
    
    def stop_system_monitoring(self):
        """Stop continuous system monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped system monitoring")
    
    def _monitor_system_resources(self, interval: int):
        """Monitor system resources continuously"""
        while self._monitoring_active:
            try:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get active connections (approximate)
                connections = len(psutil.net_connections())
                
                # Calculate error rate from recent API calls
                error_rate = self._calculate_recent_error_rate()
                
                # Calculate average response time
                avg_response_time = self._calculate_avg_response_time()
                
                # Store system resources
                resources = SystemResources(
                    timestamp=datetime.now(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    disk_usage=disk.percent,
                    active_connections=connections,
                    queue_length=0,  # Placeholder - would need queue monitoring
                    error_rate=error_rate,
                    response_time_avg=avg_response_time
                )
                
                self._store_system_resources(resources)
                
                # Check for resource alerts
                self._check_resource_alerts(resources)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(interval)
    
    def _store_system_resources(self, resources: SystemResources):
        """Store system resource metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_resources (
                    timestamp, cpu_usage, memory_usage, disk_usage,
                    active_connections, queue_length, error_rate, response_time_avg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resources.timestamp, resources.cpu_usage, resources.memory_usage,
                resources.disk_usage, resources.active_connections, resources.queue_length,
                resources.error_rate, resources.response_time_avg
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing system resources: {e}")
    
    def _calculate_recent_error_rate(self, minutes: int = 5) -> float:
        """Calculate error rate from recent API calls"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests
                FROM api_performance 
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                return (result[1] / result[0]) * 100
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    def _calculate_avg_response_time(self, minutes: int = 5) -> float:
        """Calculate average response time from recent API calls"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            cursor.execute('''
                SELECT AVG(response_time) as avg_response_time
                FROM api_performance 
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result[0] else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average response time: {e}")
            return 0.0
    
    def _check_performance_alerts(self, performance: APIPerformance):
        """Check for performance alerts"""
        if performance.response_time > self._performance_targets['max_response_time']:
            self._trigger_alert(
                'slow_response_time',
                f"Slow response time: {performance.endpoint} - {performance.response_time}ms"
            )
        
        if performance.status_code >= 500:
            self._trigger_alert(
                'server_error',
                f"Server error: {performance.endpoint} - {performance.status_code}"
            )
    
    def _check_resource_alerts(self, resources: SystemResources):
        """Check for resource usage alerts"""
        if resources.cpu_usage > self._performance_targets['max_cpu_usage']:
            self._trigger_alert(
                'high_cpu_usage',
                f"High CPU usage: {resources.cpu_usage}%"
            )
        
        if resources.memory_usage > self._performance_targets['max_memory_usage']:
            self._trigger_alert(
                'high_memory_usage',
                f"High memory usage: {resources.memory_usage}%"
            )
        
        if resources.error_rate > self._performance_targets['max_error_rate']:
            self._trigger_alert(
                'high_error_rate',
                f"High error rate: {resources.error_rate}%"
            )
    
    def _check_error_alerts(self, error_log: ErrorLog):
        """Check for error-based alerts"""
        if error_log.severity == ErrorSeverity.CRITICAL.value:
            self._trigger_alert(
                'critical_error',
                f"Critical error: {error_log.error_type} - {error_log.error_message}"
            )
    
    def _trigger_alert(self, alert_type: str, message: str):
        """Trigger a performance alert"""
        logger.warning(f"ALERT [{alert_type}]: {message}")
        # Here you would integrate with your alerting system
        # (email, Slack, PagerDuty, etc.)
    
    def get_performance_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance summary
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict containing performance summary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            # API performance metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time) as avg_response_time,
                    MIN(response_time) as min_response_time,
                    MAX(response_time) as max_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*) as error_rate,
                    COUNT(CASE WHEN response_time > 2000 THEN 1 END) * 100.0 / COUNT(*) as slow_request_rate
                FROM api_performance 
                WHERE timestamp >= ?
            ''', (start_time,))
            
            api_metrics = cursor.fetchone()
            
            # Processing metrics
            cursor.execute('''
                SELECT 
                    process_name,
                    COUNT(*) as total_processes,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    COUNT(CASE WHEN success = 0 THEN 1 END) * 100.0 / COUNT(*) as failure_rate
                FROM processing_metrics 
                WHERE start_time >= ?
                GROUP BY process_name
                ORDER BY avg_duration DESC
            ''', (start_time,))
            
            processing_metrics = []
            for row in cursor.fetchall():
                processing_metrics.append({
                    'process_name': row[0],
                    'total_processes': row[1],
                    'avg_duration': round(row[2], 2),
                    'max_duration': round(row[3], 2),
                    'failure_rate': round(row[4], 2)
                })
            
            # Error metrics
            cursor.execute('''
                SELECT 
                    severity,
                    COUNT(*) as count
                FROM error_logs 
                WHERE timestamp >= ?
                GROUP BY severity
                ORDER BY count DESC
            ''', (start_time,))
            
            error_metrics = dict(cursor.fetchall())
            
            # System resource metrics
            cursor.execute('''
                SELECT 
                    AVG(cpu_usage) as avg_cpu,
                    MAX(cpu_usage) as max_cpu,
                    AVG(memory_usage) as avg_memory,
                    MAX(memory_usage) as max_memory,
                    AVG(error_rate) as avg_error_rate
                FROM system_resources 
                WHERE timestamp >= ?
            ''', (start_time,))
            
            resource_metrics = cursor.fetchone()
            
            conn.close()
            
            return {
                'analysis_period_hours': hours,
                'api_metrics': {
                    'total_requests': api_metrics[0] or 0,
                    'avg_response_time': round(api_metrics[1] or 0, 2),
                    'min_response_time': round(api_metrics[2] or 0, 2),
                    'max_response_time': round(api_metrics[3] or 0, 2),
                    'error_rate': round(api_metrics[4] or 0, 2),
                    'slow_request_rate': round(api_metrics[5] or 0, 2)
                },
                'processing_metrics': processing_metrics,
                'error_metrics': error_metrics,
                'resource_metrics': {
                    'avg_cpu_usage': round(resource_metrics[0] or 0, 2),
                    'max_cpu_usage': round(resource_metrics[1] or 0, 2),
                    'avg_memory_usage': round(resource_metrics[2] or 0, 2),
                    'max_memory_usage': round(resource_metrics[3] or 0, 2),
                    'avg_error_rate': round(resource_metrics[4] or 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_cost_analysis(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost analysis for recommendations
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing cost analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get processing costs
            cursor.execute('''
                SELECT 
                    process_name,
                    COUNT(*) as total_processes,
                    AVG(duration) as avg_duration,
                    SUM(duration) as total_duration,
                    AVG(memory_usage) as avg_memory
                FROM processing_metrics 
                WHERE start_time >= ?
                GROUP BY process_name
            ''', (start_date,))
            
            processing_costs = []
            total_processing_time = 0
            
            for row in cursor.fetchall():
                process_name, total_processes, avg_duration, total_duration, avg_memory = row
                total_processing_time += total_duration
                
                # Estimate costs (these would be actual cloud costs in production)
                estimated_cost = total_duration * 0.001  # $0.001 per second
                
                processing_costs.append({
                    'process_name': process_name,
                    'total_processes': total_processes,
                    'avg_duration': round(avg_duration, 2),
                    'total_duration': round(total_duration, 2),
                    'avg_memory_mb': round(avg_memory, 2),
                    'estimated_cost': round(estimated_cost, 4)
                })
            
            # Get recommendation counts
            cursor.execute('''
                SELECT COUNT(*) as total_recommendations
                FROM job_recommendations 
                WHERE created_at >= ?
            ''', (start_date,))
            
            total_recommendations = cursor.fetchone()[0] or 0
            
            # Calculate cost per recommendation
            total_estimated_cost = sum(cost['estimated_cost'] for cost in processing_costs)
            cost_per_recommendation = total_estimated_cost / total_recommendations if total_recommendations > 0 else 0
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'total_recommendations': total_recommendations,
                'total_processing_time_hours': round(total_processing_time / 3600, 2),
                'total_estimated_cost': round(total_estimated_cost, 4),
                'cost_per_recommendation': round(cost_per_recommendation, 4),
                'processing_costs': processing_costs
            }
            
        except Exception as e:
            logger.error(f"Error getting cost analysis: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get real-time system metrics
        
        Returns:
            Dict containing real-time metrics
        """
        try:
            # Get current system state
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get recent performance metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Recent API performance
            cursor.execute('''
                SELECT 
                    AVG(response_time) as avg_response_time,
                    COUNT(*) as requests_last_minute
                FROM api_performance 
                WHERE timestamp >= datetime('now', '-1 minute')
            ''')
            
            api_result = cursor.fetchone()
            
            # Recent error rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests
                FROM api_performance 
                WHERE timestamp >= datetime('now', '-5 minutes')
            ''')
            
            error_result = cursor.fetchone()
            
            # Active sessions
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) as active_sessions
                FROM user_sessions 
                WHERE session_start >= datetime('now', '-30 minutes')
                AND (session_end IS NULL OR session_end >= datetime('now', '-5 minutes'))
            ''')
            
            session_result = cursor.fetchone()
            
            conn.close()
            
            # Calculate error rate
            error_rate = 0
            if error_result and error_result[0] > 0:
                error_rate = (error_result[1] / error_result[0]) * 100
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system_resources': {
                    'cpu_usage': round(cpu_usage, 2),
                    'memory_usage': round(memory.percent, 2),
                    'disk_usage': round(disk.percent, 2),
                    'available_memory_gb': round(memory.available / (1024**3), 2)
                },
                'api_performance': {
                    'avg_response_time': round(api_result[0] or 0, 2),
                    'requests_last_minute': api_result[1] or 0,
                    'error_rate': round(error_rate, 2)
                },
                'active_sessions': session_result[0] or 0,
                'system_health': self._calculate_system_health(cpu_usage, memory.percent, error_rate)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def _calculate_system_health(self, cpu: float, memory: float, error_rate: float) -> str:
        """Calculate overall system health status"""
        if cpu > 90 or memory > 95 or error_rate > 10:
            return "critical"
        elif cpu > 80 or memory > 85 or error_rate > 5:
            return "warning"
        elif cpu > 70 or memory > 75 or error_rate > 2:
            return "degraded"
        else:
            return "healthy"
