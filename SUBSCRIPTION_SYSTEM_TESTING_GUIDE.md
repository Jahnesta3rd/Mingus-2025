# MINGUS Subscription System Testing Guide

## 🎯 Overview

This guide provides comprehensive testing procedures for the MINGUS three-tier subscription system:

- **Budget Tier**: $15/month
- **Mid-Tier**: $35/month  
- **Professional Tier**: $100/month

## 📋 Test Coverage Areas

### 1. Subscription Signup Process
- [x] Budget tier signup flow
- [x] Mid-tier signup flow
- [x] Professional tier signup flow
- [x] Payment method validation
- [x] Customer creation
- [x] Subscription activation

### 2. Payment Processing & Confirmation
- [x] Payment intent creation
- [x] Payment confirmation
- [x] Payment status tracking
- [x] Payment method attachment
- [x] Payment confirmation webhooks

### 3. Subscription Management
- [x] Tier upgrades (Budget → Mid → Professional)
- [x] Tier downgrades (Professional → Mid → Budget)
- [x] Subscription cancellation
- [x] Billing cycle management
- [x] Proration handling

### 4. Payment Failure Handling
- [x] Declined card scenarios
- [x] Insufficient funds
- [x] Expired cards
- [x] Retry logic
- [x] Payment failure notifications
- [x] Grace period handling

### 5. Invoice Generation & Delivery
- [x] Invoice creation
- [x] PDF generation
- [x] Email delivery
- [x] Invoice history
- [x] Tax calculation
- [x] Receipt generation

### 6. Webhook Event Handling
- [x] Subscription created events
- [x] Subscription updated events
- [x] Subscription cancelled events
- [x] Payment succeeded events
- [x] Payment failed events
- [x] Invoice events

### 7. Security & Compliance
- [x] Webhook signature verification
- [x] Payment method validation
- [x] Customer data encryption
- [x] PCI compliance
- [x] Data protection
- [x] Audit logging

## 🚀 Running the Tests

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements-subscription-testing.txt
   ```

2. **Environment Setup**
   ```bash
   export STRIPE_TEST_KEY="sk_test_..."
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   export MINGUS_API_URL="http://localhost:5000"
   ```

### Test Execution

#### Run All Tests
```bash
python run_subscription_tests.py --tier all --category all --verbose --save-results
```

#### Test Specific Tier
```bash
# Test Budget tier only
python run_subscription_tests.py --tier budget --category all

# Test Mid-tier only
python run_subscription_tests.py --tier mid --category all

# Test Professional tier only
python run_subscription_tests.py --tier professional --category all
```

#### Test Specific Categories
```bash
# Test signup processes only
python run_subscription_tests.py --category signup

# Test payment processing only
python run_subscription_tests.py --category payment

# Test webhook handling only
python run_subscription_tests.py --category webhook

# Test security features only
python run_subscription_tests.py --category security
```

#### Generate Reports Only
```bash
python run_subscription_tests.py --report-only --results-file subscription_test_results_20250127_143022.json
```

## 📊 Expected Test Results

### Success Criteria

| Category | Minimum Success Rate | Target Success Rate |
|----------|---------------------|-------------------|
| Signup Process | 95% | 100% |
| Payment Processing | 98% | 100% |
| Subscription Management | 95% | 100% |
| Payment Failure Handling | 90% | 95% |
| Invoice Generation | 95% | 100% |
| Webhook Handling | 98% | 100% |
| Security & Compliance | 100% | 100% |

### Overall System Readiness

- **95%+ Success Rate**: Ready for production
- **90-94% Success Rate**: Ready with minor fixes
- **80-89% Success Rate**: Needs improvements
- **<80% Success Rate**: Not ready for production

## 🔍 Detailed Test Scenarios

### Budget Tier ($15/month) Tests

#### Signup Flow
1. **Customer Creation**
   - Valid email and name
   - Stripe customer ID generation
   - Database record creation

2. **Payment Method Setup**
   - Valid card information
   - Payment method attachment
   - Default payment method setting

3. **Subscription Creation**
   - Budget tier selection
   - $15.00 monthly pricing
   - Active subscription status
   - Billing cycle setup

#### Feature Access
- Basic analytics (5 reports/month)
- Goal setting (3 goals)
- Email support (3 requests/month)
- Data export (2/month)
- 12-month transaction history

### Mid-Tier ($35/month) Tests

#### Signup Flow
1. **Enhanced Customer Setup**
   - Additional metadata
   - Priority support flag
   - Advanced features enabled

2. **Subscription Features**
   - $35.00 monthly pricing
   - Advanced AI insights (50/month)
   - Career risk management (unlimited)
   - Custom categories (20)

#### Feature Access
- Advanced analytics (20 reports/month)
- AI insights (50/month)
- Career risk management (unlimited)
- Investment tracking (5 accounts)
- Priority support (10 requests/month)

### Professional Tier ($100/month) Tests

#### Signup Flow
1. **Premium Customer Setup**
   - Dedicated account manager assignment
   - Team management capabilities
   - API access provisioning

2. **Unlimited Features**
   - $100.00 monthly pricing
   - Unlimited access to all features
   - Team management (10 members)
   - API access (10,000 requests/month)

#### Feature Access
- Unlimited analytics reports
- Unlimited AI insights
- Team management (10 members)
- API access (10,000 requests/month)
- White-label reports
- Custom integrations

## 🔄 Subscription Management Tests

### Upgrade Scenarios

#### Budget → Mid-Tier
- **Price Change**: +$20.00/month
- **Proration**: Applied for current period
- **Feature Activation**: Immediate access to new features
- **Billing Update**: Next invoice reflects new pricing

#### Mid-Tier → Professional
- **Price Change**: +$65.00/month
- **Proration**: Applied for current period
- **Feature Activation**: Immediate access to unlimited features
- **Team Setup**: Account manager assignment

### Downgrade Scenarios

#### Professional → Mid-Tier
- **Price Change**: -$65.00/month
- **Effective Date**: Next billing cycle
- **Feature Limitation**: Graceful degradation
- **Data Preservation**: User data maintained

#### Mid-Tier → Budget
- **Price Change**: -$20.00/month
- **Effective Date**: Next billing cycle
- **Feature Limitation**: Basic features only
- **Data Export**: Option to export premium data

## 💳 Payment Processing Tests

### Successful Payments
1. **Payment Intent Creation**
   - Correct amount calculation
   - Currency validation
   - Customer association

2. **Payment Confirmation**
   - Status update to 'succeeded'
   - Invoice generation
   - Receipt delivery

3. **Webhook Processing**
   - Event verification
   - Database updates
   - Notification sending

### Failed Payments
1. **Declined Card**
   - Error code identification
   - User notification
   - Retry mechanism

2. **Insufficient Funds**
   - Grace period activation
   - Retry scheduling
   - Account status update

3. **Expired Card**
   - Payment method update prompt
   - Subscription status management
   - Customer communication

## 🔗 Webhook Testing

### Event Types Tested

#### Subscription Events
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.trial_will_end`

#### Payment Events
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

#### Customer Events
- `customer.created`
- `customer.updated`
- `customer.deleted`

### Webhook Security
- **Signature Verification**: All webhooks verified
- **Event Idempotency**: Duplicate events handled
- **Error Handling**: Failed webhooks logged
- **Retry Logic**: Automatic retry for failures

## 🔒 Security Testing

### Payment Security
- **PCI Compliance**: All payment data encrypted
- **Tokenization**: Sensitive data tokenized
- **Access Control**: Role-based permissions
- **Audit Logging**: All actions logged

### Data Protection
- **Encryption**: Data encrypted at rest and in transit
- **Access Logs**: All data access logged
- **Data Retention**: Compliance with retention policies
- **GDPR Compliance**: User data rights respected

### Webhook Security
- **Signature Verification**: HMAC verification
- **IP Whitelisting**: Stripe IPs only
- **Rate Limiting**: Prevent abuse
- **Event Validation**: Payload validation

## 📈 Performance Testing

### Response Times
- **Payment Processing**: < 5 seconds
- **Webhook Processing**: < 2 seconds
- **Invoice Generation**: < 3 seconds
- **Subscription Updates**: < 2 seconds

### Throughput
- **Concurrent Payments**: 100+ per minute
- **Webhook Processing**: 500+ per minute
- **Invoice Generation**: 200+ per minute

## 🐛 Troubleshooting

### Common Issues

#### Test Failures
1. **Stripe API Errors**
   - Check API key configuration
   - Verify webhook endpoint
   - Confirm test mode enabled

2. **Database Connection Issues**
   - Check database configuration
   - Verify table structure
   - Confirm permissions

3. **Webhook Failures**
   - Check webhook endpoint URL
   - Verify signature secret
   - Confirm event types

#### Performance Issues
1. **Slow Response Times**
   - Check network connectivity
   - Verify Stripe API status
   - Review database queries

2. **High Error Rates**
   - Check error logs
   - Verify configuration
   - Review test data

### Debug Mode
```bash
python run_subscription_tests.py --verbose --tier budget --category signup
```

## 📄 Test Reports

### Report Types
1. **JSON Results**: Detailed test data
2. **Markdown Report**: Human-readable summary
3. **Log Files**: Debug information
4. **Coverage Report**: Code coverage metrics

### Report Location
- **Results**: `subscription_test_results_YYYYMMDD_HHMMSS.json`
- **Reports**: `subscription_test_report_YYYYMMDD_HHMMSS.md`
- **Logs**: `subscription_tests_YYYYMMDD_HHMMSS.log`

## 🎯 Quality Gates

### Pre-Production Checklist
- [ ] All tests passing (95%+ success rate)
- [ ] Security tests 100% passing
- [ ] Performance benchmarks met
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Monitoring configured

### Production Readiness
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Compliance verified
- [ ] Backup procedures tested
- [ ] Rollback plan ready
- [ ] Support team trained

## 📞 Support

For issues with the subscription system tests:

1. **Check Logs**: Review test log files
2. **Verify Configuration**: Confirm environment setup
3. **Run Debug Mode**: Use `--verbose` flag
4. **Contact Team**: Reach out to development team

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Author**: MINGUS Development Team
