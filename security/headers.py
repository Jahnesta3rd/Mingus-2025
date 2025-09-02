#!/usr/bin/env python3
"""
MINGUS Security Headers Middleware
Banking-grade security headers for financial wellness application
Handles sensitive financial data, health information, and payment processing
"""

import os
import re
import logging
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
import secrets

from flask import Flask, request, Response, g, current_app
from werkzeug.exceptions import BadRequest

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration for different environments"""
    environment: str
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # CSP Configuration
    csp_report_only: bool = False
    csp_report_uri: Optional[str] = None
    csp_report_to: Optional[str] = None
    
    # Content Security Policy Sources
    csp_default_src: List[str] = field(default_factory=lambda: ["'self'"])
    csp_script_src: List[str] = field(default_factory=lambda: ["'self'", "'unsafe-inline'"])
    csp_style_src: List[str] = field(default_factory=lambda: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"])
    csp_img_src: List[str] = field(default_factory=lambda: ["'self'", "data:", "https:"])
    csp_font_src: List[str] = field(default_factory=lambda: ["'self'", "https://fonts.gstatic.com"])
    csp_connect_src: List[str] = field(default_factory=lambda: ["'self'", "https://api.stripe.com", "https://js.stripe.com"])
    csp_frame_src: List[str] = field(default_factory=lambda: ["'self'", "https://js.stripe.com", "https://hooks.stripe.com"])
    csp_object_src: List[str] = field(default_factory=lambda: ["'none'"])
    csp_media_src: List[str] = field(default_factory=lambda: ["'self'"])
    csp_manifest_src: List[str] = field(default_factory=lambda: ["'self'"])
    csp_worker_src: List[str] = field(default_factory=lambda: ["'self'"])
    csp_child_src: List[str] = field(default_factory=lambda: ["'self'", "https://js.stripe.com"])
    csp_form_action: List[str] = field(default_factory=lambda: ["'self'", "https://api.stripe.com"])
    csp_base_uri: List[str] = field(default_factory=lambda: ["'self'"])
    csp_frame_ancestors: List[str] = field(default_factory=lambda: ["'self'"])
    csp_upgrade_insecure_requests: bool = True
    csp_block_all_mixed_content: bool = True
    
    # Additional Security Headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
    expect_ct: Optional[str] = None
    
    # Feature Policy (legacy)
    feature_policy: str = "geolocation 'none'; microphone 'none'; camera 'none'; payment 'self'; usb 'none'; magnetometer 'none'; gyroscope 'none'; accelerometer 'none'"
    
    # Additional Headers
    x_download_options: str = "noopen"
    x_permitted_cross_domain_policies: str = "none"
    x_dns_prefetch_control: str = "off"
    x_powered_by: Optional[str] = None

class SecurityHeadersMiddleware:
    """Banking-grade security headers middleware for MINGUS Flask application"""
    
    def __init__(self, app: Flask, config: Optional[SecurityConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        self.nonce_cache = {}
        self.csp_violations = []
        
        # Register middleware
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Register error handlers
        self.app.register_error_handler(400, self._handle_bad_request)
        self.app.register_error_handler(403, self._handle_forbidden)
        self.app.register_error_handler(404, self._handle_not_found)
        self.app.register_error_handler(500, self._handle_server_error)
        
        logger.info(f"Security headers middleware initialized for {self.config.environment} environment")
    
    def _get_default_config(self) -> SecurityConfig:
        """Get default security configuration based on environment"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return SecurityConfig(
                environment='production',
                enable_hsts=True,
                hsts_max_age=31536000,  # 1 year
                hsts_include_subdomains=True,
                hsts_preload=True,
                csp_report_only=False,
                csp_report_uri=os.getenv('CSP_REPORT_URI'),
                csp_report_to=os.getenv('CSP_REPORT_TO'),
                csp_script_src=[
                    "'self'",
                    "'nonce-{nonce}'",
                    "https://www.googletagmanager.com",
                    "https://www.clarity.ms"
                ],
                csp_style_src=[
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdnjs.cloudflare.com",
                    "https://fonts.googleapis.com"
                ],
                csp_font_src=[
                    "'self'",
                    "https://cdnjs.cloudflare.com",
                    "https://fonts.gstatic.com"
                ],
                csp_img_src=[
                    "'self'",
                    "data:",
                    "https:"
                ],
                csp_connect_src=[
                    "'self'",
                    "https://www.google-analytics.com",
                    "https://www.clarity.ms"
                ],
                csp_frame_src=["'none'"],
                csp_object_src=["'none'"],
                csp_base_uri=["'self'"],
                csp_form_action=["'self'"],
                csp_upgrade_insecure_requests=True,
                csp_block_all_mixed_content=True,
                x_frame_options="DENY",
                referrer_policy="strict-origin-when-cross-origin",
                expect_ct=os.getenv('EXPECT_CT_HEADER', 'max-age=86400, enforce, report-uri="https://your-domain.com/ct-report"')
            )
        else:
            # Development configuration (less restrictive for debugging)
            return SecurityConfig(
                environment='development',
                enable_hsts=False,  # Disable HSTS in development
                csp_report_only=True,  # Report-only mode for development
                csp_script_src=[
                    "'self'",
                    "'unsafe-inline'",
                    "https://www.googletagmanager.com",
                    "https://www.clarity.ms"
                ],
                csp_style_src=[
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdnjs.cloudflare.com",
                    "https://fonts.googleapis.com"
                ],
                csp_font_src=[
                    "'self'",
                    "https://cdnjs.cloudflare.com",
                    "https://fonts.gstatic.com"
                ],
                csp_img_src=[
                    "'self'",
                    "data:",
                    "https:",
                    "http:"
                ],
                csp_connect_src=[
                    "'self'",
                    "https://www.google-analytics.com",
                    "https://www.clarity.ms",
                    "ws://localhost:*",  # Allow WebSocket connections in development
                    "wss://localhost:*"
                ],
                csp_frame_src=["'none'"],
                csp_object_src=["'none'"],
                csp_base_uri=["'self'"],
                csp_form_action=["'self'"],
                csp_upgrade_insecure_requests=False,  # Allow HTTP in development
                csp_block_all_mixed_content=False,
                x_frame_options="SAMEORIGIN",  # Less restrictive for development
                referrer_policy="no-referrer-when-downgrade"
            )
    
    def _before_request(self):
        """Before request processing"""
        # Generate nonce for CSP
        nonce = secrets.token_urlsafe(32)
        g.csp_nonce = nonce
        
        # Store nonce in cache for this request
        request_id = request.headers.get('X-Request-ID', secrets.token_urlsafe(16))
        self.nonce_cache[request_id] = nonce
        
        # Add request ID to response headers
        g.request_id = request_id
        
        # Log security-relevant request information
        self._log_security_event('request_start', {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'method': request.method,
            'path': request.path,
            'referrer': request.headers.get('Referer'),
            'request_id': request_id
        })
    
    def _after_request(self, response: Response) -> Response:
        """After request processing - add security headers"""
        try:
            # Add security headers
            self._add_security_headers(response)
            
            # Add request ID to response
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            # Log response security information
            self._log_security_event('response_complete', {
                'status_code': response.status_code,
                'content_length': len(response.get_data()),
                'content_type': response.headers.get('Content-Type'),
                'request_id': getattr(g, 'request_id', 'unknown')
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
            return response
    
    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers to response"""
        config = self.config
        
        # HTTP Strict Transport Security (HSTS)
        if config.enable_hsts and request.is_secure:
            hsts_parts = [f"max-age={config.hsts_max_age}"]
            if config.hsts_include_subdomains:
                hsts_parts.append("includeSubDomains")
            if config.hsts_preload:
                hsts_parts.append("preload")
            response.headers['Strict-Transport-Security'] = "; ".join(hsts_parts)
        
        # Content Security Policy (CSP)
        csp_directives = self._build_csp_directives()
        if csp_directives:
            csp_header = "Content-Security-Policy"
            if config.csp_report_only:
                csp_header = "Content-Security-Policy-Report-Only"
            
            response.headers[csp_header] = "; ".join(csp_directives)
        
        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = config.x_content_type_options
        
        # X-Frame-Options
        response.headers['X-Frame-Options'] = config.x_frame_options
        
        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = config.x_xss_protection
        
        # Referrer-Policy
        response.headers['Referrer-Policy'] = config.referrer_policy
        
        # Permissions-Policy
        response.headers['Permissions-Policy'] = config.permissions_policy
        
        # Feature-Policy (legacy, for older browsers)
        response.headers['Feature-Policy'] = config.feature_policy
        
        # Expect-CT (Certificate Transparency)
        if config.expect_ct:
            response.headers['Expect-CT'] = config.expect_ct
        
        # Additional security headers
        response.headers['X-Download-Options'] = config.x_download_options
        response.headers['X-Permitted-Cross-Domain-Policies'] = config.x_permitted_cross_domain_policies
        response.headers['X-DNS-Prefetch-Control'] = config.x_dns_prefetch_control
        
        # Remove X-Powered-By header
        if config.x_powered_by is None:
            response.headers.pop('X-Powered-By', None)
        elif config.x_powered_by:
            response.headers['X-Powered-By'] = config.x_powered_by
        
        # Add security-related custom headers
        response.headers['X-Security-Headers'] = 'enabled'
        response.headers['X-Content-Security-Policy-Version'] = '3.0'
    
    def _build_csp_directives(self) -> List[str]:
        """Build Content Security Policy directives"""
        config = self.config
        directives = []
        
        # Get nonce for this request
        nonce = getattr(g, 'csp_nonce', '')
        
        # Default source
        if config.csp_default_src:
            directives.append(f"default-src {' '.join(config.csp_default_src)}")
        
        # Script source
        if config.csp_script_src:
            script_src = []
            for src in config.csp_script_src:
                if src == "'nonce-{nonce}'" and nonce:
                    script_src.append(f"'nonce-{nonce}'")
                else:
                    script_src.append(src)
            directives.append(f"script-src {' '.join(script_src)}")
        
        # Style source
        if config.csp_style_src:
            directives.append(f"style-src {' '.join(config.csp_style_src)}")
        
        # Image source
        if config.csp_img_src:
            directives.append(f"img-src {' '.join(config.csp_img_src)}")
        
        # Font source
        if config.csp_font_src:
            directives.append(f"font-src {' '.join(config.csp_font_src)}")
        
        # Connect source
        if config.csp_connect_src:
            directives.append(f"connect-src {' '.join(config.csp_connect_src)}")
        
        # Frame source
        if config.csp_frame_src:
            directives.append(f"frame-src {' '.join(config.csp_frame_src)}")
        
        # Object source
        if config.csp_object_src:
            directives.append(f"object-src {' '.join(config.csp_object_src)}")
        
        # Media source
        if config.csp_media_src:
            directives.append(f"media-src {' '.join(config.csp_media_src)}")
        
        # Manifest source
        if config.csp_manifest_src:
            directives.append(f"manifest-src {' '.join(config.csp_manifest_src)}")
        
        # Worker source
        if config.csp_worker_src:
            directives.append(f"worker-src {' '.join(config.csp_worker_src)}")
        
        # Child source
        if config.csp_child_src:
            directives.append(f"child-src {' '.join(config.csp_child_src)}")
        
        # Form action
        if config.csp_form_action:
            directives.append(f"form-action {' '.join(config.csp_form_action)}")
        
        # Base URI
        if config.csp_base_uri:
            directives.append(f"base-uri {' '.join(config.csp_base_uri)}")
        
        # Frame ancestors
        if config.csp_frame_ancestors:
            directives.append(f"frame-ancestors {' '.join(config.csp_frame_ancestors)}")
        
        # Upgrade insecure requests
        if config.csp_upgrade_insecure_requests:
            directives.append("upgrade-insecure-requests")
        
        # Block all mixed content
        if config.csp_block_all_mixed_content:
            directives.append("block-all-mixed-content")
        
        # Report URI
        if config.csp_report_uri:
            directives.append(f"report-uri {config.csp_report_uri}")
        
        # Report to
        if config.csp_report_to:
            directives.append(f"report-to {config.csp_report_to}")
        
        return directives
    
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
        
        if 'user_agent' in data:
            data['user_agent_hash'] = hashlib.sha256(data['user_agent'].encode()).hexdigest()[:16]
            del data['user_agent']
        
        logger.info(f"Security event: {json.dumps(log_data)}")
    
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
        """Create error response with security headers"""
        response = Response(
            json.dumps({'error': message, 'status_code': status_code}),
            status=status_code,
            content_type='application/json'
        )
        self._add_security_headers(response)
        return response
    
    def validate_headers(self, response: Response) -> Dict[str, Any]:
        """Validate security headers in response"""
        validation_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'headers_present': {},
            'headers_missing': [],
            'recommendations': []
        }
        
        required_headers = {
            'Strict-Transport-Security': 'HSTS',
            'Content-Security-Policy': 'CSP',
            'X-Content-Type-Options': 'Content Type Options',
            'X-Frame-Options': 'Frame Options',
            'X-XSS-Protection': 'XSS Protection',
            'Referrer-Policy': 'Referrer Policy',
            'Permissions-Policy': 'Permissions Policy'
        }
        
        for header, description in required_headers.items():
            if header in response.headers:
                validation_results['headers_present'][header] = {
                    'value': response.headers[header],
                    'description': description
                }
            else:
                validation_results['headers_missing'].append(header)
                validation_results['recommendations'].append(f"Add {header} header")
        
        # Check for security issues
        if 'X-Powered-By' in response.headers:
            validation_results['recommendations'].append("Remove X-Powered-By header")
        
        return validation_results
    
    def get_csp_nonce(self) -> str:
        """Get CSP nonce for current request"""
        return getattr(g, 'csp_nonce', '')
    
    def add_csp_violation(self, violation_data: Dict[str, Any]):
        """Add CSP violation to tracking"""
        violation_data['timestamp'] = datetime.utcnow().isoformat()
        violation_data['request_id'] = getattr(g, 'request_id', 'unknown')
        self.csp_violations.append(violation_data)
        
        # Log violation
        logger.warning(f"CSP violation: {json.dumps(violation_data)}")
        
        # Keep only last 1000 violations
        if len(self.csp_violations) > 1000:
            self.csp_violations = self.csp_violations[-1000:]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.config.environment,
            'csp_violations_count': len(self.csp_violations),
            'recent_csp_violations': self.csp_violations[-10:],
            'nonce_cache_size': len(self.nonce_cache),
            'configuration': {
                'enable_hsts': self.config.enable_hsts,
                'csp_report_only': self.config.csp_report_only,
                'x_frame_options': self.config.x_frame_options,
                'referrer_policy': self.config.referrer_policy
            }
        }

# Flask extension for easy integration
class SecurityHeaders:
    """Flask extension for security headers"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.middleware = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the extension with the Flask app"""
        self.app = app
        self.middleware = SecurityHeadersMiddleware(app)
        
        # Add template context processor for CSP nonce
        @app.context_processor
        def inject_csp_nonce():
            return {'csp_nonce': self.middleware.get_csp_nonce()}
        
        # Add CSP violation reporting endpoint
        @app.route('/csp-report', methods=['POST'])
        def csp_report():
            try:
                violation_data = request.get_json()
                if violation_data:
                    self.middleware.add_csp_violation(violation_data)
                return Response(status=204)
            except Exception as e:
                logger.error(f"Error processing CSP report: {e}")
                return Response(status=400)
        
        # Add security headers validation endpoint
        @app.route('/security/validate', methods=['GET'])
        def validate_security_headers():
            if not app.debug:
                return Response(status=404)
            
            response = Response("Security headers validation")
            validation_results = self.middleware.validate_headers(response)
            return Response(
                json.dumps(validation_results, indent=2),
                content_type='application/json'
            )
        
        # Add security report endpoint
        @app.route('/security/report', methods=['GET'])
        def security_report():
            if not app.debug:
                return Response(status=404)
            
            report = self.middleware.get_security_report()
            return Response(
                json.dumps(report, indent=2),
                content_type='application/json'
            )

# Convenience function for creating security config
def create_security_config(environment: str = None, **kwargs) -> SecurityConfig:
    """Create security configuration with custom overrides"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    config = SecurityConfig(environment=environment)
    
    # Override with provided kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config 