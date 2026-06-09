#!/usr/bin/env python3
"""
Checkup hub endpoints (#170).

All card answers upsert into LifeLedgerProfile for the authenticated user.
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from backend.auth.decorators import require_auth, get_current_user_id
from backend.models.database import db
from backend.models.user_models import User
from backend.services import checkup_hub_service as chs
from backend.services import life_ledger_service as lls

checkups_hub_bp = Blueprint("checkups_hub", __name__, url_prefix="/api/checkups")


def _resolve_user_id() -> int:
    uid = get_current_user_id()
    if uid is None:
        raise ValueError("Authentication required")
    if isinstance(uid, int):
        return uid
    user = User.query.filter_by(user_id=str(uid)).first()
    if user is None:
        user = User.query.get(uid)
    if user is None:
        raise ValueError("User not found")
    return user.id


def _commit_profile(profile, *, body_score=None, roof_score=None, vehicle_score=None):
    profile.life_ledger_score = lls.compute_life_ledger_score(profile)
    profile.updated_at = datetime.utcnow()
    db.session.commit()
    payload = {"ok": True, "updated_at": profile.updated_at.isoformat()}
    if body_score is not None:
        payload["body_score"] = body_score
    if roof_score is not None:
        payload["roof_score"] = roof_score
    if vehicle_score is not None:
        payload["vehicle_score"] = vehicle_score
    return jsonify(payload)


class BodyCheckupSchema(Schema):
    body_energy_rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    body_work_impact = fields.String(
        required=True,
        validate=validate.OneOf(["none", "minor", "moderate", "major", "severe"]),
    )
    body_ongoing_health_cost = fields.Boolean(required=True)


class MindMoodSchema(Schema):
    mood_stress_triggered_purchase = fields.String(
        required=True, validate=validate.OneOf(["yes", "no", "unsure"])
    )
    mood_avoided_finances = fields.Boolean(required=True)
    mood_coping_methods = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    spending_intentionality_rating = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )


class SpiritCalmSchema(Schema):
    practice_had_moments = fields.Boolean(required=True)
    practice_affected_finances = fields.String(
        required=True,
        validate=validate.OneOf(["not_at_all", "slightly", "moderately", "significantly"]),
    )
    spirit_financially_anxious = fields.String(
        required=True, validate=validate.OneOf(["yes", "no", "unsure"])
    )


class HousingCheckupSchema(Schema):
    housing_stability_rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    housing_tenure = fields.String(required=True, validate=validate.OneOf(["rent", "own"]))
    housing_lease_end_horizon = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            ["under_3mo", "3_6mo", "6_12mo", "over_12mo", "month_to_month"]
        ),
    )
    housing_cost_changed = fields.String(
        required=True,
        validate=validate.OneOf(["increased", "decreased", "same", "not_sure"]),
    )
    housing_down_payment_status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["not_saving", "started", "on_track", "ready"]),
    )
    housing_unexpected_cost = fields.Boolean(required=True)
    housing_unexpected_cost_amount = fields.Float(required=False, allow_none=True)

    @validates_schema
    def validate_conditionals(self, data, **kwargs):
        tenure = data.get("housing_tenure")
        if tenure == "rent" and not data.get("housing_lease_end_horizon"):
            raise ValidationError(
                {"housing_lease_end_horizon": ["Required when housing_tenure is rent"]}
            )
        if tenure == "own" and not data.get("housing_down_payment_status"):
            raise ValidationError(
                {"housing_down_payment_status": ["Required when housing_tenure is own"]}
            )
        if data.get("housing_unexpected_cost") and data.get("housing_unexpected_cost_amount") is None:
            raise ValidationError(
                {
                    "housing_unexpected_cost_amount": [
                        "Required when housing_unexpected_cost is true"
                    ]
                }
            )


class VehicleCheckupSchema(Schema):
    vehicle_satisfaction_rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    vehicle_maintenance_confidence = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )
    vehicle_recent_concern = fields.Boolean(required=True)
    vehicle_concern_description = fields.String(required=False, allow_none=True)
    vehicle_weekly_miles = fields.Integer(required=True, validate=validate.Range(min=0, max=2000))
    vehicle_last_service_horizon = fields.String(
        required=True,
        validate=validate.OneOf(["under_3mo", "3_6mo", "6_12mo", "over_12mo", "never"]),
    )
    vehicle_insurance_known = fields.Boolean(required=True)
    vehicle_insurance_premium = fields.Float(required=False, allow_none=True)
    vehicle_insurance_last_shopped = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["under_6mo", "6_12mo", "1_2yr", "over_2yr", "never"]),
    )
    vehicle_decision_horizon = fields.String(
        required=True,
        validate=validate.OneOf(
            ["keeping_years", "considering_replace", "actively_shopping", "unsure"]
        ),
    )
    vehicle_reliability_rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    vehicle_value_perception = fields.Integer(required=True, validate=validate.Range(min=1, max=5))

    @validates_schema
    def validate_conditionals(self, data, **kwargs):
        if data.get("vehicle_recent_concern") and not (data.get("vehicle_concern_description") or "").strip():
            raise ValidationError(
                {"vehicle_concern_description": ["Required when vehicle_recent_concern is true"]}
            )
        if data.get("vehicle_insurance_known"):
            if data.get("vehicle_insurance_premium") is None:
                raise ValidationError(
                    {"vehicle_insurance_premium": ["Required when vehicle_insurance_known is true"]}
                )
            if not data.get("vehicle_insurance_last_shopped"):
                raise ValidationError(
                    {
                        "vehicle_insurance_last_shopped": [
                            "Required when vehicle_insurance_known is true"
                        ]
                    }
                )


class RelationshipsCheckupSchema(Schema):
    relationship_friction_type = fields.String(
        required=True,
        validate=validate.OneOf(["communication", "money", "time", "trust", "other", "none"]),
    )
    relationship_spending_this_week = fields.Boolean(required=True)
    relationship_spending_amount = fields.Float(required=False, allow_none=True)
    relationship_spending_type = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["gifts", "dates", "travel", "shared_bills", "other"]),
    )
    relationship_direction = fields.String(
        required=True,
        validate=validate.OneOf(["improving", "stable", "uncertain", "declining"]),
    )
    relationship_cost_awareness = fields.String(
        required=True,
        validate=validate.OneOf(["very_aware", "somewhat", "rarely", "unaware"]),
    )
    relationship_future_intention = fields.String(
        required=True,
        validate=validate.OneOf(["invest_more", "maintain", "reevaluate", "step_back"]),
    )

    @validates_schema
    def validate_conditionals(self, data, **kwargs):
        if data.get("relationship_spending_this_week"):
            if data.get("relationship_spending_amount") is None:
                raise ValidationError(
                    {
                        "relationship_spending_amount": [
                            "Required when relationship_spending_this_week is true"
                        ]
                    }
                )
            if not data.get("relationship_spending_type"):
                raise ValidationError(
                    {
                        "relationship_spending_type": [
                            "Required when relationship_spending_this_week is true"
                        ]
                    }
                )


def _load_json():
    if not request.is_json:
        return None, (jsonify({"error": "JSON body required"}), 400)
    return request.get_json(), None


@checkups_hub_bp.route("/body", methods=["POST"])
@require_auth
def submit_body():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = BodyCheckupSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    score = chs.apply_body_checkup(profile, parsed)
    return _commit_profile(profile, body_score=score)


@checkups_hub_bp.route("/mind-mood", methods=["POST"])
@require_auth
def submit_mind_mood():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = MindMoodSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    chs.apply_mind_mood_checkup(profile, parsed)
    return _commit_profile(profile)


@checkups_hub_bp.route("/spirit-calm", methods=["POST"])
@require_auth
def submit_spirit_calm():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = SpiritCalmSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    chs.apply_spirit_calm_checkup(profile, parsed)
    return _commit_profile(profile)


@checkups_hub_bp.route("/housing-roof", methods=["POST"])
@require_auth
def submit_housing_roof():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = HousingCheckupSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    score = chs.apply_housing_checkup(profile, parsed)
    return _commit_profile(profile, roof_score=score)


@checkups_hub_bp.route("/vehicle", methods=["POST"])
@require_auth
def submit_vehicle():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = VehicleCheckupSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    score = chs.apply_vehicle_checkup(profile, parsed)
    return _commit_profile(profile, vehicle_score=score)


@checkups_hub_bp.route("/relationships", methods=["POST"])
@require_auth
def submit_relationships():
    data, err = _load_json()
    if err:
        return err
    try:
        parsed = RelationshipsCheckupSchema().load(data)
        user_id = _resolve_user_id()
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    profile = lls.get_or_create_profile(user_id)
    chs.apply_relationships_checkup(profile, parsed)
    return _commit_profile(profile)
