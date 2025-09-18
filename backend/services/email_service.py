import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@mingus.com')
        self.from_name = os.getenv('FROM_NAME', 'Mingus Personal Finance')

    def send_assessment_results(self, email: str, first_name: str, assessment_type: str, 
                              results: Dict, recommendations: List[str]) -> bool:
        """Send personalized assessment results email"""
        try:
            subject = f"🎯 Your {self._get_assessment_title(assessment_type)} Results Are Ready!"
            
            html_content = self._generate_results_email_html(
                first_name, assessment_type, results, recommendations, email
            )
            
            text_content = self._generate_results_email_text(
                first_name, assessment_type, results, recommendations, email
            )
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending assessment results email: {e}")
            return False

    def _get_assessment_title(self, assessment_type: str) -> str:
        """Get human-readable assessment title"""
        titles = {
            'ai-risk': 'AI Replacement Risk Assessment',
            'income-comparison': 'Income Comparison Assessment',
            'cuffing-season': 'Cuffing Season Score',
            'layoff-risk': 'Layoff Risk Assessment'
        }
        return titles.get(assessment_type, 'Assessment')

    def _generate_results_email_html(self, first_name: str, assessment_type: str, 
                                   results: Dict, recommendations: List[str], email: str) -> str:
        """Generate HTML email content"""
        score = results.get('score', 0)
        risk_level = results.get('risk_level', 'Unknown')
        
        # Get assessment-specific content
        assessment_content = self._get_assessment_content(assessment_type, score, risk_level)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Assessment Results</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .content {{ padding: 40px 30px; }}
                .score-section {{ background: #f8f9fa; border-radius: 12px; padding: 30px; margin: 30px 0; text-align: center; }}
                .score-circle {{ display: inline-block; width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 700; margin: 0 auto 20px; }}
                .risk-level {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; margin: 10px 0; }}
                .risk-low {{ background: #d4edda; color: #155724; }}
                .risk-medium {{ background: #fff3cd; color: #856404; }}
                .risk-high {{ background: #f8d7da; color: #721c24; }}
                .recommendations {{ margin: 30px 0; }}
                .recommendation-item {{ background: #ffffff; border-left: 4px solid #667eea; padding: 20px; margin: 15px 0; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .recommendation-item h4 {{ margin: 0 0 10px 0; color: #667eea; font-size: 16px; }}
                .cta-section {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; margin: 30px 0; border-radius: 12px; }}
                .cta-button {{ display: inline-block; background: white; color: #667eea; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; margin: 10px; }}
                .footer {{ background: #f8f9fa; padding: 30px; text-align: center; color: #666; font-size: 14px; }}
                .social-links {{ margin: 20px 0; }}
                .social-links a {{ color: #667eea; text-decoration: none; margin: 0 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Your Results Are Ready!</h1>
                    <p>Hi {first_name}, here are your personalized {self._get_assessment_title(assessment_type)} results</p>
                </div>
                
                <div class="content">
                    <div class="score-section">
                        <div class="score-circle">{score}</div>
                        <h2>Your Score: {score}/100</h2>
                        <div class="risk-level risk-{risk_level.lower()}">{risk_level} Risk</div>
                        <p>{assessment_content['interpretation']}</p>
                    </div>
                    
                    <div class="recommendations">
                        <h3>📋 Your Personalized Recommendations</h3>
                        {self._generate_recommendations_html(recommendations)}
                    </div>
                    
                    <div class="cta-section">
                        <h3>🚀 Ready to Take Action?</h3>
                        <p>Don't let these insights go to waste. Start implementing your personalized plan today!</p>
                        <a href="https://mingus.com/dashboard" class="cta-button">View Full Dashboard</a>
                        <a href="https://mingus.com/assessments" class="cta-button">Take Another Assessment</a>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px; margin: 30px 0;">
                        <h3>💡 What's Next?</h3>
                        <p>{assessment_content['next_steps']}</p>
                        <ul>
                            <li>Track your progress with our personalized dashboard</li>
                            <li>Join our community of like-minded professionals</li>
                            <li>Access exclusive resources and tools</li>
                            <li>Get personalized coaching and support</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This email was sent to {email} because you completed an assessment on Mingus.</p>
                    <div class="social-links">
                        <a href="https://mingus.com">Website</a> |
                        <a href="https://mingus.com/privacy">Privacy Policy</a> |
                        <a href="https://mingus.com/unsubscribe">Unsubscribe</a>
                    </div>
                    <p>© 2025 Mingus Personal Finance. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _generate_results_email_text(self, first_name: str, assessment_type: str, 
                                   results: Dict, recommendations: List[str], email: str) -> str:
        """Generate plain text email content"""
        score = results.get('score', 0)
        risk_level = results.get('risk_level', 'Unknown')
        
        assessment_content = self._get_assessment_content(assessment_type, score, risk_level)
        
        text = f"""
        🎯 Your {self._get_assessment_title(assessment_type)} Results Are Ready!
        
        Hi {first_name},
        
        Thank you for completing your assessment! Here are your personalized results:
        
        📊 YOUR SCORE: {score}/100
        🎯 RISK LEVEL: {risk_level}
        
        {assessment_content['interpretation']}
        
        📋 YOUR PERSONALIZED RECOMMENDATIONS:
        
        """
        
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec}\n"
        
        text += f"""
        
        🚀 READY TO TAKE ACTION?
        
        Don't let these insights go to waste. Start implementing your personalized plan today!
        
        → View Full Dashboard: https://mingus.com/dashboard
        → Take Another Assessment: https://mingus.com/assessments
        
        💡 WHAT'S NEXT?
        
        {assessment_content['next_steps']}
        
        • Track your progress with our personalized dashboard
        • Join our community of like-minded professionals  
        • Access exclusive resources and tools
        • Get personalized coaching and support
        
        Best regards,
        The Mingus Team
        
        ---
        This email was sent to {email} because you completed an assessment on Mingus.
        © 2025 Mingus Personal Finance. All rights reserved.
        """
        
        return text

    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations list"""
        html = ""
        for i, rec in enumerate(recommendations, 1):
            html += f"""
            <div class="recommendation-item">
                <h4>Step {i}</h4>
                <p>{rec}</p>
            </div>
            """
        return html

    def _get_assessment_content(self, assessment_type: str, score: int, risk_level: str) -> Dict:
        """Get assessment-specific content based on type and results"""
        content = {
            'ai-risk': {
                'interpretation': f"Based on your score of {score}, you have a {risk_level.lower()} risk of AI replacement. Your role shows {'strong' if score < 40 else 'moderate' if score < 70 else 'high'} potential for automation.",
                'next_steps': "Focus on developing skills that complement AI rather than compete with it. Consider learning to work alongside AI tools and developing your emotional intelligence and creative problem-solving abilities."
            },
            'income-comparison': {
                'interpretation': f"Your score of {score} indicates you are {'below' if score < 40 else 'at' if score < 70 else 'above'} market rate for your role and experience level.",
                'next_steps': "Use this data to inform your salary negotiations and career planning. Consider additional certifications or skills development to increase your market value."
            },
            'cuffing-season': {
                'interpretation': f"With a score of {score}, you are {'not quite ready' if score < 40 else 'somewhat ready' if score < 70 else 'very ready'} for meaningful connections this season.",
                'next_steps': "Focus on building genuine connections and being authentic in your interactions. Work on your communication skills and take care of your physical and mental health."
            },
            'layoff-risk': {
                'interpretation': f"Your score of {score} suggests a {risk_level.lower()} risk of layoff based on current market conditions and your role.",
                'next_steps': "Build strong relationships with key stakeholders, develop in-demand skills, and create a personal brand. Consider having a backup plan and emergency fund."
            }
        }
        
        return content.get(assessment_type, {
            'interpretation': f"Your score of {score} indicates {risk_level.lower()} risk based on your responses.",
            'next_steps': "Use these insights to make informed decisions about your future."
        })

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                # In development, just log the email
                logger.info(f"Development mode: Email would be sent to {to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Content: {text_content[:200]}...")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email to new users"""
        try:
            subject = "🎉 Welcome to Mingus - Your Personal Finance Journey Starts Here!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to Mingus</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                    .content {{ padding: 40px 30px; }}
                    .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Welcome to Mingus!</h1>
                        <p>Hi {first_name}, your personal finance journey starts here</p>
                    </div>
                    <div class="content">
                        <h2>Ready to Build Wealth?</h2>
                        <p>You've taken the first step by completing your assessment. Now let's turn those insights into action!</p>
                        <a href="https://mingus.com/dashboard" class="cta-button">View Your Dashboard</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            🎉 Welcome to Mingus!
            
            Hi {first_name},
            
            Welcome to Mingus! You've taken the first step by completing your assessment. 
            Now let's turn those insights into action!
            
            Ready to build wealth? View your dashboard: https://mingus.com/dashboard
            
            Best regards,
            The Mingus Team
            """
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False
