# System Resource Monitoring & Performance Optimization Guide

## Overview

The Mingus application now includes comprehensive system resource monitoring and performance optimizations to ensure optimal operation and early detection of issues.

## Features

### 1. System Resource Monitoring

- **CPU Monitoring**: Real-time CPU usage tracking with alerts
- **Memory Monitoring**: Memory usage, available memory, and percentage tracking
- **Disk Monitoring**: Disk space usage and availability
- **Network Monitoring**: Bytes sent/received, packet counts
- **Process Monitoring**: Process and thread counts
- **Load Average**: System load tracking (Unix systems)

### 2. Application Metrics

- **Request Tracking**: Request count, rate, and response times
- **Error Tracking**: Error rate and error categorization
- **Cache Metrics**: Cache hit/miss rates
- **Connection Tracking**: Active, database, and Redis connections

### 3. Alerting System

- **Threshold-based Alerts**: Configurable thresholds for all metrics
- **Alert Levels**: Warning and Critical alerts
- **Auto-resolution**: Alerts automatically resolve when conditions improve

### 4. Performance Optimizations

- **Database Connection Pooling**: Optimized pool size and overflow settings
- **Request Size Limits**: Configurable maximum content length
- **Session Management**: Optimized session lifetime
- **File Caching**: Static file caching headers

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# System Monitoring Configuration
MONITORING_INTERVAL=10              # Seconds between metric collection
ENABLE_PROMETHEUS=false             # Enable Prometheus metrics export
PROMETHEUS_PORT=9090                # Prometheus metrics server port

# Alert Thresholds
ALERT_CPU_THRESHOLD=80.0            # CPU usage percentage
ALERT_MEMORY_THRESHOLD=85.0         # Memory usage percentage
ALERT_DISK_THRESHOLD=90.0           # Disk usage percentage
ALERT_ERROR_RATE_THRESHOLD=5.0      # Error rate percentage
ALERT_RESPONSE_TIME_THRESHOLD=1000.0 # Response time in milliseconds
ALERT_CACHE_HIT_RATE_THRESHOLD=0.70 # Cache hit rate (0.70 = 70%)

# Database Performance Settings
DB_POOL_SIZE=10                     # Connection pool size
DB_MAX_OVERFLOW=20                  # Maximum overflow connections
DB_POOL_TIMEOUT=30                  # Pool timeout in seconds
DB_POOL_RECYCLE=3600                # Connection recycle time (1 hour)
DB_POOL_PRE_PING=true               # Enable connection health checks

# Request Limits
MAX_CONTENT_LENGTH=16777216         # 16MB maximum request size
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns overall system health including monitoring status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-12T...",
  "version": "1.0.0",
  "services": {...},
  "monitoring": {
    "status": "healthy",
    "alerts": {
      "critical": 0,
      "warning": 0,
      "total": 0
    },
    "system": {
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_percent": 60.1
    },
    "application": {
      "request_rate": 12.5,
      "error_rate": 0.5,
      "avg_response_time_ms": 125.3
    }
  }
}
```

### Detailed Metrics

```bash
GET /api/metrics
```

Returns comprehensive system and application metrics.

**Response:**
```json
{
  "system": {
    "timestamp": "2026-01-12T...",
    "cpu_percent": 25.5,
    "cpu_count": 8,
    "memory_total": 17179869184,
    "memory_used": 8589934592,
    "memory_percent": 50.0,
    "memory_available": 8589934592,
    "disk_total": 500000000000,
    "disk_used": 300000000000,
    "disk_percent": 60.0,
    "disk_free": 200000000000,
    "network_bytes_sent": 1024000,
    "network_bytes_recv": 2048000,
    "load_avg": 1.5,
    "process_count": 150,
    "thread_count": 300
  },
  "application": {
    "timestamp": "2026-01-12T...",
    "request_count": 1250,
    "request_rate": 12.5,
    "avg_response_time": 125.3,
    "error_rate": 0.5,
    "active_connections": 25,
    "cache_hit_rate": 0.85,
    "database_connections": 5,
    "redis_connections": 2
  },
  "alerts": [...],
  "timestamp": "2026-01-12T..."
}
```

### Health Status

```bash
GET /api/metrics/health
```

Returns system health status with alert summary.

### Performance Recommendations

```bash
GET /api/metrics/recommendations
```

Returns actionable performance recommendations based on current metrics.

**Response:**
```json
{
  "recommendations": [
    "High CPU usage (75.2%). Consider: optimizing queries, adding caching, or scaling horizontally.",
    "Low cache hit rate (45.1%). Consider: increasing cache TTL, warming cache, or expanding cache coverage."
  ],
  "timestamp": 1705094400
}
```

## Prometheus Integration

If Prometheus is enabled (`ENABLE_PROMETHEUS=true`), metrics are available at:

```
http://localhost:9090/metrics
```

### Available Metrics

- `system_cpu_usage_percent` - CPU usage percentage
- `system_memory_usage_bytes` - Memory usage in bytes
- `system_memory_usage_percent` - Memory usage percentage
- `system_disk_usage_bytes` - Disk usage in bytes
- `system_disk_usage_percent` - Disk usage percentage
- `system_network_bytes_sent` - Network bytes sent
- `system_network_bytes_recv` - Network bytes received
- `app_requests_total` - Total requests (labeled by method, endpoint, status)
- `app_request_duration_seconds` - Request duration histogram
- `app_errors_total` - Total errors (labeled by type)
- `app_cache_hits_total` - Cache hits
- `app_cache_misses_total` - Cache misses
- `app_active_connections` - Active connections
- `app_database_connections` - Database connections

## Monitoring Best Practices

### 1. Set Appropriate Thresholds

Adjust alert thresholds based on your system capacity:

- **Development**: Higher thresholds (less sensitive)
- **Production**: Lower thresholds (more sensitive)

### 2. Monitor Key Metrics

Focus on:
- **CPU Usage**: Should stay below 80% under normal load
- **Memory Usage**: Should stay below 85% to allow for spikes
- **Error Rate**: Should stay below 5%
- **Response Time**: Should average below 1 second
- **Cache Hit Rate**: Should be above 70%

### 3. Regular Review

- Review metrics daily in production
- Check recommendations weekly
- Adjust thresholds based on actual usage patterns

### 4. Alert Response

When alerts trigger:
1. Check `/api/metrics/health` for details
2. Review `/api/metrics/recommendations` for actions
3. Investigate root cause
4. Implement fixes
5. Adjust thresholds if needed

## Performance Optimizations

### Database Connection Pooling

The application uses SQLAlchemy connection pooling with these optimizations:

- **Pool Size**: 10 connections (configurable)
- **Max Overflow**: 20 additional connections
- **Connection Recycle**: 1 hour (prevents stale connections)
- **Pre-ping**: Enabled (validates connections before use)

### Request Handling

- **Max Content Length**: 16MB (prevents memory exhaustion)
- **Rate Limiting**: 100 requests/minute (configurable)
- **Request Timeout**: Handled by web server (nginx/gunicorn)

### Caching

- **Query Cache**: Redis-based with 5-minute default TTL
- **Session Cache**: Redis-based with 24-hour lifetime
- **Static Files**: 1-year cache headers

## Troubleshooting

### High CPU Usage

1. Check `/api/metrics` for CPU percentage
2. Review `/api/metrics/recommendations`
3. Check for:
   - Inefficient database queries
   - Missing indexes
   - Heavy background tasks
   - Too many concurrent requests

### High Memory Usage

1. Check memory metrics
2. Review recommendations
3. Consider:
   - Reducing cache size
   - Optimizing data structures
   - Increasing available memory
   - Scaling horizontally

### High Error Rate

1. Check error rate in metrics
2. Review application logs
3. Check for:
   - Database connection issues
   - External API failures
   - Validation errors
   - Rate limiting

### Slow Response Times

1. Check average response time
2. Review cache hit rate
3. Consider:
   - Database query optimization
   - Increasing cache coverage
   - Adding database indexes
   - Code profiling

## Integration with Monitoring Tools

### Grafana

Use Prometheus as data source and create dashboards for:
- System resource usage
- Request rates and response times
- Error rates
- Cache performance

### Alerting

Set up alerting rules in Prometheus Alertmanager:
- CPU > 80% for 5 minutes
- Memory > 85% for 5 minutes
- Error rate > 5% for 5 minutes
- Response time > 1s average for 5 minutes

## Example Monitoring Script

```python
import requests
import time

def check_system_health():
    """Check system health and print status"""
    response = requests.get('http://localhost:5001/api/metrics/health')
    health = response.json()
    
    print(f"Status: {health['status']}")
    print(f"Alerts: {health['alerts']}")
    print(f"System: {health['system']}")
    print(f"Application: {health['application']}")
    
    if health['status'] != 'healthy':
        print("\n⚠️  System is not healthy!")
        recommendations = requests.get('http://localhost:5001/api/metrics/recommendations')
        for rec in recommendations.json()['recommendations']:
            print(f"  - {rec}")

if __name__ == '__main__':
    while True:
        check_system_health()
        time.sleep(60)  # Check every minute
```

## Next Steps

1. **Enable Prometheus** (if using monitoring tools):
   ```bash
   ENABLE_PROMETHEUS=true
   ```

2. **Set up Grafana** dashboards for visualization

3. **Configure alerting** in your monitoring stack

4. **Review metrics regularly** and adjust thresholds

5. **Implement recommendations** from the monitoring system

---

**Status**: ✅ System monitoring fully integrated and operational
