#!/usr/bin/env python3
"""Lazy DDL for Health Insurance Advisor usage fields on user_profiles."""

from __future__ import annotations

import logging

from backend.api.profile_endpoints import get_db_connection

logger = logging.getLogger(__name__)

_HIA_COLUMNS: tuple[tuple[str, str], ...] = (
    ("hia_coverage_type", "VARCHAR(20)"),
    ("hia_primary_care_visits", "INTEGER"),
    ("hia_specialist_visits", "INTEGER"),
    ("hia_er_visits", "INTEGER"),
    ("hia_planned_procedure", "BOOLEAN"),
    ("hia_takes_rx", "BOOLEAN"),
    ("hia_rx_type", "VARCHAR(20)"),
    ("hia_last_updated", "TIMESTAMP"),
)


def add_hia_columns_if_missing() -> None:
    """Add HIA usage columns to user_profiles when absent (idempotent)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user_profiles'
                """
            )
            existing = {row["column_name"] for row in cur.fetchall()}

            for column_name, column_type in _HIA_COLUMNS:
                if column_name in existing:
                    continue
                cur.execute(
                    f"ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type}"
                )
                logger.info("Added user_profiles.%s", column_name)

        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to add HIA columns to user_profiles")
        raise
    finally:
        conn.close()


add_hia_columns_if_missing()
