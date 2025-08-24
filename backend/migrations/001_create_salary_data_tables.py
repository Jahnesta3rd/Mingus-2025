"""
Migration: Create Salary Data Tables
Adds new tables for salary benchmarks, market data, and confidence scores
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001_create_salary_data_tables'
down_revision = None  # Set to the latest migration in your existing schema
depends_on = None

def upgrade():
    """Create new salary data tables"""
    
    # Create salary_benchmarks table
    op.create_table(
        'salary_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('occupation', sa.String(200), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),  # BLS, Census, FRED, Indeed, Fallback
        sa.Column('median_salary', sa.Numeric(10, 2), nullable=False),
        sa.Column('mean_salary', sa.Numeric(10, 2), nullable=False),
        sa.Column('percentile_25', sa.Numeric(10, 2), nullable=False),
        sa.Column('percentile_75', sa.Numeric(10, 2), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('data_quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('validation_level', sa.String(20), nullable=True),  # HIGH, MEDIUM, LOW, INVALID
        sa.Column('outliers_detected', sa.Integer(), nullable=True),
        sa.Column('cache_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_salary_benchmarks_location', 'location'),
        sa.Index('idx_salary_benchmarks_occupation', 'occupation'),
        sa.Index('idx_salary_benchmarks_source', 'source'),
        sa.Index('idx_salary_benchmarks_year', 'year'),
        sa.Index('idx_salary_benchmarks_confidence', 'confidence_score'),
        sa.Index('idx_salary_benchmarks_cache_key', 'cache_key')
    )
    
    # Create market_data table
    op.create_table(
        'market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('occupation', sa.String(200), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=False),  # cost_of_living, job_market
        sa.Column('overall_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('housing_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('transportation_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('food_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('healthcare_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('utilities_cost_index', sa.Numeric(5, 2), nullable=True),
        sa.Column('job_count', sa.Integer(), nullable=True),
        sa.Column('average_salary', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_range_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_range_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('demand_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('data_quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('validation_level', sa.String(20), nullable=True),
        sa.Column('cache_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_market_data_location', 'location'),
        sa.Index('idx_market_data_occupation', 'occupation'),
        sa.Index('idx_market_data_type', 'data_type'),
        sa.Index('idx_market_data_year', 'year'),
        sa.Index('idx_market_data_cache_key', 'cache_key')
    )
    
    # Create confidence_scores table
    op.create_table(
        'confidence_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('occupation', sa.String(200), nullable=True),
        sa.Column('overall_confidence_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('data_quality_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('salary_data_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('cost_of_living_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('job_market_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('validation_issues_count', sa.Integer(), nullable=True),
        sa.Column('validation_warnings_count', sa.Integer(), nullable=True),
        sa.Column('outliers_count', sa.Integer(), nullable=True),
        sa.Column('data_sources_count', sa.Integer(), nullable=True),
        sa.Column('last_validation_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_confidence_scores_location', 'location'),
        sa.Index('idx_confidence_scores_occupation', 'occupation'),
        sa.Index('idx_confidence_scores_overall', 'overall_confidence_score'),
        sa.Index('idx_confidence_scores_quality', 'data_quality_score')
    )
    
    # Create data_refresh_logs table for tracking background tasks
    op.create_table(
        'data_refresh_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),  # refresh_all, refresh_location, validate, cleanup
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('occupation', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # started, completed, failed
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable True),
        sa.Column('errors_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_data_refresh_logs_task_type', 'task_type'),
        sa.Index('idx_data_refresh_logs_status', 'status'),
        sa.Index('idx_data_refresh_logs_started_at', 'started_at'),
        sa.Index('idx_data_refresh_logs_celery_task_id', 'celery_task_id')
    )
    
    # Create cache_metrics table for Redis monitoring
    op.create_table(
        'cache_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key_pattern', sa.String(255), nullable=False),
        sa.Column('hits', sa.BigInteger(), nullable=False, default=0),
        sa.Column('misses', sa.BigInteger(), nullable=False, default=0),
        sa.Column('hit_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('avg_response_time_ms', sa.Numeric(8, 2), nullable=True),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('entries_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_cache_metrics_pattern', 'cache_key_pattern'),
        sa.Index('idx_cache_metrics_hit_rate', 'hit_rate'),
        sa.Index('idx_cache_metrics_last_accessed', 'last_accessed_at')
    )

def downgrade():
    """Drop the new tables"""
    op.drop_table('cache_metrics')
    op.drop_table('data_refresh_logs')
    op.drop_table('confidence_scores')
    op.drop_table('market_data')
    op.drop_table('salary_benchmarks') 