"""Tests for WARN Firehose client."""

from __future__ import annotations

import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import backend.services.warn_act_client as warn_act_client
from backend.services.warn_act_client import WarnActClient


@pytest.fixture(autouse=True)
def reset_call_counter():
    warn_act_client._call_counter = 0
    yield
    warn_act_client._call_counter = 0


def _mock_response(*, status_code: int, json_data):
    response = MagicMock()
    response.status_code = status_code
    response.url = "https://warnfirehose.com/api/warn"
    response.json.return_value = json_data
    return response


def test_search_by_name_returns_normalized_list_on_200():
    payload = [
        {
            "company_name": "Acme Corp",
            "state": "ca",
            "filing_date": "2026-03-01",
            "worker_count": 250,
            "layoff_type": "plant closure",
            "notice_url": "https://example.com/notice.pdf",
        }
    ]
    client = WarnActClient(api_key="")
    with patch.object(client.session, "get", return_value=_mock_response(status_code=200, json_data=payload)) as mock_get:
        results = client.search_by_name("Acme Corp", state="CA", days_back=90)

    assert len(results) == 1
    assert results[0] == {
        "company_name": "Acme Corp",
        "state": "CA",
        "filing_date": date(2026, 3, 1),
        "worker_count": 250,
        "layoff_type": "closure",
        "notice_url": "https://example.com/notice.pdf",
    }
    mock_get.assert_called_once()
    params = mock_get.call_args.kwargs["params"]
    assert params["company"] == "Acme Corp"
    assert params["state"] == "CA"
    assert "date_from" in params


def test_search_by_name_returns_empty_on_429():
    client = WarnActClient(api_key="")
    with patch.object(
        client.session,
        "get",
        return_value=_mock_response(status_code=429, json_data={"error": "rate limit"}),
    ):
        results = client.search_by_name("Acme Corp")
    assert results == []


def test_search_by_name_returns_empty_on_500():
    client = WarnActClient(api_key="")
    with patch.object(
        client.session,
        "get",
        return_value=_mock_response(status_code=500, json_data={"error": "server"}),
    ):
        results = client.search_by_name("Acme Corp")
    assert results == []


def test_search_by_cik_crossref_returns_empty_when_no_cik_match():
    payload = [
        {
            "cik": "0000320193",
            "company_name": "Apple Inc",
            "filing_date": "2026-02-15",
            "state": "CA",
            "worker_count": 100,
            "layoff_type": "layoff",
        }
    ]
    client = WarnActClient(api_key="")
    with patch.object(
        client.session,
        "get",
        return_value=_mock_response(status_code=200, json_data=payload),
    ):
        results = client.search_by_cik_crossref("0000789019")
    assert results == []


def test_search_by_cik_crossref_returns_matches_for_cik():
    payload = [
        {
            "cik": "320193",
            "company_name": "Apple Inc",
            "filing_date": "2026-02-15",
            "state": "CA",
            "worker_count": 100,
            "layoff_type": "layoff",
            "notice_url": None,
        }
    ]
    client = WarnActClient(api_key="")
    with patch.object(
        client.session,
        "get",
        return_value=_mock_response(status_code=200, json_data=payload),
    ):
        results = client.search_by_cik_crossref("0000320193")

    assert len(results) == 1
    assert results[0]["company_name"] == "Apple Inc"
    assert results[0]["filing_date"] == date(2026, 2, 15)


def test_api_key_header_sent_when_env_set(monkeypatch):
    monkeypatch.setenv("WARN_FIREHOSE_API_KEY", "test-secret-key")
    client = WarnActClient()
    assert client.session.headers.get("Authorization") == "Bearer test-secret-key"


def test_no_auth_header_when_key_absent(monkeypatch):
    monkeypatch.delenv("WARN_FIREHOSE_API_KEY", raising=False)
    client = WarnActClient(api_key="")
    assert "Authorization" not in client.session.headers
