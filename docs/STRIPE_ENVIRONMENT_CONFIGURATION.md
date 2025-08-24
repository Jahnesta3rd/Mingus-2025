# MINGUS Stripe Environment Configuration Guide

## Overview

This guide covers the comprehensive environment configuration for the MINGUS Stripe integration, including development and production environments, webhook setup, and error handling.

## Environment Configuration

### 1. Environment Variables

The Stripe integration supports both test and live environments with separate configuration for each.

#### Test Environment Variables

```bash
# Stripe Environment
STRIPE_ENVIRONMENT=test

# Test API Keys
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLISHABLE_KEY=pk_test_...
STRIPE_TEST_WEBHOOK_SECRET=whsec_...

# Test Webhook Endpoint
STRIPE_TEST_WEBHOOK_ENDPOINT=https://your-test-domain.com/api/payment/webhooks/stripe

# Test Price IDs (configure in Stripe Dashboard)
STRIPE_TEST_BUDGET_MONTHLY_PRICE_ID=price_...
STRIPE_TEST_BUDGET_YEARLY_PRICE_ID=price_...
STRIPE_TEST_MID_TIER_MONTHLY_PRICE_ID=price_...
STRIPE_TEST_MID_TIER_YEARLY_PRICE_ID=price_...
STRIPE_TEST_PROFESSIONAL_MONTHLY_PRICE_ID=price_...
STRIPE_TEST_PROFESSIONAL_YEARLY_PRICE_ID=price_...

# Test Settings
STRIPE_TEST_CURRENCY=usd
STRIPE_TEST_TRIAL_DAYS=7
STRIPE_TEST_GRACE_PERIOD_DAYS=3
STRIPE_TEST_LOG_LEVEL=DEBUG
STRIPE_TEST_DEBUG=true
```

#### Live Environment Variables

```bash
# Stripe Environment
STRIPE_ENVIRONMENT=live

# Live API Keys
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_PUBLISHABLE_KEY=pk_live_...
STRIPE_LIVE_WEBHOOK_SECRET=whsec_...

# Live Webhook Endpoint
STRIPE_LIVE_WEBHOOK_ENDPOINT=https://your-live-domain.com/api/payment/webhooks/stripe

# Live Price IDs (configure in Stripe Dashboard)
STRIPE_LIVE_BUDGET_MONTHLY_PRICE_ID=price_...
STRIPE_LIVE_BUDGET_YEARLY_PRICE_ID=price_...
STRIPE_LIVE_MID_TIER_MONTHLY_PRICE_ID=price_...
STRIPE_LIVE_MID_TIER_YEARLY_PRICE_ID=price_...
STRIPE_LIVE_PROFESSIONAL_MONTHLY_PRICE_ID=price_...
STRIPE_LIVE_PROFESSIONAL_YEARLY_PRICE_ID=price_...

# Live Settings
STRIPE_LIVE_CURRENCY=usd
STRIPE_LIVE_TRIAL_DAYS=7
STRIPE_LIVE_GRACE_PERIOD_DAYS=3
STRIPE_LIVE_LOG_LEVEL=INFO
STRIPE_LIVE_DEBUG=false
```

### 2. Environment Switching

The system automatically detects the environment based on the `STRIPE_ENVIRONMENT` variable:

```python
from backend.config.stripe import get_stripe_config

# Get configuration for current environment
config = get_stripe_config()

print(f"Current environment: {config.environment}")
print(f"Is test mode: {config.is_test_mode}")
print(f"Is live mode: {config.is_live_mode}")
```

### 3. Configuration Validation

Validate your configuration using the built-in validation:

```python
from backend.config.stripe import validate_stripe_environment

# Validate configuration
validation = validate_stripe_environment()

if validation['is_configured']:
    print("✅ Stripe is properly configured")
else:
    print("❌ Missing configuration:")
    for missing in validation['missing_configuration']:
        print(f"  - {missing}")

# Check for warnings
for warning in validation['warnings']:
    print(f"⚠️  {warning}")
```

## Webhook Configuration

### 1. Webhook Endpoint Setup

#### Test Environment
1. Go to Stripe Dashboard → Webhooks
2. Click "Add endpoint"
3. Set endpoint URL: `https://your-test-domain.com/api/payment/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.created`
   - `customer.updated`
   - `customer.deleted`
   - `payment_method.attached`
   - `payment_method.detached`
   - `invoice.created`
   - `invoice.finalized`
   - `invoice.payment_action_required`
5. Copy the webhook secret to `STRIPE_TEST_WEBHOOK_SECRET`

#### Live Environment
1. Go to Stripe Dashboard → Webhooks
2. Click "Add endpoint"
3. Set endpoint URL: `https://your-live-domain.com/api/payment/webhooks/stripe`
4. Select the same events as test environment
5. Copy the webhook secret to `STRIPE_LIVE_WEBHOOK_SECRET`

### 2. Webhook Testing

#### Using Stripe CLI (Recommended)

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Listen for webhooks (test mode)
stripe listen --forward-to localhost:5002/api/payment/webhooks/stripe

# Trigger test events
stripe trigger customer.subscription.created
stripe trigger invoice.payment_succeeded
```

#### Manual Testing

```bash
# Test webhook endpoint
curl -X POST http://localhost:5002/api/payment/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: whsec_..." \
  -d '{"type":"test.event","data":{"object":{}}}'
```

### 3. Webhook Security

The system includes comprehensive webhook security:

```python
# Automatic signature verification
if not webhook_config.validate_webhook_signature(payload, signature):
    raise stripe.error.SignatureVerificationError("Invalid signature")

# Event type validation
if not webhook_config.is_supported_event(event['type']):
    logger.warning(f"Unsupported event: {event['type']}")
```

## Error Handling and Logging

### 1. Logging Configuration

The system provides comprehensive logging for all Stripe operations:

#### Log Files
- Test environment: `logs/stripe_test.log`
- Live environment: `logs/stripe_live.log`

#### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about operations
- **WARNING**: Potential issues
- **ERROR**: Errors that need attention

### 2. Error Handling

#### Structured Error Logging

```python
# All Stripe errors are logged with context
error_handler.log_error(error, {
    'operation': 'create_subscription',
    'customer_id': customer_id,
    'tier': tier.value,
    'billing_cycle': billing_cycle
})
```

#### Error Types Handled

1. **API Errors**: Invalid API keys, rate limits
2. **Payment Errors**: Card declined, insufficient funds
3. **Webhook Errors**: Invalid signatures, unsupported events
4. **Configuration Errors**: Missing environment variables
5. **Network Errors**: Connection timeouts, DNS failures

### 3. Monitoring and Alerts

#### Key Metrics to Monitor

1. **Payment Success Rate**
   ```python
   # Track successful vs failed payments
   success_rate = successful_payments / total_payments
   ```

2. **Webhook Processing**
   ```python
   # Monitor webhook delivery and processing
   webhook_success_rate = processed_webhooks / received_webhooks
   ```

3. **Error Rates**
   ```python
   # Track error frequency by type
   error_rate = errors_per_hour / total_operations_per_hour
   ```

#### Alert Setup

```python
# Example alert configuration
ALERTS = {
    'payment_failure_rate': {
        'threshold': 0.05,  # 5%
        'window': '1h',
        'action': 'email_admin'
    },
    'webhook_failure_rate': {
        'threshold': 0.01,  # 1%
        'window': '1h',
        'action': 'email_admin'
    },
    'api_error_rate': {
        'threshold': 0.02,  # 2%
        'window': '15m',
        'action': 'email_admin'
    }
}
```

## Production Deployment

### 1. Environment Setup

#### Step 1: Configure Environment Variables
```bash
# Set environment to live
export STRIPE_ENVIRONMENT=live

# Configure live API keys
export STRIPE_LIVE_SECRET_KEY=sk_live_...
export STRIPE_LIVE_PUBLISHABLE_KEY=pk_live_...

# Configure webhook
export STRIPE_LIVE_WEBHOOK_SECRET=whsec_...
export STRIPE_LIVE_WEBHOOK_ENDPOINT=https://your-domain.com/api/payment/webhooks/stripe
```

#### Step 2: Create Products and Prices
1. Go to Stripe Dashboard → Products
2. Create three products:
   - "Budget Tier"
   - "Mid-Tier"
   - "Professional Tier"
3. For each product, create monthly and yearly prices
4. Copy price IDs to environment variables

#### Step 3: Configure Webhooks
1. Create webhook endpoint in Stripe Dashboard
2. Select all required events
3. Copy webhook secret to environment variable

### 2. Security Considerations

#### API Key Security
```bash
# Never commit API keys to version control
echo "STRIPE_LIVE_SECRET_KEY=sk_live_..." >> .env
echo ".env" >> .gitignore
```

#### Webhook Security
```python
# Verify webhook signatures
if not webhook_config.validate_webhook_signature(payload, signature):
    return jsonify({'error': 'Invalid signature'}), 400
```

#### Environment Isolation
```python
# Ensure test and live environments are completely separate
if config.is_live_mode:
    # Additional security checks for live mode
    assert config.webhook_endpoint.startswith('https://')
    assert config.api_key.startswith('sk_live_')
```

### 3. Monitoring Setup

#### Log Monitoring
```bash
# Monitor Stripe logs
tail -f logs/stripe_live.log | grep ERROR

# Set up log rotation
logrotate /etc/logrotate.d/stripe
```

#### Health Checks
```python
# Health check endpoint
@app.route('/health/stripe')
def stripe_health_check():
    try:
        validation = validate_stripe_environment()
        if validation['is_configured']:
            return jsonify({'status': 'healthy'}), 200
        else:
            return jsonify({'status': 'unhealthy', 'issues': validation['missing_configuration']}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

## Testing

### 1. Unit Tests

```python
# Test configuration loading
def test_test_environment_config():
    config = StripeConfig('test')
    assert config.is_test_mode is True
    assert config.is_live_mode is False

# Test webhook validation
def test_webhook_signature_validation():
    webhook_config = StripeWebhookConfig(config)
    assert webhook_config.is_supported_event('customer.subscription.created')
    assert not webhook_config.is_supported_event('unsupported.event')
```

### 2. Integration Tests

```python
# Test end-to-end payment flow
def test_payment_flow():
    # Create customer
    customer = stripe_service.create_customer(email="test@example.com")
    
    # Create subscription
    subscription = stripe_service.create_subscription(
        customer_id=customer.id,
        tier=SubscriptionTier.BUDGET,
        billing_cycle="monthly"
    )
    
    # Verify subscription
    assert subscription.status == SubscriptionStatus.ACTIVE
```

### 3. Webhook Testing

```python
# Test webhook processing
def test_webhook_processing():
    # Create test webhook payload
    payload = create_test_webhook_payload('customer.subscription.created')
    signature = create_test_signature(payload, webhook_secret)
    
    # Process webhook
    event = stripe_service.handle_webhook(payload, signature)
    
    # Verify event processing
    assert event['type'] == 'customer.subscription.created'
```

## Troubleshooting

### 1. Common Issues

#### Configuration Issues
```bash
# Check configuration
python -c "from backend.config.stripe import validate_stripe_environment; print(validate_stripe_environment())"
```

#### Webhook Issues
```bash
# Check webhook logs
tail -f logs/stripe_test.log | grep webhook

# Test webhook endpoint
curl -X POST http://localhost:5002/api/payment/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

#### API Issues
```bash
# Test API connection
python -c "import stripe; stripe.api_key='sk_test_...'; print(stripe.Customer.list(limit=1))"
```

### 2. Debug Mode

Enable debug mode for detailed logging:

```bash
# Test environment
export STRIPE_TEST_DEBUG=true
export STRIPE_TEST_LOG_LEVEL=DEBUG

# Live environment (use with caution)
export STRIPE_LIVE_DEBUG=true
export STRIPE_LIVE_LOG_LEVEL=DEBUG
```

### 3. Support Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Support](https://support.stripe.com)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Stripe Webhook Testing](https://stripe.com/docs/webhooks/test)

## Best Practices

### 1. Environment Management

- Always use test environment for development
- Never use live API keys in development
- Use environment variables for all configuration
- Validate configuration before deployment

### 2. Security

- Rotate API keys regularly
- Use webhook signature verification
- Monitor for suspicious activity
- Implement rate limiting

### 3. Monitoring

- Set up comprehensive logging
- Monitor payment success rates
- Track webhook delivery
- Set up alerts for critical issues

### 4. Testing

- Test all payment flows in test environment
- Use Stripe test cards for testing
- Test webhook processing
- Validate error handling

This configuration guide ensures a robust, secure, and well-monitored Stripe integration for the MINGUS application. 