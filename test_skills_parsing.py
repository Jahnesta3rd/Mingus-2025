#!/usr/bin/env python3
"""
Test script for improved skills parsing with quality control
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.api.resume_endpoints import ResumeParser

def test_skills_parsing():
    """Test the improved skills parsing logic"""
    
    print("🛠️ IMPROVED SKILLS PARSING TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Technical Skills with Quality Control",
            "content": """JOHN SMITH
Software Engineer

SKILLS
• Python, JavaScript, Java, SQL
• AWS, Azure, Docker, Kubernetes
• React, Angular, Vue.js
• Project Management, Leadership
• Communication, Teamwork
• and, or, with, including
• 12345
• SKILLS HEADER
• Very long skill name that exceeds normal length but should still be valid
• Short
• Machine Learning, AI, Data Analysis"""
        },
        {
            "name": "Mixed Quality Skills",
            "content": """JANE DOE
Developer

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript
Frameworks: React, Node.js, Django, Spring Boot
Cloud: AWS (EC2, S3, RDS), Azure, Google Cloud
Databases: PostgreSQL, MongoDB, Redis
Tools: Git, Docker, Jenkins, Terraform
Soft Skills: Communication, Leadership, Problem Solving
Invalid: and, or, with, 123, SKILLS"""
        }
    ]
    
    parser = ResumeParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        # Parse the resume
        sections = parser._extract_sections(test_case['content'])
        skills = parser._parse_skills_improved(test_case['content'], sections)
        
        print(f"🛠️ SKILLS PARSING RESULTS:")
        if skills:
            print(f"   ✅ Found {len(skills)} high-quality skills:")
            for j, skill in enumerate(skills, 1):
                print(f"      {j}. {skill}")
        else:
            print("   ❌ No skills found")
        
        # Test individual validation
        print(f"\n🔍 VALIDATION TEST:")
        test_skills = ['Python', 'and', 'JavaScript', '123', 'Project Management', 'SKILLS', 'Machine Learning']
        for skill in test_skills:
            is_valid = parser._is_valid_skill(skill)
            relevance = parser._calculate_skill_relevance(skill)
            print(f"   • '{skill}': Valid={is_valid}, Relevance={relevance:.2f}")
        
        # Show any errors or warnings
        if parser.errors:
            print("\n❌ ERRORS:")
            for error in parser.errors:
                print(f"   • {error}")
        
        if parser.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in parser.warnings:
                print(f"   • {warning}")
        
        # Reset parser for next test
        parser.errors = []
        parser.warnings = []
    
    print("\n🎉 SKILLS PARSING TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_skills_parsing()
