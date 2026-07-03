"""Synthetic lead magnet assessment outputs for visual review and email previews."""

from __future__ import annotations

import json
import os
from copy import deepcopy

from jinja2 import Environment, FileSystemLoader, select_autoescape

ASSESSMENT_LABELS = {
    "ai_risk": "AI Replacement Risk",
    "income_comparison": "Income Comparison",
    "layoff_risk": "Layoff Risk",
    "cuffing_season": "Cuffing Season Score",
}

CTA_LINKS = {
    "ai_risk": "https://mingusapp.com/dashboard/career",
    "income_comparison": "https://mingusapp.com/dashboard/income",
    "layoff_risk": "https://mingusapp.com/dashboard/job-risk",
    "cuffing_season": "https://mingusapp.com/dashboard/relationships",
}


def _template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "templates", "emails")
    )


def _assessment_label(assessment_type: str) -> str:
    return ASSESSMENT_LABELS.get(
        assessment_type,
        assessment_type.replace("_", " ").replace("-", " ").title(),
    )


def render_assessment_email(
    assessment_type: str,
    results_dict: dict,
    first_name: str,
) -> str:
    """Render lead_magnet_results.html with assessment results."""
    env = Environment(
        loader=FileSystemLoader(_template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("lead_magnet_results.html")
    return tpl.render(
        first_name=first_name,
        assessment_type=assessment_type,
        assessment_label=_assessment_label(assessment_type),
        score=results_dict.get("score"),
        risk_level=results_dict.get("risk_level"),
        percentile=results_dict.get("percentile"),
        key_insights=results_dict.get("key_insights", []),
        next_steps=results_dict.get("next_steps", []),
        cta=results_dict.get("cta"),
        cta_link=results_dict.get("cta_link") or CTA_LINKS.get(assessment_type),
        results_data=results_dict,
    )


def _sample(
    assessment_type: str,
    first_name: str,
    results_json: dict,
) -> dict:
    email_html = render_assessment_email(assessment_type, results_json, first_name)
    return {
        "score": results_json["score"],
        "risk_level": results_json.get("risk_level"),
        "percentile": results_json.get("percentile"),
        "results_json": results_json,
        "email_html": email_html,
    }


def _ai_risk_samples() -> dict:
    profiles = {
        "low": {
            "first_name": "Maya",
            "results": {
                "score": 15,
                "risk_level": "Low Risk",
                "percentile": 18,
                "role": "Graphic Designer",
                "industry": "Creative Services",
                "key_insights": [
                    "Your creative role has low automation exposure — roughly 15% of tasks are automatable today.",
                    "Your strongest protection: original visual storytelling and client-facing creative direction.",
                    "Your vulnerability: basic layout templating and stock asset assembly.",
                ],
                "next_steps": [
                    "Build a portfolio showcasing bespoke creative work AI cannot replicate.",
                    "Learn AI-assisted design tools to increase output without replacing your judgment.",
                    "Position yourself as a creative strategist, not just a production designer.",
                ],
                "cta": "Explore your creative career protection plan",
                "cta_link": CTA_LINKS["ai_risk"],
            },
        },
        "mid": {
            "first_name": "Jordan",
            "results": {
                "score": 50,
                "risk_level": "Medium Risk",
                "percentile": 55,
                "role": "Data Analyst",
                "industry": "Tech",
                "key_insights": [
                    "Your role has moderate exposure to automation — about 50% of tasks could be automated in the next 3–5 years.",
                    "Your strongest protection: judgment-based analysis and stakeholder communication.",
                    "Your vulnerability: routine reporting and data cleaning.",
                ],
                "next_steps": [
                    "Start learning advanced analytics tools (Python, SQL) to stay ahead of automation.",
                    "Document your strategic contributions (not just tactical reports).",
                    "Build visibility with decision-makers by leading one cross-functional analysis.",
                ],
                "cta": "See your skills gap and growth path with our Career Module",
                "cta_link": CTA_LINKS["ai_risk"],
            },
        },
        "high": {
            "first_name": "Alex",
            "results": {
                "score": 85,
                "risk_level": "High Risk",
                "percentile": 88,
                "role": "Data Entry Specialist",
                "industry": "Administrative Services",
                "key_insights": [
                    "Your role faces high automation pressure — up to 85% of repetitive tasks are already automatable.",
                    "Your strongest protection: institutional knowledge and cross-department relationships.",
                    "Your vulnerability: manual data input, form processing, and routine verification.",
                ],
                "next_steps": [
                    "Upskill toward data operations or business analysis within 6 months.",
                    "Volunteer for projects requiring human judgment and exception handling.",
                    "Start a 90-day transition plan toward a less automatable adjacent role.",
                ],
                "cta": "Get your personalized AI-resilience action plan",
                "cta_link": CTA_LINKS["ai_risk"],
            },
        },
    }
    return {
        level: _sample("ai_risk", data["first_name"], data["results"])
        for level, data in profiles.items()
    }


def _income_comparison_samples() -> dict:
    profiles = {
        "low": {
            "first_name": "Sam",
            "results": {
                "score": 30,
                "percentile": 20,
                "risk_level": "Below Market",
                "current_salary": 42000,
                "market_median": 52000,
                "market_75th": 61000,
                "market_90th": 72000,
                "role": "Marketing Coordinator",
                "location": "Austin, TX",
                "years_experience": 1,
                "key_insights": [
                    "You're earning roughly 19% below the median for your role in Austin.",
                    "Entry-level peers at the 50th percentile earn about $10K more annually.",
                    "Your experience level suggests significant upside with documented impact.",
                ],
                "next_steps": [
                    "Track measurable campaign results to build a raise case.",
                    "Research salary bands for Marketing Coordinator roles in your metro.",
                    "Target a compensation review after your first major project win.",
                ],
                "cta": "Get a negotiation script tailored to your role and location",
                "cta_link": CTA_LINKS["income_comparison"],
            },
        },
        "mid": {
            "first_name": "Taylor",
            "results": {
                "score": 60,
                "percentile": 60,
                "risk_level": "At Market",
                "current_salary": 78000,
                "market_median": 75000,
                "market_75th": 88000,
                "market_90th": 105000,
                "role": "Product Manager",
                "location": "Denver, CO",
                "years_experience": 5,
                "key_insights": [
                    "You're earning about 4% above the median for your role in Denver.",
                    "There's a $10K gap between your salary and the 75th percentile.",
                    "Your experience level (5 years) suggests you should target $85K–$90K in 12–18 months.",
                ],
                "next_steps": [
                    "Document product launches and revenue impact for your next review.",
                    "Benchmark against PM salaries on Levels.fyi and Blind for Denver.",
                    "Schedule a growth conversation with your manager in Q1.",
                ],
                "cta": "Get a negotiation script tailored to your role and location",
                "cta_link": CTA_LINKS["income_comparison"],
            },
        },
        "high": {
            "first_name": "Riley",
            "results": {
                "score": 90,
                "percentile": 90,
                "risk_level": "Above Market",
                "current_salary": 145000,
                "market_median": 118000,
                "market_75th": 132000,
                "market_90th": 148000,
                "role": "Senior Software Engineer",
                "location": "Houston, TX",
                "years_experience": 8,
                "key_insights": [
                    "You're earning 23% above the median for Senior SWE roles in Houston.",
                    "You're near the 90th percentile — limited immediate upside at current company.",
                    "Your compensation suggests strong leverage for staff-level transitions.",
                ],
                "next_steps": [
                    "Evaluate whether promotion to Staff Engineer is realistic within 12 months.",
                    "Benchmark total comp (base + equity + bonus) against top-quartile peers.",
                    "Consider strategic job search only if growth ceiling is confirmed.",
                ],
                "cta": "Model your 5-year income trajectory in Mingus",
                "cta_link": CTA_LINKS["income_comparison"],
            },
        },
    }
    return {
        level: _sample("income_comparison", data["first_name"], data["results"])
        for level, data in profiles.items()
    }


def _layoff_risk_samples() -> dict:
    profiles = {
        "low": {
            "first_name": "Chris",
            "results": {
                "score": 15,
                "risk_level": "Low Risk",
                "percentile": 12,
                "role": "Registered Nurse",
                "industry": "Healthcare",
                "company_stability": "Stable",
                "key_insights": [
                    "Healthcare roles in your specialty show consistently low layoff rates.",
                    "Your employer has stable headcount growth over the past 24 months.",
                    "Industry demand for your skills exceeds available talent supply.",
                ],
                "next_steps": [
                    "Maintain continuing education credits to stay marketable.",
                    "Build a professional network within your specialty for optionality.",
                    "Keep an emergency fund — low risk doesn't mean zero risk.",
                ],
                "cta": "Build your career safety net with Mingus",
                "cta_link": CTA_LINKS["layoff_risk"],
            },
        },
        "mid": {
            "first_name": "Dana",
            "results": {
                "score": 50,
                "risk_level": "Medium Risk",
                "percentile": 52,
                "role": "Growth Marketing Manager",
                "industry": "SaaS Startup",
                "company_stability": "Volatile Growth",
                "key_insights": [
                    "Your company has had two hiring freezes in the past 18 months.",
                    "Marketing roles are often cut early in downturns at growth-stage companies.",
                    "Your cross-functional skills provide some buffer against role elimination.",
                ],
                "next_steps": [
                    "Document revenue-attributed campaigns before any restructuring.",
                    "Build relationships with product and sales teams for internal mobility.",
                    "Refresh your resume and activate your network proactively.",
                ],
                "cta": "Get your layoff preparedness checklist",
                "cta_link": CTA_LINKS["layoff_risk"],
            },
        },
        "high": {
            "first_name": "Morgan",
            "results": {
                "score": 80,
                "risk_level": "High Risk",
                "percentile": 85,
                "role": "Retail Store Manager",
                "industry": "Brick-and-Mortar Retail",
                "company_stability": "Declining",
                "key_insights": [
                    "Retail sector layoffs increased 34% year-over-year in your region.",
                    "Your employer has closed 12% of locations in the past year.",
                    "Store management roles face consolidation as chains shift to e-commerce.",
                ],
                "next_steps": [
                    "Start exploring operations or logistics roles in growing sectors.",
                    "Build 6 months of expenses in emergency savings immediately.",
                    "Update LinkedIn and begin informational interviews this month.",
                ],
                "cta": "Create your 90-day job transition plan",
                "cta_link": CTA_LINKS["layoff_risk"],
            },
        },
    }
    return {
        level: _sample("layoff_risk", data["first_name"], data["results"])
        for level, data in profiles.items()
    }


def _cuffing_season_samples() -> dict:
    profiles = {
        "low": {
            "first_name": "Casey",
            "results": {
                "score": 20,
                "risk_level": "Low Readiness",
                "percentile": 22,
                "relationship_status": "Single, not actively looking",
                "key_insights": [
                    "You're currently focused on personal goals over relationship building.",
                    "Your social calendar has limited intentional dating opportunities.",
                    "Emotional bandwidth for a new relationship appears limited right now.",
                ],
                "next_steps": [
                    "Clarify what you want before investing energy in dating apps.",
                    "Strengthen friendships and social circles without romantic pressure.",
                    "Revisit relationship readiness in 3–6 months with this assessment.",
                ],
                "cta": "Explore relationship readiness tools in Mingus",
                "cta_link": CTA_LINKS["cuffing_season"],
            },
        },
        "mid": {
            "first_name": "Jamie",
            "results": {
                "score": 50,
                "risk_level": "Moderate Readiness",
                "percentile": 48,
                "relationship_status": "Open but unfocused",
                "key_insights": [
                    "You're open to connection but lack a consistent approach to meeting people.",
                    "Your lifestyle supports socializing but dating isn't a priority.",
                    "Mixed signals between wanting connection and maintaining independence.",
                ],
                "next_steps": [
                    "Set one intentional social goal per week (event, group, or activity).",
                    "Be honest with matches about what you're looking for right now.",
                    "Balance self-care with putting yourself in new social environments.",
                ],
                "cta": "Get your cuffing season action plan",
                "cta_link": CTA_LINKS["cuffing_season"],
            },
        },
        "high": {
            "first_name": "Quinn",
            "results": {
                "score": 95,
                "risk_level": "High Readiness",
                "percentile": 96,
                "relationship_status": "Very open and actively ready",
                "key_insights": [
                    "You're emotionally available and actively seeking meaningful connection.",
                    "Your schedule, social life, and communication style support dating.",
                    "You have clear values and boundaries that attract compatible partners.",
                ],
                "next_steps": [
                    "Prioritize quality over quantity — focus on aligned values.",
                    "Schedule regular social activities where you meet like-minded people.",
                    "Use Mingus relationship insights to understand your connection patterns.",
                ],
                "cta": "Start your relationship intelligence journey",
                "cta_link": CTA_LINKS["cuffing_season"],
            },
        },
    }
    return {
        level: _sample("cuffing_season", data["first_name"], data["results"])
        for level, data in profiles.items()
    }


def generate_assessment_samples() -> dict:
    """
    Generate realistic assessment completions across all 4 types.
    Returns dict with keys: ai_risk, income_comparison, layoff_risk, cuffing_season.
    Each contains low/mid/high entries with score, risk_level, percentile,
    results_json, and email_html.
    """
    return {
        "ai_risk": _ai_risk_samples(),
        "income_comparison": _income_comparison_samples(),
        "layoff_risk": _layoff_risk_samples(),
        "cuffing_season": _cuffing_season_samples(),
    }


def samples_as_json(indent: int = 2) -> str:
    """Serialize all sample results_json payloads for debugging."""
    samples = generate_assessment_samples()
    export = {
        key: {level: deepcopy(data["results_json"]) for level, data in levels.items()}
        for key, levels in samples.items()
    }
    return json.dumps(export, indent=indent)
