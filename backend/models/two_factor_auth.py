"""
Two-Factor Authentication Model for MINGUS
Handles TOTP secrets, backup codes, and 2FA configuration
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import secrets
import hashlib
from .base import Base

class TwoFactorAuth(Base):
    """Two-factor authentication configuration for users"""
    __tablename__ = 'two_factor_auth'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # TOTP Configuration
    encrypted_totp_secret = Column(Text, nullable=False)  # Encrypted TOTP secret
    totp_algorithm = Column(String(10), default='SHA1')  # TOTP algorithm (SHA1, SHA256, SHA512)
    totp_digits = Column(Integer, default=6)  # Number of digits in TOTP
    totp_period = Column(Integer, default=30)  # TOTP period in seconds
    
    # 2FA Status
    is_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    setup_completed_at = Column(DateTime, nullable=True)
    
    # SMS Fallback Configuration
    sms_fallback_enabled = Column(Boolean, default=False)
    encrypted_sms_secret = Column(Text, nullable=True)  # Encrypted SMS fallback secret
    
    # Security Settings
    max_attempts = Column(Integer, default=5)  # Max failed attempts before lockout
    lockout_until = Column(DateTime, nullable=True)  # Account lockout until timestamp
    last_used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="two_factor_auth")
    backup_codes = relationship("TwoFactorBackupCode", back_populates="two_factor_auth", cascade="all, delete-orphan")
    verification_attempts = relationship("TwoFactorVerificationAttempt", back_populates="two_factor_auth", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_two_factor_user_id', 'user_id'),
        Index('idx_two_factor_enabled', 'is_enabled'),
        Index('idx_two_factor_lockout', 'lockout_until'),
    )
    
    def __repr__(self):
        return f'<TwoFactorAuth user_id={self.user_id} enabled={self.is_enabled}>'
    
    def is_locked_out(self) -> bool:
        """Check if 2FA is locked out due to failed attempts"""
        if not self.lockout_until:
            return False
        return datetime.utcnow() < self.lockout_until
    
    def increment_failed_attempts(self) -> None:
        """Increment failed attempts and potentially lock out account"""
        # This will be handled by the service layer
        pass
    
    def reset_failed_attempts(self) -> None:
        """Reset failed attempts and remove lockout"""
        self.lockout_until = None
    
    def mark_as_used(self) -> None:
        """Mark 2FA as used"""
        self.last_used_at = datetime.utcnow()
        self.is_verified = True

class TwoFactorBackupCode(Base):
    """Backup codes for 2FA recovery"""
    __tablename__ = 'two_factor_backup_codes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    two_factor_auth_id = Column(Integer, ForeignKey('two_factor_auth.id', ondelete='CASCADE'), nullable=False)
    
    # Encrypted backup code (hashed for security)
    encrypted_code_hash = Column(Text, nullable=False)
    
    # Usage tracking
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    used_ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 support
    used_user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    two_factor_auth = relationship("TwoFactorAuth", back_populates="backup_codes")
    
    # Indexes
    __table_args__ = (
        Index('idx_backup_code_two_factor_id', 'two_factor_auth_id'),
        Index('idx_backup_code_used', 'is_used'),
    )
    
    def __repr__(self):
        return f'<TwoFactorBackupCode id={self.id} used={self.is_used}>'
    
    def mark_as_used(self, ip_address: str = None, user_agent: str = None) -> None:
        """Mark backup code as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_ip_address = ip_address
        self.used_user_agent = user_agent

class TwoFactorVerificationAttempt(Base):
    """Audit log for 2FA verification attempts"""
    __tablename__ = 'two_factor_verification_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    two_factor_auth_id = Column(Integer, ForeignKey('two_factor_auth.id', ondelete='CASCADE'), nullable=False)
    
    # Attempt details
    attempt_type = Column(String(20), nullable=False)  # 'totp', 'sms', 'backup_code'
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Security metadata
    country_code = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Timestamps
    attempted_at = Column(DateTime, default=func.now())
    
    # Relationships
    two_factor_auth = relationship("TwoFactorAuth", back_populates="verification_attempts")
    
    # Indexes
    __table_args__ = (
        Index('idx_verification_attempt_two_factor_id', 'two_factor_auth_id'),
        Index('idx_verification_attempt_success', 'success'),
        Index('idx_verification_attempt_type', 'attempt_type'),
        Index('idx_verification_attempt_timestamp', 'attempted_at'),
    )
    
    def __repr__(self):
        return f'<TwoFactorVerificationAttempt id={self.id} type={self.attempt_type} success={self.success}>'

class TwoFactorRecoveryRequest(Base):
    """Recovery requests for lost 2FA devices"""
    __tablename__ = 'two_factor_recovery_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Recovery details
    recovery_method = Column(String(20), nullable=False)  # 'sms', 'email', 'admin'
    encrypted_recovery_code = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'expired'
    expires_at = Column(DateTime, nullable=False)
    
    # Admin approval
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_recovery_request_user_id', 'user_id'),
        Index('idx_recovery_request_status', 'status'),
        Index('idx_recovery_request_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f'<TwoFactorRecoveryRequest id={self.id} method={self.recovery_method} status={self.status}>'
    
    def is_expired(self) -> bool:
        """Check if recovery request is expired"""
        return datetime.utcnow() > self.expires_at
    
    def approve(self, admin_user_id: int) -> None:
        """Approve recovery request"""
        self.status = 'approved'
        self.approved_by = admin_user_id
        self.approved_at = datetime.utcnow()
    
    def reject(self, admin_user_id: int, reason: str) -> None:
        """Reject recovery request"""
        self.status = 'rejected'
        self.approved_by = admin_user_id
        self.rejection_reason = reason
