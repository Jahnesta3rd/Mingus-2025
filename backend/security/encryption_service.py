"""
Encryption Service
==================
Handles data encryption/decryption, field-level encryption for financial data,
Redis session encryption, and database field encryption utilities.
"""

import os
import base64
import logging
import json
import gzip
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import redis
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidKey, InvalidTag

from .crypto_config import KeyType, get_crypto_config
from .key_manager import get_key_manager, EncryptionKey

logger = logging.getLogger(__name__)

class EncryptionMode(Enum):
    """Encryption modes for different use cases"""
    FIELD_LEVEL = "field_level"      # Individual field encryption
    BULK_DATA = "bulk_data"          # Large data encryption
    SESSION = "session"               # Session data encryption
    CACHE = "cache"                   # Cache data encryption
    AUDIT = "audit"                   # Audit log encryption

@dataclass
class EncryptedData:
    """Container for encrypted data with metadata"""
    encrypted_data: bytes
    key_id: str
    algorithm: str
    iv: bytes
    tag: Optional[bytes] = None
    compression: bool = False
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class EncryptionService:
    """
    Comprehensive encryption service for the Mingus Flask application
    """
    
    def __init__(self):
        self.config = get_crypto_config()
        self.key_manager = get_key_manager()
        self.performance_settings = self.config.get_performance_settings()
        self._initialize_compression()
    
    def _initialize_compression(self) -> None:
        """Initialize compression settings"""
        self.compression_enabled = self.config.get_config().compression_enabled
        self.compression_threshold = 1024  # Only compress data larger than 1KB
    
    def encrypt_field(self, value: Any, key_type: KeyType = KeyType.FINANCIAL_DATA) -> str:
        """
        Encrypt a single field value (optimized for financial data)
        
        Args:
            value: Value to encrypt
            key_type: Type of encryption key to use
            
        Returns:
            Base64 encoded encrypted string
        """
        if value is None:
            return None
        
        try:
            # Convert value to string and encode
            if isinstance(value, (int, float)):
                data = str(value).encode('utf-8')
            elif isinstance(value, str):
                data = value.encode('utf-8')
            else:
                data = json.dumps(value).encode('utf-8')
            
            # Get active encryption key
            key = self.key_manager.get_active_key(key_type)
            if not key:
                raise ValueError(f"No active key found for {key_type.value}")
            
            # Encrypt the data
            encrypted_data = self._encrypt_data(data, key, EncryptionMode.FIELD_LEVEL)
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data.encrypted_data).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to encrypt field value: {e}")
            raise
    
    def decrypt_field(self, encrypted_value: str, key_type: KeyType = KeyType.FINANCIAL_DATA) -> Any:
        """
        Decrypt a single field value
        
        Args:
            encrypted_value: Base64 encoded encrypted string
            key_type: Type of encryption key to use
            
        Returns:
            Decrypted value
        """
        if not encrypted_value:
            return None
        
        try:
            # Decode base64 string
            encrypted_bytes = base64.b64decode(encrypted_value)
            
            # Try to decrypt with current active key first
            key = self.key_manager.get_active_key(key_type)
            if key:
                try:
                    decrypted_data = self._decrypt_data(encrypted_bytes, key)
                    return self._deserialize_value(decrypted_data)
                except (InvalidKey, InvalidTag):
                    # Try with other available keys (for key rotation)
                    pass
            
            # Try with all available keys for this type
            keys = self.key_manager.list_keys(key_type=key_type)
            for key in keys:
                if key.status.value in ['active', 'rotating']:
                    try:
                        decrypted_data = self._decrypt_data(encrypted_bytes, key)
                        return self._deserialize_value(decrypted_data)
                    except (InvalidKey, InvalidTag):
                        continue
            
            raise ValueError("Failed to decrypt data with any available key")
        
        except Exception as e:
            logger.error(f"Failed to decrypt field value: {e}")
            raise
    
    def encrypt_bulk_data(self, data: bytes, key_type: KeyType = KeyType.FINANCIAL_DATA) -> EncryptedData:
        """
        Encrypt bulk data with compression support
        
        Args:
            data: Raw data to encrypt
            key_type: Type of encryption key to use
            
        Returns:
            EncryptedData object
        """
        try:
            # Get active encryption key
            key = self.key_manager.get_active_key(key_type)
            if not key:
                raise ValueError(f"No active key found for {key_type.value}")
            
            # Compress data if enabled and beneficial
            if self.compression_enabled and len(data) > self.compression_threshold:
                compressed_data = gzip.compress(data)
                if len(compressed_data) < len(data):
                    data = compressed_data
                    compression_used = True
                else:
                    compression_used = False
            else:
                compression_used = False
            
            # Encrypt the data
            encrypted_data = self._encrypt_data(data, key, EncryptionMode.BULK_DATA)
            encrypted_data.compression = compression_used
            
            return encrypted_data
        
        except Exception as e:
            logger.error(f"Failed to encrypt bulk data: {e}")
            raise
    
    def decrypt_bulk_data(self, encrypted_data: EncryptedData) -> bytes:
        """
        Decrypt bulk data
        
        Args:
            encrypted_data: EncryptedData object
            
        Returns:
            Decrypted raw data
        """
        try:
            # Get the key used for encryption
            key = self.key_manager.get_key(encrypted_data.key_id)
            if not key:
                raise ValueError(f"Key {encrypted_data.key_id} not found")
            
            # Decrypt the data
            decrypted_data = self._decrypt_data(encrypted_data.encrypted_data, key)
            
            # Decompress if needed
            if encrypted_data.compression:
                decrypted_data = gzip.decompress(decrypted_data)
            
            return decrypted_data
        
        except Exception as e:
            logger.error(f"Failed to decrypt bulk data: {e}")
            raise
    
    def encrypt_session_data(self, session_data: Dict[str, Any]) -> str:
        """
        Encrypt Redis session data
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Serialize session data
            data = json.dumps(session_data, default=str).encode('utf-8')
            
            # Get session encryption key
            key = self.key_manager.get_active_key(KeyType.SESSION)
            if not key:
                raise ValueError("No active session encryption key found")
            
            # Encrypt session data
            encrypted_data = self._encrypt_data(data, key, EncryptionMode.SESSION)
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data.encrypted_data).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to encrypt session data: {e}")
            raise
    
    def decrypt_session_data(self, encrypted_session: str) -> Dict[str, Any]:
        """
        Decrypt Redis session data
        
        Args:
            encrypted_session: Base64 encoded encrypted session string
            
        Returns:
            Decrypted session data dictionary
        """
        try:
            # Decode base64 string
            encrypted_bytes = base64.b64decode(encrypted_session)
            
            # Try to decrypt with current active session key
            key = self.key_manager.get_active_key(KeyType.SESSION)
            if key:
                try:
                    decrypted_data = self._decrypt_data(encrypted_bytes, key)
                    return json.loads(decrypted_data.decode('utf-8'))
                except (InvalidKey, InvalidTag):
                    # Try with other available session keys
                    pass
            
            # Try with all available session keys
            keys = self.key_manager.list_keys(key_type=KeyType.SESSION)
            for key in keys:
                if key.status.value in ['active', 'rotating']:
                    try:
                        decrypted_data = self._decrypt_data(encrypted_bytes, key)
                        return json.loads(decrypted_data.decode('utf-8'))
                    except (InvalidKey, InvalidTag):
                        continue
            
            raise ValueError("Failed to decrypt session data with any available key")
        
        except Exception as e:
            logger.error(f"Failed to decrypt session data: {e}")
            raise
    
    def encrypt_cache_data(self, cache_key: str, cache_value: Any, ttl: int = 3600) -> Tuple[str, str]:
        """
        Encrypt Redis cache data
        
        Args:
            cache_key: Cache key
            cache_value: Cache value to encrypt
            ttl: Time to live in seconds
            
        Returns:
            Tuple of (encrypted_key, encrypted_value)
        """
        try:
            # Encrypt cache key
            encrypted_key = self.encrypt_field(cache_key, KeyType.API_KEYS)
            
            # Encrypt cache value
            if isinstance(cache_value, (dict, list)):
                value_data = json.dumps(cache_value, default=str).encode('utf-8')
            else:
                value_data = str(cache_value).encode('utf-8')
            
            encrypted_data = self.encrypt_bulk_data(value_data, KeyType.API_KEYS)
            encrypted_value = base64.b64encode(encrypted_data.encrypted_data).decode('utf-8')
            
            return encrypted_key, encrypted_value
        
        except Exception as e:
            logger.error(f"Failed to encrypt cache data: {e}")
            raise
    
    def decrypt_cache_data(self, encrypted_key: str, encrypted_value: str) -> Tuple[str, Any]:
        """
        Decrypt Redis cache data
        
        Args:
            encrypted_key: Encrypted cache key
            encrypted_value: Encrypted cache value
            
        Returns:
            Tuple of (cache_key, cache_value)
        """
        try:
            # Decrypt cache key
            cache_key = self.decrypt_field(encrypted_key, KeyType.API_KEYS)
            
            # Decrypt cache value
            encrypted_bytes = base64.b64decode(encrypted_value)
            encrypted_data = EncryptedData(
                encrypted_data=encrypted_bytes,
                key_id="",  # Will be determined during decryption
                algorithm="",
                iv=b""
            )
            
            cache_value_data = self.decrypt_bulk_data(encrypted_data)
            
            # Try to deserialize as JSON first, fallback to string
            try:
                cache_value = json.loads(cache_value_data.decode('utf-8'))
            except json.JSONDecodeError:
                cache_value = cache_value_data.decode('utf-8')
            
            return cache_key, cache_value
        
        except Exception as e:
            logger.error(f"Failed to decrypt cache data: {e}")
            raise
    
    def _encrypt_data(self, data: bytes, key: EncryptionKey, mode: EncryptionMode) -> EncryptedData:
        """
        Internal method to encrypt data using the specified key and mode
        """
        try:
            # Generate random IV
            iv = os.urandom(16)
            
            # Use AES-256-GCM for authenticated encryption
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.GCM(iv),
                backend=default_backend()
            )
            
            encryptor = cipher.encryptor()
            
            # Encrypt the data
            encrypted_data = encryptor.update(data) + encryptor.finalize()
            
            # Get the authentication tag
            tag = encryptor.tag
            
            # Create encrypted data object
            encrypted_data_obj = EncryptedData(
                encrypted_data=encrypted_data,
                key_id=key.key_id,
                algorithm=key.algorithm,
                iv=iv,
                tag=tag,
                timestamp=datetime.utcnow(),
                metadata={
                    'mode': mode.value,
                    'key_version': key.key_version,
                    'performance_mode': self.config.get_config().performance_mode
                }
            )
            
            return encrypted_data_obj
        
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: bytes, key: EncryptionKey) -> bytes:
        """
        Internal method to decrypt data using the specified key
        """
        try:
            # For now, we'll assume the encrypted data includes IV and tag
            # In a real implementation, you'd need to extract these from the encrypted data
            # This is a simplified version - you'd need to implement proper serialization
            
            # Extract IV and tag from encrypted data (this is a placeholder)
            # In practice, you'd need to store IV and tag separately or embed them
            iv = encrypted_data[:16]
            tag = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]
            
            # Decrypt using AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            return decrypted_data
        
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """
        Deserialize decrypted data back to original type
        """
        try:
            # Try to decode as string first
            string_value = data.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(string_value)
            except json.JSONDecodeError:
                pass
            
            # Try to parse as numeric values
            try:
                if '.' in string_value:
                    return float(string_value)
                else:
                    return int(string_value)
            except ValueError:
                pass
            
            # Return as string if all else fails
            return string_value
        
        except Exception as e:
            logger.error(f"Failed to deserialize value: {e}")
            return data.decode('utf-8', errors='ignore')
    
    def encrypt_database_field(self, value: Any, field_name: str, table_name: str) -> str:
        """
        Encrypt a database field with table/field context
        
        Args:
            value: Field value to encrypt
            field_name: Name of the database field
            table_name: Name of the database table
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Determine key type based on table and field
            key_type = self._determine_key_type_for_field(table_name, field_name)
            
            # Add context metadata
            context_data = {
                'value': value,
                'table': table_name,
                'field': field_name,
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
            # Encrypt with context
            data = json.dumps(context_data, default=str).encode('utf-8')
            key = self.key_manager.get_active_key(key_type)
            
            if not key:
                raise ValueError(f"No active key found for {key_type.value}")
            
            encrypted_data = self._encrypt_data(data, key, EncryptionMode.FIELD_LEVEL)
            return base64.b64encode(encrypted_data.encrypted_data).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to encrypt database field {table_name}.{field_name}: {e}")
            raise
    
    def decrypt_database_field(self, encrypted_value: str, field_name: str, table_name: str) -> Any:
        """
        Decrypt a database field with table/field context
        
        Args:
            encrypted_value: Encrypted field value
            field_name: Name of the database field
            table_name: Name of the database table
            
        Returns:
            Decrypted field value
        """
        try:
            # Determine key type based on table and field
            key_type = self._determine_key_type_for_field(table_name, field_name)
            
            # Decrypt the value
            decrypted_data = self.decrypt_field(encrypted_value, key_type)
            
            # Extract the actual value from context
            if isinstance(decrypted_data, dict) and 'value' in decrypted_data:
                return decrypted_data['value']
            
            return decrypted_data
        
        except Exception as e:
            logger.error(f"Failed to decrypt database field {table_name}.{field_name}: {e}")
            raise
    
    def _determine_key_type_for_field(self, table_name: str, field_name: str) -> KeyType:
        """
        Determine the appropriate key type for a database field
        """
        # Financial data fields
        financial_fields = {
            'income', 'salary', 'expenses', 'savings', 'debt', 'balance',
            'amount', 'cost', 'price', 'value', 'budget', 'payment'
        }
        
        # PII fields
        pii_fields = {
            'ssn', 'social_security', 'tax_id', 'passport', 'license',
            'address', 'phone', 'birth_date', 'national_id'
        }
        
        # Session fields
        session_fields = {
            'session_id', 'token', 'auth_code', 'refresh_token'
        }
        
        # Check field name patterns
        field_lower = field_name.lower()
        
        if any(fin_field in field_lower for fin_field in financial_fields):
            return KeyType.FINANCIAL_DATA
        elif any(pii_field in field_lower for pii_field in pii_fields):
            return KeyType.PII
        elif any(sess_field in field_lower for sess_field in session_fields):
            return KeyType.SESSION
        else:
            # Default to financial data for unknown fields
            return KeyType.FINANCIAL_DATA
    
    def get_encryption_stats(self) -> Dict[str, Any]:
        """
        Get encryption service statistics
        """
        try:
            key_stats = self.key_manager.get_key_statistics()
            
            return {
                'encryption_service': 'active',
                'algorithm': self.config.get_config().algorithm.value,
                'performance_mode': self.config.get_config().performance_mode,
                'compression_enabled': self.compression_enabled,
                'key_statistics': key_stats,
                'performance_settings': self.performance_settings
            }
        
        except Exception as e:
            logger.error(f"Failed to get encryption stats: {e}")
            return {'encryption_service': 'error', 'error': str(e)}

# Global encryption service instance
encryption_service = EncryptionService()

def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance"""
    return encryption_service
