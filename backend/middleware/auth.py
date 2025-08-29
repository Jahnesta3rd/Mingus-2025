from functools import wraps
from flask import request, jsonify, current_app, session
import logging

# Import enhanced authentication
from backend.middleware.enhanced_auth import require_auth as enhanced_require_auth
from backend.middleware.enhanced_auth import get_current_user_id as enhanced_get_current_user_id

logger = logging.getLogger(__name__)

def require_auth(f):
    """Enhanced authentication decorator with security features"""
    return enhanced_require_auth(f)

def require_assessment_auth(f):
    """Enhanced authentication decorator specifically for assessment endpoints"""
    from backend.middleware.enhanced_auth import require_assessment_auth as enhanced_require_assessment_auth
    return enhanced_require_assessment_auth(f)

def require_secure_auth(f):
    """Enhanced authentication decorator with additional security checks"""
    from backend.middleware.enhanced_auth import require_secure_auth as enhanced_require_secure_auth
    return enhanced_require_secure_auth(f)

def get_current_user_id():
    """Get the current user ID from authentication context"""
    return enhanced_get_current_user_id()

def get_current_user_info():
    """Get current user information from authentication context"""
    from backend.middleware.enhanced_auth import get_current_user_info as enhanced_get_current_user_info
    return enhanced_get_current_user_info()

def logout_user():
    """Enhanced logout function with security cleanup"""
    from backend.middleware.enhanced_auth import logout_user as enhanced_logout_user
    return enhanced_logout_user()

def create_auth_response(user_id: str, remember_me: bool = False):
    """Create enhanced authentication response with security features"""
    from backend.middleware.enhanced_auth import create_auth_response as enhanced_create_auth_response
    return enhanced_create_auth_response(user_id, remember_me) 