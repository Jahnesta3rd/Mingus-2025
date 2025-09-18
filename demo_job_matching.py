#!/usr/bin/env python3
"""
Demo Script for Income-Focused Job Matching System
Showcases the key features and functionality of the IncomeBoostJobMatcher
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add backend utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'utils'))

from income_boost_job_matcher import (
    IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel,
    JobOpportunity, CompanyProfile, JobBoard
)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_job_summary(job, index=1):
    """Print a formatted job summary"""
    print(f"\n{index}. {job.title} at {job.company}")
    print(f"   Location: {job.location} ({job.msa})")
    print(f"   Salary: ${job.salary_median:,}" if job.salary_median else "   Salary: Not specified")
    print(f"   Increase Potential: {job.salary_increase_potential:.1%}")
    print(f"   Overall Score: {job.overall_score:.1f}/100")
    print(f"   Remote: {'Yes' if job.remote_friendly else 'No'}")
    print(f"   Field: {job.field.value.title()}")
    print(f"   Experience: {job.experience_level.value.title()}")
    print(f"   URL: {job.url}")

def print_company_summary(company):
    """Print a formatted company summary"""
    print(f"\nCompany: {company.name}")
    print(f"Industry: {company.industry}")
    print(f"Size: {company.size}")
    print(f"Diversity Score: {company.diversity_score:.1f}/100")
    print(f"Growth Score: {company.growth_score:.1f}/100")
    print(f"Culture Score: {company.culture_score:.1f}/100")
    print(f"Benefits Score: {company.benefits_score:.1f}/100")
    print(f"Glassdoor Rating: {company.glassdoor_rating}/5.0" if company.glassdoor_rating else "Glassdoor Rating: N/A")
    print(f"Remote Friendly: {'Yes' if company.remote_friendly else 'No'}")
    print(f"Headquarters: {company.headquarters}")

async def demo_basic_search():
    """Demo basic job search functionality"""
    print_header("DEMO: Basic Job Search")
    
    matcher = IncomeBoostJobMatcher()
    
    # Create search criteria for a mid-level technology professional
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,  # 25% increase
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA", "Houston-The Woodlands-Sugar Land, TX"],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False,
        min_company_rating=3.0
    )
    
    print("Search Criteria:")
    print(f"  Current Salary: ${criteria.current_salary:,}")
    print(f"  Target Increase: {criteria.target_salary_increase:.1%}")
    print(f"  Career Field: {criteria.career_field.value.title()}")
    print(f"  Experience Level: {criteria.experience_level.value.title()}")
    print(f"  Preferred MSAs: {', '.join(criteria.preferred_msas)}")
    print(f"  Remote OK: {criteria.remote_ok}")
    print(f"  Must Have Benefits: {', '.join(criteria.must_have_benefits)}")
    
    print("\nSearching for jobs...")
    
    # Note: In a real implementation, this would search actual job boards
    # For demo purposes, we'll create mock results
    mock_jobs = create_mock_jobs()
    
    print(f"\nFound {len(mock_jobs)} job opportunities!")
    
    # Show top 5 results
    for i, job in enumerate(mock_jobs[:5], 1):
        print_job_summary(job, i)
    
    return mock_jobs

def create_mock_jobs():
    """Create mock job data for demonstration"""
    mock_jobs = [
        JobOpportunity(
            job_id="mock_1",
            title="Senior Software Engineer",
            company="TechCorp Solutions",
            location="Atlanta, GA",
            msa="Atlanta-Sandy Springs-Alpharetta, GA",
            salary_min=95000,
            salary_max=125000,
            salary_median=110000,
            salary_increase_potential=0.47,  # 47% increase
            remote_friendly=True,
            job_board=JobBoard.INDEED,
            url="https://indeed.com/viewjob?jk=mock1",
            description="Senior software engineer role with growth opportunities",
            requirements=["Python", "JavaScript", "5+ years experience", "Leadership skills"],
            benefits=["Health insurance", "401k", "Dental", "Vision", "Unlimited PTO"],
            diversity_score=85.0,
            growth_score=90.0,
            culture_score=80.0,
            overall_score=88.5,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.SENIOR,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=15000,
            career_advancement_score=90.0,
            work_life_balance_score=85.0
        ),
        JobOpportunity(
            job_id="mock_2",
            title="Full Stack Developer",
            company="InnovateTech",
            location="Houston, TX",
            msa="Houston-The Woodlands-Sugar Land, TX",
            salary_min=85000,
            salary_max=115000,
            salary_median=100000,
            salary_increase_potential=0.33,  # 33% increase
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://linkedin.com/jobs/view/mock2",
            description="Full stack development with modern technologies",
            requirements=["React", "Node.js", "AWS", "3+ years experience"],
            benefits=["Health insurance", "401k", "Remote work", "Learning budget"],
            diversity_score=75.0,
            growth_score=85.0,
            culture_score=90.0,
            overall_score=82.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Startup",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=10000,
            career_advancement_score=85.0,
            work_life_balance_score=90.0
        ),
        JobOpportunity(
            job_id="mock_3",
            title="Software Development Manager",
            company="Enterprise Solutions Inc",
            location="Dallas, TX",
            msa="Dallas-Fort Worth-Arlington, TX",
            salary_min=120000,
            salary_max=160000,
            salary_median=140000,
            salary_increase_potential=0.87,  # 87% increase
            remote_friendly=False,
            job_board=JobBoard.GLASSDOOR,
            url="https://glassdoor.com/job-listing/mock3",
            description="Lead a team of software developers",
            requirements=["Management experience", "Python", "Agile", "7+ years experience"],
            benefits=["Health insurance", "401k", "Dental", "Vision", "PTO", "Stock options"],
            diversity_score=70.0,
            growth_score=95.0,
            culture_score=75.0,
            overall_score=85.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.EXECUTIVE,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Large",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=25000,
            career_advancement_score=95.0,
            work_life_balance_score=75.0
        ),
        JobOpportunity(
            job_id="mock_4",
            title="Data Scientist",
            company="Analytics Pro",
            location="Charlotte, NC",
            msa="Charlotte-Concord-Gastonia, NC-SC",
            salary_min=90000,
            salary_max=120000,
            salary_median=105000,
            salary_increase_potential=0.40,  # 40% increase
            remote_friendly=True,
            job_board=JobBoard.INDEED,
            url="https://indeed.com/viewjob?jk=mock4",
            description="Data science role with machine learning focus",
            requirements=["Python", "R", "Machine Learning", "Statistics", "4+ years experience"],
            benefits=["Health insurance", "401k", "Remote work", "Conference budget"],
            diversity_score=80.0,
            growth_score=85.0,
            culture_score=85.0,
            overall_score=84.0,
            field=CareerField.DATA_SCIENCE,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Analytics",
            equity_offered=False,
            bonus_potential=12000,
            career_advancement_score=85.0,
            work_life_balance_score=85.0
        ),
        JobOpportunity(
            job_id="mock_5",
            title="Product Manager",
            company="GrowthTech",
            location="Miami, FL",
            msa="Miami-Fort Lauderdale-Pompano Beach, FL",
            salary_min=100000,
            salary_max=140000,
            salary_median=120000,
            salary_increase_potential=0.60,  # 60% increase
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://linkedin.com/jobs/view/mock5",
            description="Product management for consumer applications",
            requirements=["Product management", "Agile", "Analytics", "5+ years experience"],
            benefits=["Health insurance", "401k", "Remote work", "Unlimited PTO", "Stock options"],
            diversity_score=90.0,
            growth_score=80.0,
            culture_score=95.0,
            overall_score=87.0,
            field=CareerField.PRODUCT_MANAGEMENT,
            experience_level=ExperienceLevel.SENIOR,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=20000,
            career_advancement_score=80.0,
            work_life_balance_score=95.0
        )
    ]
    
    return mock_jobs

async def demo_field_strategies():
    """Demo field-specific search strategies"""
    print_header("DEMO: Field-Specific Strategies")
    
    matcher = IncomeBoostJobMatcher()
    
    fields_to_demo = [
        CareerField.TECHNOLOGY,
        CareerField.FINANCE,
        CareerField.HEALTHCARE,
        CareerField.EDUCATION
    ]
    
    for field in fields_to_demo:
        print(f"\n{field.value.title()} Field Strategy:")
        strategies = matcher.field_specific_strategies(field)
        
        print(f"  Keywords: {', '.join(strategies['keywords'][:3])}...")
        print(f"  Salary Keywords: {', '.join(strategies['salary_keywords'][:3])}...")
        print(f"  Growth Keywords: {', '.join(strategies['growth_keywords'][:3])}...")
        print(f"  Benefits Keywords: {', '.join(strategies['benefits_keywords'][:3])}...")
        print(f"  Top Companies: {', '.join(strategies['companies'][:3])}...")

async def demo_company_assessment():
    """Demo company quality assessment"""
    print_header("DEMO: Company Quality Assessment")
    
    matcher = IncomeBoostJobMatcher()
    
    companies_to_assess = [
        "Google",
        "Microsoft",
        "Goldman Sachs",
        "Mayo Clinic",
        "Harvard University"
    ]
    
    for company_name in companies_to_assess:
        print(f"\nAssessing {company_name}...")
        
        # In a real implementation, this would fetch actual company data
        # For demo purposes, we'll create mock company profiles
        mock_profile = create_mock_company_profile(company_name)
        print_company_summary(mock_profile)

def create_mock_company_profile(company_name):
    """Create mock company profile for demonstration"""
    profiles = {
        "Google": CompanyProfile(
            company_id="comp_google",
            name="Google",
            industry="Technology",
            size="Large",
            diversity_score=85.0,
            growth_score=90.0,
            culture_score=88.0,
            benefits_score=92.0,
            leadership_diversity=70.0,
            employee_retention=88.0,
            glassdoor_rating=4.4,
            indeed_rating=4.2,
            remote_friendly=True,
            headquarters="Mountain View, CA",
            founded_year=1998,
            funding_stage="Public",
            revenue="100B+"
        ),
        "Microsoft": CompanyProfile(
            company_id="comp_microsoft",
            name="Microsoft",
            industry="Technology",
            size="Large",
            diversity_score=80.0,
            growth_score=85.0,
            culture_score=82.0,
            benefits_score=88.0,
            leadership_diversity=65.0,
            employee_retention=85.0,
            glassdoor_rating=4.3,
            indeed_rating=4.1,
            remote_friendly=True,
            headquarters="Redmond, WA",
            founded_year=1975,
            funding_stage="Public",
            revenue="100B+"
        ),
        "Goldman Sachs": CompanyProfile(
            company_id="comp_goldman",
            name="Goldman Sachs",
            industry="Finance",
            size="Large",
            diversity_score=60.0,
            growth_score=75.0,
            culture_score=70.0,
            benefits_score=85.0,
            leadership_diversity=45.0,
            employee_retention=80.0,
            glassdoor_rating=3.8,
            indeed_rating=3.9,
            remote_friendly=False,
            headquarters="New York, NY",
            founded_year=1869,
            funding_stage="Public",
            revenue="50B+"
        ),
        "Mayo Clinic": CompanyProfile(
            company_id="comp_mayo",
            name="Mayo Clinic",
            industry="Healthcare",
            size="Large",
            diversity_score=75.0,
            growth_score=70.0,
            culture_score=85.0,
            benefits_score=90.0,
            leadership_diversity=60.0,
            employee_retention=90.0,
            glassdoor_rating=4.1,
            indeed_rating=4.0,
            remote_friendly=False,
            headquarters="Rochester, MN",
            founded_year=1889,
            funding_stage="Non-profit",
            revenue="10B+"
        ),
        "Harvard University": CompanyProfile(
            company_id="comp_harvard",
            name="Harvard University",
            industry="Education",
            size="Large",
            diversity_score=70.0,
            growth_score=65.0,
            culture_score=90.0,
            benefits_score=85.0,
            leadership_diversity=55.0,
            employee_retention=95.0,
            glassdoor_rating=4.2,
            indeed_rating=4.1,
            remote_friendly=False,
            headquarters="Cambridge, MA",
            founded_year=1636,
            funding_stage="Non-profit",
            revenue="5B+"
        )
    }
    
    return profiles.get(company_name, CompanyProfile(
        company_id=f"comp_{company_name.lower().replace(' ', '_')}",
        name=company_name,
        industry="Unknown",
        size="Unknown",
        diversity_score=50.0,
        growth_score=50.0,
        culture_score=50.0,
        benefits_score=50.0,
        leadership_diversity=50.0,
        employee_retention=50.0,
        glassdoor_rating=None,
        indeed_rating=None,
        remote_friendly=False,
        headquarters="Unknown",
        founded_year=None,
        funding_stage=None,
        revenue=None
    ))

async def demo_msa_targeting():
    """Demo MSA targeting functionality"""
    print_header("DEMO: MSA Targeting")
    
    matcher = IncomeBoostJobMatcher()
    
    # Create mock jobs from different MSAs
    mock_jobs = create_mock_jobs()
    
    print("Before MSA targeting:")
    for job in mock_jobs[:3]:
        print(f"  {job.title} at {job.company} - {job.msa} (Score: {job.overall_score:.1f})")
    
    # Apply MSA targeting
    preferred_msas = ["Atlanta-Sandy Springs-Alpharetta, GA", "Houston-The Woodlands-Sugar Land, TX"]
    targeted_jobs = matcher.msa_targeting(mock_jobs, preferred_msas)
    
    print(f"\nAfter MSA targeting (preferred: {', '.join(preferred_msas)}):")
    for job in targeted_jobs[:3]:
        print(f"  {job.title} at {job.company} - {job.msa} (Score: {job.overall_score:.1f})")

async def demo_remote_detection():
    """Demo remote opportunity detection"""
    print_header("DEMO: Remote Opportunity Detection")
    
    matcher = IncomeBoostJobMatcher()
    
    # Create mock jobs with different remote characteristics
    mock_jobs = create_mock_jobs()
    
    print("Before remote detection:")
    for job in mock_jobs[:3]:
        print(f"  {job.title} at {job.company} - Remote: {job.remote_friendly} (Score: {job.overall_score:.1f})")
    
    # Apply remote detection
    remote_jobs = matcher.remote_opportunity_detection(mock_jobs)
    
    print(f"\nAfter remote detection:")
    for job in remote_jobs[:3]:
        print(f"  {job.title} at {job.company} - Remote: {job.remote_friendly} (Score: {job.overall_score:.1f})")
    
    remote_count = sum(1 for job in remote_jobs if job.remote_friendly)
    print(f"\nTotal remote opportunities: {remote_count}/{len(remote_jobs)}")

async def demo_scoring_system():
    """Demo the multi-dimensional scoring system"""
    print_header("DEMO: Multi-Dimensional Scoring System")
    
    matcher = IncomeBoostJobMatcher()
    
    # Create a test job
    test_job = JobOpportunity(
        job_id="test_scoring",
        title="Senior Software Engineer",
        company="Test Company",
        location="Atlanta, GA",
        msa="Atlanta-Sandy Springs-Alpharetta, GA",
        salary_min=95000,
        salary_max=125000,
        salary_median=110000,
        salary_increase_potential=0.0,
        remote_friendly=True,
        job_board=JobBoard.INDEED,
        url="https://test.com/job",
        description="Senior role with growth opportunities and flexible work",
        requirements=["Python", "Leadership", "5+ years"],
        benefits=["Health insurance", "401k", "Dental", "Unlimited PTO"],
        diversity_score=0.0,
        growth_score=0.0,
        culture_score=0.0,
        overall_score=0.0,
        field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.SENIOR,
        posted_date=datetime.now(),
        application_deadline=None,
        company_size="Mid",
        company_industry="Technology",
        equity_offered=True,
        bonus_potential=15000,
        career_advancement_score=0.0,
        work_life_balance_score=0.0
    )
    
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False,
        min_company_rating=3.0
    )
    
    print("Scoring job with criteria:")
    print(f"  Current Salary: ${criteria.current_salary:,}")
    print(f"  Target Increase: {criteria.target_salary_increase:.1%}")
    print(f"  Career Field: {criteria.career_field.value.title()}")
    
    # Score the job
    scored_job = matcher.multi_dimensional_scoring(test_job, criteria)
    
    print(f"\nScoring Results:")
    print(f"  Salary Increase Potential: {scored_job.salary_increase_potential:.1%}")
    print(f"  Salary Score: {matcher._calculate_salary_score(scored_job, criteria):.1f}/100")
    print(f"  Advancement Score: {scored_job.career_advancement_score:.1f}/100")
    print(f"  Diversity Score: {scored_job.diversity_score:.1f}/100")
    print(f"  Benefits Score: {scored_job.work_life_balance_score:.1f}/100")
    print(f"  Overall Score: {scored_job.overall_score:.1f}/100")
    
    print(f"\nScore Breakdown:")
    print(f"  Salary (40%): {matcher._calculate_salary_score(scored_job, criteria) * 0.40:.1f}")
    print(f"  Advancement (25%): {scored_job.career_advancement_score * 0.25:.1f}")
    print(f"  Diversity (20%): {scored_job.diversity_score * 0.20:.1f}")
    print(f"  Benefits (15%): {scored_job.work_life_balance_score * 0.15:.1f}")

async def main():
    """Main demo function"""
    print_header("INCOME-FOCUSED JOB MATCHING SYSTEM DEMO")
    print("This demo showcases the key features of the IncomeBoostJobMatcher system")
    print("designed to prioritize salary improvement opportunities for African American professionals.")
    
    try:
        # Run all demos
        await demo_basic_search()
        await demo_field_strategies()
        await demo_company_assessment()
        await demo_msa_targeting()
        await demo_remote_detection()
        await demo_scoring_system()
        
        print_header("DEMO COMPLETE")
        print("The IncomeBoostJobMatcher system provides comprehensive job matching")
        print("with a focus on salary improvement, career advancement, and diversity.")
        print("\nKey Features Demonstrated:")
        print("✓ Salary-focused search (15-45% increases)")
        print("✓ Multi-dimensional scoring system")
        print("✓ Field-specific search strategies")
        print("✓ Company quality assessment")
        print("✓ MSA targeting for top metro areas")
        print("✓ Remote opportunity detection")
        print("✓ Comprehensive job and company data")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        print("This is expected in a demo environment without actual API keys.")

if __name__ == "__main__":
    asyncio.run(main())
