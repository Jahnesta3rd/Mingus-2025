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
    session_cookie_max_age: int = 3600
    
    # Mixed Content Prevention
    block_mixed_content: bool = True
    upgrade_insecure_requests: bool = True
    
    # Certificate Transparency
    expect_ct_enabled: bool = True
    expect_ct_max_age: int = 86400
    expect_ct_enforce: bool = True
    expect_ct_report_uri: Optional[str] = None
    
    # SSL Health Monitoring
    ssl_health_check_enabled: bool = True
    ssl_health_check_interval: int = 3600  # 1 hour
    
    # Digital Ocean Integration
    digital_ocean_enabled: bool = True
    do_load_balancer_ssl: bool = True
    do_certificate_auto_renewal: bool = True
    
    # Let's Encrypt Configuration
    lets_encrypt_enabled: bool = True
    lets_encrypt_email: Optional[str] = None
    lets_encrypt_staging: bool = False
    
    # SSL Labs Grade Target
    target_ssl_labs_grade: str = "A+"
    
    # Security Headers
    security_headers: Dict[str, str] = field(default_factory=lambda: {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Resource-Policy': 'same-origin'
    })

class SSLSecurityMiddleware:
    """Comprehensive SSL/TLS security middleware for MINGUS application"""
    
    def __init__(self, app: Flask, config: Optional[SSLConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        
        # Register middleware functions
        self._register_middleware()
        
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
                cert_pinning_hashes=[],
                hsts_enabled=False,
                hsts_max_age=31536000,
                hsts_include_subdomains=False,
                hsts_preload=False,
                session_cookie_secure=False,
                session_cookie_httponly=True,
                session_cookie_samesite="Lax",
                session_cookie_max_age=3600,
                block_mixed_content=False,
                upgrade_insecure_requests=False,
                expect_ct_enabled=False,
                expect_ct_max_age=86400,
                expect_ct_enforce=False,
                expect_ct_report_uri=None,
                ssl_health_check_enabled=False,
                digital_ocean_enabled=False,
                do_load_balancer_ssl=False,
                do_certificate_auto_renewal=False
            )
    
    def _register_middleware(self):
        """Register all middleware functions with Flask app"""
        
        # Register before_request handlers
        self.app.before_request(self._enforce_https)
        self.app.before_request(self._validate_ssl_headers)
        self.app.before_request(self._check_certificate_pinning)
        
        # Register after_request handlers
        self.app.after_request(self._add_security_headers)
        self.app.after_request(self._add_hsts_header)
        self.app.after_request(self._add_expect_ct_header)
        
        # Register error handlers
        self.app.errorhandler(400)(self._handle_ssl_error)
        self.app.errorhandler(403)(self._handle_ssl_error)
        self.app.errorhandler(500)(self._handle_ssl_error)
    
    def _enforce_https(self):
        """Enforce HTTPS for all requests in production"""
        if not self.config.force_https:
            return
        
        # Skip health checks and internal routes
        if request.path.startswith('/health') or request.path.startswith('/internal/'):
            return
        
        # Check if request is secure
        is_secure = request.is_secure
        forwarded_proto = request.headers.get('X-Forwarded-Proto')
        
        # Handle proxy scenarios (Digital Ocean, Cloudflare, etc.)
        if forwarded_proto:
            is_secure = forwarded_proto == 'https'
        
        if not is_secure:
            # Redirect to HTTPS
            url = request.url.replace('http://', 'https://', 1)
            logger.warning(f"Redirecting insecure request to HTTPS: {request.url} -> {url}")
            return redirect(url, code=301)
    
    def _validate_ssl_headers(self):
        """Validate SSL-related headers"""
        if not self.config.ssl_enabled:
            return
        
        # Check for secure connection headers
        if request.headers.get('X-Forwarded-Proto') == 'http':
            logger.warning(f"Insecure request detected: {request.url}")
            return BadRequest("Insecure request not allowed")
    
    def _check_certificate_pinning(self):
        """Check certificate pinning if enabled"""
        if not self.config.cert_pinning_enabled:
            return
        
        # Certificate pinning validation would go here
        # This is typically handled at the load balancer level
        pass
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to all responses"""
        
        # Add all configured security headers
        for header, value in self.config.security_headers.items():
            response.headers[header] = value
        
        # Content Security Policy
        csp_policy = self._get_csp_policy()
        if csp_policy:
            response.headers['Content-Security-Policy'] = csp_policy
        
        # Permissions Policy
        permissions_policy = self._get_permissions_policy()
        if permissions_policy:
            response.headers['Permissions-Policy'] = permissions_policy
        
        return response
    
    def _add_hsts_header(self, response: Response) -> Response:
        """Add HTTP Strict Transport Security header"""
        if not self.config.hsts_enabled:
            return response
        
        hsts_value = f"max-age={self.config.hsts_max_age}"
        
        if self.config.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        
        if self.config.hsts_preload:
            hsts_value += "; preload"
        
        response.headers['Strict-Transport-Security'] = hsts_value
        return response
    
    def _add_expect_ct_header(self, response: Response) -> Response:
        """Add Certificate Transparency header"""
        if not self.config.expect_ct_enabled:
            return response
        
        expect_ct_value = f"max-age={self.config.expect_ct_max_age}"
        
        if self.config.expect_ct_enforce:
            expect_ct_value += ", enforce"
        
        if self.config.expect_ct_report_uri:
            expect_ct_value += f", report-uri=\"{self.config.expect_ct_report_uri}\""
        
        response.headers['Expect-CT'] = expect_ct_value
        return response
    
    def _get_csp_policy(self) -> str:
        """Get Content Security Policy"""
        if not self.config.block_mixed_content:
            return ""
        
        # Comprehensive CSP for financial application
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://checkout.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https: https://stripe.com https://checkout.stripe.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.stripe.com https://checkout.stripe.com; "
            "frame-src 'self' https://js.stripe.com https://checkout.stripe.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
    
    def _get_permissions_policy(self) -> str:
        """Get Permissions Policy"""
        return (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
    
    def _handle_ssl_error(self, error):
        """Handle SSL-related errors"""
        logger.error(f"SSL error occurred: {error}")
        
        if request.is_xhr:
            return {'error': 'SSL configuration error'}, 400
        
        return f"SSL configuration error: {error}", 400

class SSLSecurity:
    """SSL Security management class"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize SSL security with Flask app"""
        self.app = app
        
        # Initialize SSL middleware
        middleware = SSLSecurityMiddleware(app)
        
        # Register SSL configuration endpoint
        @app.route('/ssl/config', methods=['GET'])
        def ssl_config():
            """Get SSL configuration status"""
            return Response(
                json.dumps({
                    'ssl_enabled': middleware.config.ssl_enabled,
                    'force_https': middleware.config.force_https,
                    'hsts_enabled': middleware.config.hsts_enabled,
                    'session_secure': middleware.config.session_cookie_secure,
                    'tls_min_version': middleware.config.tls_min_version,
                    'tls_max_version': middleware.config.tls_max_version,
                    'environment': middleware.config.environment
                }, indent=2),
                status=200,
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
    
    # Check required settings for production
    if config.environment == 'production':
        if not config.ssl_enabled:
            issues.append("SSL must be enabled in production")
        
        if not config.force_https:
            issues.append("HTTPS enforcement must be enabled in production")
        
        if not config.session_cookie_secure:
            issues.append("Secure cookies must be enabled in production")
        
        if not config.hsts_enabled:
            issues.append("HSTS should be enabled in production")
    
    # Check TLS version settings
    if config.tls_min_version not in ['TLSv1.2', 'TLSv1.3']:
        issues.append("TLS minimum version must be TLSv1.2 or TLSv1.3")
    
    # Check HSTS settings
    if config.hsts_enabled:
        if config.hsts_max_age < 31536000:  # 1 year
            issues.append("HSTS max-age should be at least 1 year (31536000 seconds)")
    
    return issues

def check_ssl_labs_grade(domain: str) -> Dict[str, Any]:
    """Check SSL Labs grade for a domain"""
    try:
        url = f"https://api.ssllabs.com/api/v3/analyze?host={domain}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'READY':
            endpoints = data.get('endpoints', [])
            if endpoints:
                endpoint = endpoints[0]
                return {
                    'grade': endpoint.get('grade'),
                    'status': endpoint.get('statusMessage'),
                    'details': endpoint.get('details', {})
                }
        
        return {
            'grade': 'UNKNOWN',
            'status': data.get('status'),
            'details': {}
        }
    
    except Exception as e:
        logger.error(f"Error checking SSL Labs grade: {e}")
        return {
            'grade': 'ERROR',
            'status': str(e),
            'details': {}
        }

def check_certificate_expiry(domain: str, port: int = 443) -> Dict[str, Any]:
    """Check SSL certificate expiration"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                
                now = datetime.now()
                days_until_expiry = (not_after - now).days
                
                return {
                    'valid_from': not_before.isoformat(),
                    'valid_until': not_after.isoformat(),
                    'days_until_expiry': days_until_expiry,
                    'is_valid': now >= not_before and now <= not_after,
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'subject': dict(x[0] for x in cert['subject'])
                }
    
    except Exception as e:
        logger.error(f"Error checking certificate expiry: {e}")
        return {
            'error': str(e),
            'is_valid': False
        }

def generate_lets_encrypt_certificate(domain: str, email: str, staging: bool = False) -> bool:
    """Generate Let's Encrypt certificate using certbot"""
    try:
        # Build certbot command
        cmd = ['certbot', 'certonly', '--webroot', '-w', '/var/www/html']
        
        if staging:
            cmd.append('--staging')
        
        cmd.extend(['-d', domain, '--email', email, '--agree-tos', '--non-interactive'])
        
        # Run certbot
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"Successfully generated Let's Encrypt certificate for {domain}")
            return True
        else:
            logger.error(f"Failed to generate certificate: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error generating Let's Encrypt certificate: {e}")
        return False

def setup_ssl_monitoring(config: SSLConfig) -> None:
    """Setup SSL monitoring and alerts"""
    if not config.ssl_health_check_enabled:
        return
    
    # This would integrate with your monitoring system
    # For now, we'll just log the configuration
    logger.info("SSL monitoring configured with the following settings:")
    logger.info(f"  - Health check interval: {config.ssl_health_check_interval} seconds")
    logger.info(f"  - Target SSL Labs grade: {config.target_ssl_labs_grade}")
    logger.info(f"  - Certificate auto-renewal: {config.do_certificate_auto_renewal}")
