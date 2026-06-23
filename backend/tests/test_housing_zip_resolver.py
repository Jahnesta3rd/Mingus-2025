"""Unit tests for housing search zip fallback resolver (HRA-01)."""

from __future__ import annotations

import os
import sys
import types
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Avoid resume_endpoints DB init when importing user_profile_context.
sys.modules.setdefault("backend.api", types.ModuleType("backend.api"))
sys.modules["backend.api.profile_endpoints"] = MagicMock(
    get_db_connection=MagicMock(),
)

from backend.utils.user_profile_context import resolve_search_zip  # noqa: E402


def _mock_session(*, housing=None, user=None, profile=None):
    session = MagicMock()

    def query(model):
        q = MagicMock()
        if model.__name__ == "HousingProfile":
            q.filter_by.return_value.first.return_value = housing
        elif model.__name__ == "User":
            q.filter_by.return_value.first.return_value = user
        elif model.__name__ == "UserProfile":
            q.filter_by.return_value.first.return_value = profile
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    session.query.side_effect = query
    return session


def test_request_zip_used_when_valid():
    session = _mock_session()
    result = resolve_search_zip(40, "30309", session)
    assert result is not None
    assert result.zip_code == "30309"
    assert result.source == "request"
    session.query.assert_not_called()


def test_fallback_to_housing_profile_zip():
    housing = MagicMock()
    housing.zip_or_city = "10001"
    session = _mock_session(housing=housing)
    result = resolve_search_zip(40, "", session)
    assert result is not None
    assert result.zip_code == "10001"
    assert result.source == "housing_profile"


def test_fallback_to_user_profiles_zip():
    user = MagicMock()
    user.email = "user40@example.com"
    profile = MagicMock()
    profile.zip_code = "85001"
    session = _mock_session(housing=None, user=user, profile=profile)
    result = resolve_search_zip(41, None, session)
    assert result is not None
    assert result.zip_code == "85001"
    assert result.source == "user_profiles"


def test_returns_400_when_no_zip_anywhere():
    """Resolver returns None when all tiers exhausted (endpoint maps this to 400 ZIP_REQUIRED)."""
    session = _mock_session(housing=None, user=None, profile=None)
    assert resolve_search_zip(99, "", session) is None
    assert resolve_search_zip(99, None, session) is None
