# MINGUS Integration Features Guide

## Overview

This guide covers the comprehensive MINGUS integration features that provide immediate feature access updates, user notification triggers, and analytics event tracking for subscription lifecycle events.

## Table of Contents

1. [Feature Access Integration](#feature-access-integration)
2. [User Notification Integration](#user-notification-integration)
3. [Analytics Event Tracking](#analytics-event-tracking)
4. [Performance Monitoring](#performance-monitoring)
5. [Integration Workflows](#integration-workflows)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Feature Access Integration

### Overview

The Feature Access Integration provides immediate updates to user feature access when subscription changes occur, ensuring users have instant access to their subscribed features.

### Key Components

#### FeatureAccessService

The core service responsible for managing feature access updates:

```python
from backend.services.feature_access_service import FeatureAccessService

# Initialize service
feature_service = FeatureAccessService(db_session, config)

# Update feature access immediately
result = feature_service.update_feature_access_immediately(
    customer_id="customer_123",
    subscription_tier="premium",
    subscription_status="active",
    subscription_data={...}
)
```

#### Feature Access Levels

- **BASIC**: Core features, basic analytics, email support
- **PREMIUM**: Advanced analytics, custom reporting, priority support, API access
- **ENTERPRISE**: Enterprise analytics, custom dashboards, dedicated support, unlimited API access
- **UNLIMITED**: All features, custom development, dedicated account manager

#### Feature Access Update Methods

1. **Immediate Updates**: Real-time feature access changes
2. **Grace Period Management**: Limited access during cancellation
3. **Trial Ending Restrictions**: Feature limitations for trial users
4. **Cache Invalidation**: Immediate cache updates for instant access

### Integration Points

#### Webhook Integration

Feature access updates are automatically triggered by webhook events:

```python
# In StripeWebhookManager
def _execute_business_logic_for_subscription_created(self, customer, subscription, subscription_data):
    # ... business logic execution ...
    
    # Immediate feature access update
    if result['success']:
        feature_update_result = self._update_feature_access_immediately(
            customer, subscription, subscription_data
        )
        result['feature_access_updated'] = feature_update_result['success']
        result['changes'].extend(feature_update_result['changes'])
```

#### Cache Management

User-specific caches are automatically invalidated:

```python
def _invalidate_user_cache(self, user_id: str):
    cache_keys = [
        f"user_features:{user_id}",
        f"user_subscription:{user_id}",
        f"user_access:{user_id}",
        f"user_permissions:{user_id}"
    ]
    
    for cache_key in cache_keys:
        performance_optimizer.invalidate_cache(cache_key)
```

## User Notification Integration

### Overview

The User Notification Integration provides multi-channel notifications for subscription events, ensuring users are informed of important changes to their accounts.

### Key Components

#### NotificationService

The core service responsible for sending notifications:

```python
from backend.services.notification_service import NotificationService, NotificationType

# Initialize service
notification_service = NotificationService(db_session, config)

# Send welcome notifications
result = notification_service.send_welcome_notifications(notification_data)
```

#### Notification Channels

- **Email**: Primary communication channel
- **SMS**: Urgent notifications and reminders
- **Push**: Real-time mobile notifications
- **In-App**: Application-specific notifications
- **Slack**: Team collaboration notifications
- **Webhook**: External system integrations

#### Notification Types

- **WELCOME**: New subscription welcome messages
- **SUBSCRIPTION_CREATED**: Subscription creation confirmations
- **SUBSCRIPTION_UPDATED**: Subscription change notifications
- **SUBSCRIPTION_CANCELLED**: Cancellation confirmations
- **TRIAL_ENDING**: Trial expiration warnings
- **FEATURE_ACCESS_GRANTED**: Feature access notifications
- **FEATURE_ACCESS_REVOKED**: Feature removal notifications

### Integration Points

#### Webhook Integration

Notifications are automatically triggered by webhook events:

```python
# In StripeWebhookManager
def _trigger_user_notifications(self, customer, subscription, event_type, feature_update_result):
    # Prepare notification data
    notification_data = {
        'customer_id': str(customer.id),
        'user_id': str(customer.user_id) if customer.user_id else None,
        'subscription_id': str(subscription.id),
        'subscription_tier': subscription.pricing_tier,
        'subscription_status': subscription.status,
        'event_type': event_type,
        'feature_changes': feature_update_result
    }
    
    # Trigger notifications based on event type
    if event_type == "subscription_created":
        welcome_result = notification_service.send_welcome_notifications(notification_data)
        feature_result = notification_service.send_feature_access_notifications(notification_data)
```

#### Personalization

Notifications are personalized based on user preferences:

```python
def _personalize_content(self, template, template_data, user_preferences):
    personalized = {}
    
    for key, value in template.items():
        if isinstance(value, str):
            personalized_value = value
            for var_name, var_value in template_data.items():
                placeholder = f"{{{{{var_name}}}}}"
                if isinstance(var_value, list):
                    var_value = ', '.join(var_value)
                personalized_value = personalized_value.replace(placeholder, str(var_value))
            personalized[key] = personalized_value
    
    return personalized
```

## Analytics Event Tracking

### Overview

The Analytics Event Tracking system provides comprehensive tracking of subscription lifecycle events for business intelligence and user behavior analysis.

### Key Components

#### EventTracker

The core service responsible for tracking analytics events:

```python
from backend.analytics.event_tracker import EventTracker, EventType

# Initialize service
event_tracker = EventTracker(db_session, config)

# Track subscription creation
result = event_tracker.track_subscription_created(analytics_data)
```

#### Event Types

- **SUBSCRIPTION_CREATED**: New subscription events
- **SUBSCRIPTION_UPDATED**: Subscription modification events
- **SUBSCRIPTION_CANCELLED**: Subscription cancellation events
- **FEATURE_ACCESS_GRANTED**: Feature access events
- **FEATURE_ACCESS_REVOKED**: Feature removal events
- **CONVERSION**: Conversion events
- **CHURN**: Churn events
- **TRIAL_ENDING**: Trial expiration events

#### Event Categories

- **SUBSCRIPTION**: Subscription lifecycle events
- **FEATURE**: Feature access events
- **USER**: User behavior events
- **BUSINESS**: Business metrics events
- **PAYMENT**: Payment-related events

### Integration Points

#### Webhook Integration

Analytics events are automatically tracked by webhook events:

```python
# In StripeWebhookManager
def _track_analytics_events(self, customer, subscription, event_type, feature_update_result):
    # Prepare analytics data
    analytics_data = {
        'customer_id': str(customer.id),
        'user_id': str(customer.user_id) if customer.user_id else None,
        'subscription_id': str(subscription.id),
        'subscription_tier': subscription.pricing_tier,
        'subscription_status': subscription.status,
        'event_type': event_type,
        'feature_changes': feature_update_result,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    # Track events based on event type
    if event_type == "subscription_created":
        subscription_event = event_tracker.track_subscription_created(analytics_data)
        feature_event = event_tracker.track_feature_access_granted(analytics_data)
        conversion_event = event_tracker.track_conversion_event(analytics_data)
```

#### Real-time Tracking

Events are tracked in real-time for immediate analytics:

```python
def _update_real_time_metrics(self, event_data: EventData):
    # Update real-time metrics in cache/database
    logger.info(f"Real-time metric update for event: {event_data.event_type.value}")
```

## Performance Monitoring

### Overview

Performance monitoring provides insights into the performance of integration features, helping identify bottlenecks and optimize system performance.

### Key Metrics

#### Feature Access Metrics

- **Access Updates**: Number of feature access updates
- **Cache Hits/Misses**: Cache performance metrics
- **Average Update Time**: Processing time for updates
- **Success Rate**: Percentage of successful updates

#### Notification Metrics

- **Notifications Sent**: Number of notifications sent
- **Notifications Failed**: Number of failed notifications
- **Average Send Time**: Processing time for notifications
- **Channel Performance**: Performance by notification channel

#### Analytics Metrics

- **Events Tracked**: Number of events tracked
- **Events Failed**: Number of failed events
- **Average Tracking Time**: Processing time for events
- **Real-time Events**: Number of real-time events

### Integration Points

#### Performance Recording

Performance metrics are automatically recorded:

```python
def _record_feature_access_metric(self, operation: str, processing_time: float, success: bool):
    performance_optimizer.record_webhook_event(
        event_type=f"feature_access_{operation}",
        processing_time=processing_time,
        success=success
    )
```

#### Performance Optimization

The PerformanceOptimizer provides caching and optimization:

```python
def _invalidate_user_cache(self, user_id: str):
    cache_keys = [
        f"user_features:{user_id}",
        f"user_subscription:{user_id}",
        f"user_access:{user_id}",
        f"user_permissions:{user_id}"
    ]
    
    for cache_key in cache_keys:
        performance_optimizer.invalidate_cache(cache_key)
```

## Integration Workflows

### Complete Subscription Creation Workflow

1. **Webhook Receipt**: Stripe webhook received
2. **Security Validation**: Signature verification and rate limiting
3. **Business Logic Execution**: Core business rules applied
4. **Feature Access Update**: Immediate feature access changes
5. **User Notifications**: Multi-channel notifications sent
6. **Analytics Tracking**: Events tracked for analysis
7. **Performance Monitoring**: Metrics recorded
8. **Audit Trail**: Complete audit trail logged

### Feature Access Update Workflow

1. **Event Detection**: Subscription change detected
2. **Access Level Determination**: New access level calculated
3. **Feature Mapping**: Features mapped to access level
4. **Database Update**: Feature access updated in database
5. **Cache Invalidation**: User caches invalidated
6. **Audit Logging**: Access change logged
7. **Performance Recording**: Metrics recorded

### Notification Workflow

1. **Event Trigger**: Notification event triggered
2. **User Preferences**: User notification preferences retrieved
3. **Template Selection**: Appropriate template selected
4. **Content Personalization**: Content personalized for user
5. **Channel Selection**: Enabled channels determined
6. **Rate Limiting**: Rate limits checked
7. **Notification Sending**: Notifications sent through channels
8. **Delivery Tracking**: Delivery status tracked
9. **Performance Recording**: Metrics recorded

## Configuration

### Feature Access Configuration

```python
feature_config = {
    'tiers': {
        'basic': {
            'features': ['core_features', 'basic_analytics', 'email_support'],
            'access_level': FeatureAccessLevel.BASIC,
            'limits': {
                'api_calls_per_day': 1000,
                'storage_gb': 5,
                'users': 1
            }
        },
        'premium': {
            'features': ['core_features', 'premium_analytics', 'advanced_api', 'priority_support'],
            'access_level': FeatureAccessLevel.PREMIUM,
            'limits': {
                'api_calls_per_day': 10000,
                'storage_gb': 50,
                'users': 5
            }
        }
    }
}
```

### Notification Configuration

```python
notification_config = {
    'channels': {
        'email': {
            'enabled': True,
            'priority': 1,
            'rate_limit': 10,  # per hour
            'templates': {
                'welcome': 'email_welcome_template',
                'subscription_created': 'email_subscription_created_template'
            }
        },
        'sms': {
            'enabled': True,
            'priority': 2,
            'rate_limit': 5,  # per hour
            'templates': {
                'welcome': 'sms_welcome_template',
                'trial_ending': 'sms_trial_ending_template'
            }
        }
    }
}
```

### Analytics Configuration

```python
tracking_config = {
    'enabled': True,
    'batch_size': 100,
    'flush_interval_seconds': 60,
    'max_retry_attempts': 3,
    'event_ttl_days': 365,
    'real_time_tracking': True,
    'aggregation_enabled': True
}
```

## Testing

### Test Scripts

Comprehensive test scripts are provided for all integration features:

```bash
# Run feature access tests
python examples/test_feature_access.py

# Run notification tests
python examples/test_notifications.py

# Run analytics tests
python examples/test_analytics.py

# Run complete integration tests
python examples/test_mingus_integration.py
```

### Test Coverage

- **Feature Access Tests**: Immediate updates, grace periods, trial restrictions
- **Notification Tests**: Multi-channel delivery, personalization, rate limiting
- **Analytics Tests**: Event tracking, real-time metrics, data validation
- **Performance Tests**: Processing times, cache performance, optimization
- **Integration Tests**: Complete workflows, error handling, recovery

### Test Reports

Detailed test reports are generated automatically:

```json
{
  "feature_access_tests": [
    {
      "test_name": "Subscription Created - Basic Tier",
      "success": true,
      "processing_time_ms": 45.2,
      "features_updated": 3
    }
  ],
  "notification_tests": [
    {
      "test_name": "Welcome Notifications",
      "success": true,
      "notifications_sent": 4,
      "channels_used": ["email", "sms", "push", "in_app"],
      "processing_time_ms": 125.8
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### Feature Access Not Updating

1. **Check Cache**: Verify cache invalidation is working
2. **Database Connection**: Ensure database connection is active
3. **Permissions**: Verify user has necessary permissions
4. **Configuration**: Check feature access configuration

#### Notifications Not Sending

1. **Channel Configuration**: Verify channels are enabled
2. **Rate Limiting**: Check if rate limits are exceeded
3. **User Preferences**: Verify user notification preferences
4. **Template Issues**: Check notification templates

#### Analytics Events Not Tracking

1. **Event Configuration**: Verify event definitions
2. **Database Connection**: Ensure analytics database is accessible
3. **Real-time Tracking**: Check real-time tracking configuration
4. **Event Validation**: Verify event data validation

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Performance Monitoring

```python
# Get performance metrics
feature_metrics = feature_service.get_performance_metrics()
notification_metrics = notification_service.get_performance_metrics()
analytics_metrics = event_tracker.get_performance_metrics()
```

#### Audit Trail

```python
# Check audit trail
audit_events = audit_service.get_audit_events(
    user_id="user_123",
    start_date=datetime.now() - timedelta(days=1),
    end_date=datetime.now()
)
```

### Support

For additional support:

1. **Documentation**: Review this guide and related documentation
2. **Logs**: Check application logs for detailed error information
3. **Metrics**: Monitor performance metrics for system health
4. **Testing**: Run test scripts to verify functionality
5. **Configuration**: Verify all configuration settings

## Conclusion

The MINGUS Integration Features provide a comprehensive solution for managing subscription lifecycle events with immediate feature access updates, multi-channel notifications, and detailed analytics tracking. These features ensure a seamless user experience while providing valuable business intelligence and performance monitoring capabilities.

For more information, refer to the individual service documentation and test scripts provided in the examples directory. 