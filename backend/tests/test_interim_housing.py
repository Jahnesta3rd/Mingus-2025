"""Tests for interim housing analyzer and API."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.interim_housing_api import interim_housing_bp
from backend.services.interim_housing_service import InterimHousingAnalyzer


@pytest.fixture
def interim_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "interim-housing-test"
    app.register_blueprint(interim_housing_bp)
    return app


class TestInterimHousingAnalyzer:
    def test_analyze_returns_three_scenarios(self):
        analyzer = InterimHousingAnalyzer()
        with patch.object(
            analyzer,
            "_resolve_icc_inputs",
            return_value=("10001", 16050.0, 765.0, 1850.0),
        ), patch.object(
            analyzer,
            "get_market_rent_2br",
            return_value={"median_2br_rent": 1800.0, "source": "test"},
        ):
            result = analyzer.analyze_interim_options(1, "10001", 16050.0, 765.0)

        assert len(result["scenarios"]) == 3
        keys = {row["key"] for row in result["scenarios"]}
        assert keys == {"roommate", "family", "sublet"}

    def test_roommate_rent_is_half_of_2br(self):
        analyzer = InterimHousingAnalyzer()
        with patch.object(
            analyzer,
            "_resolve_icc_inputs",
            return_value=("10001", 16050.0, 765.0, 1850.0),
        ), patch.object(
            analyzer,
            "get_market_rent_2br",
            return_value={"median_2br_rent": 1800.0, "source": "test"},
        ):
            result = analyzer.analyze_interim_options(1, "10001", 16050.0, 765.0)

        roommate = next(s for s in result["scenarios"] if s["key"] == "roommate")
        assert roommate["monthly_rent"] == 900.0
        assert roommate["monthly_savings_vs_solo"] == 950.0

    def test_phased_exit_plan_has_three_phases(self):
        analyzer = InterimHousingAnalyzer()
        with patch.object(
            analyzer,
            "_resolve_icc_inputs",
            return_value=("10001", 16050.0, 765.0, 1850.0),
        ), patch.object(
            analyzer,
            "get_market_rent_2br",
            return_value={"median_2br_rent": 1800.0, "source": "test"},
        ):
            result = analyzer.analyze_interim_options(1, "10001", 16050.0, 765.0)

        plan = result["phased_exit_plan"]
        assert len(plan["phases"]) == 3
        assert plan["phases"][0]["scenario_key"] == "family"
        assert plan["phases"][1]["scenario_key"] == "sublet"
        assert plan["phases"][2]["scenario_key"] == "roommate"
        assert plan["total_months_to_solo_readiness"] > 0

    def test_solo_comparison_timeline(self):
        analyzer = InterimHousingAnalyzer()
        with patch.object(
            analyzer,
            "_resolve_icc_inputs",
            return_value=("10001", 16050.0, 765.0, 1850.0),
        ), patch.object(
            analyzer,
            "get_market_rent_2br",
            return_value={"median_2br_rent": 1800.0, "source": "test"},
        ):
            result = analyzer.analyze_interim_options(1, "10001", 16050.0, 765.0)

        solo = result["solo_comparison"]
        assert solo["monthly_gap"] == 765.0
        assert solo["startup_cost_needed"] == 16050.0
        assert solo["timeline_months"] == 21

    def test_conversation_templates_present(self):
        analyzer = InterimHousingAnalyzer()
        with patch.object(
            analyzer,
            "_resolve_icc_inputs",
            return_value=("10001", 16050.0, 765.0, 1850.0),
        ), patch.object(
            analyzer,
            "get_market_rent_2br",
            return_value={"median_2br_rent": 1800.0, "source": "test"},
        ):
            result = analyzer.analyze_interim_options(1, "10001", 16050.0, 765.0)

        templates = result["conversation_templates"]
        assert "how_to_ask_family" in templates
        assert "how_to_vet_roommate" in templates
        assert "sublet_red_flags" in templates


class TestInterimHousingApi:
    def test_scenarios_endpoint(self, interim_app):
        payload = {
            "zip_code": "10001",
            "market_rent_2br": 1800.0,
            "solo_comparison": {
                "label": "Solo 1BR apartment",
                "monthly_rent": 1850.0,
                "monthly_gap": 765.0,
                "startup_cost_needed": 16050.0,
                "timeline_months": 21,
            },
            "scenarios": [{"key": "roommate"}],
            "phased_exit_plan": {"phases": [], "total_months_to_solo_readiness": 10},
            "conversation_templates": {},
            "feature_matrix_keys": [],
        }

        client = interim_app.test_client()
        with interim_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.interim_housing_api.get_current_user_db_id",
                return_value=1,
            ), patch(
                "backend.routes.interim_housing_api.InterimHousingAnalyzer"
            ) as analyzer_cls:
                analyzer_cls.return_value.analyze_interim_options.return_value = payload
                response = client.get(
                    "/api/interim-housing/scenarios?zip_code=10001&monthly_gap=765&startup_cost_needed=16050",
                )

        assert response.status_code == 200
        body = response.get_json()
        assert body["zip_code"] == "10001"
        assert body["solo_comparison"]["monthly_gap"] == 765.0

    def test_scenarios_requires_auth(self, interim_app):
        client = interim_app.test_client()
        with interim_app.app_context(), patch(
            "backend.routes.interim_housing_api.get_current_user_db_id",
            return_value=None,
        ):
            response = client.get("/api/interim-housing/scenarios?zip_code=10001")
        assert response.status_code == 401

    def test_invalid_monthly_gap(self, interim_app):
        with interim_app.test_client() as client, patch(
            "backend.routes.interim_housing_api.get_current_user_db_id",
            return_value=1,
        ):
            response = client.get(
                "/api/interim-housing/scenarios?monthly_gap=not-a-number",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 400
