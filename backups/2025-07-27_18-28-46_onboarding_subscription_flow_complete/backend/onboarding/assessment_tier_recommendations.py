#!/usr/bin/env python3
"""
Assessment-Based Tier Recommendations
Provides intelligent tier recommendations based on financial assessment scores
and user needs analysis, with personalized benefits and upgrade paths.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import defaultdict
import uuid

# Configure logging
logger = logging.getLogger(__name__)

class AssessmentTier(Enum):
    """Assessment-based tiers"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"

class AssessmentCategory(Enum):
    """Assessment categories"""
    FINANCIAL_LITERACY = "financial_literacy"
    INVESTMENT_KNOWLEDGE = "investment_knowledge"
    DEBT_MANAGEMENT = "debt_management"
    SAVINGS_BEHAVIOR = "savings_behavior"
    RETIREMENT_PLANNING = "retirement_planning"
    TAX_KNOWLEDGE = "tax_knowledge"
    INSURANCE_UNDERSTANDING = "insurance_understanding"
    ESTATE_PLANNING = "estate_planning"

class UserNeed(Enum):
    """User needs based on assessment"""
    BASIC_FINANCIAL_EDUCATION = "basic_financial_education"
    DEBT_REDUCTION = "debt_reduction"
    SAVINGS_ACCELERATION = "savings_acceleration"
    INVESTMENT_GUIDANCE = "investment_guidance"
    RETIREMENT_PLANNING = "retirement_planning"
    TAX_OPTIMIZATION = "tax_optimization"
    INSURANCE_PLANNING = "insurance_planning"
    COMPREHENSIVE_PLANNING = "comprehensive_planning"

@dataclass
class AssessmentScore:
    """Assessment score data"""
    user_id: str
    total_score: int
    category_scores: Dict[AssessmentCategory, int]
    assessment_date: datetime
    assessment_version: str
    completion_time_minutes: int
    confidence_level: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TierRecommendation:
    """Tier recommendation data"""
    recommendation_id: str
    user_id: str
    recommended_tier: AssessmentTier
    assessment_score: int
    confidence_score: float
    primary_needs: List[UserNeed]
    secondary_needs: List[UserNeed]
    tier_benefits: List[Dict[str, Any]]
    upgrade_path: List[AssessmentTier]
    estimated_value: float
    reasoning: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

@dataclass
class TierBenefit:
    """Tier benefit data"""
    benefit_id: str
    tier: AssessmentTier
    title: str
    description: str
    value_proposition: str
    relevance_score: float
    user_need_alignment: List[UserNeed]
    implementation_effort: str
    expected_impact: str

@dataclass
class AssessmentConfig:
    """Configuration for assessment-based recommendations"""
    score_thresholds: Dict[AssessmentTier, Tuple[int, int]] = None
    category_weights: Dict[AssessmentCategory, float] = None
    need_mapping: Dict[AssessmentCategory, List[UserNeed]] = None
    tier_benefits: Dict[AssessmentTier, List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.score_thresholds is None:
            self.score_thresholds = {
                AssessmentTier.BUDGET: (0, 16),
                AssessmentTier.MID_TIER: (17, 45),
                AssessmentTier.PROFESSIONAL: (46, 100)
            }
        
        if self.category_weights is None:
            self.category_weights = {
                AssessmentCategory.FINANCIAL_LITERACY: 0.15,
                AssessmentCategory.INVESTMENT_KNOWLEDGE: 0.20,
                AssessmentCategory.DEBT_MANAGEMENT: 0.15,
                AssessmentCategory.SAVINGS_BEHAVIOR: 0.15,
                AssessmentCategory.RETIREMENT_PLANNING: 0.15,
                AssessmentCategory.TAX_KNOWLEDGE: 0.10,
                AssessmentCategory.INSURANCE_UNDERSTANDING: 0.05,
                AssessmentCategory.ESTATE_PLANNING: 0.05
            }
        
        if self.need_mapping is None:
            self.need_mapping = {
                AssessmentCategory.FINANCIAL_LITERACY: [UserNeed.BASIC_FINANCIAL_EDUCATION],
                AssessmentCategory.INVESTMENT_KNOWLEDGE: [UserNeed.INVESTMENT_GUIDANCE],
                AssessmentCategory.DEBT_MANAGEMENT: [UserNeed.DEBT_REDUCTION],
                AssessmentCategory.SAVINGS_BEHAVIOR: [UserNeed.SAVINGS_ACCELERATION],
                AssessmentCategory.RETIREMENT_PLANNING: [UserNeed.RETIREMENT_PLANNING],
                AssessmentCategory.TAX_KNOWLEDGE: [UserNeed.TAX_OPTIMIZATION],
                AssessmentCategory.INSURANCE_UNDERSTANDING: [UserNeed.INSURANCE_PLANNING],
                AssessmentCategory.ESTATE_PLANNING: [UserNeed.COMPREHENSIVE_PLANNING]
            }
        
        if self.tier_benefits is None:
            self.tier_benefits = {
                AssessmentTier.BUDGET: [
                    {
                        'title': 'Basic Financial Education',
                        'description': 'Essential financial literacy resources and tools',
                        'value_proposition': 'Build a solid foundation for financial success',
                        'relevance_score': 0.9,
                        'user_need_alignment': [UserNeed.BASIC_FINANCIAL_EDUCATION],
                        'implementation_effort': 'low',
                        'expected_impact': 'immediate'
                    },
                    {
                        'title': 'Budget Tracking Tools',
                        'description': 'Simple budget creation and expense tracking',
                        'value_proposition': 'Take control of your spending and savings',
                        'relevance_score': 0.85,
                        'user_need_alignment': [UserNeed.SAVINGS_ACCELERATION],
                        'implementation_effort': 'low',
                        'expected_impact': 'immediate'
                    },
                    {
                        'title': 'Debt Management Basics',
                        'description': 'Fundamental debt reduction strategies',
                        'value_proposition': 'Start your journey to debt freedom',
                        'relevance_score': 0.8,
                        'user_need_alignment': [UserNeed.DEBT_REDUCTION],
                        'implementation_effort': 'medium',
                        'expected_impact': 'short_term'
                    }
                ],
                AssessmentTier.MID_TIER: [
                    {
                        'title': 'Advanced Financial Planning',
                        'description': 'Comprehensive financial planning tools and guidance',
                        'value_proposition': 'Create a roadmap for your financial future',
                        'relevance_score': 0.95,
                        'user_need_alignment': [UserNeed.COMPREHENSIVE_PLANNING],
                        'implementation_effort': 'medium',
                        'expected_impact': 'medium_term'
                    },
                    {
                        'title': 'Investment Portfolio Builder',
                        'description': 'Personalized investment recommendations and portfolio management',
                        'value_proposition': 'Grow your wealth with smart investment strategies',
                        'relevance_score': 0.9,
                        'user_need_alignment': [UserNeed.INVESTMENT_GUIDANCE],
                        'implementation_effort': 'medium',
                        'expected_impact': 'long_term'
                    },
                    {
                        'title': 'Retirement Planning Suite',
                        'description': 'Comprehensive retirement planning and optimization tools',
                        'value_proposition': 'Secure your financial future with expert planning',
                        'relevance_score': 0.88,
                        'user_need_alignment': [UserNeed.RETIREMENT_PLANNING],
                        'implementation_effort': 'medium',
                        'expected_impact': 'long_term'
                    },
                    {
                        'title': 'Tax Optimization Tools',
                        'description': 'Tax planning and optimization strategies',
                        'value_proposition': 'Maximize your tax savings and efficiency',
                        'relevance_score': 0.85,
                        'user_need_alignment': [UserNeed.TAX_OPTIMIZATION],
                        'implementation_effort': 'medium',
                        'expected_impact': 'annual'
                    }
                ],
                AssessmentTier.PROFESSIONAL: [
                    {
                        'title': 'Comprehensive Financial Advisory',
                        'description': 'Full-service financial advisory and planning',
                        'value_proposition': 'Expert guidance for complex financial situations',
                        'relevance_score': 0.98,
                        'user_need_alignment': [UserNeed.COMPREHENSIVE_PLANNING],
                        'implementation_effort': 'high',
                        'expected_impact': 'comprehensive'
                    },
                    {
                        'title': 'Advanced Investment Management',
                        'description': 'Sophisticated investment strategies and portfolio optimization',
                        'value_proposition': 'Professional-level investment management',
                        'relevance_score': 0.95,
                        'user_need_alignment': [UserNeed.INVESTMENT_GUIDANCE],
                        'implementation_effort': 'high',
                        'expected_impact': 'long_term'
                    },
                    {
                        'title': 'Estate Planning & Wealth Transfer',
                        'description': 'Comprehensive estate planning and wealth transfer strategies',
                        'value_proposition': 'Protect and transfer your wealth effectively',
                        'relevance_score': 0.92,
                        'user_need_alignment': [UserNeed.COMPREHENSIVE_PLANNING],
                        'implementation_effort': 'high',
                        'expected_impact': 'generational'
                    },
                    {
                        'title': 'Insurance Planning & Risk Management',
                        'description': 'Comprehensive insurance planning and risk assessment',
                        'value_proposition': 'Protect your family and assets with optimal coverage',
                        'relevance_score': 0.9,
                        'user_need_alignment': [UserNeed.INSURANCE_PLANNING],
                        'implementation_effort': 'high',
                        'expected_impact': 'ongoing'
                    },
                    {
                        'title': 'Tax Strategy & Optimization',
                        'description': 'Advanced tax planning and optimization strategies',
                        'value_proposition': 'Minimize taxes and maximize wealth preservation',
                        'relevance_score': 0.93,
                        'user_need_alignment': [UserNeed.TAX_OPTIMIZATION],
                        'implementation_effort': 'high',
                        'expected_impact': 'annual'
                    }
                ]
            }

class AssessmentTierRecommendations:
    """Assessment-based tier recommendation system"""
    
    def __init__(self, db, subscription_service, analytics_service, notification_service):
        self.db = db
        self.subscription_service = subscription_service
        self.analytics_service = analytics_service
        self.notification_service = notification_service
        self.config = AssessmentConfig()
        
        # Tier pricing and features
        self.tier_details = {
            AssessmentTier.BUDGET: {
                'name': 'Budget Tier',
                'price': 9.99,
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': [
                    'basic_financial_education',
                    'budget_tracking',
                    'debt_management_basics',
                    'savings_goals',
                    'financial_calculators'
                ],
                'target_audience': 'Financial beginners and those building basic money management skills',
                'value_proposition': 'Essential tools to build a solid financial foundation'
            },
            AssessmentTier.MID_TIER: {
                'name': 'Mid-Tier',
                'price': 24.99,
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': [
                    'advanced_financial_planning',
                    'investment_portfolio_builder',
                    'retirement_planning_suite',
                    'tax_optimization_tools',
                    'financial_advisor_access',
                    'customized_reports'
                ],
                'target_audience': 'Individuals with basic financial knowledge seeking comprehensive planning',
                'value_proposition': 'Comprehensive financial planning for growing wealth'
            },
            AssessmentTier.PROFESSIONAL: {
                'name': 'Professional Tier',
                'price': 49.99,
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': [
                    'comprehensive_financial_advisory',
                    'advanced_investment_management',
                    'estate_planning',
                    'insurance_planning',
                    'tax_strategy_optimization',
                    'dedicated_financial_advisor',
                    'priority_support',
                    'custom_planning_sessions'
                ],
                'target_audience': 'High-net-worth individuals and those with complex financial needs',
                'value_proposition': 'Professional-level financial advisory and comprehensive planning'
            }
        }
    
    def process_assessment_results(self, user_id: str, assessment_data: Dict[str, Any]) -> AssessmentScore:
        """Process assessment results and calculate scores"""
        try:
            # Calculate category scores
            category_scores = {}
            total_score = 0
            
            for category in AssessmentCategory:
                category_data = assessment_data.get(category.value, {})
                category_score = self._calculate_category_score(category, category_data)
                category_scores[category] = category_score
                total_score += category_score * self.config.category_weights[category]
            
            # Create assessment score object
            assessment_score = AssessmentScore(
                user_id=user_id,
                total_score=int(total_score),
                category_scores=category_scores,
                assessment_date=datetime.now(timezone.utc),
                assessment_version=assessment_data.get('version', '1.0'),
                completion_time_minutes=assessment_data.get('completion_time_minutes', 0),
                confidence_level=assessment_data.get('confidence_level', 0.8),
                metadata={
                    'assessment_data': assessment_data,
                    'category_weights': self.config.category_weights
                }
            )
            
            # Save assessment score
            self._save_assessment_score(assessment_score)
            
            # Track analytics
            self._track_assessment_analytics(user_id, assessment_score)
            
            logger.info(f"Processed assessment results for user {user_id}: score {total_score}")
            return assessment_score
            
        except Exception as e:
            logger.error(f"Error processing assessment results for user {user_id}: {e}")
            raise
    
    def generate_tier_recommendation(self, user_id: str, assessment_score: AssessmentScore) -> TierRecommendation:
        """Generate tier recommendation based on assessment score"""
        try:
            # Determine recommended tier based on score
            recommended_tier = self._determine_tier_from_score(assessment_score.total_score)
            
            # Analyze user needs based on category scores
            primary_needs, secondary_needs = self._analyze_user_needs(assessment_score.category_scores)
            
            # Get tier benefits
            tier_benefits = self._get_tier_benefits(recommended_tier, primary_needs, secondary_needs)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(assessment_score)
            
            # Determine upgrade path
            upgrade_path = self._determine_upgrade_path(recommended_tier)
            
            # Calculate estimated value
            estimated_value = self._calculate_estimated_value(recommended_tier, primary_needs)
            
            # Generate reasoning
            reasoning = self._generate_recommendation_reasoning(assessment_score, recommended_tier, primary_needs)
            
            # Create recommendation
            recommendation = TierRecommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                recommended_tier=recommended_tier,
                assessment_score=assessment_score.total_score,
                confidence_score=confidence_score,
                primary_needs=primary_needs,
                secondary_needs=secondary_needs,
                tier_benefits=tier_benefits,
                upgrade_path=upgrade_path,
                estimated_value=estimated_value,
                reasoning=reasoning,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                is_active=True
            )
            
            # Save recommendation
            self._save_tier_recommendation(recommendation)
            
            # Send notification
            self._send_recommendation_notification(user_id, recommendation)
            
            logger.info(f"Generated tier recommendation for user {user_id}: {recommended_tier.value}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating tier recommendation for user {user_id}: {e}")
            raise
    
    def get_tier_benefits(self, tier: AssessmentTier, user_needs: List[UserNeed] = None) -> List[TierBenefit]:
        """Get tier benefits with optional user need filtering"""
        try:
            tier_benefits_data = self.config.tier_benefits.get(tier, [])
            benefits = []
            
            for benefit_data in tier_benefits_data:
                # Calculate relevance score based on user needs
                relevance_score = benefit_data['relevance_score']
                if user_needs:
                    need_alignment = benefit_data.get('user_need_alignment', [])
                    need_overlap = len(set(user_needs) & set(need_alignment))
                    relevance_score *= (1 + need_overlap * 0.1)  # Boost relevance for aligned needs
                
                benefit = TierBenefit(
                    benefit_id=str(uuid.uuid4()),
                    tier=tier,
                    title=benefit_data['title'],
                    description=benefit_data['description'],
                    value_proposition=benefit_data['value_proposition'],
                    relevance_score=min(1.0, relevance_score),
                    user_need_alignment=benefit_data.get('user_need_alignment', []),
                    implementation_effort=benefit_data['implementation_effort'],
                    expected_impact=benefit_data['expected_impact']
                )
                benefits.append(benefit)
            
            # Sort by relevance score
            benefits.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return benefits
            
        except Exception as e:
            logger.error(f"Error getting tier benefits for tier {tier.value}: {e}")
            return []
    
    def get_user_recommendations(self, user_id: str) -> List[TierRecommendation]:
        """Get active tier recommendations for user"""
        try:
            recommendations = self._get_tier_recommendations(user_id)
            
            # Filter active recommendations
            active_recommendations = [
                rec for rec in recommendations 
                if rec.is_active and rec.expires_at > datetime.now(timezone.utc)
            ]
            
            # Sort by confidence score
            active_recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return active_recommendations
            
        except Exception as e:
            logger.error(f"Error getting user recommendations for user {user_id}: {e}")
            return []
    
    def compare_tiers(self, user_id: str, assessment_score: AssessmentScore) -> Dict[str, Any]:
        """Compare different tiers for user"""
        try:
            comparison = {
                'user_id': user_id,
                'assessment_score': assessment_score.total_score,
                'tiers': {},
                'recommendation': None
            }
            
            # Generate recommendation
            recommendation = self.generate_tier_recommendation(user_id, assessment_score)
            comparison['recommendation'] = {
                'tier': recommendation.recommended_tier.value,
                'confidence_score': recommendation.confidence_score,
                'reasoning': recommendation.reasoning
            }
            
            # Compare all tiers
            for tier in AssessmentTier:
                tier_details = self.tier_details[tier]
                tier_benefits = self.get_tier_benefits(tier, recommendation.primary_needs)
                
                comparison['tiers'][tier.value] = {
                    'name': tier_details['name'],
                    'price': tier_details['price'],
                    'currency': tier_details['currency'],
                    'billing_cycle': tier_details['billing_cycle'],
                    'target_audience': tier_details['target_audience'],
                    'value_proposition': tier_details['value_proposition'],
                    'features': tier_details['features'],
                    'benefits': [
                        {
                            'title': benefit.title,
                            'description': benefit.description,
                            'value_proposition': benefit.value_proposition,
                            'relevance_score': benefit.relevance_score,
                            'implementation_effort': benefit.implementation_effort,
                            'expected_impact': benefit.expected_impact
                        }
                        for benefit in tier_benefits
                    ],
                    'is_recommended': tier == recommendation.recommended_tier,
                    'fit_score': self._calculate_tier_fit_score(tier, assessment_score, recommendation.primary_needs)
                }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing tiers for user {user_id}: {e}")
            raise
    
    def get_assessment_insights(self, user_id: str, assessment_score: AssessmentScore) -> Dict[str, Any]:
        """Get insights from assessment results"""
        try:
            insights = {
                'user_id': user_id,
                'total_score': assessment_score.total_score,
                'score_interpretation': self._interpret_score(assessment_score.total_score),
                'category_analysis': {},
                'strengths': [],
                'improvement_areas': [],
                'recommendations': []
            }
            
            # Analyze each category
            for category, score in assessment_score.category_scores.items():
                category_analysis = self._analyze_category(category, score)
                insights['category_analysis'][category.value] = category_analysis
                
                if category_analysis['strength_level'] == 'strong':
                    insights['strengths'].append({
                        'category': category.value,
                        'score': score,
                        'description': category_analysis['description']
                    })
                elif category_analysis['strength_level'] == 'weak':
                    insights['improvement_areas'].append({
                        'category': category.value,
                        'score': score,
                        'description': category_analysis['description'],
                        'improvement_suggestions': category_analysis['improvement_suggestions']
                    })
            
            # Generate recommendations
            insights['recommendations'] = self._generate_insight_recommendations(assessment_score)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting assessment insights for user {user_id}: {e}")
            raise
    
    def _calculate_category_score(self, category: AssessmentCategory, category_data: Dict[str, Any]) -> int:
        """Calculate score for a specific category"""
        # Mock implementation - in production, this would use actual scoring logic
        questions = category_data.get('questions', [])
        total_questions = len(questions)
        
        if total_questions == 0:
            return 0
        
        correct_answers = sum(1 for q in questions if q.get('correct', False))
        score = int((correct_answers / total_questions) * 20)  # Scale to 0-20
        
        return score
    
    def _determine_tier_from_score(self, total_score: int) -> AssessmentTier:
        """Determine tier based on total assessment score"""
        if total_score <= 16:
            return AssessmentTier.BUDGET
        elif total_score <= 45:
            return AssessmentTier.MID_TIER
        else:
            return AssessmentTier.PROFESSIONAL
    
    def _analyze_user_needs(self, category_scores: Dict[AssessmentCategory, int]) -> Tuple[List[UserNeed], List[UserNeed]]:
        """Analyze user needs based on category scores"""
        primary_needs = []
        secondary_needs = []
        
        # Determine needs based on low scores (areas needing improvement)
        for category, score in category_scores.items():
            if score < 10:  # Low score indicates need
                needs = self.config.need_mapping.get(category, [])
                primary_needs.extend(needs)
            elif score < 15:  # Moderate score indicates potential need
                needs = self.config.need_mapping.get(category, [])
                secondary_needs.extend(needs)
        
        # Remove duplicates
        primary_needs = list(set(primary_needs))
        secondary_needs = list(set(secondary_needs))
        
        # If no primary needs identified, use default based on highest scoring category
        if not primary_needs:
            highest_category = max(category_scores.items(), key=lambda x: x[1])[0]
            primary_needs = self.config.need_mapping.get(highest_category, [UserNeed.BASIC_FINANCIAL_EDUCATION])
        
        return primary_needs, secondary_needs
    
    def _get_tier_benefits(self, tier: AssessmentTier, primary_needs: List[UserNeed], secondary_needs: List[UserNeed]) -> List[Dict[str, Any]]:
        """Get tier benefits filtered by user needs"""
        all_benefits = self.config.tier_benefits.get(tier, [])
        filtered_benefits = []
        
        for benefit in all_benefits:
            benefit_needs = benefit.get('user_need_alignment', [])
            
            # Calculate relevance based on need alignment
            primary_alignment = len(set(primary_needs) & set(benefit_needs))
            secondary_alignment = len(set(secondary_needs) & set(benefit_needs))
            
            if primary_alignment > 0 or secondary_alignment > 0:
                # Boost relevance score based on alignment
                adjusted_relevance = benefit['relevance_score'] * (1 + primary_alignment * 0.2 + secondary_alignment * 0.1)
                
                filtered_benefits.append({
                    **benefit,
                    'relevance_score': min(1.0, adjusted_relevance),
                    'need_alignment_score': primary_alignment + secondary_alignment * 0.5
                })
        
        # Sort by relevance score
        filtered_benefits.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return filtered_benefits
    
    def _calculate_confidence_score(self, assessment_score: AssessmentScore) -> float:
        """Calculate confidence score for recommendation"""
        # Base confidence on assessment quality
        base_confidence = assessment_score.confidence_level
        
        # Adjust based on completion time (optimal range: 10-30 minutes)
        completion_time = assessment_score.completion_time_minutes
        if 10 <= completion_time <= 30:
            time_factor = 1.0
        elif completion_time < 10:
            time_factor = 0.8  # May have rushed
        else:
            time_factor = 0.9  # May have been distracted
        
        # Adjust based on score distribution
        category_scores = list(assessment_score.category_scores.values())
        score_variance = max(category_scores) - min(category_scores)
        variance_factor = 1.0 - (score_variance / 20) * 0.1  # Lower variance = higher confidence
        
        final_confidence = base_confidence * time_factor * variance_factor
        return min(1.0, max(0.5, final_confidence))
    
    def _determine_upgrade_path(self, current_tier: AssessmentTier) -> List[AssessmentTier]:
        """Determine upgrade path from current tier"""
        if current_tier == AssessmentTier.BUDGET:
            return [AssessmentTier.MID_TIER, AssessmentTier.PROFESSIONAL]
        elif current_tier == AssessmentTier.MID_TIER:
            return [AssessmentTier.PROFESSIONAL]
        else:
            return []  # Already at highest tier
    
    def _calculate_estimated_value(self, tier: AssessmentTier, primary_needs: List[UserNeed]) -> float:
        """Calculate estimated value of tier for user"""
        base_value = {
            AssessmentTier.BUDGET: 500.0,
            AssessmentTier.MID_TIER: 2000.0,
            AssessmentTier.PROFESSIONAL: 5000.0
        }.get(tier, 0.0)
        
        # Adjust based on number of primary needs
        need_multiplier = 1.0 + len(primary_needs) * 0.1
        
        return base_value * need_multiplier
    
    def _generate_recommendation_reasoning(self, assessment_score: AssessmentScore, tier: AssessmentTier, primary_needs: List[UserNeed]) -> str:
        """Generate reasoning for tier recommendation"""
        score_interpretation = self._interpret_score(assessment_score.total_score)
        
        reasoning = f"Based on your financial assessment score of {assessment_score.total_score} ({score_interpretation}), "
        reasoning += f"we recommend the {tier.value.replace('_', ' ').title()} tier. "
        
        if primary_needs:
            need_descriptions = [need.value.replace('_', ' ').title() for need in primary_needs]
            reasoning += f"This tier is specifically designed to address your primary needs: {', '.join(need_descriptions)}. "
        
        reasoning += f"The {tier.value.replace('_', ' ').title()} tier provides the optimal balance of features and value for your current financial knowledge level and goals."
        
        return reasoning
    
    def _interpret_score(self, score: int) -> str:
        """Interpret assessment score"""
        if score <= 16:
            return "Beginner level - Building foundational financial knowledge"
        elif score <= 45:
            return "Intermediate level - Developing comprehensive financial skills"
        else:
            return "Advanced level - Sophisticated financial planning capabilities"
    
    def _analyze_category(self, category: AssessmentCategory, score: int) -> Dict[str, Any]:
        """Analyze individual category performance"""
        if score >= 16:
            strength_level = "strong"
            description = f"Excellent understanding of {category.value.replace('_', ' ')}"
        elif score >= 12:
            strength_level = "moderate"
            description = f"Good understanding of {category.value.replace('_', ' ')} with room for improvement"
        elif score >= 8:
            strength_level = "developing"
            description = f"Basic understanding of {category.value.replace('_', ' ')} with significant improvement opportunities"
        else:
            strength_level = "weak"
            description = f"Limited understanding of {category.value.replace('_', ' ')} - high priority for improvement"
        
        improvement_suggestions = self._get_improvement_suggestions(category, score)
        
        return {
            'score': score,
            'strength_level': strength_level,
            'description': description,
            'improvement_suggestions': improvement_suggestions
        }
    
    def _get_improvement_suggestions(self, category: AssessmentCategory, score: int) -> List[str]:
        """Get improvement suggestions for category"""
        suggestions = {
            AssessmentCategory.FINANCIAL_LITERACY: [
                "Complete basic financial education modules",
                "Practice budgeting and expense tracking",
                "Learn about financial goal setting"
            ],
            AssessmentCategory.INVESTMENT_KNOWLEDGE: [
                "Study investment fundamentals",
                "Learn about different asset classes",
                "Understand risk and return principles"
            ],
            AssessmentCategory.DEBT_MANAGEMENT: [
                "Create a debt repayment plan",
                "Learn about debt consolidation strategies",
                "Understand interest rates and their impact"
            ],
            AssessmentCategory.SAVINGS_BEHAVIOR: [
                "Set up automatic savings transfers",
                "Create an emergency fund",
                "Learn about different savings vehicles"
            ],
            AssessmentCategory.RETIREMENT_PLANNING: [
                "Calculate retirement needs",
                "Learn about retirement accounts",
                "Understand Social Security benefits"
            ],
            AssessmentCategory.TAX_KNOWLEDGE: [
                "Learn about tax deductions and credits",
                "Understand tax-advantaged accounts",
                "Study tax planning strategies"
            ],
            AssessmentCategory.INSURANCE_UNDERSTANDING: [
                "Learn about different insurance types",
                "Understand coverage needs",
                "Study insurance planning strategies"
            ],
            AssessmentCategory.ESTATE_PLANNING: [
                "Learn about wills and trusts",
                "Understand estate tax implications",
                "Study wealth transfer strategies"
            ]
        }
        
        return suggestions.get(category, ["Focus on improving knowledge in this area"])
    
    def _generate_insight_recommendations(self, assessment_score: AssessmentScore) -> List[str]:
        """Generate recommendations based on assessment insights"""
        recommendations = []
        
        # Overall score recommendations
        if assessment_score.total_score <= 16:
            recommendations.append("Focus on building foundational financial knowledge through basic education modules")
            recommendations.append("Start with budgeting and expense tracking to develop good financial habits")
        elif assessment_score.total_score <= 45:
            recommendations.append("Enhance your financial planning with comprehensive tools and guidance")
            recommendations.append("Consider working with a financial advisor to optimize your strategies")
        else:
            recommendations.append("Leverage advanced planning tools to maximize your financial potential")
            recommendations.append("Consider specialized services for complex financial situations")
        
        # Category-specific recommendations
        for category, score in assessment_score.category_scores.items():
            if score < 10:
                category_name = category.value.replace('_', ' ').title()
                recommendations.append(f"Prioritize improving your {category_name} knowledge and skills")
        
        return recommendations
    
    def _calculate_tier_fit_score(self, tier: AssessmentTier, assessment_score: AssessmentScore, primary_needs: List[UserNeed]) -> float:
        """Calculate how well a tier fits the user's needs"""
        # Base fit score based on score range
        score_ranges = {
            AssessmentTier.BUDGET: (0, 16),
            AssessmentTier.MID_TIER: (17, 45),
            AssessmentTier.PROFESSIONAL: (46, 100)
        }
        
        min_score, max_score = score_ranges[tier]
        score_fit = 1.0 - abs(assessment_score.total_score - (min_score + max_score) / 2) / ((max_score - min_score) / 2)
        
        # Need alignment score
        tier_benefits = self.config.tier_benefits.get(tier, [])
        need_coverage = 0
        for benefit in tier_benefits:
            benefit_needs = benefit.get('user_need_alignment', [])
            if any(need in benefit_needs for need in primary_needs):
                need_coverage += 1
        
        need_fit = need_coverage / len(primary_needs) if primary_needs else 0.5
        
        # Combine scores
        final_fit = (score_fit * 0.6) + (need_fit * 0.4)
        return min(1.0, max(0.0, final_fit))
    
    # Database operations (mock implementations)
    def _save_assessment_score(self, assessment_score: AssessmentScore) -> None:
        """Save assessment score to database"""
        # Mock implementation - in production, save to database
        pass
    
    def _save_tier_recommendation(self, recommendation: TierRecommendation) -> None:
        """Save tier recommendation to database"""
        # Mock implementation - in production, save to database
        pass
    
    def _get_tier_recommendations(self, user_id: str) -> List[TierRecommendation]:
        """Get tier recommendations from database"""
        # Mock implementation - in production, retrieve from database
        return []
    
    # Analytics and notification methods (mock implementations)
    def _track_assessment_analytics(self, user_id: str, assessment_score: AssessmentScore) -> None:
        """Track assessment analytics"""
        # Mock implementation - in production, track analytics
        pass
    
    def _send_recommendation_notification(self, user_id: str, recommendation: TierRecommendation) -> None:
        """Send recommendation notification"""
        # Mock implementation - in production, send notification
        pass 