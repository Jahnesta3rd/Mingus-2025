#!/usr/bin/env python3
"""
Generate all assessment output samples and create an HTML report.
Usage: python -m backend.scripts.generate_assessment_samples
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from backend.tests.fixtures.assessment_output_samples import generate_assessment_samples

REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Lead Magnet Assessment Output Samples</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .assessment-section { margin: 40px 0; border: 1px solid #ddd; padding: 20px; }
        .assessment-title { font-size: 24px; font-weight: bold; color: #5B2D8E; margin-bottom: 20px; }
        .sample-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0; }
        .sample-card { border: 1px solid #eee; padding: 15px; background: #f9f9f9; }
        .sample-label { font-weight: bold; color: #333; margin-bottom: 10px; }
        .score-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; color: white; margin: 5px 0; }
        .score-low { background-color: #4CAF50; }
        .score-mid { background-color: #FF9800; }
        .score-high { background-color: #F44336; }
        .email-preview { border: 1px solid #ddd; margin-top: 15px; background: white; padding: 20px; font-size: 14px; line-height: 1.6; }
        .email-header { background: #5B2D8E; color: white; padding: 20px; text-align: center; margin: -20px -20px 20px -20px; }
        .results-text { white-space: pre-wrap; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; }
        h1 { color: #5B2D8E; }
        h2 { color: #333; margin-top: 30px; }
        details summary { cursor: pointer; color: #5B2D8E; font-weight: 600; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Lead Magnet Assessment Output Samples</h1>
        <p>Real assessment outputs across all 4 types with low/mid/high risk profiles</p>

        <div class="assessment-section">
            <div class="assessment-title">🤖 AI Replacement Risk</div>
            <div class="sample-row">
                <div class="sample-card">
                    <div class="sample-label">Low Risk: Designer</div>
                    <div class="score-badge score-low">15/100</div>
                    <div class="results-text">{ai_risk_low_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{ai_risk_low_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Mid Risk: Data Analyst</div>
                    <div class="score-badge score-mid">50/100</div>
                    <div class="results-text">{ai_risk_mid_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{ai_risk_mid_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">High Risk: Data Entry</div>
                    <div class="score-badge score-high">85/100</div>
                    <div class="results-text">{ai_risk_high_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{ai_risk_high_email}</div>
                    </details>
                </div>
            </div>
        </div>

        <div class="assessment-section">
            <div class="assessment-title">💰 Income Comparison</div>
            <div class="sample-row">
                <div class="sample-card">
                    <div class="sample-label">Entry-level: 20th Percentile</div>
                    <div class="score-badge score-low">30/100</div>
                    <div class="results-text">{income_comparison_low_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{income_comparison_low_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Mid-career: 60th Percentile</div>
                    <div class="score-badge score-mid">60/100</div>
                    <div class="results-text">{income_comparison_mid_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{income_comparison_mid_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Senior: 90th Percentile</div>
                    <div class="score-badge score-high">90/100</div>
                    <div class="results-text">{income_comparison_high_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{income_comparison_high_email}</div>
                    </details>
                </div>
            </div>
        </div>

        <div class="assessment-section">
            <div class="assessment-title">⚠️ Layoff Risk</div>
            <div class="sample-row">
                <div class="sample-card">
                    <div class="sample-label">Stable Industry</div>
                    <div class="score-badge score-low">15/100</div>
                    <div class="results-text">{layoff_risk_low_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{layoff_risk_low_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Volatile Growth</div>
                    <div class="score-badge score-mid">50/100</div>
                    <div class="results-text">{layoff_risk_mid_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{layoff_risk_mid_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Declining Sector</div>
                    <div class="score-badge score-high">80/100</div>
                    <div class="results-text">{layoff_risk_high_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{layoff_risk_high_email}</div>
                    </details>
                </div>
            </div>
        </div>

        <div class="assessment-section">
            <div class="assessment-title">💝 Cuffing Season Score</div>
            <div class="sample-row">
                <div class="sample-card">
                    <div class="sample-label">Low Readiness</div>
                    <div class="score-badge score-low">20/100</div>
                    <div class="results-text">{cuffing_season_low_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{cuffing_season_low_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">Mid Readiness</div>
                    <div class="score-badge score-mid">50/100</div>
                    <div class="results-text">{cuffing_season_mid_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{cuffing_season_mid_email}</div>
                    </details>
                </div>
                <div class="sample-card">
                    <div class="sample-label">High Readiness</div>
                    <div class="score-badge score-high">95/100</div>
                    <div class="results-text">{cuffing_season_high_json}</div>
                    <details><summary>View Email Template</summary>
                        <div class="email-preview">{cuffing_season_high_email}</div>
                    </details>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


def _badge_class(score: int) -> str:
    if score <= 35:
        return "score-low"
    if score <= 65:
        return "score-mid"
    return "score-high"


def build_report(samples: dict) -> str:
    html_content = REPORT_TEMPLATE
    for assessment_key in ("ai_risk", "income_comparison", "layoff_risk", "cuffing_season"):
        for risk_level in ("low", "mid", "high"):
            sample = samples[assessment_key][risk_level]
            json_placeholder = f"{{{assessment_key}_{risk_level}_json}}"
            email_placeholder = f"{{{assessment_key}_{risk_level}_email}}"
            results_json = html.escape(json.dumps(sample["results_json"], indent=2))
            email_html = sample["email_html"]
            html_content = html_content.replace(json_placeholder, results_json)
            html_content = html_content.replace(email_placeholder, email_html)
    return html_content


def main() -> None:
    print("📊 Generating assessment output samples...")

    samples = generate_assessment_samples()
    html_content = build_report(samples)

    output_path = Path("backend/tests/output/assessment_samples_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    print(f"✅ Report generated: {output_path}")
    print(f"📖 Open in browser: file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
