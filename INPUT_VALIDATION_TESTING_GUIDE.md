# Input Validation and Sanitization Testing Guide

**Date:** January 12, 2026  
**Status:** ✅ **COMPREHENSIVE TEST SUITE CREATED**

---

## Overview

This guide provides best practices and recommendations for testing input validation and sanitization in the Mingus application. Input validation is critical for preventing security vulnerabilities like SQL injection, XSS, command injection, and more.

---

## Best Practices for Testing Input Validation

### 1. **Comprehensive Payload Coverage**

Test with a wide variety of payloads covering:
- **Classic attacks:** Well-known attack patterns
- **Encoded variations:** URL encoding, HTML entities, Unicode
- **Obfuscated payloads:** Mixed case, whitespace, comments
- **Edge cases:** Null bytes, extremely long strings, special characters

### 2. **Multi-Layer Testing**

Test at multiple layers:
- **Frontend validation:** Client-side checks (can be bypassed)
- **Backend validation:** Server-side validation (critical)
- **Database layer:** Parameterized queries (essential)
- **Output encoding:** Proper escaping in responses

### 3. **Context-Aware Testing**

Test different input contexts:
- **URL parameters:** Query strings, path parameters
- **Request body:** JSON, form data, XML
- **Headers:** Custom headers, cookies
- **File uploads:** Filenames, file content

### 4. **Positive and Negative Testing**

- **Positive tests:** Valid inputs should work
- **Negative tests:** Invalid/malicious inputs should be rejected
- **Boundary tests:** Test limits (max length, min/max values)

---

## Test Categories

### 1. SQL Injection Testing

**What to Test:**
- Classic SQL injection patterns
- Time-based SQL injection
- Boolean-based SQL injection
- Union-based SQL injection
- Error-based SQL injection
- Encoded SQL injection

**Expected Behavior:**
- Input should be rejected or sanitized
- No SQL error messages in responses
- Parameterized queries should be used
- Database should not execute injected SQL

**Test Payloads:**
```python
"'; DROP TABLE users; --"
"1' OR '1'='1"
"admin'--"
"1' UNION SELECT * FROM users--"
```

### 2. XSS (Cross-Site Scripting) Testing

**What to Test:**
- Script tag injection
- Event handler injection
- JavaScript protocol injection
- HTML entity encoding
- CSS injection
- Encoded XSS payloads

**Expected Behavior:**
- HTML tags should be escaped or removed
- JavaScript should not execute
- Output should be properly encoded
- Content Security Policy should block inline scripts

**Test Payloads:**
```python
"<script>alert('XSS')</script>"
"<img src=x onerror=alert('XSS')>"
"javascript:alert('XSS')"
"&#60;script&#62;alert('XSS')&#60;/script&#62;"
```

### 3. Command Injection Testing

**What to Test:**
- Unix command injection (`;`, `|`, `&&`, `` ` ``, `$()`)
- Windows command injection (`&`, `|`, `&&`, `||`)
- Command chaining
- Encoded command injection

**Expected Behavior:**
- Commands should not execute
- No command output in responses
- Input should be validated/sanitized
- System commands should not be accessible

**Test Payloads:**
```python
"; ls"
"| cat /etc/passwd"
"&& rm -rf /"
"`ls`"
"$(ls)"
```

### 4. Path Traversal Testing

**What to Test:**
- Directory traversal (`../`, `..\\`)
- Encoded path traversal
- Double encoding
- Unicode encoding
- Null byte injection

**Expected Behavior:**
- Path traversal should be blocked
- Access to sensitive files should be denied
- File paths should be validated
- Absolute paths should be restricted

**Test Payloads:**
```python
"../../../etc/passwd"
"..\\..\\..\\windows\\system32\\config\\sam"
"%2e%2e%2f%2e%2e%2fetc%2fpasswd"
```

### 5. Input Type Validation

**What to Test:**
- Type mismatches (string vs number)
- Invalid data types
- Null/undefined values
- Array/object type validation

**Expected Behavior:**
- Type validation should reject wrong types
- Clear error messages for type errors
- Proper type conversion where appropriate

**Test Cases:**
```python
{'email': 123}  # Should reject
{'age': 'not_a_number'}  # Should reject
{'input': None}  # Should handle gracefully
```

### 6. Length Limit Testing

**What to Test:**
- Maximum length limits
- Minimum length requirements
- Extremely long inputs
- Empty/null inputs

**Expected Behavior:**
- Length limits should be enforced
- Clear error messages for length violations
- No buffer overflows
- Proper truncation or rejection

**Test Cases:**
```python
{'email': 'a' * 10000}  # Should reject or truncate
{'input': ''}  # Should validate minimum length
```

### 7. Special Character Handling

**What to Test:**
- SQL special characters (`'`, `"`, `;`, `--`)
- HTML special characters (`<`, `>`, `&`, `"`)
- Shell special characters (`|`, `&`, `;`, `` ` ``)
- Unicode characters
- Control characters

**Expected Behavior:**
- Special characters should be escaped or sanitized
- No special characters should break functionality
- Proper encoding in output

---

## Testing Methodology

### Phase 1: Automated Testing

1. **Run Comprehensive Test Suite**
   ```bash
   python test_input_validation_sanitization.py --base-url http://localhost:5000
   ```

2. **Review Results**
   - Check for failed tests
   - Analyze vulnerable endpoints
   - Review payloads that bypassed validation

3. **Fix Issues**
   - Update validation logic
   - Add missing sanitization
   - Fix vulnerable endpoints

### Phase 2: Manual Testing

1. **Test Real User Scenarios**
   - Test with actual user inputs
   - Test edge cases in UI
   - Test file uploads

2. **Test API Endpoints Directly**
   ```bash
   # Test SQL injection
   curl -X POST http://localhost:5000/api/assessments \
     -H "Content-Type: application/json" \
     -d '{"email": "test'\'' OR 1=1--"}'
   
   # Test XSS
   curl -X POST http://localhost:5000/api/assessments \
     -H "Content-Type: application/json" \
     -d '{"firstName": "<script>alert(\"XSS\")</script>"}'
   ```

3. **Test with Burp Suite / OWASP ZAP**
   - Automated vulnerability scanning
   - Manual penetration testing
   - Fuzzing

### Phase 3: Code Review

1. **Review Validation Logic**
   - Check all input validation functions
   - Verify sanitization is applied
   - Ensure parameterized queries are used

2. **Review Error Handling**
   - Check error messages don't leak information
   - Verify proper error responses
   - Ensure no stack traces in production

---

## Test Suite Features

### Comprehensive Payload Database

The test suite includes payloads for:
- **SQL Injection:** 30+ payloads
- **XSS:** 25+ payloads
- **Command Injection:** 15+ payloads
- **Path Traversal:** 10+ payloads
- **NoSQL Injection:** 10+ payloads
- **LDAP Injection:** 10+ payloads
- **Template Injection:** 5+ payloads
- **XXE:** 5+ payloads

### Automated Detection

The test suite automatically detects:
- SQL error messages in responses
- Unescaped XSS payloads in responses
- Command output in responses
- Sensitive file content in responses
- Type validation failures
- Length limit violations

### Detailed Reporting

- **Categorized Results:** Grouped by attack type
- **Payload Tracking:** Records exact payloads tested
- **Response Analysis:** Analyzes response for vulnerabilities
- **JSON Export:** Detailed results for further analysis

---

## Recommendations

### Immediate Actions

1. **Run Test Suite**
   ```bash
   python test_input_validation_sanitization.py --base-url http://localhost:5000
   ```

2. **Review Results**
   - Identify vulnerable endpoints
   - Prioritize fixes by severity
   - Document findings

3. **Fix Critical Issues**
   - SQL injection vulnerabilities (CRITICAL)
   - Command injection vulnerabilities (CRITICAL)
   - XSS vulnerabilities (HIGH)
   - Path traversal vulnerabilities (HIGH)

### Short-Term Improvements

1. **Add Input Validation Middleware**
   - Centralized validation
   - Consistent validation rules
   - Reusable validation functions

2. **Implement Parameterized Queries**
   - Use SQLAlchemy ORM
   - Use parameterized queries for raw SQL
   - Never use string concatenation for SQL

3. **Add Output Encoding**
   - HTML entity encoding
   - JavaScript encoding
   - URL encoding
   - Context-aware encoding

### Long-Term Improvements

1. **Implement Content Security Policy (CSP)**
   - Prevent XSS attacks
   - Restrict script execution
   - Control resource loading

2. **Add Input Validation Library**
   - Use established libraries (e.g., `marshmallow`, `pydantic`)
   - Consistent validation rules
   - Type-safe validation

3. **Regular Security Audits**
   - Quarterly security testing
   - Penetration testing
   - Code reviews

---

## Testing Checklist

### SQL Injection
- [ ] Test all user input fields
- [ ] Test URL parameters
- [ ] Test JSON request bodies
- [ ] Verify parameterized queries
- [ ] Check for SQL error messages
- [ ] Test time-based SQL injection
- [ ] Test union-based SQL injection

### XSS
- [ ] Test all text input fields
- [ ] Test output encoding
- [ ] Test script tag injection
- [ ] Test event handler injection
- [ ] Test JavaScript protocol
- [ ] Test encoded XSS payloads
- [ ] Verify CSP headers

### Command Injection
- [ ] Test command execution endpoints
- [ ] Test file upload endpoints
- [ ] Test system command inputs
- [ ] Verify command output not in responses
- [ ] Test command chaining

### Path Traversal
- [ ] Test file access endpoints
- [ ] Test file upload endpoints
- [ ] Test path parameters
- [ ] Verify access to sensitive files blocked
- [ ] Test encoded path traversal

### Input Type Validation
- [ ] Test type mismatches
- [ ] Test null/undefined values
- [ ] Test array/object validation
- [ ] Verify clear error messages

### Length Limits
- [ ] Test maximum length
- [ ] Test minimum length
- [ ] Test extremely long inputs
- [ ] Verify proper truncation/rejection

---

## Tools and Resources

### Testing Tools

1. **OWASP ZAP**
   - Automated vulnerability scanner
   - Manual penetration testing
   - Fuzzing capabilities

2. **Burp Suite**
   - Web vulnerability scanner
   - Manual testing tools
   - Intruder for fuzzing

3. **SQLMap**
   - Automated SQL injection testing
   - Database fingerprinting
   - Data extraction

### Payload Resources

1. **OWASP Testing Guide**
   - Comprehensive testing methodology
   - Payload examples
   - Best practices

2. **PayloadsAllTheThings**
   - Large collection of payloads
   - Various attack vectors
   - Regular updates

3. **PortSwigger Web Security Academy**
   - Interactive tutorials
   - Practice labs
   - Latest attack techniques

---

## Conclusion

Input validation and sanitization testing is critical for application security. The comprehensive test suite provides:

- ✅ **Automated Testing:** Run tests quickly and consistently
- ✅ **Comprehensive Coverage:** Test multiple attack vectors
- ✅ **Detailed Reporting:** Identify and fix vulnerabilities
- ✅ **Best Practices:** Follow industry standards

**Next Steps:**
1. Run the test suite
2. Review and fix vulnerabilities
3. Implement improvements
4. Schedule regular testing

---

**Test Suite:** `test_input_validation_sanitization.py`  
**Status:** ✅ **READY FOR USE**
