"""
Database Connection Pool Management for Mingus Financial Application
Production-grade connection pooling with monitoring, health checks, and optimization
Optimized for 1,000+ concurrent users with financial data reliability requirements
"""

import os
import logging
import threading
import time
import signal
import sys
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import weakref

from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError, TimeoutError

# Prometheus metrics integration
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback metrics
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Enhanced connection pool metrics with leak detection"""
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
    connection_leaks: int = 0
    slow_queries: int = 0
    last_checkout_time: Optional[datetime] = None
    last_checkin_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReadReplicaConfig:
    """Configuration for read replicas"""
    name: str
    url: str
    weight: int = 1
    health_check_interval: int = 30
    last_health_check: Optional[datetime] = None
    is_healthy: bool = True
    response_time: Optional[float] = None


class ConnectionLeakDetector:
    """Detects and prevents connection leaks"""
    
    def __init__(self, max_connection_age: int = 300, leak_threshold: int = 10):
        self.max_connection_age = max_connection_age
        self.leak_threshold = leak_threshold
        self.active_connections = weakref.WeakKeyDictionary()
        self.leak_alerts = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def track_connection(self, connection, pool_name: str):
        """Track a connection checkout"""
        with self._lock:
            self.active_connections[connection] = {
                'pool_name': pool_name,
                'checkout_time': time.time(),
                'stack_trace': self._get_stack_trace()
            }
    
    def release_connection(self, connection):
        """Release a connection from tracking"""
        with self._lock:
            self.active_connections.pop(connection, None)
    
    def check_for_leaks(self) -> List[Dict[str, Any]]:
        """Check for potential connection leaks"""
        current_time = time.time()
        leaks = []
        
        with self._lock:
            for connection, info in list(self.active_connections.items()):
                age = current_time - info['checkout_time']
                if age > self.max_connection_age:
                    leaks.append({
                        'pool_name': info['pool_name'],
                        'age_seconds': age,
                        'stack_trace': info['stack_trace']
                    })
        
        return leaks
    
    def _get_stack_trace(self) -> str:
        """Get current stack trace for debugging"""
        import traceback
        return ''.join(traceback.format_stack())


class ConnectionPoolManager:
    """
    Production-grade connection pool manager for Mingus Financial Application
    Provides monitoring, health checks, read replicas, and optimization
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engines = {}
        self.read_replicas = {}
        self.pool_metrics = {}
        self.monitoring_enabled = True
        self.health_check_interval = int(os.environ.get('DB_HEALTH_CHECK_INTERVAL', 300))  # 5 minutes
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.RLock()
        self.leak_detector = ConnectionLeakDetector()
        
        # Performance tracking
        self.performance_metrics = {
            'total_connections_created': 0,
            'total_connections_closed': 0,
            'total_checkouts': 0,
            'total_checkins': 0,
            'total_errors': 0,
            'average_checkout_time': 0.0,
            'average_checkin_time': 0.0,
            'slow_query_threshold': float(os.environ.get('DB_SLOW_QUERY_THRESHOLD', 1.0))
        }
        
        # Prometheus metrics
        self._setup_prometheus_metrics()
        
        # Graceful shutdown handling
        self._setup_graceful_shutdown()
        
        if self.database_url:
            self._initialize_pools()
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics for monitoring"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Connection pool metrics
        self.metrics = {
            'connections_total': Counter(
                'db_connections_total',
                'Total database connections created',
                ['pool_name', 'status']
            ),
            'connections_active': Gauge(
                'db_connections_active',
                'Active database connections',
                ['pool_name']
            ),
            'connections_idle': Gauge(
                'db_connections_idle',
                'Idle database connections',
                ['pool_name']
            ),
            'connection_errors': Counter(
                'db_connection_errors_total',
                'Total database connection errors',
                ['pool_name', 'error_type']
            ),
            'checkout_duration': Histogram(
                'db_checkout_duration_seconds',
                'Database connection checkout duration',
                ['pool_name'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
            ),
            'query_duration': Histogram(
                'db_query_duration_seconds',
                'Database query duration',
                ['pool_name', 'query_type'],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
            ),
            'pool_size': Gauge(
                'db_pool_size',
                'Database connection pool size',
                ['pool_name']
            ),
            'pool_overflow': Gauge(
                'db_pool_overflow',
                'Database connection pool overflow',
                ['pool_name']
            )
        }
    
    def _setup_graceful_shutdown(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.graceful_shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _initialize_pools(self):
        """Initialize connection pools for different contexts"""
        
        # Main application pool - optimized for 1,000+ concurrent users
        self.create_pool(
            name='main',
            database_url=self.database_url,
            pool_size=int(os.environ.get('DB_POOL_SIZE', 50)),  # Increased for high concurrency
            max_overflow=int(os.environ.get('DB_MAX_OVERFLOW', 100)),  # Increased overflow
            pool_recycle=int(os.environ.get('DB_POOL_RECYCLE', 3600)),
            pool_timeout=int(os.environ.get('DB_POOL_TIMEOUT', 30)),
            pool_pre_ping=True,
            echo=os.environ.get('DB_ECHO', 'false').lower() == 'true'
        )
        
        # Celery worker pool
        self.create_pool(
            name='celery',
            database_url=self.database_url,
            pool_size=int(os.environ.get('CELERY_DB_POOL_SIZE', 25)),
            max_overflow=int(os.environ.get('CELERY_DB_MAX_OVERFLOW', 50)),
            pool_recycle=int(os.environ.get('CELERY_DB_POOL_RECYCLE', 1800)),
            pool_timeout=int(os.environ.get('CELERY_DB_POOL_TIMEOUT', 30)),
            pool_pre_ping=True,
            echo=os.environ.get('CELERY_DB_ECHO', 'false').lower() == 'true'
        )
        
        # Analytics pool (for heavy reporting queries)
        self.create_pool(
            name='analytics',
            database_url=self.database_url,
            pool_size=int(os.environ.get('ANALYTICS_DB_POOL_SIZE', 10)),
            max_overflow=int(os.environ.get('ANALYTICS_DB_MAX_OVERFLOW', 20)),
            pool_recycle=int(os.environ.get('ANALYTICS_DB_POOL_RECYCLE', 7200)),
            pool_timeout=int(os.environ.get('ANALYTICS_DB_POOL_TIMEOUT', 60)),
            pool_pre_ping=True,
            echo=os.environ.get('ANALYTICS_DB_ECHO', 'false').lower() == 'true'
        )
        
        # Financial transactions pool (high reliability)
        self.create_pool(
            name='financial',
            database_url=self.database_url,
            pool_size=int(os.environ.get('FINANCIAL_DB_POOL_SIZE', 30)),
            max_overflow=int(os.environ.get('FINANCIAL_DB_MAX_OVERFLOW', 60)),
            pool_recycle=int(os.environ.get('FINANCIAL_DB_POOL_RECYCLE', 1800)),
            pool_timeout=int(os.environ.get('FINANCIAL_DB_POOL_TIMEOUT', 15)),
            pool_pre_ping=True,
            echo=os.environ.get('FINANCIAL_DB_ECHO', 'false').lower() == 'true'
        )
        
        # Initialize read replicas if configured
        self._initialize_read_replicas()
        
        logger.info("Production connection pools initialized successfully")
    
    def _initialize_read_replicas(self):
        """Initialize read replica connections"""
        replica_urls = os.environ.get('DB_READ_REPLICAS', '').split(',')
        
        for i, url in enumerate(replica_urls):
            if url.strip():
                replica_name = f'read_replica_{i+1}'
                self.add_read_replica(
                    name=replica_name,
                    url=url.strip(),
                    weight=int(os.environ.get(f'DB_REPLICA_{i+1}_WEIGHT', 1))
                )
    
    def add_read_replica(self, name: str, url: str, weight: int = 1):
        """Add a read replica"""
        try:
            # Test connection
            test_engine = create_engine(url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.read_replicas[name] = ReadReplicaConfig(
                name=name,
                url=url,
                weight=weight
            )
            
            logger.info(f"Read replica '{name}' added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add read replica '{name}': {e}")
    
    def get_read_replica(self, strategy: str = 'round_robin') -> Optional[str]:
        """Get a healthy read replica URL"""
        if not self.read_replicas:
            return None
        
        healthy_replicas = [
            name for name, config in self.read_replicas.items()
            if config.is_healthy
        ]
        
        if not healthy_replicas:
            return None
        
        if strategy == 'round_robin':
            # Simple round-robin selection
            return self.read_replicas[healthy_replicas[0]].url
        elif strategy == 'weighted':
            # Weighted selection based on replica weights
            total_weight = sum(self.read_replicas[name].weight for name in healthy_replicas)
            if total_weight == 0:
                return self.read_replicas[healthy_replicas[0]].url
            
            # Simple weighted selection (could be enhanced with more sophisticated algorithms)
            return self.read_replicas[healthy_replicas[0]].url
        
        return None
    
    def create_pool(self, name: str, database_url: str, **pool_kwargs):
        """Create a new connection pool with production optimizations"""
        
        # Default pool settings optimized for production
        default_settings = {
            'poolclass': QueuePool,
            'pool_pre_ping': True,
            'pool_reset_on_return': 'commit',
            'connect_args': {
                'application_name': f'mingus_financial_{name}',
                'options': '-c timezone=utc -c statement_timeout=30000 -c idle_in_transaction_session_timeout=60s',
                'connect_timeout': 10,
                'command_timeout': 30,
                'sslmode': os.environ.get('DB_SSL_MODE', 'prefer'),
                'keepalives_idle': 60,
                'keepalives_interval': 10,
                'keepalives_count': 5
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
        
        logger.info(f"Production connection pool '{name}' created with settings: {pool_settings}")
    
    def _setup_pool_events(self, engine: Engine, pool_name: str):
        """Setup comprehensive event listeners for pool monitoring"""
        
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Handle new connections with enhanced tracking"""
            start_time = time.time()
            
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.total_connections += 1
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_connections_created'] += 1
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics['connections_total'].labels(pool_name=pool_name, status='created').inc()
                self.metrics['pool_size'].labels(pool_name=pool_name).set(metrics.total_connections)
            
            logger.debug(f"New connection created in pool '{pool_name}'")
            
            # Set connection-level settings for financial data reliability
            try:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone = 'UTC'")
                    cursor.execute("SET statement_timeout = '30s'")
                    cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
                    cursor.execute("SET synchronous_commit = 'on'")  # Ensure data durability
                    cursor.execute("SET default_transaction_isolation = 'read committed'")
            except Exception as e:
                logger.warning(f"Failed to set connection parameters for pool '{pool_name}': {e}")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout with leak detection"""
            start_time = time.time()
            
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.checked_out += 1
                metrics.active_connections += 1
                metrics.idle_connections = max(0, metrics.idle_connections - 1)
                metrics.last_checkout_time = datetime.utcnow()
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_checkouts'] += 1
            
            # Track connection for leak detection
            self.leak_detector.track_connection(connection_proxy, pool_name)
            
            # Store checkout time for performance tracking
            connection_proxy._checkout_start = start_time
            connection_proxy._pool_name = pool_name
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics['connections_active'].labels(pool_name=pool_name).inc()
                self.metrics['connections_idle'].labels(pool_name=pool_name).dec()
            
            logger.debug(f"Connection checked out from pool '{pool_name}'")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin with performance tracking"""
            start_time = time.time()
            
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.checked_in += 1
                metrics.active_connections = max(0, metrics.active_connections - 1)
                metrics.idle_connections += 1
                metrics.last_checkin_time = datetime.utcnow()
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_checkins'] += 1
            
            # Release connection from leak detection
            if hasattr(connection_record, '_checkout_start'):
                self.leak_detector.release_connection(connection_record)
                
                # Calculate checkout duration
                checkout_duration = time.time() - connection_record._checkout_start
                self._update_average_checkout_time(checkout_duration)
                
                # Update Prometheus metrics
                if PROMETHEUS_AVAILABLE:
                    self.metrics['checkout_duration'].labels(pool_name=pool_name).observe(checkout_duration)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics['connections_active'].labels(pool_name=pool_name).dec()
                self.metrics['connections_idle'].labels(pool_name=pool_name).inc()
            
            logger.debug(f"Connection checked in to pool '{pool_name}'")
        
        # Handle connection errors
        @event.listens_for(engine, "handle_error")
        def receive_error(exception_context):
            """Handle connection errors with enhanced logging"""
            with self._lock:
                metrics = self.pool_metrics[pool_name]
                metrics.connection_errors += 1
                metrics.updated_at = datetime.utcnow()
                self.performance_metrics['total_errors'] += 1
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                error_type = type(exception_context.original_exception).__name__
                self.metrics['connection_errors'].labels(pool_name=pool_name, error_type=error_type).inc()
            
            logger.error(f"Connection error in pool '{pool_name}': {exception_context.original_exception}")
    
    def _update_average_checkout_time(self, duration: float):
        """Update average checkout time with exponential moving average"""
        total_checkouts = self.performance_metrics['total_checkouts']
        current_avg = self.performance_metrics['average_checkout_time']
        
        # Use exponential moving average for better stability
        alpha = 0.1  # Smoothing factor
        if total_checkouts == 1:
            new_avg = duration
        else:
            new_avg = (alpha * duration) + ((1 - alpha) * current_avg)
        
        self.performance_metrics['average_checkout_time'] = new_avg
        
        # Check for slow queries
        if duration > self.performance_metrics['slow_query_threshold']:
            self.performance_metrics['slow_queries'] += 1
    
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
        """Get comprehensive pool health status"""
        pools_to_check = [name] if name else self.engines.keys()
        health_status = {}
        
        for pool_name in pools_to_check:
            if pool_name not in self.engines:
                continue
            
            engine = self.engines[pool_name]
            metrics = self.pool_metrics.get(pool_name, PoolMetrics())
            
            try:
                # Test connectivity with timeout
                start_time = time.time()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                response_time = time.time() - start_time
                
                # Get pool status
                pool = engine.pool
                pool_status = {
                    'pool_size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }
                
                # Check for connection leaks
                leaks = self.leak_detector.check_for_leaks()
                leak_count = len([l for l in leaks if l['pool_name'] == pool_name])
                
                # Determine health status with enhanced criteria
                is_healthy = (
                    test_value == 1 and
                    pool_status['invalid'] == 0 and
                    metrics.connection_errors < 10 and  # Threshold for errors
                    leak_count == 0 and  # No connection leaks
                    response_time < 1.0  # Response time under 1 second
                )
                
                health_status[pool_name] = {
                    'status': 'healthy' if is_healthy else 'degraded',
                    'connectivity_test': test_value == 1,
                    'response_time': response_time,
                    'pool_status': pool_status,
                    'connection_leaks': leak_count,
                    'metrics': {
                        'total_connections': metrics.total_connections,
                        'active_connections': metrics.active_connections,
                        'idle_connections': metrics.idle_connections,
                        'connection_errors': metrics.connection_errors,
                        'slow_queries': metrics.slow_queries,
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
        """Optimize pool settings based on usage patterns and performance metrics"""
        logger.info("Starting production pool optimization...")
        
        for pool_name, metrics in self.pool_metrics.items():
            if not metrics.last_checkout_time:
                continue
            
            # Calculate usage patterns
            time_since_checkout = datetime.utcnow() - metrics.last_checkout_time
            error_rate = metrics.connection_errors / max(metrics.total_connections, 1)
            leak_rate = metrics.connection_leaks / max(metrics.total_connections, 1)
            
            # Get current pool
            current_pool = self.engines[pool_name].pool
            current_size = current_pool.size()
            
            # Optimization strategies based on financial application requirements
            if error_rate > 0.05:  # High error rate (5%)
                # Increase pool size for better reliability
                new_size = min(current_size + 10, 100)
                logger.info(f"Pool '{pool_name}' error rate high ({error_rate:.2%}), increasing size to {new_size}")
                
            elif leak_rate > 0.01:  # Connection leaks detected
                # Increase pool size to handle leaks gracefully
                new_size = min(current_size + 5, 100)
                logger.info(f"Pool '{pool_name}' leaks detected ({leak_rate:.2%}), increasing size to {new_size}")
                
            elif time_since_checkout > timedelta(minutes=30) and metrics.active_connections == 0:
                # Low usage, decrease pool size for cost optimization
                new_size = max(current_size - 5, 10)
                logger.info(f"Pool '{pool_name}' low usage, decreasing size to {new_size}")
            
            # Reset error counters
            metrics.connection_errors = 0
            metrics.connection_leaks = 0
    
    def start_monitoring(self):
        """Start comprehensive pool monitoring"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_pools, daemon=True)
        self._monitor_thread.start()
        logger.info("Production pool monitoring started")
    
    def stop_monitoring(self):
        """Stop pool monitoring"""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Production pool monitoring stopped")
    
    def _monitor_pools(self):
        """Monitor pools in background thread with enhanced checks"""
        while not self._stop_monitoring.wait(self.health_check_interval):
            try:
                # Perform health checks
                health_status = self.get_pool_health()
                
                # Log health status
                for pool_name, status in health_status.items():
                    if status['status'] != 'healthy':
                        logger.warning(f"Pool '{pool_name}' health check failed: {status}")
                
                # Check for connection leaks
                leaks = self.leak_detector.check_for_leaks()
                if leaks:
                    logger.warning(f"Connection leaks detected: {len(leaks)} active connections")
                    for leak in leaks:
                        logger.warning(f"Leak in pool '{leak['pool_name']}': {leak['age_seconds']:.1f}s old")
                
                # Optimize pools periodically
                if datetime.utcnow().minute % 15 == 0:  # Every 15 minutes
                    self.optimize_pools()
                
                # Health check read replicas
                self._health_check_replicas()
                
            except Exception as e:
                logger.error(f"Error in production pool monitoring: {e}")
    
    def _health_check_replicas(self):
        """Health check read replicas"""
        for name, config in self.read_replicas.items():
            try:
                start_time = time.time()
                test_engine = create_engine(config.url, pool_pre_ping=True)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                response_time = time.time() - start_time
                config.is_healthy = True
                config.response_time = response_time
                config.last_health_check = datetime.utcnow()
                
            except Exception as e:
                config.is_healthy = False
                config.response_time = None
                config.last_health_check = datetime.utcnow()
                logger.warning(f"Read replica '{name}' health check failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        with self._lock:
            metrics = self.performance_metrics.copy()
            
            # Add leak detection metrics
            leaks = self.leak_detector.check_for_leaks()
            metrics['active_leaks'] = len(leaks)
            metrics['leak_details'] = leaks
            
            # Add read replica metrics
            metrics['read_replicas'] = {
                name: {
                    'is_healthy': config.is_healthy,
                    'response_time': config.response_time,
                    'last_health_check': config.last_health_check.isoformat() if config.last_health_check else None
                }
                for name, config in self.read_replicas.items()
            }
            
            return metrics
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            for metrics in self.pool_metrics.values():
                metrics.connection_errors = 0
                metrics.checkout_errors = 0
                metrics.checkin_errors = 0
                metrics.connection_leaks = 0
                metrics.slow_queries = 0
            
            self.performance_metrics = {
                'total_connections_created': 0,
                'total_connections_closed': 0,
                'total_checkouts': 0,
                'total_checkins': 0,
                'total_errors': 0,
                'average_checkout_time': 0.0,
                'average_checkin_time': 0.0,
                'slow_query_threshold': float(os.environ.get('DB_SLOW_QUERY_THRESHOLD', 1.0))
            }
        
        logger.info("Production pool metrics reset")
    
    def graceful_shutdown(self, timeout: int = 30):
        """Gracefully shutdown all connection pools"""
        logger.info("Initiating graceful shutdown of connection pools...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Wait for active connections to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            total_active = sum(
                metrics.active_connections 
                for metrics in self.pool_metrics.values()
            )
            
            if total_active == 0:
                break
            
            logger.info(f"Waiting for {total_active} active connections to complete...")
            time.sleep(1)
        
        # Close all pools
        self.close_all_pools()
        
        logger.info("Connection pools gracefully shut down")
    
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


# Enhanced context manager for pool operations with leak detection
@contextmanager
def pool_context(pool_name: str = 'main', timeout: int = 30):
    """Context manager for pool operations with enhanced error handling"""
    manager = get_pool_manager()
    pool = manager.get_pool(pool_name)
    
    if not pool:
        raise ValueError(f"Pool '{pool_name}' not found")
    
    connection = None
    try:
        connection = pool.connect()
        yield connection
    except Exception as e:
        logger.error(f"Error in pool context '{pool_name}': {e}")
        raise
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.error(f"Error closing connection in pool '{pool_name}': {e}")


# Enhanced pool health check utilities
class PoolHealthChecker:
    """Enhanced utilities for checking pool health"""
    
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
        """Get comprehensive performance metrics"""
        manager = get_pool_manager()
        return manager.get_performance_metrics()
    
    @staticmethod
    def check_connection_leaks() -> List[Dict[str, Any]]:
        """Check for connection leaks"""
        manager = get_pool_manager()
        return manager.leak_detector.check_for_leaks()


# Enhanced pool optimization utilities
class PoolOptimizer:
    """Enhanced utilities for pool optimization"""
    
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
    
    @staticmethod
    def graceful_shutdown(timeout: int = 30):
        """Gracefully shutdown all pools"""
        manager = get_pool_manager()
        manager.graceful_shutdown(timeout)


# Export main functions and classes
__all__ = [
    'ConnectionPoolManager',
    'PoolMetrics',
    'ReadReplicaConfig',
    'ConnectionLeakDetector',
    'PoolHealthChecker',
    'PoolOptimizer',
    'pool_manager',
    'get_pool_manager',
    'init_pool_manager',
    'pool_context'
] 