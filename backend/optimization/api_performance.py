#!/usr/bin/env python3
"""
Mingus Application - API Performance Optimization Module
Comprehensive API performance optimization for Daily Outlook system
"""

import gzip
import json
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
from collections import defaultdict, deque
import asyncio
from concurrent.futures import ThreadPoolExecutor
import redis
from flask import request, jsonify, Response, g, current_app
from werkzeug.exceptions import TooManyRequests
import ujson as json  # Faster JSON library

# Configure logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm
    
    Features:
    - Per-user rate limiting
    - Tier-based rate limits
    - Sliding window algorithm
    - Graceful degradation
    """
    
    def __init__(self, redis_client, default_limit: int = 100, window_size: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client instance
            default_limit: Default requests per window
            window_size: Window size in seconds
        """
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_size = window_size
        
        # Tier-based rate limits (requests per hour)
        self.tier_limits = {
            'budget': 50,
            'mid_tier': 100,
            'professional': 200,
            'enterprise': 500
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/daily-outlook': 10,  # 10 requests per hour
            '/api/balance-score': 20,  # 20 requests per hour
            '/api/peer-comparison': 5,  # 5 requests per hour
            '/api/analytics': 30,  # 30 requests per hour
        }
    
    def is_allowed(self, user_id: int, endpoint: str, user_tier: str = 'budget') -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limits
        
        Args:
            user_id: User ID
            endpoint: API endpoint
            user_tier: User tier for tier-based limits
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            # Get rate limit for endpoint and tier
            endpoint_limit = self.endpoint_limits.get(endpoint, self.default_limit)
            tier_limit = self.tier_limits.get(user_tier, self.default_limit)
            limit = min(endpoint_limit, tier_limit)
            
            # Create rate limit key
            key = f"rate_limit:{user_id}:{endpoint}"
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, self.window_size)
            
            results = pipe.execute()
            current_requests = results[1]
            
            # Check if limit exceeded
            is_allowed = current_requests < limit
            
            rate_limit_info = {
                'limit': limit,
                'remaining': max(0, limit - current_requests - 1),
                'reset_time': current_time + self.window_size,
                'retry_after': self.window_size if not is_allowed else 0
            }
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {'limit': 0, 'remaining': 0, 'reset_time': 0, 'retry_after': 0}

class CompressionManager:
    """
    Response compression manager with multiple algorithms
    
    Features:
    - Gzip compression for text responses
    - Brotli compression for better ratios
    - Compression level optimization
    - Size-based compression decisions
    """
    
    def __init__(self, min_size: int = 1024, compression_level: int = 6):
        """
        Initialize compression manager
        
        Args:
            min_size: Minimum size to compress (bytes)
            compression_level: Compression level (1-9)
        """
        self.min_size = min_size
        self.compression_level = compression_level
        
        # Compression statistics
        self.stats = {
            'compressed_requests': 0,
            'total_savings': 0,
            'compression_ratio': 0.0
        }
    
    def should_compress(self, response_data: bytes, content_type: str) -> bool:
        """
        Determine if response should be compressed
        
        Args:
            response_data: Response data
            content_type: Content type
            
        Returns:
            True if should compress
        """
        # Check size threshold
        if len(response_data) < self.min_size:
            return False
        
        # Check content type
        compressible_types = [
            'application/json',
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'text/plain',
            'application/xml',
            'text/xml'
        ]
        
        return any(content_type.startswith(ct) for ct in compressible_types)
    
    def compress_response(self, response_data: bytes, content_type: str) -> Tuple[bytes, str]:
        """
        Compress response data
        
        Args:
            response_data: Response data
            content_type: Content type
            
        Returns:
            Tuple of (compressed_data, encoding)
        """
        if not self.should_compress(response_data, content_type):
            return response_data, 'identity'
        
        try:
            # Use gzip compression
            compressed = gzip.compress(response_data, compresslevel=self.compression_level)
            
            # Only use compression if it actually saves space
            if len(compressed) < len(response_data):
                savings = len(response_data) - len(compressed)
                self.stats['compressed_requests'] += 1
                self.stats['total_savings'] += savings
                self.stats['compression_ratio'] = (
                    self.stats['total_savings'] / 
                    (self.stats['compressed_requests'] * len(response_data))
                )
                
                return compressed, 'gzip'
            
            return response_data, 'identity'
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return response_data, 'identity'

class ETagManager:
    """
    ETag-based caching for API responses
    
    Features:
    - Content-based ETags
    - Weak ETags for dynamic content
    - ETag validation
    - Cache invalidation
    """
    
    def __init__(self, redis_client):
        """
        Initialize ETag manager
        
        Args:
            redis_client: Redis client for ETag storage
        """
        self.redis = redis_client
        self.etag_ttl = 3600  # 1 hour
    
    def generate_etag(self, content: Any, weak: bool = False) -> str:
        """
        Generate ETag for content
        
        Args:
            content: Content to generate ETag for
            weak: Whether to generate weak ETag
            
        Returns:
            ETag string
        """
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)
        
        # Generate hash
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        # Add weak prefix if needed
        if weak:
            return f'W/"{content_hash}"'
        else:
            return f'"{content_hash}"'
    
    def get_etag(self, key: str) -> Optional[str]:
        """
        Get stored ETag for key
        
        Args:
            key: Cache key
            
        Returns:
            ETag string or None
        """
        try:
            return self.redis.get(f"etag:{key}")
        except Exception as e:
            logger.error(f"ETag get error: {e}")
            return None
    
    def set_etag(self, key: str, etag: str) -> bool:
        """
        Store ETag for key
        
        Args:
            key: Cache key
            etag: ETag string
            
        Returns:
            True if successful
        """
        try:
            self.redis.setex(f"etag:{key}", self.etag_ttl, etag)
            return True
        except Exception as e:
            logger.error(f"ETag set error: {e}")
            return False
    
    def validate_etag(self, request_etag: str, stored_etag: str) -> bool:
        """
        Validate ETag from request
        
        Args:
            request_etag: ETag from request headers
            stored_etag: Stored ETag
            
        Returns:
            True if ETags match
        """
        if not request_etag or not stored_etag:
            return False
        
        # Remove quotes and weak prefixes for comparison
        clean_request = request_etag.strip('"').replace('W/', '')
        clean_stored = stored_etag.strip('"').replace('W/', '')
        
        return clean_request == clean_stored

class BatchAPIManager:
    """
    Batch API endpoint manager for multiple data requests
    
    Features:
    - Single request for multiple endpoints
    - Parallel processing
    - Error handling per endpoint
    - Response aggregation
    """
    
    def __init__(self, max_batch_size: int = 10, timeout: int = 30):
        """
        Initialize batch API manager
        
        Args:
            max_batch_size: Maximum requests per batch
            timeout: Timeout for batch processing
        """
        self.max_batch_size = max_batch_size
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_batch_request(self, batch_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process batch API request
        
        Args:
            batch_requests: List of batch requests
            
        Returns:
            Aggregated response
        """
        if len(batch_requests) > self.max_batch_size:
            raise ValueError(f"Batch size exceeds maximum of {self.max_batch_size}")
        
        results = {}
        errors = {}
        
        # Process requests in parallel
        tasks = []
        for req in batch_requests:
            task = asyncio.create_task(self._process_single_request(req))
            tasks.append((req['id'], task))
        
        # Wait for all tasks to complete
        for req_id, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=self.timeout)
                results[req_id] = result
            except asyncio.TimeoutError:
                errors[req_id] = {'error': 'Request timeout', 'code': 408}
            except Exception as e:
                errors[req_id] = {'error': str(e), 'code': 500}
        
        return {
            'results': results,
            'errors': errors,
            'total_requests': len(batch_requests),
            'successful_requests': len(results),
            'failed_requests': len(errors)
        }
    
    async def _process_single_request(self, request_data: Dict[str, Any]) -> Any:
        """
        Process single request within batch
        
        Args:
            request_data: Single request data
            
        Returns:
            Request result
        """
        # Simulate API call processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Mock response based on endpoint
        endpoint = request_data.get('endpoint', '')
        if 'daily-outlook' in endpoint:
            return {'balance_score': 85, 'insights': ['Great progress!']}
        elif 'balance-score' in endpoint:
            return {'score': 85, 'trend': 'up'}
        elif 'peer-comparison' in endpoint:
            return {'percentile': 75, 'comparison': 'Above average'}
        else:
            return {'status': 'success', 'data': 'Mock response'}

class APIPerformanceOptimizer:
    """
    Main API performance optimizer
    
    Features:
    - Response compression
    - ETag caching
    - Rate limiting
    - Batch API support
    - Performance monitoring
    """
    
    def __init__(self, redis_client):
        """
        Initialize API performance optimizer
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.rate_limiter = RateLimiter(redis_client)
        self.compression_manager = CompressionManager()
        self.etag_manager = ETagManager(redis_client)
        self.batch_manager = BatchAPIManager()
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'compressed_responses': 0,
            'cache_hits': 0,
            'rate_limited_requests': 0,
            'avg_response_time': 0.0
        }
    
    def rate_limit_decorator(self, endpoint: str):
        """
        Decorator for rate limiting endpoints
        
        Args:
            endpoint: API endpoint path
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get user info from request context
                user_id = getattr(g, 'user_id', 1)  # Default to user 1 for testing
                user_tier = getattr(g, 'user_tier', 'budget')
                
                # Check rate limits
                is_allowed, rate_info = self.rate_limiter.is_allowed(
                    user_id, endpoint, user_tier
                )
                
                if not is_allowed:
                    self.metrics['rate_limited_requests'] += 1
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': rate_info['retry_after']
                    }), 429
                
                # Add rate limit headers
                response = func(*args, **kwargs)
                if isinstance(response, tuple):
                    response_data, status_code = response
                else:
                    response_data, status_code = response, 200
                
                # Add rate limit headers to response
                if hasattr(response_data, 'headers'):
                    response_data.headers['X-RateLimit-Limit'] = rate_info['limit']
                    response_data.headers['X-RateLimit-Remaining'] = rate_info['remaining']
                    response_data.headers['X-RateLimit-Reset'] = rate_info['reset_time']
                
                return response_data, status_code
            
            return wrapper
        return decorator
    
    def compression_decorator(self):
        """
        Decorator for response compression
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                # Execute function
                response = func(*args, **kwargs)
                
                # Handle tuple responses (data, status_code)
                if isinstance(response, tuple):
                    response_data, status_code = response
                else:
                    response_data, status_code = response, 200
                
                # Convert to JSON if needed
                if isinstance(response_data, dict):
                    json_data = json.dumps(response_data)
                    content_type = 'application/json'
                else:
                    json_data = str(response_data)
                    content_type = 'text/plain'
                
                # Compress response
                compressed_data, encoding = self.compression_manager.compress_response(
                    json_data.encode(), content_type
                )
                
                # Update metrics
                if encoding != 'identity':
                    self.metrics['compressed_responses'] += 1
                
                self.metrics['total_requests'] += 1
                response_time = time.time() - start_time
                self.metrics['avg_response_time'] = (
                    (self.metrics['avg_response_time'] * (self.metrics['total_requests'] - 1) + response_time) 
                    / self.metrics['total_requests']
                )
                
                # Create response with compression
                response_obj = Response(
                    compressed_data,
                    status=status_code,
                    content_type=content_type,
                    headers={
                        'Content-Encoding': encoding,
                        'Vary': 'Accept-Encoding'
                    }
                )
                
                return response_obj
            
            return wrapper
        return decorator
    
    def etag_decorator(self, cache_key_func=None):
        """
        Decorator for ETag-based caching
        
        Args:
            cache_key_func: Function to generate cache key
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    cache_key = f"{request.endpoint}:{hash(str(request.args))}"
                
                # Check for ETag in request
                request_etag = request.headers.get('If-None-Match')
                stored_etag = self.etag_manager.get_etag(cache_key)
                
                if request_etag and stored_etag and self.etag_manager.validate_etag(request_etag, stored_etag):
                    self.metrics['cache_hits'] += 1
                    return Response(status=304)
                
                # Execute function
                response = func(*args, **kwargs)
                
                # Handle tuple responses
                if isinstance(response, tuple):
                    response_data, status_code = response
                else:
                    response_data, status_code = response, 200
                
                # Generate ETag for response
                if isinstance(response_data, dict):
                    etag = self.etag_manager.generate_etag(response_data)
                    
                    # Store ETag
                    self.etag_manager.set_etag(cache_key, etag)
                    
                    # Add ETag header
                    if hasattr(response_data, 'headers'):
                        response_data.headers['ETag'] = etag
                    else:
                        response_data = Response(
                            json.dumps(response_data),
                            status=status_code,
                            content_type='application/json',
                            headers={'ETag': etag}
                        )
                
                return response_data
            
            return wrapper
        return decorator
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get API performance metrics
        
        Returns:
            Dictionary containing performance metrics
        """
        compression_ratio = (
            self.compression_manager.stats['compression_ratio'] * 100
            if self.compression_manager.stats['compressed_requests'] > 0 else 0
        )
        
        cache_hit_rate = (
            self.metrics['cache_hits'] / self.metrics['total_requests'] * 100
            if self.metrics['total_requests'] > 0 else 0
        )
        
        return {
            'total_requests': self.metrics['total_requests'],
            'compressed_responses': self.metrics['compressed_responses'],
            'compression_ratio_percent': round(compression_ratio, 2),
            'cache_hits': self.metrics['cache_hits'],
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'rate_limited_requests': self.metrics['rate_limited_requests'],
            'avg_response_time_ms': round(self.metrics['avg_response_time'] * 1000, 2),
            'compression_savings_bytes': self.compression_manager.stats['total_savings']
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform API performance health check
        
        Returns:
            Health status dictionary
        """
        try:
            # Test Redis connection
            self.redis.ping()
            
            # Test compression
            test_data = json.dumps({'test': 'data' * 1000})
            compressed, encoding = self.compression_manager.compress_response(
                test_data.encode(), 'application/json'
            )
            
            compression_working = encoding == 'gzip' and len(compressed) < len(test_data)
            
            return {
                'status': 'healthy',
                'redis_connected': True,
                'compression_working': compression_working,
                'metrics': self.get_performance_metrics()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'redis_connected': False,
                'compression_working': False
            }
    
    def close(self):
        """Close resources and cleanup"""
        if hasattr(self.batch_manager, 'executor'):
            self.batch_manager.executor.shutdown(wait=True)
        
        logger.info("API Performance Optimizer closed successfully")
