"""Tests for ICC ↔ DF1 integration API."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.models.side_income_commitment import UserSideIncomeCommitment
from backend.routes.integration_api import integration_bp
from backend.services.side_income_integration_service import (
    IntegrationError,
    SideIncomeIntegrationService,
)


@pytest.fixture
def integration_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "integration-api-test"
    app.register_blueprint(integration_bp)
    return app


def _sample_assessment(
    *,
    user_id: int = 42,
    person_id: uuid.UUID | None = None,
    assessment_id: uuid.UUID | None = None,
) -> IndependenceCostAssessment:
    return IndependenceCostAssessment(
        id=assessment_id or uuid.uuid4(),
        user_id=user_id,
        person_id=person_id or uuid.uuid4(),
        estimated_housing=1800,
        estimated_utilities=150,
        estimated_food=450,
        estimated_transportation=120,
        estimated_phone_internet=90,
        estimated_other=175,
        total_monthly_solo=2785,
        total_startup_cost=Decimal("12000.00"),
        current_housing_contribution=Decimal("950.00"),
        monthly_independence_gap=Decimal("1835.00"),
        months_to_save_startup=Decimal("6.54"),
    )


class TestIccToDf1Handoff:
    @patch("backend.routes.integration_api.SideIncomeIntegrationService")
    def test_valid_request_returns_commitment(self, mock_cls, integration_app):
        commitment_id = str(uuid.uuid4())
        mock_cls.return_value.create_icc_to_df1_handoff.return_value = {
            "success": True,
            "commitment_id": commitment_id,
            "handoff_url": "/dashboard/tools?tab=debt&subTab=second-job",
            "message": "Great! You selected Freelance writing. Let's get you set up.",
        }
        client = integration_app.test_client()
        with integration_app.app_context():
            g.current_user_id = 42
            with patch(
                "backend.routes.integration_api.get_current_user_db_id",
                return_value=42,
            ):
                response = client.post(
                    "/api/integration/icc-to-df1-handoff",
                    json={
                        "icc_assessment_id": str(uuid.uuid4()),
                        "person_id": str(uuid.uuid4()),
                        "selected_job": "Freelance writing",
                        "df1_job_type": "freelance",
                        "target_monthly_income": 600,
                        "gap_coverage_pct": 78.4,
                    },
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["commitment_id"] == commitment_id
        assert "second-job" in data["handoff_url"]

    def test_service_creates_commitment_record(self, integration_app):
        assessment_id = uuid.uuid4()
        person_id = uuid.uuid4()
        assessment = _sample_assessment(
            user_id=7,
            person_id=person_id,
            assessment_id=assessment_id,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query, patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query, patch(
            "backend.services.side_income_integration_service.db.session"
        ) as session:
            assessment_query.filter_by.return_value.first.return_value = assessment
            commitment_query.filter_by.return_value.first.return_value = None
            result = service.create_icc_to_df1_handoff(
                user_id=7,
                icc_assessment_id=assessment_id,
                person_id=person_id,
                selected_job="Freelance writing",
                df1_job_type="freelance",
                target_monthly_income=600.0,
                gap_coverage_pct=78.4,
            )

        assert result["success"] is True
        session.add.assert_called_once()
        session.commit.assert_called_once()
        created = session.add.call_args[0][0]
        assert created.status == "selected"
        assert created.selected_job == "Freelance writing"
        assert float(created.target_monthly_income) == 600.0

    def test_service_rejects_wrong_user(self, integration_app):
        assessment_id = uuid.uuid4()
        person_id = uuid.uuid4()
        assessment = _sample_assessment(user_id=7, person_id=person_id, assessment_id=assessment_id)
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query:
            assessment_query.filter_by.return_value.first.return_value = assessment
            with pytest.raises(IntegrationError) as exc:
                service.create_icc_to_df1_handoff(
                    user_id=99,
                    icc_assessment_id=assessment_id,
                    person_id=person_id,
                    selected_job="Retail Shift",
                    df1_job_type="part_time",
                    target_monthly_income=900,
                    gap_coverage_pct=90,
                )
        assert exc.value.status_code == 403

    def test_service_rejects_person_mismatch(self, integration_app):
        assessment_id = uuid.uuid4()
        assessment = _sample_assessment(
            user_id=7,
            person_id=uuid.uuid4(),
            assessment_id=assessment_id,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query:
            assessment_query.filter_by.return_value.first.return_value = assessment
            with pytest.raises(IntegrationError) as exc:
                service.create_icc_to_df1_handoff(
                    user_id=7,
                    icc_assessment_id=assessment_id,
                    person_id=uuid.uuid4(),
                    selected_job="Retail Shift",
                    df1_job_type="part_time",
                    target_monthly_income=900,
                    gap_coverage_pct=90,
                )
        assert exc.value.status_code == 400

    def test_service_returns_409_for_duplicate(self, integration_app):
        assessment_id = uuid.uuid4()
        person_id = uuid.uuid4()
        assessment = _sample_assessment(
            user_id=7,
            person_id=person_id,
            assessment_id=assessment_id,
        )
        existing = UserSideIncomeCommitment(
            id=uuid.uuid4(),
            user_id=7,
            icc_assessment_id=assessment_id,
            selected_job="Existing",
            target_monthly_income=500,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query, patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query:
            assessment_query.filter_by.return_value.first.return_value = assessment
            commitment_query.filter_by.return_value.first.return_value = existing
            with pytest.raises(IntegrationError) as exc:
                service.create_icc_to_df1_handoff(
                    user_id=7,
                    icc_assessment_id=assessment_id,
                    person_id=person_id,
                    selected_job="Retail Shift",
                    df1_job_type="part_time",
                    target_monthly_income=900,
                    gap_coverage_pct=90,
                )
        assert exc.value.status_code == 409


class TestDf1ToIccMilestone:
    def test_first_income_updates_commitment_and_timeline(self, integration_app):
        commitment_id = uuid.uuid4()
        assessment_id = uuid.uuid4()
        assessment = _sample_assessment(assessment_id=assessment_id)
        commitment = UserSideIncomeCommitment(
            id=commitment_id,
            user_id=7,
            icc_assessment_id=assessment_id,
            selected_job="Freelance writing",
            target_monthly_income=600,
            status="selected",
            independence_timeline_original_months=7,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query, patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query, patch(
            "backend.services.side_income_integration_service.db.session"
        ) as session:
            commitment_query.filter_by.return_value.first.return_value = commitment
            assessment_query.filter_by.return_value.first.return_value = assessment
            result = service.record_df1_milestone(
                commitment_id=commitment_id,
                milestone_type="first_income",
                income_amount=300.0,
                income_date=datetime(2026, 7, 8, 12, 0, 0),
            )

        assert result["success"] is True
        assert result["status"] == "income_earned"
        assert result["actual_monthly_income"] == 300.0
        assert result["independence_timeline_original_months"] == 7
        assert result["independence_timeline_with_income_months"] == 8
        assert result["timeline_acceleration_months"] == 0
        assert commitment.df1_first_income_date is not None
        session.commit.assert_called_once()

    def test_monthly_update_recalculates_timeline(self, integration_app):
        commitment_id = uuid.uuid4()
        assessment_id = uuid.uuid4()
        assessment = _sample_assessment(assessment_id=assessment_id)
        commitment = UserSideIncomeCommitment(
            id=commitment_id,
            user_id=7,
            icc_assessment_id=assessment_id,
            selected_job="Freelance writing",
            target_monthly_income=600,
            status="income_earned",
            independence_timeline_original_months=7,
            independence_timeline_with_income_months=9,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query, patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query, patch(
            "backend.services.side_income_integration_service.db.session"
        ):
            commitment_query.filter_by.return_value.first.return_value = commitment
            assessment_query.filter_by.return_value.first.return_value = assessment
            result = service.record_df1_milestone(
                commitment_id=commitment_id,
                milestone_type="monthly_update",
                income_amount=600.0,
            )

        assert result["actual_monthly_income"] == 600.0
        assert result["independence_timeline_with_income_months"] == 10
        assert result["timeline_acceleration_months"] == 0

    def test_income_covers_gap_sets_zero_timeline(self, integration_app):
        commitment_id = uuid.uuid4()
        assessment_id = uuid.uuid4()
        assessment = _sample_assessment(assessment_id=assessment_id)
        commitment = UserSideIncomeCommitment(
            id=commitment_id,
            user_id=7,
            icc_assessment_id=assessment_id,
            selected_job="Freelance writing",
            target_monthly_income=600,
            status="selected",
            independence_timeline_original_months=7,
        )
        service = SideIncomeIntegrationService()

        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query, patch(
            "backend.services.side_income_integration_service.IndependenceCostAssessment.query"
        ) as assessment_query, patch(
            "backend.services.side_income_integration_service.db.session"
        ):
            commitment_query.filter_by.return_value.first.return_value = commitment
            assessment_query.filter_by.return_value.first.return_value = assessment
            result = service.record_df1_milestone(
                commitment_id=commitment_id,
                milestone_type="first_income",
                income_amount=2000.0,
            )

        assert result["independence_timeline_with_income_months"] == 0

    def test_missing_commitment_returns_404(self, integration_app):
        service = SideIncomeIntegrationService()
        with integration_app.app_context(), patch(
            "backend.services.side_income_integration_service.UserSideIncomeCommitment.query"
        ) as commitment_query:
            commitment_query.filter_by.return_value.first.return_value = None
            with pytest.raises(IntegrationError) as exc:
                service.record_df1_milestone(
                    commitment_id=uuid.uuid4(),
                    milestone_type="first_income",
                    income_amount=300,
                )
        assert exc.value.status_code == 404

    def test_endpoint_returns_milestone_payload(self, integration_app):
        client = integration_app.test_client()
        commitment_id = str(uuid.uuid4())
        with integration_app.app_context(), patch(
            "backend.routes.integration_api.SideIncomeIntegrationService"
        ) as mock_cls:
            mock_cls.return_value.record_df1_milestone.return_value = {
                "success": True,
                "commitment_id": commitment_id,
                "status": "income_earned",
                "actual_monthly_income": 600.0,
                "independence_timeline_original_months": 21,
                "independence_timeline_with_income_months": 14,
                "timeline_acceleration_months": 7,
                "message": "Congrats!",
            }
            response = client.post(
                "/api/integration/df1-to-icc-milestone",
                json={
                    "commitment_id": commitment_id,
                    "milestone_type": "first_income",
                    "income_amount": 600,
                },
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["timeline_acceleration_months"] == 7
