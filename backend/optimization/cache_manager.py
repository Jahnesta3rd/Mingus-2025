"""
Cache Management System
Implements API response caching strategies and cache invalidation
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
from loguru import logger
import pickle
import sqlite3

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size: int = 0

@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size: int = 0
    hit_rate: float = 0.0

class CacheManager:
    """Main cache management system"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600, 
                 db_path: str = "cache.db"):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.db_path = db_path
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        self._lock = threading.RLock()
        
        self._init_cache_database()
        self._start_cleanup_thread()
    
    def _init_cache_database(self):
        """Initialize persistent cache database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at DATETIME,
                        expires_at DATETIME,
                        access_count INTEGER DEFAULT 0,
                        last_accessed DATETIME,
                        size INTEGER
                    )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_access ON cache_entries(last_accessed)")
                
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
    
    def _start_cleanup_thread(self):
        """Start background thread for cache cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Clean up every 5 minutes
                    self._cleanup_expired_entries()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        with self._lock:
            current_time = datetime.now()
            expired_keys = []
            
            # Check memory cache
            for key, entry in self.cache.items():
                if current_time > entry.expires_at:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self.cache[key]
                self.stats.evictions += 1
            
            # Check database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM cache_entries 
                        WHERE expires_at < ?
                    """, (current_time,))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to cleanup database cache: {e}")
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        # Create a deterministic string representation
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _calculate_entry_size(self, value: Any) -> int:
        """Calculate approximate size of cache entry"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value))
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            self.stats.total_requests += 1
            
            # Check memory cache first
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() <= entry.expires_at:
                    # Update access statistics
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self.cache.move_to_end(key)  # Move to end (LRU)
                    
                    self.stats.cache_hits += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self.cache[key]
                    self.stats.evictions += 1
            
            # Check database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value, expires_at, access_count 
                        FROM cache_entries 
                        WHERE key = ?
                    """, (key,))
                    
                    result = cursor.fetchone()
                    if result and datetime.now() <= datetime.fromisoformat(result[1]):
                        # Load into memory cache
                        value = pickle.loads(result[0])
                        entry = CacheEntry(
                            key=key,
                            value=value,
                            created_at=datetime.now(),
                            expires_at=datetime.fromisoformat(result[1]),
                            access_count=result[2] + 1,
                            size=self._calculate_entry_size(value)
                        )
                        
                        self._add_to_memory_cache(key, entry)
                        self.stats.cache_hits += 1
                        return value
            except Exception as e:
                logger.error(f"Failed to get from database cache: {e}")
            
            self.stats.cache_misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        with self._lock:
            try:
                ttl = ttl or self.default_ttl
                expires_at = datetime.now() + timedelta(seconds=ttl)
                size = self._calculate_entry_size(value)
                
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size=size
                )
                
                # Add to memory cache
                self._add_to_memory_cache(key, entry)
                
                # Add to database cache
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            INSERT OR REPLACE INTO cache_entries 
                            (key, value, created_at, expires_at, access_count, last_accessed, size)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            key, pickle.dumps(value), entry.created_at, 
                            entry.expires_at, entry.access_count, 
                            entry.last_accessed, entry.size
                        ))
                        conn.commit()
                except Exception as e:
                    logger.error(f"Failed to save to database cache: {e}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to set cache entry: {e}")
                return False
    
    def _add_to_memory_cache(self, key: str, entry: CacheEntry):
        """Add entry to memory cache with LRU eviction"""
        if key in self.cache:
            # Update existing entry
            old_entry = self.cache[key]
            self.stats.total_size -= old_entry.size
            self.cache[key] = entry
            self.cache.move_to_end(key)
        else:
            # Check if we need to evict entries
            while (len(self.cache) >= self.max_size and 
                   self.stats.total_size + entry.size > self.max_size * 1000):  # 1KB per entry estimate
                # Remove least recently used entry
                lru_key, lru_entry = self.cache.popitem(last=False)
                self.stats.total_size -= lru_entry.size
                self.stats.evictions += 1
            
            # Add new entry
            self.cache[key] = entry
            self.stats.total_size += entry.size
        
        self.cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        with self._lock:
            try:
                # Remove from memory cache
                if key in self.cache:
                    entry = self.cache[key]
                    self.stats.total_size -= entry.size
                    del self.cache[key]
                
                # Remove from database cache
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete cache entry: {e}")
                return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        with self._lock:
            try:
                # Clear memory cache
                self.cache.clear()
                self.stats.total_size = 0
                
                # Clear database cache
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
                    conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear cache: {e}")
                return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        with self._lock:
            invalidated_count = 0
            
            try:
                # Invalidate memory cache entries
                keys_to_remove = [key for key in self.cache.keys() if pattern in key]
                for key in keys_to_remove:
                    entry = self.cache[key]
                    self.stats.total_size -= entry.size
                    del self.cache[key]
                    invalidated_count += 1
                
                # Invalidate database cache entries
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT key FROM cache_entries WHERE key LIKE ?
                    """, (f'%{pattern}%',))
                    
                    keys_to_delete = [row[0] for row in cursor.fetchall()]
                    if keys_to_delete:
                        placeholders = ','.join(['?' for _ in keys_to_delete])
                        conn.execute(f"DELETE FROM cache_entries WHERE key IN ({placeholders})", keys_to_delete)
                        conn.commit()
                        invalidated_count += len(keys_to_delete)
                
                return invalidated_count
                
            except Exception as e:
                logger.error(f"Failed to invalidate cache pattern: {e}")
                return invalidated_count
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics"""
        with self._lock:
            # Calculate hit rate
            total_requests = self.stats.total_requests
            if total_requests > 0:
                self.stats.hit_rate = self.stats.cache_hits / total_requests
            
            return CacheStats(
                total_requests=self.stats.total_requests,
                cache_hits=self.stats.cache_hits,
                cache_misses=self.stats.cache_misses,
                evictions=self.stats.evictions,
                total_size=self.stats.total_size,
                hit_rate=self.stats.hit_rate
            )
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self._lock:
            # Get memory cache info
            memory_entries = len(self.cache)
            memory_size = self.stats.total_size
            
            # Get database cache info
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*), SUM(size) FROM cache_entries")
                    db_entries, db_size = cursor.fetchone()
                    db_entries = db_entries or 0
                    db_size = db_size or 0
            except Exception as e:
                logger.error(f"Failed to get database cache info: {e}")
                db_entries = 0
                db_size = 0
            
            # Get most accessed entries
            most_accessed = sorted(
                self.cache.items(),
                key=lambda x: x[1].access_count,
                reverse=True
            )[:10]
            
            return {
                'memory_cache': {
                    'entries': memory_entries,
                    'size_bytes': memory_size,
                    'max_size': self.max_size
                },
                'database_cache': {
                    'entries': db_entries,
                    'size_bytes': db_size
                },
                'most_accessed': [
                    {
                        'key': key,
                        'access_count': entry.access_count,
                        'last_accessed': entry.last_accessed.isoformat(),
                        'size': entry.size
                    }
                    for key, entry in most_accessed
                ],
                'stats': self.get_stats().__dict__
            }
    
    def cache_decorator(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """Decorator for caching function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = key_prefix + self._generate_cache_key(*args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Global cache manager instance
cache_manager = CacheManager()

# Convenience decorators
def cache_api_response(ttl: int = 3600):
    """Decorator for caching API responses"""
    return cache_manager.cache_decorator(ttl=ttl, key_prefix="api_")

def cache_database_query(ttl: int = 1800):
    """Decorator for caching database query results"""
    return cache_manager.cache_decorator(ttl=ttl, key_prefix="db_")

def cache_score_calculation(ttl: int = 7200):
    """Decorator for caching score calculation results"""
    return cache_manager.cache_decorator(ttl=ttl, key_prefix="score_") 