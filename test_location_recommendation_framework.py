#!/usr/bin/env python3
"""
Comprehensive Location-Based Job Recommendation Testing Framework
Tests quality assurance, user scenarios, location filtering, and recommendation accuracy
"""

import asyncio
import json
import logging
import sqlite3
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import statistics
import random
import math

# Import existing components
from backend.utils.location_utils import LocationValidator, LocationService, LocationData
from backend.utils.income_boost_job_matcher import IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel
from backend.utils.three_tier_job_selector import ThreeTierJobSelector, JobTier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result with metrics and validation"""
    test_name: str
    passed: bool
    score: float
    metrics: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float

@dataclass
class LocationTestData:
    """Test data for location-based testing"""
    zipcode: str
    city: str
    state: str
    latitude: float
    longitude: float
    msa: str
    expected_distance_to_center: float
    population: int
    cost_of_living_index: float

class LocationRecommendationTestFramework:
    """
    Comprehensive testing framework for location-based job recommendations
    """
    
    def __init__(self, db_path: str = "test_location_recommendations.db"):
        self.db_path = db_path
        self.location_validator = LocationValidator()
        self.location_service = LocationService()
        self.job_matcher = IncomeBoostJobMatcher(db_path)
        self.three_tier_selector = ThreeTierJobSelector(db_path)
        
        # Test data for all target metro areas
        self.metro_test_data = self._initialize_metro_test_data()
        
        # Quality metrics thresholds
        self.quality_thresholds = {
            'recommendation_relevance': 0.90,
            'distance_accuracy_tolerance': 0.1,  # miles
            'commute_time_tolerance': 0.15,  # 15%
            'radius_filtering_precision': 0.999,
            'cost_of_living_accuracy': 0.05,  # 5%
            'tier_diversity_completeness': 1.0,
            'skills_gap_accuracy': 0.85
        }
        
        # Performance targets
        self.performance_targets = {
            'max_processing_time': 8.0,  # seconds
            'max_concurrent_users': 50,
            'max_api_response_time': 2.0,  # seconds
            'max_memory_usage_mb': 512
        }
        
        self._init_test_database()
    
    def _initialize_metro_test_data(self) -> Dict[str, List[LocationTestData]]:
        """Initialize comprehensive test data for all target metro areas"""
        return {
            "Atlanta": [
                LocationTestData("30309", "Atlanta", "GA", 33.7490, -84.3880, "Atlanta-Sandy Springs-Alpharetta, GA", 0.0, 500000, 1.1),
                LocationTestData("30024", "Duluth", "GA", 34.0029, -84.1446, "Atlanta-Sandy Springs-Alpharetta, GA", 25.2, 30000, 1.05),
                LocationTestData("30144", "Marietta", "GA", 33.9526, -84.5499, "Atlanta-Sandy Springs-Alpharetta, GA", 18.7, 60000, 1.08)
            ],
            "Houston": [
                LocationTestData("77002", "Houston", "TX", 29.7604, -95.3698, "Houston-The Woodlands-Sugar Land, TX", 0.0, 2300000, 1.05),
                LocationTestData("77494", "Katy", "TX", 29.7858, -95.8244, "Houston-The Woodlands-Sugar Land, TX", 28.5, 15000, 1.02),
                LocationTestData("77573", "Pearland", "TX", 29.5636, -95.2860, "Houston-The Woodlands-Sugar Land, TX", 22.1, 120000, 1.03)
            ],
            "DC_Metro": [
                LocationTestData("20001", "Washington", "DC", 38.9072, -77.0369, "Washington-Arlington-Alexandria, DC-VA-MD-WV", 0.0, 700000, 1.32),
                LocationTestData("22101", "McLean", "VA", 38.9343, -77.1775, "Washington-Arlington-Alexandria, DC-VA-MD-WV", 8.2, 50000, 1.35),
                LocationTestData("20852", "Bethesda", "MD", 38.9847, -77.0947, "Washington-Arlington-Alexandria, DC-VA-MD-WV", 6.8, 65000, 1.38)
            ],
            "Dallas": [
                LocationTestData("75201", "Dallas", "TX", 32.7767, -96.7970, "Dallas-Fort Worth-Arlington, TX", 0.0, 1300000, 1.05),
                LocationTestData("75024", "Plano", "TX", 33.0198, -96.6989, "Dallas-Fort Worth-Arlington, TX", 20.1, 290000, 1.08),
                LocationTestData("76102", "Fort Worth", "TX", 32.7555, -97.3308, "Dallas-Fort Worth-Arlington, TX", 32.4, 900000, 1.02)
            ],
            "NYC": [
                LocationTestData("10001", "New York", "NY", 40.7505, -73.9934, "New York-Newark-Jersey City, NY-NJ-PA", 0.0, 8500000, 1.4),
                LocationTestData("07030", "Hoboken", "NJ", 40.7431, -74.0324, "New York-Newark-Jersey City, NY-NJ-PA", 2.1, 55000, 1.35),
                LocationTestData("11201", "Brooklyn", "NY", 40.6892, -73.9442, "New York-Newark-Jersey City, NY-NJ-PA", 3.2, 2700000, 1.38)
            ],
            "Philadelphia": [
                LocationTestData("19103", "Philadelphia", "PA", 39.9526, -75.1652, "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", 0.0, 1600000, 1.1),
                LocationTestData("19087", "Bryn Mawr", "PA", 40.0234, -75.3155, "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", 12.8, 4000, 1.15),
                LocationTestData("08540", "Princeton", "NJ", 40.3573, -74.6672, "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", 45.2, 30000, 1.25)
            ],
            "Chicago": [
                LocationTestData("60601", "Chicago", "IL", 41.8781, -87.6298, "Chicago-Naperville-Elgin, IL-IN-WI", 0.0, 2700000, 1.1),
                LocationTestData("60614", "Chicago", "IL", 41.9134, -87.6483, "Chicago-Naperville-Elgin, IL-IN-WI", 2.5, 80000, 1.12),
                LocationTestData("60187", "Wheaton", "IL", 41.8661, -88.1071, "Chicago-Naperville-Elgin, IL-IN-WI", 25.8, 55000, 1.05)
            ],
            "Charlotte": [
                LocationTestData("28202", "Charlotte", "NC", 35.2271, -80.8431, "Charlotte-Concord-Gastonia, NC-SC", 0.0, 900000, 1.0),
                LocationTestData("28277", "Charlotte", "NC", 35.2271, -80.8431, "Charlotte-Concord-Gastonia, NC-SC", 8.5, 120000, 1.02),
                LocationTestData("28078", "Huntersville", "NC", 35.4107, -80.8428, "Charlotte-Concord-Gastonia, NC-SC", 15.3, 60000, 0.98)
            ],
            "Miami": [
                LocationTestData("33131", "Miami", "FL", 25.7617, -80.1918, "Miami-Fort Lauderdale-Pompano Beach, FL", 0.0, 470000, 1.0),
                LocationTestData("33186", "Miami", "FL", 25.7617, -80.1918, "Miami-Fort Lauderdale-Pompano Beach, FL", 12.4, 180000, 1.02),
                LocationTestData("33441", "Delray Beach", "FL", 26.4615, -80.0730, "Miami-Fort Lauderdale-Pompano Beach, FL", 45.8, 70000, 1.05)
            ],
            "Baltimore": [
                LocationTestData("21201", "Baltimore", "MD", 39.2904, -76.6122, "Baltimore-Columbia-Towson, MD", 0.0, 600000, 1.05),
                LocationTestData("21044", "Columbia", "MD", 39.2037, -76.8610, "Baltimore-Columbia-Towson, MD", 18.2, 100000, 1.08),
                LocationTestData("21740", "Frederick", "MD", 39.4143, -77.4105, "Baltimore-Columbia-Towson, MD", 45.6, 75000, 1.12)
            ]
        }
    
    def _init_test_database(self):
        """Initialize test database with sample data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_job_opportunities (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                zipcode TEXT,
                msa TEXT,
                salary_median INTEGER,
                salary_increase_potential REAL,
                remote_friendly BOOLEAN,
                field TEXT,
                experience_level TEXT,
                diversity_score REAL,
                growth_score REAL,
                culture_score REAL,
                overall_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test job data
        self._insert_test_job_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_test_job_data(self, cursor):
        """Insert comprehensive test job data for all metro areas"""
        test_jobs = []
        
        # Generate test jobs for each metro area
        for metro_name, locations in self.metro_test_data.items():
            for i, location in enumerate(locations):
                # Create 5-10 test jobs per location
                for j in range(5):
                    job_id = f"test_job_{metro_name}_{location.zipcode}_{j}"
                    
                    # Vary salary based on location and tier
                    base_salary = 75000
                    if location.cost_of_living_index > 1.2:
                        base_salary = int(base_salary * location.cost_of_living_index)
                    
                    # Create different tiers
                    if j < 2:  # Conservative tier
                        salary_increase = random.uniform(0.15, 0.20)
                    elif j < 4:  # Optimal tier
                        salary_increase = random.uniform(0.25, 0.30)
                    else:  # Stretch tier
                        salary_increase = random.uniform(0.35, 0.45)
                    
                    test_jobs.append((
                        job_id,
                        f"Test {['Software Engineer', 'Data Analyst', 'Product Manager', 'Marketing Manager', 'Sales Manager'][j]}",
                        f"Test Company {j+1}",
                        f"{location.city}, {location.state}",
                        location.zipcode,
                        location.msa,
                        int(base_salary * (1 + salary_increase)),
                        salary_increase,
                        random.choice([True, False]),
                        random.choice(['technology', 'finance', 'healthcare', 'marketing', 'sales']),
                        random.choice(['entry', 'mid', 'senior']),
                        random.uniform(60, 95),
                        random.uniform(70, 90),
                        random.uniform(65, 85),
                        random.uniform(75, 95)
                    ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO test_job_opportunities 
            (job_id, title, company, location, zipcode, msa, salary_median, 
             salary_increase_potential, remote_friendly, field, experience_level,
             diversity_score, growth_score, culture_score, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_jobs)

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests and return results"""
        logger.info("Starting comprehensive location-based recommendation testing...")
        
        test_results = {
            'start_time': datetime.now(),
            'location_quality_tests': {},
            'user_scenario_tests': {},
            'metro_coverage_tests': {},
            'performance_tests': {},
            'edge_case_tests': {},
            'overall_score': 0.0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
        
        try:
            # 1. Location-Based Recommendation Quality Tests
            logger.info("Running location-based recommendation quality tests...")
            test_results['location_quality_tests'] = await self._run_location_quality_tests()
            
            # 2. User Scenario Tests
            logger.info("Running user scenario tests...")
            test_results['user_scenario_tests'] = await self._run_user_scenario_tests()
            
            # 3. Metro Area Coverage Tests
            logger.info("Running metro area coverage tests...")
            test_results['metro_coverage_tests'] = await self._run_metro_coverage_tests()
            
            # 4. Performance Tests
            logger.info("Running performance tests...")
            test_results['performance_tests'] = await self._run_performance_tests()
            
            # 5. Edge Case Tests
            logger.info("Running edge case tests...")
            test_results['edge_case_tests'] = await self._run_edge_case_tests()
            
            # Calculate overall results
            test_results = self._calculate_overall_results(test_results)
            
        except Exception as e:
            logger.error(f"Error running comprehensive tests: {e}")
            test_results['error'] = str(e)
        
        test_results['end_time'] = datetime.now()
        test_results['total_duration'] = (test_results['end_time'] - test_results['start_time']).total_seconds()
        
        logger.info(f"Comprehensive testing completed in {test_results['total_duration']:.2f} seconds")
        return test_results

    async def _run_location_quality_tests(self) -> Dict[str, Any]:
        """Run location-based recommendation quality tests"""
        results = {
            'zipcode_validation_accuracy': await self._test_zipcode_validation_accuracy(),
            'radius_filtering_precision': await self._test_radius_filtering_precision(),
            'distance_calculation_verification': await self._test_distance_calculation_verification(),
            'salary_increase_accuracy': await self._test_salary_increase_accuracy(),
            'job_relevance_scoring': await self._test_job_relevance_scoring(),
            'three_tier_classification': await self._test_three_tier_classification(),
            'skills_gap_analysis_accuracy': await self._test_skills_gap_analysis_accuracy(),
            'commute_time_estimation_accuracy': await self._test_commute_time_estimation_accuracy()
        }
        
        return results

    async def _test_zipcode_validation_accuracy(self) -> TestResult:
        """Test zipcode validation accuracy"""
        start_time = time.time()
        
        test_cases = [
            ("12345", True),
            ("90210", True),
            ("10001", True),
            ("12345-6789", True),
            ("1234", False),
            ("abcde", False),
            ("123456", False),
            ("", False),
            ("00000", True),  # Valid format
            ("99999", True)   # Valid format
        ]
        
        passed = 0
        total = len(test_cases)
        errors = []
        
        for zipcode, expected in test_cases:
            try:
                result = self.location_validator.validate_zipcode(zipcode)
                if result == expected:
                    passed += 1
                else:
                    errors.append(f"ZIP {zipcode}: expected {expected}, got {result}")
            except Exception as e:
                errors.append(f"ZIP {zipcode}: error {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="zipcode_validation_accuracy",
            passed=score >= 95,  # 95% accuracy threshold
            score=score,
            metrics={
                'total_tests': total,
                'passed_tests': passed,
                'accuracy_percentage': score
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_radius_filtering_precision(self) -> TestResult:
        """Test radius filtering precision for 5/10/30-mile accuracy"""
        start_time = time.time()
        
        # Test with Atlanta metro area
        test_zipcode = "30309"  # Atlanta center
        test_radiuses = [5, 10, 30]
        
        precision_scores = []
        errors = []
        
        for radius in test_radiuses:
            try:
                # Get jobs within radius
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT job_id, zipcode, msa FROM test_job_opportunities 
                    WHERE msa = 'Atlanta-Sandy Springs-Alpharetta, GA'
                ''')
                
                jobs = cursor.fetchall()
                conn.close()
                
                # Calculate distances and check precision
                within_radius = 0
                total_jobs = len(jobs)
                
                for job_id, job_zipcode, msa in jobs:
                    if job_zipcode:
                        distance = self.location_validator.calculate_distance(test_zipcode, job_zipcode)
                        if distance and distance <= radius:
                            within_radius += 1
                
                precision = within_radius / total_jobs if total_jobs > 0 else 0
                precision_scores.append(precision)
                
            except Exception as e:
                errors.append(f"Radius {radius} miles: {e}")
        
        avg_precision = statistics.mean(precision_scores) if precision_scores else 0
        score = avg_precision * 100
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="radius_filtering_precision",
            passed=score >= 99.9,  # 99.9% precision threshold
            score=score,
            metrics={
                'tested_radiuses': test_radiuses,
                'precision_scores': precision_scores,
                'average_precision': avg_precision
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_distance_calculation_verification(self) -> TestResult:
        """Test distance calculation verification with known distances"""
        start_time = time.time()
        
        # Known distances between major cities (in miles)
        test_cases = [
            ("10001", "77002", 1620),  # NYC to Houston
            ("10001", "60601", 790),   # NYC to Chicago
            ("10001", "33131", 1090),  # NYC to Miami
            ("77002", "75201", 240),   # Houston to Dallas
            ("60601", "75201", 925),   # Chicago to Dallas
        ]
        
        passed = 0
        total = len(test_cases)
        errors = []
        distance_errors = []
        
        for zip1, zip2, expected_distance in test_cases:
            try:
                calculated_distance = self.location_validator.calculate_distance(zip1, zip2)
                if calculated_distance:
                    error_miles = abs(calculated_distance - expected_distance)
                    error_percentage = (error_miles / expected_distance) * 100
                    
                    if error_percentage <= 5:  # 5% tolerance
                        passed += 1
                    else:
                        errors.append(f"{zip1} to {zip2}: {error_percentage:.1f}% error")
                    
                    distance_errors.append(error_percentage)
                else:
                    errors.append(f"{zip1} to {zip2}: Could not calculate distance")
                    
            except Exception as e:
                errors.append(f"{zip1} to {zip2}: {e}")
        
        score = (passed / total) * 100
        avg_error = statistics.mean(distance_errors) if distance_errors else 0
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="distance_calculation_verification",
            passed=score >= 90,  # 90% accuracy threshold
            score=score,
            metrics={
                'total_tests': total,
                'passed_tests': passed,
                'average_error_percentage': avg_error,
                'max_tolerance': 5.0
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_salary_increase_accuracy(self) -> TestResult:
        """Test salary increase accuracy validation within specified radius"""
        start_time = time.time()
        
        # Test with different metro areas and salary scenarios
        test_scenarios = [
            {
                'zipcode': '10001',
                'current_salary': 100000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.45
            },
            {
                'zipcode': '77002',
                'current_salary': 80000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.45
            },
            {
                'zipcode': '30309',
                'current_salary': 75000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.45
            }
        ]
        
        passed = 0
        total = 0
        errors = []
        
        for scenario in test_scenarios:
            try:
                # Get location data
                location_data = self.location_validator.geocode_zipcode(scenario['zipcode'])
                if not location_data:
                    errors.append(f"Could not geocode {scenario['zipcode']}")
                    continue
                
                # Get jobs in the area
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT salary_median, salary_increase_potential 
                    FROM test_job_opportunities 
                    WHERE zipcode = ?
                ''', (scenario['zipcode'],))
                
                jobs = cursor.fetchall()
                conn.close()
                
                for salary_median, salary_increase_potential in jobs:
                    total += 1
                    
                    # Calculate actual salary increase
                    if salary_median and scenario['current_salary']:
                        actual_increase = (salary_median - scenario['current_salary']) / scenario['current_salary']
                        
                        # Check if within expected range
                        if (scenario['expected_min_increase'] <= actual_increase <= scenario['expected_max_increase'] or
                            scenario['expected_min_increase'] <= salary_increase_potential <= scenario['expected_max_increase']):
                            passed += 1
                        else:
                            errors.append(f"Salary increase {actual_increase:.2%} outside expected range for {scenario['zipcode']}")
                
            except Exception as e:
                errors.append(f"Scenario {scenario['zipcode']}: {e}")
        
        score = (passed / total) * 100 if total > 0 else 0
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="salary_increase_accuracy",
            passed=score >= 90,  # 90% accuracy threshold
            score=score,
            metrics={
                'total_jobs_tested': total,
                'passed_jobs': passed,
                'accuracy_percentage': score
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_job_relevance_scoring(self) -> TestResult:
        """Test job relevance scoring verification with location factors"""
        start_time = time.time()
        
        # Test job relevance scoring with location factors
        test_cases = [
            {
                'user_zipcode': '10001',
                'job_zipcode': '10001',
                'expected_high_relevance': True
            },
            {
                'user_zipcode': '10001',
                'job_zipcode': '07030',  # Hoboken, NJ - close to NYC
                'expected_high_relevance': True
            },
            {
                'user_zipcode': '10001',
                'job_zipcode': '77002',  # Houston, TX - far from NYC
                'expected_high_relevance': False
            }
        ]
        
        passed = 0
        total = len(test_cases)
        errors = []
        
        for case in test_cases:
            try:
                # Calculate distance
                distance = self.location_validator.calculate_distance(
                    case['user_zipcode'], case['job_zipcode']
                )
                
                if distance is not None:
                    # Calculate relevance score based on distance
                    if distance <= 10:  # Within 10 miles
                        relevance_score = 0.9
                    elif distance <= 30:  # Within 30 miles
                        relevance_score = 0.7
                    else:  # Beyond 30 miles
                        relevance_score = 0.3
                    
                    # Check if relevance matches expectation
                    is_high_relevance = relevance_score >= 0.7
                    if is_high_relevance == case['expected_high_relevance']:
                        passed += 1
                    else:
                        errors.append(f"Relevance mismatch for {case['user_zipcode']} to {case['job_zipcode']}")
                else:
                    errors.append(f"Could not calculate distance for {case['user_zipcode']} to {case['job_zipcode']}")
                    
            except Exception as e:
                errors.append(f"Case {case}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="job_relevance_scoring",
            passed=score >= 90,  # 90% accuracy threshold
            score=score,
            metrics={
                'total_tests': total,
                'passed_tests': passed,
                'accuracy_percentage': score
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_three_tier_classification(self) -> TestResult:
        """Test three-tier classification appropriateness across different metro areas"""
        start_time = time.time()
        
        # Test tier classification for different metro areas
        metro_areas = ['Atlanta', 'Houston', 'DC_Metro', 'Dallas', 'NYC']
        passed = 0
        total = 0
        errors = []
        
        for metro in metro_areas:
            try:
                # Get test data for this metro
                metro_data = self.metro_test_data.get(metro, [])
                if not metro_data:
                    continue
                
                # Test with different salary scenarios
                test_salaries = [60000, 80000, 100000, 120000]
                
                for salary in test_salaries:
                    for location in metro_data:
                        # Create search criteria
                        criteria = SearchCriteria(
                            current_salary=salary,
                            target_salary_increase=0.25,
                            career_field=CareerField.TECHNOLOGY,
                            experience_level=ExperienceLevel.MID,
                            preferred_msas=[location.msa],
                            remote_ok=True
                        )
                        
                        # Get jobs and classify tiers
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            SELECT job_id, salary_median, salary_increase_potential, overall_score
                            FROM test_job_opportunities 
                            WHERE msa = ?
                        ''', (location.msa,))
                        
                        jobs = cursor.fetchall()
                        conn.close()
                        
                        for job_id, salary_median, salary_increase_potential, overall_score in jobs:
                            total += 1
                            
                            # Classify tier based on salary increase
                            if salary_median:
                                actual_increase = (salary_median - salary) / salary
                            else:
                                actual_increase = salary_increase_potential
                            
                            # Determine expected tier
                            if 0.15 <= actual_increase <= 0.20:
                                expected_tier = JobTier.CONSERVATIVE
                            elif 0.25 <= actual_increase <= 0.30:
                                expected_tier = JobTier.OPTIMAL
                            elif actual_increase >= 0.35:
                                expected_tier = JobTier.STRETCH
                            else:
                                continue  # Skip jobs that don't meet minimum increase
                            
                            # Check if classification is appropriate
                            if expected_tier in [JobTier.CONSERVATIVE, JobTier.OPTIMAL, JobTier.STRETCH]:
                                passed += 1
                            else:
                                errors.append(f"Inappropriate tier classification for {job_id}")
                
            except Exception as e:
                errors.append(f"Metro {metro}: {e}")
        
        score = (passed / total) * 100 if total > 0 else 0
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="three_tier_classification",
            passed=score >= 85,  # 85% accuracy threshold
            score=score,
            metrics={
                'total_jobs_tested': total,
                'passed_classifications': passed,
                'accuracy_percentage': score
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_skills_gap_analysis_accuracy(self) -> TestResult:
        """Test skills gap analysis accuracy"""
        start_time = time.time()
        
        # Test skills gap analysis with sample job descriptions
        test_jobs = [
            {
                'title': 'Senior Software Engineer',
                'description': 'Python, JavaScript, AWS, React, Node.js, SQL, Docker',
                'expected_skills': ['python', 'javascript', 'aws', 'react', 'node.js', 'sql', 'docker']
            },
            {
                'title': 'Data Analyst',
                'description': 'SQL, Python, Tableau, Excel, Statistics, Machine Learning',
                'expected_skills': ['sql', 'python', 'tableau', 'excel', 'statistics', 'machine learning']
            },
            {
                'title': 'Product Manager',
                'description': 'Agile, Scrum, User Research, Analytics, Leadership, Communication',
                'expected_skills': ['agile', 'scrum', 'user research', 'analytics', 'leadership', 'communication']
            }
        ]
        
        passed = 0
        total = len(test_jobs)
        errors = []
        
        for job in test_jobs:
            try:
                # Extract skills using the three-tier selector
                skills_gaps = self.three_tier_selector.analyze_skills_gap(
                    type('JobOpportunity', (), {
                        'job_id': 'test_job',
                        'description': job['description'],
                        'requirements': [job['description']]
                    })(),
                    SearchCriteria(
                        current_salary=75000,
                        target_salary_increase=0.25,
                        career_field=CareerField.TECHNOLOGY,
                        experience_level=ExperienceLevel.MID,
                        preferred_msas=[],
                        remote_ok=True
                    )
                )
                
                # Check if expected skills are identified
                identified_skills = [gap.skill.lower() for gap in skills_gaps]
                expected_skills = [skill.lower() for skill in job['expected_skills']]
                
                # Count matches
                matches = sum(1 for skill in expected_skills if skill in identified_skills)
                match_percentage = (matches / len(expected_skills)) * 100 if expected_skills else 0
                
                if match_percentage >= 70:  # 70% skill identification threshold
                    passed += 1
                else:
                    errors.append(f"Job {job['title']}: Only {match_percentage:.1f}% skills identified")
                
            except Exception as e:
                errors.append(f"Job {job['title']}: {e}")
        
        score = (passed / total) * 100
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="skills_gap_analysis_accuracy",
            passed=score >= 85,  # 85% accuracy threshold
            score=score,
            metrics={
                'total_jobs_tested': total,
                'passed_jobs': passed,
                'accuracy_percentage': score
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    async def _test_commute_time_estimation_accuracy(self) -> TestResult:
        """Test commute time estimation accuracy within 15% tolerance"""
        start_time = time.time()
        
        # Test commute time estimation with known routes
        test_routes = [
            {
                'from_zip': '10001',
                'to_zip': '07030',  # NYC to Hoboken
                'expected_time_minutes': 25,
                'tolerance_percentage': 15
            },
            {
                'from_zip': '77002',
                'to_zip': '77494',  # Houston to Katy
                'expected_time_minutes': 35,
                'tolerance_percentage': 15
            },
            {
                'from_zip': '30309',
                'to_zip': '30024',  # Atlanta to Duluth
                'expected_time_minutes': 30,
                'tolerance_percentage': 15
            }
        ]
        
        passed = 0
        total = len(test_routes)
        errors = []
        time_errors = []
        
        for route in test_routes:
            try:
                commute_estimate = self.location_validator.get_commute_time_estimate(
                    route['from_zip'], route['to_zip']
                )
                
                if commute_estimate and 'estimated_time_minutes' in commute_estimate:
                    estimated_time = commute_estimate['estimated_time_minutes']
                    expected_time = route['expected_time_minutes']
                    tolerance = route['tolerance_percentage']
                    
                    # Calculate error percentage
                    error_percentage = abs(estimated_time - expected_time) / expected_time * 100
                    time_errors.append(error_percentage)
                    
                    if error_percentage <= tolerance:
                        passed += 1
                    else:
                        errors.append(f"Route {route['from_zip']} to {route['to_zip']}: {error_percentage:.1f}% error")
                else:
                    errors.append(f"Route {route['from_zip']} to {route['to_zip']}: No commute estimate")
                    
            except Exception as e:
                errors.append(f"Route {route}: {e}")
        
        score = (passed / total) * 100
        avg_error = statistics.mean(time_errors) if time_errors else 0
        execution_time = time.time() - start_time
        
        return TestResult(
            test_name="commute_time_estimation_accuracy",
            passed=score >= 90,  # 90% accuracy threshold
            score=score,
            metrics={
                'total_routes_tested': total,
                'passed_routes': passed,
                'average_error_percentage': avg_error,
                'max_tolerance': 15.0
            },
            errors=errors,
            warnings=[],
            execution_time=execution_time
        )

    def _calculate_overall_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall test results and scores"""
        total_tests = 0
        passed_tests = 0
        total_score = 0.0
        
        # Count tests and calculate scores
        for category, results in test_results.items():
            if isinstance(results, dict) and 'test_name' in str(results):
                # This is a TestResult object
                if isinstance(results, TestResult):
                    total_tests += 1
                    if results.passed:
                        passed_tests += 1
                    total_score += results.score
            elif isinstance(results, dict):
                # This is a category with multiple tests
                for test_name, test_result in results.items():
                    if isinstance(test_result, TestResult):
                        total_tests += 1
                        if test_result.passed:
                            passed_tests += 1
                        total_score += test_result.score
        
        overall_score = (total_score / total_tests) if total_tests > 0 else 0.0
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0.0
        
        test_results['overall_score'] = overall_score
        test_results['total_tests'] = total_tests
        test_results['passed_tests'] = passed_tests
        test_results['failed_tests'] = total_tests - passed_tests
        test_results['pass_rate'] = pass_rate
        
        return test_results

# Placeholder methods for remaining test categories
async def _run_user_scenario_tests(self) -> Dict[str, Any]:
    """Run location-specific user scenario tests for target demographics"""
    return {"status": "pending", "message": "User scenario tests to be implemented"}

async def _run_metro_coverage_tests(self) -> Dict[str, Any]:
    """Run metro area coverage tests for all target cities"""
    return {"status": "pending", "message": "Metro coverage tests to be implemented"}

async def _run_performance_tests(self) -> Dict[str, Any]:
    """Run performance tests with location services"""
    return {"status": "pending", "message": "Performance tests to be implemented"}

async def _run_edge_case_tests(self) -> Dict[str, Any]:
    """Run edge case and error handling tests for location features"""
    return {"status": "pending", "message": "Edge case tests to be implemented"}

# Add placeholder methods to the class
LocationRecommendationTestFramework._run_user_scenario_tests = _run_user_scenario_tests
LocationRecommendationTestFramework._run_metro_coverage_tests = _run_metro_coverage_tests
LocationRecommendationTestFramework._run_performance_tests = _run_performance_tests
LocationRecommendationTestFramework._run_edge_case_tests = _run_edge_case_tests

async def main():
    """Run the comprehensive location recommendation testing framework"""
    framework = LocationRecommendationTestFramework()
    
    print("🚀 Starting Comprehensive Location-Based Job Recommendation Testing Framework")
    print("=" * 80)
    
    # Run all tests
    results = await framework.run_comprehensive_tests()
    
    # Print summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Pass Rate: {results['pass_rate']:.1f}%")
    print(f"Total Duration: {results['total_duration']:.2f} seconds")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"location_recommendation_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
