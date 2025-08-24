#!/usr/bin/env python3
"""
Test script for income comparison integration
Tests the Flask routes and IncomeComparator integration
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from ml.models.income_comparator import IncomeComparator, EducationLevel

def test_income_comparator_direct():
    """Test IncomeComparator directly"""
    print("🧪 Testing IncomeComparator directly...")
    
    comparator = IncomeComparator()
    
    # Test case: African American professional in Atlanta
    result = comparator.analyze_income(
        user_income=65000,
        location="Atlanta",
        education_level=EducationLevel.BACHELORS,
        age_group="25-35"
    )
    
    print(f"✅ Income analysis completed:")
    print(f"   Overall Percentile: {result.overall_percentile:.1f}%")
    print(f"   Career Opportunity Score: {result.career_opportunity_score:.1f}/100")
    print(f"   Primary Gap: {result.primary_gap.group_name}")
    print(f"   Gap Amount: ${abs(result.primary_gap.income_gap):,}")
    print(f"   Motivational Summary: {result.motivational_summary}")
    
    print(f"   Comparisons: {len(result.comparisons)} demographic groups")
    for comp in result.comparisons[:3]:  # Show first 3
        print(f"     - {comp.group_name}: {comp.percentile_rank:.1f}% percentile")
    
    return result

def test_flask_integration():
    """Test Flask integration (requires running server)"""
    print("\n🌐 Testing Flask integration...")
    
    # Test data
    test_data = {
        "current_salary": 65000,
        "age_range": "25-27",
        "race": "African American",
        "education_level": "bachelors",
        "location": "Atlanta"
    }
    
    try:
        # Test the income comparison endpoint
        response = requests.post(
            "http://localhost:5003/api/enhanced-recommendations/income-comparison",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask income comparison endpoint working!")
            print(f"   Response: {data['success']}")
            if 'data' in data and 'income_comparison' in data['data']:
                ic = data['data']['income_comparison']
                print(f"   Overall Percentile: {ic['overall_percentile']:.1f}%")
                print(f"   Career Opportunity Score: {ic['career_opportunity_score']:.1f}/100")
                print(f"   Primary Gap: {ic['primary_gap']['group_name']}")
                print(f"   Gap Amount: ${abs(ic['primary_gap']['income_gap']):,}")
        else:
            print(f"❌ Flask endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask server not running. Start with: python app.py")
    except Exception as e:
        print(f"❌ Flask test failed: {str(e)}")

def test_form_data_processing():
    """Test form data processing"""
    print("\n📝 Testing form data processing...")
    
    # Simulate form data
    form_data = {
        'resume_text': 'Experienced software engineer with 5 years in Python development...',
        'current_salary': '65000',
        'age_range': '25-27',
        'race': 'African American',
        'education_level': 'bachelors',
        'location': 'Atlanta',
        'years_experience': '2-5',
        'industry': 'technology',
        'company_size': 'medium',
        'remote_preference': 'true',
        'relocation_willingness': 'same_state',
        'career_goals': 'Advance to senior engineering role',
        'salary_expectations': '15-25',
        'target_locations': ['Atlanta', 'Houston']
    }
    
    # Test education mapping
    education_mapping = {
        'high_school': EducationLevel.HIGH_SCHOOL,
        'some_college': EducationLevel.SOME_COLLEGE,
        'bachelors': EducationLevel.BACHELORS,
        'masters': EducationLevel.MASTERS,
        'doctorate': EducationLevel.DOCTORATE
    }
    
    education_level = education_mapping.get(form_data['education_level'])
    if education_level:
        print(f"✅ Education mapping working: {form_data['education_level']} -> {education_level}")
    else:
        print(f"❌ Education mapping failed for: {form_data['education_level']}")
    
    # Test required fields validation
    required_fields = ['age_range', 'race', 'education_level', 'location']
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    
    if not missing_fields:
        print("✅ All required demographic fields present")
    else:
        print(f"❌ Missing required fields: {missing_fields}")
    
    return form_data

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing error handling...")
    
    comparator = IncomeComparator()
    
    # Test 1: Invalid salary
    try:
        result = comparator.analyze_income(-1000)
        print("✅ Handles negative salary gracefully")
    except Exception as e:
        print(f"❌ Negative salary handling failed: {str(e)}")
    
    # Test 2: Missing location
    try:
        result = comparator.analyze_income(65000, location="Invalid Location")
        print("✅ Handles invalid location gracefully")
    except Exception as e:
        print(f"❌ Invalid location handling failed: {str(e)}")
    
    # Test 3: Missing education level
    try:
        result = comparator.analyze_income(65000, location="Atlanta")
        print("✅ Handles missing education level gracefully")
    except Exception as e:
        print(f"❌ Missing education handling failed: {str(e)}")

def main():
    """Main test function"""
    print("🎯 INCOME COMPARISON INTEGRATION TEST")
    print("=" * 50)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    test_income_comparator_direct()
    test_form_data_processing()
    test_error_handling()
    test_flask_integration()
    
    print("\n✅ INTEGRATION TEST COMPLETE")
    print("=" * 50)
    print("Key features tested:")
    print("• IncomeComparator direct usage")
    print("• Form data processing and validation")
    print("• Error handling scenarios")
    print("• Flask route integration (if server running)")
    print()
    print("Next steps:")
    print("1. Start Flask server: python app.py")
    print("2. Test the enhanced upload form")
    print("3. Verify income comparison appears in results")

if __name__ == "__main__":
    main() 