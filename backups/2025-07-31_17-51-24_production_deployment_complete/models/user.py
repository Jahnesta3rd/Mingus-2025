"""
User model for authentication and user management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base  # Use shared Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - using back_populates for bidirectional relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    onboarding_progress = relationship("OnboardingProgress", back_populates="user")
    health_checkins = relationship("UserHealthCheckin", back_populates="user")
    health_correlations = relationship("HealthSpendingCorrelation", back_populates="user")
    customer = relationship("Customer", back_populates="user", uselist=False)
    
    # Communication preferences relationships
    communication_preferences = relationship("CommunicationPreferences", back_populates="user", uselist=False)
    sms_consent = relationship("SMSConsent", back_populates="user", uselist=False)
    consent_records = relationship("ConsentRecord", back_populates="user")
    alert_type_preferences = relationship("AlertTypePreference", back_populates="user")
    delivery_logs = relationship("DeliveryLog", back_populates="user")
    opt_out_history = relationship("OptOutHistory", back_populates="user")
    engagement_metrics = relationship("UserEngagementMetrics", back_populates="user", uselist=False)
    
    # Communication analytics relationships
    communication_metrics = relationship("CommunicationMetrics", back_populates="user")
    financial_impact_metrics = relationship("FinancialImpactMetrics", back_populates="user")
    
    # Behavioral trigger relationships
    trigger_events = relationship("TriggerEvent", back_populates="user")
    behavior_patterns = relationship("UserBehaviorPattern", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 