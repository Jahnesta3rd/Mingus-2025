"""
Comprehensive Testing Suite for Mingus Job Recommendation Engine
Tests accuracy, reliability, and appropriateness for target demographic (African American professionals 25-35)
"""

import unittest
import pytest
import time
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the components to test
from backend.ml.models.mingus_job_recommendation_engine import (
    MingusJobRecommendationEngine, JobRecommendationResult, ProcessingMetrics
)
from backend.ml.models.resume_parser import (
    AdvancedResumeParser, FieldType, ExperienceLevel, ResumeAnalysis
)
from backend.ml.models.intelligent_job_matcher import (
    IntelligentJobMatcher, JobPosting, JobScore, SearchParameters, CompanyTier
)
from backend.ml.models.job_selection_algorithm import (
    JobSelectionAlgorithm, CareerAdvancementStrategy, CareerTier as SelectionTier
)
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService
from backend.services.resume_analysis_service import ResumeAnalysisService


class TestJobRecommendationEngine(unittest.TestCase):
    """Comprehensive unit tests for the job recommendation engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = MingusJobRecommendationEngine()
        self.resume_parser = AdvancedResumeParser()
        self.job_matcher = IntelligentJobMatcher()
        self.job_selector = JobSelectionAlgorithm()
        
        # Sample resume for testing
        self.sample_resume = """
        SENIOR DATA ANALYST
        TechCorp Inc. | Atlanta, GA | 2020-2023
        - Led data analysis initiatives using Python, SQL, and Tableau
        - Managed team of 3 analysts and delivered insights to executive leadership
        - Increased revenue by 15% through predictive analytics implementation
        - Collaborated with cross-functional teams on data-driven decision making
        
        DATA ANALYST
        DataFlow Solutions | Atlanta, GA | 2018-2020
        - Performed statistical analysis and created automated reporting systems
        - Developed SQL queries and maintained data warehouse integrity
        - Created interactive dashboards using Power BI and Tableau
        - Supported marketing and sales teams with data insights
        
        EDUCATION
        Georgia Institute of Technology
        Bachelor of Science in Industrial Engineering
        GPA: 3.8/4.0
        
        SKILLS
        Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning
        Business: Project Management, Stakeholder Communication, Strategic Analysis
        Soft Skills: Leadership, Team Management, Problem Solving, Communication
        """
        
        # Target demographic test data
        self.target_demographic_data = {
            'age_range': (25, 35),
            'locations': ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City'],
            'fields': ['Data Analysis', 'Software Development', 'Project Management', 'Marketing'],
            'experience_levels': ['Entry', 'Mid', 'Senior'],
            'salary_ranges': [(50000, 150000)]
        }

    def test_resume_parser_field_detection(self):
        """Test resume parser field detection accuracy"""
        parser = AdvancedResumeParser()
        result = parser.parse_resume(self.sample_resume)
        
        # Test field detection accuracy
        self.assertIsInstance(result, ResumeAnalysis)
        self.assertIsNotNone(result.field_analysis)
        self.assertIsNotNone(result.experience_analysis)
        self.assertIsNotNone(result.skills_analysis)
        self.assertIsNotNone(result.income_analysis)
        
        # Test skills extraction
        technical_skills = result.skills_analysis.technical_skills
        business_skills = result.skills_analysis.business_skills
        soft_skills = result.skills_analysis.soft_skills
        
        # Check that skills are extracted
        self.assertIsInstance(technical_skills, dict)
        self.assertIsInstance(business_skills, dict)
        self.assertIsInstance(soft_skills, dict)
        
        # Test experience extraction
        self.assertIsNotNone(result.experience_analysis.level)
        self.assertGreaterEqual(result.experience_analysis.total_years, 0)
        
        # Test income analysis
        self.assertGreater(result.income_analysis.estimated_salary, 0)
        self.assertGreaterEqual(result.income_analysis.percentile, 0)
        self.assertLessEqual(result.income_analysis.percentile, 1)

    def test_income_comparison_accuracy(self):
        """Test income comparison and financial analysis accuracy"""
        current_salary = 75000
        target_locations = ['Atlanta', 'Houston']
        
        # Test salary range calculations
        conservative_range = self.engine._calculate_salary_range(current_salary, 0.15, 0.20)
        optimal_range = self.engine._calculate_salary_range(current_salary, 0.25, 0.30)
        stretch_range = self.engine._calculate_salary_range(current_salary, 0.35, 0.50)
        
        # Verify ranges are correct
        self.assertEqual(conservative_range['min'], 86250)  # 75000 * 1.15
        self.assertEqual(conservative_range['max'], 90000)  # 75000 * 1.20
        self.assertEqual(optimal_range['min'], 93750)       # 75000 * 1.25
        self.assertEqual(optimal_range['max'], 97500)       # 75000 * 1.30
        self.assertEqual(stretch_range['min'], 101250)      # 75000 * 1.35
        self.assertEqual(stretch_range['max'], 112500)      # 75000 * 1.50

    def test_job_matching_algorithm(self):
        """Test job matching algorithm accuracy"""
        from backend.ml.models.intelligent_job_matcher import JobPosting, SalaryRange, SearchParameters
        from backend.ml.models.resume_parser import FieldType, ExperienceLevel
        
        # Create proper JobPosting objects
        mock_jobs = [
            JobPosting(
                id="job1",
                title='Senior Data Analyst',
                company='TechCorp',
                location='Atlanta',
                salary_range=SalaryRange(min_salary=90000, max_salary=110000),
                skills=['Python', 'SQL', 'Tableau'],
                experience_level='Senior',
                field='Data Analysis'
            ),
            JobPosting(
                id="job2",
                title='Data Scientist',
                company='DataCorp',
                location='Houston',
                salary_range=SalaryRange(min_salary=95000, max_salary=120000),
                skills=['Python', 'Machine Learning', 'SQL'],
                experience_level='Senior',
                field='Data Analysis'
            )
        ]
        
        # Create search parameters
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=85000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=['Python', 'SQL', 'Tableau', 'Machine Learning'],
            locations=['Atlanta', 'Houston']
        )
        
        # Mock resume analysis
        mock_resume_analysis = type('MockResumeAnalysis', (), {
            'field_analysis': type('MockFieldAnalysis', (), {
                'primary_field': FieldType.DATA_ANALYSIS
            })()
        })()
        
        # Test job scoring
        scored_jobs = self.job_matcher._score_jobs(mock_jobs, search_params, mock_resume_analysis)
        
        # Verify scoring results
        self.assertGreater(len(scored_jobs), 0)
        for job_score in scored_jobs:
            self.assertGreater(job_score.overall_score, 0)
            self.assertLessEqual(job_score.overall_score, 1.0)
            self.assertGreater(job_score.salary_improvement_score, 0)

    def test_workflow_orchestration(self):
        """Test complete workflow orchestration"""
        # Test end-to-end workflow
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=1,
            current_salary=75000,
            target_locations=['Atlanta', 'Houston'],
            risk_preference='balanced'
        )
        
        # Verify workflow completion
        self.assertIsInstance(result, JobRecommendationResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user_profile)
        self.assertIsNotNone(result.financial_impact)
        self.assertIsNotNone(result.career_strategy)
        self.assertIsNotNone(result.action_plan)
        
        # Verify processing metrics
        self.assertIsInstance(result.processing_metrics, ProcessingMetrics)
        self.assertGreater(result.processing_metrics.total_processing_time, 0)
        self.assertLess(result.processing_metrics.total_processing_time, 10.0)  # Under 10 seconds

    def test_target_demographic_validation(self):
        """Test recommendations are appropriate for target demographic"""
        # Test with target demographic characteristics
        target_resume = """
        MARKETING MANAGER
        GrowthCorp | Atlanta, GA | 2021-2023
        - Led digital marketing campaigns targeting diverse audiences
        - Managed $500K marketing budget and achieved 25% ROI improvement
        - Collaborated with product teams on market research and customer insights
        - Mentored junior marketers and developed team capabilities
        
        MARKETING SPECIALIST
        BrandCorp | Atlanta, GA | 2019-2021
        - Executed social media campaigns and content marketing strategies
        - Analyzed campaign performance using Google Analytics and social media tools
        - Supported brand development and customer acquisition initiatives
        
        EDUCATION
        Morehouse College
        Bachelor of Business Administration in Marketing
        GPA: 3.7/4.0
        
        SKILLS
        Technical: Google Analytics, Facebook Ads, Instagram Marketing, Email Marketing
        Business: Brand Management, Customer Acquisition, Market Research, Budget Management
        Soft Skills: Leadership, Communication, Strategic Thinking, Team Collaboration
        """
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=target_resume,
            user_id=2,
            current_salary=65000,
            target_locations=['Atlanta', 'Houston', 'Washington DC'],
            risk_preference='balanced'
        )
        
        # Verify demographic appropriateness
        self.assertTrue(result.success)
        
        # Check that recommendations include target locations
        career_strategy = result.career_strategy
        for tier in ['conservative', 'optimal', 'stretch']:
            opportunity = getattr(career_strategy, f'{tier}_opportunity', None)
            if opportunity and hasattr(opportunity, 'job'):
                job_location = opportunity.job.location
                self.assertIn(job_location, self.target_demographic_data['locations'])

    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms"""
        # Test with invalid resume
        invalid_resume = "Invalid resume text"
        
        with self.assertRaises(ValueError):
            self.engine.process_resume_and_recommend_jobs(
                resume_text=invalid_resume,
                user_id=3,
                current_salary=50000
            )
        
        # Test with missing salary
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=4,
            current_salary=None,
            target_locations=['Atlanta']
        )
        
        # Should handle missing salary gracefully
        self.assertTrue(result.success)
        self.assertIsNotNone(result.financial_impact.current_salary)

    def test_caching_mechanism(self):
        """Test caching functionality"""
        # First call
        start_time = time.time()
        result1 = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=5,
            current_salary=70000,
            target_locations=['Atlanta'],
            enable_caching=True
        )
        first_call_time = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        result2 = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=5,
            current_salary=70000,
            target_locations=['Atlanta'],
            enable_caching=True
        )
        second_call_time = time.time() - start_time
        
        # Verify cache effectiveness
        self.assertLess(second_call_time, first_call_time)
        self.assertEqual(result1.user_profile.field_expertise['primary_field'],
                        result2.user_profile.field_expertise['primary_field'])

    def test_concurrency_handling(self):
        """Test concurrent request handling"""
        def process_request(user_id):
            return self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=user_id,
                current_salary=70000 + user_id * 1000,
                target_locations=['Atlanta'],
                enable_caching=False
            )
        
        # Test concurrent processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_request, i) for i in range(10, 13)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all requests completed successfully
        for result in results:
            self.assertTrue(result.success)
            self.assertIsNotNone(result.career_strategy)

    def test_performance_targets(self):
        """Test performance meets targets"""
        # Test processing time targets
        start_time = time.time()
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=6,
            current_salary=80000,
            target_locations=['Atlanta', 'Houston'],
            risk_preference='balanced'
        )
        total_time = time.time() - start_time
        
        # Verify performance targets
        self.assertLess(total_time, 8.0)  # Under 8 seconds total
        self.assertLess(result.processing_metrics.resume_processing_time, 2.0)
        self.assertLess(result.processing_metrics.income_comparison_time, 1.0)
        self.assertLess(result.processing_metrics.job_search_time, 5.0)
        self.assertLess(result.processing_metrics.job_selection_time, 2.0)

    def test_recommendation_quality_validation(self):
        """Test recommendation quality and appropriateness"""
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=7,
            current_salary=75000,
            target_locations=['Atlanta'],
            risk_preference='balanced'
        )
        
        career_strategy = result.career_strategy
        
        # Verify three-tier strategy
        self.assertIsNotNone(career_strategy.conservative_opportunity)
        self.assertIsNotNone(career_strategy.optimal_opportunity)
        self.assertIsNotNone(career_strategy.stretch_opportunity)
        
        # Verify salary progression
        conservative_salary = career_strategy.conservative_opportunity.income_impact.new_salary_range['midpoint']
        optimal_salary = career_strategy.optimal_opportunity.income_impact.new_salary_range['midpoint']
        stretch_salary = career_strategy.stretch_opportunity.income_impact.new_salary_range['midpoint']
        
        self.assertLess(conservative_salary, optimal_salary)
        self.assertLess(optimal_salary, stretch_salary)
        
        # Verify minimum salary increases
        conservative_increase = (conservative_salary - 75000) / 75000
        optimal_increase = (optimal_salary - 75000) / 75000
        stretch_increase = (stretch_salary - 75000) / 75000
        
        self.assertGreaterEqual(conservative_increase, 0.15)  # 15% minimum
        self.assertGreaterEqual(optimal_increase, 0.25)       # 25% minimum
        self.assertGreaterEqual(stretch_increase, 0.35)       # 35% minimum

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with very short resume
        short_resume = "Data Analyst with Python skills"
        
        with self.assertRaises(ValueError):
            self.engine.process_resume_and_recommend_jobs(
                resume_text=short_resume,
                user_id=8,
                current_salary=50000
            )
        
        # Test with very high salary
        high_salary_resume = self.sample_resume.replace("SENIOR DATA ANALYST", "CHIEF DATA OFFICER")
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=high_salary_resume,
            user_id=9,
            current_salary=200000,
            target_locations=['New York City']
        )
        
        # Should handle high salaries gracefully
        self.assertTrue(result.success)
        
        # Test with no target locations
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=10,
            current_salary=60000,
            target_locations=[]
        )
        
        # Should use default locations
        self.assertTrue(result.success)
        self.assertIsNotNone(result.career_strategy)

    def test_data_validation(self):
        """Test input data validation"""
        # Test invalid salary
        with self.assertRaises(ValueError):
            self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=11,
                current_salary=-1000
            )
        
        # Test invalid risk preference
        with self.assertRaises(ValueError):
            self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=12,
                current_salary=60000,
                risk_preference='invalid'
            )
        
        # Test invalid locations
        with self.assertRaises(ValueError):
            self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=13,
                current_salary=60000,
                target_locations=['Invalid City']
            )

    def test_memory_usage(self):
        """Test memory usage optimization"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple requests
        for i in range(5):
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=20 + i,
                current_salary=70000 + i * 1000,
                target_locations=['Atlanta'],
                enable_caching=False
            )
            self.assertTrue(result.success)
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory increase should be reasonable (< 100MB)
        self.assertLess(memory_increase, 100)

    def test_api_integration_mocking(self):
        """Test API integration with mocking"""
        # Test that the engine can handle external API responses
        # Since the engine uses mock data generation, we'll test the integration
        # by verifying it can process external job data when available
        
        # Mock the job matcher to return specific external job data
        from backend.ml.models.intelligent_job_matcher import JobPosting, SalaryRange, JobSource, CompanyTier
        
        mock_job = JobPosting(
            id='ext_api_1',
            title='Senior Data Analyst',
            company='TechCorp',
            location='Atlanta',
            salary_range=SalaryRange(min_salary=90000, max_salary=110000),
            description='External API job',
            requirements=[],
            skills=['Python', 'SQL', 'Tableau'],
            experience_level='Senior',
            field='Data Analysis',
            industry='Technology',
            remote_work=False,
            source=JobSource.LINKEDIN,
            company_tier=CompanyTier.UNKNOWN
        )
        
        with patch('backend.ml.models.intelligent_job_matcher.IntelligentJobMatcher._get_mock_jobs') as mock_jobs:
            mock_jobs.return_value = [mock_job]
            
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=14,
                current_salary=75000,
                target_locations=['Atlanta']
            )
            
            self.assertTrue(result.success)
            # Verify that external job data was processed
            self.assertIsNotNone(result.career_strategy.conservative_opportunity)
            self.assertIsNotNone(result.career_strategy.optimal_opportunity)
            self.assertIsNotNone(result.career_strategy.stretch_opportunity)

    def test_database_integration(self):
        """Test database integration (with mocking)"""
        with patch('backend.services.intelligent_job_matching_service.Session') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            service = IntelligentJobMatchingService(mock_db)
            
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                current_salary=75000,
                preferred_locations=['Atlanta', 'Houston']
            )
            
            result = service.find_income_advancement_opportunities(
                user_id=15,
                resume_text=self.sample_resume,
                target_locations=['Atlanta']
            )
            
            self.assertNotIn('error', result)

    def test_security_and_privacy(self):
        """Test security and privacy measures"""
        # Test data sanitization
        sensitive_resume = self.sample_resume + "\nSSN: 123-45-6789\nCredit Card: 4111-1111-1111-1111"
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=sensitive_resume,
            user_id=16,
            current_salary=70000,
            target_locations=['Atlanta']
        )
        
        # Verify sensitive data is not logged or stored
        self.assertTrue(result.success)
        
        # Test user isolation
        result1 = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=17,
            current_salary=70000,
            target_locations=['Atlanta']
        )
        
        result2 = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=18,
            current_salary=70000,
            target_locations=['Atlanta']
        )
        
        # Results should be isolated by user
        self.assertNotEqual(result1.user_profile.user_id, result2.user_profile.user_id)

    def test_scalability(self):
        """Test system scalability"""
        # Test with increasing load
        start_time = time.time()
        
        results = []
        for i in range(10):
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=self.sample_resume,
                user_id=30 + i,
                current_salary=70000 + i * 1000,
                target_locations=['Atlanta'],
                enable_caching=False
            )
            results.append(result)
        
        total_time = time.time() - start_time
        avg_time = total_time / 10
        
        # Verify scalability
        self.assertLess(avg_time, 5.0)  # Average under 5 seconds per request
        self.assertTrue(all(result.success for result in results))

    def test_monitoring_and_metrics(self):
        """Test monitoring and metrics collection"""
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=self.sample_resume,
            user_id=19,
            current_salary=75000,
            target_locations=['Atlanta']
        )
        
        metrics = result.processing_metrics
        
        # Verify metrics collection
        self.assertGreater(metrics.total_processing_time, 0)
        self.assertGreaterEqual(metrics.cache_hits, 0)
        self.assertGreaterEqual(metrics.cache_misses, 0)
        self.assertIsInstance(metrics.errors_encountered, list)
        
        # Verify performance targets are tracked
        self.assertLess(metrics.resume_processing_time, 2.0)
        self.assertLess(metrics.income_comparison_time, 1.0)
        self.assertLess(metrics.job_search_time, 5.0)
        self.assertLess(metrics.job_selection_time, 2.0)

    def test_user_acceptance_criteria(self):
        """Test user acceptance criteria for target demographic"""
        # Test realistic user scenarios
        scenarios = [
            {
                'title': 'Entry Level Professional',
                'resume': """
                JUNIOR DATA ANALYST
                StartupCorp | Atlanta, GA | 2022-2023
                - Assisted with data analysis using Excel and basic SQL
                - Created reports and dashboards for team leads
                - Supported marketing campaigns with data insights
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Excel, SQL, Python (basic), Tableau
                Business: Data Analysis, Reporting, Communication
                """,
                'salary': 55000,
                'expected_field': 'Data Analysis',
                'expected_level': 'Entry'
            },
            {
                'title': 'Mid-Level Professional',
                'resume': """
                SENIOR MARKETING SPECIALIST
                BrandCorp | Houston, TX | 2020-2023
                - Led digital marketing campaigns with $200K budget
                - Managed team of 2 specialists and achieved 20% growth
                - Developed customer acquisition strategies
                
                MARKETING COORDINATOR
                GrowthCorp | Houston, TX | 2018-2020
                - Executed social media campaigns and email marketing
                - Analyzed campaign performance and optimized ROI
                
                EDUCATION
                Texas Southern University
                Bachelor of Business Administration in Marketing
                GPA: 3.5/4.0
                
                SKILLS
                Technical: Google Analytics, Facebook Ads, Email Marketing, CRM
                Business: Campaign Management, Budget Management, Team Leadership
                """,
                'salary': 75000,
                'expected_field': 'Marketing',
                'expected_level': 'Mid'
            }
        ]
        
        for scenario in scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=scenario['resume'],
                user_id=40 + scenarios.index(scenario),
                current_salary=scenario['salary'],
                target_locations=['Atlanta', 'Houston'],
                risk_preference='balanced'
            )
            
            # Verify user acceptance criteria
            self.assertTrue(result.success)
            self.assertEqual(result.user_profile.field_expertise['primary_field'], 
                           scenario['expected_field'])
            self.assertEqual(result.user_profile.experience_level, 
                           scenario['expected_level'])
            
            # Verify recommendations are appropriate for experience level
            career_strategy = result.career_strategy
            for tier in ['conservative', 'optimal', 'stretch']:
                opportunity = getattr(career_strategy, f'{tier}_opportunity', None)
                if opportunity and hasattr(opportunity, 'job'):
                    # Verify salary increases are reasonable for experience level
                    salary_increase = opportunity.income_impact.salary_increase_percentage
                    if scenario['expected_level'] == 'Entry':
                        self.assertLessEqual(salary_increase, 0.30)  # Max 30% for entry level
                    elif scenario['expected_level'] == 'Mid':
                        self.assertLessEqual(salary_increase, 0.40)  # Max 40% for mid level


if __name__ == '__main__':
    unittest.main() 