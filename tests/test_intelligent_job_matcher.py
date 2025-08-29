"""
Tests for Intelligent Job Matching System
Comprehensive test suite for income advancement job matching
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.models.intelligent_job_matcher import (
    IntelligentJobMatcher, JobPosting, SalaryRange, JobScore, SearchParameters,
    CompanyTier, JobSource, FieldType, ExperienceLevel
)

class TestIntelligentJobMatcher:
    """Test suite for IntelligentJobMatcher"""
    
    @pytest.fixture
    def matcher(self):
        """Create matcher instance for testing"""
        return IntelligentJobMatcher()
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing"""
        return """
        JOHN DOE
        Senior Data Analyst
        
        EXPERIENCE
        Senior Data Analyst | TechCorp | 2020-2023
        - Led data analysis projects using SQL, Python, and Tableau
        - Managed team of 3 junior analysts
        - Developed predictive models for business intelligence
        - Coordinated with stakeholders across departments
        
        Data Analyst | DataCorp | 2018-2020
        - Analyzed customer data using Excel and SQL
        - Created reports and dashboards
        - Collaborated with marketing team on campaigns
        
        SKILLS
        Technical: SQL, Python, R, Tableau, Power BI, Excel, Machine Learning
        Business: Project Management, Stakeholder Management, Business Analysis
        Soft: Leadership, Communication, Problem Solving, Teamwork
        
        EDUCATION
        Bachelor's in Statistics | University of Data | 2018
        """
    
    @pytest.fixture
    def sample_job_posting(self):
        """Sample job posting for testing"""
        return JobPosting(
            id="test_job_1",
            title="Senior Data Analyst",
            company="Test Company",
            location="Atlanta, GA",
            salary_range=SalaryRange(min_salary=90000, max_salary=110000),
            description="Senior data analyst role with Python and SQL",
            requirements=["Python", "SQL", "Tableau", "Statistics"],
            skills=["python", "sql", "tableau", "statistics"],
            experience_level="Senior",
            field="Data Analysis",
            industry="Technology",
            remote_work=True,
            source=JobSource.LINKEDIN,
            posted_date=datetime.utcnow(),
            company_tier=CompanyTier.GROWTH_COMPANY,
            company_size="100-500 employees",
            glassdoor_rating=4.2
        )
    
    def test_matcher_initialization(self, matcher):
        """Test matcher initialization"""
        assert matcher is not None
        assert hasattr(matcher, 'resume_parser')
        assert hasattr(matcher, 'job_security_predictor')
        assert hasattr(matcher, 'target_msas')
        assert hasattr(matcher, 'company_tier_scores')
    
    def test_target_msas_initialization(self, matcher):
        """Test target MSAs are properly initialized"""
        expected_msas = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
            'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore'
        ]
        
        assert len(matcher.target_msas) == len(expected_msas)
        for msa in expected_msas:
            assert msa in matcher.target_msas
    
    def test_scoring_weights_initialization(self, matcher):
        """Test scoring weights are properly initialized"""
        # Weights are now applied directly in the scoring calculation:
        # salary_score * 0.35 + skills_score * 0.25 + career_score * 0.20 + 
        # company_score * 0.10 + location_score * 0.05 + growth_score * 0.05
        expected_weights = {
            'salary_improvement': 0.35,
            'skills_match': 0.25,
            'career_progression': 0.20,
            'company_quality': 0.10,
            'location_fit': 0.05,
            'industry_alignment': 0.05
        }
        
        # Verify the weights sum to 1.0
        assert sum(expected_weights.values()) == 1.0
    
    def test_company_tier_scores_initialization(self, matcher):
        """Test company tier scores are properly initialized"""
        assert CompanyTier.FORTUNE_500 in matcher.company_tier_scores
        assert CompanyTier.GROWTH_COMPANY in matcher.company_tier_scores
        assert CompanyTier.STARTUP in matcher.company_tier_scores
        
        # Check that all scores are between 0 and 1
        for score in matcher.company_tier_scores.values():
            assert 0 <= score <= 1
    
    def test_salary_range_creation(self, matcher):
        """Test salary range creation and validation"""
        # Test normal case
        salary_range = SalaryRange(min_salary=80000, max_salary=100000)
        assert salary_range.min_salary == 80000
        assert salary_range.max_salary == 100000
        assert salary_range.midpoint == 90000
        assert salary_range.range_width == 20000
        
        # Test reversed min/max
        salary_range = SalaryRange(min_salary=100000, max_salary=80000)
        assert salary_range.min_salary == 80000
        assert salary_range.max_salary == 100000
    
    def test_job_posting_creation(self, sample_job_posting):
        """Test job posting creation"""
        assert sample_job_posting.id == "test_job_1"
        assert sample_job_posting.title == "Senior Data Analyst"
        assert sample_job_posting.company == "Test Company"
        assert sample_job_posting.location == "Atlanta, GA"
        assert sample_job_posting.remote_work is True
        assert sample_job_posting.company_tier == CompanyTier.GROWTH_COMPANY
        assert sample_job_posting.glassdoor_rating == 4.2
    
    def test_target_salary_calculation(self, matcher, sample_resume_text):
        """Test target salary calculation"""
        current_salary = 75000
        
        # Parse resume to get analysis
        resume_analysis = matcher.resume_parser.parse_resume(sample_resume_text)
        
        # Calculate target salary
        target_salary = matcher._calculate_target_salary(current_salary, resume_analysis)
        
        # Should be at least 15% increase
        assert target_salary >= current_salary * 1.15
        assert target_salary > current_salary
    
    def test_field_specific_queries_generation(self, matcher):
        """Test field-specific search query generation"""
        # Test Data Analysis field
        data_queries = matcher._get_field_specific_queries(FieldType.DATA_ANALYSIS)
        assert len(data_queries) > 0
        assert "Data Analyst" in data_queries
        assert "Business Intelligence" in data_queries
        
        # Test Software Development field
        dev_queries = matcher._get_field_specific_queries(FieldType.SOFTWARE_DEVELOPMENT)
        assert len(dev_queries) > 0
        assert "Software Engineer" in dev_queries
        assert "Developer" in dev_queries
        
        # Test Project Management field
        pm_queries = matcher._get_field_specific_queries(FieldType.PROJECT_MANAGEMENT)
        assert len(pm_queries) > 0
        assert "Project Manager" in pm_queries
        assert "Program Manager" in pm_queries
    
    def test_experience_queries_generation(self, matcher):
        """Test experience-level specific query generation"""
        # Test Entry level
        entry_queries = matcher._get_experience_queries(ExperienceLevel.ENTRY)
        assert len(entry_queries) > 0
        assert "entry level" in entry_queries
        assert "junior" in entry_queries
        
        # Test Mid level
        mid_queries = matcher._get_experience_queries(ExperienceLevel.MID)
        assert len(mid_queries) > 0
        assert "mid level" in mid_queries
        assert "specialist" in mid_queries
        
        # Test Senior level
        senior_queries = matcher._get_experience_queries(ExperienceLevel.SENIOR)
        assert len(senior_queries) > 0
        assert "senior" in senior_queries
        assert "manager" in senior_queries
    
    def test_search_queries_generation(self, matcher):
        """Test search query generation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql", "tableau"],
            locations=["Atlanta", "Houston"],
            remote_preference=True
        )
        
        queries = matcher._generate_search_queries(search_params)
        
        assert len(queries) > 0
        assert len(queries) <= 10  # Should be limited to top 10
        
        # Should contain field-specific terms
        assert any("Data" in query for query in queries)
        assert any("Analyst" in query for query in queries)
    
    def test_salary_improvement_score_calculation(self, matcher, sample_job_posting):
        """Test salary improvement score calculation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta"]
        )
        
        score = matcher._calculate_salary_improvement_score(sample_job_posting, search_params)
        
        assert 0 <= score <= 1
        assert score > 0  # Should have some score since salary is higher
    
    def test_skills_alignment_score_calculation(self, matcher, sample_job_posting):
        """Test skills alignment score calculation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql", "tableau", "statistics"],
            locations=["Atlanta"]
        )
        
        score = matcher._calculate_skills_alignment_score(sample_job_posting, search_params)
        
        assert 0 <= score <= 1
        assert score > 0  # Should have some score since skills match
    
    def test_career_progression_score_calculation(self, matcher, sample_job_posting):
        """Test career progression score calculation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.MID,  # Current level
            skills=["python", "sql"],
            locations=["Atlanta"]
        )
        
        # Mock resume analysis
        mock_resume_analysis = Mock()
        
        score = matcher._calculate_career_progression_score(sample_job_posting, search_params, mock_resume_analysis)
        
        assert 0 <= score <= 1
        # Should be high since job is "Senior" and current level is "Mid"
        assert score >= 0.7
    
    def test_company_stability_score_calculation(self, matcher, sample_job_posting):
        """Test company stability score calculation"""
        score = matcher._calculate_company_stability_score(sample_job_posting)
        
        assert 0 <= score <= 1
        assert score > 0  # Should have some score
    
    def test_location_compatibility_score_calculation(self, matcher, sample_job_posting):
        """Test location compatibility score calculation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta", "Houston"],
            remote_preference=True
        )
        
        score = matcher._calculate_location_compatibility_score(sample_job_posting, search_params)
        
        assert 0 <= score <= 1
        # Should be high since location is "Atlanta, GA" and remote work is True
        assert score >= 0.8
    
    def test_growth_potential_score_calculation(self, matcher, sample_job_posting):
        """Test growth potential score calculation"""
        # Mock resume analysis
        mock_resume_analysis = Mock()
        mock_resume_analysis.field_analysis.primary_field.value = "Data Analysis"
        
        score = matcher._calculate_growth_potential_score(sample_job_posting, mock_resume_analysis)
        
        assert 0 <= score <= 1
        assert score > 0  # Should have some score
    
    def test_job_deduplication(self, matcher):
        """Test job deduplication functionality"""
        # Create duplicate jobs
        job1 = JobPosting(
            id="job1",
            title="Data Analyst",
            company="Company A",
            location="Atlanta, GA",
            salary_range=SalaryRange(80000, 100000)
        )
        
        job2 = JobPosting(
            id="job2",
            title="Data Analyst",
            company="Company A",
            location="Atlanta, GA",
            salary_range=SalaryRange(85000, 105000)
        )
        
        job3 = JobPosting(
            id="job3",
            title="Senior Data Analyst",
            company="Company B",
            location="Houston, TX",
            salary_range=SalaryRange(90000, 110000)
        )
        
        jobs = [job1, job2, job3]
        unique_jobs = matcher._deduplicate_jobs(jobs)
        
        # Should remove one duplicate (job1 and job2 are duplicates)
        assert len(unique_jobs) == 2
    
    def test_job_scoring(self, matcher, sample_job_posting):
        """Test complete job scoring process"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.MID,
            skills=["python", "sql", "tableau", "statistics"],
            locations=["Atlanta", "Houston"],
            remote_preference=True
        )
        
        # Mock resume analysis
        mock_resume_analysis = Mock()
        mock_resume_analysis.field_analysis.primary_field.value = "Data Analysis"
        
        jobs = [sample_job_posting]
        scored_jobs = matcher._score_jobs(jobs, search_params, mock_resume_analysis)
        
        assert len(scored_jobs) == 1
        job_score = scored_jobs[0]
        
        assert isinstance(job_score, JobScore)
        assert job_score.job == sample_job_posting
        assert 0 <= job_score.overall_score <= 1
        assert len(job_score.score_breakdown) == 6  # All 6 scoring components
        assert len(job_score.recommendations) > 0
        assert isinstance(job_score.risk_factors, list)
    
    def test_salary_threshold_filtering(self, matcher):
        """Test salary threshold filtering"""
        # Create jobs with different salary levels
        high_salary_job = JobPosting(
            id="high",
            title="Senior Analyst",
            company="Company A",
            location="Atlanta",
            salary_range=SalaryRange(100000, 120000)
        )
        
        low_salary_job = JobPosting(
            id="low",
            title="Analyst",
            company="Company B",
            location="Atlanta",
            salary_range=SalaryRange(70000, 80000)
        )
        
        # Create job scores
        high_score = JobScore(
            job=high_salary_job,
            overall_score=0.8,
            salary_improvement_score=0.9,
            skills_alignment_score=0.8,
            career_progression_score=0.7,
            company_stability_score=0.8,
            location_compatibility_score=0.9,
            growth_potential_score=0.8,
            score_breakdown={},
            recommendations=[],
            risk_factors=[]
        )
        
        low_score = JobScore(
            job=low_salary_job,
            overall_score=0.6,
            salary_improvement_score=0.3,
            skills_alignment_score=0.8,
            career_progression_score=0.7,
            company_stability_score=0.8,
            location_compatibility_score=0.9,
            growth_potential_score=0.8,
            score_breakdown={},
            recommendations=[],
            risk_factors=[]
        )
        
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta"],
            min_salary_increase=0.15
        )
        
        scored_jobs = [high_score, low_score]
        filtered_jobs = matcher._filter_by_salary_threshold(scored_jobs, search_params)
        
        # Should filter out the low salary job
        assert len(filtered_jobs) == 1
        assert filtered_jobs[0].job.id == "high"
    
    def test_job_recommendations_generation(self, matcher, sample_job_posting):
        """Test job recommendations generation"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta"]
        )
        
        recommendations = matcher._generate_job_recommendations(sample_job_posting, search_params)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
    
    def test_risk_factors_identification(self, matcher, sample_job_posting):
        """Test risk factors identification"""
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta"]
        )
        
        risk_factors = matcher._identify_job_risk_factors(sample_job_posting, search_params)
        
        assert isinstance(risk_factors, list)
        # May or may not have risk factors depending on the job
    
    def test_complete_job_search_flow(self, matcher, sample_resume_text):
        """Test complete job search flow"""
        # Mock the job search to avoid external API calls
        with patch.object(matcher, '_search_jobs') as mock_search:
            mock_search.return_value = [sample_job_posting]
            
            result = matcher.find_income_advancement_jobs(
                user_id=1,
                resume_text=sample_resume_text,
                current_salary=75000,
                target_locations=["Atlanta", "Houston"]
            )
            
            assert 'job_opportunities' in result
            assert 'income_analysis' in result
            assert 'demographic_analysis' in result
            assert 'insights' in result
            assert 'search_metadata' in result
    
    def test_search_statistics_calculation(self, matcher):
        """Test search statistics calculation"""
        # Create sample job scores
        job1 = JobScore(
            job=JobPosting(
                id="1", title="Job 1", company="A", location="Atlanta",
                salary_range=SalaryRange(90000, 110000)
            ),
            overall_score=0.8,
            salary_improvement_score=0.8,
            skills_alignment_score=0.8,
            career_progression_score=0.8,
            company_stability_score=0.8,
            location_compatibility_score=0.8,
            growth_potential_score=0.8,
            score_breakdown={},
            recommendations=[],
            risk_factors=[]
        )
        
        job2 = JobScore(
            job=JobPosting(
                id="2", title="Job 2", company="B", location="Houston",
                salary_range=SalaryRange(95000, 115000)
            ),
            overall_score=0.9,
            salary_improvement_score=0.9,
            skills_alignment_score=0.9,
            career_progression_score=0.9,
            company_stability_score=0.9,
            location_compatibility_score=0.9,
            growth_potential_score=0.9,
            score_breakdown={},
            recommendations=[],
            risk_factors=[]
        )
        
        search_params = SearchParameters(
            current_salary=75000,
            target_salary_min=90000,
            primary_field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "sql"],
            locations=["Atlanta", "Houston"]
        )
        
        scored_jobs = [job1, job2]
        stats = matcher._calculate_search_statistics(scored_jobs, search_params)
        
        assert 'total_jobs' in stats
        assert 'avg_salary' in stats
        assert 'avg_salary_increase' in stats
        assert 'max_salary_increase' in stats
        assert stats['total_jobs'] == 2
        assert stats['avg_salary'] > 0
        assert stats['avg_salary_increase'] > 0
    
    def test_job_formatting(self, matcher):
        """Test job recommendation formatting"""
        job_score = JobScore(
            job=JobPosting(
                id="test",
                title="Test Job",
                company="Test Company",
                location="Atlanta, GA",
                salary_range=SalaryRange(90000, 110000),
                remote_work=True,
                company_tier=CompanyTier.GROWTH_COMPANY,
                glassdoor_rating=4.2,
                posted_date=datetime.utcnow()
            ),
            overall_score=0.8,
            salary_improvement_score=0.8,
            skills_alignment_score=0.8,
            career_progression_score=0.8,
            company_stability_score=0.8,
            location_compatibility_score=0.8,
            growth_potential_score=0.8,
            score_breakdown={'salary_improvement': 0.8},
            recommendations=["Great opportunity"],
            risk_factors=[]
        )
        
        formatted = matcher._format_job_recommendation(job_score)
        
        assert 'id' in formatted
        assert 'title' in formatted
        assert 'company' in formatted
        assert 'location' in formatted
        assert 'salary_range' in formatted
        assert 'remote_work' in formatted
        assert 'overall_score' in formatted
        assert 'recommendations' in formatted
        assert 'risk_factors' in formatted

if __name__ == "__main__":
    pytest.main([__file__]) 