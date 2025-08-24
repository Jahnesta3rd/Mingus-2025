"""
Recommendations Integration for Job Security
Provides personalized recommendations based on job security assessment
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from ..ml.job_security_predictor import JobSecurityPredictor

logger = logging.getLogger(__name__)

class RecommendationsIntegration:
    """
    Provides personalized job security recommendations
    - Skills development suggestions based on industry trends
    - Networking recommendations for career security
    - Financial product recommendations (insurance, emergency funds)
    - Career transition planning tools
    """
    
    def __init__(self, job_security_predictor: JobSecurityPredictor = None):
        self.job_security_predictor = job_security_predictor or JobSecurityPredictor()
        
        # Recommendation categories
        self.recommendation_categories = {
            'skills_development': {
                'priority_weights': {
                    'low': 0.5,
                    'medium': 1.0,
                    'high': 1.5,
                    'very_high': 2.0
                }
            },
            'networking': {
                'frequency_adjustments': {
                    'low': 0.5,
                    'medium': 1.0,
                    'high': 1.5,
                    'very_high': 2.0
                }
            },
            'financial_products': {
                'coverage_adjustments': {
                    'low': 1.0,
                    'medium': 1.2,
                    'high': 1.5,
                    'very_high': 2.0
                }
            }
        }
    
    def get_personalized_recommendations(self, user_id: int, 
                                       user_data: Dict[str, Any],
                                       company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive personalized recommendations
        
        Args:
            user_id: User ID
            user_data: User profile and preferences
            company_data: Company and industry information
            
        Returns:
            Personalized recommendations across all categories
        """
        try:
            # Get job security assessment
            job_security_assessment = self._get_job_security_assessment(user_data, company_data)
            
            # Generate recommendations by category
            skills_recommendations = self._get_skills_recommendations(user_data, company_data, job_security_assessment)
            networking_recommendations = self._get_networking_recommendations(user_data, company_data, job_security_assessment)
            financial_recommendations = self._get_financial_recommendations(user_data, company_data, job_security_assessment)
            career_recommendations = self._get_career_recommendations(user_data, company_data, job_security_assessment)
            
            # Create action plan
            action_plan = self._create_recommendation_action_plan(
                skills_recommendations,
                networking_recommendations,
                financial_recommendations,
                career_recommendations,
                job_security_assessment
            )
            
            return {
                'job_security_assessment': job_security_assessment,
                'skills_recommendations': skills_recommendations,
                'networking_recommendations': networking_recommendations,
                'financial_recommendations': financial_recommendations,
                'career_recommendations': career_recommendations,
                'action_plan': action_plan,
                'priority_recommendations': self._get_priority_recommendations(job_security_assessment),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {e}")
            return {'error': f'Failed to generate recommendations: {str(e)}'}
    
    def _get_job_security_assessment(self, user_data: Dict[str, Any], 
                                   company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get job security assessment for recommendations"""
        try:
            personal_risk = self.job_security_predictor.personal_risk_predictor.predict(
                user_data, company_data
            )
            
            company_risk = self.job_security_predictor.company_predictor.predict(company_data)
            industry_risk = self.job_security_predictor.industry_predictor.predict(
                company_data.get('industry', 'general')
            )
            
            overall_risk = self._calculate_overall_risk(personal_risk, company_risk, industry_risk)
            
            return {
                'personal_risk': personal_risk,
                'company_risk': company_risk,
                'industry_risk': industry_risk,
                'overall_risk': overall_risk,
                'risk_level': overall_risk['risk_level'],
                'layoff_probability_6m': overall_risk['risk_score']
            }
            
        except Exception as e:
            logger.error(f"Error getting job security assessment: {e}")
            return {
                'overall_risk': {'risk_level': 'medium', 'risk_score': 0.5},
                'layoff_probability_6m': 0.5
            }
    
    def _calculate_overall_risk(self, personal_risk: Dict[str, Any], 
                              company_risk: Dict[str, Any], 
                              industry_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score"""
        weights = {'personal': 0.4, 'company': 0.4, 'industry': 0.2}
        
        personal_score = personal_risk.get('risk_score', 0.5)
        company_score = company_risk.get('risk_score', 0.5)
        industry_score = industry_risk.get('risk_score', 0.5)
        
        overall_score = (
            personal_score * weights['personal'] +
            company_score * weights['company'] +
            industry_score * weights['industry']
        )
        
        if overall_score < 0.3:
            risk_level = 'low'
        elif overall_score < 0.6:
            risk_level = 'medium'
        elif overall_score < 0.8:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        return {
            'risk_score': overall_score,
            'risk_level': risk_level
        }
    
    def _get_skills_recommendations(self, user_data: Dict[str, Any], 
                                  company_data: Dict[str, Any],
                                  job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Get skills development recommendations"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        current_skills = user_data.get('skills', [])
        industry = company_data.get('industry', 'general')
        
        # Get industry-specific skill requirements
        industry_skills = self._get_industry_skill_requirements(industry)
        
        # Identify skill gaps
        skill_gaps = []
        for skill in industry_skills:
            if skill['name'] not in [s.get('name') for s in current_skills]:
                skill_gaps.append({
                    'skill_name': skill['name'],
                    'importance': skill['importance'],
                    'demand_trend': skill['demand_trend'],
                    'estimated_cost': skill['estimated_cost'],
                    'timeline_months': skill['timeline_months'],
                    'priority': self._calculate_skill_priority(skill, risk_level)
                })
        
        # Sort by priority
        skill_gaps.sort(key=lambda x: x['priority'], reverse=True)
        
        # Get learning resources
        learning_resources = self._get_learning_resources(skill_gaps[:5])  # Top 5 skills
        
        return {
            'skill_gaps': skill_gaps,
            'learning_resources': learning_resources,
            'recommended_timeline': self._get_skills_timeline(risk_level),
            'estimated_total_cost': sum(s['estimated_cost'] for s in skill_gaps[:5]),
            'priority_skills': skill_gaps[:3]  # Top 3 priority skills
        }
    
    def _get_industry_skill_requirements(self, industry: str) -> List[Dict[str, Any]]:
        """Get industry-specific skill requirements"""
        # This would typically come from a database or API
        # For now, return sample data based on industry
        industry_skills = {
            'technology': [
                {'name': 'Python Programming', 'importance': 'high', 'demand_trend': 'increasing', 'estimated_cost': 500, 'timeline_months': 3},
                {'name': 'Data Analysis', 'importance': 'high', 'demand_trend': 'increasing', 'estimated_cost': 400, 'timeline_months': 2},
                {'name': 'Cloud Computing', 'importance': 'medium', 'demand_trend': 'increasing', 'estimated_cost': 600, 'timeline_months': 4},
                {'name': 'Machine Learning', 'importance': 'medium', 'demand_trend': 'increasing', 'estimated_cost': 800, 'timeline_months': 6}
            ],
            'finance': [
                {'name': 'Financial Modeling', 'importance': 'high', 'demand_trend': 'stable', 'estimated_cost': 600, 'timeline_months': 4},
                {'name': 'Excel Advanced', 'importance': 'high', 'demand_trend': 'stable', 'estimated_cost': 200, 'timeline_months': 1},
                {'name': 'Risk Management', 'importance': 'medium', 'demand_trend': 'increasing', 'estimated_cost': 500, 'timeline_months': 3}
            ],
            'healthcare': [
                {'name': 'Healthcare Analytics', 'importance': 'high', 'demand_trend': 'increasing', 'estimated_cost': 700, 'timeline_months': 4},
                {'name': 'Electronic Health Records', 'importance': 'medium', 'demand_trend': 'stable', 'estimated_cost': 300, 'timeline_months': 2}
            ]
        }
        
        return industry_skills.get(industry, [
            {'name': 'Project Management', 'importance': 'medium', 'demand_trend': 'stable', 'estimated_cost': 400, 'timeline_months': 3},
            {'name': 'Communication Skills', 'importance': 'high', 'demand_trend': 'stable', 'estimated_cost': 200, 'timeline_months': 2}
        ])
    
    def _calculate_skill_priority(self, skill: Dict[str, Any], risk_level: str) -> float:
        """Calculate skill priority based on importance and risk level"""
        importance_scores = {'low': 0.3, 'medium': 0.6, 'high': 1.0}
        risk_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 1.5, 'very_high': 2.0}
        
        importance_score = importance_scores.get(skill['importance'], 0.5)
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        return importance_score * risk_multiplier
    
    def _get_learning_resources(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get learning resources for recommended skills"""
        resources = []
        
        for skill in skills:
            skill_name = skill['skill_name']
            
            # This would typically query a learning platform API
            # For now, return sample resources
            resources.append({
                'skill_name': skill_name,
                'resources': [
                    {
                        'name': f'{skill_name} Course on Coursera',
                        'type': 'online_course',
                        'cost': skill['estimated_cost'],
                        'duration': f"{skill['timeline_months']} months",
                        'rating': 4.5,
                        'url': f'https://coursera.org/{skill_name.lower().replace(" ", "-")}'
                    },
                    {
                        'name': f'{skill_name} Certification',
                        'type': 'certification',
                        'cost': skill['estimated_cost'] * 0.8,
                        'duration': f"{skill['timeline_months']} months",
                        'rating': 4.3,
                        'url': f'https://certification.org/{skill_name.lower().replace(" ", "-")}'
                    }
                ]
            })
        
        return resources
    
    def _get_skills_timeline(self, risk_level: str) -> Dict[str, Any]:
        """Get recommended skills development timeline"""
        timelines = {
            'low': {'total_months': 12, 'skills_per_month': 0.5},
            'medium': {'total_months': 8, 'skills_per_month': 0.75},
            'high': {'total_months': 6, 'skills_per_month': 1.0},
            'very_high': {'total_months': 4, 'skills_per_month': 1.5}
        }
        
        return timelines.get(risk_level, timelines['medium'])
    
    def _get_networking_recommendations(self, user_data: Dict[str, Any], 
                                      company_data: Dict[str, Any],
                                      job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Get networking recommendations"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        industry = company_data.get('industry', 'general')
        location = company_data.get('location', 'general')
        
        # Get networking opportunities
        networking_opportunities = self._get_networking_opportunities(industry, location)
        
        # Adjust frequency based on risk level
        frequency_adjustment = self.recommendation_categories['networking']['frequency_adjustments'][risk_level]
        
        # Create networking plan
        networking_plan = {
            'monthly_events': int(2 * frequency_adjustment),
            'online_activities': int(5 * frequency_adjustment),
            'one_on_one_meetings': int(3 * frequency_adjustment),
            'professional_associations': self._get_professional_associations(industry)
        }
        
        # Get specific networking activities
        activities = self._get_networking_activities(industry, risk_level)
        
        return {
            'networking_plan': networking_plan,
            'activities': activities,
            'opportunities': networking_opportunities,
            'estimated_monthly_cost': networking_plan['monthly_events'] * 50,
            'priority_activities': activities[:3]  # Top 3 activities
        }
    
    def _get_networking_opportunities(self, industry: str, location: str) -> List[Dict[str, Any]]:
        """Get networking opportunities for industry and location"""
        # This would typically query event databases or APIs
        opportunities = [
            {
                'name': f'{industry.title()} Industry Meetup',
                'type': 'in_person',
                'frequency': 'monthly',
                'cost': 25,
                'location': location,
                'description': f'Monthly networking event for {industry} professionals'
            },
            {
                'name': f'{industry.title()} Conference',
                'type': 'conference',
                'frequency': 'annual',
                'cost': 500,
                'location': 'various',
                'description': f'Annual conference for {industry} professionals'
            },
            {
                'name': f'{industry.title()} LinkedIn Group',
                'type': 'online',
                'frequency': 'daily',
                'cost': 0,
                'location': 'online',
                'description': f'Professional group for {industry} discussions'
            }
        ]
        
        return opportunities
    
    def _get_professional_associations(self, industry: str) -> List[Dict[str, Any]]:
        """Get professional associations for industry"""
        associations = {
            'technology': [
                {'name': 'IEEE', 'annual_cost': 150, 'benefits': ['Networking', 'Conferences', 'Publications']},
                {'name': 'ACM', 'annual_cost': 100, 'benefits': ['Networking', 'Research', 'Certifications']}
            ],
            'finance': [
                {'name': 'CFA Institute', 'annual_cost': 275, 'benefits': ['Networking', 'Certifications', 'Research']},
                {'name': 'Financial Planning Association', 'annual_cost': 200, 'benefits': ['Networking', 'Education', 'Resources']}
            ],
            'healthcare': [
                {'name': 'American Medical Association', 'annual_cost': 420, 'benefits': ['Networking', 'Advocacy', 'Education']},
                {'name': 'Healthcare Information and Management Systems Society', 'annual_cost': 150, 'benefits': ['Networking', 'Conferences', 'Resources']}
            ]
        }
        
        return associations.get(industry, [
            {'name': 'Professional Association', 'annual_cost': 100, 'benefits': ['Networking', 'Education']}
        ])
    
    def _get_networking_activities(self, industry: str, risk_level: str) -> List[Dict[str, Any]]:
        """Get specific networking activities"""
        activities = [
            {
                'name': 'Attend Industry Meetups',
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium',
                'frequency': 'monthly',
                'time_commitment': '2 hours',
                'expected_outcome': 'Build local professional network'
            },
            {
                'name': 'Join LinkedIn Groups',
                'priority': 'medium',
                'frequency': 'daily',
                'time_commitment': '15 minutes',
                'expected_outcome': 'Stay updated on industry trends'
            },
            {
                'name': 'Connect with Former Colleagues',
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium',
                'frequency': 'weekly',
                'time_commitment': '30 minutes',
                'expected_outcome': 'Maintain professional relationships'
            },
            {
                'name': 'Participate in Online Forums',
                'priority': 'medium',
                'frequency': 'weekly',
                'time_commitment': '1 hour',
                'expected_outcome': 'Build online presence and expertise'
            }
        ]
        
        return activities
    
    def _get_financial_recommendations(self, user_data: Dict[str, Any], 
                                     company_data: Dict[str, Any],
                                     job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Get financial product recommendations"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        current_salary = user_data.get('current_salary', 60000)
        monthly_expenses = user_data.get('monthly_expenses', 4000)
        
        # Calculate recommended coverage amounts
        coverage_adjustment = self.recommendation_categories['financial_products']['coverage_adjustments'][risk_level]
        
        recommendations = {
            'emergency_fund': {
                'current_amount': user_data.get('emergency_fund', 0),
                'recommended_amount': monthly_expenses * 6 * coverage_adjustment,
                'monthly_contribution': (monthly_expenses * 6 * coverage_adjustment - user_data.get('emergency_fund', 0)) / 12,
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium'
            },
            'disability_insurance': {
                'recommended_coverage': current_salary * 0.6 * coverage_adjustment,
                'monthly_premium': current_salary * 0.01 * coverage_adjustment,
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium'
            },
            'life_insurance': {
                'recommended_coverage': current_salary * 10 * coverage_adjustment,
                'monthly_premium': current_salary * 0.005 * coverage_adjustment,
                'priority': 'medium'
            },
            'unemployment_insurance': {
                'available': True,
                'coverage_percentage': 0.6,
                'duration_months': 6,
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'low'
            }
        }
        
        # Get insurance providers
        insurance_providers = self._get_insurance_providers(recommendations)
        
        return {
            'recommendations': recommendations,
            'providers': insurance_providers,
            'total_monthly_cost': sum(
                rec.get('monthly_premium', 0) for rec in recommendations.values() 
                if isinstance(rec, dict) and 'monthly_premium' in rec
            ),
            'priority_products': [
                name for name, rec in recommendations.items() 
                if isinstance(rec, dict) and rec.get('priority') == 'high'
            ]
        }
    
    def _get_insurance_providers(self, recommendations: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Get insurance provider recommendations"""
        providers = {
            'disability_insurance': [
                {'name': 'Guardian', 'rating': 4.5, 'cost_factor': 1.0},
                {'name': 'Principal', 'rating': 4.3, 'cost_factor': 0.95},
                {'name': 'MetLife', 'rating': 4.2, 'cost_factor': 0.9}
            ],
            'life_insurance': [
                {'name': 'State Farm', 'rating': 4.4, 'cost_factor': 1.0},
                {'name': 'Northwestern Mutual', 'rating': 4.6, 'cost_factor': 1.1},
                {'name': 'New York Life', 'rating': 4.3, 'cost_factor': 0.95}
            ]
        }
        
        return providers
    
    def _get_career_recommendations(self, user_data: Dict[str, Any], 
                                  company_data: Dict[str, Any],
                                  job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Get career transition and development recommendations"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        industry = company_data.get('industry', 'general')
        
        # Get career development opportunities
        career_opportunities = self._get_career_opportunities(industry, risk_level)
        
        # Get transition timeline
        transition_timeline = self._get_career_transition_timeline(risk_level)
        
        # Get target roles
        target_roles = self._get_target_roles(user_data, industry, risk_level)
        
        return {
            'career_opportunities': career_opportunities,
            'transition_timeline': transition_timeline,
            'target_roles': target_roles,
            'development_plan': self._create_career_development_plan(user_data, risk_level),
            'estimated_transition_cost': self._calculate_transition_cost(career_opportunities)
        }
    
    def _get_career_opportunities(self, industry: str, risk_level: str) -> List[Dict[str, Any]]:
        """Get career development opportunities"""
        opportunities = [
            {
                'name': 'Professional Certification',
                'type': 'certification',
                'cost': 500,
                'timeline_months': 6,
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium'
            },
            {
                'name': 'Industry Conference',
                'type': 'networking',
                'cost': 800,
                'timeline_months': 1,
                'priority': 'medium'
            },
            {
                'name': 'Advanced Degree',
                'type': 'education',
                'cost': 30000,
                'timeline_months': 24,
                'priority': 'low' if risk_level == 'low' else 'medium'
            }
        ]
        
        return opportunities
    
    def _get_career_transition_timeline(self, risk_level: str) -> Dict[str, Any]:
        """Get career transition timeline"""
        timelines = {
            'low': {'preparation_months': 12, 'active_search_months': 3},
            'medium': {'preparation_months': 8, 'active_search_months': 2},
            'high': {'preparation_months': 6, 'active_search_months': 2},
            'very_high': {'preparation_months': 3, 'active_search_months': 1}
        }
        
        return timelines.get(risk_level, timelines['medium'])
    
    def _get_target_roles(self, user_data: Dict[str, Any], industry: str, risk_level: str) -> List[Dict[str, Any]]:
        """Get target roles for career transition"""
        current_role = user_data.get('current_role', 'general')
        
        # This would typically use job market data
        target_roles = [
            {
                'title': f'Senior {current_role.title()}',
                'salary_range': (80000, 120000),
                'demand_level': 'high',
                'transition_difficulty': 'low'
            },
            {
                'title': f'{current_role.title()} Manager',
                'salary_range': (90000, 140000),
                'demand_level': 'medium',
                'transition_difficulty': 'medium'
            },
            {
                'title': f'Product Manager',
                'salary_range': (100000, 150000),
                'demand_level': 'high',
                'transition_difficulty': 'high'
            }
        ]
        
        return target_roles
    
    def _create_career_development_plan(self, user_data: Dict[str, Any], risk_level: str) -> Dict[str, Any]:
        """Create career development plan"""
        plan = {
            'short_term': {
                'duration_months': 3,
                'goals': [
                    'Update resume and LinkedIn profile',
                    'Identify target companies',
                    'Start skill development program'
                ]
            },
            'medium_term': {
                'duration_months': 6,
                'goals': [
                    'Complete certifications',
                    'Build professional network',
                    'Apply to target positions'
                ]
            },
            'long_term': {
                'duration_months': 12,
                'goals': [
                    'Secure new position',
                    'Establish industry presence',
                    'Continue professional development'
                ]
            }
        }
        
        return plan
    
    def _calculate_transition_cost(self, opportunities: List[Dict[str, Any]]) -> float:
        """Calculate total transition cost"""
        return sum(opp.get('cost', 0) for opp in opportunities)
    
    def _create_recommendation_action_plan(self, skills_recs: Dict[str, Any],
                                         networking_recs: Dict[str, Any],
                                         financial_recs: Dict[str, Any],
                                         career_recs: Dict[str, Any],
                                         job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create prioritized action plan from all recommendations"""
        actions = []
        
        # Add high priority actions from each category
        for skill in skills_recs.get('priority_skills', [])[:2]:
            actions.append({
                'category': 'skills_development',
                'action': f"Start learning {skill['skill_name']}",
                'priority': 'high',
                'timeline': f"{skill['timeline_months']} months",
                'cost': skill['estimated_cost']
            })
        
        for activity in networking_recs.get('priority_activities', [])[:2]:
            actions.append({
                'category': 'networking',
                'action': activity['name'],
                'priority': activity['priority'],
                'timeline': activity['frequency'],
                'cost': 0
            })
        
        for product in financial_recs.get('priority_products', [])[:2]:
            rec = financial_recs['recommendations'].get(product, {})
            actions.append({
                'category': 'financial_products',
                'action': f"Obtain {product.replace('_', ' ').title()}",
                'priority': rec.get('priority', 'medium'),
                'timeline': '1 month',
                'cost': rec.get('monthly_premium', 0)
            })
        
        # Sort by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return {
            'actions': actions,
            'next_30_days': [a for a in actions if a['timeline'] in ['1 month', 'monthly']],
            'next_90_days': [a for a in actions if a['timeline'] in ['1 month', 'monthly', '3 months']],
            'total_estimated_cost': sum(a.get('cost', 0) for a in actions)
        }
    
    def _get_priority_recommendations(self, job_security_assessment: Dict[str, Any]) -> List[str]:
        """Get top priority recommendations based on risk level"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        if risk_level == 'very_high':
            return [
                "Immediately build emergency fund to 12 months of expenses",
                "Start job search and networking activities",
                "Consider obtaining disability insurance",
                "Accelerate skill development program"
            ]
        elif risk_level == 'high':
            return [
                "Build emergency fund to 9 months of expenses",
                "Begin networking and skill development",
                "Review insurance coverage",
                "Start career transition planning"
            ]
        elif risk_level == 'medium':
            return [
                "Build emergency fund to 6 months of expenses",
                "Continue skill development",
                "Maintain professional network",
                "Monitor industry trends"
            ]
        else:
            return [
                "Maintain current emergency fund",
                "Continue professional development",
                "Stay connected with professional network",
                "Monitor job market trends"
            ] 