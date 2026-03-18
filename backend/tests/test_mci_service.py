import json
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pytest
from flask import Flask

from backend.api.mci_api import mci_api
from backend.services import mci_cache
from backend.services import mci_service


@pytest.mark.parametrize(
    "layoff_rate,expected",
    [
        (0.8, "green"),
        (1.2, "amber"),
        (1.8, "red"),
    ],
)
def test_labor_market_strength_severity(layoff_rate, expected):
    assert (
        mci_service.get_severity(layoff_rate=layoff_rate)
        == expected
    )


def test_labor_market_strength_direction():
    assert mci_service.get_direction(latest=1.3, three_month_avg=1.5) == "down"
    assert mci_service.get_direction(latest=1.3, three_month_avg=1.1) == "up"


@pytest.mark.parametrize(
    "rate,expected",
    [
        (5.5, "green"),
        (6.5, "amber"),
        (8.0, "red"),
    ],
)
def test_housing_affordability_pressure_severity(rate, expected):
    assert mci_service.get_severity(rate=rate) == expected


@pytest.mark.parametrize(
    "price,expected",
    [
        (2.80, "green"),
        (3.50, "amber"),
        (4.20, "red"),
    ],
)
def test_transportation_cost_burden_severity(price, expected):
    assert mci_service.get_severity(price=price) == expected


@pytest.mark.parametrize(
    "apr,expected",
    [
        (17.0, "green"),
        (20.0, "amber"),
        (23.5, "red"),
    ],
)
def test_consumer_debt_conditions_severity(apr, expected):
    assert mci_service.get_severity(apr=apr) == expected


@pytest.mark.parametrize(
    "quit_rate,expected",
    [
        (2.8, "green"),
        (2.2, "amber"),
        (1.8, "red"),
    ],
)
def test_career_income_mobility_severity(quit_rate, expected):
    assert mci_service.get_severity(quit_rate=quit_rate) == expected


@pytest.fixture
def all_green_constituents():
    constituents = [
        {"slug": "labor_market_strength", "severity": "green", "weight": 0.25},
        {
            "slug": "housing_affordability_pressure",
            "severity": "green",
            "weight": 0.25,
        },
        {
            "slug": "transportation_cost_burden",
            "severity": "green",
            "weight": 0.10,
        },
        {
            "slug": "consumer_debt_conditions",
            "severity": "green",
            "weight": 0.20,
        },
        {
            "slug": "career_income_mobility",
            "severity": "green",
            "weight": 0.15,
        },
        {
            "slug": "wellness_cost_index",
            "severity": "green",
            "weight": 0.05,
        },
    ]
    composite_score = mci_service.calculate_composite_score(constituents)
    return {"composite_score": composite_score, "constituents": constituents}


@pytest.fixture
def all_red_constituents():
    constituents = [
        {"slug": "labor_market_strength", "severity": "red", "weight": 0.25},
        {
            "slug": "housing_affordability_pressure",
            "severity": "red",
            "weight": 0.25,
        },
        {
            "slug": "transportation_cost_burden",
            "severity": "red",
            "weight": 0.10,
        },
        {
            "slug": "consumer_debt_conditions",
            "severity": "red",
            "weight": 0.20,
        },
        {
            "slug": "career_income_mobility",
            "severity": "red",
            "weight": 0.15,
        },
        {
            "slug": "wellness_cost_index",
            "severity": "red",
            "weight": 0.05,
        },
    ]
    composite_score = mci_service.calculate_composite_score(constituents)
    return {"composite_score": composite_score, "constituents": constituents}


@pytest.fixture
def mixed_constituents():
    constituents = [
        {"slug": "labor_market_strength", "severity": "green", "weight": 0.25},
        {
            "slug": "housing_affordability_pressure",
            "severity": "red",
            "weight": 0.25,
        },
        {
            "slug": "transportation_cost_burden",
            "severity": "amber",
            "weight": 0.10,
        },
        {
            "slug": "consumer_debt_conditions",
            "severity": "amber",
            "weight": 0.20,
        },
        {"slug": "career_income_mobility", "severity": "green", "weight": 0.15},
        {"slug": "wellness_cost_index", "severity": "green", "weight": 0.05},
    ]
    composite_score = mci_service.calculate_composite_score(constituents)
    return {"composite_score": composite_score, "constituents": constituents}


def test_all_green_composite_score(all_green_constituents):
    assert all_green_constituents["composite_score"] >= 75


def test_all_red_composite_score(all_red_constituents):
    assert all_red_constituents["composite_score"] <= 25


def test_mixed_composite_score(mixed_constituents):
    assert mixed_constituents["composite_score"] == 56.0


def test_cache_returns_value_within_ttl():
    now = datetime.utcnow()
    cached_at = (now - timedelta(days=3)).isoformat()
    snapshot = {"composite_score": 12.34, "constituents": []}
    payload = {"cached_at": cached_at, "snapshot": snapshot}

    m = mock_open(read_data=json.dumps(payload))
    with patch("backend.services.mci_cache.open", m):
        assert mci_cache.get_cached_mci() == snapshot


def test_cache_returns_none_when_expired():
    now = datetime.utcnow()
    cached_at = (now - timedelta(days=10)).isoformat()
    payload = {"cached_at": cached_at, "snapshot": {"composite_score": 1.0}}

    m = mock_open(read_data=json.dumps(payload))
    with patch("backend.services.mci_cache.open", m):
        assert mci_cache.get_cached_mci() is None


def test_cache_returns_none_when_missing_file():
    with patch("backend.services.mci_cache.open", side_effect=FileNotFoundError):
        assert mci_cache.get_cached_mci() is None


def test_api_endpoint_smoke(mixed_constituents):
    app = Flask(__name__)
    app.register_blueprint(mci_api)
    client = app.test_client()

    with patch("backend.api.mci_api.get_or_fetch_mci", return_value=mixed_constituents):
        resp = client.get("/api/mci/snapshot")

    assert resp.status_code == 200
    assert resp.json["composite_score"] == 56.0
    assert len(resp.json["constituents"]) == 6
    assert "Cache-Control" in resp.headers

