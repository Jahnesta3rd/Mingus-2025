"""
MINGUS Application - Health Models
==================================

SQLAlchemy models for health tracking and wellness correlations.

Models:
- UserHealthCheckin: Daily health and wellness tracking
- HealthSpendingCorrelation: Statistical health-spending analysis
- HealthGoal: Health goal setting and progress tracking

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class UserHealthCheckin(Base):
    """Daily health and wellness tracking."""
    
    __tablename__ = 'user_health_checkins'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Check-in date
    checkin_date = Column(Date, nullable=False, index=True)
    
    # Health metrics
    mood_score = Column(Integer)  # 1-10 scale
    stress_level = Column(Integer)  # 1-10 scale
    sleep_hours = Column(Numeric(3, 1))  # hours of sleep
    exercise_minutes = Column(Integer)  # minutes of exercise
    water_intake_oz = Column(Integer)  # ounces of water consumed
    medication_taken = Column(Boolean, default=False)
    
    # Additional data
    symptoms = Column(JSONB)  # flexible symptoms tracking
    wellness_activities = Column(JSONB)  # wellness activities performed
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="health_checkins")
    
    # Validation
    @validates('mood_score', 'stress_level')
    def validate_scale_scores(self, key, score):
        """Validate 1-10 scale scores."""
        if score is not None and (score < 1 or score > 10):
            raise ValueError(f"{key} must be between 1 and 10")
        return score
    
    @validates('sleep_hours')
    def validate_sleep_hours(self, key, hours):
        """Validate sleep hours."""
        if hours is not None and (hours < 0 or hours > 24):
            raise ValueError("Sleep hours must be between 0 and 24")
        return hours
    
    @validates('exercise_minutes', 'water_intake_oz')
    def validate_non_negative(self, key, value):
        """Validate non-negative values."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    # Properties
    @property
    def wellness_score(self):
        """Calculate overall wellness score."""
        score = 0
        count = 0
        
        if self.mood_score:
            score += self.mood_score
            count += 1
        
        if self.stress_level:
            # Invert stress level (lower is better)
            score += (11 - self.stress_level)
            count += 1
        
        if self.sleep_hours:
            # Optimal sleep is 7-9 hours
            if 7 <= self.sleep_hours <= 9:
                score += 10
            elif 6 <= self.sleep_hours <= 10:
                score += 7
            else:
                score += 3
            count += 1
        
        if self.exercise_minutes:
            # 30+ minutes is optimal
            if self.exercise_minutes >= 30:
                score += 10
            elif self.exercise_minutes >= 15:
                score += 7
            else:
                score += 3
            count += 1
        
        if self.water_intake_oz:
            # 64+ oz is optimal
            if self.water_intake_oz >= 64:
                score += 10
            elif self.water_intake_oz >= 32:
                score += 7
            else:
                score += 3
            count += 1
        
        return round(score / count, 1) if count > 0 else None
    
    @property
    def wellness_level(self):
        """Get wellness level based on score."""
        if not self.wellness_score:
            return None
        
        if self.wellness_score >= 8:
            return 'excellent'
        elif self.wellness_score >= 6:
            return 'good'
        elif self.wellness_score >= 4:
            return 'fair'
        else:
            return 'poor'
    
    # Methods
    def to_dict(self):
        """Convert health check-in to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'mood_score': self.mood_score,
            'stress_level': self.stress_level,
            'sleep_hours': float(self.sleep_hours) if self.sleep_hours else None,
            'exercise_minutes': self.exercise_minutes,
            'water_intake_oz': self.water_intake_oz,
            'medication_taken': self.medication_taken,
            'symptoms': self.symptoms,
            'wellness_activities': self.wellness_activities,
            'notes': self.notes,
            'wellness_score': self.wellness_score,
            'wellness_level': self.wellness_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<UserHealthCheckin(id={self.id}, user_id={self.user_id}, date={self.checkin_date}, wellness_score={self.wellness_score})>"


class HealthSpendingCorrelation(Base):
    """Statistical analysis of health-spending relationships."""
    
    __tablename__ = 'health_spending_correlations'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Analysis information
    correlation_date = Column(Date, nullable=False)
    health_metric = Column(String(100), nullable=False)  # mood, stress, sleep, exercise
    health_score = Column(Numeric(5, 2))
    spending_amount = Column(Numeric(12, 2))
    spending_category = Column(String(100))
    
    # Statistical measures
    correlation_strength = Column(Numeric(3, 2))  # -1.0 to 1.0
    confidence_interval_lower = Column(Numeric(3, 2))
    confidence_interval_upper = Column(Numeric(3, 2))
    p_value = Column(Numeric(10, 8))
    is_significant = Column(Boolean, default=False)
    
    # Analysis metadata
    analysis_period = Column(String(20))  # daily, weekly, monthly
    data_points_count = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('correlation_strength')
    def validate_correlation_strength(self, key, strength):
        """Validate correlation strength."""
        if strength is not None and (strength < -1.0 or strength > 1.0):
            raise ValueError("Correlation strength must be between -1.0 and 1.0")
        return strength
    
    @validates('p_value')
    def validate_p_value(self, key, p_value):
        """Validate p-value."""
        if p_value is not None and (p_value < 0 or p_value > 1):
            raise ValueError("P-value must be between 0 and 1")
        return p_value
    
    @validates('health_metric')
    def validate_health_metric(self, key, metric):
        """Validate health metric."""
        valid_metrics = ['mood', 'stress', 'sleep', 'exercise', 'wellness']
        if metric not in valid_metrics:
            raise ValueError(f"Health metric must be one of: {valid_metrics}")
        return metric
    
    # Properties
    @property
    def correlation_interpretation(self):
        """Interpret correlation strength."""
        if not self.correlation_strength:
            return None
        
        strength = abs(self.correlation_strength)
        if strength >= 0.7:
            return 'strong'
        elif strength >= 0.3:
            return 'moderate'
        else:
            return 'weak'
    
    @property
    def correlation_direction(self):
        """Get correlation direction."""
        if not self.correlation_strength:
            return None
        
        if self.correlation_strength > 0:
            return 'positive'
        elif self.correlation_strength < 0:
            return 'negative'
        else:
            return 'none'
    
    @property
    def is_statistically_significant(self):
        """Check if correlation is statistically significant."""
        return self.p_value is not None and self.p_value < 0.05
    
    # Methods
    def to_dict(self):
        """Convert correlation to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'correlation_date': self.correlation_date.isoformat() if self.correlation_date else None,
            'health_metric': self.health_metric,
            'health_score': float(self.health_score) if self.health_score else None,
            'spending_amount': float(self.spending_amount) if self.spending_amount else None,
            'spending_category': self.spending_category,
            'correlation_strength': float(self.correlation_strength) if self.correlation_strength else None,
            'confidence_interval_lower': float(self.confidence_interval_lower) if self.confidence_interval_lower else None,
            'confidence_interval_upper': float(self.confidence_interval_upper) if self.confidence_interval_upper else None,
            'p_value': float(self.p_value) if self.p_value else None,
            'is_significant': self.is_significant,
            'analysis_period': self.analysis_period,
            'data_points_count': self.data_points_count,
            'correlation_interpretation': self.correlation_interpretation,
            'correlation_direction': self.correlation_direction,
            'is_statistically_significant': self.is_statistically_significant,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<HealthSpendingCorrelation(id={self.id}, user_id={self.user_id}, metric='{self.health_metric}', correlation={self.correlation_strength})>"


class HealthGoal(Base):
    """Health goal setting and progress tracking."""
    
    __tablename__ = 'health_goals'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Goal information
    goal_name = Column(String(255), nullable=False)
    goal_type = Column(String(50), nullable=False)  # mood, stress, sleep, exercise, nutrition
    target_value = Column(Numeric(10, 2))
    current_value = Column(Numeric(10, 2))
    unit = Column(String(50))
    
    # Goal timeline
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
    @validates('goal_type')
    def validate_goal_type(self, key, goal_type):
        """Validate goal type."""
        valid_types = ['mood', 'stress', 'sleep', 'exercise', 'nutrition', 'wellness']
        if goal_type not in valid_types:
            raise ValueError(f"Goal type must be one of: {valid_types}")
        return goal_type
    
    @validates('progress_percentage')
    def validate_progress_percentage(self, key, percentage):
        """Validate progress percentage."""
        if percentage < 0 or percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        return percentage
    
    # Properties
    @property
    def is_overdue(self):
        """Check if goal is overdue."""
        if not self.target_date or self.is_completed:
            return False
        return datetime.now().date() > self.target_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining to target date."""
        if not self.target_date or self.is_completed:
            return None
        delta = self.target_date - datetime.now().date()
        return max(0, delta.days)
    
    @property
    def status(self):
        """Get goal status."""
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
    
    # Methods
    def update_progress(self, current_value):
        """Update goal progress."""
        self.current_value = current_value
        
        if self.target_value and self.current_value:
            if self.target_value > 0:
                progress = min(100, (self.current_value / self.target_value) * 100)
                self.progress_percentage = int(progress)
            else:
                self.progress_percentage = 100
        
        # Check if goal is completed
        if self.progress_percentage >= 100 and not self.is_completed:
            self.complete_goal()
    
    def complete_goal(self):
        """Mark goal as completed."""
        self.is_completed = True
        self.completion_date = datetime.now().date()
        self.progress_percentage = 100
    
    def to_dict(self):
        """Convert health goal to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'goal_name': self.goal_name,
            'goal_type': self.goal_type,
            'target_value': float(self.target_value) if self.target_value else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'unit': self.unit,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'progress_percentage': self.progress_percentage,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_remaining': self.days_remaining,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<HealthGoal(id={self.id}, user_id={self.user_id}, name='{self.goal_name}', progress={self.progress_percentage}%)>" 