from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, ForeignKey
from datetime import datetime
from .base import Base

class FinancialQuestionnaireSubmission(Base):
    __tablename__ = 'financial_questionnaire_submissions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    monthly_income = Column(Float)
    monthly_expenses = Column(Float)
    current_savings = Column(Float)
    total_debt = Column(Float)
    risk_tolerance = Column(Integer)
    financial_goals = Column(JSON)
    financial_health_score = Column(Integer)
    financial_health_level = Column(String(50))
    recommendations = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'monthly_income': self.monthly_income,
            'monthly_expenses': self.monthly_expenses,
            'current_savings': self.current_savings,
            'total_debt': self.total_debt,
            'risk_tolerance': self.risk_tolerance,
            'financial_goals': self.financial_goals,
            'financial_health_score': self.financial_health_score,
            'financial_health_level': self.financial_health_level,
            'recommendations': self.recommendations,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        } 