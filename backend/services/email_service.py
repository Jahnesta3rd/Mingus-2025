import os
import logging
try:
    import resend  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    resend = None
from typing import Optional
from loguru import logger as loguru_logger

logger = logging.getLogger(__name__)

ASSESSMENT_LABELS = {
    "ai-risk":                "AI Replacement Risk",
    "income-comparison":      "Income Comparison",
    "cuffing-season":         "Cuffing Season Score",
    "layoff-risk":            "Layoff Risk",
    "vehicle-financial-health": "Vehicle Financial Health",
}

def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    mail_from: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """Module-level send helper (mockable in tests)."""
    return EmailService().send_email(
        to=to,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        mail_from=mail_from,
        reply_to=reply_to,
    )


class EmailService:

    def __init__(self) -> None:
        self.from_email = os.environ.get("FROM_EMAIL", "hello@mingusapp.com")
        self.from_name = os.environ.get("FROM_NAME", "Mingus")
        if not self.from_email.endswith("@mingusapp.com"):
            loguru_logger.warning(
                "FROM_EMAIL domain mismatch — Resend may reject: {}",
                self.from_email,
            )
        if resend is not None:
            resend.api_key = os.environ.get("RESEND_API_KEY", "")

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

            from_addr = mail_from if mail_from else f"{self.from_name} <{self.from_email}>"
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
        reply_to: Optional[str] = None,
        assessment_id: Optional[int] = None,
        token: Optional[str] = None,
        is_resend: bool = False,
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
                else "<p>Check your results for personalised recommendations.</p>"
            )

            if assessment_id and token:
                public_base = os.environ.get(
                    "PUBLIC_APP_URL", "https://mingusapp.com"
                ).rstrip("/")
                results_url = (
                    f"{public_base}/api/assessments/{assessment_id}/track-click"
                    f"?token={token}"
                )
                cta_label = "View My Results"
            else:
                results_url = "https://mingusapp.com/dashboard"
                cta_label = "View Full Dashboard"

            subject_prefix = "Your new " if is_resend else "Your "
            intro = (
                "Here's a fresh link to your assessment results:"
                if is_resend
                else "Thanks for completing your assessment. Here's a summary of your results:"
            )

            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#2563eb">{subject_prefix}{label} Results</h1>
  <p>Hi {first_name},</p>
  <p>{intro}</p>
  <div style="background:#f3f4f6;border-radius:8px;padding:20px;margin:20px 0">
    <p style="font-size:2rem;font-weight:bold;margin:0">{score}<span style="font-size:1rem;color:#6b7280">/100</span></p>
    <p style="color:#6b7280;margin:4px 0 0">Risk level: <strong>{risk}</strong></p>
  </div>
  <h2 style="font-size:1.1rem">Recommendations</h2>
  {recs_block}
  <p style="margin-top:32px">
    <a href="{results_url}"
       style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600">
      {cta_label}
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0">
  <p style="color:#9ca3af;font-size:0.8rem">
    © 2025 Mingus · <a href="https://mingusapp.com" style="color:#9ca3af">mingusapp.com</a>
  </p>
</body>
</html>"""

            payload: dict = {
                "from":    f"{self.from_name} <{self.from_email}>",
                "to":      [email],
                "subject": f"{subject_prefix}{label} Results — Mingus",
                "html":    html,
            }
            if reply_to:
                payload["reply_to"] = [reply_to]
            resend.Emails.send(payload)
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
                "from":    f"{self.from_name} <{self.from_email}>",
                "to":      [email],
                "subject": "Welcome to Mingus 🎉",
                "html":    html,
            })
            return True

        except Exception as e:
            logger.exception("Resend error sending welcome email to %s: %s", email, e)
            return False
