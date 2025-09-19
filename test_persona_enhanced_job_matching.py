#!/usr/bin/env python3
"""
Enhanced Job Matching System - Persona Testing
Demonstrates the Job Description to Problem Statement Analysis Methodology
using the three Mingus personas: Maya Johnson, Marcus Thompson, and Dr. Jasmine Williams
"""

import json
import time
from datetime import datetime
import asyncio

# Import the enhanced components
from backend.utils.job_problem_extractor import JobProblemExtractor, IndustryContext, CompanyStage
from backend.utils.problem_solution_mapper import ProblemSolutionMapper
from backend.utils.enhanced_job_matching_engine import EnhancedJobMatchingEngine

def create_persona_profiles():
    """Create detailed profiles for each persona"""
    return {
        "maya_johnson": {
            "name": "Maya Johnson",
            "tier": "Budget ($15/month)",
            "location": "Atlanta, GA",
            "current_salary": 45000,
            "career_field": "MARKETING",
            "experience_level": "MID",
            "skills": [
                "Google Analytics", "Google Ads", "Facebook Ads Manager",
                "HubSpot", "Mailchimp", "Hootsuite", "Buffer",
                "Adobe Creative Suite", "Excel", "PowerPoint",
                "WordPress", "HTML/CSS", "Canva", "Figma",
                "Social Media Strategy", "Email Marketing", "Content Creation",
                "Event Planning", "Market Research", "SEO/SEM", "Brand Management"
            ],
            "certifications": [
                "Google Analytics Certified (2023)",
                "HubSpot Content Marketing Certification (2023)",
                "Facebook Blueprint Certification (2022)",
                "Google Ads Search Certification (2022)"
            ],
            "experience_years": 2.5,
            "education": "Bachelor of Arts in Communications",
            "target_salary": 60000,
            "career_goals": "Senior Marketing Coordinator or Marketing Specialist",
            "industries": ["Healthcare", "Technology", "Consumer Goods"]
        },
        
        "marcus_thompson": {
            "name": "Marcus Thompson",
            "tier": "Mid-tier ($35/month)",
            "location": "Houston, TX",
            "current_salary": 72000,
            "career_field": "TECHNOLOGY",
            "experience_level": "MID",
            "skills": [
                "JavaScript", "TypeScript", "Python", "Java", "SQL",
                "React.js", "Next.js", "Vue.js", "Angular",
                "Node.js", "Express.js", "RESTful APIs", "GraphQL",
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "DynamoDB",
                "AWS", "Docker", "Kubernetes", "CI/CD Pipelines",
                "Git/GitHub", "JIRA", "Jest", "Cypress"
            ],
            "certifications": [
                "AWS Certified Solutions Architect - Associate (2023)",
                "AWS Certified Developer - Associate (2022)",
                "MongoDB Certified Developer (2022)",
                "Certified Scrum Master (CSM) - In Progress"
            ],
            "experience_years": 3,
            "education": "Bachelor of Science in Computer Science",
            "target_salary": 90000,
            "career_goals": "Senior Software Developer or Full-Stack Engineer",
            "industries": ["Fintech", "Healthtech", "SaaS"]
        },
        
        "dr_jasmine_williams": {
            "name": "Dr. Jasmine Williams",
            "tier": "Professional ($100/month)",
            "location": "Alexandria, VA",
            "current_salary": 89000,
            "career_field": "GOVERNMENT",
            "experience_level": "SENIOR",
            "skills": [
                "Strategic Planning", "Program Development", "Team Leadership",
                "Stakeholder Management", "Change Management", "Performance Management",
                "Public Policy Analysis", "Regulatory Compliance", "Data Analysis",
                "Grant Management", "Federal Contracting", "Legislative Research",
                "Project Management", "Excel", "PowerBI", "Tableau",
                "Public Speaking", "Grant Writing", "Interagency Collaboration"
            ],
            "certifications": [
                "Project Management Professional (PMP) - 2020",
                "Certified Government Financial Manager (CGFM) - 2019",
                "Federal Acquisition Certification - Program/Project Manager (FAC-P/PM) Level II - 2021"
            ],
            "experience_years": 8,
            "education": "Master of Public Administration",
            "target_salary": 150000,
            "career_goals": "Senior Executive Service (SES) or Executive role",
            "industries": ["Federal Government", "Consulting", "Non-profit", "Mission-driven Private"]
        }
    }

def create_sample_job_descriptions():
    """Create realistic job descriptions for each persona's target roles"""
    return {
        "marketing_specialist": """
        We're looking for a Marketing Specialist to join our growing healthcare technology team. 
        You'll be responsible for developing and executing digital marketing campaigns that drive 
        patient engagement and improve healthcare outcomes. The role involves managing our social 
        media presence, creating compelling content, and analyzing campaign performance to optimize 
        our marketing ROI. We need someone who can help us scale our marketing efforts and reach 
        new patient populations through innovative digital strategies.
        
        Key challenges we're facing:
        - Low patient engagement rates on our digital platforms
        - Inconsistent brand messaging across multiple channels
        - Difficulty measuring marketing ROI and patient acquisition costs
        - Need to modernize our marketing automation and lead nurturing processes
        """,
        
        "senior_software_engineer": """
        Senior Software Engineer needed to lead our platform modernization initiative. 
        We're a fast-growing fintech startup looking to scale our infrastructure and 
        improve system performance. The role involves architecting scalable solutions, 
        mentoring junior developers, and implementing best practices for code quality 
        and deployment automation.
        
        Current challenges:
        - Legacy systems causing performance bottlenecks and scalability issues
        - Manual deployment processes slowing down feature releases
        - Need for better code quality standards and automated testing
        - Scaling our microservices architecture to handle increased transaction volume
        """,
        
        "executive_director": """
        Executive Director position for a leading public policy think tank. We're seeking 
        a visionary leader to guide our organization through a period of growth and 
        transformation. The role involves strategic planning, stakeholder management, 
        and leading policy research initiatives that influence national decision-making.
        
        Organizational challenges:
        - Need to expand our research capacity and policy impact
        - Diversifying funding sources and building sustainable revenue streams
        - Managing complex stakeholder relationships across government and private sector
        - Leading digital transformation to modernize our research and advocacy capabilities
        """
    }

def test_persona_enhanced_matching():
    """Test enhanced job matching for each persona"""
    print("🚀 ENHANCED JOB MATCHING - PERSONA TESTING")
    print("Job Description to Problem Statement Analysis Methodology")
    print("=" * 80)
    
    # Get persona profiles and job descriptions
    personas = create_persona_profiles()
    job_descriptions = create_sample_job_descriptions()
    
    # Test each persona
    test_cases = [
        ("maya_johnson", "marketing_specialist", "Healthcare Marketing Specialist"),
        ("marcus_thompson", "senior_software_engineer", "Senior Software Engineer - Fintech"),
        ("dr_jasmine_williams", "executive_director", "Executive Director - Policy Think Tank")
    ]
    
    for persona_key, job_key, job_title in test_cases:
        print(f"\n{'='*80}")
        print(f"🎯 TESTING: {personas[persona_key]['name']} - {personas[persona_key]['tier']}")
        print(f"🎯 TARGET ROLE: {job_title}")
        print(f"{'='*80}")
        
        # Get persona and job description
        persona = personas[persona_key]
        job_description = job_descriptions[job_key]
        
        print(f"\n👤 PERSONA PROFILE:")
        print(f"   Name: {persona['name']}")
        print(f"   Tier: {persona['tier']}")
        print(f"   Location: {persona['location']}")
        print(f"   Current Salary: ${persona['current_salary']:,}")
        print(f"   Target Salary: ${persona['target_salary']:,}")
        print(f"   Experience: {persona['experience_years']} years")
        print(f"   Education: {persona['education']}")
        print(f"   Career Goals: {persona['career_goals']}")
        print(f"   Key Skills: {', '.join(persona['skills'][:5])}...")
        
        print(f"\n📋 JOB DESCRIPTION:")
        print(f"   {job_description[:200]}...")
        
        # Run enhanced job matching
        print(f"\n🔄 RUNNING ENHANCED JOB MATCHING...")
        start_time = time.time()
        
        try:
            # Initialize enhanced engine
            engine = EnhancedJobMatchingEngine()
            
            # Perform enhanced matching
            result = asyncio.run(engine.enhanced_job_matching(
                job_description, 
                persona
            ))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Enhanced matching completed in {processing_time:.2f} seconds")
            
            # Display results
            display_enhanced_results(result, persona, job_title)
            
        except Exception as e:
            print(f"❌ Error in enhanced matching: {str(e)}")
            import traceback
            traceback.print_exc()

def display_enhanced_results(result, persona, job_title):
    """Display comprehensive enhanced matching results"""
    
    print(f"\n📊 ENHANCED MATCHING RESULTS:")
    print(f"   Job Matches: {len(result.job_matches)}")
    print(f"   Success Probability: {result.success_probability:.2%}")
    
    # Problem-Solution Summary
    if result.problem_solution_summary:
        summary = result.problem_solution_summary
        print(f"\n🔍 PROBLEM-SOLUTION ANALYSIS:")
        print(f"   Industry Context: {summary.get('industry_context', 'N/A')}")
        print(f"   Company Stage: {summary.get('company_stage', 'N/A')}")
        print(f"   Confidence Score: {summary.get('confidence_score', 0):.2f}")
        
        if 'problem_statement' in summary:
            ps = summary['problem_statement']
            print(f"   Problem Statement: {ps.get('context', '')} facing {ps.get('challenge', '')}")
            print(f"   Desired Outcome: {ps.get('desired_outcome', '')}")
    
    # Career Positioning Plan
    if result.career_positioning_plan:
        plan = result.career_positioning_plan
        print(f"\n🎯 CAREER POSITIONING PLAN:")
        print(f"   Problem-Solving Focus: {plan.get('problem_solving_focus', 'N/A')}")
        print(f"   Solution Roadmap Items: {len(plan.get('solution_roadmap', []))}")
        print(f"   Skill Development Items: {len(plan.get('skill_development_plan', {}))}")
        print(f"   Networking Strategy Items: {len(plan.get('networking_strategy', []))}")
        print(f"   Portfolio Projects: {len(plan.get('portfolio_projects', []))}")
        
        # Show solution roadmap
        if plan.get('solution_roadmap'):
            print(f"\n   📈 SOLUTION ROADMAP:")
            for i, item in enumerate(plan['solution_roadmap'][:3], 1):
                print(f"      {i}. {item.get('skill', 'N/A')} - {item.get('timeline', 'N/A')} - {item.get('cost', 'N/A')}")
        
        # Show networking strategy
        if plan.get('networking_strategy'):
            print(f"\n   🤝 NETWORKING STRATEGY:")
            for i, strategy in enumerate(plan['networking_strategy'][:3], 1):
                print(f"      {i}. {strategy}")
    
    # Enhanced Job Matches
    if result.job_matches:
        print(f"\n🏆 TOP ENHANCED JOB MATCHES:")
        for i, match in enumerate(result.job_matches[:3], 1):
            job = match.job_opportunity
            print(f"\n   {i}. {job.title} at {job.company}")
            print(f"      Location: {job.location}")
            print(f"      Salary: ${job.salary_min:,} - ${job.salary_max:,}")
            print(f"      Enhanced Score: {match.enhanced_score:.1f}/100")
            print(f"      Problem-Solution Alignment: {match.problem_solution_alignment:.1f}/100")
            
            # Show positioning strategy
            if match.positioning_strategy:
                strategy = match.positioning_strategy
                print(f"      Problem Focus: {strategy.get('problem_focus', 'N/A')[:100]}...")
                print(f"      Value Proposition: {strategy.get('value_proposition', 'N/A')[:100]}...")
            
            # Show application insights
            if match.application_insights:
                insights = match.application_insights
                print(f"      Application Strength: {insights.get('application_strength', 0)}%")
                print(f"      Skill Gaps: {len(insights.get('skill_gaps', []))}")
                print(f"      Immediate Actions: {len(insights.get('immediate_actions', []))}")
                
                # Show skill gaps
                if insights.get('skill_gaps'):
                    print(f"      Key Skill Gaps:")
                    for gap in insights['skill_gaps'][:3]:
                        print(f"         - {gap.get('skill', 'N/A')} ({gap.get('priority', 'N/A')} priority)")
    
    else:
        print(f"\n⚠️  No job matches found - this may indicate:")
        print(f"   - Need for more specific job descriptions")
        print(f"   - Database connection issues")
        print(f"   - Search criteria limitations")

def test_individual_components():
    """Test individual components for each persona"""
    print(f"\n\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print(f"=" * 60)
    
    personas = create_persona_profiles()
    job_descriptions = create_sample_job_descriptions()
    
    # Test problem extraction
    print(f"\n1️⃣ PROBLEM EXTRACTION TESTING")
    print(f"-" * 40)
    
    extractor = JobProblemExtractor()
    
    for job_key, job_title in [("marketing_specialist", "Marketing Specialist"), 
                              ("senior_software_engineer", "Senior Software Engineer"), 
                              ("executive_director", "Executive Director")]:
        
        print(f"\n📋 Testing: {job_title}")
        job_description = job_descriptions[job_key]
        
        problem_analysis = extractor.extract_problems(job_description)
        
        print(f"   Industry Context: {problem_analysis.industry_context.value}")
        print(f"   Company Stage: {problem_analysis.company_stage.value}")
        print(f"   Confidence Score: {problem_analysis.confidence_score:.2f}")
        print(f"   Primary Problems: {len(problem_analysis.primary_problems)}")
        print(f"   Secondary Problems: {len(problem_analysis.secondary_problems)}")
        print(f"   Tertiary Problems: {len(problem_analysis.tertiary_problems)}")
        
        if problem_analysis.primary_problems:
            print(f"   Key Problems:")
            for i, problem in enumerate(problem_analysis.primary_problems[:2], 1):
                print(f"      {i}. {problem.get('sentence', '')[:80]}...")
    
    # Test solution mapping
    print(f"\n\n2️⃣ SOLUTION MAPPING TESTING")
    print(f"-" * 40)
    
    mapper = ProblemSolutionMapper()
    
    for persona_key, persona in personas.items():
        print(f"\n👤 Testing: {persona['name']} ({persona['tier']})")
        
        # Create sample problem analysis
        from backend.utils.job_problem_extractor import ProblemAnalysis, ProblemStatement
        
        problem_analysis = ProblemAnalysis(
            problem_statement=ProblemStatement(
                context=f"{persona['name']} is a {persona['career_field'].lower()} professional",
                challenge="seeking career advancement and higher compensation",
                impact="limited growth opportunities and salary potential",
                desired_outcome="senior-level position with increased responsibilities",
                timeframe="6-12 months",
                constraints=["current experience level", "market competition"]
            ),
            primary_problems=[{
                'sentence': f'Need to advance from {persona["career_goals"]}',
                'indicators': ['need', 'advance'],
                'category': 'career_advancement',
                'confidence': 0.8
            }],
            secondary_problems=[],
            tertiary_problems=[],
            industry_context=IndustryContext.TECHNOLOGY,  # Default
            company_stage=CompanyStage.SCALE_UP,  # Default
            confidence_score=0.8,
            extracted_at=datetime.now()
        )
        
        solution_analysis = mapper.map_solutions(problem_analysis, persona)
        
        print(f"   Top Skills: {len(solution_analysis.top_skills)}")
        print(f"   Top Certifications: {len(solution_analysis.top_certifications)}")
        print(f"   Optimal Titles: {len(solution_analysis.optimal_titles)}")
        
        if solution_analysis.top_skills:
            print(f"   Top Skill: {solution_analysis.top_skills[0].name} ({solution_analysis.top_skills[0].total_score}/100)")
        if solution_analysis.top_certifications:
            print(f"   Top Certification: {solution_analysis.top_certifications[0].name} ({solution_analysis.top_certifications[0].total_score}/100)")
        if solution_analysis.optimal_titles:
            print(f"   Optimal Title: {solution_analysis.optimal_titles[0].name} ({solution_analysis.optimal_titles[0].total_score}/100)")

def main():
    """Run comprehensive persona testing"""
    print("🚀 MINGUS ENHANCED JOB MATCHING SYSTEM")
    print("Persona Testing with Real-World Examples")
    print("=" * 80)
    
    try:
        # Test individual components
        test_individual_components()
        
        # Test complete enhanced matching
        test_persona_enhanced_matching()
        
        print(f"\n\n✅ PERSONA TESTING COMPLETED SUCCESSFULLY!")
        print(f"=" * 60)
        print(f"🎯 Enhanced Job Matching System demonstrated with:")
        print(f"   • Maya Johnson (Budget Tier) - Marketing Specialist")
        print(f"   • Marcus Thompson (Mid-tier) - Senior Software Engineer")
        print(f"   • Dr. Jasmine Williams (Professional) - Executive Director")
        print(f"")
        print(f"📊 Key Features Demonstrated:")
        print(f"   • Problem extraction from job descriptions")
        print(f"   • Solution mapping with 5-factor scoring")
        print(f"   • Enhanced job matching with problem-solution alignment")
        print(f"   • Strategic career positioning for each persona")
        print(f"   • Personalized recommendations based on tier and experience")
        
    except Exception as e:
        print(f"\n❌ PERSONA TESTING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
