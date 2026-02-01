"""Add housing location tables

Revision ID: 005_add_housing_location_tables
Revises: 004_add_vehicle_management_tables
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '005_add_housing_location_tables'
down_revision = '004_add_vehicle_management_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add housing location tables to the Mingus application.
    
    Creates four new tables:
    1. housing_searches - User housing search criteria and results
    2. housing_scenarios - Specific housing options with analysis
    3. user_housing_preferences - User's housing preferences and criteria
    4. commute_route_cache - Google Maps API route caching
    """
    
    # ============================================================================
    # HOUSING_SEARCHES TABLE
    # ============================================================================
    
    # Create housing_searches table
    op.create_table('housing_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('search_criteria', sa.JSON(), nullable=False),
        sa.Column('msa_area', sa.String(length=100), nullable=False),
        sa.Column('lease_end_date', sa.Date(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('results_count >= 0', name='check_positive_results_count')
    )
    
    # Create indexes for housing_searches table
    op.create_index('idx_housing_searches_user_id', 'housing_searches', ['user_id'])
    op.create_index('idx_housing_searches_msa_area', 'housing_searches', ['msa_area'])
    op.create_index('idx_housing_searches_user_msa', 'housing_searches', ['user_id', 'msa_area'])
    op.create_index('idx_housing_searches_created_at', 'housing_searches', ['created_at'])
    op.create_index('idx_housing_searches_lease_end', 'housing_searches', ['lease_end_date'])
    
    # ============================================================================
    # HOUSING_SCENARIOS TABLE
    # ============================================================================
    
    # Create housing_scenarios table
    op.create_table('housing_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=255), nullable=False),
        sa.Column('housing_data', sa.JSON(), nullable=False),
        sa.Column('commute_data', sa.JSON(), nullable=False),
        sa.Column('financial_impact', sa.JSON(), nullable=False),
        sa.Column('career_data', sa.JSON(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for housing_scenarios table
    op.create_index('idx_housing_scenarios_user_id', 'housing_scenarios', ['user_id'])
    op.create_index('idx_housing_scenarios_is_favorite', 'housing_scenarios', ['is_favorite'])
    op.create_index('idx_housing_scenarios_user_favorite', 'housing_scenarios', ['user_id', 'is_favorite'])
    op.create_index('idx_housing_scenarios_created_at', 'housing_scenarios', ['created_at'])
    op.create_index('idx_housing_scenarios_name', 'housing_scenarios', ['scenario_name'])
    
    # ============================================================================
    # USER_HOUSING_PREFERENCES TABLE
    # ============================================================================
    
    # Create user_housing_preferences table
    op.create_table('user_housing_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('max_commute_time', sa.Integer(), nullable=True),
        sa.Column('preferred_housing_type', sa.Enum('apartment', 'house', 'condo', name='housingtype'), nullable=True),
        sa.Column('min_bedrooms', sa.Integer(), nullable=True),
        sa.Column('max_bedrooms', sa.Integer(), nullable=True),
        sa.Column('max_rent_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('preferred_neighborhoods', sa.JSON(), nullable=True),  # SQLite-compatible (ARRAY on PG)
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('user_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('max_commute_time >= 0', name='check_positive_commute_time'),
        sa.CheckConstraint('min_bedrooms >= 0', name='check_positive_min_bedrooms'),
        sa.CheckConstraint('max_bedrooms >= 0', name='check_positive_max_bedrooms'),
        sa.CheckConstraint('min_bedrooms <= max_bedrooms', name='check_bedroom_range'),
        sa.CheckConstraint('max_rent_percentage >= 0 AND max_rent_percentage <= 100', name='check_rent_percentage_range')
    )
    
    # Create indexes for user_housing_preferences table
    op.create_index('idx_housing_prefs_commute_time', 'user_housing_preferences', ['max_commute_time'])
    op.create_index('idx_housing_prefs_housing_type', 'user_housing_preferences', ['preferred_housing_type'])
    op.create_index('idx_housing_prefs_rent_percentage', 'user_housing_preferences', ['max_rent_percentage'])
    op.create_index('idx_housing_prefs_updated_at', 'user_housing_preferences', ['updated_at'])
    
    # ============================================================================
    # COMMUTE_ROUTE_CACHE TABLE
    # ============================================================================
    
    # Create commute_route_cache table
    op.create_table('commute_route_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('origin_zip', sa.String(length=10), nullable=False),
        sa.Column('destination_zip', sa.String(length=10), nullable=False),
        sa.Column('distance_miles', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('drive_time_minutes', sa.Integer(), nullable=False),
        sa.Column('traffic_factor', sa.Numeric(precision=3, scale=2), nullable=False, default=1.0),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('distance_miles >= 0', name='check_positive_distance'),
        sa.CheckConstraint('drive_time_minutes >= 0', name='check_positive_drive_time'),
        sa.CheckConstraint('traffic_factor >= 0.1 AND traffic_factor <= 3.0', name='check_traffic_factor_range')
    )
    
    # Create indexes for commute_route_cache table
    op.create_index('idx_commute_cache_origin_zip', 'commute_route_cache', ['origin_zip'])
    op.create_index('idx_commute_cache_destination_zip', 'commute_route_cache', ['destination_zip'])
    op.create_index('idx_commute_cache_route', 'commute_route_cache', ['origin_zip', 'destination_zip'])
    op.create_index('idx_commute_cache_last_updated', 'commute_route_cache', ['last_updated'])
    op.create_index('idx_commute_cache_distance', 'commute_route_cache', ['distance_miles'])
    
    # ============================================================================
    # ADD TRIGGERS FOR UPDATED_AT
    # ============================================================================
    
    # Create trigger to update updated_at on user_housing_preferences table
    op.execute('''
        CREATE TRIGGER IF NOT EXISTS update_housing_preferences_updated_at
        AFTER UPDATE ON user_housing_preferences
        BEGIN
            UPDATE user_housing_preferences SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
        END
    ''')


def downgrade():
    """
    Remove housing location tables from the Mingus application.
    
    Drops the four housing location tables in reverse order:
    1. commute_route_cache
    2. user_housing_preferences
    3. housing_scenarios
    4. housing_searches
    """
    
    # ============================================================================
    # DROP TRIGGERS
    # ============================================================================
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_housing_preferences_updated_at')
    
    # ============================================================================
    # DROP TABLES IN REVERSE ORDER
    # ============================================================================
    
    # Drop commute_route_cache table (no foreign key dependencies)
    op.drop_table('commute_route_cache')
    
    # Drop user_housing_preferences table
    op.drop_table('user_housing_preferences')
    
    # Drop housing_scenarios table
    op.drop_table('housing_scenarios')
    
    # Drop housing_searches table
    op.drop_table('housing_searches')
    
    # Drop the housing type enum
    op.execute('DROP TYPE IF EXISTS housingtype')
    
    # Note: Indexes are automatically dropped when tables are dropped
    # Foreign key constraints are also automatically handled
