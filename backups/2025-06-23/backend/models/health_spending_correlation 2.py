"""
Health spending correlation model for storing calculated correlations
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class HealthSpendingCorrelation(Base):
    __tablename__ = 'health_spending_correlations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Analysis metadata
    analysis_period = Column(String(50), nullable=False)  # weekly, monthly, quarterly, yearly
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)
    
    # Correlation details
    health_metric = Column(String(100), nullable=False)  # stress_level, energy_level, mood_rating, etc.
    spending_category = Column(String(100), nullable=False)  # food, entertainment, healthcare, etc.
    correlation_strength = Column(Float, nullable=False)  # -1.0 to 1.0
    correlation_direction = Column(String(20), nullable=False)  # positive, negative, none
    
    # Statistical details
    sample_size = Column(Integer, nullable=False)
    p_value = Column(Float)  # Statistical significance
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    
    # Insights and recommendations
    insight_text = Column(String(1000))
    recommendation_text = Column(String(1000))
    actionable_insight = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="health_correlations")
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure unique correlation per user, period, and metric combination
        Index('idx_user_period_metric', 'user_id', 'analysis_period', 'health_metric', 'spending_category'),
        # Index for efficient querying by correlation strength
        Index('idx_correlation_strength', 'correlation_strength'),
        # Index for actionable insights
        Index('idx_actionable_insights', 'actionable_insight', 'correlation_strength'),
        # Index for date range queries
        Index('idx_analysis_date_range', 'analysis_start_date', 'analysis_end_date'),
    )
    
    def __repr__(self):
        return f'<HealthSpendingCorrelation {self.user_id} {self.health_metric}->{self.spending_category}>'
    
    def get_correlation_interpretation(self) -> str:
        """Get human-readable interpretation of correlation strength"""
        abs_strength = abs(self.correlation_strength)
        
        if abs_strength >= 0.7:
            strength = "very strong"
        elif abs_strength >= 0.5:
            strength = "strong"
        elif abs_strength >= 0.3:
            strength = "moderate"
        elif abs_strength >= 0.1:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if self.correlation_strength > 0 else "negative"
        
        return f"{strength} {direction} correlation"
    
    def is_statistically_significant(self, alpha: float = 0.05) -> bool:
        """Check if correlation is statistically significant"""
        return self.p_value is not None and self.p_value < alpha
    
    def get_confidence_interval(self) -> tuple:
        """Get confidence interval as tuple"""
        return (self.confidence_interval_lower, self.confidence_interval_upper)
    
    def is_actionable(self) -> bool:
        """Determine if this correlation is actionable based on strength and significance"""
        return (
            self.actionable_insight and
            abs(self.correlation_strength) >= 0.3 and
            self.is_statistically_significant() and
            self.sample_size >= 10
        )
    
    def generate_insight_text(self) -> str:
        """Generate insight text based on correlation data"""
        if not self.is_actionable():
            return "Insufficient data for meaningful insights"
        
        direction = "increases" if self.correlation_strength > 0 else "decreases"
        strength_desc = self.get_correlation_interpretation()
        
        insight = f"When your {self.health_metric.replace('_', ' ')} {direction}, "
        insight += f"your {self.spending_category} spending tends to {direction} as well. "
        insight += f"This shows a {strength_desc}."
        
        if self.insight_text:
            insight += f" {self.insight_text}"
        
        return insight
    
    def generate_recommendation(self) -> str:
        """Generate actionable recommendation based on correlation"""
        if not self.is_actionable():
            return "Continue monitoring your health and spending patterns for more insights."
        
        if self.correlation_strength > 0:
            recommendation = f"Consider monitoring your {self.spending_category} spending "
            recommendation += f"when your {self.health_metric.replace('_', ' ')} is high, "
            recommendation += "as they may be related."
        else:
            recommendation = f"When your {self.health_metric.replace('_', ' ')} is low, "
            recommendation += f"you may spend more on {self.spending_category}. "
            recommendation += "Consider finding healthier alternatives."
        
        if self.recommendation_text:
            recommendation += f" {self.recommendation_text}"
        
        return recommendation 