# Communication System Configuration Guide

## Overview

This guide covers the complete configuration setup for the MINGUS Communication System, including Celery, SMS (Twilio), Email (Resend), rate limiting, cost tracking, and compliance settings.

## Configuration Files

### 1. Base Configuration (`config/base.py`)
Contains core communication settings integrated into the main Flask configuration.

### 2. Communication Configuration (`config/communication.py`)
Dedicated communication-specific configuration with environment-specific classes.

### 3. Environment Template (`config/communication.env.template`)
Template file for environment variables.

## Quick Setup

### 1. Environment Variables

Copy the template and configure your environment:

```bash
# Copy the template
cp config/communication.env.template .env

# Edit with your actual values
nano .env
```

### 2. Required Environment Variables

#### Celery Configuration
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=false
```

#### Twilio SMS Configuration
```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_SECRET=your_twilio_webhook_secret_here
```

#### Resend Email Configuration
```bash
RESEND_API_KEY=your_resend_api_key_here
RESEND_FROM_EMAIL=noreply@mingusapp.com
RESEND_FROM_NAME=MINGUS Financial Wellness
RESEND_WEBHOOK_SECRET=your_resend_webhook_secret_here
```

## Configuration Sections

### Celery Configuration

#### Broker and Backend
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

#### Task Configuration
```python
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_RESULT_EXPIRES = 3600  # 1 hour
```

#### Task Routes
```python
CELERY_TASK_ROUTES = {
    'backend.tasks.mingus_celery_tasks.send_critical_financial_alert': {
        'queue': 'sms_critical',
        'routing_key': 'sms.critical'
    },
    'backend.tasks.mingus_celery_tasks.send_monthly_report': {
        'queue': 'email_reports',
        'routing_key': 'email.reports'
    }
}
```

#### Beat Schedule
```python
CELERY_BEAT_SCHEDULE = {
    'monitor-queue-depth': {
        'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
        'schedule': 300.0,  # Every 5 minutes
    },
    'send-weekly-checkins': {
        'task': 'backend.tasks.mingus_celery_tasks.send_weekly_checkin',
        'schedule': 604800.0,  # Every week
    }
}
```

### SMS Configuration (Twilio)

#### API Credentials
```python
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
```

#### Rate Limits
```python
SMS_RATE_LIMITS = {
    'critical': 500,    # per minute
    'normal': 100,      # per minute
    'daily': 10000,     # per day
    'hourly': 1000      # per hour
}
```

#### Cost Tracking
```python
SMS_COST_PER_MESSAGE = 0.05  # $0.05 per SMS
SMS_COST_PER_MMS = 0.10      # $0.10 per MMS
```

#### Message Limits
```python
SMS_MAX_LENGTH = 160          # Standard SMS length
SMS_MAX_LENGTH_UNICODE = 70   # Unicode SMS length
SMS_MAX_SEGMENTS = 10         # Maximum segments
```

### Email Configuration (Resend)

#### API Credentials
```python
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RESEND_FROM_EMAIL = 'noreply@mingusapp.com'
RESEND_FROM_NAME = 'MINGUS Financial Wellness'
```

#### Rate Limits
```python
EMAIL_RATE_LIMITS = {
    'critical': 1000,   # per minute
    'normal': 200,      # per minute
    'daily': 50000,     # per day
    'hourly': 5000      # per hour
}
```

#### Cost Tracking
```python
EMAIL_COST_PER_MESSAGE = 0.001  # $0.001 per email
```

### Communication Cost Tracking

#### Budget Settings
```python
COMMUNICATION_COSTS = {
    'sms': 0.05,                    # $0.05 per SMS
    'email': 0.001,                 # $0.001 per email
    'daily_budget': 100.0,          # $100 daily budget
    'monthly_budget': 3000.0,       # $3000 monthly budget
    'alert_threshold': 0.8          # 80% of budget
}
```

### User Communication Limits

#### Per-User Limits
```python
USER_COMMUNICATION_LIMITS = {
    'daily_max': 5,        # Max 5 communications per day
    'hourly_max': 2,       # Max 2 communications per hour
    'weekly_max': 20,      # Max 20 communications per week
    'monthly_max': 80,     # Max 80 communications per month
    'sms_daily_max': 3,    # Max 3 SMS per day
    'email_daily_max': 2   # Max 2 emails per day
}
```

### Communication Timing Preferences

#### Business Hours and Timing
```python
COMMUNICATION_TIMING = {
    'business_hours_start': 9,      # 9 AM
    'business_hours_end': 17,       # 5 PM
    'timezone_default': 'UTC',
    'weekend_communications': False,
    'holiday_communications': False,
    'quiet_hours_start': 22,        # 10 PM
    'quiet_hours_end': 8,           # 8 AM
    'timezone_aware': True
}
```

### Communication Retry Configuration

#### Retry Settings
```python
COMMUNICATION_RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 300,             # 5 minutes
    'exponential_backoff': True,
    'retry_jitter': 0.1,            # 10% jitter
    'retry_on_failure': True,
    'retry_on_timeout': True,
    'retry_on_rate_limit': True
}
```

### Communication Analytics Configuration

#### Analytics Settings
```python
COMMUNICATION_ANALYTICS = {
    'track_delivery_rates': True,
    'track_open_rates': True,
    'track_click_rates': True,
    'track_conversion_rates': True,
    'track_bounce_rates': True,
    'track_unsubscribe_rates': True,
    'analytics_retention_days': 365,
    'enable_ab_testing': True,
    'ab_test_sample_size': 1000,
    'track_user_engagement': True,
    'track_financial_impact': True,
    'enable_real_time_tracking': True
}
```

### Communication Compliance Settings

#### Compliance Configuration
```python
COMMUNICATION_COMPLIANCE = {
    'tcpa_compliance': True,
    'gdpr_compliance': True,
    'can_spam_compliance': True,
    'require_explicit_consent': True,
    'opt_out_required': True,
    'consent_audit_trail': True,
    'data_retention_days': 2555,    # 7 years
    'privacy_policy_url': 'https://mingusapp.com/privacy',
    'terms_of_service_url': 'https://mingusapp.com/terms',
    'unsubscribe_url': 'https://mingusapp.com/unsubscribe',
    'preference_center_url': 'https://mingusapp.com/preferences'
}
```

### Communication Webhook Configuration

#### Webhook Settings
```python
COMMUNICATION_WEBHOOKS = {
    'twilio_webhook_url': '/webhooks/twilio',
    'resend_webhook_url': '/webhooks/resend',
    'webhook_timeout': 30,          # 30 seconds
    'webhook_retries': 3,
    'webhook_secret_validation': True,
    'webhook_rate_limiting': True,
    'webhook_logging': True
}
```

### Communication Monitoring and Alerting

#### Monitoring Configuration
```python
COMMUNICATION_MONITORING = {
    'enable_delivery_monitoring': True,
    'enable_cost_monitoring': True,
    'enable_rate_limit_monitoring': True,
    'enable_performance_monitoring': True,
    'delivery_rate_threshold': 0.95,    # 95%
    'cost_threshold_alert': 50.0,       # $50
    'rate_limit_alert_threshold': 0.8,  # 80%
    'performance_threshold_ms': 5000,   # 5 seconds
    'alert_channels': ['email', 'slack'],
    'alert_recipients': ['alerts@mingusapp.com']
}
```

## Environment-Specific Configurations

### Development Configuration
```python
class DevelopmentCommunicationConfig(CommunicationConfig):
    DEBUG = True
    CELERY_ALWAYS_EAGER = True
    COMMUNICATION_TESTING = {
        'enable_test_mode': True,
        'enable_mock_services': True,
        'enable_debug_logging': True
    }
```

### Production Configuration
```python
class ProductionCommunicationConfig(CommunicationConfig):
    DEBUG = False
    CELERY_ALWAYS_EAGER = False
    COMMUNICATION_TESTING = {
        'enable_test_mode': False,
        'enable_mock_services': False,
        'enable_debug_logging': False
    }
```

### Testing Configuration
```python
class TestingCommunicationConfig(CommunicationConfig):
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    COMMUNICATION_TESTING = {
        'enable_test_mode': True,
        'enable_mock_services': True,
        'enable_debug_logging': True
    }
```

## Usage Examples

### Using Configuration in Code

```python
from flask import current_app

# Access configuration values
celery_broker = current_app.config['CELERY_BROKER_URL']
sms_rate_limit = current_app.config['SMS_RATE_LIMITS']['critical']
email_cost = current_app.config['EMAIL_COST_PER_MESSAGE']

# Check if features are enabled
if current_app.config['COMMUNICATION_ANALYTICS']['enable_ab_testing']:
    # Run A/B test
    pass

# Get user limits
daily_limit = current_app.config['USER_COMMUNICATION_LIMITS']['daily_max']
```

### Environment-Specific Configuration

```python
# In your app factory
def create_app(config_name='development'):
    if config_name == 'development':
        app.config.from_object('config.communication.DevelopmentCommunicationConfig')
    elif config_name == 'production':
        app.config.from_object('config.communication.ProductionCommunicationConfig')
    elif config_name == 'testing':
        app.config.from_object('config.communication.TestingCommunicationConfig')
```

## Configuration Validation

### Required Environment Variables

The following environment variables are required for production:

```bash
# Celery
CELERY_BROKER_URL
CELERY_RESULT_BACKEND

# Twilio
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER

# Resend
RESEND_API_KEY
RESEND_FROM_EMAIL

# Security
JWT_SECRET_KEY
SECRET_KEY
```

### Validation Script

Create a validation script to check configuration:

```python
def validate_communication_config():
    """Validate communication configuration"""
    required_vars = [
        'CELERY_BROKER_URL',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'RESEND_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    print("Communication configuration validation passed!")
```

## Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secrets for each environment
- Rotate API keys regularly
- Use environment-specific secrets

### API Keys and Secrets
```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For FIELD_ENCRYPTION_KEY
```

### Webhook Security
```python
# Validate webhook signatures
def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

## Performance Optimization

### Redis Configuration
```bash
# Redis configuration for high performance
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Celery Optimization
```python
# Celery worker configuration
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
```

### Database Optimization
```python
# Database connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 30
}
```

## Monitoring and Alerting

### Health Checks
```python
# Communication system health check
def check_communication_health():
    health_status = {
        'celery': check_celery_health(),
        'twilio': check_twilio_health(),
        'resend': check_resend_health(),
        'redis': check_redis_health(),
        'database': check_database_health()
    }
    return health_status
```

### Metrics Collection
```python
# Key metrics to monitor
COMMUNICATION_METRICS = [
    'delivery_rate',
    'cost_per_message',
    'queue_depth',
    'response_time',
    'error_rate',
    'user_engagement'
]
```

## Troubleshooting

### Common Issues

1. **Celery Connection Issues**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Check Celery worker status
   celery -A backend.tasks.mingus_celery_tasks inspect active
   ```

2. **Twilio API Issues**
   ```python
   # Test Twilio credentials
   from twilio.rest import Client
   client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
   try:
       client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
       print("Twilio credentials valid")
   except Exception as e:
       print(f"Twilio error: {e}")
   ```

3. **Resend API Issues**
   ```python
   # Test Resend credentials
   import resend
   resend.api_key = RESEND_API_KEY
   try:
       response = resend.Emails.send({
           "from": RESEND_FROM_EMAIL,
           "to": "test@example.com",
           "subject": "Test",
           "html": "<p>Test</p>"
       })
       print("Resend credentials valid")
   except Exception as e:
       print(f"Resend error: {e}")
   ```

### Debug Mode
```bash
# Enable debug logging
export COMM_DEBUG_LOGGING=true
export CELERY_ALWAYS_EAGER=true
export COMM_TEST_MODE=true
```

## Best Practices

1. **Environment Separation**: Use different configurations for development, staging, and production
2. **Secret Management**: Use secure secret management systems in production
3. **Monitoring**: Implement comprehensive monitoring and alerting
4. **Rate Limiting**: Always implement rate limiting to prevent abuse
5. **Cost Tracking**: Monitor communication costs to stay within budget
6. **Compliance**: Ensure all communications comply with relevant regulations
7. **Testing**: Use mock services in development and testing environments
8. **Documentation**: Keep configuration documentation up to date
9. **Backup**: Regularly backup configuration and data
10. **Security**: Regularly audit and update security settings 