# Enhanced Communication Preferences System for MINGUS

## Overview

The Enhanced Communication Preferences System provides comprehensive user communication preference management with full TCPA and GDPR compliance. This system handles user consent, communication channel preferences, frequency settings, smart defaults based on user segments, and complete audit trails for all communication activities.

## Key Features

### 1. User Preference Management
- **Channel Preferences**: SMS, Email, Push, In-App notifications
- **Granular Alert Type Control**: JSON-based preferences for each alert type per channel
- **Frequency Settings**: Immediate, Daily, Weekly, Monthly, Quarterly, Never
- **Delivery Timing**: Optimal send times based on user preferences and activity patterns
- **Smart Defaults**: Automatic preference optimization based on user segments

### 2. TCPA Compliance for SMS
- **Explicit Opt-in Workflow**: Phone verification with SMS code
- **Opt-out Handling**: "STOP" message processing and tracking
- **Consent Tracking**: Timestamps and complete audit trail
- **Re-opt-in Capabilities**: User can re-enable SMS communications
- **Phone Number Validation**: Comprehensive validation for international formats

### 3. GDPR Compliance for Email
- **Granular Unsubscribe Options**: Per-alert-type and per-channel opt-outs
- **Email Preference Center**: User-friendly preference management
- **Double Opt-in**: Required for marketing content
- **Data Export/Deletion**: Full GDPR compliance support
- **Legal Basis Tracking**: Consent, legitimate interest, contract

### 4. Smart Defaults by User Segment
- **New Users**: SMS for critical alerts, Email for education
- **Premium Subscribers**: All communication types enabled
- **At-Risk Users**: SMS re-engagement only
- **High-Engagement Users**: More frequent educational content
- **Inactive Users**: Minimal communication to re-engage

### 5. Compliance Features
- **Phone Number Verification**: SMS code verification for TCPA compliance
- **Timestamp Tracking**: All consent changes tracked with timestamps
- **Automatic Opt-out Handling**: "STOP" SMS replies processed automatically
- **GDPR Data Export**: Complete user data export capability
- **Audit Trail**: All communication preference changes logged

## Database Schema

### Core Tables

#### `communication_preferences`
```sql
CREATE TABLE communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Channel preferences
    sms_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    
    -- User preference fields
    preferred_sms_time TIME DEFAULT '09:00:00',
    preferred_email_day INTEGER DEFAULT 1, -- 0=Monday, 1=Tuesday, etc.
    alert_types_sms JSONB DEFAULT '{"critical_financial": true, ...}',
    alert_types_email JSONB DEFAULT '{"critical_financial": true, ...}',
    frequency_preference frequency_type DEFAULT 'weekly',
    
    -- Content preferences
    financial_alerts_enabled BOOLEAN DEFAULT TRUE,
    career_content_enabled BOOLEAN DEFAULT TRUE,
    wellness_content_enabled BOOLEAN DEFAULT TRUE,
    marketing_content_enabled BOOLEAN DEFAULT FALSE,
    
    -- Delivery timing
    preferred_email_time TIME DEFAULT '18:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- User segment for defaults
    user_segment user_segment DEFAULT 'new_user',
    
    -- Smart defaults
    auto_adjust_frequency BOOLEAN DEFAULT TRUE,
    engagement_based_optimization BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

#### `sms_consent`
```sql
CREATE TABLE sms_consent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Phone number verification
    phone_number VARCHAR(20) NOT NULL,
    phone_verified BOOLEAN DEFAULT FALSE,
    verification_code VARCHAR(10),
    verification_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- TCPA compliance fields
    consent_granted BOOLEAN DEFAULT FALSE,
    consent_granted_at TIMESTAMP WITH TIME ZONE,
    consent_source VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Opt-out tracking
    opted_out BOOLEAN DEFAULT FALSE,
    opted_out_at TIMESTAMP WITH TIME ZONE,
    opt_out_reason VARCHAR(200),
    opt_out_method VARCHAR(50),
    
    -- Re-engagement
    re_engaged BOOLEAN DEFAULT FALSE,
    re_engaged_at TIMESTAMP WITH TIME ZONE,
    re_engagement_method VARCHAR(50),
    
    -- Compliance tracking
    last_message_sent_at TIMESTAMP WITH TIME ZONE,
    messages_sent_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

#### `delivery_logs`
```sql
CREATE TABLE delivery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferences_id UUID REFERENCES communication_preferences(id) ON DELETE CASCADE,
    
    -- Delivery details
    alert_type alert_type NOT NULL,
    channel communication_channel NOT NULL,
    message_id VARCHAR(100),
    
    -- Content and timing
    subject TEXT,
    content_preview TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery status
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    
    -- User engagement
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Compliance tracking
    consent_verified BOOLEAN DEFAULT FALSE,
    compliance_checks_passed BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `opt_out_history`
```sql
CREATE TABLE opt_out_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Opt-out details
    channel communication_channel NOT NULL,
    alert_type alert_type,
    reason VARCHAR(200),
    
    -- Opt-out method
    method VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    
    -- Timing
    opted_out_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Re-engagement
    re_engaged_at TIMESTAMP WITH TIME ZONE,
    re_engagement_method VARCHAR(50),
    
    -- Compliance tracking
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### Preference Management

#### GET `/api/communication-preferences/preferences`
Get user communication preferences.

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "user_id": 123,
        "sms_enabled": true,
        "email_enabled": true,
        "preferred_sms_time": "09:00",
        "preferred_email_day": 1,
        "alert_types_sms": {
            "critical_financial": true,
            "bill_reminders": true,
            "marketing_content": false
        },
        "alert_types_email": {
            "critical_financial": true,
            "bill_reminders": true,
            "marketing_content": false
        },
        "frequency_preference": "weekly",
        "user_segment": "new_user"
    }
}
```

#### PUT `/api/communication-preferences/preferences`
Update user communication preferences.

**Request:**
```json
{
    "sms_enabled": false,
    "preferred_sms_time": "10:00",
    "alert_types_sms": {
        "critical_financial": true,
        "marketing_content": false
    },
    "frequency_preference": "daily"
}
```

#### POST `/api/communication-preferences/preferences/reset`
Reset user preferences to defaults based on user segment.

### Consent Management

#### POST `/api/communication-preferences/consent/sms`
Grant SMS consent for TCPA compliance.

**Request:**
```json
{
    "phone_number": "+1234567890",
    "consent_source": "web_form",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
}
```

#### POST `/api/communication-preferences/consent/sms/verify`
Verify phone number with SMS code.

**Request:**
```json
{
    "verification_code": "123456"
}
```

#### POST `/api/communication-preferences/consent/email`
Grant email consent for GDPR compliance.

**Request:**
```json
{
    "consent_type": "email",
    "legal_basis": "consent",
    "purpose": "Marketing communications",
    "consent_source": "web_form"
}
```

#### POST `/api/communication-preferences/consent/revoke`
Revoke consent for communications.

**Request:**
```json
{
    "consent_type": "sms",
    "consent_source": "api"
}
```

### Opt-Out Management

#### POST `/api/communication-preferences/opt-out`
Handle user opt-out request.

**Request:**
```json
{
    "channel": "sms",
    "message_type": "marketing_content",
    "reason": "Too many messages"
}
```

#### POST `/api/communication-preferences/opt-out/sms-stop`
Public endpoint for SMS STOP requests.

**Request:**
```json
{
    "phone_number": "+1234567890"
}
```

### Consent Checking

#### POST `/api/communication-preferences/consent/check`
Check if user has consented to receive a specific message type.

**Request:**
```json
{
    "message_type": "critical_financial",
    "channel": "sms"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "can_send": true,
        "reason": "Consent verified",
        "message_type": "critical_financial",
        "channel": "sms"
    }
}
```

#### GET `/api/communication-preferences/optimal-send-time`
Get optimal send time for user.

**Query Parameters:**
- `channel`: sms, email, push, in_app

**Response:**
```json
{
    "success": true,
    "data": {
        "optimal_send_time": "2025-01-28T09:00:00Z",
        "channel": "sms"
    }
}
```

### Analytics and Reporting

#### GET `/api/communication-preferences/engagement`
Get user engagement summary.

**Response:**
```json
{
    "success": true,
    "data": {
        "total_messages_sent": 100,
        "total_messages_opened": 80,
        "sms_engagement_rate": 85,
        "email_engagement_rate": 75,
        "current_frequency": "weekly",
        "engagement_trend": "increasing"
    }
}
```

#### GET `/api/communication-preferences/compliance-report`
Get compliance report for user.

**Response:**
```json
{
    "success": true,
    "data": {
        "sms_consent": {
            "granted": true,
            "granted_at": "2025-01-27T10:00:00Z",
            "phone_verified": true,
            "opted_out": false
        },
        "email_consent": {
            "status": "granted",
            "granted_at": "2025-01-27T10:00:00Z"
        },
        "opt_outs": [
            {
                "channel": "sms",
                "alert_type": "marketing_content",
                "opted_out_at": "2025-01-26T15:30:00Z",
                "reason": "User request"
            }
        ],
        "recent_deliveries": [
            {
                "alert_type": "critical_financial",
                "channel": "sms",
                "status": "delivered",
                "sent_at": "2025-01-27T09:00:00Z"
            }
        ]
    }
}
```

### Public Endpoints

#### POST `/api/communication-preferences/public/opt-out`
Public opt-out endpoint for email communications.

**Request:**
```json
{
    "email": "user@example.com",
    "channel": "email"
}
```

#### POST `/api/communication-preferences/public/consent`
Public consent endpoint for email communications.

**Request:**
```json
{
    "email": "user@example.com",
    "consent_type": "email"
}
```

## Service Layer

### CommunicationPreferenceService

The service provides comprehensive methods for managing communication preferences:

#### Core Methods

- `get_user_communication_prefs(user_id)`: Get user preferences
- `update_user_preferences(user_id, preferences_dict)`: Update preferences
- `check_consent_for_message_type(user_id, message_type, channel)`: Check consent
- `handle_opt_out_request(user_id, channel, message_type, reason)`: Handle opt-out
- `get_optimal_send_time(user_id, channel)`: Get optimal send time

#### Consent Management

- `grant_sms_consent(user_id, phone_number, consent_source, ...)`: Grant SMS consent
- `verify_phone_number(user_id, verification_code)`: Verify phone number
- `log_delivery(user_id, alert_type, channel, message_id, status)`: Log delivery

#### Analytics and Reporting

- `get_user_engagement_summary(user_id)`: Get engagement summary
- `get_compliance_report(user_id)`: Get compliance report

#### Helper Methods

- `_validate_phone_number(phone_number)`: Validate phone number format
- `_get_smart_defaults(user_segment)`: Get smart defaults by user segment
- `_create_default_preferences(user_id)`: Create default preferences
- `_create_default_alert_preferences(user_id, preferences_id, user_segment)`: Create alert preferences
- `_create_engagement_metrics(user_id)`: Create engagement metrics

## Smart Defaults by User Segment

### New User
```json
{
    "sms_enabled": true,
    "email_enabled": true,
    "frequency_preference": "weekly",
    "alert_types_sms": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": false
    },
    "alert_types_email": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": false
    }
}
```

### Premium Subscriber
```json
{
    "sms_enabled": true,
    "email_enabled": true,
    "frequency_preference": "daily",
    "alert_types_sms": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": true
    },
    "alert_types_email": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": true
    }
}
```

### At-Risk User
```json
{
    "sms_enabled": true,
    "email_enabled": false,
    "frequency_preference": "daily",
    "alert_types_sms": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": false
    },
    "alert_types_email": {
        "critical_financial": false,
        "bill_reminders": false,
        "marketing_content": false
    }
}
```

### High Engagement User
```json
{
    "sms_enabled": true,
    "email_enabled": true,
    "frequency_preference": "daily",
    "alert_types_sms": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": true
    },
    "alert_types_email": {
        "critical_financial": true,
        "bill_reminders": true,
        "marketing_content": true
    }
}
```

## Database Functions

### `handle_sms_stop_request(phone_number)`
Handles SMS STOP requests for TCPA compliance.

### `get_optimal_send_time(user_id, channel)`
Calculates optimal send time based on user preferences.

### `check_consent_for_message_type(user_id, message_type, channel)`
Checks if user has consented to receive a specific message type.

## Integration with Celery Tasks

The communication preferences system integrates with the Celery task system:

```python
# In Celery tasks
from backend.services.communication_preference_service import communication_preference_service

def send_sms_task(user_id, message_type, content):
    # Check consent before sending
    can_send, reason = communication_preference_service.check_consent_for_message_type(
        user_id, message_type, CommunicationChannel.SMS
    )
    
    if not can_send:
        logger.warning(f"Cannot send SMS to user {user_id}: {reason}")
        return False
    
    # Send message
    # ...
    
    # Log delivery
    communication_preference_service.log_delivery(
        user_id, AlertType(message_type), CommunicationChannel.SMS, message_id, "delivered"
    )
```

## Testing

Comprehensive test coverage is provided in `tests/test_communication_preferences_enhanced.py`:

- Preference management tests
- Consent management tests
- Opt-out handling tests
- Optimal send time calculation tests
- SMS consent and verification tests
- Delivery logging tests
- Engagement and compliance reporting tests
- Helper function tests
- Integration workflow tests
- Error handling tests

## Migration

The system includes a comprehensive migration script (`migrations/004_enhance_communication_preferences.sql`) that:

- Adds new columns to existing tables
- Creates new tables for enhanced functionality
- Adds database functions for compliance
- Creates indexes for performance
- Sets up triggers for automatic updates
- Inserts default communication policies
- Migrates existing user data

## Compliance Features

### TCPA Compliance
- Explicit opt-in required for SMS
- Phone number verification
- "STOP" message handling
- Opt-out tracking and respect
- Consent audit trail

### GDPR Compliance
- Granular consent management
- Legal basis tracking
- Data retention policies
- Right to be forgotten
- Data portability

### Audit Trail
- All consent changes logged
- Opt-out history tracked
- Delivery logs maintained
- Compliance reports available

## Performance Considerations

- Indexes on frequently queried columns
- JSONB for flexible alert type preferences
- Efficient consent checking queries
- Caching for user preferences
- Batch processing for analytics

## Security Features

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting on public endpoints
- Audit logging for all changes

## Monitoring and Alerting

- Delivery success rate tracking
- Opt-out rate monitoring
- Consent compliance alerts
- Performance metrics
- Error rate monitoring

This enhanced communication preferences system provides a comprehensive, compliant, and user-friendly solution for managing all aspects of user communication preferences in the MINGUS financial application. 