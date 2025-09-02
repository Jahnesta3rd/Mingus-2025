"""
AI User Profile Extension Model
Extends existing user profile with AI job risk assessment data
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class AIUserProfileExtension(Base):
    """AI Job Risk Profile Extension for existing users"""
    __tablename__ = 'ai_user_profile_extensions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # AI Job Risk Assessment Data
    latest_ai_assessment_id = Column(UUID(as_uuid=True), ForeignKey('ai_job_assessments.id'), nullable=True)
    overall_risk_level = Column(String(20), nullable=True)  # low, medium, high
    automation_score = Column(Integer, nullable=True)
    augmentation_score = Column(Integer, nullable=True)
    
    # Career Risk Management Preferences
    career_risk_alerts_enabled = Column(Boolean, default=True)
    ai_skill_development_goals = Column(JSONB, default=list)
    career_transition_plans = Column(JSONB, default=list)
    risk_mitigation_strategies = Column(JSONB, default=list)
    
    # AI Career Insights Integration
    ai_career_insights_enabled = Column(Boolean, default=True)
    industry_risk_monitoring = Column(Boolean, default=True)
    skill_gap_analysis_enabled = Column(Boolean, default=True)
    career_advancement_tracking = Column(Boolean, default=True)
    
    # Onboarding Integration
    ai_assessment_completed = Column(Boolean, default=False)
    ai_assessment_completion_date = Column(DateTime(timezone=True), nullable=True)
    ai_onboarding_step = Column(String(50), default='not_started')  # not_started, optional, completed, skipped
    
    # Communication Preferences for AI Career Content
    ai_career_email_frequency = Column(String(20), default='weekly')  # daily, weekly, monthly, never
    ai_career_sms_enabled = Column(Boolean, default=False)
    ai_career_push_notifications = Column(Boolean, default=True)
    
    # Analytics and Tracking
    ai_assessment_count = Column(Integer, default=0)
    last_ai_assessment_date = Column(DateTime(timezone=True), nullable=True)
    ai_career_insights_engagement_score = Column(DECIMAL(3, 2), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="ai_profile_extension", uselist=False)
    latest_assessment = relationship("AIJobAssessment", foreign_keys=[latest_ai_assessment_id])
    
    def __repr__(self):
        return f'<AIUserProfileExtension {self.user_id}: {self.overall_risk_level}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile extension to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'latest_ai_assessment_id': str(self.latest_ai_assessment_id) if self.latest_ai_assessment_id else None,
            'overall_risk_level': self.overall_risk_level,
            'automation_score': self.automation_score,
            'augmentation_score': self.augmentation_score,
            'career_risk_alerts_enabled': self.career_risk_alerts_enabled,
            'ai_skill_development_goals': self.ai_skill_development_goals,
            'career_transition_plans': self.career_transition_plans,
            'risk_mitigation_strategies': self.risk_mitigation_strategies,
            'ai_career_insights_enabled': self.ai_career_insights_enabled,
            'industry_risk_monitoring': self.industry_risk_monitoring,
            'skill_gap_analysis_enabled': self.skill_gap_analysis_enabled,
            'career_advancement_tracking': self.career_advancement_tracking,
            'ai_assessment_completed': self.ai_assessment_completed,
            'ai_assessment_completion_date': self.ai_assessment_completion_date.isoformat() if self.ai_assessment_completion_date else None,
            'ai_onboarding_step': self.ai_onboarding_step,
            'ai_career_email_frequency': self.ai_career_email_frequency,
            'ai_career_sms_enabled': self.ai_career_sms_enabled,
            'ai_career_push_notifications': self.ai_career_push_notifications,
            'ai_assessment_count': self.ai_assessment_count,
            'last_ai_assessment_date': self.last_ai_assessment_date.isoformat() if self.last_ai_assessment_date else None,
            'ai_career_insights_engagement_score': float(self.ai_career_insights_engagement_score) if self.ai_career_insights_engagement_score else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AIOnboardingProgress(Base):
    """AI Assessment Onboarding Progress Tracking"""
    __tablename__ = 'ai_onboarding_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Onboarding steps
    ai_assessment_introduced = Column(Boolean, default=False)
    ai_assessment_started = Column(Boolean, default=False)
    ai_assessment_completed = Column(Boolean, default=False)
    ai_insights_explained = Column(Boolean, default=False)
    ai_career_plan_created = Column(Boolean, default=False)
    
    # Step completion timestamps
    introduction_date = Column(DateTime(timezone=True), nullable=True)
    started_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    insights_explained_date = Column(DateTime(timezone=True), nullable=True)
    career_plan_date = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences
    user_opted_in = Column(Boolean, nullable=True)  # True = opted in, False = opted out, None = not asked
    skip_reason = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="ai_onboarding_progress")
    
    def __repr__(self):
        return f'<AIOnboardingProgress {self.user_id}: {self.ai_assessment_completed}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert onboarding progress to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'ai_assessment_introduced': self.ai_assessment_introduced,
            'ai_assessment_started': self.ai_assessment_started,
            'ai_assessment_completed': self.ai_assessment_completed,
            'ai_insights_explained': self.ai_insights_explained,
            'ai_career_plan_created': self.ai_career_plan_created,
            'introduction_date': self.introduction_date.isoformat() if self.introduction_date else None,
            'started_date': self.started_date.isoformat() if self.started_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'insights_explained_date': self.insights_explained_date.isoformat() if self.insights_explained_date else None,
            'career_plan_date': self.career_plan_date.isoformat() if self.career_plan_date else None,
            'user_opted_in': self.user_opted_in,
            'skip_reason': self.skip_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
