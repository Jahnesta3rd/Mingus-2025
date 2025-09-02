#!/usr/bin/env python3
"""
CSP Configuration for Mingus Financial App
Comprehensive Content Security Policy configuration for all environments
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class CSPConfig:
    """CSP configuration for different environments"""
    environment: str
    report_only: bool = False
    report_uri: Optional[str] = None
    report_to: Optional[str] = None
    directives: Dict[str, List[str]] = field(default_factory=dict)

class CSPConfigurationManager:
    """Manages CSP configuration for different environments and integrations"""
    
    def __init__(self):
        self.configs = self._load_configurations()
    
    def _load_configurations(self) -> Dict[str, CSPConfig]:
        """Load CSP configurations for all environments"""
        return {
            'production': self._get_production_config(),
            'staging': self._get_staging_config(),
            'development': self._get_development_config(),
            'testing': self._get_testing_config()
        }
    
    def _get_production_config(self) -> CSPConfig:
        """Production CSP configuration - Strict security"""
        return CSPConfig(
            environment='production',
            report_only=False,
            report_uri=os.getenv('CSP_REPORT_URI', 'https://your-domain.com/csp-violation-report'),
            report_to=os.getenv('CSP_REPORT_TO', 'csp-endpoint'),
            directives={
                'default-src': ["'self'"],
                'script-src': [
                    "'self'",
                    "'nonce-{nonce}'",
                    # Stripe payment processing
                    "https://js.stripe.com",
                    "https://checkout.stripe.com",
                    # Google Analytics
                    "https://www.googletagmanager.com",
                    "https://www.google-analytics.com",
                    # Microsoft Clarity
                    "https://clarity.microsoft.com",
                    # Supabase (if needed)
                    "https://api.supabase.co"
                ],
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",  # Required for dynamic styles
                    # Google Fonts
                    "https://fonts.googleapis.com",
                    # CDN resources
                    "https://cdn.jsdelivr.net"
                ],
                'img-src': [
                    "'self'",
                    "data:",
                    "https:",
                    # Stripe images
                    "https://stripe.com",
                    "https://checkout.stripe.com",
                    # Analytics tracking pixels
                    "https://www.google-analytics.com",
                    "https://clarity.microsoft.com"
                ],
                'font-src': [
                    "'self'",
                    "data:",
                    # Google Fonts
                    "https://fonts.gstatic.com"
                ],
                'connect-src': [
                    "'self'",
                    # Stripe API
                    "https://api.stripe.com",
                    "https://js.stripe.com",
                    # Supabase API
                    "https://api.supabase.co",
                    # Twilio API
                    "https://api.twilio.com",
                    # Resend API
                    "https://api.resend.com",
                    # Plaid API
                    "https://api.plaid.com",
                    # Google Analytics
                    "https://www.google-analytics.com",
                    "https://analytics.google.com",
                    # Microsoft Clarity
                    "https://clarity.microsoft.com",
                    "https://c.clarity.ms"
                ],
                'frame-src': [
                    "'self'",
                    # Stripe iframes
                    "https://js.stripe.com",
                    "https://hooks.stripe.com",
                    "https://checkout.stripe.com"
                ],
                'object-src': ["'none'"],
                'media-src': ["'self'"],
                'manifest-src': ["'self'"],
                'worker-src': ["'self'"],
                'frame-ancestors': ["'none'"],
                'base-uri': ["'self'"],
                'form-action': [
                    "'self'",
                    # Stripe form submissions
                    "https://api.stripe.com",
                    "https://checkout.stripe.com"
                ],
                'upgrade-insecure-requests': [],
                'block-all-mixed-content': []
            }
        )
    
    def _get_staging_config(self) -> CSPConfig:
        """Staging CSP configuration - Report-only mode"""
        config = self._get_production_config()
        config.report_only = True
        config.environment = 'staging'
        return config
    
    def _get_development_config(self) -> CSPConfig:
        """Development CSP configuration - Permissive for debugging"""
        return CSPConfig(
            environment='development',
            report_only=True,  # Report-only mode for development
            report_uri=os.getenv('CSP_REPORT_URI'),
            directives={
                'default-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                'script-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "'unsafe-eval'",
                    # Stripe
                    "https://js.stripe.com",
                    "https://checkout.stripe.com",
                    # Google Analytics
                    "https://www.googletagmanager.com",
                    "https://www.google-analytics.com",
                    # Microsoft Clarity
                    "https://clarity.microsoft.com",
                    # CDNs for development
                    "https://cdn.jsdelivr.net",
                    "https://unpkg.com",
                    # Supabase
                    "https://api.supabase.co"
                ],
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "https://fonts.googleapis.com",
                    "https://cdn.jsdelivr.net",
                    "https://cdnjs.cloudflare.com"
                ],
                'img-src': [
                    "'self'",
                    "data:",
                    "https:",
                    "blob:"
                ],
                'font-src': [
                    "'self'",
                    "data:",
                    "https://fonts.gstatic.com"
                ],
                'connect-src': [
                    "'self'",
                    # All APIs
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
                    # Local development
                    "ws://localhost:*",
                    "wss://localhost:*"
                ],
                'frame-src': [
                    "'self'",
                    "https://js.stripe.com",
                    "https://hooks.stripe.com",
                    "https://checkout.stripe.com"
                ],
                'object-src': ["'none'"],
                'media-src': ["'self'"],
                'manifest-src': ["'self'"],
                'worker-src': ["'self'", "blob:"],
                'frame-ancestors': ["'self'"],
                'base-uri': ["'self'"],
                'form-action': [
                    "'self'",
                    "https://api.stripe.com",
                    "https://checkout.stripe.com"
                ]
            }
        )
    
    def _get_testing_config(self) -> CSPConfig:
        """Testing CSP configuration - Minimal restrictions"""
        return CSPConfig(
            environment='testing',
            report_only=True,
            directives={
                'default-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                'style-src': ["'self'", "'unsafe-inline'"],
                'img-src': ["'self'", "data:", "https:"],
                'font-src': ["'self'", "data:"],
                'connect-src': ["'self'"],
                'frame-src': ["'self'"],
                'object-src': ["'none'"],
                'media-src': ["'self'"],
                'manifest-src': ["'self'"],
                'worker-src': ["'self'"],
                'frame-ancestors': ["'self'"],
                'base-uri': ["'self'"],
                'form-action': ["'self'"]
            }
        )
    
    def get_config(self, environment: str = None) -> CSPConfig:
        """Get CSP configuration for specified environment"""
        if environment is None:
            environment = os.getenv('FLASK_ENV', 'development')
        
        return self.configs.get(environment, self.configs['development'])
    
    def build_csp_header(self, config: CSPConfig, nonce: str = None) -> str:
        """Build CSP header string from configuration"""
        directives = []
        
        for directive_name, sources in config.directives.items():
            if sources:
                # Replace nonce placeholder
                if nonce:
                    sources = [source.replace('{nonce}', nonce) for source in sources]
                directives.append(f"{directive_name} {' '.join(sources)}")
        
        # Add report directives
        if config.report_uri:
            directives.append(f"report-uri {config.report_uri}")
        
        if config.report_to:
            directives.append(f"report-to {config.report_to}")
        
        return "; ".join(directives)
    
    def get_integration_configs(self) -> Dict[str, Dict]:
        """Get configuration for specific integrations"""
        return {
            'stripe': {
                'domains': [
                    'js.stripe.com',
                    'checkout.stripe.com',
                    'hooks.stripe.com',
                    'api.stripe.com'
                ],
                'csp_directives': {
                    'script-src': [
                        "https://js.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    'frame-src': [
                        "https://js.stripe.com",
                        "https://hooks.stripe.com",
                        "https://checkout.stripe.com"
                    ],
                    'connect-src': [
                        "https://api.stripe.com",
                        "https://js.stripe.com"
                    ],
                    'form-action': [
                        "https://api.stripe.com",
                        "https://checkout.stripe.com"
                    ]
                }
            },
            'google_analytics': {
                'domains': [
                    'www.googletagmanager.com',
                    'www.google-analytics.com',
                    'analytics.google.com'
                ],
                'csp_directives': {
                    'script-src': [
                        "https://www.googletagmanager.com",
                        "https://www.google-analytics.com"
                    ],
                    'connect-src': [
                        "https://www.google-analytics.com",
                        "https://analytics.google.com"
                    ],
                    'img-src': [
                        "https://www.google-analytics.com"
                    ]
                }
            },
            'microsoft_clarity': {
                'domains': [
                    'clarity.microsoft.com',
                    'c.clarity.ms'
                ],
                'csp_directives': {
                    'script-src': [
                        "https://clarity.microsoft.com"
                    ],
                    'connect-src': [
                        "https://clarity.microsoft.com",
                        "https://c.clarity.ms"
                    ],
                    'img-src': [
                        "https://clarity.microsoft.com"
                    ]
                }
            },
            'supabase': {
                'domains': [
                    'api.supabase.co',
                    'supabase.co'
                ],
                'csp_directives': {
                    'script-src': [
                        "https://api.supabase.co"
                    ],
                    'connect-src': [
                        "https://api.supabase.co"
                    ]
                }
            },
            'twilio': {
                'domains': [
                    'api.twilio.com',
                    'twilio.com'
                ],
                'csp_directives': {
                    'connect-src': [
                        "https://api.twilio.com"
                    ]
                }
            },
            'resend': {
                'domains': [
                    'api.resend.com',
                    'resend.com'
                ],
                'csp_directives': {
                    'connect-src': [
                        "https://api.resend.com"
                    ]
                }
            },
            'plaid': {
                'domains': [
                    'api.plaid.com',
                    'plaid.com'
                ],
                'csp_directives': {
                    'connect-src': [
                        "https://api.plaid.com"
                    ]
                }
            }
        }
    
    def validate_config(self, config: CSPConfig) -> List[str]:
        """Validate CSP configuration and return warnings"""
        warnings = []
        
        # Check for unsafe directives in production
        if config.environment == 'production':
            unsafe_patterns = [
                "'unsafe-inline'",
                "'unsafe-eval'",
                "data:",
                "blob:"
            ]
            
            for directive_name, sources in config.directives.items():
                for pattern in unsafe_patterns:
                    if any(pattern in source for source in sources):
                        warnings.append(
                            f"Unsafe pattern '{pattern}' found in {directive_name} directive"
                        )
        
        # Check for missing required directives
        required_directives = ['default-src', 'script-src', 'style-src']
        for directive in required_directives:
            if directive not in config.directives:
                warnings.append(f"Missing required directive: {directive}")
        
        # Check for object-src
        if 'object-src' not in config.directives or "'none'" not in config.directives['object-src']:
            warnings.append("object-src should be set to 'none' for security")
        
        return warnings

# Global configuration manager instance
csp_config_manager = CSPConfigurationManager()

# Utility functions
def get_csp_config(environment: str = None) -> CSPConfig:
    """Get CSP configuration for environment"""
    return csp_config_manager.get_config(environment)

def build_csp_header(environment: str = None, nonce: str = None) -> str:
    """Build CSP header for environment"""
    config = get_csp_config(environment)
    return csp_config_manager.build_csp_header(config, nonce)

def validate_csp_config(environment: str = None) -> List[str]:
    """Validate CSP configuration for environment"""
    config = get_csp_config(environment)
    return csp_config_manager.validate_config(config)

# Example usage
if __name__ == "__main__":
    # Test configurations
    environments = ['production', 'staging', 'development', 'testing']
    
    for env in environments:
        print(f"\n=== {env.upper()} CSP Configuration ===")
        config = get_csp_config(env)
        header = build_csp_header(env)
        
        print(f"Environment: {config.environment}")
        print(f"Report Only: {config.report_only}")
        print(f"Report URI: {config.report_uri}")
        
        # Validate configuration
        warnings = validate_csp_config(env)
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
        else:
            print("✅ Configuration is valid")
        
        print(f"\nCSP Header (truncated):")
        print(f"{header[:100]}...")
