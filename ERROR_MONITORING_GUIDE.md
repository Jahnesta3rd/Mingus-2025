# Error Monitoring and Logging Guide

## Overview

The Mingus application includes comprehensive error monitoring and logging to track, categorize, and alert on errors across the system.

## Features

### 1. Structured Error Logging

- **Automatic Error Categorization**: Errors are automatically categorized (database, network, validation, etc.)
- **Severity Levels**: Errors are classified as Low, Medium, High, or Critical
- **Full Context**: Each error includes stack traces, request context, user info, and custom context
- **Multiple Log Formats**: Standard logs, JSON logs for aggregation, and structured error logs

### 2. Error Tracking

- **Error History**: Maintains a rolling history of errors (configurable size)
- **Error Statistics**: Real-time statistics by severity, category, and time period
- **Error Search**: Filter errors by severity, category, or time range
- **Error Aggregation**: Groups similar errors for analysis

### 3. Alerting

- **Threshold-based Alerts**: Configurable thresholds for error rates
- **Alert Levels**: Warning and Critical alerts
- **Automatic Alerting**: Alerts trigger when thresholds are exceeded

### 4. External Integration

- **Sentry Integration**: Optional integration with Sentry for error tracking
- **Log Aggregation**: JSON logs compatible with log aggregation tools (ELK, Splunk, etc.)

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Logging Configuration
LOG_DIR=logs                    # Directory for log files
LOG_LEVEL=INFO                  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Error Monitoring
ENABLE_SENTRY=false            # Enable Sentry error tracking
SENTRY_DSN=                    # Sentry DSN (required if ENABLE_SENTRY=true)
MAX_ERROR_HISTORY=10000        # Maximum errors to keep in memory

# Error Alert Thresholds
ERROR_ALERT_CRITICAL_PER_HOUR=10   # Critical errors per hour
ERROR_ALERT_HIGH_PER_HOUR=50       # High severity errors per hour
ERROR_ALERT_TOTAL_PER_HOUR=200     # Total errors per hour
```

### Sentry Setup (Optional)

1. **Create Sentry Account**: Go to https://sentry.io and create an account
2. **Create Project**: Create a new project for your application
3. **Get DSN**: Copy the DSN from your project settings
4. **Configure**:
   ```bash
   ENABLE_SENTRY=true
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   ```
5. **Install Sentry SDK** (if not already installed):
   ```bash
   pip install sentry-sdk
   ```

## Log Files

The system creates several log files in the `logs/` directory:

- **`app.log`**: All application logs (INFO level and above)
- **`errors.log`**: Error logs only (ERROR level and above)
- **`errors.json.log`**: JSON-formatted error logs for log aggregation

All log files are automatically rotated:
- **Max Size**: 10MB per file
- **Backups**: 10-20 backup files (more for error logs)
- **Encoding**: UTF-8

## API Endpoints

### Error Statistics

```bash
GET /api/errors/stats?hours=24
```

Returns error statistics for the specified time period.

**Response:**
```json
{
  "total": 150,
  "by_severity": {
    "low": 50,
    "medium": 70,
    "high": 25,
    "critical": 5
  },
  "by_category": {
    "database": 20,
    "network": 15,
    "validation": 80,
    "authentication": 10,
    "authorization": 5,
    "business_logic": 10,
    "external_api": 5,
    "system": 5,
    "unknown": 0
  },
  "recent_errors": [...],
  "alerts": [...]
}
```

### Error List

```bash
GET /api/errors?severity=high&category=database&limit=50
```

Returns filtered list of errors.

**Query Parameters:**
- `severity`: Filter by severity (low, medium, high, critical)
- `category`: Filter by category
- `limit`: Maximum number of errors to return (default: 100)

**Response:**
```json
{
  "errors": [
    {
      "timestamp": "2026-01-12T10:30:00",
      "severity": "high",
      "category": "database",
      "error_type": "DatabaseError",
      "error_message": "Connection timeout",
      "stack_trace": "...",
      "endpoint": "/api/users",
      "request_method": "GET",
      "request_path": "/api/users",
      "request_ip": "192.168.1.1",
      "user_id": "user123",
      "context": {}
    }
  ],
  "count": 25,
  "filters": {
    "severity": "high",
    "category": "database",
    "limit": 50
  }
}
```

### Error Health

```bash
GET /api/errors/health
```

Returns error monitoring health status.

**Response:**
```json
{
  "status": "healthy",
  "stats": {
    "total": 5,
    "by_severity": {...},
    "by_category": {...},
    "recent_errors": [...],
    "alerts": []
  },
  "timestamp": "2026-01-12T10:30:00"
}
```

## Error Categories

Errors are automatically categorized:

- **DATABASE**: SQL errors, connection issues, query failures
- **NETWORK**: Connection timeouts, network errors, HTTP errors
- **VALIDATION**: Input validation errors, data format errors
- **AUTHENTICATION**: Login failures, token errors
- **AUTHORIZATION**: Permission errors, access denied
- **BUSINESS_LOGIC**: Application logic errors
- **EXTERNAL_API**: Third-party API failures
- **SYSTEM**: System-level errors, critical failures
- **UNKNOWN**: Unclassified errors

## Error Severity

Errors are automatically assigned severity:

- **CRITICAL**: System failures, data corruption, critical bugs
- **HIGH**: Database errors, external API failures, security issues
- **MEDIUM**: Validation errors, authentication issues (default)
- **LOW**: Business logic errors, expected errors

## Using Error Monitoring in Code

### Manual Error Logging

```python
from backend.monitoring.error_monitor import get_error_monitor, ErrorSeverity, ErrorCategory

error_monitor = get_error_monitor()

try:
    # Your code here
    result = risky_operation()
except Exception as e:
    # Log the error
    error_monitor.log_error(
        error=e,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DATABASE,
        user_id=current_user.id if current_user else None,
        context={'operation': 'risky_operation', 'params': {...}}
    )
    raise
```

### Automatic Error Handling

The system automatically logs:
- All HTTP errors (4xx, 5xx)
- Unhandled exceptions
- Flask error handler exceptions

## Alert Thresholds

Alerts are triggered when:

- **Critical Errors**: More than 10 critical errors per hour
- **High Errors**: More than 50 high-severity errors per hour
- **Total Errors**: More than 200 total errors per hour

Adjust thresholds in `.env`:
```bash
ERROR_ALERT_CRITICAL_PER_HOUR=10
ERROR_ALERT_HIGH_PER_HOUR=50
ERROR_ALERT_TOTAL_PER_HOUR=200
```

## Log Aggregation

### JSON Logs

Error logs are written in JSON format to `logs/errors.json.log` for easy integration with log aggregation tools:

```json
{
  "timestamp": "2026-01-12T10:30:00",
  "severity": "high",
  "category": "database",
  "error_type": "DatabaseError",
  "error_message": "Connection timeout",
  "stack_trace": "...",
  "endpoint": "/api/users",
  "request_method": "GET",
  "request_path": "/api/users",
  "request_ip": "192.168.1.1",
  "user_id": "user123",
  "context": {}
}
```

### Integration with ELK Stack

1. **Filebeat Configuration**:
   ```yaml
   filebeat.inputs:
     - type: log
       paths:
         - /path/to/logs/errors.json.log
       json.keys_under_root: true
       json.add_error_key: true
   ```

2. **Logstash Parsing**: JSON logs are already structured, minimal parsing needed

3. **Kibana Dashboards**: Create dashboards for:
   - Error trends over time
   - Errors by category
   - Errors by severity
   - Top error types
   - Error rate alerts

## Best Practices

### 1. Error Context

Always provide context when logging errors:
```python
error_monitor.log_error(
    error=e,
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.DATABASE,
    context={
        'user_id': user.id,
        'operation': 'update_profile',
        'data': sanitized_data
    }
)
```

### 2. Severity Levels

Use appropriate severity:
- **CRITICAL**: System failures, data loss
- **HIGH**: Service failures, security issues
- **MEDIUM**: Validation errors, expected errors
- **LOW**: Business logic, informational

### 3. Error Filtering

Don't log expected errors (e.g., 404s for missing resources):
```python
if error.code == 404:
    return  # Don't log 404s
```

### 4. Sensitive Data

Never log sensitive data (passwords, tokens, PII):
```python
context = {
    'user_id': user.id,  # OK
    'email': user.email,  # OK (if not sensitive)
    'password': '***',    # Never log passwords
    'token': '***'        # Never log tokens
}
```

### 5. Regular Review

- Review error statistics daily
- Investigate critical and high-severity errors immediately
- Monitor error trends over time
- Adjust thresholds based on actual usage

## Troubleshooting

### High Error Rate

1. Check `/api/errors/stats` for error breakdown
2. Review `/api/errors?severity=high` for high-severity errors
3. Check logs in `logs/errors.log`
4. Review Sentry dashboard (if enabled)

### Missing Errors

1. Check log file permissions
2. Verify `LOG_DIR` is writable
3. Check disk space
4. Review log rotation settings

### Sentry Not Working

1. Verify `ENABLE_SENTRY=true`
2. Check `SENTRY_DSN` is correct
3. Verify `sentry-sdk` is installed: `pip install sentry-sdk`
4. Check Sentry project settings

## Monitoring Integration

Error statistics are integrated with the system monitor:

- Error rate is tracked in `/api/metrics`
- Errors trigger alerts in system monitoring
- Error health is included in `/health` endpoint

## Example Queries

### Get Recent Critical Errors
```bash
curl "http://localhost:5001/api/errors?severity=critical&limit=10"
```

### Get Database Errors in Last 24 Hours
```bash
curl "http://localhost:5001/api/errors/stats?hours=24" | jq '.by_category.database'
```

### Check Error Health
```bash
curl "http://localhost:5001/api/errors/health"
```

## Next Steps

1. **Enable Sentry** (optional): Set up Sentry for advanced error tracking
2. **Configure Alerts**: Adjust thresholds based on your needs
3. **Set Up Log Aggregation**: Integrate with ELK, Splunk, or similar
4. **Create Dashboards**: Visualize error trends and patterns
5. **Review Regularly**: Check error statistics daily

---

**Status**: ✅ Error monitoring fully integrated and operational
