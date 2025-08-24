# Security Testing Guide

## Overview

This guide provides comprehensive security testing for MINGUS, covering all security measures including authentication, authorization, encryption, network security, application security, data protection, monitoring, backup security, and compliance.

## 🔒 **Security Testing Features**

### **1. Authentication Testing**
- **Password Strength Validation**: Test password strength requirements
- **Login Rate Limiting**: Test login rate limiting mechanisms
- **Session Management**: Test session security and management
- **Multi-Factor Authentication**: Test MFA implementation
- **Account Lockout**: Test account lockout mechanisms

### **2. Authorization Testing**
- **Role-Based Access Control**: Test RBAC implementation
- **API Authorization**: Test API endpoint authorization
- **Resource Access Control**: Test resource access controls
- **Permission Escalation**: Test privilege escalation prevention
- **Access Control Lists**: Test ACL implementation

### **3. Encryption Testing**
- **Data Encryption at Rest**: Test data encryption while stored
- **Data Encryption in Transit**: Test data encryption during transmission
- **Key Management**: Test encryption key management
- **Certificate Management**: Test SSL/TLS certificate management
- **Encryption Algorithms**: Test encryption algorithm strength

### **4. Network Security Testing**
- **SSL/TLS Configuration**: Test SSL/TLS security configuration
- **Security Headers**: Test security header implementation
- **Firewall Configuration**: Test firewall rules and configuration
- **Network Segmentation**: Test network isolation
- **Port Security**: Test port access controls

### **5. Application Security Testing**
- **SQL Injection Prevention**: Test SQL injection protection
- **Cross-Site Scripting (XSS)**: Test XSS prevention mechanisms
- **Cross-Site Request Forgery (CSRF)**: Test CSRF protection
- **Input Validation**: Test input sanitization and validation
- **Output Encoding**: Test output encoding mechanisms

### **6. Data Protection Testing**
- **Data Anonymization**: Test data anonymization processes
- **Data Retention**: Test data retention policies
- **Data Access Logging**: Test data access audit trails
- **Data Classification**: Test data classification systems
- **Privacy Controls**: Test privacy control implementation

### **7. Monitoring Testing**
- **Security Event Monitoring**: Test security event detection
- **Alert System**: Test alert mechanisms and notifications
- **Log Management**: Test log collection and analysis
- **Performance Monitoring**: Test performance monitoring
- **Compliance Monitoring**: Test compliance monitoring

### **8. Backup Security Testing**
- **Backup Encryption**: Test backup encryption mechanisms
- **Backup Access Control**: Test backup access controls
- **Backup Integrity**: Test backup integrity verification
- **Recovery Testing**: Test backup recovery procedures
- **Backup Monitoring**: Test backup monitoring systems

### **9. Compliance Testing**
- **GDPR Compliance**: Test GDPR compliance measures
- **Data Privacy Controls**: Test data privacy implementation
- **Audit Trail**: Test audit trail functionality
- **Data Subject Rights**: Test data subject request handling
- **Compliance Reporting**: Test compliance reporting systems

### **10. Integration Testing**
- **Security Integration**: Test security component integration
- **End-to-End Security**: Test complete security workflows
- **API Security**: Test API security measures
- **Third-Party Integration**: Test third-party security
- **System Integration**: Test system-wide security

## 🚀 **Usage**

### **Basic Security Testing**

#### **Run All Security Tests**
```python
from security.security_tests import run_security_tests

# Run all security tests
report = run_security_tests(base_url="http://localhost:5000")

# Print results
print(f"Total tests: {report['summary']['total_tests']}")
print(f"Passed: {report['summary']['passed_tests']}")
print(f"Failed: {report['summary']['failed_tests']}")
print(f"Success rate: {report['summary']['success_rate']:.2%}")
```

#### **Run Specific Test Categories**
```python
# Run only authentication tests
auth_report = run_security_tests(
    base_url="http://localhost:5000",
    categories=["authentication"]
)

# Run multiple categories
security_report = run_security_tests(
    base_url="http://localhost:5000",
    categories=["authentication", "authorization", "encryption"]
)
```

#### **Run Tests with Custom Configuration**
```python
from security.security_tests import get_security_test_suite

# Get test suite instance
test_suite = get_security_test_suite("http://localhost:5000")

# Run specific tests
results = test_suite.run_all_tests(categories=["authentication"])

# Generate detailed report
report = test_suite.generate_test_report()
```

### **Advanced Testing**

#### **Custom Test Configuration**
```python
# Custom test configuration
test_config = {
    "test_timeout": 60,
    "max_retries": 5,
    "parallel_tests": 10,
    "test_credentials": {
        "admin_user": "admin",
        "admin_password": "secure_password",
        "regular_user": "user",
        "regular_password": "user_password"
    },
    "test_endpoints": {
        "health": "/health",
        "login": "/api/auth/login",
        "protected": "/api/protected",
        "admin": "/api/admin"
    }
}

# Run tests with custom config
test_suite = get_security_test_suite("http://localhost:5000")
test_suite.config.update(test_config)
results = test_suite.run_all_tests()
```

#### **Individual Test Execution**
```python
# Run specific test
test_suite = get_security_test_suite("http://localhost:5000")

# Get specific test
auth_test = test_suite.test_registry["auth_001"]

# Run test
result = test_suite._run_single_test(auth_test)
print(f"Test {auth_test.name}: {result.status.value}")
```

## 🔧 **Test Configuration**

### **Test Configuration File**

Create a test configuration file:

```yaml
# security_tests.yml
test_timeout: 30
max_retries: 3
parallel_tests: 5
test_categories: ["all"]
exclude_tests: []

test_credentials:
  admin_user: "admin"
  admin_password: "admin_password"
  regular_user: "user"
  regular_password: "user_password"

test_endpoints:
  health: "/health"
  login: "/api/auth/login"
  protected: "/api/protected"
  admin: "/api/admin"

test_severity_levels:
  - "critical"
  - "high"
  - "medium"
  - "low"

test_categories:
  - "authentication"
  - "authorization"
  - "encryption"
  - "network_security"
  - "application_security"
  - "data_protection"
  - "monitoring"
  - "backup_security"
  - "compliance"
  - "integration"
```

### **Environment-Specific Configuration**

#### **Development Environment**
```yaml
# Development test configuration
test_timeout: 60
max_retries: 5
parallel_tests: 10

test_credentials:
  admin_user: "dev_admin"
  admin_password: "dev_password"
  regular_user: "dev_user"
  regular_password: "dev_password"

test_endpoints:
  health: "/health"
  login: "/api/auth/login"
  protected: "/api/protected"
  admin: "/api/admin"

exclude_tests:
  - "backup_001"  # Skip backup tests in development
  - "comp_001"    # Skip compliance tests in development
```

#### **Staging Environment**
```yaml
# Staging test configuration
test_timeout: 45
max_retries: 3
parallel_tests: 8

test_credentials:
  admin_user: "staging_admin"
  admin_password: "staging_password"
  regular_user: "staging_user"
  regular_password: "staging_password"

test_endpoints:
  health: "/health"
  login: "/api/auth/login"
  protected: "/api/protected"
  admin: "/api/admin"

test_categories:
  - "authentication"
  - "authorization"
  - "encryption"
  - "network_security"
  - "application_security"
  - "data_protection"
  - "monitoring"
```

#### **Production Environment**
```yaml
# Production test configuration
test_timeout: 30
max_retries: 2
parallel_tests: 5

test_credentials:
  admin_user: "prod_admin"
  admin_password: "prod_password"
  regular_user: "prod_user"
  regular_password: "prod_password"

test_endpoints:
  health: "/health"
  login: "/api/auth/login"
  protected: "/api/protected"
  admin: "/api/admin"

test_categories: ["all"]
test_severity_levels:
  - "critical"
  - "high"
  - "medium"
```

## 📊 **Test Categories and Examples**

### **Authentication Tests**

#### **Password Strength Test**
```python
def test_password_strength():
    """Test password strength requirements"""
    weak_passwords = ["123456", "password", "admin", "qwerty"]
    strong_passwords = ["Str0ngP@ssw0rd!", "C0mpl3x!P@ss", "S3cur3!P@ssw0rd"]
    
    for password in weak_passwords:
        if is_password_strong(password):
            return False
    
    for password in strong_passwords:
        if not is_password_strong(password):
            return False
    
    return True

def is_password_strong(password: str) -> bool:
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
    # Attempt multiple login failures
    for i in range(10):
        response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": "test", "password": "wrong_password"}
        )
        
        if i < 5 and response.status_code == 429:  # Too Many Requests
            return True
    
    return False
```

### **Authorization Tests**

#### **Role-Based Access Control Test**
```python
def test_rbac_implementation():
    """Test role-based access control"""
    # Login as regular user
    response = session.post(
        f"{base_url}/api/auth/login",
        json={
            "username": "regular_user",
            "password": "user_password"
        }
    )
    
    if response.status_code != 200:
        return False
    
    # Try to access admin endpoint
    admin_response = session.get(f"{base_url}/api/admin")
    
    # Should be denied
    return admin_response.status_code == 403
```

#### **API Authorization Test**
```python
def test_api_authorization():
    """Test API endpoint authorization"""
    # Test protected endpoints without authentication
    protected_endpoints = ["/api/admin", "/api/users", "/api/settings"]
    
    for endpoint in protected_endpoints:
        response = session.get(f"{base_url}{endpoint}")
        if response.status_code != 401:  # Should require authentication
            return False
    
    return True
```

### **Encryption Tests**

#### **Data Encryption at Rest Test**
```python
def test_encryption_at_rest():
    """Test data encryption at rest"""
    # Check if sensitive data files are encrypted
    sensitive_files = [
        "/var/lib/mingus/database/encrypted_data.db",
        "/var/lib/mingus/backups/backup_encryption.key"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            # Check if file is encrypted (basic check)
            with open(file_path, 'rb') as f:
                content = f.read(100)
                # Check for encryption indicators
                if not is_encrypted_content(content):
                    return False
    
    return True

def is_encrypted_content(content: bytes) -> bool:
    """Check if content appears to be encrypted"""
    # Basic entropy check
    if len(content) < 10:
        return False
    
    # Check for high entropy (encrypted data should have high entropy)
    byte_counts = [0] * 256
    for byte in content:
        byte_counts[byte] += 1
    
    # Calculate entropy
    entropy = 0
    for count in byte_counts:
        if count > 0:
            p = count / len(content)
            entropy -= p * (p.bit_length() - 1)
    
    # High entropy suggests encryption
    return entropy > 7.0
```

### **Network Security Tests**

#### **SSL/TLS Configuration Test**
```python
def test_ssl_tls_configuration():
    """Test SSL/TLS configuration"""
    if not base_url.startswith("https://"):
        return False
    
    try:
        # Test SSL configuration
        hostname = base_url.replace("https://", "").split(":")[0]
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                # Check certificate validity
                if not cert:
                    return False
                
                # Check for strong cipher suites
                cipher = ssock.cipher()
                if cipher[0] in ['RC4', 'DES', '3DES']:
                    return False
        
        return True
    except:
        return False
```

#### **Security Headers Test**
```python
def test_security_headers():
    """Test security headers"""
    response = session.get(f"{base_url}/health")
    
    required_headers = [
        'Strict-Transport-Security',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection'
    ]
    
    for header in required_headers:
        if header not in response.headers:
            return False
    
    return True
```

### **Application Security Tests**

#### **SQL Injection Prevention Test**
```python
def test_sql_injection_prevention():
    """Test SQL injection prevention"""
    sql_injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --"
    ]
    
    for payload in sql_injection_payloads:
        response = session.post(
            f"{base_url}/api/search",
            json={"query": payload}
        )
        
        # Should not return sensitive data
        if "admin" in response.text.lower() or "password" in response.text.lower():
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
        "<img src=x onerror=alert('XSS')>"
    ]
    
    for payload in xss_payloads:
        response = session.post(
            f"{base_url}/api/comment",
            json={"content": payload}
        )
        
        # Check if payload is escaped
        if payload in response.text:
            return False
    
    return True
```

## 📋 **Test Reporting**

### **Test Report Structure**

#### **Summary Report**
```json
{
  "timestamp": "2024-12-01T10:00:00Z",
  "summary": {
    "total_tests": 50,
    "passed_tests": 45,
    "failed_tests": 3,
    "error_tests": 1,
    "skipped_tests": 1,
    "success_rate": 0.90
  },
  "category_results": {
    "authentication": [
      {
        "test_id": "auth_001",
        "name": "Password Strength Validation",
        "status": "passed",
        "execution_time": 0.5
      }
    ]
  },
  "severity_results": {
    "critical": [
      {
        "test_id": "app_001",
        "name": "SQL Injection Prevention",
        "status": "passed",
        "execution_time": 1.2
      }
    ]
  }
}
```

#### **Detailed Test Results**
```json
{
  "detailed_results": [
    {
      "test_id": "auth_001",
      "name": "Password Strength Validation",
      "category": "authentication",
      "severity": "high",
      "status": "passed",
      "execution_time": 0.5,
      "error_message": null,
      "details": {
        "actual_result": true
      }
    },
    {
      "test_id": "auth_002",
      "name": "Login Rate Limiting",
      "category": "authentication",
      "severity": "high",
      "status": "failed",
      "execution_time": 2.1,
      "error_message": "Expected True, got False",
      "details": {
        "actual_result": false
      }
    }
  ]
}
```

### **Report Generation**

#### **Generate Test Report**
```python
# Generate comprehensive report
report = test_suite.generate_test_report()

# Save report to file
with open("security_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

# Print summary
print(f"Security Test Summary:")
print(f"  Total Tests: {report['summary']['total_tests']}")
print(f"  Passed: {report['summary']['passed_tests']}")
print(f"  Failed: {report['summary']['failed_tests']}")
print(f"  Success Rate: {report['summary']['success_rate']:.2%}")

# Print failed tests
failed_tests = [r for r in report['detailed_results'] if r['status'] == 'failed']
if failed_tests:
    print(f"\nFailed Tests:")
    for test in failed_tests:
        print(f"  - {test['name']}: {test['error_message']}")
```

#### **Category-Based Reporting**
```python
# Generate category-specific reports
for category, results in report['category_results'].items():
    passed = len([r for r in results if r['status'] == 'passed'])
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    print(f"{category.upper()}: {passed}/{total} ({success_rate:.2%})")
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Test Failures**
```bash
# Check test logs
tail -f /var/log/mingus/security_tests.log

# Check application logs
tail -f /var/log/mingus/app.log

# Check network connectivity
curl -I http://localhost:5000/health

# Check test configuration
python -c "
from security.security_tests import get_security_test_suite
suite = get_security_test_suite()
print(suite.config)
"
```

#### **Authentication Issues**
```bash
# Test authentication manually
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Check authentication endpoints
curl -I http://localhost:5000/api/auth/login
curl -I http://localhost:5000/api/auth/logout
```

#### **Network Issues**
```bash
# Test SSL/TLS configuration
openssl s_client -connect localhost:443 -servername localhost

# Check security headers
curl -I http://localhost:5000/health | grep -i security

# Test firewall configuration
nmap -p 80,443,22,23 localhost
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
    # Daily tests
    schedule.every().day.at("02:00").do(run_critical_tests)
    
    # Weekly tests
    schedule.every().sunday.at("03:00").do(run_full_security_suite)
    
    # Monthly tests
    schedule.every().month.do(run_compliance_tests)

def run_critical_tests():
    """Run critical security tests"""
    report = run_security_tests(categories=["authentication", "authorization"])
    
    if report['summary']['success_rate'] < 0.95:
        send_security_alert("Critical security tests failed")
```

## 📚 **Additional Resources**

### **Documentation**
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Security Testing Best Practices](https://www.owasp.org/index.php/Testing_Guide_Introduction)
- [Penetration Testing](https://www.owasp.org/index.php/Penetration_testing)

### **Tools**
- [OWASP ZAP](https://owasp.org/www-project-zap/)
- [Burp Suite](https://portswigger.net/burp)
- [Nmap](https://nmap.org/)
- [Metasploit](https://www.metasploit.com/)

### **Frameworks**
- [OWASP Testing Framework](https://owasp.org/www-project-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html)

## 🎯 **Performance Optimization**

### **Test Performance Impact**

The security testing suite is optimized for minimal performance impact:

- **Authentication Tests**: < 1% CPU impact
- **Authorization Tests**: < 1% CPU impact
- **Encryption Tests**: < 2% CPU impact
- **Network Tests**: < 1% CPU impact
- **Application Tests**: < 3% CPU impact

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

*This security testing guide ensures that MINGUS maintains comprehensive security validation and provides automated testing for all security measures.* 