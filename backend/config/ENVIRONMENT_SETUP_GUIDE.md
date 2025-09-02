# Email Verification System Environment Setup Guide

## 🚀 **Quick Start**

### **1. Generate Secure Secrets**
```bash
# Generate development secret (32 bytes)
python backend/config/validate_config.py --env development --generate-secret

# Generate staging secret (64 bytes)
python backend/config/validate_config.py --env staging --generate-secret

# Generate production secret (64 bytes)
python backend/config/validate_config.py --env production --generate-secret
```

### **2. Copy Environment Templates**
```bash
# Development
cp backend/config/env_templates/env.development.template .env.development

# Staging
cp backend/config/env_templates/env.staging.template .env.staging

# Production
cp backend/config/env.staging.template .env.production
```

### **3. Validate Configuration**
```bash
# Development
python backend/config/validate_config.py --env development

# Staging
python backend/config/validate_config.py --env staging

# Production (strict mode)
python backend/config/validate_config.py --env production --strict
```

## 🔧 **Environment Configuration Files**

### **Development Environment** (`.env.development`)
- **Security**: Relaxed for testing convenience
- **Rate Limiting**: High limits for development
- **Debugging**: Full debug and test modes enabled
- **Mock Services**: Email mocking enabled

### **Staging Environment** (`.env.staging`)
- **Security**: Moderate security settings
- **Rate Limiting**: Balanced limits for testing
- **Debugging**: Limited debugging capabilities
- **Real Services**: Uses actual email service

### **Production Environment** (`.env.production`)
- **Security**: Maximum security settings
- **Rate Limiting**: Strict limits to prevent abuse
- **Debugging**: All debug modes disabled
- **Real Services**: Full production email service

## 🔐 **Critical Security Variables**

### **EMAIL_VERIFICATION_SECRET**
```bash
# CRITICAL: Must be cryptographically secure
# Development: Minimum 32 characters
# Production: Minimum 64 characters

# Generate using Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Or use the validation script
python backend/config/validate_config.py --env production --generate-secret
```

**Security Requirements:**
- ✅ **Never commit to version control**
- ✅ **Unique for each environment**
- ✅ **Randomly generated**
- ✅ **Minimum length: 32 (dev) / 64 (prod) characters**

### **Token Security Settings**
```bash
# Token length in bytes
EMAIL_VERIFICATION_TOKEN_LENGTH=64  # Production: 64, Development: 32

# Token expiration time
EMAIL_VERIFICATION_EXPIRY_HOURS=24

# Maximum token age
EMAIL_VERIFICATION_MAX_TOKEN_AGE_HOURS=48
```

## 🚦 **Rate Limiting Configuration**

### **Development Settings** (Relaxed)
```bash
# High limits for testing
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=50
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=20
EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=10
EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=0  # No cooldown
EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=10
EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=0  # No lockout
```

### **Production Settings** (Strict)
```bash
# Strict limits for security
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=5
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=3
EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=3
EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=2
EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=3
EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=2
```

### **Staging Settings** (Balanced)
```bash
# Moderate limits for testing
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=10
EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=5
EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=5
EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=1
EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=5
EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=1
```

## 📧 **Email Configuration**

### **Service Integration**
```bash
# Email service provider
EMAIL_SERVICE_PROVIDER=resend

# Template directory
EMAIL_TEMPLATE_DIR=backend/templates

# Sender addresses
EMAIL_DEFAULT_FROM=noreply@mingus.app
EMAIL_REPLY_TO=support@mingus.app

# Subject prefix
EMAIL_SUBJECT_PREFIX=Mingus -  # Production
EMAIL_SUBJECT_PREFIX=[STAGING] Mingus -  # Staging
EMAIL_SUBJECT_PREFIX=[DEV] Mingus -  # Development
```

### **Resend Integration**
```bash
# Required: Your Resend API key
RESEND_API_KEY=re_your_actual_api_key_here

# Verify your domain with Resend
# Ensure noreply@mingus.app is verified
```

## ⏰ **Reminder System Configuration**

### **Development** (Fast Testing)
```bash
EMAIL_VERIFICATION_ENABLE_REMINDERS=true
EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS=0,1,2  # Very fast
EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=5
```

### **Staging** (Moderate Testing)
```bash
EMAIL_VERIFICATION_ENABLE_REMINDERS=true
EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS=1,3,7  # Fast
EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=3
```

### **Production** (Conservative)
```bash
EMAIL_VERIFICATION_ENABLE_REMINDERS=true
EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS=7,14  # Conservative
EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=2
```

## 📊 **Audit and Monitoring**

### **Development** (Basic)
```bash
EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING=true
EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS=7
EMAIL_VERIFICATION_ENABLE_MONITORING=false
EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES=60
```

### **Production** (Comprehensive)
```bash
EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING=true
EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS=365
EMAIL_VERIFICATION_ENABLE_MONITORING=true
EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES=5
```

## 🔗 **Integration Configuration**

### **URLs and Endpoints**
```bash
# Development
FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:5000

# Staging
FRONTEND_URL=https://staging.mingus.app
API_BASE_URL=https://api.staging.mingus.app

# Production
FRONTEND_URL=https://mingus.app
API_BASE_URL=https://api.mingus.app
```

### **Service Connections**
```bash
# Redis for rate limiting
REDIS_URL=redis://localhost:6379/0  # Development
REDIS_URL=redis://localhost:6379/1  # Staging
REDIS_URL=redis://your-prod-redis:6379/0  # Production

# Database connection
DATABASE_URL=postgresql://localhost:5432/mingus_dev  # Development
DATABASE_URL=postgresql://localhost:5432/mingus_staging  # Staging
DATABASE_URL=postgresql://your-prod-db:5432/mingus_production  # Production

# Celery broker
CELERY_BROKER_URL=redis://localhost:6379/1  # Development
CELERY_BROKER_URL=redis://localhost:6379/2  # Staging
CELERY_BROKER_URL=redis://your-prod-redis:6379/1  # Production
```

## 🛡️ **Security Configuration**

### **Tracking and Monitoring**
```bash
# Development (Minimal)
EMAIL_VERIFICATION_TRACK_IP_ADDRESSES=false
EMAIL_VERIFICATION_TRACK_USER_AGENTS=false
EMAIL_VERIFICATION_TRACK_GEO_LOCATION=false

# Production (Maximum)
EMAIL_VERIFICATION_TRACK_IP_ADDRESSES=true
EMAIL_VERIFICATION_TRACK_USER_AGENTS=true
EMAIL_VERIFICATION_TRACK_GEO_LOCATION=true
```

### **Session Management**
```bash
# Development (Relaxed)
EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS=10
EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS=48

# Production (Strict)
EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS=2
EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS=12
```

## 🔧 **Development and Testing Settings**

### **Debug Modes**
```bash
# Development only
EMAIL_VERIFICATION_DEBUG=true
EMAIL_VERIFICATION_TEST_MODE=true
EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=true

# Staging and Production
EMAIL_VERIFICATION_DEBUG=false
EMAIL_VERIFICATION_TEST_MODE=false
EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=false
```

### **Test Email Override**
```bash
# Development: Redirect all emails to test address
EMAIL_VERIFICATION_TEST_EMAIL=your-test-email@example.com

# Staging and Production: No override
EMAIL_VERIFICATION_TEST_EMAIL=
```

## 🐳 **Docker Configuration**

### **Environment Variables in Docker**
```bash
# Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.email-verification.yml up -d

# Environment file
docker-compose --env-file .env.development up -d
```

### **Docker Secrets (Production)**
```bash
# Create Docker secrets for sensitive data
echo "your-secret-here" | docker secret create email_verification_secret -

# Use in docker-compose
environment:
  - EMAIL_VERIFICATION_SECRET_FILE=/run/secrets/email_verification_secret
```

## 🔍 **Configuration Validation**

### **Run Validation Scripts**
```bash
# Basic validation
python backend/config/validate_config.py --env development

# Strict validation (treats warnings as errors)
python backend/config/validate_config.py --env production --strict

# Generate secure secrets
python backend/config/validate_config.py --env production --generate-secret
```

### **Validation Checklist**
- ✅ **All required variables set**
- ✅ **Secret length meets requirements**
- ✅ **URLs use HTTPS in production**
- ✅ **Debug modes disabled in production**
- ✅ **Rate limiting appropriately configured**
- ✅ **Email service properly configured**

## 🚨 **Security Checklist**

### **Before Production Deployment**
- [ ] **EMAIL_VERIFICATION_SECRET is 64+ characters**
- [ ] **All URLs use HTTPS**
- [ ] **FLASK_DEBUG=false**
- [ ] **EMAIL_VERIFICATION_DEBUG=false**
- [ ] **EMAIL_VERIFICATION_TEST_MODE=false**
- [ ] **EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=false**
- [ ] **Rate limiting is appropriately strict**
- [ ] **Audit logging is enabled**
- [ ] **Monitoring is enabled**
- [ ] **IP and User-Agent tracking is enabled**

### **Secret Management**
- [ ] **Secrets are not in version control**
- [ ] **Secrets are unique per environment**
- [ ] **Secrets are randomly generated**
- [ ] **Secrets are rotated regularly**
- [ ] **Secrets are stored securely**

## 📝 **Environment File Examples**

### **Minimal Development Setup**
```bash
# .env.development
FLASK_ENV=development
EMAIL_VERIFICATION_SECRET=your-32-char-secret-here
FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:5000
DATABASE_URL=postgresql://localhost:5432/mingus_dev
RESEND_API_KEY=re_your_api_key_here
```

### **Minimal Production Setup**
```bash
# .env.production
FLASK_ENV=production
EMAIL_VERIFICATION_SECRET=your-64-char-secret-here
FRONTEND_URL=https://mingus.app
API_BASE_URL=https://api.mingus.app
DATABASE_URL=postgresql://your-prod-db:5432/mingus_production
REDIS_URL=redis://your-prod-redis:6379/0
CELERY_BROKER_URL=redis://your-prod-redis:6379/1
RESEND_API_KEY=re_your_api_key_here
```

## 🔄 **Environment Switching**

### **Development to Staging**
```bash
# 1. Update environment variables
export FLASK_ENV=staging
source .env.staging

# 2. Validate configuration
python backend/config/validate_config.py --env staging

# 3. Test email verification flow
```

### **Staging to Production**
```bash
# 1. Update environment variables
export FLASK_ENV=production
source .env.production

# 2. Validate configuration (strict mode)
python backend/config/validate_config.py --env production --strict

# 3. Test email verification flow
# 4. Monitor logs and metrics
```

## 📞 **Troubleshooting**

### **Common Issues**
```bash
# Missing required variables
python backend/config/validate_config.py --env development

# Invalid configuration values
python backend/config/validate_config.py --env production --strict

# Secret too short
python backend/config/validate_config.py --env production --generate-secret
```

### **Configuration Errors**
- **Missing EMAIL_VERIFICATION_SECRET**: Generate using validation script
- **Invalid URLs**: Ensure proper HTTP/HTTPS format
- **Debug modes in production**: Disable all debug settings
- **Weak rate limiting**: Adjust limits for production security

## 🎯 **Next Steps**

1. **Generate secure secrets** for each environment
2. **Copy and customize** environment templates
3. **Validate configuration** using validation scripts
4. **Test email verification flow** in each environment
5. **Deploy to staging** and validate
6. **Deploy to production** with strict validation
7. **Monitor and maintain** configuration security

---

**Remember**: Security is paramount in production. Always validate configuration before deployment and never commit secrets to version control.
