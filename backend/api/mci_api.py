#!/usr/bin/env python3
"""
Public API for Mingus Conditions Index (MCI).
"""

from __future__ import annotations

import os
import sys
import logging
from flask import Blueprint, jsonify

from flask_cors import cross_origin

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.auth.decorators import require_auth
from services.mci_cache import get_history, get_or_fetch_mci

logger = logging.getLogger(__name__)


mci_api = Blueprint("mci_api", __name__)


@mci_api.route("/api/mci/snapshot", methods=["GET"])
@cross_origin()
def mci_snapshot():
    """
    Return full MCI snapshot as JSON.
    """
    data = get_or_fetch_mci()
    resp = jsonify(data)
    # Explicit caching header for public benchmark data.
    resp.headers["Cache-Control"] = "max-age=86400"
    return resp, 200


@mci_api.route("/api/mci/history", methods=["GET"])
@cross_origin()
@require_auth
def mci_history():
    """
    Return weekly MCI history array as JSON.
    """
    history = get_history()
    resp = jsonify(history)
    resp.headers["Cache-Control"] = "max-age=3600"
    return resp, 200

