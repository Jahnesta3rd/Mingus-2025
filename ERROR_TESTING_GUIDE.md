# Error Monitoring and Alerting Test Guide

## Overview

This guide provides comprehensive testing procedures for the error monitoring and alerting system.

## Quick Test

### Automated Test Script

Run the comprehensive test suite:

```bash
# Make sure Flask app is running
export FLASK_PORT=5001
python app.py

# In another terminal, run tests
python test_error_monitoring.py
```

### Quick Shell Test

```bash
# Run quick test script
./test_error_alerting.sh

# Or with custom URL
./test_error_alerting.sh http://localhost:5001
```

## Manual Testing

### 1. Test Error Endpoints

```bash
# Error statistics (last 24 hours)
curl http://localhost:5001/api/errors/stats?hours=24 | jq

# Error list (last 10 errors)
curl http://localhost:5001/api/errors?limit=10 | jq

# Error health status
curl http://localhost:5001/api/errors/health | jq

# Filter by severity
curl "http://localhost:5001/api/errors?severity=high&limit=5" | jq

# Filter by category
curl "http://localhost:5001/api/errors?category=database&limit=5" | jq
```

### 2. Generate Test Errors

```bash
# Generate 404 errors (should be logged)
for i in {1..5}; do
    curl http://localhost:5001/api/test-endpoint-$i
    sleep 0.5
done

# Check if errors were logged
curl http://localhost:5001/api/errors/stats?hours=1 | jq '.total'
```

### 3. Test Alerting

```bash
# Check active alerts
curl http://localhost:5001/api/dashboard/alerts | jq

# Check error alerts in statistics
curl http://localhost:5001/api/errors/stats?hours=1 | jq '.alerts'

# Check system alerts
curl http://localhost:5001/api/metrics/health | jq '.alerts'
```

### 4. Test Error Categorization

```bash
# View errors by category
curl http://localhost:5001/api/errors/stats?hours=24 | jq '.by_category'

# View errors by severity
curl http://localhost:5001/api/errors/stats?hours=24 | jq '.by_severity'

# Filter errors by category
curl "http://localhost:5001/api/errors?category=network&limit=10" | jq
```

### 5. Test Dashboard Integration

```bash
# Dashboard overview (includes errors)
curl http://localhost:5001/api/dashboard/overview | jq '.errors'

# Dashboard errors endpoint
curl http://localhost:5001/api/dashboard/errors?hours=24 | jq
```

## Testing Error Thresholds

### Check Current Thresholds

Error alert thresholds are configured in `.env`:

```bash
ERROR_ALERT_CRITICAL_PER_HOUR=10
ERROR_ALERT_HIGH_PER_HOUR=50
ERROR_ALERT_TOTAL_PER_HOUR=200
```

### Test Threshold Alerts

1. **Check current error rates:**
   ```bash
   curl http://localhost:5001/api/errors/stats?hours=1 | jq
   ```

2. **Generate errors to exceed threshold:**
   ```bash
   # Generate many errors (if needed for testing)
   for i in {1..100}; do
       curl http://localhost:5001/api/test-$i > /dev/null 2>&1
   done
   ```

3. **Check for alerts:**
   ```bash
   curl http://localhost:5001/api/dashboard/alerts | jq
   ```

## Expected Test Results

### Error Statistics Endpoint

**Expected Response:**
```json
{
  "total": 0,
  "by_severity": {
    "low": 0,
    "medium": 0,
    "high": 0,
    "critical": 0
  },
  "by_category": {
    "database": 0,
    "network": 0,
    "validation": 0,
    ...
  },
  "recent_errors": [],
  "alerts": []
}
```

### Error List Endpoint

**Expected Response:**
```json
{
  "errors": [
    {
      "timestamp": "2026-01-12T...",
      "severity": "medium",
      "category": "unknown",
      "error_type": "NotFound",
      "error_message": "404 Not Found",
      "endpoint": "/api/test-endpoint",
      ...
    }
  ],
  "count": 1,
  "filters": {...}
}
```

### Error Health Endpoint

**Expected Response:**
```json
{
  "status": "healthy",
  "stats": {
    "total": 0,
    "by_severity": {...},
    "by_category": {...},
    "recent_errors": [],
    "alerts": []
  },
  "timestamp": "2026-01-12T..."
}
```

## Test Scenarios

### Scenario 1: Normal Operation

1. **Start application**
2. **Make normal requests**
3. **Check error statistics** - Should show minimal errors
4. **Verify no alerts** - Should have no active alerts

### Scenario 2: Error Generation

1. **Generate various error types:**
   - 404 errors (not found)
   - 500 errors (if possible)
   - Validation errors
2. **Check error statistics** - Should show errors
3. **Verify error categorization** - Errors should be categorized
4. **Check error list** - Should see generated errors

### Scenario 3: Alert Triggering

1. **Generate many errors** to exceed thresholds
2. **Wait for monitoring cycle** (default: 10 seconds)
3. **Check alerts endpoint** - Should show active alerts
4. **Verify alert details** - Alerts should have messages and levels

### Scenario 4: Error Filtering

1. **Generate errors of different severities**
2. **Filter by severity:**
   ```bash
   curl "http://localhost:5001/api/errors?severity=high" | jq
   ```
3. **Filter by category:**
   ```bash
   curl "http://localhost:5001/api/errors?category=database" | jq
   ```
4. **Verify filters work** - Should return only matching errors

## Verification Checklist

- [ ] Error statistics endpoint accessible
- [ ] Error list endpoint accessible
- [ ] Error health endpoint accessible
- [ ] Errors are being logged
- [ ] Errors are categorized correctly
- [ ] Errors have severity levels
- [ ] Error filtering works (by severity, category)
- [ ] Alerts are generated when thresholds exceeded
- [ ] Alerts are visible in dashboard
- [ ] Error statistics update in real-time
- [ ] Dashboard shows error data
- [ ] Error logs are written to files

## Troubleshooting

### Errors Not Being Logged

1. **Check error monitor is initialized:**
   - Look for "Error monitoring initialized" in logs
   - Check `/health` endpoint includes monitoring status

2. **Check log files:**
   ```bash
   ls -lh logs/errors.log
   tail -f logs/errors.log
   ```

3. **Verify error monitor is running:**
   - Check application logs for error monitor messages

### Alerts Not Triggering

1. **Check thresholds:**
   ```bash
   grep ERROR_ALERT env.example
   ```

2. **Verify error count:**
   ```bash
   curl http://localhost:5001/api/errors/stats?hours=1 | jq '.total'
   ```

3. **Check alert logic:**
   - Alerts check errors in last hour
   - Wait for monitoring cycle to complete

### Dashboard Not Showing Errors

1. **Check dashboard API:**
   ```bash
   curl http://localhost:5001/api/dashboard/overview | jq '.errors'
   ```

2. **Verify dashboard endpoint:**
   ```bash
   curl http://localhost:5001/api/dashboard/errors | jq
   ```

3. **Check browser console** for JavaScript errors

## Performance Testing

### Load Test with Errors

```bash
# Generate many requests (some will be errors)
python load_test_api.py --endpoint /api/nonexistent --requests 100

# Check error statistics
curl http://localhost:5001/api/errors/stats?hours=1 | jq
```

### Error Rate Under Load

```bash
# Run load test
python load_test_api.py --full --requests 500

# Monitor error rate
watch -n 5 'curl -s http://localhost:5001/api/errors/stats?hours=1 | jq ".total"'
```

## Integration Testing

### Test with System Monitor

1. **Check system monitor includes error rate:**
   ```bash
   curl http://localhost:5001/api/metrics | jq '.application.error_rate'
   ```

2. **Verify error rate in health status:**
   ```bash
   curl http://localhost:5001/api/metrics/health | jq '.application.error_rate'
   ```

### Test with Dashboard

1. **Open dashboard:**
   ```
   http://localhost:5001/dashboard
   ```

2. **Verify error statistics display**
3. **Check error charts update**
4. **Verify alerts are shown**

## Next Steps

1. **Run comprehensive tests:**
   ```bash
   python test_error_monitoring.py
   ```

2. **Review test results**
3. **Check error logs:**
   ```bash
   tail -f logs/errors.log
   ```

4. **Monitor dashboard:**
   ```
   http://localhost:5001/dashboard
   ```

5. **Set up alerting** (if using external tools)

---

**Status**: ✅ Test suite ready

**Run Tests**: `python test_error_monitoring.py`
