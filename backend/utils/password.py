#!/usr/bin/env python3
"""
Password Security Utility

Secure password hashing and verification using bcrypt
"""

import bcrypt
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Bcrypt rounds - higher is more secure but slower
# 12 rounds is recommended by OWASP (takes ~300ms per hash)
BCRYPT_ROUNDS = 12


def hash_password(password: str, rounds: int = BCRYPT_ROUNDS) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password to hash
        rounds: Number of bcrypt rounds (default: 12, recommended by OWASP)
    
    Returns:
        Bcrypt hashed password as string
    
    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def check_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash
    
    Args:
        password: Plain text password to verify
        hashed: Bcrypt hashed password string
    
    Returns:
        True if password matches hash, False otherwise
    
    Raises:
        ValueError: If inputs are invalid
    """
    if not password:
        return False
    
    if not hashed:
        logger.warning("Empty hash provided for password verification")
        return False
    
    try:
        # Verify password against hash
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def needs_rehash(hashed: str, rounds: int = BCRYPT_ROUNDS) -> bool:
    """
    Check if a password hash needs to be rehashed (e.g., if rounds changed)
    
    Args:
        hashed: Bcrypt hashed password string
        rounds: Desired number of rounds
    
    Returns:
        True if hash should be rehashed, False otherwise
    """
    try:
        # Extract rounds from hash
        # Bcrypt hash format: $2b$rounds$salt+hash
        parts = hashed.split('$')
        if len(parts) < 4:
            return True
        
        current_rounds = int(parts[2])
        return current_rounds < rounds
    
    except (ValueError, IndexError):
        # If we can't parse the hash, assume it needs rehashing
        return True


def verify_password_strength(password: str, min_length: int = 8) -> tuple[bool, Optional[str]]:
    """
    Verify password strength
    
    Args:
        password: Password to check
        min_length: Minimum password length (default: 8)
    
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if password meets requirements
        error_message: Error message if password is invalid, None otherwise
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    # Check for at least one special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, None
