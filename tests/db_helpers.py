#!/usr/bin/env python3
"""PostgreSQL test database helpers for pytest and unittest suites."""

from __future__ import annotations

import os
import threading

from sqlalchemy import text

DEFAULT_TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/mingus_test"

_schema_lock = threading.Lock()
_schema_initialized = False


def get_test_database_uri() -> str:
    """Return the PostgreSQL URL used for tests (CI sets DATABASE_URL)."""
    url = os.environ.get("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    if url.startswith("sqlite:"):
        raise RuntimeError(
            "Tests require PostgreSQL (models use JSONB/UUID). "
            f"Got SQLite DATABASE_URL: {url!r}. "
            "Set DATABASE_URL to a postgres URL or start the CI postgres service."
        )
    return url


def configure_app_for_tests(app) -> None:
    """Apply standard Flask/SQLAlchemy settings for integration tests."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = get_test_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def ensure_all_models_imported() -> None:
    """Load all SQLAlchemy models so create_all() sees every table."""
    import backend.models  # noqa: F401
    import backend.models.professional_tier_models  # noqa: F401
    import backend.models.tax_adjacent_models  # noqa: F401


def initialize_shared_schema(db=None) -> None:
    """Create all tables once per test run (idempotent via checkfirst)."""
    global _schema_initialized
    if _schema_initialized:
        return

    with _schema_lock:
        if _schema_initialized:
            return

        from flask import Flask

        if db is None:
            from backend.models.database import db as db_instance

            db = db_instance

        app = Flask("test_schema_init")
        configure_app_for_tests(app)
        ensure_all_models_imported()
        db.init_app(app)
        with app.app_context():
            db.create_all()
        _schema_initialized = True


def truncate_all_tables(db) -> None:
    """Remove row data between tests without dropping schema objects."""
    ensure_all_models_imported()
    with db.engine.begin() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))
        for table in reversed(db.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
        conn.execute(text("SET session_replication_role = 'origin'"))


def cleanup_test_data(db) -> None:
    """Clear test data and SQLAlchemy session state after a test."""
    db.session.remove()
    try:
        truncate_all_tables(db)
    except Exception:
        db.session.rollback()
        raise


def init_test_database(app, db) -> None:
    """Bind SQLAlchemy and ensure shared schema exists."""
    configure_app_for_tests(app)
    db.init_app(app)
    initialize_shared_schema(db)


def destroy_test_database(app, db) -> None:
    """Clear data after a test; keep schema intact for subsequent tests."""
    with app.app_context():
        cleanup_test_data(db)
