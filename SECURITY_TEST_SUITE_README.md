# Comprehensive Security Test Suite for MINGUS Assessment System

## Overview

This comprehensive security test suite provides automated security testing for the MINGUS Assessment System, covering input validation, authentication, authorization, data protection, and compliance with industry standards.

## Features

### 🔍 Security Test Categories

1. **Input Validation Security Tests**
   - SQL injection prevention
   - XSS (Cross-Site Scripting) prevention
   - Command injection prevention
   - NoSQL injection prevention
   - Valid input acceptance testing

2. **JWT Security Tests**
   - Token validation with IP address consistency
   - User-Agent validation
   - Token expiration handling
   - Token blacklisting
   - Token tampering detection

3. **Rate Limiting Tests**
   - Assessment submission rate limiting
   - Login attempt rate limiting
   - API endpoint rate limiting

4. **CSRF Protection Tests**
   - CSRF token requirement validation
   - Invalid token rejection
   - Valid token acceptance

5. **Security Headers Tests**
   - Content Security Policy (CSP)
   - HTTP Strict Transport Security (HSTS)
   - X-Frame-Options
   - X-Content-Type-Options
   - X-XSS-Protection

6. **Security Monitoring Tests**
   - Security event logging
   - Alert threshold triggering
   - Suspicious behavior detection

7. **Penetration Testing Scenarios**
   - Authentication bypass attempts
   - Privilege escalation attempts
   - Mass assignment vulnerability testing
   - Directory traversal attempts
   - SQL injection attempts
   - XSS attempts

8. **Data Protection Tests**
   - PII detection and masking
   - Data encryption/decryption
   - Privacy compliance

### 🏛️ Compliance Frameworks

The test suite includes compliance analysis for:

- **OWASP Top 10 2021**
- **NIST Cybersecurity Framework**
- **ISO 27001**
- **SOC 2**
- **GDPR**
- **CCPA**

### 📊 Reporting and Analytics

- Comprehensive HTML reports
- JSON data export
- Markdown documentation
- Compliance scoring
- Risk assessment
- Remediation planning

## Installation

### Prerequisites

- Python 3.9+
- pip
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mingus-assessment-system
   ```

2. **Install security testing dependencies**
   ```bash
   pip install -r requirements-security.txt
   ```

3. **Install additional tools (optional)**
   ```bash
   # For enhanced security scanning
   pip install semgrep trufflehog detect-secrets
   
   # For web security testing
   pip install zap-cli nikto
   ```

## Usage

### Running Security Tests

#### 1. Run All Security Tests
```bash
python scripts/run_security_tests.py
```

#### 2. Run Specific Test Categories
```bash
# Input validation tests only
pytest tests/security/test_comprehensive_security_suite.py::TestInputValidation -v

# JWT security tests only
pytest tests/security/test_comprehensive_security_suite.py::TestJWTSecurity -v

# Rate limiting tests only
pytest tests/security/test_comprehensive_security_suite.py::TestRateLimiting -v
```

#### 3. Run with Custom Configuration
```bash
python scripts/run_security_tests.py --config security_config.json
```

### Configuration Options

Create a `security_config.json` file:

```json
{
  "test_paths": [
    "tests/security/",
    "tests/test_comprehensive_security_suite.py"
  ],
  "output_formats": ["xml", "html", "json"],
  "fail_on_critical": true,
  "generate_reports": true,
  "coverage_threshold": 80,
  "timeout_minutes": 30,
  "parallel_jobs": 4,
  "verbose": true
}
```

### Command Line Options

```bash
python scripts/run_security_tests.py [OPTIONS]

Options:
  --config PATH              Path to configuration file
  --fail-on-critical         Fail deployment if critical security tests fail
  --generate-reports         Generate security test reports
  --verbose                  Enable verbose output
```

## CI/CD Integration

### GitHub Actions

The security tests are automatically integrated into the CI/CD pipeline via GitHub Actions:

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### Jenkins Integration

Add to your Jenkins pipeline:

```groovy
stage('Security Tests') {
    steps {
        script {
            sh 'python scripts/run_security_tests.py --fail-on-critical'
        }
    }
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'security_test_report.html',
                reportName: 'Security Test Report'
            ])
        }
    }
}
```

### Azure DevOps

Add to your Azure pipeline:

```yaml
- task: PythonScript@0
  inputs:
    scriptSource: 'filePath'
    scriptPath: 'scripts/run_security_tests.py'
    arguments: '--fail-on-critical --generate-reports'
  displayName: 'Run Security Tests'

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: 'reports/*.xml'
    mergeTestResults: true
  condition: always()
```

## Compliance Reporting

### Generate Compliance Reports

```bash
python scripts/generate_compliance_report.py
```

### Compliance Report Features

- **Executive Summary**: High-level compliance status
- **Framework Analysis**: Detailed compliance scores for each framework
- **Risk Assessment**: Overall risk level and factor analysis
- **Recommendations**: Prioritized security improvements
- **Remediation Plan**: Actionable timeline for fixes

### Compliance Thresholds

- **Compliant**: ≥85% compliance score
- **Non-Compliant**: <85% compliance score
- **Critical Failures**: Immediate action required

## Security Tools Integration

### Static Code Analysis

```bash
# Run bandit for Python security analysis
bandit -r backend/ -f json -o reports/bandit_results.json

# Run semgrep for advanced pattern matching
semgrep --config=auto backend/ -o reports/semgrep_results.json

# Run trufflehog for secrets detection
trufflehog --json . > reports/trufflehog_results.json
```

### Dependency Scanning

```bash
# Run safety for dependency vulnerabilities
safety check --json --output reports/safety_results.json

# Run pip-audit for comprehensive scanning
pip-audit --format json --output reports/pip_audit_results.json
```

### Web Security Testing

```bash
# Run OWASP ZAP for web application security
zap-cli quick-scan --self-contained http://localhost:5000

# Run nikto for web server security
nikto -h http://localhost:5000 -o reports/nikto_results.txt
```

## Test Results and Reports

### Report Locations

- **Security Test Reports**: `reports/security_test_report.html`
- **Compliance Reports**: `reports/compliance_report.html`
- **JUnit XML**: `reports/*_results.xml`
- **JSON Data**: `reports/security_test_summary.json`
- **Markdown**: `reports/security_test_report.md`

### Report Contents

1. **Test Summary**
   - Total tests executed
   - Pass/fail statistics
   - Critical failures
   - Execution time

2. **Detailed Results**
   - Individual test results
   - Error messages and stack traces
   - Performance metrics

3. **Compliance Analysis**
   - Framework-specific scores
   - Compliance status
   - Risk assessment
   - Recommendations

4. **Remediation Plan**
   - Immediate actions (1-7 days)
   - Short-term actions (1-4 weeks)
   - Long-term actions (1-6 months)

## Security Best Practices

### Development Guidelines

1. **Input Validation**
   - Always validate and sanitize user input
   - Use parameterized queries
   - Implement proper error handling

2. **Authentication & Authorization**
   - Use secure JWT implementation
   - Implement proper session management
   - Validate user permissions

3. **Data Protection**
   - Encrypt sensitive data at rest and in transit
   - Implement proper key management
   - Follow privacy regulations

4. **Configuration Security**
   - Use secure default configurations
   - Implement proper security headers
   - Regular security updates

### Testing Guidelines

1. **Regular Testing**
   - Run security tests on every commit
   - Schedule daily automated scans
   - Perform manual penetration testing quarterly

2. **Continuous Monitoring**
   - Monitor security events
   - Set up alerting for suspicious activities
   - Regular compliance assessments

3. **Incident Response**
   - Document security incidents
   - Implement proper escalation procedures
   - Regular incident response drills

## Troubleshooting

### Common Issues

1. **Test Failures**
   ```bash
   # Check test logs
   cat reports/security_test_summary.json
   
   # Run with verbose output
   python scripts/run_security_tests.py --verbose
   ```

2. **Dependency Issues**
   ```bash
   # Update security dependencies
   pip install -r requirements-security.txt --upgrade
   
   # Check for conflicts
   pip check
   ```

3. **Configuration Issues**
   ```bash
   # Validate configuration
   python -c "import json; json.load(open('security_config.json'))"
   ```

### Performance Optimization

1. **Parallel Execution**
   ```bash
   # Run tests in parallel
   pytest tests/security/ -n auto
   ```

2. **Selective Testing**
   ```bash
   # Run only critical tests
   pytest tests/security/ -m "critical"
   ```

3. **Caching**
   ```bash
   # Use pytest cache
   pytest tests/security/ --cache-clear
   ```

## Contributing

### Adding New Tests

1. **Create test class**
   ```python
   class TestNewSecurityFeature:
       def setup_method(self):
           self.app = create_app('testing')
           self.client = self.app.test_client()
       
       def test_new_security_feature(self):
           # Test implementation
           pass
   ```

2. **Add to test suite**
   ```python
   # Add to test_comprehensive_security_suite.py
   class TestNewSecurityFeature:
       # Test methods
   ```

3. **Update CI/CD**
   ```yaml
   # Add to GitHub Actions workflow
   - name: Run New Security Tests
     run: pytest tests/security/test_comprehensive_security_suite.py::TestNewSecurityFeature
   ```

### Reporting Issues

1. **Security Vulnerabilities**
   - Report via secure channel
   - Include detailed reproduction steps
   - Provide proof of concept

2. **Test Failures**
   - Include test logs
   - Describe environment
   - Provide minimal reproduction case

## Support

### Documentation

- [Security Implementation Guide](ASSESSMENT_SECURITY_IMPLEMENTATION_GUIDE.md)
- [Comprehensive Security Monitoring](COMPREHENSIVE_SECURITY_MONITORING_IMPLEMENTATION.md)
- [API Security Documentation](ASSESSMENT_API_DOCUMENTATION.md)

### Contact

- **Security Team**: security@mingus.com
- **Development Team**: dev@mingus.com
- **Compliance Team**: compliance@mingus.com

## License

This security test suite is proprietary to MINGUS and confidential. Unauthorized distribution or use is prohibited.

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: MINGUS Security Team
