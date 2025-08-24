# MINGUS Stripe Security Features Documentation

## Overview

This document details the comprehensive security features implemented in the MINGUS Stripe integration, including webhook signature verification, idempotency key management, API rate limiting compliance, and PCI compliance best practices.

## 🔒 **Security Features Implemented**

### 1. **Webhook Signature Verification**

#### ✅ **Enhanced Webhook Security**
- **Multi-layer signature verification** with HMAC-SHA256
- **Timestamp validation** to prevent replay attacks
- **Source IP validation** against Stripe's IP ranges
- **Payload structure validation** for malicious content
- **Signature caching** to prevent duplicate processing

#### **Implementation Details**
```python
# Enhanced webhook validation
is_valid, error_message = security_manager.validate_webhook_request(
    payload, signature, source_ip, timestamp, user_agent, request_id
)
```

#### **Security Checks**
1. **Signature Format Validation**: Ensures proper Stripe signature format
2. **Timestamp Verification**: Prevents replay attacks (5-minute tolerance)
3. **IP Address Validation**: Validates against Stripe's official IP ranges
4. **Payload Validation**: Checks JSON structure and required fields
5. **Duplicate Detection**: Prevents processing the same webhook multiple times

### 2. **Idempotency Key Management**

#### ✅ **Comprehensive Idempotency**
- **Automatic key generation** for all API operations
- **Redis-based storage** with fallback to memory cache
- **Configurable TTL** (default: 24 hours)
- **Operation-specific keys** for granular control
- **Result caching** to return consistent responses

#### **Implementation Details**
```python
# Generate idempotency key
idempotency_key = idempotency_manager.generate_idempotency_key(
    operation, user_id
)

# Check for existing operation
exists, cached_result = idempotency_manager.check_idempotency_key(key)

# Store operation result
idempotency_manager.store_idempotency_result(key, result, ttl=86400)
```

#### **Key Features**
- **Unique Key Generation**: Combines operation, user ID, timestamp, and UUID
- **Automatic Cleanup**: Removes expired keys to prevent memory bloat
- **Redis Integration**: Scalable storage with persistence
- **Memory Fallback**: Works without Redis for development

### 3. **API Rate Limiting Compliance**

#### ✅ **Stripe Rate Limit Compliance**
- **Operation-specific limits** based on Stripe's requirements
- **Per-user rate limiting** to prevent abuse
- **Sliding window implementation** for accurate tracking
- **Rate limit headers** in all responses
- **Configurable limits** for different operations

#### **Rate Limits Implemented**
```python
RATE_LIMITS = {
    'customer': 100,        # 100 requests per minute
    'subscription': 50,     # 50 requests per minute
    'payment_intent': 200,  # 200 requests per minute
    'webhook': 1000,        # 1000 requests per minute
    'default': 100          # Default limit
}
```

#### **Rate Limit Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

#### **Implementation Features**
- **Redis-based tracking** for distributed systems
- **Memory fallback** for single-server deployments
- **Automatic cleanup** of expired rate limit data
- **Per-operation tracking** for granular control

### 4. **PCI Compliance Best Practices**

#### ✅ **PCI DSS Compliance Features**
- **Sensitive data encryption** using Fernet (AES-128)
- **Data masking** for logging and display
- **Secure headers** for all responses
- **Audit logging** for all security events
- **No sensitive data in logs** or error messages

#### **Data Encryption**
```python
# Encrypt sensitive data
encrypted_data = pci_manager.encrypt_sensitive_data(card_number)

# Decrypt when needed
decrypted_data = pci_manager.decrypt_sensitive_data(encrypted_data)
```

#### **Data Masking**
```python
# Mask sensitive data for display
masked_card = pci_manager.mask_sensitive_data("4242424242424242", "card")
# Result: "************4242"

masked_email = pci_manager.mask_sensitive_data("user@example.com", "email")
# Result: "u***r@example.com"
```

#### **Secure Headers**
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com
Referrer-Policy: strict-origin-when-cross-origin
```

## 🛡️ **Security Architecture**

### **Security Manager Components**

#### 1. **WebhookSecurityManager**
- **Signature verification** with HMAC-SHA256
- **IP address validation** against Stripe's ranges
- **Timestamp validation** for replay protection
- **Payload structure validation**

#### 2. **IdempotencyKeyManager**
- **Key generation** and validation
- **Result caching** with TTL
- **Redis integration** with memory fallback
- **Automatic cleanup** of expired keys

#### 3. **RateLimitManager**
- **Per-operation rate limiting**
- **Sliding window implementation**
- **Rate limit headers** generation
- **Distributed rate limiting** support

#### 4. **PCISecurityManager**
- **Data encryption/decryption**
- **Sensitive data masking**
- **PCI compliance validation**
- **Secure headers** generation

#### 5. **SecurityAuditLogger**
- **Security event logging**
- **Audit trail** maintenance
- **Event severity** classification
- **Redis-based storage** for analysis

## 📊 **Security Monitoring**

### **Security Event Types**

#### **Webhook Security Events**
- `webhook_rate_limit_exceeded`
- `webhook_invalid_ip`
- `webhook_invalid_payload`
- `webhook_invalid_signature`
- `webhook_validated`

#### **API Security Events**
- `api_rate_limit_exceeded`
- `pci_compliance_violation`
- `api_request_processed`
- `security_validation_failed`

#### **Security Severity Levels**
- **LOW**: Normal operations, successful validations
- **MEDIUM**: Rate limit warnings, minor violations
- **HIGH**: Security violations, compliance issues
- **CRITICAL**: Signature failures, unauthorized access

### **Audit Logging**

#### **Security Event Structure**
```python
@dataclass
class SecurityEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    source_ip: str
    user_agent: str
    request_id: str
    severity: SecurityLevel
    details: Dict[str, Any]
    mitigated: bool = False
    mitigation_action: Optional[str] = None
```

#### **Log Storage**
- **File-based logging**: `logs/stripe_security_audit.log`
- **Redis storage**: For real-time analysis and alerting
- **30-day retention**: Automatic cleanup of old events
- **Structured format**: JSON for easy parsing

## 🔧 **Configuration**

### **Environment Variables**

#### **Security Configuration**
```bash
# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Encryption Key (auto-generated if not set)
STRIPE_ENCRYPTION_KEY=your_base64_encoded_key

# Webhook Security
STRIPE_WEBHOOK_ALLOWED_IPS=192.168.1.1,10.0.0.1

# Rate Limiting
STRIPE_RATE_LIMIT_ENABLED=true
STRIPE_RATE_LIMIT_WINDOW=60
```

#### **PCI Compliance Settings**
```python
PCI_SETTINGS = {
    'encrypt_sensitive_data': True,
    'log_retention_days': 90,
    'audit_logging': True,
    'data_masking': True,
    'secure_headers': True
}
```

## 🚀 **Usage Examples**

### **Enhanced Webhook Processing**
```python
# In your webhook endpoint
def stripe_webhook():
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    source_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    
    # Enhanced security validation
    event = stripe_service.handle_webhook(
        payload, signature, source_ip, user_agent, request_id
    )
    
    # Add security headers
    response = jsonify({'success': True})
    security_headers = security_manager.get_security_headers()
    for key, value in security_headers.items():
        response.headers[key] = value
    
    return response
```

### **Secure API Request Processing**
```python
# In your API endpoint
def create_customer():
    user_id = str(current_user.id)
    source_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    
    # Security validation and rate limiting
    customer = stripe_service.create_customer(
        email=data['email'],
        name=data.get('name'),
        user_id=user_id,
        source_ip=source_ip,
        user_agent=user_agent,
        request_id=request_id
    )
    
    # Add security headers
    response = jsonify({'success': True, 'customer': customer.to_dict()})
    security_headers = security_manager.get_security_headers()
    rate_limit_headers = security_manager.get_rate_limit_headers('customer', user_id)
    
    for key, value in {**security_headers, **rate_limit_headers}.items():
        response.headers[key] = value
    
    return response
```

### **Security Event Monitoring**
```python
# Get security events from the last 24 hours
events = security_manager.audit_logger.get_security_events(hours=24)

# Filter by severity
critical_events = security_manager.audit_logger.get_security_events(
    severity=SecurityLevel.CRITICAL, hours=24
)

# Analyze security patterns
for event in events:
    print(f"{event.timestamp}: {event.event_type} - {event.severity.value}")
    print(f"Source: {event.source_ip}, Details: {event.details}")
```

## 🧪 **Testing Security Features**

### **Webhook Security Testing**
```python
def test_webhook_security():
    # Test valid webhook
    payload = create_test_webhook_payload()
    signature = create_valid_signature(payload, webhook_secret)
    
    is_valid, error = security_manager.webhook_security.verify_webhook_signature(
        payload, signature
    )
    assert is_valid is True
    
    # Test invalid signature
    is_valid, error = security_manager.webhook_security.verify_webhook_signature(
        payload, "invalid_signature"
    )
    assert is_valid is False
```

### **Rate Limiting Testing**
```python
def test_rate_limiting():
    user_id = "test_user"
    
    # Test within limits
    for i in range(10):
        allowed, info = security_manager.rate_limit_manager.check_rate_limit(
            'customer', user_id
        )
        assert allowed is True
    
    # Test rate limit exceeded
    for i in range(200):  # Exceed limit
        allowed, info = security_manager.rate_limit_manager.check_rate_limit(
            'customer', user_id
        )
    
    assert allowed is False
    assert info['remaining'] == 0
```

### **PCI Compliance Testing**
```python
def test_pci_compliance():
    # Test data encryption
    sensitive_data = "4242424242424242"
    encrypted = security_manager.pci_manager.encrypt_sensitive_data(sensitive_data)
    decrypted = security_manager.pci_manager.decrypt_sensitive_data(encrypted)
    assert decrypted == sensitive_data
    
    # Test data masking
    masked = security_manager.pci_manager.mask_sensitive_data(sensitive_data, "card")
    assert masked == "************4242"
    
    # Test PCI validation
    compliant, violations = security_manager.pci_manager.validate_pci_compliance(
        'create_payment', {'card_number': encrypted}
    )
    assert compliant is True
    assert len(violations) == 0
```

## 📈 **Security Metrics and Monitoring**

### **Key Security Metrics**
1. **Webhook Security**
   - Signature verification success rate
   - Invalid IP attempts
   - Replay attack attempts
   - Payload validation failures

2. **Rate Limiting**
   - Rate limit violations by operation
   - Rate limit violations by user
   - Average requests per minute
   - Peak usage patterns

3. **PCI Compliance**
   - Data encryption coverage
   - Sensitive data exposure incidents
   - Compliance validation failures
   - Audit log completeness

4. **General Security**
   - Security event frequency by severity
   - Failed authentication attempts
   - Suspicious IP addresses
   - Unusual usage patterns

### **Alerting Setup**
```python
# Example alert configuration
ALERTS = {
    'webhook_security': {
        'invalid_signatures': {'threshold': 5, 'window': '1h'},
        'invalid_ips': {'threshold': 10, 'window': '1h'},
        'replay_attempts': {'threshold': 1, 'window': '1h'}
    },
    'rate_limiting': {
        'violations': {'threshold': 50, 'window': '1h'},
        'user_violations': {'threshold': 10, 'window': '1h'}
    },
    'pci_compliance': {
        'violations': {'threshold': 1, 'window': '1h'},
        'data_exposure': {'threshold': 1, 'window': '1h'}
    }
}
```

## 🔄 **Security Maintenance**

### **Regular Security Tasks**
1. **Update Stripe IP Ranges**: Monthly review of Stripe's webhook IP ranges
2. **Rotate Encryption Keys**: Quarterly key rotation for PCI compliance
3. **Review Security Logs**: Daily review of security events
4. **Update Rate Limits**: Monitor and adjust based on usage patterns
5. **Security Audits**: Monthly comprehensive security reviews

### **Security Checklist**
- [ ] Webhook signature verification enabled
- [ ] Rate limiting configured and active
- [ ] PCI compliance features enabled
- [ ] Security audit logging active
- [ ] Encryption keys properly managed
- [ ] Security headers implemented
- [ ] IP address validation active
- [ ] Idempotency keys working correctly

## 🎯 **Best Practices**

### **Security Best Practices**
1. **Never log sensitive data** - Always use data masking
2. **Validate all inputs** - Check webhook payloads and API requests
3. **Use HTTPS everywhere** - Enforce secure connections
4. **Implement proper rate limiting** - Prevent abuse and comply with Stripe limits
5. **Monitor security events** - Set up alerts for suspicious activity
6. **Regular security updates** - Keep dependencies and security features updated
7. **PCI compliance maintenance** - Regular audits and updates

### **Performance Considerations**
1. **Redis for production** - Use Redis for distributed rate limiting and caching
2. **Efficient signature validation** - Cache validated signatures
3. **Optimized rate limiting** - Use sliding windows for accurate tracking
4. **Minimal encryption overhead** - Only encrypt truly sensitive data

This comprehensive security implementation ensures that the MINGUS Stripe integration meets the highest security standards while maintaining excellent performance and usability. 