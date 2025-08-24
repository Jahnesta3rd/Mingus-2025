# MINGUS Article Library - Logging Guide

## Overview

This guide covers the comprehensive structured logging system for the MINGUS Article Library, including configuration, integration, and best practices for effective logging.

## Table of Contents

1. [Logging Architecture](#logging-architecture)
2. [Configuration](#configuration)
3. [Integration](#integration)
4. [Usage Examples](#usage-examples)
5. [Log Levels](#log-levels)
6. [Performance Monitoring](#performance-monitoring)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Monitoring and Analysis](#monitoring-and-analysis)

## Logging Architecture

### Components

The logging system consists of several key components:

- **Structured Logging**: JSON-formatted logs with consistent structure
- **Request Logging**: Automatic request/response logging with performance metrics
- **Component Loggers**: Specialized loggers for different system components
- **Performance Monitoring**: Built-in performance tracking and metrics
- **Error Tracking**: Comprehensive error logging with context

### Log Structure

All logs follow a consistent JSON structure:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "article_event",
  "message": "Article viewed",
  "article_id": 123,
  "user_id": 456,
  "request_id": "req_1705311045123",
  "endpoint": "get_article",
  "method": "GET",
  "path": "/api/articles/123",
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "service": "mingus-article-library",
  "version": "1.0.0",
  "environment": "production"
}
```

## Configuration

### Basic Setup

```python
from backend.logging_config import setup_logging
from backend.logging_integration import integrate_logging_with_flask

# Setup logging
setup_logging()

# Integrate with Flask app
app = Flask(__name__)
integrate_logging_with_flask(app)
```

### Environment Variables

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Application version
APP_VERSION=1.0.0

# Environment
FLASK_ENV=production
```

### Component-Specific Configuration

```python
# Configure specific component log levels
logging.getLogger('backend.services.article_search').setLevel(logging.DEBUG)
logging.getLogger('backend.services.ai_classifier').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
```

## Integration

### Flask Application Integration

```python
from backend.logging_integration import integrate_logging_with_flask

def create_app():
    app = Flask(__name__)
    
    # Integrate logging
    integrate_logging_with_flask(app)
    
    return app
```

### Automatic Request Logging

The system automatically logs:

- **Request Start**: Method, path, user agent, IP
- **Request End**: Status code, duration, response size
- **Errors**: Exception details with stack traces
- **Performance**: Request processing time

### Error Handling

```python
# Automatic error logging for all exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # Error is automatically logged with context
    return jsonify({'error': 'Internal server error'}), 500
```

## Usage Examples

### Basic Logging

```python
from backend.logging_config import get_logger

logger = get_logger('my_component')

# Info logging
logger.info("User logged in", user_id=123, method="oauth")

# Error logging
logger.error("Database connection failed", 
            error_type="ConnectionError",
            retry_count=3)
```

### Article-Specific Logging

```python
from backend.logging_integration import (
    log_article_view, log_article_share, log_article_bookmark
)

# Log article view
log_article_view(article_id=123, user_id=456)

# Log article share
log_article_share(article_id=123, platform="twitter", user_id=456)

# Log article bookmark
log_article_bookmark(article_id=123, user_id=456, action="add")
```

### User Activity Logging

```python
from backend.logging_integration import log_user_action, log_assessment_completion

# Log user action
log_user_action("profile_updated", user_id=123, 
               context={"fields_updated": ["email", "preferences"]})

# Log assessment completion
log_assessment_completion(user_id=123, 
                        scores={"be_score": 75, "do_score": 65, "have_score": 45})
```

### Search and Recommendations

```python
from backend.logging_integration import (
    log_search_performed, log_recommendation_requested
)

# Log search
log_search_performed(
    query="career advancement",
    filters={"phase": "BE", "difficulty": "Intermediate"},
    result_count=25,
    processing_time=0.150
)

# Log recommendations
log_recommendation_requested(
    user_id=123,
    recommendation_count=10,
    processing_time=0.250
)
```

### Performance Monitoring

```python
from backend.logging_integration import performance_monitor

@performance_monitor
def expensive_operation():
    # This function's performance will be automatically logged
    time.sleep(1)
    return "result"
```

### Component-Specific Loggers

```python
from backend.logging_integration import (
    DatabaseLogger, CacheLogger, AILogger, SearchLogger
)

# Database logging
db_logger = DatabaseLogger(db)
db_logger.log_operation("SELECT", "articles", row_count=100, execution_time=0.050)

# Cache logging
cache_logger = CacheLogger()
cache_logger.log_get("user:123:preferences", hit=True, execution_time=0.001)

# AI logging
ai_logger = AILogger()
ai_logger.log_classification(
    article_id=123,
    classification_result={"phase": "BE", "difficulty": "Intermediate"},
    processing_time=2.5
)

# Search logging
search_logger = SearchLogger()
search_logger.log_query(
    query="career development",
    filters={"category": "Career Development"},
    result_count=15,
    processing_time=0.100
)
```

## Log Levels

### Level Hierarchy

1. **DEBUG**: Detailed information for debugging
2. **INFO**: General information about application flow
3. **WARNING**: Warning messages for potential issues
4. **ERROR**: Error messages for handled exceptions
5. **CRITICAL**: Critical errors that may cause system failure

### Component-Specific Levels

```python
# Development - More verbose
logging.getLogger('backend.services.article_search').setLevel(logging.DEBUG)
logging.getLogger('backend.services.cache_service').setLevel(logging.DEBUG)

# Production - Less verbose
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('redis').setLevel(logging.WARNING)
```

## Performance Monitoring

### Automatic Performance Tracking

```python
# Request performance is automatically tracked
# Duration is logged in milliseconds
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "request",
  "message": "Request completed",
  "method": "GET",
  "path": "/api/articles/123",
  "status_code": 200,
  "duration_ms": 150.25
}
```

### Manual Performance Logging

```python
from backend.logging_config import log_performance_metric

# Log custom performance metrics
log_performance_metric(
    metric_name="database_query_time",
    value=45.2,
    unit="ms",
    context={"table": "articles", "operation": "SELECT"}
)
```

### Function Performance Decorator

```python
from backend.logging_integration import performance_monitor

@performance_monitor
def search_articles(query, filters):
    # Function execution time is automatically logged
    results = perform_search(query, filters)
    return results
```

## Error Handling

### Automatic Error Logging

```python
# All exceptions are automatically logged with context
try:
    result = risky_operation()
except Exception as e:
    # Error is automatically logged with:
    # - Exception type and message
    # - Stack trace
    # - Request context
    # - User context
    raise
```

### Manual Error Logging

```python
from backend.logging_config import log_error

try:
    result = risky_operation()
except Exception as e:
    log_error(e, {
        'operation': 'risky_operation',
        'input_data': {'param1': 'value1'},
        'user_id': 123
    })
    raise
```

### Error Context

Error logs include:

- **Exception Type**: Class name of the exception
- **Error Message**: Human-readable error message
- **Stack Trace**: Full stack trace for debugging
- **Request Context**: Endpoint, method, path
- **User Context**: User ID, request ID
- **Custom Context**: Additional error-specific data

## Best Practices

### 1. Use Structured Logging

```python
# Good - Structured logging
logger.info("User action", 
           action="article_view",
           article_id=123,
           user_id=456,
           duration_ms=150)

# Bad - String concatenation
logger.info(f"User {user_id} viewed article {article_id} in {duration}ms")
```

### 2. Include Relevant Context

```python
# Include all relevant context
logger.info("Article processed",
           article_id=123,
           processing_steps=["scraping", "classification", "indexing"],
           processing_time_ms=2500,
           success=True)
```

### 3. Use Appropriate Log Levels

```python
# DEBUG - Detailed debugging information
logger.debug("SQL query executed", query="SELECT * FROM articles", params={})

# INFO - General application flow
logger.info("User logged in", user_id=123, method="oauth")

# WARNING - Potential issues
logger.warning("Cache miss", key="user:123:preferences", fallback="database")

# ERROR - Handled exceptions
logger.error("Database connection failed", retry_count=3, max_retries=5)

# CRITICAL - System failures
logger.critical("Database unavailable", downtime_minutes=30)
```

### 4. Sanitize Sensitive Data

```python
# Sensitive data is automatically redacted
logger.info("API call", 
           endpoint="/api/users",
           api_key="***REDACTED***",  # Automatically redacted
           user_data={"name": "John", "email": "john@example.com"})
```

### 5. Use Component-Specific Loggers

```python
# Use appropriate logger for each component
search_logger = get_logger('search')
ai_logger = get_logger('ai')
db_logger = get_logger('database')

search_logger.info("Search executed", query="career", results=25)
ai_logger.info("Classification completed", article_id=123, phase="BE")
db_logger.debug("Query executed", table="articles", operation="SELECT")
```

### 6. Performance Monitoring

```python
# Use performance decorator for expensive operations
@performance_monitor
def generate_recommendations(user_id):
    # Performance is automatically tracked
    recommendations = ai_service.get_recommendations(user_id)
    return recommendations

# Log custom performance metrics
log_performance_metric(
    metric_name="external_api_call",
    value=250.5,
    unit="ms",
    context={"service": "openai", "endpoint": "/v1/chat/completions"}
)
```

## Monitoring and Analysis

### Log Aggregation

Logs can be aggregated using tools like:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **Splunk**: Log analysis and monitoring
- **CloudWatch**: AWS log management

### Log Analysis Queries

```json
// Find slow requests
{
  "query": {
    "range": {
      "duration_ms": {
        "gte": 1000
      }
    }
  }
}

// Find errors by endpoint
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"term": {"endpoint": "search_articles"}}
      ]
    }
  }
}

// Find user activity patterns
{
  "query": {
    "term": {"logger": "user_action"}
  },
  "aggs": {
    "actions_by_type": {
      "terms": {"field": "action"}
    }
  }
}
```

### Alerting

Set up alerts for:

- **High Error Rates**: > 5% error rate
- **Slow Response Times**: > 2 seconds average
- **System Failures**: Critical level logs
- **Unusual Activity**: Anomaly detection

### Metrics Dashboard

Create dashboards showing:

- **Request Volume**: Requests per minute
- **Response Times**: Average, 95th percentile
- **Error Rates**: Errors per minute
- **User Activity**: Active users, popular actions
- **System Health**: Database, cache, external services

## Integration with Monitoring Tools

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_users = Gauge('active_users', 'Number of active users')

# Export metrics from logs
def export_metrics_from_logs():
    # Parse logs and export metrics
    pass
```

### Grafana Dashboards

Create dashboards for:

- **Application Performance**: Response times, throughput
- **User Behavior**: Popular articles, search patterns
- **System Health**: Database performance, cache hit rates
- **Business Metrics**: User engagement, content consumption

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Configure Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

## Troubleshooting

### Common Issues

1. **High Log Volume**: Adjust log levels for noisy components
2. **Missing Context**: Ensure all relevant fields are included
3. **Performance Impact**: Use async logging for high-volume scenarios
4. **Storage Issues**: Implement log rotation and retention policies

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Enable SQL query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```

### Log Rotation

```python
from logging.handlers import RotatingFileHandler

# Configure log rotation
handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Next Steps

1. **Implement Log Aggregation**: Set up centralized log collection
2. **Create Dashboards**: Build monitoring dashboards
3. **Set Up Alerting**: Configure automated alerts
4. **Performance Optimization**: Use logs to identify bottlenecks
5. **Security Monitoring**: Monitor for suspicious activity
6. **Compliance**: Ensure logging meets compliance requirements
