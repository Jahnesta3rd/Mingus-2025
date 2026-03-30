"""performance monitoring tables and feature_ratings.comment

Revision ID: 009_perf_monitoring
Revises: 008_feedback_tables
Create Date: 2026-03-30

Creates api_performance and system_resources if missing (used by performance_monitor).
Adds feature_ratings.comment when the column is missing (older DBs / partial applies).
"""
from alembic import op
import sqlalchemy as sa

revision = "009_perf_monitoring"
down_revision = "008_feedback_tables"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "api_performance" not in tables:
        op.create_table(
            "api_performance",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("endpoint", sa.Text(), nullable=False),
            sa.Column("method", sa.Text(), nullable=False),
            sa.Column("response_time", sa.Float(), nullable=False),
            sa.Column("status_code", sa.Integer(), nullable=False),
            sa.Column("request_size", sa.Integer(), nullable=True),
            sa.Column("response_size", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("session_id", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "timestamp",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_api_performance_endpoint", "api_performance", ["endpoint"], unique=False
        )
        op.create_index(
            "ix_api_performance_timestamp", "api_performance", ["timestamp"], unique=False
        )

    if "system_resources" not in tables:
        op.create_table(
            "system_resources",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "timestamp",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("cpu_usage", sa.Float(), nullable=False),
            sa.Column("memory_usage", sa.Float(), nullable=False),
            sa.Column("disk_usage", sa.Float(), nullable=False),
            sa.Column("active_connections", sa.Integer(), nullable=False),
            sa.Column("queue_length", sa.Integer(), nullable=False),
            sa.Column("error_rate", sa.Float(), nullable=False),
            sa.Column("response_time_avg", sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "feature_ratings" in tables:
        cols = {c["name"] for c in inspector.get_columns("feature_ratings")}
        if "comment" not in cols:
            op.add_column(
                "feature_ratings", sa.Column("comment", sa.Text(), nullable=True)
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "api_performance" in tables:
        op.drop_index("ix_api_performance_timestamp", table_name="api_performance")
        op.drop_index("ix_api_performance_endpoint", table_name="api_performance")
        op.drop_table("api_performance")

    if "system_resources" in tables:
        op.drop_table("system_resources")

    # Do not drop feature_ratings.comment: revision 008 also defines it; dropping would
    # break databases that applied 008 correctly.
