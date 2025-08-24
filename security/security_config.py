#!/usr/bin/env python3
"""
MINGUS Security Configuration
Environment-specific security configurations for financial wellness application
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from security.headers import SecurityConfig

@dataclass
class MINGUSSecurityConfig:
    """Comprehensive security configuration for MINGUS application"""
    
    # Environment
    environment: str = "development"
    
    # Application Security
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'))
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "Lax"
    session_lifetime: int = 3600  # 1 hour
    
    # Database Security
    database_ssl_mode: str = "require"
    database_connection_pool_size: int = 20
    database_connection_timeout: int = 10
    
    # Authentication Security
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    password_history_count: int = 5
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    
    # API Security
    api_rate_limit: int = 100  # requests per minute
    api_rate_limit_window: int = 60  # seconds
    api_key_required: bool = True
    api_versioning: bool = True
    
    # File Upload Security
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.pdf', '.jpg', '.jpeg', '.png'])
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    scan_uploads: bool = True
    
    # Encryption
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    
    # Logging Security
    log_sensitive_data: bool = False
    log_ip_addresses: bool = True
    log_user_agents: bool = True
    log_authentication_events: bool = True
    log_financial_events: bool = True
    
    # Monitoring and Alerting
    security_monitoring_enabled: bool = True
    alert_on_suspicious_activity: bool = True
    alert_on_failed_logins: bool = True
    alert_on_data_breach: bool = True

class SecurityConfigFactory:
    """Factory for creating environment-specific security configurations"""
    
    @staticmethod
    def create_config(environment: str = None) -> MINGUSSecurityConfig:
        """Create security configuration for specified environment"""
        if environment is None:
            environment = os.getenv('FLASK_ENV', 'development')
        
        if environment == 'production':
            return SecurityConfigFactory._create_production_config()
        elif environment == 'staging':
            return SecurityConfigFactory._create_staging_config()
        elif environment == 'testing':
            return SecurityConfigFactory._create_testing_config()
        else:
            return SecurityConfigFactory._create_development_config()
    
    @staticmethod
    def _create_production_config() -> MINGUSSecurityConfig:
        """Create production security configuration"""
        return MINGUSSecurityConfig(
            environment='production',
            secret_key=os.getenv('SECRET_KEY'),
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            session_lifetime=1800,  # 30 minutes for financial app
            
            # Database Security
            database_ssl_mode="require",
            database_connection_pool_size=30,
            database_connection_timeout=5,
            
            # Authentication Security
            password_min_length=16,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_digits=True,
            password_require_special=True,
            password_history_count=10,
            max_login_attempts=3,
            lockout_duration=1800,  # 30 minutes
            
            # API Security
            api_rate_limit=50,  # Stricter for production
            api_rate_limit_window=60,
            api_key_required=True,
            api_versioning=True,
            
            # File Upload Security
            allowed_file_extensions=['.pdf', '.jpg', '.jpeg', '.png'],
            max_file_size=5 * 1024 * 1024,  # 5MB
            scan_uploads=True,
            
            # Encryption
            encryption_algorithm="AES-256-GCM",
            key_rotation_days=30,  # More frequent rotation
            
            # Logging Security
            log_sensitive_data=False,
            log_ip_addresses=True,
            log_user_agents=True,
            log_authentication_events=True,
            log_financial_events=True,
            
            # Monitoring and Alerting
            security_monitoring_enabled=True,
            alert_on_suspicious_activity=True,
            alert_on_failed_logins=True,
            alert_on_data_breach=True
        )
    
    @staticmethod
    def _create_staging_config() -> MINGUSSecurityConfig:
        """Create staging security configuration"""
        return MINGUSSecurityConfig(
            environment='staging',
            secret_key=os.getenv('SECRET_KEY', 'staging-secret-key'),
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Lax",
            session_lifetime=3600,  # 1 hour
            
            # Database Security
            database_ssl_mode="require",
            database_connection_pool_size=20,
            database_connection_timeout=10,
            
            # Authentication Security
            password_min_length=12,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_digits=True,
            password_require_special=True,
            password_history_count=5,
            max_login_attempts=5,
            lockout_duration=900,  # 15 minutes
            
            # API Security
            api_rate_limit=100,
            api_rate_limit_window=60,
            api_key_required=True,
            api_versioning=True,
            
            # File Upload Security
            allowed_file_extensions=['.pdf', '.jpg', '.jpeg', '.png'],
            max_file_size=10 * 1024 * 1024,  # 10MB
            scan_uploads=True,
            
            # Encryption
            encryption_algorithm="AES-256-GCM",
            key_rotation_days=90,
            
            # Logging Security
            log_sensitive_data=False,
            log_ip_addresses=True,
            log_user_agents=True,
            log_authentication_events=True,
            log_financial_events=True,
            
            # Monitoring and Alerting
            security_monitoring_enabled=True,
            alert_on_suspicious_activity=True,
            alert_on_failed_logins=True,
            alert_on_data_breach=True
        )
    
    @staticmethod
    def _create_testing_config() -> MINGUSSecurityConfig:
        """Create testing security configuration"""
        return MINGUSSecurityConfig(
            environment='testing',
            secret_key='test-secret-key',
            session_cookie_secure=False,
            session_cookie_httponly=True,
            session_cookie_samesite="Lax",
            session_lifetime=3600,
            
            # Database Security
            database_ssl_mode="prefer",
            database_connection_pool_size=5,
            database_connection_timeout=30,
            
            # Authentication Security
            password_min_length=8,
            password_require_uppercase=False,
            password_require_lowercase=False,
            password_require_digits=False,
            password_require_special=False,
            password_history_count=1,
            max_login_attempts=10,
            lockout_duration=60,  # 1 minute
            
            # API Security
            api_rate_limit=1000,
            api_rate_limit_window=60,
            api_key_required=False,
            api_versioning=False,
            
            # File Upload Security
            allowed_file_extensions=['.pdf', '.jpg', '.jpeg', '.png', '.txt'],
            max_file_size=1024 * 1024,  # 1MB
            scan_uploads=False,
            
            # Encryption
            encryption_algorithm="AES-128-GCM",
            key_rotation_days=365,  # No rotation in testing
            
            # Logging Security
            log_sensitive_data=True,  # Allow for testing
            log_ip_addresses=True,
            log_user_agents=True,
            log_authentication_events=True,
            log_financial_events=True,
            
            # Monitoring and Alerting
            security_monitoring_enabled=False,
            alert_on_suspicious_activity=False,
            alert_on_failed_logins=False,
            alert_on_data_breach=False
        )
    
    @staticmethod
    def _create_development_config() -> MINGUSSecurityConfig:
        """Create development security configuration"""
        return MINGUSSecurityConfig(
            environment='development',
            secret_key='dev-secret-key-change-in-production',
            session_cookie_secure=False,
            session_cookie_httponly=True,
            session_cookie_samesite="Lax",
            session_lifetime=7200,  # 2 hours for development
            
            # Database Security
            database_ssl_mode="prefer",
            database_connection_pool_size=10,
            database_connection_timeout=30,
            
            # Authentication Security
            password_min_length=8,
            password_require_uppercase=False,
            password_require_lowercase=False,
            password_require_digits=False,
            password_require_special=False,
            password_history_count=1,
            max_login_attempts=10,
            lockout_duration=300,  # 5 minutes
            
            # API Security
            api_rate_limit=1000,
            api_rate_limit_window=60,
            api_key_required=False,
            api_versioning=False,
            
            # File Upload Security
            allowed_file_extensions=['.pdf', '.jpg', '.jpeg', '.png', '.txt'],
            max_file_size=10 * 1024 * 1024,  # 10MB
            scan_uploads=False,
            
            # Encryption
            encryption_algorithm="AES-128-GCM",
            key_rotation_days=365,  # No rotation in development
            
            # Logging Security
            log_sensitive_data=True,  # Allow for debugging
            log_ip_addresses=True,
            log_user_agents=True,
            log_authentication_events=True,
            log_financial_events=True,
            
            # Monitoring and Alerting
            security_monitoring_enabled=False,
            alert_on_suspicious_activity=False,
            alert_on_failed_logins=False,
            alert_on_data_breach=False
        )

def get_security_headers_config(environment: str = None) -> SecurityConfig:
    """Get security headers configuration for specified environment"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    if environment == 'production':
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
                "https://js.stripe.com",
                "https://checkout.stripe.com",
                "https://www.google-analytics.com",
                "https://www.googletagmanager.com",
                "https://clarity.microsoft.com"
            ],
            csp_style_src=[
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net"
            ],
            csp_connect_src=[
                "'self'",
                "https://api.stripe.com",
                "https://js.stripe.com",
                "https://www.google-analytics.com",
                "https://analytics.google.com",
                "https://clarity.microsoft.com",
                "https://c.clarity.ms"
            ],
            csp_frame_src=[
                "'self'",
                "https://js.stripe.com",
                "https://hooks.stripe.com",
                "https://checkout.stripe.com"
            ],
            csp_form_action=[
                "'self'",
                "https://api.stripe.com",
                "https://checkout.stripe.com"
            ],
            csp_upgrade_insecure_requests=True,
            csp_block_all_mixed_content=True,
            x_frame_options="DENY",
            referrer_policy="strict-origin-when-cross-origin",
            expect_ct=os.getenv('EXPECT_CT_HEADER', 'max-age=86400, enforce, report-uri="https://your-domain.com/ct-report"')
        )
    
    elif environment == 'staging':
        return SecurityConfig(
            environment='staging',
            enable_hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=False,  # Don't preload in staging
            csp_report_only=False,
            csp_script_src=[
                "'self'",
                "'nonce-{nonce}'",
                "https://js.stripe.com",
                "https://checkout.stripe.com"
            ],
            csp_style_src=[
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com"
            ],
            csp_connect_src=[
                "'self'",
                "https://api.stripe.com",
                "https://js.stripe.com"
            ],
            csp_frame_src=[
                "'self'",
                "https://js.stripe.com",
                "https://hooks.stripe.com"
            ],
            csp_form_action=[
                "'self'",
                "https://api.stripe.com"
            ],
            csp_upgrade_insecure_requests=True,
            csp_block_all_mixed_content=True,
            x_frame_options="DENY",
            referrer_policy="strict-origin-when-cross-origin"
        )
    
    else:  # Development and Testing
        return SecurityConfig(
            environment=environment,
            enable_hsts=False,  # Disable HSTS in development
            csp_report_only=True,  # Report-only mode
            csp_script_src=[
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # Allow eval for development tools
                "https://js.stripe.com"
            ],
            csp_style_src=[
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com"
            ],
            csp_connect_src=[
                "'self'",
                "https://api.stripe.com",
                "https://js.stripe.com",
                "ws://localhost:*",  # Allow WebSocket connections
                "wss://localhost:*"
            ],
            csp_upgrade_insecure_requests=False,  # Allow HTTP
            csp_block_all_mixed_content=False,
            x_frame_options="SAMEORIGIN",  # Less restrictive
            referrer_policy="no-referrer-when-downgrade"
        )

def validate_security_config(config: MINGUSSecurityConfig) -> List[str]:
    """Validate security configuration and return list of issues"""
    issues = []
    
    # Validate secret key
    if config.environment == 'production' and config.secret_key == 'dev-secret-key-change-in-production':
        issues.append("Production secret key must be set via environment variable")
    
    if len(config.secret_key) < 32:
        issues.append("Secret key should be at least 32 characters long")
    
    # Validate password requirements
    if config.password_min_length < 8:
        issues.append("Password minimum length should be at least 8 characters")
    
    if config.environment == 'production' and config.password_min_length < 12:
        issues.append("Production password minimum length should be at least 12 characters")
    
    # Validate session settings
    if config.environment == 'production' and not config.session_cookie_secure:
        issues.append("Production sessions must use secure cookies")
    
    # Validate rate limiting
    if config.api_rate_limit < 10:
        issues.append("API rate limit should be at least 10 requests per minute")
    
    # Validate file upload settings
    if config.max_file_size > 50 * 1024 * 1024:  # 50MB
        issues.append("Maximum file size should not exceed 50MB")
    
    return issues

def get_security_checklist(environment: str = None) -> Dict[str, List[str]]:
    """Get security checklist for specified environment"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    checklist = {
        'critical': [
            'HTTPS is enabled and enforced',
            'Strong secret key is configured',
            'Security headers are implemented',
            'Database connections use SSL',
            'Authentication is properly implemented',
            'Input validation is in place',
            'Output encoding is implemented',
            'Error handling doesn\'t leak sensitive information'
        ],
        'high': [
            'Rate limiting is configured',
            'File upload validation is implemented',
            'Session management is secure',
            'Password policy is enforced',
            'Logging is configured properly',
            'Monitoring and alerting is set up',
            'Backup and recovery procedures are in place'
        ],
        'medium': [
            'API versioning is implemented',
            'Key rotation is configured',
            'Security testing is automated',
            'Documentation is up to date',
            'Incident response plan is ready'
        ],
        'low': [
            'Security training is provided',
            'Regular security audits are scheduled',
            'Vendor security assessments are performed'
        ]
    }
    
    # Add environment-specific items
    if environment == 'production':
        checklist['critical'].extend([
            'Certificate Transparency is configured',
            'HSTS preload is enabled',
            'CSP is in enforced mode (not report-only)',
            'All third-party integrations are vetted'
        ])
        checklist['high'].extend([
            'Load balancer security is configured',
            'CDN security headers are set',
            'Database encryption at rest is enabled'
        ])
    
    return checklist 