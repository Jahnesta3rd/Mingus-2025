# Content Security Policy (CSP) Implementation Guide
## Mingus Financial App - Comprehensive CSP Security

This guide documents the complete Content Security Policy implementation for the Mingus financial application, including configuration, testing, and best practices.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Resource Analysis](#resource-analysis)
3. [CSP Configuration](#csp-configuration)
4. [Implementation Details](#implementation-details)
5. [Testing and Validation](#testing-and-validation)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## 🎯 Overview

### What is CSP?
Content Security Policy (CSP) is a security standard that helps prevent cross-site scripting (XSS), clickjacking, and other code injection attacks by specifying which resources can be loaded and executed.

### Why CSP for Financial Apps?
- **Data Protection**: Prevents unauthorized script execution
- **Regulatory Compliance**: Meets financial industry security requirements
- **Attack Prevention**: Blocks XSS, CSRF, and injection attacks
- **Audit Trail**: Provides violation reporting for security monitoring

## 🔍 Resource Analysis

### External Resources Identified

#### **Payment Processing (Stripe)**
```javascript
// Domains
- js.stripe.com (Scripts)
- checkout.stripe.com (Checkout, Scripts)
- hooks.stripe.com (Webhooks)
- api.stripe.com (API calls)

// CSP Directives Required
script-src: https://js.stripe.com https://checkout.stripe.com
frame-src: https://js.stripe.com https://hooks.stripe.com https://checkout.stripe.com
connect-src: https://api.stripe.com https://js.stripe.com
form-action: https://api.stripe.com https://checkout.stripe.com
```

#### **Analytics (Google Analytics)**
```javascript
// Domains
- www.googletagmanager.com (Scripts)
- www.google-analytics.com (Scripts, Images)
- analytics.google.com (API calls)

// CSP Directives Required
script-src: https://www.googletagmanager.com https://www.google-analytics.com
connect-src: https://www.google-analytics.com https://analytics.google.com
img-src: https://www.google-analytics.com
```

#### **User Analytics (Microsoft Clarity)**
```javascript
// Domains
- clarity.microsoft.com (Scripts, Images)
- c.clarity.ms (API calls)

// CSP Directives Required
script-src: https://clarity.microsoft.com
connect-src: https://clarity.microsoft.com https://c.clarity.ms
img-src: https://clarity.microsoft.com
```

#### **Backend Services**
```javascript
// Supabase (Database/Auth)
- api.supabase.co (API calls, Scripts)

// Twilio (SMS)
- api.twilio.com (API calls)

// Resend (Email)
- api.resend.com (API calls)

// Plaid (Banking)
- api.plaid.com (API calls)
```

#### **Fonts and CDNs**
```javascript
// Google Fonts
- fonts.googleapis.com (Styles)
- fonts.gstatic.com (Fonts)

// CDN Resources
- cdn.jsdelivr.net (Scripts, Styles)
- cdnjs.cloudflare.com (Styles)
- unpkg.com (Scripts)
```

### Inline Content Analysis

#### **Inline Scripts Found**
```html
<!-- Service Worker Registration -->
<script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
    }
</script>

<!-- Analytics Initialization -->
<script>
    gtag('config', 'G-LR5TV15ZTM');
    clarity('set', 'projectId', 'your-project-id');
</script>

<!-- Form Validation -->
<script>
    document.getElementById('loginForm').addEventListener('submit', function(e) {
        // Form validation logic
    });
</script>
```

#### **Inline Styles Found**
```html
<!-- Dynamic Styles -->
<style>
    .alert { background-color: #f8d7da; }
    .session-status { display: inline-block; }
</style>

<!-- Inline Style Attributes -->
<div style="color: var(--primary-color);">
```

## ⚙️ CSP Configuration

### Environment-Specific Configurations

#### **Production Configuration (Strict)**
```python
CSPConfig(
    environment='production',
    report_only=False,
    report_uri='https://your-domain.com/csp-violation-report',
    directives={
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'nonce-{nonce}'",
            "https://js.stripe.com",
            "https://checkout.stripe.com",
            "https://www.googletagmanager.com",
            "https://www.google-analytics.com",
            "https://clarity.microsoft.com"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # Required for dynamic styles
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net"
        ],
        'img-src': [
            "'self'",
            "data:",
            "https:",
            "https://stripe.com",
            "https://checkout.stripe.com",
            "https://www.google-analytics.com",
            "https://clarity.microsoft.com"
        ],
        'connect-src': [
            "'self'",
            "https://api.stripe.com",
            "https://js.stripe.com",
            "https://api.supabase.co",
            "https://api.twilio.com",
            "https://api.resend.com",
            "https://api.plaid.com",
            "https://www.google-analytics.com",
            "https://analytics.google.com",
            "https://clarity.microsoft.com",
            "https://c.clarity.ms"
        ],
        'frame-src': [
            "'self'",
            "https://js.stripe.com",
            "https://hooks.stripe.com",
            "https://checkout.stripe.com"
        ],
        'object-src': ["'none'"],
        'frame-ancestors': ["'none'"],
        'upgrade-insecure-requests': [],
        'block-all-mixed-content': []
    }
)
```

#### **Development Configuration (Permissive)**
```python
CSPConfig(
    environment='development',
    report_only=True,  # Report-only mode
    directives={
        'default-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "https://js.stripe.com",
            "https://checkout.stripe.com",
            "https://www.googletagmanager.com",
            "https://www.google-analytics.com",
            "https://clarity.microsoft.com",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com"
        ],
        'connect-src': [
            "'self'",
            # All APIs
            "https://api.stripe.com",
            "https://api.supabase.co",
            "https://api.twilio.com",
            "https://api.resend.com",
            "https://api.plaid.com",
            # Local development
            "ws://localhost:*",
            "wss://localhost:*"
        ]
    }
)
```

### Nonce-Based Script Loading

#### **Implementation**
```python
# Generate nonce for each request
def generate_nonce():
    return secrets.token_urlsafe(32)

# Add nonce to template context
@app.before_request
def add_csp_nonce():
    g.csp_nonce = generate_nonce()
    current_app.jinja_env.globals['csp_nonce'] = g.csp_nonce
```

#### **Template Usage**
```html
<!-- Inline scripts with nonce -->
<script nonce="{{ csp_nonce }}">
    // Service worker registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
    }
</script>

<!-- External scripts -->
<script src="https://js.stripe.com/v3/" nonce="{{ csp_nonce }}"></script>
```

## 🔧 Implementation Details

### CSP Middleware Integration

#### **Flask Application Setup**
```python
from csp_policy_manager import CSPMiddleware, CSPViolationHandler

# Initialize CSP middleware
csp_middleware = CSPMiddleware(app, environment=os.getenv('FLASK_ENV', 'development'))
violation_handler = CSPViolationHandler(app)

# Register template helpers
app.jinja_env.globals['csp_nonce'] = get_csp_nonce
app.jinja_env.globals['csp_script_tag'] = csp_script_tag
app.jinja_env.globals['csp_style_tag'] = csp_style_tag
```

#### **Security Headers**
```python
def add_security_headers(response):
    # CSP Header
    csp_header = build_csp_header(environment, nonce)
    if config.report_only:
        response.headers['Content-Security-Policy-Report-Only'] = csp_header
    else:
        response.headers['Content-Security-Policy'] = csp_header
    
    # Additional Security Headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(self)'
    
    return response
```

### Violation Reporting

#### **Violation Handler**
```python
@app.route('/csp-violation-report', methods=['POST'])
def handle_csp_violation():
    try:
        violation_data = request.get_json()
        
        # Log violation
        logger.warning(f"CSP Violation: {violation_data}")
        
        # Store for analysis
        store_violation(violation_data)
        
        # Alert if critical
        if is_critical_violation(violation_data):
            send_alert(violation_data)
        
        return {'status': 'received'}, 200
        
    except Exception as e:
        logger.error(f"Error handling CSP violation: {e}")
        return {'error': 'Internal server error'}, 500
```

#### **Violation Analysis**
```python
def analyze_violations():
    """Analyze CSP violations for patterns"""
    violations = load_violations()
    
    # Group by violated directive
    directive_violations = {}
    for violation in violations:
        directive = violation.get('violated-directive', 'unknown')
        if directive not in directive_violations:
            directive_violations[directive] = []
        directive_violations[directive].append(violation)
    
    # Generate recommendations
    recommendations = []
    for directive, violations in directive_violations.items():
        if len(violations) > 10:  # Threshold for action
            recommendations.append(f"Review {directive} violations: {len(violations)} occurrences")
    
    return recommendations
```

## 🧪 Testing and Validation

### Automated Testing Suite

#### **CSP Header Testing**
```python
def test_csp_headers():
    """Test CSP header presence and configuration"""
    response = requests.get(base_url)
    
    # Check for CSP header
    csp_header = response.headers.get('Content-Security-Policy')
    assert csp_header is not None, "CSP header not found"
    
    # Validate required directives
    required_directives = ['default-src', 'script-src', 'style-src']
    for directive in required_directives:
        assert directive in csp_header, f"Missing {directive} directive"
    
    # Check for unsafe patterns
    unsafe_patterns = ["'unsafe-inline'", "'unsafe-eval'"]
    for pattern in unsafe_patterns:
        if pattern in csp_header:
            logger.warning(f"Unsafe pattern found: {pattern}")
```

#### **Resource Loading Testing**
```python
def test_resource_loading():
    """Test that all required resources load with CSP"""
    resources = [
        '/static/css/style.css',
        '/static/js/app.js',
        'https://js.stripe.com/v3/',
        'https://fonts.googleapis.com/css2?family=Inter'
    ]
    
    for resource in resources:
        try:
            response = requests.get(resource)
            assert response.status_code == 200, f"Failed to load {resource}"
        except Exception as e:
            logger.error(f"Error loading {resource}: {e}")
```

#### **Browser Compatibility Testing**
```python
def test_browser_compatibility():
    """Test CSP compatibility across browsers"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/91.0.4472.124',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15'
    ]
    
    for user_agent in user_agents:
        headers = {'User-Agent': user_agent}
        response = requests.get(base_url, headers=headers)
        assert 'Content-Security-Policy' in response.headers, f"CSP header missing for {user_agent}"
```

### Manual Testing Checklist

#### **Functionality Testing**
- [ ] Login/logout functionality works
- [ ] Payment processing (Stripe) works
- [ ] Analytics tracking works
- [ ] Form submissions work
- [ ] Dynamic content loads correctly
- [ ] Service worker registration works

#### **Security Testing**
- [ ] XSS attempts are blocked
- [ ] Inline scripts are blocked (without nonce)
- [ ] External scripts from unauthorized domains are blocked
- [ ] Clickjacking attempts are prevented
- [ ] Mixed content is blocked

#### **Performance Testing**
- [ ] Page load times are acceptable
- [ ] No significant performance impact from CSP
- [ ] Resource loading is optimized
- [ ] Violation reporting doesn't impact performance

## 📚 Best Practices

### Security Best Practices

#### **1. Principle of Least Privilege**
```python
# Good: Specific domains only
'script-src': ["'self'", "https://js.stripe.com", "https://checkout.stripe.com"]

# Bad: Too permissive
'script-src': ["'self'", "https:", "'unsafe-inline'"]
```

#### **2. Use Nonces for Inline Scripts**
```html
<!-- Good: Use nonce -->
<script nonce="{{ csp_nonce }}">
    // Inline script content
</script>

<!-- Bad: No nonce -->
<script>
    // This will be blocked
</script>
```

#### **3. Block Dangerous Directives**
```python
# Always block object-src
'object-src': ["'none'"],

# Block frame-ancestors to prevent clickjacking
'frame-ancestors': ["'none'"]
```

#### **4. Upgrade Insecure Requests**
```python
# Force HTTPS
'upgrade-insecure-requests': [],
'block-all-mixed-content': []
```

### Development Best Practices

#### **1. Start with Report-Only Mode**
```python
# Development: Report-only mode
CSPConfig(report_only=True)

# Production: Enforced mode
CSPConfig(report_only=False)
```

#### **2. Monitor Violations**
```python
# Set up violation monitoring
def monitor_violations():
    violations = get_recent_violations()
    for violation in violations:
        if is_critical(violation):
            send_alert(violation)
        log_violation(violation)
```

#### **3. Regular Policy Reviews**
```python
# Monthly policy review
def review_csp_policy():
    violations = analyze_violations()
    unused_domains = find_unused_domains()
    recommendations = generate_recommendations(violations, unused_domains)
    return recommendations
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### **1. Scripts Not Loading**
```javascript
// Problem: External script blocked
// Solution: Add domain to script-src
'script-src': ["'self'", "https://cdn.example.com"]

// Problem: Inline script blocked
// Solution: Add nonce
<script nonce="{{ csp_nonce }}">...</script>
```

#### **2. Styles Not Loading**
```css
/* Problem: External styles blocked */
/* Solution: Add domain to style-src */
'style-src': ["'self'", "https://fonts.googleapis.com"]

/* Problem: Inline styles blocked */
/* Solution: Add 'unsafe-inline' or use nonces */
'style-src': ["'self'", "'unsafe-inline'"]
```

#### **3. API Calls Failing**
```javascript
// Problem: API call blocked
// Solution: Add domain to connect-src
'connect-src': ["'self'", "https://api.example.com"]
```

#### **4. Images Not Loading**
```html
<!-- Problem: External images blocked -->
<!-- Solution: Add domain to img-src -->
'img-src': ["'self'", "https://images.example.com"]
```

### Debugging Tools

#### **1. Browser Developer Tools**
```javascript
// Check CSP violations in console
// Look for messages like:
// "Refused to load the script 'https://example.com/script.js' 
//  because it violates the following Content Security Policy directive: script-src 'self'"
```

#### **2. CSP Violation Reports**
```python
# Monitor violation reports
@app.route('/csp-violation-report', methods=['POST'])
def handle_violation():
    violation = request.get_json()
    logger.warning(f"CSP Violation: {violation}")
    # Store for analysis
```

#### **3. Online CSP Validators**
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [CSP Builder](https://report-uri.com/home/generate/)
- [Mozilla CSP Validator](https://observatory.mozilla.org/)

## 📊 Monitoring and Analytics

### Violation Monitoring

#### **Real-time Monitoring**
```python
def monitor_csp_violations():
    """Real-time CSP violation monitoring"""
    violations = get_recent_violations(hours=1)
    
    # Alert on critical violations
    critical_violations = [v for v in violations if is_critical(v)]
    if critical_violations:
        send_alert(f"Critical CSP violations detected: {len(critical_violations)}")
    
    # Log all violations
    for violation in violations:
        log_violation(violation)
```

#### **Analytics Dashboard**
```python
def generate_csp_analytics():
    """Generate CSP analytics report"""
    violations = get_violations_by_period(days=30)
    
    analytics = {
        'total_violations': len(violations),
        'violations_by_directive': group_by_directive(violations),
        'violations_by_domain': group_by_domain(violations),
        'trends': analyze_trends(violations),
        'recommendations': generate_recommendations(violations)
    }
    
    return analytics
```

### Performance Monitoring

#### **CSP Impact Analysis**
```python
def analyze_csp_performance_impact():
    """Analyze CSP performance impact"""
    metrics = {
        'page_load_time': measure_page_load_time(),
        'resource_blocking_time': measure_resource_blocking(),
        'violation_reporting_overhead': measure_reporting_overhead()
    }
    
    return metrics
```

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] CSP policy configured for production
- [ ] All required domains whitelisted
- [ ] Nonces implemented for inline scripts
- [ ] Violation reporting configured
- [ ] Monitoring and alerting set up

### Deployment
- [ ] Deploy with report-only mode first
- [ ] Monitor violations for 24-48 hours
- [ ] Address any critical violations
- [ ] Switch to enforced mode
- [ ] Continue monitoring

### Post-Deployment
- [ ] Monitor violation reports
- [ ] Track performance metrics
- [ ] Review and update policy monthly
- [ ] Document any policy changes

## 📞 Support and Resources

### Documentation
- [MDN CSP Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSP Level 3 Specification](https://www.w3.org/TR/CSP3/)
- [Google CSP Guide](https://developers.google.com/web/fundamentals/security/csp)

### Tools
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [Report URI](https://report-uri.com/)
- [CSP Builder](https://report-uri.com/home/generate/)

### Testing
- [CSP Test Suite](csp_test_suite.py)
- [Browser Developer Tools](https://developer.chrome.com/docs/devtools/)
- [Online CSP Validators](https://observatory.mozilla.org/)

---

**Note**: This CSP implementation is designed for financial applications and follows industry best practices for security. Regular reviews and updates are recommended to maintain optimal security posture.
