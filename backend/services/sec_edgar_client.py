#!/usr/bin/env python3
"""SEC EDGAR API client with token-bucket rate limiting and resilient parsing."""

from __future__ import annotations

import logging
import threading
import time
from datetime import date
from typing import Any
from urllib.parse import quote

import requests

from backend.config.edgar_config import (
    EDGAR_COMPANY_FACTS_URL,
    EDGAR_COMPANY_SEARCH_URL,
    EDGAR_FULL_TEXT_URL,
    EDGAR_SUBMISSIONS_URL,
    RATE_LIMIT_RPS,
    SEC_USER_AGENT,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class EdgarRateLimiter:
    """Token-bucket limiter — default 8 req/s to stay under SEC's 10/sec cap."""

    def __init__(self, capacity: int = RATE_LIMIT_RPS, rate: float = RATE_LIMIT_RPS) -> None:
        self.capacity = capacity
        self.rate = rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, n: int = 1) -> None:
        with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now
                if self.tokens >= n:
                    self.tokens -= n
                    return
                wait = (n - self.tokens) / self.rate
                time.sleep(wait)


_limiter = EdgarRateLimiter()


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


def extract_concept(
    facts: dict,
    taxonomy: str,
    concept: str,
    unit: str = "USD",
) -> list[dict]:
    """Navigate facts[taxonomy][concept][units][unit]; return normalized entries."""
    try:
        raw_entries = facts["facts"][taxonomy][concept]["units"][unit]
    except (KeyError, TypeError):
        return []

    result: list[dict] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        result.append(
            {
                "val": entry.get("val"),
                "end": entry.get("end"),
                "filed": entry.get("filed"),
                "accession": entry.get("accn") or entry.get("accession"),
                "form": entry.get("form"),
            }
        )
    return result


def latest_annual_value(entries: list[dict]) -> float | None:
    """Return the val from the most recent 10-K entry by end date."""
    annual = [
        e for e in entries
        if e.get("form") == "10-K" and e.get("val") is not None and e.get("end")
    ]
    if not annual:
        return None
    annual.sort(key=lambda e: e["end"], reverse=True)
    return float(annual[0]["val"])


def trailing_four_quarters(entries: list[dict], skip: int = 0) -> float | None:
    """Sum vals from the four most recent non-overlapping 10-Q quarters."""
    quarterly = [
        e for e in entries
        if e.get("form") == "10-Q" and e.get("val") is not None and e.get("end")
    ]
    if not quarterly:
        return None

    quarterly.sort(key=lambda e: e["end"], reverse=True)
    seen_ends: set[str] = set()
    selected: list[dict] = []
    skipped = 0

    for entry in quarterly:
        end = entry["end"]
        if end in seen_ends:
            continue
        if skipped < skip:
            seen_ends.add(end)
            skipped += 1
            continue
        seen_ends.add(end)
        selected.append(entry)
        if len(selected) == 4:
            break

    if len(selected) < 4:
        return None
    return sum(float(e["val"]) for e in selected)


class SecEdgarClient:
    """Rate-limited wrapper for SEC EDGAR company facts, submissions, and search."""

    def __init__(self, user_agent: str | None = None) -> None:
        self.user_agent = (user_agent or SEC_USER_AGENT or "").strip()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )

    def _request(self, url: str, host: str) -> requests.Response | None:
        _limiter.acquire()
        try:
            return self.session.get(
                url,
                headers={"Host": host},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("SEC EDGAR request failed for %s: %s", url, exc)
            return None

    def _handle_facts_response(self, response: requests.Response | None) -> dict | None:
        if response is None:
            return None
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                logger.warning("SEC EDGAR JSON parse failed: %s", exc)
                return None
        if response.status_code == 404:
            return None
        if response.status_code == 403:
            logger.warning("SEC blocked request — check User-Agent")
            return None
        logger.warning(
            "SEC EDGAR unexpected status %s for %s",
            response.status_code,
            response.url,
        )
        return None

    def get_company_facts(self, cik: str) -> dict | None:
        cik_padded = _pad_cik(cik)
        url = EDGAR_COMPANY_FACTS_URL.format(cik=cik_padded)
        response = self._request(url, host="data.sec.gov")
        return self._handle_facts_response(response)

    def get_company_submissions(self, cik: str) -> dict | None:
        cik_padded = _pad_cik(cik)
        url = EDGAR_SUBMISSIONS_URL.format(cik=cik_padded)
        response = self._request(url, host="api.sec.gov")
        return self._handle_facts_response(response)

    def search_8k_layoff_filings(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        url = EDGAR_FULL_TEXT_URL.format(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )
        response = self._request(url, host="efts.sec.gov")
        if response is None or response.status_code != 200:
            return []

        try:
            payload = response.json()
        except ValueError:
            return []

        hits = payload.get("hits", {}).get("hits", [])
        if not isinstance(hits, list):
            return []

        results: list[dict] = []
        for hit in hits:
            source = hit.get("_source", hit) if isinstance(hit, dict) else {}
            if not isinstance(source, dict):
                continue

            ciks = source.get("ciks") or source.get("cik") or []
            if isinstance(ciks, str):
                ciks = [ciks]
            cik = _pad_cik(ciks[0]) if ciks else None

            accession = (
                source.get("adsh")
                or source.get("accession_number")
                or source.get("accession")
            )
            filed = source.get("file_date") or source.get("filed")
            entity_name = (
                source.get("display_names", [None])[0]
                if source.get("display_names")
                else source.get("entity_name") or source.get("display_name")
            )

            if cik and accession:
                results.append(
                    {
                        "cik": cik,
                        "accession": accession,
                        "filed": filed,
                        "entity_name": entity_name,
                    }
                )
        return results

    def resolve_cik(self, company_name: str) -> list[dict]:
        encoded_name = quote(company_name.strip())
        url = EDGAR_COMPANY_SEARCH_URL.format(company_name=encoded_name)
        response = self._request(url, host="efts.sec.gov")
        if response is None or response.status_code != 200:
            return []

        try:
            payload = response.json()
        except ValueError:
            return []

        hits = payload.get("hits", {}).get("hits", [])
        if not isinstance(hits, list):
            return []

        results: list[dict] = []
        for hit in hits[:5]:
            source = hit.get("_source", hit) if isinstance(hit, dict) else {}
            if not isinstance(source, dict):
                continue

            ciks = source.get("ciks") or source.get("cik") or []
            if isinstance(ciks, str):
                ciks = [ciks]
            if not ciks:
                continue

            name = (
                source.get("display_names", [None])[0]
                if source.get("display_names")
                else source.get("entity_name") or source.get("display_name")
            )
            tickers = source.get("tickers") or []
            exchanges = source.get("exchanges") or source.get("exchange") or []

            ticker = tickers[0] if isinstance(tickers, list) and tickers else None
            exchange = (
                exchanges[0]
                if isinstance(exchanges, list) and exchanges
                else exchanges if isinstance(exchanges, str) else None
            )

            results.append(
                {
                    "cik": _pad_cik(ciks[0]),
                    "name": name,
                    "ticker": ticker,
                    "exchange": exchange,
                }
            )
        return results

    def fetch_filing_text(self, cik: str, accession_number: str) -> str | None:
        """Fetch full submission text from SEC Archives for an accession number."""
        cik_padded = _pad_cik(cik)
        cik_int = str(int(cik_padded))
        accession = accession_number.strip()
        accession_nodash = accession.replace("-", "")
        url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_nodash}/{accession}.txt"
        )
        response = self._request(url, host="www.sec.gov")
        if response is None or response.status_code != 200:
            return None
        return response.text
