"""
Comprehensive Security Testing Suite for MINGUS
Validates all security measures are working correctly
"""

import os
import sys
import json
import time
import hashlib
import requests
import subprocess
import threading
import ssl
import socket
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import unittest
import pytest
from loguru import logger
import asyncio
import aiohttp
import sqlite3
import psutil
import yaml

class TestCategory(Enum):
    """Security test categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    NETWORK_SECURITY = "network_security"
    APPLICATION_SECURITY = "application_security"
    DATA_PROTECTION = "data_protection"
    MONITORING = "monitoring"
    BACKUP_SECURITY = "backup_security"
    COMPLIANCE = "compliance"
    INTEGRATION = "integration"

class TestSeverity(Enum):
    """Test severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TestStatus(Enum):
    """Test status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class SecurityTest:
    """Security test structure"""
    test_id: str
    name: str
    category: TestCategory
    severity: TestSeverity
    description: str
    test_function: Callable
    expected_result: Any
    timeout: int = 30
    dependencies: List[str] = field(default_factory=list)

@dataclass
class TestResult:
    """Test result structure"""
    test_id: str
    status: TestStatus
    execution_time: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class SecurityTestSuite:
    """Comprehensive security testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000", config_path: str = "/etc/mingus/security_tests.yml"):
        self.base_url = base_url
        self.config_path = config_path
        self.test_results = []
        self.test_registry = {}
        self.session = requests.Session()
        
        # Load test configuration
        self.config = self._load_test_config()
        
        # Register all security tests
        self._register_security_tests()
    
    def _load_test_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        default_config = {
            "test_timeout": 30,
            "max_retries": 3,
            "parallel_tests": 5,
            "test_categories": ["all"],
            "exclude_tests": [],
            "test_credentials": {
                "admin_user": "admin",
                "admin_password": "admin_password",
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
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                default_config.update(config)
        
        return default_config
    
    def _register_security_tests(self):
        """Register all security tests"""
        # Authentication tests
        self._register_auth_tests()
        
        # Authorization tests
        self._register_authz_tests()
        
        # Encryption tests
        self._register_encryption_tests()
        
        # Network security tests
        self._register_network_tests()
        
        # Application security tests
        self._register_app_security_tests()
        
        # Data protection tests
        self._register_data_protection_tests()
        
        # Monitoring tests
        self._register_monitoring_tests()
        
        # Backup security tests
        self._register_backup_security_tests()
        
        # Compliance tests
        self._register_compliance_tests()
        
        # Integration tests
        self._register_integration_tests()
    
    def _register_auth_tests(self):
        """Register authentication tests"""
        self.register_test(SecurityTest(
            test_id="auth_001",
            name="Password Strength Validation",
            category=TestCategory.AUTHENTICATION,
            severity=TestSeverity.HIGH,
            description="Test password strength requirements",
            test_function=self._test_password_strength,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="auth_002",
            name="Login Rate Limiting",
            category=TestCategory.AUTHENTICATION,
            severity=TestSeverity.HIGH,
            description="Test login rate limiting",
            test_function=self._test_login_rate_limiting,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="auth_003",
            name="Session Management",
            category=TestCategory.AUTHENTICATION,
            severity=TestSeverity.MEDIUM,
            description="Test session management security",
            test_function=self._test_session_management,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="auth_004",
            name="MFA Implementation",
            category=TestCategory.AUTHENTICATION,
            severity=TestSeverity.HIGH,
            description="Test multi-factor authentication",
            test_function=self._test_mfa_implementation,
            expected_result=True
        ))
    
    def _register_authz_tests(self):
        """Register authorization tests"""
        self.register_test(SecurityTest(
            test_id="authz_001",
            name="Role-Based Access Control",
            category=TestCategory.AUTHORIZATION,
            severity=TestSeverity.HIGH,
            description="Test RBAC implementation",
            test_function=self._test_rbac_implementation,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="authz_002",
            name="API Authorization",
            category=TestCategory.AUTHORIZATION,
            severity=TestSeverity.HIGH,
            description="Test API endpoint authorization",
            test_function=self._test_api_authorization,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="authz_003",
            name="Resource Access Control",
            category=TestCategory.AUTHORIZATION,
            severity=TestSeverity.MEDIUM,
            description="Test resource access controls",
            test_function=self._test_resource_access_control,
            expected_result=True
        ))
    
    def _register_encryption_tests(self):
        """Register encryption tests"""
        self.register_test(SecurityTest(
            test_id="enc_001",
            name="Data Encryption at Rest",
            category=TestCategory.ENCRYPTION,
            severity=TestSeverity.HIGH,
            description="Test data encryption at rest",
            test_function=self._test_encryption_at_rest,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="enc_002",
            name="Data Encryption in Transit",
            category=TestCategory.ENCRYPTION,
            severity=TestSeverity.HIGH,
            description="Test data encryption in transit",
            test_function=self._test_encryption_in_transit,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="enc_003",
            name="Key Management",
            category=TestCategory.ENCRYPTION,
            severity=TestSeverity.HIGH,
            description="Test encryption key management",
            test_function=self._test_key_management,
            expected_result=True
        ))
    
    def _register_network_tests(self):
        """Register network security tests"""
        self.register_test(SecurityTest(
            test_id="net_001",
            name="SSL/TLS Configuration",
            category=TestCategory.NETWORK_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test SSL/TLS configuration",
            test_function=self._test_ssl_tls_configuration,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="net_002",
            name="Security Headers",
            category=TestCategory.NETWORK_SECURITY,
            severity=TestSeverity.MEDIUM,
            description="Test security headers",
            test_function=self._test_security_headers,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="net_003",
            name="Firewall Configuration",
            category=TestCategory.NETWORK_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test firewall configuration",
            test_function=self._test_firewall_configuration,
            expected_result=True
        ))
    
    def _register_app_security_tests(self):
        """Register application security tests"""
        self.register_test(SecurityTest(
            test_id="app_001",
            name="SQL Injection Prevention",
            category=TestCategory.APPLICATION_SECURITY,
            severity=TestSeverity.CRITICAL,
            description="Test SQL injection prevention",
            test_function=self._test_sql_injection_prevention,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="app_002",
            name="XSS Prevention",
            category=TestCategory.APPLICATION_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test XSS prevention",
            test_function=self._test_xss_prevention,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="app_003",
            name="CSRF Protection",
            category=TestCategory.APPLICATION_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test CSRF protection",
            test_function=self._test_csrf_protection,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="app_004",
            name="Input Validation",
            category=TestCategory.APPLICATION_SECURITY,
            severity=TestSeverity.MEDIUM,
            description="Test input validation",
            test_function=self._test_input_validation,
            expected_result=True
        ))
    
    def _register_data_protection_tests(self):
        """Register data protection tests"""
        self.register_test(SecurityTest(
            test_id="data_001",
            name="Data Anonymization",
            category=TestCategory.DATA_PROTECTION,
            severity=TestSeverity.MEDIUM,
            description="Test data anonymization",
            test_function=self._test_data_anonymization,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="data_002",
            name="Data Retention",
            category=TestCategory.DATA_PROTECTION,
            severity=TestSeverity.MEDIUM,
            description="Test data retention policies",
            test_function=self._test_data_retention,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="data_003",
            name="Data Access Logging",
            category=TestCategory.DATA_PROTECTION,
            severity=TestSeverity.MEDIUM,
            description="Test data access logging",
            test_function=self._test_data_access_logging,
            expected_result=True
        ))
    
    def _register_monitoring_tests(self):
        """Register monitoring tests"""
        self.register_test(SecurityTest(
            test_id="mon_001",
            name="Security Event Monitoring",
            category=TestCategory.MONITORING,
            severity=TestSeverity.HIGH,
            description="Test security event monitoring",
            test_function=self._test_security_event_monitoring,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="mon_002",
            name="Alert System",
            category=TestCategory.MONITORING,
            severity=TestSeverity.HIGH,
            description="Test alert system",
            test_function=self._test_alert_system,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="mon_003",
            name="Log Management",
            category=TestCategory.MONITORING,
            severity=TestSeverity.MEDIUM,
            description="Test log management",
            test_function=self._test_log_management,
            expected_result=True
        ))
    
    def _register_backup_security_tests(self):
        """Register backup security tests"""
        self.register_test(SecurityTest(
            test_id="backup_001",
            name="Backup Encryption",
            category=TestCategory.BACKUP_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test backup encryption",
            test_function=self._test_backup_encryption,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="backup_002",
            name="Backup Access Control",
            category=TestCategory.BACKUP_SECURITY,
            severity=TestSeverity.HIGH,
            description="Test backup access control",
            test_function=self._test_backup_access_control,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="backup_003",
            name="Backup Integrity",
            category=TestCategory.BACKUP_SECURITY,
            severity=TestSeverity.MEDIUM,
            description="Test backup integrity",
            test_function=self._test_backup_integrity,
            expected_result=True
        ))
    
    def _register_compliance_tests(self):
        """Register compliance tests"""
        self.register_test(SecurityTest(
            test_id="comp_001",
            name="GDPR Compliance",
            category=TestCategory.COMPLIANCE,
            severity=TestSeverity.HIGH,
            description="Test GDPR compliance",
            test_function=self._test_gdpr_compliance,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="comp_002",
            name="Data Privacy Controls",
            category=TestCategory.COMPLIANCE,
            severity=TestSeverity.HIGH,
            description="Test data privacy controls",
            test_function=self._test_data_privacy_controls,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="comp_003",
            name="Audit Trail",
            category=TestCategory.COMPLIANCE,
            severity=TestSeverity.MEDIUM,
            description="Test audit trail",
            test_function=self._test_audit_trail,
            expected_result=True
        ))
    
    def _register_integration_tests(self):
        """Register integration tests"""
        self.register_test(SecurityTest(
            test_id="int_001",
            name="Security Integration",
            category=TestCategory.INTEGRATION,
            severity=TestSeverity.HIGH,
            description="Test security integration",
            test_function=self._test_security_integration,
            expected_result=True
        ))
        
        self.register_test(SecurityTest(
            test_id="int_002",
            name="End-to-End Security",
            category=TestCategory.INTEGRATION,
            severity=TestSeverity.HIGH,
            description="Test end-to-end security",
            test_function=self._test_end_to_end_security,
            expected_result=True
        ))
    
    def register_test(self, test: SecurityTest):
        """Register a security test"""
        self.test_registry[test.test_id] = test
    
    def run_all_tests(self, categories: List[str] = None) -> List[TestResult]:
        """Run all security tests"""
        logger.info("Starting comprehensive security test suite")
        
        if categories is None:
            categories = ["all"]
        
        # Filter tests by category
        tests_to_run = []
        for test in self.test_registry.values():
            if "all" in categories or test.category.value in categories:
                tests_to_run.append(test)
        
        logger.info(f"Running {len(tests_to_run)} security tests")
        
        # Run tests
        results = []
        for test in tests_to_run:
            result = self._run_single_test(test)
            results.append(result)
            
            # Log result
            if result.status == TestStatus.PASSED:
                logger.info(f"✓ {test.name} - PASSED")
            elif result.status == TestStatus.FAILED:
                logger.error(f"✗ {test.name} - FAILED: {result.error_message}")
            elif result.status == TestStatus.SKIPPED:
                logger.warning(f"- {test.name} - SKIPPED: {result.error_message}")
            else:
                logger.error(f"! {test.name} - ERROR: {result.error_message}")
        
        self.test_results.extend(results)
        return results
    
    def _run_single_test(self, test: SecurityTest) -> TestResult:
        """Run a single security test"""
        start_time = time.time()
        
        try:
            # Check dependencies
            for dependency in test.dependencies:
                if not self._check_dependency(dependency):
                    return TestResult(
                        test_id=test.test_id,
                        status=TestStatus.SKIPPED,
                        execution_time=time.time() - start_time,
                        error_message=f"Dependency not met: {dependency}"
                    )
            
            # Run test with timeout
            result = self._run_test_with_timeout(test)
            
            return TestResult(
                test_id=test.test_id,
                status=TestStatus.PASSED if result == test.expected_result else TestStatus.FAILED,
                execution_time=time.time() - start_time,
                error_message=None if result == test.expected_result else f"Expected {test.expected_result}, got {result}",
                details={"actual_result": result}
            )
            
        except Exception as e:
            return TestResult(
                test_id=test.test_id,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _run_test_with_timeout(self, test: SecurityTest):
        """Run test with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Test {test.test_id} timed out after {test.timeout} seconds")
        
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(test.timeout)
        
        try:
            result = test.test_function()
            signal.alarm(0)  # Cancel timeout
            return result
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            raise e
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is met"""
        # This would check various dependencies like services running, etc.
        return True
    
    # Authentication Tests
    def _test_password_strength(self) -> bool:
        """Test password strength requirements"""
        weak_passwords = ["123456", "password", "admin", "qwerty"]
        strong_passwords = ["Str0ngP@ssw0rd!", "C0mpl3x!P@ss", "S3cur3!P@ssw0rd"]
        
        for password in weak_passwords:
            if self._is_password_strong(password):
                return False
        
        for password in strong_passwords:
            if not self._is_password_strong(password):
                return False
        
        return True
    
    def _test_login_rate_limiting(self) -> bool:
        """Test login rate limiting"""
        # Attempt multiple login failures
        for i in range(10):
            response = self.session.post(
                f"{self.base_url}{self.config['test_endpoints']['login']}",
                json={"username": "test", "password": "wrong_password"}
            )
            
            if i < 5 and response.status_code == 429:  # Too Many Requests
                return True
        
        return False
    
    def _test_session_management(self) -> bool:
        """Test session management security"""
        # Login and get session
        response = self.session.post(
            f"{self.base_url}{self.config['test_endpoints']['login']}",
            json={
                "username": self.config["test_credentials"]["admin_user"],
                "password": self.config["test_credentials"]["admin_password"]
            }
        )
        
        if response.status_code != 200:
            return False
        
        # Check session security headers
        session_response = self.session.get(f"{self.base_url}{self.config['test_endpoints']['protected']}")
        
        # Check for secure session attributes
        cookies = self.session.cookies
        for cookie in cookies:
            if not cookie.secure and not cookie.has_nonstandard_attr('HttpOnly'):
                return False
        
        return True
    
    def _test_mfa_implementation(self) -> bool:
        """Test multi-factor authentication"""
        # Check if MFA endpoints exist
        mfa_endpoints = ["/api/auth/mfa/setup", "/api/auth/mfa/verify"]
        
        for endpoint in mfa_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                return False
        
        return True
    
    # Authorization Tests
    def _test_rbac_implementation(self) -> bool:
        """Test role-based access control"""
        # Login as regular user
        response = self.session.post(
            f"{self.base_url}{self.config['test_endpoints']['login']}",
            json={
                "username": self.config["test_credentials"]["regular_user"],
                "password": self.config["test_credentials"]["regular_password"]
            }
        )
        
        if response.status_code != 200:
            return False
        
        # Try to access admin endpoint
        admin_response = self.session.get(f"{self.base_url}{self.config['test_endpoints']['admin']}")
        
        # Should be denied
        return admin_response.status_code == 403
    
    def _test_api_authorization(self) -> bool:
        """Test API endpoint authorization"""
        # Test protected endpoints without authentication
        protected_endpoints = ["/api/admin", "/api/users", "/api/settings"]
        
        for endpoint in protected_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code != 401:  # Should require authentication
                return False
        
        return True
    
    def _test_resource_access_control(self) -> bool:
        """Test resource access controls"""
        # Test file access controls
        sensitive_files = ["/etc/passwd", "/etc/shadow", "/var/log/auth.log"]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                # Check file permissions
                stat = os.stat(file_path)
                if stat.st_mode & 0o777 == 0o777:  # Too permissive
                    return False
        
        return True
    
    # Encryption Tests
    def _test_encryption_at_rest(self) -> bool:
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
                    if not self._is_encrypted_content(content):
                        return False
        
        return True
    
    def _test_encryption_in_transit(self) -> bool:
        """Test data encryption in transit"""
        # Check if HTTPS is enabled
        if not self.base_url.startswith("https://"):
            return False
        
        # Test SSL/TLS configuration
        try:
            response = self.session.get(f"{self.base_url}{self.config['test_endpoints']['health']}")
            return response.status_code == 200
        except:
            return False
    
    def _test_key_management(self) -> bool:
        """Test encryption key management"""
        # Check key file permissions
        key_files = ["/var/lib/mingus/backups/backup_encryption.key"]
        
        for key_file in key_files:
            if os.path.exists(key_file):
                stat = os.stat(key_file)
                if stat.st_mode & 0o777 != 0o600:  # Should be 600
                    return False
        
        return True
    
    # Network Security Tests
    def _test_ssl_tls_configuration(self) -> bool:
        """Test SSL/TLS configuration"""
        if not self.base_url.startswith("https://"):
            return False
        
        try:
            # Test SSL configuration
            hostname = self.base_url.replace("https://", "").split(":")[0]
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
    
    def _test_security_headers(self) -> bool:
        """Test security headers"""
        response = self.session.get(f"{self.base_url}{self.config['test_endpoints']['health']}")
        
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
    
    def _test_firewall_configuration(self) -> bool:
        """Test firewall configuration"""
        # Check if common attack ports are closed
        attack_ports = [22, 23, 3389, 5900]
        
        for port in attack_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:  # Port is open
                    return False
            except:
                pass
        
        return True
    
    # Application Security Tests
    def _test_sql_injection_prevention(self) -> bool:
        """Test SQL injection prevention"""
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_injection_payloads:
            response = self.session.post(
                f"{self.base_url}/api/search",
                json={"query": payload}
            )
            
            # Should not return sensitive data
            if "admin" in response.text.lower() or "password" in response.text.lower():
                return False
        
        return True
    
    def _test_xss_prevention(self) -> bool:
        """Test XSS prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            response = self.session.post(
                f"{self.base_url}/api/comment",
                json={"content": payload}
            )
            
            # Check if payload is escaped
            if payload in response.text:
                return False
        
        return True
    
    def _test_csrf_protection(self) -> bool:
        """Test CSRF protection"""
        # Check for CSRF tokens in forms
        response = self.session.get(f"{self.base_url}/api/form")
        
        if "csrf_token" not in response.text and "X-CSRF-Token" not in response.headers:
            return False
        
        return True
    
    def _test_input_validation(self) -> bool:
        """Test input validation"""
        malicious_inputs = [
            "../../../etc/passwd",
            "<script>",
            "javascript:",
            "data:text/html,<script>alert('XSS')</script>"
        ]
        
        for input_data in malicious_inputs:
            response = self.session.post(
                f"{self.base_url}/api/upload",
                json={"filename": input_data}
            )
            
            # Should reject malicious input
            if response.status_code == 200:
                return False
        
        return True
    
    # Data Protection Tests
    def _test_data_anonymization(self) -> bool:
        """Test data anonymization"""
        # Check if sensitive data is properly anonymized
        response = self.session.get(f"{self.base_url}/api/users")
        
        if response.status_code == 200:
            data = response.json()
            for user in data:
                if "password" in user or "ssn" in user:
                    return False
        
        return True
    
    def _test_data_retention(self) -> bool:
        """Test data retention policies"""
        # Check if old data is properly deleted
        old_data_response = self.session.get(f"{self.base_url}/api/old-data")
        
        # Should not return data older than retention period
        if old_data_response.status_code == 200:
            data = old_data_response.json()
            for item in data:
                if "created_at" in item:
                    created_date = datetime.fromisoformat(item["created_at"])
                    if created_date < datetime.utcnow() - timedelta(days=365):
                        return False
        
        return True
    
    def _test_data_access_logging(self) -> bool:
        """Test data access logging"""
        # Check if data access is logged
        log_file = "/var/log/mingus/data_access.log"
        
        if os.path.exists(log_file):
            # Make a data access request
            self.session.get(f"{self.base_url}/api/sensitive-data")
            
            # Check if access was logged
            time.sleep(1)
            with open(log_file, 'r') as f:
                log_content = f.read()
                if "sensitive-data" not in log_content:
                    return False
        
        return True
    
    # Monitoring Tests
    def _test_security_event_monitoring(self) -> bool:
        """Test security event monitoring"""
        # Trigger a security event
        self.session.post(
            f"{self.base_url}{self.config['test_endpoints']['login']}",
            json={"username": "test", "password": "wrong_password"}
        )
        
        # Check if event was logged
        log_file = "/var/log/mingus/security.log"
        
        if os.path.exists(log_file):
            time.sleep(1)
            with open(log_file, 'r') as f:
                log_content = f.read()
                if "failed_login" in log_content:
                    return True
        
        return False
    
    def _test_alert_system(self) -> bool:
        """Test alert system"""
        # Check if alert endpoints exist
        alert_endpoints = ["/api/alerts", "/api/monitoring/status"]
        
        for endpoint in alert_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                return False
        
        return True
    
    def _test_log_management(self) -> bool:
        """Test log management"""
        # Check if log files exist and are writable
        log_files = [
            "/var/log/mingus/app.log",
            "/var/log/mingus/security.log",
            "/var/log/mingus/error.log"
        ]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                return False
            
            # Check if log file is writable
            if not os.access(log_file, os.W_OK):
                return False
        
        return True
    
    # Backup Security Tests
    def _test_backup_encryption(self) -> bool:
        """Test backup encryption"""
        # Check if backup files are encrypted
        backup_files = [
            "/var/lib/mingus/backups/full_system_backup.tar.gz.encrypted",
            "/var/lib/mingus/backups/database_backup.sql.encrypted"
        ]
        
        for backup_file in backup_files:
            if os.path.exists(backup_file):
                with open(backup_file, 'rb') as f:
                    content = f.read(100)
                    if not self._is_encrypted_content(content):
                        return False
        
        return True
    
    def _test_backup_access_control(self) -> bool:
        """Test backup access control"""
        # Check backup file permissions
        backup_files = [
            "/var/lib/mingus/backups/",
            "/var/lib/mingus/backups/backup_encryption.key"
        ]
        
        for backup_path in backup_files:
            if os.path.exists(backup_path):
                stat = os.stat(backup_path)
                if stat.st_mode & 0o777 == 0o777:  # Too permissive
                    return False
        
        return True
    
    def _test_backup_integrity(self) -> bool:
        """Test backup integrity"""
        # Check if backup verification is working
        backup_verification_endpoint = "/api/backup/verify"
        
        response = self.session.get(f"{self.base_url}{backup_verification_endpoint}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("integrity_check", False)
        
        return False
    
    # Compliance Tests
    def _test_gdpr_compliance(self) -> bool:
        """Test GDPR compliance"""
        # Check GDPR endpoints
        gdpr_endpoints = [
            "/api/gdpr/consent",
            "/api/gdpr/data-export",
            "/api/gdpr/data-deletion"
        ]
        
        for endpoint in gdpr_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                return False
        
        return True
    
    def _test_data_privacy_controls(self) -> bool:
        """Test data privacy controls"""
        # Check privacy control endpoints
        privacy_endpoints = [
            "/api/privacy/controls",
            "/api/privacy/preferences"
        ]
        
        for endpoint in privacy_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                return False
        
        return True
    
    def _test_audit_trail(self) -> bool:
        """Test audit trail"""
        # Check audit trail endpoints
        audit_endpoints = [
            "/api/audit/trail",
            "/api/audit/events"
        ]
        
        for endpoint in audit_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                return False
        
        return True
    
    # Integration Tests
    def _test_security_integration(self) -> bool:
        """Test security integration"""
        # Check if all security components are integrated
        integration_endpoints = [
            "/api/security/status",
            "/api/monitoring/health",
            "/api/backup/status"
        ]
        
        for endpoint in integration_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code != 200:
                return False
        
        return True
    
    def _test_end_to_end_security(self) -> bool:
        """Test end-to-end security"""
        # Perform a complete security flow
        # 1. Login
        login_response = self.session.post(
            f"{self.base_url}{self.config['test_endpoints']['login']}",
            json={
                "username": self.config["test_credentials"]["admin_user"],
                "password": self.config["test_credentials"]["admin_password"]
            }
        )
        
        if login_response.status_code != 200:
            return False
        
        # 2. Access protected resource
        protected_response = self.session.get(f"{self.base_url}{self.config['test_endpoints']['protected']}")
        
        if protected_response.status_code != 200:
            return False
        
        # 3. Check security headers
        if not self._test_security_headers():
            return False
        
        return True
    
    # Helper Methods
    def _is_password_strong(self, password: str) -> bool:
        """Check if password meets strength requirements"""
        if len(password) < 12:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _is_encrypted_content(self, content: bytes) -> bool:
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
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.test_results if r.status == TestStatus.ERROR])
        skipped_tests = len([r for r in self.test_results if r.status == TestStatus.SKIPPED])
        
        # Group by category
        category_results = {}
        for result in self.test_results:
            test = self.test_registry.get(result.test_id)
            if test:
                category = test.category.value
                if category not in category_results:
                    category_results[category] = []
                category_results[category].append(result)
        
        # Group by severity
        severity_results = {}
        for result in self.test_results:
            test = self.test_registry.get(result.test_id)
            if test:
                severity = test.severity.value
                if severity not in severity_results:
                    severity_results[severity] = []
                severity_results[severity].append(result)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "skipped_tests": skipped_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "category_results": category_results,
            "severity_results": severity_results,
            "detailed_results": [
                {
                    "test_id": result.test_id,
                    "name": self.test_registry.get(result.test_id, {}).get("name", "Unknown"),
                    "category": self.test_registry.get(result.test_id, {}).get("category", {}).get("value", "Unknown"),
                    "severity": self.test_registry.get(result.test_id, {}).get("severity", {}).get("value", "Unknown"),
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                    "details": result.details
                }
                for result in self.test_results
            ]
        }

# Global test suite instance
_security_test_suite = None

def get_security_test_suite(base_url: str = "http://localhost:5000") -> SecurityTestSuite:
    """Get global security test suite instance"""
    global _security_test_suite
    
    if _security_test_suite is None:
        _security_test_suite = SecurityTestSuite(base_url)
    
    return _security_test_suite

def run_security_tests(base_url: str = "http://localhost:5000", categories: List[str] = None) -> Dict[str, Any]:
    """Run comprehensive security tests"""
    test_suite = get_security_test_suite(base_url)
    results = test_suite.run_all_tests(categories)
    return test_suite.generate_test_report()

if __name__ == "__main__":
    # Run security tests
    report = run_security_tests()
    print(json.dumps(report, indent=2)) 