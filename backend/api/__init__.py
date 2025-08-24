"""
MINGUS API Package
Comprehensive REST API implementation with authentication, authorization, rate limiting, and validation
"""

from .auth_api import auth_bp
from .user_api import user_bp
from .financial_api import financial_bp
from .communication_api import communication_bp
from .analytics_api import analytics_bp
from .admin_api import admin_bp

__all__ = [
    'auth_bp',
    'user_bp', 
    'financial_bp',
    'communication_bp',
    'analytics_bp',
    'admin_bp'
] 