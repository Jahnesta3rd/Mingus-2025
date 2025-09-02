#!/usr/bin/env python3
"""
Test script for the Job Risk Calculator system.
Demonstrates various job profiles and A/B testing capabilities.
"""

import json
import logging
from datetime import datetime
from src.services.JobRiskCalculator import JobRiskCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_high_risk_jobs():
    """Test high-risk job profiles."""
    print("\n" + "="*60)
    print("TESTING HIGH-RISK JOB PROFILES")
    print("="*60)
    
    calculator = JobRiskCalculator("v1.0")
    
    high_risk_profiles = [
        {
            "job_info": {"title": "data entry clerk", "industry": "technology", "experience": 2},
            "daily_tasks": {"data_entry": True, "customer_service": False, "content_creation": False, "analysis": False, "coding": False, "design": False, "management": False, "research": False},
            "work_environment": {"remote_work": "full", "ai_usage": "extensive", "team_size": "small"},
            "skills_and_concerns": {"tech_skills": [], "ai_concerns": {"job_loss": True, "skill_gap": True, "privacy": False, "bias": False, "overreliance": False}},
            "contact_info": {"name": "John Doe", "email": "john@example.com", "location": "San Francisco"}
        },
        {
            "job_info": {"title": "translator", "industry": "media", "experience": 5},
            "daily_tasks": {"data_entry": False, "customer_service": False, "content_creation": True, "analysis": False, "coding": False, "design": False, "management": False, "research": False},
            "work_environment": {"remote_work": "full", "ai_usage": "moderate", "team_size": "solo"},
            "skills_and_concerns": {"tech_skills": ["translation_tools"], "ai_concerns": {"job_loss": True, "skill_gap": False, "privacy": True, "bias": False, "overreliance": True}},
            "contact_info": {"name": "Maria Garcia", "email": "maria@example.com", "location": "New York"}
        },
        {
            "job_info": {"title": "software developer", "industry": "technology", "experience": 3},
            "daily_tasks": {"data_entry": False, "customer_service": False, "content_creation": False, "analysis": True, "coding": True, "design": False, "management": False, "research": False},
            "work_environment": {"remote_work": "hybrid", "ai_usage": "extensive", "team_size": "medium"},
            "skills_and_concerns": {"tech_skills": ["python", "javascript", "git", "docker"], "ai_concerns": {"job_loss": False, "skill_gap": True, "privacy": False, "bias": True, "overreliance": False}},
            "contact_info": {"name": "Alex Chen", "email": "alex@example.com", "location": "Seattle"}
        }
    ]
    
    for i, profile in enumerate(high_risk_profiles, 1):
        print(f"\n--- High Risk Profile {i} ---")
        result = calculator.calculate_job_risk(profile)
        print(f"Job Title: {result.job_title}")
        print(f"Automation Risk: {result.final_automation_risk:.1f}%")
        print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
        print(f"Overall Risk Score: {result.overall_risk_score:.1f}%")
        print(f"Risk Level: {result.risk_level.value}")
        print(f"Timeframe: {result.timeframe.value}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Recommendations: {len(result.recommendations)}")
        print(f"Insights: {len(result.insights)}")

def test_medium_risk_jobs():
    """Test medium-risk job profiles."""
    print("\n" + "="*60)
    print("TESTING MEDIUM-RISK JOB PROFILES")
    print("="*60)
    
    calculator = JobRiskCalculator("v1.0")
    
    medium_risk_profiles = [
        {
            "job_info": {"title": "marketing manager", "industry": "marketing", "experience": 7},
            "daily_tasks": {"data_entry": False, "customer_service": False, "content_creation": True, "analysis": True, "coding": False, "design": False, "management": True, "research": True},
            "work_environment": {"remote_work": "hybrid", "ai_usage": "moderate", "team_size": "medium"},
            "skills_and_concerns": {"tech_skills": ["google_analytics", "hubspot", "canva"], "ai_concerns": {"job_loss": False, "skill_gap": True, "privacy": False, "bias": False, "overreliance": True}},
            "contact_info": {"name": "Sarah Johnson", "email": "sarah@example.com", "location": "Chicago"}
        },
        {
            "job_info": {"title": "financial analyst", "industry": "finance", "experience": 4},
            "daily_tasks": {"data_entry": True, "customer_service": False, "content_creation": False, "analysis": True, "coding": False, "design": False, "management": False, "research": True},
            "work_environment": {"remote_work": "full", "ai_usage": "extensive", "team_size": "large"},
            "skills_and_concerns": {"tech_skills": ["excel", "python", "sql", "tableau"], "ai_concerns": {"job_loss": True, "skill_gap": True, "privacy": True, "bias": False, "overreliance": False}},
            "contact_info": {"name": "David Kim", "email": "david@example.com", "location": "Boston"}
        }
    ]
    
    for i, profile in enumerate(medium_risk_profiles, 1):
        print(f"\n--- Medium Risk Profile {i} ---")
        result = calculator.calculate_job_risk(profile)
        print(f"Job Title: {result.job_title}")
        print(f"Automation Risk: {result.final_automation_risk:.1f}%")
        print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
        print(f"Overall Risk Score: {result.overall_risk_score:.1f}%")
        print(f"Risk Level: {result.risk_level.value}")
        print(f"Timeframe: {result.timeframe.value}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Recommendations: {len(result.recommendations)}")
        print(f"Insights: {len(result.insights)}")

def test_low_risk_jobs():
    """Test low-risk job profiles."""
    print("\n" + "="*60)
    print("TESTING LOW-RISK JOB PROFILES")
    print("="*60)
    
    calculator = JobRiskCalculator("v1.0")
    
    low_risk_profiles = [
        {
            "job_info": {"title": "teacher", "industry": "education", "experience": 10},
            "daily_tasks": {"data_entry": False, "customer_service": True, "content_creation": True, "analysis": False, "coding": False, "design": False, "management": False, "research": True},
            "work_environment": {"remote_work": "none", "ai_usage": "minimal", "team_size": "small"},
            "skills_and_concerns": {"tech_skills": ["google_classroom", "zoom"], "ai_concerns": {"job_loss": False, "skill_gap": False, "privacy": True, "bias": True, "overreliance": False}},
            "contact_info": {"name": "Lisa Thompson", "email": "lisa@example.com", "location": "Austin"}
        },
        {
            "job_info": {"title": "therapist", "industry": "healthcare", "experience": 8},
            "daily_tasks": {"data_entry": False, "customer_service": True, "content_creation": False, "analysis": False, "coding": False, "design": False, "management": False, "research": False},
            "work_environment": {"remote_work": "hybrid", "ai_usage": "none", "team_size": "solo"},
            "skills_and_concerns": {"tech_skills": ["teletherapy_platforms"], "ai_concerns": {"job_loss": False, "skill_gap": False, "privacy": True, "bias": True, "overreliance": False}},
            "contact_info": {"name": "Dr. Michael Brown", "email": "michael@example.com", "location": "Denver"}
        },
        {
            "job_info": {"title": "consultant", "industry": "consulting", "experience": 12},
            "daily_tasks": {"data_entry": False, "customer_service": False, "content_creation": True, "analysis": True, "coding": False, "design": False, "management": True, "research": True},
            "work_environment": {"remote_work": "hybrid", "ai_usage": "moderate", "team_size": "medium"},
            "skills_and_concerns": {"tech_skills": ["powerpoint", "excel", "salesforce"], "ai_concerns": {"job_loss": False, "skill_gap": False, "privacy": False, "bias": False, "overreliance": False}},
            "contact_info": {"name": "Jennifer Lee", "email": "jennifer@example.com", "location": "Washington DC"}
        }
    ]
    
    for i, profile in enumerate(low_risk_profiles, 1):
        print(f"\n--- Low Risk Profile {i} ---")
        result = calculator.calculate_job_risk(profile)
        print(f"Job Title: {result.job_title}")
        print(f"Automation Risk: {result.final_automation_risk:.1f}%")
        print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
        print(f"Overall Risk Score: {result.overall_risk_score:.1f}%")
        print(f"Risk Level: {result.risk_level.value}")
        print(f"Timeframe: {result.timeframe.value}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Recommendations: {len(result.recommendations)}")
        print(f"Insights: {len(result.insights)}")

def test_ab_testing():
    """Test A/B testing with different algorithm versions."""
    print("\n" + "="*60)
    print("A/B TESTING DIFFERENT ALGORITHM VERSIONS")
    print("="*60)
    
    # Test profile
    test_profile = {
        "job_info": {"title": "data analyst", "industry": "technology", "experience": 5},
        "daily_tasks": {"data_entry": True, "customer_service": False, "content_creation": False, "analysis": True, "coding": False, "design": False, "management": False, "research": True},
        "work_environment": {"remote_work": "full", "ai_usage": "extensive", "team_size": "large"},
        "skills_and_concerns": {"tech_skills": ["python", "sql", "excel", "tableau"], "ai_concerns": {"job_loss": True, "skill_gap": True, "privacy": False, "bias": False, "overreliance": True}},
        "contact_info": {"name": "Test User", "email": "test@example.com", "location": "Test City"}
    }
    
    # Test different algorithm versions
    versions = ["v1.0", "v1.1", "v2.0"]
    
    for version in versions:
        print(f"\n--- Algorithm Version {version} ---")
        calculator = JobRiskCalculator(version)
        result = calculator.calculate_job_risk(test_profile)
        
        print(f"Automation Risk: {result.final_automation_risk:.1f}%")
        print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
        print(f"Overall Risk Score: {result.overall_risk_score:.1f}%")
        print(f"Risk Level: {result.risk_level.value}")
        print(f"Timeframe: {result.timeframe.value}")
        print(f"Confidence: {result.confidence:.1f}%")
        
        # Export calculation log for analysis
        log = calculator.export_calculation_log(result, test_profile)
        print(f"Calculation Log: {json.dumps(log, indent=2)}")

def test_fuzzy_matching():
    """Test fuzzy string matching for job titles."""
    print("\n" + "="*60)
    print("TESTING FUZZY STRING MATCHING")
    print("="*60)
    
    calculator = JobRiskCalculator("v1.0")
    
    test_titles = [
        "software engineer",
        "data entry specialist",
        "marketing coordinator",
        "financial advisor",
        "customer success manager",
        "product designer",
        "business development manager",
        "human resources coordinator",
        "sales executive",
        "content strategist"
    ]
    
    for title in test_titles:
        matched_title, similarity = calculator.find_best_job_match(title)
        print(f"'{title}' -> '{matched_title}' (similarity: {similarity:.1f}%)")

def test_recommendation_generation():
    """Test recommendation generation for different risk levels."""
    print("\n" + "="*60)
    print("TESTING RECOMMENDATION GENERATION")
    print("="*60)
    
    calculator = JobRiskCalculator("v1.0")
    
    # Test profiles for each risk level
    test_profiles = {
        "high_risk": {
            "job_info": {"title": "data entry clerk", "industry": "technology", "experience": 1},
            "daily_tasks": {"data_entry": True, "customer_service": False, "content_creation": False, "analysis": False, "coding": False, "design": False, "management": False, "research": False},
            "work_environment": {"remote_work": "full", "ai_usage": "none", "team_size": "solo"},
            "skills_and_concerns": {"tech_skills": [], "ai_concerns": {"job_loss": True, "skill_gap": True, "privacy": False, "bias": False, "overreliance": False}},
            "contact_info": {"name": "High Risk User", "email": "high@example.com", "location": "Test City"}
        },
        "medium_risk": {
            "job_info": {"title": "marketing manager", "industry": "marketing", "experience": 5},
            "daily_tasks": {"data_entry": False, "customer_service": False, "content_creation": True, "analysis": True, "coding": False, "design": False, "management": True, "research": True},
            "work_environment": {"remote_work": "hybrid", "ai_usage": "moderate", "team_size": "medium"},
            "skills_and_concerns": {"tech_skills": ["google_analytics", "hubspot"], "ai_concerns": {"job_loss": False, "skill_gap": True, "privacy": False, "bias": False, "overreliance": True}},
            "contact_info": {"name": "Medium Risk User", "email": "medium@example.com", "location": "Test City"}
        },
        "low_risk": {
            "job_info": {"title": "teacher", "industry": "education", "experience": 10},
            "daily_tasks": {"data_entry": False, "customer_service": True, "content_creation": True, "analysis": False, "coding": False, "design": False, "management": False, "research": True},
            "work_environment": {"remote_work": "none", "ai_usage": "minimal", "team_size": "small"},
            "skills_and_concerns": {"tech_skills": ["google_classroom"], "ai_concerns": {"job_loss": False, "skill_gap": False, "privacy": True, "bias": True, "overreliance": False}},
            "contact_info": {"name": "Low Risk User", "email": "low@example.com", "location": "Test City"}
        }
    }
    
    for risk_level, profile in test_profiles.items():
        print(f"\n--- {risk_level.upper()} RISK RECOMMENDATIONS ---")
        result = calculator.calculate_job_risk(profile)
        
        print(f"Risk Level: {result.risk_level.value}")
        print(f"Automation Risk: {result.final_automation_risk:.1f}%")
        print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
        
        print("\nRecommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec['title']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Category: {rec['category']}")
            print(f"   Impact: {rec['estimated_impact']}%")
            print(f"   Timeframe: {rec['timeframe']}")
            print(f"   Description: {rec['description']}")
            print()
        
        print("Insights:")
        for insight in result.insights:
            print(f"• {insight}")
        print()

def main():
    """Run all tests."""
    print("JOB RISK CALCULATOR TEST SUITE")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_high_risk_jobs()
        test_medium_risk_jobs()
        test_low_risk_jobs()
        test_fuzzy_matching()
        test_recommendation_generation()
        test_ab_testing()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
