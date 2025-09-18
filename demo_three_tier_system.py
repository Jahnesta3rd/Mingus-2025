#!/usr/bin/env python3
"""
Three-Tier Job Recommendation System Demo
Demonstrates the functionality of the three-tier job recommendation system
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.three_tier_job_selector import ThreeTierJobSelector, JobTier
from backend.utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel

def print_separator(title=""):
    """Print a formatted separator"""
    print("\n" + "="*80)
    if title:
        print(f" {title}")
        print("="*80)
    print()

def print_tier_header(tier_name, tier_spec):
    """Print formatted tier header"""
    print(f"\n🎯 {tier_name.upper()} TIER")
    print("-" * 50)
    print(f"Description: {tier_spec['description']}")
    print(f"Salary Increase: {int(tier_spec['salary_increase_min']*100)}-{int(tier_spec['salary_increase_max']*100)}%")
    print(f"Success Probability: {int(tier_spec['success_probability_min']*100)}%+")
    print(f"Risk Level: {tier_spec['risk_level'].upper()}")
    print(f"Company Types: {', '.join(tier_spec['company_types'])}")

def print_job_recommendation(rec, index):
    """Print formatted job recommendation"""
    print(f"\n{index+1}. {rec.job.title} at {rec.job.company}")
    print(f"   Location: {rec.job.location}")
    print(f"   Salary: ${rec.job.salary_min:,} - ${rec.job.salary_max:,}")
    print(f"   Salary Increase: {rec.salary_increase_potential:.1%}")
    print(f"   Success Probability: {rec.success_probability:.1%}")
    print(f"   Overall Score: {rec.job.overall_score:.1f}/100")
    print(f"   Remote Friendly: {'Yes' if rec.job.remote_friendly else 'No'}")
    
    # Skills gap analysis
    if rec.skills_gap_analysis:
        print(f"   Key Skill Gaps:")
        for gap in rec.skills_gap_analysis[:3]:  # Show top 3 gaps
            if gap.priority == "high":
                print(f"     • {gap.skill} ({gap.priority} priority) - {gap.learning_time_estimate}")
    
    # Application strategy highlights
    if rec.application_strategy.key_selling_points:
        print(f"   Key Selling Points:")
        for point in rec.application_strategy.key_selling_points[:2]:
            print(f"     • {point}")
    
    # Preparation timeline
    if rec.preparation_roadmap.total_preparation_time:
        print(f"   Preparation Time: {rec.preparation_roadmap.total_preparation_time}")

def print_skills_gap_analysis(skills_gaps):
    """Print detailed skills gap analysis"""
    if not skills_gaps:
        print("   No significant skill gaps identified.")
        return
    
    print("\n📊 SKILLS GAP ANALYSIS")
    print("-" * 30)
    
    for gap in skills_gaps:
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(gap.priority, "⚪")
        print(f"\n{priority_emoji} {gap.skill} ({gap.category.value})")
        print(f"   Current Level: {gap.current_level:.1f}/1.0")
        print(f"   Required Level: {gap.required_level:.1f}/1.0")
        print(f"   Gap Size: {gap.gap_size:.1f}")
        print(f"   Learning Time: {gap.learning_time_estimate}")
        print(f"   Resources: {', '.join(gap.resources[:2])}")

def print_application_strategy(strategy):
    """Print application strategy details"""
    print("\n📋 APPLICATION STRATEGY")
    print("-" * 25)
    
    print(f"\nTimeline:")
    for phase, timeline in strategy.timeline.items():
        print(f"  {phase}: {timeline}")
    
    print(f"\nKey Selling Points:")
    for point in strategy.key_selling_points:
        print(f"  • {point}")
    
    print(f"\nPotential Challenges:")
    for challenge in strategy.potential_challenges:
        print(f"  • {challenge}")
    
    print(f"\nInterview Preparation:")
    for phase, tasks in strategy.interview_preparation.items():
        print(f"  {phase}:")
        for task in tasks[:2]:  # Show first 2 tasks
            print(f"    • {task}")
    
    print(f"\nSalary Negotiation Tips:")
    for tip in strategy.salary_negotiation_tips[:3]:
        print(f"  • {tip}")

def print_preparation_roadmap(roadmap):
    """Print preparation roadmap details"""
    print("\n🗺️ PREPARATION ROADMAP")
    print("-" * 25)
    
    print(f"Total Preparation Time: {roadmap.total_preparation_time}")
    
    print(f"\nPhases:")
    for i, phase in enumerate(roadmap.phases, 1):
        print(f"  {i}. {phase['name']} ({phase['duration']})")
        for task in phase['tasks'][:2]:  # Show first 2 tasks
            print(f"     • {task}")
    
    if roadmap.certification_recommendations:
        print(f"\nRecommended Certifications:")
        for cert in roadmap.certification_recommendations:
            print(f"  • {cert}")
    
    if roadmap.networking_plan:
        print(f"\nNetworking Plan:")
        for activity in roadmap.networking_plan[:3]:
            print(f"  • {activity}")

async def demo_three_tier_system():
    """Demonstrate the three-tier job recommendation system"""
    print_separator("THREE-TIER JOB RECOMMENDATION SYSTEM DEMO")
    
    # Initialize the selector
    print("Initializing Three-Tier Job Selector...")
    selector = ThreeTierJobSelector()
    
    # Display tier specifications
    print_separator("TIER SPECIFICATIONS")
    for tier in JobTier:
        tier_spec = selector.tier_specs[tier]
        print_tier_header(tier.value, tier_spec)
    
    # Create sample search criteria
    print_separator("SAMPLE SEARCH CRITERIA")
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA", "Houston-The Woodlands-Sugar Land, TX"],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False,
        min_company_rating=3.5
    )
    
    print(f"Current Salary: ${criteria.current_salary:,}")
    print(f"Career Field: {criteria.career_field.value}")
    print(f"Experience Level: {criteria.experience_level.value}")
    print(f"Preferred Locations: {', '.join(criteria.preferred_msas)}")
    print(f"Remote OK: {criteria.remote_ok}")
    print(f"Company Size Preference: {criteria.company_size_preference}")
    
    # Generate recommendations
    print_separator("GENERATING RECOMMENDATIONS")
    print("Searching for job opportunities across all three tiers...")
    
    try:
        recommendations = await selector.generate_tiered_recommendations(
            criteria, max_recommendations_per_tier=3
        )
        
        # Display recommendations by tier
        for tier in JobTier:
            tier_recommendations = recommendations.get(tier, [])
            if not tier_recommendations:
                continue
            
            tier_spec = selector.tier_specs[tier]
            print_tier_header(tier.value, tier_spec)
            
            for i, rec in enumerate(tier_recommendations):
                print_job_recommendation(rec, i)
        
        # Display detailed analysis for first recommendation of each tier
        print_separator("DETAILED ANALYSIS")
        
        for tier in JobTier:
            tier_recommendations = recommendations.get(tier, [])
            if not tier_recommendations:
                continue
            
            rec = tier_recommendations[0]  # Get first recommendation
            print(f"\n🔍 DETAILED ANALYSIS: {rec.job.title} at {rec.job.company}")
            print("=" * 60)
            
            # Skills gap analysis
            print_skills_gap_analysis(rec.skills_gap_analysis)
            
            # Application strategy
            print_application_strategy(rec.application_strategy)
            
            # Preparation roadmap
            print_preparation_roadmap(rec.preparation_roadmap)
        
        # Display tier summary
        print_separator("TIER SUMMARY")
        summary = selector.get_tier_summary(recommendations)
        
        for tier_name, tier_summary in summary.items():
            print(f"\n{tier_name.upper()} TIER SUMMARY:")
            print(f"  Count: {tier_summary['count']} recommendations")
            print(f"  Average Salary Increase: {tier_summary['avg_salary_increase']}%")
            print(f"  Average Success Probability: {tier_summary['avg_success_probability']}%")
            print(f"  Average Preparation Time: {tier_summary['avg_preparation_time']}")
            print(f"  Industries: {', '.join(tier_summary['industries'])}")
            print(f"  Company Sizes: {', '.join(tier_summary['company_sizes'])}")
        
        print_separator("DEMO COMPLETE")
        print("✅ Three-tier job recommendation system demonstration completed successfully!")
        print(f"📊 Total recommendations generated: {sum(len(recs) for recs in recommendations.values())}")
        print(f"🎯 Recommendations across {len([t for t in recommendations.values() if t])} tiers")
        
    except Exception as e:
        print(f"❌ Error generating recommendations: {str(e)}")
        print("This is expected in the demo as we don't have actual job data.")
        print("The system is designed to work with real job opportunities from the job matching system.")

def main():
    """Main function to run the demo"""
    print("Starting Three-Tier Job Recommendation System Demo...")
    print("This demo showcases the system's capabilities with sample data.")
    
    # Run the async demo
    asyncio.run(demo_three_tier_system())

if __name__ == "__main__":
    main()
