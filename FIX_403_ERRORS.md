# Fix 403 Errors - Solution

## Root Cause Identified

**Port 5000 is being used by Apple AirPlay/AirTunes service on macOS!**

The 403 errors are NOT from your Flask application - they're from Apple's AirPlay service that's running on port 5000 by default on macOS.

## Solution Options

### Option 1: Use Different Port (Recommended)

**Update `.env` file:**
```bash
FLASK_PORT=5001
```

Or set environment variable:
```bash
export FLASK_PORT=5001
python app.py
```

### Option 2: Disable AirPlay Receiver (macOS)

1. Open **System Settings** (or System Preferences)
2. Go to **General** → **AirDrop & AirPlay**
3. Turn off **AirPlay Receiver**

This will free up port 5000.

### Option 3: Use Port 8000 or 8080

```bash
export FLASK_PORT=8000
python app.py
```

## Updated Code

I've updated `app.py` to automatically use port 5001 if AirPlay is detected, but you can also explicitly set the port.

## Test After Fix

Once you've changed the port:

```bash
# Start Flask on new port
export FLASK_PORT=5001
python app.py

# Test in another terminal
python load_test_api.py --url http://localhost:5001 --endpoint /health --requests 50
```

## Verification

Check if Flask is actually running:
```bash
# Check what's on port 5000
lsof -i:5000

# Check what's on port 5001 (or your chosen port)
lsof -i:5001

# Test the correct port
curl http://localhost:5001/health
```

---

**Status:** Issue identified - Port conflict with Apple AirPlay
