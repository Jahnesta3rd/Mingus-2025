"""
Email Verification Model for MINGUS Flask Application
Handles secure email verification with comprehensive security features
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import hmac
import os
from .base import Base

class EmailVerification(Base):
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    email = Column(String(255), nullable=False, index=True)
    verification_token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resend_count = Column(Integer, default=0, nullable=False)
    last_resend_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional security fields
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    verification_type = Column(String(50), default='signup', nullable=False)  # signup, email_change, password_reset
    old_email = Column(String(255), nullable=True)  # For email change verification
    
    # Rate limiting fields
    failed_attempts = Column(Integer, default=0, nullable=False)
    last_failed_attempt = Column(DateTime(timezone=True), nullable=True)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="email_verification")
    
    # Indexes for performance and security
    __table_args__ = (
        Index('idx_email_verification_user_type', 'user_id', 'verification_type'),
        Index('idx_email_verification_expires_created', 'expires_at', 'created_at'),
        Index('idx_email_verification_rate_limit', 'user_id', 'failed_attempts', 'locked_until'),
    )
    
    def __repr__(self):
        return f'<EmailVerification {self.email} - {self.verification_type}>'
    
    @property
    def is_expired(self) -> bool:
        """Check if verification token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_verified(self) -> bool:
        """Check if email has been verified"""
        return self.verified_at is not None
    
    @property
    def is_locked(self) -> bool:
        """Check if verification is temporarily locked due to failed attempts"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def can_resend(self) -> bool:
        """Check if verification email can be resent"""
        if self.is_verified:
            return False
        
        # Rate limiting: max 5 resends per day
        if self.resend_count >= 5:
            return False
        
        # Check if enough time has passed since last resend
        if self.last_resend_at:
            time_since_last = datetime.utcnow() - self.last_resend_at
            if time_since_last < timedelta(hours=1):  # 1 hour cooldown
                return False
        
        return True
    
    @property
    def remaining_attempts(self) -> int:
        """Get remaining verification attempts before lockout"""
        max_attempts = 5
        return max(0, max_attempts - self.failed_attempts)
    
    def generate_token(self, length: int = 64) -> str:
        """Generate a cryptographically secure verification token"""
        return secrets.token_urlsafe(length)
    
    def hash_token(self, token: str) -> str:
        """Hash the verification token using HMAC-SHA256"""
        secret_key = os.getenv('EMAIL_VERIFICATION_SECRET', 'default-secret-key')
        return hmac.new(
            secret_key.encode('utf-8'),
            token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_token(self, token: str) -> bool:
        """Verify the provided token against the stored hash"""
        if self.is_expired or self.is_verified:
            return False
        
        expected_hash = self.verification_token_hash
        provided_hash = self.hash_token(token)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, provided_hash)
    
    def mark_verified(self) -> None:
        """Mark the email as verified"""
        self.verified_at = datetime.utcnow()
    
    def increment_resend_count(self) -> None:
        """Increment the resend counter and update timestamp"""
        self.resend_count += 1
        self.last_resend_at = datetime.utcnow()
    
    def record_failed_attempt(self) -> None:
        """Record a failed verification attempt"""
        self.failed_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        # Lock after 5 failed attempts for 1 hour
        if self.failed_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(hours=1)
    
    def reset_failed_attempts(self) -> None:
        """Reset failed attempts counter"""
        self.failed_attempts = 0
        self.last_failed_attempt = None
        self.locked_until = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'verification_type': self.verification_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resend_count': self.resend_count,
            'last_resend_at': self.last_resend_at.isoformat() if self.last_resend_at else None,
            'is_expired': self.is_expired,
            'is_verified': self.is_verified,
            'is_locked': self.is_locked,
            'can_resend': self.can_resend,
            'remaining_attempts': self.remaining_attempts,
            'old_email': self.old_email
        }
    
    @classmethod
    def create_verification(cls, user_id: int, email: str, verification_type: str = 'signup', 
                           old_email: str = None, expires_in_hours: int = 24) -> 'EmailVerification':
        """Create a new email verification record"""
        token = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        verification = cls(
            user_id=user_id,
            email=email,
            verification_token_hash=cls.hash_token_static(token),
            expires_at=expires_at,
            verification_type=verification_type,
            old_email=old_email
        )
        
        return verification, token
    
    @classmethod
    def hash_token_static(cls, token: str) -> str:
        """Static method to hash tokens (for creation)"""
        secret_key = os.getenv('EMAIL_VERIFICATION_SECRET', 'default-secret-key')
        return hmac.new(
            secret_key.encode('utf-8'),
            token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @classmethod
    def is_rate_limited(cls, user_id: int, action: str) -> bool:
        """Check if user is rate limited for specific actions"""
        # This would be implemented with Redis for production
        # For now, return False (no rate limiting at model level)
        return False
