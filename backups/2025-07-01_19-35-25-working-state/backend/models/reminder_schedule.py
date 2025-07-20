from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.base import Base

class ReminderSchedule(Base):
    """Model for scheduling user reminders and check-ins."""
    
    __tablename__ = 'reminder_schedules'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reminder_type = Column(String(50), nullable=False)  # 'first_checkin', 'weekly_checkin', 'goal_reminder', etc.
    scheduled_date = Column(DateTime, nullable=False)
    frequency = Column(String(20), default='weekly')  # 'daily', 'weekly', 'biweekly', 'monthly'
    enabled = Column(Boolean, default=True)
    preferences = Column(JSON)  # Store user preferences for this reminder
    message = Column(Text)  # Custom message for the reminder
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reminder_schedules")
    
    def __repr__(self):
        return f"<ReminderSchedule(id={self.id}, user_id={self.user_id}, type={self.reminder_type}, scheduled={self.scheduled_date})>"
    
    def to_dict(self):
        """Convert reminder schedule to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reminder_type': self.reminder_type,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'frequency': self.frequency,
            'enabled': self.enabled,
            'preferences': self.preferences,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_reminders(cls, user_id: int, reminder_type: str = None):
        """Get reminders for a specific user."""
        query = cls.query.filter(cls.user_id == user_id)
        if reminder_type:
            query = query.filter(cls.reminder_type == reminder_type)
        return query.all()
    
    @classmethod
    def get_upcoming_reminders(cls, days_ahead: int = 7):
        """Get reminders scheduled within the next N days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        return cls.query.filter(
            cls.scheduled_date <= cutoff_date,
            cls.enabled == True
        ).all()
    
    def is_due(self) -> bool:
        """Check if reminder is due to be sent."""
        from datetime import datetime
        return datetime.utcnow() >= self.scheduled_date
    
    def calculate_next_scheduled_date(self):
        """Calculate the next scheduled date based on frequency."""
        from datetime import datetime, timedelta
        
        if not self.scheduled_date:
            return None
            
        if self.frequency == 'daily':
            return self.scheduled_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return self.scheduled_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            return self.scheduled_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            # Simple monthly calculation (30 days)
            return self.scheduled_date + timedelta(days=30)
        else:
            return self.scheduled_date + timedelta(weeks=1)  # Default to weekly 