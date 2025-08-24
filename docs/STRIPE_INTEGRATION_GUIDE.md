# MINGUS Stripe Integration Guide

## Overview

The MINGUS personal finance application includes a comprehensive Stripe integration for payment processing and subscription management. This guide covers the implementation details, configuration, and usage of the payment system.

## Features

### Subscription Tiers

The application offers three subscription tiers:

#### 1. Budget Tier ($15/month)
- **Price**: $15/month or $144/year (20% discount)
- **Features**:
  - Basic analytics and reporting
  - Goal setting and tracking
  - Email support
  - Mobile app access
  - Data export (2/month)
  - Basic notifications
- **Limits**:
  - 5 analytics reports per month
  - 3 goals per account
  - 3 support requests per month
  - 12 months transaction history

#### 2. Mid-Tier ($35/month)
- **Price**: $35/month or $336/year (20% discount)
- **Features**: All Budget features plus:
  - Advanced AI insights
  - Career risk management
  - Priority support
  - Advanced reports
  - Custom categories
  - Investment tracking
  - Debt optimization
  - Tax planning
- **Limits**:
  - 20 analytics reports per month
  - 10 goals per account
  - 10 support requests per month
  - 36 months transaction history
  - 50 AI insights per month
  - 5 investment accounts
  - 20 custom categories

#### 3. Professional Tier ($75/month)
- **Price**: $75/month or $720/year (20% discount)
- **Features**: All Mid-Tier features plus:
  - Unlimited access to all features
  - Dedicated account manager
  - Team management (up to 10 members)
  - White-label reports
  - API access
  - Custom integrations
  - Priority feature requests
  - Phone support
  - Onboarding call
- **Limits**:
  - Unlimited usage for most features
  - 10 team members
  - 10,000 API requests per month

## Architecture

### File Structure

```
backend/
├── payment/
│   ├── __init__.py                 # Payment package initialization
│   ├── stripe_integration.py       # Main Stripe service
│   └── payment_models.py           # Payment-related models and enums
├── routes/
│   └── payment.py                  # Payment API endpoints
└── config/
    └── base.py                     # Stripe configuration settings
```

### Core Components

#### 1. StripeService (`backend/payment/stripe_integration.py`)

The main service class that handles all Stripe operations:

- **Customer Management**: Create, retrieve, and update Stripe customers
- **Subscription Management**: Create, update, and cancel subscriptions
- **Payment Processing**: Handle payment intents and one-time payments
- **Billing Management**: Manage invoices and payment methods
- **Webhook Handling**: Process Stripe webhook events

#### 2. Payment Models (`backend/payment/payment_models.py`)

Data models and enums for payment-related entities:

- `PaymentStatus`: Payment status enumeration
- `SubscriptionStatus`: Subscription status enumeration
- `SubscriptionTier`: MINGUS subscription tiers
- `PaymentError`: Error handling for payment operations
- `Customer`, `Subscription`, `Invoice`, `PaymentMethod`: Data classes

#### 3. Payment Routes (`backend/routes/payment.py`)

RESTful API endpoints for payment operations:

- Customer management endpoints
- Subscription creation and management
- Payment processing endpoints
- Webhook handling
- Billing and invoice management

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Configuration
STRIPE_API_VERSION=2023-10-16
STRIPE_DEBUG=false
STRIPE_CURRENCY=usd

# Stripe Price IDs (configure in Stripe Dashboard)
STRIPE_BUDGET_MONTHLY_PRICE_ID=price_...
STRIPE_BUDGET_YEARLY_PRICE_ID=price_...
STRIPE_MID_TIER_MONTHLY_PRICE_ID=price_...
STRIPE_MID_TIER_YEARLY_PRICE_ID=price_...
STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID=price_...
STRIPE_PROFESSIONAL_YEARLY_PRICE_ID=price_...

# Stripe Settings
STRIPE_TRIAL_DAYS=7
STRIPE_GRACE_PERIOD_DAYS=3
STRIPE_ENABLE_3D_SECURE=true
STRIPE_AUTOMATIC_TAX_ENABLED=false
```

### Stripe Dashboard Setup

1. **Create Products and Prices**:
   - Create three products in Stripe Dashboard: "Budget Tier", "Mid-Tier", "Professional Tier"
   - For each product, create monthly and yearly recurring prices
   - Copy the price IDs to your environment variables

2. **Configure Webhooks**:
   - Create a webhook endpoint in Stripe Dashboard
   - Set the endpoint URL to: `https://yourdomain.com/api/payment/webhooks/stripe`
   - Select the following events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
   - Copy the webhook secret to your environment variables

3. **Configure Payment Methods**:
   - Enable the payment methods you want to support (card, bank account, etc.)
   - Configure 3D Secure settings
   - Set up automatic payment methods

## API Endpoints

### Customer Management

#### Create Customer
```http
POST /api/payment/customers
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "+1234567890",
  "metadata": {"user_id": "uuid"}
}
```

#### Get Customer
```http
GET /api/payment/customers/me
```

#### Update Customer
```http
PUT /api/payment/customers/me
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "+1234567890"
}
```

### Subscription Management

#### Get Subscription Tiers
```http
GET /api/payment/subscriptions/tiers
```

#### Create Subscription
```http
POST /api/payment/subscriptions
Content-Type: application/json

{
  "tier": "budget",
  "billing_cycle": "monthly",
  "trial_days": 7,
  "payment_method_id": "pm_xxx"
}
```

#### Get Subscriptions
```http
GET /api/payment/subscriptions/me
```

#### Update Subscription
```http
PUT /api/payment/subscriptions/{subscription_id}
Content-Type: application/json

{
  "tier": "mid_tier",
  "billing_cycle": "yearly"
}
```

#### Cancel Subscription
```http
POST /api/payment/subscriptions/{subscription_id}/cancel
Content-Type: application/json

{
  "at_period_end": true
}
```

### Payment Processing

#### Create Payment Intent
```http
POST /api/payment/payment-intents
Content-Type: application/json

{
  "amount": 1500,
  "currency": "usd",
  "description": "Payment for premium features"
}
```

#### Get Payment Methods
```http
GET /api/payment/payment-methods
```

#### Attach Payment Method
```http
POST /api/payment/payment-methods
Content-Type: application/json

{
  "payment_method_id": "pm_xxx"
}
```

#### Detach Payment Method
```http
DELETE /api/payment/payment-methods/{payment_method_id}
```

### Billing Management

#### Get Invoices
```http
GET /api/payment/invoices?limit=10
```

#### Get Invoice
```http
GET /api/payment/invoices/{invoice_id}
```

### Utility Endpoints

#### Get Payment Config
```http
GET /api/payment/config
```

#### Calculate Proration
```http
POST /api/payment/proration
Content-Type: application/json

{
  "subscription_id": "sub_xxx",
  "new_price_id": "price_xxx"
}
```

## Usage Examples

### Python Usage

```python
from backend.payment.stripe_integration import StripeService, SubscriptionTier

# Initialize service
stripe_service = StripeService()

# Create a customer
customer = stripe_service.create_customer(
    email="user@example.com",
    name="John Doe",
    metadata={"user_id": "uuid"}
)

# Create a subscription
subscription = stripe_service.create_subscription(
    customer_id=customer.id,
    tier=SubscriptionTier.MID_TIER,
    billing_cycle="monthly",
    trial_days=7
)

# Get subscription information
tier_info = stripe_service.get_subscription_tier_info(SubscriptionTier.PROFESSIONAL)
print(f"Professional tier price: ${tier_info.price_monthly / 100}/month")
```

### JavaScript/Client-Side Usage

```javascript
// Load Stripe
const stripe = Stripe('pk_test_...');

// Create payment intent
const response = await fetch('/api/payment/payment-intents', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    amount: 1500,
    currency: 'usd',
    description: 'Payment for premium features'
  })
});

const { payment_intent } = await response.json();

// Confirm payment
const result = await stripe.confirmCardPayment(payment_intent.client_secret, {
  payment_method: {
    card: elements.getElement('card'),
    billing_details: {
      name: 'John Doe',
    },
  }
});

if (result.error) {
  console.error(result.error);
} else {
  console.log('Payment succeeded!');
}
```

## Webhook Handling

The application automatically handles Stripe webhook events to keep the system in sync:

### Supported Events

- `customer.subscription.created`: New subscription created
- `customer.subscription.updated`: Subscription updated
- `customer.subscription.deleted`: Subscription cancelled
- `invoice.payment_succeeded`: Payment successful
- `invoice.payment_failed`: Payment failed
- `payment_intent.succeeded`: One-time payment successful
- `payment_intent.payment_failed`: One-time payment failed

### Webhook Processing

```python
# Webhook endpoint automatically processes events
@payment_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    event = stripe_service.handle_webhook(payload, signature)
    
    # Event is automatically processed based on type
    return jsonify({'success': True})
```

## Security Features

### 1. API Key Protection
- Stripe secret keys are stored in environment variables
- Never exposed to client-side code
- Rotated regularly for security

### 2. Webhook Verification
- All webhooks are verified using Stripe signatures
- Prevents replay attacks and unauthorized requests
- Secure webhook secret management

### 3. Customer Isolation
- Each user has their own Stripe customer
- Payment methods are isolated per customer
- Subscription access is verified per user

### 4. Input Validation
- All API inputs are validated
- Amount limits and currency validation
- Subscription tier validation

### 5. Error Handling
- Comprehensive error handling for all Stripe operations
- Secure error messages (no sensitive data exposed)
- Detailed logging for debugging

## Testing

### Test Environment

1. **Use Stripe Test Keys**:
   - Use `sk_test_...` and `pk_test_...` keys for development
   - Test webhooks using Stripe CLI

2. **Test Cards**:
   - Use Stripe test card numbers for testing
   - Test various scenarios (success, failure, 3D Secure)

3. **Webhook Testing**:
   ```bash
   # Install Stripe CLI
   stripe listen --forward-to localhost:5002/api/payment/webhooks/stripe
   ```

### Test Scenarios

1. **Subscription Creation**:
   - Create subscription with trial
   - Create subscription without trial
   - Test different tiers and billing cycles

2. **Payment Processing**:
   - Successful payments
   - Failed payments
   - 3D Secure authentication

3. **Subscription Management**:
   - Upgrade/downgrade subscriptions
   - Cancel subscriptions
   - Proration calculations

4. **Webhook Events**:
   - Test all webhook event types
   - Verify event processing
   - Check database updates

## Monitoring and Logging

### Logging

The application logs all payment-related activities:

```python
logger.info(f"Created subscription {subscription.id} for user {user.id}")
logger.error(f"Failed to create payment intent: {e}")
```

### Monitoring

Monitor the following metrics:

1. **Payment Success Rate**: Track successful vs failed payments
2. **Subscription Metrics**: Active subscriptions, churn rate
3. **Revenue Metrics**: Monthly recurring revenue (MRR)
4. **Error Rates**: Payment failures, webhook errors

### Alerts

Set up alerts for:

- High payment failure rates
- Webhook processing errors
- Subscription cancellations
- Revenue anomalies

## Troubleshooting

### Common Issues

1. **Webhook Failures**:
   - Check webhook endpoint URL
   - Verify webhook secret
   - Check server logs for errors

2. **Payment Failures**:
   - Verify payment method is valid
   - Check 3D Secure configuration
   - Review Stripe dashboard for errors

3. **Subscription Issues**:
   - Verify price IDs are correct
   - Check customer exists in Stripe
   - Review subscription status

### Debug Mode

Enable debug mode for detailed logging:

```bash
STRIPE_DEBUG=true
```

### Support

For Stripe-specific issues:
- Check [Stripe Documentation](https://stripe.com/docs)
- Review [Stripe Support](https://support.stripe.com)
- Use Stripe CLI for local testing

## Migration Guide

### From Existing Payment System

1. **Data Migration**:
   - Export existing subscription data
   - Create Stripe customers for existing users
   - Migrate subscription data to Stripe

2. **API Migration**:
   - Update client code to use new endpoints
   - Test all payment flows
   - Verify webhook handling

3. **Configuration**:
   - Set up Stripe products and prices
   - Configure webhooks
   - Update environment variables

### Rollback Plan

1. **Keep Existing System**:
   - Maintain existing payment system during transition
   - Run both systems in parallel
   - Gradual migration of users

2. **Monitoring**:
   - Monitor both systems during migration
   - Track payment success rates
   - Verify data consistency

## Future Enhancements

### Planned Features

1. **Advanced Billing**:
   - Usage-based billing
   - Custom pricing tiers
   - Volume discounts

2. **Payment Methods**:
   - ACH payments
   - International payment methods
   - Digital wallets

3. **Analytics**:
   - Revenue analytics
   - Churn analysis
   - Customer lifetime value

4. **Automation**:
   - Automated dunning management
   - Smart retry logic
   - Proactive customer outreach

### Integration Opportunities

1. **Accounting Systems**:
   - QuickBooks integration
   - Xero integration
   - Automated reconciliation

2. **CRM Integration**:
   - Salesforce integration
   - HubSpot integration
   - Customer journey tracking

3. **Analytics Platforms**:
   - Google Analytics
   - Mixpanel
   - Amplitude

## Conclusion

The MINGUS Stripe integration provides a robust, secure, and scalable payment processing solution. With comprehensive subscription management, flexible billing options, and extensive security features, it supports the application's growth and provides a excellent user experience.

For questions or support, refer to the Stripe documentation or contact the development team. 