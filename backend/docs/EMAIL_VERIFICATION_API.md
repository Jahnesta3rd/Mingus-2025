# Email Verification API Documentation

## Overview

The Email Verification API provides secure email verification functionality for the MINGUS application. This system ensures that users verify their email addresses before accessing certain features, enhancing security and user account integrity.

## Base URL

```
/api/email-verification
```

## Authentication

Most endpoints require authentication. Include your session cookie or authentication token in requests.

## Endpoints

### 1. Send Verification Email

**POST** `/api/email-verification/send`

Sends a verification email to the specified email address.

#### Request Body

```json
{
  "email": "user@example.com",
  "verification_type": "signup"
}
```

#### Parameters

- `email` (string, required): The email address to verify
- `verification_type` (string, required): Type of verification
  - `signup`: New user registration
  - `email_change`: Email address change
  - `password_reset`: Password reset

#### Response

**Success (200)**
```json
{
  "message": "Verification email sent successfully",
  "verification_type": "signup",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

**Error (400)**
```json
{
  "error": "Invalid email format"
}
```

**Error (429)**
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many verification requests. Please try again later."
}
```

#### Rate Limiting

- **IP-based**: 5 requests per hour per IP address
- **User-based**: 3 requests per hour per authenticated user

---

### 2. Verify Email

**POST** `/api/email-verification/verify`

Verifies an email address using a verification token.

#### Request Body

```json
{
  "token": "verification_token_here",
  "verification_type": "signup"
}
```

#### Parameters

- `token` (string, required): The verification token from the email
- `verification_type` (string, required): Type of verification being performed

#### Response

**Success (200)**
```json
{
  "message": "Email verified successfully",
  "user": {
    "id": "user_uuid",
    "email": "user@example.com",
    "email_verified": true
  },
  "verification_type": "signup"
}
```

**Error (400)**
```json
{
  "error": "Invalid or expired token"
}
```

**Error (404)**
```json
{
  "error": "Verification not found"
}
```

---

### 3. Resend Verification Email

**POST** `/api/email-verification/resend`

Resends a verification email to the user.

#### Request Body

```json
{
  "email": "user@example.com",
  "verification_type": "signup"
}
```

#### Parameters

- `email` (string, required): The email address to resend verification to
- `verification_type` (string, required): Type of verification

#### Response

**Success (200)**
```json
{
  "message": "Verification email resent successfully",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

**Error (429)**
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many resend attempts. Please try again later."
}
```

#### Rate Limiting

- **Daily limit**: 3 resend attempts per day per user
- **Cooldown**: 2 hours between resend attempts

---

### 4. Email Change Verification

**POST** `/api/email-verification/change-email/initiate`

Initiates an email change verification process.

#### Request Body

```json
{
  "new_email": "newemail@example.com"
}
```

#### Parameters

- `new_email` (string, required): The new email address

#### Response

**Success (200)**
```json
{
  "message": "Email change verification initiated",
  "verification_sent": true,
  "expires_at": "2024-01-15T10:30:00Z"
}
```

**Error (400)**
```json
{
  "error": "Invalid email format"
}
```

---

**POST** `/api/email-verification/change-email/complete`

Completes the email change verification process.

#### Request Body

```json
{
  "token": "verification_token_here",
  "new_email": "newemail@example.com"
}
```

#### Parameters

- `token` (string, required): The verification token from the email
- `new_email` (string, required): The new email address being verified

#### Response

**Success (200)**
```json
{
  "message": "Email changed successfully",
  "user": {
    "id": "user_uuid",
    "email": "newemail@example.com",
    "email_verified": true
  }
}
```

---

### 5. Get Verification Status

**GET** `/api/email-verification/status`

Gets the verification status for the current user.

#### Response

**Success (200)**
```json
{
  "success": true,
  "verification": {
    "verified": true,
    "email": "user@example.com"
  }
}
```

**Not Verified (200)**
```json
{
  "success": true,
  "verification": {
    "verified": false,
    "email": "user@example.com",
    "pending": true,
    "expires_at": "2024-01-15T10:30:00Z",
    "verification_type": "signup",
    "resend_available": true
  }
}
```

---

### 6. Admin Endpoints

#### Get All Verifications

**GET** `/api/email-verification/admin/all`

*Requires admin privileges*

Returns all email verification records.

#### Response

**Success (200)**
```json
{
  "success": true,
  "verifications": [
    {
      "id": "verification_uuid",
      "user_id": "user_uuid",
      "email": "user@example.com",
      "verification_type": "signup",
      "status": "pending",
      "created_at": "2024-01-15T09:00:00Z",
      "expires_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get User Verifications

**GET** `/api/email-verification/admin/user/{user_id}`

*Requires admin privileges*

Returns verification records for a specific user.

#### Response

**Success (200)**
```json
{
  "success": true,
  "verifications": [
    {
      "id": "verification_uuid",
      "user_id": "user_uuid",
      "email": "user@example.com",
      "verification_type": "signup",
      "status": "pending",
      "created_at": "2024-01-15T09:00:00Z",
      "expires_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `INVALID_SESSION` | Invalid or expired session |
| `EMAIL_VERIFICATION_REQUIRED` | Email verification required |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `VERIFICATION_ERROR` | Verification process error |
| `INVALID_CSRF_TOKEN` | Invalid CSRF token |

## Rate Limiting

The API implements comprehensive rate limiting to prevent abuse:

### IP-based Limits
- **Verification requests**: 5 per hour per IP
- **Resend requests**: 3 per hour per IP

### User-based Limits
- **Verification attempts**: 3 per hour per authenticated user
- **Resend attempts**: 3 per day per user
- **Failed attempts**: 5 before temporary lockout

### Cooldown Periods
- **Resend cooldown**: 2 hours between resend attempts
- **Lockout duration**: 2 hours after max failed attempts

## Security Features

### Token Security
- **Cryptographic tokens**: HMAC-SHA256 with 64-byte secrets
- **Token expiration**: 24 hours from creation
- **Constant-time comparison**: Prevents timing attacks

### Protection Against
- **Email enumeration**: Rate limiting and consistent responses
- **Brute force attacks**: Account lockout after failed attempts
- **Token reuse**: Single-use verification tokens
- **CSRF attacks**: CSRF token validation

### Audit Logging
- **Comprehensive logging**: All verification activities logged
- **Security events**: Suspicious activity detection
- **IP tracking**: IP address and User-Agent logging
- **Geolocation**: Optional geographic tracking

## Integration with Authentication

### Registration Flow
1. User registers with email and password
2. Account created with `email_verified: false`
3. Verification email sent automatically
4. User must verify email to access full features

### Login Flow
1. User logs in with credentials
2. System checks email verification status
3. If not verified, shows verification notice
4. User can request verification resend

### Protected Features
- **Email verification required**: Certain features require verified email
- **Optional authentication**: Some endpoints work with or without verification
- **Admin access**: Administrative functions require verified email

## Frontend Integration

### Verification Status Check
```javascript
// Check if user's email is verified
const response = await fetch('/api/auth/verification-status');
const data = await response.json();

if (!data.verification.verified) {
  // Show verification notice
  showVerificationBanner(data.verification);
}
```

### Sending Verification Email
```javascript
// Send verification email
const response = await fetch('/api/email-verification/send', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: userEmail,
    verification_type: 'signup'
  })
});
```

### Verifying Email
```javascript
// Verify email with token
const response = await fetch('/api/email-verification/verify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token: verificationToken,
    verification_type: 'signup'
  })
});
```

## Monitoring and Metrics

### Health Checks
- **Endpoint health**: `/api/email-verification/health`
- **Service status**: Database and email service connectivity
- **Rate limit status**: Current rate limiting state

### Metrics
- **Success rates**: Verification success/failure ratios
- **Response times**: API endpoint performance
- **Rate limiting**: Number of rate-limited requests
- **Security events**: Suspicious activity detection

### Logging
- **Request logging**: All API requests logged with context
- **Security logging**: Suspicious activity and rate limiting
- **Error logging**: Detailed error information for debugging
- **Audit logging**: Complete audit trail of verification activities

## Troubleshooting

### Common Issues

#### Rate Limit Exceeded
- **Cause**: Too many requests from same IP/user
- **Solution**: Wait for rate limit window to reset
- **Prevention**: Implement exponential backoff in frontend

#### Token Expired
- **Cause**: Verification token older than 24 hours
- **Solution**: Request new verification email
- **Prevention**: Prompt users to verify email promptly

#### Email Not Received
- **Cause**: Email service issues or spam filtering
- **Solution**: Check spam folder, request resend
- **Prevention**: Use verified sender domains

### Debug Information
- **Request ID**: Each request gets unique ID for tracking
- **Rate limit headers**: Response headers show current limits
- **Verification context**: Detailed verification status information
- **Error details**: Comprehensive error messages with codes

## Support

For technical support or questions about the Email Verification API:

- **Email**: support@mingus.app
- **Documentation**: [API Documentation](https://docs.mingus.app)
- **Status Page**: [Service Status](https://status.mingus.app)

---

*Last updated: January 2024*
*Version: 1.0.0*
