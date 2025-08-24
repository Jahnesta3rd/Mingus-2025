# Webhook Logging and Monitoring Guide

## Overview

The MINGUS application implements comprehensive webhook logging and monitoring capabilities to ensure reliable, secure, and observable webhook processing. This system provides detailed event tracking, performance monitoring, health checks, and analytics for all webhook operations.

## 🔍 Core Features

### **1. Comprehensive Event Logging**
- **Structured Logging**: All webhook events are logged with structured data
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Event Categories**: Security, Performance, Business, System, Error
- **Rich Metadata**: Complete context for each webhook event

### **2. Performance Monitoring**
- **Processing Time Tracking**: Monitor webhook processing performance
- **Success Rate Monitoring**: Track success and failure rates
- **Throughput Analytics**: Monitor events per minute/hour
- **Performance Percentiles**: P95, P99 processing times

### **3. Health Monitoring**
- **System Health Checks**: Database, processing, security, performance health
- **Real-time Alerts**: Automatic alerting for critical issues
- **Health Scoring**: Overall system health score (0.0 to 1.0)
- **Issue Tracking**: Active issues and recommendations

### **4. Analytics and Reporting**
- **Event Analytics**: Detailed event type and entity analytics
- **Error Analytics**: Error patterns, trends, and distribution
- **Comprehensive Reports**: Complete webhook system reports
- **Trend Analysis**: Performance and error trends over time

## 🏗️ Architecture

### **Service Components**

#### **1. WebhookLoggingService**
Main service for comprehensive webhook logging and monitoring.

```python
class WebhookLoggingService:
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.health_thresholds = {...}
        self.alert_thresholds = {...}
```

#### **2. WebhookEventLog**
Structured log entry for webhook events.

```python
@dataclass
class WebhookEventLog:
    event_id: str
    event_type: str
    timestamp: datetime
    level: LogLevel
    category: EventCategory
    source_ip: str
    user_agent: str
    request_id: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
```

#### **3. WebhookPerformanceMetrics**
Comprehensive performance metrics.

```python
@dataclass
class WebhookPerformanceMetrics:
    # Basic metrics
    total_events: int
    successful_events: int
    failed_events: int
    success_rate: float
    
    # Performance metrics
    average_processing_time: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    
    # Throughput metrics
    events_per_minute: float
    events_per_hour: float
    peak_events_per_minute: float
    
    # Error metrics
    error_rate: float
    error_distribution: Dict[str, int]
    top_errors: List[Tuple[str, int]]
```

#### **4. WebhookHealthStatus**
System health status and monitoring.

```python
@dataclass
class WebhookHealthStatus:
    overall_status: str  # healthy, degraded, critical
    health_score: float  # 0.0 to 1.0
    last_check: datetime
    
    # Component status
    database_health: str
    processing_health: str
    security_health: str
    performance_health: str
    
    # Issues and alerts
    active_issues: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    recommendations: List[str]
```

## 🔧 Usage Examples

### **1. Basic Event Logging**

```python
from backend.services.webhook_logging_service import WebhookLoggingService

# Initialize logging service
logging_service = WebhookLoggingService(db_session, config)

# Log successful webhook event
log_entry = logging_service.log_webhook_event(
    event_id="evt_1234567890",
    event_type="customer.created",
    source_ip="192.168.1.100",
    user_agent="stripe-webhook/1.0",
    request_id="req_1234567890",
    processing_time=1.5,
    success=True,
    metadata={
        "customer_id": "cus_1234567890",
        "email": "customer@example.com"
    },
    entity_type="customer",
    entity_id="cus_1234567890"
)
```

### **2. Logging Failed Events**

```python
# Log failed webhook event
log_entry = logging_service.log_webhook_event(
    event_id="evt_1234567891",
    event_type="customer.updated",
    source_ip="192.168.1.101",
    user_agent="stripe-webhook/1.0",
    request_id="req_1234567891",
    processing_time=5.2,
    success=False,
    error_message="Database connection timeout",
    error_details={
        "error_type": "database_error",
        "error_code": "DB_TIMEOUT",
        "retry_attempts": 3
    },
    metadata={
        "customer_id": "cus_1234567891",
        "operation": "customer_update"
    },
    entity_type="customer",
    entity_id="cus_1234567891"
)
```

### **3. Performance Monitoring**

```python
# Get performance metrics
metrics = logging_service.get_performance_metrics(
    time_range_hours=24,
    event_type="customer.created"
)

print(f"Total events: {metrics.total_events}")
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Average processing time: {metrics.average_processing_time:.3f}s")
print(f"P95 processing time: {metrics.p95_processing_time:.3f}s")
print(f"Events per minute: {metrics.events_per_minute:.2f}")
print(f"Error rate: {metrics.error_rate:.2%}")

# Check top errors
for error, count in metrics.top_errors:
    print(f"Error: {error}, Count: {count}")
```

### **4. Health Monitoring**

```python
# Get system health status
health_status = logging_service.get_health_status()

print(f"Overall status: {health_status.overall_status}")
print(f"Health score: {health_status.health_score:.2%}")
print(f"Database health: {health_status.database_health}")
print(f"Processing health: {health_status.processing_health}")
print(f"Security health: {health_status.security_health}")
print(f"Performance health: {health_status.performance_health}")

# Check active issues
for issue in health_status.active_issues:
    print(f"Issue: {issue['type']} - {issue['description']}")

# Check recommendations
for recommendation in health_status.recommendations:
    print(f"Recommendation: {recommendation}")
```

### **5. Event Analytics**

```python
# Get event analytics by event type
event_analytics = logging_service.get_event_analytics(
    time_range_hours=24,
    group_by="event_type"
)

print(f"Total events: {event_analytics['total_events']}")
for group in event_analytics['groups']:
    print(f"Event type: {group['name']}")
    print(f"  Count: {group['count']}")
    print(f"  Avg processing time: {group['avg_processing_time']:.3f}s")
    if 'success_rate' in group:
        print(f"  Success rate: {group['success_rate']:.2%}")

# Get event analytics by entity type
entity_analytics = logging_service.get_event_analytics(
    time_range_hours=24,
    group_by="entity_type"
)

for group in entity_analytics['groups']:
    print(f"Entity type: {group['name']}")
    print(f"  Count: {group['count']}")
    print(f"  Avg processing time: {group['avg_processing_time']:.3f}s")
```

### **6. Error Analytics**

```python
# Get error analytics
error_analytics = logging_service.get_error_analytics(time_range_hours=24)

print(f"Total failed events: {error_analytics['total_failed_events']}")

# Check error patterns
for error_pattern, count in error_analytics['error_patterns'].items():
    print(f"Error pattern: {error_pattern}, Count: {count}")

# Check top errors
for error, count in error_analytics['top_errors']:
    print(f"Top error: {error}, Count: {count}")

# Check error trends
trends = error_analytics['error_trends']
print(f"Error trend direction: {trends['trend_direction']}")
print(f"Error trend: {trends['trend']:.2f}")
```

### **7. Report Generation**

```python
# Generate comprehensive webhook report
report = logging_service.generate_webhook_report(
    time_range_hours=24,
    include_details=True
)

# Print summary
summary = report['summary']
print(f"Webhook Report Summary:")
print(f"  Total events: {summary['total_events']}")
print(f"  Success rate: {summary['success_rate']}")
print(f"  Average processing time: {summary['average_processing_time']}")
print(f"  Error rate: {summary['error_rate']}")
print(f"  Health status: {summary['health_status']}")
print(f"  Health score: {summary['health_score']}")

# Print detailed information
if 'details' in report:
    details = report['details']
    print(f"\nTop Errors:")
    for error, count in details['top_errors']:
        print(f"  {error}: {count}")
    
    print(f"\nActive Issues:")
    for issue in details['active_issues']:
        print(f"  {issue['type']}: {issue['description']}")
    
    print(f"\nRecommendations:")
    for recommendation in details['recommendations']:
        print(f"  {recommendation}")
```

### **8. Webhook Manager Integration**

```python
from backend.webhooks.stripe_webhooks import StripeWebhookManager

# Initialize webhook manager
webhook_manager = StripeWebhookManager(db_session, config)

# Get webhook analytics
analytics = webhook_manager.get_webhook_analytics(
    time_range_hours=24,
    include_health=True
)

# Generate webhook report
report = webhook_manager.generate_webhook_report(
    time_range_hours=24,
    include_details=True
)
```

## 📊 Monitoring Dashboard

### **Key Metrics to Monitor**

#### **1. Performance Metrics**
- **Success Rate**: Should be > 95%
- **Average Processing Time**: Should be < 5 seconds
- **P95 Processing Time**: Should be < 10 seconds
- **Events per Minute**: Monitor for unusual spikes or drops

#### **2. Error Metrics**
- **Error Rate**: Should be < 5%
- **Top Errors**: Monitor for recurring error patterns
- **Error Trends**: Watch for increasing error rates

#### **3. Health Metrics**
- **Overall Health Score**: Should be > 0.9
- **Component Health**: All components should be "healthy"
- **Active Issues**: Should be minimal or none

#### **4. Security Metrics**
- **Security Events**: Monitor for suspicious activity
- **Failed Authentications**: Watch for brute force attempts
- **IP Restrictions**: Monitor for unauthorized access attempts

### **Alerting Thresholds**

```python
# Default health thresholds
health_thresholds = {
    'success_rate_min': 0.95,  # 95% minimum success rate
    'avg_processing_time_max': 5.0,  # 5 seconds max average
    'error_rate_max': 0.05,  # 5% maximum error rate
    'p95_processing_time_max': 10.0,  # 10 seconds max p95
    'events_per_minute_min': 0.1,  # Minimum event rate
}

# Alert thresholds
alert_thresholds = {
    'critical_error_rate': 0.10,  # 10% critical error rate
    'high_processing_time': 15.0,  # 15 seconds high processing time
    'low_success_rate': 0.90,  # 90% low success rate
}
```

## 🔧 Configuration

### **Environment Variables**

```bash
# Logging Configuration
WEBHOOK_LOG_LEVEL=INFO
WEBHOOK_LOG_RETENTION_DAYS=30
WEBHOOK_METRICS_RETENTION_DAYS=90
WEBHOOK_AUDIT_RETENTION_DAYS=365

# Health Monitoring
WEBHOOK_HEALTH_CHECK_INTERVAL=300
WEBHOOK_SUCCESS_RATE_THRESHOLD=0.95
WEBHOOK_PROCESSING_TIME_THRESHOLD=5.0
WEBHOOK_ERROR_RATE_THRESHOLD=0.05

# Alerting
WEBHOOK_ALERT_CRITICAL_ERROR_RATE=0.10
WEBHOOK_ALERT_HIGH_PROCESSING_TIME=15.0
WEBHOOK_ALERT_LOW_SUCCESS_RATE=0.90
```

### **Service Configuration**

```python
# Initialize with custom settings
logging_service = WebhookLoggingService(
    db_session=db_session,
    config=config
)

# Custom health thresholds
logging_service.health_thresholds = {
    'success_rate_min': 0.98,  # Higher threshold
    'avg_processing_time_max': 3.0,  # Lower threshold
    'error_rate_max': 0.02,  # Lower threshold
}

# Custom alert thresholds
logging_service.alert_thresholds = {
    'critical_error_rate': 0.05,  # Lower critical threshold
    'high_processing_time': 10.0,  # Lower high processing time
    'low_success_rate': 0.95,  # Higher low success rate
}
```

## 🛡️ Security Features

### **1. Audit Trail**
- **Complete Event History**: All webhook events are logged
- **Security Events**: Special tracking for security-related events
- **Compliance**: Meets audit and compliance requirements

### **2. Access Control**
- **IP Filtering**: Monitor and restrict by IP address
- **User Agent Validation**: Validate webhook sources
- **Authentication Tracking**: Monitor authentication failures

### **3. Threat Detection**
- **Anomaly Detection**: Detect unusual patterns
- **Rate Limiting**: Monitor and alert on rate limit violations
- **Security Alerts**: Automatic alerts for security events

## 🔍 Troubleshooting

### **Common Issues**

#### **1. High Error Rates**
**Symptoms**: Error rate > 5%
**Causes**: 
- Database connection issues
- External service failures
- Configuration problems

**Solutions**:
```python
# Check error analytics
error_analytics = logging_service.get_error_analytics(time_range_hours=1)

# Identify top errors
for error, count in error_analytics['top_errors']:
    print(f"Error: {error}, Count: {count}")

# Check error trends
trends = error_analytics['error_trends']
if trends['trend_direction'] == 'increasing':
    print("Error rate is increasing - investigate immediately")
```

#### **2. High Processing Times**
**Symptoms**: Average processing time > 5 seconds
**Causes**:
- Database performance issues
- External API timeouts
- Resource constraints

**Solutions**:
```python
# Get performance metrics
metrics = logging_service.get_performance_metrics(time_range_hours=1)

# Check processing time percentiles
print(f"P95 processing time: {metrics.p95_processing_time:.3f}s")
print(f"P99 processing time: {metrics.p99_processing_time:.3f}s")

# Check for specific event types
event_analytics = logging_service.get_event_analytics(time_range_hours=1)
for group in event_analytics['groups']:
    if group['avg_processing_time'] > 5.0:
        print(f"Slow event type: {group['name']}")
```

#### **3. Low Success Rates**
**Symptoms**: Success rate < 95%
**Causes**:
- Validation failures
- Business logic errors
- Data integrity issues

**Solutions**:
```python
# Get health status
health_status = logging_service.get_health_status()

# Check active issues
for issue in health_status.active_issues:
    if issue['type'] == 'low_success_rate':
        print(f"Success rate issue: {issue['description']}")

# Check recommendations
for recommendation in health_status.recommendations:
    print(f"Recommendation: {recommendation}")
```

### **Debugging Tools**

#### **Enable Debug Logging**
```python
import logging
logging.getLogger('backend.services.webhook_logging_service').setLevel(logging.DEBUG)
```

#### **Check Processing State**
```python
def debug_webhook_processing(event_id: str):
    # Query webhook event records
    event_record = db_session.query(WebhookEventRecord).filter(
        WebhookEventRecord.stripe_event_id == event_id
    ).first()
    
    if event_record:
        print(f"Event ID: {event_record.stripe_event_id}")
        print(f"Status: {event_record.processing_status}")
        print(f"Attempts: {event_record.processing_attempts}")
        print(f"Error: {event_record.error_message}")
        print(f"Processing time: {event_record.processing_completed_at - event_record.processing_started_at}")
    else:
        print("Event not found")
```

## 📈 Performance Optimization

### **Database Optimization**

#### **Indexes**
Ensure proper indexes are created:
```sql
-- Webhook event records
CREATE INDEX idx_webhook_event_timestamp ON webhook_event_records(created_at);
CREATE INDEX idx_webhook_event_type ON webhook_event_records(event_type);
CREATE INDEX idx_webhook_event_status ON webhook_event_records(processing_status);

-- Audit logs
CREATE INDEX idx_audit_log_timestamp ON audit_logs(created_at);
CREATE INDEX idx_audit_log_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_log_severity ON audit_logs(severity);
```

#### **Partitioning**
For high-volume systems, consider table partitioning:
```sql
-- Partition by date for better performance
CREATE TABLE webhook_event_records_2025_01 PARTITION OF webhook_event_records
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### **Caching Strategy**
```python
# Cache frequently accessed metrics
@lru_cache(maxsize=100)
def get_cached_metrics(time_range_hours: int):
    return logging_service.get_performance_metrics(time_range_hours)

# Cache health status
@lru_cache(maxsize=10)
def get_cached_health_status():
    return logging_service.get_health_status()
```

### **Batch Operations**
```python
def batch_log_events(events: List[WebhookEventLog]):
    """Batch log multiple events for better performance"""
    for event in events:
        logging_service.log_webhook_event(
            event_id=event.event_id,
            event_type=event.event_type,
            # ... other parameters
        )
```

## 🚀 Best Practices

### **1. Monitoring Setup**
- Set up automated health checks
- Configure appropriate alerting thresholds
- Monitor key metrics continuously
- Set up dashboards for visualization

### **2. Logging Strategy**
- Use appropriate log levels
- Include relevant metadata
- Structure log data consistently
- Implement log rotation and retention

### **3. Performance Monitoring**
- Monitor processing times regularly
- Track success rates by event type
- Monitor error patterns and trends
- Set up performance alerts

### **4. Security Monitoring**
- Monitor authentication failures
- Track security events
- Monitor IP access patterns
- Set up security alerts

### **5. Maintenance**
- Regular cleanup of old logs
- Monitor database performance
- Update monitoring thresholds
- Review and optimize queries

## 📋 Conclusion

The webhook logging and monitoring system provides comprehensive visibility into webhook processing, enabling reliable operation, quick troubleshooting, and continuous improvement. By following the best practices and monitoring guidelines, you can ensure optimal webhook performance and reliability in your MINGUS application.

The system is designed to be:
- **Comprehensive**: Tracks all aspects of webhook processing
- **Real-time**: Provides immediate visibility into system health
- **Actionable**: Generates alerts and recommendations
- **Scalable**: Handles high-volume webhook processing
- **Secure**: Includes security monitoring and audit trails
- **Maintainable**: Includes cleanup and optimization features 