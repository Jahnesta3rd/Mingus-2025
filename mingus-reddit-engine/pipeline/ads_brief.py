"""Reddit Ads targeting brief generator — reads leads, produces structured brief."""

import csv
import io
import logging
import os
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from storage import db

logger = logging.getLogger(__name__)

CITY_DMA = {
    "atlanta": "Atlanta-Athens, GA",
    "houston": "Houston, TX",
    "dc": "Washington DC-Hagerstown, MD",
    "washington": "Washington DC-Hagerstown, MD",
    "dallas": "Dallas-Fort Worth, TX",
    "charlotte": "Charlotte, NC",
    "new york": "New York, NY",
    "nyc": "New York, NY",
    "philadelphia": "Philadelphia, PA",
    "chicago": "Chicago, IL",
    "miami": "Miami-Ft. Lauderdale, FL",
    "baltimore": "Baltimore, MD",
}

PIXEL_EVENTS = int(os.getenv("PIXEL_EVENTS", "0"))


# ---------------------------------------------------------------------------
# Budget helpers
# ---------------------------------------------------------------------------

def _daily_budget(heat_score: float) -> float:
    if heat_score >= 8.0:
        return 15.0
    if heat_score >= 6.0:
        return 10.0
    return 5.0


def _weekly_budget(leads: list) -> dict:
    """Compute weekly budget and phase from lead history depth."""
    if leads:
        # Use the earliest ingested_at in the result set as the anchor
        dates = [
            lead["ingested_at"] for lead in leads if lead.get("ingested_at")
        ]
        if dates:
            first_date = min(dates)
            if hasattr(first_date, "date"):
                first_date = first_date.date()
            week_number = max(1, ((date.today() - first_date).days // 7) + 1)
        else:
            week_number = 1
    else:
        week_number = 1

    if week_number <= 4:
        total = 300.0
        phase = "validation"
    elif week_number <= 8:
        total = 600.0
        phase = "scaling"
    else:
        total = 900.0
        phase = "optimizing"

    campaign_d = 70.0 if PIXEL_EVENTS >= 500 else None

    return {
        "weekly_total": total,
        "phase": phase,
        "campaign_a": round(total * 0.50, 2),
        "campaign_b": round(total * 0.30, 2),
        "campaign_c": round(total * 0.20, 2),
        "campaign_d": campaign_d,
    }


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_top_communities(leads: list) -> list:
    community_leads = defaultdict(list)
    for lead in leads:
        subreddit = (lead.get("subreddit") or "").lower().strip()
        if subreddit:
            community_leads[subreddit].append(lead)

    rows = []
    for subreddit, sub_leads in community_leads.items():
        scores = [
            float(l["composite_score"])
            for l in sub_leads
            if l.get("composite_score") is not None
        ]
        avg_composite = round(sum(scores) / len(scores), 2) if scores else 0.0
        rank = len(sub_leads) * avg_composite

        community = db.get_community_by_name(subreddit)
        heat_score = float(community.get("heat_score") or 0) if community else 0.0
        primary_domain = community.get("primary_domain", "") if community else ""

        rows.append({
            "subreddit": subreddit,
            "lead_count": len(sub_leads),
            "avg_composite": avg_composite,
            "primary_domain": primary_domain,
            "heat_score": heat_score,
            "recommended_daily_budget": _daily_budget(heat_score),
            "_rank": rank,
        })

    rows.sort(key=lambda r: r["_rank"], reverse=True)
    for row in rows:
        del row["_rank"]
    return rows[:8]


def _build_top_keywords(leads: list) -> list:
    keyword_leads = defaultdict(list)
    for lead in leads:
        keywords = lead.get("matched_keywords") or []
        for kw in keywords:
            keyword_leads[kw.lower()].append(lead)

    rows = []
    for keyword, kw_leads in keyword_leads.items():
        domain_counter = Counter(
            l.get("domain_id") for l in kw_leads if l.get("domain_id")
        )
        primary_domain = domain_counter.most_common(1)[0][0] if domain_counter else ""
        scores = [
            float(l["composite_score"])
            for l in kw_leads
            if l.get("composite_score") is not None
        ]
        avg_composite = round(sum(scores) / len(scores), 2) if scores else 0.0
        freq = len(kw_leads)
        bid_tier = "high" if freq >= 10 else ("medium" if freq >= 5 else "low")

        rows.append({
            "keyword": keyword,
            "frequency": freq,
            "primary_domain": primary_domain,
            "avg_composite": avg_composite,
            "bid_tier": bid_tier,
        })

    rows.sort(key=lambda r: r["frequency"], reverse=True)
    return rows[:25]


def _build_top_domains(leads: list) -> list:
    domain_leads = defaultdict(list)
    for lead in leads:
        domain_id = lead.get("domain_id") or ""
        if domain_id:
            domain_leads[domain_id].append(lead)

    rows = []
    for domain_id, dom_leads in domain_leads.items():
        scores = [
            float(l["composite_score"])
            for l in dom_leads
            if l.get("composite_score") is not None
        ]
        avg_composite = round(sum(scores) / len(scores), 2) if scores else 0.0
        rank = len(dom_leads) * avg_composite

        magnet_counter = Counter(
            l.get("lead_magnet_match")
            for l in dom_leads
            if l.get("lead_magnet_match")
        )
        top_lead_magnet = magnet_counter.most_common(1)[0][0] if magnet_counter else ""

        angle_counter = Counter(
            (l.get("suggested_reply_angle") or "")[:60]
            for l in dom_leads
            if l.get("suggested_reply_angle")
        )
        suggested_copy_angle = (
            angle_counter.most_common(1)[0][0] if angle_counter else ""
        )

        rows.append({
            "domain_id": domain_id,
            "lead_count": len(dom_leads),
            "avg_composite": avg_composite,
            "top_lead_magnet": top_lead_magnet,
            "suggested_copy_angle": suggested_copy_angle,
            "_rank": rank,
        })

    rows.sort(key=lambda r: r["_rank"], reverse=True)
    for row in rows:
        del row["_rank"]
    return rows[:3]


def _build_geo_targets(leads: list) -> list:
    city_counts = Counter()
    for lead in leads:
        city_signal = (lead.get("city_signal") or "").lower().strip()
        if not city_signal:
            continue
        for city_key in CITY_DMA:
            if city_key in city_signal:
                city_counts[city_key] += 1
                break

    rows = []
    for city_key, count in city_counts.most_common(6):
        rows.append({
            "city": city_key,
            "dma": CITY_DMA[city_key],
            "lead_count": count,
        })
    return rows


# ---------------------------------------------------------------------------
# Main public functions
# ---------------------------------------------------------------------------

def generate_brief(lookback_days: int = 14) -> dict:
    """Generate a Reddit Ads brief from recent qualifying leads."""
    min_score = float(os.getenv("COMPOSITE_THRESHOLD", "6.5"))
    leads = db.get_leads_for_brief(lookback_days=lookback_days, min_score=min_score)

    now = datetime.now(timezone.utc)
    period_start = (now - timedelta(days=lookback_days)).date()
    period_end = now.date()

    top_communities = _build_top_communities(leads)
    top_keywords = _build_top_keywords(leads)
    top_domains = _build_top_domains(leads)
    geo_targets = _build_geo_targets(leads)
    budget_allocation = _weekly_budget(leads)

    brief = {
        "generated_at": now,
        "period_start": period_start,
        "period_end": period_end,
        "top_communities": top_communities,
        "top_keywords": top_keywords,
        "top_domains": top_domains,
        "geo_targets": geo_targets,
        "budget_allocation": budget_allocation,
        "status": "draft",
    }

    saved = db.insert_ad_brief({
        "period_start": period_start,
        "period_end": period_end,
        "top_communities": top_communities,
        "top_keywords": top_keywords,
        "top_domains": top_domains,
        "suggested_copy_angles": [d["suggested_copy_angle"] for d in top_domains],
        "geo_targets": geo_targets,
        "budget_allocation": budget_allocation,
        "status": "draft",
    })
    if saved:
        brief["id"] = str(saved["id"])
        logger.info(
            "Ad brief saved (id=%s) for %s → %s with %s leads",
            saved["id"],
            period_start,
            period_end,
            len(leads),
        )

    return brief


def export_brief_markdown(brief_dict: dict) -> str:
    """Write a human-readable markdown brief and return the file path."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    period_end = brief_dict.get("period_end", date.today())
    if isinstance(period_end, datetime):
        period_end = period_end.date()
    filename = f"ad_brief_{period_end}.md"
    filepath = output_dir / filename

    lines = []
    lines.append(f"# Mingus Reddit Ads Brief — {period_end}")
    lines.append(f"")
    lines.append(
        f"**Period:** {brief_dict.get('period_start')} → {period_end}  "
    )
    lines.append(f"**Generated:** {brief_dict.get('generated_at')}  ")
    lines.append(f"**Status:** {brief_dict.get('status', 'draft')}")
    lines.append("")

    # Section 1 — Communities
    lines.append("## Top Communities")
    lines.append("")
    lines.append(
        "| Subreddit | Leads | Avg Score | Domain | Heat | Budget/Day |"
    )
    lines.append("|-----------|-------|-----------|--------|------|------------|")
    for c in brief_dict.get("top_communities", []):
        lines.append(
            f"| r/{c['subreddit']} | {c['lead_count']} | {c['avg_composite']} "
            f"| {c['primary_domain']} | {c['heat_score']} "
            f"| ${c['recommended_daily_budget']}/day |"
        )
    lines.append("")

    # Section 2 — Keywords
    lines.append("## Top Keywords")
    lines.append("")
    lines.append(
        "| Keyword | Frequency | Domain | Avg Score | Bid Tier |"
    )
    lines.append("|---------|-----------|--------|-----------|----------|")
    for k in brief_dict.get("top_keywords", []):
        lines.append(
            f"| {k['keyword']} | {k['frequency']} | {k['primary_domain']} "
            f"| {k['avg_composite']} | {k['bid_tier']} |"
        )
    lines.append("")

    # Section 3 — Domains
    lines.append("## Top Domains")
    lines.append("")
    lines.append(
        "| Domain | Leads | Avg Score | Top Lead Magnet | Copy Angle |"
    )
    lines.append("|--------|-------|-----------|-----------------|------------|")
    for d in brief_dict.get("top_domains", []):
        angle = (d.get("suggested_copy_angle") or "")[:60]
        lines.append(
            f"| {d['domain_id']} | {d['lead_count']} | {d['avg_composite']} "
            f"| {d['top_lead_magnet']} | {angle} |"
        )
    lines.append("")

    # Section 4 — Geo Targets
    lines.append("## Geo Targets")
    lines.append("")
    lines.append("| City | DMA | Leads |")
    lines.append("|------|-----|-------|")
    for g in brief_dict.get("geo_targets", []):
        lines.append(f"| {g['city'].title()} | {g['dma']} | {g['lead_count']} |")
    lines.append("")

    # Section 5 — Budget
    lines.append("## Budget Allocation")
    lines.append("")
    budget = brief_dict.get("budget_allocation", {})
    lines.append(f"**Phase:** {budget.get('phase', '—')}  ")
    lines.append(f"**Weekly Total:** ${budget.get('weekly_total', 0):,.0f}")
    lines.append("")
    lines.append("| Campaign | Budget |")
    lines.append("|----------|--------|")
    lines.append(f"| Campaign A (Awareness) | ${budget.get('campaign_a', 0):,.2f} |")
    lines.append(f"| Campaign B (Conversion) | ${budget.get('campaign_b', 0):,.2f} |")
    lines.append(f"| Campaign C (Retargeting seed) | ${budget.get('campaign_c', 0):,.2f} |")
    if budget.get("campaign_d"):
        lines.append(
            f"| Campaign D (Retargeting — pixel) | ${budget['campaign_d']:,.2f} |"
        )
    lines.append("")

    filepath.write_text("\n".join(lines))
    return str(filepath)


def mark_brief_ready(brief_id: str) -> None:
    """Mark an ad brief as ready for activation."""
    db.mark_brief_ready(brief_id)
    logger.info("Ad brief %s marked ready", brief_id)


# ---------------------------------------------------------------------------
# Reddit Ads export — 5-file package
# ---------------------------------------------------------------------------

_AD_COPY_HEADLINES: dict[str, list[str]] = {
    "career_income": [
        "If you haven't gotten a raise in 2 years, you've probably left $15K-$40K on the table.",
        "If you're not sure what your role pays in your city, you're probably negotiating blind.",
        "If AI is changing your industry, your job security score is not what you think it is.",
    ],
    "financial_habits": [
        "If you can't explain where your money went this month, the problem isn't discipline.",
        "If you're living paycheck to paycheck on a good salary, something else is driving it.",
        "The reason budgets fail isn't math — it's that nobody tracks the emotional triggers.",
    ],
    "housing": [
        "If you want to buy but don't know if you're ready, you're probably closer than you think.",
        "Your mortgage readiness isn't about your down payment. It's about 4 factors most people check too late.",
        "If your rent keeps going up, the buy vs. rent math in your city may have already flipped.",
    ],
    "mental_health_money": [
        "If you avoid opening your bank app, that's not a money problem. It's a stress problem.",
        "Financial anxiety is measurable. So is the fix.",
        "If money stress is affecting your sleep, there's a specific pattern behind it.",
    ],
    "relationships_money": [
        "Financial compatibility is the most underrated thing people forget to check before committing.",
        "If money is causing tension in your relationship, it's probably not about the money.",
        "Before combining finances, there's one conversation most couples skip entirely.",
    ],
    "wellness_correlation": [
        "Your stress level and your spending are more connected than you realize.",
        "If work stress is affecting your health, it's also affecting your finances.",
        "Burnout has a dollar amount. Most people never calculate it.",
    ],
    "mental_models": [
        "If you keep making the same financial mistakes, the problem isn't information.",
        "Bad money decisions are usually pattern problems, not math problems.",
        "The gap between knowing what to do and actually doing it has a name — and a fix.",
    ],
}

_BODY_COPY_TEMPLATES: dict[str, list[str]] = {
    "career_income": [
        "Most people discover they've been underpaid only after they've already left money on the table. A 3-minute income comparison tells you exactly where you stand — before your next review. Take the free Income Comparison Assessment — no signup.",
        "Salary negotiation feels risky when you don't have data. The Income Comparison Assessment benchmarks your role, city, and experience level in under 3 minutes. Take the free Income Comparison Assessment — no signup.",
        "AI isn't replacing everyone — but it is changing which skills command a premium. The Layoff Risk Assessment scores your exposure based on your actual role. Take the free Layoff Risk Assessment — no signup.",
    ],
    "financial_habits": [
        "The problem usually isn't spending too much. It's that most people don't see the pattern until it's already happened again. A 3-minute assessment identifies the specific trigger. Take the free Vibe Check Assessment — no signup.",
        "Living paycheck to paycheck on a solid income is a sign, not a character flaw. The Vibe Check identifies whether it's behavioral, structural, or psychological. Take the free Vibe Check Assessment — no signup.",
        "Budgets don't fail because the math is wrong. They fail because the emotional side goes unmeasured. Find out your specific pattern in 3 minutes. Take the free Vibe Check Assessment — no signup.",
    ],
    "housing": [
        "Most first-time buyers wait too long because they're focused on the wrong metrics. The Mortgage Readiness Assessment checks the 4 factors lenders actually care about. Take the free assessment — no signup.",
        "Down payment isn't the main reason buyers get rejected. Knowing the real checklist takes 3 minutes. Take the free Mortgage Readiness Assessment — no signup.",
        "In some markets, buying is already cheaper than renting — even after the down payment. The assessment runs the math for your situation specifically. Take the free assessment — no signup.",
    ],
    "mental_health_money": [
        "Financial anxiety doesn't mean you're bad with money. It usually means something specific is triggering it. A 3-minute check identifies what's actually driving it. Take the free Vibe Check Assessment — no signup.",
        "There's a measurable pattern between money stress and avoidance behavior. Finding your specific trigger is the first step to changing it. Take the free Vibe Check Assessment — no signup.",
        "Sleep disruption from money stress follows a pattern that's been identified and addressed. Find out where you are in 3 minutes. Take the free Vibe Check Assessment — no signup.",
    ],
    "relationships_money": [
        "Financial compatibility isn't just about income — it's about patterns, history, and defaults. The Financial Compatibility Score identifies where you and your partner are aligned (and where you're not). Take the free score — no signup.",
        "Most money arguments in relationships aren't about money. They're about values and defaults. The assessment surfaces the actual pattern in 3 minutes. Take the free Financial Compatibility Score — no signup.",
        "Before combining finances, one conversation matters more than any other. The Financial Compatibility Score shows you what to discuss. Take the free score — no signup.",
    ],
    "wellness_correlation": [
        "There's a measurable relationship between chronic stress and financial decisions. The Vibe Check Assessment identifies the connection in your specific situation. Take the free Vibe Check — no signup.",
        "Work stress affects more than health — it changes spending patterns in ways most people don't notice until later. Take the free Vibe Check Assessment — no signup.",
        "Burnout costs money in ways that don't show up until months later. The Vibe Check helps you identify the pattern before it escalates. Take the free Vibe Check Assessment — no signup.",
    ],
    "mental_models": [
        "Knowing what to do and actually doing it are different problems. The Vibe Check Assessment identifies which mental patterns are running your financial decisions. Take the free Vibe Check — no signup.",
        "The same financial mistake repeated isn't a discipline problem — it's a pattern problem. The assessment identifies yours in 3 minutes. Take the free Vibe Check Assessment — no signup.",
        "Most financial advice assumes the problem is information. It usually isn't. Find your actual pattern in 3 minutes. Take the free Vibe Check Assessment — no signup.",
    ],
}

_LEAD_MAGNET_DISPLAY: dict[str, str] = {
    "income_comparison": "Income Comparison Assessment",
    "layoff_risk": "Layoff Risk Assessment",
    "ai_replacement_risk": "AI Replacement Risk Assessment",
    "cuffing_season_score": "Financial Compatibility Score",
    "vibe_check": "Vibe Check Assessment",
}

_DEFAULT_BODY_COPY = [
    "Find out where you stand in 3 minutes. Take the free assessment — no signup.",
    "Most people don't know their number until they check. The assessment takes 3 minutes. Take the free assessment — no signup.",
    "The data says most people in your situation are closer than they think. Find out in 3 minutes. Take the free assessment — no signup.",
]


def _csv_bytes(headers: list[str], rows: list[dict], comment: str = "") -> bytes:
    buf = io.StringIO()
    if comment:
        buf.write(f"# {comment}\n")
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, "") for h in headers})
    return buf.getvalue().encode()


def _build_ad_copy_brief(top_domains: list, top_cities: list, top_communities: list) -> str:
    top_city = top_cities[0]["city"].title() if top_cities else "your city"
    lines = ["# Mingus Ad Copy Brief", ""]
    lines.append("Review all variants before activating. Edit to match current voice.\n")

    for domain in top_domains:
        did = domain.get("domain_id", "")
        magnet = domain.get("top_lead_magnet", "")
        magnet_display = _LEAD_MAGNET_DISPLAY.get(magnet, magnet or "assessment")
        copy_angle = domain.get("suggested_copy_angle", "")

        headlines = _AD_COPY_HEADLINES.get(did, [
            "If you're dealing with this, you're not alone — and there's a specific pattern behind it.",
            "Most people in your situation discover the answer only after they check.",
            "The gap between where you are and where you want to be has a name. Find it in 3 minutes.",
        ])
        # Personalise H2 with top city where placeholder exists
        headlines = [h.replace("[top city]", top_city) for h in headlines]

        body_variants = _BODY_COPY_TEMPLATES.get(did, _DEFAULT_BODY_COPY)

        lines += [
            f"## {did} — {magnet_display}",
            "",
            f"> **Signal from data:** {copy_angle}" if copy_angle else "",
            "",
            "### Headline options (3 variants — use one per ad set)",
            "",
        ]
        for i, h in enumerate(headlines, 1):
            lines.append(f"**H{i}:** {h}")
        lines.append("")

        lines.append("### Body copy options (3 variants — A/B test these)")
        lines.append("")
        for i, b in enumerate(body_variants, 1):
            lines.append(f"**B{i}:** {b}")
        lines.append("")

        lines.append(f"### CTA")
        lines.append(f"CTA: Take the free {magnet_display} — 3 minutes, no signup required.")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _build_campaign_guide(brief_dict: dict) -> str:
    budget = brief_dict.get("budget_allocation") or {}
    communities = brief_dict.get("top_communities") or []
    geo = brief_dict.get("geo_targets") or []
    top_domains = brief_dict.get("top_domains") or []

    top_domain_id = top_domains[0].get("domain_id", "") if top_domains else ""
    top_magnet = top_domains[0].get("top_lead_magnet", "") if top_domains else ""
    magnet_display = _LEAD_MAGNET_DISPLAY.get(top_magnet, top_magnet or "assessment")

    sub_list = "\n".join(f"  - r/{c['subreddit']} (${c['recommended_daily_budget']:.0f}/day)" for c in communities[:8])
    geo_top3 = ", ".join(g["dma"] for g in geo[:3]) or "All locations"

    budget_a = f"${budget.get('campaign_a', 0):,.0f}"
    budget_b = f"${budget.get('campaign_b', 0):,.0f}"
    budget_c = f"${budget.get('campaign_c', 0):,.0f}"
    phase = budget.get("phase", "validation")
    weekly_total = f"${budget.get('weekly_total', 0):,.0f}"

    has_housing = any(d.get("domain_id") == "housing" for d in top_domains)
    interest_housing = "\n  - Real Estate" if has_housing else ""

    lines = [
        "# Mingus Reddit Ads — Campaign Setup Guide",
        "",
        f"**Budget phase:** {phase} | **Weekly total:** {weekly_total}",
        "",
        "Follow each campaign in order. Do not activate Campaign D until pixel threshold is met.",
        "",
        "---",
        "",
        "## Campaign A — Community Targeting",
        "",
        "**Objective:** Traffic",
        f"**Budget:** {budget_a}/week",
        "**Ad format:** Single image or text post",
        "",
        "**Subreddits to target** (enter manually in Reddit Ads UI — see community_targeting.csv):",
        sub_list or "  (no communities in this brief)",
        "",
        "**Creative:** Use headline H1 from ad_copy_brief.md for the top domain",
        f"**Top domain this week:** {top_domain_id}",
        "",
        f"**Geo:** {geo_top3}",
        "**Schedule:** Run 24/7 (Reddit's delivery system handles peak optimization)",
        "",
        "---",
        "",
        "## Campaign B — Keyword Targeting",
        "",
        "**Objective:** Traffic",
        f"**Budget:** {budget_b}/week",
        "**Ad format:** Single image or text post",
        "",
        "**Keywords:** Upload keywords.csv directly via the Reddit Ads keyword tool",
        "**Creative:** Use headline H2 from ad_copy_brief.md",
        f"**Geo:** {geo_top3}",
        "",
        "---",
        "",
        "## Campaign C — Interest Targeting",
        "",
        "**Objective:** Awareness",
        f"**Budget:** {budget_c}/week",
        "**Ad format:** Single image",
        "",
        "**Targeting:** Select these Reddit interest categories manually in the UI:",
        "  - Personal Finance",
        "  - Career & Business",
        "  - Health & Fitness" + interest_housing,
        "",
        "**Creative:** Use headline H3 from ad_copy_brief.md",
        f"**Geo:** {geo_top3}",
        "",
        "---",
        "",
        "## Campaign D — Retargeting",
        "",
        "**Status: DO NOT ACTIVATE until Reddit pixel has 500+ events**",
        "**Budget:** $70/week (add to weekly total when activated)",
        "**Audience:** Reddit Pixel — visited site, did not convert",
        f"**Creative:** \"Still thinking about your {magnet_display}? Pick up where you left off.\"",
        "**Geo:** All locations",
        "",
        "---",
        "",
        "## Checklist before going live",
        "",
        "- [ ] Review ad_copy_brief.md — edit headlines to match current brand voice",
        "- [ ] Upload keywords.csv to Reddit Ads keyword tool",
        "- [ ] Enter subreddits from community_targeting.csv manually in Campaign A",
        "- [ ] Set geo targets as listed above",
        "- [ ] Confirm Reddit pixel is installed on assessment landing page",
        "- [ ] Set Campaign A live first — validate CTR before launching B and C",
        "",
    ]
    return "\n".join(lines)


def export_for_reddit_ads(brief_id: str) -> str:
    """
    Generate 5 Reddit Ads targeting files for the given brief_id.
    Returns the output folder path.
    """
    row = db.get_ad_brief_by_id(brief_id)
    if not row:
        # Fall back to latest if not found by id (handles abbreviated ids)
        row = db.get_latest_ad_brief()
    if not row:
        raise ValueError("No ad brief found in database.")

    brief_dict = dict(row)
    brief_uuid = str(brief_dict.get("id", brief_id))
    folder_name = f"reddit_ads_{brief_uuid[:8]}"
    output_dir = Path(__file__).parent.parent / "output"
    folder = output_dir / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    communities = brief_dict.get("top_communities") or []
    keywords = brief_dict.get("top_keywords") or []
    top_domains = brief_dict.get("top_domains") or []
    geo_targets = brief_dict.get("geo_targets") or []
    budget = brief_dict.get("budget_allocation") or {}

    # --- File 1: community_targeting.csv ---
    comm_headers = ["subreddit", "recommended_daily_budget", "primary_domain",
                    "lead_count_14d", "avg_composite", "heat_score"]
    comm_rows = [
        {
            "subreddit": c.get("subreddit", ""),
            "recommended_daily_budget": c.get("recommended_daily_budget", ""),
            "primary_domain": c.get("primary_domain", ""),
            "lead_count_14d": c.get("lead_count", ""),
            "avg_composite": c.get("avg_composite", ""),
            "heat_score": c.get("heat_score", ""),
        }
        for c in communities
    ]
    f1 = folder / "community_targeting.csv"
    f1.write_bytes(_csv_bytes(
        comm_headers, comm_rows,
        comment="Manual input guide for Campaign A — Community Targeting"
    ))
    logger.info("Wrote %s", f1)

    # --- File 2: keywords.csv ---
    kw_headers = ["keyword", "frequency", "domain", "avg_composite", "bid_tier"]
    kw_rows = [
        {
            "keyword": k.get("keyword", ""),
            "frequency": k.get("frequency", ""),
            "domain": k.get("primary_domain", ""),
            "avg_composite": k.get("avg_composite", ""),
            "bid_tier": k.get("bid_tier", ""),
        }
        for k in keywords
    ]
    f2 = folder / "keywords.csv"
    f2.write_bytes(_csv_bytes(kw_headers, kw_rows))
    logger.info("Wrote %s", f2)

    # --- File 3: ad_copy_brief.md ---
    f3 = folder / "ad_copy_brief.md"
    f3.write_text(_build_ad_copy_brief(top_domains, geo_targets, communities))
    logger.info("Wrote %s", f3)

    # --- File 4: geo_targets.txt ---
    geo_lines = ["# Reddit DMA geo-targeting list — Campaign A/B/C"]
    for g in geo_targets:
        geo_lines.append(f"{g['dma']} | {g['lead_count']} leads")
    f4 = folder / "geo_targets.txt"
    f4.write_text("\n".join(geo_lines))
    logger.info("Wrote %s", f4)

    # --- File 5: campaign_setup_guide.md ---
    f5 = folder / "campaign_setup_guide.md"
    f5.write_text(_build_campaign_guide(brief_dict))
    logger.info("Wrote %s", f5)

    print(f"Ads brief exported: output/{folder_name}/")
    print("5 files ready. Review ad_copy_brief.md before activating campaigns.")
    return str(folder)


def zip_reddit_ads_export(folder_path: str) -> bytes:
    """Return a ZIP of the 5 export files as bytes (for download)."""
    buf = io.BytesIO()
    folder = Path(folder_path)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(folder.iterdir()):
            zf.write(f, arcname=f.name)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Reddit Ads brief generator")
    parser.add_argument("lookback_days", nargs="?", type=int, default=14,
                        help="Days of leads to include (default 14)")
    parser.add_argument("--export", nargs="?", const="latest", metavar="BRIEF_ID",
                        help="Export 5-file Reddit Ads package for a brief ID (omit for latest)")
    args = parser.parse_args()

    if args.export:
        if args.export == "latest":
            row = db.get_latest_ad_brief()
            if not row:
                print("No brief found. Run without --export first to generate one.")
                sys.exit(1)
            brief_id = str(row["id"])
        else:
            brief_id = args.export
        folder = export_for_reddit_ads(brief_id)
        print(f"Output folder: {folder}")
        return

    min_score = float(os.getenv("COMPOSITE_THRESHOLD", "6.5"))
    leads = db.get_leads_for_brief(lookback_days=args.lookback_days, min_score=min_score)
    brief = generate_brief(lookback_days=args.lookback_days)
    filepath = export_brief_markdown(brief)

    print(f"Brief generated: {filepath}")
    print(
        f"Leads used: {len(leads)} | "
        f"Period: {brief['period_start']} → {brief['period_end']}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
