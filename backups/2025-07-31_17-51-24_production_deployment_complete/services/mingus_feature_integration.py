"""
MINGUS Feature Integration Service
Handles integration with MINGUS features including feature access control,
usage limit adjustments, data retention policies, and analytics updates
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func, update
import json

from ..models.subscription import (
    Customer, Subscription, PricingTier, FeatureUsage,
    AuditLog, AuditEventType, AuditSeverity
)
from ..models.user import User, UserProfile
from ..models.user_health_checkin import UserHealthCheckin
from ..models.health_spending_correlation import HealthSpendingCorrelation
from ..config.base import Config

logger = logging.getLogger(__name__)

class FeatureType(Enum):
    """MINGUS feature types"""
    HEALTH_CHECKIN = "health_checkin"
    FINANCIAL_REPORT = "financial_report"
    AI_INSIGHT = "ai_insight"
    DATA_EXPORT = "data_export"
    ADVANCED_ANALYTICS = "advanced_analytics"
    API_ACCESS = "api_access"
    CUSTOM_INTEGRATIONS = "custom_integrations"

class AccessLevel(Enum):
    """Feature access levels"""
    NONE = "none"
    LIMITED = "limited"
    STANDARD = "standard"
    PREMIUM = "premium"
    UNLIMITED = "unlimited"

class MINGUSFeatureIntegration:
    """Comprehensive MINGUS feature integration management"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Feature configuration
        self.feature_config = {
            FeatureType.HEALTH_CHECKIN: {
                'budget': {'access': AccessLevel.LIMITED, 'limit': 4},
                'mid_tier': {'access': AccessLevel.STANDARD, 'limit': 12},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.FINANCIAL_REPORT: {
                'budget': {'access': AccessLevel.LIMITED, 'limit': 2},
                'mid_tier': {'access': AccessLevel.STANDARD, 'limit': 10},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.AI_INSIGHT: {
                'budget': {'access': AccessLevel.NONE, 'limit': 0},
                'mid_tier': {'access': AccessLevel.STANDARD, 'limit': 50},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.DATA_EXPORT: {
                'budget': {'access': AccessLevel.NONE, 'limit': 0},
                'mid_tier': {'access': AccessLevel.LIMITED, 'limit': 5},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.ADVANCED_ANALYTICS: {
                'budget': {'access': AccessLevel.NONE, 'limit': 0},
                'mid_tier': {'access': AccessLevel.LIMITED, 'limit': 3},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.API_ACCESS: {
                'budget': {'access': AccessLevel.NONE, 'limit': 0},
                'mid_tier': {'access': AccessLevel.LIMITED, 'limit': 1000},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            },
            FeatureType.CUSTOM_INTEGRATIONS: {
                'budget': {'access': AccessLevel.NONE, 'limit': 0},
                'mid_tier': {'access': AccessLevel.NONE, 'limit': 0},
                'professional': {'access': AccessLevel.UNLIMITED, 'limit': -1}
            }
        }
        
        # Data retention policies
        self.retention_policies = {
            'health_checkins': {
                'budget': {'retention_days': 90, 'backup_enabled': False},
                'mid_tier': {'retention_days': 365, 'backup_enabled': True},
                'professional': {'retention_days': 2555, 'backup_enabled': True}  # 7 years
            },
            'financial_data': {
                'budget': {'retention_days': 365, 'backup_enabled': False},
                'mid_tier': {'retention_days': 1095, 'backup_enabled': True},  # 3 years
                'professional': {'retention_days': 2555, 'backup_enabled': True}  # 7 years
            },
            'analytics_data': {
                'budget': {'retention_days': 90, 'backup_enabled': False},
                'mid_tier': {'retention_days': 365, 'backup_enabled': True},
                'professional': {'retention_days': 1825, 'backup_enabled': True}  # 5 years
            }
        }
    
    # ============================================================================
    # FEATURE ACCESS CONTROL
    # ============================================================================
    
    def update_feature_access_control(
        self,
        subscription_id: int,
        feature_type: FeatureType,
        access_level: AccessLevel,
        limit: int = None
    ) -> Dict[str, Any]:
        """Update feature access control for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Update feature usage record
            feature_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == datetime.utcnow().month,
                    FeatureUsage.usage_year == datetime.utcnow().year
                )
            ).first()
            
            if not feature_usage:
                feature_usage = FeatureUsage(
                    subscription_id=subscription_id,
                    usage_month=datetime.utcnow().month,
                    usage_year=datetime.utcnow().year
                )
                self.db.add(feature_usage)
            
            # Update feature limits based on type
            if feature_type == FeatureType.HEALTH_CHECKIN:
                feature_usage.max_health_checkins_per_month = limit
            elif feature_type == FeatureType.FINANCIAL_REPORT:
                feature_usage.max_financial_reports_per_month = limit
            elif feature_type == FeatureType.AI_INSIGHT:
                feature_usage.max_ai_insights_per_month = limit
            
            # Update subscription metadata with access control info
            if not subscription.metadata:
                subscription.metadata = {}
            
            subscription.metadata['feature_access'] = subscription.metadata.get('feature_access', {})
            subscription.metadata['feature_access'][feature_type.value] = {
                'access_level': access_level.value,
                'limit': limit,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.db.commit()
            
            # Log access control update
            self._log_feature_access_update(
                subscription_id=subscription_id,
                feature_type=feature_type,
                access_level=access_level,
                limit=limit
            )
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'feature_type': feature_type.value,
                'access_level': access_level.value,
                'limit': limit,
                'message': f'Feature access control updated for {feature_type.value}'
            }
            
        except Exception as e:
            logger.error(f"Error updating feature access control: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_feature_access_status(
        self,
        subscription_id: int,
        feature_type: FeatureType = None
    ) -> Dict[str, Any]:
        """Get feature access status for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get current feature usage
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            feature_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            if feature_type:
                # Return specific feature access status
                tier_config = self.feature_config[feature_type][subscription.pricing_tier.tier_type]
                
                current_usage = 0
                if feature_usage:
                    if feature_type == FeatureType.HEALTH_CHECKIN:
                        current_usage = feature_usage.health_checkins_used
                    elif feature_type == FeatureType.FINANCIAL_REPORT:
                        current_usage = feature_usage.financial_reports_used
                    elif feature_type == FeatureType.AI_INSIGHT:
                        current_usage = feature_usage.ai_insights_used
                
                return {
                    'success': True,
                    'feature_type': feature_type.value,
                    'access_level': tier_config['access'].value,
                    'limit': tier_config['limit'],
                    'current_usage': current_usage,
                    'available': tier_config['limit'] == -1 or current_usage < tier_config['limit'],
                    'usage_percentage': (current_usage / tier_config['limit'] * 100) if tier_config['limit'] > 0 else 0
                }
            else:
                # Return all feature access statuses
                all_features = {}
                
                for feature_type_enum in FeatureType:
                    tier_config = self.feature_config[feature_type_enum][subscription.pricing_tier.tier_type]
                    
                    current_usage = 0
                    if feature_usage:
                        if feature_type_enum == FeatureType.HEALTH_CHECKIN:
                            current_usage = feature_usage.health_checkins_used
                        elif feature_type_enum == FeatureType.FINANCIAL_REPORT:
                            current_usage = feature_usage.financial_reports_used
                        elif feature_type_enum == FeatureType.AI_INSIGHT:
                            current_usage = feature_usage.ai_insights_used
                    
                    all_features[feature_type_enum.value] = {
                        'access_level': tier_config['access'].value,
                        'limit': tier_config['limit'],
                        'current_usage': current_usage,
                        'available': tier_config['limit'] == -1 or current_usage < tier_config['limit'],
                        'usage_percentage': (current_usage / tier_config['limit'] * 100) if tier_config['limit'] > 0 else 0
                    }
                
                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'tier': subscription.pricing_tier.tier_type,
                    'features': all_features
                }
            
        except Exception as e:
            logger.error(f"Error getting feature access status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # USAGE LIMIT ADJUSTMENTS
    # ============================================================================
    
    def adjust_usage_limits(
        self,
        subscription_id: int,
        adjustments: Dict[str, int]
    ) -> Dict[str, Any]:
        """Adjust usage limits for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get or create feature usage record
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            feature_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            if not feature_usage:
                feature_usage = FeatureUsage(
                    subscription_id=subscription_id,
                    usage_month=current_month,
                    usage_year=current_year
                )
                self.db.add(feature_usage)
            
            # Apply adjustments
            adjustments_applied = {}
            
            for feature, adjustment in adjustments.items():
                if feature == 'health_checkins':
                    feature_usage.max_health_checkins_per_month += adjustment
                    adjustments_applied['health_checkins'] = feature_usage.max_health_checkins_per_month
                elif feature == 'financial_reports':
                    feature_usage.max_financial_reports_per_month += adjustment
                    adjustments_applied['financial_reports'] = feature_usage.max_financial_reports_per_month
                elif feature == 'ai_insights':
                    feature_usage.max_ai_insights_per_month += adjustment
                    adjustments_applied['ai_insights'] = feature_usage.max_ai_insights_per_month
            
            self.db.commit()
            
            # Log usage limit adjustment
            self._log_usage_limit_adjustment(
                subscription_id=subscription_id,
                adjustments=adjustments_applied
            )
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'adjustments_applied': adjustments_applied,
                'message': 'Usage limits adjusted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error adjusting usage limits: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reset_monthly_usage(self, subscription_id: int) -> Dict[str, Any]:
        """Reset monthly usage for a subscription"""
        try:
            # Create new usage record for current month
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            new_usage = FeatureUsage(
                subscription_id=subscription_id,
                usage_month=current_month,
                usage_year=current_year,
                health_checkins_used=0,
                financial_reports_used=0,
                ai_insights_used=0
            )
            
            self.db.add(new_usage)
            self.db.commit()
            
            # Log usage reset
            self._log_usage_reset(subscription_id=subscription_id)
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'month': current_month,
                'year': current_year,
                'message': 'Monthly usage reset successfully'
            }
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # DATA RETENTION POLICIES
    # ============================================================================
    
    def apply_data_retention_policies(self) -> Dict[str, Any]:
        """Apply data retention policies across all subscriptions"""
        try:
            results = {
                'data_cleaned': 0,
                'subscriptions_processed': 0,
                'errors': []
            }
            
            # Get all active subscriptions
            subscriptions = self.db.query(Subscription).filter(
                Subscription.status.in_(['active', 'trialing', 'past_due'])
            ).all()
            
            for subscription in subscriptions:
                try:
                    retention_result = self._apply_retention_policy_for_subscription(subscription)
                    
                    if retention_result['success']:
                        results['data_cleaned'] += retention_result['data_cleaned']
                        results['subscriptions_processed'] += 1
                    else:
                        results['errors'].append(f"Retention policy failed for subscription {subscription.id}: {retention_result['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing subscription {subscription.id}: {str(e)}")
            
            logger.info(f"Data retention policies applied: {results['data_cleaned']} records cleaned")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error applying data retention policies: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_retention_policy_for_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """Apply retention policy for a specific subscription"""
        try:
            tier_type = subscription.pricing_tier.tier_type
            data_cleaned = 0
            
            # Apply health checkin retention
            health_retention = self.retention_policies['health_checkins'][tier_type]
            health_cutoff = datetime.utcnow() - timedelta(days=health_retention['retention_days'])
            
            health_deleted = self.db.query(UserHealthCheckin).filter(
                and_(
                    UserHealthCheckin.user_id == subscription.customer.user_id,
                    UserHealthCheckin.created_at < health_cutoff
                )
            ).delete()
            
            data_cleaned += health_deleted
            
            # Apply financial data retention
            financial_retention = self.retention_policies['financial_data'][tier_type]
            financial_cutoff = datetime.utcnow() - timedelta(days=financial_retention['retention_days'])
            
            financial_deleted = self.db.query(HealthSpendingCorrelation).filter(
                and_(
                    HealthSpendingCorrelation.user_id == subscription.customer.user_id,
                    HealthSpendingCorrelation.created_at < financial_cutoff
                )
            ).delete()
            
            data_cleaned += financial_deleted
            
            # Log retention policy application
            self._log_retention_policy_application(
                subscription_id=subscription.id,
                tier_type=tier_type,
                data_cleaned=data_cleaned
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'tier_type': tier_type,
                'data_cleaned': data_cleaned
            }
            
        except Exception as e:
            logger.error(f"Error applying retention policy for subscription {subscription.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_retention_policy_status(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get retention policy status for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            tier_type = subscription.pricing_tier.tier_type
            user_id = subscription.customer.user_id
            
            # Get data counts and retention info
            retention_status = {}
            
            for data_type, policies in self.retention_policies.items():
                policy = policies[tier_type]
                cutoff_date = datetime.utcnow() - timedelta(days=policy['retention_days'])
                
                if data_type == 'health_checkins':
                    total_count = self.db.query(UserHealthCheckin).filter(
                        UserHealthCheckin.user_id == user_id
                    ).count()
                    
                    expired_count = self.db.query(UserHealthCheckin).filter(
                        and_(
                            UserHealthCheckin.user_id == user_id,
                            UserHealthCheckin.created_at < cutoff_date
                        )
                    ).count()
                    
                elif data_type == 'financial_data':
                    total_count = self.db.query(HealthSpendingCorrelation).filter(
                        HealthSpendingCorrelation.user_id == user_id
                    ).count()
                    
                    expired_count = self.db.query(HealthSpendingCorrelation).filter(
                        and_(
                            HealthSpendingCorrelation.user_id == user_id,
                            HealthSpendingCorrelation.created_at < cutoff_date
                        )
                    ).count()
                
                retention_status[data_type] = {
                    'retention_days': policy['retention_days'],
                    'backup_enabled': policy['backup_enabled'],
                    'total_records': total_count,
                    'expired_records': expired_count,
                    'cutoff_date': cutoff_date.isoformat()
                }
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'tier_type': tier_type,
                'retention_status': retention_status
            }
            
        except Exception as e:
            logger.error(f"Error getting retention policy status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # ANALYTICS AND REPORTING UPDATES
    # ============================================================================
    
    def update_analytics_and_reporting(
        self,
        subscription_id: int,
        analytics_enabled: bool = None,
        reporting_frequency: str = None,
        custom_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Update analytics and reporting settings for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Update subscription metadata
            if not subscription.metadata:
                subscription.metadata = {}
            
            if 'analytics' not in subscription.metadata:
                subscription.metadata['analytics'] = {}
            
            if analytics_enabled is not None:
                subscription.metadata['analytics']['enabled'] = analytics_enabled
            
            if reporting_frequency:
                subscription.metadata['analytics']['reporting_frequency'] = reporting_frequency
            
            if custom_metrics:
                subscription.metadata['analytics']['custom_metrics'] = custom_metrics
            
            subscription.metadata['analytics']['updated_at'] = datetime.utcnow().isoformat()
            
            self.db.commit()
            
            # Log analytics update
            self._log_analytics_update(
                subscription_id=subscription_id,
                analytics_enabled=analytics_enabled,
                reporting_frequency=reporting_frequency,
                custom_metrics=custom_metrics
            )
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'analytics_settings': subscription.metadata['analytics'],
                'message': 'Analytics and reporting settings updated'
            }
            
        except Exception as e:
            logger.error(f"Error updating analytics and reporting: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_feature_usage_report(
        self,
        subscription_id: int = None,
        period: str = 'monthly'
    ) -> Dict[str, Any]:
        """Generate feature usage report"""
        try:
            if subscription_id:
                # Generate report for specific subscription
                subscription = self.db.query(Subscription).filter(
                    Subscription.id == subscription_id
                ).first()
                
                if not subscription:
                    return {
                        'success': False,
                        'error': 'Subscription not found'
                    }
                
                report = self._generate_subscription_usage_report(subscription, period)
                
                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'period': period,
                    'report': report
                }
            else:
                # Generate aggregate report
                report = self._generate_aggregate_usage_report(period)
                
                return {
                    'success': True,
                    'period': period,
                    'report': report
                }
            
        except Exception as e:
            logger.error(f"Error generating feature usage report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_subscription_usage_report(
        self,
        subscription: Subscription,
        period: str
    ) -> Dict[str, Any]:
        """Generate usage report for a specific subscription"""
        try:
            # Get feature usage data
            if period == 'monthly':
                current_month = datetime.utcnow().month
                current_year = datetime.utcnow().year
                
                feature_usage = self.db.query(FeatureUsage).filter(
                    and_(
                        FeatureUsage.subscription_id == subscription.id,
                        FeatureUsage.usage_month == current_month,
                        FeatureUsage.usage_year == current_year
                    )
                ).first()
                
                if feature_usage:
                    usage_data = {
                        'health_checkins': {
                            'used': feature_usage.health_checkins_used,
                            'limit': feature_usage.max_health_checkins_per_month,
                            'percentage': (feature_usage.health_checkins_used / feature_usage.max_health_checkins_per_month * 100) if feature_usage.max_health_checkins_per_month > 0 else 0
                        },
                        'financial_reports': {
                            'used': feature_usage.financial_reports_used,
                            'limit': feature_usage.max_financial_reports_per_month,
                            'percentage': (feature_usage.financial_reports_used / feature_usage.max_financial_reports_per_month * 100) if feature_usage.max_financial_reports_per_month > 0 else 0
                        },
                        'ai_insights': {
                            'used': feature_usage.ai_insights_used,
                            'limit': feature_usage.max_ai_insights_per_month,
                            'percentage': (feature_usage.ai_insights_used / feature_usage.max_ai_insights_per_month * 100) if feature_usage.max_ai_insights_per_month > 0 else 0
                        }
                    }
                else:
                    usage_data = {
                        'health_checkins': {'used': 0, 'limit': 0, 'percentage': 0},
                        'financial_reports': {'used': 0, 'limit': 0, 'percentage': 0},
                        'ai_insights': {'used': 0, 'limit': 0, 'percentage': 0}
                    }
            
            # Get access control status
            access_status = self.get_feature_access_status(subscription.id)
            
            report = {
                'subscription_id': subscription.id,
                'customer_name': subscription.customer.name,
                'tier': subscription.pricing_tier.name,
                'period': period,
                'usage_data': usage_data,
                'access_status': access_status.get('features', {}),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating subscription usage report: {e}")
            return {'error': str(e)}
    
    def _generate_aggregate_usage_report(self, period: str) -> Dict[str, Any]:
        """Generate aggregate usage report across all subscriptions"""
        try:
            # Get aggregate usage statistics
            if period == 'monthly':
                current_month = datetime.utcnow().month
                current_year = datetime.utcnow().year
                
                # Aggregate usage by tier
                tier_usage = self.db.query(
                    PricingTier.tier_type,
                    func.sum(FeatureUsage.health_checkins_used).label('total_health_checkins'),
                    func.sum(FeatureUsage.financial_reports_used).label('total_financial_reports'),
                    func.sum(FeatureUsage.ai_insights_used).label('total_ai_insights'),
                    func.count(FeatureUsage.subscription_id).label('active_subscriptions')
                ).join(
                    Subscription, FeatureUsage.subscription_id == Subscription.id
                ).join(
                    PricingTier, Subscription.pricing_tier_id == PricingTier.id
                ).filter(
                    and_(
                        FeatureUsage.usage_month == current_month,
                        FeatureUsage.usage_year == current_year
                    )
                ).group_by(PricingTier.tier_type).all()
            
            # Format aggregate data
            aggregate_data = {}
            for tier_data in tier_usage:
                aggregate_data[tier_data.tier_type] = {
                    'active_subscriptions': tier_data.active_subscriptions,
                    'total_health_checkins': tier_data.total_health_checkins or 0,
                    'total_financial_reports': tier_data.total_financial_reports or 0,
                    'total_ai_insights': tier_data.total_ai_insights or 0
                }
            
            report = {
                'period': period,
                'aggregate_data': aggregate_data,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating aggregate usage report: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # LOGGING METHODS
    # ============================================================================
    
    def _log_feature_access_update(
        self,
        subscription_id: int,
        feature_type: FeatureType,
        access_level: AccessLevel,
        limit: int
    ):
        """Log feature access update"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                event_description=f"Feature access control updated: {feature_type.value} -> {access_level.value}",
                metadata={
                    'feature_type': feature_type.value,
                    'access_level': access_level.value,
                    'limit': limit,
                    'update_type': 'feature_access_control'
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log feature access update: {e}")
    
    def _log_usage_limit_adjustment(
        self,
        subscription_id: int,
        adjustments: Dict[str, int]
    ):
        """Log usage limit adjustment"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                event_description="Usage limits adjusted",
                metadata={
                    'adjustments': adjustments,
                    'update_type': 'usage_limit_adjustment'
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log usage limit adjustment: {e}")
    
    def _log_usage_reset(self, subscription_id: int):
        """Log usage reset"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                event_description="Monthly usage reset",
                metadata={
                    'update_type': 'usage_reset',
                    'reset_month': datetime.utcnow().month,
                    'reset_year': datetime.utcnow().year
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log usage reset: {e}")
    
    def _log_retention_policy_application(
        self,
        subscription_id: int,
        tier_type: str,
        data_cleaned: int
    ):
        """Log retention policy application"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                event_description="Data retention policy applied",
                metadata={
                    'tier_type': tier_type,
                    'data_cleaned': data_cleaned,
                    'update_type': 'retention_policy_application'
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log retention policy application: {e}")
    
    def _log_analytics_update(
        self,
        subscription_id: int,
        analytics_enabled: bool = None,
        reporting_frequency: str = None,
        custom_metrics: List[str] = None
    ):
        """Log analytics update"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                event_description="Analytics and reporting settings updated",
                metadata={
                    'analytics_enabled': analytics_enabled,
                    'reporting_frequency': reporting_frequency,
                    'custom_metrics': custom_metrics,
                    'update_type': 'analytics_update'
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log analytics update: {e}") 