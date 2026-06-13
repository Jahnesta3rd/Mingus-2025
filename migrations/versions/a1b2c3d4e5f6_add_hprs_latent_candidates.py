"""add_hprs_latent_candidates

Revision ID: a1b2c3d4e5f6
Revises: 27dfadd0e9cf
Create Date: 2026-06-13 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "27dfadd0e9cf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hprs_latent_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "first_evaluated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_evaluated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("threshold_met_at", sa.DateTime(), nullable=True),
        sa.Column("nudge_sent_at", sa.DateTime(), nullable=True),
        sa.Column("nudge_type", sa.String(length=20), nullable=True),
        sa.Column("nudge_text", sa.Text(), nullable=True),
        sa.Column("user_engaged_at", sa.DateTime(), nullable=True),
        sa.Column("snoozed_until", sa.DateTime(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="monitoring",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_hprs_latent_candidates_user_id"),
    )
    op.create_index(
        "ix_hprs_latent_candidates_user_id",
        "hprs_latent_candidates",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_hprs_latent_candidates_status",
        "hprs_latent_candidates",
        ["status"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_hprs_latent_candidates_status", table_name="hprs_latent_candidates")
    op.drop_index("ix_hprs_latent_candidates_user_id", table_name="hprs_latent_candidates")
    op.drop_table("hprs_latent_candidates")
