"""
Job Security Analysis Database Models
Stores historical score tracking, confidence levels, risk factors, and recommendations
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Text, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class JobSecurityAnalysis(Base):
    """Main job security analysis table for historical score tracking"""
    __tablename__ = 'job_security_analysis'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Analysis metadata
    analysis_date = Column(DateTime, nullable=False, index=True)
    employer_name = Column(String(255))
    industry_sector = Column(String(100))
    location = Column(String(100))
    
    # Core scores (0-100)
    overall_score = Column(Float, nullable=False)
    user_perception_score = Column(Float, nullable=False)
    external_data_score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)  # 0-100 confidence in analysis
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False)  # low, medium, high, very_high
    layoff_probability_6m = Column(Float)  # 0-1 probability
    
    # Detailed analysis data
    risk_factors = Column(JSON)  # Array of risk factor objects
    positive_indicators = Column(JSON)  # Array of positive indicators
    recommendations = Column(JSON)  # Array of recommendation objects
    
    # Trend data
    score_change = Column(Float)  # Change from previous analysis
    trend_direction = Column(String(10))  # up, down, stable
    
    # Integration data
    subscription_tier = Column(String(50))  # free, premium, enterprise
    analysis_version = Column(String(20))  # ML model version used
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_security_analyses")
    risk_factors_detail = relationship("JobSecurityRiskFactor", back_populates="analysis")
    recommendations_detail = relationship("JobSecurityRecommendation", back_populates="analysis")
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure one analysis per user per day
        UniqueConstraint('user_id', 'analysis_date', name='uq_user_daily_analysis'),
        # Index for efficient querying by user and date range
        Index('idx_job_security_user_date', 'user_id', 'analysis_date'),
        # Index for risk level analysis
        Index('idx_job_security_risk_level', 'risk_level', 'analysis_date'),
        # Index for subscription tier analysis
        Index('idx_job_security_subscription', 'subscription_tier', 'analysis_date'),
    )
    
    def __repr__(self):
        return f'<JobSecurityAnalysis {self.user_id} {self.analysis_date}>'

class JobSecurityRiskFactor(Base):
    """Detailed risk factors for job security analysis"""
    __tablename__ = 'job_security_risk_factors'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('job_security_analysis.id'), nullable=False)
    
    # Risk factor details
    category = Column(String(100), nullable=False)  # e.g., "Local Layoffs", "Company Financials"
    severity = Column(String(20), nullable=False)  # low, medium, high
    description = Column(Text, nullable=False)
    impact_score = Column(Float, nullable=False)  # 0-100 impact on overall score
    
    # Additional metadata
    source = Column(String(50))  # user_input, external_data, ml_prediction
    confidence = Column(Float)  # 0-100 confidence in this factor
    data_points = Column(JSON)  # Supporting data for the factor
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("JobSecurityAnalysis", back_populates="risk_factors_detail")
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_factor_category', 'category', 'severity'),
        Index('idx_risk_factor_analysis', 'analysis_id', 'impact_score'),
    )
    
    def __repr__(self):
        return f'<JobSecurityRiskFactor {self.category} {self.severity}>'

class JobSecurityRecommendation(Base):
    """Personalized recommendations for job security improvement"""
    __tablename__ = 'job_security_recommendations'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('job_security_analysis.id'), nullable=False)
    
    # Recommendation details
    priority = Column(String(20), nullable=False)  # high, medium, low
    category = Column(String(100), nullable=False)  # Career Development, Financial Planning, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    action_items = Column(JSON)  # Array of specific action items
    
    # Personalization data
    personalization_score = Column(Float)  # 0-100 relevance to user
    estimated_impact = Column(Float)  # 0-100 potential impact on job security
    time_to_implement = Column(String(50))  # e.g., "1-2 weeks", "1-3 months"
    
    # User interaction tracking
    is_dismissed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("JobSecurityAnalysis", back_populates="recommendations_detail")
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_priority', 'priority', 'personalization_score'),
        Index('idx_recommendation_category', 'category', 'analysis_id'),
        Index('idx_recommendation_status', 'is_dismissed', 'is_completed'),
    )
    
    def __repr__(self):
        return f'<JobSecurityRecommendation {self.title} {self.priority}>'

class ExternalDataCache(Base):
    """Cache for external data sources with TTL management"""
    __tablename__ = 'external_data_cache'
    
    id = Column(Integer, primary_key=True)
    
    # Cache key and data
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    data_type = Column(String(50), nullable=False)  # employer_financial, labor_market, warn_notices, bls_data
    data_source = Column(String(100), nullable=False)  # API endpoint or data source
    
    # Cached data
    cached_data = Column(JSON, nullable=False)
    data_hash = Column(String(64))  # For change detection
    
    # TTL management
    ttl_seconds = Column(Integer, nullable=False)  # Time to live in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    
    # Metadata
    is_valid = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_data_type', 'data_type', 'expires_at'),
        Index('idx_cache_access', 'last_accessed', 'access_count'),
        Index('idx_cache_validity', 'is_valid', 'expires_at'),
    )
    
    def __repr__(self):
        return f'<ExternalDataCache {self.data_type} {self.cache_key}>'
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def should_refresh(self) -> bool:
        """Check if cache entry should be refreshed based on TTL"""
        return datetime.utcnow() > self.expires_at 