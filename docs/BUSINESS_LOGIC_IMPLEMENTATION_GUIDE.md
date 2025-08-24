# Business Logic Implementation Guide

## Overview

The MINGUS application implements comprehensive business logic for webhook events, focusing on feature access control updates and user notifications for billing events. This system ensures that webhook events trigger appropriate business actions, maintain data consistency, and provide excellent user experience through timely communications.

## 🔧 Core Features

### **1. Feature Access Control Management**
- **Dynamic Feature Updates**: Automatic feature access updates based on subscription changes
- **Tier-Based Access**: Different feature sets for different pricing tiers
- **Access Level Management**: Granular control over user permissions and capabilities
- **Downgrade Handling**: Proper feature removal when subscriptions are cancelled or downgraded

### **2. User Notification System**
- **Multi-Channel Notifications**: Email, SMS, in-app, and push notifications
- **Event-Driven Messaging**: Automatic notifications triggered by webhook events
- **Template-Based Communication**: Consistent messaging with customizable templates
- **Priority-Based Delivery**: Different notification priorities based on event importance

### **3. Subscription Lifecycle Management**
- **Creation Workflows**: Complete setup for new subscriptions
- **Update Handling**: Managing subscription changes and upgrades
- **Cancellation Processing**: Graceful handling of subscription cancellations
- **Trial Management**: Trial period setup and conversion workflows

### **4. Payment Event Processing**
- **Success Handling**: Processing successful payments and reactivating services
- **Failure Management**: Handling failed payments with retry logic
- **Dunning Management**: Automated collection processes for overdue payments
- **Payment Method Updates**: Managing payment method changes

## 🏗️ Architecture

### **Service Components**

#### **1. BusinessLogicService**
Main service for handling business logic in webhook events.

```python
class BusinessLogicService:
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.feature_configs = {...}
        self.notification_templates = {...}
```

#### **2. Feature Access Control**
Comprehensive feature access management system.

```python
class FeatureAccessLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"

@dataclass
class FeatureAccessUpdate:
    customer_id: str
    subscription_id: str
    old_tier: Optional[str]
    new_tier: str
    features_added: List[str]
    features_removed: List[str]
    access_level: FeatureAccessLevel
    effective_date: datetime
    reason: str
```

#### **3. User Notifications**
Structured notification system for user communications.

```python
class NotificationType(Enum):
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    TRIAL_ENDING = "trial_ending"
    FEATURE_ACCESS_UPDATED = "feature_access_updated"

@dataclass
class UserNotification:
    user_id: str
    customer_id: str
    notification_type: NotificationType
    subject: str
    message: str
    priority: str  # low, medium, high, urgent
    channels: List[str]  # email, sms, push, in_app
    metadata: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
```

## 🔧 Usage Examples

### **1. Subscription Creation Business Logic**

```python
from backend.services.business_logic_service import BusinessLogicService

# Initialize business logic service
business_logic_service = BusinessLogicService(db_session, config)

# Handle subscription creation
result = business_logic_service.handle_subscription_created(
    customer=customer,
    subscription=subscription,
    subscription_data=subscription_data
)

# Check results
if result['success']:
    print(f"Business logic executed successfully")
    print(f"Changes: {result['changes']}")
    print(f"Notifications sent: {result['notifications_sent']}")
else:
    print(f"Error: {result['error']}")
```

### **2. Feature Access Control**

```python
# Update feature access for new subscription
feature_update = business_logic_service._update_feature_access_for_subscription(
    customer=customer,
    subscription=subscription,
    subscription_data=subscription_data
)

print(f"Feature access updated: {feature_update.reason}")
print(f"Features added: {feature_update.features_added}")
print(f"Features removed: {feature_update.features_removed}")
print(f"Access level: {feature_update.access_level.value}")

# Downgrade feature access for cancellation
downgrade_update = business_logic_service._downgrade_feature_access_for_cancellation(
    customer=customer,
    subscription=subscription,
    cancellation_data=cancellation_data
)

print(f"Downgrade reason: {downgrade_update.reason}")
print(f"New access level: {downgrade_update.access_level.value}")
```

### **3. User Notifications**

```python
# Send welcome notifications
welcome_notifications = business_logic_service._send_subscription_welcome_notifications(
    customer=customer,
    subscription=subscription,
    subscription_data=subscription_data
)

print(f"Welcome notifications sent: {len(welcome_notifications)}")

# Send payment success notifications
payment_notifications = business_logic_service._send_payment_success_notifications(
    customer=customer,
    billing_record=billing_record,
    payment_data=payment_data
)

print(f"Payment notifications sent: {len(payment_notifications)}")

# Send payment failure notifications
failure_notifications = business_logic_service._send_payment_failure_notifications(
    customer=customer,
    billing_record=billing_record,
    payment_data=payment_data
)

print(f"Failure notifications sent: {len(failure_notifications)}")
```

### **4. Payment Event Handling**

```python
# Handle successful payments
payment_result = business_logic_service.handle_payment_succeeded(
    customer=customer,
    billing_record=billing_record,
    payment_data=payment_data
)

if payment_result['success']:
    print(f"Payment processed successfully")
    print(f"Changes: {payment_result['changes']}")
    print(f"Notifications sent: {payment_result['notifications_sent']}")

# Handle failed payments
failure_result = business_logic_service.handle_payment_failed(
    customer=customer,
    billing_record=billing_record,
    payment_data=payment_data
)

if failure_result['success']:
    print(f"Payment failure handled")
    print(f"Changes: {failure_result['changes']}")
    print(f"Notifications sent: {failure_result['notifications_sent']}")
```

### **5. Subscription Lifecycle Management**

```python
# Handle subscription updates
update_result = business_logic_service.handle_subscription_updated(
    customer=customer,
    subscription=subscription,
    old_values=old_values,
    new_data=new_data
)

if update_result['success']:
    print(f"Subscription updated successfully")
    print(f"Changes: {update_result['changes']}")

# Handle subscription cancellations
cancellation_result = business_logic_service.handle_subscription_cancelled(
    customer=customer,
    subscription=subscription,
    cancellation_data=cancellation_data
)

if cancellation_result['success']:
    print(f"Subscription cancelled successfully")
    print(f"Changes: {cancellation_result['changes']}")

# Handle trial ending
trial_result = business_logic_service.handle_trial_ending(
    customer=customer,
    subscription=subscription,
    trial_data=trial_data
)

if trial_result['success']:
    print(f"Trial ending handled successfully")
    print(f"Changes: {trial_result['changes']}")
```

## 📊 Feature Configuration

### **Feature Tiers and Capabilities**

#### **Basic Tier**
```python
'basic': {
    'features': [
        'basic_analytics',
        'standard_reports',
        'email_support'
    ],
    'limits': {
        'api_calls_per_month': 1000,
        'storage_gb': 5,
        'users': 1
    }
}
```

#### **Premium Tier**
```python
'premium': {
    'features': [
        'advanced_analytics',
        'custom_reports',
        'priority_support',
        'api_access'
    ],
    'limits': {
        'api_calls_per_month': 10000,
        'storage_gb': 50,
        'users': 5
    }
}
```

#### **Enterprise Tier**
```python
'enterprise': {
    'features': [
        'enterprise_analytics',
        'white_label_reports',
        'dedicated_support',
        'api_access',
        'custom_integrations'
    ],
    'limits': {
        'api_calls_per_month': 100000,
        'storage_gb': 500,
        'users': 25
    }
}
```

#### **Unlimited Tier**
```python
'unlimited': {
    'features': [
        'unlimited_analytics',
        'unlimited_reports',
        'dedicated_support',
        'api_access',
        'custom_integrations',
        'premium_features'
    ],
    'limits': {
        'api_calls_per_month': -1,  # Unlimited
        'storage_gb': -1,  # Unlimited
        'users': -1  # Unlimited
    }
}
```

## 📧 Notification Templates

### **Welcome Message Template**
```python
'welcome': """
Welcome to MINGUS! Your subscription is now active.

Subscription Details:
- Plan: {pricing_tier}
- Billing Cycle: {billing_cycle}
- Next Billing Date: {next_billing_date}

Your features are now available. Get started by exploring your dashboard!

Best regards,
The MINGUS Team
"""
```

### **Payment Success Template**
```python
'payment_success': """
Payment Successful!

Your payment of {amount} {currency} has been processed successfully.

Payment Details:
- Date: {payment_date}
- Invoice: {invoice_id}
- Next Billing: {next_billing_date}

Thank you for your continued support!

Best regards,
The MINGUS Team
"""
```

### **Payment Failure Template**
```python
'payment_failure': """
Payment Failed - Action Required

We were unable to process your payment of {amount} {currency}.

Reason: {failure_reason}

Please update your payment method to avoid service interruption.

Update Payment Method: {payment_portal_url}

Best regards,
The MINGUS Team
"""
```

### **Cancellation Template**
```python
'cancellation': """
Subscription Cancelled

Your MINGUS subscription has been cancelled as requested.

Cancellation Details:
- Effective Date: {effective_date}
- Reason: {reason}

Your account will remain active until {effective_date}. After that, you'll have access to basic features only.

To reactivate your subscription, visit your account settings.

Best regards,
The MINGUS Team
"""
```

### **Trial Ending Template**
```python
'trial_ending': """
Your Trial is Ending Soon

Your MINGUS trial will end on {trial_end_date} ({days_remaining} days remaining).

To continue enjoying all features, please add a payment method:

{payment_setup_url}

Don't lose access to your data and features!

Best regards,
The MINGUS Team
"""
```

## 🔧 Integration with Webhook Handlers

### **Enhanced Webhook Processing Pipeline**

The business logic service is integrated into the webhook processing pipeline:

```python
# Step 14: Execute business logic for subscription creation
business_logic_result = self._execute_business_logic_for_subscription_created(
    customer, subscription, subscription_data
)

# Add business logic changes and notifications
if business_logic_result['success']:
    changes.extend(business_logic_result['changes'])
    notifications_sent += business_logic_result['notifications_sent']
```

### **Business Logic Methods**

#### **Subscription Events**
```python
def _execute_business_logic_for_subscription_created(self, customer, subscription, subscription_data):
    """Execute business logic for subscription creation"""
    
def _execute_business_logic_for_subscription_updated(self, customer, subscription, old_values, new_data):
    """Execute business logic for subscription updates"""
    
def _execute_business_logic_for_subscription_cancelled(self, customer, subscription, cancellation_data):
    """Execute business logic for subscription cancellation"""
```

#### **Payment Events**
```python
def _execute_business_logic_for_payment_succeeded(self, customer, billing_record, payment_data):
    """Execute business logic for successful payments"""
    
def _execute_business_logic_for_payment_failed(self, customer, billing_record, payment_data):
    """Execute business logic for failed payments"""
```

#### **Trial Events**
```python
def _execute_business_logic_for_trial_ending(self, customer, subscription, trial_data):
    """Execute business logic for trial ending"""
```

## 🛡️ Security and Compliance

### **1. Access Control Security**
- **Feature Validation**: Ensures users only access features they're entitled to
- **Permission Checks**: Validates access rights before feature activation
- **Audit Trail**: Complete logging of feature access changes

### **2. Notification Security**
- **Template Validation**: Ensures notification content is safe and appropriate
- **Channel Security**: Secure delivery through encrypted channels
- **Rate Limiting**: Prevents notification spam

### **3. Data Protection**
- **PII Handling**: Proper handling of personally identifiable information
- **GDPR Compliance**: Respects user privacy preferences
- **Data Retention**: Appropriate data retention policies

## 🔍 Monitoring and Analytics

### **1. Business Metrics Tracking**
- **Feature Usage**: Track which features are most used
- **Subscription Conversions**: Monitor trial to paid conversions
- **Payment Success Rates**: Track payment processing success
- **Customer Satisfaction**: Monitor notification effectiveness

### **2. Performance Monitoring**
- **Processing Times**: Monitor business logic execution times
- **Notification Delivery**: Track notification delivery success rates
- **Error Rates**: Monitor business logic error rates

### **3. Health Checks**
- **Service Availability**: Monitor business logic service health
- **Database Performance**: Monitor feature access database performance
- **Notification Queue**: Monitor notification processing queue

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Business Logic Configuration
BUSINESS_LOGIC_ENABLED=true
FEATURE_ACCESS_ENABLED=true
NOTIFICATION_ENABLED=true

# Feature Configuration
BASIC_TIER_FEATURES=basic_analytics,standard_reports,email_support
PREMIUM_TIER_FEATURES=advanced_analytics,custom_reports,priority_support,api_access
ENTERPRISE_TIER_FEATURES=enterprise_analytics,white_label_reports,dedicated_support,api_access,custom_integrations

# Notification Configuration
NOTIFICATION_CHANNELS=email,sms,in_app
NOTIFICATION_PRIORITY_DEFAULT=medium
NOTIFICATION_RATE_LIMIT=100
```

### **Service Configuration**
```python
# Initialize with custom settings
business_logic_service = BusinessLogicService(
    db_session=db_session,
    config=config
)

# Custom feature configurations
business_logic_service.feature_configs = {
    'custom_tier': {
        'features': ['custom_feature_1', 'custom_feature_2'],
        'limits': {
            'api_calls_per_month': 5000,
            'storage_gb': 25,
            'users': 3
        }
    }
}

# Custom notification templates
business_logic_service.notification_templates['custom_welcome'] = """
Custom welcome message for {customer_name}!
"""
```

## 🚀 Best Practices

### **1. Feature Access Management**
- **Granular Permissions**: Use fine-grained feature permissions
- **Progressive Enhancement**: Add features gradually as users upgrade
- **Graceful Degradation**: Remove features gracefully on downgrade
- **Access Auditing**: Regularly audit feature access permissions

### **2. Notification Strategy**
- **Relevant Content**: Ensure notifications are relevant and timely
- **Multi-Channel Delivery**: Use multiple channels for important notifications
- **User Preferences**: Respect user notification preferences
- **A/B Testing**: Test different notification approaches

### **3. Business Logic Design**
- **Idempotent Operations**: Ensure business logic is idempotent
- **Error Handling**: Implement comprehensive error handling
- **Rollback Capability**: Provide rollback mechanisms for failed operations
- **Monitoring**: Monitor business logic execution and outcomes

### **4. Performance Optimization**
- **Caching**: Cache feature configurations and templates
- **Batch Processing**: Process notifications in batches when possible
- **Async Processing**: Use async processing for non-critical operations
- **Database Optimization**: Optimize database queries for feature access

## 📋 Troubleshooting

### **Common Issues**

#### **1. Feature Access Not Updated**
**Symptoms**: Users don't have access to features they should have
**Causes**: 
- Business logic service not called
- Database transaction failed
- Feature configuration error

**Solutions**:
```python
# Check business logic execution
result = business_logic_service.handle_subscription_created(customer, subscription, data)
if not result['success']:
    print(f"Business logic failed: {result['error']}")

# Check feature access record
feature_access = db_session.query(FeatureAccess).filter(
    FeatureAccess.customer_id == customer.id
).first()
print(f"Current features: {feature_access.features if feature_access else 'None'}")
```

#### **2. Notifications Not Sent**
**Symptoms**: Users don't receive expected notifications
**Causes**:
- Notification service not configured
- Template errors
- Channel delivery failures

**Solutions**:
```python
# Check notification service
notifications = business_logic_service._send_subscription_welcome_notifications(
    customer, subscription, data
)
print(f"Notifications sent: {len(notifications)}")

# Check notification templates
template = business_logic_service.notification_templates.get('welcome')
if not template:
    print("Welcome template not found")
```

#### **3. Business Logic Errors**
**Symptoms**: Webhook processing fails with business logic errors
**Causes**:
- Database connection issues
- Invalid data
- Configuration errors

**Solutions**:
```python
# Enable debug logging
import logging
logging.getLogger('backend.services.business_logic_service').setLevel(logging.DEBUG)

# Check business logic execution
try:
    result = business_logic_service.handle_subscription_created(customer, subscription, data)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

## 📈 Conclusion

The business logic implementation provides comprehensive feature access control and user notification capabilities for webhook events. By following the best practices and monitoring guidelines, you can ensure reliable business logic execution and excellent user experience in your MINGUS application.

The system is designed to be:
- **Comprehensive**: Handles all major webhook events with appropriate business logic
- **Flexible**: Configurable feature tiers and notification templates
- **Reliable**: Robust error handling and rollback capabilities
- **Scalable**: Efficient processing for high-volume webhook events
- **Secure**: Proper access control and data protection
- **Observable**: Comprehensive monitoring and analytics 