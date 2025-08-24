"""
Subscription Conversion Analytics System

This module provides comprehensive subscription conversion analytics including trial-to-paid
conversion impact of banking features, tier upgrade rates after bank connection, banking
feature usage correlation with upgrades, churn reduction from banking engagement, and
customer lifetime value impact.
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
from backend.models.subscription_models import Subscription, SubscriptionTier
from backend.models.analytics_models import AnalyticsEvent, UserBehavior
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity

logger = logging.getLogger(__name__)


class ConversionMetric(Enum):
    """Conversion metrics for subscription analytics"""
    TRIAL_TO_PAID = "trial_to_paid"
    TIER_UPGRADE = "tier_upgrade"
    FEATURE_USAGE_CORRELATION = "feature_usage_correlation"
    CHURN_REDUCTION = "churn_reduction"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    CONVERSION_FUNNEL = "conversion_funnel"
    REVENUE_IMPACT = "revenue_impact"


class ConversionStage(Enum):
    """Conversion funnel stages"""
    TRIAL_START = "trial_start"
    BANK_CONNECTION = "bank_connection"
    FEATURE_USAGE = "feature_usage"
    TRIAL_CONVERSION = "trial_conversion"
    TIER_UPGRADE = "tier_upgrade"
    CHURN = "churn"


@dataclass
class TrialConversionData:
    """Trial-to-paid conversion data"""
    conversion_id: str
    user_id: str
    trial_start_date: datetime
    trial_end_date: datetime
    conversion_date: Optional[datetime]
    converted: bool
    subscription_tier: str
    banking_features_used: List[str]
    bank_connection_date: Optional[datetime]
    conversion_reason: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierUpgradeData:
    """Tier upgrade data"""
    upgrade_id: str
    user_id: str
    from_tier: str
    to_tier: str
    upgrade_date: datetime
    bank_connection_date: Optional[datetime]
    days_since_connection: Optional[int]
    banking_features_used: List[str]
    upgrade_reason: str
    revenue_impact: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureUsageCorrelationData:
    """Feature usage correlation with upgrades data"""
    correlation_id: str
    user_id: str
    feature_name: str
    usage_count: int
    usage_frequency: float
    upgrade_occurred: bool
    upgrade_date: Optional[datetime]
    days_to_upgrade: Optional[int]
    correlation_strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChurnReductionData:
    """Churn reduction from banking engagement data"""
    churn_id: str
    user_id: str
    subscription_tier: str
    engagement_score: float
    banking_features_used: List[str]
    churn_risk_before: float
    churn_risk_after: float
    churn_reduction: float
    retained: bool
    retention_date: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerLifetimeValueData:
    """Customer lifetime value impact data"""
    clv_id: str
    user_id: str
    subscription_tier: str
    initial_clv: float
    current_clv: float
    clv_increase: float
    banking_features_used: List[str]
    engagement_score: float
    retention_months: int
    total_revenue: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionInsight:
    """Conversion insight structure"""
    insight_id: str
    insight_type: str
    metric: ConversionMetric
    severity: str  # low, medium, high, critical
    description: str
    recommendation: str
    impact_score: float
    affected_tier: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubscriptionConversionAnalytics:
    """Comprehensive subscription conversion analytics system"""
    
    def __init__(self, db_session: Session, access_control_service: AccessControlService,
                 audit_service: AuditLoggingService):
        self.db = db_session
        self.access_control_service = access_control_service
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize data storage
        self.trial_conversion_data = self._initialize_trial_conversion_data()
        self.tier_upgrade_data = self._initialize_tier_upgrade_data()
        self.feature_usage_correlation_data = self._initialize_feature_usage_correlation_data()
        self.churn_reduction_data = self._initialize_churn_reduction_data()
        self.customer_lifetime_value_data = self._initialize_customer_lifetime_value_data()
        self.conversion_insights = self._initialize_conversion_insights()
        
        # Conversion thresholds
        self.conversion_thresholds = self._initialize_conversion_thresholds()
        
        # Start conversion monitoring
        self._start_conversion_monitoring()
    
    def _initialize_trial_conversion_data(self) -> Dict[str, TrialConversionData]:
        """Initialize trial conversion data storage"""
        return {}
    
    def _initialize_tier_upgrade_data(self) -> Dict[str, TierUpgradeData]:
        """Initialize tier upgrade data storage"""
        return {}
    
    def _initialize_feature_usage_correlation_data(self) -> Dict[str, FeatureUsageCorrelationData]:
        """Initialize feature usage correlation data storage"""
        return {}
    
    def _initialize_churn_reduction_data(self) -> Dict[str, ChurnReductionData]:
        """Initialize churn reduction data storage"""
        return {}
    
    def _initialize_customer_lifetime_value_data(self) -> Dict[str, CustomerLifetimeValueData]:
        """Initialize customer lifetime value data storage"""
        return {}
    
    def _initialize_conversion_insights(self) -> Dict[str, ConversionInsight]:
        """Initialize conversion insights storage"""
        return {}
    
    def _initialize_conversion_thresholds(self) -> Dict[ConversionMetric, Dict[str, float]]:
        """Initialize conversion thresholds"""
        return {
            ConversionMetric.TRIAL_TO_PAID: {
                'warning': 0.15,
                'critical': 0.10
            },
            ConversionMetric.TIER_UPGRADE: {
                'warning': 0.05,
                'critical': 0.03
            },
            ConversionMetric.CHURN_REDUCTION: {
                'warning': 0.20,
                'critical': 0.10
            },
            ConversionMetric.CUSTOMER_LIFETIME_VALUE: {
                'warning': 0.25,
                'critical': 0.15
            }
        }
    
    def _start_conversion_monitoring(self):
        """Start conversion monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_conversion, daemon=True)
            monitoring_thread.start()
            self.logger.info("Subscription conversion analytics monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting conversion monitoring: {e}")
    
    def _monitor_conversion(self):
        """Monitor conversion metrics and generate insights"""
        while True:
            try:
                # Generate conversion insights
                self._generate_conversion_insights()
                
                # Update conversion correlations
                self._update_conversion_correlations()
                
                # Sleep for monitoring interval
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in conversion monitoring: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def record_trial_conversion(self, user_id: str, trial_start_date: datetime,
                              trial_end_date: datetime, converted: bool,
                              subscription_tier: str, banking_features_used: List[str],
                              bank_connection_date: datetime = None,
                              conversion_date: datetime = None,
                              conversion_reason: str = None,
                              metadata: Dict[str, Any] = None) -> str:
        """Record trial-to-paid conversion data"""
        try:
            conversion_id = f"trial_{int(time.time())}_{secrets.token_hex(4)}"
            
            conversion_data = TrialConversionData(
                conversion_id=conversion_id,
                user_id=user_id,
                trial_start_date=trial_start_date,
                trial_end_date=trial_end_date,
                conversion_date=conversion_date,
                converted=converted,
                subscription_tier=subscription_tier,
                banking_features_used=banking_features_used,
                bank_connection_date=bank_connection_date,
                conversion_reason=conversion_reason,
                metadata=metadata or {}
            )
            
            self.trial_conversion_data[conversion_id] = conversion_data
            
            # Log trial conversion
            self.audit_service.log_event(
                event_type=AuditEventType.TRIAL_CONVERSION,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Trial conversion recorded for user {user_id}",
                resource_type="trial_conversion",
                resource_id=conversion_id,
                user_id=user_id,
                metadata={
                    'converted': converted,
                    'subscription_tier': subscription_tier,
                    'banking_features_used': banking_features_used
                }
            )
            
            return conversion_id
            
        except Exception as e:
            self.logger.error(f"Error recording trial conversion: {e}")
            raise
    
    def record_tier_upgrade(self, user_id: str, from_tier: str, to_tier: str,
                          upgrade_date: datetime, bank_connection_date: datetime = None,
                          banking_features_used: List[str] = None,
                          upgrade_reason: str = None, revenue_impact: float = 0.0,
                          metadata: Dict[str, Any] = None) -> str:
        """Record tier upgrade data"""
        try:
            upgrade_id = f"upgrade_{int(time.time())}_{secrets.token_hex(4)}"
            
            # Calculate days since bank connection
            days_since_connection = None
            if bank_connection_date:
                days_since_connection = (upgrade_date - bank_connection_date).days
            
            upgrade_data = TierUpgradeData(
                upgrade_id=upgrade_id,
                user_id=user_id,
                from_tier=from_tier,
                to_tier=to_tier,
                upgrade_date=upgrade_date,
                bank_connection_date=bank_connection_date,
                days_since_connection=days_since_connection,
                banking_features_used=banking_features_used or [],
                upgrade_reason=upgrade_reason or "user_initiated",
                revenue_impact=revenue_impact,
                metadata=metadata or {}
            )
            
            self.tier_upgrade_data[upgrade_id] = upgrade_data
            
            # Log tier upgrade
            self.audit_service.log_event(
                event_type=AuditEventType.TIER_UPGRADE,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Tier upgrade recorded for user {user_id}",
                resource_type="tier_upgrade",
                resource_id=upgrade_id,
                user_id=user_id,
                metadata={
                    'from_tier': from_tier,
                    'to_tier': to_tier,
                    'revenue_impact': revenue_impact,
                    'banking_features_used': banking_features_used
                }
            )
            
            return upgrade_id
            
        except Exception as e:
            self.logger.error(f"Error recording tier upgrade: {e}")
            raise
    
    def analyze_trial_to_paid_conversion(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze trial-to-paid conversion impact of banking features"""
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
            
            # Filter trial conversion data by time period
            conversion_data = [
                data for data in self.trial_conversion_data.values()
                if data.trial_start_date >= start_time
            ]
            
            if not conversion_data:
                return {"error": "No trial conversion data available"}
            
            # Analyze conversion rates
            total_trials = len(conversion_data)
            converted_trials = len([data for data in conversion_data if data.converted])
            overall_conversion_rate = converted_trials / total_trials if total_trials > 0 else 0
            
            # Analyze by banking features
            feature_analysis = defaultdict(lambda: {
                'total_trials': 0,
                'converted_trials': 0,
                'conversion_rate': 0.0,
                'users': set()
            })
            
            for data in conversion_data:
                feature_analysis['all_trials']['total_trials'] += 1
                feature_analysis['all_trials']['users'].add(data.user_id)
                if data.converted:
                    feature_analysis['all_trials']['converted_trials'] += 1
                
                # Analyze by banking features used
                for feature in data.banking_features_used:
                    feature_analysis[feature]['total_trials'] += 1
                    feature_analysis[feature]['users'].add(data.user_id)
                    if data.converted:
                        feature_analysis[feature]['converted_trials'] += 1
            
            # Calculate conversion rates
            for feature, analysis in feature_analysis.items():
                analysis['conversion_rate'] = analysis['converted_trials'] / analysis['total_trials'] if analysis['total_trials'] > 0 else 0
            
            # Analyze by bank connection
            with_connection = [data for data in conversion_data if data.bank_connection_date]
            without_connection = [data for data in conversion_data if not data.bank_connection_date]
            
            connection_conversion_rate = len([data for data in with_connection if data.converted]) / len(with_connection) if with_connection else 0
            no_connection_conversion_rate = len([data for data in without_connection if data.converted]) / len(without_connection) if without_connection else 0
            
            return {
                'time_period': time_period,
                'overall_conversion_rate': overall_conversion_rate,
                'total_trials': total_trials,
                'converted_trials': converted_trials,
                'feature_analysis': dict(feature_analysis),
                'connection_impact': {
                    'with_connection': {
                        'total_trials': len(with_connection),
                        'converted_trials': len([data for data in with_connection if data.converted]),
                        'conversion_rate': connection_conversion_rate
                    },
                    'without_connection': {
                        'total_trials': len(without_connection),
                        'converted_trials': len([data for data in without_connection if data.converted]),
                        'conversion_rate': no_connection_conversion_rate
                    },
                    'impact_multiplier': connection_conversion_rate / no_connection_conversion_rate if no_connection_conversion_rate > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trial-to-paid conversion: {e}")
            return {"error": str(e)}
    
    def analyze_tier_upgrade_rates(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze tier upgrade rates after bank connection"""
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
            
            # Filter upgrade data by time period
            upgrade_data = [
                data for data in self.tier_upgrade_data.values()
                if data.upgrade_date >= start_time
            ]
            
            if not upgrade_data:
                return {"error": "No tier upgrade data available"}
            
            # Analyze by tier and bank connection
            tier_analysis = defaultdict(lambda: {
                'total_users': 0,
                'upgraded_users': 0,
                'upgrade_rate': 0.0,
                'avg_days_since_connection': [],
                'revenue_impact': 0.0,
                'banking_features_used': Counter()
            })
            
            for data in upgrade_data:
                tier_analysis[data.from_tier]['total_users'] += 1
                tier_analysis[data.from_tier]['upgraded_users'] += 1
                tier_analysis[data.from_tier]['revenue_impact'] += data.revenue_impact
                
                if data.days_since_connection:
                    tier_analysis[data.from_tier]['avg_days_since_connection'].append(data.days_since_connection)
                
                for feature in data.banking_features_used:
                    tier_analysis[data.from_tier]['banking_features_used'][feature] += 1
            
            # Calculate metrics
            results = {}
            for tier, analysis in tier_analysis.items():
                avg_days_since_connection = statistics.mean(analysis['avg_days_since_connection']) if analysis['avg_days_since_connection'] else 0
                
                results[tier] = {
                    'total_users': analysis['total_users'],
                    'upgraded_users': analysis['upgraded_users'],
                    'upgrade_rate': analysis['upgrade_rate'],
                    'average_days_since_connection': avg_days_since_connection,
                    'total_revenue_impact': analysis['revenue_impact'],
                    'average_revenue_impact': analysis['revenue_impact'] / analysis['upgraded_users'] if analysis['upgraded_users'] > 0 else 0,
                    'most_used_features': dict(analysis['banking_features_used'].most_common(5))
                }
            
            return {
                'time_period': time_period,
                'tier_analysis': results,
                'total_upgrades': len(upgrade_data),
                'total_revenue_impact': sum(data.revenue_impact for data in upgrade_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing tier upgrade rates: {e}")
            return {"error": str(e)}
    
    def analyze_feature_usage_correlation(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze banking feature usage correlation with upgrades"""
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
            
            # Filter correlation data by time period
            correlation_data = [
                data for data in self.feature_usage_correlation_data.values()
                if hasattr(data, 'timestamp') and data.timestamp >= start_time
            ]
            
            if not correlation_data:
                return {"error": "No feature usage correlation data available"}
            
            # Analyze by feature
            feature_analysis = defaultdict(lambda: {
                'total_users': 0,
                'upgraded_users': 0,
                'upgrade_rate': 0.0,
                'usage_counts': [],
                'usage_frequencies': [],
                'days_to_upgrade': [],
                'correlation_strengths': []
            })
            
            for data in correlation_data:
                feature_analysis[data.feature_name]['total_users'] += 1
                feature_analysis[data.feature_name]['usage_counts'].append(data.usage_count)
                feature_analysis[data.feature_name]['usage_frequencies'].append(data.usage_frequency)
                feature_analysis[data.feature_name]['correlation_strengths'].append(data.correlation_strength)
                
                if data.upgrade_occurred:
                    feature_analysis[data.feature_name]['upgraded_users'] += 1
                    if data.days_to_upgrade:
                        feature_analysis[data.feature_name]['days_to_upgrade'].append(data.days_to_upgrade)
            
            # Calculate metrics
            results = {}
            for feature_name, analysis in feature_analysis.items():
                upgrade_rate = analysis['upgraded_users'] / analysis['total_users'] if analysis['total_users'] > 0 else 0
                avg_usage_count = statistics.mean(analysis['usage_counts']) if analysis['usage_counts'] else 0
                avg_usage_frequency = statistics.mean(analysis['usage_frequencies']) if analysis['usage_frequencies'] else 0
                avg_days_to_upgrade = statistics.mean(analysis['days_to_upgrade']) if analysis['days_to_upgrade'] else 0
                avg_correlation_strength = statistics.mean(analysis['correlation_strengths']) if analysis['correlation_strengths'] else 0
                
                results[feature_name] = {
                    'total_users': analysis['total_users'],
                    'upgraded_users': analysis['upgraded_users'],
                    'upgrade_rate': upgrade_rate,
                    'average_usage_count': avg_usage_count,
                    'average_usage_frequency': avg_usage_frequency,
                    'average_days_to_upgrade': avg_days_to_upgrade,
                    'average_correlation_strength': avg_correlation_strength,
                    'correlation_interpretation': self._interpret_correlation(avg_correlation_strength)
                }
            
            return {
                'time_period': time_period,
                'feature_analysis': results,
                'total_features_analyzed': len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing feature usage correlation: {e}")
            return {"error": str(e)}
    
    def analyze_churn_reduction(self, time_period: str = "90d") -> Dict[str, Any]:
        """Analyze churn reduction from banking engagement"""
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
            
            # Filter churn reduction data by time period
            churn_data = [
                data for data in self.churn_reduction_data.values()
                if hasattr(data, 'timestamp') and data.timestamp >= start_time
            ]
            
            if not churn_data:
                return {"error": "No churn reduction data available"}
            
            # Analyze by tier
            tier_analysis = defaultdict(lambda: {
                'total_users': 0,
                'retained_users': 0,
                'retention_rate': 0.0,
                'avg_engagement_score': [],
                'avg_churn_reduction': [],
                'banking_features_used': Counter(),
                'engagement_levels': defaultdict(int)
            })
            
            for data in churn_data:
                tier_analysis[data.subscription_tier]['total_users'] += 1
                tier_analysis[data.subscription_tier]['avg_engagement_score'].append(data.engagement_score)
                tier_analysis[data.subscription_tier]['avg_churn_reduction'].append(data.churn_reduction)
                
                for feature in data.banking_features_used:
                    tier_analysis[data.subscription_tier]['banking_features_used'][feature] += 1
                
                # Categorize engagement level
                if data.engagement_score >= 80:
                    tier_analysis[data.subscription_tier]['engagement_levels']['high'] += 1
                elif data.engagement_score >= 50:
                    tier_analysis[data.subscription_tier]['engagement_levels']['medium'] += 1
                else:
                    tier_analysis[data.subscription_tier]['engagement_levels']['low'] += 1
                
                if data.retained:
                    tier_analysis[data.subscription_tier]['retained_users'] += 1
            
            # Calculate metrics
            results = {}
            for tier, analysis in tier_analysis.items():
                retention_rate = analysis['retained_users'] / analysis['total_users'] if analysis['total_users'] > 0 else 0
                avg_engagement = statistics.mean(analysis['avg_engagement_score']) if analysis['avg_engagement_score'] else 0
                avg_churn_reduction = statistics.mean(analysis['avg_churn_reduction']) if analysis['avg_churn_reduction'] else 0
                
                results[tier] = {
                    'total_users': analysis['total_users'],
                    'retained_users': analysis['retained_users'],
                    'retention_rate': retention_rate,
                    'average_engagement_score': avg_engagement,
                    'average_churn_reduction': avg_churn_reduction,
                    'engagement_level_distribution': dict(analysis['engagement_levels']),
                    'most_used_features': dict(analysis['banking_features_used'].most_common(5))
                }
            
            return {
                'time_period': time_period,
                'tier_analysis': results,
                'overall_retention_rate': sum(analysis['retained_users'] for analysis in tier_analysis.values()) / 
                                        sum(analysis['total_users'] for analysis in tier_analysis.values()) if any(analysis['total_users'] for analysis in tier_analysis.values()) else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing churn reduction: {e}")
            return {"error": str(e)}
    
    def analyze_customer_lifetime_value(self, time_period: str = "180d") -> Dict[str, Any]:
        """Analyze customer lifetime value impact"""
        try:
            end_time = datetime.utcnow()
            if time_period == "90d":
                start_time = end_time - timedelta(days=90)
            elif time_period == "180d":
                start_time = end_time - timedelta(days=180)
            elif time_period == "365d":
                start_time = end_time - timedelta(days=365)
            else:
                start_time = end_time - timedelta(days=180)
            
            # Filter CLV data by time period
            clv_data = [
                data for data in self.customer_lifetime_value_data.values()
                if hasattr(data, 'timestamp') and data.timestamp >= start_time
            ]
            
            if not clv_data:
                return {"error": "No customer lifetime value data available"}
            
            # Analyze by tier
            tier_analysis = defaultdict(lambda: {
                'total_customers': 0,
                'total_revenue': 0.0,
                'avg_initial_clv': [],
                'avg_current_clv': [],
                'avg_clv_increase': [],
                'avg_engagement_score': [],
                'avg_retention_months': [],
                'banking_features_used': Counter()
            })
            
            for data in clv_data:
                tier_analysis[data.subscription_tier]['total_customers'] += 1
                tier_analysis[data.subscription_tier]['total_revenue'] += data.total_revenue
                tier_analysis[data.subscription_tier]['avg_initial_clv'].append(data.initial_clv)
                tier_analysis[data.subscription_tier]['avg_current_clv'].append(data.current_clv)
                tier_analysis[data.subscription_tier]['avg_clv_increase'].append(data.clv_increase)
                tier_analysis[data.subscription_tier]['avg_engagement_score'].append(data.engagement_score)
                tier_analysis[data.subscription_tier]['avg_retention_months'].append(data.retention_months)
                
                for feature in data.banking_features_used:
                    tier_analysis[data.subscription_tier]['banking_features_used'][feature] += 1
            
            # Calculate metrics
            results = {}
            for tier, analysis in tier_analysis.items():
                avg_initial_clv = statistics.mean(analysis['avg_initial_clv']) if analysis['avg_initial_clv'] else 0
                avg_current_clv = statistics.mean(analysis['avg_current_clv']) if analysis['avg_current_clv'] else 0
                avg_clv_increase = statistics.mean(analysis['avg_clv_increase']) if analysis['avg_clv_increase'] else 0
                avg_engagement = statistics.mean(analysis['avg_engagement_score']) if analysis['avg_engagement_score'] else 0
                avg_retention = statistics.mean(analysis['avg_retention_months']) if analysis['avg_retention_months'] else 0
                
                results[tier] = {
                    'total_customers': analysis['total_customers'],
                    'total_revenue': analysis['total_revenue'],
                    'average_initial_clv': avg_initial_clv,
                    'average_current_clv': avg_current_clv,
                    'average_clv_increase': avg_clv_increase,
                    'clv_increase_percentage': (avg_clv_increase / avg_initial_clv * 100) if avg_initial_clv > 0 else 0,
                    'average_engagement_score': avg_engagement,
                    'average_retention_months': avg_retention,
                    'most_used_features': dict(analysis['banking_features_used'].most_common(5))
                }
            
            return {
                'time_period': time_period,
                'tier_analysis': results,
                'total_customers': sum(analysis['total_customers'] for analysis in tier_analysis.values()),
                'total_revenue': sum(analysis['total_revenue'] for analysis in tier_analysis.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing customer lifetime value: {e}")
            return {"error": str(e)}
    
    def _interpret_correlation(self, correlation_strength: float) -> str:
        """Interpret correlation strength"""
        if abs(correlation_strength) >= 0.7:
            return "strong"
        elif abs(correlation_strength) >= 0.4:
            return "moderate"
        elif abs(correlation_strength) >= 0.2:
            return "weak"
        else:
            return "negligible"
    
    def _generate_conversion_insights(self):
        """Generate conversion insights"""
        try:
            # Analyze trial conversion rates
            trial_analysis = self.analyze_trial_to_paid_conversion("90d")
            
            if 'error' not in trial_analysis:
                overall_rate = trial_analysis['overall_conversion_rate']
                
                if overall_rate < self.conversion_thresholds[ConversionMetric.TRIAL_TO_PAID]['critical']:
                    insight_id = f"insight_{int(time.time())}_{secrets.token_hex(4)}"
                    
                    insight = ConversionInsight(
                        insight_id=insight_id,
                        insight_type="trial_conversion",
                        metric=ConversionMetric.TRIAL_TO_PAID,
                        severity="critical",
                        description=f"Critical trial conversion rate: {overall_rate:.2%}",
                        recommendation="Implement immediate conversion optimization strategies",
                        impact_score=0.9,
                        affected_tier=None,
                        timestamp=datetime.utcnow(),
                        metadata={'conversion_rate': overall_rate}
                    )
                    
                    self.conversion_insights[insight_id] = insight
            
            # Analyze tier upgrade rates
            upgrade_analysis = self.analyze_tier_upgrade_rates("90d")
            
            if 'error' not in upgrade_analysis:
                for tier, data in upgrade_analysis['tier_analysis'].items():
                    if data['upgrade_rate'] < self.conversion_thresholds[ConversionMetric.TIER_UPGRADE]['warning']:
                        insight_id = f"insight_{int(time.time())}_{secrets.token_hex(4)}"
                        
                        insight = ConversionInsight(
                            insight_id=insight_id,
                            insight_type="tier_upgrade",
                            metric=ConversionMetric.TIER_UPGRADE,
                            severity="medium",
                            description=f"Low tier upgrade rate for {tier}: {data['upgrade_rate']:.2%}",
                            recommendation=f"Implement upgrade incentives for {tier} tier users",
                            impact_score=0.6,
                            affected_tier=tier,
                            timestamp=datetime.utcnow(),
                            metadata={'upgrade_rate': data['upgrade_rate']}
                        )
                        
                        self.conversion_insights[insight_id] = insight
                        
        except Exception as e:
            self.logger.error(f"Error generating conversion insights: {e}")
    
    def _update_conversion_correlations(self):
        """Update conversion correlations"""
        try:
            # This would update conversion correlation data with new user behavior
            # For now, we'll just log the update
            self.logger.info("Conversion correlations update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating conversion correlations: {e}")
    
    def get_conversion_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive conversion dashboard data"""
        try:
            # Get various conversion analytics
            trial_conversion = self.analyze_trial_to_paid_conversion("90d")
            tier_upgrades = self.analyze_tier_upgrade_rates("90d")
            feature_correlation = self.analyze_feature_usage_correlation("90d")
            churn_reduction = self.analyze_churn_reduction("90d")
            customer_lifetime_value = self.analyze_customer_lifetime_value("180d")
            
            # Get recent insights
            recent_insights = [
                {
                    'insight_id': insight.insight_id,
                    'insight_type': insight.insight_type,
                    'metric': insight.metric.value,
                    'severity': insight.severity,
                    'description': insight.description,
                    'recommendation': insight.recommendation,
                    'impact_score': insight.impact_score,
                    'affected_tier': insight.affected_tier,
                    'timestamp': insight.timestamp.isoformat()
                }
                for insight in self.conversion_insights.values()
                if insight.timestamp >= datetime.utcnow() - timedelta(days=7)
            ]
            
            return {
                'trial_conversion': trial_conversion,
                'tier_upgrades': tier_upgrades,
                'feature_correlation': feature_correlation,
                'churn_reduction': churn_reduction,
                'customer_lifetime_value': customer_lifetime_value,
                'recent_insights': recent_insights,
                'total_insights': len(self.conversion_insights),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conversion dashboard data: {e}")
            return {"error": str(e)} 