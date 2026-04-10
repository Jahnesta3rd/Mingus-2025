#!/usr/bin/env python3
"""Backend-level Flask wiring: blueprints that live under ``backend/``."""

from backend.routes.admin import admin_bp
from backend.routes.admin_beta import admin_beta_bp
from backend.routes.beta import beta_bp
from backend.routes.feedback import feedback_bp
from backend.routes.life_correlation import life_correlation_bp
from backend.routes.life_ledger import life_ledger_bp
from backend.routes.telemetry import telemetry_bp
from backend.routes.vibe_tracker import vibe_tracker_bp
from backend.routes.spirit_finance import spirit_finance_bp
from backend.routes.transaction_schedule import transaction_schedule_bp


def register_backend_blueprints(app):
    """Register Flask blueprints owned by this package."""
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_beta_bp)
    app.register_blueprint(beta_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(life_ledger_bp, url_prefix="/api/life-ledger")
    app.register_blueprint(
        life_correlation_bp, url_prefix="/api/life-correlation"
    )
    app.register_blueprint(vibe_tracker_bp, url_prefix="/api/vibe-tracker")
    app.register_blueprint(spirit_finance_bp, url_prefix="/api/spirit")
    app.register_blueprint(
        transaction_schedule_bp, url_prefix="/api/transaction-schedule"
    )
