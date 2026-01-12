# How to Start Flask App Correctly

## Issue Summary

1. **Port 5000 is used by Apple AirPlay** - Use port 5001 instead
2. **App may crash if Redis not available** - App will now handle this gracefully

## Correct Startup Steps

### Step 1: Set Port to 5001

```bash
export FLASK_PORT=5001
```

Or add to `.env` file:
```bash
FLASK_PORT=5001
```

### Step 2: Start Flask App

```bash
python app.py
```

**Look for:** `* Running on http://0.0.0.0:5001`

### Step 3: Test Health Endpoint

In another terminal:
```bash
curl http://localhost:5001/health
```

Should return JSON with status "healthy"

### Step 4: Run Load Tests

```bash
# Health endpoint test
python load_test_api.py --endpoint /health --requests 50

# Cache performance test
python performance_test_suite.py --endpoint /api/vehicle --compare-cache --url http://localhost:5001

# Full test suite
python load_test_api.py --full --requests 100 --concurrent 10 --save
```

## Troubleshooting

### App Crashes on Startup

If you see "Floating point exception":
1. **Check Redis** - App will work without Redis (uses filesystem sessions)
2. **Check logs** - Look for specific error messages
3. **Try without Redis** - Comment out Redis initialization temporarily

### Still Getting 403

1. **Verify correct port** - Make sure you're testing port 5001, not 5000
2. **Check app is running** - Look for "Running on" message
3. **Check security middleware** - Public endpoints should work

### Connection Refused

1. **App not started** - Make sure Flask app is running
2. **Wrong port** - Verify you're using port 5001
3. **Check firewall** - Make sure port is not blocked

## Quick Test

```bash
# Terminal 1: Start app
export FLASK_PORT=5001
python app.py

# Terminal 2: Test
curl http://localhost:5001/health
python load_test_api.py --endpoint /health --requests 10
```

---

**Status:** Ready to start on port 5001
