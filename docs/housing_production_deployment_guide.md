# MINGUS Optimal Living Location - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Optimal Living Location feature to production in the MINGUS application. The guide covers environment configuration, database migration, monitoring, security, documentation, and feature flag management.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Database Migration](#database-migration)
3. [Monitoring & Analytics](#monitoring--analytics)
4. [Security Configuration](#security-configuration)
5. [Documentation](#documentation)
6. [Feature Flag Configuration](#feature-flag-configuration)
7. [Rollback Procedures](#rollback-procedures)
8. [Health Checks](#health-checks)
9. [Troubleshooting](#troubleshooting)

## Environment Configuration

### Production API Keys

Set the following environment variables for production:

```bash
# External API Keys
export RENTALS_API_KEY="your_rentals_api_key"
export ZILLOW_RAPIDAPI_KEY="your_zillow_rapidapi_key"
export GOOGLE_MAPS_API_KEY="your_google_maps_api_key"

# Database Configuration
export DATABASE_URL="postgresql://user:password@host:port/database"
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=30
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600

# Redis Configuration
export REDIS_URL="redis://user:password@host:port/db"
export REDIS_PASSWORD="your_redis_password"
export REDIS_MAX_CONNECTIONS=50

# Security
export SECRET_KEY="your_secret_key"
export HOUSING_ENCRYPTION_KEY="your_encryption_key"

# Rate Limiting
export EXTERNAL_API_RATE_LIMIT=100
export HOUSING_SEARCH_RATE_LIMIT=30
export SCENARIO_RATE_LIMIT=20

# Feature Flags
export HOUSING_ROLLOUT_STRATEGY="percentage"
export HOUSING_ROLLOUT_PERCENTAGE=100

# Monitoring
export SENTRY_DSN="your_sentry_dsn"
export ROLLBACK_NOTIFICATION_WEBHOOK="your_webhook_url"
```

### Rate Limiting Configuration

Configure rate limiting for production traffic:

```python
# config/production_housing_config.py
rate_limiting = {
    'housing_searches': {
        'budget_tier': 5,      # searches per month
        'mid_tier': -1,        # unlimited
        'professional_tier': -1 # unlimited
    },
    'scenario_saves': {
        'budget_tier': 3,      # scenarios saved
        'mid_tier': 10,        # scenarios saved
        'professional_tier': -1 # unlimited
    }
}
```

### Database Connection Pooling

Configure connection pooling for housing data:

```python
# config/production_housing_config.py
database_config = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Redis Cache Configuration

Configure Redis for route caching:

```python
# config/production_housing_config.py
redis_config = {
    'max_connections': 50,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True
}
```

### SSL Certificate Requirements

Ensure SSL certificates are configured for external API calls:

```bash
# SSL Configuration
export VERIFY_SSL=true
export SSL_CERT_PATH="/path/to/cert.pem"
export SSL_KEY_PATH="/path/to/key.pem"
export CA_BUNDLE_PATH="/path/to/ca-bundle.pem"
```

## Database Migration

### Production Migration Scripts

Run the production migration script:

```bash
# Run migration
python migrations/001_housing_production_migration.py

# Verify migration
python -c "from backend.models.database import db; print('Migration successful')"
```

### Index Optimization

The migration script creates optimized indexes for housing search queries:

```sql
-- Housing searches indexes
CREATE INDEX idx_housing_searches_user_created ON housing_searches (user_id, created_at);
CREATE INDEX idx_housing_searches_msa_created ON housing_searches (msa_area, created_at);
CREATE INDEX idx_housing_searches_lease_end ON housing_searches (lease_end_date);

-- Housing scenarios indexes
CREATE INDEX idx_housing_scenarios_user_favorite ON housing_scenarios (user_id, is_favorite);
CREATE INDEX idx_housing_scenarios_created ON housing_scenarios (created_at);

-- Commute route cache indexes
CREATE INDEX idx_commute_cache_route ON commute_route_cache (origin_zip, destination_zip);
CREATE INDEX idx_commute_cache_last_updated ON commute_route_cache (last_updated);
```

### Data Retention Policies

Configure data retention policies:

```python
# config/production_housing_config.py
retention_periods = {
    'housing_searches': 365,      # 1 year
    'housing_scenarios': 1095,    # 3 years
    'commute_route_cache': 30,    # 30 days
    'user_preferences': 1095      # 3 years
}
```

### Backup Strategy

Configure backup strategy for housing data:

```python
# config/production_housing_config.py
backup_config = {
    'enabled': True,
    'frequency': 'daily',
    'retention_days': 30,
    's3_bucket': 'mingus-housing-backups',
    'encryption_key': 'your_encryption_key'
}
```

## Monitoring & Analytics

### Housing Feature Usage Tracking

Integrate housing feature tracking with existing analytics:

```python
# backend/analytics/housing_analytics.py
from backend.analytics.housing_analytics import housing_analytics_tracker

# Track housing search
housing_analytics_tracker.track_housing_search(
    user_id=user_id,
    search_criteria=criteria,
    results_count=len(results),
    response_time_ms=response_time
)
```

### Error Monitoring

Configure error monitoring for external API failures:

```python
# backend/analytics/housing_analytics.py
from backend.analytics.housing_analytics import housing_error_monitor

# Record API error
housing_error_monitor.record_error(
    error_type='api_error',
    error_message=str(e),
    user_id=user_id,
    context={'api_name': 'rentals', 'endpoint': '/search'}
)
```

### Performance Monitoring

Monitor housing search response times:

```python
# backend/analytics/housing_analytics.py
from backend.analytics.housing_analytics import housing_performance_monitor

# Record search performance
housing_performance_monitor.record_search_performance(
    response_time_ms=response_time,
    api_calls=api_calls_made,
    cache_hits=cache_hits,
    results_count=len(results)
)
```

### User Engagement Metrics

Track user engagement with housing features:

```python
# backend/analytics/housing_analytics.py
from backend.analytics.housing_analytics import housing_engagement_analyzer

# Get user engagement metrics
engagement_metrics = housing_engagement_analyzer.get_user_engagement_metrics(
    user_id=user_id,
    days=30
)
```

## Security Configuration

### API Key Rotation Strategy

Configure API key rotation:

```python
# config/housing_security_config.py
from config.housing_security_config import api_key_rotation_manager

# Check if key should be rotated
if api_key_rotation_manager.should_rotate_key('rentals'):
    api_key_rotation_manager.rotate_key('rentals')
```

### Rate Limiting for External API Calls

Configure rate limiting:

```python
# config/housing_security_config.py
from config.housing_security_config import housing_rate_limiter

# Check rate limit
if housing_rate_limiter.is_rate_limited(user_id, 'housing_searches', ip_address):
    return jsonify({'error': 'Rate limit exceeded'}), 429
```

### Input Validation

Validate housing search parameters:

```python
# config/housing_security_config.py
from config.housing_security_config import housing_input_validator

# Validate search criteria
validation_result = housing_input_validator.validate_search_criteria(search_criteria)
if not validation_result['valid']:
    return jsonify({'error': 'Validation failed', 'details': validation_result['errors']}), 400
```

### GDPR Compliance

Ensure GDPR compliance for housing preference data:

```python
# config/housing_security_config.py
from config.housing_security_config import housing_gdpr_compliance

# Encrypt sensitive data
encrypted_data = housing_gdpr_compliance.encrypt_sensitive_data(housing_data)

# Generate data export
data_export = housing_gdpr_compliance.generate_data_export(user_id)
```

## Documentation

### API Documentation

Document housing endpoints:

```markdown
## Housing API Endpoints

### POST /api/housing/search
Search for optimal housing locations

**Request Body:**
```json
{
    "max_rent": 2000,
    "bedrooms": 2,
    "commute_time": 30,
    "zip_code": "30309",
    "housing_type": "apartment"
}
```

**Response:**
```json
{
    "success": true,
    "search_id": 123,
    "listings": [...],
    "total_results": 25
}
```
```

### User Guide

Create user guide for housing location feature:

```markdown
# Optimal Living Location Feature Guide

## Getting Started

1. Navigate to the Housing section in your MINGUS dashboard
2. Set your housing preferences
3. Search for locations
4. Create and compare scenarios

## Features

- **Location Search**: Find housing options based on your criteria
- **Scenario Creation**: Save and compare different housing options
- **Commute Analysis**: Calculate commute costs and times
- **Career Integration**: Analyze career impact of location choices
```

### Admin Documentation

Document admin procedures:

```markdown
# Housing Feature Admin Guide

## Monitoring

- Check health status: `/api/housing/health`
- View analytics: `/admin/housing/analytics`
- Monitor errors: `/admin/housing/errors`

## Maintenance

- Run data cleanup: `python scripts/cleanup_housing_data.py`
- Update feature flags: `/admin/feature-flags`
- Rotate API keys: `python scripts/rotate_api_keys.py`
```

### Troubleshooting Guide

Document common issues and solutions:

```markdown
# Housing Feature Troubleshooting

## Common Issues

### Search Not Returning Results
- Check API key configuration
- Verify rate limiting settings
- Check external API status

### Slow Response Times
- Check database connection pool
- Verify Redis cache status
- Monitor external API response times

### Feature Not Available
- Check user tier permissions
- Verify feature flag settings
- Check rollout percentage
```

## Feature Flag Configuration

### Production Feature Flags

Configure feature flags for gradual rollout:

```python
# deployment/feature-flags/housing_feature_flags.py
from deployment.feature_flags.housing_feature_flags import housing_feature_flags

# Check if feature is enabled
if housing_feature_flags.is_feature_enabled('optimal_location_enabled', user_id, user_tier):
    # Enable feature
    pass
```

### A/B Testing Setup

Configure A/B testing:

```python
# deployment/feature-flags/housing_feature_flags.py
# Get A/B test variant
variant = housing_feature_flags.get_ab_test_variant('search_interface', user_id)
```

### Emergency Kill Switch

Configure emergency kill switch:

```python
# deployment/feature-flags/housing_feature_flags.py
# Activate emergency kill switch
housing_feature_flags.activate_emergency_kill_switch(
    'housing_feature_kill_switch',
    'Critical bug detected',
    'admin@mingus.com'
)
```

### Tier-based Feature Enablement

Configure tier-based access:

```python
# deployment/feature-flags/housing_feature_flags.py
# Check tier-based access
if housing_feature_flags.is_feature_enabled('career_integration_enabled', user_id, 'mid_tier'):
    # Enable career integration
    pass
```

## Rollback Procedures

### Database Rollback

Execute database rollback:

```python
# deployment/rollback/housing_rollback_procedures.py
from deployment.rollback.housing_rollback_procedures import housing_rollback_manager

# Initiate rollback
rollback_id = housing_rollback_manager.initiate_rollback(
    severity=RollbackSeverity.HIGH,
    reason='Critical database issue',
    rollback_type='database',
    initiated_by='admin@mingus.com'
)

# Execute rollback
success = housing_rollback_manager.execute_rollback(rollback_id)
```

### Feature Flag Rollback

Rollback feature flags:

```python
# deployment/rollback/housing_rollback_procedures.py
# Rollback feature flags
rollback_id = housing_rollback_manager.initiate_rollback(
    severity=RollbackSeverity.MEDIUM,
    reason='Feature causing issues',
    rollback_type='feature_flags',
    initiated_by='admin@mingus.com'
)
```

### Emergency Response

Emergency response procedures:

```python
# deployment/rollback/housing_rollback_procedures.py
# Full system rollback
rollback_id = housing_rollback_manager.initiate_rollback(
    severity=RollbackSeverity.CRITICAL,
    reason='System-wide issue',
    rollback_type='full',
    initiated_by='admin@mingus.com'
)
```

## Health Checks

### API Health Checks

Run API health checks:

```python
# deployment/rollback/housing_rollback_procedures.py
from deployment.rollback.housing_rollback_procedures import housing_health_checker

# Run health checks
health_results = housing_health_checker.run_health_checks()
print(f"Overall status: {health_results['overall_status']}")
```

### Database Health Checks

Check database health:

```python
# Check database connectivity
with db.engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Database connection: OK")
```

### External API Health Checks

Check external API health:

```python
# Check external APIs
for api in ['rentals', 'zillow', 'google_maps']:
    try:
        # Make test API call
        response = requests.get(f"{api}_health_endpoint", timeout=5)
        print(f"{api} API: OK")
    except Exception as e:
        print(f"{api} API: FAILED - {e}")
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify API keys are set correctly
   - Check API key rotation status
   - Verify API quotas

2. **Database Issues**
   - Check connection pool status
   - Verify migration was successful
   - Check database indexes

3. **Rate Limiting Issues**
   - Check rate limit configuration
   - Verify user tier permissions
   - Monitor API usage

4. **Feature Flag Issues**
   - Check feature flag status
   - Verify rollout percentage
   - Check emergency switches

### Monitoring Commands

```bash
# Check application health
curl -f http://localhost:5000/health

# Check housing feature health
curl -f http://localhost:5000/api/housing/health

# Check database status
python -c "from backend.models.database import db; print('DB OK')"

# Check Redis status
redis-cli ping

# Check feature flags
python -c "from deployment.feature_flags.housing_feature_flags import housing_feature_flags; print(housing_feature_flags.get_all_feature_flags())"
```

### Log Analysis

```bash
# Check application logs
tail -f logs/mingus.log | grep "housing"

# Check error logs
tail -f logs/error.log | grep "housing"

# Check API logs
tail -f logs/api.log | grep "housing"
```

## Conclusion

This guide provides comprehensive instructions for deploying the Optimal Living Location feature to production. Follow the steps carefully and monitor the system closely during the initial rollout period.

For additional support, contact the MINGUS development team or refer to the troubleshooting guide.
