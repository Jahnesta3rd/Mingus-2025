#!/usr/bin/env python3
"""
Authentication decorators for Mingus application
JWT-based authentication with proper error handling and security
"""

import jwt
import os
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

def require_auth(f):
    """
    Decorator to require JWT authentication for protected routes
    Extracts user information from JWT token and stores in Flask g object
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Missing or invalid Authorization header'
                }), 401
            
            # Extract token
            token = auth_header.split(' ')[1]
            
            # Decode and validate JWT token
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                
                # Check token expiration
                if 'exp' in payload:
                    exp_timestamp = payload['exp']
                    if datetime.utcnow().timestamp() > exp_timestamp:
                        return jsonify({
                            'error': 'Token expired',
                            'message': 'Please refresh your authentication token'
                        }), 401
                
                # Store user information in Flask g object
                g.current_user_id = payload.get('user_id')
                g.current_user_email = payload.get('email')
                g.token_payload = payload
                
                logger.debug(f"Authenticated user: {g.current_user_id}")
                
            except jwt.ExpiredSignatureError:
                return jsonify({
                    'error': 'Token expired',
                    'message': 'Please refresh your authentication token'
                }), 401
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Authentication token is malformed or invalid'
                }), 401
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'An error occurred during authentication'
            }), 500
    
    return decorated_function

def require_csrf(f):
    """
    Decorator to require CSRF token for state-changing operations
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET requests
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # Check for CSRF token in headers or form data
        csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        
        if not csrf_token:
            return jsonify({
                'error': 'CSRF token required',
                'message': 'X-CSRF-Token header is required for this operation'
            }), 403
        
        # Validate CSRF token (simplified for now)
        if not validate_csrf_token(csrf_token):
            return jsonify({
                'error': 'Invalid CSRF token',
                'message': 'CSRF token validation failed'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_csrf_token(token: str) -> bool:
    """
    Validate CSRF token
    In production, implement proper CSRF token validation with secret key
    """
    if not token:
        return False
    
    # For development/testing, accept 'test-token'
    if token == 'test-token':
        return True
    
    # In production, implement proper CSRF token validation
    # This should use a secret key and time-based validation
    expected_token = os.environ.get('CSRF_SECRET_KEY', 'default-csrf-secret')
    return token == expected_token

def require_admin(f):
    """
    Decorator to require admin privileges
    Must be used after @require_auth
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'token_payload'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'Admin access requires authentication'
            }), 401
        
        # Check if user has admin role
        user_role = g.token_payload.get('role', 'user')
        if user_role != 'admin':
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Admin access required for this operation'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_user_access(user_id: int) -> bool:
    """
    Validate that the authenticated user can access the specified user_id
    """
    if not hasattr(g, 'current_user_id'):
        return False
    
    # Users can only access their own data
    return g.current_user_id == user_id

def get_current_user_id() -> int:
    """
    Get the current authenticated user ID
    """
    return getattr(g, 'current_user_id', None)

def get_current_user_email() -> str:
    """
    Get the current authenticated user email
    """
    return getattr(g, 'current_user_email', None)

def require_housing_feature(feature_name: str):
    """
    Decorator to require specific housing feature access
    Must be used after @require_auth
    
    Args:
        feature_name: Name of the housing feature to check (e.g., 'career_integration')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user_id'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Housing feature access requires authentication'
                }), 401
            
            user_id = g.current_user_id
            
            # Import here to avoid circular imports
            from backend.services.feature_flag_service import feature_flag_service
            
            # Check if user has access to optimal location features
            if not feature_flag_service.has_feature_access(user_id, feature_flag_service.FeatureFlag.OPTIMAL_LOCATION):
                return jsonify({
                    'error': 'Feature not available',
                    'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                    'upgrade_required': True,
                    'required_tier': 'mid_tier'
                }), 403
            
            # Check specific housing subfeature
            if not feature_flag_service.has_optimal_location_feature(user_id, feature_name):
                return jsonify({
                    'error': 'Feature not available',
                    'message': f'{feature_name.replace("_", " ").title()} feature is not available in your current tier.',
                    'upgrade_required': True,
                    'feature_name': feature_name
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_housing_searches():
    """
    Decorator to rate limit housing searches based on user tier
    Must be used after @require_auth
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user_id'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Rate limiting requires authentication'
                }), 401
            
            user_id = g.current_user_id
            
            # Import here to avoid circular imports
            from backend.services.feature_flag_service import feature_flag_service
            from backend.models.housing_models import HousingSearch
            from datetime import datetime, timedelta
            
            # Check if user has access to optimal location features
            if not feature_flag_service.has_feature_access(user_id, feature_flag_service.FeatureFlag.OPTIMAL_LOCATION):
                return jsonify({
                    'error': 'Feature not available',
                    'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                    'upgrade_required': True,
                    'required_tier': 'mid_tier'
                }), 403
            
            # Count searches this month
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            searches_this_month = HousingSearch.query.filter(
                HousingSearch.user_id == user_id,
                HousingSearch.created_at >= current_month
            ).count()
            
            # Check search limit
            if not feature_flag_service.check_housing_search_limit(user_id, searches_this_month):
                features = feature_flag_service.get_optimal_location_features(user_id)
                limit = features.get('housing_searches_per_month', 0)
                
                return jsonify({
                    'error': 'Search limit exceeded',
                    'message': f'You have reached your monthly limit of {limit} housing searches. Upgrade to Mid-tier for unlimited searches.',
                    'upgrade_required': True,
                    'current_limit': limit,
                    'searches_used': searches_this_month
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
