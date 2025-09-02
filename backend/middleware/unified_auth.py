#!/usr/bin/env python3
"""
Unified Authentication Middleware for MINGUS Assessment System
Secure JWT-based authentication with comprehensive security features
"""

import logging
from functools import wraps
from flask import request, jsonify, current_app, g
from typing import Optional, Dict, Any
import jwt
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UnifiedAuthMiddleware:
    """Unified JWT-based authentication middleware"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        self.secret_key = app.config.get('JWT_SECRET_KEY')
        self.algorithm = app.config.get('JWT_ALGORITHM', 'HS256')
        self.access_token_expiry = app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)  # 1 hour
        self.refresh_token_expiry = app.config.get('JWT_REFRESH_TOKEN_EXPIRES', 604800)  # 7 days
        self.token_rotation_threshold = app.config.get('JWT_TOKEN_ROTATION_THRESHOLD', 300)  # 5 minutes
        
        # Blacklisted tokens (in production, use Redis)
        self.blacklisted_tokens = set()
        
        # User session tracking
        self.user_sessions = {}  # user_id -> {session_id: last_activity}
        self.max_concurrent_sessions = app.config.get('MAX_CONCURRENT_SESSIONS', 3)
    
    def create_access_token(self, user_id: str, subscription_tier: str = 'free') -> str:
        """Create a secure access token"""
        payload = {
            'sub': user_id,
            'tier': subscription_tier,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.access_token_expiry),
            'jti': self._generate_token_id()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a secure refresh token"""
        payload = {
            'sub': user_id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry),
            'jti': self._generate_token_id()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload"""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                return {'valid': False, 'reason': 'Token blacklisted'}
            
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Validate token type
            if payload.get('type') != 'access':
                return {'valid': False, 'reason': 'Invalid token type'}
            
            # Check if token needs rotation
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp)
                time_until_expiry = (exp_time - datetime.utcnow()).total_seconds()
                
                if time_until_expiry < self.token_rotation_threshold:
                    return {
                        'valid': True, 
                        'payload': payload, 
                        'rotation_needed': True
                    }
            
            return {'valid': True, 'payload': payload}
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'reason': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'reason': f'Invalid token: {str(e)}'}
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {'valid': False, 'reason': 'Token validation failed'}
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get('type') != 'refresh':
                return None
            
            user_id = payload.get('sub')
            if not user_id:
                return None
            
            # Create new access token
            return self.create_access_token(user_id)
            
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str):
        """Revoke/blacklist a token"""
        self.blacklisted_tokens.add(token)
    
    def revoke_user_sessions(self, user_id: str):
        """Revoke all sessions for a user"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
    
    def track_user_session(self, user_id: str, session_id: str):
        """Track user session for concurrent session management"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        # Remove old sessions if exceeding limit
        if len(self.user_sessions[user_id]) >= self.max_concurrent_sessions:
            oldest_session = min(self.user_sessions[user_id].keys(), 
                               key=lambda k: self.user_sessions[user_id][k])
            del self.user_sessions[user_id][oldest_session]
        
        self.user_sessions[user_id][session_id] = time.time()
    
    def _generate_token_id(self) -> str:
        """Generate unique token ID"""
        import secrets
        return secrets.token_urlsafe(32)

# Global middleware instance
auth_middleware = UnifiedAuthMiddleware()

def require_auth(f):
    """Unified authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization header required"}), 401
            
            token = auth_header[7:]
            
            # Validate token
            validation_result = auth_middleware.validate_token(token)
            
            if not validation_result['valid']:
                return jsonify({"error": validation_result['reason']}), 401
            
            payload = validation_result['payload']
            user_id = payload.get('sub')
            
            # Set user context
            g.current_user_id = user_id
            g.auth_method = 'jwt'
            g.token_payload = payload
            g.subscription_tier = payload.get('tier', 'free')
            
            # Check if token rotation is needed
            if validation_result.get('rotation_needed'):
                new_token = auth_middleware.create_access_token(
                    user_id, 
                    payload.get('tier', 'free')
                )
                g.new_token = new_token
            
            logger.debug(f"JWT authentication successful for user {user_id}")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated

def require_subscription_tier(minimum_tier: str):
    """Decorator to require minimum subscription tier"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # First require authentication
            auth_result = require_auth(lambda: None)()
            if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
                return auth_result
            
            # Check subscription tier
            current_tier = getattr(g, 'subscription_tier', 'free')
            tier_hierarchy = ['free', 'basic', 'premium', 'enterprise']
            
            current_index = tier_hierarchy.index(current_tier) if current_tier in tier_hierarchy else -1
            required_index = tier_hierarchy.index(minimum_tier) if minimum_tier in tier_hierarchy else 0
            
            if current_index < required_index:
                return jsonify({
                    "error": "Insufficient subscription tier",
                    "required_tier": minimum_tier,
                    "current_tier": current_tier
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def get_current_user_id() -> Optional[str]:
    """Get current user ID from request context"""
    return getattr(g, 'current_user_id', None)

def get_current_user_tier() -> str:
    """Get current user subscription tier"""
    return getattr(g, 'subscription_tier', 'free')

def logout_user():
    """Logout user and revoke tokens"""
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_middleware.revoke_token(token)
        
        # Clear Flask context
        if hasattr(g, 'current_user_id'):
            user_id = g.current_user_id
            auth_middleware.revoke_user_sessions(user_id)
            del g.current_user_id
        
        if hasattr(g, 'auth_method'):
            del g.auth_method
        if hasattr(g, 'token_payload'):
            del g.token_payload
        if hasattr(g, 'subscription_tier'):
            del g.subscription_tier
        
        logger.info(f"User logged out successfully")
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")

def create_auth_response(user_id: str, subscription_tier: str = 'free', remember_me: bool = False) -> Dict[str, Any]:
    """Create unified authentication response"""
    try:
        # Create tokens
        access_token = auth_middleware.create_access_token(user_id, subscription_tier)
        refresh_token = auth_middleware.create_refresh_token(user_id)
        
        # Track session
        session_id = auth_middleware._generate_token_id()
        auth_middleware.track_user_session(user_id, session_id)
        
        response_data = {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': auth_middleware.access_token_expiry,
            'user_id': user_id,
            'subscription_tier': subscription_tier
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error creating auth response: {str(e)}")
        raise
