# 🔒 SSL Testing and Validation Guide for MINGUS Application

## **Status**: ✅ **READY FOR TESTING**
## **Target**: SSL Labs Grade A+ | Banking-Grade Security Validation

---

## **📋 Testing Overview**

This guide provides comprehensive testing procedures to validate your SSL/HTTPS implementation and achieve SSL Labs Grade A+ for your MINGUS financial wellness application.

### **Testing Objectives**
- ✅ **SSL Labs Grade A+** validation
- ✅ **Certificate validity** and expiration monitoring
- ✅ **Security headers** verification
- ✅ **Mixed content** detection and resolution
- ✅ **HTTPS enforcement** testing
- ✅ **Session security** validation

---

## **🧪 Automated SSL Testing Script**

### **Step 1: Create SSL Testing Script**
```bash
#!/bin/bash

# MINGUS SSL Testing Script
# Comprehensive SSL validation for financial wellness application

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOMAIN=""
EMAIL=""
LOG_FILE="/var/log/mingus-ssl-test.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Get domain
get_domain() {
    read -p "Enter your domain name: " DOMAIN
    if [[ -z "$DOMAIN" ]]; then
        error "Domain name is required"
        exit 1
    fi
}

# Test 1: Certificate Validation
test_certificate() {
    log "Testing SSL certificate..."
    
    # Check certificate validity
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -dates; then
        log "✅ Certificate validation passed"
    else
        error "❌ Certificate validation failed"
        return 1
    fi
    
    # Check certificate expiry
    expiry_date=$(openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [[ $days_until_expiry -gt 30 ]]; then
        log "✅ Certificate expires in $days_until_expiry days"
    else
        warn "⚠️ Certificate expires in $days_until_expiry days"
    fi
}

# Test 2: TLS Version Support
test_tls_versions() {
    log "Testing TLS version support..."
    
    # Test TLS 1.2
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -tls1_2 < /dev/null >/dev/null 2>&1; then
        log "✅ TLS 1.2 supported"
    else
        error "❌ TLS 1.2 not supported"
    fi
    
    # Test TLS 1.3
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -tls1_3 < /dev/null >/dev/null 2>&1; then
        log "✅ TLS 1.3 supported"
    else
        warn "⚠️ TLS 1.3 not supported"
    fi
    
    # Test TLS 1.1 (should be disabled)
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -tls1_1 < /dev/null >/dev/null 2>&1; then
        warn "⚠️ TLS 1.1 still supported (should be disabled)"
    else
        log "✅ TLS 1.1 properly disabled"
    fi
    
    # Test TLS 1.0 (should be disabled)
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -tls1 < /dev/null >/dev/null 2>&1; then
        warn "⚠️ TLS 1.0 still supported (should be disabled)"
    else
        log "✅ TLS 1.0 properly disabled"
    fi
}

# Test 3: Cipher Suite Validation
test_cipher_suites() {
    log "Testing cipher suites..."
    
    # Test strong cipher suites
    strong_ciphers=(
        "ECDHE-RSA-AES256-GCM-SHA384"
        "ECDHE-RSA-AES128-GCM-SHA256"
        "ECDHE-RSA-CHACHA20-POLY1305"
    )
    
    for cipher in "${strong_ciphers[@]}"; do
        if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -cipher "$cipher" < /dev/null >/dev/null 2>&1; then
            log "✅ Strong cipher supported: $cipher"
        else
            warn "⚠️ Strong cipher not supported: $cipher"
        fi
    done
}

# Test 4: Security Headers
test_security_headers() {
    log "Testing security headers..."
    
    # Test HSTS
    if curl -sI "https://$DOMAIN" | grep -i "strict-transport-security" >/dev/null; then
        log "✅ HSTS header present"
    else
        error "❌ HSTS header missing"
    fi
    
    # Test X-Frame-Options
    if curl -sI "https://$DOMAIN" | grep -i "x-frame-options" >/dev/null; then
        log "✅ X-Frame-Options header present"
    else
        warn "⚠️ X-Frame-Options header missing"
    fi
    
    # Test X-Content-Type-Options
    if curl -sI "https://$DOMAIN" | grep -i "x-content-type-options" >/dev/null; then
        log "✅ X-Content-Type-Options header present"
    else
        warn "⚠️ X-Content-Type-Options header missing"
    fi
    
    # Test X-XSS-Protection
    if curl -sI "https://$DOMAIN" | grep -i "x-xss-protection" >/dev/null; then
        log "✅ X-XSS-Protection header present"
    else
        warn "⚠️ X-XSS-Protection header missing"
    fi
    
    # Test Content-Security-Policy
    if curl -sI "https://$DOMAIN" | grep -i "content-security-policy" >/dev/null; then
        log "✅ Content-Security-Policy header present"
    else
        warn "⚠️ Content-Security-Policy header missing"
    fi
}

# Test 5: HTTPS Enforcement
test_https_enforcement() {
    log "Testing HTTPS enforcement..."
    
    # Test HTTP to HTTPS redirect
    http_status=$(curl -sI "http://$DOMAIN" | head -n1 | cut -d' ' -f2)
    if [[ "$http_status" == "301" ]] || [[ "$http_status" == "302" ]]; then
        log "✅ HTTP to HTTPS redirect working"
    else
        error "❌ HTTP to HTTPS redirect not working"
    fi
    
    # Test HTTPS accessibility
    if curl -sI "https://$DOMAIN" | head -n1 | grep -q "200\|301\|302"; then
        log "✅ HTTPS accessible"
    else
        error "❌ HTTPS not accessible"
    fi
}

# Test 6: OCSP Stapling
test_ocsp_stapling() {
    log "Testing OCSP stapling..."
    
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" -status < /dev/null 2>/dev/null | grep -q "OCSP Response Status: successful"; then
        log "✅ OCSP stapling working"
    else
        warn "⚠️ OCSP stapling not working or not configured"
    fi
}

# Test 7: Mixed Content Detection
test_mixed_content() {
    log "Testing for mixed content..."
    
    # Download the page and check for HTTP resources
    temp_file=$(mktemp)
    curl -s "https://$DOMAIN" > "$temp_file"
    
    # Check for HTTP URLs in the page
    http_urls=$(grep -o 'http://[^"'\''\s]*' "$temp_file" | wc -l)
    
    if [[ $http_urls -eq 0 ]]; then
        log "✅ No mixed content detected"
    else
        warn "⚠️ Found $http_urls HTTP URLs (potential mixed content)"
        grep -o 'http://[^"'\''\s]*' "$temp_file" | head -5
    fi
    
    rm "$temp_file"
}

# Test 8: SSL Labs Grade Check
test_ssl_labs_grade() {
    log "Checking SSL Labs grade..."
    
    # Note: This requires the SSL Labs API
    # For now, we'll provide instructions
    info "To check SSL Labs grade:"
    info "1. Visit: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    info "2. Wait for the test to complete"
    info "3. Target grade: A+"
}

# Test 9: Certificate Transparency
test_certificate_transparency() {
    log "Testing certificate transparency..."
    
    # Check for Expect-CT header
    if curl -sI "https://$DOMAIN" | grep -i "expect-ct" >/dev/null; then
        log "✅ Certificate Transparency header present"
    else
        warn "⚠️ Certificate Transparency header missing"
    fi
}

# Test 10: Session Security
test_session_security() {
    log "Testing session security..."
    
    # Test secure cookie flags
    cookies=$(curl -sI "https://$DOMAIN" | grep -i "set-cookie")
    
    if echo "$cookies" | grep -q "Secure"; then
        log "✅ Secure cookie flag present"
    else
        warn "⚠️ Secure cookie flag missing"
    fi
    
    if echo "$cookies" | grep -q "HttpOnly"; then
        log "✅ HttpOnly cookie flag present"
    else
        warn "⚠️ HttpOnly cookie flag missing"
    fi
    
    if echo "$cookies" | grep -q "SameSite"; then
        log "✅ SameSite cookie flag present"
    else
        warn "⚠️ SameSite cookie flag missing"
    fi
}

# Main testing function
main() {
    log "Starting MINGUS SSL testing..."
    
    get_domain
    
    log "Testing domain: $DOMAIN"
    log "Log file: $LOG_FILE"
    
    # Run all tests
    test_certificate
    test_tls_versions
    test_cipher_suites
    test_security_headers
    test_https_enforcement
    test_ocsp_stapling
    test_mixed_content
    test_ssl_labs_grade
    test_certificate_transparency
    test_session_security
    
    log "SSL testing completed!"
    
    echo
    echo -e "${GREEN}=== SSL Testing Summary ===${NC}"
    echo -e "Domain: ${BLUE}$DOMAIN${NC}"
    echo -e "Log file: ${BLUE}$LOG_FILE${NC}"
    echo
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Review the test results above"
    echo "2. Fix any issues identified"
    echo "3. Run SSL Labs test manually"
    echo "4. Monitor certificate expiry"
    echo
    echo -e "${YELLOW}SSL Labs Test:${NC} https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
}

# Run main function
main "$@"
```

### **Step 2: Make Script Executable**
```bash
chmod +x ssl_test.sh
```

### **Step 3: Run SSL Tests**
```bash
./ssl_test.sh
```

---

## **🔍 Manual SSL Testing Procedures**

### **1. Certificate Validation**

#### **Check Certificate Details**
```bash
# View certificate information
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null | openssl x509 -noout -text

# Check certificate expiry
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null | openssl x509 -noout -dates

# Check certificate chain
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null | openssl x509 -noout -issuer -subject
```

#### **Expected Results**
- ✅ Certificate is valid and not expired
- ✅ Certificate chain is complete
- ✅ Certificate is issued by a trusted CA
- ✅ Certificate matches the domain name

### **2. TLS Version Testing**

#### **Test TLS 1.2 Support**
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com -tls1_2 < /dev/null
```

#### **Test TLS 1.3 Support**
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com -tls1_3 < /dev/null
```

#### **Test Legacy TLS Disabled**
```bash
# These should fail
openssl s_client -connect your-domain.com:443 -servername your-domain.com -tls1_1 < /dev/null
openssl s_client -connect your-domain.com:443 -servername your-domain.com -tls1 < /dev/null
```

#### **Expected Results**
- ✅ TLS 1.2 supported
- ✅ TLS 1.3 supported
- ✅ TLS 1.1 disabled
- ✅ TLS 1.0 disabled

### **3. Security Headers Testing**

#### **Check All Security Headers**
```bash
curl -sI https://your-domain.com | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options|X-XSS-Protection|Content-Security-Policy|Referrer-Policy|Permissions-Policy|Cross-Origin-Opener-Policy|Cross-Origin-Embedder-Policy|Cross-Origin-Resource-Policy)"
```

#### **Expected Headers**
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://checkout.stripe.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: https://stripe.com https://checkout.stripe.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.stripe.com https://checkout.stripe.com; frame-src 'self' https://js.stripe.com https://checkout.stripe.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Resource-Policy: same-origin
```

### **4. HTTPS Enforcement Testing**

#### **Test HTTP to HTTPS Redirect**
```bash
# Should return 301 or 302
curl -sI http://your-domain.com | head -n1
```

#### **Test HTTPS Accessibility**
```bash
# Should return 200, 301, or 302
curl -sI https://your-domain.com | head -n1
```

#### **Expected Results**
- ✅ HTTP requests redirect to HTTPS (301/302)
- ✅ HTTPS requests are successful (200/301/302)
- ✅ No mixed content warnings

### **5. Mixed Content Detection**

#### **Check for HTTP Resources**
```bash
# Download page and check for HTTP URLs
curl -s https://your-domain.com | grep -o 'http://[^"'\''\s]*'
```

#### **Browser Developer Tools**
1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for mixed content warnings
4. Check Network tab for HTTP requests

#### **Expected Results**
- ✅ No HTTP URLs in the page
- ✅ No mixed content warnings in browser console
- ✅ All resources loaded over HTTPS

### **6. OCSP Stapling Testing**

#### **Check OCSP Stapling**
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com -status < /dev/null
```

#### **Expected Results**
- ✅ OCSP Response Status: successful
- ✅ OCSP stapling is working

### **7. Session Security Testing**

#### **Check Cookie Security**
```bash
curl -sI https://your-domain.com | grep -i "set-cookie"
```

#### **Expected Cookie Flags**
- ✅ `Secure` flag present
- ✅ `HttpOnly` flag present
- ✅ `SameSite=Strict` flag present

---

## **📊 SSL Labs Grade A+ Checklist**

### **Certificate (25 points)**
- [ ] **Certificate is trusted** (10 points)
- [ ] **Certificate is not expired** (5 points)
- [ ] **Certificate is not revoked** (5 points)
- [ ] **Certificate is not weak** (5 points)

### **Protocol Support (20 points)**
- [ ] **TLS 1.3 supported** (10 points)
- [ ] **TLS 1.2 supported** (5 points)
- [ ] **TLS 1.1 disabled** (5 points)
- [ ] **TLS 1.0 disabled** (5 points)

### **Key Exchange (25 points)**
- [ ] **Forward secrecy** (15 points)
- [ ] **Key exchange is not weak** (10 points)

### **Cipher Strength (25 points)**
- [ ] **Cipher is not weak** (15 points)
- [ ] **Cipher is not null** (10 points)

### **Protocol Security (5 points)**
- [ ] **Protocol is not vulnerable** (5 points)

### **Additional Features**
- [ ] **OCSP stapling enabled**
- [ ] **HSTS enabled**
- [ ] **Certificate transparency**
- [ ] **Secure renegotiation**

---

## **🚨 Common SSL Issues and Fixes**

### **Issue 1: Certificate Not Trusted**
**Symptoms**: Browser shows "Not Secure" warning
**Fix**: Ensure certificate is issued by a trusted CA

### **Issue 2: Mixed Content Warnings**
**Symptoms**: Browser console shows mixed content errors
**Fix**: Update all HTTP URLs to HTTPS

### **Issue 3: HSTS Not Working**
**Symptoms**: HSTS header missing or incorrect
**Fix**: Configure HSTS header in Nginx/Apache

### **Issue 4: Weak Cipher Suites**
**Symptoms**: SSL Labs shows weak ciphers
**Fix**: Update cipher configuration in Nginx/Apache

### **Issue 5: Certificate Expiry**
**Symptoms**: Certificate expired or expiring soon
**Fix**: Renew certificate and update configuration

---

## **📈 SSL Monitoring and Maintenance**

### **Daily Monitoring**
```bash
# Check certificate expiry
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null | openssl x509 -noout -enddate

# Check SSL Labs grade (manual)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### **Weekly Monitoring**
```bash
# Run full SSL test
./ssl_test.sh

# Check for security updates
apt update && apt list --upgradable | grep -E "(nginx|openssl|certbot)"
```

### **Monthly Monitoring**
- Review SSL Labs grade
- Check certificate renewal status
- Update SSL configuration if needed
- Review security headers

---

## **✅ SSL Testing Summary**

### **Automated Tests**
- [ ] Certificate validation
- [ ] TLS version support
- [ ] Cipher suite validation
- [ ] Security headers verification
- [ ] HTTPS enforcement
- [ ] OCSP stapling
- [ ] Mixed content detection
- [ ] Session security

### **Manual Tests**
- [ ] SSL Labs grade check
- [ ] Browser compatibility
- [ ] Mobile device testing
- [ ] Performance impact assessment

### **Target Results**
- **SSL Labs Grade**: A+
- **Certificate**: Valid and trusted
- **TLS Versions**: 1.2 and 1.3 only
- **Security Headers**: All present and correct
- **HTTPS Enforcement**: 100% redirect
- **Mixed Content**: None detected
- **Session Security**: All flags set

---

**🎯 Expected Completion Time**: 30-60 minutes for full testing
**🔒 Security Level**: Banking-grade validation
**📈 Target SSL Labs Grade**: A+
