#!/usr/bin/env python3
"""PostgreSQL test database helpers for pytest and unittest suites."""

from __future__ import annotations

import os

DEFAULT_TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/mingus_test"


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


def init_test_database(app, db) -> None:
    """Bind SQLAlchemy and create tables on the test database."""
    ensure_all_models_imported()
    configure_app_for_tests(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()


def destroy_test_database(app, db) -> None:
    """Drop all tables and clear the session after a test."""
    with app.app_context():
        db.session.remove()
        db.drop_all()
