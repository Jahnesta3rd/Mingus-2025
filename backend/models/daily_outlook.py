#!/usr/bin/env python3
"""
Mingus Application - Daily Outlook Models
SQLAlchemy models for daily outlook feature
"""

from datetime import datetime, date
from decimal import Decimal
from .database import db
import enum


class RelationshipStatus(enum.Enum):
    """Enum for relationship status"""
    SINGLE_CAREER_FOCUSED = "single_career_focused"
    SINGLE_LOOKING = "single_looking"
    DATING = "dating"
    EARLY_RELATIONSHIP = "early_relationship"
    COMMITTED = "committed"
    ENGAGED = "engaged"
    MARRIED = "married"
    COMPLICATED = "complicated"


class TemplateTier(enum.Enum):
    """Enum for template tiers"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"


class TemplateCategory(enum.Enum):
    """Enum for template categories"""
    FINANCIAL = "financial"
    WELLNESS = "wellness"
    RELATIONSHIP = "relationship"
    CAREER = "career"


class DailyOutlook(db.Model):
    """
    Daily outlook model for tracking user's daily insights and actions
    """
    __tablename__ = 'daily_outlooks'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Date of the outlook
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Balance score (0-100)
    balance_score = db.Column(db.Integer, nullable=False)
    
    # Weight scores (decimal values)
    financial_weight = db.Column(db.Numeric(5, 2), nullable=False)
    wellness_weight = db.Column(db.Numeric(5, 2), nullable=False)
    relationship_weight = db.Column(db.Numeric(5, 2), nullable=False)
    career_weight = db.Column(db.Numeric(5, 2), nullable=False)
    
    # Content fields
    primary_insight = db.Column(db.Text, nullable=True)
    quick_actions = db.Column(db.JSON, nullable=True)
    encouragement_message = db.Column(db.Text, nullable=True)
    surprise_element = db.Column(db.Text, nullable=True)
    
    # Tracking fields
    streak_count = db.Column(db.Integer, nullable=False, default=0)
    viewed_at = db.Column(db.DateTime, nullable=True)
    actions_completed = db.Column(db.JSON, nullable=True)
    user_rating = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships - defined in User model to avoid conflicts
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_daily_outlooks_user_date', 'user_id', 'date'),
        db.Index('idx_daily_outlooks_created_at', 'created_at'),
        db.Index('idx_daily_outlooks_balance_score', 'balance_score'),
        db.Index('idx_daily_outlooks_streak_count', 'streak_count'),
        db.CheckConstraint('balance_score >= 0 AND balance_score <= 100', name='check_balance_score_range'),
        db.CheckConstraint('financial_weight >= 0 AND financial_weight <= 100', name='check_financial_weight_range'),
        db.CheckConstraint('wellness_weight >= 0 AND wellness_weight <= 100', name='check_wellness_weight_range'),
        db.CheckConstraint('relationship_weight >= 0 AND relationship_weight <= 100', name='check_relationship_weight_range'),
        db.CheckConstraint('career_weight >= 0 AND career_weight <= 100', name='check_career_weight_range'),
        db.CheckConstraint('user_rating >= 1 AND user_rating <= 5', name='check_user_rating_range'),
        db.CheckConstraint('streak_count >= 0', name='check_positive_streak_count'),
        db.UniqueConstraint('user_id', 'date', name='unique_user_date_outlook'),
    )
    
    def __repr__(self):
        return f'<DailyOutlook {self.id}: User {self.user_id} - {self.date}>'
    
    def to_dict(self):
        """Convert daily outlook to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'balance_score': self.balance_score,
            'financial_weight': float(self.financial_weight) if self.financial_weight else None,
            'wellness_weight': float(self.wellness_weight) if self.wellness_weight else None,
            'relationship_weight': float(self.relationship_weight) if self.relationship_weight else None,
            'career_weight': float(self.career_weight) if self.career_weight else None,
            'primary_insight': self.primary_insight,
            'quick_actions': self.quick_actions,
            'encouragement_message': self.encouragement_message,
            'surprise_element': self.surprise_element,
            'streak_count': self.streak_count,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
            'actions_completed': self.actions_completed,
            'user_rating': self.user_rating,
            'created_at': self.created_at.isoformat()
        }


class UserRelationshipStatus(db.Model):
    """
    User relationship status model for tracking relationship context
    """
    __tablename__ = 'user_relationship_status'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Relationship status
    status = db.Column(db.Enum(RelationshipStatus), nullable=False)
    
    # Satisfaction and impact scores (1-10)
    satisfaction_score = db.Column(db.Integer, nullable=False)
    financial_impact_score = db.Column(db.Integer, nullable=False)
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - defined in User model to avoid conflicts
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_relationship_status_user', 'user_id'),
        db.Index('idx_relationship_status_status', 'status'),
        db.Index('idx_relationship_status_updated_at', 'updated_at'),
        db.CheckConstraint('satisfaction_score >= 1 AND satisfaction_score <= 10', name='check_satisfaction_score_range'),
        db.CheckConstraint('financial_impact_score >= 1 AND financial_impact_score <= 10', name='check_financial_impact_score_range'),
        db.UniqueConstraint('user_id', name='unique_user_relationship_status'),
    )
    
    def __repr__(self):
        return f'<UserRelationshipStatus {self.id}: User {self.user_id} - {self.status.value}>'
    
    def to_dict(self):
        """Convert relationship status to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status.value if self.status else None,
            'satisfaction_score': self.satisfaction_score,
            'financial_impact_score': self.financial_impact_score,
            'updated_at': self.updated_at.isoformat()
        }


class DailyOutlookTemplate(db.Model):
    """
    Daily outlook template model for storing content templates
    """
    __tablename__ = 'daily_outlook_templates'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Template identification
    template_name = db.Column(db.String(255), nullable=False, index=True)
    
    # Template classification
    tier = db.Column(db.Enum(TemplateTier), nullable=False, index=True)
    category = db.Column(db.Enum(TemplateCategory), nullable=False, index=True)
    
    # Template content
    content_template = db.Column(db.Text, nullable=False)
    
    # Trigger conditions (JSON)
    trigger_conditions = db.Column(db.JSON, nullable=True)
    
    # Active status
    active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_outlook_templates_tier_category', 'tier', 'category'),
        db.Index('idx_outlook_templates_active', 'active'),
        db.Index('idx_outlook_templates_created_at', 'created_at'),
        db.Index('idx_outlook_templates_name', 'template_name'),
    )
    
    def __repr__(self):
        return f'<DailyOutlookTemplate {self.id}: {self.template_name} ({self.tier.value}/{self.category.value})>'
    
    def to_dict(self):
        """Convert template to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'template_name': self.template_name,
            'tier': self.tier.value if self.tier else None,
            'category': self.category.value if self.category else None,
            'content_template': self.content_template,
            'trigger_conditions': self.trigger_conditions,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
