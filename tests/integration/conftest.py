"""Integration test fixtures — inherit shared app/DB setup from tests/conftest.py."""

import pytest


@pytest.fixture
def client(daily_outlook_client):
    """HTTP client with daily_outlook_api routes registered."""
    return daily_outlook_client
