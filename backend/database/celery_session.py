"""
Celery Session Management for Communication Tasks
Specialized session handling for Celery background tasks
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any, Dict
from datetime import datetime, timedelta
import threading
from functools import wraps

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import (
    SQLAlchemyError, 
    DisconnectionError, 
    TimeoutError, 
    OperationalError,
    IntegrityError,
    DataError
)

from celery import current_task, Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class CeleryDatabaseSession:
    """
    Database session management specifically for Celery tasks
    Optimized for background task processing with proper connection pooling
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engine = None
        self.session_factory = None
        self._worker_sessions = {}
        self._lock = threading.Lock()
        self._stats = {
            'sessions_created': 0,
            'sessions_closed': 0,
            'transactions_committed': 0,
            'transactions_rollbacked': 0,
            'connection_errors': 0,
            'timeout_errors': 0
        }
        
        if self.database_url:
            self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the database engine with Celery-optimized settings"""
        # Celery-specific connection pooling settings
        pool_settings = {
            'poolclass': QueuePool,
            'pool_size': int(os.environ.get('CELERY_DB_POOL_SIZE', 10)),  # Smaller pool for workers
            'max_overflow': int(os.environ.get('CELERY_DB_MAX_OVERFLOW', 20)),
            'pool_recycle': int(os.environ.get('CELERY_DB_POOL_RECYCLE', 1800)),  # 30 minutes
            'pool_pre_ping': True,
            'pool_timeout': int(os.environ.get('CELERY_DB_POOL_TIMEOUT', 30)),
            'pool_reset_on_return': 'commit',
            'echo': os.environ.get('CELERY_DB_ECHO', 'false').lower() == 'true'
        }
        
        # Connection arguments optimized for Celery tasks
        connect_args = {
            'application_name': 'mingus_celery_communication',
            'options': '-c timezone=utc -c statement_timeout=60000 -c idle_in_transaction_session_timeout=120000',
            'connect_timeout': 10,
            'command_timeout': 60,
            'sslmode': os.environ.get('DB_SSL_MODE', 'prefer')
        }
        
        self.engine = create_engine(
            self.database_url,
            **pool_settings,
            connect_args=connect_args
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Setup engine event listeners
        self._setup_engine_events()
        
        logger.info(f"Celery database engine initialized with pool_size={pool_settings['pool_size']}")
    
    def _setup_engine_events(self):
        """Setup engine event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Handle new connections"""
            logger.debug("New Celery database connection established")
            
            # Set connection-level settings
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET timezone = 'UTC'")
                cursor.execute("SET statement_timeout = '60s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '120s'")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout"""
            logger.debug("Celery database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin"""
            logger.debug("Celery database connection checked in")
        
        # 'disconnect' is not a valid Engine event in SQLAlchemy 2.x; guard registration
        try:
            @event.listens_for(self.engine, "disconnect")
            def receive_disconnect(dbapi_connection, connection_record):
                """Handle connection disconnection"""
                logger.warning("Celery database connection disconnected")
                self._stats['connection_errors'] += 1
        except Exception:
            logger.debug("Skipping 'disconnect' engine event registration (unsupported)")
    
    def get_session(self) -> Session:
        """Get a new database session for the current task"""
        try:
            session = self.session_factory()
            self._stats['sessions_created'] += 1
            
            # Store session reference for cleanup
            task_id = self._get_current_task_id()
            if task_id:
                with self._lock:
                    if task_id not in self._worker_sessions:
                        self._worker_sessions[task_id] = []
                    self._worker_sessions[task_id].append(session)
            
            logger.debug(f"New Celery database session created for task {task_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create Celery database session: {e}")
            raise
    
    def _get_current_task_id(self) -> Optional[str]:
        """Get the current Celery task ID"""
        if current_task and current_task.request:
            return current_task.request.id
        return None
    
    @contextmanager
    def session_scope(self, commit_on_success: bool = True, rollback_on_error: bool = True) -> Generator[Session, None, None]:
        """
        Context manager for Celery database sessions
        
        Args:
            commit_on_success: Whether to commit on successful completion
            rollback_on_error: Whether to rollback on error
        """
        session = None
        task_id = self._get_current_task_id()
        
        try:
            session = self.get_session()
            logger.debug(f"Celery session scope entered for task {task_id}")
            
            yield session
            
            if commit_on_success:
                session.commit()
                self._stats['transactions_committed'] += 1
                logger.debug(f"Celery session committed for task {task_id}")
                
        except Exception as e:
            if session and rollback_on_error:
                session.rollback()
                self._stats['transactions_rollbacked'] += 1
                logger.warning(f"Celery session rolled back for task {task_id}: {e}")
            
            # Log specific error types
            if isinstance(e, TimeoutError):
                self._stats['timeout_errors'] += 1
            elif isinstance(e, DisconnectionError):
                self._stats['connection_errors'] += 1
            
            raise
            
        finally:
            if session:
                session.close()
                self._stats['sessions_closed'] += 1
                logger.debug(f"Celery session closed for task {task_id}")
    
    def cleanup_task_sessions(self, task_id: str = None):
        """Cleanup sessions for a specific task"""
        if not task_id:
            task_id = self._get_current_task_id()
        
        if task_id and task_id in self._worker_sessions:
            with self._lock:
                sessions = self._worker_sessions[task_id]
                for session in sessions:
                    try:
                        session.close()
                        self._stats['sessions_closed'] += 1
                    except Exception as e:
                        logger.warning(f"Error closing session for task {task_id}: {e}")
                
                del self._worker_sessions[task_id]
                logger.debug(f"Cleaned up {len(sessions)} sessions for task {task_id}")
    
    def execute_with_retry(self, operation, max_retries: int = 3, base_delay: float = 1.0):
        """
        Execute database operation with retry logic optimized for Celery tasks
        
        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
        """
        last_exception = None
        task_id = self._get_current_task_id()
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
                
            except (DisconnectionError, OperationalError, TimeoutError) as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Celery task {task_id} database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay}s")
                    
                    import time
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Celery task {task_id} database operation failed after {max_retries + 1} attempts: {e}")
                    raise
                    
            except (IntegrityError, DataError) as e:
                # Don't retry on data/constraint errors
                logger.error(f"Celery task {task_id} database operation failed with data error: {e}")
                raise
                
            except SQLAlchemyError as e:
                last_exception = e
                logger.error(f"Celery task {task_id} database operation failed with SQLAlchemy error: {e}")
                raise
        
        if last_exception:
            raise last_exception
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check for Celery workers"""
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
                
                return {
                    'status': 'healthy' if test_value == 1 else 'unhealthy',
                    'test_value': test_value,
                    'pool_status': pool_status,
                    'session_stats': self._stats.copy(),
                    'active_task_sessions': len(self._worker_sessions),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Celery database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self._stats.copy()


# Global Celery session manager
celery_db_session = CeleryDatabaseSession()


def get_celery_db_session() -> CeleryDatabaseSession:
    """Get the global Celery database session manager"""
    return celery_db_session


def init_celery_db_session(database_url: str = None):
    """Initialize the Celery database session manager"""
    global celery_db_session
    if database_url:
        celery_db_session = CeleryDatabaseSession(database_url)
    else:
        celery_db_session = CeleryDatabaseSession()


# Celery task base class with database session management
class DatabaseTask(Task):
    """
    Base Celery task class with integrated database session management
    """
    
    abstract = True
    
    def __init__(self):
        self.db_session = None
    
    def __call__(self, *args, **kwargs):
        """Initialize database session when task is called"""
        try:
            self.db_session = get_celery_db_session()
            return super().__call__(*args, **kwargs)
        finally:
            # Cleanup task sessions
            task_id = self.request.id if self.request else None
            if task_id:
                self.db_session.cleanup_task_sessions(task_id)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion"""
        super().on_success(retval, task_id, args, kwargs)
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        super().on_failure(exc, task_id, args, kwargs, einfo)
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Cleanup database sessions on failure
        if self.db_session:
            self.db_session.cleanup_task_sessions(task_id)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        super().on_retry(exc, task_id, args, kwargs, einfo)
        logger.warning(f"Task {task_id} retrying: {exc}")


# Decorator for automatic session management in Celery tasks
def with_celery_db_session(commit_on_success: bool = True, rollback_on_error: bool = True):
    """
    Decorator for automatic database session management in Celery tasks
    
    Args:
        commit_on_success: Whether to commit on successful completion
        rollback_on_error: Whether to rollback on error
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_session = get_celery_db_session()
            
            with db_session.session_scope(
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


# Communication-specific transaction management
class CommunicationTransactionManager:
    """
    Specialized transaction manager for communication-related operations
    """
    
    def __init__(self, db_session: CeleryDatabaseSession = None):
        self.db_session = db_session or get_celery_db_session()
    
    @contextmanager
    def communication_logging_transaction(self, operation_name: str = "communication_logging"):
        """
        Context manager for communication logging transactions
        Includes specific error handling and retry logic
        """
        task_id = self._get_current_task_id()
        
        with self.db_session.session_scope() as session:
            transaction_start = datetime.utcnow()
            
            try:
                logger.debug(f"Starting {operation_name} transaction for task {task_id}")
                yield session
                
                session.commit()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                logger.info(f"{operation_name} transaction committed for task {task_id} in {transaction_duration:.3f}s")
                
            except Exception as e:
                session.rollback()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                
                logger.error(f"{operation_name} transaction failed for task {task_id} after {transaction_duration:.3f}s: {e}")
                
                # Handle specific communication logging errors
                if isinstance(e, IntegrityError):
                    logger.error(f"Data integrity error in {operation_name} for task {task_id}: {e}")
                elif isinstance(e, TimeoutError):
                    logger.error(f"Timeout error in {operation_name} for task {task_id}: {e}")
                elif isinstance(e, DisconnectionError):
                    logger.error(f"Connection error in {operation_name} for task {task_id}: {e}")
                
                raise
    
    def batch_communication_transaction(self, operations: list, operation_name: str = "batch_communication"):
        """
        Execute multiple communication operations in a single transaction
        """
        task_id = self._get_current_task_id()
        
        with self.db_session.session_scope() as session:
            transaction_start = datetime.utcnow()
            successful_operations = 0
            failed_operations = []
            
            try:
                logger.debug(f"Starting {operation_name} batch transaction for task {task_id} with {len(operations)} operations")
                
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
                        logger.warning(f"Operation {i} in {operation_name} failed for task {task_id}: {e}")
                
                if failed_operations:
                    # Rollback if any operations failed
                    session.rollback()
                    transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                    logger.error(f"{operation_name} batch transaction rolled back for task {task_id} after {transaction_duration:.3f}s. "
                               f"Successful: {successful_operations}, Failed: {len(failed_operations)}")
                    
                    raise Exception(f"Batch operation failed: {len(failed_operations)} operations failed")
                
                else:
                    # Commit if all operations succeeded
                    session.commit()
                    transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                    logger.info(f"{operation_name} batch transaction committed for task {task_id} in {transaction_duration:.3f}s. "
                              f"Operations: {successful_operations}")
                
            except Exception as e:
                session.rollback()
                transaction_duration = (datetime.utcnow() - transaction_start).total_seconds()
                logger.error(f"{operation_name} batch transaction failed for task {task_id} after {transaction_duration:.3f}s: {e}")
                raise
    
    def _get_current_task_id(self) -> Optional[str]:
        """Get the current Celery task ID"""
        if current_task and current_task.request:
            return current_task.request.id
        return None


# Error handling utilities for Celery tasks
class CeleryDatabaseErrorHandler:
    """Error handling utilities for Celery database operations"""
    
    @staticmethod
    def handle_communication_error(error: Exception, task_id: str = None, context: str = "") -> Dict[str, Any]:
        """Handle database errors in communication tasks"""
        if not task_id:
            task_id = current_task.request.id if current_task and current_task.request else "unknown"
        
        error_info = {
            'task_id': task_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if isinstance(error, IntegrityError):
            logger.error(f"Database integrity error in task {task_id} ({context}): {error}")
            error_info['severity'] = 'high'
            error_info['action'] = 'check_data_consistency'
            
        elif isinstance(error, OperationalError):
            logger.error(f"Database operational error in task {task_id} ({context}): {error}")
            error_info['severity'] = 'medium'
            error_info['action'] = 'retry_operation'
            
        elif isinstance(error, TimeoutError):
            logger.error(f"Database timeout error in task {task_id} ({context}): {error}")
            error_info['severity'] = 'medium'
            error_info['action'] = 'increase_timeout'
            
        elif isinstance(error, DisconnectionError):
            logger.error(f"Database disconnection error in task {task_id} ({context}): {error}")
            error_info['severity'] = 'high'
            error_info['action'] = 'reconnect'
            
        else:
            logger.error(f"Unexpected database error in task {task_id} ({context}): {error}")
            error_info['severity'] = 'unknown'
            error_info['action'] = 'investigate'
        
        return error_info
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if an error should trigger a retry in Celery tasks"""
        retryable_errors = (
            OperationalError,
            TimeoutError,
            DisconnectionError
        )
        
        return isinstance(error, retryable_errors)
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate retry delay with exponential backoff for Celery tasks"""
        if isinstance(error, TimeoutError):
            return base_delay * (2 ** attempt)  # Exponential backoff
        elif isinstance(error, DisconnectionError):
            return base_delay * (3 ** attempt)  # More aggressive backoff
        else:
            return base_delay * (1.5 ** attempt)  # Moderate backoff


# Export main functions and classes
__all__ = [
    'CeleryDatabaseSession',
    'DatabaseTask',
    'CommunicationTransactionManager',
    'CeleryDatabaseErrorHandler',
    'celery_db_session',
    'get_celery_db_session',
    'init_celery_db_session',
    'with_celery_db_session'
] 