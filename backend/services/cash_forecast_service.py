#!/usr/bin/env python3
"""
Daily cash forecast from IncomeStream, RecurringExpense, ScheduledExpense, and profile important_dates.

Currency math uses Decimal; API-facing values are rounded to 2 decimal places.
"""

from __future__ import annotations

import calendar
import json
import logging
import os
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - optional in minimal dev envs
    psycopg2 = None  # type: ignore[misc, assignment]

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.transaction_schedule import IncomeStream, ScheduledExpense
from backend.models.user_models import User

logger = logging.getLogger(__name__)

Q2 = Decimal("0.01")
STATUS_RANK = {"danger": 3, "warning": 2, "healthy": 1}


def _d(x: Any) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _money(x: Decimal) -> Decimal:
    return x.quantize(Q2, rounding=ROUND_HALF_UP)


def _money_float(x: Decimal) -> float:
    return float(_money(x))


def _get_pg_conn():
    if psycopg2 is None:
        return None
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    conn = psycopg2.connect(db_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _load_profile_balance_and_dates(email: str) -> tuple[Decimal, dict[str, Any]]:
    """Return (current_balance, important_dates dict). Balance defaults to 0."""
    if not email:
        return Decimal("0"), {}
    conn = _get_pg_conn()
    if not conn:
        return Decimal("0"), {}
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT current_balance, important_dates
            FROM user_profiles
            WHERE email = %s
            """,
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        if not row:
            return Decimal("0"), {}
        bal = row.get("current_balance")
        current = Decimal("0") if bal is None else _d(bal)
        raw = row.get("important_dates")
        if raw is None or raw == "":
            return current, {}
        if isinstance(raw, dict):
            dates_obj = raw
        else:
            dates_obj = json.loads(raw)
        return current, dates_obj if isinstance(dates_obj, dict) else {}
    except Exception as e:
        logger.warning("cash_forecast profile load failed for %s: %s", email, e)
        return Decimal("0"), {}
    finally:
        conn.close()


def _add_months(d: date, months: int) -> date:
    m0 = d.month - 1 + months
    y = d.year + m0 // 12
    m = m0 % 12 + 1
    last = calendar.monthrange(y, m)[1]
    day = min(d.day, last)
    return date(y, m, day)


def _advance_to_window(anchor: date, window_start: date, step_days: int) -> date:
    d = anchor
    if step_days <= 0:
        return max(d, window_start)
    safety = 0
    while d < window_start and safety < 10000:
        d += timedelta(days=step_days)
        safety += 1
    return d


def _dates_in_range_weekly_biweekly(
    next_or_anchor: date, window_start: date, window_end: date, step_days: int
) -> list[date]:
    out: list[date] = []
    d = _advance_to_window(next_or_anchor, window_start, step_days)
    while d <= window_end:
        out.append(d)
        d += timedelta(days=step_days)
    return out


def _semimonthly_pay_day(due_day: int) -> int:
    """1–14 -> pay on 1st; 15–31 -> pay on 15th."""
    if due_day <= 14:
        return 1
    return 15


def _dates_semimonthly(
    due_day: int, window_start: date, window_end: date
) -> list[date]:
    dom = _semimonthly_pay_day(due_day)
    out: list[date] = []
    cur = date(window_start.year, window_start.month, 1)
    end_m = date(window_end.year, window_end.month, 1)
    while cur <= end_m:
        y, m = cur.year, cur.month
        try:
            landing = date(y, m, dom)
        except ValueError:
            landing = date(y, m, min(dom, calendar.monthrange(y, m)[1]))
        if window_start <= landing <= window_end:
            out.append(landing)
        cur = _add_months(cur, 1)
    return out


def _dates_monthly_series(
    anchor: date, window_start: date, window_end: date
) -> list[date]:
    """Same calendar day each month as ``anchor`` (day clamped per month via _add_months)."""
    out: list[date] = []
    d = anchor
    safety = 0
    while d < window_start and safety < 240:
        d = _add_months(d, 1)
        safety += 1
    while d <= window_end:
        if d >= window_start:
            out.append(d)
        d = _add_months(d, 1)
    return out


def _normalize_dom(due_day: int | None) -> int:
    if due_day is None or due_day < 1:
        return 1
    return min(int(due_day), 31)


def expand_income_stream_dates(
    frequency: str,
    next_date: date,
    window_start: date,
    window_end: date,
) -> list[date]:
    f = (frequency or "").strip().lower()
    if f == "weekly":
        return _dates_in_range_weekly_biweekly(
            next_date, window_start, window_end, 7
        )
    if f == "biweekly":
        return _dates_in_range_weekly_biweekly(
            next_date, window_start, window_end, 14
        )
    if f == "semimonthly":
        due = next_date.day
        return _dates_semimonthly(due, window_start, window_end)
    if f == "monthly":
        return _dates_monthly_series(next_date, window_start, window_end)
    return []


def expand_scheduled_expense_dates(
    row: ScheduledExpense, window_start: date, window_end: date
) -> list[date]:
    """Scheduled cadence expenses: semimonthly uses ``due_day`` (1–14 → 1st, 15–31 → 15th)."""
    f = (row.frequency or "").strip().lower()
    if f == "semimonthly":
        due = _normalize_dom(row.due_day)
        return _dates_semimonthly(due, window_start, window_end)
    return expand_income_stream_dates(f, row.next_date, window_start, window_end)


def expand_recurring_expense_dates(
    row: RecurringExpense, window_start: date, window_end: date
) -> list[date]:
    f = (row.frequency or "").strip().lower()
    due = _normalize_dom(row.due_day)
    anchor = row.created_at.date() if row.created_at else window_start

    if f == "weekly":
        return _dates_in_range_weekly_biweekly(anchor, window_start, window_end, 7)
    if f == "biweekly":
        return _dates_in_range_weekly_biweekly(anchor, window_start, window_end, 14)
    if f == "monthly":
        y, m = anchor.year, anchor.month
        last = calendar.monthrange(y, m)[1]
        first = date(y, m, min(due, last))
        return _dates_monthly_series(first, window_start, window_end)
    if f == "quarterly":
        out: list[date] = []
        d = anchor
        safety = 0
        while d < window_start and safety < 120:
            d = _add_months(d, 3)
            safety += 1
        while d <= window_end:
            if d >= window_start:
                y2, m2 = d.year, d.month
                last2 = calendar.monthrange(y2, m2)[1]
                out.append(date(y2, m2, min(due, last2)))
            d = _add_months(d, 3)
        return out
    if f == "annual":
        out = []
        d = date(anchor.year, anchor.month, min(due, calendar.monthrange(anchor.year, anchor.month)[1]))
        safety = 0
        while d < window_start and safety < 120:
            d = _add_months(d, 12)
            safety += 1
        while d <= window_end:
            if d >= window_start:
                y2, m2 = d.year, d.month
                last2 = calendar.monthrange(y2, m2)[1]
                out.append(date(y2, m2, min(due, last2)))
            d = _add_months(d, 12)
        return out
    return []


def _get_nested(obj: dict, *keys: str) -> Any:
    for k in keys:
        if k in obj:
            return obj[k]
    return None


def iter_special_date_outflows(
    important_dates: dict[str, Any], window_start: date, window_end: date
) -> list[tuple[date, Decimal]]:
    """Yield (event_date, cost) for events with cost > 0 in the window."""
    if not important_dates:
        return []

    events: list[tuple[date, Decimal]] = []

    def pick_date_cost(node: Any) -> tuple[date | None, Decimal]:
        if not isinstance(node, dict):
            return None, Decimal("0")
        raw_d = node.get("date") or node.get("Date")
        if not raw_d:
            return None, Decimal("0")
        if isinstance(raw_d, str) and len(raw_d) >= 10:
            raw_d = raw_d[:10]
        try:
            evd = date.fromisoformat(str(raw_d)[:10])
        except ValueError:
            return None, Decimal("0")
        c = node.get("cost", node.get("Cost", 0))
        try:
            cost = _d(c)
        except Exception:
            cost = Decimal("0")
        return evd, cost

    pairs = [
        ("plannedVacation", "vacation"),
        ("carInspection", "car_inspection"),
        ("sistersWedding", "sisters_wedding"),
    ]
    for a, b in pairs:
        node = _get_nested(important_dates, a, b)
        if node:
            evd, cost = pick_date_cost(node)
            if evd and cost > 0 and window_start <= evd <= window_end:
                events.append((evd, _money(cost)))

    customs = important_dates.get("customEvents") or important_dates.get(
        "custom_events"
    )
    if isinstance(customs, list):
        for item in customs:
            if not isinstance(item, dict):
                continue
            evd, cost = pick_date_cost(item)
            if evd and cost > 0 and window_start <= evd <= window_end:
                events.append((evd, _money(cost)))

    return events


def classify_status(closing: Decimal) -> str:
    if closing >= Decimal("1000"):
        return "healthy"
    if closing >= Decimal("200"):
        return "warning"
    return "danger"


def _forecast_bundle(
    user_id: int, days: int
) -> tuple[
    list[dict[str, Any]],
    dict[str, Decimal],
    dict[str, Decimal],
]:
    """
    Build daily rows plus per-month gross income and expense totals (from flows).
    """
    if days < 1:
        return [], {}, {}

    user = db.session.get(User, user_id)
    if not user:
        return [], {}, {}

    email = (user.email or "").strip().lower()
    current_balance, important_dates = _load_profile_balance_and_dates(email)
    current_balance = _money(current_balance)

    today = date.today()
    window_start = today
    window_end = today + timedelta(days=days - 1)

    flows_in: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    flows_out: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    streams = (
        IncomeStream.query.filter_by(user_id=user_id, is_active=True)
        .order_by(IncomeStream.created_at.asc())
        .all()
    )
    for s in streams:
        amt = _money(_d(s.amount))
        if amt <= 0:
            continue
        for d0 in expand_income_stream_dates(
            s.frequency, s.next_date, window_start, window_end
        ):
            flows_in[d0.isoformat()] += amt

    expenses = (
        RecurringExpense.query.filter_by(user_id=user_id, is_active=True)
        .order_by(RecurringExpense.created_at.asc())
        .all()
    )
    for e in expenses:
        amt = _money(_d(e.amount))
        if amt <= 0:
            continue
        for d0 in expand_recurring_expense_dates(e, window_start, window_end):
            flows_out[d0.isoformat()] += amt

    scheduled = (
        ScheduledExpense.query.filter_by(user_id=user_id, is_active=True)
        .order_by(ScheduledExpense.created_at.asc())
        .all()
    )
    for se in scheduled:
        amt = _money(_d(se.amount))
        if amt <= 0:
            continue
        for d0 in expand_scheduled_expense_dates(se, window_start, window_end):
            flows_out[d0.isoformat()] += amt

    for evd, cost in iter_special_date_outflows(
        important_dates, window_start, window_end
    ):
        flows_out[evd.isoformat()] += cost

    month_in: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    month_out: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    result: list[dict[str, Any]] = []
    prev_close = current_balance

    for i in range(days):
        d0 = today + timedelta(days=i)
        key = d0.isoformat()
        month_key = d0.strftime("%Y-%m")

        inc = _money(flows_in.get(key, Decimal("0")))
        out = _money(flows_out.get(key, Decimal("0")))
        month_in[month_key] += inc
        month_out[month_key] += out

        opening = prev_close
        net = _money(inc - out)
        closing = _money(opening + net)
        status = classify_status(closing)

        result.append(
            {
                "date": key,
                "opening_balance": _money_float(opening),
                "closing_balance": _money_float(closing),
                "net_change": _money_float(net),
                "balance_status": status,
            }
        )
        prev_close = closing

    return result, dict(month_in), dict(month_out)


def build_forecast_for_user(
    user_id: int, days: int = 90
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run schedule expansion and return (daily_cashflow, monthly_summaries)."""
    daily, mi, mo = _forecast_bundle(user_id, days)
    summaries = generate_monthly_summaries(
        daily, month_income_by_month=mi, month_expense_by_month=mo
    )
    return daily, summaries


def generate_daily_forecast(user_id: int, days: int = 90) -> list[dict[str, Any]]:
    """
    Build per-day opening/closing balance from scheduled inflows/outflows.

    Returns dicts: date, opening_balance, closing_balance, net_change, balance_status
    (numeric values as floats rounded to 2 decimals).
    """
    daily, _, _ = _forecast_bundle(user_id, days)
    return daily


def generate_monthly_summaries(
    daily_cashflow: list[dict[str, Any]],
    *,
    month_income_by_month: dict[str, Decimal] | None = None,
    month_expense_by_month: dict[str, Decimal] | None = None,
) -> list[dict[str, Any]]:
    """
    Group daily rows by calendar month.

    Each item: month, month_label, opening_balance, total_income, total_expenses,
    closing_balance, worst_status

    When month_income_by_month / month_expense_by_month are provided (same call
    as generate_daily_forecast), totals match gross inflows/outflows per month.
    """
    if not daily_cashflow:
        return []

    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in daily_cashflow:
        mkey = row["date"][:7]
        by_month[mkey].append(row)

    summaries: list[dict[str, Any]] = []
    for mkey in sorted(by_month.keys()):
        rows = sorted(by_month[mkey], key=lambda r: r["date"])
        opening_balance = float(rows[0]["opening_balance"])
        closing_balance = float(rows[-1]["closing_balance"])
        statuses = [str(r["balance_status"]) for r in rows]
        worst = max(statuses, key=lambda s: STATUS_RANK.get(s, 0))

        if month_income_by_month is not None and month_expense_by_month is not None:
            ti = _money_float(_d(month_income_by_month.get(mkey, Decimal("0"))))
            te = _money_float(_d(month_expense_by_month.get(mkey, Decimal("0"))))
        else:
            ti = 0.0
            te = 0.0
            for r in rows:
                nc = Decimal(str(r["net_change"]))
                if nc > 0:
                    ti += float(_money(nc))
                elif nc < 0:
                    te += float(_money(-nc))

        y, mo = int(mkey[:4]), int(mkey[5:7])
        dt = date(y, mo, 1)
        month_label = dt.strftime("%B %Y")

        summaries.append(
            {
                "month": mkey,
                "month_key": mkey,
                "month_label": month_label,
                "opening_balance": round(opening_balance, 2),
                "total_income": round(ti, 2),
                "total_expenses": round(te, 2),
                "closing_balance": round(closing_balance, 2),
                "worst_status": worst,
            }
        )

    return summaries
