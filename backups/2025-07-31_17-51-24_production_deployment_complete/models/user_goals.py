"""
User Goals Model
Stores user financial goals and objectives
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class UserGoals(Base):
    """
    User financial goals model
    """
    __tablename__ = 'user_goals'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Goal details
    goal_name = Column(String(100), nullable=False)
    goal_type = Column(String(50), nullable=False)  # savings, debt_payoff, investment, etc.
    target_amount = Column(DECIMAL(10, 2), nullable=True)
    current_amount = Column(DECIMAL(10, 2), default=0.0)
    target_date = Column(DateTime, nullable=True)
    
    # Goal status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="user_goals")
    
    def __repr__(self):
        return f"<UserGoals(id='{self.id}', user_id='{self.user_id}', goal_name='{self.goal_name}')>"
    
    def to_dict(self):
        """Convert goal object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_name': self.goal_name,
            'goal_type': self.goal_type,
            'target_amount': float(self.target_amount) if self.target_amount else None,
            'current_amount': float(self.current_amount) if self.current_amount else 0.0,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 