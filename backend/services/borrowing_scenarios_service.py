#!/usr/bin/env python3
"""Borrowing scenario analysis with hard safety rules — analysis only, no persistence."""

from __future__ import annotations

from typing import Any

_BRIDGE_MIN = 2000.0
_BRIDGE_MAX = 3000.0
_MAX_DEBT_SERVICE_RATIO = 0.10
_CREDIT_UNION_APR_RANGE = (0.08, 0.12)
_ZERO_APR_PROMO_MONTHS = 15
_FAMILY_LOAN_TERM_MONTHS = 24

_HARD_RULES_META: tuple[dict[str, str], ...] = (
    {
        "id": "no_accelerate_timeline",
        "type": "block",
        "message": "DON'T borrow to accelerate timeline — use side income, expense cuts, and interim housing first.",
    },
    {
        "id": "safety_over_debt",
        "type": "allow",
        "message": "DO borrow if relationship is UNSAFE — safety takes priority over avoiding debt.",
    },
    {
        "id": "no_unstable_income",
        "type": "block",
        "message": "DON'T borrow if income is unstable.",
    },
    {
        "id": "bridge_only",
        "type": "allow",
        "message": "DO borrow only for a $2–3k short bridge when other paths are exhausted.",
    },
    {
        "id": "no_friend_loans",
        "type": "block",
        "message": "DON'T borrow from friends — use a written family loan or formal credit instead.",
    },
    {
        "id": "never_payday",
        "type": "block",
        "message": "NEVER use payday loans.",
    },
    {
        "id": "never_401k",
        "type": "block",
        "message": "NEVER withdraw from a 401(k) for move-out costs.",
    },
)

_BLOCKED_OPTION_TYPES = frozenset(
    {
        "payday_loan",
        "payday",
        "401k_withdrawal",
        "401k",
        "friend_loan",
        "friends",
    }
)

_FAMILY_LOAN_TEMPLATE = (
    "Hi [family member],\n\n"
    "I'm working toward moving out on my own and need a short bridge loan of ${amount:,.0f}. "
    "I'm asking for a {term_months}-month repayment plan at 0% interest with ${payment:,.0f}/month.\n\n"
    "I'll put the terms in writing and share my budget. Would you be open to a call this week?\n\n"
    "Thank you,\n[Your name]"
)


def _round2(value: float) -> float:
    return round(float(value), 2)


def _monthly_payment_principal_only(amount: float, months: int) -> float:
    if months <= 0:
        return amount
    return _round2(amount / months)


def _monthly_payment_amortized(amount: float, apr: float, months: int) -> float:
    if months <= 0 or amount <= 0:
        return 0.0
    monthly_rate = apr / 12.0
    if monthly_rate <= 0:
        return _monthly_payment_principal_only(amount, months)
    factor = (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return _round2(amount * factor)


class BorrowingScenarios:
    """Rank borrowing options by safety and enforce hard ICC guardrails."""

    def sustainability_check(
        self,
        monthly_income: float,
        side_income: float,
        loan_payment: float,
    ) -> dict[str, Any]:
        """Return whether the user can realistically repay the proposed payment."""
        income = float(monthly_income) + float(side_income)
        payment = float(loan_payment)
        if income <= 0:
            return {
                "sustainable": False,
                "reasoning": "No reliable monthly income is available to cover loan payments.",
                "max_affordable_payment": 0.0,
                "debt_service_ratio": None,
            }
        if payment <= 0:
            return {
                "sustainable": True,
                "reasoning": "No monthly payment required.",
                "max_affordable_payment": _round2(income * _MAX_DEBT_SERVICE_RATIO),
                "debt_service_ratio": 0.0,
            }

        max_payment = income * _MAX_DEBT_SERVICE_RATIO
        ratio = payment / income
        sustainable = payment <= max_payment and income >= payment * 3
        if sustainable:
            reasoning = (
                f"Payment of ${_round2(payment):,.0f}/mo is {_round2(ratio * 100):.1f}% of income "
                f"(under the {_round2(_MAX_DEBT_SERVICE_RATIO * 100):.0f}% guardrail)."
            )
        elif payment > max_payment:
            reasoning = (
                f"Payment of ${_round2(payment):,.0f}/mo exceeds the {_round2(_MAX_DEBT_SERVICE_RATIO * 100):.0f}% "
                f"affordability cap (${_round2(max_payment):,.0f}/mo)."
            )
        else:
            reasoning = (
                "Income is too thin relative to payment size — build a larger buffer before borrowing."
            )

        return {
            "sustainable": sustainable,
            "reasoning": reasoning,
            "max_affordable_payment": _round2(max_payment),
            "debt_service_ratio": _round2(ratio),
        }

    def check_hard_rules(self, scenario: dict[str, Any]) -> tuple[bool, list[str]]:
        """Evaluate scenario against non-negotiable borrowing rules."""
        violations: list[str] = []
        allows: list[str] = []

        option_type = str(scenario.get("selected_option") or scenario.get("option_type") or "").lower()
        amount = float(scenario.get("amount_needed") or 0)
        reason = str(scenario.get("borrowing_reason") or "").lower()
        relationship_unsafe = bool(scenario.get("relationship_unsafe"))
        income_stable = bool(scenario.get("income_stable", True))
        accelerate = bool(scenario.get("accelerate_timeline")) or "accelerat" in reason

        if option_type in _BLOCKED_OPTION_TYPES or "payday" in option_type:
            violations.append(_HARD_RULES_META[5]["message"])
        if option_type in {"401k_withdrawal", "401k"}:
            violations.append(_HARD_RULES_META[6]["message"])
        if option_type in {"friend_loan", "friends"}:
            violations.append(_HARD_RULES_META[4]["message"])

        if accelerate and not relationship_unsafe:
            violations.append(_HARD_RULES_META[0]["message"])

        if not income_stable and option_type not in {"", "dont_borrow", "none"}:
            violations.append(_HARD_RULES_META[2]["message"])

        if relationship_unsafe:
            allows.append(_HARD_RULES_META[1]["message"])

        if _BRIDGE_MIN <= amount <= _BRIDGE_MAX and income_stable:
            allows.append(_HARD_RULES_META[3]["message"])

        if amount > _BRIDGE_MAX and not relationship_unsafe and option_type not in {
            "",
            "dont_borrow",
            "none",
        }:
            violations.append(
                f"Amount ${_round2(amount):,.0f} exceeds the recommended $2–3k bridge — "
                "reduce the gap with side income and expense cuts first."
            )

        is_allowed = len(violations) == 0 or (
            relationship_unsafe and not any("NEVER" in v for v in violations)
        )
        messages = violations if violations else allows
        return is_allowed, messages

    def _build_option(
        self,
        *,
        key: str,
        name: str,
        safety_rank: int,
        safety_level: str,
        amount: float,
        monthly_payment: float,
        term_months: int,
        apr_percent: float,
        pros: list[str],
        cons: list[str],
        terms: dict[str, Any],
        monthly_income: float,
        side_income: float,
        scenario_context: dict[str, Any],
    ) -> dict[str, Any]:
        sustainability = self.sustainability_check(monthly_income, side_income, monthly_payment)
        option_scenario = {**scenario_context, "selected_option": key}
        allowed, rule_messages = self.check_hard_rules(option_scenario)
        blocked = not allowed and key != "dont_borrow"
        return {
            "key": key,
            "name": name,
            "safety_rank": safety_rank,
            "safety_level": safety_level,
            "recommended": key == "dont_borrow",
            "blocked": blocked,
            "allowed": allowed if key != "dont_borrow" else True,
            "terms": terms,
            "monthly_payment": monthly_payment,
            "term_months": term_months,
            "apr_percent": apr_percent,
            "total_repayment": _round2(monthly_payment * term_months) if monthly_payment else 0.0,
            "pros": pros,
            "cons": cons,
            "sustainability": sustainability,
            "rule_messages": rule_messages,
        }

    def analyze_borrowing_options(
        self,
        user_id: int,
        amount_needed: float,
        monthly_income: float,
        side_income: float,
        *,
        borrowing_reason: str = "bridge_startup",
        relationship_unsafe: bool = False,
        income_stable: bool = True,
        accelerate_timeline: bool = False,
    ) -> dict[str, Any]:
        if amount_needed < 0:
            raise ValueError("amount_needed must be non-negative")
        if monthly_income < 0 or side_income < 0:
            raise ValueError("income values must be non-negative")

        amount = _round2(float(amount_needed))
        scenario_context = {
            "amount_needed": amount,
            "borrowing_reason": borrowing_reason,
            "monthly_income": monthly_income,
            "side_income": side_income,
            "relationship_unsafe": relationship_unsafe,
            "income_stable": income_stable,
            "accelerate_timeline": accelerate_timeline,
            "user_id": user_id,
        }

        family_payment = _monthly_payment_principal_only(amount, _FAMILY_LOAN_TERM_MONTHS)
        card_payment = _monthly_payment_principal_only(amount, _ZERO_APR_PROMO_MONTHS)
        cu_apr = sum(_CREDIT_UNION_APR_RANGE) / 2.0
        cu_term = 48
        cu_payment = _monthly_payment_amortized(amount, cu_apr, cu_term)

        options = [
            self._build_option(
                key="dont_borrow",
                name="Don't borrow (recommended)",
                safety_rank=1,
                safety_level="green",
                amount=0.0,
                monthly_payment=0.0,
                term_months=0,
                apr_percent=0.0,
                pros=[
                    "No interest or damaged relationships",
                    "Forces side income, expense cuts, and interim housing first",
                    "Best long-term financial health",
                ],
                cons=[
                    "May extend timeline if savings are thin",
                    "Requires discipline on spending and income growth",
                ],
                terms={
                    "summary": "Close the gap with side income, tiered expense cuts, and interim housing.",
                    "alternative_paths": [
                        "Side income accelerator (DF1)",
                        "90-day expense audit tiers",
                        "Family / roommate / sublet interim housing",
                    ],
                },
                monthly_income=monthly_income,
                side_income=side_income,
                scenario_context=scenario_context,
            ),
            self._build_option(
                key="family_loan",
                name="Family loan (0% interest)",
                safety_rank=2,
                safety_level="green",
                amount=amount,
                monthly_payment=family_payment,
                term_months=_FAMILY_LOAN_TERM_MONTHS,
                apr_percent=0.0,
                pros=[
                    "0% interest if documented clearly",
                    "Flexible repayment conversations",
                    "Safer than commercial debt for small bridges",
                ],
                cons=[
                    "Can strain family relationships without clear terms",
                    "Not available to everyone",
                    "Still requires written agreement",
                ],
                terms={
                    "interest_rate": "0%",
                    "suggested_term_months": _FAMILY_LOAN_TERM_MONTHS,
                    "documentation": "Simple written promissory note with payment dates",
                },
                monthly_income=monthly_income,
                side_income=side_income,
                scenario_context=scenario_context,
            ),
            self._build_option(
                key="zero_apr_card",
                name="0% APR promotional credit card",
                safety_rank=3,
                safety_level="yellow",
                amount=amount,
                monthly_payment=card_payment,
                term_months=_ZERO_APR_PROMO_MONTHS,
                apr_percent=0.0,
                pros=[
                    "No interest during promo period if paid on time",
                    "Fast access if approved",
                    "Works for short bridges with a payoff plan",
                ],
                cons=[
                    "High retroactive APR if promo expires with a balance",
                    "Easy to overspend without discipline",
                    "Credit score impact if utilization stays high",
                ],
                terms={
                    "promo_apr": "0% for 12–18 months (modeled at 15)",
                    "post_promo_warning": "Pay off before promo ends or refinance immediately",
                    "credit_limit_needed": amount,
                },
                monthly_income=monthly_income,
                side_income=side_income,
                scenario_context=scenario_context,
            ),
            self._build_option(
                key="credit_union_loan",
                name="Credit union personal loan",
                safety_rank=4,
                safety_level="yellow",
                amount=amount,
                monthly_payment=cu_payment,
                term_months=cu_term,
                apr_percent=_round2(cu_apr * 100),
                pros=[
                    "Fixed payment and defined payoff date",
                    "Lower rates than most banks or cards after promo",
                    "Builds credit history when paid on time",
                ],
                cons=[
                    f"Interest cost ({_round2(_CREDIT_UNION_APR_RANGE[0]*100):.0f}–{_round2(_CREDIT_UNION_APR_RANGE[1]*100):.0f}% APR modeled)",
                    "Approval depends on credit and income",
                    "Longer commitment than a true bridge loan",
                ],
                terms={
                    "apr_range": f"{_round2(_CREDIT_UNION_APR_RANGE[0]*100):.0f}%–{_round2(_CREDIT_UNION_APR_RANGE[1]*100):.0f}%",
                    "modeled_apr": _round2(cu_apr * 100),
                    "term_months": cu_term,
                },
                monthly_income=monthly_income,
                side_income=side_income,
                scenario_context=scenario_context,
            ),
        ]

        options.sort(key=lambda row: row["safety_rank"])

        global_allowed, global_violations = self.check_hard_rules(scenario_context)
        warnings = [v for v in global_violations if v.startswith("DON'T") or v.startswith("NEVER") or "exceeds" in v]
        if not income_stable:
            warnings.append(_HARD_RULES_META[2]["message"])
        if accelerate_timeline and not relationship_unsafe:
            warnings.append(_HARD_RULES_META[0]["message"])

        forbidden_mentions = [
            {"key": "payday_loan", "label": "Payday loan", "blocked": True, "reason": _HARD_RULES_META[5]["message"]},
            {"key": "401k_withdrawal", "label": "401(k) withdrawal", "blocked": True, "reason": _HARD_RULES_META[6]["message"]},
            {"key": "friend_loan", "label": "Friend loan", "blocked": True, "reason": _HARD_RULES_META[4]["message"]},
        ]

        best_option = next((o for o in options if o["key"] == "dont_borrow"), options[0])
        if relationship_unsafe and global_allowed:
            recommendation = (
                "If you must borrow for immediate safety, a documented family loan or 0% card "
                "with a strict payoff plan is least risky — but only after confirming income can sustain payments."
            )
        elif not global_allowed:
            recommendation = (
                "Borrowing is not recommended under current rules. Pursue side income, expense cuts, "
                "and interim housing before taking on debt."
            )
        else:
            recommendation = best_option["name"]

        family_template = _FAMILY_LOAN_TEMPLATE.format(
            amount=amount,
            term_months=_FAMILY_LOAN_TERM_MONTHS,
            payment=family_payment,
        )

        return {
            "user_id": user_id,
            "amount_needed": amount,
            "monthly_income": _round2(monthly_income),
            "side_income": _round2(side_income),
            "borrowing_reason": borrowing_reason,
            "allowed": global_allowed,
            "options": options,
            "warnings": warnings,
            "hard_rules": [rule["message"] for rule in _HARD_RULES_META],
            "forbidden_products": forbidden_mentions,
            "recommendation": recommendation,
            "resources": {
                "family_loan_template": family_template,
                "credit_union_locator_url": "https://www.mycreditunion.gov/about-credit-unions/credit-union-locator",
                "nfcc_counseling_url": "https://www.nfcc.org/",
            },
        }
