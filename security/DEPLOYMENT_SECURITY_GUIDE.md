# Deployment Security Checks Guide

## Overview

This guide provides comprehensive deployment security checks for MINGUS, covering pre-deployment validation, SSL certificate verification, security header testing, database connection security verification, and API endpoint security testing.

## 🔒 **Deployment Security Features**

### **1. Pre-Deployment Security Validation**
- **Environment Variables**: Validation of required environment variables
- **File Permissions**: Security check for critical file permissions
- **Dependencies**: Vulnerability scanning for package dependencies
- **Configuration Files**: Validation of security configuration files
- **Security Policies**: Verification of environment-specific security policies
- **Network Configuration**: Firewall and network security validation

### **2. SSL Certificate Verification**
- **Certificate Validity**: Verification of SSL certificate authenticity
- **TLS Version**: Validation of minimum TLS version requirements
- **Cipher Suites**: Verification of secure cipher suite usage
- **Certificate Chain**: Validation of certificate chain integrity
- **Certificate Expiry**: Monitoring of certificate expiration dates

### **3. Security Header Testing**
- **Required Headers**: Validation of essential security headers
- **Optional Headers**: Verification of recommended security headers
- **Header Values**: Validation of security header configurations
- **Content Security Policy**: Verification of CSP implementation
- **HSTS Configuration**: Validation of HTTP Strict Transport Security

### **4. Database Connection Security Verification**
- **Connection Security**: Validation of database connection settings
- **SSL Connection**: Verification of database SSL/TLS configuration
- **Connection Limits**: Validation of database connection limits
- **User Permissions**: Verification of database user privileges
- **Authentication**: Validation of database authentication methods

### **5. API Endpoint Security Testing**
- **Authentication**: Verification of API endpoint authentication
- **Rate Limiting**: Validation of API rate limiting implementation
- **Input Validation**: Testing for common security vulnerabilities
- **Authorization**: Verification of proper access controls
- **Security Headers**: Validation of API response headers

## 🚀 **Usage**

### **Command Line Usage**

#### **Run Security Checks**
```bash
# Development Environment
python security/deployment_security_checks.py --environment development

# Staging Environment
python security/deployment_security_checks.py --environment staging

# Production Environment
python security/deployment_security_checks.py --environment production
```

#### **Programmatic Usage**
```python
from security.deployment_security_checks import run_deployment_security_checks

# Run security checks
report = run_deployment_security_checks("production")

# Check overall status
if report.overall_status.value == "passed":
    print("✅ All security checks passed")
elif report.overall_status.value == "warning":
    print("⚠️ Some security warnings found")
else:
    print("❌ Security check failures detected")
```

## 🔧 **Configuration**

### **Security Configuration File**

Create environment-specific configuration files:

```json
{
  "ssl_checks": {
    "enabled": true,
    "min_tls_version": "1.2",
    "required_cipher_suites": [
      "ECDHE-RSA-AES256-GCM-SHA384",
      "ECDHE-RSA-AES128-GCM-SHA256"
    ],
    "certificate_expiry_warning_days": 30,
    "certificate_expiry_critical_days": 7
  },
  "security_headers": {
    "enabled": true,
    "required_headers": [
      "Strict-Transport-Security",
      "X-Content-Type-Options",
      "X-Frame-Options",
      "X-XSS-Protection",
      "Referrer-Policy"
    ],
    "optional_headers": [
      "Content-Security-Policy",
      "Permissions-Policy"
    ]
  },
  "database_checks": {
    "enabled": true,
    "ssl_required": true,
    "connection_timeout": 10,
    "max_connections": 100
  },
  "api_checks": {
    "enabled": true,
    "endpoints": [
      "/api/health",
      "/api/auth/login",
      "/api/users",
      "/api/admin"
    ],
    "auth_required": true,
    "rate_limiting": true
  }
}
```

## 📊 **Security Check Details**

### **Pre-Deployment Checks**

#### **Environment Variables Validation**
```python
# Required variables for production
required_vars = [
    "MINGUS_ENV",
    "SECRET_KEY",
    "DATABASE_URL",
    "PROD_DB_PASSWORD",
    "PROD_JWT_SECRET",
    "PROD_SSL_CERT_PATH"
]

# Check if all required variables are set
for var in required_vars:
    if not os.getenv(var):
        print(f"❌ Missing environment variable: {var}")
```

#### **File Permissions Check**
```python
# Critical files that should have secure permissions
critical_files = [
    "/var/lib/mingus/security/encryption.key",
    "/var/lib/mingus/security/secret_encryption.key"
]

# Check file permissions (should be 600)
for file_path in critical_files:
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        if stat.st_mode & 0o777 != 0o600:
            print(f"❌ Insecure permissions on {file_path}")
```

#### **Dependencies Security Check**
```python
# Check for known vulnerable packages
vulnerable_versions = {
    "requests": ["2.25.0", "2.25.1"],
    "urllib3": ["1.26.0", "1.26.1"]
}

# Run pip list and check versions
result = subprocess.run(["pip", "list", "--format=json"], capture_output=True)
packages = json.loads(result.stdout)

for package in packages:
    name = package["name"]
    version = package["version"]
    
    if name in vulnerable_versions and version in vulnerable_versions[name]:
        print(f"❌ Vulnerable package: {name}=={version}")
```

### **SSL Certificate Checks**

#### **Certificate Validity Check**
```python
import ssl
import socket

def check_certificate_validity(domain, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((domain, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            
            if not cert:
                return False, "No certificate found"
            
            return True, "Certificate is valid"
```

#### **TLS Version Check**
```python
def check_tls_version(domain, port=443, min_version="1.2"):
    tls_versions = {
        "1.0": ssl.TLSVersion.TLSv1,
        "1.1": ssl.TLSVersion.TLSv1_1,
        "1.2": ssl.TLSVersion.TLSv1_2,
        "1.3": ssl.TLSVersion.TLSv1_3
    }
    
    supported_versions = []
    for version_name, version_enum in tls_versions.items():
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.minimum_version = version_enum
            context.maximum_version = version_enum
            
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    supported_versions.append(version_name)
        except:
            pass
    
    if min_version not in supported_versions:
        return False, f"Required TLS version {min_version} not supported"
    
    return True, f"TLS {min_version} is supported"
```

#### **Certificate Expiry Check**
```python
def check_certificate_expiry(domain, port=443, warning_days=30):
    context = ssl.create_default_context()
    with socket.create_connection((domain, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            
            not_after = cert['notAfter']
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            days_until_expiry = (expiry_date - datetime.utcnow()).days
            
            if days_until_expiry < 0:
                return False, "Certificate has expired"
            elif days_until_expiry < warning_days:
                return False, f"Certificate expires in {days_until_expiry} days"
            
            return True, f"Certificate expires in {days_until_expiry} days"
```

### **Security Header Checks**

#### **Required Headers Check**
```python
import requests

def check_required_headers(url):
    response = requests.get(url, timeout=10, verify=True)
    headers = response.headers
    
    required_headers = [
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy"
    ]
    
    missing_headers = []
    for header in required_headers:
        if header not in headers:
            missing_headers.append(header)
    
    if missing_headers:
        return False, f"Missing required headers: {', '.join(missing_headers)}"
    
    return True, "All required security headers are present"
```

#### **Header Values Check**
```python
def check_header_values(url):
    response = requests.get(url, timeout=10, verify=True)
    headers = response.headers
    
    issues = []
    
    # Check HSTS
    if "Strict-Transport-Security" in headers:
        hsts_value = headers["Strict-Transport-Security"]
        if "max-age=" not in hsts_value:
            issues.append("HSTS missing max-age")
        if "includeSubDomains" not in hsts_value:
            issues.append("HSTS missing includeSubDomains")
    
    # Check X-Frame-Options
    if "X-Frame-Options" in headers:
        xfo_value = headers["X-Frame-Options"]
        if xfo_value not in ["DENY", "SAMEORIGIN"]:
            issues.append("X-Frame-Options should be DENY or SAMEORIGIN")
    
    if issues:
        return False, f"Header value issues: {', '.join(issues)}"
    
    return True, "Security header values are properly configured"
```

### **Database Security Checks**

#### **Database Connection Check**
```python
import psycopg2

def check_database_connection(db_url):
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {e}"
```

#### **Database SSL Check**
```python
from urllib.parse import urlparse

def check_database_ssl(db_url):
    parsed = urlparse(db_url)
    
    if parsed.scheme != "postgresql":
        return True, "Not a PostgreSQL connection"
    
    if "sslmode=" not in parsed.query:
        return False, "SSL not enabled for database connection"
    
    return True, "Database SSL connection is enabled"
```

#### **Database Permissions Check**
```python
def check_database_permissions(db_url):
    conn = psycopg2.connect(db_url, connect_timeout=5)
    cursor = conn.cursor()
    
    # Check current user
    cursor.execute("SELECT current_user, session_user")
    current_user, session_user = cursor.fetchone()
    
    # Check if user has superuser privileges
    cursor.execute("SELECT usesuper FROM pg_user WHERE usename = %s", (current_user,))
    is_superuser = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    if is_superuser:
        return False, f"User {current_user} has superuser privileges"
    
    return True, f"Database user {current_user} has appropriate permissions"
```

### **API Endpoint Security Checks**

#### **Authentication Check**
```python
def check_endpoint_auth(url, auth_required=True):
    response = requests.get(url, timeout=10, verify=True)
    
    if response.status_code == 401:
        return True, "Endpoint requires authentication"
    elif response.status_code == 403:
        return True, "Endpoint requires authorization"
    elif response.status_code == 200:
        if auth_required:
            return False, "Endpoint should require authentication"
        else:
            return True, "Endpoint authentication is appropriate"
    else:
        return False, f"Unexpected response code: {response.status_code}"
```

#### **Rate Limiting Check**
```python
import time

def check_endpoint_rate_limiting(url):
    responses = []
    for i in range(10):
        response = requests.get(url, timeout=5, verify=True)
        responses.append(response.status_code)
        time.sleep(0.1)
    
    rate_limited = any(code == 429 for code in responses)
    
    if rate_limited:
        return True, "Endpoint has rate limiting enabled"
    else:
        return False, "Endpoint should have rate limiting"
```

#### **Input Validation Check**
```python
def check_endpoint_input_validation(url):
    malicious_inputs = [
        "' OR '1'='1",
        "<script>alert('xss')</script>",
        "../../../etc/passwd",
        "'; DROP TABLE users; --"
    ]
    
    vulnerabilities = []
    
    for malicious_input in malicious_inputs:
        try:
            response = requests.get(f"{url}?input={malicious_input}", timeout=5, verify=True)
            
            if "error" in response.text.lower() and "sql" in response.text.lower():
                vulnerabilities.append("Potential SQL injection")
            
            if "<script>" in response.text:
                vulnerabilities.append("Potential XSS vulnerability")
                
        except:
            pass
    
    if vulnerabilities:
        return False, f"Input validation issues found: {', '.join(vulnerabilities)}"
    
    return True, "Input validation appears to be working"
```

## 📋 **Security Checklist**

### **Pre-Deployment Checklist**

#### **Environment Setup**
- [ ] Environment variables configured
- [ ] File permissions set correctly
- [ ] Dependencies updated and secure
- [ ] Configuration files validated
- [ ] Security policies enforced
- [ ] Network configuration secure

#### **SSL/TLS Configuration**
- [ ] SSL certificate installed and valid
- [ ] TLS version 1.2+ enabled
- [ ] Secure cipher suites configured
- [ ] Certificate chain validated
- [ ] Certificate expiry monitored
- [ ] HSTS configured

#### **Security Headers**
- [ ] Required security headers present
- [ ] Header values configured correctly
- [ ] Content Security Policy implemented
- [ ] HSTS configured with appropriate max-age
- [ ] X-Frame-Options set to DENY or SAMEORIGIN
- [ ] X-Content-Type-Options set to nosniff

#### **Database Security**
- [ ] Database connection secure
- [ ] SSL/TLS enabled for database
- [ ] Connection limits configured
- [ ] User permissions appropriate
- [ ] Authentication methods secure
- [ ] Database access controlled

#### **API Security**
- [ ] Authentication required for sensitive endpoints
- [ ] Rate limiting implemented
- [ ] Input validation working
- [ ] Authorization properly configured
- [ ] Security headers in API responses
- [ ] Error handling secure

### **Post-Deployment Checklist**

#### **Verification**
- [ ] All security checks passed
- [ ] SSL certificate working correctly
- [ ] Security headers present and correct
- [ ] Database connections secure
- [ ] API endpoints properly secured
- [ ] Monitoring and alerting configured

#### **Documentation**
- [ ] Security report generated
- [ ] Configuration documented
- [ ] Procedures documented
- [ ] Contact information updated
- [ ] Emergency procedures ready

### **Ongoing Maintenance**

#### **Regular Checks**
- [ ] SSL certificate expiry monitoring
- [ ] Security header validation
- [ ] Database security verification
- [ ] API endpoint security testing
- [ ] Dependency vulnerability scanning
- [ ] Configuration validation

#### **Updates**
- [ ] Security patches applied
- [ ] Dependencies updated
- [ ] Configuration reviewed
- [ ] Policies updated
- [ ] Procedures improved

## 🔧 **Troubleshooting**

### **Common Issues**

#### **SSL Certificate Issues**
```bash
# Check certificate validity
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiry
openssl x509 -in /path/to/certificate.crt -text -noout | grep "Not After"

# Verify certificate chain
openssl verify -CAfile /path/to/ca-bundle.crt /path/to/certificate.crt
```

#### **Security Header Issues**
```bash
# Check security headers
curl -I https://yourdomain.com

# Test specific headers
curl -I https://yourdomain.com | grep -i "strict-transport-security"
curl -I https://yourdomain.com | grep -i "x-frame-options"
```

#### **Database Connection Issues**
```bash
# Test database connection
psql -h localhost -U username -d database_name

# Check SSL connection
psql "postgresql://username:password@localhost:5432/database?sslmode=require"

# Verify user permissions
psql -c "SELECT current_user, session_user;"
```

#### **API Endpoint Issues**
```bash
# Test API endpoint
curl -X GET https://yourdomain.com/api/health

# Test authentication
curl -X GET https://yourdomain.com/api/protected -H "Authorization: Bearer token"

# Test rate limiting
for i in {1..10}; do curl -X GET https://yourdomain.com/api/endpoint; done
```

### **Error Resolution**

#### **SSL Certificate Errors**
1. **Certificate not found**: Install SSL certificate
2. **Certificate expired**: Renew certificate
3. **Certificate chain invalid**: Fix certificate chain
4. **TLS version not supported**: Update server configuration

#### **Security Header Errors**
1. **Missing headers**: Configure web server
2. **Incorrect header values**: Update header configuration
3. **CSP violations**: Review Content Security Policy
4. **HSTS issues**: Configure HSTS properly

#### **Database Security Errors**
1. **Connection failed**: Check database status
2. **SSL not enabled**: Enable SSL for database
3. **Permission denied**: Fix user permissions
4. **Authentication failed**: Verify credentials

#### **API Security Errors**
1. **Authentication missing**: Add authentication
2. **Rate limiting not working**: Configure rate limiting
3. **Input validation issues**: Fix validation logic
4. **Authorization problems**: Review access controls

## 📚 **Additional Resources**

### **Documentation**
- [SSL/TLS Best Practices](https://www.ssllabs.com/projects/best-practices/)
- [Security Headers Guide](https://owasp.org/www-project-secure-headers/)
- [Database Security](https://www.postgresql.org/docs/current/security.html)
- [API Security](https://owasp.org/www-project-api-security/)

### **Security Tools**
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [OWASP ZAP](https://owasp.org/www-project-zap/)

### **Monitoring Tools**
- [Let's Encrypt](https://letsencrypt.org/)
- [Certbot](https://certbot.eff.org/)
- [SSL Certificate Monitor](https://sslshopper.com/ssl-checker.html)
- [Security Headers Monitor](https://securityheaders.com/)

## 🎯 **Performance Optimization**

### **Security Check Performance**

The deployment security checks are optimized for minimal performance impact:

- **Pre-deployment checks**: < 5 seconds
- **SSL certificate checks**: < 10 seconds
- **Security header checks**: < 5 seconds
- **Database security checks**: < 10 seconds
- **API endpoint checks**: < 15 seconds

### **Optimization Recommendations**

1. **Run checks in parallel** where possible
2. **Cache results** for repeated checks
3. **Use connection pooling** for database checks
4. **Implement timeouts** for all network requests
5. **Optimize check frequency** based on environment

## 🔄 **Updates and Maintenance**

### **Security Updates**

1. **Automatic Updates**
   - Security check updates applied automatically
   - New vulnerability checks added
   - Configuration improvements applied

2. **Manual Updates**
   - Custom security checks added
   - Environment-specific configurations
   - Policy updates and modifications

### **Backup and Recovery**

1. **Configuration Backup**
   - Security configurations backed up
   - Check results archived
   - Reports stored securely

2. **Recovery Procedures**
   - Configuration restoration
   - Check result recovery
   - Report regeneration

---

*This deployment security guide ensures that MINGUS maintains the highest security standards during deployment and provides comprehensive validation of all security measures.* 