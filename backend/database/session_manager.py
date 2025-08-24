"""
SQLAlchemy Session Management for Communication System
Comprehensive session handling with connection pooling, transaction management, and error handling
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any, Dict
from datetime import datetime, timedelta
import threading
from functools import wraps

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import (
    SQLAlchemyError, 
    DisconnectionError, 
    TimeoutError, 
    OperationalError,
    IntegrityError,
    DataError,
    ProgrammingError
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL

from flask import current_app, g, has_app_context
from celery import current_task

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Comprehensive SQLAlchemy session manager for communication system
    Handles connection pooling, transaction management, and error handling
    """
    
    def __init__(self, database_url: str = None, app=None):
        """Initialize the session manager"""
        self.database_url = database_url
        self.app = app
        self.engine = None
        self.session_factory = None
        self.scoped_session_factory = None
        self._lock = threading.Lock()
        self._session_stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'failed_sessions': 0,
            'connection_errors': 0,
            'transaction_rollbacks': 0
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the session manager with Flask app"""
        self.app = app
        self.database_url = self.database_url or app.config.get('SQLALCHEMY_DATABASE_URI')
        
        if not self.database_url:
            raise ValueError("Database URL not provided")
        
        self._create_engine()
        self._create_session_factories()
        self._setup_engine_events()
        
        # Register cleanup on app teardown
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self._cleanup_session)
    
    def _create_engine(self):
        """Create SQLAlchemy engine with optimized pooling"""
        # Parse database URL to extract components
        url = URL.create(self.database_url)
        
        # Determine pool class based on environment
        if self.app and self.app.config.get('TESTING'):
            pool_class = StaticPool
            pool_kwargs = {}
        else:
            pool_class = QueuePool
            pool_kwargs = {
                'pool_size': self.app.config.get('DB_POOL_SIZE', 20) if self.app else 20,
                'max_overflow': self.app.config.get('DB_MAX_OVERFLOW', 30) if self.app else 30,
                'pool_recycle': self.app.config.get('DB_POOL_RECYCLE', 3600) if self.app else 3600,
                'pool_pre_ping': True,
                'pool_timeout': self.app.config.get('DB_POOL_TIMEOUT', 30) if self.app else 30,
                'pool_reset_on_return': 'commit',
                'echo': self.app.config.get('DB_ECHO', False) if self.app else False,
                'echo_pool': self.app.config.get('DB_ECHO_POOL', False) if self.app else False
            }
        
        # Create engine with optimized settings
        self.engine = create_engine(
            self.database_url,
            poolclass=pool_class,
            **pool_kwargs,
            connect_args={
                'application_name': 'mingus_communication_system',
                'options': '-c timezone=utc -c statement_timeout=30000',
                'sslmode': self.app.config.get('DB_SSL_MODE', 'prefer') if self.app else 'prefer',
                'connect_timeout': 10,
                'command_timeout': 30
            }
        )
        
        logger.info(f"Database engine created with pool_size={pool_kwargs.get('pool_size', 20)}")
    
    def _create_session_factories(self):
        """Create session factories with proper configuration"""
        # Create session factory with optimized settings
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=Session
        )
        
        # Create scoped session factory for thread safety
        self.scoped_session_factory = scoped_session(
            self.session_factory,
            scopefunc=self._get_scope_func()
        )
        
        logger.info("Session factories created successfully")
    
    def _get_scope_func(self):
        """Get the appropriate scope function based on context"""
        if has_app_context():
            return lambda: id(g)
        elif current_task:
            return lambda: current_task.request.id
        else:
            return lambda: threading.get_ident()
    
    def _setup_engine_events(self):
        """Setup engine event listeners for monitoring and error handling"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Handle new database connections"""
            logger.debug("New database connection established")
            
            # Set connection-level settings
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET timezone = 'UTC'")
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool"""
            logger.debug("Database connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool"""
            logger.debug("Database connection checked in to pool")
        
        @event.listens_for(self.engine, "disconnect")
        def receive_disconnect(dbapi_connection, connection_record):
            """Handle connection disconnection"""
            logger.warning("Database connection disconnected")
            self._session_stats['connection_errors'] += 1
        
        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_connection):
            """Handle connection close"""
            logger.debug("Database connection closed")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        try:
            session = self.session_factory()
            self._session_stats['total_sessions'] += 1
            self._session_stats['active_sessions'] += 1
            
            logger.debug(f"New session created. Active sessions: {self._session_stats['active_sessions']}")
            return session
            
        except Exception as e:
            self._session_stats['failed_sessions'] += 1
            logger.error(f"Failed to create database session: {e}")
            raise
    
    def get_scoped_session(self) -> Session:
        """Get a scoped database session for current context"""
        try:
            session = self.scoped_session_factory()
            self._session_stats['total_sessions'] += 1
            self._session_stats['active_sessions'] += 1
            
            logger.debug(f"New scoped session created. Active sessions: {self._session_stats['active_sessions']}")
            return session
            
        except Exception as e:
            self._session_stats['failed_sessions'] += 1
            logger.error(f"Failed to create scoped database session: {e}")
            raise
    
    @contextmanager
    def session_scope(self, commit_on_success: bool = True, rollback_on_error: bool = True) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic transaction management
        
        Args:
            commit_on_success: Whether to commit on successful completion
            rollback_on_error: Whether to rollback on error
        """
        session = None
        try:
            session = self.get_session()
            logger.debug("Session scope entered")
            
            yield session
            
            if commit_on_success:
                session.commit()
                logger.debug("Session committed successfully")
                
        except Exception as e:
            if session and rollback_on_error:
                session.rollback()
                self._session_stats['transaction_rollbacks'] += 1
                logger.warning(f"Session rolled back due to error: {e}")
            
            # Re-raise the exception
            raise
            
        finally:
            if session:
                session.close()
                self._session_stats['active_sessions'] -= 1
                logger.debug(f"Session closed. Active sessions: {self._session_stats['active_sessions']}")
    
    @contextmanager
    def scoped_session_scope(self, commit_on_success: bool = True, rollback_on_error: bool = True) -> Generator[Session, None, None]:
        """
        Context manager for scoped database sessions
        
        Args:
            commit_on_success: Whether to commit on successful completion
            rollback_on_error: Whether to rollback on error
        """
        session = None
        try:
            session = self.get_scoped_session()
            logger.debug("Scoped session scope entered")
            
            yield session
            
            if commit_on_success:
                session.commit()
                logger.debug("Scoped session committed successfully")
                
        except Exception as e:
            if session and rollback_on_error:
                session.rollback()
                self._session_stats['transaction_rollbacks'] += 1
                logger.warning(f"Scoped session rolled back due to error: {e}")
            
            # Re-raise the exception
            raise
            
        finally:
            if session:
                session.close()
                self._session_stats['active_sessions'] -= 1
                logger.debug(f"Scoped session closed. Active sessions: {self._session_stats['active_sessions']}")
    
    def execute_with_retry(self, operation, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Execute database operation with retry logic
        
        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
                
            except (DisconnectionError, OperationalError, TimeoutError) as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    import time
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Database operation failed after {max_retries + 1} attempts: {e}")
                    raise
                    
            except (IntegrityError, DataError, ProgrammingError) as e:
                # Don't retry on data/constraint errors
                logger.error(f"Database operation failed with data error: {e}")
                raise
                
            except SQLAlchemyError as e:
                last_exception = e
                logger.error(f"Database operation failed with SQLAlchemy error: {e}")
                raise
        
        if last_exception:
            raise last_exception
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            with self.session_scope() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                # Get connection pool status
                pool_status = {
                    'pool_size': self.engine.pool.size(),
                    'checked_in': self.engine.pool.checkedin(),
                    'checked_out': self.engine.pool.checkedout(),
                    'overflow': self.engine.pool.overflow(),
                    'invalid': self.engine.pool.invalid()
                }
                
                # Get session statistics
                session_stats = self._session_stats.copy()
                
                return {
                    'status': 'healthy' if test_value == 1 else 'unhealthy',
                    'test_value': test_value,
                    'pool_status': pool_status,
                    'session_stats': session_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _cleanup_session(self, exception=None):
        """Cleanup session on Flask app teardown"""
        if hasattr(g, 'db_session'):
            g.db_session.close()
            delattr(g, 'db_session')
            logger.debug("Flask app context session cleaned up")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self._session_stats.copy()


# Global session manager instance
session_manager = DatabaseSessionManager()


def get_session_manager() -> DatabaseSessionManager:
    """Get the global session manager instance"""
    return session_manager


def init_session_manager(app=None, database_url: str = None):
    """Initialize the global session manager"""
    global session_manager
    
    if app:
        session_manager.init_app(app)
    elif database_url:
        session_manager = DatabaseSessionManager(database_url)
    else:
        raise ValueError("Either app or database_url must be provided")


# Convenience functions for common operations
def get_db_session() -> Session:
    """Get a database session for the current context"""
    return session_manager.get_scoped_session()


def get_db_session_scope():
    """Get a session scope context manager"""
    return session_manager.scoped_session_scope()


def execute_db_operation(operation, max_retries: int = 3):
    """Execute database operation with retry logic"""
    return session_manager.execute_with_retry(operation, max_retries)


# Decorator for automatic session management
def with_db_session(commit_on_success: bool = True, rollback_on_error: bool = True):
    """
    Decorator for automatic database session management
    
    Args:
        commit_on_success: Whether to commit on successful completion
        rollback_on_error: Whether to rollback on error
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with session_manager.scoped_session_scope(
                commit_on_success=commit_on_success,
                rollback_on_error=rollback_on_error
            ) as session:
                # Inject session as first argument if function expects it
                if 'session' in func.__code__.co_varnames:
                    return func(session, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return wrapper
    return decorator


# Celery-specific session management
class CelerySessionManager:
    """
    Specialized session manager for Celery tasks
    Handles session lifecycle in Celery worker processes
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self._worker_session = None
        self._worker_id = None
    
    def init_worker(self, worker_id: str):
        """Initialize session manager for a Celery worker"""
        self._worker_id = worker_id
        
        # Create engine with worker-specific settings
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,  # Smaller pool for workers
            max_overflow=10,
            pool_recycle=1800,  # 30 minutes
            pool_pre_ping=True,
            pool_timeout=30,
            connect_args={
                'application_name': f'mingus_celery_worker_{worker_id}',
                'options': '-c timezone=utc -c statement_timeout=60000',  # Longer timeout for tasks
                'connect_timeout': 10,
                'command_timeout': 60
            }
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        logger.info(f"Celery worker {worker_id} session manager initialized")
    
    def get_worker_session(self) -> Session:
        """Get a session for the current worker"""
        if not self._worker_session:
            self._worker_session = self.session_factory()
        
        return self._worker_session
    
    def close_worker_session(self):
        """Close the worker session"""
        if self._worker_session:
            self._worker_session.close()
            self._worker_session = None
            logger.debug(f"Celery worker {self._worker_id} session closed")
    
    @contextmanager
    def worker_session_scope(self, commit_on_success: bool = True) -> Generator[Session, None, None]:
        """Context manager for worker sessions"""
        session = None
        try:
            session = self.get_worker_session()
            yield session
            
            if commit_on_success:
                session.commit()
                
        except Exception as e:
            if session:
                session.rollback()
            raise
        finally:
            # Don't close the session here, keep it for reuse
            pass


# Global Celery session manager
celery_session_manager = None


def get_celery_session_manager() -> CelerySessionManager:
    """Get the global Celery session manager"""
    global celery_session_manager
    return celery_session_manager


def init_celery_session_manager(database_url: str, worker_id: str = None):
    """Initialize the Celery session manager"""
    global celery_session_manager
    
    if not celery_session_manager:
        celery_session_manager = CelerySessionManager(database_url)
    
    if worker_id:
        celery_session_manager.init_worker(worker_id)


# Error handling utilities
class DatabaseErrorHandler:
    """Utility class for handling database errors"""
    
    @staticmethod
    def handle_communication_logging_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle errors specifically for communication logging"""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if isinstance(error, IntegrityError):
            logger.error(f"Database integrity error in {context}: {error}")
            error_info['severity'] = 'high'
            error_info['action'] = 'check_data_consistency'
            
        elif isinstance(error, OperationalError):
            logger.error(f"Database operational error in {context}: {error}")
            error_info['severity'] = 'medium'
            error_info['action'] = 'retry_operation'
            
        elif isinstance(error, TimeoutError):
            logger.error(f"Database timeout error in {context}: {error}")
            error_info['severity'] = 'medium'
            error_info['action'] = 'increase_timeout'
            
        elif isinstance(error, DisconnectionError):
            logger.error(f"Database disconnection error in {context}: {error}")
            error_info['severity'] = 'high'
            error_info['action'] = 'reconnect'
            
        else:
            logger.error(f"Unexpected database error in {context}: {error}")
            error_info['severity'] = 'unknown'
            error_info['action'] = 'investigate'
        
        return error_info
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if an error should trigger a retry"""
        retryable_errors = (
            OperationalError,
            TimeoutError,
            DisconnectionError
        )
        
        return isinstance(error, retryable_errors)
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate retry delay with exponential backoff"""
        if isinstance(error, TimeoutError):
            return base_delay * (2 ** attempt)  # Exponential backoff
        elif isinstance(error, DisconnectionError):
            return base_delay * (3 ** attempt)  # More aggressive backoff
        else:
            return base_delay * (1.5 ** attempt)  # Moderate backoff


# Transaction management utilities
class TransactionManager:
    """Utility class for managing database transactions"""
    
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager
    
    @contextmanager
    def communication_transaction(self, operation_name: str = "communication_operation"):
        """
        Context manager for communication-related transactions
        Includes specific error handling and logging
        """
        with self.session_manager.scoped_session_scope() as session:
            transaction_start = datetime.utcnow()
            
            try:
                logger.debug(f"Starting {operation_name} transaction")
                yield session
                
                session.commit()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                logger.info(f"{operation_name} transaction committed successfully in {transaction_duration:.3f}s")
                
            except Exception as e:
                session.rollback()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                
                error_info = DatabaseErrorHandler.handle_communication_logging_error(e, operation_name)
                error_info['transaction_duration'] = transaction_duration
                
                logger.error(f"{operation_name} transaction failed after {transaction_duration:.3f}s: {e}")
                raise
    
    def batch_communication_transaction(self, operations: list, operation_name: str = "batch_communication"):
        """
        Execute multiple communication operations in a single transaction
        """
        with self.session_manager.scoped_session_scope() as session:
            transaction_start = datetime.utcnow()
            successful_operations = 0
            failed_operations = []
            
            try:
                logger.debug(f"Starting {operation_name} batch transaction with {len(operations)} operations")
                
                for i, operation in enumerate(operations):
                    try:
                        operation(session)
                        successful_operations += 1
                        
                    except Exception as e:
                        failed_operations.append({
                            'index': i,
                            'error': str(e),
                            'operation': str(operation)
                        })
                        logger.warning(f"Operation {i} in {operation_name} failed: {e}")
                
                if failed_operations:
                    # Rollback if any operations failed
                    session.rollback()
                    transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                    logger.error(f"{operation_name} batch transaction rolled back after {transaction_duration:.3f}s. "
                               f"Successful: {successful_operations}, Failed: {len(failed_operations)}")
                    
                    raise Exception(f"Batch operation failed: {len(failed_operations)} operations failed")
                
                else:
                    # Commit if all operations succeeded
                    session.commit()
                    transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                    logger.info(f"{operation_name} batch transaction committed successfully in {transaction_duration:.3f}s. "
                              f"Operations: {successful_operations}")
                
            except Exception as e:
                session.rollback()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                logger.error(f"{operation_name} batch transaction failed after {transaction_duration:.3f}s: {e}")
                raise


# Export main functions and classes
__all__ = [
    'DatabaseSessionManager',
    'CelerySessionManager',
    'DatabaseErrorHandler',
    'TransactionManager',
    'session_manager',
    'get_session_manager',
    'init_session_manager',
    'get_db_session',
    'get_db_session_scope',
    'execute_db_operation',
    'with_db_session',
    'get_celery_session_manager',
    'init_celery_session_manager'
] 