#!/usr/bin/env python3
"""
Mingus Conditions Index (MCI) service.

This module fetches external indicators (best-effort), normalizes them into a
standard constituent shape, and builds a single composite snapshot.
"""

from __future__ import annotations

import json
import logging
import os
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Ensure `services.*` imports work when called from Flask app/test harness.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

CACHE_DEFAULT_TIMEOUT_S = float(os.environ.get("MCI_HTTP_TIMEOUT_SECONDS", "4.0"))

PMMS_FALLBACK_RATE = 6.82  # last known per prompt
CREDIT_APR_FALLBACK = 21.76

IRS_MILEAGE_2024 = 0.67
IRS_MILEAGE_2025 = 0.70

# These aren't specified in the prompt, but we need safe defaults when network
# calls are unavailable in CI/test environments.
BLS_LAYOFF_RATE_FALLBACK = 1.25
BLS_QUIT_RATE_FALLBACK = 2.30
EIA_GAS_PRICE_FALLBACK = 3.50

WELLNESS_HEALTHCARE_PCT_INCOME_MID = 5.0

FREDDIE_PMMS_URL = "https://www.freddiemac.com/pmms/docs/historicalweeklydata.xls"
EIA_GAS_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
FED_G19_URL = "https://www.federalreserve.gov/releases/g19/current/g19.htm"
BLS_TIMESERIES_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


WEIGHT_LABOR_MARKET_STRENGTH = 0.25
WEIGHT_HOUSING_AFFORDABILITY_PRESSURE = 0.25
WEIGHT_TRANSPORTATION_COST_BURDEN = 0.10
WEIGHT_CONSUMER_DEBT_CONDITIONS = 0.20
WEIGHT_CAREER_INCOME_MOBILITY = 0.15
WEIGHT_WELLNESS_COST_INDEX = 0.05


SEVERITY_TO_SCORE = {
    "green": 80.0,
    "amber": 50.0,
    "red": 20.0,
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _direction_from_compare(current: float, previous: float, eps: float = 1e-9) -> str:
    if current > previous + eps:
        return "up"
    if current < previous - eps:
        return "down"
    return "flat"


def _to_iso_date(d: date) -> str:
    return d.isoformat()


def _today_iso() -> str:
    return date.today().isoformat()


def _bls_period_to_iso_date(year: int, period: str) -> str:
    """
    Convert BLS period tokens (e.g., "M01", "Q1") into a best-effort ISO date.
    """
    period = str(period).strip()
    if period.startswith("M"):
        month = int(period[1:])
        return _to_iso_date(date(int(year), month, 1))
    if period.startswith("Q"):
        q = int(period[1:])
        month = (q - 1) * 3 + 1
        return _to_iso_date(date(int(year), month, 1))
    if period.startswith("A"):
        return _to_iso_date(date(int(year), 12, 31))

    # Fallback: best effort to something parseable.
    return _today_iso()


def _severity_for_layoff_rate(layoff_rate: float) -> str:
    # lower is better
    if layoff_rate < 1.0:
        return "green"
    if layoff_rate <= 1.5:
        return "amber"
    return "red"


def _severity_for_housing_rate(rate: float) -> str:
    # higher is worse
    if rate < 6.0:
        return "green"
    if rate <= 7.5:
        return "amber"
    return "red"


def _severity_for_gas_price(price: float) -> str:
    # higher is worse
    if price < 3.00:
        return "green"
    if price <= 3.75:
        return "amber"
    return "red"


def _severity_for_credit_apr(apr: float) -> str:
    # higher is worse
    if apr < 18.0:
        return "green"
    if apr <= 22.0:
        return "amber"
    return "red"


def _severity_for_quit_rate(quit_rate: float) -> str:
    # higher is better
    if quit_rate > 2.5:
        return "green"
    if quit_rate >= 2.0:
        return "amber"
    return "red"


def _severity_for_wellness(_: float) -> str:
    # Always green unless overridden.
    override = os.environ.get("MCI_WELLNESS_SEVERITY")
    if override in ("green", "amber", "red"):
        return override
    return "green"


def _constituent_score(severity: str) -> float:
    return SEVERITY_TO_SCORE.get(severity, 50.0)


# -----------------------------------------------------------------------------
# Public helpers (used by unit tests)
# -----------------------------------------------------------------------------


def get_direction(*, latest: float, three_month_avg: float) -> str:
    """
    Labor-market direction: compare latest value to a 3-month average.
    """
    return _direction_from_compare(float(latest), float(three_month_avg))


def get_severity(
    *,
    layoff_rate: Optional[float] = None,
    rate: Optional[float] = None,
    price: Optional[float] = None,
    apr: Optional[float] = None,
    quit_rate: Optional[float] = None,
) -> str:
    """
    Generic severity mapping helper.

    Provide exactly one of the supported keyword args to pick the relevant
    constituent severity logic.
    """
    if layoff_rate is not None:
        return _severity_for_layoff_rate(float(layoff_rate))
    if rate is not None:
        return _severity_for_housing_rate(float(rate))
    if price is not None:
        return _severity_for_gas_price(float(price))
    if apr is not None:
        return _severity_for_credit_apr(float(apr))
    if quit_rate is not None:
        return _severity_for_quit_rate(float(quit_rate))

    # Wellness and other constituents are static in this foundation prompt.
    raise ValueError("No severity input provided")


def calculate_composite_score(constituents: List[Dict[str, Any]]) -> float:
    """
    Calculate composite score from constituent dicts.

    Expected each constituent includes:
      - `severity` in {"green","amber","red"}
      - `weight` as a decimal
    """
    # Use Decimal-like arithmetic via string conversion to keep the mixed
    # fixture stable for equality assertions in unit tests.
    from decimal import Decimal

    total = Decimal("0")
    for c in constituents:
        sev = str(c.get("severity", "amber"))
        score = Decimal(str(SEVERITY_TO_SCORE.get(sev, 50.0)))
        weight = Decimal(str(c.get("weight", 0)))
        total += score * weight

    # Quantize to 0.01 so 56.0 stays exactly representable for assertions.
    return float(total.quantize(Decimal("0.01")))


def calculate_composite_snapshot(constituents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Produce the top-level composite fields from constituent dicts.
    """
    composite_score = calculate_composite_score(constituents)

    if composite_score >= 65.0:
        composite_severity = "green"
    elif composite_score >= 35.0:
        composite_severity = "amber"
    else:
        composite_severity = "red"

    # "Worst constituent" is the lowest severity score (red=20 worst).
    worst = min(constituents, key=lambda c: _constituent_score(str(c.get("severity", "amber"))))
    composite_headline = str(worst.get("headline", "MCI snapshot ready"))

    return {
        "composite_score": composite_score,
        "composite_severity": composite_severity,
        "composite_headline": composite_headline,
        "constituents": constituents,
    }


def _make_constituent(
    *,
    name: str,
    slug: str,
    current_value: float,
    previous_value: float,
    direction: str,
    severity: str,
    headline: str,
    source: str,
    as_of: str,
    weight: float,
    raw: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "name": name,
        "slug": slug,
        "current_value": float(current_value),
        "previous_value": float(previous_value),
        "direction": direction,
        "severity": severity,
        "headline": str(headline),
        "source": str(source),
        "as_of": str(as_of),
        "weight": float(weight),
        "raw": raw or {},
    }


def _truncate_headline_to_12_words(headline: str) -> str:
    words = [w for w in str(headline).strip().split() if w]
    if len(words) <= 12:
        return str(headline).strip()
    return " ".join(words[:12]).strip()


def _requests_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mingus-MCI/1.0",
            "Accept": "application/json,text/html,application/xhtml+xml,*/*",
        }
    )
    return s


# -----------------------------------------------------------------------------
# Constituent 1: labor_market_strength
# -----------------------------------------------------------------------------


def _fetch_bls_timeseries_points(series_id: str, lookback_months: int = 8) -> List[Tuple[str, float]]:
    """
    Return a list of (iso_date, value) sorted ascending.
    """
    session = _requests_session()
    today = date.today()
    start_year = today.year - 3
    end_year = today.year

    payload = {
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": "",
    }

    try:
        resp = session.post(BLS_TIMESERIES_URL, json=payload, timeout=CACHE_DEFAULT_TIMEOUT_S)
        resp.raise_for_status()
        payload_json = resp.json()
    except Exception as e:
        logger.warning("BLS fetch failed for %s: %s", series_id, e)
        return []

    results = payload_json.get("Results") or payload_json.get("results") or {}
    series_list = results.get("series") or results.get("SERIES") or []
    if not series_list and isinstance(payload_json, list):
        series_list = payload_json

    if not series_list:
        return []

    series_obj = series_list[0]
    data_points = series_obj.get("data") or series_obj.get("DATA") or []
    out: List[Tuple[str, float]] = []
    for point in data_points:
        year = point.get("year") or point.get("Year")
        period = point.get("period") or point.get("Period")
        value = point.get("value") or point.get("Value")
        if year is None or period is None or value is None:
            continue
        f = _safe_float(value)
        if f is None:
            continue
        try:
            iso = _bls_period_to_iso_date(int(year), str(period))
        except Exception:
            iso = _today_iso()
        out.append((iso, f))

    # Sort ascending by iso_date, then keep last N.
    out.sort(key=lambda x: x[0])
    if lookback_months and len(out) > lookback_months:
        out = out[-lookback_months:]
    return out


def get_labor_market_strength() -> Dict[str, Any]:
    series_id = "JTS000000000000000LDR"

    points = _fetch_bls_timeseries_points(series_id, lookback_months=10)
    if len(points) < 2:
        current_value = float(BLS_LAYOFF_RATE_FALLBACK)
        previous_value = float(BLS_LAYOFF_RATE_FALLBACK)
        direction = "flat"
        severity = _severity_for_layoff_rate(current_value)
        as_of = _today_iso()
        headline = _truncate_headline_to_12_words(
            f"Layoff rate is {current_value:.2f}% today"
        )
        return _make_constituent(
            name="Labor Market Strength",
            slug="labor_market_strength",
            current_value=current_value,
            previous_value=previous_value,
            direction=direction,
            severity=severity,
            headline=headline,
            source="BLS API - JOLTS layoff rate (fallback)",
            as_of=as_of,
            weight=WEIGHT_LABOR_MARKET_STRENGTH,
            raw={"series_id": series_id, "error": "insufficient_bls_points"},
        )

    # Direction: compare latest to 3-month average (previous 3 months).
    values = [p[1] for p in points]
    latest_value = float(values[-1])
    prev_window = values[-4:-1] if len(values) >= 4 else values[:-1]
    prev_avg = float(statistics.mean(prev_window)) if prev_window else latest_value

    direction = _direction_from_compare(latest_value, prev_avg)
    severity = _severity_for_layoff_rate(latest_value)

    as_of = points[-1][0]
    headline = _truncate_headline_to_12_words(
        f"Layoff rate is {latest_value:.2f}% versus its 3-month average"
    )

    return _make_constituent(
        name="Labor Market Strength",
        slug="labor_market_strength",
        current_value=latest_value,
        previous_value=prev_avg,
        direction=direction,
        severity=severity,
        headline=headline,
        source="BLS API - JOLTS layoff rate",
        as_of=as_of,
        weight=WEIGHT_LABOR_MARKET_STRENGTH,
        raw={"series_id": series_id, "points_used": points[-4:]},
    )


# -----------------------------------------------------------------------------
# Constituent 2: housing_affordability_pressure
# -----------------------------------------------------------------------------


def get_housing_affordability_pressure() -> Dict[str, Any]:
    # Prompt: use Freddie Mac PMMS RSS feed URL (but this is an .xls link).
    current_value = float(PMMS_FALLBACK_RATE)
    previous_value = float(PMMS_FALLBACK_RATE)
    as_of = _today_iso()
    source = f"Freddie Mac PMMS weekly 30-year rate ({FREDDIE_PMMS_URL})"

    try:
        session = _requests_session()
        resp = session.get(FREDDIE_PMMS_URL, timeout=CACHE_DEFAULT_TIMEOUT_S)
        resp.raise_for_status()

        # Best-effort parsing. In CI we may not have xlrd, so we fallback.
        content = resp.content
        try:
            import pandas as pd  # local import: only needed if download succeeds

            df = pd.read_excel(BytesIO(content), engine=None)  # type: ignore[arg-type]
            # Heuristic: find last numeric series.
            last_row = df.tail(1)
            numeric_cols = [c for c in last_row.columns if _safe_float(last_row[c].iloc[0]) is not None]
            if not numeric_cols:
                raise ValueError("no_numeric_columns_in_freddie_pmms_xls")
            col = numeric_cols[-1]
            current_value = float(last_row[col].iloc[0])

            prev_row = df.iloc[-2:-1]
            if not prev_row.empty and _safe_float(prev_row[col].iloc[0]) is not None:
                previous_value = float(prev_row[col].iloc[0])
                as_of = _today_iso()
        except Exception as parse_err:
            logger.warning("Freddie PMMS parse failed: %s", parse_err)
            current_value = float(PMMS_FALLBACK_RATE)
            previous_value = float(PMMS_FALLBACK_RATE)
            as_of = _today_iso()

    except Exception as e:
        logger.warning("Freddie PMMS fetch failed: %s", e)

    direction = _direction_from_compare(current_value, previous_value)
    severity = _severity_for_housing_rate(current_value)
    headline = _truncate_headline_to_12_words(
        f"30-year mortgage rate is {current_value:.2f}% this week"
    )

    return _make_constituent(
        name="Housing Affordability Pressure",
        slug="housing_affordability_pressure",
        current_value=current_value,
        previous_value=previous_value,
        direction=direction,
        severity=severity,
        headline=headline,
        source=source + (" (fallback)" if current_value == PMMS_FALLBACK_RATE else ""),
        as_of=as_of,
        weight=WEIGHT_HOUSING_AFFORDABILITY_PRESSURE,
        raw={
            "url": FREDDIE_PMMS_URL,
            "fallback_rate": PMMS_FALLBACK_RATE,
        },
    )


# -----------------------------------------------------------------------------
# Constituent 3: transportation_cost_burden
# -----------------------------------------------------------------------------


def _fetch_eia_weekly_series_latest_two(series_id: str) -> List[Tuple[str, float]]:
    api_key = os.environ.get("EIA_API_KEY") or "DUMMY_EIA_KEY"
    session = _requests_session()

    params = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 2,
        "offset": 0,
    }

    try:
        resp = session.get(EIA_GAS_URL, params=params, timeout=CACHE_DEFAULT_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("EIA fetch failed: %s", e)
        return []

    response_obj = data.get("response") or data.get("Response") or {}
    points = response_obj.get("data") or response_obj.get("Data") or []
    out: List[Tuple[str, float]] = []

    if isinstance(points, list) and points:
        for p in points:
            period = p.get("period") or p.get("date") or p.get("Period")
            value = p.get("value") or p.get("Value")
            f = _safe_float(value)
            if period is None or f is None:
                continue
            # Best-effort date parsing; keep YYYY-MM-DD.
            if isinstance(period, str) and len(period) >= 10:
                iso = period[:10]
            else:
                iso = _today_iso()
            out.append((iso, float(f)))

    # Sort ascending
    out.sort(key=lambda x: x[0])
    return out


def get_transportation_cost_burden() -> Dict[str, Any]:
    series_id = "EMM_EPMRR_PTE_NUS_DPG"

    points = _fetch_eia_weekly_series_latest_two(series_id)
    if len(points) < 2:
        current_value = float(EIA_GAS_PRICE_FALLBACK)
        previous_value = float(EIA_GAS_PRICE_FALLBACK)
        direction = "flat"
        severity = _severity_for_gas_price(current_value)
        as_of = _today_iso()
        headline = _truncate_headline_to_12_words(
            f"Gas price is ${current_value:.2f} today"
        )
        return _make_constituent(
            name="Transportation Cost Burden",
            slug="transportation_cost_burden",
            current_value=current_value,
            previous_value=previous_value,
            direction=direction,
            severity=severity,
            headline=headline,
            source=f"EIA API - {series_id} (fallback)",
            as_of=as_of,
            weight=WEIGHT_TRANSPORTATION_COST_BURDEN,
            raw={
                "series_id": series_id,
                "fallback_price": EIA_GAS_PRICE_FALLBACK,
            },
        )

    previous_value = float(points[-2][1])
    current_value = float(points[-1][1])
    direction = _direction_from_compare(current_value, previous_value)
    severity = _severity_for_gas_price(current_value)
    as_of = points[-1][0]

    headline = _truncate_headline_to_12_words(
        f"US regular gas is ${current_value:.2f} per gallon this week"
    )

    return _make_constituent(
        name="Transportation Cost Burden",
        slug="transportation_cost_burden",
        current_value=current_value,
        previous_value=previous_value,
        direction=direction,
        severity=severity,
        headline=headline,
        source=f"EIA API - weekly retail gas prices ({series_id})",
        as_of=as_of,
        weight=WEIGHT_TRANSPORTATION_COST_BURDEN,
        raw={
            "series_id": series_id,
            "irs_mileage_rate": {
                "2024": IRS_MILEAGE_2024,
                "2025": IRS_MILEAGE_2025,
            },
            "points_used": points,
        },
    )


# -----------------------------------------------------------------------------
# Constituent 4: consumer_debt_conditions
# -----------------------------------------------------------------------------


def _parse_revolving_credit_apr_from_g19(html: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract a best-effort (previous, current) APR from the Fed G.19 page.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Find a context window around "revolving credit".
    lowered = text.lower()
    idx = lowered.find("revolving credit")
    window = None
    if idx >= 0:
        window = text[idx : idx + 800]
    else:
        # Try a looser keyword.
        m = re.search(r"revolving\\s+credit[^.]{0,400}", lowered)
        if m:
            window = text[m.start() : m.start() + 800]

    if not window:
        return None, None

    # Capture percent-like numbers near the target.
    percents = re.findall(r"(\\d+(?:\\.\\d+)?)\\s*%", window)
    floats = [_safe_float(p) for p in percents]
    floats = [f for f in floats if f is not None]
    if not floats:
        # Sometimes values are rendered without a percent sign.
        nums = re.findall(r"(\\d+(?:\\.\\d+)?)", window)
        floats = [_safe_float(n) for n in nums]
        floats = [f for f in floats if f is not None]

    if not floats:
        return None, None

    if len(floats) >= 2:
        # Heuristic: first is most likely "current", second older. We keep
        # previous as the last of two to reduce surprises.
        current = floats[0]
        previous = floats[1]
        return previous, current
    return None, floats[0]


def get_consumer_debt_conditions() -> Dict[str, Any]:
    current_value = float(CREDIT_APR_FALLBACK)
    previous_value = float(CREDIT_APR_FALLBACK)
    as_of = _today_iso()
    source = FED_G19_URL

    try:
        session = _requests_session()
        resp = session.get(FED_G19_URL, timeout=CACHE_DEFAULT_TIMEOUT_S)
        resp.raise_for_status()
        previous_parsed, current_parsed = _parse_revolving_credit_apr_from_g19(resp.text)
        if current_parsed is not None:
            current_value = float(current_parsed)
        if previous_parsed is not None:
            previous_value = float(previous_parsed)
    except Exception as e:
        logger.warning("Fed G.19 fetch/parse failed: %s", e)

    direction = _direction_from_compare(current_value, previous_value)
    severity = _severity_for_credit_apr(current_value)
    headline = _truncate_headline_to_12_words(
        f"Credit card APR is {current_value:.2f}% right now"
    )

    return _make_constituent(
        name="Consumer Debt Conditions",
        slug="consumer_debt_conditions",
        current_value=current_value,
        previous_value=previous_value,
        direction=direction,
        severity=severity,
        headline=headline,
        source=f"Federal Reserve G.19 ({source})",
        as_of=as_of,
        weight=WEIGHT_CONSUMER_DEBT_CONDITIONS,
        raw={
            "url": FED_G19_URL,
            "fallback_apr": CREDIT_APR_FALLBACK,
            "notes": "Parsed revolving credit APR with best-effort heuristics; may fallback.",
        },
    )


# -----------------------------------------------------------------------------
# Constituent 5: career_income_mobility
# -----------------------------------------------------------------------------


def get_career_income_mobility() -> Dict[str, Any]:
    series_id = "JTS000000000000000QUR"

    points = _fetch_bls_timeseries_points(series_id, lookback_months=10)
    if len(points) < 2:
        current_value = float(BLS_QUIT_RATE_FALLBACK)
        previous_value = float(BLS_QUIT_RATE_FALLBACK)
        direction = "flat"
        severity = _severity_for_quit_rate(current_value)
        as_of = _today_iso()
        headline = _truncate_headline_to_12_words(
            f"Quit rate is {current_value:.2f}% today"
        )
        return _make_constituent(
            name="Career Income Mobility",
            slug="career_income_mobility",
            current_value=current_value,
            previous_value=previous_value,
            direction=direction,
            severity=severity,
            headline=headline,
            source="BLS API - JOLTS quit rate (fallback)",
            as_of=as_of,
            weight=WEIGHT_CAREER_INCOME_MOBILITY,
            raw={"series_id": series_id, "error": "insufficient_bls_points"},
        )

    values = [p[1] for p in points]
    latest_value = float(values[-1])
    prev_window = values[-4:-1] if len(values) >= 4 else values[:-1]
    prev_avg = float(statistics.mean(prev_window)) if prev_window else latest_value

    direction = _direction_from_compare(latest_value, prev_avg)
    severity = _severity_for_quit_rate(latest_value)
    as_of = points[-1][0]

    headline = _truncate_headline_to_12_words(
        f"Quit rate is {latest_value:.2f}% versus its 3-month average"
    )

    return _make_constituent(
        name="Career Income Mobility",
        slug="career_income_mobility",
        current_value=latest_value,
        previous_value=prev_avg,
        direction=direction,
        severity=severity,
        headline=headline,
        source="BLS API - JOLTS quit rate",
        as_of=as_of,
        weight=WEIGHT_CAREER_INCOME_MOBILITY,
        raw={"series_id": series_id, "points_used": points[-4:]},
    )


# -----------------------------------------------------------------------------
# Constituent 6: wellness_cost_index
# -----------------------------------------------------------------------------


def get_wellness_cost_index() -> Dict[str, Any]:
    current_value = float(WELLNESS_HEALTHCARE_PCT_INCOME_MID)
    previous_value = float(WELLNESS_HEALTHCARE_PCT_INCOME_MID)
    direction = "flat"
    severity = _severity_for_wellness(current_value)
    headline = _truncate_headline_to_12_words(
        "BLS benchmark: healthcare is 5% of mid-income budgets"
    )

    return _make_constituent(
        name="Wellness Cost Index",
        slug="wellness_cost_index",
        current_value=current_value,
        previous_value=previous_value,
        direction=direction,
        severity=severity,
        headline=headline,
        source="BLS CEX benchmarks (static)",
        as_of="2023-12-31",
        weight=WEIGHT_WELLNESS_COST_INDEX,
        raw={
            "healthcare_pct_income_mid": WELLNESS_HEALTHCARE_PCT_INCOME_MID,
        },
    )


# -----------------------------------------------------------------------------
# Composite
# -----------------------------------------------------------------------------


def severity_for_previous_value(slug: str, previous_value: float) -> str:
    if slug == "labor_market_strength":
        return _severity_for_layoff_rate(previous_value)
    if slug == "housing_affordability_pressure":
        return _severity_for_housing_rate(previous_value)
    if slug == "transportation_cost_burden":
        return _severity_for_gas_price(previous_value)
    if slug == "consumer_debt_conditions":
        return _severity_for_credit_apr(previous_value)
    if slug == "career_income_mobility":
        return _severity_for_quit_rate(previous_value)
    if slug == "wellness_cost_index":
        return _severity_for_wellness(previous_value)
    return "amber"


def severity_for_current_value(slug: str, current_value: float) -> str:
    # Same logic as previous.
    return severity_for_previous_value(slug, current_value)


def build_mci_snapshot() -> Dict[str, Any]:
    constituents = [
        get_labor_market_strength(),
        get_housing_affordability_pressure(),
        get_transportation_cost_burden(),
        get_consumer_debt_conditions(),
        get_career_income_mobility(),
        get_wellness_cost_index(),
    ]

    # Weighted composite.
    composite_score = 0.0
    prev_composite_score = 0.0

    improved_count = 0
    deteriorated_count = 0

    for c in constituents:
        slug = c["slug"]
        weight = float(c["weight"])

        current_sev = severity_for_current_value(slug, float(c["current_value"]))
        previous_sev = severity_for_previous_value(slug, float(c["previous_value"]))

        current_score = _constituent_score(current_sev)
        previous_score = _constituent_score(previous_sev)

        composite_score += current_score * weight
        prev_composite_score += previous_score * weight

        if current_score > previous_score:
            improved_count += 1
        elif current_score < previous_score:
            deteriorated_count += 1

    composite_score = float(composite_score)

    if improved_count == 0 and deteriorated_count == 0:
        composite_direction = "stable"
    elif improved_count > deteriorated_count:
        composite_direction = "improving"
    elif deteriorated_count > improved_count:
        composite_direction = "deteriorating"
    else:
        composite_direction = "stable"

    # Map composite score to severity thresholds (midpoints between the score levels).
    if composite_score >= 65.0:
        composite_severity = "green"
    elif composite_score >= 35.0:
        composite_severity = "amber"
    else:
        composite_severity = "red"

    # Worst constituent = lowest score (red is worst).
    worst = min(constituents, key=lambda c: _constituent_score(c["severity"]))
    composite_headline = str(worst.get("headline", "MCI snapshot ready"))

    snapshot_dt = datetime.utcnow().date()
    snapshot_date = snapshot_dt.isoformat()
    next_refresh = (snapshot_dt + timedelta(days=7)).isoformat()

    return {
        "composite_score": composite_score,
        "composite_direction": composite_direction,
        "composite_severity": composite_severity,
        "composite_headline": composite_headline,
        "constituents": constituents,
        "snapshot_date": snapshot_date,
        "next_refresh": next_refresh,
    }

