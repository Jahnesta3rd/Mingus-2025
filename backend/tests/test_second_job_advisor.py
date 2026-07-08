"""Tests for second job advisor earnings → ICC milestone integration."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.side_income_commitment import UserSideIncomeCommitment
from backend.routes.second_job_advisor import (
    notify_icc_first_income,
    second_job_advisor_bp,
)


@pytest.fixture
def second_job_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "second-job-test"
    app.register_blueprint(second_job_advisor_bp)
    return app


class TestNotifyIccFirstIncome:
    def test_triggers_icc_milestone_for_active_commitment(self, second_job_app):
        commitment_id = uuid.uuid4()
        commitment = UserSideIncomeCommitment(
            id=commitment_id,
            user_id=42,
            selected_job="Freelance writing",
            target_monthly_income=Decimal("600.00"),
            status="selected",
            independence_timeline_original_months=21,
        )
        milestone_result = {
            "success": True,
            "commitment_id": str(commitment_id),
            "status": "income_earned",
            "actual_monthly_income": 300.0,
            "independence_timeline_original_months": 21,
            "independence_timeline_with_income_months": 19,
            "timeline_acceleration_months": 2,
            "message": "Congrats!",
        }

        with second_job_app.app_context(), patch(
            "backend.routes.second_job_advisor.UserSideIncomeCommitment.query"
        ) as query, patch(
            "backend.routes.second_job_advisor.SideIncomeIntegrationService"
        ) as service_cls:
            query.filter.return_value.order_by.return_value.first.return_value = commitment
            service_cls.return_value.record_df1_milestone.return_value = milestone_result
            result = notify_icc_first_income(
                42,
                300.0,
                earned_date=datetime(2026, 7, 8, 12, 0, 0),
            )

        assert result == milestone_result
        service_cls.return_value.record_df1_milestone.assert_called_once_with(
            commitment_id=commitment_id,
            milestone_type="first_income",
            income_amount=300.0,
            income_date=datetime(2026, 7, 8, 12, 0, 0),
            user_id=42,
        )

    def test_skips_when_no_active_commitment(self, second_job_app):
        with second_job_app.app_context(), patch(
            "backend.routes.second_job_advisor.UserSideIncomeCommitment.query"
        ) as query, patch(
            "backend.routes.second_job_advisor.SideIncomeIntegrationService"
        ) as service_cls:
            query.filter.return_value.order_by.return_value.first.return_value = None
            result = notify_icc_first_income(42, 300.0)

        assert result is None
        service_cls.return_value.record_df1_milestone.assert_not_called()

    def test_does_not_raise_when_integration_fails(self, second_job_app):
        commitment = UserSideIncomeCommitment(
            id=uuid.uuid4(),
            user_id=42,
            selected_job="Freelance writing",
            target_monthly_income=Decimal("600.00"),
            status="selected",
        )

        with second_job_app.app_context(), patch(
            "backend.routes.second_job_advisor.UserSideIncomeCommitment.query"
        ) as query, patch(
            "backend.routes.second_job_advisor.SideIncomeIntegrationService"
        ) as service_cls:
            query.filter.return_value.order_by.return_value.first.return_value = commitment
            service_cls.return_value.record_df1_milestone.side_effect = RuntimeError("icc down")
            result = notify_icc_first_income(42, 300.0)

        assert result is None


class TestRecordEarningsEndpoint:
    def test_record_earnings_updates_icc_commitment(self, second_job_app):
        client = second_job_app.test_client()
        commitment_id = str(uuid.uuid4())
        with second_job_app.app_context():
            g.current_user_id = 42
            with patch(
                "backend.routes.second_job_advisor.get_current_user_db_id",
                return_value=42,
            ), patch(
                "backend.routes.second_job_advisor.notify_icc_first_income",
                return_value={
                    "success": True,
                    "commitment_id": commitment_id,
                    "status": "income_earned",
                    "actual_monthly_income": 300.0,
                    "independence_timeline_original_months": 21,
                    "independence_timeline_with_income_months": 19,
                    "timeline_acceleration_months": 2,
                    "message": "Congrats!",
                },
            ) as notify_mock:
                response = client.post(
                    "/api/second-job/record-earnings",
                    json={"amount": 300.0, "job_id": "test-job-123"},
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["amount"] == 300.0
        assert data["icc_milestone_recorded"] is True
        assert data["icc"]["status"] == "income_earned"
        assert data["icc"]["actual_monthly_income"] == 300.0
        notify_mock.assert_called_once()
        assert notify_mock.call_args[0][0] == 42
        assert notify_mock.call_args[0][1] == 300.0

    def test_record_earnings_requires_amount(self, second_job_app):
        client = second_job_app.test_client()
        with second_job_app.app_context():
            g.current_user_id = 42
            with patch(
                "backend.routes.second_job_advisor.get_current_user_db_id",
                return_value=42,
            ):
                response = client.post("/api/second-job/record-earnings", json={})

        assert response.status_code == 400

    def test_record_earnings_succeeds_without_icc_commitment(self, second_job_app):
        client = second_job_app.test_client()
        with second_job_app.app_context():
            g.current_user_id = 42
            with patch(
                "backend.routes.second_job_advisor.get_current_user_db_id",
                return_value=42,
            ), patch(
                "backend.routes.second_job_advisor.notify_icc_first_income",
                return_value=None,
            ):
                response = client.post(
                    "/api/second-job/record-earnings",
                    json={"amount": 150.0},
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["icc_milestone_recorded"] is False
        assert data["icc"] is None
