#!/usr/bin/env python3
"""
Encryption Service Utility

Production-ready encryption service using Fernet (symmetric encryption)
Fernet guarantees that a message encrypted using it cannot be manipulated or read without the key.
"""

import os
import json
import logging
from typing import Any, Dict, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Secure encryption service using Fernet (AES-128 in CBC mode with HMAC)
    
    Fernet provides:
    - Authenticated encryption (prevents tampering)
    - Automatic timestamping
    - Secure key derivation
    """
    
    def __init__(self, encryption_key: Union[str, bytes, None] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Encryption key from environment variable or provided directly.
                          If None, will try to get from ENCRYPTION_KEY environment variable.
                          If not found, will raise ValueError (security requirement).
        """
        if encryption_key is None:
            encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable is required for encryption. "
                "Set it in your .env file or environment."
            )
        
        # Handle key format
        if isinstance(encryption_key, str):
            # If it's a Fernet key (base64 URL-safe), use it directly
            try:
                # Try to decode as base64 to validate format
                base64.urlsafe_b64decode(encryption_key)
                if len(encryption_key) == 44:  # Fernet key length
                    self.cipher_suite = Fernet(encryption_key.encode())
                else:
                    # Derive Fernet key from password using PBKDF2
                    self.cipher_suite = self._derive_key(encryption_key)
            except Exception:
                # If not valid base64, derive key from password
                self.cipher_suite = self._derive_key(encryption_key)
        else:
            # If bytes, assume it's already a Fernet key
            self.cipher_suite = Fernet(encryption_key)
    
    def _derive_key(self, password: str, salt: bytes = None) -> Fernet:
        """
        Derive a Fernet key from a password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Optional salt (will generate if not provided)
        
        Returns:
            Fernet cipher suite with derived key
        """
        if salt is None:
            # Use a fixed salt derived from application secret for consistency
            # In production, consider using a stored salt per encryption
            app_secret = os.environ.get('SECRET_KEY', 'mingus-app-secret')
            salt = hashes.Hash(hashes.SHA256())
            salt.update(app_secret.encode())
            salt = salt.finalize()[:16]  # Use first 16 bytes as salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def encrypt(self, data: Union[str, dict]) -> str:
        """
        Encrypt data using Fernet
        
        Args:
            data: String or dictionary to encrypt
        
        Returns:
            Base64-encoded encrypted string
        
        Raises:
            ValueError: If data cannot be encrypted
        """
        try:
            # Convert dict to JSON string if needed
            if isinstance(data, dict):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            
            # Encrypt the data
            encrypted_bytes = self.cipher_suite.encrypt(data_str.encode('utf-8'))
            
            # Return base64-encoded string for safe storage/transmission
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet
        
        Args:
            encrypted_data: Base64-encoded encrypted string
        
        Returns:
            Decrypted string
        
        Raises:
            ValueError: If decryption fails (invalid key, tampered data, etc.)
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data. Data may be corrupted or key is incorrect: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt a dictionary, preserving structure
        
        Args:
            data: Dictionary to encrypt
        
        Returns:
            Dictionary with encrypted values (as strings)
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, (str, dict)):
                encrypted[key] = self.encrypt(value)
            else:
                # For non-string values, convert to string first
                encrypted[key] = self.encrypt(str(value))
        return encrypted
    
    def decrypt_dict(self, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypt a dictionary
        
        Args:
            encrypted_data: Dictionary with encrypted string values
        
        Returns:
            Dictionary with decrypted values (attempts JSON parsing)
        """
        decrypted = {}
        for key, encrypted_value in encrypted_data.items():
            try:
                decrypted_str = self.decrypt(encrypted_value)
                # Try to parse as JSON
                try:
                    decrypted[key] = json.loads(decrypted_str)
                except json.JSONDecodeError:
                    decrypted[key] = decrypted_str
            except Exception as e:
                logger.warning(f"Failed to decrypt key '{key}': {e}")
                decrypted[key] = encrypted_value  # Return original if decryption fails
        return decrypted
