#!/usr/bin/env python3
"""Corporate jargon scoring via web text fetch and Claude analysis (CS1 layer 2)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from typing import Any
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Mingus/1.0; +https://mingusapp.com)",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 10
GOOGLE_SEARCH_URL = "https://www.google.com/search"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
LLM_MODEL = "claude-sonnet-4-6"
LLM_MAX_TOKENS = 800
JSON_RETRY_APPEND = (
    "\n\nIMPORTANT: Return only raw JSON. No backticks, no markdown, no prose."
)

SYSTEM_PROMPT = """You are a corporate culture analyst. You evaluate companies based on
the clarity and authenticity of their public communications.
Research shows that high-jargon language in corporate communications
correlates with lower internal accountability and weaker analytical culture.
Return ONLY valid JSON. No preamble. No markdown fences. No explanation."""


class JargonScorer:
    """Fetch employer public text, score jargon via LLM, and cache results."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    @staticmethod
    def _log_warning(message: str) -> None:
        try:
            from flask import current_app, has_app_context

            if has_app_context():
                current_app.logger.warning(message)
                return
        except Exception:
            pass
        print(message)

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """SHA-256 of lowercased, whitespace-normalized text."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def compute_name_hash(employer_name: str) -> str:
        """SHA-256 hash of lowercased employer name."""
        return JargonScorer.compute_text_hash(employer_name.lower())

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _strip_scripts_and_styles(self, soup: BeautifulSoup) -> None:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

    def _google_search_urls(self, query: str, max_results: int) -> list[str]:
        urls: list[str] = []
        try:
            response = self.session.get(
                GOOGLE_SEARCH_URL,
                params={"q": query, "num": max(max_results, 10)},
                headers=REQUEST_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.select("a[href]"):
                href = anchor.get("href", "")
                url: str | None = None
                if href.startswith("/url?q="):
                    url = unquote(href.split("/url?q=")[1].split("&")[0])
                elif href.startswith("http") and "google." not in href:
                    url = href
                if not url or not url.startswith("http"):
                    continue
                if url in urls:
                    continue
                urls.append(url)
                if len(urls) >= max_results:
                    break
        except Exception as exc:
            self._log_warning(f"Google search failed for query {query!r}: {exc}")
        return urls

    def _fetch_page_html(self, url: str) -> str | None:
        try:
            response = self.session.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except Exception as exc:
            self._log_warning(f"Page fetch failed for {url!r}: {exc}")
            return None

    def _extract_careers_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        self._strip_scripts_and_styles(soup)

        for tag_name in ("main", "article", "section"):
            element = soup.find(tag_name)
            if element:
                return self._normalize_whitespace(element.get_text(separator=" "))

        for div in soup.find_all("div", class_=True):
            class_names = " ".join(div.get("class", [])).lower()
            if "career" in class_names or "job" in class_names:
                return self._normalize_whitespace(div.get_text(separator=" "))

        paragraphs = [p.get_text(separator=" ") for p in soup.find_all("p")]
        return self._normalize_whitespace(" ".join(paragraphs))

    def _extract_paragraph_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        self._strip_scripts_and_styles(soup)
        paragraphs = [p.get_text(separator=" ") for p in soup.find_all("p")]
        return self._normalize_whitespace(" ".join(paragraphs))

    def fetch_company_text(
        self,
        employer_name: str,
        employer_cik: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetch up to three text sources via Google search.
        Never raises — network failures yield empty strings and fetch_errors entries.
        """
        del employer_cik  # reserved for future CIK-specific sources
        fetch_errors: list[str] = []
        careers_text = ""
        job_posting_text = ""
        about_text = ""

        # Source A — careers page
        try:
            domain_guess = employer_name.lower().replace(" ", "")
            careers_query = (
                f'"{employer_name}" careers jobs site:{domain_guess}.com'
            )
            careers_urls = self._google_search_urls(careers_query, max_results=1)
            if not careers_urls:
                fetch_errors.append("careers: no Google search results")
            else:
                html = self._fetch_page_html(careers_urls[0])
                if html is None:
                    fetch_errors.append(
                        f"careers: failed to fetch {careers_urls[0]}"
                    )
                else:
                    careers_text = self._extract_careers_text(html)[:3000]
        except Exception as exc:
            fetch_errors.append(f"careers: {exc}")
            careers_text = ""

        # Source B — job postings (first two results)
        try:
            jobs_query = (
                f'"{employer_name}" job description responsibilities qualifications'
            )
            job_urls = self._google_search_urls(jobs_query, max_results=2)
            if not job_urls:
                fetch_errors.append("job_postings: no Google search results")
            else:
                job_chunks: list[str] = []
                for url in job_urls:
                    try:
                        html = self._fetch_page_html(url)
                        if html is None:
                            fetch_errors.append(f"job_postings: failed to fetch {url}")
                            continue
                        chunk = self._extract_paragraph_text(html)[:1200]
                        if chunk:
                            job_chunks.append(chunk)
                    except Exception as exc:
                        fetch_errors.append(f"job_postings: {url}: {exc}")
                job_posting_text = " | ".join(job_chunks)
        except Exception as exc:
            fetch_errors.append(f"job_postings: {exc}")
            job_posting_text = ""

        # Source C — about/mission page
        try:
            about_query = f'"{employer_name}" about us mission values culture'
            about_urls = self._google_search_urls(about_query, max_results=1)
            if not about_urls:
                fetch_errors.append("about: no Google search results")
            else:
                html = self._fetch_page_html(about_urls[0])
                if html is None:
                    fetch_errors.append(f"about: failed to fetch {about_urls[0]}")
                else:
                    about_text = self._extract_paragraph_text(html)[:1000]
        except Exception as exc:
            fetch_errors.append(f"about: {exc}")
            about_text = ""

        total_chars = len(careers_text) + len(job_posting_text) + len(about_text)
        return {
            "careers_text": careers_text,
            "job_posting_text": job_posting_text,
            "about_text": about_text,
            "fetch_errors": fetch_errors,
            "total_chars": total_chars,
        }

    @staticmethod
    def get_cached_score(
        employer_name_hash: str,
        raw_text_hash: str,
        db_session,
    ):
        """Return a non-expired CompanyJargonCache row, or None."""
        from datetime import datetime

        from backend.models.company_screen import CompanyJargonCache

        return (
            db_session.query(CompanyJargonCache)
            .filter(
                CompanyJargonCache.employer_name_hash == employer_name_hash,
                CompanyJargonCache.raw_text_hash == raw_text_hash,
                CompanyJargonCache.expires_at > datetime.utcnow(),
            )
            .first()
        )

    def _build_user_prompt(self, text_bundle: dict[str, Any], employer_name: str) -> str:
        return f"""
Analyze the following public text from {employer_name}.
Score each dimension 0-100 where 100 = maximum clarity and authenticity,
0 = pure jargon and vagueness.

CAREERS PAGE TEXT:
{text_bundle['careers_text'][:2000]}

JOB POSTING TEXT:
{text_bundle['job_posting_text'][:2000]}

ABOUT/MISSION TEXT:
{text_bundle['about_text'][:800]}

Return this exact JSON structure:
{{
  "jargon_density_score": <integer 0-100, where 100 = crystal clear, 0 = pure jargon>,
  "role_clarity_score": <integer 0-100, does job text describe concrete work or vague ownership?>,
  "values_authenticity_score": <integer 0-100, are stated values specific or generic platitudes?>,
  "leadership_transparency_score": <integer 0-100, do leadership bios show real work or just titles?>,
  "composite_layer2_score": <integer: (jargon*0.40 + role*0.25 + values*0.20 + leadership*0.15), round to int>,
  "top_jargon_phrases": [<list of up to 5 exact phrases from the text flagged as empty jargon. Empty list [] if none found.>],
  "scoring_notes": "<one sentence plain-English explanation of the score>"
}}
"""

    @staticmethod
    def _strip_markdown_fences(raw: str) -> str:
        return (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

    def _anthropic_post(self, api_key: str, user_prompt: str) -> str:
        response = requests.post(
            ANTHROPIC_MESSAGES_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "max_tokens": LLM_MAX_TOKENS,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    def score_with_llm(
        self,
        text_bundle: dict[str, Any],
        employer_name: str,
    ) -> dict[str, Any]:
        """Call Anthropic API and return parsed scoring dict; never raises."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "layer2_score": None,
                "layer2_status": "unavailable",
                "error": "ANTHROPIC_API_KEY not configured",
            }

        user_prompt = self._build_user_prompt(text_bundle, employer_name)
        raw = ""

        try:
            raw = self._anthropic_post(api_key, user_prompt)
            parsed = json.loads(self._strip_markdown_fences(raw))
            return parsed
        except json.JSONDecodeError:
            try:
                raw = self._anthropic_post(api_key, user_prompt + JSON_RETRY_APPEND)
                parsed = json.loads(self._strip_markdown_fences(raw))
                return parsed
            except json.JSONDecodeError:
                self._log_warning(f"LLM returned unparseable JSON: {raw}")
                return {
                    "layer2_score": None,
                    "layer2_status": "parse_error",
                    "error": "LLM returned unparseable JSON",
                }
        except requests.RequestException as exc:
            return {
                "layer2_score": None,
                "layer2_status": "unavailable",
                "error": str(exc),
            }

    def save_to_cache(
        self,
        employer_name: str,
        employer_cik: str | None,
        text_bundle: dict[str, Any],
        llm_result: dict[str, Any],
        db_session,
    ):
        """Persist a CompanyJargonCache row; rollback silently on unique constraint race."""
        from backend.models.company_screen import CompanyJargonCache

        combined = (
            text_bundle["careers_text"]
            + text_bundle["job_posting_text"]
            + text_bundle["about_text"]
        )
        row = CompanyJargonCache(
            employer_cik=employer_cik,
            employer_name_hash=self.compute_name_hash(employer_name),
            raw_text_hash=self.compute_text_hash(combined),
            jargon_score=llm_result.get("composite_layer2_score"),
            jargon_density_pct=round(
                (100 - llm_result.get("jargon_density_score", 100)) / 100,
                4,
            ),
            top_jargon_phrases=llm_result.get("top_jargon_phrases", []),
        )
        db_session.add(row)
        try:
            db_session.commit()
        except Exception:
            db_session.rollback()
        return row

    def score_employer(
        self,
        employer_name: str,
        employer_cik: str | None = None,
        db_session=None,
    ) -> dict[str, Any]:
        """Main entry point for layer-2 jargon scoring; never raises."""
        text_bundle = self.fetch_company_text(employer_name, employer_cik)

        if text_bundle["total_chars"] < 100:
            return {
                "layer2_score": None,
                "layer2_status": "insufficient_text",
                "top_jargon_phrases": [],
                "scoring_notes": None,
                "from_cache": False,
                "fetch_errors": text_bundle["fetch_errors"],
            }

        combined_text = (
            text_bundle["careers_text"]
            + text_bundle["job_posting_text"]
            + text_bundle["about_text"]
        )
        employer_name_hash = self.compute_name_hash(employer_name)
        raw_text_hash = self.compute_text_hash(combined_text)

        if db_session is not None:
            cached = self.get_cached_score(
                employer_name_hash,
                raw_text_hash,
                db_session,
            )
            if cached:
                return {
                    "layer2_score": cached.jargon_score,
                    "layer2_status": "complete",
                    "jargon_density_pct": cached.jargon_density_pct,
                    "top_jargon_phrases": cached.top_jargon_phrases or [],
                    "scoring_notes": None,
                    "from_cache": True,
                    "fetch_errors": [],
                }

        time.sleep(2)
        llm_result = self.score_with_llm(text_bundle, employer_name)
        if llm_result.get("layer2_status") in ("unavailable", "parse_error"):
            return {
                **llm_result,
                "from_cache": False,
                "top_jargon_phrases": [],
                "fetch_errors": text_bundle["fetch_errors"],
            }

        if db_session is not None:
            self.save_to_cache(
                employer_name,
                employer_cik,
                text_bundle,
                llm_result,
                db_session,
            )

        return {
            "layer2_score": llm_result["composite_layer2_score"],
            "layer2_status": "complete",
            "jargon_density_score": llm_result["jargon_density_score"],
            "role_clarity_score": llm_result["role_clarity_score"],
            "values_authenticity_score": llm_result["values_authenticity_score"],
            "leadership_transparency_score": llm_result["leadership_transparency_score"],
            "top_jargon_phrases": llm_result["top_jargon_phrases"],
            "scoring_notes": llm_result["scoring_notes"],
            "from_cache": False,
            "fetch_errors": text_bundle["fetch_errors"],
        }
