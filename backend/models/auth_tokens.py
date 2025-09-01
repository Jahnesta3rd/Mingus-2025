"""
Authentication Token Models for Email Verification and Password Reset
Secure token management with expiration and rate limiting
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import secrets
import hashlib
from .base import Base

class AuthToken(Base):
    __tablename__ = 'auth_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_type = Column(String(50), nullable=False)  # 'email_verification', 'password_reset'
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="auth_tokens")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_auth_tokens_user_type', 'user_id', 'token_type'),
        Index('idx_auth_tokens_expires', 'expires_at'),
        Index('idx_auth_tokens_hash', 'token_hash'),
    )
    
    def __repr__(self):
        return f'<AuthToken {self.token_type} for user {self.user_id}>'
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def hash_token(cls, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_used(self) -> bool:
        """Check if token has been used"""
        return self.used_at is not None
    
    def mark_used(self):
        """Mark token as used"""
        self.used_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert token to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class EmailVerification(Base):
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False)
    verification_token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    resend_count = Column(Integer, default=0)
    last_resend_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="email_verification")
    
    def __repr__(self):
        return f'<EmailVerification for user {self.user_id}>'
    
    def is_expired(self) -> bool:
        """Check if verification has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_verified(self) -> bool:
        """Check if email is verified"""
        return self.verified_at is not None
    
    def mark_verified(self):
        """Mark email as verified"""
        self.verified_at = datetime.utcnow()
    
    def can_resend(self) -> bool:
        """Check if verification email can be resent"""
        if self.last_resend_at is None:
            return True
        
        # Allow resend after 5 minutes
        return datetime.utcnow() > self.last_resend_at + timedelta(minutes=5)
    
    def increment_resend_count(self):
        """Increment resend counter"""
        self.resend_count += 1
        self.last_resend_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert verification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resend_count': self.resend_count,
            'last_resend_at': self.last_resend_at.isoformat() if self.last_resend_at else None
        }
