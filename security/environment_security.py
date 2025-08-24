"""
Environment-Specific Security Configuration
Comprehensive security management for different environments
"""

import os
import json
import yaml
import hashlib
import secrets
import base64
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hvac
import boto3
from loguru import logger

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class SecurityLevel(Enum):
    """Security levels for different environments"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecretType(Enum):
    """Types of secrets"""
    DATABASE_PASSWORD = "database_password"
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    SSL_CERTIFICATE = "ssl_certificate"
    OAUTH_SECRET = "oauth_secret"
    SSH_KEY = "ssh_key"
    ACCESS_TOKEN = "access_token"

@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    environment: Environment
    security_level: SecurityLevel
    debug_enabled: bool
    logging_level: str
    ssl_required: bool
    session_timeout: int
    max_login_attempts: int
    password_min_length: int
    mfa_required: bool
    rate_limiting_enabled: bool
    backup_enabled: bool
    monitoring_enabled: bool
    audit_logging_enabled: bool
    encryption_required: bool
    allowed_hosts: List[str] = field(default_factory=list)
    cors_origins: List[str] = field(default_factory=list)
    security_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class SecretConfig:
    """Secret configuration"""
    secret_id: str
    secret_type: SecretType
    environment: Environment
    encrypted_value: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    policy_id: str
    environment: Environment
    policy_name: str
    policy_type: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    priority: int = 100
    created_at: datetime = field(default_factory=datetime.utcnow)

class EnvironmentSecurityManager:
    """Environment-specific security manager"""
    
    def __init__(self, base_path: str = "/var/lib/mingus/security"):
        self.base_path = base_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.config_lock = threading.Lock()
        
        # Initialize databases
        self._init_databases()
        
        # Load environment configurations
        self.environment_configs = self._load_environment_configs()
        
        # Initialize secret management
        self.secret_manager = SecretManager(base_path)
        
        # Initialize policy enforcer
        self.policy_enforcer = SecurityPolicyEnforcer(base_path)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = os.path.join(self.base_path, "encryption.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _init_databases(self):
        """Initialize security databases"""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            
            # Environment config database
            env_db_path = os.path.join(self.base_path, "environment_config.db")
            with sqlite3.connect(env_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS environment_configs (
                        environment TEXT PRIMARY KEY,
                        config_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
            
            # Security policies database
            policy_db_path = os.path.join(self.base_path, "security_policies.db")
            with sqlite3.connect(policy_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        environment TEXT NOT NULL,
                        policy_name TEXT NOT NULL,
                        policy_type TEXT NOT NULL,
                        rules TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        priority INTEGER DEFAULT 100,
                        created_at TEXT NOT NULL
                    )
                """)
                
        except Exception as e:
            logger.error(f"Error initializing security databases: {e}")
    
    def _load_environment_configs(self) -> Dict[Environment, EnvironmentConfig]:
        """Load environment-specific configurations"""
        configs = {}
        
        # Development environment
        configs[Environment.DEVELOPMENT] = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            security_level=SecurityLevel.LOW,
            debug_enabled=True,
            logging_level="DEBUG",
            ssl_required=False,
            session_timeout=3600,
            max_login_attempts=10,
            password_min_length=8,
            mfa_required=False,
            rate_limiting_enabled=False,
            backup_enabled=False,
            monitoring_enabled=False,
            audit_logging_enabled=False,
            encryption_required=False,
            allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"],
            cors_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            security_headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN"
            }
        )
        
        # Staging environment
        configs[Environment.STAGING] = EnvironmentConfig(
            environment=Environment.STAGING,
            security_level=SecurityLevel.MEDIUM,
            debug_enabled=False,
            logging_level="INFO",
            ssl_required=True,
            session_timeout=1800,
            max_login_attempts=5,
            password_min_length=10,
            mfa_required=True,
            rate_limiting_enabled=True,
            backup_enabled=True,
            monitoring_enabled=True,
            audit_logging_enabled=True,
            encryption_required=True,
            allowed_hosts=["staging.yourdomain.com"],
            cors_origins=["https://staging.yourdomain.com"],
            security_headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            }
        )
        
        # Production environment
        configs[Environment.PRODUCTION] = EnvironmentConfig(
            environment=Environment.PRODUCTION,
            security_level=SecurityLevel.HIGH,
            debug_enabled=False,
            logging_level="WARNING",
            ssl_required=True,
            session_timeout=900,
            max_login_attempts=3,
            password_min_length=12,
            mfa_required=True,
            rate_limiting_enabled=True,
            backup_enabled=True,
            monitoring_enabled=True,
            audit_logging_enabled=True,
            encryption_required=True,
            allowed_hosts=["yourdomain.com", "www.yourdomain.com"],
            cors_origins=["https://yourdomain.com", "https://www.yourdomain.com"],
            security_headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        return configs
    
    def get_environment_config(self, environment: Environment) -> EnvironmentConfig:
        """Get environment-specific configuration"""
        return self.environment_configs.get(environment)
    
    def update_environment_config(self, environment: Environment, config: EnvironmentConfig):
        """Update environment configuration"""
        try:
            with self.config_lock:
                self.environment_configs[environment] = config
                
                # Save to database
                env_db_path = os.path.join(self.base_path, "environment_config.db")
                with sqlite3.connect(env_db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO environment_configs 
                        (environment, config_data, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        environment.value,
                        json.dumps(config.__dict__, default=str),
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat()
                    ))
                
                logger.info(f"Environment config updated for {environment.value}")
                
        except Exception as e:
            logger.error(f"Error updating environment config: {e}")
    
    def validate_environment_config(self, environment: Environment) -> List[str]:
        """Validate environment configuration"""
        config = self.get_environment_config(environment)
        errors = []
        
        if not config:
            errors.append(f"No configuration found for environment {environment.value}")
            return errors
        
        # Validate security level
        if environment == Environment.PRODUCTION and config.security_level != SecurityLevel.HIGH:
            errors.append("Production environment must have HIGH security level")
        
        # Validate SSL requirements
        if environment in [Environment.STAGING, Environment.PRODUCTION] and not config.ssl_required:
            errors.append(f"{environment.value} environment must require SSL")
        
        # Validate password requirements
        if environment == Environment.PRODUCTION and config.password_min_length < 12:
            errors.append("Production environment must have minimum 12 character passwords")
        
        # Validate MFA requirements
        if environment in [Environment.STAGING, Environment.PRODUCTION] and not config.mfa_required:
            errors.append(f"{environment.value} environment must require MFA")
        
        # Validate allowed hosts
        if not config.allowed_hosts:
            errors.append(f"{environment.value} environment must have allowed hosts configured")
        
        return errors
    
    def get_secret(self, secret_id: str, environment: Environment) -> Optional[str]:
        """Get secret for environment"""
        return self.secret_manager.get_secret(secret_id, environment)
    
    def set_secret(self, secret_id: str, secret_type: SecretType, value: str, 
                   environment: Environment, description: str = "", 
                   expires_at: Optional[datetime] = None) -> bool:
        """Set secret for environment"""
        return self.secret_manager.set_secret(
            secret_id, secret_type, value, environment, description, expires_at
        )
    
    def validate_security_policy(self, environment: Environment, 
                                policy_name: str, data: Dict[str, Any]) -> List[str]:
        """Validate security policy"""
        return self.policy_enforcer.validate_policy(environment, policy_name, data)
    
    def enforce_security_policy(self, environment: Environment, 
                               policy_name: str, data: Dict[str, Any]) -> bool:
        """Enforce security policy"""
        return self.policy_enforcer.enforce_policy(environment, policy_name, data)

class SecretManager:
    """Secret management system"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.secret_lock = threading.Lock()
        
        self._init_secret_database()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secrets"""
        key_file = os.path.join(self.base_path, "secret_encryption.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _init_secret_database(self):
        """Initialize secret database"""
        try:
            secret_db_path = os.path.join(self.base_path, "secrets.db")
            with sqlite3.connect(secret_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS secrets (
                        secret_id TEXT PRIMARY KEY,
                        secret_type TEXT NOT NULL,
                        environment TEXT NOT NULL,
                        encrypted_value TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        description TEXT,
                        tags TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_secret_env ON secrets(environment)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_secret_type ON secrets(secret_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_secret_expires ON secrets(expires_at)")
                
        except Exception as e:
            logger.error(f"Error initializing secret database: {e}")
    
    def set_secret(self, secret_id: str, secret_type: SecretType, value: str,
                   environment: Environment, description: str = "",
                   expires_at: Optional[datetime] = None) -> bool:
        """Set secret"""
        try:
            with self.secret_lock:
                # Encrypt the secret value
                encrypted_value = self.cipher_suite.encrypt(value.encode()).decode()
                
                secret_db_path = os.path.join(self.base_path, "secrets.db")
                with sqlite3.connect(secret_db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO secrets 
                        (secret_id, secret_type, environment, encrypted_value, 
                         created_at, expires_at, description, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        secret_id,
                        secret_type.value,
                        environment.value,
                        encrypted_value,
                        datetime.utcnow().isoformat(),
                        expires_at.isoformat() if expires_at else None,
                        description,
                        json.dumps([])
                    ))
                
                logger.info(f"Secret {secret_id} set for environment {environment.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting secret: {e}")
            return False
    
    def get_secret(self, secret_id: str, environment: Environment) -> Optional[str]:
        """Get secret"""
        try:
            secret_db_path = os.path.join(self.base_path, "secrets.db")
            with sqlite3.connect(secret_db_path) as conn:
                cursor = conn.execute("""
                    SELECT encrypted_value, expires_at
                    FROM secrets 
                    WHERE secret_id = ? AND environment = ?
                """, (secret_id, environment.value))
                
                row = cursor.fetchone()
                if row:
                    encrypted_value, expires_at = row
                    
                    # Check if secret has expired
                    if expires_at:
                        expiry = datetime.fromisoformat(expires_at)
                        if datetime.utcnow() > expiry:
                            logger.warning(f"Secret {secret_id} has expired")
                            return None
                    
                    # Decrypt the secret value
                    decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode()).decode()
                    return decrypted_value
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting secret: {e}")
            return None
    
    def delete_secret(self, secret_id: str, environment: Environment) -> bool:
        """Delete secret"""
        try:
            secret_db_path = os.path.join(self.base_path, "secrets.db")
            with sqlite3.connect(secret_db_path) as conn:
                conn.execute("""
                    DELETE FROM secrets 
                    WHERE secret_id = ? AND environment = ?
                """, (secret_id, environment.value))
                
                logger.info(f"Secret {secret_id} deleted for environment {environment.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting secret: {e}")
            return False
    
    def list_secrets(self, environment: Environment) -> List[Dict[str, Any]]:
        """List secrets for environment"""
        try:
            secret_db_path = os.path.join(self.base_path, "secrets.db")
            with sqlite3.connect(secret_db_path) as conn:
                cursor = conn.execute("""
                    SELECT secret_id, secret_type, created_at, expires_at, description
                    FROM secrets 
                    WHERE environment = ?
                    ORDER BY created_at DESC
                """, (environment.value,))
                
                secrets = []
                for row in cursor.fetchall():
                    secrets.append({
                        "secret_id": row[0],
                        "secret_type": row[1],
                        "created_at": row[2],
                        "expires_at": row[3],
                        "description": row[4]
                    })
                
                return secrets
                
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []
    
    def rotate_secret(self, secret_id: str, environment: Environment, 
                     new_value: str) -> bool:
        """Rotate secret"""
        try:
            # Get current secret info
            secret_db_path = os.path.join(self.base_path, "secrets.db")
            with sqlite3.connect(secret_db_path) as conn:
                cursor = conn.execute("""
                    SELECT secret_type, description, expires_at
                    FROM secrets 
                    WHERE secret_id = ? AND environment = ?
                """, (secret_id, environment.value))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"Secret {secret_id} not found")
                    return False
                
                secret_type, description, expires_at = row
                
                # Update with new value
                encrypted_value = self.cipher_suite.encrypt(new_value.encode()).decode()
                
                conn.execute("""
                    UPDATE secrets 
                    SET encrypted_value = ?, created_at = ?
                    WHERE secret_id = ? AND environment = ?
                """, (
                    encrypted_value,
                    datetime.utcnow().isoformat(),
                    secret_id,
                    environment.value
                ))
                
                logger.info(f"Secret {secret_id} rotated for environment {environment.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error rotating secret: {e}")
            return False

class SecurityPolicyEnforcer:
    """Security policy enforcement system"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.policy_lock = threading.Lock()
        
        self._init_policy_database()
        self._load_default_policies()
    
    def _init_policy_database(self):
        """Initialize policy database"""
        try:
            policy_db_path = os.path.join(self.base_path, "security_policies.db")
            with sqlite3.connect(policy_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        environment TEXT NOT NULL,
                        policy_name TEXT NOT NULL,
                        policy_type TEXT NOT NULL,
                        rules TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        priority INTEGER DEFAULT 100,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_env ON security_policies(environment)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_type ON security_policies(policy_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_enabled ON security_policies(enabled)")
                
        except Exception as e:
            logger.error(f"Error initializing policy database: {e}")
    
    def _load_default_policies(self):
        """Load default security policies"""
        default_policies = [
            {
                "policy_id": "password_policy",
                "policy_name": "Password Policy",
                "policy_type": "authentication",
                "rules": {
                    "min_length": {"dev": 8, "staging": 10, "prod": 12},
                    "require_uppercase": {"dev": False, "staging": True, "prod": True},
                    "require_lowercase": {"dev": True, "staging": True, "prod": True},
                    "require_numbers": {"dev": True, "staging": True, "prod": True},
                    "require_special": {"dev": False, "staging": True, "prod": True},
                    "max_age_days": {"dev": 365, "staging": 90, "prod": 60}
                }
            },
            {
                "policy_id": "session_policy",
                "policy_name": "Session Policy",
                "policy_type": "session",
                "rules": {
                    "timeout_minutes": {"dev": 60, "staging": 30, "prod": 15},
                    "max_concurrent_sessions": {"dev": 5, "staging": 3, "prod": 1},
                    "require_secure_cookies": {"dev": False, "staging": True, "prod": True},
                    "require_https": {"dev": False, "staging": True, "prod": True}
                }
            },
            {
                "policy_id": "rate_limiting_policy",
                "policy_name": "Rate Limiting Policy",
                "policy_type": "rate_limiting",
                "rules": {
                    "requests_per_minute": {"dev": 1000, "staging": 100, "prod": 50},
                    "burst_limit": {"dev": 2000, "staging": 200, "prod": 100},
                    "block_duration_minutes": {"dev": 5, "staging": 15, "prod": 30}
                }
            },
            {
                "policy_id": "encryption_policy",
                "policy_name": "Encryption Policy",
                "policy_type": "encryption",
                "rules": {
                    "require_ssl": {"dev": False, "staging": True, "prod": True},
                    "min_tls_version": {"dev": "1.0", "staging": "1.2", "prod": "1.3"},
                    "require_encryption_at_rest": {"dev": False, "staging": True, "prod": True},
                    "require_encryption_in_transit": {"dev": False, "staging": True, "prod": True}
                }
            }
        ]
        
        for policy in default_policies:
            for env in Environment:
                self.create_policy(
                    f"{policy['policy_id']}_{env.value}",
                    env,
                    policy["policy_name"],
                    policy["policy_type"],
                    policy["rules"]
                )
    
    def create_policy(self, policy_id: str, environment: Environment,
                     policy_name: str, policy_type: str, rules: Dict[str, Any]) -> bool:
        """Create security policy"""
        try:
            with self.policy_lock:
                policy_db_path = os.path.join(self.base_path, "security_policies.db")
                with sqlite3.connect(policy_db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO security_policies 
                        (policy_id, environment, policy_name, policy_type, rules, 
                         enabled, priority, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        policy_id,
                        environment.value,
                        policy_name,
                        policy_type,
                        json.dumps(rules),
                        1,
                        100,
                        datetime.utcnow().isoformat()
                    ))
                
                logger.info(f"Policy {policy_id} created for environment {environment.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating policy: {e}")
            return False
    
    def get_policy(self, policy_id: str, environment: Environment) -> Optional[Dict[str, Any]]:
        """Get security policy"""
        try:
            policy_db_path = os.path.join(self.base_path, "security_policies.db")
            with sqlite3.connect(policy_db_path) as conn:
                cursor = conn.execute("""
                    SELECT policy_id, environment, policy_name, policy_type, 
                           rules, enabled, priority, created_at
                    FROM security_policies 
                    WHERE policy_id = ? AND environment = ?
                """, (policy_id, environment.value))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "policy_id": row[0],
                        "environment": row[1],
                        "policy_name": row[2],
                        "policy_type": row[3],
                        "rules": json.loads(row[4]),
                        "enabled": bool(row[5]),
                        "priority": row[6],
                        "created_at": row[7]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting policy: {e}")
            return None
    
    def validate_policy(self, environment: Environment, policy_name: str, 
                       data: Dict[str, Any]) -> List[str]:
        """Validate data against security policy"""
        errors = []
        
        try:
            # Get applicable policies
            policies = self._get_applicable_policies(environment, policy_name)
            
            for policy in policies:
                if not policy["enabled"]:
                    continue
                
                rules = policy["rules"]
                policy_errors = self._validate_against_rules(rules, data, environment)
                errors.extend(policy_errors)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating policy: {e}")
            return [f"Policy validation error: {e}"]
    
    def _get_applicable_policies(self, environment: Environment, 
                                policy_name: str) -> List[Dict[str, Any]]:
        """Get applicable policies for environment and policy name"""
        try:
            policy_db_path = os.path.join(self.base_path, "security_policies.db")
            with sqlite3.connect(policy_db_path) as conn:
                cursor = conn.execute("""
                    SELECT policy_id, environment, policy_name, policy_type, 
                           rules, enabled, priority, created_at
                    FROM security_policies 
                    WHERE environment = ? AND policy_name LIKE ?
                    ORDER BY priority DESC
                """, (environment.value, f"%{policy_name}%"))
                
                policies = []
                for row in cursor.fetchall():
                    policies.append({
                        "policy_id": row[0],
                        "environment": row[1],
                        "policy_name": row[2],
                        "policy_type": row[3],
                        "rules": json.loads(row[4]),
                        "enabled": bool(row[5]),
                        "priority": row[6],
                        "created_at": row[7]
                    })
                
                return policies
                
        except Exception as e:
            logger.error(f"Error getting applicable policies: {e}")
            return []
    
    def _validate_against_rules(self, rules: Dict[str, Any], 
                               data: Dict[str, Any], environment: Environment) -> List[str]:
        """Validate data against specific rules"""
        errors = []
        
        for rule_name, rule_value in rules.items():
            if isinstance(rule_value, dict):
                # Environment-specific rule
                env_rule = rule_value.get(environment.value)
                if env_rule is not None:
                    error = self._validate_rule(rule_name, env_rule, data)
                    if error:
                        errors.append(error)
            else:
                # Global rule
                error = self._validate_rule(rule_name, rule_value, data)
                if error:
                    errors.append(error)
        
        return errors
    
    def _validate_rule(self, rule_name: str, rule_value: Any, 
                      data: Dict[str, Any]) -> Optional[str]:
        """Validate single rule"""
        if rule_name not in data:
            return f"Required field '{rule_name}' is missing"
        
        actual_value = data[rule_name]
        
        if rule_name == "min_length":
            if len(str(actual_value)) < rule_value:
                return f"Value for '{rule_name}' must be at least {rule_value} characters"
        
        elif rule_name == "require_uppercase":
            if rule_value and not any(c.isupper() for c in str(actual_value)):
                return f"Value for '{rule_name}' must contain uppercase characters"
        
        elif rule_name == "require_lowercase":
            if rule_value and not any(c.islower() for c in str(actual_value)):
                return f"Value for '{rule_name}' must contain lowercase characters"
        
        elif rule_name == "require_numbers":
            if rule_value and not any(c.isdigit() for c in str(actual_value)):
                return f"Value for '{rule_name}' must contain numbers"
        
        elif rule_name == "require_special":
            if rule_value and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in str(actual_value)):
                return f"Value for '{rule_name}' must contain special characters"
        
        elif rule_name == "timeout_minutes":
            if actual_value > rule_value:
                return f"Value for '{rule_name}' must not exceed {rule_value} minutes"
        
        elif rule_name == "max_concurrent_sessions":
            if actual_value > rule_value:
                return f"Value for '{rule_name}' must not exceed {rule_value}"
        
        elif rule_name == "require_secure_cookies":
            if rule_value and not data.get("secure_cookies", False):
                return f"Secure cookies are required for '{rule_name}'"
        
        elif rule_name == "require_https":
            if rule_value and not data.get("https_enabled", False):
                return f"HTTPS is required for '{rule_name}'"
        
        return None
    
    def enforce_policy(self, environment: Environment, policy_name: str, 
                      data: Dict[str, Any]) -> bool:
        """Enforce security policy"""
        try:
            # Validate against policies
            errors = self.validate_policy(environment, policy_name, data)
            
            if errors:
                logger.warning(f"Policy enforcement failed for {policy_name}: {errors}")
                return False
            
            # Apply policy enforcement
            policies = self._get_applicable_policies(environment, policy_name)
            
            for policy in policies:
                if not policy["enabled"]:
                    continue
                
                self._apply_policy_enforcement(policy, data)
            
            logger.info(f"Policy {policy_name} enforced successfully for {environment.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error enforcing policy: {e}")
            return False
    
    def _apply_policy_enforcement(self, policy: Dict[str, Any], data: Dict[str, Any]):
        """Apply policy enforcement actions"""
        policy_type = policy["policy_type"]
        rules = policy["rules"]
        
        if policy_type == "authentication":
            # Apply authentication policies
            if "max_login_attempts" in rules:
                data["max_login_attempts"] = rules["max_login_attempts"]
        
        elif policy_type == "session":
            # Apply session policies
            if "timeout_minutes" in rules:
                data["session_timeout"] = rules["timeout_minutes"] * 60
        
        elif policy_type == "rate_limiting":
            # Apply rate limiting policies
            if "requests_per_minute" in rules:
                data["rate_limit"] = rules["requests_per_minute"]
        
        elif policy_type == "encryption":
            # Apply encryption policies
            if "require_ssl" in rules:
                data["ssl_required"] = rules["require_ssl"]

# Global environment security manager instance
_env_security_manager = None

def get_environment_security_manager(base_path: str = "/var/lib/mingus/security") -> EnvironmentSecurityManager:
    """Get global environment security manager instance"""
    global _env_security_manager
    
    if _env_security_manager is None:
        _env_security_manager = EnvironmentSecurityManager(base_path)
    
    return _env_security_manager

def get_environment_config(environment: Environment, base_path: str = "/var/lib/mingus/security") -> EnvironmentConfig:
    """Get environment configuration"""
    manager = get_environment_security_manager(base_path)
    return manager.get_environment_config(environment)

def validate_environment_security(environment: Environment, base_path: str = "/var/lib/mingus/security") -> List[str]:
    """Validate environment security configuration"""
    manager = get_environment_security_manager(base_path)
    return manager.validate_environment_config(environment)

def get_secret(secret_id: str, environment: Environment, base_path: str = "/var/lib/mingus/security") -> Optional[str]:
    """Get secret for environment"""
    manager = get_environment_security_manager(base_path)
    return manager.get_secret(secret_id, environment)

def set_secret(secret_id: str, secret_type: SecretType, value: str, environment: Environment,
               description: str = "", expires_at: Optional[datetime] = None,
               base_path: str = "/var/lib/mingus/security") -> bool:
    """Set secret for environment"""
    manager = get_environment_security_manager(base_path)
    return manager.set_secret(secret_id, secret_type, value, environment, description, expires_at) 