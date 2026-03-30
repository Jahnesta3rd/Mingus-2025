#!/usr/bin/env python3
"""Feature ratings and NPS survey API (JWT)."""

from datetime import datetime

from flask import Blueprint, jsonify, request, g

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.feedback import FeatureRating, NPSSurvey
from backend.models.user_models import User

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@feedback_bp.route("/feature-rating", methods=["POST"])
@require_auth
def feature_rating():
    data = request.get_json(silent=True) or {}
    feature_name = (data.get("feature_name") or "").strip()
    rating = (data.get("rating") or "").strip().lower()
    comment = data.get("comment")
    if comment is not None:
        comment = str(comment).strip() or None

    if not feature_name or len(feature_name) > 100:
        return jsonify({"error": "Invalid feature_name"}), 400
    if rating not in ("up", "down"):
        return jsonify({"error": 'rating must be "up" or "down"'}), 400

    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    tier = (user.tier or "")[:20] if user.tier else ""

    existing = FeatureRating.query.filter_by(
        user_id=user.id, feature_name=feature_name
    ).first()
    now = datetime.utcnow()
    if existing:
        existing.rating = rating
        existing.comment = comment
        existing.created_at = now
        existing.user_tier = tier
    else:
        db.session.add(
            FeatureRating(
                user_id=user.id,
                feature_name=feature_name,
                rating=rating,
                comment=comment,
                created_at=now,
                user_tier=tier,
            )
        )
    db.session.commit()
    return jsonify({"success": True}), 200


@feedback_bp.route("/nps", methods=["POST"])
@require_auth
def nps_submit():
    data = request.get_json(silent=True) or {}
    try:
        score = int(data.get("score"))
    except (TypeError, ValueError):
        return jsonify({"error": "score must be an integer 0-10"}), 400
    if score < 0 or score > 10:
        return jsonify({"error": "score must be between 0 and 10"}), 400

    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if NPSSurvey.query.filter_by(user_id=user.id).first():
        return jsonify({"error": "Already submitted"}), 409

    mvf = data.get("most_valuable_feature")
    if mvf is not None:
        mvf = str(mvf).strip()[:100] or None
    lvf = data.get("least_valuable_feature")
    if lvf is not None:
        lvf = str(lvf).strip()[:100] or None
    would_pay = data.get("would_pay")
    if would_pay is not None:
        would_pay = str(would_pay).strip().lower()[:10] or None
        if would_pay and would_pay not in ("yes", "no", "maybe"):
            return jsonify({"error": 'would_pay must be "yes", "no", or "maybe"'}), 400

    price_willing = data.get("price_willing")
    if price_willing is not None:
        try:
            price_willing = int(price_willing)
        except (TypeError, ValueError):
            return jsonify({"error": "price_willing must be an integer"}), 400

    additional = data.get("additional_comments")
    if additional is not None:
        additional = str(additional).strip() or None
        if additional and len(additional) > 500:
            return jsonify({"error": "additional_comments max 500 characters"}), 400

    db.session.add(
        NPSSurvey(
            user_id=user.id,
            score=score,
            most_valuable_feature=mvf,
            least_valuable_feature=lvf,
            would_pay=would_pay,
            price_willing=price_willing,
            additional_comments=additional,
            submitted_at=datetime.utcnow(),
        )
    )
    db.session.commit()
    return jsonify({"success": True}), 200


@feedback_bp.route("/nps/status", methods=["GET"])
@require_auth
def nps_status():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    submitted = NPSSurvey.query.filter_by(user_id=user.id).first() is not None
    created = user.created_at or datetime.utcnow()
    delta = datetime.utcnow() - created
    days_since_beta_start = max(0, delta.days)

    should_show = bool(
        user.is_beta and days_since_beta_start >= 7 and not submitted
    )

    return (
        jsonify(
            {
                "submitted": submitted,
                "days_since_beta_start": days_since_beta_start,
                "should_show_survey": should_show,
            }
        ),
        200,
    )
