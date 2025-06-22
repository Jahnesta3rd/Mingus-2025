"""
User health checkin model for tracking health metrics
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .base import Base

class UserHealthCheckin(Base):
    __tablename__ = 'user_health_checkins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Checkin date and time
    checkin_date = Column(DateTime, nullable=False, index=True)
    
    # Sleep metrics
    sleep_hours = Column(Float)  # Hours of sleep (e.g., 7.5 for 7.5 hours)
    
    # Physical activity metrics
    physical_activity_minutes = Column(Integer)
    physical_activity_level = Column(String(50))  # low, moderate, high
    
    # Relationship metrics
    relationships_rating = Column(Integer)  # 1-10 scale
    relationships_notes = Column(String(500))
    
    # Mindfulness metrics
    mindfulness_minutes = Column(Integer)
    mindfulness_type = Column(String(100))  # meditation, yoga, breathing, etc.
    
    # Health metrics
    stress_level = Column(Integer)  # 1-10 scale
    energy_level = Column(Integer)  # 1-10 scale
    mood_rating = Column(Integer)  # 1-10 scale
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="health_checkins")
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure only one checkin per user per week
        UniqueConstraint('user_id', 'checkin_date', name='uq_user_weekly_checkin'),
        # Index for efficient querying by user and date range
        Index('idx_user_health_checkin_date_range', 'user_id', 'checkin_date'),
        # Index for health metrics analysis
        Index('idx_health_metrics', 'stress_level', 'energy_level', 'mood_rating'),
    )
    
    def __repr__(self):
        return f'<UserHealthCheckin {self.user_id} {self.checkin_date}>'
    
    @classmethod
    def get_week_start(cls, checkin_date: datetime) -> datetime:
        """Get the start of the week for a given date (Monday)"""
        return checkin_date - timedelta(days=checkin_date.weekday())
    
    def get_week_start_date(self) -> datetime:
        """Get the start of the week for this checkin"""
        return self.get_week_start(self.checkin_date)
    
    def calculate_health_score(self) -> float:
        """Calculate a composite health score based on metrics"""
        score = 0.0
        factors = 0
        
        # Sleep quality (0-100 points)
        if self.sleep_hours is not None:
            if 7 <= self.sleep_hours <= 9:  # Optimal sleep range
                score += 100
            elif 6 <= self.sleep_hours <= 10:  # Acceptable range
                score += 80
            elif 5 <= self.sleep_hours <= 11:  # Borderline
                score += 60
            else:  # Too little or too much sleep
                score += 30
            factors += 1
        
        # Physical activity (0-100 points)
        if self.physical_activity_minutes is not None:
            if self.physical_activity_minutes >= 150:  # Recommended weekly minimum
                score += 100
            else:
                score += min(100, (self.physical_activity_minutes / 150) * 100)
            factors += 1
        
        # Stress level (inverted, lower is better)
        if self.stress_level is not None:
            stress_score = max(0, 10 - self.stress_level) * 10  # 0-100 scale
            score += stress_score
            factors += 1
        
        # Energy level
        if self.energy_level is not None:
            score += self.energy_level * 10  # 10-100 scale
            factors += 1
        
        # Mood rating
        if self.mood_rating is not None:
            score += self.mood_rating * 10  # 10-100 scale
            factors += 1
        
        # Relationships rating
        if self.relationships_rating is not None:
            score += self.relationships_rating * 10  # 10-100 scale
            factors += 1
        
        # Mindfulness (bonus points)
        if self.mindfulness_minutes is not None and self.mindfulness_minutes > 0:
            score += min(20, self.mindfulness_minutes)  # Up to 20 bonus points
            factors += 0.2  # Small factor to avoid over-weighting
        
        return score / factors if factors > 0 else 0.0 