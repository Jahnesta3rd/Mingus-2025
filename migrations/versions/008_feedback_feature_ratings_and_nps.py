"""feedback feature_ratings and nps_surveys

Revision ID: 008_feedback_tables
Revises: 007_add_beta_code_table_and_user_beta_fields
Create Date: 2026-03-30

"""
from alembic import op
import sqlalchemy as sa

revision = "008_feedback_tables"
down_revision = "007_add_beta_code_table_and_user_beta_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feature_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("rating", sa.String(length=4), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_tier", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feature_ratings_user_id"), "feature_ratings", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_feature_ratings_feature_name"),
        "feature_ratings",
        ["feature_name"],
        unique=False,
    )

    op.create_table(
        "nps_surveys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("most_valuable_feature", sa.String(length=100), nullable=True),
        sa.Column("least_valuable_feature", sa.String(length=100), nullable=True),
        sa.Column("would_pay", sa.String(length=10), nullable=True),
        sa.Column("price_willing", sa.Integer(), nullable=True),
        sa.Column("additional_comments", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_nps_surveys_user_id"),
    )


def downgrade():
    op.drop_table("nps_surveys")
    op.drop_index(op.f("ix_feature_ratings_feature_name"), table_name="feature_ratings")
    op.drop_index(op.f("ix_feature_ratings_user_id"), table_name="feature_ratings")
    op.drop_table("feature_ratings")
