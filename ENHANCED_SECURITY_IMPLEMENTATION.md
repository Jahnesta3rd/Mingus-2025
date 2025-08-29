# Enhanced Authentication and JWT Security Implementation

## Overview

This document describes the comprehensive enhanced authentication and JWT security system implemented for the MINGUS Assessment System. The system provides banking-grade security with multiple layers of protection against common attack vectors.

## Security Components

### 1. Secure JWT Manager (`backend/security/secure_jwt_manager.py`)

**Features:**
- Enhanced JWT validation with security features
- IP address consistency checks
- User-Agent validation
- Token blacklisting
- Comprehensive payload validation
- Security event logging
- Token rotation capabilities

**Key Security Features:**
- **IP Validation**: Tokens are bound to the IP address where they were created
- **User-Agent Validation**: Tokens are bound to the User-Agent string
- **Token Blacklisting**: Revoked tokens are immediately invalidated
- **Token Rotation**: Automatic token refresh for long-lived sessions
- **Security Event Logging**: All JWT events are logged for monitoring

### 2. Brute Force Protection (`backend/security/brute_force_protection.py`)

**Features:**
- Redis-based attempt tracking
- Progressive lockout policies
- IP and user-based protection
- Security event logging
- Assessment submission protection

**Key Security Features:**
- **Progressive Lockouts**: Lockout duration increases with repeated failures
- **Multiple Action Types**: Separate protection for login, assessment, and password reset
- **Whitelist Support**: Trusted IPs and users can bypass restrictions
- **Suspicious Activity Detection**: Identifies patterns of abuse
- **Assessment Protection**: Prevents rapid assessment submissions

### 3. Secure Session Manager (`backend/security/secure_session_manager.py`)

**Features:**
- Redis-based session storage
- IP address consistency checks
- User-Agent validation
- Session fixation protection
- Comprehensive security monitoring

**Key Security Features:**
- **Session Consistency**: Sessions are bound to IP and User-Agent
- **Concurrent Session Limits**: Prevents session hijacking
- **Session Fixation Protection**: Regenerates session IDs on privilege escalation
- **Automatic Cleanup**: Expired sessions are automatically removed

### 4. Enhanced Authentication Middleware (`backend/middleware/enhanced_auth.py`)

**Features:**
- Integrates all security components
- Multiple authentication methods (JWT + Session)
- Assessment-specific authentication
- Security event monitoring

## Configuration

### Security Configuration (`backend/config/security_config.py`)

The system uses environment-specific configurations:

```python
# Development
class DevelopmentSecurityConfig(SecurityConfig):
    JWT_SECRET_KEY = 'dev-secret-key-change-in-production'
    MFA_ENABLED = False
    SUSPICIOUS_ACTIVITY_DETECTION = False

# Production
class ProductionSecurityConfig(SecurityConfig):
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    MFA_ENABLED = True
    SUSPICIOUS_ACTIVITY_DETECTION = True
```

### Environment Variables

```bash
# Required for production
JWT_SECRET_KEY=your-super-secret-jwt-key
REDIS_HOST=your-redis-host
REDIS_PASSWORD=your-redis-password

# Optional
MFA_ENABLED=true
FLASK_ENV=production
```

## Usage Examples

### 1. Basic Authentication

```python
from backend.middleware.enhanced_auth import require_auth

@app.route('/protected')
@require_auth
def protected_route():
    user_id = get_current_user_id()
    return jsonify({"message": f"Hello {user_id}"})
```

### 2. Assessment-Specific Authentication

```python
from backend.middleware.enhanced_auth import require_assessment_auth

@app.route('/assessment/submit', methods=['POST'])
@require_assessment_auth
def submit_assessment():
    # Assessment ID is automatically extracted from request
    assessment_id = g.assessment_id
    user_id = g.current_user_id
    
    # Process assessment submission
    return jsonify({"success": True})
```

### 3. Enhanced Authentication Routes

```python
from backend.routes.enhanced_auth_routes import auth_bp

# Register authentication routes
app.register_blueprint(auth_bp)

# Available endpoints:
# POST /auth/login - Enhanced login with security features
# POST /auth/logout - Secure logout with cleanup
# POST /auth/refresh - Token refresh
# POST /auth/validate - Token validation
# GET /auth/status - Authentication status
# GET /auth/sessions - User sessions
# DELETE /auth/sessions/<session_id> - Revoke session
# GET /auth/security/events - Security events
```

### 4. Login Example

```python
# Client-side login request
response = requests.post('/auth/login', json={
    'email': 'user@example.com',
    'password': 'secure-password',
    'remember_me': False
})

if response.status_code == 200:
    data = response.json()
    token = data['token']
    session_id = data['session_id']
    
    # Use token in subsequent requests
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('/protected', headers=headers)
```

### 5. Assessment Submission with Protection

```python
# Assessment submission with brute force protection
response = requests.post('/assessment/submit', 
    json={'assessment_id': 'assessment-123', 'answers': {...}},
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 429:
    # Rate limited - too many submissions
    retry_after = response.json().get('retry_after')
```

## Integration with Existing Code

### 1. Update Existing Routes

Replace existing authentication decorators:

```python
# Before
from backend.middleware.auth import require_auth

# After
from backend.middleware.enhanced_auth import require_auth
```

### 2. Update Assessment Routes

For assessment endpoints, use the assessment-specific decorator:

```python
# Before
@app.route('/assessment/submit', methods=['POST'])
@require_auth
def submit_assessment():
    # Manual assessment ID extraction
    assessment_id = request.json.get('assessment_id')
    
# After
@app.route('/assessment/submit', methods=['POST'])
@require_assessment_auth
def submit_assessment():
    # Assessment ID automatically available
    assessment_id = g.assessment_id
```

### 3. Update Login Routes

Replace existing login logic with enhanced authentication:

```python
# Before
@app.route('/login', methods=['POST'])
def login():
    # Manual authentication logic
    if validate_credentials(email, password):
        session['user_id'] = user_id
        return jsonify({"success": True})

# After
from backend.routes.enhanced_auth_routes import login
# Use the enhanced login endpoint with all security features
```

## Security Features in Detail

### 1. JWT Security

**Token Structure:**
```json
{
  "sub": "user-id",
  "iat": 1640995200,
  "exp": 1640998800,
  "iss": "mingus-app",
  "aud": "mingus-users",
  "jti": "unique-token-id",
  "ip": "192.168.1.1",
  "user_agent_hash": "sha256-hash",
  "created_at": 1640995200,
  "token_version": "1.0"
}
```

**Validation Checks:**
- Signature verification
- Expiration validation
- Issuer and audience validation
- IP address consistency
- User-Agent consistency
- Token blacklist check

### 2. Brute Force Protection

**Configuration:**
```python
# Login attempts
max_login_attempts = 5
login_lockout_duration = 300  # 5 minutes
progressive_multiplier = 2.0

# Assessment attempts
max_assessment_attempts = 10
assessment_lockout_duration = 600  # 10 minutes
```

**Progressive Lockout:**
- 1st lockout: 5 minutes
- 2nd lockout: 10 minutes
- 3rd lockout: 20 minutes
- Maximum: 24 hours

### 3. Session Security

**Session Data:**
```json
{
  "session_id": "unique-session-id",
  "user_id": "user-id",
  "created_at": 1640995200,
  "last_activity": 1640995200,
  "expires_at": 1640998800,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "user_agent_hash": "sha256-hash",
  "is_active": true,
  "remember_me": false
}
```

## Monitoring and Logging

### 1. Security Events

All security events are logged to dedicated files:

- `logs/security_jwt.log` - JWT security events
- `logs/brute_force_security.log` - Brute force protection events
- `logs/session_security.log` - Session security events

### 2. Security Event Types

**JWT Events:**
- `token_created` - New token created
- `token_validated` - Token successfully validated
- `token_expired` - Token expired
- `token_revoked` - Token manually revoked
- `ip_mismatch` - IP address mismatch detected
- `user_agent_mismatch` - User-Agent mismatch detected

**Brute Force Events:**
- `failed_attempt` - Failed login attempt
- `account_locked` - Account locked due to failed attempts
- `successful_attempt` - Successful login
- `lockout_cleared` - Lockout manually cleared

**Session Events:**
- `session_created` - New session created
- `session_validated` - Session successfully validated
- `session_expired` - Session expired
- `session_revoked` - Session manually revoked
- `session_ip_mismatch` - Session IP mismatch detected

### 3. Monitoring Endpoints

```python
# Get security events for current user
GET /auth/security/events?hours=24

# Get suspicious activity
GET /auth/security/suspicious-activity?hours=24

# Get lockout information
GET /auth/security/lockout-info?identifier=user@example.com&action_type=login
```

## Testing

### 1. Run Security Tests

```bash
# Run all security tests
pytest tests/test_enhanced_security.py -v

# Run specific test categories
pytest tests/test_enhanced_security.py::TestSecureJWTManager -v
pytest tests/test_enhanced_security.py::TestBruteForceProtection -v
pytest tests/test_enhanced_security.py::TestSecureSessionManager -v
```

### 2. Test Scenarios

**JWT Security Tests:**
- Token creation and validation
- IP address mismatch detection
- User-Agent mismatch detection
- Token expiration handling
- Token revocation

**Brute Force Protection Tests:**
- Failed attempt tracking
- Account lockout functionality
- Progressive lockout calculation
- Assessment submission protection

**Session Security Tests:**
- Session creation and validation
- IP consistency checks
- Session expiration handling
- Concurrent session limits

## Deployment Considerations

### 1. Production Setup

**Redis Configuration:**
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis for security
sudo nano /etc/redis/redis.conf

# Set password
requirepass your-redis-password

# Bind to localhost only
bind 127.0.0.1

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

**Environment Variables:**
```bash
# Production environment
export FLASK_ENV=production
export JWT_SECRET_KEY=your-super-secret-jwt-key
export REDIS_HOST=localhost
export REDIS_PASSWORD=your-redis-password
export MFA_ENABLED=true
```

### 2. Monitoring Setup

**Log Rotation:**
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/mingus-security

# Log rotation configuration
/var/log/mingus/security_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

**Security Monitoring:**
- Monitor security log files for suspicious activity
- Set up alerts for repeated failed login attempts
- Monitor Redis memory usage for security data
- Regular security event analysis

### 3. Performance Considerations

**Redis Optimization:**
- Use separate Redis databases for different security components
- Configure appropriate TTL for security data
- Monitor Redis memory usage
- Consider Redis clustering for high availability

**JWT Optimization:**
- Keep JWT payload size minimal
- Use appropriate token expiration times
- Implement token refresh strategies
- Monitor token usage patterns

## Troubleshooting

### 1. Common Issues

**Redis Connection Issues:**
```python
# Check Redis connection
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Should return True
```

**JWT Validation Issues:**
```python
# Check JWT configuration
from backend.config.security_config import SecurityConfig
config = SecurityConfig()
print(config.get_jwt_config())
```

**Session Issues:**
```python
# Check session configuration
from backend.config.security_config import SecurityConfig
config = SecurityConfig()
print(config.get_session_config())
```

### 2. Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('security.jwt').setLevel(logging.DEBUG)
logging.getLogger('security.brute_force').setLevel(logging.DEBUG)
logging.getLogger('security.session').setLevel(logging.DEBUG)
```

### 3. Configuration Validation

```python
from backend.config.security_config import SecurityConfig

# Validate configuration
issues = SecurityConfig.validate_config()
for issue in issues:
    print(f"Configuration issue: {issue}")
```

## Security Best Practices

### 1. Token Management

- Use short-lived JWT tokens (1 hour or less)
- Implement token refresh mechanisms
- Revoke tokens on logout
- Monitor token usage patterns

### 2. Session Management

- Limit concurrent sessions per user
- Implement session timeout
- Use secure session cookies
- Monitor session activity

### 3. Brute Force Protection

- Use progressive lockouts
- Implement CAPTCHA after multiple failures
- Monitor for suspicious activity patterns
- Whitelist trusted IPs when appropriate

### 4. Monitoring and Alerting

- Log all security events
- Set up alerts for suspicious activity
- Regular security event analysis
- Monitor system performance impact

## Conclusion

The enhanced authentication and JWT security system provides comprehensive protection for the MINGUS Assessment System. The multi-layered approach ensures that even if one security measure is bypassed, others remain active to protect the system.

Key benefits:
- **Enhanced Security**: Multiple layers of protection
- **Comprehensive Monitoring**: Detailed logging and event tracking
- **Flexible Configuration**: Environment-specific settings
- **Easy Integration**: Drop-in replacement for existing authentication
- **Scalable Design**: Redis-based storage for high performance

For questions or support, refer to the security logs and monitoring endpoints for detailed information about system behavior and security events.
