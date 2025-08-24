"""
Income Comparison Database Models
Comprehensive models for salary benchmarking, predictions, lead capture, and analytics
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import enum
from datetime import datetime, timedelta
from .base import Base


class ExperienceLevel(enum.Enum):
    """Experience level enumeration"""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"


class EducationLevel(enum.Enum):
    """Education level enumeration"""
    HIGH_SCHOOL = "high-school"
    SOME_COLLEGE = "some-college"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"


class IndustryType(enum.Enum):
    """Industry type enumeration"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    CONSULTING = "consulting"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    MEDIA = "media"


class BadgeType(enum.Enum):
    """Gamification badge types"""
    SALARY_INSIGHT = "salary_insight"
    CAREER_PLANNER = "career_planner"
    MARKET_EXPERT = "market_expert"
    GOAL_SETTER = "goal_setter"
    SKILL_DEVELOPER = "skill_developer"
    NETWORK_BUILDER = "network_builder"
    DATA_DRIVEN = "data_driven"
    PROGRESS_MAKER = "progress_maker"


class EmailSequenceType(enum.Enum):
    """Email sequence types"""
    WELCOME = "welcome"
    SALARY_INSIGHTS = "salary_insights"
    CAREER_PLANNING = "career_planning"
    SKILL_DEVELOPMENT = "skill_development"
    MARKET_UPDATES = "market_updates"
    RE_ENGAGEMENT = "re_engagement"


class SalaryBenchmark(Base):
    """Salary benchmark data from external APIs"""
    __tablename__ = 'salary_benchmarks'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), nullable=False, index=True)
    industry = Column(Enum(IndustryType), nullable=False, index=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=False, index=True)
    education_level = Column(Enum(EducationLevel), nullable=False, index=True)
    job_title = Column(String(200), nullable=True)
    
    # Salary data
    mean_salary = Column(Float, nullable=False)
    median_salary = Column(Float, nullable=False)
    percentile_25 = Column(Float, nullable=False)
    percentile_75 = Column(Float, nullable=False)
    percentile_90 = Column(Float, nullable=False)
    
    # Metadata
    sample_size = Column(Integer, nullable=False)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    data_source = Column(String(50), nullable=False, default='BLS')
    last_updated = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Additional context
    market_conditions = Column(JSON, nullable=True)  # Economic indicators
    demographic_data = Column(JSON, nullable=True)   # Population data
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('location', 'industry', 'experience_level', 'education_level', 'job_title', 
                        name='uq_salary_benchmark'),
        CheckConstraint('mean_salary > 0', name='ck_mean_salary_positive'),
        CheckConstraint('median_salary > 0', name='ck_median_salary_positive'),
        CheckConstraint('sample_size > 0', name='ck_sample_size_positive'),
    )
    
    # Indexes for performance
    __table_args__ += (
        Index('idx_salary_benchmarks_lookup', 'location', 'industry', 'experience_level', 'education_level'),
        Index('idx_salary_benchmarks_location', 'location'),
        Index('idx_salary_benchmarks_industry', 'industry'),
        Index('idx_salary_benchmarks_experience', 'experience_level'),
        Index('idx_salary_benchmarks_education', 'education_level'),
        Index('idx_salary_benchmarks_updated', 'last_updated'),
    )


class PredictionCache(Base):
    """Cache for ML predictions to improve performance"""
    __tablename__ = 'prediction_cache'
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # Prediction data
    prediction_data = Column(JSON, nullable=False)
    prediction_type = Column(String(50), nullable=False)  # salary, career, skill_impact
    
    # Cache metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime, nullable=False, default=func.now())
    
    # Performance metrics
    generation_time_ms = Column(Integer, nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('hit_count >= 0', name='ck_hit_count_positive'),
        Index('idx_prediction_cache_expires', 'expires_at'),
        Index('idx_prediction_cache_type', 'prediction_type'),
        Index('idx_prediction_cache_accessed', 'last_accessed'),
    )


class LeadEngagementScore(Base):
    """Lead engagement scoring for conversion optimization"""
    __tablename__ = 'lead_engagement_scores'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    
    # Engagement metrics
    engagement_score = Column(Float, nullable=False, default=0.0)
    interaction_count = Column(Integer, nullable=False, default=0)
    last_interaction = Column(DateTime, nullable=True)
    
    # Behavioral data
    pages_visited = Column(ARRAY(String), nullable=True)
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    features_used = Column(ARRAY(String), nullable=True)
    
    # Conversion data
    conversion_probability = Column(Float, nullable=False, default=0.0)
    conversion_stage = Column(String(50), nullable=True)  # awareness, consideration, decision
    conversion_value = Column(Float, nullable=True)
    
    # Lead quality indicators
    salary_range = Column(String(50), nullable=True)
    industry = Column(Enum(IndustryType), nullable=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=True)
    education_level = Column(Enum(EducationLevel), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='ck_engagement_score_range'),
        CheckConstraint('interaction_count >= 0', name='ck_interaction_count_positive'),
        CheckConstraint('conversion_probability >= 0 AND conversion_probability <= 1', name='ck_conversion_probability_range'),
        Index('idx_lead_engagement_email', 'email'),
        Index('idx_lead_engagement_score', 'engagement_score'),
        Index('idx_lead_engagement_conversion', 'conversion_probability'),
        Index('idx_lead_engagement_updated', 'updated_at'),
    )


class SalaryPrediction(Base):
    """Individual salary predictions for users"""
    __tablename__ = 'salary_predictions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=True, index=True)  # Can be anonymous
    session_id = Column(String(100), nullable=True, index=True)
    
    # User parameters
    current_salary = Column(Float, nullable=False)
    location = Column(String(100), nullable=False)
    industry = Column(Enum(IndustryType), nullable=False)
    experience_level = Column(Enum(ExperienceLevel), nullable=False)
    education_level = Column(Enum(EducationLevel), nullable=False)
    skills = Column(ARRAY(String), nullable=True)
    
    # Prediction results
    predicted_salary_1yr = Column(Float, nullable=False)
    predicted_salary_3yr = Column(Float, nullable=False)
    predicted_salary_5yr = Column(Float, nullable=False)
    
    # Market comparison
    peer_average = Column(Float, nullable=False)
    peer_median = Column(Float, nullable=False)
    percentile_rank = Column(Float, nullable=False)
    salary_gap = Column(Float, nullable=False)
    
    # Confidence and accuracy
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    prediction_confidence = Column(Float, nullable=False, default=0.7)
    
    # Metadata
    prediction_model_version = Column(String(50), nullable=True)
    data_sources_used = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('current_salary > 0', name='ck_current_salary_positive'),
        CheckConstraint('predicted_salary_1yr > 0', name='ck_predicted_1yr_positive'),
        CheckConstraint('predicted_salary_3yr > 0', name='ck_predicted_3yr_positive'),
        CheckConstraint('predicted_salary_5yr > 0', name='ck_predicted_5yr_positive'),
        CheckConstraint('percentile_rank >= 0 AND percentile_rank <= 100', name='ck_percentile_range'),
        CheckConstraint('prediction_confidence >= 0 AND prediction_confidence <= 1', name='ck_confidence_range'),
        Index('idx_salary_prediction_user', 'user_id'),
        Index('idx_salary_prediction_session', 'session_id'),
        Index('idx_salary_prediction_location', 'location'),
        Index('idx_salary_prediction_industry', 'industry'),
        Index('idx_salary_prediction_created', 'created_at'),
    )


class CareerPathRecommendation(Base):
    """Career path recommendations for users"""
    __tablename__ = 'career_path_recommendations'
    
    id = Column(Integer, primary_key=True)
    salary_prediction_id = Column(Integer, ForeignKey('salary_predictions.id'), nullable=False)
    
    # Career path data
    target_role = Column(String(100), nullable=False)
    target_salary = Column(Float, nullable=False)
    estimated_timeline_months = Column(Integer, nullable=False)
    
    # Investment analysis
    required_investment = Column(Float, nullable=False, default=0.0)
    projected_return = Column(Float, nullable=False, default=0.0)
    roi_percentage = Column(Float, nullable=False, default=0.0)
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False, default='medium')  # low, medium, high
    success_probability = Column(Float, nullable=False, default=0.5)
    
    # Recommendations
    recommended_actions = Column(ARRAY(String), nullable=True)
    skill_gaps = Column(ARRAY(String), nullable=True)
    education_requirements = Column(ARRAY(String), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    salary_prediction = relationship("SalaryPrediction", backref="career_recommendations")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('target_salary > 0', name='ck_target_salary_positive'),
        CheckConstraint('estimated_timeline_months > 0', name='ck_timeline_positive'),
        CheckConstraint('roi_percentage >= -100', name='ck_roi_minimum'),
        CheckConstraint('success_probability >= 0 AND success_probability <= 1', name='ck_success_probability_range'),
        Index('idx_career_path_prediction', 'salary_prediction_id'),
        Index('idx_career_path_target_role', 'target_role'),
        Index('idx_career_path_roi', 'roi_percentage'),
    )


class LeadCaptureEvent(Base):
    """Lead capture events and form submissions"""
    __tablename__ = 'lead_capture_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, index=True)
    
    # Lead information
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Professional data
    current_salary = Column(Float, nullable=True)
    target_salary = Column(Float, nullable=True)
    location = Column(String(100), nullable=True)
    industry = Column(Enum(IndustryType), nullable=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=True)
    education_level = Column(Enum(EducationLevel), nullable=True)
    
    # Career goals
    career_goals = Column(ARRAY(String), nullable=True)
    preferred_location = Column(String(100), nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    company_size = Column(String(50), nullable=True)
    current_role = Column(String(100), nullable=True)
    
    # Event metadata
    event_type = Column(String(50), nullable=False)  # form_submit, report_download, etc.
    step_completed = Column(Integer, nullable=False, default=1)
    total_steps = Column(Integer, nullable=False, default=4)
    
    # Conversion tracking
    converted = Column(Boolean, nullable=False, default=False)
    conversion_value = Column(Float, nullable=True)
    conversion_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('step_completed > 0', name='ck_step_completed_positive'),
        CheckConstraint('total_steps > 0', name='ck_total_steps_positive'),
        CheckConstraint('step_completed <= total_steps', name='ck_step_completed_valid'),
        Index('idx_lead_capture_email', 'email'),
        Index('idx_lead_capture_session', 'session_id'),
        Index('idx_lead_capture_event_type', 'event_type'),
        Index('idx_lead_capture_converted', 'converted'),
        Index('idx_lead_capture_created', 'created_at'),
    )


class GamificationBadge(Base):
    """Gamification badges for user engagement"""
    __tablename__ = 'gamification_badges'
    
    id = Column(Integer, primary_key=True)
    badge_name = Column(String(100), nullable=False, unique=True)
    badge_description = Column(Text, nullable=False)
    badge_icon = Column(String(50), nullable=False)  # Emoji or icon name
    badge_color = Column(String(7), nullable=False)  # Hex color code
    
    # Unlock criteria
    unlock_criteria = Column(JSON, nullable=False)  # Criteria for unlocking
    points_value = Column(Integer, nullable=False, default=10)
    
    # Badge metadata
    badge_type = Column(Enum(BadgeType), nullable=False)
    rarity = Column(String(20), nullable=False, default='common')  # common, rare, epic, legendary
    category = Column(String(50), nullable=False, default='general')
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('points_value >= 0', name='ck_points_value_positive'),
        Index('idx_gamification_badge_type', 'badge_type'),
        Index('idx_gamification_badge_rarity', 'rarity'),
        Index('idx_gamification_badge_category', 'category'),
    )


class UserBadge(Base):
    """User badge assignments and achievements"""
    __tablename__ = 'user_badges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=True, index=True)  # Can be anonymous
    session_id = Column(String(100), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey('gamification_badges.id'), nullable=False)
    
    # Achievement data
    unlocked_at = Column(DateTime, nullable=False, default=func.now())
    unlock_context = Column(JSON, nullable=True)  # Context when badge was unlocked
    
    # Progress tracking
    progress_percentage = Column(Float, nullable=False, default=100.0)
    progress_data = Column(JSON, nullable=True)  # Detailed progress information
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    badge = relationship("GamificationBadge", backref="user_assignments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='ck_progress_percentage_range'),
        Index('idx_user_badge_user', 'user_id'),
        Index('idx_user_badge_session', 'session_id'),
        Index('idx_user_badge_badge', 'badge_id'),
        Index('idx_user_badge_unlocked', 'unlocked_at'),
    )


class EmailSequence(Base):
    """Email sequence definitions for lead nurturing"""
    __tablename__ = 'email_sequences'
    
    id = Column(Integer, primary_key=True)
    sequence_name = Column(String(100), nullable=False, unique=True)
    sequence_description = Column(Text, nullable=False)
    
    # Sequence configuration
    trigger_event = Column(String(50), nullable=False)  # lead_captured, report_generated, etc.
    delay_hours = Column(Integer, nullable=False, default=0)
    email_template = Column(String(100), nullable=False)
    
    # Email content
    subject_line = Column(String(200), nullable=False)
    email_content = Column(Text, nullable=False)
    personalization_fields = Column(ARRAY(String), nullable=True)
    
    # Sequence metadata
    sequence_type = Column(Enum(EmailSequenceType), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)
    
    # Performance tracking
    open_rate = Column(Float, nullable=True)
    click_rate = Column(Float, nullable=True)
    conversion_rate = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('delay_hours >= 0', name='ck_delay_hours_positive'),
        CheckConstraint('priority > 0', name='ck_priority_positive'),
        CheckConstraint('open_rate >= 0 AND open_rate <= 1', name='ck_open_rate_range'),
        CheckConstraint('click_rate >= 0 AND click_rate <= 1', name='ck_click_rate_range'),
        CheckConstraint('conversion_rate >= 0 AND conversion_rate <= 1', name='ck_conversion_rate_range'),
        Index('idx_email_sequence_trigger', 'trigger_event'),
        Index('idx_email_sequence_type', 'sequence_type'),
        Index('idx_email_sequence_active', 'is_active'),
        Index('idx_email_sequence_priority', 'priority'),
    )


class EmailSend(Base):
    """Email send tracking and analytics"""
    __tablename__ = 'email_sends'
    
    id = Column(Integer, primary_key=True)
    sequence_id = Column(Integer, ForeignKey('email_sequences.id'), nullable=False)
    lead_id = Column(String(100), nullable=False, index=True)
    
    # Email data
    recipient_email = Column(String(255), nullable=False, index=True)
    subject_line = Column(String(200), nullable=False)
    email_content = Column(Text, nullable=False)
    
    # Send tracking
    sent_at = Column(DateTime, nullable=False, default=func.now())
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    
    # Engagement metrics
    opened = Column(Boolean, nullable=False, default=False)
    clicked = Column(Boolean, nullable=False, default=False)
    unsubscribed = Column(Boolean, nullable=False, default=False)
    bounced = Column(Boolean, nullable=False, default=False)
    
    # Performance data
    open_count = Column(Integer, nullable=False, default=0)
    click_count = Column(Integer, nullable=False, default=0)
    time_to_open_minutes = Column(Integer, nullable=True)
    time_to_click_minutes = Column(Integer, nullable=True)
    
    # Metadata
    email_provider = Column(String(50), nullable=True)
    campaign_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    sequence = relationship("EmailSequence", backref="email_sends")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('open_count >= 0', name='ck_open_count_positive'),
        CheckConstraint('click_count >= 0', name='ck_click_count_positive'),
        CheckConstraint('time_to_open_minutes >= 0', name='ck_time_to_open_positive'),
        CheckConstraint('time_to_click_minutes >= 0', name='ck_time_to_click_positive'),
        Index('idx_email_send_sequence', 'sequence_id'),
        Index('idx_email_send_lead', 'lead_id'),
        Index('idx_email_send_email', 'recipient_email'),
        Index('idx_email_send_sent', 'sent_at'),
        Index('idx_email_send_opened', 'opened'),
        Index('idx_email_send_clicked', 'clicked'),
    )


class IncomeComparisonAnalytics(Base):
    """Analytics and metrics for the income comparison tool"""
    __tablename__ = 'income_comparison_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Usage metrics
    total_sessions = Column(Integer, nullable=False, default=0)
    unique_users = Column(Integer, nullable=False, default=0)
    predictions_generated = Column(Integer, nullable=False, default=0)
    reports_downloaded = Column(Integer, nullable=False, default=0)
    
    # Conversion metrics
    leads_captured = Column(Integer, nullable=False, default=0)
    conversion_rate = Column(Float, nullable=False, default=0.0)
    average_engagement_score = Column(Float, nullable=False, default=0.0)
    
    # Performance metrics
    average_prediction_time_ms = Column(Integer, nullable=True)
    api_success_rate = Column(Float, nullable=True)
    cache_hit_rate = Column(Float, nullable=True)
    
    # User behavior
    average_session_duration_seconds = Column(Integer, nullable=True)
    average_predictions_per_session = Column(Float, nullable=True)
    most_popular_locations = Column(ARRAY(String), nullable=True)
    most_popular_industries = Column(ARRAY(String), nullable=True)
    
    # Revenue metrics
    total_conversion_value = Column(Float, nullable=False, default=0.0)
    average_conversion_value = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_sessions >= 0', name='ck_total_sessions_positive'),
        CheckConstraint('unique_users >= 0', name='ck_unique_users_positive'),
        CheckConstraint('predictions_generated >= 0', name='ck_predictions_positive'),
        CheckConstraint('leads_captured >= 0', name='ck_leads_positive'),
        CheckConstraint('conversion_rate >= 0 AND conversion_rate <= 1', name='ck_conversion_rate_range'),
        CheckConstraint('average_engagement_score >= 0 AND average_engagement_score <= 100', name='ck_engagement_score_range'),
        CheckConstraint('api_success_rate >= 0 AND api_success_rate <= 1', name='ck_api_success_range'),
        CheckConstraint('cache_hit_rate >= 0 AND cache_hit_rate <= 1', name='ck_cache_hit_range'),
        Index('idx_analytics_date', 'date'),
        Index('idx_analytics_conversion', 'conversion_rate'),
        Index('idx_analytics_engagement', 'average_engagement_score'),
    )


# Export all models
__all__ = [
    'SalaryBenchmark',
    'PredictionCache', 
    'LeadEngagementScore',
    'SalaryPrediction',
    'CareerPathRecommendation',
    'LeadCaptureEvent',
    'GamificationBadge',
    'UserBadge',
    'EmailSequence',
    'EmailSend',
    'IncomeComparisonAnalytics',
    'ExperienceLevel',
    'EducationLevel',
    'IndustryType',
    'BadgeType',
    'EmailSequenceType'
] 