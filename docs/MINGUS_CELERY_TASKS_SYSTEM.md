# MINGUS Celery Tasks System

## Overview

The MINGUS Celery Tasks System provides comprehensive asynchronous processing for all SMS and Email communications with proper prioritization, error handling, and integration with the MINGUS financial app ecosystem.

## Architecture

### Task Prioritization

The system implements a priority-based queue structure:

| Priority | Queue | Task Type | Description |
|----------|-------|-----------|-------------|
| 1 | `sms_critical` | Critical Financial Alerts | Overdraft, security alerts |
| 2 | `sms_daily` | Payment Reminders | Bills due, subscriptions |
| 3 | `sms_daily` | Weekly Checkins | Wellness, engagement |
| 4 | `sms_daily` | Milestone Reminders | Birthdays, goals |
| 5 | `email_reports` | Monthly Reports | Financial wellness analysis |
| 6 | `email_education` | Career Insights | Job market, skills |
| 7 | `email_education` | Educational Content | Learning materials |
| 8 | `email_education` | Onboarding Sequence | New user welcome |

### External Service Integration

- **Twilio**: SMS delivery service
- **Resend**: Email delivery service
- **Redis**: Queue management and caching
- **PostgreSQL**: User data and analytics storage

## Core SMS Tasks

### 1. send_critical_financial_alert()

**Priority**: 1 (Highest)
**Queue**: `sms_critical`
**Rate Limit**: 10/minute

**Purpose**: Send immediate alerts for critical financial situations

**Features**:
- Immediate delivery with highest priority
- TCPA compliance checking
- Exponential backoff retry (3 attempts)
- Fallback to email for failed deliveries
- Cost tracking and analytics

**Usage**:
```python
send_critical_financial_alert.delay(
    user_id="user_123",
    alert_data={
        "template": "Critical: {message}",
        "message": "Overdraft detected on account ending in 1234",
        "urgency": "high"
    }
)
```

### 2. send_payment_reminder()

**Priority**: 2
**Queue**: `sms_daily`
**Rate Limit**: 20/minute

**Purpose**: Remind users about upcoming payments

**Features**:
- Payment-specific personalization
- Bill amount and due date inclusion
- 2 retry attempts with 5-minute backoff
- User preference validation

**Usage**:
```python
send_payment_reminder.delay(
    user_id="user_123",
    payment_data={
        "template": "Reminder: {bill_name} due {due_date} - ${amount}",
        "bill_name": "Electric Bill",
        "due_date": "2025-01-15",
        "amount": "125.50"
    }
)
```

### 3. send_weekly_checkin()

**Priority**: 3
**Queue**: `sms_daily`
**Rate Limit**: 50/minute

**Purpose**: Weekly wellness and engagement checkins

**Features**:
- Wellness-focused messaging
- Engagement tracking
- 2 retry attempts with 10-minute backoff
- Batch processing capability

**Usage**:
```python
send_weekly_checkin.delay(
    user_id="user_123",
    checkin_data={
        "template": "Weekly check-in: {message}",
        "message": "How's your financial wellness this week?",
        "wellness_score": 85
    }
)
```

### 4. send_milestone_reminder()

**Priority**: 4
**Queue**: `sms_daily`
**Rate Limit**: 30/minute

**Purpose**: Celebrate user achievements and milestones

**Features**:
- Celebration-focused messaging
- Emoji support
- 1 retry attempt with 15-minute backoff
- Goal achievement tracking

**Usage**:
```python
send_milestone_reminder.delay(
    user_id="user_123",
    milestone_data={
        "template": "🎉 {milestone_name} achieved! {message}",
        "milestone_name": "Emergency Fund Goal",
        "message": "You've saved $5,000!",
        "goal_amount": 5000
    }
)
```

## Core Email Tasks

### 1. send_monthly_report()

**Priority**: 5
**Queue**: `email_reports`
**Rate Limit**: 10/minute

**Purpose**: Send comprehensive monthly financial reports

**Features**:
- Rich HTML content
- Financial analysis charts
- 2 retry attempts with 30-minute backoff
- GDPR compliance checking

**Usage**:
```python
send_monthly_report.delay(
    user_id="user_123",
    report_data={
        "subject": "Your Monthly Financial Report - January 2025",
        "html_content": "<h1>Monthly Report</h1><p>Your financial summary...</p>",
        "spending_summary": {...},
        "savings_progress": {...}
    }
)
```

### 2. send_career_insights()

**Priority**: 6
**Queue**: `email_education`
**Rate Limit**: 20/minute

**Purpose**: Provide career advancement opportunities

**Features**:
- Job market analysis
- Skill gap identification
- Salary benchmarking
- 2 retry attempts with 30-minute backoff

**Usage**:
```python
send_career_insights.delay(
    user_id="user_123",
    career_data={
        "subject": "Career Opportunities for You",
        "html_content": "<h1>Career Insights</h1><p>New opportunities...</p>",
        "job_opportunities": [...],
        "skill_recommendations": [...]
    }
)
```

### 3. send_educational_content()

**Priority**: 7
**Queue**: `email_education`
**Rate Limit**: 30/minute

**Purpose**: Deliver educational financial content

**Features**:
- Learning material delivery
- Topic personalization
- 2 retry attempts with 30-minute backoff
- Content engagement tracking

**Usage**:
```python
send_educational_content.delay(
    user_id="user_123",
    education_data={
        "subject": "Financial Education: {topic}",
        "html_content": "<h1>Investment Basics</h1><p>Learn about...</p>",
        "topic": "Investment Basics",
        "difficulty": "beginner"
    }
)
```

### 4. send_onboarding_sequence()

**Priority**: 8
**Queue**: `email_education`
**Rate Limit**: 50/minute

**Purpose**: Welcome new users with onboarding sequence

**Features**:
- Multi-email sequence
- Welcome messaging
- Feature introduction
- 3 retry attempts with 15-minute backoff

**Usage**:
```python
send_onboarding_sequence.delay(
    user_id="user_123",
    onboarding_data={
        "subject": "Welcome to MINGUS!",
        "html_content": "<h1>Welcome!</h1><p>Get started with...</p>",
        "sequence_step": 1,
        "total_steps": 5
    }
)
```

## Monitoring and Analytics Tasks

### 1. monitor_queue_depth()

**Schedule**: Every 5 minutes
**Purpose**: Monitor Celery queue depths

**Features**:
- Real-time queue monitoring
- Threshold-based alerts
- Performance tracking
- 1 retry attempt with 5-minute backoff

### 2. track_delivery_rates()

**Schedule**: Every 30 minutes
**Purpose**: Track message delivery success rates

**Features**:
- 24-hour delivery rate calculation
- Analytics database updates
- Performance reporting
- 1 retry attempt with 10-minute backoff

### 3. analyze_user_engagement()

**Schedule**: Every hour
**Purpose**: Analyze user engagement patterns

**Features**:
- Hourly engagement analysis
- Pattern recognition
- Optimization recommendations
- 1 retry attempt with 30-minute backoff

### 4. process_failed_messages()

**Schedule**: Every 15 minutes
**Purpose**: Process and retry failed messages

**Features**:
- Failed message identification
- Automatic retry logic
- Fallback channel selection
- 2 retry attempts with 5-minute backoff

### 5. optimize_send_timing()

**Schedule**: Every 2 hours
**Purpose**: Optimize send timing based on engagement

**Features**:
- Engagement pattern analysis
- Optimal time calculation
- Redis caching of results
- 1 retry attempt with 60-minute backoff

## Helper Functions

### validate_user_preferences()

Validates user consent and preferences before sending communications.

**Parameters**:
- `user_id`: User identifier
- `channel`: Communication channel (SMS/EMAIL)
- `alert_type`: Type of alert

**Returns**:
- `(can_send, reason)`: Tuple of boolean and reason string

**Features**:
- TCPA compliance checking for SMS
- GDPR compliance checking for email
- Alert type preference validation
- Consent status verification

### track_communication_cost()

Tracks communication costs for billing and analytics.

**Parameters**:
- `user_id`: User identifier
- `channel`: Communication channel
- `message_type`: Type of message
- `success`: Delivery success status

**Features**:
- Real-time cost tracking in Redis
- Per-user daily cost aggregation
- Analytics logging
- Billing integration

### log_delivery_status()

Logs delivery status to database for analytics and compliance.

**Parameters**:
- `user_id`: User identifier
- `channel`: Communication channel
- `message_type`: Type of message
- `message_id`: External service message ID
- `status`: Delivery status
- `error_message`: Error message if failed

**Features**:
- Database logging
- External service message ID tracking
- Error message storage
- Compliance audit trail

### handle_failed_delivery()

Handles failed message delivery with fallback logic.

**Parameters**:
- `user_id`: User identifier
- `channel`: Communication channel
- `message_type`: Type of message
- `error_message`: Error message

**Features**:
- Automatic fallback channel selection
- Retry logic for critical messages
- Analytics updates
- Error logging

### generate_personalized_content()

Generates personalized message content based on user data.

**Parameters**:
- `user_id`: User identifier
- `template`: Message template
- `personalization_data`: Data for personalization

**Returns**:
- Personalized message content

**Features**:
- User name personalization
- Dynamic data insertion
- Template variable replacement
- Error handling

## Configuration

### Environment Variables

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Resend Configuration
RESEND_API_KEY=your_resend_api_key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Cost Tracking Constants

```python
SMS_COST_PER_MESSAGE = Decimal('0.0075')  # $0.0075 per SMS
EMAIL_COST_PER_MESSAGE = Decimal('0.0001')  # $0.0001 per email
```

### Rate Limiting

```python
RATE_LIMITS = {
    'critical_financial': {'sms': '10/m', 'email': '5/m'},
    'payment_reminder': {'sms': '20/m', 'email': '10/m'},
    'weekly_checkin': {'sms': '50/m', 'email': '25/m'},
    'milestone_reminder': {'sms': '30/m', 'email': '15/m'},
    'monthly_report': {'sms': '0/m', 'email': '10/m'},
    'career_insights': {'sms': '0/m', 'email': '20/m'},
    'educational_content': {'sms': '0/m', 'email': '30/m'},
    'onboarding_sequence': {'sms': '100/m', 'email': '50/m'}
}
```

## Error Handling

### Retry Logic

Each task implements exponential backoff retry logic:

- **Critical SMS**: 3 retries, 60-second base delay
- **Payment Reminders**: 2 retries, 5-minute base delay
- **Weekly Checkins**: 2 retries, 10-minute base delay
- **Milestone Reminders**: 1 retry, 15-minute base delay
- **Email Tasks**: 2-3 retries, 15-30 minute base delay

### Fallback Mechanisms

- **SMS Failure**: Fallback to email for critical messages
- **Email Failure**: Fallback to SMS for urgent communications
- **Service Unavailable**: Queue message for later retry
- **User Unavailable**: Log and skip delivery

### Error Logging

All errors are logged with:
- User identifier
- Task type
- Error message
- Stack trace
- Retry attempt number
- Timestamp

## Security Considerations

### Data Protection

- User data encryption in transit and at rest
- Secure API key management
- Database connection security
- Redis access control

### Compliance

- TCPA compliance for SMS communications
- GDPR compliance for email communications
- Consent tracking and management
- Opt-out request handling

### Access Control

- Task-level authentication
- User preference validation
- Rate limiting per user
- Queue access control

## Performance Optimization

### Queue Management

- Priority-based task routing
- Queue depth monitoring
- Automatic scaling based on load
- Dead letter queue for failed tasks

### Caching

- Redis caching for user preferences
- Optimal send time caching
- Cost tracking aggregation
- Performance metrics caching

### Database Optimization

- Connection pooling
- Query optimization
- Index usage
- Batch processing

## Monitoring and Alerting

### Queue Monitoring

- Real-time queue depth tracking
- Threshold-based alerts
- Performance metrics
- Error rate monitoring

### Delivery Monitoring

- Success rate tracking
- Delivery time monitoring
- Cost tracking
- User engagement metrics

### System Health

- Service availability monitoring
- Error rate tracking
- Performance metrics
- Resource utilization

## Deployment

### Celery Worker Commands

```bash
# Start workers for specific queues
celery -A backend.tasks.mingus_celery_tasks worker --loglevel=info -Q sms_critical,sms_daily,email_reports,email_education

# Start Celery beat for scheduled tasks
celery -A backend.tasks.mingus_celery_tasks beat --loglevel=info

# Start Flower for monitoring
celery -A backend.tasks.mingus_celery_tasks flower
```

### Docker Deployment

```yaml
version: '3.8'
services:
  celery-worker:
    build: .
    command: celery -A backend.tasks.mingus_celery_tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres

  celery-beat:
    build: .
    command: celery -A backend.tasks.mingus_celery_tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
```

## Testing

### Unit Tests

```python
def test_send_critical_financial_alert():
    """Test critical financial alert sending"""
    result = send_critical_financial_alert.delay(
        user_id="test_user",
        alert_data={"template": "Test alert", "message": "Test message"}
    )
    assert result.get() == True
```

### Integration Tests

```python
def test_sms_delivery_integration():
    """Test SMS delivery with Twilio integration"""
    # Mock Twilio client
    with patch('twilio.rest.Client'):
        result = send_critical_financial_alert.delay(
            user_id="test_user",
            alert_data={"template": "Test", "message": "Test"}
        )
        assert result.get() == True
```

## Troubleshooting

### Common Issues

1. **Task Not Executing**
   - Check Celery worker status
   - Verify queue configuration
   - Check Redis connectivity

2. **SMS Delivery Failures**
   - Verify Twilio credentials
   - Check phone number format
   - Review TCPA compliance

3. **Email Delivery Failures**
   - Verify Resend API key
   - Check email format
   - Review GDPR compliance

4. **High Queue Depth**
   - Scale up workers
   - Check task processing rate
   - Review rate limiting

### Debug Commands

```bash
# Check queue depths
celery -A backend.tasks.mingus_celery_tasks inspect active_queues

# Check worker status
celery -A backend.tasks.mingus_celery_tasks inspect active

# Monitor tasks
celery -A backend.tasks.mingus_celery_tasks events
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Predictive send timing
   - Content personalization
   - Engagement optimization

2. **Advanced Analytics**
   - Real-time dashboards
   - Predictive modeling
   - A/B testing framework

3. **Multi-channel Support**
   - Push notifications
   - In-app messaging
   - Webhook integrations

4. **Advanced Scheduling**
   - Timezone-aware scheduling
   - User preference learning
   - Dynamic frequency adjustment 