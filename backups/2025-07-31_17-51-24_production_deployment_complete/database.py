"""
Database Session Management
Provides SQLAlchemy session handling for the MINGUS application
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from flask import g, current_app
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global session factory
SessionLocal = None
engine = None


def init_database_session_factory(database_url: str, pool_size: int = 10, max_overflow: int = 20):
    """
    Initialize the database session factory
    
    Args:
        database_url: Database connection URL
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
    """
    global SessionLocal, engine
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info(f"Database session factory initialized with URL: {database_url}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database session factory: {e}")
        raise


def get_db_session() -> Session:
    """
    Get a database session
    
    Returns:
        SQLAlchemy session instance
    """
    if SessionLocal is None:
        raise RuntimeError("Database session factory not initialized. Call init_database_session_factory first.")
    
    return SessionLocal()


def get_flask_db_session() -> Session:
    """
    Get a database session for Flask application context
    
    Returns:
        SQLAlchemy session instance
    """
    if 'db_session' not in g:
        g.db_session = get_db_session()
    
    return g.db_session


def close_flask_db_session(error=None):
    """
    Close the database session for Flask application context
    """
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.close()


@contextmanager
def get_db_session_context():
    """
    Context manager for database sessions
    
    Usage:
        with get_db_session_context() as session:
            # Use session
            session.commit()
    """
    session = get_db_session()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_app_database(app):
    """
    Initialize database for Flask application
    
    Args:
        app: Flask application instance
    """
    try:
        database_url = app.config.get('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not configured, skipping database setup")
            return
        
        pool_size = app.config.get('DB_POOL_SIZE', 10)
        max_overflow = app.config.get('DB_MAX_OVERFLOW', 20)
        
        # Initialize session factory
        init_database_session_factory(database_url, pool_size, max_overflow)
        
        # Register Flask teardown context
        app.teardown_appcontext(close_flask_db_session)
        
        logger.info("Database initialized for Flask application")
        
    except Exception as e:
        logger.error(f"Failed to initialize database for Flask app: {e}")
        raise


def create_tables():
    """
    Create all database tables
    """
    try:
        from backend.models import Base
        
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        from backend.models import Base
        
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        if engine is None:
            return False
        
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
        
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database information
    
    Returns:
        Dictionary with database information
    """
    try:
        if engine is None:
            return {"status": "not_initialized"}
        
        info = {
            "status": "initialized",
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"status": "error", "error": str(e)}


# Flask application context helpers
def get_current_db_session() -> Optional[Session]:
    """
    Get current database session from Flask application context
    
    Returns:
        Current database session or None if not in Flask context
    """
    try:
        return get_flask_db_session()
    except RuntimeError:
        # Not in Flask application context
        return None


def commit_current_session():
    """
    Commit the current Flask database session
    """
    try:
        session = get_current_db_session()
        if session:
            session.commit()
    except Exception as e:
        logger.error(f"Failed to commit current session: {e}")
        raise


def rollback_current_session():
    """
    Rollback the current Flask database session
    """
    try:
        session = get_current_db_session()
        if session:
            session.rollback()
    except Exception as e:
        logger.error(f"Failed to rollback current session: {e}")
        raise


# Migration helpers
def run_migration(migration_file: str):
    """
    Run a SQL migration file
    
    Args:
        migration_file: Path to the migration SQL file
    """
    try:
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        with engine.connect() as connection:
            connection.execute(sql_content)
            connection.commit()
        
        logger.info(f"Migration {migration_file} executed successfully")
        
    except Exception as e:
        logger.error(f"Failed to run migration {migration_file}: {e}")
        raise


def execute_sql(sql: str, params: dict = None):
    """
    Execute raw SQL with parameters
    
    Args:
        sql: SQL query to execute
        params: Parameters for the query
    """
    try:
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        with engine.connect() as connection:
            if params:
                result = connection.execute(sql, params)
            else:
                result = connection.execute(sql)
            connection.commit()
            return result
        
    except Exception as e:
        logger.error(f"Failed to execute SQL: {e}")
        raise


# Health check
def health_check() -> dict:
    """
    Perform database health check
    
    Returns:
        Dictionary with health check results
    """
    try:
        connection_ok = check_database_connection()
        info = get_database_info()
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "connection": connection_ok,
            "database_info": info,
            "timestamp": "2025-01-27T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": "2025-01-27T12:00:00Z"
        } 