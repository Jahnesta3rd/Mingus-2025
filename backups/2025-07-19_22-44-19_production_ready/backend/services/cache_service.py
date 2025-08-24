"""
Cache Service for Enhanced Job Recommendations
Manages caching strategies and performance optimization
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from loguru import logger
import redis
import os

class CacheService:
    """Service for managing caching strategies"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.default_ttl = 3600  # 1 hour
        
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Cache service connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory storage.")
            self.redis_client = None
            self._memory_storage = {}
            self._memory_stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
                return default
            else:
                if key in self._memory_storage:
                    item = self._memory_storage[key]
                    if datetime.utcnow() < item['expires_at']:
                        self._memory_stats['hits'] += 1
                        return item['data']
                    else:
                        del self._memory_storage[key]
                
                self._memory_stats['misses'] += 1
                return default
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self._memory_storage[key] = {
                    'data': value,
                    'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
                }
                self._memory_stats['sets'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self._memory_storage:
                    del self._memory_storage[key]
                    self._memory_stats['deletes'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                if key in self._memory_storage:
                    item = self._memory_storage[key]
                    if datetime.utcnow() < item['expires_at']:
                        return True
                    else:
                        del self._memory_storage[key]
                return False
            
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if self.redis_client:
                return bool(self.redis_client.expire(key, ttl))
            else:
                if key in self._memory_storage:
                    self._memory_storage[key]['expires_at'] = datetime.utcnow() + timedelta(seconds=ttl)
                    return True
                return False
            
        except Exception as e:
            logger.error(f"Error setting expiration for cache key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern"""
        try:
            cleared_count = 0
            
            if self.redis_client:
                # Scan for keys matching pattern
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
                    cleared_count += 1
            else:
                # In-memory pattern matching
                keys_to_delete = []
                for key in self._memory_storage.keys():
                    if self._match_pattern(key, pattern):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_storage[key]
                    cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} cache entries matching pattern: {pattern}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0
    
    def clear_all(self) -> int:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                # Flush all databases
                self.redis_client.flushall()
                return 1  # Redis doesn't return count for flushall
            else:
                # Clear in-memory storage
                count = len(self._memory_storage)
                self._memory_storage.clear()
                logger.info(f"Cleared all {count} cache entries")
                return count
            
        except Exception as e:
            logger.error(f"Error clearing all cache: {str(e)}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                # Get Redis info
                info = self.redis_client.info()
                stats = {
                    'total_keys': info.get('db0', {}).get('keys', 0),
                    'memory_usage': info.get('used_memory_human', 'Unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                    'uptime': info.get('uptime_in_seconds', 0),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
                
                # Calculate hit rate
                total_requests = stats['hits'] + stats['misses']
                if total_requests > 0:
                    stats['hit_rate'] = stats['hits'] / total_requests
                else:
                    stats['hit_rate'] = 0
                
                return stats
            else:
                # In-memory statistics
                total_requests = self._memory_stats['hits'] + self._memory_stats['misses']
                hit_rate = self._memory_stats['hits'] / total_requests if total_requests > 0 else 0
                
                return {
                    'total_keys': len(self._memory_storage),
                    'memory_usage': 'In-memory',
                    'connected_clients': 1,
                    'uptime': 0,
                    'hits': self._memory_stats['hits'],
                    'misses': self._memory_stats['misses'],
                    'sets': self._memory_stats['sets'],
                    'deletes': self._memory_stats['deletes'],
                    'hit_rate': hit_rate
                }
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {str(e)}")
            return {}
    
    def cache_function_result(self, func_name: str, args: tuple, kwargs: dict, 
                            result: Any, ttl: Optional[int] = None) -> str:
        """Cache function result with automatic key generation"""
        try:
            # Generate cache key from function name and arguments
            key_data = {
                'func': func_name,
                'args': args,
                'kwargs': sorted(kwargs.items()) if kwargs else []
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = f"func:{func_name}:{hashlib.md5(key_string.encode()).hexdigest()}"
            
            # Store result
            self.set(cache_key, result, ttl)
            
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching function result: {str(e)}")
            return ""
    
    def get_cached_function_result(self, func_name: str, args: tuple, kwargs: dict) -> Any:
        """Get cached function result"""
        try:
            # Generate cache key
            key_data = {
                'func': func_name,
                'args': args,
                'kwargs': sorted(kwargs.items()) if kwargs else []
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = f"func:{func_name}:{hashlib.md5(key_string.encode()).hexdigest()}"
            
            # Get cached result
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached function result: {str(e)}")
            return None
    
    def cache_user_data(self, user_id: int, data_type: str, data: Any, 
                       ttl: Optional[int] = None) -> str:
        """Cache user-specific data"""
        try:
            cache_key = f"user:{user_id}:{data_type}"
            self.set(cache_key, data, ttl)
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching user data: {str(e)}")
            return ""
    
    def get_cached_user_data(self, user_id: int, data_type: str) -> Any:
        """Get cached user-specific data"""
        try:
            cache_key = f"user:{user_id}:{data_type}"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached user data: {str(e)}")
            return None
    
    def cache_search_results(self, search_params: Dict[str, Any], results: Any, 
                           ttl: Optional[int] = None) -> str:
        """Cache search results"""
        try:
            # Generate cache key from search parameters
            key_string = json.dumps(search_params, sort_keys=True)
            cache_key = f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
            
            self.set(cache_key, results, ttl)
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching search results: {str(e)}")
            return ""
    
    def get_cached_search_results(self, search_params: Dict[str, Any]) -> Any:
        """Get cached search results"""
        try:
            # Generate cache key from search parameters
            key_string = json.dumps(search_params, sort_keys=True)
            cache_key = f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
            
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached search results: {str(e)}")
            return None
    
    def warm_cache(self, warmup_data: List[Dict[str, Any]]) -> int:
        """Warm up cache with predefined data"""
        try:
            warmed_count = 0
            
            for item in warmup_data:
                key = item.get('key')
                value = item.get('value')
                ttl = item.get('ttl', self.default_ttl)
                
                if key and value is not None:
                    if self.set(key, value, ttl):
                        warmed_count += 1
            
            logger.info(f"Warmed up {warmed_count} cache entries")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Error warming cache: {str(e)}")
            return 0
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            cleaned_count = 0
            
            if self.redis_client:
                # Redis handles expiration automatically
                return 0
            else:
                # Clean up in-memory storage
                current_time = datetime.utcnow()
                keys_to_delete = []
                
                for key, item in self._memory_storage.items():
                    if current_time >= item['expires_at']:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_storage[key]
                    cleaned_count += 1
                
                logger.info(f"Cleaned up {cleaned_count} expired cache entries")
                return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")
            return 0
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys"""
        try:
            if pattern == '*':
                return True
            
            if '*' in pattern:
                # Simple wildcard matching
                parts = pattern.split('*')
                if len(parts) == 2:
                    return key.startswith(parts[0]) and key.endswith(parts[1])
                elif len(parts) == 1:
                    return key.startswith(parts[0])
            
            return key == pattern
            
        except Exception:
            return False
    
    def ping(self) -> bool:
        """Health check for the service"""
        try:
            if self.redis_client:
                self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache service health check failed: {str(e)}")
            return False 