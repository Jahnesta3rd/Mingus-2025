#!/usr/bin/env python3
"""
Market conditions service (#165) — national, regional, and personal layers.

National/regional indicators are cached in market_data_cache with TTL.
Personal income percentile uses seeded oes_wage_data (no live BLS OES API).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from backend.utils.user_profile_context import (
    extract_zip_from_text,
    resolve_current_salary,
    resolve_user_zip_code,
)
from backend.data.oes_wage_data_2024 import MSA_META
from backend.data.zip_to_msa import ZIP_TO_MSA, MSA_DISPLAY_NAMES
from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.housing_profile import HousingProfile
from backend.models.market_conditions_models import MarketDataCache, OesWageData
from backend.models.user_models import User
from backend.services.mci_service import (
    BLS_LAYOFF_RATE_FALLBACK,
    FRED_MORTGAGE_SERIES,
    PMMS_FALLBACK_RATE,
    _fetch_bls_timeseries_points,
    _fetch_fred_series_latest,
    _today_iso,
)

logger = logging.getLogger(__name__)

BLS_LAYOFF_SERIES = "JTS000000000000000LDR"
BLS_CPI_SERIES = "CUSR0000SA0"

NATIONAL_TTL = timedelta(hours=24)
REGIONAL_TTL = timedelta(hours=24)
PERSONAL_TTL = timedelta(days=7)

MSA_FRED_UNEMPLOYMENT: dict[str, str] = {
    "12060": "ATLA013URN",
    "47900": "WASH911URN",
    "26420": "HOUS448URN",
    "19100": "DALL148URN",
    "35620": "NEWY636URN",
    "16980": "CHIC917URN",
    "31080": "LOSA706URN",
    "41860": "SANF806URN",
    "38060": "PHOE004URN",
    "14460": "BOST115URN",
    "33100": "MIAM112URN",
    "42660": "SEAT653URN",
    "19740": "DENV708URN",
    "37980": "PHIL148URN",
    "41740": "SAND706URN",
}

MSA_STHPI_PREFIX: dict[str, str] = {
    "12060": "ATL",
    "47900": "WAS",
    "26420": "HOU",
    "19100": "DAL",
    "35620": "NYC",
    "16980": "CHI",
}

MSA_STATE_FALLBACK: dict[str, str] = {
    "12060": "GAURN",
    "47900": "DCURN",
    "26420": "TXURN",
    "19100": "TXURN",
    "35620": "NYURN",
    "16980": "ILURN",
    "31080": "CAURN",
    "41860": "CAURN",
    "38060": "AZURN",
    "14460": "MAURN",
    "33100": "FLURN",
    "42660": "WAURN",
    "19740": "COURN",
    "37980": "PAURN",
    "41740": "CAURN",
}

# Field-level wage growth YoY fallback when Atlanta Fed series unavailable.
FIELD_WAGE_GROWTH_YOY: dict[str, float] = {
    "Technology": 4.2,
    "Healthcare (Clinical)": 3.8,
    "Healthcare (Admin/Ops)": 3.5,
    "Finance & Accounting": 3.6,
    "Legal": 3.2,
    "Marketing & Communications": 3.4,
    "Sales": 3.0,
    "Education & Training": 2.8,
    "Engineering (Civil/Mech/Ind)": 3.9,
    "Creative & Design": 3.1,
    "Operations & Supply Chain": 3.5,
    "Human Resources": 3.3,
    "Real Estate": 3.0,
    "Government & Public Policy": 2.9,
    "Hospitality & Food Service": 4.5,
    "Retail & Consumer": 3.2,
    "Construction & Trades": 4.0,
    "Media & Journalism": 2.7,
    "Science & Research": 3.6,
    "Military / Veterans": 3.0,
}
DEFAULT_WAGE_GROWTH_YOY = 3.5


def resolve_user_msa(user: User) -> tuple[str | None, str | None]:
    """
    Resolve CBSA code and display name from profile zip sources.

    Order: housing_profile.zip_or_city → user_profiles.zip_code (via helper).
    """
    hp = HousingProfile.query.filter_by(user_id=user.id).first()
    zip_code = extract_zip_from_text(hp.zip_or_city if hp else None)
    if not zip_code:
        zip_code = resolve_user_zip_code(user)

    msa_code = ZIP_TO_MSA.get(zip_code) if zip_code else None

    # City-name text fallback if zip lookup failed
    if not msa_code and zip_code is None:
        raw_text = (hp.zip_or_city if hp else None) or ''
        if raw_text:
            normalized = raw_text.strip().lower()
            for code, display in MSA_DISPLAY_NAMES.items():
                city = display.split(',')[0].lower()
                if city in normalized:
                    msa_code = code
                    break

    if not msa_code:
        return None, None

    msa_name = MSA_DISPLAY_NAMES.get(msa_code) or MSA_META.get(msa_code)
    if not msa_name:
        from backend.scripts.job_postings_seed_data import MSA_CONFIG

        meta = MSA_CONFIG.get(msa_code, {})
        city = meta.get("city", "")
        state = meta.get("state", "")
        msa_name = f"{city}, {state}" if city else msa_code

    return msa_code, msa_name


def _read_cache(key: str) -> tuple[dict | None, datetime | None]:
    try:
        row = MarketDataCache.query.filter_by(key=key).first()
        if row:
            return dict(row.value), row.fetched_at
    except Exception as exc:
        logger.warning("market_data_cache read failed for %s: %s", key, exc)
    return None, None


def _write_cache(key: str, value: dict) -> None:
    try:
        row = MarketDataCache.query.filter_by(key=key).first()
        now = datetime.utcnow()
        if row:
            row.value = value
            row.fetched_at = now
        else:
            db.session.add(MarketDataCache(key=key, value=value, fetched_at=now))
        db.session.commit()
    except Exception as exc:
        logger.warning("market_data_cache write failed for %s: %s", key, exc)
        db.session.rollback()


def _cached_fetch(
    key: str,
    ttl: timedelta,
    fetch_fn,
) -> tuple[dict, bool]:
    """
    Return (payload, stale_flag).
    On fetch failure returns last cached value with stale=True.
    """
    cached, fetched_at = _read_cache(key)
    fresh = (
        cached is not None
        and fetched_at is not None
        and datetime.utcnow() - fetched_at < ttl
    )
    if fresh:
        return cached, False

    try:
        payload = fetch_fn()
        if payload:
            _write_cache(key, payload)
            return payload, False
    except Exception as exc:
        logger.warning("Live fetch failed for %s: %s", key, exc)

    if cached:
        return cached, True

    try:
        payload = fetch_fn(fallback_only=True)
    except TypeError:
        payload = fetch_fn()
    return payload or {}, True


def _fetch_layoff_rate(*, fallback_only: bool = False) -> dict:
    if fallback_only:
        rate = float(BLS_LAYOFF_RATE_FALLBACK)
        return {
            "layoff_rate": rate,
            "layoff_rate_label": f"{rate:.1f}% monthly layoff rate",
            "data_date": _today_iso(),
        }

    points = _fetch_bls_timeseries_points(BLS_LAYOFF_SERIES, lookback_months=6)
    if points:
        rate = float(points[-1][1])
        as_of = points[-1][0]
    else:
        rate = float(BLS_LAYOFF_RATE_FALLBACK)
        as_of = _today_iso()

    return {
        "layoff_rate": round(rate, 2),
        "layoff_rate_label": f"{rate:.1f}% monthly layoff rate",
        "data_date": as_of,
    }


def _fetch_mortgage_rate(*, fallback_only: bool = False) -> dict:
    if fallback_only:
        rate = float(PMMS_FALLBACK_RATE)
        return {
            "mortgage_rate": rate,
            "mortgage_rate_label": f"{rate:.2f}% 30-year fixed",
            "data_date": _today_iso(),
        }

    points = _fetch_fred_series_latest(FRED_MORTGAGE_SERIES, limit=1)
    if points:
        rate = float(points[-1][1])
        as_of = points[-1][0]
    else:
        rate = float(PMMS_FALLBACK_RATE)
        as_of = _today_iso()

    return {
        "mortgage_rate": round(rate, 2),
        "mortgage_rate_label": f"{rate:.2f}% 30-year fixed",
        "data_date": as_of,
    }


def _fetch_cpi_yoy(*, fallback_only: bool = False) -> dict:
    fallback_yoy = 3.1
    if fallback_only:
        return {
            "cpi_yoy": fallback_yoy,
            "cpi_label": f"{fallback_yoy:.1f}% year-over-year",
            "data_date": _today_iso(),
        }

    points = _fetch_bls_timeseries_points(BLS_CPI_SERIES, lookback_months=14)
    if len(points) >= 13:
        latest_val = points[-1][1]
        year_ago_val = points[-13][1]
        if year_ago_val:
            yoy = ((latest_val - year_ago_val) / year_ago_val) * 100.0
            as_of = points[-1][0]
            return {
                "cpi_yoy": round(yoy, 1),
                "cpi_label": f"{yoy:.1f}% year-over-year",
                "data_date": as_of,
            }

    return {
        "cpi_yoy": fallback_yoy,
        "cpi_label": f"{fallback_yoy:.1f}% year-over-year",
        "data_date": _today_iso(),
    }


def _fetch_national_layer() -> tuple[dict, bool]:
    stale_flags: list[bool] = []

    layoff, s1 = _cached_fetch("national:jolts", NATIONAL_TTL, _fetch_layoff_rate)
    stale_flags.append(s1)
    mortgage, s2 = _cached_fetch("national:mortgage", NATIONAL_TTL, _fetch_mortgage_rate)
    stale_flags.append(s2)
    cpi, s3 = _cached_fetch("national:cpi", NATIONAL_TTL, _fetch_cpi_yoy)
    stale_flags.append(s3)

    dates = [layoff.get("data_date"), mortgage.get("data_date"), cpi.get("data_date")]
    data_date = max(d for d in dates if d) if any(dates) else _today_iso()

    national = {
        "layoff_rate": layoff.get("layoff_rate", BLS_LAYOFF_RATE_FALLBACK),
        "layoff_rate_label": layoff.get("layoff_rate_label", ""),
        "mortgage_rate": mortgage.get("mortgage_rate", PMMS_FALLBACK_RATE),
        "mortgage_rate_label": mortgage.get("mortgage_rate_label", ""),
        "cpi_yoy": cpi.get("cpi_yoy", 3.1),
        "cpi_label": cpi.get("cpi_label", ""),
        "data_date": data_date,
    }
    return national, any(stale_flags)


def _fetch_regional_unemployment(msa_code: str, *, fallback_only: bool = False) -> dict:
    series_id = MSA_FRED_UNEMPLOYMENT.get(msa_code)
    state_series = MSA_STATE_FALLBACK.get(msa_code)

    if fallback_only or not series_id:
        return {"unemployment_rate": None, "data_date": _today_iso()}

    points = _fetch_fred_series_latest(series_id, limit=1)
    if not points and state_series:
        points = _fetch_fred_series_latest(state_series, limit=1)

    if points:
        return {
            "unemployment_rate": round(float(points[-1][1]), 1),
            "data_date": points[-1][0],
        }
    return {"unemployment_rate": None, "data_date": _today_iso()}


def _fetch_regional_hpi(msa_code: str, *, fallback_only: bool = False) -> dict:
    if fallback_only:
        return {"housing_price_index": None, "data_date": _today_iso()}

    series_attempts = [f"ATNHPIUS{msa_code}Q"]
    sthpi_prefix = MSA_STHPI_PREFIX.get(msa_code)
    if sthpi_prefix:
        series_attempts.append(f"{sthpi_prefix}STHPI")

    for series_id in series_attempts:
        points = _fetch_fred_series_latest(series_id, limit=1)
        if points:
            return {
                "housing_price_index": round(float(points[-1][1]), 1),
                "data_date": points[-1][0],
            }

    return {"housing_price_index": None, "data_date": _today_iso()}


def _fetch_regional_layer(msa_code: str, msa_name: str) -> tuple[dict | None, bool]:
    unemp_key = f"regional:{msa_code}:unemployment"
    hpi_key = f"regional:{msa_code}:hpi:v2"

    unemp, s1 = _cached_fetch(
        unemp_key,
        REGIONAL_TTL,
        lambda fallback_only=False: _fetch_regional_unemployment(msa_code, fallback_only=fallback_only),
    )
    hpi, s2 = _cached_fetch(
        hpi_key,
        REGIONAL_TTL,
        lambda fallback_only=False: _fetch_regional_hpi(msa_code, fallback_only=fallback_only),
    )

    dates = [unemp.get("data_date"), hpi.get("data_date")]
    data_date = max(d for d in dates if d) if any(dates) else _today_iso()

    regional = {
        "msa_name": msa_name,
        "unemployment_rate": unemp.get("unemployment_rate"),
        "housing_price_index": hpi.get("housing_price_index"),
        "data_date": data_date,
    }
    return regional, any([s1, s2])


def compute_percentile(
    salary: int,
    pct_10: int,
    pct_25: int,
    pct_50: int,
    pct_75: int,
    pct_90: int,
) -> int:
    """Interpolate an integer percentile (1–99) from OES wage bands."""
    bands = [(10, pct_10), (25, pct_25), (50, pct_50), (75, pct_75), (90, pct_90)]
    salary_f = float(salary)

    if salary_f <= pct_10:
        if pct_10 <= 0:
            return 1
        return max(1, min(10, int(round((salary_f / pct_10) * 10))))

    if salary_f >= pct_90:
        if pct_90 <= 0:
            return 99
        excess = salary_f - pct_90
        span = max(pct_90 * 0.25, 1.0)
        return min(99, 90 + int(round((excess / span) * 9)))

    prev_pct, prev_wage = 10, float(pct_10)
    for pct, wage in bands[1:]:
        if salary_f <= wage:
            if wage <= prev_wage:
                return pct
            frac = (salary_f - prev_wage) / (wage - prev_wage)
            return max(prev_pct, min(pct, int(round(prev_pct + frac * (pct - prev_pct)))))
        prev_pct, prev_wage = pct, float(wage)

    return 90


def _lookup_oes_row(bls_career_field: str, msa_code: str) -> OesWageData | None:
    cache_key = f"personal:oes:{bls_career_field}:{msa_code}"
    cached, fetched_at = _read_cache(cache_key)
    if cached and fetched_at and datetime.utcnow() - fetched_at < PERSONAL_TTL:
        return _oes_from_cache_dict(cached)

    row = (
        OesWageData.query.filter_by(
            bls_career_field=bls_career_field,
            msa_code=msa_code,
        ).first()
    )
    if row:
        _write_cache(
            cache_key,
            {
                "bls_career_field": row.bls_career_field,
                "msa_code": row.msa_code,
                "msa_name": row.msa_name,
                "pct_10": row.pct_10,
                "pct_25": row.pct_25,
                "pct_50": row.pct_50,
                "pct_75": row.pct_75,
                "pct_90": row.pct_90,
                "source_year": row.source_year,
            },
        )
    return row


def _oes_from_cache_dict(data: dict) -> OesWageData:
    row = OesWageData()
    row.bls_career_field = data["bls_career_field"]
    row.msa_code = data["msa_code"]
    row.msa_name = data["msa_name"]
    row.pct_10 = data["pct_10"]
    row.pct_25 = data["pct_25"]
    row.pct_50 = data["pct_50"]
    row.pct_75 = data["pct_75"]
    row.pct_90 = data["pct_90"]
    row.source_year = data["source_year"]
    return row


def _wage_growth_yoy(bls_career_field: str) -> float:
    return FIELD_WAGE_GROWTH_YOY.get(bls_career_field, DEFAULT_WAGE_GROWTH_YOY)


def _build_personal_layer(
    user: User,
    cp: CareerProfile | None,
    msa_code: str | None,
    msa_name: str | None,
) -> tuple[dict | None, str | None]:
    if not cp or not cp.bls_career_field:
        return None, None

    current_salary = resolve_current_salary(user, cp)
    if current_salary is None or current_salary <= 0:
        return None, None

    lookup_msa = msa_code if msa_code else "00000"
    oes = _lookup_oes_row(cp.bls_career_field, lookup_msa)
    if not oes and lookup_msa != "00000":
        oes = _lookup_oes_row(cp.bls_career_field, "00000")

    if not oes:
        return None, None

    display_msa = msa_name if msa_code else "National"
    percentile = compute_percentile(
        current_salary,
        oes.pct_10,
        oes.pct_25,
        oes.pct_50,
        oes.pct_75,
        oes.pct_90,
    )

    personal = {
        "percentile": percentile,
        "current_salary": current_salary,
        "pct_10": oes.pct_10,
        "pct_25": oes.pct_25,
        "pct_50": oes.pct_50,
        "pct_75": oes.pct_75,
        "pct_90": oes.pct_90,
        "field_label": cp.bls_career_field,
        "msa_name": display_msa,
        "wage_growth_yoy": _wage_growth_yoy(cp.bls_career_field),
        "source_year": oes.source_year,
        "above_median": current_salary >= oes.pct_50,
    }
    note = f"Based on {oes.source_year} BLS data"
    return personal, note


def get_market_conditions(user: User) -> dict:
    """Build full market conditions payload for an authenticated user."""
    national, national_stale = _fetch_national_layer()

    msa_code, msa_name = resolve_user_msa(user)
    regional = None
    regional_stale = False
    if msa_code and msa_name:
        regional, regional_stale = _fetch_regional_layer(msa_code, msa_name)

    cp = CareerProfile.query.filter_by(user_id=user.id).first()
    personal, personal_note = _build_personal_layer(user, cp, msa_code, msa_name)

    return {
        "national": national,
        "regional": regional,
        "personal": personal,
        "meta": {
            "national_stale": national_stale,
            "regional_stale": regional_stale,
            "personal_note": personal_note,
        },
    }
