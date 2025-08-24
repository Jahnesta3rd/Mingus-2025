# Financial Alert Detection System for MINGUS

## Overview

The Financial Alert Detection System is a comprehensive monitoring and notification system designed specifically for African American professionals (25-35, $40k-$100k income) that intelligently detects financial risks and opportunities, then routes appropriate SMS/Email notifications based on user engagement patterns and cultural context.

## 🎯 Key Features

### 1. **Intelligent Alert Detection**
- **Cash Flow Monitoring**: Detects when account balance will go negative within 7 days
- **Bill Payment Reminders**: Alerts for upcoming rent, student loans, and family obligations
- **Subscription Renewals**: Notifications for subscription payments
- **Unusual Spending Patterns**: AI-powered anomaly detection
- **Budget Exceeded Alerts**: When spending exceeds budget by 20%+
- **Emergency Fund Monitoring**: Alerts when emergency fund drops below 25% of target

### 2. **Smart Communication Routing**
- **SMS for Urgent Alerts**: Critical financial alerts, payment reminders
- **Email for Detailed Content**: Monthly reports, educational content, spending analysis
- **Engagement-Based Routing**: High engagement users get more emails, low engagement users get more SMS
- **Cultural Personalization**: Tailored messaging for African American professionals

### 3. **Cultural Context Integration**
- **Regional Cost of Living**: Atlanta, Houston, DC Metro, NYC, LA, Chicago, Miami, Dallas
- **Income Level Personalization**: Different strategies for $40k-60k, $60k-80k, $80k-100k
- **Family Financial Obligations**: Recognition of family support responsibilities
- **Career Advancement Focus**: Support for professional development goals

## 🏗️ Architecture

### Database Models

#### `FinancialAlert`
```sql
-- Tracks all financial alerts
CREATE TABLE financial_alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- cash_flow, bill_payment, subscription, etc.
    urgency_level VARCHAR(20) NOT NULL,  -- critical, high, medium, low
    trigger_amount DECIMAL(10,2),
    current_balance DECIMAL(10,2),
    projected_balance DECIMAL(10,2),
    due_date TIMESTAMP,
    days_until_negative INTEGER,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    sms_message TEXT,
    email_subject VARCHAR(200),
    email_content TEXT,
    communication_channel VARCHAR(20) NOT NULL,  -- sms, email, both
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `UserFinancialContext`
```sql
-- User financial context for personalization
CREATE TABLE user_financial_contexts (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL,
    primary_income_source VARCHAR(50),  -- full_time, part_time, gig_work, business
    monthly_income DECIMAL(10,2),
    income_frequency VARCHAR(20),  -- weekly, bi_weekly, monthly
    student_loan_payment DECIMAL(10,2),
    student_loan_due_date INTEGER,  -- Day of month
    family_obligations DECIMAL(10,2),
    rent_mortgage DECIMAL(10,2),
    rent_mortgage_due_date INTEGER,
    emergency_fund_balance DECIMAL(10,2),
    emergency_fund_target DECIMAL(10,2),
    regional_cost_of_living VARCHAR(50),
    primary_financial_goal VARCHAR(100),
    optimal_engagement_time VARCHAR(20)
);
```

#### `CashFlowForecast`
```sql
-- Cash flow forecasting for alert detection
CREATE TABLE cash_flow_forecasts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    forecast_date TIMESTAMP NOT NULL,
    projected_balance DECIMAL(10,2) NOT NULL,
    confidence_level DECIMAL(3,2),
    risk_level VARCHAR(20),  -- low, medium, high, critical
    days_until_negative INTEGER,
    negative_balance_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `SpendingPattern`
```sql
-- Spending pattern analysis for anomaly detection
CREATE TABLE spending_patterns (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly, seasonal
    average_amount DECIMAL(10,2) NOT NULL,
    standard_deviation DECIMAL(10,2),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(3,2),
    anomaly_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Setup and Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# MINGUS Support Contact
MINGUS_SUPPORT_PHONE=+1-800-MINGUS-1
MINGUS_SUPPORT_EMAIL=support@mingusapp.com

# Redis Configuration (for rate limiting & tracking)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2. Database Migration

Run the database migrations to create the required tables:

```bash
# Create migration
alembic revision --autogenerate -m "Add financial alert detection tables"

# Apply migration
alembic upgrade head
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Celery Workers

```bash
# Start Celery worker
celery -A backend.tasks.communication_tasks worker --loglevel=info

# Start Celery beat for scheduled tasks
celery -A backend.tasks.communication_tasks beat --loglevel=info
```

## 📋 Usage Examples

### 1. Detect Alerts for a User

```python
from backend.services.financial_alert_detector import FinancialAlertDetector
from backend.database import get_db_session

# Get database session
db = get_db_session()

# Initialize detector
detector = FinancialAlertDetector(db)

# Detect alerts for a user
user_id = "user-uuid-here"
alerts = detector.detect_alerts(user_id)

print(f"Detected {len(alerts)} alerts for user {user_id}")
```

### 2. Send Financial Alert

```python
from backend.tasks.communication_tasks import send_financial_alert

# Send alert via Celery task
alert_id = "alert-uuid-here"
result = send_financial_alert.delay(alert_id)

print(f"Alert sent: {result.get()}")
```

### 3. Route Communication Message

```python
from backend.services.communication_router import communication_router
from backend.services.communication_router import CommunicationMessage, MessageType, UrgencyLevel

# Create message
message = CommunicationMessage(
    message_id="msg-uuid",
    user_id="user-uuid",
    message_type=MessageType.FINANCIAL_ALERT,
    urgency_level=UrgencyLevel.CRITICAL,
    content={
        "title": "Cash Flow Alert",
        "message": "Your balance will go negative in 3 days."
    }
)

# Get user profile (simplified)
user_profile = get_user_profile(user_id)

# Route message
routing_decision = communication_router.route_message(message, user_profile)
print(f"Channel: {routing_decision.channel}")
print(f"Reasoning: {routing_decision.reasoning}")
```

## 🎨 Alert Types and Triggers

### 1. Cash Flow Alerts

**Trigger**: Balance going negative within 7 days
**Priority**: Critical
**Channel**: SMS immediately
**Message Example**:
```
⚠️ MINGUS Alert: Your balance will go negative in 5 days. 
Current: $-500.00. Consider transferring funds. 
Reply HELP for assistance.
```

### 2. Bill Payment Reminders

**Trigger**: Bills due in 2-3 days
**Priority**: High
**Channel**: SMS
**Message Example**:
```
📅 MINGUS Reminder: Your Student Loan payment of $350.00 
is due in 3 days. Consider income-driven repayment options 
if you're struggling with payments.
```

### 3. Unusual Spending Patterns

**Trigger**: Spending 50%+ above average in a category
**Priority**: Medium
**Channel**: Email with detailed analysis
**Content**: Detailed spending breakdown with recommendations

### 4. Budget Exceeded Alerts

**Trigger**: Spending 20%+ over budget
**Priority**: High
**Channel**: Both SMS and Email
**Message Example**:
```
💰 MINGUS Alert: Your Transportation spending is 30% over budget. 
Spent: $520.00, Budget: $400.00.
```

### 5. Emergency Fund Alerts

**Trigger**: Emergency fund below 25% of target
**Priority**: Medium
**Channel**: Email with guidance
**Content**: Detailed guidance on building emergency fund

## 🌍 Cultural Personalization

### Regional Cost of Living Adjustments

| Region | Cost Multiplier | Rent Multiplier | Focus Areas |
|--------|----------------|-----------------|-------------|
| Atlanta | 1.0x | 1.0x | Career advancement, home ownership |
| Houston | 0.95x | 0.9x | Energy industry, family support |
| DC Metro | 1.3x | 1.4x | Government careers, networking |
| New York | 1.5x | 1.8x | Finance careers, networking |
| Los Angeles | 1.4x | 1.6x | Entertainment, tech, real estate |
| Chicago | 1.1x | 1.2x | Business, manufacturing |
| Miami | 1.1x | 1.3x | Tourism, international business |
| Dallas | 0.9x | 0.85x | Tech, energy, family support |

### Income Level Personalization

#### $40k-60k Income
- **Financial Priorities**: Budgeting, debt management, savings
- **Investment Approach**: Conservative
- **Education Focus**: Basic financial literacy
- **Alert Frequency**: Higher for critical alerts

#### $60k-80k Income
- **Financial Priorities**: Investing, retirement planning, wealth building
- **Investment Approach**: Moderate
- **Education Focus**: Advanced financial strategies
- **Alert Frequency**: Balanced

#### $80k-100k Income
- **Financial Priorities**: Wealth preservation, tax optimization, legacy planning
- **Investment Approach**: Aggressive
- **Education Focus**: Sophisticated investment strategies
- **Alert Frequency**: Lower, more selective

## 🔄 Communication Routing Logic

### Engagement-Based Routing

| Engagement Level | SMS Frequency | Email Frequency | Primary Channel |
|------------------|---------------|-----------------|-----------------|
| High | Low | High | Email for detailed content |
| Medium | Balanced | Balanced | Mixed approach |
| Low | High | Low | SMS for re-engagement |
| At-Risk | Critical only | Low | SMS for critical alerts |

### Urgency-Based Timing

| Urgency Level | Timing | Channel | Example |
|---------------|--------|---------|---------|
| Critical | Immediate | SMS | Cash flow negative |
| High | Within 1 hour | SMS | Bill payment due |
| Medium | Daily batch | SMS/Email | Check-ins, reminders |
| Low | Weekly | Email | Education, insights |

## 📊 Monitoring and Analytics

### Key Metrics

1. **Alert Detection Rate**: Percentage of actual financial issues detected
2. **False Positive Rate**: Percentage of unnecessary alerts
3. **Response Rate**: User engagement with alerts
4. **Delivery Success Rate**: SMS/Email delivery success
5. **Cost per Alert**: Average cost of sending alerts

### Redis Analytics

The system tracks various metrics in Redis:

```python
# Get SMS statistics
stats = twilio_sms_service.get_sms_statistics(days=30)

# Get user engagement level
engagement = communication_router.get_user_engagement_level(user_id)

# Update user activity
communication_router.update_user_activity(user_id, "email_open")
```

## 🔧 Integration with Existing Systems

### 1. Cash Flow Forecasting System

```python
# Integrate with existing cash flow forecasting
from backend.services.cash_flow_forecaster import CashFlowForecaster

forecaster = CashFlowForecaster()
forecast = forecaster.generate_forecast(user_id)

# Use forecast for alert detection
detector = FinancialAlertDetector(db)
alerts = detector.detect_alerts(user_id)
```

### 2. Payment Processing System

```python
# Integrate with Stripe for subscription alerts
from backend.services.stripe_service import StripeService

stripe_service = StripeService()
subscriptions = stripe_service.get_active_subscriptions(user_id)

# Check for upcoming renewals
for subscription in subscriptions:
    if subscription.days_until_renewal <= 2:
        # Trigger subscription alert
        pass
```

### 3. Banking Integration

```python
# Integrate with Plaid for transaction monitoring
from backend.services.plaid_service import PlaidService

plaid_service = PlaidService()
transactions = plaid_service.get_recent_transactions(user_id)

# Analyze spending patterns
for transaction in transactions:
    # Update spending patterns
    # Check for anomalies
    pass
```

## 🚨 Error Handling and Fallbacks

### 1. SMS Delivery Failure

```python
# SMS fails → Send email for critical alerts
if sms_result.get('success') == False:
    if message.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        email_result = resend_email_service.send_email(...)
```

### 2. No SMS Response in 24h

```python
# No response → Follow-up email
@celery_app.task
def send_follow_up_email(user_id, original_message_id):
    # Send follow-up email with original alert content
    pass
```

### 3. Email Bounce

```python
# Email bounces → Try SMS for urgent content
if email_result.get('bounced'):
    if message.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        sms_result = twilio_sms_service.send_sms(...)
```

## 📈 Performance Optimization

### 1. Rate Limiting

- **Regular Alerts**: 100 SMS/minute
- **Critical Alerts**: 500 SMS/minute
- **Email**: No rate limiting (handled by Resend)

### 2. Batching

- **Medium Priority**: Batched hourly
- **Low Priority**: Batched daily
- **Critical/High**: Sent immediately

### 3. Caching

- **User Profiles**: Cached in Redis for 1 hour
- **Alert Rules**: Cached in Redis for 24 hours
- **Engagement Metrics**: Cached in Redis for 1 hour

## 🔒 Security and Compliance

### 1. TCPA Compliance

- **Opt-in Required**: Users must explicitly opt-in to SMS
- **Opt-out Handling**: Automatic opt-out on STOP, CANCEL, UNSUBSCRIBE
- **Help Support**: HELP keyword provides support information

### 2. Data Privacy

- **PII Protection**: Phone numbers and emails encrypted
- **Audit Logging**: All alert deliveries logged
- **Data Retention**: Alert data retained for 90 days

### 3. Access Control

- **User-Specific**: Users can only access their own alerts
- **Admin Access**: Admins can view system-wide statistics
- **API Rate Limiting**: API endpoints rate-limited

## 🧪 Testing

### 1. Unit Tests

```python
# Test alert detection
def test_cash_flow_alert_detection():
    detector = FinancialAlertDetector(db)
    alerts = detector.detect_alerts(user_id)
    assert len(alerts) > 0
    assert alerts[0].alert_type == 'cash_flow'
```

### 2. Integration Tests

```python
# Test communication routing
def test_communication_routing():
    message = CommunicationMessage(...)
    routing_decision = communication_router.route_message(message, user_profile)
    assert routing_decision.channel in ['sms', 'email', 'both']
```

### 3. End-to-End Tests

```python
# Test complete alert flow
def test_alert_flow():
    # 1. Detect alert
    alerts = detector.detect_alerts(user_id)
    
    # 2. Send alert
    result = send_financial_alert.delay(alert_id)
    
    # 3. Verify delivery
    assert result.get()['success'] == True
```

## 📚 API Reference

### Financial Alert Detector

```python
class FinancialAlertDetector:
    def detect_alerts(self, user_id: str) -> List[FinancialAlert]
    def _detect_cash_flow_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]
    def _detect_bill_payment_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]
    def _detect_spending_pattern_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]
    def _detect_budget_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]
    def _detect_emergency_fund_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]
```

### Communication Router

```python
class CommunicationRouter:
    def route_message(self, message: CommunicationMessage, user_profile: UserProfile) -> RoutingDecision
    def get_user_engagement_level(self, user_id: str) -> UserEngagementLevel
    def update_user_activity(self, user_id: str, activity_type: str)
```

### Celery Tasks

```python
@celery_app.task
def route_and_send_message(message_data: Dict[str, Any]) -> Dict[str, Any]

@celery_app.task
def send_financial_alert(alert_id: str) -> Dict[str, Any]

@celery_app.task
def send_batch_messages(batch_key: str) -> Dict[str, Any]

@celery_app.task
def handle_delivery_fallback(original_message_id: str, fallback_channel: str) -> Dict[str, Any]

@celery_app.task
def check_delivery_status(message_id: str, delivery_method: str) -> Dict[str, Any]

@celery_app.task
def send_follow_up_email(user_id: str, original_message_id: str) -> Dict[str, Any]
```

## 🎯 Best Practices

### 1. Alert Design

- **Clear and Actionable**: Every alert should have a clear next step
- **Culturally Relevant**: Use language and examples relevant to African American professionals
- **Timely**: Send alerts when users can take action
- **Personalized**: Use user's financial context and preferences

### 2. Communication Strategy

- **Respect User Preferences**: Honor SMS/Email preferences
- **Avoid Alert Fatigue**: Don't send too many alerts
- **Provide Value**: Every communication should provide value
- **Support Multiple Channels**: Have fallback options

### 3. Performance

- **Monitor Delivery Rates**: Track SMS/Email delivery success
- **Optimize Timing**: Send messages at optimal engagement times
- **Batch Non-Urgent**: Batch low-priority messages
- **Cache Frequently**: Cache user profiles and preferences

### 4. Cultural Sensitivity

- **Recognize Family Obligations**: Acknowledge family support responsibilities
- **Support Career Goals**: Align with career advancement objectives
- **Community Focus**: Emphasize community and networking
- **Representation Matters**: Use inclusive language and examples

## 🚀 Deployment

### 1. Production Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start Redis
redis-server

# Start Celery workers
celery -A backend.tasks.communication_tasks worker --loglevel=info -Q alerts,communication,batch,fallback,monitoring,followup

# Start Celery beat
celery -A backend.tasks.communication_tasks beat --loglevel=info

# Start web application
python app.py
```

### 2. Monitoring

```bash
# Monitor Celery workers
celery -A backend.tasks.communication_tasks flower

# Monitor Redis
redis-cli monitor

# Check alert statistics
python -c "from backend.services.twilio_sms_service import twilio_sms_service; print(twilio_sms_service.get_sms_statistics())"
```

### 3. Scaling

- **Horizontal Scaling**: Add more Celery workers
- **Queue Separation**: Separate queues for different alert types
- **Database Optimization**: Index frequently queried fields
- **Caching Strategy**: Cache user profiles and preferences

## 📞 Support

For questions or issues with the Financial Alert Detection System:

- **Email**: support@mingusapp.com
- **Phone**: +1-800-MINGUS-1
- **Documentation**: [MINGUS Documentation](https://docs.mingusapp.com)
- **GitHub Issues**: [MINGUS GitHub](https://github.com/mingus-app)

---

**Built with ❤️ for African American professionals building wealth while maintaining healthy relationships.** 