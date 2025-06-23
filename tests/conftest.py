"""
Pytest configuration and fixtures for job security testing
"""

import pytest
import tempfile
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from backend.app_factory import create_app
from backend.models.base import Base
from backend.app_factory import engine
from backend.services.user_service import UserService
from backend.services.onboarding_service import OnboardingService


@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        Base.metadata.create_all(engine)
        yield app
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'id': 1,
        'email': 'test@example.com',
        'full_name': 'Test User',
        'age': 32,
        'years_experience': 8,
        'education_level': 'bachelor',
        'skills': ['python', 'data_analysis', 'project_management'],
        'current_salary': 85000,
        'tenure_months': 36,
        'performance_rating': 4.5,
        'department': 'engineering',
        'role_level': 'senior',
        'certifications': ['AWS', 'PMP'],
        'languages': ['English', 'Spanish'],
        'remote_work_capability': True,
        'willingness_to_relocate': True,
        'industry_experience': 6,
        'management_experience': 2,
        'publications': 3,
        'patents': 1,
        'awards': ['Employee of the Year 2023'],
        'volunteer_work': True,
        'professional_memberships': ['IEEE', 'ACM'],
        'github_contributions': 150,
        'linkedin_connections': 500,
        'blog_posts': 12,
        'conference_presentations': 5
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing"""
    return {
        'company_id': 'COMP001',
        'company_name': 'TechInnovate Inc',
        'industry': 'technology',
        'sub_industry': 'software_development',
        'size': 'medium',
        'location': 'San Francisco, CA',
        'financial_health': 'strong',
        'revenue_growth': 0.25,
        'profit_margin': 0.18,
        'employee_count': 750,
        'founded_year': 2015,
        'funding_rounds': 4,
        'last_funding_date': '2023-06-15',
        'funding_amount': 50000000,
        'valuation': 500000000,
        'ipo_status': 'private',
        'acquisition_target': False,
        'layoff_history': {
            '2020': 0,
            '2021': 0,
            '2022': 0,
            '2023': 0
        },
        'hiring_trends': {
            '2020': 50,
            '2021': 75,
            '2022': 100,
            '2023': 125
        },
        'employee_satisfaction': 4.2,
        'glassdoor_rating': 4.3,
        'customer_satisfaction': 4.5,
        'market_share': 0.15,
        'competitors': ['TechCorp', 'InnovateSoft', 'DevSolutions'],
        'technology_stack': ['Python', 'React', 'AWS', 'Kubernetes'],
        'business_model': 'SaaS',
        'customer_base': 10000,
        'revenue_per_employee': 200000,
        'debt_to_equity_ratio': 0.3,
        'cash_reserves': 25000000,
        'burn_rate': 2000000,
        'runway_months': 12
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'industry_growth_rate': 0.12,
        'unemployment_rate': 0.035,
        'job_market_health': 'strong',
        'skill_demand': {
            'python': 'very_high',
            'data_analysis': 'very_high',
            'project_management': 'high',
            'machine_learning': 'very_high',
            'cloud_computing': 'high',
            'devops': 'high'
        },
        'geographic_economic_health': 'strong',
        'salary_trends': {
            'software_engineer': 0.08,
            'data_scientist': 0.12,
            'product_manager': 0.10
        },
        'remote_work_adoption': 0.75,
        'automation_risk': {
            'software_development': 0.15,
            'data_analysis': 0.25,
            'project_management': 0.10
        },
        'industry_disruption_risk': 0.20,
        'regulatory_environment': 'stable',
        'economic_outlook': 'positive',
        'venture_capital_activity': 'high',
        'merger_acquisition_activity': 'moderate',
        'global_economic_indicators': {
            'gdp_growth': 0.025,
            'inflation_rate': 0.03,
            'interest_rates': 0.05
        }
    }


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing"""
    return {
        'current_savings': 15000,
        'monthly_expenses': 4000,
        'debt_payments': 800,
        'emergency_fund': 8000,
        'investment_assets': 25000,
        'monthly_income': 6250,
        'monthly_savings_rate': 0.2,
        'insurance_coverage': {
            'health': True,
            'disability': False,
            'life': False,
            'unemployment': False
        },
        'debt_breakdown': {
            'credit_cards': 5000,
            'student_loans': 15000,
            'mortgage': 200000,
            'car_loan': 8000
        },
        'investment_breakdown': {
            'retirement_accounts': 15000,
            'brokerage_accounts': 8000,
            'real_estate': 2000
        }
    }


@pytest.fixture
def sample_goals_data():
    """Sample goals data for testing"""
    return [
        {
            'id': 1,
            'type': 'emergency_fund',
            'name': 'Build 6-Month Emergency Fund',
            'description': 'Build emergency fund to cover 6 months of expenses',
            'target_amount': 24000,
            'current_amount': 8000,
            'timeline_months': 12,
            'priority': 'high',
            'progress_percentage': 33,
            'job_security_related': True
        },
        {
            'id': 2,
            'type': 'skill_development',
            'name': 'Learn Machine Learning',
            'description': 'Complete ML certification to improve job security',
            'target_amount': 2000,
            'current_amount': 500,
            'timeline_months': 6,
            'priority': 'medium',
            'progress_percentage': 25,
            'job_security_related': True
        },
        {
            'id': 3,
            'type': 'networking',
            'name': 'Build Professional Network',
            'description': 'Expand professional network for career opportunities',
            'target_amount': 500,
            'current_amount': 200,
            'timeline_months': 12,
            'priority': 'medium',
            'progress_percentage': 40,
            'job_security_related': True
        }
    ]


@pytest.fixture
def sample_notifications_data():
    """Sample notifications data for testing"""
    return [
        {
            'id': 1,
            'type': 'risk_alert',
            'title': 'Job Security Risk Increased',
            'message': 'Your job security risk has increased from medium to high',
            'priority': 'high',
            'read': False,
            'created_at': datetime.now() - timedelta(hours=2),
            'action_required': True
        },
        {
            'id': 2,
            'type': 'recommendation_update',
            'title': 'New Skill Recommendation',
            'message': 'Consider learning cloud computing to improve job security',
            'priority': 'medium',
            'read': False,
            'created_at': datetime.now() - timedelta(days=1),
            'action_required': False
        },
        {
            'id': 3,
            'type': 'goal_reminder',
            'title': 'Goal Progress Update',
            'message': 'You\'re 25% complete with your ML certification goal',
            'priority': 'low',
            'read': True,
            'created_at': datetime.now() - timedelta(days=3),
            'action_required': False
        }
    ]


@pytest.fixture
def mock_job_security_predictor():
    """Mock job security predictor"""
    mock_predictor = Mock()
    
    # Mock prediction results
    mock_predictor.predict_comprehensive.return_value = {
        'overall_risk_score': 0.45,
        'risk_level': 'medium',
        'confidence': 0.82,
        'risk_factors': ['moderate_company_growth', 'stable_industry'],
        'recommendations': [
            'Build emergency fund to 6 months of expenses',
            'Continue skill development',
            'Monitor industry trends'
        ],
        'personal_risk': {
            'risk_score': 0.4,
            'confidence': 0.8,
            'risk_factors': ['good_performance', 'valuable_skills']
        },
        'company_risk': {
            'risk_score': 0.5,
            'confidence': 0.85,
            'risk_factors': ['stable_financials', 'moderate_growth']
        },
        'industry_risk': {
            'risk_score': 0.3,
            'confidence': 0.9,
            'risk_factors': ['strong_growth', 'high_demand']
        }
    }
    
    return mock_predictor


@pytest.fixture
def mock_financial_planning_integration():
    """Mock financial planning integration"""
    mock_integration = Mock()
    
    # Mock financial plan results
    mock_integration.get_job_security_adjusted_financial_plan.return_value = {
        'job_security_assessment': {
            'overall_risk': {'risk_level': 'medium', 'risk_score': 0.45}
        },
        'current_financials': {
            'monthly_income': 6250,
            'monthly_expenses': 4000,
            'current_savings': 8000,
            'emergency_fund_months': 2,
            'monthly_savings_rate': 0.2,
            'debt_payments': 800,
            'investment_assets': 25000
        },
        'adjusted_recommendations': {
            'emergency_fund': {
                'current_months': 2,
                'recommended_months': 6,
                'current_amount': 8000,
                'recommended_amount': 24000,
                'gap': 16000,
                'monthly_savings_needed': 1333
            },
            'investment_strategy': {
                'current_risk_tolerance': 0.7,
                'adjusted_risk_tolerance': 0.56,
                'recommendation': 'Moderate portfolio: 50% bonds, 50% stocks'
            },
            'savings_rate': {
                'current_rate': 0.2,
                'recommended_rate': 0.3,
                'additional_savings_needed': 625
            }
        },
        'scenario_planning': {
            'immediate_layoff': {
                'severance_pay': 0,
                'unemployment_benefits': 2400,
                'savings_depletion_months': 5
            }
        },
        'action_plan': {
            'actions': [
                {
                    'priority': 'high',
                    'category': 'emergency_fund',
                    'action': 'Save $1,333/month to reach emergency fund goal',
                    'timeline': '3-6 months',
                    'impact': 'high'
                }
            ]
        }
    }
    
    return mock_integration


@pytest.fixture
def mock_goal_setting_integration():
    """Mock goal setting integration"""
    mock_integration = Mock()
    
    # Mock goal results
    mock_integration.create_job_security_aware_goals.return_value = {
        'job_security_assessment': {
            'overall_risk': {'risk_level': 'medium', 'risk_score': 0.45}
        },
        'new_goals': [
            {
                'id': 'emergency_fund_1',
                'type': 'emergency_fund',
                'name': 'Build 6-Month Emergency Fund',
                'description': 'Build emergency fund to cover 6 months of expenses',
                'target_amount': 24000,
                'timeline_months': 12,
                'priority': 'high',
                'job_security_related': True
            },
            {
                'id': 'skill_development_1',
                'type': 'skill_development',
                'name': 'Enhance Professional Skills',
                'description': 'Develop skills to improve job security and career opportunities',
                'target_amount': 2000,
                'timeline_months': 6,
                'priority': 1.0,
                'job_security_related': True
            }
        ],
        'career_planning': {
            'risk_level': 'medium',
            'recommended_timeline': {
                'preparation_months': 8,
                'active_search_months': 2,
                'total_timeline': 10,
                'urgency': 'medium'
            },
            'skill_gaps': [
                {
                    'skill': 'Data Analysis',
                    'current_level': 'basic',
                    'required_level': 'intermediate',
                    'priority': 'high',
                    'estimated_cost': 500,
                    'timeline_months': 3
                }
            ]
        }
    }
    
    return mock_integration


@pytest.fixture
def mock_recommendations_integration():
    """Mock recommendations integration"""
    mock_integration = Mock()
    
    # Mock recommendations results
    mock_integration.get_personalized_recommendations.return_value = {
        'job_security_assessment': {
            'overall_risk': {'risk_level': 'medium', 'risk_score': 0.45}
        },
        'skills_recommendations': {
            'skill_gaps': [
                {
                    'skill_name': 'Data Analysis',
                    'importance': 'high',
                    'demand_trend': 'increasing',
                    'estimated_cost': 500,
                    'timeline_months': 3,
                    'priority': 1.0
                }
            ],
            'learning_resources': [
                {
                    'skill_name': 'Data Analysis',
                    'resources': [
                        {
                            'name': 'Data Analysis Course on Coursera',
                            'type': 'online_course',
                            'cost': 500,
                            'duration': '3 months',
                            'rating': 4.5
                        }
                    ]
                }
            ],
            'priority_skills': [
                {
                    'skill_name': 'Data Analysis',
                    'importance': 'high',
                    'priority': 1.0
                }
            ]
        },
        'networking_recommendations': {
            'networking_plan': {
                'monthly_events': 2,
                'online_activities': 5,
                'one_on_one_meetings': 3
            },
            'activities': [
                {
                    'name': 'Attend Industry Meetups',
                    'priority': 'medium',
                    'frequency': 'monthly',
                    'time_commitment': '2 hours'
                }
            ]
        },
        'financial_recommendations': {
            'recommendations': {
                'emergency_fund': {
                    'current_amount': 8000,
                    'recommended_amount': 24000,
                    'gap': 16000,
                    'priority': 'high'
                },
                'disability_insurance': {
                    'recommended_coverage': 45000,
                    'monthly_premium': 450,
                    'priority': 'medium'
                }
            },
            'priority_products': ['emergency_fund']
        },
        'action_plan': {
            'actions': [
                {
                    'category': 'emergency_fund',
                    'action': 'Save $1,333/month to reach emergency fund goal',
                    'priority': 'high',
                    'timeline': '3-6 months',
                    'cost': 0
                }
            ],
            'next_30_days': [
                {
                    'category': 'emergency_fund',
                    'action': 'Save $1,333/month to reach emergency fund goal',
                    'priority': 'high',
                    'timeline': '3-6 months',
                    'cost': 0
                }
            ]
        }
    }
    
    return mock_integration


@pytest.fixture
def sample_test_data():
    """Generate sample test data for performance testing"""
    np.random.seed(42)
    
    # Generate user data
    users = []
    for i in range(100):
        user = {
            'id': i + 1,
            'age': np.random.randint(25, 65),
            'years_experience': np.random.randint(1, 20),
            'education_level': np.random.choice(['high_school', 'bachelor', 'master', 'phd']),
            'skills': np.random.choice(['python', 'javascript', 'java', 'react', 'aws'], 
                                     size=np.random.randint(3, 8), replace=False).tolist(),
            'current_salary': np.random.randint(50000, 150000),
            'tenure_months': np.random.randint(1, 120),
            'performance_rating': np.random.uniform(3.0, 5.0),
            'department': np.random.choice(['engineering', 'marketing', 'sales', 'finance']),
            'role_level': np.random.choice(['junior', 'mid', 'senior', 'lead'])
        }
        users.append(user)
    
    # Generate company data
    companies = []
    for i in range(50):
        company = {
            'company_id': f'COMP{i:03d}',
            'company_name': f'Company{i}',
            'industry': np.random.choice(['technology', 'finance', 'healthcare', 'retail']),
            'size': np.random.choice(['small', 'medium', 'large']),
            'location': np.random.choice(['San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA']),
            'financial_health': np.random.choice(['strong', 'stable', 'weak']),
            'revenue_growth': np.random.uniform(-0.1, 0.3),
            'profit_margin': np.random.uniform(0.05, 0.25),
            'employee_count': np.random.randint(50, 5000)
        }
        companies.append(company)
    
    return {
        'users': users,
        'companies': companies,
        'market_data': sample_market_data()
    }


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        'single_prediction_time': 1.0,  # seconds
        'batch_prediction_time': 5.0,   # seconds for 10 predictions
        'memory_threshold': 100 * 1024 * 1024,  # 100MB
        'cpu_threshold': 80,  # 80% CPU usage
        'api_response_time': 1.0,  # seconds
        'database_query_time': 0.1,  # seconds
        'concurrent_users': 10,
        'success_rate': 0.95  # 95% success rate
    }


@pytest.fixture
def test_database():
    """Create test database"""
    db_fd, db_path = tempfile.mkstemp()
    
    yield db_path
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client"""
    # Register and login user
    registration_data = {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone_number': '1234567890'
    }
    
    client.post('/api/auth/register',
               data=json.dumps(registration_data),
               content_type='application/json')
    
    login_data = {
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    }
    
    client.post('/api/auth/login',
               data=json.dumps(login_data),
               content_type='application/json')
    
    return client 