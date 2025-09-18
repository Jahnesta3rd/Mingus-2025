#!/usr/bin/env python3
"""
Integration Test for Three-Tier Job Recommendation System
Tests the complete integration with the existing job matching system
"""

import unittest
import asyncio
import tempfile
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.three_tier_job_selector import ThreeTierJobSelector, JobTier
from backend.utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel

class TestThreeTierIntegration(unittest.TestCase):
    """Integration tests for the three-tier system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.selector = ThreeTierJobSelector(db_path=self.temp_db.name)
        
        # Create test search criteria
        self.criteria = SearchCriteria(
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
            min_company_rating=3.5
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
    
    def test_selector_initialization(self):
        """Test that the selector initializes correctly"""
        self.assertIsNotNone(self.selector)
        self.assertIsNotNone(self.selector.tier_specs)
        self.assertEqual(len(self.selector.tier_specs), 3)
    
    def test_tier_specifications(self):
        """Test that tier specifications are properly configured"""
        for tier in JobTier:
            spec = self.selector.tier_specs[tier]
            
            # Check required fields
            self.assertIn('salary_increase_min', spec)
            self.assertIn('salary_increase_max', spec)
            self.assertIn('success_probability_min', spec)
            self.assertIn('description', spec)
            self.assertIn('company_types', spec)
            self.assertIn('risk_level', spec)
            
            # Check value ranges
            self.assertGreater(spec['salary_increase_min'], 0)
            self.assertLess(spec['salary_increase_max'], 1)
            self.assertGreater(spec['success_probability_min'], 0)
            self.assertLessEqual(spec['success_probability_min'], 1)
    
    def test_skill_categories(self):
        """Test that skill categories are properly configured"""
        from backend.utils.three_tier_job_selector import SkillCategory
        
        self.assertIsInstance(self.selector.skill_categories, dict)
        
        for category in SkillCategory:
            self.assertIn(category, self.selector.skill_categories)
            self.assertIsInstance(self.selector.skill_categories[category], list)
            self.assertGreater(len(self.selector.skill_categories[category]), 0)
    
    def test_database_initialization(self):
        """Test that database tables are created correctly"""
        import sqlite3
        
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check tiered_recommendations table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tiered_recommendations'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        # Check skills_gap_analysis table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='skills_gap_analysis'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    @patch('backend.utils.three_tier_job_selector.IncomeBoostJobMatcher')
    async def test_full_integration_workflow(self, mock_matcher_class):
        """Test the complete integration workflow"""
        # Mock the job matcher
        mock_matcher = AsyncMock()
        mock_matcher_class.return_value = mock_matcher
        
        # Create mock job opportunities
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        mock_jobs = [
            JobOpportunity(
                job_id="test_001",
                title="Senior Software Engineer",
                company="Test Company",
                location="Atlanta, GA",
                msa="Atlanta-Sandy Springs-Alpharetta, GA",
                salary_min=85000,
                salary_max=95000,
                salary_median=90000,
                salary_increase_potential=0.20,
                remote_friendly=True,
                job_board=JobBoard.LINKEDIN,
                url="https://test.com/job1",
                description="Senior software engineer role",
                requirements=["Python", "AWS", "5+ years"],
                benefits=["Health insurance", "401k"],
                diversity_score=80.0,
                growth_score=75.0,
                culture_score=85.0,
                overall_score=80.0,
                field=CareerField.TECHNOLOGY,
                experience_level=ExperienceLevel.SENIOR,
                posted_date=datetime.now(),
                application_deadline=None,
                company_size="Large",
                company_industry="Technology",
                equity_offered=True,
                bonus_potential=10000,
                career_advancement_score=80.0,
                work_life_balance_score=85.0
            )
        ]
        
        mock_matcher.salary_focused_search.return_value = mock_jobs
        
        # Test the full workflow
        selector = ThreeTierJobSelector(db_path=self.temp_db.name)
        selector.job_matcher = mock_matcher
        
        recommendations = await selector.generate_tiered_recommendations(
            self.criteria, max_recommendations_per_tier=1
        )
        
        # Verify results
        self.assertIsInstance(recommendations, dict)
        self.assertIn(JobTier.CONSERVATIVE, recommendations)
        self.assertIn(JobTier.OPTIMAL, recommendations)
        self.assertIn(JobTier.STRETCH, recommendations)
        
        # Check that the job matcher was called
        mock_matcher.salary_focused_search.assert_called_once_with(self.criteria)
    
    def test_classify_job_tier_edge_cases(self):
        """Test job tier classification with edge cases"""
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        # Test job with no salary information
        job_no_salary = JobOpportunity(
            job_id="no_salary",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=None,
            salary_max=None,
            salary_median=None,
            salary_increase_potential=0.25,
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://test.com",
            description="Test job",
            requirements=[],
            benefits=[],
            diversity_score=50.0,
            growth_score=50.0,
            culture_score=50.0,
            overall_score=50.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=False,
            bonus_potential=None,
            career_advancement_score=50.0,
            work_life_balance_score=50.0
        )
        
        tier = self.selector.classify_job_tier(job_no_salary, self.criteria)
        self.assertIsNotNone(tier)
        self.assertIn(tier, JobTier)
    
    def test_skills_gap_analysis_with_empty_job(self):
        """Test skills gap analysis with minimal job data"""
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        minimal_job = JobOpportunity(
            job_id="minimal",
            title="Minimal Job",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=None,
            salary_max=None,
            salary_median=None,
            salary_increase_potential=0.0,
            remote_friendly=False,
            job_board=JobBoard.LINKEDIN,
            url="https://test.com",
            description="",
            requirements=[],
            benefits=[],
            diversity_score=0.0,
            growth_score=0.0,
            culture_score=0.0,
            overall_score=0.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.ENTRY,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size=None,
            company_industry=None,
            equity_offered=False,
            bonus_potential=None,
            career_advancement_score=0.0,
            work_life_balance_score=0.0
        )
        
        skills_gaps = self.selector.analyze_skills_gap(minimal_job, self.criteria)
        self.assertIsInstance(skills_gaps, list)
        # Should still return some sample skills gaps even with minimal data
    
    def test_application_strategy_generation(self):
        """Test application strategy generation for all tiers"""
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        test_job = JobOpportunity(
            job_id="strategy_test",
            title="Test Engineer",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=80000,
            salary_max=100000,
            salary_median=90000,
            salary_increase_potential=0.20,
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://test.com",
            description="Test engineering role",
            requirements=["Python", "Testing"],
            benefits=["Health insurance"],
            diversity_score=70.0,
            growth_score=80.0,
            culture_score=75.0,
            overall_score=75.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=5000,
            career_advancement_score=80.0,
            work_life_balance_score=75.0
        )
        
        for tier in JobTier:
            strategy = self.selector.generate_application_strategy(
                test_job, tier, self.criteria
            )
            
            self.assertIsNotNone(strategy)
            self.assertEqual(strategy.job_id, test_job.job_id)
            self.assertEqual(strategy.tier, tier)
            self.assertIsInstance(strategy.timeline, dict)
            self.assertIsInstance(strategy.key_selling_points, list)
            self.assertIsInstance(strategy.potential_challenges, list)
            self.assertIsInstance(strategy.interview_preparation, dict)
            self.assertIsInstance(strategy.salary_negotiation_tips, list)
            self.assertIsInstance(strategy.networking_opportunities, list)
            self.assertIsInstance(strategy.follow_up_strategy, list)
    
    def test_preparation_roadmap_generation(self):
        """Test preparation roadmap generation for all tiers"""
        from backend.utils.three_tier_job_selector import SkillGap, SkillCategory
        
        # Create sample skills gaps
        skills_gaps = [
            SkillGap(
                skill="Python",
                category=SkillCategory.TECHNICAL,
                current_level=0.6,
                required_level=0.9,
                gap_size=0.3,
                priority="high",
                learning_time_estimate="3-6 months",
                resources=["Python.org tutorial", "Coursera course"]
            )
        ]
        
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        test_job = JobOpportunity(
            job_id="roadmap_test",
            title="Test Developer",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=70000,
            salary_max=90000,
            salary_median=80000,
            salary_increase_potential=0.07,
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://test.com",
            description="Test development role",
            requirements=["Python", "Development"],
            benefits=["Health insurance"],
            diversity_score=60.0,
            growth_score=70.0,
            culture_score=65.0,
            overall_score=65.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=False,
            bonus_potential=None,
            career_advancement_score=70.0,
            work_life_balance_score=65.0
        )
        
        for tier in JobTier:
            roadmap = self.selector.create_preparation_roadmap(
                test_job, tier, skills_gaps
            )
            
            self.assertIsNotNone(roadmap)
            self.assertEqual(roadmap.job_id, test_job.job_id)
            self.assertEqual(roadmap.tier, tier)
            self.assertIsInstance(roadmap.total_preparation_time, str)
            self.assertIsInstance(roadmap.phases, list)
            self.assertIsInstance(roadmap.skill_development_plan, list)
            self.assertIsInstance(roadmap.networking_plan, list)
            self.assertIsInstance(roadmap.portfolio_building, list)
            self.assertIsInstance(roadmap.certification_recommendations, list)
    
    def test_tier_summary_generation(self):
        """Test tier summary generation"""
        from backend.utils.three_tier_job_selector import TieredJobRecommendation
        from backend.utils.income_boost_job_matcher import JobOpportunity, JobBoard
        from datetime import datetime
        
        # Create mock recommendations
        mock_job = JobOpportunity(
            job_id="summary_test",
            title="Test Role",
            company="Test Company",
            location="Test Location",
            msa="Test MSA",
            salary_min=80000,
            salary_max=100000,
            salary_median=90000,
            salary_increase_potential=0.20,
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://test.com",
            description="Test role",
            requirements=[],
            benefits=[],
            diversity_score=70.0,
            growth_score=80.0,
            culture_score=75.0,
            overall_score=75.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            posted_date=datetime.now(),
            application_deadline=None,
            company_size="Mid",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=5000,
            career_advancement_score=80.0,
            work_life_balance_score=75.0
        )
        
        mock_recommendation = TieredJobRecommendation(
            job=mock_job,
            tier=JobTier.CONSERVATIVE,
            success_probability=0.8,
            salary_increase_potential=0.20,
            skills_gap_analysis=[],
            application_strategy=Mock(),
            preparation_roadmap=Mock(total_preparation_time="2-4 weeks"),
            diversity_analysis={},
            company_culture_fit=0.8,
            career_advancement_potential=0.8
        )
        
        recommendations = {
            JobTier.CONSERVATIVE: [mock_recommendation],
            JobTier.OPTIMAL: [],
            JobTier.STRETCH: []
        }
        
        summary = self.selector.get_tier_summary(recommendations)
        
        self.assertIsInstance(summary, dict)
        self.assertIn('conservative', summary)
        self.assertIn('optimal', summary)
        self.assertIn('stretch', summary)
        
        conservative_summary = summary['conservative']
        self.assertEqual(conservative_summary['count'], 1)
        self.assertIn('avg_salary_increase', conservative_summary)
        self.assertIn('avg_success_probability', conservative_summary)
        self.assertIn('description', conservative_summary)

def run_async_test(coro):
    """Helper function to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)
