# Phone Verification Endpoints

This document describes the phone verification endpoints for the Mingus financial wellness app onboarding process.

## Overview

The phone verification system provides secure SMS-based verification for user phone numbers during the onboarding process. The system includes:

- **Code Generation**: 6-digit numeric codes
- **Rate Limiting**: Maximum attempts and resend limits
- **Security**: Hashed code storage
- **Expiration**: 10-minute code validity
- **Database Integration**: PostgreSQL with phone_verification table

## Endpoints

### 1. Send Verification Code

**Endpoint:** `POST /api/onboarding/send-verification`

**Description:** Sends a verification code to the provided phone number.

**Authentication:** Required (user must be logged in)

**Request Body:**
```json
{
    "phone_number": "+1234567890"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Verification code sent successfully",
    "expires_at": "2024-01-01T12:10:00",
    "resend_count": 1
}
```

**Response (Error - 400/401/500):**
```json
{
    "success": false,
    "error": "Error message here"
}
```

**Error Cases:**
- `401`: User not authenticated
- `400`: Invalid phone number format
- `400`: Maximum resend attempts reached
- `400`: Code already sent, please wait
- `500`: Verification service not available
- `500`: Internal server error

### 2. Verify Phone Number

**Endpoint:** `POST /api/onboarding/verify-phone`

**Description:** Verifies the provided code against the stored verification code.

**Authentication:** Required (user must be logged in)

**Request Body:**
```json
{
    "phone_number": "+1234567890",
    "verification_code": "123456"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Phone number verified successfully"
}
```

**Response (Error - 400/401/500):**
```json
{
    "success": false,
    "error": "Error message here",
    "remaining_attempts": 2
}
```

**Error Cases:**
- `401`: User not authenticated
- `400`: Phone number and verification code required
- `400`: No verification code found
- `400`: Verification code expired
- `400`: Maximum verification attempts reached
- `400`: Invalid verification code
- `500`: Verification service not available
- `500`: Internal server error

### 3. Resend Verification Code

**Endpoint:** `POST /api/onboarding/resend-verification`

**Description:** Resends a verification code to the provided phone number.

**Authentication:** Required (user must be logged in)

**Request Body:**
```json
{
    "phone_number": "+1234567890"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Verification code resent successfully",
    "expires_at": "2024-01-01T12:10:00",
    "resend_count": 2
}
```

**Response (Error - 400/401/500):**
```json
{
    "success": false,
    "error": "Error message here"
}
```

**Error Cases:**
- `401`: User not authenticated
- `400`: Phone number required
- `400`: No verification code found
- `400`: Maximum resend attempts reached
- `400`: Please wait before requesting new code
- `500`: Verification service not available
- `500`: Internal server error

## Configuration

### Rate Limiting
- **Max Attempts**: 3 verification attempts per code
- **Max Resends**: 3 resend attempts per phone number
- **Code Expiry**: 10 minutes
- **Resend Cooldown**: 1 minute between resends

### Phone Number Format
- **Input**: Accepts various formats (e.g., "123-456-7890", "(123) 456-7890", "+1 123 456 7890")
- **Storage**: Normalized to E.164 format (e.g., "+11234567890")
- **Validation**: Basic E.164 pattern validation

## Database Schema

The verification system uses the `phone_verification` table:

```sql
CREATE TABLE phone_verification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    verification_code_hash VARCHAR(128) NOT NULL,
    code_sent_at TIMESTAMPTZ DEFAULT NOW(),
    code_expires_at TIMESTAMPTZ NOT NULL,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    status verification_status DEFAULT 'pending',
    method verification_method DEFAULT 'sms',
    last_attempt_at TIMESTAMPTZ,
    fallback_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT phone_verification_user_phone_unique UNIQUE (user_id, phone_number)
);
```

## Security Features

1. **Code Hashing**: Verification codes are hashed using SHA-256 before storage
2. **Rate Limiting**: Prevents abuse through attempt and resend limits
3. **Expiration**: Codes automatically expire after 10 minutes
4. **Unique Constraints**: One active verification per user/phone combination
5. **Audit Trail**: All attempts are logged with timestamps

## Integration with Onboarding Flow

The verification step is integrated into the onboarding flow:

1. **Profile Step**: User enters phone number
2. **Verification Step**: User verifies phone number with SMS code
3. **Preferences Step**: User continues with onboarding

The verification step updates the onboarding progress when successful:

```python
current_app.onboarding_service.update_onboarding_progress(
    user_id=user_id,
    step_name='verification',
    is_completed=True,
    responses={'phone_number': phone_number, 'verified_at': datetime.utcnow().isoformat()}
)
```

## SMS Service Integration

**Current State**: SMS simulation (logs to console)

**Production Integration**: Replace `_send_sms_simulation()` method with actual SMS service:

```python
# Example with Twilio
from twilio.rest import Client

def _send_sms_actual(self, phone_number: str, code: str) -> None:
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"Your Mingus verification code is: {code}",
        from_=twilio_phone_number,
        to=phone_number
    )
```

**Recommended SMS Services:**
- Twilio
- AWS SNS
- SendGrid
- MessageBird

## Testing

Use the provided test script to verify endpoints:

```bash
python test_verification_endpoints.py
```

**Note**: Tests require authentication and a running Flask server.

## Error Handling

All endpoints include comprehensive error handling:

- **Validation Errors**: Invalid phone numbers, missing fields
- **Rate Limiting**: Too many attempts or resends
- **Authentication**: User not logged in
- **Database Errors**: Connection issues, constraint violations
- **Service Errors**: SMS service failures

## Monitoring

The system logs all verification activities:

- Code generation and sending
- Verification attempts (success/failure)
- Rate limiting events
- Database operations
- SMS service interactions

Use these logs for monitoring and debugging verification issues. 