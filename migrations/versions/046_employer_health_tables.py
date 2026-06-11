"""CR9a: employer health tables + career_profile employer fields

Revision ID: 046_employer_health
Revises: 045_market_conditions
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa

revision = "046_employer_health"
down_revision = "045_market_conditions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cik", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=True),
        sa.Column("sic_code", sa.String(length=4), nullable=True),
        sa.Column("sic_desc", sa.String(length=100), nullable=True),
        sa.Column("exchange", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cik"),
    )

    op.create_table(
        "employer_health_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("revenue_delta_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("margin_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("fcf_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("runway_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("leverage_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("revenue_ttm", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("operating_margin", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("free_cash_flow", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("cash_and_equiv", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_debt", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("fiscal_period_end", sa.Date(), nullable=True),
        sa.Column("filing_accession", sa.String(length=25), nullable=True),
        sa.Column(
            "data_source",
            sa.String(length=20),
            nullable=False,
            server_default="sec_edgar",
        ),
        sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "refreshed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_employer_health_snapshots_employer_refreshed",
        "employer_health_snapshots",
        ["employer_id", "refreshed_at"],
        postgresql_ops={"refreshed_at": "DESC"},
    )

    op.create_table(
        "layoff_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("accession_number", sa.String(length=25), nullable=False),
        sa.Column(
            "item_number",
            sa.String(length=10),
            nullable=False,
            server_default="2.05",
        ),
        sa.Column("affected_count", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column(
            "review_state",
            sa.String(length=20),
            nullable=False,
            server_default="auto",
        ),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_layoff_events_employer_filing_date",
        "layoff_events",
        ["employer_id", "filing_date"],
        postgresql_ops={"filing_date": "DESC"},
    )
    op.create_index(
        "ix_layoff_events_expires_at",
        "layoff_events",
        ["expires_at"],
    )

    op.add_column(
        "career_profile",
        sa.Column("employer_cik", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("employer_name_text", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("employer_type", sa.String(length=30), nullable=True),
    )


def downgrade():
    op.drop_column("career_profile", "employer_type")
    op.drop_column("career_profile", "employer_name_text")
    op.drop_column("career_profile", "employer_cik")

    op.drop_index("ix_layoff_events_expires_at", table_name="layoff_events")
    op.drop_index("ix_layoff_events_employer_filing_date", table_name="layoff_events")
    op.drop_table("layoff_events")

    op.drop_index(
        "ix_employer_health_snapshots_employer_refreshed",
        table_name="employer_health_snapshots",
    )
    op.drop_table("employer_health_snapshots")

    op.drop_table("employers")
