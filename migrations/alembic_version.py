"""Ensure alembic_version.version_num fits descriptive revision IDs.

Alembic 1.14+ creates version_num as VARCHAR(32) by default; many Mingus
revisions exceed that limit (e.g. 066_create_relationship_milestone_checkins).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

VERSION_NUM_LENGTH = 128


def ensure_alembic_version_table(connection: Connection) -> None:
    """Create or widen alembic_version before Alembic stamp/upgrade runs."""
    connection.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR({VERSION_NUM_LENGTH}) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
            """
        )
    )
    row = connection.execute(
        text(
            """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'alembic_version'
              AND column_name = 'version_num'
            """
        )
    ).fetchone()
    if row and row[0] is not None and row[0] < VERSION_NUM_LENGTH:
        connection.execute(
            text(
                f"""
                ALTER TABLE alembic_version
                ALTER COLUMN version_num TYPE VARCHAR({VERSION_NUM_LENGTH})
                """
            )
        )
