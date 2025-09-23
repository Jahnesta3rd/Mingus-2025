#!/usr/bin/env python3
"""
Mingus Application - Cache Manager Service
Comprehensive Redis-based caching system for Daily Outlook performance optimization
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import redis
from redis.exceptions import RedisError, ConnectionError
import pickle
import gzip
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy types"""
    DAILY_OUTLOOK = "daily_outlook"
    USER_BALANCE_SCORE = "user_balance_score"
    CONTENT_TEMPLATE = "content_template"
    PEER_COMPARISON = "peer_comparison"
    USER_AGGREGATION = "user_aggregation"
    ANALYTICS_DATA = "analytics_data"

@dataclass
class CacheConfig:
    """Cache configuration for different data types"""
    ttl_seconds: int
    compression: bool = True
    serialize_method: str = "json"  # json, pickle
    warm_on_startup: bool = False
    invalidation_triggers: List[str] = None

class CacheManager:
    """
    Comprehensive Redis-based cache manager for Daily Outlook system
    
    Features:
    - Multi-tier caching with different TTL strategies
    - Smart invalidation based on data dependencies
    - Compression for large data structures
    - Cache warming and pre-computation
    - Performance metrics and monitoring
    - Graceful fallback when Redis is unavailable
    """
    
    # Cache configurations for different data types
    CACHE_CONFIGS = {
        CacheStrategy.DAILY_OUTLOOK: CacheConfig(
            ttl_seconds=86400,  # 24 hours
            compression=True,
            serialize_method="json",
            warm_on_startup=True,
            invalidation_triggers=["user_profile_update", "relationship_status_change"]
        ),
        CacheStrategy.USER_BALANCE_SCORE: CacheConfig(
            ttl_seconds=3600,  # 1 hour
            compression=False,
            serialize_method="json",
            warm_on_startup=False,
            invalidation_triggers=["financial_data_update", "wellness_data_update", "career_data_update", "relationship_data_update"]
        ),
        CacheStrategy.CONTENT_TEMPLATE: CacheConfig(
            ttl_seconds=604800,  # 7 days
            compression=True,
            serialize_method="pickle",
            warm_on_startup=True,
            invalidation_triggers=["template_update"]
        ),
        CacheStrategy.PEER_COMPARISON: CacheConfig(
            ttl_seconds=1800,  # 30 minutes
            compression=True,
            serialize_method="json",
            warm_on_startup=False,
            invalidation_triggers=["user_tier_change", "location_update"]
        ),
        CacheStrategy.USER_AGGREGATION: CacheConfig(
            ttl_seconds=1800,  # 30 minutes
            compression=True,
            serialize_method="json",
            warm_on_startup=False,
            invalidation_triggers=["user_activity_update"]
        ),
        CacheStrategy.ANALYTICS_DATA: CacheConfig(
            ttl_seconds=3600,  # 1 hour
            compression=True,
            serialize_method="pickle",
            warm_on_startup=True,
            invalidation_triggers=["analytics_refresh"]
        )
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 max_connections: int = 20, 
                 socket_timeout: int = 5,
                 retry_on_timeout: bool = True):
        """
        Initialize CacheManager with Redis connection
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum number of connections in pool
            socket_timeout: Socket timeout in seconds
            retry_on_timeout: Whether to retry on timeout
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.retry_on_timeout = retry_on_timeout
        
        # Initialize Redis connection pool
        self.redis_pool = None
        self.redis_client = None
        self._initialize_redis()
        
        # Performance metrics
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'compression_savings': 0,
            'cache_size_bytes': 0
        }
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("CacheManager initialized successfully")
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling"""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=False  # We handle encoding/decoding manually
            )
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis connection failed: {e}. Cache will operate in fallback mode.")
            self.redis_client = None
    
    def _generate_cache_key(self, strategy: CacheStrategy, identifier: str, 
                          additional_params: Dict[str, Any] = None) -> str:
        """
        Generate standardized cache key
        
        Args:
            strategy: Cache strategy type
            identifier: Primary identifier (user_id, template_id, etc.)
            additional_params: Additional parameters for key uniqueness
            
        Returns:
            Standardized cache key
        """
        key_parts = [strategy.value, str(identifier)]
        
        if additional_params:
            # Sort parameters for consistent key generation
            sorted_params = sorted(additional_params.items())
            param_string = "_".join([f"{k}:{v}" for k, v in sorted_params])
            key_parts.append(param_string)
        
        key = ":".join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key) > 250:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"{strategy.value}:{key_hash}"
        
        return key
    
    def _serialize_data(self, data: Any, strategy: CacheStrategy) -> bytes:
        """
        Serialize data based on strategy configuration
        
        Args:
            data: Data to serialize
            strategy: Cache strategy
            
        Returns:
            Serialized data as bytes
        """
        config = self.CACHE_CONFIGS[strategy]
        
        if config.serialize_method == "json":
            serialized = json.dumps(data, default=str).encode('utf-8')
        elif config.serialize_method == "pickle":
            serialized = pickle.dumps(data)
        else:
            raise ValueError(f"Unknown serialize method: {config.serialize_method}")
        
        # Apply compression if configured
        if config.compression and len(serialized) > 1024:  # Only compress if > 1KB
            compressed = gzip.compress(serialized)
            if len(compressed) < len(serialized):
                self.metrics['compression_savings'] += len(serialized) - len(compressed)
                return compressed
        
        return serialized
    
    def _deserialize_data(self, data: bytes, strategy: CacheStrategy) -> Any:
        """
        Deserialize data based on strategy configuration
        
        Args:
            data: Serialized data
            strategy: Cache strategy
            
        Returns:
            Deserialized data
        """
        config = self.CACHE_CONFIGS[strategy]
        
        # Decompress if needed
        try:
            decompressed = gzip.decompress(data)
            data = decompressed
        except (gzip.BadGzipFile, OSError):
            # Data wasn't compressed, use as-is
            pass
        
        if config.serialize_method == "json":
            return json.loads(data.decode('utf-8'))
        elif config.serialize_method == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"Unknown serialize method: {config.serialize_method}")
    
    def get(self, strategy: CacheStrategy, identifier: str, 
            additional_params: Dict[str, Any] = None) -> Optional[Any]:
        """
        Get data from cache
        
        Args:
            strategy: Cache strategy type
            identifier: Primary identifier
            additional_params: Additional parameters for key generation
            
        Returns:
            Cached data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_cache_key(strategy, identifier, additional_params)
            cached_data = self.redis_client.get(key)
            
            if cached_data is None:
                self.metrics['misses'] += 1
                return None
            
            data = self._deserialize_data(cached_data, strategy)
            self.metrics['hits'] += 1
            return data
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.metrics['errors'] += 1
            return None
    
    def set(self, strategy: CacheStrategy, identifier: str, data: Any,
            additional_params: Dict[str, Any] = None, 
            custom_ttl: Optional[int] = None) -> bool:
        """
        Set data in cache
        
        Args:
            strategy: Cache strategy type
            identifier: Primary identifier
            data: Data to cache
            additional_params: Additional parameters for key generation
            custom_ttl: Custom TTL override
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._generate_cache_key(strategy, identifier, additional_params)
            serialized_data = self._serialize_data(data, strategy)
            
            config = self.CACHE_CONFIGS[strategy]
            ttl = custom_ttl if custom_ttl is not None else config.ttl_seconds
            
            self.redis_client.setex(key, ttl, serialized_data)
            
            # Update cache size metric
            self.metrics['cache_size_bytes'] += len(serialized_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.metrics['errors'] += 1
            return False
    
    def delete(self, strategy: CacheStrategy, identifier: str,
               additional_params: Dict[str, Any] = None) -> bool:
        """
        Delete data from cache
        
        Args:
            strategy: Cache strategy type
            identifier: Primary identifier
            additional_params: Additional parameters for key generation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._generate_cache_key(strategy, identifier, additional_params)
            result = self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.metrics['errors'] += 1
            return False
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern
        
        Args:
            pattern: Redis key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for pattern {pattern}: {e}")
            self.metrics['errors'] += 1
            return 0
    
    def invalidate_user_data(self, user_id: int, trigger: str = None):
        """
        Invalidate all cache entries for a specific user
        
        Args:
            user_id: User ID to invalidate
            trigger: Invalidation trigger (optional)
        """
        patterns = [
            f"daily_outlook:{user_id}:*",
            f"user_balance_score:{user_id}:*",
            f"user_aggregation:{user_id}:*",
            f"peer_comparison:*:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.invalidate_by_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id} (trigger: {trigger})")
        return total_deleted
    
    def warm_cache(self, strategy: CacheStrategy, warm_function: callable, 
                   identifiers: List[str], **kwargs) -> Dict[str, bool]:
        """
        Warm cache with pre-computed data
        
        Args:
            strategy: Cache strategy type
            warm_function: Function to generate data for warming
            identifiers: List of identifiers to warm
            **kwargs: Additional arguments for warm_function
            
        Returns:
            Dictionary mapping identifiers to success status
        """
        results = {}
        
        for identifier in identifiers:
            try:
                # Generate data using warm function
                data = warm_function(identifier, **kwargs)
                
                # Cache the data
                success = self.set(strategy, identifier, data)
                results[identifier] = success
                
            except Exception as e:
                logger.error(f"Cache warming error for {identifier}: {e}")
                results[identifier] = False
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics
        
        Returns:
            Dictionary containing cache metrics
        """
        total_requests = self.metrics['hits'] + self.metrics['misses']
        hit_rate = (self.metrics['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.metrics['hits'],
            'misses': self.metrics['misses'],
            'errors': self.metrics['errors'],
            'hit_rate_percent': round(hit_rate, 2),
            'compression_savings_bytes': self.metrics['compression_savings'],
            'cache_size_bytes': self.metrics['cache_size_bytes'],
            'redis_connected': self.redis_client is not None
        }
    
    def clear_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'compression_savings': 0,
            'cache_size_bytes': 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check
        
        Returns:
            Health status dictionary
        """
        if not self.redis_client:
            return {
                'status': 'unhealthy',
                'redis_connected': False,
                'error': 'Redis connection not available'
            }
        
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            
            # Test set
            self.redis_client.setex(test_key, 10, json.dumps(test_data).encode())
            
            # Test get
            retrieved = self.redis_client.get(test_key)
            if retrieved:
                parsed = json.loads(retrieved.decode())
                if parsed.get("test"):
                    # Test delete
                    self.redis_client.delete(test_key)
                    
                    return {
                        'status': 'healthy',
                        'redis_connected': True,
                        'metrics': self.get_metrics()
                    }
            
            return {
                'status': 'unhealthy',
                'redis_connected': True,
                'error': 'Basic operations failed'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'redis_connected': True,
                'error': str(e)
            }
    
    def close(self):
        """Close Redis connections and cleanup resources"""
        if self.redis_pool:
            self.redis_pool.disconnect()
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("CacheManager closed successfully")


# Decorator for automatic caching
def cached(strategy: CacheStrategy, ttl_override: Optional[int] = None):
    """
    Decorator for automatic method result caching
    
    Args:
        strategy: Cache strategy to use
        ttl_override: Custom TTL override
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cache_manager = getattr(self, 'cache_manager', None)
            if cache_manager:
                cached_result = cache_manager.get(strategy, cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            
            if cache_manager:
                cache_manager.set(strategy, cache_key, result, custom_ttl=ttl_override)
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()

# Export commonly used functions
def get_daily_outlook_cache(user_id: int, date: str) -> Optional[Dict[str, Any]]:
    """Get cached daily outlook for user and date"""
    return cache_manager.get(CacheStrategy.DAILY_OUTLOOK, str(user_id), {"date": date})

def set_daily_outlook_cache(user_id: int, date: str, data: Dict[str, Any]) -> bool:
    """Cache daily outlook for user and date"""
    return cache_manager.set(CacheStrategy.DAILY_OUTLOOK, str(user_id), data, {"date": date})

def get_user_balance_score_cache(user_id: int) -> Optional[Dict[str, Any]]:
    """Get cached user balance score"""
    return cache_manager.get(CacheStrategy.USER_BALANCE_SCORE, str(user_id))

def set_user_balance_score_cache(user_id: int, data: Dict[str, Any]) -> bool:
    """Cache user balance score"""
    return cache_manager.set(CacheStrategy.USER_BALANCE_SCORE, str(user_id), data)

def invalidate_user_cache(user_id: int, trigger: str = None):
    """Invalidate all cache entries for a user"""
    return cache_manager.invalidate_user_data(user_id, trigger)
