"""
Usage Tracking Service for MINGUS
Handles feature usage monitoring, overage billing, limit enforcement, and real-time updates
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
import json
import asyncio
from threading import Timer
import schedule
import time

from ..models.subscription import (
    Subscription, FeatureUsage, Customer, PricingTier, AuditLog, AuditEventType, AuditSeverity
)
from ..models.user import User

logger = logging.getLogger(__name__)

class UsageTracker:
    """Comprehensive usage tracking system with real-time monitoring and automation"""
    
    def __init__(self, db_session: Session, config):
        self.db = db_session
        self.config = config
        
        # Real-time usage cache
        self.usage_cache = {}
        
        # Trackable features with pricing for overage calculations
        self.trackable_features = {
            'health_checkin': {
                'name': 'Health Check-ins',
                'unit': 'check-in',
                'overage_price': 2.00,  # $2 per additional check-in
                'notification_threshold': 0.8,  # 80% usage warning
                'critical_threshold': 0.95  # 95% usage critical warning
            },
            'financial_report': {
                'name': 'Financial Reports',
                'unit': 'report',
                'overage_price': 5.00,  # $5 per additional report
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'ai_insight': {
                'name': 'AI Insights',
                'unit': 'insight',
                'overage_price': 1.00,  # $1 per additional insight
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'custom_reports': {
                'name': 'Custom Reports',
                'unit': 'report',
                'overage_price': 10.00,  # $10 per additional report
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'team_members': {
                'name': 'Team Members',
                'unit': 'member',
                'overage_price': 15.00,  # $15 per additional member
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'api_access': {
                'name': 'API Calls',
                'unit': 'call',
                'overage_price': 0.01,  # $0.01 per additional call
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'support_requests': {
                'name': 'Support Requests',
                'unit': 'request',
                'overage_price': 25.00,  # $25 per additional request
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'career_risk_management': {
                'name': 'Career Risk Management',
                'unit': 'session',
                'overage_price': 5.00,  # $5 per additional session
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            },
            'dedicated_account_manager': {
                'name': 'Dedicated Account Manager',
                'unit': 'session',
                'overage_price': 50.00,  # $50 per additional session
                'notification_threshold': 0.8,
                'critical_threshold': 0.95
            }
        }
        
        # Feature pricing for overage calculations
        self.feature_pricing = {
            'health_checkin': 2.00,
            'financial_report': 5.00,
            'ai_insight': 1.00,
            'custom_reports': 10.00,
            'team_members': 15.00,
            'api_access': 0.01,
            'support_requests': 25.00,
            'career_risk_management': 5.00,
            'dedicated_account_manager': 50.00
        }
        
        # Initialize monthly reset scheduler
        self._initialize_monthly_reset_scheduler()
        
        # Initialize real-time monitoring
        self._initialize_real_time_monitoring()
    
    def _initialize_monthly_reset_scheduler(self):
        """Initialize automated monthly usage reset scheduler"""
        try:
            # Schedule monthly reset for the 1st of each month at 00:01
            schedule.every().month.at("00:01").do(self._automated_monthly_reset)
            
            # Start the scheduler in a separate thread
            import threading
            scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("Monthly usage reset scheduler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize monthly reset scheduler: {e}")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _initialize_real_time_monitoring(self):
        """Initialize real-time usage monitoring"""
        try:
            # Start real-time monitoring thread
            import threading
            monitoring_thread = threading.Thread(target=self._real_time_monitoring_loop, daemon=True)
            monitoring_thread.start()
            
            logger.info("Real-time usage monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to initialize real-time monitoring: {e}")
    
    def _real_time_monitoring_loop(self):
        """Real-time monitoring loop for usage tracking"""
        while True:
            try:
                # Update usage cache every 30 seconds
                self._update_usage_cache()
                
                # Check for overage conditions
                self._check_overage_conditions()
                
                # Sleep for 30 seconds
                time.sleep(30)
            except Exception as e:
                logger.error(f"Error in real-time monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _update_usage_cache(self):
        """Update real-time usage cache"""
        try:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            # Get all active subscriptions
            active_subscriptions = self.db.query(Subscription).filter(
                Subscription.status == 'active'
            ).all()
            
            for subscription in active_subscriptions:
                # Get or create usage record
                usage_record = self._get_or_create_usage_record(
                    subscription.id, current_month, current_year
                )
                
                # Update cache with current usage
                cache_key = f"{subscription.id}_{current_month}_{current_year}"
                self.usage_cache[cache_key] = {
                    'health_checkins_used': usage_record.health_checkins_used or 0,
                    'financial_reports_used': usage_record.financial_reports_used or 0,
                    'ai_insights_used': usage_record.ai_insights_used or 0,
                    'custom_reports_used': usage_record.custom_reports_used or 0,
                    'team_members_used': usage_record.team_members_used or 0,
                    'support_requests_used': usage_record.support_requests_used or 0,
                    'career_risk_management_used': usage_record.career_risk_management_used or 0,
                    'dedicated_account_manager_used': usage_record.dedicated_account_manager_used or 0,
                    'last_updated': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error updating usage cache: {e}")
    
    def _check_overage_conditions(self):
        """Check for overage conditions and send notifications"""
        try:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            # Get all active subscriptions
            active_subscriptions = self.db.query(Subscription).filter(
                Subscription.status == 'active'
            ).all()
            
            for subscription in active_subscriptions:
                # Check each feature for overage conditions
                self._check_subscription_overage(subscription, current_month, current_year)
                
        except Exception as e:
            logger.error(f"Error checking overage conditions: {e}")
    
    def _check_subscription_overage(self, subscription: Subscription, month: int, year: int):
        """Check overage conditions for a specific subscription"""
        try:
            usage_record = self._get_or_create_usage_record(subscription.id, month, year)
            
            # Get tier limits
            tier_limits = self._get_tier_limits(subscription.pricing_tier.tier_type)
            
            for feature_name, feature_config in self.trackable_features.items():
                current_usage = self._get_feature_usage(usage_record, feature_name)
                limit = tier_limits.get(feature_name, 0)
                
                if limit > 0:  # Only check features with limits
                    usage_percentage = current_usage / limit
                    
                    # Check notification threshold
                    if usage_percentage >= feature_config['notification_threshold']:
                        self._send_usage_notification(
                            subscription, feature_name, current_usage, limit, usage_percentage, 'warning'
                        )
                    
                    # Check critical threshold
                    if usage_percentage >= feature_config['critical_threshold']:
                        self._send_usage_notification(
                            subscription, feature_name, current_usage, limit, usage_percentage, 'critical'
                        )
                    
                    # Check overage
                    if current_usage > limit:
                        self._handle_overage(
                            subscription, feature_name, current_usage, limit
                        )
                        
        except Exception as e:
            logger.error(f"Error checking subscription overage: {e}")
    
    def _get_tier_limits(self, tier_type: str) -> Dict[str, int]:
        """Get feature limits for a specific tier"""
        limits = {}
        
        if tier_type == 'budget':
            limits = {
                'health_checkin': 4,
                'financial_report': 2,
                'ai_insight': 0,
                'custom_reports': 0,
                'team_members': 0,
                'api_access': 0,
                'support_requests': 1,
                'career_risk_management': 0,
                'dedicated_account_manager': 0
            }
        elif tier_type == 'mid_tier':
            limits = {
                'health_checkin': 12,
                'financial_report': 10,
                'ai_insight': 50,
                'custom_reports': 5,
                'team_members': 0,
                'api_access': 0,
                'support_requests': 3,
                'career_risk_management': -1,  # Unlimited
                'dedicated_account_manager': 0
            }
        elif tier_type == 'professional':
            limits = {
                'health_checkin': -1,  # Unlimited
                'financial_report': -1,  # Unlimited
                'ai_insight': -1,  # Unlimited
                'custom_reports': -1,  # Unlimited
                'team_members': 10,
                'api_access': 10000,  # 10,000 per hour
                'support_requests': -1,  # Unlimited
                'career_risk_management': -1,  # Unlimited
                'dedicated_account_manager': 1
            }
        
        return limits
    
    def _get_feature_usage(self, usage_record: FeatureUsage, feature_name: str) -> int:
        """Get current usage for a specific feature"""
        if feature_name == 'health_checkin':
            return usage_record.health_checkins_used or 0
        elif feature_name == 'financial_report':
            return usage_record.financial_reports_used or 0
        elif feature_name == 'ai_insight':
            return usage_record.ai_insights_used or 0
        elif feature_name == 'custom_reports':
            return usage_record.custom_reports_used or 0
        elif feature_name == 'team_members':
            return usage_record.team_members_used or 0
        elif feature_name == 'support_requests':
            return usage_record.support_requests_used or 0
        elif feature_name == 'career_risk_management':
            return usage_record.career_risk_management_used or 0
        elif feature_name == 'dedicated_account_manager':
            return usage_record.dedicated_account_manager_used or 0
        else:
            return 0
    
    def _send_usage_notification(
        self,
        subscription: Subscription,
        feature_name: str,
        current_usage: int,
        limit: int,
        usage_percentage: float,
        notification_type: str
    ):
        """Send usage notification to customer"""
        try:
            feature_config = self.trackable_features[feature_name]
            
            if notification_type == 'warning':
                message = f"You're at {usage_percentage:.0%} of your {feature_config['name']} limit ({current_usage}/{limit}). Consider upgrading to avoid overage charges."
                severity = AuditSeverity.WARNING
            else:  # critical
                message = f"CRITICAL: You're at {usage_percentage:.0%} of your {feature_config['name']} limit ({current_usage}/{limit}). Upgrade immediately to avoid overage charges."
                severity = AuditSeverity.ERROR
            
            # Log the notification
            self._log_audit_event(
                subscription.customer.user_id,
                AuditEventType.USAGE_NOTIFICATION,
                severity,
                f"Usage notification sent for {feature_name}",
                {
                    'subscription_id': subscription.id,
                    'feature_name': feature_name,
                    'current_usage': current_usage,
                    'limit': limit,
                    'usage_percentage': usage_percentage,
                    'notification_type': notification_type,
                    'message': message
                }
            )
            
            # TODO: Send actual notification (email, SMS, in-app)
            logger.info(f"Usage notification sent to subscription {subscription.id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending usage notification: {e}")
    
    def _handle_overage(self, subscription: Subscription, feature_name: str, current_usage: int, limit: int):
        """Handle overage for a specific feature"""
        try:
            overage_amount = current_usage - limit
            feature_config = self.trackable_features[feature_name]
            overage_cost = overage_amount * feature_config['overage_price']
            
            # Log overage event
            self._log_audit_event(
                subscription.customer.user_id,
                AuditEventType.USAGE_OVERAGE,
                AuditSeverity.ERROR,
                f"Usage overage detected for {feature_name}",
                {
                    'subscription_id': subscription.id,
                    'feature_name': feature_name,
                    'current_usage': current_usage,
                    'limit': limit,
                    'overage_amount': overage_amount,
                    'overage_cost': overage_cost
                }
            )
            
            # TODO: Generate overage invoice
            logger.warning(f"Overage detected for subscription {subscription.id}: {overage_amount} {feature_config['unit']} over limit, cost: ${overage_cost:.2f}")
            
        except Exception as e:
            logger.error(f"Error handling overage: {e}")
    
    def _automated_monthly_reset(self):
        """Automated monthly usage reset"""
        try:
            logger.info("Starting automated monthly usage reset")
            
            # Get all active subscriptions
            active_subscriptions = self.db.query(Subscription).filter(
                Subscription.status == 'active'
            ).all()
            
            reset_count = 0
            
            for subscription in active_subscriptions:
                try:
                    # Create new usage record for the new month
                    new_month = datetime.utcnow().month
                    new_year = datetime.utcnow().year
                    
                    # Check if usage record already exists for new month
                    existing_record = self.db.query(FeatureUsage).filter(
                        and_(
                            FeatureUsage.subscription_id == subscription.id,
                            FeatureUsage.usage_month == new_month,
                            FeatureUsage.usage_year == new_year
                        )
                    ).first()
                    
                    if not existing_record:
                        # Create new usage record with zero usage
                        new_usage_record = FeatureUsage(
                            subscription_id=subscription.id,
                            usage_month=new_month,
                            usage_year=new_year,
                            health_checkins_used=0,
                            financial_reports_used=0,
                            ai_insights_used=0,
                            custom_reports_used=0,
                            team_members_used=0,
                            support_requests_used=0,
                            career_risk_management_used=0,
                            dedicated_account_manager_used=0
                        )
                        
                        self.db.add(new_usage_record)
                        reset_count += 1
                        
                        # Log the reset
                        self._log_audit_event(
                            subscription.customer.user_id,
                            AuditEventType.USAGE_RESET,
                            AuditSeverity.INFO,
                            f"Monthly usage reset for subscription {subscription.id}",
                            {
                                'subscription_id': subscription.id,
                                'month': new_month,
                                'year': new_year
                            }
                        )
                
                except Exception as e:
                    logger.error(f"Error resetting usage for subscription {subscription.id}: {e}")
            
            self.db.commit()
            logger.info(f"Monthly usage reset completed. {reset_count} subscriptions reset.")
            
        except Exception as e:
            logger.error(f"Error in automated monthly reset: {e}")
            self.db.rollback()
    
    def track_feature_usage(
        self,
        subscription_id: int,
        feature_name: str,
        user_id: int = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Track real-time feature usage with immediate cache update"""
        try:
            # Get current month and year
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            # Get or create usage record
            usage_record = self._get_or_create_usage_record(subscription_id, current_month, current_year)
            
            # Get subscription and tier info
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get tier limits
            tier_limits = self._get_tier_limits(subscription.pricing_tier.tier_type)
            limit = tier_limits.get(feature_name, 0)
            
            # Get current usage
            current_usage = self._get_feature_usage(usage_record, feature_name)
            
            # Check if usage is allowed
            if limit > 0 and current_usage >= limit:
                return {
                    'success': False,
                    'error': f'Usage limit reached for {feature_name}',
                    'current_usage': current_usage,
                    'limit': limit,
                    'decision': 'limit_reached'
                }
            
            # Update usage
            self._update_feature_usage(usage_record, feature_name)
            
            # Update cache immediately
            cache_key = f"{subscription_id}_{current_month}_{current_year}"
            if cache_key in self.usage_cache:
                self.usage_cache[cache_key][f"{feature_name}_used"] = current_usage + 1
                self.usage_cache[cache_key]['last_updated'] = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            
            # Log usage event
            self._log_audit_event(
                user_id,
                AuditEventType.FEATURE_USAGE,
                AuditSeverity.INFO,
                f"Feature usage tracked: {feature_name}",
                {
                    'subscription_id': subscription_id,
                    'feature_name': feature_name,
                    'usage_count': current_usage + 1,
                    'limit': limit,
                    'metadata': metadata
                }
            )
            
            return {
                'success': True,
                'current_usage': current_usage + 1,
                'limit': limit,
                'usage_percentage': ((current_usage + 1) / limit * 100) if limit > 0 else 0,
                'decision': 'allowed'
            }
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_real_time_usage(
        self,
        subscription_id: int,
        feature_name: str = None
    ) -> Dict[str, Any]:
        """Get real-time usage data from cache"""
        try:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            cache_key = f"{subscription_id}_{current_month}_{current_year}"
            
            if cache_key in self.usage_cache:
                cache_data = self.usage_cache[cache_key]
                
                if feature_name:
                    usage_key = f"{feature_name}_used"
                    if usage_key in cache_data:
                        return {
                            'success': True,
                            'usage': cache_data[usage_key],
                            'last_updated': cache_data['last_updated'],
                            'cache_hit': True
                        }
                else:
                    return {
                        'success': True,
                        'usage': cache_data,
                        'cache_hit': True
                    }
            
            # Fallback to database if not in cache
            return self.get_feature_usage(subscription_id, feature_name)
            
        except Exception as e:
            logger.error(f"Error getting real-time usage: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_analytics(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None,
        feature_name: str = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics and reporting"""
        try:
            query = self.db.query(FeatureUsage)
            
            if subscription_id:
                query = query.filter(FeatureUsage.subscription_id == subscription_id)
            
            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    and_(
                        FeatureUsage.usage_year >= start_date.year,
                        FeatureUsage.usage_year <= end_date.year,
                        FeatureUsage.usage_month >= start_date.month,
                        FeatureUsage.usage_month <= end_date.month
                    )
                )
            
            usage_records = query.all()
            
            # Aggregate analytics
            analytics = {
                'total_records': len(usage_records),
                'feature_usage': {},
                'subscription_usage': {},
                'monthly_trends': {},
                'overage_analysis': {},
                'peak_usage_periods': {}
            }
            
            for record in usage_records:
                # Feature usage aggregation
                features = [
                    ('health_checkin', record.health_checkins_used or 0),
                    ('financial_report', record.financial_reports_used or 0),
                    ('ai_insight', record.ai_insights_used or 0),
                    ('custom_reports', record.custom_reports_used or 0),
                    ('team_members', record.team_members_used or 0),
                    ('support_requests', record.support_requests_used or 0),
                    ('career_risk_management', record.career_risk_management_used or 0),
                    ('dedicated_account_manager', record.dedicated_account_manager_used or 0)
                ]
                
                for feature_name, usage in features:
                    if feature_name not in analytics['feature_usage']:
                        analytics['feature_usage'][feature_name] = {
                            'total_usage': 0,
                            'average_usage': 0,
                            'max_usage': 0,
                            'min_usage': float('inf'),
                            'usage_count': 0
                        }
                    
                    analytics['feature_usage'][feature_name]['total_usage'] += usage
                    analytics['feature_usage'][feature_name]['max_usage'] = max(
                        analytics['feature_usage'][feature_name]['max_usage'], usage
                    )
                    analytics['feature_usage'][feature_name]['min_usage'] = min(
                        analytics['feature_usage'][feature_name]['min_usage'], usage
                    )
                    analytics['feature_usage'][feature_name]['usage_count'] += 1
                
                # Monthly trends
                month_key = f"{record.usage_year}-{record.usage_month:02d}"
                if month_key not in analytics['monthly_trends']:
                    analytics['monthly_trends'][month_key] = {
                        'total_usage': 0,
                        'subscription_count': 0
                    }
                
                analytics['monthly_trends'][month_key]['total_usage'] += sum([
                    record.health_checkins_used or 0,
                    record.financial_reports_used or 0,
                    record.ai_insights_used or 0,
                    record.custom_reports_used or 0,
                    record.team_members_used or 0,
                    record.support_requests_used or 0,
                    record.career_risk_management_used or 0,
                    record.dedicated_account_manager_used or 0
                ])
                analytics['monthly_trends'][month_key]['subscription_count'] += 1
            
            # Calculate averages
            for feature_name, data in analytics['feature_usage'].items():
                if data['usage_count'] > 0:
                    data['average_usage'] = data['total_usage'] / data['usage_count']
                if data['min_usage'] == float('inf'):
                    data['min_usage'] = 0
            
            return {
                'success': True,
                'analytics': analytics,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_overage_report(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive overage report"""
        try:
            query = self.db.query(FeatureUsage)
            
            if subscription_id:
                query = query.filter(FeatureUsage.subscription_id == subscription_id)
            
            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    and_(
                        FeatureUsage.usage_year >= start_date.year,
                        FeatureUsage.usage_year <= end_date.year,
                        FeatureUsage.usage_month >= start_date.month,
                        FeatureUsage.usage_month <= end_date.month
                    )
                )
            
            usage_records = query.all()
            
            overage_report = {
                'total_overages': 0,
                'total_overage_cost': 0.0,
                'subscription_overages': {},
                'feature_overages': {},
                'monthly_overages': {}
            }
            
            for record in usage_records:
                subscription = self.db.query(Subscription).filter(
                    Subscription.id == record.subscription_id
                ).first()
                
                if not subscription:
                    continue
                
                tier_limits = self._get_tier_limits(subscription.pricing_tier.tier_type)
                
                # Check each feature for overages
                features = [
                    ('health_checkin', record.health_checkins_used or 0),
                    ('financial_report', record.financial_reports_used or 0),
                    ('ai_insight', record.ai_insights_used or 0),
                    ('custom_reports', record.custom_reports_used or 0),
                    ('team_members', record.team_members_used or 0),
                    ('support_requests', record.support_requests_used or 0),
                    ('career_risk_management', record.career_risk_management_used or 0),
                    ('dedicated_account_manager', record.dedicated_account_manager_used or 0)
                ]
                
                subscription_overages = []
                
                for feature_name, usage in features:
                    limit = tier_limits.get(feature_name, 0)
                    
                    if limit > 0 and usage > limit:
                        overage_amount = usage - limit
                        overage_cost = overage_amount * self.feature_pricing.get(feature_name, 0)
                        
                        overage_info = {
                            'feature_name': feature_name,
                            'usage': usage,
                            'limit': limit,
                            'overage_amount': overage_amount,
                            'overage_cost': overage_cost
                        }
                        
                        subscription_overages.append(overage_info)
                        overage_report['total_overages'] += 1
                        overage_report['total_overage_cost'] += overage_cost
                        
                        # Aggregate by feature
                        if feature_name not in overage_report['feature_overages']:
                            overage_report['feature_overages'][feature_name] = {
                                'total_overages': 0,
                                'total_overage_cost': 0.0,
                                'subscriptions_affected': 0
                            }
                        
                        overage_report['feature_overages'][feature_name]['total_overages'] += overage_amount
                        overage_report['feature_overages'][feature_name]['total_overage_cost'] += overage_cost
                        overage_report['feature_overages'][feature_name]['subscriptions_affected'] += 1
                
                if subscription_overages:
                    overage_report['subscription_overages'][record.subscription_id] = {
                        'subscription_id': record.subscription_id,
                        'customer_email': subscription.customer.email,
                        'tier': subscription.pricing_tier.tier_type,
                        'overages': subscription_overages,
                        'total_overage_cost': sum(o['overage_cost'] for o in subscription_overages)
                    }
                
                # Monthly aggregation
                month_key = f"{record.usage_year}-{record.usage_month:02d}"
                if month_key not in overage_report['monthly_overages']:
                    overage_report['monthly_overages'][month_key] = {
                        'total_overages': 0,
                        'total_overage_cost': 0.0,
                        'subscriptions_affected': 0
                    }
                
                if subscription_overages:
                    overage_report['monthly_overages'][month_key]['total_overages'] += len(subscription_overages)
                    overage_report['monthly_overages'][month_key]['total_overage_cost'] += sum(
                        o['overage_cost'] for o in subscription_overages
                    )
                    overage_report['monthly_overages'][month_key]['subscriptions_affected'] += 1
            
            return {
                'success': True,
                'overage_report': overage_report,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting overage report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_usage_record(
        self,
        subscription_id: int,
        month: int,
        year: int
    ) -> FeatureUsage:
        """Get or create usage record for subscription and month"""
        usage_record = self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.subscription_id == subscription_id,
                FeatureUsage.usage_month == month,
                FeatureUsage.usage_year == year
            )
        ).first()
        
        if not usage_record:
            usage_record = FeatureUsage(
                subscription_id=subscription_id,
                usage_month=month,
                usage_year=year,
                health_checkins_used=0,
                financial_reports_used=0,
                ai_insights_used=0,
                custom_reports_used=0,
                team_members_used=0,
                support_requests_used=0,
                career_risk_management_used=0,
                dedicated_account_manager_used=0
            )
            self.db.add(usage_record)
            self.db.commit()
        
        return usage_record
    
    def _update_feature_usage(self, usage_record: FeatureUsage, feature_name: str):
        """Update usage for a specific feature"""
        if feature_name == 'health_checkin':
            usage_record.health_checkins_used = (usage_record.health_checkins_used or 0) + 1
        elif feature_name == 'financial_report':
            usage_record.financial_reports_used = (usage_record.financial_reports_used or 0) + 1
        elif feature_name == 'ai_insight':
            usage_record.ai_insights_used = (usage_record.ai_insights_used or 0) + 1
        elif feature_name == 'custom_reports':
            usage_record.custom_reports_used = (usage_record.custom_reports_used or 0) + 1
        elif feature_name == 'team_members':
            usage_record.team_members_used = (usage_record.team_members_used or 0) + 1
        elif feature_name == 'support_requests':
            usage_record.support_requests_used = (usage_record.support_requests_used or 0) + 1
        elif feature_name == 'career_risk_management':
            usage_record.career_risk_management_used = (usage_record.career_risk_management_used or 0) + 1
        elif feature_name == 'dedicated_account_manager':
            usage_record.dedicated_account_manager_used = (usage_record.dedicated_account_manager_used or 0) + 1
    
    def _log_audit_event(
        self,
        user_id: int,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Log audit event for usage tracking"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                severity=severity,
                event_timestamp=datetime.utcnow(),
                user_id=user_id,
                message=message,
                metadata=json.dumps(metadata) if metadata else None
            )
            self.db.add(audit_log)
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}") 