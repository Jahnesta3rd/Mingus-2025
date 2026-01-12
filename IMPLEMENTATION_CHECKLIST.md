# Database Optimization & Redis Implementation Checklist

**Quick Start Guide** - Follow these steps in order

---

## Prerequisites

- [ ] Redis server running (check: `redis-cli ping`)
- [ ] PostgreSQL or SQLite database configured
- [ ] Python dependencies installed

---

## Step 1: Install Dependencies

```bash
pip install Flask-Session redis
```

---

## Step 2: Update Database Configuration

**File:** `backend/models/database.py`

**Add optimized connection pooling:**

```python
def init_database(app: Flask):
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
    
    # Enhanced connection pooling for PostgreSQL
    if database_url.startswith('postgresql'):
        engine_options = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        }
    else:
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
        # Create indexes
        from backend.optimization.database_indexes import create_performance_indexes
        create_performance_indexes()
    
    return db
```

---

## Step 3: Configure Redis Sessions

**File:** `app.py`

**Add after app creation:**

```python
from backend.config.session_config import init_redis_session

app = Flask(__name__)

# Initialize Redis sessions (add this line)
init_redis_session(app)

# ... rest of your app configuration ...
```

---

## Step 4: Initialize Query Cache Manager

**File:** `app.py`

**Add after Redis session initialization:**

```python
import redis
from backend.services.query_cache_manager import QueryCacheManager

# Initialize Redis for query caching
redis_cache_url = os.environ.get('REDIS_CACHE_URL', 'redis://localhost:6379/1')
redis_password = os.environ.get('REDIS_PASSWORD')

if redis_password:
    redis_cache_url = redis_cache_url.replace('redis://', f'redis://:{redis_password}@')

redis_cache_client = redis.from_url(redis_cache_url, decode_responses=True)
app.query_cache_manager = QueryCacheManager(redis_cache_client, default_ttl=300)
```

---

## Step 5: Update Environment Variables

**File:** `.env` or `.env.production`

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/mingus_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/2

# Session Configuration
SESSION_COOKIE_SECURE=false  # true in production with HTTPS
PERMANENT_SESSION_LIFETIME=86400  # 24 hours
```

---

## Step 6: Use Query Caching (Example)

**File:** `backend/api/profile_endpoints.py`

```python
from backend.services.query_cache_manager import cache_query

@profile_api.route('/profile/<user_id>', methods=['GET'])
@cache_query(ttl=300, key_prefix='user_profile')
def get_profile(user_id):
    """Get user profile with automatic caching"""
    profile = db.session.query(UserProfile).filter_by(user_id=user_id).first()
    if profile:
        return jsonify(profile.to_dict())
    return jsonify({'error': 'Profile not found'}), 404
```

**When updating, invalidate cache:**

```python
from flask import current_app

@profile_api.route('/profile', methods=['PUT'])
def update_profile():
    # ... update logic ...
    
    # Invalidate cache
    cache_manager = current_app.query_cache_manager
    cache_manager.invalidate_pattern(f"user_profile:{user_id}")
    
    return jsonify({'success': True})
```

---

## Step 7: Use Session Manager (Example)

**File:** `backend/api/auth_endpoints.py`

```python
from backend.utils.session_manager import SessionManager

@auth_bp.route('/login', methods=['POST'])
def login():
    # ... validation ...
    
    # Create session using SessionManager
    SessionManager.create_session(
        user_id=user.id,
        user_data={
            'email': user.email,
            'name': user.name
        }
    )
    
    return jsonify({'success': True})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    SessionManager.destroy_session()
    return jsonify({'success': True})
```

---

## Step 8: Test Implementation

### Test Redis Connection
```python
import redis
r = redis.from_url('redis://localhost:6379/0')
r.ping()  # Should return True
```

### Test Session Storage
```python
from flask import session
session['test'] = 'value'
print(session.get('test'))  # Should print 'value'
```

### Test Query Caching
```python
# First call - cache miss
result1 = get_profile(user_id)  # Executes query

# Second call - cache hit
result2 = get_profile(user_id)  # Returns from cache
```

---

## Step 9: Monitor Performance

### Check Cache Statistics
```python
from flask import current_app
stats = current_app.query_cache_manager.get_stats()
print(f"Cache hit rate: {stats['hit_rate']}%")
```

### Monitor Redis Memory
```bash
redis-cli INFO memory
```

### Monitor Database Queries
Check logs for slow queries (queries > 1 second)

---

## Troubleshooting

### Issue: Redis Connection Failed
**Solution:** 
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL in environment
- Check Redis password if configured

### Issue: Sessions Not Persisting
**Solution:**
- Verify Flask-Session is installed
- Check SESSION_REDIS configuration
- Verify session cookie settings

### Issue: Cache Not Working
**Solution:**
- Check Redis connection for cache
- Verify query_cache_manager is initialized
- Check cache TTL settings
- Monitor Redis memory usage

---

## Expected Results

After implementation:
- ✅ Database queries 30-50% faster
- ✅ Cached queries 70-90% faster
- ✅ Sessions persist across server restarts
- ✅ Support for multiple server instances
- ✅ Reduced database load

---

## Next Steps

1. **Monitor Performance** - Track cache hit rates and query times
2. **Tune TTLs** - Adjust cache expiration based on data freshness needs
3. **Add More Indexes** - Create indexes for frequently queried columns
4. **Scale Redis** - Consider Redis cluster for high availability

---

**Status:** Ready to implement
