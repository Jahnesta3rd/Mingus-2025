#!/usr/bin/env python3
"""
Resume Parser Demo
Demonstrates the advanced resume parser functionality with sample resumes
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.models.resume_parser import AdvancedResumeParser

def demo_data_analyst_resume():
    """Demo with a data analyst resume"""
    print("=" * 60)
    print("DEMO: Data Analyst Resume")
    print("=" * 60)
    
    resume_text = """
    SARAH JOHNSON
    Senior Data Analyst
    
    EXPERIENCE
    Senior Data Analyst | TechCorp | 2020-2023
    - Led data analysis projects using SQL, Python, and Tableau
    - Managed team of 3 junior analysts and mentored new hires
    - Developed predictive models for business intelligence
    - Coordinated with stakeholders across marketing, sales, and product teams
    - Improved data accuracy by 25% through automated validation processes
    
    Data Analyst | DataCorp | 2018-2020
    - Analyzed customer data using Excel, SQL, and basic Python
    - Created reports and dashboards for executive presentations
    - Collaborated with marketing team on campaign performance analysis
    - Reduced reporting time by 40% through automation
    
    SKILLS
    Technical: SQL, Python, R, Tableau, Power BI, Excel, Machine Learning, Statistics
    Business: Project Management, Stakeholder Management, Business Analysis, Data Strategy
    Soft: Leadership, Communication, Problem Solving, Teamwork, Mentoring
    
    EDUCATION
    Master's in Statistics | University of Data Science | 2018
    Bachelor's in Mathematics | State University | 2016
    """
    
    return resume_text

def demo_software_developer_resume():
    """Demo with a software developer resume"""
    print("=" * 60)
    print("DEMO: Software Developer Resume")
    print("=" * 60)
    
    resume_text = """
    MICHAEL CHEN
    Senior Software Engineer
    
    EXPERIENCE
    Senior Software Engineer | TechStartup | 2021-2023
    - Led development of React.js applications with Node.js backend
    - Managed team of 4 developers using Agile methodology and Scrum
    - Implemented CI/CD pipelines with Docker, AWS, and Jenkins
    - Mentored junior developers and conducted code reviews
    - Reduced application load time by 40% through optimization
    
    Software Engineer | BigTech | 2019-2021
    - Developed Java applications and REST APIs using Spring Boot
    - Worked with microservices architecture and cloud deployment
    - Used Git for version control and collaborated with cross-functional teams
    - Implemented automated testing with JUnit and Mockito
    
    Junior Developer | StartupCorp | 2018-2019
    - Built web applications using JavaScript and Python
    - Learned modern development practices and tools
    - Contributed to team projects and code reviews
    
    SKILLS
    Programming: Java, JavaScript, Python, React, Node.js, Spring Boot
    Tools: Git, Docker, AWS, Jenkins, JUnit, Mockito, VS Code
    Methodologies: Agile, Scrum, TDD, DevOps, Microservices
    
    EDUCATION
    Computer Science Degree | Tech University | 2018
    """
    
    return resume_text

def demo_project_manager_resume():
    """Demo with a project manager resume"""
    print("=" * 60)
    print("DEMO: Project Manager Resume")
    print("=" * 60)
    
    resume_text = """
    LISA RODRIGUEZ
    Senior Project Manager
    
    EXPERIENCE
    Senior Project Manager | GlobalCorp | 2020-2023
    - Led cross-functional teams of 15+ members across multiple projects
    - Managed $2M+ project budgets and delivered on time and under budget
    - Implemented Agile and Scrum methodologies across the organization
    - Coordinated with stakeholders at all levels including C-suite executives
    - Improved project delivery efficiency by 30% through process optimization
    
    Project Manager | MidSizeCorp | 2018-2020
    - Managed software development projects using Waterfall and Agile
    - Led teams of 8-10 developers, designers, and QA engineers
    - Created project plans, timelines, and risk mitigation strategies
    - Facilitated stakeholder meetings and status reporting
    
    Project Coordinator | SmallCorp | 2016-2018
    - Assisted project managers with documentation and scheduling
    - Coordinated team meetings and tracked project milestones
    - Learned project management fundamentals and tools
    
    SKILLS
    Project Management: PMP, Agile, Scrum, Kanban, Waterfall, Risk Management
    Tools: Jira, Confluence, Microsoft Project, Slack, Trello
    Business: Stakeholder Management, Budget Management, Team Leadership, Strategic Planning
    Soft: Communication, Leadership, Problem Solving, Negotiation, Conflict Resolution
    
    EDUCATION
    MBA in Project Management | Business University | 2016
    Bachelor's in Business Administration | State University | 2014
    PMP Certification | Project Management Institute | 2019
    """
    
    return resume_text

def demo_marketing_resume():
    """Demo with a marketing resume"""
    print("=" * 60)
    print("DEMO: Marketing Professional Resume")
    print("=" * 60)
    
    resume_text = """
    DAVID THOMPSON
    Marketing Manager
    
    EXPERIENCE
    Marketing Manager | ConsumerBrand | 2021-2023
    - Led digital marketing campaigns across social media, email, and paid advertising
    - Managed team of 5 marketing specialists and creative professionals
    - Increased brand awareness by 45% through strategic campaign execution
    - Optimized marketing spend resulting in 30% improvement in ROI
    - Collaborated with product and sales teams on go-to-market strategies
    
    Marketing Specialist | EcommerceCorp | 2019-2021
    - Executed email marketing campaigns and social media content
    - Analyzed campaign performance using Google Analytics and marketing tools
    - Created content for website, blog, and social media platforms
    - Assisted with SEO optimization and content marketing strategies
    
    Marketing Intern | StartupCorp | 2018-2019
    - Supported marketing team with content creation and campaign assistance
    - Learned digital marketing tools and analytics platforms
    - Contributed to social media management and community engagement
    
    SKILLS
    Digital Marketing: Social Media Marketing, Email Marketing, SEO, SEM, Google Analytics
    Tools: HubSpot, Mailchimp, Hootsuite, Canva, Google Ads, Facebook Ads
    Content: Content Creation, Copywriting, Brand Management, Campaign Strategy
    Analytics: Data Analysis, Performance Tracking, A/B Testing, ROI Optimization
    Soft: Creativity, Communication, Strategic Thinking, Team Collaboration
    
    EDUCATION
    Bachelor's in Marketing | Marketing University | 2019
    Google Analytics Certification | Google | 2020
    HubSpot Marketing Certification | HubSpot | 2021
    """
    
    return resume_text

def analyze_resume(parser: AdvancedResumeParser, resume_text: str, title: str):
    """Analyze a resume and display results"""
    try:
        print(f"\nAnalyzing {title}...")
        print("-" * 40)
        
        # Parse resume
        analysis = parser.parse_resume(resume_text)
        
        # Get summary
        summary = parser.get_analysis_summary(analysis)
        
        # Display results
        print(f"Primary Field: {summary['primary_field']}")
        if summary['secondary_field']:
            print(f"Secondary Field: {summary['secondary_field']}")
        
        print(f"Experience Level: {summary['experience_level']}")
        print(f"Total Experience: {summary['total_experience_years']:.1f} years")
        print(f"Leadership Potential: {summary['leadership_potential']:.2f}")
        print(f"Technical/Business Ratio: {summary['technical_business_ratio']:.2f}")
        print(f"Growth Potential: {summary['growth_potential']:.2f}")
        print(f"Advancement Readiness: {summary['advancement_readiness']:.2f}")
        
        print(f"\nNext Career Steps:")
        for step in summary['next_career_steps']:
            print(f"  - {step}")
        
        print(f"\nTransferable Skills:")
        for skill in summary['transferable_skills'][:5]:  # Show top 5
            print(f"  - {skill}")
        
        print(f"\nIndustry Experience:")
        for industry in summary['industry_experience']:
            print(f"  - {industry}")
        
        # Display detailed analysis
        print(f"\nDetailed Analysis:")
        print(f"  Field Keywords: {', '.join(analysis.field_analysis.field_keywords[:5])}")
        print(f"  Leadership Indicators: {', '.join(analysis.experience_analysis.leadership_indicators[:3])}")
        print(f"  Career Progression: {', '.join(analysis.career_trajectory.career_progression[:2])}")
        
        # Skills breakdown
        tech_skills = list(analysis.skills_analysis.technical_skills.keys())[:3]
        business_skills = list(analysis.skills_analysis.business_skills.keys())[:3]
        soft_skills = list(analysis.skills_analysis.soft_skills.keys())[:3]
        
        print(f"\nSkills Breakdown:")
        print(f"  Technical: {', '.join(tech_skills)}")
        print(f"  Business: {', '.join(business_skills)}")
        print(f"  Soft: {', '.join(soft_skills)}")
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing resume: {str(e)}")
        return None

def main():
    """Main demo function"""
    print("Advanced Resume Parser Demo")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize parser
    try:
        parser = AdvancedResumeParser()
        print("✓ Resume parser initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing parser: {str(e)}")
        return
    
    # Demo resumes
    demos = [
        ("Data Analyst", demo_data_analyst_resume()),
        ("Software Developer", demo_software_developer_resume()),
        ("Project Manager", demo_project_manager_resume()),
        ("Marketing Professional", demo_marketing_resume())
    ]
    
    results = []
    
    for title, resume_text in demos:
        analysis = analyze_resume(parser, resume_text, title)
        if analysis:
            results.append((title, analysis))
        print("\n" + "=" * 60 + "\n")
    
    # Summary comparison
    print("SUMMARY COMPARISON")
    print("=" * 60)
    print(f"{'Role':<20} {'Field':<15} {'Level':<10} {'Leadership':<12} {'Growth':<8}")
    print("-" * 60)
    
    for title, analysis in results:
        summary = parser.get_analysis_summary(analysis)
        print(f"{title:<20} {summary['primary_field']:<15} {summary['experience_level']:<10} "
              f"{summary['leadership_potential']:<12.2f} {summary['growth_potential']:<8.2f}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main() 