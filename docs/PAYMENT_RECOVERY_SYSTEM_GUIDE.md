# Payment Recovery System Guide

## Overview

The Payment Recovery System for MINGUS is a comprehensive solution designed to maximize subscription retention and revenue recovery through intelligent payment failure handling, automated recovery strategies, and sophisticated dunning management.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Payment Failure Handling](#payment-failure-handling)
3. [Recovery Strategies](#recovery-strategies)
4. [Dunning Management](#dunning-management)
5. [Payment Retry Mechanisms](#payment-retry-mechanisms)
6. [Grace Period Management](#grace-period-management)
7. [Analytics and Reporting](#analytics-and-reporting)
8. [Configuration](#configuration)
9. [Integration](#integration)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

## System Architecture

### Core Components

#### PaymentRecoverySystem

The main system class that orchestrates all payment recovery operations:

```python
from backend.billing.payment_recovery import PaymentRecoverySystem

# Initialize the system
recovery_system = PaymentRecoverySystem(db_session, config)
```

#### Database Models

- **PaymentRecoveryRecord**: Tracks payment failures and recovery attempts
- **DunningEvent**: Records dunning communication events
- **RecoveryAction**: Scheduled and executed recovery actions
- **PaymentFailure**: Historical payment failure data
- **RecoveryStrategyConfig**: Recovery strategy configurations
- **DunningSchedule**: Dunning schedule configurations

#### Key Enumerations

```python
class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"

class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RECOVERED = "recovered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class DunningStage(Enum):
    SOFT_FAILURE = "soft_failure"
    HARD_FAILURE = "hard_failure"
    DUNNING_1 = "dunning_1"
    DUNNING_2 = "dunning_2"
    DUNNING_3 = "dunning_3"
    DUNNING_4 = "dunning_4"
    DUNNING_5 = "dunning_5"
    FINAL_NOTICE = "final_notice"
    CANCELLATION = "cancellation"
    RECOVERY = "recovery"

class RecoveryStrategy(Enum):
    AUTOMATIC_RETRY = "automatic_retry"
    PAYMENT_METHOD_UPDATE = "payment_method_update"
    GRACE_PERIOD = "grace_period"
    PARTIAL_PAYMENT = "partial_payment"
    PAYMENT_PLAN = "payment_plan"
    MANUAL_INTERVENTION = "manual_intervention"
    CANCELLATION = "cancellation"
```

## Payment Failure Handling

### Automatic Failure Detection

The system automatically detects payment failures from Stripe webhooks and initiates recovery processes:

```python
# Handle payment failure
result = recovery_system.handle_payment_failure(
    customer_id="customer_123",
    subscription_id="sub_456",
    invoice_id="inv_789",
    payment_intent_id="pi_012",
    failure_reason="card_declined",
    failure_code="card_declined",
    amount=99.99,
    currency="usd"
)
```

### Failure Categorization

The system categorizes failures into different types for appropriate handling:

- **card_declined**: Card declined by issuer
- **insufficient_funds**: Insufficient funds in account
- **expired_card**: Card has expired
- **fraudulent**: Suspected fraudulent transaction
- **processing_error**: Payment processing error
- **unknown**: Unknown failure reason

### Immediate Actions

Upon failure detection, the system performs immediate actions:

1. **Create Failure Record**: Store failure details in database
2. **Determine Strategy**: Select appropriate recovery strategy
3. **Send Notifications**: Immediate customer notification
4. **Schedule Actions**: Plan follow-up recovery actions
5. **Update Status**: Update customer payment status

## Recovery Strategies

### Strategy Selection

The system automatically selects recovery strategies based on failure type and customer value:

```python
# Strategy mapping by failure type
recovery_strategies = {
    'card_declined': [
        RecoveryStrategy.AUTOMATIC_RETRY,
        RecoveryStrategy.PAYMENT_METHOD_UPDATE,
        RecoveryStrategy.GRACE_PERIOD
    ],
    'insufficient_funds': [
        RecoveryStrategy.AUTOMATIC_RETRY,
        RecoveryStrategy.PARTIAL_PAYMENT,
        RecoveryStrategy.PAYMENT_PLAN
    ],
    'expired_card': [
        RecoveryStrategy.PAYMENT_METHOD_UPDATE,
        RecoveryStrategy.GRACE_PERIOD
    ],
    'fraudulent': [
        RecoveryStrategy.MANUAL_INTERVENTION
    ],
    'processing_error': [
        RecoveryStrategy.AUTOMATIC_RETRY,
        RecoveryStrategy.MANUAL_INTERVENTION
    ]
}
```

### Strategy Types

#### Automatic Retry

Automatically retry failed payments with exponential backoff:

```python
# Retry payment
result = recovery_system.retry_payment(
    failure_id="failure_123",
    payment_method_id="pm_456"  # Optional new payment method
)
```

#### Payment Method Update

Prompt customer to update payment method:

```python
# Update payment method
result = recovery_system.update_payment_method(
    customer_id="customer_123",
    new_payment_method_id="pm_new_456"
)
```

#### Grace Period

Provide temporary access while resolving payment issues:

```python
# Manage grace period
result = recovery_system.manage_grace_period(
    customer_id="customer_123",
    grace_period_days=7
)
```

#### Partial Payment

Accept partial payments to reduce outstanding balance:

```python
# Configure partial payment threshold
recovery_config = {
    'partial_payment_threshold': 0.5  # 50% of original amount
}
```

#### Payment Plan

Create installment plans for large amounts:

```python
# Payment plan configuration
payment_plan_config = {
    'max_installments': 3,
    'min_amount_per_installment': 10.0
}
```

#### Manual Intervention

Escalate to customer support for complex cases:

```python
# Manual intervention triggers
manual_intervention_triggers = [
    'fraudulent_transaction',
    'high_value_customer',
    'multiple_failures',
    'customer_request'
]
```

## Dunning Management

### Dunning Schedule

The system implements a comprehensive dunning schedule with escalating communication:

```python
dunning_schedule = {
    DunningStage.SOFT_FAILURE: DunningSchedule(
        stage=DunningStage.SOFT_FAILURE,
        delay_days=0,
        notification_type='immediate_notification',
        retry_attempt=True,
        payment_method_update=False
    ),
    DunningStage.HARD_FAILURE: DunningSchedule(
        stage=DunningStage.HARD_FAILURE,
        delay_days=1,
        notification_type='payment_failed_notification',
        retry_attempt=True,
        payment_method_update=True
    ),
    DunningStage.DUNNING_1: DunningSchedule(
        stage=DunningStage.DUNNING_1,
        delay_days=3,
        notification_type='dunning_notification_1',
        retry_attempt=True,
        payment_method_update=True
    ),
    DunningStage.DUNNING_2: DunningSchedule(
        stage=DunningStage.DUNNING_2,
        delay_days=7,
        notification_type='dunning_notification_2',
        retry_attempt=True,
        payment_method_update=True,
        grace_period_days=3
    ),
    DunningStage.FINAL_NOTICE: DunningSchedule(
        stage=DunningStage.FINAL_NOTICE,
        delay_days=30,
        notification_type='final_notice',
        retry_attempt=False,
        payment_method_update=True,
        grace_period_days=30
    ),
    DunningStage.CANCELLATION: DunningSchedule(
        stage=DunningStage.CANCELLATION,
        delay_days=35,
        notification_type='cancellation_notice',
        retry_attempt=False,
        payment_method_update=False
    )
}
```

### Communication Channels

Dunning communications are sent through multiple channels:

- **Email**: Primary communication channel
- **SMS**: Urgent notifications and reminders
- **Push**: Real-time mobile notifications
- **In-App**: Application-specific notifications
- **Slack**: Team collaboration notifications

### Notification Types

- **immediate_notification**: Instant failure notification
- **payment_failed_notification**: Detailed failure explanation
- **dunning_notification_1-5**: Escalating payment reminders
- **final_notice**: Last chance payment reminder
- **cancellation_notice**: Subscription cancellation notification

## Payment Retry Mechanisms

### Retry Configuration

```python
recovery_config = {
    'max_retry_attempts': 5,
    'retry_intervals_days': [1, 3, 7, 14, 30],
    'recovery_timeout_days': 90,
    'auto_cancellation_days': 30
}
```

### Retry Logic

The system implements intelligent retry logic:

1. **Exponential Backoff**: Increasing delays between retries
2. **Smart Timing**: Retry during optimal payment times
3. **Payment Method Rotation**: Try different payment methods
4. **Amount Adjustment**: Retry with partial amounts
5. **Customer Segmentation**: Different strategies for different customer tiers

### Retry Execution

```python
# Process scheduled retry actions
result = recovery_system.process_recovery_actions()

# Manual retry
result = recovery_system.retry_payment(
    failure_id="failure_123",
    payment_method_id="pm_456"
)
```

## Grace Period Management

### Grace Period Configuration

```python
grace_period_config = {
    'standard_grace_period_days': 7,
    'enterprise_customer_grace_period': 14,
    'high_value_threshold': 100.0,
    'grace_period_features': ['core_features'],
    'grace_period_limits': {
        'api_calls_per_day': 100,
        'storage_gb': 1,
        'users': 1
    }
}
```

### Grace Period Features

During grace periods, customers retain limited access:

- **Core Features**: Essential functionality remains available
- **Reduced Limits**: Lower usage limits applied
- **Payment Reminders**: Regular payment update prompts
- **Easy Reactivation**: Simple process to restore full access

### Grace Period Management

```python
# Manage grace period
result = recovery_system.manage_grace_period(
    customer_id="customer_123",
    grace_period_days=7
)

# Check grace period status
grace_period_status = recovery_system.get_grace_period_status(
    customer_id="customer_123"
)
```

## Analytics and Reporting

### Recovery Analytics

Comprehensive analytics for monitoring recovery performance:

```python
# Get recovery analytics
analytics = recovery_system.get_recovery_analytics(days=30)

# Analytics data includes:
# - Total failures
# - Successful recoveries
# - Recovery rate
# - Revenue at risk
# - Recovered revenue
# - Failure reasons breakdown
# - Strategy effectiveness
```

### Key Metrics

- **Recovery Rate**: Percentage of failed payments successfully recovered
- **Revenue Recovery Rate**: Percentage of revenue at risk that was recovered
- **Average Recovery Time**: Time to successful recovery
- **Strategy Effectiveness**: Success rate by recovery strategy
- **Failure Pattern Analysis**: Common failure reasons and patterns

### Performance Metrics

```python
# Get performance metrics
metrics = recovery_system.get_performance_metrics()

# Metrics include:
# - Recovery attempts
# - Successful recoveries
# - Failed recoveries
# - Average recovery time
# - Recovery rate
# - Revenue recovered
```

### Reporting

The system provides detailed reports for:

- **Daily Recovery Summary**: Daily recovery performance
- **Monthly Recovery Report**: Monthly trends and analysis
- **Strategy Effectiveness Report**: Performance by recovery strategy
- **Customer Recovery Report**: Recovery performance by customer segment
- **Revenue Impact Report**: Revenue impact of recovery efforts

## Configuration

### System Configuration

```python
recovery_config = {
    'max_retry_attempts': 5,
    'retry_intervals_days': [1, 3, 7, 14, 30],
    'grace_period_days': 7,
    'partial_payment_threshold': 0.5,
    'recovery_timeout_days': 90,
    'auto_cancellation_days': 30,
    'high_value_threshold': 100.0,
    'enterprise_customer_grace_period': 14,
    'notification_channels': ['email', 'sms', 'in_app']
}
```

### Strategy Configuration

```python
strategy_config = {
    'card_declined': {
        'max_retries': 3,
        'retry_intervals': [1, 3, 7],
        'notification_channels': ['email', 'sms']
    },
    'insufficient_funds': {
        'max_retries': 5,
        'retry_intervals': [1, 3, 7, 14, 30],
        'partial_payment_enabled': True
    },
    'expired_card': {
        'max_retries': 1,
        'payment_method_update_required': True,
        'grace_period_days': 7
    }
}
```

### Dunning Configuration

```python
dunning_config = {
    'enabled': True,
    'max_dunning_stages': 5,
    'final_notice_delay_days': 30,
    'cancellation_delay_days': 35,
    'notification_channels': ['email', 'sms', 'push', 'in_app'],
    'escalation_enabled': True
}
```

## Integration

### Webhook Integration

The system integrates with Stripe webhooks for automatic failure detection:

```python
# Webhook event handling
def handle_stripe_webhook(event):
    if event.type == 'invoice.payment_failed':
        recovery_system.handle_payment_failure(
            customer_id=event.data.object.customer,
            subscription_id=event.data.object.subscription,
            invoice_id=event.data.object.id,
            payment_intent_id=event.data.object.payment_intent,
            failure_reason=event.data.object.last_payment_error.reason,
            failure_code=event.data.object.last_payment_error.code,
            amount=event.data.object.amount_due / 100,
            currency=event.data.object.currency
        )
```

### Notification Integration

Integrates with the notification system for customer communications:

```python
# Send dunning notification
notification_service.send_dunning_notifications({
    'customer_id': customer_id,
    'dunning_stage': dunning_stage,
    'failure_reason': failure_reason,
    'amount': amount,
    'currency': currency
})
```

### Analytics Integration

Integrates with analytics system for tracking and reporting:

```python
# Track recovery event
event_tracker.track_payment_recovery_success({
    'customer_id': customer_id,
    'event_type': 'payment_recovery_success',
    'amount': amount,
    'currency': currency,
    'failure_reason': failure_reason
})
```

## Testing

### Test Scripts

Comprehensive test scripts are provided:

```bash
# Run payment recovery tests
python examples/test_payment_recovery.py
```

### Test Coverage

- **Failure Handling Tests**: Payment failure detection and processing
- **Recovery Strategy Tests**: Strategy determination and execution
- **Dunning Tests**: Dunning schedule and communication
- **Retry Tests**: Payment retry mechanisms
- **Grace Period Tests**: Grace period management
- **Analytics Tests**: Recovery analytics and reporting
- **Integration Tests**: Complete workflow testing

### Test Scenarios

- Card declined failures
- Insufficient funds scenarios
- Expired card handling
- Fraudulent transaction detection
- Processing error recovery
- High-value customer handling
- Enterprise customer scenarios

## Troubleshooting

### Common Issues

#### Payment Failures Not Detected

1. **Check Webhook Configuration**: Verify Stripe webhook endpoints
2. **Database Connection**: Ensure database connectivity
3. **Event Processing**: Check webhook event processing logs
4. **Configuration**: Verify recovery system configuration

#### Recovery Actions Not Executing

1. **Scheduled Jobs**: Check scheduled job execution
2. **Action Queue**: Verify action queue processing
3. **Database Locks**: Check for database transaction locks
4. **Error Logs**: Review error logs for action failures

#### Notifications Not Sending

1. **Notification Service**: Verify notification service connectivity
2. **Channel Configuration**: Check notification channel settings
3. **Rate Limiting**: Verify rate limiting configuration
4. **Template Issues**: Check notification templates

#### Analytics Not Updating

1. **Data Collection**: Verify data collection processes
2. **Aggregation Jobs**: Check analytics aggregation jobs
3. **Database Queries**: Review analytics query performance
4. **Cache Issues**: Clear analytics cache if needed

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Performance Monitoring

```python
# Get performance metrics
metrics = recovery_system.get_performance_metrics()
print(f"Recovery Rate: {metrics['recovery_rate']:.2f}%")
print(f"Average Recovery Time: {metrics['average_recovery_time_days']:.2f} days")
```

#### Database Queries

```python
# Check recovery records
recovery_records = db.query(PaymentRecoveryRecord).filter(
    PaymentRecoveryRecord.status == 'pending'
).all()

# Check dunning events
dunning_events = db.query(DunningEvent).filter(
    DunningEvent.status == 'sent'
).all()
```

### Support

For additional support:

1. **Documentation**: Review this guide and related documentation
2. **Logs**: Check application logs for detailed error information
3. **Metrics**: Monitor performance metrics for system health
4. **Testing**: Run test scripts to verify functionality
5. **Configuration**: Verify all configuration settings

## Conclusion

The Payment Recovery System provides a comprehensive solution for maximizing subscription retention and revenue recovery. Through intelligent failure handling, automated recovery strategies, and sophisticated dunning management, the system helps businesses minimize revenue loss and maintain customer relationships.

The system is designed to be:

- **Automated**: Minimal manual intervention required
- **Intelligent**: Smart strategy selection based on failure type and customer value
- **Scalable**: Handles high volumes of payment failures
- **Configurable**: Flexible configuration for different business needs
- **Analytics-Driven**: Comprehensive reporting and analytics
- **Integration-Ready**: Easy integration with existing systems

For more information, refer to the individual component documentation and test scripts provided in the examples directory. 