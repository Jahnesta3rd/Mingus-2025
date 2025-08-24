# MINGUS Communication Preferences and Consent Management System

## Overview

The MINGUS Communication Preferences and Consent Management System provides comprehensive user communication preference management with full TCPA and GDPR compliance. This system handles user consent, communication channel preferences, frequency settings, and smart defaults based on user behavior.

## Features

### 1. User Preference Management
- **Channel Preferences**: SMS, Email, Push, In-App notifications
- **Frequency Settings**: Immediate, Daily, Weekly, Monthly, Quarterly, Never
- **Content Type Preferences**: Financial alerts, Career content, Wellness tips, Marketing content
- **Delivery Timing**: Optimal send times based on user activity patterns
- **Smart Defaults**: Automatic preference optimization based on user engagement

### 2. TCPA Compliance for SMS
- **Explicit Opt-in Workflow**: Phone verification with SMS code
- **Opt-out Handling**: "STOP" message processing
- **Consent Tracking**: Timestamps and audit trail
- **Re-opt-in Capabilities**: User can re-enable SMS communications

### 3. Email Compliance (GDPR)
- **Subscription Management**: Granular unsubscribe options
- **Email Preference Center**: User-controlled email settings
- **Double Opt-in**: Required for marketing content
- **Data Retention**: Configurable retention periods

### 4. Smart Defaults Based on User Profile
- **New Users**: SMS for critical alerts, Email for education
- **High-engagement Users**: More email content enabled
- **At-risk Users**: SMS re-engagement focused
- **Premium Subscribers**: All content types enabled

### 5. Preference Learning System
- **Engagement Tracking**: Monitor user response patterns
- **Automatic Frequency Adjustment**: Based on response rates
- **A/B Testing**: Optimal communication strategies
- **Cultural/Demographic Defaults**: Region-based preferences

### 6. Admin Interface
- **Policy Management**: System-wide communication policies
- **Consent Status Monitoring**: Real-time user consent tracking
- **Analytics Dashboard**: Delivery rates and engagement metrics
- **Compliance Reporting**: Audit trails and regulatory compliance

## Database Schema

### Core Tables

#### `communication_preferences`
Stores user communication preferences and settings.

```sql
CREATE TABLE communication_preferences (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Channel preferences
    sms_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    
    -- Frequency preferences
    critical_frequency frequency_type DEFAULT 'immediate',
    daily_frequency frequency_type DEFAULT 'daily',
    weekly_frequency frequency_type DEFAULT 'weekly',
    monthly_frequency frequency_type DEFAULT 'monthly',
    
    -- Content type preferences
    financial_alerts_enabled BOOLEAN DEFAULT TRUE,
    career_content_enabled BOOLEAN DEFAULT TRUE,
    wellness_content_enabled BOOLEAN DEFAULT TRUE,
    marketing_content_enabled BOOLEAN DEFAULT FALSE,
    
    -- Delivery timing preferences
    preferred_sms_time VARCHAR(5) DEFAULT '09:00',
    preferred_email_time VARCHAR(5) DEFAULT '18:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Smart defaults
    auto_adjust_frequency BOOLEAN DEFAULT TRUE,
    engagement_based_optimization BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `consent_records`
Tracks TCPA and GDPR consent with full audit trail.

```sql
CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id),
    
    -- Consent details
    consent_type VARCHAR(50) NOT NULL, -- 'sms', 'email', 'marketing'
    consent_status consent_status DEFAULT 'pending',
    
    -- TCPA compliance fields
    phone_number VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent TEXT,
    consent_source VARCHAR(100) NOT NULL, -- 'web_form', 'mobile_app', 'api'
    
    -- GDPR compliance fields
    legal_basis VARCHAR(50), -- 'consent', 'legitimate_interest', 'contract'
    purpose TEXT,
    data_retention_period INTEGER, -- days
    
    -- Consent lifecycle
    granted_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Verification
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_method VARCHAR(50), -- 'sms_code', 'email_link', 'manual'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `alert_type_preferences`
Granular preferences for specific alert types.

```sql
CREATE TABLE alert_type_preferences (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id),
    
    alert_type alert_type NOT NULL,
    sms_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    
    frequency frequency_type NOT NULL,
    priority INTEGER DEFAULT 5, -- 1-10 scale
    preferred_time VARCHAR(5), -- HH:MM format
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, alert_type)
);
```

#### `communication_delivery_logs`
Logs all communication deliveries for compliance and analytics.

```sql
CREATE TABLE communication_delivery_logs (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id),
    
    -- Delivery details
    alert_type alert_type NOT NULL,
    channel communication_channel NOT NULL,
    message_id VARCHAR(100), -- External service message ID
    
    -- Content and timing
    subject TEXT,
    content_preview TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery status
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
    error_message TEXT,
    
    -- User engagement
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Compliance tracking
    consent_verified BOOLEAN DEFAULT FALSE,
    compliance_checks_passed BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `opt_out_records`
Tracks opt-outs for compliance and re-engagement.

```sql
CREATE TABLE opt_out_records (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Opt-out details
    channel communication_channel NOT NULL,
    alert_type alert_type, -- null means all types
    reason VARCHAR(200),
    
    -- Opt-out method
    method VARCHAR(50) NOT NULL, -- 'sms_stop', 'email_unsubscribe', 'web_form', 'api'
    source VARCHAR(100), -- 'sms', 'email', 'web', 'mobile_app'
    
    -- Timing
    opted_out_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- for temporary opt-outs
    
    -- Re-engagement
    re_engaged_at TIMESTAMP WITH TIME ZONE,
    re_engagement_method VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `user_engagement_metrics`
Tracks user engagement for preference optimization.

```sql
CREATE TABLE user_engagement_metrics (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Engagement metrics
    total_messages_sent INTEGER DEFAULT 0,
    total_messages_opened INTEGER DEFAULT 0,
    total_messages_clicked INTEGER DEFAULT 0,
    total_messages_responded INTEGER DEFAULT 0,
    
    -- Channel-specific metrics
    sms_engagement_rate INTEGER DEFAULT 0, -- percentage
    email_engagement_rate INTEGER DEFAULT 0, -- percentage
    push_engagement_rate INTEGER DEFAULT 0, -- percentage
    
    -- Alert type engagement
    alert_type_engagement JSONB, -- {alert_type: engagement_rate}
    
    -- Timing preferences
    optimal_send_times JSONB, -- {day_of_week: {hour: engagement_rate}}
    
    -- Frequency optimization
    current_frequency VARCHAR(50) DEFAULT 'weekly',
    recommended_frequency VARCHAR(50),
    frequency_adjustment_reason TEXT,
    
    -- Last engagement
    last_engagement_at TIMESTAMP WITH TIME ZONE,
    engagement_trend VARCHAR(20) DEFAULT 'stable', -- increasing, decreasing, stable
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

#### `communication_policies`
System-wide communication policies and rules.

```sql
CREATE TABLE communication_policies (
    id UUID PRIMARY KEY,
    
    -- Policy details
    policy_name VARCHAR(100) NOT NULL,
    policy_type VARCHAR(50) NOT NULL, -- 'default', 'tier_based', 'region_based'
    
    -- Target criteria
    user_tier VARCHAR(50), -- 'free', 'premium', 'enterprise'
    region VARCHAR(50),
    user_segment VARCHAR(50), -- 'new_user', 'engaged', 'at_risk'
    
    -- Policy rules
    default_channel communication_channel DEFAULT 'email',
    default_frequency frequency_type DEFAULT 'weekly',
    max_messages_per_day INTEGER DEFAULT 5,
    max_messages_per_week INTEGER DEFAULT 20,
    
    -- Content restrictions
    allowed_alert_types JSONB, -- list of allowed alert types
    marketing_content_allowed BOOLEAN DEFAULT FALSE,
    
    -- Compliance settings
    require_double_optin BOOLEAN DEFAULT TRUE,
    consent_retention_days INTEGER DEFAULT 2555, -- 7 years
    auto_optout_inactive_days INTEGER DEFAULT 365, -- 1 year
    
    -- Timing restrictions
    quiet_hours_start VARCHAR(5) DEFAULT '22:00', -- HH:MM format
    quiet_hours_end VARCHAR(5) DEFAULT '08:00', -- HH:MM format
    timezone_aware BOOLEAN DEFAULT TRUE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5, -- 1-10 scale for policy precedence
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

## API Endpoints

### User Communication Preferences

#### GET `/api/communication-preferences/preferences`
Get user communication preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_id": "user_id",
    "sms_enabled": true,
    "email_enabled": true,
    "push_enabled": false,
    "in_app_enabled": true,
    "critical_frequency": "immediate",
    "daily_frequency": "daily",
    "weekly_frequency": "weekly",
    "monthly_frequency": "monthly",
    "financial_alerts_enabled": true,
    "career_content_enabled": true,
    "wellness_content_enabled": true,
    "marketing_content_enabled": false,
    "preferred_sms_time": "09:00",
    "preferred_email_time": "18:00",
    "timezone": "UTC",
    "auto_adjust_frequency": true,
    "engagement_based_optimization": true
  }
}
```

#### PUT `/api/communication-preferences/preferences`
Update user communication preferences.

**Request:**
```json
{
  "sms_enabled": true,
  "email_enabled": false,
  "critical_frequency": "immediate",
  "marketing_content_enabled": true,
  "preferred_sms_time": "10:00"
}
```

#### GET `/api/communication-preferences/alert-type-preferences`
Get user alert type preferences.

#### PUT `/api/communication-preferences/alert-type-preferences/{alert_type}`
Update specific alert type preference.

### Consent Management

#### POST `/api/communication-preferences/consent`
Grant consent for communication.

**Request:**
```json
{
  "consent_type": "sms",
  "phone_number": "+1234567890",
  "consent_source": "web_form",
  "legal_basis": "consent",
  "purpose": "Financial alerts and notifications"
}
```

#### DELETE `/api/communication-preferences/consent/{consent_type}`
Revoke consent for communication.

#### POST `/api/communication-preferences/consent/{consent_type}/verify`
Verify consent (e.g., SMS code, email link).

#### GET `/api/communication-preferences/consent/status`
Get consent status for all types.

### Opt-out Management

#### POST `/api/communication-preferences/opt-out`
Process opt-out request.

**Request:**
```json
{
  "channel": "sms",
  "alert_type": "marketing_content",
  "reason": "Too many messages",
  "method": "api"
}
```

#### POST `/api/communication-preferences/opt-out/public`
Public opt-out endpoint (for SMS STOP, email unsubscribe).

### Analytics and Monitoring

#### POST `/api/communication-preferences/can-send`
Check if message can be sent to user.

**Request:**
```json
{
  "alert_type": "critical_financial",
  "channel": "sms"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "can_send": true,
    "reason": "OK",
    "alert_type": "critical_financial",
    "channel": "sms"
  }
}
```

#### GET `/api/communication-preferences/engagement`
Get user engagement summary.

#### GET `/api/communication-preferences/compliance-report`
Get compliance report for user.

## Admin API Endpoints

### Policy Management

#### GET `/api/admin/communication/policies`
Get all communication policies.

#### POST `/api/admin/communication/policies`
Create a new communication policy.

#### PUT `/api/admin/communication/policies/{policy_id}`
Update a communication policy.

#### DELETE `/api/admin/communication/policies/{policy_id}`
Delete a communication policy.

### User Consent Management

#### GET `/api/admin/communication/user-consent`
Get user consent data with filtering.

**Query Parameters:**
- `consent_type`: Filter by consent type (sms, email, marketing)
- `consent_status`: Filter by status (pending, granted, denied, revoked, expired)
- `date_from`: Filter by date range
- `date_to`: Filter by date range
- `limit`: Pagination limit (1-1000)
- `offset`: Pagination offset

#### GET `/api/admin/communication/user-consent/summary`
Get consent summary statistics.

#### GET `/api/admin/communication/user-consent/{user_id}`
Get detailed consent information for a specific user.

### Analytics

#### GET `/api/admin/communication/analytics/delivery-rates`
Get delivery rate analytics.

#### GET `/api/admin/communication/analytics/engagement`
Get user engagement analytics.

## Service Layer

### CommunicationPreferenceService

The main service class that handles all communication preference logic:

```python
class CommunicationPreferenceService:
    def create_user_preferences(self, user_id: str, **kwargs) -> CommunicationPreferences
    def get_user_preferences(self, user_id: str) -> Optional[CommunicationPreferences]
    def update_preferences(self, user_id: str, **updates) -> CommunicationPreferences
    def grant_consent(self, user_id: str, consent_type: str, **kwargs) -> ConsentRecord
    def revoke_consent(self, user_id: str, consent_type: str, reason: str = None) -> bool
    def verify_consent(self, user_id: str, consent_type: str, verification_method: str) -> bool
    def check_consent_status(self, user_id: str, consent_type: str) -> ConsentStatus
    def process_opt_out(self, user_id: str, channel: CommunicationChannel, 
                       alert_type: AlertType = None, method: str = 'api') -> bool
    def can_send_message(self, user_id: str, alert_type: AlertType, 
                        channel: CommunicationChannel) -> Tuple[bool, str]
    def log_delivery(self, user_id: str, alert_type: AlertType, channel: CommunicationChannel,
                    message_id: str = None, **kwargs) -> CommunicationDeliveryLog
    def get_optimal_send_time(self, user_id: str, channel: CommunicationChannel) -> str
    def get_user_engagement_summary(self, user_id: str) -> Dict[str, Any]
    def get_compliance_report(self, user_id: str) -> Dict[str, Any]
```

## Compliance Features

### TCPA Compliance
- **Explicit Consent**: Users must explicitly opt-in to SMS communications
- **Clear Disclosure**: Purpose and frequency of communications clearly stated
- **Easy Opt-out**: "STOP" keyword processing and web-based opt-out
- **Consent Records**: Full audit trail with timestamps and verification
- **Re-opt-in**: Users can re-enable SMS communications

### GDPR Compliance
- **Legal Basis**: Clear legal basis for data processing (consent, legitimate interest, contract)
- **Purpose Limitation**: Specific purposes for data processing
- **Data Retention**: Configurable retention periods
- **Right to Withdraw**: Easy consent withdrawal
- **Data Portability**: Export user consent data
- **Privacy by Design**: Built-in privacy controls

### CAN-SPAM Compliance
- **Clear Identification**: Sender identification in emails
- **Subject Line Accuracy**: Honest subject lines
- **Physical Address**: Company address in emails
- **Opt-out Mechanism**: Easy unsubscribe process
- **Honor Opt-outs**: Process opt-outs within 10 business days

## Smart Defaults and Optimization

### User Profile Analysis
The system analyzes user profiles to determine optimal communication preferences:

- **New Users**: Conservative defaults with focus on critical alerts
- **Engaged Users**: More frequent communications and diverse content types
- **At-risk Users**: SMS-focused re-engagement strategies
- **Premium Users**: Full feature access with all content types

### Engagement-Based Optimization
- **Response Rate Analysis**: Adjust frequency based on user engagement
- **Channel Preference Learning**: Identify user's preferred channels
- **Timing Optimization**: Determine optimal send times
- **Content Relevance**: Adjust content types based on user behavior

### A/B Testing Framework
- **Frequency Testing**: Test different communication frequencies
- **Channel Testing**: Compare SMS vs Email effectiveness
- **Content Testing**: Test different message formats and content
- **Timing Testing**: Test different send times

## Integration Points

### Celery Task System
The communication preferences system integrates with the Celery task system for:

- **Scheduled Communications**: Respect user frequency preferences
- **Delivery Logging**: Track all communication attempts
- **Engagement Tracking**: Monitor user responses
- **Compliance Checks**: Verify consent before sending

### External Services
- **Twilio SMS**: SMS delivery and verification
- **Resend Email**: Email delivery and tracking
- **Push Notifications**: Mobile push notification delivery
- **Analytics Platforms**: Engagement and delivery analytics

## Security and Privacy

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **Access Controls**: Role-based access to admin functions
- **Audit Logging**: Complete audit trail for all operations
- **Data Minimization**: Only collect necessary data

### Privacy Controls
- **User Control**: Users have full control over their preferences
- **Transparency**: Clear information about data usage
- **Consent Management**: Granular consent controls
- **Data Portability**: Export user data on request

## Monitoring and Alerting

### System Health
- **Queue Monitoring**: Monitor communication queue depths
- **Delivery Rates**: Track successful vs failed deliveries
- **Consent Compliance**: Monitor consent status across users
- **Performance Metrics**: Track system performance

### Alerting
- **High Failure Rates**: Alert on delivery failures
- **Consent Violations**: Alert on potential compliance issues
- **System Issues**: Alert on system health problems
- **User Complaints**: Track and respond to user feedback

## Best Practices

### Implementation Guidelines
1. **Always Check Consent**: Verify consent before sending any communication
2. **Respect Preferences**: Honor user communication preferences
3. **Monitor Engagement**: Track and respond to user engagement patterns
4. **Maintain Compliance**: Regular compliance audits and updates
5. **User Education**: Provide clear information about communication options

### Operational Guidelines
1. **Regular Audits**: Conduct regular compliance audits
2. **User Feedback**: Monitor and respond to user feedback
3. **Performance Monitoring**: Track system performance metrics
4. **Documentation**: Maintain up-to-date documentation
5. **Training**: Regular staff training on compliance requirements

## Troubleshooting

### Common Issues
1. **Consent Verification Failures**: Check verification method and user input
2. **Delivery Failures**: Verify user preferences and consent status
3. **Opt-out Processing**: Ensure opt-outs are processed correctly
4. **Performance Issues**: Monitor queue depths and system resources

### Debugging Tools
1. **Compliance Reports**: Generate detailed compliance reports
2. **Delivery Logs**: Review delivery logs for issues
3. **User Consent History**: Track user consent changes over time
4. **System Metrics**: Monitor system performance and health

## Future Enhancements

### Planned Features
1. **AI-Powered Optimization**: Machine learning for preference optimization
2. **Advanced Analytics**: Predictive analytics for user behavior
3. **Multi-language Support**: Internationalization for global users
4. **Advanced Segmentation**: More sophisticated user segmentation
5. **Real-time Optimization**: Real-time preference adjustment

### Integration Opportunities
1. **Marketing Automation**: Integration with marketing platforms
2. **Customer Support**: Integration with support systems
3. **Analytics Platforms**: Enhanced analytics integration
4. **Compliance Tools**: Integration with compliance monitoring tools 