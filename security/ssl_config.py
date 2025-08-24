#!/usr/bin/env python3
"""
MINGUS SSL/TLS Security Configuration
Comprehensive HTTPS and SSL security system for financial wellness application
Ensures all data transmission is secure with banking-grade encryption
"""

import os
import ssl
import socket
import hashlib
import logging
import requests
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json

from flask import Flask, request, Response, g, current_app, redirect, url_for
from werkzeug.exceptions import BadRequest, Forbidden

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SSLConfig:
    """SSL/TLS configuration for different environments"""
    environment: str
    
    # SSL/TLS Configuration
    ssl_enabled: bool = True
    force_https: bool = True
    tls_min_version: str = "TLSv1.2"
    tls_max_version: str = "TLSv1.3"
    
    # Cipher Suites
    cipher_suites: List[str] = field(default_factory=lambda: [
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-CHACHA20-POLY1305",
        "ECDHE-RSA-CHACHA20-POLY1305",
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-SHA384",
        "ECDHE-RSA-AES256-SHA384",
        "ECDHE-ECDSA-AES128-SHA256",
        "ECDHE-RSA-AES128-SHA256"
    ])
    
    # Certificate Configuration
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    cert_chain_file: Optional[str] = None
    cert_pinning_enabled: bool = False
    cert_pinning_hashes: List[str] = field(default_factory=list)
    
    # HSTS Configuration
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # Session Security
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "Strict"
    session_cookie_max_age: int = 3600  # 1 hour
    
    # Mixed Content Prevention
    block_mixed_content: bool = True
    upgrade_insecure_requests: bool = True
    
    # Certificate Transparency
    expect_ct_enabled: bool = True
    expect_ct_max_age: int = 86400  # 24 hours
    expect_ct_enforce: bool = True
    expect_ct_report_uri: Optional[str] = None
    
    # Health Checks
    ssl_health_check_enabled: bool = True
    ssl_health_check_interval: int = 300  # 5 minutes
    
    # Digital Ocean Specific
    digital_ocean_enabled: bool = False
    do_load_balancer_ssl: bool = True
    do_certificate_auto_renewal: bool = True

class SSLSecurityMiddleware:
    """Comprehensive SSL/TLS security middleware for MINGUS application"""
    
    def __init__(self, app: Flask, config: Optional[SSLConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        self.ssl_health_status = {}
        self.certificate_info = {}
        
        # Register middleware
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Register error handlers
        self.app.register_error_handler(400, self._handle_bad_request)
        self.app.register_error_handler(403, self._handle_forbidden)
        self.app.register_error_handler(404, self._handle_not_found)
        self.app.register_error_handler(500, self._handle_server_error)
        
        # Initialize SSL health monitoring
        if self.config.ssl_health_check_enabled:
            self._init_ssl_health_monitoring()
        
        logger.info(f"SSL security middleware initialized for {self.config.environment} environment")
    
    def _get_default_config(self) -> SSLConfig:
        """Get default SSL configuration based on environment"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return SSLConfig(
                environment='production',
                ssl_enabled=True,
                force_https=True,
                tls_min_version="TLSv1.2",
                tls_max_version="TLSv1.3",
                cert_pinning_enabled=True,
                cert_pinning_hashes=[
                    # Add your certificate pinning hashes here
                    # Example: "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
                ],
                hsts_enabled=True,
                hsts_max_age=31536000,
                hsts_include_subdomains=True,
                hsts_preload=True,
                session_cookie_secure=True,
                session_cookie_httponly=True,
                session_cookie_samesite="Strict",
                session_cookie_max_age=1800,  # 30 minutes for financial app
                block_mixed_content=True,
                upgrade_insecure_requests=True,
                expect_ct_enabled=True,
                expect_ct_max_age=86400,
                expect_ct_enforce=True,
                expect_ct_report_uri=os.getenv('EXPECT_CT_REPORT_URI'),
                ssl_health_check_enabled=True,
                digital_ocean_enabled=True,
                do_load_balancer_ssl=True,
                do_certificate_auto_renewal=True
            )
        else:
            # Development configuration
            return SSLConfig(
                environment='development',
                ssl_enabled=False,
                force_https=False,
                tls_min_version="TLSv1.2",
                tls_max_version="TLSv1.3",
                cert_pinning_enabled=False,
                hsts_enabled=False,
                session_cookie_secure=False,
                session_cookie_httponly=True,
                session_cookie_samesite="Lax",
                session_cookie_max_age=7200,  # 2 hours for development
                block_mixed_content=False,
                upgrade_insecure_requests=False,
                expect_ct_enabled=False,
                ssl_health_check_enabled=False,
                digital_ocean_enabled=False
            )
    
    def _before_request(self):
        """Before request processing - enforce HTTPS and security checks"""
        # Force HTTPS redirect in production
        if self.config.force_https and not request.is_secure:
            if self.config.environment == 'production':
                # Redirect to HTTPS
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
            else:
                # Log warning in development
                logger.warning(f"Insecure request in {self.config.environment}: {request.url}")
        
        # Check certificate pinning in production
        if self.config.cert_pinning_enabled and request.is_secure:
            if not self._verify_certificate_pinning():
                logger.error("Certificate pinning verification failed")
                return self._create_error_response(403, "Certificate verification failed")
        
        # Log security-relevant request information
        self._log_security_event('request_start', {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'method': request.method,
            'path': request.path,
            'is_secure': request.is_secure,
            'protocol': request.environ.get('wsgi.url_scheme', 'http')
        })
    
    def _after_request(self, response: Response) -> Response:
        """After request processing - add SSL security headers"""
        try:
            # Add SSL security headers
            self._add_ssl_security_headers(response)
            
            # Log response security information
            self._log_security_event('response_complete', {
                'status_code': response.status_code,
                'content_length': len(response.get_data()),
                'content_type': response.headers.get('Content-Type'),
                'is_secure': request.is_secure
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding SSL security headers: {e}")
            return response
    
    def _add_ssl_security_headers(self, response: Response):
        """Add comprehensive SSL security headers to response"""
        config = self.config
        
        # HTTP Strict Transport Security (HSTS)
        if config.hsts_enabled and request.is_secure:
            hsts_parts = [f"max-age={config.hsts_max_age}"]
            if config.hsts_include_subdomains:
                hsts_parts.append("includeSubDomains")
            if config.hsts_preload:
                hsts_parts.append("preload")
            response.headers['Strict-Transport-Security'] = "; ".join(hsts_parts)
        
        # Expect-CT (Certificate Transparency)
        if config.expect_ct_enabled and request.is_secure:
            ct_parts = [f"max-age={config.expect_ct_max_age}"]
            if config.expect_ct_enforce:
                ct_parts.append("enforce")
            if config.expect_ct_report_uri:
                ct_parts.append(f'report-uri="{config.expect_ct_report_uri}"')
            response.headers['Expect-CT'] = ", ".join(ct_parts)
        
        # Upgrade Insecure Requests
        if config.upgrade_insecure_requests:
            response.headers['Upgrade-Insecure-Requests'] = '1'
        
        # Additional SSL security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        # Add SSL security indicators
        response.headers['X-SSL-Security'] = 'enabled'
        response.headers['X-TLS-Version'] = config.tls_min_version
    
    def _verify_certificate_pinning(self) -> bool:
        """Verify certificate pinning for production"""
        if not self.config.cert_pinning_hashes:
            return True  # No pins configured
        
        try:
            # Get certificate from request
            cert = request.environ.get('SSL_CLIENT_CERT')
            if not cert:
                # Try to get from connection
                cert = request.environ.get('SSL_CLIENT_CERT_RAW')
            
            if cert:
                # Calculate certificate hash
                cert_hash = hashlib.sha256(cert.encode()).digest()
                cert_hash_b64 = f"sha256/{cert_hash.hex()}"
                
                # Check against pinned hashes
                return cert_hash_b64 in self.config.cert_pinning_hashes
            
            return True  # No certificate to verify
            
        except Exception as e:
            logger.error(f"Certificate pinning verification error: {e}")
            return False
    
    def _init_ssl_health_monitoring(self):
        """Initialize SSL health monitoring"""
        import threading
        import time
        
        def health_monitor():
            while True:
                try:
                    self._check_ssl_health()
                    time.sleep(self.config.ssl_health_check_interval)
                except Exception as e:
                    logger.error(f"SSL health monitoring error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        # Start health monitoring in background thread
        health_thread = threading.Thread(target=health_monitor, daemon=True)
        health_thread.start()
    
    def _check_ssl_health(self):
        """Check SSL/TLS health and certificate status"""
        try:
            domain = request.host if request else 'localhost'
            
            # Check SSL certificate
            cert_info = self._get_certificate_info(domain)
            self.certificate_info[domain] = cert_info
            
            # Check SSL configuration
            ssl_config = self._check_ssl_configuration(domain)
            
            # Update health status
            self.ssl_health_status[domain] = {
                'timestamp': datetime.utcnow().isoformat(),
                'certificate': cert_info,
                'ssl_configuration': ssl_config,
                'healthy': cert_info['valid'] and ssl_config['secure']
            }
            
            # Log health status
            if not self.ssl_health_status[domain]['healthy']:
                logger.warning(f"SSL health check failed for {domain}: {self.ssl_health_status[domain]}")
            
        except Exception as e:
            logger.error(f"SSL health check error: {e}")
    
    def _get_certificate_info(self, domain: str) -> Dict[str, Any]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days until expiration
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    return {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'valid': days_until_expiry > 0,
                        'expires_soon': days_until_expiry <= 30,
                        'serial_number': cert.get('serialNumber'),
                        'version': cert.get('version'),
                        'san': cert.get('subjectAltName', [])
                    }
                    
        except Exception as e:
            logger.error(f"Error getting certificate info for {domain}: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _check_ssl_configuration(self, domain: str) -> Dict[str, Any]:
        """Check SSL/TLS configuration security"""
        try:
            # Test different TLS versions
            tls_versions = {
                'TLSv1.0': ssl.TLSVersion.TLSv1,
                'TLSv1.1': ssl.TLSVersion.TLSv1_1,
                'TLSv1.2': ssl.TLSVersion.TLSv1_2,
                'TLSv1.3': ssl.TLSVersion.TLSv1_3
            }
            
            supported_versions = {}
            for version_name, version_enum in tls_versions.items():
                try:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    context.minimum_version = version_enum
                    context.maximum_version = version_enum
                    
                    with socket.create_connection((domain, 443), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            supported_versions[version_name] = True
                except:
                    supported_versions[version_name] = False
            
            # Check cipher suites
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cipher = ssock.cipher()
                    cipher_suite = cipher[0] if cipher else None
            
            return {
                'supported_tls_versions': supported_versions,
                'current_cipher_suite': cipher_suite,
                'secure': (
                    supported_versions.get('TLSv1.2', False) or 
                    supported_versions.get('TLSv1.3', False)
                ) and cipher_suite in self.config.cipher_suites
            }
            
        except Exception as e:
            logger.error(f"Error checking SSL configuration for {domain}: {e}")
            return {
                'secure': False,
                'error': str(e)
            }
    
    def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log security-related events"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'environment': self.config.environment,
            'data': data
        }
        
        # Hash sensitive data
        if 'ip' in data:
            data['ip_hash'] = hashlib.sha256(data['ip'].encode()).hexdigest()[:16]
            del data['ip']
        
        logger.info(f"SSL security event: {json.dumps(log_data)}")
    
    def _handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        self._log_security_event('bad_request', {
            'error': str(error),
            'path': request.path,
            'method': request.method
        })
        return self._create_error_response(400, "Bad Request")
    
    def _handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        self._log_security_event('forbidden', {
            'error': str(error),
            'path': request.path,
            'method': request.method,
            'ip': request.remote_addr
        })
        return self._create_error_response(403, "Forbidden")
    
    def _handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        self._log_security_event('not_found', {
            'path': request.path,
            'method': request.method
        })
        return self._create_error_response(404, "Not Found")
    
    def _handle_server_error(self, error):
        """Handle 500 Internal Server Error"""
        self._log_security_event('server_error', {
            'error': str(error),
            'path': request.path,
            'method': request.method
        })
        return self._create_error_response(500, "Internal Server Error")
    
    def _create_error_response(self, status_code: int, message: str) -> Response:
        """Create error response with SSL security headers"""
        response = Response(
            json.dumps({'error': message, 'status_code': status_code}),
            status=status_code,
            content_type='application/json'
        )
        self._add_ssl_security_headers(response)
        return response
    
    def get_ssl_health_report(self) -> Dict[str, Any]:
        """Generate SSL health report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.config.environment,
            'ssl_enabled': self.config.ssl_enabled,
            'force_https': self.config.force_https,
            'hsts_enabled': self.config.hsts_enabled,
            'cert_pinning_enabled': self.config.cert_pinning_enabled,
            'health_status': self.ssl_health_status,
            'certificate_info': self.certificate_info,
            'configuration': {
                'tls_min_version': self.config.tls_min_version,
                'tls_max_version': self.config.tls_max_version,
                'session_cookie_secure': self.config.session_cookie_secure,
                'session_cookie_httponly': self.config.session_cookie_httponly,
                'session_cookie_samesite': self.config.session_cookie_samesite
            }
        }

class SSLSecurity:
    """Flask extension for SSL security"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.middleware = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the extension with the Flask app"""
        self.app = app
        self.middleware = SSLSecurityMiddleware(app)
        
        # Configure Flask session security
        app.config['SESSION_COOKIE_SECURE'] = self.middleware.config.session_cookie_secure
        app.config['SESSION_COOKIE_HTTPONLY'] = self.middleware.config.session_cookie_httponly
        app.config['SESSION_COOKIE_SAMESITE'] = self.middleware.config.session_cookie_samesite
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=self.middleware.config.session_cookie_max_age)
        
        # Add SSL health check endpoint
        @app.route('/ssl/health', methods=['GET'])
        def ssl_health_check():
            if not app.debug and not self.middleware.config.ssl_health_check_enabled:
                return Response(status=404)
            
            report = self.middleware.get_ssl_health_report()
            return Response(
                json.dumps(report, indent=2),
                content_type='application/json'
            )
        
        # Add SSL configuration endpoint
        @app.route('/ssl/config', methods=['GET'])
        def ssl_config():
            if not app.debug:
                return Response(status=404)
            
            config_info = {
                'environment': self.middleware.config.environment,
                'ssl_enabled': self.middleware.config.ssl_enabled,
                'force_https': self.middleware.config.force_https,
                'tls_min_version': self.middleware.config.tls_min_version,
                'tls_max_version': self.middleware.config.tls_max_version,
                'hsts_enabled': self.middleware.config.hsts_enabled,
                'cert_pinning_enabled': self.middleware.config.cert_pinning_enabled,
                'session_cookie_secure': self.middleware.config.session_cookie_secure,
                'session_cookie_httponly': self.middleware.config.session_cookie_httponly,
                'session_cookie_samesite': self.middleware.config.session_cookie_samesite
            }
            
            return Response(
                json.dumps(config_info, indent=2),
                content_type='application/json'
            )

def create_ssl_context(config: SSLConfig) -> ssl.SSLContext:
    """Create SSL context with secure configuration"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    
    # Set minimum and maximum TLS versions
    if hasattr(ssl, 'TLSVersion'):
        if config.tls_min_version == "TLSv1.2":
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        elif config.tls_min_version == "TLSv1.3":
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        
        if config.tls_max_version == "TLSv1.3":
            context.maximum_version = ssl.TLSVersion.TLSv1_3
        elif config.tls_max_version == "TLSv1.2":
            context.maximum_version = ssl.TLSVersion.TLSv1_2
    
    # Set cipher suites
    context.set_ciphers(':'.join(config.cipher_suites))
    
    # Set certificate files if provided
    if config.cert_file and config.key_file:
        context.load_cert_chain(config.cert_file, config.key_file)
    
    if config.cert_chain_file:
        context.load_verify_locations(config.cert_chain_file)
    
    # Set verification mode
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    
    return context

def validate_ssl_configuration(config: SSLConfig) -> List[str]:
    """Validate SSL configuration and return list of issues"""
    issues = []
    
    # Validate TLS versions
    if config.tls_min_version not in ["TLSv1.2", "TLSv1.3"]:
        issues.append("Minimum TLS version should be TLSv1.2 or higher")
    
    if config.tls_max_version not in ["TLSv1.2", "TLSv1.3"]:
        issues.append("Maximum TLS version should be TLSv1.2 or TLSv1.3")
    
    if config.tls_min_version > config.tls_max_version:
        issues.append("Minimum TLS version cannot be higher than maximum version")
    
    # Validate certificate files
    if config.cert_file and not os.path.exists(config.cert_file):
        issues.append(f"Certificate file not found: {config.cert_file}")
    
    if config.key_file and not os.path.exists(config.key_file):
        issues.append(f"Private key file not found: {config.key_file}")
    
    # Validate session configuration
    if config.environment == 'production' and not config.session_cookie_secure:
        issues.append("Production sessions must use secure cookies")
    
    if config.session_cookie_samesite not in ["Strict", "Lax", "None"]:
        issues.append("Session cookie SameSite must be Strict, Lax, or None")
    
    return issues 