#!/usr/bin/env python3
"""
BLS OES (Occupational Employment and Wage Statistics) service.
Fetches national wage percentiles by occupation.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from backend.services.mci_service import (
    BLS_TIMESERIES_URL,
    CACHE_DEFAULT_TIMEOUT_S,
    _bls_period_to_iso_date,
    _requests_session,
    _safe_float,
    _today_iso,
)

logger = logging.getLogger(__name__)

BLS_CAREER_FIELD_TO_SOC = {
    'Technology': '151299',       # Software/IT misc
    'Healthcare': '291299',       # Healthcare practitioners misc
    'Finance': '132099',          # Financial specialists misc
    'Education': '250000',        # Education occupations
    'Legal': '231011',            # Lawyers
    'Engineering': '172199',      # Engineers misc
    'Sales': '419099',            # Sales misc
    'Management': '119199',       # Managers misc
    'Creative': '271099',         # Arts/design misc
    'Other': '000000',            # All occupations
}

NATIONAL_MEDIAN_FALLBACK = {
    'Technology': 104900,
    'Healthcare': 77760,
    'Finance': 76570,
    'Education': 61730,
    'Legal': 127990,
    'Engineering': 96350,
    'Sales': 48340,
    'Management': 107360,
    'Creative': 53780,
    'Other': 61900,
}

# BLS OEWS annual wage percentile datatype codes (25-char OEUN… series IDs).
_PERCENTILE_DATA_TYPES = {
    'p10': 11,
    'p25': 12,
    'p50': 13,
    'p75': 14,
    'p90': 15,
}

_FALLBACK_PERCENTILE_RATIOS = {
    'p10': 0.50,
    'p25': 0.65,
    'p50': 1.0,
    'p75': 1.30,
    'p90': 1.66,
}

_CACHE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'cache', 'bls_oes_percentiles.json'
)
_CACHE_TTL_DAYS = 7


def _normalize_career_field(bls_career_field: str) -> str:
    field = (bls_career_field or '').strip()
    if field in BLS_CAREER_FIELD_TO_SOC:
        return field
    for key in BLS_CAREER_FIELD_TO_SOC:
        if key.lower() == field.lower():
            return key
    return 'Other'


def _build_oes_series_id(soc_code: str, data_type: int) -> str:
    """Build a 25-char OEWS national series ID (OE + U + N + area + industry + occ + dtype)."""
    occupation = str(soc_code).zfill(6)[-6:]
    return f'OEUN{"0" * 7}{"000000"}{occupation}{int(data_type):02d}'


def _fetch_oes_timeseries_points(series_id: str) -> list[tuple[str, float]]:
    """
    Fetch latest OEWS annual wage points for a series.

    OEWS annual series return empty data when startyear/endyear are supplied;
    omit the year range and use the API default window instead.
    """
    session = _requests_session()
    payload = {
        'seriesid': [series_id],
        'registrationkey': '',
    }

    try:
        resp = session.post(BLS_TIMESERIES_URL, json=payload, timeout=CACHE_DEFAULT_TIMEOUT_S)
        resp.raise_for_status()
        payload_json = resp.json()
    except Exception as exc:
        logger.warning('BLS OES fetch failed for %s: %s', series_id, exc)
        return []

    results = payload_json.get('Results') or payload_json.get('results') or {}
    series_list = results.get('series') or results.get('SERIES') or []
    if not series_list:
        return []

    data_points = series_list[0].get('data') or series_list[0].get('DATA') or []
    out: list[tuple[str, float]] = []
    for point in data_points:
        year = point.get('year') or point.get('Year')
        period = point.get('period') or point.get('Period')
        value = point.get('value') or point.get('Value')
        if year is None or period is None or value is None:
            continue
        parsed_value = _safe_float(value)
        if parsed_value is None:
            continue
        try:
            iso = _bls_period_to_iso_date(int(year), str(period))
        except Exception:
            iso = _today_iso()
        out.append((iso, parsed_value))

    out.sort(key=lambda item: item[0])
    return out


def _percentiles_from_median(median: int, source: str, as_of: str) -> Dict[str, Any]:
    percentiles = {
        key: int(round(median * ratio))
        for key, ratio in _FALLBACK_PERCENTILE_RATIOS.items()
    }
    return {
        **percentiles,
        'as_of': as_of,
        'source': source,
    }


def _fallback_percentiles(bls_career_field: str) -> Dict[str, Any]:
    field = _normalize_career_field(bls_career_field)
    median = NATIONAL_MEDIAN_FALLBACK.get(field, NATIONAL_MEDIAN_FALLBACK['Other'])
    return _percentiles_from_median(
        median,
        source='BLS OES national (fallback median)',
        as_of=_today_iso(),
    )


def _read_cache(career_field: str) -> Optional[Dict[str, Any]]:
    try:
        with open(_CACHE_PATH, 'r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return None
    except Exception as exc:
        logger.warning('BLS OES cache read failed: %s', exc)
        return None

    entries = payload.get('entries') if isinstance(payload, dict) else None
    if not isinstance(entries, dict):
        return None

    entry = entries.get(career_field)
    if not isinstance(entry, dict):
        return None

    cached_at = entry.get('cached_at')
    data = entry.get('data')
    if not cached_at or not isinstance(data, dict):
        return None

    try:
        cached_dt = datetime.fromisoformat(str(cached_at))
    except ValueError:
        return None

    if datetime.utcnow() - cached_dt > timedelta(days=_CACHE_TTL_DAYS):
        return None

    return data


def _write_cache(career_field: str, data: Dict[str, Any]) -> None:
    try:
        cache_dir = os.path.dirname(_CACHE_PATH)
        os.makedirs(cache_dir, exist_ok=True)

        try:
            with open(_CACHE_PATH, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            payload = {'entries': {}}
        except Exception:
            payload = {'entries': {}}

        if not isinstance(payload, dict):
            payload = {'entries': {}}
        entries = payload.setdefault('entries', {})
        if not isinstance(entries, dict):
            entries = {}
            payload['entries'] = entries

        entries[career_field] = {
            'cached_at': datetime.utcnow().isoformat(),
            'data': data,
        }

        with open(_CACHE_PATH, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False)
    except Exception as exc:
        logger.warning('BLS OES cache write failed: %s', exc)


def _latest_point_value(series_id: str) -> tuple[Optional[float], Optional[str]]:
    points = _fetch_oes_timeseries_points(series_id)
    if not points:
        return None, None
    as_of, value = points[-1]
    return value, as_of


def get_national_wage_percentiles(bls_career_field: str) -> dict:
    """
    Fetch 10th/25th/50th/75th/90th percentile wages for a BLS career field.
    Returns dict with keys: p10, p25, p50, p75, p90, as_of, source.
    Returns fallback national medians if BLS fetch fails.
    """
    field = _normalize_career_field(bls_career_field)
    cached = _read_cache(field)
    if cached is not None:
        return cached

    soc_code = BLS_CAREER_FIELD_TO_SOC.get(field)
    if not soc_code:
        result = _fallback_percentiles(field)
        _write_cache(field, result)
        return result

    percentiles: Dict[str, int] = {}
    as_of_values: list[str] = []
    fetch_failed = False

    for percentile_key, data_type in _PERCENTILE_DATA_TYPES.items():
        series_id = _build_oes_series_id(soc_code, data_type)
        value, as_of = _latest_point_value(series_id)
        if value is None:
            fetch_failed = True
            break
        percentiles[percentile_key] = int(round(value))
        if as_of:
            as_of_values.append(as_of)

    if fetch_failed or len(percentiles) != len(_PERCENTILE_DATA_TYPES):
        logger.warning('BLS OES fetch incomplete for %s; using fallback medians', field)
        result = _fallback_percentiles(field)
        _write_cache(field, result)
        return result

    result = {
        **percentiles,
        'as_of': max(as_of_values) if as_of_values else _today_iso(),
        'source': 'BLS OES national',
    }
    _write_cache(field, result)
    return result
