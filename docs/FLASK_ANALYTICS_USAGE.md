# Flask Analytics Service Usage Guide

This guide shows how to use the Flask analytics service functions to track communication metrics and user engagement in your MINGUS application.

## Quick Start

### Import the Functions

```python
from backend.services.flask_analytics_service import (
    track_message_sent,
    track_message_delivered,
    track_message_opened,
    track_user_action,
    track_financial_outcome,
    get_user_communication_history,
    get_communication_stats
)
```

## Core Functions

### 1. track_message_sent(user_id, channel, message_type, cost)

Track when a message is sent to a user.

```python
# Example: Track SMS alert sent
message_metrics = track_message_sent(
    user_id=123,
    channel="sms",
    message_type="low_balance",
    cost=0.05  # $0.05 per SMS
)

# Example: Track email report sent
email_metrics = track_message_sent(
    user_id=123,
    channel="email",
    message_type="weekly_checkin",
    cost=0.001  # $0.001 per email
)

# Get the message ID for future tracking
message_id = message_metrics.id
```

### 2. track_message_delivered(message_id, delivery_time)

Track when a message is successfully delivered.

```python
# Track delivery (uses current time if not specified)
track_message_delivered(message_id=456)

# Track delivery with specific time
from datetime import datetime
delivery_time = datetime.utcnow()
track_message_delivered(message_id=456, delivery_time=delivery_time)
```

### 3. track_message_opened(message_id, open_time)

Track when a user opens a message (typically for emails).

```python
# Track email opened
track_message_opened(message_id=456)

# Track with specific time
open_time = datetime.utcnow()
track_message_opened(message_id=456, open_time=open_time)
```

### 4. track_user_action(message_id, action_type, timestamp)

Track user actions taken in response to a message.

```python
# Track user viewed forecast
track_user_action(
    message_id=456,
    action_type="viewed_forecast"
)

# Track user updated budget
track_user_action(
    message_id=456,
    action_type="updated_budget"
)

# Track with specific timestamp
action_time = datetime.utcnow()
track_user_action(
    message_id=456,
    action_type="clicked_link",
    timestamp=action_time
)
```

### 5. track_financial_outcome(user_id, action, impact_amount)

Track financial outcomes resulting from user actions.

```python
# Track bill paid on time (avoided late fee)
track_financial_outcome(
    user_id=123,
    action="bill_paid_on_time",
    impact_amount=25.00  # Avoided $25 late fee
)

# Track savings goal achieved
track_financial_outcome(
    user_id=123,
    action="savings_goal_achieved",
    impact_amount=500.00  # Saved $500
)

# Track subscription upgrade
track_financial_outcome(
    user_id=123,
    action="subscription_upgraded",
    impact_amount=10.00  # Additional $10/month revenue
)
```

## Query Functions

### 6. get_user_communication_history(user_id, limit)

Get communication history for a specific user.

```python
# Get last 50 communications for user
history = get_user_communication_history(user_id=123, limit=50)

for message in history:
    print(f"Message: {message.message_type}")
    print(f"Channel: {message.channel}")
    print(f"Status: {message.status}")
    print(f"Sent: {message.sent_at}")
    print(f"Action: {message.action_taken}")
    print("---")
```

### 7. get_communication_stats(user_id, **filters)

Get aggregated communication statistics.

```python
# Get overall stats
stats = get_communication_stats()

print(f"Total messages: {stats['total_messages']}")
print(f"Delivery rate: {stats['delivery_rate']:.1f}%")
print(f"Open rate: {stats['open_rate']:.1f}%")
print(f"Total cost: ${stats['total_cost']:.2f}")

# Get stats for specific user
user_stats = get_communication_stats(user_id=123)

# Get stats with filters
filtered_stats = get_communication_stats(
    user_id=123,
    message_type="low_balance",
    channel="sms",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)
```

## Integration Examples

### In Celery Tasks

```python
from backend.services.flask_analytics_service import track_message_sent, track_message_delivered

@celery.task
def send_sms_alert(user_id, message_content):
    # Send SMS via Twilio
    twilio_response = send_sms(user_id, message_content)
    
    # Track message sent
    message_metrics = track_message_sent(
        user_id=user_id,
        channel="sms",
        message_type="low_balance",
        cost=0.05
    )
    
    # If delivery confirmed, track delivery
    if twilio_response.status == "delivered":
        track_message_delivered(message_metrics.id)
    
    return message_metrics.id
```

### In Flask Routes

```python
from flask import Blueprint, request, jsonify
from backend.services.flask_analytics_service import track_user_action, track_financial_outcome

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/user-action', methods=['POST'])
def record_user_action():
    data = request.json
    
    # Track user action
    track_user_action(
        message_id=data['message_id'],
        action_type=data['action_type']
    )
    
    # If action has financial impact, track it
    if data.get('financial_impact'):
        track_financial_outcome(
            user_id=data['user_id'],
            action=data['action_type'],
            impact_amount=data['financial_impact']
        )
    
    return jsonify({"success": True})
```

### In Email Webhooks

```python
from backend.services.flask_analytics_service import track_message_opened

@app.route('/webhook/email-opened', methods=['POST'])
def email_opened_webhook():
    data = request.json
    
    # Track email opened
    track_message_opened(
        message_id=data['message_id'],
        open_time=datetime.utcnow()
    )
    
    return jsonify({"success": True})
```

## Error Handling

All functions return `None` if they fail, so you can handle errors gracefully:

```python
# Track message sent with error handling
message_metrics = track_message_sent(user_id=123, channel="sms", message_type="alert")

if message_metrics is None:
    logger.error("Failed to track message sent")
    # Handle error appropriately
else:
    logger.info(f"Message tracked with ID: {message_metrics.id}")
```

## Performance Considerations

- All functions use the existing database session from Flask context
- Functions are designed to be non-blocking and fast
- Database operations are wrapped in try-catch blocks
- Logging is included for debugging and monitoring

## Database Schema

The analytics functions work with these main tables:

- `communication_metrics` - Individual message tracking
- `financial_impact_metrics` - Financial outcomes
- `user_engagement_metrics` - User engagement patterns
- `channel_effectiveness` - Channel performance comparison
- `cost_tracking` - Cost analysis and budget monitoring

## Best Practices

1. **Always track message sent first** - This creates the base record
2. **Track delivery when confirmed** - Update status when delivery is confirmed
3. **Track opens for emails** - Use webhooks or tracking pixels
4. **Track user actions promptly** - Record actions as soon as they happen
5. **Use consistent action types** - Standardize action type strings
6. **Monitor costs** - Track actual costs for accurate ROI calculation
7. **Handle errors gracefully** - Check return values and log errors 