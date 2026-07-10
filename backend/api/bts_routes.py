#!/usr/bin/env python3
"""Back-to-school date setup, cash forecast, and purchase-plan API."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth
from backend.models.bts import BackToSchoolSession
from backend.models.database import db
from backend.services.bts_checkout_service import bts_checkout_service
from backend.services.bts_job_integration_service import (
    JOB_CATALOG,
    bts_job_integration_service,
)
from backend.services.bts_purchase_plan_service import bts_plan_service
from backend.services.bts_recommendation_service import bts_recommendation_service
from backend.services.bts_service import BTSService

logger = logging.getLogger(__name__)

bts_bp = Blueprint("bts", __name__)
bts_service = BTSService()


def _resolve_user_id(explicit: str | None = None) -> str:
    """Prefer explicit userId from the client; fall back to JWT claim."""
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    jwt_uid = getattr(g, "current_user_id", None)
    if jwt_uid is not None and str(jwt_uid).strip():
        return str(jwt_uid).strip()
    raise ValueError("userId is required")


def _load_owned_session(session_id: str, user_id: str) -> BackToSchoolSession:
    import uuid as uuid_mod

    try:
        session_uuid = uuid_mod.UUID(str(session_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid sessionId") from exc

    session = BackToSchoolSession.query.filter_by(session_id=session_uuid).first()
    if not session:
        raise LookupError("Session not found")
    if str(session.user_id) != str(user_id):
        raise PermissionError("Unauthorized")
    return session


def _session_reminder_payload(session_id: str) -> dict:
    """Reminder flags for purchase-plan / banner consumers."""
    import uuid as uuid_mod
    from datetime import date

    try:
        session_uuid = uuid_mod.UUID(str(session_id))
    except (TypeError, ValueError):
        return {}

    session = BackToSchoolSession.query.filter_by(session_id=session_uuid).first()
    if not session:
        return {}

    tier2_date = session.tier2_date
    today = date.today()
    date_reached = bool(tier2_date and today >= tier2_date)
    sent = bool(session.tier2_reminder_sent)
    dismissed = bool(session.tier2_reminder_dismissed)

    return {
        "tier1PurchasedAt": (
            session.tier1_purchased_at.isoformat() if session.tier1_purchased_at else None
        ),
        "tier2ReminderSent": sent,
        "tier2ReminderSentAt": (
            session.tier2_reminder_sent_at.isoformat()
            if session.tier2_reminder_sent_at
            else None
        ),
        "tier2ReminderDismissed": dismissed,
        "tier2Date": tier2_date.isoformat() if tier2_date else None,
        "tier2BudgetWithEarnings": (
            float(session.tier2_budget_with_earnings)
            if session.tier2_budget_with_earnings is not None
            else None
        ),
        "shouldShowTier2Reminder": bool(sent and not dismissed and date_reached),
    }


@bts_bp.route("/api/bts/setup", methods=["POST"])
@require_auth
def setup_bts_date():
    """
    Create back-to-school planning session.

    Request:
    {
      "userId": "user-123",
      "btsDate": "2026-08-28",
      "childName": "Emma",
      "childAge": 8,
      "childGender": "girl"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = _resolve_user_id(data.get("userId"))
        bts_raw = data.get("btsDate")
        if not bts_raw:
            raise ValueError("btsDate is required (YYYY-MM-DD)")
        bts_date = datetime.strptime(str(bts_raw)[:10], "%Y-%m-%d").date()

        child_age = data.get("childAge")
        if child_age is not None and child_age != "":
            try:
                child_age = int(child_age)
            except (TypeError, ValueError) as exc:
                raise ValueError("childAge must be an integer") from exc
        else:
            child_age = None

        result = bts_service.setup_bts_session(
            userId=user_id,
            btsDate=bts_date,
            childName=data.get("childName"),
            childAge=child_age,
            childGender=data.get("childGender"),
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS setup failed: %s", exc)
        return jsonify({"error": str(exc)}), 400


@bts_bp.route("/api/bts/forecast-timeline/<user_id>/<bts_date>", methods=["GET"])
@require_auth
def get_forecast_timeline(user_id, bts_date):
    """
    Get cash forecast for 3-week BTS planning window.

    Returns timeline of balances at:
    - Today
    - Tier 1 purchase date (BTS - 14 days)
    - Tier 2 purchase date (BTS - 7 days)
    - Tier 3 purchase date (BTS)
    """
    try:
        resolved = _resolve_user_id(user_id)
        bts_date_obj = datetime.strptime(str(bts_date)[:10], "%Y-%m-%d").date()
        timeline = bts_service.get_forecast_timeline(resolved, bts_date_obj)
        return jsonify(timeline), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS forecast timeline failed: %s", exc)
        return jsonify({"error": str(exc)}), 400


@bts_bp.route("/api/bts/generate-purchase-plan", methods=["POST"])
@require_auth
def generate_purchase_plan():
    """Generate tiered purchase plan from BTS1 session + capsule quantities."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("sessionId")
        capsule = data.get("capsule")

        if not session_id:
            return jsonify({"error": "sessionId required"}), 400
        if not capsule:
            return jsonify({"error": "capsule required"}), 400

        plan = bts_plan_service.generate_plan(session_id, capsule)
        return jsonify(plan), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS generate purchase plan failed: %s", exc)
        return jsonify({"error": f"Internal error: {exc}"}), 500


@bts_bp.route("/api/bts/purchase-plan/<session_id>", methods=["GET"])
@require_auth
def get_purchase_plan(session_id):
    """Retrieve existing purchase plan for a BTS session (flattened for UI)."""
    try:
        plan = bts_plan_service.get_plan(session_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        plan_data = plan.get("planData") if isinstance(plan, dict) else None
        if not isinstance(plan_data, dict):
            return jsonify({"error": "Invalid plan structure"}), 500

        reminder = _session_reminder_payload(session_id)
        return (
            jsonify(
                {
                    "status": "success",
                    "sessionId": plan.get("sessionId") or str(session_id),
                    "planId": plan.get("planId"),
                    **plan_data,
                    **reminder,
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS get purchase plan failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@bts_bp.route("/api/bts/recommendations/<tier>", methods=["POST"])
@require_auth
def get_recommendations(tier):
    """Generate product recommendations for a purchase-plan tier."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("sessionId")
        # Allow tier from path or body; path wins when both present.
        tier_arg = tier or data.get("tier")
        if not session_id:
            return jsonify({"error": "sessionId required"}), 400
        if tier_arg not in ("tier1", "tier2", "tier3"):
            return jsonify({"error": "tier must be tier1, tier2, or tier3"}), 400

        recommendations = bts_recommendation_service.generate_recommendations(
            session_id, tier_arg
        )
        return jsonify(recommendations), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS recommendations failed: %s", exc)
        return jsonify({"error": f"Internal error: {exc}"}), 500


@bts_bp.route("/api/bts/recommendations/<tier>/<session_id>", methods=["GET"])
@require_auth
def get_stored_recommendations(tier, session_id):
    """Retrieve previously stored recommendations for a session + tier."""
    try:
        if tier not in ("tier1", "tier2", "tier3"):
            return jsonify({"error": "tier must be tier1, tier2, or tier3"}), 400
        stored = bts_recommendation_service.get_recommendations(session_id, tier)
        if not stored:
            return jsonify({"error": "Recommendations not found"}), 404
        return jsonify({"status": "success", "recommendation": stored}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("BTS get stored recommendations failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@bts_bp.route("/api/bts/checkout/create-payment-intent", methods=["POST"])
@require_auth
def create_payment_intent():
    """Create Stripe PaymentIntent for BTS Tier 1 checkout."""
    try:
        data = request.get_json(silent=True) or {}
        total = data.get("total")
        if total is None:
            return jsonify({"error": "total is required", "code": "PAYMENT_INTENT_FAILED"}), 400

        user_id = _resolve_user_id(data.get("userId"))
        result = bts_checkout_service.create_payment_intent(
            float(total),
            session_id=data.get("sessionId"),
            user_id=user_id,
            tier=int(data.get("tier") or 1),
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "PAYMENT_INTENT_FAILED"}), 400
    except Exception as exc:
        logger.exception("BTS create payment intent failed: %s", exc)
        return jsonify({"error": str(exc), "code": "PAYMENT_INTENT_FAILED"}), 500


@bts_bp.route("/api/bts/checkout/validate-coupon", methods=["POST"])
@require_auth
def validate_coupon():
    """Validate MVP coupon code and return discount percent."""
    try:
        data = request.get_json(silent=True) or {}
        coupon_code = data.get("couponCode")
        if not coupon_code:
            return jsonify({"error": "Coupon code required", "code": "COUPON_INVALID"}), 400
        result = bts_checkout_service.validate_coupon(coupon_code)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "COUPON_INVALID"}), 400
    except Exception as exc:
        logger.exception("BTS validate coupon failed: %s", exc)
        return jsonify({"error": str(exc), "code": "COUPON_ERROR"}), 500


@bts_bp.route("/api/bts/checkout/submit", methods=["POST"])
@require_auth
def submit_checkout():
    """
    Finalize checkout after Stripe payment succeeds.

    Body: sessionId, tier, cartItems, shippingAddress, paymentIntentId,
          subtotal, couponCode (optional)
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = _resolve_user_id(data.get("userId"))

        session_id = data.get("sessionId")
        tier = data.get("tier")
        cart_items = data.get("cartItems")
        shipping_address = data.get("shippingAddress")
        payment_intent_id = data.get("paymentIntentId")
        subtotal = data.get("subtotal")
        coupon_code = data.get("couponCode")

        if not all(
            [
                session_id,
                tier is not None,
                cart_items,
                shipping_address,
                payment_intent_id,
                subtotal is not None,
            ]
        ):
            return jsonify({"error": "Missing required fields", "code": "CHECKOUT_ERROR"}), 400

        order = bts_checkout_service.create_order(
            session_id=session_id,
            user_id=user_id,
            tier=tier,
            cart_items=cart_items,
            shipping_address=shipping_address,
            payment_intent_id=payment_intent_id,
            subtotal=float(subtotal),
            coupon_code=coupon_code,
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "orderId": order["orderId"],
                    "order": order,
                    "message": "Order created successfully",
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "CHECKOUT_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS checkout submit failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/order/<order_id>", methods=["GET"])
@require_auth
def get_order(order_id):
    """Fetch a BTS purchase order by ID (owner only)."""
    try:
        user_id = _resolve_user_id()
        order = bts_checkout_service.get_order(order_id, user_id=user_id)
        return jsonify(order), 200
    except ValueError as exc:
        msg = str(exc)
        status = 404 if "not found" in msg.lower() else 400
        return jsonify({"error": msg}), status
    except Exception as exc:
        logger.exception("BTS get order failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@bts_bp.route("/api/bts/job-commitment", methods=["POST"])
@require_auth
def create_job_commitment():
    """
    Create/update a side-job commitment for a BTS session.

    Body: sessionId, jobId, jobTitle, tier2Date, tier2BaseBudget, targetEarnings
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = _resolve_user_id(data.get("userId"))

        session_id = data.get("sessionId")
        job_id = data.get("jobId")
        job_title = data.get("jobTitle")
        tier2_date_raw = data.get("tier2Date")
        tier2_base_budget = data.get("tier2BaseBudget")
        target_earnings = data.get("targetEarnings")

        if not all(
            [
                session_id,
                job_id,
                job_title,
                tier2_date_raw,
                tier2_base_budget is not None,
                target_earnings is not None,
            ]
        ):
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "code": "VALIDATION_ERROR",
                    }
                ),
                400,
            )

        tier2_date = datetime.strptime(str(tier2_date_raw)[:10], "%Y-%m-%d").date()
        result = bts_job_integration_service.create_commitment(
            session_id=session_id,
            user_id=user_id,
            job_id=job_id,
            job_title=job_title,
            tier2_date=tier2_date,
            tier2_base_budget=float(tier2_base_budget),
            target_earnings=float(target_earnings),
        )
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS create job commitment failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/job-commitment/<session_id>", methods=["GET"])
@require_auth
def get_job_commitment(session_id):
    """Get job commitment for a session (if exists)."""
    try:
        user_id = _resolve_user_id()
        commitment = bts_job_integration_service.get_commitment(
            session_id, user_id=user_id
        )
        if not commitment:
            return jsonify({"status": "no_commitment"}), 200
        return jsonify(commitment), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS get job commitment failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/tier2-status/<session_id>", methods=["GET"])
@require_auth
def get_tier2_status(session_id):
    """Get Tier 2 readiness status (earnings progress + date gate)."""
    try:
        user_id = _resolve_user_id()
        status = bts_job_integration_service.get_tier2_status(
            session_id, user_id=user_id
        )
        return jsonify(status), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS tier2 status failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/tier2-decision/<session_id>", methods=["POST"])
@require_auth
def tier2_decision(session_id):
    """Record proceed / defer / skip for Tier 2 shopping."""
    try:
        data = request.get_json(silent=True) or {}
        user_id = _resolve_user_id(data.get("userId"))
        decision = data.get("decision")
        result = bts_job_integration_service.record_decision(
            session_id, user_id, decision
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS tier2 decision failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/job-catalog", methods=["GET"])
@require_auth
def get_job_catalog():
    """MVP job options for the BTS job picker."""
    return jsonify({"jobs": JOB_CATALOG}), 200


@bts_bp.route("/api/bts/tier2-reminder/<session_id>", methods=["GET"])
@require_auth
def get_tier2_reminder(session_id):
    """Fetch Tier 2 reminder banner state for a session."""
    try:
        user_id = _resolve_user_id()
        session = _load_owned_session(session_id, user_id)
        payload = _session_reminder_payload(str(session.session_id))
        commitment = bts_job_integration_service.get_commitment(
            str(session.session_id), user_id=user_id
        )
        # Prefer plan tier2 budget when session denormalized value is empty
        base_budget = None
        plan = bts_plan_service.get_plan(session_id)
        plan_data = plan.get("planData") if isinstance(plan, dict) else None
        if isinstance(plan_data, dict):
            base_budget = (plan_data.get("tier2") or {}).get("budget")

        return (
            jsonify(
                {
                    "status": "success",
                    "sessionId": str(session.session_id),
                    **payload,
                    "tier2BaseBudget": (
                        float(base_budget) if base_budget is not None else None
                    ),
                    "commitment": commitment,
                }
            ),
            200,
        )
    except LookupError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except PermissionError as exc:
        return jsonify({"error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        logger.exception("BTS get tier2 reminder failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@bts_bp.route("/api/bts/dismiss-tier2-reminder/<session_id>", methods=["POST"])
@require_auth
def dismiss_tier2_reminder(session_id):
    """User dismisses the Tier 2 reminder banner (persists across refresh)."""
    try:
        user_id = _resolve_user_id()
        session = _load_owned_session(session_id, user_id)
        session.tier2_reminder_dismissed = True
        db.session.commit()
        return jsonify({"status": "dismissed"}), 200
    except LookupError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except PermissionError as exc:
        return jsonify({"error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 400
    except Exception as exc:
        db.session.rollback()
        logger.exception("BTS dismiss tier2 reminder failed: %s", exc)
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
