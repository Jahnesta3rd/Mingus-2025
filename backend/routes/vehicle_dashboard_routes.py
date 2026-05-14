#!/usr/bin/env python3
"""
Public GET /api/vehicles/dashboard — aggregates vehicle list, maintenance predictions,
and lightweight stats for ``VehicleDashboardData`` (camelCase per frontend contract).
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

from flask import Blueprint, jsonify

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.models.vehicle_models import Vehicle

logger = logging.getLogger(__name__)

vehicle_dashboard_public_bp = Blueprint(
    "vehicle_dashboard_public",
    __name__,
    url_prefix="/api/vehicles",
)

_MTE: Any = None


def _maintenance_engine():
    """Lazy-load prediction engine (same service stack as ``vehicle_endpoints`` GET predictions)."""
    global _MTE
    if _MTE is None:
        from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

        _MTE = MaintenancePredictionEngine()
    return _MTE


def _default_quick_actions() -> list[dict[str, Any]]:
    return [
        {
            "id": "add-vehicle",
            "title": "Add a vehicle",
            "description": "Register VIN and basics",
            "icon": "car",
            "color": "blue",
            "enabled": True,
            "href": "/vehicles/add",
        },
        {
            "id": "maintenance",
            "title": "Maintenance outlook",
            "description": "Review predicted services",
            "icon": "wrench",
            "color": "purple",
            "enabled": True,
            "href": "/vehicles/maintenance",
        },
        {
            "id": "expenses",
            "title": "Vehicle expenses",
            "description": "Track fuel and repairs",
            "icon": "receipt",
            "color": "green",
            "enabled": True,
            "href": "/vehicles/expenses",
        },
    ]


def _empty_dashboard() -> dict[str, Any]:
    return {
        "vehicles": [],
        "stats": {
            "totalVehicles": 0,
            "totalMileage": 0,
            "averageMonthlyMiles": 0,
            "totalMonthlyBudget": 0,
            "upcomingMaintenanceCount": 0,
            "overdueMaintenanceCount": 0,
        },
        "upcomingMaintenance": [],
        "maintenancePredictions": [],
        # TODO: wire dedicated vehicle budget model/service when available
        "budgets": [],
        # TODO: wire vehicle_expenses or enhanced expense API when dashboard contract is finalized
        "recentExpenses": [],
        "quickActions": _default_quick_actions(),
    }


def _coerce_date(raw: Any) -> Optional[date]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        return date.fromisoformat(raw[:10])
    return None


def _vehicle_to_camel(v: Vehicle) -> dict[str, Any]:
    """Same fields as ``Vehicle.to_dict`` reshaped to frontend ``Vehicle`` (camelCase)."""
    return {
        "id": v.id,
        "vin": v.vin or "",
        "year": v.year,
        "make": v.make,
        "model": v.model,
        "trim": v.trim,
        "currentMileage": int(v.current_mileage or 0),
        "monthlyMiles": int(v.monthly_miles or 0),
        "userZipcode": v.user_zipcode or "",
        "assignedMsa": v.assigned_msa,
        "createdAt": v.created_date.isoformat() if v.created_date else "",
        "updatedAt": v.updated_date.isoformat() if v.updated_date else "",
    }


def _map_priority(priority_raw: Any) -> str:
    s = (str(priority_raw).lower().strip() if priority_raw is not None else "") or "medium"
    if s == "critical":
        return "urgent"
    if s in ("low", "medium", "high", "urgent"):
        return s
    return "medium"


def _map_maintenance_item_type(service_type: Any, maintenance_type: Any) -> str:
    """TS union is narrow; keep values conservative."""
    st = f"{service_type or ''} {maintenance_type or ''}".lower()
    if "oil" in st:
        return "oil_change"
    if "tire" in st or "rotation" in st:
        return "tire_rotation"
    if "brake" in st:
        return "brake_service"
    if "transmission" in st:
        return "transmission"
    if "inspect" in st:
        return "inspection"
    return "other"


def _prediction_to_dashboard_prediction(pred: dict[str, Any]) -> dict[str, Any]:
    """Normalize engine/DB row to ``MaintenancePrediction`` (camelCase)."""
    pid = pred.get("id")
    return {
        "id": int(pid) if pid is not None else 0,
        "vehicleId": int(pred.get("vehicle_id") or 0),
        "maintenanceType": str(
            pred.get("maintenance_type") or pred.get("service_type") or ""
        ),
        "predictedDate": _coerce_date(pred.get("predicted_date")).isoformat()
        if _coerce_date(pred.get("predicted_date"))
        else "",
        "confidence": float(pred.get("probability") or 0.0),
        "estimatedCost": float(pred.get("estimated_cost") or 0.0),
        "mileageAtService": int(pred.get("predicted_mileage") or 0),
        # TODO: expose structured factors from maintenance engine when available
        "factors": [],
    }


def _prediction_to_upcoming_item(pred: dict[str, Any], today: date) -> dict[str, Any]:
    """Map stored prediction row to ``MaintenanceItem`` (camelCase)."""
    pdate = _coerce_date(pred.get("predicted_date"))
    is_overdue = bool(pdate and pdate < today)
    est = float(pred.get("estimated_cost") or 0.0)
    pid = pred.get("id")
    return {
        "id": int(pid) if pid is not None else 0,
        "vehicleId": int(pred.get("vehicle_id") or 0),
        "type": _map_maintenance_item_type(
            pred.get("service_type"), pred.get("maintenance_type")
        ),
        "description": str(pred.get("description") or pred.get("service_type") or ""),
        "dueDate": pdate.isoformat() if pdate else "",
        "estimatedCost": est,
        "mileageThreshold": int(pred.get("predicted_mileage") or 0)
        if pred.get("predicted_mileage") is not None
        else None,
        "isOverdue": is_overdue,
        "priority": _map_priority(pred.get("priority")),
        "status": "overdue" if is_overdue else "scheduled",
        "notes": None,
    }


def _compute_stats(
    vehicles: list[Vehicle], flat_predictions: list[dict[str, Any]], today: date
) -> dict[str, Any]:
    n = len(vehicles)
    total_mileage = sum(int(v.current_mileage or 0) for v in vehicles)
    total_monthly = 0.0
    for v in vehicles:
        try:
            fc = float(v.monthly_fuel_cost) if v.monthly_fuel_cost is not None else 0.0
        except (TypeError, ValueError):
            fc = 0.0
        try:
            mp = float(v.monthly_payment) if v.monthly_payment is not None else 0.0
        except (TypeError, ValueError):
            mp = 0.0
        total_monthly += fc + mp
    avg_mm = 0
    if n > 0:
        avg_mm = int(round(sum(int(v.monthly_miles or 0) for v in vehicles) / n))

    upcoming = 0
    overdue = 0
    for pred in flat_predictions:
        pd = _coerce_date(pred.get("predicted_date"))
        if not pd:
            continue
        if pd < today:
            overdue += 1
        else:
            upcoming += 1

    return {
        "totalVehicles": n,
        "totalMileage": total_mileage,
        "averageMonthlyMiles": avg_mm,
        "totalMonthlyBudget": round(total_monthly, 2),
        "upcomingMaintenanceCount": upcoming,
        "overdueMaintenanceCount": overdue,
    }


@vehicle_dashboard_public_bp.route("/dashboard", methods=["GET"])
@require_auth
def vehicle_dashboard():
    """GET /api/vehicles/dashboard — thin aggregator; safe 200 defaults."""
    try:
        user = get_current_jwt_user()
        if not user:
            return jsonify(_empty_dashboard()), 200

        uid = int(user.id)
        vehicles = Vehicle.query.filter_by(user_id=uid).order_by(Vehicle.id).all()
        vehicles_out = [_vehicle_to_camel(v) for v in vehicles]

        today = date.today()
        flat_preds: list[dict[str, Any]] = []
        try:
            eng = _maintenance_engine()
            for v in vehicles:
                try:
                    preds = eng.get_predictions_for_vehicle(int(v.id))
                    for p in preds:
                        if isinstance(p, dict):
                            flat_preds.append(p)
                except Exception as ex:
                    logger.warning("predictions for vehicle %s: %s", v.id, ex)

        except Exception as ex:
            logger.warning("maintenance engine unavailable: %s", ex)

        maintenance_predictions_out = [
            _prediction_to_dashboard_prediction(p) for p in flat_preds
        ]

        # Next maintenance items by due date (soonest first), cap 5
        with_dates: list[tuple[date, dict[str, Any]]] = []
        for p in flat_preds:
            d = _coerce_date(p.get("predicted_date"))
            if d is not None:
                with_dates.append((d, p))
        with_dates.sort(key=lambda x: x[0])
        upcoming_maintenance = [
            _prediction_to_upcoming_item(p, today) for _, p in with_dates[:5]
        ]

        stats = _compute_stats(vehicles, flat_preds, today)

        payload: dict[str, Any] = {
            "vehicles": vehicles_out,
            "stats": stats,
            "upcomingMaintenance": upcoming_maintenance,
            "maintenancePredictions": maintenance_predictions_out,
            "budgets": [],
            "recentExpenses": [],
            "quickActions": _default_quick_actions(),
        }
        return jsonify(payload), 200
    except Exception as e:
        logger.exception("vehicle dashboard: %s", e)
        body = _empty_dashboard()
        body["error"] = "aggregation_failed"
        body["message"] = "Unable to load vehicle dashboard."
        return jsonify(body), 200
