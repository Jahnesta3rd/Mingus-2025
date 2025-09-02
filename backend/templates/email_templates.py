"""
Complete Email Templates for MINGUS Email Automation
Contains all HTML and text templates for welcome series, segmented messaging, and behavioral triggers
"""

def get_welcome_3_html() -> str:
    """Success Stories Email Template"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success Stories from {{industry}} Professionals</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .story-card { background: white; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #10b981; }
            .quote { font-style: italic; color: #666; margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
            .stats { display: flex; justify-content: space-around; text-align: center; margin: 20px 0; }
            .stat { flex: 1; padding: 15px; }
            .stat-number { font-size: 24px; font-weight: bold; color: #10b981; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 Success Stories from {{industry}} Professionals</h1>
                <p>{{first_name}}, see how others in your industry are thriving with AI</p>
            </div>
            
            <div class="content">
                <h2>Real Stories from {{industry}} Professionals</h2>
                <p>Here are inspiring stories from professionals who successfully navigated AI disruption in {{industry}}:</p>
                
                <div class="story-card">
                    <h3>Sarah Chen - Marketing Director</h3>
                    <p><strong>Challenge:</strong> 65% automation risk in traditional marketing tasks</p>
                    <p><strong>Solution:</strong> Learned AI-powered marketing tools and data analysis</p>
                    <div class="quote">
                        "I was worried AI would replace my job, but instead it made me 3x more productive. I now focus on strategy while AI handles routine tasks."
                    </div>
                    <p><strong>Result:</strong> 40% salary increase, promoted to VP of Digital Marketing</p>
                </div>
                
                <div class="story-card">
                    <h3>Marcus Johnson - Software Engineer</h3>
                    <p><strong>Challenge:</strong> 45% automation risk in coding tasks</p>
                    <p><strong>Solution:</strong> Mastered AI coding assistants and prompt engineering</p>
                    <div class="quote">
                        "AI coding tools help me write better code faster. I spend more time on architecture and less on boilerplate."
                    </div>
                    <p><strong>Result:</strong> 50% faster development, leading AI integration projects</p>
                </div>
                
                <div class="story-card">
                    <h3>Dr. Lisa Rodriguez - Healthcare Administrator</h3>
                    <p><strong>Challenge:</strong> 35% automation risk in administrative tasks</p>
                    <p><strong>Solution:</strong> Implemented AI-powered patient management systems</p>
                    <div class="quote">
                        "AI helps us provide better patient care by automating routine tasks. Our team can focus on what matters most."
                    </div>
                    <p><strong>Result:</strong> 30% efficiency improvement, better patient satisfaction scores</p>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">87%</div>
                        <div>Career advancement rate</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">3.2x</div>
                        <div>Average productivity increase</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">$45K</div>
                        <div>Average salary increase</div>
                    </div>
                </div>
                
                <h3>Your Success Story Starts Here</h3>
                <p>These professionals started exactly where you are now. They took action and transformed their careers with AI.</p>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/success-stories" class="cta-button">Read More Success Stories →</a>
                </div>
                
                <p><strong>Coming up next:</strong> Advanced career planning strategies tailored to your {{risk_level}} risk level.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_3_text() -> str:
    return """
Success Stories from {{industry}} Professionals

Hi {{first_name}},

Here are inspiring stories from {{industry}} professionals who successfully navigated AI disruption:

Sarah Chen - Marketing Director
Challenge: 65% automation risk in traditional marketing tasks
Solution: Learned AI-powered marketing tools and data analysis
Quote: "I was worried AI would replace my job, but instead it made me 3x more productive."
Result: 40% salary increase, promoted to VP of Digital Marketing

Marcus Johnson - Software Engineer
Challenge: 45% automation risk in coding tasks
Solution: Mastered AI coding assistants and prompt engineering
Quote: "AI coding tools help me write better code faster."
Result: 50% faster development, leading AI integration projects

Dr. Lisa Rodriguez - Healthcare Administrator
Challenge: 35% automation risk in administrative tasks
Solution: Implemented AI-powered patient management systems
Quote: "AI helps us provide better patient care by automating routine tasks."
Result: 30% efficiency improvement, better patient satisfaction scores

Success Statistics:
- 87% career advancement rate
- 3.2x average productivity increase
- $45K average salary increase

Your success story starts here: https://mingusapp.com/success-stories

Coming up next: Advanced career planning strategies.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """

def get_welcome_4_html() -> str:
    """Advanced Career Planning Email Template"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your AI Career Protection Strategy</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .strategy-card { background: white; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .priority-high { border-left: 4px solid #ef4444; }
            .priority-medium { border-left: 4px solid #f59e0b; }
            .priority-low { border-left: 4px solid #10b981; }
            .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
            .timeline { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .timeline-item { display: flex; margin: 15px 0; align-items: center; }
            .timeline-marker { width: 20px; height: 20px; border-radius: 50%; background: #10b981; margin-right: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Your AI Career Protection Strategy</h1>
                <p>{{first_name}}, here's your personalized career protection plan</p>
            </div>
            
            <div class="content">
                <h2>Your {{risk_level}} Risk Level Strategy</h2>
                <p>Based on your {{automation_score}}% automation risk, here's your comprehensive career protection plan:</p>
                
                <div class="strategy-card priority-high">
                    <h3>🚨 Immediate Actions (Next 30 Days)</h3>
                    <ul>
                        <li><strong>Skill Assessment:</strong> Identify AI-vulnerable skills in your role</li>
                        <li><strong>Learning Plan:</strong> Start AI collaboration training</li>
                        <li><strong>Network Building:</strong> Connect with AI-savvy professionals</li>
                        <li><strong>Market Research:</strong> Monitor AI trends in {{industry}}</li>
                    </ul>
                </div>
                
                <div class="strategy-card priority-medium">
                    <h3>📈 Short-term Goals (3-6 Months)</h3>
                    <ul>
                        <li><strong>Skill Development:</strong> Master 2-3 AI tools relevant to your role</li>
                        <li><strong>Project Leadership:</strong> Lead AI integration initiatives</li>
                        <li><strong>Certification:</strong> Obtain AI-related certifications</li>
                        <li><strong>Portfolio Building:</strong> Document AI-enhanced achievements</li>
                    </ul>
                </div>
                
                <div class="strategy-card priority-low">
                    <h3>🎯 Long-term Vision (6-12 Months)</h3>
                    <ul>
                        <li><strong>Career Pivot:</strong> Transition to AI-augmented roles</li>
                        <li><strong>Leadership:</strong> Position yourself as an AI strategy expert</li>
                        <li><strong>Innovation:</strong> Drive AI adoption in your organization</li>
                        <li><strong>Mentorship:</strong> Help others navigate AI disruption</li>
                    </ul>
                </div>
                
                <div class="timeline">
                    <h3>Your 90-Day Action Timeline</h3>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div><strong>Week 1-2:</strong> Complete AI skills assessment and create learning plan</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div><strong>Week 3-4:</strong> Start AI tool training and join professional communities</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div><strong>Month 2:</strong> Implement AI tools in current projects</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div><strong>Month 3:</strong> Lead AI initiatives and document achievements</div>
                    </div>
                </div>
                
                <h3>Recommended Resources for {{industry}}</h3>
                <ul>
                    <li><strong>Courses:</strong> AI for {{industry}} Professionals</li>
                    <li><strong>Tools:</strong> Industry-specific AI platforms</li>
                    <li><strong>Communities:</strong> {{industry}} AI networking groups</li>
                    <li><strong>Events:</strong> AI conferences and workshops</li>
                </ul>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/career-strategy" class="cta-button">Get Your Complete Career Strategy →</a>
                </div>
                
                <p><strong>Coming up next:</strong> Exclusive offer for our complete career intelligence report.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_4_text() -> str:
    return """
Your AI Career Protection Strategy

Hi {{first_name}},

Here's your personalized career protection plan for {{risk_level}} risk level:

IMMEDIATE ACTIONS (Next 30 Days):
- Skill Assessment: Identify AI-vulnerable skills in your role
- Learning Plan: Start AI collaboration training
- Network Building: Connect with AI-savvy professionals
- Market Research: Monitor AI trends in {{industry}}

SHORT-TERM GOALS (3-6 Months):
- Skill Development: Master 2-3 AI tools relevant to your role
- Project Leadership: Lead AI integration initiatives
- Certification: Obtain AI-related certifications
- Portfolio Building: Document AI-enhanced achievements

LONG-TERM VISION (6-12 Months):
- Career Pivot: Transition to AI-augmented roles
- Leadership: Position yourself as an AI strategy expert
- Innovation: Drive AI adoption in your organization
- Mentorship: Help others navigate AI disruption

Your 90-Day Timeline:
Week 1-2: Complete AI skills assessment and create learning plan
Week 3-4: Start AI tool training and join professional communities
Month 2: Implement AI tools in current projects
Month 3: Lead AI initiatives and document achievements

Get your complete career strategy: https://mingusapp.com/career-strategy

Coming up next: Exclusive offer for our complete career intelligence report.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """

def get_welcome_5_html() -> str:
    """Exclusive Career Intelligence Offer Email Template"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Exclusive: Complete Career Intelligence Report</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .offer-box { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 30px; border-radius: 12px; margin: 30px 0; text-align: center; border: 2px solid #f59e0b; }
            .price { font-size: 36px; font-weight: bold; color: #d97706; margin: 10px 0; }
            .original-price { text-decoration: line-through; color: #666; font-size: 18px; }
            .cta-button { display: inline-block; padding: 20px 40px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; font-size: 18px; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
            .feature-list { background: white; padding: 25px; border-radius: 8px; margin: 20px 0; }
            .feature-item { display: flex; align-items: center; margin: 15px 0; }
            .feature-icon { width: 24px; height: 24px; background: #10b981; border-radius: 50%; margin-right: 15px; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; }
            .testimonial { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎁 Exclusive Offer: Complete Career Intelligence Report</h1>
                <p>{{first_name}}, unlock your full career potential with our comprehensive analysis</p>
            </div>
            
            <div class="content">
                <div class="offer-box">
                    <h2>🚨 LIMITED TIME OFFER</h2>
                    <div class="price">$97</div>
                    <div class="original-price">Regular Price: $297</div>
                    <p><strong>Save $200</strong> - Available for 48 hours only</p>
                    <a href="https://mingusapp.com/career-intelligence-offer" class="cta-button">Get Your Complete Report Now →</a>
                </div>
                
                <h2>What's Included in Your Career Intelligence Report:</h2>
                
                <div class="feature-list">
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Detailed AI Risk Analysis:</strong> Comprehensive breakdown of automation and augmentation potential</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Personalized Skill Gap Analysis:</strong> Identify exactly which skills you need to develop</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Industry-Specific Career Paths:</strong> 5 detailed career trajectories for {{industry}} professionals</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Salary Projections:</strong> Expected earnings with AI skills vs. without</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Learning Roadmap:</strong> Step-by-step plan to acquire essential AI skills</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Network Building Strategy:</strong> Connect with the right people in your industry</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Resume Optimization Guide:</strong> Highlight AI skills and achievements</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div><strong>Interview Preparation:</strong> Ace AI-related interview questions</div>
                    </div>
                </div>
                
                <div class="testimonial">
                    "The Career Intelligence Report was a game-changer. It showed me exactly what skills I needed and helped me land a 40% salary increase within 6 months." - Sarah M., Marketing Director
                </div>
                
                <h3>Why This Report is Essential for {{risk_level}} Risk Professionals:</h3>
                <ul>
                    <li><strong>Urgency:</strong> {{automation_score}}% automation risk requires immediate action</li>
                    <li><strong>Opportunity:</strong> {{augmentation_score}}% augmentation potential means significant upside</li>
                    <li><strong>Competition:</strong> Others in {{industry}} are already adapting</li>
                    <li><strong>Investment:</strong> $97 today could mean $50K+ in additional earnings</li>
                </ul>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/career-intelligence-offer" class="cta-button">Get Your Complete Report Now →</a>
                    <p style="font-size: 14px; color: #666; margin-top: 10px;">48-hour limited offer • 30-day money-back guarantee</p>
                </div>
                
                <p><strong>P.S.</strong> This offer expires in 48 hours. Don't let AI disruption catch you unprepared.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_5_text() -> str:
    return """
Exclusive: Complete Career Intelligence Report for {{first_name}}

Hi {{first_name}},

🚨 LIMITED TIME OFFER - 48 HOURS ONLY

Get your complete Career Intelligence Report for just $97 (Regular Price: $297)
Save $200 - Available for 48 hours only

What's Included:
✓ Detailed AI Risk Analysis: Comprehensive breakdown of automation and augmentation potential
✓ Personalized Skill Gap Analysis: Identify exactly which skills you need to develop
✓ Industry-Specific Career Paths: 5 detailed career trajectories for {{industry}} professionals
✓ Salary Projections: Expected earnings with AI skills vs. without
✓ Learning Roadmap: Step-by-step plan to acquire essential AI skills
✓ Network Building Strategy: Connect with the right people in your industry
✓ Resume Optimization Guide: Highlight AI skills and achievements
✓ Interview Preparation: Ace AI-related interview questions

Testimonial:
"The Career Intelligence Report was a game-changer. It showed me exactly what skills I needed and helped me land a 40% salary increase within 6 months." - Sarah M., Marketing Director

Why This Report is Essential for {{risk_level}} Risk Professionals:
- Urgency: {{automation_score}}% automation risk requires immediate action
- Opportunity: {{augmentation_score}}% augmentation potential means significant upside
- Competition: Others in {{industry}} are already adapting
- Investment: $97 today could mean $50K+ in additional earnings

Get your complete report: https://mingusapp.com/career-intelligence-offer

48-hour limited offer • 30-day money-back guarantee

P.S. This offer expires in 48 hours. Don't let AI disruption catch you unprepared.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """

# Risk Level Specific Templates
def get_high_risk_urgent_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚨 {{first_name}}, Your Career Needs Immediate Attention</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .urgent-box { background: #fef2f2; border: 2px solid #ef4444; padding: 25px; border-radius: 8px; margin: 25px 0; }
            .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
            .action-list { background: white; padding: 25px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 {{first_name}}, Your Career Needs Immediate Attention</h1>
                <p>Your {{automation_score}}% automation risk requires urgent action</p>
            </div>
            
            <div class="content">
                <div class="urgent-box">
                    <h2>⚠️ HIGH RISK ALERT</h2>
                    <p>Your role as a <strong>{{job_title}}</strong> in <strong>{{industry}}</strong> has a <strong>{{automation_score}}% automation risk</strong>. This means AI could significantly impact your job within the next 2-3 years.</p>
                </div>
                
                <h2>Why This Requires Immediate Action:</h2>
                <ul>
                    <li><strong>Timeline:</strong> AI disruption in {{industry}} is accelerating</li>
                    <li><strong>Competition:</strong> Others are already adapting their skills</li>
                    <li><strong>Market Shift:</strong> Companies are prioritizing AI-savvy professionals</li>
                    <li><strong>Career Risk:</strong> Delaying action could limit your options</li>
                </ul>
                
                <div class="action-list">
                    <h3>Your 30-Day Emergency Action Plan:</h3>
                    <ol>
                        <li><strong>Week 1:</strong> Complete AI skills assessment and identify transferable skills</li>
                        <li><strong>Week 2:</strong> Start intensive AI tool training for your industry</li>
                        <li><strong>Week 3:</strong> Network with AI professionals and explore new roles</li>
                        <li><strong>Week 4:</strong> Apply for AI-augmented positions and update resume</li>
                    </ol>
                </div>
                
                <h3>Immediate Next Steps:</h3>
                <ul>
                    <li>Download our "High-Risk Career Transition Guide"</li>
                    <li>Join our "AI Career Emergency" support group</li>
                    <li>Schedule a free career consultation</li>
                    <li>Start your AI skills certification program</li>
                </ul>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/high-risk-action-plan" class="cta-button">Get Your Emergency Action Plan →</a>
                </div>
                
                <p><strong>Remember:</strong> High risk doesn't mean no opportunity. Many professionals have successfully transitioned to higher-paying, AI-augmented roles.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_high_risk_urgent_text() -> str:
    return """
🚨 {{first_name}}, Your Career Needs Immediate Attention

Hi {{first_name}},

⚠️ HIGH RISK ALERT

Your role as a {{job_title}} in {{industry}} has a {{automation_score}}% automation risk. This means AI could significantly impact your job within the next 2-3 years.

Why This Requires Immediate Action:
- Timeline: AI disruption in {{industry}} is accelerating
- Competition: Others are already adapting their skills
- Market Shift: Companies are prioritizing AI-savvy professionals
- Career Risk: Delaying action could limit your options

Your 30-Day Emergency Action Plan:
Week 1: Complete AI skills assessment and identify transferable skills
Week 2: Start intensive AI tool training for your industry
Week 3: Network with AI professionals and explore new roles
Week 4: Apply for AI-augmented positions and update resume

Immediate Next Steps:
- Download our "High-Risk Career Transition Guide"
- Join our "AI Career Emergency" support group
- Schedule a free career consultation
- Start your AI skills certification program

Get your emergency action plan: https://mingusapp.com/high-risk-action-plan

Remember: High risk doesn't mean no opportunity. Many professionals have successfully transitioned to higher-paying, AI-augmented roles.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """

# Industry-Specific Templates
def get_tech_ai_coding_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{first_name}}, AI Coding Tools That Will Transform Your Work</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .tool-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💻 AI Coding Tools That Will Transform Your Work</h1>
                <p>{{first_name}}, discover the AI tools revolutionizing software development</p>
            </div>
            
            <div class="content">
                <h2>Essential AI Tools for {{job_title}}</h2>
                <p>Based on your {{automation_score}}% automation risk, here are the AI coding tools you need to master:</p>
                
                <div class="tool-card">
                    <h3>🤖 GitHub Copilot</h3>
                    <p><strong>Best for:</strong> Code completion, documentation, testing</p>
                    <p><strong>Productivity boost:</strong> 30-50% faster coding</p>
                    <p><strong>Learning curve:</strong> 1-2 weeks to master</p>
                </div>
                
                <div class="tool-card">
                    <h3>🔧 Claude for Code</h3>
                    <p><strong>Best for:</strong> Code review, debugging, architecture</p>
                    <p><strong>Productivity boost:</strong> 40-60% faster problem-solving</p>
                    <p><strong>Learning curve:</strong> 2-3 weeks to master</p>
                </div>
                
                <div class="tool-card">
                    <h3>⚡ Cursor IDE</h3>
                    <p><strong>Best for:</strong> Full-stack development, refactoring</p>
                    <p><strong>Productivity boost:</strong> 50-70% faster development</p>
                    <p><strong>Learning curve:</strong> 1 week to master</p>
                </div>
                
                <h3>Your AI Coding Learning Path:</h3>
                <ol>
                    <li><strong>Week 1:</strong> Master GitHub Copilot basics and prompts</li>
                    <li><strong>Week 2:</strong> Learn Claude for code review and debugging</li>
                    <li><strong>Week 3:</strong> Explore Cursor IDE for full-stack development</li>
                    <li><strong>Week 4:</strong> Integrate all tools into your workflow</li>
                </ol>
                
                <h3>Career Opportunities with AI Coding Skills:</h3>
                <ul>
                    <li><strong>AI-Augmented Developer:</strong> 25-40% salary increase</li>
                    <li><strong>AI Integration Specialist:</strong> New high-demand role</li>
                    <li><strong>Technical Lead:</strong> Lead AI adoption in teams</li>
                    <li><strong>AI Product Manager:</strong> Bridge technical and business needs</li>
                </ul>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/ai-coding-tools" class="cta-button">Get Your AI Coding Toolkit →</a>
                </div>
                
                <p><strong>Coming up next:</strong> Success stories from developers who've mastered AI coding tools.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_tech_ai_coding_text() -> str:
    return """
{{first_name}}, AI Coding Tools That Will Transform Your Work

Hi {{first_name}},

Discover the AI tools revolutionizing software development:

Essential AI Tools for {{job_title}}:

🤖 GitHub Copilot
Best for: Code completion, documentation, testing
Productivity boost: 30-50% faster coding
Learning curve: 1-2 weeks to master

🔧 Claude for Code
Best for: Code review, debugging, architecture
Productivity boost: 40-60% faster problem-solving
Learning curve: 2-3 weeks to master

⚡ Cursor IDE
Best for: Full-stack development, refactoring
Productivity boost: 50-70% faster development
Learning curve: 1 week to master

Your AI Coding Learning Path:
Week 1: Master GitHub Copilot basics and prompts
Week 2: Learn Claude for code review and debugging
Week 3: Explore Cursor IDE for full-stack development
Week 4: Integrate all tools into your workflow

Career Opportunities with AI Coding Skills:
- AI-Augmented Developer: 25-40% salary increase
- AI Integration Specialist: New high-demand role
- Technical Lead: Lead AI adoption in teams
- AI Product Manager: Bridge technical and business needs

Get your AI coding toolkit: https://mingusapp.com/ai-coding-tools

Coming up next: Success stories from developers who've mastered AI coding tools.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """

# Behavioral Trigger Templates
def get_incomplete_assessment_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{first_name}}, Complete Your AI Risk Assessment</title>
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
            .header { background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 40px 30px; text-align: center; }
            .content { padding: 40px 30px; background: #f9f9f9; }
            .reminder-box { background: #fff3cd; border: 2px solid #ffc107; padding: 25px; border-radius: 8px; margin: 25px 0; }
            .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
            .footer { background: #333; color: white; padding: 30px; text-align: center; }
            .footer a { color: #10b981; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏰ Don't Miss Out on Your AI Risk Assessment</h1>
                <p>{{first_name}}, complete your assessment in just 2 minutes</p>
            </div>
            
            <div class="content">
                <div class="reminder-box">
                    <h2>📋 Your Assessment is Waiting</h2>
                    <p>You started your {{assessment_type}} but haven't completed it yet. Don't miss out on your personalized AI risk analysis!</p>
                </div>
                
                <h2>What You'll Get When You Complete It:</h2>
                <ul>
                    <li><strong>Personalized Risk Score:</strong> Your exact automation and augmentation potential</li>
                    <li><strong>Industry-Specific Insights:</strong> How AI affects your specific role</li>
                    <li><strong>Action Plan:</strong> Step-by-step career protection strategy</li>
                    <li><strong>Resource Recommendations:</strong> Tools and courses tailored to your needs</li>
                </ul>
                
                <h3>Why Complete It Now:</h3>
                <ul>
                    <li>AI disruption is accelerating in all industries</li>
                    <li>Early adopters are already gaining competitive advantages</li>
                    <li>Your personalized insights could save you months of research</li>
                    <li>It only takes 2 minutes to complete</li>
                </ul>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="https://mingusapp.com/complete-assessment" class="cta-button">Complete Your Assessment Now →</a>
                </div>
                
                <p><strong>P.S.</strong> Over 12,000 professionals have already completed their assessments and received personalized career protection plans.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 MINGUS Financial Wellness. All rights reserved.</p>
                <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def get_incomplete_assessment_text() -> str:
    return """
{{first_name}}, Complete Your AI Risk Assessment

Hi {{first_name}},

📋 Your Assessment is Waiting

You started your {{assessment_type}} but haven't completed it yet. Don't miss out on your personalized AI risk analysis!

What You'll Get When You Complete It:
- Personalized Risk Score: Your exact automation and augmentation potential
- Industry-Specific Insights: How AI affects your specific role
- Action Plan: Step-by-step career protection strategy
- Resource Recommendations: Tools and courses tailored to your needs

Why Complete It Now:
- AI disruption is accelerating in all industries
- Early adopters are already gaining competitive advantages
- Your personalized insights could save you months of research
- It only takes 2 minutes to complete

Complete your assessment: https://mingusapp.com/complete-assessment

P.S. Over 12,000 professionals have already completed their assessments and received personalized career protection plans.

Best regards,
The MINGUS Team

© 2024 MINGUS Financial Wellness
    """
