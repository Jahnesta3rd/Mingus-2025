# Database Query Optimization, Query Caching, and Redis Session Configuration Guide

**Date:** January 2026  
**Status:** 📋 **IMPLEMENTATION GUIDE**

---

## Overview

This guide provides step-by-step recommendations for:
1. **Database Query Optimization** - Improve query performance
2. **Query Caching with Redis** - Cache frequently accessed queries
3. **Redis Session Configuration** - Move sessions from Flask to Redis

---

## Current State Analysis

### Database Setup
- **Primary DB:** SQLite (dev) / PostgreSQL (production)
- **ORM:** SQLAlchemy
- **Connection Pooling:** Basic (pool_pre_ping, pool_recycle)
- **Query Optimization:** Partial (some indexes exist)

### Redis Setup
- **Status:** Configured for rate limiting
- **URL:** `redis://localhost:6379/1` (rate limiting)
- **Usage:** Rate limiting only
- **Sessions:** Not using Redis (using Flask sessions)

### Session Management
- **Current:** Flask server-side sessions
- **Storage:** Server memory/filesystem
- **Issues:** Not scalable, lost on server restart

---

## Part 1: Database Query Optimization

### Step 1.1: Enhance Connection Pooling

**File:** `backend/models/database.py`

**Current:**
```python
'SQLALCHEMY_ENGINE_OPTIONS': {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

**Optimized:**
```python
'SQLALCHEMY_ENGINE_OPTIONS': {
    'pool_pre_ping': True,
    'pool_recycle': 3600,  # 1 hour (PostgreSQL default)
    'pool_size': 10,  # Number of connections to maintain
    'max_overflow': 20,  # Additional connections when pool is exhausted
    'pool_timeout': 30,  # Seconds to wait for connection
    'echo': False,  # Set to True for SQL query logging (dev only)
    'connect_args': {
        'connect_timeout': 10,
        'application_name': 'mingus_app',
    }
}
```

**Implementation:**
```python
def init_database(app: Flask):
    """Initialize database with optimized connection pooling"""
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
    
    # Determine pool settings based on database type
    if database_url.startswith('postgresql'):
        engine_options = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true',
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'mingus_app',
            }
        }
    else:
        # SQLite doesn't support connection pooling
        engine_options = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': engine_options
    })
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return db
```

### Step 1.2: Add Database Indexes

**File:** Create `backend/optimization/database_indexes.py`

**Common Indexes Needed:**
```python
from sqlalchemy import Index, text
from backend.models.database import db

def create_performance_indexes():
    """Create indexes for frequently queried columns"""
    
    indexes = [
        # User-related indexes
        Index('idx_user_email', 'users.email'),
        Index('idx_user_created_at', 'users.created_at'),
        
        # Assessment indexes
        Index('idx_assessment_user_id', 'assessments.user_id'),
        Index('idx_assessment_type', 'assessments.assessment_type'),
        Index('idx_assessment_created_at', 'assessments.created_at'),
        Index('idx_assessment_user_type', 'assessments.user_id', 'assessments.assessment_type'),
        
        # Profile indexes
        Index('idx_profile_user_id', 'user_profiles.user_id'),
        Index('idx_profile_email', 'user_profiles.email'),
        
        # Vehicle indexes
        Index('idx_vehicle_user_id', 'vehicles.user_id'),
        Index('idx_vehicle_created_at', 'vehicles.created_at'),
        
        # Session indexes
        Index('idx_session_user_id', 'user_sessions.user_id'),
        Index('idx_session_start', 'user_sessions.session_start'),
    ]
    
    for index in indexes:
        try:
            index.create(db.engine, checkfirst=True)
            logger.info(f"Created index: {index.name}")
        except Exception as e:
            logger.warning(f"Index {index.name} may already exist: {e}")
```

**Add to app initialization:**
```python
# In app.py, after db.create_all()
from backend.optimization.database_indexes import create_performance_indexes
create_performance_indexes()
```

### Step 1.3: Optimize Common Queries

**File:** `backend/utils/query_optimizer.py`

**Create query optimization utilities:**
```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Utilities for optimizing database queries"""
    
    @staticmethod
    def optimize_user_query(query, include_profile=False, include_vehicles=False):
        """Optimize user queries with eager loading"""
        if include_profile:
            query = query.options(joinedload('profile'))
        if include_vehicles:
            query = query.options(selectinload('vehicles'))
        return query
    
    @staticmethod
    def paginate_query(query, page=1, per_page=20):
        """Add pagination to queries"""
        return query.offset((page - 1) * per_page).limit(per_page)
    
    @staticmethod
    def use_index_hint(query, table_name, index_name):
        """Add index hint for PostgreSQL"""
        # PostgreSQL specific
        return query.with_hint(
            table_name,
            f"USE INDEX ({index_name})",
            'postgresql'
        )
    
    @staticmethod
    def explain_query(query):
        """Explain query plan for debugging"""
        explanation = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        logger.debug(f"Query: {explanation}")
        return explanation
```

### Step 1.4: Add Query Monitoring

**File:** `backend/monitoring/query_monitor.py`

```python
import time
import logging
from functools import wraps
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Track slow queries
SLOW_QUERY_THRESHOLD = 1.0  # seconds

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > SLOW_QUERY_THRESHOLD:
        logger.warning(f"Slow query detected ({total:.2f}s): {statement[:200]}")
```

---

## Part 2: Query Caching with Redis

### Step 2.1: Create Query Cache Manager

**File:** `backend/services/query_cache_manager.py`

```python
import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
import redis
from datetime import timedelta

logger = logging.getLogger(__name__)

class QueryCacheManager:
    """Redis-based query result caching"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def _generate_cache_key(self, query_str: str, params: dict = None) -> str:
        """Generate cache key from query and parameters"""
        cache_data = f"{query_str}:{json.dumps(params or {}, sort_keys=True)}"
        cache_hash = hashlib.sha256(cache_data.encode()).hexdigest()
        return f"query_cache:{cache_hash}"
    
    def get_cached_result(self, query_str: str, params: dict = None) -> Optional[Any]:
        """Get cached query result"""
        try:
            cache_key = self._generate_cache_key(query_str, params)
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for query: {query_str[:100]}")
                return json.loads(cached)
            logger.debug(f"Cache miss for query: {query_str[:100]}")
            return None
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            return None
    
    def set_cached_result(
        self, 
        query_str: str, 
        result: Any, 
        params: dict = None,
        ttl: int = None
    ):
        """Cache query result"""
        try:
            cache_key = self._generate_cache_key(query_str, params)
            ttl = ttl or self.default_ttl
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            logger.debug(f"Cached query result: {query_str[:100]}")
        except Exception as e:
            logger.error(f"Error caching result: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            keys = self.redis.keys(f"query_cache:{pattern}*")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def clear_all(self):
        """Clear all query cache"""
        try:
            keys = self.redis.keys("query_cache:*")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

def cache_query(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache query results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager from app context or create new
            from flask import current_app
            cache_manager = current_app.query_cache_manager
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_hash = hashlib.sha256(cache_key.encode()).hexdigest()
            full_key = f"query_cache:{cache_hash}"
            
            # Try to get from cache
            try:
                cached = cache_manager.redis.get(full_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            try:
                cache_manager.redis.setex(
                    full_key,
                    ttl,
                    json.dumps(result, default=str)
                )
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        return wrapper
    return decorator
```

### Step 2.2: Integrate Query Caching

**File:** Update `backend/api/profile_endpoints.py` (example)

```python
from backend.services.query_cache_manager import cache_query, QueryCacheManager

# Initialize cache manager
query_cache = None

@profile_api.route('/profile/<user_id>', methods=['GET'])
@cache_query(ttl=300, key_prefix='user_profile')
def get_profile(user_id):
    """Get user profile with caching"""
    # Query will be cached automatically
    profile = db.session.query(UserProfile).filter_by(user_id=user_id).first()
    return jsonify(profile.to_dict())
```

### Step 2.3: Add Cache Invalidation

**File:** Update endpoints that modify data

```python
from backend.services.query_cache_manager import QueryCacheManager

@profile_api.route('/profile', methods=['PUT'])
def update_profile():
    """Update profile and invalidate cache"""
    # ... update logic ...
    
    # Invalidate related caches
    cache_manager = current_app.query_cache_manager
    cache_manager.invalidate_pattern(f"user_profile:{user_id}")
    cache_manager.invalidate_pattern(f"user:{user_id}")
    
    return jsonify({'success': True})
```

---

## Part 3: Redis Session Configuration

### Step 3.1: Install Flask-Session

```bash
pip install Flask-Session redis
```

### Step 3.2: Configure Redis Session Store

**File:** `backend/config/session_config.py`

```python
import os
import redis
from flask import Flask
from flask_session import Session

def init_redis_session(app: Flask):
    """Initialize Redis-based session storage"""
    
    redis_url = os.environ.get('REDIS_SESSION_URL', 'redis://localhost:6379/0')
    redis_password = os.environ.get('REDIS_PASSWORD')
    
    # Parse Redis URL
    if redis_password:
        # Update URL with password if provided
        if '://:' in redis_url:
            redis_url = redis_url.replace('://:', f'://:{redis_password}@')
        elif '@' not in redis_url:
            # Add password to URL
            redis_url = redis_url.replace('redis://', f'redis://:{redis_password}@')
    
    app.config.update({
        'SESSION_TYPE': 'redis',
        'SESSION_REDIS': redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        ),
        'SESSION_PERMANENT': True,
        'SESSION_USE_SIGNER': True,  # Sign session cookies
        'SESSION_KEY_PREFIX': 'mingus:session:',
        'SESSION_COOKIE_NAME': 'mingus_session',
        'SESSION_COOKIE_SECURE': os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Strict',
        'PERMANENT_SESSION_LIFETIME': 86400,  # 24 hours in seconds
    })
    
    # Initialize Flask-Session
    Session(app)
    
    return app
```

### Step 3.3: Update App Initialization

**File:** `app.py`

```python
from backend.config.session_config import init_redis_session

# After app creation, before blueprint registration
app = Flask(__name__)

# Initialize Redis sessions
init_redis_session(app)

# ... rest of initialization ...
```

### Step 3.4: Update Session Usage

**File:** Update authentication endpoints

**Before (Flask sessions):**
```python
from flask import session

@auth_bp.route('/login', methods=['POST'])
def login():
    # ... validation ...
    session['user_id'] = user.id
    session['email'] = user.email
    session.permanent = True
    return jsonify({'success': True})
```

**After (Redis sessions - same API):**
```python
from flask import session

@auth_bp.route('/login', methods=['POST'])
def login():
    # ... validation ...
    # Same API, but now stored in Redis!
    session['user_id'] = user.id
    session['email'] = user.email
    session.permanent = True
    return jsonify({'success': True})
```

### Step 3.5: Add Session Management Utilities

**File:** `backend/utils/session_manager.py`

```python
from flask import session, current_app
from flask_session import Session
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Utilities for managing Redis sessions"""
    
    @staticmethod
    def get_user_id():
        """Get current user ID from session"""
        return session.get('user_id')
    
    @staticmethod
    def is_authenticated():
        """Check if user is authenticated"""
        return 'user_id' in session
    
    @staticmethod
    def create_session(user_id: str, user_data: dict = None):
        """Create new session"""
        session['user_id'] = user_id
        session.permanent = True
        if user_data:
            session.update(user_data)
        logger.info(f"Session created for user {user_id}")
    
    @staticmethod
    def destroy_session():
        """Destroy current session"""
        user_id = session.get('user_id')
        session.clear()
        logger.info(f"Session destroyed for user {user_id}")
    
    @staticmethod
    def extend_session():
        """Extend session lifetime"""
        session.permanent = True
        # Session lifetime is managed by Redis TTL
    
    @staticmethod
    def get_session_data():
        """Get all session data"""
        return dict(session)
```

---

## Part 4: Environment Configuration

### Step 4.1: Update Environment Variables

**File:** `.env` or `.env.production`

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/mingus_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/2

# Session Configuration
SESSION_COOKIE_SECURE=true  # Use true in production with HTTPS
PERMANENT_SESSION_LIFETIME=86400  # 24 hours
```

### Step 4.2: Update Docker Compose

**File:** `docker-compose.yml`

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: mingus-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - mingus-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## Part 5: Implementation Checklist

### Phase 1: Database Optimization (Week 1)
- [ ] Update connection pooling configuration
- [ ] Create database indexes
- [ ] Add query monitoring
- [ ] Optimize common queries with eager loading
- [ ] Test query performance improvements

### Phase 2: Query Caching (Week 2)
- [ ] Create QueryCacheManager
- [ ] Integrate caching decorator
- [ ] Add cache invalidation logic
- [ ] Configure cache TTLs per query type
- [ ] Test cache hit rates

### Phase 3: Redis Sessions (Week 3)
- [ ] Install Flask-Session
- [ ] Configure Redis session store
- [ ] Update app initialization
- [ ] Test session persistence
- [ ] Verify session security

### Phase 4: Testing & Monitoring (Week 4)
- [ ] Load testing with caching
- [ ] Session persistence testing
- [ ] Monitor Redis memory usage
- [ ] Monitor database query performance
- [ ] Performance benchmarking

---

## Part 6: Monitoring & Metrics

### Step 6.1: Add Cache Metrics

```python
class CacheMetrics:
    """Track cache performance"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.hits_key = "cache_metrics:hits"
        self.misses_key = "cache_metrics:misses"
    
    def record_hit(self):
        self.redis.incr(self.hits_key)
    
    def record_miss(self):
        self.redis.incr(self.misses_key)
    
    def get_hit_rate(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        total = hits + misses
        return hits / total if total > 0 else 0
```

### Step 6.2: Add Query Performance Dashboard

Create endpoint to monitor:
- Cache hit rates
- Slow queries
- Database connection pool usage
- Redis memory usage
- Session count

---

## Expected Performance Improvements

### Database Optimization
- **Query Speed:** 30-50% faster with proper indexes
- **Connection Efficiency:** Better connection reuse
- **Scalability:** Handle more concurrent requests

### Query Caching
- **Response Time:** 70-90% faster for cached queries
- **Database Load:** 50-70% reduction in query load
- **User Experience:** Faster page loads

### Redis Sessions
- **Scalability:** Support multiple server instances
- **Persistence:** Sessions survive server restarts
- **Performance:** Faster session lookups
- **Memory:** Better memory management

---

## Troubleshooting

### Redis Connection Issues
```python
# Test Redis connection
import redis
r = redis.from_url('redis://localhost:6379/0')
r.ping()  # Should return True
```

### Session Not Persisting
- Check Redis is running
- Verify SESSION_REDIS configuration
- Check session cookie settings
- Verify PERMANENT_SESSION_LIFETIME

### Cache Not Working
- Check Redis connection
- Verify cache keys are being generated
- Check TTL settings
- Monitor Redis memory usage

---

## Next Steps

1. **Start with Database Optimization** - Immediate performance gains
2. **Add Query Caching** - Reduce database load
3. **Migrate to Redis Sessions** - Improve scalability
4. **Monitor and Tune** - Optimize based on metrics

---

**Status:** Ready for implementation
