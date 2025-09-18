#!/usr/bin/env python3
"""
Mingus Application - User Models
SQLAlchemy models for user management
"""

from datetime import datetime
from .database import db

class User(db.Model):
    """
    User model for the Mingus financial application
    Based on existing user table structure from referral_models.py
    """
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Personal information
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    
    # Referral system fields (from existing structure)
    referral_code = db.Column(db.String(50), unique=True, nullable=True)
    referred_by = db.Column(db.String(255), nullable=True)
    referral_count = db.Column(db.Integer, default=0)
    successful_referrals = db.Column(db.Integer, default=0)
    feature_unlocked = db.Column(db.Boolean, default=False)
    unlock_date = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.user_id}: {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'referral_code': self.referral_code,
            'referral_count': self.referral_count,
            'successful_referrals': self.successful_referrals,
            'feature_unlocked': self.feature_unlocked,
            'unlock_date': self.unlock_date.isoformat() if self.unlock_date else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
