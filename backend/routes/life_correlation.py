#!/usr/bin/env python3
"""Life Correlation API: observational summaries over LifeScoreSnapshot series."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.services import life_correlation_service as lcs

life_correlation_bp = Blueprint("life_correlation", __name__)

_TIER_PROFESSIONAL = "professional"
_TIER_MID = "mid_tier"
_TIER_BUDGET = "budget"

_UPGRADE_SUMMARY = (
    "Life Correlation analysis is available on the Professional plan. "
    "Upgrade to see full cross-domain insights."
)
_UPGRADE_SNAPSHOTS = (
    "Historical life snapshots for correlation are available on Mid tier and above. "
    "Upgrade to access this data."
)


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@life_correlation_bp.route("/summary", methods=["GET"])
@require_auth
def get_correlation_summary():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    tier = (user.tier or _TIER_BUDGET).strip().lower()
    if tier == _TIER_BUDGET:
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "message": _UPGRADE_SUMMARY,
                }
            ),
            403,
        )

    summary = lcs.generate_correlation_summary(user.id)

    if tier == _TIER_MID:
        return jsonify(
            {
                "has_sufficient_data": summary["has_sufficient_data"],
                "headline_insight": summary["headline_insight"],
                "correlations": [],
                "message": "Upgrade for full correlation analysis",
                "snapshots_count": summary["snapshots_count"],
            }
        )

    return jsonify(summary)


@life_correlation_bp.route("/snapshots", methods=["GET"])
@require_auth
def list_snapshots():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    tier = (user.tier or _TIER_BUDGET).strip().lower()
    if tier not in (_TIER_MID, _TIER_PROFESSIONAL):
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "message": _UPGRADE_SNAPSHOTS,
                }
            ),
            403,
        )

    snaps = lcs.get_snapshots(user.id, days=180)
    return jsonify(
        {
            "snapshots": [lcs.snapshot_to_dict(s) for s in snaps],
        }
    )
