#!/usr/bin/env python3
"""Seed job_postings table with curated MSA/field data (#113 Phase A2)."""

from __future__ import annotations

import os
import sys
from collections import Counter

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import app  # noqa: E402
from backend.models.database import db  # noqa: E402
from backend.models.job_posting import JobPosting  # noqa: E402
from backend.scripts.job_postings_seed_data import (  # noqa: E402
    ADVANCEMENT_BY_FIELD,
    FIELD_BASE_SALARIES,
    FIELD_COMPANIES,
    FIELD_ROLE_TITLES,
    MSA_CONFIG,
    MSA_SALARY_MULTIPLIERS,
    MSA_STRONG_FIELDS,
    SENIORITY_LEVELS,
    TIER_ROLE_COUNTS,
)

SEED_SOURCE = "seed_2026"


def _scaled_salary(
    field: str,
    seniority: str,
    msa_code: str,
    title_index: int,
) -> tuple[int, int]:
    base_min, base_max = FIELD_BASE_SALARIES[field][seniority]
    multiplier = MSA_SALARY_MULTIPLIERS[msa_code]
    spread = 1 + (title_index * 0.02)
    salary_min = int(base_min * multiplier * spread)
    salary_max = int(base_max * multiplier * spread)
    return salary_min, salary_max


def _build_rows() -> list[JobPosting]:
    rows: list[JobPosting] = []
    for msa_code, fields in MSA_STRONG_FIELDS.items():
        meta = MSA_CONFIG[msa_code]
        tier = meta["tier"]
        role_counts = TIER_ROLE_COUNTS[tier]
        for field in fields:
            titles_by_level = FIELD_ROLE_TITLES[field]
            companies = FIELD_COMPANIES[field]
            for seniority in SENIORITY_LEVELS:
                count = role_counts[seniority]
                for idx in range(count):
                    title = titles_by_level[seniority][idx]
                    company = companies[idx % len(companies)]
                    salary_min, salary_max = _scaled_salary(field, seniority, msa_code, idx)
                    rows.append(
                        JobPosting(
                            title=title,
                            company=company,
                            career_field=field,
                            msa_code=msa_code,
                            city=meta["city"],
                            state=meta["state"],
                            salary_min=salary_min,
                            salary_max=salary_max,
                            seniority_level=seniority,
                            is_management=seniority == "director",
                            advancement_trajectory=ADVANCEMENT_BY_FIELD[field][seniority],
                            source=SEED_SOURCE,
                            is_active=True,
                        )
                    )
    return rows


def seed_job_postings() -> tuple[int, Counter[str], Counter[str], int]:
    """Replace seed_2026 rows and insert fresh data. Returns total and summary counters."""
    deleted = (
        JobPosting.query.filter_by(source=SEED_SOURCE).delete(synchronize_session=False)
    )
    rows = _build_rows()
    db.session.add_all(rows)
    db.session.commit()

    field_counts: Counter[str] = Counter()
    msa_counts: Counter[str] = Counter()
    for row in rows:
        field_counts[row.career_field] += 1
        msa_counts[row.msa_code] += 1

    return len(rows), field_counts, msa_counts, deleted


def main() -> None:
    with app.app_context():
        inserted, by_field, by_msa, deleted = seed_job_postings()

        print(f"Seed complete: removed {deleted} existing rows, inserted {inserted} rows")
        print("\nRows by career field:")
        for field, count in sorted(by_field.items()):
            print(f"  {field}: {count}")

        print("\nRows by MSA:")
        for msa_code, count in sorted(by_msa.items()):
            city = MSA_CONFIG[msa_code]["city"]
            print(f"  {msa_code} ({city}): {count}")


if __name__ == "__main__":
    main()
