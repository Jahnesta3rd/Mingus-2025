"""
Business Intelligence System

This module provides comprehensive business intelligence including revenue attribution
to banking features, cost-per-connection analysis, Plaid API usage optimization,
feature development prioritization, and competitive analysis integration.
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


class BusinessIntelligenceMetric(Enum):
    """Business intelligence metrics"""
    REVENUE_ATTRIBUTION = "revenue_attribution"
    COST_PER_CONNECTION = "cost_per_connection"
    PLAID_API_OPTIMIZATION = "plaid_api_optimization"
    FEATURE_PRIORITIZATION = "feature_prioritization"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    ROI_ANALYSIS = "roi_analysis"
    PROFITABILITY_ANALYSIS = "profitability_analysis"
    MARKET_POSITIONING = "market_positioning"


class RevenueSource(Enum):
    """Revenue sources"""
    SUBSCRIPTION = "subscription"
    FEATURE_USAGE = "feature_usage"
    UPGRADE = "upgrade"
    TRANSACTION_FEE = "transaction_fee"
    PREMIUM_FEATURES = "premium_features"
    CONSULTING = "consulting"
    PARTNERSHIP = "partnership"
    DATA_LICENSING = "data_licensing"


class CostType(Enum):
    """Cost types"""
    PLAID_API_COST = "plaid_api_cost"
    INFRASTRUCTURE_COST = "infrastructure_cost"
    DEVELOPMENT_COST = "development_cost"
    MARKETING_COST = "marketing_cost"
    SUPPORT_COST = "support_cost"
    COMPLIANCE_COST = "compliance_cost"
    OPERATIONAL_COST = "operational_cost"
    THIRD_PARTY_COST = "third_party_cost"


@dataclass
class RevenueAttribution:
    """Revenue attribution data"""
    attribution_id: str
    feature_name: str
    subscription_tier: str
    revenue_amount: float
    revenue_source: RevenueSource
    attribution_percentage: float
    attribution_method: str
    attribution_date: datetime
    user_count: int
    conversion_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostPerConnection:
    """Cost per connection analysis data"""
    cost_id: str
    connection_type: str
    total_cost: float
    total_connections: int
    cost_per_connection: float
    cost_breakdown: Dict[CostType, float]
    time_period: str
    cost_trend: str
    optimization_opportunities: List[str]
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaidApiUsage:
    """Plaid API usage optimization data"""
    usage_id: str
    api_endpoint: str
    request_count: int
    success_rate: float
    average_response_time: float
    error_rate: float
    cost_per_request: float
    total_cost: float
    optimization_recommendations: List[str]
    usage_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureDevelopmentPriority:
    """Feature development prioritization data"""
    priority_id: str
    feature_name: str
    business_value: float
    development_effort: float
    technical_risk: float
    market_demand: float
    competitive_advantage: float
    priority_score: float
    development_phase: str
    estimated_roi: float
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompetitiveAnalysis:
    """Competitive analysis data"""
    analysis_id: str
    competitor_name: str
    feature_comparison: Dict[str, Dict[str, Any]]
    market_share: float
    pricing_strategy: str
    technology_stack: List[str]
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    competitive_position: str
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ROIAnalysis:
    """ROI analysis data"""
    roi_id: str
    investment_type: str
    investment_amount: float
    return_amount: float
    roi_percentage: float
    payback_period: float
    net_present_value: float
    internal_rate_of_return: float
    risk_assessment: str
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfitabilityAnalysis:
    """Profitability analysis data"""
    profitability_id: str
    revenue_stream: str
    total_revenue: float
    total_costs: float
    gross_profit: float
    gross_margin: float
    operating_expenses: float
    net_profit: float
    profit_margin: float
    break_even_point: float
    analysis_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class BusinessIntelligence:
    """Comprehensive business intelligence system"""
    
    def __init__(self, db_session: Session, access_control_service: AccessControlService,
                 audit_service: AuditLoggingService):
        self.db = db_session
        self.access_control_service = access_control_service
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize data storage
        self.revenue_attributions = self._initialize_revenue_attributions()
        self.cost_per_connections = self._initialize_cost_per_connections()
        self.plaid_api_usage = self._initialize_plaid_api_usage()
        self.feature_priorities = self._initialize_feature_priorities()
        self.competitive_analyses = self._initialize_competitive_analyses()
        self.roi_analyses = self._initialize_roi_analyses()
        self.profitability_analyses = self._initialize_profitability_analyses()
        
        # Business intelligence thresholds and weights
        self.bi_thresholds = self._initialize_bi_thresholds()
        self.attribution_weights = self._initialize_attribution_weights()
        self.priority_weights = self._initialize_priority_weights()
        
        # Start business intelligence monitoring
        self._start_bi_monitoring()
    
    def _initialize_revenue_attributions(self) -> Dict[str, RevenueAttribution]:
        """Initialize revenue attributions storage"""
        return {}
    
    def _initialize_cost_per_connections(self) -> Dict[str, CostPerConnection]:
        """Initialize cost per connections storage"""
        return {}
    
    def _initialize_plaid_api_usage(self) -> Dict[str, PlaidApiUsage]:
        """Initialize Plaid API usage storage"""
        return {}
    
    def _initialize_feature_priorities(self) -> Dict[str, FeatureDevelopmentPriority]:
        """Initialize feature priorities storage"""
        return {}
    
    def _initialize_competitive_analyses(self) -> Dict[str, CompetitiveAnalysis]:
        """Initialize competitive analyses storage"""
        return {}
    
    def _initialize_roi_analyses(self) -> Dict[str, ROIAnalysis]:
        """Initialize ROI analyses storage"""
        return {}
    
    def _initialize_profitability_analyses(self) -> Dict[str, ProfitabilityAnalysis]:
        """Initialize profitability analyses storage"""
        return {}
    
    def _initialize_bi_thresholds(self) -> Dict[BusinessIntelligenceMetric, Dict[str, float]]:
        """Initialize business intelligence thresholds"""
        return {
            BusinessIntelligenceMetric.REVENUE_ATTRIBUTION: {
                'high_attribution': 0.7,
                'medium_attribution': 0.4,
                'low_attribution': 0.2
            },
            BusinessIntelligenceMetric.COST_PER_CONNECTION: {
                'high_cost': 5.0,
                'medium_cost': 2.0,
                'low_cost': 0.5
            },
            BusinessIntelligenceMetric.FEATURE_PRIORITIZATION: {
                'high_priority': 0.8,
                'medium_priority': 0.6,
                'low_priority': 0.4
            }
        }
    
    def _initialize_attribution_weights(self) -> Dict[str, float]:
        """Initialize revenue attribution weights"""
        return {
            'direct_attribution': 1.0,
            'incremental_attribution': 0.7,
            'influenced_attribution': 0.3,
            'assisted_attribution': 0.1
        }
    
    def _initialize_priority_weights(self) -> Dict[str, float]:
        """Initialize feature priority weights"""
        return {
            'business_value': 0.30,
            'development_effort': 0.20,
            'technical_risk': 0.15,
            'market_demand': 0.20,
            'competitive_advantage': 0.15
        }
    
    def _start_bi_monitoring(self):
        """Start business intelligence monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_business_intelligence, daemon=True)
            monitoring_thread.start()
            self.logger.info("Business intelligence monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting business intelligence monitoring: {e}")
    
    def _monitor_business_intelligence(self):
        """Monitor business intelligence and generate insights"""
        while True:
            try:
                # Update revenue attributions
                self._update_revenue_attributions()
                
                # Update cost per connection analysis
                self._update_cost_per_connection_analysis()
                
                # Update Plaid API usage optimization
                self._update_plaid_api_optimization()
                
                # Update feature development priorities
                self._update_feature_development_priorities()
                
                # Update competitive analysis
                self._update_competitive_analysis()
                
                # Sleep for monitoring interval
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in business intelligence monitoring: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def analyze_revenue_attribution(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze revenue attribution to banking features"""
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
            
            # Filter revenue attributions by time period
            attributions = [
                attribution for attribution in self.revenue_attributions.values()
                if attribution.attribution_date >= start_time
            ]
            
            if not attributions:
                return {"error": "No revenue attribution data available"}
            
            # Analyze by feature and tier
            feature_analysis = defaultdict(lambda: {
                'total_revenue': 0.0,
                'attribution_count': 0,
                'average_attribution': 0.0,
                'revenue_sources': Counter(),
                'tier_breakdown': defaultdict(lambda: {'revenue': 0.0, 'users': 0}),
                'conversion_rates': []
            })
            
            for attribution in attributions:
                feature_analysis[attribution.feature_name]['total_revenue'] += attribution.revenue_amount
                feature_analysis[attribution.feature_name]['attribution_count'] += 1
                feature_analysis[attribution.feature_name]['revenue_sources'][attribution.revenue_source.value] += 1
                feature_analysis[attribution.feature_name]['tier_breakdown'][attribution.subscription_tier]['revenue'] += attribution.revenue_amount
                feature_analysis[attribution.feature_name]['tier_breakdown'][attribution.subscription_tier]['users'] += attribution.user_count
                feature_analysis[attribution.feature_name]['conversion_rates'].append(attribution.conversion_rate)
            
            # Calculate metrics
            results = {}
            for feature_name, analysis in feature_analysis.items():
                avg_attribution = analysis['total_revenue'] / analysis['attribution_count'] if analysis['attribution_count'] > 0 else 0.0
                avg_conversion_rate = statistics.mean(analysis['conversion_rates']) if analysis['conversion_rates'] else 0.0
                
                # Get top revenue sources
                top_revenue_sources = analysis['revenue_sources'].most_common(3)
                
                # Calculate tier breakdown
                tier_breakdown = {}
                for tier, data in analysis['tier_breakdown'].items():
                    tier_breakdown[tier] = {
                        'revenue': data['revenue'],
                        'users': data['users'],
                        'revenue_per_user': data['revenue'] / data['users'] if data['users'] > 0 else 0.0
                    }
                
                results[feature_name] = {
                    'total_revenue': analysis['total_revenue'],
                    'attribution_count': analysis['attribution_count'],
                    'average_attribution': avg_attribution,
                    'average_conversion_rate': avg_conversion_rate,
                    'top_revenue_sources': [{'source': source, 'count': count} for source, count in top_revenue_sources],
                    'tier_breakdown': tier_breakdown,
                    'revenue_attribution_score': self._calculate_attribution_score(avg_attribution, avg_conversion_rate)
                }
            
            return {
                'time_period': time_period,
                'feature_analysis': results,
                'total_revenue_attributed': sum(analysis['total_revenue'] for analysis in feature_analysis.values()),
                'total_attributions': len(attributions)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing revenue attribution: {e}")
            return {"error": str(e)}
    
    def analyze_cost_per_connection(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze cost per connection"""
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
            
            # Filter cost per connections by time period
            costs = [
                cost for cost in self.cost_per_connections.values()
                if cost.analysis_date >= start_time
            ]
            
            if not costs:
                return {"error": "No cost per connection data available"}
            
            # Analyze by connection type
            connection_analysis = defaultdict(lambda: {
                'total_cost': 0.0,
                'total_connections': 0,
                'average_cost_per_connection': 0.0,
                'cost_breakdown': defaultdict(float),
                'optimization_opportunities': [],
                'trend_analysis': []
            })
            
            for cost in costs:
                connection_analysis[cost.connection_type]['total_cost'] += cost.total_cost
                connection_analysis[cost.connection_type]['total_connections'] += cost.total_connections
                
                # Aggregate cost breakdown
                for cost_type, amount in cost.cost_breakdown.items():
                    connection_analysis[cost.connection_type]['cost_breakdown'][cost_type.value] += amount
                
                # Collect optimization opportunities
                connection_analysis[cost.connection_type]['optimization_opportunities'].extend(cost.optimization_opportunities)
            
            # Calculate metrics
            results = {}
            for connection_type, analysis in connection_analysis.items():
                avg_cost_per_connection = analysis['total_cost'] / analysis['total_connections'] if analysis['total_connections'] > 0 else 0.0
                
                # Get top cost contributors
                top_cost_contributors = sorted(analysis['cost_breakdown'].items(), key=lambda x: x[1], reverse=True)[:3]
                
                # Remove duplicate optimization opportunities
                unique_opportunities = list(set(analysis['optimization_opportunities']))
                
                results[connection_type] = {
                    'total_cost': analysis['total_cost'],
                    'total_connections': analysis['total_connections'],
                    'average_cost_per_connection': avg_cost_per_connection,
                    'top_cost_contributors': [{'cost_type': cost_type, 'amount': amount} for cost_type, amount in top_cost_contributors],
                    'optimization_opportunities': unique_opportunities,
                    'cost_efficiency_score': self._calculate_cost_efficiency_score(avg_cost_per_connection, analysis['total_connections'])
                }
            
            return {
                'time_period': time_period,
                'connection_analysis': results,
                'total_cost': sum(analysis['total_cost'] for analysis in connection_analysis.values()),
                'total_connections': sum(analysis['total_connections'] for analysis in connection_analysis.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cost per connection: {e}")
            return {"error": str(e)}
    
    def analyze_plaid_api_optimization(self, time_period: str = "30d") -> Dict[str, Any]:
        """Analyze Plaid API usage optimization"""
        try:
            end_time = datetime.utcnow()
            if time_period == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            else:
                start_time = end_time - timedelta(days=30)
            
            # Filter Plaid API usage by time period
            api_usage = [
                usage for usage in self.plaid_api_usage.values()
                if usage.usage_date >= start_time
            ]
            
            if not api_usage:
                return {"error": "No Plaid API usage data available"}
            
            # Analyze by API endpoint
            endpoint_analysis = defaultdict(lambda: {
                'total_requests': 0,
                'total_cost': 0.0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_response_time': 0.0,
                'optimization_recommendations': [],
                'usage_trends': []
            })
            
            for usage in api_usage:
                endpoint_analysis[usage.api_endpoint]['total_requests'] += usage.request_count
                endpoint_analysis[usage.api_endpoint]['total_cost'] += usage.total_cost
                endpoint_analysis[usage.api_endpoint]['successful_requests'] += int(usage.request_count * usage.success_rate)
                endpoint_analysis[usage.api_endpoint]['failed_requests'] += int(usage.request_count * usage.error_rate)
                endpoint_analysis[usage.api_endpoint]['total_response_time'] += usage.average_response_time * usage.request_count
                endpoint_analysis[usage.api_endpoint]['optimization_recommendations'].extend(usage.optimization_recommendations)
            
            # Calculate metrics
            results = {}
            for endpoint, analysis in endpoint_analysis.items():
                success_rate = analysis['successful_requests'] / analysis['total_requests'] if analysis['total_requests'] > 0 else 0.0
                error_rate = analysis['failed_requests'] / analysis['total_requests'] if analysis['total_requests'] > 0 else 0.0
                avg_response_time = analysis['total_response_time'] / analysis['total_requests'] if analysis['total_requests'] > 0 else 0.0
                cost_per_request = analysis['total_cost'] / analysis['total_requests'] if analysis['total_requests'] > 0 else 0.0
                
                # Remove duplicate optimization recommendations
                unique_recommendations = list(set(analysis['optimization_recommendations']))
                
                results[endpoint] = {
                    'total_requests': analysis['total_requests'],
                    'total_cost': analysis['total_cost'],
                    'success_rate': success_rate,
                    'error_rate': error_rate,
                    'average_response_time': avg_response_time,
                    'cost_per_request': cost_per_request,
                    'optimization_recommendations': unique_recommendations,
                    'api_efficiency_score': self._calculate_api_efficiency_score(success_rate, avg_response_time, cost_per_request)
                }
            
            return {
                'time_period': time_period,
                'endpoint_analysis': results,
                'total_api_requests': sum(analysis['total_requests'] for analysis in endpoint_analysis.values()),
                'total_api_cost': sum(analysis['total_cost'] for analysis in endpoint_analysis.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Plaid API optimization: {e}")
            return {"error": str(e)}
    
    def analyze_feature_development_priorities(self) -> Dict[str, Any]:
        """Analyze feature development prioritization"""
        try:
            # Get all feature priorities
            priorities = list(self.feature_priorities.values())
            
            if not priorities:
                return {"error": "No feature development priority data available"}
            
            # Analyze by development phase
            phase_analysis = defaultdict(lambda: {
                'features': [],
                'total_priority_score': 0.0,
                'average_priority_score': 0.0,
                'total_estimated_roi': 0.0,
                'average_estimated_roi': 0.0,
                'development_effort_distribution': [],
                'business_value_distribution': []
            })
            
            for priority in priorities:
                phase_analysis[priority.development_phase]['features'].append({
                    'feature_name': priority.feature_name,
                    'business_value': priority.business_value,
                    'development_effort': priority.development_effort,
                    'technical_risk': priority.technical_risk,
                    'market_demand': priority.market_demand,
                    'competitive_advantage': priority.competitive_advantage,
                    'priority_score': priority.priority_score,
                    'estimated_roi': priority.estimated_roi
                })
                phase_analysis[priority.development_phase]['total_priority_score'] += priority.priority_score
                phase_analysis[priority.development_phase]['total_estimated_roi'] += priority.estimated_roi
                phase_analysis[priority.development_phase]['development_effort_distribution'].append(priority.development_effort)
                phase_analysis[priority.development_phase]['business_value_distribution'].append(priority.business_value)
            
            # Calculate metrics
            results = {}
            for phase, analysis in phase_analysis.items():
                feature_count = len(analysis['features'])
                avg_priority_score = analysis['total_priority_score'] / feature_count if feature_count > 0 else 0.0
                avg_estimated_roi = analysis['total_estimated_roi'] / feature_count if feature_count > 0 else 0.0
                avg_development_effort = statistics.mean(analysis['development_effort_distribution']) if analysis['development_effort_distribution'] else 0.0
                avg_business_value = statistics.mean(analysis['business_value_distribution']) if analysis['business_value_distribution'] else 0.0
                
                # Sort features by priority score
                analysis['features'].sort(key=lambda x: x['priority_score'], reverse=True)
                
                # Get top features
                analysis['top_features'] = analysis['features'][:5]
                
                results[phase] = {
                    'feature_count': feature_count,
                    'average_priority_score': avg_priority_score,
                    'average_estimated_roi': avg_estimated_roi,
                    'average_development_effort': avg_development_effort,
                    'average_business_value': avg_business_value,
                    'top_features': analysis['top_features'],
                    'development_priority_score': self._calculate_development_priority_score(avg_priority_score, avg_estimated_roi, avg_business_value)
                }
            
            return {
                'phase_analysis': results,
                'total_features': len(priorities),
                'average_priority_score': statistics.mean([p.priority_score for p in priorities]),
                'average_estimated_roi': statistics.mean([p.estimated_roi for p in priorities])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing feature development priorities: {e}")
            return {"error": str(e)}
    
    def analyze_competitive_analysis(self) -> Dict[str, Any]:
        """Analyze competitive analysis"""
        try:
            # Get all competitive analyses
            analyses = list(self.competitive_analyses.values())
            
            if not analyses:
                return {"error": "No competitive analysis data available"}
            
            # Analyze by competitor
            competitor_analysis = {}
            
            for analysis in analyses:
                competitor_analysis[analysis.competitor_name] = {
                    'market_share': analysis.market_share,
                    'competitive_position': analysis.competitive_position,
                    'pricing_strategy': analysis.pricing_strategy,
                    'technology_stack': analysis.technology_stack,
                    'strengths': analysis.strengths,
                    'weaknesses': analysis.weaknesses,
                    'opportunities': analysis.opportunities,
                    'threats': analysis.threats,
                    'feature_comparison': analysis.feature_comparison,
                    'competitive_score': self._calculate_competitive_score(analysis)
                }
            
            # Calculate market positioning
            total_market_share = sum(analysis['market_share'] for analysis in competitor_analysis.values())
            market_positioning = {
                'total_market_share_analyzed': total_market_share,
                'competitor_count': len(competitor_analysis),
                'average_market_share': total_market_share / len(competitor_analysis) if competitor_analysis else 0.0,
                'market_leader': max(competitor_analysis.items(), key=lambda x: x[1]['market_share'])[0] if competitor_analysis else None
            }
            
            return {
                'competitor_analysis': competitor_analysis,
                'market_positioning': market_positioning,
                'total_analyses': len(analyses)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitive analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_attribution_score(self, avg_attribution: float, avg_conversion_rate: float) -> float:
        """Calculate revenue attribution score"""
        try:
            # Normalize attribution and conversion rate to 0-1 scale
            normalized_attribution = min(1.0, avg_attribution / 1000)  # Assuming $1000 is max
            normalized_conversion = avg_conversion_rate
            
            # Weighted score
            attribution_score = (normalized_attribution * 0.6) + (normalized_conversion * 0.4)
            return min(1.0, max(0.0, attribution_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating attribution score: {e}")
            return 0.0
    
    def _calculate_cost_efficiency_score(self, avg_cost_per_connection: float, total_connections: int) -> float:
        """Calculate cost efficiency score"""
        try:
            # Lower cost per connection is better
            normalized_cost = max(0.0, 1.0 - (avg_cost_per_connection / 10.0))  # Assuming $10 is max
            normalized_volume = min(1.0, total_connections / 10000)  # Assuming 10k connections is max
            
            # Weighted score
            efficiency_score = (normalized_cost * 0.7) + (normalized_volume * 0.3)
            return min(1.0, max(0.0, efficiency_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating cost efficiency score: {e}")
            return 0.0
    
    def _calculate_api_efficiency_score(self, success_rate: float, avg_response_time: float, cost_per_request: float) -> float:
        """Calculate API efficiency score"""
        try:
            # Normalize metrics
            normalized_success = success_rate
            normalized_response = max(0.0, 1.0 - (avg_response_time / 5000))  # Assuming 5s is max
            normalized_cost = max(0.0, 1.0 - (cost_per_request / 1.0))  # Assuming $1 is max
            
            # Weighted score
            efficiency_score = (normalized_success * 0.4) + (normalized_response * 0.3) + (normalized_cost * 0.3)
            return min(1.0, max(0.0, efficiency_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating API efficiency score: {e}")
            return 0.0
    
    def _calculate_development_priority_score(self, avg_priority_score: float, avg_estimated_roi: float, avg_business_value: float) -> float:
        """Calculate development priority score"""
        try:
            # Normalize metrics
            normalized_priority = avg_priority_score
            normalized_roi = min(1.0, avg_estimated_roi / 100)  # Assuming 100% ROI is max
            normalized_value = avg_business_value
            
            # Weighted score
            priority_score = (normalized_priority * 0.4) + (normalized_roi * 0.3) + (normalized_value * 0.3)
            return min(1.0, max(0.0, priority_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating development priority score: {e}")
            return 0.0
    
    def _calculate_competitive_score(self, analysis: CompetitiveAnalysis) -> float:
        """Calculate competitive score"""
        try:
            # Score based on market share and competitive position
            market_share_score = min(1.0, analysis.market_share / 50.0)  # Assuming 50% is max
            
            position_scores = {
                'leader': 1.0,
                'strong': 0.8,
                'moderate': 0.6,
                'weak': 0.4,
                'challenger': 0.2
            }
            position_score = position_scores.get(analysis.competitive_position, 0.5)
            
            # Weighted score
            competitive_score = (market_share_score * 0.6) + (position_score * 0.4)
            return min(1.0, max(0.0, competitive_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating competitive score: {e}")
            return 0.0
    
    def record_revenue_attribution(self, feature_name: str, subscription_tier: str,
                                 revenue_amount: float, revenue_source: RevenueSource,
                                 attribution_percentage: float, attribution_method: str,
                                 user_count: int, conversion_rate: float,
                                 metadata: Dict[str, Any] = None) -> str:
        """Record revenue attribution"""
        try:
            attribution_id = f"attribution_{int(time.time())}_{secrets.token_hex(4)}"
            
            revenue_attribution = RevenueAttribution(
                attribution_id=attribution_id,
                feature_name=feature_name,
                subscription_tier=subscription_tier,
                revenue_amount=revenue_amount,
                revenue_source=revenue_source,
                attribution_percentage=attribution_percentage,
                attribution_method=attribution_method,
                attribution_date=datetime.utcnow(),
                user_count=user_count,
                conversion_rate=conversion_rate,
                metadata=metadata or {}
            )
            
            self.revenue_attributions[attribution_id] = revenue_attribution
            
            # Log revenue attribution
            self.audit_service.log_event(
                event_type=AuditEventType.REVENUE_ATTRIBUTION,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Revenue attribution recorded for feature {feature_name}",
                resource_type="revenue_attribution",
                resource_id=attribution_id,
                user_id=None,
                metadata={
                    'feature_name': feature_name,
                    'revenue_amount': revenue_amount,
                    'attribution_percentage': attribution_percentage
                }
            )
            
            return attribution_id
            
        except Exception as e:
            self.logger.error(f"Error recording revenue attribution: {e}")
            raise
    
    def get_business_intelligence_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive business intelligence dashboard data"""
        try:
            # Get various business intelligence analyses
            revenue_attribution = self.analyze_revenue_attribution("90d")
            cost_per_connection = self.analyze_cost_per_connection("90d")
            plaid_api_optimization = self.analyze_plaid_api_optimization("30d")
            feature_priorities = self.analyze_feature_development_priorities()
            competitive_analysis = self.analyze_competitive_analysis()
            
            # Get recent ROI and profitability analyses
            recent_roi_analyses = [
                {
                    'roi_id': roi.roi_id,
                    'investment_type': roi.investment_type,
                    'roi_percentage': roi.roi_percentage,
                    'payback_period': roi.payback_period,
                    'analysis_date': roi.analysis_date.isoformat()
                }
                for roi in self.roi_analyses.values()
                if roi.analysis_date >= datetime.utcnow() - timedelta(days=30)
            ]
            
            recent_profitability_analyses = [
                {
                    'profitability_id': prof.profitability_id,
                    'revenue_stream': prof.revenue_stream,
                    'profit_margin': prof.profit_margin,
                    'gross_margin': prof.gross_margin,
                    'analysis_date': prof.analysis_date.isoformat()
                }
                for prof in self.profitability_analyses.values()
                if prof.analysis_date >= datetime.utcnow() - timedelta(days=30)
            ]
            
            return {
                'revenue_attribution': revenue_attribution,
                'cost_per_connection': cost_per_connection,
                'plaid_api_optimization': plaid_api_optimization,
                'feature_priorities': feature_priorities,
                'competitive_analysis': competitive_analysis,
                'recent_roi_analyses': recent_roi_analyses,
                'recent_profitability_analyses': recent_profitability_analyses,
                'total_attributions': len(self.revenue_attributions),
                'total_costs': len(self.cost_per_connections),
                'total_api_usage': len(self.plaid_api_usage),
                'total_features': len(self.feature_priorities),
                'total_competitors': len(self.competitive_analyses),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting business intelligence dashboard: {e}")
            return {"error": str(e)}
    
    def _update_revenue_attributions(self):
        """Update revenue attributions"""
        try:
            # This would update revenue attributions
            # For now, we'll just log the update
            self.logger.info("Revenue attribution update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating revenue attributions: {e}")
    
    def _update_cost_per_connection_analysis(self):
        """Update cost per connection analysis"""
        try:
            # This would update cost per connection analysis
            # For now, we'll just log the update
            self.logger.info("Cost per connection analysis update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating cost per connection analysis: {e}")
    
    def _update_plaid_api_optimization(self):
        """Update Plaid API optimization"""
        try:
            # This would update Plaid API optimization
            # For now, we'll just log the update
            self.logger.info("Plaid API optimization update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating Plaid API optimization: {e}")
    
    def _update_feature_development_priorities(self):
        """Update feature development priorities"""
        try:
            # This would update feature development priorities
            # For now, we'll just log the update
            self.logger.info("Feature development priorities update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating feature development priorities: {e}")
    
    def _update_competitive_analysis(self):
        """Update competitive analysis"""
        try:
            # This would update competitive analysis
            # For now, we'll just log the update
            self.logger.info("Competitive analysis update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating competitive analysis: {e}") 