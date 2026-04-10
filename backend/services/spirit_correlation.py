#!/usr/bin/env python3
"""Spirit practice vs. finance signals: weekly aggregates and Pearson correlations."""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from statistics import mean
from typing import Any

from loguru import logger
from sqlalchemy import cast
from sqlalchemy.types import Date

from backend.models.database import db
from backend.models.financial_setup import UserIncome
from backend.models.spirit_checkin import (
    SpiritCheckin,
    SpiritFinanceCorrelation,
)
from backend.models.wellness import WeeklyCheckin


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _iso_week_label(monday: date) -> str:
    y, w, _ = monday.isocalendar()
    return f"{y}-W{w:02d}"


def _iter_week_windows(num_weeks: int, end_date: date) -> list[tuple[str, date, date]]:
    """(week_label, monday, sunday) from oldest to newest, ending at week containing end_date."""
    current_monday = _week_monday(end_date)
    first_monday = current_monday - timedelta(weeks=num_weeks - 1)
    out: list[tuple[str, date, date]] = []
    for i in range(num_weeks):
        mon = first_monday + timedelta(weeks=i)
        sun = mon + timedelta(days=6)
        out.append((_iso_week_label(mon), mon, sun))
    return out


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _user_monthly_income(user_id: int) -> float | None:
    rows = UserIncome.query.filter_by(user_id=user_id, is_active=True).all()
    total = 0.0
    for r in rows:
        a = _to_float(r.amount)
        if a is None:
            continue
        freq = (r.frequency or "").lower()
        if freq == "monthly":
            total += a
        elif freq == "biweekly":
            total += a * 26.0 / 12.0
        elif freq == "weekly":
            total += a * 52.0 / 12.0
        elif freq == "annual":
            total += a / 12.0
    return total if total > 0 else None


class SpiritCorrelationEngine:
    """Compute weekly spirit/finance series and persist SpiritFinanceCorrelation rows."""

    @staticmethod
    def week_windows(num_weeks: int, end_date: date) -> list[tuple[str, date, date]]:
        return _iter_week_windows(num_weeks, end_date)

    def compute_pearson(self, x_list: list[float | None], y_list: list[float | None]) -> float | None:
        if len(x_list) != len(y_list):
            return None
        pairs: list[tuple[float, float]] = []
        for x, y in zip(x_list, y_list):
            if x is None or y is None:
                continue
            try:
                pairs.append((float(x), float(y)))
            except (TypeError, ValueError):
                continue
        n = len(pairs)
        if n < 4:
            return None
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mx = mean(xs)
        my = mean(ys)
        dx = [a - mx for a in xs]
        dy = [b - my for b in ys]
        var_x = sum(a * a for a in dx)
        var_y = sum(b * b for b in dy)
        if var_x == 0.0 or var_y == 0.0:
            return None
        cov = sum(dx[i] * dy[i] for i in range(n))
        denom = math.sqrt(var_x * var_y)
        if denom == 0.0:
            return None
        return cov / denom

    def get_weekly_practice_scores(
        self, user_id: int, weeks: int = 8
    ) -> list[dict[str, Any]]:
        try:
            today = _utc_today()
            windows = _iter_week_windows(weeks, today)
            result: list[dict[str, Any]] = []
            for label, mon, sun in windows:
                rows = (
                    SpiritCheckin.query.filter(
                        SpiritCheckin.user_id == user_id,
                        SpiritCheckin.checked_in_date >= mon,
                        SpiritCheckin.checked_in_date <= sun,
                    )
                    .order_by(SpiritCheckin.checked_in_date.asc())
                    .all()
                )
                cnt = len(rows)
                if cnt:
                    score = mean(float(c.practice_score) for c in rows)
                else:
                    score = 0.0
                result.append(
                    {
                        "week_label": label,
                        "practice_score": round(score, 4),
                        "checkin_count": cnt,
                    }
                )
            return result
        except Exception as e:
            logger.error(f"get_weekly_practice_scores failed for user {user_id}: {e}")
            return []

    def get_weekly_financial_data(
        self, user_id: int, weeks: int = 8
    ) -> list[dict[str, Any]]:
        try:
            today = _utc_today()
            windows = _iter_week_windows(weeks, today)
            monthly_in = _user_monthly_income(user_id)
            weekly_income = (monthly_in * 12.0 / 52.0) if monthly_in else None

            result: list[dict[str, Any]] = []
            for label, mon, sun in windows:
                wc = WeeklyCheckin.query.filter_by(
                    user_id=user_id, week_ending_date=sun
                ).first()
                if not wc:
                    result.append(
                        {
                            "week_label": label,
                            "savings_rate": None,
                            "impulse_spend": None,
                            "stress_index": None,
                            "bills_ontime": None,
                        }
                    )
                    continue

                stress = _to_float(wc.stress_level)
                impulse = _to_float(wc.impulse_spending)

                savings_rate: float | None = None
                if weekly_income and weekly_income > 0:
                    parts = [
                        wc.groceries_estimate,
                        wc.dining_estimate,
                        wc.entertainment_estimate,
                        wc.shopping_estimate,
                        wc.transport_estimate,
                        wc.utilities_estimate,
                        wc.other_estimate,
                    ]
                    spend = 0.0
                    for p in parts:
                        f = _to_float(p)
                        if f is not None:
                            spend += f
                    savings_rate = (weekly_income - spend) / weekly_income

                bills = _to_float(wc.spending_control)
                bills_ontime = (bills / 10.0) if bills is not None else None

                result.append(
                    {
                        "week_label": label,
                        "savings_rate": savings_rate,
                        "impulse_spend": impulse,
                        "stress_index": stress,
                        "bills_ontime": bills_ontime,
                    }
                )
            return result
        except Exception as e:
            logger.error(f"get_weekly_financial_data failed for user {user_id}: {e}")
            return []

    def _build_insight_strings(
        self,
        corr_s: float | None,
        corr_i: float | None,
        corr_st: float | None,
        practice_weeks: list[dict[str, Any]],
        fin_weeks: list[dict[str, Any]],
        total_checkins: int,
        avg_high: float | None,
        avg_impulse_hi: float | None,
        avg_impulse_lo: float | None,
        avg_stress_miss_weeks: float | None,
        avg_stress_practice_weeks: float | None,
    ) -> list[str]:
        insights: list[str] = []
        by_label = {f["week_label"]: f for f in fin_weeks}

        if corr_s is not None and corr_s > 0.5:
            hi_sav: list[float] = []
            lo_sav: list[float] = []
            for pw in practice_weeks:
                label = pw["week_label"]
                fin = by_label.get(label) or {}
                sr = fin.get("savings_rate")
                if sr is None:
                    continue
                if pw["checkin_count"] >= 5:
                    hi_sav.append(float(sr))
                elif pw["checkin_count"] == 0:
                    lo_sav.append(float(sr))
            if hi_sav and lo_sav:
                diff = (mean(hi_sav) - mean(lo_sav)) * 100.0
                insights.append(
                    "On weeks you check in 5+ times, your savings rate is "
                    f"{abs(diff):.1f}% higher than weeks you miss your practice."
                )

        if corr_i is not None and corr_i < -0.4:
            y = 0.0
            if avg_impulse_hi is not None and avg_impulse_lo is not None:
                y = max(0.0, float(avg_impulse_lo) - float(avg_impulse_hi))
            insights.append(
                "Days with a check-in average "
                f"${y:.0f} less in impulse spending than days without."
            )

        if corr_st is not None and corr_st < -0.5:
            z = (
                avg_stress_miss_weeks
                if avg_stress_miss_weeks is not None
                else 0.0
            )
            w = (
                avg_stress_practice_weeks
                if avg_stress_practice_weeks is not None
                else 0.0
            )
            insights.append(
                "Your financial stress index drops from "
                f"{z:.1f} to {w:.1f} on weeks with consistent practice."
            )

        insights.append(
            f"You have completed {total_checkins} check-ins over the last 8 weeks."
        )
        return insights

    def refresh_correlation(self, user_id: int) -> SpiritFinanceCorrelation | None:
        try:
            weeks_n = 8
            practice_weeks = self.get_weekly_practice_scores(user_id, weeks=weeks_n)
            fin_weeks = self.get_weekly_financial_data(user_id, weeks=weeks_n)

            labels = [p["week_label"] for p in practice_weeks]
            p_scores = [float(p["practice_score"]) for p in practice_weeks]
            by_label_fin = {f["week_label"]: f for f in fin_weeks}
            savings = [by_label_fin.get(l, {}).get("savings_rate") for l in labels]
            impulse = [by_label_fin.get(l, {}).get("impulse_spend") for l in labels]
            stress = [by_label_fin.get(l, {}).get("stress_index") for l in labels]
            bills = [by_label_fin.get(l, {}).get("bills_ontime") for l in labels]

            corr_s = self.compute_pearson(p_scores, savings)
            corr_i = self.compute_pearson(p_scores, impulse)
            corr_st = self.compute_pearson(p_scores, stress)
            corr_b = self.compute_pearson(p_scores, bills)

            hi_practice_scores: list[float] = []
            lo_practice_scores: list[float] = []
            impulse_hi_weeks: list[float] = []
            impulse_lo_weeks: list[float] = []
            stress_practice_weeks: list[float] = []
            stress_miss_weeks: list[float] = []

            for pw in practice_weeks:
                label = pw["week_label"]
                fin = by_label_fin.get(label) or {}
                ps = float(pw["practice_score"])
                cc = int(pw["checkin_count"])
                imp = fin.get("impulse_spend")
                st = fin.get("stress_index")

                if cc >= 5:
                    hi_practice_scores.append(ps)
                    if imp is not None:
                        impulse_hi_weeks.append(float(imp))
                    if st is not None:
                        stress_practice_weeks.append(float(st))
                if cc == 0:
                    lo_practice_scores.append(ps)
                    if imp is not None:
                        impulse_lo_weeks.append(float(imp))
                    if st is not None:
                        stress_miss_weeks.append(float(st))

            avg_practice_high = mean(hi_practice_scores) if len(hi_practice_scores) else None
            avg_impulse_hi = mean(impulse_hi_weeks) if impulse_hi_weeks else None
            avg_impulse_lo = mean(impulse_lo_weeks) if impulse_lo_weeks else None
            avg_stress_practice_weeks = (
                mean(stress_practice_weeks) if stress_practice_weeks else None
            )
            avg_stress_miss_weeks = (
                mean(stress_miss_weeks) if stress_miss_weeks else None
            )

            total_checkins = sum(int(p["checkin_count"]) for p in practice_weeks)

            insights = self._build_insight_strings(
                corr_s,
                corr_i,
                corr_st,
                practice_weeks,
                fin_weeks,
                total_checkins,
                avg_practice_high,
                avg_impulse_hi,
                avg_impulse_lo,
                avg_stress_miss_weeks,
                avg_stress_practice_weeks,
            )
            insight_json = json.dumps(insights)

            today = _utc_today()
            existing = (
                SpiritFinanceCorrelation.query.filter(
                    SpiritFinanceCorrelation.user_id == user_id,
                    cast(SpiritFinanceCorrelation.computed_at, Date) == today,
                )
                .order_by(SpiritFinanceCorrelation.computed_at.desc())
                .first()
            )

            if existing:
                row = existing
                row.weeks_analyzed = weeks_n
                row.corr_practice_savings = corr_s
                row.corr_practice_impulse = corr_i
                row.corr_practice_stress = corr_st
                row.corr_practice_bills_ontime = corr_b
                row.avg_practice_score_high_weeks = avg_practice_high
                row.avg_impulse_miss_days = avg_impulse_lo
                row.avg_impulse_checkin_days = avg_impulse_hi
                row.insight_summary = insight_json
                row.computed_at = datetime.utcnow()
            else:
                row = SpiritFinanceCorrelation(
                    user_id=user_id,
                    computed_at=datetime.utcnow(),
                    weeks_analyzed=weeks_n,
                    corr_practice_savings=corr_s,
                    corr_practice_impulse=corr_i,
                    corr_practice_stress=corr_st,
                    corr_practice_bills_ontime=corr_b,
                    avg_practice_score_high_weeks=avg_practice_high,
                    avg_impulse_miss_days=avg_impulse_lo,
                    avg_impulse_checkin_days=avg_impulse_hi,
                    insight_summary=insight_json,
                )
                db.session.add(row)

            db.session.commit()
            return row
        except Exception as e:
            logger.error(f"refresh_spirit_correlation failed for user {user_id}: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
            return None

    def latest_correlation(self, user_id: int) -> SpiritFinanceCorrelation | None:
        try:
            return (
                SpiritFinanceCorrelation.query.filter_by(user_id=user_id)
                .order_by(SpiritFinanceCorrelation.computed_at.desc())
                .first()
            )
        except Exception as e:
            logger.error(f"latest_correlation failed for user {user_id}: {e}")
            return None
