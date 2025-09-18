#!/usr/bin/env python3
"""
Advanced Resume Parser Test Suite
Tests the AdvancedResumeParser with sample resumes from target demographic
African American professionals aged 25-35 earning $40k-$100k in major metro areas
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from utils.advanced_resume_parser import AdvancedResumeParser
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_resume_parser():
    """Test the AdvancedResumeParser with sample resumes"""
    
    print("🎯 ADVANCED RESUME PARSER TESTING")
    print("=" * 60)
    print("Target Demographic: African American professionals aged 25-35")
    print("Income Range: $40k-$100k in major metro areas")
    print("=" * 60)
    
    # Initialize parser
    parser = AdvancedResumeParser()
    
    # Sample resumes representing the target demographic
    test_resumes = [
        {
            "name": "Marcus Johnson - Software Engineer (Atlanta)",
            "age_range": "28-30",
            "expected_income": "$75k-$85k",
            "location": "Atlanta",
            "content": """MARCUS JOHNSON
Software Engineer
marcus.johnson@email.com | (404) 555-0123 | Atlanta, GA
LinkedIn: linkedin.com/in/marcusjohnson | GitHub: github.com/marcusj

PROFESSIONAL SUMMARY
Passionate software engineer with 4+ years of experience in full-stack development, specializing in React, Node.js, and cloud technologies. Strong background in building scalable applications and mentoring junior developers. Committed to diversity and inclusion in tech.

WORK EXPERIENCE

Senior Software Engineer
TechFlow Solutions, Atlanta, GA
March 2022 - Present
• Led development of microservices architecture serving 500K+ users
• Implemented CI/CD pipelines reducing deployment time by 50%
• Mentored 2 junior developers and conducted code reviews
• Collaborated with product team to define technical requirements
• Technologies: React, Node.js, AWS, Docker, Kubernetes, TypeScript

Software Engineer
StartupHub, Atlanta, GA
June 2020 - February 2022
• Developed responsive web applications using React and Redux
• Optimized database queries improving performance by 35%
• Participated in agile development processes
• Technologies: JavaScript, Python, PostgreSQL, Redis, Express

Junior Developer
CodeCraft Inc., Atlanta, GA
August 2019 - May 2020
• Built frontend components using React and CSS
• Assisted in debugging and testing applications
• Participated in code reviews and team meetings
• Technologies: HTML, CSS, JavaScript, React

EDUCATION

Bachelor of Science in Computer Science
Georgia Institute of Technology, Atlanta, GA
Graduated: May 2019
GPA: 3.6/4.0
Relevant Coursework: Data Structures, Algorithms, Software Engineering

SKILLS
• Programming Languages: JavaScript, Python, Java, TypeScript, SQL
• Frontend: React, Vue.js, HTML5, CSS3, Redux
• Backend: Node.js, Express, Django, FastAPI
• Databases: PostgreSQL, MongoDB, Redis
• Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
• Tools: Git, Jenkins, Jira, Confluence, VS Code

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate (2022)
• Google Cloud Professional Developer (2021)

PROJECTS
E-commerce Platform
• Built full-stack e-commerce platform with React and Node.js
• Implemented payment processing with Stripe API
• Technologies: React, Node.js, MongoDB, Stripe

Community Outreach App
• Developed mobile app for local community events
• Led team of 3 developers in 6-month project
• Technologies: React Native, Firebase, JavaScript

LANGUAGES
• English: Native
• Spanish: Conversational

VOLUNTEER EXPERIENCE
• Code for Atlanta - Volunteer Developer (2020-Present)
• Black Tech Atlanta - Mentor (2021-Present)"""
        },
        {
            "name": "Keisha Williams - Financial Analyst (Chicago)",
            "age_range": "26-28",
            "expected_income": "$65k-$75k",
            "location": "Chicago",
            "content": """KEISHA WILLIAMS
Financial Analyst
keisha.williams@email.com | (312) 555-0456 | Chicago, IL
LinkedIn: linkedin.com/in/keishawilliams

PROFESSIONAL SUMMARY
Detail-oriented financial analyst with 3+ years of experience in financial modeling, budgeting, and data analysis. Strong analytical skills and experience with financial software. Passionate about helping individuals and businesses make informed financial decisions.

WORK EXPERIENCE

Financial Analyst
Midwest Financial Group, Chicago, IL
January 2021 - Present
• Developed financial models for investment analysis and portfolio management
• Created monthly and quarterly financial reports for senior management
• Analyzed market trends and provided investment recommendations
• Managed budget forecasting for $50M+ portfolio
• Collaborated with cross-functional teams on financial planning
• Technologies: Excel, Power BI, SQL, Bloomberg Terminal

Junior Financial Analyst
Chicago Investment Partners, Chicago, IL
June 2019 - December 2020
• Assisted in financial statement analysis and valuation
• Prepared client presentations and investment reports
• Conducted market research and competitive analysis
• Supported senior analysts in due diligence processes
• Technologies: Excel, PowerPoint, FactSet, Morningstar

Financial Intern
First National Bank, Chicago, IL
May 2018 - August 2018
• Assisted with loan processing and credit analysis
• Prepared financial reports and presentations
• Shadowed senior financial advisors
• Participated in client meetings and presentations

EDUCATION

Bachelor of Science in Finance
University of Illinois at Chicago, Chicago, IL
Graduated: May 2019
GPA: 3.7/4.0
Relevant Coursework: Financial Analysis, Investment Management, Risk Management

SKILLS
• Financial Analysis: Financial modeling, Valuation, Budgeting, Forecasting
• Software: Excel (Advanced), Power BI, SQL, Bloomberg Terminal, FactSet
• Analytical: Data analysis, Statistical analysis, Market research
• Communication: Report writing, Presentation skills, Client relations
• Certifications: CFA Level 1 Candidate

CERTIFICATIONS
• CFA Level 1 (Passed - 2022)
• Microsoft Excel Expert (2021)

PROJECTS
Portfolio Optimization Model
• Developed Excel-based model for portfolio optimization
• Implemented Monte Carlo simulation for risk analysis
• Presented findings to investment committee

Market Analysis Dashboard
• Created Power BI dashboard for real-time market analysis
• Integrated multiple data sources for comprehensive view
• Technologies: Power BI, SQL, Excel

LANGUAGES
• English: Native

VOLUNTEER EXPERIENCE
• Financial Literacy Workshop - Volunteer Instructor (2020-Present)
• Junior Achievement - Financial Education Volunteer (2019-2021)"""
        },
        {
            "name": "David Thompson - Marketing Manager (Houston)",
            "age_range": "30-32",
            "expected_income": "$70k-$80k",
            "location": "Houston",
            "content": """DAVID THOMPSON
Marketing Manager
david.thompson@email.com | (713) 555-0789 | Houston, TX
LinkedIn: linkedin.com/in/davidthompson

PROFESSIONAL SUMMARY
Results-driven marketing professional with 5+ years of experience in digital marketing, brand management, and campaign development. Proven track record of increasing brand awareness and driving revenue growth. Strong leadership skills and experience managing cross-functional teams.

WORK EXPERIENCE

Marketing Manager
Houston Marketing Solutions, Houston, TX
August 2021 - Present
• Led digital marketing campaigns generating $2M+ in revenue
• Managed team of 4 marketing specialists and coordinators
• Developed and executed comprehensive marketing strategies
• Increased social media engagement by 150% across all platforms
• Collaborated with sales team to align marketing and sales objectives
• Managed annual marketing budget of $500K
• Technologies: HubSpot, Google Analytics, Facebook Ads, LinkedIn Ads

Senior Marketing Specialist
Texas Brand Agency, Houston, TX
March 2019 - July 2021
• Developed and executed integrated marketing campaigns
• Managed client relationships and project timelines
• Created content for various marketing channels
• Analyzed campaign performance and provided recommendations
• Technologies: Adobe Creative Suite, Mailchimp, Hootsuite

Marketing Coordinator
Houston Business Journal, Houston, TX
June 2018 - February 2019
• Supported marketing team in campaign development and execution
• Managed social media accounts and content creation
• Assisted with event planning and coordination
• Conducted market research and competitive analysis
• Technologies: Canva, Buffer, Google Analytics

EDUCATION

Master of Business Administration (MBA)
Rice University, Houston, TX
Graduated: May 2018
Concentration: Marketing
GPA: 3.8/4.0

Bachelor of Arts in Communications
Texas Southern University, Houston, TX
Graduated: May 2016
GPA: 3.5/4.0

SKILLS
• Digital Marketing: SEO, SEM, Social Media Marketing, Email Marketing
• Analytics: Google Analytics, Facebook Analytics, HubSpot Analytics
• Design: Adobe Creative Suite, Canva, Figma
• Management: Team Leadership, Project Management, Budget Management
• Communication: Public Speaking, Content Writing, Presentation Skills

CERTIFICATIONS
• Google Analytics Certified (2022)
• HubSpot Content Marketing Certified (2021)
• Facebook Blueprint Certified (2020)

PROJECTS
Brand Awareness Campaign
• Led 6-month campaign increasing brand awareness by 200%
• Managed $100K budget across multiple channels
• Coordinated with creative team and external agencies

Customer Retention Program
• Developed loyalty program increasing customer retention by 40%
• Implemented email marketing automation
• Technologies: Mailchimp, Salesforce, Zapier

LANGUAGES
• English: Native
• Spanish: Basic

VOLUNTEER EXPERIENCE
• Houston Marketing Association - Board Member (2020-Present)
• Junior Achievement - Marketing Mentor (2019-2021)"""
        },
        {
            "name": "Aisha Brown - Healthcare Administrator (Philadelphia)",
            "age_range": "29-31",
            "expected_income": "$60k-$70k",
            "location": "Philadelphia",
            "content": """AISHA BROWN
Healthcare Administrator
aisha.brown@email.com | (215) 555-0321 | Philadelphia, PA
LinkedIn: linkedin.com/in/aishabrown

PROFESSIONAL SUMMARY
Dedicated healthcare administrator with 4+ years of experience in healthcare operations, patient care coordination, and staff management. Strong background in healthcare policy, compliance, and quality improvement. Committed to improving healthcare access and outcomes for underserved communities.

WORK EXPERIENCE

Healthcare Administrator
Philadelphia Community Health Center, Philadelphia, PA
September 2020 - Present
• Managed daily operations of 50+ staff healthcare facility
• Oversaw patient care coordination and scheduling
• Implemented quality improvement initiatives resulting in 25% efficiency gain
• Managed annual budget of $3M and ensured compliance with regulations
• Led staff training programs and performance evaluations
• Collaborated with medical staff and external stakeholders
• Technologies: Epic, Cerner, Microsoft Office, Healthcare Analytics

Assistant Healthcare Administrator
Temple University Hospital, Philadelphia, PA
June 2018 - August 2020
• Assisted in managing healthcare operations and staff scheduling
• Coordinated patient care services and discharge planning
• Maintained compliance with healthcare regulations and standards
• Supported quality assurance and performance improvement initiatives
• Technologies: Epic, Microsoft Office, Healthcare Management Systems

Healthcare Coordinator
Children's Hospital of Philadelphia, Philadelphia, PA
May 2017 - May 2018
• Coordinated patient care services and family support programs
• Managed patient records and documentation
• Assisted with community outreach and health education programs
• Supported clinical staff in patient care delivery
• Technologies: Epic, Microsoft Office, Patient Management Systems

EDUCATION

Master of Health Administration (MHA)
Drexel University, Philadelphia, PA
Graduated: May 2018
GPA: 3.7/4.0
Relevant Coursework: Healthcare Policy, Healthcare Finance, Quality Improvement

Bachelor of Science in Health Sciences
Temple University, Philadelphia, PA
Graduated: May 2016
GPA: 3.6/4.0

SKILLS
• Healthcare Management: Operations, Quality Improvement, Compliance
• Technology: Epic, Cerner, Microsoft Office, Healthcare Analytics
• Leadership: Staff Management, Team Building, Performance Evaluation
• Communication: Patient Relations, Staff Training, Public Speaking
• Analytical: Data Analysis, Performance Metrics, Process Improvement

CERTIFICATIONS
• Certified Healthcare Financial Professional (CHFP) - 2021
• Healthcare Quality Management Certification - 2020
• HIPAA Compliance Certification - 2019

PROJECTS
Patient Satisfaction Improvement Initiative
• Led initiative increasing patient satisfaction scores by 30%
• Implemented new patient communication protocols
• Coordinated staff training and process improvements

Electronic Health Records Implementation
• Managed transition to new EHR system
• Trained 100+ staff members on new system
• Ensured compliance with healthcare regulations
• Technologies: Epic, Training Management Systems

LANGUAGES
• English: Native

VOLUNTEER EXPERIENCE
• Philadelphia Health Department - Community Health Volunteer (2018-Present)
• American Red Cross - Healthcare Volunteer (2017-2020)"""
        },
        {
            "name": "Michael Davis - Sales Manager (Detroit)",
            "age_range": "27-29",
            "expected_income": "$55k-$65k",
            "location": "Detroit",
            "content": """MICHAEL DAVIS
Sales Manager
michael.davis@email.com | (313) 555-0654 | Detroit, MI
LinkedIn: linkedin.com/in/michaeldavis

PROFESSIONAL SUMMARY
Dynamic sales professional with 4+ years of experience in B2B sales, account management, and team leadership. Proven track record of exceeding sales targets and building strong client relationships. Strong background in automotive and manufacturing industries.

WORK EXPERIENCE

Sales Manager
Detroit Automotive Solutions, Detroit, MI
January 2021 - Present
• Led sales team of 6 representatives achieving $5M+ annual revenue
• Managed key accounts and developed new business opportunities
• Exceeded quarterly sales targets by 15% consistently
• Implemented CRM system improving sales tracking and reporting
• Conducted sales training and performance evaluations
• Technologies: Salesforce, HubSpot, Microsoft Office, CRM Systems

Senior Sales Representative
Michigan Manufacturing Co., Detroit, MI
March 2019 - December 2020
• Generated $2M+ in annual sales revenue
• Managed portfolio of 50+ B2B clients
• Developed and maintained strong client relationships
• Collaborated with technical team on product specifications
• Technologies: Salesforce, Microsoft Office, Video Conferencing

Sales Representative
AutoParts Direct, Detroit, MI
June 2018 - February 2019
• Sold automotive parts and accessories to retail and wholesale customers
• Met and exceeded monthly sales quotas
• Provided product knowledge and technical support to customers
• Maintained customer database and sales records
• Technologies: Point of Sale Systems, Microsoft Office

EDUCATION

Bachelor of Business Administration
Wayne State University, Detroit, MI
Graduated: May 2018
Major: Marketing
GPA: 3.4/4.0
Relevant Coursework: Sales Management, Consumer Behavior, Business Communications

SKILLS
• Sales: B2B Sales, Account Management, Lead Generation, Negotiation
• Technology: Salesforce, HubSpot, Microsoft Office, CRM Systems
• Leadership: Team Management, Sales Training, Performance Evaluation
• Communication: Client Relations, Presentation Skills, Public Speaking
• Industry Knowledge: Automotive, Manufacturing, Supply Chain

CERTIFICATIONS
• Salesforce Certified Sales Professional (2022)
• HubSpot Sales Software Certified (2021)
• Dale Carnegie Sales Training (2019)

PROJECTS
CRM Implementation Project
• Led implementation of new CRM system for sales team
• Trained 15+ sales representatives on new system
• Improved sales tracking and reporting efficiency by 40%
• Technologies: Salesforce, Training Management Systems

Client Retention Program
• Developed program increasing client retention by 25%
• Implemented regular check-ins and customer satisfaction surveys
• Created client success metrics and reporting system

LANGUAGES
• English: Native

VOLUNTEER EXPERIENCE
• Detroit Sales Professionals Association - Member (2019-Present)
• Junior Achievement - Sales Mentor (2020-2021)"""
        }
    ]
    
    # Test each resume
    results = []
    
    for i, resume in enumerate(test_resumes, 1):
        print(f"\n📄 TESTING RESUME {i}: {resume['name']}")
        print("-" * 50)
        
        try:
            # Parse resume with advanced analytics
            result = parser.parse_resume_advanced(
                content=resume['content'],
                file_name=f"test_resume_{i}.txt",
                location=resume['location']
            )
            
            if result.get('success', False):
                print("✅ Parsing successful!")
                
                # Display basic parsing results
                parsed_data = result.get('parsed_data', {})
                print(f"📊 Basic Parsing Results:")
                print(f"   • Name: {parsed_data.get('personal_info', {}).get('full_name', 'N/A')}")
                print(f"   • Email: {parsed_data.get('contact_info', {}).get('email', 'N/A')}")
                print(f"   • Experience Entries: {len(parsed_data.get('experience', []))}")
                print(f"   • Skills Count: {len(parsed_data.get('skills', []))}")
                print(f"   • Confidence Score: {result.get('metadata', {}).get('confidence_score', 0):.2f}")
                
                # Display advanced analytics
                advanced = result.get('advanced_analytics', {})
                print(f"\n🎯 Advanced Analytics:")
                print(f"   • Career Field: {advanced.get('career_field', 'N/A')}")
                print(f"   • Experience Level: {advanced.get('experience_level', 'N/A')}")
                
                # Career trajectory
                trajectory = advanced.get('career_trajectory', {})
                print(f"   • Growth Pattern: {trajectory.get('growth_pattern', 'N/A')}")
                print(f"   • Promotion Frequency: {trajectory.get('promotion_frequency', 0):.2f}/year")
                print(f"   • Industry Consistency: {'Yes' if trajectory.get('industry_consistency', False) else 'No'}")
                print(f"   • Leadership Development: {'Yes' if trajectory.get('leadership_development', False) else 'No'}")
                
                # Skills categorization
                skills_cat = advanced.get('skills_categorized', {})
                print(f"   • Technical Skills: {len(skills_cat.get('Technical', []))}")
                print(f"   • Soft Skills: {len(skills_cat.get('Soft Skills', []))}")
                print(f"   • Leadership Skills: {len(skills_cat.get('Leadership', []))}")
                
                # Leadership indicators
                leadership = advanced.get('leadership_indicators', {})
                print(f"   • Leadership Score: {leadership.get('leadership_score', 0):.2f}")
                
                # Income potential
                income = advanced.get('income_potential', {})
                estimated_salary = income.get('estimated_current_salary', 0)
                market_range = income.get('market_value_range', [0, 0])
                print(f"   • Estimated Salary: ${estimated_salary:,.0f}")
                print(f"   • Market Range: ${market_range[0]:,.0f} - ${market_range[1]:,.0f}")
                print(f"   • Growth Potential: {income.get('growth_potential', 0):.2f}")
                
                # Compare with expected
                print(f"\n📈 Comparison with Expected:")
                print(f"   • Expected Income: {resume['expected_income']}")
                print(f"   • Estimated Income: ${estimated_salary:,.0f}")
                
                # Check if estimated salary is within expected range
                expected_range = resume['expected_income'].replace('$', '').replace('k', '000').split('-')
                if len(expected_range) == 2:
                    expected_min = int(expected_range[0])
                    expected_max = int(expected_range[1])
                    if expected_min <= estimated_salary <= expected_max:
                        print("   ✅ Salary estimate within expected range")
                    else:
                        print("   ⚠️  Salary estimate outside expected range")
                
                results.append({
                    'resume_name': resume['name'],
                    'success': True,
                    'estimated_salary': estimated_salary,
                    'career_field': advanced.get('career_field'),
                    'experience_level': advanced.get('experience_level'),
                    'leadership_score': leadership.get('leadership_score', 0)
                })
                
            else:
                print("❌ Parsing failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                results.append({
                    'resume_name': resume['name'],
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            print(f"❌ Exception during parsing: {str(e)}")
            results.append({
                'resume_name': resume['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n💰 Salary Analysis:")
        salaries = [r['estimated_salary'] for r in successful_tests if 'estimated_salary' in r]
        if salaries:
            print(f"   • Average Estimated Salary: ${sum(salaries)/len(salaries):,.0f}")
            print(f"   • Salary Range: ${min(salaries):,.0f} - ${max(salaries):,.0f}")
        
        print(f"\n🎯 Career Field Distribution:")
        career_fields = [r['career_field'] for r in successful_tests if 'career_field' in r]
        field_counts = {}
        for field in career_fields:
            field_counts[field] = field_counts.get(field, 0) + 1
        for field, count in field_counts.items():
            print(f"   • {field}: {count}")
        
        print(f"\n📈 Experience Level Distribution:")
        exp_levels = [r['experience_level'] for r in successful_tests if 'experience_level' in r]
        level_counts = {}
        for level in exp_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        for level, count in level_counts.items():
            print(f"   • {level}: {count}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   • {test['resume_name']}: {test['error']}")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"advanced_resume_parser_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'test_timestamp': timestamp,
            'total_tests': len(results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    test_advanced_resume_parser()
