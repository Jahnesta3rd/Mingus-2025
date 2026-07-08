"""Tests for SideIncomeAccelerator and side income API."""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.side_income_api import side_income_bp
from backend.services.side_income_accelerator import SideIncomeAccelerator


def _sample_df1_jobs() -> list[dict]:
    return [
        {
            "title": "Weekend Tutor",
            "type": "gig",
            "hourly_range": "$30-45/hr",
            "hours_per_week": 10,
            "monthly_est": 600.0,
            "schedule_fit": "Flexible weekends",
            "why_it_fits": "Uses teaching skills",
            "debt_impact": "Adds cushion",
            "first_step": "Sign up on a tutoring platform",
            "startup_cost": "$0-100",
        },
        {
            "title": "Freelance Design",
            "type": "freelance",
            "hourly_range": "$50-80/hr",
            "hours_per_week": 10,
            "monthly_est": 1200.0,
            "schedule_fit": "Remote, flexible",
            "why_it_fits": "Leverages design portfolio",
            "debt_impact": "Strong monthly boost",
            "first_step": "Create portfolio site",
            "startup_cost": "$0-500",
        },
        {
            "title": "Retail Shift",
            "type": "part_time",
            "hourly_range": "$18-22/hr",
            "hours_per_week": 15,
            "monthly_est": 900.0,
            "schedule_fit": "Evenings and weekends",
            "why_it_fits": "Fast to start",
            "debt_impact": "Steady income",
            "first_step": "Apply locally",
            "startup_cost": "$0",
        },
    ]


@pytest.fixture
def accelerator_app():
    from backend.models.database import init_database

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "side-income-test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    init_database(app)
    app.register_blueprint(side_income_bp)
    return app


class TestSideIncomeAccelerator:
    def test_enrichment_and_sorting(self):
        accelerator = SideIncomeAccelerator(
            location_calculator=MagicMock(get_user_location=MagicMock(return_value=("78701", "Austin"))),
            job_generator=lambda _prompt: _sample_df1_jobs(),
        )

        with patch.object(accelerator, "extract_current_job", return_value="Engineer"), patch.object(
            accelerator, "extract_skills_from_profile", return_value="Python"
        ):
            result = accelerator.get_side_income_recommendations(
                user_id=1,
                monthly_gap=1000.0,
                hours_per_week_available=10,
                startup_cost_needed=6000.0,
                timeline_months=12,
            )

        assert len(result["matches"]) == 3
        assert result["recommendation"]["title"] == "Freelance Design"
        assert result["matches"][0]["icc_impact"]["gap_coverage_pct"] == 120.0
        assert result["matches"][0]["icc_impact"]["closes_monthly_gap"] is True
        assert result["matches"][0]["icc_impact"]["timeline_acceleration_months"] == 7.0
        combo = result["matches"][0]["interim_housing_combo"]
        assert combo["new_gap_with_roommate"] == 0.0
        assert combo["months_to_startup_with_roommate"] == 4.0
        assert result["context"]["relationship_exit_urgency"] == "medium"

    def test_interim_housing_combo_partial_gap(self):
        accelerator = SideIncomeAccelerator(job_generator=lambda _prompt: [_sample_df1_jobs()[0]])
        with patch.object(accelerator, "extract_current_job", return_value="Engineer"), patch.object(
            accelerator, "extract_skills_from_profile", return_value=None
        ), patch.object(
            accelerator.location_calculator,
            "get_user_location",
            return_value=(None, None),
        ):
            result = accelerator.get_side_income_recommendations(
                user_id=1,
                monthly_gap=1000.0,
                hours_per_week_available=5,
                startup_cost_needed=3000.0,
                timeline_months=6,
            )

        combo = result["matches"][0]["interim_housing_combo"]
        assert combo["new_gap_with_roommate"] == 100.0
        assert combo["months_to_startup_with_roommate"] == 3.33

    def test_rejects_non_positive_monthly_gap(self):
        accelerator = SideIncomeAccelerator(job_generator=lambda _prompt: _sample_df1_jobs())
        with pytest.raises(ValueError, match="monthly_gap"):
            accelerator.get_side_income_recommendations(
                user_id=1,
                monthly_gap=0,
                hours_per_week_available=10,
                startup_cost_needed=1000.0,
                timeline_months=6,
            )

    def test_df1_failure_raises(self):
        accelerator = SideIncomeAccelerator(job_generator=lambda _prompt: None)
        with patch.object(accelerator, "extract_current_job", return_value="Engineer"), patch.object(
            accelerator, "extract_skills_from_profile", return_value=None
        ), patch.object(
            accelerator.location_calculator,
            "get_user_location",
            return_value=(None, None),
        ), pytest.raises(RuntimeError, match="DF1"):
            accelerator.get_side_income_recommendations(
                user_id=1,
                monthly_gap=500.0,
                hours_per_week_available=20,
                startup_cost_needed=2000.0,
                timeline_months=4,
            )

    def test_extract_current_job_from_career_profile(self, accelerator_app):
        career = MagicMock(current_role="Product Manager")
        with accelerator_app.app_context(), patch(
            "backend.services.side_income_accelerator.CareerProfile.query"
        ) as career_query, patch(
            "backend.services.side_income_accelerator.User.query"
        ) as user_query:
            career_query.filter_by.return_value.first.return_value = career
            user_query.filter_by.return_value.first.return_value = None
            accelerator = SideIncomeAccelerator()
            assert accelerator.extract_current_job(1) == "Product Manager"

    def test_extract_skills_from_profile(self, accelerator_app):
        user = MagicMock(email="skills@test.com")
        profile = MagicMock(
            personal_info=json.dumps({"skills": ["Python", "SQL"]}),
        )
        career = MagicMock(industry="Technology", bls_career_field=None, occupation_key=None)
        with accelerator_app.app_context(), patch(
            "backend.services.side_income_accelerator.User.query"
        ) as user_query, patch(
            "backend.services.side_income_accelerator.UserProfile.query"
        ) as profile_query, patch(
            "backend.services.side_income_accelerator.CareerProfile.query"
        ) as career_query:
            user_query.filter_by.return_value.first.return_value = user
            profile_query.filter_by.return_value.first.return_value = profile
            career_query.filter_by.return_value.first.return_value = career
            accelerator = SideIncomeAccelerator()
            skills = accelerator.extract_skills_from_profile(1)
            assert skills is not None
            assert "Python" in skills
            assert "Technology" in skills


class TestSideIncomeApi:
    @patch("backend.routes.side_income_api.SideIncomeAccelerator")
    def test_endpoint_returns_enriched_payload(self, mock_cls, accelerator_app):
        mock_cls.return_value.get_side_income_recommendations.return_value = {
            "matches": [{"title": "Freelance Design"}],
            "recommendation": {"title": "Freelance Design"},
            "context": {"total_monthly_gap": 1000.0},
        }

        client = accelerator_app.test_client()
        with accelerator_app.app_context():
            g.current_user_id = 42
            with patch(
                "backend.routes.side_income_api.get_current_user_db_id",
                return_value=42,
            ):
                response = client.post(
                    "/api/independence-cost/side-income-recommendations",
                    json={
                        "monthly_gap": 1000,
                        "hours_per_week_available": 10,
                        "startup_cost_needed": 6000,
                        "timeline_months": 12,
                    },
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["recommendation"]["title"] == "Freelance Design"
        mock_cls.return_value.get_side_income_recommendations.assert_called_once_with(
            42,
            monthly_gap=1000.0,
            hours_per_week_available=10,
            startup_cost_needed=6000.0,
            timeline_months=12,
        )

    def test_endpoint_rejects_invalid_monthly_gap(self, accelerator_app):
        client = accelerator_app.test_client()
        with accelerator_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.side_income_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/independence-cost/side-income-recommendations",
                    json={
                        "monthly_gap": 0,
                        "hours_per_week_available": 10,
                        "startup_cost_needed": 6000,
                        "timeline_months": 12,
                    },
                )
        assert response.status_code == 400

    def test_endpoint_rejects_negative_monthly_gap(self, accelerator_app):
        client = accelerator_app.test_client()
        with accelerator_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.side_income_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/independence-cost/side-income-recommendations",
                    json={
                        "monthly_gap": -100,
                        "hours_per_week_available": 10,
                        "startup_cost_needed": 6000,
                        "timeline_months": 12,
                    },
                )
        assert response.status_code == 400

    @patch("backend.routes.side_income_api.SideIncomeAccelerator")
    def test_high_hours_passed_to_accelerator(self, mock_cls, accelerator_app):
        mock_cls.return_value.get_side_income_recommendations.return_value = {
            "matches": [],
            "recommendation": None,
            "context": {},
        }
        client = accelerator_app.test_client()
        with accelerator_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.side_income_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/independence-cost/side-income-recommendations",
                    json={
                        "monthly_gap": 1000,
                        "hours_per_week_available": 40,
                        "startup_cost_needed": 6000,
                        "timeline_months": 6,
                    },
                )
        assert response.status_code == 200
        mock_cls.return_value.get_side_income_recommendations.assert_called_once_with(
            1,
            monthly_gap=1000.0,
            hours_per_week_available=40,
            startup_cost_needed=6000.0,
            timeline_months=6,
        )

    def test_endpoint_requires_auth_when_not_testing(self, accelerator_app):
        accelerator_app.config["TESTING"] = False
        client = accelerator_app.test_client()
        response = client.post(
            "/api/independence-cost/side-income-recommendations",
            json={
                "monthly_gap": 1000,
                "hours_per_week_available": 10,
                "startup_cost_needed": 6000,
                "timeline_months": 12,
            },
        )
        assert response.status_code == 401
        accelerator_app.config["TESTING"] = True
