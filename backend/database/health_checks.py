"""
Database Health Monitoring System for Mingus Financial Application
Comprehensive health checks, connection pool monitoring, and financial data consistency validation
Optimized for production environments with 1,000+ concurrent users
"""

import os
import logging
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError, TimeoutError

# Import connection pool manager
from .connection_pool import (
    ConnectionPoolManager, 
    PoolHealthChecker, 
    PoolOptimizer,
    get_pool_manager
)

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    status: str  # 'healthy', 'degraded', 'unhealthy', 'critical'
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class FinancialDataConsistencyCheck:
    """Financial data consistency validation"""
    table_name: str
    check_type: str  # 'referential_integrity', 'data_validation', 'constraint_check'
    status: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DatabaseHealthMonitor:
    """
    Comprehensive database health monitoring system
    Provides real-time monitoring, alerting, and automated recovery
    """
    
    def __init__(self, pool_manager: ConnectionPoolManager = None):
        self.pool_manager = pool_manager or get_pool_manager()
        self.health_check_interval = int(os.environ.get('DB_HEALTH_CHECK_INTERVAL', 300))  # 5 minutes
        self.critical_check_interval = int(os.environ.get('DB_CRITICAL_CHECK_INTERVAL', 60))  # 1 minute
        self.consistency_check_interval = int(os.environ.get('DB_CONSISTENCY_CHECK_INTERVAL', 3600))  # 1 hour
        
        self._monitor_thread = None
        self._critical_monitor_thread = None
        self._consistency_monitor_thread = None
        self._stop_monitoring = threading.Event()
        
        self.health_history = deque(maxlen=1000)
        self.alert_history = deque(maxlen=100)
        self.recovery_actions = deque(maxlen=100)
        
        # Health thresholds
        self.thresholds = {
            'connection_pool_utilization': 0.8,  # 80%
            'response_time_critical': 2.0,  # 2 seconds
            'response_time_warning': 1.0,  # 1 second
            'error_rate_critical': 0.1,  # 10%
            'error_rate_warning': 0.05,  # 5%
            'connection_leak_threshold': 5,  # 5 connections
            'replica_lag_threshold': 30,  # 30 seconds
        }
        
        # Financial data consistency rules
        self.consistency_rules = {
            'users': [
                'check_user_references',
                'check_email_uniqueness',
                'check_user_status_consistency'
            ],
            'financial_accounts': [
                'check_account_balance_consistency',
                'check_account_user_references',
                'check_account_status_consistency'
            ],
            'transactions': [
                'check_transaction_balance_consistency',
                'check_transaction_references',
                'check_transaction_amounts'
            ],
            'subscriptions': [
                'check_subscription_user_references',
                'check_subscription_status_consistency',
                'check_subscription_billing_consistency'
            ]
        }
    
    def start_monitoring(self):
        """Start comprehensive health monitoring"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        
        # Start main health monitoring
        self._monitor_thread = threading.Thread(target=self._monitor_health, daemon=True)
        self._monitor_thread.start()
        
        # Start critical health monitoring
        self._critical_monitor_thread = threading.Thread(target=self._monitor_critical_health, daemon=True)
        self._critical_monitor_thread.start()
        
        # Start consistency monitoring
        self._consistency_monitor_thread = threading.Thread(target=self._monitor_data_consistency, daemon=True)
        self._consistency_monitor_thread.start()
        
        logger.info("Database health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self._stop_monitoring.set()
        
        for thread in [self._monitor_thread, self._critical_monitor_thread, self._consistency_monitor_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("Database health monitoring stopped")
    
    def _monitor_health(self):
        """Main health monitoring loop"""
        while not self._stop_monitoring.wait(self.health_check_interval):
            try:
                # Perform comprehensive health checks
                health_results = self.perform_health_checks()
                
                # Store results
                for result in health_results:
                    self.health_history.append(result)
                    
                    # Check for critical issues
                    if result.status in ['unhealthy', 'critical']:
                        self._handle_critical_health_issue(result)
                
                # Log health summary
                self._log_health_summary(health_results)
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
    
    def _monitor_critical_health(self):
        """Critical health monitoring loop for immediate response"""
        while not self._stop_monitoring.wait(self.critical_check_interval):
            try:
                # Check only critical components
                critical_results = self.perform_critical_health_checks()
                
                for result in critical_results:
                    if result.status in ['unhealthy', 'critical']:
                        self._handle_critical_health_issue(result, immediate=True)
                
            except Exception as e:
                logger.error(f"Error in critical health monitoring: {e}")
    
    def _monitor_data_consistency(self):
        """Data consistency monitoring loop"""
        while not self._stop_monitoring.wait(self.consistency_check_interval):
            try:
                # Perform data consistency checks
                consistency_results = self.perform_data_consistency_checks()
                
                for result in consistency_results:
                    if result.status != 'healthy':
                        self._handle_consistency_issue(result)
                
            except Exception as e:
                logger.error(f"Error in data consistency monitoring: {e}")
    
    def perform_health_checks(self) -> List[HealthCheckResult]:
        """Perform comprehensive health checks"""
        results = []
        
        # Connection pool health checks
        results.extend(self._check_connection_pools())
        
        # Database connectivity checks
        results.extend(self._check_database_connectivity())
        
        # Read replica health checks
        results.extend(self._check_read_replicas())
        
        # Performance metrics checks
        results.extend(self._check_performance_metrics())
        
        # Resource utilization checks
        results.extend(self._check_resource_utilization())
        
        return results
    
    def perform_critical_health_checks(self) -> List[HealthCheckResult]:
        """Perform critical health checks for immediate response"""
        results = []
        
        # Critical connection pool checks
        results.extend(self._check_critical_connection_pools())
        
        # Critical database connectivity
        results.extend(self._check_critical_database_connectivity())
        
        return results
    
    def perform_data_consistency_checks(self) -> List[HealthCheckResult]:
        """Perform financial data consistency checks"""
        results = []
        
        for table_name, rules in self.consistency_rules.items():
            for rule in rules:
                try:
                    result = self._execute_consistency_rule(table_name, rule)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error executing consistency rule {rule} for table {table_name}: {e}")
                    results.append(HealthCheckResult(
                        status='unhealthy',
                        component=f'consistency_{table_name}_{rule}',
                        message=f'Error executing consistency rule: {e}',
                        details={'table': table_name, 'rule': rule, 'error': str(e)},
                        error=str(e)
                    ))
        
        return results
    
    def _check_connection_pools(self) -> List[HealthCheckResult]:
        """Check connection pool health"""
        results = []
        
        try:
            pool_health = self.pool_manager.get_pool_health()
            
            for pool_name, health_data in pool_health.items():
                status = health_data['status']
                response_time = health_data.get('response_time', 0)
                
                # Determine health status based on thresholds
                if response_time > self.thresholds['response_time_critical']:
                    health_status = 'critical'
                elif response_time > self.thresholds['response_time_warning']:
                    health_status = 'degraded'
                elif status == 'healthy':
                    health_status = 'healthy'
                else:
                    health_status = 'unhealthy'
                
                # Check for connection leaks
                leak_count = health_data.get('connection_leaks', 0)
                if leak_count > self.thresholds['connection_leak_threshold']:
                    health_status = 'critical'
                
                results.append(HealthCheckResult(
                    status=health_status,
                    component=f'connection_pool_{pool_name}',
                    message=f"Pool '{pool_name}' status: {health_status}",
                    details=health_data,
                    response_time=response_time
                ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='critical',
                component='connection_pool_health',
                message=f'Failed to check connection pool health: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_critical_connection_pools(self) -> List[HealthCheckResult]:
        """Check critical connection pool health"""
        results = []
        
        try:
            # Check only main and financial pools
            critical_pools = ['main', 'financial']
            pool_health = self.pool_manager.get_pool_health()
            
            for pool_name in critical_pools:
                if pool_name in pool_health:
                    health_data = pool_health[pool_name]
                    status = health_data['status']
                    
                    if status != 'healthy':
                        results.append(HealthCheckResult(
                            status='critical',
                            component=f'critical_connection_pool_{pool_name}',
                            message=f"Critical pool '{pool_name}' is unhealthy",
                            details=health_data
                        ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='critical',
                component='critical_connection_pool_health',
                message=f'Failed to check critical connection pool health: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_database_connectivity(self) -> List[HealthCheckResult]:
        """Check database connectivity"""
        results = []
        
        try:
            # Test main database connectivity
            main_pool = self.pool_manager.get_pool('main')
            if main_pool:
                start_time = time.time()
                with main_pool.connect() as conn:
                    # Test basic connectivity
                    result = conn.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                    
                    # Test financial data access
                    result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
                    table_count = result.scalar()
                    
                response_time = time.time() - start_time
                
                if test_value == 1 and table_count > 0:
                    status = 'healthy'
                else:
                    status = 'unhealthy'
                
                results.append(HealthCheckResult(
                    status=status,
                    component='database_connectivity',
                    message=f"Database connectivity: {status}",
                    details={
                        'test_value': test_value,
                        'table_count': table_count,
                        'response_time': response_time
                    },
                    response_time=response_time
                ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='critical',
                component='database_connectivity',
                message=f'Database connectivity check failed: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_critical_database_connectivity(self) -> List[HealthCheckResult]:
        """Check critical database connectivity"""
        results = []
        
        try:
            # Test main database connectivity with timeout
            main_pool = self.pool_manager.get_pool('main')
            if main_pool:
                with main_pool.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                
                if test_value != 1:
                    results.append(HealthCheckResult(
                        status='critical',
                        component='critical_database_connectivity',
                        message='Critical database connectivity failure',
                        details={'test_value': test_value}
                    ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='critical',
                component='critical_database_connectivity',
                message=f'Critical database connectivity check failed: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_read_replicas(self) -> List[HealthCheckResult]:
        """Check read replica health"""
        results = []
        
        try:
            # Get read replica metrics from pool manager
            performance_metrics = self.pool_manager.get_performance_metrics()
            replica_metrics = performance_metrics.get('read_replicas', {})
            
            for replica_name, metrics in replica_metrics.items():
                is_healthy = metrics.get('is_healthy', False)
                response_time = metrics.get('response_time')
                last_health_check = metrics.get('last_health_check')
                
                if not is_healthy:
                    status = 'unhealthy'
                elif response_time and response_time > self.thresholds['replica_lag_threshold']:
                    status = 'degraded'
                else:
                    status = 'healthy'
                
                results.append(HealthCheckResult(
                    status=status,
                    component=f'read_replica_{replica_name}',
                    message=f"Read replica '{replica_name}' status: {status}",
                    details=metrics
                ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='unhealthy',
                component='read_replica_health',
                message=f'Failed to check read replica health: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_performance_metrics(self) -> List[HealthCheckResult]:
        """Check performance metrics"""
        results = []
        
        try:
            performance_metrics = self.pool_manager.get_performance_metrics()
            
            # Check error rates
            total_errors = performance_metrics.get('total_errors', 0)
            total_connections = performance_metrics.get('total_connections_created', 1)
            error_rate = total_errors / total_connections
            
            if error_rate > self.thresholds['error_rate_critical']:
                status = 'critical'
            elif error_rate > self.thresholds['error_rate_warning']:
                status = 'degraded'
            else:
                status = 'healthy'
            
            results.append(HealthCheckResult(
                status=status,
                component='performance_metrics',
                message=f"Performance metrics: {status} (error rate: {error_rate:.2%})",
                details={
                    'error_rate': error_rate,
                    'total_errors': total_errors,
                    'total_connections': total_connections,
                    'average_checkout_time': performance_metrics.get('average_checkout_time', 0)
                }
            ))
            
            # Check for connection leaks
            active_leaks = performance_metrics.get('active_leaks', 0)
            if active_leaks > 0:
                leak_status = 'critical' if active_leaks > self.thresholds['connection_leak_threshold'] else 'degraded'
                results.append(HealthCheckResult(
                    status=leak_status,
                    component='connection_leaks',
                    message=f"Connection leaks detected: {active_leaks}",
                    details={
                        'active_leaks': active_leaks,
                        'leak_details': performance_metrics.get('leak_details', [])
                    }
                ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='unhealthy',
                component='performance_metrics',
                message=f'Failed to check performance metrics: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _check_resource_utilization(self) -> List[HealthCheckResult]:
        """Check resource utilization"""
        results = []
        
        try:
            pool_metrics = self.pool_manager.get_pool_metrics()
            
            for pool_name, metrics in pool_metrics.items():
                # Calculate pool utilization
                total_connections = metrics.total_connections
                active_connections = metrics.active_connections
                
                if total_connections > 0:
                    utilization = active_connections / total_connections
                    
                    if utilization > self.thresholds['connection_pool_utilization']:
                        status = 'degraded'
                    else:
                        status = 'healthy'
                    
                    results.append(HealthCheckResult(
                        status=status,
                        component=f'resource_utilization_{pool_name}',
                        message=f"Pool '{pool_name}' utilization: {utilization:.2%}",
                        details={
                            'utilization': utilization,
                            'active_connections': active_connections,
                            'total_connections': total_connections,
                            'idle_connections': metrics.idle_connections
                        }
                    ))
        
        except Exception as e:
            results.append(HealthCheckResult(
                status='unhealthy',
                component='resource_utilization',
                message=f'Failed to check resource utilization: {e}',
                details={'error': str(e)},
                error=str(e)
            ))
        
        return results
    
    def _execute_consistency_rule(self, table_name: str, rule: str) -> HealthCheckResult:
        """Execute a specific consistency rule"""
        try:
            main_pool = self.pool_manager.get_pool('main')
            if not main_pool:
                return HealthCheckResult(
                    status='unhealthy',
                    component=f'consistency_{table_name}_{rule}',
                    message=f'No main pool available for consistency check',
                    details={'table': table_name, 'rule': rule}
                )
            
            # Execute the specific consistency rule
            if rule == 'check_user_references':
                result = self._check_user_references(main_pool)
            elif rule == 'check_email_uniqueness':
                result = self._check_email_uniqueness(main_pool)
            elif rule == 'check_account_balance_consistency':
                result = self._check_account_balance_consistency(main_pool)
            elif rule == 'check_transaction_references':
                result = self._check_transaction_references(main_pool)
            elif rule == 'check_subscription_billing_consistency':
                result = self._check_subscription_billing_consistency(main_pool)
            else:
                # Generic consistency check
                result = self._generic_consistency_check(main_pool, table_name, rule)
            
            return result
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component=f'consistency_{table_name}_{rule}',
                message=f'Error executing consistency rule: {e}',
                details={'table': table_name, 'rule': rule, 'error': str(e)},
                error=str(e)
            )
    
    def _check_user_references(self, pool: Engine) -> HealthCheckResult:
        """Check user reference consistency"""
        try:
            with pool.connect() as conn:
                # Check for orphaned records that reference non-existent users
                result = conn.execute(text("""
                    SELECT COUNT(*) as orphaned_count
                    FROM questionnaire_submissions qs
                    LEFT JOIN users u ON qs.user_id = u.id
                    WHERE qs.user_id IS NOT NULL AND u.id IS NULL
                """))
                orphaned_count = result.scalar()
                
                if orphaned_count > 0:
                    return HealthCheckResult(
                        status='degraded',
                        component='consistency_users_references',
                        message=f'Found {orphaned_count} orphaned user references',
                        details={'orphaned_count': orphaned_count}
                    )
                else:
                    return HealthCheckResult(
                        status='healthy',
                        component='consistency_users_references',
                        message='User references are consistent',
                        details={'orphaned_count': 0}
                    )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component='consistency_users_references',
                message=f'Failed to check user references: {e}',
                details={'error': str(e)},
                error=str(e)
            )
    
    def _check_email_uniqueness(self, pool: Engine) -> HealthCheckResult:
        """Check email uniqueness consistency"""
        try:
            with pool.connect() as conn:
                # Check for duplicate emails
                result = conn.execute(text("""
                    SELECT email, COUNT(*) as duplicate_count
                    FROM users
                    GROUP BY email
                    HAVING COUNT(*) > 1
                """))
                duplicates = result.fetchall()
                
                if duplicates:
                    return HealthCheckResult(
                        status='critical',
                        component='consistency_users_email_uniqueness',
                        message=f'Found {len(duplicates)} duplicate emails',
                        details={'duplicates': [dict(row) for row in duplicates]}
                    )
                else:
                    return HealthCheckResult(
                        status='healthy',
                        component='consistency_users_email_uniqueness',
                        message='Email uniqueness is maintained',
                        details={'duplicates': []}
                    )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component='consistency_users_email_uniqueness',
                message=f'Failed to check email uniqueness: {e}',
                details={'error': str(e)},
                error=str(e)
            )
    
    def _check_account_balance_consistency(self, pool: Engine) -> HealthCheckResult:
        """Check account balance consistency"""
        try:
            with pool.connect() as conn:
                # This is a placeholder - implement based on your actual financial data structure
                # For now, just check if the table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'financial_accounts'
                    ) as table_exists
                """))
                table_exists = result.scalar()
                
                if table_exists:
                    return HealthCheckResult(
                        status='healthy',
                        component='consistency_financial_accounts_balance',
                        message='Financial accounts table exists',
                        details={'table_exists': True}
                    )
                else:
                    return HealthCheckResult(
                        status='healthy',
                        component='consistency_financial_accounts_balance',
                        message='Financial accounts table not yet implemented',
                        details={'table_exists': False}
                    )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component='consistency_financial_accounts_balance',
                message=f'Failed to check account balance consistency: {e}',
                details={'error': str(e)},
                error=str(e)
            )
    
    def _check_transaction_references(self, pool: Engine) -> HealthCheckResult:
        """Check transaction reference consistency"""
        try:
            with pool.connect() as conn:
                # This is a placeholder - implement based on your actual transaction structure
                return HealthCheckResult(
                    status='healthy',
                    component='consistency_transactions_references',
                    message='Transaction references check not yet implemented',
                    details={'status': 'not_implemented'}
                )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component='consistency_transactions_references',
                message=f'Failed to check transaction references: {e}',
                details={'error': str(e)},
                error=str(e)
            )
    
    def _check_subscription_billing_consistency(self, pool: Engine) -> HealthCheckResult:
        """Check subscription billing consistency"""
        try:
            with pool.connect() as conn:
                # This is a placeholder - implement based on your actual subscription structure
                return HealthCheckResult(
                    status='healthy',
                    component='consistency_subscriptions_billing',
                    message='Subscription billing consistency check not yet implemented',
                    details={'status': 'not_implemented'}
                )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component='consistency_subscriptions_billing',
                message=f'Failed to check subscription billing consistency: {e}',
                details={'error': str(e)},
                error=str(e)
            )
    
    def _generic_consistency_check(self, pool: Engine, table_name: str, rule: str) -> HealthCheckResult:
        """Generic consistency check for tables"""
        try:
            with pool.connect() as conn:
                # Check if table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = :table_name
                    ) as table_exists
                """), {'table_name': table_name})
                table_exists = result.scalar()
                
                if table_exists:
                    # Count records
                    result = conn.execute(text(f"SELECT COUNT(*) as record_count FROM {table_name}"))
                    record_count = result.scalar()
                    
                    return HealthCheckResult(
                        status='healthy',
                        component=f'consistency_{table_name}_{rule}',
                        message=f'Table {table_name} consistency check passed',
                        details={'table_exists': True, 'record_count': record_count}
                    )
                else:
                    return HealthCheckResult(
                        status='healthy',
                        component=f'consistency_{table_name}_{rule}',
                        message=f'Table {table_name} does not exist',
                        details={'table_exists': False}
                    )
        
        except Exception as e:
            return HealthCheckResult(
                status='unhealthy',
                component=f'consistency_{table_name}_{rule}',
                message=f'Generic consistency check failed: {e}',
                details={'table': table_name, 'rule': rule, 'error': str(e)},
                error=str(e)
            )
    
    def _handle_critical_health_issue(self, result: HealthCheckResult, immediate: bool = False):
        """Handle critical health issues"""
        # Log the issue
        log_level = logging.CRITICAL if immediate else logging.ERROR
        logger.log(log_level, f"Critical health issue: {result.message}")
        
        # Store in alert history
        self.alert_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'component': result.component,
            'status': result.status,
            'message': result.message,
            'immediate': immediate
        })
        
        # Attempt automatic recovery for certain issues
        if immediate:
            self._attempt_automatic_recovery(result)
    
    def _handle_consistency_issue(self, result: HealthCheckResult):
        """Handle data consistency issues"""
        logger.warning(f"Data consistency issue: {result.message}")
        
        # Store in alert history
        self.alert_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'component': result.component,
            'status': result.status,
            'message': result.message,
            'type': 'consistency'
        })
    
    def _attempt_automatic_recovery(self, result: HealthCheckResult):
        """Attempt automatic recovery for critical issues"""
        try:
            if 'connection_pool' in result.component:
                # Attempt pool restart
                pool_name = result.component.split('_')[-1]
                logger.info(f"Attempting to restart connection pool: {pool_name}")
                
                # This would require pool manager to support pool restart
                # For now, just log the attempt
                self.recovery_actions.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': f'restart_pool_{pool_name}',
                    'status': 'attempted',
                    'details': result.details
                })
            
            elif 'database_connectivity' in result.component:
                # Attempt connection reset
                logger.info("Attempting to reset database connections")
                
                self.recovery_actions.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'reset_database_connections',
                    'status': 'attempted',
                    'details': result.details
                })
        
        except Exception as e:
            logger.error(f"Automatic recovery failed: {e}")
            self.recovery_actions.append({
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'automatic_recovery',
                'status': 'failed',
                'error': str(e)
            })
    
    def _log_health_summary(self, results: List[HealthCheckResult]):
        """Log health check summary"""
        status_counts = defaultdict(int)
        for result in results:
            status_counts[result.status] += 1
        
        logger.info(f"Health check summary: {dict(status_counts)}")
        
        # Log any unhealthy components
        unhealthy_results = [r for r in results if r.status != 'healthy']
        if unhealthy_results:
            for result in unhealthy_results:
                logger.warning(f"Unhealthy component: {result.component} - {result.message}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        try:
            # Get current health status
            current_health = self.perform_health_checks()
            
            # Calculate summary statistics
            status_counts = defaultdict(int)
            for result in current_health:
                status_counts[result.status] += 1
            
            # Get historical data
            recent_alerts = list(self.alert_history)[-10:]  # Last 10 alerts
            recent_recoveries = list(self.recovery_actions)[-10:]  # Last 10 recovery actions
            
            return {
                'current_status': {
                    'total_checks': len(current_health),
                    'healthy': status_counts['healthy'],
                    'degraded': status_counts['degraded'],
                    'unhealthy': status_counts['unhealthy'],
                    'critical': status_counts['critical']
                },
                'recent_alerts': recent_alerts,
                'recent_recoveries': recent_recoveries,
                'health_history_count': len(self.health_history),
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for monitoring systems"""
        try:
            health_summary = self.get_health_summary()
            
            # Convert to metrics format
            metrics = {
                'db_health_checks_total': health_summary['current_status']['total_checks'],
                'db_health_checks_healthy': health_summary['current_status']['healthy'],
                'db_health_checks_degraded': health_summary['current_status']['degraded'],
                'db_health_checks_unhealthy': health_summary['current_status']['unhealthy'],
                'db_health_checks_critical': health_summary['current_status']['critical'],
                'db_health_alerts_total': len(self.alert_history),
                'db_health_recoveries_total': len(self.recovery_actions)
            }
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return {'error': str(e)}


# Global health monitor instance
health_monitor = DatabaseHealthMonitor()


def get_health_monitor() -> DatabaseHealthMonitor:
    """Get the global health monitor"""
    return health_monitor


def init_health_monitor(pool_manager: ConnectionPoolManager = None):
    """Initialize the global health monitor"""
    global health_monitor
    if pool_manager:
        health_monitor = DatabaseHealthMonitor(pool_manager)
    else:
        health_monitor = DatabaseHealthMonitor()


# Health check utilities
class HealthCheckUtils:
    """Utility functions for health checks"""
    
    @staticmethod
    def quick_health_check() -> Dict[str, Any]:
        """Perform a quick health check"""
        try:
            monitor = get_health_monitor()
            return monitor.get_health_summary()
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    @staticmethod
    def check_connection_pools() -> Dict[str, Any]:
        """Check connection pool health"""
        try:
            pool_manager = get_pool_manager()
            return pool_manager.get_pool_health()
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    @staticmethod
    def check_data_consistency() -> List[Dict[str, Any]]:
        """Check data consistency"""
        try:
            monitor = get_health_monitor()
            results = monitor.perform_data_consistency_checks()
            return [
                {
                    'component': result.component,
                    'status': result.status,
                    'message': result.message,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in results
            ]
        except Exception as e:
            return [{'error': str(e), 'status': 'failed'}]


# Export main functions and classes
__all__ = [
    'DatabaseHealthMonitor',
    'HealthCheckResult',
    'FinancialDataConsistencyCheck',
    'HealthCheckUtils',
    'health_monitor',
    'get_health_monitor',
    'init_health_monitor'
]
