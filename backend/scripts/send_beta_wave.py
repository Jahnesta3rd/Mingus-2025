#!/usr/bin/env python3
# RECOMMENDED SEND SCHEDULE:
# Wave 1: 25 users — batch label "wave_1" — send first, wait 5-7 days
# Wave 2: 50 users — batch label "wave_2" — send after wave_1 issues resolved
# Wave 3: 25 users — batch label "wave_3" — final batch
"""CLI: prepare and dispatch batched beta invite emails via Celery."""

from __future__ import annotations

import argparse
import csv
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import app  # noqa: E402
from backend.services.beta_invite_service import BetaInviteService  # noqa: E402


def _load_recipients(path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("CSV has no header row (expected email, first_name, code).")
        fields = {h.strip().lower(): h for h in reader.fieldnames if h}
        for key in ("email", "first_name", "code"):
            if key not in fields:
                raise SystemExit(f"CSV missing required column: {key}")
        em = fields["email"]
        fn = fields["first_name"]
        cd = fields["code"]
        for row in reader:
            out.append(
                {
                    "email": (row.get(em) or "").strip(),
                    "first_name": (row.get(fn) or "").strip(),
                    "code": (row.get(cd) or "").strip(),
                }
            )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a wave of beta invite emails.")
    parser.add_argument("--wave-label", required=True, help='e.g. "wave_1"')
    parser.add_argument("--csv-file", required=True, help="Path to CSV (email, first_name, code)")
    parser.add_argument(
        "--beta-url",
        default="https://mingusapp.com/beta",
        help="Beta landing URL for the CTA",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print recipients only; do not write queue or send",
    )
    args = parser.parse_args()

    recipients = _load_recipients(args.csv_file)
    with app.app_context():
        prep = BetaInviteService.prepare_wave(
            args.wave_label,
            recipients,
            dry_run=args.dry_run,
        )

    valid = prep["valid"]
    skipped = prep["skipped"]
    print(
        f"Prepared {len(valid)} invites for wave {args.wave_label}. "
        f"Skipped {len(skipped)}."
    )
    if skipped:
        for s in skipped:
            print(
                f"  skip: {s.get('email')} code={s.get('code')} — {s.get('reason')}",
                file=sys.stderr,
            )

    if args.dry_run:
        for v in valid:
            print(f"  {v.get('email')}\t{v.get('first_name')}\t{v.get('code')}")
        return

    with app.app_context():
        send = BetaInviteService.send_wave(args.wave_label, args.beta_url)
    print(
        f"Dispatched {send['dispatched']} emails to Celery queue for wave {args.wave_label}"
    )


if __name__ == "__main__":
    main()
