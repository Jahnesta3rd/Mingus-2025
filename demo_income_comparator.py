#!/usr/bin/env python3
"""
Income Comparator Demonstration
Shows comprehensive income analysis for African American professionals
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from ml.models.income_comparator import IncomeComparator, EducationLevel

def demo_income_analysis():
    """Demonstrate comprehensive income analysis"""
    
    print("🎯 INCOME COMPARATOR DEMONSTRATION")
    print("=" * 60)
    print("Comprehensive income analysis for African American professionals")
    print("Target demographic: Ages 25-35, $40k-100k income range")
    print("Data source: 2022 American Community Survey")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize comparator
    comparator = IncomeComparator()
    
    # Demo scenarios
    scenarios = [
        {
            'name': 'Entry-Level Professional',
            'income': 45000,
            'location': 'Atlanta',
            'education': EducationLevel.BACHELORS,
            'description': 'Recent college graduate starting career'
        },
        {
            'name': 'Mid-Career Professional',
            'income': 65000,
            'location': 'Houston',
            'education': EducationLevel.BACHELORS,
            'description': '5-7 years experience, looking to advance'
        },
        {
            'name': 'Senior Professional',
            'income': 85000,
            'location': 'Washington DC',
            'education': EducationLevel.MASTERS,
            'description': '10+ years experience, leadership potential'
        },
        {
            'name': 'High-Performing Professional',
            'income': 95000,
            'location': 'New York City',
            'education': EducationLevel.BACHELORS,
            'description': 'Top performer, seeking executive roles'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📊 SCENARIO {i}: {scenario['name']}")
        print("=" * 60)
        print(f"Profile: {scenario['description']}")
        print(f"Income: ${scenario['income']:,}")
        print(f"Location: {scenario['location']}")
        print(f"Education: {scenario['education'].value.replace('_', ' ').title()}")
        print()
        
        # Run analysis
        result = comparator.analyze_income(
            user_income=scenario['income'],
            location=scenario['location'],
            education_level=scenario['education']
        )
        
        # Display key metrics
        print("🎯 KEY METRICS:")
        print(f"  Overall Percentile: {result.overall_percentile:.1f}%")
        print(f"  Career Opportunity Score: {result.career_opportunity_score:.1f}/100")
        print(f"  Primary Gap: {result.primary_gap.group_name}")
        print(f"  Gap Amount: ${abs(result.primary_gap.income_gap):,}")
        print()
        
        # Display top 3 comparisons
        print("📈 TOP COMPARISONS:")
        sorted_comparisons = sorted(result.comparisons, key=lambda x: abs(x.income_gap), reverse=True)
        for j, comparison in enumerate(sorted_comparisons[:3], 1):
            gap_sign = "+" if comparison.income_gap >= 0 else ""
            print(f"  {j}. {comparison.group_name}")
            print(f"     Median: ${comparison.median_income:,}")
            print(f"     Your Percentile: {comparison.percentile_rank:.1f}%")
            print(f"     Gap: {gap_sign}${comparison.income_gap:,} ({gap_sign}{comparison.gap_percentage:+.1f}%)")
            print(f"     Insight: {comparison.motivational_insight}")
            print()
        
        # Display motivational summary
        print("💡 MOTIVATIONAL SUMMARY:")
        print(f"  {result.motivational_summary}")
        print()
        
        # Display action plan
        print("🚀 ACTION PLAN:")
        for k, action in enumerate(result.action_plan, 1):
            print(f"  {k}. {action}")
        print()
        
        # Display next steps
        print("📋 IMMEDIATE NEXT STEPS:")
        for l, step in enumerate(result.next_steps, 1):
            print(f"  {l}. {step}")
        print()
        
        print("-" * 60)
        print()

def demo_demographic_data():
    """Demonstrate available demographic data"""
    
    print("📊 DEMOGRAPHIC DATA OVERVIEW")
    print("=" * 60)
    
    comparator = IncomeComparator()
    
    # Show available locations
    print("🏙️  AVAILABLE METRO AREAS:")
    locations = comparator.get_available_locations()
    for i, location in enumerate(locations, 1):
        print(f"  {i:2d}. {location}")
    print()
    
    # Show demographic summary
    summary = comparator.get_demographic_summary()
    print("📈 DATA SUMMARY:")
    print(f"  Data Year: {summary['data_year']}")
    print(f"  Data Source: {summary['data_source']}")
    print(f"  National Groups: {len(summary['national_groups'])}")
    print(f"  Metro Areas: {len(summary['metro_areas'])}")
    print()
    
    # Show sample demographic data
    print("🎯 SAMPLE DEMOGRAPHIC BENCHMARKS:")
    demo_data = comparator.demographic_data
    
    key_groups = [
        'national_median',
        'african_american',
        'age_25_35',
        'african_american_25_35',
        'college_graduate',
        'african_american_college'
    ]
    
    for group_key in key_groups:
        if group_key in demo_data:
            data = demo_data[group_key]
            print(f"  {data.group_name}:")
            print(f"    Median Income: ${data.median_income:,}")
            print(f"    Mean Income: ${data.mean_income:,}")
            print(f"    25th Percentile: ${data.percentile_25:,}")
            print(f"    75th Percentile: ${data.percentile_75:,}")
            print()

def demo_percentile_calculations():
    """Demonstrate percentile calculations"""
    
    print("📊 PERCENTILE CALCULATION DEMO")
    print("=" * 60)
    
    comparator = IncomeComparator()
    
    # Test different income levels
    test_incomes = [30000, 45000, 60000, 75000, 90000, 120000]
    
    print("Income Level Analysis:")
    print("Income Level | National Median | African American | Age 25-35 | AA Age 25-35")
    print("-" * 80)
    
    for income in test_incomes:
        national = comparator._compare_national_median(income)
        aa = comparator._compare_african_american(income)
        age = comparator._compare_age_group(income, "25-35")
        aa_age = comparator._compare_african_american_age_group(income, "25-35")
        
        print(f"${income:8,} | {national.percentile_rank:14.1f}% | {aa.percentile_rank:16.1f}% | {age.percentile_rank:10.1f}% | {aa_age.percentile_rank:12.1f}%")
    
    print()

def demo_opportunity_analysis():
    """Demonstrate career opportunity analysis"""
    
    print("🎯 CAREER OPPORTUNITY ANALYSIS")
    print("=" * 60)
    
    comparator = IncomeComparator()
    
    # Analyze different scenarios
    scenarios = [
        {"income": 40000, "description": "Below median across all groups"},
        {"income": 55000, "description": "Above AA median, below national"},
        {"income": 70000, "description": "Above most medians, good position"},
        {"income": 90000, "description": "High performer, leadership potential"}
    ]
    
    for scenario in scenarios:
        print(f"💰 Income: ${scenario['income']:,}")
        print(f"   Description: {scenario['description']}")
        
        result = comparator.analyze_income(scenario['income'])
        
        print(f"   Overall Percentile: {result.overall_percentile:.1f}%")
        print(f"   Career Opportunity Score: {result.career_opportunity_score:.1f}/100")
        
        # Find largest gap
        largest_gap = max(result.comparisons, key=lambda x: abs(x.income_gap))
        gap_sign = "+" if largest_gap.income_gap >= 0 else ""
        print(f"   Largest Gap: {gap_sign}${largest_gap.income_gap:,} vs {largest_gap.group_name}")
        print(f"   Primary Insight: {largest_gap.motivational_insight}")
        print()

def main():
    """Main demonstration function"""
    
    print("🎯 MINGUS INCOME COMPARATOR DEMONSTRATION")
    print("=" * 80)
    print("Comprehensive income analysis for African American professionals")
    print("Target: Ages 25-35, $40k-100k income range")
    print("Purpose: Motivate career advancement through demographic insights")
    print("=" * 80)
    print()
    
    # Run demonstrations
    demo_demographic_data()
    demo_percentile_calculations()
    demo_opportunity_analysis()
    demo_income_analysis()
    
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("The IncomeComparator provides comprehensive demographic analysis")
    print("to help African American professionals understand their income")
    print("position and identify career advancement opportunities.")
    print()
    print("Key Features:")
    print("• Multiple demographic comparisons (national, racial, age, location)")
    print("• Percentile rankings and income gap analysis")
    print("• Motivational insights and action items")
    print("• Career opportunity scoring")
    print("• Comprehensive action plans")
    print()
    print("Ready for integration with the job recommendation engine!")


if __name__ == "__main__":
    main() 