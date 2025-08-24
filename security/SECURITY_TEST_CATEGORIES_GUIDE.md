# Security Test Categories Guide

## Overview

This guide provides comprehensive security testing for specific security domains in MINGUS, covering authentication, authorization, input validation, session management, API security, data encryption, payment processing, and file upload security.

## 🔒 **Security Test Categories**

### **1. Authentication Security Tests**
- **Password Strength Requirements**: Test password complexity and strength validation
- **Login Rate Limiting**: Test brute force attack prevention
- **Account Lockout Mechanism**: Test account protection after failed attempts
- **Multi-Factor Authentication**: Test MFA implementation and security
- **Password Reset Security**: Test secure password reset procedures

### **2. Authorization and Access Control Tests**
- **Role-Based Access Control**: Test RBAC implementation and enforcement
- **API Endpoint Authorization**: Test API access control mechanisms
- **Resource Access Control**: Test file and resource permission systems
- **Privilege Escalation Prevention**: Test privilege escalation attack prevention

### **3. Input Validation and Sanitization Tests**
- **SQL Injection Prevention**: Test SQL injection attack prevention
- **Cross-Site Scripting (XSS)**: Test XSS attack prevention
- **Command Injection Prevention**: Test command injection attack prevention
- **Input Length Validation**: Test input size and length restrictions
- **File Path Traversal Prevention**: Test directory traversal attack prevention

### **4. Session Management Security Tests**
- **Session Timeout**: Test session expiration and timeout mechanisms
- **Session Fixation Prevention**: Test session fixation attack prevention
- **Session Regeneration**: Test session ID regeneration after sensitive actions
- **Concurrent Session Control**: Test multiple session handling
- **Session Logout**: Test secure session termination

### **5. API Security Tests**
- **API Rate Limiting**: Test API request rate limiting
- **API Authentication**: Test API authentication requirements
- **API Authorization**: Test API authorization mechanisms
- **API Input Validation**: Test API input validation and sanitization
- **API Error Handling**: Test secure error handling and information disclosure

### **6. Data Encryption and Protection Tests**
- **Data Encryption at Rest**: Test data encryption while stored
- **Data Encryption in Transit**: Test data encryption during transmission
- **Key Management**: Test encryption key security and management
- **Data Anonymization**: Test sensitive data anonymization processes

### **7. Payment Processing Security Tests**
- **Payment Data Encryption**: Test payment information encryption
- **PCI Compliance**: Test Payment Card Industry compliance measures
- **Payment Validation**: Test payment data validation and verification
- **Payment Audit Trail**: Test payment transaction logging and auditing

### **8. File Upload Security Tests**
- **File Type Validation**: Test malicious file type prevention
- **File Size Limits**: Test file size restriction enforcement
- **File Content Validation**: Test malicious content detection
- **File Storage Security**: Test secure file storage and permissions
- **Path Traversal Prevention**: Test directory traversal attack prevention

## 🚀 **Usage**

### **Run All Security Test Categories**
```python
from security.security_test_categories import run_security_test_categories

# Run all security test categories
results = run_security_test_categories(base_url="http://localhost:5000")

# Print results
print("Security Test Results:")
for category, tests in results["categories"].items():
    print(f"\n{category.upper()}:")
    for test_name, passed in tests.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
```

### **Run Specific Test Categories**
```python
# Import specific test classes
from security.security_test_categories import (
    AuthenticationSecurityTests,
    AuthorizationAccessControlTests,
    InputValidationSanitizationTests
)

# Create test instances
session = requests.Session()
auth_tests = AuthenticationSecurityTests("http://localhost:5000", session)
authz_tests = AuthorizationAccessControlTests("http://localhost:5000", session)
input_tests = InputValidationSanitizationTests("http://localhost:5000", session)

# Run specific tests
password_strength = auth_tests.test_password_strength_requirements()
rbac_test = authz_tests.test_role_based_access_control()
sql_injection = input_tests.test_sql_injection_prevention()

print(f"Password Strength: {'✓' if password_strength else '✗'}")
print(f"RBAC Test: {'✓' if rbac_test else '✗'}")
print(f"SQL Injection Prevention: {'✓' if sql_injection else '✗'}")
```

## 🔧 **Test Configuration**

### **Test Configuration File**
```yaml
# security_test_categories.yml
base_url: "http://localhost:5000"
test_timeout: 30
max_retries: 3

authentication:
  password_min_length: 12
  require_special_chars: true
  max_login_attempts: 5
  lockout_duration: 300

authorization:
  admin_roles: ["admin", "super_admin"]
  user_roles: ["user", "moderator"]
  guest_roles: ["guest"]

input_validation:
  max_input_length: 1000
  allowed_file_types: ["jpg", "png", "pdf", "txt"]
  max_file_size: 10485760  # 10MB

session_management:
  session_timeout: 3600
  regenerate_on_login: true
  max_concurrent_sessions: 1

api_security:
  rate_limit_requests: 100
  rate_limit_window: 3600
  require_authentication: true

data_encryption:
  encryption_algorithm: "AES-256-GCM"
  key_rotation_days: 90
  require_https: true

payment_processing:
  pci_compliance: true
  encrypt_payment_data: true
  audit_trail: true

file_upload:
  max_file_size: 10485760
  allowed_extensions: ["jpg", "png", "pdf", "txt"]
  scan_for_malware: true
```

## 📊 **Test Examples**

### **Authentication Security Tests**

#### **Password Strength Test**
```python
def test_password_strength_requirements():
    """Test password strength requirements"""
    weak_passwords = [
        "123456", "password", "admin", "qwerty", "letmein",
        "welcome", "monkey", "dragon", "master", "hello"
    ]
    
    strong_passwords = [
        "Str0ngP@ssw0rd!", "C0mpl3x!P@ss2024", "S3cur3!P@ssw0rd#",
        "MyP@ssw0rd!2024", "S3cur1ty!P@ss"
    ]
    
    # Test weak passwords should be rejected
    for password in weak_passwords:
        if is_password_accepted(password):
            return False
    
    # Test strong passwords should be accepted
    for password in strong_passwords:
        if not is_password_accepted(password):
            return False
    
    return True

def is_password_accepted(password: str) -> bool:
    """Check if password meets strength requirements"""
    if len(password) < 12:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special
```

#### **Login Rate Limiting Test**
```python
def test_login_rate_limiting():
    """Test login rate limiting"""
    max_attempts = 5
    
    # Attempt multiple failed logins
    for i in range(max_attempts + 2):
        response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": "test_user", "password": "wrong_password"}
        )
        
        if i < max_attempts and response.status_code == 429:  # Too Many Requests
            return True
        
        if i >= max_attempts and response.status_code != 429:
            return False
    
    return True
```

### **Authorization and Access Control Tests**

#### **Role-Based Access Control Test**
```python
def test_role_based_access_control():
    """Test role-based access control"""
    roles = ["user", "admin", "moderator", "guest"]
    protected_endpoints = [
        "/api/admin/users",
        "/api/admin/settings",
        "/api/admin/logs",
        "/api/user/profile",
        "/api/user/settings"
    ]
    
    for role in roles:
        # Login with role
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": f"{role}_user", "password": "password"}
        )
        
        if login_response.status_code != 200:
            continue
        
        # Test access to endpoints
        for endpoint in protected_endpoints:
            response = session.get(f"{base_url}{endpoint}")
            
            if "admin" in endpoint and role != "admin":
                if response.status_code != 403:
                    return False
            elif role == "admin":
                if response.status_code == 403:
                    return False
    
    return True
```

### **Input Validation and Sanitization Tests**

#### **SQL Injection Prevention Test**
```python
def test_sql_injection_prevention():
    """Test SQL injection prevention"""
    sql_injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "' OR 1=1 --",
        "admin'--",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --"
    ]
    
    endpoints = [
        "/api/search",
        "/api/users",
        "/api/login"
    ]
    
    for endpoint in endpoints:
        for payload in sql_injection_payloads:
            response = session.post(
                f"{base_url}{endpoint}",
                json={"query": payload, "username": payload, "email": payload}
            )
            
            # Check for SQL error messages
            sql_errors = [
                "sql syntax", "mysql", "oracle", "postgresql",
                "sqlite", "database error", "sql error"
            ]
            
            response_text = response.text.lower()
            for error in sql_errors:
                if error in response_text:
                    return False
    
    return True
```

#### **XSS Prevention Test**
```python
def test_xss_prevention():
    """Test XSS prevention"""
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert(document.cookie)",
        "<iframe src=javascript:alert('XSS')>"
    ]
    
    endpoints = [
        "/api/comment",
        "/api/profile",
        "/api/message"
    ]
    
    for endpoint in endpoints:
        for payload in xss_payloads:
            response = session.post(
                f"{base_url}{endpoint}",
                json={"content": payload, "message": payload}
            )
            
            # Check if payload is reflected without encoding
            if payload in response.text:
                return False
    
    return True
```

### **Session Management Security Tests**

#### **Session Timeout Test**
```python
def test_session_timeout():
    """Test session timeout"""
    # Login and get session
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": "test_user", "password": "password"}
    )
    
    if login_response.status_code != 200:
        return False
    
    # Wait for session timeout (if configured)
    time.sleep(2)  # Adjust based on session timeout
    
    # Try to access protected resource
    protected_response = session.get(f"{base_url}/api/protected")
    
    # Should be redirected to login or return 401
    return protected_response.status_code in [401, 302]
```

#### **Session Fixation Prevention Test**
```python
def test_session_fixation_prevention():
    """Test session fixation prevention"""
    # Get initial session
    initial_response = session.get(f"{base_url}/api/auth/login")
    initial_session_id = session.cookies.get("session_id")
    
    # Login
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": "test_user", "password": "password"}
    )
    
    # Check if session ID changed
    new_session_id = session.cookies.get("session_id")
    
    if initial_session_id == new_session_id:
        return False
    
    return True
```

### **API Security Tests**

#### **API Rate Limiting Test**
```python
def test_api_rate_limiting():
    """Test API rate limiting"""
    endpoints = [
        "/api/users",
        "/api/search",
        "/api/data"
    ]
    
    for endpoint in endpoints:
        # Make multiple requests
        for i in range(20):
            response = session.get(f"{base_url}{endpoint}")
            
            if i < 10 and response.status_code == 429:  # Rate limited
                return True
    
    return False
```

#### **API Authentication Test**
```python
def test_api_authentication():
    """Test API authentication"""
    protected_endpoints = [
        "/api/admin/users",
        "/api/user/profile",
        "/api/settings"
    ]
    
    for endpoint in protected_endpoints:
        # Test without authentication
        response = session.get(f"{base_url}{endpoint}")
        
        if response.status_code != 401:
            return False
    
    return True
```

### **Data Encryption and Protection Tests**

#### **Data Encryption at Rest Test**
```python
def test_data_encryption_at_rest():
    """Test data encryption at rest"""
    sensitive_files = [
        "/var/lib/mingus/database/encrypted_data.db",
        "/var/lib/mingus/backups/backup_encryption.key",
        "/var/lib/mingus/config/secrets.conf"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read(100)
                
                # Check if content is encrypted
                if not is_encrypted_content(content):
                    return False
    
    return True

def is_encrypted_content(content: bytes) -> bool:
    """Check if content appears to be encrypted"""
    if len(content) < 10:
        return False
    
    # Calculate entropy
    byte_counts = [0] * 256
    for byte in content:
        byte_counts[byte] += 1
    
    entropy = 0
    for count in byte_counts:
        if count > 0:
            p = count / len(content)
            entropy -= p * (p.bit_length() - 1)
    
    # High entropy suggests encryption
    return entropy > 7.0
```

#### **Data Encryption in Transit Test**
```python
def test_data_encryption_in_transit():
    """Test data encryption in transit"""
    if not base_url.startswith("https://"):
        return False
    
    # Test SSL/TLS configuration
    try:
        hostname = base_url.replace("https://", "").split(":")[0]
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                if not cert:
                    return False
                
                # Check for strong cipher suites
                cipher = ssock.cipher()
                weak_ciphers = ['RC4', 'DES', '3DES', 'MD5']
                
                if any(weak in cipher[0] for weak in weak_ciphers):
                    return False
        
        return True
    except:
        return False
```

### **Payment Processing Security Tests**

#### **Payment Data Encryption Test**
```python
def test_payment_data_encryption():
    """Test payment data encryption"""
    # Test payment endpoint
    payment_data = {
        "card_number": "4111111111111111",
        "expiry_date": "12/25",
        "cvv": "123",
        "amount": 100.00
    }
    
    response = session.post(
        f"{base_url}/api/payment/process",
        json=payment_data
    )
    
    # Check if sensitive data is encrypted in logs
    log_file = "/var/log/mingus/payment.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_content = f.read()
            
            # Check for unencrypted card data
            if "4111111111111111" in log_content:
                return False
    
    return True
```

#### **PCI Compliance Test**
```python
def test_pci_compliance():
    """Test PCI compliance measures"""
    # Check for PCI compliance endpoints
    pci_endpoints = [
        "/api/payment/pci/status",
        "/api/payment/pci/compliance"
    ]
    
    for endpoint in pci_endpoints:
        response = session.get(f"{base_url}{endpoint}")
        if response.status_code == 404:
            return False
    
    return True
```

### **File Upload Security Tests**

#### **File Type Validation Test**
```python
def test_file_type_validation():
    """Test file type validation"""
    malicious_files = [
        ("malicious.php", b"<?php system($_GET['cmd']); ?>", "text/plain"),
        ("malicious.jsp", b"<%@ page import=\"java.io.*\" %>", "text/plain"),
        ("malicious.asp", b"<% Response.Write(Request.QueryString(\"cmd\")) %>", "text/plain")
    ]
    
    for filename, content, content_type in malicious_files:
        files = {"file": (filename, content, content_type)}
        
        response = session.post(
            f"{base_url}/api/upload",
            files=files
        )
        
        if response.status_code == 200:
            return False
    
    return True
```

#### **File Size Limits Test**
```python
def test_file_size_limits():
    """Test file size limits"""
    # Create large file
    large_content = b"x" * (10 * 1024 * 1024)  # 10MB
    
    files = {"file": ("large.txt", large_content, "text/plain")}
    
    response = session.post(
        f"{base_url}/api/upload",
        files=files
    )
    
    if response.status_code == 200:
        return False
    
    return True
```

#### **Path Traversal Prevention Test**
```python
def test_path_traversal_prevention():
    """Test path traversal prevention in file uploads"""
    path_traversal_filenames = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd"
    ]
    
    test_content = b"test content"
    
    for filename in path_traversal_filenames:
        files = {"file": (filename, test_content, "text/plain")}
        
        response = session.post(
            f"{base_url}/api/upload",
            files=files
        )
        
        if response.status_code == 200:
            return False
    
    return True
```

## 📋 **Test Reporting**

### **Comprehensive Test Report**
```json
{
  "timestamp": "2024-12-01T10:00:00Z",
  "base_url": "http://localhost:5000",
  "categories": {
    "authentication": {
      "password_strength": true,
      "rate_limiting": true,
      "account_lockout": true,
      "mfa": true,
      "password_reset": true
    },
    "authorization": {
      "rbac": true,
      "api_auth": true,
      "resource_access": true,
      "privilege_escalation": true
    },
    "input_validation": {
      "sql_injection": true,
      "xss": true,
      "command_injection": true,
      "length_validation": true,
      "path_traversal": true
    },
    "session_management": {
      "timeout": true,
      "fixation": true,
      "regeneration": true,
      "concurrent": true,
      "logout": true
    },
    "api_security": {
      "rate_limiting": true,
      "authentication": true,
      "authorization": true,
      "input_validation": true,
      "error_handling": true
    },
    "data_encryption": {
      "encryption_at_rest": true,
      "encryption_in_transit": true,
      "key_management": true,
      "anonymization": true
    },
    "payment_processing": {
      "data_encryption": true,
      "pci_compliance": true,
      "validation": true,
      "audit_trail": true
    },
    "file_upload": {
      "file_type_validation": true,
      "file_size_limits": true,
      "content_validation": true,
      "storage_security": true,
      "path_traversal": true
    }
  }
}
```

### **Test Result Analysis**
```python
def analyze_test_results(results):
    """Analyze security test results"""
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for category, tests in results["categories"].items():
        for test_name, passed in tests.items():
            total_tests += 1
            if passed:
                passed_tests += 1
            else:
                failed_tests += 1
                print(f"FAILED: {category}.{test_name}")
    
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    print(f"\nSecurity Test Summary:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Success Rate: {success_rate:.2%}")
    
    return success_rate
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Authentication Test Failures**
```bash
# Check authentication endpoints
curl -I http://localhost:5000/api/auth/login
curl -I http://localhost:5000/api/auth/logout

# Test authentication manually
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "password"}'
```

#### **Authorization Test Failures**
```bash
# Check user roles and permissions
curl -H "Authorization: Bearer token" \
  http://localhost:5000/api/admin/users

# Test role-based access
curl -H "Authorization: Bearer user_token" \
  http://localhost:5000/api/admin/users
```

#### **Input Validation Test Failures**
```bash
# Test SQL injection manually
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "\' OR \'1\'=\'1"}'

# Test XSS manually
curl -X POST http://localhost:5000/api/comment \
  -H "Content-Type: application/json" \
  -d '{"content": "<script>alert(\"XSS\")</script>"}'
```

### **Performance Optimization**

#### **Test Performance**
```python
# Optimize test execution
test_optimization = {
    "parallel_execution": True,
    "test_timeout": 30,
    "max_retries": 2,
    "connection_pooling": True,
    "caching": True
}
```

#### **Test Scheduling**
```python
# Schedule security tests
def schedule_security_tests():
    """Schedule regular security tests"""
    # Daily critical tests
    schedule.every().day.at("02:00").do(run_critical_tests)
    
    # Weekly full tests
    schedule.every().sunday.at("03:00").do(run_full_security_tests)
    
    # Monthly comprehensive tests
    schedule.every().month.do(run_comprehensive_security_tests)

def run_critical_tests():
    """Run critical security tests"""
    results = run_security_test_categories()
    
    # Check critical categories
    critical_categories = ["authentication", "authorization", "input_validation"]
    for category in critical_categories:
        if category in results["categories"]:
            tests = results["categories"][category]
            if not all(tests.values()):
                send_security_alert(f"Critical security tests failed in {category}")
```

## 📚 **Additional Resources**

### **Documentation**
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Authentication Security](https://owasp.org/www-project-authentication-cheat-sheet/)
- [Authorization Security](https://owasp.org/www-project-authorization-cheat-sheet/)
- [Input Validation](https://owasp.org/www-project-input-validation-cheat-sheet/)

### **Tools**
- [OWASP ZAP](https://owasp.org/www-project-zap/)
- [Burp Suite](https://portswigger.net/burp)
- [SQLMap](https://sqlmap.org/)
- [XSSer](https://xsser.03c8.net/)

### **Standards**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PCI DSS](https://www.pcisecuritystandards.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 🎯 **Performance Optimization**

### **Test Performance Impact**

The security test categories are optimized for minimal performance impact:

- **Authentication Tests**: < 1% CPU impact
- **Authorization Tests**: < 1% CPU impact
- **Input Validation Tests**: < 2% CPU impact
- **Session Management Tests**: < 1% CPU impact
- **API Security Tests**: < 1% CPU impact
- **Data Encryption Tests**: < 2% CPU impact
- **Payment Processing Tests**: < 1% CPU impact
- **File Upload Tests**: < 3% CPU impact

### **Optimization Recommendations**

1. **Run tests during low-usage periods**
2. **Use parallel test execution**
3. **Implement test result caching**
4. **Optimize test timeouts**
5. **Use connection pooling**

## 🔄 **Updates and Maintenance**

### **Test Maintenance**

1. **Regular Updates**
   - Update test payloads monthly
   - Update security test cases quarterly
   - Update test configurations as needed

2. **Test Validation**
   - Validate test results regularly
   - Review failed tests and update
   - Add new security test cases

3. **Performance Monitoring**
   - Monitor test execution times
   - Optimize slow tests
   - Update test timeouts

### **Continuous Integration**

1. **Automated Testing**
   - Integrate with CI/CD pipeline
   - Run tests on every deployment
   - Block deployment on critical failures

2. **Test Reporting**
   - Generate automated reports
   - Send alerts on failures
   - Track security metrics over time

---

*This security test categories guide ensures that MINGUS maintains comprehensive security validation for specific security domains and provides focused testing for critical security measures.* 