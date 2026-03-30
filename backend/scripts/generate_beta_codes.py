#!/usr/bin/env python3
"""Generate beta invite codes and write CSV under backend/data/."""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import app  # noqa: E402
from backend.models.beta_code import BetaCode  # noqa: E402


def _safe_batch_filename(batch: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", batch).strip("_")
    return cleaned or "batch"


def main():
    parser = argparse.ArgumentParser(description="Generate Mingus beta codes.")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--batch", type=str, default="wave_1")
    args = parser.parse_args()

    with app.app_context():
        created = BetaCode.generate_bulk(args.count, args.batch)

    for row in created:
        print(row.code)

    print(f"Generated {len(created)} codes for batch {args.batch}", file=sys.stderr)

    data_dir = os.path.join(_REPO_ROOT, "backend", "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_name = f"beta_codes_{_safe_batch_filename(args.batch)}.csv"
    csv_path = os.path.join(data_dir, csv_name)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "status", "batch", "created_at"])
        for row in created:
            w.writerow(
                [
                    row.code,
                    row.status,
                    row.batch or "",
                    row.created_at.isoformat() if row.created_at else "",
                ]
            )

    print(f"Wrote {csv_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
