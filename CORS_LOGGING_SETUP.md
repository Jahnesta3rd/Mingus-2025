# CORS Failure Logging Setup

**Date:** January 12, 2026  
**Status:** ✅ **IMPLEMENTED**

---

## Overview

CORS failure logging has been set up to monitor and log all CORS-related requests, failures, and security events. This enables:

- **Security Monitoring:** Track unauthorized origin attempts
- **Debugging:** Identify CORS configuration issues
- **Analytics:** Monitor CORS request patterns
- **Compliance:** Maintain audit logs for security events

---

## Implementation

### Files Created

1. **`backend/middleware/cors_logging.py`**
   - CORS logging middleware
   - Dedicated CORS logger (`mingus.cors`)
   - Logs to `logs/cors.log` with rotation (10MB, 5 backups)

2. **`test_cors_logging.py`**
   - Test script to verify CORS logging functionality
   - Makes various CORS requests and checks log output

3. **`CORS_LOGGING_SETUP.md`** (this file)
   - Documentation for CORS logging setup

### Integration

The CORS logging middleware is automatically initialized in `app.py`:

```python
from backend.middleware.cors_logging import setup_cors_logging

# After CORS configuration
cors_logging_middleware = setup_cors_logging(app, allowed_origins=CORS_ORIGINS)
```

---

## Log File Location

**Log File:** `logs/cors.log`

The log file is automatically created in the `logs/` directory with:
- **Rotation:** 10MB max size, 5 backup files
- **Encoding:** UTF-8
- **Format:** Detailed timestamp, logger name, level, message

---

## What Gets Logged

### 1. CORS Preflight Requests (OPTIONS)

**Logged Information:**
- Origin
- Requested method
- Requested headers
- IP address
- Path
- Status (allowed/blocked)

**Example Log Entry:**
```
2026-01-12 19:30:15 - mingus.cors - INFO - CORS Preflight Request - Origin: http://localhost:3000, Path: /api/assessments, Method: POST, Headers: Content-Type,Authorization, IP: 127.0.0.1
```

### 2. Unauthorized Origin Attempts

**Logged Information:**
- ⚠️ **WARNING level** - Unauthorized origin blocked
- Origin
- Path
- Method
- IP address
- Status code
- Full details in DEBUG level

**Example Log Entry:**
```
2026-01-12 19:30:20 - mingus.cors - WARNING - CORS BLOCKED - Unauthorized origin: http://evil.com, Path: /health, Method: GET, IP: 192.168.1.100, Status: 200
```

### 3. Successful CORS Requests

**Logged Information:**
- Origin
- Path
- Method
- Status code
- CORS headers present

**Example Log Entry:**
```
2026-01-12 19:30:25 - mingus.cors - DEBUG - CORS Request ALLOWED - Origin: http://localhost:3000, Path: /health, Method: GET, Status: 200
```

### 4. CORS Configuration Issues

**Logged Information:**
- Missing CORS headers
- Origin mismatches
- Wildcard usage warnings
- Missing preflight headers

**Example Log Entry:**
```
2026-01-12 19:30:30 - mingus.cors - WARNING - CORS Preflight MISSING HEADERS - Origin: http://localhost:3000, Path: /api/endpoint, Status: 200
```

---

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Successful CORS requests, detailed information | Allowed requests, detailed headers |
| **INFO** | Normal CORS operations | Preflight requests, successful operations |
| **WARNING** | Security events, configuration issues | Unauthorized origins, missing headers |
| **ERROR** | CORS failures, missing headers | Missing Access-Control-Allow-Origin |

---

## Monitoring CORS Logs

### Real-time Monitoring

**Watch all CORS events:**
```bash
tail -f logs/cors.log
```

**Monitor only security events (blocked origins):**
```bash
tail -f logs/cors.log | grep -i "blocked\|failure\|error"
```

**Monitor unauthorized origin attempts:**
```bash
tail -f logs/cors.log | grep "CORS BLOCKED"
```

### Log Analysis

**Count unauthorized origin attempts:**
```bash
grep -c "CORS BLOCKED" logs/cors.log
```

**List all blocked origins:**
```bash
grep "CORS BLOCKED" logs/cors.log | grep -oP "origin: \K[^,]+" | sort | uniq
```

**Find most common blocked origins:**
```bash
grep "CORS BLOCKED" logs/cors.log | grep -oP "origin: \K[^,]+" | sort | uniq -c | sort -rn
```

**View CORS preflight requests:**
```bash
grep "CORS Preflight" logs/cors.log
```

**View CORS errors:**
```bash
grep "CORS ERROR" logs/cors.log
```

---

## Testing CORS Logging

### Run Test Script

```bash
python3 test_cors_logging.py
```

The test script will:
1. Make various CORS requests (allowed, blocked, preflight)
2. Wait for logs to be written
3. Display the last 20 lines of the CORS log
4. Provide summary and next steps

### Manual Testing

**Test allowed origin:**
```bash
curl -H "Origin: http://localhost:3000" http://localhost:5000/health
```

**Test unauthorized origin (should be blocked and logged):**
```bash
curl -H "Origin: http://evil.com" http://localhost:5000/health
```

**Test preflight request:**
```bash
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://localhost:5000/api/assessments
```

Then check the log:
```bash
tail -20 logs/cors.log
```

---

## Programmatic Usage

### Log CORS Failures from Code

```python
from backend.middleware.cors_logging import CORSLoggingMiddleware

# Log a CORS failure
CORSLoggingMiddleware.log_cors_failure(
    origin='http://evil.com',
    reason='Origin not in allowed list',
    details={'path': '/api/endpoint', 'method': 'POST'}
)
```

### Log CORS Success

```python
from backend.middleware.cors_logging import CORSLoggingMiddleware

# Log a successful CORS request
CORSLoggingMiddleware.log_cors_success(
    origin='http://localhost:3000',
    path='/api/endpoint',
    method='POST'
)
```

---

## Configuration

### Environment Variables

The CORS logging uses the same CORS configuration as the main app:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

### Log File Settings

**Default Settings:**
- **Location:** `logs/cors.log`
- **Max Size:** 10MB per file
- **Backups:** 5 rotated files
- **Encoding:** UTF-8

**To change log location:**
Modify `backend/middleware/cors_logging.py`:
```python
cors_log_file = os.path.join(log_dir, 'cors.log')  # Change this
```

---

## Security Considerations

### Log File Permissions

Ensure log files have appropriate permissions:
```bash
chmod 640 logs/cors.log
chown app:app logs/cors.log
```

### Sensitive Data

The CORS logger does NOT log:
- Request bodies
- Authorization tokens
- User credentials
- Session IDs

It only logs:
- Origin headers
- Request methods
- Paths
- IP addresses
- User agents (for security analysis)

### Log Rotation

Logs are automatically rotated to prevent:
- Disk space issues
- Performance degradation
- Unwieldy log files

---

## Troubleshooting

### Log File Not Created

**Issue:** `logs/cors.log` doesn't exist

**Solutions:**
1. Check that the Flask app has started
2. Verify write permissions on the `logs/` directory
3. Check that CORS logging middleware is initialized in `app.py`
4. Look for errors in the main application log

### No Logs Appearing

**Issue:** CORS requests aren't being logged

**Solutions:**
1. Verify CORS logging middleware is initialized:
   ```python
   cors_logging_middleware = setup_cors_logging(app, allowed_origins=CORS_ORIGINS)
   ```
2. Check that requests include an `Origin` header
3. Verify log level is set correctly (INFO or DEBUG)
4. Check application logs for initialization errors

### Too Many Logs

**Issue:** Log file growing too quickly

**Solutions:**
1. Increase log rotation size in `cors_logging.py`
2. Change log level from DEBUG to INFO
3. Filter logs using grep (see Monitoring section)
4. Set up log aggregation/archival

---

## Integration with Monitoring Systems

### Log Aggregation

CORS logs can be integrated with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **CloudWatch** (AWS)
- **Datadog**
- **New Relic**

### Alerting

Set up alerts for:
- High frequency of blocked origins (potential attack)
- Missing CORS headers (configuration issue)
- Unauthorized origin patterns

**Example Alert Rule:**
```bash
# Alert if more than 10 blocked origins in 1 minute
grep "CORS BLOCKED" logs/cors.log | tail -100 | grep "$(date +%Y-%m-%d)" | wc -l
```

---

## Best Practices

1. **Regular Review:** Review CORS logs weekly for security patterns
2. **Alert Setup:** Set up alerts for suspicious patterns
3. **Log Retention:** Keep logs for at least 90 days for security audits
4. **Access Control:** Limit access to CORS logs (contain IP addresses)
5. **Monitoring:** Include CORS logs in your monitoring dashboard

---

## Next Steps

1. ✅ CORS logging implemented
2. ✅ Test script created
3. ⏭️ Set up log monitoring/alerting
4. ⏭️ Integrate with monitoring system (optional)
5. ⏭️ Review logs regularly for security patterns

---

## Summary

CORS failure logging is now fully implemented and ready for use. The system will automatically log:

- ✅ All CORS preflight requests
- ✅ Unauthorized origin attempts (security events)
- ✅ Successful CORS requests
- ✅ CORS configuration issues
- ✅ Missing CORS headers

**Log Location:** `logs/cors.log`  
**Test Script:** `test_cors_logging.py`  
**Status:** ✅ **READY FOR USE**
