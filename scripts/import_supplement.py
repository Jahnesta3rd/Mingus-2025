#!/usr/bin/env python3
"""Import classified supplement JSON into Postgres articles table."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_JSON = PROJECT_ROOT / "data" / "classified_supplement.json"


def _load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    for line in (PROJECT_ROOT / ".env").read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import classified supplement JSON")
    parser.add_argument("--input", type=Path, default=INPUT_JSON)
    args = parser.parse_args()

    input_json = args.input
    if not input_json.exists():
        raise FileNotFoundError(f"Missing {input_json}")

    records = json.loads(input_json.read_text())
    if not records:
        print("No records to import.")
        return

    conn = psycopg2.connect(_load_database_url())
    inserted = 0
    skipped = 0
    inserted_domains: Counter[str] = Counter()

    try:
        with conn.cursor() as cur:
            for rec in records:
                url = rec["url"]
                cur.execute("SELECT id FROM articles WHERE url = %s", (url,))
                if cur.fetchone():
                    skipped += 1
                    print(f"skipped duplicate: {url[:80]}")
                    continue

                title = rec.get("title") or "Untitled"
                description = rec.get("description") or rec.get("summary") or ""
                summary = rec.get("summary") or description
                source = rec.get("source") or "unknown"
                domain = rec["domain"]
                tags = rec.get("tags") or []
                read_time = int(rec.get("read_time_minutes") or 1)
                published = rec.get("published_date")
                classified_at = rec.get("classified_at")

                cur.execute(
                    """
                    INSERT INTO articles (
                        url, title, description, source, domain, tags,
                        read_time_minutes, published_date, classified_at,
                        is_active, summary, search_vector
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        TRUE, %s,
                        to_tsvector('english',
                            coalesce(%s, '') || ' ' ||
                            coalesce(%s, '') || ' ' ||
                            coalesce(%s, '')
                        )
                    )
                    RETURNING id
                    """,
                    (
                        url,
                        title[:500],
                        description,
                        source[:255],
                        domain,
                        tags,
                        read_time,
                        published,
                        classified_at,
                        summary,
                        title,
                        description,
                        summary,
                    ),
                )
                new_id = cur.fetchone()[0]
                inserted += 1
                inserted_domains[domain] += 1
                print(f"inserted id={new_id} domain={domain}: {title[:60]}")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"\nImport complete: inserted {inserted}, skipped {skipped} (duplicate)")

    if inserted_domains:
        print("Newly inserted by domain:")
        for domain, count in inserted_domains.most_common():
            print(f"  {domain}: {count}")

    conn = psycopg2.connect(_load_database_url())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT domain, COUNT(*) AS count
                FROM articles
                WHERE is_active = TRUE
                GROUP BY domain
                ORDER BY count DESC
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    print("\nFinal active article counts:")
    counts = {}
    for domain, count in rows:
        counts[domain] = count
        print(f"  {domain}: {count}")

    if counts.get("housing", 0) >= 20:
        print("RESOLVED: housing >= 20")
    else:
        print("FLAG: housing still thin, consider more sources")
    if counts.get("mental_health_money", 0) >= 18:
        print("RESOLVED: mental_health_money >= 18")
    else:
        print("FLAG: mental_health_money still thin, consider more sources")


if __name__ == "__main__":
    main()
