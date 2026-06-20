#!/usr/bin/env python3
"""Initialize the CI test Postgres schema once before pytest runs."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.db_helpers import (  # noqa: E402
    ensure_libpq_env,
    ensure_postgres_extensions,
    get_test_database_uri,
    initialize_shared_schema,
    run_alembic_migrations,
)

ANALYTICS_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS api_performance (
    id SERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    response_time REAL NOT NULL,
    status_code INTEGER NOT NULL,
    request_size INTEGER,
    response_size INTEGER,
    user_id TEXT,
    session_id TEXT,
    error_message TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS system_resources (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cpu_usage REAL NOT NULL,
    memory_usage REAL NOT NULL,
    disk_usage REAL NOT NULL,
    active_connections INTEGER NOT NULL,
    queue_length INTEGER NOT NULL,
    error_rate REAL NOT NULL,
    response_time_avg REAL NOT NULL
);
"""


def _bootstrap_analytics_tables() -> None:
    import psycopg2

    ensure_libpq_env()
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(ANALYTICS_BOOTSTRAP_SQL)
    finally:
        conn.close()


def main() -> int:
    ensure_libpq_env()
    print(f"Initializing schema at {os.environ['DATABASE_URL']}")
    ensure_postgres_extensions()
    run_alembic_migrations()
    initialize_shared_schema()
    _bootstrap_analytics_tables()
    print("Schema ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
