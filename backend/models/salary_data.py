"""
SQLAlchemy Models for Real-time Salary Data Integration
Integrates with existing MINGUS PostgreSQL schema and Redis caching system
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Text, 
    UniqueConstraint, Index, ForeignKey, func, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func as sql_func

from ..database import Base
from ..utils.validators import validate_decimal_range, validate_confidence_score

class SalaryBenchmark(Base):
    """Model for salary benchmark data from multiple sources"""
    
    __tablename__ = 'salary_benchmarks'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core data fields
    location = Column(String(255), nullable=False, index=True)
    occupation = Column(String(255), nullable=False, index=True)
    industry = Column(String(255), index=True)
    experience_level = Column(String(50))  # Entry, Mid, Senior, Executive
    education_level = Column(String(50))   # High School, Bachelor's, Master's, PhD
    
    # Salary data
    median_salary = Column(DECIMAL(12,2), nullable=False, index=True)
    mean_salary = Column(DECIMAL(12,2))
    percentile_25 = Column(DECIMAL(12,2))
    percentile_75 = Column(DECIMAL(12,2))
    percentile_90 = Column(DECIMAL(12,2))
    
    # Sample and confidence data
    sample_size = Column(Integer)
    confidence_interval_lower = Column(DECIMAL(12,2))
    confidence_interval_upper = Column(DECIMAL(12,2))
    
    # Data source information
    data_source = Column(String(50), nullable=False, index=True)  # BLS, Census, Indeed, etc.
    source_confidence_score = Column(DECIMAL(3,2), default=0.0)
    data_freshness_days = Column(Integer)
    
    # Temporal data
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer)  # Q1, Q2, Q3, Q4
    
    # Cache and metadata
    cache_key = Column(String(255), index=True)
    metadata = Column(JSONB, index=True)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    created_at = Column(DateTime(timezone=True), default=sql_func.now())
    updated_at = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    
    # Relationships
    confidence_scores = relationship("ConfidenceScore", back_populates="salary_benchmark")
    cache_entries = relationship("SalaryDataCache", back_populates="salary_benchmark")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'location', 'occupation', 'industry', 'experience_level', 
            'education_level', 'year', 'quarter', 'data_source',
            name='uq_salary_benchmarks_composite'
        ),
        Index('idx_salary_benchmarks_location_occupation', 'location', 'occupation'),
        Index('idx_salary_benchmarks_location_industry', 'location', 'industry'),
        Index('idx_salary_benchmarks_metadata_gin', 'metadata', postgresql_using='gin'),
    )
    
    @validates('median_salary')
    def validate_median_salary(self, key, value):
        """Validate median salary is positive"""
        if value is not None and value <= 0:
            raise ValueError("Median salary must be positive")
        return value
    
    @validates('source_confidence_score')
    def validate_source_confidence_score(self, key, value):
        """Validate confidence score is between 0 and 1"""
        return validate_confidence_score(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': str(self.id),
            'location': self.location,
            'occupation': self.occupation,
            'industry': self.industry,
            'experience_level': self.experience_level,
            'education_level': self.education_level,
            'median_salary': float(self.median_salary) if self.median_salary else None,
            'mean_salary': float(self.mean_salary) if self.mean_salary else None,
            'percentile_25': float(self.percentile_25) if self.percentile_25 else None,
            'percentile_75': float(self.percentile_75) if self.percentile_75 else None,
            'percentile_90': float(self.percentile_90) if self.percentile_90 else None,
            'sample_size': self.sample_size,
            'confidence_interval_lower': float(self.confidence_interval_lower) if self.confidence_interval_lower else None,
            'confidence_interval_upper': float(self.confidence_interval_upper) if self.confidence_interval_upper else None,
            'data_source': self.data_source,
            'source_confidence_score': float(self.source_confidence_score) if self.source_confidence_score else None,
            'data_freshness_days': self.data_freshness_days,
            'year': self.year,
            'quarter': self.quarter,
            'cache_key': self.cache_key,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SalaryBenchmark(id={self.id}, location='{self.location}', occupation='{self.occupation}', median_salary={self.median_salary})>"

class MarketData(Base):
    """Model for job market and economic data"""
    
    __tablename__ = 'market_data'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core data fields
    location = Column(String(255), nullable=False, index=True)
    occupation = Column(String(255), index=True)
    industry = Column(String(255), index=True)
    
    # Job market indicators
    job_count = Column(Integer)
    job_growth_rate = Column(DECIMAL(5,2))  # Annual growth percentage
    unemployment_rate = Column(DECIMAL(5,2))  # Local unemployment rate
    labor_force_participation = Column(DECIMAL(5,2))  # Labor force participation rate
    
    # Economic indicators
    cost_of_living_index = Column(DECIMAL(8,2))  # Relative to national average (100)
    housing_cost_index = Column(DECIMAL(8,2))
    transportation_cost_index = Column(DECIMAL(8,2))
    healthcare_cost_index = Column(DECIMAL(8,2))
    
    # Demand and supply metrics
    demand_score = Column(DECIMAL(3,2), default=0.0, index=True)
    supply_score = Column(DECIMAL(3,2), default=0.0)
    market_balance_score = Column(DECIMAL(3,2), default=0.0)
    
    # Remote work and flexibility
    remote_work_percentage = Column(DECIMAL(5,2))  # % of jobs offering remote work
    hybrid_work_percentage = Column(DECIMAL(5,2))  # % of jobs offering hybrid work
    
    # Data source and quality
    data_source = Column(String(50), nullable=False, index=True)
    source_confidence_score = Column(DECIMAL(3,2), default=0.0)
    data_freshness_days = Column(Integer)
    
    # Temporal data
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer)  # 1-12
    quarter = Column(Integer)  # 1-4
    
    # Cache and metadata
    cache_key = Column(String(255), index=True)
    metadata = Column(JSONB, index=True)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    created_at = Column(DateTime(timezone=True), default=sql_func.now())
    updated_at = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    
    # Relationships
    confidence_scores = relationship("ConfidenceScore", back_populates="market_data")
    cache_entries = relationship("SalaryDataCache", back_populates="market_data")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'location', 'occupation', 'industry', 'year', 'month', 'quarter', 'data_source',
            name='uq_market_data_composite'
        ),
        Index('idx_market_data_location_occupation', 'location', 'occupation'),
        Index('idx_market_data_metadata_gin', 'metadata', postgresql_using='gin'),
    )
    
    @validates('demand_score', 'supply_score', 'market_balance_score', 'source_confidence_score')
    def validate_scores(self, key, value):
        """Validate scores are between 0 and 1"""
        return validate_confidence_score(value)
    
    @validates('job_growth_rate', 'unemployment_rate', 'labor_force_participation')
    def validate_percentages(self, key, value):
        """Validate percentage values are reasonable"""
        if value is not None and (value < -100 or value > 100):
            raise ValueError(f"{key} must be between -100 and 100")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': str(self.id),
            'location': self.location,
            'occupation': self.occupation,
            'industry': self.industry,
            'job_count': self.job_count,
            'job_growth_rate': float(self.job_growth_rate) if self.job_growth_rate else None,
            'unemployment_rate': float(self.unemployment_rate) if self.unemployment_rate else None,
            'labor_force_participation': float(self.labor_force_participation) if self.labor_force_participation else None,
            'cost_of_living_index': float(self.cost_of_living_index) if self.cost_of_living_index else None,
            'housing_cost_index': float(self.housing_cost_index) if self.housing_cost_index else None,
            'transportation_cost_index': float(self.transportation_cost_index) if self.transportation_cost_index else None,
            'healthcare_cost_index': float(self.healthcare_cost_index) if self.healthcare_cost_index else None,
            'demand_score': float(self.demand_score) if self.demand_score else None,
            'supply_score': float(self.supply_score) if self.supply_score else None,
            'market_balance_score': float(self.market_balance_score) if self.market_balance_score else None,
            'remote_work_percentage': float(self.remote_work_percentage) if self.remote_work_percentage else None,
            'hybrid_work_percentage': float(self.hybrid_work_percentage) if self.hybrid_work_percentage else None,
            'data_source': self.data_source,
            'source_confidence_score': float(self.source_confidence_score) if self.source_confidence_score else None,
            'data_freshness_days': self.data_freshness_days,
            'year': self.year,
            'month': self.month,
            'quarter': self.quarter,
            'cache_key': self.cache_key,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<MarketData(id={self.id}, location='{self.location}', job_count={self.job_count}, demand_score={self.demand_score})>"

class ConfidenceScore(Base):
    """Model for data quality and reliability metrics"""
    
    __tablename__ = 'confidence_scores'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core data fields
    data_type = Column(String(50), nullable=False, index=True)  # 'salary', 'market', 'cost_of_living'
    location = Column(String(255), nullable=False, index=True)
    occupation = Column(String(255), index=True)
    industry = Column(String(255), index=True)
    
    # Confidence scoring components
    sample_size_score = Column(DECIMAL(3,2), default=0.0)
    data_freshness_score = Column(DECIMAL(3,2), default=0.0)
    source_reliability_score = Column(DECIMAL(3,2), default=0.0)
    methodology_score = Column(DECIMAL(3,2), default=0.0)
    consistency_score = Column(DECIMAL(3,2), default=0.0)
    
    # Composite scores
    overall_confidence_score = Column(DECIMAL(3,2), default=0.0, index=True)
    data_quality_score = Column(DECIMAL(3,2), default=0.0)
    reliability_score = Column(DECIMAL(3,2), default=0.0)
    
    # Scoring metadata
    scoring_methodology = Column(JSONB)
    contributing_sources = Column(JSONB)
    last_calculated = Column(DateTime(timezone=True), default=sql_func.now())
    
    # Temporal data
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer)
    
    # Cache and metadata
    cache_key = Column(String(255), index=True)
    metadata = Column(JSONB, index=True)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    created_at = Column(DateTime(timezone=True), default=sql_func.now())
    updated_at = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    
    # Relationships
    salary_benchmark = relationship("SalaryBenchmark", back_populates="confidence_scores")
    market_data = relationship("MarketData", back_populates="confidence_scores")
    cache_entries = relationship("SalaryDataCache", back_populates="confidence_score")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'data_type', 'location', 'occupation', 'industry', 'year', 'quarter',
            name='uq_confidence_scores_composite'
        ),
        Index('idx_confidence_scores_location_data_type', 'location', 'data_type'),
        Index('idx_confidence_scores_metadata_gin', 'metadata', postgresql_using='gin'),
    )
    
    @validates('sample_size_score', 'data_freshness_score', 'source_reliability_score', 
               'methodology_score', 'consistency_score', 'overall_confidence_score', 
               'data_quality_score', 'reliability_score')
    def validate_scores(self, key, value):
        """Validate all scores are between 0 and 1"""
        return validate_confidence_score(value)
    
    def calculate_overall_confidence(self):
        """Calculate overall confidence score from component scores"""
        weights = {
            'sample_size_score': 0.25,
            'data_freshness_score': 0.25,
            'source_reliability_score': 0.2,
            'methodology_score': 0.2,
            'consistency_score': 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for component, weight in weights.items():
            value = getattr(self, component, 0.0)
            if value is not None:
                total_score += float(value) * weight
                total_weight += weight
        
        if total_weight > 0:
            self.overall_confidence_score = Decimal(str(min(max(total_score / total_weight, 0.0), 1.0)))
        
        return self.overall_confidence_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': str(self.id),
            'data_type': self.data_type,
            'location': self.location,
            'occupation': self.occupation,
            'industry': self.industry,
            'sample_size_score': float(self.sample_size_score) if self.sample_size_score else None,
            'data_freshness_score': float(self.data_freshness_score) if self.data_freshness_score else None,
            'source_reliability_score': float(self.source_reliability_score) if self.source_reliability_score else None,
            'methodology_score': float(self.methodology_score) if self.methodology_score else None,
            'consistency_score': float(self.consistency_score) if self.consistency_score else None,
            'overall_confidence_score': float(self.overall_confidence_score) if self.overall_confidence_score else None,
            'data_quality_score': float(self.data_quality_score) if self.data_quality_score else None,
            'reliability_score': float(self.reliability_score) if self.reliability_score else None,
            'scoring_methodology': self.scoring_methodology,
            'contributing_sources': self.contributing_sources,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'year': self.year,
            'quarter': self.quarter,
            'cache_key': self.cache_key,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<ConfidenceScore(id={self.id}, data_type='{self.data_type}', location='{self.location}', overall_confidence={self.overall_confidence_score})>"

class SalaryDataCache(Base):
    """Model for tracking Redis cache performance and metadata"""
    
    __tablename__ = 'salary_data_cache'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Cache identification
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)  # 'salary', 'market', 'confidence'
    
    # Cache management
    redis_key = Column(String(255), nullable=False)  # Actual Redis key
    ttl_seconds = Column(Integer, default=86400)  # Time to live in seconds
    cache_hits = Column(Integer, default=0)  # Number of cache hits
    cache_misses = Column(Integer, default=0)  # Number of cache misses
    last_accessed = Column(DateTime(timezone=True), index=True)
    
    # Data metadata
    data_size_bytes = Column(Integer)  # Size of cached data
    compression_ratio = Column(DECIMAL(5,2))  # If data is compressed
    cache_strategy = Column(String(50), default='standard')  # 'standard', 'aggressive', 'conservative'
    
    # Performance metrics
    average_response_time_ms = Column(Integer)  # Average time to retrieve from cache
    hit_rate = Column(DECIMAL(5,2))  # Hit rate percentage
    
    # Management
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    metadata = Column(JSONB, index=True)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), default=sql_func.now(), onupdate=sql_func.now())
    created_at = Column(DateTime(timezone=True), default=sql_func.now())
    
    # Relationships
    salary_benchmark = relationship("SalaryBenchmark", back_populates="cache_entries")
    market_data = relationship("MarketData", back_populates="cache_entries")
    confidence_score = relationship("ConfidenceScore", back_populates="cache_entries")
    
    # Constraints
    __table_args__ = (
        Index('idx_salary_data_cache_metadata_gin', 'metadata', postgresql_using='gin'),
    )
    
    @validates('compression_ratio', 'hit_rate')
    def validate_percentages(self, key, value):
        """Validate percentage values are between 0 and 100"""
        if value is not None and (value < 0 or value > 100):
            raise ValueError(f"{key} must be between 0 and 100")
        return value
    
    def update_hit_rate(self):
        """Calculate and update hit rate"""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests > 0:
            self.hit_rate = Decimal(str((self.cache_hits / total_requests) * 100))
        else:
            self.hit_rate = Decimal('0.0')
    
    def increment_hit(self):
        """Increment cache hit counter"""
        self.cache_hits += 1
        self.last_accessed = datetime.utcnow()
        self.update_hit_rate()
    
    def increment_miss(self):
        """Increment cache miss counter"""
        self.cache_misses += 1
        self.last_accessed = datetime.utcnow()
        self.update_hit_rate()
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': str(self.id),
            'cache_key': self.cache_key,
            'data_type': self.data_type,
            'redis_key': self.redis_key,
            'ttl_seconds': self.ttl_seconds,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'data_size_bytes': self.data_size_bytes,
            'compression_ratio': float(self.compression_ratio) if self.compression_ratio else None,
            'cache_strategy': self.cache_strategy,
            'average_response_time_ms': self.average_response_time_ms,
            'hit_rate': float(self.hit_rate) if self.hit_rate else None,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<SalaryDataCache(id={self.id}, cache_key='{self.cache_key}', hit_rate={self.hit_rate}%)>" 