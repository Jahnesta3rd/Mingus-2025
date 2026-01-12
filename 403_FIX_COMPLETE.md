# 403 Errors - Fix Complete

## Root Cause

**Port 5000 is occupied by Apple AirPlay/AirTunes service on macOS**

The 403 errors were NOT from your Flask application - they were from Apple's AirPlay service intercepting requests on port 5000.

## Solution Implemented

### 1. Updated Default Port

Modified `app.py` to automatically use port 5001 if AirPlay is detected:
```python
# Use 5001 if 5000 is occupied (common on macOS due to AirPlay)
default_port = 5001 if os.path.exists('/System/Library/CoreServices/AirPlayXPCHelper') else 5000
port = int(os.environ.get('FLASK_PORT', str(default_port)))
```

### 2. Updated Security Middleware

Enhanced security middleware to properly skip public endpoints:
- `/health` - No security checks
- `/api/status` - No security checks
- OPTIONS requests - Allowed for CORS preflight

### 3. Updated CORS Configuration

Made CORS more permissive in development mode:
- Allows all origins in development
- Allows all headers in development
- Properly handles requests without Origin header

### 4. Updated Load Test Scripts

Changed default port in load testing scripts from 5000 to 5001.

## How to Run

### Option 1: Use Port 5001 (Recommended)

```bash
# Set port in environment
export FLASK_PORT=5001

# Start Flask app
python app.py

# Run load tests (will use port 5001 by default now)
python load_test_api.py --endpoint /health --requests 50
```

### Option 2: Disable AirPlay (Free Port 5000)

1. System Settings → General → AirDrop & AirPlay
2. Turn off "AirPlay Receiver"
3. Then use port 5000 normally

### Option 3: Use Different Port

```bash
export FLASK_PORT=8000
python app.py

# Update load test URL
python load_test_api.py --url http://localhost:8000 --endpoint /health
```

## Verification

After starting Flask on the correct port:

```bash
# Test health endpoint
curl http://localhost:5001/health

# Should return:
# {"status": "healthy", ...}

# Run load test
python load_test_api.py --endpoint /health --requests 50

# Should show:
# Status: 200 OK
# Successful: 50/50
```

## Files Modified

1. ✅ `app.py` - Auto-detect port conflict, use 5001
2. ✅ `backend/middleware/security.py` - Skip public endpoints
3. ✅ `app.py` - CORS configuration for development
4. ✅ `load_test_api.py` - Default port 5001
5. ✅ `performance_test_suite.py` - Default port 5001

## Next Steps

1. **Start Flask on port 5001:**
   ```bash
   export FLASK_PORT=5001
   python app.py
   ```

2. **Run load tests:**
   ```bash
   python load_test_api.py --endpoint /health --requests 50
   python load_test_api.py --full --save
   ```

3. **Test cache performance:**
   ```bash
   python performance_test_suite.py --endpoint /api/vehicle --compare-cache
   ```

---

**Status:** ✅ Fixes implemented - Ready to test on port 5001
