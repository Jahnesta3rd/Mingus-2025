from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from .base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB

class QuestionnaireSubmission(Base):
    """Store questionnaire submissions with email addresses for follow-up"""
    __tablename__ = 'questionnaire_submissions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    
    # Questionnaire data
    answers = Column(JSONB, nullable=False)  # Store the 5 question answers
    total_score = Column(Integer, nullable=False)
    wellness_level = Column(String(100), nullable=False)
    wellness_description = Column(Text)
    
    # User journey tracking
    has_signed_up = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Set when user signs up
    
    # Marketing data
    source = Column(String(100), default='financial_wellness_questionnaire')
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow)
    signed_up_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<QuestionnaireSubmission {self.email}: {self.total_score}%>'
    
    def to_dict(self):
        """Convert submission to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'answers': self.answers,
            'total_score': self.total_score,
            'wellness_level': self.wellness_level,
            'wellness_description': self.wellness_description,
            'has_signed_up': self.has_signed_up,
            'user_id': str(self.user_id) if self.user_id else None,
            'source': self.source,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'signed_up_at': self.signed_up_at.isoformat() if self.signed_up_at else None
        }
