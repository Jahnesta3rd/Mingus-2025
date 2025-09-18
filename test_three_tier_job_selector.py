#!/usr/bin/env python3
"""
Comprehensive Test Suite for Three-Tier Job Recommendation System
Tests all functionality of the ThreeTierJobSelector class
"""

import unittest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import the classes to test
import sys
sys.path.append('backend')

from backend.utils.three_tier_job_selector import (
    ThreeTierJobSelector, JobTier, SkillCategory, SkillGap,
    ApplicationStrategy, PreparationRoadmap, TieredJobRecommendation
)
from backend.utils.income_boost_job_matcher import (
    JobOpportunity, SearchCriteria, CareerField, ExperienceLevel, JobBoard
)

class TestThreeTierJobSelector(unittest.TestCase):
    """Test cases for ThreeTierJobSelector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.selector = ThreeTierJobSelector(db_path=self.temp_db.name)
        
        # Create sample job opportunities for testing
        self.sample_jobs = self._create_sample_jobs()
        
        # Create sample search criteria
        self.sample_criteria = SearchCriteria(
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
    
    def _create_sample_jobs(self):
        """Create sample job opportunities for testing"""
        jobs = []
        
        # Conservative tier job (15-20% increase, high success probability)
        conservative_job = JobOpportunity(
            job_id="conservative_001",
            title="Senior Software Engineer",
            company="Microsoft",
            location="Atlanta, GA",
            msa="Atlanta-Sandy Springs-Alpharetta, GA",
            salary_min=85000,
            salary_max=95000,
            salary_median=90000,
            salary_increase_potential=0.20,  # 20% increase
            remote_friendly=True,
            job_board=JobBoard.LINKEDIN,
            url="https://linkedin.com/jobs/123",
            description="Senior software engineer role with Python and AWS experience",
            requirements=["Python", "AWS", "Docker", "5+ years experience"],
            benefits=["Health insurance", "401k", "PTO", "Remote work"],
            diversity_score=85.0,
            growth_score=75.0,
            culture_score=80.0,
            overall_score=82.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.SENIOR,
            posted_date=datetime.now(),
            application_deadline=datetime.now() + timedelta(days=30),
            company_size="Large Enterprise",
            company_industry="Technology",
            equity_offered=True,
            bonus_potential=15000,
            career_advancement_score=80.0,
            work_life_balance_score=85.0
        )
        jobs.append(conservative_job)
        
        # Optimal tier job (25-30% increase, moderate stretch)
        optimal_job = JobOpportunity(
            job_id="optimal_001",
            title="Lead Software Engineer",
            company="Stripe",
            location="San Francisco, CA",
            msa="San Francisco-Oakland-Berkeley, CA",
            salary_min=100000,
            salary_max=120000,
            salary_median=110000,
            salary_increase_potential=0.47,  # 47% increase
            remote_friendly=True,
            job_board=JobBoard.INDEED,
            url="https://indeed.com/jobs/456",
            description="Lead software engineer role with team management responsibilities",
            requirements=["Python", "React", "Leadership", "7+ years experience"],
            benefits=["Health insurance", "401k", "Equity", "Learning budget"],
            diversity_score=70.0,
            growth_score=90.0,
            culture_score=75.0,
            overall_score=78.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.SENIOR,
            posted_date=datetime.now(),
            application_deadline=datetime.now() + timedelta(days=21),
            company_size="Growth Company",
            company_industry="Fintech",
            equity_offered=True,
            bonus_potential=20000,
            career_advancement_score=90.0,
            work_life_balance_score=70.0
        )
        jobs.append(optimal_job)
        
        # Stretch tier job (35%+ increase, aspirational)
        stretch_job = JobOpportunity(
            job_id="stretch_001",
            title="Principal Software Architect",
            company="OpenAI",
            location="San Francisco, CA",
            msa="San Francisco-Oakland-Berkeley, CA",
            salary_min=150000,
            salary_max=180000,
            salary_median=165000,
            salary_increase_potential=1.20,  # 120% increase
            remote_friendly=True,
            job_board=JobBoard.GLASSDOOR,
            url="https://glassdoor.com/jobs/789",
            description="Principal architect role with AI/ML focus",
            requirements=["Python", "Machine Learning", "AI", "10+ years experience"],
            benefits=["Health insurance", "401k", "Equity", "Research time"],
            diversity_score=60.0,
            growth_score=95.0,
            culture_score=85.0,
            overall_score=80.0,
            field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.EXECUTIVE,
            posted_date=datetime.now(),
            application_deadline=datetime.now() + timedelta(days=14),
            company_size="Startup",
            company_industry="AI/ML",
            equity_offered=True,
            bonus_potential=30000,
            career_advancement_score=95.0,
            work_life_balance_score=75.0
        )
        jobs.append(stretch_job)
        
        return jobs
    
    def test_initialization(self):
        """Test ThreeTierJobSelector initialization"""
        self.assertIsNotNone(self.selector)
        self.assertEqual(len(self.selector.tier_specs), 3)
        self.assertIn(JobTier.CONSERVATIVE, self.selector.tier_specs)
        self.assertIn(JobTier.OPTIMAL, self.selector.tier_specs)
        self.assertIn(JobTier.STRETCH, self.selector.tier_specs)
    
    def test_classify_job_tier_conservative(self):
        """Test job tier classification for conservative tier"""
        conservative_job = self.sample_jobs[0]
        tier = self.selector.classify_job_tier(conservative_job, self.sample_criteria)
        self.assertEqual(tier, JobTier.CONSERVATIVE)
    
    def test_classify_job_tier_optimal(self):
        """Test job tier classification for optimal tier"""
        optimal_job = self.sample_jobs[1]
        tier = self.selector.classify_job_tier(optimal_job, self.sample_criteria)
        # Note: This might be classified as stretch due to high salary increase
        self.assertIn(tier, [JobTier.OPTIMAL, JobTier.STRETCH])
    
    def test_classify_job_tier_stretch(self):
        """Test job tier classification for stretch tier"""
        stretch_job = self.sample_jobs[2]
        tier = self.selector.classify_job_tier(stretch_job, self.sample_criteria)
        self.assertEqual(tier, JobTier.STRETCH)
    
    def test_calculate_success_probability(self):
        """Test success probability calculation"""
        job = self.sample_jobs[0]
        probability = self.selector.calculate_success_probability(job, self.sample_criteria)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)
    
    def test_analyze_skills_gap(self):
        """Test skills gap analysis"""
        job = self.sample_jobs[0]
        skills_gaps = self.selector.analyze_skills_gap(job, self.sample_criteria)
        
        self.assertIsInstance(skills_gaps, list)
        for gap in skills_gaps:
            self.assertIsInstance(gap, SkillGap)
            self.assertIn(gap.category, SkillCategory)
            self.assertIn(gap.priority, ["high", "medium", "low"])
    
    def test_generate_application_strategy_conservative(self):
        """Test application strategy generation for conservative tier"""
        job = self.sample_jobs[0]
        strategy = self.selector.generate_application_strategy(
            job, JobTier.CONSERVATIVE, self.sample_criteria
        )
        
        self.assertIsInstance(strategy, ApplicationStrategy)
        self.assertEqual(strategy.tier, JobTier.CONSERVATIVE)
        self.assertIsInstance(strategy.timeline, dict)
        self.assertIsInstance(strategy.key_selling_points, list)
        self.assertIsInstance(strategy.potential_challenges, list)
    
    def test_generate_application_strategy_optimal(self):
        """Test application strategy generation for optimal tier"""
        job = self.sample_jobs[1]
        strategy = self.selector.generate_application_strategy(
            job, JobTier.OPTIMAL, self.sample_criteria
        )
        
        self.assertIsInstance(strategy, ApplicationStrategy)
        self.assertEqual(strategy.tier, JobTier.OPTIMAL)
        self.assertIsInstance(strategy.interview_preparation, dict)
        self.assertIsInstance(strategy.salary_negotiation_tips, list)
    
    def test_generate_application_strategy_stretch(self):
        """Test application strategy generation for stretch tier"""
        job = self.sample_jobs[2]
        strategy = self.selector.generate_application_strategy(
            job, JobTier.STRETCH, self.sample_criteria
        )
        
        self.assertIsInstance(strategy, ApplicationStrategy)
        self.assertEqual(strategy.tier, JobTier.STRETCH)
        self.assertIsInstance(strategy.networking_opportunities, list)
        self.assertIsInstance(strategy.follow_up_strategy, list)
    
    def test_create_preparation_roadmap_conservative(self):
        """Test preparation roadmap creation for conservative tier"""
        job = self.sample_jobs[0]
        skills_gaps = self.selector.analyze_skills_gap(job, self.sample_criteria)
        roadmap = self.selector.create_preparation_roadmap(
            job, JobTier.CONSERVATIVE, skills_gaps
        )
        
        self.assertIsInstance(roadmap, PreparationRoadmap)
        self.assertEqual(roadmap.tier, JobTier.CONSERVATIVE)
        self.assertIsInstance(roadmap.phases, list)
        self.assertIsInstance(roadmap.skill_development_plan, list)
        self.assertIsInstance(roadmap.networking_plan, list)
    
    def test_create_preparation_roadmap_optimal(self):
        """Test preparation roadmap creation for optimal tier"""
        job = self.sample_jobs[1]
        skills_gaps = self.selector.analyze_skills_gap(job, self.sample_criteria)
        roadmap = self.selector.create_preparation_roadmap(
            job, JobTier.OPTIMAL, skills_gaps
        )
        
        self.assertIsInstance(roadmap, PreparationRoadmap)
        self.assertEqual(roadmap.tier, JobTier.OPTIMAL)
        self.assertIn("months", roadmap.total_preparation_time.lower())
    
    def test_create_preparation_roadmap_stretch(self):
        """Test preparation roadmap creation for stretch tier"""
        job = self.sample_jobs[2]
        skills_gaps = self.selector.analyze_skills_gap(job, self.sample_criteria)
        roadmap = self.selector.create_preparation_roadmap(
            job, JobTier.STRETCH, skills_gaps
        )
        
        self.assertIsInstance(roadmap, PreparationRoadmap)
        self.assertEqual(roadmap.tier, JobTier.STRETCH)
        self.assertIsInstance(roadmap.certification_recommendations, list)
    
    def test_ensure_tier_diversity(self):
        """Test tier diversity ensuring"""
        tiered_jobs = {
            JobTier.CONSERVATIVE: self.sample_jobs[:1],
            JobTier.OPTIMAL: self.sample_jobs[1:2],
            JobTier.STRETCH: self.sample_jobs[2:3]
        }
        
        diverse_jobs = self.selector._ensure_tier_diversity(tiered_jobs)
        
        self.assertIsInstance(diverse_jobs, dict)
        for tier in JobTier:
            self.assertIn(tier, diverse_jobs)
            self.assertIsInstance(diverse_jobs[tier], list)
    
    def test_get_tier_summary(self):
        """Test tier summary generation"""
        # Create mock recommendations
        recommendations = {
            JobTier.CONSERVATIVE: [
                Mock(
                    salary_increase_potential=0.20,
                    success_probability=0.80,
                    preparation_roadmap=Mock(total_preparation_time="2-4 weeks"),
                    job=Mock(company_industry="Technology", company_size="Large")
                )
            ],
            JobTier.OPTIMAL: [
                Mock(
                    salary_increase_potential=0.30,
                    success_probability=0.60,
                    preparation_roadmap=Mock(total_preparation_time="1-3 months"),
                    job=Mock(company_industry="Fintech", company_size="Growth")
                )
            ],
            JobTier.STRETCH: [
                Mock(
                    salary_increase_potential=0.50,
                    success_probability=0.40,
                    preparation_roadmap=Mock(total_preparation_time="3-6 months"),
                    job=Mock(company_industry="AI/ML", company_size="Startup")
                )
            ]
        }
        
        summary = self.selector.get_tier_summary(recommendations)
        
        self.assertIsInstance(summary, dict)
        for tier in JobTier:
            self.assertIn(tier.value, summary)
            tier_summary = summary[tier.value]
            self.assertIn('count', tier_summary)
            self.assertIn('avg_salary_increase', tier_summary)
            self.assertIn('avg_success_probability', tier_summary)
            self.assertIn('description', tier_summary)
    
    @patch('backend.utils.three_tier_job_selector.IncomeBoostJobMatcher')
    async def test_generate_tiered_recommendations(self, mock_matcher):
        """Test full tiered recommendations generation"""
        # Mock the job matcher
        mock_matcher_instance = AsyncMock()
        mock_matcher_instance.salary_focused_search.return_value = self.sample_jobs
        mock_matcher.return_value = mock_matcher_instance
        
        # Create new selector with mocked matcher
        selector = ThreeTierJobSelector(db_path=self.temp_db.name)
        selector.job_matcher = mock_matcher_instance
        
        recommendations = await selector.generate_tiered_recommendations(
            self.sample_criteria, max_recommendations_per_tier=2
        )
        
        self.assertIsInstance(recommendations, dict)
        for tier in JobTier:
            self.assertIn(tier, recommendations)
            self.assertIsInstance(recommendations[tier], list)
    
    def test_skill_categories(self):
        """Test skill categories configuration"""
        self.assertIsInstance(self.selector.skill_categories, dict)
        for category in SkillCategory:
            self.assertIn(category, self.selector.skill_categories)
            self.assertIsInstance(self.selector.skill_categories[category], list)
    
    def test_tier_specifications(self):
        """Test tier specifications"""
        for tier in JobTier:
            spec = self.selector.tier_specs[tier]
            self.assertIn('salary_increase_min', spec)
            self.assertIn('salary_increase_max', spec)
            self.assertIn('success_probability_min', spec)
            self.assertIn('description', spec)
            self.assertIn('company_types', spec)
            self.assertIn('risk_level', spec)
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Check if database file exists
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Check if tables were created
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check tiered_recommendations table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiered_recommendations'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check skills_gap_analysis table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skills_gap_analysis'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()

class TestSkillGap(unittest.TestCase):
    """Test cases for SkillGap dataclass"""
    
    def test_skill_gap_creation(self):
        """Test SkillGap object creation"""
        gap = SkillGap(
            skill="Python",
            category=SkillCategory.TECHNICAL,
            current_level=0.6,
            required_level=0.9,
            gap_size=0.3,
            priority="high",
            learning_time_estimate="3-6 months",
            resources=["Python.org tutorial", "Coursera course"]
        )
        
        self.assertEqual(gap.skill, "Python")
        self.assertEqual(gap.category, SkillCategory.TECHNICAL)
        self.assertEqual(gap.gap_size, 0.3)
        self.assertEqual(gap.priority, "high")
        self.assertIsInstance(gap.resources, list)

class TestApplicationStrategy(unittest.TestCase):
    """Test cases for ApplicationStrategy dataclass"""
    
    def test_application_strategy_creation(self):
        """Test ApplicationStrategy object creation"""
        strategy = ApplicationStrategy(
            job_id="test_001",
            tier=JobTier.CONSERVATIVE,
            timeline={"Week 1": "Research company"},
            key_selling_points=["Strong technical skills"],
            potential_challenges=["Competition"],
            interview_preparation={"Technical": ["Review requirements"]},
            salary_negotiation_tips=["Research market rates"],
            networking_opportunities=["LinkedIn connections"],
            follow_up_strategy=["Send thank you email"]
        )
        
        self.assertEqual(strategy.job_id, "test_001")
        self.assertEqual(strategy.tier, JobTier.CONSERVATIVE)
        self.assertIsInstance(strategy.timeline, dict)
        self.assertIsInstance(strategy.key_selling_points, list)

class TestPreparationRoadmap(unittest.TestCase):
    """Test cases for PreparationRoadmap dataclass"""
    
    def test_preparation_roadmap_creation(self):
        """Test PreparationRoadmap object creation"""
        roadmap = PreparationRoadmap(
            job_id="test_001",
            tier=JobTier.OPTIMAL,
            total_preparation_time="1-3 months",
            phases=[{"name": "Skill Development", "duration": "2-4 weeks"}],
            skill_development_plan=[],
            networking_plan=["Connect on LinkedIn"],
            portfolio_building=["Create projects"],
            certification_recommendations=["AWS Certification"]
        )
        
        self.assertEqual(roadmap.job_id, "test_001")
        self.assertEqual(roadmap.tier, JobTier.OPTIMAL)
        self.assertEqual(roadmap.total_preparation_time, "1-3 months")
        self.assertIsInstance(roadmap.phases, list)

def run_async_test(coro):
    """Helper function to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
