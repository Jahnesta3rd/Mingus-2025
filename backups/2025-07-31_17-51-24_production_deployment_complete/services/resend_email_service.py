import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64

logger = logging.getLogger(__name__)

class ResendEmailService:
    """Resend email service for MINGUS backend"""
    
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.from_name = os.getenv('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        self.base_url = 'https://api.resend.com'
        
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str = None,
        attachments: List[Dict[str, Any]] = None,
        template_id: str = None,
        template_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send email via Resend API"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Resend API key not configured'
                }
            
            # Prepare email data
            email_data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': [to_email],
                'subject': subject,
                'html': html_content
            }
            
            # Add text content if provided
            if text_content:
                email_data['text'] = text_content
            
            # Add template if specified
            if template_id:
                email_data['template_id'] = template_id
                if template_data:
                    email_data['template_data'] = template_data
            
            # Add attachments if provided
            if attachments:
                email_data['attachments'] = attachments
            
            # Send email via Resend API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/emails',
                json=email_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent successfully to {to_email}: {result.get('id')}")
                return {
                    'success': True,
                    'email_id': result.get('id'),
                    'message': 'Email sent successfully'
                }
            else:
                error_msg = f"Resend API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_welcome_email(self, user_email: str, user_name: str) -> Dict[str, Any]:
        """Send welcome email to new users"""
        subject = "Welcome to MINGUS - Your Financial Wellness Journey Begins"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>Welcome to MINGUS</h1>
                <p>Your Personal Finance & Relationship Companion</p>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>Hi {user_name}! 👋</h2>
                <p>Welcome to MINGUS! We're excited to help you build wealth while maintaining healthy relationships.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>What you can do with MINGUS:</h3>
                    <ul>
                        <li>📊 Track your financial health and relationship with money</li>
                        <li>💡 Get personalized insights and recommendations</li>
                        <li>🎯 Set and achieve financial goals</li>
                        <li>📈 Monitor your progress over time</li>
                        <li>🤝 Build healthier financial relationships</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Get Started
                    </a>
                </div>
                
                <p>If you have any questions, just reply to this email. We're here to help!</p>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_password_reset_email(self, user_email: str, reset_token: str) -> Dict[str, Any]:
        """Send password reset email"""
        subject = "Reset Your MINGUS Password"
        reset_url = f"{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/reset-password?token={reset_token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc3545; color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>Password Reset Request</h1>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>Hi there!</h2>
                <p>We received a request to reset your MINGUS password.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                
                <p><strong>This link will expire in 1 hour.</strong></p>
                
                <p>If you didn't request this password reset, you can safely ignore this email.</p>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_verification_email(self, user_email: str, verification_token: str) -> Dict[str, Any]:
        """Send email verification email"""
        subject = "Verify Your MINGUS Email Address"
        verify_url = f"{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/verify-email?token={verification_token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #28a745; color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>Verify Your Email</h1>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>Welcome to MINGUS!</h2>
                <p>Please verify your email address to complete your account setup.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>If you didn't create a MINGUS account, you can safely ignore this email.</p>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_notification_email(
        self, 
        user_email: str, 
        subject: str, 
        message: str, 
        notification_type: str = 'general'
    ) -> Dict[str, Any]:
        """Send notification email"""
        # Get notification-specific styling
        colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8',
            'general': '#6c757d'
        }
        
        color = colors.get(notification_type, colors['general'])
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>MINGUS Notification</h1>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>{subject}</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    {message}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/dashboard" 
                       style="background: {color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Dashboard
                    </a>
                </div>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_pdf_report_email(
        self, 
        user_email: str, 
        user_name: str, 
        report_type: str, 
        pdf_url: str,
        report_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send email with PDF report attachment"""
        subject = f"Your MINGUS {report_type.title()} Report"
        
        # Prepare attachment data
        attachments = []
        if pdf_url and pdf_url.startswith('http'):
            try:
                # Download PDF and convert to base64
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    pdf_content = base64.b64encode(response.content).decode('utf-8')
                    attachments.append({
                        'filename': f'mingus_{report_type}_report.pdf',
                        'content': pdf_content
                    })
            except Exception as e:
                logger.error(f"Error downloading PDF: {e}")
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>Your {report_type.title()} Report</h1>
                <p>Personalized insights from MINGUS</p>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>Hi {user_name}!</h2>
                <p>Your personalized {report_type} report is ready and attached to this email.</p>
                
                <div style="background: #f0fff4; border: 2px solid #68d391; padding: 25px; border-radius: 12px; text-align: center; margin: 25px 0;">
                    <div style="font-size: 24px; margin-bottom: 10px;">📄</div>
                    <h3 style="color: #2f855a; margin-bottom: 15px;">Your {report_type.title()} Report</h3>
                    <p style="color: #2f855a; margin-bottom: 20px;">
                        We've created a detailed report with your personalized insights and recommendations.
                    </p>
                    <a href="{pdf_url}" style="background: #38a169; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        📥 Download Report
                    </a>
                </div>
                
                <p><strong>What's included in your report:</strong></p>
                <ul>
                    <li>📊 Detailed analysis of your financial situation</li>
                    <li>💡 Personalized recommendations and strategies</li>
                    <li>🎯 Actionable next steps and goals</li>
                    <li>📈 Progress tracking tools and resources</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Dashboard
                    </a>
                </div>
                
                <p>If you have any questions about your report, just reply to this email!</p>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content, attachments=attachments)
    
    def send_billing_email(
        self, 
        user_email: str, 
        user_name: str, 
        invoice_data: Dict[str, Any],
        pdf_url: str = None
    ) -> Dict[str, Any]:
        """Send billing/invoice email"""
        subject = f"Invoice #{invoice_data.get('invoice_number', 'N/A')} from MINGUS"
        
        # Prepare attachment data
        attachments = []
        if pdf_url and pdf_url.startswith('http'):
            try:
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    pdf_content = base64.b64encode(response.content).decode('utf-8')
                    attachments.append({
                        'filename': f'invoice_{invoice_data.get("invoice_number", "N/A")}.pdf',
                        'content': pdf_content
                    })
            except Exception as e:
                logger.error(f"Error downloading invoice PDF: {e}")
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #6c757d; color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>MINGUS Invoice</h1>
                <p>Invoice #{invoice_data.get('invoice_number', 'N/A')}</p>
            </div>
            <div style="padding: 30px; background: white; border: 1px solid #ddd;">
                <h2>Hi {user_name}!</h2>
                <p>Thank you for your business. Here's your invoice for MINGUS services.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Invoice Details:</h3>
                    <p><strong>Invoice Number:</strong> {invoice_data.get('invoice_number', 'N/A')}</p>
                    <p><strong>Amount:</strong> ${invoice_data.get('amount', 0):.2f}</p>
                    <p><strong>Due Date:</strong> {invoice_data.get('due_date', 'N/A')}</p>
                    <p><strong>Status:</strong> {invoice_data.get('status', 'N/A')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('FRONTEND_URL', 'https://mingusapp.com')}/billing" 
                       style="background: #6c757d; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Billing
                    </a>
                </div>
                
                <p>If you have any questions about this invoice, please contact our support team.</p>
                
                <p>Best regards,<br>The MINGUS Team</p>
            </div>
        </div>
        """
        
        return self.send_email(user_email, subject, html_content, attachments=attachments)

# Create singleton instance
resend_email_service = ResendEmailService() 