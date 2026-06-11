#!/usr/bin/env python3
"""Employer health scoring from SEC EDGAR company facts (CR9b)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from backend.models.database import db
from backend.models.employer import Employer, EmployerHealthSnapshot
from backend.services.sec_edgar_client import (
    SecEdgarClient,
    extract_concept,
    trailing_four_quarters,
)

logger = logging.getLogger(__name__)

REVENUE_CONCEPTS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
)
OPERATING_INCOME_CONCEPT = "OperatingIncomeLoss"
OPERATING_CF_CONCEPT = "NetCashProvidedByUsedInOperatingActivities"
CAPEX_CONCEPT = "PaymentsToAcquirePropertyPlantAndEquipment"
CASH_CONCEPT = "CashAndCashEquivalentsAtCarryingValue"
OPERATING_EXPENSE_CONCEPT = "OperatingExpenses"
EQUITY_CONCEPT = "StockholdersEquity"
DEBT_CONCEPTS = ("LongTermDebt", "LongTermDebtNoncurrent")


def get_multiplier(score: float | None) -> float:
    """Map health score to career risk multiplier."""
    if score is None:
        return 1.0
    if score >= 80:
        return 0.85
    if score >= 65:
        return 0.95
    if score >= 50:
        return 1.0
    if score >= 35:
        return 1.15
    if score >= 20:
        return 1.35
    return 1.50


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _first_concept_entries(facts_response: dict, concepts: tuple[str, ...]) -> list[dict]:
    for concept in concepts:
        entries = extract_concept(facts_response, "us-gaap", concept)
        if entries:
            return entries
    return []


def _score_revenue_delta(current_ttm: float | None, prior_ttm: float | None) -> float:
    if current_ttm is None or prior_ttm is None or prior_ttm == 0:
        return 0.0
    pct = ((current_ttm - prior_ttm) / prior_ttm) * 100.0
    if pct > 10:
        return 10.0
    if pct >= 5:
        return 5.0
    if pct >= 0:
        return 0.0
    if pct >= -5:
        return -5.0
    return -10.0


def _score_operating_margin(margin: float | None) -> float:
    if margin is None:
        return 0.0
    pct = margin * 100.0
    if pct > 20:
        return 10.0
    if pct >= 10:
        return 5.0
    if pct >= 0:
        return 0.0
    if pct >= -10:
        return -5.0
    return -10.0


def _score_fcf(fcf: float | None, revenue_ttm: float | None) -> float:
    if fcf is None:
        return 0.0
    if fcf > 0 and revenue_ttm and revenue_ttm > 0 and (fcf / revenue_ttm) > 0.1:
        return 10.0
    if fcf > 0:
        return 5.0
    if fcf == 0:
        return 0.0
    if revenue_ttm and revenue_ttm > 0 and (fcf / revenue_ttm) < -0.1:
        return -10.0
    if fcf < 0:
        return -5.0
    return 0.0


def _score_runway(cash: float | None, quarterly_opex: float | None) -> float:
    if cash is None or quarterly_opex is None or quarterly_opex <= 0:
        return 0.0
    annual_burn = quarterly_opex * 4
    if annual_burn <= 0:
        return 0.0
    runway_years = cash / annual_burn
    if runway_years > 2:
        return 10.0
    if runway_years >= 1:
        return 5.0
    if runway_years >= 0.5:
        return 0.0
    if runway_years >= 0.25:
        return -5.0
    return -10.0


def _score_leverage(debt: float | None, equity: float | None) -> float:
    if debt is None or equity is None or equity <= 0:
        return 0.0
    ratio = debt / equity
    if ratio < 0.5:
        return 10.0
    if ratio <= 1.0:
        return 5.0
    if ratio <= 2.0:
        return 0.0
    if ratio <= 3.0:
        return -5.0
    return -10.0


def compute_health_scores(facts_response: dict) -> dict[str, Any]:
    """
    Compute component and final scores from a companyfacts API response.
    Returns dict with metrics, component scores, final score, and multiplier.
    """
    revenue_entries = _first_concept_entries(facts_response, REVENUE_CONCEPTS)
    op_income_entries = extract_concept(facts_response, "us-gaap", OPERATING_INCOME_CONCEPT)
    op_cf_entries = extract_concept(facts_response, "us-gaap", OPERATING_CF_CONCEPT)
    capex_entries = extract_concept(facts_response, "us-gaap", CAPEX_CONCEPT)
    cash_entries = extract_concept(facts_response, "us-gaap", CASH_CONCEPT)
    opex_entries = extract_concept(facts_response, "us-gaap", OPERATING_EXPENSE_CONCEPT)
    equity_entries = extract_concept(facts_response, "us-gaap", EQUITY_CONCEPT)
    debt_entries = _first_concept_entries(facts_response, DEBT_CONCEPTS)

    revenue_ttm = trailing_four_quarters(revenue_entries)
    prior_revenue_ttm = trailing_four_quarters(revenue_entries, skip=4)
    op_income_ttm = trailing_four_quarters(op_income_entries)
    op_cf_ttm = trailing_four_quarters(op_cf_entries)
    capex_ttm = trailing_four_quarters(capex_entries)

    operating_margin = None
    if revenue_ttm and revenue_ttm > 0 and op_income_ttm is not None:
        operating_margin = op_income_ttm / revenue_ttm

    free_cash_flow = None
    if op_cf_ttm is not None and capex_ttm is not None:
        free_cash_flow = op_cf_ttm - capex_ttm

    cash_and_equiv = None
    if cash_entries:
        cash_entries.sort(key=lambda e: e.get("end") or "", reverse=True)
        if cash_entries[0].get("val") is not None:
            cash_and_equiv = float(cash_entries[0]["val"])

    quarterly_opex = trailing_four_quarters(opex_entries)
    if quarterly_opex is not None:
        quarterly_opex = quarterly_opex / 4.0

    total_debt = None
    if debt_entries:
        debt_entries.sort(key=lambda e: e.get("end") or "", reverse=True)
        if debt_entries[0].get("val") is not None:
            total_debt = float(debt_entries[0]["val"])

    equity = None
    if equity_entries:
        equity_entries.sort(key=lambda e: e.get("end") or "", reverse=True)
        if equity_entries[0].get("val") is not None:
            equity = float(equity_entries[0]["val"])

    revenue_delta_score = _score_revenue_delta(revenue_ttm, prior_revenue_ttm)
    margin_score = _score_operating_margin(operating_margin)
    fcf_score = _score_fcf(free_cash_flow, revenue_ttm)
    runway_score = _score_runway(cash_and_equiv, quarterly_opex)
    leverage_score = _score_leverage(total_debt, equity)

    component_sum = (
        revenue_delta_score
        + margin_score
        + fcf_score
        + runway_score
        + leverage_score
    )
    final_score = _clamp_score(50.0 + component_sum)

    fiscal_period_end = None
    if revenue_entries:
        revenue_entries.sort(key=lambda e: e.get("end") or "", reverse=True)
        end_str = revenue_entries[0].get("end")
        if end_str:
            try:
                fiscal_period_end = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                fiscal_period_end = None

    return {
        "score": final_score,
        "revenue_delta_score": revenue_delta_score,
        "margin_score": margin_score,
        "fcf_score": fcf_score,
        "runway_score": runway_score,
        "leverage_score": leverage_score,
        "multiplier": get_multiplier(final_score),
        "revenue_ttm": revenue_ttm,
        "operating_margin": operating_margin,
        "free_cash_flow": free_cash_flow,
        "cash_and_equiv": cash_and_equiv,
        "total_debt": total_debt,
        "fiscal_period_end": fiscal_period_end,
    }


def get_latest_snapshot(
    employer_id: int,
    db_session=None,
) -> EmployerHealthSnapshot | None:
    session = db_session or db.session
    return (
        session.query(EmployerHealthSnapshot)
        .filter_by(employer_id=employer_id)
        .order_by(EmployerHealthSnapshot.refreshed_at.desc())
        .first()
    )


def refresh_employer_health(
    cik: str,
    db_session=None,
) -> EmployerHealthSnapshot | None:
    """Fetch EDGAR facts, score employer health, and persist snapshot."""
    session = db_session or db.session
    try:
        cik_padded = str(cik).strip().zfill(10)
        client = SecEdgarClient()
        facts_response = client.get_company_facts(cik_padded)
        if facts_response is None:
            logger.warning("No company facts returned for CIK %s", cik_padded)
            return None

        entity_name = facts_response.get("entityName") or "Unknown"
        scores = compute_health_scores(facts_response)

        employer = session.query(Employer).filter_by(cik=cik_padded).first()
        if employer is None:
            employer = Employer(cik=cik_padded, name=entity_name)
            session.add(employer)
            session.flush()
        else:
            employer.name = entity_name
            employer.updated_at = datetime.utcnow()

        now = datetime.utcnow()
        six_days_ago = now - timedelta(days=6)
        eight_days_ago = now - timedelta(days=8)

        snapshot = (
            session.query(EmployerHealthSnapshot)
            .filter(
                EmployerHealthSnapshot.employer_id == employer.id,
                EmployerHealthSnapshot.refreshed_at >= six_days_ago,
            )
            .order_by(EmployerHealthSnapshot.refreshed_at.desc())
            .first()
        )

        if snapshot is None:
            snapshot = EmployerHealthSnapshot(employer_id=employer.id)
            session.add(snapshot)

        snapshot.score = scores["score"]
        snapshot.revenue_delta_score = scores["revenue_delta_score"]
        snapshot.margin_score = scores["margin_score"]
        snapshot.fcf_score = scores["fcf_score"]
        snapshot.runway_score = scores["runway_score"]
        snapshot.leverage_score = scores["leverage_score"]
        snapshot.revenue_ttm = scores["revenue_ttm"]
        snapshot.operating_margin = scores["operating_margin"]
        snapshot.free_cash_flow = scores["free_cash_flow"]
        snapshot.cash_and_equiv = scores["cash_and_equiv"]
        snapshot.total_debt = scores["total_debt"]
        snapshot.fiscal_period_end = scores["fiscal_period_end"]
        snapshot.data_source = "sec_edgar"
        snapshot.is_stale = False
        snapshot.refreshed_at = now

        session.query(EmployerHealthSnapshot).filter(
            EmployerHealthSnapshot.employer_id == employer.id,
            EmployerHealthSnapshot.refreshed_at < eight_days_ago,
        ).update({"is_stale": True}, synchronize_session=False)

        session.commit()
        return snapshot
    except Exception:
        logger.exception("refresh_employer_health failed for CIK %s", cik)
        session.rollback()
        return None
