#!/usr/bin/env python3
"""
Session Management Utilities
Helper functions for managing Redis-based sessions
"""

from flask import session, current_app
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Utilities for managing Redis sessions"""
    
    @staticmethod
    def get_user_id():
        """Get current user ID from session"""
        return session.get('user_id')
    
    @staticmethod
    def get_user_email():
        """Get current user email from session"""
        return session.get('email')
    
    @staticmethod
    def is_authenticated():
        """Check if user is authenticated"""
        return 'user_id' in session
    
    @staticmethod
    def create_session(user_id: str, user_data: dict = None):
        """
        Create new session
        
        Args:
            user_id: User identifier
            user_data: Additional user data to store in session
        """
        session['user_id'] = user_id
        session.permanent = True
        
        if user_data:
            session.update(user_data)
        
        logger.info(f"Session created for user {user_id}")
    
    @staticmethod
    def destroy_session():
        """Destroy current session"""
        user_id = session.get('user_id')
        session.clear()
        logger.info(f"Session destroyed for user {user_id}")
    
    @staticmethod
    def extend_session():
        """Extend session lifetime"""
        session.permanent = True
        # Session lifetime is managed by Redis TTL
        logger.debug("Session extended")
    
    @staticmethod
    def get_session_data():
        """Get all session data as dictionary"""
        return dict(session)
    
    @staticmethod
    def update_session(key: str, value: Any):
        """Update a specific session value"""
        session[key] = value
        session.permanent = True
    
    @staticmethod
    def get_session_value(key: str, default=None):
        """Get a specific session value"""
        return session.get(key, default)
