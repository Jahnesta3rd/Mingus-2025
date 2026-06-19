"""Unit tests for housing search zip fallback resolver (HRA-01)."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

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


class TestResolveSearchZip:
    def test_request_zip_used_when_valid(self):
        session = _mock_session()
        result = resolve_search_zip(40, "30309", session)
        assert result is not None
        assert result.zip_code == "30309"
        assert result.source == "request"
        session.query.assert_not_called()

    def test_housing_profile_fallback_when_request_empty(self):
        housing = MagicMock()
        housing.zip_or_city = "10001"
        session = _mock_session(housing=housing)
        result = resolve_search_zip(40, "", session)
        assert result is not None
        assert result.zip_code == "10001"
        assert result.source == "housing_profile"

    def test_user_profiles_fallback_when_no_housing_zip(self):
        user = MagicMock()
        user.email = "user40@example.com"
        profile = MagicMock()
        profile.zip_code = "85001"
        session = _mock_session(housing=None, user=user, profile=profile)
        result = resolve_search_zip(41, None, session)
        assert result is not None
        assert result.zip_code == "85001"
        assert result.source == "user_profiles"

    def test_returns_none_when_no_zip_anywhere(self):
        session = _mock_session(housing=None, user=None, profile=None)
        assert resolve_search_zip(99, "", session) is None

    def test_short_request_zip_skips_request_path(self):
        housing = MagicMock()
        housing.zip_or_city = "10001"
        session = _mock_session(housing=housing)
        result = resolve_search_zip(40, "123", session)
        assert result is not None
        assert result.source == "housing_profile"
