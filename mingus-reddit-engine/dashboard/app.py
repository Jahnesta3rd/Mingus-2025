"""Mingus Reddit Engine — founder dashboard (Flask, port 5001)."""

import functools
import json
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

# ---------------------------------------------------------------------------
# Bootstrap env before any DB import
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv("/var/www/mingus/.env")
except ImportError:
    pass

_dbu = os.getenv("DATABASE_URL", "")
if _dbu:
    _p = urlparse(_dbu)
    os.environ["PGHOST"] = _p.hostname or ""
    os.environ["PGPORT"] = str(_p.port or 5432)
    os.environ["PGUSER"] = unquote(_p.username or "")
    os.environ["PGPASSWORD"] = unquote(_p.password or "")
    os.environ["PGDATABASE"] = _p.path.lstrip("/")
    os.environ["PGSSLMODE"] = "require"

from flask import (
    Flask, request, redirect, url_for, Response, flash,
    get_flashed_messages, send_file, render_template, jsonify,
)
import requests
from psycopg2.extras import RealDictCursor

from storage import db
from intelligence import heat_map
from pipeline import ads_brief as ads_brief_mod
from pipeline.ads_brief import export_for_reddit_ads, zip_reddit_ads_export
from reporting import feedback_loop

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "mingus-dev-secret-2024")

HOT_LEAD_THRESHOLD = float(os.getenv("HOT_LEAD_THRESHOLD", "9.0"))
OUTPUT_DIR = Path(__file__).parent.parent / "output"
SIGNALS_PATH = Path(__file__).parent.parent / "config" / "domain_signals.json"
PENDING_PATH = Path(__file__).parent.parent / "config" / "signal_updates_pending.json"
MINGUS_BACKEND_URL = os.getenv("MINGUS_BACKEND_URL", "http://127.0.0.1:5000")

# ---------------------------------------------------------------------------
# Inline styles
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #1A1A2E; color: #E8E8F0;
  font-family: system-ui, sans-serif; font-size: 14px;
  padding: 20px;
}
.wrap { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin-bottom: 6px; color: #B8B4FF; }
h2 { font-size: 1.15rem; margin: 24px 0 8px; color: #B8B4FF; border-bottom: 1px solid #333; padding-bottom: 4px; }
h3 { font-size: 1rem; margin: 16px 0 6px; color: #9996CC; }
a { color: #7B76DD; text-decoration: none; }
a:hover { text-decoration: underline; }
nav { margin-bottom: 20px; display: flex; gap: 16px; flex-wrap: wrap; }
nav a { color: #A8A4DD; font-size: 13px; padding: 4px 10px;
  border: 1px solid #333; border-radius: 4px; }
nav a:hover { border-color: #534AB7; background: #22203A; }
.cards { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 24px; }
.card { background: #22203A; border: 1px solid #333; border-radius: 6px;
  padding: 14px 18px; min-width: 160px; }
.card .val { font-size: 1.8rem; font-weight: bold; font-family: monospace;
  color: #B8B4FF; }
.card .lbl { font-size: 11px; color: #888; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; font-family: monospace;
  font-size: 13px; margin-bottom: 16px; }
th { text-align: left; padding: 6px 10px; background: #22203A;
  color: #9996CC; border-bottom: 1px solid #333; }
td { padding: 6px 10px; border-bottom: 1px solid #252540; vertical-align: top; }
tr:nth-child(even) td { background: #1E1C35; }
tr:hover td { background: #27254A; }
.tier-high { color: #1D9E75; font-weight: bold; }
.tier-medium { color: #D97706; }
.tier-low { color: #666; }
.score-hot { color: #FF6B6B; font-weight: bold; }
.score-high { color: #D97706; }
.score-ok { color: #888; }
form { display: inline; }
.btn { display: inline-block; padding: 5px 12px; border-radius: 4px;
  border: 1px solid #444; background: #2A2850; color: #E8E8F0;
  cursor: pointer; font-size: 12px; font-family: system-ui; }
.btn:hover { background: #534AB7; border-color: #534AB7; }
.btn-green { background: #0E5C45; border-color: #1D9E75; color: #7FFFCC; }
.btn-green:hover { background: #1D9E75; }
.btn-red { background: #5C1A1A; border-color: #9E1D1D; color: #FFAAAA; }
.btn-red:hover { background: #9E1D1D; }
input[type=text], input[type=number], input[type=password], select, textarea {
  background: #16152A; border: 1px solid #444; color: #E8E8F0;
  padding: 5px 10px; border-radius: 4px; font-size: 13px;
  font-family: monospace; }
textarea { width: 100%; min-height: 100px; }
.filter-bar { display: flex; gap: 10px; flex-wrap: wrap;
  margin-bottom: 16px; align-items: center; }
.flash { background: #2A3A2A; border: 1px solid #1D9E75; color: #7FFFCC;
  padding: 8px 14px; border-radius: 4px; margin-bottom: 14px; }
.warn { background: #3A2A0A; border: 1px solid #D97706; color: #FFD06B;
  padding: 8px 14px; border-radius: 4px; margin-bottom: 14px; }
.detail-box { background: #22203A; border: 1px solid #333; border-radius: 6px;
  padding: 16px; margin-bottom: 14px; white-space: pre-wrap;
  font-family: monospace; font-size: 13px; line-height: 1.5; }
.kw-pill { display: inline-block; background: #2A2850; border: 1px solid #534AB7;
  border-radius: 12px; padding: 2px 9px; font-size: 11px;
  margin: 2px; color: #B8B4FF; }
.pending-row { background: #3A3A0A !important; }
hr { border: none; border-top: 1px solid #333; margin: 18px 0; }
.report-body h2 { font-size: 1rem; }
.report-body table { font-size: 12px; }
"""


def _html(title, body, active=""):
    flash_html = ""
    for msg in get_flashed_messages():
        flash_html += f'<div class="flash">{msg}</div>'
    nav_links = [
        ("/", "Overview"),
        ("/leads", "Lead Queue"),
        ("/marketing", "Marketing"),
        ("/pmf", "PMF"),
        ("/communities", "Heat Map"),
        ("/ads", "Ads Brief"),
        ("/signal-library", "Signals"),
        ("/weekly-report", "Reports"),
    ]
    nav_html = "".join(
        f'<a href="{href}" {"style=border-color:#534AB7;background:#22203A" if href == active else ""}>'
        f'{label}</a>'
        for href, label in nav_links
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Mingus — {title}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    <h1>Mingus Reddit Engine</h1>
    <nav>{nav_html}</nav>
    {flash_html}
    {body}
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        password = os.getenv("DASHBOARD_PASSWORD", "")
        if not password:
            return f(*args, **kwargs)
        username = os.getenv("DASHBOARD_USER", "admin")
        auth = request.authorization
        if not auth or auth.username != username or auth.password != password:
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Mingus Dashboard"'},
            )
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# DB helpers (raw queries not yet in db.py)
# ---------------------------------------------------------------------------

def _query(sql, params=()):
    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        db.release_connection(conn)


def _query_one(sql, params=()):
    rows = _query(sql, params)
    return rows[0] if rows else None


def _exec(sql, params=()):
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        db.release_connection(conn)


# ---------------------------------------------------------------------------
# Score badge helper
# ---------------------------------------------------------------------------

def _score_cls(score):
    s = float(score or 0)
    if s >= HOT_LEAD_THRESHOLD:
        return "score-hot"
    if s >= 8.0:
        return "score-high"
    return "score-ok"


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GET / — Overview
# ---------------------------------------------------------------------------

@app.route("/")
@requires_auth
def overview():
    total_leads = (_query_one("SELECT COUNT(*) AS n FROM leads") or {}).get("n", 0)
    hot_unresponded = (_query_one(
        "SELECT COUNT(*) AS n FROM leads WHERE composite_score >= %s AND responded = FALSE",
        (HOT_LEAD_THRESHOLD,)
    ) or {}).get("n", 0)
    active_communities = (_query_one(
        "SELECT COUNT(*) AS n FROM communities WHERE active = TRUE"
    ) or {}).get("n", 0)
    last_scan_row = _query_one("SELECT MAX(ingested_at) AS t FROM leads")
    last_scan = last_scan_row["t"].strftime("%Y-%m-%d %H:%M") if last_scan_row and last_scan_row["t"] else "never"
    brief_row = _query_one(
        "SELECT generated_at, status FROM ad_briefs ORDER BY generated_at DESC LIMIT 1"
    )
    last_brief = f"{brief_row['generated_at'].strftime('%Y-%m-%d')} [{brief_row['status']}]" if brief_row else "none"

    cards = [
        (total_leads, "Total Leads"),
        (hot_unresponded, "Hot Leads (unresponded)"),
        (active_communities, "Active Communities"),
        (last_scan, "Last Scan"),
        (last_brief, "Last Ads Brief"),
    ]
    cards_html = "".join(
        f'<div class="card"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
        for v, l in cards
    )

    quick_links = [
        ("/leads", "→ Review lead queue"),
        ("/marketing", "→ Marketing tracker"),
        ("/communities", "→ Check heat map"),
        ("/ads", "→ View latest ads brief"),
        ("/signal-library", "→ Manage keywords"),
        ("/weekly-report", "→ Read weekly report"),
    ]
    links_html = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in quick_links)

    body = f"""
<h2>System Overview</h2>
<div class="cards">{cards_html}</div>
<h2>Quick Actions</h2>
<ul style="list-style:none;line-height:2">{links_html}</ul>
"""
    return _html("Overview", body, active="/")


# ---------------------------------------------------------------------------
# GET /leads — Lead Queue
# ---------------------------------------------------------------------------

@app.route("/leads")
@requires_auth
def leads():
    domain_filter = request.args.get("domain", "")
    subreddit_filter = request.args.get("subreddit", "")
    min_score = float(request.args.get("min_score", "0"))
    days = int(request.args.get("days", "14"))

    conditions = [
        "l.responded = FALSE",
        "l.ingested_at >= NOW() - (%s || ' days')::INTERVAL",
    ]
    params: list = [str(days)]
    if domain_filter:
        conditions.append("l.domain_id = %s")
        params.append(domain_filter)
    if subreddit_filter:
        conditions.append("c.name ILIKE %s")
        params.append(f"%{subreddit_filter}%")
    if min_score:
        conditions.append("l.composite_score >= %s")
        params.append(min_score)

    where = " AND ".join(conditions)
    rows = _query(
        f"SELECT l.id, l.composite_score, c.name AS subreddit, l.domain_id, "
        f"l.title, l.ingested_at "
        f"FROM leads l LEFT JOIN communities c ON c.id = l.community_id "
        f"WHERE {where} ORDER BY l.composite_score DESC NULLS LAST LIMIT 200",
        params,
    )

    # Domain options for filter
    domains = [r["domain_id"] for r in _query(
        "SELECT DISTINCT domain_id FROM leads WHERE domain_id IS NOT NULL ORDER BY domain_id"
    )]
    domain_opts = "<option value=''>All domains</option>" + "".join(
        f'<option value="{d}" {"selected" if d == domain_filter else ""}>{d}</option>'
        for d in domains
    )

    filter_html = f"""
<form method="get" class="filter-bar">
  <select name="domain">{domain_opts}</select>
  <input type="text" name="subreddit" placeholder="subreddit" value="{subreddit_filter}" style="width:160px">
  <input type="number" name="min_score" placeholder="min score" value="{min_score or ''}" step="0.1" style="width:100px">
  <input type="number" name="days" placeholder="days" value="{days}" style="width:70px">
  <button type="submit" class="btn">Filter</button>
</form>"""

    rows_html = ""
    for r in rows:
        score = float(r.get("composite_score") or 0)
        cls = _score_cls(score)
        title = (r.get("title") or "")[:60]
        date_str = r["ingested_at"].strftime("%m/%d") if r.get("ingested_at") else ""
        rows_html += (
            f'<tr>'
            f'<td class="{cls}">{score:.1f}</td>'
            f'<td>r/{r.get("subreddit") or "?"}</td>'
            f'<td>{r.get("domain_id") or "—"}</td>'
            f'<td><a href="/leads/{r["id"]}">{title}</a></td>'
            f'<td style="color:#555">{date_str}</td>'
            f'</tr>'
        )

    body = f"""
<h2>Lead Queue <span style="color:#555;font-size:0.85rem">({len(rows)} shown)</span></h2>
{filter_html}
<table>
  <thead><tr>
    <th>Score</th><th>Community</th><th>Domain</th><th>Title</th><th>Date</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>"""
    return _html("Leads", body, active="/leads")


# ---------------------------------------------------------------------------
# GET /leads/<id> — Lead Detail
# ---------------------------------------------------------------------------

@app.route("/leads/<lead_id>")
@requires_auth
def lead_detail(lead_id):
    lead = _query_one(
        "SELECT l.*, c.name AS subreddit, c.heat_score AS community_heat "
        "FROM leads l LEFT JOIN communities c ON c.id = l.community_id "
        "WHERE l.id = %s",
        (lead_id,),
    )
    if not lead:
        return _html("Not Found", "<p>Lead not found.</p>"), 404

    score = float(lead.get("composite_score") or 0)
    cls = _score_cls(score)
    kws = lead.get("matched_keywords") or []
    kw_pills = "".join(f'<span class="kw-pill">{k}</span>' for k in kws)

    rating_opts = "".join(
        f'<option value="{i}" {"selected" if lead.get("lead_quality_rating") == i else ""}>{i}</option>'
        for i in range(1, 6)
    )

    body = f"""
<h2>Lead Detail</h2>
<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">
  <form action="/leads/{lead_id}/respond" method="post">
    <button class="btn btn-green">✓ Mark Responded</button>
  </form>
  <form action="/leads/{lead_id}/dismiss" method="post">
    <button class="btn btn-red">✕ Dismiss</button>
  </form>
  <form action="/leads/{lead_id}/rate" method="post" style="display:flex;gap:6px;align-items:center">
    <select name="rating">{rating_opts}</select>
    <button class="btn">Rate</button>
  </form>
  <a href="/leads" class="btn">← Back</a>
</div>

<table style="width:auto;margin-bottom:16px">
  <tr><th>Score</th><td class="{cls}">{score:.2f}</td></tr>
  <tr><th>Community</th><td>r/{lead.get("subreddit") or "?"} &nbsp;<span style="color:#555;font-size:11px">heat {lead.get("community_heat") or "?"}/10</span></td></tr>
  <tr><th>Domain</th><td>{lead.get("domain_id") or "—"}</td></tr>
  <tr><th>Pain score</th><td>{lead.get("pain_score") or "—"}</td></tr>
  <tr><th>Readiness</th><td>{lead.get("readiness_score") or "—"}</td></tr>
  <tr><th>Quality rating</th><td>{lead.get("lead_quality_rating") or "unrated"}</td></tr>
  <tr><th>Keywords</th><td>{kw_pills or "—"}</td></tr>
  <tr><th>URL</th><td><a href="{lead.get("url") or "#"}" target="_blank">{lead.get("url") or "—"}</a></td></tr>
</table>

<h3>Post</h3>
<div class="detail-box">{lead.get("title") or ""}

{lead.get("body") or "(no body)"}</div>

<h3>AI Summary</h3>
<div class="detail-box">{lead.get("ai_summary") or "(none)"}</div>

<h3>Suggested Reply Angle</h3>
<div class="detail-box">{lead.get("suggested_reply_angle") or "(none)"}</div>

<h3>Drafted Reply — edit before posting</h3>
<div class="detail-box">{lead.get("drafted_reply") or "(no draft — run reply crafter)"}</div>
"""
    return _html("Lead Detail", body, active="/leads")


@app.route("/leads/<lead_id>/respond", methods=["POST"])
@requires_auth
def lead_respond(lead_id):
    _exec("UPDATE leads SET responded = TRUE WHERE id = %s", (lead_id,))
    flash("Lead marked as responded.")
    return redirect(url_for("leads"))


@app.route("/leads/<lead_id>/dismiss", methods=["POST"])
@requires_auth
def lead_dismiss(lead_id):
    _exec("UPDATE leads SET notified = TRUE, responded = TRUE WHERE id = %s", (lead_id,))
    flash("Lead dismissed.")
    return redirect(url_for("leads"))


@app.route("/leads/<lead_id>/rate", methods=["POST"])
@requires_auth
def lead_rate(lead_id):
    rating = request.form.get("rating", "")
    if rating.isdigit() and 1 <= int(rating) <= 5:
        db.update_quality_rating(lead_id, int(rating))
        flash(f"Rated {rating}/5.")
    return redirect(url_for("lead_detail", lead_id=lead_id))


# ---------------------------------------------------------------------------
# GET /communities — Heat Map View
# ---------------------------------------------------------------------------

@app.route("/communities")
@requires_auth
def communities():
    rows = _query(
        """
        SELECT c.name, c.heat_score, c.posts_per_day, c.growth_rate_3mo,
               c.priority_tier, c.last_heat_check,
               COUNT(l.id) FILTER (
                   WHERE l.ingested_at >= NOW() - INTERVAL '7 days'
               ) AS leads_7d
        FROM communities c
        LEFT JOIN leads l ON l.community_id = c.id
        WHERE c.active = TRUE
        GROUP BY c.id
        ORDER BY c.heat_score DESC NULLS LAST
        """
    )

    rows_html = ""
    for r in rows:
        tier = r.get("priority_tier") or "low"
        tier_cls = f"tier-{tier}"
        heat = f"{float(r.get('heat_score') or 0):.1f}"
        ppd = f"{float(r.get('posts_per_day') or 0):.1f}"
        growth = f"{float(r.get('growth_rate_3mo') or 0):.1f}"
        last_check = r["last_heat_check"].strftime("%m/%d %H:%M") if r.get("last_heat_check") else "never"
        rows_html += (
            f'<tr>'
            f'<td><a href="https://reddit.com/r/{r["name"]}" target="_blank">r/{r["name"]}</a></td>'
            f'<td style="font-family:monospace">{heat}</td>'
            f'<td>{ppd}</td>'
            f'<td>{growth}</td>'
            f'<td>{r.get("leads_7d") or 0}</td>'
            f'<td class="{tier_cls}">{tier}</td>'
            f'<td style="color:#555;font-size:11px">{last_check}</td>'
            f'</tr>'
        )

    body = f"""
<h2>Heat Map <span style="color:#555;font-size:0.85rem">({len(rows)} active communities)</span></h2>
<div style="margin-bottom:14px;display:flex;gap:10px">
  <form action="/communities/heat-check" method="post">
    <button class="btn">↻ Run Heat Check</button>
  </form>
  <a href="/communities/add" class="btn">+ Add Community</a>
</div>
<table>
  <thead><tr>
    <th>Community</th><th>Heat Score</th><th>Posts/Day</th>
    <th>Growth 3mo</th><th>Leads (7d)</th><th>Tier</th><th>Last Check</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>
"""
    return _html("Heat Map", body, active="/communities")


@app.route("/communities/heat-check", methods=["POST"])
@requires_auth
def communities_heat_check():
    def _run():
        try:
            heat_map.run_heat_check()
        except Exception as exc:
            app.logger.error("Heat check error: %s", exc)
    threading.Thread(target=_run, daemon=True).start()
    flash("Heat check running in background — refresh in a minute.")
    return redirect(url_for("communities"))


@app.route("/communities/add", methods=["GET"])
@requires_auth
def communities_add_form():
    signals = json.loads(SIGNALS_PATH.read_text())
    domain_opts = "".join(
        f'<option value="{d["domain_id"]}">{d["domain_id"]}</option>'
        for d in signals.get("domains", [])
    )
    body = f"""
<h2>Add Community</h2>
<form action="/communities/add" method="post" style="display:flex;flex-direction:column;gap:10px;max-width:400px">
  <label>Subreddit name (no r/)<br>
    <input type="text" name="name" required style="width:100%"></label>
  <label>Platform<br>
    <select name="platform" style="width:100%">
      <option value="reddit">reddit</option>
    </select>
  </label>
  <label>Primary domain<br>
    <select name="primary_domain" style="width:100%">{domain_opts}</select>
  </label>
  <button type="submit" class="btn btn-green">Add Community</button>
  <a href="/communities" class="btn">Cancel</a>
</form>
"""
    return _html("Add Community", body, active="/communities")


@app.route("/communities/add", methods=["POST"])
@requires_auth
def communities_add():
    name = request.form.get("name", "").strip().lower()
    platform = request.form.get("platform", "reddit")
    primary_domain = request.form.get("primary_domain", "")
    if name:
        try:
            heat_map.add_community(name, platform, primary_domain)
            flash(f"r/{name} added.")
        except Exception as exc:
            flash(f"Error adding community: {exc}")
    return redirect(url_for("communities"))


# ---------------------------------------------------------------------------
# GET /ads — Ads Brief
# ---------------------------------------------------------------------------

def _render_brief_section(title, rows_data, columns):
    if not rows_data:
        return f"<p style='color:#555'>No data.</p>"
    headers = "".join(f"<th>{c}</th>" for c in columns)
    rows_html = ""
    for row in rows_data:
        cells = "".join(f"<td>{row.get(k, '—')}</td>" for k in columns)
        rows_html += f"<tr>{cells}</tr>"
    return f"<h3>{title}</h3><table><thead><tr>{headers}</tr></thead><tbody>{rows_html}</tbody></table>"


@app.route("/ads")
@requires_auth
def ads():
    brief_row = _query_one(
        "SELECT * FROM ad_briefs ORDER BY generated_at DESC LIMIT 1"
    )
    past_briefs = _query(
        "SELECT id, generated_at, status FROM ad_briefs ORDER BY generated_at DESC LIMIT 10"
    )

    if not brief_row:
        body = """
<h2>Ads Brief</h2>
<div class="warn">No brief generated yet.
  <form action="/ads/generate" method="post" style="display:inline;margin-left:10px">
    <button class="btn btn-green">Generate Now</button>
  </form>
</div>"""
        return _html("Ads Brief", body, active="/ads")

    brief_id = str(brief_row["id"])
    tc = brief_row.get("top_communities") or []
    tk = brief_row.get("top_keywords") or []
    td = brief_row.get("top_domains") or []
    geo = brief_row.get("geo_targets") or []
    budget = brief_row.get("budget_allocation") or {}

    comm_html = _render_brief_section(
        "Top Communities", tc,
        ["subreddit", "lead_count", "avg_composite", "primary_domain", "heat_score", "recommended_daily_budget"]
    )
    kw_html = _render_brief_section(
        "Top Keywords", tk,
        ["keyword", "frequency", "primary_domain", "avg_composite", "bid_tier"]
    )
    dom_html = _render_brief_section(
        "Top Domains", td,
        ["domain_id", "lead_count", "avg_composite", "top_lead_magnet"]
    )
    geo_html = _render_brief_section("Geo Targets", geo, ["city", "dma", "lead_count"])

    budget_html = f"""
<h3>Budget Allocation</h3>
<table style="width:auto">
  <tr><th>Phase</th><td>{budget.get("phase", "—")}</td></tr>
  <tr><th>Weekly Total</th><td>${budget.get("weekly_total", 0):,.0f}</td></tr>
  <tr><th>Campaign A</th><td>${budget.get("campaign_a", 0):,.2f}</td></tr>
  <tr><th>Campaign B</th><td>${budget.get("campaign_b", 0):,.2f}</td></tr>
  <tr><th>Campaign C</th><td>${budget.get("campaign_c", 0):,.2f}</td></tr>
  <tr><th>Campaign D</th><td>{"${:,.2f}".format(budget["campaign_d"]) if budget.get("campaign_d") else "—"}</td></tr>
</table>"""

    past_rows = "".join(
        f'<tr><td>{r["generated_at"].strftime("%Y-%m-%d %H:%M")}</td>'
        f'<td>{r["status"]}</td></tr>'
        for r in past_briefs
    )

    body = f"""
<h2>Ads Brief
  <span style="color:#555;font-size:0.8rem;margin-left:10px">
    {brief_row["generated_at"].strftime("%Y-%m-%d")} [{brief_row["status"]}]
  </span>
</h2>
<div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
  <form action="/ads/generate" method="post">
    <button class="btn">↻ Regenerate</button>
  </form>
  <form action="/ads/mark-ready" method="post">
    <input type="hidden" name="brief_id" value="{brief_id}">
    <button class="btn btn-green">✓ Mark Ready</button>
  </form>
  <a href="/ads/export" class="btn">⬇ Export</a>
</div>
{comm_html}{kw_html}{dom_html}{geo_html}{budget_html}
<h3>Brief History</h3>
<table style="width:auto"><thead><tr><th>Date</th><th>Status</th></tr></thead>
<tbody>{past_rows}</tbody></table>
"""
    return _html("Ads Brief", body, active="/ads")


@app.route("/ads/generate", methods=["POST"])
@requires_auth
def ads_generate():
    try:
        ads_brief_mod.generate_brief()
        flash("Brief generated.")
    except Exception as exc:
        flash(f"Error: {exc}")
    return redirect(url_for("ads"))


@app.route("/ads/mark-ready", methods=["POST"])
@requires_auth
def ads_mark_ready():
    brief_id = request.form.get("brief_id")
    if brief_id:
        ads_brief_mod.mark_brief_ready(brief_id)
        flash("Brief marked ready.")
    return redirect(url_for("ads"))


@app.route("/ads/export")
@requires_auth
def ads_export():
    brief_row = _query_one("SELECT id, generated_at FROM ad_briefs ORDER BY generated_at DESC LIMIT 1")
    if not brief_row:
        flash("No brief available to export.")
        return redirect(url_for("ads"))

    brief_id = str(brief_row["id"])
    brief_date = brief_row["generated_at"].strftime("%Y-%m-%d")

    try:
        folder_path = export_for_reddit_ads(brief_id)
        zip_bytes = zip_reddit_ads_export(folder_path)
        return Response(
            zip_bytes,
            mimetype="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="mingus_ads_brief_{brief_date}.zip"',
                "Content-Length": len(zip_bytes),
            },
        )
    except Exception as exc:
        app.logger.error("Export failed: %s", exc)
        flash(f"Export error: {exc}")
        return redirect(url_for("ads"))


# ---------------------------------------------------------------------------
# GET /signal-library — Keyword Management
# ---------------------------------------------------------------------------

@app.route("/signal-library")
@requires_auth
def signal_library():
    signals = json.loads(SIGNALS_PATH.read_text())
    pending_data = {"pending_additions": [], "pending_removals": []}
    if PENDING_PATH.exists():
        try:
            pending_data = json.loads(PENDING_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    domain_opts = "".join(
        f'<option value="{d["domain_id"]}">{d["domain_id"]}</option>'
        for d in signals.get("domains", [])
    )

    domains_html = ""
    for domain in signals.get("domains", []):
        did = domain["domain_id"]
        keywords = domain.get("keywords", [])
        kw_html = "".join(
            f'<span class="kw-pill">{kw} '
            f'<form action="/signal-library/remove" method="post" style="display:inline">'
            f'<input type="hidden" name="keyword" value="{kw}">'
            f'<input type="hidden" name="domain_id" value="{did}">'
            f'<button type="submit" style="background:none;border:none;color:#FF6B6B;cursor:pointer;font-size:10px;padding:0">✕</button>'
            f'</form></span>'
            for kw in keywords
        )
        domains_html += f"""
<div style="margin-bottom:18px">
  <strong style="color:#9996CC">{did}</strong>
  <span style="color:#555;font-size:11px;margin-left:6px">({len(keywords)} keywords)</span>
  <div style="margin-top:6px">{kw_html or "<span style='color:#555'>no keywords</span>"}</div>
</div>"""

    # Pending additions
    pending_add_html = ""
    for item in pending_data.get("pending_additions", []):
        kw = item["keyword"]
        pending_add_html += f"""
<tr class="pending-row">
  <td>{kw}</td><td>{item.get("reason", "—")}</td>
  <td>
    <form action="/signal-library/apply-pending" method="post" style="display:inline">
      <input type="hidden" name="keyword" value="{kw}">
      <input type="hidden" name="action" value="add">
      <select name="domain_id">{domain_opts}</select>
      <button class="btn btn-green" style="padding:3px 8px">Apply</button>
    </form>
    <form action="/signal-library/reject-pending" method="post" style="display:inline;margin-left:4px">
      <input type="hidden" name="keyword" value="{kw}">
      <input type="hidden" name="action" value="add">
      <button class="btn btn-red" style="padding:3px 8px">Reject</button>
    </form>
  </td>
</tr>"""

    pending_rem_html = ""
    for item in pending_data.get("pending_removals", []):
        kw = item["keyword"]
        pending_rem_html += f"""
<tr class="pending-row">
  <td>{kw}</td><td>{item.get("reason", "—")}</td>
  <td>
    <form action="/signal-library/apply-pending" method="post" style="display:inline">
      <input type="hidden" name="keyword" value="{kw}">
      <input type="hidden" name="action" value="remove">
      <select name="domain_id">{domain_opts}</select>
      <button class="btn btn-red" style="padding:3px 8px">Remove</button>
    </form>
    <form action="/signal-library/reject-pending" method="post" style="display:inline;margin-left:4px">
      <input type="hidden" name="keyword" value="{kw}">
      <input type="hidden" name="action" value="remove">
      <button class="btn" style="padding:3px 8px">Skip</button>
    </form>
  </td>
</tr>"""

    pending_section = ""
    if pending_add_html or pending_rem_html:
        pending_section = f"""
<div class="warn" style="padding:0">
  <div style="padding:8px 14px;border-bottom:1px solid #D97706;font-weight:bold">
    ⚠ Pending Signal Updates
  </div>
  <div style="padding:12px 14px">
"""
        if pending_add_html:
            pending_section += f"""
    <strong>Additions</strong>
    <table><thead><tr><th>Keyword</th><th>Reason</th><th>Action</th></tr></thead>
    <tbody>{pending_add_html}</tbody></table>"""
        if pending_rem_html:
            pending_section += f"""
    <strong>Removals</strong>
    <table><thead><tr><th>Keyword</th><th>Reason</th><th>Action</th></tr></thead>
    <tbody>{pending_rem_html}</tbody></table>"""
        pending_section += "</div></div>"

    body = f"""
<h2>Signal Library</h2>
{pending_section}
<h3>Add Keyword</h3>
<form action="/signal-library/add" method="post" class="filter-bar">
  <select name="domain_id">{domain_opts}</select>
  <input type="text" name="keyword" placeholder="new keyword" style="width:220px" required>
  <input type="text" name="reason" placeholder="reason (optional)" style="width:180px">
  <button type="submit" class="btn btn-green">Add</button>
</form>
<h3>All Domains</h3>
{domains_html}
"""
    return _html("Signal Library", body, active="/signal-library")


@app.route("/signal-library/add", methods=["POST"])
@requires_auth
def signal_library_add():
    kw = request.form.get("keyword", "").strip()
    domain_id = request.form.get("domain_id", "").strip()
    reason = request.form.get("reason", "manual").strip() or "manual"
    if kw and domain_id:
        feedback_loop.apply_keyword_addition(kw, domain_id, reason=reason, source="dashboard")
        flash(f"Added '{kw}' to {domain_id}.")
    return redirect(url_for("signal_library"))


@app.route("/signal-library/remove", methods=["POST"])
@requires_auth
def signal_library_remove():
    kw = request.form.get("keyword", "").strip()
    domain_id = request.form.get("domain_id", "").strip()
    if kw and domain_id:
        feedback_loop.apply_keyword_removal(kw, domain_id, reason="dashboard_remove", source="dashboard")
        flash(f"Removed '{kw}' from {domain_id}.")
    return redirect(url_for("signal_library"))


@app.route("/signal-library/apply-pending", methods=["POST"])
@requires_auth
def signal_library_apply_pending():
    kw = request.form.get("keyword", "").strip()
    domain_id = request.form.get("domain_id", "").strip()
    action = request.form.get("action", "add")
    if kw and domain_id:
        if action == "add":
            feedback_loop.apply_keyword_addition(kw, domain_id, reason="pending_review", source="dashboard")
        else:
            feedback_loop.apply_keyword_removal(kw, domain_id, reason="pending_review", source="dashboard")
        # Remove from pending
        _remove_from_pending(kw, action)
        flash(f"{'Added' if action == 'add' else 'Removed'} '{kw}'.")
    return redirect(url_for("signal_library"))


@app.route("/signal-library/reject-pending", methods=["POST"])
@requires_auth
def signal_library_reject_pending():
    kw = request.form.get("keyword", "").strip()
    action = request.form.get("action", "add")
    if kw:
        _remove_from_pending(kw, action)
        flash(f"Rejected pending {'addition' if action == 'add' else 'removal'} of '{kw}'.")
    return redirect(url_for("signal_library"))


def _remove_from_pending(keyword: str, action: str):
    if not PENDING_PATH.exists():
        return
    try:
        data = json.loads(PENDING_PATH.read_text())
        key = "pending_additions" if action == "add" else "pending_removals"
        data[key] = [i for i in data.get(key, []) if i["keyword"] != keyword]
        PENDING_PATH.write_text(json.dumps(data, indent=2))
    except (json.JSONDecodeError, OSError):
        pass


# ---------------------------------------------------------------------------
# GET /marketing — Marketing strategy tracker (standalone template)
# ---------------------------------------------------------------------------

@app.route("/marketing")
@requires_auth
def marketing():
    return render_template("marketing.html")


# ---------------------------------------------------------------------------
# GET /pmf — Product-Market Fit tracker (standalone template)
# ---------------------------------------------------------------------------

@app.route("/pmf")
@requires_auth
def pmf():
    return render_template("pmf.html")


# ---------------------------------------------------------------------------
# Proxy admin API calls to main Mingus backend (JWT auth on backend)
# ---------------------------------------------------------------------------

@app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@requires_auth
def api_proxy(subpath):
    if request.method == "OPTIONS":
        return Response("", status=204)

    target = f"{MINGUS_BACKEND_URL}/api/{subpath}"
    headers = {}
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth
    cookie_token = request.cookies.get("mingus_token")
    if cookie_token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {cookie_token}"

    try:
        proxied = requests.request(
            method=request.method,
            url=target,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30,
        )
    except requests.RequestException as exc:
        return jsonify({"error": "Backend unavailable", "message": str(exc)}), 502

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [
        (k, v) for k, v in proxied.headers.items() if k.lower() not in excluded
    ]
    return Response(proxied.content, proxied.status_code, response_headers)


# ---------------------------------------------------------------------------
# GET /weekly-report — Report Archive
# ---------------------------------------------------------------------------

def _md_to_html(text: str) -> str:
    """Convert markdown subset to HTML — no library required."""
    # Escape HTML entities first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = text.splitlines()
    output = []
    in_table = False

    for line in lines:
        # Headings
        if line.startswith("### "):
            if in_table:
                output.append("</table>"); in_table = False
            output.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            if in_table:
                output.append("</table>"); in_table = False
            output.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            if in_table:
                output.append("</table>"); in_table = False
            output.append(f"<h1>{line[2:]}</h1>")
        # HR
        elif re.match(r"^-{3,}$", line.strip()):
            if in_table:
                output.append("</table>"); in_table = False
            output.append("<hr>")
        # Table rows
        elif line.strip().startswith("|") and line.strip().endswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Separator row (---|---|---)
            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                output.append('<table><thead>')
                in_table = True
                cells_html = "".join(f"<{tag}>{c}</{tag}>" for c in cells)
                output.append(f"<tr>{cells_html}</tr></thead><tbody>")
            else:
                cells_html = "".join(f"<td>{c}</td>" for c in cells)
                output.append(f"<tr>{cells_html}</tr>")
        else:
            if in_table:
                output.append("</tbody></table>"); in_table = False
            # Bold
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            # Inline code
            line = re.sub(r"`(.+?)`", r"<code>\1</code>", line)
            if line.strip():
                output.append(f"<p>{line}</p>")

    if in_table:
        output.append("</tbody></table>")
    return "\n".join(output)


@app.route("/weekly-report")
@requires_auth
def weekly_report():
    report_files = sorted(OUTPUT_DIR.glob("weekly_report_*.md"), reverse=True)
    selected = request.args.get("file", "")
    target_file = None

    if selected:
        target_path = OUTPUT_DIR / selected
        if target_path.exists() and target_path.parent == OUTPUT_DIR:
            target_file = target_path
    if not target_file and report_files:
        target_file = report_files[0]

    report_html = ""
    if target_file:
        md_text = target_file.read_text()
        report_html = f'<div class="report-body">{_md_to_html(md_text)}</div>'
    else:
        report_html = "<div class='warn'>No reports generated yet. Run the scheduler to generate the first report.</div>"

    file_opts = "".join(
        f'<option value="{f.name}" {"selected" if f == target_file else ""}>{f.name}</option>'
        for f in report_files
    )
    dropdown = f"""
<form method="get" class="filter-bar" style="margin-bottom:16px">
  <select name="file" onchange="this.form.submit()">{file_opts}</select>
</form>""" if report_files else ""

    body = f"""
<h2>Weekly Reports</h2>
{dropdown}
{report_html}
"""
    return _html("Weekly Report", body, active="/weekly-report")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
