#!/usr/bin/env python3
"""
Comprehensive Test Suite for IncomeBoostJobMatcher
Tests all functionality of the income-focused job matching system
"""

import unittest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add backend utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'utils'))

from income_boost_job_matcher import (
    IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel,
    JobOpportunity, CompanyProfile, JobBoard
)
from job_board_apis import JobBoardAPIManager, CompanyDataAPIManager

class TestIncomeBoostJobMatcher(unittest.TestCase):
    """Test cases for IncomeBoostJobMatcher"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.matcher = IncomeBoostJobMatcher(db_path=self.temp_db.name)
        
        # Create test search criteria
        self.test_criteria = SearchCriteria(
            current_salary=75000,
            target_salary_increase=0.25,
            career_field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
            remote_ok=True,
            max_commute_time=30,
            must_have_benefits=["health insurance", "401k"],
            company_size_preference="mid",
            industry_preference="technology",
            equity_required=False,
            min_company_rating=3.0
        )
        
        # Create test job opportunity
        self.test_job = JobOpportunity(
            job_id="test_job_1",
            title="Senior Software Engineer",
            company="Test Company",
            location="Atlanta, GA",
            msa="Atlanta-Sandy Springs-Alpharetta, GA",
            salary_min=90000,
            salary_max=120000,
            salary_median=105000,
            salary_increase_potential=0.0,
            remote_friendly=True,
            job_board=JobBoard.INDEED,
            url="https://example.com/job/1",
            description="Great opportunity for senior software engineer",
            requirements=["Python", "JavaScript", "5+ years experience"],
            benefits=["Health insurance", "401k", "Remote work"],
            diversity_score=0.0,
            growth_score=0.0,
            culture_score=0.0,
            overall_score=0.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.SENIOR,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="mid",
            company_industry="technology",
            equity_offered=True,
            bonus_potential=10000,
            career_advancement_score=0.0,
            work_life_balance_score=0.0
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test IncomeBoostJobMatcher initialization"""
        self.assertIsNotNone(self.matcher)
        self.assertEqual(len(self.matcher.target_msas), 10)
        self.assertIn("Atlanta-Sandy Springs-Alpharetta, GA", self.matcher.target_msas)
        self.assertIn("Houston-The Woodlands-Sugar Land, TX", self.matcher.target_msas)
    
    def test_field_specific_strategies(self):
        """Test field-specific search strategies"""
        # Test technology field
        tech_strategies = self.matcher.field_specific_strategies(CareerField.TECHNOLOGY)
        self.assertIn("keywords", tech_strategies)
        self.assertIn("software engineer", tech_strategies["keywords"])
        self.assertIn("equity", tech_strategies["salary_keywords"])
        
        # Test finance field
        finance_strategies = self.matcher.field_specific_strategies(CareerField.FINANCE)
        self.assertIn("financial analyst", finance_strategies["keywords"])
        self.assertIn("bonus", finance_strategies["salary_keywords"])
        
        # Test healthcare field
        healthcare_strategies = self.matcher.field_specific_strategies(CareerField.HEALTHCARE)
        self.assertIn("nurse", healthcare_strategies["keywords"])
        self.assertIn("health insurance", healthcare_strategies["benefits_keywords"])
    
    def test_multi_dimensional_scoring(self):
        """Test multi-dimensional job scoring"""
        scored_job = self.matcher.multi_dimensional_scoring(self.test_job, self.test_criteria)
        
        # Check that scores are calculated
        self.assertGreater(scored_job.overall_score, 0)
        self.assertGreater(scored_job.salary_increase_potential, 0)
        self.assertGreaterEqual(scored_job.diversity_score, 0)
        self.assertGreaterEqual(scored_job.growth_score, 0)
        self.assertGreaterEqual(scored_job.culture_score, 0)
        
        # Check that salary increase potential is calculated correctly
        expected_increase = (105000 - 75000) / 75000
        self.assertAlmostEqual(scored_job.salary_increase_potential, expected_increase, places=2)
    
    def test_salary_score_calculation(self):
        """Test salary score calculation"""
        # Test high salary increase
        high_salary_job = self.test_job
        high_salary_job.salary_median = 120000  # 60% increase
        score = self.matcher._calculate_salary_score(high_salary_job, self.test_criteria)
        self.assertGreaterEqual(score, 80)
        
        # Test moderate salary increase
        moderate_salary_job = self.test_job
        moderate_salary_job.salary_median = 90000  # 20% increase
        score = self.matcher._calculate_salary_score(moderate_salary_job, self.test_criteria)
        self.assertGreaterEqual(score, 60)
        
        # Test low salary increase
        low_salary_job = self.test_job
        low_salary_job.salary_median = 80000  # 6.7% increase
        score = self.matcher._calculate_salary_score(low_salary_job, self.test_criteria)
        self.assertLess(score, 70)
    
    def test_advancement_score_calculation(self):
        """Test career advancement score calculation"""
        # Test job with advancement keywords
        advancement_job = self.test_job
        advancement_job.title = "Senior Lead Software Engineer"
        advancement_job.description = "Great growth opportunity with leadership responsibilities"
        advancement_job.equity_offered = True
        advancement_job.bonus_potential = 15000
        
        score = self.matcher._calculate_advancement_score(advancement_job, self.test_criteria)
        self.assertGreaterEqual(score, 70)
        
        # Test job without advancement indicators
        basic_job = self.test_job
        basic_job.title = "Software Engineer"
        basic_job.description = "Basic software development role"
        basic_job.equity_offered = False
        basic_job.bonus_potential = 0
        
        score = self.matcher._calculate_advancement_score(basic_job, self.test_criteria)
        self.assertLess(score, 60)
    
    def test_benefits_score_calculation(self):
        """Test benefits and work-life balance score calculation"""
        # Test job with good benefits
        good_benefits_job = self.test_job
        good_benefits_job.benefits = ["health insurance", "401k", "dental", "vision", "PTO"]
        good_benefits_job.description = "Flexible work environment with work-life balance"
        good_benefits_job.remote_friendly = True
        
        score = self.matcher._calculate_benefits_score(good_benefits_job, self.test_criteria)
        self.assertGreaterEqual(score, 70)
        
        # Test job with minimal benefits
        minimal_benefits_job = self.test_job
        minimal_benefits_job.benefits = ["health insurance"]
        minimal_benefits_job.description = "Standard office job"
        minimal_benefits_job.remote_friendly = False
        
        score = self.matcher._calculate_benefits_score(minimal_benefits_job, self.test_criteria)
        self.assertLess(score, 60)
    
    def test_msa_targeting(self):
        """Test MSA targeting functionality"""
        jobs = [self.test_job]
        preferred_msas = ["Atlanta-Sandy Springs-Alpharetta, GA"]
        
        targeted_jobs = self.matcher.msa_targeting(jobs, preferred_msas)
        
        # Check that preferred MSA jobs get score boost
        self.assertGreaterEqual(targeted_jobs[0].overall_score, self.test_job.overall_score)
    
    def test_remote_opportunity_detection(self):
        """Test remote opportunity detection"""
        jobs = [self.test_job]
        
        remote_jobs = self.matcher.remote_opportunity_detection(jobs)
        
        # Check that remote-friendly jobs are identified
        self.assertTrue(remote_jobs[0].remote_friendly)
        self.assertGreaterEqual(remote_jobs[0].overall_score, self.test_job.overall_score)
    
    def test_company_quality_assessment(self):
        """Test company quality assessment"""
        company_name = "Test Company"
        
        # Mock the database query to return None (new company)
        with patch.object(self.matcher, '_get_glassdoor_data', return_value=None), \
             patch.object(self.matcher, '_get_indeed_company_data', return_value=None), \
             patch.object(self.matcher, '_get_diversity_data', return_value=None), \
             patch.object(self.matcher, '_get_growth_data', return_value=None):
            
            profile = self.matcher.company_quality_assessment(company_name)
            
            self.assertIsNotNone(profile)
            self.assertEqual(profile.name, company_name)
            self.assertIsNotNone(profile.company_id)
    
    def test_salary_increase_potential_calculation(self):
        """Test salary increase potential calculation"""
        # Test with valid salary data
        potential = self.matcher._calculate_salary_increase_potential(self.test_job, self.test_criteria)
        expected = (105000 - 75000) / 75000
        self.assertAlmostEqual(potential, expected, places=2)
        
        # Test with no salary data
        no_salary_job = self.test_job
        no_salary_job.salary_median = None
        potential = self.matcher._calculate_salary_increase_potential(no_salary_job, self.test_criteria)
        self.assertEqual(potential, 0.0)
    
    def test_meets_salary_criteria(self):
        """Test salary criteria filtering"""
        # Test job within salary range
        self.assertTrue(self.matcher._meets_salary_criteria(
            self.test_job, self.test_criteria, 80000, 120000
        ))
        
        # Test job below salary range
        low_salary_job = self.test_job
        low_salary_job.salary_median = 70000
        self.assertFalse(self.matcher._meets_salary_criteria(
            low_salary_job, self.test_criteria, 80000, 120000
        ))
        
        # Test job above salary range
        high_salary_job = self.test_job
        high_salary_job.salary_median = 130000
        self.assertFalse(self.matcher._meets_salary_criteria(
            high_salary_job, self.test_criteria, 80000, 120000
        ))
    
    @patch('aiohttp.ClientSession')
    async def test_salary_focused_search(self, mock_session):
        """Test salary-focused search functionality"""
        # Mock the job board API responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'jobs': []})
        
        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Test search
        jobs = await self.matcher.salary_focused_search(self.test_criteria)
        
        # Should return empty list since we mocked empty responses
        self.assertIsInstance(jobs, list)
    
    def test_database_operations(self):
        """Test database operations"""
        # Test storing company profile
        profile = CompanyProfile(
            company_id="test_comp_1",
            name="Test Company",
            industry="Technology",
            size="Mid",
            diversity_score=75.0,
            growth_score=80.0,
            culture_score=70.0,
            benefits_score=85.0,
            leadership_diversity=60.0,
            employee_retention=85.0,
            glassdoor_rating=4.2,
            indeed_rating=4.0,
            remote_friendly=True,
            headquarters="Atlanta, GA",
            founded_year=2010,
            funding_stage="Series B",
            revenue="10M-50M"
        )
        
        self.matcher._store_company_profile(profile)
        
        # Verify profile was stored
        import sqlite3
        conn = sqlite3.connect(self.matcher.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM company_profiles WHERE company_id = ?', (profile.company_id,))
        stored_profile = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(stored_profile)
        self.assertEqual(stored_profile[1], profile.name)
    
    def test_search_criteria_validation(self):
        """Test search criteria validation"""
        # Test valid criteria
        valid_criteria = SearchCriteria(
            current_salary=75000,
            target_salary_increase=0.25,
            career_field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
            remote_ok=True,
            max_commute_time=30,
            must_have_benefits=["health insurance"],
            company_size_preference="mid",
            industry_preference="technology",
            equity_required=False,
            min_company_rating=3.0
        )
        
        self.assertEqual(valid_criteria.current_salary, 75000)
        self.assertEqual(valid_criteria.target_salary_increase, 0.25)
        self.assertEqual(valid_criteria.career_field, CareerField.TECHNOLOGY)
        self.assertEqual(valid_criteria.experience_level, ExperienceLevel.MID)
    
    def test_job_opportunity_creation(self):
        """Test JobOpportunity object creation"""
        job = JobOpportunity(
            job_id="test_1",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=50000,
            salary_max=70000,
            salary_median=60000,
            salary_increase_potential=0.2,
            remote_friendly=True,
            job_board=JobBoard.INDEED,
            url="https://test.com",
            description="Test description",
            requirements=["Python"],
            benefits=["Health insurance"],
            diversity_score=75.0,
            growth_score=80.0,
            culture_score=70.0,
            overall_score=75.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=False,
            bonus_potential=5000,
            career_advancement_score=75.0,
            work_life_balance_score=80.0
        )
        
        self.assertEqual(job.job_id, "test_1")
        self.assertEqual(job.title, "Test Job")
        self.assertEqual(job.company, "Test Company")
        self.assertEqual(job.salary_median, 60000)
        self.assertEqual(job.salary_increase_potential, 0.2)
        self.assertTrue(job.remote_friendly)
        self.assertEqual(job.job_board, JobBoard.INDEED)
        self.assertEqual(job.field, CareerField.TECHNOLOGY)
        self.assertEqual(job.experience_level, ExperienceLevel.MID)

class TestJobBoardAPIManager(unittest.TestCase):
    """Test cases for JobBoardAPIManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_manager = JobBoardAPIManager()
    
    def test_initialization(self):
        """Test JobBoardAPIManager initialization"""
        self.assertIsNotNone(self.api_manager)
        self.assertIn('indeed', self.api_manager.configs)
        self.assertIn('linkedin', self.api_manager.configs)
        self.assertIn('glassdoor', self.api_manager.configs)
    
    def test_extract_salary(self):
        """Test salary extraction from text"""
        # Test with dollar signs
        salary_text = "$80,000 - $120,000"
        min_salary = self.api_manager._extract_salary(salary_text, 'min')
        max_salary = self.api_manager._extract_salary(salary_text, 'max')
        
        self.assertEqual(min_salary, 80000)
        self.assertEqual(max_salary, 120000)
        
        # Test with no dollar signs
        salary_text = "80000-120000"
        min_salary = self.api_manager._extract_salary(salary_text, 'min')
        max_salary = self.api_manager._extract_salary(salary_text, 'max')
        
        self.assertEqual(min_salary, 80000)
        self.assertEqual(max_salary, 120000)
        
        # Test with single salary
        salary_text = "$100,000"
        min_salary = self.api_manager._extract_salary(salary_text, 'min')
        max_salary = self.api_manager._extract_salary(salary_text, 'max')
        
        self.assertEqual(min_salary, 100000)
        self.assertEqual(max_salary, 100000)
        
        # Test with no salary
        salary_text = "Salary not specified"
        min_salary = self.api_manager._extract_salary(salary_text, 'min')
        max_salary = self.api_manager._extract_salary(salary_text, 'max')
        
        self.assertIsNone(min_salary)
        self.assertIsNone(max_salary)
    
    def test_parse_indeed_jobs(self):
        """Test Indeed job parsing"""
        mock_data = {
            'jobs': [
                {
                    'id': '123',
                    'title': 'Software Engineer',
                    'company': 'Test Company',
                    'location': 'Atlanta, GA',
                    'salary': '$80,000 - $120,000',
                    'description': 'Great opportunity',
                    'url': 'https://indeed.com/viewjob?jk=123',
                    'date': '2024-01-01'
                }
            ]
        }
        
        jobs = self.api_manager._parse_indeed_jobs(mock_data)
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_id'], 'indeed_123')
        self.assertEqual(jobs[0]['title'], 'Software Engineer')
        self.assertEqual(jobs[0]['company'], 'Test Company')
        self.assertEqual(jobs[0]['salary_min'], 80000)
        self.assertEqual(jobs[0]['salary_max'], 120000)
        self.assertEqual(jobs[0]['job_board'], 'indeed')
    
    def test_parse_linkedin_jobs(self):
        """Test LinkedIn job parsing"""
        mock_data = {
            'jobs': [
                {
                    'id': '456',
                    'title': 'Senior Developer',
                    'company': 'LinkedIn Company',
                    'location': 'San Francisco, CA',
                    'salary': '$120,000 - $150,000',
                    'description': 'Senior role',
                    'url': 'https://linkedin.com/jobs/view/456',
                    'date': '2024-01-02'
                }
            ]
        }
        
        jobs = self.api_manager._parse_linkedin_jobs(mock_data)
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_id'], 'linkedin_456')
        self.assertEqual(jobs[0]['title'], 'Senior Developer')
        self.assertEqual(jobs[0]['company'], 'LinkedIn Company')
        self.assertEqual(jobs[0]['salary_min'], 120000)
        self.assertEqual(jobs[0]['salary_max'], 150000)
        self.assertEqual(jobs[0]['job_board'], 'linkedin')
    
    def test_parse_glassdoor_jobs(self):
        """Test Glassdoor job parsing"""
        mock_data = {
            'jobs': [
                {
                    'id': '789',
                    'title': 'Product Manager',
                    'company': 'Glassdoor Company',
                    'location': 'New York, NY',
                    'salary': '$100,000 - $140,000',
                    'description': 'Product management role',
                    'url': 'https://glassdoor.com/job-listing/789',
                    'date': '2024-01-03'
                }
            ]
        }
        
        jobs = self.api_manager._parse_glassdoor_jobs(mock_data)
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_id'], 'glassdoor_789')
        self.assertEqual(jobs[0]['title'], 'Product Manager')
        self.assertEqual(jobs[0]['company'], 'Glassdoor Company')
        self.assertEqual(jobs[0]['salary_min'], 100000)
        self.assertEqual(jobs[0]['salary_max'], 140000)
        self.assertEqual(jobs[0]['job_board'], 'glassdoor')

class TestCompanyDataAPIManager(unittest.TestCase):
    """Test cases for CompanyDataAPIManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_manager = CompanyDataAPIManager()
    
    def test_initialization(self):
        """Test CompanyDataAPIManager initialization"""
        self.assertIsNotNone(self.api_manager)
        self.assertIn('glassdoor_company', self.api_manager.configs)
        self.assertIn('crunchbase', self.api_manager.configs)
    
    def test_calculate_growth_score(self):
        """Test growth score calculation"""
        # Test with Series B funding
        data = {'funding_stage': 'Series B', 'revenue': '10M-50M'}
        score = self.api_manager._calculate_growth_score(data)
        self.assertGreaterEqual(score, 70)
        
        # Test with IPO
        data = {'funding_stage': 'IPO', 'revenue': '100M-500M'}
        score = self.api_manager._calculate_growth_score(data)
        self.assertGreaterEqual(score, 80)
        
        # Test with acquisition
        data = {'funding_stage': 'Acquisition', 'revenue': '50M-100M'}
        score = self.api_manager._calculate_growth_score(data)
        self.assertGreaterEqual(score, 65)
        
        # Test with no data
        data = {}
        score = self.api_manager._calculate_growth_score(data)
        self.assertEqual(score, 50.0)

def run_async_test(coro):
    """Helper function to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class TestAsyncFunctionality(unittest.TestCase):
    """Test async functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.matcher = IncomeBoostJobMatcher(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_async_search_functionality(self):
        """Test async search functionality"""
        criteria = SearchCriteria(
            current_salary=75000,
            target_salary_increase=0.25,
            career_field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
            remote_ok=True,
            max_commute_time=30,
            must_have_benefits=["health insurance"],
            company_size_preference="mid",
            industry_preference="technology",
            equity_required=False,
            min_company_rating=3.0
        )
        
        # Mock the search methods to return empty results
        with patch.object(self.matcher, '_search_indeed', return_value=[]), \
             patch.object(self.matcher, '_search_linkedin', return_value=[]), \
             patch.object(self.matcher, '_search_glassdoor', return_value=[]):
            
            jobs = run_async_test(self.matcher.salary_focused_search(criteria))
            self.assertIsInstance(jobs, list)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
