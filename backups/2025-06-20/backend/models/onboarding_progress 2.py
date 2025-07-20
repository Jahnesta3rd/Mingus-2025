from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class OnboardingProgress(Base):
    """Onboarding progress tracking model"""
    __tablename__ = 'onboarding_progress'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Step tracking
    current_step = Column(String(100), default='welcome')  # welcome, profile, goals, preferences, complete
    total_steps = Column(Integer, default=5)
    completed_steps = Column(Integer, default=0)
    
    # Step completion status (JSON stored as text)
    step_status = Column(Text, nullable=True)  # JSON string of step completion status
    
    # Progress details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Completion status
    is_complete = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)
    
    # User preferences and responses
    onboarding_responses = Column(Text, nullable=True)  # JSON string of user responses
    
    # Relationship
    user = relationship("User", back_populates="onboarding_progress")
    
    def __repr__(self):
        return f"<OnboardingProgress(id='{self.id}', user_id='{self.user_id}', current_step='{self.current_step}', is_complete={self.is_complete})>"
    
    def to_dict(self):
        """Convert progress object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'step_status': self.step_status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_complete': self.is_complete,
            'completion_percentage': self.completion_percentage,
            'onboarding_responses': self.onboarding_responses
        }
    
    def update_progress(self, step_name: str, is_completed: bool = True):
        """Update progress for a specific step"""
        import json
        
        # Parse existing step status
        step_status = {}
        if self.step_status:
            try:
                step_status = json.loads(self.step_status)
            except json.JSONDecodeError:
                step_status = {}
        
        # Update step status
        step_status[step_name] = {
            'completed': is_completed,
            'completed_at': datetime.utcnow().isoformat() if is_completed else None
        }
        
        # Update completion count
        completed_count = sum(1 for step in step_status.values() if step.get('completed', False))
        
        # Update fields
        self.step_status = json.dumps(step_status)
        self.completed_steps = completed_count
        self.completion_percentage = int((completed_count / self.total_steps) * 100)
        self.last_activity = datetime.utcnow()
        
        # Check if onboarding is complete
        if self.completion_percentage >= 100:
            self.is_complete = True
            self.completed_at = datetime.utcnow()
            self.current_step = 'complete' 