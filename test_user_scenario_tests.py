#!/usr/bin/env python3
"""
Location-Specific User Scenario Tests for Target Demographics
Tests African American professionals 25-35 years old across different locations
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from backend.utils.location_utils import LocationValidator, LocationService
from backend.utils.income_boost_job_matcher import IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel
from backend.utils.three_tier_job_selector import ThreeTierJobSelector, JobTier

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile for scenario testing"""
    age: int
    ethnicity: str
    current_salary: int
    career_field: CareerField
    experience_level: ExperienceLevel
    zipcode: str
    search_radius: int
    commute_preference: str
    remote_ok: bool
    target_salary_increase: float

class UserScenarioTestFramework:
    """
    User scenario testing framework for location-specific recommendations
    """
    
    def __init__(self, db_path: str = "test_location_recommendations.db"):
        self.db_path = db_path
        self.location_validator = LocationValidator()
        self.location_service = LocationService()
        self.job_matcher = IncomeBoostJobMatcher(db_path)
        self.three_tier_selector = ThreeTierJobSelector(db_path)
        
        # Target demographic profiles
        self.target_demographics = self._create_target_demographics()
        
        # Metro area scenarios
        self.metro_scenarios = self._create_metro_scenarios()
    
    def _create_target_demographics(self) -> List[UserProfile]:
        """Create target demographic profiles for African American professionals 25-35"""
        profiles = []
        
        # Base profiles for different career fields and experience levels
        base_profiles = [
            {
                'age': 28,
                'current_salary': 75000,
                'career_field': CareerField.TECHNOLOGY,
                'experience_level': ExperienceLevel.MID,
                'target_salary_increase': 0.25
            },
            {
                'age': 32,
                'current_salary': 95000,
                'career_field': CareerField.FINANCE,
                'experience_level': ExperienceLevel.SENIOR,
                'target_salary_increase': 0.30
            },
            {
                'age': 26,
                'current_salary': 65000,
                'career_field': CareerField.MARKETING,
                'experience_level': ExperienceLevel.MID,
                'target_salary_increase': 0.20
            },
            {
                'age': 30,
                'current_salary': 85000,
                'career_field': CareerField.HEALTHCARE,
                'experience_level': ExperienceLevel.SENIOR,
                'target_salary_increase': 0.25
            },
            {
                'age': 29,
                'current_salary': 70000,
                'career_field': CareerField.ENGINEERING,
                'experience_level': ExperienceLevel.MID,
                'target_salary_increase': 0.30
            }
        ]
        
        # Create profiles for each metro area
        metro_zipcodes = {
            'Atlanta': ['30309', '30024', '30144'],
            'Houston': ['77002', '77494', '77573'],
            'DC_Metro': ['20001', '22101', '20852'],
            'Dallas': ['75201', '75024', '76102'],
            'NYC': ['10001', '07030', '11201'],
            'Philadelphia': ['19103', '19087', '08540'],
            'Chicago': ['60601', '60614', '60187'],
            'Charlotte': ['28202', '28277', '28078'],
            'Miami': ['33131', '33186', '33441'],
            'Baltimore': ['21201', '21044', '21740']
        }
        
        for metro, zipcodes in metro_zipcodes.items():
            for zipcode in zipcodes:
                for base_profile in base_profiles:
                    # Vary search radius and commute preferences
                    search_radius = random.choice([5, 10, 30])
                    commute_preference = random.choice(['short', 'medium', 'long'])
                    remote_ok = random.choice([True, False])
                    
                    profiles.append(UserProfile(
                        age=base_profile['age'],
                        ethnicity='African American',
                        current_salary=base_profile['current_salary'],
                        career_field=base_profile['career_field'],
                        experience_level=base_profile['experience_level'],
                        zipcode=zipcode,
                        search_radius=search_radius,
                        commute_preference=commute_preference,
                        remote_ok=remote_ok,
                        target_salary_increase=base_profile['target_salary_increase']
                    ))
        
        return profiles
    
    def _create_metro_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create specific scenarios for each metro area"""
        return {
            'Atlanta': {
                'description': 'Urban vs suburban zipcode scenarios in Atlanta metro',
                'test_zipcodes': ['30309', '30024', '30144'],
                'radius_scenarios': [5, 10, 30],
                'expected_opportunities': 'High tech and finance opportunities',
                'cost_of_living_factor': 1.1
            },
            'Houston': {
                'description': 'Energy sector and diverse opportunities in Houston',
                'test_zipcodes': ['77002', '77494', '77573'],
                'radius_scenarios': [5, 15, 30],
                'expected_opportunities': 'Energy, healthcare, and technology',
                'cost_of_living_factor': 1.05
            },
            'DC_Metro': {
                'description': 'Cross-state boundary testing in DC metro area',
                'test_zipcodes': ['20001', '22101', '20852'],
                'radius_scenarios': [5, 10, 25],
                'expected_opportunities': 'Government, consulting, and tech',
                'cost_of_living_factor': 1.32
            },
            'Dallas': {
                'description': 'Sprawl handling in Dallas-Fort Worth metro',
                'test_zipcodes': ['75201', '75024', '76102'],
                'radius_scenarios': [10, 20, 40],
                'expected_opportunities': 'Technology, finance, and healthcare',
                'cost_of_living_factor': 1.05
            },
            'NYC': {
                'description': 'High-density testing in NYC metro',
                'test_zipcodes': ['10001', '07030', '11201'],
                'radius_scenarios': [5, 10, 20],
                'expected_opportunities': 'Finance, tech, media, and consulting',
                'cost_of_living_factor': 1.4
            },
            'Philadelphia': {
                'description': 'Cross-state testing in Philadelphia metro',
                'test_zipcodes': ['19103', '19087', '08540'],
                'radius_scenarios': [5, 15, 30],
                'expected_opportunities': 'Healthcare, education, and finance',
                'cost_of_living_factor': 1.1
            },
            'Chicago': {
                'description': 'Metro boundary testing in Chicago',
                'test_zipcodes': ['60601', '60614', '60187'],
                'radius_scenarios': [5, 15, 30],
                'expected_opportunities': 'Technology, finance, and manufacturing',
                'cost_of_living_factor': 1.1
            },
            'Charlotte': {
                'description': 'Cross-state testing in Charlotte metro',
                'test_zipcodes': ['28202', '28277', '28078'],
                'radius_scenarios': [5, 15, 25],
                'expected_opportunities': 'Banking, technology, and healthcare',
                'cost_of_living_factor': 1.0
            },
            'Miami': {
                'description': 'Coastal geography testing in Miami',
                'test_zipcodes': ['33131', '33186', '33441'],
                'radius_scenarios': [5, 20, 35],
                'expected_opportunities': 'Tourism, finance, and international business',
                'cost_of_living_factor': 1.0
            },
            'Baltimore': {
                'description': 'Proximity to DC testing in Baltimore',
                'test_zipcodes': ['21201', '21044', '21740'],
                'radius_scenarios': [5, 15, 30],
                'expected_opportunities': 'Healthcare, government, and technology',
                'cost_of_living_factor': 1.05
            }
        }
    
    async def run_user_scenario_tests(self) -> Dict[str, Any]:
        """Run comprehensive user scenario tests"""
        logger.info("Starting user scenario tests for target demographics...")
        
        results = {
            'start_time': datetime.now(),
            'demographic_tests': {},
            'metro_scenario_tests': {},
            'radius_preference_tests': {},
            'remote_work_tests': {},
            'cost_of_living_tests': {},
            'overall_score': 0.0,
            'total_scenarios': 0,
            'passed_scenarios': 0
        }
        
        try:
            # 1. Demographic-specific tests
            results['demographic_tests'] = await self._test_demographic_scenarios()
            
            # 2. Metro area scenario tests
            results['metro_scenario_tests'] = await self._test_metro_scenarios()
            
            # 3. Radius preference tests
            results['radius_preference_tests'] = await self._test_radius_preferences()
            
            # 4. Remote work preference tests
            results['remote_work_tests'] = await self._test_remote_work_preferences()
            
            # 5. Cost of living adjustment tests
            results['cost_of_living_tests'] = await self._test_cost_of_living_adjustments()
            
            # Calculate overall results
            results = self._calculate_scenario_results(results)
            
        except Exception as e:
            logger.error(f"Error running user scenario tests: {e}")
            results['error'] = str(e)
        
        results['end_time'] = datetime.now()
        results['total_duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        return results
    
    async def _test_demographic_scenarios(self) -> Dict[str, Any]:
        """Test scenarios for African American professionals 25-35"""
        logger.info("Testing demographic scenarios...")
        
        results = {
            'age_group_tests': await self._test_age_group_scenarios(),
            'salary_expectation_tests': await self._test_salary_expectations(),
            'career_field_tests': await self._test_career_field_scenarios(),
            'experience_level_tests': await self._test_experience_level_scenarios()
        }
        
        return results
    
    async def _test_age_group_scenarios(self) -> Dict[str, Any]:
        """Test scenarios for 25-35 age group"""
        start_time = time.time()
        
        # Test different age groups within target range
        age_groups = [25, 28, 30, 32, 35]
        passed = 0
        total = 0
        errors = []
        
        for age in age_groups:
            try:
                # Create test profile
                profile = UserProfile(
                    age=age,
                    ethnicity='African American',
                    current_salary=75000,
                    career_field=CareerField.TECHNOLOGY,
                    experience_level=ExperienceLevel.MID,
                    zipcode='10001',
                    search_radius=10,
                    commute_preference='medium',
                    remote_ok=True,
                    target_salary_increase=0.25
                )
                
                # Test recommendation generation
                criteria = SearchCriteria(
                    current_salary=profile.current_salary,
                    target_salary_increase=profile.target_salary_increase,
                    career_field=profile.career_field,
                    experience_level=profile.experience_level,
                    preferred_msas=[],
                    remote_ok=profile.remote_ok
                )
                
                # Generate recommendations
                recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                    criteria, max_recommendations_per_tier=3
                )
                
                total += 1
                
                # Check if recommendations are appropriate for age group
                if self._validate_age_appropriate_recommendations(recommendations, age):
                    passed += 1
                else:
                    errors.append(f"Age {age}: Inappropriate recommendations")
                
            except Exception as e:
                errors.append(f"Age {age}: {e}")
        
        score = (passed / total) * 100 if total > 0 else 0
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'age_group_scenarios',
            'passed': score >= 90,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_salary_expectations(self) -> Dict[str, Any]:
        """Test salary expectations for target demographic"""
        start_time = time.time()
        
        # Test different salary scenarios
        salary_scenarios = [
            {'current': 60000, 'expected_increase': 0.20, 'target': 72000},
            {'current': 75000, 'expected_increase': 0.25, 'target': 93750},
            {'current': 90000, 'expected_increase': 0.30, 'target': 117000},
            {'current': 110000, 'expected_increase': 0.35, 'target': 148500}
        ]
        
        passed = 0
        total = len(salary_scenarios)
        errors = []
        
        for scenario in salary_scenarios:
            try:
                # Create search criteria
                criteria = SearchCriteria(
                    current_salary=scenario['current'],
                    target_salary_increase=scenario['expected_increase'],
                    career_field=CareerField.TECHNOLOGY,
                    experience_level=ExperienceLevel.MID,
                    preferred_msas=[],
                    remote_ok=True
                )
                
                # Generate recommendations
                recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                    criteria, max_recommendations_per_tier=2
                )
                
                # Check if recommendations meet salary expectations
                if self._validate_salary_expectations(recommendations, scenario):
                    passed += 1
                else:
                    errors.append(f"Salary scenario {scenario['current']}: Expectations not met")
                
            except Exception as e:
                errors.append(f"Salary scenario {scenario['current']}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'salary_expectations',
            'passed': score >= 85,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_career_field_scenarios(self) -> Dict[str, Any]:
        """Test scenarios across different career fields"""
        start_time = time.time()
        
        career_fields = [
            CareerField.TECHNOLOGY,
            CareerField.FINANCE,
            CareerField.HEALTHCARE,
            CareerField.MARKETING,
            CareerField.ENGINEERING
        ]
        
        passed = 0
        total = len(career_fields)
        errors = []
        
        for field in career_fields:
            try:
                # Create search criteria for each field
                criteria = SearchCriteria(
                    current_salary=75000,
                    target_salary_increase=0.25,
                    career_field=field,
                    experience_level=ExperienceLevel.MID,
                    preferred_msas=[],
                    remote_ok=True
                )
                
                # Generate recommendations
                recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                    criteria, max_recommendations_per_tier=2
                )
                
                # Check if recommendations are field-appropriate
                if self._validate_field_appropriate_recommendations(recommendations, field):
                    passed += 1
                else:
                    errors.append(f"Career field {field.value}: Inappropriate recommendations")
                
            except Exception as e:
                errors.append(f"Career field {field.value}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'career_field_scenarios',
            'passed': score >= 85,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_experience_level_scenarios(self) -> Dict[str, Any]:
        """Test scenarios for different experience levels"""
        start_time = time.time()
        
        experience_levels = [
            ExperienceLevel.ENTRY,
            ExperienceLevel.MID,
            ExperienceLevel.SENIOR,
            ExperienceLevel.EXECUTIVE
        ]
        
        passed = 0
        total = len(experience_levels)
        errors = []
        
        for level in experience_levels:
            try:
                # Create search criteria for each experience level
                criteria = SearchCriteria(
                    current_salary=75000,
                    target_salary_increase=0.25,
                    career_field=CareerField.TECHNOLOGY,
                    experience_level=level,
                    preferred_msas=[],
                    remote_ok=True
                )
                
                # Generate recommendations
                recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                    criteria, max_recommendations_per_tier=2
                )
                
                # Check if recommendations are level-appropriate
                if self._validate_experience_level_recommendations(recommendations, level):
                    passed += 1
                else:
                    errors.append(f"Experience level {level.value}: Inappropriate recommendations")
                
            except Exception as e:
                errors.append(f"Experience level {level.value}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'experience_level_scenarios',
            'passed': score >= 85,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_metro_scenarios(self) -> Dict[str, Any]:
        """Test scenarios for each metro area"""
        logger.info("Testing metro area scenarios...")
        
        results = {}
        
        for metro_name, scenario in self.metro_scenarios.items():
            try:
                metro_result = await self._test_single_metro_scenario(metro_name, scenario)
                results[metro_name] = metro_result
            except Exception as e:
                results[metro_name] = {
                    'error': str(e),
                    'passed': False,
                    'score': 0
                }
        
        return results
    
    async def _test_single_metro_scenario(self, metro_name: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single metro area scenario"""
        start_time = time.time()
        
        passed = 0
        total = 0
        errors = []
        
        # Test each zipcode in the metro area
        for zipcode in scenario['test_zipcodes']:
            try:
                # Test each radius scenario
                for radius in scenario['radius_scenarios']:
                    # Create search criteria
                    criteria = SearchCriteria(
                        current_salary=75000,
                        target_salary_increase=0.25,
                        career_field=CareerField.TECHNOLOGY,
                        experience_level=ExperienceLevel.MID,
                        preferred_msas=[],
                        remote_ok=True
                    )
                    
                    # Test location validation
                    location_data = self.location_validator.geocode_zipcode(zipcode)
                    if not location_data:
                        errors.append(f"Could not geocode {zipcode}")
                        continue
                    
                    # Test distance calculations
                    center_zipcode = scenario['test_zipcodes'][0]  # Use first as center
                    distance = self.location_validator.calculate_distance(center_zipcode, zipcode)
                    
                    if distance is not None:
                        # Check if distance is within expected radius
                        if distance <= radius:
                            passed += 1
                        else:
                            errors.append(f"Distance {distance:.1f} miles exceeds radius {radius} for {zipcode}")
                    else:
                        errors.append(f"Could not calculate distance for {zipcode}")
                    
                    total += 1
                
            except Exception as e:
                errors.append(f"Metro {metro_name}, zipcode {zipcode}: {e}")
        
        score = (passed / total) * 100 if total > 0 else 0
        execution_time = time.time() - start_time
        
        return {
            'test_name': f'metro_{metro_name.lower()}',
            'passed': score >= 90,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time,
            'description': scenario['description']
        }
    
    async def _test_radius_preferences(self) -> Dict[str, Any]:
        """Test different radius preferences (5-mile downtown vs 30-mile suburban)"""
        start_time = time.time()
        
        # Test scenarios for different radius preferences
        radius_scenarios = [
            {
                'zipcode': '10001',  # NYC downtown
                'radius': 5,
                'description': '5-mile downtown radius'
            },
            {
                'zipcode': '07030',  # Hoboken, NJ
                'radius': 10,
                'description': '10-mile suburban radius'
            },
            {
                'zipcode': '30024',  # Duluth, GA
                'radius': 30,
                'description': '30-mile suburban radius'
            }
        ]
        
        passed = 0
        total = len(radius_scenarios)
        errors = []
        
        for scenario in radius_scenarios:
            try:
                # Test radius filtering
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get all jobs in the area
                cursor.execute('''
                    SELECT job_id, zipcode FROM test_job_opportunities 
                    WHERE zipcode IS NOT NULL
                ''')
                
                jobs = cursor.fetchall()
                conn.close()
                
                # Filter jobs by radius
                jobs_within_radius = 0
                total_jobs = len(jobs)
                
                for job_id, job_zipcode in jobs:
                    distance = self.location_validator.calculate_distance(
                        scenario['zipcode'], job_zipcode
                    )
                    
                    if distance is not None and distance <= scenario['radius']:
                        jobs_within_radius += 1
                
                # Check if radius filtering is working
                if jobs_within_radius > 0:
                    passed += 1
                else:
                    errors.append(f"Radius {scenario['radius']} miles: No jobs found for {scenario['zipcode']}")
                
            except Exception as e:
                errors.append(f"Radius scenario {scenario['zipcode']}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'radius_preferences',
            'passed': score >= 90,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_remote_work_preferences(self) -> Dict[str, Any]:
        """Test remote work preference combinations"""
        start_time = time.time()
        
        # Test scenarios for remote work preferences
        remote_scenarios = [
            {'remote_ok': True, 'zipcode': '10001', 'description': 'Remote OK in NYC'},
            {'remote_ok': False, 'zipcode': '77002', 'description': 'No remote in Houston'},
            {'remote_ok': True, 'zipcode': '30309', 'description': 'Remote OK in Atlanta'}
        ]
        
        passed = 0
        total = len(remote_scenarios)
        errors = []
        
        for scenario in remote_scenarios:
            try:
                # Create search criteria
                criteria = SearchCriteria(
                    current_salary=75000,
                    target_salary_increase=0.25,
                    career_field=CareerField.TECHNOLOGY,
                    experience_level=ExperienceLevel.MID,
                    preferred_msas=[],
                    remote_ok=scenario['remote_ok']
                )
                
                # Generate recommendations
                recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                    criteria, max_recommendations_per_tier=2
                )
                
                # Check if remote work preferences are respected
                if self._validate_remote_work_preferences(recommendations, scenario['remote_ok']):
                    passed += 1
                else:
                    errors.append(f"Remote scenario {scenario['zipcode']}: Preferences not respected")
                
            except Exception as e:
                errors.append(f"Remote scenario {scenario['zipcode']}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'remote_work_preferences',
            'passed': score >= 85,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    async def _test_cost_of_living_adjustments(self) -> Dict[str, Any]:
        """Test cost of living adjustment scenarios across metros"""
        start_time = time.time()
        
        # Test cost of living adjustments for different metros
        col_scenarios = [
            {'zipcode': '10001', 'expected_factor': 1.4, 'description': 'High COL NYC'},
            {'zipcode': '77002', 'expected_factor': 1.05, 'description': 'Medium COL Houston'},
            {'zipcode': '30309', 'expected_factor': 1.1, 'description': 'Medium COL Atlanta'},
            {'zipcode': '28202', 'expected_factor': 1.0, 'description': 'Low COL Charlotte'}
        ]
        
        passed = 0
        total = len(col_scenarios)
        errors = []
        
        for scenario in col_scenarios:
            try:
                # Test cost of living adjustment
                base_salary = 75000
                adjustment = self.location_validator.get_salary_adjustment_for_location(
                    base_salary, scenario['zipcode']
                )
                
                if adjustment and 'adjustment_factor' in adjustment:
                    actual_factor = adjustment['adjustment_factor']
                    expected_factor = scenario['expected_factor']
                    
                    # Check if adjustment is within 10% of expected
                    error_percentage = abs(actual_factor - expected_factor) / expected_factor * 100
                    
                    if error_percentage <= 10:
                        passed += 1
                    else:
                        errors.append(f"COL adjustment {scenario['zipcode']}: {error_percentage:.1f}% error")
                else:
                    errors.append(f"COL adjustment {scenario['zipcode']}: No adjustment data")
                
            except Exception as e:
                errors.append(f"COL scenario {scenario['zipcode']}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return {
            'test_name': 'cost_of_living_adjustments',
            'passed': score >= 85,
            'score': score,
            'total_tests': total,
            'passed_tests': passed,
            'errors': errors,
            'execution_time': execution_time
        }
    
    def _validate_age_appropriate_recommendations(self, recommendations: Dict, age: int) -> bool:
        """Validate that recommendations are appropriate for age group"""
        # Check if recommendations exist and are reasonable for age
        if not recommendations:
            return False
        
        # Check if all tiers have appropriate recommendations
        for tier, tier_recommendations in recommendations.items():
            if not tier_recommendations:
                continue
            
            for rec in tier_recommendations:
                # Check if salary increase is appropriate for age
                if hasattr(rec, 'salary_increase_potential'):
                    if age < 30 and rec.salary_increase_potential > 0.4:  # Too high for young age
                        return False
                    if age > 35 and rec.salary_increase_potential < 0.15:  # Too low for experienced
                        return False
        
        return True
    
    def _validate_salary_expectations(self, recommendations: Dict, scenario: Dict) -> bool:
        """Validate that recommendations meet salary expectations"""
        if not recommendations:
            return False
        
        # Check if any recommendation meets salary expectations
        for tier, tier_recommendations in recommendations.items():
            for rec in tier_recommendations:
                if hasattr(rec, 'salary_increase_potential'):
                    if rec.salary_increase_potential >= scenario['expected_increase']:
                        return True
        
        return False
    
    def _validate_field_appropriate_recommendations(self, recommendations: Dict, field: CareerField) -> bool:
        """Validate that recommendations are appropriate for career field"""
        if not recommendations:
            return False
        
        # Check if recommendations are field-appropriate
        for tier, tier_recommendations in recommendations.items():
            for rec in tier_recommendations:
                if hasattr(rec, 'job') and hasattr(rec.job, 'field'):
                    if rec.job.field == field:
                        return True
        
        return True
    
    def _validate_experience_level_recommendations(self, recommendations: Dict, level: ExperienceLevel) -> bool:
        """Validate that recommendations are appropriate for experience level"""
        if not recommendations:
            return False
        
        # Check if recommendations are level-appropriate
        for tier, tier_recommendations in recommendations.items():
            for rec in tier_recommendations:
                if hasattr(rec, 'job') and hasattr(rec.job, 'experience_level'):
                    if rec.job.experience_level == level:
                        return True
        
        return True
    
    def _validate_remote_work_preferences(self, recommendations: Dict, remote_ok: bool) -> bool:
        """Validate that remote work preferences are respected"""
        if not recommendations:
            return False
        
        # If remote is OK, should have some remote opportunities
        if remote_ok:
            for tier, tier_recommendations in recommendations.items():
                for rec in tier_recommendations:
                    if hasattr(rec, 'job') and hasattr(rec.job, 'remote_friendly'):
                        if rec.job.remote_friendly:
                            return True
        
        return True
    
    def _calculate_scenario_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall scenario test results"""
        total_tests = 0
        passed_tests = 0
        total_score = 0.0
        
        # Count tests and calculate scores
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                if 'test_name' in category_results:
                    # Single test result
                    total_tests += 1
                    if category_results.get('passed', False):
                        passed_tests += 1
                    total_score += category_results.get('score', 0)
                else:
                    # Multiple test results
                    for test_name, test_result in category_results.items():
                        if isinstance(test_result, dict) and 'test_name' in test_result:
                            total_tests += 1
                            if test_result.get('passed', False):
                                passed_tests += 1
                            total_score += test_result.get('score', 0)
        
        overall_score = (total_score / total_tests) if total_tests > 0 else 0.0
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0.0
        
        results['overall_score'] = overall_score
        results['total_scenarios'] = total_tests
        results['passed_scenarios'] = passed_tests
        results['pass_rate'] = pass_rate
        
        return results

async def main():
    """Run user scenario tests"""
    framework = UserScenarioTestFramework()
    
    print("👥 Starting User Scenario Tests for Target Demographics")
    print("=" * 60)
    
    results = await framework.run_user_scenario_tests()
    
    print(f"\n📊 USER SCENARIO TEST RESULTS")
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Total Scenarios: {results['total_scenarios']}")
    print(f"Passed: {results['passed_scenarios']}")
    print(f"Pass Rate: {results['pass_rate']:.1f}%")
    print(f"Total Duration: {results['total_duration']:.2f} seconds")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
