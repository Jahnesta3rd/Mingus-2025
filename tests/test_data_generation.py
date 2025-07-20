"""
Mock Data Generation for Job Recommendation Engine Testing
Generates realistic test data for resumes, demographics, job market data, and test scenarios
"""

import unittest
import pytest
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import faker

from backend.ml.models.resume_parser import FieldType, ExperienceLevel
from backend.ml.models.intelligent_job_matcher import CompanyTier


@dataclass
class MockResumeData:
    """Mock resume data structure"""
    text: str
    field: FieldType
    experience_level: ExperienceLevel
    current_salary: int
    skills: List[str]
    education: str
    locations: List[str]


@dataclass
class MockJobData:
    """Mock job posting data structure"""
    title: str
    company: str
    location: str
    salary_range: Dict[str, int]
    skills: List[str]
    experience_level: str
    company_tier: CompanyTier
    remote_work: bool


class MockDataGenerator:
    """Generates realistic mock data for testing"""
    
    def __init__(self):
        """Initialize the mock data generator"""
        self.fake = faker.Faker()
        
        # Target demographic data
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
        
        # Field-specific data
        self.field_data = {
            FieldType.DATA_ANALYSIS: {
                'titles': ['Data Analyst', 'Business Analyst', 'Data Scientist', 'Analytics Specialist'],
                'skills': ['Python', 'SQL', 'Excel', 'Tableau', 'Power BI', 'R', 'Statistics'],
                'salary_ranges': {
                    'Entry': (50000, 65000),
                    'Mid': (65000, 85000),
                    'Senior': (85000, 120000)
                }
            },
            FieldType.SOFTWARE_DEVELOPMENT: {
                'titles': ['Software Engineer', 'Developer', 'Full Stack Developer', 'Backend Engineer'],
                'skills': ['JavaScript', 'Python', 'Java', 'React', 'Node.js', 'Git', 'AWS'],
                'salary_ranges': {
                    'Entry': (55000, 70000),
                    'Mid': (70000, 95000),
                    'Senior': (95000, 130000)
                }
            },
            FieldType.PROJECT_MANAGEMENT: {
                'titles': ['Project Manager', 'Program Manager', 'Product Manager', 'Scrum Master'],
                'skills': ['Agile', 'Scrum', 'JIRA', 'Project Planning', 'Stakeholder Management'],
                'salary_ranges': {
                    'Entry': (50000, 65000),
                    'Mid': (65000, 85000),
                    'Senior': (85000, 120000)
                }
            },
            FieldType.MARKETING: {
                'titles': ['Marketing Specialist', 'Digital Marketing Manager', 'Marketing Analyst'],
                'skills': ['Google Analytics', 'Facebook Ads', 'Email Marketing', 'SEO', 'CRM'],
                'salary_ranges': {
                    'Entry': (45000, 60000),
                    'Mid': (60000, 80000),
                    'Senior': (80000, 110000)
                }
            },
            FieldType.FINANCE: {
                'titles': ['Financial Analyst', 'Accountant', 'Finance Manager', 'Investment Analyst'],
                'skills': ['Excel', 'Financial Modeling', 'Accounting', 'Budgeting', 'Forecasting'],
                'salary_ranges': {
                    'Entry': (50000, 65000),
                    'Mid': (65000, 85000),
                    'Senior': (85000, 120000)
                }
            }
        }
        
        # Company data
        self.company_data = {
            CompanyTier.FORTUNE_500: [
                'Microsoft', 'Google', 'Amazon', 'Apple', 'Meta', 'Netflix',
                'Coca-Cola', 'Home Depot', 'UPS', 'Delta Airlines'
            ],
            CompanyTier.GROWTH_COMPANY: [
                'Salesforce', 'Adobe', 'Zoom', 'Slack', 'Airbnb', 'Uber',
                'Lyft', 'DoorDash', 'Instacart', 'Robinhood'
            ],
            CompanyTier.STARTUP: [
                'TechStartup', 'InnovateCorp', 'FutureTech', 'NextGen', 'DisruptInc',
                'ScaleUp', 'GrowthTech', 'VentureCorp', 'InnovationLabs', 'StartupXYZ'
            ],
            CompanyTier.ESTABLISHED: [
                'EstablishedCorp', 'LegacyTech', 'TraditionalInc', 'HeritageCorp',
                'ClassicTech', 'TimeTested', 'ProvenCorp', 'ReliableTech'
            ]
        }

    def generate_resume(self, field: FieldType = None, experience_level: ExperienceLevel = None, 
                       current_salary: int = None, education: str = None) -> MockResumeData:
        """Generate a realistic resume for testing"""
        
        # Randomly select field if not specified
        if field is None:
            field = random.choice(list(FieldType))
        
        # Randomly select experience level if not specified
        if experience_level is None:
            experience_level = random.choice(list(ExperienceLevel))
        
        # Generate salary if not specified
        if current_salary is None:
            salary_range = self.field_data[field]['salary_ranges'][experience_level.value]
            current_salary = random.randint(salary_range[0], salary_range[1])
        
        # Generate education if not specified
        if education is None:
            education = random.choice(self.target_demographic['hbcus'])
        
        # Generate resume text
        resume_text = self._generate_resume_text(field, experience_level, education)
        
        # Generate skills
        skills = self._generate_skills(field, experience_level)
        
        # Generate locations
        locations = random.sample(self.target_demographic['locations'], 
                                random.randint(1, 3))
        
        return MockResumeData(
            text=resume_text,
            field=field,
            experience_level=experience_level,
            current_salary=current_salary,
            skills=skills,
            education=education,
            locations=locations
        )

    def _generate_resume_text(self, field: FieldType, experience_level: ExperienceLevel, 
                            education: str) -> str:
        """Generate realistic resume text"""
        
        field_data = self.field_data[field]
        title = random.choice(field_data['titles'])
        
        # Generate experience section based on level
        if experience_level == ExperienceLevel.ENTRY:
            experience_section = self._generate_entry_level_experience(field, title)
        elif experience_level == ExperienceLevel.MID:
            experience_section = self._generate_mid_level_experience(field, title)
        else:  # Senior
            experience_section = self._generate_senior_level_experience(field, title)
        
        # Generate education section
        education_section = f"""
        EDUCATION
        {education}
        Bachelor of Science in {self._get_degree_for_field(field)}
        GPA: {random.uniform(3.0, 4.0):.1f}/4.0
        Graduated: {random.randint(2018, 2023)}
        """
        
        # Generate skills section
        skills = self._generate_skills(field, experience_level)
        skills_section = f"""
        SKILLS
        Technical: {', '.join(skills[:5])}
        Business: {', '.join(skills[5:8]) if len(skills) > 5 else ''}
        Soft Skills: Communication, Teamwork, Problem Solving, Time Management
        """
        
        return f"{title}\n{experience_section}\n{education_section}\n{skills_section}"

    def _generate_entry_level_experience(self, field: FieldType, title: str) -> str:
        """Generate entry-level experience section"""
        company = random.choice(self.company_data[CompanyTier.STARTUP])
        location = random.choice(self.target_demographic['locations'])
        
        return f"""
        {title}
        {company} | {location} | {random.randint(2022, 2023)}-Present
        - Assisted with {self._get_field_activity(field)} using {random.choice(self.field_data[field]['skills'])}
        - Created reports and dashboards for team leads
        - Supported cross-functional teams with data and insights
        - Learned new technologies and methodologies
        
        INTERNSHIP
        {random.choice(self.company_data[CompanyTier.STARTUP])} | {location} | {random.randint(2021, 2022)}
        - Performed entry-level {self._get_field_activity(field)} tasks
        - Assisted senior team members with projects
        - Gained hands-on experience with industry tools
        """

    def _generate_mid_level_experience(self, field: FieldType, title: str) -> str:
        """Generate mid-level experience section"""
        current_company = random.choice(self.company_data[CompanyTier.GROWTH_COMPANY])
        previous_company = random.choice(self.company_data[CompanyTier.STARTUP])
        location = random.choice(self.target_demographic['locations'])
        
        return f"""
        {title}
        {current_company} | {location} | {random.randint(2020, 2023)}-Present
        - Led {self._get_field_activity(field)} initiatives with measurable impact
        - Managed projects and collaborated with cross-functional teams
        - Developed and implemented {self._get_field_activity(field)} strategies
        - Mentored junior team members and conducted training sessions
        
        {self._get_junior_title(field)}
        {previous_company} | {location} | {random.randint(2018, 2020)}
        - Performed {self._get_field_activity(field)} and created automated solutions
        - Supported team leads with analysis and reporting
        - Developed skills in {', '.join(random.sample(self.field_data[field]['skills'], 3))}
        """

    def _generate_senior_level_experience(self, field: FieldType, title: str) -> str:
        """Generate senior-level experience section"""
        current_company = random.choice(self.company_data[CompanyTier.FORTUNE_500])
        previous_company = random.choice(self.company_data[CompanyTier.GROWTH_COMPANY])
        location = random.choice(self.target_demographic['locations'])
        
        return f"""
        SENIOR {title.upper()}
        {current_company} | {location} | {random.randint(2020, 2023)}-Present
        - Led strategic {self._get_field_activity(field)} initiatives with $1M+ impact
        - Managed team of {random.randint(3, 8)} professionals and delivered executive insights
        - Established best practices and standards for {self._get_field_activity(field)}
        - Collaborated with C-suite on strategic decision-making
        - Mentored {random.randint(5, 15)} team members and conducted leadership training
        
        {title}
        {previous_company} | {location} | {random.randint(2018, 2020)}
        - Led {self._get_field_activity(field)} projects and achieved {random.randint(15, 30)}% improvement
        - Managed cross-functional teams and stakeholder relationships
        - Developed innovative solutions using {', '.join(random.sample(self.field_data[field]['skills'], 4))}
        """

    def _generate_skills(self, field: FieldType, experience_level: ExperienceLevel) -> List[str]:
        """Generate skills based on field and experience level"""
        field_skills = self.field_data[field]['skills'].copy()
        
        # Add more skills for higher experience levels
        if experience_level == ExperienceLevel.SENIOR:
            num_skills = random.randint(8, 12)
        elif experience_level == ExperienceLevel.MID:
            num_skills = random.randint(6, 9)
        else:  # Entry
            num_skills = random.randint(4, 6)
        
        # Add some additional skills based on field
        additional_skills = {
            FieldType.DATA_ANALYSIS: ['Machine Learning', 'Data Visualization', 'ETL', 'Data Warehousing'],
            FieldType.SOFTWARE_DEVELOPMENT: ['Docker', 'Kubernetes', 'CI/CD', 'Microservices'],
            FieldType.PROJECT_MANAGEMENT: ['PMP', 'Six Sigma', 'Risk Management', 'Budget Management'],
            FieldType.MARKETING: ['Content Marketing', 'Social Media', 'Brand Management', 'Market Research'],
            FieldType.FINANCE: ['Financial Planning', 'Investment Analysis', 'Audit', 'Compliance']
        }
        
        field_skills.extend(additional_skills.get(field, []))
        
        return random.sample(field_skills, min(num_skills, len(field_skills)))

    def _get_field_activity(self, field: FieldType) -> str:
        """Get field-specific activity description"""
        activities = {
            FieldType.DATA_ANALYSIS: 'data analysis',
            FieldType.SOFTWARE_DEVELOPMENT: 'software development',
            FieldType.PROJECT_MANAGEMENT: 'project management',
            FieldType.MARKETING: 'marketing campaigns',
            FieldType.FINANCE: 'financial analysis'
        }
        return activities.get(field, 'analysis')

    def _get_junior_title(self, field: FieldType) -> str:
        """Get junior title for field"""
        titles = {
            FieldType.DATA_ANALYSIS: 'Data Analyst',
            FieldType.SOFTWARE_DEVELOPMENT: 'Software Engineer',
            FieldType.PROJECT_MANAGEMENT: 'Project Coordinator',
            FieldType.MARKETING: 'Marketing Specialist',
            FieldType.FINANCE: 'Financial Analyst'
        }
        return titles.get(field, 'Analyst')

    def _get_degree_for_field(self, field: FieldType) -> str:
        """Get appropriate degree for field"""
        degrees = {
            FieldType.DATA_ANALYSIS: 'Mathematics',
            FieldType.SOFTWARE_DEVELOPMENT: 'Computer Science',
            FieldType.PROJECT_MANAGEMENT: 'Business Administration',
            FieldType.MARKETING: 'Marketing',
            FieldType.FINANCE: 'Finance'
        }
        return degrees.get(field, 'Business Administration')

    def generate_job_posting(self, field: FieldType = None, experience_level: str = None,
                           salary_range: Dict[str, int] = None, location: str = None) -> MockJobData:
        """Generate a realistic job posting for testing"""
        
        # Randomly select field if not specified
        if field is None:
            field = random.choice(list(FieldType))
        
        # Randomly select experience level if not specified
        if experience_level is None:
            experience_level = random.choice(['Entry', 'Mid', 'Senior'])
        
        # Generate salary range if not specified
        if salary_range is None:
            field_salary_range = self.field_data[field]['salary_ranges'][experience_level]
            min_salary = field_salary_range[0]
            max_salary = field_salary_range[1]
            salary_range = {
                'min': min_salary,
                'max': max_salary,
                'midpoint': (min_salary + max_salary) // 2
            }
        
        # Generate location if not specified
        if location is None:
            location = random.choice(self.target_demographic['locations'])
        
        # Generate company and tier
        company_tier = random.choice(list(CompanyTier))
        company = random.choice(self.company_data[company_tier])
        
        # Generate title
        title = random.choice(self.field_data[field]['titles'])
        if experience_level == 'Senior':
            title = f"Senior {title}"
        elif experience_level == 'Entry':
            title = f"Junior {title}"
        
        # Generate skills
        skills = self._generate_skills(field, ExperienceLevel(experience_level))
        
        # Determine remote work availability
        remote_work = random.choice([True, False])
        
        return MockJobData(
            title=title,
            company=company,
            location=location,
            salary_range=salary_range,
            skills=skills,
            experience_level=experience_level,
            company_tier=company_tier,
            remote_work=remote_work
        )

    def generate_job_market_data(self, field: FieldType = None, location: str = None) -> Dict[str, Any]:
        """Generate job market data for testing"""
        
        if field is None:
            field = random.choice(list(FieldType))
        
        if location is None:
            location = random.choice(self.target_demographic['locations'])
        
        # Generate market statistics
        base_salary = self.field_data[field]['salary_ranges']['Mid'][0]
        
        return {
            'field': field.value,
            'location': location,
            'market_data': {
                'average_salary': base_salary + random.randint(0, 10000),
                'median_salary': base_salary + random.randint(-5000, 5000),
                'salary_10th_percentile': base_salary - random.randint(10000, 15000),
                'salary_90th_percentile': base_salary + random.randint(15000, 25000),
                'job_growth_rate': random.uniform(0.05, 0.15),
                'demand_score': random.uniform(0.7, 1.0)
            },
            'demographics': {
                'age_distribution': {
                    '25-29': random.randint(20, 30),
                    '30-34': random.randint(30, 40),
                    '35-39': random.randint(20, 30)
                },
                'education_distribution': {
                    'bachelor': random.randint(60, 80),
                    'master': random.randint(15, 25),
                    'phd': random.randint(5, 10)
                }
            }
        }

    def generate_test_scenarios(self, num_scenarios: int = 10) -> List[Dict[str, Any]]:
        """Generate comprehensive test scenarios"""
        scenarios = []
        
        for i in range(num_scenarios):
            # Generate random parameters
            field = random.choice(list(FieldType))
            experience_level = random.choice(list(ExperienceLevel))
            risk_preference = random.choice(['conservative', 'balanced', 'aggressive'])
            
            # Generate resume
            resume_data = self.generate_resume(field, experience_level)
            
            # Generate job market data
            market_data = self.generate_job_market_data(field, resume_data.locations[0])
            
            # Generate job postings
            job_postings = []
            for j in range(random.randint(5, 15)):
                job_posting = self.generate_job_posting(field, experience_level.value)
                job_postings.append(job_posting)
            
            scenario = {
                'id': i + 1,
                'name': f"Test Scenario {i + 1}",
                'resume_data': resume_data,
                'market_data': market_data,
                'job_postings': job_postings,
                'risk_preference': risk_preference,
                'expected_outcomes': {
                    'field_detection': field.value,
                    'experience_level': experience_level.value,
                    'min_salary_increase': 0.15,
                    'max_salary_increase': 0.45
                }
            }
            
            scenarios.append(scenario)
        
        return scenarios

    def generate_demographic_test_data(self) -> Dict[str, Any]:
        """Generate demographic-specific test data"""
        return {
            'target_demographic': self.target_demographic,
            'hbcu_graduates': [
                {
                    'institution': hbcu,
                    'field': random.choice(list(FieldType)).value,
                    'graduation_year': random.randint(2018, 2023),
                    'current_salary': random.randint(45000, 120000),
                    'location': random.choice(self.target_demographic['locations'])
                }
                for hbcu in self.target_demographic['hbcus']
                for _ in range(5)  # 5 graduates per HBCU
            ],
            'location_preferences': {
                location: {
                    'popularity_score': random.uniform(0.5, 1.0),
                    'cost_of_living': random.uniform(0.8, 1.5),
                    'job_market_strength': random.uniform(0.6, 1.0)
                }
                for location in self.target_demographic['locations']
            },
            'salary_distributions': {
                'entry_level': {'min': 45000, 'max': 65000, 'median': 55000},
                'mid_level': {'min': 65000, 'max': 85000, 'median': 75000},
                'senior_level': {'min': 85000, 'max': 120000, 'median': 95000}
            }
        }

    def save_test_data(self, filename: str, data: Any):
        """Save test data to file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_test_data(self, filename: str) -> Any:
        """Load test data from file"""
        with open(filename, 'r') as f:
            return json.load(f)


class TestMockDataGenerator(unittest.TestCase):
    """Tests for mock data generator"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = MockDataGenerator()

    def test_resume_generation(self):
        """Test resume generation"""
        # Test with specific parameters
        resume = self.generator.generate_resume(
            field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.MID,
            current_salary=75000,
            education='Morehouse College'
        )
        
        # Verify resume structure
        self.assertIsInstance(resume, MockResumeData)
        self.assertEqual(resume.field, FieldType.DATA_ANALYSIS)
        self.assertEqual(resume.experience_level, ExperienceLevel.MID)
        self.assertEqual(resume.current_salary, 75000)
        self.assertEqual(resume.education, 'Morehouse College')
        self.assertGreater(len(resume.text), 100)
        self.assertGreater(len(resume.skills), 0)
        self.assertGreater(len(resume.locations), 0)
        
        # Verify resume content
        self.assertIn('Morehouse College', resume.text)
        self.assertIn('Data Analyst', resume.text)
        self.assertIn('Python', resume.text)  # Should contain field-specific skills

    def test_job_posting_generation(self):
        """Test job posting generation"""
        job = self.generator.generate_job_posting(
            field=FieldType.SOFTWARE_DEVELOPMENT,
            experience_level='Senior',
            location='Atlanta'
        )
        
        # Verify job structure
        self.assertIsInstance(job, MockJobData)
        self.assertEqual(job.experience_level, 'Senior')
        self.assertEqual(job.location, 'Atlanta')
        self.assertIn('Senior', job.title)
        self.assertGreater(len(job.skills), 0)
        self.assertIsInstance(job.salary_range, dict)
        self.assertIn('min', job.salary_range)
        self.assertIn('max', job.salary_range)
        self.assertIn('midpoint', job.salary_range)

    def test_job_market_data_generation(self):
        """Test job market data generation"""
        market_data = self.generator.generate_job_market_data(
            field=FieldType.MARKETING,
            location='Houston'
        )
        
        # Verify market data structure
        self.assertEqual(market_data['field'], 'Marketing')
        self.assertEqual(market_data['location'], 'Houston')
        self.assertIn('market_data', market_data)
        self.assertIn('demographics', market_data)
        
        # Verify market statistics
        market_stats = market_data['market_data']
        self.assertGreater(market_stats['average_salary'], 0)
        self.assertGreater(market_stats['job_growth_rate'], 0)
        self.assertLess(market_stats['demand_score'], 1.0)

    def test_test_scenarios_generation(self):
        """Test test scenarios generation"""
        scenarios = self.generator.generate_test_scenarios(5)
        
        # Verify scenarios structure
        self.assertEqual(len(scenarios), 5)
        
        for scenario in scenarios:
            self.assertIn('id', scenario)
            self.assertIn('resume_data', scenario)
            self.assertIn('market_data', scenario)
            self.assertIn('job_postings', scenario)
            self.assertIn('risk_preference', scenario)
            self.assertIn('expected_outcomes', scenario)
            
            # Verify resume data
            self.assertIsInstance(scenario['resume_data'], MockResumeData)
            
            # Verify job postings
            self.assertGreater(len(scenario['job_postings']), 0)
            for job in scenario['job_postings']:
                self.assertIsInstance(job, MockJobData)

    def test_demographic_test_data_generation(self):
        """Test demographic test data generation"""
        demographic_data = self.generator.generate_demographic_test_data()
        
        # Verify demographic data structure
        self.assertIn('target_demographic', demographic_data)
        self.assertIn('hbcu_graduates', demographic_data)
        self.assertIn('location_preferences', demographic_data)
        self.assertIn('salary_distributions', demographic_data)
        
        # Verify HBCU graduates data
        hbcu_graduates = demographic_data['hbcu_graduates']
        self.assertGreater(len(hbcu_graduates), 0)
        
        for graduate in hbcu_graduates:
            self.assertIn('institution', graduate)
            self.assertIn('field', graduate)
            self.assertIn('current_salary', graduate)
            self.assertIn('location', graduate)
            self.assertIn(graduate['institution'], self.generator.target_demographic['hbcus'])

    def test_data_persistence(self):
        """Test data persistence (save/load)"""
        # Generate test data
        resume = self.generator.generate_resume()
        scenarios = self.generator.generate_test_scenarios(3)
        
        # Save data
        test_data = {
            'resume': resume,
            'scenarios': scenarios
        }
        
        filename = 'test_mock_data.json'
        self.generator.save_test_data(filename, test_data)
        
        # Load data
        loaded_data = self.generator.load_test_data(filename)
        
        # Verify data integrity
        self.assertIn('resume', loaded_data)
        self.assertIn('scenarios', loaded_data)
        self.assertEqual(len(loaded_data['scenarios']), 3)
        
        # Clean up
        import os
        os.remove(filename)

    def test_field_specific_data(self):
        """Test field-specific data generation"""
        for field in FieldType:
            # Test resume generation for each field
            resume = self.generator.generate_resume(field=field)
            self.assertEqual(resume.field, field)
            
            # Test job posting generation for each field
            job = self.generator.generate_job_posting(field=field)
            self.assertIn(field.value, str(job.title))
            
            # Test market data generation for each field
            market_data = self.generator.generate_job_market_data(field=field)
            self.assertEqual(market_data['field'], field.value)

    def test_experience_level_data(self):
        """Test experience level-specific data generation"""
        for experience_level in ExperienceLevel:
            # Test resume generation for each experience level
            resume = self.generator.generate_resume(experience_level=experience_level)
            self.assertEqual(resume.experience_level, experience_level)
            
            # Test job posting generation for each experience level
            job = self.generator.generate_job_posting(experience_level=experience_level.value)
            self.assertEqual(job.experience_level, experience_level.value)
            
            # Verify salary ranges are appropriate for experience level
            field_data = self.generator.field_data[resume.field]
            expected_range = field_data['salary_ranges'][experience_level.value]
            self.assertGreaterEqual(resume.current_salary, expected_range[0])
            self.assertLessEqual(resume.current_salary, expected_range[1])


if __name__ == '__main__':
    unittest.main() 