"""Market conditions OES wage data + market_data_cache (#165)

Revision ID: 045_market_conditions
Revises: 044_plaid_transactions
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa

revision = "045_market_conditions"
down_revision = "044_plaid_transactions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oes_wage_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bls_career_field", sa.String(length=100), nullable=False),
        sa.Column("msa_code", sa.String(length=20), nullable=False),
        sa.Column("msa_name", sa.String(length=100), nullable=False),
        sa.Column("pct_10", sa.Integer(), nullable=False),
        sa.Column("pct_25", sa.Integer(), nullable=False),
        sa.Column("pct_50", sa.Integer(), nullable=False),
        sa.Column("pct_75", sa.Integer(), nullable=False),
        sa.Column("pct_90", sa.Integer(), nullable=False),
        sa.Column("source_year", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "bls_career_field",
            "msa_code",
            name="uq_oes_wage_data_field_msa",
        ),
    )
    op.create_index(
        "ix_oes_wage_data_bls_career_field",
        "oes_wage_data",
        ["bls_career_field"],
    )
    op.create_index(
        "ix_oes_wage_data_msa_code",
        "oes_wage_data",
        ["msa_code"],
    )

    op.create_table(
        "market_data_cache",
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade():
    op.drop_table("market_data_cache")
    op.drop_index("ix_oes_wage_data_msa_code", table_name="oes_wage_data")
    op.drop_index("ix_oes_wage_data_bls_career_field", table_name="oes_wage_data")
    op.drop_table("oes_wage_data")
