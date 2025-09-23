#!/usr/bin/env python3
"""
Content Optimization Database Models
Database schema and models for A/B testing and content optimization
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class TestStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestType(Enum):
    CONTENT_FORMAT = "content_format"
    TIMING_OPTIMIZATION = "timing_optimization"
    PERSONALIZATION_DEPTH = "personalization_depth"
    CALL_TO_ACTION = "call_to_action"
    INSIGHT_TYPE = "insight_type"
    ENCOURAGEMENT_STYLE = "encouragement_style"

class VariantType(Enum):
    CONTROL = "control"
    VARIANT = "variant"

class MetricType(Enum):
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REVENUE = "revenue"
    CLICK_THROUGH = "click_through"
    TIME_SPENT = "time_spent"

class ABTest(Base):
    """A/B Test configuration and metadata"""
    __tablename__ = 'ab_tests'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(String(100), unique=True, nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(50), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default='draft')
    variants = Column(JSON, nullable=False)
    target_segments = Column(JSON, nullable=False)
    success_metrics = Column(JSON, nullable=False)
    duration_days = Column(Integer, default=14)
    traffic_allocation = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    user_assignments = relationship("UserAssignment", back_populates="test")
    interactions = relationship("TestInteraction", back_populates="test")
    metrics = relationship("VariantMetric", back_populates="test")

class UserAssignment(Base):
    """User assignments to test variants"""
    __tablename__ = 'user_assignments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'), nullable=False)
    variant_id = Column(String(100), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    test = relationship("ABTest", back_populates="user_assignments")
    user = relationship("User")

class TestInteraction(Base):
    """User interactions with test content"""
    __tablename__ = 'test_interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'), nullable=False)
    variant_id = Column(String(100), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    interaction_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship("ABTest", back_populates="interactions")
    user = relationship("User")

class VariantMetric(Base):
    """Performance metrics for test variants"""
    __tablename__ = 'variant_metrics'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'), nullable=False)
    variant_id = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    sample_size = Column(Integer, default=0)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    p_value = Column(Float)
    effect_size = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship("ABTest", back_populates="metrics")

class ContentTemplate(Base):
    """Content templates for A/B testing"""
    __tablename__ = 'content_templates'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(String(100), unique=True, nullable=False)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)
    content_config = Column(JSON, nullable=False)
    tier_restrictions = Column(JSON)
    segment_restrictions = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class TestResult(Base):
    """Statistical analysis results for completed tests"""
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'), nullable=False)
    winner_variant = Column(String(100))
    is_statistically_significant = Column(Boolean, default=False)
    confidence_level = Column(Float, default=0.95)
    effect_size = Column(Float)
    p_value = Column(Float)
    statistical_power = Column(Float)
    recommendations = Column(JSON)
    analysis_notes = Column(Text)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship("ABTest")

class UserSegment(Base):
    """User segmentation definitions"""
    __tablename__ = 'user_segments'
    
    id = Column(Integer, primary_key=True)
    segment_id = Column(String(100), unique=True, nullable=False)
    segment_name = Column(String(200), nullable=False)
    criteria = Column(JSON, nullable=False)
    description = Column(Text)
    user_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class ContentVariation(Base):
    """Content variations for testing"""
    __tablename__ = 'content_variations'
    
    id = Column(Integer, primary_key=True)
    variation_id = Column(String(100), unique=True, nullable=False)
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'), nullable=False)
    variant_id = Column(String(100), nullable=False)
    content_type = Column(String(50), nullable=False)
    content_data = Column(JSON, nullable=False)
    weight = Column(Float, default=0.5)
    is_control = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship("ABTest")

class PerformanceThreshold(Base):
    """Performance thresholds for automated optimization"""
    __tablename__ = 'performance_thresholds'
    
    id = Column(Integer, primary_key=True)
    threshold_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # '>', '<', '>=', '<=', '=='
    action_type = Column(String(50), nullable=False)  # 'pause_test', 'end_test', 'alert'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class OptimizationRule(Base):
    """Automated optimization rules"""
    __tablename__ = 'optimization_rules'
    
    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ContentPerformance(Base):
    """Historical content performance data"""
    __tablename__ = 'content_performance'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(String(100), nullable=False)
    content_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    variant_id = Column(String(100))
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'))
    engagement_score = Column(Float)
    conversion_rate = Column(Float)
    time_spent = Column(Integer)  # seconds
    click_through_rate = Column(Float)
    revenue_impact = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship("ABTest")
    user = relationship("User")

class AnalyticsEvent(Base):
    """Analytics events for A/B testing"""
    __tablename__ = 'analytics_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    test_id = Column(String(100), ForeignKey('ab_tests.test_id'))
    variant_id = Column(String(100))
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100))
    
    # Relationships
    test = relationship("ABTest")
    user = relationship("User")

# Database schema creation script
def create_content_optimization_schema():
    """Create the content optimization database schema"""
    from sqlalchemy import create_engine
    from backend.config.database import DATABASE_URL
    
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    
    print("Content optimization database schema created successfully")

# Indexes for performance optimization
def create_indexes():
    """Create database indexes for performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_user_assignments_user_test ON user_assignments(user_id, test_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_assignments_test_variant ON user_assignments(test_id, variant_id)",
        "CREATE INDEX IF NOT EXISTS idx_test_interactions_user_test ON test_interactions(user_id, test_id)",
        "CREATE INDEX IF NOT EXISTS idx_test_interactions_test_variant ON test_interactions(test_id, variant_id)",
        "CREATE INDEX IF NOT EXISTS idx_test_interactions_timestamp ON test_interactions(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_variant_metrics_test_variant ON variant_metrics(test_id, variant_id)",
        "CREATE INDEX IF NOT EXISTS idx_content_performance_date ON content_performance(date)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_user_test ON analytics_events(user_id, test_id)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp)"
    ]
    
    return indexes
