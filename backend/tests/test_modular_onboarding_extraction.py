"""Regression tests for recurring_expenses extraction / ready-token gating."""

from __future__ import annotations

import pytest

from backend.routes.modular_onboarding import (
    _recurring_expense_positive_category_count,
    extract_module_data,
)


def _positive_amounts_by_category(data: dict) -> dict[str, float]:
    """Map category_id -> amount for diagnostics in assertion messages."""
    out: dict[str, float] = {}
    for row in data.get("categories") or []:
        if not isinstance(row, dict):
            continue
        cid = row.get("category_id")
        if not cid:
            continue
        try:
            out[str(cid)] = float(row.get("amount") or 0)
        except (TypeError, ValueError):
            out[str(cid)] = 0.0
    return out


def test_scenario_1_no_token_returns_empty():
    text = "What's your second biggest expense?"
    got = extract_module_data(text, "recurring_expenses")
    assert got == {}, (
        "expected empty dict when no [EXPENSES_READY] token is present; "
        f"got keys={list(got.keys()) if isinstance(got, dict) else type(got)}"
    )


def test_scenario_2_token_not_at_end_returns_empty():
    text = "I got [EXPENSES_READY] categories already from earlier."
    got = extract_module_data(text, "recurring_expenses")
    assert got == {}, (
        "token must be at end of response (after rstrip); substring match alone "
        "must not commit"
    )


def test_scenario_3_token_at_end_but_only_two_categories_returns_empty():
    text = "Rent is $700 and car payment is $220. [EXPENSES_READY]"
    got = extract_module_data(text, "recurring_expenses")
    assert got == {}, (
        "expected {} when fewer than 3 categories resolve to a positive amount; "
        f"got positive_count={_recurring_expense_positive_category_count(got)} "
        f"amounts_by_cat={_positive_amounts_by_category(got)}"
    )


def test_scenario_4_token_at_end_three_positive_categories():
    text = "Rent $700, car payment $220, groceries $300. [EXPENSES_READY]"
    got = extract_module_data(text, "recurring_expenses")
    assert got, "expected non-empty extraction when token is at end and >=3 positives"
    assert "categories" in got, f"missing categories key; got keys={list(got.keys())}"
    n = _recurring_expense_positive_category_count(got)
    assert n >= 3, (
        f"expected at least 3 categories with amount > 0, got {n}; "
        f"amounts_by_cat={_positive_amounts_by_category(got)}"
    )


def test_scenario_5_token_at_end_five_positive_categories():
    text = (
        "Got it: rent $700, car payment $220, groceries $300, "
        "utilities $120, subscriptions $50. [EXPENSES_READY]"
    )
    got = extract_module_data(text, "recurring_expenses")
    assert got, "expected non-empty extraction for five labeled expense amounts"
    assert "categories" in got, f"missing categories key; got keys={list(got.keys())}"
    n = _recurring_expense_positive_category_count(got)
    assert n >= 5, (
        f"expected at least 5 categories with amount > 0, got {n}; "
        f"amounts_by_cat={_positive_amounts_by_category(got)}"
    )


def test_scenario_6_only_zeros_returns_empty():
    text = "Rent $0, car payment $0, groceries $0. [EXPENSES_READY]"
    got = extract_module_data(text, "recurring_expenses")
    assert got == {}, (
        "zeros must not satisfy the 3-category minimum; "
        f"got positive_count={_recurring_expense_positive_category_count(got)}"
    )


def test_scenario_7_mixed_zeros_and_real_values():
    text = (
        "Rent $700, food $0, car $220, utilities $0, subs $50.\n[EXPENSES_READY]"
    )
    got = extract_module_data(text, "recurring_expenses")
    assert got, (
        "expected non-empty dict when at least three hint categories resolve to "
        "positive amounts despite zeros elsewhere"
    )
    n = _recurring_expense_positive_category_count(got)
    assert n >= 3, (
        f"expected >=3 positive categories (rent/other, utilities, groceries chain, "
        f"etc. per extractor), got {n}; amounts_by_cat={_positive_amounts_by_category(got)}"
    )


def test_scenario_8_trailing_whitespace_after_token_still_commits():
    # Same as spec intent (rent / car / food + trailing spaces); use "car payment"
    # so the debt hints in CATEGORY_KEYS match (plain "car" does not).
    text = "Rent $700, car payment $220, food $300. [EXPENSES_READY]   \n"
    got = extract_module_data(text, "recurring_expenses")
    assert got, (
        "rstrip() before endswith should allow trailing whitespace after the token"
    )
    n = _recurring_expense_positive_category_count(got)
    assert n >= 3, (
        f"expected >=3 positive categories, got {n}; "
        f"amounts_by_cat={_positive_amounts_by_category(got)}"
    )


def test_scenario_9_stale_module_complete_expenses_token_ignored():
    text = "Rent $700, car $220, food $300. [MODULE_COMPLETE:expenses]"
    got = extract_module_data(text, "recurring_expenses")
    assert got == {}, (
        "legacy [MODULE_COMPLETE:expenses] must not satisfy recurring_expenses "
        f"ready gate; got={got!r}"
    )


def test_recurring_expense_positive_category_count_three_positives():
    sample = {
        "categories": [
            {"category_id": "insurance", "amount": 100.0},
            {"category_id": "debt", "amount": 200.0},
            {"category_id": "subscription", "amount": 0.0},
            {"category_id": "utilities", "amount": 50.0},
        ]
    }
    assert (
        _recurring_expense_positive_category_count(sample) == 3
    ), "should count exactly three strictly positive amounts"


def test_recurring_expense_positive_category_count_empty_dict():
    assert (
        _recurring_expense_positive_category_count({}) == 0
    ), "missing categories should yield zero positives"
