#!/usr/bin/env python3
"""
Test script for the income data management system
Tests fallback data, API integration, and data validation
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_data_manager():
    """Test the IncomeDataManager class"""
    print("🧪 Testing Income Data Manager...")
    
    try:
        from data.income_data_manager import IncomeDataManager, DataSource, DataQuality
        
        # Initialize manager
        manager = IncomeDataManager()
        
        # Test basic functionality
        test_cases = [
            ('african_american', None, None, None),
            ('white', '25-34', None, None),
            ('hispanic_latino', None, 'bachelors', None),
            ('asian', '35-44', 'masters', 'Atlanta')
        ]
        
        working_tests = 0
        total_tests = len(test_cases)
        
        for race, age_group, education_level, location in test_cases:
            try:
                data = manager.get_income_data(race, age_group, education_level, location)
                
                if data and data.median_income > 0:
                    print(f"✅ {race}, {age_group}, {education_level}, {location}: ${data.median_income:,}")
                    working_tests += 1
                else:
                    print(f"❌ {race}, {age_group}, {education_level}, {location}: No valid data")
                    
            except Exception as e:
                print(f"❌ {race}, {age_group}, {education_level}, {location}: Error - {str(e)}")
        
        # Test data quality validation
        quality_report = manager.validate_data_quality()
        print(f"\n📊 Data Quality Report:")
        print(f"   Overall Quality: {quality_report['overall_quality']}")
        print(f"   Issues: {len(quality_report['issues'])}")
        print(f"   Recommendations: {len(quality_report['recommendations'])}")
        
        # Test available locations
        locations = manager.get_available_locations()
        print(f"\n📍 Available Locations: {len(locations)}")
        for location in locations[:5]:  # Show first 5
            print(f"   • {location}")
        
        # Test demographic summary
        summary = manager.get_demographic_summary()
        print(f"\n👥 Demographic Summary:")
        print(f"   Races: {len(summary['races'])}")
        print(f"   Age Groups: {len(summary['age_groups'])}")
        print(f"   Education Levels: {len(summary['education_levels'])}")
        print(f"   Metro Areas: {len(summary['metro_areas'])}")
        
        if working_tests == total_tests:
            print("✅ All data manager tests passed")
            return True
        else:
            print(f"⚠️  {working_tests}/{total_tests} data manager tests passed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data manager: {str(e)}")
        return False

def test_fallback_data():
    """Test fallback data structure and content"""
    print("\n📋 Testing Fallback Data...")
    
    try:
        fallback_file = Path("backend/data/income_datasets/fallback_income_data.json")
        
        if not fallback_file.exists():
            print("❌ Fallback data file not found")
            return False
        
        with open(fallback_file, 'r') as f:
            data = json.load(f)
        
        # Check metadata
        metadata = data.get('metadata', {})
        required_metadata = ['version', 'data_year', 'source', 'last_updated']
        missing_metadata = [key for key in required_metadata if key not in metadata]
        
        if missing_metadata:
            print(f"❌ Missing metadata: {missing_metadata}")
            return False
        
        print(f"✅ Metadata complete - Data from {metadata['data_year']}")
        
        # Check data categories
        categories = ['national_data', 'age_groups', 'education_levels', 'metro_areas']
        missing_categories = [cat for cat in categories if cat not in data]
        
        if missing_categories:
            print(f"❌ Missing categories: {missing_categories}")
            return False
        
        print("✅ All data categories present")
        
        # Check data completeness
        required_races = ['african_american', 'white', 'hispanic_latino', 'asian']
        required_metros = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
        
        # Check national data
        national_data = data.get('national_data', {})
        missing_races = [race for race in required_races if race not in national_data]
        
        if missing_races:
            print(f"❌ Missing national data for: {missing_races}")
            return False
        
        print("✅ National data complete")
        
        # Check metro areas
        metro_areas = data.get('metro_areas', {})
        missing_metros = [metro for metro in required_metros if metro not in metro_areas]
        
        if missing_metros:
            print(f"❌ Missing metro data for: {missing_metros}")
            return False
        
        print("✅ Metro area data complete")
        
        # Check data quality
        total_data_points = 0
        valid_data_points = 0
        
        for category in categories:
            if category in data:
                category_data = data[category]
                for group_name, group_data in category_data.items():
                    if isinstance(group_data, dict):
                        for race, data_point in group_data.items():
                            if isinstance(data_point, dict):
                                total_data_points += 1
                                if data_point.get('median_income', 0) > 0:
                                    valid_data_points += 1
        
        print(f"✅ Data quality: {valid_data_points}/{total_data_points} valid data points")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback data: {str(e)}")
        return False

def test_data_validation():
    """Test data validation functionality"""
    print("\n🔍 Testing Data Validation...")
    
    try:
        from scripts.income_data_validator import IncomeDataValidator
        
        validator = IncomeDataValidator()
        
        # Run validation
        validation_report = validator.validate_all_data()
        
        print(f"📊 Validation Results:")
        print(f"   Overall Status: {validation_report['overall_status']}")
        print(f"   Quality Score: {validation_report['data_quality_score']:.1f}%")
        print(f"   Total Issues: {len(validation_report['issues'])}")
        print(f"   Total Recommendations: {len(validation_report['recommendations'])}")
        
        # Check validation results
        validation_results = validation_report.get('validation_results', {})
        passed_checks = len([r for r in validation_results.values() if r.get('status') == 'passed'])
        total_checks = len(validation_results)
        
        print(f"   Passed Checks: {passed_checks}/{total_checks}")
        
        # Show some issues if any
        if validation_report['issues']:
            print(f"\n❌ Sample Issues:")
            for issue in validation_report['issues'][:3]:
                print(f"   • {issue}")
        
        # Show some recommendations
        if validation_report['recommendations']:
            print(f"\n💡 Sample Recommendations:")
            for rec in validation_report['recommendations'][:3]:
                print(f"   • {rec}")
        
        # Generate update report
        update_report = validator.generate_update_report()
        print(f"\n📋 Update Report:")
        print(f"   Priority Updates: {len(update_report['priority_updates'])}")
        print(f"   Recommended Updates: {len(update_report['recommended_updates'])}")
        
        if validation_report['overall_status'] in ['good', 'excellent']:
            print("✅ Data validation passed")
            return True
        else:
            print("⚠️  Data validation needs attention")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data validation: {str(e)}")
        return False

def test_api_integration():
    """Test Census API integration (without making actual API calls)"""
    print("\n🌐 Testing API Integration Framework...")
    
    try:
        from scripts.census_api_integration import CensusAPIClient, CensusDataUpdater
        
        # Test API client initialization
        client = CensusAPIClient()
        
        # Check API key
        if not client.api_key:
            print("⚠️  No API key configured (expected for testing)")
        else:
            print("✅ API key configured")
        
        # Test metro codes
        metro_codes = client._get_metro_codes()
        expected_metros = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
        
        missing_metros = [metro for metro in expected_metros if metro not in metro_codes]
        
        if missing_metros:
            print(f"❌ Missing metro codes: {missing_metros}")
            return False
        
        print("✅ Metro area codes complete")
        
        # Test income variables
        income_vars = client.income_variables
        required_vars = ['median_household_income', 'black_median_income', 'white_median_income']
        
        missing_vars = [var for var in required_vars if var not in income_vars]
        
        if missing_vars:
            print(f"❌ Missing income variables: {missing_vars}")
            return False
        
        print("✅ Income variables complete")
        
        # Test rate limiting
        if client._check_rate_limit():
            print("✅ Rate limiting working")
        else:
            print("⚠️  Rate limit reached (expected if no API key)")
        
        # Test updater initialization
        updater = CensusDataUpdater()
        print("✅ Data updater initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API integration: {str(e)}")
        return False

def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        from data.income_data_manager import IncomeDataManager
        
        manager = IncomeDataManager()
        
        # Test with invalid parameters
        test_cases = [
            ('invalid_race', None, None, None),
            ('african_american', 'invalid_age', None, None),
            ('white', None, 'invalid_education', None),
            ('hispanic_latino', None, None, 'invalid_location')
        ]
        
        working_fallbacks = 0
        total_tests = len(test_cases)
        
        for race, age_group, education_level, location in test_cases:
            try:
                data = manager.get_income_data(race, age_group, education_level, location)
                
                if data and data.median_income > 0:
                    print(f"✅ Fallback working for invalid: {race}, {age_group}, {education_level}, {location}")
                    working_fallbacks += 1
                else:
                    print(f"❌ No fallback for invalid: {race}, {age_group}, {education_level}, {location}")
                    
            except Exception as e:
                print(f"❌ Error with invalid params: {str(e)}")
        
        # Test data quality validation with errors
        try:
            quality_report = manager.validate_data_quality()
            print("✅ Data quality validation handles errors gracefully")
            working_fallbacks += 1
        except Exception as e:
            print(f"❌ Data quality validation failed: {str(e)}")
        
        if working_fallbacks >= total_tests:
            print("✅ Error handling working correctly")
            return True
        else:
            print(f"⚠️  {working_fallbacks}/{total_tests + 1} error handling tests passed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing error handling: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🎯 INCOME DATA MANAGEMENT SYSTEM TEST")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        test_data_manager,
        test_fallback_data,
        test_data_validation,
        test_api_integration,
        test_error_handling
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Income data management system is ready for production")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Most tests passed - system is mostly ready")
    else:
        print("⚠️  Several tests failed - review needed")
    
    print("\nKey features tested:")
    print("• Income data manager functionality")
    print("• Fallback data structure and completeness")
    print("• Data validation and quality checks")
    print("• API integration framework")
    print("• Error handling and fallback mechanisms")
    
    print("\nNext steps:")
    print("1. Set CENSUS_API_KEY environment variable for API testing")
    print("2. Run data validation script: python scripts/income_data_validator.py")
    print("3. Test API integration: python scripts/census_api_integration.py")
    print("4. Update fallback data annually with latest ACS estimates")
    print("5. Monitor data quality and address any issues")

if __name__ == "__main__":
    main() 