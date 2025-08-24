# Communication API Documentation

## Overview

The Communication API provides a comprehensive interface for managing all communication-related functionality in the MINGUS application. This includes sending smart communications, managing user preferences, handling webhooks, and accessing analytics.

**Base URL**: `/api/communication`

**Authentication**: All endpoints require JWT authentication unless specified otherwise.

## Table of Contents

1. [Communication Orchestrator Endpoints](#communication-orchestrator-endpoints)
2. [User Preference Management](#user-preference-management)
3. [Webhook Handlers](#webhook-handlers)
4. [Analytics API](#analytics-api)
5. [Reporting API](#reporting-api)
6. [Health Checks](#health-checks)
7. [Error Handling](#error-handling)

---

## Communication Orchestrator Endpoints

### Send Communication

**POST** `/api/communication/send`

Send a smart communication based on trigger type and user preferences.

#### Request Body

```json
{
  "user_id": 123,
  "trigger_type": "financial_alert",
  "data": {
    "amount": 100.50,
    "account": "checking",
    "threshold": 200.00
  },
  "channel": "sms",
  "priority": "critical",
  "scheduled_time": "2025-01-27T10:00:00Z"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | Target user ID |
| `trigger_type` | string | Yes | Type of communication trigger |
| `data` | object | Yes | Context data for the communication |
| `channel` | string | No | Preferred channel (sms/email/both) |
| `priority` | string | No | Priority level (critical/high/medium/low) |
| `scheduled_time` | string | No | ISO 8601 timestamp for scheduling |

#### Response

**Success (200)**
```json
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "cost": 0.05,
  "fallback_used": false,
  "analytics_tracked": true,
  "message": "Communication scheduled successfully"
}
```

**Error (400)**
```json
{
  "success": false,
  "error": "Invalid trigger type: unknown_trigger",
  "fallback_used": false
}
```

### Get Communication Status

**GET** `/api/communication/status/{task_id}`

Get the status of a communication task.

#### Response

**Success (200)**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "message_id": "msg_123456",
    "delivered": true,
    "delivery_time": "2025-01-27T10:00:05Z"
  },
  "created": "2025-01-27T10:00:00Z",
  "started": "2025-01-27T10:00:01Z",
  "succeeded": "2025-01-27T10:00:05Z"
}
```

### Cancel Communication

**POST** `/api/communication/cancel/{task_id}`

Cancel a scheduled communication task.

#### Response

**Success (200)**
```json
{
  "success": true,
  "message": "Communication cancelled successfully"
}
```

### Send Batch Communications

**POST** `/api/communication/batch`

Send multiple communications in a single request.

#### Request Body

```json
{
  "communications": [
    {
      "user_id": 123,
      "trigger_type": "financial_alert",
      "data": {"amount": 100.50},
      "channel": "sms"
    },
    {
      "user_id": 124,
      "trigger_type": "weekly_checkin",
      "data": {"week": 3},
      "channel": "email"
    }
  ]
}
```

#### Response

**Success (200)**
```json
{
  "success": true,
  "results": [
    {
      "user_id": 123,
      "success": true,
      "task_id": "abc123-def456",
      "cost": 0.05,
      "fallback_used": false
    },
    {
      "user_id": 124,
      "success": true,
      "task_id": "ghi789-jkl012",
      "cost": 0.001,
      "fallback_used": false
    }
  ],
  "summary": {
    "total": 2,
    "successful": 2,
    "failed": 0,
    "total_cost": 0.051
  }
}
```

### Get Trigger Types

**GET** `/api/communication/trigger-types`

Get available communication trigger types.

#### Response

**Success (200)**
```json
{
  "trigger_types": [
    {
      "value": "financial_alert",
      "name": "Financial Alert",
      "description": "Critical financial notifications",
      "default_channel": "sms",
      "default_priority": "critical"
    },
    {
      "value": "payment_reminder",
      "name": "Payment Reminder",
      "description": "Payment due notifications",
      "default_channel": "sms",
      "default_priority": "high"
    }
  ]
}
```

---

## User Preference Management

### Get/Update User Preferences

**GET/PUT** `/api/communication/preferences/{user_id}`

Get or update user communication preferences.

#### GET Response

**Success (200)**
```json
{
  "success": true,
  "preferences": {
    "user_id": 123,
    "sms_enabled": true,
    "email_enabled": true,
    "preferred_sms_time": "09:00:00",
    "preferred_email_day": 1,
    "alert_types_sms": {
      "financial_alert": true,
      "payment_reminder": true,
      "weekly_checkin": false
    },
    "alert_types_email": {
      "monthly_report": true,
      "career_insight": true,
      "educational_content": false
    },
    "frequency_preference": "weekly",
    "user_segment": "premium_subscriber"
  }
}
```

#### PUT Request Body

```json
{
  "sms_enabled": true,
  "preferred_sms_time": "10:00:00",
  "alert_types_sms": {
    "financial_alert": true,
    "payment_reminder": false
  },
  "frequency_preference": "daily"
}
```

### Reset User Preferences

**POST** `/api/communication/preferences/{user_id}/reset`

Reset user preferences to smart defaults.

#### Response

**Success (200)**
```json
{
  "success": true,
  "message": "Preferences reset to defaults successfully",
  "preferences": {
    "user_id": 123,
    "sms_enabled": true,
    "email_enabled": true,
    "frequency_preference": "weekly"
  }
}
```

### Grant SMS Consent

**POST** `/api/communication/consent/sms`

Grant SMS consent for a user.

#### Request Body

```json
{
  "user_id": 123,
  "phone_number": "+1234567890",
  "consent_source": "web_form"
}
```

#### Response

**Success (200)**
```json
{
  "success": true,
  "message": "SMS consent granted successfully",
  "verification_required": true
}
```

### Verify SMS Consent

**POST** `/api/communication/consent/sms/verify`

Verify SMS consent with verification code.

#### Request Body

```json
{
  "phone_number": "+1234567890",
  "verification_code": "123456"
}
```

#### Response

**Success (200)**
```json
{
  "success": true,
  "message": "Phone number verified successfully"
}
```

### Grant Email Consent

**POST** `/api/communication/consent/email`

Grant email consent for a user.

#### Request Body

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "message_types": ["monthly_report", "career_insight"],
  "consent_source": "api"
}
```

### Revoke Consent

**POST** `/api/communication/consent/revoke`

Revoke consent for a specific channel and message type.

#### Request Body

```json
{
  "user_id": 123,
  "channel": "sms",
  "message_types": ["financial_alert"],
  "reason": "user_request"
}
```

### Opt Out

**POST** `/api/communication/opt-out`

Opt out of communications.

#### Request Body

```json
{
  "user_id": 123,
  "channel": "sms",
  "message_type": "all",
  "reason": "too_frequent"
}
```

### Check Consent

**POST** `/api/communication/consent/check`

Check if user has consent for specific communication.

#### Request Body

```json
{
  "user_id": 123,
  "message_type": "financial_alert",
  "channel": "sms"
}
```

#### Response

**Success (200)**
```json
{
  "success": true,
  "can_send": true,
  "reason": "explicit_consent",
  "consent_status": "granted"
}
```

### Get Optimal Send Time

**GET** `/api/communication/optimal-send-time`

Get optimal send time for user.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |
| `channel` | string | No | Channel (sms/email) |

#### Response

**Success (200)**
```json
{
  "success": true,
  "optimal_time": "2025-01-27T09:00:00+00:00",
  "channel": "sms"
}
```

---

## Webhook Handlers

### Twilio Webhook

**POST** `/api/communication/webhooks/twilio`

Handle Twilio SMS status webhooks.

#### Request Body (Twilio Format)

```json
{
  "MessageSid": "SM1234567890abcdef",
  "MessageStatus": "delivered",
  "ErrorCode": null,
  "ErrorMessage": null
}
```

#### Response

**Success (200)**
```json
{
  "success": true
}
```

### Resend Webhook

**POST** `/api/communication/webhooks/resend`

Handle Resend email status webhooks.

#### Request Body (Resend Format)

```json
{
  "type": "email.delivered",
  "id": "msg_1234567890abcdef"
}
```

### SMS Opt-Out Webhook

**POST** `/api/communication/webhooks/sms-opt-out`

Handle SMS opt-out replies.

#### Request Body

```json
{
  "From": "+1234567890",
  "Body": "STOP"
}
```

---

## Analytics API

### Get Communication Summary

**GET** `/api/communication/analytics/summary`

Get overall communication performance summary.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

#### Response

**Success (200)**
```json
{
  "success": true,
  "summary": {
    "total_sent": 1500,
    "total_delivered": 1425,
    "total_opened": 855,
    "total_clicked": 285,
    "total_actions": 342,
    "delivery_rate": 0.95,
    "open_rate": 0.60,
    "click_rate": 0.20,
    "action_rate": 0.24,
    "sms_sent": 800,
    "email_sent": 700,
    "sms_delivery_rate": 0.98,
    "email_delivery_rate": 0.91
  }
}
```

### Get User Engagement

**GET** `/api/communication/analytics/user/{user_id}`

Get user-specific engagement analytics.

#### Response

**Success (200)**
```json
{
  "success": true,
  "user_id": 123,
  "engagement_metrics": {
    "total_communications": 25,
    "delivery_rate": 0.96,
    "open_rate": 0.72,
    "click_rate": 0.28,
    "action_rate": 0.32,
    "recent_communications": [
      {
        "id": 456,
        "message_type": "financial_alert",
        "channel": "sms",
        "status": "delivered",
        "sent_at": "2025-01-27T09:00:00Z",
        "delivered_at": "2025-01-27T09:00:05Z",
        "opened_at": null,
        "action_taken": "viewed_forecast"
      }
    ]
  }
}
```

### Get Channel Effectiveness

**GET** `/api/communication/analytics/channel-effectiveness`

Get SMS vs Email performance comparison.

#### Response

**Success (200)**
```json
{
  "success": true,
  "sms": {
    "channel": "sms",
    "total_sent": 800,
    "delivery_rate": 0.98,
    "cost_per_message": 0.05,
    "total_cost": 40.0,
    "engagement_rate": 0.35
  },
  "email": {
    "channel": "email",
    "total_sent": 700,
    "delivery_rate": 0.91,
    "open_rate": 0.60,
    "click_rate": 0.20,
    "cost_per_message": 0.001,
    "total_cost": 0.7,
    "engagement_rate": 0.28
  },
  "recommendations": [
    "SMS has higher delivery rate - consider for critical communications",
    "Email has higher engagement - consider for educational content"
  ]
}
```

### Get Cost Tracking

**GET** `/api/communication/analytics/cost-tracking`

Get detailed cost tracking and budget analysis.

#### Response

**Success (200)**
```json
{
  "success": true,
  "cost_analysis": {
    "total_cost": 40.7,
    "sms_cost": 40.0,
    "email_cost": 0.7,
    "daily_budget": 100.0,
    "monthly_budget": 3000.0,
    "daily_budget_usage": 40.7,
    "monthly_budget_usage": 1.36,
    "cost_per_message": 0.027,
    "roi_analysis": {
      "total_communications": 1500,
      "total_engagements": 342,
      "engagement_rate": 0.228,
      "cost_per_engagement": 0.119
    }
  },
  "alerts": []
}
```

---

## Reporting API

### Get Dashboard Report

**GET** `/api/communication/reports/dashboard`

Get comprehensive dashboard report.

#### Response

**Success (200)**
```json
{
  "success": true,
  "dashboard": {
    "overview": {
      "total_communications": 1500,
      "delivery_rate": 0.95,
      "engagement_rate": 0.228,
      "total_cost": 40.7
    },
    "trends": {
      "daily_sent": [45, 52, 48, 61, 55],
      "daily_delivered": [43, 50, 46, 58, 53],
      "daily_engaged": [12, 15, 11, 18, 14]
    },
    "channel_performance": {
      "sms": {"sent": 800, "delivered": 784, "engaged": 280},
      "email": {"sent": 700, "delivered": 637, "engaged": 178}
    }
  }
}
```

### Get Performance Report

**GET** `/api/communication/reports/performance`

Get performance metrics report.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |
| `channel` | string | No | Channel filter (sms/email) |

#### Response

**Success (200)**
```json
{
  "success": true,
  "performance": {
    "delivery_rates": {
      "overall": 0.95,
      "sms": 0.98,
      "email": 0.91
    },
    "engagement_rates": {
      "overall": 0.228,
      "sms": 0.357,
      "email": 0.279
    },
    "cost_metrics": {
      "total_cost": 40.7,
      "cost_per_message": 0.027,
      "cost_per_engagement": 0.119
    }
  }
}
```

### Get Trends Report

**GET** `/api/communication/reports/trends`

Get trend analysis report.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `metric` | string | No | Metric to analyze (delivery_rate/engagement_rate/cost) |
| `period` | string | No | Period (daily/weekly/monthly) |
| `days` | integer | No | Number of days to analyze |

#### Response

**Success (200)**
```json
{
  "success": true,
  "trends": {
    "metric": "delivery_rate",
    "period": "daily",
    "data": [
      {"date": "2025-01-23", "value": 0.96},
      {"date": "2025-01-24", "value": 0.94},
      {"date": "2025-01-25", "value": 0.97}
    ],
    "trend": "increasing",
    "change_percentage": 1.04
  }
}
```

---

## Health Checks

### Communication Health Check

**GET** `/api/communication/health`

Health check for communication system.

#### Response

**Success (200)**
```json
{
  "status": "healthy",
  "services": {
    "preference_service": true,
    "analytics_service": true,
    "celery_integration": true,
    "twilio_configured": true,
    "resend_configured": true
  },
  "timestamp": "2025-01-27T10:00:00Z",
  "version": "1.0.0"
}
```

**Degraded (503)**
```json
{
  "status": "degraded",
  "services": {
    "preference_service": true,
    "analytics_service": false,
    "celery_integration": true,
    "twilio_configured": true,
    "resend_configured": true
  },
  "timestamp": "2025-01-27T10:00:00Z",
  "version": "1.0.0"
}
```

---

## Error Handling

### Standard Error Response

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error description",
  "details": "Detailed error message",
  "context": "endpoint_context"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Authentication required |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

### Common Error Scenarios

#### Invalid Trigger Type
```json
{
  "error": "Invalid trigger type: unknown_trigger"
}
```

#### Missing Required Fields
```json
{
  "error": "Missing required field: user_id"
}
```

#### Invalid Webhook Signature
```json
{
  "error": "Invalid signature"
}
```

#### Service Unavailable
```json
{
  "error": "Communication service error",
  "details": "Database connection failed",
  "context": "send_communication"
}
```

---

## Rate Limiting

The API implements rate limiting based on user and endpoint:

- **General endpoints**: 100 requests per minute per user
- **Communication sending**: 10 requests per minute per user
- **Batch operations**: 5 requests per minute per user
- **Analytics queries**: 50 requests per minute per user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time

---

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Required Scopes

- `communication:send` - Send communications
- `communication:read` - Read communication data
- `preferences:manage` - Manage user preferences
- `analytics:read` - Read analytics data

---

## Webhook Security

Webhooks require signature verification:

### Twilio Webhook Signature
```python
# Verify using X-Twilio-Signature header
signature = request.headers.get('X-Twilio-Signature')
```

### Resend Webhook Signature
```python
# Verify using X-Resend-Signature header
signature = request.headers.get('X-Resend-Signature')
```

---

## Best Practices

### Sending Communications

1. **Use appropriate trigger types** for different scenarios
2. **Include relevant data** in the request body
3. **Respect user preferences** and consent
4. **Monitor task status** for delivery confirmation
5. **Handle failures gracefully** with fallback options

### Managing Preferences

1. **Always check consent** before sending communications
2. **Provide clear opt-out options** in all messages
3. **Respect frequency limits** to avoid spam
4. **Use smart defaults** for new users
5. **Track preference changes** for compliance

### Analytics and Reporting

1. **Monitor key metrics** regularly
2. **Set up alerts** for performance issues
3. **Track costs** to stay within budget
4. **Analyze trends** to optimize performance
5. **Use A/B testing** for content optimization

### Webhook Handling

1. **Verify signatures** for security
2. **Handle all event types** appropriately
3. **Process opt-outs** immediately
4. **Log all events** for debugging
5. **Implement retry logic** for failures

---

## SDK Examples

### Python SDK Example

```python
import requests

class CommunicationAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def send_communication(self, user_id, trigger_type, data):
        url = f"{self.base_url}/api/communication/send"
        payload = {
            "user_id": user_id,
            "trigger_type": trigger_type,
            "data": data
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
    
    def get_user_preferences(self, user_id):
        url = f"{self.base_url}/api/communication/preferences/{user_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
```

### JavaScript SDK Example

```javascript
class CommunicationAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async sendCommunication(userId, triggerType, data) {
        const response = await fetch(`${this.baseUrl}/api/communication/send`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                user_id: userId,
                trigger_type: triggerType,
                data: data
            })
        });
        return response.json();
    }
    
    async getUserPreferences(userId) {
        const response = await fetch(`${this.baseUrl}/api/communication/preferences/${userId}`, {
            headers: this.headers
        });
        return response.json();
    }
}
```

---

## Support

For API support and questions:

- **Documentation**: [API Documentation](https://docs.mingusapp.com/api)
- **Support Email**: api-support@mingusapp.com
- **Status Page**: [API Status](https://status.mingusapp.com)
- **Rate Limits**: [Rate Limit Guide](https://docs.mingusapp.com/api/rate-limits) 