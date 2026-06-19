#!/usr/bin/env python3
"""Backend-level Flask wiring: blueprints that live under ``backend/``."""

from backend.routes.admin import admin_bp
from backend.routes.admin_beta import admin_beta_bp
from backend.routes.admin_pmf import admin_pmf_bp, admin_sean_ellis_bp
from backend.routes.beta import beta_bp
from backend.routes.feedback import feedback_bp
from backend.routes.life_correlation import life_correlation_bp
from backend.routes.life_ledger import life_ledger_bp
from backend.routes.life_ready_score import life_ready_score_bp
from backend.routes.self_card import self_card_bp
from backend.routes.telemetry import telemetry_bp
from backend.routes.vibe_tracker import vibe_tracker_bp
from backend.routes.relationship_check import relationship_check_bp
from backend.routes.connection_trend import connection_trend_bp
from backend.routes.alerts import alerts_bp
from backend.routes.spirit_finance import spirit_finance_bp
from backend.routes.transaction_schedule import transaction_schedule_bp
from backend.routes.faith_card import faith_card_bp
from backend.routes.bug_report import bug_report_bp
from backend.routes.modular_onboarding import modular_onboarding_bp
from backend.routes.user import user_bp as user_agreement_bp
from backend.routes.vehicle_dashboard_routes import vehicle_dashboard_public_bp
from backend.routes.vin_advisor import vin_advisor_bp
from backend.routes.hprs import hprs_bp
import backend.routes.housing  # noqa: F401 — registers HPRS action routes on hprs_bp
from backend.routes.vibe_daily_routes import vibe_daily_public_bp
from backend.routes.checkups_hub_api import checkups_hub_bp
from backend.routes.waterfall_context_api import waterfall_context_bp
from backend.routes.plaid_api import plaid_bp
from backend.routes.wellness_routes import wellness_public_bp
from backend.routes.gamification_routes import gamification_public_bp
from backend.routes.user_activity_routes import user_activity_public_bp
from backend.routes.daily_outlook_routes import daily_outlook_public_bp
from backend.models.onboarding_progress import OnboardingProgress  # noqa: F401
from backend.models.database import db
from backend.api.employer_health import employer_health_api
from backend.routes.parent_checklist import parent_checklist_bp
from backend.routes.articles import articles_bp
from backend.routes.debt_analyzer import debt_analyzer_bp
from backend.routes.second_job_advisor import second_job_advisor_bp
from backend.api.health_insurance_endpoints import health_insurance_bp
from backend.routes.expenses_summary import expenses_summary_bp
from backend.routes.quick_spend_api import quick_spend_bp
from backend.cli.employer_refresh import register_employer_cli
from backend.cli.hprs_refresh import register_hprs_cli
from backend.cli.warn_scan import scan_warn_notices


def register_backend_blueprints(app):
    """Register Flask blueprints owned by this package."""

    @app.teardown_request
    def rollback_on_exception(exception):
        if exception is not None:
            db.session.rollback()

    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_beta_bp)
    app.register_blueprint(admin_pmf_bp)
    app.register_blueprint(admin_sean_ellis_bp)
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
        relationship_check_bp, url_prefix="/api/relationship-check"
    )
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
    app.register_blueprint(wellness_public_bp)
    app.register_blueprint(gamification_public_bp)
    app.register_blueprint(user_activity_public_bp)
    app.register_blueprint(daily_outlook_public_bp)
    # Vehicle dashboard GET /api/vehicles/dashboard (alongside ``vehicle_api`` in root app).
    app.register_blueprint(vehicle_dashboard_public_bp)
    app.register_blueprint(vin_advisor_bp)
    app.register_blueprint(hprs_bp)
    # Stub GET /api/vibe/daily — placeholder for #99.
    app.register_blueprint(vibe_daily_public_bp)
    app.register_blueprint(checkups_hub_bp)
    app.register_blueprint(waterfall_context_bp)
    app.register_blueprint(plaid_bp)
    app.register_blueprint(employer_health_api)
    app.register_blueprint(parent_checklist_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(debt_analyzer_bp)
    app.register_blueprint(second_job_advisor_bp)
    app.register_blueprint(health_insurance_bp)
    app.register_blueprint(expenses_summary_bp)
    app.register_blueprint(quick_spend_bp)
    register_employer_cli(app)
    register_hprs_cli(app)
    app.cli.add_command(scan_warn_notices)
