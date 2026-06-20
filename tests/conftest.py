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
    initialize_shared_schema,
)


@pytest.fixture(scope="session", autouse=True)
def _shared_db_schema():
    """Create Postgres schema once for the entire test session."""
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


@pytest.fixture(autouse=True, scope="function")
def disable_auth_for_tests():
    """Disable authentication decorators for all tests"""
    # Patch both where it's defined and where it's used
    with patch('backend.auth.decorators.require_auth', lambda f: f):
        with patch('backend.auth.decorators.require_csrf', lambda f: f):
            with patch('backend.auth.decorators.require_admin', lambda f: f):
                with patch('backend.api.daily_outlook_api.require_auth', lambda f: f):
                    with patch('backend.api.daily_outlook_api.require_csrf', lambda f: f):
                        yield


# Additional shared fixtures can be added here as needed
