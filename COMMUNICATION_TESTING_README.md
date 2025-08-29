# 📧 MINGUS Communication Features Testing Guide

## 🎯 Overview

This comprehensive test suite validates all communication features in the MINGUS application, including email delivery via Resend, SMS notifications via Twilio, communication routing, and delivery success rates.

## 🧪 Test Coverage

### 📧 Email Delivery via Resend
- **Welcome Emails**: New user onboarding emails with personalized content
- **Password Reset Emails**: Secure password reset functionality
- **Notification Emails**: Financial alerts and general notifications
- **PDF Report Emails**: Monthly reports with attachments
- **Billing Emails**: Invoice and payment notifications

### 📱 SMS Notifications via Twilio
- **Basic SMS**: Standard text message delivery
- **Template-based SMS**: Pre-configured message templates
- **Critical Alerts**: High-priority financial alerts
- **Phone Number Validation**: E.164 format validation
- **Opt-in/Opt-out Handling**: TCPA compliance

### 🎨 Email Template Rendering
- **Personalization**: Dynamic content based on user data
- **HTML Content**: Professional email templates
- **Cultural Context**: African American professional focus
- **Responsive Design**: Mobile-friendly email layouts

### 🔄 Communication Routing
- **Intelligent Routing**: Channel selection based on message type and urgency
- **User Engagement**: Routing based on user activity levels
- **Cultural Personalization**: Age and income-based routing decisions
- **Fallback Mechanisms**: Automatic channel switching on failures

### 📊 Delivery Success Rates
- **SMS Tracking**: Twilio delivery status monitoring
- **Email Success Rates**: Resend delivery analytics
- **Cost Tracking**: Per-message cost monitoring
- **Performance Metrics**: Response time and throughput

### ⚠️ Error Handling
- **Invalid Inputs**: Graceful handling of bad email/phone numbers
- **Service Failures**: Fallback mechanisms when APIs are unavailable
- **Rate Limiting**: Proper handling of API limits
- **Retry Logic**: Automatic retry with exponential backoff

### 👤 User Preferences
- **Opt-in Management**: SMS and email consent handling
- **Help Requests**: Support message processing
- **Weekly Check-ins**: Interactive SMS responses
- **Preference Updates**: Real-time preference changes

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements-communication-testing.txt

# Or use the test runner
python run_communication_tests.py --install-deps
```

### 2. Set Environment Variables

```bash
# Required for actual API testing
export RESEND_API_KEY="your_resend_api_key"
export TWILIO_ACCOUNT_SID="your_twilio_account_sid"
export TWILIO_AUTH_TOKEN="your_twilio_auth_token"
export TWILIO_PHONE_NUMBER="+1234567890"

# Test configuration
export TEST_EMAIL="your_test_email@example.com"
export TEST_PHONE="+1234567890"
```

### 3. Run All Tests

```bash
# Run complete test suite
python run_communication_tests.py

# Or run the test file directly
python test_communication_features.py
```

## 🎛️ Test Options

### Run Specific Test Categories

```bash
# Email tests only
python run_communication_tests.py --test-type email

# SMS tests only
python run_communication_tests.py --test-type sms

# Routing tests only
python run_communication_tests.py --test-type routing

# Integration tests only
python run_communication_tests.py --test-type integration

# Performance tests only
python run_communication_tests.py --test-type performance
```

### Additional Options

```bash
# Verbose output
python run_communication_tests.py --verbose

# Don't save detailed report
python run_communication_tests.py --no-report

# Setup environment variables
python run_communication_tests.py --setup-env

# Install dependencies first
python run_communication_tests.py --install-deps
```

## 📊 Test Results

### Report Structure

The test suite generates comprehensive reports including:

```json
{
  "summary": {
    "total_tests": 25,
    "successful_tests": 23,
    "failed_tests": 2,
    "overall_success_rate": 92.0,
    "total_duration_seconds": 45.23,
    "average_duration_per_test": 1.81
  },
  "category_breakdown": {
    "Email Delivery": {
      "success_rate": 100.0,
      "total": 4,
      "successful": 4,
      "failed": 0
    },
    "SMS Notifications": {
      "success_rate": 87.5,
      "total": 4,
      "successful": 3,
      "failed": 1
    }
  },
  "failed_tests": [
    {
      "test_name": "Critical Alert SMS",
      "error": "Twilio API error: Invalid phone number",
      "details": {...}
    }
  ]
}
```

### Success Criteria

- **Email Delivery**: 95%+ success rate
- **SMS Delivery**: 90%+ success rate
- **Routing Accuracy**: 100% correct channel selection
- **Error Handling**: Graceful failure handling
- **Performance**: <2 seconds average per test

## 🔧 Configuration

### Test Configuration

```python
# In test_communication_features.py
class CommunicationFeaturesTestSuite:
    def __init__(self):
        self.test_email = os.getenv('TEST_EMAIL', 'test@example.com')
        self.test_phone = os.getenv('TEST_PHONE', '+1234567890')
        self.test_user_id = "test_user_123"
```

### Service Configuration

```python
# Resend Email Service
RESEND_API_KEY = "your_api_key"
RESEND_FROM_EMAIL = "noreply@mingusapp.com"
RESEND_FROM_NAME = "MINGUS Financial Wellness"

# Twilio SMS Service
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE_NUMBER = "+1234567890"
```

## 🧪 Individual Test Details

### Email Delivery Tests

```python
def test_email_delivery(self):
    # Welcome Email
    result = self.email_service.send_welcome_email(
        user_email=self.test_email,
        user_name="Test User"
    )
    
    # Password Reset Email
    result = self.email_service.send_password_reset_email(
        user_email=self.test_email,
        reset_token="test_token"
    )
    
    # Notification Email
    result = self.email_service.send_notification_email(
        user_email=self.test_email,
        subject="Test Alert",
        message="Test message",
        notification_type="alert"
    )
    
    # PDF Report Email
    result = self.email_service.send_pdf_report_email(
        user_email=self.test_email,
        user_name="Test User",
        report_type="monthly",
        pdf_url="https://example.com/report.pdf"
    )
```

### SMS Notification Tests

```python
def test_sms_notifications(self):
    # Basic SMS
    result = self.sms_service.send_sms(
        phone_number=self.test_phone,
        message="Test SMS message",
        priority_level=SMSPriority.MEDIUM
    )
    
    # Template-based SMS
    result = self.sms_service.send_sms(
        phone_number=self.test_phone,
        template_name="low_balance_warning",
        template_vars={'balance': '150.00'},
        priority_level=SMSPriority.URGENT
    )
    
    # Critical Alert
    result = self.sms_service.send_sms(
        phone_number=self.test_phone,
        message="🚨 CRITICAL: Payment failed",
        priority_level=SMSPriority.CRITICAL
    )
```

### Communication Routing Tests

```python
def test_communication_routing(self):
    # Create test message
    message = CommunicationMessage(
        message_id="test_001",
        user_id=self.test_user_id,
        message_type=MessageType.FINANCIAL_ALERT,
        urgency_level=UrgencyLevel.CRITICAL,
        content={'alert_type': 'low_balance'}
    )
    
    # Create user profile
    user_profile = UserProfile(
        user_id=self.test_user_id,
        email=self.test_email,
        phone_number=self.test_phone,
        engagement_level=UserEngagementLevel.MEDIUM
    )
    
    # Route message
    routing_decision = self.router.route_message(message, user_profile)
    
    # Verify routing decision
    assert routing_decision.channel.value == 'sms'
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: Resend API key not configured
   Solution: Set RESEND_API_KEY environment variable
   ```

2. **Phone Number Validation**
   ```
   Error: Invalid phone number format
   Solution: Use E.164 format (+1234567890)
   ```

3. **Redis Connection**
   ```
   Error: Redis connection failed
   Solution: Start Redis server or use mock mode
   ```

4. **Import Errors**
   ```
   Error: No module named 'backend.services'
   Solution: Ensure backend directory is in Python path
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_communication_tests.py --verbose
```

### Mock Mode

```bash
# Use mock services instead of real APIs
export MOCK_EXTERNAL_APIS=true
python run_communication_tests.py
```

## 📈 Performance Testing

### Load Testing

```bash
# Run performance tests
python run_communication_tests.py --test-type performance
```

### Benchmark Results

Expected performance metrics:

- **Email Delivery**: <1 second per email
- **SMS Delivery**: <2 seconds per SMS
- **Routing Decision**: <100ms per decision
- **Template Rendering**: <50ms per template

## 🔒 Security Testing

### Data Protection

- **PII Handling**: Test data anonymization
- **API Security**: Secure credential management
- **Rate Limiting**: Prevent API abuse
- **Opt-out Compliance**: TCPA compliance testing

### Compliance Testing

```python
def test_tcpa_compliance(self):
    # Test opt-out handling
    opt_out_result = self.sms_service.handle_opt_out_responses({
        'From': '+1234567890',
        'Body': 'STOP'
    })
    
    # Verify opt-out processing
    assert opt_out_result['action'] == 'opted_out'
```

## 📝 Continuous Integration

### GitHub Actions

```yaml
name: Communication Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements-communication-testing.txt
      - name: Run tests
        run: python run_communication_tests.py
        env:
          MOCK_EXTERNAL_APIS: true
```

## 📚 Additional Resources

- [Resend API Documentation](https://resend.com/docs)
- [Twilio SMS API Documentation](https://www.twilio.com/docs/sms)
- [TCPA Compliance Guide](https://www.fcc.gov/consumers/guides/telephone-consumer-protection-act-tcpa)
- [Email Template Best Practices](https://www.litmus.com/blog/email-design-best-practices/)

## 🤝 Contributing

To add new tests:

1. Create test method in `CommunicationFeaturesTestSuite`
2. Add test to appropriate category
3. Update test runner options if needed
4. Add documentation for new test type
5. Update requirements if new dependencies needed

## 📞 Support

For issues with the test suite:

1. Check the troubleshooting section
2. Review the detailed test report
3. Enable debug logging
4. Contact the development team

---

**Last Updated**: August 27, 2025  
**Version**: 1.0.0  
**Maintainer**: MINGUS Development Team
