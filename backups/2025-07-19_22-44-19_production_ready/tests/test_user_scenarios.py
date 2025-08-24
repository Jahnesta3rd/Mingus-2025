"""
User Acceptance Tests for Job Recommendation Engine
Tests realistic scenarios for target demographic (African American professionals 25-35)
"""

import unittest
import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend.ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from backend.ml.models.resume_parser import AdvancedResumeParser
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService


class TestUserScenarios(unittest.TestCase):
    """User acceptance tests for realistic demographic scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = MingusJobRecommendationEngine()
        self.resume_parser = AdvancedResumeParser()
        
        # Target demographic characteristics
        self.target_demographic = {
            'age_range': (25, 35),
            'locations': ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City'],
            'hbcus': [
                'Morehouse College', 'Spelman College', 'Howard University', 
                'Texas Southern University', 'Florida A&M University',
                'North Carolina A&T State University', 'Hampton University'
            ],
            'fields': ['Data Analysis', 'Software Development', 'Project Management', 'Marketing', 'Finance'],
            'experience_levels': ['Entry', 'Mid', 'Senior'],
            'salary_ranges': [(45000, 120000)]
        }

    def test_entry_level_professional_scenario(self):
        """Test scenario for entry-level professional (25-27 years old)"""
        resume = """
        JUNIOR DATA ANALYST
        StartupCorp | Atlanta, GA | 2022-2023
        - Assisted with data analysis using Excel and basic SQL queries
        - Created monthly reports and dashboards for team leads
        - Supported marketing campaigns with data insights and performance tracking
        - Collaborated with cross-functional teams on data collection and analysis
        
        DATA ANALYST INTERN
        TechCorp | Atlanta, GA | 2021-2022
        - Performed data entry and validation for customer databases
        - Created basic visualizations using Tableau and Power BI
        - Assisted senior analysts with report generation and data cleaning
        - Learned Python and SQL for data manipulation and analysis
        
        EDUCATION
        Morehouse College
        Bachelor of Science in Mathematics
        GPA: 3.6/4.0
        Graduated: May 2022
        
        RELEVANT COURSEWORK
        Statistics, Calculus, Linear Algebra, Data Structures, Programming Fundamentals
        
        SKILLS
        Technical: Excel, SQL (basic), Python (basic), Tableau, Power BI, Google Analytics
        Business: Data Analysis, Reporting, Communication, Problem Solving
        Soft Skills: Teamwork, Time Management, Attention to Detail, Learning Agility
        """
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=resume,
            user_id=1,
            current_salary=55000,
            target_locations=['Atlanta', 'Houston'],
            risk_preference='conservative'
        )
        
        # Verify user acceptance criteria
        self.assertTrue(result.success)
        
        # Check field detection
        self.assertEqual(result.user_profile.field_expertise['primary_field'], 'Data Analysis')
        self.assertEqual(result.user_profile.experience_level, 'Entry')
        
        # Check education recognition
        self.assertIn('Morehouse College', str(result.user_profile))
        
        # Verify recommendations are appropriate for entry level
        career_strategy = result.career_strategy
        
        # Conservative opportunity should be realistic for entry level
        conservative = career_strategy.conservative_opportunity
        conservative_increase = conservative.income_impact.salary_increase_percentage
        self.assertLessEqual(conservative_increase, 0.25)  # Max 25% for entry level
        self.assertGreaterEqual(conservative_increase, 0.15)  # Min 15% increase
        
        # Skills should match entry level expectations
        skill_gaps = conservative.skill_gap_analysis.missing_critical_skills
        self.assertLess(len(skill_gaps), 5)  # Shouldn't have too many missing skills
        
        # Timeline should be reasonable for entry level
        timeline = conservative.application_strategy.timeline_to_application
        self.assertIn(timeline, ['1-2 weeks', '2-4 weeks', '4-6 weeks'])

    def test_mid_level_professional_scenario(self):
        """Test scenario for mid-level professional (28-32 years old)"""
        resume = """
        SENIOR MARKETING SPECIALIST
        BrandCorp | Houston, TX | 2020-2023
        - Led digital marketing campaigns with $200K annual budget
        - Managed team of 2 marketing specialists and achieved 20% YoY growth
        - Developed customer acquisition strategies that increased conversion by 15%
        - Collaborated with product teams on market research and customer insights
        - Mentored junior marketers and developed team capabilities
        
        MARKETING COORDINATOR
        GrowthCorp | Houston, TX | 2018-2020
        - Executed social media campaigns and email marketing initiatives
        - Analyzed campaign performance using Google Analytics and social media tools
        - Supported brand development and customer acquisition initiatives
        - Managed relationships with external vendors and agencies
        
        EDUCATION
        Texas Southern University
        Bachelor of Business Administration in Marketing
        GPA: 3.5/4.0
        Graduated: May 2018
        
        CERTIFICATIONS
        Google Analytics Individual Qualification (GAIQ)
        Facebook Blueprint Certification
        HubSpot Inbound Marketing Certification
        
        SKILLS
        Technical: Google Analytics, Facebook Ads, Instagram Marketing, Email Marketing, CRM Systems
        Business: Campaign Management, Budget Management, Team Leadership, Strategic Planning
        Soft Skills: Leadership, Communication, Strategic Thinking, Team Collaboration, Mentoring
        """
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=resume,
            user_id=2,
            current_salary=75000,
            target_locations=['Houston', 'Atlanta', 'Dallas'],
            risk_preference='balanced'
        )
        
        # Verify user acceptance criteria
        self.assertTrue(result.success)
        
        # Check field detection
        self.assertEqual(result.user_profile.field_expertise['primary_field'], 'Marketing')
        self.assertEqual(result.user_profile.experience_level, 'Mid')
        
        # Check education recognition
        self.assertIn('Texas Southern University', str(result.user_profile))
        
        # Verify recommendations are appropriate for mid level
        career_strategy = result.career_strategy
        
        # Optimal opportunity should be realistic for mid level
        optimal = career_strategy.optimal_opportunity
        optimal_increase = optimal.income_impact.salary_increase_percentage
        self.assertGreaterEqual(optimal_increase, 0.20)  # Min 20% for mid level
        self.assertLessEqual(optimal_increase, 0.35)     # Max 35% for mid level
        
        # Should have leadership opportunities
        self.assertIn('leadership', str(optimal.application_strategy.recommended_approach).lower())
        
        # Timeline should allow for skill development
        timeline = optimal.application_strategy.timeline_to_application
        self.assertIn(timeline, ['4-8 weeks', '6-10 weeks', '8-12 weeks'])

    def test_senior_level_professional_scenario(self):
        """Test scenario for senior-level professional (30-35 years old)"""
        resume = """
        SENIOR DATA ANALYST
        TechCorp Inc. | Atlanta, GA | 2020-2023
        - Led data analysis initiatives using Python, SQL, and Tableau
        - Managed team of 3 analysts and delivered insights to executive leadership
        - Increased revenue by 15% through predictive analytics implementation
        - Collaborated with cross-functional teams on data-driven decision making
        - Mentored junior analysts and developed team capabilities
        
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
        Graduated: May 2018
        
        CERTIFICATIONS
        AWS Certified Data Analytics - Specialty
        Tableau Desktop Certified Associate
        Microsoft Certified: Data Analyst Associate
        
        SKILLS
        Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning, AWS, Git
        Business: Project Management, Stakeholder Communication, Strategic Analysis, Team Leadership
        Soft Skills: Leadership, Team Management, Problem Solving, Communication, Mentoring
        """
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=resume,
            user_id=3,
            current_salary=95000,
            target_locations=['Atlanta', 'Washington DC', 'New York City'],
            risk_preference='aggressive'
        )
        
        # Verify user acceptance criteria
        self.assertTrue(result.success)
        
        # Check field detection
        self.assertEqual(result.user_profile.field_expertise['primary_field'], 'Data Analysis')
        self.assertEqual(result.user_profile.experience_level, 'Senior')
        
        # Check education recognition
        self.assertIn('Georgia Institute of Technology', str(result.user_profile))
        
        # Verify recommendations are appropriate for senior level
        career_strategy = result.career_strategy
        
        # Stretch opportunity should be available for senior level
        stretch = career_strategy.stretch_opportunity
        stretch_increase = stretch.income_impact.salary_increase_percentage
        self.assertGreaterEqual(stretch_increase, 0.30)  # Min 30% for senior level
        
        # Should include management/leadership opportunities
        self.assertIn('manager', str(stretch.job.title).lower()) or \
        self.assertIn('director', str(stretch.job.title).lower()) or \
        self.assertIn('lead', str(stretch.job.title).lower())
        
        # Timeline should allow for strategic preparation
        timeline = stretch.application_strategy.timeline_to_application
        self.assertIn(timeline, ['8-12 weeks', '12-16 weeks', '16-20 weeks'])

    def test_career_transition_scenario(self):
        """Test scenario for professional seeking career transition"""
        resume = """
        PROJECT MANAGER
        ConstructionCorp | Atlanta, GA | 2021-2023
        - Managed construction projects with budgets up to $2M
        - Led cross-functional teams of 10+ professionals
        - Implemented project management methodologies and improved efficiency by 20%
        - Developed stakeholder communication strategies and reporting systems
        - Managed vendor relationships and contract negotiations
        
        PROJECT COORDINATOR
        BuildCorp | Atlanta, GA | 2019-2021
        - Coordinated project schedules and resource allocation
        - Created project documentation and progress reports
        - Assisted with budget tracking and cost analysis
        - Supported project managers with administrative tasks
        
        EDUCATION
        Howard University
        Bachelor of Science in Civil Engineering
        GPA: 3.4/4.0
        Graduated: May 2019
        
        CERTIFICATIONS
        Project Management Professional (PMP)
        Certified ScrumMaster (CSM)
        Six Sigma Green Belt
        
        SKILLS
        Technical: Microsoft Project, Excel, AutoCAD, Primavera, JIRA, Confluence
        Business: Project Management, Budget Management, Risk Management, Stakeholder Management
        Soft Skills: Leadership, Communication, Problem Solving, Team Management, Negotiation
        """
        
        result = self.engine.process_resume_and_recommend_jobs(
            resume_text=resume,
            user_id=4,
            current_salary=80000,
            target_locations=['Atlanta', 'Washington DC'],
            risk_preference='balanced'
        )
        
        # Verify user acceptance criteria
        self.assertTrue(result.success)
        
        # Check field detection (should recognize transferable skills)
        self.assertEqual(result.user_profile.field_expertise['primary_field'], 'Project Management')
        self.assertEqual(result.user_profile.experience_level, 'Mid')
        
        # Check education recognition
        self.assertIn('Howard University', str(result.user_profile))
        
        # Verify transferable skills are identified
        transferable_skills = result.user_profile.transferable_skills
        self.assertGreater(len(transferable_skills), 0)
        
        # Should include project management and leadership skills
        skill_names = [skill.lower() for skill in transferable_skills]
        self.assertTrue(any('project' in skill for skill in skill_names))
        self.assertTrue(any('leadership' in skill for skill in skill_names))

    def test_location_preference_scenarios(self):
        """Test scenarios with different location preferences"""
        base_resume = """
        DATA ANALYST
        TechCorp | Atlanta, GA | 2020-2023
        - Performed data analysis using Python, SQL, and Tableau
        - Created reports and dashboards for business stakeholders
        - Collaborated with cross-functional teams on data projects
        
        EDUCATION
        Spelman College
        Bachelor of Science in Mathematics
        GPA: 3.6/4.0
        
        SKILLS
        Technical: Python, SQL, Tableau, Excel, R
        Business: Data Analysis, Reporting, Communication
        """
        
        location_scenarios = [
            {
                'name': 'Atlanta Focus',
                'locations': ['Atlanta'],
                'expected_primary': 'Atlanta'
            },
            {
                'name': 'Multiple Cities',
                'locations': ['Atlanta', 'Houston', 'Washington DC'],
                'expected_primary': 'Atlanta'  # Should prioritize first location
            },
            {
                'name': 'No Preference',
                'locations': [],
                'expected_primary': 'Atlanta'  # Should use defaults
            }
        ]
        
        for scenario in location_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=base_resume,
                user_id=5 + location_scenarios.index(scenario),
                current_salary=65000,
                target_locations=scenario['locations'],
                risk_preference='balanced'
            )
            
            self.assertTrue(result.success)
            
            # Verify location preferences are respected
            career_strategy = result.career_strategy
            
            # Check that recommendations include preferred locations
            for tier in ['conservative', 'optimal', 'stretch']:
                opportunity = getattr(career_strategy, f'{tier}_opportunity', None)
                if opportunity and hasattr(opportunity, 'job'):
                    job_location = opportunity.job.location
                    if scenario['locations']:
                        self.assertIn(job_location, scenario['locations'])
                    else:
                        # Should use default locations
                        self.assertIn(job_location, self.target_demographic['locations'])

    def test_risk_preference_scenarios(self):
        """Test scenarios with different risk preferences"""
        base_resume = """
        MARKETING SPECIALIST
        BrandCorp | Houston, TX | 2020-2023
        - Led digital marketing campaigns with $150K budget
        - Managed social media presence and email marketing
        - Analyzed campaign performance and optimized ROI
        
        EDUCATION
        Texas Southern University
        Bachelor of Business Administration in Marketing
        GPA: 3.5/4.0
        
        SKILLS
        Technical: Google Analytics, Facebook Ads, Email Marketing, CRM
        Business: Campaign Management, Budget Management, Analytics
        """
        
        risk_scenarios = [
            {
                'name': 'Conservative',
                'risk_preference': 'conservative',
                'expected_max_increase': 0.25
            },
            {
                'name': 'Balanced',
                'risk_preference': 'balanced',
                'expected_max_increase': 0.35
            },
            {
                'name': 'Aggressive',
                'risk_preference': 'aggressive',
                'expected_max_increase': 0.50
            }
        ]
        
        for scenario in risk_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=base_resume,
                user_id=8 + risk_scenarios.index(scenario),
                current_salary=70000,
                target_locations=['Houston', 'Atlanta'],
                risk_preference=scenario['risk_preference']
            )
            
            self.assertTrue(result.success)
            
            # Verify risk preferences are reflected in recommendations
            career_strategy = result.career_strategy
            
            # Check stretch opportunity salary increase
            stretch = career_strategy.stretch_opportunity
            stretch_increase = stretch.income_impact.salary_increase_percentage
            self.assertLessEqual(stretch_increase, scenario['expected_max_increase'])
            
            # Conservative should have lower risk factors
            conservative = career_strategy.conservative_opportunity
            conservative_risks = len(conservative.application_strategy.risk_factors)
            
            if scenario['risk_preference'] == 'conservative':
                self.assertLess(conservative_risks, 3)  # Fewer risk factors
            elif scenario['risk_preference'] == 'aggressive':
                self.assertGreater(conservative_risks, 1)  # More risk factors

    def test_salary_progression_scenarios(self):
        """Test scenarios with different salary levels and progression expectations"""
        base_resume = """
        SOFTWARE DEVELOPER
        TechCorp | Atlanta, GA | 2020-2023
        - Developed web applications using JavaScript, React, and Node.js
        - Collaborated with product teams on feature development
        - Participated in code reviews and agile development processes
        
        EDUCATION
        Morehouse College
        Bachelor of Science in Computer Science
        GPA: 3.7/4.0
        
        SKILLS
        Technical: JavaScript, React, Node.js, Python, Git, AWS
        Business: Agile Development, Team Collaboration, Problem Solving
        """
        
        salary_scenarios = [
            {
                'name': 'Entry Level',
                'salary': 55000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.30
            },
            {
                'name': 'Mid Level',
                'salary': 75000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.40
            },
            {
                'name': 'Senior Level',
                'salary': 95000,
                'expected_min_increase': 0.15,
                'expected_max_increase': 0.45
            }
        ]
        
        for scenario in salary_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=base_resume,
                user_id=11 + salary_scenarios.index(scenario),
                current_salary=scenario['salary'],
                target_locations=['Atlanta'],
                risk_preference='balanced'
            )
            
            self.assertTrue(result.success)
            
            # Verify salary progression is appropriate
            career_strategy = result.career_strategy
            
            # Check all opportunities meet minimum increase
            for tier in ['conservative', 'optimal', 'stretch']:
                opportunity = getattr(career_strategy, f'{tier}_opportunity', None)
                if opportunity:
                    increase = opportunity.income_impact.salary_increase_percentage
                    self.assertGreaterEqual(increase, scenario['expected_min_increase'])
                    self.assertLessEqual(increase, scenario['expected_max_increase'])

    def test_education_recognition_scenarios(self):
        """Test scenarios with different educational backgrounds"""
        education_scenarios = [
            {
                'name': 'HBCU Graduate',
                'resume': """
                DATA ANALYST
                TechCorp | Atlanta, GA | 2020-2023
                - Performed data analysis using Python and SQL
                - Created reports and dashboards for stakeholders
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Python, SQL, Excel, Tableau
                Business: Data Analysis, Reporting
                """,
                'expected_institution': 'Spelman College'
            },
            {
                'name': 'Non-HBCU Graduate',
                'resume': """
                MARKETING SPECIALIST
                BrandCorp | Houston, TX | 2020-2023
                - Led marketing campaigns and analyzed performance
                - Managed social media presence and customer engagement
                
                EDUCATION
                University of Houston
                Bachelor of Business Administration in Marketing
                GPA: 3.5/4.0
                
                SKILLS
                Technical: Google Analytics, Facebook Ads, Email Marketing
                Business: Campaign Management, Analytics
                """,
                'expected_institution': 'University of Houston'
            }
        ]
        
        for scenario in education_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=scenario['resume'],
                user_id=14 + education_scenarios.index(scenario),
                current_salary=65000,
                target_locations=['Atlanta'],
                risk_preference='balanced'
            )
            
            self.assertTrue(result.success)
            
            # Verify education is recognized
            profile_str = str(result.user_profile)
            self.assertIn(scenario['expected_institution'], profile_str)
            
            # Verify recommendations are appropriate regardless of institution
            career_strategy = result.career_strategy
            self.assertIsNotNone(career_strategy.conservative_opportunity)
            self.assertIsNotNone(career_strategy.optimal_opportunity)
            self.assertIsNotNone(career_strategy.stretch_opportunity)

    def test_skill_gap_scenarios(self):
        """Test scenarios with different skill gaps and development needs"""
        skill_scenarios = [
            {
                'name': 'Strong Technical Skills',
                'resume': """
                SENIOR DEVELOPER
                TechCorp | Atlanta, GA | 2020-2023
                - Developed full-stack applications using modern technologies
                - Led technical architecture decisions and code reviews
                - Mentored junior developers and conducted technical interviews
                
                EDUCATION
                Morehouse College
                Bachelor of Science in Computer Science
                GPA: 3.8/4.0
                
                SKILLS
                Technical: JavaScript, React, Node.js, Python, Java, AWS, Docker, Kubernetes
                Business: Technical Leadership, Architecture Design, Team Mentoring
                """,
                'expected_gaps': 0  # Should have few skill gaps
            },
            {
                'name': 'Developing Technical Skills',
                'resume': """
                JUNIOR ANALYST
                DataCorp | Houston, TX | 2022-2023
                - Assisted with data analysis using Excel and basic SQL
                - Created reports and dashboards for team leads
                - Learned Python and data visualization tools
                
                EDUCATION
                Texas Southern University
                Bachelor of Science in Mathematics
                GPA: 3.4/4.0
                
                SKILLS
                Technical: Excel, SQL (basic), Python (basic), Tableau
                Business: Data Analysis, Reporting, Communication
                """,
                'expected_gaps': 3  # Should have some skill gaps
            }
        ]
        
        for scenario in skill_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=scenario['resume'],
                user_id=16 + skill_scenarios.index(scenario),
                current_salary=70000,
                target_locations=['Atlanta'],
                risk_preference='balanced'
            )
            
            self.assertTrue(result.success)
            
            # Verify skill gap analysis
            career_strategy = result.career_strategy
            conservative = career_strategy.conservative_opportunity
            
            missing_skills = len(conservative.skill_gap_analysis.missing_critical_skills)
            
            if scenario['name'] == 'Strong Technical Skills':
                self.assertLessEqual(missing_skills, 2)  # Few gaps
            else:
                self.assertGreaterEqual(missing_skills, 1)  # Some gaps

    def test_comprehensive_user_journey(self):
        """Test comprehensive user journey with realistic progression"""
        # Simulate a user's career progression over time
        journey_scenarios = [
            {
                'stage': 'Entry Level (Year 1)',
                'resume': """
                JUNIOR DATA ANALYST
                StartupCorp | Atlanta, GA | 2022-2023
                - Assisted with data analysis using Excel and basic SQL
                - Created monthly reports and dashboards
                - Supported marketing campaigns with data insights
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Excel, SQL (basic), Python (basic), Tableau
                Business: Data Analysis, Reporting, Communication
                """,
                'salary': 55000,
                'expected_level': 'Entry',
                'expected_increase': (0.15, 0.25)
            },
            {
                'stage': 'Mid Level (Year 3)',
                'resume': """
                DATA ANALYST
                TechCorp | Atlanta, GA | 2020-2023
                - Performed statistical analysis and created automated reporting
                - Developed SQL queries and maintained data warehouse
                - Created interactive dashboards using Power BI and Tableau
                - Supported cross-functional teams with data insights
                
                JUNIOR DATA ANALYST
                StartupCorp | Atlanta, GA | 2019-2020
                - Assisted with data analysis using Excel and basic SQL
                - Created monthly reports and dashboards
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning
                Business: Data Analysis, Reporting, Project Management
                """,
                'salary': 75000,
                'expected_level': 'Mid',
                'expected_increase': (0.20, 0.35)
            },
            {
                'stage': 'Senior Level (Year 5)',
                'resume': """
                SENIOR DATA ANALYST
                TechCorp Inc. | Atlanta, GA | 2020-2023
                - Led data analysis initiatives using Python, SQL, and Tableau
                - Managed team of 3 analysts and delivered insights to executives
                - Increased revenue by 15% through predictive analytics
                - Mentored junior analysts and developed team capabilities
                
                DATA ANALYST
                TechCorp | Atlanta, GA | 2018-2020
                - Performed statistical analysis and created automated reporting
                - Developed SQL queries and maintained data warehouse
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning, AWS
                Business: Project Management, Team Leadership, Strategic Analysis
                """,
                'salary': 95000,
                'expected_level': 'Senior',
                'expected_increase': (0.25, 0.45)
            }
        ]
        
        for scenario in journey_scenarios:
            result = self.engine.process_resume_and_recommend_jobs(
                resume_text=scenario['resume'],
                user_id=18 + journey_scenarios.index(scenario),
                current_salary=scenario['salary'],
                target_locations=['Atlanta'],
                risk_preference='balanced'
            )
            
            self.assertTrue(result.success)
            
            # Verify career progression
            self.assertEqual(result.user_profile.experience_level, scenario['expected_level'])
            
            # Verify salary progression expectations
            career_strategy = result.career_strategy
            optimal = career_strategy.optimal_opportunity
            optimal_increase = optimal.income_impact.salary_increase_percentage
            
            min_expected, max_expected = scenario['expected_increase']
            self.assertGreaterEqual(optimal_increase, min_expected)
            self.assertLessEqual(optimal_increase, max_expected)


if __name__ == '__main__':
    unittest.main() 