#!/usr/bin/env python3
"""Tier-specific next-step recommendations for public assessment results."""

RECOMMENDATIONS_BY_TYPE: dict[str, dict[str, dict]] = {
    "ai-risk": {
        "low": {
            "tier_title": "Low Risk",
            "next_steps": [
                "Continue building skills in judgment-based analysis and leadership.",
                "Document your unique contributions that AI cannot replicate.",
                "Mentor junior team members in your domain expertise.",
            ],
            "actions": [
                {"label": "View AI-Proof Career Paths", "link": "/resources/ai-proof-careers"},
                {
                    "label": "Schedule Free Career Coaching",
                    "link": "/register?tier=budget&course=career-coaching",
                },
            ],
        },
        "medium": {
            "tier_title": "Moderate Risk",
            "next_steps": [
                "Upskill in advanced tools and frameworks specific to your role.",
                "Start a high-visibility project to demonstrate irreplaceable value.",
                "Build relationships with decision-makers who understand your strategic impact.",
            ],
            "actions": [
                {
                    "label": "Explore Advanced Skills Training",
                    "link": "/courses?category=skill-building",
                },
                {"label": "Start Career Growth Plan", "link": "/register?tier=mid&course=career-growth"},
            ],
        },
        "high": {
            "tier_title": "High Risk",
            "next_steps": [
                "Immediately begin learning adjacent skills to diversify your value.",
                "Explore roles in your industry that leverage judgment over automation.",
                "Consider career transition planning with expert guidance.",
            ],
            "actions": [
                {"label": "Career Transition Workshop", "link": "/courses?category=career-transition"},
                {
                    "label": "Get 1-on-1 Career Guidance",
                    "link": "/register?tier=professional&addon=career-coach",
                },
            ],
        },
    },
    "income-comparison": {
        "low": {
            "tier_title": "Below Market",
            "next_steps": [
                "Research market rate for your role, location, and experience level.",
                "Document your achievements and value to the organization.",
                "Schedule a compensation conversation with your manager in Q1.",
            ],
            "actions": [
                {"label": "Salary Negotiation Script", "link": "/resources/negotiation-guide"},
                {"label": "Get Market Research", "link": "/register?course=income-optimization"},
            ],
        },
        "medium": {
            "tier_title": "Near Market",
            "next_steps": [
                "You're competitive but could push higher with the right negotiation.",
                "Track accomplishments for next review cycle.",
                "Explore high-value skills that command premium salaries.",
            ],
            "actions": [
                {"label": "Salary Negotiation Masterclass", "link": "/courses?category=negotiation"},
                {"label": "Income Growth Plan", "link": "/register?tier=mid"},
            ],
        },
        "high": {
            "tier_title": "Above Market",
            "next_steps": [
                "You're well-positioned — focus on wealth-building strategies.",
                "Explore executive coaching or leadership development.",
                "Consider side income opportunities aligned with your expertise.",
            ],
            "actions": [
                {"label": "Wealth Accumulation Strategy", "link": "/resources/wealth-building"},
                {"label": "Executive Development Program", "link": "/register?tier=professional"},
            ],
        },
    },
    "layoff-risk": {
        "low": {
            "tier_title": "Stable",
            "next_steps": [
                "Focus on growth and strategic contributions.",
                "Build your professional network for long-term opportunities.",
            ],
            "actions": [
                {"label": "Career Growth Path", "link": "/courses?category=leadership"},
                {"label": "Explore Advancement Opportunities", "link": "/register"},
            ],
        },
        "medium": {
            "tier_title": "Moderate Risk",
            "next_steps": [
                "Stay alert to company changes and industry trends.",
                "Keep your resume updated and continue building your network.",
                "Consider side projects or freelance work as a backup.",
            ],
            "actions": [
                {"label": "Job Search Masterclass", "link": "/courses?category=job-search"},
                {"label": "Get Career Protection Plan", "link": "/register?tier=mid"},
            ],
        },
        "high": {
            "tier_title": "At Risk",
            "next_steps": [
                "Start a quiet job search immediately.",
                "Update your resume and LinkedIn profile.",
                "Build visibility in your industry.",
            ],
            "actions": [
                {"label": "Job Search Masterclass", "link": "/courses?category=job-search"},
                {
                    "label": "Get Career Protection Plan",
                    "link": "/register?tier=professional&addon=job-coach",
                },
            ],
        },
    },
    "cuffing-season": {
        "low": {
            "tier_title": "Not Ready",
            "next_steps": [
                "Focus on personal growth and self-discovery.",
                "Build quality friendships and expand your social circle.",
            ],
            "actions": [
                {"label": "Relationship Readiness Guide", "link": "/resources/relationships"},
            ],
        },
        "high": {
            "tier_title": "Ready to Connect",
            "next_steps": [
                "You're in a great place emotionally and financially.",
                "Be intentional about the qualities you want in a partner.",
                "Join communities aligned with your values.",
            ],
            "actions": [
                {"label": "Relationship Goals Workshop", "link": "/courses?category=relationships"},
                {"label": "Explore Connections", "link": "/register"},
            ],
        },
    },
}


def get_recommendation_tier(assessment_type: str, score: int | float | None) -> str:
    """Map score to tier (low, medium, high)."""
    if score is None:
        return "medium"
    score = float(score)
    if assessment_type in ("ai-risk", "income-comparison", "layoff-risk"):
        if score < 33:
            return "low"
        if score < 67:
            return "medium"
        return "high"
    if assessment_type == "cuffing-season":
        return "high" if score >= 50 else "low"
    return "medium"


def get_tier_recommendations(assessment_type: str, score: int | float | None) -> dict:
    """Return tier_title, next_steps, and actions for an assessment result."""
    tier = get_recommendation_tier(assessment_type, score)
    type_recs = RECOMMENDATIONS_BY_TYPE.get(assessment_type, {})
    recs = type_recs.get(tier)
    if recs is None and tier == "medium":
        recs = type_recs.get("high") or type_recs.get("low") or {}
    return recs or {}
