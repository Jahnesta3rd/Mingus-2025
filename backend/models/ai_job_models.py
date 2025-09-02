"""
AI Job Impact Calculator SQLAlchemy Models
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, DECIMAL, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .base import Base

class AIJobAssessment(Base):
    """AI Job Impact Assessment Model"""
    __tablename__ = 'ai_job_assessments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Nullable for anonymous assessments
    
    # Assessment data
    job_title = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False)
    experience_level = Column(String(20), nullable=False)
    tasks_array = Column(JSONB, nullable=False, default=list)
    remote_work_frequency = Column(String(20), nullable=False)
    ai_usage_frequency = Column(String(20), nullable=False)
    team_size = Column(String(20), nullable=False)
    tech_skills_level = Column(String(20), nullable=False)
    concerns_array = Column(JSONB, nullable=False, default=list)
    
    # Contact information
    first_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    location = Column(String(100), nullable=True)
    
    # Assessment results
    automation_score = Column(Integer, nullable=False)
    augmentation_score = Column(Integer, nullable=False)
    overall_risk_level = Column(String(20), nullable=False)
    assessment_type = Column(String(50), default='ai_job_risk')
    
    # Lead generation fields
    lead_source = Column(String(100), default='ai_job_calculator')
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    
    # Email and communication preferences
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    communication_preferences = Column(JSONB, default=dict)
    
    # Assessment metadata
    assessment_duration_seconds = Column(Integer, nullable=True)
    questions_answered = Column(Integer, default=0)
    total_questions = Column(Integer, default=15)
    completion_percentage = Column(DECIMAL(5, 2), default=0.0)
    
    # Risk analysis details
    risk_factors = Column(JSONB, default=dict)
    mitigation_strategies = Column(JSONB, default=list)
    recommended_skills = Column(JSONB, default=list)
    career_advice = Column(JSONB, default=dict)
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="ai_job_assessments", foreign_keys=[user_id])
    conversions = relationship("AICalculatorConversion", back_populates="assessment", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('automation_score >= 0 AND automation_score <= 100', name='valid_automation_score'),
        CheckConstraint('augmentation_score >= 0 AND augmentation_score <= 100', name='valid_augmentation_score'),
        CheckConstraint('experience_level IN (\'entry\', \'mid\', \'senior\', \'executive\')', name='valid_experience_level'),
        CheckConstraint('remote_work_frequency IN (\'never\', \'rarely\', \'sometimes\', \'often\', \'always\')', name='valid_remote_work_frequency'),
        CheckConstraint('ai_usage_frequency IN (\'never\', \'rarely\', \'sometimes\', \'often\', \'always\')', name='valid_ai_usage_frequency'),
        CheckConstraint('team_size IN (\'1-5\', \'6-10\', \'11-25\', \'26-50\', \'50+\')', name='valid_team_size'),
        CheckConstraint('tech_skills_level IN (\'basic\', \'intermediate\', \'advanced\', \'expert\')', name='valid_tech_skills_level'),
        CheckConstraint('overall_risk_level IN (\'low\', \'medium\', \'high\')', name='valid_risk_level'),
    )
    
    def __repr__(self):
        return f'<AIJobAssessment {self.email}: {self.job_title}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary"""
        return {
            'id': str(self.id),
            'job_title': self.job_title,
            'industry': self.industry,
            'experience_level': self.experience_level,
            'tasks_array': self.tasks_array,
            'remote_work_frequency': self.remote_work_frequency,
            'ai_usage_frequency': self.ai_usage_frequency,
            'team_size': self.team_size,
            'tech_skills_level': self.tech_skills_level,
            'concerns_array': self.concerns_array,
            'first_name': self.first_name,
            'email': self.email,
            'location': self.location,
            'automation_score': self.automation_score,
            'augmentation_score': self.augmentation_score,
            'overall_risk_level': self.overall_risk_level,
            'assessment_type': self.assessment_type,
            'lead_source': self.lead_source,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'utm_term': self.utm_term,
            'utm_content': self.utm_content,
            'email_verified': self.email_verified,
            'communication_preferences': self.communication_preferences,
            'questions_answered': self.questions_answered,
            'total_questions': self.total_questions,
            'completion_percentage': float(self.completion_percentage) if self.completion_percentage else 0.0,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'recommended_skills': self.recommended_skills,
            'career_advice': self.career_advice,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AIJobRiskData(Base):
    """AI Job Risk Reference Data Model"""
    __tablename__ = 'ai_job_risk_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_keyword = Column(String(100), nullable=False, unique=True, index=True)
    automation_base_score = Column(Integer, nullable=False)
    augmentation_base_score = Column(Integer, nullable=False)
    risk_category = Column(String(20), nullable=False)
    industry_modifiers = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint('automation_base_score >= 0 AND automation_base_score <= 100', name='valid_automation_base_score'),
        CheckConstraint('augmentation_base_score >= 0 AND augmentation_base_score <= 100', name='valid_augmentation_base_score'),
        CheckConstraint('risk_category IN (\'low\', \'medium\', \'high\')', name='valid_risk_category'),
    )
    
    def __repr__(self):
        return f'<AIJobRiskData {self.job_keyword}: {self.risk_category}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert risk data to dictionary"""
        return {
            'id': str(self.id),
            'job_keyword': self.job_keyword,
            'automation_base_score': self.automation_base_score,
            'augmentation_base_score': self.augmentation_base_score,
            'risk_category': self.risk_category,
            'industry_modifiers': self.industry_modifiers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AICalculatorConversion(Base):
    """AI Calculator Conversion Tracking Model"""
    __tablename__ = 'ai_calculator_conversions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversion_type = Column(String(50), nullable=False)
    conversion_value = Column(DECIMAL(10, 2), default=0.0)
    converted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Conversion details
    conversion_source = Column(String(100), nullable=True)
    conversion_medium = Column(String(100), nullable=True)
    conversion_campaign = Column(String(100), nullable=True)
    conversion_revenue = Column(DECIMAL(10, 2), default=0.0)
    
    # User journey tracking
    touchpoints_before_conversion = Column(Integer, default=0)
    days_to_conversion = Column(Integer, default=0)
    conversion_funnel_stage = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    assessment = relationship("AIJobAssessment", back_populates="conversions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('conversion_type IN (\'email_signup\', \'paid_upgrade\', \'consultation_booking\', \'course_enrollment\')', name='valid_conversion_type'),
    )
    
    def __repr__(self):
        return f'<AICalculatorConversion {self.conversion_type}: ${self.conversion_value}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversion to dictionary"""
        return {
            'id': str(self.id),
            'assessment_id': str(self.assessment_id),
            'conversion_type': self.conversion_type,
            'conversion_value': float(self.conversion_value) if self.conversion_value else 0.0,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'conversion_source': self.conversion_source,
            'conversion_medium': self.conversion_medium,
            'conversion_campaign': self.conversion_campaign,
            'conversion_revenue': float(self.conversion_revenue) if self.conversion_revenue else 0.0,
            'touchpoints_before_conversion': self.touchpoints_before_conversion,
            'days_to_conversion': self.days_to_conversion,
            'conversion_funnel_stage': self.conversion_funnel_stage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
