#!/usr/bin/env python3
"""Seed raw_urls_complete.csv and approved_domains.txt for thin domain supplement."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
CSV_PATH = DATA_DIR / "raw_urls_complete.csv"
APPROVED_PATH = CONFIG_DIR / "approved_domains.txt"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

SKIP_PATH_RE = re.compile(
    r"/(login|signup|register|subscribe|cart|checkout|privacy|terms|contact|about|"
    r"admin|api|feed|rss|tag|tags|category|categories|hub|section|series|resources|"
    r"programs|topics|blog/?$|research/?$)",
    re.I,
)

HOUSING_URLS = [
    "https://shelterforce.org/category/affordable-housing/",
    "https://nextcity.org/urbanist-news/housing",
    "https://www.nahb.org/news-and-economics/housing-economics",
    "https://www.freddiemac.com/research/insight",
    "https://www.apartmentlist.com/research",
    "https://blavity.com/tag/homeownership",
    "https://www.essence.com/money/home-buying/",
    "https://www.biggerpockets.com/blog/category/first-time-home-buyers",
    "https://therealdeal.com/",
    "https://apnews.com/hub/housing",
    "https://www.nytimes.com/section/realestate",
]

MENTAL_HEALTH_URLS = [
    "https://www.apa.org/topics/stress/money",
    "https://www.financialhealthnetwork.org/news/",
    "https://psychcentral.com/stress/financial-stress",
    "https://www.mentalhealthamerica.net/mental-health-and-financial-wellness",
    "https://www.therapyforblackgirls.com/blog/",
    "https://therapyforblackmen.org/resources/",
    "https://www.blackenterprise.com/category/money/financial-wellness/",
    "https://blavity.com/tag/mental-health",
    "https://humbledollar.com/category/our-minds/",
    "https://www.calm.com/blog/",
    "https://www.psychologytoday.com/us/blog/science-choice",
    "https://www.vox.com/money",
    "https://www.npr.org/series/money-and-mental-health",
]

SEEDS: list[tuple[str, str]] = [
    *(("housing", u) for u in HOUSING_URLS),
    *(("mental_health_money", u) for u in MENTAL_HEALTH_URLS),
]


def _load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL not found in environment or .env")


def _existing_db_urls(database_url: str) -> set[str]:
    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT url FROM articles")
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def _netloc(url: str) -> str:
    return urlparse(url).netloc.lower()


def _looks_like_article_path(path: str) -> bool:
    if not path or path == "/":
        return False
    if SKIP_PATH_RE.search(path):
        return False
    segments = [s for s in path.strip("/").split("/") if s]
    if len(segments) < 2:
        return False
    last = segments[-1]
    if len(last) < 5:
        return False
    return True


def _discover_article_links(seed_url: str, max_links: int = 8) -> list[str]:
    """Fetch a hub/listing page and return same-domain article-like links."""
    found: list[str] = []
    try:
        resp = requests.get(
            seed_url,
            timeout=25,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            return found
        soup = BeautifulSoup(resp.text, "html.parser")
        base_host = _netloc(seed_url)
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:"):
                continue
            full = urljoin(seed_url, href)
            parsed = urlparse(full)
            if parsed.netloc.lower() != base_host:
                continue
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/"
            if clean.rstrip("/") == seed_url.rstrip("/"):
                continue
            if not _looks_like_article_path(parsed.path):
                continue
            if clean in seen:
                continue
            seen.add(clean)
            found.append(clean)
            if len(found) >= max_links:
                break
    except requests.RequestException:
        return found
    return found


def _collect_seed_urls(domain_hint: str, seed_url: str) -> list[str]:
    """Return article URLs: discovered links first, else the seed if it looks like an article."""
    discovered = _discover_article_links(seed_url)
    if discovered:
        return discovered
    path = urlparse(seed_url).path
    if _looks_like_article_path(path):
        return [seed_url]
    return []


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    db_urls = _existing_db_urls(_load_database_url())

    rows: list[dict[str, str]] = []
    domains: set[str] = set()
    added = 0
    skipped = 0
    seen_urls: set[str] = set()

    session_urls: list[tuple[str, str]] = []
    for domain_hint, seed_url in SEEDS:
        for url in _collect_seed_urls(domain_hint, seed_url):
            session_urls.append((domain_hint, url))

    for domain_hint, url in session_urls:
        if url in db_urls or url in seen_urls:
            skipped += 1
            continue
        seen_urls.add(url)
        host = _netloc(url)
        rows.append({"url": url, "domain": host, "domain_hint": domain_hint})
        domains.add(host)
        added += 1

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "domain", "domain_hint"])
        writer.writeheader()
        writer.writerows(rows)

    with APPROVED_PATH.open("w", encoding="utf-8") as f:
        for d in sorted(domains):
            f.write(f"{d}\n")

    print(f"{added} added, {skipped} skipped (already in DB)")
    print(f"Wrote {CSV_PATH} ({len(rows)} rows)")
    print(f"Wrote {APPROVED_PATH} ({len(domains)} domains)")


if __name__ == "__main__":
    main()
