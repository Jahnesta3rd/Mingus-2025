"""
Security and Compliance Database Models for MINGUS

This module defines the database models for security and compliance features:
- Encryption key management
- User consent tracking
- Data retention policies
- Security audit logs
- PCI DSS compliance tracking
- GDPR compliance management
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from backend.models.base import Base

class EncryptionKey(Base):
    """Encryption key management model"""
    
    __tablename__ = 'encryption_keys'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Key metadata
    key_id = Column(String(255), nullable=False, unique=True, index=True)
    key_material = Column(LargeBinary, nullable=False)  # Encrypted key material
    algorithm = Column(String(50), nullable=False)  # AES-256-GCM, Fernet, etc.
    key_type = Column(String(50), nullable=False)  # symmetric, asymmetric, derived
    
    # Key lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    rotated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Key usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security metadata
    key_version = Column(String(20), nullable=False, default='1.0')
    key_purpose = Column(String(100), nullable=False)  # data_encryption, token_encryption, etc.
    data_classification = Column(String(50), nullable=False)  # public, internal, confidential, restricted, highly_restricted
    
    # Indexes
    __table_args__ = (
        Index('idx_encryption_keys_active', 'is_active'),
        Index('idx_encryption_keys_algorithm', 'algorithm'),
        Index('idx_encryption_keys_purpose', 'key_purpose'),
        Index('idx_encryption_keys_classification', 'data_classification'),
        Index('idx_encryption_keys_expires', 'expires_at'),
    )
    
    @validates('algorithm')
    def validate_algorithm(self, key, value):
        """Validate encryption algorithm"""
        valid_algorithms = ['AES-256-GCM', 'Fernet', 'RSA-2048', 'RSA-4096']
        if value not in valid_algorithms:
            raise ValueError(f"Invalid encryption algorithm: {value}")
        return value
    
    @validates('key_type')
    def validate_key_type(self, key, value):
        """Validate key type"""
        valid_types = ['symmetric', 'asymmetric', 'derived']
        if value not in valid_types:
            raise ValueError(f"Invalid key type: {value}")
        return value
    
    def __repr__(self):
        return f'<EncryptionKey {self.key_id} ({self.algorithm})>'

class UserConsent(Base):
    """User consent tracking for GDPR compliance"""
    
    __tablename__ = 'user_consents'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Consent information
    consent_type = Column(String(100), nullable=False, index=True)
    granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Consent metadata
    consent_version = Column(String(20), nullable=False, default='1.0')
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=False)
    
    # Data processing details
    data_processing_purposes = Column(JSON, nullable=False, default=list)
    third_parties = Column(JSON, nullable=False, default=list)
    
    # Consent lifecycle
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(255), nullable=True)
    revoked_ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="consents")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_consents_user_type', 'user_id', 'consent_type'),
        Index('idx_user_consents_granted', 'granted'),
        Index('idx_user_consents_expires', 'expires_at'),
        Index('idx_user_consents_revoked', 'revoked_at'),
    )
    
    @validates('consent_type')
    def validate_consent_type(self, key, value):
        """Validate consent type"""
        valid_types = [
            'plaid_account_access',
            'transaction_data_processing',
            'identity_verification',
            'analytics_processing',
            'marketing_communications',
            'third_party_sharing'
        ]
        if value not in valid_types:
            raise ValueError(f"Invalid consent type: {value}")
        return value
    
    @validates('ip_address')
    def validate_ip_address(self, key, value):
        """Validate IP address format"""
        # Basic IP validation (IPv4 or IPv6)
        if not value or len(value) > 45:
            raise ValueError("Invalid IP address format")
        return value
    
    def __repr__(self):
        return f'<UserConsent {self.consent_type} for user {self.user_id}>'

class DataRetentionRecord(Base):
    """Data retention policy tracking"""
    
    __tablename__ = 'data_retention_records'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Retention information
    data_type = Column(String(100), nullable=False, index=True)
    retention_policy = Column(String(50), nullable=False, index=True)
    
    # Retention lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    deletion_scheduled = Column(Boolean, default=True, nullable=False)
    deletion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Deletion tracking
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deletion_method = Column(String(50), nullable=True)  # soft_delete, hard_delete, anonymize
    deletion_verified = Column(Boolean, default=False, nullable=False)
    
    # Retention metadata
    retention_reason = Column(String(255), nullable=True)
    legal_basis = Column(String(100), nullable=True)  # contract, legal_obligation, legitimate_interest, consent
    data_volume = Column(Integer, nullable=True)  # Number of records
    
    # Indexes
    __table_args__ = (
        Index('idx_data_retention_user_type', 'user_id', 'data_type'),
        Index('idx_data_retention_policy', 'retention_policy'),
        Index('idx_data_retention_expires', 'expires_at'),
        Index('idx_data_retention_deletion', 'deletion_date'),
        Index('idx_data_retention_deleted', 'deleted_at'),
    )
    
    @validates('retention_policy')
    def validate_retention_policy(self, key, value):
        """Validate retention policy"""
        valid_policies = ['immediate', 'short_term', 'medium_term', 'long_term', 'permanent']
        if value not in valid_policies:
            raise ValueError(f"Invalid retention policy: {value}")
        return value
    
    @validates('deletion_method')
    def validate_deletion_method(self, key, value):
        """Validate deletion method"""
        if value:
            valid_methods = ['soft_delete', 'hard_delete', 'anonymize']
            if value not in valid_methods:
                raise ValueError(f"Invalid deletion method: {value}")
        return value
    
    def __repr__(self):
        return f'<DataRetentionRecord {self.data_type} for user {self.user_id}>'

class SecurityAuditLog(Base):
    """Security audit logging for compliance"""
    
    __tablename__ = 'security_audit_logs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Audit information
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Request details
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Security assessment
    success = Column(Boolean, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    threat_score = Column(Integer, nullable=True)  # 0-100 threat assessment
    
    # Additional details
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Session information
    session_id = Column(String(255), nullable=True, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # Geolocation (optional)
    country_code = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_security_audit_timestamp', 'timestamp'),
        Index('idx_security_audit_user_action', 'user_id', 'action'),
        Index('idx_security_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_security_audit_risk', 'risk_level'),
        Index('idx_security_audit_success', 'success'),
        Index('idx_security_audit_session', 'session_id'),
        Index('idx_security_audit_correlation', 'correlation_id'),
    )
    
    @validates('risk_level')
    def validate_risk_level(self, key, value):
        """Validate risk level"""
        valid_levels = ['low', 'medium', 'high', 'critical']
        if value not in valid_levels:
            raise ValueError(f"Invalid risk level: {value}")
        return value
    
    @validates('threat_score')
    def validate_threat_score(self, key, value):
        """Validate threat score"""
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Threat score must be between 0 and 100")
        return value
    
    def __repr__(self):
        return f'<SecurityAuditLog {self.action} by {self.user_id} at {self.timestamp}>'

class PCIComplianceRecord(Base):
    """PCI DSS compliance tracking"""
    
    __tablename__ = 'pci_compliance_records'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # PCI requirement tracking
    requirement_id = Column(String(20), nullable=False, index=True)  # 3.1, 4.1, etc.
    requirement_name = Column(String(255), nullable=False)
    requirement_description = Column(Text, nullable=False)
    
    # Compliance status
    compliant = Column(Boolean, nullable=False)
    last_assessed = Column(DateTime(timezone=True), nullable=False)
    next_assessment = Column(DateTime(timezone=True), nullable=True)
    
    # Assessment details
    assessment_method = Column(String(100), nullable=True)  # automated, manual, third_party
    assessor = Column(String(255), nullable=True)
    assessment_notes = Column(Text, nullable=True)
    
    # Violations and remediation
    violations_found = Column(JSON, nullable=True)
    remediation_actions = Column(JSON, nullable=True)
    remediation_completed = Column(Boolean, default=False, nullable=False)
    remediation_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Evidence and documentation
    evidence_files = Column(JSON, nullable=True)  # List of file references
    documentation_urls = Column(JSON, nullable=True)  # List of documentation URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_pci_compliance_requirement', 'requirement_id'),
        Index('idx_pci_compliance_status', 'compliant'),
        Index('idx_pci_compliance_assessment', 'last_assessed'),
        Index('idx_pci_compliance_next', 'next_assessment'),
        Index('idx_pci_compliance_remediation', 'remediation_completed'),
    )
    
    @validates('requirement_id')
    def validate_requirement_id(self, key, value):
        """Validate PCI requirement ID format"""
        # PCI requirements follow format like "3.1", "4.1", etc.
        if not value or not value.replace('.', '').isdigit():
            raise ValueError("Invalid PCI requirement ID format")
        return value
    
    def __repr__(self):
        return f'<PCIComplianceRecord {self.requirement_id} ({self.compliant})>'

class GDPRDataRequest(Base):
    """GDPR data subject request tracking"""
    
    __tablename__ = 'gdpr_data_requests'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Request information
    request_type = Column(String(50), nullable=False, index=True)  # access, rectification, erasure, portability
    request_reason = Column(Text, nullable=True)
    
    # Request lifecycle
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, default='pending', index=True)  # pending, processing, completed, rejected
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing details
    assigned_to = Column(String(255), nullable=True)
    processing_notes = Column(Text, nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Request details
    data_categories = Column(JSON, nullable=True)  # Categories of data requested
    date_range = Column(JSON, nullable=True)  # Date range for data
    format_preference = Column(String(50), nullable=True)  # json, csv, pdf
    
    # Verification
    verification_method = Column(String(50), nullable=True)  # email, phone, id_document
    verification_completed = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    
    # Response
    response_data = Column(JSON, nullable=True)  # Response data or file references
    response_format = Column(String(50), nullable=True)
    response_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="gdpr_requests")
    
    # Indexes
    __table_args__ = (
        Index('idx_gdpr_requests_user_type', 'user_id', 'request_type'),
        Index('idx_gdpr_requests_status', 'status'),
        Index('idx_gdpr_requests_submitted', 'submitted_at'),
        Index('idx_gdpr_requests_completed', 'completed_at'),
        Index('idx_gdpr_requests_verification', 'verification_completed'),
    )
    
    @validates('request_type')
    def validate_request_type(self, key, value):
        """Validate GDPR request type"""
        valid_types = ['access', 'rectification', 'erasure', 'portability', 'restriction', 'objection']
        if value not in valid_types:
            raise ValueError(f"Invalid GDPR request type: {value}")
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """Validate request status"""
        valid_statuses = ['pending', 'processing', 'completed', 'rejected', 'cancelled']
        if value not in valid_statuses:
            raise ValueError(f"Invalid request status: {value}")
        return value
    
    def __repr__(self):
        return f'<GDPRDataRequest {self.request_type} for user {self.user_id}>'

class SecurityIncident(Base):
    """Security incident tracking"""
    
    __tablename__ = 'security_incidents'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Incident information
    incident_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    status = Column(String(50), nullable=False, default='open', index=True)  # open, investigating, resolved, closed
    
    # Incident details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    affected_users = Column(Integer, nullable=True)
    affected_data = Column(JSON, nullable=True)
    
    # Timeline
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Response
    assigned_to = Column(String(255), nullable=True)
    response_actions = Column(JSON, nullable=True)
    containment_measures = Column(Text, nullable=True)
    remediation_actions = Column(Text, nullable=True)
    
    # Impact assessment
    data_breach = Column(Boolean, default=False, nullable=False)
    financial_impact = Column(Integer, nullable=True)  # Estimated cost in cents
    reputation_impact = Column(String(50), nullable=True)  # low, medium, high
    
    # Compliance
    regulatory_notification = Column(Boolean, default=False, nullable=False)
    notification_date = Column(DateTime(timezone=True), nullable=True)
    notification_authority = Column(String(255), nullable=True)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_security_incidents_type', 'incident_type'),
        Index('idx_security_incidents_severity', 'severity'),
        Index('idx_security_incidents_status', 'status'),
        Index('idx_security_incidents_detected', 'detected_at'),
        Index('idx_security_incidents_resolved', 'resolved_at'),
        Index('idx_security_incidents_breach', 'data_breach'),
    )
    
    @validates('severity')
    def validate_severity(self, key, value):
        """Validate incident severity"""
        valid_severities = ['low', 'medium', 'high', 'critical']
        if value not in valid_severities:
            raise ValueError(f"Invalid incident severity: {value}")
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """Validate incident status"""
        valid_statuses = ['open', 'investigating', 'resolved', 'closed']
        if value not in valid_statuses:
            raise ValueError(f"Invalid incident status: {value}")
        return value
    
    def __repr__(self):
        return f'<SecurityIncident {self.title} ({self.severity})>' 