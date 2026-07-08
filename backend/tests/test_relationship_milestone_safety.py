"""Safety-critical tests for relationship milestone emergency detection."""

from __future__ import annotations

import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.relationship_checkin_api import relationship_checkin_bp
from backend.services.relationship_milestone_service import (
    DV_RESOURCES,
    EMERGENCY_TRIGGER_TYPES,
    RelationshipMilestoneChecker,
)


@pytest.fixture
def checker():
    return RelationshipMilestoneChecker()


@pytest.fixture
def checkin_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "relationship-checkin-test"
    app.register_blueprint(relationship_checkin_bp)
    return app


class TestEmergencyTriggerDetection:
    @pytest.mark.parametrize(
        "signal",
        list(EMERGENCY_TRIGGER_TYPES),
    )
    def test_each_explicit_emergency_signal_is_detected(self, checker, signal):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "stable",
                "feels_safe": "yes",
                "emergency_signals": {signal: True},
            }
        )
        assert signal in flags

    def test_unsafe_feels_triggers_physical_and_abuse_flags(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "stable",
                "feels_safe": "unsafe",
                "needs_to_leave_sooner": False,
                "prefer_leave_now": False,
            }
        )
        assert "physical_threat" in flags
        assert "abuse_escalation" in flags
        assert "emotional_abuse" in flags

    def test_prefer_leave_now_triggers_imminent_danger(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "declining",
                "feels_safe": "mostly",
                "prefer_leave_now": True,
            }
        )
        assert "imminent_danger" in flags

    def test_needs_to_leave_sooner_with_unsafe_feels_triggers_escalation(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "declining",
                "feels_safe": "no",
                "needs_to_leave_sooner": True,
            }
        )
        assert "abuse_escalation" in flags
        assert "imminent_danger" in flags


class TestFalsePositivePrevention:
    def test_safe_improving_responses_do_not_trigger_emergency(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "improving",
                "feels_safe": "yes",
                "needs_to_leave_sooner": False,
                "prefer_leave_now": False,
                "on_track_savings": True,
            }
        )
        assert flags == []

    def test_on_track_status_for_safe_responses(self, checker):
        status = checker._determine_status(
            {
                "vibe_trend": "stable",
                "feels_safe": "yes",
                "needs_to_leave_sooner": False,
                "on_track_savings": True,
                "prefer_leave_now": False,
            },
            [],
        )
        assert status == "on_track"


class TestFalseNegativePrevention:
    """SAFETY CRITICAL: any credible danger signal must not be missed."""

    @pytest.mark.parametrize(
        "feels_safe",
        ["no", "unsafe", "never", "not_safe"],
    )
    def test_all_unsafe_feels_values_trigger_emergency_status(self, checker, feels_safe):
        flags = checker.detect_emergency_triggers(
            {"vibe_trend": "stable", "feels_safe": feels_safe}
        )
        status = checker._determine_status(
            {"vibe_trend": "stable", "feels_safe": feels_safe},
            flags,
        )
        assert len(flags) > 0
        assert status == "emergency"

    def test_physical_threat_signal_always_emergency(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "improving",
                "feels_safe": "yes",
                "emergency_signals": {"physical_threat": True},
            }
        )
        status = checker._determine_status(
            {"vibe_trend": "improving", "feels_safe": "yes"},
            flags,
        )
        assert status == "emergency"

    def test_substance_abuse_signal_triggers_emergency(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "vibe_trend": "stable",
                "feels_safe": "mostly",
                "emergency_signals": {"substance_abuse": True},
            }
        )
        assert "substance_abuse" in flags

    def test_financial_control_signal_triggers_emergency(self, checker):
        flags = checker.detect_emergency_triggers(
            {
                "emergency_signals": {"financial_control": True},
                "feels_safe": "yes",
                "vibe_trend": "stable",
            }
        )
        status = checker._determine_status(
            {"feels_safe": "yes", "vibe_trend": "stable"},
            flags,
        )
        assert "financial_control" in flags
        assert status == "emergency"


class TestDvResourceAvailability:
    def test_dv_hotline_always_available(self):
        hotline = next(r for r in DV_RESOURCES if "799-7233" in r["phone"])
        assert hotline["name"]
        assert hotline["url"]

    def test_safety_plan_resource_available(self):
        assert any(r["type"] == "safety_plan" for r in DV_RESOURCES)

    def test_shelter_finder_available(self):
        assert any(r["type"] == "shelter" for r in DV_RESOURCES)

    def test_counseling_resource_available(self):
        assert any(r["type"] == "counseling" for r in DV_RESOURCES)

    def test_assess_response_includes_resources(self, checkin_app):
        client = checkin_app.test_client()
        person_id = str(uuid.uuid4())
        with checkin_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.relationship_checkin_api.get_current_user_db_id",
                return_value=1,
            ), patch(
                "backend.routes.relationship_checkin_api.RelationshipMilestoneChecker"
            ) as mock_cls:
                mock_cls.return_value.monthly_readiness_check.return_value = {
                    "status": "on_track",
                    "emergency_alert": False,
                    "emergency_flags": [],
                    "next_steps": ["Stay on plan"],
                    "resources_if_needed": DV_RESOURCES,
                    "checkin_id": str(uuid.uuid4()),
                    "tier_recommendation": None,
                }
                response = client.post(
                    "/api/relationship-checkin/assess",
                    json={
                        "person_id": person_id,
                        "vibe_trend": "stable",
                        "feels_safe": "yes",
                        "needs_to_leave_sooner": False,
                        "on_track_savings": True,
                        "prefer_leave_now": False,
                    },
                )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["resources_if_needed"]) >= 5
        assert any("799-7233" in r.get("phone", "") for r in data["resources_if_needed"])


class TestMonthlyReadinessIntegration:
    def test_emergency_checkin_stored_with_tier_zero(self, checker, checkin_app):
        partner_id = uuid.uuid4()
        partner = MagicMock(nickname="Alex")

        with checkin_app.app_context(), patch(
            "backend.services.relationship_milestone_service.VibeTrackedPerson.query"
        ) as person_query, patch(
            "backend.services.relationship_milestone_service.db.session"
        ) as session:
            person_query.filter_by.return_value.first.return_value = partner
            result = checker.monthly_readiness_check(
                1,
                partner_id,
                {
                    "vibe_trend": "declining",
                    "feels_safe": "unsafe",
                    "needs_to_leave_sooner": True,
                    "on_track_savings": False,
                    "prefer_leave_now": True,
                },
            )

        assert result["status"] == "emergency"
        assert result["emergency_alert"] is True
        assert result["tier_recommendation"] == "tier_0_emergency_exit"
        assert len(result["emergency_flags"]) > 0
        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_improving_path_status(self, checker, checkin_app):
        partner_id = uuid.uuid4()
        partner = MagicMock(nickname="Alex")

        with checkin_app.app_context(), patch(
            "backend.services.relationship_milestone_service.VibeTrackedPerson.query"
        ) as person_query, patch(
            "backend.services.relationship_milestone_service.db.session"
        ):
            person_query.filter_by.return_value.first.return_value = partner
            result = checker.monthly_readiness_check(
                1,
                partner_id,
                {
                    "vibe_trend": "improving",
                    "feels_safe": "yes",
                    "needs_to_leave_sooner": False,
                    "on_track_savings": True,
                    "prefer_leave_now": False,
                },
            )

        assert result["status"] == "improving"
        assert result["emergency_alert"] is False
