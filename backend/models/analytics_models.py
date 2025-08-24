"""
Analytics Models for tracking user events and behavior
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from .base import Base


class UserEvent(Base):
    """Model for tracking user events and interactions"""
    __tablename__ = 'user_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(50), nullable=False)  # meme_opt_out, meme_opt_in, meme_view, etc.
    event_data = Column(Text)  # JSON data for additional event context
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    session_id = Column(String(100))  # For tracking user sessions
    source = Column(String(50))  # splash_page, settings, etc.
    user_agent = Column(Text)  # Browser/device info
    ip_address = Column(String(45))  # User IP address
    
    # Relationships
    user = relationship("User", back_populates="events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_events_user_id', 'user_id'),
        Index('idx_user_events_event_type', 'event_type'),
        Index('idx_user_events_timestamp', 'timestamp'),
        Index('idx_user_events_user_type_timestamp', 'user_id', 'event_type', 'timestamp'),
        Index('idx_user_events_source', 'source'),
    )
    
    def __repr__(self):
        return f'<UserEvent {self.user_id}:{self.event_type}:{self.timestamp}>'


class AnalyticsEvent(Base):
    """Model for system-level analytics events"""
    __tablename__ = 'analytics_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)  # system_event, error, performance, etc.
    event_data = Column(Text)  # JSON data for event details
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    severity = Column(String(20), default='info')  # info, warning, error, critical
    source = Column(String(50))  # service name or component
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_events_event_type', 'event_type'),
        Index('idx_analytics_events_timestamp', 'timestamp'),
        Index('idx_analytics_events_severity', 'severity'),
        Index('idx_analytics_events_source', 'source'),
        Index('idx_analytics_events_user_id', 'user_id'),
    )
    
    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}:{self.severity}:{self.timestamp}>'


class MemeAnalytics(Base):
    """Model for meme-specific analytics and performance metrics"""
    __tablename__ = 'meme_analytics'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), ForeignKey('memes.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, nullable=False)  # Date for daily aggregation
    
    # Daily metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    skips = Column(Integer, default=0)
    opt_outs = Column(Integer, default=0)  # Users who opted out after seeing this meme
    
    # Engagement metrics
    engagement_rate = Column(Integer, default=0)  # (likes + shares) / views * 100
    skip_rate = Column(Integer, default=0)  # skips / views * 100
    opt_out_rate = Column(Integer, default=0)  # opt_outs / views * 100
    
    # User demographics (aggregated)
    age_group_distribution = Column(Text)  # JSON with age group counts
    income_level_distribution = Column(Text)  # JSON with income level counts
    education_level_distribution = Column(Text)  # JSON with education level counts
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    meme = relationship("Meme", back_populates="analytics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_meme_analytics_meme_id', 'meme_id'),
        Index('idx_meme_analytics_date', 'date'),
        Index('idx_meme_analytics_engagement_rate', 'engagement_rate'),
        Index('idx_meme_analytics_opt_out_rate', 'opt_out_rate'),
    )
    
    def __repr__(self):
        return f'<MemeAnalytics {self.meme_id}:{self.date}:{self.views}>'


class UserMemeAnalytics(Base):
    """Model for user-specific meme interaction analytics"""
    __tablename__ = 'user_meme_analytics'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Interaction counts
    total_memes_viewed = Column(Integer, default=0)
    total_memes_liked = Column(Integer, default=0)
    total_memes_shared = Column(Integer, default=0)
    total_memes_skipped = Column(Integer, default=0)
    
    # Preference tracking
    favorite_categories = Column(Text)  # JSON array of most engaged categories
    least_favorite_categories = Column(Text)  # JSON array of least engaged categories
    
    # Engagement patterns
    average_view_time_seconds = Column(Integer, default=0)
    most_active_time_of_day = Column(String(10))  # HH:MM format
    most_active_day_of_week = Column(String(10))  # Monday, Tuesday, etc.
    
    # Opt-out history
    total_opt_outs = Column(Integer, default=0)
    total_opt_ins = Column(Integer, default=0)
    last_opt_out_date = Column(DateTime)
    last_opt_in_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meme_analytics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_meme_analytics_user_id', 'user_id'),
        Index('idx_user_meme_analytics_total_views', 'total_memes_viewed'),
        Index('idx_user_meme_analytics_engagement', 'total_memes_liked'),
    )
    
    def __repr__(self):
        return f'<UserMemeAnalytics {self.user_id}:{self.total_memes_viewed}>'
