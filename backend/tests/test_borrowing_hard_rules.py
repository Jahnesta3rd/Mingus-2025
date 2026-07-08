"""Hard-rule safety tests for borrowing scenarios."""

from __future__ import annotations

import os
import sys

import pytest
from flask import Flask, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.routes.borrowing_api import borrowing_bp
from backend.services.borrowing_scenarios_service import BorrowingScenarios


@pytest.fixture
def borrowing_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "borrowing-test"
    app.register_blueprint(borrowing_bp)
    return app


@pytest.fixture
def service():
    return BorrowingScenarios()


class TestHardRulesEnforcement:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "no_accelerate_timeline",
            "safety_over_debt",
            "no_unstable_income",
            "bridge_only",
            "no_friend_loans",
            "never_payday",
            "never_401k",
        ],
    )
    def test_hard_rules_meta_coverage(self, service, rule_id):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 500)
        messages = " ".join(payload["hard_rules"]).lower()
        if rule_id == "never_payday":
            assert "payday" in messages
        elif rule_id == "never_401k":
            assert "401" in messages
        elif rule_id == "no_friend_loans":
            assert "friends" in messages
        elif rule_id == "no_accelerate_timeline":
            assert "accelerate" in messages
        elif rule_id == "no_unstable_income":
            assert "unstable" in messages
        elif rule_id == "bridge_only":
            assert "bridge" in messages or "$2" in messages
        elif rule_id == "safety_over_debt":
            assert "unsafe" in messages or "safety" in messages

    def test_payday_loans_never_suggested(self, service):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 500)
        option_keys = {row["key"] for row in payload["options"]}
        assert "payday_loan" not in option_keys
        assert "payday" not in option_keys
        forbidden = {row["key"] for row in payload["forbidden_products"]}
        assert "payday_loan" in forbidden

    def test_401k_never_suggested(self, service):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 500)
        forbidden = {row["key"] for row in payload["forbidden_products"]}
        assert "401k_withdrawal" in forbidden

    def test_friend_loan_blocked(self, service):
        allowed, violations = service.check_hard_rules(
            {
                "selected_option": "friend_loan",
                "amount_needed": 2500,
                "income_stable": True,
                "relationship_unsafe": False,
            }
        )
        assert allowed is False
        assert any("friends" in v.lower() for v in violations)

    def test_payday_blocked(self, service):
        allowed, violations = service.check_hard_rules(
            {"selected_option": "payday_loan", "amount_needed": 500, "income_stable": True}
        )
        assert allowed is False
        assert any("payday" in v.lower() for v in violations)

    def test_401k_blocked(self, service):
        allowed, violations = service.check_hard_rules(
            {"selected_option": "401k_withdrawal", "amount_needed": 5000, "income_stable": True}
        )
        assert allowed is False
        assert any("401" in v for v in violations)

    def test_accelerate_timeline_blocked_without_safety(self, service):
        allowed, violations = service.check_hard_rules(
            {
                "borrowing_reason": "accelerate_timeline",
                "accelerate_timeline": True,
                "amount_needed": 2500,
                "selected_option": "credit_union_loan",
                "income_stable": True,
                "relationship_unsafe": False,
            }
        )
        assert allowed is False
        assert any("accelerate" in v.lower() for v in violations)

    def test_unstable_income_blocked(self, service):
        allowed, violations = service.check_hard_rules(
            {
                "selected_option": "zero_apr_card",
                "amount_needed": 2500,
                "income_stable": False,
                "relationship_unsafe": False,
            }
        )
        assert allowed is False
        assert any("unstable" in v.lower() for v in violations)

    def test_relationship_unsafe_allows_borrowing_exception(self, service):
        payload = service.analyze_borrowing_options(
            1,
            2500,
            5000,
            500,
            borrowing_reason="relationship_unsafe",
            relationship_unsafe=True,
            income_stable=True,
        )
        assert payload["allowed"] is True

    def test_bridge_amount_allowed_when_stable(self, service):
        allowed, messages = service.check_hard_rules(
            {
                "amount_needed": 2500,
                "income_stable": True,
                "selected_option": "family_loan",
                "relationship_unsafe": False,
            }
        )
        assert allowed is True
        assert any("bridge" in m.lower() or "$2" in m for m in messages)

    def test_large_amount_blocked_without_safety(self, service):
        allowed, violations = service.check_hard_rules(
            {
                "amount_needed": 8000,
                "income_stable": True,
                "selected_option": "credit_union_loan",
                "relationship_unsafe": False,
            }
        )
        assert allowed is False
        assert any("exceeds" in v.lower() or "bridge" in v.lower() for v in violations)


class TestSustainability:
    def test_sustainable_payment(self, service):
        result = service.sustainability_check(5000, 500, 400)
        assert result["sustainable"] is True
        assert "guardrail" in result["reasoning"].lower()

    def test_unsustainable_payment(self, service):
        result = service.sustainability_check(3000, 0, 800)
        assert result["sustainable"] is False
        assert result["max_affordable_payment"] == 300.0

    def test_zero_income_not_sustainable(self, service):
        result = service.sustainability_check(0, 0, 100)
        assert result["sustainable"] is False


class TestAnalyzeOptions:
    def test_options_ranked_and_include_dont_borrow(self, service):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 600)
        keys = [row["key"] for row in payload["options"]]
        assert keys[0] == "dont_borrow"
        assert "family_loan" in keys
        assert "zero_apr_card" in keys
        assert "credit_union_loan" in keys

    def test_each_option_has_terms_and_sustainability(self, service):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 600)
        for option in payload["options"]:
            assert "terms" in option
            assert "pros" in option and option["pros"]
            assert "cons" in option and option["cons"]
            assert "sustainability" in option
            assert "monthly_payment" in option

    def test_unsafe_scenario_not_allowed(self, service):
        payload = service.analyze_borrowing_options(
            1,
            2500,
            3000,
            0,
            borrowing_reason="accelerate_timeline",
            accelerate_timeline=True,
            income_stable=False,
        )
        assert payload["allowed"] is False
        assert payload["warnings"]

    def test_resources_present(self, service):
        payload = service.analyze_borrowing_options(1, 2500, 5000, 500)
        assert "family_loan_template" in payload["resources"]
        assert "credit_union_locator_url" in payload["resources"]


class TestBorrowingApi:
    def test_analyze_endpoint(self, borrowing_app):
        client = borrowing_app.test_client()
        with borrowing_app.app_context():
            g.current_user_id = 1
            from unittest.mock import patch

            with patch(
                "backend.routes.borrowing_api.get_current_user_db_id",
                return_value=1,
            ):
                response = client.post(
                    "/api/borrowing/analyze",
                    json={
                        "amount_needed": 2500,
                        "monthly_income": 5000,
                        "side_income": 500,
                        "borrowing_reason": "bridge_startup",
                    },
                )

        assert response.status_code == 200
        body = response.get_json()
        assert "allowed" in body
        assert len(body["options"]) == 4
        assert body["forbidden_products"]

    def test_analyze_requires_auth(self, borrowing_app):
        client = borrowing_app.test_client()
        from unittest.mock import patch

        with borrowing_app.app_context(), patch(
            "backend.routes.borrowing_api.get_current_user_db_id",
            return_value=None,
        ):
            response = client.post(
                "/api/borrowing/analyze",
                json={"amount_needed": 2500, "monthly_income": 5000, "side_income": 0},
            )
        assert response.status_code == 401

    def test_invalid_reason_rejected(self, borrowing_app):
        client = borrowing_app.test_client()
        from unittest.mock import patch

        with borrowing_app.app_context(), patch(
            "backend.routes.borrowing_api.get_current_user_db_id",
            return_value=1,
        ):
            response = client.post(
                "/api/borrowing/analyze",
                json={
                    "amount_needed": 2500,
                    "monthly_income": 5000,
                    "side_income": 0,
                    "borrowing_reason": "payday_loan",
                },
            )
        assert response.status_code == 400
