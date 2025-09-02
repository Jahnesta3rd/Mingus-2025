"""
Comprehensive Rate Limiting Middleware for Financial Application
Advanced rate limiting with Redis support, multiple strategies, and cultural sensitivity
"""

import time
import logging
import json
import hashlib
from functools import wraps
from typing import Dict, Any, Optional, Tuple, List, Union
from flask import request, jsonify, g, current_app, Response
import redis
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitStrategy:
    """Base class for rate limiting strategies"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    def check_rate_limit(self, identifier: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limit using sliding window algorithm"""
        raise NotImplementedError
    
    def get_remaining_requests(self, identifier: str, limits: Dict[str, Any]) -> int:
        """Get remaining requests for identifier"""
        raise NotImplementedError

class SlidingWindowStrategy(RateLimitStrategy):
    """Sliding window rate limiting implementation"""
    
    def check_rate_limit(self, identifier: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check rate limit using sliding window algorithm
        
        Args:
            identifier: Client identifier
            limits: Rate limit configuration
            
        Returns:
            Dictionary with rate limit information
        """
        try:
            key = f"rate_limit:{identifier}"
            current_time = time.time()
            window_size = limits['window']
            
            # Remove expired entries (older than window_size)
            self.redis_client.zremrangebyscore(key, 0, current_time - window_size)
            
            # Get current request count
            current_requests = self.redis_client.zcard(key)
            
            if current_requests >= limits['requests']:
                # Rate limit exceeded
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    oldest_time = oldest_request[0][1]
                    window_remaining = window_size - (current_time - oldest_time)
                else:
                    window_remaining = window_size
                
                return {
                    'limited': True,
                    'requests_made': current_requests,
                    'limit': limits['requests'],
                    'window_remaining': max(0, window_remaining),
                    'retry_after': max(1, window_remaining)  # Ensure retry_after is at least 1 second
                }
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, window_size)
            
            return {
                'limited': False,
                'requests_made': current_requests + 1,
                'limit': limits['requests'],
                'window_remaining': window_size,
                'remaining_requests': limits['requests'] - (current_requests + 1)
            }
            
        except Exception as e:
            logger.error(f"Sliding window rate limit check error: {e}")
            # Allow request if rate limiting fails
            return {
                'limited': False,
                'requests_made': 0,
                'limit': limits['requests'],
                'window_remaining': limits['window'],
                'remaining_requests': limits['requests']
            }
    
    def get_remaining_requests(self, identifier: str, limits: Dict[str, Any]) -> int:
        """Get remaining requests for identifier"""
        try:
            key = f"rate_limit:{identifier}"
            current_time = time.time()
            window_size = limits['window']
            
            # Remove expired entries
            self.redis_client.zremrangebyscore(key, 0, current_time - window_size)
            
            # Get current count
            current_requests = self.redis_client.zcard(key)
            return max(0, limits['requests'] - current_requests)
            
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return limits['requests']

class ComprehensiveRateLimiter:
    """Comprehensive rate limiting with multiple strategies and cultural sensitivity"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.strategy = SlidingWindowStrategy(redis_client) if redis_client else None
        
        # Rate limit configurations with cultural sensitivity
        self.rate_limits = {
            # Authentication endpoints - protect against brute force
            'login': {
                'requests': 5,
                'window': 900,  # 15 minutes
                'message': 'Too many login attempts. Please wait before trying again.',
                'cultural_message': 'We understand the importance of secure access to your financial information. Please take a moment before your next attempt.'
            },
            'password_reset': {
                'requests': 3,
                'window': 3600,  # 1 hour
                'message': 'Too many password reset attempts. Please wait before trying again.',
                'cultural_message': 'Your security is our priority. Please wait before requesting another password reset.'
            },
            'register': {
                'requests': 5,
                'window': 900,  # 15 minutes
                'message': 'Too many registration attempts. Please wait before trying again.',
                'cultural_message': 'We appreciate your interest in joining our community. Please wait before your next registration attempt.'
            },
            
            # Financial data endpoints - protect sensitive information
            'financial_api': {
                'requests': 100,
                'window': 60,  # 1 minute
                'message': 'Too many financial data requests. Please wait before trying again.',
                'cultural_message': 'We\'re processing your financial data requests. Please wait a moment before your next request.'
            },
            'financial_hourly': {
                'requests': 1000,
                'window': 3600,  # 1 hour
                'message': 'Hourly financial API limit exceeded. Please wait before trying again.',
                'cultural_message': 'We\'ve reached our hourly limit for financial data requests. Please wait before your next request.'
            },
            
            # Payment endpoints - critical security
            'payment': {
                'requests': 10,
                'window': 3600,  # 1 hour
                'message': 'Too many payment requests. Please wait before trying again.',
                'cultural_message': 'We\'re processing your payment requests. Please wait before your next payment attempt.'
            },
            'stripe_webhook': {
                'requests': 200,
                'window': 3600,  # 1 hour
                'message': 'Too many webhook requests. Please wait before trying again.',
                'cultural_message': 'We\'re processing your webhook requests. Please wait before your next attempt.'
            },
            
            # General API endpoints
            'api_general': {
                'requests': 1000,
                'window': 3600,  # 1 hour
                'message': 'Hourly API limit exceeded. Please wait before trying again.',
                'cultural_message': 'We\'ve reached our hourly API limit. Please wait before your next request.'
            },
            'api_per_minute': {
                'requests': 100,
                'window': 60,  # 1 minute
                'message': 'Too many API requests. Please wait before trying again.',
                'cultural_message': 'We\'re processing your requests. Please wait a moment before your next request.'
            },
            
            # Assessment and onboarding endpoints
            'assessment_submit': {
                'requests': 3,
                'window': 300,  # 5 minutes
                'message': 'Too many assessment submissions. Please wait before trying again.',
                'cultural_message': 'We\'re processing your assessment. Please wait before your next submission.'
            },
            'assessment_view': {
                'requests': 20,
                'window': 300,  # 5 minutes
                'message': 'Too many assessment views. Please wait before trying again.',
                'cultural_message': 'We\'re loading your assessment data. Please wait before your next request.'
            }
        }
        
        # Admin and whitelisted IPs
        self.admin_ips = self._load_admin_ips()
        self.whitelisted_ips = self._load_whitelisted_ips()
    
    def _load_admin_ips(self) -> List[str]:
        """Load admin IP addresses from configuration"""
        try:
            admin_ips = current_app.config.get('ADMIN_IPS', [])
            if isinstance(admin_ips, str):
                admin_ips = [ip.strip() for ip in admin_ips.split(',') if ip.strip()]
            return admin_ips
        except Exception:
            return []
    
    def _load_whitelisted_ips(self) -> List[str]:
        """Load whitelisted IP addresses from configuration"""
        try:
            whitelisted_ips = current_app.config.get('WHITELISTED_IPS', [])
            if isinstance(whitelisted_ips, str):
                whitelisted_ips = [ip.strip() for ip in whitelisted_ips.split(',') if ip.strip()]
            return whitelisted_ips
        except Exception:
            return []
    
    def get_identifier(self, request) -> str:
        """Get unique client identifier for rate limiting"""
        try:
            # Check if IP is admin or whitelisted
            ip_address = self._get_client_ip(request)
            if ip_address in self.admin_ips:
                return f"admin:{ip_address}"
            if ip_address in self.whitelisted_ips:
                return f"whitelisted:{ip_address}"
            
            # Use user ID if authenticated, otherwise IP address
            user_id = g.get('user_id')
            if user_id:
                return f"user:{user_id}"
            
            # Fallback to IP address with user agent hash
            user_agent = request.headers.get('User-Agent', 'unknown')[:50]
            return f"ip:{ip_address}:{hash(user_agent) % 1000}"
            
        except Exception as e:
            logger.error(f"Error getting client identifier: {e}")
            return 'unknown'
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address considering proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
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
            # Check if identifier is admin or whitelisted
            if identifier.startswith('admin:') or identifier.startswith('whitelisted:'):
                return {
                    'limited': False,
                    'requests_made': 0,
                    'limit': float('inf'),
                    'window_remaining': float('inf'),
                    'remaining_requests': float('inf'),
                    'bypassed': True
                }
            
            # Get rate limit configuration
            limits = self.rate_limits.get(endpoint_type, self.rate_limits['api_general'])
            
            if self.strategy and self.redis_client:
                return self.strategy.check_rate_limit(identifier, limits)
            else:
                return self._check_memory_rate_limit(identifier, limits)
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return {
                'limited': False,
                'requests_made': 0,
                'limit': 100,
                'window_remaining': 3600,
                'remaining_requests': 100
            }
    
    def _check_memory_rate_limit(self, identifier: str, limits: Dict[str, Any]) -> Dict[str, Any]:
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
            if identifier in cache:
                entry = cache[identifier]
                if current_time <= entry['expires_at']:
                    current_count = entry['count'] + 1
                    entry['count'] = current_count
                    
                    if current_count > limits['requests']:
                        return {
                            'limited': True,
                            'requests_made': current_count,
                            'limit': limits['requests'],
                            'window_remaining': entry['expires_at'] - current_time,
                            'retry_after': entry['expires_at'] - current_time
                        }
                else:
                    current_count = 1
                    cache[identifier] = {
                        'count': current_count,
                        'expires_at': current_time + limits['window']
                    }
            else:
                current_count = 1
                cache[identifier] = {
                    'count': current_count,
                    'expires_at': current_time + limits['window']
                }
            
            return {
                'limited': False,
                'requests_made': current_count,
                'limit': limits['requests'],
                'window_remaining': limits['window'],
                'remaining_requests': limits['requests'] - current_count
            }
            
        except Exception as e:
            logger.error(f"Memory rate limit check error: {e}")
            return {
                'limited': False,
                'requests_made': 0,
                'limit': limits['requests'],
                'window_remaining': limits['window'],
                'remaining_requests': limits['requests']
            }
    
    def log_rate_limit_violation(self, identifier: str, endpoint_type: str, limit_info: Dict):
        """Log rate limit violations for security monitoring"""
        try:
            from backend.monitoring.logging_config import log_security_event
            
            # Get cultural context for logging
            cultural_context = self._get_cultural_context(request)
            
            log_security_event("rate_limit_exceeded", {
                "identifier": identifier,
                "endpoint_type": endpoint_type,
                "requests_made": limit_info['requests_made'],
                "limit": limit_info['limit'],
                "endpoint": request.endpoint,
                "user_agent": request.headers.get('User-Agent'),
                "ip_address": self._get_client_ip(request),
                "method": request.method,
                "path": request.path,
                "cultural_context": cultural_context
            }, g.get('user_id'), self._get_client_ip(request))
            
        except Exception as e:
            logger.error(f"Error logging rate limit violation: {e}")
    
    def _get_cultural_context(self, request) -> Dict[str, Any]:
        """Get cultural context for the request"""
        try:
            # Check for cultural indicators in headers or user agent
            user_agent = request.headers.get('User-Agent', '').lower()
            accept_language = request.headers.get('Accept-Language', '')
            
            cultural_indicators = {
                'african_american_focused': False,
                'financial_professional': False,
                'mobile_user': 'mobile' in user_agent,
                'preferred_language': accept_language.split(',')[0] if accept_language else 'en'
            }
            
            # Check if this is a financial professional (based on endpoint patterns)
            if any(pattern in request.path.lower() for pattern in ['financial', 'payment', 'stripe', 'plaid']):
                cultural_indicators['financial_professional'] = True
            
            # Check if this is an African American focused application
            if any(pattern in request.path.lower() for pattern in ['assessment', 'onboarding', 'career']):
                cultural_indicators['african_american_focused'] = True
            
            return cultural_indicators
            
        except Exception as e:
            logger.error(f"Error getting cultural context: {e}")
            return {}
    
    def get_rate_limit_message(self, endpoint_type: str, cultural: bool = True) -> str:
        """Get culturally appropriate rate limit message"""
        try:
            limits = self.rate_limits.get(endpoint_type, self.rate_limits['api_general'])
            
            if cultural:
                return limits.get('cultural_message', limits['message'])
            else:
                return limits['message']
                
        except Exception as e:
            logger.error(f"Error getting rate limit message: {e}")
            return "Rate limit exceeded. Please wait before trying again."

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> ComprehensiveRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        # Try to get Redis client from app context
        redis_client = None
        try:
            if hasattr(current_app, 'redis_client'):
                redis_client = current_app.redis_client
            elif hasattr(current_app, 'extensions') and 'redis' in current_app.extensions:
                redis_client = current_app.extensions['redis']
        except RuntimeError:
            pass  # Outside app context
        
        _rate_limiter = ComprehensiveRateLimiter(redis_client)
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
                    rate_limiter.rate_limits[endpoint_type] = custom_limits
                
                identifier = rate_limiter.get_identifier(request)
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info['window_remaining'])
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
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

def add_rate_limit_headers(response: Response, limit_info: Dict[str, Any]) -> Response:
    """Add rate limit headers to response"""
    try:
        if not limit_info.get('bypassed', False):
            response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining_requests', 0))
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_info['window_remaining']))
            
            if limit_info.get('limited', False):
                response.headers['Retry-After'] = str(int(limit_info.get('retry_after', 0)))
        
        return response
        
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
                        'message': limiter.get_rate_limit_message(action),
                        'retry_after': int(limit_info['window_remaining'])
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
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
                        'message': limiter.get_rate_limit_message(action),
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
                        'message': limiter.get_rate_limit_message(action),
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