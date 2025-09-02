"""
Content Security Policy (CSP) Middleware
Provides comprehensive CSP protection against XSS, injection attacks, and other security vulnerabilities
"""

import re
from typing import Dict, List, Optional
from flask import request, current_app, g
from loguru import logger

class CSPMiddleware:
    """Content Security Policy middleware for Flask applications"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize CSP middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Register CSP configuration
        app.config.setdefault('CSP_DIRECTIVES', self.get_default_csp_directives())
        
        logger.info("CSP middleware initialized")
    
    def get_default_csp_directives(self) -> Dict[str, List[str]]:
        """Get default CSP directives if none configured"""
        return {
            'default-src': ["'self'"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
            'script-src': ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com", "https://www.clarity.ms"],
            'font-src': ["'self'", "https://cdnjs.cloudflare.com", "https://fonts.gstatic.com"],
            'img-src': ["'self'", "data:", "https:", "http:"],
            'connect-src': ["'self'", "https://www.google-analytics.com", "https://www.clarity.ms"],
            'frame-src': ["'none'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'upgrade-insecure-requests': []
        }
    
    def before_request(self):
        """Process requests before handling"""
        # Log CSP-related request details
        if current_app.config.get('DEBUG'):
            self.log_csp_request()
    
    def after_request(self, response):
        """Add CSP headers to response"""
        # Check if CSP headers are already set by existing security system
        existing_csp = response.headers.get('Content-Security-Policy') or response.headers.get('Content-Security-Policy-Report-Only')
        
        if existing_csp:
            # Log that existing CSP is being used
            if current_app.config.get('DEBUG'):
                logger.debug(f"Existing CSP headers detected: {existing_csp}")
            return response
        
        # Get CSP configuration from app config
        csp_directives = current_app.config.get('CSP_DIRECTIVES', {})
        
        # Build CSP header string
        csp_header = self.build_csp_header(csp_directives)
        
        # Add CSP headers only if not already set
        response.headers['Content-Security-Policy'] = csp_header
        response.headers['Content-Security-Policy-Report-Only'] = csp_header  # Report-only mode for development
        
        # Add CSP-related security headers
        response.headers['X-Content-Security-Policy'] = csp_header
        
        return response
    
    def build_csp_header(self, directives: Dict[str, List[str]]) -> str:
        """Build CSP header string from directives"""
        csp_parts = []
        
        for directive, sources in directives.items():
            if sources:
                # Handle special cases
                if directive == 'upgrade-insecure-requests' and sources:
                    csp_parts.append(directive)
                else:
                    # Join sources with space
                    sources_str = ' '.join(sources)
                    csp_parts.append(f"{directive} {sources_str}")
        
        return '; '.join(csp_parts)
    
    def log_csp_request(self):
        """Log CSP-related request information for debugging"""
        if current_app.config.get('DEBUG'):
            logger.debug(f"CSP Request: {request.method} {request.path}")
            logger.debug(f"CSP User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
            logger.debug(f"CSP Referer: {request.headers.get('Referer', 'None')}")
    
    def validate_csp_directives(self, directives: Dict[str, List[str]]) -> bool:
        """Validate CSP directives for security"""
        required_directives = ['default-src', 'script-src', 'style-src']
        
        for directive in required_directives:
            if directive not in directives:
                logger.warning(f"Missing required CSP directive: {directive}")
                return False
        
        # Check for dangerous directives
        dangerous_values = ["'unsafe-eval'", "'unsafe-inline'"]
        for directive, sources in directives.items():
            if directive in ['script-src', 'style-src']:
                for value in dangerous_values:
                    if value in sources:
                        logger.warning(f"Potentially dangerous CSP value in {directive}: {value}")
        
        return True
    
    def get_csp_report_uri(self) -> Optional[str]:
        """Get CSP report URI if configured"""
        try:
            return current_app.config.get('CSP_REPORT_URI')
        except RuntimeError:
            # Working outside of application context
            return None
    
    def add_csp_reporting(self, directives: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Add CSP reporting directive if configured"""
        report_uri = self.get_csp_report_uri()
        if report_uri:
            directives['report-uri'] = [report_uri]
            directives['report-to'] = [report_uri]
        
        return directives
    
    def get_csp_nonce(self) -> str:
        """Generate CSP nonce for inline scripts/styles"""
        if not hasattr(g, 'csp_nonce'):
            import secrets
            g.csp_nonce = secrets.token_urlsafe(16)
        return g.csp_nonce
    
    def add_nonce_support(self, directives: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Add nonce support to CSP directives"""
        try:
            nonce = self.get_csp_nonce()
            
            # Add nonce to script-src and style-src
            for directive in ['script-src', 'style-src']:
                if directive in directives:
                    directives[directive].append(f"'nonce-{nonce}'")
        except RuntimeError:
            # Working outside of application context, skip nonce
            pass
        
        return directives

def init_csp(app):
    """Initialize CSP middleware for Flask application"""
    csp_middleware = CSPMiddleware()
    csp_middleware.init_app(app)
    
    # Validate CSP configuration
    csp_directives = app.config.get('CSP_DIRECTIVES', {})
    if not csp_middleware.validate_csp_directives(csp_directives):
        logger.warning("CSP configuration validation failed")
    
    # Add reporting if configured
    csp_directives = csp_middleware.add_csp_reporting(csp_directives)
    
    # Add nonce support
    csp_directives = csp_middleware.add_nonce_support(csp_directives)
    
    # Update app config with enhanced directives
    app.config['CSP_DIRECTIVES'] = csp_directives
    
    logger.info("CSP middleware initialized successfully")
    
    return csp_middleware
