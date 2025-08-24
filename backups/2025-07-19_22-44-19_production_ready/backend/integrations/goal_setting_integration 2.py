"""
Goal Setting Integration with Job Security
Integrates job security considerations into financial goal setting
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from ..ml.job_security_predictor import JobSecurityPredictor

logger = logging.getLogger(__name__)

class GoalSettingIntegration:
    """
    Integrates job security considerations into goal setting
    - Adds job security considerations to financial goals
    - Creates employment transition planning tools
    - Integrates career development goals with financial planning
    - Adds industry change scenario modeling
    """
    
    def __init__(self, job_security_predictor: JobSecurityPredictor = None):
        self.job_security_predictor = job_security_predictor or JobSecurityPredictor()
        
        # Goal categories with job security considerations
        self.goal_categories = {
            'emergency_fund': {
                'base_target': 6,  # months of expenses
                'risk_adjustments': {
                    'low': 0,
                    'medium': 2,
                    'high': 4,
                    'very_high': 6
                }
            },
            'career_transition': {
                'timeline_adjustments': {
                    'low': 0,
                    'medium': 3,
                    'high': 6,
                    'very_high': 12
                }
            },
            'skill_development': {
                'priority_adjustments': {
                    'low': 0.5,
                    'medium': 1.0,
                    'high': 1.5,
                    'very_high': 2.0
                }
            }
        }
    
    def create_job_security_aware_goals(self, user_id: int, 
                                      user_data: Dict[str, Any],
                                      company_data: Dict[str, Any],
                                      existing_goals: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create or update goals with job security considerations
        
        Args:
            user_id: User ID
            user_data: User data including current goals
            company_data: Company and industry data
            existing_goals: Current user goals
            
        Returns:
            Updated goals with job security considerations
        """
        try:
            # Get job security assessment
            job_security_assessment = self._get_job_security_assessment(user_data, company_data)
            
            # Analyze existing goals
            existing_goals = existing_goals or []
            goal_analysis = self._analyze_existing_goals(existing_goals, job_security_assessment)
            
            # Create new job security focused goals
            new_goals = self._create_job_security_goals(user_data, company_data, job_security_assessment)
            
            # Update existing goals with job security considerations
            updated_goals = self._update_existing_goals(existing_goals, job_security_assessment)
            
            # Create career transition planning
            career_planning = self._create_career_transition_planning(user_data, company_data, job_security_assessment)
            
            # Generate industry change scenarios
            industry_scenarios = self._generate_industry_change_scenarios(user_data, company_data, job_security_assessment)
            
            return {
                'job_security_assessment': job_security_assessment,
                'goal_analysis': goal_analysis,
                'new_goals': new_goals,
                'updated_goals': updated_goals,
                'career_planning': career_planning,
                'industry_scenarios': industry_scenarios,
                'recommendations': self._get_goal_recommendations(job_security_assessment, goal_analysis),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating job security aware goals: {e}")
            return {'error': f'Failed to create goals: {str(e)}'}
    
    def _get_job_security_assessment(self, user_data: Dict[str, Any], 
                                   company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get job security assessment for goal planning"""
        try:
            # Get predictions from ML models
            personal_risk = self.job_security_predictor.personal_risk_predictor.predict(
                user_data, company_data
            )
            
            company_risk = self.job_security_predictor.company_predictor.predict(company_data)
            industry_risk = self.job_security_predictor.industry_predictor.predict(
                company_data.get('industry', 'general')
            )
            
            # Calculate overall risk
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
    
    def _analyze_existing_goals(self, existing_goals: List[Dict[str, Any]], 
                              job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing goals for job security considerations"""
        analysis = {
            'total_goals': len(existing_goals),
            'job_security_related': 0,
            'needs_adjustment': [],
            'well_positioned': [],
            'missing_considerations': []
        }
        
        for goal in existing_goals:
            goal_type = goal.get('type', '')
            
            # Check if goal is job security related
            if goal_type in ['emergency_fund', 'debt_reduction', 'skill_development', 'career_transition']:
                analysis['job_security_related'] += 1
            
            # Check if goal needs adjustment based on risk level
            if self._goal_needs_adjustment(goal, job_security_assessment):
                analysis['needs_adjustment'].append(goal)
            else:
                analysis['well_positioned'].append(goal)
        
        # Identify missing job security considerations
        analysis['missing_considerations'] = self._identify_missing_considerations(
            existing_goals, job_security_assessment
        )
        
        return analysis
    
    def _goal_needs_adjustment(self, goal: Dict[str, Any], 
                             job_security_assessment: Dict[str, Any]) -> bool:
        """Check if a goal needs adjustment based on job security risk"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        goal_type = goal.get('type', '')
        
        if goal_type == 'emergency_fund':
            current_target = goal.get('target_amount', 0)
            recommended_months = self.goal_categories['emergency_fund']['risk_adjustments'][risk_level] + 6
            # Would need monthly expenses to calculate properly
            return False  # Placeholder
        
        elif goal_type == 'career_transition':
            timeline = goal.get('timeline_months', 0)
            recommended_adjustment = self.goal_categories['career_transition']['timeline_adjustments'][risk_level]
            return recommended_adjustment > 0
        
        elif goal_type == 'skill_development':
            priority = goal.get('priority', 1.0)
            recommended_priority = self.goal_categories['skill_development']['priority_adjustments'][risk_level]
            return recommended_priority > priority
        
        return False
    
    def _identify_missing_considerations(self, existing_goals: List[Dict[str, Any]], 
                                       job_security_assessment: Dict[str, Any]) -> List[str]:
        """Identify missing job security considerations in goals"""
        missing = []
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        # Check for emergency fund goal
        has_emergency_fund = any(g.get('type') == 'emergency_fund' for g in existing_goals)
        if not has_emergency_fund and risk_level in ['high', 'very_high']:
            missing.append('emergency_fund')
        
        # Check for skill development goal
        has_skill_development = any(g.get('type') == 'skill_development' for g in existing_goals)
        if not has_skill_development and risk_level in ['medium', 'high', 'very_high']:
            missing.append('skill_development')
        
        # Check for career transition planning
        has_career_transition = any(g.get('type') == 'career_transition' for g in existing_goals)
        if not has_career_transition and risk_level in ['high', 'very_high']:
            missing.append('career_transition')
        
        # Check for networking goal
        has_networking = any(g.get('type') == 'networking' for g in existing_goals)
        if not has_networking and risk_level in ['medium', 'high', 'very_high']:
            missing.append('networking')
        
        return missing
    
    def _create_job_security_goals(self, user_data: Dict[str, Any], 
                                 company_data: Dict[str, Any],
                                 job_security_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new goals focused on job security"""
        new_goals = []
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        # Emergency fund goal
        if risk_level in ['medium', 'high', 'very_high']:
            emergency_months = self.goal_categories['emergency_fund']['risk_adjustments'][risk_level] + 6
            new_goals.append({
                'id': f'emergency_fund_{datetime.now().timestamp()}',
                'type': 'emergency_fund',
                'name': f'Build {emergency_months}-Month Emergency Fund',
                'description': f'Build emergency fund to cover {emergency_months} months of expenses',
                'target_amount': user_data.get('monthly_expenses', 0) * emergency_months,
                'timeline_months': 12,
                'priority': 'high' if risk_level in ['high', 'very_high'] else 'medium',
                'job_security_related': True,
                'risk_level': risk_level
            })
        
        # Skill development goal
        if risk_level in ['medium', 'high', 'very_high']:
            priority = self.goal_categories['skill_development']['priority_adjustments'][risk_level]
            new_goals.append({
                'id': f'skill_development_{datetime.now().timestamp()}',
                'type': 'skill_development',
                'name': 'Enhance Professional Skills',
                'description': 'Develop skills to improve job security and career opportunities',
                'target_amount': 2000,  # Estimated cost for courses/certifications
                'timeline_months': 6,
                'priority': priority,
                'job_security_related': True,
                'risk_level': risk_level,
                'sub_goals': [
                    'Complete relevant certifications',
                    'Attend industry conferences',
                    'Join professional associations',
                    'Develop technical skills'
                ]
            })
        
        # Networking goal
        if risk_level in ['medium', 'high', 'very_high']:
            new_goals.append({
                'id': f'networking_{datetime.now().timestamp()}',
                'type': 'networking',
                'name': 'Build Professional Network',
                'description': 'Expand professional network for career security and opportunities',
                'target_amount': 500,  # Estimated cost for networking events
                'timeline_months': 12,
                'priority': 'medium',
                'job_security_related': True,
                'risk_level': risk_level,
                'sub_goals': [
                    'Attend industry meetups',
                    'Join LinkedIn groups',
                    'Connect with former colleagues',
                    'Participate in professional forums'
                ]
            })
        
        # Career transition planning goal
        if risk_level in ['high', 'very_high']:
            timeline_adjustment = self.goal_categories['career_transition']['timeline_adjustments'][risk_level]
            new_goals.append({
                'id': f'career_transition_{datetime.now().timestamp()}',
                'type': 'career_transition',
                'name': 'Plan Career Transition',
                'description': 'Develop plan for potential career transition or industry change',
                'target_amount': 0,  # Planning goal, no direct cost
                'timeline_months': 12 + timeline_adjustment,
                'priority': 'high',
                'job_security_related': True,
                'risk_level': risk_level,
                'sub_goals': [
                    'Research target industries',
                    'Identify transferable skills',
                    'Create transition timeline',
                    'Build industry connections'
                ]
            })
        
        return new_goals
    
    def _update_existing_goals(self, existing_goals: List[Dict[str, Any]], 
                             job_security_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update existing goals with job security considerations"""
        updated_goals = []
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        for goal in existing_goals:
            updated_goal = goal.copy()
            
            # Add job security metadata
            updated_goal['job_security_risk_level'] = risk_level
            updated_goal['last_risk_assessment'] = datetime.now().isoformat()
            
            # Adjust goal based on risk level
            if goal.get('type') == 'emergency_fund':
                current_target = goal.get('target_amount', 0)
                adjustment = self.goal_categories['emergency_fund']['risk_adjustments'][risk_level]
                if adjustment > 0:
                    updated_goal['adjusted_target'] = current_target * (1 + adjustment / 6)
                    updated_goal['adjustment_reason'] = f'Increased due to {risk_level} job security risk'
            
            elif goal.get('type') == 'skill_development':
                current_priority = goal.get('priority', 1.0)
                recommended_priority = self.goal_categories['skill_development']['priority_adjustments'][risk_level]
                if recommended_priority > current_priority:
                    updated_goal['adjusted_priority'] = recommended_priority
                    updated_goal['adjustment_reason'] = f'Priority increased due to {risk_level} job security risk'
            
            updated_goals.append(updated_goal)
        
        return updated_goals
    
    def _create_career_transition_planning(self, user_data: Dict[str, Any], 
                                         company_data: Dict[str, Any],
                                         job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create career transition planning based on job security assessment"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        planning = {
            'risk_level': risk_level,
            'recommended_timeline': self._get_transition_timeline(risk_level),
            'skill_gaps': self._identify_skill_gaps(user_data, company_data),
            'target_industries': self._suggest_target_industries(user_data, company_data),
            'transition_strategy': self._create_transition_strategy(risk_level, user_data),
            'financial_considerations': self._get_transition_financial_considerations(user_data, risk_level)
        }
        
        return planning
    
    def _get_transition_timeline(self, risk_level: str) -> Dict[str, Any]:
        """Get recommended transition timeline based on risk level"""
        timelines = {
            'low': {
                'preparation_months': 6,
                'active_search_months': 3,
                'total_timeline': 9,
                'urgency': 'low'
            },
            'medium': {
                'preparation_months': 4,
                'active_search_months': 2,
                'total_timeline': 6,
                'urgency': 'medium'
            },
            'high': {
                'preparation_months': 3,
                'active_search_months': 2,
                'total_timeline': 5,
                'urgency': 'high'
            },
            'very_high': {
                'preparation_months': 2,
                'active_search_months': 1,
                'total_timeline': 3,
                'urgency': 'critical'
            }
        }
        
        return timelines.get(risk_level, timelines['medium'])
    
    def _identify_skill_gaps(self, user_data: Dict[str, Any], 
                           company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify skill gaps for career transition"""
        current_skills = user_data.get('skills', [])
        industry = company_data.get('industry', 'general')
        
        # This would typically use industry data to identify required skills
        # For now, return placeholder skill gaps
        skill_gaps = [
            {
                'skill': 'Data Analysis',
                'current_level': 'basic',
                'required_level': 'intermediate',
                'priority': 'high',
                'estimated_cost': 500,
                'timeline_months': 3
            },
            {
                'skill': 'Project Management',
                'current_level': 'none',
                'required_level': 'basic',
                'priority': 'medium',
                'estimated_cost': 300,
                'timeline_months': 2
            }
        ]
        
        return skill_gaps
    
    def _suggest_target_industries(self, user_data: Dict[str, Any], 
                                 company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest target industries for transition"""
        current_industry = company_data.get('industry', 'general')
        
        # This would use industry data to suggest related industries
        suggestions = [
            {
                'industry': 'Technology',
                'similarity_score': 0.8,
                'growth_rate': 'high',
                'average_salary': 85000,
                'transition_difficulty': 'medium'
            },
            {
                'industry': 'Healthcare',
                'similarity_score': 0.6,
                'growth_rate': 'high',
                'average_salary': 75000,
                'transition_difficulty': 'high'
            },
            {
                'industry': 'Finance',
                'similarity_score': 0.7,
                'growth_rate': 'medium',
                'average_salary': 80000,
                'transition_difficulty': 'medium'
            }
        ]
        
        return suggestions
    
    def _create_transition_strategy(self, risk_level: str, 
                                  user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create career transition strategy"""
        strategy = {
            'phase_1_preparation': {
                'duration_months': 2 if risk_level in ['high', 'very_high'] else 3,
                'activities': [
                    'Update resume and LinkedIn profile',
                    'Identify target companies and roles',
                    'Research salary expectations',
                    'Prepare interview responses'
                ]
            },
            'phase_2_skill_development': {
                'duration_months': 3 if risk_level in ['high', 'very_high'] else 6,
                'activities': [
                    'Complete relevant certifications',
                    'Develop technical skills',
                    'Build portfolio or case studies',
                    'Attend industry events'
                ]
            },
            'phase_3_networking': {
                'duration_months': 2,
                'activities': [
                    'Connect with industry professionals',
                    'Join professional associations',
                    'Attend networking events',
                    'Reach out to former colleagues'
                ]
            },
            'phase_4_active_search': {
                'duration_months': 2 if risk_level in ['high', 'very_high'] else 3,
                'activities': [
                    'Apply to target positions',
                    'Schedule informational interviews',
                    'Follow up on applications',
                    'Negotiate offers'
                ]
            }
        }
        
        return strategy
    
    def _get_transition_financial_considerations(self, user_data: Dict[str, Any], 
                                               risk_level: str) -> Dict[str, Any]:
        """Get financial considerations for career transition"""
        considerations = {
            'emergency_fund_requirement': {
                'low': 3,
                'medium': 6,
                'high': 9,
                'very_high': 12
            }[risk_level],
            'estimated_transition_costs': {
                'certifications': 1000,
                'networking_events': 500,
                'resume_services': 200,
                'interview_travel': 300,
                'total': 2000
            },
            'salary_expectations': {
                'current_salary': user_data.get('current_salary', 60000),
                'target_salary': user_data.get('current_salary', 60000) * 1.15,
                'negotiation_buffer': 0.1
            }
        }
        
        return considerations
    
    def _generate_industry_change_scenarios(self, user_data: Dict[str, Any], 
                                          company_data: Dict[str, Any],
                                          job_security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate industry change scenario modeling"""
        current_industry = company_data.get('industry', 'general')
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        scenarios = {
            'stay_current_industry': {
                'probability': 0.6 if risk_level == 'low' else 0.3,
                'timeline_months': 3,
                'salary_impact': 0.05,
                'risk_reduction': 0.2
            },
            'transition_related_industry': {
                'probability': 0.3 if risk_level == 'low' else 0.5,
                'timeline_months': 6,
                'salary_impact': 0.1,
                'risk_reduction': 0.4
            },
            'complete_industry_change': {
                'probability': 0.1 if risk_level == 'low' else 0.2,
                'timeline_months': 12,
                'salary_impact': -0.1,
                'risk_reduction': 0.6
            }
        }
        
        return scenarios
    
    def _get_goal_recommendations(self, job_security_assessment: Dict[str, Any], 
                                goal_analysis: Dict[str, Any]) -> List[str]:
        """Get recommendations for goal setting based on job security"""
        recommendations = []
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        if risk_level in ['high', 'very_high']:
            recommendations.append("Prioritize emergency fund and skill development goals")
            recommendations.append("Consider accelerating career transition planning")
        
        if goal_analysis['job_security_related'] < 2:
            recommendations.append("Add more job security focused goals")
        
        if goal_analysis['needs_adjustment']:
            recommendations.append(f"Review and adjust {len(goal_analysis['needs_adjustment'])} existing goals")
        
        if goal_analysis['missing_considerations']:
            recommendations.append(f"Add goals for: {', '.join(goal_analysis['missing_considerations'])}")
        
        return recommendations 