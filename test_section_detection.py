#!/usr/bin/env python3
"""
Test script for improved section detection with proper boundaries
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.api.resume_endpoints import ResumeParser

def test_section_detection():
    """Test the improved section detection logic"""
    
    print("📋 IMPROVED SECTION DETECTION TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Well-Structured Resume",
            "content": """JOHN SMITH
Software Engineer
john.smith@email.com | (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years of experience in full-stack development.

WORK EXPERIENCE

Senior Software Engineer
TechCorp Inc., San Francisco, CA
January 2020 - Present
• Led development of microservices architecture
• Implemented CI/CD pipelines

Software Engineer
StartupXYZ, San Francisco, CA
June 2018 - December 2019
• Developed responsive web applications

EDUCATION

Bachelor of Science in Computer Science
University of California, Berkeley
Graduated: May 2018

TECHNICAL SKILLS
• Programming Languages: JavaScript, Python, Java
• Frameworks: React, Node.js, Django
• Cloud: AWS, Docker, Kubernetes

CERTIFICATIONS
• AWS Certified Solutions Architect (2021)
• Google Cloud Professional Developer (2020)

PROJECTS
E-commerce Platform
• Built full-stack e-commerce platform
• Technologies: React, Node.js, MongoDB

LANGUAGES
• English: Native
• Spanish: Fluent"""
        },
        {
            "name": "Alternative Section Headers",
            "content": """JANE DOE
jane.doe@email.com

PERSONAL INFORMATION
Location: San Francisco, CA
LinkedIn: linkedin.com/in/janedoe

EMPLOYMENT HISTORY

Software Developer
ABC Company (2020-2022)
• Built web applications

ACADEMIC BACKGROUND

BS Computer Science
State University (2020)

COMPETENCIES
JavaScript, Python, React, SQL

CREDENTIALS
• Microsoft Azure Fundamentals (2021)"""
        }
    ]
    
    parser = ResumeParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        # Test section detection
        sections = parser._improve_section_detection(test_case['content'])
        
        print(f"📋 SECTION DETECTION RESULTS:")
        if sections:
            print(f"   ✅ Found {len(sections)} sections:")
            for section_name, content in sections.items():
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"      • {section_name}: {content_preview}")
        else:
            print("   ❌ No sections found")
        
        # Test boundary detection
        print(f"\n🔍 BOUNDARY DETECTION TEST:")
        section_patterns = {
            'contact': r'(?:CONTACT|PERSONAL|PROFILE)(?:\s+INFO(?:RMATION)?)?',
            'experience': r'(?:EXPERIENCE|WORK\s+HISTORY|EMPLOYMENT|PROFESSIONAL\s+EXPERIENCE)',
            'education': r'(?:EDUCATION|ACADEMIC|QUALIFICATIONS)',
            'skills': r'(?:SKILLS|TECHNICAL\s+SKILLS|COMPETENCIES|EXPERTISE)',
            'certifications': r'(?:CERTIFICATIONS?|LICENSES?|CREDENTIALS)',
        }
        
        boundaries = parser._find_section_boundaries(test_case['content'], section_patterns)
        for section, (start, end) in boundaries.items():
            print(f"   • {section}: position {start}-{end}")
        
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
    
    print("\n🎉 SECTION DETECTION TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_section_detection()
