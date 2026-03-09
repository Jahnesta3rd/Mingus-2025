import os
import logging
import resend
from typing import Optional

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")

FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@mingusapp.com")
FROM_NAME  = os.getenv("FROM_NAME",  "Mingus")

ASSESSMENT_LABELS = {
    "ai-risk":                "AI Replacement Risk",
    "income-comparison":      "Income Comparison",
    "cuffing-season":         "Cuffing Season Score",
    "layoff-risk":            "Layoff Risk",
    "vehicle-financial-health": "Vehicle Financial Health",
}

class EmailService:

    def send_assessment_results(
        self,
        email: str,
        first_name: str,
        assessment_type: str,
        results: dict,
        recommendations: list,
    ) -> bool:
        try:
            label = ASSESSMENT_LABELS.get(assessment_type, assessment_type.replace("-", " ").title())
            score = results.get("score", "N/A")
            risk  = results.get("risk_level", "")

            recs_html = "".join(
                f"<li style='margin-bottom:8px'>{r}</li>"
                for r in (recommendations or [])
            )
            recs_block = (
                f"<ul style='padding-left:20px'>{recs_html}</ul>"
                if recs_html
                else "<p>Check your dashboard for personalised recommendations.</p>"
            )

            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#2563eb">Your {label} Results</h1>
  <p>Hi {first_name},</p>
  <p>Thanks for completing your assessment. Here's a summary of your results:</p>
  <div style="background:#f3f4f6;border-radius:8px;padding:20px;margin:20px 0">
    <p style="font-size:2rem;font-weight:bold;margin:0">{score}<span style="font-size:1rem;color:#6b7280">/100</span></p>
    <p style="color:#6b7280;margin:4px 0 0">Risk level: <strong>{risk}</strong></p>
  </div>
  <h2 style="font-size:1.1rem">Recommendations</h2>
  {recs_block}
  <p style="margin-top:32px">
    <a href="https://mingusapp.com/dashboard"
       style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600">
      View Full Dashboard
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0">
  <p style="color:#9ca3af;font-size:0.8rem">
    © 2025 Mingus · <a href="https://mingusapp.com" style="color:#9ca3af">mingusapp.com</a>
  </p>
</body>
</html>"""

            resend.Emails.send({
                "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
                "to":      [email],
                "subject": f"Your {label} Results — Mingus",
                "html":    html,
            })
            return True

        except Exception as e:
            logger.exception("Resend error sending assessment results to %s: %s", email, e)
            return False

    def send_welcome_email(self, email: str, first_name: str) -> bool:
        try:
            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#2563eb">Welcome to Mingus, {first_name}!</h1>
  <p>Your account is ready. Head to your dashboard to explore your career protection tools.</p>
  <p style="margin-top:32px">
    <a href="https://mingusapp.com/dashboard"
       style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600">
      Go to Dashboard
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0">
  <p style="color:#9ca3af;font-size:0.8rem">© 2025 Mingus · <a href="https://mingusapp.com" style="color:#9ca3af">mingusapp.com</a></p>
</body>
</html>"""

            resend.Emails.send({
                "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
                "to":      [email],
                "subject": "Welcome to Mingus 🎉",
                "html":    html,
            })
            return True

        except Exception as e:
            logger.exception("Resend error sending welcome email to %s: %s", email, e)
            return False
