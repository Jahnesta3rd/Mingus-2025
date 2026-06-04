#!/usr/bin/env python3
"""Backfill BLS career field classification for existing career profiles."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import app  # noqa: E402
from backend.models.career_profile import CareerProfile  # noqa: E402
from backend.models.database import db  # noqa: E402
from backend.models.llm_usage import LlmUsage  # noqa: E402
from backend.services.career_title_classifier import classify_career_title  # noqa: E402


def main() -> None:
    script_start = datetime.utcnow()

    with app.app_context():
        profiles = (
            CareerProfile.query.filter(
                CareerProfile.bls_career_field.is_(None),
                CareerProfile.current_role.isnot(None),
            )
            .order_by(CareerProfile.user_id)
            .all()
        )
        n = len(profiles)
        print(f"Found {n} profiles to classify")

        for i, profile in enumerate(profiles, start=1):
            raw = profile.current_role or ""
            result = classify_career_title(
                raw_title=raw,
                raw_industry=profile.industry,
                user_id=profile.user_id,
                db_session=db.session,
            )
            if result.get("confidence", 0) >= 0.5:
                profile.bls_career_field = result["career_field"]
                profile.seniority_level = result["seniority_level"]
                profile.is_management = result["is_management"]
                profile.title_normalized_at = datetime.utcnow()
                profile.title_normalization_source = result.get("source", "llm")
                db.session.commit()

            print(
                f'[{i}/{n}] user={profile.user_id}: "{raw}" -> '
                f'{result.get("career_field")} ({result.get("source")})'
            )
            time.sleep(0.2)

        usage_rows = (
            LlmUsage.query.filter(LlmUsage.created_at >= script_start).all()
        )
        llm_count = sum(1 for r in usage_rows if r.classification_source == "llm")
        rule_count = sum(1 for r in usage_rows if r.classification_source == "rule")
        error_count = sum(
            1 for r in usage_rows if r.classification_source == "fallback_on_error"
        )
        total_tokens = sum(r.total_tokens for r in usage_rows)
        total_cost = sum(float(r.cost_usd or 0) for r in usage_rows)

        print(f"LLM classified: {llm_count}")
        print(f"Rule-based: {rule_count}")
        print(f"Error fallbacks: {error_count}")
        print(f"Total tokens used: {total_tokens}")
        print(f"Estimated cost: ${total_cost:.4f}")


if __name__ == "__main__":
    main()
