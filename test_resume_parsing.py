#!/usr/bin/env python3
"""
Resume Parsing Test Script
Tests the resume parsing functionality with simulated resume data and documents errors
"""

import json
import time
import requests
from datetime import datetime

def test_resume_parsing_system():
    """Test the complete resume parsing system with various resume formats"""
    
    print("🎯 RESUME PARSING FEATURE TESTING")
    print("=" * 60)
    
    # Test data - various resume formats to test parsing robustness
    test_resumes = [
        {
            "name": "Well-Formatted Resume",
            "content": """JOHN SMITH
Software Engineer
john.smith@email.com | (555) 123-4567 | San Francisco, CA
LinkedIn: linkedin.com/in/johnsmith | GitHub: github.com/johnsmith

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years of experience in full-stack development, specializing in React, Node.js, and cloud technologies. Passionate about building scalable applications and leading development teams.

WORK EXPERIENCE

Senior Software Engineer
TechCorp Inc., San Francisco, CA
January 2020 - Present
• Led development of microservices architecture serving 1M+ users
• Implemented CI/CD pipelines reducing deployment time by 60%
• Mentored 3 junior developers and conducted code reviews
• Technologies: React, Node.js, AWS, Docker, Kubernetes

Software Engineer
StartupXYZ, San Francisco, CA
June 2018 - December 2019
• Developed responsive web applications using React and Redux
• Collaborated with product team to define technical requirements
• Optimized database queries improving performance by 40%
• Technologies: JavaScript, Python, PostgreSQL, Redis

EDUCATION

Bachelor of Science in Computer Science
University of California, Berkeley
Graduated: May 2018
GPA: 3.8/4.0

SKILLS
• Programming Languages: JavaScript, Python, Java, Go
• Frontend: React, Vue.js, HTML5, CSS3, TypeScript
• Backend: Node.js, Express, Django, FastAPI
• Databases: PostgreSQL, MongoDB, Redis
• Cloud: AWS, Docker, Kubernetes, Terraform
• Tools: Git, Jenkins, Jira, Confluence

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate (2021)
• Google Cloud Professional Developer (2020)

PROJECTS
E-commerce Platform
• Built full-stack e-commerce platform with React and Node.js
• Implemented payment processing with Stripe API
• Technologies: React, Node.js, MongoDB, Stripe

LANGUAGES
• English: Native
• Spanish: Fluent
• French: Intermediate""",
            "expected_errors": []
        },
        {
            "name": "Minimal Resume",
            "content": """Jane Doe
jane.doe@email.com
(555) 987-6543

Experience:
Software Developer at ABC Company (2020-2022)
Built web applications

Education:
BS Computer Science, State University (2020)

Skills: JavaScript, Python, React""",
            "expected_errors": ["Limited experience data", "Missing detailed descriptions"]
        },
        {
            "name": "Poorly Formatted Resume",
            "content": """RESUME
name:alex johnson
email:alex@email.com
phone:555-111-2222

work:
company1:software dev:2020-2022
company2:junior dev:2018-2020

school:university of state:computer science:2018

skills:java python javascript

projects:
project1:web app:react nodejs
project2:mobile app:react native""",
            "expected_errors": ["Poor formatting", "Missing section headers", "Inconsistent structure"]
        },
        {
            "name": "Empty Resume",
            "content": "",
            "expected_errors": ["Resume content is too short or empty"]
        },
        {
            "name": "Very Short Resume",
            "content": "John Smith\nDeveloper",
            "expected_errors": ["Resume content is too short or empty"]
        },
        {
            "name": "Resume with Special Characters",
            "content": """MARÍA GONZÁLEZ
Software Engineer
maria.gonzalez@email.com | +1 (555) 123-4567 | México City, México
LinkedIn: linkedin.com/in/mariagonzalez

EXPERIENCIA PROFESIONAL

Desarrolladora Senior de Software
EmpresaTech S.A. de C.V., México City
Enero 2019 - Presente
• Desarrollé aplicaciones web escalables usando React y Node.js
• Lideré un equipo de 4 desarrolladores
• Implementé soluciones de microservicios en AWS

EDUCACIÓN

Licenciatura en Ciencias de la Computación
Universidad Nacional Autónoma de México
Graduada: Mayo 2018
Promedio: 9.2/10

HABILIDADES
• Lenguajes: JavaScript, Python, Java, C++
• Frontend: React, Vue.js, Angular
• Backend: Node.js, Express, Django
• Bases de datos: PostgreSQL, MongoDB
• Cloud: AWS, Azure, Google Cloud

PROYECTOS
Sistema de Gestión Empresarial
• Plataforma completa de gestión empresarial
• Tecnologías: React, Node.js, PostgreSQL
• Desplegado en AWS con Docker""",
            "expected_errors": []
        }
    ]
    
    # Test API endpoints
    base_url = "http://localhost:5001"
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": "test-token"
    }
    
    print("🔧 1. API ENDPOINT AVAILABILITY TEST")
    print("-" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: Available")
        else:
            print(f"❌ Health endpoint: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Health endpoint: Error - {e}")
    
    # Test resume parsing endpoint
    try:
        test_payload = {
            "content": "Test resume content",
            "file_name": "test.pdf",
            "user_id": "test_user"
        }
        response = requests.post(f"{base_url}/api/resume/parse", 
                               json=test_payload, 
                               headers=headers, 
                               timeout=10)
        if response.status_code in [200, 400]:  # 400 is expected for short content
            print("✅ Resume parsing endpoint: Available")
        else:
            print(f"❌ Resume parsing endpoint: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Resume parsing endpoint: Error - {e}")
    
    print("\n📋 2. RESUME PARSING TESTS")
    print("-" * 40)
    
    test_results = []
    
    for i, resume_data in enumerate(test_resumes, 1):
        print(f"\n🧪 Test {i}: {resume_data['name']}")
        print("-" * 30)
        
        try:
            # Prepare test payload
            payload = {
                "content": resume_data["content"],
                "file_name": f"test_resume_{i}.txt",
                "user_id": f"test_user_{i}"
            }
            
            # Send request
            start_time = time.time()
            response = requests.post(f"{base_url}/api/resume/parse", 
                                   json=payload, 
                                   headers=headers, 
                                   timeout=15)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Analyze response
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    parsed_data = result.get('parsed_data', {})
                    metadata = result.get('metadata', {})
                    errors = result.get('errors', [])
                    warnings = result.get('warnings', [])
                    
                    print(f"✅ Parsing: SUCCESS")
                    print(f"   • Processing time: {processing_time:.2f}s")
                    print(f"   • Confidence score: {metadata.get('confidence_score', 0):.1f}%")
                    print(f"   • Errors: {len(errors)}")
                    print(f"   • Warnings: {len(warnings)}")
                    
                    # Show extracted data
                    if parsed_data.get('personal_info', {}).get('full_name'):
                        print(f"   • Name: {parsed_data['personal_info']['full_name']}")
                    if parsed_data.get('contact_info', {}).get('email'):
                        print(f"   • Email: {parsed_data['contact_info']['email']}")
                    if parsed_data.get('experience'):
                        print(f"   • Experience entries: {len(parsed_data['experience'])}")
                    if parsed_data.get('education'):
                        print(f"   • Education entries: {len(parsed_data['education'])}")
                    if parsed_data.get('skills'):
                        print(f"   • Skills: {len(parsed_data['skills'])}")
                    
                    # Show errors if any
                    if errors:
                        print(f"   • Parsing errors:")
                        for error in errors[:3]:  # Show first 3 errors
                            print(f"     - {error}")
                        if len(errors) > 3:
                            print(f"     ... and {len(errors) - 3} more errors")
                    
                    # Show warnings if any
                    if warnings:
                        print(f"   • Parsing warnings:")
                        for warning in warnings[:2]:  # Show first 2 warnings
                            print(f"     - {warning}")
                        if len(warnings) > 2:
                            print(f"     ... and {len(warnings) - 2} more warnings")
                    
                    test_results.append({
                        'test_name': resume_data['name'],
                        'status': 'SUCCESS',
                        'processing_time': processing_time,
                        'confidence_score': metadata.get('confidence_score', 0),
                        'errors': errors,
                        'warnings': warnings,
                        'extracted_data': parsed_data
                    })
                    
                else:
                    print(f"❌ Parsing: FAILED")
                    print(f"   • Error: {result.get('error', 'Unknown error')}")
                    test_results.append({
                        'test_name': resume_data['name'],
                        'status': 'FAILED',
                        'error': result.get('error', 'Unknown error')
                    })
                    
            else:
                print(f"❌ API Request: FAILED ({response.status_code})")
                try:
                    error_data = response.json()
                    print(f"   • Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   • Response: {response.text[:100]}...")
                
                test_results.append({
                    'test_name': resume_data['name'],
                    'status': 'API_ERROR',
                    'status_code': response.status_code,
                    'error': response.text[:100]
                })
                
        except requests.exceptions.Timeout:
            print(f"❌ Request: TIMEOUT")
            test_results.append({
                'test_name': resume_data['name'],
                'status': 'TIMEOUT',
                'error': 'Request timed out'
            })
            
        except Exception as e:
            print(f"❌ Request: ERROR - {e}")
            test_results.append({
                'test_name': resume_data['name'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    print("\n📊 3. ANALYTICS TEST")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/resume/analytics", 
                              headers=headers, 
                              timeout=5)
        if response.status_code == 200:
            analytics = response.json()
            if analytics.get('success'):
                data = analytics.get('analytics', {})
                print("✅ Analytics: Available")
                print(f"   • Total resumes parsed: {data.get('total_resumes', 0)}")
                print(f"   • Average confidence: {data.get('average_confidence_score', 0):.1f}%")
                print(f"   • Average processing time: {data.get('average_processing_time', 0):.2f}s")
                print(f"   • Recent activity: {data.get('recent_activity', {})}")
            else:
                print(f"❌ Analytics: Failed - {analytics.get('error', 'Unknown error')}")
        else:
            print(f"❌ Analytics: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Analytics: Error - {e}")
    
    print("\n📈 4. ERROR ANALYSIS")
    print("-" * 40)
    
    # Analyze errors across all tests
    all_errors = []
    all_warnings = []
    success_count = 0
    total_tests = len(test_results)
    
    for result in test_results:
        if result['status'] == 'SUCCESS':
            success_count += 1
            all_errors.extend(result.get('errors', []))
            all_warnings.extend(result.get('warnings', []))
        else:
            all_errors.append(f"Test failed: {result.get('error', 'Unknown error')}")
    
    print(f"✅ Success rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if all_errors:
        print(f"\n❌ Common Errors ({len(all_errors)} total):")
        error_counts = {}
        for error in all_errors:
            error_key = error.split(':')[0] if ':' in error else error
            error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {error}: {count} occurrences")
    
    if all_warnings:
        print(f"\n⚠️  Common Warnings ({len(all_warnings)} total):")
        warning_counts = {}
        for warning in all_warnings:
            warning_key = warning.split(':')[0] if ':' in warning else warning
            warning_counts[warning_key] = warning_counts.get(warning_key, 0) + 1
        
        for warning, count in sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   • {warning}: {count} occurrences")
    
    print("\n🎯 5. DETAILED ERROR BREAKDOWN")
    print("-" * 40)
    
    for result in test_results:
        if result['status'] != 'SUCCESS':
            print(f"\n❌ {result['test_name']}:")
            print(f"   Status: {result['status']}")
            print(f"   Error: {result.get('error', 'No error details')}")
        elif result.get('errors'):
            print(f"\n⚠️  {result['test_name']} (with errors):")
            for error in result['errors'][:2]:  # Show first 2 errors
                print(f"   • {error}")
    
    print("\n🎉 RESUME PARSING TEST COMPLETE!")
    print("=" * 60)
    
    # Summary
    print("📋 TEST SUMMARY:")
    print(f"   • Total tests: {total_tests}")
    print(f"   • Successful: {success_count}")
    print(f"   • Failed: {total_tests - success_count}")
    print(f"   • Success rate: {success_count/total_tests*100:.1f}%")
    print(f"   • Total errors: {len(all_errors)}")
    print(f"   • Total warnings: {len(all_warnings)}")
    
    return test_results

if __name__ == "__main__":
    test_resume_parsing_system()
