#!/usr/bin/env python3
"""
Encryption Service Utility

Simple encryption service for testing purposes
"""

import hashlib
import base64
from typing import Any, Dict


class EncryptionService:
    """Simple encryption service for testing"""
    
    def __init__(self, secret_key: str = "test_secret_key"):
        self.secret_key = secret_key
    
    def encrypt(self, data: str) -> str:
        """Encrypt data (simple base64 encoding for testing)"""
        if isinstance(data, dict):
            data = json.dumps(data)
        encoded = base64.b64encode(data.encode()).decode()
        return f"encrypted_{encoded}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        if encrypted_data.startswith("encrypted_"):
            encoded = encrypted_data[10:]  # Remove "encrypted_" prefix
            return base64.b64decode(encoded.encode()).decode()
        return encrypted_data
