"""Integration tests for assessment funnel analytics, tokens, and recommendations."""

from __future__ import annotations

import hashlib
import json

import pytest

from backend.models.assessment_event import AssessmentEvent
from backend.models.assessment_token import AssessmentToken


@pytest.fixture
def funnel_assessment(client, auth_headers, monkeypatch):
    """Submit an assessment and return ids for funnel tests."""
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("FLASK_ENV", "testing")

    payload = {
        "email": "funnel-test@example.com",
        "firstName": "Funnel",
        "assessmentType": "ai-risk",
        "answers": {
            "jobTitle": "Engineer",
            "industry": "Technology/Software",
            "automationLevel": "Moderate",
            "aiTools": "Sometimes",
            "skills": ["Coding/Programming"],
        },
    }
    response = client.post(
        "/api/assessments",
        data=json.dumps(payload),
        headers=auth_headers,
        content_type="application/json",
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    data = json.loads(response.data)
    assessment_id = data["assessment_id"]

    with client.application.app_context():
        token_obj = (
            AssessmentToken.query.filter_by(assessment_id=assessment_id)
            .order_by(AssessmentToken.created_at.desc())
            .first()
        )
        assert token_obj is not None
        yield {
            "assessment_id": assessment_id,
            "token": token_obj.token,
            "email": payload["email"],
            "email_hash": hashlib.sha256(payload["email"].encode()).hexdigest(),
        }


class TestAssessmentFunnel:
    def test_submit_logs_submitted_event(self, client, funnel_assessment):
        with client.application.app_context():
            event = AssessmentEvent.query.filter_by(
                assessment_id=funnel_assessment["assessment_id"],
                event_type="submitted",
            ).first()
            assert event is not None
            assert event.email_hash == funnel_assessment["email_hash"]

    def test_public_results_includes_recommendations(self, client, funnel_assessment):
        aid = funnel_assessment["assessment_id"]
        token = funnel_assessment["token"]
        response = client.get(f"/api/assessments/{aid}/public-results?token={token}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "score" in data
        assert data.get("next_steps")
        assert data.get("tier_title")
        assert data.get("actions")

    def test_public_results_does_not_mark_token_used(self, client, funnel_assessment):
        aid = funnel_assessment["assessment_id"]
        token = funnel_assessment["token"]
        client.get(f"/api/assessments/{aid}/public-results?token={token}")
        with client.application.app_context():
            token_obj = AssessmentToken.query.filter_by(token=token).first()
            assert token_obj is not None
            assert token_obj.is_used is False

    def test_analytics_results_viewed(self, client, funnel_assessment):
        aid = funnel_assessment["assessment_id"]
        token = funnel_assessment["token"]
        response = client.post(
            "/api/analytics/assessment-event",
            data=json.dumps(
                {
                    "assessment_id": aid,
                    "token": token,
                    "event_type": "results_viewed",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        with client.application.app_context():
            event = AssessmentEvent.query.filter_by(
                assessment_id=aid,
                event_type="results_viewed",
            ).first()
            assert event is not None

    def test_track_click_redirects_and_logs(self, client, funnel_assessment):
        aid = funnel_assessment["assessment_id"]
        token = funnel_assessment["token"]
        response = client.get(
            f"/api/assessments/{aid}/track-click?token={token}",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert token in response.location
        with client.application.app_context():
            event = AssessmentEvent.query.filter_by(
                assessment_id=aid,
                event_type="link_clicked",
            ).first()
            assert event is not None

    def test_resend_token(self, client, funnel_assessment, monkeypatch):
        monkeypatch.setenv("TESTING", "1")
        aid = funnel_assessment["assessment_id"]
        response = client.post(
            f"/api/assessments/{aid}/resend-token",
            data=json.dumps({"email": funnel_assessment["email"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        with client.application.app_context():
            event = AssessmentEvent.query.filter_by(
                assessment_id=aid,
                event_type="token_resent",
            ).first()
            assert event is not None
