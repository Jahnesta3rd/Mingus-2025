#!/usr/bin/env python3
"""
MINGUS SSL Security Middleware
Comprehensive HTTPS and SSL security middleware for financial wellness application
Ensures all data transmission is secure with banking-grade encryption
"""

import os
import logging
import hashlib
import ssl
import socket
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, Response, g, current_app, redirect, url_for, session
from werkzeug.exceptions import BadRequest, Forbidden

# Configure logging
logger = logging.getLogger(__name__)

class SSLSecurityMiddleware:
    """Comprehensive SSL/TLS security middleware for MINGUS application"""
    
    def __init__(self, app: Flask, config: Optional[Dict[str, Any]] = None):
        self.app = app
        self.config = config or self._get_default_config()
        
        # Register middleware functions
        self._register_middleware()
        
        logger.info(f"SSL security middleware initialized for {self.config.get('environment', 'production')} environment")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default SSL configuration based on environment"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return {
                'environment': 'production',
                'ssl_enabled': True,
                'force_https': True,
                'tls_min_version': "TLSv1.2",
                'tls_max_version': "TLSv1.3",
                'cert_pinning_enabled': True,
                'cert_pinning_hashes': [
                    # Add your certificate pinning hashes here
                    # Example: "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
                ],
                'hsts_enabled': True,
                'hsts_max_age': 31536000,
                'hsts_include_subdomains': True,
                'hsts_preload': True,
                'session_cookie_secure': True,
                'session_cookie_httponly': True,
                'session_cookie_samesite': "Strict",
                'session_cookie_max_age': 1800,  # 30 minutes for financial app
                'block_mixed_content': True,
                'upgrade_insecure_requests': True,
                'expect_ct_enabled': True,
                'expect_ct_max_age': 86400,
                'expect_ct_enforce': True,
                'expect_ct_report_uri': os.getenv('EXPECT_CT_REPORT_URI'),
                'ssl_health_check_enabled': True,
                'digital_ocean_enabled': True,
                'do_load_balancer_ssl': True,
                'do_certificate_auto_renewal': True
            }
        else:
            # Development configuration
            return {
                'environment': 'development',
                'ssl_enabled': False,
                'force_https': False,
                'tls_min_version': "TLSv1.2",
                'tls_max_version': "TLSv1.3",
                'cert_pinning_enabled': False,
                'cert_pinning_hashes': [],
                'hsts_enabled': False,
                'hsts_max_age': 31536000,
                'hsts_include_subdomains': False,
                'hsts_preload': False,
                'session_cookie_secure': False,
                'session_cookie_httponly': True,
                'session_cookie_samesite': "Lax",
                'session_cookie_max_age': 3600,
                'block_mixed_content': False,
                'upgrade_insecure_requests': False,
                'expect_ct_enabled': False,
                'expect_ct_max_age': 86400,
                'expect_ct_enforce': False,
                'expect_ct_report_uri': None,
                'ssl_health_check_enabled': False,
                'digital_ocean_enabled': False,
                'do_load_balancer_ssl': False,
                'do_certificate_auto_renewal': False
            }
    
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
        if not self.config.get('force_https', False):
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
        if not self.config.get('ssl_enabled', False):
            return
        
        # Check for secure connection headers
        if request.headers.get('X-Forwarded-Proto') == 'http':
            logger.warning(f"Insecure request detected: {request.url}")
            return BadRequest("Insecure request not allowed")
    
    def _check_certificate_pinning(self):
        """Check certificate pinning if enabled"""
        if not self.config.get('cert_pinning_enabled', False):
            return
        
        # Certificate pinning validation would go here
        # This is typically handled at the load balancer level
        pass
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to all responses"""
        
        # Basic security headers
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp_policy = self._get_csp_policy()
        if csp_policy:
            response.headers['Content-Security-Policy'] = csp_policy
        
        # Permissions Policy
        permissions_policy = self._get_permissions_policy()
        if permissions_policy:
            response.headers['Permissions-Policy'] = permissions_policy
        
        # Feature Policy (legacy)
        feature_policy = self._get_feature_policy()
        if feature_policy:
            response.headers['Feature-Policy'] = feature_policy
        
        # Cross-Origin headers
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        return response
    
    def _add_hsts_header(self, response: Response) -> Response:
        """Add HTTP Strict Transport Security header"""
        if not self.config.get('hsts_enabled', False):
            return response
        
        hsts_value = f"max-age={self.config.get('hsts_max_age', 31536000)}"
        
        if self.config.get('hsts_include_subdomains', False):
            hsts_value += "; includeSubDomains"
        
        if self.config.get('hsts_preload', False):
            hsts_value += "; preload"
        
        response.headers['Strict-Transport-Security'] = hsts_value
        return response
    
    def _add_expect_ct_header(self, response: Response) -> Response:
        """Add Certificate Transparency header"""
        if not self.config.get('expect_ct_enabled', False):
            return response
        
        expect_ct_value = f"max-age={self.config.get('expect_ct_max_age', 86400)}"
        
        if self.config.get('expect_ct_enforce', False):
            expect_ct_value += ", enforce"
        
        report_uri = self.config.get('expect_ct_report_uri')
        if report_uri:
            expect_ct_value += f", report-uri=\"{report_uri}\""
        
        response.headers['Expect-CT'] = expect_ct_value
        return response
    
    def _get_csp_policy(self) -> str:
        """Get Content Security Policy"""
        if not self.config.get('block_mixed_content', False):
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
    
    def _get_feature_policy(self) -> str:
        """Get Feature Policy (legacy)"""
        return (
            "geolocation 'none'; "
            "microphone 'none'; "
            "camera 'none'; "
            "payment 'self'; "
            "usb 'none'; "
            "magnetometer 'none'; "
            "gyroscope 'none'; "
            "accelerometer 'none'"
        )
    
    def _handle_ssl_error(self, error):
        """Handle SSL-related errors"""
        logger.error(f"SSL error occurred: {error}")
        
        if request.is_xhr:
            return {'error': 'SSL configuration error'}, 400
        
        return f"SSL configuration error: {error}", 400

def require_https():
    """Decorator to require HTTPS for specific routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def secure_cookies():
    """Decorator to ensure secure cookie settings"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Set secure cookie configuration
            session.permanent = True
            session.modified = True
            
            # Ensure session cookie is secure in production
            if os.getenv('FLASK_ENV') == 'production':
                session.secure = True
                session.httponly = True
                session.samesite = 'Strict'
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_ssl_configuration(config: Dict[str, Any]) -> List[str]:
    """Validate SSL configuration and return list of issues"""
    issues = []
    
    # Check required settings for production
    if config.get('environment') == 'production':
        if not config.get('ssl_enabled'):
            issues.append("SSL must be enabled in production")
        
        if not config.get('force_https'):
            issues.append("HTTPS enforcement must be enabled in production")
        
        if not config.get('session_cookie_secure'):
            issues.append("Secure cookies must be enabled in production")
        
        if not config.get('hsts_enabled'):
            issues.append("HSTS should be enabled in production")
    
    # Check TLS version settings
    tls_min = config.get('tls_min_version')
    if tls_min and tls_min not in ['TLSv1.2', 'TLSv1.3']:
        issues.append("TLS minimum version must be TLSv1.2 or TLSv1.3")
    
    # Check HSTS settings
    if config.get('hsts_enabled'):
        hsts_max_age = config.get('hsts_max_age', 0)
        if hsts_max_age < 31536000:  # 1 year
            issues.append("HSTS max-age should be at least 1 year (31536000 seconds)")
    
    return issues

def init_ssl_middleware(app: Flask, config: Optional[Dict[str, Any]] = None):
    """Initialize SSL middleware for Flask application"""
    middleware = SSLSecurityMiddleware(app, config)
    
    # Validate configuration
    issues = validate_ssl_configuration(middleware.config)
    if issues:
        logger.warning("SSL configuration issues detected:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    return middleware
