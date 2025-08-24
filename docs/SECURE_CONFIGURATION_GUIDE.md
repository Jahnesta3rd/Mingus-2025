# Secure Configuration Management Guide for MINGUS Application

## Overview

The MINGUS application implements a comprehensive secure configuration management system that eliminates all hard-coded secrets and provides enterprise-grade security features. This system ensures that sensitive configuration data is properly managed, validated, and protected throughout the application lifecycle.

## Features

### 🔐 Security Features
- **Environment Variable Validation**: Comprehensive validation of all configuration values
- **Secret Rotation**: Automated secret rotation with backup functionality
- **Configuration Encryption**: Optional encryption of sensitive configuration values
- **Audit Logging**: Complete audit trail of configuration access and changes
- **Security Level Classification**: Different security levels for different types of configuration
- **Weak Secret Detection**: Automatic detection of weak or compromised secrets

### 🛡️ Protection Features
- **No Hard-coded Secrets**: Complete elimination of hard-coded secrets in code
- **Environment-specific Configuration**: Separate configurations for development, testing, and production
- **External Service Integration**: Secure management of API keys and credentials
- **Database Security**: Encrypted database connections and credentials
- **SSL/TLS Enforcement**: Automatic SSL redirect and security headers

### 🔍 Validation Features
- **Comprehensive Validation**: Validation of all configuration values
- **Pattern Matching**: Regex-based validation for URLs, keys, and other patterns
- **Type Checking**: Automatic type conversion and validation
- **Dependency Validation**: Validation of external service dependencies
- **Performance Validation**: Validation of performance-related settings

## Architecture

### Core Components

1. **SecureConfigManager** (`config/secure_config.py`)
   - Main configuration management class
   - Handles loading, validation, and access to configuration
   - Provides encryption and audit logging

2. **Validation Rules** (`config/secure_config.py`)
   - Defines validation rules for each configuration key
   - Specifies security levels and requirements
   - Provides pattern matching and type validation

3. **Environment Template** (`env.template`)
   - Comprehensive template with all required variables
   - Detailed documentation for each variable
   - Security best practices and warnings

4. **Configuration Classes** (`config/base.py`, `config/production.py`, etc.)
   - Environment-specific configuration classes
   - Integration with secure configuration manager
   - Feature flags and environment detection

### Security Levels

- **CRITICAL**: Highest security level (e.g., encryption keys, API secrets)
- **HIGH**: High security level (e.g., database passwords, service tokens)
- **MEDIUM**: Medium security level (e.g., configuration flags, URLs)
- **LOW**: Low security level (e.g., feature flags, display settings)

## Setup Instructions

### 1. Initial Setup

```bash
# Run the setup script
python scripts/setup_secure_config.py

# Or run in automatic mode
python scripts/setup_secure_config.py --auto
```

The setup script will:
- Create environment file from template
- Generate secure secrets
- Validate configuration
- Provide setup instructions

### 2. Environment File Configuration

Copy the template and configure your values:

```bash
# Copy template to environment file
cp env.template .env

# Edit the environment file
nano .env
```

### 3. Required Configuration

#### Flask Configuration
```bash
# Flask secret key (auto-generated)
SECRET_KEY=your-secret-key-change-in-production

# Environment
FLASK_ENV=development

# Debug mode (false in production)
DEBUG=false
```

#### Database Configuration
```bash
# Database connection URL
DATABASE_URL=postgresql://username:password@host:port/database

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

#### Encryption Keys
```bash
# Field-level encryption key (auto-generated)
FIELD_ENCRYPTION_KEY=your-field-encryption-key-here

# Django secret key (auto-generated)
DJANGO_SECRET_KEY=your-django-secret-key-here
```

#### External Services
```bash
# Stripe configuration
STRIPE_ENVIRONMENT=test
STRIPE_TEST_SECRET_KEY=sk_test_your_test_secret_key
STRIPE_LIVE_SECRET_KEY=sk_live_your_live_secret_key

# Plaid configuration
PLAID_ENVIRONMENT=sandbox
PLAID_SANDBOX_CLIENT_ID=your_sandbox_client_id
PLAID_SANDBOX_SECRET=your_sandbox_secret

# Email configuration
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_resend_api_key

# SMS configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

## Usage

### Basic Configuration Access

```python
from config.secure_config import get_secure_config

# Get configuration manager
config = get_secure_config()

# Get configuration values
secret_key = config.get('SECRET_KEY')
database_url = config.get('DATABASE_URL')
debug_mode = config.get('DEBUG', 'false').lower() == 'true'
```

### Environment Detection

```python
from config.secure_config import is_production, is_development, is_testing

if is_production():
    # Production-specific code
    pass
elif is_development():
    # Development-specific code
    pass
```

### Configuration Validation

```python
from config.secure_config import get_secure_config

config = get_secure_config()
validation_results = config.validate_environment()

if validation_results['valid']:
    print("Configuration is valid")
else:
    print("Configuration validation failed:")
    for error in validation_results['errors']:
        print(f"  - {error}")
```

### Secret Rotation

```python
from config.secure_config import get_secure_config

config = get_secure_config()

# Rotate a specific secret
new_secret = config.rotate_secret('SECRET_KEY')

# Get audit log
audit_log = config.get_audit_log()
```

## Scripts

### Configuration Validation

```bash
# Basic validation
python scripts/validate_config.py

# Verbose validation with detailed output
python scripts/validate_config.py --verbose

# Validate specific environment file
python scripts/validate_config.py --env-file .env.production

# Generate missing secrets
python scripts/validate_config.py --fix

# Output results to file
python scripts/validate_config.py --output validation_results.json
```

### Secret Rotation

```bash
# Show rotation status
python scripts/rotate_secrets.py --status

# Rotate weak secrets only
python scripts/rotate_secrets.py

# Rotate all secrets
python scripts/rotate_secrets.py --all

# Rotate specific secrets
python scripts/rotate_secrets.py --secrets SECRET_KEY,FIELD_ENCRYPTION_KEY

# Force rotation of strong secrets
python scripts/rotate_secrets.py --force

# Create backup before rotation
python scripts/rotate_secrets.py --backup

# Dry run (show what would be rotated)
python scripts/rotate_secrets.py --dry-run
```

### Setup and Maintenance

```bash
# Initial setup
python scripts/setup_secure_config.py

# Automatic setup
python scripts/setup_secure_config.py --auto

# Setup with specific environment file
python scripts/setup_secure_config.py --env-file .env.production
```

## Security Best Practices

### 1. Environment File Security

- **Never commit .env files to version control**
- Use `.gitignore` to exclude environment files
- Store environment files securely
- Use different files for different environments

### 2. Secret Management

- **Generate strong, unique secrets**
- Rotate secrets regularly (every 90 days)
- Use different secrets for different environments
- Store secrets securely (e.g., AWS Secrets Manager, Azure Key Vault)

### 3. Production Security

- **Enable SSL/TLS in production**
- Use strong encryption keys
- Enable audit logging
- Monitor configuration access
- Regular security audits

### 4. External Service Security

- **Enable 2FA on all external service accounts**
- Use environment-specific API keys
- Monitor API usage and costs
- Regular credential rotation

### 5. Database Security

- **Use encrypted database connections**
- Implement connection pooling
- Regular database backups
- Monitor database access

## Validation Rules

### Required Variables

The following variables are required for all environments:

- `SECRET_KEY`: Flask secret key for session management
- `DATABASE_URL`: Database connection URL
- `FIELD_ENCRYPTION_KEY`: Field-level encryption key
- `DJANGO_SECRET_KEY`: Django secret key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key

### Pattern Validation

- **Database URLs**: Must match `^(postgresql|sqlite)://.*`
- **Redis URLs**: Must match `^redis://.*`
- **Supabase URLs**: Must match `^https://.*\.supabase\.co$`
- **Stripe Keys**: Must match `^sk_(test|live)_.*` or `^pk_(test|live)_.*`
- **Twilio SID**: Must match `^AC[a-f0-9]{32}$`

### Security Validation

- **Weak Secret Detection**: Identifies common weak patterns
- **Production Security**: Enforces production security settings
- **SSL Enforcement**: Requires SSL in production
- **Debug Mode**: Prevents debug mode in production

## Troubleshooting

### Common Issues

1. **Configuration Validation Fails**
   - Check that all required variables are set
   - Verify variable formats match expected patterns
   - Ensure environment-specific requirements are met

2. **Secret Rotation Fails**
   - Check that secrets exist in configuration
   - Verify backup directory permissions
   - Ensure environment file is writable

3. **Encryption Issues**
   - Verify encryption keys are properly set
   - Check that cryptography package is installed
   - Ensure consistent encryption key usage

4. **External Service Issues**
   - Verify API keys are correct
   - Check service account permissions
   - Ensure proper environment configuration

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug mode in environment file
DEBUG=true

# Run validation with verbose output
python scripts/validate_config.py --verbose

# Check configuration summary
python scripts/validate_config.py --output debug.json
```

## Monitoring and Maintenance

### Regular Tasks

1. **Daily**
   - Monitor configuration access logs
   - Check for configuration errors
   - Verify external service connectivity

2. **Weekly**
   - Review audit logs
   - Check for weak secrets
   - Validate configuration integrity

3. **Monthly**
   - Rotate secrets (if needed)
   - Update dependencies
   - Review security settings

4. **Quarterly**
   - Complete secret rotation
   - Security audit
   - Performance review

### Monitoring Tools

- **Configuration Validation**: `scripts/validate_config.py`
- **Secret Rotation**: `scripts/rotate_secrets.py`
- **Audit Logging**: Built into secure configuration manager
- **Performance Monitoring**: Application monitoring tools

## Integration with CI/CD

### Environment Setup

```yaml
# Example GitHub Actions workflow
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Validate Configuration
        run: |
          python scripts/validate_config.py --env-file .env.production
      
      - name: Deploy
        run: |
          # Deployment steps
```

### Secret Management

```yaml
# Example with GitHub Secrets
- name: Setup Environment
  run: |
    echo "SECRET_KEY=${{ secrets.SECRET_KEY }}" >> .env
    echo "DATABASE_URL=${{ secrets.DATABASE_URL }}" >> .env
    echo "STRIPE_LIVE_SECRET_KEY=${{ secrets.STRIPE_LIVE_SECRET_KEY }}" >> .env
```

## Advanced Features

### Custom Validation Rules

```python
from config.secure_config import ValidationRule, SecurityLevel

# Add custom validation rule
custom_rule = ValidationRule(
    key='CUSTOM_API_KEY',
    required=True,
    min_length=32,
    pattern=r'^custom_[a-f0-9]{32}$',
    security_level=SecurityLevel.HIGH,
    description="Custom API key for external service"
)
```

### Configuration Encryption

```python
from config.secure_config import get_secure_config

config = get_secure_config()

# Set encrypted value
config.set('SENSITIVE_DATA', 'secret_value', encrypt=True)

# Get decrypted value
value = config.get('SENSITIVE_DATA', decrypt=True)
```

### Audit Logging

```python
from config.secure_config import get_secure_config

config = get_secure_config()

# Get audit log
audit_log = config.get_audit_log()

# Process audit entries
for entry in audit_log:
    print(f"{entry['timestamp']} - {entry['action']} - {entry['key']}")
```

## Support and Documentation

### Additional Resources

- **Template Documentation**: See `env.template` for detailed variable descriptions
- **Code Documentation**: Check docstrings in `config/secure_config.py`
- **Validation Scripts**: Review `scripts/validate_config.py` for validation options
- **Rotation Scripts**: See `scripts/rotate_secrets.py` for secret management

### Getting Help

1. **Check the logs**: Review application and validation logs
2. **Run validation**: Use `scripts/validate_config.py --verbose`
3. **Review documentation**: Check this guide and code comments
4. **Test configuration**: Use dry-run options in scripts

### Security Contacts

For security issues or questions:
- Review security documentation
- Check audit logs for suspicious activity
- Contact security team for critical issues
- Follow incident response procedures

---

**Remember**: Security is an ongoing process. Regularly review and update your configuration security practices to maintain the highest level of protection for your MINGUS application. 