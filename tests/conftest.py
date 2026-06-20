#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Daily Outlook testing suite.

This module provides shared fixtures and configuration for all tests,
including authentication bypass for API endpoint testing.
"""

import pytest
from unittest.mock import patch
from flask import Flask

from backend.models.database import db
from tests.db_helpers import (
    cleanup_test_data,
    configure_app_for_tests,
    ensure_libpq_env,
    initialize_shared_schema,
    persist_test_user,
)


@pytest.fixture(scope="session", autouse=True)
def _shared_db_schema():
    """Create Postgres schema once for the entire test session."""
    ensure_libpq_env()
    initialize_shared_schema(db)
    yield


@pytest.fixture
def app(_shared_db_schema):
    """Flask app backed by PostgreSQL (DATABASE_URL from CI or local default)."""
    flask_app = Flask(__name__)
    configure_app_for_tests(flask_app)
    db.init_app(flask_app)
    with flask_app.app_context():
        yield flask_app
        cleanup_test_data(db)


@pytest.fixture
def sample_user(app):
    """Create a user whose id is safe to use after the DB session closes."""
    with app.app_context():
        return persist_test_user(
            db,
            user_id="test_user_123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            tier="budget",
        )


@pytest.fixture(autouse=True, scope="function")
def disable_auth_for_tests():
    """Bypass JWT auth and no-op route decorators for API tests."""
    fake_payload = {
        "user_id": "test_user",
        "email": "test@example.com",
        "exp": 9999999999,
    }
    passthrough = lambda f: f
    with patch("backend.auth.decorators.jwt.decode", return_value=fake_payload):
        with patch("backend.auth.decorators.require_auth", passthrough):
            with patch("backend.auth.decorators.require_csrf", passthrough):
                with patch("backend.auth.decorators.require_admin", passthrough):
                    with patch("backend.api.daily_outlook_api.require_auth", passthrough):
                        with patch("backend.api.daily_outlook_api.require_csrf", passthrough):
                            with patch("backend.api.optimal_location_api.require_auth", passthrough):
                                with patch("backend.api.optimal_location_api.require_csrf", passthrough):
                                    yield
