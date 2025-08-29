"""
Assessment System Models

This module defines the SQLAlchemy ORM models for the assessment system,
corresponding to the database schema defined in the migration files.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid
from enum import Enum

# Import base model
from .base import Base

# =====================================================
# ENUM DEFINITIONS
# =====================================================

class AssessmentType(str, Enum):
    """Assessment types enum"""
    AI_JOB_RISK = 'ai_job_risk'
    RELATIONSHIP_IMPACT = 'relationship_impact'
    TAX_IMPACT = 'tax_impact'
    INCOME_COMPARISON = 'income_comparison'

class RiskLevelType(str, Enum):
    """Risk level types enum"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

# =====================================================
# ASSESSMENT MODELS
# =====================================================

class Assessment(Base):
    """Assessment templates and configurations"""
    __tablename__ = 'assessments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False, index=True)  # assessment_type enum
    title = Column(String(255), nullable=False)
    description = Column(Text)
    questions_json = Column(JSONB, nullable=False, default=[])
    scoring_config = Column(JSONB, nullable=False, default={})
    version = Column(String(20), default='1.0')
    estimated_duration_minutes = Column(Integer, default=10)
    is_active = Column(Boolean, default=True, index=True)
    requires_authentication = Column(Boolean, default=False)
    allow_anonymous = Column(Boolean, default=True)
    max_attempts_per_user = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_assessments = relationship("UserAssessment", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Assessment {self.type}: {self.title}>'
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            'id': str(self.id),
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'questions_json': self.questions_json,
            'scoring_config': self.scoring_config,
            'version': self.version,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'is_active': self.is_active,
            'requires_authentication': self.requires_authentication,
            'allow_anonymous': self.allow_anonymous,
            'max_attempts_per_user': self.max_attempts_per_user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserAssessment(Base):
    """User assessment responses and metadata"""
    __tablename__ = 'user_assessments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False, index=True)
    responses_json = Column(JSONB, nullable=False, default={})
    score = Column(Integer)  # 0-100
    risk_level = Column(String(20))  # risk_level_type enum
    
    # Anonymous user fields
    email = Column(String(255), index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    location = Column(String(255))
    job_title = Column(String(255))
    industry = Column(String(255))
    
    # Metadata
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    time_spent_seconds = Column(Integer, default=0)
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(UUID(as_uuid=True))
    assessment_version = Column(String(20))
    
    # Status tracking
    is_complete = Column(Boolean, default=False, index=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Conversion tracking
    conversion_data = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="assessments")
    assessment = relationship("Assessment", back_populates="user_assessments")
    assessment_result = relationship("AssessmentResult", back_populates="user_assessment", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<UserAssessment {self.id}: {self.assessment_id} - Score: {self.score}>'
    
    def to_dict(self):
        """Convert user assessment to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'assessment_id': str(self.assessment_id),
            'score': self.score,
            'risk_level': self.risk_level,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'location': self.location,
            'job_title': self.job_title,
            'industry': self.industry,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_spent_seconds': self.time_spent_seconds,
            'is_complete': self.is_complete,
            'is_valid': self.is_valid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AssessmentResult(Base):
    """Detailed assessment analysis and recommendations"""
    __tablename__ = 'assessment_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_assessment_id = Column(UUID(as_uuid=True), ForeignKey('user_assessments.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Analysis results
    insights_json = Column(JSONB, nullable=False, default={})
    recommendations_json = Column(JSONB, nullable=False, default={})
    
    # AI-specific scores (for AI job risk assessment)
    automation_score = Column(Integer)  # 0-100
    augmentation_score = Column(Integer)  # 0-100
    
    # Financial impact calculations
    cost_projections = Column(JSONB, default={})
    risk_factors = Column(JSONB, default=[])
    mitigation_strategies = Column(JSONB, default=[])
    
    # Relationship impact analysis (for relationship impact assessment)
    relationship_stress_score = Column(Integer)  # 0-100
    financial_harmony_score = Column(Integer)  # 0-100
    
    # Tax impact analysis (for tax impact assessment)
    tax_efficiency_score = Column(Integer)  # 0-100
    potential_savings = Column(DECIMAL(12, 2))
    tax_optimization_opportunities = Column(JSONB, default=[])
    
    # Income comparison analysis (for income comparison assessment)
    market_position_score = Column(Integer)  # 0-100
    salary_benchmark_data = Column(JSONB, default={})
    negotiation_leverage_points = Column(JSONB, default=[])
    
    # Metadata
    analysis_version = Column(String(20), default='1.0')
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_assessment = relationship("UserAssessment", back_populates="assessment_result")
    
    def __repr__(self):
        return f'<AssessmentResult {self.id}: {self.user_assessment_id}>'
    
    def to_dict(self):
        """Convert assessment result to dictionary"""
        return {
            'id': str(self.id),
            'user_assessment_id': str(self.user_assessment_id),
            'insights_json': self.insights_json,
            'recommendations_json': self.recommendations_json,
            'automation_score': self.automation_score,
            'augmentation_score': self.augmentation_score,
            'cost_projections': self.cost_projections,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'relationship_stress_score': self.relationship_stress_score,
            'financial_harmony_score': self.financial_harmony_score,
            'tax_efficiency_score': self.tax_efficiency_score,
            'potential_savings': float(self.potential_savings) if self.potential_savings else None,
            'tax_optimization_opportunities': self.tax_optimization_opportunities,
            'market_position_score': self.market_position_score,
            'salary_benchmark_data': self.salary_benchmark_data,
            'negotiation_leverage_points': self.negotiation_leverage_points,
            'analysis_version': self.analysis_version,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# LEAD MANAGEMENT MODELS
# =====================================================

class Lead(Base):
    """Lead records for anonymous assessment users"""
    __tablename__ = 'leads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    
    # Assessment data
    assessment_type = Column(String(50))
    assessment_score = Column(Integer)
    segment = Column(String(50))
    risk_level = Column(String(20))
    
    # Lead scoring
    lead_score = Column(Integer, default=0)
    lead_status = Column(String(50), default='new')  # new, contacted, qualified, converted, lost
    
    # Contact information
    phone = Column(String(50))
    company = Column(String(255))
    job_title = Column(String(255))
    industry = Column(String(255))
    
    # Marketing data
    source = Column(String(100), default='assessment')
    campaign = Column(String(100))
    utm_parameters = Column(JSONB, default={})
    
    # Conversion tracking
    converted_at = Column(DateTime(timezone=True))
    converted_to_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="leads")
    
    def __repr__(self):
        return f'<Lead {self.email}: {self.lead_score}>'
    
    def to_dict(self):
        """Convert lead to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'assessment_type': self.assessment_type,
            'assessment_score': self.assessment_score,
            'segment': self.segment,
            'risk_level': self.risk_level,
            'lead_score': self.lead_score,
            'lead_status': self.lead_status,
            'phone': self.phone,
            'company': self.company,
            'job_title': self.job_title,
            'industry': self.industry,
            'source': self.source,
            'campaign': self.campaign,
            'utm_parameters': self.utm_parameters,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'converted_to_user_id': str(self.converted_to_user_id) if self.converted_to_user_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# EMAIL SEQUENCE MODELS
# =====================================================

class EmailSequence(Base):
    """Email sequence templates for assessment follow-up"""
    __tablename__ = 'email_sequences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Trigger conditions
    assessment_type = Column(String(50))
    segment = Column(String(50))
    risk_level = Column(String(20))
    score_range_min = Column(Integer)
    score_range_max = Column(Integer)
    
    # Sequence configuration
    emails_json = Column(JSONB, nullable=False, default=[])
    delay_hours = Column(JSONB, default=[])  # Hours between emails
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<EmailSequence {self.name}: {self.assessment_type}>'
    
    def to_dict(self):
        """Convert email sequence to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'assessment_type': self.assessment_type,
            'segment': self.segment,
            'risk_level': self.risk_level,
            'score_range_min': self.score_range_min,
            'score_range_max': self.score_range_max,
            'emails_json': self.emails_json,
            'delay_hours': self.delay_hours,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EmailLog(Base):
    """Email delivery logs for assessment sequences"""
    __tablename__ = 'email_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    email_sequence_id = Column(UUID(as_uuid=True), ForeignKey('email_sequences.id', ondelete='SET NULL'))
    
    # Email details
    email_type = Column(String(50), nullable=False)  # confirmation, assessment_results, follow_up
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default='sent')  # sent, delivered, failed
    external_id = Column(String(255))  # Email service tracking ID
    
    # Engagement tracking
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # Relationships
    lead = relationship("Lead", back_populates="email_logs")
    email_sequence = relationship("EmailSequence")
    
    def __repr__(self):
        return f'<EmailLog {self.id}: {self.email_type} - {self.status}>'
    
    def to_dict(self):
        """Convert email log to dictionary"""
        return {
            'id': str(self.id),
            'lead_id': str(self.lead_id),
            'email_sequence_id': str(self.email_sequence_id) if self.email_sequence_id else None,
            'email_type': self.email_type,
            'subject': self.subject,
            'body': self.body,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'external_id': self.external_id,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'error_message': self.error_message
        }

# =====================================================
# RELATIONSHIP UPDATES
# =====================================================

# Update User model to include assessment relationships
# This would be added to the existing User model in user.py
"""
# Add to User model in user.py:
assessments = relationship("UserAssessment", back_populates="user")
leads = relationship("Lead", back_populates="user")
"""
