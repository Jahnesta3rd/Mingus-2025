"""
Salary Data Models for MINGUS
Handles salary information and compensation data
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, DECIMAL, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base
from typing import Optional, List
from decimal import Decimal

class SalaryBenchmark(Base):
    """Model for salary benchmark data"""
    __tablename__ = 'salary_benchmarks'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), nullable=False, index=True)
    occupation = Column(String(200), nullable=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # BLS, Census, FRED, Indeed, Fallback
    median_salary = Column(DECIMAL(10, 2), nullable=False)
    mean_salary = Column(DECIMAL(10, 2), nullable=False)
    percentile_25 = Column(DECIMAL(10, 2), nullable=False)
    percentile_75 = Column(DECIMAL(10, 2), nullable=False)
    sample_size = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=False, index=True)
    data_quality_score = Column(DECIMAL(3, 2), nullable=True)
    validation_level = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW, INVALID
    outliers_detected = Column(Integer, nullable=True)
    cache_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SalaryBenchmark(location='{self.location}', occupation='{self.occupation}', source='{self.source}', median_salary={self.median_salary})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'location': self.location,
            'occupation': self.occupation,
            'source': self.source,
            'median_salary': float(self.median_salary) if self.median_salary else None,
            'mean_salary': float(self.mean_salary) if self.mean_salary else None,
            'percentile_25': float(self.percentile_25) if self.percentile_25 else None,
            'percentile_75': float(self.percentile_75) if self.percentile_75 else None,
            'sample_size': self.sample_size,
            'year': self.year,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'data_quality_score': float(self.data_quality_score) if self.data_quality_score else None,
            'validation_level': self.validation_level,
            'outliers_detected': self.outliers_detected,
            'cache_key': self.cache_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MarketData(Base):
    """Model for market data (cost of living and job market)"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), nullable=False, index=True)
    occupation = Column(String(200), nullable=True, index=True)
    data_type = Column(String(50), nullable=False, index=True)  # cost_of_living, job_market
    overall_cost_index = Column(DECIMAL(5, 2), nullable=True)
    housing_cost_index = Column(DECIMAL(5, 2), nullable=True)
    transportation_cost_index = Column(DECIMAL(5, 2), nullable=True)
    food_cost_index = Column(DECIMAL(5, 2), nullable=True)
    healthcare_cost_index = Column(DECIMAL(5, 2), nullable=True)
    utilities_cost_index = Column(DECIMAL(5, 2), nullable=True)
    job_count = Column(Integer, nullable=True)
    average_salary = Column(DECIMAL(10, 2), nullable=True)
    salary_range_min = Column(DECIMAL(10, 2), nullable=True)
    salary_range_max = Column(DECIMAL(10, 2), nullable=True)
    demand_score = Column(DECIMAL(5, 2), nullable=True)
    year = Column(Integer, nullable=False, index=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=False)
    data_quality_score = Column(DECIMAL(3, 2), nullable=True)
    validation_level = Column(String(20), nullable=True)
    cache_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketData(location='{self.location}', data_type='{self.data_type}', year={self.year})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'location': self.location,
            'occupation': self.occupation,
            'data_type': self.data_type,
            'overall_cost_index': float(self.overall_cost_index) if self.overall_cost_index else None,
            'housing_cost_index': float(self.housing_cost_index) if self.housing_cost_index else None,
            'transportation_cost_index': float(self.transportation_cost_index) if self.transportation_cost_index else None,
            'food_cost_index': float(self.food_cost_index) if self.food_cost_index else None,
            'healthcare_cost_index': float(self.healthcare_cost_index) if self.healthcare_cost_index else None,
            'utilities_cost_index': float(self.utilities_cost_index) if self.utilities_cost_index else None,
            'job_count': self.job_count,
            'average_salary': float(self.average_salary) if self.average_salary else None,
            'salary_range_min': float(self.salary_range_min) if self.salary_range_min else None,
            'salary_range_max': float(self.salary_range_max) if self.salary_range_max else None,
            'demand_score': float(self.demand_score) if self.demand_score else None,
            'year': self.year,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'data_quality_score': float(self.data_quality_score) if self.data_quality_score else None,
            'validation_level': self.validation_level,
            'cache_key': self.cache_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ConfidenceScore(Base):
    """Model for confidence scores and data quality metrics"""
    __tablename__ = 'confidence_scores'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), nullable=False, index=True)
    occupation = Column(String(200), nullable=True, index=True)
    overall_confidence_score = Column(DECIMAL(3, 2), nullable=False, index=True)
    data_quality_score = Column(DECIMAL(3, 2), nullable=False, index=True)
    salary_data_confidence = Column(DECIMAL(3, 2), nullable=True)
    cost_of_living_confidence = Column(DECIMAL(3, 2), nullable=True)
    job_market_confidence = Column(DECIMAL(3, 2), nullable=True)
    validation_issues_count = Column(Integer, nullable=True)
    validation_warnings_count = Column(Integer, nullable=True)
    outliers_count = Column(Integer, nullable=True)
    data_sources_count = Column(Integer, nullable=True)
    last_validation_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ConfidenceScore(location='{self.location}', overall_confidence={self.overall_confidence_score})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'location': self.location,
            'occupation': self.occupation,
            'overall_confidence_score': float(self.overall_confidence_score) if self.overall_confidence_score else None,
            'data_quality_score': float(self.data_quality_score) if self.data_quality_score else None,
            'salary_data_confidence': float(self.salary_data_confidence) if self.salary_data_confidence else None,
            'cost_of_living_confidence': float(self.cost_of_living_confidence) if self.cost_of_living_confidence else None,
            'job_market_confidence': float(self.job_market_confidence) if self.job_market_confidence else None,
            'validation_issues_count': self.validation_issues_count,
            'validation_warnings_count': self.validation_warnings_count,
            'outliers_count': self.outliers_count,
            'data_sources_count': self.data_sources_count,
            'last_validation_at': self.last_validation_at.isoformat() if self.last_validation_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DataRefreshLog(Base):
    """Model for tracking background task execution"""
    __tablename__ = 'data_refresh_logs'
    
    id = Column(Integer, primary_key=True)
    task_type = Column(String(50), nullable=False, index=True)  # refresh_all, refresh_location, validate, cleanup
    location = Column(String(100), nullable=True)
    occupation = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, index=True)  # started, completed, failed
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    records_processed = Column(Integer, nullable=True)
    records_updated = Column(Integer, nullable=True)
    errors_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return f"<DataRefreshLog(task_type='{self.task_type}', status='{self.status}', started_at={self.started_at})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'location': self.location,
            'occupation': self.occupation,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'records_processed': self.records_processed,
            'records_updated': self.records_updated,
            'errors_count': self.errors_count,
            'error_message': self.error_message,
            'celery_task_id': self.celery_task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CacheMetric(Base):
    """Model for Redis cache monitoring metrics"""
    __tablename__ = 'cache_metrics'
    
    id = Column(Integer, primary_key=True)
    cache_key_pattern = Column(String(255), nullable=False, index=True)
    hits = Column(Integer, nullable=False, default=0)
    misses = Column(Integer, nullable=False, default=0)
    hit_rate = Column(DECIMAL(5, 4), nullable=True, index=True)
    avg_response_time_ms = Column(DECIMAL(8, 2), nullable=True)
    total_size_bytes = Column(Integer, nullable=True)
    entries_count = Column(Integer, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CacheMetric(pattern='{self.cache_key_pattern}', hit_rate={self.hit_rate})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'cache_key_pattern': self.cache_key_pattern,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': float(self.hit_rate) if self.hit_rate else None,
            'avg_response_time_ms': float(self.avg_response_time_ms) if self.avg_response_time_ms else None,
            'total_size_bytes': self.total_size_bytes,
            'entries_count': self.entries_count,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 