# Daily Outlook Celery Tasks System

## Overview

The Daily Outlook Celery Tasks System provides automated background processing for daily outlook pre-generation, notification delivery, and content optimization in the Mingus Personal Finance Application. This system ensures users receive personalized daily insights at optimal times while continuously improving content performance.

## Architecture

### Core Components

1. **Daily Outlook Pre-generation** - Batch generation of personalized outlooks for all active users
2. **Timezone-Aware Notifications** - Intelligent notification delivery based on user preferences and timezones
3. **Content Performance Optimization** - Weekly analysis and A/B testing for content improvements
4. **Health Monitoring** - System health checks and performance monitoring

### Database Integration

The system integrates with existing Mingus models:
- `DailyOutlook` - Stores generated outlook content and user interactions
- `User` - User profiles and notification preferences
- `UserRelationshipStatus` - Relationship context for personalization

## Tasks

### 1. Daily Outlook Pre-generation (`generate_daily_outlooks_batch`)

**Schedule**: Every day at 5:00 AM UTC
**Purpose**: Pre-generate personalized daily outlooks for all active users

**Features**:
- Processes all active users (active within last 30 days)
- Generates personalized content using `DailyOutlookContentService`
- Handles duplicate prevention (skips existing outlooks unless forced)
- Comprehensive error handling with retry logic
- Performance metrics and logging

**Parameters**:
- `target_date` (optional): Date to generate outlooks for (defaults to tomorrow)
- `force_regenerate` (optional): Force regeneration even if outlooks exist

**Returns**:
```json
{
  "success": true,
  "target_date": "2024-01-15",
  "task_id": "abc123",
  "total_users": 150,
  "generated_count": 145,
  "skipped_count": 3,
  "failed_count": 2,
  "errors": []
}
```

### 2. Daily Outlook Notifications (`send_daily_outlook_notifications`)

**Schedule**: Every day at 6:45 AM UTC (handles timezone conversion internally)
**Purpose**: Send push notifications to users at their preferred times

**Features**:
- Timezone-aware delivery (6:45 AM weekdays, 8:30 AM weekends by default)
- Integration with existing notification system
- User preference handling
- Delivery tracking and metrics
- Graceful error handling

**Parameters**:
- `target_date` (optional): Date to send notifications for (defaults to today)

**Returns**:
```json
{
  "success": true,
  "target_date": "2024-01-15",
  "task_id": "def456",
  "total_users": 145,
  "notifications_sent": 140,
  "failed_count": 5,
  "errors": []
}
```

### 3. Content Performance Optimization (`optimize_content_performance`)

**Schedule**: Weekly on Sunday at 3:00 AM UTC
**Purpose**: Analyze content performance and trigger improvements

**Features**:
- Performance metrics analysis (view rates, engagement, ratings)
- Low-performing content identification
- A/B testing triggers for improvements
- Content template updates
- Optimization recommendations

**Parameters**:
- `analysis_period_days` (optional): Days to analyze (default 7)

**Returns**:
```json
{
  "success": true,
  "analysis_period": {
    "start_date": "2024-01-08",
    "end_date": "2024-01-15",
    "days": 7
  },
  "performance_metrics": {
    "total_outlooks": 1000,
    "view_rate": 0.75,
    "engagement_rate": 0.45,
    "average_rating": 4.2,
    "completion_rate": 0.35
  },
  "low_performing_content": [...],
  "recommendations": [...],
  "ab_tests_triggered": 2,
  "templates_updated": 1
}
```

### 4. Health Monitoring (`health_check_daily_outlook_tasks`)

**Schedule**: Every 4 hours
**Purpose**: Monitor system health and performance

**Features**:
- Database connectivity checks
- Recent task performance analysis
- Active user count monitoring
- System status reporting

## Configuration

### Celery Configuration

The system uses a dedicated Celery queue (`daily_outlook_queue`) with the following settings:

```python
# Task settings
task_time_limit = 600  # 10 minutes for content generation
task_soft_time_limit = 540  # 9 minutes
max_retries = 3
default_retry_delay = 300  # 5 minutes
```

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Notification Settings
NOTIFICATION_ENABLED=true
DEFAULT_WEEKDAY_TIME=06:45
DEFAULT_WEEKEND_TIME=08:30
```

## Setup and Deployment

### 1. Celery Worker Setup

Start Celery worker for daily outlook tasks:

```bash
# Start Celery worker
celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue

# Start Celery Beat for scheduled tasks
celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info
```

### 2. Database Migration

Ensure the following models are available:
- `DailyOutlook` model with all required fields
- `User` model with notification preferences
- Proper indexes for performance

### 3. Notification Integration

The system integrates with existing notification infrastructure:
- Push notifications via FCM/APNS
- Email notifications via SMTP
- WebSocket real-time updates
- Notification history tracking

## Monitoring and Analytics

### Performance Metrics

The system tracks comprehensive metrics:

1. **Generation Metrics**:
   - Total users processed
   - Success/failure rates
   - Processing time per user
   - Content quality scores

2. **Notification Metrics**:
   - Delivery rates by timezone
   - User engagement rates
   - Notification preferences usage
   - Error patterns

3. **Content Performance**:
   - View rates by content type
   - User engagement patterns
   - Rating distributions
   - Action completion rates

### Health Monitoring

Regular health checks monitor:
- Database connectivity
- Task queue performance
- Error rates and patterns
- System resource usage

## Error Handling

### Retry Logic

All tasks implement exponential backoff retry logic:
- **Pre-generation**: 3 retries with 5-minute base delay
- **Notifications**: 2 retries with 1-minute base delay
- **Optimization**: 2 retries with 5-minute base delay

### Error Recovery

The system includes comprehensive error recovery:
- Database connection failures
- Service unavailability
- Invalid user data
- Notification delivery failures

### Logging

Detailed logging at multiple levels:
- **INFO**: Task progress and completion
- **WARNING**: Non-critical issues
- **ERROR**: Task failures and retries
- **DEBUG**: Detailed operation tracing

## API Integration

### Manual Task Triggers

Tasks can be triggered manually via API:

```python
# Generate outlooks for specific date
from backend.tasks.daily_outlook_tasks import generate_daily_outlooks_batch
result = generate_daily_outlooks_batch.delay(target_date='2024-01-15')

# Send notifications immediately
from backend.tasks.daily_outlook_tasks import send_daily_outlook_notifications
result = send_daily_outlook_notifications.delay()

# Run content optimization
from backend.tasks.daily_outlook_tasks import optimize_content_performance
result = optimize_content_performance.delay(analysis_period_days=14)
```

### Status Monitoring

Check task status and results:

```python
# Check task status
task_id = result.id
status = result.status
result_data = result.result

# Get task info
from celery.result import AsyncResult
task_result = AsyncResult(task_id)
```

## Best Practices

### 1. Resource Management

- Monitor queue sizes and processing times
- Scale workers based on user growth
- Implement circuit breakers for external services

### 2. Data Quality

- Validate user data before processing
- Handle edge cases gracefully
- Maintain data consistency

### 3. Performance Optimization

- Use database indexes effectively
- Implement caching for frequently accessed data
- Monitor and optimize slow queries

### 4. User Experience

- Respect user notification preferences
- Handle timezone differences correctly
- Provide fallback content for failures

## Troubleshooting

### Common Issues

1. **Task Failures**:
   - Check database connectivity
   - Verify user data integrity
   - Review error logs for specific issues

2. **Notification Delivery**:
   - Verify notification service configuration
   - Check user timezone settings
   - Review delivery metrics

3. **Performance Issues**:
   - Monitor queue backlogs
   - Check database performance
   - Review system resources

### Debug Commands

```bash
# Check Celery worker status
celery -A backend.tasks.daily_outlook_tasks inspect active

# Monitor task queues
celery -A backend.tasks.daily_outlook_tasks inspect scheduled

# Check task results
celery -A backend.tasks.daily_outlook_tasks inspect stats
```

## Future Enhancements

### Planned Features

1. **Advanced Personalization**:
   - Machine learning-based content optimization
   - Dynamic content templates
   - User behavior prediction

2. **Enhanced Analytics**:
   - Real-time performance dashboards
   - Predictive analytics
   - A/B testing framework

3. **Scalability Improvements**:
   - Horizontal scaling support
   - Load balancing
   - Geographic distribution

### Integration Opportunities

1. **External Services**:
   - Weather API integration
   - News API for contextual content
   - Calendar integration for scheduling

2. **Advanced Notifications**:
   - Multi-channel delivery
   - Smart notification timing
   - User preference learning

## Support

For issues or questions regarding the Daily Outlook Tasks System:

1. Check the logs for error details
2. Verify Celery worker status
3. Review database connectivity
4. Check notification service configuration

The system is designed to be robust and self-healing, but manual intervention may be required for critical issues.
