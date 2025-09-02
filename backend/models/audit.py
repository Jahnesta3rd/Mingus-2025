"""
MINGUS Application - Audit Database Models
==========================================

SQLAlchemy models for comprehensive audit logging system.
Provides structured storage for all audit events with JSONB support
for flexible data storage and efficient querying.

Features:
- Comprehensive audit log tables
- JSONB fields for flexible data storage
- Proper indexing for performance
- Partitioning support for large datasets
- Data retention policies
- Compliance reporting data models

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Boolean, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    JSON, LargeBinary, Numeric, SmallInteger
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP, TEXT
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

# Import base model
from .base import Base


class AuditLog(Base):
    """
    Main audit log table for all audit events.
    
    Stores comprehensive audit trail with JSONB data fields for
    flexible storage and efficient querying.
    """
    __tablename__ = 'audit_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Audit identification
    audit_id = Column(UUID(as_uuid=True), unique=True, nullable=False, 
                     default=uuid.uuid4, index=True)
    
    # Timestamp and metadata
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                      default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now(), onupdate=func.now())
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Event description
    description = Column(Text, nullable=False)
    
    # User and session context
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Request context
    request_id = Column(String(100), nullable=True, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    
    # Network context
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Source information
    source = Column(String(200), nullable=True, index=True)
    endpoint = Column(String(200), nullable=True)
    
    # Data storage
    data = Column(JSONB, nullable=True, default={})
    audit_metadata = Column(JSONB, nullable=True, default={})
    
    # Integrity and security
    hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    encrypted = Column(Boolean, default=False)
    retention_until = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    
    # Performance and partitioning
    partition_key = Column(String(20), nullable=True, index=True)  # For table partitioning
    
    # Constraints
    __table_args__ = (
        # Ensure audit_id is unique
        UniqueConstraint('audit_id', name='uq_audit_logs_audit_id'),
        
        # Check constraints for data validation
        CheckConstraint("severity IN ('debug', 'info', 'warning', 'error', 'critical', 'security', 'compliance')", 
                       name='chk_audit_logs_severity'),
        CheckConstraint("category IN ('financial', 'user_activity', 'security', 'compliance', 'system', 'data_access', 'payment', 'subscription')", 
                       name='chk_audit_logs_category'),
        
        # Indexes for performance
        Index('idx_audit_logs_timestamp_category', 'timestamp', 'category'),
        Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_logs_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_logs_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_audit_logs_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_audit_logs_session_timestamp', 'session_id', 'timestamp'),
        
        # JSONB indexes for efficient querying
        Index('idx_audit_logs_data_gin', 'data', postgresql_using='gin'),
        Index('idx_audit_logs_audit_metadata_gin', 'audit_metadata', postgresql_using='gin'),
        
        # Partitioning support
        {'postgresql_partition_by': 'RANGE (timestamp)'}
    )
    
    @validates('data', 'metadata')
    def validate_json_fields(self, key, value):
        """Validate JSON fields"""
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"{key} must be a dictionary")
        return value or {}
    
    def __repr__(self):
        return f"<AuditLog(audit_id='{self.audit_id}', event_type='{self.event_type}', timestamp='{self.timestamp}')>"


class FinancialTransactionAudit(Base):
    """
    Specialized audit table for financial transactions.
    
    Provides detailed tracking of all financial operations with
    structured data for compliance reporting.
    """
    __tablename__ = 'financial_transaction_audits'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to main audit log
    audit_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.audit_id'), 
                     nullable=False, unique=True, index=True)
    
    # Transaction identification
    transaction_id = Column(String(100), nullable=False, unique=True, index=True)
    stripe_payment_intent_id = Column(String(100), nullable=True, index=True)
    stripe_charge_id = Column(String(100), nullable=True, index=True)
    
    # Financial details
    amount = Column(Numeric(15, 2), nullable=False)  # Amount in dollars
    currency = Column(String(3), nullable=False, default='USD')
    payment_method = Column(String(50), nullable=False, index=True)
    payment_method_type = Column(String(50), nullable=True, index=True)
    
    # Transaction status
    status = Column(String(50), nullable=False, index=True)
    failure_reason = Column(Text, nullable=True)
    failure_code = Column(String(100), nullable=True)
    
    # Customer and subscription context
    customer_id = Column(String(100), nullable=True, index=True)
    subscription_id = Column(String(100), nullable=True, index=True)
    invoice_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    transaction_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                                 default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    
    # Additional data
    audit_metadata = Column(JSONB, nullable=True, default={})
    risk_score = Column(SmallInteger, nullable=True)  # 0-100 risk assessment
    fraud_detection_result = Column(String(50), nullable=True)
    
    # Compliance fields
    pci_compliant = Column(Boolean, default=True)
    gdpr_compliant = Column(Boolean, default=True)
    
    # Relationships
    audit_log = relationship("AuditLog", backref="financial_transaction")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('transaction_id', name='uq_financial_transaction_audits_transaction_id'),
        CheckConstraint("amount > 0", name='chk_financial_transaction_audits_amount_positive'),
        CheckConstraint("status IN ('pending', 'processing', 'succeeded', 'failed', 'canceled', 'refunded', 'partially_refunded', 'disputed')", 
                       name='chk_financial_transaction_audits_status'),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name='chk_financial_transaction_audits_risk_score'),
        
        # Indexes
        Index('idx_financial_transaction_audits_amount_timestamp', 'amount', 'transaction_timestamp'),
        Index('idx_financial_transaction_audits_status_timestamp', 'status', 'transaction_timestamp'),
        Index('idx_financial_transaction_audits_customer_timestamp', 'customer_id', 'transaction_timestamp'),
        Index('idx_financial_transaction_audits_stripe_payment_intent', 'stripe_payment_intent_id'),
        Index('idx_financial_transaction_audits_metadata_gin', 'audit_metadata', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<FinancialTransactionAudit(transaction_id='{self.transaction_id}', amount={self.amount}, status='{self.status}')>"


class UserActivityAudit(Base):
    """
    Specialized audit table for user activities.
    
    Tracks user interactions, profile changes, and preferences
    for comprehensive user behavior analysis.
    """
    __tablename__ = 'user_activity_audits'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to main audit log
    audit_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.audit_id'), 
                     nullable=False, unique=True, index=True)
    
    # User identification
    user_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)
    activity_subtype = Column(String(100), nullable=True, index=True)
    
    # Resource information
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    resource_action = Column(String(50), nullable=True, index=True)
    
    # User context
    user_role = Column(String(50), nullable=True, index=True)
    user_permissions = Column(JSONB, nullable=True, default=[])
    
    # Session information
    session_start = Column(TIMESTAMP(timezone=True), nullable=True)
    session_duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Device and location
    device_type = Column(String(50), nullable=True, index=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    
    # Timestamps
    activity_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                              default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    
    # Additional data
    audit_metadata = Column(JSONB, nullable=True, default={})
    performance_metrics = Column(JSONB, nullable=True, default={})
    
    # Relationships
    audit_log = relationship("AuditLog", backref="user_activity")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("session_duration >= 0", name='chk_user_activity_audits_session_duration'),
        
        # Indexes
        Index('idx_user_activity_audits_user_timestamp', 'user_id', 'activity_timestamp'),
        Index('idx_user_activity_audits_activity_type_timestamp', 'activity_type', 'activity_timestamp'),
        Index('idx_user_activity_audits_resource_timestamp', 'resource_type', 'resource_id', 'activity_timestamp'),
        Index('idx_user_activity_audits_session_timestamp', 'session_id', 'activity_timestamp'),
        Index('idx_user_activity_audits_metadata_gin', 'audit_metadata', postgresql_using='gin'),
        Index('idx_user_activity_audits_performance_gin', 'performance_metrics', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<UserActivityAudit(user_id='{self.user_id}', activity_type='{self.activity_type}', timestamp='{self.activity_timestamp}')>"


class SecurityEventAudit(Base):
    """
    Specialized audit table for security events.
    
    Tracks security incidents, threats, and compliance violations
    for comprehensive security monitoring and response.
    """
    __tablename__ = 'security_event_audits'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to main audit log
    audit_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.audit_id'), 
                     nullable=False, unique=True, index=True)
    
    # Security event classification
    event_type = Column(String(100), nullable=False, index=True)
    threat_level = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    risk_score = Column(SmallInteger, nullable=False, default=0)  # 0-100
    
    # Event details
    description = Column(Text, nullable=False)
    technical_details = Column(Text, nullable=True)
    
    # Source information
    source_ip = Column(String(45), nullable=True, index=True)
    source_country = Column(String(2), nullable=True, index=True)
    source_type = Column(String(50), nullable=True, index=True)  # external, internal, automated
    
    # Target information
    target_user = Column(String(100), nullable=True, index=True)
    target_resource = Column(String(200), nullable=True, index=True)
    target_system = Column(String(100), nullable=True, index=True)
    
    # Security context
    attack_vector = Column(String(100), nullable=True, index=True)
    vulnerability_type = Column(String(100), nullable=True, index=True)
    cve_references = Column(JSONB, nullable=True, default=[])
    
    # Response and mitigation
    response_action = Column(String(100), nullable=True, index=True)
    response_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    mitigation_status = Column(String(50), nullable=True, index=True)
    
    # Timestamps
    event_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                           default=func.now(), index=True)
    detected_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                              default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    
    # Additional data
    audit_metadata = Column(JSONB, nullable=True, default={})
    ioc_data = Column(JSONB, nullable=True, default={})  # Indicators of Compromise
    threat_intel = Column(JSONB, nullable=True, default={})
    
    # Relationships
    audit_log = relationship("AuditLog", backref="security_event")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("threat_level IN ('low', 'medium', 'high', 'critical')", 
                       name='chk_security_event_audits_threat_level'),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", 
                       name='chk_security_event_audits_risk_score'),
        CheckConstraint("mitigation_status IN ('pending', 'in_progress', 'resolved', 'false_positive')", 
                       name='chk_security_event_audits_mitigation_status'),
        
        # Indexes
        Index('idx_security_event_audits_threat_level_timestamp', 'threat_level', 'event_timestamp'),
        Index('idx_security_event_audits_risk_score_timestamp', 'risk_score', 'event_timestamp'),
        Index('idx_security_event_audits_source_ip_timestamp', 'source_ip', 'event_timestamp'),
        Index('idx_security_event_audits_target_user_timestamp', 'target_user', 'event_timestamp'),
        Index('idx_security_event_audits_attack_vector_timestamp', 'attack_vector', 'event_timestamp'),
        Index('idx_security_event_audits_metadata_gin', 'audit_metadata', postgresql_using='gin'),
        Index('idx_security_event_audits_ioc_data_gin', 'ioc_data', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<SecurityEventAudit(event_type='{self.event_type}', threat_level='{self.threat_level}', timestamp='{self.event_timestamp}')>"


class ComplianceReport(Base):
    """
    Compliance reporting data model.
    
    Stores generated compliance reports and audit summaries
    for regulatory reporting and internal compliance monitoring.
    """
    __tablename__ = 'compliance_reports'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Report identification
    report_id = Column(UUID(as_uuid=True), unique=True, nullable=False, 
                      default=uuid.uuid4, index=True)
    report_type = Column(String(100), nullable=False, index=True)
    report_name = Column(String(200), nullable=False)
    
    # Compliance framework
    framework = Column(String(100), nullable=False, index=True)  # PCI DSS, GDPR, SOX, etc.
    framework_version = Column(String(20), nullable=True)
    
    # Report scope
    start_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    scope_description = Column(Text, nullable=True)
    
    # Report content
    report_data = Column(JSONB, nullable=False, default={})
    summary = Column(JSONB, nullable=True, default={})
    findings = Column(JSONB, nullable=True, default=[])
    recommendations = Column(JSONB, nullable=True, default=[])
    
    # Compliance status
    overall_status = Column(String(50), nullable=False, index=True)  # compliant, non_compliant, partially_compliant
    risk_level = Column(String(20), nullable=True, index=True)
    compliance_score = Column(SmallInteger, nullable=True)  # 0-100
    
    # Generation details
    generated_by = Column(String(100), nullable=True, index=True)
    generation_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, 
                                default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    
    # Export and sharing
    export_format = Column(String(20), nullable=True)  # PDF, JSON, CSV, XML
    export_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    shared_with = Column(JSONB, nullable=True, default=[])
    
    # Additional metadata
    audit_metadata = Column(JSONB, nullable=True, default={})
    tags = Column(JSONB, nullable=True, default=[])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('report_id', name='uq_compliance_reports_report_id'),
        CheckConstraint("overall_status IN ('compliant', 'non_compliant', 'partially_compliant')", 
                       name='chk_compliance_reports_overall_status'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", 
                       name='chk_compliance_reports_risk_level'),
        CheckConstraint("compliance_score >= 0 AND compliance_score <= 100", 
                       name='chk_compliance_reports_compliance_score'),
        CheckConstraint("end_date > start_date", name='chk_compliance_reports_date_range'),
        
        # Indexes
        Index('idx_compliance_reports_type_timestamp', 'report_type', 'generation_timestamp'),
        Index('idx_compliance_reports_framework_timestamp', 'framework', 'generation_timestamp'),
        Index('idx_compliance_reports_status_timestamp', 'overall_status', 'generation_timestamp'),
        Index('idx_compliance_reports_date_range', 'start_date', 'end_date'),
        Index('idx_compliance_reports_data_gin', 'report_data', postgresql_using='gin'),
        Index('idx_compliance_reports_summary_gin', 'summary', postgresql_using='gin'),
        Index('idx_compliance_reports_findings_gin', 'findings', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<ComplianceReport(report_id='{self.report_id}', report_type='{self.report_type}', status='{self.overall_status}')>"


class AuditDataRetention(Base):
    """
    Data retention policy configuration and tracking.
    
    Manages retention policies for different types of audit data
    and tracks data lifecycle for compliance purposes.
    """
    __tablename__ = 'audit_data_retention'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Policy identification
    policy_id = Column(UUID(as_uuid=True), unique=True, nullable=False, 
                      default=uuid.uuid4, index=True)
    policy_name = Column(String(200), nullable=False, unique=True)
    
    # Policy scope
    data_type = Column(String(100), nullable=False, index=True)  # audit_logs, financial_transactions, etc.
    category = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=True, index=True)
    
    # Retention rules
    retention_period_days = Column(Integer, nullable=False, index=True)
    retention_period_months = Column(Integer, nullable=True)
    retention_period_years = Column(Integer, nullable=True)
    
    # Archival settings
    archive_after_days = Column(Integer, nullable=True)
    archive_location = Column(String(200), nullable=True)
    archive_format = Column(String(20), nullable=True)  # compressed, encrypted, etc.
    
    # Deletion settings
    delete_after_days = Column(Integer, nullable=True)
    soft_delete = Column(Boolean, default=True)
    deletion_method = Column(String(50), nullable=True)  # secure_delete, overwrite, etc.
    
    # Compliance requirements
    regulatory_requirement = Column(String(200), nullable=True)
    legal_hold = Column(Boolean, default=False)
    legal_hold_reason = Column(Text, nullable=True)
    
    # Policy status
    active = Column(Boolean, default=True, index=True)
    last_reviewed = Column(TIMESTAMP(timezone=True), nullable=True)
    next_review = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now(), onupdate=func.now())
    
    # Additional metadata
    audit_metadata = Column(JSONB, nullable=True, default={})
    description = Column(Text, nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('policy_id', name='uq_audit_data_retention_policy_id'),
        UniqueConstraint('policy_name', name='uq_audit_data_retention_policy_name'),
        CheckConstraint("retention_period_days > 0", name='chk_audit_data_retention_retention_period_days'),
        CheckConstraint("retention_period_months >= 0", name='chk_audit_data_retention_retention_period_months'),
        CheckConstraint("retention_period_years >= 0", name='chk_audit_data_retention_retention_period_years'),
        
        # Indexes
        Index('idx_audit_data_retention_data_type', 'data_type'),
        Index('idx_audit_data_retention_category', 'category'),
        Index('idx_audit_data_retention_active', 'active'),
        Index('idx_audit_data_retention_metadata_gin', 'audit_metadata', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<AuditDataRetention(policy_name='{self.policy_name}', data_type='{self.data_type}', retention_days={self.retention_period_days})>"


# Audit log views for common queries
class AuditLogView(Base):
    """
    Database view for common audit log queries.
    
    Provides optimized views for frequently accessed audit data
    with proper indexing and materialization support.
    """
    __tablename__ = 'audit_log_view'
    
    # This is a view, so we define it as a table but it will be created as a view
    __table_args__ = {'info': {'is_view': True}}
    
    # View columns (matching the actual view definition)
    audit_id = Column(UUID(as_uuid=True), primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    user_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    source = Column(String(200), nullable=True, index=True)
    
    # Computed fields
    hour_bucket = Column(String(13), nullable=True, index=True)  # YYYY-MM-DD-HH
    day_bucket = Column(String(10), nullable=True, index=True)  # YYYY-MM-DD
    month_bucket = Column(String(7), nullable=True, index=True)  # YYYY-MM
    
    def __repr__(self):
        return f"<AuditLogView(audit_id='{self.audit_id}', event_type='{self.event_type}', timestamp='{self.timestamp}')>"


# Audit statistics table for performance optimization
class AuditStatistics(Base):
    """
    Pre-computed audit statistics for performance optimization.
    
    Stores aggregated audit data to avoid expensive real-time
    calculations for common queries and reports.
    """
    __tablename__ = 'audit_statistics'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time bucket
    time_bucket = Column(String(13), nullable=False, index=True)  # YYYY-MM-DD-HH
    bucket_type = Column(String(20), nullable=False, index=True)  # hour, day, month
    
    # Statistical data
    total_events = Column(Integer, nullable=False, default=0)
    events_by_category = Column(JSONB, nullable=True, default={})
    events_by_severity = Column(JSONB, nullable=True, default={})
    events_by_type = Column(JSONB, nullable=True, default={})
    
    # User activity statistics
    unique_users = Column(Integer, nullable=False, default=0)
    unique_sessions = Column(Integer, nullable=False, default=0)
    unique_ips = Column(Integer, nullable=False, default=0)
    
    # Security statistics
    security_events = Column(Integer, nullable=False, default=0)
    high_risk_events = Column(Integer, nullable=False, default=0)
    failed_logins = Column(Integer, nullable=False, default=0)
    
    # Financial statistics
    financial_transactions = Column(Integer, nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    failed_transactions = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    avg_response_time = Column(Numeric(10, 3), nullable=True)
    max_response_time = Column(Numeric(10, 3), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                       default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('time_bucket', 'bucket_type', name='uq_audit_statistics_time_bucket'),
        CheckConstraint("total_events >= 0", name='chk_audit_statistics_total_events'),
        CheckConstraint("unique_users >= 0", name='chk_audit_statistics_unique_users'),
        CheckConstraint("total_amount >= 0", name='chk_audit_statistics_total_amount'),
        
        # Indexes
        Index('idx_audit_statistics_time_bucket_type', 'time_bucket', 'bucket_type'),
        Index('idx_audit_statistics_bucket_type_timestamp', 'bucket_type', 'created_at'),
        Index('idx_audit_statistics_events_by_category_gin', 'events_by_category', postgresql_using='gin'),
        Index('idx_audit_statistics_events_by_severity_gin', 'events_by_severity', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<AuditStatistics(time_bucket='{self.time_bucket}', bucket_type='{self.bucket_type}', total_events={self.total_events})>"
