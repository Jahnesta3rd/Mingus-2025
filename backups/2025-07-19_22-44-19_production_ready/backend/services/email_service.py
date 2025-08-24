import logging
from typing import Optional, Dict, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to users."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@mingus.com')
        self.from_name = os.getenv('FROM_NAME', 'Mingus Financial Wellness')
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email with HTML and text content."""
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
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        subject = "🎉 Welcome to Mingus! Your Financial Wellness Journey Begins"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Mingus</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
                .feature {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Mingus!</h1>
                    <p>Hi {user_name}, your financial wellness journey starts now</p>
                </div>
                
                <div class="content">
                    <h2>You're All Set!</h2>
                    <p>Congratulations on completing your onboarding! You've taken the first step toward financial wellness and joined a community of {self._get_community_stats()['total_members']:,}+ members.</p>
                    
                    <div class="feature">
                        <h3>📊 Your Personalized Dashboard</h3>
                        <p>Your dashboard is ready with insights tailored to your financial situation and goals.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🎯 Weekly Check-ins</h3>
                        <p>Your first wellness check-in is scheduled. It only takes 2 minutes and helps you track your progress.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>💡 Smart Insights</h3>
                        <p>Get personalized recommendations based on your spending patterns and financial goals.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🤝 Community Support</h3>
                        <p>Join discussions, share achievements, and get motivated by our supportive community.</p>
                    </div>
                    
                    <a href="{self._get_dashboard_url()}" class="button">Go to Your Dashboard</a>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>Complete your first weekly check-in</li>
                        <li>Explore your personalized insights</li>
                        <li>Connect with the community</li>
                        <li>Download our mobile app for on-the-go access</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Questions? Reply to this email or visit our <a href="{self._get_help_url()}">Help Center</a></p>
                    <p>© 2024 Mingus Financial Wellness. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Mingus!
        
        Hi {user_name},
        
        Congratulations on completing your onboarding! You've taken the first step toward financial wellness and joined a community of {self._get_community_stats()['total_members']:,}+ members.
        
        You're All Set!
        - Your personalized dashboard is ready with insights tailored to your financial situation
        - Your first weekly check-in is scheduled (takes only 2 minutes)
        - Get personalized recommendations based on your spending patterns
        - Join our supportive community for motivation and tips
        
        What's Next?
        1. Complete your first weekly check-in
        2. Explore your personalized insights
        3. Connect with the community
        4. Download our mobile app for on-the-go access
        
        Go to your dashboard: {self._get_dashboard_url()}
        
        Questions? Reply to this email or visit our Help Center: {self._get_help_url()}
        
        © 2024 Mingus Financial Wellness. All rights reserved.
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_checkin_confirmation(self, user_email: str, user_name: str, scheduled_date: datetime, frequency: str) -> bool:
        """Send confirmation email for scheduled check-in."""
        subject = "✅ Your First Check-in is Scheduled!"
        
        formatted_date = scheduled_date.strftime("%A, %B %d at %I:%M %p")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Check-in Scheduled</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .schedule-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border: 2px solid #28a745; text-align: center; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Check-in Scheduled!</h1>
                    <p>Hi {user_name}, your wellness check-ins are ready to go</p>
                </div>
                
                <div class="content">
                    <h2>Your First Check-in is Set</h2>
                    <p>Great news! Your first wellness check-in has been scheduled. These quick check-ins help you track your progress and build healthy financial habits.</p>
                    
                    <div class="schedule-box">
                        <h3>📅 Your Schedule</h3>
                        <p><strong>First Check-in:</strong> {formatted_date}</p>
                        <p><strong>Frequency:</strong> {frequency.title()}</p>
                        <p><strong>Duration:</strong> Just 2 minutes</p>
                    </div>
                    
                    <h3>What to Expect</h3>
                    <ul>
                        <li>Quick questions about your financial wellness</li>
                        <li>Progress tracking toward your goals</li>
                        <li>Personalized insights and recommendations</li>
                        <li>Motivation to stay on track</li>
                    </ul>
                    
                    <a href="{self._get_checkin_url()}" class="button">Complete Check-in Now</a>
                    
                    <p><strong>Need to adjust your schedule?</strong></p>
                    <p>You can always change your reminder preferences in your <a href="{self._get_settings_url()}">account settings</a>.</p>
                </div>
                
                <div class="footer">
                    <p>Questions? Reply to this email or visit our <a href="{self._get_help_url()}">Help Center</a></p>
                    <p>© 2024 Mingus Financial Wellness. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Check-in Scheduled!
        
        Hi {user_name},
        
        Great news! Your first wellness check-in has been scheduled. These quick check-ins help you track your progress and build healthy financial habits.
        
        Your Schedule:
        - First Check-in: {formatted_date}
        - Frequency: {frequency.title()}
        - Duration: Just 2 minutes
        
        What to Expect:
        - Quick questions about your financial wellness
        - Progress tracking toward your goals
        - Personalized insights and recommendations
        - Motivation to stay on track
        
        Complete your check-in now: {self._get_checkin_url()}
        
        Need to adjust your schedule? You can change your reminder preferences in your account settings: {self._get_settings_url()}
        
        Questions? Reply to this email or visit our Help Center: {self._get_help_url()}
        
        © 2024 Mingus Financial Wellness. All rights reserved.
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_reminder_email(self, user_email: str, user_name: str, reminder_data: Dict[str, Any]) -> bool:
        """Send reminder email for check-in."""
        subject = "🔔 Time for Your Weekly Check-in!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Check-in Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .stats-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #007bff; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Time for Your Check-in!</h1>
                    <p>Hi {user_name}, let's check in on your financial wellness</p>
                </div>
                
                <div class="content">
                    <h2>Your Weekly Wellness Check-in</h2>
                    <p>It's time for your weekly check-in! This quick 2-minute survey helps you track your progress and get personalized insights.</p>
                    
                    <div class="stats-box">
                        <h3>📊 Your Progress</h3>
                        <p><strong>Current Streak:</strong> {reminder_data.get('streak', 0)} weeks</p>
                        <p><strong>Last Check-in:</strong> {reminder_data.get('last_checkin', 'Never')}</p>
                        <p><strong>Community Average:</strong> {reminder_data.get('community_average', 0)} weeks</p>
                    </div>
                    
                    <a href="{self._get_checkin_url()}" class="button">Start My Check-in</a>
                    
                    <p><strong>Why Check-ins Matter:</strong></p>
                    <ul>
                        <li>Track your financial wellness progress</li>
                        <li>Get personalized insights and recommendations</li>
                        <li>Stay motivated with your goals</li>
                        <li>Build healthy financial habits</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Questions? Reply to this email or visit our <a href="{self._get_help_url()}">Help Center</a></p>
                    <p>© 2024 Mingus Financial Wellness. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def _get_community_stats(self) -> Dict[str, int]:
        """Get community statistics for email content."""
        # This would typically come from the database
        return {
            'total_members': 15420,
            'active_this_week': 8234,
            'average_savings': 247
        }
    
    def _get_dashboard_url(self) -> str:
        """Get dashboard URL."""
        base_url = os.getenv('BASE_URL', 'https://mingus.com')
        return f"{base_url}/dashboard"
    
    def _get_checkin_url(self) -> str:
        """Get check-in URL."""
        base_url = os.getenv('BASE_URL', 'https://mingus.com')
        return f"{base_url}/checkin"
    
    def _get_settings_url(self) -> str:
        """Get settings URL."""
        base_url = os.getenv('BASE_URL', 'https://mingus.com')
        return f"{base_url}/settings"
    
    def _get_help_url(self) -> str:
        """Get help center URL."""
        base_url = os.getenv('BASE_URL', 'https://mingus.com')
        return f"{base_url}/help" 