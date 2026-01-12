#!/usr/bin/env python3
"""
Redis Session Configuration for Mingus Application
Configures Flask-Session to use Redis for session storage
"""

import os
import redis
from flask import Flask
from flask_session import Session
import logging

logger = logging.getLogger(__name__)

def init_redis_session(app: Flask):
    """
    Initialize Redis-based session storage
    
    Args:
        app: Flask application instance
        
    Returns:
        Flask app with Redis session configured
    """
    try:
        # Get Redis configuration from environment
        redis_url = os.environ.get('REDIS_SESSION_URL', 'redis://localhost:6379/0')
        redis_password = os.environ.get('REDIS_PASSWORD')
        
        # Parse Redis URL and add password if provided
        if redis_password and '@' not in redis_url:
            # Add password to URL
            if '://:' in redis_url:
                redis_url = redis_url.replace('://:', f'://:{redis_password}@')
            elif 'redis://' in redis_url:
                redis_url = redis_url.replace('redis://', f'redis://:{redis_password}@')
        
        # Create Redis connection
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # Test connection
        redis_client.ping()
        logger.info("Redis connection successful for session storage")
        
        # Configure Flask-Session
        app.config.update({
            'SESSION_TYPE': 'redis',
            'SESSION_REDIS': redis_client,
            'SESSION_PERMANENT': True,
            'SESSION_USE_SIGNER': True,  # Sign session cookies for security
            'SESSION_KEY_PREFIX': 'mingus:session:',
            'SESSION_COOKIE_NAME': 'mingus_session',
            'SESSION_COOKIE_SECURE': os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'PERMANENT_SESSION_LIFETIME': int(os.environ.get('PERMANENT_SESSION_LIFETIME', '86400')),  # 24 hours
        })
        
        # Initialize Flask-Session
        Session(app)
        
        logger.info("Redis session storage configured successfully")
        return app
        
    except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
        logger.warning(f"Failed to connect to Redis for sessions: {e}")
        logger.info("Falling back to filesystem session storage")
        # Fallback to filesystem sessions
        try:
            import tempfile
            session_dir = os.path.join(tempfile.gettempdir(), 'flask_sessions')
            os.makedirs(session_dir, exist_ok=True)
            
            app.config.update({
                'SESSION_TYPE': 'filesystem',
                'SESSION_FILE_DIR': session_dir,
                'SESSION_FILE_THRESHOLD': 500,
            })
            Session(app)
            logger.info("Filesystem session storage configured successfully")
            return app
        except Exception as fallback_error:
            logger.error(f"Failed to configure filesystem sessions: {fallback_error}")
            # Last resort: use null session (no persistence)
            app.config.update({
                'SESSION_TYPE': 'null',
            })
            Session(app)
            logger.warning("Using null session storage (no persistence)")
            return app
    except Exception as e:
        logger.error(f"Unexpected error configuring Redis sessions: {e}")
        logger.warning("Falling back to filesystem session storage")
        # Fallback to filesystem sessions
        try:
            import tempfile
            session_dir = os.path.join(tempfile.gettempdir(), 'flask_sessions')
            os.makedirs(session_dir, exist_ok=True)
            
            app.config.update({
                'SESSION_TYPE': 'filesystem',
                'SESSION_FILE_DIR': session_dir,
                'SESSION_FILE_THRESHOLD': 500,
            })
            Session(app)
            return app
        except Exception:
            # Last resort
            app.config.update({'SESSION_TYPE': 'null'})
            Session(app)
            return app
