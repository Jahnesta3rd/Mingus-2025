"""
Product Optimization Insights System

This module provides comprehensive product optimization insights including most valuable
banking features by tier, feature usage patterns and workflows, user journey analysis
through banking features, drop-off points in banking workflows, and optimization
opportunities identification.
"""

import logging
import time
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import threading
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, case, when
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
from scipy import stats

from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.models.analytics_models import AnalyticsEvent, UserBehavior
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity

logger = logging.getLogger(__name__)


class OptimizationMetric(Enum):
    """Product optimization metrics"""
    FEATURE_VALUE = "feature_value"
    USAGE_PATTERNS = "usage_patterns"
    USER_JOURNEY = "user_journey"
    DROP_OFF_POINTS = "drop_off_points"
    OPTIMIZATION_OPPORTUNITIES = "optimization_opportunities"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"
    CONVERSION_FUNNELS = "conversion_funnels"
    ENGAGEMENT_SCORES = "engagement_scores"


class JourneyStage(Enum):
    """User journey stages"""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    ONBOARDING = "onboarding"
    FEATURE_DISCOVERY = "feature_discovery"
    FEATURE_USAGE = "feature_usage"
    ADVANCED_USAGE = "advanced_usage"
    ADVOCACY = "advocacy"
    CHURN = "churn"


class DropOffType(Enum):
    """Drop-off point types"""
    ONBOARDING = "onboarding"
    FEATURE_ACCESS = "feature_access"
    WORKFLOW_STEP = "workflow_step"
    PAYMENT = "payment"
    VERIFICATION = "verification"
    CONFIGURATION = "configuration"
    INTEGRATION = "integration"


@dataclass
class FeatureValueAnalysis:
    """Feature value analysis data"""
    analysis_id: str
    feature_name: str
    subscription_tier: str
    usage_count: int
    unique_users: int
    time_spent: float
    revenue_impact: float
    user_satisfaction: float
    retention_impact: float
    value_score: float
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsagePattern:
    """Feature usage pattern data"""
    pattern_id: str
    feature_name: str
    user_id: str
    session_id: str
    workflow_steps: List[str]
    step_durations: Dict[str, float]
    step_completion_rates: Dict[str, float]
    total_duration: float
    completion_status: str
    pattern_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserJourney:
    """User journey analysis data"""
    journey_id: str
    user_id: str
    journey_type: str
    stages_completed: List[JourneyStage]
    stage_durations: Dict[JourneyStage, float]
    stage_transitions: List[Tuple[JourneyStage, JourneyStage]]
    conversion_points: List[str]
    drop_off_points: List[str]
    journey_duration: float
    success_rate: float
    journey_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DropOffPoint:
    """Drop-off point analysis data"""
    drop_off_id: str
    feature_name: str
    workflow_step: str
    drop_off_type: DropOffType
    user_count: int
    drop_off_rate: float
    average_time_before_drop: float
    common_reasons: List[str]
    impact_score: float
    optimization_priority: str
    detected_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationOpportunity:
    """Optimization opportunity data"""
    opportunity_id: str
    opportunity_type: str
    feature_name: str
    current_metric: float
    target_metric: float
    improvement_potential: float
    implementation_effort: str
    business_impact: str
    user_impact: str
    priority_score: float
    recommendations: List[str]
    detected_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEfficiency:
    """Workflow efficiency analysis data"""
    workflow_id: str
    workflow_name: str
    total_users: int
    completed_users: int
    completion_rate: float
    average_duration: float
    step_efficiencies: Dict[str, float]
    bottleneck_steps: List[str]
    optimization_opportunities: List[str]
    efficiency_score: float
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductOptimizationInsights:
    """Comprehensive product optimization insights system"""
    
    def __init__(self, db_session: Session, access_control_service: AccessControlService,
                 audit_service: AuditLoggingService):
        self.db = db_session
        self.access_control_service = access_control_service
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize data storage
        self.feature_value_analyses = self._initialize_feature_value_analyses()
        self.usage_patterns = self._initialize_usage_patterns()
        self.user_journeys = self._initialize_user_journeys()
        self.drop_off_points = self._initialize_drop_off_points()
        self.optimization_opportunities = self._initialize_optimization_opportunities()
        self.workflow_efficiencies = self._initialize_workflow_efficiencies()
        
        # Optimization thresholds and weights
        self.optimization_thresholds = self._initialize_optimization_thresholds()
        self.feature_weights = self._initialize_feature_weights()
        
        # Start optimization monitoring
        self._start_optimization_monitoring()
    
    def _initialize_feature_value_analyses(self) -> Dict[str, FeatureValueAnalysis]:
        """Initialize feature value analyses storage"""
        return {}
    
    def _initialize_usage_patterns(self) -> Dict[str, UsagePattern]:
        """Initialize usage patterns storage"""
        return {}
    
    def _initialize_user_journeys(self) -> Dict[str, UserJourney]:
        """Initialize user journeys storage"""
        return {}
    
    def _initialize_drop_off_points(self) -> Dict[str, DropOffPoint]:
        """Initialize drop-off points storage"""
        return {}
    
    def _initialize_optimization_opportunities(self) -> Dict[str, OptimizationOpportunity]:
        """Initialize optimization opportunities storage"""
        return {}
    
    def _initialize_workflow_efficiencies(self) -> Dict[str, WorkflowEfficiency]:
        """Initialize workflow efficiencies storage"""
        return {}
    
    def _initialize_optimization_thresholds(self) -> Dict[OptimizationMetric, Dict[str, float]]:
        """Initialize optimization thresholds"""
        return {
            OptimizationMetric.FEATURE_VALUE: {
                'low_value': 0.3,
                'medium_value': 0.6,
                'high_value': 0.8
            },
            OptimizationMetric.DROP_OFF_POINTS: {
                'critical_drop_off': 0.5,
                'high_drop_off': 0.3,
                'medium_drop_off': 0.15
            },
            OptimizationMetric.WORKFLOW_EFFICIENCY: {
                'low_efficiency': 0.5,
                'medium_efficiency': 0.7,
                'high_efficiency': 0.9
            }
        }
    
    def _initialize_feature_weights(self) -> Dict[str, float]:
        """Initialize feature weights for value calculation"""
        return {
            'usage_count': 0.25,
            'time_spent': 0.20,
            'revenue_impact': 0.25,
            'user_satisfaction': 0.15,
            'retention_impact': 0.15
        }
    
    def _start_optimization_monitoring(self):
        """Start product optimization monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_optimization, daemon=True)
            monitoring_thread.start()
            self.logger.info("Product optimization monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting optimization monitoring: {e}")
    
    def _monitor_optimization(self):
        """Monitor product optimization and generate insights"""
        while True:
            try:
                # Analyze feature values
                self._analyze_feature_values()
                
                # Identify drop-off points
                self._identify_drop_off_points()
                
                # Find optimization opportunities
                self._find_optimization_opportunities()
                
                # Update workflow efficiencies
                self._update_workflow_efficiencies()
                
                # Sleep for monitoring interval
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in optimization monitoring: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def analyze_feature_value_by_tier(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze most valuable banking features by tier"""
        try:
            end_time = datetime.utcnow()
            if time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            else:
                start_time = end_time - timedelta(days=90)
            
            # Filter feature value analyses by time period
            analyses = [
                analysis for analysis in self.feature_value_analyses.values()
                if analysis.analysis_date >= start_time
            ]
            
            if not analyses:
                return {"error": "No feature value analysis data available"}
            
            # Analyze by tier
            tier_analysis = defaultdict(lambda: {
                'features': [],
                'total_value_score': 0.0,
                'average_value_score': 0.0,
                'feature_count': 0
            })
            
            for analysis in analyses:
                tier_analysis[analysis.subscription_tier]['features'].append({
                    'feature_name': analysis.feature_name,
                    'usage_count': analysis.usage_count,
                    'unique_users': analysis.unique_users,
                    'time_spent': analysis.time_spent,
                    'revenue_impact': analysis.revenue_impact,
                    'user_satisfaction': analysis.user_satisfaction,
                    'retention_impact': analysis.retention_impact,
                    'value_score': analysis.value_score
                })
                tier_analysis[analysis.subscription_tier]['total_value_score'] += analysis.value_score
                tier_analysis[analysis.subscription_tier]['feature_count'] += 1
            
            # Calculate averages and sort features
            results = {}
            for tier, data in tier_analysis.items():
                data['average_value_score'] = data['total_value_score'] / data['feature_count'] if data['feature_count'] > 0 else 0.0
                
                # Sort features by value score
                data['features'].sort(key=lambda x: x['value_score'], reverse=True)
                
                # Get top features
                data['top_features'] = data['features'][:5]
                
                results[tier] = data
            
            return {
                'time_period': time_period,
                'tier_analysis': results,
                'total_features_analyzed': len(analyses)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing feature value by tier: {e}")
            return {"error": str(e)}
    
    def analyze_feature_usage_patterns(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze feature usage patterns and workflows"""
        try:
            end_time = datetime.utcnow()
            if time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            else:
                start_time = end_time - timedelta(days=90)
            
            # Filter usage patterns by time period
            patterns = [
                pattern for pattern in self.usage_patterns.values()
                if pattern.pattern_date >= start_time
            ]
            
            if not patterns:
                return {"error": "No usage pattern data available"}
            
            # Analyze by feature
            feature_analysis = defaultdict(lambda: {
                'total_sessions': 0,
                'completed_sessions': 0,
                'completion_rate': 0.0,
                'average_duration': 0.0,
                'workflow_steps': Counter(),
                'step_durations': defaultdict(list),
                'step_completion_rates': defaultdict(list),
                'common_workflows': []
            })
            
            for pattern in patterns:
                feature_analysis[pattern.feature_name]['total_sessions'] += 1
                feature_analysis[pattern.feature_name]['workflow_steps'].update(pattern.workflow_steps)
                
                if pattern.completion_status == 'completed':
                    feature_analysis[pattern.feature_name]['completed_sessions'] += 1
                
                # Collect step durations and completion rates
                for step, duration in pattern.step_durations.items():
                    feature_analysis[pattern.feature_name]['step_durations'][step].append(duration)
                
                for step, rate in pattern.step_completion_rates.items():
                    feature_analysis[pattern.feature_name]['step_completion_rates'][step].append(rate)
            
            # Calculate metrics
            results = {}
            for feature_name, analysis in feature_analysis.items():
                completion_rate = analysis['completed_sessions'] / analysis['total_sessions'] if analysis['total_sessions'] > 0 else 0.0
                
                # Calculate average step durations
                avg_step_durations = {}
                for step, durations in analysis['step_durations'].items():
                    avg_step_durations[step] = statistics.mean(durations) if durations else 0.0
                
                # Calculate average step completion rates
                avg_step_completion_rates = {}
                for step, rates in analysis['step_completion_rates'].items():
                    avg_step_completion_rates[step] = statistics.mean(rates) if rates else 0.0
                
                # Get most common workflows
                common_workflows = analysis['workflow_steps'].most_common(5)
                
                results[feature_name] = {
                    'total_sessions': analysis['total_sessions'],
                    'completed_sessions': analysis['completed_sessions'],
                    'completion_rate': completion_rate,
                    'average_step_durations': avg_step_durations,
                    'average_step_completion_rates': avg_step_completion_rates,
                    'most_common_workflows': [{'step': step, 'count': count} for step, count in common_workflows]
                }
            
            return {
                'time_period': time_period,
                'feature_analysis': results,
                'total_patterns_analyzed': len(patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing feature usage patterns: {e}")
            return {"error": str(e)}
    
    def analyze_user_journey_through_features(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze user journey through banking features"""
        try:
            end_time = datetime.utcnow()
            if time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            else:
                start_time = end_time - timedelta(days=90)
            
            # Filter user journeys by time period
            journeys = [
                journey for journey in self.user_journeys.values()
                if journey.journey_date >= start_time
            ]
            
            if not journeys:
                return {"error": "No user journey data available"}
            
            # Analyze by journey type
            journey_analysis = defaultdict(lambda: {
                'total_journeys': 0,
                'successful_journeys': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'stage_completion_rates': defaultdict(list),
                'stage_durations': defaultdict(list),
                'common_transitions': Counter(),
                'drop_off_points': Counter(),
                'conversion_points': Counter()
            })
            
            for journey in journeys:
                journey_analysis[journey.journey_type]['total_journeys'] += 1
                
                if journey.success_rate >= 0.8:  # 80% success threshold
                    journey_analysis[journey.journey_type]['successful_journeys'] += 1
                
                # Collect stage completion rates
                for stage in JourneyStage:
                    if stage in journey.stages_completed:
                        journey_analysis[journey.journey_type]['stage_completion_rates'][stage.value].append(1.0)
                    else:
                        journey_analysis[journey.journey_type]['stage_completion_rates'][stage.value].append(0.0)
                
                # Collect stage durations
                for stage, duration in journey.stage_durations.items():
                    journey_analysis[journey.journey_type]['stage_durations'][stage.value].append(duration)
                
                # Collect transitions
                for transition in journey.stage_transitions:
                    transition_key = f"{transition[0].value} -> {transition[1].value}"
                    journey_analysis[journey.journey_type]['common_transitions'][transition_key] += 1
                
                # Collect drop-off points
                for drop_off in journey.drop_off_points:
                    journey_analysis[journey.journey_type]['drop_off_points'][drop_off] += 1
                
                # Collect conversion points
                for conversion in journey.conversion_points:
                    journey_analysis[journey.journey_type]['conversion_points'][conversion] += 1
            
            # Calculate metrics
            results = {}
            for journey_type, analysis in journey_analysis.items():
                success_rate = analysis['successful_journeys'] / analysis['total_journeys'] if analysis['total_journeys'] > 0 else 0.0
                
                # Calculate average stage completion rates
                avg_stage_completion_rates = {}
                for stage, rates in analysis['stage_completion_rates'].items():
                    avg_stage_completion_rates[stage] = statistics.mean(rates) if rates else 0.0
                
                # Calculate average stage durations
                avg_stage_durations = {}
                for stage, durations in analysis['stage_durations'].items():
                    avg_stage_durations[stage] = statistics.mean(durations) if durations else 0.0
                
                # Get most common transitions, drop-offs, and conversions
                common_transitions = analysis['common_transitions'].most_common(5)
                common_drop_offs = analysis['drop_off_points'].most_common(5)
                common_conversions = analysis['conversion_points'].most_common(5)
                
                results[journey_type] = {
                    'total_journeys': analysis['total_journeys'],
                    'successful_journeys': analysis['successful_journeys'],
                    'success_rate': success_rate,
                    'average_stage_completion_rates': avg_stage_completion_rates,
                    'average_stage_durations': avg_stage_durations,
                    'most_common_transitions': [{'transition': trans, 'count': count} for trans, count in common_transitions],
                    'most_common_drop_offs': [{'drop_off': drop, 'count': count} for drop, count in common_drop_offs],
                    'most_common_conversions': [{'conversion': conv, 'count': count} for conv, count in common_conversions]
                }
            
            return {
                'time_period': time_period,
                'journey_analysis': results,
                'total_journeys_analyzed': len(journeys)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing user journey through features: {e}")
            return {"error": str(e)}
    
    def identify_drop_off_points(self, time_period: str = "90d") -> Dict[str, Any]:
        """Identify drop-off points in banking workflows"""
        try:
            end_time = datetime.utcnow()
            if time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            else:
                start_time = end_time - timedelta(days=90)
            
            # Filter drop-off points by time period
            drop_offs = [
                drop_off for drop_off in self.drop_off_points.values()
                if drop_off.detected_date >= start_time
            ]
            
            if not drop_offs:
                return {"error": "No drop-off point data available"}
            
            # Analyze by feature and workflow step
            drop_off_analysis = defaultdict(lambda: {
                'total_users': 0,
                'total_drop_offs': 0,
                'overall_drop_off_rate': 0.0,
                'drop_off_points': [],
                'average_impact_score': 0.0,
                'optimization_priorities': Counter()
            })
            
            for drop_off in drop_offs:
                key = f"{drop_off.feature_name}_{drop_off.workflow_step}"
                drop_off_analysis[key]['total_users'] += drop_off.user_count
                drop_off_analysis[key]['total_drop_offs'] += drop_off.user_count
                drop_off_analysis[key]['drop_off_points'].append({
                    'drop_off_type': drop_off.drop_off_type.value,
                    'drop_off_rate': drop_off.drop_off_rate,
                    'average_time_before_drop': drop_off.average_time_before_drop,
                    'common_reasons': drop_off.common_reasons,
                    'impact_score': drop_off.impact_score,
                    'optimization_priority': drop_off.optimization_priority
                })
                drop_off_analysis[key]['optimization_priorities'][drop_off.optimization_priority] += 1
            
            # Calculate metrics
            results = {}
            for key, analysis in drop_off_analysis.items():
                overall_drop_off_rate = analysis['total_drop_offs'] / analysis['total_users'] if analysis['total_users'] > 0 else 0.0
                avg_impact_score = statistics.mean([point['impact_score'] for point in analysis['drop_off_points']]) if analysis['drop_off_points'] else 0.0
                
                # Get most common optimization priorities
                common_priorities = analysis['optimization_priorities'].most_common(3)
                
                results[key] = {
                    'total_users': analysis['total_users'],
                    'total_drop_offs': analysis['total_drop_offs'],
                    'overall_drop_off_rate': overall_drop_off_rate,
                    'drop_off_points': analysis['drop_off_points'],
                    'average_impact_score': avg_impact_score,
                    'optimization_priorities': [{'priority': pri, 'count': count} for pri, count in common_priorities],
                    'severity_level': self._determine_drop_off_severity(overall_drop_off_rate, avg_impact_score)
                }
            
            return {
                'time_period': time_period,
                'drop_off_analysis': results,
                'total_drop_off_points': len(drop_offs)
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying drop-off points: {e}")
            return {"error": str(e)}
    
    def identify_optimization_opportunities(self, time_period: str = "90d") -> Dict[str, Any]:
        """Identify optimization opportunities"""
        try:
            end_time = datetime.utcnow()
            if time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            else:
                start_time = end_time - timedelta(days=90)
            
            # Filter optimization opportunities by time period
            opportunities = [
                opportunity for opportunity in self.optimization_opportunities.values()
                if opportunity.detected_date >= start_time
            ]
            
            if not opportunities:
                return {"error": "No optimization opportunity data available"}
            
            # Analyze by opportunity type
            opportunity_analysis = defaultdict(lambda: {
                'total_opportunities': 0,
                'average_improvement_potential': 0.0,
                'average_priority_score': 0.0,
                'opportunities': [],
                'implementation_efforts': Counter(),
                'business_impacts': Counter()
            })
            
            for opportunity in opportunities:
                opportunity_analysis[opportunity.opportunity_type]['total_opportunities'] += 1
                opportunity_analysis[opportunity.opportunity_type]['opportunities'].append({
                    'opportunity_id': opportunity.opportunity_id,
                    'feature_name': opportunity.feature_name,
                    'current_metric': opportunity.current_metric,
                    'target_metric': opportunity.target_metric,
                    'improvement_potential': opportunity.improvement_potential,
                    'implementation_effort': opportunity.implementation_effort,
                    'business_impact': opportunity.business_impact,
                    'user_impact': opportunity.user_impact,
                    'priority_score': opportunity.priority_score,
                    'recommendations': opportunity.recommendations
                })
                opportunity_analysis[opportunity.opportunity_type]['implementation_efforts'][opportunity.implementation_effort] += 1
                opportunity_analysis[opportunity.opportunity_type]['business_impacts'][opportunity.business_impact] += 1
            
            # Calculate metrics
            results = {}
            for opportunity_type, analysis in opportunity_analysis.items():
                avg_improvement = statistics.mean([opp['improvement_potential'] for opp in analysis['opportunities']]) if analysis['opportunities'] else 0.0
                avg_priority = statistics.mean([opp['priority_score'] for opp in analysis['opportunities']]) if analysis['opportunities'] else 0.0
                
                # Sort opportunities by priority score
                analysis['opportunities'].sort(key=lambda x: x['priority_score'], reverse=True)
                
                # Get top opportunities
                analysis['top_opportunities'] = analysis['opportunities'][:5]
                
                # Get most common implementation efforts and business impacts
                common_efforts = analysis['implementation_efforts'].most_common(3)
                common_impacts = analysis['business_impacts'].most_common(3)
                
                results[opportunity_type] = {
                    'total_opportunities': analysis['total_opportunities'],
                    'average_improvement_potential': avg_improvement,
                    'average_priority_score': avg_priority,
                    'top_opportunities': analysis['top_opportunities'],
                    'implementation_efforts': [{'effort': eff, 'count': count} for eff, count in common_efforts],
                    'business_impacts': [{'impact': imp, 'count': count} for imp, count in common_impacts]
                }
            
            return {
                'time_period': time_period,
                'opportunity_analysis': results,
                'total_opportunities': len(opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying optimization opportunities: {e}")
            return {"error": str(e)}
    
    def _determine_drop_off_severity(self, drop_off_rate: float, impact_score: float) -> str:
        """Determine drop-off severity level"""
        try:
            if drop_off_rate >= self.optimization_thresholds[OptimizationMetric.DROP_OFF_POINTS]['critical_drop_off'] or impact_score >= 0.8:
                return "critical"
            elif drop_off_rate >= self.optimization_thresholds[OptimizationMetric.DROP_OFF_POINTS]['high_drop_off'] or impact_score >= 0.6:
                return "high"
            elif drop_off_rate >= self.optimization_thresholds[OptimizationMetric.DROP_OFF_POINTS]['medium_drop_off'] or impact_score >= 0.4:
                return "medium"
            else:
                return "low"
            
        except Exception as e:
            self.logger.error(f"Error determining drop-off severity: {e}")
            return "medium"
    
    def record_feature_usage_pattern(self, user_id: str, feature_name: str, session_id: str,
                                   workflow_steps: List[str], step_durations: Dict[str, float],
                                   step_completion_rates: Dict[str, float], total_duration: float,
                                   completion_status: str, metadata: Dict[str, Any] = None) -> str:
        """Record feature usage pattern"""
        try:
            pattern_id = f"pattern_{int(time.time())}_{secrets.token_hex(4)}"
            
            usage_pattern = UsagePattern(
                pattern_id=pattern_id,
                feature_name=feature_name,
                user_id=user_id,
                session_id=session_id,
                workflow_steps=workflow_steps,
                step_durations=step_durations,
                step_completion_rates=step_completion_rates,
                total_duration=total_duration,
                completion_status=completion_status,
                pattern_date=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.usage_patterns[pattern_id] = usage_pattern
            
            # Log usage pattern
            self.audit_service.log_event(
                event_type=AuditEventType.FEATURE_USAGE,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Feature usage pattern recorded for user {user_id}",
                resource_type="usage_pattern",
                resource_id=pattern_id,
                user_id=user_id,
                metadata={
                    'feature_name': feature_name,
                    'completion_status': completion_status,
                    'total_duration': total_duration
                }
            )
            
            return pattern_id
            
        except Exception as e:
            self.logger.error(f"Error recording feature usage pattern: {e}")
            raise
    
    def record_user_journey(self, user_id: str, journey_type: str, stages_completed: List[JourneyStage],
                          stage_durations: Dict[JourneyStage, float], stage_transitions: List[Tuple[JourneyStage, JourneyStage]],
                          conversion_points: List[str], drop_off_points: List[str],
                          journey_duration: float, success_rate: float,
                          metadata: Dict[str, Any] = None) -> str:
        """Record user journey analysis"""
        try:
            journey_id = f"journey_{int(time.time())}_{secrets.token_hex(4)}"
            
            user_journey = UserJourney(
                journey_id=journey_id,
                user_id=user_id,
                journey_type=journey_type,
                stages_completed=stages_completed,
                stage_durations=stage_durations,
                stage_transitions=stage_transitions,
                conversion_points=conversion_points,
                drop_off_points=drop_off_points,
                journey_duration=journey_duration,
                success_rate=success_rate,
                journey_date=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.user_journeys[journey_id] = user_journey
            
            # Log user journey
            self.audit_service.log_event(
                event_type=AuditEventType.USER_JOURNEY,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"User journey recorded for user {user_id}",
                resource_type="user_journey",
                resource_id=journey_id,
                user_id=user_id,
                metadata={
                    'journey_type': journey_type,
                    'success_rate': success_rate,
                    'stages_completed': len(stages_completed)
                }
            )
            
            return journey_id
            
        except Exception as e:
            self.logger.error(f"Error recording user journey: {e}")
            raise
    
    def get_optimization_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive optimization dashboard data"""
        try:
            # Get various optimization analyses
            feature_values = self.analyze_feature_value_by_tier("90d")
            usage_patterns = self.analyze_feature_usage_patterns("90d")
            user_journeys = self.analyze_user_journey_through_features("90d")
            drop_off_points = self.identify_drop_off_points("90d")
            optimization_opportunities = self.identify_optimization_opportunities("90d")
            
            # Get recent optimization opportunities
            recent_opportunities = [
                {
                    'opportunity_id': opp.opportunity_id,
                    'opportunity_type': opp.opportunity_type,
                    'feature_name': opp.feature_name,
                    'improvement_potential': opp.improvement_potential,
                    'priority_score': opp.priority_score,
                    'business_impact': opp.business_impact,
                    'detected_date': opp.detected_date.isoformat()
                }
                for opp in self.optimization_opportunities.values()
                if opp.detected_date >= datetime.utcnow() - timedelta(days=7)
            ]
            
            return {
                'feature_values': feature_values,
                'usage_patterns': usage_patterns,
                'user_journeys': user_journeys,
                'drop_off_points': drop_off_points,
                'optimization_opportunities': optimization_opportunities,
                'recent_opportunities': recent_opportunities,
                'total_opportunities': len(self.optimization_opportunities),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting optimization dashboard: {e}")
            return {"error": str(e)}
    
    def _analyze_feature_values(self):
        """Analyze feature values for all features"""
        try:
            # This would analyze feature values for all features
            # For now, we'll just log the analysis
            self.logger.info("Feature value analysis scheduled")
            
        except Exception as e:
            self.logger.error(f"Error analyzing feature values: {e}")
    
    def _identify_drop_off_points(self):
        """Identify drop-off points for all workflows"""
        try:
            # This would identify drop-off points for all workflows
            # For now, we'll just log the identification
            self.logger.info("Drop-off point identification scheduled")
            
        except Exception as e:
            self.logger.error(f"Error identifying drop-off points: {e}")
    
    def _find_optimization_opportunities(self):
        """Find optimization opportunities"""
        try:
            # This would find optimization opportunities
            # For now, we'll just log the search
            self.logger.info("Optimization opportunity search scheduled")
            
        except Exception as e:
            self.logger.error(f"Error finding optimization opportunities: {e}")
    
    def _update_workflow_efficiencies(self):
        """Update workflow efficiencies"""
        try:
            # This would update workflow efficiencies
            # For now, we'll just log the update
            self.logger.info("Workflow efficiency update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating workflow efficiencies: {e}") 