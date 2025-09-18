#!/usr/bin/env python3
"""
Mingus Integration Module
Connects referral-gated job recommendations with existing Mingus features
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.referral_models import ReferralSystem
from utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine

logger = logging.getLogger(__name__)

class MingusIntegrationManager:
    """Manages integration between referral system and existing Mingus features"""
    
    def __init__(self):
        self.referral_system = ReferralSystem()
        self.job_engine = MingusJobRecommendationEngine()
        self.user_profiles_db = 'user_profiles.db'
        self.app_db = 'app.db'
    
    def integrate_with_financial_planning(self, user_id: str, job_recommendations: List[Dict]) -> Dict:
        """Integrate job recommendations with financial planning features"""
        try:
            # Get user's financial profile
            financial_profile = self._get_user_financial_profile(user_id)
            if not financial_profile:
                return {'success': False, 'error': 'Financial profile not found'}
            
            # Calculate potential financial impact
            current_salary = financial_profile.get('annual_income', 0)
            potential_increases = []
            
            for job in job_recommendations:
                if job.get('salary_median') and job.get('salary_increase_potential'):
                    potential_salary = job['salary_median']
                    increase_amount = potential_salary - current_salary
                    increase_percentage = (increase_amount / current_salary * 100) if current_salary > 0 else 0
                    
                    potential_increases.append({
                        'job_title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'current_salary': current_salary,
                        'potential_salary': potential_salary,
                        'increase_amount': increase_amount,
                        'increase_percentage': increase_percentage,
                        'monthly_increase': increase_amount / 12,
                        'annual_benefit': self._calculate_annual_benefit(increase_amount, financial_profile)
                    })
            
            # Sort by potential increase
            potential_increases.sort(key=lambda x: x['increase_amount'], reverse=True)
            
            # Generate financial recommendations
            financial_recommendations = self._generate_financial_recommendations(
                financial_profile, potential_increases
            )
            
            return {
                'success': True,
                'financial_impact': {
                    'current_salary': current_salary,
                    'potential_increases': potential_increases[:5],  # Top 5
                    'recommendations': financial_recommendations,
                    'total_potential_increase': sum(inc['increase_amount'] for inc in potential_increases[:3]) / 3
                }
            }
            
        except Exception as e:
            logger.error(f"Error integrating with financial planning: {e}")
            return {'success': False, 'error': 'Integration failed'}
    
    def integrate_with_goal_setting(self, user_id: str, job_recommendations: List[Dict]) -> Dict:
        """Integrate job recommendations with goal-setting functionality"""
        try:
            # Get user's current goals
            user_goals = self._get_user_goals(user_id)
            
            # Analyze how job recommendations align with goals
            goal_alignment = []
            
            for goal in user_goals:
                if goal['category'] == 'career' or goal['category'] == 'financial':
                    aligned_jobs = self._find_goal_aligned_jobs(goal, job_recommendations)
                    goal_alignment.append({
                        'goal_id': goal['id'],
                        'goal_title': goal['title'],
                        'goal_category': goal['category'],
                        'aligned_jobs': aligned_jobs,
                        'alignment_score': len(aligned_jobs) / len(job_recommendations) if job_recommendations else 0
                    })
            
            # Generate goal-based recommendations
            goal_recommendations = self._generate_goal_recommendations(goal_alignment)
            
            return {
                'success': True,
                'goal_integration': {
                    'user_goals': user_goals,
                    'goal_alignment': goal_alignment,
                    'recommendations': goal_recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"Error integrating with goal setting: {e}")
            return {'success': False, 'error': 'Goal integration failed'}
    
    def track_feature_unlock_analytics(self, user_id: str, unlock_method: str) -> Dict:
        """Track analytics for feature unlock events"""
        try:
            # Get user's referral progress
            progress = self.referral_system.get_referral_progress(user_id)
            if not progress['success']:
                return {'success': False, 'error': 'Failed to get referral progress'}
            
            # Track unlock event
            analytics_data = {
                'user_id': user_id,
                'unlock_method': unlock_method,
                'unlock_timestamp': datetime.now().isoformat(),
                'referral_count': progress['progress']['successful_referrals'],
                'total_referrals': progress['progress']['total_referrals'],
                'time_to_unlock': self._calculate_time_to_unlock(user_id),
                'feature_accessed': 'job_recommendations'
            }
            
            # Save to analytics database
            self._save_analytics_event('feature_unlock', analytics_data)
            
            # Update user engagement metrics
            self._update_engagement_metrics(user_id, 'feature_unlock')
            
            return {'success': True, 'analytics': analytics_data}
            
        except Exception as e:
            logger.error(f"Error tracking unlock analytics: {e}")
            return {'success': False, 'error': 'Analytics tracking failed'}
    
    def generate_career_insights(self, user_id: str, job_recommendations: List[Dict]) -> Dict:
        """Generate career insights based on job recommendations"""
        try:
            # Analyze job market trends
            market_analysis = self._analyze_market_trends(job_recommendations)
            
            # Generate skill gap analysis
            skill_gaps = self._analyze_skill_gaps(user_id, job_recommendations)
            
            # Calculate career progression potential
            career_progression = self._analyze_career_progression(job_recommendations)
            
            # Generate personalized insights
            insights = {
                'market_analysis': market_analysis,
                'skill_gaps': skill_gaps,
                'career_progression': career_progression,
                'recommendations': self._generate_career_recommendations(
                    market_analysis, skill_gaps, career_progression
                )
            }
            
            return {'success': True, 'insights': insights}
            
        except Exception as e:
            logger.error(f"Error generating career insights: {e}")
            return {'success': False, 'error': 'Insights generation failed'}
    
    def _get_user_financial_profile(self, user_id: str) -> Optional[Dict]:
        """Get user's financial profile from existing database"""
        try:
            conn = sqlite3.connect(self.user_profiles_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT financial_info FROM user_profiles WHERE email = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting financial profile: {e}")
            return None
    
    def _get_user_goals(self, user_id: str) -> List[Dict]:
        """Get user's goals from existing database"""
        try:
            conn = sqlite3.connect(self.user_profiles_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT goals FROM user_profiles WHERE email = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                goals_data = json.loads(result[0])
                return goals_data.get('goals', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting user goals: {e}")
            return []
    
    def _calculate_annual_benefit(self, salary_increase: float, financial_profile: Dict) -> Dict:
        """Calculate annual financial benefit of salary increase"""
        try:
            # Calculate tax impact (simplified)
            tax_rate = 0.25  # Simplified tax rate
            after_tax_increase = salary_increase * (1 - tax_rate)
            
            # Calculate impact on savings goals
            current_savings_goal = financial_profile.get('monthly_savings_goal', 0) * 12
            new_savings_goal = current_savings_goal + (after_tax_increase * 0.3)  # Assume 30% goes to savings
            
            # Calculate debt payoff acceleration
            current_debt = financial_profile.get('student_loans', 0) + financial_profile.get('credit_card_debt', 0)
            debt_payoff_time = self._calculate_debt_payoff_time(current_debt, after_tax_increase)
            
            return {
                'after_tax_increase': after_tax_increase,
                'monthly_benefit': after_tax_increase / 12,
                'savings_impact': {
                    'current_goal': current_savings_goal,
                    'new_goal': new_savings_goal,
                    'additional_savings': new_savings_goal - current_savings_goal
                },
                'debt_payoff': {
                    'current_debt': current_debt,
                    'payoff_time_months': debt_payoff_time,
                    'interest_savings': self._calculate_interest_savings(current_debt, debt_payoff_time)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating annual benefit: {e}")
            return {}
    
    def _calculate_debt_payoff_time(self, debt_amount: float, additional_payment: float) -> int:
        """Calculate debt payoff time with additional payment"""
        if debt_amount <= 0 or additional_payment <= 0:
            return 0
        
        # Simplified calculation (assumes 5% interest rate)
        interest_rate = 0.05
        monthly_interest = interest_rate / 12
        monthly_payment = additional_payment / 12
        
        # Calculate payoff time using loan formula
        if monthly_payment > debt_amount * monthly_interest:
            months = -1 * (1 / monthly_interest) * (1 - (1 + monthly_interest) ** (-1)) * \
                    (debt_amount * monthly_interest / monthly_payment - 1)
            return max(1, int(months))
        
        return 999  # Will never pay off at this rate
    
    def _calculate_interest_savings(self, debt_amount: float, payoff_time_months: int) -> float:
        """Calculate interest savings from faster payoff"""
        if payoff_time_months <= 0:
            return 0
        
        # Simplified calculation
        interest_rate = 0.05
        monthly_interest = interest_rate / 12
        
        # Calculate total interest paid
        total_interest = debt_amount * monthly_interest * payoff_time_months
        return max(0, total_interest)
    
    def _generate_financial_recommendations(self, financial_profile: Dict, potential_increases: List[Dict]) -> List[Dict]:
        """Generate financial recommendations based on potential salary increases"""
        recommendations = []
        
        if not potential_increases:
            return recommendations
        
        avg_increase = sum(inc['increase_amount'] for inc in potential_increases) / len(potential_increases)
        
        # Emergency fund recommendation
        current_savings = financial_profile.get('current_savings', 0)
        monthly_expenses = sum([
            financial_profile.get('rent', 0),
            financial_profile.get('car_payment', 0),
            financial_profile.get('insurance', 0),
            financial_profile.get('groceries', 0),
            financial_profile.get('utilities', 0)
        ])
        
        emergency_fund_goal = monthly_expenses * 6
        
        if current_savings < emergency_fund_goal:
            recommendations.append({
                'category': 'emergency_fund',
                'title': 'Build Emergency Fund with New Income',
                'description': f'With a ${avg_increase:,.0f} salary increase, you could build your emergency fund to ${emergency_fund_goal:,.0f} in {(emergency_fund_goal - current_savings) / (avg_increase * 0.3):.1f} months',
                'priority': 'high',
                'action': 'Set aside 30% of salary increase for emergency fund'
            })
        
        # Debt payoff recommendation
        total_debt = financial_profile.get('student_loans', 0) + financial_profile.get('credit_card_debt', 0)
        if total_debt > 0:
            recommendations.append({
                'category': 'debt_payoff',
                'title': 'Accelerate Debt Payoff',
                'description': f'Use 40% of your salary increase (${avg_increase * 0.4:,.0f}) to pay off debt faster',
                'priority': 'high',
                'action': 'Increase debt payments by 40% of salary increase'
            })
        
        # Investment recommendation
        recommendations.append({
            'category': 'investment',
            'title': 'Increase Retirement Contributions',
            'description': f'Consider increasing your 401(k) contribution by ${avg_increase * 0.2:,.0f} annually',
            'priority': 'medium',
            'action': 'Increase 401(k) contribution by 20% of salary increase'
        })
        
        return recommendations
    
    def _find_goal_aligned_jobs(self, goal: Dict, job_recommendations: List[Dict]) -> List[Dict]:
        """Find jobs that align with user's goals"""
        aligned_jobs = []
        
        for job in job_recommendations:
            alignment_score = 0
            
            # Check salary alignment
            if goal.get('target_salary') and job.get('salary_median'):
                if job['salary_median'] >= goal['target_salary']:
                    alignment_score += 0.4
            
            # Check location alignment
            if goal.get('preferred_location') and job.get('location'):
                if goal['preferred_location'].lower() in job['location'].lower():
                    alignment_score += 0.3
            
            # Check remote work alignment
            if goal.get('remote_work') and job.get('remote_friendly'):
                alignment_score += 0.3
            
            if alignment_score > 0.5:
                aligned_jobs.append({
                    'job_id': job.get('job_id'),
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'alignment_score': alignment_score
                })
        
        return aligned_jobs
    
    def _generate_goal_recommendations(self, goal_alignment: List[Dict]) -> List[Dict]:
        """Generate recommendations based on goal alignment"""
        recommendations = []
        
        for alignment in goal_alignment:
            if alignment['alignment_score'] > 0.7:
                recommendations.append({
                    'goal_id': alignment['goal_id'],
                    'title': f"High Alignment with '{alignment['goal_title']}'",
                    'description': f"Found {len(alignment['aligned_jobs'])} jobs that strongly align with this goal",
                    'priority': 'high',
                    'action': 'Focus on these high-alignment opportunities'
                })
            elif alignment['alignment_score'] < 0.3:
                recommendations.append({
                    'goal_id': alignment['goal_id'],
                    'title': f"Low Alignment with '{alignment['goal_title']}'",
                    'description': 'Consider adjusting your job search criteria to better match this goal',
                    'priority': 'medium',
                    'action': 'Review and refine job search parameters'
                })
        
        return recommendations
    
    def _analyze_market_trends(self, job_recommendations: List[Dict]) -> Dict:
        """Analyze job market trends from recommendations"""
        if not job_recommendations:
            return {}
        
        # Analyze salary trends
        salaries = [job.get('salary_median', 0) for job in job_recommendations if job.get('salary_median')]
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        
        # Analyze remote work trends
        remote_jobs = sum(1 for job in job_recommendations if job.get('remote_friendly'))
        remote_percentage = (remote_jobs / len(job_recommendations)) * 100
        
        # Analyze company size trends
        company_sizes = {}
        for job in job_recommendations:
            size = job.get('company_size', 'Unknown')
            company_sizes[size] = company_sizes.get(size, 0) + 1
        
        return {
            'average_salary': avg_salary,
            'salary_range': {
                'min': min(salaries) if salaries else 0,
                'max': max(salaries) if salaries else 0
            },
            'remote_work_percentage': remote_percentage,
            'company_size_distribution': company_sizes,
            'total_opportunities': len(job_recommendations)
        }
    
    def _analyze_skill_gaps(self, user_id: str, job_recommendations: List[Dict]) -> Dict:
        """Analyze skill gaps based on job requirements"""
        # This would integrate with existing skill assessment
        # For now, return a simplified analysis
        
        common_skills = []
        for job in job_recommendations:
            if 'requirements' in job:
                common_skills.extend(job['requirements'])
        
        # Count skill frequency
        skill_counts = {}
        for skill in common_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Get top required skills
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_required_skills': top_skills,
            'skill_demand': len(common_skills),
            'recommendations': [
                f"Focus on developing {skill[0]}" for skill in top_skills[:3]
            ]
        }
    
    def _analyze_career_progression(self, job_recommendations: List[Dict]) -> Dict:
        """Analyze career progression potential"""
        if not job_recommendations:
            return {}
        
        # Analyze experience level distribution
        experience_levels = {}
        for job in job_recommendations:
            level = job.get('experience_level', 'Unknown')
            experience_levels[level] = experience_levels.get(level, 0) + 1
        
        # Analyze growth potential
        growth_scores = [job.get('growth_score', 0) for job in job_recommendations if job.get('growth_score')]
        avg_growth_score = sum(growth_scores) / len(growth_scores) if growth_scores else 0
        
        return {
            'experience_level_distribution': experience_levels,
            'average_growth_score': avg_growth_score,
            'progression_opportunities': len([j for j in job_recommendations if j.get('career_advancement_score', 0) > 0.7])
        }
    
    def _generate_career_recommendations(self, market_analysis: Dict, skill_gaps: Dict, career_progression: Dict) -> List[Dict]:
        """Generate career recommendations based on analysis"""
        recommendations = []
        
        # Market-based recommendations
        if market_analysis.get('remote_work_percentage', 0) > 50:
            recommendations.append({
                'category': 'market_trends',
                'title': 'Remote Work Opportunities',
                'description': f"{market_analysis['remote_work_percentage']:.0f}% of opportunities are remote-friendly",
                'priority': 'medium',
                'action': 'Consider remote work preferences in your search'
            })
        
        # Skill-based recommendations
        if skill_gaps.get('top_required_skills'):
            top_skill = skill_gaps['top_required_skills'][0]
            recommendations.append({
                'category': 'skill_development',
                'title': 'High-Demand Skill',
                'description': f"{top_skill[0]} is the most frequently required skill",
                'priority': 'high',
                'action': f'Focus on developing {top_skill[0]} skills'
            })
        
        # Career progression recommendations
        if career_progression.get('progression_opportunities', 0) > 0:
            recommendations.append({
                'category': 'career_growth',
                'title': 'Growth Opportunities Available',
                'description': f"Found {career_progression['progression_opportunities']} high-growth opportunities",
                'priority': 'high',
                'action': 'Prioritize companies with strong growth potential'
            })
        
        return recommendations
    
    def _calculate_time_to_unlock(self, user_id: str) -> Optional[str]:
        """Calculate time taken to unlock feature"""
        try:
            conn = sqlite3.connect(self.referral_system.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT created_at, unlock_date FROM users 
                WHERE user_id = ? AND unlock_date IS NOT NULL
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                created_at = datetime.fromisoformat(result[0])
                unlock_date = datetime.fromisoformat(result[1])
                time_diff = unlock_date - created_at
                return str(time_diff)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating time to unlock: {e}")
            return None
    
    def _save_analytics_event(self, event_type: str, data: Dict):
        """Save analytics event to database"""
        try:
            conn = sqlite3.connect(self.app_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO analytics_events (event_type, data)
                VALUES (?, ?)
            ''', (event_type, json.dumps(data)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving analytics event: {e}")
    
    def _update_engagement_metrics(self, user_id: str, event_type: str):
        """Update user engagement metrics"""
        try:
            conn = sqlite3.connect(self.app_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_engagement (
                    user_id TEXT PRIMARY KEY,
                    total_events INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    feature_unlocks INTEGER DEFAULT 0,
                    referral_activity INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_engagement 
                (user_id, total_events, last_activity, feature_unlocks, referral_activity)
                VALUES (
                    ?, 
                    COALESCE((SELECT total_events FROM user_engagement WHERE user_id = ?), 0) + 1,
                    CURRENT_TIMESTAMP,
                    CASE WHEN ? = 'feature_unlock' THEN 
                        COALESCE((SELECT feature_unlocks FROM user_engagement WHERE user_id = ?), 0) + 1
                    ELSE COALESCE((SELECT feature_unlocks FROM user_engagement WHERE user_id = ?), 0) END,
                    CASE WHEN ? LIKE 'referral_%' THEN 
                        COALESCE((SELECT referral_activity FROM user_engagement WHERE user_id = ?), 0) + 1
                    ELSE COALESCE((SELECT referral_activity FROM user_engagement WHERE user_id = ?), 0) END
                )
            ''', (user_id, user_id, event_type, user_id, user_id, event_type, user_id, user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating engagement metrics: {e}")
