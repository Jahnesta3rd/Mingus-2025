"""
Database Connection Pool Management for Communication System
Comprehensive connection pooling with monitoring, health checks, and optimization
"""

import os
import logging
import threading
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Connection pool metrics"""
    pool_size: int = 0
    checked_in: int = 0
    checked_out: int = 0
    overflow: int = 0
    invalid: int = 0
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connection_errors: int = 0
    checkout_errors: int = 0
    checkin_errors: int = 0
    last_checkout_time: Optional[datetime] = None
    last_checkin_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ConnectionPoolManager:
    """
    Comprehensive connection pool manager for the communication system
    Provides monitoring, health checks, and optimization
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engines = {}
        self.pool_metrics = {}
        self.monitoring_enabled = True
        self.health_check_interval = 300  # 5 minutes
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            'total_connections_created': 0,
            'total_connections_closed': 0,
            'total_checkouts': 0,
            'total_checkins': 0,
            'total_errors': 0,
            'average_checkout_time': 0.0,
            'average_checkin_time': 0.0
        }
        
        if self.database_url:
            self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize connection pools for different contexts"""
        
        # Main application pool
        self.create_pool(
            name='main',
            database_url=self.database_url,
            pool_size=int(os.environ.get('DB_POOL_SIZE', 20)),
            max_overflow=int(os.environ.get('DB_MAX_OVERFLOW', 30)),
            pool_recycle=int(os.environ.get('DB_POOL_RECYCLE', 3600)),
            pool_timeout=int(os.environ.get('DB_POOL_TIMEOUT', 30)),
            echo=os.environ.get('DB_ECHO', 'false').lower() == 'true'
        )
        
        # Celery worker pool
        self.create_pool(
            name='celery',
            database_url=self.database_url,
            pool_size=int(os.environ.get('CELERY_DB_POOL_SIZE', 10)),
            max_overflow=int(os.environ.get('CELERY_DB_MAX_OVERFLOW', 20)),
            pool_recycle=int(os.environ.get('CELERY_DB_POOL_RECYCLE', 1800)),
            pool_timeout=int(os.environ.get('CELERY_DB_POOL_TIMEOUT', 30)),
            echo=os.environ.get('CELERY_DB_ECHO', 'false').lower() == 'true'
        )
        
        # Analytics pool (for heavy reporting queries)
        self.create_pool(
            name='analytics',
            database_url=self.database_url,
            pool_size=int(os.environ.get('ANALYTICS_DB_POOL_SIZE', 5)),
            max_overflow=int(os.environ.get('ANALYTICS_DB_MAX_OVERFLOW', 10)),
            pool_recycle=int(os.environ.get('ANALYTICS_DB_POOL_RECYCLE', 7200)),
            pool_timeout=int(os.environ.get('ANALYTICS_DB_POOL_TIMEOUT', 60)),
            echo=os.environ.get('ANALYTICS_DB_ECHO', 'false').lower() == 'true'
        )
        
        logger.info("Connection pools initialized successfully")
    
    def create_pool(self, name: str, database_url: str, **pool_kwargs):
        """Create a new connection pool"""
        
        # Default pool settings
        default_settings = {
            'poolclass': QueuePool,
            'pool_pre_ping': True,
            'pool_reset_on_return': 'commit',
            'connect_args': {
                'application_name': f'mingus_communication_{name}',
                'options': '-c timezone=utc -c statement_timeout=30000',
                'connect_timeout': 10,
                'command_timeout': 30,
                'sslmode': os.environ.get('DB_SSL_MODE', 'prefer')
            }
        }
        
        # Merge with provided settings
        pool_settings = {**default_settings, **pool_kwargs}
        
        # Create engine
        engine = create_engine(database_url, **pool_settings)
        
        # Setup event listeners
        self._setup_pool_events(engine, name)
        
        # Store engine and initialize metrics
        with self._lock:
            self.engines[name] = engine
            self.pool_metrics[name] = PoolMetrics()
        
        logger.info(f"Connection pool '{name}' created with settings: {pool_settings}")
    
    def _setup_pool_events(self, engine: Engine, pool_name: str):
        """Setup event listeners for pool monitoring"""
        
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Handle new connections"""
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.total_connections += 1
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_connections_created'] += 1
            
            logger.debug(f"New connection created in pool '{pool_name}'")
            
            # Set connection-level settings
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET timezone = 'UTC'")
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout"""
            start_time = time.time()
            
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.checked_out += 1
                metrics.active_connections += 1
                metrics.idle_connections = max(0, metrics.idle_connections - 1)
                metrics.last_checkout_time = datetime.utcnow()
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_checkouts'] += 1
            
            # Store checkout time for performance tracking
            connection_proxy._checkout_start = start_time
            
            logger.debug(f"Connection checked out from pool '{pool_name}'")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin"""
            start_time = time.time()
            
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.checked_in += 1
                metrics.active_connections = max(0, metrics.active_connections - 1)
                metrics.idle_connections += 1
                metrics.last_checkin_time = datetime.utcnow()
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_checkins'] += 1
            
            # Calculate checkout duration if available
            if hasattr(connection_record, '_checkout_start'):
                checkout_duration = time.time() - connection_record._checkout_start
                self._update_average_checkout_time(checkout_duration)
            
            logger.debug(f"Connection checked in to pool '{pool_name}'")
        
        @event.listens_for(engine, "disconnect")
        def receive_disconnect(dbapi_connection, connection_record):
            """Handle connection disconnection"""
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.connection_errors += 1
                metrics.total_connections = max(0, metrics.total_connections - 1)
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_connections_closed'] += 1
                self.performance_metrics['total_errors'] += 1
            
            logger.warning(f"Connection disconnected from pool '{pool_name}'")
    
    def _update_average_checkout_time(self, duration: float):
        """Update average checkout time"""
        total_checkouts = self.performance_metrics['total_checkouts']
        current_avg = self.performance_metrics['average_checkout_time']
        
        # Calculate new average
        new_avg = ((current_avg * (total_checkouts - 1)) + duration) / total_checkouts
        self.performance_metrics['average_checkout_time'] = new_avg
    
    def get_pool(self, name: str = 'main') -> Optional[Engine]:
        """Get a connection pool by name"""
        return self.engines.get(name)
    
    def get_pool_metrics(self, name: str = None) -> Dict[str, PoolMetrics]:
        """Get pool metrics"""
        with self._lock:
            if name:
                return {name: self.pool_metrics.get(name)}
            return self.pool_metrics.copy()
    
    def get_pool_health(self, name: str = None) -> Dict[str, Any]:
        """Get pool health status"""
        pools_to_check = [name] if name else self.engines.keys()
        health_status = {}
        
        for pool_name in pools_to_check:
            if pool_name not in self.engines:
                continue
            
            engine = self.engines[pool_name]
            metrics = self.pool_metrics.get(pool_name, PoolMetrics())
            
            try:
                # Test connectivity
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                
                # Get pool status
                pool = engine.pool
                pool_status = {
                    'pool_size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }
                
                # Determine health status
                is_healthy = (
                    test_value == 1 and
                    pool_status['invalid'] == 0 and
                    metrics.connection_errors < 10  # Threshold for errors
                )
                
                health_status[pool_name] = {
                    'status': 'healthy' if is_healthy else 'degraded',
                    'connectivity_test': test_value == 1,
                    'pool_status': pool_status,
                    'metrics': {
                        'total_connections': metrics.total_connections,
                        'active_connections': metrics.active_connections,
                        'idle_connections': metrics.idle_connections,
                        'connection_errors': metrics.connection_errors,
                        'last_checkout': metrics.last_checkout_time.isoformat() if metrics.last_checkout_time else None,
                        'last_checkin': metrics.last_checkin_time.isoformat() if metrics.last_checkin_time else None
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                health_status[pool_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
        
        return health_status
    
    def optimize_pools(self):
        """Optimize pool settings based on usage patterns"""
        logger.info("Starting pool optimization...")
        
        for pool_name, metrics in self.pool_metrics.items():
            if not metrics.last_checkout_time:
                continue
            
            # Calculate usage patterns
            time_since_checkout = datetime.utcnow() - metrics.last_checkout_time
            error_rate = metrics.connection_errors / max(metrics.total_connections, 1)
            
            # Adjust pool size based on usage
            current_pool = self.engines[pool_name].pool
            current_size = current_pool.size()
            
            if error_rate > 0.1:  # High error rate
                # Increase pool size
                new_size = min(current_size + 5, 50)
                logger.info(f"Pool '{pool_name}' error rate high ({error_rate:.2%}), increasing size to {new_size}")
                
            elif time_since_checkout > timedelta(minutes=30) and metrics.active_connections == 0:
                # Low usage, decrease pool size
                new_size = max(current_size - 2, 5)
                logger.info(f"Pool '{pool_name}' low usage, decreasing size to {new_size}")
            
            # Reset error counters
            metrics.connection_errors = 0
    
    def start_monitoring(self):
        """Start pool monitoring"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_pools, daemon=True)
        self._monitor_thread.start()
        logger.info("Pool monitoring started")
    
    def stop_monitoring(self):
        """Stop pool monitoring"""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Pool monitoring stopped")
    
    def _monitor_pools(self):
        """Monitor pools in background thread"""
        while not self._stop_monitoring.wait(self.health_check_interval):
            try:
                # Perform health checks
                health_status = self.get_pool_health()
                
                # Log health status
                for pool_name, status in health_status.items():
                    if status['status'] != 'healthy':
                        logger.warning(f"Pool '{pool_name}' health check failed: {status}")
                
                # Optimize pools periodically
                if datetime.utcnow().minute % 15 == 0:  # Every 15 minutes
                    self.optimize_pools()
                
            except Exception as e:
                logger.error(f"Error in pool monitoring: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            for metrics in self.pool_metrics.values():
                metrics.connection_errors = 0
                metrics.checkout_errors = 0
                metrics.checkin_errors = 0
            
            self.performance_metrics = {
                'total_connections_created': 0,
                'total_connections_closed': 0,
                'total_checkouts': 0,
                'total_checkins': 0,
                'total_errors': 0,
                'average_checkout_time': 0.0,
                'average_checkin_time': 0.0
            }
        
        logger.info("Pool metrics reset")
    
    def close_all_pools(self):
        """Close all connection pools"""
        for name, engine in self.engines.items():
            try:
                engine.dispose()
                logger.info(f"Pool '{name}' closed")
            except Exception as e:
                logger.error(f"Error closing pool '{name}': {e}")
        
        self.engines.clear()
        self.pool_metrics.clear()


# Global pool manager instance
pool_manager = ConnectionPoolManager()


def get_pool_manager() -> ConnectionPoolManager:
    """Get the global pool manager"""
    return pool_manager


def init_pool_manager(database_url: str = None):
    """Initialize the global pool manager"""
    global pool_manager
    if database_url:
        pool_manager = ConnectionPoolManager(database_url)
    else:
        pool_manager = ConnectionPoolManager()


# Context manager for pool operations
@contextmanager
def pool_context(pool_name: str = 'main'):
    """Context manager for pool operations"""
    manager = get_pool_manager()
    pool = manager.get_pool(pool_name)
    
    if not pool:
        raise ValueError(f"Pool '{pool_name}' not found")
    
    try:
        yield pool
    except Exception as e:
        logger.error(f"Error in pool context '{pool_name}': {e}")
        raise


# Pool health check utilities
class PoolHealthChecker:
    """Utilities for checking pool health"""
    
    @staticmethod
    def check_all_pools() -> Dict[str, Any]:
        """Check health of all pools"""
        manager = get_pool_manager()
        return manager.get_pool_health()
    
    @staticmethod
    def check_pool_health(pool_name: str) -> Dict[str, Any]:
        """Check health of specific pool"""
        manager = get_pool_manager()
        health_status = manager.get_pool_health(pool_name)
        return health_status.get(pool_name, {})
    
    @staticmethod
    def get_pool_metrics(pool_name: str = None) -> Dict[str, PoolMetrics]:
        """Get metrics for pools"""
        manager = get_pool_manager()
        return manager.get_pool_metrics(pool_name)
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """Get performance metrics"""
        manager = get_pool_manager()
        return manager.get_performance_metrics()


# Pool optimization utilities
class PoolOptimizer:
    """Utilities for pool optimization"""
    
    @staticmethod
    def optimize_all_pools():
        """Optimize all pools"""
        manager = get_pool_manager()
        manager.optimize_pools()
    
    @staticmethod
    def reset_metrics():
        """Reset all metrics"""
        manager = get_pool_manager()
        manager.reset_metrics()
    
    @staticmethod
    def start_monitoring():
        """Start pool monitoring"""
        manager = get_pool_manager()
        manager.start_monitoring()
    
    @staticmethod
    def stop_monitoring():
        """Stop pool monitoring"""
        manager = get_pool_manager()
        manager.stop_monitoring()


# Export main functions and classes
__all__ = [
    'ConnectionPoolManager',
    'PoolMetrics',
    'PoolHealthChecker',
    'PoolOptimizer',
    'pool_manager',
    'get_pool_manager',
    'init_pool_manager',
    'pool_context'
] 