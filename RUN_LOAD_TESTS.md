# Run Load Tests - Step by Step

## Prerequisites

1. ✅ Flask-Session and redis installed
2. ✅ Redis running (or app will use filesystem sessions)
3. ✅ Flask app can start

## Execution Steps

### Step 1: Start Redis (Optional but Recommended)

```bash
# Check if Redis is running
redis-cli ping

# If not running, start it:
# macOS (Homebrew)
brew services start redis

# Or test without Redis (app will use filesystem sessions)
```

### Step 2: Start Flask Application

**Open Terminal 1:**
```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
python app.py
```

**Wait for:** `* Running on http://0.0.0.0:5000`

### Step 3: Run Load Tests

**Open Terminal 2** (keep Terminal 1 running):

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# Test 1: Health endpoint (50 requests)
python load_test_api.py --endpoint /health --requests 50 --concurrent 5

# Test 2: Cache performance comparison
python performance_test_suite.py --endpoint /api/vehicle --compare-cache

# Test 3: Full test suite
python load_test_api.py --full --requests 100 --concurrent 10 --save
```

## Expected Output

### Health Endpoint Test
```
======================================================================
RESULTS: GET /health
======================================================================
Total Requests:        50
Successful:            50 (100.0%)
Failed:                0 (0.0%)

Response Times:
  Average:             45.23 ms
  Median:              42.10 ms
  Min:                 38.50 ms
  Max:                 125.30 ms
  95th Percentile:     89.45 ms
  99th Percentile:     112.20 ms

Throughput:
  Requests/Second:     11.05
======================================================================
```

### Cache Performance Test
```
======================================================================
Cache Performance Comparison: /api/vehicle
======================================================================

Without Cache (Cold):
  Avg Response Time: 450.23 ms
  Requests/Second:  2.22

With Cache (Warm):
  Avg Response Time: 89.45 ms
  Requests/Second:  11.18

Performance Improvement: 80.1% faster with cache
```

## Automated Script

You can also use the automated script:

```bash
./run_load_tests.sh
```

This script will:
1. Check if Flask app is running
2. Run health endpoint test
3. Test cache performance
4. Run full test suite
5. Save results

## Troubleshooting

### "Connection refused" errors
- Make sure Flask app is running in another terminal
- Check: `curl http://localhost:5000/health`

### All requests fail
- Verify app started successfully
- Check app logs for errors
- Try: `python load_test_api.py --endpoint /health --requests 10`

### Redis connection errors
- App will automatically use filesystem sessions
- This is fine for testing, but cache won't work
- To enable caching: start Redis first

## Results Files

Test results are saved as:
- `load_test_results_YYYYMMDD_HHMMSS.json`
- `performance_test_YYYYMMDD_HHMMSS.json`

Review these files to analyze performance over time.
