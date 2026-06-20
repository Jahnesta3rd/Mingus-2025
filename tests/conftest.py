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
def mock_auth_defaults():
    """Default auth/tier mocks for API modules used across pytest suites."""
    def _default_user_id():
        return 1

    def _allow_tier(user_id, required_tier=None):
        return True

    patches = [
        patch("backend.api.daily_outlook_api.get_current_user_id", _default_user_id),
        patch("backend.api.daily_outlook_api.check_user_tier_access", _allow_tier),
        patch("backend.api.optimal_location_api.get_current_user_id", _default_user_id),
        patch(
            "backend.api.optimal_location_api.check_optimal_location_feature_access",
            lambda _uid: True,
        ),
    ]
    with patches[0], patches[1], patches[2], patches[3]:
        yield
