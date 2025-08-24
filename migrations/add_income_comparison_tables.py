"""Add income comparison calculator tables

Revision ID: 2024_01_income_comparison
Revises: 2024_01_base_schema
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2024_01_income_comparison'
down_revision = '2024_01_base_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create salary_benchmarks table
    op.create_table('salary_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('experience_level', sa.String(length=50), nullable=False),
        sa.Column('education_level', sa.String(length=50), nullable=False),
        sa.Column('job_title', sa.String(length=200), nullable=True),
        sa.Column('percentile_10', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('percentile_25', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('percentile_50', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('percentile_75', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('percentile_90', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('mean_salary', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('std_deviation', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_interval_lower', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('confidence_interval_upper', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('data_source', sa.String(length=100), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('location', 'industry', 'experience_level', 'education_level', 'job_title', name='uq_salary_benchmark')
    )
    
    # Create index for faster lookups
    op.create_index('idx_salary_benchmarks_lookup', 'salary_benchmarks', 
                   ['location', 'industry', 'experience_level', 'education_level'])
    op.create_index('idx_salary_benchmarks_updated', 'salary_benchmarks', ['last_updated'])

    # Create prediction_cache table
    op.create_table('prediction_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('prediction_type', sa.String(length=50), nullable=False),
        sa.Column('input_parameters', postgresql.JSONB(), nullable=False),
        sa.Column('prediction_result', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key', name='uq_prediction_cache_key')
    )
    
    # Create indexes for cache management
    op.create_index('idx_prediction_cache_type', 'prediction_cache', ['prediction_type'])
    op.create_index('idx_prediction_cache_expires', 'prediction_cache', ['expires_at'])
    op.create_index('idx_prediction_cache_created', 'prediction_cache', ['created_at'])

    # Create lead_engagement_scores table
    op.create_table('lead_engagement_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('engagement_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('interaction_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('conversion_probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('lead_stage', sa.String(length=50), nullable=False),
        sa.Column('preferred_contact_method', sa.String(length=50), nullable=True),
        sa.Column('urgency_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_lead_engagement_email')
    )
    
    # Create indexes for lead management
    op.create_index('idx_lead_engagement_score', 'lead_engagement_scores', ['engagement_score'])
    op.create_index('idx_lead_engagement_stage', 'lead_engagement_scores', ['lead_stage'])
    op.create_index('idx_lead_engagement_updated', 'lead_engagement_scores', ['updated_at'])

    # Create salary_predictions table
    op.create_table('salary_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('current_salary', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('target_salary', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('experience_years', sa.Integer(), nullable=False),
        sa.Column('education_level', sa.String(length=50), nullable=False),
        sa.Column('skills', postgresql.JSONB(), nullable=True),
        sa.Column('predicted_salary_1yr', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('predicted_salary_3yr', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('predicted_salary_5yr', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('growth_rate', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('percentile_rank', sa.Integer(), nullable=False),
        sa.Column('market_position', sa.String(length=50), nullable=False),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for salary predictions
    op.create_index('idx_salary_predictions_user', 'salary_predictions', ['user_id'])
    op.create_index('idx_salary_predictions_session', 'salary_predictions', ['session_id'])
    op.create_index('idx_salary_predictions_location', 'salary_predictions', ['location'])
    op.create_index('idx_salary_predictions_industry', 'salary_predictions', ['industry'])

    # Create career_path_recommendations table
    op.create_table('career_path_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_id', sa.Integer(), nullable=False),
        sa.Column('path_name', sa.String(length=200), nullable=False),
        sa.Column('path_description', sa.Text(), nullable=True),
        sa.Column('estimated_timeline_months', sa.Integer(), nullable=False),
        sa.Column('required_investment', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('projected_return', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('roi_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('required_skills', postgresql.JSONB(), nullable=True),
        sa.Column('certifications', postgresql.JSONB(), nullable=True),
        sa.Column('education_requirements', postgresql.JSONB(), nullable=True),
        sa.Column('market_demand_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prediction_id'], ['salary_predictions.id'], ondelete='CASCADE')
    )
    
    # Create indexes for career paths
    op.create_index('idx_career_path_prediction', 'career_path_recommendations', ['prediction_id'])
    op.create_index('idx_career_path_roi', 'career_path_recommendations', ['roi_percentage'])
    op.create_index('idx_career_path_risk', 'career_path_recommendations', ['risk_level'])

    # Create lead_capture_events table
    op.create_table('lead_capture_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('form_data', postgresql.JSONB(), nullable=True),
        sa.Column('completion_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for lead capture analytics
    op.create_index('idx_lead_capture_session', 'lead_capture_events', ['session_id'])
    op.create_index('idx_lead_capture_type', 'lead_capture_events', ['event_type'])
    op.create_index('idx_lead_capture_created', 'lead_capture_events', ['created_at'])

    # Create gamification_badges table
    op.create_table('gamification_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('badge_name', sa.String(length=100), nullable=False),
        sa.Column('badge_description', sa.Text(), nullable=True),
        sa.Column('badge_icon', sa.String(length=100), nullable=True),
        sa.Column('badge_color', sa.String(length=7), nullable=True),
        sa.Column('unlock_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('badge_name', name='uq_gamification_badge_name')
    )

    # Create user_badges table
    op.create_table('user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False),
        sa.Column('unlock_context', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['badge_id'], ['gamification_badges.id'], ondelete='CASCADE')
    )
    
    # Create indexes for gamification
    op.create_index('idx_user_badges_user', 'user_badges', ['user_id'])
    op.create_index('idx_user_badges_session', 'user_badges', ['session_id'])
    op.create_index('idx_user_badges_unlocked', 'user_badges', ['unlocked_at'])

    # Create email_sequences table
    op.create_table('email_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sequence_name', sa.String(length=100), nullable=False),
        sa.Column('sequence_description', sa.Text(), nullable=True),
        sa.Column('trigger_event', sa.String(length=50), nullable=False),
        sa.Column('delay_hours', sa.Integer(), nullable=False),
        sa.Column('email_template', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create email_sends table
    op.create_table('email_sends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('sequence_id', sa.Integer(), nullable=False),
        sa.Column('email_address', sa.String(length=255), nullable=False),
        sa.Column('email_subject', sa.String(length=200), nullable=False),
        sa.Column('email_content', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='scheduled'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['lead_engagement_scores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sequence_id'], ['email_sequences.id'], ondelete='CASCADE')
    )
    
    # Create indexes for email tracking
    op.create_index('idx_email_sends_lead', 'email_sends', ['lead_id'])
    op.create_index('idx_email_sends_status', 'email_sends', ['status'])
    op.create_index('idx_email_sends_scheduled', 'email_sends', ['scheduled_at'])

    # Insert default gamification badges
    op.execute("""
        INSERT INTO gamification_badges (badge_name, badge_description, badge_icon, badge_color, unlock_criteria, created_at) VALUES
        ('Getting Started', 'Completed your first step in the income comparison process', '🚀', '#3B82F6', '{"step_completed": 1}', NOW()),
        ('Salary Insight', 'Unlocked detailed salary analysis and benchmarking', '💰', '#10B981', '{"step_completed": 2}', NOW()),
        ('Career Planner', 'Generated personalized career plan and recommendations', '📈', '#8B5CF6', '{"step_completed": 3}', NOW()),
        ('Market Expert', 'Achieved top 10% salary percentile in your field', '🏆', '#F59E0B', '{"percentile_rank": 90}', NOW()),
        ('Goal Setter', 'Set ambitious career goals and target salary', '🎯', '#EF4444', '{"target_salary_set": true}', NOW()),
        ('Skill Developer', 'Identified key skills for career advancement', '🛠️', '#06B6D4', '{"skills_identified": 3}', NOW()),
        ('Network Builder', 'Engaged with professional networking features', '🤝', '#84CC16', '{"networking_actions": 5}', NOW()),
        ('Data Driven', 'Viewed comprehensive salary and market data', '📊', '#6366F1', '{"data_views": 10}', NOW())
    """)

    # Insert default email sequences
    op.execute("""
        INSERT INTO email_sequences (sequence_name, sequence_description, trigger_event, delay_hours, email_template, created_at) VALUES
        ('Welcome Series', 'Welcome new leads with personalized insights', 'lead_captured', 0, 'welcome_email', NOW()),
        ('Salary Insights', 'Follow up with detailed salary analysis', 'report_generated', 24, 'salary_insights', NOW()),
        ('Career Planning', 'Send career advancement recommendations', 'report_generated', 72, 'career_planning', NOW()),
        ('Skill Development', 'Recommend skill development opportunities', 'skills_identified', 168, 'skill_development', NOW()),
        ('Market Updates', 'Send market trend updates and insights', 'lead_engaged', 336, 'market_updates', NOW()),
        ('Re-engagement', 'Re-engage inactive leads with new features', 'lead_inactive', 720, 're_engagement', NOW())
    """)


def downgrade():
    # Drop tables in reverse order
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