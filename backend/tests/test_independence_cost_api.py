"""Tests for Independence Cost Calculator API and trigger detector."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.routes.independence_cost_api import (
    IndependenceCostTriggerDetector,
    independence_cost_bp,
)


@pytest.fixture
def icc_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "icc-api-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    init_database(app)
    app.register_blueprint(independence_cost_bp)
    return app


@pytest.fixture
def icc_client(icc_app):
    return icc_app.test_client()


@pytest.fixture
def auth_headers():
    return {"Content-Type": "application/json"}


def _make_partner(
    *,
    partner_id: uuid.UUID | None = None,
    user_id: int = 1,
    relationship_type: str = "partner",
    estimated_monthly_cost: float | None = 950.0,
    nickname: str = "Alex",
) -> VibeTrackedPerson:
    return VibeTrackedPerson(
        id=partner_id or uuid.uuid4(),
        user_id=user_id,
        nickname=nickname,
        relationship_type=relationship_type,
        estimated_monthly_cost=estimated_monthly_cost,
    )


def _make_assessments(partner_id: uuid.UUID, scores: list[int]) -> list[VibePersonAssessment]:
    now = datetime.utcnow()
    return [
        VibePersonAssessment(
            tracked_person_id=partner_id,
            emotional_score=score,
            financial_score=3,
            verdict_label="test",
            annual_projection=12000,
            answers_snapshot={},
            completed_at=now - timedelta(weeks=len(scores) - 1 - idx),
        )
        for idx, score in enumerate(scores)
    ]


class TestIndependenceCostTriggerDetector:
    def test_should_show_false_when_no_partner(self, icc_app):
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibeTrackedPerson.query"
        ) as query:
            query.filter.return_value.order_by.return_value.all.return_value = []
            detector = IndependenceCostTriggerDetector()
            should_show, person_id = detector.should_show_independence_calculator(1)
        assert should_show is False
        assert person_id is None

    def test_should_show_false_when_partner_not_cohabiting(self, icc_app):
        partner = _make_partner(estimated_monthly_cost=500.0)
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibeTrackedPerson.query"
        ) as query:
            query.filter.return_value.order_by.return_value.all.return_value = [partner]
            detector = IndependenceCostTriggerDetector()
            with patch.object(detector, "is_cohabiting", return_value=False):
                should_show, person_id = detector.should_show_independence_calculator(1)
        assert should_show is False
        assert person_id is None

    def test_should_show_false_when_vibe_trend_not_declining(self, icc_app):
        partner = _make_partner()
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibeTrackedPerson.query"
        ) as query:
            query.filter.return_value.order_by.return_value.all.return_value = [partner]
            detector = IndependenceCostTriggerDetector()
            with patch.object(detector, "is_cohabiting", return_value=True), patch.object(
                detector, "is_declining_12_weeks", return_value=(False, [5, 4, 3, 2, 3])
            ):
                should_show, person_id = detector.should_show_independence_calculator(1)
        assert should_show is False
        assert person_id is None

    def test_should_show_true_when_both_cohabiting_and_declining(self, icc_app):
        partner = _make_partner(relationship_type="spouse", estimated_monthly_cost=1200.0)
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibeTrackedPerson.query"
        ) as query:
            query.filter.return_value.order_by.return_value.all.return_value = [partner]
            detector = IndependenceCostTriggerDetector()
            with patch.object(detector, "is_cohabiting", return_value=True), patch.object(
                detector, "is_declining_12_weeks", return_value=(True, [8, 7, 6, 5, 4, 3, 2, 2, 2, 2])
            ):
                should_show, person_id = detector.should_show_independence_calculator(1)
        assert should_show is True
        assert person_id == partner.id

    def test_is_cohabiting_threshold(self, icc_app):
        partner_id = uuid.uuid4()
        partner = _make_partner(partner_id=partner_id, estimated_monthly_cost=850.0)
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibeTrackedPerson.query"
        ) as query:
            query.filter_by.return_value.first.return_value = partner
            assert IndependenceCostTriggerDetector().is_cohabiting(partner_id) is True
            partner.estimated_monthly_cost = 799.0
            assert IndependenceCostTriggerDetector().is_cohabiting(partner_id) is False

    def test_is_declining_false_when_fewer_than_10_assessments(self, icc_app):
        partner_id = uuid.uuid4()
        assessments = _make_assessments(partner_id, [5, 4, 3, 2, 1])
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibePersonAssessment.query"
        ) as query:
            query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, scores = IndependenceCostTriggerDetector().is_declining_12_weeks(
                partner_id
            )
        assert is_declining is False
        assert len(scores) == 5

    def test_is_declining_false_when_trend_has_uptick(self, icc_app):
        partner_id = uuid.uuid4()
        assessments = _make_assessments(partner_id, [6, 5, 4, 3, 2, 3, 2, 2, 2, 2])
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibePersonAssessment.query"
        ) as query:
            query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, _scores = IndependenceCostTriggerDetector().is_declining_12_weeks(
                partner_id
            )
        assert is_declining is False

    def test_is_declining_false_when_ends_above_2(self, icc_app):
        partner_id = uuid.uuid4()
        assessments = _make_assessments(partner_id, [8, 7, 6, 5, 4, 4, 4, 4, 4, 4, 4, 4])
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibePersonAssessment.query"
        ) as query:
            query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, _scores = IndependenceCostTriggerDetector().is_declining_12_weeks(
                partner_id
            )
        assert is_declining is False

    def test_is_declining_true_for_valid_declining_pattern(self, icc_app):
        partner_id = uuid.uuid4()
        assessments = _make_assessments(
            partner_id, [8, 7, 6, 5, 4, 3, 3, 2, 2, 2, 2, 1]
        )
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api.VibePersonAssessment.query"
        ) as query:
            query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, scores = IndependenceCostTriggerDetector().is_declining_12_weeks(
                partner_id
            )
        assert is_declining is True
        assert len(scores) == 12
        assert scores[-1] <= 2


class TestIndependenceCostApiEndpoints:
    @patch("backend.routes.independence_cost_api.IndependenceCostCalculator")
    @patch("backend.routes.independence_cost_api.IndependenceCostTriggerDetector")
    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_should_recommend_returns_correct_structure(
        self,
        mock_resolve_user,
        mock_detector_cls,
        mock_calculator_cls,
        icc_app,
        icc_client,
        auth_headers,
    ):
        partner_id = uuid.uuid4()
        user = User(id=1, user_id=str(uuid.uuid4()), email="icc@test.com")
        partner = _make_partner(partner_id=partner_id, user_id=1)
        mock_resolve_user.return_value = user
        mock_detector_cls.return_value.should_show_independence_calculator.return_value = (
            True,
            partner_id,
        )
        mock_calculator_cls.return_value.calculate_full_assessment.return_value = {
            "monthly_costs": {"total_monthly": 2800.0},
            "gap": {"monthly_independence_gap": 900.0, "startup_cost": 12000.0},
            "current_situation": {"current_housing_contribution": 1900.0},
            "location": {"city_name": "Austin"},
        }

        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api._get_partner_for_user",
            return_value=partner,
        ), patch(
            "backend.routes.independence_cost_api._user_dismissed_flag",
            return_value=False,
        ):
            g.current_user_id = user.user_id
            response = icc_client.get(
                "/api/independence-cost/should-recommend",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["should_recommend"] is True
        assert data["partner_id"] == str(partner_id)
        assert data["partner_name"] == "Alex"
        assert data["city"] == "Austin"
        assert data["monthly_cost"] == 2800.0
        assert data["cta"] == "Explore RFR Module"

    @patch("backend.routes.independence_cost_api.IndependenceCostCalculator")
    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_assess_returns_full_assessment(
        self,
        mock_resolve_user,
        mock_calculator_cls,
        icc_app,
        icc_client,
        auth_headers,
    ):
        partner_id = uuid.uuid4()
        user = User(id=1, user_id=str(uuid.uuid4()), email="icc@test.com")
        mock_resolve_user.return_value = user
        mock_calculator_cls.return_value.calculate_full_assessment.return_value = {
            "monthly_costs": {"total_monthly": 2500.0},
            "startup_costs": {"total_without_car": 10000.0},
            "current_situation": {"current_housing_contribution": 900.0},
            "gap": {"monthly_independence_gap": 1600.0},
            "timeline": {"months_to_save_startup": 6.25},
            "vibe_data": {"is_declining_12_weeks": True, "emotional_scores": [5, 4, 3, 2]},
        }

        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api._get_partner_for_user",
            return_value=_make_partner(partner_id=partner_id, user_id=1),
        ):
            g.current_user_id = user.user_id
            response = icc_client.get(
                f"/api/independence-cost/assess?person_id={partner_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["monthly_costs"]["total_monthly"] == 2500.0
        assert data["gap"] == 1600.0
        assert data["timeline_months"] == 6.25
        assert data["vibe_data"]["is_declining_12_weeks"] is True

    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_assess_returns_404_for_missing_partner(
        self,
        mock_resolve_user,
        icc_app,
        icc_client,
        auth_headers,
    ):
        user = User(id=1, user_id=str(uuid.uuid4()), email="icc@test.com")
        mock_resolve_user.return_value = user
        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api._get_partner_for_user",
            return_value=None,
        ):
            g.current_user_id = user.user_id
            response = icc_client.get(
                f"/api/independence-cost/assess?person_id={uuid.uuid4()}",
                headers=auth_headers,
            )
        assert response.status_code == 404

    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_dismiss_sets_flag_and_returns_success(
        self,
        mock_resolve_user,
        icc_app,
        icc_client,
        auth_headers,
    ):
        user = User(id=1, user_id=str(uuid.uuid4()), email="icc@test.com")
        user.has_independence_calculator_dismissed = False
        mock_resolve_user.return_value = user

        with icc_app.app_context():
            g.current_user_id = user.user_id
            with patch.object(db.session, "commit") as commit_mock:
                response = icc_client.post(
                    "/api/independence-cost/dismiss",
                    headers=auth_headers,
                    data=json.dumps({}),
                )
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert user.has_independence_calculator_dismissed is True
        commit_mock.assert_called_once()

    @patch("backend.routes.independence_cost_api.IndependenceCostTriggerDetector")
    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_status_returns_correct_values(
        self,
        mock_resolve_user,
        mock_detector_cls,
        icc_app,
        icc_client,
        auth_headers,
    ):
        partner_id = uuid.uuid4()
        user = User(id=1, user_id=str(uuid.uuid4()), email="icc@test.com")
        mock_resolve_user.return_value = user
        mock_detector_cls.return_value.should_show_independence_calculator.return_value = (
            True,
            partner_id,
        )

        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api._user_dismissed_flag",
            return_value=False,
        ), patch(
            "backend.routes.independence_cost_api._has_assessment_today",
            return_value=False,
        ):
            g.current_user_id = user.user_id
            response = icc_client.get(
                "/api/independence-cost/status",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["dismissed"] is False
        assert data["can_calculate"] is True
        assert data["has_assessment_today"] is False
        assert data["partner_id"] == str(partner_id)

    def test_endpoints_require_auth_when_not_testing(self, icc_app, icc_client):
        icc_app.config["TESTING"] = False
        endpoints = [
            ("GET", "/api/independence-cost/should-recommend"),
            ("GET", f"/api/independence-cost/assess?person_id={uuid.uuid4()}"),
            ("POST", "/api/independence-cost/dismiss"),
            ("GET", "/api/independence-cost/status"),
        ]
        for method, path in endpoints:
            if method == "GET":
                response = icc_client.get(path)
            else:
                response = icc_client.post(path, json={})
            assert response.status_code == 401, f"{method} {path} should return 401"
        icc_app.config["TESTING"] = True

    @patch("backend.routes.independence_cost_api.IndependenceCostTriggerDetector")
    @patch("backend.routes.independence_cost_api._resolve_db_user")
    def test_endpoints_handle_user_id_from_current_user_context(
        self,
        mock_resolve_user,
        mock_detector_cls,
        icc_app,
        icc_client,
        auth_headers,
    ):
        user = User(id=42, user_id=str(uuid.uuid4()), email="icc@test.com")
        mock_resolve_user.return_value = user
        mock_detector_cls.return_value.should_show_independence_calculator.return_value = (
            False,
            None,
        )

        with icc_app.app_context(), patch(
            "backend.routes.independence_cost_api._user_dismissed_flag",
            return_value=False,
        ), patch(
            "backend.routes.independence_cost_api._has_assessment_today",
            return_value=False,
        ):
            g.current_user_id = user.user_id
            response = icc_client.get(
                "/api/independence-cost/status",
                headers=auth_headers,
            )

        assert response.status_code == 200
        mock_detector_cls.return_value.should_show_independence_calculator.assert_called_once_with(
            42
        )
