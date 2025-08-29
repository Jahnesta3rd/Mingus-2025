"""
Advanced Rate Limiting Middleware
Comprehensive rate limiting with Redis support, configurable limits, and security monitoring
"""

import time
import logging
import json
from functools import wraps
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify, g, current_app
import redis
import re

logger = logging.getLogger(__name__)

class AdvancedRateLimiter:
    """Advanced rate limiting implementation with Redis support and comprehensive monitoring"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.default_limits = {
            'assessment_submit': {'requests': 3, 'window': 300},   # 3 per 5 minutes
            'assessment_view': {'requests': 20, 'window': 300},    # 20 per 5 minutes
            'api_general': {'requests': 100, 'window': 3600},      # 100 per hour
            'auth': {'requests': 10, 'window': 300},              # 10 per 5 minutes
            'register': {'requests': 5, 'window': 300},           # 5 per 5 minutes
            'login': {'requests': 10, 'window': 300},             # 10 per 5 minutes
            'password_reset': {'requests': 3, 'window': 3600},    # 3 per hour
            'financial': {'requests': 50, 'window': 3600},        # 50 per hour
            'admin': {'requests': 200, 'window': 3600},           # 200 per hour
            'meme_upload': {'requests': 10, 'window': 3600},      # 10 per hour
            'meme_view': {'requests': 100, 'window': 3600},       # 100 per hour
            'analytics': {'requests': 30, 'window': 3600},        # 30 per hour
            'communication': {'requests': 20, 'window': 3600},    # 20 per hour
            'webhook': {'requests': 100, 'window': 3600},         # 100 per hour
        }
    
    def get_identifier(self, request) -> str:
        """Get unique client identifier for rate limiting"""
        try:
            # Use user ID if authenticated, otherwise IP address
            user_id = g.get('user_id')
            if user_id:
                return f"user:{user_id}"
            
            # Fallback to IP address with user agent hash
            ip_address = request.remote_addr or 'unknown'
            user_agent = request.headers.get('User-Agent', 'unknown')[:50]
            return f"ip:{ip_address}:{hash(user_agent) % 1000}"
            
        except Exception as e:
            logger.error(f"Error getting client identifier: {e}")
            return 'unknown'
    
    def is_rate_limited(self, identifier: str, endpoint_type: str) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: Client identifier
            endpoint_type: Rate limit endpoint type
            
        Returns:
            Dictionary with rate limit information
        """
        try:
            limits = self.default_limits.get(endpoint_type, self.default_limits['api_general'])
            key = f"rate_limit:{endpoint_type}:{identifier}"
            
            if self.redis_client:
                return self._check_redis_rate_limit(key, limits)
            else:
                return self._check_memory_rate_limit(key, limits)
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return {
                'limited': False,
                'requests_made': 0,
                'limit': limits['requests'],
                'window_remaining': limits['window']
            }
    
    def _check_redis_rate_limit(self, key: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limit using Redis"""
        try:
            # Get current usage
            current_usage = self.redis_client.get(key)
            if current_usage:
                usage_data = json.loads(current_usage)
                requests_made = usage_data['requests']
                window_start = usage_data['window_start']
                
                # Check if we're still in the same window
                if time.time() - window_start < limits['window']:
                    if requests_made >= limits['requests']:
                        return {
                            'limited': True,
                            'requests_made': requests_made,
                            'limit': limits['requests'],
                            'window_remaining': limits['window'] - (time.time() - window_start)
                        }
                    
                    # Increment counter
                    usage_data['requests'] += 1
                    self.redis_client.setex(key, limits['window'], json.dumps(usage_data))
                    
                    return {
                        'limited': False,
                        'requests_made': usage_data['requests'],
                        'limit': limits['requests'],
                        'window_remaining': limits['window'] - (time.time() - window_start)
                    }
            
            # First request in new window
            usage_data = {
                'requests': 1,
                'window_start': time.time()
            }
            self.redis_client.setex(key, limits['window'], json.dumps(usage_data))
            
            return {
                'limited': False,
                'requests_made': 1,
                'limit': limits['requests'],
                'window_remaining': limits['window']
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            return {
                'limited': False,
                'requests_made': 0,
                'limit': limits['requests'],
                'window_remaining': limits['window']
            }
    
    def _check_memory_rate_limit(self, key: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limit using in-memory storage (fallback)"""
        try:
            # Use Flask app context for in-memory storage
            if not hasattr(current_app, '_rate_limit_cache'):
                current_app._rate_limit_cache = {}
            
            cache = current_app._rate_limit_cache
            current_time = time.time()
            
            # Clean expired entries
            expired_keys = [k for k, v in cache.items() 
                          if current_time > v['expires_at']]
            for k in expired_keys:
                del cache[k]
            
            # Check current count
            if key in cache:
                entry = cache[key]
                if current_time <= entry['expires_at']:
                    current_count = entry['count'] + 1
                    entry['count'] = current_count
                    
                    if current_count > limits['requests']:
                        return {
                            'limited': True,
                            'requests_made': current_count,
                            'limit': limits['requests'],
                            'window_remaining': entry['expires_at'] - current_time
                        }
                else:
                    current_count = 1
                    cache[key] = {
                        'count': current_count,
                        'expires_at': current_time + limits['window']
                    }
            else:
                current_count = 1
                cache[key] = {
                    'count': current_count,
                    'expires_at': current_time + limits['window']
                }
            
            return {
                'limited': False,
                'requests_made': current_count,
                'limit': limits['requests'],
                'window_remaining': limits['window']
            }
            
        except Exception as e:
            logger.error(f"Memory rate limit check error: {e}")
            return {
                'limited': False,
                'requests_made': 0,
                'limit': limits['requests'],
                'window_remaining': limits['window']
            }
    
    def log_rate_limit_violation(self, identifier: str, endpoint_type: str, limit_info: Dict):
        """Log rate limit violations for security monitoring"""
        try:
            from backend.monitoring.logging_config import log_security_event
            
            log_security_event("rate_limit_exceeded", {
                "identifier": identifier,
                "endpoint_type": endpoint_type,
                "requests_made": limit_info['requests_made'],
                "limit": limit_info['limit'],
                "endpoint": request.endpoint,
                "user_agent": request.headers.get('User-Agent'),
                "ip_address": request.remote_addr,
                "method": request.method,
                "path": request.path
            }, g.get('user_id'), request.remote_addr)
            
        except Exception as e:
            logger.error(f"Error logging rate limit violation: {e}")

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> AdvancedRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        # Try to get Redis client from app context
        redis_client = None
        try:
            if hasattr(current_app, 'redis_client'):
                redis_client = current_app.redis_client
        except RuntimeError:
            pass  # Outside app context
        
        _rate_limiter = AdvancedRateLimiter(redis_client)
    return _rate_limiter

def rate_limited(endpoint_type: str, custom_limits: Optional[Dict] = None):
    """
    Advanced rate limiting decorator
    
    Args:
        endpoint_type: Rate limit endpoint type
        custom_limits: Custom limits to override defaults
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Override default limits if provided
                if custom_limits:
                    rate_limiter.default_limits[endpoint_type] = custom_limits
                
                identifier = rate_limiter.get_identifier(request)
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests for {endpoint_type}",
                        "retry_after": int(limit_info['window_remaining'])
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(int(limit_info['window_remaining']))
                    response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_info['window_remaining']))
                    
                    return response
                
                # Add rate limit headers to successful responses
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    try:
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['limit'] - info['requests_made'])
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + info['window_remaining']))
    except Exception as e:
        logger.error(f"Error adding rate limit headers: {e}")
    
    return response

# Legacy decorators for backward compatibility
def rate_limit(action: str, max_requests: Optional[int] = None, 
               window: Optional[int] = None):
    """Legacy rate limiting decorator for backward compatibility"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = get_rate_limiter()
                identifier = limiter.get_identifier(request)
                
                # Use custom limits if provided
                custom_limits = None
                if max_requests and window:
                    custom_limits = {'requests': max_requests, 'window': window}
                
                limit_info = limiter.is_rate_limited(identifier, action)
                
                if limit_info['limited']:
                    limiter.log_rate_limit_violation(identifier, action, limit_info)
                    
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests for {action}',
                        'retry_after': int(limit_info['window_remaining'])
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(int(limit_info['window_remaining']))
                    response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_info['window_remaining']))
                    
                    return response
                
                # Add rate limit headers to successful response
                response = f(*args, **kwargs)
                
                # Handle both tuple and response object
                if isinstance(response, tuple):
                    response_obj, status_code = response
                else:
                    response_obj = response
                    status_code = 200
                
                response_obj.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                response_obj.headers['X-RateLimit-Remaining'] = str(limit_info['limit'] - limit_info['requests_made'])
                response_obj.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_info['window_remaining']))
                
                if isinstance(response, tuple):
                    return response_obj, status_code
                else:
                    return response_obj
                    
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_ip(action: str, max_requests: int, window: int):
    """Rate limiting decorator based on IP address only"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = get_rate_limiter()
                ip_address = request.remote_addr or 'unknown'
                identifier = f"ip:{ip_address}"
                
                custom_limits = {'requests': max_requests, 'window': window}
                limit_info = limiter.is_rate_limited(identifier, action)
                
                if limit_info['limited']:
                    limiter.log_rate_limit_violation(identifier, action, limit_info)
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests from this IP address',
                        'retry_after': int(limit_info['window_remaining'])
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"IP rate limiting error: {e}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_user(action: str, max_requests: int, window: int):
    """Rate limiting decorator based on user ID"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = get_rate_limiter()
                user_id = getattr(g, 'user_id', None)
                
                if not user_id:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'User authentication required for rate limiting'
                    }), 401
                
                identifier = f"user:{user_id}"
                custom_limits = {'requests': max_requests, 'window': window}
                limit_info = limiter.is_rate_limited(identifier, action)
                
                if limit_info['limited']:
                    limiter.log_rate_limit_violation(identifier, action, limit_info)
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests for this user',
                        'retry_after': int(limit_info['window_remaining'])
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"User rate limiting error: {e}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Rate limit configuration for different endpoints
RATE_LIMIT_CONFIG = {
    'assessment': {
        'submit': {'requests': 3, 'window': 300},
        'view': {'requests': 20, 'window': 300},
        'analytics': {'requests': 10, 'window': 300}
    },
    'auth': {
        'register': {'requests': 5, 'window': 300},
        'login': {'requests': 10, 'window': 300},
        'password_reset': {'requests': 3, 'window': 3600},
        'refresh': {'requests': 20, 'window': 300}
    },
    'api': {
        'general': {'requests': 100, 'window': 3600},
        'financial': {'requests': 50, 'window': 3600},
        'analytics': {'requests': 30, 'window': 3600},
        'admin': {'requests': 200, 'window': 3600}
    },
    'meme': {
        'upload': {'requests': 10, 'window': 3600},
        'view': {'requests': 100, 'window': 3600},
        'analytics': {'requests': 20, 'window': 3600}
    },
    'communication': {
        'send': {'requests': 20, 'window': 3600},
        'batch': {'requests': 5, 'window': 3600}
    },
    'webhook': {
        'general': {'requests': 100, 'window': 3600},
        'plaid': {'requests': 200, 'window': 3600},
        'stripe': {'requests': 200, 'window': 3600}
    }
} 