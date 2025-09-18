#!/usr/bin/env python3
"""
Advanced Resume Parser Demo
Demonstrates the key features of the AdvancedResumeParser
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from utils.advanced_resume_parser import AdvancedResumeParser

def demo_advanced_parser():
    """Demo the AdvancedResumeParser functionality"""
    
    print("🎯 ADVANCED RESUME PARSER DEMO")
    print("=" * 50)
    
    # Initialize parser
    parser = AdvancedResumeParser()
    
    # Sample resume content
    sample_resume = """
    MARCUS JOHNSON
    Software Engineer
    marcus.johnson@email.com | (404) 555-0123 | Atlanta, GA
    
    PROFESSIONAL SUMMARY
    Passionate software engineer with 4+ years of experience in full-stack development, 
    specializing in React, Node.js, and cloud technologies. Strong background in building 
    scalable applications and mentoring junior developers.
    
    WORK EXPERIENCE
    
    Senior Software Engineer
    TechFlow Solutions, Atlanta, GA
    March 2022 - Present
    • Led development of microservices architecture serving 500K+ users
    • Implemented CI/CD pipelines reducing deployment time by 50%
    • Mentored 2 junior developers and conducted code reviews
    • Technologies: React, Node.js, AWS, Docker, Kubernetes
    
    Software Engineer
    StartupHub, Atlanta, GA
    June 2020 - February 2022
    • Developed responsive web applications using React and Redux
    • Optimized database queries improving performance by 35%
    • Technologies: JavaScript, Python, PostgreSQL, Redis
    
    EDUCATION
    
    Bachelor of Science in Computer Science
    Georgia Institute of Technology, Atlanta, GA
    Graduated: May 2019
    GPA: 3.6/4.0
    
    SKILLS
    • Programming Languages: JavaScript, Python, Java, TypeScript, SQL
    • Frontend: React, Vue.js, HTML5, CSS3, Redux
    • Backend: Node.js, Express, Django, FastAPI
    • Databases: PostgreSQL, MongoDB, Redis
    • Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
    • Tools: Git, Jenkins, Jira, Confluence
    """
    
    # Create mock parsed data for demonstration
    mock_parsed_data = {
        'personal_info': {'full_name': 'MARCUS JOHNSON'},
        'contact_info': {'email': 'marcus.johnson@email.com'},
        'experience': [
            {
                'job_title': 'Senior Software Engineer',
                'company': 'TechFlow Solutions',
                'start_date': '2022-03',
                'end_date': 'Present',
                'description': 'Led development of microservices architecture serving 500K+ users. Implemented CI/CD pipelines reducing deployment time by 50%. Mentored 2 junior developers and conducted code reviews. Technologies: React, Node.js, AWS, Docker, Kubernetes'
            },
            {
                'job_title': 'Software Engineer',
                'company': 'StartupHub',
                'start_date': '2020-06',
                'end_date': '2022-02',
                'description': 'Developed responsive web applications using React and Redux. Optimized database queries improving performance by 35%. Technologies: JavaScript, Python, PostgreSQL, Redis'
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Computer Science',
                'university': 'Georgia Institute of Technology',
                'graduation_date': '2019-05'
            }
        ],
        'skills': [
            'JavaScript', 'Python', 'Java', 'TypeScript', 'SQL', 'React', 'Vue.js',
            'HTML5', 'CSS3', 'Redux', 'Node.js', 'Express', 'Django', 'FastAPI',
            'PostgreSQL', 'MongoDB', 'Redis', 'AWS', 'Docker', 'Kubernetes',
            'Git', 'Jenkins', 'Jira', 'Confluence'
        ],
        'summary': 'Passionate software engineer with 4+ years of experience in full-stack development, specializing in React, Node.js, and cloud technologies. Strong background in building scalable applications and mentoring junior developers.'
    }
    
    print("📄 Sample Resume: Marcus Johnson - Software Engineer")
    print("-" * 50)
    
    # Test career field classification
    print("\n🎯 Career Field Classification:")
    career_field = parser.classify_career_field(mock_parsed_data)
    print(f"   • Detected Field: {career_field.value}")
    
    # Test experience level detection
    print("\n📈 Experience Level Detection:")
    experience_level = parser.calculate_experience_level(mock_parsed_data)
    print(f"   • Experience Level: {experience_level.value}")
    
    # Test career trajectory analysis
    print("\n🚀 Career Trajectory Analysis:")
    trajectory = parser.analyze_career_trajectory(mock_parsed_data)
    print(f"   • Growth Pattern: {trajectory.growth_pattern}")
    print(f"   • Promotion Frequency: {trajectory.promotion_frequency:.2f}/year")
    print(f"   • Industry Consistency: {'Yes' if trajectory.industry_consistency else 'No'}")
    print(f"   • Leadership Development: {'Yes' if trajectory.leadership_development else 'No'}")
    
    # Test skills categorization
    print("\n🛠️ Skills Categorization:")
    skills_categorized = parser.categorize_skills(mock_parsed_data)
    for category, skills in skills_categorized.items():
        if skills:
            print(f"   • {category.value}: {len(skills)} skills")
            print(f"     {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")
    
    # Test leadership indicators
    print("\n👥 Leadership Indicators:")
    leadership = parser.extract_leadership_indicators(mock_parsed_data)
    print(f"   • Leadership Score: {leadership.leadership_score:.2f}")
    print(f"   • Management Keywords Found: {len([k for k in leadership.title_keywords if any(k in exp.get('job_title', '').lower() for exp in mock_parsed_data.get('experience', []))])}")
    
    # Test income potential calculation
    print("\n💰 Income Potential Calculation:")
    income = parser.calculate_income_potential(mock_parsed_data, "Atlanta")
    print(f"   • Estimated Current Salary: ${income.estimated_current_salary:,.0f}")
    print(f"   • Market Value Range: ${income.market_value_range[0]:,.0f} - ${income.market_value_range[1]:,.0f}")
    print(f"   • Growth Potential: {income.growth_potential:.2f}")
    print(f"   • Industry Multiplier: {income.industry_multiplier:.2f}")
    print(f"   • Location Multiplier: {income.location_multiplier:.2f}")
    print(f"   • Experience Multiplier: {income.experience_multiplier:.2f}")
    
    # Test full advanced parsing
    print("\n🔍 Full Advanced Parsing:")
    result = parser.parse_resume_advanced(sample_resume, "marcus_johnson.txt", "Atlanta")
    
    if result.get('success', False):
        print("   ✅ Advanced parsing successful!")
        advanced = result.get('advanced_analytics', {})
        print(f"   • Career Field: {advanced.get('career_field', 'N/A')}")
        print(f"   • Experience Level: {advanced.get('experience_level', 'N/A')}")
        
        income_data = advanced.get('income_potential', {})
        if income_data:
            print(f"   • Estimated Salary: ${income_data.get('estimated_current_salary', 0):,.0f}")
    else:
        print("   ❌ Advanced parsing failed")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed successfully!")
    print("The Advanced Resume Parser provides comprehensive analysis")
    print("for African American professionals in the target demographic.")

if __name__ == "__main__":
    demo_advanced_parser()
