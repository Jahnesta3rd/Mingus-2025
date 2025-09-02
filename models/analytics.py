"""
MINGUS Application - Analytics Models
=====================================

SQLAlchemy models for analytics and business intelligence.

Models:
- UserAnalytics: User behavior and engagement tracking
- PerformanceMetric: System performance monitoring
- FeatureUsage: Feature usage analytics and tracking
- UserFeedback: User feedback and satisfaction tracking

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


class UserAnalytics(Base):
    """User behavior and engagement tracking."""
    
    __tablename__ = 'user_analytics'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Event information
    event_date = Column(Date, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSONB)
    
    # Session information
    session_duration = Column(Integer)  # in seconds
    page_views = Column(Integer)
    features_used = Column(JSONB)
    
    # Engagement metrics
    engagement_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    retention_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    
    # Validation
    @validates('session_duration')
    def validate_session_duration(self, key, duration):
        """Validate session duration."""
        if duration is not None and duration < 0:
            raise ValueError("Session duration cannot be negative")
        return duration
    
    @validates('page_views')
    def validate_page_views(self, key, views):
        """Validate page views."""
        if views is not None and views < 0:
            raise ValueError("Page views cannot be negative")
        return views
    
    @validates('engagement_score', 'retention_score')
    def validate_scores(self, key, score):
        """Validate engagement and retention scores."""
        if score is not None and (score < 0 or score > 1):
            raise ValueError(f"{key} must be between 0 and 1")
        return score
    
    # Properties
    @property
    def session_minutes(self):
        """Convert session duration to minutes."""
        if not self.session_duration:
            return None
        return round(self.session_duration / 60, 1)
    
    @property
    def engagement_level(self):
        """Get engagement level based on score."""
        if not self.engagement_score:
            return None
        
        if self.engagement_score >= 0.8:
            return 'high'
        elif self.engagement_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    @property
    def retention_level(self):
        """Get retention level based on score."""
        if not self.retention_score:
            return None
        
        if self.retention_score >= 0.8:
            return 'excellent'
        elif self.retention_score >= 0.6:
            return 'good'
        elif self.retention_score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    # Methods
    def to_dict(self):
        """Convert user analytics to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'session_duration': self.session_duration,
            'session_minutes': self.session_minutes,
            'page_views': self.page_views,
            'features_used': self.features_used,
            'engagement_score': float(self.engagement_score) if self.engagement_score else None,
            'retention_score': float(self.retention_score) if self.retention_score else None,
            'engagement_level': self.engagement_level,
            'retention_level': self.retention_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<UserAnalytics(id={self.id}, user_id={self.user_id}, event_type='{self.event_type}', engagement_score={self.engagement_score})>"


class PerformanceMetric(Base):
    """System performance monitoring."""
    
    __tablename__ = 'performance_metrics'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric information
    metric_date = Column(Date, nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(15, 2))
    metric_unit = Column(String(50))
    
    # Categorization
    category = Column(String(100))
    subcategory = Column(String(100))
    
    # Additional data
    extra_metadata = Column('metadata', JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Validation
    @validates('metric_name')
    def validate_metric_name(self, key, name):
        """Validate metric name."""
        if not name or len(name.strip()) == 0:
            raise ValueError("Metric name cannot be empty")
        return name.strip()
    
    # Properties
    @property
    def is_positive(self):
        """Check if metric value is positive."""
        if self.metric_value is None:
            return None
        return self.metric_value > 0
    
    @property
    def formatted_value(self):
        """Get formatted metric value with unit."""
        if self.metric_value is None:
            return None
        
        value = float(self.metric_value)
        if self.metric_unit:
            return f"{value} {self.metric_unit}"
        return str(value)
    
    # Methods
    def to_dict(self):
        """Convert performance metric to dictionary."""
        return {
            'id': str(self.id),
            'metric_date': self.metric_date.isoformat() if self.metric_date else None,
            'metric_name': self.metric_name,
            'metric_value': float(self.metric_value) if self.metric_value else None,
            'metric_unit': self.metric_unit,
            'category': self.category,
            'subcategory': self.subcategory,
            'metadata': self.extra_metadata,
            'is_positive': self.is_positive,
            'formatted_value': self.formatted_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<PerformanceMetric(id={self.id}, name='{self.metric_name}', value={self.formatted_value})>"


class FeatureUsage(Base):
    """Feature usage analytics and tracking."""
    
    __tablename__ = 'feature_usage'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Feature information
    feature_name = Column(String(100), nullable=False)
    usage_date = Column(Date, nullable=False)
    usage_count = Column(Integer, default=1)
    usage_duration = Column(Integer)  # in seconds
    
    # Performance metrics
    success_rate = Column(Numeric(3, 2))  # 0.0 to 1.0
    error_count = Column(Integer, default=0)
    performance_metrics = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('usage_count')
    def validate_usage_count(self, key, count):
        """Validate usage count."""
        if count < 0:
            raise ValueError("Usage count cannot be negative")
        return count
    
    @validates('usage_duration')
    def validate_usage_duration(self, key, duration):
        """Validate usage duration."""
        if duration is not None and duration < 0:
            raise ValueError("Usage duration cannot be negative")
        return duration
    
    @validates('success_rate')
    def validate_success_rate(self, key, rate):
        """Validate success rate."""
        if rate is not None and (rate < 0 or rate > 1):
            raise ValueError("Success rate must be between 0 and 1")
        return rate
    
    @validates('error_count')
    def validate_error_count(self, key, count):
        """Validate error count."""
        if count < 0:
            raise ValueError("Error count cannot be negative")
        return count
    
    # Properties
    @property
    def usage_minutes(self):
        """Convert usage duration to minutes."""
        if not self.usage_duration:
            return None
        return round(self.usage_duration / 60, 1)
    
    @property
    def success_percentage(self):
        """Convert success rate to percentage."""
        if not self.success_rate:
            return None
        return round(self.success_rate * 100, 1)
    
    @property
    def is_successful(self):
        """Check if usage was successful."""
        if self.success_rate is None:
            return None
        return self.success_rate >= 0.8
    
    @property
    def has_errors(self):
        """Check if usage had errors."""
        return self.error_count > 0
    
    # Methods
    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
    
    def add_error(self):
        """Increment error count."""
        self.error_count += 1
    
    def to_dict(self):
        """Convert feature usage to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'feature_name': self.feature_name,
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'usage_count': self.usage_count,
            'usage_duration': self.usage_duration,
            'usage_minutes': self.usage_minutes,
            'success_rate': float(self.success_rate) if self.success_rate else None,
            'success_percentage': self.success_percentage,
            'error_count': self.error_count,
            'performance_metrics': self.performance_metrics,
            'is_successful': self.is_successful,
            'has_errors': self.has_errors,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<FeatureUsage(id={self.id}, user_id={self.user_id}, feature='{self.feature_name}', count={self.usage_count})>"


class UserFeedback(Base):
    """User feedback and satisfaction tracking."""
    
    __tablename__ = 'user_feedback'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Feedback information
    feedback_date = Column(Date, nullable=False)
    feedback_type = Column(String(50), nullable=False)  # feature, support, general
    rating = Column(Integer)  # 1-5 scale
    feedback_text = Column(Text)
    
    # Categorization
    category = Column(String(100))
    
    # Status tracking
    status = Column(String(50), default='open')  # open, in_progress, resolved, closed
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    assigned_to = Column(UUID(as_uuid=True))
    
    # Resolution
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('rating')
    def validate_rating(self, key, rating):
        """Validate rating."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        return rating
    
    @validates('feedback_type')
    def validate_feedback_type(self, key, feedback_type):
        """Validate feedback type."""
        valid_types = ['feature', 'support', 'general', 'bug', 'enhancement']
        if feedback_type not in valid_types:
            raise ValueError(f"Feedback type must be one of: {valid_types}")
        return feedback_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status."""
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed', 'pending']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate priority."""
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return priority
    
    # Properties
    @property
    def is_positive(self):
        """Check if feedback is positive."""
        if not self.rating:
            return None
        return self.rating >= 4
    
    @property
    def is_negative(self):
        """Check if feedback is negative."""
        if not self.rating:
            return None
        return self.rating <= 2
    
    @property
    def is_resolved(self):
        """Check if feedback is resolved."""
        return self.status in ['resolved', 'closed']
    
    @property
    def is_open(self):
        """Check if feedback is open."""
        return self.status in ['open', 'in_progress', 'pending']
    
    @property
    def days_since_creation(self):
        """Calculate days since feedback creation."""
        if not self.created_at:
            return None
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.days
    
    @property
    def resolution_time_days(self):
        """Calculate resolution time in days."""
        if not self.is_resolved or not self.resolved_at or not self.created_at:
            return None
        delta = self.resolved_at - self.created_at
        return delta.days
    
    # Methods
    def assign_to(self, user_id):
        """Assign feedback to a user."""
        self.assigned_to = user_id
        self.status = 'in_progress'
    
    def mark_resolved(self, resolution_notes=None):
        """Mark feedback as resolved."""
        self.status = 'resolved'
        self.resolved_at = datetime.now(timezone.utc)
        if resolution_notes:
            self.resolution_notes = resolution_notes
    
    def close_feedback(self):
        """Close feedback."""
        self.status = 'closed'
    
    def to_dict(self):
        """Convert user feedback to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'feedback_date': self.feedback_date.isoformat() if self.feedback_date else None,
            'feedback_type': self.feedback_type,
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': str(self.assigned_to) if self.assigned_to else None,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_positive': self.is_positive,
            'is_negative': self.is_negative,
            'is_resolved': self.is_resolved,
            'is_open': self.is_open,
            'days_since_creation': self.days_since_creation,
            'resolution_time_days': self.resolution_time_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, user_id={self.user_id}, type='{self.feedback_type}', rating={self.rating})>" 