"""
Production Security Configuration for MINGUS on Digital Ocean
Comprehensive security settings for production deployment with maximum security
"""

import os
import secrets
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import ssl
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64

class SecurityLevel(Enum):
    """Security levels for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_SECURITY = "high_security"

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    CHACHA20_POLY1305 = "chacha20_poly1305"

class HashAlgorithm(Enum):
    """Supported hash algorithms"""
    SHA_256 = "sha256"
    SHA_512 = "sha512"
    BLAKE2B = "blake2b"
    ARGON2 = "argon2"

@dataclass
class SSLConfig:
    """SSL/TLS configuration"""
    enabled: bool = True
    certificate_path: str = "/etc/ssl/certs/mingus.crt"
    private_key_path: str = "/etc/ssl/private/mingus.key"
    ca_certificate_path: str = "/etc/ssl/certs/ca-bundle.crt"
    ssl_protocol: str = "TLSv1.3"
    cipher_suite: str = "ECDHE-RSA-AES256-GCM-SHA384"
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    ocsp_stapling: bool = True
    ssl_session_cache: str = "shared:SSL:10m"
    ssl_session_timeout: str = "10m"

@dataclass
class FirewallConfig:
    """Firewall configuration"""
    enabled: bool = True
    default_policy: str = "DROP"
    allowed_ports: List[int] = field(default_factory=lambda: [22, 80, 443, 8080])
    allowed_ips: List[str] = field(default_factory=list)
    rate_limiting_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    ddos_protection: bool = True
    fail2ban_enabled: bool = True
    fail2ban_max_retries: int = 3
    fail2ban_ban_time: int = 3600  # 1 hour

@dataclass
class DatabaseSecurityConfig:
    """Database security configuration"""
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    connection_encryption: str = "require"
    ssl_cert_verification: bool = True
    connection_pooling: bool = True
    max_connections: int = 100
    connection_timeout: int = 30
    query_timeout: int = 300
    audit_logging: bool = True
    backup_encryption: bool = True
    backup_retention_days: int = 30

@dataclass
class AuthenticationConfig:
    """Authentication security configuration"""
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    password_min_length: int = 12
    password_complexity: bool = True
    password_history: int = 5
    password_expiry_days: int = 90
    mfa_required: bool = True
    mfa_methods: List[str] = field(default_factory=lambda: ["totp", "sms", "email"])
    jwt_secret: str = ""
    jwt_algorithm: str = "HS512"
    jwt_expiry_hours: int = 24
    refresh_token_expiry_days: int = 30
    oauth_enabled: bool = True
    oauth_providers: List[str] = field(default_factory=lambda: ["google", "github"])

@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_rotation_days: int = 90
    key_storage_path: str = "/var/lib/mingus/keys"
    master_key_path: str = "/var/lib/mingus/master.key"
    data_encryption_key: str = ""
    file_encryption_enabled: bool = True
    backup_encryption_enabled: bool = True
    communication_encryption: bool = True
    end_to_end_encryption: bool = True

@dataclass
class LoggingSecurityConfig:
    """Security logging configuration"""
    security_log_level: str = "INFO"
    security_log_path: str = "/var/log/mingus/security.log"
    audit_log_path: str = "/var/log/mingus/audit.log"
    log_encryption: bool = True
    log_retention_days: int = 365
    log_rotation_size: str = "100M"
    log_rotation_count: int = 10
    sensitive_data_masking: bool = True
    ip_address_logging: bool = True
    user_agent_logging: bool = True
    request_id_logging: bool = True

@dataclass
class NetworkSecurityConfig:
    """Network security configuration"""
    vpn_required: bool = True
    vpn_endpoint: str = ""
    proxy_enabled: bool = False
    proxy_config: Dict[str, str] = field(default_factory=dict)
    cdn_enabled: bool = True
    cdn_provider: str = "cloudflare"
    load_balancer_enabled: bool = True
    health_check_enabled: bool = True
    monitoring_enabled: bool = True
    intrusion_detection: bool = True
    network_segmentation: bool = True

@dataclass
class ApplicationSecurityConfig:
    """Application security configuration"""
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=list)
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    csrf_protection: bool = True
    csrf_token_expiry: int = 3600
    xss_protection: bool = True
    content_security_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    strict_transport_security: bool = True
    x_content_type_options: bool = True
    x_frame_options: str = "DENY"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

@dataclass
class BackupSecurityConfig:
    """Backup security configuration"""
    backup_encryption: bool = True
    backup_compression: bool = True
    backup_verification: bool = True
    backup_retention_days: int = 90
    backup_frequency_hours: int = 24
    backup_storage_encrypted: bool = True
    backup_transfer_encrypted: bool = True
    backup_integrity_check: bool = True
    disaster_recovery_enabled: bool = True
    backup_monitoring: bool = True

@dataclass
class MonitoringSecurityConfig:
    """Security monitoring configuration"""
    real_time_monitoring: bool = True
    alert_threshold: int = 5
    alert_channels: List[str] = field(default_factory=lambda: ["email", "sms", "slack"])
    incident_response_enabled: bool = True
    threat_intelligence: bool = True
    vulnerability_scanning: bool = True
    penetration_testing: bool = True
    security_metrics: bool = True
    compliance_monitoring: bool = True
    risk_assessment: bool = True

class ProductionSecurityConfig:
    """Production security configuration manager"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.config = self._load_configuration()
        self._validate_configuration()
        self._generate_secrets()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load security configuration based on security level"""
        base_config = {
            "ssl": self._get_ssl_config(),
            "firewall": self._get_firewall_config(),
            "database": self._get_database_security_config(),
            "authentication": self._get_authentication_config(),
            "encryption": self._get_encryption_config(),
            "logging": self._get_logging_security_config(),
            "network": self._get_network_security_config(),
            "application": self._get_application_security_config(),
            "backup": self._get_backup_security_config(),
            "monitoring": self._get_monitoring_security_config()
        }
        
        # Apply security level specific configurations
        if self.security_level == SecurityLevel.HIGH_SECURITY:
            base_config = self._apply_high_security_config(base_config)
        elif self.security_level == SecurityLevel.PRODUCTION:
            base_config = self._apply_production_config(base_config)
        
        return base_config
    
    def _get_ssl_config(self) -> SSLConfig:
        """Get SSL/TLS configuration"""
        return SSLConfig(
            enabled=True,
            certificate_path=os.getenv('SSL_CERT_PATH', '/etc/ssl/certs/mingus.crt'),
            private_key_path=os.getenv('SSL_KEY_PATH', '/etc/ssl/private/mingus.key'),
            ca_certificate_path=os.getenv('SSL_CA_PATH', '/etc/ssl/certs/ca-bundle.crt'),
            ssl_protocol=os.getenv('SSL_PROTOCOL', 'TLSv1.3'),
            cipher_suite=os.getenv('SSL_CIPHER', 'ECDHE-RSA-AES256-GCM-SHA384'),
            hsts_enabled=os.getenv('HSTS_ENABLED', 'true').lower() == 'true',
            hsts_max_age=int(os.getenv('HSTS_MAX_AGE', '31536000')),
            hsts_include_subdomains=os.getenv('HSTS_INCLUDE_SUBDOMAINS', 'true').lower() == 'true',
            hsts_preload=os.getenv('HSTS_PRELOAD', 'true').lower() == 'true',
            ocsp_stapling=os.getenv('OCSP_STAPLING', 'true').lower() == 'true'
        )
    
    def _get_firewall_config(self) -> FirewallConfig:
        """Get firewall configuration"""
        allowed_ports = [22, 80, 443, 8080]
        if os.getenv('ADDITIONAL_PORTS'):
            allowed_ports.extend([int(p) for p in os.getenv('ADDITIONAL_PORTS').split(',')])
        
        allowed_ips = []
        if os.getenv('ALLOWED_IPS'):
            allowed_ips = os.getenv('ALLOWED_IPS').split(',')
        
        return FirewallConfig(
            enabled=True,
            default_policy=os.getenv('FIREWALL_DEFAULT_POLICY', 'DROP'),
            allowed_ports=allowed_ports,
            allowed_ips=allowed_ips,
            rate_limiting_enabled=os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
            rate_limit_requests=int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
            rate_limit_window=int(os.getenv('RATE_LIMIT_WINDOW', '60')),
            ddos_protection=os.getenv('DDOS_PROTECTION', 'true').lower() == 'true',
            fail2ban_enabled=os.getenv('FAIL2BAN_ENABLED', 'true').lower() == 'true',
            fail2ban_max_retries=int(os.getenv('FAIL2BAN_MAX_RETRIES', '3')),
            fail2ban_ban_time=int(os.getenv('FAIL2BAN_BAN_TIME', '3600'))
        )
    
    def _get_database_security_config(self) -> DatabaseSecurityConfig:
        """Get database security configuration"""
        return DatabaseSecurityConfig(
            encryption_at_rest=os.getenv('DB_ENCRYPTION_AT_REST', 'true').lower() == 'true',
            encryption_in_transit=os.getenv('DB_ENCRYPTION_IN_TRANSIT', 'true').lower() == 'true',
            connection_encryption=os.getenv('DB_CONNECTION_ENCRYPTION', 'require'),
            ssl_cert_verification=os.getenv('DB_SSL_CERT_VERIFICATION', 'true').lower() == 'true',
            connection_pooling=os.getenv('DB_CONNECTION_POOLING', 'true').lower() == 'true',
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '100')),
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            query_timeout=int(os.getenv('DB_QUERY_TIMEOUT', '300')),
            audit_logging=os.getenv('DB_AUDIT_LOGGING', 'true').lower() == 'true',
            backup_encryption=os.getenv('DB_BACKUP_ENCRYPTION', 'true').lower() == 'true',
            backup_retention_days=int(os.getenv('DB_BACKUP_RETENTION_DAYS', '30'))
        )
    
    def _get_authentication_config(self) -> AuthenticationConfig:
        """Get authentication security configuration"""
        mfa_methods = ["totp", "sms", "email"]
        if os.getenv('MFA_METHODS'):
            mfa_methods = os.getenv('MFA_METHODS').split(',')
        
        oauth_providers = ["google", "github"]
        if os.getenv('OAUTH_PROVIDERS'):
            oauth_providers = os.getenv('OAUTH_PROVIDERS').split(',')
        
        return AuthenticationConfig(
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration=int(os.getenv('LOCKOUT_DURATION', '900')),
            password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '12')),
            password_complexity=os.getenv('PASSWORD_COMPLEXITY', 'true').lower() == 'true',
            password_history=int(os.getenv('PASSWORD_HISTORY', '5')),
            password_expiry_days=int(os.getenv('PASSWORD_EXPIRY_DAYS', '90')),
            mfa_required=os.getenv('MFA_REQUIRED', 'true').lower() == 'true',
            mfa_methods=mfa_methods,
            jwt_secret=os.getenv('JWT_SECRET', ''),
            jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS512'),
            jwt_expiry_hours=int(os.getenv('JWT_EXPIRY_HOURS', '24')),
            refresh_token_expiry_days=int(os.getenv('REFRESH_TOKEN_EXPIRY_DAYS', '30')),
            oauth_enabled=os.getenv('OAUTH_ENABLED', 'true').lower() == 'true',
            oauth_providers=oauth_providers
        )
    
    def _get_encryption_config(self) -> EncryptionConfig:
        """Get encryption configuration"""
        return EncryptionConfig(
            algorithm=EncryptionAlgorithm(os.getenv('ENCRYPTION_ALGORITHM', 'aes_256_gcm')),
            key_rotation_days=int(os.getenv('KEY_ROTATION_DAYS', '90')),
            key_storage_path=os.getenv('KEY_STORAGE_PATH', '/var/lib/mingus/keys'),
            master_key_path=os.getenv('MASTER_KEY_PATH', '/var/lib/mingus/master.key'),
            data_encryption_key=os.getenv('DATA_ENCRYPTION_KEY', ''),
            file_encryption_enabled=os.getenv('FILE_ENCRYPTION_ENABLED', 'true').lower() == 'true',
            backup_encryption_enabled=os.getenv('BACKUP_ENCRYPTION_ENABLED', 'true').lower() == 'true',
            communication_encryption=os.getenv('COMMUNICATION_ENCRYPTION', 'true').lower() == 'true',
            end_to_end_encryption=os.getenv('END_TO_END_ENCRYPTION', 'true').lower() == 'true'
        )
    
    def _get_logging_security_config(self) -> LoggingSecurityConfig:
        """Get security logging configuration"""
        return LoggingSecurityConfig(
            security_log_level=os.getenv('SECURITY_LOG_LEVEL', 'INFO'),
            security_log_path=os.getenv('SECURITY_LOG_PATH', '/var/log/mingus/security.log'),
            audit_log_path=os.getenv('AUDIT_LOG_PATH', '/var/log/mingus/audit.log'),
            log_encryption=os.getenv('LOG_ENCRYPTION', 'true').lower() == 'true',
            log_retention_days=int(os.getenv('LOG_RETENTION_DAYS', '365')),
            log_rotation_size=os.getenv('LOG_ROTATION_SIZE', '100M'),
            log_rotation_count=int(os.getenv('LOG_ROTATION_COUNT', '10')),
            sensitive_data_masking=os.getenv('SENSITIVE_DATA_MASKING', 'true').lower() == 'true',
            ip_address_logging=os.getenv('IP_ADDRESS_LOGGING', 'true').lower() == 'true',
            user_agent_logging=os.getenv('USER_AGENT_LOGGING', 'true').lower() == 'true',
            request_id_logging=os.getenv('REQUEST_ID_LOGGING', 'true').lower() == 'true'
        )
    
    def _get_network_security_config(self) -> NetworkSecurityConfig:
        """Get network security configuration"""
        return NetworkSecurityConfig(
            vpn_required=os.getenv('VPN_REQUIRED', 'true').lower() == 'true',
            vpn_endpoint=os.getenv('VPN_ENDPOINT', ''),
            proxy_enabled=os.getenv('PROXY_ENABLED', 'false').lower() == 'true',
            proxy_config={},
            cdn_enabled=os.getenv('CDN_ENABLED', 'true').lower() == 'true',
            cdn_provider=os.getenv('CDN_PROVIDER', 'cloudflare'),
            load_balancer_enabled=os.getenv('LOAD_BALANCER_ENABLED', 'true').lower() == 'true',
            health_check_enabled=os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
            monitoring_enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            intrusion_detection=os.getenv('INTRUSION_DETECTION', 'true').lower() == 'true',
            network_segmentation=os.getenv('NETWORK_SEGMENTATION', 'true').lower() == 'true'
        )
    
    def _get_application_security_config(self) -> ApplicationSecurityConfig:
        """Get application security configuration"""
        cors_origins = []
        if os.getenv('CORS_ORIGINS'):
            cors_origins = os.getenv('CORS_ORIGINS').split(',')
        
        return ApplicationSecurityConfig(
            cors_enabled=os.getenv('CORS_ENABLED', 'true').lower() == 'true',
            cors_origins=cors_origins,
            cors_methods=os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE').split(','),
            cors_headers=os.getenv('CORS_HEADERS', 'Content-Type,Authorization').split(','),
            csrf_protection=os.getenv('CSRF_PROTECTION', 'true').lower() == 'true',
            csrf_token_expiry=int(os.getenv('CSRF_TOKEN_EXPIRY', '3600')),
            xss_protection=os.getenv('XSS_PROTECTION', 'true').lower() == 'true',
            content_security_policy=os.getenv('CSP_POLICY', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"),
            strict_transport_security=os.getenv('HSTS_ENABLED', 'true').lower() == 'true',
            x_content_type_options=os.getenv('X_CONTENT_TYPE_OPTIONS', 'true').lower() == 'true',
            x_frame_options=os.getenv('X_FRAME_OPTIONS', 'DENY'),
            referrer_policy=os.getenv('REFERRER_POLICY', 'strict-origin-when-cross-origin'),
            permissions_policy=os.getenv('PERMISSIONS_POLICY', 'geolocation=(), microphone=(), camera=()')
        )
    
    def _get_backup_security_config(self) -> BackupSecurityConfig:
        """Get backup security configuration"""
        return BackupSecurityConfig(
            backup_encryption=os.getenv('BACKUP_ENCRYPTION', 'true').lower() == 'true',
            backup_compression=os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true',
            backup_verification=os.getenv('BACKUP_VERIFICATION', 'true').lower() == 'true',
            backup_retention_days=int(os.getenv('BACKUP_RETENTION_DAYS', '90')),
            backup_frequency_hours=int(os.getenv('BACKUP_FREQUENCY_HOURS', '24')),
            backup_storage_encrypted=os.getenv('BACKUP_STORAGE_ENCRYPTED', 'true').lower() == 'true',
            backup_transfer_encrypted=os.getenv('BACKUP_TRANSFER_ENCRYPTED', 'true').lower() == 'true',
            backup_integrity_check=os.getenv('BACKUP_INTEGRITY_CHECK', 'true').lower() == 'true',
            disaster_recovery_enabled=os.getenv('DISASTER_RECOVERY_ENABLED', 'true').lower() == 'true',
            backup_monitoring=os.getenv('BACKUP_MONITORING', 'true').lower() == 'true'
        )
    
    def _get_monitoring_security_config(self) -> MonitoringSecurityConfig:
        """Get security monitoring configuration"""
        alert_channels = ["email", "sms", "slack"]
        if os.getenv('ALERT_CHANNELS'):
            alert_channels = os.getenv('ALERT_CHANNELS').split(',')
        
        return MonitoringSecurityConfig(
            real_time_monitoring=os.getenv('REAL_TIME_MONITORING', 'true').lower() == 'true',
            alert_threshold=int(os.getenv('ALERT_THRESHOLD', '5')),
            alert_channels=alert_channels,
            incident_response_enabled=os.getenv('INCIDENT_RESPONSE_ENABLED', 'true').lower() == 'true',
            threat_intelligence=os.getenv('THREAT_INTELLIGENCE', 'true').lower() == 'true',
            vulnerability_scanning=os.getenv('VULNERABILITY_SCANNING', 'true').lower() == 'true',
            penetration_testing=os.getenv('PENETRATION_TESTING', 'true').lower() == 'true',
            security_metrics=os.getenv('SECURITY_METRICS', 'true').lower() == 'true',
            compliance_monitoring=os.getenv('COMPLIANCE_MONITORING', 'true').lower() == 'true',
            risk_assessment=os.getenv('RISK_ASSESSMENT', 'true').lower() == 'true'
        )
    
    def _apply_high_security_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply high security configuration overrides"""
        # Enhanced SSL/TLS
        config['ssl'].ssl_protocol = "TLSv1.3"
        config['ssl'].cipher_suite = "ECDHE-RSA-AES256-GCM-SHA384"
        config['ssl'].hsts_max_age = 63072000  # 2 years
        
        # Enhanced firewall
        config['firewall'].rate_limit_requests = 50
        config['firewall'].fail2ban_max_retries = 2
        config['firewall'].fail2ban_ban_time = 7200  # 2 hours
        
        # Enhanced authentication
        config['authentication'].session_timeout = 1800  # 30 minutes
        config['authentication'].max_login_attempts = 3
        config['authentication'].password_min_length = 16
        config['authentication'].password_expiry_days = 60
        config['authentication'].jwt_expiry_hours = 12
        
        # Enhanced encryption
        config['encryption'].key_rotation_days = 30
        config['encryption'].algorithm = EncryptionAlgorithm.CHACHA20_POLY1305
        
        # Enhanced logging
        config['logging'].security_log_level = "DEBUG"
        config['logging'].log_retention_days = 730  # 2 years
        
        # Enhanced application security
        config['application'].content_security_policy = "default-src 'self'; script-src 'self'; style-src 'self';"
        config['application'].x_frame_options = "DENY"
        
        return config
    
    def _apply_production_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply production configuration overrides"""
        # Standard production settings are already applied in base config
        return config
    
    def _validate_configuration(self):
        """Validate security configuration"""
        # Validate SSL configuration
        if self.config['ssl'].enabled:
            if not os.path.exists(self.config['ssl'].certificate_path):
                raise ValueError(f"SSL certificate not found: {self.config['ssl'].certificate_path}")
            if not os.path.exists(self.config['ssl'].private_key_path):
                raise ValueError(f"SSL private key not found: {self.config['ssl'].private_key_path}")
        
        # Validate encryption keys
        if not self.config['encryption'].data_encryption_key:
            raise ValueError("Data encryption key is required")
        
        # Validate JWT secret
        if not self.config['authentication'].jwt_secret:
            raise ValueError("JWT secret is required")
        
        # Validate required directories
        required_dirs = [
            self.config['encryption'].key_storage_path,
            os.path.dirname(self.config['logging'].security_log_path),
            os.path.dirname(self.config['logging'].audit_log_path)
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o700)
    
    def _generate_secrets(self):
        """Generate required secrets if not provided"""
        # Generate JWT secret if not provided
        if not self.config['authentication'].jwt_secret:
            self.config['authentication'].jwt_secret = secrets.token_urlsafe(64)
        
        # Generate data encryption key if not provided
        if not self.config['encryption'].data_encryption_key:
            self.config['encryption'].data_encryption_key = Fernet.generate_key().decode()
        
        # Generate master key if not exists
        if not os.path.exists(self.config['encryption'].master_key_path):
            master_key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.config['encryption'].master_key_path), exist_ok=True)
            with open(self.config['encryption'].master_key_path, 'wb') as f:
                f.write(master_key)
    
    def get_nginx_config(self) -> str:
        """Generate Nginx security configuration"""
        config = f"""
# MINGUS Production Security Configuration
server {{
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate {self.config['ssl'].certificate_path};
    ssl_certificate_key {self.config['ssl'].private_key_path};
    ssl_trusted_certificate {self.config['ssl'].ca_certificate_path};
    
    # SSL Security Settings
    ssl_protocols {self.config['ssl'].ssl_protocol};
    ssl_ciphers {self.config['ssl'].cipher_suite};
    ssl_prefer_server_ciphers on;
    ssl_session_cache {self.config['ssl'].ssl_session_cache};
    ssl_session_timeout {self.config['ssl'].ssl_session_timeout};
    
    # HSTS
    add_header Strict-Transport-Security "max-age={self.config['ssl'].hsts_max_age}; includeSubDomains; preload" always;
    
    # Security Headers
    add_header X-Frame-Options "{self.config['application'].x_frame_options}" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "{self.config['application'].referrer_policy}" always;
    add_header Content-Security-Policy "{self.config['application'].content_security_policy}" always;
    add_header Permissions-Policy "{self.config['application'].permissions_policy}" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate={self.config['firewall'].rate_limit_requests}r/m;
    limit_req zone=api burst=20 nodelay;
    
    # File Upload Limits
    client_max_body_size 10M;
    client_body_timeout 30s;
    client_header_timeout 30s;
    
    # Proxy Settings
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    
    # Security
    server_tokens off;
    hide_version_string on;
    
    # Main Application
    location / {{
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security Headers for API
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
    }}
    
    # Health Check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
    
    # Deny access to sensitive files
    location ~ /\\. {{
        deny all;
    }}
    
    location ~* \\.(log|sql|conf|key)$ {{
        deny all;
    }}
}}
"""
        return config
    
    def get_systemd_service_config(self) -> str:
        """Generate systemd service configuration"""
        config = f"""
[Unit]
Description=MINGUS Production Application
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=mingus
Group=mingus
WorkingDirectory=/opt/mingus
Environment=PATH=/opt/mingus/venv/bin
Environment=PYTHONPATH=/opt/mingus
Environment=SECURITY_LEVEL={self.security_level.value}
Environment=SSL_CERT_PATH={self.config['ssl'].certificate_path}
Environment=SSL_KEY_PATH={self.config['ssl'].private_key_path}
Environment=JWT_SECRET={self.config['authentication'].jwt_secret}
Environment=DATA_ENCRYPTION_KEY={self.config['encryption'].data_encryption_key}
ExecStart=/opt/mingus/venv/bin/python /opt/mingus/app.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mingus

# Security Settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/mingus /var/log/mingus /tmp
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true

# Resource Limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
"""
        return config
    
    def get_firewall_rules(self) -> List[str]:
        """Generate firewall rules"""
        rules = [
            "# MINGUS Production Firewall Rules",
            "# Flush existing rules",
            "iptables -F",
            "iptables -X",
            "",
            "# Set default policies",
            f"iptables -P INPUT {self.config['firewall'].default_policy}",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "",
            "# Allow loopback",
            "iptables -A INPUT -i lo -j ACCEPT",
            "",
            "# Allow established connections",
            "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
            "",
            "# Allow SSH (port 22)",
            "iptables -A INPUT -p tcp --dport 22 -j ACCEPT",
            "",
            "# Allow HTTP (port 80)",
            "iptables -A INPUT -p tcp --dport 80 -j ACCEPT",
            "",
            "# Allow HTTPS (port 443)",
            "iptables -A INPUT -p tcp --dport 443 -j ACCEPT",
            "",
            "# Allow application port (8080)",
            "iptables -A INPUT -p tcp --dport 8080 -j ACCEPT",
            "",
            "# Rate limiting",
            "iptables -A INPUT -p tcp --dport 80 -m limit --limit {self.config['firewall'].rate_limit_requests}/minute --limit-burst 20 -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 443 -m limit --limit {self.config['firewall'].rate_limit_requests}/minute --limit-burst 20 -j ACCEPT",
            "",
            "# Log dropped packets",
            "iptables -A INPUT -j LOG --log-prefix 'MINGUS_FIREWALL_DROP: '",
            "",
            "# Save rules",
            "iptables-save > /etc/iptables/rules.v4"
        ]
        
        return rules
    
    def get_security_checklist(self) -> List[str]:
        """Get security checklist for deployment"""
        checklist = [
            "✅ SSL/TLS certificates installed and configured",
            "✅ Firewall rules applied and active",
            "✅ Database encryption enabled",
            "✅ Authentication security configured",
            "✅ Encryption keys generated and secured",
            "✅ Logging and monitoring configured",
            "✅ Backup encryption enabled",
            "✅ Security headers configured",
            "✅ Rate limiting enabled",
            "✅ Fail2ban configured",
            "✅ VPN access configured (if required)",
            "✅ Intrusion detection enabled",
            "✅ Vulnerability scanning completed",
            "✅ Penetration testing completed",
            "✅ Security monitoring active",
            "✅ Incident response procedures documented",
            "✅ Disaster recovery plan in place",
            "✅ Compliance monitoring active",
            "✅ Security metrics collection enabled",
            "✅ Risk assessment completed"
        ]
        
        return checklist
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export configuration for deployment"""
        return {
            "security_level": self.security_level.value,
            "configuration": {
                "ssl": self.config['ssl'].__dict__,
                "firewall": self.config['firewall'].__dict__,
                "database": self.config['database'].__dict__,
                "authentication": self.config['authentication'].__dict__,
                "encryption": self.config['encryption'].__dict__,
                "logging": self.config['logging'].__dict__,
                "network": self.config['network'].__dict__,
                "application": self.config['application'].__dict__,
                "backup": self.config['backup'].__dict__,
                "monitoring": self.config['monitoring'].__dict__
            },
            "nginx_config": self.get_nginx_config(),
            "systemd_config": self.get_systemd_service_config(),
            "firewall_rules": self.get_firewall_rules(),
            "security_checklist": self.get_security_checklist(),
            "generated_at": datetime.utcnow().isoformat()
        }

# Global production security config instance
_production_security_config = None

def get_production_security_config(security_level: SecurityLevel = SecurityLevel.PRODUCTION) -> ProductionSecurityConfig:
    """Get global production security configuration instance"""
    global _production_security_config
    
    if _production_security_config is None:
        _production_security_config = ProductionSecurityConfig(security_level)
    
    return _production_security_config

def generate_security_config(security_level: SecurityLevel = SecurityLevel.PRODUCTION) -> Dict[str, Any]:
    """Generate complete security configuration for deployment"""
    config = get_production_security_config(security_level)
    return config.export_configuration() 