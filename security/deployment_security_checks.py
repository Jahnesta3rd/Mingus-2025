"""
Deployment Security Checks
Comprehensive security validation for deployment processes
"""

import os
import sys
import json
import ssl
import socket
import requests
import subprocess
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import threading
from urllib.parse import urlparse
import OpenSSL
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from loguru import logger

class SecurityCheckType(Enum):
    """Types of security checks"""
    PRE_DEPLOYMENT = "pre_deployment"
    SSL_CERTIFICATE = "ssl_certificate"
    SECURITY_HEADERS = "security_headers"
    DATABASE_SECURITY = "database_security"
    API_ENDPOINT = "api_endpoint"

class SecurityCheckStatus(Enum):
    """Security check status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class SecurityCheckResult:
    """Security check result"""
    check_type: SecurityCheckType
    check_name: str
    status: SecurityCheckStatus
    details: str
    timestamp: datetime
    duration_ms: int
    recommendations: List[str] = field(default_factory=list)
    severity: str = "medium"

@dataclass
class DeploymentSecurityReport:
    """Deployment security report"""
    deployment_id: str
    environment: str
    timestamp: datetime
    overall_status: SecurityCheckStatus
    checks: List[SecurityCheckResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

class DeploymentSecurityChecker:
    """Deployment security checker"""
    
    def __init__(self, environment: str, base_path: str = "/var/lib/mingus/security"):
        self.environment = environment
        self.base_path = base_path
        self.results = []
        self.start_time = datetime.utcnow()
        
        # Load configuration
        self.config = self._load_security_config()
        
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        config_path = os.path.join(self.base_path, f"deployment_security_config_{self.environment}.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default security configuration"""
        return {
            "ssl_checks": {
                "enabled": True,
                "min_tls_version": "1.2",
                "required_cipher_suites": ["ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-RSA-AES128-GCM-SHA256"],
                "certificate_expiry_warning_days": 30,
                "certificate_expiry_critical_days": 7
            },
            "security_headers": {
                "enabled": True,
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
                "enabled": True,
                "ssl_required": True,
                "connection_timeout": 10,
                "max_connections": 100
            },
            "api_checks": {
                "enabled": True,
                "endpoints": [
                    "/api/health",
                    "/api/auth/login",
                    "/api/users",
                    "/api/admin"
                ],
                "auth_required": True,
                "rate_limiting": True
            }
        }
    
    def run_all_checks(self) -> DeploymentSecurityReport:
        """Run all security checks"""
        logger.info(f"Starting deployment security checks for {self.environment}")
        
        # Pre-deployment checks
        self._run_pre_deployment_checks()
        
        # SSL certificate checks
        if self.config["ssl_checks"]["enabled"]:
            self._run_ssl_certificate_checks()
        
        # Security header checks
        if self.config["security_headers"]["enabled"]:
            self._run_security_header_checks()
        
        # Database security checks
        if self.config["database_checks"]["enabled"]:
            self._run_database_security_checks()
        
        # API endpoint checks
        if self.config["api_checks"]["enabled"]:
            self._run_api_endpoint_checks()
        
        # Generate report
        return self._generate_report()
    
    def _run_pre_deployment_checks(self):
        """Run pre-deployment security checks"""
        logger.info("Running pre-deployment security checks")
        
        checks = [
            ("Environment Variables", self._check_environment_variables),
            ("File Permissions", self._check_file_permissions),
            ("Dependencies", self._check_dependencies),
            ("Configuration Files", self._check_configuration_files),
            ("Security Policies", self._check_security_policies),
            ("Network Configuration", self._check_network_configuration)
        ]
        
        for check_name, check_func in checks:
            self._run_check(SecurityCheckType.PRE_DEPLOYMENT, check_name, check_func)
    
    def _check_environment_variables(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check environment variables"""
        required_vars = [
            "MINGUS_ENV",
            "SECRET_KEY",
            "DATABASE_URL"
        ]
        
        if self.environment == "production":
            required_vars.extend([
                "PROD_DB_PASSWORD",
                "PROD_JWT_SECRET",
                "PROD_SSL_CERT_PATH"
            ])
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            return SecurityCheckStatus.FAILED, f"Missing environment variables: {', '.join(missing_vars)}", [
                "Set all required environment variables",
                "Use secure secret management for sensitive variables"
            ]
        
        return SecurityCheckStatus.PASSED, "All required environment variables are set", []
    
    def _check_file_permissions(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check file permissions"""
        critical_files = [
            "/var/lib/mingus/security/encryption.key",
            "/var/lib/mingus/security/secret_encryption.key"
        ]
        
        insecure_files = []
        for file_path in critical_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                if stat.st_mode & 0o777 != 0o600:
                    insecure_files.append(file_path)
        
        if insecure_files:
            return SecurityCheckStatus.FAILED, f"Insecure file permissions: {', '.join(insecure_files)}", [
                "Set file permissions to 600 for sensitive files",
                "Ensure only root can access encryption keys"
            ]
        
        return SecurityCheckStatus.PASSED, "All critical files have secure permissions", []
    
    def _check_dependencies(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check dependencies for security vulnerabilities"""
        try:
            # Check for known vulnerable packages
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return SecurityCheckStatus.WARNING, "Could not check dependencies", [
                    "Manually verify package versions",
                    "Run security audit on dependencies"
                ]
            
            packages = json.loads(result.stdout)
            vulnerable_packages = []
            
            # Check for known vulnerable versions (simplified check)
            vulnerable_versions = {
                "requests": ["2.25.0", "2.25.1"],
                "urllib3": ["1.26.0", "1.26.1"]
            }
            
            for package in packages:
                name = package["name"]
                version = package["version"]
                
                if name in vulnerable_versions and version in vulnerable_versions[name]:
                    vulnerable_packages.append(f"{name}=={version}")
            
            if vulnerable_packages:
                return SecurityCheckStatus.FAILED, f"Vulnerable packages found: {', '.join(vulnerable_packages)}", [
                    "Update vulnerable packages to latest versions",
                    "Run security audit on all dependencies"
                ]
            
            return SecurityCheckStatus.PASSED, "No known vulnerable packages found", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check dependencies: {e}", [
                "Manually verify package versions",
                "Run security audit on dependencies"
            ]
    
    def _check_configuration_files(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check configuration files"""
        config_files = [
            os.path.join(self.base_path, "environment_security.py"),
            os.path.join(self.base_path, "deploy_environment_security.py")
        ]
        
        missing_files = []
        for file_path in config_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            return SecurityCheckStatus.FAILED, f"Missing configuration files: {', '.join(missing_files)}", [
                "Ensure all security configuration files are present",
                "Verify file paths and permissions"
            ]
        
        return SecurityCheckStatus.PASSED, "All configuration files are present", []
    
    def _check_security_policies(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check security policies"""
        try:
            # Import and check security policies
            sys.path.append(self.base_path)
            from environment_security import get_environment_security_manager, Environment
            
            env_map = {"development": Environment.DEVELOPMENT, 
                      "staging": Environment.STAGING, 
                      "production": Environment.PRODUCTION}
            
            manager = get_environment_security_manager()
            env_config = manager.get_environment_config(env_map.get(self.environment))
            
            if not env_config:
                return SecurityCheckStatus.FAILED, "No security configuration found for environment", [
                    "Configure environment-specific security settings",
                    "Run environment security deployment"
                ]
            
            # Validate configuration
            errors = manager.validate_environment_config(env_map.get(self.environment))
            
            if errors:
                return SecurityCheckStatus.FAILED, f"Security policy validation failed: {', '.join(errors)}", [
                    "Fix security policy validation errors",
                    "Review environment security configuration"
                ]
            
            return SecurityCheckStatus.PASSED, "Security policies are properly configured", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check security policies: {e}", [
                "Verify security configuration",
                "Check environment security setup"
            ]
    
    def _check_network_configuration(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check network configuration"""
        try:
            # Check firewall status
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return SecurityCheckStatus.WARNING, "Could not check firewall status", [
                    "Verify firewall is enabled and configured",
                    "Check firewall rules for required ports"
                ]
            
            if "Status: active" not in result.stdout:
                return SecurityCheckStatus.FAILED, "Firewall is not active", [
                    "Enable and configure firewall",
                    "Set up proper firewall rules"
                ]
            
            return SecurityCheckStatus.PASSED, "Network security is properly configured", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check network configuration: {e}", [
                "Verify network security settings",
                "Check firewall and network configuration"
            ]
    
    def _run_ssl_certificate_checks(self):
        """Run SSL certificate checks"""
        logger.info("Running SSL certificate checks")
        
        domain = os.getenv("MINGUS_DOMAIN", "localhost")
        port = 443
        
        checks = [
            ("Certificate Validity", lambda: self._check_certificate_validity(domain, port)),
            ("TLS Version", lambda: self._check_tls_version(domain, port)),
            ("Cipher Suites", lambda: self._check_cipher_suites(domain, port)),
            ("Certificate Chain", lambda: self._check_certificate_chain(domain, port)),
            ("Certificate Expiry", lambda: self._check_certificate_expiry(domain, port))
        ]
        
        for check_name, check_func in checks:
            self._run_check(SecurityCheckType.SSL_CERTIFICATE, check_name, check_func)
    
    def _check_certificate_validity(self, domain: str, port: int) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check certificate validity"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if not cert:
                        return SecurityCheckStatus.FAILED, "No certificate found", [
                            "Install valid SSL certificate",
                            "Verify certificate configuration"
                        ]
                    
                    return SecurityCheckStatus.PASSED, "Certificate is valid", []
                    
        except Exception as e:
            return SecurityCheckStatus.FAILED, f"Certificate validation failed: {e}", [
                "Verify SSL certificate is installed",
                "Check certificate configuration"
            ]
    
    def _check_tls_version(self, domain: str, port: int) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check TLS version"""
        try:
            min_tls_version = self.config["ssl_checks"]["min_tls_version"]
            
            # Test different TLS versions
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
            
            if not supported_versions:
                return SecurityCheckStatus.FAILED, "No supported TLS versions found", [
                    "Enable TLS support on server",
                    "Configure minimum TLS version"
                ]
            
            if min_tls_version not in supported_versions:
                return SecurityCheckStatus.FAILED, f"Required TLS version {min_tls_version} not supported", [
                    f"Enable TLS {min_tls_version} support",
                    "Update server configuration"
                ]
            
            return SecurityCheckStatus.PASSED, f"TLS {min_tls_version} is supported", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check TLS version: {e}", [
                "Verify TLS configuration",
                "Check server SSL settings"
            ]
    
    def _check_cipher_suites(self, domain: str, port: int) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check cipher suites"""
        try:
            required_ciphers = self.config["ssl_checks"]["required_cipher_suites"]
            
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cipher = ssock.cipher()
                    
                    if not cipher:
                        return SecurityCheckStatus.FAILED, "No cipher suite information available", [
                            "Verify SSL configuration",
                            "Check cipher suite support"
                        ]
                    
                    cipher_name = cipher[0]
                    
                    if cipher_name not in required_ciphers:
                        return SecurityCheckStatus.WARNING, f"Current cipher {cipher_name} not in recommended list", [
                            "Configure recommended cipher suites",
                            "Update SSL configuration"
                        ]
                    
                    return SecurityCheckStatus.PASSED, f"Using secure cipher: {cipher_name}", []
                    
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check cipher suites: {e}", [
                "Verify SSL configuration",
                "Check cipher suite support"
            ]
    
    def _check_certificate_chain(self, domain: str, port: int) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check certificate chain"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if not cert:
                        return SecurityCheckStatus.FAILED, "No certificate found", [
                            "Install valid SSL certificate",
                            "Verify certificate configuration"
                        ]
                    
                    # Check if certificate is self-signed
                    issuer = dict(x[0] for x in cert['issuer'])
                    subject = dict(x[0] for x in cert['subject'])
                    
                    if issuer == subject:
                        return SecurityCheckStatus.WARNING, "Certificate appears to be self-signed", [
                            "Use certificate from trusted CA",
                            "Consider Let's Encrypt for free certificates"
                        ]
                    
                    return SecurityCheckStatus.PASSED, "Certificate chain is valid", []
                    
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check certificate chain: {e}", [
                "Verify certificate configuration",
                "Check certificate chain"
            ]
    
    def _check_certificate_expiry(self, domain: str, port: int) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check certificate expiry"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if not cert:
                        return SecurityCheckStatus.FAILED, "No certificate found", [
                            "Install valid SSL certificate",
                            "Verify certificate configuration"
                        ]
                    
                    # Parse expiry date
                    not_after = cert['notAfter']
                    expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.utcnow()).days
                    
                    warning_days = self.config["ssl_checks"]["certificate_expiry_warning_days"]
                    critical_days = self.config["ssl_checks"]["certificate_expiry_critical_days"]
                    
                    if days_until_expiry < 0:
                        return SecurityCheckStatus.FAILED, "Certificate has expired", [
                            "Renew SSL certificate immediately",
                            "Install new certificate"
                        ]
                    elif days_until_expiry < critical_days:
                        return SecurityCheckStatus.FAILED, f"Certificate expires in {days_until_expiry} days", [
                            "Renew SSL certificate immediately",
                            "Set up automatic renewal"
                        ]
                    elif days_until_expiry < warning_days:
                        return SecurityCheckStatus.WARNING, f"Certificate expires in {days_until_expiry} days", [
                            "Plan certificate renewal",
                            "Set up automatic renewal"
                        ]
                    
                    return SecurityCheckStatus.PASSED, f"Certificate expires in {days_until_expiry} days", []
                    
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check certificate expiry: {e}", [
                "Verify certificate configuration",
                "Check certificate expiry manually"
            ]
    
    def _run_security_header_checks(self):
        """Run security header checks"""
        logger.info("Running security header checks")
        
        base_url = f"https://{os.getenv('MINGUS_DOMAIN', 'localhost')}"
        
        checks = [
            ("Required Security Headers", lambda: self._check_required_headers(base_url)),
            ("Optional Security Headers", lambda: self._check_optional_headers(base_url)),
            ("Header Values", lambda: self._check_header_values(base_url))
        ]
        
        for check_name, check_func in checks:
            self._run_check(SecurityCheckType.SECURITY_HEADERS, check_name, check_func)
    
    def _check_required_headers(self, base_url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check required security headers"""
        try:
            response = requests.get(base_url, timeout=10, verify=True)
            headers = response.headers
            
            required_headers = self.config["security_headers"]["required_headers"]
            missing_headers = []
            
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                return SecurityCheckStatus.FAILED, f"Missing required headers: {', '.join(missing_headers)}", [
                    "Configure required security headers",
                    "Update web server configuration"
                ]
            
            return SecurityCheckStatus.PASSED, "All required security headers are present", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check security headers: {e}", [
                "Verify web server configuration",
                "Check security header setup"
            ]
    
    def _check_optional_headers(self, base_url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check optional security headers"""
        try:
            response = requests.get(base_url, timeout=10, verify=True)
            headers = response.headers
            
            optional_headers = self.config["security_headers"]["optional_headers"]
            present_headers = []
            
            for header in optional_headers:
                if header in headers:
                    present_headers.append(header)
            
            if not present_headers:
                return SecurityCheckStatus.WARNING, "No optional security headers found", [
                    "Consider adding optional security headers",
                    "Enhance security with additional headers"
                ]
            
            return SecurityCheckStatus.PASSED, f"Optional headers present: {', '.join(present_headers)}", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check optional headers: {e}", [
                "Verify web server configuration",
                "Check security header setup"
            ]
    
    def _check_header_values(self, base_url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check security header values"""
        try:
            response = requests.get(base_url, timeout=10, verify=True)
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
            
            # Check X-Content-Type-Options
            if "X-Content-Type-Options" in headers:
                xcto_value = headers["X-Content-Type-Options"]
                if xcto_value != "nosniff":
                    issues.append("X-Content-Type-Options should be nosniff")
            
            if issues:
                return SecurityCheckStatus.WARNING, f"Header value issues: {', '.join(issues)}", [
                    "Review security header values",
                    "Update header configurations"
                ]
            
            return SecurityCheckStatus.PASSED, "Security header values are properly configured", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check header values: {e}", [
                "Verify web server configuration",
                "Check security header setup"
            ]
    
    def _run_database_security_checks(self):
        """Run database security checks"""
        logger.info("Running database security checks")
        
        checks = [
            ("Database Connection", self._check_database_connection),
            ("SSL Connection", self._check_database_ssl),
            ("Connection Limits", self._check_database_limits),
            ("User Permissions", self._check_database_permissions)
        ]
        
        for check_name, check_func in checks:
            self._run_check(SecurityCheckType.DATABASE_SECURITY, check_name, check_func)
    
    def _check_database_connection(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check database connection"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return SecurityCheckStatus.FAILED, "DATABASE_URL not set", [
                    "Set DATABASE_URL environment variable",
                    "Configure database connection"
                ]
            
            # Test connection
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=5)
            conn.close()
            
            return SecurityCheckStatus.PASSED, "Database connection successful", []
            
        except Exception as e:
            return SecurityCheckStatus.FAILED, f"Database connection failed: {e}", [
                "Verify database is running",
                "Check database connection settings"
            ]
    
    def _check_database_ssl(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check database SSL connection"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return SecurityCheckStatus.SKIPPED, "DATABASE_URL not set", []
            
            # Parse connection string
            parsed = urlparse(db_url)
            
            if parsed.scheme != "postgresql":
                return SecurityCheckStatus.SKIPPED, "Not a PostgreSQL connection", []
            
            # Check if SSL is enabled
            if "sslmode=" not in parsed.query:
                if self.config["database_checks"]["ssl_required"]:
                    return SecurityCheckStatus.FAILED, "SSL not enabled for database connection", [
                        "Enable SSL for database connection",
                        "Add sslmode=require to connection string"
                    ]
                else:
                    return SecurityCheckStatus.WARNING, "SSL not enabled for database connection", [
                        "Consider enabling SSL for database connection"
                    ]
            
            return SecurityCheckStatus.PASSED, "Database SSL connection is enabled", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check database SSL: {e}", [
                "Verify database SSL configuration",
                "Check connection string format"
            ]
    
    def _check_database_limits(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check database connection limits"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return SecurityCheckStatus.SKIPPED, "DATABASE_URL not set", []
            
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=5)
            cursor = conn.cursor()
            
            # Check max connections
            cursor.execute("SHOW max_connections")
            max_connections = int(cursor.fetchone()[0])
            
            if max_connections > 200:
                return SecurityCheckStatus.WARNING, f"High max connections: {max_connections}", [
                    "Consider reducing max connections",
                    "Monitor connection usage"
                ]
            
            cursor.close()
            conn.close()
            
            return SecurityCheckStatus.PASSED, f"Database connection limits are reasonable: {max_connections}", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check database limits: {e}", [
                "Verify database configuration",
                "Check connection limits manually"
            ]
    
    def _check_database_permissions(self) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check database user permissions"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return SecurityCheckStatus.SKIPPED, "DATABASE_URL not set", []
            
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=5)
            cursor = conn.cursor()
            
            # Check current user permissions
            cursor.execute("SELECT current_user, session_user")
            current_user, session_user = cursor.fetchone()
            
            # Check if user has superuser privileges
            cursor.execute("SELECT usesuper FROM pg_user WHERE usename = %s", (current_user,))
            is_superuser = cursor.fetchone()[0]
            
            if is_superuser:
                return SecurityCheckStatus.WARNING, f"User {current_user} has superuser privileges", [
                    "Use dedicated application user",
                    "Limit user privileges to minimum required"
                ]
            
            cursor.close()
            conn.close()
            
            return SecurityCheckStatus.PASSED, f"Database user {current_user} has appropriate permissions", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check database permissions: {e}", [
                "Verify database user permissions",
                "Check user privileges manually"
            ]
    
    def _run_api_endpoint_checks(self):
        """Run API endpoint security checks"""
        logger.info("Running API endpoint security checks")
        
        base_url = f"https://{os.getenv('MINGUS_DOMAIN', 'localhost')}"
        endpoints = self.config["api_checks"]["endpoints"]
        
        for endpoint in endpoints:
            checks = [
                (f"Authentication - {endpoint}", lambda: self._check_endpoint_auth(base_url + endpoint)),
                (f"Rate Limiting - {endpoint}", lambda: self._check_endpoint_rate_limiting(base_url + endpoint)),
                (f"Input Validation - {endpoint}", lambda: self._check_endpoint_input_validation(base_url + endpoint))
            ]
            
            for check_name, check_func in checks:
                self._run_check(SecurityCheckType.API_ENDPOINT, check_name, check_func)
    
    def _check_endpoint_auth(self, url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check endpoint authentication"""
        try:
            response = requests.get(url, timeout=10, verify=True)
            
            if response.status_code == 401:
                return SecurityCheckStatus.PASSED, "Endpoint requires authentication", []
            elif response.status_code == 403:
                return SecurityCheckStatus.PASSED, "Endpoint requires authorization", []
            elif response.status_code == 200:
                if self.config["api_checks"]["auth_required"]:
                    return SecurityCheckStatus.FAILED, "Endpoint should require authentication", [
                        "Add authentication to endpoint",
                        "Implement proper access control"
                    ]
                else:
                    return SecurityCheckStatus.PASSED, "Endpoint authentication is appropriate", []
            else:
                return SecurityCheckStatus.WARNING, f"Unexpected response code: {response.status_code}", [
                    "Verify endpoint behavior",
                    "Check authentication configuration"
                ]
                
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check endpoint authentication: {e}", [
                "Verify endpoint is accessible",
                "Check authentication configuration"
            ]
    
    def _check_endpoint_rate_limiting(self, url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check endpoint rate limiting"""
        try:
            # Make multiple requests quickly
            responses = []
            for i in range(10):
                response = requests.get(url, timeout=5, verify=True)
                responses.append(response.status_code)
                time.sleep(0.1)
            
            # Check if any requests were rate limited
            rate_limited = any(code == 429 for code in responses)
            
            if rate_limited:
                return SecurityCheckStatus.PASSED, "Endpoint has rate limiting enabled", []
            else:
                if self.config["api_checks"]["rate_limiting"]:
                    return SecurityCheckStatus.WARNING, "Endpoint should have rate limiting", [
                        "Implement rate limiting for endpoint",
                        "Configure appropriate rate limits"
                    ]
                else:
                    return SecurityCheckStatus.PASSED, "Rate limiting is not required for this endpoint", []
                    
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check rate limiting: {e}", [
                "Verify endpoint is accessible",
                "Check rate limiting configuration"
            ]
    
    def _check_endpoint_input_validation(self, url: str) -> Tuple[SecurityCheckStatus, str, List[str]]:
        """Check endpoint input validation"""
        try:
            # Test with potentially malicious input
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
                    
                    # Check for potential vulnerabilities
                    if "error" in response.text.lower() and "sql" in response.text.lower():
                        vulnerabilities.append("Potential SQL injection")
                    
                    if "<script>" in response.text:
                        vulnerabilities.append("Potential XSS vulnerability")
                    
                except:
                    pass
            
            if vulnerabilities:
                return SecurityCheckStatus.FAILED, f"Input validation issues found: {', '.join(vulnerabilities)}", [
                    "Implement proper input validation",
                    "Add security headers and filters"
                ]
            
            return SecurityCheckStatus.PASSED, "Input validation appears to be working", []
            
        except Exception as e:
            return SecurityCheckStatus.WARNING, f"Could not check input validation: {e}", [
                "Verify endpoint is accessible",
                "Check input validation manually"
            ]
    
    def _run_check(self, check_type: SecurityCheckType, check_name: str, check_func):
        """Run a single security check"""
        start_time = time.time()
        
        try:
            status, details, recommendations = check_func()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = SecurityCheckResult(
                check_type=check_type,
                check_name=check_name,
                status=status,
                details=details,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                recommendations=recommendations
            )
            
            self.results.append(result)
            
            # Log result
            if status == SecurityCheckStatus.PASSED:
                logger.info(f"✅ {check_name}: {details}")
            elif status == SecurityCheckStatus.WARNING:
                logger.warning(f"⚠️ {check_name}: {details}")
            elif status == SecurityCheckStatus.FAILED:
                logger.error(f"❌ {check_name}: {details}")
            else:
                logger.info(f"⏭️ {check_name}: {details}")
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = SecurityCheckResult(
                check_type=check_type,
                check_name=check_name,
                status=SecurityCheckStatus.FAILED,
                details=f"Check failed with error: {e}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                recommendations=["Review check implementation", "Check system configuration"]
            )
            
            self.results.append(result)
            logger.error(f"❌ {check_name}: Check failed with error: {e}")
    
    def _generate_report(self) -> DeploymentSecurityReport:
        """Generate deployment security report"""
        # Calculate overall status
        failed_checks = [r for r in self.results if r.status == SecurityCheckStatus.FAILED]
        warning_checks = [r for r in self.results if r.status == SecurityCheckStatus.WARNING]
        passed_checks = [r for r in self.results if r.status == SecurityCheckStatus.PASSED]
        
        if failed_checks:
            overall_status = SecurityCheckStatus.FAILED
        elif warning_checks:
            overall_status = SecurityCheckStatus.WARNING
        else:
            overall_status = SecurityCheckStatus.PASSED
        
        # Generate summary
        summary = {
            "total_checks": len(self.results),
            "passed_checks": len(passed_checks),
            "failed_checks": len(failed_checks),
            "warning_checks": len(warning_checks),
            "skipped_checks": len([r for r in self.results if r.status == SecurityCheckStatus.SKIPPED]),
            "total_duration_ms": sum(r.duration_ms for r in self.results),
            "check_types": {
                check_type.value: len([r for r in self.results if r.check_type == check_type])
                for check_type in SecurityCheckType
            }
        }
        
        report = DeploymentSecurityReport(
            deployment_id=f"deployment_{int(time.time())}",
            environment=self.environment,
            timestamp=self.start_time,
            overall_status=overall_status,
            checks=self.results,
            summary=summary
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: DeploymentSecurityReport):
        """Save security report"""
        try:
            report_path = os.path.join(
                self.base_path, 
                f"security_report_{self.environment}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_path, 'w') as f:
                json.dump({
                    "deployment_id": report.deployment_id,
                    "environment": report.environment,
                    "timestamp": report.timestamp.isoformat(),
                    "overall_status": report.overall_status.value,
                    "summary": report.summary,
                    "checks": [
                        {
                            "check_type": check.check_type.value,
                            "check_name": check.check_name,
                            "status": check.status.value,
                            "details": check.details,
                            "timestamp": check.timestamp.isoformat(),
                            "duration_ms": check.duration_ms,
                            "recommendations": check.recommendations,
                            "severity": check.severity
                        }
                        for check in report.checks
                    ]
                }, f, indent=2)
            
            logger.info(f"Security report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to save security report: {e}")

def run_deployment_security_checks(environment: str, base_path: str = "/var/lib/mingus/security") -> DeploymentSecurityReport:
    """Run deployment security checks"""
    checker = DeploymentSecurityChecker(environment, base_path)
    return checker.run_all_checks()

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run deployment security checks")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        required=True,
        help="Environment to check"
    )
    parser.add_argument(
        "--base-path",
        default="/var/lib/mingus/security",
        help="Base path for security configuration"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_deployment_security_checks(args.environment, args.base_path)
        
        # Print summary
        print(f"\n🔒 Deployment Security Report for {args.environment}")
        print(f"📅 Generated: {report.timestamp}")
        print(f"📊 Overall Status: {report.overall_status.value.upper()}")
        print(f"📈 Summary:")
        print(f"   Total Checks: {report.summary['total_checks']}")
        print(f"   Passed: {report.summary['passed_checks']}")
        print(f"   Failed: {report.summary['failed_checks']}")
        print(f"   Warnings: {report.summary['warning_checks']}")
        print(f"   Duration: {report.summary['total_duration_ms']}ms")
        
        # Print failed checks
        failed_checks = [c for c in report.checks if c.status == SecurityCheckStatus.FAILED]
        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check in failed_checks:
                print(f"   • {check.check_name}: {check.details}")
                for rec in check.recommendations:
                    print(f"     - {rec}")
        
        # Print warnings
        warning_checks = [c for c in report.checks if c.status == SecurityCheckStatus.WARNING]
        if warning_checks:
            print(f"\n⚠️ Warnings:")
            for check in warning_checks:
                print(f"   • {check.check_name}: {check.details}")
        
        if report.overall_status == SecurityCheckStatus.FAILED:
            sys.exit(1)
        elif report.overall_status == SecurityCheckStatus.WARNING:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Security checks failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 