#!/usr/bin/env python3
"""
Income Data Validation and Update Script
Validates data integrity and provides update procedures for income comparison data
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from loguru import logger

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from data.income_data_manager import IncomeDataManager, DataQuality, DataSource

class IncomeDataValidator:
    """
    Comprehensive data validation and update system for income comparison data
    """
    
    def __init__(self, data_dir: str = "backend/data/income_datasets"):
        self.data_dir = Path(data_dir)
        self.data_manager = IncomeDataManager(str(self.data_dir))
        self.validation_results = {}
        
    def validate_all_data(self) -> Dict[str, Any]:
        """
        Perform comprehensive validation of all income data
        
        Returns:
            Dictionary with validation results and recommendations
        """
        logger.info("Starting comprehensive income data validation...")
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'data_quality_score': 0,
            'validation_results': {},
            'issues': [],
            'recommendations': [],
            'summary': {}
        }
        
        # Run all validation checks
        checks = [
            self._validate_data_structure,
            self._validate_data_completeness,
            self._validate_data_consistency,
            self._validate_data_freshness,
            self._validate_statistical_quality,
            self._validate_geographic_coverage,
            self._validate_demographic_coverage
        ]
        
        total_score = 0
        max_score = len(checks) * 100
        
        for check in checks:
            try:
                result = check()
                validation_report['validation_results'][check.__name__] = result
                total_score += result.get('score', 0)
                
                if result.get('issues'):
                    validation_report['issues'].extend(result['issues'])
                if result.get('recommendations'):
                    validation_report['recommendations'].extend(result['recommendations'])
                    
            except Exception as e:
                logger.error(f"Error in validation check {check.__name__}: {str(e)}")
                validation_report['issues'].append(f"Validation check {check.__name__} failed: {str(e)}")
        
        # Calculate overall quality score
        validation_report['data_quality_score'] = (total_score / max_score) * 100
        
        # Determine overall status
        if validation_report['data_quality_score'] >= 90:
            validation_report['overall_status'] = 'excellent'
        elif validation_report['data_quality_score'] >= 80:
            validation_report['overall_status'] = 'good'
        elif validation_report['data_quality_score'] >= 70:
            validation_report['overall_status'] = 'fair'
        else:
            validation_report['overall_status'] = 'poor'
        
        # Generate summary
        validation_report['summary'] = {
            'total_checks': len(checks),
            'passed_checks': len([r for r in validation_report['validation_results'].values() if r.get('status') == 'passed']),
            'failed_checks': len([r for r in validation_report['validation_results'].values() if r.get('status') == 'failed']),
            'total_issues': len(validation_report['issues']),
            'total_recommendations': len(validation_report['recommendations'])
        }
        
        logger.info(f"Validation completed. Overall status: {validation_report['overall_status']}")
        logger.info(f"Quality score: {validation_report['data_quality_score']:.1f}%")
        
        return validation_report
    
    def _validate_data_structure(self) -> Dict[str, Any]:
        """Validate data structure and schema"""
        logger.info("Validating data structure...")
        
        result = {
            'check_name': 'Data Structure Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            
            # Check required top-level keys
            required_keys = ['metadata', 'national_data', 'age_groups', 'education_levels', 'metro_areas']
            missing_keys = [key for key in required_keys if key not in fallback_data]
            
            if missing_keys:
                result['issues'].append(f"Missing required top-level keys: {missing_keys}")
                result['score'] = 0
                result['status'] = 'failed'
                return result
            
            # Check metadata structure
            metadata = fallback_data.get('metadata', {})
            required_metadata = ['version', 'data_year', 'source', 'last_updated']
            missing_metadata = [key for key in required_metadata if key not in metadata]
            
            if missing_metadata:
                result['issues'].append(f"Missing required metadata: {missing_metadata}")
                result['score'] = 50
                result['status'] = 'failed'
                return result
            
            # Check data point structure
            required_data_fields = ['median_income', 'sample_size', 'standard_error', 'confidence_interval']
            
            for category in ['national_data', 'age_groups', 'education_levels']:
                if category in fallback_data:
                    for group_name, group_data in fallback_data[category].items():
                        if isinstance(group_data, dict):
                            for race, data_point in group_data.items():
                                if isinstance(data_point, dict):
                                    missing_fields = [field for field in required_data_fields if field not in data_point]
                                    if missing_fields:
                                        result['issues'].append(f"Missing fields in {category}/{group_name}/{race}: {missing_fields}")
            
            # Check metro areas structure
            if 'metro_areas' in fallback_data:
                for metro, metro_data in fallback_data['metro_areas'].items():
                    if isinstance(metro_data, dict):
                        for race, data_point in metro_data.items():
                            if isinstance(data_point, dict):
                                missing_fields = [field for field in required_data_fields if field not in data_point]
                                if missing_fields:
                                    result['issues'].append(f"Missing fields in metro_areas/{metro}/{race}: {missing_fields}")
            
            if result['issues']:
                result['score'] = 50
                result['status'] = 'failed'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("Data structure is valid and complete")
            
        except Exception as e:
            result['issues'].append(f"Error validating data structure: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_data_completeness(self) -> Dict[str, Any]:
        """Validate data completeness across all demographic groups"""
        logger.info("Validating data completeness...")
        
        result = {
            'check_name': 'Data Completeness Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            
            # Required demographic groups
            required_races = ['african_american', 'white', 'hispanic_latino', 'asian']
            required_age_groups = ['25-34', '35-44']
            required_education_levels = ['high_school', 'bachelors', 'masters']
            required_metro_areas = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City', 
                                  'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore']
            
            missing_data = []
            
            # Check national data
            national_data = fallback_data.get('national_data', {})
            for race in required_races:
                if race not in national_data:
                    missing_data.append(f"national_data/{race}")
            
            # Check age groups
            age_groups = fallback_data.get('age_groups', {})
            for age_group in required_age_groups:
                if age_group not in age_groups:
                    missing_data.append(f"age_groups/{age_group}")
                else:
                    for race in required_races:
                        if race not in age_groups[age_group]:
                            missing_data.append(f"age_groups/{age_group}/{race}")
            
            # Check education levels
            education_levels = fallback_data.get('education_levels', {})
            for education in required_education_levels:
                if education not in education_levels:
                    missing_data.append(f"education_levels/{education}")
                else:
                    for race in required_races:
                        if race not in education_levels[education]:
                            missing_data.append(f"education_levels/{education}/{race}")
            
            # Check metro areas
            metro_areas = fallback_data.get('metro_areas', {})
            for metro in required_metro_areas:
                if metro not in metro_areas:
                    missing_data.append(f"metro_areas/{metro}")
                else:
                    for race in required_races:
                        if race not in metro_areas[metro]:
                            missing_data.append(f"metro_areas/{metro}/{race}")
            
            if missing_data:
                result['issues'].extend([f"Missing data: {item}" for item in missing_data])
                result['score'] = max(0, 100 - (len(missing_data) * 5))  # 5 points per missing item
                result['status'] = 'failed' if len(missing_data) > 10 else 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("All required demographic data is present")
            
        except Exception as e:
            result['issues'].append(f"Error validating data completeness: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_data_consistency(self) -> Dict[str, Any]:
        """Validate data consistency and logical relationships"""
        logger.info("Validating data consistency...")
        
        result = {
            'check_name': 'Data Consistency Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            
            # Check for logical inconsistencies
            inconsistencies = []
            
            # Check that income values are positive
            for category in ['national_data', 'age_groups', 'education_levels', 'metro_areas']:
                if category in fallback_data:
                    for group_name, group_data in fallback_data[category].items():
                        if isinstance(group_data, dict):
                            for race, data_point in group_data.items():
                                if isinstance(data_point, dict) and 'median_income' in data_point:
                                    income = data_point['median_income']
                                    if income <= 0:
                                        inconsistencies.append(f"Non-positive income in {category}/{group_name}/{race}: {income}")
            
            # Check that education level incomes follow expected pattern (higher education = higher income)
            education_levels = fallback_data.get('education_levels', {})
            for race in ['african_american', 'white', 'hispanic_latino', 'asian']:
                if race in education_levels.get('high_school', {}) and race in education_levels.get('bachelors', {}):
                    hs_income = education_levels['high_school'][race].get('median_income', 0)
                    ba_income = education_levels['bachelors'][race].get('median_income', 0)
                    if hs_income >= ba_income:
                        inconsistencies.append(f"Education income pattern violated for {race}: HS({hs_income}) >= BA({ba_income})")
                
                if race in education_levels.get('bachelors', {}) and race in education_levels.get('masters', {}):
                    ba_income = education_levels['bachelors'][race].get('median_income', 0)
                    ma_income = education_levels['masters'][race].get('median_income', 0)
                    if ba_income >= ma_income:
                        inconsistencies.append(f"Education income pattern violated for {race}: BA({ba_income}) >= MA({ma_income})")
            
            # Check that age group incomes follow expected pattern (older = higher income)
            age_groups = fallback_data.get('age_groups', {})
            for race in ['african_american', 'white', 'hispanic_latino', 'asian']:
                if race in age_groups.get('25-34', {}) and race in age_groups.get('35-44', {}):
                    young_income = age_groups['25-34'][race].get('median_income', 0)
                    older_income = age_groups['35-44'][race].get('median_income', 0)
                    if young_income > older_income * 1.1:  # Allow some variation
                        inconsistencies.append(f"Age income pattern violated for {race}: 25-34({young_income}) > 35-44({older_income})")
            
            if inconsistencies:
                result['issues'].extend(inconsistencies)
                result['score'] = max(0, 100 - (len(inconsistencies) * 10))  # 10 points per inconsistency
                result['status'] = 'failed' if len(inconsistencies) > 5 else 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("Data consistency checks passed")
            
        except Exception as e:
            result['issues'].append(f"Error validating data consistency: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_data_freshness(self) -> Dict[str, Any]:
        """Validate data freshness and update frequency"""
        logger.info("Validating data freshness...")
        
        result = {
            'check_name': 'Data Freshness Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            metadata = fallback_data.get('metadata', {})
            
            # Check data year
            data_year = metadata.get('data_year', 2020)
            current_year = datetime.now().year
            
            if data_year < current_year - 2:
                result['issues'].append(f"Data is from {data_year}, more than 2 years old")
                result['score'] = 50
                result['status'] = 'failed'
            elif data_year < current_year - 1:
                result['issues'].append(f"Data is from {data_year}, consider updating to {current_year}")
                result['score'] = 75
                result['status'] = 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append(f"Data is current (from {data_year})")
            
            # Check last updated timestamp
            last_updated = metadata.get('last_updated')
            if last_updated:
                try:
                    update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    days_since_update = (datetime.now() - update_date).days
                    
                    if days_since_update > 365:
                        result['issues'].append(f"Data was last updated {days_since_update} days ago")
                        result['recommendations'].append("Consider updating data annually")
                    elif days_since_update > 180:
                        result['issues'].append(f"Data was last updated {days_since_update} days ago")
                except Exception as e:
                    result['issues'].append(f"Invalid last_updated timestamp: {last_updated}")
            
        except Exception as e:
            result['issues'].append(f"Error validating data freshness: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_statistical_quality(self) -> Dict[str, Any]:
        """Validate statistical quality of income data"""
        logger.info("Validating statistical quality...")
        
        result = {
            'check_name': 'Statistical Quality Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            
            # Check sample sizes
            small_samples = []
            for category in ['national_data', 'age_groups', 'education_levels', 'metro_areas']:
                if category in fallback_data:
                    for group_name, group_data in fallback_data[category].items():
                        if isinstance(group_data, dict):
                            for race, data_point in group_data.items():
                                if isinstance(data_point, dict) and 'sample_size' in data_point:
                                    sample_size = data_point['sample_size']
                                    if sample_size < 1000:
                                        small_samples.append(f"{category}/{group_name}/{race}: {sample_size}")
            
            if small_samples:
                result['issues'].extend([f"Small sample size: {item}" for item in small_samples])
                result['score'] = max(0, 100 - (len(small_samples) * 5))
                result['status'] = 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("All sample sizes are adequate")
            
            # Check confidence intervals
            invalid_intervals = []
            for category in ['national_data', 'age_groups', 'education_levels', 'metro_areas']:
                if category in fallback_data:
                    for group_name, group_data in fallback_data[category].items():
                        if isinstance(group_data, dict):
                            for race, data_point in group_data.items():
                                if isinstance(data_point, dict) and 'confidence_interval' in data_point:
                                    interval = data_point['confidence_interval']
                                    median = data_point.get('median_income', 0)
                                    if len(interval) == 2:
                                        lower, upper = interval
                                        if lower >= upper or median < lower or median > upper:
                                            invalid_intervals.append(f"{category}/{group_name}/{race}")
            
            if invalid_intervals:
                result['issues'].extend([f"Invalid confidence interval: {item}" for item in invalid_intervals])
                result['score'] = max(0, result['score'] - (len(invalid_intervals) * 10))
                result['status'] = 'failed' if result['score'] < 50 else 'partial'
            
        except Exception as e:
            result['issues'].append(f"Error validating statistical quality: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_geographic_coverage(self) -> Dict[str, Any]:
        """Validate geographic coverage of metro areas"""
        logger.info("Validating geographic coverage...")
        
        result = {
            'check_name': 'Geographic Coverage Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            metro_areas = fallback_data.get('metro_areas', {})
            
            # Check target metro areas
            target_metros = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City', 
                           'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore']
            
            missing_metros = [metro for metro in target_metros if metro not in metro_areas]
            
            if missing_metros:
                result['issues'].append(f"Missing target metro areas: {missing_metros}")
                result['score'] = max(0, 100 - (len(missing_metros) * 10))
                result['status'] = 'failed' if len(missing_metros) > 3 else 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("All target metro areas are covered")
            
            # Check for additional metro areas
            additional_metros = [metro for metro in metro_areas.keys() if metro not in target_metros]
            if additional_metros:
                result['recommendations'].append(f"Additional metro areas available: {additional_metros}")
            
        except Exception as e:
            result['issues'].append(f"Error validating geographic coverage: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def _validate_demographic_coverage(self) -> Dict[str, Any]:
        """Validate demographic coverage across all categories"""
        logger.info("Validating demographic coverage...")
        
        result = {
            'check_name': 'Demographic Coverage Validation',
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            fallback_data = self.data_manager.fallback_data
            
            # Check racial/ethnic coverage
            required_races = ['african_american', 'white', 'hispanic_latino', 'asian']
            
            for category in ['national_data', 'age_groups', 'education_levels', 'metro_areas']:
                if category in fallback_data:
                    for group_name, group_data in fallback_data[category].items():
                        if isinstance(group_data, dict):
                            missing_races = [race for race in required_races if race not in group_data]
                            if missing_races:
                                result['issues'].append(f"Missing races in {category}/{group_name}: {missing_races}")
            
            # Check age group coverage
            age_groups = fallback_data.get('age_groups', {})
            if not age_groups:
                result['issues'].append("No age group data available")
            else:
                result['recommendations'].append(f"Age groups covered: {list(age_groups.keys())}")
            
            # Check education level coverage
            education_levels = fallback_data.get('education_levels', {})
            if not education_levels:
                result['issues'].append("No education level data available")
            else:
                result['recommendations'].append(f"Education levels covered: {list(education_levels.keys())}")
            
            if result['issues']:
                result['score'] = max(0, 100 - (len(result['issues']) * 15))
                result['status'] = 'failed' if len(result['issues']) > 3 else 'partial'
            else:
                result['score'] = 100
                result['status'] = 'passed'
                result['recommendations'].append("All required demographic categories are covered")
            
        except Exception as e:
            result['issues'].append(f"Error validating demographic coverage: {str(e)}")
            result['score'] = 0
            result['status'] = 'failed'
        
        return result
    
    def generate_update_report(self) -> Dict[str, Any]:
        """Generate report for data updates"""
        logger.info("Generating update report...")
        
        validation_report = self.validate_all_data()
        
        update_report = {
            'timestamp': datetime.now().isoformat(),
            'current_data_year': validation_report['validation_results'].get('_validate_data_freshness', {}).get('data_year', 'unknown'),
            'recommended_updates': [],
            'priority_updates': [],
            'update_procedures': []
        }
        
        # Analyze issues and create recommendations
        for issue in validation_report.get('issues', []):
            if 'missing' in issue.lower():
                update_report['recommended_updates'].append(issue)
            elif 'old' in issue.lower() or 'outdated' in issue.lower():
                update_report['priority_updates'].append(issue)
            elif 'inconsistent' in issue.lower():
                update_report['priority_updates'].append(issue)
        
        # Add update procedures
        update_report['update_procedures'] = [
            "1. Download latest ACS 5-Year Estimates from Census Bureau",
            "2. Extract median household income by race, age, education, and metro area",
            "3. Calculate standard errors and confidence intervals",
            "4. Validate data consistency and logical relationships",
            "5. Update fallback_income_data.json with new data",
            "6. Update metadata with new data year and timestamp",
            "7. Run validation script to ensure data quality",
            "8. Test income comparison functionality with new data"
        ]
        
        return update_report
    
    def save_validation_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save validation report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"income_data_validation_report_{timestamp}.json"
        
        report_file = self.data_dir / filename
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Validation report saved to {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Error saving validation report: {str(e)}")
            return ""

def main():
    """Main function for data validation"""
    print("🔍 INCOME DATA VALIDATION SYSTEM")
    print("=" * 50)
    
    validator = IncomeDataValidator()
    
    # Run comprehensive validation
    print("\nRunning comprehensive data validation...")
    validation_report = validator.validate_all_data()
    
    # Print summary
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"Overall Status: {validation_report['overall_status'].upper()}")
    print(f"Quality Score: {validation_report['data_quality_score']:.1f}%")
    print(f"Total Issues: {len(validation_report['issues'])}")
    print(f"Total Recommendations: {len(validation_report['recommendations'])}")
    
    # Print issues
    if validation_report['issues']:
        print(f"\n❌ ISSUES FOUND:")
        for issue in validation_report['issues'][:10]:  # Show first 10 issues
            print(f"  • {issue}")
        if len(validation_report['issues']) > 10:
            print(f"  ... and {len(validation_report['issues']) - 10} more issues")
    
    # Print recommendations
    if validation_report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in validation_report['recommendations'][:10]:  # Show first 10 recommendations
            print(f"  • {rec}")
        if len(validation_report['recommendations']) > 10:
            print(f"  ... and {len(validation_report['recommendations']) - 10} more recommendations")
    
    # Generate update report
    print(f"\n📋 GENERATING UPDATE REPORT...")
    update_report = validator.generate_update_report()
    
    # Save reports
    validation_file = validator.save_validation_report(validation_report)
    update_file = validator.save_validation_report(update_report, "income_data_update_report.json")
    
    print(f"\n✅ REPORTS SAVED:")
    print(f"  Validation Report: {validation_file}")
    print(f"  Update Report: {update_file}")
    
    print(f"\n🎯 NEXT STEPS:")
    if validation_report['overall_status'] in ['poor', 'fair']:
        print("  • Address critical issues identified in validation report")
        print("  • Update data to latest ACS estimates")
        print("  • Re-run validation after updates")
    else:
        print("  • Data quality is acceptable")
        print("  • Consider annual updates to maintain freshness")
        print("  • Monitor for new Census Bureau data releases")

if __name__ == "__main__":
    main() 