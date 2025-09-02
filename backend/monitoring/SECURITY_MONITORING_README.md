# Security Performance Monitoring System

## Overview

The Security Performance Monitoring System provides comprehensive monitoring for security system performance with minimal impact on system operations. It tracks encryption/decryption timing, audit logging performance, key rotation performance, and overall security system health.

## Features

### 🔒 Security System Performance Metrics
- **Real-time monitoring** of security operations
- **Performance thresholds** with automatic alerting
- **Success rate tracking** for all security operations
- **Response time monitoring** with detailed analytics

### 🔐 Encryption/Decryption Timing
- **Algorithm-specific performance** tracking (AES, RSA, etc.)
- **Key size impact** analysis
- **Operation type monitoring** (encrypt/decrypt)
- **Data size correlation** with performance

### 📊 Audit Logging Performance
- **Logging operation timing** measurement
- **Batch processing performance** tracking
- **Log size monitoring** and optimization
- **Backlog detection** and alerting

### 🔑 Key Rotation Performance
- **Rotation duration** tracking
- **Affected entities** counting
- **Success rate monitoring** for key operations
- **Compliance tracking** for key rotation schedules

### 🏥 PCI Compliance Monitoring
- **Real-time compliance status** checking
- **Key rotation compliance** verification
- **Audit logging compliance** monitoring
- **Security monitoring compliance** validation

## Architecture

### Components

1. **SecurityPerformanceMonitor** - Core monitoring class
2. **Health Check Endpoints** - REST API health checks
3. **Database Tables** - Metrics storage and analysis
4. **Prometheus Integration** - Metrics export for external monitoring
5. **Background Processing** - Asynchronous metrics processing

### Database Schema

#### Core Tables
- `security_performance_metrics` - General security operation metrics
- `encryption_performance_metrics` - Encryption-specific performance data
- `audit_log_performance_metrics` - Audit logging performance data
- `key_rotation_performance_metrics` - Key rotation performance data
- `security_monitoring_summary` - Real-time summary data

#### Views
- `security_performance_summary` - Hourly aggregated security metrics
- `encryption_performance_summary` - Hourly aggregated encryption metrics
- `audit_log_performance_summary` - Hourly aggregated audit metrics

## Installation

### 1. Database Setup

Run the setup script to create necessary tables:

```bash
cd backend/monitoring
python setup_security_monitoring.py
```

### 2. Environment Variables

Set the following environment variables:

```bash
export DATABASE_URL="postgresql://user:password@localhost/mingus_db"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

### 3. Dependencies

Install required packages:

```bash
pip install prometheus-client psutil loguru sqlalchemy
```

## Usage

### Basic Monitoring

```python
from backend.monitoring.security_monitor import SecurityPerformanceMonitor
from sqlalchemy.orm import Session

# Initialize monitor
db_session = Session()
monitor = SecurityPerformanceMonitor(db_session)

# Monitor security operations
with monitor.measure_security_operation('user_authentication', {'user_id': '123'}):
    # Your security operation here
    authenticate_user(user_id='123')

# Monitor encryption operations
with monitor.measure_encryption_operation('AES-256', 256, 'encrypt', 1024):
    # Your encryption operation here
    encrypted_data = encrypt_data(data, key)

# Monitor audit logging
with monitor.measure_audit_logging('user_login', 512):
    # Your audit logging here
    log_user_login(user_id='123', timestamp=datetime.utcnow())
```

### Health Check Endpoints

#### General Health Check
```bash
GET /health/detailed
```

#### Security-Specific Health Check
```bash
GET /health/security
```

#### Individual Component Checks
```bash
GET /health/readiness
GET /health/liveness
GET /health/startup
```

### Performance Monitoring

#### Get Performance Summary
```python
# Get 24-hour performance summary
summary = monitor.get_performance_summary(hours=24)

# Get real-time metrics
realtime = monitor.get_real_time_metrics()
```

#### Clean Up Old Data
```python
# Clean up metrics older than 30 days
monitor.cleanup_old_metrics(days_to_keep=30)
```

## Configuration

### Performance Thresholds

```python
monitor.performance_thresholds = {
    'encryption_max_duration_ms': 100,      # 100ms max for encryption
    'audit_log_max_duration_ms': 50,        # 50ms max for audit logging
    'key_rotation_max_duration_ms': 5000,   # 5s max for key rotation
    'security_operation_max_duration_ms': 200  # 200ms max for security ops
}
```

### Prometheus Metrics

The system automatically exports the following Prometheus metrics:

- `security_operations_total` - Total security operations by type and status
- `security_operation_duration_seconds` - Duration of security operations
- `encryption_operation_duration_seconds` - Encryption operation duration
- `audit_log_performance_seconds` - Audit logging performance
- `key_rotation_duration_seconds` - Key rotation duration
- `security_system_health_score` - Overall security system health (0-100)
- `pci_compliance_status` - PCI compliance status (1=compliant, 0=non-compliant)

## Monitoring Dashboard

### Security Health Score

The system calculates a real-time health score (0-100) based on:
- **Success rates** of security operations
- **Performance thresholds** compliance
- **Error counts** and frequency
- **System resource** utilization

### PCI Compliance Status

Real-time monitoring of:
- **Encryption key rotation** schedules
- **Audit logging** completeness
- **Security monitoring** activity
- **Access control** configuration

### Performance Alerts

Automatic alerts for:
- **Slow operations** exceeding thresholds
- **High failure rates** in security operations
- **Audit log backlogs** and delays
- **Key rotation** delays

## Best Practices

### 1. Minimal Performance Impact
- **Batch processing** of metrics for database operations
- **Asynchronous processing** in background threads
- **Efficient indexing** on timestamp and operation columns
- **Partitioned tables** for large datasets

### 2. Real-time Monitoring
- **Immediate storage** of critical metrics
- **Real-time health score** calculation
- **Instant alerting** for threshold violations
- **Live dashboard** updates

### 3. Scalability
- **Horizontal partitioning** by time periods
- **Efficient cleanup** of old data
- **Optimized queries** using database views
- **Connection pooling** for database operations

### 4. Security
- **No sensitive data** in metrics
- **Access control** on monitoring endpoints
- **Audit logging** of monitoring access
- **Encrypted storage** of metrics data

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database connectivity
python -c "from sqlalchemy import create_engine; engine = create_engine('your_db_url'); print(engine.execute('SELECT 1').scalar())"
```

#### 2. Performance Issues
```python
# Check current performance thresholds
print(monitor.performance_thresholds)

# Analyze performance bottlenecks
summary = monitor.get_performance_summary(hours=1)
print(summary['overall_performance'])
```

#### 3. Missing Metrics
```python
# Verify tables exist
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print([t for t in tables if 'security' in t or 'encryption' in t or 'audit' in t])
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor with detailed logging
with monitor.measure_security_operation('debug_operation', {'debug': True}):
    # Operation with detailed logging
    pass
```

## API Reference

### SecurityPerformanceMonitor

#### Methods

- `measure_security_operation(operation_type, metadata)` - Context manager for security operations
- `measure_encryption_operation(algorithm, key_size, operation, data_size_bytes)` - Context manager for encryption
- `measure_audit_logging(operation_type, log_size_bytes, batch_size)` - Context manager for audit logging
- `measure_key_rotation(key_type, old_key_id, new_key_id)` - Context manager for key rotation
- `get_performance_summary(hours)` - Get performance summary for time period
- `get_real_time_metrics()` - Get current real-time metrics
- `cleanup_old_metrics(days_to_keep)` - Clean up old metrics data

### Health Check Functions

- `check_security_system_health()` - Check overall security system health
- `check_pci_compliance_status()` - Check PCI compliance status
- `check_encryption_system_health()` - Check encryption system health
- `check_audit_system_performance()` - Check audit system performance

## Contributing

### Adding New Metrics

1. **Define metric structure** in appropriate dataclass
2. **Add storage method** for the new metric type
3. **Update health checks** to include new metrics
4. **Add Prometheus metrics** if needed
5. **Update documentation** and examples

### Performance Optimization

1. **Profile database queries** for slow operations
2. **Optimize indexes** based on query patterns
3. **Implement caching** for frequently accessed data
4. **Use batch operations** for bulk data processing

## License

This security monitoring system is part of the Mingus Application and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Verify database connectivity and permissions
4. Contact the development team with specific error messages
