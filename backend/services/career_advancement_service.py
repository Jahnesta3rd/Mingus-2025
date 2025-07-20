"""
Career Advancement Service
Integrates job selection algorithm with Mingus application infrastructure
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json

from ..ml.models.job_selection_algorithm import (
    JobSelectionAlgorithm, CareerAdvancementStrategy, CareerTier
)
from ..ml.models.intelligent_job_matcher import IntelligentJobMatcher
from ..ml.models.resume_parser import AdvancedResumeParser
from ..models.user import User
from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class CareerAdvancementService:
    """
    Service for career advancement strategy and job selection
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.job_selection_algorithm = JobSelectionAlgorithm()
        self.job_matcher = IntelligentJobMatcher()
        self.resume_parser = AdvancedResumeParser()
        
        # Career advancement tracking
        self.advancement_history = {}
        
    def generate_career_advancement_strategy(self, user_id: int, 
                                           resume_text: str = None,
                                           target_locations: List[str] = None,
                                           risk_preference: str = 'balanced') -> Dict[str, Any]:
        """
        Generate comprehensive career advancement strategy with 3 opportunities
        
        Args:
            user_id: User ID
            resume_text: Resume text (optional, will fetch from profile if not provided)
            target_locations: Preferred locations
            risk_preference: Risk preference ('conservative', 'balanced', 'aggressive')
            
        Returns:
            Dictionary with career advancement strategy
        """
        try:
            logger.info(f"Generating career advancement strategy for user {user_id}")
            
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
            
            # Find job opportunities
            job_results = self.job_matcher.find_income_advancement_jobs(
                user_id=user_id,
                resume_text=resume_text or "",
                current_salary=current_salary,
                target_locations=target_locations
            )
            
            if 'error' in job_results:
                return job_results
            
            # Extract scored jobs
            job_recommendations = job_results.get('job_recommendations', [])
            if not job_recommendations:
                return {'error': 'No job opportunities found'}
            
            # Convert to JobScore objects
            scored_jobs = self._convert_to_job_scores(job_recommendations)
            
            # Create search parameters
            search_params = self._create_search_parameters(
                current_salary, resume_analysis, target_locations
            )
            
            # Generate career advancement strategy
            strategy = self.job_selection_algorithm.select_career_advancement_strategy(
                scored_jobs, search_params, resume_analysis
            )
            
            # Adjust strategy based on risk preference
            adjusted_strategy = self._adjust_strategy_for_risk_preference(
                strategy, risk_preference
            )
            
            # Generate additional insights
            insights = self._generate_career_insights(adjusted_strategy, resume_analysis)
            
            # Store strategy
            self._store_career_strategy(user_id, adjusted_strategy)
            
            return {
                'career_strategy': self._format_career_strategy(adjusted_strategy),
                'insights': insights,
                'risk_analysis': self._analyze_risk_distribution(adjusted_strategy),
                'timeline_guidance': self._generate_timeline_guidance(adjusted_strategy),
                'success_metrics': self._calculate_success_metrics(adjusted_strategy),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating career advancement strategy: {str(e)}")
            raise
    
    def get_career_strategy(self, user_id: int) -> Dict[str, Any]:
        """
        Get stored career advancement strategy
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with career strategy
        """
        try:
            strategy_data = self._get_stored_career_strategy(user_id)
            if not strategy_data:
                return {'error': 'No career strategy found'}
            
            return {
                'success': True,
                'data': strategy_data
            }
            
        except Exception as e:
            logger.error(f"Error getting career strategy: {str(e)}")
            raise
    
    def update_career_strategy(self, user_id: int, 
                             strategy_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update career advancement strategy based on user feedback
        
        Args:
            user_id: User ID
            strategy_updates: Updates to apply to strategy
            
        Returns:
            Updated strategy
        """
        try:
            current_strategy = self._get_stored_career_strategy(user_id)
            if not current_strategy:
                return {'error': 'No existing strategy to update'}
            
            # Apply updates
            updated_strategy = self._apply_strategy_updates(current_strategy, strategy_updates)
            
            # Store updated strategy
            self._store_career_strategy(user_id, updated_strategy)
            
            return {
                'success': True,
                'data': updated_strategy
            }
            
        except Exception as e:
            logger.error(f"Error updating career strategy: {str(e)}")
            raise
    
    def analyze_strategy_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze progress on career advancement strategy
        
        Args:
            user_id: User ID
            
        Returns:
            Progress analysis
        """
        try:
            strategy = self._get_stored_career_strategy(user_id)
            if not strategy:
                return {'error': 'No career strategy found'}
            
            # Analyze progress for each tier
            progress_analysis = {
                'conservative': self._analyze_tier_progress(strategy, 'conservative'),
                'optimal': self._analyze_tier_progress(strategy, 'optimal'),
                'stretch': self._analyze_tier_progress(strategy, 'stretch')
            }
            
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress(progress_analysis)
            
            # Generate recommendations
            recommendations = self._generate_progress_recommendations(progress_analysis)
            
            return {
                'progress_analysis': progress_analysis,
                'overall_progress': overall_progress,
                'recommendations': recommendations,
                'next_steps': self._generate_next_steps(progress_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strategy progress: {str(e)}")
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
        return ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
    
    def _convert_to_job_scores(self, job_recommendations: List[Dict[str, Any]]) -> List[Any]:
        """Convert job recommendations to JobScore objects"""
        from ..ml.models.intelligent_job_matcher import JobScore, JobPosting, SalaryRange, CompanyTier, JobSource
        
        scored_jobs = []
        
        for job_data in job_recommendations:
            try:
                # Create JobPosting object
                job = JobPosting(
                    id=job_data.get('id', ''),
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    location=job_data.get('location', ''),
                    salary_range=SalaryRange(
                        min_salary=job_data.get('salary_range', {}).get('min', 0),
                        max_salary=job_data.get('salary_range', {}).get('max', 0)
                    ) if job_data.get('salary_range') else None,
                    description=job_data.get('description', ''),
                    requirements=job_data.get('requirements', []),
                    skills=job_data.get('skills', []),
                    experience_level=job_data.get('experience_level', ''),
                    field=job_data.get('field', ''),
                    industry=job_data.get('industry', ''),
                    remote_work=job_data.get('remote_work', False),
                    source=JobSource(job_data.get('source', 'linkedin').upper()),
                    company_tier=CompanyTier(job_data.get('company_tier', 'unknown')),
                    glassdoor_rating=job_data.get('glassdoor_rating')
                )
                
                # Create JobScore object
                score_breakdown = job_data.get('score_breakdown', {})
                job_score = JobScore(
                    job=job,
                    overall_score=job_data.get('overall_score', 0.0),
                    salary_improvement_score=score_breakdown.get('salary_improvement', 0.0),
                    skills_alignment_score=score_breakdown.get('skills_match', 0.0),
                    career_progression_score=score_breakdown.get('career_progression', 0.0),
                    company_stability_score=score_breakdown.get('company_quality', 0.0),
                    location_compatibility_score=score_breakdown.get('location_fit', 0.0),
                    growth_potential_score=score_breakdown.get('growth_potential', 0.0),
                    score_breakdown=score_breakdown,
                    recommendations=job_data.get('recommendations', []),
                    risk_factors=job_data.get('risk_factors', [])
                )
                
                scored_jobs.append(job_score)
                
            except Exception as e:
                logger.error(f"Error converting job recommendation: {str(e)}")
                continue
        
        return scored_jobs
    
    def _create_search_parameters(self, current_salary: int, 
                                resume_analysis: Any, 
                                target_locations: List[str]) -> Any:
        """Create search parameters for job selection"""
        from ..ml.models.intelligent_job_matcher import SearchParameters
        from ..ml.models.resume_parser import FieldType, ExperienceLevel
        
        return SearchParameters(
            current_salary=current_salary,
            target_salary_min=int(current_salary * 1.15),  # 15% minimum increase
            primary_field=resume_analysis.field_analysis.primary_field,
            experience_level=resume_analysis.experience_analysis.level,
            skills=list(resume_analysis.skills_analysis.technical_skills.keys()) + 
                   list(resume_analysis.skills_analysis.business_skills.keys()),
            locations=target_locations,
            remote_preference=True,
            min_salary_increase=0.15
        )
    
    def _adjust_strategy_for_risk_preference(self, strategy: CareerAdvancementStrategy, 
                                           risk_preference: str) -> CareerAdvancementStrategy:
        """Adjust strategy based on user's risk preference"""
        if risk_preference == 'conservative':
            # Emphasize conservative opportunities
            strategy.strategy_summary['risk_distribution']['conservative'] = 'very_low'
            strategy.strategy_summary['risk_distribution']['optimal'] = 'low'
            strategy.strategy_summary['risk_distribution']['stretch'] = 'medium'
        elif risk_preference == 'aggressive':
            # Emphasize stretch opportunities
            strategy.strategy_summary['risk_distribution']['conservative'] = 'medium'
            strategy.strategy_summary['risk_distribution']['optimal'] = 'high'
            strategy.strategy_summary['risk_distribution']['stretch'] = 'very_high'
        
        return strategy
    
    def _generate_career_insights(self, strategy: CareerAdvancementStrategy, 
                                resume_analysis: Any) -> List[Dict[str, Any]]:
        """Generate career insights based on strategy"""
        insights = []
        
        # Salary progression insights
        salary_increases = [
            strategy.conservative_opportunity.income_impact.salary_increase_percentage,
            strategy.optimal_opportunity.income_impact.salary_increase_percentage,
            strategy.stretch_opportunity.income_impact.salary_increase_percentage
        ]
        
        avg_increase = sum(salary_increases) / len(salary_increases)
        
        insights.append({
            'type': 'salary_progression',
            'title': 'Salary Advancement Potential',
            'description': f'Average salary increase potential: {avg_increase*100:.1f}%',
            'details': {
                'conservative': f"{salary_increases[0]*100:.1f}%",
                'optimal': f"{salary_increases[1]*100:.1f}%",
                'stretch': f"{salary_increases[2]*100:.1f}%"
            }
        })
        
        # Skills development insights
        skill_gaps = []
        for opportunity in [strategy.conservative_opportunity, strategy.optimal_opportunity, strategy.stretch_opportunity]:
            skill_gaps.extend(opportunity.skill_gap_analysis.missing_critical_skills)
        
        if skill_gaps:
            unique_gaps = list(set(skill_gaps))
            insights.append({
                'type': 'skills_development',
                'title': 'Key Skills to Develop',
                'description': f'Focus on developing: {", ".join(unique_gaps[:3])}',
                'priority': 'high' if len(unique_gaps) > 2 else 'medium'
            })
        
        # Career trajectory insights
        field = resume_analysis.field_analysis.primary_field.value
        insights.append({
            'type': 'career_trajectory',
            'title': 'Career Advancement Path',
            'description': f'Clear progression path in {field} with multiple advancement levels',
            'timeline': '6-18 months for full progression'
        })
        
        return insights
    
    def _analyze_risk_distribution(self, strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Analyze risk distribution across opportunities"""
        return {
            'risk_levels': {
                'conservative': {
                    'level': 'low',
                    'success_probability': strategy.conservative_opportunity.application_strategy.success_probability,
                    'time_to_readiness': strategy.conservative_opportunity.skill_gap_analysis.timeline_to_readiness
                },
                'optimal': {
                    'level': 'medium',
                    'success_probability': strategy.optimal_opportunity.application_strategy.success_probability,
                    'time_to_readiness': strategy.optimal_opportunity.skill_gap_analysis.timeline_to_readiness
                },
                'stretch': {
                    'level': 'high',
                    'success_probability': strategy.stretch_opportunity.application_strategy.success_probability,
                    'time_to_readiness': strategy.stretch_opportunity.skill_gap_analysis.timeline_to_readiness
                }
            },
            'recommended_approach': 'Start with conservative, prepare for optimal, plan for stretch',
            'risk_mitigation': 'Maintain current position while pursuing opportunities'
        }
    
    def _generate_timeline_guidance(self, strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Generate timeline guidance for career advancement"""
        return {
            'immediate_actions': [
                f"Apply to {strategy.conservative_opportunity.job.company}",
                "Begin skill development for optimal opportunity",
                "Start networking for stretch opportunity"
            ],
            'week_1_4': [
                "Follow up on conservative application",
                "Enroll in recommended courses",
                "Connect with professionals at target companies"
            ],
            'month_2_3': [
                f"Apply to {strategy.optimal_opportunity.job.company}",
                "Complete skill development projects",
                "Attend industry events"
            ],
            'month_4_6': [
                f"Apply to {strategy.stretch_opportunity.job.company}",
                "Continue networking and relationship building",
                "Evaluate and adjust strategy"
            ]
        }
    
    def _calculate_success_metrics(self, strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Calculate success metrics for the strategy"""
        success_probabilities = [
            strategy.conservative_opportunity.application_strategy.success_probability,
            strategy.optimal_opportunity.application_strategy.success_probability,
            strategy.stretch_opportunity.application_strategy.success_probability
        ]
        
        salary_increases = [
            strategy.conservative_opportunity.income_impact.salary_increase_percentage,
            strategy.optimal_opportunity.income_impact.salary_increase_percentage,
            strategy.stretch_opportunity.income_impact.salary_increase_percentage
        ]
        
        return {
            'average_success_probability': sum(success_probabilities) / len(success_probabilities),
            'average_salary_increase': sum(salary_increases) / len(salary_increases),
            'total_opportunities': 3,
            'geographic_diversity': len(set([
                strategy.conservative_opportunity.job.location,
                strategy.optimal_opportunity.job.location,
                strategy.stretch_opportunity.job.location
            ])),
            'company_diversity': len(set([
                strategy.conservative_opportunity.job.company,
                strategy.optimal_opportunity.job.company,
                strategy.stretch_opportunity.job.company
            ]))
        }
    
    def _format_career_strategy(self, strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Format career strategy for API response"""
        return {
            'conservative_opportunity': self._format_opportunity(strategy.conservative_opportunity),
            'optimal_opportunity': self._format_opportunity(strategy.optimal_opportunity),
            'stretch_opportunity': self._format_opportunity(strategy.stretch_opportunity),
            'strategy_summary': strategy.strategy_summary,
            'timeline_recommendations': strategy.timeline_recommendations,
            'risk_mitigation_plan': strategy.risk_mitigation_plan,
            'generated_at': strategy.generated_at.isoformat()
        }
    
    def _format_opportunity(self, opportunity: Any) -> Dict[str, Any]:
        """Format individual opportunity for API response"""
        return {
            'tier': opportunity.tier.value,
            'job': {
                'title': opportunity.job.title,
                'company': opportunity.job.company,
                'location': opportunity.job.location,
                'salary_range': {
                    'min': opportunity.job.salary_range.min_salary if opportunity.job.salary_range else None,
                    'max': opportunity.job.salary_range.max_salary if opportunity.job.salary_range else None,
                    'midpoint': opportunity.job.salary_range.midpoint if opportunity.job.salary_range else None
                },
                'remote_work': opportunity.job.remote_work,
                'company_tier': opportunity.job.company_tier.value,
                'glassdoor_rating': opportunity.job.glassdoor_rating
            },
            'income_impact': {
                'salary_increase_percentage': opportunity.income_impact.salary_increase_percentage * 100,
                'current_percentile': opportunity.income_impact.current_percentile,
                'new_percentile': opportunity.income_impact.new_percentile,
                'percentile_improvement': opportunity.income_impact.percentile_improvement
            },
            'skill_gap_analysis': {
                'skills_match_percentage': opportunity.skill_gap_analysis.skills_match_percentage * 100,
                'missing_critical_skills': opportunity.skill_gap_analysis.missing_critical_skills,
                'learning_recommendations': opportunity.skill_gap_analysis.learning_recommendations,
                'timeline_to_readiness': opportunity.skill_gap_analysis.timeline_to_readiness
            },
            'application_strategy': {
                'strategy_type': opportunity.application_strategy.strategy_type.value,
                'recommended_approach': opportunity.application_strategy.recommended_approach,
                'timeline_to_application': opportunity.application_strategy.timeline_to_application,
                'preparation_steps': opportunity.application_strategy.preparation_steps,
                'success_probability': opportunity.application_strategy.success_probability,
                'risk_factors': opportunity.application_strategy.risk_factors,
                'mitigation_strategies': opportunity.application_strategy.mitigation_strategies
            },
            'selection_reasoning': opportunity.selection_reasoning,
            'alternative_options': opportunity.alternative_options,
            'backup_recommendations': opportunity.backup_recommendations
        }
    
    def _store_career_strategy(self, user_id: int, strategy: CareerAdvancementStrategy) -> None:
        """Store career strategy in database"""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile:
                user_profile.career_strategy = json.dumps(self._format_career_strategy(strategy))
                self.db_session.commit()
        except Exception as e:
            logger.error(f"Error storing career strategy: {str(e)}")
            self.db_session.rollback()
    
    def _get_stored_career_strategy(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get stored career strategy from database"""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile and user_profile.career_strategy:
                return json.loads(user_profile.career_strategy)
            return None
        except Exception as e:
            logger.error(f"Error getting stored career strategy: {str(e)}")
            return None
    
    def _apply_strategy_updates(self, current_strategy: Dict[str, Any], 
                              updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply updates to career strategy"""
        # Deep copy current strategy
        updated_strategy = json.loads(json.dumps(current_strategy))
        
        # Apply updates
        for key, value in updates.items():
            if key in updated_strategy:
                updated_strategy[key] = value
        
        return updated_strategy
    
    def _analyze_tier_progress(self, strategy: Dict[str, Any], tier: str) -> Dict[str, Any]:
        """Analyze progress for a specific tier"""
        opportunity = strategy.get(f'{tier}_opportunity', {})
        
        if not opportunity:
            return {'status': 'not_started', 'progress': 0}
        
        # Analyze based on application strategy
        app_strategy = opportunity.get('application_strategy', {})
        strategy_type = app_strategy.get('strategy_type', '')
        
        if strategy_type == 'immediate_apply':
            return {'status': 'ready_to_apply', 'progress': 90}
        elif strategy_type == 'upskill_first':
            return {'status': 'skill_development', 'progress': 60}
        elif strategy_type == 'networking_required':
            return {'status': 'networking', 'progress': 40}
        elif strategy_type == 'strategic_preparation':
            return {'status': 'preparation', 'progress': 30}
        else:
            return {'status': 'not_started', 'progress': 0}
    
    def _calculate_overall_progress(self, progress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall progress across all tiers"""
        total_progress = 0
        active_tiers = 0
        
        for tier, progress in progress_analysis.items():
            if progress['progress'] > 0:
                total_progress += progress['progress']
                active_tiers += 1
        
        if active_tiers == 0:
            return {'overall_progress': 0, 'status': 'not_started'}
        
        overall_progress = total_progress / active_tiers
        
        if overall_progress >= 80:
            status = 'excellent'
        elif overall_progress >= 60:
            status = 'good'
        elif overall_progress >= 40:
            status = 'fair'
        else:
            status = 'needs_improvement'
        
        return {
            'overall_progress': overall_progress,
            'status': status,
            'active_tiers': active_tiers
        }
    
    def _generate_progress_recommendations(self, progress_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on progress analysis"""
        recommendations = []
        
        for tier, progress in progress_analysis.items():
            if progress['progress'] < 50:
                recommendations.append({
                    'tier': tier,
                    'recommendation': f'Focus on {tier} opportunity - current progress: {progress["progress"]}%',
                    'priority': 'high' if tier == 'conservative' else 'medium'
                })
        
        return recommendations
    
    def _generate_next_steps(self, progress_analysis: Dict[str, Any]) -> List[str]:
        """Generate next steps based on progress analysis"""
        next_steps = []
        
        # Prioritize conservative tier
        conservative_progress = progress_analysis.get('conservative', {}).get('progress', 0)
        if conservative_progress < 80:
            next_steps.append("Apply to conservative opportunity immediately")
        
        # Focus on skill development for optimal
        optimal_progress = progress_analysis.get('optimal', {}).get('progress', 0)
        if optimal_progress < 60:
            next_steps.append("Continue skill development for optimal opportunity")
        
        # Build network for stretch
        stretch_progress = progress_analysis.get('stretch', {}).get('progress', 0)
        if stretch_progress < 40:
            next_steps.append("Build professional network for stretch opportunity")
        
        return next_steps 