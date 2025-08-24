# SMS Notifications and In-App Notifications Guide

## Overview

The SMS Notifications and In-App Notifications system provides multi-channel communication for critical payment failures, ensuring customers are immediately aware of payment issues through their preferred communication channels. This system integrates seamlessly with the dunning management workflow to maximize payment recovery rates.

## Feature Overview

### Purpose
- **Multi-Channel Communication**: Reach customers through SMS, in-app notifications, and billing alerts
- **Critical Payment Failure Alerts**: Immediate notification for urgent payment issues
- **Progressive Escalation**: Increase urgency and frequency for persistent failures
- **Interactive SMS Responses**: Handle customer responses and provide support
- **Real-Time Billing Alerts**: Instant notifications for payment status changes
- **Comprehensive Tracking**: Monitor delivery and engagement across all channels

### Key Benefits
- **Immediate Awareness**: Critical payment failures are communicated instantly
- **Multiple Touchpoints**: Reach customers through their preferred channels
- **Interactive Support**: SMS responses provide immediate customer assistance
- **Visual Alerts**: In-app notifications with clear call-to-action buttons
- **Audible Notifications**: Billing alerts with sound and vibration for urgent issues
- **Comprehensive Analytics**: Track effectiveness of each notification channel

## SMS Notifications

### Configuration

SMS notifications are configured for critical payment failure stages:

```python
'sms_notifications': {
    'enabled': True,
    'critical_stages': ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice'],
    'sms_templates': {
        'dunning_3_urgent': {
            'message': 'URGENT: Your MINGUS payment of ${amount} failed. Update payment method within 7 days to avoid suspension. Reply HELP for support.',
            'priority': 'high',
            'retry_count': 3
        },
        'dunning_4_critical': {
            'message': 'CRITICAL: Your MINGUS account will be suspended in 7 days due to payment failure. Call {support_phone} immediately to resolve.',
            'priority': 'urgent',
            'retry_count': 5
        },
        'dunning_5_suspension': {
            'message': 'FINAL WARNING: MINGUS account suspension scheduled. Contact support immediately at {support_phone} to prevent loss of access.',
            'priority': 'urgent',
            'retry_count': 5
        },
        'final_suspension': {
            'message': 'ALERT: Your MINGUS account has been suspended. Call {support_phone} to reactivate your account and restore access.',
            'priority': 'urgent',
            'retry_count': 3
        }
    },
    'support_phone': '+1-800-MINGUS-1',
    'opt_out_keywords': ['STOP', 'CANCEL', 'UNSUBSCRIBE'],
    'help_keywords': ['HELP', 'SUPPORT', 'INFO']
}
```

### SMS Templates

#### Dunning 3 - Urgent Reminder
- **Stage**: Day 7 after payment failure
- **Message**: "URGENT: Your MINGUS payment of ${amount} failed. Update payment method within 7 days to avoid suspension. Reply HELP for support."
- **Priority**: High
- **Retry Count**: 3

#### Dunning 4 - Critical Warning
- **Stage**: Day 14 after payment failure
- **Message**: "CRITICAL: Your MINGUS account will be suspended in 7 days due to payment failure. Call {support_phone} immediately to resolve."
- **Priority**: Urgent
- **Retry Count**: 5

#### Dunning 5 - Suspension Warning
- **Stage**: Day 21 after payment failure
- **Message**: "FINAL WARNING: MINGUS account suspension scheduled. Contact support immediately at {support_phone} to prevent loss of access."
- **Priority**: Urgent
- **Retry Count**: 5

#### Final Notice - Account Suspended
- **Stage**: Day 28 after payment failure
- **Message**: "ALERT: Your MINGUS account has been suspended. Call {support_phone} to reactivate your account and restore access."
- **Priority**: Urgent
- **Retry Count**: 3

### Usage Examples

#### Send SMS Notification

```python
# Send SMS notification for critical stage
def send_critical_sms_notification(failure_id, stage_name):
    recovery_system = PaymentRecoverySystem(db, config)
    
    result = recovery_system.send_sms_notification(failure_id, stage_name)
    
    if result['success']:
        print(f"SMS sent to {result['phone_number']}")
        print(f"Message: {result['message']}")
        print(f"Priority: {result['priority']}")
    else:
        print(f"SMS failed: {result['error']}")
```

#### Generate SMS Content

```python
# Generate SMS content for stage
def generate_sms_content(failure_record, customer, stage_name):
    recovery_system = PaymentRecoverySystem(db, config)
    
    content = recovery_system._generate_sms_content(failure_record, customer, stage_name)
    
    return {
        'message': content['message'],
        'priority': content['priority'],
        'retry_count': content['retry_count']
    }
```

#### Handle SMS Response

```python
# Handle customer SMS response
def handle_sms_response(phone_number, message):
    recovery_system = PaymentRecoverySystem(db, config)
    
    result = recovery_system.handle_sms_response(phone_number, message)
    
    if result['success']:
        print(f"Action: {result['action']}")
        print(f"Message: {result['message']}")
    else:
        print(f"Error: {result['error']}")
```

### SMS Response Handling

The system handles various customer SMS responses:

#### Opt-out Requests
- **Keywords**: STOP, CANCEL, UNSUBSCRIBE
- **Action**: Unsubscribe customer from SMS notifications
- **Response**: Confirmation message with resubscribe instructions

#### Help Requests
- **Keywords**: HELP, SUPPORT, INFO
- **Action**: Send support information and contact details
- **Response**: Support phone number and website information

#### Payment Update Requests
- **Keywords**: UPDATE, PAYMENT, CARD
- **Action**: Send payment method update instructions
- **Response**: Instructions for updating payment method

#### Default Response
- **Action**: Send general assistance information
- **Response**: Support contact and payment update instructions

## In-App Notifications

### Configuration

In-app notifications provide persistent, actionable notifications within the application:

```python
'in_app_notifications': {
    'enabled': True,
    'notification_types': {
        'payment_failure': {
            'title': 'Payment Issue Detected',
            'message': 'We couldn\'t process your recent payment of ${amount}. Please update your payment method to continue using MINGUS.',
            'severity': 'warning',
            'action_required': True,
            'action_text': 'Update Payment Method',
            'action_url': '/billing/payment-method',
            'dismissible': False,
            'persistent': True
        },
        'grace_period_active': {
            'title': 'Grace Period Active',
            'message': 'Your account is in a 7-day grace period. Update your payment method to avoid service interruption.',
            'severity': 'warning',
            'action_required': True,
            'action_text': 'Resolve Payment Issue',
            'action_url': '/billing/resolve-payment',
            'dismissible': False,
            'persistent': True
        },
        'suspension_warning': {
            'title': 'Account Suspension Warning',
            'message': 'Your account will be suspended in {days_remaining} days due to payment issues. Take action now to prevent service interruption.',
            'severity': 'critical',
            'action_required': True,
            'action_text': 'Contact Support',
            'action_url': '/support/contact',
            'dismissible': False,
            'persistent': True
        },
        'account_suspended': {
            'title': 'Account Suspended',
            'message': 'Your account has been suspended due to payment issues. Contact support to reactivate your account.',
            'severity': 'critical',
            'action_required': True,
            'action_text': 'Reactivate Account',
            'action_url': '/support/reactivate',
            'dismissible': False,
            'persistent': True
        }
    }
}
```

### Notification Types

#### Payment Failure
- **Title**: "Payment Issue Detected"
- **Severity**: Warning
- **Action**: Update Payment Method
- **URL**: /billing/payment-method
- **Dismissible**: False
- **Persistent**: True

#### Grace Period Active
- **Title**: "Grace Period Active"
- **Severity**: Warning
- **Action**: Resolve Payment Issue
- **URL**: /billing/resolve-payment
- **Dismissible**: False
- **Persistent**: True

#### Suspension Warning
- **Title**: "Account Suspension Warning"
- **Severity**: Critical
- **Action**: Contact Support
- **URL**: /support/contact
- **Dismissible**: False
- **Persistent**: True

#### Account Suspended
- **Title**: "Account Suspended"
- **Severity**: Critical
- **Action**: Reactivate Account
- **URL**: /support/reactivate
- **Dismissible**: False
- **Persistent**: True

### Usage Examples

#### Send In-App Notification

```python
# Send in-app notification
def send_in_app_notification(failure_id, notification_type):
    recovery_system = PaymentRecoverySystem(db, config)
    
    result = recovery_system.send_in_app_notification(failure_id, notification_type)
    
    if result['success']:
        print(f"Notification sent: {result['title']}")
        print(f"Severity: {result['severity']}")
        print(f"Action Required: {result['action_required']}")
    else:
        print(f"Notification failed: {result['error']}")
```

#### Generate In-App Content

```python
# Generate in-app notification content
def generate_in_app_content(failure_record, customer, notification_type):
    recovery_system = PaymentRecoverySystem(db, config)
    
    content = recovery_system._generate_in_app_notification_content(
        failure_record, customer, notification_type
    )
    
    return {
        'title': content['title'],
        'message': content['message'],
        'severity': content['severity'],
        'action_text': content['action_text'],
        'action_url': content['action_url']
    }
```

## Billing Alerts

### Configuration

Billing alerts provide immediate, attention-grabbing notifications with sound and vibration:

```python
'billing_alerts': {
    'enabled': True,
    'alert_types': {
        'payment_failed': {
            'title': 'Payment Failed',
            'message': 'Your payment of ${amount} {currency} failed. Please update your payment method.',
            'icon': 'payment_error',
            'color': 'red',
            'sound': 'alert',
            'vibration': True
        },
        'grace_period_started': {
            'title': 'Grace Period Started',
            'message': 'Your account is now in a grace period. Update payment method to continue.',
            'icon': 'warning',
            'color': 'orange',
            'sound': 'notification',
            'vibration': False
        },
        'suspension_imminent': {
            'title': 'Suspension Imminent',
            'message': 'Your account will be suspended in {days_remaining} days.',
            'icon': 'critical',
            'color': 'red',
            'sound': 'alert',
            'vibration': True
        },
        'account_suspended': {
            'title': 'Account Suspended',
            'message': 'Your account has been suspended due to payment issues.',
            'icon': 'blocked',
            'color': 'red',
            'sound': 'alert',
            'vibration': True
        }
    },
    'notification_frequency': {
        'payment_failed': 'immediate',
        'grace_period_started': 'daily',
        'suspension_imminent': 'daily',
        'account_suspended': 'once'
    }
}
```

### Alert Types

#### Payment Failed
- **Title**: "Payment Failed"
- **Icon**: payment_error
- **Color**: red
- **Sound**: alert
- **Vibration**: true
- **Frequency**: immediate

#### Grace Period Started
- **Title**: "Grace Period Started"
- **Icon**: warning
- **Color**: orange
- **Sound**: notification
- **Vibration**: false
- **Frequency**: daily

#### Suspension Imminent
- **Title**: "Suspension Imminent"
- **Icon**: critical
- **Color**: red
- **Sound**: alert
- **Vibration**: true
- **Frequency**: daily

#### Account Suspended
- **Title**: "Account Suspended"
- **Icon**: blocked
- **Color**: red
- **Sound**: alert
- **Vibration**: true
- **Frequency**: once

### Usage Examples

#### Send Billing Alert

```python
# Send billing alert
def send_billing_alert(failure_id, alert_type):
    recovery_system = PaymentRecoverySystem(db, config)
    
    result = recovery_system.send_billing_alert(failure_id, alert_type)
    
    if result['success']:
        print(f"Alert sent: {result['title']}")
        print(f"Icon: {result['icon']}")
        print(f"Color: {result['color']}")
        print(f"Sound: {result['sound']}")
        print(f"Vibration: {result['vibration']}")
    else:
        print(f"Alert failed: {result['error']}")
```

#### Generate Billing Alert Content

```python
# Generate billing alert content
def generate_billing_alert_content(failure_record, customer, alert_type):
    recovery_system = PaymentRecoverySystem(db, config)
    
    content = recovery_system._generate_billing_alert_content(
        failure_record, customer, alert_type
    )
    
    return {
        'title': content['title'],
        'message': content['message'],
        'icon': content['icon'],
        'color': content['color'],
        'sound': content['sound'],
        'vibration': content['vibration']
    }
```

## Multi-Channel Notifications

### Configuration

The system automatically sends notifications across multiple channels based on the dunning stage:

```python
def send_multi_channel_notifications(failure_id, stage_name):
    recovery_system = PaymentRecoverySystem(db, config)
    
    result = recovery_system.send_multi_channel_notifications(failure_id, stage_name)
    
    if result['success']:
        print(f"Total channels: {result['total_channels']}")
        print(f"Channels sent: {result['channels_sent']}")
        
        # Show individual results
        for channel, channel_result in result['results'].items():
            if channel_result:
                print(f"{channel}: {channel_result.get('success', False)}")
    else:
        print(f"Multi-channel failed: {result['error']}")
```

### Channel Mapping

#### Dunning 1-2 (Early Stages)
- **Email**: Always sent
- **SMS**: Not sent (not critical)
- **In-App**: Payment failure notification
- **Billing Alert**: Payment failed alert

#### Dunning 3-4 (Critical Stages)
- **Email**: Always sent
- **SMS**: Sent with urgent priority
- **In-App**: Grace period or suspension warning
- **Billing Alert**: Grace period or suspension imminent

#### Dunning 5-Final (Suspension Stages)
- **Email**: Always sent
- **SMS**: Sent with urgent priority
- **In-App**: Suspension warning or account suspended
- **Billing Alert**: Suspension imminent or account suspended

## Phone Number Management

### Phone Number Retrieval

The system retrieves customer phone numbers from multiple sources:

```python
def get_customer_phone_number(customer):
    recovery_system = PaymentRecoverySystem(db, config)
    
    phone_number = recovery_system._get_customer_phone_number(customer)
    
    if phone_number:
        print(f"Phone number found: {phone_number}")
    else:
        print("No phone number available")
    
    return phone_number
```

### Phone Number Normalization

Phone numbers are normalized to ensure consistent formatting:

```python
def normalize_phone_number(phone_number):
    recovery_system = PaymentRecoverySystem(db, config)
    
    normalized = recovery_system._normalize_phone_number(phone_number)
    
    print(f"Original: {phone_number}")
    print(f"Normalized: {normalized}")
    
    return normalized
```

### Normalization Examples

- `555-123-4567` → `+15551234567`
- `(555) 123-4567` → `+15551234567`
- `555.123.4567` → `+15551234567`
- `5551234567` → `+15551234567`
- `1-555-123-4567` → `+15551234567`
- `+1-555-123-4567` → `+15551234567`

## Stage to Notification Mapping

### In-App Notification Mapping

```python
def get_in_app_notification_type_for_stage(stage_name):
    recovery_system = PaymentRecoverySystem(db, config)
    
    notification_type = recovery_system._get_in_app_notification_type_for_stage(stage_name)
    
    print(f"Stage: {stage_name} -> Notification Type: {notification_type}")
    
    return notification_type
```

### Billing Alert Mapping

```python
def get_billing_alert_type_for_stage(stage_name):
    recovery_system = PaymentRecoverySystem(db, config)
    
    alert_type = recovery_system._get_billing_alert_type_for_stage(stage_name)
    
    print(f"Stage: {stage_name} -> Alert Type: {alert_type}")
    
    return alert_type
```

### Mapping Table

| Dunning Stage | In-App Notification | Billing Alert |
|---------------|-------------------|---------------|
| dunning_1 | payment_failure | payment_failed |
| dunning_2 | payment_failure | payment_failed |
| dunning_3 | grace_period_active | grace_period_started |
| dunning_4 | suspension_warning | suspension_imminent |
| dunning_5 | suspension_warning | suspension_imminent |
| final_notice | account_suspended | account_suspended |

## Analytics and Monitoring

### Key Metrics

Track the effectiveness of multi-channel notifications:

- **Delivery Rates**: Success rate for each channel
- **Engagement Rates**: Click-through and response rates
- **Response Times**: Time to customer action after notification
- **Channel Preferences**: Most effective channels by customer segment
- **Opt-out Rates**: SMS opt-out frequency and reasons
- **Support Interactions**: Customer support requests triggered by notifications

### Performance Tracking

```python
def track_notification_performance(failure_id):
    # Track notification delivery and engagement
    metrics = {
        'sms_delivered': 0,
        'sms_responded': 0,
        'in_app_delivered': 0,
        'in_app_clicked': 0,
        'billing_alerts_delivered': 0,
        'billing_alerts_acknowledged': 0
    }
    
    return metrics
```

## Best Practices

### SMS Notifications

1. **Clear and Concise**: Keep messages under 160 characters
2. **Action-Oriented**: Include clear call-to-action
3. **Support Information**: Provide support contact details
4. **Opt-out Compliance**: Include opt-out instructions
5. **Timing**: Send during business hours when possible
6. **Frequency**: Limit to critical stages only

### In-App Notifications

1. **Persistent Display**: Keep critical notifications visible
2. **Clear Actions**: Provide direct action buttons
3. **Progressive Escalation**: Increase urgency through stages
4. **Visual Hierarchy**: Use appropriate colors and icons
5. **Non-Dismissible**: Prevent dismissal of critical notifications
6. **Contextual Information**: Include relevant payment details

### Billing Alerts

1. **Immediate Delivery**: Send alerts instantly for critical issues
2. **Attention-Grabbing**: Use sound and vibration for urgency
3. **Clear Messaging**: Simple, actionable messages
4. **Frequency Control**: Limit to prevent notification fatigue
5. **Visual Distinction**: Use appropriate colors and icons
6. **Escalation**: Increase urgency for later stages

## Troubleshooting

### Common Issues

1. **SMS Not Delivered**: Check phone number format and carrier
2. **In-App Notifications Not Showing**: Verify notification permissions
3. **Billing Alerts Not Triggering**: Check device notification settings
4. **Phone Number Not Found**: Verify customer data completeness
5. **Opt-out Not Working**: Check keyword matching and processing

### Debug Information

```python
def debug_notification_issues(failure_id):
    recovery_system = PaymentRecoverySystem(db, config)
    
    debug_info = {
        'failure_record': recovery_system._get_payment_failure_record(failure_id),
        'customer': recovery_system._get_customer(failure_record.customer_id),
        'phone_number': recovery_system._get_customer_phone_number(customer),
        'sms_enabled': recovery_system.recovery_config['dunning_email_sequence']['sms_notifications']['enabled'],
        'in_app_enabled': recovery_system.recovery_config['dunning_email_sequence']['in_app_notifications']['enabled']
    }
    
    return debug_info
```

## Configuration Recommendations

### High-Value Customers

```python
# Enhanced configuration for high-value customers
high_value_config = {
    'sms_notifications': {
        'critical_stages': ['dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice'],  # Earlier SMS
        'retry_count': 5  # More retry attempts
    },
    'in_app_notifications': {
        'notification_types': {
            'payment_failure': {
                'persistent': True,  # Always persistent
                'dismissible': False
            }
        }
    }
}
```

### Standard Customers

```python
# Standard configuration for regular customers
standard_config = {
    'sms_notifications': {
        'critical_stages': ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice'],  # Standard timing
        'retry_count': 3  # Standard retry attempts
    },
    'in_app_notifications': {
        'notification_types': {
            'payment_failure': {
                'persistent': True,
                'dismissible': False
            }
        }
    }
}
```

## Conclusion

The SMS Notifications and In-App Notifications system provides comprehensive multi-channel communication for payment failures:

- **Immediate Awareness**: Critical payment failures are communicated instantly across multiple channels
- **Interactive Support**: SMS responses provide immediate customer assistance
- **Visual Engagement**: In-app notifications with clear call-to-action buttons
- **Audible Alerts**: Billing alerts with sound and vibration for urgent issues
- **Progressive Escalation**: Increase urgency and frequency through dunning stages
- **Comprehensive Analytics**: Track effectiveness of each notification channel
- **Flexible Configuration**: Customizable for different customer segments

This feature significantly improves payment recovery rates by ensuring customers are immediately aware of payment issues through their preferred communication channels, with clear paths to resolution. 