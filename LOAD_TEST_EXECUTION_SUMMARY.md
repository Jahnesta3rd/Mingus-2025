# Load Test Execution Summary

## Current Status

⚠️ **Flask app crashed during startup** - Floating point exception  
⚠️ **Redis not accessible** - Connection refused

## Issue Analysis

The Flask app is trying to initialize Redis sessions but Redis is not running or not accessible. This causes the app to crash during startup.

## Solution Steps

### Step 1: Start Redis

**Option A: If Redis is installed via Homebrew (macOS)**
```bash
brew services start redis
# Verify: redis-cli ping (should return PONG)
```

**Option B: If Redis is in Docker**
```bash
docker-compose up -d redis
# Or: docker run -d -p 6379:6379 redis:7-alpine
```

**Option C: Install Redis (if not installed)**
```bash
# macOS
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

### Step 2: Verify Redis is Running

```bash
redis-cli ping
# Expected output: PONG
```

### Step 3: Start Flask App

In a **separate terminal window**:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
python app.py
```

Wait for the message: `* Running on http://0.0.0.0:5000`

### Step 4: Run Load Tests

In **another terminal window** (keep Flask app running):

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# 1. Test health endpoint (50 requests)
python load_test_api.py --endpoint /health --requests 50 --concurrent 5

# 2. Test cache performance
python performance_test_suite.py --endpoint /api/vehicle --compare-cache

# 3. Run full test suite
python load_test_api.py --full --requests 100 --concurrent 10 --save
```

## Alternative: Run Without Redis (Temporary)

If you want to test without Redis, you can modify `app.py` to skip Redis initialization temporarily:

1. Comment out the Redis session initialization:
```python
# Initialize Redis-based session storage
# try:
#     init_redis_session(app)
#     logger.info("Redis session storage initialized successfully")
# except Exception as e:
#     logger.warning(f"Failed to initialize Redis sessions, falling back to filesystem: {e}")
```

2. The app will use filesystem sessions instead
3. Note: Query caching won't work without Redis

## Expected Test Results

### Health Endpoint Test
- **Expected Response Time:** < 50ms average
- **Expected Success Rate:** 100%
- **Expected Throughput:** > 50 requests/second

### Cache Performance Test
- **Cold (No Cache):** Slower response times
- **Warm (With Cache):** 70-90% faster response times
- **Cache Hit Rate:** Should improve after warmup

### Full Test Suite
- Tests multiple endpoints
- Generates performance report
- Saves results to JSON file

## Quick Test Commands

Once everything is running:

```bash
# Quick health check
curl http://localhost:5000/health

# Light load test
python load_test_api.py --endpoint /health --requests 50

# Medium load test  
python load_test_api.py --endpoint /api/status --requests 200 --concurrent 20

# Cache comparison
python performance_test_suite.py --endpoint /api/vehicle --compare-cache

# Full suite with results saved
python load_test_api.py --full --save
```

## Troubleshooting

### App Won't Start
- Check Redis is running: `redis-cli ping`
- Check port 5000 is free: `lsof -ti:5000`
- Check for Python errors in terminal

### All Requests Fail
- Verify app is running: `curl http://localhost:5000/health`
- Check app logs for errors
- Verify CORS settings if testing from different origin

### Slow Response Times
- Check database connection
- Verify Redis is working
- Monitor server resources (CPU, memory)

## Files Created

1. ✅ `load_test_api.py` - Main load testing tool
2. ✅ `performance_test_suite.py` - Cache performance testing
3. ✅ `LOAD_TESTING_GUIDE.md` - Complete documentation
4. ✅ `run_load_tests.sh` - Automated test script
5. ✅ `APP_STARTUP_FIX.md` - Troubleshooting guide

## Next Steps

1. **Start Redis** (if not running)
2. **Start Flask app** in separate terminal
3. **Run load tests** using the commands above
4. **Review results** and optimize based on findings

---

**Status:** Ready to test once Redis and Flask app are running
