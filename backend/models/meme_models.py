"""
Meme Splash Page Feature Models
Models for the meme splash page feature in the Mingus personal finance app.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import json
from .base import Base


class Meme(Base):
    """Core meme storage model"""
    __tablename__ = 'memes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_url = Column(String(500), nullable=False)
    image_file_path = Column(String(500))  # Alternative local file path
    category = Column(String(20), nullable=False)
    caption_text = Column(Text, nullable=False)
    alt_text = Column(Text, nullable=False)  # For accessibility
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    engagement_score = Column(Integer, default=0.0)
    priority = Column(Integer, default=5)
    tags = Column(Text)  # JSON stored as TEXT for additional categorization
    source_attribution = Column(String(200))  # Credit to original creator if applicable
    admin_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user_history = relationship("UserMemeHistory", back_populates="meme", cascade="all, delete-orphan")
    user_preferences_last_shown = relationship("UserMemePreferences", back_populates="last_meme_shown")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            category.in_(['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out']),
            name='valid_meme_category'
        ),
        CheckConstraint(
            priority >= 1,
            name='valid_meme_priority_min'
        ),
        CheckConstraint(
            priority <= 10,
            name='valid_meme_priority_max'
        ),
        Index('idx_memes_category', 'category'),
        Index('idx_memes_active', 'is_active'),
        Index('idx_memes_priority', 'priority'),
        Index('idx_memes_engagement', 'engagement_score'),
        Index('idx_memes_created_at', 'created_at'),
        Index('idx_memes_category_active', 'category', 'is_active'),
    )
    
    def __repr__(self):
        return f'<Meme {self.id}: {self.category}>'
    
    def to_dict(self):
        """Convert meme to dictionary"""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'image_file_path': self.image_file_path,
            'category': self.category,
            'caption_text': self.caption_text,
            'alt_text': self.alt_text,
            'is_active': self.is_active,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'engagement_score': self.engagement_score,
            'priority': self.priority,
            'tags': json.loads(self.tags) if self.tags else [],
            'source_attribution': self.source_attribution,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def tags_list(self):
        """Get tags as a list"""
        return json.loads(self.tags) if self.tags else []
    
    @tags_list.setter
    def tags_list(self, tags):
        """Set tags from a list"""
        self.tags = json.dumps(tags) if tags else None


class UserMemeHistory(Base):
    """Track user interactions with memes"""
    __tablename__ = 'user_meme_history'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    meme_id = Column(String(36), ForeignKey('memes.id', ondelete='CASCADE'), nullable=False)
    viewed_at = Column(DateTime, default=func.now(), nullable=False)
    time_spent_seconds = Column(Integer, default=0)
    interaction_type = Column(String(20), default='view')
    session_id = Column(String(100))  # For tracking user sessions
    source_page = Column(String(200))  # Where the meme was displayed
    device_type = Column(String(50))
    user_agent = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meme_history")
    meme = relationship("Meme", back_populates="user_history")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            interaction_type.in_(['view', 'like', 'share', 'skip', 'report']),
            name='valid_interaction_type'
        ),
        Index('idx_user_meme_history_user_id', 'user_id'),
        Index('idx_user_meme_history_meme_id', 'meme_id'),
        Index('idx_user_meme_history_viewed_at', 'viewed_at'),
        Index('idx_user_meme_history_user_viewed', 'user_id', 'viewed_at'),
        Index('idx_user_meme_history_interaction', 'interaction_type'),
    )
    
    def __repr__(self):
        return f'<UserMemeHistory {self.user_id}:{self.meme_id}:{self.interaction_type}>'
    
    def to_dict(self):
        """Convert user meme history to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'meme_id': self.meme_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
            'time_spent_seconds': self.time_spent_seconds,
            'interaction_type': self.interaction_type,
            'session_id': self.session_id,
            'source_page': self.source_page,
            'device_type': self.device_type,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserMemePreferences(Base):
    """User control and customization settings for memes"""
    __tablename__ = 'user_meme_preferences'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    memes_enabled = Column(Boolean, default=True)
    preferred_categories = Column(Text)  # JSON array of preferred categories
    frequency_setting = Column(String(20), default='daily')
    custom_frequency_days = Column(Integer, default=1)
    last_meme_shown_at = Column(DateTime)
    last_meme_shown_id = Column(String(36), ForeignKey('memes.id', ondelete='SET NULL'))
    opt_out_reason = Column(Text)  # Optional feedback when user disables memes
    opt_out_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meme_preferences")
    last_meme_shown = relationship("Meme", back_populates="user_preferences_last_shown")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            frequency_setting.in_(['daily', 'weekly', 'disabled', 'custom']),
            name='valid_frequency_setting'
        ),
        CheckConstraint(
            custom_frequency_days >= 1,
            name='valid_custom_frequency_days_min'
        ),
        CheckConstraint(
            custom_frequency_days <= 30,
            name='valid_custom_frequency_days_max'
        ),
        Index('idx_user_meme_preferences_enabled', 'memes_enabled'),
        Index('idx_user_meme_preferences_frequency', 'frequency_setting'),
        Index('idx_user_meme_preferences_last_shown', 'last_meme_shown_at'),
    )
    
    def __repr__(self):
        return f'<UserMemePreferences {self.user_id}:{self.frequency_setting}>'
    
    def to_dict(self):
        """Convert user meme preferences to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'memes_enabled': self.memes_enabled,
            'preferred_categories': json.loads(self.preferred_categories) if self.preferred_categories else [],
            'frequency_setting': self.frequency_setting,
            'custom_frequency_days': self.custom_frequency_days,
            'last_meme_shown_at': self.last_meme_shown_at.isoformat() if self.last_meme_shown_at else None,
            'last_meme_shown_id': self.last_meme_shown_id,
            'opt_out_reason': self.opt_out_reason,
            'opt_out_date': self.opt_out_date.isoformat() if self.opt_out_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def preferred_categories_list(self):
        """Get preferred categories as a list"""
        return json.loads(self.preferred_categories) if self.preferred_categories else []
    
    @preferred_categories_list.setter
    def preferred_categories_list(self, categories):
        """Set preferred categories from a list"""
        self.preferred_categories = json.dumps(categories) if categories else None
    
    def should_show_meme(self):
        """Determine if a meme should be shown based on frequency settings"""
        if not self.memes_enabled:
            return False
        
        if self.frequency_setting == 'disabled':
            return False
        
        if not self.last_meme_shown_at:
            return True
        
        now = datetime.utcnow()
        days_since_last = (now - self.last_meme_shown_at).days
        
        if self.frequency_setting == 'daily':
            return days_since_last >= 1
        elif self.frequency_setting == 'weekly':
            return days_since_last >= 7
        elif self.frequency_setting == 'custom':
            return days_since_last >= self.custom_frequency_days
        
        return True
