import { Database } from '../types/database'

type Lead = Database['public']['Tables']['leads']['Row']

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  body: string
  template_type: string
  segment: string | null
  variables: string[]
}

// Email Template Collection
export const EMAIL_TEMPLATES: EmailTemplate[] = [
  // 1. Immediate Results Delivery
  {
    id: 'results-immediate',
    name: 'Your Financial Assessment Results',
    subject: '🎯 Your Financial Profile: {{segment}} - Here\'s Your Action Plan',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Financial Assessment Results</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .score-circle { width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; margin: 20px auto; }
        .segment-badge { display: inline-block; padding: 8px 16px; background: #667eea; color: white; border-radius: 20px; font-weight: bold; text-transform: uppercase; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .highlight { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Your Financial Assessment Results</h1>
            <p>Hi {{name}}, here's your personalized financial profile analysis</p>
        </div>
        
        <div class="content">
            <div style="text-align: center;">
                <div class="score-circle">{{score}}/100</div>
                <div class="segment-badge">{{segment}}</div>
            </div>
            
            <h2>Your Financial Profile: {{segment}}</h2>
            
            <div class="highlight">
                <strong>Key Insight:</strong> Based on your responses, you're in the <strong>{{segment}}</strong> category. 
                This means you're ready for our <strong>{{product_tier}}</strong> solution.
            </div>
            
            <h3>What This Means For You:</h3>
            <ul>
                <li><strong>Your Current State:</strong> {{getSegmentDescription}}</li>
                <li><strong>Recommended Solution:</strong> {{product_tier}}</li>
                <li><strong>Expected Timeline:</strong> {{getTimeline}}</li>
            </ul>
            
            <h3>Your Next Steps:</h3>
            <ol>
                <li><strong>Review Your Personalized Plan</strong> - We've created a custom roadmap just for you</li>
                <li><strong>Join Our Beta Program</strong> - Get early access to our {{product_tier}} solution</li>
                <li><strong>Schedule a Free Consultation</strong> - Let's discuss your specific needs</li>
            </ol>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{getCtaLink}}" class="cta-button">Get Your Personalized Plan →</a>
            </div>
            
            <p><strong>P.S.</strong> You're among the first to access our new financial assessment system. 
            We're offering exclusive early-bird pricing for our beta users.</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'assessment_results',
    segment: null,
    variables: ['name', 'segment', 'score', 'product_tier', 'getSegmentDescription', 'getTimeline', 'getCtaLink', 'unsubscribeLink', 'preferencesLink']
  },

  // 2. Welcome Sequence - Email 1
  {
    id: 'welcome-1',
    name: 'Welcome to Ratchet Money',
    subject: 'Welcome to Ratchet Money, {{name}}! 🚀',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Ratchet Money</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Welcome to Ratchet Money!</h1>
            <p>You're about to transform your financial life</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>Welcome to the Ratchet Money family! We're excited to have you on board.</p>
            
            <p>You've just joined thousands of people who are taking control of their financial future with our proven strategies.</p>
            
            <h3>What You Can Expect:</h3>
            <ul>
                <li><strong>Daily Tips:</strong> Actionable financial advice delivered to your inbox</li>
                <li><strong>Exclusive Content:</strong> Strategies that aren't shared anywhere else</li>
                <li><strong>Community Access:</strong> Connect with like-minded money enthusiasts</li>
                <li><strong>Early Access:</strong> Be the first to know about new products and services</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{assessmentLink}}" class="cta-button">Take Your Financial Assessment →</a>
            </div>
            
            <p><strong>Coming up next:</strong> Tomorrow, you'll receive our "5-Minute Money Audit" - a quick exercise that will reveal exactly where your money is going and how to optimize it.</p>
            
            <p>Stay tuned!</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'welcome',
    segment: null,
    variables: ['name', 'assessmentLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Welcome Sequence - Email 2
  {
    id: 'welcome-2',
    name: '5-Minute Money Audit',
    subject: '🔍 Your 5-Minute Money Audit (Action Required)',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>5-Minute Money Audit</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .highlight { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 5-Minute Money Audit</h1>
            <p>Discover exactly where your money is going</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>Ready to see exactly where your money is going? This 5-minute audit will reveal insights that could save you hundreds (or thousands) every month.</p>
            
            <div class="highlight">
                <strong>Quick Fact:</strong> Most people are surprised to learn they're spending 30% more on non-essentials than they think.
            </div>
            
            <h3>What You'll Discover:</h3>
            <ul>
                <li>Your biggest money leaks (and how to plug them)</li>
                <li>Hidden expenses you didn't know about</li>
                <li>Opportunities to save without sacrifice</li>
                <li>Your personal spending personality</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{auditLink}}" class="cta-button">Start Your Money Audit →</a>
            </div>
            
            <p><strong>Time Investment:</strong> Just 5 minutes<br>
            <strong>Potential Savings:</strong> $200-500+ per month</p>
            
            <p>This audit is completely free and will give you a personalized action plan based on your spending patterns.</p>
            
            <p>Let's find your money leaks!</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'welcome',
    segment: null,
    variables: ['name', 'auditLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Welcome Sequence - Email 3
  {
    id: 'welcome-3',
    name: 'Your Money Personality Revealed',
    subject: '🎭 {{name}}, Your Money Personality is {{segment}}',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Money Personality</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .personality-box { background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2196f3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Your Money Personality</h1>
            <p>Understanding your financial DNA</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>Based on your assessment, you're a <strong>{{segment}}</strong>! This is your financial personality type.</p>
            
            <div class="personality-box">
                <h3>What Being a {{segment}} Means:</h3>
                <p>{{getPersonalityDescription}}</p>
            </div>
            
            <h3>Your Strengths:</h3>
            <ul>
                {{getStrengthsList}}
            </ul>
            
            <h3>Areas for Growth:</h3>
                {{getGrowthAreas}}
            
            <h3>Your Perfect Strategy:</h3>
            <p>{{getStrategyDescription}}</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{strategyLink}}" class="cta-button">Get Your Personalized Strategy →</a>
            </div>
            
            <p><strong>Coming tomorrow:</strong> We'll show you exactly how other {{segment}}s have transformed their financial lives using our proven methods.</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'welcome',
    segment: null,
    variables: ['name', 'segment', 'getPersonalityDescription', 'getStrengthsList', 'getGrowthAreas', 'getStrategyDescription', 'strategyLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Welcome Sequence - Email 4
  {
    id: 'welcome-4',
    name: 'Success Stories from Your Segment',
    subject: '💪 How Other {{segment}}s Are Winning (Real Results)',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success Stories</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .testimonial { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💪 Success Stories</h1>
            <p>Real results from people just like you</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>You're not alone in your financial journey. Here are real stories from other {{segment}}s who've transformed their financial lives:</p>
            
            <div class="testimonial">
                <h4>Sarah M. - {{segment}}</h4>
                <p>"I was struggling with {{getCommonChallenge}}. After implementing the {{segment}} strategy, I saved $3,200 in just 6 months!"</p>
                <strong>Results:</strong> $3,200 saved, debt-free in 18 months
            </div>
            
            <div class="testimonial">
                <h4>Mike R. - {{segment}}</h4>
                <p>"The personalized approach for {{segment}}s was exactly what I needed. I went from living paycheck to paycheck to having a 6-month emergency fund."</p>
                <strong>Results:</strong> 6-month emergency fund, 15% raise at work
            </div>
            
            <div class="testimonial">
                <h4>Lisa T. - {{segment}}</h4>
                <p>"As a {{segment}}, I thought I'd never get my finances under control. Now I'm on track to retire 10 years early!"</p>
                <strong>Results:</strong> $45,000 invested, early retirement plan
            </div>
            
            <h3>Your Turn to Win:</h3>
            <p>These people started exactly where you are. They used our {{segment}}-specific strategies and got incredible results.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{joinLink}}" class="cta-button">Join the Success Stories →</a>
            </div>
            
            <p><strong>Tomorrow:</strong> We'll show you the exact step-by-step process to achieve similar results.</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'welcome',
    segment: null,
    variables: ['name', 'segment', 'getCommonChallenge', 'joinLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Welcome Sequence - Email 5
  {
    id: 'welcome-5',
    name: 'Your Action Plan & Next Steps',
    subject: '🎯 {{name}}, Here\'s Your 30-Day Action Plan',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your 30-Day Action Plan</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .action-step { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Your 30-Day Action Plan</h1>
            <p>Transform your finances, one step at a time</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>Congratulations! You've completed your financial assessment and discovered your money personality. Now it's time to take action.</p>
            
            <h3>Your 30-Day {{segment}} Action Plan:</h3>
            
            <div class="action-step">
                <strong>Week 1: Foundation (Days 1-7)</strong><br>
                {{getWeek1Actions}}
            </div>
            
            <div class="action-step">
                <strong>Week 2: Implementation (Days 8-14)</strong><br>
                {{getWeek2Actions}}
            </div>
            
            <div class="action-step">
                <strong>Week 3: Optimization (Days 15-21)</strong><br>
                {{getWeek3Actions}}
            </div>
            
            <div class="action-step">
                <strong>Week 4: Scaling (Days 22-30)</strong><br>
                {{getWeek4Actions}}
            </div>
            
            <h3>Expected Results:</h3>
            <ul>
                <li><strong>Week 1:</strong> {{getWeek1Results}}</li>
                <li><strong>Week 2:</strong> {{getWeek2Results}}</li>
                <li><strong>Week 3:</strong> {{getWeek3Results}}</li>
                <li><strong>Week 4:</strong> {{getWeek4Results}}</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{actionPlanLink}}" class="cta-button">Get Your Complete Action Plan →</a>
            </div>
            
            <p><strong>What's Next:</strong> You'll receive weekly check-ins to track your progress and get personalized guidance based on your results.</p>
            
            <p>Ready to transform your financial life?</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'welcome',
    segment: null,
    variables: ['name', 'segment', 'getWeek1Actions', 'getWeek2Actions', 'getWeek3Actions', 'getWeek4Actions', 'getWeek1Results', 'getWeek2Results', 'getWeek3Results', 'getWeek4Results', 'actionPlanLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Segment-specific templates
  {
    id: 'segment-stress-free',
    name: 'Stress-Free Financial Freedom',
    subject: '🌿 {{name}}, Your Stress-Free Money Strategy',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stress-Free Financial Strategy</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌿 Stress-Free Financial Freedom</h1>
            <p>Simple strategies for lasting peace of mind</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>As a Stress-Free money personality, you value simplicity and peace of mind. Here's your personalized strategy:</p>
            
            <h3>Your Stress-Free Approach:</h3>
            <ul>
                <li><strong>Automation First:</strong> Set up automatic savings and bill payments</li>
                <li><strong>Simple Budgeting:</strong> Use the 50/30/20 rule for effortless money management</li>
                <li><strong>Emergency Fund:</strong> Build 3-6 months of expenses for peace of mind</li>
                <li><strong>Low-Maintenance Investing:</strong> Index funds and target-date funds</li>
            </ul>
            
            <h3>Your Perfect Solution:</h3>
            <p>Our <strong>Budget ($10)</strong> plan is designed specifically for Stress-Free personalities like you. It includes:</p>
            <ul>
                <li>Automated budget tracking</li>
                <li>Simple goal setting</li>
                <li>Peace-of-mind emergency fund builder</li>
                <li>Stress-free investment guidance</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{budgetPlanLink}}" class="cta-button">Start Your Stress-Free Journey →</a>
            </div>
            
            <p><strong>Remember:</strong> Financial freedom doesn't have to be complicated. Sometimes the simplest approach is the most effective.</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'segment_specific',
    segment: 'stress-free',
    variables: ['name', 'budgetPlanLink', 'unsubscribeLink', 'preferencesLink']
  },

  // Product Launch Notification
  {
    id: 'product-launch',
    name: 'New Product Launch - Exclusive Access',
    subject: '🚀 {{name}}, You\'re Invited: New {{product_tier}} Launch',
    body: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Product Launch</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .cta-button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }
        .launch-badge { background: #ff6b6b; color: white; padding: 5px 15px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 New Product Launch</h1>
            <p>Exclusive early access for {{segment}}s</p>
        </div>
        
        <div class="content">
            <h2>Hi {{name}},</h2>
            
            <p>We're excited to announce the launch of our new <strong>{{product_tier}}</strong> solution, designed specifically for {{segment}}s like you!</p>
            
            <div style="text-align: center; margin: 20px 0;">
                <span class="launch-badge">LAUNCHING TODAY</span>
            </div>
            
            <h3>What's New in {{product_tier}}:</h3>
            <ul>
                <li><strong>Advanced Analytics:</strong> Deep insights into your spending patterns</li>
                <li><strong>AI-Powered Recommendations:</strong> Personalized financial advice</li>
                <li><strong>Goal Tracking:</strong> Visual progress toward your financial goals</li>
                <li><strong>Community Access:</strong> Connect with other {{segment}}s</li>
                <li><strong>Priority Support:</strong> Direct access to our financial experts</li>
            </ul>
            
            <h3>Exclusive Launch Offer:</h3>
            <ul>
                <li><strong>50% Off:</strong> First 3 months at half price</li>
                <li><strong>Free Consultation:</strong> 30-minute session with a financial advisor</li>
                <li><strong>Bonus Content:</strong> Exclusive {{segment}}-specific resources</li>
                <li><strong>Lifetime Access:</strong> Early adopter benefits</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{launchLink}}" class="cta-button">Get Early Access Now →</a>
            </div>
            
            <p><strong>Limited Time:</strong> This offer expires in 48 hours. Don't miss out on these exclusive benefits!</p>
            
            <p><strong>P.S.</strong> As a {{segment}}, you're among the first to know about this launch. Share this with friends who might benefit from our {{product_tier}} solution.</p>
            
            <p>Best regards,<br>The Ratchet Money Team</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p><a href="{{unsubscribeLink}}" style="color: #ccc;">Unsubscribe</a> | <a href="{{preferencesLink}}" style="color: #ccc;">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>
    `,
    template_type: 'product_launch',
    segment: null,
    variables: ['name', 'segment', 'product_tier', 'launchLink', 'unsubscribeLink', 'preferencesLink']
  }
]

// Template helper functions
export function getSegmentDescription(segment: string): string {
  const descriptions = {
    'stress-free': 'You prefer simple, automated financial solutions that require minimal effort and provide peace of mind.',
    'relationship-spender': 'You often make financial decisions based on relationships and social factors, sometimes prioritizing others over your own financial goals.',
    'emotional-manager': 'You tend to make financial decisions based on emotions and current feelings, which can lead to impulsive spending or saving.',
    'crisis-mode': 'You\'re currently in a financial emergency or high-stress situation that requires immediate attention and aggressive action.'
  }
  return descriptions[segment as keyof typeof descriptions] || descriptions['stress-free']
}

export function getPersonalityDescription(segment: string): string {
  const descriptions = {
    'stress-free': 'You naturally gravitate toward simplicity and automation. You prefer set-it-and-forget-it solutions that don\'t require constant attention.',
    'relationship-spender': 'You\'re generous and caring, often putting others\' needs before your own financial security. You find meaning in spending on experiences and gifts.',
    'emotional-manager': 'You\'re highly intuitive and make decisions based on your current emotional state. You can be very disciplined when motivated but may struggle with consistency.',
    'crisis-mode': 'You\'re in a situation that requires immediate, focused action. You\'re ready to make significant changes to improve your financial situation.'
  }
  return descriptions[segment as keyof typeof descriptions] || descriptions['stress-free']
}

export function getStrengthsList(segment: string): string {
  const strengths = {
    'stress-free': '<li>Natural preference for simplicity</li><li>Good at setting up systems</li><li>Consistent with automated processes</li><li>Values peace of mind</li>',
    'relationship-spender': '<li>Generous and caring nature</li><li>Good at building relationships</li><li>Values experiences over things</li><li>Motivated by helping others</li>',
    'emotional-manager': '<li>Highly intuitive decision-making</li><li>Can be very focused when motivated</li><li>Good at reading situations</li><li>Adaptable to changing circumstances</li>',
    'crisis-mode': '<li>Ready for immediate action</li><li>Highly motivated to change</li><li>Can handle intense focus</li><li>Willing to make sacrifices</li>'
  }
  return strengths[segment as keyof typeof strengths] || strengths['stress-free']
}

export function getGrowthAreas(segment: string): string {
  const areas = {
    'stress-free': '<li>Setting boundaries with spending</li><li>Taking calculated risks</li><li>Engaging more actively with finances</li>',
    'relationship-spender': '<li>Setting financial boundaries</li><li>Prioritizing your own financial security</li><li>Learning to say no to spending requests</li>',
    'emotional-manager': '<li>Creating consistent habits</li><li>Making decisions based on logic vs emotion</li><li>Building long-term discipline</li>',
    'crisis-mode': '<li>Building sustainable habits</li><li>Planning for long-term stability</li><li>Managing stress and emotions</li>'
  }
  return areas[segment as keyof typeof areas] || areas['stress-free']
}

export function getStrategyDescription(segment: string): string {
  const strategies = {
    'stress-free': 'Focus on automation and simplicity. Set up automatic savings, use simple budgeting tools, and create systems that require minimal ongoing effort.',
    'relationship-spender': 'Learn to set healthy financial boundaries while still being generous. Create separate accounts for giving and personal finances.',
    'emotional-manager': 'Build systems that work regardless of your emotional state. Use automation for consistency and create clear decision-making frameworks.',
    'crisis-mode': 'Focus on immediate action and debt reduction. Create a strict budget, cut unnecessary expenses, and build emergency savings quickly.'
  }
  return strategies[segment as keyof typeof strategies] || strategies['stress-free']
}

export function getCommonChallenge(segment: string): string {
  const challenges = {
    'stress-free': 'overspending on convenience and comfort',
    'relationship-spender': 'spending too much on others and relationships',
    'emotional-manager': 'inconsistent saving and spending habits',
    'crisis-mode': 'managing debt and building emergency savings'
  }
  return challenges[segment as keyof typeof challenges] || challenges['stress-free']
}

// Week-by-week action plans
export function getWeekActions(segment: string, week: number): string {
  const actionPlans = {
    'stress-free': {
      1: 'Set up automatic savings, create simple budget categories, establish emergency fund goal',
      2: 'Automate bill payments, set up spending alerts, create financial goals',
      3: 'Review and optimize automatic systems, increase savings rate, plan for future expenses',
      4: 'Scale up investments, create long-term financial plan, set up retirement accounts'
    },
    'relationship-spender': {
      1: 'Create separate accounts for personal and relationship spending, set spending limits',
      2: 'Practice saying no to non-essential spending requests, track relationship expenses',
      3: 'Build personal emergency fund, create boundaries around gift-giving',
      4: 'Develop sustainable giving strategy, increase personal savings, plan for future'
    },
    'emotional-manager': {
      1: 'Set up automatic savings and bill payments, create decision-making frameworks',
      2: 'Build consistent daily money habits, track spending without judgment',
      3: 'Create emotional spending triggers list, develop coping strategies',
      4: 'Establish long-term financial goals, build sustainable money management systems'
    },
    'crisis-mode': {
      1: 'Create strict budget, cut all non-essential expenses, contact creditors',
      2: 'Build emergency fund, negotiate payment plans, find additional income sources',
      3: 'Consolidate debt, refinance high-interest loans, build credit score',
      4: 'Create long-term financial plan, establish sustainable spending habits'
    }
  }
  
  const plan = actionPlans[segment as keyof typeof actionPlans]
  return plan ? plan[week as keyof typeof plan] : actionPlans['stress-free'][week as keyof typeof actionPlans['stress-free']]
}

export function getWeekResults(segment: string, week: number): string {
  const results = {
    'stress-free': {
      1: 'Automated systems in place, clear financial picture',
      2: 'Reduced financial stress, consistent bill payments',
      3: 'Increased savings, optimized spending patterns',
      4: 'Long-term financial plan established, investments growing'
    },
    'relationship-spender': {
      1: 'Clear boundaries set, separate accounts established',
      2: 'Reduced relationship spending, personal savings growing',
      3: 'Emergency fund building, healthier spending balance',
      4: 'Sustainable giving strategy, strong personal finances'
    },
    'emotional-manager': {
      1: 'Consistent systems in place, reduced financial stress',
      2: 'Daily habits established, better spending awareness',
      3: 'Emotional triggers identified, coping strategies working',
      4: 'Long-term goals set, sustainable systems created'
    },
    'crisis-mode': {
      1: 'Immediate expenses under control, budget established',
      2: 'Emergency fund growing, payment plans negotiated',
      3: 'Debt consolidation in progress, credit improving',
      4: 'Financial stability achieved, long-term plan in place'
    }
  }
  
  const result = results[segment as keyof typeof results]
  return result ? result[week as keyof typeof result] : results['stress-free'][week as keyof typeof results['stress-free']]
} 