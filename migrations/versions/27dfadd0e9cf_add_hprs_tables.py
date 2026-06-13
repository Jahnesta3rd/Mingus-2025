"""add_hprs_tables

Revision ID: 27dfadd0e9cf
Revises: 048_llm_narrative_credits
Create Date: 2026-06-13 15:40:22.861590

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "27dfadd0e9cf"
down_revision = "048_llm_narrative_credits"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hprs_scores",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("readiness_tier", sa.String(length=20), nullable=False),
        sa.Column("down_payment_score", sa.Integer(), nullable=True),
        sa.Column("credit_score", sa.Integer(), nullable=True),
        sa.Column("dti_score", sa.Integer(), nullable=True),
        sa.Column("savings_rate_score", sa.Integer(), nullable=True),
        sa.Column("income_stability_score", sa.Integer(), nullable=True),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("target_timeline_months", sa.Integer(), nullable=True),
        sa.Column("down_payment_saved", sa.Float(), nullable=True),
        sa.Column("down_payment_needed", sa.Float(), nullable=True),
        sa.Column("inputs_snapshot", JSONB(), nullable=True),
        # Career risk (populated by HPRS-04)
        sa.Column("career_risk_score", sa.Integer(), nullable=True),
        sa.Column("career_risk_band", sa.String(length=20), nullable=True),
        sa.Column(
            "career_modifier",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Vehicle risk (populated by HPRS-05)
        sa.Column("vehicle_risk_score", sa.Integer(), nullable=True),
        sa.Column("vehicle_risk_band", sa.String(length=20), nullable=True),
        sa.Column(
            "vehicle_modifier",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Combined modifier (career + vehicle)
        sa.Column(
            "combined_modifier",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Market timing pillar (D6)
        sa.Column("market_score", sa.Integer(), nullable=True),
        sa.Column(
            "computed_at",
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
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_hprs_scores_overall_score",
        ),
        sa.CheckConstraint(
            "down_payment_score IS NULL OR (down_payment_score >= 0 AND down_payment_score <= 100)",
            name="ck_hprs_scores_down_payment_score",
        ),
        sa.CheckConstraint(
            "credit_score IS NULL OR (credit_score >= 0 AND credit_score <= 100)",
            name="ck_hprs_scores_credit_score",
        ),
        sa.CheckConstraint(
            "dti_score IS NULL OR (dti_score >= 0 AND dti_score <= 100)",
            name="ck_hprs_scores_dti_score",
        ),
        sa.CheckConstraint(
            "savings_rate_score IS NULL OR (savings_rate_score >= 0 AND savings_rate_score <= 100)",
            name="ck_hprs_scores_savings_rate_score",
        ),
        sa.CheckConstraint(
            "income_stability_score IS NULL OR (income_stability_score >= 0 AND income_stability_score <= 100)",
            name="ck_hprs_scores_income_stability_score",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_hprs_scores_user_id"),
    )
    op.create_index("ix_hprs_scores_user_id", "hprs_scores", ["user_id"])

    op.create_table(
        "hprs_plans",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("score_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("plan_summary", sa.Text(), nullable=True),
        sa.Column(
            "action_steps",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("focus_pillar", sa.String(length=30), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("llm_model", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["score_id"], ["hprs_scores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hprs_plans_user_id", "hprs_plans", ["user_id"])
    op.create_index(
        "ix_hprs_plans_user_id_is_active",
        "hprs_plans",
        ["user_id", "is_active"],
    )

    op.create_table(
        "hprs_score_history",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("readiness_tier", sa.String(length=20), nullable=False),
        sa.Column("down_payment_score", sa.Integer(), nullable=True),
        sa.Column("credit_score", sa.Integer(), nullable=True),
        sa.Column("dti_score", sa.Integer(), nullable=True),
        sa.Column("savings_rate_score", sa.Integer(), nullable=True),
        sa.Column("income_stability_score", sa.Integer(), nullable=True),
        sa.Column("trigger", sa.String(length=50), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_hprs_score_history_overall_score",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hprs_score_history_user_id_recorded_at",
        "hprs_score_history",
        ["user_id", "recorded_at"],
    )


def downgrade():
    op.drop_index(
        "ix_hprs_score_history_user_id_recorded_at",
        table_name="hprs_score_history",
    )
    op.drop_table("hprs_score_history")
    op.drop_index("ix_hprs_plans_user_id_is_active", table_name="hprs_plans")
    op.drop_index("ix_hprs_plans_user_id", table_name="hprs_plans")
    op.drop_table("hprs_plans")
    op.drop_index("ix_hprs_scores_user_id", table_name="hprs_scores")
    op.drop_table("hprs_scores")
