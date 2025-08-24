"""
Intelligent Job Matching Service
Integrates intelligent job matching with Mingus application infrastructure
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
import numpy as np

from ..ml.models.intelligent_job_matcher import IntelligentJobMatcher, SearchParameters
from ..ml.models.resume_parser import AdvancedResumeParser
from ..models.user import User
from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class IntelligentJobMatchingService:
    """
    Service for intelligent job matching with income advancement focus
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.job_matcher = IntelligentJobMatcher()
        self.resume_parser = AdvancedResumeParser()
        
        # Income advancement thresholds
        self.income_thresholds = {
            'minimum_increase': 0.15,  # 15% minimum increase
            'target_increase': 0.25,   # 25% target increase
            'excellent_increase': 0.35  # 35% excellent increase
        }
        
        # MSA-specific salary data (simplified - in production, use real data)
        self.msa_salary_data = {
            'Atlanta': {'cost_of_living': 1.0, 'salary_multiplier': 1.0},
            'Houston': {'cost_of_living': 0.95, 'salary_multiplier': 0.95},
            'Washington DC': {'cost_of_living': 1.3, 'salary_multiplier': 1.25},
            'Dallas': {'cost_of_living': 0.98, 'salary_multiplier': 0.98},
            'New York City': {'cost_of_living': 1.5, 'salary_multiplier': 1.4},
            'Philadelphia': {'cost_of_living': 1.1, 'salary_multiplier': 1.05},
            'Chicago': {'cost_of_living': 1.2, 'salary_multiplier': 1.15},
            'Charlotte': {'cost_of_living': 0.9, 'salary_multiplier': 0.9},
            'Miami': {'cost_of_living': 1.1, 'salary_multiplier': 1.0},
            'Baltimore': {'cost_of_living': 1.05, 'salary_multiplier': 1.0}
        }
        
        # Company quality indicators
        self.company_quality_indicators = {
            'fortune_500': ['Apple', 'Google', 'Microsoft', 'Amazon', 'Meta'],
            'growth_companies': ['Stripe', 'Airbnb', 'Uber', 'Lyft', 'DoorDash'],
            'established': ['IBM', 'Oracle', 'Cisco', 'Intel', 'Adobe']
        }
    
    def find_income_advancement_opportunities(self, user_id: int, 
                                           resume_text: str = None,
                                           target_locations: List[str] = None,
                                           min_salary_increase: float = None) -> Dict[str, Any]:
        """
        Find income advancement opportunities for a user
        
        Args:
            user_id: User ID
            resume_text: Resume text (optional, will fetch from profile if not provided)
            target_locations: Preferred locations
            min_salary_increase: Minimum salary increase percentage
            
        Returns:
            Dictionary with job opportunities and analysis
        """
        try:
            logger.info(f"Finding income advancement opportunities for user {user_id}")
            
            # Get user profile and current salary
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return {'error': 'User profile not found'}
            
            current_salary = user_profile.current_salary or 0
            if current_salary == 0:
                return {'error': 'Current salary not available'}
            
            # Get or analyze resume
            if not resume_text:
                resume_analysis = self._get_stored_resume_analysis(user_id)
                if not resume_analysis:
                    return {'error': 'Resume analysis not available'}
            else:
                resume_analysis = self.resume_parser.parse_resume(resume_text)
                self._store_resume_analysis(user_id, resume_analysis)
            
            # Set default locations if not provided
            if not target_locations:
                target_locations = self._get_user_preferred_locations(user_profile)
            
            # Set minimum salary increase
            if min_salary_increase is None:
                min_salary_increase = self.income_thresholds['minimum_increase']
            
            # Find job opportunities
            job_results = self.job_matcher.find_income_advancement_jobs(
                user_id=user_id,
                resume_text=resume_text or "",
                current_salary=current_salary,
                target_locations=target_locations
            )
            
            # Add income gap analysis
            income_analysis = self._analyze_income_gap(current_salary, job_results)
            
            # Add demographic comparisons
            demographic_analysis = self._analyze_demographic_comparisons(
                current_salary, resume_analysis, target_locations
            )
            
            # Generate personalized insights
            insights = self._generate_personalized_insights(
                job_results, income_analysis, demographic_analysis, user_profile
            )
            
            # Store search results
            self._store_job_search_results(user_id, job_results)
            
            return {
                'job_opportunities': job_results,
                'income_analysis': income_analysis,
                'demographic_analysis': demographic_analysis,
                'insights': insights,
                'search_metadata': {
                    'user_id': user_id,
                    'search_date': datetime.utcnow().isoformat(),
                    'target_locations': target_locations,
                    'min_salary_increase': min_salary_increase
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding income advancement opportunities: {str(e)}")
            raise
    
    def get_job_recommendations(self, user_id: int, 
                              recommendation_type: str = 'income_advancement') -> Dict[str, Any]:
        """
        Get job recommendations based on user profile and preferences
        
        Args:
            user_id: User ID
            recommendation_type: Type of recommendations ('income_advancement', 'career_growth', 'skill_development')
            
        Returns:
            Dictionary with job recommendations
        """
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return {'error': 'User profile not found'}
            
            # Get stored resume analysis
            resume_analysis = self._get_stored_resume_analysis(user_id)
            if not resume_analysis:
                return {'error': 'Resume analysis not available'}
            
            # Get stored job search results
            job_results = self._get_stored_job_search_results(user_id)
            if not job_results:
                return {'error': 'No job search results available'}
            
            # Filter recommendations based on type
            if recommendation_type == 'income_advancement':
                recommendations = self._filter_income_advancement_jobs(job_results)
            elif recommendation_type == 'career_growth':
                recommendations = self._filter_career_growth_jobs(job_results)
            elif recommendation_type == 'skill_development':
                recommendations = self._filter_skill_development_jobs(job_results)
            else:
                recommendations = job_results['job_recommendations']
            
            return {
                'recommendations': recommendations,
                'recommendation_type': recommendation_type,
                'total_opportunities': len(recommendations),
                'last_updated': job_results.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Error getting job recommendations: {str(e)}")
            raise
    
    def analyze_salary_potential(self, user_id: int, target_locations: List[str] = None) -> Dict[str, Any]:
        """
        Analyze salary potential across different locations and career paths
        
        Args:
            user_id: User ID
            target_locations: Locations to analyze
            
        Returns:
            Dictionary with salary potential analysis
        """
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return {'error': 'User profile not found'}
            
            current_salary = user_profile.current_salary or 0
            if current_salary == 0:
                return {'error': 'Current salary not available'}
            
            # Get resume analysis
            resume_analysis = self._get_stored_resume_analysis(user_id)
            if not resume_analysis:
                return {'error': 'Resume analysis not available'}
            
            # Set default locations
            if not target_locations:
                target_locations = list(self.msa_salary_data.keys())
            
            # Analyze salary potential by location
            location_analysis = {}
            for location in target_locations:
                location_data = self.msa_salary_data.get(location, {})
                salary_multiplier = location_data.get('salary_multiplier', 1.0)
                cost_of_living = location_data.get('cost_of_living', 1.0)
                
                # Calculate adjusted salary potential
                adjusted_salary = current_salary * salary_multiplier
                purchasing_power = adjusted_salary / cost_of_living
                
                location_analysis[location] = {
                    'adjusted_salary': int(adjusted_salary),
                    'salary_increase': (adjusted_salary - current_salary) / current_salary,
                    'purchasing_power': int(purchasing_power),
                    'cost_of_living_factor': cost_of_living,
                    'recommendation': self._get_location_recommendation(
                        adjusted_salary, purchasing_power, current_salary
                    )
                }
            
            # Analyze career path potential
            career_path_analysis = self._analyze_career_path_potential(
                resume_analysis, current_salary
            )
            
            return {
                'current_salary': current_salary,
                'location_analysis': location_analysis,
                'career_path_analysis': career_path_analysis,
                'recommendations': self._generate_salary_potential_recommendations(
                    location_analysis, career_path_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing salary potential: {str(e)}")
            raise
    
    def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile from database"""
        try:
            return self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def _get_stored_resume_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get stored resume analysis from database"""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile and user_profile.resume_analysis:
                return json.loads(user_profile.resume_analysis)
            return None
        except Exception as e:
            logger.error(f"Error getting stored resume analysis: {str(e)}")
            return None
    
    def _store_resume_analysis(self, user_id: int, resume_analysis: Any) -> None:
        """Store resume analysis in database"""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile:
                user_profile.resume_analysis = json.dumps(
                    self.resume_parser.get_analysis_summary(resume_analysis)
                )
                self.db_session.commit()
        except Exception as e:
            logger.error(f"Error storing resume analysis: {str(e)}")
            self.db_session.rollback()
    
    def _get_user_preferred_locations(self, user_profile: UserProfile) -> List[str]:
        """Get user's preferred locations"""
        # This would typically come from user preferences
        # For now, return default target MSAs
        return list(self.msa_salary_data.keys())[:5]  # Top 5 locations
    
    def _analyze_income_gap(self, current_salary: int, job_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze income gap and improvement opportunities"""
        job_recommendations = job_results.get('job_recommendations', [])
        
        if not job_recommendations:
            return {'error': 'No job recommendations available'}
        
        # Calculate salary statistics
        salaries = []
        salary_increases = []
        
        for job in job_recommendations:
            salary_data = job.get('salary_range', {})
            if salary_data.get('midpoint'):
                salary = salary_data['midpoint']
                salaries.append(salary)
                salary_increases.append((salary - current_salary) / current_salary)
        
        if not salaries:
            return {'error': 'No salary data available'}
        
        # Calculate statistics
        avg_salary = np.mean(salaries)
        avg_increase = np.mean(salary_increases)
        max_increase = max(salary_increases)
        min_increase = min(salary_increases)
        
        # Categorize opportunities
        excellent_opportunities = len([inc for inc in salary_increases if inc >= self.income_thresholds['excellent_increase']])
        good_opportunities = len([inc for inc in salary_increases if inc >= self.income_thresholds['target_increase']])
        minimum_opportunities = len([inc for inc in salary_increases if inc >= self.income_thresholds['minimum_increase']])
        
        return {
            'current_salary': current_salary,
            'average_target_salary': int(avg_salary),
            'average_salary_increase': avg_increase,
            'maximum_salary_increase': max_increase,
            'minimum_salary_increase': min_increase,
            'opportunity_categories': {
                'excellent': excellent_opportunities,
                'good': good_opportunities,
                'minimum': minimum_opportunities
            },
            'income_gap_analysis': {
                'gap_to_average': avg_salary - current_salary,
                'gap_to_max': max(salaries) - current_salary,
                'improvement_potential': (avg_salary - current_salary) / current_salary
            }
        }
    
    def _analyze_demographic_comparisons(self, current_salary: int, 
                                       resume_analysis: Any, 
                                       target_locations: List[str]) -> Dict[str, Any]:
        """Analyze salary comparisons with demographic data"""
        # This would integrate with real demographic data sources
        # For now, provide simplified analysis
        
        field = resume_analysis.field_analysis.primary_field.value
        experience_level = resume_analysis.experience_analysis.level.value
        
        # Simplified demographic data (in production, use real data sources)
        demographic_data = {
            'field_averages': {
                'Data Analysis': 85000,
                'Software Development': 95000,
                'Project Management': 90000,
                'Marketing': 75000,
                'Finance': 80000,
                'Sales': 70000,
                'Operations': 75000,
                'HR': 65000
            },
            'experience_multipliers': {
                'Entry': 0.7,
                'Mid': 1.0,
                'Senior': 1.4
            }
        }
        
        field_average = demographic_data['field_averages'].get(field, 75000)
        experience_multiplier = demographic_data['experience_multipliers'].get(experience_level, 1.0)
        
        expected_salary = field_average * experience_multiplier
        
        return {
            'current_salary': current_salary,
            'expected_salary_for_field': int(expected_salary),
            'expected_salary_for_experience': int(expected_salary),
            'salary_percentile': self._calculate_salary_percentile(current_salary, field, experience_level),
            'field_comparison': {
                'field_average': field_average,
                'difference_from_average': current_salary - field_average,
                'percentage_of_average': current_salary / field_average
            },
            'location_adjustments': {
                location: self.msa_salary_data.get(location, {})
                for location in target_locations
            }
        }
    
    def _calculate_salary_percentile(self, salary: int, field: str, experience_level: str) -> float:
        """Calculate salary percentile (simplified)"""
        # This would use real salary distribution data
        # For now, provide rough estimates
        
        field_averages = {
            'Data Analysis': 85000,
            'Software Development': 95000,
            'Project Management': 90000,
            'Marketing': 75000,
            'Finance': 80000,
            'Sales': 70000,
            'Operations': 75000,
            'HR': 65000
        }
        
        field_avg = field_averages.get(field, 75000)
        
        if salary >= field_avg * 1.5:
            return 90.0
        elif salary >= field_avg * 1.25:
            return 75.0
        elif salary >= field_avg:
            return 50.0
        elif salary >= field_avg * 0.75:
            return 25.0
        else:
            return 10.0
    
    def _generate_personalized_insights(self, job_results: Dict[str, Any],
                                     income_analysis: Dict[str, Any],
                                     demographic_analysis: Dict[str, Any],
                                     user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate personalized insights based on analysis"""
        insights = []
        
        # Income gap insights
        if 'income_gap_analysis' in income_analysis:
            gap_analysis = income_analysis['income_gap_analysis']
            improvement_potential = gap_analysis['improvement_potential']
            
            if improvement_potential >= 0.3:
                insights.append({
                    'type': 'opportunity',
                    'title': 'High Income Improvement Potential',
                    'description': f'You have {improvement_potential*100:.1f}% salary improvement potential',
                    'priority': 'high'
                })
            elif improvement_potential >= 0.2:
                insights.append({
                    'type': 'opportunity',
                    'title': 'Good Income Improvement Potential',
                    'description': f'You have {improvement_potential*100:.1f}% salary improvement potential',
                    'priority': 'medium'
                })
        
        # Field comparison insights
        if 'field_comparison' in demographic_analysis:
            field_comp = demographic_analysis['field_comparison']
            percentage_of_average = field_comp['percentage_of_average']
            
            if percentage_of_average < 0.8:
                insights.append({
                    'type': 'warning',
                    'title': 'Below Market Compensation',
                    'description': f'Your salary is {((1-percentage_of_average)*100):.1f}% below field average',
                    'priority': 'high'
                })
            elif percentage_of_average > 1.2:
                insights.append({
                    'type': 'positive',
                    'title': 'Above Market Compensation',
                    'description': f'Your salary is {((percentage_of_average-1)*100):.1f}% above field average',
                    'priority': 'low'
                })
        
        # Job opportunity insights
        job_recommendations = job_results.get('job_recommendations', [])
        if job_recommendations:
            remote_opportunities = len([job for job in job_recommendations if job.get('remote_work')])
            if remote_opportunities > 0:
                insights.append({
                    'type': 'opportunity',
                    'title': 'Remote Work Opportunities',
                    'description': f'Found {remote_opportunities} remote opportunities to expand your reach',
                    'priority': 'medium'
                })
        
        return insights
    
    def _store_job_search_results(self, user_id: int, job_results: Dict[str, Any]) -> None:
        """Store job search results in database"""
        try:
            # This would store in a dedicated job search results table
            # For now, store in user profile as JSON
            user_profile = self._get_user_profile(user_id)
            if user_profile:
                user_profile.job_search_results = json.dumps({
                    'last_search': datetime.utcnow().isoformat(),
                    'total_opportunities': len(job_results.get('job_recommendations', [])),
                    'search_summary': job_results.get('search_statistics', {})
                })
                self.db_session.commit()
        except Exception as e:
            logger.error(f"Error storing job search results: {str(e)}")
            self.db_session.rollback()
    
    def _get_stored_job_search_results(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get stored job search results from database"""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile and user_profile.job_search_results:
                return json.loads(user_profile.job_search_results)
            return None
        except Exception as e:
            logger.error(f"Error getting stored job search results: {str(e)}")
            return None
    
    def _filter_income_advancement_jobs(self, job_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter jobs for income advancement focus"""
        job_recommendations = job_results.get('job_recommendations', [])
        
        # Filter by salary improvement score
        return [
            job for job in job_recommendations
            if job.get('score_breakdown', {}).get('salary_improvement', 0) >= 0.7
        ]
    
    def _filter_career_growth_jobs(self, job_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter jobs for career growth focus"""
        job_recommendations = job_results.get('job_recommendations', [])
        
        # Filter by career progression score
        return [
            job for job in job_recommendations
            if job.get('score_breakdown', {}).get('career_progression', 0) >= 0.8
        ]
    
    def _filter_skill_development_jobs(self, job_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter jobs for skill development focus"""
        job_recommendations = job_results.get('job_recommendations', [])
        
        # Filter by skills alignment score
        return [
            job for job in job_recommendations
            if job.get('score_breakdown', {}).get('skills_match', 0) >= 0.6
        ]
    
    def _analyze_career_path_potential(self, resume_analysis: Any, current_salary: int) -> Dict[str, Any]:
        """Analyze career path potential"""
        field = resume_analysis.field_analysis.primary_field.value
        experience_level = resume_analysis.experience_analysis.level.value
        
        # Simplified career path analysis
        career_paths = {
            'Data Analysis': {
                'next_level': 'Senior Data Analyst',
                'salary_multiplier': 1.3,
                'time_to_next': '2-3 years'
            },
            'Software Development': {
                'next_level': 'Senior Software Engineer',
                'salary_multiplier': 1.4,
                'time_to_next': '2-3 years'
            },
            'Project Management': {
                'next_level': 'Senior Project Manager',
                'salary_multiplier': 1.35,
                'time_to_next': '2-3 years'
            }
        }
        
        path_info = career_paths.get(field, {})
        next_level_salary = int(current_salary * path_info.get('salary_multiplier', 1.2))
        
        return {
            'current_field': field,
            'current_level': experience_level,
            'next_level': path_info.get('next_level', 'Senior Position'),
            'next_level_salary': next_level_salary,
            'salary_increase_potential': (next_level_salary - current_salary) / current_salary,
            'time_to_next_level': path_info.get('time_to_next', '2-3 years')
        }
    
    def _get_location_recommendation(self, adjusted_salary: float, 
                                   purchasing_power: float, 
                                   current_salary: float) -> str:
        """Get location-specific recommendation"""
        salary_increase = (adjusted_salary - current_salary) / current_salary
        
        if salary_increase >= 0.3 and purchasing_power >= current_salary * 0.9:
            return "Excellent opportunity - high salary increase with good purchasing power"
        elif salary_increase >= 0.2:
            return "Good opportunity - significant salary increase"
        elif salary_increase >= 0.1:
            return "Moderate opportunity - some salary increase"
        else:
            return "Limited opportunity - consider other locations"
    
    def _generate_salary_potential_recommendations(self, location_analysis: Dict[str, Any],
                                                 career_path_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate salary potential recommendations"""
        recommendations = []
        
        # Location recommendations
        best_locations = sorted(
            location_analysis.items(),
            key=lambda x: x[1]['salary_increase'],
            reverse=True
        )[:3]
        
        for location, data in best_locations:
            recommendations.append({
                'type': 'location',
                'title': f'Top Location: {location}',
                'description': f'Potential {data["salary_increase"]*100:.1f}% salary increase',
                'priority': 'high' if data['salary_increase'] >= 0.2 else 'medium'
            })
        
        # Career path recommendations
        if career_path_analysis:
            path_data = career_path_analysis
            recommendations.append({
                'type': 'career_path',
                'title': f'Career Advancement: {path_data["next_level"]}',
                'description': f'Potential {path_data["salary_increase_potential"]*100:.1f}% increase in {path_data["time_to_next_level"]}',
                'priority': 'high'
            })
        
        return recommendations 