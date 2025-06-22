"""
User profile model for financial and demographic data
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Financial Information
    monthly_income = Column(Float)
    income_frequency = Column(String(50))  # monthly, bi-weekly, weekly, etc.
    primary_income_source = Column(String(100))
    secondary_income_source = Column(String(100))
    
    # Financial Goals
    primary_goal = Column(String(100))  # save, invest, debt_payoff, etc.
    goal_amount = Column(Float)
    goal_timeline_months = Column(Integer)
    
    # Demographics
    age_range = Column(String(50))  # 18-25, 26-35, 36-45, etc.
    location_state = Column(String(50))
    location_city = Column(String(100))
    household_size = Column(Integer)
    employment_status = Column(String(50))  # employed, self_employed, student, etc.
    
    # Financial Situation
    current_savings = Column(Float)
    current_debt = Column(Float)
    credit_score_range = Column(String(50))  # excellent, good, fair, poor
    
    # Preferences
    risk_tolerance = Column(String(50))  # conservative, moderate, aggressive
    investment_experience = Column(String(50))  # beginner, intermediate, advanced
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_complete = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>' 