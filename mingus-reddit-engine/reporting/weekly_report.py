"""Weekly performance report — heat map, listener, engagement, ads, signal library."""

import json
import logging
import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from storage import db

logger = logging.getLogger(__name__)

SCORER_MODEL = os.getenv("SCORER_MODEL", "claude-haiku-3")
_7D = timedelta(days=7)


# ---------------------------------------------------------------------------
# DB helpers that don't yet exist as dedicated functions
# ---------------------------------------------------------------------------

def _leads_last_7d():
    """Return all leads ingested in the past 7 days."""
    from psycopg2.extras import RealDictCursor

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM leads
                WHERE ingested_at >= NOW() - INTERVAL '7 days'
                ORDER BY composite_score DESC NULLS LAST
                """
            )
            return cur.fetchall()
    finally:
        db.release_connection(conn)


def _leads_community_7d(community_name: str):
    """Return leads for a specific community in the past 7 days."""
    from psycopg2.extras import RealDictCursor

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT l.composite_score
                FROM leads l
                JOIN communities c ON c.id = l.community_id
                WHERE LOWER(c.name) = LOWER(%s)
                  AND l.ingested_at >= NOW() - INTERVAL '7 days'
                """,
                (community_name,),
            )
            return cur.fetchall()
    finally:
        db.release_connection(conn)


def _responded_leads_7d():
    from psycopg2.extras import RealDictCursor

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT response_upvotes, response_got_dm, lead_quality_rating
                FROM leads
                WHERE responded = TRUE
                  AND ingested_at >= NOW() - INTERVAL '7 days'
                """
            )
            return cur.fetchall()
    finally:
        db.release_connection(conn)


def _missed_leads_7d():
    from psycopg2.extras import RealDictCursor

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT composite_score
                FROM leads
                WHERE notified = TRUE
                  AND responded = FALSE
                  AND ingested_at >= NOW() - INTERVAL '7 days'
                """
            )
            return cur.fetchall()
    finally:
        db.release_connection(conn)


def _ad_performance_7d():
    from psycopg2.extras import RealDictCursor

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT campaign_type, targeting_value, ctr,
                       cost_per_lead, assessment_starts
                FROM ad_performance
                WHERE date_recorded >= CURRENT_DATE - INTERVAL '7 days'
                """
            )
            return cur.fetchall()
    finally:
        db.release_connection(conn)


# ---------------------------------------------------------------------------
# Section 1 — heat map
# ---------------------------------------------------------------------------

def _heat_map_section() -> dict:
    communities = db.get_communities()  # active only
    results = []

    for c in communities:
        name = c.get("name", "")
        heat_score = float(c.get("heat_score") or 0)

        # heat_score 7 days ago proxy: we only store latest, so delta = 0
        # A future enhancement can store a heat_history table.
        heat_delta = 0.0

        sub_leads = _leads_community_7d(name)
        leads_7d = len(sub_leads)
        scores = [float(l["composite_score"]) for l in sub_leads if l.get("composite_score")]
        avg_composite = round(sum(scores) / len(scores), 2) if scores else 0.0

        if heat_delta > 1.5:
            status = "heating"
        elif heat_delta < -1.5:
            status = "cooling"
        else:
            status = "stable"

        results.append({
            "name": name,
            "heat_score": heat_score,
            "heat_delta": heat_delta,
            "leads_7d": leads_7d,
            "avg_composite": avg_composite,
            "status": status,
        })

    results.sort(key=lambda r: r["heat_score"], reverse=True)
    heating = [r["name"] for r in results if r["status"] == "heating"]
    cooling = [r["name"] for r in results if r["status"] == "cooling"]

    return {"communities": results, "heating": heating, "cooling": cooling}


# ---------------------------------------------------------------------------
# Section 2 — listener
# ---------------------------------------------------------------------------

def _listener_section() -> dict:
    leads = _leads_last_7d()
    domain_counts: Counter = Counter(
        l.get("domain_id") for l in leads if l.get("domain_id")
    )
    sorted_domains = dict(
        sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
    )
    top_domain = next(iter(sorted_domains), "")

    return {
        "total_leads_stored": len(leads),
        "domain_breakdown": sorted_domains,
        "top_domain": top_domain,
    }


# ---------------------------------------------------------------------------
# Section 3 — engagement
# ---------------------------------------------------------------------------

def _engagement_section() -> dict:
    responded = _responded_leads_7d()
    responded_count = len(responded)

    upvotes = [float(r["response_upvotes"]) for r in responded if r.get("response_upvotes") is not None]
    avg_upvotes = round(sum(upvotes) / len(upvotes), 2) if upvotes else None

    dm_flags = [r["response_got_dm"] for r in responded if r.get("response_got_dm") is not None]
    dm_rate = round(sum(1 for d in dm_flags if d) / len(dm_flags) * 100, 1) if dm_flags else None

    ratings = [float(r["lead_quality_rating"]) for r in responded if r.get("lead_quality_rating") is not None]
    avg_quality_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    missed = _missed_leads_7d()
    missed_count = len(missed)
    missed_scores = [float(m["composite_score"]) for m in missed if m.get("composite_score")]
    missed_avg_composite = round(sum(missed_scores) / len(missed_scores), 2) if missed_scores else None

    return {
        "responded_count": responded_count,
        "avg_upvotes": avg_upvotes,
        "dm_rate": dm_rate,
        "avg_quality_rating": avg_quality_rating,
        "missed_count": missed_count,
        "missed_avg_composite": missed_avg_composite,
    }


# ---------------------------------------------------------------------------
# Section 4 — ads
# ---------------------------------------------------------------------------

def _ads_section() -> dict:
    rows = _ad_performance_7d()
    if not rows:
        return {"status": "no_data"}

    # total spend
    total_spend = sum(
        (float(r.get("cost_per_lead") or 0) * int(r.get("assessment_starts") or 0))
        for r in rows
    )

    # per campaign_type aggregates
    by_type: dict = defaultdict(list)
    for r in rows:
        by_type[r["campaign_type"]].append(r)

    avg_ctr = {
        ct: round(sum(float(r.get("ctr") or 0) for r in rs) / len(rs), 4)
        for ct, rs in by_type.items()
    }
    avg_cpl = {
        ct: round(sum(float(r.get("cost_per_lead") or 0) for r in rs) / len(rs), 2)
        for ct, rs in by_type.items()
    }

    # top community by CTR
    community_rows = [r for r in rows if r.get("campaign_type") == "community"]
    top_community = (
        max(community_rows, key=lambda r: float(r.get("ctr") or 0))["targeting_value"]
        if community_rows
        else None
    )

    keyword_rows = [r for r in rows if r.get("campaign_type") == "keyword"]
    top_keyword = (
        max(keyword_rows, key=lambda r: float(r.get("ctr") or 0))["targeting_value"]
        if keyword_rows
        else None
    )

    return {
        "status": "ok",
        "total_spend": round(total_spend, 2),
        "avg_ctr_by_campaign": avg_ctr,
        "avg_cpl_by_campaign": avg_cpl,
        "top_community": top_community,
        "top_keyword": top_keyword,
    }


# ---------------------------------------------------------------------------
# Section 5 — signal library (Claude)
# ---------------------------------------------------------------------------

def _signal_library_section(leads: list) -> str:
    if not leads:
        return "No leads this week — system is in warmup phase."

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        return "Signal analysis unavailable."

    summary_items = [
        {
            "domain_id": l.get("domain_id"),
            "subreddit": l.get("subreddit"),
            "composite_score": float(l.get("composite_score") or 0),
            "matched_keywords": l.get("matched_keywords") or [],
            "ai_summary": (l.get("ai_summary") or "")[:100],
            "city_signal": l.get("city_signal"),
        }
        for l in leads[:50]
    ]
    leads_json = json.dumps(summary_items, indent=2)

    system_prompt = (
        "You are a growth analyst for Mingus. Review this week's lead\n"
        "data and identify:\n\n"
        "1. Which communities generated the most high-signal leads?\n"
        "   Name them specifically.\n"
        "2. Which problem domain is showing the most activity?\n"
        "3. Which specific phrases appeared in 3 or more high-scoring\n"
        "   leads? Quote them exactly — these are keyword library\n"
        "   candidates.\n"
        "4. Are there any keywords that matched many leads but produced\n"
        "   low composite scores (below 5.0)? Name them — these are\n"
        "   false positives to remove.\n"
        "5. One specific recommended action for next week. Be concrete:\n"
        "   name the community, keyword, or template to act on.\n\n"
        "Return a structured markdown report with numbered sections.\n"
        "Be specific. Quote actual phrases. Name actual communities."
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=SCORER_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Here is this week's lead data:\n{leads_json}"}
            ],
        )
        return response.content[0].text
    except Exception as exc:
        logger.error("Signal library Claude call failed: %s", exc)
        return "Signal analysis unavailable."


# ---------------------------------------------------------------------------
# Section 6 — recommendations
# ---------------------------------------------------------------------------

def _recommendations_section(sections: dict) -> list:
    recs = []

    heat = sections.get("heat_map", {})
    listener = sections.get("listener", {})
    engagement = sections.get("engagement", {})
    ads = sections.get("ads", {})

    heating = heat.get("heating", [])
    if heating:
        recs.append(
            f"r/{heating[0]} is heating up — check it for new content opportunities this week."
        )

    missed = engagement.get("missed_count", 0)
    if missed > 5:
        recs.append(
            f"{missed} notified leads went unanswered — aim to respond within 4 hours of notification."
        )

    top_domain = listener.get("top_domain", "")
    if top_domain and len(recs) < 3:
        recs.append(
            f"Lead volume is highest in '{top_domain}' — lead with that framing in next week's replies."
        )

    if ads.get("status") == "ok":
        low_ctr = {
            ct: ctr
            for ct, ctr in ads.get("avg_ctr_by_campaign", {}).items()
            if ctr < 0.003  # 0.3%
        }
        for ct in low_ctr:
            if len(recs) < 3:
                recs.append(
                    f"Campaign type '{ct}' has CTR below 0.3% — consider pausing and reallocating budget."
                )

    # Default fallbacks
    defaults = [
        "Continue building karma in top communities.",
        "Run a manual heat check this week.",
        "Respond to at least 5 leads before next report.",
    ]
    for d in defaults:
        if len(recs) >= 3:
            break
        recs.append(d)

    return recs[:3]


# ---------------------------------------------------------------------------
# Markdown render
# ---------------------------------------------------------------------------

def _render_markdown(report: dict) -> str:
    period_start = report["period_start"]
    period_end = report["period_end"]
    sections = report["sections"]

    lines = []
    lines += [
        f"# Mingus Weekly Performance Report — {period_end}",
        "",
        f"**Period:** {period_start} → {period_end}  ",
        f"**Generated:** {report['generated_at']}",
        "",
        "---",
        "",
    ]

    # Heat map
    lines += ["## Heat Map", ""]
    hm = sections.get("heat_map", {})
    if hm.get("communities"):
        lines += [
            "| Community | Heat | Delta | Leads 7d | Avg Score | Status |",
            "|-----------|------|-------|----------|-----------|--------|",
        ]
        for c in hm["communities"]:
            delta_str = f"{c['heat_delta']:+.1f}" if c["heat_delta"] != 0 else "—"
            lines.append(
                f"| r/{c['name']} | {c['heat_score']} | {delta_str} "
                f"| {c['leads_7d']} | {c['avg_composite']} | {c['status']} |"
            )
    if hm.get("heating"):
        lines.append(f"\n🔥 **Heating:** {', '.join(hm['heating'])}")
    if hm.get("cooling"):
        lines.append(f"❄️ **Cooling:** {', '.join(hm['cooling'])}")
    lines += ["", "---", ""]

    # Listener
    lines += ["## Listener", ""]
    ls = sections.get("listener", {})
    lines += [
        f"**Leads stored (7d):** {ls.get('total_leads_stored', 0)}  ",
        f"**Top domain:** {ls.get('top_domain') or '—'}",
        "",
    ]
    breakdown = ls.get("domain_breakdown", {})
    if breakdown:
        lines += ["| Domain | Lead Count |", "|--------|------------|"]
        for domain, count in breakdown.items():
            lines.append(f"| {domain} | {count} |")
    lines += ["", "---", ""]

    # Engagement
    lines += ["## Engagement", ""]
    eng = sections.get("engagement", {})
    lines += [
        f"**Responded:** {eng.get('responded_count', 0)}  ",
        f"**Avg upvotes:** {eng.get('avg_upvotes') or '—'}  ",
        f"**DM rate:** {(str(eng['dm_rate']) + '%') if eng.get('dm_rate') is not None else '—'}  ",
        f"**Avg quality rating:** {eng.get('avg_quality_rating') or '—'}  ",
        f"**Missed (notified, not responded):** {eng.get('missed_count', 0)}  ",
        f"**Missed avg composite:** {eng.get('missed_avg_composite') or '—'}",
        "",
        "---",
        "",
    ]

    # Ads
    lines += ["## Ads Performance", ""]
    ads = sections.get("ads", {})
    if ads.get("status") == "no_data":
        lines.append("_No ad performance data this week._")
    else:
        lines += [
            f"**Total spend (est.):** ${ads.get('total_spend', 0):,.2f}  ",
            f"**Top community:** {ads.get('top_community') or '—'}  ",
            f"**Top keyword:** {ads.get('top_keyword') or '—'}",
            "",
        ]
        ctr_data = ads.get("avg_ctr_by_campaign", {})
        cpl_data = ads.get("avg_cpl_by_campaign", {})
        if ctr_data:
            lines += ["| Campaign Type | Avg CTR | Avg CPL |", "|---------------|---------|---------|"]
            for ct in ctr_data:
                ctr_pct = f"{ctr_data[ct] * 100:.2f}%"
                cpl = f"${cpl_data.get(ct, 0):.2f}"
                lines.append(f"| {ct} | {ctr_pct} | {cpl} |")
    lines += ["", "---", ""]

    # Signal library
    lines += ["## Signal Library Analysis", ""]
    lines.append(sections.get("signal_library", "_No analysis available._"))
    lines += ["", "---", ""]

    # Recommendations
    lines += ["## Recommendations for Next Week", ""]
    for i, rec in enumerate(sections.get("recommendations", []), 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    return "\n".join(lines)


def _save_markdown(content: str, period_end: date) -> str:
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / f"weekly_report_{period_end}.md"
    filepath.write_text(content)
    return str(filepath)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def generate_report() -> dict:
    """Generate the full weekly performance report and save to output/."""
    now = datetime.now(timezone.utc)
    period_start = (now - _7D).date()
    period_end = now.date()

    leads_7d = _leads_last_7d()

    heat_map = _heat_map_section()
    listener = _listener_section()
    engagement = _engagement_section()
    ads = _ads_section()
    signal_library = _signal_library_section(leads_7d)

    all_sections = {
        "heat_map": heat_map,
        "listener": listener,
        "engagement": engagement,
        "ads": ads,
        "signal_library": signal_library,
    }
    recommendations = _recommendations_section(all_sections)
    all_sections["recommendations"] = recommendations

    report = {
        "generated_at": now,
        "period_start": period_start,
        "period_end": period_end,
        "sections": all_sections,
    }

    md = _render_markdown(report)
    filepath = _save_markdown(md, period_end)
    logger.info("Weekly report saved: %s", filepath)
    report["output_file"] = filepath

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    report = generate_report()
    listener = report["sections"]["listener"]
    print(f"Weekly report saved: {report['output_file']}")
    print(
        f"Leads this week: {listener['total_leads_stored']} | "
        f"Top domain: {listener.get('top_domain') or '—'}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
