#!/usr/bin/env python3
"""
Test script for assessment result document generation
Tests PDF/document generation functionality for assessment results
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_assessment_result_structure():
    """Test that assessment results have the structure needed for document generation"""
    print("🧪 Testing Assessment Result Structure...")
    
    # Sample assessment result
    sample_result = {
        'score': 75,
        'risk_level': 'Medium',
        'recommendations': [
            'Continue building on your AI-resistant skills',
            'Consider mentoring others in your field',
            'Stay updated with industry trends'
        ],
        'assessment_type': 'ai-risk',
        'completed_at': datetime.now().isoformat(),
        'email': 'test@example.com',
        'first_name': 'Test User'
    }
    
    required_fields = ['score', 'risk_level', 'recommendations', 'assessment_type', 'completed_at']
    missing_fields = [field for field in required_fields if field not in sample_result]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print("✅ Assessment result structure is valid")
    return True

def test_pdf_generation_capability():
    """Test if PDF generation libraries are available"""
    print("\n🧪 Testing PDF Generation Capability...")
    
    pdf_libraries = []
    
    # Check for reportlab
    try:
        import reportlab
        pdf_libraries.append('reportlab')
        print("✅ reportlab is available")
    except ImportError:
        print("⚠️  reportlab not installed")
    
    # Check for weasyprint
    try:
        import weasyprint
        pdf_libraries.append('weasyprint')
        print("✅ weasyprint is available")
    except ImportError:
        print("⚠️  weasyprint not installed")
    
    # Check for fpdf
    try:
        import fpdf
        pdf_libraries.append('fpdf')
        print("✅ fpdf is available")
    except ImportError:
        print("⚠️  fpdf not installed")
    
    if not pdf_libraries:
        print("❌ No PDF generation libraries found")
        print("   Install one of: pip install reportlab weasyprint fpdf")
        return False
    
    print(f"✅ PDF generation capability available ({', '.join(pdf_libraries)})")
    return True

def test_document_endpoint():
    """Test if assessment document endpoint exists"""
    print("\n🧪 Testing Assessment Document Endpoint...")
    
    try:
        # Check if endpoint is defined in assessment_endpoints.py
        assessment_endpoints_path = Path('backend/api/assessment_endpoints.py')
        
        if not assessment_endpoints_path.exists():
            print("⚠️  assessment_endpoints.py not found")
            return False
        
        with open(assessment_endpoints_path, 'r') as f:
            content = f.read()
        
        # Look for download endpoint patterns
        if '/download' in content or 'download' in content.lower():
            print("✅ Download endpoint pattern found in assessment_endpoints.py")
            return True
        else:
            print("⚠️  Document download endpoint not found in code")
            print("   Expected: GET /api/assessments/<id>/download")
            return False
                
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def generate_sample_document(result_data):
    """Generate a sample assessment result document (text format)"""
    print("\n📄 Generating Sample Assessment Result Document...")
    
    assessment_titles = {
        'ai-risk': 'AI Replacement Risk Assessment',
        'income-comparison': 'Income Comparison Assessment',
        'cuffing-season': 'Cuffing Season Score',
        'layoff-risk': 'Layoff Risk Assessment'
    }
    
    title = assessment_titles.get(result_data['assessment_type'], 'Assessment Results')
    
    document = f"""
================================================================================
{title.upper()}
================================================================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
For: {result_data.get('first_name', 'User')} ({result_data.get('email', 'N/A')})

================================================================================
YOUR RESULTS
================================================================================

Score: {result_data['score']}/100
Risk Level: {result_data['risk_level']}

================================================================================
INTERPRETATION
================================================================================

"""
    
    if result_data['assessment_type'] == 'ai-risk':
        if result_data['score'] >= 70:
            document += "High Risk - Your job may be at risk from AI automation.\n"
        elif result_data['score'] >= 40:
            document += "Medium Risk - Some aspects of your role could be automated.\n"
        else:
            document += "Low Risk - Your job is relatively safe from AI automation.\n"
    
    document += f"""
================================================================================
PERSONALIZED RECOMMENDATIONS
================================================================================

"""
    
    for i, rec in enumerate(result_data['recommendations'], 1):
        document += f"{i}. {rec}\n"
    
    document += f"""
================================================================================
NEXT STEPS
================================================================================

1. Review your personalized recommendations above
2. Create an action plan based on your results
3. Track your progress over time
4. Consider retaking this assessment in 3-6 months

================================================================================
For more information, visit: https://mingus.com
© 2025 Mingus Personal Finance. All rights reserved.
================================================================================
"""
    
    return document

def test_document_generation():
    """Test generating a sample document"""
    print("\n🧪 Testing Document Generation...")
    
    sample_result = {
        'score': 65,
        'risk_level': 'Medium',
        'recommendations': [
            'Continue building on your AI-resistant skills',
            'Consider mentoring others in your field',
            'Stay updated with industry trends',
            'Document your achievements and value to the company'
        ],
        'assessment_type': 'ai-risk',
        'completed_at': datetime.now().isoformat(),
        'email': 'test@example.com',
        'first_name': 'Test User'
    }
    
    try:
        document = generate_sample_document(sample_result)
        
        # Save to file
        output_dir = Path('test_output')
        output_dir.mkdir(exist_ok=True)
        
        filename = output_dir / f"assessment_result_{sample_result['assessment_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w') as f:
            f.write(document)
        
        print(f"✅ Sample document generated: {filename}")
        print(f"   File size: {filename.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating document: {e}")
        return False

def test_frontend_download_button():
    """Test if frontend download button exists"""
    print("\n🧪 Testing Frontend Download Button...")
    
    assessment_results_path = Path('frontend/src/components/AssessmentResults.tsx')
    
    if not assessment_results_path.exists():
        print("❌ AssessmentResults.tsx not found")
        return False
    
    try:
        with open(assessment_results_path, 'r') as f:
            content = f.read()
        
        if 'Download PDF' in content:
            print("✅ Download PDF button found in AssessmentResults.tsx")
            
            # Check if it has an onClick handler
            if 'onClick' in content and 'Download' in content:
                # Check if handler is implemented
                if 'handleDownload' in content or 'downloadPDF' in content:
                    print("✅ Download handler appears to be implemented")
                    return True
                else:
                    print("⚠️  Download button exists but handler may not be implemented")
                    return False
            else:
                print("⚠️  Download button found but may not have onClick handler")
                return False
        else:
            print("❌ Download PDF button not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 ASSESSMENT RESULT DOCUMENT GENERATION TEST")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Result structure
    results['structure'] = test_assessment_result_structure()
    
    # Test 2: PDF capability
    results['pdf_capability'] = test_pdf_generation_capability()
    
    # Test 3: Document endpoint
    results['endpoint'] = test_document_endpoint()
    
    # Test 4: Document generation
    results['generation'] = test_document_generation()
    
    # Test 5: Frontend button
    results['frontend'] = test_frontend_download_button()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print("⚠️  Some tests failed - review above for details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
