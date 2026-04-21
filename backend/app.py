#!/usr/bin/env python3
"""Backend-level Flask wiring: blueprints that live under ``backend/``."""

from backend.routes.admin import admin_bp
from backend.routes.admin_beta import admin_beta_bp
from backend.routes.beta import beta_bp
from backend.routes.feedback import feedback_bp
from backend.routes.life_correlation import life_correlation_bp
from backend.routes.life_ledger import life_ledger_bp
from backend.routes.life_ready_score import life_ready_score_bp
from backend.routes.self_card import self_card_bp
from backend.routes.telemetry import telemetry_bp
from backend.routes.vibe_tracker import vibe_tracker_bp
from backend.routes.connection_trend import connection_trend_bp
from backend.routes.alerts import alerts_bp
from backend.routes.spirit_finance import spirit_finance_bp
from backend.routes.transaction_schedule import transaction_schedule_bp
from backend.routes.faith_card import faith_card_bp
from backend.routes.bug_report import bug_report_bp
from backend.routes.modular_onboarding import modular_onboarding_bp
from backend.routes.user import user_bp as user_agreement_bp
from backend.models.onboarding_progress import OnboardingProgress  # noqa: F401


def register_backend_blueprints(app):
    """Register Flask blueprints owned by this package."""
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_beta_bp)
    app.register_blueprint(beta_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(life_ledger_bp, url_prefix="/api/life-ledger")
    app.register_blueprint(life_ready_score_bp)
    app.register_blueprint(self_card_bp, url_prefix="/api")
    app.register_blueprint(
        life_correlation_bp, url_prefix="/api/life-correlation"
    )
    app.register_blueprint(vibe_tracker_bp, url_prefix="/api/vibe-tracker")
    app.register_blueprint(
        connection_trend_bp, url_prefix="/api/connection-trend"
    )
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(spirit_finance_bp, url_prefix="/api/spirit")
    app.register_blueprint(
        transaction_schedule_bp, url_prefix="/api/transaction-schedule"
    )
    app.register_blueprint(faith_card_bp)
    app.register_blueprint(bug_report_bp)
    app.register_blueprint(modular_onboarding_bp)
    app.register_blueprint(user_agreement_bp)
