# CSRF Protection Testing Suite

## Overview

This comprehensive CSRF (Cross-Site Request Forgery) protection testing suite is designed to thoroughly test the security of the MINGUS application against CSRF attacks. The testing covers all critical areas where CSRF protection is essential.

## Features

### 🔒 Financial Transaction Endpoints CSRF Protection
- Tests payment processing endpoints
- Validates subscription management endpoints
- Checks banking integration endpoints
- Ensures secure financial profile endpoints

### 📝 Form Submissions Security
- Tests all form submission endpoints
- Validates CSRF token requirements
- Checks form data integrity
- Ensures proper token validation

### 🔌 API Endpoint Protection
- Tests general API endpoints
- Validates state-changing operations
- Checks authentication requirements
- Ensures proper CSRF token handling

### 🔄 State-Changing Operations Security
- Tests user profile updates
- Validates assessment submissions
- Checks communication preferences
- Ensures secure data modifications

### 🌐 Cross-Origin Request Handling
- Tests malicious origin detection
- Validates CORS policy enforcement
- Checks referer header validation
- Ensures proper origin verification

### 🔄 Token Validation and Rotation
- Tests token generation uniqueness
- Validates token expiration handling
- Checks token signature verification
- Ensures proper token rotation

### ⚡ Concurrent Request Testing
- Tests CSRF protection under load
- Validates race condition handling
- Checks concurrent token usage
- Ensures thread safety

## Installation

### Prerequisites
- Python 3.8 or higher
- Access to the MINGUS application
- Network connectivity to the application endpoints

### Setup

1. **Install Dependencies**
   ```bash
   python run_csrf_tests.py --install-deps
   ```

2. **Manual Installation (if needed)**
   ```bash
   pip install -r requirements-csrf-testing.txt
   ```

## Usage

### Basic Usage

```bash
python run_csrf_tests.py --base-url http://localhost:5000 --secret-key your-secret-key
```

### Advanced Usage

```bash
python run_csrf_tests.py \
  --base-url https://your-app.com \
  --secret-key your-secret-key \
  --timeout 60 \
  --concurrent 10
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--base-url` | Base URL of the application | Required |
| `--secret-key` | Secret key for CSRF token generation | Required |
| `--timeout` | Request timeout in seconds | 30 |
| `--concurrent` | Number of concurrent requests | 5 |
| `--install-deps` | Install required dependencies | False |

## Test Categories

### 1. Financial Transaction Endpoints

Tests the following endpoints for CSRF protection:
- `/api/payment/customers`
- `/api/payment/subscriptions`
- `/api/payment/process-payment`
- `/api/secure/financial-profile`
- `/api/banking/connect-account`
- `/api/banking/transfer-funds`
- `/api/subscription/upgrade`
- `/api/subscription/cancel`

**Test Scenarios:**
- Request without CSRF token (should be rejected)
- Request with invalid CSRF token (should be rejected)
- Request with expired CSRF token (should be rejected)
- Request with valid CSRF token (should be accepted if authenticated)

### 2. Form Submissions Security

Tests form submission endpoints:
- `/api/onboarding/complete`
- `/api/goals/set`
- `/api/questionnaire/submit`
- `/api/health/update-profile`

**Test Scenarios:**
- Form submission without CSRF token
- Form submission with invalid token
- Form submission with valid token

### 3. API Endpoint Protection

Tests general API endpoints:
- `/api/user/profile`
- `/api/assessment/submit`
- `/api/analytics/export`
- `/api/communication/send`
- `/api/admin/users`

### 4. State-Changing Operations

Tests operations that modify application state:
- User profile updates
- Assessment submissions
- Communication preferences
- Banking account management
- Analytics data export
- Admin user management

### 5. Cross-Origin Request Handling

Tests against malicious origins:
- `https://malicious-site.com`
- `https://evil.com`
- `http://localhost:8080`
- `https://attacker.com`

**Test Scenarios:**
- Cross-origin requests with valid CSRF tokens
- Origin header validation
- Referer header validation
- CORS policy enforcement

### 6. Token Validation and Rotation

Tests CSRF token mechanisms:
- Token generation uniqueness
- Token validation logic
- Token expiration handling
- Token signature verification
- Token rotation policies

### 7. Concurrent Request Testing

Tests CSRF protection under concurrent load:
- Multiple simultaneous requests
- Race condition detection
- Token reuse prevention
- Thread safety validation

## Test Results

### Success Criteria

A test is considered **PASS** if:
- ✅ Expected behavior matches actual behavior
- ✅ Security controls are working as intended
- ✅ No vulnerabilities are detected

A test is considered **FAIL** if:
- ❌ CSRF protection is bypassed
- ❌ Security controls are not working
- ❌ Vulnerabilities are detected

A test is considered **ERROR** if:
- ⚠️ Request fails due to technical issues
- ⚠️ Endpoint is not available
- ⚠️ Network connectivity issues

### Security Impact Levels

- **Critical**: CSRF protection completely bypassed
- **High**: Significant security vulnerability detected
- **Medium**: Potential security issue identified
- **Low**: Minor security concern
- **Good**: Security controls working properly

## Reports

### JSON Report

Detailed test results are saved to a JSON file:
```
csrf_protection_test_report_YYYYMMDD_HHMMSS.json
```

### Markdown Summary

A human-readable summary is generated:
```
csrf_test_summary_YYYYMMDD_HHMMSS.md
```

### Report Contents

1. **Test Summary**
   - Total tests executed
   - Pass/fail/error counts
   - Success rate percentage

2. **Security Assessment**
   - Critical issues count
   - High/medium/low issue counts
   - Overall security posture

3. **Category Breakdown**
   - Tests by category
   - Performance metrics
   - Coverage analysis

4. **Failed Tests**
   - Detailed failure information
   - Security impact assessment
   - Specific recommendations

5. **Recommendations**
   - Actionable security improvements
   - Implementation guidance
   - Best practices suggestions

## Security Recommendations

### Immediate Actions (Critical Issues)

1. **Review CSRF Protection Implementation**
   - Ensure all state-changing endpoints require CSRF tokens
   - Verify token validation logic
   - Check token generation security

2. **Implement Proper CORS Policy**
   - Configure allowed origins
   - Validate cross-origin requests
   - Implement proper CORS headers

3. **Fix Token Validation**
   - Ensure proper signature verification
   - Implement token expiration checks
   - Add session binding validation

### Medium Priority Actions

1. **Enhance Token Security**
   - Implement token rotation
   - Add rate limiting for token generation
   - Improve token entropy

2. **Add Monitoring**
   - Log CSRF validation failures
   - Monitor suspicious patterns
   - Implement alerting

3. **Improve Error Handling**
   - Provide consistent error responses
   - Avoid information disclosure
   - Implement proper logging

### Long-term Improvements

1. **Security Headers**
   - Implement Content Security Policy
   - Add X-Frame-Options
   - Configure X-Content-Type-Options

2. **Authentication Enhancement**
   - Implement multi-factor authentication
   - Add session management
   - Improve password policies

3. **Regular Testing**
   - Schedule regular CSRF testing
   - Implement automated security scans
   - Conduct penetration testing

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements-csrf-testing.txt
   ```

2. **Connection Errors**
   - Verify application is running
   - Check base URL configuration
   - Ensure network connectivity

3. **Authentication Issues**
   - Verify secret key configuration
   - Check application authentication
   - Review session management

4. **Timeout Errors**
   - Increase timeout value
   - Check application performance
   - Verify network stability

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### For Developers

1. **Always Use CSRF Tokens**
   - Include tokens in all forms
   - Validate tokens on all state-changing operations
   - Use secure token generation

2. **Implement Proper Validation**
   - Validate token signatures
   - Check token expiration
   - Verify session binding

3. **Follow Security Headers**
   - Set appropriate CORS headers
   - Implement CSP policies
   - Use secure cookie settings

### For Security Teams

1. **Regular Testing**
   - Run CSRF tests regularly
   - Monitor for new vulnerabilities
   - Keep testing tools updated

2. **Documentation**
   - Maintain security documentation
   - Update test procedures
   - Track security improvements

3. **Incident Response**
   - Have response procedures ready
   - Monitor security logs
   - Prepare communication plans

## Contributing

### Adding New Tests

1. **Identify Test Category**
   - Choose appropriate category
   - Define test objectives
   - Plan test scenarios

2. **Implement Test Logic**
   - Add test method to appropriate class
   - Implement validation logic
   - Add proper error handling

3. **Update Documentation**
   - Document new test purpose
   - Update test categories
   - Add usage examples

### Reporting Issues

1. **Create Issue Report**
   - Describe the problem
   - Include error messages
   - Provide reproduction steps

2. **Submit Fix**
   - Implement solution
   - Add tests for fix
   - Update documentation

## License

This testing suite is part of the MINGUS application security framework.

## Support

For support and questions:
- Check the troubleshooting section
- Review the documentation
- Contact the security team

---

**Note**: This testing suite is designed for security testing purposes. Always ensure you have proper authorization before testing any application.
