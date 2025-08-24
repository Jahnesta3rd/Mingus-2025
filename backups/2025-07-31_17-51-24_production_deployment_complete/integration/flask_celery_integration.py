"""
Flask-Celery Integration for MINGUS Communication System
Proper Flask app context handling in Celery tasks with database session management
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Any, Dict
from functools import wraps

from flask import Flask, current_app, g
from celery import Task, current_task
from celery.utils.log import get_task_logger

from ..database.celery_session import get_celery_db_session, CommunicationTransactionManager
from ..database.connection_pool import get_pool_manager

logger = get_task_logger(__name__)


class FlaskTask(Task):
    """
    Base Celery task class with Flask app context integration
    Provides automatic Flask app context and database session management
    """
    
    abstract = True
    
    def __init__(self):
        self.flask_app = None
        self.db_session = None
        self.transaction_manager = None
    
    def __call__(self, *args, **kwargs):
        """Initialize Flask app context when task is called"""
        try:
            # Get Flask app from Celery config or environment
            if hasattr(self.app.conf, 'flask_app'):
                self.flask_app = self.app.conf.flask_app
            else:
                # Try to get Flask app from environment
                self.flask_app = self._get_flask_app()
            
            # Initialize database session
            self.db_session = get_celery_db_session()
            self.transaction_manager = CommunicationTransactionManager(self.db_session)
            
            # Execute task with Flask app context
            if self.flask_app:
                with self.flask_app.app_context():
                    return super().__call__(*args, **kwargs)
            else:
                return super().__call__(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Error in Flask task {self.name}: {e}")
            raise
        finally:
            # Cleanup task sessions
            task_id = current_task.request.id if current_task and current_task.request else None
            if task_id and self.db_session:
                self.db_session.cleanup_task_sessions(task_id)
    
    def _get_flask_app(self) -> Optional[Flask]:
        """Get Flask app from environment or configuration"""
        try:
            # Try to import and create Flask app
            from backend.app_factory import create_app
            
            # Get environment from Celery config or environment variable
            environment = getattr(self.app.conf, 'flask_environment', None)
            if not environment:
                environment = os.environ.get('FLASK_ENV', 'development')
            
            return create_app(environment)
            
        except Exception as e:
            logger.warning(f"Could not create Flask app: {e}")
            return None
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion"""
        super().on_success(retval, task_id, args, kwargs)
        logger.info(f"Flask task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        super().on_failure(exc, task_id, args, kwargs, einfo)
        logger.error(f"Flask task {task_id} failed: {exc}")
        
        # Cleanup database sessions on failure
        if self.db_session:
            self.db_session.cleanup_task_sessions(task_id)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        super().on_retry(exc, task_id, args, kwargs, einfo)
        logger.warning(f"Flask task {task_id} retrying: {exc}")
    
    def get_flask_app(self) -> Optional[Flask]:
        """Get Flask app instance"""
        return self.flask_app or current_app._get_current_object()
    
    def get_db_session(self):
        """Get database session for the task"""
        return self.db_session
    
    def get_transaction_manager(self):
        """Get transaction manager for the task"""
        return self.transaction_manager


class FlaskAppContextTask(FlaskTask):
    """
    Celery task with explicit Flask app context management
    Use this for tasks that need more control over Flask app context
    """
    
    abstract = True
    
    def __call__(self, *args, **kwargs):
        """Execute task with explicit Flask app context"""
        flask_app = self.get_flask_app()
        
        if flask_app:
            with flask_app.app_context():
                # Set up Flask g object for database session
                if not hasattr(g, 'db_session'):
                    g.db_session = get_celery_db_session()
                
                return super().__call__(*args, **kwargs)
        else:
            return super().__call__(*args, **kwargs)


def with_flask_context(func):
    """
    Decorator to ensure Flask app context in Celery tasks
    
    Args:
        func: Function to wrap with Flask context
    
    Returns:
        Wrapped function with Flask app context
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get Flask app from current task or environment
        flask_app = None
        
        if current_task and hasattr(current_task, 'get_flask_app'):
            flask_app = current_task.get_flask_app()
        else:
            # Try to get Flask app from environment
            try:
                from backend.app_factory import create_app
                environment = os.environ.get('FLASK_ENV', 'development')
                flask_app = create_app(environment)
            except Exception as e:
                logger.warning(f"Could not create Flask app: {e}")
        
        if flask_app:
            with flask_app.app_context():
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    return wrapper


def with_database_session(func):
    """
    Decorator to provide database session in Celery tasks
    
    Args:
        func: Function to wrap with database session
    
    Returns:
        Wrapped function with database session
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session = get_celery_db_session()
        
        with db_session.session_scope() as session:
            # Inject session as first argument if function expects it
            if 'session' in func.__code__.co_varnames:
                return func(session, *args, **kwargs)
            else:
                return func(*args, **kwargs)
    
    return wrapper


def with_flask_and_database(func):
    """
    Decorator to provide both Flask app context and database session
    
    Args:
        func: Function to wrap with Flask context and database session
    
    Returns:
        Wrapped function with Flask context and database session
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get Flask app
        flask_app = None
        if current_task and hasattr(current_task, 'get_flask_app'):
            flask_app = current_task.get_flask_app()
        else:
            try:
                from backend.app_factory import create_app
                environment = os.environ.get('FLASK_ENV', 'development')
                flask_app = create_app(environment)
            except Exception as e:
                logger.warning(f"Could not create Flask app: {e}")
        
        # Get database session
        db_session = get_celery_db_session()
        
        if flask_app:
            with flask_app.app_context():
                with db_session.session_scope() as session:
                    if 'session' in func.__code__.co_varnames:
                        return func(session, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
        else:
            with db_session.session_scope() as session:
                if 'session' in func.__code__.co_varnames:
                    return func(session, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
    
    return wrapper


@contextmanager
def flask_app_context():
    """
    Context manager for Flask app context in Celery tasks
    
    Yields:
        Flask app context
    """
    flask_app = None
    
    # Try to get Flask app from current task
    if current_task and hasattr(current_task, 'get_flask_app'):
        flask_app = current_task.get_flask_app()
    
    # Try to get Flask app from environment
    if not flask_app:
        try:
            from backend.app_factory import create_app
            environment = os.environ.get('FLASK_ENV', 'development')
            flask_app = create_app(environment)
        except Exception as e:
            logger.warning(f"Could not create Flask app: {e}")
    
    if flask_app:
        with flask_app.app_context():
            yield flask_app
    else:
        yield None


@contextmanager
def celery_database_session():
    """
    Context manager for database session in Celery tasks
    
    Yields:
        Database session
    """
    db_session = get_celery_db_session()
    
    with db_session.session_scope() as session:
        yield session


@contextmanager
def flask_and_database_context():
    """
    Context manager for both Flask app context and database session
    
    Yields:
        Tuple of (Flask app, database session)
    """
    flask_app = None
    
    # Try to get Flask app from current task
    if current_task and hasattr(current_task, 'get_flask_app'):
        flask_app = current_task.get_flask_app()
    
    # Try to get Flask app from environment
    if not flask_app:
        try:
            from backend.app_factory import create_app
            environment = os.environ.get('FLASK_ENV', 'development')
            flask_app = create_app(environment)
        except Exception as e:
            logger.warning(f"Could not create Flask app: {e}")
    
    # Get database session
    db_session = get_celery_db_session()
    
    if flask_app:
        with flask_app.app_context():
            with db_session.session_scope() as session:
                yield flask_app, session
    else:
        with db_session.session_scope() as session:
            yield None, session


def get_flask_service(service_name: str):
    """
    Get Flask service from current app context
    
    Args:
        service_name: Name of the service to get
    
    Returns:
        Service instance or None
    """
    try:
        flask_app = None
        
        # Try to get Flask app from current task
        if current_task and hasattr(current_task, 'get_flask_app'):
            flask_app = current_task.get_flask_app()
        
        # Try to get Flask app from current app context
        if not flask_app:
            flask_app = current_app._get_current_object()
        
        # Get service from Flask app
        if hasattr(flask_app, 'config') and 'services' in flask_app.config:
            services = flask_app.config['services']
            if service_name in services:
                return services[service_name]
        
        # Try to get service from app factory
        if hasattr(flask_app, 'get_service'):
            return flask_app.get_service(service_name)
        
        logger.warning(f"Service {service_name} not found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting Flask service {service_name}: {e}")
        return None


def get_database_session():
    """
    Get database session for current task
    
    Returns:
        Database session instance
    """
    try:
        # Try to get session from current task
        if current_task and hasattr(current_task, 'get_db_session'):
            return current_task.get_db_session()
        
        # Get session from global manager
        return get_celery_db_session()
        
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        return None


def get_transaction_manager():
    """
    Get transaction manager for current task
    
    Returns:
        Transaction manager instance
    """
    try:
        # Try to get transaction manager from current task
        if current_task and hasattr(current_task, 'get_transaction_manager'):
            return current_task.get_transaction_manager()
        
        # Create new transaction manager
        db_session = get_celery_db_session()
        return CommunicationTransactionManager(db_session)
        
    except Exception as e:
        logger.error(f"Error getting transaction manager: {e}")
        return None


def init_flask_celery_integration(flask_app: Flask, celery_app):
    """
    Initialize Flask-Celery integration
    
    Args:
        flask_app: Flask application instance
        celery_app: Celery application instance
    """
    try:
        # Store Flask app in Celery config
        celery_app.conf.update(
            flask_app=flask_app,
            flask_environment=flask_app.config.get('ENV', 'development'),
            flask_app_context=True
        )
        
        # Set Flask task as default task class
        celery_app.Task = FlaskTask
        
        # Initialize database session manager
        from ..database.celery_session import init_celery_db_session
        init_celery_db_session()
        
        # Initialize connection pool manager
        from ..database.connection_pool import init_pool_manager
        init_pool_manager()
        
        logger.info("Flask-Celery integration initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing Flask-Celery integration: {e}")
        raise


def get_flask_celery_integration() -> Dict[str, Any]:
    """
    Get Flask-Celery integration status
    
    Returns:
        Integration status information
    """
    try:
        status = {
            'flask_app_available': False,
            'celery_app_available': False,
            'database_session_available': False,
            'connection_pool_available': False,
            'services': {}
        }
        
        # Check Flask app availability
        try:
            flask_app = current_app._get_current_object()
            status['flask_app_available'] = True
            status['flask_app_name'] = flask_app.name
        except Exception:
            pass
        
        # Check Celery app availability
        try:
            from celery import current_app as celery_current_app
            if celery_current_app:
                status['celery_app_available'] = True
                status['celery_app_name'] = celery_current_app.main
        except Exception:
            pass
        
        # Check database session availability
        try:
            db_session = get_celery_db_session()
            if db_session:
                status['database_session_available'] = True
                status['database_session_stats'] = db_session.get_stats()
        except Exception:
            pass
        
        # Check connection pool availability
        try:
            pool_manager = get_pool_manager()
            if pool_manager:
                status['connection_pool_available'] = True
                status['connection_pool_health'] = pool_manager.get_pool_health()
        except Exception:
            pass
        
        # Check service availability
        services_to_check = [
            'communication_preference_service',
            'analytics_service',
            'reporting_service',
            'communication_orchestrator'
        ]
        
        for service_name in services_to_check:
            try:
                service = get_flask_service(service_name)
                status['services'][service_name] = service is not None
            except Exception:
                status['services'][service_name] = False
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting Flask-Celery integration status: {e}")
        return {
            'error': str(e),
            'flask_app_available': False,
            'celery_app_available': False,
            'database_session_available': False,
            'connection_pool_available': False,
            'services': {}
        }


# Export main functions and classes
__all__ = [
    'FlaskTask',
    'FlaskAppContextTask',
    'with_flask_context',
    'with_database_session',
    'with_flask_and_database',
    'flask_app_context',
    'celery_database_session',
    'flask_and_database_context',
    'get_flask_service',
    'get_database_session',
    'get_transaction_manager',
    'init_flask_celery_integration',
    'get_flask_celery_integration'
] 