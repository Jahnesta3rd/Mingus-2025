"""
Migration: Create Job Security Analysis Tables
Handles extending health_checkins, creating job security analysis tables,
employer analysis cache, and setting up proper indexes and relationships.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_job_security_analysis_tables'
down_revision = '004_fix_anon_access'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade database schema for job security analysis"""
    
    # 1. Extend existing health_checkins table with job security fields
    op.add_column('user_health_checkins', sa.Column('job_security_concern', sa.Integer(), nullable=True))
    op.add_column('user_health_checkins', sa.Column('career_stress_level', sa.Integer(), nullable=True))
    op.add_column('user_health_checkins', sa.Column('job_satisfaction_rating', sa.Integer(), nullable=True))
    op.add_column('user_health_checkins', sa.Column('workplace_stability_feeling', sa.Integer(), nullable=True))
    op.add_column('user_health_checkins', sa.Column('career_growth_confidence', sa.Integer(), nullable=True))
    op.add_column('user_health_checkins', sa.Column('employer_name', sa.String(255), nullable=True))
    op.add_column('user_health_checkins', sa.Column('industry_sector', sa.String(100), nullable=True))
    op.add_column('user_health_checkins', sa.Column('job_title', sa.String(255), nullable=True))
    
    # Add indexes for new job security fields
    op.create_index('idx_health_checkin_job_security', 'user_health_checkins', ['job_security_concern', 'career_stress_level'])
    op.create_index('idx_health_checkin_employer', 'user_health_checkins', ['employer_name', 'industry_sector'])
    
    # 2. Create job_security_analysis table
    op.create_table('job_security_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(), nullable=False),
        sa.Column('employer_name', sa.String(255), nullable=True),
        sa.Column('industry_sector', sa.String(100), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('user_perception_score', sa.Float(), nullable=False),
        sa.Column('external_data_score', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('layoff_probability_6m', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('positive_indicators', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('score_change', sa.Float(), nullable=True),
        sa.Column('trend_direction', sa.String(10), nullable=True),
        sa.Column('subscription_tier', sa.String(50), nullable=True),
        sa.Column('analysis_version', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add unique constraint for one analysis per user per day
    op.create_unique_constraint('uq_user_daily_analysis', 'job_security_analysis', ['user_id', 'analysis_date'])
    
    # Add indexes for performance
    op.create_index('idx_job_security_user_date', 'job_security_analysis', ['user_id', 'analysis_date'])
    op.create_index('idx_job_security_risk_level', 'job_security_analysis', ['risk_level', 'analysis_date'])
    op.create_index('idx_job_security_subscription', 'job_security_analysis', ['subscription_tier', 'analysis_date'])
    op.create_index('idx_job_security_employer', 'job_security_analysis', ['employer_name', 'industry_sector'])
    
    # 3. Create job_security_risk_factors table
    op.create_table('job_security_risk_factors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_score', sa.Float(), nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('data_points', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['job_security_analysis.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for risk factors
    op.create_index('idx_risk_factor_category', 'job_security_risk_factors', ['category', 'severity'])
    op.create_index('idx_risk_factor_analysis', 'job_security_risk_factors', ['analysis_id', 'impact_score'])
    
    # 4. Create job_security_recommendations table
    op.create_table('job_security_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('action_items', postgresql.JSONB(), nullable=True),
        sa.Column('personalization_score', sa.Float(), nullable=True),
        sa.Column('estimated_impact', sa.Float(), nullable=True),
        sa.Column('time_to_implement', sa.String(50), nullable=True),
        sa.Column('is_dismissed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['job_security_analysis.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for recommendations
    op.create_index('idx_recommendation_priority', 'job_security_recommendations', ['priority', 'personalization_score'])
    op.create_index('idx_recommendation_category', 'job_security_recommendations', ['category', 'analysis_id'])
    op.create_index('idx_recommendation_status', 'job_security_recommendations', ['is_dismissed', 'is_completed'])
    
    # 5. Create employer_analysis_cache table
    op.create_table('employer_analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('data_source', sa.String(100), nullable=False),
        sa.Column('cached_data', postgresql.JSONB(), nullable=False),
        sa.Column('data_hash', sa.String(64), nullable=True),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_valid', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('error_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('subscription_tier', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add unique constraint and indexes for cache
    op.create_unique_constraint('uq_employer_cache_key', 'employer_analysis_cache', ['cache_key'])
    op.create_index('idx_cache_data_type', 'employer_analysis_cache', ['data_type', 'expires_at'])
    op.create_index('idx_cache_access', 'employer_analysis_cache', ['last_accessed', 'access_count'])
    op.create_index('idx_cache_validity', 'employer_analysis_cache', ['is_valid', 'expires_at'])
    op.create_index('idx_cache_subscription', 'employer_analysis_cache', ['subscription_tier', 'data_type'])
    
    # 6. Add RLS policies for Supabase compatibility
    # Enable RLS on all new tables
    op.execute('ALTER TABLE job_security_analysis ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE job_security_risk_factors ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE job_security_recommendations ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE employer_analysis_cache ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policies for job_security_analysis
    op.execute("""
        CREATE POLICY "Users can view their own job security analysis" ON job_security_analysis
        FOR SELECT USING (auth.uid() = user_id)
    """)
    
    op.execute("""
        CREATE POLICY "Users can insert their own job security analysis" ON job_security_analysis
        FOR INSERT WITH CHECK (auth.uid() = user_id)
    """)
    
    op.execute("""
        CREATE POLICY "Users can update their own job security analysis" ON job_security_analysis
        FOR UPDATE USING (auth.uid() = user_id)
    """)
    
    # Create RLS policies for job_security_risk_factors
    op.execute("""
        CREATE POLICY "Users can view their own risk factors" ON job_security_risk_factors
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM job_security_analysis 
                WHERE job_security_analysis.id = job_security_risk_factors.analysis_id 
                AND job_security_analysis.user_id = auth.uid()
            )
        )
    """)
    
    # Create RLS policies for job_security_recommendations
    op.execute("""
        CREATE POLICY "Users can view their own recommendations" ON job_security_recommendations
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM job_security_analysis 
                WHERE job_security_analysis.id = job_security_recommendations.analysis_id 
                AND job_security_analysis.user_id = auth.uid()
            )
        )
    """)
    
    op.execute("""
        CREATE POLICY "Users can update their own recommendations" ON job_security_recommendations
        FOR UPDATE USING (
            EXISTS (
                SELECT 1 FROM job_security_analysis 
                WHERE job_security_analysis.id = job_security_recommendations.analysis_id 
                AND job_security_analysis.user_id = auth.uid()
            )
        )
    """)
    
    # Create RLS policies for employer_analysis_cache (read-only for users)
    op.execute("""
        CREATE POLICY "Users can view cached employer data" ON employer_analysis_cache
        FOR SELECT USING (is_valid = true AND expires_at > now())
    """)

def downgrade():
    """Downgrade database schema"""
    
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS "Users can view their own job security analysis" ON job_security_analysis')
    op.execute('DROP POLICY IF EXISTS "Users can insert their own job security analysis" ON job_security_analysis')
    op.execute('DROP POLICY IF EXISTS "Users can update their own job security analysis" ON job_security_analysis')
    op.execute('DROP POLICY IF EXISTS "Users can view their own risk factors" ON job_security_risk_factors')
    op.execute('DROP POLICY IF EXISTS "Users can view their own recommendations" ON job_security_recommendations')
    op.execute('DROP POLICY IF EXISTS "Users can update their own recommendations" ON job_security_recommendations')
    op.execute('DROP POLICY IF EXISTS "Users can view cached employer data" ON employer_analysis_cache')
    
    # Drop tables
    op.drop_table('employer_analysis_cache')
    op.drop_table('job_security_recommendations')
    op.drop_table('job_security_risk_factors')
    op.drop_table('job_security_analysis')
    
    # Drop indexes from health_checkins
    op.drop_index('idx_health_checkin_job_security', table_name='user_health_checkins')
    op.drop_index('idx_health_checkin_employer', table_name='user_health_checkins')
    
    # Drop columns from health_checkins
    op.drop_column('user_health_checkins', 'job_security_concern')
    op.drop_column('user_health_checkins', 'career_stress_level')
    op.drop_column('user_health_checkins', 'job_satisfaction_rating')
    op.drop_column('user_health_checkins', 'workplace_stability_feeling')
    op.drop_column('user_health_checkins', 'career_growth_confidence')
    op.drop_column('user_health_checkins', 'employer_name')
    op.drop_column('user_health_checkins', 'industry_sector')
    op.drop_column('user_health_checkins', 'job_title') 