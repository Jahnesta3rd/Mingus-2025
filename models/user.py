"""
MINGUS Application - User Models
================================

SQLAlchemy models for user management, profiles, and onboarding.

Models:
- User: Core user authentication and account management
- UserProfile: Enhanced user profiles with demographic data
- OnboardingProgress: Step-by-step onboarding tracking

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Numeric, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class User(Base):
    """Core user model for authentication and account management."""
    
    __tablename__ = 'users'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Security tokens
    email_verification_token = Column(UUID(as_uuid=True))
    password_reset_token = Column(UUID(as_uuid=True))
    password_reset_expires_at = Column(DateTime(timezone=True))
    
    # Session management
    last_login_at = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    onboarding_progress = relationship("OnboardingProgress", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    feature_access = relationship("FeatureAccess", back_populates="user", cascade="all, delete-orphan")
    health_checkins = relationship("UserHealthCheckin", back_populates="user", cascade="all, delete-orphan")
    financial_profiles = relationship("EncryptedFinancialProfile", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("UserAnalytics", back_populates="user", cascade="all, delete-orphan")
    
    # Validation
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates('login_attempts')
    def validate_login_attempts(self, key, attempts):
        """Validate login attempts count."""
        if attempts < 0:
            raise ValueError("Login attempts cannot be negative")
        return attempts
    
    # Methods
    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False
    
    def increment_login_attempts(self):
        """Increment failed login attempts."""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            # Lock account for 30 minutes
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_login_attempts(self):
        """Reset login attempts on successful login."""
        self.login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"


class UserProfile(Base):
    """Enhanced user profile with demographic and financial information."""
    
    __tablename__ = 'user_profiles'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    phone_number = Column(String(20))
    
    # Address information
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(10), nullable=False, index=True)
    country = Column(String(100), default='USA')
    timezone = Column(String(50), default='America/New_York')
    
    # Family information
    dependents = Column(Integer, default=0)
    marital_status = Column(String(20))
    household_size = Column(Integer, default=1)
    
    # Financial information
    annual_income = Column(Numeric(12, 2), index=True)
    income_source = Column(String(100))
    
    # Employment information
    employment_status = Column(String(50))
    education_level = Column(String(50))
    occupation = Column(String(100))
    industry = Column(String(100), index=True)
    years_of_experience = Column(Integer)
    company_name = Column(String(255))
    company_size = Column(String(50))
    job_title = Column(String(100))
    naics_code = Column(String(10))
    
    # Financial preferences
    risk_tolerance = Column(String(20), default='moderate')
    financial_goals = Column(JSONB)
    preferences = Column(JSONB)
    
    # Profile completion
    profile_completion_percentage = Column(Integer, default=0)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    # Validation
    @validates('first_name', 'last_name')
    def validate_names(self, key, value):
        """Validate name fields."""
        if not value or len(value.strip()) == 0:
            raise ValueError(f"{key} cannot be empty")
        return value.strip()
    
    @validates('zip_code')
    def validate_zip_code(self, key, zip_code):
        """Validate ZIP code format."""
        if not zip_code:
            raise ValueError("ZIP code is required")
        # Basic US ZIP code validation
        if len(zip_code) not in [5, 10] or not zip_code.replace('-', '').isdigit():
            raise ValueError("Invalid ZIP code format")
        return zip_code
    
    @validates('dependents', 'household_size', 'years_of_experience')
    def validate_non_negative_integers(self, key, value):
        """Validate non-negative integer fields."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('annual_income')
    def validate_annual_income(self, key, income):
        """Validate annual income."""
        if income is not None and income < 0:
            raise ValueError("Annual income cannot be negative")
        return income
    
    @validates('phone_number')
    def validate_phone_number(self, key, phone):
        """Validate phone number format."""
        if phone:
            # Remove all non-digit characters
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) not in [10, 11]:
                raise ValueError("Invalid phone number format")
        return phone
    
    # Properties
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate user's age."""
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def is_complete(self):
        """Check if profile is complete."""
        required_fields = ['first_name', 'last_name', 'zip_code', 'annual_income', 'industry']
        return all(getattr(self, field) for field in required_fields)
    
    # Methods
    def calculate_completion_percentage(self):
        """Calculate profile completion percentage."""
        required_fields = [
            'first_name', 'last_name', 'zip_code', 'annual_income', 'industry',
            'job_title', 'education_level', 'marital_status', 'dependents'
        ]
        
        completed = sum(1 for field in required_fields if getattr(self, field))
        self.profile_completion_percentage = int((completed / len(required_fields)) * 100)
        return self.profile_completion_percentage
    
    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'phone_number': self.phone_number,
            'address_line_1': self.address_line_1,
            'address_line_2': self.address_line_2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'timezone': self.timezone,
            'dependents': self.dependents,
            'marital_status': self.marital_status,
            'household_size': self.household_size,
            'annual_income': float(self.annual_income) if self.annual_income else None,
            'income_source': self.income_source,
            'employment_status': self.employment_status,
            'education_level': self.education_level,
            'occupation': self.occupation,
            'industry': self.industry,
            'years_of_experience': self.years_of_experience,
            'company_name': self.company_name,
            'company_size': self.company_size,
            'job_title': self.job_title,
            'naics_code': self.naics_code,
            'risk_tolerance': self.risk_tolerance,
            'financial_goals': self.financial_goals,
            'preferences': self.preferences,
            'profile_completion_percentage': self.profile_completion_percentage,
            'onboarding_completed': self.onboarding_completed,
            'is_complete': self.is_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, name='{self.full_name}')>"


class OnboardingProgress(Base):
    """Step-by-step onboarding progress tracking."""
    
    __tablename__ = 'onboarding_progress'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Progress tracking
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    step_data = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="onboarding_progress")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'step_name', name='uq_user_step'),
    )
    
    # Validation
    @validates('step_order')
    def validate_step_order(self, key, order):
        """Validate step order."""
        if order < 1:
            raise ValueError("Step order must be positive")
        return order
    
    # Methods
    def complete_step(self, step_data=None):
        """Mark step as completed."""
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc)
        if step_data:
            self.step_data = step_data
    
    def to_dict(self):
        """Convert onboarding progress to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'step_name': self.step_name,
            'step_order': self.step_order,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'step_data': self.step_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<OnboardingProgress(id={self.id}, user_id={self.user_id}, step='{self.step_name}', completed={self.is_completed})>" 