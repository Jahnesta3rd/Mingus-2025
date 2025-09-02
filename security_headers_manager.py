#!/usr/bin/env python3
"""
Complete Security Headers Manager for Mingus Financial App
Production-grade security headers implementation with Flask-Talisman
"""

import os
import logging
import secrets
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Flask, request, Response, current_app, g
from flask_talisman import Talisman, ALLOW_FROM
import talisman

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers"""
    environment: str = 'production'
    
    # HSTS Configuration
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # X-Frame-Options Configuration
    x_frame_options: str = 'DENY'
    frame_ancestors: str = "'none'"
    
    # Content Security Policy
    csp_enabled: bool = True
    csp_report_only: bool = False
    csp_report_uri: Optional[str] = None
    csp_report_to: Optional[str] = None
    
    # Additional Security Headers
    x_content_type_options: str = 'nosniff'
    x_xss_protection: str = '1; mode=block'
    referrer_policy: str = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    permissions_policy: Dict[str, str] = field(default_factory=lambda: {
        'geolocation': '()',
        'microphone': '()',
        'camera': '()',
        'payment': '(self)',
        'usb': '()',
        'magnetometer': '()',
        'gyroscope': '()',
        'accelerometer': '()',
        'ambient-light-sensor': '()',
        'autoplay': '()',
        'encrypted-media': '()',
        'fullscreen': '(self)',
        'picture-in-picture': '()',
        'publickey-credentials-get': '()',
        'screen-wake-lock': '()',
        'sync-xhr': '()',
        'web-share': '()',
        'xr-spatial-tracking': '()'
    })
    
    # Feature Policy (legacy)
    feature_policy: Dict[str, str] = field(default_factory=lambda: {
        'geolocation': "'none'",
        'microphone': "'none'",
        'camera': "'none'",
        'payment': "'self'",
        'usb': "'none'",
        'magnetometer': "'none'",
        'gyroscope': "'none'",
        'accelerometer': "'none'"
    })
    
    # Cross-Origin Headers
    cross_origin_opener_policy: str = 'same-origin'
    cross_origin_embedder_policy: str = 'require-corp'
    cross_origin_resource_policy: str = 'same-origin'
    
    # Additional Headers
    x_download_options: str = 'noopen'
    x_permitted_cross_domain_policies: str = 'none'
    x_dns_prefetch_control: str = 'off'
    
    # Expect-CT (Certificate Transparency)
    expect_ct_enabled: bool = True
    expect_ct_max_age: int = 86400  # 24 hours
    expect_ct_enforce: bool = True
    expect_ct_report_uri: Optional[str] = None

class SecurityHeadersManager:
    """Manages comprehensive security headers for Flask applications"""
    
    def __init__(self, app: Flask, config: Optional[SecurityHeadersConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        self.talisman = None
        self._initialize_talisman()
        self._register_middleware()
        
        logger.info(f"Security Headers Manager initialized for {self.config.environment} environment")
    
    def _get_default_config(self) -> SecurityHeadersConfig:
        """Get default configuration based on environment"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return SecurityHeadersConfig(
                environment='production',
                hsts_enabled=True,
                hsts_max_age=31536000,  # 1 year
                hsts_include_subdomains=True,
                hsts_preload=True,
                x_frame_options='DENY',
                frame_ancestors="'none'",
                csp_enabled=True,
                csp_report_only=False,
                csp_report_uri=os.getenv('CSP_REPORT_URI'),
                csp_report_to=os.getenv('CSP_REPORT_TO'),
                expect_ct_enabled=True,
                expect_ct_report_uri=os.getenv('EXPECT_CT_REPORT_URI')
            )
        elif env == 'staging':
            return SecurityHeadersConfig(
                environment='staging',
                hsts_enabled=True,
                hsts_max_age=31536000,  # 1 year
                hsts_include_subdomains=True,
                hsts_preload=False,  # No preload for staging
                x_frame_options='DENY',
                frame_ancestors="'none'",
                csp_enabled=True,
                csp_report_only=True,  # Report-only mode
                csp_report_uri=os.getenv('CSP_REPORT_URI')
            )
        else:
            return SecurityHeadersConfig(
                environment='development',
                hsts_enabled=False,  # Disabled for development
                x_frame_options='SAMEORIGIN',  # Allow same-origin frames
                frame_ancestors="'self'",
                csp_enabled=True,
                csp_report_only=True,  # Report-only mode
                x_dns_prefetch_control='on'  # Enable for development
            )
    
    def _initialize_talisman(self):
        """Initialize Flask-Talisman with security headers"""
        # Build HSTS header
        hsts_header = self._build_hsts_header()
        
        # Build CSP header
        csp_header = self._build_csp_header()
        
        # Build Permissions Policy header
        permissions_policy_header = self._build_permissions_policy_header()
        
        # Build Feature Policy header (legacy)
        feature_policy_header = self._build_feature_policy_header()
        
        # Build Expect-CT header
        expect_ct_header = self._build_expect_ct_header()
        
        # Configure Talisman
        talisman_config = {
            'force_https': self.config.hsts_enabled,
            'force_https_permanent': self.config.hsts_enabled,
            'strict_transport_security': self.config.hsts_enabled,
            'strict_transport_security_max_age': self.config.hsts_max_age,
            'strict_transport_security_include_subdomains': self.config.hsts_include_subdomains,
            'strict_transport_security_preload': self.config.hsts_preload,
            'frame_options': self.config.x_frame_options,
            'content_security_policy': csp_header if self.config.csp_enabled else None,
            'content_security_policy_report_only': self.config.csp_report_only,
            'content_security_policy_report_uri': self.config.csp_report_uri,
            'content_security_policy_report_to': self.config.csp_report_to,
            'x_content_type_options': self.config.x_content_type_options,
            'x_xss_protection': self.config.x_xss_protection,
            'referrer_policy': self.config.referrer_policy,
            'permissions_policy': permissions_policy_header,
            'feature_policy': feature_policy_header,
            'cross_origin_opener_policy': self.config.cross_origin_opener_policy,
            'cross_origin_embedder_policy': self.config.cross_origin_embedder_policy,
            'cross_origin_resource_policy': self.config.cross_origin_resource_policy,
            'expect_ct': expect_ct_header if self.config.expect_ct_enabled else None,
            'expect_ct_max_age': self.config.expect_ct_max_age,
            'expect_ct_enforce': self.config.expect_ct_enforce,
            'expect_ct_report_uri': self.config.expect_ct_report_uri
        }
        
        # Initialize Talisman
        self.talisman = Talisman(
            self.app,
            **talisman_config,
            content_security_policy_nonce_in=['script-src', 'style-src']
        )
        
        # Add custom headers
        self._add_custom_headers()
    
    def _build_hsts_header(self) -> str:
        """Build HSTS header string"""
        if not self.config.hsts_enabled:
            return None
        
        parts = [f"max-age={self.config.hsts_max_age}"]
        
        if self.config.hsts_include_subdomains:
            parts.append("includeSubDomains")
        
        if self.config.hsts_preload:
            parts.append("preload")
        
        return "; ".join(parts)
    
    def _build_csp_header(self) -> str:
        """Build CSP header string"""
        if not self.config.csp_enabled:
            return None
        
        # Import CSP configuration
        try:
            from csp_config import build_csp_header
            return build_csp_header(self.config.environment)
        except ImportError:
            # Fallback CSP if csp_config is not available
            return self._build_fallback_csp()
    
    def _build_fallback_csp(self) -> str:
        """Build fallback CSP header"""
        directives = [
            "default-src 'self'",
            "script-src 'self' 'nonce-{nonce}' https://js.stripe.com https://checkout.stripe.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: https: https://stripe.com https://checkout.stripe.com",
            "font-src 'self' https://fonts.gstatic.com data:",
            "connect-src 'self' https://api.stripe.com https://js.stripe.com",
            "frame-src 'self' https://js.stripe.com https://hooks.stripe.com https://checkout.stripe.com",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self' https://api.stripe.com https://checkout.stripe.com",
            "upgrade-insecure-requests"
        ]
        
        csp_string = "; ".join(directives)
        
        if self.config.csp_report_uri:
            csp_string += f"; report-uri {self.config.csp_report_uri}"
        
        if self.config.csp_report_to:
            csp_string += f"; report-to {self.config.csp_report_to}"
        
        return csp_string
    
    def _build_permissions_policy_header(self) -> str:
        """Build Permissions Policy header"""
        policies = []
        for feature, value in self.config.permissions_policy.items():
            policies.append(f"{feature}={value}")
        
        return ", ".join(policies)
    
    def _build_feature_policy_header(self) -> str:
        """Build Feature Policy header (legacy)"""
        policies = []
        for feature, value in self.config.feature_policy.items():
            policies.append(f"{feature} {value}")
        
        return "; ".join(policies)
    
    def _build_expect_ct_header(self) -> str:
        """Build Expect-CT header"""
        if not self.config.expect_ct_enabled:
            return None
        
        parts = [f"max-age={self.config.expect_ct_max_age}"]
        
        if self.config.expect_ct_enforce:
            parts.append("enforce")
        
        if self.config.expect_ct_report_uri:
            parts.append(f'report-uri="{self.config.expect_ct_report_uri}"')
        
        return ", ".join(parts)
    
    def _add_custom_headers(self):
        """Add custom security headers"""
        @self.app.after_request
        def add_custom_headers(response: Response) -> Response:
            # Add X-Download-Options
            response.headers['X-Download-Options'] = self.config.x_download_options
            
            # Add X-Permitted-Cross-Domain-Policies
            response.headers['X-Permitted-Cross-Domain-Policies'] = self.config.x_permitted_cross_domain_policies
            
            # Add X-DNS-Prefetch-Control
            response.headers['X-DNS-Prefetch-Control'] = self.config.x_dns_prefetch_control
            
            # Add Server header (remove or customize)
            if 'Server' in response.headers:
                del response.headers['Server']
            
            # Add custom security headers for financial apps
            response.headers['X-Financial-App'] = 'Mingus'
            response.headers['X-Security-Level'] = self.config.environment
            
            return response
    
    def _register_middleware(self):
        """Register security middleware"""
        @self.app.before_request
        def security_checks():
            # Generate nonce for CSP
            g.csp_nonce = secrets.token_urlsafe(32)
            
            # Security checks
            self._check_https_redirect()
            self._check_security_headers()
    
    def _check_https_redirect(self):
        """Check and redirect to HTTPS if needed"""
        if (self.config.hsts_enabled and 
            not request.is_secure and 
            not request.headers.get('X-Forwarded-Proto', 'http').startswith('https')):
            
            # Don't redirect for health checks or API endpoints
            if not (request.path.startswith('/health') or request.path.startswith('/api/')):
                logger.warning(f"Insecure request detected: {request.url}")
    
    def _check_security_headers(self):
        """Check if security headers are present"""
        # This is handled by Talisman, but we can add additional checks here
        pass
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get all security headers for documentation/testing"""
        headers = {
            'Strict-Transport-Security': self._build_hsts_header(),
            'X-Frame-Options': self.config.x_frame_options,
            'X-Content-Type-Options': self.config.x_content_type_options,
            'X-XSS-Protection': self.config.x_xss_protection,
            'Referrer-Policy': self.config.referrer_policy,
            'Permissions-Policy': self._build_permissions_policy_header(),
            'Feature-Policy': self._build_feature_policy_header(),
            'Cross-Origin-Opener-Policy': self.config.cross_origin_opener_policy,
            'Cross-Origin-Embedder-Policy': self.config.cross_origin_embedder_policy,
            'Cross-Origin-Resource-Policy': self.config.cross_origin_resource_policy,
            'X-Download-Options': self.config.x_download_options,
            'X-Permitted-Cross-Domain-Policies': self.config.x_permitted_cross_domain_policies,
            'X-DNS-Prefetch-Control': self.config.x_dns_prefetch_control
        }
        
        if self.config.csp_enabled:
            headers['Content-Security-Policy'] = self._build_csp_header()
        
        if self.config.expect_ct_enabled:
            headers['Expect-CT'] = self._build_expect_ct_header()
        
        # Remove None values
        return {k: v for k, v in headers.items() if v is not None}

class SecurityHeadersTester:
    """Test security headers implementation"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.test_results = []
    
    def test_all_headers(self, base_url: str = "http://localhost:5000") -> Dict:
        """Test all security headers"""
        import requests
        
        print("🔍 Testing Security Headers...")
        
        try:
            response = requests.get(base_url)
            
            # Test HSTS
            self._test_hsts_header(response)
            
            # Test X-Frame-Options
            self._test_frame_options(response)
            
            # Test CSP
            self._test_csp_header(response)
            
            # Test Additional Headers
            self._test_additional_headers(response)
            
            # Test Permissions Policy
            self._test_permissions_policy(response)
            
            return self._generate_report()
            
        except Exception as e:
            print(f"❌ Error testing headers: {e}")
            return {'error': str(e)}
    
    def _test_hsts_header(self, response: requests.Response):
        """Test HSTS header"""
        hsts_header = response.headers.get('Strict-Transport-Security')
        
        if hsts_header:
            self.test_results.append({
                'test': 'HSTS Header',
                'status': 'PASS',
                'details': f'HSTS header found: {hsts_header}'
            })
            
            # Check HSTS configuration
            if 'max-age=31536000' in hsts_header:
                self.test_results.append({
                    'test': 'HSTS Max Age',
                    'status': 'PASS',
                    'details': 'HSTS max-age set to 1 year'
                })
            else:
                self.test_results.append({
                    'test': 'HSTS Max Age',
                    'status': 'WARN',
                    'details': 'HSTS max-age should be 1 year minimum'
                })
            
            if 'includeSubDomains' in hsts_header:
                self.test_results.append({
                    'test': 'HSTS Include Subdomains',
                    'status': 'PASS',
                    'details': 'HSTS includes subdomains'
                })
            
            if 'preload' in hsts_header:
                self.test_results.append({
                    'test': 'HSTS Preload',
                    'status': 'PASS',
                    'details': 'HSTS preload enabled'
                })
        else:
            self.test_results.append({
                'test': 'HSTS Header',
                'status': 'WARN',
                'details': 'HSTS header not found'
            })
    
    def _test_frame_options(self, response: requests.Response):
        """Test X-Frame-Options and frame-ancestors"""
        x_frame_options = response.headers.get('X-Frame-Options')
        csp_header = response.headers.get('Content-Security-Policy', '')
        
        if x_frame_options == 'DENY':
            self.test_results.append({
                'test': 'X-Frame-Options',
                'status': 'PASS',
                'details': 'X-Frame-Options set to DENY'
            })
        else:
            self.test_results.append({
                'test': 'X-Frame-Options',
                'status': 'WARN',
                'details': f'X-Frame-Options: {x_frame_options}'
            })
        
        if 'frame-ancestors' in csp_header:
            self.test_results.append({
                'test': 'CSP Frame Ancestors',
                'status': 'PASS',
                'details': 'CSP frame-ancestors directive present'
            })
    
    def _test_csp_header(self, response: requests.Response):
        """Test Content Security Policy header"""
        csp_header = response.headers.get('Content-Security-Policy')
        csp_report_only = response.headers.get('Content-Security-Policy-Report-Only')
        
        if csp_header:
            self.test_results.append({
                'test': 'CSP Header',
                'status': 'PASS',
                'details': 'Content-Security-Policy header present'
            })
        elif csp_report_only:
            self.test_results.append({
                'test': 'CSP Header',
                'status': 'INFO',
                'details': 'CSP in report-only mode'
            })
        else:
            self.test_results.append({
                'test': 'CSP Header',
                'status': 'WARN',
                'details': 'No CSP header found'
            })
    
    def _test_additional_headers(self, response: requests.Response):
        """Test additional security headers"""
        additional_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, expected_value in additional_headers.items():
            actual_value = response.headers.get(header)
            if actual_value:
                if expected_value in actual_value:
                    self.test_results.append({
                        'test': f'{header}',
                        'status': 'PASS',
                        'details': f'{header}: {actual_value}'
                    })
                else:
                    self.test_results.append({
                        'test': f'{header}',
                        'status': 'WARN',
                        'details': f'{header}: {actual_value} (expected: {expected_value})'
                    })
            else:
                self.test_results.append({
                    'test': f'{header}',
                    'status': 'WARN',
                    'details': f'{header} header not found'
                })
    
    def _test_permissions_policy(self, response: requests.Response):
        """Test Permissions Policy header"""
        permissions_policy = response.headers.get('Permissions-Policy')
        
        if permissions_policy:
            self.test_results.append({
                'test': 'Permissions Policy',
                'status': 'PASS',
                'details': 'Permissions-Policy header present'
            })
            
            # Check for critical permissions
            critical_permissions = ['geolocation', 'microphone', 'camera']
            for permission in critical_permissions:
                if f'{permission}=()' in permissions_policy:
                    self.test_results.append({
                        'test': f'Permissions Policy - {permission}',
                        'status': 'PASS',
                        'details': f'{permission} permission blocked'
                    })
        else:
            self.test_results.append({
                'test': 'Permissions Policy',
                'status': 'WARN',
                'details': 'Permissions-Policy header not found'
            })
    
    def _generate_report(self) -> Dict:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'warnings': warning_tests,
                'score': round(score, 2)
            },
            'results': self.test_results
        }

# Utility functions
def get_security_headers_config(environment: str = None) -> SecurityHeadersConfig:
    """Get security headers configuration for environment"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    config = SecurityHeadersConfig()
    config.environment = environment
    
    if environment == 'production':
        config.hsts_enabled = True
        config.hsts_max_age = 31536000
        config.hsts_include_subdomains = True
        config.hsts_preload = True
        config.x_frame_options = 'DENY'
        config.frame_ancestors = "'none'"
        config.csp_report_only = False
    elif environment == 'staging':
        config.hsts_enabled = True
        config.hsts_preload = False
        config.x_frame_options = 'DENY'
        config.csp_report_only = True
    else:
        config.hsts_enabled = False
        config.x_frame_options = 'SAMEORIGIN'
        config.frame_ancestors = "'self'"
        config.csp_report_only = True
    
    return config

def test_security_headers(app: Flask, base_url: str = "http://localhost:5000") -> Dict:
    """Test security headers for Flask app"""
    tester = SecurityHeadersTester(app)
    return tester.test_all_headers(base_url)

# Example usage
if __name__ == "__main__":
    # Example Flask app setup
    app = Flask(__name__)
    
    # Initialize security headers manager
    security_manager = SecurityHeadersManager(app)
    
    # Test security headers
    results = test_security_headers(app)
    
    print("Security Headers Test Results:")
    print(f"Score: {results['summary']['score']}%")
    print(f"Passed: {results['summary']['passed']}/{results['summary']['total_tests']}")
    
    for result in results['results']:
        status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARN' else "❌"
        print(f"{status_icon} {result['test']}: {result['details']}")
