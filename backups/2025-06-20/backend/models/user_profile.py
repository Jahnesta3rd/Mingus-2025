from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class UserProfile(Base):
    """User profile model for financial and demographic data"""
    __tablename__ = 'user_profiles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Financial Information
    monthly_income = Column(Float, nullable=True)
    income_frequency = Column(String(50), nullable=True)  # monthly, bi-weekly, weekly, etc.
    primary_income_source = Column(String(100), nullable=True)
    secondary_income_source = Column(String(100), nullable=True)
    
    # Expense Categories (JSON stored as text)
    expense_categories = Column(Text, nullable=True)  # JSON string of categories and amounts
    
    # Financial Goals
    primary_goal = Column(String(100), nullable=True)  # save, invest, debt_payoff, etc.
    goal_amount = Column(Float, nullable=True)
    goal_timeline_months = Column(Integer, nullable=True)
    
    # Demographics
    age_range = Column(String(50), nullable=True)  # 18-25, 26-35, 36-45, etc.
    location_state = Column(String(50), nullable=True)
    location_city = Column(String(100), nullable=True)
    household_size = Column(Integer, nullable=True)
    employment_status = Column(String(50), nullable=True)  # employed, self_employed, student, etc.
    
    # Financial Situation
    current_savings = Column(Float, nullable=True)
    current_debt = Column(Float, nullable=True)
    credit_score_range = Column(String(50), nullable=True)  # excellent, good, fair, poor
    
    # Preferences
    risk_tolerance = Column(String(50), nullable=True)  # conservative, moderate, aggressive
    investment_experience = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_complete = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(id='{self.id}', user_id='{self.user_id}', is_complete={self.is_complete})>"
    
    def to_dict(self):
        """Convert profile object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'monthly_income': self.monthly_income,
            'income_frequency': self.income_frequency,
            'primary_income_source': self.primary_income_source,
            'secondary_income_source': self.secondary_income_source,
            'expense_categories': self.expense_categories,
            'primary_goal': self.primary_goal,
            'goal_amount': self.goal_amount,
            'goal_timeline_months': self.goal_timeline_months,
            'age_range': self.age_range,
            'location_state': self.location_state,
            'location_city': self.location_city,
            'household_size': self.household_size,
            'employment_status': self.employment_status,
            'current_savings': self.current_savings,
            'current_debt': self.current_debt,
            'credit_score_range': self.credit_score_range,
            'risk_tolerance': self.risk_tolerance,
            'investment_experience': self.investment_experience,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_complete': self.is_complete
        } 