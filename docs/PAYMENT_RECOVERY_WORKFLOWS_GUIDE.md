# Payment Recovery Workflows Guide

## Overview

The MINGUS application implements comprehensive payment recovery workflows to handle failed payments, manage customer communications, and maximize payment success rates. This system provides automated recovery strategies, intelligent dunning management, and graceful service degradation to maintain customer relationships while ensuring revenue collection.

## 🔧 Core Features

### **1. Dunning Management System**
- **Progressive Escalation**: 7-stage dunning process from initial failure to cancellation
- **Intelligent Timing**: Configurable retry intervals with exponential backoff
- **Stage-Specific Actions**: Different actions and communications for each dunning stage
- **Automatic Escalation**: Scheduled progression through dunning stages

### **2. Recovery Strategy Engine**
- **Failure Analysis**: Automatic determination of recovery strategy based on failure reason
- **Multiple Strategies**: Support for automatic retry, payment method updates, grace periods, and more
- **Configurable Rules**: Business rules for strategy selection and execution
- **Strategy Execution**: Automated execution of chosen recovery strategies

### **3. Payment Retry Logic**
- **Exponential Backoff**: Intelligent retry timing to maximize success rates
- **Attempt Limits**: Configurable maximum retry attempts per payment
- **Retry Scheduling**: Automated scheduling of retry attempts
- **Success Tracking**: Monitoring and tracking of retry success rates

### **4. Grace Period Management**
- **Service Degradation**: Gradual reduction of service features during grace periods
- **Customer Communication**: Clear communication about grace period status
- **Flexible Duration**: Configurable grace period lengths
- **Automatic Expiration**: Scheduled handling of grace period expiration

### **5. Payment Method Management**
- **Update Requests**: Automated requests for payment method updates
- **Validation**: Comprehensive validation of new payment methods
- **Retry Integration**: Automatic retry with updated payment methods
- **Follow-up Actions**: Scheduled follow-up for payment method updates

## 🏗️ Architecture

### **Service Components**

#### **1. PaymentRecoveryService**
Main service for handling payment recovery workflows.

```python
class PaymentRecoveryService:
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.dunning_config = {...}
        self.recovery_templates = {...}
```

#### **2. Dunning Management**
Comprehensive dunning stage management system.

```python
class DunningStage(Enum):
    INITIAL_FAILURE = 1
    FIRST_RETRY = 2
    SECOND_RETRY = 3
    FINAL_WARNING = 4
    GRACE_PERIOD = 5
    SUSPENSION = 6
    CANCELLATION = 7

@dataclass
class DunningEvent:
    customer_id: str
    subscription_id: str
    billing_record_id: str
    stage: DunningStage
    attempt_number: int
    amount: float
    currency: str
    failure_reason: str
    next_attempt_date: datetime
    grace_period_end: Optional[datetime] = None
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.AUTOMATIC_RETRY
    metadata: Dict[str, Any] = None
```

#### **3. Recovery Strategies**
Intelligent recovery strategy selection and execution.

```python
class RecoveryStrategy(Enum):
    AUTOMATIC_RETRY = "automatic_retry"
    PAYMENT_METHOD_UPDATE = "payment_method_update"
    GRACE_PERIOD = "grace_period"
    PARTIAL_PAYMENT = "partial_payment"
    PAYMENT_PLAN = "payment_plan"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class RecoveryAction:
    action_type: str
    description: str
    priority: str  # low, medium, high, urgent
    scheduled_at: datetime
    metadata: Dict[str, Any]
    notifications_sent: int = 0
```

## 🔧 Usage Examples

### **1. Payment Failure Handling**

```python
from backend.services.payment_recovery_service import PaymentRecoveryService

# Initialize payment recovery service
recovery_service = PaymentRecoveryService(db_session, config)

# Handle payment failure
failure_data = {
    "failure_reason": "insufficient_funds",
    "failure_code": "card_declined",
    "payment_method": "card",
    "webhook_event_id": "evt_1234567890"
}

result = recovery_service.handle_payment_failure(
    customer=customer,
    billing_record=billing_record,
    failure_data=failure_data
)

if result['success']:
    print(f"Recovery strategy: {result['recovery_strategy']}")
    print(f"Dunning stage: {result['dunning_event'].stage.value}")
    print(f"Next action: {result['next_action']}")
    print(f"Changes: {result['changes']}")
    print(f"Notifications sent: {result['notifications_sent']}")
```

### **2. Dunning Escalation**

```python
# Process dunning escalation
escalation_result = recovery_service.process_dunning_escalation(
    customer=customer,
    billing_record=billing_record,
    dunning_event=dunning_event
)

if escalation_result['success']:
    print(f"Escalated to stage: {escalation_result['new_stage']}")
    print(f"Next attempt date: {escalation_result['next_attempt_date']}")
    print(f"Changes: {escalation_result['changes']}")
    print(f"Notifications sent: {escalation_result['notifications_sent']}")
```

### **3. Payment Method Updates**

```python
# Handle payment method update during recovery
payment_method_data = {
    "type": "card",
    "card": {
        "brand": "visa",
        "last4": "4242",
        "exp_month": 12,
        "exp_year": 2025
    },
    "billing_details": {
        "name": "John Doe",
        "email": "john@example.com"
    }
}

update_result = recovery_service.handle_payment_method_update(
    customer=customer,
    billing_record=billing_record,
    payment_method_data=payment_method_data
)

if update_result['success']:
    print(f"Payment method updated: {update_result['payment_method_id']}")
    print(f"Retry success: {update_result['retry_success']}")
    print(f"Changes: {update_result['changes']}")
```

### **4. Grace Period Management**

```python
# Handle grace period management
grace_period_data = {
    "duration_days": 7,
    "restrictions": ["limited_features", "no_api_access"],
    "notifications": ["email", "sms"]
}

grace_result = recovery_service.handle_grace_period_management(
    customer=customer,
    billing_record=billing_record,
    grace_period_data=grace_period_data
)

if grace_result['success']:
    print(f"Grace period end: {grace_result['grace_period_end']}")
    print(f"Restrictions applied: {grace_result['restrictions_applied']}")
    print(f"Changes: {grace_result['changes']}")
```

### **5. Payment Success After Recovery**

```python
# Handle successful payment after recovery
payment_data = {
    "payment_method": "card",
    "receipt_url": "https://receipt.stripe.com/test",
    "payment_intent": "pi_1234567890"
}

success_result = recovery_service.handle_payment_success_after_failure(
    customer=customer,
    billing_record=billing_record,
    payment_data=payment_data
)

if success_result['success']:
    print(f"Events cleared: {success_result['cleared_events']}")
    print(f"Changes: {success_result['changes']}")
    print(f"Notifications sent: {success_result['notifications_sent']}")
```

## 📊 Dunning Configuration

### **Default Configuration**

```python
dunning_config = {
    'retry_intervals': [1, 3, 7, 14, 30],  # Days between retries
    'max_retry_attempts': 5,
    'grace_period_days': 7,
    'suspension_threshold': 4,
    'cancellation_threshold': 7,
    'recovery_strategies': {
        'automatic_retry': {
            'enabled': True,
            'max_attempts': 3,
            'backoff_multiplier': 2
        },
        'payment_method_update': {
            'enabled': True,
            'notification_delay_hours': 24
        },
        'grace_period': {
            'enabled': True,
            'duration_days': 7,
            'service_restriction': 'limited'
        },
        'partial_payment': {
            'enabled': True,
            'minimum_amount_percent': 50
        },
        'payment_plan': {
            'enabled': True,
            'max_installments': 3
        }
    }
}
```

### **Dunning Stage Progression**

#### **Stage 1: Initial Failure**
- **Timing**: Immediate
- **Actions**: Create dunning event, determine recovery strategy
- **Notifications**: Payment failure notification
- **Next Stage**: First Retry (1 day)

#### **Stage 2: First Retry**
- **Timing**: 1 day after initial failure
- **Actions**: Automatic retry, escalation notification
- **Notifications**: Retry scheduled notification
- **Next Stage**: Second Retry (3 days)

#### **Stage 3: Second Retry**
- **Timing**: 3 days after first retry
- **Actions**: Automatic retry, payment method update request
- **Notifications**: Payment method update request
- **Next Stage**: Final Warning (7 days)

#### **Stage 4: Final Warning**
- **Timing**: 7 days after second retry
- **Actions**: Final warning, grace period activation
- **Notifications**: Final warning notification
- **Next Stage**: Grace Period (7 days)

#### **Stage 5: Grace Period**
- **Timing**: 7 days after final warning
- **Actions**: Service restrictions, grace period notifications
- **Notifications**: Grace period notifications
- **Next Stage**: Suspension (14 days)

#### **Stage 6: Suspension**
- **Timing**: 14 days after grace period
- **Actions**: Service suspension, final recovery attempts
- **Notifications**: Suspension notifications
- **Next Stage**: Cancellation (30 days)

#### **Stage 7: Cancellation**
- **Timing**: 30 days after suspension
- **Actions**: Service cancellation, final communications
- **Notifications**: Cancellation notifications
- **Next Stage**: None (final stage)

## 📧 Recovery Templates

### **Retry Notification Template**
```python
'retry_notification': """
Payment Retry Scheduled

We'll automatically retry your payment of {amount} {currency} on {retry_date}.

If you'd like to update your payment method now, please visit:
{payment_portal_url}

Best regards,
The MINGUS Team
"""
```

### **Payment Method Update Template**
```python
'payment_method_update': """
Payment Method Update Required

Your payment of {amount} {currency} failed due to an issue with your payment method.

Please update your payment method to avoid service interruption:
{payment_portal_url}

Best regards,
The MINGUS Team
"""
```

### **Grace Period Template**
```python
'grace_period': """
Grace Period Active

Your payment of {amount} {currency} is overdue. We've activated a grace period until {grace_period_end}.

During this time, your service will have limited functionality. Please update your payment method:
{payment_portal_url}

Best regards,
The MINGUS Team
"""
```

### **Recovery Success Template**
```python
'recovery_success': """
Payment Recovery Successful

Great news! Your payment of {amount} {currency} has been processed successfully.

Your service has been fully restored. Thank you for your patience!

Best regards,
The MINGUS Team
"""
```

## 🔧 Integration with Business Logic

### **Enhanced Payment Failure Handling**

The payment recovery service is integrated into the business logic service:

```python
def handle_payment_failure_with_recovery(
    self,
    customer: Customer,
    billing_record: BillingHistory,
    failure_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle payment failure with comprehensive recovery workflow"""
    try:
        from .payment_recovery_service import PaymentRecoveryService
        
        # Initialize payment recovery service
        recovery_service = PaymentRecoveryService(self.db, self.config)
        
        # Execute payment recovery workflow
        recovery_result = recovery_service.handle_payment_failure(
            customer, billing_record, failure_data
        )
        
        # Add recovery-specific changes to business logic result
        if recovery_result['success']:
            return {
                'success': True,
                'changes': recovery_result['changes'],
                'notifications_sent': recovery_result['notifications_sent'],
                'recovery_strategy': recovery_result['recovery_strategy'],
                'dunning_stage': recovery_result['dunning_event'].stage.value,
                'next_action': recovery_result['next_action'],
                'message': f"Payment recovery workflow initiated: {recovery_result['recovery_strategy']}"
            }
        else:
            return {
                'success': False,
                'error': recovery_result['error'],
                'changes': recovery_result['changes'],
                'notifications_sent': recovery_result['notifications_sent']
            }
            
    except Exception as e:
        logger.error(f"Error handling payment failure with recovery: {e}")
        return {
            'success': False,
            'error': str(e),
            'changes': [],
            'notifications_sent': 0
        }
```

### **Recovery Scenario Detection**

The webhook manager automatically detects recovery scenarios:

```python
def _is_recovery_scenario(self, customer: Customer, billing_record: BillingHistory) -> bool:
    """Check if this is a recovery scenario (payment after previous failures)"""
    try:
        # Check if subscription was in a failed state
        if customer.subscription and customer.subscription.status in ['past_due', 'unpaid', 'canceled']:
            return True
        
        # Check if there are recent failed billing records
        recent_failed_records = self.db.query(BillingHistory).filter(
            BillingHistory.customer_id == customer.id,
            BillingHistory.subscription_id == billing_record.subscription_id,
            BillingHistory.status == 'failed',
            BillingHistory.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).count()
        
        return recent_failed_records > 0
        
    except Exception as e:
        logger.error(f"Error checking recovery scenario: {e}")
        return False
```

## 🛡️ Security and Compliance

### **1. Payment Method Security**
- **Tokenization**: Secure storage of payment method tokens
- **Validation**: Comprehensive validation of payment method data
- **Encryption**: End-to-end encryption of sensitive payment data
- **PCI Compliance**: Adherence to PCI DSS standards

### **2. Data Protection**
- **Audit Trail**: Complete logging of all recovery actions
- **Data Retention**: Appropriate retention policies for recovery data
- **Access Control**: Role-based access to recovery functions
- **Privacy Compliance**: GDPR and other privacy regulation compliance

### **3. Fraud Prevention**
- **Risk Assessment**: Automatic risk scoring for payment failures
- **Manual Review**: Escalation to manual review for suspicious activity
- **Fraud Detection**: Integration with fraud detection systems
- **Rate Limiting**: Protection against abuse of recovery systems

## 🔍 Monitoring and Analytics

### **1. Recovery Metrics**
- **Success Rates**: Track recovery success rates by strategy
- **Dunning Progression**: Monitor progression through dunning stages
- **Time to Recovery**: Measure time from failure to successful payment
- **Strategy Effectiveness**: Compare effectiveness of different recovery strategies

### **2. Performance Monitoring**
- **Processing Times**: Monitor recovery workflow execution times
- **Queue Monitoring**: Track recovery action queue performance
- **Error Rates**: Monitor error rates in recovery processes
- **System Health**: Overall recovery system health monitoring

### **3. Business Intelligence**
- **Revenue Impact**: Measure revenue impact of recovery efforts
- **Customer Retention**: Track customer retention during recovery
- **Churn Analysis**: Analyze churn patterns during recovery
- **Strategy Optimization**: Data-driven optimization of recovery strategies

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Payment Recovery Configuration
PAYMENT_RECOVERY_ENABLED=true
DUNNING_ENABLED=true
GRACE_PERIOD_ENABLED=true

# Dunning Configuration
DUNNING_RETRY_INTERVALS=1,3,7,14,30
DUNNING_MAX_ATTEMPTS=5
DUNNING_GRACE_PERIOD_DAYS=7
DUNNING_SUSPENSION_THRESHOLD=4
DUNNING_CANCELLATION_THRESHOLD=7

# Recovery Strategy Configuration
AUTOMATIC_RETRY_ENABLED=true
AUTOMATIC_RETRY_MAX_ATTEMPTS=3
AUTOMATIC_RETRY_BACKOFF_MULTIPLIER=2

PAYMENT_METHOD_UPDATE_ENABLED=true
PAYMENT_METHOD_UPDATE_DELAY_HOURS=24

GRACE_PERIOD_ENABLED=true
GRACE_PERIOD_DURATION_DAYS=7
GRACE_PERIOD_SERVICE_RESTRICTION=limited

PARTIAL_PAYMENT_ENABLED=true
PARTIAL_PAYMENT_MINIMUM_PERCENT=50

PAYMENT_PLAN_ENABLED=true
PAYMENT_PLAN_MAX_INSTALLMENTS=3
```

### **Service Configuration**
```python
# Initialize with custom settings
recovery_service = PaymentRecoveryService(
    db_session=db_session,
    config=config
)

# Custom dunning configuration
recovery_service.dunning_config = {
    'retry_intervals': [1, 2, 5, 10, 20],  # Custom intervals
    'max_retry_attempts': 3,  # Fewer attempts
    'grace_period_days': 5,  # Shorter grace period
    'recovery_strategies': {
        'automatic_retry': {
            'enabled': True,
            'max_attempts': 2,
            'backoff_multiplier': 1.5
        }
    }
}

# Custom recovery templates
recovery_service.recovery_templates['custom_retry'] = """
Custom retry message for {customer_name}!
Amount: {amount} {currency}
Retry date: {retry_date}
"""
```

## 🚀 Best Practices

### **1. Recovery Strategy Design**
- **Customer-Centric**: Design strategies with customer experience in mind
- **Gradual Escalation**: Use gradual escalation to avoid customer frustration
- **Multiple Channels**: Use multiple communication channels
- **Personalization**: Personalize recovery communications

### **2. Timing Optimization**
- **Optimal Timing**: Schedule retries at optimal times for success
- **Customer Behavior**: Consider customer behavior patterns
- **Time Zones**: Account for customer time zones
- **Business Hours**: Schedule actions during business hours when possible

### **3. Communication Strategy**
- **Clear Messaging**: Use clear, actionable messaging
- **Urgency Levels**: Vary urgency based on dunning stage
- **Multiple Formats**: Use email, SMS, and in-app notifications
- **Consistent Branding**: Maintain consistent brand voice

### **4. Performance Optimization**
- **Batch Processing**: Process recovery actions in batches
- **Async Processing**: Use async processing for non-critical actions
- **Caching**: Cache frequently accessed configuration
- **Database Optimization**: Optimize database queries for recovery data

### **5. Monitoring and Alerting**
- **Real-time Monitoring**: Monitor recovery processes in real-time
- **Alert Thresholds**: Set appropriate alert thresholds
- **Escalation Procedures**: Define escalation procedures for issues
- **Performance Baselines**: Establish performance baselines

## 📋 Troubleshooting

### **Common Issues**

#### **1. Recovery Actions Not Scheduled**
**Symptoms**: Recovery actions not being scheduled or executed
**Causes**: 
- Recovery service not properly initialized
- Configuration errors
- Database connection issues

**Solutions**:
```python
# Check recovery service initialization
recovery_service = PaymentRecoveryService(db_session, config)
print(f"Service initialized: {recovery_service is not None}")

# Check configuration
print(f"Dunning config: {recovery_service.dunning_config}")
print(f"Recovery templates: {len(recovery_service.recovery_templates)}")

# Check database connection
try:
    db_session.execute("SELECT 1")
    print("Database connection: OK")
except Exception as e:
    print(f"Database connection error: {e}")
```

#### **2. Dunning Events Not Created**
**Symptoms**: Dunning events not being created for payment failures
**Causes**:
- Payment failure not properly detected
- Dunning event creation errors
- Database transaction issues

**Solutions**:
```python
# Check payment failure detection
failure_result = recovery_service.handle_payment_failure(
    customer, billing_record, failure_data
)
print(f"Failure handling result: {failure_result}")

# Check dunning event creation
if 'dunning_event' in failure_result:
    dunning_event = failure_result['dunning_event']
    print(f"Dunning event created: {dunning_event.stage.value}")
    print(f"Next attempt: {dunning_event.next_attempt_date}")
else:
    print("No dunning event created")
```

#### **3. Recovery Strategies Not Executing**
**Symptoms**: Recovery strategies not being executed
**Causes**:
- Strategy determination errors
- Strategy execution failures
- Configuration issues

**Solutions**:
```python
# Check strategy determination
strategy = recovery_service._determine_recovery_strategy(
    customer, billing_record, failure_data
)
print(f"Determined strategy: {strategy.value}")

# Check strategy execution
strategy_result = recovery_service._execute_recovery_strategy(
    customer, billing_record, dunning_event, strategy
)
print(f"Strategy execution result: {strategy_result}")

# Check configuration
strategy_config = recovery_service.dunning_config['recovery_strategies']
print(f"Strategy configuration: {strategy_config}")
```

#### **4. Notifications Not Sent**
**Symptoms**: Recovery notifications not being sent
**Causes**:
- Notification service issues
- Template errors
- Customer data issues

**Solutions**:
```python
# Check notification templates
templates = recovery_service.recovery_templates
print(f"Available templates: {list(templates.keys())}")

# Check template formatting
try:
    template = templates['retry_notification']
    message = template.format(
        amount=29.00,
        currency="usd",
        retry_date="2025-01-15",
        payment_portal_url="https://example.com/billing"
    )
    print(f"Template formatted successfully: {len(message)} characters")
except Exception as e:
    print(f"Template formatting error: {e}")

# Check notification service
try:
    notification_result = recovery_service._send_retry_notification(
        customer, billing_record, dunning_event
    )
    print(f"Notification sent: {notification_result}")
except Exception as e:
    print(f"Notification error: {e}")
```

## 📈 Conclusion

The payment recovery workflows provide comprehensive handling of failed payments with intelligent recovery strategies, automated dunning management, and customer-friendly communications. By following the best practices and monitoring guidelines, you can maximize payment success rates while maintaining excellent customer relationships.

The system is designed to be:
- **Comprehensive**: Handles all aspects of payment recovery
- **Intelligent**: Uses data-driven strategy selection
- **Customer-Friendly**: Maintains positive customer experience
- **Automated**: Reduces manual intervention
- **Configurable**: Adaptable to business needs
- **Monitored**: Complete visibility into recovery processes
- **Compliant**: Adheres to security and privacy standards 