# MINGUS Authentication System Documentation

## Overview

The MINGUS Authentication System provides a comprehensive, secure authentication solution with email verification, password reset capabilities, and advanced security features. This system is designed to handle production workloads with 1,000+ users across multiple metropolitan areas.

## Architecture

### Core Components

1. **AuthService** - Business logic for authentication operations
2. **AuthToken Model** - Secure token management for password reset
3. **EmailVerification Model** - Email verification tracking and management
4. **Enhanced Auth Routes** - Flask endpoints with security middleware
5. **Resend Email Service** - Email delivery via Resend API
6. **Rate Limiting** - Protection against abuse and brute force attacks

### Security Features

- **CSRF Protection** - All state-changing operations protected
- **Rate Limiting** - Configurable limits per endpoint type
- **Secure Token Generation** - Cryptographically secure random tokens
- **Token Hashing** - SHA-256 hashing for secure storage
- **Timing Attack Protection** - Constant-time operations
- **Audit Logging** - Comprehensive security event tracking
- **IP and User Agent Tracking** - Security monitoring and fraud detection

## Database Schema

### Tables

#### `auth_tokens`
Stores authentication tokens for password reset and other operations.

```sql
CREATE TABLE auth_tokens (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    token_type VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET NULL,
    user_agent TEXT NULL
);
```

#### `email_verifications`
Tracks email verification status and tokens.

```sql
CREATE TABLE email_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    verification_token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resend_count INTEGER DEFAULT 0,
    last_resend_at TIMESTAMP WITH TIME ZONE NULL
);
```

#### `auth_audit_log`
Comprehensive audit trail for security monitoring.

```sql
CREATE TABLE auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NULL,
    ip_address INET NULL,
    user_agent TEXT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Database Functions

#### `cleanup_expired_auth_tokens()`
Automatically removes expired tokens and verifications.

#### `log_auth_event()`
Logs authentication events for security monitoring.

#### `get_user_verification_status()`
Returns comprehensive verification status for a user.

#### `validate_password_strength()`
Validates password strength against security requirements.

## API Endpoints

### Email Verification

#### `POST /auth/verify-email`
Verify user email with token.

**Request Body:**
```json
{
    "token": "verification_token_string"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Email verified successfully",
    "user_id": 123
}
```

#### `GET /auth/verify-email/<token>`
Verify user email via GET (for email links).

**Response:**
```json
{
    "success": true,
    "message": "Email verified successfully",
    "user_id": 123,
    "redirect_url": "https://mingusapp.com/dashboard"
}
```

#### `POST /auth/resend-verification`
Resend verification email.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Verification email sent successfully"
}
```

### Password Reset

#### `POST /auth/forgot-password`
Request password reset.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password reset email sent successfully"
}
```

#### `GET /auth/reset-password/<token>`
Validate password reset token.

**Response:**
```json
{
    "success": true,
    "message": "Token is valid",
    "user_id": 123,
    "token_valid": true
}
```

#### `POST /auth/reset-password`
Reset password with token.

**Request Body:**
```json
{
    "token": "reset_token_string",
    "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password reset successfully"
}
```

### User Management

#### `GET /auth/verification-status`
Get current user's email verification status.

**Response:**
```json
{
    "success": true,
    "verification_status": {
        "user_id": 123,
        "email": "user@example.com",
        "email_verified": false,
        "verification_status": {
            "has_verification": true,
            "is_expired": false,
            "can_resend": true,
            "resend_count": 1,
            "max_resend_attempts": 5
        }
    }
}
```

#### `POST /auth/request-verification`
Request email verification for authenticated user.

**Response:**
```json
{
    "success": true,
    "message": "Verification email sent successfully"
}
```

#### `POST /auth/cleanup-tokens`
Clean up expired tokens (admin/maintenance).

**Response:**
```json
{
    "success": true,
    "message": "Cleanup completed successfully",
    "tokens_cleaned": 15
}
```

## Authentication Flow

### User Registration Flow

1. User submits registration form
2. System creates user account with `email_verified = false`
3. System generates verification token
4. Verification email sent via Resend
5. User clicks verification link
6. System verifies token and sets `email_verified = true`
7. User can now access protected features

### Password Reset Flow

1. User requests password reset
2. System validates email and creates reset token
3. Reset email sent via Resend with 1-hour expiry
4. User clicks reset link
5. System validates token
6. User submits new password
7. System updates password and marks token as used
8. User can login with new password

### Email Verification Flow

1. User requests verification email
2. System checks resend limits and timing
3. System generates new verification token
4. Verification email sent via Resend
5. User clicks verification link
6. System verifies token and updates user status

## Security Features

### Rate Limiting

- **Authentication endpoints**: 10 requests per 5 minutes
- **Password reset**: 3 requests per hour
- **General API**: 100 requests per hour
- **Registration**: 5 requests per 5 minutes

### Token Security

- **Verification tokens**: 24-hour expiry
- **Password reset tokens**: 1-hour expiry
- **Secure generation**: 32+ character random tokens
- **SHA-256 hashing**: Secure storage of tokens
- **Single use**: Tokens marked as used after consumption

### Password Requirements

- Minimum 8 characters
- At least one letter
- At least one number
- At least one special character

### CSRF Protection

All state-changing operations require CSRF tokens to prevent cross-site request forgery attacks.

### Audit Logging

Every authentication event is logged with:
- User ID (if applicable)
- Event type
- IP address
- User agent
- Success/failure status
- Error messages
- Timestamp

## Integration

### Flask Application

Register the enhanced authentication blueprint:

```python
from backend.routes.enhanced_auth_routes import enhanced_auth_bp

app.register_blueprint(enhanced_auth_bp)
```

### Service Initialization

Initialize the authentication service:

```python
from backend.services.auth_service import AuthService

auth_service = AuthService(session_factory)
app.auth_service = auth_service
```

### Email Service

The system integrates with the existing Resend email service for reliable email delivery.

### Database Migration

Run the authentication migration:

```bash
psql -d your_database -f backend/migrations/002_create_auth_tables.sql
```

## Configuration

### Environment Variables

```bash
# Email service
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=noreply@mingusapp.com
RESEND_FROM_NAME=MINGUS Financial Wellness

# Frontend URLs
FRONTEND_URL=https://mingusapp.com

# Security
SECRET_KEY=your_secret_key
```

### Rate Limiting Configuration

Customize rate limits in `backend/middleware/rate_limiter.py`:

```python
self.default_limits = {
    'auth': {'requests': 10, 'window': 300},              # 10 per 5 minutes
    'password_reset': {'requests': 3, 'window': 3600},    # 3 per hour
    'register': {'requests': 5, 'window': 300},           # 5 per 5 minutes
}
```

## Testing

### Running Tests

```bash
# Run all authentication tests
pytest backend/tests/test_auth_system.py -v

# Run specific test class
pytest backend/tests/test_auth_system.py::TestAuthService -v

# Run with coverage
pytest backend/tests/test_auth_system.py --cov=backend.services.auth_service --cov-report=html
```

### Test Coverage

The test suite covers:
- Token generation and validation
- Email verification flows
- Password reset operations
- Rate limiting
- Security features
- Error handling
- Edge cases

## Monitoring and Maintenance

### Token Cleanup

Set up automated cleanup of expired tokens:

```sql
-- Manual cleanup
SELECT cleanup_expired_auth_tokens();

-- Automated cleanup (if using pg_cron)
SELECT cron.schedule('cleanup-expired-tokens', '0 2 * * *', 'SELECT cleanup_expired_auth_tokens();');
```

### Security Monitoring

Monitor authentication events:

```sql
-- Failed authentication attempts
SELECT * FROM auth_audit_log 
WHERE success = false 
ORDER BY created_at DESC;

-- Suspicious activity by IP
SELECT ip_address, COUNT(*) as attempts
FROM auth_audit_log 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address 
HAVING COUNT(*) > 10;
```

### Performance Monitoring

Monitor token table performance:

```sql
-- Token usage statistics
SELECT 
    token_type,
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN used_at IS NOT NULL THEN 1 END) as used_tokens,
    COUNT(CASE WHEN expires_at < NOW() THEN 1 END) as expired_tokens
FROM auth_tokens 
GROUP BY token_type;
```

## Troubleshooting

### Common Issues

#### Email Delivery Failures
- Check Resend API key configuration
- Verify sender email domain
- Check email service logs

#### Token Validation Errors
- Ensure tokens haven't expired
- Check token format validation
- Verify database connectivity

#### Rate Limiting Issues
- Check client IP detection
- Verify rate limit configuration
- Monitor for abuse patterns

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('backend.services.auth_service').setLevel(logging.DEBUG)
```

## Performance Considerations

### Database Optimization

- Indexes on frequently queried columns
- Regular cleanup of expired tokens
- Connection pooling for database sessions

### Caching Strategy

- Cache user verification status
- Redis-based rate limiting
- Session token caching

### Scalability

- Horizontal scaling with load balancers
- Database read replicas for auth queries
- Async email processing for high volume

## Compliance and Privacy

### GDPR Compliance

- User consent for email communications
- Right to be forgotten implementation
- Data retention policies for audit logs

### Security Standards

- OWASP Top 10 compliance
- Secure password storage (PBKDF2)
- TLS encryption for all communications
- Regular security audits

## Future Enhancements

### Planned Features

- Two-factor authentication (2FA)
- Social login integration
- Advanced fraud detection
- Biometric authentication
- Multi-tenant authentication

### API Improvements

- GraphQL support
- Webhook notifications
- Real-time status updates
- Mobile SDK integration

## Support and Maintenance

### Documentation Updates

This documentation is maintained by the MINGUS development team. For updates or corrections, please contact the development team.

### Security Issues

For security-related issues, please follow the responsible disclosure policy and contact security@mingusapp.com.

### Feature Requests

Submit feature requests through the development team's issue tracking system.

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintained By**: MINGUS Development Team
