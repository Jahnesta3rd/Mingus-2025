# Monitoring Integration Guide

This document provides comprehensive information about the monitoring integration for the Mingus Flask application, including Prometheus metrics, alerting, and health check endpoints.

## Table of Contents

1. [Overview](#overview)
2. [Prometheus Metrics](#prometheus-metrics)
3. [Health Check Endpoints](#health-check-endpoints)
4. [Alerting System](#alerting-system)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Deployment](#deployment)

## Overview

The monitoring integration provides comprehensive observability for the Mingus Flask application through:

- **Prometheus Metrics**: Real-time metrics collection and export
- **Health Check Endpoints**: Multiple health check endpoints for different monitoring scenarios
- **Alerting System**: Automated alerting for failures and threshold violations
- **Response Time Monitoring**: Detailed performance metrics for all components

## Prometheus Metrics

### Available Metrics

#### Health Check Metrics
- `health_check_duration_seconds`: Response time for health checks
- `health_check_failures_total`: Total number of health check failures
- `health_check_status`: Current status of health checks (1=healthy, 0=unhealthy)

#### Application Metrics
- `app_request_duration_seconds`: Request processing time
- `app_request_total`: Total number of requests

#### System Metrics
- `system_memory_bytes`: Memory usage in bytes
- `system_cpu_percent`: CPU usage percentage
- `system_disk_bytes`: Disk usage in bytes

#### Database Metrics
- `db_connection_pool_size`: Database connection pool size
- `db_connection_pool_used`: Number of connections currently in use

#### Redis Metrics
- `redis_memory_bytes`: Redis memory usage
- `redis_connected_clients`: Number of connected clients

### Metrics Endpoint

**URL:** `GET /metrics`

**Response:** Prometheus-formatted metrics

**Example:**
```bash
curl http://localhost:5003/metrics
```

**Sample Output:**
```
# HELP health_check_duration_seconds Time spent performing health checks
# TYPE health_check_duration_seconds histogram
health_check_duration_seconds_bucket{endpoint="standard",component="database",le="0.1"} 1
health_check_duration_seconds_bucket{endpoint="standard",component="database",le="0.5"} 5
health_check_duration_seconds_bucket{endpoint="standard",component="database",le="1.0"} 10

# HELP health_check_failures_total Total number of health check failures
# TYPE health_check_failures_total counter
health_check_failures_total{endpoint="standard",component="database",error_type="ConnectionError"} 2

# HELP health_check_status Current status of health checks (1=healthy, 0=unhealthy)
# TYPE health_check_status gauge
health_check_status{endpoint="standard",component="database"} 1
```

## Health Check Endpoints

### 1. Standard Health Check
**URL:** `GET /health/standard`

**Purpose:** Standardized health check with consistent response format

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "response_time": 15},
    "redis": {"status": "healthy", "response_time": 5},
    "external_apis": {
      "supabase": {"status": "healthy"},
      "stripe": {"status": "healthy"}
    }
  }
}
```

### 2. Metrics Health Check
**URL:** `GET /health/metrics`

**Purpose:** Health check with comprehensive Prometheus metrics

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0",
  "response_time_ms": 125.5,
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2
    },
    "redis": {
      "status": "healthy", 
      "response_time_ms": 5.1
    },
    "external_apis": {
      "supabase": {
        "status": "healthy",
        "response_time_ms": 45.3
      },
      "stripe": {
        "status": "healthy",
        "response_time_ms": 89.7
      }
    }
  },
  "metrics": {
    "system_metrics": {
      "memory_total_bytes": 8589934592,
      "memory_available_bytes": 4294967296,
      "memory_used_bytes": 4294967296,
      "memory_percent": 50.0,
      "cpu_percent": 25.5,
      "disk_used_bytes": 107374182400,
      "disk_total_bytes": 250000000000,
      "disk_percent": 42.9
    },
    "database_metrics": {
      "connection_pool_size": 10,
      "connections_checked_out": 2
    },
    "redis_metrics": {
      "memory_usage_bytes": 1048576,
      "connected_clients": 5,
      "total_commands_processed": 1000
    }
  }
}
```

### 3. Other Health Check Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check
- `GET /health/database` - Database-specific health check
- `GET /health/redis` - Redis-specific health check
- `GET /health/external` - External services health check

## Alerting System

### Configuration

The alerting system can be configured through environment variables:

```bash
# Enable alerting
ALERTING_ENABLED=true

# Webhook URL for alerts
ALERT_WEBHOOK_URL=https://your-webhook-url.com/alerts

# Slack webhook for alerts
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Failure threshold before alerting
HEALTH_CHECK_FAILURE_THRESHOLD=3

# Response time threshold for alerts
RESPONSE_TIME_THRESHOLD_MS=5000
```

### Alert Types

#### 1. Health Check Failures
- **Trigger:** When health checks fail repeatedly
- **Threshold:** Configurable failure count
- **Cooldown:** 5 minutes between alerts for the same issue

#### 2. Threshold Violations
- **Memory Usage:** > 90% (critical), > 80% (warning)
- **CPU Usage:** > 90% (critical), > 80% (warning)
- **Disk Usage:** > 95% (critical), > 85% (warning)
- **Response Time:** > 5 seconds

#### 3. Service Recovery
- **Trigger:** When a service recovers from failure
- **Purpose:** Notify when issues are resolved

### Alert Format

#### Webhook Alert
```json
{
  "title": "Health Check Failure: database",
  "message": "Health check for database failed on endpoint standard. Error type: ConnectionError",
  "severity": "critical",
  "component": "database",
  "error_type": "ConnectionError",
  "timestamp": "2025-01-27T10:30:00Z",
  "environment": "production"
}
```

#### Slack Alert
Rich Slack message with color-coded severity and detailed fields.

## Configuration

### Environment Variables

```bash
# Prometheus Configuration
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
PROMETHEUS_PATH=/metrics

# Health Check Configuration
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=60

# Alerting Configuration
ALERTING_ENABLED=false
ALERT_WEBHOOK_URL=
ALERT_SLACK_WEBHOOK=
HEALTH_CHECK_FAILURE_THRESHOLD=3
RESPONSE_TIME_THRESHOLD_MS=5000

# Thresholds
MEMORY_USAGE_THRESHOLD_PERCENT=90
CPU_USAGE_THRESHOLD_PERCENT=80
DISK_USAGE_THRESHOLD_PERCENT=85
DB_POOL_UTILIZATION_THRESHOLD=0.8
DB_CONNECTION_TIMEOUT_THRESHOLD_MS=1000
REDIS_MEMORY_THRESHOLD_PERCENT=80
REDIS_CONNECTION_TIMEOUT_THRESHOLD_MS=500
EXTERNAL_API_TIMEOUT_THRESHOLD_MS=3000
EXTERNAL_API_FAILURE_THRESHOLD=2

# Metrics Configuration
METRICS_RETENTION_HOURS=24
METRICS_LOGGING_ENABLED=true
METRICS_LOG_LEVEL=INFO
```

### Monitoring Configuration File

The monitoring configuration is defined in `config/monitoring.py`:

```python
from config.monitoring import MonitoringConfig

# Access configuration values
config = MonitoringConfig()
print(f"Prometheus enabled: {config.PROMETHEUS_ENABLED}")
print(f"Alerting enabled: {config.ALERTING_ENABLED}")
```

## Usage Examples

### 1. Basic Health Check
```bash
curl http://localhost:5003/health/standard
```

### 2. Metrics Health Check
```bash
curl http://localhost:5003/health/metrics
```

### 3. Prometheus Metrics
```bash
curl http://localhost:5003/metrics
```

### 4. Python Client Usage
```python
from scripts.health_check_demo import HealthCheckClient

client = HealthCheckClient()

# Get standardized health
health = client.get_standard_health()
print(f"Status: {health['data']['status']}")

# Get metrics health
metrics = client.get_metrics_health()
print(f"Response time: {metrics['data']['response_time_ms']}ms")

# Get Prometheus metrics
prometheus = client.get_prometheus_metrics()
print(f"Metrics length: {len(prometheus['data'])}")
```

### 5. Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mingus'
    static_configs:
      - targets: ['localhost:5003']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 6. Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Mingus Health Dashboard",
    "panels": [
      {
        "title": "Health Check Status",
        "type": "stat",
        "targets": [
          {
            "expr": "health_check_status",
            "legendFormat": "{{component}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(health_check_duration_seconds_sum[5m]) / rate(health_check_duration_seconds_count[5m])",
            "legendFormat": "{{component}}"
          }
        ]
      }
    ]
  }
}
```

## Deployment

### 1. Install Dependencies
```bash
pip install -r requirements-monitoring.txt
```

### 2. Configure Environment
```bash
export PROMETHEUS_ENABLED=true
export ALERTING_ENABLED=true
export ALERT_WEBHOOK_URL=https://your-webhook-url.com/alerts
```

### 3. Start Application
```bash
python backend/app.py
```

### 4. Verify Endpoints
```bash
# Test health check
curl http://localhost:5003/health/standard

# Test metrics
curl http://localhost:5003/metrics

# Test metrics health check
curl http://localhost:5003/health/metrics
```

### 5. Run Demo Script
```bash
python scripts/health_check_demo.py
```

## Monitoring Best Practices

### 1. Health Check Frequency
- **Load Balancers:** Every 30 seconds
- **Kubernetes:** Every 10 seconds (liveness), 5 seconds (readiness)
- **Monitoring Systems:** Every 60 seconds

### 2. Alert Thresholds
- **Critical Services:** Alert on first failure
- **Non-Critical Services:** Alert after 3 consecutive failures
- **Performance:** Alert when response time > 5 seconds

### 3. Metrics Retention
- **High-Resolution:** Keep 1 hour of 15-second intervals
- **Medium-Resolution:** Keep 1 day of 1-minute intervals
- **Low-Resolution:** Keep 30 days of 5-minute intervals

### 4. Dashboard Setup
- **Overview:** Overall health status and key metrics
- **Performance:** Response times and throughput
- **Resources:** CPU, memory, and disk usage
- **Alerts:** Recent alerts and their status

## Troubleshooting

### Common Issues

1. **Metrics Not Available**
   - Check if Prometheus client is installed
   - Verify `/metrics` endpoint is accessible
   - Check application logs for errors

2. **Alerts Not Sending**
   - Verify alerting is enabled
   - Check webhook URLs are correct
   - Review failure thresholds

3. **High Response Times**
   - Check database connection pool
   - Monitor Redis performance
   - Review external API calls

4. **Memory Leaks**
   - Monitor memory usage over time
   - Check for connection leaks
   - Review application logs

### Debug Commands

```bash
# Check all health endpoints
curl http://localhost:5003/health/standard
curl http://localhost:5003/health/metrics
curl http://localhost:5003/metrics

# Check specific components
curl http://localhost:5003/health/database
curl http://localhost:5003/health/redis
curl http://localhost:5003/health/external

# Run demo script
python scripts/health_check_demo.py
```

## Conclusion

The monitoring integration provides comprehensive observability for the Mingus Flask application. With Prometheus metrics, health check endpoints, and alerting capabilities, you can effectively monitor the application's health and performance in production environments.

For additional support or questions, refer to the main health check documentation or contact the development team. 