"""Unit tests for SEC EDGAR concept extraction and employer health scoring."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.services.employer_health_scoring import compute_health_scores, get_multiplier
from backend.services.sec_edgar_client import (
    extract_concept,
    latest_annual_value,
    trailing_four_quarters,
)


def _entry(val, end, form="10-Q", filed=None):
    return {
        "val": val,
        "end": end,
        "filed": filed or end,
        "form": form,
        "accn": "0000000000-24-000001",
    }


def _build_facts(concept_entries: dict) -> dict:
    us_gaap = {}
    for concept, entries in concept_entries.items():
        us_gaap[concept] = {"units": {"USD": entries}}
    return {"facts": {"us-gaap": us_gaap}}


def _revenue_quarters(current_per_q: float, prior_per_q: float) -> list[dict]:
    """Eight consecutive quarters: four current TTM + four prior TTM."""
    ends = [
        "2024-12-31",
        "2024-09-30",
        "2024-06-30",
        "2024-03-31",
        "2023-12-31",
        "2023-09-30",
        "2023-06-30",
        "2023-03-31",
    ]
    vals = [current_per_q] * 4 + [prior_per_q] * 4
    return [_entry(v, end) for v, end in zip(vals, ends)]


class TestExtractConcept(unittest.TestCase):
    def test_returns_entries_when_key_exists(self):
        facts = _build_facts(
            {
                "Revenues": [
                    _entry(100, "2024-12-31"),
                    _entry(90, "2024-09-30"),
                ],
            }
        )
        entries = extract_concept(facts, "us-gaap", "Revenues")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["val"], 100)
        self.assertEqual(entries[0]["end"], "2024-12-31")

    def test_returns_empty_when_taxonomy_missing(self):
        facts = {"facts": {}}
        self.assertEqual(extract_concept(facts, "us-gaap", "Revenues"), [])

    def test_returns_empty_when_unit_missing(self):
        facts = {
            "facts": {
                "us-gaap": {
                    "Revenues": {"units": {"EUR": [_entry(1, "2024-12-31")]}},
                },
            },
        }
        self.assertEqual(extract_concept(facts, "us-gaap", "Revenues", unit="USD"), [])


class TestLatestAnnualValue(unittest.TestCase):
    def test_returns_most_recent_10k(self):
        entries = [
            _entry(100, "2023-12-31", form="10-K"),
            _entry(120, "2024-12-31", form="10-K"),
            _entry(30, "2024-09-30", form="10-Q"),
        ]
        self.assertEqual(latest_annual_value(entries), 120.0)

    def test_returns_none_without_10k(self):
        entries = [_entry(30, "2024-09-30", form="10-Q")]
        self.assertIsNone(latest_annual_value(entries))


class TestTrailingFourQuarters(unittest.TestCase):
    def test_sums_four_most_recent_quarters(self):
        entries = [
            _entry(10, "2024-12-31"),
            _entry(20, "2024-09-30"),
            _entry(30, "2024-06-30"),
            _entry(40, "2024-03-31"),
            _entry(5, "2023-12-31"),
        ]
        self.assertEqual(trailing_four_quarters(entries), 100.0)

    def test_returns_none_with_fewer_than_four_quarters(self):
        entries = [
            _entry(10, "2024-12-31"),
            _entry(20, "2024-09-30"),
        ]
        self.assertIsNone(trailing_four_quarters(entries))


class TestScoreComputation(unittest.TestCase):
    def _case_a_facts(self) -> dict:
        revenue = _revenue_quarters(28, 25)
        op_income = [_entry(5.04, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        op_cf = [_entry(7.5, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        capex = [_entry(3.58, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        opex = [_entry(15, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        return _build_facts(
            {
                "Revenues": revenue,
                "OperatingIncomeLoss": op_income,
                "NetCashProvidedByUsedInOperatingActivities": op_cf,
                "PaymentsToAcquirePropertyPlantAndEquipment": capex,
                "OperatingExpenses": opex,
                "CashAndCashEquivalentsAtCarryingValue": [
                    _entry(80, "2024-12-31"),
                ],
                "LongTermDebt": [_entry(55, "2024-12-31")],
                "StockholdersEquity": [_entry(100, "2024-12-31")],
            }
        )

    def _case_b_facts(self) -> dict:
        revenue = _revenue_quarters(23, 25)
        op_income = [_entry(-3.45, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        op_cf = [_entry(-2.0, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        capex = [_entry(1.45, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        opex = [_entry(15, end) for end in [
            "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31",
        ]]
        return _build_facts(
            {
                "Revenues": revenue,
                "OperatingIncomeLoss": op_income,
                "NetCashProvidedByUsedInOperatingActivities": op_cf,
                "PaymentsToAcquirePropertyPlantAndEquipment": capex,
                "OperatingExpenses": opex,
                "CashAndCashEquivalentsAtCarryingValue": [
                    _entry(40, "2024-12-31"),
                ],
                "LongTermDebt": [_entry(250, "2024-12-31")],
                "StockholdersEquity": [_entry(100, "2024-12-31")],
            }
        )

    def test_case_a_strong_employer(self):
        scores = compute_health_scores(self._case_a_facts())
        self.assertGreaterEqual(scores["score"], 75)
        self.assertLessEqual(scores["score"], 85)

    def test_case_b_distressed_employer(self):
        scores = compute_health_scores(self._case_b_facts())
        self.assertGreaterEqual(scores["score"], 15)
        self.assertLessEqual(scores["score"], 25)


class TestGetMultiplier(unittest.TestCase):
    def test_boundary_values(self):
        self.assertEqual(get_multiplier(80), 0.85)
        self.assertEqual(get_multiplier(50), 1.0)
        self.assertEqual(get_multiplier(19), 1.50)
        self.assertEqual(get_multiplier(None), 1.0)


if __name__ == "__main__":
    unittest.main()
