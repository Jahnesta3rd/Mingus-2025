#!/usr/bin/env python3
"""
Financial Profile Testing Script for Mingus Personal Finance Application
Tests complete financial profiles for all three personas with detailed analysis
"""

import json
import time
from datetime import datetime
import math

# Complete financial profiles for the three personas
FINANCIAL_PERSONAS = {
    "maya_johnson": {
        "name": "Maya Johnson",
        "tier": "Budget ($15/month)",
        "location": "Decatur, GA",
        "monthly_income": 2800,
        "monthly_expenses": {
            "rent": 1100,
            "car_payment": 320,
            "car_insurance": 140,
            "gas": 120,
            "groceries": 300,
            "utilities": 85,
            "phone": 75,
            "student_loans": 285,
            "credit_cards": 95,
            "entertainment": 150,
            "dining_out": 200,
            "gym": 35,
            "streaming": 45
        },
        "debts": {
            "student_loans": 28000,
            "credit_cards": 3200
        },
        "assets": {
            "emergency_fund": 800,
            "credit_score": 680
        }
    },
    "marcus_thompson": {
        "name": "Marcus Thompson",
        "tier": "Mid-tier ($35/month)",
        "location": "Spring, TX",
        "monthly_income": 4200,
        "monthly_expenses": {
            "rent": 700,
            "car_payment": 485,
            "car_insurance": 160,
            "gas": 140,
            "groceries": 400,
            "utilities": 60,
            "phone": 85,
            "student_loans": 365,
            "credit_cards": 120,
            "entertainment": 250,
            "dining_out": 300,
            "gym": 45,
            "streaming_software": 75,
            "401k_contribution": 290
        },
        "debts": {
            "student_loans": 35000,
            "credit_cards": 1800
        },
        "assets": {
            "emergency_fund": 3500,
            "401k_balance": 8500,
            "credit_score": 720
        }
    },
    "dr_jasmine_williams": {
        "name": "Dr. Jasmine Williams",
        "tier": "Professional ($100/month)",
        "location": "Alexandria, VA",
        "monthly_income": 5200,
        "spouse_income": 95000,
        "combined_household_income": 184000,
        "monthly_expenses": {
            "mortgage": 2800,
            "car_payment": 520,
            "car_insurance": 180,
            "gas": 160,
            "groceries": 600,
            "utilities": 140,
            "phone": 95,
            "student_loans": 485,
            "childcare": 1200,
            "life_insurance": 85,
            "health_insurance": 245,
            "entertainment": 200,
            "dining_out": 400,
            "tsp_contribution": 445,
            "529_plan": 300
        },
        "debts": {
            "student_loans_hers": 42000,
            "student_loans_spouse": 85000,
            "mortgage": 420000
        },
        "assets": {
            "emergency_fund": 15000,
            "tsp_balance": 28000,
            "401k_balance": 35000,
            "joint_savings": 25000,
            "home_equity": 100000,
            "credit_score": 780
        }
    }
}

def calculate_monthly_totals(expenses):
    """Calculate total monthly expenses"""
    return sum(expenses.values())

def calculate_debt_to_income_ratio(monthly_income, monthly_debt_payments):
    """Calculate debt-to-income ratio"""
    return (monthly_debt_payments / monthly_income) * 100

def calculate_emergency_fund_months(emergency_fund, monthly_expenses):
    """Calculate how many months emergency fund will last"""
    return emergency_fund / monthly_expenses

def calculate_net_worth(assets, debts):
    """Calculate net worth"""
    total_assets = sum(assets.values())
    total_debts = sum(debts.values())
    return total_assets - total_debts

def calculate_savings_rate(monthly_income, monthly_expenses, retirement_contributions=0):
    """Calculate savings rate"""
    total_savings = monthly_income - monthly_expenses + retirement_contributions
    return (total_savings / monthly_income) * 100

def analyze_credit_score(score):
    """Analyze credit score and provide recommendations"""
    if score >= 750:
        return "Excellent", "Continue maintaining good credit habits"
    elif score >= 700:
        return "Good", "Minor improvements could help reach excellent range"
    elif score >= 650:
        return "Fair", "Focus on paying bills on time and reducing debt"
    else:
        return "Poor", "Priority focus on improving credit score"

def analyze_expense_categories(expenses):
    """Analyze expense categories and provide recommendations"""
    analysis = {
        "housing": 0,
        "transportation": 0,
        "food": 0,
        "debt": 0,
        "utilities": 0,
        "entertainment": 0,
        "other": 0
    }
    
    # Categorize expenses
    housing_keys = ['rent', 'mortgage']
    transportation_keys = ['car_payment', 'car_insurance', 'gas']
    food_keys = ['groceries', 'dining_out']
    debt_keys = ['student_loans', 'credit_cards']
    utilities_keys = ['utilities', 'phone']
    entertainment_keys = ['entertainment', 'streaming', 'streaming_software', 'gym']
    
    for category, amount in expenses.items():
        if any(key in category for key in housing_keys):
            analysis["housing"] += amount
        elif any(key in category for key in transportation_keys):
            analysis["transportation"] += amount
        elif any(key in category for key in food_keys):
            analysis["food"] += amount
        elif any(key in category for key in debt_keys):
            analysis["debt"] += amount
        elif any(key in category for key in utilities_keys):
            analysis["utilities"] += amount
        elif any(key in category for key in entertainment_keys):
            analysis["entertainment"] += amount
        else:
            analysis["other"] += amount
    
    return analysis

def generate_financial_recommendations(persona_data, analysis):
    """Generate personalized financial recommendations"""
    recommendations = []
    
    # Emergency fund recommendations
    emergency_months = analysis["emergency_fund_months"]
    if emergency_months < 3:
        recommendations.append(f"🚨 URGENT: Build emergency fund to at least 3 months of expenses (currently {emergency_months:.1f} months)")
    elif emergency_months < 6:
        recommendations.append(f"⚠️ Build emergency fund to 6 months of expenses (currently {emergency_months:.1f} months)")
    else:
        recommendations.append(f"✅ Emergency fund is well-funded ({emergency_months:.1f} months)")
    
    # Debt-to-income ratio recommendations
    dti_ratio = analysis["debt_to_income_ratio"]
    if dti_ratio > 40:
        recommendations.append(f"🚨 URGENT: Debt-to-income ratio is {dti_ratio:.1f}% (should be <40%)")
    elif dti_ratio > 30:
        recommendations.append(f"⚠️ Consider reducing debt payments (currently {dti_ratio:.1f}%)")
    else:
        recommendations.append(f"✅ Debt-to-income ratio is healthy ({dti_ratio:.1f}%)")
    
    # Credit score recommendations
    credit_rating, credit_advice = analyze_credit_score(persona_data["assets"]["credit_score"])
    recommendations.append(f"💳 Credit Score: {credit_rating} - {credit_advice}")
    
    # Savings rate recommendations
    savings_rate = analysis["savings_rate"]
    if savings_rate < 10:
        recommendations.append(f"💰 Increase savings rate (currently {savings_rate:.1f}%, target 20%+)")
    elif savings_rate < 20:
        recommendations.append(f"💰 Good savings rate, aim for 20%+ (currently {savings_rate:.1f}%)")
    else:
        recommendations.append(f"✅ Excellent savings rate ({savings_rate:.1f}%)")
    
    # Expense category recommendations
    expense_analysis = analysis["expense_analysis"]
    total_expenses = sum(expense_analysis.values())
    
    # Housing (should be <30% of income)
    housing_pct = (expense_analysis["housing"] / analysis["monthly_income"]) * 100
    if housing_pct > 30:
        recommendations.append(f"🏠 Housing costs are {housing_pct:.1f}% of income (target <30%)")
    else:
        recommendations.append(f"✅ Housing costs are reasonable ({housing_pct:.1f}% of income)")
    
    # Transportation (should be <15% of income)
    transport_pct = (expense_analysis["transportation"] / analysis["monthly_income"]) * 100
    if transport_pct > 15:
        recommendations.append(f"🚗 Transportation costs are {transport_pct:.1f}% of income (target <15%)")
    else:
        recommendations.append(f"✅ Transportation costs are reasonable ({transport_pct:.1f}% of income)")
    
    return recommendations

def test_financial_profile(persona_name, persona_data):
    """Test complete financial profile for a persona"""
    print(f"\n{'='*70}")
    print(f"FINANCIAL PROFILE TESTING: {persona_data['name']}")
    print(f"Tier: {persona_data['tier']}")
    print(f"Location: {persona_data['location']}")
    print(f"{'='*70}")
    
    # Calculate basic metrics
    monthly_expenses = calculate_monthly_totals(persona_data["monthly_expenses"])
    monthly_income = persona_data["monthly_income"]
    
    # Calculate debt payments
    debt_payments = 0
    for debt_type, amount in persona_data["debts"].items():
        if "student_loans" in debt_type:
            debt_payments += persona_data["monthly_expenses"].get("student_loans", 0)
        elif "credit_cards" in debt_type:
            debt_payments += persona_data["monthly_expenses"].get("credit_cards", 0)
        elif "mortgage" in debt_type:
            debt_payments += persona_data["monthly_expenses"].get("mortgage", 0)
    
    # Calculate key financial metrics
    analysis = {
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_debt_payments": debt_payments,
        "debt_to_income_ratio": calculate_debt_to_income_ratio(monthly_income, debt_payments),
        "emergency_fund_months": calculate_emergency_fund_months(
            persona_data["assets"]["emergency_fund"], 
            monthly_expenses
        ),
        "net_worth": calculate_net_worth(persona_data["assets"], persona_data["debts"]),
        "savings_rate": calculate_savings_rate(
            monthly_income, 
            monthly_expenses,
            persona_data["monthly_expenses"].get("401k_contribution", 0) + 
            persona_data["monthly_expenses"].get("tsp_contribution", 0)
        ),
        "expense_analysis": analyze_expense_categories(persona_data["monthly_expenses"])
    }
    
    # Display financial overview
    print(f"\n📊 FINANCIAL OVERVIEW")
    print("-" * 40)
    print(f"Monthly Income: ${monthly_income:,}")
    print(f"Monthly Expenses: ${monthly_expenses:,}")
    print(f"Monthly Debt Payments: ${debt_payments:,}")
    print(f"Emergency Fund: ${persona_data['assets']['emergency_fund']:,}")
    print(f"Credit Score: {persona_data['assets']['credit_score']}")
    
    # Display key ratios
    print(f"\n📈 KEY FINANCIAL RATIOS")
    print("-" * 40)
    print(f"Debt-to-Income Ratio: {analysis['debt_to_income_ratio']:.1f}%")
    print(f"Emergency Fund Coverage: {analysis['emergency_fund_months']:.1f} months")
    print(f"Savings Rate: {analysis['savings_rate']:.1f}%")
    print(f"Net Worth: ${analysis['net_worth']:,}")
    
    # Display expense breakdown
    print(f"\n💸 EXPENSE BREAKDOWN")
    print("-" * 40)
    expense_analysis = analysis["expense_analysis"]
    total_expenses = sum(expense_analysis.values())
    
    for category, amount in expense_analysis.items():
        if amount > 0:
            percentage = (amount / total_expenses) * 100
            print(f"{category.title()}: ${amount:,} ({percentage:.1f}%)")
    
    # Display debt summary
    print(f"\n💳 DEBT SUMMARY")
    print("-" * 40)
    total_debt = sum(persona_data["debts"].values())
    print(f"Total Debt: ${total_debt:,}")
    for debt_type, amount in persona_data["debts"].items():
        print(f"  {debt_type.replace('_', ' ').title()}: ${amount:,}")
    
    # Display asset summary
    print(f"\n💰 ASSET SUMMARY")
    print("-" * 40)
    total_assets = sum(persona_data["assets"].values())
    print(f"Total Assets: ${total_assets:,}")
    for asset_type, amount in persona_data["assets"].items():
        if asset_type != "credit_score":
            print(f"  {asset_type.replace('_', ' ').title()}: ${amount:,}")
    
    # Generate and display recommendations
    print(f"\n💡 FINANCIAL RECOMMENDATIONS")
    print("-" * 40)
    recommendations = generate_financial_recommendations(persona_data, analysis)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Calculate financial health score
    health_score = calculate_financial_health_score(analysis, persona_data)
    print(f"\n🏆 FINANCIAL HEALTH SCORE: {health_score}/100")
    
    if health_score >= 80:
        print("Status: EXCELLENT - Strong financial foundation")
    elif health_score >= 60:
        print("Status: GOOD - Some areas for improvement")
    elif health_score >= 40:
        print("Status: FAIR - Multiple areas need attention")
    else:
        print("Status: POOR - Significant financial challenges")
    
    return {
        "persona": persona_data["name"],
        "tier": persona_data["tier"],
        "analysis": analysis,
        "recommendations": recommendations,
        "health_score": health_score,
        "status": "SUCCESS"
    }

def calculate_financial_health_score(analysis, persona_data):
    """Calculate overall financial health score (0-100)"""
    score = 0
    
    # Emergency fund (25 points)
    emergency_months = analysis["emergency_fund_months"]
    if emergency_months >= 6:
        score += 25
    elif emergency_months >= 3:
        score += 15
    elif emergency_months >= 1:
        score += 10
    
    # Debt-to-income ratio (25 points)
    dti_ratio = analysis["debt_to_income_ratio"]
    if dti_ratio <= 20:
        score += 25
    elif dti_ratio <= 30:
        score += 20
    elif dti_ratio <= 40:
        score += 10
    
    # Savings rate (20 points)
    savings_rate = analysis["savings_rate"]
    if savings_rate >= 20:
        score += 20
    elif savings_rate >= 15:
        score += 15
    elif savings_rate >= 10:
        score += 10
    elif savings_rate >= 5:
        score += 5
    
    # Credit score (15 points)
    credit_score = persona_data["assets"]["credit_score"]
    if credit_score >= 750:
        score += 15
    elif credit_score >= 700:
        score += 12
    elif credit_score >= 650:
        score += 8
    elif credit_score >= 600:
        score += 5
    
    # Net worth (15 points)
    net_worth = analysis["net_worth"]
    if net_worth > 0:
        score += 15
    elif net_worth > -10000:
        score += 10
    elif net_worth > -50000:
        score += 5
    
    return min(100, max(0, score))

def generate_financial_report(all_results):
    """Generate comprehensive financial analysis report"""
    print(f"\n{'='*80}")
    print("MINGUS PERSONAL FINANCE APPLICATION - FINANCIAL PROFILE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    print(f"\n📋 FINANCIAL PROFILE SUMMARY")
    print("-" * 40)
    print(f"Total Personas Analyzed: {len(all_results)}")
    
    # Calculate average metrics
    avg_health_score = sum(r["health_score"] for r in all_results) / len(all_results)
    avg_savings_rate = sum(r["analysis"]["savings_rate"] for r in all_results) / len(all_results)
    avg_emergency_months = sum(r["analysis"]["emergency_fund_months"] for r in all_results) / len(all_results)
    
    print(f"Average Financial Health Score: {avg_health_score:.1f}/100")
    print(f"Average Savings Rate: {avg_savings_rate:.1f}%")
    print(f"Average Emergency Fund Coverage: {avg_emergency_months:.1f} months")
    
    # Tier analysis
    print(f"\n📊 TIER-SPECIFIC ANALYSIS")
    print("-" * 40)
    
    for result in all_results:
        print(f"\n{result['persona']} ({result['tier']}):")
        print(f"  Financial Health Score: {result['health_score']}/100")
        print(f"  Monthly Income: ${result['analysis']['monthly_income']:,}")
        print(f"  Monthly Expenses: ${result['analysis']['monthly_expenses']:,}")
        print(f"  Emergency Fund: {result['analysis']['emergency_fund_months']:.1f} months")
        print(f"  Debt-to-Income: {result['analysis']['debt_to_income_ratio']:.1f}%")
        print(f"  Savings Rate: {result['analysis']['savings_rate']:.1f}%")
        print(f"  Net Worth: ${result['analysis']['net_worth']:,}")
    
    # Key recommendations by tier
    print(f"\n💡 TIER-SPECIFIC RECOMMENDATIONS")
    print("-" * 40)
    
    for result in all_results:
        print(f"\n{result['persona']} ({result['tier']}):")
        for i, rec in enumerate(result['recommendations'][:3], 1):  # Top 3 recommendations
            print(f"  {i}. {rec}")
    
    # Overall financial trends
    print(f"\n📈 OVERALL FINANCIAL TRENDS")
    print("-" * 40)
    
    # Calculate common issues
    common_issues = []
    if avg_emergency_months < 3:
        common_issues.append("Emergency fund coverage below 3 months")
    if avg_savings_rate < 15:
        common_issues.append("Savings rate below recommended 15%")
    
    if common_issues:
        print("Common Financial Challenges:")
        for issue in common_issues:
            print(f"  • {issue}")
    else:
        print("✅ All personas show strong financial fundamentals")
    
    print(f"\n✅ FINANCIAL PROFILE ANALYSIS COMPLETED")
    print(f"All {len(all_results)} personas analyzed with detailed recommendations")

def main():
    """Main financial profile testing function"""
    print("🚀 MINGUS PERSONAL FINANCE APPLICATION - FINANCIAL PROFILE TESTING")
    print("Testing complete financial profiles for all three personas")
    print("=" * 80)
    
    all_results = []
    
    # Test each persona's financial profile
    for persona_name, persona_data in FINANCIAL_PERSONAS.items():
        try:
            result = test_financial_profile(persona_name, persona_data)
            all_results.append(result)
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Error testing {persona_data['name']}: {e}")
            continue
    
    # Generate comprehensive report
    generate_financial_report(all_results)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"mingus_financial_profiles_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📁 Financial profile results saved to: {filename}")

if __name__ == "__main__":
    main()

