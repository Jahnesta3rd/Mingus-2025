"""
Enhanced Security Performance Monitoring System
Comprehensive monitoring for security system performance with minimal impact
"""

import time
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import psutil
import threading
from collections import defaultdict, deque
import statistics
from contextlib import contextmanager
import asyncio
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, Summary

# Prometheus metrics for security monitoring
SECURITY_OPERATIONS_TOTAL = Counter(
    'security_operations_total',
    'Total number of security operations',
    ['operation_type', 'status']
)

SECURITY_OPERATION_DURATION = Histogram(
    'security_operation_duration_seconds',
    'Duration of security operations in seconds',
    ['operation_type']
)

ENCRYPTION_OPERATION_DURATION = Histogram(
    'encryption_operation_duration_seconds',
    'Duration of encryption/decryption operations in seconds',
    ['algorithm', 'key_size', 'operation']
)

AUDIT_LOG_PERFORMANCE = Histogram(
    'audit_log_performance_seconds',
    'Audit logging performance metrics in seconds',
    ['operation_type']
)

KEY_ROTATION_DURATION = Histogram(
    'key_rotation_duration_seconds',
    'Key rotation operation duration in seconds',
    ['key_type']
)

SECURITY_SYSTEM_HEALTH = Gauge(
    'security_system_health_score',
    'Overall security system health score (0-100)'
)

PCI_COMPLIANCE_STATUS = Gauge(
    'pci_compliance_status',
    'PCI compliance status (1=compliant, 0=non-compliant)'
)

@dataclass
class SecurityPerformanceMetrics:
    """Security performance metrics data structure"""
    timestamp: datetime
    operation_type: str
    duration_ms: float
    success: bool
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class EncryptionMetrics:
    """Encryption/decryption performance metrics"""
    algorithm: str
    key_size: int
    operation: str  # 'encrypt' or 'decrypt'
    data_size_bytes: int
    duration_ms: float
    success: bool
    timestamp: datetime

@dataclass
class AuditLogMetrics:
    """Audit logging performance metrics"""
    operation_type: str
    duration_ms: float
    log_size_bytes: int
    success: bool
    timestamp: datetime
    batch_size: Optional[int]

@dataclass
class KeyRotationMetrics:
    """Key rotation performance metrics"""
    key_type: str
    old_key_id: str
    new_key_id: str
    duration_ms: float
    success: bool
    timestamp: datetime
    affected_entities: int

class SecurityPerformanceMonitor:
    """High-performance security system monitoring with minimal impact"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.metrics_buffer = deque(maxlen=1000)  # Buffer for batch processing
        self.performance_thresholds = {
            'encryption_max_duration_ms': 100,  # 100ms max for encryption
            'audit_log_max_duration_ms': 50,    # 50ms max for audit logging
            'key_rotation_max_duration_ms': 5000,  # 5s max for key rotation
            'security_operation_max_duration_ms': 200  # 200ms max for security ops
        }
        
        # Performance tracking
        self.operation_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.success_rates = defaultdict(lambda: {'success': 0, 'total': 0})
        
        # Start background metrics processor
        self._start_background_processor()
    
    def _start_background_processor(self):
        """Start background thread for processing metrics"""
        def process_metrics():
            while True:
                try:
                    if self.metrics_buffer:
                        self._process_batch_metrics()
                    time.sleep(5)  # Process every 5 seconds
                except Exception as e:
                    logger.error(f"Error in background metrics processor: {e}")
        
        thread = threading.Thread(target=process_metrics, daemon=True)
        thread.start()
    
    @contextmanager
    def measure_security_operation(self, operation_type: str, metadata: Dict[str, Any] = None):
        """Context manager for measuring security operation performance"""
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            self.error_counts[operation_type] += 1
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Update Prometheus metrics
            SECURITY_OPERATIONS_TOTAL.labels(
                operation_type=operation_type,
                status='success' if success else 'error'
            ).inc()
            
            SECURITY_OPERATION_DURATION.labels(
                operation_type=operation_type
            ).observe(duration_ms / 1000)
            
            # Store metrics
            metrics = SecurityPerformanceMetrics(
                timestamp=datetime.utcnow(),
                operation_type=operation_type,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            self._store_metrics(metrics)
            
            # Update success rates
            self.success_rates[operation_type]['total'] += 1
            if success:
                self.success_rates[operation_type]['success'] += 1
            
            # Check performance thresholds
            self._check_performance_thresholds(operation_type, duration_ms)
    
    @contextmanager
    def measure_encryption_operation(self, algorithm: str, key_size: int, operation: str, data_size_bytes: int):
        """Context manager for measuring encryption/decryption performance"""
        start_time = time.time()
        success = False
        
        try:
            yield
            success = True
        except Exception as e:
            logger.error(f"Encryption operation failed: {e}")
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Update Prometheus metrics
            ENCRYPTION_OPERATION_DURATION.labels(
                algorithm=algorithm,
                key_size=key_size,
                operation=operation
            ).observe(duration_ms / 1000)
            
            # Store encryption metrics
            metrics = EncryptionMetrics(
                algorithm=algorithm,
                key_size=key_size,
                operation=operation,
                data_size_bytes=data_size_bytes,
                duration_ms=duration_ms,
                success=success,
                timestamp=datetime.utcnow()
            )
            
            self._store_encryption_metrics(metrics)
    
    @contextmanager
    def measure_audit_logging(self, operation_type: str, log_size_bytes: int, batch_size: Optional[int] = None):
        """Context manager for measuring audit logging performance"""
        start_time = time.time()
        success = False
        
        try:
            yield
            success = True
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Update Prometheus metrics
            AUDIT_LOG_PERFORMANCE.labels(
                operation_type=operation_type
            ).observe(duration_ms / 1000)
            
            # Store audit log metrics
            metrics = AuditLogMetrics(
                operation_type=operation_type,
                duration_ms=duration_ms,
                log_size_bytes=log_size_bytes,
                success=success,
                timestamp=datetime.utcnow(),
                batch_size=batch_size
            )
            
            self._store_audit_log_metrics(metrics)
    
    @contextmanager
    def measure_key_rotation(self, key_type: str, old_key_id: str, new_key_id: str):
        """Context manager for measuring key rotation performance"""
        start_time = time.time()
        success = False
        affected_entities = 0
        
        try:
            yield
            success = True
            # Count affected entities (this would be implemented based on your system)
            affected_entities = self._count_affected_entities(key_type, old_key_id)
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Update Prometheus metrics
            KEY_ROTATION_DURATION.labels(
                key_type=key_type
            ).observe(duration_ms / 1000)
            
            # Store key rotation metrics
            metrics = KeyRotationMetrics(
                key_type=key_type,
                old_key_id=old_key_id,
                new_key_id=new_key_id,
                duration_ms=duration_ms,
                success=success,
                timestamp=datetime.utcnow(),
                affected_entities=affected_entities
            )
            
            self._store_key_rotation_metrics(metrics)
    
    def _store_metrics(self, metrics: SecurityPerformanceMetrics):
        """Store security performance metrics"""
        try:
            # Add to buffer for batch processing
            self.metrics_buffer.append(metrics)
            
            # Also store immediately for critical metrics
            if metrics.duration_ms > self.performance_thresholds['security_operation_max_duration_ms']:
                self._store_metrics_immediate(metrics)
                
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def _store_metrics_immediate(self, metrics: SecurityPerformanceMetrics):
        """Store metrics immediately in database"""
        try:
            query = text("""
                INSERT INTO security_performance_metrics 
                (timestamp, operation_type, duration_ms, success, error_message, metadata)
                VALUES (:timestamp, :operation_type, :duration_ms, :success, :error_message, :metadata)
            """)
            
            self.db_session.execute(query, {
                'timestamp': metrics.timestamp,
                'operation_type': metrics.operation_type,
                'duration_ms': metrics.duration_ms,
                'success': metrics.success,
                'error_message': metrics.error_message,
                'metadata': json.dumps(metrics.metadata)
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing metrics immediately: {e}")
            self.db_session.rollback()
    
    def _store_encryption_metrics(self, metrics: EncryptionMetrics):
        """Store encryption performance metrics"""
        try:
            query = text("""
                INSERT INTO encryption_performance_metrics 
                (algorithm, key_size, operation, data_size_bytes, duration_ms, success, timestamp)
                VALUES (:algorithm, :key_size, :operation, :data_size_bytes, :duration_ms, :success, :timestamp)
            """)
            
            self.db_session.execute(query, {
                'algorithm': metrics.algorithm,
                'key_size': metrics.key_size,
                'operation': metrics.operation,
                'data_size_bytes': metrics.data_size_bytes,
                'duration_ms': metrics.duration_ms,
                'success': metrics.success,
                'timestamp': metrics.timestamp
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing encryption metrics: {e}")
            self.db_session.rollback()
    
    def _store_audit_log_metrics(self, metrics: AuditLogMetrics):
        """Store audit logging performance metrics"""
        try:
            query = text("""
                INSERT INTO audit_log_performance_metrics 
                (operation_type, duration_ms, log_size_bytes, success, timestamp, batch_size)
                VALUES (:operation_type, :duration_ms, :log_size_bytes, :success, :timestamp, :batch_size)
            """)
            
            self.db_session.execute(query, {
                'operation_type': metrics.operation_type,
                'duration_ms': metrics.duration_ms,
                'log_size_bytes': metrics.log_size_bytes,
                'success': metrics.success,
                'timestamp': metrics.timestamp,
                'batch_size': metrics.batch_size
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing audit log metrics: {e}")
            self.db_session.rollback()
    
    def _store_key_rotation_metrics(self, metrics: KeyRotationMetrics):
        """Store key rotation performance metrics"""
        try:
            query = text("""
                INSERT INTO key_rotation_performance_metrics 
                (key_type, old_key_id, new_key_id, duration_ms, success, timestamp, affected_entities)
                VALUES (:key_type, :old_key_id, :new_key_id, :duration_ms, :success, :timestamp, :affected_entities)
            """)
            
            self.db_session.execute(query, {
                'key_type': metrics.key_type,
                'old_key_id': metrics.old_key_id,
                'new_key_id': metrics.new_key_id,
                'duration_ms': metrics.duration_ms,
                'success': metrics.success,
                'timestamp': metrics.timestamp,
                'affected_entities': metrics.affected_entities
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing key rotation metrics: {e}")
            self.db_session.rollback()
    
    def _process_batch_metrics(self):
        """Process metrics in batch for better performance"""
        try:
            if not self.metrics_buffer:
                return
            
            # Batch insert metrics
            metrics_to_insert = []
            while self.metrics_buffer:
                metrics_to_insert.append(self.metrics_buffer.popleft())
            
            if metrics_to_insert:
                self._batch_insert_metrics(metrics_to_insert)
                
        except Exception as e:
            logger.error(f"Error processing batch metrics: {e}")
    
    def _batch_insert_metrics(self, metrics_list: List[SecurityPerformanceMetrics]):
        """Batch insert metrics for better performance"""
        try:
            # Group by operation type for efficient batch insertion
            grouped_metrics = defaultdict(list)
            for metrics in metrics_list:
                grouped_metrics[metrics.operation_type].append(metrics)
            
            for operation_type, metrics in grouped_metrics.items():
                query = text("""
                    INSERT INTO security_performance_metrics 
                    (timestamp, operation_type, duration_ms, success, error_message, metadata)
                    VALUES (:timestamp, :operation_type, :duration_ms, :success, :error_message, :metadata)
                """)
                
                values = [
                    {
                        'timestamp': m.timestamp,
                        'operation_type': m.operation_type,
                        'duration_ms': m.duration_ms,
                        'success': m.success,
                        'error_message': m.error_message,
                        'metadata': json.dumps(m.metadata)
                    }
                    for m in metrics
                ]
                
                self.db_session.execute(query, values)
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error batch inserting metrics: {e}")
            self.db_session.rollback()
    
    def _check_performance_thresholds(self, operation_type: str, duration_ms: float):
        """Check if performance exceeds thresholds and alert if necessary"""
        try:
            threshold_key = f"{operation_type}_max_duration_ms"
            threshold = self.performance_thresholds.get(threshold_key, float('inf'))
            
            if duration_ms > threshold:
                logger.warning(
                    f"Performance threshold exceeded for {operation_type}: "
                    f"{duration_ms:.2f}ms > {threshold}ms"
                )
                
                # Update Prometheus alert metric
                SECURITY_SYSTEM_HEALTH.set(50)  # Degraded health
                
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
    
    def _count_affected_entities(self, key_type: str, old_key_id: str) -> int:
        """Count entities affected by key rotation"""
        try:
            # This would be implemented based on your specific system
            # For now, return a placeholder
            return 0
        except Exception as e:
            logger.error(f"Error counting affected entities: {e}")
            return 0
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security performance summary for the specified time period"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get overall performance metrics
            query = text("""
                SELECT 
                    operation_type,
                    COUNT(*) as total_operations,
                    AVG(duration_ms) as avg_duration_ms,
                    MAX(duration_ms) as max_duration_ms,
                    MIN(duration_ms) as min_duration_ms,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations
                FROM security_performance_metrics 
                WHERE timestamp >= :since_time
                GROUP BY operation_type
            """)
            
            results = self.db_session.execute(query, {'since_time': since_time}).fetchall()
            
            # Get encryption performance metrics
            encryption_query = text("""
                SELECT 
                    algorithm,
                    key_size,
                    operation,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(*) as total_operations
                FROM encryption_performance_metrics 
                WHERE timestamp >= :since_time
                GROUP BY algorithm, key_size, operation
            """)
            
            encryption_results = self.db_session.execute(encryption_query, {'since_time': since_time}).fetchall()
            
            # Get audit log performance metrics
            audit_query = text("""
                SELECT 
                    operation_type,
                    AVG(duration_ms) as avg_duration_ms,
                    AVG(log_size_bytes) as avg_log_size_bytes,
                    COUNT(*) as total_operations
                FROM audit_log_performance_metrics 
                WHERE timestamp >= :since_time
                GROUP BY operation_type
            """)
            
            audit_results = self.db_session.execute(audit_query, {'since_time': since_time}).fetchall()
            
            # Calculate success rates
            success_rates = {}
            for operation_type in self.success_rates:
                total = self.success_rates[operation_type]['total']
                success = self.success_rates[operation_type]['success']
                if total > 0:
                    success_rates[operation_type] = (success / total) * 100
                else:
                    success_rates[operation_type] = 0.0
            
            return {
                'time_period_hours': hours,
                'overall_performance': [
                    {
                        'operation_type': row.operation_type,
                        'total_operations': row.total_operations,
                        'avg_duration_ms': float(row.avg_duration_ms) if row.avg_duration_ms else 0.0,
                        'max_duration_ms': float(row.max_duration_ms) if row.max_duration_ms else 0.0,
                        'min_duration_ms': float(row.min_duration_ms) if row.min_duration_ms else 0.0,
                        'success_rate_percent': (row.successful_operations / row.total_operations * 100) if row.total_operations > 0 else 0.0
                    }
                    for row in results
                ],
                'encryption_performance': [
                    {
                        'algorithm': row.algorithm,
                        'key_size': row.key_size,
                        'operation': row.operation,
                        'avg_duration_ms': float(row.avg_duration_ms) if row.avg_duration_ms else 0.0,
                        'total_operations': row.total_operations
                    }
                    for row in encryption_results
                ],
                'audit_log_performance': [
                    {
                        'operation_type': row.operation_type,
                        'avg_duration_ms': float(row.avg_duration_ms) if row.avg_duration_ms else 0.0,
                        'avg_log_size_bytes': float(row.avg_log_size_bytes) if row.avg_log_size_bytes else 0.0,
                        'total_operations': row.total_operations
                    }
                    for row in audit_results
                ],
                'success_rates': success_rates,
                'error_counts': dict(self.error_counts),
                'performance_thresholds': self.performance_thresholds
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time security performance metrics"""
        try:
            # Get current system performance
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Get recent operation counts
            recent_operations = defaultdict(int)
            for operation_type in self.success_rates:
                recent_operations[operation_type] = self.success_rates[operation_type]['total']
            
            # Calculate current health score
            health_score = self._calculate_health_score()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system_performance': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3)
                },
                'recent_operations': dict(recent_operations),
                'current_health_score': health_score,
                'active_alerts': len([m for m in self.metrics_buffer if not m.success]),
                'buffer_size': len(self.metrics_buffer)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def _calculate_health_score(self) -> float:
        """Calculate overall security system health score (0-100)"""
        try:
            if not self.success_rates:
                return 100.0
            
            total_success_rate = 0.0
            total_operations = 0
            
            for operation_type, rates in self.success_rates.items():
                if rates['total'] > 0:
                    success_rate = (rates['success'] / rates['total']) * 100
                    total_success_rate += success_rate * rates['total']
                    total_operations += rates['total']
            
            if total_operations == 0:
                return 100.0
            
            weighted_success_rate = total_success_rate / total_operations
            
            # Factor in error counts
            total_errors = sum(self.error_counts.values())
            error_penalty = min(total_errors * 5, 20)  # Max 20 point penalty
            
            health_score = max(0, weighted_success_rate - error_penalty)
            
            # Update Prometheus metric
            SECURITY_SYSTEM_HEALTH.set(health_score)
            
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0
    
    def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Clean up old metrics to maintain database performance"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up security performance metrics
            query = text("""
                DELETE FROM security_performance_metrics 
                WHERE timestamp < :cutoff_date
            """)
            
            self.db_session.execute(query, {'cutoff_date': cutoff_date})
            
            # Clean up encryption metrics
            query = text("""
                DELETE FROM encryption_performance_metrics 
                WHERE timestamp < :cutoff_date
            """)
            
            self.db_session.execute(query, {'cutoff_date': cutoff_date})
            
            # Clean up audit log metrics
            query = text("""
                DELETE FROM audit_log_performance_metrics 
                WHERE timestamp < :cutoff_date
            """)
            
            self.db_session.execute(query, {'cutoff_date': cutoff_date})
            
            # Clean up key rotation metrics
            query = text("""
                DELETE FROM key_rotation_performance_metrics 
                WHERE timestamp < :cutoff_date
            """)
            
            self.db_session.execute(query, {'cutoff_date': cutoff_date})
            
            self.db_session.commit()
            
            logger.info(f"Cleaned up metrics older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            self.db_session.rollback()

# Example usage functions
def monitor_security_operation(operation_type: str, func, *args, **kwargs):
    """Decorator for monitoring security operations"""
    def wrapper(*args, **kwargs):
        with SecurityPerformanceMonitor.measure_security_operation(operation_type):
            return func(*args, **kwargs)
    return wrapper

def monitor_encryption(algorithm: str, key_size: int, operation: str, data_size_bytes: int):
    """Decorator for monitoring encryption operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with SecurityPerformanceMonitor.measure_encryption_operation(algorithm, key_size, operation, data_size_bytes):
                return func(*args, **kwargs)
        return wrapper
    return decorator 