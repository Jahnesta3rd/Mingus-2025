#!/usr/bin/env python3
"""
Comprehensive Content Security Policy Manager for Mingus Financial App
Implements strict CSP policies for financial applications with third-party integrations
"""

import os
import re
import hashlib
import secrets
import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, request, Response, current_app, g
from werkzeug.exceptions import BadRequest

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CSPDirective:
    """CSP directive configuration"""
    name: str
    sources: List[str] = field(default_factory=list)
    nonce_required: bool = False
    strict_mode: bool = True

@dataclass
class CSPPolicy:
    """Complete CSP policy configuration"""
    environment: str
    report_only: bool = False
    report_uri: Optional[str] = None
    report_to: Optional[str] = None
    directives: Dict[str, CSPDirective] = field(default_factory=dict)
    nonce_length: int = 32
    hash_algorithms: List[str] = field(default_factory=lambda: ['sha256', 'sha384', 'sha512'])

class CSPResourceAuditor:
    """Audits application resources for CSP policy creation"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.external_domains: Set[str] = set()
        self.inline_scripts: List[str] = []
        self.inline_styles: List[str] = []
        self.api_endpoints: Set[str] = set()
        self.third_party_integrations: Dict[str, List[str]] = {}
        
    def audit_resources(self) -> Dict[str, any]:
        """Comprehensive resource audit"""
        logger.info("Starting CSP resource audit...")
        
        # Audit external resources
        self._audit_external_resources()
        
        # Audit inline content
        self._audit_inline_content()
        
        # Audit API endpoints
        self._audit_api_endpoints()
        
        # Audit third-party integrations
        self._audit_third_party_integrations()
        
        return {
            'external_domains': list(self.external_domains),
            'inline_scripts': self.inline_scripts,
            'inline_styles': self.inline_styles,
            'api_endpoints': list(self.api_endpoints),
            'third_party_integrations': self.third_party_integrations
        }
    
    def _audit_external_resources(self):
        """Audit external scripts, stylesheets, and resources"""
        # Known external domains from codebase analysis
        external_resources = {
            'scripts': [
                'https://js.stripe.com',
                'https://checkout.stripe.com',
                'https://www.googletagmanager.com',
                'https://www.google-analytics.com',
                'https://clarity.microsoft.com',
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com',
                'https://unpkg.com'
            ],
            'styles': [
                'https://fonts.googleapis.com',
                'https://fonts.gstatic.com',
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com'
            ],
            'images': [
                'https://stripe.com',
                'https://checkout.stripe.com',
                'https://www.google-analytics.com'
            ],
            'frames': [
                'https://js.stripe.com',
                'https://hooks.stripe.com',
                'https://checkout.stripe.com'
            ]
        }
        
        for category, urls in external_resources.items():
            for url in urls:
                domain = urlparse(url).netloc
                self.external_domains.add(domain)
    
    def _audit_inline_content(self):
        """Audit inline scripts and styles"""
        # Common inline patterns found in the codebase
        inline_patterns = [
            # Service worker registration
            "navigator.serviceWorker.register",
            # Analytics initialization
            "gtag('config'",
            "clarity('set'",
            # Form validation
            "document.getElementById",
            "addEventListener",
            # Stripe integration
            "stripe.createToken",
            "stripe.createPaymentMethod"
        ]
        
        self.inline_scripts.extend(inline_patterns)
    
    def _audit_api_endpoints(self):
        """Audit API endpoints for connect-src directive"""
        # Internal API endpoints
        internal_apis = [
            '/api/auth',
            '/api/payment',
            '/api/webhooks',
            '/api/analytics',
            '/api/user',
            '/api/subscription'
        ]
        
        # External API endpoints
        external_apis = [
            'https://api.stripe.com',
            'https://api.supabase.co',
            'https://api.twilio.com',
            'https://api.resend.com',
            'https://api.plaid.com',
            'https://www.google-analytics.com',
            'https://analytics.google.com',
            'https://clarity.microsoft.com',
            'https://c.clarity.ms'
        ]
        
        self.api_endpoints.update(internal_apis)
        self.api_endpoints.update(external_apis)
    
    def _audit_third_party_integrations(self):
        """Audit third-party service integrations"""
        self.third_party_integrations = {
            'stripe': {
                'domains': [
                    'js.stripe.com',
                    'checkout.stripe.com',
                    'hooks.stripe.com',
                    'api.stripe.com'
                ],
                'features': ['payment_processing', 'webhooks', 'checkout']
            },
            'supabase': {
                'domains': [
                    'api.supabase.co',
                    'supabase.co'
                ],
                'features': ['database', 'auth', 'storage']
            },
            'twilio': {
                'domains': [
                    'api.twilio.com',
                    'twilio.com'
                ],
                'features': ['sms', 'voice', 'webhooks']
            },
            'google_analytics': {
                'domains': [
                    'www.googletagmanager.com',
                    'www.google-analytics.com',
                    'analytics.google.com'
                ],
                'features': ['analytics', 'tracking']
            },
            'microsoft_clarity': {
                'domains': [
                    'clarity.microsoft.com',
                    'c.clarity.ms'
                ],
                'features': ['analytics', 'session_recording']
            },
            'resend': {
                'domains': [
                    'api.resend.com',
                    'resend.com'
                ],
                'features': ['email', 'webhooks']
            },
            'plaid': {
                'domains': [
                    'api.plaid.com',
                    'plaid.com'
                ],
                'features': ['banking', 'financial_data']
            }
        }

class CSPPolicyManager:
    """Manages Content Security Policy generation and enforcement"""
    
    def __init__(self, app: Flask, environment: str = 'production'):
        self.app = app
        self.environment = environment
        self.auditor = CSPResourceAuditor(app)
        self.policy = self._create_policy()
        self.nonce_cache = {}
        
    def _create_policy(self) -> CSPPolicy:
        """Create CSP policy based on environment and audit results"""
        audit_results = self.auditor.audit_resources()
        
        if self.environment == 'production':
            return self._create_production_policy(audit_results)
        elif self.environment == 'staging':
            return self._create_staging_policy(audit_results)
        else:
            return self._create_development_policy(audit_results)
    
    def _create_production_policy(self, audit_results: Dict) -> CSPPolicy:
        """Create strict production CSP policy"""
        policy = CSPPolicy(
            environment='production',
            report_only=False,
            report_uri=os.getenv('CSP_REPORT_URI'),
            report_to=os.getenv('CSP_REPORT_TO'),
            directives={
                'default-src': CSPDirective(
                    name='default-src',
                    sources=["'self'"],
                    strict_mode=True
                ),
                'script-src': CSPDirective(
                    name='script-src',
                    sources=[
                        "'self'",
                        "'nonce-{nonce}'",
                        "https://js.stripe.com",
                        "https://checkout.stripe.com",
                        "https://www.googletagmanager.com",
                        "https://www.google-analytics.com",
                        "https://clarity.microsoft.com"
                    ],
                    nonce_required=True,
                    strict_mode=True
                ),
                'style-src': CSPDirective(
                    name='style-src',
                    sources=[
                        "'self'",
                        "'unsafe-inline'",  # Required for dynamic styles
                        "https://fonts.googleapis.com",
                        "https://cdn.jsdelivr.net"
                    ],
                    strict_mode=True
                ),
                'img-src': CSPDirective(
                    name='img-src',
                    sources=[
                        "'self'",
                        "data:",
                        "https:",
                        "https://stripe.com",
                        "https://checkout.stripe.com",
                        "https://www.google-analytics.com"
                    ],
                    strict_mode=True
                ),
                'font-src': CSPDirective(
                    name='font-src',
                    sources=[
                        "'self'",
                        "https://fonts.gstatic.com",
                        "data:"
                    ],
                    strict_mode=True
                ),
                'connect-src': CSPDirective(
                    name='connect-src',
                    sources=[
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
                    strict_mode=True
                ),
                'frame-src': CSPDirective(
                    name='frame-src',
                    sources=[
                        "'self'",
                        "https://js.stripe.com",
                        "https://hooks.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    strict_mode=True
                ),
                'object-src': CSPDirective(
                    name='object-src',
                    sources=["'none'"],
                    strict_mode=True
                ),
                'media-src': CSPDirective(
                    name='media-src',
                    sources=["'self'"],
                    strict_mode=True
                ),
                'manifest-src': CSPDirective(
                    name='manifest-src',
                    sources=["'self'"],
                    strict_mode=True
                ),
                'worker-src': CSPDirective(
                    name='worker-src',
                    sources=["'self'"],
                    strict_mode=True
                ),
                'frame-ancestors': CSPDirective(
                    name='frame-ancestors',
                    sources=["'none'"],
                    strict_mode=True
                ),
                'base-uri': CSPDirective(
                    name='base-uri',
                    sources=["'self'"],
                    strict_mode=True
                ),
                'form-action': CSPDirective(
                    name='form-action',
                    sources=[
                        "'self'",
                        "https://api.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    strict_mode=True
                ),
                'upgrade-insecure-requests': CSPDirective(
                    name='upgrade-insecure-requests',
                    sources=[],
                    strict_mode=True
                ),
                'block-all-mixed-content': CSPDirective(
                    name='block-all-mixed-content',
                    sources=[],
                    strict_mode=True
                )
            }
        )
        
        return policy
    
    def _create_staging_policy(self, audit_results: Dict) -> CSPPolicy:
        """Create staging CSP policy (slightly less strict)"""
        policy = self._create_production_policy(audit_results)
        policy.report_only = True  # Report-only mode for staging
        return policy
    
    def _create_development_policy(self, audit_results: Dict) -> CSPPolicy:
        """Create development CSP policy (permissive for debugging)"""
        policy = CSPPolicy(
            environment='development',
            report_only=True,  # Report-only mode for development
            directives={
                'default-src': CSPDirective(
                    name='default-src',
                    sources=["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                    strict_mode=False
                ),
                'script-src': CSPDirective(
                    name='script-src',
                    sources=[
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
                    strict_mode=False
                ),
                'style-src': CSPDirective(
                    name='style-src',
                    sources=[
                        "'self'",
                        "'unsafe-inline'",
                        "https://fonts.googleapis.com",
                        "https://cdn.jsdelivr.net",
                        "https://cdnjs.cloudflare.com"
                    ],
                    strict_mode=False
                ),
                'img-src': CSPDirective(
                    name='img-src',
                    sources=[
                        "'self'",
                        "data:",
                        "https:",
                        "blob:"
                    ],
                    strict_mode=False
                ),
                'font-src': CSPDirective(
                    name='font-src',
                    sources=[
                        "'self'",
                        "https://fonts.gstatic.com",
                        "data:"
                    ],
                    strict_mode=False
                ),
                'connect-src': CSPDirective(
                    name='connect-src',
                    sources=[
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
                        "https://c.clarity.ms",
                        "ws://localhost:*",
                        "wss://localhost:*"
                    ],
                    strict_mode=False
                ),
                'frame-src': CSPDirective(
                    name='frame-src',
                    sources=[
                        "'self'",
                        "https://js.stripe.com",
                        "https://hooks.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    strict_mode=False
                ),
                'object-src': CSPDirective(
                    name='object-src',
                    sources=["'none'"],
                    strict_mode=False
                ),
                'media-src': CSPDirective(
                    name='media-src',
                    sources=["'self'"],
                    strict_mode=False
                ),
                'manifest-src': CSPDirective(
                    name='manifest-src',
                    sources=["'self'"],
                    strict_mode=False
                ),
                'worker-src': CSPDirective(
                    name='worker-src',
                    sources=["'self'", "blob:"],
                    strict_mode=False
                ),
                'frame-ancestors': CSPDirective(
                    name='frame-ancestors',
                    sources=["'self'"],
                    strict_mode=False
                ),
                'base-uri': CSPDirective(
                    name='base-uri',
                    sources=["'self'"],
                    strict_mode=False
                ),
                'form-action': CSPDirective(
                    name='form-action',
                    sources=[
                        "'self'",
                        "https://api.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    strict_mode=False
                )
            }
        )
        
        return policy
    
    def generate_nonce(self, request_id: str = None) -> str:
        """Generate cryptographically secure nonce"""
        if request_id is None:
            request_id = str(id(request))
        
        if request_id in self.nonce_cache:
            return self.nonce_cache[request_id]
        
        nonce = secrets.token_urlsafe(self.policy.nonce_length)
        self.nonce_cache[request_id] = nonce
        
        return nonce
    
    def build_csp_header(self, nonce: str = None) -> str:
        """Build CSP header string"""
        if nonce is None:
            nonce = self.generate_nonce()
        
        directives = []
        
        for directive_name, directive in self.policy.directives.items():
            if directive.sources:
                # Replace nonce placeholder
                sources = [source.replace('{nonce}', nonce) for source in directive.sources]
                directives.append(f"{directive_name} {' '.join(sources)}")
        
        # Add report directives
        if self.policy.report_uri:
            directives.append(f"report-uri {self.policy.report_uri}")
        
        if self.policy.report_to:
            directives.append(f"report-to {self.policy.report_to}")
        
        return "; ".join(directives)
    
    def add_csp_headers(self, response: Response, nonce: str = None) -> Response:
        """Add CSP headers to response"""
        csp_header = self.build_csp_header(nonce)
        
        if self.policy.report_only:
            response.headers['Content-Security-Policy-Report-Only'] = csp_header
        else:
            response.headers['Content-Security-Policy'] = csp_header
        
        # Add additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Permissions Policy
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(self), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers['Permissions-Policy'] = permissions_policy
        
        return response

class CSPMiddleware:
    """Flask middleware for CSP enforcement"""
    
    def __init__(self, app: Flask, environment: str = None):
        self.app = app
        self.environment = environment or os.getenv('FLASK_ENV', 'development')
        self.csp_manager = CSPPolicyManager(app, self.environment)
        
        # Register middleware
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        logger.info(f"CSP middleware initialized for {self.environment} environment")
    
    def _before_request(self):
        """Before request processing"""
        # Generate nonce for this request
        g.csp_nonce = self.csp_manager.generate_nonce()
        
        # Store nonce in app context for template access
        current_app.jinja_env.globals['csp_nonce'] = g.csp_nonce
    
    def _after_request(self, response: Response) -> Response:
        """After request processing"""
        # Add CSP headers
        response = self.csp_manager.add_csp_headers(response, g.csp_nonce)
        
        return response

class CSPViolationHandler:
    """Handles CSP violation reports"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.violation_logger = logging.getLogger('csp.violations')
        
        # Register violation endpoint
        app.route('/csp-violation-report', methods=['POST'])(self._handle_violation_report)
    
    def _handle_violation_report(self):
        """Handle CSP violation reports"""
        try:
            violation_data = request.get_json()
            
            if not violation_data:
                return {'error': 'Invalid violation data'}, 400
            
            # Log violation
            self._log_violation(violation_data)
            
            # Store violation for analysis
            self._store_violation(violation_data)
            
            # Alert if critical
            if self._is_critical_violation(violation_data):
                self._alert_critical_violation(violation_data)
            
            return {'status': 'received'}, 200
            
        except Exception as e:
            logger.error(f"Error handling CSP violation: {e}")
            return {'error': 'Internal server error'}, 500
    
    def _log_violation(self, violation_data: Dict):
        """Log CSP violation"""
        self.violation_logger.warning(
            f"CSP Violation: {violation_data.get('violated-directive', 'unknown')} "
            f"from {violation_data.get('source-file', 'unknown')} "
            f"at {violation_data.get('line-number', 'unknown')}"
        )
    
    def _store_violation(self, violation_data: Dict):
        """Store violation for analysis"""
        # In production, store in database or monitoring service
        # For now, just log to file
        violation_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr,
            'violation': violation_data
        }
        
        # Store in file for analysis
        with open('csp_violations.log', 'a') as f:
            f.write(json.dumps(violation_record) + '\n')
    
    def _is_critical_violation(self, violation_data: Dict) -> bool:
        """Check if violation is critical"""
        critical_directives = [
            'script-src',
            'object-src',
            'base-uri'
        ]
        
        violated_directive = violation_data.get('violated-directive', '')
        return any(directive in violated_directive for directive in critical_directives)
    
    def _alert_critical_violation(self, violation_data: Dict):
        """Alert on critical violations"""
        # In production, send alert via email, Slack, etc.
        logger.critical(
            f"CRITICAL CSP VIOLATION: {violation_data.get('violated-directive')} "
            f"from {violation_data.get('source-file')}"
        )

# Utility functions for templates
def get_csp_nonce():
    """Get CSP nonce for templates"""
    return g.get('csp_nonce', '')

def csp_script_tag(script_content: str, nonce: str = None) -> str:
    """Generate script tag with CSP nonce"""
    if nonce is None:
        nonce = get_csp_nonce()
    
    return f'<script nonce="{nonce}">{script_content}</script>'

def csp_style_tag(style_content: str, nonce: str = None) -> str:
    """Generate style tag with CSP nonce"""
    if nonce is None:
        nonce = get_csp_nonce()
    
    return f'<style nonce="{nonce}">{style_content}</style>'

# Example usage
if __name__ == "__main__":
    # Example Flask app setup
    app = Flask(__name__)
    
    # Initialize CSP middleware
    csp_middleware = CSPMiddleware(app, 'production')
    
    # Initialize violation handler
    violation_handler = CSPViolationHandler(app)
    
    # Register template helpers
    app.jinja_env.globals['csp_nonce'] = get_csp_nonce
    app.jinja_env.globals['csp_script_tag'] = csp_script_tag
    app.jinja_env.globals['csp_style_tag'] = csp_style_tag
    
    print("CSP Policy Manager initialized successfully!")
