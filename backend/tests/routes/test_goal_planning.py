"""Tests for goal planning API route."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from flask import Flask

from backend.routes.goal_planning import goal_planning_bp


@pytest.fixture
def goal_planning_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(goal_planning_bp)
    return app


@pytest.fixture
def goal_planning_client(goal_planning_app):
    return goal_planning_app.test_client()


@pytest.fixture
def sample_payload():
    return {
        "goal": {
            "type": "home_purchase",
            "parameters": {"homePrice": 400000},
            "timeline": 5,
        },
        "userProfile": {
            "id": "user-1",
            "income": 8000,
            "savings": 25000,
            "expenses": 5200,
            "skills": ["JavaScript"],
            "availableHours": 10,
        },
    }


@pytest.fixture
def sample_result():
    return {
        "goalAnalysis": {"goalType": "home_purchase", "gaps": {"monthlyToSave": 1200}},
        "recommendations": {
            "paths": [{"pathId": "combined", "title": "Combined"}],
            "selectedPath": "combined",
            "source": "fallback",
            "generatedAt": "2026-07-07T00:00:00.000Z",
        },
        "jobSuggestions": {"global": {"jobs": []}, "byPathId": {}},
        "gigSuggestions": {"global": {"gigs": []}, "byPathId": {}},
        "expenseSuggestions": {"global": {"suggestions": []}, "byPathId": {}},
        "partialErrors": [],
    }


@patch("backend.routes.goal_planning.run_goal_planning_analyze")
def test_analyze_goal_planning_success(mock_run, goal_planning_client, sample_payload, sample_result):
    mock_run.return_value = sample_result

    response = goal_planning_client.post(
        "/api/goal-planning/analyze",
        data=json.dumps(sample_payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["goalAnalysis"]["goalType"] == "home_purchase"
    assert data["recommendations"]["selectedPath"] == "combined"
    mock_run.assert_called_once_with(sample_payload["goal"], sample_payload["userProfile"])


@patch("backend.routes.goal_planning.run_goal_planning_analyze")
def test_analyze_goal_planning_service_error(mock_run, goal_planning_client, sample_payload):
    from backend.services.goal_planning_service import GoalPlanningServiceError

    mock_run.side_effect = GoalPlanningServiceError("goal.type is required")

    response = goal_planning_client.post(
        "/api/goal-planning/analyze",
        data=json.dumps({"goal": {}, "userProfile": sample_payload["userProfile"]}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "analysis_failed"
