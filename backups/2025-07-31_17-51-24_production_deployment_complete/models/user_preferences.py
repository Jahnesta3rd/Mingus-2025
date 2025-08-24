from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.base import Base

class UserPreferences(Base):
    """Model for storing user preferences and settings."""
    
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    
    # Reminder preferences
    reminder_preferences = Column(JSON)  # Store detailed reminder settings
    
    # Communication preferences
    preferred_communication = Column(String(20), default='email')  # 'email', 'sms', 'push'
    communication_frequency = Column(String(20), default='weekly')  # 'daily', 'weekly', 'monthly'
    
    # Privacy preferences
    share_anonymized_data = Column(Boolean, default=True)
    allow_marketing_emails = Column(Boolean, default=True)
    
    # UI preferences
    theme_preference = Column(String(20), default='light')  # 'light', 'dark', 'auto'
    language_preference = Column(String(10), default='en')  # 'en', 'es', 'fr', etc.
    
    # Engagement preferences
    onboarding_completed = Column(Boolean, default=False)
    first_checkin_scheduled = Column(Boolean, default=False)
    mobile_app_downloaded = Column(Boolean, default=False)
    
    # Custom preferences
    custom_preferences = Column(JSON)  # Store any additional user preferences
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, email_notifications={self.email_notifications})>"
    
    def to_dict(self):
        """Convert user preferences to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'sms_notifications': self.sms_notifications,
            'reminder_preferences': self.reminder_preferences,
            'preferred_communication': self.preferred_communication,
            'communication_frequency': self.communication_frequency,
            'share_anonymized_data': self.share_anonymized_data,
            'allow_marketing_emails': self.allow_marketing_emails,
            'theme_preference': self.theme_preference,
            'language_preference': self.language_preference,
            'onboarding_completed': self.onboarding_completed,
            'first_checkin_scheduled': self.first_checkin_scheduled,
            'mobile_app_downloaded': self.mobile_app_downloaded,
            'custom_preferences': self.custom_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_preferences(cls, user_id: int):
        """Get preferences for a specific user."""
        return cls.query.filter(cls.user_id == user_id).first()
    
    @classmethod
    def create_default_preferences(cls, user_id: int):
        """Create default preferences for a new user."""
        default_preferences = cls(
            user_id=user_id,
            email_notifications=True,
            push_notifications=True,
            sms_notifications=False,
            reminder_preferences={
                'enabled': True,
                'frequency': 'weekly',
                'day': 'wednesday',
                'time': '10:00',
                'email': True,
                'push': True
            },
            preferred_communication='email',
            communication_frequency='weekly',
            share_anonymized_data=True,
            allow_marketing_emails=True,
            theme_preference='light',
            language_preference='en',
            onboarding_completed=False,
            first_checkin_scheduled=False,
            mobile_app_downloaded=False,
            custom_preferences={}
        )
        return default_preferences
    
    def update_reminder_preferences(self, new_preferences: dict):
        """Update reminder preferences."""
        if not self.reminder_preferences:
            self.reminder_preferences = {}
        
        self.reminder_preferences.update(new_preferences)
        self.updated_at = func.now()
    
    def get_reminder_setting(self, key: str, default=None):
        """Get a specific reminder setting."""
        if not self.reminder_preferences:
            return default
        return self.reminder_preferences.get(key, default)
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        """Check if a specific notification type is enabled."""
        if notification_type == 'email':
            return self.email_notifications
        elif notification_type == 'push':
            return self.push_notifications
        elif notification_type == 'sms':
            return self.sms_notifications
        return False
    
    def mark_onboarding_completed(self):
        """Mark onboarding as completed."""
        self.onboarding_completed = True
        self.updated_at = func.now()
    
    def mark_first_checkin_scheduled(self):
        """Mark first check-in as scheduled."""
        self.first_checkin_scheduled = True
        self.updated_at = func.now()
    
    def mark_mobile_app_downloaded(self):
        """Mark mobile app as downloaded."""
        self.mobile_app_downloaded = True
        self.updated_at = func.now() 