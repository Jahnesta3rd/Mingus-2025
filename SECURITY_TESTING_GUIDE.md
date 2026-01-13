# Backend Security Testing Guide

**Last Updated:** January 13, 2026

This guide provides comprehensive information about all backend security tests available for the Mingus application.

---

## Overview

The Mingus backend includes a comprehensive security testing suite that covers:

1. **Comprehensive Backend Security Tests** - Authentication, authorization, CSRF, SQL injection, XSS, security headers, and more
2. **Rate Limiting Tests** - Rate limit enforcement, headers, and reset behavior
3. **Input Validation & Sanitization Tests** - SQL injection, XSS, command injection, path traversal, and input validation
4. **CORS Configuration Tests** - CORS preflight, headers, origin validation, and unauthorized origin blocking

---

## Prerequisites

### 1. Install Dependencies

The test scripts require the `requests` library. Install it using one of these methods:

**Option A: Using pip (if not in externally-managed environment)**
```bash
pip install requests
```

**Option B: Using a virtual environment (recommended)**
```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

**Option C: Install from requirements**
```bash
pip install -r test_requirements.txt
```

### 2. Backend Server Must Be Running

The tests require the backend server to be running. Start it with:

```bash
python app.py
# or
flask run
```

The default test URL is `http://localhost:5000`. You can change this with the `--base-url` flag.

---

## Running Security Tests

### Option 1: Run All Tests (Recommended)

Use the comprehensive test runner to execute all security test suites:

```bash
python run_all_security_tests.py
```

**Options:**
- `--base-url URL` - Set the backend URL (default: http://localhost:5000)
- `--skip-rate-reset` - Skip the rate limit reset test (saves 60 seconds)

**Example:**
```bash
python run_all_security_tests.py --base-url http://localhost:5000 --skip-rate-reset
```

### Option 2: Run Individual Test Suites

#### 1. Comprehensive Backend Security Tests

Tests authentication, authorization, CSRF, SQL injection, XSS, security headers, session security, API endpoint security, and data protection.

```bash
python comprehensive_backend_security_tests.py --base-url http://localhost:5000
```

**Test Coverage:**
- ✅ Authentication & Authorization (JWT tokens, protected endpoints)
- ✅ CSRF Protection (state-changing endpoints)
- ✅ SQL Injection Prevention (multiple payloads and endpoints)
- ✅ XSS Protection (script injection, event handlers, encoded payloads)
- ✅ Input Validation (email, length, type validation)
- ✅ Rate Limiting (request limits)
- ✅ Security Headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
- ✅ Session Security (HttpOnly, Secure flags)
- ✅ API Endpoint Security (information disclosure)
- ✅ Data Protection (sensitive data in error messages)

**Output:**
- Console output with colored results
- JSON file: `backend_security_test_results_YYYYMMDD_HHMMSS.json`

#### 2. Rate Limiting Tests

Tests rate limiting functionality including limits, headers, reset behavior, and concurrent requests.

```bash
python test_rate_limiting.py --base-url http://localhost:5000 --limit 100
```

**Options:**
- `--base-url URL` - Backend URL
- `--limit N` - Expected rate limit per minute (default: 100)
- `--skip-reset` - Skip the rate limit reset test

**Test Coverage:**
- ✅ Basic rate limiting (request limits)
- ✅ Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
- ✅ Rate limit exceeded responses (429 status)
- ✅ Different endpoints
- ✅ Rate limit reset (time window)
- ✅ Concurrent requests
- ✅ IP-based limiting

**Output:**
- Console output with colored results
- JSON file: `rate_limiting_test_results_YYYYMMDD_HHMMSS.json`

#### 3. Input Validation & Sanitization Tests

Tests comprehensive input validation including SQL injection, XSS, command injection, path traversal, and type validation.

```bash
python test_input_validation_sanitization.py --base-url http://localhost:5000
```

**Test Coverage:**
- ✅ SQL Injection (30+ payloads)
- ✅ XSS (Cross-Site Scripting) (20+ payloads)
- ✅ Command Injection (Unix and Windows)
- ✅ Path Traversal (multiple encoding methods)
- ✅ NoSQL Injection
- ✅ LDAP Injection
- ✅ Template Injection
- ✅ XXE (XML External Entity)
- ✅ Input Type Validation
- ✅ Length Limits

**Output:**
- Console output with colored results
- JSON file: `input_validation_test_results_YYYYMMDD_HHMMSS.json`

#### 4. CORS Configuration Tests

Tests CORS configuration including preflight requests, headers, origin validation, and unauthorized origin blocking.

```bash
python verify_cors_configuration.py --base-url http://localhost:5000
```

**Test Coverage:**
- ✅ CORS Preflight (OPTIONS) requests
- ✅ CORS headers in actual requests
- ✅ Allowed origins validation
- ✅ Allowed methods validation
- ✅ Allowed headers validation
- ✅ Credentials support
- ✅ Exposed headers
- ✅ Unauthorized origin blocking

**Output:**
- Console output with colored results
- JSON file: `cors_verification_results_YYYYMMDD_HHMMSS.json`

---

## Test Results

### Result Status

Each test can have one of three statuses:

- ✅ **PASS** - Test passed, security feature working correctly
- ❌ **FAIL** - Test failed, security issue detected
- ⚠️ **WARN** - Warning, may need attention but not critical

### Output Files

All test suites generate JSON result files with detailed information:

- `backend_security_test_results_YYYYMMDD_HHMMSS.json`
- `rate_limiting_test_results_YYYYMMDD_HHMMSS.json`
- `input_validation_test_results_YYYYMMDD_HHMMSS.json`
- `cors_verification_results_YYYYMMDD_HHMMSS.json`
- `all_security_tests_results_YYYYMMDD_HHMMSS.json` (combined results)

### Reading Results

The JSON files contain:
- Test summary (total, passed, failed, warnings)
- Individual test results with details
- Timestamps and configuration
- Response data and status codes

---

## Security Features Tested

### 1. Authentication & Authorization

**Tests:**
- Protected endpoints require authentication
- Invalid JWT tokens are rejected
- Authorization bypass attempts are blocked

**Expected Behavior:**
- Protected endpoints return 401 (Unauthorized) without valid tokens
- Invalid tokens are rejected
- User ID manipulation attempts are blocked

### 2. CSRF Protection

**Tests:**
- State-changing endpoints (POST, PUT, DELETE) require CSRF tokens
- Missing CSRF tokens result in 403 (Forbidden)

**Expected Behavior:**
- POST/PUT/DELETE requests without CSRF tokens are rejected
- Valid CSRF tokens are accepted

### 3. SQL Injection Prevention

**Tests:**
- Multiple SQL injection payloads tested
- SQL error messages should not be exposed
- Injection attempts should be rejected

**Expected Behavior:**
- SQL injection attempts return 400/422 (validation error) or 403 (forbidden)
- No SQL error messages in responses
- Database structure not exposed

### 4. XSS Protection

**Tests:**
- Script injection attempts
- Event handler injection
- Encoded payloads
- JavaScript protocol attempts

**Expected Behavior:**
- XSS payloads are sanitized or rejected
- Script tags are escaped in responses
- No executable JavaScript in responses

### 5. Input Validation

**Tests:**
- Email format validation
- Length limits
- Type validation
- Special character handling

**Expected Behavior:**
- Invalid inputs return 400 (Bad Request) or 422 (Unprocessable Entity)
- Length limits are enforced
- Type mismatches are rejected

### 6. Rate Limiting

**Tests:**
- Request limits are enforced
- Rate limit headers are present
- 429 status on limit exceeded
- Rate limit resets after time window

**Expected Behavior:**
- Requests exceeding limit return 429 (Too Many Requests)
- Rate limit headers present in responses
- Limits reset after configured time window

### 7. Security Headers

**Tests:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

**Expected Behavior:**
- All required security headers are present
- Header values match security configuration

### 8. CORS Configuration

**Tests:**
- Allowed origins are validated
- Unauthorized origins are blocked
- Preflight requests work correctly
- Credentials support is configured

**Expected Behavior:**
- Only configured origins are allowed
- Unauthorized origins are blocked
- CORS headers are present in responses

---

## Previous Test Results

Based on previous test runs:

### Comprehensive Backend Security (66% Pass Rate)
- ✅ CSRF Protection: 100% (4/4 passed)
- ✅ XSS Protection: 100% (8/8 passed)
- ✅ Security Headers: 100% (5/5 passed)
- ✅ API Endpoint Security: 100% (7/7 passed)
- ✅ Authorization Bypass: 100% (3/3 passed)
- ⚠️ Authentication: 10% (1/10 passed) - Some endpoints return 404 instead of 401
- ⚠️ SQL Injection: 67% (6/9 passed)
- ⚠️ Input Validation: 0% (0/5 passed) - Tests hit CSRF protection first
- ⚠️ Rate Limiting: 0% (0/1 passed) - May not be active on /health endpoint

### CORS Configuration (87% Pass Rate)
- ✅ Origin Validation: Working
- ✅ Unauthorized Origin Blocking: Working
- ✅ Methods: All required methods allowed
- ✅ Credentials: Enabled
- ⚠️ Headers: Minor case sensitivity warnings

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'requests'

**Solution:**
```bash
pip install requests
# or
pip install -r test_requirements.txt
```

### Issue: Connection refused / Cannot connect to backend

**Solution:**
1. Ensure backend server is running: `python app.py`
2. Check the URL matches your server: `--base-url http://localhost:5000`
3. Verify firewall/network settings

### Issue: All tests fail with 404 errors

**Solution:**
- Verify endpoint routes exist in your application
- Check that the backend server is running the correct version
- Some endpoints may not exist - this is expected for some tests

### Issue: CSRF tests fail but endpoints work in browser

**Solution:**
- CSRF protection may be disabled in development mode
- Check `FLASK_ENV` environment variable
- Verify CSRF token generation and validation

### Issue: Rate limiting tests don't trigger

**Solution:**
- Rate limiting may be disabled on public endpoints (like /health)
- Test on protected endpoints with authentication
- Verify rate limit configuration in `backend/config/security.py`

---

## Continuous Security Testing

### Recommended Testing Schedule

- **Before Deployment:** Run all test suites
- **Weekly:** Run comprehensive backend security tests
- **After Security Updates:** Run all test suites
- **After Adding New Endpoints:** Run relevant test suites

### Integration with CI/CD

You can integrate these tests into your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Security Tests
  run: |
    python run_all_security_tests.py --base-url http://localhost:5000 --skip-rate-reset
```

---

## Security Best Practices

Based on test results, ensure:

1. ✅ **All state-changing endpoints require CSRF tokens**
2. ✅ **All user inputs are validated and sanitized**
3. ✅ **SQL queries use parameterized statements**
4. ✅ **XSS payloads are sanitized before rendering**
5. ✅ **Security headers are set on all responses**
6. ✅ **Rate limiting is active on protected endpoints**
7. ✅ **CORS is configured with specific origins (not wildcard)**
8. ✅ **Authentication is required for protected endpoints**
9. ✅ **Error messages don't expose sensitive information**

---

## Additional Resources

- **Security Configuration:** `backend/config/security.py`
- **Security Middleware:** `backend/middleware/security.py`
- **CORS Configuration:** `app.py` (CORS setup)
- **Previous Test Reports:**
  - `BACKEND_SECURITY_TEST_REPORT.md`
  - `CORS_VERIFICATION_REPORT.md`
  - `CORS_VERIFICATION_SUMMARY.md`

---

## Support

For issues or questions about security testing:

1. Check the test output JSON files for detailed error information
2. Review the security configuration files
3. Verify backend server logs for additional context
4. Check previous test reports for known issues

---

**Last Test Run:** See individual JSON result files for timestamps  
**Test Coverage:** Comprehensive - All major security features tested  
**Status:** ✅ Test suites ready for execution
