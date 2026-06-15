#!/usr/bin/env python3
"""WARN Firehose API client for state WARN Act layoff notices."""

from __future__ import annotations

import logging
import os
import threading
from datetime import date, datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

WARN_API_BASE = "https://warnfirehose.com/api"
REQUEST_TIMEOUT = 15
DAILY_CALL_LIMIT = 25
DAILY_CALL_WARN_THRESHOLD = 20

_call_counter = 0
_call_counter_lock = threading.Lock()


def _increment_call_counter() -> int:
    global _call_counter
    with _call_counter_lock:
        _call_counter += 1
        count = _call_counter
    if count >= DAILY_CALL_WARN_THRESHOLD:
        logger.warning(
            "WARN Firehose API calls at %s/%s for this process",
            count,
            DAILY_CALL_LIMIT,
        )
    return count


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace(",", "")
    try:
        return int(float(text))
    except ValueError:
        return 0


def _normalize_layoff_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "closure" in text or "closing" in text or "shutdown" in text:
        return "closure"
    if "layoff" in text or "rif" in text or "reduction" in text:
        return "layoff"
    return "unknown"


def _normalize_warn_record(raw: dict[str, Any]) -> dict | None:
    company_name = (
        raw.get("company_name")
        or raw.get("company")
        or raw.get("employer_name")
        or raw.get("debtor_name")
        or raw.get("name")
    )
    if not company_name:
        return None

    state = (
        raw.get("state")
        or raw.get("state_code")
        or raw.get("notice_state")
        or ""
    )
    state = str(state).strip().upper()[:2]

    filing_date = _parse_date(
        raw.get("filing_date")
        or raw.get("notice_date")
        or raw.get("date")
        or raw.get("effective_date")
        or raw.get("warn_date")
    )
    if filing_date is None:
        return None

    worker_count = _parse_int(
        raw.get("worker_count")
        or raw.get("employees_affected")
        or raw.get("num_employees")
        or raw.get("affected_workers")
        or raw.get("employees")
        or raw.get("total_employees_affected")
    )

    layoff_type = _normalize_layoff_type(
        raw.get("layoff_type")
        or raw.get("notice_type")
        or raw.get("type")
        or raw.get("event_type")
    )

    notice_url = (
        raw.get("notice_url")
        or raw.get("url")
        or raw.get("source_url")
        or raw.get("link")
        or raw.get("docket_url")
    )
    if notice_url is not None:
        notice_url = str(notice_url).strip() or None

    return {
        "company_name": str(company_name).strip(),
        "state": state,
        "filing_date": filing_date,
        "worker_count": worker_count,
        "layoff_type": layoff_type,
        "notice_url": notice_url,
    }


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("results", "records", "data", "notices", "items", "warn_notices"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    if any(
        key in payload
        for key in ("company_name", "company", "filing_date", "notice_date", "date")
    ):
        return [payload]
    return []


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


class WarnActClient:
    """Client for WARN Firehose layoff notice and CIK cross-reference endpoints."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key if api_key is not None else os.environ.get("WARN_FIREHOSE_API_KEY") or "").strip()
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> requests.Response | None:
        if _increment_call_counter() > DAILY_CALL_LIMIT:
            logger.warning("WARN Firehose daily call limit reached for this process")
            return None

        url = f"{WARN_API_BASE}/{path.lstrip('/')}"
        try:
            return self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            logger.warning("WARN Firehose request failed for %s: %s", url, exc)
            return None

    def _normalize_response(self, response: requests.Response | None) -> list[dict]:
        if response is None:
            return []
        if response.status_code != 200:
            logger.warning(
                "WARN Firehose returned HTTP %s for %s",
                response.status_code,
                response.url,
            )
            return []

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning("WARN Firehose JSON parse failed: %s", exc)
            return []

        normalized: list[dict] = []
        for raw in _extract_records(payload):
            record = _normalize_warn_record(raw)
            if record is not None:
                normalized.append(record)
        return normalized

    def search_by_name(
        self,
        company_name: str,
        state: str | None = None,
        days_back: int = 90,
    ) -> list[dict]:
        """Search WARN notices by company name."""
        company_name = str(company_name).strip()
        if not company_name:
            return []

        date_from = (date.today() - timedelta(days=int(days_back))).isoformat()
        params: dict[str, Any] = {
            "company": company_name,
            "date_from": date_from,
        }
        if state:
            params["state"] = str(state).strip().upper()[:2]

        response = self._get("warn", params=params)
        return self._normalize_response(response)

    def search_by_cik_crossref(self, cik: str) -> list[dict]:
        """Search WARN notices cross-referenced to a SEC CIK."""
        cik_padded = _pad_cik(cik)
        if not cik_padded.strip("0"):
            return []

        response = self._get("bankruptcies/warn-crossref")
        if response is None:
            return []

        try:
            payload = response.json()
        except ValueError:
            return []

        matched: list[dict] = []
        for raw in _extract_records(payload):
            if not isinstance(raw, dict):
                continue
            raw_cik = raw.get("cik") or raw.get("company_cik") or raw.get("sec_cik")
            if raw_cik is None:
                continue
            if _pad_cik(str(raw_cik)) != cik_padded:
                continue

            nested = raw.get("warn_notices") or raw.get("notices") or raw.get("records")
            if isinstance(nested, list) and nested:
                for item in nested:
                    if not isinstance(item, dict):
                        continue
                    merged = {**raw, **item}
                    record = _normalize_warn_record(merged)
                    if record is not None:
                        matched.append(record)
            else:
                record = _normalize_warn_record(raw)
                if record is not None:
                    matched.append(record)

        return matched
