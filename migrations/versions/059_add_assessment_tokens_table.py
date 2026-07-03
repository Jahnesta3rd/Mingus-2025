"""Add assessment_tokens table and assessments.user_id for signup linking.

Revision ID: 059_add_assessment_tokens
Revises: c56cc3904151
Create Date: 2026-07-02

"""
from alembic import op
import sqlalchemy as sa

revision = "059_add_assessment_tokens"
down_revision = "c56cc3904151"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    bool_false = sa.text("false") if postgres else sa.text("0")

    op.create_table(
        "assessment_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("email_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_used",
            sa.Boolean(),
            nullable=False,
            server_default=bool_false,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("redeemed_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["redeemed_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_assessment_tokens_token"),
        "assessment_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f("ix_assessment_tokens_assessment_id"),
        "assessment_tokens",
        ["assessment_id"],
        unique=False,
    )

    # Link anonymous assessments to users after signup
    op.add_column(
        "assessments",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_assessments_user_id",
        "assessments",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_assessments_user_id"),
        "assessments",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_assessments_user_id"), table_name="assessments")
    op.drop_constraint("fk_assessments_user_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "user_id")
    op.drop_index(
        op.f("ix_assessment_tokens_assessment_id"),
        table_name="assessment_tokens",
    )
    op.drop_index(op.f("ix_assessment_tokens_token"), table_name="assessment_tokens")
    op.drop_table("assessment_tokens")
