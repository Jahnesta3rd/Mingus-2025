"""
Tests for Job Selection Algorithm
Comprehensive test suite for 3-tier career advancement selection
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.models.job_selection_algorithm import (
    JobSelectionAlgorithm, CareerAdvancementStrategy, CareerTier,
    ApplicationStrategy, SkillGapAnalysis, IncomeImpactAnalysis,
    ApplicationStrategyGuide, CareerOpportunity
)
from ml.models.intelligent_job_matcher import JobPosting, JobScore, SalaryRange, CompanyTier, JobSource
from ml.models.resume_parser import FieldType, ExperienceLevel

class TestJobSelectionAlgorithm:
    """Test suite for JobSelectionAlgorithm"""
    
    @pytest.fixture
    def algorithm(self):
        """Create algorithm instance for testing"""
        return JobSelectionAlgorithm()
    
    @pytest.fixture
    def sample_job_scores(self):
        """Create sample job scores for testing"""
        # Conservative job
        conservative_job = JobPosting(
            id="conservative_1",
            title="Senior Data Analyst",
            company="Established Corp",
            location="Atlanta, GA",
            salary_range=SalaryRange(min_salary=85000, max_salary=95000),
            requirements=["SQL", "Python", "Tableau", "Excel"],
            skills=["sql", "python", "tableau", "excel"],
            experience_level="Senior",
            field="Data Analysis",
            company_tier=CompanyTier.ESTABLISHED,
            glassdoor_rating=4.2
        )
        
        conservative_score = JobScore(
            job=conservative_job,
            overall_score=0.85,
            salary_improvement_score=0.8,
            skills_alignment_score=0.9,
            career_progression_score=0.7,
            company_stability_score=0.9,
            location_compatibility_score=0.9,
            growth_potential_score=0.8,
            score_breakdown={},
            recommendations=["Great conservative opportunity"],
            risk_factors=[]
        )
        
        # Optimal job
        optimal_job = JobPosting(
            id="optimal_1",
            title="Lead Data Analyst",
            company="Growth Tech",
            location="Houston, TX",
            salary_range=SalaryRange(min_salary=95000, max_salary=110000),
            requirements=["SQL", "Python", "Machine Learning", "Leadership"],
            skills=["sql", "python", "machine_learning", "leadership"],
            experience_level="Senior",
            field="Data Analysis",
            company_tier=CompanyTier.GROWTH_COMPANY,
            glassdoor_rating=4.0
        )
        
        optimal_score = JobScore(
            job=optimal_job,
            overall_score=0.75,
            salary_improvement_score=0.9,
            skills_alignment_score=0.75,
            career_progression_score=0.9,
            company_stability_score=0.8,
            location_compatibility_score=0.8,
            growth_potential_score=0.9,
            score_breakdown={},
            recommendations=["Strong optimal opportunity"],
            risk_factors=["Some skill gaps"]
        )
        
        # Stretch job
        stretch_job = JobPosting(
            id="stretch_1",
            title="Data Science Manager",
            company="Fortune 500 Corp",
            location="New York, NY",
            salary_range=SalaryRange(min_salary=120000, max_salary=140000),
            requirements=["SQL", "Python", "Machine Learning", "Management", "Strategy"],
            skills=["sql", "python", "machine_learning", "management", "strategy"],
            experience_level="Senior",
            field="Data Analysis",
            company_tier=CompanyTier.FORTUNE_500,
            glassdoor_rating=4.5
        )
        
        stretch_score = JobScore(
            job=stretch_job,
            overall_score=0.65,
            salary_improvement_score=1.0,
            skills_alignment_score=0.6,
            career_progression_score=1.0,
            company_stability_score=0.9,
            location_compatibility_score=0.7,
            growth_potential_score=1.0,
            score_breakdown={},
            recommendations=["Ambitious stretch opportunity"],
            risk_factors=["Significant skill gaps", "High competition"]
        )
        
        return [conservative_score, optimal_score, stretch_score]
    
    @pytest.fixture
    def sample_search_params(self):
        """Create sample search parameters"""
        from ml.models.intelligent_job_matcher import SearchParameters
        
        return SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["sql", "python", "tableau", "excel"],
            locations=["Atlanta", "Houston", "New York"],
            remote_preference=True,
            min_salary_increase=0.15
        )
    
    @pytest.fixture
    def sample_resume_analysis(self):
        """Create sample resume analysis"""
        mock_analysis = Mock()
        mock_analysis.field_analysis.primary_field = FieldType.DATA_ANALYSIS
        mock_analysis.experience_analysis.level = ExperienceLevel.SENIOR
        mock_analysis.skills_analysis.technical_skills = {
            'sql': 0.9,
            'python': 0.8,
            'tableau': 0.7,
            'excel': 0.9
        }
        mock_analysis.skills_analysis.business_skills = {
            'project_management': 0.6,
            'stakeholder_management': 0.7
        }
        mock_analysis.leadership_potential = 0.7
        return mock_analysis
    
    def test_algorithm_initialization(self, algorithm):
        """Test algorithm initialization"""
        assert algorithm is not None
        assert hasattr(algorithm, 'tier_criteria')
        assert hasattr(algorithm, 'tier_weights')
        assert hasattr(algorithm, 'learning_resources')
        
        # Check tier criteria
        assert CareerTier.CONSERVATIVE in algorithm.tier_criteria
        assert CareerTier.OPTIMAL in algorithm.tier_criteria
        assert CareerTier.STRETCH in algorithm.tier_criteria
        
        # Check tier weights
        assert CareerTier.CONSERVATIVE in algorithm.tier_weights
        assert CareerTier.OPTIMAL in algorithm.tier_weights
        assert CareerTier.STRETCH in algorithm.tier_weights
    
    def test_tier_criteria_validation(self, algorithm):
        """Test tier criteria are properly configured"""
        conservative_criteria = algorithm.tier_criteria[CareerTier.CONSERVATIVE]
        optimal_criteria = algorithm.tier_criteria[CareerTier.OPTIMAL]
        stretch_criteria = algorithm.tier_criteria[CareerTier.STRETCH]
        
        # Conservative criteria
        assert conservative_criteria['salary_increase_min'] == 0.15
        assert conservative_criteria['salary_increase_max'] == 0.20
        assert conservative_criteria['skills_match_min'] == 0.80
        assert conservative_criteria['risk_level'] == 'low'
        
        # Optimal criteria
        assert optimal_criteria['salary_increase_min'] == 0.25
        assert optimal_criteria['salary_increase_max'] == 0.30
        assert optimal_criteria['skills_match_min'] == 0.70
        assert optimal_criteria['risk_level'] == 'medium'
        
        # Stretch criteria
        assert stretch_criteria['salary_increase_min'] == 0.35
        assert stretch_criteria['skills_match_min'] == 0.60
        assert stretch_criteria['risk_level'] == 'high'
    
    def test_tier_weights_validation(self, algorithm):
        """Test tier weights sum to 1.0 for each tier"""
        for tier, weights in algorithm.tier_weights.items():
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.001, f"Weights for {tier} don't sum to 1.0"
    
    def test_job_classification_into_tiers(self, algorithm, sample_job_scores, sample_search_params):
        """Test job classification into tiers"""
        tiered_jobs = algorithm._classify_jobs_into_tiers(sample_job_scores, sample_search_params)
        
        # Should have jobs in each tier
        assert CareerTier.CONSERVATIVE in tiered_jobs
        assert CareerTier.OPTIMAL in tiered_jobs
        assert CareerTier.STRETCH in tiered_jobs
        
        # Check that jobs are properly classified
        assert len(tiered_jobs[CareerTier.CONSERVATIVE]) >= 1
        assert len(tiered_jobs[CareerTier.OPTIMAL]) >= 1
        assert len(tiered_jobs[CareerTier.STRETCH]) >= 1
    
    def test_tier_specific_scoring(self, algorithm, sample_job_scores):
        """Test tier-specific scoring"""
        # Test conservative tier scoring
        conservative_score = algorithm._calculate_tier_specific_score(
            sample_job_scores[0], CareerTier.CONSERVATIVE
        )
        assert 0 <= conservative_score <= 1
        
        # Test optimal tier scoring
        optimal_score = algorithm._calculate_tier_specific_score(
            sample_job_scores[1], CareerTier.OPTIMAL
        )
        assert 0 <= optimal_score <= 1
        
        # Test stretch tier scoring
        stretch_score = algorithm._calculate_tier_specific_score(
            sample_job_scores[2], CareerTier.STRETCH
        )
        assert 0 <= stretch_score <= 1
    
    def test_income_impact_analysis(self, algorithm, sample_job_scores, sample_search_params):
        """Test income impact analysis"""
        job = sample_job_scores[0].job
        income_impact = algorithm._analyze_income_impact(job, sample_search_params)
        
        assert isinstance(income_impact, IncomeImpactAnalysis)
        assert income_impact.current_salary == 75000
        assert income_impact.salary_increase_percentage > 0
        assert 0 <= income_impact.current_percentile <= 100
        assert 0 <= income_impact.new_percentile <= 100
    
    def test_skill_gap_analysis(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test skill gap analysis"""
        job = sample_job_scores[0].job
        skill_gap_analysis = algorithm._analyze_skill_gaps(job, sample_search_params, sample_resume_analysis)
        
        assert isinstance(skill_gap_analysis, SkillGapAnalysis)
        assert 0 <= skill_gap_analysis.skills_match_percentage <= 1
        assert isinstance(skill_gap_analysis.missing_critical_skills, list)
        assert isinstance(skill_gap_analysis.learning_recommendations, list)
        assert isinstance(skill_gap_analysis.timeline_to_readiness, str)
    
    def test_application_strategy_generation(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test application strategy generation"""
        job = sample_job_scores[0].job
        skill_gap_analysis = algorithm._analyze_skill_gaps(job, sample_search_params, sample_resume_analysis)
        
        app_strategy = algorithm._generate_application_strategy(
            job, CareerTier.CONSERVATIVE, skill_gap_analysis, sample_search_params
        )
        
        assert isinstance(app_strategy, ApplicationStrategyGuide)
        assert app_strategy.strategy_type in [strategy.value for strategy in ApplicationStrategy]
        assert 0 <= app_strategy.success_probability <= 1
        assert isinstance(app_strategy.preparation_steps, list)
        assert isinstance(app_strategy.risk_factors, list)
        assert isinstance(app_strategy.mitigation_strategies, list)
    
    def test_opportunity_package_creation(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test opportunity package creation"""
        job_score = sample_job_scores[0]
        
        opportunity = algorithm._create_opportunity_package(
            job_score, CareerTier.CONSERVATIVE, sample_search_params, sample_resume_analysis
        )
        
        assert isinstance(opportunity, CareerOpportunity)
        assert opportunity.tier == CareerTier.CONSERVATIVE
        assert opportunity.job == job_score.job
        assert isinstance(opportunity.income_impact, IncomeImpactAnalysis)
        assert isinstance(opportunity.skill_gap_analysis, SkillGapAnalysis)
        assert isinstance(opportunity.application_strategy, ApplicationStrategyGuide)
        assert isinstance(opportunity.selection_reasoning, str)
        assert isinstance(opportunity.alternative_options, list)
    
    def test_complete_strategy_selection(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test complete strategy selection process"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        assert isinstance(strategy, CareerAdvancementStrategy)
        assert isinstance(strategy.conservative_opportunity, CareerOpportunity)
        assert isinstance(strategy.optimal_opportunity, CareerOpportunity)
        assert isinstance(strategy.stretch_opportunity, CareerOpportunity)
        assert isinstance(strategy.strategy_summary, dict)
        assert isinstance(strategy.timeline_recommendations, dict)
        assert isinstance(strategy.risk_mitigation_plan, dict)
        assert isinstance(strategy.generated_at, datetime)
    
    def test_diversity_enforcement(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test diversity enforcement across selections"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        # Check geographic diversity
        locations = [
            strategy.conservative_opportunity.job.location,
            strategy.optimal_opportunity.job.location,
            strategy.stretch_opportunity.job.location
        ]
        
        # Should have at least 2 different locations
        assert len(set(locations)) >= 2, "Limited geographic diversity"
        
        # Check company diversity
        companies = [
            strategy.conservative_opportunity.job.company,
            strategy.optimal_opportunity.job.company,
            strategy.stretch_opportunity.job.company
        ]
        
        # Should have at least 2 different companies
        assert len(set(companies)) >= 2, "Limited company diversity"
    
    def test_fallback_opportunity_creation(self, algorithm, sample_search_params, sample_resume_analysis):
        """Test fallback opportunity creation when no jobs meet criteria"""
        empty_job_list = []
        
        fallback = algorithm._create_fallback_opportunity(
            CareerTier.CONSERVATIVE, sample_search_params, sample_resume_analysis
        )
        
        assert isinstance(fallback, CareerOpportunity)
        assert fallback.tier == CareerTier.CONSERVATIVE
        assert fallback.job.title == "Conservative Data Analysis"
        assert fallback.overall_score == 0.5
    
    def test_salary_percentile_calculation(self, algorithm):
        """Test salary percentile calculation"""
        # Test different salary levels
        low_salary = 50000
        avg_salary = 85000
        high_salary = 120000
        
        low_percentile = algorithm._calculate_salary_percentile(low_salary, "Data Analysis", "Mid")
        avg_percentile = algorithm._calculate_salary_percentile(avg_salary, "Data Analysis", "Mid")
        high_percentile = algorithm._calculate_salary_percentile(high_salary, "Data Analysis", "Mid")
        
        assert low_percentile < avg_percentile
        assert avg_percentile < high_percentile
        assert 0 <= low_percentile <= 100
        assert 0 <= avg_percentile <= 100
        assert 0 <= high_percentile <= 100
    
    def test_cost_of_living_adjustment(self, algorithm):
        """Test cost of living adjustment calculation"""
        # Test different locations
        atlanta_adjustment = algorithm._calculate_cost_of_living_adjustment("Atlanta, GA")
        nyc_adjustment = algorithm._calculate_cost_of_living_adjustment("New York, NY")
        remote_adjustment = algorithm._calculate_cost_of_living_adjustment("Remote")
        
        assert atlanta_adjustment == 1.0
        assert nyc_adjustment == 1.5
        assert remote_adjustment == 1.0
    
    def test_strategy_summary_generation(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test strategy summary generation"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        summary = strategy.strategy_summary
        
        assert 'total_salary_increase_potential' in summary
        assert 'average_salary_increase' in summary
        assert 'risk_distribution' in summary
        assert 'timeline_recommendation' in summary
        assert 'success_probability_range' in summary
        
        # Check salary increase data
        salary_data = summary['total_salary_increase_potential']
        assert 'conservative' in salary_data
        assert 'optimal' in salary_data
        assert 'stretch' in salary_data
        
        # Check risk distribution
        risk_data = summary['risk_distribution']
        assert risk_data['conservative'] == 'low'
        assert risk_data['optimal'] == 'medium'
        assert risk_data['stretch'] == 'high'
    
    def test_timeline_recommendations(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test timeline recommendations generation"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        timeline = strategy.timeline_recommendations
        
        assert 'immediate_actions' in timeline
        assert 'week_1_4' in timeline
        assert 'month_2_3' in timeline
        assert 'month_4_6' in timeline
        
        # Check that each timeline has actions
        for period, actions in timeline.items():
            assert isinstance(actions, list)
            assert len(actions) > 0
    
    def test_risk_mitigation_plan(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test risk mitigation plan generation"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        risk_plan = strategy.risk_mitigation_plan
        
        assert 'conservative_risks' in risk_plan
        assert 'conservative_mitigation' in risk_plan
        assert 'optimal_risks' in risk_plan
        assert 'optimal_mitigation' in risk_plan
        assert 'stretch_risks' in risk_plan
        assert 'stretch_mitigation' in risk_plan
        assert 'overall_risk_management' in risk_plan
    
    def test_learning_resources_validation(self, algorithm):
        """Test learning resources are properly configured"""
        resources = algorithm.learning_resources
        
        # Check that key skills have resources
        key_skills = ['python', 'sql', 'tableau', 'machine_learning', 'project_management']
        
        for skill in key_skills:
            if skill in resources:
                skill_resources = resources[skill]
                assert 'courses' in skill_resources
                assert 'timeline' in skill_resources
                assert 'difficulty' in skill_resources
                assert 'cost' in skill_resources
                
                assert isinstance(skill_resources['courses'], list)
                assert len(skill_resources['courses']) > 0
                assert isinstance(skill_resources['timeline'], str)
                assert isinstance(skill_resources['difficulty'], str)
                assert isinstance(skill_resources['cost'], str)
    
    def test_application_strategy_types(self, algorithm):
        """Test all application strategy types are properly defined"""
        strategy_types = [strategy.value for strategy in ApplicationStrategy]
        
        expected_types = [
            'immediate_apply',
            'upskill_first',
            'networking_required',
            'strategic_preparation'
        ]
        
        assert set(strategy_types) == set(expected_types)
    
    def test_career_tier_enum(self, algorithm):
        """Test career tier enum values"""
        tier_values = [tier.value for tier in CareerTier]
        
        expected_tiers = ['conservative', 'optimal', 'stretch']
        
        assert set(tier_values) == set(expected_tiers)
    
    def test_strategy_with_insufficient_jobs(self, algorithm, sample_search_params, sample_resume_analysis):
        """Test strategy generation with insufficient jobs"""
        # Create only one job that doesn't meet any tier criteria
        insufficient_job = JobPosting(
            id="insufficient",
            title="Junior Analyst",
            company="Small Company",
            location="Remote",
            salary_range=SalaryRange(min_salary=60000, max_salary=70000),  # Below 15% increase
            requirements=["Excel"],
            skills=["excel"],
            experience_level="Entry",
            field="Data Analysis"
        )
        
        insufficient_score = JobScore(
            job=insufficient_job,
            overall_score=0.3,
            salary_improvement_score=0.2,  # Below threshold
            skills_alignment_score=0.5,
            career_progression_score=0.3,
            company_stability_score=0.6,
            location_compatibility_score=0.8,
            growth_potential_score=0.4,
            score_breakdown={},
            recommendations=[],
            risk_factors=[]
        )
        
        strategy = algorithm.select_career_advancement_strategy(
            [insufficient_score], sample_search_params, sample_resume_analysis
        )
        
        # Should create fallback opportunities
        assert isinstance(strategy.conservative_opportunity, CareerOpportunity)
        assert isinstance(strategy.optimal_opportunity, CareerOpportunity)
        assert isinstance(strategy.stretch_opportunity, CareerOpportunity)
    
    def test_strategy_formatting(self, algorithm, sample_job_scores, sample_search_params, sample_resume_analysis):
        """Test strategy formatting for API response"""
        strategy = algorithm.select_career_advancement_strategy(
            sample_job_scores, sample_search_params, sample_resume_analysis
        )
        
        # Test that all required fields are present and properly formatted
        assert strategy.conservative_opportunity.tier == CareerTier.CONSERVATIVE
        assert strategy.optimal_opportunity.tier == CareerTier.OPTIMAL
        assert strategy.stretch_opportunity.tier == CareerTier.STRETCH
        
        # Test that each opportunity has complete data
        for opportunity in [strategy.conservative_opportunity, strategy.optimal_opportunity, strategy.stretch_opportunity]:
            assert opportunity.job is not None
            assert opportunity.income_impact is not None
            assert opportunity.skill_gap_analysis is not None
            assert opportunity.application_strategy is not None
            assert opportunity.selection_reasoning is not None
            assert opportunity.alternative_options is not None
            assert opportunity.backup_recommendations is not None

if __name__ == "__main__":
    pytest.main([__file__]) 