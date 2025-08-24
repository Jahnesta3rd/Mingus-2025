# Plaid Environment Configuration Guide for MINGUS

## 🎯 Overview

This guide provides comprehensive instructions for configuring Plaid integration across different environments in the MINGUS application. It covers development/sandbox setup, production configuration, and webhook management for real-time updates.

## 📋 Table of Contents

1. [Environment Overview](#environment-overview)
2. [Development/Sandbox Setup](#developmentsandbox-setup)
3. [Production Setup](#production-setup)
4. [Webhook Configuration](#webhook-configuration)
5. [Security Considerations](#security-considerations)
6. [Testing and Validation](#testing-and-validation)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## 🏗️ Environment Overview

### Environment Types

1. **Development/Sandbox Environment**
   - Used for testing and development
   - Uses Plaid's sandbox API
   - Simulated bank data and transactions
   - No real financial data

2. **Production Environment**
   - Used for live applications
   - Uses Plaid's production API
   - Real bank data and transactions
   - Strict security requirements

### Configuration Files

- `config/plaid_config.py` - Main configuration management
- `config/environments/development.env.example` - Development environment template
- `config/environments/production.env.example` - Production environment template
- `scripts/setup_plaid_config.py` - Automated setup script

## 🔧 Development/Sandbox Setup

### Prerequisites

1. **Plaid Account**: Sign up at [plaid.com](https://plaid.com)
2. **Sandbox Access**: Get sandbox credentials from Plaid Dashboard
3. **Local Development Environment**: Python, PostgreSQL, ngrok (for webhooks)

### Step 1: Automated Setup

Run the automated setup script:

```bash
# Interactive setup for development environment
python scripts/setup_plaid_config.py --environment development --interactive

# Non-interactive setup (creates template files)
python scripts/setup_plaid_config.py --environment development
```

### Step 2: Manual Configuration

If you prefer manual setup, copy the example file:

```bash
cp config/environments/development.env.example config/environments/development.env
```

Edit the file with your credentials:

```bash
# Plaid Sandbox Configuration
PLAID_ENV=sandbox
PLAID_SANDBOX_CLIENT_ID=your_sandbox_client_id
PLAID_SANDBOX_SECRET=your_sandbox_secret

# Webhook Configuration
PLAID_SANDBOX_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/api/plaid/webhook
PLAID_SANDBOX_WEBHOOK_SECRET=your_webhook_secret

# Redirect URI
PLAID_SANDBOX_REDIRECT_URI=http://localhost:5000/plaid/callback
```

### Step 3: Local Webhook Testing with ngrok

For local webhook testing:

```bash
# Install ngrok
# Download from https://ngrok.com/

# Start ngrok
ngrok http 5000

# Use the HTTPS URL as your webhook URL
# Example: https://abc123.ngrok.io/api/plaid/webhook
```

### Step 4: Environment Validation

Validate your development configuration:

```bash
python scripts/setup_plaid_config.py --validate --environment development
```

## 🚀 Production Setup

### Prerequisites

1. **Production Plaid Account**: Upgrade to production access
2. **SSL Certificate**: Valid SSL certificate for your domain
3. **Production Server**: Deployed application with HTTPS
4. **Security Review**: Complete security assessment

### Step 1: Automated Setup

```bash
# Interactive setup for production environment
python scripts/setup_plaid_config.py --environment production --interactive

# Non-interactive setup
python scripts/setup_plaid_config.py --environment production
```

### Step 2: Manual Configuration

Copy and configure the production template:

```bash
cp config/environments/production.env.example config/environments/production.env
```

Configure production settings:

```bash
# Plaid Production Configuration
PLAID_ENV=production
PLAID_PRODUCTION_CLIENT_ID=your_production_client_id
PLAID_PRODUCTION_SECRET=your_production_secret

# Production Webhook (MUST use HTTPS)
PLAID_PRODUCTION_WEBHOOK_URL=https://your-domain.com/api/plaid/webhook
PLAID_PRODUCTION_WEBHOOK_SECRET=your_production_webhook_secret

# Production Redirect URI (MUST use HTTPS)
PLAID_PRODUCTION_REDIRECT_URI=https://your-domain.com/plaid/callback

# Security (REQUIRED for production)
PLAID_PRODUCTION_ENCRYPTION_KEY=your_encryption_key
```

### Step 3: Security Configuration

Ensure all security settings are properly configured:

```bash
# HTTPS Enforcement
HTTPS_ENFORCED=True
HSTS_ENABLED=True

# Session Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

### Step 4: Production Validation

```bash
python scripts/setup_plaid_config.py --validate --environment production
```

## 🔗 Webhook Configuration

### Webhook Events

The following webhook events are configured:

| Event | Description | Environment |
|-------|-------------|-------------|
| `TRANSACTIONS_INITIAL_UPDATE` | Initial transaction sync | Both |
| `TRANSACTIONS_HISTORICAL_UPDATE` | Historical transaction sync | Both |
| `TRANSACTIONS_DEFAULT_UPDATE` | Regular transaction updates | Both |
| `TRANSACTIONS_REMOVED` | Transaction removals | Both |
| `ITEM_LOGIN_REQUIRED` | Re-authentication required | Both |
| `ITEM_ERROR` | Item errors | Both |
| `ACCOUNT_UPDATED` | Account information updates | Production |
| `ACCOUNT_AVAILABLE_BALANCE_UPDATED` | Balance updates | Production |

### Webhook Security

1. **Signature Verification**: All webhooks are verified using HMAC-SHA256
2. **HTTPS Enforcement**: Production webhooks must use HTTPS
3. **Rate Limiting**: Webhook endpoints are rate-limited
4. **Error Handling**: Comprehensive error handling and logging

### Webhook Setup

```bash
# Set up webhook verification
python scripts/setup_plaid_config.py --webhook-setup --environment production
```

### Webhook Testing

Test webhook delivery:

```bash
# Test webhook endpoint
curl -X POST https://your-domain.com/api/plaid/webhook \
  -H "Content-Type: application/json" \
  -H "Plaid-Verification: v0=test_signature" \
  -d '{
    "webhook_type": "TRANSACTIONS",
    "webhook_code": "TRANSACTIONS_DEFAULT_UPDATE",
    "item_id": "test_item_id",
    "environment": "production",
    "timestamp": "2025-01-27T00:00:00Z",
    "new_transactions": 0
  }'
```

## 🔒 Security Considerations

### Development Environment

1. **No Real Data**: Sandbox environment uses simulated data
2. **Local Testing**: Webhooks can use HTTP for local testing
3. **Basic Security**: Minimal security requirements
4. **Debug Mode**: Detailed logging enabled

### Production Environment

1. **Real Financial Data**: Strict security requirements
2. **HTTPS Only**: All communications must use HTTPS
3. **Encryption**: Access tokens must be encrypted
4. **Audit Logging**: Complete audit trail required
5. **Rate Limiting**: API rate limiting enforced
6. **Monitoring**: Real-time monitoring and alerting

### Security Checklist

- [ ] HTTPS enforced for all production URLs
- [ ] Webhook signature verification enabled
- [ ] Access tokens encrypted at rest
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Error handling implemented
- [ ] Monitoring and alerting set up
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Session security enabled

## 🧪 Testing and Validation

### Environment Validation

```bash
# Validate development environment
python scripts/setup_plaid_config.py --validate --environment development

# Validate production environment
python scripts/setup_plaid_config.py --validate --environment production

# Validate both environments
python scripts/setup_plaid_config.py --validate --environment both
```

### API Connection Testing

The setup script automatically tests:

1. **Plaid API Connection**: Verifies credentials and API access
2. **Webhook Endpoint**: Tests webhook URL accessibility
3. **Configuration Validation**: Validates all required settings

### Manual Testing

```python
# Test Plaid configuration
from config.plaid_config import get_plaid_config, validate_plaid_config

# Get configuration
config = get_plaid_config()

# Validate configuration
is_valid = validate_plaid_config()

if is_valid:
    print("✅ Configuration is valid")
else:
    print("❌ Configuration is invalid")
```

### Webhook Testing

```python
# Test webhook handler
from backend.webhooks.plaid_webhooks import PlaidWebhookHandler

# Create test event
test_event = {
    "webhook_type": "TRANSACTIONS",
    "webhook_code": "TRANSACTIONS_DEFAULT_UPDATE",
    "item_id": "test_item_id",
    "environment": "sandbox",
    "timestamp": "2025-01-27T00:00:00Z",
    "new_transactions": 0
}

# Test webhook processing
handler = PlaidWebhookHandler(db_session)
result = handler.handle_webhook(test_event)
print(f"Webhook result: {result}")
```

## 🔧 Troubleshooting

### Common Issues

1. **Invalid Credentials**
   ```
   Error: Plaid API connection test failed
   Solution: Verify your Plaid credentials in the environment file
   ```

2. **Webhook URL Not Accessible**
   ```
   Error: Webhook endpoint test failed
   Solution: Ensure webhook URL is publicly accessible and uses HTTPS (production)
   ```

3. **Missing Environment Variables**
   ```
   Error: Configuration validation failed
   Solution: Check all required environment variables are set
   ```

4. **Signature Verification Failed**
   ```
   Error: Invalid webhook signature
   Solution: Verify webhook secret is correctly configured
   ```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variables
export PLAID_DEBUG_MODE=True
export PLAID_VERBOSE_LOGGING=True
export LOG_LEVEL=DEBUG
```

### Log Analysis

Check logs for webhook processing:

```bash
# View application logs
tail -f logs/application.log | grep plaid

# View webhook logs
tail -f logs/webhook.log
```

## 📚 Best Practices

### Development

1. **Use Sandbox Environment**: Always test with sandbox first
2. **Local Webhook Testing**: Use ngrok for local webhook testing
3. **Version Control**: Never commit real credentials to version control
4. **Environment Separation**: Keep development and production configurations separate
5. **Regular Testing**: Test webhook processing regularly

### Production

1. **Security First**: Implement all security measures before deployment
2. **Monitoring**: Set up comprehensive monitoring and alerting
3. **Backup Strategy**: Implement proper backup and recovery procedures
4. **Documentation**: Maintain up-to-date documentation
5. **Regular Updates**: Keep dependencies and security patches updated

### Webhook Management

1. **Idempotency**: Ensure webhook processing is idempotent
2. **Error Handling**: Implement proper error handling and retry logic
3. **Rate Limiting**: Configure appropriate rate limits
4. **Monitoring**: Monitor webhook delivery and processing
5. **Testing**: Regularly test webhook functionality

### Configuration Management

1. **Environment Variables**: Use environment variables for all sensitive data
2. **Validation**: Validate configuration on startup
3. **Documentation**: Document all configuration options
4. **Version Control**: Version control configuration templates
5. **Secrets Management**: Use proper secrets management in production

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations run
- [ ] Webhook endpoints tested
- [ ] Security review completed
- [ ] Monitoring configured
- [ ] Backup procedures tested

### Post-Deployment

- [ ] Webhook delivery verified
- [ ] API connections tested
- [ ] Error monitoring active
- [ ] Performance monitoring active
- [ ] Security monitoring active
- [ ] Documentation updated
- [ ] Team trained on new features

## 📞 Support

For additional support:

1. **Plaid Documentation**: [https://plaid.com/docs/](https://plaid.com/docs/)
2. **Plaid Support**: [https://support.plaid.com/](https://support.plaid.com/)
3. **MINGUS Documentation**: Check the main documentation repository
4. **Configuration Issues**: Review this guide and troubleshooting section

## 📄 License

This configuration guide is part of the MINGUS application and follows the same licensing terms.

---

**Note**: This guide provides comprehensive instructions for configuring Plaid integration across different environments. Always follow security best practices and test thoroughly before deploying to production. 