"""
Security Headers Middleware
Provides comprehensive security headers for all application responses
"""

from flask import Response, current_app, request
from typing import Dict, Any, Optional
import re

class SecurityHeaders:
    """Security headers middleware for comprehensive protection"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security headers middleware with Flask app"""
        app.after_request(self.add_security_headers)
        
        # Store security headers configuration
        app.security_headers = self
    
    def add_security_headers(self, response: Response) -> Response:
        """
        Add comprehensive security headers to all responses
        
        Args:
            response: Flask response object
            
        Returns:
            Response with security headers added
        """
        # Basic security headers
        self._add_basic_security_headers(response)
        
        # Content Security Policy
        self._add_csp_headers(response)
        
        # HTTPS enforcement
        self._add_https_headers(response)
        
        # Privacy and permissions
        self._add_privacy_headers(response)
        
        # Remove server information
        self._remove_server_info(response)
        
        return response
    
    def _add_basic_security_headers(self, response: Response):
        """Add basic security headers"""
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # XSS protection (deprecated but still used by some browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent browsers from detecting the MIME type
        response.headers['X-Download-Options'] = 'noopen'
        
        # Disable IE compatibility mode
        response.headers['X-UA-Compatible'] = 'IE=edge'
    
    def _add_csp_headers(self, response: Response):
        """Add Content Security Policy headers"""
        # Base CSP policy
        csp_policy = [
            # Default source restrictions
            "default-src 'self'",
            
            # Script sources - allow inline scripts for React/JS frameworks
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.clarity.ms",
            
            # Style sources - allow inline styles and Google Fonts
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
            
            # Font sources
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:",
            
            # Image sources
            "img-src 'self' data: https: blob:",
            
            # Connect sources for API calls
            "connect-src 'self' https://www.google-analytics.com https://www.clarity.ms",
            
            # Media sources
            "media-src 'self'",
            
            # Object sources - block plugins
            "object-src 'none'",
            
            # Frame sources - block frames
            "frame-src 'none'",
            
            # Frame ancestors - prevent embedding
            "frame-ancestors 'none'",
            
            # Base URI restriction
            "base-uri 'self'",
            
            # Form action restriction
            "form-action 'self'",
            
            # Upgrade insecure requests
            "upgrade-insecure-requests"
        ]
        
        # Add analytics domains if enabled
        if current_app.config.get('ENABLE_ANALYTICS', False):
            csp_policy.extend([
                "script-src https://www.googletagmanager.com https://www.google-analytics.com",
                "connect-src https://www.google-analytics.com https://analytics.google.com"
            ])
        
        # Add payment domains if enabled
        if current_app.config.get('ENABLE_PAYMENTS', False):
            csp_policy.extend([
                "script-src https://js.stripe.com https://checkout.stripe.com",
                "frame-src https://js.stripe.com https://hooks.stripe.com",
                "connect-src https://api.stripe.com"
            ])
        
        # Join policy directives
        csp_string = "; ".join(csp_policy)
        
        # Add CSP header
        response.headers['Content-Security-Policy'] = csp_string
        
        # Add CSP report-only header for monitoring (optional)
        if current_app.config.get('CSP_REPORT_ONLY', False):
            response.headers['Content-Security-Policy-Report-Only'] = csp_string
    
    def _add_https_headers(self, response: Response):
        """Add HTTPS enforcement headers"""
        # Strict Transport Security
        hsts_policy = [
            "max-age=31536000",  # 1 year
            "includeSubDomains",
            "preload"
        ]
        
        # Add HSTS header if HTTPS
        if request.is_secure or current_app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = "; ".join(hsts_policy)
        
        # Upgrade insecure requests (already in CSP, but explicit header for older browsers)
        if request.is_secure:
            response.headers['Upgrade-Insecure-Requests'] = '1'
    
    def _add_privacy_headers(self, response: Response):
        """Add privacy and permissions headers"""
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (formerly Feature Policy)
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "speaker=()",
            "fullscreen=()",
            "display-capture=()",
            "encrypted-media=()",
            "picture-in-picture=()",
            "publickey-credentials-get=()",
            "screen-wake-lock=()",
            "web-share=()",
            "xr-spatial-tracking=()"
        ]
        
        response.headers['Permissions-Policy'] = ", ".join(permissions_policy)
        
        # Cross-Origin Embedder Policy
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cross-Origin Opener Policy
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # Cross-Origin Resource Policy
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    
    def _remove_server_info(self, response: Response):
        """Remove server information headers"""
        # Remove server information
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        response.headers.pop('X-AspNet-Version', None)
        response.headers.pop('X-AspNetMvc-Version', None)
    
    def get_custom_headers(self, endpoint: str = None) -> Dict[str, str]:
        """
        Get custom headers for specific endpoints
        
        Args:
            endpoint: Specific endpoint name
            
        Returns:
            Dictionary of custom headers
        """
        custom_headers = {}
        
        # Assessment-specific headers
        if endpoint and 'assessment' in endpoint:
            custom_headers.update({
                'X-Assessment-Security': 'enabled',
                'X-Content-Type': 'application/json'
            })
        
        # API-specific headers
        if endpoint and endpoint.startswith('api.'):
            custom_headers.update({
                'X-API-Version': current_app.config.get('API_VERSION', '1.0'),
                'X-API-Deprecation': 'false'
            })
        
        return custom_headers

def configure_secure_cookies(app):
    """
    Configure secure cookie settings for the Flask application
    
    Args:
        app: Flask application instance
    """
    app.config.update(
        # Session cookie security
        SESSION_COOKIE_SECURE=True,  # HTTPS only
        SESSION_COOKIE_HTTPONLY=True,  # No JavaScript access
        SESSION_COOKIE_SAMESITE='Strict',  # CSRF protection
        SESSION_COOKIE_NAME='mingus_session',
        
        # Session lifetime
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
        
        # Additional cookie security
        SESSION_COOKIE_PATH='/',
        SESSION_COOKIE_DOMAIN=None,  # Current domain only
        
        # Cookie encryption
        SESSION_COOKIE_USE_SIGNER=True,
        
        # Session configuration
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR='/tmp/flask_session',
        SESSION_FILE_THRESHOLD=500
    )
    
    # Set secure headers for cookie management
    app.config['SECURE_HEADERS'] = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'
    }

def add_security_headers_to_response(response: Response, endpoint: str = None) -> Response:
    """
    Utility function to add security headers to a specific response
    
    Args:
        response: Flask response object or dict
        endpoint: Endpoint name for custom headers
        
    Returns:
        Response with security headers added
    """
    # Convert dict to Response if needed
    if isinstance(response, dict):
        from flask import jsonify
        response = jsonify(response)
    
    security_headers = SecurityHeaders()
    security_headers.add_security_headers(response)
    
    # Add custom headers if endpoint specified
    if endpoint:
        custom_headers = security_headers.get_custom_headers(endpoint)
        for header, value in custom_headers.items():
            response.headers[header] = value
    
    return response

def validate_security_headers(response: Response) -> Dict[str, Any]:
    """
    Validate that all required security headers are present
    
    Args:
        response: Flask response object
        
    Returns:
        Dictionary with validation results
    """
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Content-Security-Policy',
        'Referrer-Policy',
        'Permissions-Policy'
    ]
    
    validation_results = {
        'missing_headers': [],
        'present_headers': [],
        'is_secure': True
    }
    
    for header in required_headers:
        if header in response.headers:
            validation_results['present_headers'].append(header)
        else:
            validation_results['missing_headers'].append(header)
            validation_results['is_secure'] = False
    
    return validation_results
