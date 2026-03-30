#!/usr/bin/env python3
"""Backend-level Flask wiring: blueprints that live under ``backend/``."""

from backend.routes.beta import beta_bp
from backend.routes.feedback import feedback_bp
from backend.routes.telemetry import telemetry_bp


def register_backend_blueprints(app):
    """Register Flask blueprints owned by this package."""
    app.register_blueprint(beta_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(telemetry_bp)
