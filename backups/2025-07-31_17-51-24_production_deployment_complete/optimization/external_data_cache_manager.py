"""
External Data Cache Manager
Specialized cache manager for employer financial data, WARN notices, BLS data, and job security scores
with specific TTL requirements and subscription tier-based policies.
"""

import time
import json
import hashlib
import redis
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
from loguru import logger
import pickle
import sqlite3
from enum import Enum

class DataType(Enum):
    """External data types with their TTL configurations"""
    EMPLOYER_FINANCIAL = "employer_financial"
    WARN_NOTICES = "warn_notices"
    BLS_INDUSTRY = "bls_industry"
    JOB_SECURITY_SCORE = "job_security_score"
    LABOR_MARKET = "labor_market"

class SubscriptionTier(Enum):
    """Subscription tiers with cache policy configurations"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class CachePolicy:
    """Cache policy configuration for different data types and subscription tiers"""
    ttl_seconds: int
    max_size_mb: int
    refresh_threshold: float  # Percentage of TTL remaining to trigger refresh
    subscription_tier: SubscriptionTier
    redis_enabled: bool = True
    db_persistence: bool = True

@dataclass
class ExternalCacheEntry:
    """External data cache entry with metadata"""
    cache_key: str
    data_type: DataType
    data_source: str
    cached_data: Any
    data_hash: str
    ttl_seconds: int
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    access_count: int
    is_valid: bool
    error_count: int
    last_error: Optional[str]
    subscription_tier: SubscriptionTier
    size_bytes: int = 0

class ExternalDataCacheManager:
    """
    Specialized cache manager for external data with:
    - Employer financial data (24hr TTL)
    - WARN notices by metro area (7 day TTL)
    - BLS industry data (30 day TTL)
    - User job security scores (1hr TTL, refresh on check-in)
    - Redis integration
    - Subscription tier-based cache policies
    """
    
    # TTL configurations in seconds
    TTL_CONFIGS = {
        DataType.EMPLOYER_FINANCIAL: 86400,      # 24 hours
        DataType.WARN_NOTICES: 604800,           # 7 days
        DataType.BLS_INDUSTRY: 2592000,          # 30 days
        DataType.JOB_SECURITY_SCORE: 3600,       # 1 hour
        DataType.LABOR_MARKET: 604800,           # 7 days
    }
    
    # Subscription tier cache policies
    SUBSCRIPTION_POLICIES = {
        SubscriptionTier.FREE: {
            'max_cache_size_mb': 100,
            'refresh_threshold': 0.8,  # Refresh at 80% of TTL
            'redis_enabled': False,
            'db_persistence': True
        },
        SubscriptionTier.PREMIUM: {
            'max_cache_size_mb': 500,
            'refresh_threshold': 0.7,  # Refresh at 70% of TTL
            'redis_enabled': True,
            'db_persistence': True
        },
        SubscriptionTier.ENTERPRISE: {
            'max_cache_size_mb': 2000,
            'refresh_threshold': 0.6,  # Refresh at 60% of TTL
            'redis_enabled': True,
            'db_persistence': True
        }
    }
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 db_path: str = "external_cache.db",
                 max_memory_mb: int = 1000):
        """
        Initialize external data cache manager
        
        Args:
            redis_url: Redis connection URL (optional)
            db_path: SQLite database path for persistence
            max_memory_mb: Maximum memory usage in MB
        """
        self.redis_url = redis_url
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # Initialize Redis connection if available
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Initialize SQLite database
        self._init_cache_database()
        
        # Memory cache for frequently accessed data
        self.memory_cache: OrderedDict[str, ExternalCacheEntry] = OrderedDict()
        self.current_memory_usage = 0
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'redis_hits': 0,
            'db_hits': 0,
            'evictions': 0,
            'errors': 0
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Start background cleanup thread
        self._start_cleanup_thread()
    
    def _init_cache_database(self):
        """Initialize SQLite database for external data cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS employer_analysis_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cache_key TEXT UNIQUE NOT NULL,
                        data_type TEXT NOT NULL,
                        data_source TEXT NOT NULL,
                        cached_data BLOB NOT NULL,
                        data_hash TEXT,
                        ttl_seconds INTEGER NOT NULL,
                        created_at DATETIME NOT NULL,
                        expires_at DATETIME NOT NULL,
                        last_accessed DATETIME NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        is_valid BOOLEAN DEFAULT TRUE,
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        subscription_tier TEXT,
                        size_bytes INTEGER DEFAULT 0
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_data_type ON employer_analysis_cache(data_type, expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_access ON employer_analysis_cache(last_accessed, access_count)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_validity ON employer_analysis_cache(is_valid, expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_subscription ON employer_analysis_cache(subscription_tier, data_type)")
                
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
        """Remove expired cache entries from all storage layers"""
        with self._lock:
            current_time = datetime.utcnow()
            
            # Clean memory cache
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if current_time > entry.expires_at:
                    expired_keys.append(key)
                    self.current_memory_usage -= entry.size_bytes
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats['evictions'] += 1
            
            # Clean Redis cache
            if self.redis_client:
                try:
                    # Redis handles TTL automatically, but we can clean up invalid entries
                    pass
                except Exception as e:
                    logger.error(f"Redis cleanup error: {e}")
            
            # Clean database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM employer_analysis_cache 
                        WHERE expires_at < ? OR is_valid = FALSE
                    """, (current_time,))
                    conn.commit()
            except Exception as e:
                logger.error(f"Database cleanup error: {e}")
    
    def _generate_cache_key(self, data_type: DataType, identifier: str, subscription_tier: SubscriptionTier) -> str:
        """Generate cache key for external data"""
        key_data = {
            'data_type': data_type.value,
            'identifier': identifier,
            'subscription_tier': subscription_tier.value,
            'version': '1.0'  # For cache invalidation
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of cached data for change detection"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calculate approximate size of cached data in bytes"""
        try:
            return len(pickle.dumps(data))
        except:
            return len(json.dumps(data, default=str))
    
    def get_external_data(self, 
                         data_type: DataType, 
                         identifier: str, 
                         subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Any]:
        """
        Get external data from cache
        
        Args:
            data_type: Type of external data
            identifier: Unique identifier (e.g., company name, metro area)
            subscription_tier: User's subscription tier
            
        Returns:
            Cached data if available and valid, None otherwise
        """
        with self._lock:
            self.stats['total_requests'] += 1
            
            cache_key = self._generate_cache_key(data_type, identifier, subscription_tier)
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if datetime.utcnow() <= entry.expires_at and entry.is_valid:
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    self.memory_cache.move_to_end(cache_key)
                    self.stats['cache_hits'] += 1
                    return entry.cached_data
            
            # Check Redis cache
            if self.redis_client and self._is_redis_enabled(subscription_tier):
                try:
                    redis_key = f"external_data:{cache_key}"
                    cached_data = self.redis_client.get(redis_key)
                    if cached_data:
                        data = pickle.loads(cached_data)
                        self.stats['redis_hits'] += 1
                        self.stats['cache_hits'] += 1
                        return data
                except Exception as e:
                    logger.error(f"Redis get error: {e}")
                    self.stats['errors'] += 1
            
            # Check database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT cached_data, expires_at, access_count, is_valid
                        FROM employer_analysis_cache 
                        WHERE cache_key = ?
                    """, (cache_key,))
                    
                    result = cursor.fetchone()
                    if result and datetime.utcnow() <= datetime.fromisoformat(result[1]) and result[3]:
                        # Load into memory cache
                        data = pickle.loads(result[0])
                        entry = ExternalCacheEntry(
                            cache_key=cache_key,
                            data_type=data_type,
                            data_source="",  # Would need to store this
                            cached_data=data,
                            data_hash="",
                            ttl_seconds=self.TTL_CONFIGS[data_type],
                            created_at=datetime.utcnow(),
                            expires_at=datetime.fromisoformat(result[1]),
                            last_accessed=datetime.utcnow(),
                            access_count=result[2] + 1,
                            is_valid=result[3],
                            error_count=0,
                            last_error=None,
                            subscription_tier=subscription_tier,
                            size_bytes=self._calculate_data_size(data)
                        )
                        
                        self._add_to_memory_cache(cache_key, entry)
                        self.stats['db_hits'] += 1
                        self.stats['cache_hits'] += 1
                        return data
            except Exception as e:
                logger.error(f"Database get error: {e}")
                self.stats['errors'] += 1
            
            self.stats['cache_misses'] += 1
            return None
    
    def set_external_data(self, 
                         data_type: DataType, 
                         identifier: str, 
                         data: Any, 
                         data_source: str,
                         subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
                         ttl_override: Optional[int] = None) -> bool:
        """
        Cache external data with appropriate TTL and storage policies
        
        Args:
            data_type: Type of external data
            identifier: Unique identifier
            data: Data to cache
            data_source: Source of the data
            subscription_tier: User's subscription tier
            ttl_override: Override default TTL (in seconds)
            
        Returns:
            True if successfully cached, False otherwise
        """
        with self._lock:
            try:
                cache_key = self._generate_cache_key(data_type, identifier, subscription_tier)
                ttl_seconds = ttl_override or self.TTL_CONFIGS[data_type]
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                data_hash = self._calculate_data_hash(data)
                size_bytes = self._calculate_data_size(data)
                
                entry = ExternalCacheEntry(
                    cache_key=cache_key,
                    data_type=data_type,
                    data_source=data_source,
                    cached_data=data,
                    data_hash=data_hash,
                    ttl_seconds=ttl_seconds,
                    created_at=datetime.utcnow(),
                    expires_at=expires_at,
                    last_accessed=datetime.utcnow(),
                    access_count=1,
                    is_valid=True,
                    error_count=0,
                    last_error=None,
                    subscription_tier=subscription_tier,
                    size_bytes=size_bytes
                )
                
                # Store in memory cache
                self._add_to_memory_cache(cache_key, entry)
                
                # Store in Redis if enabled
                if self.redis_client and self._is_redis_enabled(subscription_tier):
                    try:
                        redis_key = f"external_data:{cache_key}"
                        self.redis_client.setex(
                            redis_key, 
                            ttl_seconds, 
                            pickle.dumps(data)
                        )
                    except Exception as e:
                        logger.error(f"Redis set error: {e}")
                        self.stats['errors'] += 1
                
                # Store in database if enabled
                if self._is_db_persistence_enabled(subscription_tier):
                    try:
                        with sqlite3.connect(self.db_path) as conn:
                            conn.execute("""
                                INSERT OR REPLACE INTO employer_analysis_cache
                                (cache_key, data_type, data_source, cached_data, data_hash, 
                                 ttl_seconds, created_at, expires_at, last_accessed, access_count, 
                                 is_valid, error_count, last_error, subscription_tier, size_bytes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                cache_key, data_type.value, data_source, pickle.dumps(data),
                                data_hash, ttl_seconds, entry.created_at, expires_at,
                                entry.last_accessed, entry.access_count, entry.is_valid,
                                entry.error_count, entry.last_error, subscription_tier.value,
                                size_bytes
                            ))
                            conn.commit()
                    except Exception as e:
                        logger.error(f"Database set error: {e}")
                        self.stats['errors'] += 1
                
                return True
                
            except Exception as e:
                logger.error(f"Cache set error: {e}")
                self.stats['errors'] += 1
                return False
    
    def _add_to_memory_cache(self, key: str, entry: ExternalCacheEntry):
        """Add entry to memory cache with size management"""
        # Remove existing entry if present
        if key in self.memory_cache:
            self.current_memory_usage -= self.memory_cache[key].size_bytes
        
        # Check if we need to evict entries due to size limits
        policy = self.SUBSCRIPTION_POLICIES[entry.subscription_tier]
        max_size_bytes = policy['max_cache_size_mb'] * 1024 * 1024
        
        while (self.current_memory_usage + entry.size_bytes > max_size_bytes and 
               self.memory_cache):
            # Remove least recently used entry
            oldest_key, oldest_entry = self.memory_cache.popitem(last=False)
            self.current_memory_usage -= oldest_entry.size_bytes
            self.stats['evictions'] += 1
        
        # Add new entry
        self.memory_cache[key] = entry
        self.current_memory_usage += entry.size_bytes
    
    def _is_redis_enabled(self, subscription_tier: SubscriptionTier) -> bool:
        """Check if Redis is enabled for the subscription tier"""
        return (self.redis_client is not None and 
                self.SUBSCRIPTION_POLICIES[subscription_tier]['redis_enabled'])
    
    def _is_db_persistence_enabled(self, subscription_tier: SubscriptionTier) -> bool:
        """Check if database persistence is enabled for the subscription tier"""
        return self.SUBSCRIPTION_POLICIES[subscription_tier]['db_persistence']
    
    def invalidate_user_job_security_cache(self, user_id: int):
        """Invalidate job security cache for a specific user (called on health check-in)"""
        with self._lock:
            # Invalidate memory cache
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if (entry.data_type == DataType.JOB_SECURITY_SCORE and 
                    str(user_id) in entry.cache_key):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self.current_memory_usage -= self.memory_cache[key].size_bytes
                del self.memory_cache[key]
            
            # Invalidate Redis cache
            if self.redis_client:
                try:
                    pattern = f"external_data:*job_security_score*{user_id}*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis invalidation error: {e}")
            
            # Invalidate database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE employer_analysis_cache 
                        SET is_valid = FALSE 
                        WHERE data_type = ? AND cache_key LIKE ?
                    """, (DataType.JOB_SECURITY_SCORE.value, f"%{user_id}%"))
                    conn.commit()
            except Exception as e:
                logger.error(f"Database invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            return {
                **self.stats,
                'memory_usage_mb': self.current_memory_usage / (1024 * 1024),
                'memory_cache_size': len(self.memory_cache),
                'redis_enabled': self.redis_client is not None,
                'hit_rate': (self.stats['cache_hits'] / max(self.stats['total_requests'], 1)) * 100
            }
    
    def clear_cache(self, data_type: Optional[DataType] = None):
        """Clear cache entries, optionally filtered by data type"""
        with self._lock:
            if data_type:
                # Clear specific data type
                keys_to_remove = [
                    key for key, entry in self.memory_cache.items() 
                    if entry.data_type == data_type
                ]
                for key in keys_to_remove:
                    self.current_memory_usage -= self.memory_cache[key].size_bytes
                    del self.memory_cache[key]
            else:
                # Clear all cache
                self.memory_cache.clear()
                self.current_memory_usage = 0
            
            # Clear Redis cache
            if self.redis_client:
                try:
                    if data_type:
                        pattern = f"external_data:*{data_type.value}*"
                    else:
                        pattern = "external_data:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis clear error: {e}")
            
            # Clear database cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    if data_type:
                        conn.execute("DELETE FROM employer_analysis_cache WHERE data_type = ?", 
                                   (data_type.value,))
                    else:
                        conn.execute("DELETE FROM employer_analysis_cache")
                    conn.commit()
            except Exception as e:
                logger.error(f"Database clear error: {e}")

    # Convenience methods for specific data types
    def cache_employer_financial_data(self, 
                                    company_name: str, 
                                    financial_data: Dict[str, Any],
                                    subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
        """Cache employer financial data with 24hr TTL"""
        return self.set_external_data(
            DataType.EMPLOYER_FINANCIAL,
            company_name,
            financial_data,
            "financial_api",
            subscription_tier
        )

    def cache_warn_notices(self,
                          metro_area: str,
                          warn_data: List[Dict[str, Any]],
                          subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
        """Cache WARN notices by metro area with 7 day TTL"""
        return self.set_external_data(
            DataType.WARN_NOTICES,
            metro_area,
            warn_data,
            "warn_api",
            subscription_tier
        )

    def cache_bls_industry_data(self,
                               industry_code: str,
                               bls_data: Dict[str, Any],
                               subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
        """Cache BLS industry data with 30 day TTL"""
        return self.set_external_data(
            DataType.BLS_INDUSTRY,
            industry_code,
            bls_data,
            "bls_api",
            subscription_tier
        )

    def cache_job_security_score(self,
                                user_id: int,
                                score_data: Dict[str, Any],
                                subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
        """Cache user job security score with 1hr TTL"""
        return self.set_external_data(
            DataType.JOB_SECURITY_SCORE,
            str(user_id),
            score_data,
            "job_security_ml",
            subscription_tier
        )

    def get_employer_financial_data(self, 
                                  company_name: str,
                                  subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
        """Get cached employer financial data"""
        return self.get_external_data(DataType.EMPLOYER_FINANCIAL, company_name, subscription_tier)

    def get_warn_notices(self,
                        metro_area: str,
                        subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[List[Dict[str, Any]]]:
        """Get cached WARN notices for metro area"""
        return self.get_external_data(DataType.WARN_NOTICES, metro_area, subscription_tier)

    def get_bls_industry_data(self,
                             industry_code: str,
                             subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
        """Get cached BLS industry data"""
        return self.get_external_data(DataType.BLS_INDUSTRY, industry_code, subscription_tier)

    def get_job_security_score(self,
                              user_id: int,
                              subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
        """Get cached job security score for user"""
        return self.get_external_data(DataType.JOB_SECURITY_SCORE, str(user_id), subscription_tier)

# Global cache manager instance
_external_cache_manager = None

def get_external_cache_manager(redis_url: Optional[str] = None) -> ExternalDataCacheManager:
    """Get or create global external cache manager instance"""
    global _external_cache_manager
    if _external_cache_manager is None:
        _external_cache_manager = ExternalDataCacheManager(redis_url=redis_url)
    return _external_cache_manager

# Convenience functions for easy access
def cache_employer_financial_data(company_name: str, 
                                financial_data: Dict[str, Any],
                                subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
    """Cache employer financial data with 24hr TTL"""
    cache_manager = get_external_cache_manager()
    return cache_manager.cache_employer_financial_data(company_name, financial_data, subscription_tier)

def cache_warn_notices(metro_area: str,
                      warn_data: List[Dict[str, Any]],
                      subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
    """Cache WARN notices by metro area with 7 day TTL"""
    cache_manager = get_external_cache_manager()
    return cache_manager.cache_warn_notices(metro_area, warn_data, subscription_tier)

def cache_bls_industry_data(industry_code: str,
                           bls_data: Dict[str, Any],
                           subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
    """Cache BLS industry data with 30 day TTL"""
    cache_manager = get_external_cache_manager()
    return cache_manager.cache_bls_industry_data(industry_code, bls_data, subscription_tier)

def cache_job_security_score(user_id: int,
                            score_data: Dict[str, Any],
                            subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> bool:
    """Cache user job security score with 1hr TTL"""
    cache_manager = get_external_cache_manager()
    return cache_manager.cache_job_security_score(user_id, score_data, subscription_tier)

def get_employer_financial_data(company_name: str,
                              subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
    """Get cached employer financial data"""
    cache_manager = get_external_cache_manager()
    return cache_manager.get_employer_financial_data(company_name, subscription_tier)

def get_warn_notices(metro_area: str,
                    subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[List[Dict[str, Any]]]:
    """Get cached WARN notices for metro area"""
    cache_manager = get_external_cache_manager()
    return cache_manager.get_warn_notices(metro_area, subscription_tier)

def get_bls_industry_data(industry_code: str,
                         subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
    """Get cached BLS industry data"""
    cache_manager = get_external_cache_manager()
    return cache_manager.get_bls_industry_data(industry_code, subscription_tier)

def get_job_security_score(user_id: int,
                          subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Optional[Dict[str, Any]]:
    """Get cached job security score for user"""
    cache_manager = get_external_cache_manager()
    return cache_manager.get_job_security_score(user_id, subscription_tier)

def invalidate_user_job_security_cache(user_id: int):
    """Invalidate job security cache for a specific user (called on health check-in)"""
    cache_manager = get_external_cache_manager()
    cache_manager.invalidate_user_job_security_cache(user_id) 