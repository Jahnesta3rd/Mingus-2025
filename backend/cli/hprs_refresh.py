#!/usr/bin/env python3
"""Flask CLI command for weekly HPRS score refresh."""

from __future__ import annotations

import json

from flask import Flask
from flask.cli import with_appcontext

from backend.services.hprs_service import refresh_hprs_scores


def register_hprs_cli(app: Flask) -> None:
    """Register HPRS refresh CLI commands on the Flask app."""

    @app.cli.command("refresh-hprs-scores")
    @with_appcontext
    def refresh_hprs_scores_cmd():
        """Weekly HPRS score refresh for all users with housing profiles."""
        result = refresh_hprs_scores()
        print(json.dumps(result, indent=2))
