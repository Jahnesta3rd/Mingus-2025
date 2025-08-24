"""
Article Library Analytics Models for Mingus Application

This module defines the SQLAlchemy models for storing comprehensive analytics data
for the article library system, including user engagement, article performance,
search behavior, and cultural relevance effectiveness.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.models.base import Base


class UserEngagementMetrics(Base):
    """Track detailed user engagement with article library"""
    __tablename__ = 'user_engagement_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(50), nullable=False)
    
    # Session metrics
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime)
    total_session_time = Column(Integer, default=0)  # seconds
    
    # Article interaction metrics
    articles_viewed = Column(Integer, default=0)
    articles_completed = Column(Integer, default=0)
    articles_bookmarked = Column(Integer, default=0)
    articles_shared = Column(Integer, default=0)
    
    # Search and discovery metrics
    search_queries_count = Column(Integer, default=0)
    search_success_rate = Column(Float, default=0.0)  # percentage
    recommendations_clicked = Column(Integer, default=0)
    
    # Assessment and progression metrics
    assessment_completed = Column(Boolean, default=False)
    be_score_change = Column(Integer, default=0)
    do_score_change = Column(Integer, default=0) 
    have_score_change = Column(Integer, default=0)
    content_unlocked_count = Column(Integer, default=0)
    
    # Cultural engagement metrics
    cultural_content_preference = Column(Float, default=0.0)  # 0-10 scale
    community_focused_articles_read = Column(Integer, default=0)
    
    # Device and context
    device_type = Column(String(20))  # mobile, desktop, tablet
    user_agent = Column(String(200))
    ip_location = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_engagement_user_session', 'user_id', 'session_id'),
        Index('idx_user_engagement_session_time', 'session_start', 'session_end'),
        Index('idx_user_engagement_assessment', 'assessment_completed', 'created_at'),
    )


class ArticlePerformanceMetrics(Base):
    """Track individual article performance and impact"""
    __tablename__ = 'article_performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Basic engagement metrics
    total_views = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)
    average_reading_time = Column(Float, default=0.0)  # seconds
    completion_rate = Column(Float, default=0.0)  # percentage
    
    # User interaction metrics
    bookmark_rate = Column(Float, default=0.0)  # bookmarks/views percentage
    share_rate = Column(Float, default=0.0)  # shares/views percentage
    rating_average = Column(Float, default=0.0)  # 1-5 star average
    rating_count = Column(Integer, default=0)
    
    # Cultural relevance performance
    cultural_engagement_score = Column(Float, default=0.0)  # how well it resonates
    demographic_reach = Column(JSON)  # breakdown by user demographics
    
    # Business impact metrics
    subscription_conversion_rate = Column(Float, default=0.0)  # reading to upgrade
    user_retention_impact = Column(Float, default=0.0)  # retention correlation
    
    # Content quality indicators
    bounce_rate = Column(Float, default=0.0)  # quick exits
    return_reader_rate = Column(Float, default=0.0)  # users who come back
    recommendation_click_rate = Column(Float, default=0.0)
    
    # Temporal metrics
    peak_reading_hours = Column(JSON)  # when article is most read
    seasonal_performance = Column(JSON)  # performance over time
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_article_performance_article', 'article_id'),
        Index('idx_article_performance_views', 'total_views', 'created_at'),
        Index('idx_article_performance_completion', 'completion_rate', 'created_at'),
        Index('idx_article_performance_cultural', 'cultural_engagement_score', 'created_at'),
    )


class SearchAnalytics(Base):
    """Track search behavior and effectiveness"""
    __tablename__ = 'search_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    search_query = Column(String(500), nullable=False)
    
    # Search context
    search_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    selected_phase = Column(String(10))  # BE/DO/HAVE filter
    cultural_relevance_filter = Column(Integer)  # minimum relevance
    
    # Search results
    results_count = Column(Integer, default=0)
    clicked_article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'))
    click_position = Column(Integer)  # position in results clicked
    
    # Search success metrics
    result_clicked = Column(Boolean, default=False)
    session_continued = Column(Boolean, default=False)  # stayed to explore more
    
    # Query analysis
    query_length = Column(Integer, default=0)
    query_type = Column(String(50))  # topic, author, specific_question, etc.
    cultural_keywords_present = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_search_analytics_user_time', 'user_id', 'search_timestamp'),
        Index('idx_search_analytics_query', 'search_query', 'search_timestamp'),
        Index('idx_search_analytics_phase', 'selected_phase', 'search_timestamp'),
        Index('idx_search_analytics_success', 'result_clicked', 'search_timestamp'),
    )


class CulturalRelevanceAnalytics(Base):
    """Track effectiveness of cultural personalization"""
    __tablename__ = 'cultural_relevance_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Cultural engagement patterns
    high_relevance_content_preference = Column(Float, default=0.0)  # 8+ score preference
    community_content_engagement = Column(Float, default=0.0)  # cultural keyword articles
    diverse_representation_response = Column(Float, default=0.0)  # response to diverse authors
    
    # Professional development cultural alignment
    corporate_navigation_interest = Column(Float, default=0.0)
    generational_wealth_focus = Column(Float, default=0.0) 
    systemic_barrier_awareness_content = Column(Float, default=0.0)
    
    # Content discovery through cultural lens
    cultural_search_terms_frequency = Column(Integer, default=0)
    cultural_recommendation_click_rate = Column(Float, default=0.0)
    
    # Impact measurements
    cultural_content_completion_rate = Column(Float, default=0.0)
    cultural_content_sharing_rate = Column(Float, default=0.0)
    cultural_content_return_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_calculated = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_cultural_analytics_user', 'user_id'),
        Index('idx_cultural_analytics_engagement', 'high_relevance_content_preference', 'created_at'),
        Index('idx_cultural_analytics_community', 'community_content_engagement', 'created_at'),
    )


class BeDoHaveTransformationAnalytics(Base):
    """Track user progression through Be-Do-Have transformation journey"""
    __tablename__ = 'be_do_have_transformation_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Current phase metrics
    current_phase = Column(String(10), nullable=False)  # BE, DO, HAVE
    phase_start_date = Column(DateTime, default=datetime.utcnow)
    phase_duration_days = Column(Integer, default=0)
    
    # Phase progression metrics
    be_phase_articles_read = Column(Integer, default=0)
    do_phase_articles_read = Column(Integer, default=0)
    have_phase_articles_read = Column(Integer, default=0)
    
    # Transformation indicators
    mindset_shift_indicators = Column(JSON)  # tracking mindset changes
    action_taking_metrics = Column(JSON)  # concrete actions taken
    wealth_building_progress = Column(JSON)  # financial progress indicators
    
    # Engagement by phase
    phase_engagement_scores = Column(JSON)  # engagement level per phase
    phase_completion_rates = Column(JSON)  # completion rates per phase
    phase_retention_rates = Column(JSON)  # return rates per phase
    
    # Cross-phase learning
    cross_phase_connections = Column(JSON)  # how users connect concepts across phases
    transformation_milestones = Column(JSON)  # key transformation moments
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_transformation_analytics_user', 'user_id'),
        Index('idx_transformation_analytics_phase', 'current_phase', 'created_at'),
        Index('idx_transformation_analytics_progression', 'phase_start_date', 'created_at'),
    )


class ContentGapAnalysis(Base):
    """Track content gaps and user needs"""
    __tablename__ = 'content_gap_analysis'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Gap identification
    gap_category = Column(String(100), nullable=False)  # topic, phase, cultural, etc.
    gap_description = Column(Text, nullable=False)
    gap_severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # User impact
    affected_user_count = Column(Integer, default=0)
    user_requests_count = Column(Integer, default=0)
    search_failure_rate = Column(Float, default=0.0)  # searches with no results
    
    # Content recommendations
    recommended_topics = Column(JSON)  # suggested topics to address gap
    recommended_authors = Column(JSON)  # suggested authors for content
    recommended_formats = Column(JSON)  # suggested content formats
    
    # Business impact
    potential_subscription_impact = Column(Float, default=0.0)
    potential_retention_impact = Column(Float, default=0.0)
    
    # Status tracking
    status = Column(String(20), default='identified')  # identified, in_progress, addressed
    priority_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    addressed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_content_gap_category', 'gap_category', 'gap_severity'),
        Index('idx_content_gap_status', 'status', 'priority_score'),
        Index('idx_content_gap_impact', 'affected_user_count', 'created_at'),
    )


class SystemPerformanceMetrics(Base):
    """Track system performance and API usage"""
    __tablename__ = 'system_performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # API performance
    endpoint_name = Column(String(100), nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_count = Column(Integer, default=1)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)
    
    # Resource usage
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_mb = Column(Float, default=0.0)
    database_connection_count = Column(Integer, default=0)
    
    # Cache performance
    cache_hit_rate = Column(Float, default=0.0)
    cache_miss_count = Column(Integer, default=0)
    
    # User load
    concurrent_users = Column(Integer, default=0)
    peak_concurrent_users = Column(Integer, default=0)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_performance_endpoint', 'endpoint_name', 'recorded_at'),
        Index('idx_system_performance_time', 'recorded_at'),
        Index('idx_system_performance_response_time', 'response_time_ms', 'recorded_at'),
    )


class A_BTestResults(Base):
    """Track A/B testing results for feature optimization"""
    __tablename__ = 'a_b_test_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Test configuration
    test_name = Column(String(100), nullable=False)
    test_variant = Column(String(50), nullable=False)  # A, B, C, etc.
    test_feature = Column(String(100), nullable=False)  # search_algorithm, ui_layout, etc.
    
    # User assignment
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Performance metrics
    engagement_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    retention_rate = Column(Float, default=0.0)
    satisfaction_score = Column(Float, default=0.0)
    
    # Feature-specific metrics
    feature_usage_count = Column(Integer, default=0)
    feature_completion_rate = Column(Float, default=0.0)
    feature_error_rate = Column(Float, default=0.0)
    
    # Statistical significance
    is_statistically_significant = Column(Boolean, default=False)
    confidence_level = Column(Float, default=0.0)
    p_value = Column(Float, default=1.0)
    
    # Test status
    test_status = Column(String(20), default='active')  # active, completed, paused
    winner_determined = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_ab_test_name_variant', 'test_name', 'test_variant'),
        Index('idx_ab_test_user', 'user_id', 'test_name'),
        Index('idx_ab_test_status', 'test_status', 'created_at'),
        Index('idx_ab_test_performance', 'engagement_rate', 'conversion_rate'),
    )
