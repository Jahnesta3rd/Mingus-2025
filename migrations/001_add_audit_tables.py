"""Migration: Add Comprehensive Audit Tables

Revision ID: 001_add_audit_tables
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP, TEXT, INTEGER, BOOLEAN, VARCHAR, BYTEA
import uuid

# revision identifiers, used by Alembic.
revision = '001_add_audit_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comprehensive audit tables with performance optimizations."""
    
    # Create audit_events table - Main audit log with JSONB optimization
    op.create_table(
        'audit_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('event_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('event_type', VARCHAR(100), nullable=False, index=True),
        sa.Column('event_category', VARCHAR(50), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('correlation_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('ip_address', VARCHAR(45), nullable=False, index=True),
        sa.Column('user_agent', TEXT, nullable=True),
        sa.Column('request_method', VARCHAR(10), nullable=True),
        sa.Column('request_path', VARCHAR(500), nullable=True),
        sa.Column('request_headers', JSONB, nullable=True),
        sa.Column('request_body', JSONB, nullable=True),
        sa.Column('response_status', INTEGER, nullable=True),
        sa.Column('response_body', JSONB, nullable=True),
        sa.Column('execution_time_ms', INTEGER, nullable=True),
        sa.Column('success', BOOLEAN, nullable=False, default=True),
        sa.Column('error_message', TEXT, nullable=True),
        sa.Column('error_stack_trace', TEXT, nullable=True),
        sa.Column('risk_level', VARCHAR(20), nullable=False, default='LOW', index=True),
        sa.Column('threat_score', INTEGER, nullable=True, index=True),
        sa.Column('country_code', VARCHAR(2), nullable=True, index=True),
        sa.Column('city', VARCHAR(100), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('partition_date', sa.Date, nullable=False, server_default=sa.func.current_date())
    )
    
    # Create audit_data_access table - Track data access patterns
    op.create_table(
        'audit_data_access',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('access_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('data_type', VARCHAR(100), nullable=False, index=True),
        sa.Column('data_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('access_method', VARCHAR(50), nullable=False, index=True),
        sa.Column('access_purpose', VARCHAR(200), nullable=True),
        sa.Column('data_sensitivity', VARCHAR(50), nullable=False, index=True),
        sa.Column('access_granted', BOOLEAN, nullable=False),
        sa.Column('access_reason', VARCHAR(255), nullable=True),
        sa.Column('ip_address', VARCHAR(45), nullable=False, index=True),
        sa.Column('session_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('request_headers', JSONB, nullable=True),
        sa.Column('access_details', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('partition_date', sa.Date, nullable=False, server_default=sa.func.current_date())
    )
    
    # Create audit_security_events table - Security-specific audit trail
    op.create_table(
        'audit_security_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('event_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('event_type', VARCHAR(100), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('ip_address', VARCHAR(45), nullable=False, index=True),
        sa.Column('session_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('threat_type', VARCHAR(100), nullable=True, index=True),
        sa.Column('threat_level', VARCHAR(20), nullable=False, default='LOW', index=True),
        sa.Column('threat_score', INTEGER, nullable=True, index=True),
        sa.Column('blocked', BOOLEAN, nullable=False, default=False),
        sa.Column('block_reason', VARCHAR(255), nullable=True),
        sa.Column('request_details', JSONB, nullable=True),
        sa.Column('response_action', VARCHAR(100), nullable=True),
        sa.Column('mitigation_applied', VARCHAR(200), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('partition_date', sa.Date, nullable=False, server_default=sa.func.current_date())
    )
    
    # Create audit_compliance table - Compliance and regulatory tracking
    op.create_table(
        'audit_compliance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('compliance_date', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('regulation_type', VARCHAR(100), nullable=False, index=True),
        sa.Column('requirement_id', VARCHAR(50), nullable=False, index=True),
        sa.Column('requirement_name', VARCHAR(255), nullable=False),
        sa.Column('requirement_description', TEXT, nullable=True),
        sa.Column('compliance_status', VARCHAR(50), nullable=False, index=True),
        sa.Column('assessment_method', VARCHAR(100), nullable=True),
        sa.Column('assessor', VARCHAR(255), nullable=True),
        sa.Column('assessment_notes', TEXT, nullable=True),
        sa.Column('next_assessment_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('compliance_evidence', JSONB, nullable=True),
        sa.Column('violations_found', JSONB, nullable=True),
        sa.Column('remediation_actions', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create audit_retention table - Data retention and deletion tracking
    op.create_table(
        'audit_retention',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('retention_date', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('data_type', VARCHAR(100), nullable=False, index=True),
        sa.Column('data_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('retention_policy', VARCHAR(100), nullable=False, index=True),
        sa.Column('retention_period_days', INTEGER, nullable=False),
        sa.Column('expiration_date', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('deletion_scheduled', BOOLEAN, nullable=False, default=True),
        sa.Column('deletion_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deletion_method', VARCHAR(50), nullable=True),
        sa.Column('deletion_verified', BOOLEAN, nullable=False, default=False),
        sa.Column('retention_reason', VARCHAR(255), nullable=True),
        sa.Column('legal_basis', VARCHAR(100), nullable=True),
        sa.Column('data_volume_bytes', sa.BigInteger, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for performance optimization
    # Composite indexes for common query patterns
    op.create_index('idx_audit_events_user_timestamp', 'audit_events', ['user_id', 'event_timestamp'])
    op.create_index('idx_audit_events_type_timestamp', 'audit_events', ['event_type', 'event_timestamp'])
    op.create_index('idx_audit_events_risk_timestamp', 'audit_events', ['risk_level', 'event_timestamp'])
    op.create_index('idx_audit_events_ip_timestamp', 'audit_events', ['ip_address', 'event_timestamp'])
    op.create_index('idx_audit_events_correlation', 'audit_events', ['correlation_id', 'event_timestamp'])
    
    # GIN indexes for JSONB fields (PostgreSQL specific)
    op.create_index('idx_audit_events_metadata_gin', 'audit_events', ['metadata'], postgresql_using='gin')
    op.create_index('idx_audit_events_request_headers_gin', 'audit_events', ['request_headers'], postgresql_using='gin')
    op.create_index('idx_audit_events_request_body_gin', 'audit_events', ['request_body'], postgresql_using='gin')
    
    # Partitioning indexes
    op.create_index('idx_audit_events_partition_date', 'audit_events', ['partition_date'])
    op.create_index('idx_audit_data_access_partition_date', 'audit_data_access', ['partition_date'])
    op.create_index('idx_audit_security_events_partition_date', 'audit_security_events', ['partition_date'])
    
    # Data access audit indexes
    op.create_index('idx_audit_data_access_user_type', 'audit_data_access', ['user_id', 'data_type'])
    op.create_index('idx_audit_data_access_sensitivity', 'audit_data_access', ['data_sensitivity', 'access_timestamp'])
    op.create_index('idx_audit_data_access_method', 'audit_data_access', ['access_method', 'access_timestamp'])
    
    # Security events indexes
    op.create_index('idx_audit_security_events_threat', 'audit_security_events', ['threat_type', 'threat_level'])
    op.create_index('idx_audit_security_events_user_ip', 'audit_security_events', ['user_id', 'ip_address'])
    op.create_index('idx_audit_security_events_blocked', 'audit_security_events', ['blocked', 'event_timestamp'])
    
    # Compliance indexes
    op.create_index('idx_audit_compliance_regulation', 'audit_compliance', ['regulation_type', 'compliance_status'])
    op.create_index('idx_audit_compliance_requirement', 'audit_compliance', ['requirement_id', 'compliance_status'])
    op.create_index('idx_audit_compliance_assessment', 'audit_compliance', ['next_assessment_date', 'compliance_status'])
    
    # Retention indexes
    op.create_index('idx_audit_retention_expiration', 'audit_retention', ['expiration_date', 'deletion_scheduled'])
    op.create_index('idx_audit_retention_policy', 'audit_retention', ['retention_policy', 'data_type'])
    op.create_index('idx_audit_retention_user_type', 'audit_retention', ['user_id', 'data_type'])
    
    # Create partitioned tables for large datasets (PostgreSQL specific)
    # This creates monthly partitions for audit_events
    op.execute("""
        CREATE TABLE audit_events_y2025m01 PARTITION OF audit_events
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    """)
    
    op.execute("""
        CREATE TABLE audit_events_y2025m02 PARTITION OF audit_events
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    """)
    
    # Create monthly partitions for audit_data_access
    op.execute("""
        CREATE TABLE audit_data_access_y2025m01 PARTITION OF audit_data_access
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    """)
    
    op.execute("""
        CREATE TABLE audit_data_access_y2025m02 PARTITION OF audit_data_access
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    """)
    
    # Create monthly partitions for audit_security_events
    op.execute("""
        CREATE TABLE audit_security_events_y2025m01 PARTITION OF audit_security_events
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    """)
    
    op.execute("""
        CREATE TABLE audit_security_events_y2025m02 PARTITION OF audit_security_events
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    """)
    
    # Create functions for automatic partition creation
    op.execute("""
        CREATE OR REPLACE FUNCTION create_audit_partition(table_name text, start_date date, end_date date)
        RETURNS void AS $$
        DECLARE
            partition_name text;
            start_year integer;
            start_month integer;
        BEGIN
            start_year := EXTRACT(YEAR FROM start_date);
            start_month := EXTRACT(MONTH FROM start_date);
            partition_name := table_name || '_y' || start_year || 'm' || LPAD(start_month::text, 2, '0');
            
            EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                          partition_name, table_name, start_date, end_date);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to automatically create next month's partitions
    op.execute("""
        CREATE OR REPLACE FUNCTION create_next_month_audit_partitions()
        RETURNS void AS $$
        DECLARE
            next_month date;
            next_month_end date;
        BEGIN
            next_month := (CURRENT_DATE + INTERVAL '1 month')::date;
            next_month_end := (next_month + INTERVAL '1 month')::date;
            
            PERFORM create_audit_partition('audit_events', next_month, next_month_end);
            PERFORM create_audit_partition('audit_data_access', next_month, next_month_end);
            PERFORM create_audit_partition('audit_security_events', next_month, next_month_end);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create a cron job or scheduled task to call this function monthly
    # This would typically be handled by pg_cron extension or external scheduler


def downgrade() -> None:
    """Rollback all audit table changes."""
    
    # Drop functions first
    op.execute("DROP FUNCTION IF EXISTS create_next_month_audit_partitions();")
    op.execute("DROP FUNCTION IF EXISTS create_audit_partition(text, date, date);")
    
    # Drop partitioned tables
    op.execute("DROP TABLE IF EXISTS audit_security_events_y2025m02;")
    op.execute("DROP TABLE IF EXISTS audit_security_events_y2025m01;")
    op.execute("DROP TABLE IF EXISTS audit_data_access_y2025m02;")
    op.execute("DROP TABLE IF EXISTS audit_data_access_y2025m01;")
    op.execute("DROP TABLE IF EXISTS audit_events_y2025m02;")
    op.execute("DROP TABLE IF EXISTS audit_events_y2025m01;")
    
    # Drop main tables
    op.drop_table('audit_retention')
    op.drop_table('audit_compliance')
    op.drop_table('audit_security_events')
    op.drop_table('audit_data_access')
    op.drop_table('audit_events')
