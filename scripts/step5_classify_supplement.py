#!/usr/bin/env python3
"""Classify scraped supplement articles into Mingus 7-domain schema via Claude."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import anthropic
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_CSV = DATA_DIR / "scraped_supplement.csv"
OUTPUT_JSON = DATA_DIR / "classified_supplement.json"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400

VALID_DOMAINS = frozenset(
    {
        "housing",
        "mental_health_money",
        "career_income",
        "financial_habits",
        "physical_wellness",
        "relationships_money",
        "mental_models",
    }
)

SYSTEM_PROMPT = (
    "You are a content classifier for Mingus, a personal finance "
    "and wellness app for African American professionals ages 28-45. "
    "Classify the article into exactly one of these 7 domains: "
    "housing, mental_health_money, career_income, financial_habits, "
    "physical_wellness, relationships_money, mental_models. "
    "Return ONLY valid JSON. No preamble, no markdown."
)


def _load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("ANTHROPIC_API_KEY not found")


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_classification(raw: str) -> dict:
    data = json.loads(_strip_json(raw))
    domain = data.get("domain", "").strip()
    if domain not in VALID_DOMAINS:
        raise ValueError(f"invalid domain: {domain}")
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        raise ValueError("tags must be a list")
    return {
        "domain": domain,
        "tags": [str(t) for t in tags[:5]],
        "read_time_minutes": int(data.get("read_time_minutes") or 1),
        "summary": str(data.get("summary") or "").strip(),
    }


def _classify_row(client: anthropic.Anthropic, row: dict) -> dict | None:
    title = str(row.get("title") or "")
    description = str(row.get("summary") or row.get("meta_description") or "")
    body = str(row.get("content") or "")
    domain_hint = str(row.get("domain_hint") or "")

    user_prompt = (
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Body excerpt (first 800 chars): {body[:800]}\n"
        f"Domain hint from source: {domain_hint}\n\n"
        "Return:\n"
        "{\n"
        "  \"domain\": \"<one of the 7 domains>\",\n"
        "  \"tags\": [\"<3-5 relevant tags>\"],\n"
        "  \"read_time_minutes\": <int>,\n"
        "  \"summary\": \"<2 sentence plain English summary>\"\n"
        "}"
    )

    for attempt in range(2):
        extra = ""
        if attempt == 1:
            extra = "\n\nReturn only raw JSON, no backticks or explanation."
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt + extra}],
        )
        raw = message.content[0].text if message.content else ""
        try:
            return _parse_classification(raw)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            if attempt == 1:
                print(f"SKIP classify failed for {row.get('url')}: {exc}")
                return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify scraped supplement articles")
    parser.add_argument("--input", type=Path, default=INPUT_CSV)
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON)
    args = parser.parse_args()

    input_csv = args.input
    output_json = args.output

    if not input_csv.exists():
        raise FileNotFoundError(f"Missing {input_csv} — run step4 first")

    df = pd.read_csv(input_csv)
    if df.empty:
        print("No scraped rows to classify.")
        output_json.write_text("[]")
        return

    client = anthropic.Anthropic(api_key=_load_api_key())
    results: list[dict] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        url = str(row_dict.get("url") or "")
        if not url:
            continue

        classified = _classify_row(client, row_dict)
        if not classified:
            continue

        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            source = host[4:]
        else:
            source = host

        read_time = classified["read_time_minutes"]
        if row_dict.get("reading_time") and not pd.isna(row_dict.get("reading_time")):
            read_time = int(row_dict["reading_time"])

        results.append(
            {
                "url": url,
                "title": str(row_dict.get("title") or "Untitled")[:500],
                "description": classified["summary"] or str(row_dict.get("summary") or "")[:2000],
                "source": source,
                "domain": classified["domain"],
                "tags": classified["tags"],
                "read_time_minutes": max(1, read_time),
                "summary": classified["summary"],
                "published_date": row_dict.get("publish_date")
                if row_dict.get("publish_date") and not pd.isna(row_dict.get("publish_date"))
                else None,
                "classified_at": now,
            }
        )
        time.sleep(0.5)

    output_json.write_text(json.dumps(results, indent=2))
    print(f"Wrote {len(results)} records to {output_json}")

    dist = Counter(r["domain"] for r in results)
    print("Classification domain distribution:")
    for domain, count in dist.most_common():
        print(f"  {domain}: {count}")


if __name__ == "__main__":
    main()
