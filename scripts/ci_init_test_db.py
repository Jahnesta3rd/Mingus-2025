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
    ensure_root_role,
    get_test_database_uri,
    init_ci_database_schema,
    truncate_all_tables,
    verify_ci_schema,
    wait_for_postgres,
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
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL not set", file=sys.stderr)
        return 2

    ensure_libpq_env()
    print(f"Initializing schema at {os.environ['DATABASE_URL']}")

    wait_for_postgres()
    ensure_root_role()
    _reset_test_data()

    # create_all + alembic upgrade (fallback stamp) + table verification
    init_ci_database_schema()

    # Analytics tables used by performance_monitor (not in SQLAlchemy models)
    _bootstrap_analytics_tables()

    verify_ci_schema()
    print("Schema ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ci_init_test_db failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
