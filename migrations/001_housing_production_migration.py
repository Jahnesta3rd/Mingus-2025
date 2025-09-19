#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Production Database Migration

Production migration script for housing location feature with:
- Index optimization for housing search queries
- Data retention policies implementation
- Performance optimizations
- Backup strategy setup
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import text, Index, CheckConstraint
from sqlalchemy.exc import SQLAlchemyError
from alembic import op
import sqlalchemy as sa

# Configure logging
logger = logging.getLogger(__name__)

def upgrade():
    """Upgrade database schema for production housing feature"""
    logger.info("Starting housing production migration")
    
    try:
        # Create housing tables if they don't exist
        _create_housing_tables()
        
        # Add production indexes
        _add_production_indexes()
        
        # Add data retention constraints
        _add_retention_constraints()
        
        # Create performance optimization views
        _create_performance_views()
        
        # Setup backup triggers
        _setup_backup_triggers()
        
        logger.info("Housing production migration completed successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Migration failed: {e}")
        raise

def downgrade():
    """Downgrade database schema"""
    logger.info("Starting housing production migration rollback")
    
    try:
        # Remove backup triggers
        _remove_backup_triggers()
        
        # Drop performance views
        _drop_performance_views()
        
        # Remove retention constraints
        _remove_retention_constraints()
        
        # Remove production indexes
        _remove_production_indexes()
        
        logger.info("Housing production migration rollback completed")
        
    except SQLAlchemyError as e:
        logger.error(f"Migration rollback failed: {e}")
        raise

def _create_housing_tables():
    """Create housing tables with production optimizations"""
    
    # Housing searches table
    op.create_table(
        'housing_searches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('search_criteria', sa.JSON(), nullable=False),
        sa.Column('msa_area', sa.String(100), nullable=False),
        sa.Column('lease_end_date', sa.Date(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Housing scenarios table
    op.create_table(
        'housing_scenarios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(255), nullable=False),
        sa.Column('housing_data', sa.JSON(), nullable=False),
        sa.Column('commute_data', sa.JSON(), nullable=False),
        sa.Column('financial_impact', sa.JSON(), nullable=False),
        sa.Column('career_data', sa.JSON(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # User housing preferences table
    op.create_table(
        'user_housing_preferences',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('max_commute_time', sa.Integer(), nullable=True),
        sa.Column('preferred_housing_type', sa.String(50), nullable=True),
        sa.Column('min_bedrooms', sa.Integer(), nullable=True),
        sa.Column('max_bedrooms', sa.Integer(), nullable=True),
        sa.Column('max_rent_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('preferred_neighborhoods', sa.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Commute route cache table
    op.create_table(
        'commute_route_cache',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('origin_zip', sa.String(10), nullable=False),
        sa.Column('destination_zip', sa.String(10), nullable=False),
        sa.Column('distance_miles', sa.Numeric(8, 2), nullable=False),
        sa.Column('drive_time_minutes', sa.Integer(), nullable=False),
        sa.Column('traffic_factor', sa.Numeric(3, 2), nullable=False, default=1.0),
        sa.Column('last_updated', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('access_count', sa.Integer(), nullable=False, default=0),
    )
    
    logger.info("Housing tables created")

def _add_production_indexes():
    """Add production-optimized indexes for housing queries"""
    
    # Housing searches indexes
    op.create_index('idx_housing_searches_user_created', 'housing_searches', ['user_id', 'created_at'])
    op.create_index('idx_housing_searches_msa_created', 'housing_searches', ['msa_area', 'created_at'])
    op.create_index('idx_housing_searches_lease_end', 'housing_searches', ['lease_end_date'])
    op.create_index('idx_housing_searches_deleted', 'housing_searches', ['is_deleted'])
    
    # Housing scenarios indexes
    op.create_index('idx_housing_scenarios_user_favorite', 'housing_scenarios', ['user_id', 'is_favorite'])
    op.create_index('idx_housing_scenarios_created', 'housing_scenarios', ['created_at'])
    op.create_index('idx_housing_scenarios_name', 'housing_scenarios', ['scenario_name'])
    op.create_index('idx_housing_scenarios_deleted', 'housing_scenarios', ['is_deleted'])
    
    # User preferences indexes
    op.create_index('idx_housing_prefs_commute_time', 'user_housing_preferences', ['max_commute_time'])
    op.create_index('idx_housing_prefs_housing_type', 'user_housing_preferences', ['preferred_housing_type'])
    op.create_index('idx_housing_prefs_rent_percentage', 'user_housing_preferences', ['max_rent_percentage'])
    
    # Commute route cache indexes
    op.create_index('idx_commute_cache_route', 'commute_route_cache', ['origin_zip', 'destination_zip'])
    op.create_index('idx_commute_cache_last_updated', 'commute_route_cache', ['last_updated'])
    op.create_index('idx_commute_cache_access_count', 'commute_route_cache', ['access_count'])
    
    # Composite indexes for complex queries
    op.create_index('idx_housing_searches_user_msa_created', 'housing_searches', 
                   ['user_id', 'msa_area', 'created_at'])
    op.create_index('idx_housing_scenarios_user_created_favorite', 'housing_scenarios', 
                   ['user_id', 'created_at', 'is_favorite'])
    
    logger.info("Production indexes created")

def _add_retention_constraints():
    """Add data retention constraints and triggers"""
    
    # Add check constraints for data validation
    op.create_check_constraint(
        'check_positive_commute_time',
        'user_housing_preferences',
        'max_commute_time >= 0'
    )
    
    op.create_check_constraint(
        'check_positive_bedrooms',
        'user_housing_preferences',
        'min_bedrooms >= 0 AND max_bedrooms >= 0'
    )
    
    op.create_check_constraint(
        'check_bedroom_range',
        'user_housing_preferences',
        'min_bedrooms <= max_bedrooms'
    )
    
    op.create_check_constraint(
        'check_rent_percentage_range',
        'user_housing_preferences',
        'max_rent_percentage >= 0 AND max_rent_percentage <= 100'
    )
    
    op.create_check_constraint(
        'check_positive_distance',
        'commute_route_cache',
        'distance_miles >= 0'
    )
    
    op.create_check_constraint(
        'check_positive_drive_time',
        'commute_route_cache',
        'drive_time_minutes >= 0'
    )
    
    op.create_check_constraint(
        'check_traffic_factor_range',
        'commute_route_cache',
        'traffic_factor >= 0.1 AND traffic_factor <= 3.0'
    )
    
    logger.info("Retention constraints added")

def _create_performance_views():
    """Create performance optimization views"""
    
    # View for active housing searches (not deleted)
    op.execute("""
        CREATE VIEW active_housing_searches AS
        SELECT 
            id,
            user_id,
            search_criteria,
            msa_area,
            lease_end_date,
            results_count,
            created_at
        FROM housing_searches
        WHERE is_deleted = false
    """)
    
    # View for user's favorite scenarios
    op.execute("""
        CREATE VIEW user_favorite_scenarios AS
        SELECT 
            id,
            user_id,
            scenario_name,
            housing_data,
            commute_data,
            financial_impact,
            career_data,
            created_at
        FROM housing_scenarios
        WHERE is_favorite = true AND is_deleted = false
    """)
    
    # View for recent searches with user info
    op.execute("""
        CREATE VIEW recent_housing_activity AS
        SELECT 
            hs.id,
            hs.user_id,
            u.email,
            hs.msa_area,
            hs.results_count,
            hs.created_at,
            CASE 
                WHEN hs.created_at > NOW() - INTERVAL '7 days' THEN 'recent'
                WHEN hs.created_at > NOW() - INTERVAL '30 days' THEN 'monthly'
                ELSE 'older'
            END as activity_period
        FROM housing_searches hs
        JOIN users u ON hs.user_id = u.id
        WHERE hs.is_deleted = false
        ORDER BY hs.created_at DESC
    """)
    
    # View for commute route statistics
    op.execute("""
        CREATE VIEW commute_route_stats AS
        SELECT 
            origin_zip,
            destination_zip,
            AVG(distance_miles) as avg_distance,
            AVG(drive_time_minutes) as avg_drive_time,
            AVG(traffic_factor) as avg_traffic_factor,
            COUNT(*) as usage_count,
            MAX(last_updated) as last_used
        FROM commute_route_cache
        GROUP BY origin_zip, destination_zip
        HAVING COUNT(*) > 1
    """)
    
    logger.info("Performance views created")

def _setup_backup_triggers():
    """Setup backup triggers for data retention"""
    
    # Function to clean up old housing searches
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_housing_searches()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Soft delete searches older than 1 year
            UPDATE housing_searches 
            SET is_deleted = true 
            WHERE created_at < NOW() - INTERVAL '1 year' 
            AND is_deleted = false;
            
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Function to clean up old route cache
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_route_cache()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Delete route cache older than 30 days
            DELETE FROM commute_route_cache 
            WHERE last_updated < NOW() - INTERVAL '30 days';
            
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers
    op.execute("""
        CREATE TRIGGER trigger_cleanup_housing_searches
        AFTER INSERT ON housing_searches
        FOR EACH STATEMENT
        EXECUTE FUNCTION cleanup_old_housing_searches();
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_cleanup_route_cache
        AFTER INSERT ON commute_route_cache
        FOR EACH STATEMENT
        EXECUTE FUNCTION cleanup_old_route_cache();
    """)
    
    logger.info("Backup triggers created")

def _remove_backup_triggers():
    """Remove backup triggers"""
    op.execute("DROP TRIGGER IF EXISTS trigger_cleanup_housing_searches ON housing_searches;")
    op.execute("DROP TRIGGER IF EXISTS trigger_cleanup_route_cache ON commute_route_cache;")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_housing_searches();")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_route_cache();")
    
    logger.info("Backup triggers removed")

def _drop_performance_views():
    """Drop performance views"""
    op.execute("DROP VIEW IF EXISTS active_housing_searches;")
    op.execute("DROP VIEW IF EXISTS user_favorite_scenarios;")
    op.execute("DROP VIEW IF EXISTS recent_housing_activity;")
    op.execute("DROP VIEW IF EXISTS commute_route_stats;")
    
    logger.info("Performance views dropped")

def _remove_retention_constraints():
    """Remove retention constraints"""
    op.drop_constraint('check_positive_commute_time', 'user_housing_preferences')
    op.drop_constraint('check_positive_bedrooms', 'user_housing_preferences')
    op.drop_constraint('check_bedroom_range', 'user_housing_preferences')
    op.drop_constraint('check_rent_percentage_range', 'user_housing_preferences')
    op.drop_constraint('check_positive_distance', 'commute_route_cache')
    op.drop_constraint('check_positive_drive_time', 'commute_route_cache')
    op.drop_constraint('check_traffic_factor_range', 'commute_route_cache')
    
    logger.info("Retention constraints removed")

def _remove_production_indexes():
    """Remove production indexes"""
    op.drop_index('idx_housing_searches_user_created', 'housing_searches')
    op.drop_index('idx_housing_searches_msa_created', 'housing_searches')
    op.drop_index('idx_housing_searches_lease_end', 'housing_searches')
    op.drop_index('idx_housing_searches_deleted', 'housing_searches')
    op.drop_index('idx_housing_scenarios_user_favorite', 'housing_scenarios')
    op.drop_index('idx_housing_scenarios_created', 'housing_scenarios')
    op.drop_index('idx_housing_scenarios_name', 'housing_scenarios')
    op.drop_index('idx_housing_scenarios_deleted', 'housing_scenarios')
    op.drop_index('idx_housing_prefs_commute_time', 'user_housing_preferences')
    op.drop_index('idx_housing_prefs_housing_type', 'user_housing_preferences')
    op.drop_index('idx_housing_prefs_rent_percentage', 'user_housing_preferences')
    op.drop_index('idx_commute_cache_route', 'commute_route_cache')
    op.drop_index('idx_commute_cache_last_updated', 'commute_route_cache')
    op.drop_index('idx_commute_cache_access_count', 'commute_route_cache')
    op.drop_index('idx_housing_searches_user_msa_created', 'housing_searches')
    op.drop_index('idx_housing_scenarios_user_created_favorite', 'housing_scenarios')
    
    logger.info("Production indexes removed")
