"""
Tests for Advanced Resume Parser
Comprehensive test suite for field expertise analysis and career trajectory detection
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.models.resume_parser import (
    AdvancedResumeParser, FieldType, ExperienceLevel, SkillCategory,
    ResumeAnalysis, FieldAnalysis, ExperienceAnalysis, SkillsAnalysis,
    CareerTrajectory
)

class TestAdvancedResumeParser:
    """Test suite for AdvancedResumeParser"""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return AdvancedResumeParser()
    
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
    def software_dev_resume(self):
        """Software developer resume for testing"""
        return """
        JANE SMITH
        Senior Software Engineer
        
        EXPERIENCE
        Senior Software Engineer | TechStartup | 2021-2023
        - Led development of React.js applications
        - Managed team of 4 developers using Agile methodology
        - Implemented CI/CD pipelines with Docker and AWS
        - Mentored junior developers and conducted code reviews
        
        Software Engineer | BigTech | 2019-2021
        - Developed Java applications and REST APIs
        - Worked with microservices architecture
        - Used Git for version control and collaboration
        
        SKILLS
        Programming: Java, JavaScript, Python, React, Node.js
        Tools: Git, Docker, AWS, Jenkins, JUnit
        Methodologies: Agile, Scrum, TDD, DevOps
        
        EDUCATION
        Computer Science Degree | Tech University | 2019
        """
    
    def test_parser_initialization(self, parser):
        """Test parser initialization"""
        assert parser is not None
        assert hasattr(parser, 'field_keywords')
        assert hasattr(parser, 'experience_indicators')
        assert hasattr(parser, 'leadership_indicators')
        assert hasattr(parser, 'skill_categories')
    
    def test_field_keywords_initialization(self, parser):
        """Test field keywords are properly initialized"""
        assert FieldType.DATA_ANALYSIS in parser.field_keywords
        assert FieldType.SOFTWARE_DEVELOPMENT in parser.field_keywords
        assert FieldType.PROJECT_MANAGEMENT in parser.field_keywords
        
        # Check that each field has keywords
        for field in FieldType:
            assert field in parser.field_keywords
            assert len(parser.field_keywords[field]) > 0
    
    def test_experience_indicators_initialization(self, parser):
        """Test experience indicators are properly initialized"""
        assert ExperienceLevel.ENTRY in parser.experience_indicators
        assert ExperienceLevel.MID in parser.experience_indicators
        assert ExperienceLevel.SENIOR in parser.experience_indicators
        
        # Check that each level has indicators
        for level in ExperienceLevel:
            assert level in parser.experience_indicators
            assert len(parser.experience_indicators[level]) > 0
    
    def test_text_preprocessing(self, parser):
        """Test text preprocessing functionality"""
        raw_text = "  Senior   Data   Analyst  \n\n  SQL, Python  "
        processed = parser._preprocess_text(raw_text)
        
        assert processed == "senior data analyst sql, python"
        assert "  " not in processed  # No double spaces
        assert "\n" not in processed  # No newlines
    
    def test_field_expertise_analysis_data_analyst(self, parser, sample_resume_text):
        """Test field expertise analysis for data analyst"""
        processed_text = parser._preprocess_text(sample_resume_text)
        analysis = parser._analyze_field_expertise(processed_text)
        
        assert analysis.primary_field == FieldType.DATA_ANALYSIS
        assert analysis.confidence_score > 0.5
        assert len(analysis.field_keywords) > 0
        assert "sql" in analysis.field_keywords or "python" in analysis.field_keywords
    
    def test_field_expertise_analysis_software_dev(self, parser, software_dev_resume):
        """Test field expertise analysis for software developer"""
        processed_text = parser._preprocess_text(software_dev_resume)
        analysis = parser._analyze_field_expertise(processed_text)
        
        assert analysis.primary_field == FieldType.SOFTWARE_DEVELOPMENT
        assert analysis.confidence_score > 0.5
        assert len(analysis.field_keywords) > 0
        assert any(keyword in analysis.field_keywords for keyword in ["java", "javascript", "react"])
    
    def test_experience_level_analysis_senior(self, parser, sample_resume_text):
        """Test experience level analysis for senior position"""
        processed_text = parser._preprocess_text(sample_resume_text)
        analysis = parser._analyze_experience_level(processed_text)
        
        assert analysis.level == ExperienceLevel.SENIOR
        assert analysis.confidence_score > 0.5
        assert analysis.total_years > 0
        assert len(analysis.leadership_indicators) > 0
    
    def test_experience_level_analysis_entry(self, parser):
        """Test experience level analysis for entry level"""
        entry_resume = """
        JUNIOR ANALYST
        Intern | Company | 2023
        - Assisted with data entry
        - Learned Excel and basic reporting
        """
        
        processed_text = parser._preprocess_text(entry_resume)
        analysis = parser._analyze_experience_level(processed_text)
        
        assert analysis.level == ExperienceLevel.ENTRY
        assert analysis.confidence_score > 0.5
    
    def test_skills_analysis(self, parser, sample_resume_text):
        """Test skills analysis functionality"""
        processed_text = parser._preprocess_text(sample_resume_text)
        analysis = parser._analyze_skills(processed_text)
        
        assert len(analysis.technical_skills) > 0
        assert len(analysis.business_skills) > 0
        assert len(analysis.soft_skills) > 0
        assert 0 <= analysis.technical_business_ratio <= 1
        assert len(analysis.proficiency_levels) > 0
    
    def test_career_trajectory_analysis(self, parser, sample_resume_text):
        """Test career trajectory analysis"""
        processed_text = parser._preprocess_text(sample_resume_text)
        analysis = parser._analyze_career_trajectory(processed_text)
        
        assert analysis.current_position is not None
        assert len(analysis.career_progression) >= 0
        assert len(analysis.next_logical_steps) > 0
        assert 0 <= analysis.growth_potential <= 1
        assert 0 <= analysis.advancement_readiness <= 1
        assert len(analysis.industry_focus) >= 0
    
    def test_leadership_potential_calculation(self, parser, sample_resume_text):
        """Test leadership potential calculation"""
        processed_text = parser._preprocess_text(sample_resume_text)
        potential = parser._calculate_leadership_potential(processed_text)
        
        assert 0 <= potential <= 1
        assert potential > 0  # Should detect some leadership indicators
    
    def test_transferable_skills_extraction(self, parser, sample_resume_text):
        """Test transferable skills extraction"""
        processed_text = parser._preprocess_text(sample_resume_text)
        field_analysis = parser._analyze_field_expertise(processed_text)
        transferable_skills = parser._extract_transferable_skills(processed_text, field_analysis)
        
        assert len(transferable_skills) > 0
        assert all(isinstance(skill, str) for skill in transferable_skills)
    
    def test_industry_experience_extraction(self, parser, sample_resume_text):
        """Test industry experience extraction"""
        processed_text = parser._preprocess_text(sample_resume_text)
        industry_experience = parser._extract_industry_experience(processed_text)
        
        assert isinstance(industry_experience, list)
        assert all(isinstance(industry, str) for industry in industry_experience)
    
    def test_complete_resume_analysis(self, parser, sample_resume_text):
        """Test complete resume analysis pipeline"""
        analysis = parser.parse_resume(sample_resume_text)
        
        assert isinstance(analysis, ResumeAnalysis)
        assert analysis.field_analysis is not None
        assert analysis.experience_analysis is not None
        assert analysis.skills_analysis is not None
        assert analysis.career_trajectory is not None
        assert 0 <= analysis.leadership_potential <= 1
        assert isinstance(analysis.transferable_skills, list)
        assert isinstance(analysis.industry_experience, list)
    
    def test_analysis_summary(self, parser, sample_resume_text):
        """Test analysis summary generation"""
        analysis = parser.parse_resume(sample_resume_text)
        summary = parser.get_analysis_summary(analysis)
        
        assert isinstance(summary, dict)
        assert 'primary_field' in summary
        assert 'experience_level' in summary
        assert 'leadership_potential' in summary
        assert 'growth_potential' in summary
        assert 'next_career_steps' in summary
    
    def test_error_handling(self, parser):
        """Test error handling with invalid input"""
        with pytest.raises(Exception):
            parser.parse_resume("")
        
        with pytest.raises(Exception):
            parser.parse_resume(None)
    
    def test_skill_categorization(self, parser):
        """Test skill categorization functionality"""
        # Test technical skills
        assert parser._categorize_skill("python") == SkillCategory.TECHNICAL
        assert parser._categorize_skill("sql") == SkillCategory.TECHNICAL
        assert parser._categorize_skill("react") == SkillCategory.TECHNICAL
        
        # Test business skills
        assert parser._categorize_skill("project management") == SkillCategory.BUSINESS
        assert parser._categorize_skill("business analysis") == SkillCategory.BUSINESS
        
        # Test soft skills
        assert parser._categorize_skill("communication") == SkillCategory.SOFT
        assert parser._categorize_skill("leadership") == SkillCategory.SOFT
    
    def test_experience_calculation(self, parser):
        """Test experience calculation"""
        text_with_years = "Worked from 2018 to 2023 at various companies"
        years = parser._calculate_total_experience(text_with_years)
        assert years == 5.0
    
    def test_progression_analysis(self, parser):
        """Test career progression analysis"""
        progression_text = "Promoted from Junior to Senior Analyst"
        progression = parser._analyze_career_progression(progression_text)
        assert "progression" in progression.lower()
    
    def test_next_steps_prediction(self, parser):
        """Test next career steps prediction"""
        job_history = ["Senior Data Analyst", "Data Analyst"]
        next_steps = parser._predict_next_career_steps(job_history, "")
        assert len(next_steps) > 0
        assert all(isinstance(step, str) for step in next_steps)
    
    def test_growth_potential_calculation(self, parser):
        """Test growth potential calculation"""
        job_history = ["Junior Analyst"]
        potential = parser._calculate_growth_potential(job_history, "")
        assert 0 <= potential <= 1
        assert potential > 0.5  # Junior positions should have high growth potential
    
    def test_advancement_readiness(self, parser):
        """Test advancement readiness calculation"""
        readiness = parser._calculate_advancement_readiness("", [])
        assert 0 <= readiness <= 1
    
    def test_industry_focus_extraction(self, parser):
        """Test industry focus extraction"""
        tech_text = "Worked in technology sector with software development"
        industries = parser._extract_industry_focus(tech_text, [])
        assert "technology" in industries
    
    def test_field_experience_estimation(self, parser):
        """Test field experience estimation"""
        data_text = "SQL Python R Tableau Analytics"
        years = parser._estimate_field_experience(data_text, FieldType.DATA_ANALYSIS)
        assert years > 0
    
    def test_leadership_indicators_extraction(self, parser):
        """Test leadership indicators extraction"""
        leadership_text = "Led team of 5 developers and managed projects"
        indicators = parser._extract_leadership_indicators(leadership_text)
        assert len(indicators) > 0
        assert "led" in indicators or "managed" in indicators
    
    def test_skills_extraction(self, parser):
        """Test skills extraction from text"""
        skills_text = "Python SQL React JavaScript"
        skills = parser._extract_skills_from_text(skills_text)
        assert len(skills) > 0
        assert "python" in skills or "sql" in skills
    
    def test_skill_proficiency_calculation(self, parser):
        """Test skill proficiency calculation"""
        proficiency = parser._calculate_skill_proficiency("python", 3, "expert python developer")
        assert 0 <= proficiency <= 1
    
    def test_job_history_extraction(self, parser):
        """Test job history extraction"""
        job_text = "Senior Data Analyst at TechCorp, Data Analyst at DataCorp"
        history = parser._extract_job_history(job_text)
        assert len(history) > 0
        assert all("analyst" in job.lower() for job in history)
    
    def test_progression_pattern_analysis(self, parser):
        """Test progression pattern analysis"""
        history = ["Senior Analyst", "Data Analyst"]
        progression = parser._analyze_progression_pattern(history)
        assert len(progression) > 0
        assert all(isinstance(pattern, str) for pattern in progression)

if __name__ == "__main__":
    pytest.main([__file__]) 