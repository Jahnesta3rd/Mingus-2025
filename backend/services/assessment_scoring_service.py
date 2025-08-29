"""
Assessment Scoring Service - MINGUS Calculator Analysis Implementation

This service implements the EXACT calculation logic from the MINGUS Calculator Analysis Summary:
1. AI Job Risk Calculator - EXACT algorithm with field_salary_multipliers
2. Relationship Impact Calculator - EXACT point system from assessmentService.ts
3. Income Comparison Calculator - EXACT percentile formula with 8 demographic groups

Performance Requirements:
- Achieve 45ms average calculation time for income comparisons
- Use LRU caching with maxsize=1000
- Memory-efficient immutable data structures
- Thread-safe operations with proper locking
"""

import logging
import time
import math
import hashlib
import json
import threading
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from collections import defaultdict
import numpy as np

# Import existing services and models
from backend.ml.models.intelligent_job_matcher import IntelligentJobMatcher, FieldType, ExperienceLevel
from backend.ml.models.income_comparator_optimized import IncomeComparatorOptimized, ComparisonGroup, EducationLevel
from backend.services.billing_features import BillingFeaturesService

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    """AI Job Risk Levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RelationshipSegment(str, Enum):
    """Relationship Impact Segments"""
    STRESS_FREE = "stress-free"
    RELATIONSHIP_SPENDER = "relationship-spender"
    EMOTIONAL_MANAGER = "emotional-manager"
    CRISIS_MODE = "crisis-mode"

@dataclass(frozen=True)
class JobRiskScore:
    """Immutable job risk scoring result"""
    overall_score: float
    salary_score: float
    skills_score: float
    career_score: float
    company_score: float
    location_score: float
    growth_score: float
    automation_score: float
    augmentation_score: float
    final_risk_level: RiskLevel
    field_multiplier: float
    confidence_interval: Tuple[float, float]
    recommendations: List[str]
    risk_factors: List[str]

@dataclass(frozen=True)
class RelationshipScore:
    """Immutable relationship impact scoring result"""
    total_score: int
    segment: RelationshipSegment
    product_tier: str
    relationship_points: int
    stress_points: int
    trigger_points: int
    challenges: List[str]
    recommendations: List[str]
    financial_impact: Dict[str, float]

@dataclass(frozen=True)
class IncomeComparisonScore:
    """Immutable income comparison scoring result"""
    user_income: int
    overall_percentile: float
    primary_gap: Dict[str, Any]
    career_opportunity_score: float
    comparisons: List[Dict[str, Any]]
    motivational_summary: str
    action_plan: List[str]
    next_steps: List[str]
    confidence_level: float
    calculation_time_ms: float

@dataclass(frozen=True)
class AssessmentScoringResult:
    """Complete assessment scoring result"""
    user_id: str
    timestamp: datetime
    job_risk: JobRiskScore
    relationship_impact: RelationshipScore
    income_comparison: IncomeComparisonScore
    overall_risk_level: str
    primary_concerns: List[str]
    action_priorities: List[str]
    subscription_recommendation: str
    confidence_score: float

class AssessmentScoringService:
    """
    Comprehensive assessment scoring service implementing EXACT MINGUS algorithms
    """
    
    def __init__(self, db_session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.lock = threading.Lock()
        
        # Initialize calculator services
        self.job_matcher = IntelligentJobMatcher(config)
        self.income_comparator = IncomeComparatorOptimized(config)
        self.billing_service = BillingFeaturesService(db_session, config)
        
        # Performance monitoring
        self.performance_metrics = defaultdict(list)
        self.metrics_lock = threading.Lock()
        
        # Cache for assessment results
        self._assessment_cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # EXACT field salary multipliers from intelligent_job_matcher.py
        self.field_salary_multipliers = {
            FieldType.SOFTWARE_DEVELOPMENT: 1.2,  # 20% premium
            FieldType.DATA_ANALYSIS: 1.1,         # 10% premium
            FieldType.PROJECT_MANAGEMENT: 1.0,    # Base level
            FieldType.MARKETING: 0.95,             # 5% discount
            FieldType.FINANCE: 1.05,               # 5% premium
            FieldType.SALES: 0.9,                  # 10% discount
            FieldType.OPERATIONS: 0.95,            # 5% discount
            FieldType.HR: 0.9                      # 10% discount
        }
        
        # EXACT relationship scoring points from assessmentService.ts
        self.relationship_points = {
            'single': 0, 'dating': 2, 'serious': 4, 
            'married': 6, 'complicated': 8
        }
        
        self.stress_points = {
            'never': 0, 'rarely': 2, 'sometimes': 4,
            'often': 6, 'always': 8
        }
        
        self.trigger_points = {
            'after_breakup': 3, 'after_arguments': 3,
            'when_lonely': 2, 'when_jealous': 2, 'social_pressure': 2
        }
        
        logger.info("AssessmentScoringService initialized with EXACT MINGUS algorithms")
    
    def record_metric(self, operation: str, duration: float):
        """Record performance metric"""
        with self.metrics_lock:
            self.performance_metrics[operation].append(duration)
            # Keep only last 100 measurements
            if len(self.performance_metrics[operation]) > 100:
                self.performance_metrics[operation] = self.performance_metrics[operation][-100:]
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        with self.metrics_lock:
            return {op: sum(times) / len(times) if times else 0.0 
                   for op, times in self.performance_metrics.items()}
    
    def calculate_comprehensive_assessment(self, 
                                         user_id: str,
                                         assessment_data: Dict[str, Any]) -> AssessmentScoringResult:
        """
        Calculate comprehensive assessment using EXACT MINGUS algorithms
        
        Args:
            user_id: User identifier
            assessment_data: Complete assessment responses
            
        Returns:
            AssessmentScoringResult with all three calculator results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting comprehensive assessment for user {user_id}")
            
            # Generate cache key
            cache_key = self._generate_cache_key(user_id, assessment_data)
            
            # Check cache
            if cache_key in self._assessment_cache:
                cached_result = self._assessment_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self._cache_ttl:
                    logger.info(f"Returning cached assessment result for user {user_id}")
                    return cached_result['result']
            
            # Calculate all three assessments
            job_risk = self._calculate_ai_job_risk(assessment_data)
            relationship_impact = self._calculate_relationship_impact(assessment_data)
            income_comparison = self._calculate_income_comparison(assessment_data)
            
            # Generate overall assessment
            overall_result = self._generate_overall_assessment(
                job_risk, relationship_impact, income_comparison
            )
            
            # Cache result
            self._assessment_cache[cache_key] = {
                'result': overall_result,
                'timestamp': time.time()
            }
            
            # Record performance
            total_time = time.time() - start_time
            self.record_metric("comprehensive_assessment", total_time)
            
            logger.info(f"Completed comprehensive assessment for user {user_id} in {total_time:.3f}s")
            
            return overall_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive assessment for user {user_id}: {str(e)}")
            raise
    
    def _calculate_ai_job_risk(self, assessment_data: Dict[str, Any]) -> JobRiskScore:
        """
        AI Job Risk Calculator - IMPLEMENT EXACT ALGORITHM:
        overall_score = (
            salary_score * 0.35 +      # 35% weight - Primary importance
            skills_score * 0.25 +      # 25% weight - Skills alignment 
            career_score * 0.20 +      # 20% weight - Career progression
            company_score * 0.10 +     # 10% weight - Company quality
            location_score * 0.05 +    # 5% weight - Location fit
            growth_score * 0.05        # 5% weight - Industry alignment
        )
        """
        start_time = time.time()
        
        try:
            # Extract job-related data
            current_salary = assessment_data.get('current_salary', 50000)
            field = assessment_data.get('field', 'software_development')
            experience_level = assessment_data.get('experience_level', 'mid')
            company_size = assessment_data.get('company_size', 'medium')
            location = assessment_data.get('location', 'national')
            industry = assessment_data.get('industry', 'technology')
            
            # Calculate individual scores
            salary_score = self._calculate_salary_score(current_salary, field)
            skills_score = self._calculate_skills_score(assessment_data)
            career_score = self._calculate_career_score(experience_level, field)
            company_score = self._calculate_company_score(company_size)
            location_score = self._calculate_location_score(location)
            growth_score = self._calculate_growth_score(industry)
            
            # Apply EXACT algorithm with weights
            overall_score = (
                salary_score * 0.35 +      # 35% weight - Primary importance
                skills_score * 0.25 +      # 25% weight - Skills alignment 
                career_score * 0.20 +      # 20% weight - Career progression
                company_score * 0.10 +     # 10% weight - Company quality
                location_score * 0.05 +    # 5% weight - Location fit
                growth_score * 0.05        # 5% weight - Industry alignment
            )
            
            # Calculate automation and augmentation scores
            automation_score = self._calculate_automation_score(field, experience_level)
            augmentation_score = self._calculate_augmentation_score(field, skills_score)
            
            # Final risk level: automation_score * 0.7 + augmentation_score * 0.3
            final_risk_score = automation_score * 0.7 + augmentation_score * 0.3
            
            # Determine risk level
            if final_risk_score <= 0.3:
                risk_level = RiskLevel.LOW
            elif final_risk_score <= 0.6:
                risk_level = RiskLevel.MEDIUM
            elif final_risk_score <= 0.8:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.CRITICAL
            
            # Get field multiplier
            field_multiplier = self.field_salary_multipliers.get(
                FieldType(field), 1.0
            )
            
            # Generate recommendations
            recommendations = self._generate_job_risk_recommendations(
                risk_level, field, experience_level, salary_score
            )
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                overall_score, salary_score, skills_score
            )
            
            # Record performance
            calculation_time = time.time() - start_time
            self.record_metric("ai_job_risk_calculation", calculation_time)
            
            return JobRiskScore(
                overall_score=overall_score,
                salary_score=salary_score,
                skills_score=skills_score,
                career_score=career_score,
                company_score=company_score,
                location_score=location_score,
                growth_score=growth_score,
                automation_score=automation_score,
                augmentation_score=augmentation_score,
                final_risk_level=risk_level,
                field_multiplier=field_multiplier,
                confidence_interval=confidence_interval,
                recommendations=recommendations,
                risk_factors=self._identify_risk_factors(risk_level, field, experience_level)
            )
            
        except Exception as e:
            logger.error(f"Error in AI job risk calculation: {str(e)}")
            raise
    
    def _calculate_relationship_impact(self, assessment_data: Dict[str, Any]) -> RelationshipScore:
        """
        Relationship Impact Calculator - EXACT POINT SYSTEM:
        Implement exact scoring from assessmentService.ts
        """
        start_time = time.time()
        
        try:
            total_score = 0
            
            # Relationship status points
            relationship_status = assessment_data.get('relationship_status', 'single')
            relationship_points = self.relationship_points.get(relationship_status, 0)
            total_score += relationship_points
            
            # Financial stress frequency
            stress_frequency = assessment_data.get('financial_stress_frequency', 'never')
            stress_points = self.stress_points.get(stress_frequency, 0)
            total_score += stress_points
            
            # Emotional spending triggers (additive)
            trigger_points = 0
            emotional_triggers = assessment_data.get('emotional_triggers', [])
            for trigger in emotional_triggers:
                trigger_points += self.trigger_points.get(trigger, 0)
            total_score += trigger_points
            
            # EXACT segment classification
            if total_score <= 16:
                segment = RelationshipSegment.STRESS_FREE
                product_tier = 'Budget ($10)'
            elif total_score <= 25:
                segment = RelationshipSegment.RELATIONSHIP_SPENDER
                product_tier = 'Mid-tier ($20)'
            elif total_score <= 35:
                segment = RelationshipSegment.EMOTIONAL_MANAGER
                product_tier = 'Mid-tier ($20)'
            else:
                segment = RelationshipSegment.CRISIS_MODE
                product_tier = 'Professional ($50)'
            
            # Generate segment-specific content
            segment_content = self._get_relationship_segment_content(segment)
            
            # Calculate financial impact
            financial_impact = self._calculate_relationship_financial_impact(
                segment, total_score, assessment_data
            )
            
            # Record performance
            calculation_time = time.time() - start_time
            self.record_metric("relationship_impact_calculation", calculation_time)
            
            return RelationshipScore(
                total_score=total_score,
                segment=segment,
                product_tier=product_tier,
                relationship_points=relationship_points,
                stress_points=stress_points,
                trigger_points=trigger_points,
                challenges=segment_content['challenges'],
                recommendations=segment_content['recommendations'],
                financial_impact=financial_impact
            )
            
        except Exception as e:
            logger.error(f"Error in relationship impact calculation: {str(e)}")
            raise
    
    def _calculate_income_comparison(self, assessment_data: Dict[str, Any]) -> IncomeComparisonScore:
        """
        Income Comparison Calculator - EXACT PERCENTILE FORMULA:
        Integrate with existing income_comparator_optimized.py
        Use the exact _calculate_percentile_cached method
        """
        start_time = time.time()
        
        try:
            user_income = assessment_data.get('current_salary', 50000)
            location = assessment_data.get('location', None)
            education_level = assessment_data.get('education_level', None)
            age_group = assessment_data.get('age_group', '25-35')
            
            # Use existing income comparator with EXACT formula
            income_analysis = self.income_comparator.analyze_income(
                user_income=user_income,
                location=location,
                education_level=EducationLevel(education_level) if education_level else None,
                age_group=age_group
            )
            
            # Record performance
            calculation_time = time.time() - start_time
            self.record_metric("income_comparison_calculation", calculation_time)
            
            return IncomeComparisonScore(
                user_income=user_income,
                overall_percentile=income_analysis.overall_percentile,
                primary_gap=income_analysis.primary_gap,
                career_opportunity_score=income_analysis.career_opportunity_score,
                comparisons=income_analysis.comparisons,
                motivational_summary=income_analysis.motivational_summary,
                action_plan=income_analysis.action_plan,
                next_steps=income_analysis.next_steps,
                confidence_level=income_analysis.confidence_level,
                calculation_time_ms=calculation_time * 1000
            )
            
        except Exception as e:
            logger.error(f"Error in income comparison calculation: {str(e)}")
            raise
    
    def _generate_overall_assessment(self, 
                                   job_risk: JobRiskScore,
                                   relationship_impact: RelationshipScore,
                                   income_comparison: IncomeComparisonScore) -> AssessmentScoringResult:
        """Generate overall assessment with integrated insights"""
        
        # Determine overall risk level
        risk_scores = {
            'job': self._risk_level_to_score(job_risk.final_risk_level),
            'relationship': self._relationship_segment_to_score(relationship_impact.segment),
            'income': self._percentile_to_risk_score(income_comparison.overall_percentile)
        }
        
        overall_risk_score = sum(risk_scores.values()) / len(risk_scores)
        
        if overall_risk_score <= 0.3:
            overall_risk_level = "Low Risk"
        elif overall_risk_score <= 0.6:
            overall_risk_level = "Medium Risk"
        elif overall_risk_score <= 0.8:
            overall_risk_level = "High Risk"
        else:
            overall_risk_level = "Critical Risk"
        
        # Identify primary concerns
        primary_concerns = []
        if job_risk.final_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            primary_concerns.append("Job Security Risk")
        if relationship_impact.segment in [RelationshipSegment.EMOTIONAL_MANAGER, RelationshipSegment.CRISIS_MODE]:
            primary_concerns.append("Financial Relationship Stress")
        if income_comparison.overall_percentile < 50:
            primary_concerns.append("Income Gap")
        
        # Generate action priorities
        action_priorities = self._generate_action_priorities(
            job_risk, relationship_impact, income_comparison
        )
        
        # Determine subscription recommendation
        subscription_recommendation = self._determine_subscription_recommendation(
            relationship_impact.product_tier, overall_risk_score
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            job_risk.confidence_interval,
            income_comparison.confidence_level
        )
        
        return AssessmentScoringResult(
            user_id="",  # Will be set by caller
            timestamp=datetime.utcnow(),
            job_risk=job_risk,
            relationship_impact=relationship_impact,
            income_comparison=income_comparison,
            overall_risk_level=overall_risk_level,
            primary_concerns=primary_concerns,
            action_priorities=action_priorities,
            subscription_recommendation=subscription_recommendation,
            confidence_score=confidence_score
        )
    
    # Helper methods for individual score calculations
    def _calculate_salary_score(self, current_salary: int, field: str) -> float:
        """Calculate salary score based on field and current salary"""
        field_multiplier = self.field_salary_multipliers.get(FieldType(field), 1.0)
        base_salary = 50000  # Base salary for comparison
        
        # Normalize salary relative to field
        normalized_salary = current_salary / (base_salary * field_multiplier)
        
        # Score based on percentile (0-1 scale)
        if normalized_salary <= 0.5:
            return 0.2
        elif normalized_salary <= 0.8:
            return 0.5
        elif normalized_salary <= 1.2:
            return 0.8
        else:
            return 1.0
    
    def _calculate_skills_score(self, assessment_data: Dict[str, Any]) -> float:
        """Calculate skills alignment score"""
        skills = assessment_data.get('skills', [])
        required_skills = assessment_data.get('required_skills', [])
        
        if not required_skills:
            return 0.5  # Default score if no required skills specified
        
        # Calculate skills match percentage
        matched_skills = set(skills) & set(required_skills)
        match_percentage = len(matched_skills) / len(required_skills)
        
        return min(1.0, match_percentage)
    
    def _calculate_career_score(self, experience_level: str, field: str) -> float:
        """Calculate career progression score"""
        experience_scores = {
            'entry': 0.3,
            'mid': 0.6,
            'senior': 0.8,
            'lead': 0.9,
            'executive': 1.0
        }
        
        base_score = experience_scores.get(experience_level, 0.5)
        
        # Adjust based on field growth potential
        field_growth_factors = {
            'software_development': 1.2,
            'data_analysis': 1.1,
            'project_management': 1.0,
            'marketing': 0.9,
            'finance': 1.0,
            'sales': 0.8,
            'operations': 0.9,
            'hr': 0.8
        }
        
        growth_factor = field_growth_factors.get(field, 1.0)
        return min(1.0, base_score * growth_factor)
    
    def _calculate_company_score(self, company_size: str) -> float:
        """Calculate company stability score"""
        company_scores = {
            'startup': 0.3,
            'small': 0.5,
            'medium': 0.7,
            'large': 0.8,
            'enterprise': 0.9
        }
        
        return company_scores.get(company_size, 0.5)
    
    def _calculate_location_score(self, location: str) -> float:
        """Calculate location fit score"""
        location_scores = {
            'national': 0.5,
            'urban': 0.8,
            'suburban': 0.7,
            'rural': 0.3
        }
        
        return location_scores.get(location, 0.5)
    
    def _calculate_growth_score(self, industry: str) -> float:
        """Calculate industry growth score"""
        industry_growth_scores = {
            'technology': 0.9,
            'healthcare': 0.8,
            'finance': 0.7,
            'education': 0.6,
            'retail': 0.4,
            'manufacturing': 0.5,
            'government': 0.3
        }
        
        return industry_growth_scores.get(industry, 0.5)
    
    def _calculate_automation_score(self, field: str, experience_level: str) -> float:
        """Calculate automation risk score"""
        field_automation_risk = {
            'software_development': 0.3,
            'data_analysis': 0.4,
            'project_management': 0.2,
            'marketing': 0.5,
            'finance': 0.6,
            'sales': 0.4,
            'operations': 0.7,
            'hr': 0.6
        }
        
        experience_modifier = {
            'entry': 1.2,  # Higher risk for entry level
            'mid': 1.0,
            'senior': 0.8,  # Lower risk for senior level
            'lead': 0.6,
            'executive': 0.4
        }
        
        base_risk = field_automation_risk.get(field, 0.5)
        modifier = experience_modifier.get(experience_level, 1.0)
        
        return min(1.0, base_risk * modifier)
    
    def _calculate_augmentation_score(self, field: str, skills_score: float) -> float:
        """Calculate augmentation potential score"""
        # Higher skills score means better augmentation potential
        return skills_score
    
    def _calculate_confidence_interval(self, overall_score: float, 
                                     salary_score: float, 
                                     skills_score: float) -> Tuple[float, float]:
        """Calculate confidence interval for job risk assessment"""
        # Simple confidence calculation based on data quality
        base_confidence = 0.8
        data_quality_factor = (salary_score + skills_score) / 2
        
        confidence_width = 0.1 + (1 - data_quality_factor) * 0.2
        lower_bound = max(0, overall_score - confidence_width)
        upper_bound = min(1, overall_score + confidence_width)
        
        return (lower_bound, upper_bound)
    
    def _generate_job_risk_recommendations(self, risk_level: RiskLevel, 
                                         field: str, 
                                         experience_level: str, 
                                         salary_score: float) -> List[str]:
        """Generate job risk-specific recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Consider upskilling in emerging technologies")
            recommendations.append("Explore roles with higher automation resistance")
            
        if salary_score < 0.5:
            recommendations.append("Research salary benchmarks for your field and experience")
            recommendations.append("Consider negotiating for better compensation")
        
        if experience_level == 'entry':
            recommendations.append("Focus on building transferable skills")
            recommendations.append("Seek mentorship opportunities")
        
        return recommendations
    
    def _identify_risk_factors(self, risk_level: RiskLevel, 
                             field: str, 
                             experience_level: str) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            risk_factors.append(f"High automation risk in {field} field")
            
        if experience_level == 'entry':
            risk_factors.append("Entry-level position vulnerability")
            
        if field in ['operations', 'finance', 'hr']:
            risk_factors.append("Industry-specific automation trends")
            
        return risk_factors
    
    def _get_relationship_segment_content(self, segment: RelationshipSegment) -> Dict[str, List[str]]:
        """Get segment-specific content from assessmentService.ts"""
        content = {
            RelationshipSegment.STRESS_FREE: {
                'challenges': [
                    'Maintaining this balance during life changes',
                    'Helping others achieve similar harmony',
                    'Taking your success to the next level'
                ],
                'recommendations': [
                    'Share your wisdom with others',
                    'Consider becoming a mentor',
                    'Explore advanced financial strategies'
                ]
            },
            RelationshipSegment.RELATIONSHIP_SPENDER: {
                'challenges': [
                    'Setting healthy financial boundaries',
                    'Balancing generosity with self-care',
                    'Planning for long-term financial security'
                ],
                'recommendations': [
                    'Learn boundary-setting techniques',
                    'Create a relationship spending budget',
                    'Build an emergency fund for emotional times'
                ]
            },
            RelationshipSegment.EMOTIONAL_MANAGER: {
                'challenges': [
                    'Identifying emotional spending triggers',
                    'Developing healthier coping mechanisms',
                    'Building financial resilience'
                ],
                'recommendations': [
                    'Track your emotional spending patterns',
                    'Create a 30-day spending pause strategy',
                    'Build a support system for financial goals'
                ]
            },
            RelationshipSegment.CRISIS_MODE: {
                'challenges': [
                    'Breaking the cycle of financial stress',
                    'Creating immediate financial stability',
                    'Building healthy relationship boundaries'
                ],
                'recommendations': [
                    'Implement emergency financial controls',
                    'Seek professional financial counseling',
                    'Create a 90-day recovery plan'
                ]
            }
        }
        
        return content.get(segment, {'challenges': [], 'recommendations': []})
    
    def _calculate_relationship_financial_impact(self, segment: RelationshipSegment, 
                                               total_score: int, 
                                               assessment_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate financial impact of relationship patterns"""
        base_income = assessment_data.get('current_salary', 50000)
        
        # Estimate monthly spending impact based on segment
        monthly_impact_factors = {
            RelationshipSegment.STRESS_FREE: 0.0,
            RelationshipSegment.RELATIONSHIP_SPENDER: 0.15,  # 15% of income
            RelationshipSegment.EMOTIONAL_MANAGER: 0.25,     # 25% of income
            RelationshipSegment.CRISIS_MODE: 0.40            # 40% of income
        }
        
        impact_factor = monthly_impact_factors.get(segment, 0.0)
        monthly_impact = base_income / 12 * impact_factor
        
        return {
            'monthly_spending_impact': monthly_impact,
            'annual_spending_impact': monthly_impact * 12,
            'potential_savings': monthly_impact * 0.5,  # 50% of impact could be saved
            'stress_cost_percentage': impact_factor * 100
        }
    
    # Utility methods for overall assessment
    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """Convert risk level to numeric score"""
        risk_scores = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0
        }
        return risk_scores.get(risk_level, 0.5)
    
    def _relationship_segment_to_score(self, segment: RelationshipSegment) -> float:
        """Convert relationship segment to risk score"""
        segment_scores = {
            RelationshipSegment.STRESS_FREE: 0.1,
            RelationshipSegment.RELATIONSHIP_SPENDER: 0.4,
            RelationshipSegment.EMOTIONAL_MANAGER: 0.7,
            RelationshipSegment.CRISIS_MODE: 1.0
        }
        return segment_scores.get(segment, 0.5)
    
    def _percentile_to_risk_score(self, percentile: float) -> float:
        """Convert income percentile to risk score"""
        if percentile >= 80:
            return 0.1
        elif percentile >= 60:
            return 0.3
        elif percentile >= 40:
            return 0.5
        elif percentile >= 20:
            return 0.7
        else:
            return 1.0
    
    def _generate_action_priorities(self, job_risk: JobRiskScore,
                                  relationship_impact: RelationshipScore,
                                  income_comparison: IncomeComparisonScore) -> List[str]:
        """Generate prioritized action items"""
        priorities = []
        
        # Job-related priorities
        if job_risk.final_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            priorities.append("Immediate: Address job security concerns")
        
        # Relationship priorities
        if relationship_impact.segment in [RelationshipSegment.EMOTIONAL_MANAGER, RelationshipSegment.CRISIS_MODE]:
            priorities.append("High: Implement financial relationship boundaries")
        
        # Income priorities
        if income_comparison.overall_percentile < 50:
            priorities.append("Medium: Explore income advancement opportunities")
        
        # Add general priorities
        priorities.extend([
            "Ongoing: Monitor financial health metrics",
            "Regular: Review and adjust financial goals"
        ])
        
        return priorities[:5]  # Limit to top 5 priorities
    
    def _determine_subscription_recommendation(self, product_tier: str, 
                                             overall_risk_score: float) -> str:
        """Determine subscription recommendation based on risk and tier"""
        if overall_risk_score >= 0.8:
            return "Professional ($50) - High-risk situation requires expert guidance"
        elif overall_risk_score >= 0.6:
            return "Mid-tier ($20) - Moderate risk with targeted support needs"
        else:
            return product_tier  # Use relationship assessment recommendation
    
    def _calculate_confidence_score(self, job_confidence: Tuple[float, float],
                                  income_confidence: float) -> float:
        """Calculate overall confidence score"""
        job_confidence_width = job_confidence[1] - job_confidence[0]
        job_confidence_score = 1 - job_confidence_width
        
        # Average confidence scores
        overall_confidence = (job_confidence_score + income_confidence) / 2
        return min(1.0, max(0.0, overall_confidence))
    
    def _generate_cache_key(self, user_id: str, assessment_data: Dict[str, Any]) -> str:
        """Generate cache key for assessment results"""
        # Create deterministic string representation
        data_str = json.dumps(assessment_data, sort_keys=True)
        return hashlib.md5(f"{user_id}:{data_str}".encode()).hexdigest()
    
    def get_assessment_breakdown(self, user_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed breakdown of assessment calculations"""
        try:
            result = self.calculate_comprehensive_assessment(user_id, assessment_data)
            
            return {
                'overall_result': {
                    'risk_level': result.overall_risk_level,
                    'primary_concerns': result.primary_concerns,
                    'action_priorities': result.action_priorities,
                    'subscription_recommendation': result.subscription_recommendation,
                    'confidence_score': result.confidence_score
                },
                'job_risk_breakdown': {
                    'overall_score': result.job_risk.overall_score,
                    'component_scores': {
                        'salary': result.job_risk.salary_score,
                        'skills': result.job_risk.skills_score,
                        'career': result.job_risk.career_score,
                        'company': result.job_risk.company_score,
                        'location': result.job_risk.location_score,
                        'growth': result.job_risk.growth_score
                    },
                    'risk_factors': result.job_risk.risk_factors,
                    'field_multiplier': result.job_risk.field_multiplier,
                    'confidence_interval': result.job_risk.confidence_interval
                },
                'relationship_breakdown': {
                    'total_score': result.relationship_impact.total_score,
                    'segment': result.relationship_impact.segment.value,
                    'component_scores': {
                        'relationship_points': result.relationship_impact.relationship_points,
                        'stress_points': result.relationship_impact.stress_points,
                        'trigger_points': result.relationship_impact.trigger_points
                    },
                    'financial_impact': result.relationship_impact.financial_impact
                },
                'income_comparison_breakdown': {
                    'overall_percentile': result.income_comparison.overall_percentile,
                    'career_opportunity_score': result.income_comparison.career_opportunity_score,
                    'calculation_time_ms': result.income_comparison.calculation_time_ms,
                    'confidence_level': result.income_comparison.confidence_level
                },
                'performance_metrics': self.get_performance_stats()
            }
            
        except Exception as e:
            logger.error(f"Error getting assessment breakdown: {str(e)}")
            raise
