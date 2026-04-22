#!/usr/bin/env python3
"""
Migration: user_profiles balance columns + user_interactions analytics table.

Run standalone (after setting DATABASE_URL):

    python backend/migrations/add_user_profile_balance_and_user_interactions.py

Or invoke ``upgrade()`` from an Alembic context (``op.get_bind()``).

PostgreSQL executed by upgrade() (conceptually; IF NOT EXISTS / guards applied at runtime):

-- 1) user_profiles (skipped if columns already exist)
ALTER TABLE user_profiles ADD COLUMN current_balance NUMERIC(18, 2);
ALTER TABLE user_profiles ADD COLUMN balance_last_updated TIMESTAMPTZ;

-- 2) user_interactions (skipped if table exists)
CREATE TABLE user_interactions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(128) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(64) NOT NULL,
    page_url TEXT,
    element_id TEXT,
    element_text TEXT,
    interaction_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    CONSTRAINT ck_user_interactions_type CHECK (interaction_type IN (
        'page_view', 'button_click', 'form_submit', 'scroll_depth', 'time_on_page',
        'recommendation_view', 'recommendation_click', 'application_start',
        'application_complete', 'share', 'bookmark'
    ))
);

CREATE INDEX idx_user_interactions_session ON user_interactions (session_id);
CREATE INDEX idx_user_interactions_type ON user_interactions (interaction_type);
CREATE INDEX idx_user_interactions_timestamp ON user_interactions ("timestamp");
CREATE INDEX idx_user_interactions_user_id ON user_interactions (user_id);

Downgrade drops indexes, table, then columns (when present).
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import inspect, text

try:
    from alembic import op

    HAS_ALEMBIC = True
except ImportError:
    HAS_ALEMBIC = False
    op = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


def _apply_upgrade(bind) -> None:
    insp = inspect(bind)

    if insp.has_table("user_profiles"):
        cols = {c["name"] for c in insp.get_columns("user_profiles")}
        if "current_balance" not in cols:
            bind.execute(
                text(
                    "ALTER TABLE user_profiles ADD COLUMN current_balance NUMERIC(18, 2)"
                )
            )
        if "balance_last_updated" not in cols:
            bind.execute(
                text(
                    "ALTER TABLE user_profiles ADD COLUMN balance_last_updated TIMESTAMPTZ"
                )
            )

    if not insp.has_table("user_interactions"):
        bind.execute(
            text(
                """
                CREATE TABLE user_interactions (
                    id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(128) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    interaction_type VARCHAR(64) NOT NULL,
                    page_url TEXT,
                    element_id TEXT,
                    element_text TEXT,
                    interaction_data JSONB NOT NULL DEFAULT '{}'::jsonb,
                    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
                    CONSTRAINT ck_user_interactions_type CHECK (interaction_type IN (
                        'page_view', 'button_click', 'form_submit', 'scroll_depth', 'time_on_page',
                        'recommendation_view', 'recommendation_click', 'application_start',
                        'application_complete', 'share', 'bookmark'
                    ))
                )
                """
            )
        )
        for stmt in (
            "CREATE INDEX idx_user_interactions_session ON user_interactions (session_id)",
            "CREATE INDEX idx_user_interactions_type ON user_interactions (interaction_type)",
            'CREATE INDEX idx_user_interactions_timestamp ON user_interactions ("timestamp")',
            "CREATE INDEX idx_user_interactions_user_id ON user_interactions (user_id)",
        ):
            bind.execute(text(stmt))


def _apply_downgrade(bind) -> None:
    insp = inspect(bind)

    if insp.has_table("user_interactions"):
        for ix in (
            "idx_user_interactions_user_id",
            "idx_user_interactions_timestamp",
            "idx_user_interactions_type",
            "idx_user_interactions_session",
        ):
            bind.execute(text(f"DROP INDEX IF EXISTS {ix}"))
        bind.execute(text("DROP TABLE IF EXISTS user_interactions"))

    if insp.has_table("user_profiles"):
        cols = {c["name"] for c in insp.get_columns("user_profiles")}
        if "balance_last_updated" in cols:
            bind.execute(
                text("ALTER TABLE user_profiles DROP COLUMN balance_last_updated")
            )
        if "current_balance" in cols:
            bind.execute(text("ALTER TABLE user_profiles DROP COLUMN current_balance"))


def upgrade() -> None:
    if HAS_ALEMBIC:
        bind = op.get_bind()
        _apply_upgrade(bind)
        return
    logger.warning("alembic op not available; run this module as __main__ with DATABASE_URL")


def downgrade() -> None:
    if HAS_ALEMBIC:
        bind = op.get_bind()
        _apply_downgrade(bind)
        return


if __name__ == "__main__":
    from sqlalchemy import create_engine

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is required to run this migration.")
    engine = create_engine(url)
    with engine.begin() as conn:
        _apply_upgrade(conn)
    print("upgrade() applied successfully.")
