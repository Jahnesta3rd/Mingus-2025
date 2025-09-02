# Comprehensive Performance Monitoring Setup Guide

This guide explains how to set up and use the comprehensive performance monitoring system for your Flask financial application.

## 🚀 Overview

The monitoring system provides:

- **Real-time performance metrics collection** for Flask, PostgreSQL, Redis, and Celery
- **Database query performance monitoring** with detailed query analysis
- **Redis cache performance tracking** including hit rates and operation timing
- **API response time monitoring** with endpoint-specific metrics
- **User experience metrics** (Core Web Vitals) collection
- **System resource monitoring** (CPU, memory, disk, network)
- **Prometheus integration** for metrics export
- **Grafana dashboards** for visualization
- **Alerting system** for performance issues

## 📋 Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL database
- Redis cache
- Celery worker setup

## 🛠️ Installation

### 1. Install Dependencies

```bash
# Install monitoring dependencies
pip install -r requirements-monitoring.txt

# Or install core packages individually
pip install prometheus-client psutil redis psycopg2-binary flask-limiter flask-caching
```

### 2. Environment Configuration

Create a `.env` file with your configuration:

```bash
# Flask Environment
FLASK_ENV=production  # or development, testing

# Database
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://user:pass@localhost:5432/mingus_financial

# Redis
REDIS_URL=redis://localhost:6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# Alerting (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_FROM_EMAIL=alerts@yourcompany.com
ALERT_TO_EMAILS=admin@yourcompany.com,dev@yourcompany.com

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#monitoring
```

## 🔧 Integration with Flask App

### Option 1: Automatic Setup (Recommended)

Add this to your Flask app factory or main app file:

```python
from monitoring.setup_monitoring import setup_monitoring_for_app

def create_app():
    app = Flask(__name__)
    
    # Your existing app configuration...
    
    # Setup comprehensive monitoring
    monitor = setup_monitoring_for_app(app)
    
    return app
```

### Option 2: Manual Setup

```python
from monitoring.comprehensive_monitor import comprehensive_monitor
from monitoring.api import monitoring_bp
from monitoring.prometheus_exporter import prometheus_metrics, start_background_updater

def create_app():
    app = Flask(__name__)
    
    # Initialize monitoring
    comprehensive_monitor.init_app(app)
    
    # Register monitoring blueprint
    app.register_blueprint(monitoring_bp)
    
    # Add Prometheus metrics endpoint
    app.add_url_rule('/metrics', 'prometheus_metrics', prometheus_metrics)
    
    # Start background metrics updater
    start_background_updater()
    
    return app
```

## 🐳 Docker Setup

### 1. Start Monitoring Stack

```bash
# Start the complete monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Monitoring Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alert Manager**: http://localhost:9093
- **cAdvisor**: http://localhost:8080
- **Jaeger**: http://localhost:16686

### 3. Configure Grafana

1. Login to Grafana (admin/admin123)
2. Add Prometheus as a data source:
   - URL: `http://prometheus:9090`
   - Access: Server (default)
3. Import dashboards from `monitoring/grafana/dashboards/`

## 📊 Available Metrics

### API Metrics
- Request count by endpoint and method
- Response time percentiles
- Status code distribution
- Request/response sizes

### Database Metrics
- Query execution time
- Slow query detection
- Table-level statistics
- Connection pool status

### Redis Metrics
- Operation timing
- Memory usage
- Hit rates
- Connection status

### Celery Metrics
- Task execution time
- Success/failure rates
- Queue depths
- Worker status

### System Metrics
- CPU usage
- Memory consumption
- Disk I/O
- Network traffic

### Core Web Vitals
- Largest Contentful Paint (LCP)
- First Input Delay (FID)
- Cumulative Layout Shift (CLS)
- Time to First Byte (TTFB)

## 🌐 Frontend Integration

### 1. Include Performance Monitor

Add this to your HTML templates:

```html
<script src="/static/js/performance-monitor.js"></script>
```

### 2. Configure Monitoring

```javascript
// Configure the performance monitor
window.performanceMonitor.setConfig({
    endpoint: '/monitoring/web-vitals',
    sampleRate: 1.0,  // 100% sampling
    enableDebug: true,
    customMetrics: [
        { name: 'page_load_time', value: Date.now() - performance.timing.navigationStart },
        { name: 'user_interaction_count', value: 0 }
    ]
});
```

### 3. Custom Metrics

```javascript
// Record custom business metrics
window.performanceMonitor.recordCustomMetric('transaction_amount', 1500.00, {
    currency: 'USD',
    transaction_type: 'deposit'
});

// Record user interactions
window.performanceMonitor.recordCustomMetric('form_submission', 1, {
    form_name: 'loan_application',
    user_type: 'premium'
});
```

## 📈 Monitoring Endpoints

### REST API Endpoints

- `GET /monitoring/health` - Health check
- `GET /monitoring/metrics` - Comprehensive metrics summary
- `GET /monitoring/metrics/database` - Database metrics
- `GET /monitoring/metrics/redis` - Redis metrics
- `GET /monitoring/metrics/api` - API metrics
- `GET /monitoring/metrics/celery` - Celery metrics
- `GET /monitoring/metrics/system` - System metrics
- `GET /monitoring/metrics/web-vitals` - Web vitals metrics
- `POST /monitoring/web-vitals` - Submit web vitals
- `GET /monitoring/config` - Current configuration
- `PUT /monitoring/config/thresholds` - Update thresholds
- `GET /monitoring/export` - Export metrics (JSON/CSV)
- `POST /monitoring/reset` - Reset all metrics

### Prometheus Endpoint

- `GET /metrics` - Prometheus-formatted metrics

### Dashboard Endpoints

- `GET /monitoring/dashboard` - Built-in monitoring dashboard
- `GET /monitoring/test-web-vitals` - Web vitals test page

## 🔍 Query Examples

### Get Slow Database Queries

```bash
curl "http://localhost:5001/monitoring/metrics/database?slow_only=true&limit=10"
```

### Get API Performance by Endpoint

```bash
curl "http://localhost:5001/monitoring/metrics/api?endpoint=forecast&limit=20"
```

### Get System Metrics for Last Hour

```bash
curl "http://localhost:5001/monitoring/metrics/system?hours=1&limit=100"
```

### Export Metrics as CSV

```bash
curl "http://localhost:5001/monitoring/export?format=csv" -o metrics.csv
```

## 🚨 Alerting Configuration

### 1. Update Thresholds

```bash
curl -X PUT "http://localhost:5001/monitoring/config/thresholds" \
  -H "Content-Type: application/json" \
  -d '{
    "slow_query_threshold_ms": 2000,
    "slow_api_threshold_ms": 5000,
    "memory_usage_max_percent": 85
  }'
```

### 2. Email Alerts

Configure SMTP settings in your `.env` file and the system will automatically send alerts when thresholds are exceeded.

### 3. Slack Alerts

Set up Slack webhook integration for real-time notifications.

## 📝 Performance Decorators

Use the built-in decorators to monitor specific functions:

```python
from monitoring.comprehensive_monitor import monitor_performance

@monitor_performance(operation_type='database')
def complex_database_query():
    # Your database operation
    pass

@monitor_performance(operation_type='redis')
def cache_operation():
    # Your cache operation
    pass

@monitor_performance(operation_type='api')
def business_logic():
    # Your business logic
    pass
```

## 🧪 Testing

### 1. Test Monitoring Setup

```bash
# Run the setup script
python backend/setup_monitoring.py

# Test individual components
curl http://localhost:5001/monitoring/health
curl http://localhost:5001/monitoring/metrics
```

### 2. Test Web Vitals Collection

Visit `/monitoring/test-web-vitals` to test frontend metrics collection.

### 3. Load Testing

```bash
# Install locust for load testing
pip install locust

# Run load test
locust -f load_test.py --host=http://localhost:5001
```

## 🔧 Troubleshooting

### Common Issues

1. **Metrics not appearing**: Check if monitoring is properly initialized
2. **High memory usage**: Adjust `max_metrics_per_type` in configuration
3. **Prometheus connection issues**: Verify Docker network configuration
4. **Frontend metrics not sending**: Check browser console for errors

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('monitoring').setLevel(logging.DEBUG)
```

### Performance Impact

The monitoring system is designed to have minimal performance impact:
- Metrics are collected asynchronously
- Memory usage is bounded
- Sampling can be configured
- Background cleanup prevents memory leaks

## 📚 Advanced Configuration

### Custom Metrics

Extend the monitoring system with custom metrics:

```python
from monitoring.comprehensive_monitor import comprehensive_monitor

# Add custom business metrics
comprehensive_monitor.add_custom_metric('business_value', 1000.0, {
    'metric_type': 'revenue',
    'period': 'daily'
})
```

### Custom Alerting

Implement custom alerting logic:

```python
def custom_alert_handler(alert):
    # Your custom alert handling logic
    if alert.level == 'critical':
        # Send SMS, create ticket, etc.
        pass

comprehensive_monitor.alert_callbacks.append(custom_alert_handler)
```

### Data Retention

Configure data retention policies:

```python
# In monitoring/config.py
config = {
    'metrics_retention_days': 90,  # Keep 90 days of data
    'max_metrics_per_type': 50000,  # Store up to 50k metrics per type
}
```

## 🚀 Production Deployment

### 1. Security Considerations

- Use HTTPS in production
- Implement authentication for monitoring endpoints
- Restrict access to monitoring services
- Use environment variables for sensitive configuration

### 2. Scaling

- Use Redis for distributed metrics storage
- Implement metrics aggregation across multiple instances
- Use load balancers for monitoring endpoints
- Consider using external monitoring services (DataDog, New Relic)

### 3. Backup and Recovery

- Backup Prometheus data volumes
- Export metrics regularly
- Monitor monitoring system health
- Have fallback monitoring in place

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review logs in `/logs/` directory
3. Check monitoring system health endpoints
4. Verify Docker container status

## 🔄 Updates and Maintenance

### Regular Maintenance

- Monitor disk usage for metrics storage
- Review and adjust thresholds
- Clean up old metrics data
- Update monitoring dependencies

### Version Updates

- Backup configuration before updates
- Test in staging environment
- Update monitoring stack components
- Verify metrics continuity

---

This monitoring system provides comprehensive visibility into your Flask financial application's performance. Start with the basic setup and gradually enable advanced features as needed. 