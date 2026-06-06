"""Add agreement_acceptances table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_agreement_acceptances_clean'
down_revision = '035_vehicle_nullable_vin_zip'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'agreement_acceptances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agreement_version', sa.String(50), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('agreement_hash', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_agreement_acceptances_user_id', 'agreement_acceptances', ['user_id'])
    op.create_index('ix_agreement_acceptances_agreement_version', 'agreement_acceptances', ['agreement_version'])

def downgrade():
    op.drop_index('ix_agreement_acceptances_agreement_version', 'agreement_acceptances')
    op.drop_index('ix_agreement_acceptances_user_id', 'agreement_acceptances')
    op.drop_table('agreement_acceptances')
