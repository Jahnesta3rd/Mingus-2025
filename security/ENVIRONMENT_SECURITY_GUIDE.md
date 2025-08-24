# Environment-Specific Security Configuration Guide

## Overview

This guide provides comprehensive environment-specific security configuration for MINGUS, covering production vs staging vs development environments, environment variable security, secret management, configuration validation, and security policy enforcement.

## 🔒 **Environment Security Features**

### **1. Environment-Specific Configurations**
- **Production Environment**: Maximum security with strict policies
- **Staging Environment**: Enhanced security for testing
- **Development Environment**: Basic security for development
- **Security Level Mapping**: Automatic security level assignment
- **Configuration Validation**: Environment-specific validation rules

### **2. Environment Variable Security**
- **Encrypted Environment Variables**: Secure storage of sensitive data
- **Environment-Specific Variables**: Different configurations per environment
- **Variable Validation**: Automatic validation of environment variables
- **Access Control**: Role-based access to environment variables
- **Audit Logging**: Complete audit trail for variable changes

### **3. Secret Management**
- **Encrypted Secret Storage**: AES-256 encryption for all secrets
- **Environment-Specific Secrets**: Separate secrets per environment
- **Secret Rotation**: Automated secret rotation policies
- **Access Control**: Granular access control for secrets
- **Audit Trail**: Complete audit trail for secret access

### **4. Configuration Validation**
- **Environment Validation**: Automatic validation of environment configurations
- **Policy Enforcement**: Security policy enforcement across environments
- **Compliance Checking**: Automatic compliance validation
- **Error Reporting**: Detailed error reporting for validation failures
- **Auto-Correction**: Automatic correction of common issues

### **5. Security Policy Enforcement**
- **Password Policies**: Environment-specific password requirements
- **Session Policies**: Environment-specific session management
- **Rate Limiting**: Environment-specific rate limiting policies
- **Encryption Policies**: Environment-specific encryption requirements
- **Access Control**: Environment-specific access control policies

## 🚀 **Deployment Process**

### **Prerequisites**

1. **Environment Setup**
   - Environment variables configured
   - Base path for security configuration
   - Required tools installed

2. **Environment Variables**
   ```bash
   # Development Environment
   export MINGUS_ENV="development"
   
   # Staging Environment
   export MINGUS_ENV="staging"
   export STAGING_DB_PASSWORD="your_staging_db_password"
   export STAGING_JWT_SECRET="your_staging_jwt_secret"
   
   # Production Environment
   export MINGUS_ENV="production"
   export PROD_DB_PASSWORD="your_prod_db_password"
   export PROD_JWT_SECRET="your_prod_jwt_secret"
   export PROD_API_KEYS="your_prod_api_keys"
   export PROD_ENCRYPTION_KEY="your_prod_encryption_key"
   export PROD_SSL_CERT_PATH="/path/to/ssl/cert"
   export PROD_SSL_KEY_PATH="/path/to/ssl/key"
   ```

3. **Required Tools**
   - Python 3.8+
   - OpenSSL
   - Required Python packages

### **Deployment Commands**

#### **Development Environment**
```bash
python security/deploy_environment_security.py --environment development
```

#### **Staging Environment**
```bash
python security/deploy_environment_security.py --environment staging
```

#### **Production Environment**
```bash
python security/deploy_environment_security.py --environment production
```

## 🔧 **Configuration Details**

### **Environment Configurations**

#### **Development Environment**
```yaml
environment:
  name: "development"
  security_level: "low"
  debug_enabled: true
  logging_level: "DEBUG"
  ssl_required: false
  session_timeout: 3600
  max_login_attempts: 10
  password_min_length: 8
  mfa_required: false
  rate_limiting_enabled: false
  backup_enabled: false
  monitoring_enabled: false
  audit_logging_enabled: false
  encryption_required: false
  allowed_hosts:
    - "localhost"
    - "127.0.0.1"
    - "0.0.0.0"
  cors_origins:
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"
  security_headers:
    X-Content-Type-Options: "nosniff"
    X-Frame-Options: "SAMEORIGIN"
```

#### **Staging Environment**
```yaml
environment:
  name: "staging"
  security_level: "medium"
  debug_enabled: false
  logging_level: "INFO"
  ssl_required: true
  session_timeout: 1800
  max_login_attempts: 5
  password_min_length: 10
  mfa_required: true
  rate_limiting_enabled: true
  backup_enabled: true
  monitoring_enabled: true
  audit_logging_enabled: true
  encryption_required: true
  allowed_hosts:
    - "staging.yourdomain.com"
  cors_origins:
    - "https://staging.yourdomain.com"
  security_headers:
    X-Content-Type-Options: "nosniff"
    X-Frame-Options: "DENY"
    X-XSS-Protection: "1; mode=block"
    Referrer-Policy: "strict-origin-when-cross-origin"
```

#### **Production Environment**
```yaml
environment:
  name: "production"
  security_level: "high"
  debug_enabled: false
  logging_level: "WARNING"
  ssl_required: true
  session_timeout: 900
  max_login_attempts: 3
  password_min_length: 12
  mfa_required: true
  rate_limiting_enabled: true
  backup_enabled: true
  monitoring_enabled: true
  audit_logging_enabled: true
  encryption_required: true
  allowed_hosts:
    - "yourdomain.com"
    - "www.yourdomain.com"
  cors_origins:
    - "https://yourdomain.com"
    - "https://www.yourdomain.com"
  security_headers:
    X-Content-Type-Options: "nosniff"
    X-Frame-Options: "DENY"
    X-XSS-Protection: "1; mode=block"
    Referrer-Policy: "strict-origin-when-cross-origin"
    Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
```

### **Secret Management**

#### **Secret Types**
```yaml
secrets:
  database:
    enabled: true
    secret_id: "db_password_{environment}"
    description: "Database password for {environment} environment"
    type: "database_password"
    expiry_days: 90
  
  jwt:
    enabled: true
    secret_id: "jwt_secret_{environment}"
    description: "JWT secret for {environment} environment"
    type: "jwt_secret"
    expiry_days: 90
  
  api_keys:
    enabled: true
    secret_id: "api_keys_{environment}"
    description: "API keys for {environment} environment"
    type: "api_key"
    expiry_days: 90
  
  encryption:
    enabled: true
    secret_id: "encryption_key_{environment}"
    description: "Encryption key for {environment} environment"
    type: "encryption_key"
    expiry_days: 90
```

#### **Secret Management Commands**
```bash
# Set secret
python -c "
from security.environment_security import set_secret, SecretType, Environment
set_secret('db_password_prod', SecretType.DATABASE_PASSWORD, 'your_password', Environment.PRODUCTION)
"

# Get secret
python -c "
from security.environment_security import get_secret, Environment
password = get_secret('db_password_prod', Environment.PRODUCTION)
print(password)
"
```

### **Security Policies**

#### **Password Policy**
```yaml
password_policy:
  enabled: true
  min_length:
    development: 8
    staging: 10
    production: 12
  require_uppercase:
    development: false
    staging: true
    production: true
  require_lowercase:
    development: true
    staging: true
    production: true
  require_numbers:
    development: true
    staging: true
    production: true
  require_special:
    development: false
    staging: true
    production: true
  max_age_days:
    development: 365
    staging: 90
    production: 60
```

#### **Session Policy**
```yaml
session_policy:
  enabled: true
  timeout_minutes:
    development: 60
    staging: 30
    production: 15
  max_concurrent_sessions:
    development: 5
    staging: 3
    production: 1
  require_secure_cookies:
    development: false
    staging: true
    production: true
  require_https:
    development: false
    staging: true
    production: true
```

#### **Rate Limiting Policy**
```yaml
rate_limiting_policy:
  enabled: true
  requests_per_minute:
    development: 1000
    staging: 100
    production: 50
  burst_limit:
    development: 2000
    staging: 200
    production: 100
  block_duration_minutes:
    development: 5
    staging: 15
    production: 30
```

#### **Encryption Policy**
```yaml
encryption_policy:
  enabled: true
  require_ssl:
    development: false
    staging: true
    production: true
  min_tls_version:
    development: "1.0"
    staging: "1.2"
    production: "1.3"
  require_encryption_at_rest:
    development: false
    staging: true
    production: true
  require_encryption_in_transit:
    development: false
    staging: true
    production: true
```

## 📊 **Security Monitoring**

### **Environment-Specific Monitoring**

#### **Development Monitoring**
```yaml
monitoring:
  enabled: false
  log_level: "DEBUG"
  audit_logging: false
  security_alerts: false
  metrics:
    enabled: false
    interval: 300
    retention_days: 1
```

#### **Staging Monitoring**
```yaml
monitoring:
  enabled: true
  log_level: "INFO"
  audit_logging: true
  security_alerts: true
  metrics:
    enabled: true
    interval: 60
    retention_days: 7
  alerts:
    email: "staging-alerts@yourdomain.com"
    slack: "https://hooks.slack.com/services/your/staging/webhook"
```

#### **Production Monitoring**
```yaml
monitoring:
  enabled: true
  log_level: "WARNING"
  audit_logging: true
  security_alerts: true
  metrics:
    enabled: true
    interval: 30
    retention_days: 30
  alerts:
    email: "security-alerts@yourdomain.com"
    slack: "https://hooks.slack.com/services/your/production/webhook"
    sms: "+1234567890"
```

### **Security Metrics**

#### **Environment Security Scores**
- **Development**: 30-50 points (Basic security)
- **Staging**: 60-80 points (Enhanced security)
- **Production**: 80-100 points (Maximum security)

#### **Security Score Components**
- **Environment Configuration**: 30 points
- **Secrets Management**: 25 points
- **Security Policies**: 25 points
- **Monitoring**: 20 points

## 🔍 **Configuration Validation**

### **Environment Validation Rules**

#### **Development Environment**
- Debug mode enabled
- SSL not required
- MFA not required
- Basic password requirements
- No rate limiting
- No audit logging

#### **Staging Environment**
- Debug mode disabled
- SSL required
- MFA required
- Enhanced password requirements
- Rate limiting enabled
- Audit logging enabled

#### **Production Environment**
- Debug mode disabled
- SSL required with HSTS
- MFA required
- Maximum password requirements
- Strict rate limiting
- Full audit logging
- Encryption required

### **Validation Commands**
```bash
# Validate environment configuration
python -c "
from security.environment_security import validate_environment_security, Environment
errors = validate_environment_security(Environment.PRODUCTION)
for error in errors:
    print(f'ERROR: {error}')
"

# Get environment configuration
python -c "
from security.environment_security import get_environment_config, Environment
config = get_environment_config(Environment.PRODUCTION)
print(f'Security Level: {config.security_level}')
print(f'SSL Required: {config.ssl_required}')
print(f'MFA Required: {config.mfa_required}')
"
```

## 🛡️ **Security Policy Enforcement**

### **Policy Enforcement Examples**

#### **Password Policy Enforcement**
```python
# Validate password against policy
password_data = {
    "password": "MySecurePassword123!",
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True
}

errors = security_manager.validate_security_policy(
    Environment.PRODUCTION, "password_policy", password_data
)

if errors:
    print("Password policy violations:")
    for error in errors:
        print(f"  - {error}")
```

#### **Session Policy Enforcement**
```python
# Validate session configuration
session_data = {
    "timeout_minutes": 15,
    "max_concurrent_sessions": 1,
    "secure_cookies": True,
    "https_enabled": True
}

success = security_manager.enforce_security_policy(
    Environment.PRODUCTION, "session_policy", session_data
)

if success:
    print("Session policy enforced successfully")
else:
    print("Session policy enforcement failed")
```

#### **Rate Limiting Policy Enforcement**
```python
# Validate rate limiting configuration
rate_limit_data = {
    "requests_per_minute": 50,
    "burst_limit": 100,
    "block_duration_minutes": 30
}

success = security_manager.enforce_security_policy(
    Environment.PRODUCTION, "rate_limiting_policy", rate_limit_data
)

if success:
    print("Rate limiting policy enforced successfully")
else:
    print("Rate limiting policy enforcement failed")
```

## 📋 **Security Checklist**

### **Pre-Deployment Checklist**

#### **Development Environment**
- [ ] Environment variables configured
- [ ] Basic security settings applied
- [ ] Debug mode enabled
- [ ] Local development secrets set
- [ ] Basic monitoring configured

#### **Staging Environment**
- [ ] Environment variables configured
- [ ] Enhanced security settings applied
- [ ] SSL certificates configured
- [ ] Staging secrets set
- [ ] MFA configured
- [ ] Monitoring and alerting configured

#### **Production Environment**
- [ ] Environment variables configured
- [ ] Maximum security settings applied
- [ ] SSL certificates with HSTS configured
- [ ] Production secrets set
- [ ] MFA configured
- [ ] Advanced monitoring and alerting configured
- [ ] Backup and disaster recovery configured
- [ ] Security audit completed

### **Post-Deployment Checklist**

#### **All Environments**
- [ ] Environment configuration validated
- [ ] Secrets properly configured
- [ ] Security policies enforced
- [ ] Monitoring working correctly
- [ ] Security tests passed
- [ ] Security report generated

### **Ongoing Maintenance Checklist**

#### **Weekly**
- [ ] Security logs reviewed
- [ ] Environment configurations checked
- [ ] Secret expiration dates verified
- [ ] Policy compliance checked

#### **Monthly**
- [ ] Security policy review
- [ ] Environment configuration audit
- [ ] Secret rotation performed
- [ ] Security score assessment

#### **Quarterly**
- [ ] Security architecture review
- [ ] Policy updates applied
- [ ] Security testing performed
- [ ] Compliance verification

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Environment Configuration Issues**
```bash
# Check environment configuration
python -c "
from security.environment_security import get_environment_config, Environment
config = get_environment_config(Environment.PRODUCTION)
print(f'Configuration: {config}')
"

# Validate environment configuration
python -c "
from security.environment_security import validate_environment_security, Environment
errors = validate_environment_security(Environment.PRODUCTION)
for error in errors:
    print(f'Validation Error: {error}')
"
```

#### **Secret Management Issues**
```bash
# Check secret status
python -c "
from security.environment_security import get_secret, Environment
secret = get_secret('db_password_prod', Environment.PRODUCTION)
if secret:
    print('Secret found')
else:
    print('Secret not found or expired')
"

# List all secrets
python -c "
from security.environment_security import get_environment_security_manager, Environment
manager = get_environment_security_manager()
secrets = manager.secret_manager.list_secrets(Environment.PRODUCTION)
for secret in secrets:
    print(f'Secret: {secret}')
"
```

#### **Policy Enforcement Issues**
```bash
# Check policy status
python -c "
from security.environment_security import get_environment_security_manager, Environment
manager = get_environment_security_manager()
policies = manager.policy_enforcer._get_applicable_policies(Environment.PRODUCTION, 'all')
for policy in policies:
    print(f'Policy: {policy}')
"
```

### **Security Log Analysis**

#### **Environment Security Logs**
```bash
# Check environment security logs
tail -f /var/lib/mingus/security/environment_security.log

# Check secret access logs
tail -f /var/lib/mingus/security/secret_access.log

# Check policy enforcement logs
tail -f /var/lib/mingus/security/policy_enforcement.log
```

## 📚 **Additional Resources**

### **Documentation**
- [Environment Security API Documentation](security/environment_security.py)
- [Secret Management Best Practices](https://docs.aws.amazon.com/secretsmanager/)
- [Security Policy Guidelines](https://owasp.org/www-project-top-ten/)

### **Security Tools**
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Azure Key Vault](https://azure.microsoft.com/services/key-vault/)

### **Monitoring Tools**
- [Prometheus Monitoring](https://prometheus.io/)
- [Grafana Dashboards](https://grafana.com/)
- [ELK Stack Logging](https://www.elastic.co/elk-stack)

## 🎯 **Performance Optimization**

### **Security Performance Impact**

The environment-specific security configuration is optimized for minimal performance impact:

- **Development**: < 1% performance impact
- **Staging**: < 2% performance impact
- **Production**: < 3% performance impact

### **Optimization Recommendations**

1. **Use environment-specific caching** for frequently accessed configurations
2. **Implement lazy loading** for security policies
3. **Optimize secret retrieval** with caching
4. **Use efficient encryption** algorithms
5. **Implement connection pooling** for database access

## 🔄 **Updates and Maintenance**

### **Security Updates**

1. **Automatic Updates**
   - Security patches applied automatically
   - Policy updates applied within 24 hours
   - Secret rotation performed automatically

2. **Manual Updates**
   - Environment configuration changes
   - Security policy modifications
   - Secret management updates

### **Backup and Recovery**

1. **Automated Backups**
   - Environment configurations backed up daily
   - Secrets backed up with encryption
   - Security policies backed up

2. **Recovery Procedures**
   - Environment configuration recovery
   - Secret recovery procedures
   - Policy recovery procedures

---

*This environment security guide ensures that MINGUS maintains appropriate security levels across all environments while providing flexibility for development, testing, and production needs.* 