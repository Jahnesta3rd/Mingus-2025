#!/usr/bin/env python3
"""
Financial Alert Detection System Usage Examples for MINGUS

This file demonstrates how to use the financial alert detection system
and communication router for African American professionals.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.financial_alert_detector import FinancialAlertDetector
from services.communication_router import communication_router, UserProfile, UserEngagementLevel
from services.twilio_sms_service import twilio_sms_service
from models.financial_alerts import UserFinancialContext, CashFlowForecast, SpendingPattern
from database import get_db_session

def example_1_cash_flow_alert():
    """Example 1: Cash flow going negative in 7 days"""
    print("=== Example 1: Cash Flow Alert ===")
    
    # Create user financial context
    user_context = UserFinancialContext(
        user_id=str(uuid.uuid4()),
        primary_income_source='full_time',
        monthly_income=65000,
        income_frequency='bi_weekly',
        student_loan_payment=450.0,
        student_loan_due_date=15,
        family_obligations=200.0,
        rent_mortgage=1800.0,
        rent_mortgage_due_date=1,
        emergency_fund_balance=2500.0,
        emergency_fund_target=10000.0,
        regional_cost_of_living='atlanta',
        primary_financial_goal='home_ownership',
        optimal_engagement_time='evening'
    )
    
    # Create cash flow forecast showing negative balance in 5 days
    forecast = CashFlowForecast(
        user_id=user_context.user_id,
        forecast_date=datetime.utcnow() + timedelta(days=5),
        projected_balance=-500.0,
        confidence_level=0.85,
        projected_income=2500.0,
        projected_expenses=3000.0,
        risk_level='critical',
        days_until_negative=5,
        negative_balance_amount=500.0
    )
    
    print(f"User: {user_context.user_id}")
    print(f"Income: ${user_context.monthly_income:,.2f}/month")
    print(f"Projected balance in 5 days: ${forecast.projected_balance:,.2f}")
    print(f"Risk level: {forecast.risk_level}")
    print(f"Days until negative: {forecast.days_until_negative}")
    
    # This would trigger a CRITICAL SMS alert
    print("→ Would trigger: CRITICAL SMS alert")
    print("→ Message: '⚠️ MINGUS Alert: Your balance will go negative in 5 days. Current: $-500.00. Consider transferring funds.'")
    print()

def example_2_bill_payment_reminder():
    """Example 2: Bill payment reminder for student loan"""
    print("=== Example 2: Bill Payment Reminder ===")
    
    user_context = UserFinancialContext(
        user_id=str(uuid.uuid4()),
        primary_income_source='gig_work',
        monthly_income=45000,
        income_frequency='weekly',
        student_loan_payment=350.0,
        student_loan_due_date=15,
        family_obligations=150.0,
        regional_cost_of_living='houston',
        primary_financial_goal='student_loan_payoff',
        optimal_engagement_time='morning'
    )
    
    # Student loan due in 3 days
    due_date = datetime.utcnow() + timedelta(days=3)
    
    print(f"User: {user_context.user_id}")
    print(f"Income source: {user_context.primary_income_source}")
    print(f"Student loan payment: ${user_context.student_loan_payment:.2f}")
    print(f"Due in: 3 days")
    print(f"Regional cost of living: {user_context.regional_cost_of_living}")
    
    # This would trigger a HIGH priority SMS alert
    print("→ Would trigger: HIGH priority SMS alert")
    print("→ Message: '📅 MINGUS Reminder: Your Student Loan payment of $350.00 is due in 3 days. Consider income-driven repayment options if you're struggling with payments. Since you're paid weekly, you may want to set aside funds each week.'")
    print()

def example_3_unusual_spending_pattern():
    """Example 3: Unusual spending pattern detection"""
    print("=== Example 3: Unusual Spending Pattern ===")
    
    user_context = UserFinancialContext(
        user_id=str(uuid.uuid4()),
        primary_income_source='full_time',
        monthly_income=75000,
        income_frequency='monthly',
        regional_cost_of_living='dc_metro',
        primary_financial_goal='wealth_building',
        optimal_engagement_time='afternoon'
    )
    
    # Unusual spending pattern in dining category
    pattern = SpendingPattern(
        user_id=user_context.user_id,
        category='dining',
        pattern_type='weekly',
        average_amount=120.0,
        standard_deviation=25.0,
        frequency=2.5,
        is_anomaly=True,
        anomaly_score=0.85,
        anomaly_reason='Spending 85% above average in dining category'
    )
    
    print(f"User: {user_context.user_id}")
    print(f"Income: ${user_context.monthly_income:,.2f}/month")
    print(f"Category: {pattern.category}")
    print(f"Average spending: ${pattern.average_amount:.2f}/week")
    print(f"Anomaly score: {pattern.anomaly_score:.0%}")
    print(f"Reason: {pattern.anomaly_reason}")
    
    # This would trigger a MEDIUM priority email alert
    print("→ Would trigger: MEDIUM priority email alert")
    print("→ Subject: 'MINGUS Alert: Unusual Dining Spending'")
    print("→ Content: Detailed analysis with spending breakdown and recommendations")
    print()

def example_4_budget_exceeded():
    """Example 4: Budget exceeded by 20%+"""
    print("=== Example 4: Budget Exceeded ===")
    
    user_context = UserFinancialContext(
        user_id=str(uuid.uuid4()),
        primary_income_source='business',
        monthly_income=85000,
        income_frequency='monthly',
        regional_cost_of_living='new_york',
        primary_financial_goal='wealth_preservation',
        optimal_engagement_time='evening'
    )
    
    # Budget exceeded in transportation category
    budget = 400.0
    spent = 520.0  # 30% over budget
    overage_percentage = ((spent - budget) / budget) * 100
    
    print(f"User: {user_context.user_id}")
    print(f"Income: ${user_context.monthly_income:,.2f}/month")
    print(f"Category: Transportation")
    print(f"Budget: ${budget:.2f}")
    print(f"Spent: ${spent:.2f}")
    print(f"Overage: {overage_percentage:.0%}")
    
    # This would trigger both SMS and email alerts
    print("→ Would trigger: HIGH priority SMS + Email alerts")
    print("→ SMS: '💰 MINGUS Alert: Your Transportation spending is 30% over budget. Spent: $520.00, Budget: $400.00.'")
    print("→ Email: Detailed breakdown with spending analysis and recommendations")
    print()

def example_5_emergency_fund_alert():
    """Example 5: Emergency fund below 25% of target"""
    print("=== Example 5: Emergency Fund Alert ===")
    
    user_context = UserFinancialContext(
        user_id=str(uuid.uuid4()),
        primary_income_source='full_time',
        monthly_income=60000,
        income_frequency='bi_weekly',
        emergency_fund_balance=1500.0,
        emergency_fund_target=8000.0,
        regional_cost_of_living='atlanta',
        primary_financial_goal='emergency_fund',
        optimal_engagement_time='morning'
    )
    
    fund_percentage = (user_context.emergency_fund_balance / user_context.emergency_fund_target) * 100
    
    print(f"User: {user_context.user_id}")
    print(f"Income: ${user_context.monthly_income:,.2f}/month")
    print(f"Emergency fund balance: ${user_context.emergency_fund_balance:,.2f}")
    print(f"Emergency fund target: ${user_context.emergency_fund_target:,.2f}")
    print(f"Percentage of target: {fund_percentage:.0%}")
    
    # This would trigger a MEDIUM priority email alert
    print("→ Would trigger: MEDIUM priority email alert")
    print("→ Subject: 'MINGUS: Emergency Fund Alert'")
    print("→ Content: Detailed guidance on building emergency fund with cultural context")
    print()

def example_6_communication_routing():
    """Example 6: Communication routing based on user engagement"""
    print("=== Example 6: Communication Routing ===")
    
    # High engagement user
    high_engagement_user = UserProfile(
        user_id=str(uuid.uuid4()),
        email="high_engagement@example.com",
        phone_number="+1234567890",
        engagement_level=UserEngagementLevel.HIGH,
        income_range="80k-100k",
        age_range="25-35",
        cultural_preferences={
            'career_focus': 'career_advancement',
            'community_emphasis': True,
            'representation_matters': True
        },
        sms_opted_in=True,
        email_opted_in=True
    )
    
    # Low engagement user
    low_engagement_user = UserProfile(
        user_id=str(uuid.uuid4()),
        email="low_engagement@example.com",
        phone_number="+1234567891",
        engagement_level=UserEngagementLevel.LOW,
        income_range="40k-60k",
        age_range="25-35",
        cultural_preferences={
            'career_focus': 'career_advancement',
            'community_emphasis': True
        },
        sms_opted_in=True,
        email_opted_in=True
    )
    
    print("High Engagement User:")
    print(f"  - Income: {high_engagement_user.income_range}")
    print(f"  - Engagement: {high_engagement_user.engagement_level.value}")
    print(f"  - Routing preference: Email for detailed content")
    print(f"  - Cultural focus: Career advancement, community emphasis")
    
    print("\nLow Engagement User:")
    print(f"  - Income: {low_engagement_user.income_range}")
    print(f"  - Engagement: {low_engagement_user.engagement_level.value}")
    print(f"  - Routing preference: SMS for re-engagement")
    print(f"  - Cultural focus: Career advancement, community emphasis")
    print()

def example_7_cultural_personalization():
    """Example 7: Cultural personalization for African American professionals"""
    print("=== Example 7: Cultural Personalization ===")
    
    # Young professional in Atlanta
    atlanta_user = UserProfile(
        user_id=str(uuid.uuid4()),
        email="atlanta_professional@example.com",
        phone_number="+1234567892",
        engagement_level=UserEngagementLevel.MEDIUM,
        income_range="60k-80k",
        age_range="25-35",
        cultural_preferences={
            'career_focus': 'career_advancement',
            'financial_goals': ['home_ownership', 'student_loan_payoff', 'emergency_fund'],
            'communication_style': 'direct_and_supportive',
            'community_emphasis': True,
            'representation_matters': True
        },
        sms_opted_in=True,
        email_opted_in=True
    )
    
    print("Atlanta Professional (25-35, $60k-80k):")
    print(f"  - Age range: {atlanta_user.age_range}")
    print(f"  - Income range: {atlanta_user.income_range}")
    print(f"  - Financial goals: {atlanta_user.cultural_preferences['financial_goals']}")
    print(f"  - Communication style: {atlanta_user.cultural_preferences['communication_style']}")
    print(f"  - Community emphasis: {atlanta_user.cultural_preferences['community_emphasis']}")
    print(f"  - Representation matters: {atlanta_user.cultural_preferences['representation_matters']}")
    
    print("\nPersonalized messaging would include:")
    print("  - Community-focused language")
    print("  - Emphasis on building generational wealth")
    print("  - References to African American financial history")
    print("  - Support for career advancement goals")
    print("  - Recognition of family obligations")
    print()

def example_8_smart_timing():
    """Example 8: Smart timing for message delivery"""
    print("=== Example 8: Smart Timing ===")
    
    print("Critical Alerts (Cash flow negative):")
    print("  - Timing: Immediate")
    print("  - Channel: SMS")
    print("  - Example: '⚠️ MINGUS Alert: Your balance will go negative in 3 days.'")
    
    print("\nBill Reminders:")
    print("  - Timing: 2-3 days before due date")
    print("  - Channel: SMS")
    print("  - Example: '📅 MINGUS Reminder: Your rent payment of $1,800 is due in 2 days.'")
    
    print("\nCheck-ins:")
    print("  - Timing: User's optimal engagement time")
    print("  - Channel: SMS for low engagement, Email for high engagement")
    print("  - Example: '💡 MINGUS Weekly Check-in: How's your financial wellness journey?'")
    
    print("\nReports:")
    print("  - Timing: First Sunday of each month")
    print("  - Channel: Email")
    print("  - Example: '📊 Your MINGUS Monthly Financial Report'")
    print()

def run_all_examples():
    """Run all examples"""
    print("MINGUS Financial Alert Detection System Examples")
    print("=" * 50)
    print()
    
    example_1_cash_flow_alert()
    example_2_bill_payment_reminder()
    example_3_unusual_spending_pattern()
    example_4_budget_exceeded()
    example_5_emergency_fund_alert()
    example_6_communication_routing()
    example_7_cultural_personalization()
    example_8_smart_timing()
    
    print("=" * 50)
    print("All examples completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Cash flow monitoring and negative balance alerts")
    print("✅ Bill payment reminders with cultural context")
    print("✅ Unusual spending pattern detection")
    print("✅ Budget exceeded alerts")
    print("✅ Emergency fund monitoring")
    print("✅ Intelligent communication routing")
    print("✅ Cultural personalization for African American professionals")
    print("✅ Smart timing for message delivery")
    print("✅ SMS and Email integration with fallback logic")

if __name__ == "__main__":
    run_all_examples() 