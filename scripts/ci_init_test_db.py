#!/usr/bin/env python3
"""Initialize the CI test Postgres schema once before pytest runs."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.db_helpers import (
    ensure_libpq_env,
    get_test_database_uri,
    initialize_shared_schema,
    stamp_alembic_head,
    truncate_all_tables,
    verify_users_table,
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


def _reset_test_data() -> None:
    """Clear any leftover rows so init is safe to re-run locally."""
    import psycopg2
    from flask import Flask
    from backend.models.database import db

    ensure_libpq_env()
    app = Flask("ci_init_reset")
    app.config["SQLALCHEMY_DATABASE_URI"] = get_test_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        try:
            truncate_all_tables(db)
        except Exception:
            pass


def main() -> int:
    ensure_libpq_env()
    print(f"Initializing schema at {os.environ['DATABASE_URL']}")

    # 0) Clear leftover data when re-running init against an existing DB
    _reset_test_data()

    # 1) Extensions required by models/migrations
    from tests.db_helpers import ensure_postgres_extensions  # noqa: E402

    ensure_postgres_extensions()

    # 2) create_all first — Alembic chain root (004) FK-references users but no
    #    migration creates users; SQLAlchemy metadata is the source of truth in CI.
    initialize_shared_schema()

    # 3) Sync alembic_version without re-running migrations that duplicate tables
    stamp_alembic_head()

    # 4) Analytics tables used by performance_monitor (not in SQLAlchemy models)
    _bootstrap_analytics_tables()

    # 5) Fail fast with a clear message if schema init did not create users
    verify_users_table()

    print("Schema ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ci_init_test_db failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
