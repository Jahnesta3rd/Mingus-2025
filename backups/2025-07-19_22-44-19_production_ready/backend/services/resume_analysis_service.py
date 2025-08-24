"""
Resume Analysis Service
Integrates advanced resume parser with Mingus application infrastructure
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json

from ..ml.models.resume_parser import AdvancedResumeParser, ResumeAnalysis
from ..models.user import User
from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class ResumeAnalysisService:
    """
    Service for resume analysis and career insights
    Integrates with user profiles and provides personalized recommendations
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.parser = AdvancedResumeParser()
        
        # Career advancement thresholds
        self.advancement_thresholds = {
            'ready_for_promotion': 0.7,
            'ready_for_career_change': 0.6,
            'needs_skill_development': 0.4
        }
        
        # Field-specific salary ranges (simplified)
        self.salary_ranges = {
            'Data Analysis': {'entry': 60000, 'mid': 85000, 'senior': 120000},
            'Software Development': {'entry': 70000, 'mid': 95000, 'senior': 130000},
            'Project Management': {'entry': 65000, 'mid': 90000, 'senior': 125000},
            'Marketing': {'entry': 55000, 'mid': 80000, 'senior': 110000},
            'Finance': {'entry': 60000, 'mid': 85000, 'senior': 120000},
            'Sales': {'entry': 50000, 'mid': 75000, 'senior': 100000},
            'Operations': {'entry': 55000, 'mid': 80000, 'senior': 115000},
            'HR': {'entry': 50000, 'mid': 75000, 'senior': 105000}
        }
    
    def analyze_user_resume(self, user_id: int, resume_text: str) -> Dict[str, Any]:
        """
        Analyze user's resume and store results
        
        Args:
            user_id: User ID
            resume_text: Raw resume text
            
        Returns:
            Analysis results with recommendations
        """
        try:
            logger.info(f"Starting resume analysis for user {user_id}")
            
            # Parse resume
            analysis = self.parser.parse_resume(resume_text)
            
            # Store analysis results
            self._store_analysis_results(user_id, analysis)
            
            # Generate personalized recommendations
            recommendations = self._generate_recommendations(user_id, analysis)
            
            # Calculate career insights
            insights = self._calculate_career_insights(analysis)
            
            # Get salary insights
            salary_insights = self._calculate_salary_insights(analysis)
            
            return {
                'analysis': self.parser.get_analysis_summary(analysis),
                'recommendations': recommendations,
                'insights': insights,
                'salary_insights': salary_insights,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume for user {user_id}: {str(e)}")
            raise
    
    def get_user_career_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's career profile and analysis
        
        Args:
            user_id: User ID
            
        Returns:
            Career profile with analysis
        """
        try:
            # Get user profile
            user_profile = self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not user_profile:
                return {'error': 'User profile not found'}
            
            # Get stored analysis results
            analysis_data = self._get_stored_analysis(user_id)
            
            if not analysis_data:
                return {'error': 'No resume analysis found'}
            
            return {
                'user_profile': {
                    'current_position': user_profile.current_position,
                    'years_experience': user_profile.years_experience,
                    'education_level': user_profile.education_level
                },
                'career_analysis': analysis_data,
                'last_updated': analysis_data.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Error getting career profile for user {user_id}: {str(e)}")
            raise
    
    def get_career_recommendations(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized career recommendations
        
        Args:
            user_id: User ID
            
        Returns:
            Career recommendations
        """
        try:
            # Get user's analysis
            analysis_data = self._get_stored_analysis(user_id)
            
            if not analysis_data:
                return {'error': 'No resume analysis found'}
            
            # Generate recommendations based on analysis
            recommendations = self._generate_recommendations(user_id, analysis_data)
            
            return {
                'recommendations': recommendations,
                'priority_level': self._calculate_priority_level(analysis_data),
                'timeline': self._calculate_recommendation_timeline(analysis_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting career recommendations for user {user_id}: {str(e)}")
            raise
    
    def compare_with_market(self, user_id: int) -> Dict[str, Any]:
        """
        Compare user's profile with market data
        
        Args:
            user_id: User ID
            
        Returns:
            Market comparison results
        """
        try:
            analysis_data = self._get_stored_analysis(user_id)
            
            if not analysis_data:
                return {'error': 'No resume analysis found'}
            
            field = analysis_data.get('primary_field')
            experience_level = analysis_data.get('experience_level')
            
            # Get market data for comparison
            market_data = self._get_market_data(field, experience_level)
            
            return {
                'user_profile': analysis_data,
                'market_comparison': market_data,
                'competitive_position': self._calculate_competitive_position(analysis_data, market_data)
            }
            
        except Exception as e:
            logger.error(f"Error comparing with market for user {user_id}: {str(e)}")
            raise
    
    def _store_analysis_results(self, user_id: int, analysis: ResumeAnalysis) -> None:
        """Store analysis results in database"""
        try:
            # Convert analysis to JSON-serializable format
            analysis_data = {
                'field_analysis': {
                    'primary_field': analysis.field_analysis.primary_field.value,
                    'secondary_field': analysis.field_analysis.secondary_field.value if analysis.field_analysis.secondary_field else None,
                    'confidence_score': analysis.field_analysis.confidence_score,
                    'field_keywords': analysis.field_analysis.field_keywords,
                    'field_experience_years': analysis.field_analysis.field_experience_years
                },
                'experience_analysis': {
                    'level': analysis.experience_analysis.level.value,
                    'confidence_score': analysis.experience_analysis.confidence_score,
                    'total_years': analysis.experience_analysis.total_years,
                    'progression_indicator': analysis.experience_analysis.progression_indicator,
                    'leadership_indicators': analysis.experience_analysis.leadership_indicators
                },
                'skills_analysis': {
                    'technical_skills': analysis.skills_analysis.technical_skills,
                    'business_skills': analysis.skills_analysis.business_skills,
                    'soft_skills': analysis.skills_analysis.soft_skills,
                    'technical_business_ratio': analysis.skills_analysis.technical_business_ratio,
                    'proficiency_levels': analysis.skills_analysis.proficiency_levels
                },
                'career_trajectory': {
                    'current_position': analysis.career_trajectory.current_position,
                    'career_progression': analysis.career_trajectory.career_progression,
                    'next_logical_steps': analysis.career_trajectory.next_logical_steps,
                    'growth_potential': analysis.career_trajectory.growth_potential,
                    'advancement_readiness': analysis.career_trajectory.advancement_readiness,
                    'industry_focus': analysis.career_trajectory.industry_focus
                },
                'leadership_potential': analysis.leadership_potential,
                'transferable_skills': analysis.transferable_skills,
                'industry_experience': analysis.industry_experience,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store in user profile or create new table entry
            # For now, we'll store as JSON in a field - in production, create dedicated table
            user_profile = self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if user_profile:
                user_profile.resume_analysis = json.dumps(analysis_data)
                self.db_session.commit()
                logger.info(f"Stored resume analysis for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing analysis results for user {user_id}: {str(e)}")
            self.db_session.rollback()
            raise
    
    def _get_stored_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get stored analysis results from database"""
        try:
            user_profile = self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if user_profile and user_profile.resume_analysis:
                return json.loads(user_profile.resume_analysis)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting stored analysis for user {user_id}: {str(e)}")
            return None
    
    def _generate_recommendations(self, user_id: int, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized career recommendations"""
        recommendations = []
        
        try:
            # Get user's current financial situation
            user_profile = self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            current_salary = user_profile.current_salary if user_profile else 0
            
            # Skill development recommendations
            if analysis.get('skills_analysis', {}).get('technical_business_ratio', 0.5) < 0.3:
                recommendations.append({
                    'category': 'skill_development',
                    'title': 'Develop Technical Skills',
                    'description': 'Focus on building technical expertise to increase market value',
                    'priority': 'high',
                    'estimated_impact': '15-25% salary increase potential'
                })
            
            # Leadership development
            if analysis.get('leadership_potential', 0) > 0.6:
                recommendations.append({
                    'category': 'leadership',
                    'title': 'Pursue Leadership Opportunities',
                    'description': 'Your leadership potential is high - seek management roles',
                    'priority': 'medium',
                    'estimated_impact': '20-30% salary increase potential'
                })
            
            # Career advancement
            if analysis.get('career_trajectory', {}).get('advancement_readiness', 0) > 0.7:
                recommendations.append({
                    'category': 'career_advancement',
                    'title': 'Ready for Promotion',
                    'description': 'You have the skills and experience for the next level',
                    'priority': 'high',
                    'estimated_impact': '25-40% salary increase potential'
                })
            
            # Field transition
            primary_field = analysis.get('field_analysis', {}).get('primary_field')
            if primary_field and self._should_consider_field_change(analysis):
                recommendations.append({
                    'category': 'field_transition',
                    'title': 'Consider Field Transition',
                    'description': f'Your skills could transfer well to {primary_field}',
                    'priority': 'medium',
                    'estimated_impact': '30-50% salary increase potential'
                })
            
            # Networking and visibility
            recommendations.append({
                'category': 'networking',
                'title': 'Enhance Professional Network',
                'description': 'Build connections in your field for better opportunities',
                'priority': 'medium',
                'estimated_impact': '10-20% salary increase potential'
            })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations
    
    def _calculate_career_insights(self, analysis: ResumeAnalysis) -> Dict[str, Any]:
        """Calculate career insights from analysis"""
        insights = {
            'market_position': 'competitive',
            'growth_trajectory': 'positive',
            'risk_factors': [],
            'opportunities': [],
            'skill_gaps': []
        }
        
        try:
            # Market position
            if analysis.leadership_potential > 0.7:
                insights['market_position'] = 'strong'
            elif analysis.leadership_potential < 0.3:
                insights['market_position'] = 'needs_improvement'
            
            # Growth trajectory
            if analysis.career_trajectory.growth_potential > 0.7:
                insights['growth_trajectory'] = 'excellent'
            elif analysis.career_trajectory.growth_potential < 0.4:
                insights['growth_trajectory'] = 'limited'
            
            # Risk factors
            if analysis.skills_analysis.technical_business_ratio < 0.2:
                insights['risk_factors'].append('Limited technical skills may limit opportunities')
            
            if analysis.experience_analysis.total_years < 2:
                insights['risk_factors'].append('Limited experience may affect job security')
            
            # Opportunities
            if analysis.leadership_potential > 0.6:
                insights['opportunities'].append('High leadership potential - management track available')
            
            if len(analysis.transferable_skills) > 5:
                insights['opportunities'].append('Strong transferable skills - flexible career options')
            
            # Skill gaps
            if not analysis.skills_analysis.technical_skills:
                insights['skill_gaps'].append('Technical skills needed for advancement')
            
            if not analysis.skills_analysis.business_skills:
                insights['skill_gaps'].append('Business acumen needed for leadership')
                
        except Exception as e:
            logger.error(f"Error calculating career insights: {str(e)}")
        
        return insights
    
    def _calculate_salary_insights(self, analysis: ResumeAnalysis) -> Dict[str, Any]:
        """Calculate salary insights based on analysis"""
        salary_insights = {
            'current_market_range': {'min': 0, 'max': 0},
            'next_level_range': {'min': 0, 'max': 0},
            'salary_potential': 0,
            'recommendations': []
        }
        
        try:
            field = analysis.field_analysis.primary_field.value
            experience_level = analysis.experience_analysis.level.value
            
            # Get salary ranges for field and experience
            if field in self.salary_ranges:
                field_ranges = self.salary_ranges[field]
                
                # Current level range
                if experience_level == 'Entry':
                    salary_insights['current_market_range'] = {
                        'min': field_ranges['entry'] * 0.8,
                        'max': field_ranges['entry'] * 1.2
                    }
                    next_level = 'mid'
                elif experience_level == 'Mid':
                    salary_insights['current_market_range'] = {
                        'min': field_ranges['mid'] * 0.8,
                        'max': field_ranges['mid'] * 1.2
                    }
                    next_level = 'senior'
                else:  # Senior
                    salary_insights['current_market_range'] = {
                        'min': field_ranges['senior'] * 0.8,
                        'max': field_ranges['senior'] * 1.2
                    }
                    next_level = 'senior'
                
                # Next level range
                salary_insights['next_level_range'] = {
                    'min': field_ranges[next_level] * 0.8,
                    'max': field_ranges[next_level] * 1.2
                }
                
                # Salary potential
                current_max = salary_insights['current_market_range']['max']
                next_max = salary_insights['next_level_range']['max']
                salary_insights['salary_potential'] = ((next_max - current_max) / current_max) * 100
                
                # Recommendations
                if analysis.career_trajectory.advancement_readiness > 0.7:
                    salary_insights['recommendations'].append(
                        f"Ready for advancement to {next_level} level - potential {salary_insights['salary_potential']:.0f}% increase"
                    )
                
                if analysis.leadership_potential > 0.6:
                    salary_insights['recommendations'].append(
                        "Leadership track available - additional 15-25% premium for management roles"
                    )
                    
        except Exception as e:
            logger.error(f"Error calculating salary insights: {str(e)}")
        
        return salary_insights
    
    def _should_consider_field_change(self, analysis: Dict[str, Any]) -> bool:
        """Determine if user should consider field change"""
        try:
            # Check if user has transferable skills and growth potential
            transferable_skills = analysis.get('transferable_skills', [])
            growth_potential = analysis.get('career_trajectory', {}).get('growth_potential', 0)
            
            return len(transferable_skills) > 3 and growth_potential > 0.6
            
        except Exception as e:
            logger.error(f"Error checking field change: {str(e)}")
            return False
    
    def _calculate_priority_level(self, analysis: Dict[str, Any]) -> str:
        """Calculate priority level for recommendations"""
        try:
            advancement_readiness = analysis.get('career_trajectory', {}).get('advancement_readiness', 0)
            leadership_potential = analysis.get('leadership_potential', 0)
            
            if advancement_readiness > 0.8 or leadership_potential > 0.8:
                return 'high'
            elif advancement_readiness > 0.6 or leadership_potential > 0.6:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error calculating priority level: {str(e)}")
            return 'medium'
    
    def _calculate_recommendation_timeline(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Calculate timeline for recommendations"""
        try:
            advancement_readiness = analysis.get('career_trajectory', {}).get('advancement_readiness', 0)
            
            if advancement_readiness > 0.8:
                return {
                    'immediate': '3-6 months',
                    'short_term': '6-12 months',
                    'long_term': '1-2 years'
                }
            elif advancement_readiness > 0.6:
                return {
                    'immediate': '6-12 months',
                    'short_term': '1-2 years',
                    'long_term': '2-3 years'
                }
            else:
                return {
                    'immediate': '1-2 years',
                    'short_term': '2-3 years',
                    'long_term': '3-5 years'
                }
                
        except Exception as e:
            logger.error(f"Error calculating timeline: {str(e)}")
            return {
                'immediate': '6-12 months',
                'short_term': '1-2 years',
                'long_term': '2-3 years'
            }
    
    def _get_market_data(self, field: str, experience_level: str) -> Dict[str, Any]:
        """Get market data for comparison (simplified)"""
        # In production, this would fetch from external APIs or databases
        return {
            'average_salary': 75000,
            'demand_level': 'high',
            'growth_rate': 0.15,
            'skill_demand': ['python', 'sql', 'analytics'],
            'market_trends': ['remote work', 'automation', 'data-driven decisions']
        }
    
    def _calculate_competitive_position(self, analysis: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Calculate competitive position in market"""
        try:
            leadership_potential = analysis.get('leadership_potential', 0)
            skills_count = len(analysis.get('skills_analysis', {}).get('technical_skills', {}))
            
            if leadership_potential > 0.7 and skills_count > 5:
                return 'highly_competitive'
            elif leadership_potential > 0.5 and skills_count > 3:
                return 'competitive'
            else:
                return 'needs_improvement'
                
        except Exception as e:
            logger.error(f"Error calculating competitive position: {str(e)}")
            return 'competitive' 