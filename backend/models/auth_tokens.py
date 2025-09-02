"""
Authentication Token Models for MINGUS Application
Provides secure token management for authentication and verification
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class AuthToken(Base):
    """Model for authentication tokens"""
    __tablename__ = 'auth_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_type = Column(String(50), nullable=False)  # refresh, access, etc.
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="auth_tokens")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_auth_tokens_user_id', 'user_id'),
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
