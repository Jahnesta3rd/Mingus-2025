#!/usr/bin/env python3
"""
Query Cache Manager - Redis-based query result caching
Caches database query results to reduce database load
"""

import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
import redis
from datetime import timedelta

logger = logging.getLogger(__name__)

class QueryCacheManager:
    """
    Redis-based query result caching manager
    
    Features:
    - Automatic cache key generation
    - TTL-based expiration
    - Cache invalidation patterns
    - Performance metrics
    """
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 300):
        """
        Initialize query cache manager
        
        Args:
            redis_client: Redis client instance
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = "query_cache:"
        
        # Metrics
        self.hits = 0
        self.misses = 0
    
    def _generate_cache_key(self, query_str: str, params: dict = None) -> str:
        """
        Generate cache key from query and parameters
        
        Args:
            query_str: SQL query string or function identifier
            params: Query parameters
            
        Returns:
            Cache key string
        """
        # Normalize query string (remove whitespace)
        normalized_query = ' '.join(query_str.split())
        
        # Create cache data string
        cache_data = f"{normalized_query}:{json.dumps(params or {}, sort_keys=True)}"
        
        # Generate hash
        cache_hash = hashlib.sha256(cache_data.encode()).hexdigest()
        
        return f"{self.cache_prefix}{cache_hash}"
    
    def get_cached_result(self, query_str: str, params: dict = None) -> Optional[Any]:
        """
        Get cached query result
        
        Args:
            query_str: SQL query string or function identifier
            params: Query parameters
            
        Returns:
            Cached result or None if not found
        """
        try:
            cache_key = self._generate_cache_key(query_str, params)
            cached = self.redis.get(cache_key)
            
            if cached:
                self.hits += 1
                logger.debug(f"Cache HIT for query: {query_str[:100]}")
                return json.loads(cached)
            else:
                self.misses += 1
                logger.debug(f"Cache MISS for query: {query_str[:100]}")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Error decoding cached result: {e}")
            self.misses += 1
            return None
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            self.misses += 1
            return None
    
    def set_cached_result(
        self, 
        query_str: str, 
        result: Any, 
        params: dict = None,
        ttl: int = None
    ):
        """
        Cache query result
        
        Args:
            query_str: SQL query string or function identifier
            result: Query result to cache
            params: Query parameters
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        try:
            cache_key = self._generate_cache_key(query_str, params)
            ttl = ttl or self.default_ttl
            
            # Serialize result
            serialized = json.dumps(result, default=str)
            
            # Cache with TTL
            self.redis.setex(cache_key, ttl, serialized)
            
            logger.debug(f"Cached query result (TTL: {ttl}s): {query_str[:100]}")
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Error serializing result for cache: {e}")
        except Exception as e:
            logger.error(f"Error caching result: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Pattern to match (e.g., 'user_profile:*')
        """
        try:
            full_pattern = f"{self.cache_prefix}*{pattern}*"
            keys = self.redis.keys(full_pattern)
            
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
            else:
                logger.debug(f"No cache entries found matching pattern: {pattern}")
                
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {e}")
    
    def invalidate_by_key(self, cache_key: str):
        """Invalidate specific cache key"""
        try:
            full_key = f"{self.cache_prefix}{cache_key}" if not cache_key.startswith(self.cache_prefix) else cache_key
            self.redis.delete(full_key)
            logger.debug(f"Invalidated cache key: {cache_key}")
        except Exception as e:
            logger.error(f"Error invalidating cache key: {e}")
    
    def clear_all(self):
        """Clear all query cache entries"""
        try:
            keys = self.redis.keys(f"{self.cache_prefix}*")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries")
            else:
                logger.info("No cache entries to clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'hit_rate': round(hit_rate, 2)
        }


def cache_query(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results (typically database queries)
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        
    Usage:
        @cache_query(ttl=600, key_prefix='user_profile')
        def get_user_profile(user_id):
            return db.session.query(User).filter_by(id=user_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from flask import current_app
                cache_manager = getattr(current_app, 'query_cache_manager', None)
                
                if not cache_manager:
                    logger.warning("QueryCacheManager not available, skipping cache")
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key_data = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_hash = hashlib.sha256(cache_key_data.encode()).hexdigest()
                full_key = f"query_cache:{cache_hash}"
                
                # Try to get from cache
                try:
                    cached = cache_manager.redis.get(full_key)
                    if cached:
                        logger.debug(f"Cache HIT for {func.__name__}")
                        return json.loads(cached)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                try:
                    serialized = json.dumps(result, default=str)
                    cache_manager.redis.setex(full_key, ttl, serialized)
                    logger.debug(f"Cached result for {func.__name__} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in cache_query decorator: {e}")
                # Fallback to executing function without cache
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
