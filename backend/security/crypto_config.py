"""
Encryption Configuration Management
==================================
Manages encryption settings, key rotation policies, and environment variables
for the Mingus Flask finance application.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    CHACHA20_POLY1305 = "CHACHA20-POLY1305"
    FERNET = "FERNET"  # Legacy support

class KeyType(Enum):
    """Types of encryption keys"""
    FINANCIAL_DATA = "financial_data"
    PII = "pii"
    SESSION = "session"
    API_KEYS = "api_keys"
    AUDIT_LOGS = "audit_logs"

@dataclass
class KeyRotationPolicy:
    """Configuration for key rotation policies"""
    key_type: KeyType
    rotation_interval_days: int
    max_key_age_days: int
    grace_period_days: int
    auto_rotation: bool
    batch_size: int  # Number of records to process per rotation batch

@dataclass
class EncryptionConfig:
    """Main encryption configuration"""
    algorithm: EncryptionAlgorithm
    key_size_bits: int
    iv_size_bytes: int
    tag_size_bytes: int
    compression_enabled: bool
    performance_mode: str  # 'security', 'balanced', 'performance'

class CryptoConfigManager:
    """
    Manages encryption configuration and environment variables
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'encryption.json'
        )
        self._config = None
        self._rotation_policies = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or use defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self._config = self._parse_config(config_data)
                self._rotation_policies = self._parse_rotation_policies(config_data)
                logger.info(f"Loaded encryption config from {self.config_path}")
            else:
                self._config = self._get_default_config()
                self._rotation_policies = self._get_default_rotation_policies()
                logger.info("Using default encryption configuration")
        except Exception as e:
            logger.error(f"Failed to load encryption config: {e}")
            self._config = self._get_default_config()
            self._rotation_policies = self._get_default_rotation_policies()
    
    def _parse_config(self, config_data: Dict[str, Any]) -> EncryptionConfig:
        """Parse configuration from JSON data"""
        try:
            algorithm = EncryptionAlgorithm(config_data.get('algorithm', 'AES_256_GCM'))
            return EncryptionConfig(
                algorithm=algorithm,
                key_size_bits=config_data.get('key_size_bits', 256),
                iv_size_bytes=config_data.get('iv_size_bytes', 16),
                tag_size_bytes=config_data.get('tag_size_bytes', 16),
                compression_enabled=config_data.get('compression_enabled', False),
                performance_mode=config_data.get('performance_mode', 'balanced')
            )
        except Exception as e:
            logger.error(f"Failed to parse encryption config: {e}")
            return self._get_default_config()
    
    def _parse_rotation_policies(self, config_data: Dict[str, Any]) -> Dict[KeyType, KeyRotationPolicy]:
        """Parse rotation policies from JSON data"""
        policies = {}
        try:
            for policy_data in config_data.get('rotation_policies', []):
                key_type = KeyType(policy_data['key_type'])
                policies[key_type] = KeyRotationPolicy(
                    key_type=key_type,
                    rotation_interval_days=policy_data.get('rotation_interval_days', 90),
                    max_key_age_days=policy_data.get('max_key_age_days', 365),
                    grace_period_days=policy_data.get('grace_period_days', 30),
                    auto_rotation=policy_data.get('auto_rotation', True),
                    batch_size=policy_data.get('batch_size', 1000)
                )
        except Exception as e:
            logger.error(f"Failed to parse rotation policies: {e}")
        
        # Ensure all key types have policies
        for key_type in KeyType:
            if key_type not in policies:
                policies[key_type] = self._get_default_policy(key_type)
        
        return policies
    
    def _get_default_config(self) -> EncryptionConfig:
        """Get default encryption configuration"""
        return EncryptionConfig(
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            key_size_bits=256,
            iv_size_bytes=16,
            tag_size_bytes=16,
            compression_enabled=False,
            performance_mode='balanced'
        )
    
    def _get_default_rotation_policies(self) -> Dict[KeyType, KeyRotationPolicy]:
        """Get default rotation policies for all key types"""
        policies = {}
        for key_type in KeyType:
            policies[key_type] = self._get_default_policy(key_type)
        return policies
    
    def _get_default_policy(self, key_type: KeyType) -> KeyRotationPolicy:
        """Get default policy for a specific key type"""
        if key_type == KeyType.FINANCIAL_DATA:
            return KeyRotationPolicy(
                key_type=key_type,
                rotation_interval_days=90,  # 3 months
                max_key_age_days=365,       # 1 year
                grace_period_days=30,       # 1 month grace
                auto_rotation=True,
                batch_size=500
            )
        elif key_type == KeyType.PII:
            return KeyRotationPolicy(
                key_type=key_type,
                rotation_interval_days=180,  # 6 months
                max_key_age_days=730,        # 2 years
                grace_period_days=60,        # 2 months grace
                auto_rotation=True,
                batch_size=1000
            )
        elif key_type == KeyType.SESSION:
            return KeyRotationPolicy(
                key_type=key_type,
                rotation_interval_days=30,   # 1 month
                max_key_age_days=90,         # 3 months
                grace_period_days=7,         # 1 week grace
                auto_rotation=True,
                batch_size=2000
            )
        else:
            return KeyRotationPolicy(
                key_type=key_type,
                rotation_interval_days=90,
                max_key_age_days=365,
                grace_period_days=30,
                auto_rotation=True,
                batch_size=1000
            )
    
    def get_config(self) -> EncryptionConfig:
        """Get current encryption configuration"""
        return self._config
    
    def get_rotation_policy(self, key_type: KeyType) -> KeyRotationPolicy:
        """Get rotation policy for a specific key type"""
        return self._rotation_policies.get(key_type)
    
    def get_all_rotation_policies(self) -> Dict[KeyType, KeyRotationPolicy]:
        """Get all rotation policies"""
        return self._rotation_policies.copy()
    
    def update_config(self, new_config: EncryptionConfig) -> None:
        """Update encryption configuration"""
        self._config = new_config
        self._save_config()
    
    def update_rotation_policy(self, key_type: KeyType, policy: KeyRotationPolicy) -> None:
        """Update rotation policy for a specific key type"""
        self._rotation_policies[key_type] = policy
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            os.makedirs(config_dir, exist_ok=True)
            
            config_data = {
                'algorithm': self._config.algorithm.value,
                'key_size_bits': self._config.key_size_bits,
                'iv_size_bytes': self._config.iv_size_bytes,
                'tag_size_bytes': self._config.tag_size_bytes,
                'compression_enabled': self._config.compression_enabled,
                'performance_mode': self._config.performance_mode,
                'rotation_policies': [
                    {
                        'key_type': policy.key_type.value,
                        'rotation_interval_days': policy.rotation_interval_days,
                        'max_key_age_days': policy.max_key_age_days,
                        'grace_period_days': policy.grace_period_days,
                        'auto_rotation': policy.auto_rotation,
                        'batch_size': policy.batch_size
                    }
                    for policy in self._rotation_policies.values()
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved encryption config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save encryption config: {e}")
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get required environment variables for encryption"""
        return {
            'ENCRYPTION_MASTER_KEY': 'Master encryption key (base64 encoded)',
            'ENCRYPTION_KEY_ID': 'Current active encryption key ID',
            'ENCRYPTION_KEY_VERSION': 'Current encryption key version',
            'ENCRYPTION_KEY_ROTATION_ENABLED': 'Enable/disable automatic key rotation (true/false)',
            'ENCRYPTION_KEY_STORAGE_BACKEND': 'Key storage backend (file, redis, vault, aws_kms, azure_kv, gcp_kms)',
            'ENCRYPTION_KEY_STORAGE_PATH': 'Path for file-based key storage',
            'ENCRYPTION_REDIS_URL': 'Redis URL for key storage',
            'ENCRYPTION_VAULT_URL': 'HashiCorp Vault URL',
            'ENCRYPTION_VAULT_TOKEN': 'Vault authentication token',
            'ENCRYPTION_AWS_REGION': 'AWS region for KMS',
            'ENCRYPTION_AWS_ACCESS_KEY_ID': 'AWS access key ID',
            'ENCRYPTION_AWS_SECRET_ACCESS_KEY': 'AWS secret access key',
            'ENCRYPTION_AZURE_TENANT_ID': 'Azure tenant ID',
            'ENCRYPTION_AZURE_CLIENT_ID': 'Azure client ID',
            'ENCRYPTION_AZURE_CLIENT_SECRET': 'Azure client secret',
            'ENCRYPTION_GCP_PROJECT_ID': 'Google Cloud project ID',
            'ENCRYPTION_GCP_LOCATION': 'Google Cloud KMS location',
            'ENCRYPTION_GCP_KEYRING': 'Google Cloud KMS keyring'
        }
    
    def validate_environment(self) -> List[str]:
        """Validate that required environment variables are set"""
        errors = []
        required_vars = ['ENCRYPTION_MASTER_KEY', 'ENCRYPTION_KEY_ID']
        
        for var in required_vars:
            if not os.environ.get(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate key storage backend configuration
        backend = os.environ.get('ENCRYPTION_KEY_STORAGE_BACKEND', 'file')
        if backend == 'redis' and not os.environ.get('ENCRYPTION_REDIS_URL'):
            errors.append("Redis backend requires ENCRYPTION_REDIS_URL")
        elif backend == 'vault' and not os.environ.get('ENCRYPTION_VAULT_URL'):
            errors.append("Vault backend requires ENCRYPTION_VAULT_URL")
        elif backend == 'aws_kms' and not os.environ.get('ENCRYPTION_AWS_REGION'):
            errors.append("AWS KMS backend requires ENCRYPTION_AWS_REGION")
        elif backend == 'azure_kv' and not os.environ.get('ENCRYPTION_AZURE_TENANT_ID'):
            errors.append("Azure Key Vault backend requires ENCRYPTION_AZURE_TENANT_ID")
        elif backend == 'gcp_kms' and not os.environ.get('ENCRYPTION_GCP_PROJECT_ID'):
            errors.append("Google Cloud KMS backend requires ENCRYPTION_GCP_PROJECT_ID")
        
        return errors
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-optimized settings based on current mode"""
        mode = self._config.performance_mode
        
        if mode == 'security':
            return {
                'use_hardware_acceleration': True,
                'key_derivation_iterations': 100000,
                'memory_cost': 65536,
                'parallel_factor': 4,
                'cache_encrypted_data': False
            }
        elif mode == 'performance':
            return {
                'use_hardware_acceleration': True,
                'key_derivation_iterations': 10000,
                'memory_cost': 16384,
                'parallel_factor': 1,
                'cache_encrypted_data': True
            }
        else:  # balanced
            return {
                'use_hardware_acceleration': True,
                'key_derivation_iterations': 50000,
                'memory_cost': 32768,
                'parallel_factor': 2,
                'cache_encrypted_data': True
            }

# Global configuration instance
crypto_config = CryptoConfigManager()

def get_crypto_config() -> CryptoConfigManager:
    """Get global crypto configuration instance"""
    return crypto_config
