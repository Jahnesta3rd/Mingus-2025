"""
Migration: Create Income Comparison Tables
Creates all tables for the income comparison calculator with proper constraints and indexes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timedelta
import json

# revision identifiers, used by Alembic
revision = '001_create_income_comparison_tables'
down_revision = None  # Set to the previous migration if exists
branch_labels = None
depends_on = None


def upgrade():
    """Create all income comparison tables"""
    
    # Create enums first
    op.execute("""
        CREATE TYPE experience_level AS ENUM ('entry', 'mid', 'senior');
    """)
    
    op.execute("""
        CREATE TYPE education_level AS ENUM ('high-school', 'some-college', 'bachelor', 'master', 'doctorate');
    """)
    
    op.execute("""
        CREATE TYPE industry_type AS ENUM ('technology', 'healthcare', 'finance', 'education', 'manufacturing', 'retail', 'consulting', 'government', 'nonprofit', 'media');
    """)
    
    op.execute("""
        CREATE TYPE badge_type AS ENUM ('salary_insight', 'career_planner', 'market_expert', 'goal_setter', 'skill_developer', 'network_builder', 'data_driven', 'progress_maker');
    """)
    
    op.execute("""
        CREATE TYPE email_sequence_type AS ENUM ('welcome', 'salary_insights', 'career_planning', 'skill_development', 'market_updates', 're_engagement');
    """)
    
    # 1. Salary Benchmarks Table
    op.create_table('salary_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.Enum('technology', 'healthcare', 'finance', 'education', 'manufacturing', 'retail', 'consulting', 'government', 'nonprofit', 'media', name='industry_type'), nullable=False),
        sa.Column('experience_level', sa.Enum('entry', 'mid', 'senior', name='experience_level'), nullable=False),
        sa.Column('education_level', sa.Enum('high-school', 'some-college', 'bachelor', 'master', 'doctorate', name='education_level'), nullable=False),
        sa.Column('job_title', sa.String(length=200), nullable=True),
        sa.Column('mean_salary', sa.Float(), nullable=False),
        sa.Column('median_salary', sa.Float(), nullable=False),
        sa.Column('percentile_25', sa.Float(), nullable=False),
        sa.Column('percentile_75', sa.Float(), nullable=False),
        sa.Column('percentile_90', sa.Float(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=False, server_default='BLS'),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('market_conditions', sa.JSON(), nullable=True),
        sa.Column('demographic_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('location', 'industry', 'experience_level', 'education_level', 'job_title', name='uq_salary_benchmark'),
        sa.CheckConstraint('mean_salary > 0', name='ck_mean_salary_positive'),
        sa.CheckConstraint('median_salary > 0', name='ck_median_salary_positive'),
        sa.CheckConstraint('sample_size > 0', name='ck_sample_size_positive')
    )
    
    # Indexes for salary_benchmarks
    op.create_index('idx_salary_benchmarks_lookup', 'salary_benchmarks', ['location', 'industry', 'experience_level', 'education_level'])
    op.create_index('idx_salary_benchmarks_location', 'salary_benchmarks', ['location'])
    op.create_index('idx_salary_benchmarks_industry', 'salary_benchmarks', ['industry'])
    op.create_index('idx_salary_benchmarks_experience', 'salary_benchmarks', ['experience_level'])
    op.create_index('idx_salary_benchmarks_education', 'salary_benchmarks', ['education_level'])
    op.create_index('idx_salary_benchmarks_updated', 'salary_benchmarks', ['last_updated'])
    
    # 2. Prediction Cache Table
    op.create_table('prediction_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('prediction_data', sa.JSON(), nullable=False),
        sa.Column('prediction_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key', name='uq_prediction_cache_key'),
        sa.CheckConstraint('hit_count >= 0', name='ck_hit_count_positive')
    )
    
    # Indexes for prediction_cache
    op.create_index('idx_prediction_cache_expires', 'prediction_cache', ['expires_at'])
    op.create_index('idx_prediction_cache_type', 'prediction_cache', ['prediction_type'])
    op.create_index('idx_prediction_cache_accessed', 'prediction_cache', ['last_accessed'])
    
    # 3. Lead Engagement Score Table
    op.create_table('lead_engagement_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('interaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('pages_visited', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('features_used', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('conversion_probability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('conversion_stage', sa.String(length=50), nullable=True),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('salary_range', sa.String(length=50), nullable=True),
        sa.Column('industry', sa.Enum('technology', 'healthcare', 'finance', 'education', 'manufacturing', 'retail', 'consulting', 'government', 'nonprofit', 'media', name='industry_type'), nullable=True),
        sa.Column('experience_level', sa.Enum('entry', 'mid', 'senior', name='experience_level'), nullable=True),
        sa.Column('education_level', sa.Enum('high-school', 'some-college', 'bachelor', 'master', 'doctorate', name='education_level'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id', name='uq_lead_engagement_lead_id'),
        sa.CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='ck_engagement_score_range'),
        sa.CheckConstraint('interaction_count >= 0', name='ck_interaction_count_positive'),
        sa.CheckConstraint('conversion_probability >= 0 AND conversion_probability <= 1', name='ck_conversion_probability_range')
    )
    
    # Indexes for lead_engagement_scores
    op.create_index('idx_lead_engagement_email', 'lead_engagement_scores', ['email'])
    op.create_index('idx_lead_engagement_score', 'lead_engagement_scores', ['engagement_score'])
    op.create_index('idx_lead_engagement_conversion', 'lead_engagement_scores', ['conversion_probability'])
    op.create_index('idx_lead_engagement_updated', 'lead_engagement_scores', ['updated_at'])
    
    # 4. Salary Predictions Table
    op.create_table('salary_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('current_salary', sa.Float(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.Enum('technology', 'healthcare', 'finance', 'education', 'manufacturing', 'retail', 'consulting', 'government', 'nonprofit', 'media', name='industry_type'), nullable=False),
        sa.Column('experience_level', sa.Enum('entry', 'mid', 'senior', name='experience_level'), nullable=False),
        sa.Column('education_level', sa.Enum('high-school', 'some-college', 'bachelor', 'master', 'doctorate', name='education_level'), nullable=False),
        sa.Column('skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('predicted_salary_1yr', sa.Float(), nullable=False),
        sa.Column('predicted_salary_3yr', sa.Float(), nullable=False),
        sa.Column('predicted_salary_5yr', sa.Float(), nullable=False),
        sa.Column('peer_average', sa.Float(), nullable=False),
        sa.Column('peer_median', sa.Float(), nullable=False),
        sa.Column('percentile_rank', sa.Float(), nullable=False),
        sa.Column('salary_gap', sa.Float(), nullable=False),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('prediction_confidence', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('prediction_model_version', sa.String(length=50), nullable=True),
        sa.Column('data_sources_used', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('current_salary > 0', name='ck_current_salary_positive'),
        sa.CheckConstraint('predicted_salary_1yr > 0', name='ck_predicted_1yr_positive'),
        sa.CheckConstraint('predicted_salary_3yr > 0', name='ck_predicted_3yr_positive'),
        sa.CheckConstraint('predicted_salary_5yr > 0', name='ck_predicted_5yr_positive'),
        sa.CheckConstraint('percentile_rank >= 0 AND percentile_rank <= 100', name='ck_percentile_range'),
        sa.CheckConstraint('prediction_confidence >= 0 AND prediction_confidence <= 1', name='ck_confidence_range')
    )
    
    # Indexes for salary_predictions
    op.create_index('idx_salary_prediction_user', 'salary_predictions', ['user_id'])
    op.create_index('idx_salary_prediction_session', 'salary_predictions', ['session_id'])
    op.create_index('idx_salary_prediction_location', 'salary_predictions', ['location'])
    op.create_index('idx_salary_prediction_industry', 'salary_predictions', ['industry'])
    op.create_index('idx_salary_prediction_created', 'salary_predictions', ['created_at'])
    
    # 5. Career Path Recommendations Table
    op.create_table('career_path_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salary_prediction_id', sa.Integer(), nullable=False),
        sa.Column('target_role', sa.String(length=100), nullable=False),
        sa.Column('target_salary', sa.Float(), nullable=False),
        sa.Column('estimated_timeline_months', sa.Integer(), nullable=False),
        sa.Column('required_investment', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('projected_return', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('roi_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('success_probability', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('recommended_actions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('skill_gaps', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('education_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['salary_prediction_id'], ['salary_predictions.id'], name='fk_career_path_prediction'),
        sa.CheckConstraint('target_salary > 0', name='ck_target_salary_positive'),
        sa.CheckConstraint('estimated_timeline_months > 0', name='ck_timeline_positive'),
        sa.CheckConstraint('roi_percentage >= -100', name='ck_roi_minimum'),
        sa.CheckConstraint('success_probability >= 0 AND success_probability <= 1', name='ck_success_probability_range')
    )
    
    # Indexes for career_path_recommendations
    op.create_index('idx_career_path_prediction', 'career_path_recommendations', ['salary_prediction_id'])
    op.create_index('idx_career_path_target_role', 'career_path_recommendations', ['target_role'])
    op.create_index('idx_career_path_roi', 'career_path_recommendations', ['roi_percentage'])
    
    # 6. Lead Capture Events Table
    op.create_table('lead_capture_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('current_salary', sa.Float(), nullable=True),
        sa.Column('target_salary', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.Enum('technology', 'healthcare', 'finance', 'education', 'manufacturing', 'retail', 'consulting', 'government', 'nonprofit', 'media', name='industry_type'), nullable=True),
        sa.Column('experience_level', sa.Enum('entry', 'mid', 'senior', name='experience_level'), nullable=True),
        sa.Column('education_level', sa.Enum('high-school', 'some-college', 'bachelor', 'master', 'doctorate', name='education_level'), nullable=True),
        sa.Column('career_goals', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_location', sa.String(length=100), nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('current_role', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('step_completed', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('converted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('conversion_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('step_completed > 0', name='ck_step_completed_positive'),
        sa.CheckConstraint('total_steps > 0', name='ck_total_steps_positive'),
        sa.CheckConstraint('step_completed <= total_steps', name='ck_step_completed_valid')
    )
    
    # Indexes for lead_capture_events
    op.create_index('idx_lead_capture_email', 'lead_capture_events', ['email'])
    op.create_index('idx_lead_capture_session', 'lead_capture_events', ['session_id'])
    op.create_index('idx_lead_capture_event_type', 'lead_capture_events', ['event_type'])
    op.create_index('idx_lead_capture_converted', 'lead_capture_events', ['converted'])
    op.create_index('idx_lead_capture_created', 'lead_capture_events', ['created_at'])
    
    # 7. Gamification Badges Table
    op.create_table('gamification_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('badge_name', sa.String(length=100), nullable=False),
        sa.Column('badge_description', sa.Text(), nullable=False),
        sa.Column('badge_icon', sa.String(length=50), nullable=False),
        sa.Column('badge_color', sa.String(length=7), nullable=False),
        sa.Column('unlock_criteria', sa.JSON(), nullable=False),
        sa.Column('points_value', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('badge_type', sa.Enum('salary_insight', 'career_planner', 'market_expert', 'goal_setter', 'skill_developer', 'network_builder', 'data_driven', 'progress_maker', name='badge_type'), nullable=False),
        sa.Column('rarity', sa.String(length=20), nullable=False, server_default='common'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('badge_name', name='uq_gamification_badge_name'),
        sa.CheckConstraint('points_value >= 0', name='ck_points_value_positive')
    )
    
    # Indexes for gamification_badges
    op.create_index('idx_gamification_badge_type', 'gamification_badges', ['badge_type'])
    op.create_index('idx_gamification_badge_rarity', 'gamification_badges', ['rarity'])
    op.create_index('idx_gamification_badge_category', 'gamification_badges', ['category'])
    
    # 8. User Badges Table
    op.create_table('user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('unlock_context', sa.JSON(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('progress_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['badge_id'], ['gamification_badges.id'], name='fk_user_badge_badge'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='ck_progress_percentage_range')
    )
    
    # Indexes for user_badges
    op.create_index('idx_user_badge_user', 'user_badges', ['user_id'])
    op.create_index('idx_user_badge_session', 'user_badges', ['session_id'])
    op.create_index('idx_user_badge_badge', 'user_badges', ['badge_id'])
    op.create_index('idx_user_badge_unlocked', 'user_badges', ['unlocked_at'])
    
    # 9. Email Sequences Table
    op.create_table('email_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sequence_name', sa.String(length=100), nullable=False),
        sa.Column('sequence_description', sa.Text(), nullable=False),
        sa.Column('trigger_event', sa.String(length=50), nullable=False),
        sa.Column('delay_hours', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('email_template', sa.String(length=100), nullable=False),
        sa.Column('subject_line', sa.String(length=200), nullable=False),
        sa.Column('email_content', sa.Text(), nullable=False),
        sa.Column('personalization_fields', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('sequence_type', sa.Enum('welcome', 'salary_insights', 'career_planning', 'skill_development', 'market_updates', 're_engagement', name='email_sequence_type'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('open_rate', sa.Float(), nullable=True),
        sa.Column('click_rate', sa.Float(), nullable=True),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sequence_name', name='uq_email_sequence_name'),
        sa.CheckConstraint('delay_hours >= 0', name='ck_delay_hours_positive'),
        sa.CheckConstraint('priority > 0', name='ck_priority_positive'),
        sa.CheckConstraint('open_rate >= 0 AND open_rate <= 1', name='ck_open_rate_range'),
        sa.CheckConstraint('click_rate >= 0 AND click_rate <= 1', name='ck_click_rate_range'),
        sa.CheckConstraint('conversion_rate >= 0 AND conversion_rate <= 1', name='ck_conversion_rate_range')
    )
    
    # Indexes for email_sequences
    op.create_index('idx_email_sequence_trigger', 'email_sequences', ['trigger_event'])
    op.create_index('idx_email_sequence_type', 'email_sequences', ['sequence_type'])
    op.create_index('idx_email_sequence_active', 'email_sequences', ['is_active'])
    op.create_index('idx_email_sequence_priority', 'email_sequences', ['priority'])
    
    # 10. Email Sends Table
    op.create_table('email_sends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sequence_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.String(length=100), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('subject_line', sa.String(length=200), nullable=False),
        sa.Column('email_content', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('opened', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('clicked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unsubscribed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bounced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('open_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('click_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_to_open_minutes', sa.Integer(), nullable=True),
        sa.Column('time_to_click_minutes', sa.Integer(), nullable=True),
        sa.Column('email_provider', sa.String(length=50), nullable=True),
        sa.Column('campaign_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sequence_id'], ['email_sequences.id'], name='fk_email_send_sequence'),
        sa.CheckConstraint('open_count >= 0', name='ck_open_count_positive'),
        sa.CheckConstraint('click_count >= 0', name='ck_click_count_positive'),
        sa.CheckConstraint('time_to_open_minutes >= 0', name='ck_time_to_open_positive'),
        sa.CheckConstraint('time_to_click_minutes >= 0', name='ck_time_to_click_positive')
    )
    
    # Indexes for email_sends
    op.create_index('idx_email_send_sequence', 'email_sends', ['sequence_id'])
    op.create_index('idx_email_send_lead', 'email_sends', ['lead_id'])
    op.create_index('idx_email_send_email', 'email_sends', ['recipient_email'])
    op.create_index('idx_email_send_sent', 'email_sends', ['sent_at'])
    op.create_index('idx_email_send_opened', 'email_sends', ['opened'])
    op.create_index('idx_email_send_clicked', 'email_sends', ['clicked'])
    
    # 11. Income Comparison Analytics Table
    op.create_table('income_comparison_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_sessions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('predictions_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reports_downloaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('leads_captured', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_engagement_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_prediction_time_ms', sa.Integer(), nullable=True),
        sa.Column('api_success_rate', sa.Float(), nullable=True),
        sa.Column('cache_hit_rate', sa.Float(), nullable=True),
        sa.Column('average_session_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('average_predictions_per_session', sa.Float(), nullable=True),
        sa.Column('most_popular_locations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('most_popular_industries', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('total_conversion_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_conversion_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('total_sessions >= 0', name='ck_total_sessions_positive'),
        sa.CheckConstraint('unique_users >= 0', name='ck_unique_users_positive'),
        sa.CheckConstraint('predictions_generated >= 0', name='ck_predictions_positive'),
        sa.CheckConstraint('leads_captured >= 0', name='ck_leads_positive'),
        sa.CheckConstraint('conversion_rate >= 0 AND conversion_rate <= 1', name='ck_conversion_rate_range'),
        sa.CheckConstraint('average_engagement_score >= 0 AND average_engagement_score <= 100', name='ck_engagement_score_range'),
        sa.CheckConstraint('api_success_rate >= 0 AND api_success_rate <= 1', name='ck_api_success_range'),
        sa.CheckConstraint('cache_hit_rate >= 0 AND cache_hit_rate <= 1', name='ck_cache_hit_range')
    )
    
    # Indexes for income_comparison_analytics
    op.create_index('idx_analytics_date', 'income_comparison_analytics', ['date'])
    op.create_index('idx_analytics_conversion', 'income_comparison_analytics', ['conversion_rate'])
    op.create_index('idx_analytics_engagement', 'income_comparison_analytics', ['average_engagement_score'])
    
    # Insert initial data
    insert_initial_data()


def downgrade():
    """Drop all income comparison tables"""
    
    # Drop tables in reverse order
    op.drop_table('income_comparison_analytics')
    op.drop_table('email_sends')
    op.drop_table('email_sequences')
    op.drop_table('user_badges')
    op.drop_table('gamification_badges')
    op.drop_table('lead_capture_events')
    op.drop_table('career_path_recommendations')
    op.drop_table('salary_predictions')
    op.drop_table('lead_engagement_scores')
    op.drop_table('prediction_cache')
    op.drop_table('salary_benchmarks')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS email_sequence_type")
    op.execute("DROP TYPE IF EXISTS badge_type")
    op.execute("DROP TYPE IF EXISTS industry_type")
    op.execute("DROP TYPE IF EXISTS education_level")
    op.execute("DROP TYPE IF EXISTS experience_level")


def insert_initial_data():
    """Insert initial data for the income comparison system"""
    
    # Insert gamification badges
    op.execute("""
        INSERT INTO gamification_badges (badge_name, badge_description, badge_icon, badge_color, unlock_criteria, badge_type, rarity, category, created_at) VALUES
        ('Getting Started', 'Completed your first step in the income comparison process', '🚀', '#3B82F6', '{"step_completed": 1}', 'progress_maker', 'common', 'onboarding', NOW()),
        ('Salary Insight', 'Unlocked detailed salary analysis and benchmarking', '💰', '#10B981', '{"step_completed": 2}', 'salary_insight', 'common', 'analysis', NOW()),
        ('Career Planner', 'Generated personalized career plan and recommendations', '📈', '#8B5CF6', '{"step_completed": 3}', 'career_planner', 'rare', 'planning', NOW()),
        ('Market Expert', 'Achieved top 10% salary percentile in your field', '🏆', '#F59E0B', '{"percentile_rank": 90}', 'market_expert', 'epic', 'achievement', NOW()),
        ('Goal Setter', 'Set ambitious career goals and target salary', '🎯', '#EF4444', '{"target_salary_set": true}', 'goal_setter', 'common', 'planning', NOW()),
        ('Skill Developer', 'Identified key skills for career advancement', '🛠️', '#06B6D4', '{"skills_identified": 3}', 'skill_developer', 'rare', 'development', NOW()),
        ('Network Builder', 'Engaged with professional networking features', '🤝', '#84CC16', '{"networking_actions": 5}', 'network_builder', 'common', 'networking', NOW()),
        ('Data Driven', 'Viewed comprehensive salary and market data', '📊', '#6366F1', '{"data_views": 10}', 'data_driven', 'rare', 'analysis', NOW())
    """)
    
    # Insert email sequences
    op.execute("""
        INSERT INTO email_sequences (sequence_name, sequence_description, trigger_event, delay_hours, email_template, subject_line, email_content, sequence_type, is_active, priority, created_at) VALUES
        ('Welcome Series', 'Welcome new leads with personalized insights', 'lead_captured', 0, 'welcome_email', 'Welcome to Your Salary Journey!', 'Welcome to your personalized salary analysis journey...', 'welcome', true, 1, NOW()),
        ('Salary Insights', 'Follow up with detailed salary analysis', 'report_generated', 24, 'salary_insights', 'Your Personalized Salary Analysis is Ready', 'Your detailed salary analysis and market insights are ready...', 'salary_insights', true, 2, NOW()),
        ('Career Planning', 'Send career advancement recommendations', 'report_generated', 72, 'career_planning', 'Your Career Advancement Roadmap', 'Based on your profile, here''s your personalized career advancement roadmap...', 'career_planning', true, 3, NOW()),
        ('Skill Development', 'Recommend skill development opportunities', 'skills_identified', 168, 'skill_development', 'Skills That Will Boost Your Salary', 'Here are the top skills that can significantly increase your earning potential...', 'skill_development', true, 4, NOW()),
        ('Market Updates', 'Send market trend updates and insights', 'lead_engaged', 336, 'market_updates', 'Latest Market Trends in Your Industry', 'Stay ahead with the latest salary trends and market insights...', 'market_updates', true, 5, NOW()),
        ('Re-engagement', 'Re-engage inactive leads with new features', 'lead_inactive', 720, 're_engagement', 'New Features to Help You Succeed', 'We''ve added new features to help you maximize your earning potential...', 're_engagement', true, 6, NOW())
    """)
    
    # Insert sample salary benchmarks (technology industry)
    op.execute("""
        INSERT INTO salary_benchmarks (location, industry, experience_level, education_level, mean_salary, median_salary, percentile_25, percentile_75, percentile_90, sample_size, data_source, created_at) VALUES
        ('atlanta', 'technology', 'entry', 'bachelor', 65000, 63000, 55000, 72000, 85000, 1250, 'BLS', NOW()),
        ('atlanta', 'technology', 'mid', 'bachelor', 85000, 82000, 72000, 95000, 110000, 2100, 'BLS', NOW()),
        ('atlanta', 'technology', 'senior', 'bachelor', 120000, 115000, 95000, 135000, 160000, 1800, 'BLS', NOW()),
        ('new-york', 'technology', 'entry', 'bachelor', 75000, 72000, 65000, 82000, 95000, 2800, 'BLS', NOW()),
        ('new-york', 'technology', 'mid', 'bachelor', 100000, 95000, 82000, 115000, 135000, 3200, 'BLS', NOW()),
        ('new-york', 'technology', 'senior', 'bachelor', 150000, 140000, 115000, 170000, 200000, 2500, 'BLS', NOW()),
        ('san-francisco', 'technology', 'entry', 'bachelor', 85000, 82000, 72000, 92000, 105000, 3500, 'BLS', NOW()),
        ('san-francisco', 'technology', 'mid', 'bachelor', 120000, 115000, 95000, 135000, 160000, 4200, 'BLS', NOW()),
        ('san-francisco', 'technology', 'senior', 'bachelor', 180000, 170000, 135000, 200000, 250000, 3100, 'BLS', NOW())
    """)
    
    # Insert sample salary benchmarks (healthcare industry)
    op.execute("""
        INSERT INTO salary_benchmarks (location, industry, experience_level, education_level, mean_salary, median_salary, percentile_25, percentile_75, percentile_90, sample_size, data_source, created_at) VALUES
        ('atlanta', 'healthcare', 'entry', 'bachelor', 55000, 53000, 45000, 62000, 75000, 1800, 'BLS', NOW()),
        ('atlanta', 'healthcare', 'mid', 'bachelor', 75000, 72000, 62000, 85000, 100000, 2400, 'BLS', NOW()),
        ('atlanta', 'healthcare', 'senior', 'bachelor', 100000, 95000, 80000, 115000, 135000, 1600, 'BLS', NOW()),
        ('new-york', 'healthcare', 'entry', 'bachelor', 65000, 62000, 55000, 72000, 85000, 3200, 'BLS', NOW()),
        ('new-york', 'healthcare', 'mid', 'bachelor', 85000, 82000, 72000, 95000, 115000, 3800, 'BLS', NOW()),
        ('new-york', 'healthcare', 'senior', 'bachelor', 120000, 115000, 95000, 135000, 160000, 2800, 'BLS', NOW())
    """)
    
    # Insert sample salary benchmarks (finance industry)
    op.execute("""
        INSERT INTO salary_benchmarks (location, industry, experience_level, education_level, mean_salary, median_salary, percentile_25, percentile_75, percentile_90, sample_size, data_source, created_at) VALUES
        ('atlanta', 'finance', 'entry', 'bachelor', 60000, 58000, 50000, 67000, 80000, 1500, 'BLS', NOW()),
        ('atlanta', 'finance', 'mid', 'bachelor', 80000, 77000, 67000, 90000, 110000, 2200, 'BLS', NOW()),
        ('atlanta', 'finance', 'senior', 'bachelor', 110000, 105000, 90000, 125000, 150000, 1900, 'BLS', NOW()),
        ('new-york', 'finance', 'entry', 'bachelor', 70000, 67000, 60000, 77000, 90000, 3500, 'BLS', NOW()),
        ('new-york', 'finance', 'mid', 'bachelor', 95000, 92000, 80000, 110000, 130000, 4200, 'BLS', NOW()),
        ('new-york', 'finance', 'senior', 'bachelor', 140000, 135000, 110000, 160000, 190000, 3100, 'BLS', NOW())
    """) 