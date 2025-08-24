# Security Implementation for Financial Profile Feature

## Overview

This document outlines the comprehensive security measures implemented for the financial profile feature, ensuring the highest level of protection for sensitive financial data.

## Security Measures Implemented

### 1. Supabase Row Level Security (RLS)

**File:** `migrations/security_policies.sql`

- **Enabled RLS** on all financial tables:
  - `user_income_due_dates`
  - `user_expense_due_dates`
  - `user_onboarding_profiles`
  - `user_income_sources`
  - `anonymous_onboarding_responses`

- **Security Policies:**
  - Users can only access their own data
  - SELECT, INSERT, UPDATE, DELETE operations restricted by user_id
  - Data validation constraints with reasonable limits
  - Automatic cleanup of old records

- **Validation Limits:**
  - Income amounts: $0 - $1M per source
  - Expense amounts: $0 - $100K per expense
  - Monthly income: $0 - $1M
  - Monthly expenses: $0 - $500K
  - Savings goals: $0 - $10M
  - Debt amounts: $0 - $5M

### 2. Field-Level Encryption

**File:** `backend/models/encrypted_financial_models.py`

- **Encryption Algorithm:** AES-256-GCM with Fernet
- **Encrypted Fields:**
  - Monthly income
  - Current savings
  - Current debt
  - Emergency fund
  - Savings goals
  - Debt payoff goals
  - Investment goals
  - Income source amounts
  - Debt account balances
  - Minimum payments

- **Key Management:**
  - Environment variable: `ENCRYPTION_KEY`
  - Automatic key generation for development
  - Secure key storage in production

- **Encryption Functions:**
  - `encrypt_value()`: Encrypts numeric values
  - `decrypt_value()`: Decrypts numeric values
  - Automatic encryption/decryption in model methods

### 3. HTTPS and Security Headers

**File:** `config/base.py`

- **HTTPS Enforcement:**
  - `SESSION_COOKIE_SECURE = True`
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Strict'`
  - HSTS header with preload

- **Security Headers:**
  - Content Security Policy (CSP)
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: restrictive
  - Cache-Control: no-store, no-cache, must-revalidate

### 4. Input Validation

**File:** `backend/middleware/security_middleware.py`

- **Validation Rules:**
  - Amount validation with reasonable limits
  - Frequency validation (weekly, bi-weekly, monthly, etc.)
  - Currency symbol and comma removal
  - Negative value prevention
  - Type checking and conversion

- **Rate Limiting:**
  - 10 requests per minute for financial endpoints
  - IP-based rate limiting
  - Request tracking and logging

### 5. Audit Logging

**File:** `backend/services/audit_logging.py`

- **Comprehensive Logging:**
  - All financial data access (CREATE, READ, UPDATE, DELETE)
  - Field-level change tracking
  - IP address and user agent logging
  - Session tracking
  - Request ID correlation

- **Audit Features:**
  - User activity summaries
  - Suspicious activity detection
  - Export capabilities
  - Automatic cleanup (90-day retention)

- **Suspicious Activity Detection:**
  - High frequency access (>50 requests in 24 hours)
  - Multiple IP access (>3 IPs in 24 hours)
  - Rapid field updates (>10 updates in 24 hours)

## Database Schema

### Encrypted Financial Tables

```sql
-- Encrypted Financial Profile
CREATE TABLE encrypted_financial_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    monthly_income TEXT, -- Encrypted
    income_frequency VARCHAR(50),
    primary_income_source VARCHAR(100),
    secondary_income_source VARCHAR(100),
    current_savings TEXT, -- Encrypted
    current_debt TEXT, -- Encrypted
    emergency_fund TEXT, -- Encrypted
    savings_goal TEXT, -- Encrypted
    debt_payoff_goal TEXT, -- Encrypted
    investment_goal TEXT, -- Encrypted
    risk_tolerance VARCHAR(50),
    investment_experience VARCHAR(50),
    budgeting_experience VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    is_complete BOOLEAN DEFAULT FALSE
);

-- Encrypted Income Sources
CREATE TABLE encrypted_income_sources (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    source_name VARCHAR(100) NOT NULL,
    amount TEXT NOT NULL, -- Encrypted
    frequency VARCHAR(50) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Encrypted Debt Accounts
CREATE TABLE encrypted_debt_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    account_name VARCHAR(100) NOT NULL,
    balance TEXT NOT NULL, -- Encrypted
    interest_rate DECIMAL(5,4),
    minimum_payment TEXT, -- Encrypted
    account_type VARCHAR(50) NOT NULL,
    due_date INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Financial Audit Logs
CREATE TABLE financial_audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    field_name VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### Secure Financial Profile Endpoints

- `GET /api/secure/financial-profile` - Get encrypted profile
- `POST /api/secure/financial-profile` - Create encrypted profile
- `PUT /api/secure/financial-profile` - Update encrypted profile

### Income Sources Endpoints

- `GET /api/secure/income-sources` - Get encrypted income sources
- `POST /api/secure/income-sources` - Create encrypted income source

### Debt Accounts Endpoints

- `GET /api/secure/debt-accounts` - Get encrypted debt accounts
- `POST /api/secure/debt-accounts` - Create encrypted debt account

### Audit Endpoints

- `GET /api/secure/audit-logs` - Get user audit logs
- `GET /api/secure/audit-summary` - Get audit summary

## Security Decorators

### Available Decorators

- `@require_https` - Enforce HTTPS
- `@require_authentication` - Require user authentication
- `@validate_financial_data` - Validate financial input
- `@audit_financial_access` - Log financial access

### Usage Example

```python
@secure_financial_bp.route('/api/secure/financial-profile', methods=['GET'])
@require_https
@require_authentication
@audit_financial_access
def get_financial_profile():
    # Implementation
    pass
```

## Configuration

### Environment Variables

```bash
# Required for encryption
ENCRYPTION_KEY=your-secure-encryption-key

# Supabase configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Security settings
SECRET_KEY=your-flask-secret-key
```

### Security Configuration

```python
# Security headers
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'Content-Security-Policy': '...',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    # ... more headers
}

# Financial validation limits
FINANCIAL_VALIDATION_LIMITS = {
    'max_income_per_source': 1000000,
    'max_expense_per_item': 100000,
    'max_monthly_income': 1000000,
    'max_monthly_expenses': 500000,
    'max_savings_goal': 10000000,
    'max_debt_amount': 5000000,
    'min_amount': 0,
    'max_frequency_options': ['weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually']
}

# Audit logging
AUDIT_LOG_ENABLED = True
AUDIT_LOG_RETENTION_DAYS = 90
AUDIT_LOG_SENSITIVE_FIELDS = [
    'monthly_income', 'current_savings', 'current_debt', 
    'emergency_fund', 'savings_goal', 'debt_payoff_goal'
]
```

## Monitoring and Alerts

### Audit Log Monitoring

- Real-time access logging
- Suspicious activity detection
- Automated alerts for unusual patterns
- Regular audit report generation

### Security Metrics

- Failed authentication attempts
- Rate limit violations
- Encryption/decryption errors
- Database access patterns
- API usage statistics

## Best Practices

### Development

1. **Never commit encryption keys** to version control
2. **Use environment variables** for all sensitive configuration
3. **Test security measures** thoroughly in development
4. **Validate all inputs** before processing
5. **Log security events** for monitoring

### Production

1. **Use strong encryption keys** (32+ characters)
2. **Enable HTTPS** with valid certificates
3. **Monitor audit logs** regularly
4. **Implement backup encryption** for audit logs
5. **Regular security reviews** and updates

### Data Protection

1. **Encrypt sensitive data** at rest and in transit
2. **Implement proper access controls** (RLS)
3. **Regular data backups** with encryption
4. **Data retention policies** for audit logs
5. **Secure disposal** of old data

## Compliance

This implementation supports compliance with:

- **GDPR** - Data protection and privacy
- **SOX** - Financial data security
- **PCI DSS** - Payment card data security
- **HIPAA** - Health information privacy (if applicable)

## Troubleshooting

### Common Issues

1. **Encryption Key Errors**
   - Ensure `ENCRYPTION_KEY` is set
   - Check key format and length
   - Verify key is accessible to application

2. **RLS Policy Errors**
   - Verify user authentication
   - Check user_id in policies
   - Ensure proper table permissions

3. **Validation Errors**
   - Check input format and limits
   - Verify currency formatting
   - Review validation rules

4. **Audit Log Issues**
   - Check database permissions
   - Verify log file permissions
   - Monitor disk space for logs

### Security Incident Response

1. **Immediate Actions**
   - Isolate affected systems
   - Preserve audit logs
   - Notify security team

2. **Investigation**
   - Review audit logs
   - Analyze access patterns
   - Identify root cause

3. **Recovery**
   - Implement additional security measures
   - Update encryption keys if compromised
   - Restore from secure backups

## Conclusion

This comprehensive security implementation provides multiple layers of protection for financial data:

1. **Database-level security** with RLS policies
2. **Field-level encryption** for sensitive data
3. **Transport security** with HTTPS and headers
4. **Input validation** with reasonable limits
5. **Comprehensive audit logging** for monitoring

The implementation follows security best practices and provides a robust foundation for protecting sensitive financial information in the Mingus application.

# Phone Verification Security Implementation

## Overview

This document outlines the comprehensive security measures implemented for the phone verification system, including rate limiting, CAPTCHA integration, SIM swap protection, secure code generation, and monitoring.

## 🔒 Security Features Implemented

### 1. **Rate Limiting (Frontend & Backend)**

#### Backend Rate Limiting
- **Per-action limits**: Different limits for send_code, verify_code, resend_code, change_phone
- **Progressive delays**: 60s, 120s, 300s for resend attempts
- **IP-based tracking**: Prevents abuse from single IP addresses
- **User-based tracking**: Prevents abuse from single users
- **Session-based limits**: Maximum 3 resend attempts per session

#### Frontend Rate Limiting
- **Client-side protection**: Prevents excessive requests before reaching server
- **Local storage tracking**: Persists across page refreshes
- **Real-time feedback**: Shows remaining attempts and cooldown timers
- **Automatic reset**: Clears after window expiration

### 2. **CAPTCHA Integration**

#### Implementation
- **reCAPTCHA v2**: Google's reCAPTCHA service
- **Conditional display**: Only shown after multiple failed attempts
- **Dark theme support**: Matches Mingus design system
- **Accessibility**: Screen reader compatible
- **Error handling**: Graceful fallback on CAPTCHA failures

#### Configuration
```typescript
const captchaConfig = {
  enabled: true,
  provider: 'recaptcha',
  site_key: 'your_recaptcha_site_key',
  secret_key: 'your_recaptcha_secret_key',
  trigger_attempts: 3  // Show after 3 failed attempts
};
```

### 3. **SIM Swap Attack Protection**

#### Detection Methods
- **Phone number changes**: Track rapid phone number changes per user
- **IP address changes**: Monitor IP changes during verification process
- **Time-based analysis**: Detect suspicious patterns within 24-hour windows
- **Geographic anomalies**: Flag verification from unexpected locations

#### Response Actions
- **Additional verification**: Require extra steps for suspicious users
- **Support notification**: Alert support team for manual review
- **Temporary blocking**: Block suspicious IPs for 24 hours
- **User notification**: Inform users of suspicious activity

### 4. **Secure Code Generation**

#### Cryptographic Security
- **Secrets module**: Uses Python's `secrets` module for cryptographically secure random numbers
- **HMAC-SHA256**: Secure hashing with salt for code storage
- **Salt generation**: Unique salt per verification attempt
- **Constant-time comparison**: Prevents timing attacks

#### Code Properties
- **Length**: 6 digits (configurable)
- **Expiration**: 10 minutes (configurable)
- **Single-use**: Each code can only be used once
- **Rate-limited**: Maximum 3 attempts per code

### 5. **Input Sanitization & Validation**

#### Phone Number Validation
- **Format validation**: E.164 format enforcement
- **Pattern detection**: Identifies suspicious patterns (repeated digits, palindromes)
- **Test number blocking**: Prevents use of common test numbers
- **Length validation**: Enforces proper phone number length

#### Code Validation
- **Length check**: Ensures 6-digit codes
- **Format validation**: Numeric only
- **Expiration check**: Validates against stored expiration time
- **Attempt tracking**: Prevents brute force attacks

### 6. **Audit Logging**

#### Logged Events
- **send_code**: Initial code send attempts
- **verify_success**: Successful verifications
- **verify_failed**: Failed verification attempts
- **rate_limit_exceeded**: Rate limit violations
- **suspicious_activity**: Flagged suspicious behavior
- **sim_swap_detected**: Potential SIM swap attacks
- **captcha_failed**: CAPTCHA verification failures

#### Log Data
- **User ID**: Associated user (if available)
- **IP Address**: Client IP address
- **User Agent**: Browser/client information
- **Phone Number**: Target phone number
- **Event Type**: Type of security event
- **Risk Score**: Calculated risk score (0.0-1.0)
- **Timestamp**: Event occurrence time
- **Details**: JSON data with event-specific information

### 7. **GDPR/Privacy Compliance**

#### Data Protection
- **Minimal collection**: Only collect necessary data
- **Encrypted storage**: All sensitive data encrypted at rest
- **Access controls**: Role-based access to audit logs
- **Data retention**: Automatic cleanup after 90 days
- **User rights**: Support for data deletion requests

#### Privacy Features
- **Phone number hashing**: Store hashed phone numbers where possible
- **IP anonymization**: Option to anonymize IP addresses
- **Consent tracking**: Track user consent for verification
- **Audit trails**: Complete audit trails for compliance

## 🛡️ Security Monitoring & Alerting

### 1. **Real-time Monitoring**

#### Suspicious Activity Detection
- **High-risk activities**: Events with risk score > 0.8
- **Rapid attempts**: >10 attempts per minute
- **Multiple failures**: >5 consecutive failures
- **Suspicious IPs**: >20 events per hour from single IP
- **SIM swap indicators**: >3 phone changes per day

#### Alert Types
- **High Risk Activity**: High risk score events
- **Rapid Attempts**: Excessive request rates
- **Multiple Failures**: Consecutive verification failures
- **Suspicious IP**: Suspicious IP address activity
- **SIM Swap Indicator**: Potential SIM swap attacks

### 2. **Automated Responses**

#### Immediate Actions
- **IP blocking**: Temporary block suspicious IPs (24 hours)
- **Rate limiting**: Increase rate limits for suspicious users
- **Additional verification**: Require extra steps for high-risk users
- **Support notification**: Alert security team

#### Escalation Procedures
- **Low risk**: Log and monitor
- **Medium risk**: Increase monitoring, require CAPTCHA
- **High risk**: Block IP, require manual review
- **Critical risk**: Immediate support intervention

### 3. **Security Dashboard**

#### Metrics Display
- **Alert summary**: Counts by type and severity
- **Suspicious IPs**: Top suspicious IP addresses
- **High-risk activities**: Recent high-risk events
- **Success rates**: Verification success rates
- **Trend analysis**: Security trends over time

## 🔧 Implementation Details

### 1. **Database Schema**

#### Security Tables
```sql
-- Verification audit log
CREATE TABLE verification_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    phone_number TEXT,
    event_type TEXT NOT NULL,
    event_details TEXT,
    risk_score REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced phone verification table
ALTER TABLE phone_verification ADD COLUMN salt TEXT;
ALTER TABLE phone_verification ADD COLUMN ip_address TEXT;
ALTER TABLE phone_verification ADD COLUMN user_agent TEXT;
ALTER TABLE phone_verification ADD COLUMN captcha_verified INTEGER DEFAULT 0;
ALTER TABLE phone_verification ADD COLUMN risk_score REAL DEFAULT 0.0;
```

#### Security Views
```sql
-- Suspicious IP addresses
CREATE VIEW suspicious_ips AS
SELECT ip_address, COUNT(*) as total_events,
       COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failed_attempts,
       AVG(risk_score) as avg_risk_score
FROM verification_audit_log 
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY ip_address
HAVING COUNT(*) > 10 OR AVG(risk_score) > 0.6;

-- User security summary
CREATE VIEW user_security_summary AS
SELECT user_id, COUNT(*) as total_verifications,
       COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
       AVG(risk_score) as avg_risk_score
FROM phone_verification 
GROUP BY user_id;
```

### 2. **Backend Services**

#### VerificationSecurity Class
- **Rate limiting**: Per-action and per-user limits
- **CAPTCHA verification**: reCAPTCHA integration
- **SIM swap detection**: Pattern-based detection
- **Risk scoring**: Calculates risk scores for events
- **Audit logging**: Comprehensive event logging

#### SecurityMonitor Class
- **Real-time monitoring**: Continuous security monitoring
- **Alert generation**: Automatic alert creation
- **Automated responses**: Immediate security actions
- **Dashboard data**: Security metrics and insights

### 3. **Frontend Components**

#### CAPTCHAComponent
- **reCAPTCHA integration**: Google reCAPTCHA v2
- **Theme support**: Dark/light theme compatibility
- **Error handling**: Graceful error handling
- **Accessibility**: Screen reader support

#### Rate Limiting Hook
- **Client-side protection**: Prevents excessive requests
- **Local storage**: Persists across sessions
- **Real-time feedback**: Shows remaining attempts
- **Automatic reset**: Clears after expiration

## 📊 Security Metrics & KPIs

### 1. **Key Metrics**
- **Verification success rate**: Target >95%
- **False positive rate**: Target <1%
- **Response time**: <5 minutes for critical alerts
- **Data retention compliance**: 100% GDPR compliance

### 2. **Risk Scoring**
- **0.0-0.3**: Low risk (normal activity)
- **0.3-0.6**: Medium risk (monitor closely)
- **0.6-0.8**: High risk (require additional verification)
- **0.8-1.0**: Critical risk (immediate action required)

### 3. **Alert Severity**
- **Low**: Log and monitor
- **Medium**: Increase monitoring, require CAPTCHA
- **High**: Block IP, require manual review
- **Critical**: Immediate support intervention

## 🚀 Production Deployment

### 1. **Environment Variables**
```bash
# CAPTCHA Configuration
RECAPTCHA_SITE_KEY=your_site_key
RECAPTCHA_SECRET_KEY=your_secret_key

# Security Thresholds
SECURITY_MAX_ATTEMPTS=3
SECURITY_CAPTCHA_TRIGGER=3
SECURITY_RISK_THRESHOLD=0.8

# Monitoring
SECURITY_ALERT_EMAIL=security@mingus.com
SECURITY_RETENTION_DAYS=90
```

### 2. **SMS Service Integration**
- **Twilio**: Recommended for production
- **AWS SNS**: Alternative option
- **SendGrid**: Email fallback option
- **Rate limiting**: Respect SMS provider limits

### 3. **Monitoring Setup**
- **Log aggregation**: Centralized logging system
- **Alert channels**: Email, Slack, PagerDuty
- **Dashboard**: Real-time security dashboard
- **Backup monitoring**: Redundant monitoring systems

## 🔍 Testing & Validation

### 1. **Security Testing**
- **Rate limiting tests**: Verify limits are enforced
- **CAPTCHA tests**: Ensure CAPTCHA works correctly
- **SIM swap tests**: Validate detection algorithms
- **Penetration testing**: Regular security assessments

### 2. **Performance Testing**
- **Load testing**: Verify system under high load
- **Stress testing**: Test rate limiting effectiveness
- **Latency testing**: Ensure security doesn't impact performance

### 3. **Compliance Testing**
- **GDPR compliance**: Verify data protection measures
- **Audit trail validation**: Ensure complete logging
- **Data retention testing**: Verify cleanup processes

## 📋 Maintenance & Updates

### 1. **Regular Maintenance**
- **Log cleanup**: Daily cleanup of old audit logs
- **Risk score calibration**: Monthly risk score adjustments
- **Threshold updates**: Quarterly threshold reviews
- **Security updates**: Regular security patch updates

### 2. **Monitoring Improvements**
- **Pattern analysis**: Continuous improvement of detection algorithms
- **False positive reduction**: Regular review and adjustment
- **Performance optimization**: Ongoing performance improvements

### 3. **Compliance Updates**
- **GDPR updates**: Stay current with privacy regulations
- **Security standards**: Follow industry best practices
- **Audit preparation**: Regular compliance audits

This comprehensive security implementation provides robust protection against various attack vectors while maintaining user experience and compliance with privacy regulations. 