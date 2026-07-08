"""Tests for phased independence planner and API."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.phased_independence_api import phased_independence_bp
from backend.services.phased_independence_service import PhasedIndependencePlanner


@pytest.fixture
def phased_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "phased-independence-test"
    app.register_blueprint(phased_independence_bp)
    return app


class TestPhasedIndependencePlanner:
    def test_generate_tiers_cumulative_totals(self):
        planner = PhasedIndependencePlanner()
        tiers = planner.generate_tiers(16100.0)

        assert tiers["tier_0"]["cumulative_cost"] == 3500.0
        assert tiers["tier_1"]["cumulative_cost"] == 6000.0
        assert tiers["tier_2"]["cumulative_cost"] == 8000.0
        assert tiers["tier_3"]["cumulative_cost"] == 16100.0
        assert tiers["summary"]["tier_3_total"] == 16100.0

    def test_leave_by_month_scenarios(self):
        planner = PhasedIndependencePlanner()
        scenarios = planner.leave_by_month_scenarios(765.0, 600.0)

        assert len(scenarios) == 4
        leave_6 = next(row for row in scenarios if row["key"] == "leave_6")
        assert leave_6["cumulative_startup"] == 6000.0
        assert leave_6["tier_levels"] == [0, 1]
        assert leave_6["housing"] == "roommate"
        assert leave_6["months_to_fund"] == 10

    def test_buying_guide_for_tier(self):
        planner = PhasedIndependencePlanner()
        guide = planner.buying_guide_for_tier(0)

        assert guide["tier"] == 0
        assert guide["budget_target"] == 3500.0
        assert len(guide["categories"]) >= 3
        assert any(r["name"] == "IKEA" for r in guide["retailers"])

    def test_buying_guide_invalid_tier(self):
        planner = PhasedIndependencePlanner()
        with pytest.raises(ValueError):
            planner.buying_guide_for_tier(9)

    def test_contingency_scenarios(self):
        planner = PhasedIndependencePlanner()
        rows = planner.contingency_scenarios("leave_6", 765.0, 600.0)

        assert len(rows) == 4
        assert any(row["key"] == "savings_drop_20" for row in rows)
        assert any(row["key"] == "side_income_plus_200" for row in rows)

    def test_build_timeline_payload(self):
        planner = PhasedIndependencePlanner()
        payload = planner.build_timeline_payload(765.0, 600.0, 16100.0)

        assert payload["total_monthly_gap"] == 765.0
        assert payload["monthly_savings"] == 600.0
        assert "tier_definitions" in payload
        assert len(payload["buying_guides"]) == 4
        assert payload["default_scenario_key"] == "leave_6"


class TestPhasedIndependenceApi:
    def test_timeline_endpoint(self, phased_app):
        payload = {
            "total_monthly_gap": 765.0,
            "monthly_savings": 600.0,
            "startup_cost_full": 16100.0,
            "tier_definitions": {},
            "scenarios": [{"key": "leave_6"}],
            "buying_guides": {},
            "contingency_scenarios": [],
            "default_scenario_key": "leave_6",
            "selected_scenario_key": "leave_6",
        }

        client = phased_app.test_client()
        with phased_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.phased_independence_api.get_current_user_db_id",
                return_value=1,
            ), patch(
                "backend.routes.phased_independence_api.IndependenceCostAssessment.query"
            ), patch(
                "backend.routes.phased_independence_api.PhasedIndependencePlanner"
            ) as planner_cls:
                instance = planner_cls.return_value
                instance.build_timeline_payload.return_value = payload
                instance.contingency_scenarios.return_value = []
                response = client.get(
                    "/api/phased-independence/timeline?total_gap=765&monthly_savings=600&startup_cost_full=16100",
                )

        assert response.status_code == 200
        body = response.get_json()
        assert body["total_monthly_gap"] == 765.0

    def test_timeline_requires_auth(self, phased_app):
        client = phased_app.test_client()
        with phased_app.app_context(), patch(
            "backend.routes.phased_independence_api.get_current_user_db_id",
            return_value=None,
        ):
            response = client.get(
                "/api/phased-independence/timeline?total_gap=765&monthly_savings=600",
            )
        assert response.status_code == 401

    def test_timeline_missing_total_gap(self, phased_app):
        client = phased_app.test_client()
        with phased_app.app_context(), patch(
            "backend.routes.phased_independence_api.get_current_user_db_id",
            return_value=1,
        ):
            response = client.get("/api/phased-independence/timeline")
        assert response.status_code == 400
