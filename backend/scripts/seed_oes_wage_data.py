#!/usr/bin/env python3
"""
Seed oes_wage_data with 2024 BLS OES figures (#165).

Usage:
    python3 -m backend.scripts.seed_oes_wage_data

Idempotent: existing (bls_career_field, msa_code) rows are skipped.
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from backend.data.oes_wage_data_2024 import build_oes_wage_rows  # noqa: E402
from backend.models.database import db  # noqa: E402
from backend.models.market_conditions_models import OesWageData  # noqa: E402


def seed_oes_wage_data() -> tuple[int, int]:
    """Insert missing OES rows. Returns (inserted, skipped)."""
    from app import app  # noqa: WPS433 — Flask app factory for DB context

    rows = build_oes_wage_rows()
    inserted = 0
    skipped = 0

    with app.app_context():
        for row in rows:
            exists = (
                OesWageData.query.filter_by(
                    bls_career_field=row["bls_career_field"],
                    msa_code=row["msa_code"],
                ).first()
            )
            if exists:
                skipped += 1
                continue
            db.session.add(
                OesWageData(
                    bls_career_field=row["bls_career_field"],
                    msa_code=row["msa_code"],
                    msa_name=row["msa_name"],
                    pct_10=row["pct_10"],
                    pct_25=row["pct_25"],
                    pct_50=row["pct_50"],
                    pct_75=row["pct_75"],
                    pct_90=row["pct_90"],
                    source_year=row["source_year"],
                )
            )
            inserted += 1
        db.session.commit()

    return inserted, skipped


def main() -> None:
    inserted, skipped = seed_oes_wage_data()
    total = inserted + skipped
    print(f"oes_wage_data seed complete: {inserted} inserted, {skipped} skipped ({total} total rows checked)")


if __name__ == "__main__":
    main()
