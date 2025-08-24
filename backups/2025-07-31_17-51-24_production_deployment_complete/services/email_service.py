import logging
from typing import Optional, Dict, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

# Import Resend service
from .resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to users with Resend integration."""
    
    def __init__(self):
        # Legacy SMTP configuration (fallback)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@mingusapp.com')
        self.from_name = os.getenv('FROM_NAME', 'Mingus Financial Wellness')
        
        # Email provider preference
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'resend').lower()
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email with HTML and text content using preferred provider."""
        try:
            # Use Resend if configured and preferred
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                )
                return result.get('success', False)
            
            # Fallback to SMTP
            return self._send_email_smtp(to_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_email_smtp(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email using SMTP (legacy method)."""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return False
                
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new users."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_welcome_email(user_email, user_name)
                return result.get('success', False)
            else:
                # Fallback to SMTP welcome email
                subject = "Welcome to MINGUS - Your Financial Wellness Journey Begins"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Welcome to MINGUS!</h1>
                    <p>Hi {user_name},</p>
                    <p>Welcome to MINGUS! We're excited to help you build wealth while maintaining healthy relationships.</p>
                    <p>Best regards,<br>The MINGUS Team</p>
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {e}")
            return False
    
    def send_password_reset_email(self, user_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_password_reset_email(user_email, reset_token)
                return result.get('success', False)
            else:
                # Fallback to SMTP password reset email
                subject = "Reset Your MINGUS Password"
                reset_url = f"{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/reset-password?token={reset_token}"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Password Reset Request</h1>
                    <p>Click the link below to reset your password:</p>
                    <a href="{reset_url}">Reset Password</a>
                    <p>This link will expire in 1 hour.</p>
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user_email}: {e}")
            return False
    
    def send_verification_email(self, user_email: str, verification_token: str) -> bool:
        """Send email verification email."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_verification_email(user_email, verification_token)
                return result.get('success', False)
            else:
                # Fallback to SMTP verification email
                subject = "Verify Your MINGUS Email Address"
                verify_url = f"{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/verify-email?token={verification_token}"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Verify Your Email</h1>
                    <p>Click the link below to verify your email address:</p>
                    <a href="{verify_url}">Verify Email Address</a>
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send verification email to {user_email}: {e}")
            return False
    
    def send_notification_email(self, user_email: str, subject: str, message: str, notification_type: str = 'general') -> bool:
        """Send notification email."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_notification_email(user_email, subject, message, notification_type)
                return result.get('success', False)
            else:
                # Fallback to SMTP notification email
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>{subject}</h1>
                    <p>{message}</p>
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send notification email to {user_email}: {e}")
            return False
    
    def send_pdf_report_email(self, user_email: str, user_name: str, report_type: str, pdf_url: str, report_data: Dict[str, Any] = None) -> bool:
        """Send email with PDF report attachment."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_pdf_report_email(user_email, user_name, report_type, pdf_url, report_data)
                return result.get('success', False)
            else:
                # Fallback to SMTP with PDF link
                subject = f"Your MINGUS {report_type.title()} Report"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Your {report_type.title()} Report</h1>
                    <p>Hi {user_name},</p>
                    <p>Your personalized {report_type} report is ready.</p>
                    <a href="{pdf_url}">Download Report</a>
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send PDF report email to {user_email}: {e}")
            return False
    
    def send_billing_email(self, user_email: str, user_name: str, invoice_data: Dict[str, Any], pdf_url: str = None) -> bool:
        """Send billing/invoice email."""
        try:
            if self.email_provider == 'resend' and resend_email_service.api_key:
                result = resend_email_service.send_billing_email(user_email, user_name, invoice_data, pdf_url)
                return result.get('success', False)
            else:
                # Fallback to SMTP billing email
                subject = f"Invoice #{invoice_data.get('invoice_number', 'N/A')} from MINGUS"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>MINGUS Invoice</h1>
                    <p>Hi {user_name},</p>
                    <p>Invoice #{invoice_data.get('invoice_number', 'N/A')}</p>
                    <p>Amount: ${invoice_data.get('amount', 0):.2f}</p>
                    <p>Due Date: {invoice_data.get('due_date', 'N/A')}</p>
                    {f'<a href="{pdf_url}">Download Invoice</a>' if pdf_url else ''}
                </div>
                """
                return self._send_email_smtp(user_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send billing email to {user_email}: {e}")
            return False 