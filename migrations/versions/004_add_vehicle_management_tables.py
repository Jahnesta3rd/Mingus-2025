"""Add vehicle management tables

Revision ID: 004_add_vehicle_management_tables
Revises: 003_seed_initial_data
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004_add_vehicle_management_tables'
down_revision = '003_seed_initial_data'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add vehicle management tables to the Mingus application.
    
    Creates four new tables:
    1. vehicles - User vehicle information
    2. maintenance_predictions - Predictive maintenance tracking
    3. commute_scenarios - Job location commute analysis
    4. msa_gas_prices - Gas prices by Metropolitan Statistical Area
    """
    
    # ============================================================================
    # VEHICLES TABLE
    # ============================================================================
    
    # Create vehicles table
    op.create_table('vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vin', sa.String(length=17), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('make', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('trim', sa.String(length=100), nullable=True),
        sa.Column('current_mileage', sa.Integer(), nullable=False, default=0),
        sa.Column('monthly_miles', sa.Integer(), nullable=False, default=0),
        sa.Column('user_zipcode', sa.String(length=10), nullable=False),
        sa.Column('assigned_msa', sa.String(length=100), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('current_mileage >= 0', name='check_positive_mileage'),
        sa.CheckConstraint('monthly_miles >= 0', name='check_positive_monthly_miles'),
        sa.CheckConstraint('year >= 1900 AND year <= 2030', name='check_valid_year'),
        sa.CheckConstraint('LENGTH(vin) = 17', name='check_vin_length')
    )
    
    # Create indexes for vehicles table
    op.create_index('idx_vehicles_user_id', 'vehicles', ['user_id'])
    op.create_index('idx_vehicles_vin', 'vehicles', ['vin'], unique=True)
    op.create_index('idx_vehicles_make', 'vehicles', ['make'])
    op.create_index('idx_vehicles_model', 'vehicles', ['model'])
    op.create_index('idx_vehicles_zipcode', 'vehicles', ['user_zipcode'])
    op.create_index('idx_vehicles_msa', 'vehicles', ['assigned_msa'])
    op.create_index('idx_vehicles_user_year', 'vehicles', ['user_id', 'year'])
    op.create_index('idx_vehicles_make_model', 'vehicles', ['make', 'model'])
    op.create_index('idx_vehicles_msa_zipcode', 'vehicles', ['assigned_msa', 'user_zipcode'])
    
    # ============================================================================
    # MAINTENANCE_PREDICTIONS TABLE
    # ============================================================================
    
    # Create maintenance_predictions table
    op.create_table('maintenance_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('predicted_date', sa.Date(), nullable=False),
        sa.Column('predicted_mileage', sa.Integer(), nullable=False),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False, default=0.0),
        sa.Column('is_routine', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.CheckConstraint('probability >= 0.0 AND probability <= 1.0', name='check_probability_range'),
        sa.CheckConstraint('estimated_cost >= 0', name='check_positive_cost'),
        sa.CheckConstraint('predicted_mileage >= 0', name='check_positive_predicted_mileage')
    )
    
    # Create indexes for maintenance_predictions table
    op.create_index('idx_maintenance_vehicle_id', 'maintenance_predictions', ['vehicle_id'])
    op.create_index('idx_maintenance_service_type', 'maintenance_predictions', ['service_type'])
    op.create_index('idx_maintenance_predicted_date', 'maintenance_predictions', ['predicted_date'])
    op.create_index('idx_maintenance_routine', 'maintenance_predictions', ['is_routine'])
    op.create_index('idx_maintenance_vehicle_date', 'maintenance_predictions', ['vehicle_id', 'predicted_date'])
    op.create_index('idx_maintenance_created_date', 'maintenance_predictions', ['created_date'])
    
    # ============================================================================
    # COMMUTE_SCENARIOS TABLE
    # ============================================================================
    
    # Create commute_scenarios table
    op.create_table('commute_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('job_location', sa.String(length=255), nullable=False),
        sa.Column('job_zipcode', sa.String(length=10), nullable=False),
        sa.Column('distance_miles', sa.Float(), nullable=False),
        sa.Column('daily_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('monthly_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('gas_price_per_gallon', sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column('vehicle_mpg', sa.Float(), nullable=False),
        sa.Column('from_msa', sa.String(length=100), nullable=True),
        sa.Column('to_msa', sa.String(length=100), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.CheckConstraint('distance_miles >= 0', name='check_positive_distance'),
        sa.CheckConstraint('daily_cost >= 0', name='check_positive_daily_cost'),
        sa.CheckConstraint('monthly_cost >= 0', name='check_positive_monthly_cost'),
        sa.CheckConstraint('gas_price_per_gallon >= 0', name='check_positive_gas_price'),
        sa.CheckConstraint('vehicle_mpg > 0', name='check_positive_mpg')
    )
    
    # Create indexes for commute_scenarios table
    op.create_index('idx_commute_vehicle_id', 'commute_scenarios', ['vehicle_id'])
    op.create_index('idx_commute_job_zipcode', 'commute_scenarios', ['job_zipcode'])
    op.create_index('idx_commute_from_msa', 'commute_scenarios', ['from_msa'])
    op.create_index('idx_commute_to_msa', 'commute_scenarios', ['to_msa'])
    op.create_index('idx_commute_monthly_cost', 'commute_scenarios', ['monthly_cost'])
    op.create_index('idx_commute_vehicle_zipcode', 'commute_scenarios', ['vehicle_id', 'job_zipcode'])
    op.create_index('idx_commute_msa_route', 'commute_scenarios', ['from_msa', 'to_msa'])
    op.create_index('idx_commute_created_date', 'commute_scenarios', ['created_date'])
    
    # ============================================================================
    # MSA_GAS_PRICES TABLE
    # ============================================================================
    
    # Create msa_gas_prices table
    op.create_table('msa_gas_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('msa_name', sa.String(length=100), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('current_price >= 0', name='check_positive_price')
    )
    
    # Create indexes for msa_gas_prices table
    op.create_index('idx_msa_gas_prices_name', 'msa_gas_prices', ['msa_name'], unique=True)
    op.create_index('idx_msa_gas_prices_last_updated', 'msa_gas_prices', ['last_updated'])
    op.create_index('idx_msa_gas_prices_price', 'msa_gas_prices', ['current_price'])
    
    # ============================================================================
    # ADD TRIGGERS FOR UPDATED_DATE
    # ============================================================================
    
    # Create trigger to update updated_date on vehicles table
    op.execute('''
        CREATE TRIGGER IF NOT EXISTS update_vehicles_updated_date
        AFTER UPDATE ON vehicles
        BEGIN
            UPDATE vehicles SET updated_date = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    # ============================================================================
    # INSERT INITIAL DATA
    # ============================================================================
    
    # Insert initial MSA gas prices with common MSAs
    op.execute('''
        INSERT INTO msa_gas_prices (msa_name, current_price, last_updated)
        VALUES 
            ('National Average', 3.45, CURRENT_TIMESTAMP),
            ('Los Angeles-Long Beach-Anaheim, CA', 4.25, CURRENT_TIMESTAMP),
            ('New York-Newark-Jersey City, NY-NJ-PA', 3.85, CURRENT_TIMESTAMP),
            ('Chicago-Naperville-Elgin, IL-IN-WI', 3.65, CURRENT_TIMESTAMP),
            ('Houston-The Woodlands-Sugar Land, TX', 3.15, CURRENT_TIMESTAMP),
            ('Phoenix-Mesa-Scottsdale, AZ', 3.55, CURRENT_TIMESTAMP),
            ('Philadelphia-Camden-Wilmington, PA-NJ-DE-MD', 3.75, CURRENT_TIMESTAMP),
            ('San Antonio-New Braunfels, TX', 3.25, CURRENT_TIMESTAMP),
            ('San Diego-Carlsbad, CA', 4.15, CURRENT_TIMESTAMP),
            ('Dallas-Fort Worth-Arlington, TX', 3.35, CURRENT_TIMESTAMP)
    ''')


def downgrade():
    """
    Remove vehicle management tables from the Mingus application.
    
    Drops the four vehicle management tables in reverse order:
    1. msa_gas_prices
    2. commute_scenarios  
    3. maintenance_predictions
    4. vehicles
    """
    
    # ============================================================================
    # DROP TRIGGERS
    # ============================================================================
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_vehicles_updated_date')
    
    # ============================================================================
    # DROP TABLES IN REVERSE ORDER
    # ============================================================================
    
    # Drop msa_gas_prices table (no foreign key dependencies)
    op.drop_table('msa_gas_prices')
    
    # Drop commute_scenarios table
    op.drop_table('commute_scenarios')
    
    # Drop maintenance_predictions table
    op.drop_table('maintenance_predictions')
    
    # Drop vehicles table
    op.drop_table('vehicles')
    
    # Note: Indexes are automatically dropped when tables are dropped
    # Foreign key constraints are also automatically handled
