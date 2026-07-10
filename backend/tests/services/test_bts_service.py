"""Unit tests for BTSService tier dates, budget estimates, and shortfall jobs."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from backend.services import bts_service as bts_mod
from backend.services.bts_service import (
    BTSService,
    compute_tier_dates,
    estimate_bts_budget,
)


FIXED_TODAY = date(2026, 7, 10)


def _stub_db_persist(monkeypatch):
    """Avoid needing a Flask app context when persisting sessions in unit tests."""
    import uuid as uuid_mod

    class FakeSession:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.session_id = uuid_mod.uuid4()

    fake_db = type("DB", (), {"session": type("S", (), {"add": staticmethod(lambda x: None), "commit": staticmethod(lambda: None)})()})()
    monkeypatch.setattr(bts_mod, "BackToSchoolSession", FakeSession)
    monkeypatch.setattr(bts_mod, "db", fake_db)


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(bts_mod, "_today", lambda: FIXED_TODAY)
    _stub_db_persist(monkeypatch)

    def fake_forecast(user_id, days=90):
        start = FIXED_TODAY
        rows = []
        balance = 600.0
        for i in range(days):
            d0 = start + timedelta(days=i)
            # Dip mid-window then recover — mirrors sample response shape.
            if i == 35:  # ~Aug 14
                balance = 520.0
            elif i == 42:  # ~Aug 21
                balance = 280.0
            elif i == 49:  # ~Aug 28
                balance = 450.0
            else:
                balance = max(200.0, balance - 2)

            status = "healthy"
            if balance < 200:
                status = "danger"
            elif balance < 1000:
                status = "warning" if balance < 400 else "healthy"

            rows.append(
                {
                    "date": d0.isoformat(),
                    "opening_balance": balance,
                    "closing_balance": balance,
                    "net_change": 0.0,
                    "balance_status": status,
                }
            )
        return rows

    monkeypatch.setattr(bts_mod, "generate_daily_forecast", fake_forecast)
    return BTSService()


def test_compute_tier_dates():
    bts = date(2026, 8, 28)
    tiers = compute_tier_dates(bts)
    assert tiers["tier1"] == date(2026, 8, 14)
    assert tiers["tier2"] == date(2026, 8, 21)
    assert tiers["tier3"] == date(2026, 8, 28)


def test_estimate_bts_budget_by_age():
    assert estimate_bts_budget(8) == 280.0
    assert estimate_bts_budget(None) == 300.0
    assert estimate_bts_budget(16) == 500.0


def test_setup_bts_session_returns_tiers(service):
    result = service.setup_bts_session(
        userId="user-abc",
        btsDate=date(2026, 8, 28),
        childName="Emma",
        childAge=8,
        childGender="girl",
    )

    assert result["btsDate"] == "2026-08-28"
    assert result["tier1Date"] == "2026-08-14"
    assert result["tier2Date"] == "2026-08-21"
    assert result["tier3Date"] == "2026-08-28"
    assert result["daysUntilSchool"] == 49
    # Session IDs are UUIDs persisted in back_to_school_sessions.
    import uuid as uuid_mod

    uuid_mod.UUID(result["sessionId"])
    assert result["availableBalances"]["tier1"]["date"] == "2026-08-14"
    assert result["availableBalances"]["tier1"]["forecastedBalance"] == 520.0
    assert result["availableBalances"]["tier2"]["forecastedBalance"] == 280.0
    assert result["child"]["name"] == "Emma"
    # 520 >= 280 estimated → no shortfall
    assert result["shortfall"] == 0
    assert result["recommendedSecondJobs"] == []


def test_setup_recommends_jobs_on_shortfall(service, monkeypatch):
    def low_forecast(user_id, days=90):
        start = FIXED_TODAY
        return [
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "opening_balance": 50.0,
                "closing_balance": 50.0,
                "net_change": 0.0,
                "balance_status": "danger",
            }
            for i in range(days)
        ]

    monkeypatch.setattr(bts_mod, "generate_daily_forecast", low_forecast)

    result = service.setup_bts_session(
        userId="user-abc",
        btsDate=date(2026, 8, 28),
        childAge=8,
    )

    assert result["shortfall"] == 230.0  # 280 - 50
    assert len(result["recommendedSecondJobs"]) >= 1
    job = result["recommendedSecondJobs"][0]
    assert "jobId" in job
    assert job["potentialEarnings"] > 0
    assert job["couldEarnBy"] == "2026-08-21"


def test_get_forecast_timeline(service):
    timeline = service.get_forecast_timeline("user-abc", date(2026, 8, 28))
    assert timeline["btsDate"] == "2026-08-28"
    keys = [p["key"] for p in timeline["timeline"]]
    assert keys == ["today", "tier1", "tier2", "tier3"]
    assert timeline["timeline"][0]["date"] == "2026-07-10"
    assert timeline["timeline"][1]["forecastedBalance"] == 520.0


def test_rejects_past_bts_date(service):
    with pytest.raises(ValueError, match="future"):
        service.setup_bts_session(
            userId="user-abc",
            btsDate=date(2026, 6, 1),
        )


def test_classify_status_import():
    # Ensure cash forecast status helper stays compatible.
    from backend.services.cash_forecast_service import classify_status

    assert classify_status(Decimal("1200")) == "healthy"
    assert classify_status(Decimal("300")) == "warning"
    assert classify_status(Decimal("50")) == "danger"
