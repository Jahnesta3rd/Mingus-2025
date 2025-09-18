#!/usr/bin/env python3
"""
Three-Tier Job Recommendation System - Usage Example
Shows how to use the three-tier job recommendation system in practice
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

async def example_basic_usage():
    """Example of basic usage of the three-tier system"""
    print("🚀 Three-Tier Job Recommendation System - Basic Usage Example")
    print("=" * 70)
    
    # 1. Initialize the selector
    print("\n1. Initializing Three-Tier Job Selector...")
    selector = ThreeTierJobSelector()
    print("✅ Selector initialized successfully")
    
    # 2. Create search criteria
    print("\n2. Creating search criteria...")
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,  # 25% target increase
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=[
            "Atlanta-Sandy Springs-Alpharetta, GA",
            "Houston-The Woodlands-Sugar Land, TX"
        ],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False,
        min_company_rating=3.5
    )
    print("✅ Search criteria created")
    print(f"   Current Salary: ${criteria.current_salary:,}")
    print(f"   Career Field: {criteria.career_field.value}")
    print(f"   Experience Level: {criteria.experience_level.value}")
    print(f"   Preferred Locations: {', '.join(criteria.preferred_msas)}")
    
    # 3. Generate recommendations
    print("\n3. Generating tiered recommendations...")
    try:
        recommendations = await selector.generate_tiered_recommendations(
            criteria, max_recommendations_per_tier=2
        )
        print("✅ Recommendations generated successfully")
        
        # 4. Display results by tier
        print("\n4. Recommendation Results:")
        print("-" * 50)
        
        for tier in JobTier:
            tier_recommendations = recommendations.get(tier, [])
            print(f"\n{tier.value.upper()} TIER ({len(tier_recommendations)} recommendations):")
            
            for i, rec in enumerate(tier_recommendations, 1):
                print(f"  {i}. {rec.job.title} at {rec.job.company}")
                print(f"     Salary: ${rec.job.salary_min:,} - ${rec.job.salary_max:,}")
                print(f"     Increase: {rec.salary_increase_potential:.1%}")
                print(f"     Success Probability: {rec.success_probability:.1%}")
                print(f"     Location: {rec.job.location}")
                print(f"     Remote: {'Yes' if rec.job.remote_friendly else 'No'}")
        
        # 5. Get tier summary
        print("\n5. Tier Summary:")
        print("-" * 20)
        summary = selector.get_tier_summary(recommendations)
        
        for tier_name, tier_summary in summary.items():
            print(f"\n{tier_name.upper()}:")
            print(f"  Count: {tier_summary['count']} jobs")
            print(f"  Avg Salary Increase: {tier_summary['avg_salary_increase']}%")
            print(f"  Avg Success Probability: {tier_summary['avg_success_probability']}%")
            print(f"  Avg Preparation Time: {tier_summary['avg_preparation_time']}")
            print(f"  Industries: {', '.join(tier_summary['industries'])}")
        
        return recommendations
        
    except Exception as e:
        print(f"❌ Error generating recommendations: {str(e)}")
        print("Note: This is expected in the example as we don't have real job data.")
        return None

async def example_detailed_analysis():
    """Example of detailed analysis for a specific recommendation"""
    print("\n\n🔍 Detailed Analysis Example")
    print("=" * 40)
    
    # This would typically use a real recommendation from the previous example
    print("This example shows how to analyze a specific job recommendation:")
    print("\n1. Skills Gap Analysis:")
    print("   • Python (Technical) - High Priority")
    print("     Current: 0.6/1.0, Required: 0.9/1.0")
    print("     Learning Time: 3-6 months")
    print("     Resources: Python.org tutorial, Coursera course")
    
    print("\n2. Application Strategy:")
    print("   Timeline:")
    print("     Week 1: Research company and role")
    print("     Week 2: Tailor resume and cover letter")
    print("     Week 3: Submit application")
    print("     Week 4: Prepare for interviews")
    
    print("\n3. Preparation Roadmap:")
    print("   Total Time: 2-4 weeks")
    print("   Phases:")
    print("     1. Research and Preparation (1-2 weeks)")
    print("     2. Application and Follow-up (1-2 weeks)")
    
    print("\n4. Key Selling Points:")
    print("   • Proven track record in similar roles")
    print("   • Strong technical skills match")
    print("   • Experience with established processes")
    
    print("\n5. Interview Preparation:")
    print("   Technical:")
    print("     • Review job-specific requirements")
    print("     • Practice coding problems")
    print("   Behavioral:")
    print("     • Prepare STAR method examples")
    print("     • Research company culture")

def example_api_usage():
    """Example of using the API endpoints"""
    print("\n\n🌐 API Usage Example")
    print("=" * 30)
    
    print("1. Get Tiered Recommendations:")
    print("   POST /api/three-tier/recommendations")
    print("   Body:")
    print(json.dumps({
        "current_salary": 75000,
        "career_field": "technology",
        "experience_level": "mid",
        "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
        "remote_ok": True,
        "max_commute_time": 30,
        "must_have_benefits": ["health insurance", "401k"],
        "company_size_preference": "mid",
        "industry_preference": "technology",
        "equity_required": False,
        "min_company_rating": 3.5,
        "max_recommendations_per_tier": 5
    }, indent=2))
    
    print("\n2. Get Specific Tier Recommendations:")
    print("   GET /api/three-tier/tier/conservative")
    print("   Query Parameters:")
    print("   ?current_salary=75000&career_field=technology&experience_level=mid")
    
    print("\n3. Get Tier Summary:")
    print("   GET /api/three-tier/tiers/summary")
    
    print("\n4. Get Job Analysis:")
    print("   GET /api/three-tier/job/{job_id}/analysis")
    print("   Query Parameters:")
    print("   ?current_salary=75000&career_field=technology&experience_level=mid")

def example_tier_comparison():
    """Example of comparing different tiers"""
    print("\n\n📊 Tier Comparison Example")
    print("=" * 35)
    
    print("CONSERVATIVE TIER:")
    print("  • Salary Increase: 15-20%")
    print("  • Success Probability: 70%+")
    print("  • Preparation Time: 2-4 weeks")
    print("  • Risk Level: Low")
    print("  • Best For: Similar roles, established companies")
    print("  • Company Types: Fortune 500, Large Enterprise")
    
    print("\nOPTIMAL TIER:")
    print("  • Salary Increase: 25-30%")
    print("  • Success Probability: 50%+")
    print("  • Preparation Time: 1-3 months")
    print("  • Risk Level: Medium")
    print("  • Best For: Role elevation, growth companies")
    print("  • Company Types: Growth Company, Mid-size, Scale-up")
    
    print("\nSTRETCH TIER:")
    print("  • Salary Increase: 35%+")
    print("  • Success Probability: 30%+")
    print("  • Preparation Time: 3-6 months")
    print("  • Risk Level: High")
    print("  • Best For: Career pivots, innovation companies")
    print("  • Company Types: Startup, Innovation, High-growth")

async def main():
    """Main function to run all examples"""
    print("🎯 Three-Tier Job Recommendation System - Complete Usage Guide")
    print("=" * 80)
    
    # Run basic usage example
    recommendations = await example_basic_usage()
    
    # Run detailed analysis example
    await example_detailed_analysis()
    
    # Show API usage
    example_api_usage()
    
    # Show tier comparison
    example_tier_comparison()
    
    print("\n\n✅ All examples completed!")
    print("\nNext Steps:")
    print("1. Run the demo: python demo_three_tier_system.py")
    print("2. Run tests: python test_three_tier_job_selector.py")
    print("3. Start the Flask app: python app.py")
    print("4. Test API endpoints with curl or Postman")
    print("5. Integrate with your frontend application")

if __name__ == "__main__":
    asyncio.run(main())
