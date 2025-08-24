"""
Rate Limiting Middleware
Comprehensive rate limiting with Redis support and configurable limits
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify, g, current_app
import redis
import json

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with Redis support"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.default_limits = {
            'api': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'auth': {'requests': 10, 'window': 300},   # 10 requests per 5 minutes
            'register': {'requests': 5, 'window': 300}, # 5 requests per 5 minutes
            'login': {'requests': 10, 'window': 300},   # 10 requests per 5 minutes
            'password_reset': {'requests': 3, 'window': 3600}, # 3 requests per hour
            'financial': {'requests': 50, 'window': 3600}, # 50 requests per hour
            'admin': {'requests': 200, 'window': 3600},  # 200 requests per hour
        }
    
    def get_client_identifier(self) -> str:
        """Get unique client identifier for rate limiting"""
        try:
            # Use IP address and user ID if available
            ip_address = request.remote_addr or 'unknown'
            user_id = getattr(g, 'user_id', None) or 'anonymous'
            
            # Add user agent for additional uniqueness
            user_agent = request.headers.get('User-Agent', 'unknown')[:50]
            
            return f"{ip_address}:{user_id}:{hash(user_agent) % 1000}"
            
        except Exception as e:
            logger.error(f"Error getting client identifier: {e}")
            return 'unknown'
    
    def check_rate_limit(self, identifier: str, action: str, 
                        max_requests: Optional[int] = None, 
                        window: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: Client identifier
            action: Rate limit action type
            max_requests: Maximum requests allowed (overrides default)
            window: Time window in seconds (overrides default)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            # Get limits for action
            limits = self.default_limits.get(action, self.default_limits['api'])
            max_req = max_requests or limits['requests']
            time_window = window or limits['window']
            
            # Create rate limit key
            current_time = int(time.time())
            window_start = current_time - (current_time % time_window)
            key = f"rate_limit:{action}:{identifier}:{window_start}"
            
            if self.redis_client:
                return self._check_redis_rate_limit(key, max_req, time_window, current_time)
            else:
                return self._check_memory_rate_limit(key, max_req, time_window, current_time)
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True, {
                'allowed': True,
                'remaining': -1,
                'reset_time': current_time + time_window,
                'limit': max_req
            }
    
    def _check_redis_rate_limit(self, key: str, max_requests: int, 
                               window: int, current_time: int) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Get current count
            pipe.get(key)
            # Increment counter
            pipe.incr(key)
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = int(results[0] or 0) + 1
            
            is_allowed = current_count <= max_requests
            remaining = max(0, max_requests - current_count)
            reset_time = current_time + window
            
            return is_allowed, {
                'allowed': is_allowed,
                'remaining': remaining,
                'reset_time': reset_time,
                'limit': max_requests,
                'current_count': current_count
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            return True, {
                'allowed': True,
                'remaining': -1,
                'reset_time': current_time + window,
                'limit': max_requests
            }
    
    def _check_memory_rate_limit(self, key: str, max_requests: int, 
                                window: int, current_time: int) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory storage (fallback)"""
        try:
            # Use Flask app context for in-memory storage
            if not hasattr(current_app, '_rate_limit_cache'):
                current_app._rate_limit_cache = {}
            
            cache = current_app._rate_limit_cache
            
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
                else:
                    current_count = 1
                    cache[key] = {
                        'count': current_count,
                        'expires_at': current_time + window
                    }
            else:
                current_count = 1
                cache[key] = {
                    'count': current_count,
                    'expires_at': current_time + window
                }
            
            is_allowed = current_count <= max_requests
            remaining = max(0, max_requests - current_count)
            reset_time = current_time + window
            
            return is_allowed, {
                'allowed': is_allowed,
                'remaining': remaining,
                'reset_time': reset_time,
                'limit': max_requests,
                'current_count': current_count
            }
            
        except Exception as e:
            logger.error(f"Memory rate limit check error: {e}")
            return True, {
                'allowed': True,
                'remaining': -1,
                'reset_time': current_time + window,
                'limit': max_requests
            }

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
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
        
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter

def rate_limit(action: str, max_requests: Optional[int] = None, 
               window: Optional[int] = None):
    """
    Rate limiting decorator
    
    Args:
        action: Rate limit action type
        max_requests: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = get_rate_limiter()
                identifier = limiter.get_client_identifier()
                
                is_allowed, rate_info = limiter.check_rate_limit(
                    identifier, action, max_requests, window
                )
                
                if not is_allowed:
                    # Add rate limit headers
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests for {action}',
                        'retry_after': rate_info['reset_time'] - int(time.time()),
                        'limit': rate_info['limit']
                    })
                    
                    response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])
                    response.headers['Retry-After'] = str(rate_info['reset_time'] - int(time.time()))
                    
                    return response, 429
                
                # Add rate limit headers to successful response
                response = f(*args, **kwargs)
                
                # Handle both tuple and response object
                if isinstance(response, tuple):
                    response_obj, status_code = response
                else:
                    response_obj = response
                    status_code = 200
                
                response_obj.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response_obj.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response_obj.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])
                
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
    """
    Rate limiting decorator based on IP address only
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = get_rate_limiter()
                ip_address = request.remote_addr or 'unknown'
                identifier = f"ip:{ip_address}"
                
                is_allowed, rate_info = limiter.check_rate_limit(
                    identifier, action, max_requests, window
                )
                
                if not is_allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests from this IP address',
                        'retry_after': rate_info['reset_time'] - int(time.time())
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"IP rate limiting error: {e}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_user(action: str, max_requests: int, window: int):
    """
    Rate limiting decorator based on user ID
    """
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
                
                is_allowed, rate_info = limiter.check_rate_limit(
                    identifier, action, max_requests, window
                )
                
                if not is_allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests for this user',
                        'retry_after': rate_info['reset_time'] - int(time.time())
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"User rate limiting error: {e}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Rate limit configuration for different endpoints
RATE_LIMIT_CONFIG = {
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
    'communication': {
        'send': {'requests': 20, 'window': 3600},
        'batch': {'requests': 5, 'window': 3600}
    }
} 