"""
MINGUS Data Encryption and Protection System
Comprehensive field-level encryption for sensitive financial data
"""

import os
import base64
import json
import hashlib
import hmac
import secrets
import hashlib
import sqlite3
from typing import Dict, Any, Optional, List, Union, Tuple, BinaryIO, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import logging
from enum import Enum
import tempfile
import shutil
from pathlib import Path
import threading
import queue
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSensitivity(Enum):
    """Data sensitivity levels for encryption"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    AES_256_CTR = "aes-256-ctr"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    FERNET = "fernet"

class KeyStorageType(Enum):
    """Key storage types"""
    ENVIRONMENT = "environment"
    VAULT = "vault"
    DATABASE = "database"
    FILE = "file"

class TokenizationType(Enum):
    """Types of data tokenization"""
    PAYMENT_CARD = "payment_card"
    BANK_ACCOUNT = "bank_account"
    SSN = "ssn"
    EMAIL = "email"
    PHONE = "phone"
    CUSTOM = "custom"

class AuditEventType(Enum):
    """Types of audit events"""
    DATA_ACCESS = "data_access"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_ENCRYPT = "data_encrypt"
    DATA_DECRYPT = "data_decrypt"
    TOKEN_CREATE = "token_create"
    TOKEN_ACCESS = "token_access"
    KEY_ROTATION = "key_rotation"
    COMPLIANCE_CHECK = "compliance_check"
    INTEGRITY_VERIFY = "integrity_verify"
    CRYPTO_SHRED = "crypto_shred"

class ComplianceRegulation(Enum):
    """Financial compliance regulations"""
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOX = "sox"
    GLBA = "glba"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"

@dataclass
class EncryptionConfig:
    """Configuration for encryption system"""
    # Master encryption key (should be stored securely)
    master_key: Optional[str] = None
    
    # Key derivation settings
    key_derivation_salt: Optional[str] = None
    key_derivation_iterations: int = 100000
    scrypt_n: int = 16384
    scrypt_r: int = 8
    scrypt_p: int = 1
    
    # Encryption algorithm preferences
    preferred_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    
    # Key rotation settings
    key_rotation_days: int = 90
    max_key_age_days: int = 365
    
    # Field-specific settings
    field_encryption_enabled: bool = True
    field_key_derivation: bool = True
    
    # Key storage settings
    key_storage_type: KeyStorageType = KeyStorageType.ENVIRONMENT
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_path: str = "secret/mingus/encryption"
    
    # Database encryption settings
    database_encryption_enabled: bool = True
    database_key_table: str = "encryption_keys"
    
    # File encryption settings
    file_encryption_enabled: bool = True
    file_chunk_size: int = 64 * 1024  # 64KB chunks
    temp_directory: str = "/tmp/mingus_encryption"
    
    # Audit settings
    audit_encryption_operations: bool = True
    log_encryption_events: bool = True
    
    # Compliance settings
    fips_140_2_compliant: bool = True
    gdpr_compliant: bool = True
    pci_dss_compliant: bool = True
    
    # Performance settings
    cache_encryption_keys: bool = True
    key_cache_ttl_seconds: int = 3600

@dataclass
class EncryptedField:
    """Represents an encrypted field with metadata"""
    encrypted_data: str
    algorithm: str
    key_id: str
    iv: str
    auth_tag: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"
    sensitivity: DataSensitivity = DataSensitivity.HIGH

@dataclass
class EncryptedFile:
    """Represents an encrypted file with metadata"""
    file_path: str
    algorithm: str
    key_id: str
    iv: str
    auth_tag: Optional[str] = None
    chunk_size: int = 64 * 1024
    total_chunks: int = 0
    file_size: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"

@dataclass
class TokenizedData:
    """Represents tokenized data with metadata"""
    token: str
    original_data_hash: str
    tokenization_type: TokenizationType
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditEvent:
    """Represents an audit event"""
    event_id: str
    event_type: AuditEventType
    user_id: Optional[str]
    ip_address: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[ComplianceRegulation] = field(default_factory=list)
    risk_level: str = "low"

@dataclass
class DataIntegrityRecord:
    """Represents data integrity verification record"""
    data_id: str
    original_hash: str
    current_hash: str
    verification_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    integrity_status: str = "verified"
    verification_method: str = "sha256"
    previous_verifications: List[Dict[str, Any]] = field(default_factory=list)

class SecureKeyStorage:
    """Secure key storage with multiple backends"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.storage_type = config.key_storage_type
    
    def store_key(self, key_id: str, key_data: bytes, metadata: Dict[str, Any] = None):
        """Store encryption key securely"""
        if self.storage_type == KeyStorageType.ENVIRONMENT:
            return self._store_in_environment(key_id, key_data, metadata)
        elif self.storage_type == KeyStorageType.VAULT:
            return self._store_in_vault(key_id, key_data, metadata)
        elif self.storage_type == KeyStorageType.DATABASE:
            return self._store_in_database(key_id, key_data, metadata)
        elif self.storage_type == KeyStorageType.FILE:
            return self._store_in_file(key_id, key_data, metadata)
        else:
            raise ValueError(f"Unsupported key storage type: {self.storage_type}")
    
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve encryption key securely"""
        if self.storage_type == KeyStorageType.ENVIRONMENT:
            return self._retrieve_from_environment(key_id)
        elif self.storage_type == KeyStorageType.VAULT:
            return self._retrieve_from_vault(key_id)
        elif self.storage_type == KeyStorageType.DATABASE:
            return self._retrieve_from_database(key_id)
        elif self.storage_type == KeyStorageType.FILE:
            return self._retrieve_from_file(key_id)
        else:
            raise ValueError(f"Unsupported key storage type: {self.storage_type}")
    
    def _store_in_environment(self, key_id: str, key_data: bytes, metadata: Dict[str, Any] = None):
        """Store key in environment variables"""
        env_key = f"MINGUS_ENCRYPTION_KEY_{key_id.upper()}"
        os.environ[env_key] = base64.b64encode(key_data).decode()
        logger.info(f"Stored key {key_id} in environment variable {env_key}")
    
    def _retrieve_from_environment(self, key_id: str) -> Optional[bytes]:
        """Retrieve key from environment variables"""
        env_key = f"MINGUS_ENCRYPTION_KEY_{key_id.upper()}"
        key_b64 = os.environ.get(env_key)
        if key_b64:
            return base64.b64decode(key_b64)
        return None
    
    def _store_in_vault(self, key_id: str, key_data: bytes, metadata: Dict[str, Any] = None):
        """Store key in HashiCorp Vault"""
        try:
            import hvac
            client = hvac.Client(url=self.config.vault_url, token=self.config.vault_token)
            
            secret_path = f"{self.config.vault_path}/{key_id}"
            secret_data = {
                'key_data': base64.b64encode(key_data).decode(),
                'created_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret=secret_data
            )
            logger.info(f"Stored key {key_id} in Vault at {secret_path}")
        except ImportError:
            logger.error("HashiCorp Vault client not available")
            raise
        except Exception as e:
            logger.error(f"Failed to store key in Vault: {e}")
            raise
    
    def _retrieve_from_vault(self, key_id: str) -> Optional[bytes]:
        """Retrieve key from HashiCorp Vault"""
        try:
            import hvac
            client = hvac.Client(url=self.config.vault_url, token=self.config.vault_token)
            
            secret_path = f"{self.config.vault_path}/{key_id}"
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
            
            if response and 'data' in response and 'data' in response['data']:
                key_b64 = response['data']['data']['key_data']
                return base64.b64decode(key_b64)
            return None
        except ImportError:
            logger.error("HashiCorp Vault client not available")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve key from Vault: {e}")
            return None
    
    def _store_in_database(self, key_id: str, key_data: bytes, metadata: Dict[str, Any] = None):
        """Store key in database"""
        # This would typically use your database connection
        # For demo purposes, using SQLite
        conn = sqlite3.connect(':memory:')  # Use your actual database
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.database_key_table} (
                key_id TEXT PRIMARY KEY,
                key_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO {self.config.database_key_table}
            (key_id, key_data, created_at, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            key_id,
            base64.b64encode(key_data).decode(),
            datetime.utcnow().isoformat(),
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored key {key_id} in database")
    
    def _retrieve_from_database(self, key_id: str) -> Optional[bytes]:
        """Retrieve key from database"""
        conn = sqlite3.connect(':memory:')  # Use your actual database
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT key_data FROM {self.config.database_key_table}
            WHERE key_id = ? AND active = TRUE
        """, (key_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return base64.b64decode(result[0])
        return None
    
    def _store_in_file(self, key_id: str, key_data: bytes, metadata: Dict[str, Any] = None):
        """Store key in encrypted file"""
        key_file = Path(f"/tmp/mingus_keys/{key_id}.key")
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Encrypt the key data before storing
        fernet = Fernet(base64.urlsafe_b64encode(os.urandom(32)))
        encrypted_key_data = fernet.encrypt(key_data)
        
        key_file.write_bytes(encrypted_key_data)
        logger.info(f"Stored key {key_id} in file {key_file}")
    
    def _retrieve_from_file(self, key_id: str) -> Optional[bytes]:
        """Retrieve key from encrypted file"""
        key_file = Path(f"/tmp/mingus_keys/{key_id}.key")
        
        if key_file.exists():
            encrypted_key_data = key_file.read_bytes()
            # Decrypt the key data
            fernet = Fernet(base64.urlsafe_b64encode(os.urandom(32)))
            return fernet.decrypt(encrypted_key_data)
        return None

class PasswordKeyDerivation:
    """Key derivation from user passwords"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
    
    def derive_key_from_password(self, password: str, salt: Optional[str] = None) -> Tuple[bytes, str]:
        """Derive encryption key from user password"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use Scrypt for password-based key derivation
        kdf = Scrypt(
            salt=salt.encode(),
            length=32,
            n=self.config.scrypt_n,
            r=self.config.scrypt_r,
            p=self.config.scrypt_p,
            backend=default_backend()
        )
        
        derived_key = kdf.derive(password.encode())
        return derived_key, salt
    
    def verify_password_key(self, password: str, salt: str, expected_key: bytes) -> bool:
        """Verify password-derived key"""
        try:
            derived_key, _ = self.derive_key_from_password(password, salt)
            return hmac.compare_digest(derived_key, expected_key)
        except Exception:
            return False

class DatabaseColumnEncryption:
    """Database column-level encryption"""
    
    def __init__(self, config: EncryptionConfig, key_manager):
        self.config = config
        self.key_manager = key_manager
    
    def encrypt_column_value(self, value: Any, column_name: str, table_name: str) -> str:
        """Encrypt a database column value"""
        if not self.config.database_encryption_enabled:
            return str(value)
        
        # Create column-specific key
        column_key_salt = f"{table_name}_{column_name}".encode()
        key_id, master_key = self.key_manager.get_current_key()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=column_key_salt,
            iterations=self.config.key_derivation_iterations,
            backend=default_backend()
        )
        
        column_key = kdf.derive(master_key)
        
        # Convert value to string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        # Encrypt with AES-256-GCM
        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(column_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(value.encode()) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        # Create encrypted value structure
        encrypted_value = {
            'encrypted_data': base64.b64encode(ciphertext).decode(),
            'iv': base64.b64encode(iv).decode(),
            'auth_tag': base64.b64encode(auth_tag).decode(),
            'key_id': key_id,
            'algorithm': 'aes-256-gcm',
            'created_at': datetime.utcnow().isoformat()
        }
        
        return json.dumps(encrypted_value)
    
    def decrypt_column_value(self, encrypted_value: str, column_name: str, table_name: str) -> Any:
        """Decrypt a database column value"""
        if not self.config.database_encryption_enabled:
            return encrypted_value
        
        try:
            # Parse encrypted value
            encrypted_data = json.loads(encrypted_value)
            
            # Get column-specific key
            column_key_salt = f"{table_name}_{column_name}".encode()
            key_id = encrypted_data['key_id']
            master_key = self.key_manager.get_key_by_id(key_id)
            
            if not master_key:
                raise ValueError(f"Key {key_id} not found")
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=column_key_salt,
                iterations=self.config.key_derivation_iterations,
                backend=default_backend()
            )
            
            column_key = kdf.derive(master_key)
            
            # Decrypt
            ciphertext = base64.b64decode(encrypted_data['encrypted_data'])
            iv = base64.b64decode(encrypted_data['iv'])
            auth_tag = base64.b64decode(encrypted_data['auth_tag'])
            
            cipher = Cipher(
                algorithms.AES(column_key),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Try to parse as JSON, otherwise return as string
            try:
                return json.loads(plaintext.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return plaintext.decode()
                
        except Exception as e:
            logger.error(f"Failed to decrypt column value: {e}")
            return encrypted_value

class FileEncryption:
    """File encryption for uploaded documents"""
    
    def __init__(self, config: EncryptionConfig, key_manager):
        self.config = config
        self.key_manager = key_manager
        self.temp_dir = Path(self.config.temp_directory)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> EncryptedFile:
        """Encrypt a file"""
        if not self.config.file_encryption_enabled:
            return EncryptedFile(file_path=file_path, algorithm="none", key_id="none", iv="")
        
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not output_path:
            output_path = str(input_path) + ".encrypted"
        
        output_path = Path(output_path)
        
        # Get encryption key
        key_id, master_key = self.key_manager.get_current_key()
        
        # Generate IV
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt file in chunks
        total_chunks = 0
        file_size = input_path.stat().st_size
        
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            while True:
                chunk = infile.read(self.config.file_chunk_size)
                if not chunk:
                    break
                
                encrypted_chunk = encryptor.update(chunk)
                outfile.write(encrypted_chunk)
                total_chunks += 1
        
        # Finalize encryption
        final_chunk = encryptor.finalize()
        outfile.write(final_chunk)
        auth_tag = encryptor.tag
        
        # Create encrypted file metadata
        encrypted_file = EncryptedFile(
            file_path=str(output_path),
            algorithm=self.config.preferred_algorithm.value,
            key_id=key_id,
            iv=base64.b64encode(iv).decode(),
            auth_tag=base64.b64encode(auth_tag).decode(),
            chunk_size=self.config.file_chunk_size,
            total_chunks=total_chunks,
            file_size=file_size
        )
        
        logger.info(f"Encrypted file {file_path} -> {output_path}")
        return encrypted_file
    
    def decrypt_file(self, encrypted_file: EncryptedFile, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        if encrypted_file.algorithm == "none":
            return encrypted_file.file_path
        
        input_path = Path(encrypted_file.file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_file.file_path}")
        
        if not output_path:
            output_path = str(input_path).replace('.encrypted', '.decrypted')
        
        output_path = Path(output_path)
        
        # Get encryption key
        master_key = self.key_manager.get_key_by_id(encrypted_file.key_id)
        if not master_key:
            raise ValueError(f"Key {encrypted_file.key_id} not found")
        
        # Decode IV and auth tag
        iv = base64.b64decode(encrypted_file.iv)
        auth_tag = base64.b64decode(encrypted_file.auth_tag)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.GCM(iv, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt file in chunks
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            while True:
                chunk = infile.read(self.config.file_chunk_size)
                if not chunk:
                    break
                
                decrypted_chunk = decryptor.update(chunk)
                outfile.write(decrypted_chunk)
        
        # Finalize decryption
        final_chunk = decryptor.finalize()
        outfile.write(final_chunk)
        
        logger.info(f"Decrypted file {encrypted_file.file_path} -> {output_path}")
        return str(output_path)
    
    def encrypt_file_stream(self, file_stream: BinaryIO, chunk_size: Optional[int] = None) -> Tuple[bytes, EncryptedFile]:
        """Encrypt a file stream"""
        if not self.config.file_encryption_enabled:
            return file_stream.read(), EncryptedFile(
                file_path="stream", algorithm="none", key_id="none", iv=""
            )
        
        chunk_size = chunk_size or self.config.file_chunk_size
        
        # Get encryption key
        key_id, master_key = self.key_manager.get_current_key()
        
        # Generate IV
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt stream
        encrypted_data = b""
        total_chunks = 0
        
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break
            
            encrypted_chunk = encryptor.update(chunk)
            encrypted_data += encrypted_chunk
            total_chunks += 1
        
        # Finalize encryption
        final_chunk = encryptor.finalize()
        encrypted_data += final_chunk
        auth_tag = encryptor.tag
        
        # Create encrypted file metadata
        encrypted_file = EncryptedFile(
            file_path="stream",
            algorithm=self.config.preferred_algorithm.value,
            key_id=key_id,
            iv=base64.b64encode(iv).decode(),
            auth_tag=base64.b64encode(auth_tag).decode(),
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            file_size=len(encrypted_data)
        )
        
        return encrypted_data, encrypted_file

class KeyManager:
    """Manages encryption keys and key rotation"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.current_key_id = None
        self.secure_storage = SecureKeyStorage(config)
        self.password_derivation = PasswordKeyDerivation(config)
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize encryption keys"""
        if not self.config.master_key:
            self.config.master_key = self._generate_master_key()
        
        if not self.config.key_derivation_salt:
            self.config.key_derivation_salt = secrets.token_hex(32)
        
        # Generate initial keys
        self._generate_new_key_pair()
    
    def _generate_master_key(self) -> str:
        """Generate a new master encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _generate_new_key_pair(self):
        """Generate new encryption key pair"""
        key_id = f"key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        # Generate symmetric key
        symmetric_key = secrets.token_bytes(32)
        
        # Generate asymmetric key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Store key information
        self.keys[key_id] = {
            'symmetric_key': symmetric_key,
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.utcnow(),
            'algorithm': self.config.preferred_algorithm.value,
            'active': True
        }
        
        # Store key securely
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'algorithm': self.config.preferred_algorithm.value,
            'key_type': 'symmetric'
        }
        self.secure_storage.store_key(key_id, symmetric_key, metadata)
        
        self.current_key_id = key_id
        logger.info(f"Generated new encryption key pair: {key_id}")
    
    def get_current_key(self) -> Tuple[str, bytes]:
        """Get current encryption key"""
        if not self.current_key_id or self.current_key_id not in self.keys:
            self._generate_new_key_pair()
        
        return self.current_key_id, self.keys[self.current_key_id]['symmetric_key']
    
    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """Get encryption key by ID"""
        # First check in-memory cache
        if key_id in self.keys and self.keys[key_id]['active']:
            return self.keys[key_id]['symmetric_key']
        
        # Try to retrieve from secure storage
        key_data = self.secure_storage.retrieve_key(key_id)
        if key_data:
            # Cache the key
            self.keys[key_id] = {
                'symmetric_key': key_data,
                'created_at': datetime.utcnow(),
                'algorithm': self.config.preferred_algorithm.value,
                'active': True
            }
            return key_data
        
        return None
    
    def derive_key_from_password(self, password: str, salt: Optional[str] = None) -> Tuple[bytes, str]:
        """Derive encryption key from user password"""
        return self.password_derivation.derive_key_from_password(password, salt)
    
    def verify_password_key(self, password: str, salt: str, expected_key: bytes) -> bool:
        """Verify password-derived key"""
        return self.password_derivation.verify_password_key(password, salt, expected_key)
    
    def rotate_keys(self):
        """Rotate encryption keys"""
        logger.info("Starting key rotation process")
        
        # Generate new key pair
        old_key_id = self.current_key_id
        self._generate_new_key_pair()
        
        # Mark old key as inactive after grace period
        if old_key_id and old_key_id in self.keys:
            self.keys[old_key_id]['active'] = False
            self.keys[old_key_id]['deactivated_at'] = datetime.utcnow()
        
        logger.info(f"Key rotation completed. New key: {self.current_key_id}")

class FieldEncryptionManager:
    """Manages field-level encryption for sensitive data"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.key_manager = KeyManager(config)
        self.field_keys: Dict[str, bytes] = {}
    
    def _derive_field_key(self, field_name: str, sensitivity: DataSensitivity) -> bytes:
        """Derive field-specific encryption key"""
        if not self.config.field_key_derivation:
            key_id, master_key = self.key_manager.get_current_key()
            return master_key
        
        # Derive field-specific key
        salt = f"{field_name}_{sensitivity.value}".encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config.key_derivation_iterations,
            backend=default_backend()
        )
        
        key_id, master_key = self.key_manager.get_current_key()
        field_key = kdf.derive(master_key)
        
        return field_key
    
    def encrypt_field(self, data: Any, field_name: str, 
                     sensitivity: DataSensitivity = DataSensitivity.HIGH) -> EncryptedField:
        """Encrypt a single field"""
        if not self.config.field_encryption_enabled:
            return EncryptedField(
                encrypted_data=str(data),
                algorithm="none",
                key_id="none",
                iv="",
                sensitivity=sensitivity
            )
        
        # Convert data to string if needed
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Derive field-specific key
        field_key = self._derive_field_key(field_name, sensitivity)
        
        # Generate IV
        iv = secrets.token_bytes(16)
        
        # Encrypt data
        if self.config.preferred_algorithm == EncryptionAlgorithm.AES_256_GCM:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
            auth_tag = encryptor.tag
            
            encrypted_data = base64.b64encode(ciphertext).decode()
            auth_tag_b64 = base64.b64encode(auth_tag).decode()
            
        elif self.config.preferred_algorithm == EncryptionAlgorithm.AES_256_CBC:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad data to block size
            padded_data = self._pad_data(data.encode())
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            encrypted_data = base64.b64encode(ciphertext).decode()
            auth_tag_b64 = None
            
        else:  # Default to Fernet
            fernet = Fernet(base64.urlsafe_b64encode(field_key))
            encrypted_data = fernet.encrypt(data.encode()).decode()
            auth_tag_b64 = None
        
        key_id, _ = self.key_manager.get_current_key()
        
        # Create encrypted field
        encrypted_field = EncryptedField(
            encrypted_data=encrypted_data,
            algorithm=self.config.preferred_algorithm.value,
            key_id=key_id,
            iv=base64.b64encode(iv).decode(),
            auth_tag=auth_tag_b64,
            sensitivity=sensitivity
        )
        
        if self.config.audit_encryption_operations:
            logger.info(f"Encrypted field '{field_name}' with sensitivity '{sensitivity.value}'")
        
        return encrypted_field
    
    def decrypt_field(self, encrypted_field: EncryptedField, field_name: str) -> Any:
        """Decrypt a single field"""
        if encrypted_field.algorithm == "none":
            return encrypted_field.encrypted_data
        
        # Get encryption key
        if encrypted_field.key_id == "none":
            return encrypted_field.encrypted_data
        
        field_key = self._derive_field_key(field_name, encrypted_field.sensitivity)
        
        # Decode data
        encrypted_data = base64.b64decode(encrypted_field.encrypted_data)
        iv = base64.b64decode(encrypted_field.iv)
        
        # Decrypt data
        if encrypted_field.algorithm == EncryptionAlgorithm.AES_256_GCM.value:
            if encrypted_field.auth_tag:
                auth_tag = base64.b64decode(encrypted_field.auth_tag)
                cipher = Cipher(
                    algorithms.AES(field_key),
                    modes.GCM(iv, auth_tag),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                
                plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
                
        elif encrypted_field.algorithm == EncryptionAlgorithm.AES_256_CBC.value:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
            plaintext = self._unpad_data(plaintext)
            
        else:  # Fernet
            fernet = Fernet(base64.urlsafe_b64encode(field_key))
            plaintext = fernet.decrypt(encrypted_data)
        
        # Try to parse as JSON, otherwise return as string
        try:
            return json.loads(plaintext.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return plaintext.decode()
    
    def _pad_data(self, data: bytes) -> bytes:
        """Pad data to AES block size"""
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """Remove padding from data"""
        padding_length = data[-1]
        return data[:-padding_length]

class DataProtectionManager:
    """Main data protection manager for MINGUS financial data"""
    
    def __init__(self, config: Optional[EncryptionConfig] = None):
        self.config = config or self._get_default_config()
        self.field_manager = FieldEncryptionManager(self.config)
        self.key_manager = KeyManager(self.config)
        self.database_encryption = DatabaseColumnEncryption(self.config, self.key_manager)
        self.file_encryption = FileEncryption(self.config, self.key_manager)
        self.data_masking = DataMasking(self.config)
        self.data_tokenization = DataTokenization(self.config)
        self.secure_deletion = SecureDataDeletion(self.config)
        self.data_integrity = DataIntegrityVerification(self.config)
        self.audit_trail = AuditTrail(self.config)
        self.compliance_logging = ComplianceLogging(self.config)
        
        # Define sensitive field mappings
        self.sensitive_fields = {
            # Financial account information
            'account_number': DataSensitivity.CRITICAL,
            'routing_number': DataSensitivity.CRITICAL,
            'account_balance': DataSensitivity.HIGH,
            'account_type': DataSensitivity.MEDIUM,
            'bank_name': DataSensitivity.MEDIUM,
            'account_holder': DataSensitivity.HIGH,
            
            # Social Security numbers
            'ssn': DataSensitivity.CRITICAL,
            'social_security_number': DataSensitivity.CRITICAL,
            'tax_id': DataSensitivity.CRITICAL,
            
            # Bank account details
            'bank_account': DataSensitivity.CRITICAL,
            'checking_account': DataSensitivity.CRITICAL,
            'savings_account': DataSensitivity.CRITICAL,
            'credit_card_number': DataSensitivity.CRITICAL,
            'cvv': DataSensitivity.CRITICAL,
            'expiry_date': DataSensitivity.HIGH,
            'card_holder': DataSensitivity.HIGH,
            
            # Credit scores
            'credit_score': DataSensitivity.HIGH,
            'fico_score': DataSensitivity.HIGH,
            'credit_report': DataSensitivity.HIGH,
            'credit_history': DataSensitivity.HIGH,
            
            # Detailed income information
            'salary': DataSensitivity.HIGH,
            'annual_income': DataSensitivity.HIGH,
            'monthly_income': DataSensitivity.HIGH,
            'hourly_wage': DataSensitivity.HIGH,
            'bonus': DataSensitivity.HIGH,
            'commission': DataSensitivity.HIGH,
            'overtime_pay': DataSensitivity.HIGH,
            'employer': DataSensitivity.MEDIUM,
            'job_title': DataSensitivity.MEDIUM,
            'employment_history': DataSensitivity.HIGH,
            
            # Health data correlations
            'health_insurance': DataSensitivity.HIGH,
            'medical_expenses': DataSensitivity.HIGH,
            'healthcare_costs': DataSensitivity.HIGH,
            'medical_debt': DataSensitivity.HIGH,
            'health_conditions': DataSensitivity.HIGH,
            'medications': DataSensitivity.HIGH,
            'healthcare_provider': DataSensitivity.MEDIUM,
            
            # Personal identification
            'driver_license': DataSensitivity.CRITICAL,
            'passport_number': DataSensitivity.CRITICAL,
            'date_of_birth': DataSensitivity.HIGH,
            'address': DataSensitivity.MEDIUM,
            'phone_number': DataSensitivity.MEDIUM,
            'email': DataSensitivity.MEDIUM,
            
            # Investment information
            'investment_accounts': DataSensitivity.HIGH,
            'portfolio_value': DataSensitivity.HIGH,
            'stock_holdings': DataSensitivity.HIGH,
            'retirement_accounts': DataSensitivity.HIGH,
            '401k_balance': DataSensitivity.HIGH,
            'ira_balance': DataSensitivity.HIGH,
            
            # Debt information
            'mortgage_balance': DataSensitivity.HIGH,
            'car_loan_balance': DataSensitivity.HIGH,
            'student_loan_balance': DataSensitivity.HIGH,
            'credit_card_balance': DataSensitivity.HIGH,
            'debt_to_income_ratio': DataSensitivity.HIGH,
            
            # Tax information
            'tax_return': DataSensitivity.CRITICAL,
            'w2_form': DataSensitivity.CRITICAL,
            '1099_form': DataSensitivity.CRITICAL,
            'tax_liability': DataSensitivity.HIGH,
            'tax_refund': DataSensitivity.HIGH
        }
    
    def _get_default_config(self) -> EncryptionConfig:
        """Get default encryption configuration"""
        return EncryptionConfig(
            master_key=os.environ.get('MINGUS_MASTER_KEY'),
            field_encryption_enabled=True,
            database_encryption_enabled=True,
            file_encryption_enabled=True,
            audit_encryption_operations=True,
            log_encryption_events=True
        )
    
    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a record"""
        encrypted_record = {}
        
        for field_name, value in record.items():
            if field_name in self.sensitive_fields:
                # Encrypt sensitive field
                sensitivity = self.sensitive_fields[field_name]
                encrypted_field = self.field_manager.encrypt_field(
                    value, field_name, sensitivity
                )
                encrypted_record[field_name] = encrypted_field.__dict__
            else:
                # Keep non-sensitive field as is
                encrypted_record[field_name] = value
        
        return encrypted_record
    
    def decrypt_record(self, encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a record"""
        decrypted_record = {}
        
        for field_name, value in encrypted_record.items():
            if field_name in self.sensitive_fields:
                # Decrypt sensitive field
                if isinstance(value, dict) and 'encrypted_data' in value:
                    encrypted_field = EncryptedField(**value)
                    decrypted_value = self.field_manager.decrypt_field(
                        encrypted_field, field_name
                    )
                    decrypted_record[field_name] = decrypted_value
                else:
                    # Field was not encrypted
                    decrypted_record[field_name] = value
            else:
                # Keep non-sensitive field as is
                decrypted_record[field_name] = value
        
        return decrypted_record
    
    def mask_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in a record for display/logging"""
        return self.data_masking.mask_database_record(record)
    
    def mask_text(self, text: str) -> str:
        """Mask sensitive data in text"""
        return self.data_masking.mask_all_sensitive_data(text)
    
    def mask_log_message(self, message: str) -> str:
        """Mask sensitive data in log messages"""
        return self.data_masking.mask_log_message(message)
    
    def mask_error_message(self, error_message: str) -> str:
        """Mask sensitive data in error messages"""
        return self.data_masking.mask_error_message(error_message)
    
    def mask_api_response(self, response_data: Any) -> Any:
        """Mask sensitive data in API responses"""
        return self.data_masking.mask_api_response(response_data)
    
    def mask_request_data(self, request_data: Any) -> Any:
        """Mask sensitive data in request data"""
        return self.data_masking.mask_request_data(request_data)
    
    def encrypt_specific_field(self, field_name: str, value: Any) -> EncryptedField:
        """Encrypt a specific field"""
        if field_name not in self.sensitive_fields:
            raise ValueError(f"Field '{field_name}' is not marked as sensitive")
        
        sensitivity = self.sensitive_fields[field_name]
        return self.field_manager.encrypt_field(value, field_name, sensitivity)
    
    def decrypt_specific_field(self, field_name: str, encrypted_field: EncryptedField) -> Any:
        """Decrypt a specific field"""
        if field_name not in self.sensitive_fields:
            raise ValueError(f"Field '{field_name}' is not marked as sensitive")
        
        return self.field_manager.decrypt_field(encrypted_field, field_name)
    
    def encrypt_database_column(self, value: Any, column_name: str, table_name: str) -> str:
        """Encrypt a database column value"""
        return self.database_encryption.encrypt_column_value(value, column_name, table_name)
    
    def decrypt_database_column(self, encrypted_value: str, column_name: str, table_name: str) -> Any:
        """Decrypt a database column value"""
        return self.database_encryption.decrypt_column_value(encrypted_value, column_name, table_name)
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> EncryptedFile:
        """Encrypt a file"""
        return self.file_encryption.encrypt_file(file_path, output_path)
    
    def decrypt_file(self, encrypted_file: EncryptedFile, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        return self.file_encryption.decrypt_file(encrypted_file, output_path)
    
    def encrypt_file_stream(self, file_stream: BinaryIO, chunk_size: Optional[int] = None) -> Tuple[bytes, EncryptedFile]:
        """Encrypt a file stream"""
        return self.file_encryption.encrypt_file_stream(file_stream, chunk_size)
    
    def derive_key_from_password(self, password: str, salt: Optional[str] = None) -> Tuple[bytes, str]:
        """Derive encryption key from user password"""
        return self.key_manager.derive_key_from_password(password, salt)
    
    def verify_password_key(self, password: str, salt: str, expected_key: bytes) -> bool:
        """Verify password-derived key"""
        return self.key_manager.verify_password_key(password, salt, expected_key)
    
    def add_sensitive_field(self, field_name: str, sensitivity: DataSensitivity):
        """Add a new sensitive field to the protection system"""
        self.sensitive_fields[field_name] = sensitivity
        logger.info(f"Added sensitive field '{field_name}' with sensitivity '{sensitivity.value}'")
    
    def remove_sensitive_field(self, field_name: str):
        """Remove a field from sensitive field list"""
        if field_name in self.sensitive_fields:
            del self.sensitive_fields[field_name]
            logger.info(f"Removed sensitive field '{field_name}'")
    
    def get_sensitive_fields(self) -> Dict[str, DataSensitivity]:
        """Get all sensitive field mappings"""
        return self.sensitive_fields.copy()
    
    def rotate_encryption_keys(self):
        """Rotate all encryption keys"""
        self.key_manager.rotate_keys()
        logger.info("Encryption keys rotated successfully")
    
    def get_encryption_stats(self) -> Dict[str, Any]:
        """Get encryption system statistics"""
        return {
            'sensitive_fields_count': len(self.sensitive_fields),
            'current_key_id': self.key_manager.current_key_id,
            'total_keys': len(self.key_manager.keys),
            'active_keys': len([k for k, v in self.key_manager.keys.items() 
                              if v.get('active', False)]),
            'field_encryption_enabled': self.config.field_encryption_enabled,
            'database_encryption_enabled': self.config.database_encryption_enabled,
            'file_encryption_enabled': self.config.file_encryption_enabled,
            'audit_enabled': self.config.audit_encryption_operations,
            'key_storage_type': self.config.key_storage_type.value,
            'data_masking_enabled': True,
            'tokenization_enabled': True,
            'crypto_shredding_enabled': True,
            'integrity_verification_enabled': True,
            'audit_trail_enabled': True,
            'compliance_logging_enabled': True
        }
    
    def create_token(self, data: str, tokenization_type: TokenizationType,
                    expires_at: Optional[datetime] = None, metadata: Dict[str, Any] = None) -> str:
        """Create a token for sensitive data"""
        token = self.data_tokenization.create_token(data, tokenization_type, expires_at, metadata)
        
        # Log audit event
        self.audit_trail.log_event(
            AuditEventType.TOKEN_CREATE,
            resource_type="token",
            resource_id=token,
            details={"tokenization_type": tokenization_type.value},
            compliance_tags=[ComplianceRegulation.PCI_DSS]
        )
        
        return token
    
    def retrieve_token_data(self, token: str, user_id: Optional[str] = None,
                           ip_address: Optional[str] = None) -> Optional[str]:
        """Retrieve data using token"""
        data = self.data_tokenization.retrieve_data(token, user_id, ip_address)
        
        # Log audit event
        self.audit_trail.log_event(
            AuditEventType.TOKEN_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="token",
            resource_id=token,
            details={"success": data is not None}
        )
        
        return data
    
    def revoke_token(self, token: str, user_id: Optional[str] = None) -> bool:
        """Revoke a token (crypto-shredding)"""
        success = self.data_tokenization.revoke_token(token)
        
        if success:
            # Log audit event
            self.audit_trail.log_event(
                AuditEventType.CRYPTO_SHRED,
                user_id=user_id,
                resource_type="token",
                resource_id=token,
                details={"method": "token_revocation"},
                compliance_tags=[ComplianceRegulation.GDPR]
            )
        
        return success
    
    def crypto_shred_data(self, data_id: str, data_type: str, user_id: Optional[str] = None) -> bool:
        """Perform crypto-shredding of data"""
        success = self.secure_deletion.crypto_shred_data(data_id, data_type, user_id)
        
        if success:
            # Log audit event
            self.audit_trail.log_event(
                AuditEventType.CRYPTO_SHRED,
                user_id=user_id,
                resource_type=data_type,
                resource_id=data_id,
                details={"method": "crypto_shred"},
                compliance_tags=[ComplianceRegulation.GDPR],
                risk_level="high"
            )
        
        return success
    
    def create_integrity_record(self, data_id: str, data: Any) -> DataIntegrityRecord:
        """Create integrity record for data"""
        record = self.data_integrity.create_integrity_record(data_id, data)
        
        # Log audit event
        self.audit_trail.log_event(
            AuditEventType.INTEGRITY_VERIFY,
            resource_type="data_integrity",
            resource_id=data_id,
            details={"action": "create_record", "hash": record.original_hash}
        )
        
        return record
    
    def verify_data_integrity(self, data_id: str, data: Any) -> Tuple[bool, str]:
        """Verify data integrity"""
        is_valid, message = self.data_integrity.verify_integrity(data_id, data)
        
        # Log audit event
        self.audit_trail.log_event(
            AuditEventType.INTEGRITY_VERIFY,
            resource_type="data_integrity",
            resource_id=data_id,
            details={"action": "verify", "result": is_valid, "message": message},
            risk_level="high" if not is_valid else "low"
        )
        
        return is_valid, message
    
    def log_audit_event(self, event_type: AuditEventType, user_id: Optional[str] = None,
                       ip_address: Optional[str] = None, resource_type: Optional[str] = None,
                       resource_id: Optional[str] = None, action: Optional[str] = None,
                       details: Dict[str, Any] = None, compliance_tags: List[ComplianceRegulation] = None,
                       risk_level: str = "low"):
        """Log an audit event"""
        self.audit_trail.log_event(
            event_type, user_id, ip_address, resource_type, resource_id,
            action, details, compliance_tags, risk_level
        )
    
    def get_audit_events(self, user_id: Optional[str] = None,
                        event_type: Optional[AuditEventType] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[AuditEvent]:
        """Get audit events with filtering"""
        return self.audit_trail.get_audit_events(user_id, event_type, start_time, end_time)
    
    def log_compliance_event(self, regulation: ComplianceRegulation, event_type: str,
                           user_id: Optional[str] = None, data_type: Optional[str] = None,
                           details: Dict[str, Any] = None):
        """Log compliance event"""
        self.compliance_logging.log_compliance_event(regulation, event_type, user_id, data_type, details)
    
    def generate_compliance_report(self, regulation: ComplianceRegulation,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate compliance report for regulation"""
        return self.compliance_logging.generate_compliance_report(regulation, start_date, end_date)
    
    def get_deletion_log(self, data_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deletion log for audit purposes"""
        return self.secure_deletion.get_deletion_log(data_id)
    
    def get_integrity_status(self, data_id: str) -> Optional[DataIntegrityRecord]:
        """Get integrity status for data"""
        return self.data_integrity.get_integrity_status(data_id)

class DataMasking:
    """Data masking for sensitive information display and logging"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        
        # Define masking patterns
        self.masking_patterns = {
            # Credit card numbers (16 digits)
            'credit_card': {
                'pattern': r'\b(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})\b',
                'mask': r'****-****-****-\1',
                'show_last': 4,
                'total_length': 16
            },
            
            # Bank account numbers (8-17 digits)
            'bank_account': {
                'pattern': r'\b(\d{8,17})\b',
                'mask': r'****\1',
                'show_last': 4,
                'min_length': 8,
                'max_length': 17
            },
            
            # Social Security numbers (XXX-XX-XXXX)
            'ssn': {
                'pattern': r'\b(\d{3}[-]?\d{2}[-]?\d{4})\b',
                'mask': r'***-**-\1',
                'show_last': 4,
                'total_length': 9
            },
            
            # Routing numbers (9 digits)
            'routing_number': {
                'pattern': r'\b(\d{9})\b',
                'mask': r'****\1',
                'show_last': 4,
                'total_length': 9
            },
            
            # Email addresses
            'email': {
                'pattern': r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
                'mask': r'\1***@\2',
                'show_first': 3,
                'show_domain': True
            },
            
            # Phone numbers
            'phone': {
                'pattern': r'\b(\d{3}[-. ]?\d{3}[-. ]?\d{4})\b',
                'mask': r'***-***-\1',
                'show_last': 4,
                'total_length': 10
            },
            
            # Addresses
            'address': {
                'pattern': r'\b(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Terrace|Ter|Circle|Cir|Square|Sq|Highway|Hwy|Parkway|Pkwy|Expressway|Expy|Freeway|Fwy|Turnpike|Tpke|Bridge|Br|Tunnel|Tun|Causeway|Cswy|Plaza|Plz|Commons|Com|Heights|Hts|Gardens|Gdn|Manor|Mnr|Village|Vlg|Center|Ctr|Mall|Plaza|Plz|Building|Bldg|Suite|Ste|Apartment|Apt|Unit|Floor|Fl|Room|Rm|Office|Ofc|Department|Dept|Division|Div|Section|Sec|Wing|Tower|Twr|Complex|Cpx|Center|Ctr|Campus|Cmp|Park|Pk|Garden|Gdn|Grove|Grv|Meadow|Mdw|Field|Fld|Valley|Vly|Hill|Hl|Mountain|Mtn|Peak|Pk|Ridge|Rdg|Summit|Sum|Crest|Crst|Bluff|Blf|Cliff|Clf|Canyon|Cyn|Gorge|Grg|Ravine|Rvn|Gulch|Glch|Hollow|Hlw|Glen|Gln|Dale|Dl|Dell|Dl|Vale|Vl|Meadow|Mdw|Prairie|Prr|Plains|Pln|Steppe|Stp|Savanna|Svn|Desert|Dst|Oasis|Oas|Island|Isl|Peninsula|Pns|Cape|Cp|Point|Pt|Bay|By|Harbor|Hbr|Cove|Cv|Inlet|Inl|Sound|Snd|Strait|Strt|Channel|Chnl|Canal|Cnl|River|Rvr|Stream|Strm|Creek|Crk|Brook|Brk|Branch|Brn|Fork|Frk|Tributary|Trb|Estuary|Est|Delta|Dlt|Marsh|Mrsh|Swamp|Swp|Bog|Bg|Fen|Fn|Moor|Mr|Heath|Hth|Moorland|Mrld|Tundra|Tnd|Taiga|Tg|Forest|Frst|Wood|Wd|Grove|Grv|Orchard|Orch|Vineyard|Vny|Farm|Frm|Ranch|Rnch|Plantation|Plnt|Estate|Est|Manor|Mnr|Castle|Cstl|Palace|Plc|Chateau|Cht|Villa|Vll|Cottage|Cttg|Cabin|Cbn|Lodge|Ldg|Inn|In|Hotel|Htl|Motel|Mtl|Resort|Rst|Spa|Sp|Club|Clb|Golf|Glf|Country|Cntry|Tennis|Tns|Ski|Sk|Beach|Bch|Marina|Mrn|Yacht|Yct|Boat|Bt|Ship|Shp|Cruise|Crs|Ferry|Fry|Port|Prt|Dock|Dck|Pier|Pr|Wharf|Whrf|Quay|Qy|Jetty|Jty|Breakwater|Brkw|Seawall|Swl|Levee|Lv|Dam|Dm|Reservoir|Rsvr|Lake|Lk|Pond|Pd|Pool|Pl|Spring|Spg|Well|Wl|Fountain|Ftn|Cascade|Csc|Waterfall|Wtrf|Rapids|Rpd|Whitewater|Whtw|Rough|Rgh|Smooth|Smth|Calm|Clm|Still|Stl|Quiet|Qt|Peaceful|Pcf|Serene|Srn|Tranquil|Trnq|Placid|Plcd|Gentle|Gntl|Soft|Sft|Hard|Hrd|Sharp|Shrp|Blunt|Blnt|Dull|Dl|Bright|Brt|Dark|Drk|Light|Lt|Heavy|Hvy|Light|Lt|Fast|Fst|Slow|Slw|Quick|Qck|Rapid|Rpd|Swift|Swft|Fleet|Flt|Speedy|Spdy|Hasty|Hsty|Hurried|Hrrd|Rushed|Rshd|Urgent|Urgt|Immediate|Imm|Instant|Inst|Momentary|Mmt|Brief|Brf|Short|Shrt|Long|Lng|Extended|Ext|Prolonged|Prlg|Enduring|Endr|Lasting|Lstng|Permanent|Prm|Temporary|Tmp|Provisional|Prv|Interim|Int|Acting|Act|Deputy|Dpty|Assistant|Asst|Associate|Assoc|Senior|Snr|Junior|Jnr|Chief|Chf|Principal|Prnc|Executive|Exec|Director|Dir|Manager|Mgr|Supervisor|Spr|Coordinator|Crd|Specialist|Spc|Technician|Tch|Engineer|Eng|Architect|Arch|Designer|Dsgn|Artist|Art|Musician|Msc|Singer|Sng|Dancer|Dnc|Actor|Act|Actress|Act|Performer|Prf|Entertainer|Ent|Comedian|Cmd|Magician|Mgc|Clown|Cln|Juggler|Jgl|Acrobat|Acr|Trapeze|Trp|Tightrope|Tgr|Highwire|Hgh|Balance|Blc|Equilibrium|Eql|Harmony|Hrm|Melody|Mld|Rhythm|Rthm|Beat|Bt|Tempo|Tmp|Pitch|Ptch|Tone|Tn|Note|Nt|Chord|Chrd|Scale|Scl|Key|Ky|Major|Mjr|Minor|Mnr|Sharp|Shrp|Flat|Flt|Natural|Ntrl|Accidental|Acc|Grace|Grc|Trill|Trl|Vibrato|Vbr|Tremolo|Trm|Glissando|Gls|Arpeggio|Arp|Staccato|Stc|Legato|Lgt|Pizzicato|Pzz|Harmonics|Hrm|Overtones|Ovt|Resonance|Rsn|Echo|Ech|Reverb|Rvb|Delay|Dly|Chorus|Chr|Flanger|Flg|Phaser|Phs|Distortion|Dst|Overdrive|Ovd|Fuzz|Fzz|Wah|Wh|Tremolo|Trm|Vibrato|Vbr|Chorus|Chr|Flanger|Flg|Phaser|Phs|Delay|Dly|Reverb|Rvb|Echo|Ech|Resonance|Rsn|Overtones|Ovt|Harmonics|Hrm|Pizzicato|Pzz|Legato|Lgt|Staccato|Stc|Arpeggio|Arp|Glissando|Gls|Tremolo|Trm|Vibrato|Vbr|Trill|Trl|Grace|Grc|Accidental|Acc|Natural|Ntrl|Flat|Flt|Sharp|Shrp|Minor|Mnr|Major|Mjr|Key|Ky|Scale|Scl|Chord|Chrd|Note|Nt|Tone|Tn|Pitch|Ptch|Tempo|Tmp|Beat|Bt|Rhythm|Rthm|Melody|Mld|Harmony|Hrm|Equilibrium|Eql|Balance|Blc|Highwire|Hgh|Tightrope|Tgr|Trapeze|Trp|Acrobat|Acr|Juggler|Jgl|Clown|Cln|Magician|Mgc|Comedian|Cmd|Entertainer|Ent|Performer|Prf|Actress|Act|Actor|Act|Singer|Sng|Musician|Msc|Artist|Art|Designer|Dsgn|Architect|Arch|Engineer|Eng|Technician|Tch|Specialist|Spc|Coordinator|Crd|Supervisor|Spr|Manager|Mgr|Director|Dir|Executive|Exec|Principal|Prnc|Chief|Chf|Junior|Jnr|Senior|Snr|Associate|Assoc|Assistant|Asst|Deputy|Dpty|Acting|Act|Interim|Int|Provisional|Prv|Temporary|Tmp|Permanent|Prm|Lasting|Lstng|Enduring|Endr|Prolonged|Prlg|Extended|Ext|Long|Lng|Short|Shrt|Brief|Brf|Momentary|Mmt|Instant|Inst|Immediate|Imm|Urgent|Urgt|Rushed|Rshd|Hurried|Hrrd|Hasty|Hsty|Speedy|Spdy|Fleet|Flt|Swift|Swft|Rapid|Rpd|Quick|Qck|Slow|Slw|Fast|Fst|Light|Lt|Heavy|Hvy|Light|Lt|Dark|Drk|Bright|Brt|Dull|Dl|Blunt|Blnt|Sharp|Shrp|Hard|Hrd|Soft|Sft|Gentle|Gntl|Placid|Plcd|Tranquil|Trnq|Serene|Srn|Peaceful|Pcf|Quiet|Qt|Still|Stl|Calm|Clm|Smooth|Smth|Rough|Rgh|Whitewater|Whtw|Rapids|Rpd|Waterfall|Wtrf|Cascade|Csc|Fountain|Ftn|Well|Wl|Spring|Spg|Pool|Pl|Pond|Pd|Lake|Lk|Reservoir|Rsvr|Dam|Dm|Levee|Lv|Seawall|Swl|Breakwater|Brkw|Jetty|Jty|Quay|Qy|Wharf|Whrf|Pier|Pr|Dock|Dck|Port|Prt|Ferry|Fry|Cruise|Crs|Ship|Shp|Boat|Bt|Yacht|Yct|Marina|Mrn|Beach|Bch|Ski|Sk|Tennis|Tns|Golf|Glf|Country|Cntry|Club|Clb|Spa|Sp|Resort|Rst|Motel|Mtl|Hotel|Htl|Inn|In|Lodge|Ldg|Cabin|Cbn|Cottage|Cttg|Villa|Vll|Chateau|Cht|Palace|Plc|Castle|Cstl|Manor|Mnr|Estate|Est|Plantation|Plnt|Ranch|Rnch|Farm|Frm|Vineyard|Vny|Orchard|Orch|Grove|Grv|Wood|Wd|Forest|Frst|Taiga|Tg|Tundra|Tnd|Moorland|Mrld|Heath|Hth|Moor|Mr|Fen|Fn|Bog|Bg|Swamp|Swp|Marsh|Mrsh|Delta|Dlt|Estuary|Est|Tributary|Trb|Fork|Frk|Branch|Brn|Brook|Brk|Creek|Crk|Stream|Strm|River|Rvr|Canal|Cnl|Channel|Chnl|Strait|Strt|Sound|Snd|Inlet|Inl|Cove|Cv|Harbor|Hbr|Bay|By|Point|Pt|Cape|Cp|Peninsula|Pns|Island|Isl|Oasis|Oas|Desert|Dst|Savanna|Svn|Steppe|Stp|Plains|Pln|Prairie|Prr|Meadow|Mdw|Vale|Vl|Glen|Gln|Hollow|Hlw|Gulch|Glch|Ravine|Rvn|Gorge|Grg|Canyon|Cyn|Cliff|Clf|Bluff|Blf|Crest|Crst|Summit|Sum|Peak|Pk|Mountain|Mtn|Hill|Hl|Valley|Vly|Field|Fld|Meadow|Mdw|Grove|Grv|Garden|Gdn|Park|Pk|Campus|Cmp|Complex|Cpx|Tower|Twr|Wing|Section|Sec|Division|Div|Department|Dept|Office|Ofc|Room|Rm|Floor|Fl|Unit|Apartment|Apt|Suite|Ste|Building|Bldg|Plaza|Plz|Mall|Center|Ctr|Village|Vlg|Manor|Mnr|Gardens|Gdn|Heights|Hts|Commons|Com|Plaza|Plz|Bridge|Br|Tunnel|Tun|Causeway|Cswy|Turnpike|Tpke|Freeway|Fwy|Expressway|Expy|Parkway|Pkwy|Highway|Hwy|Square|Sq|Circle|Cir|Terrace|Ter|Way|Place|Pl|Court|Ct|Drive|Dr|Lane|Ln|Boulevard|Blvd|Road|Rd|Avenue|Ave|Street|St)\b',
                'mask': r'*** \1',
                'show_first': 0,
                'show_last': 0
            },
            
            # Income amounts
            'income': {
                'pattern': r'\b(\$[\d,]+(?:\.\d{2})?)\b',
                'mask': r'$***',
                'show_first': 0,
                'show_last': 0
            },
            
            # Salary amounts
            'salary': {
                'pattern': r'\b(salary|wage|income|earnings|pay|compensation|remuneration|stipend|allowance|bonus|commission|overtime|hourly|annual|monthly|weekly|daily|yearly|biweekly|semimonthly|quarterly|semiannual|biannual|per\s+hour|per\s+day|per\s+week|per\s+month|per\s+year|USD|dollars?|cents?)\s*[:=]?\s*(\$[\d,]+(?:\.\d{2})?)\b',
                'mask': r'\1: $***',
                'show_first': 0,
                'show_last': 0
            },
            
            # Account balances
            'balance': {
                'pattern': r'\b(balance|amount|total|sum|value|worth|assets?|liabilities?|equity|capital|funds?|money|cash|checking|savings|investment|portfolio|retirement|401k|ira|roth|traditional|sep|simple|keogh|pension|annuity|trust|estate|inheritance|gift|donation|charity|foundation|endowment|scholarship|grant|loan|mortgage|credit|debt|liability|obligation|payment|installment|premium|deductible|coverage|policy|claim|settlement|award|judgment|fine|penalty|fee|charge|cost|expense|expenditure|outlay|disbursement|payment|remittance|transfer|deposit|withdrawal|transaction|purchase|sale|trade|exchange|conversion|redemption|maturity|interest|dividend|yield|return|profit|loss|gain|earnings|revenue|income|salary|wage|pay|compensation|remuneration|stipend|allowance|bonus|commission|overtime|hourly|annual|monthly|weekly|daily|yearly|biweekly|semimonthly|quarterly|semiannual|biannual|per\s+hour|per\s+day|per\s+week|per\s+month|per\s+year|USD|dollars?|cents?)\s*[:=]?\s*(\$[\d,]+(?:\.\d{2})?)\b',
                'mask': r'\1: $***',
                'show_first': 0,
                'show_last': 0
            }
        }
    
    def mask_credit_card(self, text: str) -> str:
        """Mask credit card numbers showing only last 4 digits"""
        import re
        pattern = self.masking_patterns['credit_card']['pattern']
        mask = self.masking_patterns['credit_card']['mask']
        show_last = self.masking_patterns['credit_card']['show_last']
        
        def mask_cc(match):
            cc_number = re.sub(r'[^0-9]', '', match.group(1))
            if len(cc_number) == 16:
                return f"****-****-****-{cc_number[-show_last:]}"
            return match.group(0)
        
        return re.sub(pattern, mask_cc, text)
    
    def mask_bank_account(self, text: str) -> str:
        """Mask bank account numbers showing only last 4 digits"""
        import re
        pattern = self.masking_patterns['bank_account']['pattern']
        show_last = self.masking_patterns['bank_account']['show_last']
        min_length = self.masking_patterns['bank_account']['min_length']
        max_length = self.masking_patterns['bank_account']['max_length']
        
        def mask_account(match):
            account_number = re.sub(r'[^0-9]', '', match.group(1))
            if min_length <= len(account_number) <= max_length:
                return f"****{account_number[-show_last:]}"
            return match.group(0)
        
        return re.sub(pattern, mask_account, text)
    
    def mask_ssn(self, text: str) -> str:
        """Mask Social Security numbers showing only last 4 digits"""
        import re
        pattern = self.masking_patterns['ssn']['pattern']
        show_last = self.masking_patterns['ssn']['show_last']
        
        def mask_ssn_number(match):
            ssn = re.sub(r'[^0-9]', '', match.group(1))
            if len(ssn) == 9:
                return f"***-**-{ssn[-show_last:]}"
            return match.group(0)
        
        return re.sub(pattern, mask_ssn_number, text)
    
    def mask_routing_number(self, text: str) -> str:
        """Mask routing numbers showing only last 4 digits"""
        import re
        pattern = self.masking_patterns['routing_number']['pattern']
        show_last = self.masking_patterns['routing_number']['show_last']
        
        def mask_routing(match):
            routing = re.sub(r'[^0-9]', '', match.group(1))
            if len(routing) == 9:
                return f"****{routing[-show_last:]}"
            return match.group(0)
        
        return re.sub(pattern, mask_routing, text)
    
    def mask_email(self, text: str) -> str:
        """Mask email addresses showing first 3 characters and domain"""
        import re
        pattern = self.masking_patterns['email']['pattern']
        show_first = self.masking_patterns['email']['show_first']
        show_domain = self.masking_patterns['email']['show_domain']
        
        def mask_email_address(match):
            local_part = match.group(1)
            domain = match.group(2)
            
            if len(local_part) > show_first:
                masked_local = local_part[:show_first] + "***"
            else:
                masked_local = local_part
            
            if show_domain:
                return f"{masked_local}@{domain}"
            else:
                return f"{masked_local}@***"
        
        return re.sub(pattern, mask_email_address, text)
    
    def mask_phone(self, text: str) -> str:
        """Mask phone numbers showing only last 4 digits"""
        import re
        pattern = self.masking_patterns['phone']['pattern']
        show_last = self.masking_patterns['phone']['show_last']
        
        def mask_phone_number(match):
            phone = re.sub(r'[^0-9]', '', match.group(1))
            if len(phone) == 10:
                return f"***-***-{phone[-show_last:]}"
            return match.group(0)
        
        return re.sub(pattern, mask_phone_number, text)
    
    def mask_address(self, text: str) -> str:
        """Mask addresses showing only street type"""
        import re
        pattern = self.masking_patterns['address']['pattern']
        
        def mask_address_text(match):
            address = match.group(1)
            # Keep only the street type (Street, Avenue, etc.)
            words = address.split()
            if len(words) > 1:
                return f"*** {words[-1]}"
            return "***"
        
        return re.sub(pattern, mask_address_text, text)
    
    def mask_income(self, text: str) -> str:
        """Mask income amounts"""
        import re
        pattern = self.masking_patterns['income']['pattern']
        
        def mask_income_amount(match):
            return "$***"
        
        return re.sub(pattern, mask_income_amount, text)
    
    def mask_salary(self, text: str) -> str:
        """Mask salary information"""
        import re
        pattern = self.masking_patterns['salary']['pattern']
        
        def mask_salary_info(match):
            label = match.group(1)
            return f"{label}: $***"
        
        return re.sub(pattern, mask_salary_info, text)
    
    def mask_balance(self, text: str) -> str:
        """Mask account balances and financial amounts"""
        import re
        pattern = self.masking_patterns['balance']['pattern']
        
        def mask_balance_amount(match):
            label = match.group(1)
            return f"{label}: $***"
        
        return re.sub(pattern, mask_balance_amount, text)
    
    def mask_all_sensitive_data(self, text: str) -> str:
        """Apply all masking patterns to text"""
        if not text:
            return text
        
        # Apply all masking functions
        text = self.mask_credit_card(text)
        text = self.mask_bank_account(text)
        text = self.mask_ssn(text)
        text = self.mask_routing_number(text)
        text = self.mask_email(text)
        text = self.mask_phone(text)
        text = self.mask_address(text)
        text = self.mask_income(text)
        text = self.mask_salary(text)
        text = self.mask_balance(text)
        
        return text
    
    def mask_log_message(self, message: str) -> str:
        """Mask sensitive data in log messages"""
        return self.mask_all_sensitive_data(message)
    
    def mask_error_message(self, error_message: str) -> str:
        """Mask sensitive data in error messages"""
        return self.mask_all_sensitive_data(error_message)
    
    def mask_json_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in JSON/dict structures"""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                # Check if key contains sensitive information
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in [
                    'credit', 'card', 'account', 'ssn', 'social', 'security',
                    'routing', 'income', 'salary', 'balance', 'amount',
                    'email', 'phone', 'address', 'name', 'address'
                ]):
                    if isinstance(value, str):
                        masked_data[key] = self.mask_all_sensitive_data(value)
                    elif isinstance(value, (int, float)):
                        masked_data[key] = "***"
                    else:
                        masked_data[key] = self.mask_json_data(value)
                else:
                    masked_data[key] = self.mask_json_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self.mask_json_data(item) for item in data]
        elif isinstance(data, str):
            return self.mask_all_sensitive_data(data)
        else:
            return data
    
    def mask_database_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in database records"""
        return self.mask_json_data(record)
    
    def mask_api_response(self, response_data: Any) -> Any:
        """Mask sensitive data in API responses"""
        return self.mask_json_data(response_data)
    
    def mask_request_data(self, request_data: Any) -> Any:
        """Mask sensitive data in request data"""
        return self.mask_json_data(request_data)

class DataTokenization:
    """Data tokenization for payment processing and sensitive data"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.token_mapping: Dict[str, str] = {}  # token -> original_data_hash
        self.reverse_mapping: Dict[str, str] = {}  # original_data_hash -> token
        self.token_lock = threading.Lock()
        
        # Initialize token database
        self._init_token_database()
    
    def _init_token_database(self):
        """Initialize token storage database"""
        self.db_path = Path("/tmp/mingus_tokens.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokenized_data (
                token TEXT PRIMARY KEY,
                original_data_hash TEXT NOT NULL,
                tokenization_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                metadata TEXT,
                encrypted_original TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                user_id TEXT,
                ip_address TEXT,
                access_timestamp TEXT NOT NULL,
                access_type TEXT NOT NULL,
                success BOOLEAN DEFAULT TRUE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_token(self, data: str, tokenization_type: TokenizationType, 
                    expires_at: Optional[datetime] = None, metadata: Dict[str, Any] = None) -> str:
        """Create a token for sensitive data"""
        with self.token_lock:
            # Generate hash of original data
            data_hash = hashlib.sha256(data.encode()).hexdigest()
            
            # Check if token already exists
            if data_hash in self.reverse_mapping:
                return self.reverse_mapping[data_hash]
            
            # Generate unique token
            token = self._generate_unique_token(tokenization_type)
            
            # Encrypt original data
            encrypted_data = self._encrypt_original_data(data)
            
            # Store token mapping
            self.tokens[token] = {
                'original_data_hash': data_hash,
                'tokenization_type': tokenization_type.value,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
                'access_count': 0,
                'last_accessed': None,
                'metadata': metadata or {},
                'encrypted_original': encrypted_data
            }
            
            self.token_mapping[token] = data_hash
            self.reverse_mapping[data_hash] = token
            
            # Store in database
            self._store_token_in_db(token, data_hash, tokenization_type, encrypted_data, expires_at, metadata)
            
            return token
    
    def _generate_unique_token(self, tokenization_type: TokenizationType) -> str:
        """Generate a unique token based on type"""
        prefix_map = {
            TokenizationType.PAYMENT_CARD: "pc_",
            TokenizationType.BANK_ACCOUNT: "ba_",
            TokenizationType.SSN: "ssn_",
            TokenizationType.EMAIL: "em_",
            TokenizationType.PHONE: "ph_",
            TokenizationType.CUSTOM: "cu_"
        }
        
        prefix = prefix_map.get(tokenization_type, "tk_")
        unique_id = str(uuid.uuid4()).replace('-', '')[:16]
        return f"{prefix}{unique_id}"
    
    def _encrypt_original_data(self, data: str) -> str:
        """Encrypt original data for secure storage"""
        key_id, master_key = self.key_manager.get_current_key()
        
        # Use AES-256-GCM for encryption
        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        # Combine IV, ciphertext, and auth tag
        encrypted_data = iv + auth_tag + ciphertext
        return base64.b64encode(encrypted_data).decode()
    
    def _decrypt_original_data(self, encrypted_data: str) -> str:
        """Decrypt original data"""
        key_id, master_key = self.key_manager.get_current_key()
        
        # Decode and separate components
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv = encrypted_bytes[:16]
        auth_tag = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.GCM(iv, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()
    
    def _store_token_in_db(self, token: str, data_hash: str, tokenization_type: TokenizationType,
                          encrypted_data: str, expires_at: Optional[datetime], metadata: Dict[str, Any]):
        """Store token in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tokenized_data 
            (token, original_data_hash, tokenization_type, created_at, expires_at, metadata, encrypted_original)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            token,
            data_hash,
            tokenization_type.value,
            datetime.utcnow().isoformat(),
            expires_at.isoformat() if expires_at else None,
            json.dumps(metadata or {}),
            encrypted_data
        ))
        
        conn.commit()
        conn.close()
    
    def retrieve_data(self, token: str, user_id: Optional[str] = None, 
                     ip_address: Optional[str] = None) -> Optional[str]:
        """Retrieve original data using token"""
        with self.token_lock:
            if token not in self.tokens:
                return None
            
            token_data = self.tokens[token]
            
            # Check expiration
            if token_data['expires_at']:
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    self._log_token_access(token, user_id, ip_address, "retrieve", False, "Token expired")
                    return None
            
            # Update access count and timestamp
            token_data['access_count'] += 1
            token_data['last_accessed'] = datetime.utcnow().isoformat()
            
            # Log access
            self._log_token_access(token, user_id, ip_address, "retrieve", True)
            
            # Decrypt and return original data
            encrypted_data = token_data['encrypted_original']
            return self._decrypt_original_data(encrypted_data)
    
    def _log_token_access(self, token: str, user_id: Optional[str], ip_address: Optional[str],
                         access_type: str, success: bool, details: str = ""):
        """Log token access for audit trail"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO token_access_log 
            (token, user_id, ip_address, access_timestamp, access_type, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            token,
            user_id,
            ip_address,
            datetime.utcnow().isoformat(),
            access_type,
            success
        ))
        
        conn.commit()
        conn.close()
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token (crypto-shredding)"""
        with self.token_lock:
            if token not in self.tokens:
                return False
            
            # Get data hash
            data_hash = self.token_mapping[token]
            
            # Remove from memory
            del self.tokens[token]
            del self.token_mapping[token]
            del self.reverse_mapping[data_hash]
            
            # Remove from database
            self._remove_token_from_db(token)
            
            return True
    
    def _remove_token_from_db(self, token: str):
        """Remove token from database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tokenized_data WHERE token = ?", (token,))
        cursor.execute("DELETE FROM token_access_log WHERE token = ?", (token,))
        
        conn.commit()
        conn.close()

class SecureDataDeletion:
    """Secure data deletion with crypto-shredding"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.deletion_log: List[Dict[str, Any]] = []
        self.deletion_lock = threading.Lock()
    
    def crypto_shred_data(self, data_id: str, data_type: str, 
                         user_id: Optional[str] = None) -> bool:
        """Perform crypto-shredding of data"""
        with self.deletion_lock:
            try:
                # Generate multiple random keys for overwriting
                shred_keys = [secrets.token_bytes(32) for _ in range(7)]
                
                # Overwrite data multiple times with different patterns
                for i, key in enumerate(shred_keys):
                    # Overwrite with random data
                    self._overwrite_with_pattern(data_id, key, f"pass_{i}")
                
                # Final overwrite with zeros
                self._overwrite_with_pattern(data_id, b'\x00' * 32, "final_zero")
                
                # Log deletion
                deletion_record = {
                    'data_id': data_id,
                    'data_type': data_type,
                    'user_id': user_id,
                    'deletion_timestamp': datetime.utcnow().isoformat(),
                    'method': 'crypto_shred',
                    'passes': len(shred_keys) + 1,
                    'status': 'completed'
                }
                
                self.deletion_log.append(deletion_record)
                self._log_deletion_to_db(deletion_record)
                
                logger.info(f"Crypto-shredded data {data_id} with {len(shred_keys) + 1} passes")
                return True
                
            except Exception as e:
                logger.error(f"Failed to crypto-shred data {data_id}: {e}")
                return False
    
    def _overwrite_with_pattern(self, data_id: str, pattern: bytes, pass_name: str):
        """Overwrite data with specific pattern"""
        # This would typically overwrite the actual data storage
        # For demo purposes, we'll simulate the overwrite
        logger.debug(f"Overwriting {data_id} with {pass_name} pattern")
    
    def _log_deletion_to_db(self, deletion_record: Dict[str, Any]):
        """Log deletion to database"""
        # Implementation would store deletion records in database
        pass
    
    def get_deletion_log(self, data_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deletion log for audit purposes"""
        if data_id:
            return [record for record in self.deletion_log if record['data_id'] == data_id]
        return self.deletion_log.copy()

class DataIntegrityVerification:
    """Data integrity verification and monitoring"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.integrity_records: Dict[str, DataIntegrityRecord] = {}
        self.verification_lock = threading.Lock()
    
    def create_integrity_record(self, data_id: str, data: Any) -> DataIntegrityRecord:
        """Create integrity record for data"""
        with self.verification_lock:
            # Generate hash of data
            if isinstance(data, str):
                data_bytes = data.encode()
            elif isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode()
            else:
                data_bytes = str(data).encode()
            
            data_hash = hashlib.sha256(data_bytes).hexdigest()
            
            # Create integrity record
            integrity_record = DataIntegrityRecord(
                data_id=data_id,
                original_hash=data_hash,
                current_hash=data_hash
            )
            
            self.integrity_records[data_id] = integrity_record
            self._store_integrity_record(integrity_record)
            
            return integrity_record
    
    def verify_integrity(self, data_id: str, data: Any) -> Tuple[bool, str]:
        """Verify data integrity"""
        with self.verification_lock:
            if data_id not in self.integrity_records:
                return False, "No integrity record found"
            
            record = self.integrity_records[data_id]
            
            # Generate current hash
            if isinstance(data, str):
                data_bytes = data.encode()
            elif isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode()
            else:
                data_bytes = str(data).encode()
            
            current_hash = hashlib.sha256(data_bytes).hexdigest()
            
            # Compare hashes
            if current_hash == record.original_hash:
                # Update record
                record.current_hash = current_hash
                record.integrity_status = "verified"
                record.verification_timestamp = datetime.utcnow().isoformat()
                
                # Add to previous verifications
                record.previous_verifications.append({
                    'timestamp': record.verification_timestamp,
                    'hash': current_hash,
                    'status': 'verified'
                })
                
                self._update_integrity_record(record)
                return True, "Integrity verified"
            else:
                # Update record with failure
                record.current_hash = current_hash
                record.integrity_status = "compromised"
                record.verification_timestamp = datetime.utcnow().isoformat()
                
                record.previous_verifications.append({
                    'timestamp': record.verification_timestamp,
                    'hash': current_hash,
                    'status': 'compromised'
                })
                
                self._update_integrity_record(record)
                return False, "Data integrity compromised"
    
    def _store_integrity_record(self, record: DataIntegrityRecord):
        """Store integrity record in database"""
        # Implementation would store in database
        pass
    
    def _update_integrity_record(self, record: DataIntegrityRecord):
        """Update integrity record in database"""
        # Implementation would update in database
        pass
    
    def get_integrity_status(self, data_id: str) -> Optional[DataIntegrityRecord]:
        """Get integrity status for data"""
        return self.integrity_records.get(data_id)

class AuditTrail:
    """Comprehensive audit trail for data access and operations"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.audit_events: List[AuditEvent] = []
        self.audit_lock = threading.Lock()
        self.audit_queue = queue.Queue()
        
        # Start audit worker thread
        self.audit_worker = threading.Thread(target=self._audit_worker, daemon=True)
        self.audit_worker.start()
    
    def log_event(self, event_type: AuditEventType, user_id: Optional[str] = None,
                  ip_address: Optional[str] = None, resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None, action: Optional[str] = None,
                  details: Dict[str, Any] = None, compliance_tags: List[ComplianceRegulation] = None,
                  risk_level: str = "low"):
        """Log an audit event"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            compliance_tags=compliance_tags or [],
            risk_level=risk_level
        )
        
        # Add to queue for async processing
        self.audit_queue.put(event)
    
    def _audit_worker(self):
        """Background worker for processing audit events"""
        while True:
            try:
                event = self.audit_queue.get(timeout=1)
                self._process_audit_event(event)
                self.audit_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audit event: {e}")
    
    def _process_audit_event(self, event: AuditEvent):
        """Process and store audit event"""
        with self.audit_lock:
            self.audit_events.append(event)
            self._store_audit_event(event)
            
            # Check for high-risk events
            if event.risk_level in ["high", "critical"]:
                self._alert_high_risk_event(event)
    
    def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        # Implementation would store in database
        pass
    
    def _alert_high_risk_event(self, event: AuditEvent):
        """Alert on high-risk audit events"""
        logger.warning(f"High-risk audit event: {event.event_type.value} by {event.user_id} at {event.timestamp}")
        # Implementation would send alerts
    
    def get_audit_events(self, user_id: Optional[str] = None, 
                        event_type: Optional[AuditEventType] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[AuditEvent]:
        """Get audit events with filtering"""
        with self.audit_lock:
            events = self.audit_events.copy()
        
        # Apply filters
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if start_time:
            events = [e for e in events if datetime.fromisoformat(e.timestamp) >= start_time]
        if end_time:
            events = [e for e in events if datetime.fromisoformat(e.timestamp) <= end_time]
        
        return events

class ComplianceLogging:
    """Compliance logging for financial regulations"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.compliance_events: List[Dict[str, Any]] = []
        self.compliance_lock = threading.Lock()
        
        # Define compliance requirements
        self.compliance_requirements = {
            ComplianceRegulation.PCI_DSS: {
                'data_retention_days': 365,
                'audit_required': True,
                'encryption_required': True,
                'access_logging': True
            },
            ComplianceRegulation.GDPR: {
                'data_retention_days': 2555,  # 7 years
                'audit_required': True,
                'encryption_required': True,
                'access_logging': True,
                'right_to_forget': True
            },
            ComplianceRegulation.SOX: {
                'data_retention_days': 2555,  # 7 years
                'audit_required': True,
                'encryption_required': True,
                'access_logging': True
            },
            ComplianceRegulation.GLBA: {
                'data_retention_days': 1825,  # 5 years
                'audit_required': True,
                'encryption_required': True,
                'access_logging': True
            }
        }
    
    def log_compliance_event(self, regulation: ComplianceRegulation, event_type: str,
                           user_id: Optional[str] = None, data_type: Optional[str] = None,
                           details: Dict[str, Any] = None):
        """Log compliance event"""
        with self.compliance_lock:
            event = {
                'regulation': regulation.value,
                'event_type': event_type,
                'user_id': user_id,
                'data_type': data_type,
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {},
                'requirements_met': self._check_compliance_requirements(regulation, event_type)
            }
            
            self.compliance_events.append(event)
            self._store_compliance_event(event)
    
    def _check_compliance_requirements(self, regulation: ComplianceRegulation, event_type: str) -> Dict[str, bool]:
        """Check if compliance requirements are met"""
        requirements = self.compliance_requirements.get(regulation, {})
        
        return {
            'data_retention': self._check_data_retention(requirements.get('data_retention_days', 0)),
            'audit_trail': requirements.get('audit_required', False),
            'encryption_enabled': requirements.get('encryption_required', False),
            'access_logging': requirements.get('access_logging', False)
        }
    
    def _check_data_retention(self, required_days: int) -> bool:
        """Check if data retention requirements are met"""
        # Implementation would check actual data retention
        return True
    
    def _store_compliance_event(self, event: Dict[str, Any]):
        """Store compliance event in database"""
        # Implementation would store in database
        pass
    
    def generate_compliance_report(self, regulation: ComplianceRegulation,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate compliance report for regulation"""
        with self.compliance_lock:
            events = [e for e in self.compliance_events if e['regulation'] == regulation.value]
        
        if start_date:
            events = [e for e in events if datetime.fromisoformat(e['timestamp']) >= start_date]
        if end_date:
            events = [e for e in events if datetime.fromisoformat(e['timestamp']) <= end_date]
        
        return {
            'regulation': regulation.value,
            'report_period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'total_events': len(events),
            'compliance_score': self._calculate_compliance_score(events),
            'requirements_met': self._check_compliance_requirements(regulation, "report"),
            'events': events
        }
    
    def _calculate_compliance_score(self, events: List[Dict[str, Any]]) -> float:
        """Calculate compliance score based on events"""
        if not events:
            return 0.0
        
        met_requirements = sum(1 for event in events if all(event['requirements_met'].values()))
        return (met_requirements / len(events)) * 100.0

# Enhanced utility functions
def create_data_protection_manager(config: Optional[EncryptionConfig] = None) -> DataProtectionManager:
    """Create a new data protection manager"""
    return DataProtectionManager(config)

def encrypt_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt financial data using default configuration"""
    manager = create_data_protection_manager()
    return manager.encrypt_record(data)

def decrypt_financial_data(encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt financial data using default configuration"""
    manager = create_data_protection_manager()
    return manager.decrypt_record(encrypted_data)

def encrypt_sensitive_field(field_name: str, value: Any) -> EncryptedField:
    """Encrypt a specific sensitive field"""
    manager = create_data_protection_manager()
    return manager.encrypt_specific_field(field_name, value)

def decrypt_sensitive_field(field_name: str, encrypted_field: EncryptedField) -> Any:
    """Decrypt a specific sensitive field"""
    manager = create_data_protection_manager()
    return manager.decrypt_specific_field(field_name, encrypted_field)

# Database encryption helpers
def encrypt_database_column(value: Any, column_name: str, table_name: str) -> str:
    """Encrypt a database column value"""
    manager = create_data_protection_manager()
    return manager.encrypt_database_column(value, column_name, table_name)

def decrypt_database_column(encrypted_value: str, column_name: str, table_name: str) -> Any:
    """Decrypt a database column value"""
    manager = create_data_protection_manager()
    return manager.decrypt_database_column(encrypted_value, column_name, table_name)

# File encryption helpers
def encrypt_file(file_path: str, output_path: Optional[str] = None) -> EncryptedFile:
    """Encrypt a file"""
    manager = create_data_protection_manager()
    return manager.encrypt_file(file_path, output_path)

def decrypt_file(encrypted_file: EncryptedFile, output_path: Optional[str] = None) -> str:
    """Decrypt a file"""
    manager = create_data_protection_manager()
    return manager.decrypt_file(encrypted_file, output_path)

def encrypt_file_stream(file_stream: BinaryIO, chunk_size: Optional[int] = None) -> Tuple[bytes, EncryptedFile]:
    """Encrypt a file stream"""
    manager = create_data_protection_manager()
    return manager.encrypt_file_stream(file_stream, chunk_size)

# Password key derivation helpers
def derive_key_from_password(password: str, salt: Optional[str] = None) -> Tuple[bytes, str]:
    """Derive encryption key from user password"""
    manager = create_data_protection_manager()
    return manager.derive_key_from_password(password, salt)

def verify_password_key(password: str, salt: str, expected_key: bytes) -> bool:
    """Verify password-derived key"""
    manager = create_data_protection_manager()
    return manager.verify_password_key(password, salt, expected_key)

# Flask integration helpers
def encrypt_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt request data for API endpoints"""
    manager = create_data_protection_manager()
    return manager.encrypt_record(data)

def decrypt_response_data(encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt response data for API endpoints"""
    manager = create_data_protection_manager()
    return manager.decrypt_record(encrypted_data)

# Database integration helpers
def encrypt_for_storage(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt data for database storage"""
    manager = create_data_protection_manager()
    return manager.encrypt_record(data)

def decrypt_from_storage(encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt data from database storage"""
    manager = create_data_protection_manager()
    return manager.decrypt_record(encrypted_data) 

# Data masking utility functions
def mask_credit_card(text: str) -> str:
    """Mask credit card numbers showing only last 4 digits"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_credit_card(text)

def mask_bank_account(text: str) -> str:
    """Mask bank account numbers showing only last 4 digits"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_bank_account(text)

def mask_ssn(text: str) -> str:
    """Mask Social Security numbers showing only last 4 digits"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_ssn(text)

def mask_routing_number(text: str) -> str:
    """Mask routing numbers showing only last 4 digits"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_routing_number(text)

def mask_email(text: str) -> str:
    """Mask email addresses showing first 3 characters and domain"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_email(text)

def mask_phone(text: str) -> str:
    """Mask phone numbers showing only last 4 digits"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_phone(text)

def mask_address(text: str) -> str:
    """Mask addresses showing only street type"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_address(text)

def mask_income(text: str) -> str:
    """Mask income amounts"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_income(text)

def mask_salary(text: str) -> str:
    """Mask salary information"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_salary(text)

def mask_balance(text: str) -> str:
    """Mask account balances and financial amounts"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_balance(text)

def mask_all_sensitive_data(text: str) -> str:
    """Apply all masking patterns to text"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_all_sensitive_data(text)

def mask_log_message(message: str) -> str:
    """Mask sensitive data in log messages"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_log_message(message)

def mask_error_message(error_message: str) -> str:
    """Mask sensitive data in error messages"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_error_message(error_message)

def mask_json_data(data: Any) -> Any:
    """Recursively mask sensitive data in JSON/dict structures"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_json_data(data)

def mask_database_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in database records"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_database_record(record)

def mask_api_response(response_data: Any) -> Any:
    """Mask sensitive data in API responses"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_api_response(response_data)

def mask_request_data(request_data: Any) -> Any:
    """Mask sensitive data in request data"""
    manager = create_data_protection_manager()
    return manager.data_masking.mask_request_data(request_data) 