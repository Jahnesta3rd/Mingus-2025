import os
import logging
try:
    import resend  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    resend = None
from typing import Optional

logger = logging.getLogger(__name__)

# Configure Resend only if the dependency is available.
if resend is not None:
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

    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        mail_from: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send a transactional HTML email via Resend (shared by Celery tasks and services)."""
        try:
            if resend is None:
                logger.warning("Resend dependency not installed; skipping email send.")
                return False

            from_addr = mail_from if mail_from else f"{FROM_NAME} <{FROM_EMAIL}>"
            payload: dict = {
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": html_body,
            }
            if text_body:
                payload["text"] = text_body
            if reply_to:
                payload["reply_to"] = [reply_to] if isinstance(reply_to, str) else reply_to

            resend.Emails.send(payload)
            return True

        except Exception as e:
            logger.exception("Resend error sending email to %s: %s", to, e)
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """Compatibility wrapper used by notification and check-in services."""
        return self.send_email(
            to_email,
            subject,
            html_content,
            text_body=text_content or None,
        )

    def send_assessment_results(
        self,
        email: str,
        first_name: str,
        assessment_type: str,
        results: dict,
        recommendations: list,
    ) -> bool:
        try:
            if resend is None:
                logger.warning("Resend dependency not installed; skipping email send.")
                return False

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
            if resend is None:
                logger.warning("Resend dependency not installed; skipping welcome email send.")
                return False

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
