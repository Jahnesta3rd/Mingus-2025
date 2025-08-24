"""
MINGUS Application - Career Models
==================================

SQLAlchemy models for career tracking and analysis.

Models:
- JobSecurityAnalysis: Career risk assessment and job security analysis
- CareerMilestone: Career goal setting and milestone tracking

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class JobSecurityAnalysis(Base):
    """Career risk assessment and job security analysis."""
    
    __tablename__ = 'job_security_analysis'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Analysis information
    analysis_date = Column(Date, nullable=False)
    
    # Risk scores (0.0 to 1.0, where 1.0 is highest risk)
    industry_risk_score = Column(Numeric(3, 2))
    company_risk_score = Column(Numeric(3, 2))
    personal_risk_score = Column(Numeric(3, 2))
    overall_risk_score = Column(Numeric(3, 2))
    
    # Analysis details
    risk_factors = Column(JSONB)
    mitigation_strategies = Column(JSONB)
    market_conditions = Column(JSONB)
    salary_comparison = Column(JSONB)
    career_opportunities = Column(JSONB)
    recommendations = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('industry_risk_score', 'company_risk_score', 'personal_risk_score', 'overall_risk_score')
    def validate_risk_scores(self, key, score):
        """Validate risk scores."""
        if score is not None and (score < 0 or score > 1):
            raise ValueError(f"{key} must be between 0 and 1")
        return score
    
    # Properties
    @property
    def security_level(self):
        """Get security level based on overall risk score."""
        if not self.overall_risk_score:
            return None
        
        if self.overall_risk_score <= 0.2:
            return 'very_secure'
        elif self.overall_risk_score <= 0.4:
            return 'secure'
        elif self.overall_risk_score <= 0.6:
            return 'moderate'
        elif self.overall_risk_score <= 0.8:
            return 'at_risk'
        else:
            return 'high_risk'
    
    @property
    def risk_level(self):
        """Get risk level description."""
        if not self.overall_risk_score:
            return None
        
        if self.overall_risk_score <= 0.2:
            return 'Low Risk'
        elif self.overall_risk_score <= 0.4:
            return 'Moderate Risk'
        elif self.overall_risk_score <= 0.6:
            return 'Elevated Risk'
        elif self.overall_risk_score <= 0.8:
            return 'High Risk'
        else:
            return 'Critical Risk'
    
    @property
    def risk_percentage(self):
        """Convert risk score to percentage."""
        if not self.overall_risk_score:
            return None
        return round(self.overall_risk_score * 100, 1)
    
    @property
    def security_percentage(self):
        """Convert to security percentage (inverse of risk)."""
        if not self.overall_risk_score:
            return None
        return round((1 - self.overall_risk_score) * 100, 1)
    
    # Methods
    def to_dict(self):
        """Convert job security analysis to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'industry_risk_score': float(self.industry_risk_score) if self.industry_risk_score else None,
            'company_risk_score': float(self.company_risk_score) if self.company_risk_score else None,
            'personal_risk_score': float(self.personal_risk_score) if self.personal_risk_score else None,
            'overall_risk_score': float(self.overall_risk_score) if self.overall_risk_score else None,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'market_conditions': self.market_conditions,
            'salary_comparison': self.salary_comparison,
            'career_opportunities': self.career_opportunities,
            'recommendations': self.recommendations,
            'security_level': self.security_level,
            'risk_level': self.risk_level,
            'risk_percentage': self.risk_percentage,
            'security_percentage': self.security_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<JobSecurityAnalysis(id={self.id}, user_id={self.user_id}, risk_score={self.overall_risk_score}, security_level='{self.security_level}')>"


class CareerMilestone(Base):
    """Career goal setting and milestone tracking."""
    
    __tablename__ = 'career_milestones'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Milestone information
    milestone_name = Column(String(255), nullable=False)
    milestone_type = Column(String(50), nullable=False)  # promotion, raise, certification, education
    
    # Financial targets
    target_salary = Column(Numeric(12, 2))
    current_salary = Column(Numeric(12, 2))
    
    # Timeline
    target_date = Column(Date)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(Date)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('milestone_type')
    def validate_milestone_type(self, key, milestone_type):
        """Validate milestone type."""
        valid_types = ['promotion', 'raise', 'certification', 'education', 'skill_development', 'job_change']
        if milestone_type not in valid_types:
            raise ValueError(f"Milestone type must be one of: {valid_types}")
        return milestone_type
    
    @validates('progress_percentage')
    def validate_progress_percentage(self, key, percentage):
        """Validate progress percentage."""
        if percentage < 0 or percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        return percentage
    
    @validates('target_salary', 'current_salary')
    def validate_salary(self, key, salary):
        """Validate salary amounts."""
        if salary is not None and salary < 0:
            raise ValueError("Salary cannot be negative")
        return salary
    
    # Properties
    @property
    def is_overdue(self):
        """Check if milestone is overdue."""
        if not self.target_date or self.is_completed:
            return False
        return date.today() > self.target_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining to target date."""
        if not self.target_date or self.is_completed:
            return None
        delta = self.target_date - date.today()
        return max(0, delta.days)
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.target_date).days
    
    @property
    def salary_gap(self):
        """Calculate salary gap to target."""
        if not self.target_salary or not self.current_salary:
            return None
        return self.target_salary - self.current_salary
    
    @property
    def salary_gap_percentage(self):
        """Calculate salary gap as percentage."""
        if not self.salary_gap or not self.current_salary:
            return None
        return (self.salary_gap / self.current_salary) * 100
    
    @property
    def status(self):
        """Get milestone status."""
        if self.is_completed:
            return 'completed'
        elif self.is_overdue:
            return 'overdue'
        elif self.progress_percentage >= 100:
            return 'achieved'
        elif self.progress_percentage >= 75:
            return 'on_track'
        elif self.progress_percentage >= 50:
            return 'in_progress'
        else:
            return 'just_started'
    
    @property
    def priority_level(self):
        """Get priority level based on overdue status and progress."""
        if self.is_overdue:
            return 'critical'
        elif self.days_remaining is not None and self.days_remaining <= 30:
            return 'high'
        elif self.progress_percentage >= 75:
            return 'medium'
        else:
            return 'normal'
    
    # Methods
    def update_progress(self, progress_percentage):
        """Update milestone progress."""
        if progress_percentage < 0 or progress_percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        
        self.progress_percentage = progress_percentage
        
        # Check if milestone is completed
        if progress_percentage >= 100 and not self.is_completed:
            self.complete_milestone()
    
    def complete_milestone(self):
        """Mark milestone as completed."""
        self.is_completed = True
        self.completion_date = date.today()
        self.progress_percentage = 100
    
    def update_salary(self, new_salary):
        """Update current salary."""
        self.current_salary = new_salary
        
        # Recalculate progress if target salary exists
        if self.target_salary and self.current_salary:
            if self.current_salary >= self.target_salary:
                self.update_progress(100)
            else:
                progress = (self.current_salary / self.target_salary) * 100
                self.update_progress(min(99, progress))
    
    def to_dict(self):
        """Convert career milestone to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'milestone_name': self.milestone_name,
            'milestone_type': self.milestone_type,
            'target_salary': float(self.target_salary) if self.target_salary else None,
            'current_salary': float(self.current_salary) if self.current_salary else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'progress_percentage': self.progress_percentage,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_remaining': self.days_remaining,
            'days_overdue': self.days_overdue,
            'salary_gap': float(self.salary_gap) if self.salary_gap else None,
            'salary_gap_percentage': float(self.salary_gap_percentage) if self.salary_gap_percentage else None,
            'status': self.status,
            'priority_level': self.priority_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<CareerMilestone(id={self.id}, user_id={self.user_id}, name='{self.milestone_name}', progress={self.progress_percentage}%)>" 