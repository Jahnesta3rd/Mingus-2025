#!/usr/bin/env python3
"""
Stub GET /api/vibe/daily — empty-state JSON until real implementation (#99).

Does not read memes or any other source; always returns has_vibe false.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from backend.auth.decorators import require_auth

vibe_daily_public_bp = Blueprint(
    "vibe_daily_public",
    __name__,
    url_prefix="/api/vibe",
)


@vibe_daily_public_bp.route("/daily", methods=["GET"])
@require_auth
def vibe_daily():
    return jsonify(
        {
            "has_vibe": False,
            "message": "No vibe content for today yet.",
        }
    )

