"""Tests for lease break analyzer and API."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.lease_break_api import lease_break_bp
from backend.services.lease_break_service import LeaseBreakAnalyzer


@pytest.fixture
def lease_break_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "lease-break-test"
    app.register_blueprint(lease_break_bp)
    return app


class TestLeaseBreakAnalyzer:
    def test_break_early_when_interim_cheaper(self):
        analyzer = LeaseBreakAnalyzer()
        with patch("backend.services.lease_break_service.db.session"):
            result = analyzer.analyze_break_cost(
                user_id=1,
                months_remaining=6,
                monthly_rent=1800.0,
                break_fee_percent=1.5,
                interim_monthly=500.0,
                persist=False,
            )

        assert result["scenario_a_cost"] > result["scenario_b_cost"]
        assert result["recommendation"] == "break_early"
        assert result["savings"] > 0

    def test_stay_when_break_fee_high(self):
        analyzer = LeaseBreakAnalyzer()
        result = analyzer.analyze_break_cost(
            user_id=1,
            months_remaining=3,
            monthly_rent=1200.0,
            break_fee_percent=4.0,
            interim_monthly=900.0,
            persist=False,
        )
        assert result["recommendation"] in {"stay_through_lease", "either", "break_early"}

    def test_negotiation_script_fields(self):
        analyzer = LeaseBreakAnalyzer()
        script = analyzer.generate_negotiation_script(
            months_remaining=6,
            monthly_rent=1800.0,
            break_fee_percent=1.5,
            savings_if_negotiated=2500.0,
        )
        assert len(script["talking_points"]) >= 3
        assert "Subject:" in script["email_template"]
        assert "lease" in script["phone_script"].lower()

    def test_persists_record(self, lease_break_app):
        analyzer = LeaseBreakAnalyzer()
        with lease_break_app.app_context(), patch(
            "backend.services.lease_break_service.db.session"
        ) as session:
            result = analyzer.analyze_break_cost(
                user_id=1,
                months_remaining=6,
                monthly_rent=1800.0,
                break_fee_percent=1.5,
                persist=True,
            )
        assert result["analysis_id"] is not None
        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_invalid_months(self):
        analyzer = LeaseBreakAnalyzer()
        with pytest.raises(ValueError):
            analyzer.analyze_break_cost(1, 0, 1800.0, persist=False)


class TestLeaseBreakApi:
    def test_analyze_endpoint(self, lease_break_app):
        payload = {
            "analysis_id": "test-id",
            "scenario_a_cost": 12000.0,
            "scenario_b_cost": 9000.0,
            "recommendation": "break_early",
            "savings": 3000.0,
            "negotiation_script": {"talking_points": [], "email_template": "", "phone_script": ""},
            "scenario_a": {"label": "Stay"},
            "scenario_b": {"label": "Break"},
            "timeline_impact": {},
        }
        client = lease_break_app.test_client()
        with lease_break_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.lease_break_api.get_current_user_db_id",
                return_value=1,
            ), patch("backend.routes.lease_break_api.LeaseBreakAnalyzer") as mock_cls:
                mock_cls.return_value.analyze_break_cost.return_value = payload
                response = client.post(
                    "/api/lease-break/analyze",
                    json={
                        "months_remaining": 6,
                        "monthly_rent": 1800,
                        "break_fee_percent": 1.5,
                    },
                )

        assert response.status_code == 200
        body = response.get_json()
        assert body["recommendation"] == "break_early"
        assert body["savings"] == 3000.0

    def test_analyze_requires_auth(self, lease_break_app):
        client = lease_break_app.test_client()
        with lease_break_app.app_context(), patch(
            "backend.routes.lease_break_api.get_current_user_db_id",
            return_value=None,
        ):
            response = client.post(
                "/api/lease-break/analyze",
                json={"months_remaining": 6, "monthly_rent": 1800},
            )
        assert response.status_code == 401

    def test_analyze_validation(self, lease_break_app):
        client = lease_break_app.test_client()
        with lease_break_app.app_context(), patch(
            "backend.routes.lease_break_api.get_current_user_db_id",
            return_value=1,
        ):
            response = client.post(
                "/api/lease-break/analyze",
                json={"months_remaining": 0, "monthly_rent": 1800},
            )
        assert response.status_code == 400
