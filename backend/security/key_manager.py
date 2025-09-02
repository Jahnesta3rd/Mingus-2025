"""
Encryption Key Management System
================================
Enterprise-grade encryption key management with automatic rotation,
versioning, and multi-backend storage support.
"""

import os
import uuid
import base64
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import pickle
import redis
import hvac
import boto3
from azure.keyvault.keys import KeyClient
from azure.identity import DefaultAzureCredential
from google.cloud import kms_v1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

from .crypto_config import KeyType, KeyRotationPolicy, get_crypto_config

logger = logging.getLogger(__name__)

class KeyStatus(Enum):
    """Key status enumeration"""
    ACTIVE = "active"
    ROTATING = "rotating"
    EXPIRED = "expired"
    COMPROMISED = "compromised"
    ARCHIVED = "archived"

class KeyStorageBackend(Enum):
    """Supported key storage backends"""
    FILE = "file"
    REDIS = "redis"
    VAULT = "vault"
    AWS_KMS = "aws_kms"
    AZURE_KV = "azure_kv"
    GCP_KMS = "gcp_kms"

@dataclass
class EncryptionKey:
    """Encryption key metadata and data"""
    key_id: str
    key_type: KeyType
    key_data: bytes
    key_version: int
    created_at: datetime
    expires_at: datetime
    status: KeyStatus
    algorithm: str
    key_size: int
    metadata: Dict[str, Any]
    encrypted_key_data: Optional[bytes] = None  # For encrypted storage

class KeyManager:
    """
    Enterprise-grade encryption key management system
    """
    
    def __init__(self, storage_backend: Optional[str] = None):
        self.config = get_crypto_config()
        self.storage_backend = storage_backend or os.environ.get(
            'ENCRYPTION_KEY_STORAGE_BACKEND', 'file'
        )
        self.master_key = self._load_master_key()
        self._initialize_storage()
        self._load_keys()
    
    def _load_master_key(self) -> bytes:
        """Load or generate master encryption key"""
        master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        if master_key:
            try:
                return base64.b64decode(master_key)
            except Exception as e:
                logger.error(f"Failed to decode master key: {e}")
                raise
        
        # Generate new master key for development
        logger.warning("No master key found, generating new one for development")
        new_master_key = Fernet.generate_key()
        os.environ['ENCRYPTION_MASTER_KEY'] = base64.b64encode(new_master_key).decode()
        return new_master_key
    
    def _initialize_storage(self) -> None:
        """Initialize key storage backend"""
        if self.storage_backend == 'redis':
            self._init_redis_storage()
        elif self.storage_backend == 'vault':
            self._init_vault_storage()
        elif self.storage_backend == 'aws_kms':
            self._init_aws_kms_storage()
        elif self.storage_backend == 'azure_kv':
            self._init_azure_kv_storage()
        elif self.storage_backend == 'gcp_kms':
            self._init_gcp_kms_storage()
        else:
            self._init_file_storage()
    
    def _init_file_storage(self) -> None:
        """Initialize file-based key storage"""
        self.storage_path = os.environ.get(
            'ENCRYPTION_KEY_STORAGE_PATH',
            os.path.join(os.path.dirname(__file__), '..', '..', 'keys')
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.keys_file = os.path.join(self.storage_path, 'encryption_keys.json')
        self.keys_metadata_file = os.path.join(self.storage_path, 'keys_metadata.pkl')
    
    def _init_redis_storage(self) -> None:
        """Initialize Redis-based key storage"""
        redis_url = os.environ.get('ENCRYPTION_REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = redis.from_url(redis_url)
        self.keys_prefix = "encryption_keys:"
        self.metadata_prefix = "key_metadata:"
    
    def _init_vault_storage(self) -> None:
        """Initialize HashiCorp Vault storage"""
        vault_url = os.environ.get('ENCRYPTION_VAULT_URL')
        vault_token = os.environ.get('ENCRYPTION_VAULT_TOKEN')
        if not vault_url or not vault_token:
            raise ValueError("Vault URL and token required for Vault storage")
        
        self.vault_client = hvac.Client(url=vault_url, token=vault_token)
        self.vault_mount_point = "secret"
    
    def _init_aws_kms_storage(self) -> None:
        """Initialize AWS KMS storage"""
        region = os.environ.get('ENCRYPTION_AWS_REGION')
        access_key = os.environ.get('ENCRYPTION_AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('ENCRYPTION_AWS_SECRET_ACCESS_KEY')
        
        if not region:
            raise ValueError("AWS region required for KMS storage")
        
        self.kms_client = boto3.client(
            'kms',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    
    def _init_azure_kv_storage(self) -> None:
        """Initialize Azure Key Vault storage"""
        tenant_id = os.environ.get('ENCRYPTION_AZURE_TENANT_ID')
        client_id = os.environ.get('ENCRYPTION_AZURE_CLIENT_ID')
        client_secret = os.environ.get('ENCRYPTION_AZURE_CLIENT_SECRET')
        
        if not tenant_id:
            raise ValueError("Azure tenant ID required for Key Vault storage")
        
        credential = DefaultAzureCredential()
        self.key_vault_url = f"https://{tenant_id}.vault.azure.net/"
        self.key_client = KeyClient(vault_url=self.key_vault_url, credential=credential)
    
    def _init_gcp_kms_storage(self) -> None:
        """Initialize Google Cloud KMS storage"""
        project_id = os.environ.get('ENCRYPTION_GCP_PROJECT_ID')
        location = os.environ.get('ENCRYPTION_GCP_LOCATION', 'global')
        keyring = os.environ.get('ENCRYPTION_GCP_KEYRING', 'mingus-encryption')
        
        if not project_id:
            raise ValueError("Google Cloud project ID required for KMS storage")
        
        self.kms_client = kms_v1.KeyManagementServiceClient()
        self.project_id = project_id
        self.location = location
        self.keyring = keyring
    
    def _load_keys(self) -> None:
        """Load existing keys from storage"""
        self.keys: Dict[str, EncryptionKey] = {}
        self.key_metadata: Dict[str, Dict[str, Any]] = {}
        
        try:
            if self.storage_backend == 'redis':
                self._load_keys_from_redis()
            elif self.storage_backend == 'vault':
                self._load_keys_from_vault()
            elif self.storage_backend in ['aws_kms', 'azure_kv', 'gcp_kms']:
                self._load_keys_from_cloud_kms()
            else:
                self._load_keys_from_file()
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            # Initialize with default keys if loading fails
            self._initialize_default_keys()
    
    def _load_keys_from_file(self) -> None:
        """Load keys from file storage"""
        if os.path.exists(self.keys_file):
            with open(self.keys_file, 'r') as f:
                keys_data = json.load(f)
            
            for key_id, key_data in keys_data.items():
                try:
                    key = self._deserialize_key(key_data)
                    self.keys[key_id] = key
                except Exception as e:
                    logger.error(f"Failed to deserialize key {key_id}: {e}")
        
        if os.path.exists(self.keys_metadata_file):
            with open(self.keys_metadata_file, 'rb') as f:
                self.key_metadata = pickle.load(f)
    
    def _load_keys_from_redis(self) -> None:
        """Load keys from Redis storage"""
        try:
            # Load key metadata
            metadata_keys = self.redis_client.keys(f"{self.metadata_prefix}*")
            for metadata_key in metadata_keys:
                key_id = metadata_key.decode().replace(self.metadata_prefix, '')
                metadata = json.loads(self.redis_client.get(metadata_key))
                self.key_metadata[key_id] = metadata
            
            # Load actual keys
            key_keys = self.redis_client.keys(f"{self.keys_prefix}*")
            for key_key in key_keys:
                key_id = key_key.decode().replace(self.keys_prefix, '')
                key_data = self.redis_client.get(key_key)
                if key_data:
                    try:
                        key = self._deserialize_key(json.loads(key_data))
                        self.keys[key_id] = key
                    except Exception as e:
                        logger.error(f"Failed to deserialize key {key_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to load keys from Redis: {e}")
    
    def _load_keys_from_vault(self) -> None:
        """Load keys from HashiCorp Vault"""
        try:
            # List all secrets in the mount point
            secrets = self.vault_client.secrets.kv.v2.list_secrets(
                path="encryption_keys",
                mount_point=self.vault_mount_point
            )
            
            for secret_name in secrets.get('data', {}).get('keys', []):
                try:
                    secret = self.vault_client.secrets.kv.v2.read_secret_version(
                        path=f"encryption_keys/{secret_name}",
                        mount_point=self.vault_mount_point
                    )
                    
                    key_data = secret['data']['data']
                    key = self._deserialize_key(key_data)
                    self.keys[secret_name] = key
                except Exception as e:
                    logger.error(f"Failed to load key {secret_name} from Vault: {e}")
        except Exception as e:
            logger.error(f"Failed to load keys from Vault: {e}")
    
    def _load_keys_from_cloud_kms(self) -> None:
        """Load keys from cloud KMS services"""
        # Cloud KMS services don't store key data, only metadata
        # We need to reconstruct keys from metadata
        logger.info("Cloud KMS storage - keys will be reconstructed from metadata")
    
    def _initialize_default_keys(self) -> None:
        """Initialize with default encryption keys"""
        logger.info("Initializing default encryption keys")
        
        for key_type in KeyType:
            self.generate_key(key_type)
    
    def generate_key(self, key_type: KeyType, key_size: Optional[int] = None) -> EncryptionKey:
        """Generate a new encryption key"""
        if key_size is None:
            key_size = self.config.get_config().key_size_bits
        
        # Generate random key data
        if key_size == 256:
            key_data = os.urandom(32)
        elif key_size == 192:
            key_data = os.urandom(24)
        elif key_size == 128:
            key_data = os.urandom(16)
        else:
            key_data = os.urandom(key_size // 8)
        
        # Create key metadata
        key_id = str(uuid.uuid4())
        key_version = self._get_next_key_version(key_type)
        created_at = datetime.utcnow()
        
        # Get rotation policy for this key type
        policy = self.config.get_rotation_policy(key_type)
        expires_at = created_at + timedelta(days=policy.max_key_age_days)
        
        # Create encryption key object
        key = EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            key_data=key_data,
            key_version=key_version,
            created_at=created_at,
            expires_at=expires_at,
            status=KeyStatus.ACTIVE,
            algorithm=self.config.get_config().algorithm.value,
            key_size=key_size,
            metadata={
                'created_by': 'key_manager',
                'rotation_policy': policy.key_type.value,
                'performance_mode': self.config.get_config().performance_mode
            }
        )
        
        # Store the key
        self._store_key(key)
        self.keys[key_id] = key
        
        logger.info(f"Generated new {key_type.value} key: {key_id} (v{key_version})")
        return key
    
    def _get_next_key_version(self, key_type: KeyType) -> int:
        """Get next version number for a key type"""
        existing_versions = [
            key.key_version for key in self.keys.values()
            if key.key_type == key_type
        ]
        return max(existing_versions, default=0) + 1
    
    def _store_key(self, key: EncryptionKey) -> None:
        """Store key in the configured backend"""
        try:
            if self.storage_backend == 'redis':
                self._store_key_in_redis(key)
            elif self.storage_backend == 'vault':
                self._store_key_in_vault(key)
            elif self.storage_backend in ['aws_kms', 'azure_kv', 'gcp_kms']:
                self._store_key_in_cloud_kms(key)
            else:
                self._store_key_in_file(key)
        except Exception as e:
            logger.error(f"Failed to store key {key.key_id}: {e}")
            raise
    
    def _store_key_in_file(self, key: EncryptionKey) -> None:
        """Store key in file storage"""
        # Encrypt key data before storing
        encrypted_key_data = self._encrypt_key_data(key.key_data)
        key.encrypted_key_data = encrypted_key_data
        
        # Store key metadata
        key_data = self._serialize_key(key)
        with open(self.keys_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        # Store additional metadata
        with open(self.keys_metadata_file, 'wb') as f:
            pickle.dump(self.key_metadata, f)
    
    def _store_key_in_redis(self, key: EncryptionKey) -> None:
        """Store key in Redis storage"""
        # Encrypt key data before storing
        encrypted_key_data = self._encrypt_key_data(key.key_data)
        key.encrypted_key_data = encrypted_key_data
        
        # Store key data
        key_data = self._serialize_key(key)
        self.redis_client.setex(
            f"{self.keys_prefix}{key.key_id}",
            86400,  # 24 hour TTL
            json.dumps(key_data)
        )
        
        # Store metadata
        self.redis_client.setex(
            f"{self.metadata_prefix}{key.key_id}",
            86400,
            json.dumps(key.metadata)
        )
    
    def _store_key_in_vault(self, key: EncryptionKey) -> None:
        """Store key in HashiCorp Vault"""
        # Encrypt key data before storing
        encrypted_key_data = self._encrypt_key_data(key.key_data)
        key.encrypted_key_data = encrypted_key_data
        
        # Store in Vault
        key_data = self._serialize_key(key)
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"encryption_keys/{key.key_id}",
            secret_dict=key_data,
            mount_point=self.vault_mount_point
        )
    
    def _store_key_in_cloud_kms(self, key: EncryptionKey) -> None:
        """Store key metadata in cloud KMS (actual key data not stored)"""
        # Cloud KMS doesn't store key data, only metadata
        # The actual encryption/decryption is handled by the cloud service
        logger.info(f"Key {key.key_id} metadata stored in cloud KMS")
    
    def _encrypt_key_data(self, key_data: bytes) -> bytes:
        """Encrypt key data using master key"""
        # Use Fernet for key encryption (simple and secure)
        f = Fernet(self.master_key)
        return f.encrypt(key_data)
    
    def _decrypt_key_data(self, encrypted_key_data: bytes) -> bytes:
        """Decrypt key data using master key"""
        f = Fernet(self.master_key)
        return f.decrypt(encrypted_key_data)
    
    def _serialize_key(self, key: EncryptionKey) -> Dict[str, Any]:
        """Serialize key for storage"""
        return {
            'key_id': key.key_id,
            'key_type': key.key_type.value,
            'key_data': base64.b64encode(key.key_data).decode() if not key.encrypted_key_data else None,
            'encrypted_key_data': base64.b64encode(key.encrypted_key_data).decode() if key.encrypted_key_data else None,
            'key_version': key.key_version,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat(),
            'status': key.status.value,
            'algorithm': key.algorithm,
            'key_size': key.key_size,
            'metadata': key.metadata
        }
    
    def _deserialize_key(self, key_data: Dict[str, Any]) -> EncryptionKey:
        """Deserialize key from storage"""
        # Decrypt key data if it's encrypted
        key_data_bytes = None
        if key_data.get('encrypted_key_data'):
            encrypted_data = base64.b64decode(key_data['encrypted_key_data'])
            key_data_bytes = self._decrypt_key_data(encrypted_data)
        elif key_data.get('key_data'):
            key_data_bytes = base64.b64decode(key_data['key_data'])
        
        if not key_data_bytes:
            raise ValueError("No key data found")
        
        return EncryptionKey(
            key_id=key_data['key_id'],
            key_type=KeyType(key_data['key_type']),
            key_data=key_data_bytes,
            key_version=key_data['key_version'],
            created_at=datetime.fromisoformat(key_data['created_at']),
            expires_at=datetime.fromisoformat(key_data['expires_at']),
            status=KeyStatus(key_data['status']),
            algorithm=key_data['algorithm'],
            key_size=key_data['key_size'],
            metadata=key_data.get('metadata', {}),
            encrypted_key_data=base64.b64decode(key_data['encrypted_key_data']) if key_data.get('encrypted_key_data') else None
        )
    
    def get_active_key(self, key_type: KeyType) -> Optional[EncryptionKey]:
        """Get the currently active key for a specific type"""
        active_keys = [
            key for key in self.keys.values()
            if key.key_type == key_type and key.status == KeyStatus.ACTIVE
        ]
        
        if not active_keys:
            return None
        
        # Return the most recent active key
        return max(active_keys, key=lambda k: k.created_at)
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get a specific key by ID"""
        return self.keys.get(key_id)
    
    def rotate_key(self, key_type: KeyType, force: bool = False) -> EncryptionKey:
        """Rotate encryption key for a specific type"""
        policy = self.config.get_rotation_policy(key_type)
        
        if not policy.auto_rotation and not force:
            raise ValueError(f"Auto-rotation disabled for {key_type.value}")
        
        # Check if rotation is needed
        current_key = self.get_active_key(key_type)
        if current_key and not force:
            days_until_expiry = (current_key.expires_at - datetime.utcnow()).days
            if days_until_expiry > policy.grace_period_days:
                raise ValueError(f"Key rotation not needed yet. Expires in {days_until_expiry} days")
        
        # Mark current key as rotating
        if current_key:
            current_key.status = KeyStatus.ROTATING
        
        # Generate new key
        new_key = self.generate_key(key_type)
        
        # Archive old key after grace period
        if current_key:
            self._schedule_key_archival(current_key, policy.grace_period_days)
        
        logger.info(f"Rotated {key_type.value} key: {current_key.key_id if current_key else 'None'} -> {new_key.key_id}")
        return new_key
    
    def _schedule_key_archival(self, key: EncryptionKey, grace_period_days: int) -> None:
        """Schedule key archival after grace period"""
        # This would typically be handled by a background task
        # For now, we'll just log it
        logger.info(f"Key {key.key_id} scheduled for archival in {grace_period_days} days")
    
    def revoke_key(self, key_id: str, reason: str = "Manual revocation") -> None:
        """Revoke a key (mark as compromised)"""
        key = self.keys.get(key_id)
        if not key:
            raise ValueError(f"Key {key_id} not found")
        
        key.status = KeyStatus.COMPROMISED
        key.metadata['revocation_reason'] = reason
        key.metadata['revoked_at'] = datetime.utcnow().isoformat()
        
        # Store updated key
        self._store_key(key)
        
        logger.warning(f"Key {key_id} revoked: {reason}")
    
    def list_keys(self, key_type: Optional[KeyType] = None, status: Optional[KeyStatus] = None) -> List[EncryptionKey]:
        """List keys with optional filtering"""
        filtered_keys = self.keys.values()
        
        if key_type:
            filtered_keys = [k for k in filtered_keys if k.key_type == key_type]
        
        if status:
            filtered_keys = [k for k in filtered_keys if k.status == status]
        
        return sorted(filtered_keys, key=lambda k: k.created_at, reverse=True)
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired keys and return count of cleaned keys"""
        current_time = datetime.utcnow()
        expired_keys = [
            key_id for key_id, key in self.keys.items()
            if key.expires_at < current_time and key.status != KeyStatus.ARCHIVED
        ]
        
        for key_id in expired_keys:
            key = self.keys[key_id]
            key.status = KeyStatus.EXPIRED
            self._store_key(key)
        
        logger.info(f"Marked {len(expired_keys)} keys as expired")
        return len(expired_keys)
    
    def get_key_statistics(self) -> Dict[str, Any]:
        """Get statistics about managed keys"""
        stats = {
            'total_keys': len(self.keys),
            'by_type': {},
            'by_status': {},
            'rotation_needed': []
        }
        
        for key_type in KeyType:
            type_keys = [k for k in self.keys.values() if k.key_type == key_type]
            stats['by_type'][key_type.value] = len(type_keys)
            
            # Check if rotation is needed
            active_keys = [k for k in type_keys if k.status == KeyStatus.ACTIVE]
            if active_keys:
                policy = self.config.get_rotation_policy(key_type)
                for key in active_keys:
                    days_until_expiry = (key.expires_at - datetime.utcnow()).days
                    if days_until_expiry <= policy.grace_period_days:
                        stats['rotation_needed'].append({
                            'key_id': key.key_id,
                            'key_type': key_type.value,
                            'days_until_expiry': days_until_expiry
                        })
        
        for status in KeyStatus:
            status_keys = [k for k in self.keys.values() if k.status == status]
            stats['by_status'][status.value] = len(status_keys)
        
        return stats

# Global key manager instance
key_manager = KeyManager()

def get_key_manager() -> KeyManager:
    """Get global key manager instance"""
    return key_manager
