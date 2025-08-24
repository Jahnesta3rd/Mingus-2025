"""
Database Configuration for MINGUS Production Deployment
Optimized for PostgreSQL with proper connection pooling and performance tuning
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# =====================================================
# DATABASE CONNECTION CONFIGURATION
# =====================================================

class DatabaseConfig:
    """Database configuration for MINGUS production deployment"""
    
    def __init__(self):
        # Database connection settings
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')
        self.database_pool_size = int(os.getenv('DB_POOL_SIZE', 20))
        self.database_max_overflow = int(os.getenv('DB_MAX_OVERFLOW', 30))
        self.database_pool_recycle = int(os.getenv('DB_POOL_RECYCLE', 3600))  # 1 hour
        self.database_pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', 30))
        self.database_pool_pre_ping = True
        
        # Performance settings
        self.database_echo = os.getenv('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
        self.database_echo_pool = False
        self.database_statement_timeout = int(os.getenv('DB_STATEMENT_TIMEOUT', 30000))  # 30 seconds
        self.database_idle_in_transaction_timeout = int(os.getenv('DB_IDLE_TIMEOUT', 60000))  # 60 seconds
        
        # SSL settings
        self.database_ssl_mode = os.getenv('DB_SSL_MODE', 'require')
        self.database_ssl_cert = os.getenv('DB_SSL_CERT')
        self.database_ssl_key = os.getenv('DB_SSL_KEY')
        self.database_ssl_ca = os.getenv('DB_SSL_CA')
        self.database_ssl_crl = os.getenv('DB_SSL_CRL')
        
        # Monitoring settings
        self.database_enable_monitoring = os.getenv('DB_ENABLE_MONITORING', 'true').lower() == 'true'
        self.database_slow_query_threshold = int(os.getenv('DB_SLOW_QUERY_THRESHOLD', 1000))  # 1 second
        
        # Connection retry settings
        self.database_connect_retries = int(os.getenv('DB_CONNECT_RETRIES', 3))
        self.database_connect_retry_delay = int(os.getenv('DB_CONNECT_RETRY_DELAY', 5))  # 5 seconds
        
        # Initialize engine and session factory
        self.engine = None
        self.session_factory = None
        self.Session = None
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        try:
            # Create engine with optimized settings
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.database_pool_size,
                max_overflow=self.database_max_overflow,
                pool_recycle=self.database_pool_recycle,
                pool_timeout=self.database_pool_timeout,
                pool_pre_ping=self.database_pool_pre_ping,
                echo=self.database_echo,
                echo_pool=self.database_echo_pool,
                connect_args=self._get_connect_args(),
                isolation_level='READ_COMMITTED'
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            # Create scoped session
            self.Session = scoped_session(self.session_factory)
            
            # Setup monitoring if enabled
            if self.database_enable_monitoring:
                self._setup_monitoring()
            
            logger.info("Database configuration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database configuration: {e}")
            raise
    
    def _get_connect_args(self):
        """Get database connection arguments"""
        connect_args = {
            'application_name': 'mingus_production',
            'options': f'-c timezone=utc -c statement_timeout={self.database_statement_timeout} -c idle_in_transaction_session_timeout={self.database_idle_in_transaction_timeout}',
        }
        
        # Add SSL settings if configured
        if self.database_ssl_mode != 'disable':
            connect_args['sslmode'] = self.database_ssl_mode
            
            if self.database_ssl_cert:
                connect_args['sslcert'] = self.database_ssl_cert
            if self.database_ssl_key:
                connect_args['sslkey'] = self.database_ssl_key
            if self.database_ssl_ca:
                connect_args['sslca'] = self.database_ssl_ca
            if self.database_ssl_crl:
                connect_args['sslcrl'] = self.database_ssl_crl
        
        return connect_args
    
    def _setup_monitoring(self):
        """Setup database monitoring and performance tracking"""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query execution time"""
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries and track performance"""
            total = time.time() - conn.info['query_start_time'].pop(-1)
            
            if total > (self.database_slow_query_threshold / 1000.0):
                logger.warning(f"Slow query detected ({total:.3f}s): {statement[:200]}...")
            
            # Track query metrics
            if hasattr(conn.info, 'query_count'):
                conn.info.query_count += 1
                conn.info.total_query_time += total
            else:
                conn.info.query_count = 1
                conn.info.total_query_time = total
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkout"""
            logger.debug("Database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Track connection checkin"""
            logger.debug("Database connection checked in")
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_connection_pool_stats(self):
        """Get connection pool statistics"""
        if not self.engine:
            return None
        
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
    
    def health_check(self):
        """Perform database health check"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# =====================================================
# CONNECTION POOL OPTIMIZATION
# =====================================================

class ConnectionPoolOptimizer:
    """Connection pool optimization for production workloads"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.optimization_interval = int(os.getenv('DB_OPTIMIZATION_INTERVAL', 300))  # 5 minutes
        self.last_optimization = 0
    
    def optimize_pool(self):
        """Optimize connection pool based on current usage"""
        import time
        
        current_time = time.time()
        if current_time - self.last_optimization < self.optimization_interval:
            return
        
        stats = self.config.get_connection_pool_stats()
        if not stats:
            return
        
        # Adjust pool size based on usage
        pool_usage = stats['checked_out'] / stats['pool_size']
        
        if pool_usage > 0.8:  # High usage
            # Consider increasing pool size
            logger.info(f"High pool usage detected: {pool_usage:.2%}")
        elif pool_usage < 0.2:  # Low usage
            # Consider decreasing pool size
            logger.info(f"Low pool usage detected: {pool_usage:.2%}")
        
        self.last_optimization = current_time

# =====================================================
# DATABASE MAINTENANCE
# =====================================================

class DatabaseMaintenance:
    """Database maintenance tasks for production"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    def run_vacuum(self):
        """Run VACUUM to reclaim storage and update statistics"""
        try:
            with self.config.get_session() as session:
                session.execute("VACUUM ANALYZE")
                logger.info("Database VACUUM completed successfully")
        except Exception as e:
            logger.error(f"Database VACUUM failed: {e}")
    
    def update_statistics(self):
        """Update database statistics for query optimization"""
        try:
            with self.config.get_session() as session:
                session.execute("ANALYZE")
                logger.info("Database statistics updated successfully")
        except Exception as e:
            logger.error(f"Database statistics update failed: {e}")
    
    def check_table_sizes(self):
        """Check table sizes and growth"""
        try:
            with self.config.get_session() as session:
                result = session.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """)
                
                logger.info("Top 10 largest tables:")
                for row in result:
                    logger.info(f"  {row.schemaname}.{row.tablename}: {row.size}")
                    
        except Exception as e:
            logger.error(f"Table size check failed: {e}")

# =====================================================
# PERFORMANCE MONITORING
# =====================================================

class DatabasePerformanceMonitor:
    """Database performance monitoring for production"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.metrics = {}
    
    def collect_metrics(self):
        """Collect database performance metrics"""
        try:
            with self.config.get_session() as session:
                # Connection pool stats
                pool_stats = self.config.get_connection_pool_stats()
                
                # Active connections
                result = session.execute("SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'")
                active_connections = result.scalar()
                
                # Slow queries
                result = session.execute("""
                    SELECT count(*) as slow_queries 
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND now() - query_start > interval '1 second'
                """)
                slow_queries = result.scalar()
                
                # Cache hit ratio
                result = session.execute("""
                    SELECT 
                        round(100.0 * sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)), 2) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                cache_hit_ratio = result.scalar()
                
                self.metrics = {
                    'pool_stats': pool_stats,
                    'active_connections': active_connections,
                    'slow_queries': slow_queries,
                    'cache_hit_ratio': cache_hit_ratio,
                    'timestamp': time.time()
                }
                
                logger.info(f"Database metrics collected: {self.metrics}")
                
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
    
    def get_metrics(self):
        """Get collected metrics"""
        return self.metrics

# =====================================================
# GLOBAL INSTANCE
# =====================================================

# Create global database configuration instance
db_config = DatabaseConfig()
db_optimizer = ConnectionPoolOptimizer(db_config)
db_maintenance = DatabaseMaintenance(db_config)
db_monitor = DatabasePerformanceMonitor(db_config)

# =====================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =====================================================

def get_production_config():
    """Get production-specific database configuration"""
    return {
        'pool_size': 50,
        'max_overflow': 100,
        'pool_recycle': 1800,  # 30 minutes
        'statement_timeout': 60000,  # 60 seconds
        'idle_timeout': 120000,  # 2 minutes
        'ssl_mode': 'require',
        'enable_monitoring': True,
        'slow_query_threshold': 500,  # 500ms
    }

def get_development_config():
    """Get development-specific database configuration"""
    return {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_recycle': 3600,  # 1 hour
        'statement_timeout': 30000,  # 30 seconds
        'idle_timeout': 60000,  # 1 minute
        'ssl_mode': 'prefer',
        'enable_monitoring': False,
        'slow_query_threshold': 1000,  # 1 second
    }

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')

def get_database_ssl_config():
    """Get database SSL configuration"""
    return {
        'ssl_mode': os.getenv('DB_SSL_MODE', 'require'),
        'ssl_cert': os.getenv('DB_SSL_CERT'),
        'ssl_key': os.getenv('DB_SSL_KEY'),
        'ssl_ca': os.getenv('DB_SSL_CA'),
        'ssl_crl': os.getenv('DB_SSL_CRL'),
    }

def validate_database_connection():
    """Validate database connection"""
    try:
        return db_config.health_check()
    except Exception as e:
        logger.error(f"Database connection validation failed: {e}")
        return False

# Import time module for monitoring
import time 