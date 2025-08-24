"""
Encryption utilities for the Mingus application
"""

import base64
from typing import Optional
from cryptography.fernet import Fernet

from backend.models.encrypted_financial_models import (
    encrypt_value,
    decrypt_value,
    get_encryption_key,
)


def _get_fernet() -> Fernet:
    key = get_encryption_key()
    return Fernet(key if isinstance(key, (bytes, bytearray)) else key.encode())


def encrypt_data(plaintext: str) -> str:
    if plaintext is None:
        return ""
    f = _get_fernet()
    token = f.encrypt(plaintext.encode())
    return base64.b64encode(token).decode()


def decrypt_data(token_b64: str) -> Optional[str]:
    if not token_b64:
        return None
    try:
        f = _get_fernet()
        token = base64.b64decode(token_b64.encode())
        return f.decrypt(token).decode()
    except Exception:
        return None


__all__ = ['encrypt_value', 'decrypt_value', 'encrypt_data', 'decrypt_data']