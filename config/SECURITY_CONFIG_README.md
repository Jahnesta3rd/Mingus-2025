# Security Configuration Management System

## Overview

The Security Configuration Management System provides centralized, secure configuration management for all security systems across the MINGUS application. It includes environment-specific settings, validation, policy management, and comprehensive documentation.

## Architecture

### Core Components

1. **SecurityConfigurationManager** - Main configuration manager class
2. **Validation Rules** - Configurable validation for security-critical values
3. **Security Policies** - Environment-specific security requirements
4. **Configuration Validation** - Automatic validation on startup
5. **Environment Management** - Support for dev/staging/production/testing

### Security Levels

- **CRITICAL** - Application secrets, encryption keys
- **HIGH** - Database connections, API keys
- **MEDIUM** - CORS settings, session configuration
- **LOW** - General application settings

## File Structure

```
config/
├── security_config.py          # Main security configuration system
├── SECURITY_CONFIG_README.md   # This documentation
├── development.py              # Development environment config
├── production.py               # Production environment config
├── testing.py                  # Testing environment config
└── staging.py                  # Staging environment config

docker/
└── security.env.template       # Environment variables template
```

## Usage

### Basic Usage

```python
from config.security_config import get_security_config

# Get global security configuration
security_config = get_security_config()

# Access configuration values
secret_key = security_config.get('SECRET_KEY')
debug_mode = security_config.get('DEBUG', False)

# Get all configuration
all_config = security_config.get_all()

# Get security summary
summary = security_config.get_security_summary()
```

### Initialization

```python
from config.security_config import init_security_config

# Initialize with specific environment
security_config = init_security_config('production')

# Initialize with current environment
security_config = init_security_config()
```

### Configuration Updates

```python
# Update configuration values (with validation)
security_config.update('SESSION_COOKIE_SECURE', True)

# Export configuration (optionally excluding secrets)
export_config = security_config.export_config(include_secrets=False)
```

## Environment Configuration

### Development Environment

- Basic validation enabled
- Warnings for weak configurations
- Local development overrides allowed
- Debug mode enabled
- Insecure cookies allowed

### Staging Environment

- Enhanced validation
- Production-like security settings
- Testing of security features
- Audit logging enabled
- Rate limiting enabled

### Production Environment

- Strict validation required
- All security features enabled
- HTTPS required
- Secure cookies required
- Audit logging required
- Critical security violations block startup

### Testing Environment

- Minimal validation
- Test-specific configurations
- Mock security components
- Fast startup for testing

## Security Policies

### Production Security Policy

- All secrets must be at least 32 characters
- HTTPS must be enabled
- Secure cookies must be enabled
- Audit logging must be enabled
- Rate limiting must be enabled

### Development Security Policy

- Basic validation enabled
- Warnings for weak configurations
- Local development overrides allowed

### Testing Security Policy

- Minimal validation
- Test-specific configurations allowed
- Mock security components enabled

## Validation Rules

### Built-in Validators

- **SECRET_KEY**: Minimum 32 characters, alphanumeric + special chars
- **DATABASE_URL**: Valid database connection format
- **JWT_SECRET_KEY**: Minimum 32 characters, secure format
- **ENCRYPTION_KEY**: Minimum 32 characters, secure format
- **CORS_ORIGINS**: Valid URL format
- **SESSION_COOKIE_SECURE**: Boolean values only
- **SESSION_COOKIE_HTTPONLY**: Boolean values only

### Custom Validators

```python
def custom_validator(value):
    # Custom validation logic
    return True

# Add custom validation rule
validation_rule = ValidationRule(
    custom_validator=custom_validator,
    description="Custom validation rule"
)
```

## Environment Variables

### Required Variables

- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key
- `ENCRYPTION_KEY` - Data encryption key
- `DATABASE_URL` - Database connection string

### Optional Variables

- `CORS_ORIGINS` - Allowed CORS origins
- `SESSION_COOKIE_SECURE` - Secure session cookies
- `RATE_LIMIT_ENABLED` - Enable rate limiting
- `CSRF_ENABLED` - Enable CSRF protection
- `AUDIT_LOGGING_ENABLED` - Enable audit logging

## Security Features

### Rate Limiting

- API rate limits: 100 per minute
- Web rate limits: 1000 per minute
- Login rate limits: 5 per 15 minutes
- Registration rate limits: 3 per hour

### Session Security

- Configurable session lifetime
- Maximum sessions per user
- Session timeout and idle timeout
- Remember me functionality
- Secure cookie settings

### Authentication Security

- Password policy enforcement
- MFA requirements
- Login attempt limits
- Account lockout protection
- Verification rate limits

### Security Headers

- Content Security Policy (CSP)
- Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer Policy
- Permissions Policy

## Deployment

### Development Deployment

1. Copy `docker/security.env.template` to `docker/security.env`
2. Fill in development values
3. Set `FLASK_ENV=development`
4. Start application

### Production Deployment

1. Copy `docker/security.env.template` to `docker/security.env`
2. Generate strong, unique secrets
3. Set `FLASK_ENV=production`
4. Verify all security requirements met
5. Deploy with HTTPS enabled
6. Monitor security logs

### Environment Variable Generation

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Monitoring and Logging

### Security Logs

- Configuration validation results
- Security policy violations
- Startup warnings and errors
- Configuration changes

### Audit Logging

- User authentication events
- Security policy changes
- Configuration modifications
- Access control events

### Monitoring

- Security configuration status
- Policy compliance
- Validation failures
- Critical security warnings

## Best Practices

### Configuration Management

1. **Never commit secrets** to version control
2. **Use environment-specific** configurations
3. **Validate all configuration** before deployment
4. **Rotate secrets regularly** in production
5. **Monitor configuration changes** and security events

### Security Hardening

1. **Enable all security features** in production
2. **Use HTTPS everywhere** in production
3. **Implement strong password policies**
4. **Enable MFA** for sensitive operations
5. **Monitor and log** all security events

### Development Workflow

1. **Use template files** for environment configuration
2. **Test security features** in staging environment
3. **Validate configuration** before deployment
4. **Document security decisions** and configurations
5. **Regular security reviews** of configuration

## Troubleshooting

### Common Issues

#### Configuration Validation Failed

```python
# Check validation errors
try:
    security_config._validate_configuration()
except ConfigValidationError as e:
    print(f"Validation failed: {e}")
```

#### Security Policy Violations

```python
# Check policy compliance
compliance = security_config.validate_security_policy("Production Security")
if not compliance:
    print("Production security policy violations detected")
```

#### Environment Configuration Issues

```python
# Check environment configuration
environment = security_config.environment
config_file = f"config/{environment.value}.py"
print(f"Loading config from: {config_file}")
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('config.security_config').setLevel(logging.DEBUG)

# Check configuration summary
summary = security_config.get_security_summary()
print(f"Security summary: {summary}")
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets are at least 32 characters
- [ ] Environment variables are properly set
- [ ] Security configuration is validated
- [ ] Security policies are compliant
- [ ] HTTPS is enabled (production)
- [ ] Secure cookies are enabled (production)
- [ ] Audit logging is enabled (production)

### Post-Deployment

- [ ] Security monitoring is active
- [ ] Security logs are being generated
- [ ] Rate limiting is working
- [ ] CSRF protection is active
- [ ] Security headers are present
- [ ] Session security is enforced

### Regular Maintenance

- [ ] Secrets are rotated regularly
- [ ] Security policies are reviewed
- [ ] Configuration is audited
- [ ] Security logs are monitored
- [ ] Updates are applied promptly
- [ ] Security incidents are documented

## Support and Maintenance

### Documentation Updates

- Keep this README updated with configuration changes
- Document new security features and policies
- Update deployment procedures as needed

### Security Reviews

- Regular security configuration reviews
- Policy compliance audits
- Configuration validation testing
- Security feature testing

### Incident Response

- Document security incidents
- Update configuration based on lessons learned
- Review and update security policies
- Implement additional security measures as needed

## Contributing

### Adding New Security Features

1. Update `SecurityConfigurationManager` class
2. Add validation rules if needed
3. Update security policies
4. Add environment variable support
5. Update documentation
6. Add tests

### Configuration Changes

1. Update relevant configuration files
2. Add validation rules
3. Update security policies
4. Test in all environments
5. Update documentation
6. Deploy with proper testing

## License

This security configuration system is part of the MINGUS application and follows the same licensing terms.
