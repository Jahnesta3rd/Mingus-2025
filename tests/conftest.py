#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Daily Outlook testing suite.

This module provides shared fixtures and configuration for all tests,
including authentication bypass for API endpoint testing.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True, scope="function")
def disable_auth_for_tests():
    """Disable authentication decorators for all tests"""
    with patch('backend.auth.decorators.require_auth', lambda f: f):
        with patch('backend.auth.decorators.require_csrf', lambda f: f):
            with patch('backend.auth.decorators.require_admin', lambda f: f):
                yield


# Additional shared fixtures can be added here as needed
