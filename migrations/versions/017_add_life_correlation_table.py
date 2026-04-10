"""add life_score_snapshots for life correlation

Revision ID: 017_add_life_correlation_table
Revises: 016_add_vibe_tracker_tables
Create Date: 2026-04-08

Daily upserted snapshot: ledger scores, vibe aggregates, wellness averages, projections.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "017_add_life_correlation_table"
down_revision = "016_add_vibe_tracker_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "life_score_snapshots",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("trigger", sa.String(length=50), nullable=False),
        sa.Column("body_score", sa.Integer(), nullable=True),
        sa.Column("roof_score", sa.Integer(), nullable=True),
        sa.Column("vehicle_score", sa.Integer(), nullable=True),
        sa.Column("life_ledger_score", sa.Integer(), nullable=True),
        sa.Column("best_vibe_emotional_score", sa.Integer(), nullable=True),
        sa.Column("best_vibe_financial_score", sa.Integer(), nullable=True),
        sa.Column("best_vibe_combined_score", sa.Integer(), nullable=True),
        sa.Column("active_tracked_people_count", sa.Integer(), nullable=True),
        sa.Column("monthly_savings_rate", sa.Float(), nullable=True),
        sa.Column("net_worth_estimate", sa.Integer(), nullable=True),
        sa.Column("relationship_monthly_cost", sa.Integer(), nullable=True),
        sa.Column("avg_wellness_score", sa.Float(), nullable=True),
        sa.Column("avg_stress_level", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "snapshot_date",
            name="uq_life_score_snapshots_user_id_snapshot_date",
        ),
    )
    op.create_index(
        "ix_life_score_snapshots_user_id",
        "life_score_snapshots",
        ["user_id"],
    )


def downgrade():
    op.drop_index("ix_life_score_snapshots_user_id", table_name="life_score_snapshots")
    op.drop_table("life_score_snapshots")
