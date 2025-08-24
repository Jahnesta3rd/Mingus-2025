# Webhook Handlers Guide

This guide covers the webhook handlers for external services (Twilio SMS and Resend Email) that provide real-time status updates for communication tracking.

## Overview

The webhook handlers system provides secure endpoints for receiving status updates from external communication services:

- **Twilio Webhook**: Handles SMS delivery status updates
- **Resend Webhook**: Handles email delivery, open, click, and bounce events
- **Health Check**: Monitors webhook system health

## Endpoints

### 1. Twilio SMS Webhook
```
POST /webhooks/twilio
```

**Purpose**: Receives SMS delivery status updates from Twilio

**Headers Required**:
- `X-Twilio-Signature`: HMAC signature for verification
- `Content-Type`: `application/x-www-form-urlencoded`

**Form Data**:
- `MessageSid` or `SmsSid`: Twilio message identifier
- `MessageStatus` or `SmsStatus`: Delivery status
- `To`: Recipient phone number
- `From`: Sender phone number
- `ErrorCode`: Error code (if failed)
- `ErrorMessage`: Error message (if failed)

**Status Types**:
- `delivered`: SMS successfully delivered
- `failed`: SMS delivery failed
- `undelivered`: SMS not delivered
- `sent`: SMS sent to carrier

**Response**: `200 OK` with `{"success": true}`

### 2. Resend Email Webhook
```
POST /webhooks/resend
```

**Purpose**: Receives email event updates from Resend

**Headers Required**:
- `Resend-Signature`: HMAC signature for verification
- `Content-Type`: `application/json`

**JSON Payload**:
```json
{
  "type": "email.delivered",
  "data": {
    "id": "email_id",
    "from": "sender@example.com",
    "to": ["recipient@example.com"],
    "subject": "Email Subject",
    "created_at": "2025-01-27T12:00:00Z"
  },
  "created_at": "2025-01-27T12:00:00Z"
}
```

**Event Types**:
- `email.delivered`: Email successfully delivered
- `email.opened`: Email was opened by recipient
- `email.clicked`: Email link was clicked
- `email.complained`: Email marked as spam
- `email.bounced`: Email bounced

**Response**: `200 OK` with `{"success": true}`

### 3. Health Check
```
GET /webhooks/health
```

**Purpose**: Monitor webhook system health

**Response**:
```json
{
  "status": "healthy",
  "service": "webhook_handlers",
  "endpoints": {
    "twilio": "/webhooks/twilio",
    "resend": "/webhooks/resend"
  },
  "timestamp": "2025-01-27T12:00:00Z"
}
```

## Security Features

### 1. Signature Verification

**Twilio Signature Verification**:
```python
def verify_twilio_signature(request_body: str, signature: str, auth_token: str) -> bool:
    expected_signature = hmac.new(
        auth_token.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

**Resend Signature Verification**:
```python
def verify_resend_signature(request_body: str, signature: str, webhook_secret: str) -> bool:
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

### 2. Request Validation

All webhook requests are validated using Marshmallow schemas:

```python
class TwilioWebhookSchema(Schema):
    MessageSid = fields.Str(required=True)
    MessageStatus = fields.Str(required=True)
    To = fields.Str(required=True)
    From = fields.Str(required=True)
    ErrorCode = fields.Str(required=False)
    ErrorMessage = fields.Str(required=False)
```

### 3. Error Handling

Comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request`: Invalid webhook data
- `401 Unauthorized`: Invalid signature
- `404 Not Found`: Message ID not found
- `500 Internal Server Error`: Server processing error

## Configuration

### Environment Variables

```bash
# Twilio Configuration
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_PHONE_NUMBER=+1234567890

# Resend Configuration
RESEND_API_KEY=your_resend_api_key
RESEND_WEBHOOK_SECRET=your_webhook_secret
RESEND_FROM_EMAIL=noreply@mingus.com

# Webhook URLs
WEBHOOK_BASE_URL=https://api.mingus.com
TWILIO_WEBHOOK_URL=/webhooks/twilio
RESEND_WEBHOOK_URL=/webhooks/resend

# Security
VERIFY_WEBHOOK_SIGNATURES=true
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3

# Message ID Mapping
MESSAGE_ID_MAPPING_STRATEGY=database
TIMESTAMP_MATCHING_WINDOW=3600
```

### Configuration Validation

```python
from config.webhook_config import WebhookConfig

# Validate configuration
validation = WebhookConfig.validate_config()
if not validation['valid']:
    print("Configuration errors:", validation['errors'])
if validation['warnings']:
    print("Configuration warnings:", validation['warnings'])

# Get webhook URLs
urls = WebhookConfig.get_webhook_urls()
print("Twilio webhook URL:", urls['twilio'])
print("Resend webhook URL:", urls['resend'])
```

## Message ID Mapping

The webhook handlers need to map external service IDs (Twilio SID, Resend email ID) to our internal message IDs. Three strategies are supported:

### 1. Database Strategy (Recommended)

Store external IDs in a mapping table:

```sql
CREATE TABLE message_external_ids (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES communication_metrics(id),
    external_id VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- 'twilio' or 'resend'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Embedded Strategy

Embed our message ID in external service metadata:

```python
# When sending SMS via Twilio
twilio_client.messages.create(
    body="Your message",
    from_=phone_number,
    to=recipient,
    metadata={'message_id': str(our_message_id)}
)

# When sending email via Resend
resend_client.emails.send({
    'from': sender,
    'to': recipient,
    'subject': subject,
    'html': content,
    'headers': {'X-Message-ID': str(our_message_id)}
})
```

### 3. Timestamp Strategy

Match messages by timestamp within a window:

```python
def get_message_id_from_timestamp(service_type: str, external_timestamp: datetime) -> Optional[int]:
    window_start = external_timestamp - timedelta(seconds=3600)
    window_end = external_timestamp + timedelta(seconds=3600)
    
    message = db.query(CommunicationMetrics).filter(
        CommunicationMetrics.channel == service_type,
        CommunicationMetrics.sent_at.between(window_start, window_end)
    ).first()
    
    return message.id if message else None
```

## Integration Examples

### Setting Up Twilio Webhooks

1. **Configure Twilio Webhook URL**:
   ```
   https://api.mingus.com/webhooks/twilio
   ```

2. **Set Webhook Events**:
   - Message Status Callback: `delivered`, `failed`, `undelivered`

3. **Test Webhook**:
   ```bash
   curl -X POST https://api.mingus.com/webhooks/twilio \
     -H "X-Twilio-Signature: your_signature" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "MessageSid=SM123&MessageStatus=delivered&To=+1234567890&From=+0987654321"
   ```

### Setting Up Resend Webhooks

1. **Configure Resend Webhook URL**:
   ```
   https://api.mingus.com/webhooks/resend
   ```

2. **Set Webhook Events**:
   - `email.delivered`
   - `email.opened`
   - `email.clicked`
   - `email.complained`
   - `email.bounced`

3. **Test Webhook**:
   ```bash
   curl -X POST https://api.mingus.com/webhooks/resend \
     -H "Resend-Signature: your_signature" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "email.delivered",
       "data": {
         "id": "email_123",
         "from": "noreply@mingus.com",
         "to": ["user@example.com"],
         "subject": "Test Email",
         "created_at": "2025-01-27T12:00:00Z"
       },
       "created_at": "2025-01-27T12:00:00Z"
     }'
   ```

## Monitoring and Logging

### Log Levels

- `INFO`: Normal webhook processing
- `WARNING`: Invalid signatures, missing messages
- `ERROR`: Processing failures, database errors

### Metrics to Monitor

1. **Webhook Volume**:
   - Requests per minute/hour
   - Success vs failure rates

2. **Processing Time**:
   - Average response time
   - Timeout occurrences

3. **Error Rates**:
   - Invalid signatures
   - Missing message IDs
   - Database errors

4. **Business Metrics**:
   - SMS delivery rates
   - Email open rates
   - User engagement tracking

### Health Monitoring

```python
# Check webhook health
response = requests.get('https://api.mingus.com/webhooks/health')
if response.status_code == 200:
    health_data = response.json()
    if health_data['status'] == 'healthy':
        print("Webhook system is healthy")
    else:
        print("Webhook system issues detected")
```

## Best Practices

### 1. Security
- Always verify webhook signatures
- Use HTTPS for all webhook URLs
- Rotate webhook secrets regularly
- Monitor for suspicious activity

### 2. Reliability
- Implement idempotent webhook processing
- Handle duplicate webhook events
- Use database transactions for updates
- Implement retry logic for failures

### 3. Performance
- Process webhooks asynchronously when possible
- Use connection pooling for database operations
- Implement rate limiting to prevent abuse
- Monitor webhook processing times

### 4. Monitoring
- Log all webhook events
- Set up alerts for webhook failures
- Track webhook processing metrics
- Monitor external service status

### 5. Testing
- Test webhook endpoints with sample data
- Verify signature validation works correctly
- Test error handling scenarios
- Monitor webhook processing in staging environment

## Troubleshooting

### Common Issues

1. **Invalid Signature Errors**:
   - Check webhook secret configuration
   - Verify signature calculation
   - Ensure request body is not modified

2. **Message ID Not Found**:
   - Check message ID mapping strategy
   - Verify message exists in database
   - Check timestamp matching window

3. **Database Errors**:
   - Check database connection
   - Verify table structure
   - Check for constraint violations

4. **Timeout Errors**:
   - Optimize database queries
   - Implement async processing
   - Increase webhook timeout settings

### Debug Mode

Enable debug logging for webhook troubleshooting:

```bash
export WEBHOOK_LOG_LEVEL=DEBUG
export VERIFY_WEBHOOK_SIGNATURES=false  # Only in development
```

### Webhook Testing Tools

1. **ngrok** for local testing:
   ```bash
   ngrok http 5000
   ```

2. **Webhook.site** for testing:
   - Use temporary webhook URLs
   - Inspect webhook payloads
   - Test signature verification

3. **Postman** for manual testing:
   - Create webhook request collections
   - Test different payload scenarios
   - Verify response handling 