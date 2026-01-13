# Flask App Startup Issue - Fix Guide

## Issue Detected

The Flask app crashed with a "Floating point exception" during startup. This is likely related to Redis session initialization.

## Quick Fix Options

### Option 1: Check Redis Connection

Make sure Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

If Redis is not running, start it:

```bash
# macOS (Homebrew)
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker-compose up -d redis
```

### Option 2: Temporarily Disable Redis Sessions

If Redis is not available, you can temporarily comment out the Redis session initialization in `app.py`:

```python
# Initialize Redis-based session storage
try:
    init_redis_session(app)
    logger.info("Redis session storage initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Redis sessions: {e}")
    # Continue without Redis sessions
```

### Option 3: Check for Missing Dependencies

Make sure all dependencies are installed:

```bash
pip install Flask-Session redis
```

### Option 4: Check Environment Variables

Verify your `.env` file has correct Redis configuration:

```bash
cat .env | grep REDIS
```

Should show:
```
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_PASSWORD=
```

## Manual Testing Steps

1. **Start Redis** (if not running):
   ```bash
   redis-cli ping
   ```

2. **Start Flask app** in a separate terminal:
   ```bash
   python app.py
   ```

3. **Wait for startup** (look for "Running on http://..." message)

4. **Run load tests** in another terminal:
   ```bash
   # Test health endpoint
   python load_test_api.py --endpoint /health --requests 50
   
   # Test cache performance
   python performance_test_suite.py --endpoint /api/vehicle --compare-cache
   
   # Full test suite
   python load_test_api.py --full --save
   ```

## Alternative: Run Tests Without Redis

If you want to test without Redis sessions, you can modify `app.py` to skip Redis initialization:

```python
# Comment out or modify this section:
# try:
#     init_redis_session(app)
#     logger.info("Redis session storage initialized successfully")
# except Exception as e:
#     logger.warning(f"Failed to initialize Redis sessions, falling back to filesystem: {e}")
```

The app will fall back to filesystem sessions automatically if Redis fails.

## Expected Startup Output

When the app starts successfully, you should see:

```
INFO:__main__:Starting Mingus Personal Finance App on 0.0.0.0:5000
INFO:__main__:Debug mode: True
INFO:__main__:CORS origins: ['http://localhost:3000', ...]
INFO:__main__:Rate limit: 100 per minute
 * Running on http://0.0.0.0:5000
```

## Next Steps

Once the app is running:

1. ✅ Run health check: `curl http://localhost:5000/health`
2. ✅ Run load test: `python load_test_api.py --endpoint /health --requests 50`
3. ✅ Test cache: `python performance_test_suite.py --endpoint /api/vehicle --compare-cache`
4. ✅ Full suite: `python load_test_api.py --full --save`
