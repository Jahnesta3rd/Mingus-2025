"""Tests for expense audit analyzer and API."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.expense_audit_api import expense_audit_bp
from backend.routes.integration_api import integration_bp
from backend.services.expense_audit_service import ExpenseAuditAnalyzer


@pytest.fixture
def audit_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "expense-audit-test"
    app.register_blueprint(expense_audit_bp)
    app.register_blueprint(integration_bp)
    return app


class TestExpenseAuditAnalyzer:
    def test_categorize_and_aggregate(self):
        analyzer = ExpenseAuditAnalyzer()
        entries = [
            {"amount": 300, "category": "Dining", "merchant": "Starbucks"},
            {"amount": 200, "category": "Groceries", "merchant": "Kroger"},
            {"amount": 45, "category": "Subscriptions", "merchant": "Netflix"},
        ]
        monthly = analyzer._aggregate_by_category(entries, days_lookback=90)
        assert monthly["Dining"] == 100.0
        assert monthly["Groceries"] == pytest.approx(66.67, rel=0.01)

    def test_combined_savings_keys(self):
        combined = ExpenseAuditAnalyzer()._combined_savings()
        assert combined["A"] == 120.0
        assert combined["A+B"] == 370.0
        assert combined["A+B+C"] == 520.0

    def test_analyze_expenses_persists_snapshot(self, audit_app):
        analyzer = ExpenseAuditAnalyzer()
        today = date.today()
        txn = MagicMock(
            amount=-45.0,
            merchant="Netflix",
            category="Subscription",
            subcategory=None,
            date=today,
            is_debit=True,
            pending=False,
        )

        with audit_app.app_context(), patch.object(
            analyzer, "_fetch_transactions", return_value=[{"amount": 45, "category": "Subscriptions", "merchant": "Netflix", "source": "plaid"}]
        ), patch.object(analyzer, "_fetch_quick_spend", return_value=[]), patch.object(
            analyzer, "_fetch_recurring_subscriptions", return_value=[]
        ), patch(
            "backend.services.expense_audit_service.db.session"
        ) as session:
            result = analyzer.analyze_expenses(1, days_lookback=90)

        assert result["total_monthly"] >= 0
        assert "tier_recommendations" in result
        assert result["combined_savings"]["A+B"] == 370.0
        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_apply_tiers_to_icc_recalculates_gap(self, audit_app):
        analyzer = ExpenseAuditAnalyzer()
        assessment_id = uuid.uuid4()
        snapshot_id = uuid.uuid4()
        snapshot = MagicMock(
            id=snapshot_id,
            combined_savings={"A": 120, "B": 250, "C": 150, "A+B": 370, "A+B+C": 520},
            selected_tiers=None,
            total_savings_selected=None,
        )
        assessment = MagicMock(
            monthly_independence_gap=Decimal("765"),
            total_startup_cost=Decimal("12000"),
            months_to_save_startup=Decimal("15.69"),
        )

        with audit_app.app_context(), patch(
            "backend.services.expense_audit_service.ExpenseAuditSnapshot.query"
        ) as snap_query, patch(
            "backend.services.expense_audit_service.IndependenceCostAssessment.query"
        ) as icc_query, patch(
            "backend.services.expense_audit_service.db.session"
        ):
            snap_query.filter_by.return_value.first.return_value = snapshot
            icc_query.filter_by.return_value.first.return_value = assessment
            result = analyzer.apply_tiers_to_icc(
                user_id=1,
                icc_assessment_id=assessment_id,
                selected_tiers=["A", "B"],
                snapshot_id=snapshot_id,
            )

        assert result["success"] is True
        assert result["total_monthly_savings"] == 370.0
        assert result["new_gap_after_cuts"] == 395.0


class TestExpenseAuditApi:
    @patch("backend.routes.expense_audit_api.ExpenseAuditAnalyzer")
    def test_analyze_endpoint(self, mock_cls, audit_app):
        mock_cls.return_value.analyze_expenses.return_value = {
            "total_monthly": 2400,
            "spending_by_category": {"Dining": 400},
            "tier_recommendations": {},
            "combined_savings": {"A+B": 370},
        }
        client = audit_app.test_client()
        with audit_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.expense_audit_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/expense-audit/analyze",
                    json={"days_lookback": 90},
                )

        assert response.status_code == 200
        assert response.get_json()["combined_savings"]["A+B"] == 370

    @patch("backend.routes.integration_api.ExpenseAuditAnalyzer")
    def test_icc_integration_endpoint(self, mock_cls, audit_app):
        mock_cls.return_value.apply_tiers_to_icc.return_value = {
            "success": True,
            "total_monthly_savings": 370.0,
            "new_gap_after_cuts": 395.0,
        }
        client = audit_app.test_client()
        with audit_app.app_context():
            g.current_user_id = 1
            with patch(
                "backend.routes.integration_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/integration/expense-audit-to-icc-dashboard",
                    json={
                        "icc_assessment_id": str(uuid.uuid4()),
                        "selected_tiers": ["A", "B"],
                    },
                )

        assert response.status_code == 200
        assert response.get_json()["new_gap_after_cuts"] == 395.0
