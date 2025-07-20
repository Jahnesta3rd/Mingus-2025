from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey
from datetime import datetime
from .base import Base

class LifestyleQuestionnaireSubmission(Base):
    __tablename__ = 'lifestyle_questionnaire_submissions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    responses = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'responses': self.responses,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        } 