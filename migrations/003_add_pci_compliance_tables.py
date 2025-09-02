"""Migration: Add PCI Compliance Tables

Revision ID: 003_add_pci_compliance_tables
Revises: 002_add_encryption_fields
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP, TEXT, INTEGER, BOOLEAN, VARCHAR, BYTEA, DECIMAL
import uuid

# revision identifiers, used by Alembic.
revision = '003_add_pci_compliance_tables'
down_revision = '002_add_encryption_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comprehensive PCI compliance tables and structures."""
    
    # Create PCI DSS requirements tracking table
    op.create_table(
        'pci_dss_requirements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('requirement_id', VARCHAR(20), nullable=False, unique=True, index=True),  # e.g., "3.4", "4.1"
        sa.Column('requirement_category', VARCHAR(100), nullable=False, index=True),  # e.g., "Build and Maintain a Secure Network"
        sa.Column('requirement_title', VARCHAR(255), nullable=False),
        sa.Column('requirement_description', TEXT, nullable=False),
        sa.Column('requirement_details', JSONB, nullable=True),
        sa.Column('testing_procedures', TEXT, nullable=True),
        sa.Column('guidance', TEXT, nullable=True),
        sa.Column('pci_dss_version', VARCHAR(10), nullable=False, default='4.0', index=True),
        sa.Column('is_active', BOOLEAN, nullable=False, default=True, index=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create PCI compliance assessment table
    op.create_table(
        'pci_compliance_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_id', VARCHAR(100), nullable=False, unique=True, index=True),
        sa.Column('assessment_type', VARCHAR(50), nullable=False, index=True),  # SAQ, ROC, Onsite Assessment
        sa.Column('assessment_date', TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column('assessor_name', VARCHAR(255), nullable=False),
        sa.Column('assessor_company', VARCHAR(255), nullable=True),
        sa.Column('assessor_qualification', VARCHAR(100), nullable=True),
        sa.Column('assessment_scope', TEXT, nullable=False),
        sa.Column('overall_compliance_status', VARCHAR(50), nullable=False, index=True),  # COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT
        sa.Column('compliance_score_percentage', DECIMAL(5, 2), nullable=True),
        sa.Column('assessment_notes', TEXT, nullable=True),
        sa.Column('next_assessment_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('assessment_evidence', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create PCI requirement compliance details table
    op.create_table(
        'pci_requirement_compliance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('requirement_id', VARCHAR(20), nullable=False, index=True),
        sa.Column('compliance_status', VARCHAR(50), nullable=False, index=True),  # COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT, NOT_APPLICABLE
        sa.Column('compliance_evidence', TEXT, nullable=True),
        sa.Column('testing_results', TEXT, nullable=True),
        sa.Column('remediation_required', BOOLEAN, nullable=False, default=False),
        sa.Column('remediation_plan', TEXT, nullable=True),
        sa.Column('remediation_deadline', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('remediation_completed', BOOLEAN, nullable=False, default=False),
        sa.Column('remediation_notes', TEXT, nullable=True),
        sa.Column('risk_level', VARCHAR(20), nullable=False, default='MEDIUM', index=True),
        sa.Column('compliance_notes', TEXT, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create payment card data tracking table
    op.create_table(
        'payment_card_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('card_reference_id', VARCHAR(255), nullable=False, unique=True, index=True),  # Internal reference, not actual card data
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('card_type', VARCHAR(50), nullable=False, index=True),  # VISA, MASTERCARD, AMEX, etc.
        sa.Column('card_brand', VARCHAR(50), nullable=False, index=True),
        sa.Column('card_level', VARCHAR(50), nullable=True, index=True),  # CLASSIC, GOLD, PLATINUM, etc.
        sa.Column('card_issuer', VARCHAR(100), nullable=True),
        sa.Column('card_country', VARCHAR(2), nullable=True, index=True),
        sa.Column('card_currency', VARCHAR(3), nullable=True, index=True),
        sa.Column('encrypted_pan', BYTEA, nullable=False),  # Encrypted Primary Account Number
        sa.Column('encrypted_expiry_date', BYTEA, nullable=False),
        sa.Column('encrypted_cvv', BYTEA, nullable=True),
        sa.Column('encrypted_cardholder_name', BYTEA, nullable=True),
        sa.Column('encrypted_track_data', BYTEA, nullable=True),
        sa.Column('encryption_version', VARCHAR(20), nullable=False, server_default='1.0'),
        sa.Column('encryption_algorithm', VARCHAR(50), nullable=False, server_default='AES-256-GCM'),
        sa.Column('encryption_key_id', VARCHAR(255), nullable=False, index=True),
        sa.Column('encryption_iv', BYTEA, nullable=False),
        sa.Column('encryption_tag', BYTEA, nullable=False),
        sa.Column('data_classification', VARCHAR(50), nullable=False, default='PCI_SENSITIVE', index=True),
        sa.Column('storage_purpose', VARCHAR(100), nullable=False, index=True),  # TOKENIZATION, REFUNDS, DISPUTES, etc.
        sa.Column('retention_policy', VARCHAR(100), nullable=False, index=True),
        sa.Column('retention_expiry', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_active', BOOLEAN, nullable=False, default=True, index=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create payment transaction audit trail table
    op.create_table(
        'payment_transaction_audit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('transaction_id', VARCHAR(255), nullable=False, index=True),
        sa.Column('card_reference_id', VARCHAR(255), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('transaction_type', VARCHAR(50), nullable=False, index=True),  # AUTHORIZATION, CAPTURE, REFUND, VOID, etc.
        sa.Column('transaction_status', VARCHAR(50), nullable=False, index=True),  # SUCCESS, FAILED, PENDING, DECLINED
        sa.Column('transaction_amount', DECIMAL(10, 2), nullable=False),
        sa.Column('transaction_currency', VARCHAR(3), nullable=False, default='USD'),
        sa.Column('merchant_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('merchant_name', VARCHAR(255), nullable=True),
        sa.Column('merchant_category_code', VARCHAR(10), nullable=True, index=True),
        sa.Column('transaction_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('authorization_code', VARCHAR(50), nullable=True),
        sa.Column('response_code', VARCHAR(10), nullable=True),
        sa.Column('response_message', VARCHAR(255), nullable=True),
        sa.Column('avs_result', VARCHAR(10), nullable=True),  # Address Verification System
        sa.Column('cvv_result', VARCHAR(10), nullable=True),
        sa.Column('risk_score', INTEGER, nullable=True, index=True),
        sa.Column('fraud_indicators', JSONB, nullable=True),
        sa.Column('ip_address', VARCHAR(45), nullable=True, index=True),
        sa.Column('user_agent', TEXT, nullable=True),
        sa.Column('session_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('correlation_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('processing_gateway', VARCHAR(100), nullable=True, index=True),
        sa.Column('gateway_response', JSONB, nullable=True),
        sa.Column('compliance_flags', JSONB, nullable=True),
        sa.Column('audit_metadata', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('partition_date', sa.Date, nullable=False, server_default=sa.func.current_date())
    )
    
    # Create PCI security incident tracking table
    op.create_table(
        'pci_security_incidents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('incident_id', VARCHAR(100), nullable=False, unique=True, index=True),
        sa.Column('incident_type', VARCHAR(100), nullable=False, index=True),  # DATA_BREACH, UNAUTHORIZED_ACCESS, MALWARE, etc.
        sa.Column('incident_severity', VARCHAR(20), nullable=False, index=True),  # LOW, MEDIUM, HIGH, CRITICAL
        sa.Column('incident_status', VARCHAR(50), nullable=False, index=True),  # OPEN, INVESTIGATING, RESOLVED, CLOSED
        sa.Column('incident_discovery_date', TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column('incident_occurrence_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('incident_description', TEXT, nullable=False),
        sa.Column('affected_systems', JSONB, nullable=True),
        sa.Column('affected_data_types', JSONB, nullable=True),
        sa.Column('potential_card_data_exposure', BOOLEAN, nullable=False, default=False),
        sa.Column('exposed_card_count', INTEGER, nullable=True),
        sa.Column('incident_impact', TEXT, nullable=True),
        sa.Column('root_cause_analysis', TEXT, nullable=True),
        sa.Column('remediation_actions', JSONB, nullable=True),
        sa.Column('remediation_completion_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('incident_owner', VARCHAR(255), nullable=True),
        sa.Column('assigned_team', VARCHAR(100), nullable=True),
        sa.Column('external_reporting_required', BOOLEAN, nullable=False, default=False),
        sa.Column('external_reporting_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('external_reporting_recipients', JSONB, nullable=True),
        sa.Column('incident_lessons_learned', TEXT, nullable=True),
        sa.Column('prevention_measures', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create PCI compliance reporting table
    op.create_table(
        'pci_compliance_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_id', VARCHAR(100), nullable=False, unique=True, index=True),
        sa.Column('report_type', VARCHAR(100), nullable=False, index=True),  # SAQ, ROC, COMPLIANCE_SUMMARY, etc.
        sa.Column('report_period_start', TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column('report_period_end', TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column('report_generation_date', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('report_generated_by', VARCHAR(255), nullable=False),
        sa.Column('report_status', VARCHAR(50), nullable=False, default='DRAFT', index=True),  # DRAFT, REVIEW, APPROVED, SUBMITTED
        sa.Column('report_approver', VARCHAR(255), nullable=True),
        sa.Column('report_approval_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('report_submission_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('report_recipients', JSONB, nullable=True),
        sa.Column('compliance_summary', TEXT, nullable=True),
        sa.Column('compliance_score', DECIMAL(5, 2), nullable=True),
        sa.Column('non_compliant_requirements', JSONB, nullable=True),
        sa.Column('remediation_plans', JSONB, nullable=True),
        sa.Column('risk_assessment', TEXT, nullable=True),
        sa.Column('report_metadata', JSONB, nullable=True),
        sa.Column('report_file_path', VARCHAR(500), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create PCI data flow mapping table
    op.create_table(
        'pci_data_flow_mapping',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('flow_id', VARCHAR(100), nullable=False, unique=True, index=True),
        sa.Column('flow_name', VARCHAR(255), nullable=False),
        sa.Column('flow_description', TEXT, nullable=True),
        sa.Column('data_type', VARCHAR(100), nullable=False, index=True),  # PAN, CVV, TRACK_DATA, etc.
        sa.Column('data_classification', VARCHAR(50), nullable=False, index=True),
        sa.Column('source_system', VARCHAR(100), nullable=False, index=True),
        sa.Column('destination_system', VARCHAR(100), nullable=False, index=True),
        sa.Column('data_transmission_method', VARCHAR(100), nullable=False, index=True),  # API, FILE_TRANSFER, DATABASE, etc.
        sa.Column('encryption_in_transit', BOOLEAN, nullable=False, default=True),
        sa.Column('encryption_algorithm_transit', VARCHAR(50), nullable=True),
        sa.Column('encryption_at_rest', BOOLEAN, nullable=False, default=True),
        sa.Column('encryption_algorithm_rest', VARCHAR(50), nullable=True),
        sa.Column('authentication_required', BOOLEAN, nullable=False, default=True),
        sa.Column('authentication_method', VARCHAR(100), nullable=True),
        sa.Column('authorization_required', BOOLEAN, nullable=False, default=True),
        sa.Column('authorization_method', VARCHAR(100), nullable=True),
        sa.Column('audit_logging_enabled', BOOLEAN, nullable=False, default=True),
        sa.Column('data_retention_policy', VARCHAR(100), nullable=True),
        sa.Column('data_retention_period', INTEGER, nullable=True),  # Days
        sa.Column('flow_risk_assessment', TEXT, nullable=True),
        sa.Column('flow_controls', JSONB, nullable=True),
        sa.Column('flow_owner', VARCHAR(255), nullable=True),
        sa.Column('flow_review_date', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('flow_status', VARCHAR(50), nullable=False, default='ACTIVE', index=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for performance optimization
    # PCI DSS requirements indexes
    op.create_index('idx_pci_dss_requirements_category', 'pci_dss_requirements', ['requirement_category', 'is_active'])
    op.create_index('idx_pci_dss_requirements_version', 'pci_dss_requirements', ['pci_dss_version', 'is_active'])
    
    # PCI compliance assessments indexes
    op.create_index('idx_pci_compliance_assessments_type_date', 'pci_compliance_assessments', ['assessment_type', 'assessment_date'])
    op.create_index('idx_pci_compliance_assessments_status', 'pci_compliance_assessments', ['overall_compliance_status', 'assessment_date'])
    op.create_index('idx_pci_compliance_assessments_assessor', 'pci_compliance_assessments', ['assessor_name', 'assessment_date'])
    
    # PCI requirement compliance indexes
    op.create_index('idx_pci_requirement_compliance_assessment', 'pci_requirement_compliance', ['assessment_id', 'requirement_id'])
    op.create_index('idx_pci_requirement_compliance_status', 'pci_requirement_compliance', ['compliance_status', 'remediation_required'])
    op.create_index('idx_pci_requirement_compliance_risk', 'pci_requirement_compliance', ['risk_level', 'compliance_status'])
    
    # Payment card data indexes
    op.create_index('idx_payment_card_data_type_brand', 'payment_card_data', ['card_type', 'card_brand'])
    op.create_index('idx_payment_card_data_user', 'payment_card_data', ['user_id', 'is_active'])
    op.create_index('idx_payment_card_data_retention', 'payment_card_data', ['retention_expiry', 'is_active'])
    op.create_index('idx_payment_card_data_purpose', 'payment_card_data', ['storage_purpose', 'is_active'])
    
    # Payment transaction audit indexes
    op.create_index('idx_payment_transaction_audit_card', 'payment_transaction_audit', ['card_reference_id', 'transaction_timestamp'])
    op.create_index('idx_payment_transaction_audit_user', 'payment_transaction_audit', ['user_id', 'transaction_timestamp'])
    op.create_index('idx_payment_transaction_audit_type_status', 'payment_transaction_audit', ['transaction_type', 'transaction_status'])
    op.create_index('idx_payment_transaction_audit_amount', 'payment_transaction_audit', ['transaction_amount', 'transaction_timestamp'])
    op.create_index('idx_payment_transaction_audit_merchant', 'payment_transaction_audit', ['merchant_id', 'transaction_timestamp'])
    op.create_index('idx_payment_transaction_audit_partition', 'payment_transaction_audit', ['partition_date'])
    
    # PCI security incidents indexes
    op.create_index('idx_pci_security_incidents_type_severity', 'pci_security_incidents', ['incident_type', 'incident_severity'])
    op.create_index('idx_pci_security_incidents_status_date', 'pci_security_incidents', ['incident_status', 'incident_discovery_date'])
    op.create_index('idx_pci_security_incidents_card_exposure', 'pci_security_incidents', ['potential_card_data_exposure', 'incident_severity'])
    
    # PCI compliance reports indexes
    op.create_index('idx_pci_compliance_reports_type_period', 'pci_compliance_reports', ['report_type', 'report_period_start'])
    op.create_index('idx_pci_compliance_reports_status', 'pci_compliance_reports', ['report_status', 'report_generation_date'])
    op.create_index('idx_pci_compliance_reports_approver', 'pci_compliance_reports', ['report_approver', 'report_approval_date'])
    
    # PCI data flow mapping indexes
    op.create_index('idx_pci_data_flow_mapping_type', 'pci_data_flow_mapping', ['data_type', 'flow_status'])
    op.create_index('idx_pci_data_flow_mapping_source', 'pci_data_flow_mapping', ['source_system', 'flow_status'])
    op.create_index('idx_pci_data_flow_mapping_destination', 'pci_data_flow_mapping', ['destination_system', 'flow_status'])
    
    # Create partitioned tables for large datasets
    # Monthly partitions for payment transaction audit
    op.execute("""
        CREATE TABLE payment_transaction_audit_y2025m01 PARTITION OF payment_transaction_audit
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    """)
    
    op.execute("""
        CREATE TABLE payment_transaction_audit_y2025m02 PARTITION OF payment_transaction_audit
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    """)
    
    # Create functions for PCI compliance automation
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_pci_compliance_score(assessment_uuid uuid)
        RETURNS DECIMAL AS $$
        DECLARE
            total_requirements integer;
            compliant_requirements integer;
            compliance_score DECIMAL(5, 2);
        BEGIN
            -- Count total applicable requirements
            SELECT COUNT(*) INTO total_requirements
            FROM pci_requirement_compliance prc
            JOIN pci_dss_requirements pdr ON prc.requirement_id = pdr.requirement_id
            WHERE prc.assessment_id = assessment_uuid
            AND pdr.is_active = true;
            
            -- Count compliant requirements
            SELECT COUNT(*) INTO compliant_requirements
            FROM pci_requirement_compliance prc
            JOIN pci_dss_requirements pdr ON prc.requirement_id = pdr.requirement_id
            WHERE prc.assessment_id = assessment_uuid
            AND pdr.is_active = true
            AND prc.compliance_status = 'COMPLIANT';
            
            -- Calculate percentage
            IF total_requirements > 0 THEN
                compliance_score := (compliant_requirements::DECIMAL / total_requirements::DECIMAL) * 100;
            ELSE
                compliance_score := 0;
            END IF;
            
            RETURN ROUND(compliance_score, 2);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function for automatic PCI requirement compliance tracking
    op.execute("""
        CREATE OR REPLACE FUNCTION track_pci_requirement_compliance(
            p_assessment_id uuid,
            p_requirement_id varchar,
            p_compliance_status varchar,
            p_evidence text DEFAULT NULL,
            p_notes text DEFAULT NULL
        ) RETURNS void AS $$
        BEGIN
            INSERT INTO pci_requirement_compliance (
                assessment_id, requirement_id, compliance_status, 
                compliance_evidence, compliance_notes, created_at, updated_at
            ) VALUES (
                p_assessment_id, p_requirement_id, p_compliance_status,
                p_evidence, p_notes, NOW(), NOW()
            )
            ON CONFLICT (assessment_id, requirement_id)
            DO UPDATE SET
                compliance_status = EXCLUDED.compliance_status,
                compliance_evidence = EXCLUDED.compliance_evidence,
                compliance_notes = EXCLUDED.compliance_notes,
                updated_at = NOW();
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function for PCI data exposure risk assessment
    op.execute("""
        CREATE OR REPLACE FUNCTION assess_pci_data_exposure_risk(
            p_incident_id uuid
        ) RETURNS varchar AS $$
        DECLARE
            risk_level varchar := 'LOW';
            exposed_card_count integer;
            incident_severity varchar;
        BEGIN
            -- Get incident details
            SELECT 
                COALESCE(exposed_card_count, 0),
                incident_severity
            INTO exposed_card_count, incident_severity
            FROM pci_security_incidents
            WHERE id = p_incident_id;
            
            -- Risk assessment logic
            IF incident_severity = 'CRITICAL' THEN
                risk_level := 'CRITICAL';
            ELSIF incident_severity = 'HIGH' OR exposed_card_count > 1000 THEN
                risk_level := 'HIGH';
            ELSIF incident_severity = 'MEDIUM' OR exposed_card_count > 100 THEN
                risk_level := 'MEDIUM';
            ELSIF incident_severity = 'LOW' AND exposed_card_count <= 100 THEN
                risk_level := 'LOW';
            END IF;
            
            RETURN risk_level;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create views for PCI compliance reporting
    op.execute("""
        CREATE OR REPLACE VIEW pci_compliance_summary AS
        SELECT 
            pca.assessment_id,
            pca.assessment_type,
            pca.assessment_date,
            pca.overall_compliance_status,
            pca.compliance_score_percentage,
            pca.assessor_name,
            pca.next_assessment_date,
            COUNT(prc.requirement_id) as total_requirements,
            COUNT(CASE WHEN prc.compliance_status = 'COMPLIANT' THEN 1 END) as compliant_requirements,
            COUNT(CASE WHEN prc.compliance_status = 'NON_COMPLIANT' THEN 1 END) as non_compliant_requirements,
            COUNT(CASE WHEN prc.compliance_status = 'PARTIALLY_COMPLIANT' THEN 1 END) as partially_compliant_requirements,
            COUNT(CASE WHEN prc.remediation_required = true THEN 1 END) as requirements_needing_remediation
        FROM pci_compliance_assessments pca
        LEFT JOIN pci_requirement_compliance prc ON pca.id = prc.assessment_id
        GROUP BY pca.id, pca.assessment_id, pca.assessment_type, pca.assessment_date, 
                 pca.overall_compliance_status, pca.compliance_score_percentage, 
                 pca.assessor_name, pca.next_assessment_date;
    """)
    
    # Create view for PCI data flow compliance
    op.execute("""
        CREATE OR REPLACE VIEW pci_data_flow_compliance AS
        SELECT 
            pdfm.flow_id,
            pdfm.flow_name,
            pdfm.data_type,
            pdfm.data_classification,
            pdfm.source_system,
            pdfm.destination_system,
            pdfm.encryption_in_transit,
            pdfm.encryption_at_rest,
            pdfm.authentication_required,
            pdfm.authorization_required,
            pdfm.audit_logging_enabled,
            pdfm.flow_risk_assessment,
            pdfm.flow_status,
            CASE 
                WHEN pdfm.encryption_in_transit = true 
                     AND pdfm.encryption_at_rest = true 
                     AND pdfm.authentication_required = true 
                     AND pdfm.authorization_required = true 
                     AND pdfm.audit_logging_enabled = true
                THEN 'COMPLIANT'
                ELSE 'NON_COMPLIANT'
            END as flow_compliance_status
        FROM pci_data_flow_mapping pdfm
        WHERE pdfm.flow_status = 'ACTIVE';
    """)


def downgrade() -> None:
    """Rollback PCI compliance table additions."""
    
    # Drop functions first
    op.execute("DROP FUNCTION IF EXISTS assess_pci_data_exposure_risk(uuid);")
    op.execute("DROP FUNCTION IF EXISTS track_pci_requirement_compliance(uuid, varchar, varchar, text, text);")
    op.execute("DROP FUNCTION IF EXISTS calculate_pci_compliance_score(uuid);")
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS pci_data_flow_compliance;")
    op.execute("DROP VIEW IF EXISTS pci_compliance_summary;")
    
    # Drop partitioned tables
    op.execute("DROP TABLE IF EXISTS payment_transaction_audit_y2025m02;")
    op.execute("DROP TABLE IF EXISTS payment_transaction_audit_y2025m01;")
    
    # Drop main tables
    op.drop_table('pci_data_flow_mapping')
    op.drop_table('pci_compliance_reports')
    op.drop_table('pci_security_incidents')
    op.drop_table('payment_transaction_audit')
    op.drop_table('payment_card_data')
    op.drop_table('pci_requirement_compliance')
    op.drop_table('pci_compliance_assessments')
    op.drop_table('pci_dss_requirements')
