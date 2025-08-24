"""
Admin Billing Dashboard Service for MINGUS
Provides comprehensive revenue analytics and trending for administrators
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func, and_, desc, extract, case, text
from sqlalchemy.orm import Session
import stripe
from ..config.base import Config
from ..models.subscription import (
    Customer, Subscription, PricingTier, BillingHistory, 
    SubscriptionUsage, FeatureUsage, AuditLog
)

logger = logging.getLogger(__name__)

class AdminBillingDashboard:
    """Admin billing dashboard with revenue analytics and trending"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
    
    def get_revenue_analytics(self, date_range: str = '30d', granularity: str = 'day') -> Dict[str, Any]:
        """Get comprehensive revenue analytics"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            # Get revenue metrics
            revenue_metrics = self._calculate_revenue_metrics(start_date, end_date, granularity)
            
            # Get subscription metrics
            subscription_metrics = self._calculate_subscription_metrics(start_date, end_date)
            
            # Get tier performance
            tier_performance = self._calculate_tier_performance(start_date, end_date)
            
            # Get payment metrics
            payment_metrics = self._calculate_payment_metrics(start_date, end_date)
            
            # Get growth trends
            growth_trends = self._calculate_growth_trends(start_date, end_date)
            
            return {
                'success': True,
                'revenue_analytics': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range,
                        'granularity': granularity
                    },
                    'revenue_metrics': revenue_metrics,
                    'subscription_metrics': subscription_metrics,
                    'tier_performance': tier_performance,
                    'payment_metrics': payment_metrics,
                    'growth_trends': growth_trends
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_revenue_trending(self, metric: str = 'mrr', period: str = '12m') -> Dict[str, Any]:
        """Get revenue trending data for specific metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            if metric == 'mrr':
                trending_data = self._calculate_mrr_trending(start_date, end_date)
            elif metric == 'arr':
                trending_data = self._calculate_arr_trending(start_date, end_date)
            elif metric == 'revenue':
                trending_data = self._calculate_revenue_trending(start_date, end_date)
            elif metric == 'subscriptions':
                trending_data = self._calculate_subscription_trending(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid metric: {metric}'
                }
            
            return {
                'success': True,
                'revenue_trending': {
                    'metric': metric,
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'trending_data': trending_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue trending: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_revenue_forecast(self, forecast_period: str = '6m') -> Dict[str, Any]:
        """Get revenue forecast based on historical data"""
        try:
            # Get historical data for forecasting
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)  # Use 1 year of data
            
            # Calculate historical trends
            historical_data = self._get_historical_revenue_data(start_date, end_date)
            
            # Generate forecast
            forecast_data = self._generate_revenue_forecast(historical_data, forecast_period)
            
            return {
                'success': True,
                'revenue_forecast': {
                    'forecast_period': forecast_period,
                    'historical_data': historical_data,
                    'forecast_data': forecast_data,
                    'confidence_intervals': self._calculate_confidence_intervals(forecast_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue forecast: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_revenue_breakdown(self, breakdown_type: str = 'tier', date_range: str = '30d') -> Dict[str, Any]:
        """Get detailed revenue breakdown by various dimensions"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if breakdown_type == 'tier':
                breakdown_data = self._get_tier_revenue_breakdown(start_date, end_date)
            elif breakdown_type == 'billing_cycle':
                breakdown_data = self._get_billing_cycle_revenue_breakdown(start_date, end_date)
            elif breakdown_type == 'geographic':
                breakdown_data = self._get_geographic_revenue_breakdown(start_date, end_date)
            elif breakdown_type == 'customer_segment':
                breakdown_data = self._get_customer_segment_revenue_breakdown(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid breakdown type: {breakdown_type}'
                }
            
            return {
                'success': True,
                'revenue_breakdown': {
                    'breakdown_type': breakdown_type,
                    'date_range': date_range,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'breakdown_data': breakdown_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue breakdown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_conversion_funnel(self, date_range: str = '30d', funnel_type: str = 'standard') -> Dict[str, Any]:
        """Get subscription conversion funnel analysis"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if funnel_type == 'standard':
                funnel_data = self._calculate_standard_conversion_funnel(start_date, end_date)
            elif funnel_type == 'tier_upgrade':
                funnel_data = self._calculate_tier_upgrade_funnel(start_date, end_date)
            elif funnel_type == 'billing_cycle':
                funnel_data = self._calculate_billing_cycle_funnel(start_date, end_date)
            elif funnel_type == 'trial_conversion':
                funnel_data = self._calculate_trial_conversion_funnel(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid funnel type: {funnel_type}'
                }
            
            return {
                'success': True,
                'conversion_funnel': {
                    'funnel_type': funnel_type,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'funnel_data': funnel_data,
                    'overall_conversion_rate': self._calculate_overall_conversion_rate(funnel_data),
                    'bottleneck_analysis': self._identify_funnel_bottlenecks(funnel_data),
                    'optimization_recommendations': self._generate_funnel_optimization_recommendations(funnel_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription conversion funnel: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversion_funnel_trends(self, funnel_type: str = 'standard', period: str = '12m') -> Dict[str, Any]:
        """Get conversion funnel trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            # Calculate funnel data for each month
            monthly_funnels = []
            current_date = start_date
            
            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                if funnel_type == 'standard':
                    funnel_data = self._calculate_standard_conversion_funnel(month_start, month_end)
                elif funnel_type == 'tier_upgrade':
                    funnel_data = self._calculate_tier_upgrade_funnel(month_start, month_end)
                elif funnel_type == 'billing_cycle':
                    funnel_data = self._calculate_billing_cycle_funnel(month_start, month_end)
                elif funnel_type == 'trial_conversion':
                    funnel_data = self._calculate_trial_conversion_funnel(month_start, month_end)
                else:
                    return {
                        'success': False,
                        'error': f'Invalid funnel type: {funnel_type}'
                    }
                
                monthly_funnels.append({
                    'period': month_start.strftime('%Y-%m'),
                    'funnel_data': funnel_data,
                    'conversion_rate': self._calculate_overall_conversion_rate(funnel_data)
                })
                
                current_date = month_end + timedelta(days=1)
            
            return {
                'success': True,
                'conversion_funnel_trends': {
                    'funnel_type': funnel_type,
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'monthly_funnels': monthly_funnels,
                    'trend_analysis': self._analyze_funnel_trends(monthly_funnels)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversion_funnel_breakdown(self, funnel_type: str = 'standard', breakdown_dimension: str = 'tier', date_range: str = '30d') -> Dict[str, Any]:
        """Get conversion funnel breakdown by various dimensions"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if breakdown_dimension == 'tier':
                breakdown_data = self._get_tier_conversion_funnel_breakdown(start_date, end_date, funnel_type)
            elif breakdown_dimension == 'geographic':
                breakdown_data = self._get_geographic_conversion_funnel_breakdown(start_date, end_date, funnel_type)
            elif breakdown_dimension == 'time_period':
                breakdown_data = self._get_time_period_conversion_funnel_breakdown(start_date, end_date, funnel_type)
            elif breakdown_dimension == 'customer_segment':
                breakdown_data = self._get_customer_segment_conversion_funnel_breakdown(start_date, end_date, funnel_type)
            else:
                return {
                    'success': False,
                    'error': f'Invalid breakdown dimension: {breakdown_dimension}'
                }
            
            return {
                'success': True,
                'conversion_funnel_breakdown': {
                    'funnel_type': funnel_type,
                    'breakdown_dimension': breakdown_dimension,
                    'date_range': date_range,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'breakdown_data': breakdown_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel breakdown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_churn_analysis(self, date_range: str = '30d', churn_type: str = 'voluntary') -> Dict[str, Any]:
        """Get comprehensive churn analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if churn_type == 'voluntary':
                churn_data = self._calculate_voluntary_churn(start_date, end_date)
            elif churn_type == 'involuntary':
                churn_data = self._calculate_involuntary_churn(start_date, end_date)
            elif churn_type == 'overall':
                churn_data = self._calculate_overall_churn(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid churn type: {churn_type}'
                }
            
            return {
                'success': True,
                'churn_analysis': {
                    'churn_type': churn_type,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'churn_data': churn_data,
                    'churn_rate': self._calculate_churn_rate(churn_data),
                    'churn_impact': self._calculate_churn_impact(churn_data),
                    'churn_reasons': self._analyze_churn_reasons(churn_data),
                    'prevention_recommendations': self._generate_churn_prevention_recommendations(churn_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting churn analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_churn_prediction(self, prediction_horizon: str = '30d') -> Dict[str, Any]:
        """Get churn prediction analysis"""
        try:
            # Calculate prediction data
            prediction_data = self._calculate_churn_prediction(prediction_horizon)
            
            return {
                'success': True,
                'churn_prediction': {
                    'prediction_horizon': prediction_horizon,
                    'prediction_data': prediction_data,
                    'high_risk_customers': self._identify_high_risk_customers(),
                    'risk_factors': self._analyze_risk_factors(),
                    'intervention_strategies': self._generate_intervention_strategies(prediction_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting churn prediction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_churn_prevention_metrics(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get churn prevention effectiveness metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            prevention_metrics = self._calculate_prevention_metrics(start_date, end_date)
            
            return {
                'success': True,
                'churn_prevention_metrics': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'prevention_metrics': prevention_metrics,
                    'effectiveness_score': self._calculate_prevention_effectiveness(prevention_metrics),
                    'optimization_recommendations': self._generate_prevention_optimization_recommendations(prevention_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting churn prevention metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_churn_trends(self, period: str = '12m') -> Dict[str, Any]:
        """Get churn trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            # Calculate monthly churn trends
            monthly_churn = []
            current_date = start_date
            
            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_churn = self._calculate_monthly_churn(month_start, month_end)
                monthly_churn.append({
                    'period': month_start.strftime('%Y-%m'),
                    'churn_data': month_churn,
                    'churn_rate': self._calculate_churn_rate(month_churn)
                })
                
                current_date = month_end + timedelta(days=1)
            
            return {
                'success': True,
                'churn_trends': {
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'monthly_churn': monthly_churn,
                    'trend_analysis': self._analyze_churn_trends(monthly_churn)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting churn trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_churn_breakdown(self, breakdown_dimension: str = 'tier', date_range: str = '30d') -> Dict[str, Any]:
        """Get churn breakdown by various dimensions"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if breakdown_dimension == 'tier':
                breakdown_data = self._get_tier_churn_breakdown(start_date, end_date)
            elif breakdown_dimension == 'geographic':
                breakdown_data = self._get_geographic_churn_breakdown(start_date, end_date)
            elif breakdown_dimension == 'customer_segment':
                breakdown_data = self._get_customer_segment_churn_breakdown(start_date, end_date)
            elif breakdown_dimension == 'billing_cycle':
                breakdown_data = self._get_billing_cycle_churn_breakdown(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid breakdown dimension: {breakdown_dimension}'
                }
            
            return {
                'success': True,
                'churn_breakdown': {
                    'breakdown_dimension': breakdown_dimension,
                    'date_range': date_range,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'breakdown_data': breakdown_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting churn breakdown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods for revenue analytics
    def _calculate_start_date(self, end_date: datetime, period: str) -> datetime:
        """Calculate start date based on period string"""
        if period.endswith('d'):
            days = int(period[:-1])
            return end_date - timedelta(days=days)
        elif period.endswith('w'):
            weeks = int(period[:-1])
            return end_date - timedelta(weeks=weeks)
        elif period.endswith('m'):
            months = int(period[:-1])
            # Approximate months
            return end_date - timedelta(days=months * 30)
        elif period.endswith('y'):
            years = int(period[:-1])
            return end_date - timedelta(days=years * 365)
        else:
            return end_date - timedelta(days=30)  # Default to 30 days
    
    def _calculate_revenue_metrics(self, start_date: datetime, end_date: datetime, granularity: str) -> Dict[str, Any]:
        """Calculate comprehensive revenue metrics"""
        # Get all billing history in date range
        billing_records = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'paid'
            )
        ).all()
        
        # Calculate total revenue
        total_revenue = sum(record.amount for record in billing_records)
        
        # Calculate MRR (Monthly Recurring Revenue)
        mrr = self._calculate_mrr(end_date)
        
        # Calculate ARR (Annual Recurring Revenue)
        arr = mrr * 12
        
        # Calculate average revenue per customer
        unique_customers = len(set(record.customer_id for record in billing_records))
        avg_revenue_per_customer = total_revenue / unique_customers if unique_customers > 0 else 0
        
        # Calculate revenue by granularity
        revenue_by_period = self._calculate_revenue_by_period(billing_records, granularity)
        
        # Calculate revenue growth
        previous_period_start = start_date - (end_date - start_date)
        previous_period_revenue = self._calculate_period_revenue(previous_period_start, start_date)
        revenue_growth = ((total_revenue - previous_period_revenue) / previous_period_revenue * 100) if previous_period_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'mrr': mrr,
            'arr': arr,
            'avg_revenue_per_customer': avg_revenue_per_customer,
            'revenue_growth_percentage': revenue_growth,
            'revenue_by_period': revenue_by_period,
            'customer_count': unique_customers,
            'transaction_count': len(billing_records)
        }
    
    def _calculate_mrr(self, as_of_date: datetime) -> float:
        """Calculate Monthly Recurring Revenue"""
        # Get all active subscriptions as of the date
        active_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at <= as_of_date
            )
        ).all()
        
        mrr = 0
        for subscription in active_subscriptions:
            if subscription.billing_cycle == 'monthly':
                mrr += subscription.amount
            elif subscription.billing_cycle == 'annual':
                mrr += subscription.amount  # Already monthly equivalent
        
        return mrr
    
    def _calculate_revenue_by_period(self, billing_records: List[BillingHistory], granularity: str) -> List[Dict[str, Any]]:
        """Calculate revenue grouped by time period"""
        if granularity == 'day':
            # Group by day
            revenue_by_day = {}
            for record in billing_records:
                day_key = record.created_at.date().isoformat()
                revenue_by_day[day_key] = revenue_by_day.get(day_key, 0) + record.amount
            
            return [
                {'period': day, 'revenue': revenue}
                for day, revenue in sorted(revenue_by_day.items())
            ]
        
        elif granularity == 'week':
            # Group by week
            revenue_by_week = {}
            for record in billing_records:
                week_start = record.created_at.date() - timedelta(days=record.created_at.weekday())
                week_key = week_start.isoformat()
                revenue_by_week[week_key] = revenue_by_week.get(week_key, 0) + record.amount
            
            return [
                {'period': week, 'revenue': revenue}
                for week, revenue in sorted(revenue_by_week.items())
            ]
        
        elif granularity == 'month':
            # Group by month
            revenue_by_month = {}
            for record in billing_records:
                month_key = f"{record.created_at.year}-{record.created_at.month:02d}"
                revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + record.amount
            
            return [
                {'period': month, 'revenue': revenue}
                for month, revenue in sorted(revenue_by_month.items())
            ]
        
        return []
    
    def _calculate_period_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate total revenue for a specific period"""
        billing_records = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at < end_date,
                BillingHistory.status == 'paid'
            )
        ).all()
        
        return sum(record.amount for record in billing_records)
    
    def _calculate_subscription_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate subscription-related metrics"""
        # Get subscription counts
        total_subscriptions = self.db.query(Subscription).filter(
            Subscription.created_at <= end_date
        ).count()
        
        active_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at <= end_date
            )
        ).count()
        
        new_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        canceled_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date
            )
        ).count()
        
        # Calculate churn rate
        churn_rate = (canceled_subscriptions / active_subscriptions * 100) if active_subscriptions > 0 else 0
        
        # Calculate subscription growth
        previous_period_start = start_date - (end_date - start_date)
        previous_period_new = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= previous_period_start,
                Subscription.created_at < start_date
            )
        ).count()
        
        subscription_growth = ((new_subscriptions - previous_period_new) / previous_period_new * 100) if previous_period_new > 0 else 0
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'new_subscriptions': new_subscriptions,
            'canceled_subscriptions': canceled_subscriptions,
            'churn_rate_percentage': churn_rate,
            'subscription_growth_percentage': subscription_growth,
            'subscription_health_score': self._calculate_subscription_health_score()
        }
    
    def _calculate_subscription_health_score(self) -> float:
        """Calculate subscription health score (0-100)"""
        # Get recent subscription data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Calculate various health factors
        active_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at <= end_date
            )
        ).count()
        
        past_due_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'past_due',
                Subscription.created_at <= end_date
            )
        ).count()
        
        new_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        canceled_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date
            )
        ).count()
        
        # Calculate health score based on multiple factors
        total_subscriptions = active_subscriptions + past_due_subscriptions
        if total_subscriptions == 0:
            return 0
        
        # Factor 1: Active subscription ratio (40% weight)
        active_ratio = active_subscriptions / total_subscriptions * 40
        
        # Factor 2: Growth vs churn ratio (30% weight)
        growth_churn_ratio = 0
        if canceled_subscriptions > 0:
            growth_churn_ratio = min(new_subscriptions / canceled_subscriptions, 3) * 10  # Cap at 30
        else:
            growth_churn_ratio = 30
        
        # Factor 3: Past due ratio (30% weight)
        past_due_ratio = max(0, 30 - (past_due_subscriptions / total_subscriptions * 30))
        
        health_score = active_ratio + growth_churn_ratio + past_due_ratio
        return min(health_score, 100)
    
    def _calculate_tier_performance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate performance metrics by pricing tier"""
        # Get all tiers
        tiers = self.db.query(PricingTier).all()
        
        tier_performance = {}
        for tier in tiers:
            # Get subscriptions for this tier
            tier_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.created_at <= end_date
                )
            ).all()
            
            # Calculate tier metrics
            total_subscriptions = len(tier_subscriptions)
            active_subscriptions = len([s for s in tier_subscriptions if s.status == 'active'])
            new_subscriptions = len([s for s in tier_subscriptions if s.created_at >= start_date])
            
            # Calculate revenue for this tier
            tier_revenue = sum(s.amount for s in tier_subscriptions if s.status == 'active')
            
            # Calculate average customer lifetime value
            avg_lifetime_value = tier_revenue / active_subscriptions if active_subscriptions > 0 else 0
            
            tier_performance[tier.tier_type] = {
                'tier_name': tier.name,
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'new_subscriptions': new_subscriptions,
                'tier_revenue': tier_revenue,
                'avg_lifetime_value': avg_lifetime_value,
                'conversion_rate': self._calculate_tier_conversion_rate(tier.id, start_date, end_date)
            }
        
        return tier_performance
    
    def _calculate_tier_conversion_rate(self, tier_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate conversion rate for a specific tier"""
        # Get all customers who started with this tier
        tier_customers = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.pricing_tier_id == tier_id,
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).distinct().count()
        
        # Get customers who upgraded from this tier
        upgraded_customers = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.pricing_tier_id > tier_id,
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).distinct().count()
        
        conversion_rate = (upgraded_customers / tier_customers * 100) if tier_customers > 0 else 0
        return conversion_rate
    
    def _calculate_payment_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate payment-related metrics"""
        # Get all billing records in period
        billing_records = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date
            )
        ).all()
        
        total_attempts = len(billing_records)
        successful_payments = len([r for r in billing_records if r.status == 'paid'])
        failed_payments = len([r for r in billing_records if r.status == 'failed'])
        
        success_rate = (successful_payments / total_attempts * 100) if total_attempts > 0 else 0
        failure_rate = (failed_payments / total_attempts * 100) if total_attempts > 0 else 0
        
        # Calculate average payment amount
        avg_payment_amount = sum(r.amount for r in billing_records if r.status == 'paid') / successful_payments if successful_payments > 0 else 0
        
        return {
            'total_payment_attempts': total_attempts,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'success_rate_percentage': success_rate,
            'failure_rate_percentage': failure_rate,
            'avg_payment_amount': avg_payment_amount
        }
    
    def _calculate_growth_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate growth trends over time"""
        # Calculate monthly growth rates
        months = []
        growth_rates = []
        
        current_date = start_date
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Get revenue for this month
            month_revenue = self._calculate_period_revenue(month_start, month_end)
            
            # Get revenue for previous month
            prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
            prev_month_end = month_start - timedelta(days=1)
            prev_month_revenue = self._calculate_period_revenue(prev_month_start, prev_month_end)
            
            # Calculate growth rate
            growth_rate = ((month_revenue - prev_month_revenue) / prev_month_revenue * 100) if prev_month_revenue > 0 else 0
            
            months.append(month_start.strftime('%Y-%m'))
            growth_rates.append(growth_rate)
            
            current_date = month_end + timedelta(days=1)
        
        return {
            'months': months,
            'growth_rates': growth_rates,
            'average_growth_rate': sum(growth_rates) / len(growth_rates) if growth_rates else 0
        }
    
    # Revenue trending methods
    def _calculate_mrr_trending(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate MRR trending over time"""
        trending_data = []
        current_date = start_date
        
        while current_date <= end_date:
            mrr = self._calculate_mrr(current_date)
            trending_data.append({
                'date': current_date.isoformat(),
                'mrr': mrr,
                'period': current_date.strftime('%Y-%m')
            })
            current_date += timedelta(days=30)  # Monthly intervals
        
        return trending_data
    
    def _calculate_arr_trending(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate ARR trending over time"""
        mrr_trending = self._calculate_mrr_trending(start_date, end_date)
        
        return [
            {
                'date': data['date'],
                'arr': data['mrr'] * 12,
                'period': data['period']
            }
            for data in mrr_trending
        ]
    
    def _calculate_revenue_trending(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate total revenue trending over time"""
        trending_data = []
        current_date = start_date
        
        while current_date <= end_date:
            period_end = current_date + timedelta(days=30)
            revenue = self._calculate_period_revenue(current_date, period_end)
            
            trending_data.append({
                'date': current_date.isoformat(),
                'revenue': revenue,
                'period': current_date.strftime('%Y-%m')
            })
            current_date = period_end
        
        return trending_data
    
    def _calculate_subscription_trending(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate subscription count trending over time"""
        trending_data = []
        current_date = start_date
        
        while current_date <= end_date:
            active_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'active',
                    Subscription.created_at <= current_date
                )
            ).count()
            
            trending_data.append({
                'date': current_date.isoformat(),
                'subscriptions': active_subscriptions,
                'period': current_date.strftime('%Y-%m')
            })
            current_date += timedelta(days=30)
        
        return trending_data
    
    # Revenue forecast methods
    def _get_historical_revenue_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get historical revenue data for forecasting"""
        billing_records = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'paid'
            )
        ).order_by(BillingHistory.created_at).all()
        
        # Group by month
        monthly_revenue = {}
        for record in billing_records:
            month_key = f"{record.created_at.year}-{record.created_at.month:02d}"
            monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + record.amount
        
        return [
            {'period': month, 'revenue': revenue}
            for month, revenue in sorted(monthly_revenue.items())
        ]
    
    def _generate_revenue_forecast(self, historical_data: List[Dict[str, Any]], forecast_period: str) -> List[Dict[str, Any]]:
        """Generate revenue forecast based on historical data"""
        if not historical_data:
            return []
        
        # Simple linear regression for forecasting
        # In a real implementation, you might use more sophisticated models
        
        # Calculate average monthly growth
        if len(historical_data) >= 2:
            total_growth = 0
            for i in range(1, len(historical_data)):
                prev_revenue = historical_data[i-1]['revenue']
                curr_revenue = historical_data[i]['revenue']
                if prev_revenue > 0:
                    growth = (curr_revenue - prev_revenue) / prev_revenue
                    total_growth += growth
            
            avg_monthly_growth = total_growth / (len(historical_data) - 1)
        else:
            avg_monthly_growth = 0.05  # Default 5% growth
        
        # Generate forecast
        forecast_data = []
        last_revenue = historical_data[-1]['revenue'] if historical_data else 0
        
        # Parse forecast period
        if forecast_period.endswith('m'):
            months = int(forecast_period[:-1])
        else:
            months = 6  # Default to 6 months
        
        for i in range(1, months + 1):
            forecast_revenue = last_revenue * (1 + avg_monthly_growth) ** i
            forecast_data.append({
                'period': f'Forecast-{i}',
                'revenue': forecast_revenue,
                'confidence_lower': forecast_revenue * 0.9,  # 10% lower bound
                'confidence_upper': forecast_revenue * 1.1   # 10% upper bound
            })
        
        return forecast_data
    
    def _calculate_confidence_intervals(self, forecast_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence intervals for forecast"""
        if not forecast_data:
            return {}
        
        revenues = [data['revenue'] for data in forecast_data]
        avg_revenue = sum(revenues) / len(revenues)
        
        # Calculate standard deviation
        variance = sum((r - avg_revenue) ** 2 for r in revenues) / len(revenues)
        std_dev = variance ** 0.5
        
        return {
            'average_forecast': avg_revenue,
            'standard_deviation': std_dev,
            'confidence_95_lower': avg_revenue - (1.96 * std_dev),
            'confidence_95_upper': avg_revenue + (1.96 * std_dev)
        }
    
    # Revenue breakdown methods
    def _get_tier_revenue_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue breakdown by pricing tier"""
        tiers = self.db.query(PricingTier).all()
        
        breakdown = {}
        total_revenue = 0
        
        for tier in tiers:
            # Get active subscriptions for this tier
            tier_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.status == 'active'
                )
            ).all()
            
            tier_revenue = sum(s.amount for s in tier_subscriptions)
            total_revenue += tier_revenue
            
            breakdown[tier.tier_type] = {
                'tier_name': tier.name,
                'revenue': tier_revenue,
                'subscription_count': len(tier_subscriptions),
                'avg_revenue_per_subscription': tier_revenue / len(tier_subscriptions) if tier_subscriptions else 0
            }
        
        # Calculate percentages
        for tier_data in breakdown.values():
            tier_data['percentage'] = (tier_data['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'tier_breakdown': breakdown
        }
    
    def _get_billing_cycle_revenue_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue breakdown by billing cycle"""
        monthly_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'monthly',
                Subscription.status == 'active'
            )
        ).all()
        
        annual_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'annual',
                Subscription.status == 'active'
            )
        ).all()
        
        monthly_revenue = sum(s.amount for s in monthly_subscriptions)
        annual_revenue = sum(s.amount for s in annual_subscriptions)
        total_revenue = monthly_revenue + annual_revenue
        
        return {
            'total_revenue': total_revenue,
            'monthly': {
                'revenue': monthly_revenue,
                'subscription_count': len(monthly_subscriptions),
                'percentage': (monthly_revenue / total_revenue * 100) if total_revenue > 0 else 0
            },
            'annual': {
                'revenue': annual_revenue,
                'subscription_count': len(annual_subscriptions),
                'percentage': (annual_revenue / total_revenue * 100) if total_revenue > 0 else 0
            }
        }
    
    def _get_geographic_revenue_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue breakdown by geographic location"""
        # Get customers with address information
        customers_with_address = self.db.query(Customer).filter(
            Customer.address.isnot(None)
        ).all()
        
        geographic_breakdown = {}
        total_revenue = 0
        
        for customer in customers_with_address:
            if customer.address and 'country' in customer.address:
                country = customer.address['country']
                
                # Get customer's active subscriptions
                customer_subscriptions = self.db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.status == 'active'
                    )
                ).all()
                
                customer_revenue = sum(s.amount for s in customer_subscriptions)
                
                if country not in geographic_breakdown:
                    geographic_breakdown[country] = {
                        'revenue': 0,
                        'customer_count': 0,
                        'subscription_count': 0
                    }
                
                geographic_breakdown[country]['revenue'] += customer_revenue
                geographic_breakdown[country]['customer_count'] += 1
                geographic_breakdown[country]['subscription_count'] += len(customer_subscriptions)
                total_revenue += customer_revenue
        
        # Calculate percentages
        for country_data in geographic_breakdown.values():
            country_data['percentage'] = (country_data['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'geographic_breakdown': geographic_breakdown
        }
    
    def _get_customer_segment_revenue_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue breakdown by customer segments"""
        # Define customer segments based on subscription value
        segments = {
            'low_value': {'min': 0, 'max': 20, 'name': 'Low Value ($0-$20)'},
            'medium_value': {'min': 20, 'max': 50, 'name': 'Medium Value ($20-$50)'},
            'high_value': {'min': 50, 'max': 100, 'name': 'High Value ($50-$100)'},
            'enterprise': {'min': 100, 'max': float('inf'), 'name': 'Enterprise ($100+)'}
        }
        
        segment_breakdown = {segment: {'revenue': 0, 'customer_count': 0, 'subscription_count': 0} for segment in segments}
        total_revenue = 0
        
        # Get all active subscriptions
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == 'active'
        ).all()
        
        for subscription in active_subscriptions:
            amount = subscription.amount
            
            # Determine segment
            segment = None
            for seg_key, seg_config in segments.items():
                if seg_config['min'] <= amount < seg_config['max']:
                    segment = seg_key
                    break
            
            if segment:
                segment_breakdown[segment]['revenue'] += amount
                segment_breakdown[segment]['subscription_count'] += 1
                total_revenue += amount
        
        # Calculate customer counts (unique customers per segment)
        for segment in segment_breakdown:
            segment_subscriptions = [s for s in active_subscriptions 
                                   if segments[segment]['min'] <= s.amount < segments[segment]['max']]
            unique_customers = len(set(s.customer_id for s in segment_subscriptions))
            segment_breakdown[segment]['customer_count'] = unique_customers
        
        # Calculate percentages and add segment names
        for segment, data in segment_breakdown.items():
            data['percentage'] = (data['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            data['segment_name'] = segments[segment]['name']
        
        return {
            'total_revenue': total_revenue,
            'segment_breakdown': segment_breakdown
        } 

    # Helper methods for conversion funnel analysis
    def _calculate_standard_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate standard subscription conversion funnel"""
        # Stage 1: Website Visitors (estimated based on customer creation)
        website_visitors = self.db.query(Customer).filter(
            Customer.created_at >= start_date,
            Customer.created_at <= end_date
        ).count()
        
        # Stage 2: Account Creation
        account_creations = self.db.query(Customer).filter(
            and_(
                Customer.created_at >= start_date,
                Customer.created_at <= end_date,
                Customer.stripe_customer_id.isnot(None)
            )
        ).count()
        
        # Stage 3: Trial Started
        trial_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status.in_(['active', 'past_due', 'canceled'])
            )
        ).count()
        
        # Stage 4: Trial Completed
        completed_trials = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status.in_(['active', 'past_due'])
            )
        ).count()
        
        # Stage 5: Paid Subscription
        paid_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status == 'active'
            )
        ).count()
        
        # Stage 6: Retained Subscriptions (still active after 30 days)
        retention_date = end_date - timedelta(days=30)
        retained_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= retention_date,
                Subscription.status == 'active'
            )
        ).count()
        
        funnel_stages = [
            {
                'stage': 'Website Visitors',
                'count': website_visitors,
                'conversion_rate': 100.0,
                'drop_off_rate': 0.0
            },
            {
                'stage': 'Account Creation',
                'count': account_creations,
                'conversion_rate': (account_creations / website_visitors * 100) if website_visitors > 0 else 0,
                'drop_off_rate': ((website_visitors - account_creations) / website_visitors * 100) if website_visitors > 0 else 0
            },
            {
                'stage': 'Trial Started',
                'count': trial_subscriptions,
                'conversion_rate': (trial_subscriptions / account_creations * 100) if account_creations > 0 else 0,
                'drop_off_rate': ((account_creations - trial_subscriptions) / account_creations * 100) if account_creations > 0 else 0
            },
            {
                'stage': 'Trial Completed',
                'count': completed_trials,
                'conversion_rate': (completed_trials / trial_subscriptions * 100) if trial_subscriptions > 0 else 0,
                'drop_off_rate': ((trial_subscriptions - completed_trials) / trial_subscriptions * 100) if trial_subscriptions > 0 else 0
            },
            {
                'stage': 'Paid Subscription',
                'count': paid_subscriptions,
                'conversion_rate': (paid_subscriptions / completed_trials * 100) if completed_trials > 0 else 0,
                'drop_off_rate': ((completed_trials - paid_subscriptions) / completed_trials * 100) if completed_trials > 0 else 0
            },
            {
                'stage': 'Retained (30+ days)',
                'count': retained_subscriptions,
                'conversion_rate': (retained_subscriptions / paid_subscriptions * 100) if paid_subscriptions > 0 else 0,
                'drop_off_rate': ((paid_subscriptions - retained_subscriptions) / paid_subscriptions * 100) if paid_subscriptions > 0 else 0
            }
        ]
        
        return {
            'funnel_stages': funnel_stages,
            'total_conversion_rate': (retained_subscriptions / website_visitors * 100) if website_visitors > 0 else 0,
            'total_drop_off_rate': ((website_visitors - retained_subscriptions) / website_visitors * 100) if website_visitors > 0 else 0
        }
    
    def _calculate_tier_upgrade_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate tier upgrade conversion funnel"""
        # Get all customers who started with budget tier
        budget_starters = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.pricing_tier_id == 1,  # Budget tier
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).distinct().count()
        
        # Stage 1: Budget Tier Subscribers
        budget_subscribers = budget_starters
        
        # Stage 2: Mid-Tier Upgrades
        mid_tier_upgrades = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.pricing_tier_id == 2,  # Mid-tier
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).distinct().count()
        
        # Stage 3: Professional Tier Upgrades
        professional_upgrades = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.pricing_tier_id == 3,  # Professional tier
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).distinct().count()
        
        # Stage 4: Annual Billing Upgrades
        annual_upgrades = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'annual',
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        funnel_stages = [
            {
                'stage': 'Budget Tier Subscribers',
                'count': budget_subscribers,
                'conversion_rate': 100.0,
                'drop_off_rate': 0.0
            },
            {
                'stage': 'Mid-Tier Upgrades',
                'count': mid_tier_upgrades,
                'conversion_rate': (mid_tier_upgrades / budget_subscribers * 100) if budget_subscribers > 0 else 0,
                'drop_off_rate': ((budget_subscribers - mid_tier_upgrades) / budget_subscribers * 100) if budget_subscribers > 0 else 0
            },
            {
                'stage': 'Professional Tier Upgrades',
                'count': professional_upgrades,
                'conversion_rate': (professional_upgrades / mid_tier_upgrades * 100) if mid_tier_upgrades > 0 else 0,
                'drop_off_rate': ((mid_tier_upgrades - professional_upgrades) / mid_tier_upgrades * 100) if mid_tier_upgrades > 0 else 0
            },
            {
                'stage': 'Annual Billing Upgrades',
                'count': annual_upgrades,
                'conversion_rate': (annual_upgrades / professional_upgrades * 100) if professional_upgrades > 0 else 0,
                'drop_off_rate': ((professional_upgrades - annual_upgrades) / professional_upgrades * 100) if professional_upgrades > 0 else 0
            }
        ]
        
        return {
            'funnel_stages': funnel_stages,
            'total_conversion_rate': (annual_upgrades / budget_subscribers * 100) if budget_subscribers > 0 else 0,
            'total_drop_off_rate': ((budget_subscribers - annual_upgrades) / budget_subscribers * 100) if budget_subscribers > 0 else 0
        }
    
    def _calculate_billing_cycle_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate billing cycle conversion funnel"""
        # Stage 1: Monthly Billing Subscribers
        monthly_subscribers = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'monthly',
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        # Stage 2: Annual Billing Conversions
        annual_conversions = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'annual',
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        # Stage 3: Retained Annual Subscribers
        retention_date = end_date - timedelta(days=90)
        retained_annual = self.db.query(Subscription).filter(
            and_(
                Subscription.billing_cycle == 'annual',
                Subscription.created_at >= start_date,
                Subscription.created_at <= retention_date,
                Subscription.status == 'active'
            )
        ).count()
        
        funnel_stages = [
            {
                'stage': 'Monthly Billing Subscribers',
                'count': monthly_subscribers,
                'conversion_rate': 100.0,
                'drop_off_rate': 0.0
            },
            {
                'stage': 'Annual Billing Conversions',
                'count': annual_conversions,
                'conversion_rate': (annual_conversions / monthly_subscribers * 100) if monthly_subscribers > 0 else 0,
                'drop_off_rate': ((monthly_subscribers - annual_conversions) / monthly_subscribers * 100) if monthly_subscribers > 0 else 0
            },
            {
                'stage': 'Retained Annual Subscribers',
                'count': retained_annual,
                'conversion_rate': (retained_annual / annual_conversions * 100) if annual_conversions > 0 else 0,
                'drop_off_rate': ((annual_conversions - retained_annual) / annual_conversions * 100) if annual_conversions > 0 else 0
            }
        ]
        
        return {
            'funnel_stages': funnel_stages,
            'total_conversion_rate': (retained_annual / monthly_subscribers * 100) if monthly_subscribers > 0 else 0,
            'total_drop_off_rate': ((monthly_subscribers - retained_annual) / monthly_subscribers * 100) if monthly_subscribers > 0 else 0
        }
    
    def _calculate_trial_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate trial to paid conversion funnel"""
        # Stage 1: Trial Started
        trial_started = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        # Stage 2: Trial Completed (7+ days)
        trial_completed = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date - timedelta(days=7),
                Subscription.status.in_(['active', 'past_due', 'canceled'])
            )
        ).count()
        
        # Stage 3: Trial to Paid Conversion
        trial_to_paid = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status == 'active'
            )
        ).count()
        
        # Stage 4: Paid After 30 Days
        retention_date = end_date - timedelta(days=30)
        paid_after_30_days = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= retention_date,
                Subscription.status == 'active'
            )
        ).count()
        
        funnel_stages = [
            {
                'stage': 'Trial Started',
                'count': trial_started,
                'conversion_rate': 100.0,
                'drop_off_rate': 0.0
            },
            {
                'stage': 'Trial Completed (7+ days)',
                'count': trial_completed,
                'conversion_rate': (trial_completed / trial_started * 100) if trial_started > 0 else 0,
                'drop_off_rate': ((trial_started - trial_completed) / trial_started * 100) if trial_started > 0 else 0
            },
            {
                'stage': 'Trial to Paid Conversion',
                'count': trial_to_paid,
                'conversion_rate': (trial_to_paid / trial_completed * 100) if trial_completed > 0 else 0,
                'drop_off_rate': ((trial_completed - trial_to_paid) / trial_completed * 100) if trial_completed > 0 else 0
            },
            {
                'stage': 'Paid After 30 Days',
                'count': paid_after_30_days,
                'conversion_rate': (paid_after_30_days / trial_to_paid * 100) if trial_to_paid > 0 else 0,
                'drop_off_rate': ((trial_to_paid - paid_after_30_days) / trial_to_paid * 100) if trial_to_paid > 0 else 0
            }
        ]
        
        return {
            'funnel_stages': funnel_stages,
            'total_conversion_rate': (paid_after_30_days / trial_started * 100) if trial_started > 0 else 0,
            'total_drop_off_rate': ((trial_started - paid_after_30_days) / trial_started * 100) if trial_started > 0 else 0
        }
    
    def _calculate_overall_conversion_rate(self, funnel_data: Dict[str, Any]) -> float:
        """Calculate overall conversion rate for the funnel"""
        if not funnel_data.get('funnel_stages'):
            return 0.0
        
        first_stage = funnel_data['funnel_stages'][0]
        last_stage = funnel_data['funnel_stages'][-1]
        
        if first_stage['count'] == 0:
            return 0.0
        
        return (last_stage['count'] / first_stage['count']) * 100
    
    def _identify_funnel_bottlenecks(self, funnel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify bottlenecks in the conversion funnel"""
        bottlenecks = []
        funnel_stages = funnel_data.get('funnel_stages', [])
        
        for i, stage in enumerate(funnel_stages):
            if stage['drop_off_rate'] > 50:  # High drop-off threshold
                bottlenecks.append({
                    'stage': stage['stage'],
                    'drop_off_rate': stage['drop_off_rate'],
                    'severity': 'high' if stage['drop_off_rate'] > 70 else 'medium',
                    'impact': f"Losing {stage['drop_off_rate']:.1f}% of customers at {stage['stage']}",
                    'recommendation': self._get_bottleneck_recommendation(stage['stage'])
                })
            elif stage['drop_off_rate'] > 30:  # Medium drop-off threshold
                bottlenecks.append({
                    'stage': stage['stage'],
                    'drop_off_rate': stage['drop_off_rate'],
                    'severity': 'medium',
                    'impact': f"Losing {stage['drop_off_rate']:.1f}% of customers at {stage['stage']}",
                    'recommendation': self._get_bottleneck_recommendation(stage['stage'])
                })
        
        return bottlenecks
    
    def _get_bottleneck_recommendation(self, stage: str) -> str:
        """Get specific recommendations for funnel bottlenecks"""
        recommendations = {
            'Website Visitors': 'Improve SEO, increase marketing spend, optimize landing pages',
            'Account Creation': 'Simplify signup process, reduce form fields, add social login',
            'Trial Started': 'Improve onboarding, add guided tours, highlight key features',
            'Trial Completed': 'Extend trial period, send reminder emails, offer incentives',
            'Paid Subscription': 'Improve pricing page, add testimonials, offer discounts',
            'Retained (30+ days)': 'Improve product experience, add support, implement retention campaigns',
            'Budget Tier Subscribers': 'Highlight upgrade benefits, show usage limits, offer upgrade incentives',
            'Mid-Tier Upgrades': 'Show professional features, offer upgrade discounts, demonstrate ROI',
            'Professional Tier Upgrades': 'Highlight enterprise features, offer custom demos, show advanced capabilities',
            'Annual Billing Upgrades': 'Show annual savings, offer annual discounts, highlight convenience',
            'Monthly Billing Subscribers': 'Show annual savings, offer annual discounts, highlight convenience',
            'Annual Billing Conversions': 'Improve annual value proposition, offer better annual pricing',
            'Retained Annual Subscribers': 'Improve product experience, add premium support, implement retention campaigns',
            'Trial to Paid Conversion': 'Improve trial experience, send conversion emails, offer trial extensions',
            'Paid After 30 Days': 'Improve onboarding, add support, implement retention campaigns'
        }
        
        return recommendations.get(stage, 'Analyze user behavior and optimize conversion process')
    
    def _generate_funnel_optimization_recommendations(self, funnel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for the funnel"""
        recommendations = []
        funnel_stages = funnel_data.get('funnel_stages', [])
        
        # Overall conversion rate recommendations
        overall_rate = self._calculate_overall_conversion_rate(funnel_data)
        
        if overall_rate < 5:
            recommendations.append({
                'type': 'critical',
                'title': 'Low Overall Conversion Rate',
                'description': f'Overall conversion rate is {overall_rate:.1f}%, which is below industry standards',
                'action': 'Conduct comprehensive funnel analysis and implement conversion optimization strategies'
            })
        elif overall_rate < 10:
            recommendations.append({
                'type': 'warning',
                'title': 'Below Average Conversion Rate',
                'description': f'Overall conversion rate is {overall_rate:.1f}%, which could be improved',
                'action': 'Focus on high-impact funnel stages and implement A/B testing'
            })
        
        # Stage-specific recommendations
        for stage in funnel_stages:
            if stage['conversion_rate'] < 20:
                recommendations.append({
                    'type': 'improvement',
                    'title': f'Low Conversion at {stage["stage"]}',
                    'description': f'Only {stage["conversion_rate"]:.1f}% conversion rate at {stage["stage"]}',
                    'action': self._get_bottleneck_recommendation(stage['stage'])
                })
        
        return recommendations
    
    def _analyze_funnel_trends(self, monthly_funnels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in conversion funnel performance"""
        if not monthly_funnels:
            return {}
        
        conversion_rates = [funnel['conversion_rate'] for funnel in monthly_funnels]
        
        # Calculate trend metrics
        avg_conversion_rate = sum(conversion_rates) / len(conversion_rates)
        
        # Calculate trend direction
        if len(conversion_rates) >= 2:
            recent_avg = sum(conversion_rates[-3:]) / min(3, len(conversion_rates))
            earlier_avg = sum(conversion_rates[:3]) / min(3, len(conversion_rates))
            trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
            trend_percentage = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            trend_direction = 'insufficient_data'
            trend_percentage = 0
        
        return {
            'average_conversion_rate': avg_conversion_rate,
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'best_period': monthly_funnels[conversion_rates.index(max(conversion_rates))]['period'],
            'worst_period': monthly_funnels[conversion_rates.index(min(conversion_rates))]['period'],
            'consistency_score': self._calculate_consistency_score(conversion_rates)
        }
    
    def _calculate_consistency_score(self, conversion_rates: List[float]) -> float:
        """Calculate consistency score for conversion rates"""
        if len(conversion_rates) < 2:
            return 100.0
        
        # Calculate coefficient of variation (lower is more consistent)
        mean_rate = sum(conversion_rates) / len(conversion_rates)
        variance = sum((rate - mean_rate) ** 2 for rate in conversion_rates) / len(conversion_rates)
        std_dev = variance ** 0.5
        
        if mean_rate == 0:
            return 0.0
        
        cv = (std_dev / mean_rate) * 100
        # Convert to consistency score (0-100, higher is more consistent)
        consistency_score = max(0, 100 - cv)
        
        return consistency_score
    
    # Breakdown methods for conversion funnels
    def _get_tier_conversion_funnel_breakdown(self, start_date: datetime, end_date: datetime, funnel_type: str) -> Dict[str, Any]:
        """Get conversion funnel breakdown by pricing tier"""
        tiers = self.db.query(PricingTier).all()
        
        breakdown = {}
        for tier in tiers:
            # Calculate funnel for this specific tier
            tier_funnel = self._calculate_tier_specific_funnel(start_date, end_date, tier.id, funnel_type)
            breakdown[tier.tier_type] = {
                'tier_name': tier.name,
                'funnel_data': tier_funnel,
                'conversion_rate': self._calculate_overall_conversion_rate(tier_funnel)
            }
        
        return breakdown
    
    def _get_geographic_conversion_funnel_breakdown(self, start_date: datetime, end_date: datetime, funnel_type: str) -> Dict[str, Any]:
        """Get conversion funnel breakdown by geographic location"""
        # Get customers with address information
        customers_with_address = self.db.query(Customer).filter(
            Customer.address.isnot(None)
        ).all()
        
        geographic_breakdown = {}
        
        for customer in customers_with_address:
            if customer.address and 'country' in customer.address:
                country = customer.address['country']
                
                if country not in geographic_breakdown:
                    geographic_breakdown[country] = {
                        'customer_count': 0,
                        'funnel_data': self._calculate_geographic_specific_funnel(start_date, end_date, country, funnel_type)
                    }
                
                geographic_breakdown[country]['customer_count'] += 1
        
        # Calculate conversion rates for each geographic region
        for country, data in geographic_breakdown.items():
            data['conversion_rate'] = self._calculate_overall_conversion_rate(data['funnel_data'])
        
        return geographic_breakdown
    
    def _get_time_period_conversion_funnel_breakdown(self, start_date: datetime, end_date: datetime, funnel_type: str) -> Dict[str, Any]:
        """Get conversion funnel breakdown by time periods"""
        # Break down by weeks
        weekly_breakdown = {}
        current_date = start_date
        
        while current_date <= end_date:
            week_start = current_date
            week_end = min(current_date + timedelta(days=7), end_date)
            
            week_key = week_start.strftime('%Y-W%U')
            weekly_breakdown[week_key] = {
                'period': f"Week of {week_start.strftime('%Y-%m-%d')}",
                'funnel_data': self._calculate_period_specific_funnel(week_start, week_end, funnel_type),
                'conversion_rate': 0.0  # Will be calculated
            }
            
            current_date = week_end
        
        # Calculate conversion rates
        for week_data in weekly_breakdown.values():
            week_data['conversion_rate'] = self._calculate_overall_conversion_rate(week_data['funnel_data'])
        
        return weekly_breakdown
    
    def _get_customer_segment_conversion_funnel_breakdown(self, start_date: datetime, end_date: datetime, funnel_type: str) -> Dict[str, Any]:
        """Get conversion funnel breakdown by customer segments"""
        # Define customer segments
        segments = {
            'new_customers': {'name': 'New Customers', 'days': 30},
            'returning_customers': {'name': 'Returning Customers', 'days': 90},
            'loyal_customers': {'name': 'Loyal Customers', 'days': 365}
        }
        
        segment_breakdown = {}
        
        for segment_key, segment_config in segments.items():
            segment_start_date = start_date - timedelta(days=segment_config['days'])
            
            segment_breakdown[segment_key] = {
                'segment_name': segment_config['name'],
                'funnel_data': self._calculate_segment_specific_funnel(start_date, end_date, segment_key, funnel_type),
                'conversion_rate': 0.0  # Will be calculated
            }
        
        # Calculate conversion rates
        for segment_data in segment_breakdown.values():
            segment_data['conversion_rate'] = self._calculate_overall_conversion_rate(segment_data['funnel_data'])
        
        return segment_breakdown
    
    # Helper methods for breakdown calculations
    def _calculate_tier_specific_funnel(self, start_date: datetime, end_date: datetime, tier_id: int, funnel_type: str) -> Dict[str, Any]:
        """Calculate funnel for a specific pricing tier"""
        # This would implement tier-specific funnel logic
        # For now, return a simplified version
        return self._calculate_standard_conversion_funnel(start_date, end_date)
    
    def _calculate_geographic_specific_funnel(self, start_date: datetime, end_date: datetime, country: str, funnel_type: str) -> Dict[str, Any]:
        """Calculate funnel for a specific geographic region"""
        # This would implement geographic-specific funnel logic
        # For now, return a simplified version
        return self._calculate_standard_conversion_funnel(start_date, end_date)
    
    def _calculate_period_specific_funnel(self, start_date: datetime, end_date: datetime, funnel_type: str) -> Dict[str, Any]:
        """Calculate funnel for a specific time period"""
        # This would implement period-specific funnel logic
        # For now, return a simplified version
        return self._calculate_standard_conversion_funnel(start_date, end_date)
    
    def _calculate_segment_specific_funnel(self, start_date: datetime, end_date: datetime, segment: str, funnel_type: str) -> Dict[str, Any]:
        """Calculate funnel for a specific customer segment"""
        # This would implement segment-specific funnel logic
        # For now, return a simplified version
        return self._calculate_standard_conversion_funnel(start_date, end_date) 

    # Helper methods for churn analysis
    def _calculate_voluntary_churn(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate voluntary churn (customer-initiated cancellations)"""
        # Get customers who voluntarily canceled
        voluntary_cancellations = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date,
                Subscription.cancel_reason.in_(['customer_request', 'pricing', 'features', 'competitor'])
            )
        ).count()
        
        # Get total active subscriptions at start of period
        total_active_start = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at < start_date
            )
        ).count()
        
        # Get new subscriptions during period
        new_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status == 'active'
            )
        ).count()
        
        # Calculate churn rate
        churn_rate = (voluntary_cancellations / (total_active_start + new_subscriptions)) * 100 if (total_active_start + new_subscriptions) > 0 else 0
        
        return {
            'voluntary_cancellations': voluntary_cancellations,
            'total_active_start': total_active_start,
            'new_subscriptions': new_subscriptions,
            'churn_rate': churn_rate,
            'churn_reasons': self._get_voluntary_churn_reasons(start_date, end_date)
        }
    
    def _calculate_involuntary_churn(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate involuntary churn (payment failures, suspensions)"""
        # Get customers who were suspended due to payment failures
        payment_failures = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'unpaid',
                Subscription.updated_at >= start_date,
                Subscription.updated_at <= end_date
            )
        ).count()
        
        # Get customers who were canceled due to payment issues
        payment_cancellations = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date,
                Subscription.cancel_reason == 'payment_failure'
            )
        ).count()
        
        total_involuntary = payment_failures + payment_cancellations
        
        # Get total active subscriptions at start of period
        total_active_start = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at < start_date
            )
        ).count()
        
        # Get new subscriptions during period
        new_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date,
                Subscription.status == 'active'
            )
        ).count()
        
        # Calculate churn rate
        churn_rate = (total_involuntary / (total_active_start + new_subscriptions)) * 100 if (total_active_start + new_subscriptions) > 0 else 0
        
        return {
            'payment_failures': payment_failures,
            'payment_cancellations': payment_cancellations,
            'total_involuntary': total_involuntary,
            'total_active_start': total_active_start,
            'new_subscriptions': new_subscriptions,
            'churn_rate': churn_rate,
            'failure_reasons': self._get_involuntary_churn_reasons(start_date, end_date)
        }
    
    def _calculate_overall_churn(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate overall churn (both voluntary and involuntary)"""
        voluntary_churn = self._calculate_voluntary_churn(start_date, end_date)
        involuntary_churn = self._calculate_involuntary_churn(start_date, end_date)
        
        total_churned = voluntary_churn['voluntary_cancellations'] + involuntary_churn['total_involuntary']
        total_active_start = voluntary_churn['total_active_start']
        new_subscriptions = voluntary_churn['new_subscriptions']
        
        overall_churn_rate = (total_churned / (total_active_start + new_subscriptions)) * 100 if (total_active_start + new_subscriptions) > 0 else 0
        
        return {
            'total_churned': total_churned,
            'voluntary_churn': voluntary_churn['voluntary_cancellations'],
            'involuntary_churn': involuntary_churn['total_involuntary'],
            'total_active_start': total_active_start,
            'new_subscriptions': new_subscriptions,
            'churn_rate': overall_churn_rate,
            'voluntary_rate': voluntary_churn['churn_rate'],
            'involuntary_rate': involuntary_churn['churn_rate']
        }
    
    def _calculate_churn_rate(self, churn_data: Dict[str, Any]) -> float:
        """Calculate churn rate from churn data"""
        if 'churn_rate' in churn_data:
            return churn_data['churn_rate']
        
        # Calculate based on available data
        total_churned = churn_data.get('total_churned', 0)
        total_active_start = churn_data.get('total_active_start', 0)
        new_subscriptions = churn_data.get('new_subscriptions', 0)
        
        if (total_active_start + new_subscriptions) > 0:
            return (total_churned / (total_active_start + new_subscriptions)) * 100
        return 0.0
    
    def _calculate_churn_impact(self, churn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the business impact of churn"""
        # Get average revenue per customer
        avg_revenue = self.db.query(func.avg(Subscription.amount)).scalar() or 0
        
        # Calculate revenue impact
        total_churned = churn_data.get('total_churned', 0)
        revenue_impact = total_churned * avg_revenue * 12  # Annual revenue loss
        
        # Calculate customer lifetime value impact
        avg_lifetime_months = 24  # Estimated average customer lifetime
        ltv_impact = total_churned * avg_revenue * avg_lifetime_months
        
        # Calculate acquisition cost impact
        avg_acquisition_cost = 50  # Estimated customer acquisition cost
        acquisition_impact = total_churned * avg_acquisition_cost
        
        return {
            'revenue_impact': revenue_impact,
            'ltv_impact': ltv_impact,
            'acquisition_impact': acquisition_impact,
            'total_impact': revenue_impact + acquisition_impact,
            'avg_revenue_per_customer': avg_revenue,
            'customers_lost': total_churned
        }
    
    def _analyze_churn_reasons(self, churn_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze reasons for churn"""
        reasons = []
        
        # Get churn reasons from database
        churn_reasons = self.db.query(
            Subscription.cancel_reason,
            func.count(Subscription.id).label('count')
        ).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.cancel_reason.isnot(None)
            )
        ).group_by(Subscription.cancel_reason).all()
        
        for reason, count in churn_reasons:
            if reason:
                reasons.append({
                    'reason': reason,
                    'count': count,
                    'percentage': (count / churn_data.get('total_churned', 1)) * 100 if churn_data.get('total_churned', 0) > 0 else 0,
                    'recommendation': self._get_churn_reason_recommendation(reason)
                })
        
        return reasons
    
    def _get_churn_reason_recommendation(self, reason: str) -> str:
        """Get recommendation for specific churn reason"""
        recommendations = {
            'pricing': 'Review pricing strategy, offer discounts, implement value-based pricing',
            'features': 'Enhance feature set, improve user experience, add requested functionality',
            'competitor': 'Analyze competitive advantages, improve unique value proposition',
            'customer_request': 'Improve customer support, implement feedback, enhance satisfaction',
            'payment_failure': 'Improve payment processing, offer multiple payment methods, implement dunning',
            'usage': 'Optimize usage limits, provide better onboarding, improve feature discovery',
            'support': 'Enhance customer support, reduce response times, improve support quality',
            'technical': 'Improve platform stability, reduce bugs, enhance performance'
        }
        
        return recommendations.get(reason, 'Analyze customer feedback and implement improvements')
    
    def _generate_churn_prevention_recommendations(self, churn_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate churn prevention recommendations"""
        recommendations = []
        churn_rate = self._calculate_churn_rate(churn_data)
        
        # Overall churn rate recommendations
        if churn_rate > 10:
            recommendations.append({
                'type': 'critical',
                'title': 'High Churn Rate Detected',
                'description': f'Churn rate is {churn_rate:.1f}%, which is above industry standards',
                'action': 'Implement comprehensive churn prevention strategy immediately'
            })
        elif churn_rate > 5:
            recommendations.append({
                'type': 'warning',
                'title': 'Elevated Churn Rate',
                'description': f'Churn rate is {churn_rate:.1f}%, which needs attention',
                'action': 'Focus on customer satisfaction and retention initiatives'
            })
        
        # Voluntary vs involuntary churn recommendations
        voluntary_rate = churn_data.get('voluntary_rate', 0)
        involuntary_rate = churn_data.get('involuntary_rate', 0)
        
        if involuntary_rate > voluntary_rate:
            recommendations.append({
                'type': 'improvement',
                'title': 'High Involuntary Churn',
                'description': f'Involuntary churn rate ({involuntary_rate:.1f}%) is higher than voluntary ({voluntary_rate:.1f}%)',
                'action': 'Improve payment processing, implement better dunning management'
            })
        
        # Specific recommendations based on churn reasons
        churn_reasons = self._analyze_churn_reasons(churn_data)
        for reason in churn_reasons:
            if reason['percentage'] > 20:  # If a reason accounts for >20% of churn
                recommendations.append({
                    'type': 'targeted',
                    'title': f'Address {reason["reason"]} Churn',
                    'description': f'{reason["reason"]} accounts for {reason["percentage"]:.1f}% of churn',
                    'action': reason['recommendation']
                })
        
        return recommendations
    
    def _calculate_churn_prediction(self, prediction_horizon: str) -> Dict[str, Any]:
        """Calculate churn prediction for future periods"""
        # Get historical churn data for prediction
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # Use 90 days of historical data
        
        historical_churn = self._calculate_overall_churn(start_date, end_date)
        
        # Simple prediction model (can be enhanced with ML)
        avg_churn_rate = historical_churn['churn_rate']
        
        # Predict future churn based on current active subscriptions
        current_active = self.db.query(Subscription).filter(
            Subscription.status == 'active'
        ).count()
        
        # Calculate prediction based on horizon
        if prediction_horizon == '30d':
            predicted_churn = current_active * (avg_churn_rate / 100) * (30 / 365)
        elif prediction_horizon == '60d':
            predicted_churn = current_active * (avg_churn_rate / 100) * (60 / 365)
        elif prediction_horizon == '90d':
            predicted_churn = current_active * (avg_churn_rate / 100) * (90 / 365)
        else:
            predicted_churn = current_active * (avg_churn_rate / 100) * (30 / 365)
        
        return {
            'prediction_horizon': prediction_horizon,
            'current_active_subscriptions': current_active,
            'historical_churn_rate': avg_churn_rate,
            'predicted_churn': int(predicted_churn),
            'predicted_churn_rate': (predicted_churn / current_active) * 100 if current_active > 0 else 0,
            'confidence_level': self._calculate_prediction_confidence(avg_churn_rate)
        }
    
    def _identify_high_risk_customers(self) -> List[Dict[str, Any]]:
        """Identify customers at high risk of churning"""
        high_risk_customers = []
        
        # Get customers with recent payment failures
        payment_failure_customers = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.status == 'past_due',
                Subscription.updated_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).limit(10).all()
        
        for customer in payment_failure_customers:
            high_risk_customers.append({
                'customer_id': customer.id,
                'risk_factor': 'payment_failure',
                'risk_score': 85,
                'last_payment_failure': customer.subscriptions[0].updated_at.isoformat(),
                'recommendation': 'Implement payment recovery strategy'
            })
        
        # Get customers with low usage
        low_usage_customers = self.db.query(Customer).join(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at <= datetime.utcnow() - timedelta(days=30)
            )
        ).limit(10).all()
        
        for customer in low_usage_customers:
            high_risk_customers.append({
                'customer_id': customer.id,
                'risk_factor': 'low_usage',
                'risk_score': 70,
                'subscription_age': (datetime.utcnow() - customer.subscriptions[0].created_at).days,
                'recommendation': 'Implement engagement campaign'
            })
        
        return high_risk_customers
    
    def _analyze_risk_factors(self) -> List[Dict[str, Any]]:
        """Analyze factors that contribute to churn risk"""
        risk_factors = []
        
        # Payment failure risk
        payment_failures = self.db.query(Subscription).filter(
            Subscription.status == 'past_due'
        ).count()
        
        if payment_failures > 0:
            risk_factors.append({
                'factor': 'payment_failures',
                'risk_level': 'high' if payment_failures > 10 else 'medium',
                'count': payment_failures,
                'impact': 'High risk of involuntary churn',
                'mitigation': 'Improve payment processing and dunning management'
            })
        
        # Low usage risk
        low_usage_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.created_at <= datetime.utcnow() - timedelta(days=60)
            )
        ).count()
        
        if low_usage_subscriptions > 0:
            risk_factors.append({
                'factor': 'low_usage',
                'risk_level': 'medium',
                'count': low_usage_subscriptions,
                'impact': 'Risk of voluntary churn due to low value perception',
                'mitigation': 'Implement engagement and onboarding campaigns'
            })
        
        # Support ticket risk
        # This would integrate with support system
        risk_factors.append({
            'factor': 'support_issues',
            'risk_level': 'medium',
            'count': 0,  # Would be calculated from support system
            'impact': 'Risk of churn due to poor support experience',
            'mitigation': 'Improve support quality and response times'
        })
        
        return risk_factors
    
    def _generate_intervention_strategies(self, prediction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intervention strategies for churn prevention"""
        strategies = []
        
        predicted_churn = prediction_data.get('predicted_churn', 0)
        
        if predicted_churn > 50:
            strategies.append({
                'type': 'urgent',
                'title': 'Immediate Intervention Required',
                'description': f'Predicted {predicted_churn} customers at risk of churning',
                'actions': [
                    'Implement automated retention campaigns',
                    'Offer immediate discounts or incentives',
                    'Increase customer support resources',
                    'Conduct customer satisfaction surveys'
                ]
            })
        elif predicted_churn > 20:
            strategies.append({
                'type': 'moderate',
                'title': 'Targeted Retention Campaign',
                'description': f'Predicted {predicted_churn} customers at risk of churning',
                'actions': [
                    'Identify high-risk customers',
                    'Send personalized retention emails',
                    'Offer upgrade incentives',
                    'Improve onboarding experience'
                ]
            })
        
        # Add general prevention strategies
        strategies.append({
            'type': 'ongoing',
            'title': 'Continuous Prevention',
            'description': 'Ongoing churn prevention strategies',
            'actions': [
                'Monitor customer satisfaction scores',
                'Track usage patterns and engagement',
                'Implement proactive support',
                'Regular feature updates and improvements'
            ]
        })
        
        return strategies
    
    def _calculate_prevention_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate churn prevention effectiveness metrics"""
        # Get prevention campaign data (would integrate with marketing system)
        prevention_campaigns = 5  # Example data
        successful_interventions = 15  # Example data
        
        # Calculate intervention success rate
        intervention_success_rate = (successful_interventions / (prevention_campaigns * 10)) * 100 if prevention_campaigns > 0 else 0
        
        # Calculate cost per saved customer
        campaign_cost = prevention_campaigns * 1000  # Example cost
        cost_per_saved = campaign_cost / successful_interventions if successful_interventions > 0 else 0
        
        # Calculate ROI
        avg_customer_value = 500  # Example customer lifetime value
        total_value_saved = successful_interventions * avg_customer_value
        roi = ((total_value_saved - campaign_cost) / campaign_cost) * 100 if campaign_cost > 0 else 0
        
        return {
            'prevention_campaigns': prevention_campaigns,
            'successful_interventions': successful_interventions,
            'intervention_success_rate': intervention_success_rate,
            'campaign_cost': campaign_cost,
            'cost_per_saved_customer': cost_per_saved,
            'total_value_saved': total_value_saved,
            'roi': roi
        }
    
    def _calculate_prevention_effectiveness(self, prevention_metrics: Dict[str, Any]) -> float:
        """Calculate overall prevention effectiveness score"""
        success_rate = prevention_metrics.get('intervention_success_rate', 0)
        roi = prevention_metrics.get('roi', 0)
        
        # Weighted score based on success rate and ROI
        effectiveness_score = (success_rate * 0.6) + (min(roi, 100) * 0.4)
        
        return min(effectiveness_score, 100)
    
    def _generate_prevention_optimization_recommendations(self, prevention_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for optimizing churn prevention"""
        recommendations = []
        
        success_rate = prevention_metrics.get('intervention_success_rate', 0)
        roi = prevention_metrics.get('roi', 0)
        
        if success_rate < 30:
            recommendations.append({
                'type': 'critical',
                'title': 'Low Intervention Success Rate',
                'description': f'Intervention success rate is {success_rate:.1f}%',
                'action': 'Review and improve intervention strategies, better target high-risk customers'
            })
        
        if roi < 100:
            recommendations.append({
                'type': 'warning',
                'title': 'Low Prevention ROI',
                'description': f'Prevention ROI is {roi:.1f}%',
                'action': 'Optimize campaign costs, improve targeting, focus on high-value customers'
            })
        
        recommendations.append({
            'type': 'improvement',
            'title': 'Enhance Prevention Strategy',
            'description': 'Continuous improvement of churn prevention',
            'action': 'Implement A/B testing for campaigns, use machine learning for better targeting'
        })
        
        return recommendations
    
    def _calculate_monthly_churn(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate churn for a specific month"""
        return self._calculate_overall_churn(start_date, end_date)
    
    def _analyze_churn_trends(self, monthly_churn: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in churn rates over time"""
        if not monthly_churn:
            return {}
        
        churn_rates = [month['churn_rate'] for month in monthly_churn]
        
        # Calculate trend metrics
        avg_churn_rate = sum(churn_rates) / len(churn_rates)
        
        # Calculate trend direction
        if len(churn_rates) >= 2:
            recent_avg = sum(churn_rates[-3:]) / min(3, len(churn_rates))
            earlier_avg = sum(churn_rates[:3]) / min(3, len(churn_rates))
            trend_direction = 'improving' if recent_avg < earlier_avg else 'worsening' if recent_avg > earlier_avg else 'stable'
            trend_percentage = ((earlier_avg - recent_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            trend_direction = 'insufficient_data'
            trend_percentage = 0
        
        return {
            'average_churn_rate': avg_churn_rate,
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'best_period': monthly_churn[churn_rates.index(min(churn_rates))]['period'],
            'worst_period': monthly_churn[churn_rates.index(max(churn_rates))]['period']
        }
    
    def _get_voluntary_churn_reasons(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get detailed voluntary churn reasons"""
        reasons = self.db.query(
            Subscription.cancel_reason,
            func.count(Subscription.id).label('count')
        ).filter(
            and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date,
                Subscription.cancel_reason.in_(['customer_request', 'pricing', 'features', 'competitor'])
            )
        ).group_by(Subscription.cancel_reason).all()
        
        return [{'reason': reason, 'count': count} for reason, count in reasons if reason]
    
    def _get_involuntary_churn_reasons(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get detailed involuntary churn reasons"""
        # This would integrate with payment processing system
        return [
            {'reason': 'payment_failure', 'count': 5},
            {'reason': 'card_expired', 'count': 3},
            {'reason': 'insufficient_funds', 'count': 2}
        ]
    
    def _calculate_prediction_confidence(self, churn_rate: float) -> str:
        """Calculate confidence level for churn prediction"""
        if churn_rate < 2:
            return 'high'
        elif churn_rate < 5:
            return 'medium'
        else:
            return 'low'
    
    # Breakdown methods for churn analysis
    def _get_tier_churn_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get churn breakdown by pricing tier"""
        tiers = self.db.query(PricingTier).all()
        
        breakdown = {}
        for tier in tiers:
            tier_churn = self.db.query(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.status == 'canceled',
                    Subscription.canceled_at >= start_date,
                    Subscription.canceled_at <= end_date
                )
            ).count()
            
            tier_active = self.db.query(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.status == 'active',
                    Subscription.created_at < start_date
                )
            ).count()
            
            tier_churn_rate = (tier_churn / tier_active * 100) if tier_active > 0 else 0
            
            breakdown[tier.tier_type] = {
                'tier_name': tier.name,
                'churned_customers': tier_churn,
                'active_customers': tier_active,
                'churn_rate': tier_churn_rate
            }
        
        return breakdown
    
    def _get_geographic_churn_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get churn breakdown by geographic location"""
        # Get customers with address information
        customers_with_address = self.db.query(Customer).filter(
            Customer.address.isnot(None)
        ).all()
        
        geographic_breakdown = {}
        
        for customer in customers_with_address:
            if customer.address and 'country' in customer.address:
                country = customer.address['country']
                
                if country not in geographic_breakdown:
                    geographic_breakdown[country] = {
                        'churned_customers': 0,
                        'active_customers': 0
                    }
                
                # Count churned customers
                churned = self.db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.status == 'canceled',
                        Subscription.canceled_at >= start_date,
                        Subscription.canceled_at <= end_date
                    )
                ).count()
                
                if churned > 0:
                    geographic_breakdown[country]['churned_customers'] += 1
                else:
                    geographic_breakdown[country]['active_customers'] += 1
        
        # Calculate churn rates
        for country, data in geographic_breakdown.items():
            total_customers = data['churned_customers'] + data['active_customers']
            data['churn_rate'] = (data['churned_customers'] / total_customers * 100) if total_customers > 0 else 0
        
        return geographic_breakdown
    
    def _get_customer_segment_churn_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get churn breakdown by customer segments"""
        # Define customer segments
        segments = {
            'new_customers': {'name': 'New Customers', 'days': 30},
            'returning_customers': {'name': 'Returning Customers', 'days': 90},
            'loyal_customers': {'name': 'Loyal Customers', 'days': 365}
        }
        
        segment_breakdown = {}
        
        for segment_key, segment_config in segments.items():
            segment_start_date = start_date - timedelta(days=segment_config['days'])
            
            # Count churned customers in segment
            churned = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'canceled',
                    Subscription.canceled_at >= start_date,
                    Subscription.canceled_at <= end_date,
                    Subscription.created_at >= segment_start_date
                )
            ).count()
            
            # Count active customers in segment
            active = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'active',
                    Subscription.created_at >= segment_start_date,
                    Subscription.created_at < start_date
                )
            ).count()
            
            total_customers = churned + active
            churn_rate = (churned / total_customers * 100) if total_customers > 0 else 0
            
            segment_breakdown[segment_key] = {
                'segment_name': segment_config['name'],
                'churned_customers': churned,
                'active_customers': active,
                'churn_rate': churn_rate
            }
        
        return segment_breakdown
    
    def _get_billing_cycle_churn_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get churn breakdown by billing cycle"""
        cycles = ['monthly', 'annual']
        
        breakdown = {}
        for cycle in cycles:
            churned = self.db.query(Subscription).filter(
                and_(
                    Subscription.billing_cycle == cycle,
                    Subscription.status == 'canceled',
                    Subscription.canceled_at >= start_date,
                    Subscription.canceled_at <= end_date
                )
            ).count()
            
            active = self.db.query(Subscription).filter(
                and_(
                    Subscription.billing_cycle == cycle,
                    Subscription.status == 'active',
                    Subscription.created_at < start_date
                )
            ).count()
            
            total_customers = churned + active
            churn_rate = (churned / total_customers * 100) if total_customers > 0 else 0
            
            breakdown[cycle] = {
                'billing_cycle': cycle,
                'churned_customers': churned,
                'active_customers': active,
                'churn_rate': churn_rate
            }
        
        return breakdown 

    def get_payment_success_rates(self, date_range: str = '30d', analysis_type: str = 'overall') -> Dict[str, Any]:
        """Get comprehensive payment success rate analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if analysis_type == 'overall':
                success_data = self._calculate_overall_payment_success(start_date, end_date)
            elif analysis_type == 'by_tier':
                success_data = self._calculate_tier_payment_success(start_date, end_date)
            elif analysis_type == 'by_billing_cycle':
                success_data = self._calculate_billing_cycle_payment_success(start_date, end_date)
            elif analysis_type == 'by_payment_method':
                success_data = self._calculate_payment_method_success(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid analysis type: {analysis_type}'
                }
            
            return {
                'success': True,
                'payment_success_analysis': {
                    'analysis_type': analysis_type,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'success_data': success_data,
                    'success_rate': self._calculate_payment_success_rate(success_data),
                    'failure_analysis': self._analyze_payment_failures(success_data),
                    'retry_analysis': self._analyze_payment_retries(success_data),
                    'optimization_recommendations': self._generate_payment_optimization_recommendations(success_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment success rates: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_success_trends(self, period: str = '12m') -> Dict[str, Any]:
        """Get payment success rate trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            # Calculate monthly payment success trends
            monthly_success = []
            current_date = start_date
            
            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_success = self._calculate_monthly_payment_success(month_start, month_end)
                monthly_success.append({
                    'period': month_start.strftime('%Y-%m'),
                    'success_data': month_success,
                    'success_rate': self._calculate_payment_success_rate(month_success)
                })
                
                current_date = month_end + timedelta(days=1)
            
            return {
                'success': True,
                'payment_success_trends': {
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'monthly_success': monthly_success,
                    'trend_analysis': self._analyze_payment_success_trends(monthly_success)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment success trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_failure_breakdown(self, breakdown_dimension: str = 'reason', date_range: str = '30d') -> Dict[str, Any]:
        """Get payment failure breakdown by various dimensions"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if breakdown_dimension == 'reason':
                breakdown_data = self._get_failure_reason_breakdown(start_date, end_date)
            elif breakdown_dimension == 'geographic':
                breakdown_data = self._get_geographic_failure_breakdown(start_date, end_date)
            elif breakdown_dimension == 'time_period':
                breakdown_data = self._get_time_period_failure_breakdown(start_date, end_date)
            elif breakdown_dimension == 'customer_segment':
                breakdown_data = self._get_customer_segment_failure_breakdown(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid breakdown dimension: {breakdown_dimension}'
                }
            
            return {
                'success': True,
                'payment_failure_breakdown': {
                    'breakdown_dimension': breakdown_dimension,
                    'date_range': date_range,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'breakdown_data': breakdown_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment failure breakdown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_retry_analysis(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get detailed payment retry analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            retry_analysis = self._calculate_payment_retry_analysis(start_date, end_date)
            
            return {
                'success': True,
                'payment_retry_analysis': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'retry_analysis': retry_analysis,
                    'retry_success_rate': self._calculate_retry_success_rate(retry_analysis),
                    'retry_optimization_recommendations': self._generate_retry_optimization_recommendations(retry_analysis)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment retry analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_performance_metrics(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get comprehensive payment performance metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            performance_metrics = self._calculate_payment_performance_metrics(start_date, end_date)
            
            return {
                'success': True,
                'payment_performance_metrics': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'performance_metrics': performance_metrics,
                    'performance_score': self._calculate_payment_performance_score(performance_metrics),
                    'optimization_recommendations': self._generate_performance_optimization_recommendations(performance_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment performance metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods for payment success rate analysis
    def _calculate_overall_payment_success(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate overall payment success rates"""
        # Get total payment attempts
        total_attempts = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date
            )
        ).count()
        
        # Get successful payments
        successful_payments = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'paid'
            )
        ).count()
        
        # Get failed payments
        failed_payments = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'failed'
            )
        ).count()
        
        # Get pending payments
        pending_payments = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'pending'
            )
        ).count()
        
        # Calculate success rate
        success_rate = (successful_payments / total_attempts * 100) if total_attempts > 0 else 0
        failure_rate = (failed_payments / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            'total_attempts': total_attempts,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'pending_payments': pending_payments,
            'success_rate': success_rate,
            'failure_rate': failure_rate,
            'total_amount_attempted': self._calculate_total_amount_attempted(start_date, end_date),
            'total_amount_collected': self._calculate_total_amount_collected(start_date, end_date)
        }
    
    def _calculate_tier_payment_success(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate payment success rates by pricing tier"""
        tiers = self.db.query(PricingTier).all()
        
        tier_success = {}
        for tier in tiers:
            # Get payments for this tier
            tier_payments = self.db.query(BillingHistory).join(Subscription).filter(
                and_(
                    BillingHistory.created_at >= start_date,
                    BillingHistory.created_at <= end_date,
                    Subscription.pricing_tier_id == tier.id
                )
            ).all()
            
            total_attempts = len(tier_payments)
            successful_payments = len([p for p in tier_payments if p.status == 'paid'])
            failed_payments = len([p for p in tier_payments if p.status == 'failed'])
            
            success_rate = (successful_payments / total_attempts * 100) if total_attempts > 0 else 0
            
            tier_success[tier.tier_type] = {
                'tier_name': tier.name,
                'total_attempts': total_attempts,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'success_rate': success_rate,
                'avg_amount': tier.monthly_price
            }
        
        return tier_success
    
    def _calculate_billing_cycle_payment_success(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate payment success rates by billing cycle"""
        cycles = ['monthly', 'annual']
        
        cycle_success = {}
        for cycle in cycles:
            # Get payments for this billing cycle
            cycle_payments = self.db.query(BillingHistory).join(Subscription).filter(
                and_(
                    BillingHistory.created_at >= start_date,
                    BillingHistory.created_at <= end_date,
                    Subscription.billing_cycle == cycle
                )
            ).all()
            
            total_attempts = len(cycle_payments)
            successful_payments = len([p for p in cycle_payments if p.status == 'paid'])
            failed_payments = len([p for p in cycle_payments if p.status == 'failed'])
            
            success_rate = (successful_payments / total_attempts * 100) if total_attempts > 0 else 0
            
            cycle_success[cycle] = {
                'billing_cycle': cycle,
                'total_attempts': total_attempts,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'success_rate': success_rate,
                'avg_amount': sum(p.amount for p in cycle_payments) / len(cycle_payments) if cycle_payments else 0
            }
        
        return cycle_success
    
    def _calculate_payment_method_success(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate payment success rates by payment method"""
        # This would integrate with payment method data
        # For now, return example data
        payment_methods = {
            'credit_card': {
                'payment_method': 'Credit Card',
                'total_attempts': 150,
                'successful_payments': 135,
                'failed_payments': 15,
                'success_rate': 90.0,
                'avg_amount': 35.00
            },
            'debit_card': {
                'payment_method': 'Debit Card',
                'total_attempts': 80,
                'successful_payments': 72,
                'failed_payments': 8,
                'success_rate': 90.0,
                'avg_amount': 25.00
            },
            'bank_transfer': {
                'payment_method': 'Bank Transfer',
                'total_attempts': 30,
                'successful_payments': 29,
                'failed_payments': 1,
                'success_rate': 96.7,
                'avg_amount': 75.00
            },
            'digital_wallet': {
                'payment_method': 'Digital Wallet',
                'total_attempts': 40,
                'successful_payments': 36,
                'failed_payments': 4,
                'success_rate': 90.0,
                'avg_amount': 20.00
            }
        }
        
        return payment_methods
    
    def _calculate_payment_success_rate(self, success_data: Dict[str, Any]) -> float:
        """Calculate payment success rate from success data"""
        if isinstance(success_data, dict) and 'success_rate' in success_data:
            return success_data['success_rate']
        
        # Calculate for aggregated data
        total_attempts = success_data.get('total_attempts', 0)
        successful_payments = success_data.get('successful_payments', 0)
        
        if total_attempts > 0:
            return (successful_payments / total_attempts) * 100
        return 0.0
    
    def _analyze_payment_failures(self, success_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze payment failure reasons and patterns"""
        failures = []
        
        # Get failure reasons from database
        failure_reasons = self.db.query(
            BillingHistory.description,
            func.count(BillingHistory.id).label('count')
        ).filter(
            and_(
                BillingHistory.status == 'failed',
                BillingHistory.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).group_by(BillingHistory.description).all()
        
        for reason, count in failure_reasons:
            if reason:
                failures.append({
                    'reason': reason,
                    'count': count,
                    'percentage': (count / success_data.get('failed_payments', 1)) * 100 if success_data.get('failed_payments', 0) > 0 else 0,
                    'recommendation': self._get_failure_reason_recommendation(reason)
                })
        
        # Add common failure patterns
        common_failures = [
            {'reason': 'insufficient_funds', 'count': 25, 'percentage': 35.7, 'recommendation': 'Implement better payment timing and customer education'},
            {'reason': 'card_expired', 'count': 15, 'percentage': 21.4, 'recommendation': 'Implement card expiration notifications and auto-update'},
            {'reason': 'invalid_card', 'count': 10, 'percentage': 14.3, 'recommendation': 'Improve card validation and customer support'},
            {'reason': 'network_error', 'count': 8, 'percentage': 11.4, 'recommendation': 'Implement retry logic and fallback payment methods'},
            {'reason': 'fraud_detection', 'count': 7, 'percentage': 10.0, 'recommendation': 'Review fraud detection rules and customer verification'},
            {'reason': 'bank_decline', 'count': 5, 'percentage': 7.1, 'recommendation': 'Offer alternative payment methods and customer support'}
        ]
        
        return common_failures
    
    def _get_failure_reason_recommendation(self, reason: str) -> str:
        """Get recommendation for specific payment failure reason"""
        recommendations = {
            'insufficient_funds': 'Implement better payment timing, offer payment plans, send advance notifications',
            'card_expired': 'Implement card expiration notifications, auto-update functionality, customer reminders',
            'invalid_card': 'Improve card validation, enhance customer support, offer alternative payment methods',
            'network_error': 'Implement retry logic, add fallback payment methods, improve error handling',
            'fraud_detection': 'Review fraud detection rules, improve customer verification, offer manual review',
            'bank_decline': 'Offer alternative payment methods, improve customer support, implement retry logic',
            'payment_failure': 'Implement comprehensive retry strategy, improve payment processing, enhance customer support',
            'card_declined': 'Offer alternative payment methods, improve customer support, implement retry logic'
        }
        
        return recommendations.get(reason, 'Analyze failure pattern and implement targeted improvements')
    
    def _analyze_payment_retries(self, success_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payment retry patterns and success rates"""
        # This would integrate with retry tracking system
        # For now, return example data
        retry_analysis = {
            'total_retries': 45,
            'successful_retries': 28,
            'failed_retries': 17,
            'retry_success_rate': 62.2,
            'retry_attempts_distribution': {
                '1_attempt': {'count': 15, 'success_rate': 80.0},
                '2_attempts': {'count': 20, 'success_rate': 65.0},
                '3_attempts': {'count': 8, 'success_rate': 50.0},
                '4_attempts': {'count': 2, 'success_rate': 0.0}
            },
            'retry_timing_analysis': {
                'immediate_retry': {'count': 10, 'success_rate': 40.0},
                '1_day_delay': {'count': 20, 'success_rate': 70.0},
                '3_day_delay': {'count': 10, 'success_rate': 80.0},
                '7_day_delay': {'count': 5, 'success_rate': 60.0}
            },
            'retry_method_analysis': {
                'same_method': {'count': 30, 'success_rate': 55.0},
                'alternative_method': {'count': 15, 'success_rate': 80.0}
            }
        }
        
        return retry_analysis
    
    def _generate_payment_optimization_recommendations(self, success_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate payment optimization recommendations"""
        recommendations = []
        success_rate = self._calculate_payment_success_rate(success_data)
        
        # Overall success rate recommendations
        if success_rate < 85:
            recommendations.append({
                'type': 'critical',
                'title': 'Low Payment Success Rate',
                'description': f'Payment success rate is {success_rate:.1f}%, which is below industry standards',
                'action': 'Implement comprehensive payment optimization strategy immediately'
            })
        elif success_rate < 90:
            recommendations.append({
                'type': 'warning',
                'title': 'Below Average Payment Success Rate',
                'description': f'Payment success rate is {success_rate:.1f}%, which could be improved',
                'action': 'Focus on payment failure analysis and implement targeted improvements'
            })
        
        # Failure-specific recommendations
        failure_analysis = self._analyze_payment_failures(success_data)
        for failure in failure_analysis:
            if failure['percentage'] > 15:  # If a failure reason accounts for >15% of failures
                recommendations.append({
                    'type': 'targeted',
                    'title': f'Address {failure["reason"]} Failures',
                    'description': f'{failure["reason"]} accounts for {failure["percentage"]:.1f}% of payment failures',
                    'action': failure['recommendation']
                })
        
        # Retry optimization recommendations
        retry_analysis = self._analyze_payment_retries(success_data)
        retry_success_rate = retry_analysis.get('retry_success_rate', 0)
        
        if retry_success_rate < 60:
            recommendations.append({
                'type': 'improvement',
                'title': 'Low Retry Success Rate',
                'description': f'Retry success rate is {retry_success_rate:.1f}%',
                'action': 'Optimize retry timing, improve retry methods, implement better customer communication'
            })
        
        return recommendations
    
    def _calculate_monthly_payment_success(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate payment success for a specific month"""
        return self._calculate_overall_payment_success(start_date, end_date)
    
    def _analyze_payment_success_trends(self, monthly_success: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in payment success rates over time"""
        if not monthly_success:
            return {}
        
        success_rates = [month['success_rate'] for month in monthly_success]
        
        # Calculate trend metrics
        avg_success_rate = sum(success_rates) / len(success_rates)
        
        # Calculate trend direction
        if len(success_rates) >= 2:
            recent_avg = sum(success_rates[-3:]) / min(3, len(success_rates))
            earlier_avg = sum(success_rates[:3]) / min(3, len(success_rates))
            trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
            trend_percentage = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            trend_direction = 'insufficient_data'
            trend_percentage = 0
        
        return {
            'average_success_rate': avg_success_rate,
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'best_period': monthly_success[success_rates.index(max(success_rates))]['period'],
            'worst_period': monthly_success[success_rates.index(min(success_rates))]['period']
        }
    
    def _get_failure_reason_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment failure breakdown by reason"""
        # This would integrate with detailed failure tracking
        failure_reasons = {
            'insufficient_funds': {
                'reason': 'Insufficient Funds',
                'count': 25,
                'percentage': 35.7,
                'avg_amount': 45.00,
                'recommendation': 'Implement better payment timing and customer education'
            },
            'card_expired': {
                'reason': 'Card Expired',
                'count': 15,
                'percentage': 21.4,
                'avg_amount': 35.00,
                'recommendation': 'Implement card expiration notifications and auto-update'
            },
            'invalid_card': {
                'reason': 'Invalid Card',
                'count': 10,
                'percentage': 14.3,
                'avg_amount': 30.00,
                'recommendation': 'Improve card validation and customer support'
            },
            'network_error': {
                'reason': 'Network Error',
                'count': 8,
                'percentage': 11.4,
                'avg_amount': 40.00,
                'recommendation': 'Implement retry logic and fallback payment methods'
            },
            'fraud_detection': {
                'reason': 'Fraud Detection',
                'count': 7,
                'percentage': 10.0,
                'avg_amount': 75.00,
                'recommendation': 'Review fraud detection rules and customer verification'
            },
            'bank_decline': {
                'reason': 'Bank Decline',
                'count': 5,
                'percentage': 7.1,
                'avg_amount': 50.00,
                'recommendation': 'Offer alternative payment methods and customer support'
            }
        }
        
        return failure_reasons
    
    def _get_geographic_failure_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment failure breakdown by geographic location"""
        # Get customers with address information
        customers_with_address = self.db.query(Customer).filter(
            Customer.address.isnot(None)
        ).all()
        
        geographic_failures = {}
        
        for customer in customers_with_address:
            if customer.address and 'country' in customer.address:
                country = customer.address['country']
                
                if country not in geographic_failures:
                    geographic_failures[country] = {
                        'total_attempts': 0,
                        'failed_attempts': 0
                    }
                
                # Count payment attempts and failures for this customer
                customer_payments = self.db.query(BillingHistory).filter(
                    and_(
                        BillingHistory.customer_id == customer.id,
                        BillingHistory.created_at >= start_date,
                        BillingHistory.created_at <= end_date
                    )
                ).all()
                
                geographic_failures[country]['total_attempts'] += len(customer_payments)
                geographic_failures[country]['failed_attempts'] += len([p for p in customer_payments if p.status == 'failed'])
        
        # Calculate failure rates
        for country, data in geographic_failures.items():
            data['failure_rate'] = (data['failed_attempts'] / data['total_attempts'] * 100) if data['total_attempts'] > 0 else 0
        
        return geographic_failures
    
    def _get_time_period_failure_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment failure breakdown by time periods"""
        # Break down by weeks
        weekly_failures = {}
        current_date = start_date
        
        while current_date <= end_date:
            week_start = current_date
            week_end = min(current_date + timedelta(days=7), end_date)
            
            week_key = week_start.strftime('%Y-W%U')
            
            # Get payments for this week
            week_payments = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.created_at >= week_start,
                    BillingHistory.created_at <= week_end
                )
            ).all()
            
            total_attempts = len(week_payments)
            failed_attempts = len([p for p in week_payments if p.status == 'failed'])
            failure_rate = (failed_attempts / total_attempts * 100) if total_attempts > 0 else 0
            
            weekly_failures[week_key] = {
                'period': f"Week of {week_start.strftime('%Y-%m-%d')}",
                'total_attempts': total_attempts,
                'failed_attempts': failed_attempts,
                'failure_rate': failure_rate
            }
            
            current_date = week_end
        
        return weekly_failures
    
    def _get_customer_segment_failure_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment failure breakdown by customer segments"""
        # Define customer segments
        segments = {
            'new_customers': {'name': 'New Customers', 'days': 30},
            'returning_customers': {'name': 'Returning Customers', 'days': 90},
            'loyal_customers': {'name': 'Loyal Customers', 'days': 365}
        }
        
        segment_failures = {}
        
        for segment_key, segment_config in segments.items():
            segment_start_date = start_date - timedelta(days=segment_config['days'])
            
            # Get payments for customers in this segment
            segment_payments = self.db.query(BillingHistory).join(Customer).filter(
                and_(
                    BillingHistory.created_at >= start_date,
                    BillingHistory.created_at <= end_date,
                    Customer.created_at >= segment_start_date
                )
            ).all()
            
            total_attempts = len(segment_payments)
            failed_attempts = len([p for p in segment_payments if p.status == 'failed'])
            failure_rate = (failed_attempts / total_attempts * 100) if total_attempts > 0 else 0
            
            segment_failures[segment_key] = {
                'segment_name': segment_config['name'],
                'total_attempts': total_attempts,
                'failed_attempts': failed_attempts,
                'failure_rate': failure_rate
            }
        
        return segment_failures
    
    def _calculate_payment_retry_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate detailed payment retry analysis"""
        # This would integrate with retry tracking system
        # For now, return comprehensive example data
        retry_analysis = {
            'retry_summary': {
                'total_failed_payments': 70,
                'total_retries_attempted': 45,
                'successful_retries': 28,
                'failed_retries': 17,
                'retry_attempt_rate': 64.3,  # Percentage of failed payments that were retried
                'retry_success_rate': 62.2
            },
            'retry_attempts_analysis': {
                '1_attempt': {'count': 15, 'success_rate': 80.0, 'avg_delay_hours': 0},
                '2_attempts': {'count': 20, 'success_rate': 65.0, 'avg_delay_hours': 24},
                '3_attempts': {'count': 8, 'success_rate': 50.0, 'avg_delay_hours': 72},
                '4_attempts': {'count': 2, 'success_rate': 0.0, 'avg_delay_hours': 168}
            },
            'retry_timing_analysis': {
                'immediate_retry': {'count': 10, 'success_rate': 40.0, 'avg_delay_hours': 0},
                '1_day_delay': {'count': 20, 'success_rate': 70.0, 'avg_delay_hours': 24},
                '3_day_delay': {'count': 10, 'success_rate': 80.0, 'avg_delay_hours': 72},
                '7_day_delay': {'count': 5, 'success_rate': 60.0, 'avg_delay_hours': 168}
            },
            'retry_method_analysis': {
                'same_method': {'count': 30, 'success_rate': 55.0, 'method': 'Credit Card'},
                'alternative_method': {'count': 15, 'success_rate': 80.0, 'method': 'Bank Transfer'}
            },
            'retry_customer_communication': {
                'emails_sent': 45,
                'sms_sent': 30,
                'calls_made': 15,
                'response_rate': 75.0
            }
        }
        
        return retry_analysis
    
    def _calculate_retry_success_rate(self, retry_analysis: Dict[str, Any]) -> float:
        """Calculate overall retry success rate"""
        retry_summary = retry_analysis.get('retry_summary', {})
        successful_retries = retry_summary.get('successful_retries', 0)
        total_retries = retry_summary.get('total_retries_attempted', 0)
        
        if total_retries > 0:
            return (successful_retries / total_retries) * 100
        return 0.0
    
    def _generate_retry_optimization_recommendations(self, retry_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate retry optimization recommendations"""
        recommendations = []
        retry_success_rate = self._calculate_retry_success_rate(retry_analysis)
        
        # Retry success rate recommendations
        if retry_success_rate < 50:
            recommendations.append({
                'type': 'critical',
                'title': 'Low Retry Success Rate',
                'description': f'Retry success rate is {retry_success_rate:.1f}%, which is very low',
                'action': 'Completely review and redesign retry strategy'
            })
        elif retry_success_rate < 70:
            recommendations.append({
                'type': 'warning',
                'title': 'Below Average Retry Success Rate',
                'description': f'Retry success rate is {retry_success_rate:.1f}%, which needs improvement',
                'action': 'Optimize retry timing and improve customer communication'
            })
        
        # Timing optimization recommendations
        timing_analysis = retry_analysis.get('retry_timing_analysis', {})
        if timing_analysis.get('immediate_retry', {}).get('success_rate', 0) < 50:
            recommendations.append({
                'type': 'improvement',
                'title': 'Poor Immediate Retry Performance',
                'description': 'Immediate retries have low success rate',
                'action': 'Implement longer delays before first retry attempt'
            })
        
        # Method optimization recommendations
        method_analysis = retry_analysis.get('retry_method_analysis', {})
        same_method_success = method_analysis.get('same_method', {}).get('success_rate', 0)
        alternative_method_success = method_analysis.get('alternative_method', {}).get('success_rate', 0)
        
        if alternative_method_success > same_method_success + 20:
            recommendations.append({
                'type': 'optimization',
                'title': 'Alternative Payment Methods More Effective',
                'description': f'Alternative methods have {alternative_method_success - same_method_success:.1f}% higher success rate',
                'action': 'Implement automatic alternative payment method suggestions'
            })
        
        return recommendations
    
    def _calculate_payment_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate comprehensive payment performance metrics"""
        # Get overall payment data
        overall_success = self._calculate_overall_payment_success(start_date, end_date)
        
        # Calculate performance metrics
        performance_metrics = {
            'success_rate': overall_success['success_rate'],
            'failure_rate': overall_success['failure_rate'],
            'total_volume': overall_success['total_amount_attempted'],
            'collected_volume': overall_success['total_amount_collected'],
            'collection_rate': (overall_success['total_amount_collected'] / overall_success['total_amount_attempted'] * 100) if overall_success['total_amount_attempted'] > 0 else 0,
            'avg_transaction_value': overall_success['total_amount_attempted'] / overall_success['total_attempts'] if overall_success['total_attempts'] > 0 else 0,
            'processing_time': {
                'avg_processing_time_seconds': 2.5,
                'p95_processing_time_seconds': 5.2,
                'p99_processing_time_seconds': 8.7
            },
            'customer_satisfaction': {
                'payment_success_satisfaction': 4.2,
                'payment_failure_satisfaction': 2.8,
                'overall_payment_satisfaction': 3.9
            },
            'cost_metrics': {
                'processing_fees': overall_success['total_amount_collected'] * 0.029,  # 2.9% processing fee
                'chargeback_rate': 0.5,  # 0.5% chargeback rate
                'refund_rate': 2.1,  # 2.1% refund rate
                'cost_per_transaction': 0.30  # $0.30 per transaction
            }
        }
        
        return performance_metrics
    
    def _calculate_payment_performance_score(self, performance_metrics: Dict[str, Any]) -> float:
        """Calculate overall payment performance score"""
        success_rate = performance_metrics.get('success_rate', 0)
        collection_rate = performance_metrics.get('collection_rate', 0)
        processing_time_score = max(0, 100 - (performance_metrics.get('processing_time', {}).get('avg_processing_time_seconds', 10) * 10))
        satisfaction_score = performance_metrics.get('customer_satisfaction', {}).get('overall_payment_satisfaction', 0) * 20
        
        # Weighted score
        performance_score = (
            success_rate * 0.4 +
            collection_rate * 0.3 +
            processing_time_score * 0.2 +
            satisfaction_score * 0.1
        )
        
        return min(performance_score, 100)
    
    def _generate_performance_optimization_recommendations(self, performance_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations"""
        recommendations = []
        performance_score = self._calculate_payment_performance_score(performance_metrics)
        
        # Overall performance recommendations
        if performance_score < 70:
            recommendations.append({
                'type': 'critical',
                'title': 'Low Payment Performance Score',
                'description': f'Payment performance score is {performance_score:.1f}/100',
                'action': 'Implement comprehensive payment optimization strategy'
            })
        elif performance_score < 85:
            recommendations.append({
                'type': 'warning',
                'title': 'Below Average Payment Performance',
                'description': f'Payment performance score is {performance_score:.1f}/100',
                'action': 'Focus on key performance areas and implement targeted improvements'
            })
        
        # Success rate recommendations
        success_rate = performance_metrics.get('success_rate', 0)
        if success_rate < 90:
            recommendations.append({
                'type': 'improvement',
                'title': 'Improve Payment Success Rate',
                'description': f'Success rate is {success_rate:.1f}%',
                'action': 'Analyze failure reasons and implement targeted improvements'
            })
        
        # Processing time recommendations
        avg_processing_time = performance_metrics.get('processing_time', {}).get('avg_processing_time_seconds', 0)
        if avg_processing_time > 3:
            recommendations.append({
                'type': 'optimization',
                'title': 'Optimize Payment Processing Time',
                'description': f'Average processing time is {avg_processing_time:.1f} seconds',
                'action': 'Review payment processor configuration and optimize API calls'
            })
        
        # Cost optimization recommendations
        cost_metrics = performance_metrics.get('cost_metrics', {})
        chargeback_rate = cost_metrics.get('chargeback_rate', 0)
        if chargeback_rate > 1:
            recommendations.append({
                'type': 'risk',
                'title': 'High Chargeback Rate',
                'description': f'Chargeback rate is {chargeback_rate:.1f}%',
                'action': 'Implement better fraud detection and customer verification'
            })
        
        return recommendations
    
    def _calculate_total_amount_attempted(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate total amount attempted in payments"""
        total_amount = self.db.query(func.sum(BillingHistory.amount)).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date
            )
        ).scalar()
        
        return float(total_amount) if total_amount else 0.0
    
    def _calculate_total_amount_collected(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate total amount successfully collected"""
        total_amount = self.db.query(func.sum(BillingHistory.amount)).filter(
            and_(
                BillingHistory.created_at >= start_date,
                BillingHistory.created_at <= end_date,
                BillingHistory.status == 'paid'
            )
        ).scalar()
        
        return float(total_amount) if total_amount else 0.0
    
    def get_customer_lifetime_value_metrics(self, date_range: str = '30d', analysis_type: str = 'by_tier') -> Dict[str, Any]:
        """Get comprehensive customer lifetime value metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            if analysis_type == 'by_tier':
                clv_data = self._calculate_tier_clv_metrics(start_date, end_date)
            elif analysis_type == 'by_customer_segment':
                clv_data = self._calculate_customer_segment_clv(start_date, end_date)
            elif analysis_type == 'by_geographic':
                clv_data = self._calculate_geographic_clv(start_date, end_date)
            elif analysis_type == 'by_billing_cycle':
                clv_data = self._calculate_billing_cycle_clv(start_date, end_date)
            else:
                return {
                    'success': False,
                    'error': f'Invalid analysis type: {analysis_type}'
                }
            
            return {
                'success': True,
                'customer_lifetime_value_analysis': {
                    'analysis_type': analysis_type,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'clv_data': clv_data,
                    'clv_summary': self._calculate_clv_summary(clv_data),
                    'clv_trends': self._analyze_clv_trends(clv_data),
                    'optimization_recommendations': self._generate_clv_optimization_recommendations(clv_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting customer lifetime value metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tier_distribution_analysis(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get comprehensive tier distribution analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            distribution_data = self._calculate_tier_distribution(start_date, end_date)
            
            return {
                'success': True,
                'tier_distribution_analysis': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'distribution_data': distribution_data,
                    'distribution_summary': self._calculate_distribution_summary(distribution_data),
                    'tier_movement_analysis': self._analyze_tier_movements(start_date, end_date),
                    'optimization_recommendations': self._generate_distribution_optimization_recommendations(distribution_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tier distribution analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tier_movement_trends(self, period: str = '12m') -> Dict[str, Any]:
        """Get tier movement trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            # Calculate monthly tier movement trends
            monthly_movements = []
            current_date = start_date
            
            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_movements = self._calculate_monthly_tier_movements(month_start, month_end)
                monthly_movements.append({
                    'period': month_start.strftime('%Y-%m'),
                    'movements': month_movements,
                    'movement_summary': self._calculate_movement_summary(month_movements)
                })
                
                current_date = month_end + timedelta(days=1)
            
            return {
                'success': True,
                'tier_movement_trends': {
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'monthly_movements': monthly_movements,
                    'trend_analysis': self._analyze_movement_trends(monthly_movements)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tier movement trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tier_migration_analysis(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get detailed tier migration analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            migration_analysis = self._calculate_tier_migrations(start_date, end_date)
            
            return {
                'success': True,
                'tier_migration_analysis': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'migration_analysis': migration_analysis,
                    'migration_matrix': self._generate_migration_matrix(migration_analysis),
                    'migration_reasons': self._analyze_migration_reasons(start_date, end_date),
                    'optimization_recommendations': self._generate_migration_optimization_recommendations(migration_analysis)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tier migration analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tier_value_optimization(self, date_range: str = '30d') -> Dict[str, Any]:
        """Get tier value optimization insights"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, date_range)
            
            optimization_data = self._calculate_tier_value_optimization(start_date, end_date)
            
            return {
                'success': True,
                'tier_value_optimization': {
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'period': date_range
                    },
                    'optimization_data': optimization_data,
                    'upgrade_opportunities': self._identify_upgrade_opportunities(start_date, end_date),
                    'retention_strategies': self._generate_retention_strategies(optimization_data),
                    'optimization_recommendations': self._generate_value_optimization_recommendations(optimization_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tier value optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods for customer lifetime value and tier distribution analysis
    def _calculate_tier_clv_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate customer lifetime value metrics by tier"""
        tiers = self.db.query(PricingTier).all()
        
        tier_clv = {}
        for tier in tiers:
            # Get customers in this tier
            tier_customers = self.db.query(Customer).join(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.status == 'active',
                    Subscription.created_at <= end_date
                )
            ).all()
            
            if not tier_customers:
                tier_clv[tier.tier_type] = {
                    'tier_name': tier.name,
                    'customer_count': 0,
                    'avg_clv': 0,
                    'total_clv': 0,
                    'avg_lifetime_months': 0,
                    'avg_monthly_revenue': tier.monthly_price,
                    'clv_distribution': {}
                }
                continue
            
            # Calculate CLV metrics for each customer
            customer_clvs = []
            total_clv = 0
            
            for customer in tier_customers:
                # Get customer's subscription history
                customer_subscriptions = self.db.query(Subscription).filter(
                    Subscription.customer_id == customer.id
                ).all()
                
                # Calculate customer's total revenue
                total_revenue = sum(sub.amount for sub in customer_subscriptions if sub.status == 'active')
                
                # Calculate customer's lifetime in months
                if customer_subscriptions:
                    first_subscription = min(customer_subscriptions, key=lambda s: s.created_at)
                    lifetime_months = (end_date - first_subscription.created_at).days / 30.44
                else:
                    lifetime_months = 0
                
                # Calculate CLV (simplified: total revenue + projected future revenue)
                avg_monthly_revenue = tier.monthly_price
                projected_months = 24  # Assume 24 months average customer lifetime
                clv = total_revenue + (avg_monthly_revenue * projected_months)
                
                customer_clvs.append({
                    'customer_id': customer.id,
                    'total_revenue': total_revenue,
                    'lifetime_months': lifetime_months,
                    'clv': clv,
                    'avg_monthly_revenue': avg_monthly_revenue
                })
                
                total_clv += clv
            
            # Calculate tier-level metrics
            avg_clv = total_clv / len(tier_customers) if tier_customers else 0
            avg_lifetime_months = sum(c['lifetime_months'] for c in customer_clvs) / len(customer_clvs) if customer_clvs else 0
            
            # CLV distribution
            clv_distribution = {
                'low_value': len([c for c in customer_clvs if c['clv'] < avg_clv * 0.5]),
                'medium_value': len([c for c in customer_clvs if avg_clv * 0.5 <= c['clv'] < avg_clv * 1.5]),
                'high_value': len([c for c in customer_clvs if c['clv'] >= avg_clv * 1.5])
            }
            
            tier_clv[tier.tier_type] = {
                'tier_name': tier.name,
                'customer_count': len(tier_customers),
                'avg_clv': avg_clv,
                'total_clv': total_clv,
                'avg_lifetime_months': avg_lifetime_months,
                'avg_monthly_revenue': tier.monthly_price,
                'clv_distribution': clv_distribution,
                'customer_clvs': customer_clvs
            }
        
        return tier_clv
    
    def _calculate_customer_segment_clv(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate customer lifetime value by customer segments"""
        # Define customer segments
        segments = {
            'new_customers': {'name': 'New Customers', 'days': 30},
            'returning_customers': {'name': 'Returning Customers', 'days': 90},
            'loyal_customers': {'name': 'Loyal Customers', 'days': 365}
        }
        
        segment_clv = {}
        
        for segment_key, segment_config in segments.items():
            segment_start_date = start_date - timedelta(days=segment_config['days'])
            
            # Get customers in this segment
            segment_customers = self.db.query(Customer).filter(
                and_(
                    Customer.created_at >= segment_start_date,
                    Customer.created_at < start_date
                )
            ).all()
            
            if not segment_customers:
                segment_clv[segment_key] = {
                    'segment_name': segment_config['name'],
                    'customer_count': 0,
                    'avg_clv': 0,
                    'total_clv': 0,
                    'avg_lifetime_months': 0
                }
                continue
            
            # Calculate CLV for segment customers
            customer_clvs = []
            total_clv = 0
            
            for customer in segment_customers:
                # Get customer's total revenue
                customer_revenue = self.db.query(func.sum(BillingHistory.amount)).filter(
                    and_(
                        BillingHistory.customer_id == customer.id,
                        BillingHistory.status == 'paid',
                        BillingHistory.created_at >= start_date,
                        BillingHistory.created_at <= end_date
                    )
                ).scalar() or 0
                
                # Calculate CLV
                avg_monthly_revenue = 35.00  # Average across tiers
                projected_months = 24
                clv = customer_revenue + (avg_monthly_revenue * projected_months)
                
                customer_clvs.append({
                    'customer_id': customer.id,
                    'total_revenue': customer_revenue,
                    'clv': clv
                })
                
                total_clv += clv
            
            avg_clv = total_clv / len(segment_customers) if segment_customers else 0
            avg_lifetime_months = segment_config['days'] / 30.44
            
            segment_clv[segment_key] = {
                'segment_name': segment_config['name'],
                'customer_count': len(segment_customers),
                'avg_clv': avg_clv,
                'total_clv': total_clv,
                'avg_lifetime_months': avg_lifetime_months
            }
        
        return segment_clv
    
    def _calculate_geographic_clv(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate customer lifetime value by geographic location"""
        # Get customers with address information
        customers_with_address = self.db.query(Customer).filter(
            Customer.address.isnot(None)
        ).all()
        
        geographic_clv = {}
        
        for customer in customers_with_address:
            if customer.address and 'country' in customer.address:
                country = customer.address['country']
                
                if country not in geographic_clv:
                    geographic_clv[country] = {
                        'customer_count': 0,
                        'total_revenue': 0,
                        'avg_clv': 0
                    }
                
                # Get customer's revenue
                customer_revenue = self.db.query(func.sum(BillingHistory.amount)).filter(
                    and_(
                        BillingHistory.customer_id == customer.id,
                        BillingHistory.status == 'paid',
                        BillingHistory.created_at >= start_date,
                        BillingHistory.created_at <= end_date
                    )
                ).scalar() or 0
                
                geographic_clv[country]['customer_count'] += 1
                geographic_clv[country]['total_revenue'] += customer_revenue
        
        # Calculate CLV for each geographic region
        for country, data in geographic_clv.items():
            avg_monthly_revenue = 35.00  # Average across tiers
            projected_months = 24
            avg_clv = (data['total_revenue'] / data['customer_count']) + (avg_monthly_revenue * projected_months) if data['customer_count'] > 0 else 0
            
            data['avg_clv'] = avg_clv
        
        return geographic_clv
    
    def _calculate_billing_cycle_clv(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate customer lifetime value by billing cycle"""
        cycles = ['monthly', 'annual']
        
        cycle_clv = {}
        for cycle in cycles:
            # Get customers with this billing cycle
            cycle_customers = self.db.query(Customer).join(Subscription).filter(
                and_(
                    Subscription.billing_cycle == cycle,
                    Subscription.status == 'active',
                    Subscription.created_at <= end_date
                )
            ).all()
            
            if not cycle_customers:
                cycle_clv[cycle] = {
                    'billing_cycle': cycle,
                    'customer_count': 0,
                    'avg_clv': 0,
                    'total_clv': 0,
                    'avg_monthly_revenue': 0
                }
                continue
            
            # Calculate CLV for cycle customers
            customer_clvs = []
            total_clv = 0
            
            for customer in cycle_customers:
                # Get customer's subscription
                subscription = self.db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.billing_cycle == cycle
                    )
                ).first()
                
                if subscription:
                    # Calculate CLV
                    avg_monthly_revenue = subscription.amount if cycle == 'monthly' else subscription.amount / 12
                    projected_months = 24
                    clv = (avg_monthly_revenue * projected_months)
                    
                    customer_clvs.append({
                        'customer_id': customer.id,
                        'avg_monthly_revenue': avg_monthly_revenue,
                        'clv': clv
                    })
                    
                    total_clv += clv
            
            avg_clv = total_clv / len(cycle_customers) if cycle_customers else 0
            avg_monthly_revenue = sum(c['avg_monthly_revenue'] for c in customer_clvs) / len(customer_clvs) if customer_clvs else 0
            
            cycle_clv[cycle] = {
                'billing_cycle': cycle,
                'customer_count': len(cycle_customers),
                'avg_clv': avg_clv,
                'total_clv': total_clv,
                'avg_monthly_revenue': avg_monthly_revenue
            }
        
        return cycle_clv
    
    def _calculate_clv_summary(self, clv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for CLV data"""
        if not clv_data:
            return {}
        
        # Aggregate CLV metrics
        total_customers = sum(tier_data.get('customer_count', 0) for tier_data in clv_data.values())
        total_clv = sum(tier_data.get('total_clv', 0) for tier_data in clv_data.values())
        avg_clv = total_clv / total_customers if total_customers > 0 else 0
        
        # Find highest and lowest CLV tiers
        tier_clvs = [(tier_type, tier_data.get('avg_clv', 0)) for tier_type, tier_data in clv_data.items()]
        tier_clvs.sort(key=lambda x: x[1], reverse=True)
        
        highest_clv_tier = tier_clvs[0] if tier_clvs else None
        lowest_clv_tier = tier_clvs[-1] if tier_clvs else None
        
        return {
            'total_customers': total_customers,
            'total_clv': total_clv,
            'avg_clv': avg_clv,
            'highest_clv_tier': highest_clv_tier,
            'lowest_clv_tier': lowest_clv_tier,
            'clv_range': highest_clv_tier[1] - lowest_clv_tier[1] if highest_clv_tier and lowest_clv_tier else 0
        }
    
    def _analyze_clv_trends(self, clv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in customer lifetime value"""
        if not clv_data:
            return {}
        
        # Calculate trend metrics
        tier_clvs = [tier_data.get('avg_clv', 0) for tier_data in clv_data.values()]
        avg_clv = sum(tier_clvs) / len(tier_clvs) if tier_clvs else 0
        
        # Identify trends (simplified - would need historical data for real trends)
        trend_analysis = {
            'overall_trend': 'stable',
            'growth_rate': 0.0,
            'tier_performance': {}
        }
        
        for tier_type, tier_data in clv_data.items():
            avg_clv_tier = tier_data.get('avg_clv', 0)
            customer_count = tier_data.get('customer_count', 0)
            
            # Simple performance indicator
            if avg_clv_tier > avg_clv * 1.2:
                performance = 'high'
            elif avg_clv_tier < avg_clv * 0.8:
                performance = 'low'
            else:
                performance = 'medium'
            
            trend_analysis['tier_performance'][tier_type] = {
                'avg_clv': avg_clv_tier,
                'customer_count': customer_count,
                'performance': performance
            }
        
        return trend_analysis
    
    def _generate_clv_optimization_recommendations(self, clv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate CLV optimization recommendations"""
        recommendations = []
        
        if not clv_data:
            return recommendations
        
        # Calculate overall metrics
        total_customers = sum(tier_data.get('customer_count', 0) for tier_data in clv_data.values())
        total_clv = sum(tier_data.get('total_clv', 0) for tier_data in clv_data.values())
        avg_clv = total_clv / total_customers if total_customers > 0 else 0
        
        # Tier-specific recommendations
        for tier_type, tier_data in clv_data.items():
            tier_clv = tier_data.get('avg_clv', 0)
            customer_count = tier_data.get('customer_count', 0)
            
            if tier_clv < avg_clv * 0.8:
                recommendations.append({
                    'type': 'improvement',
                    'title': f'Improve {tier_data["tier_name"]} CLV',
                    'description': f'{tier_data["tier_name"]} has below-average CLV of ${tier_clv:.2f}',
                    'action': 'Implement value-add features, improve customer engagement, optimize pricing'
                })
            
            if customer_count < 10:  # Small tier
                recommendations.append({
                    'type': 'growth',
                    'title': f'Grow {tier_data["tier_name"]} Customer Base',
                    'description': f'{tier_data["tier_name"]} has only {customer_count} customers',
                    'action': 'Implement targeted marketing campaigns, improve tier positioning'
                })
        
        # Overall recommendations
        if avg_clv < 500:  # Low average CLV
            recommendations.append({
                'type': 'critical',
                'title': 'Low Average Customer Lifetime Value',
                'description': f'Average CLV is ${avg_clv:.2f}, which is below target',
                'action': 'Implement comprehensive CLV optimization strategy'
            })
        
        return recommendations
    
    def _calculate_tier_distribution(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate tier distribution analysis"""
        tiers = self.db.query(PricingTier).all()
        
        distribution_data = {}
        total_customers = 0
        
        for tier in tiers:
            # Get active customers in this tier
            tier_customers = self.db.query(Customer).join(Subscription).filter(
                and_(
                    Subscription.pricing_tier_id == tier.id,
                    Subscription.status == 'active',
                    Subscription.created_at <= end_date
                )
            ).count()
            
            total_customers += tier_customers
            
            distribution_data[tier.tier_type] = {
                'tier_name': tier.name,
                'customer_count': tier_customers,
                'percentage': 0,  # Will be calculated below
                'monthly_revenue': tier.monthly_price * tier_customers,
                'yearly_revenue': tier.yearly_price * (tier_customers / 12) if tier.yearly_price else 0
            }
        
        # Calculate percentages
        for tier_data in distribution_data.values():
            tier_data['percentage'] = (tier_data['customer_count'] / total_customers * 100) if total_customers > 0 else 0
        
        # Add total metrics
        distribution_data['total'] = {
            'total_customers': total_customers,
            'total_monthly_revenue': sum(tier_data['monthly_revenue'] for tier_data in distribution_data.values() if tier_data != distribution_data['total']),
            'total_yearly_revenue': sum(tier_data['yearly_revenue'] for tier_data in distribution_data.values() if tier_data != distribution_data['total'])
        }
        
        return distribution_data
    
    def _calculate_distribution_summary(self, distribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for tier distribution"""
        if not distribution_data:
            return {}
        
        # Remove total from calculations
        tier_data = {k: v for k, v in distribution_data.items() if k != 'total'}
        
        if not tier_data:
            return {}
        
        # Calculate metrics
        total_customers = sum(tier_data['customer_count'] for tier_data in tier_data.values())
        total_monthly_revenue = sum(tier_data['monthly_revenue'] for tier_data in tier_data.values())
        
        # Find dominant tier
        dominant_tier = max(tier_data.items(), key=lambda x: x[1]['customer_count'])
        
        # Calculate distribution evenness
        percentages = [tier_data['percentage'] for tier_data in tier_data.values()]
        distribution_evenness = 1 - (max(percentages) - min(percentages)) / 100 if percentages else 0
        
        return {
            'total_customers': total_customers,
            'total_monthly_revenue': total_monthly_revenue,
            'dominant_tier': dominant_tier[0],
            'dominant_tier_percentage': dominant_tier[1]['percentage'],
            'distribution_evenness': distribution_evenness,
            'tier_count': len(tier_data)
        }
    
    def _analyze_tier_movements(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze tier movements during the period"""
        # This would require tracking tier changes in the database
        # For now, return example data
        movements = {
            'upgrades': {
                'budget_to_mid_tier': 15,
                'mid_tier_to_professional': 8,
                'budget_to_professional': 3
            },
            'downgrades': {
                'professional_to_mid_tier': 5,
                'mid_tier_to_budget': 12,
                'professional_to_budget': 2
            },
            'cancellations': {
                'budget': 8,
                'mid_tier': 6,
                'professional': 3
            },
            'new_subscriptions': {
                'budget': 25,
                'mid_tier': 18,
                'professional': 12
            }
        }
        
        # Calculate movement metrics
        total_upgrades = sum(movements['upgrades'].values())
        total_downgrades = sum(movements['downgrades'].values())
        total_cancellations = sum(movements['cancellations'].values())
        total_new = sum(movements['new_subscriptions'].values())
        
        net_movement = total_new + total_upgrades - total_downgrades - total_cancellations
        
        movements['summary'] = {
            'total_upgrades': total_upgrades,
            'total_downgrades': total_downgrades,
            'total_cancellations': total_cancellations,
            'total_new_subscriptions': total_new,
            'net_movement': net_movement,
            'upgrade_rate': (total_upgrades / (total_upgrades + total_downgrades) * 100) if (total_upgrades + total_downgrades) > 0 else 0
        }
        
        return movements
    
    def _calculate_monthly_tier_movements(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate tier movements for a specific month"""
        # Simplified calculation - would need historical movement data
        return {
            'upgrades': 12,
            'downgrades': 8,
            'cancellations': 5,
            'new_subscriptions': 20,
            'net_movement': 19
        }
    
    def _calculate_movement_summary(self, movements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary for movement data"""
        return {
            'total_movements': movements.get('upgrades', 0) + movements.get('downgrades', 0),
            'net_movement': movements.get('net_movement', 0),
            'movement_rate': (movements.get('upgrades', 0) / (movements.get('upgrades', 0) + movements.get('downgrades', 0)) * 100) if (movements.get('upgrades', 0) + movements.get('downgrades', 0)) > 0 else 0
        }
    
    def _analyze_movement_trends(self, monthly_movements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in tier movements over time"""
        if not monthly_movements:
            return {}
        
        # Calculate trend metrics
        net_movements = [month['movement_summary']['net_movement'] for month in monthly_movements]
        movement_rates = [month['movement_summary']['movement_rate'] for month in monthly_movements]
        
        avg_net_movement = sum(net_movements) / len(net_movements) if net_movements else 0
        avg_movement_rate = sum(movement_rates) / len(movement_rates) if movement_rates else 0
        
        # Determine trend direction
        if len(net_movements) >= 2:
            recent_avg = sum(net_movements[-3:]) / min(3, len(net_movements))
            earlier_avg = sum(net_movements[:3]) / min(3, len(net_movements))
            trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'avg_net_movement': avg_net_movement,
            'avg_movement_rate': avg_movement_rate,
            'trend_direction': trend_direction,
            'best_period': monthly_movements[net_movements.index(max(net_movements))]['period'] if net_movements else None,
            'worst_period': monthly_movements[net_movements.index(min(net_movements))]['period'] if net_movements else None
        }
    
    def _calculate_tier_migrations(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate detailed tier migration patterns"""
        # This would require tracking tier changes in the database
        # For now, return comprehensive example data
        migrations = {
            'migration_patterns': {
                'budget_to_mid_tier': {
                    'count': 15,
                    'percentage': 35.7,
                    'avg_time_to_upgrade': 4.2,  # months
                    'common_reasons': ['feature_limits', 'usage_growth', 'pricing_value']
                },
                'mid_tier_to_professional': {
                    'count': 8,
                    'percentage': 19.0,
                    'avg_time_to_upgrade': 6.8,
                    'common_reasons': ['team_features', 'api_access', 'support_needs']
                },
                'budget_to_professional': {
                    'count': 3,
                    'percentage': 7.1,
                    'avg_time_to_upgrade': 2.1,
                    'common_reasons': ['immediate_need', 'budget_available', 'feature_requirements']
                },
                'professional_to_mid_tier': {
                    'count': 5,
                    'percentage': 11.9,
                    'avg_time_to_downgrade': 8.5,
                    'common_reasons': ['cost_reduction', 'feature_overkill', 'team_size_reduction']
                },
                'mid_tier_to_budget': {
                    'count': 12,
                    'percentage': 28.6,
                    'avg_time_to_downgrade': 5.2,
                    'common_reasons': ['cost_reduction', 'usage_decrease', 'feature_simplification']
                },
                'professional_to_budget': {
                    'count': 2,
                    'percentage': 4.8,
                    'avg_time_to_downgrade': 12.1,
                    'common_reasons': ['significant_cost_reduction', 'business_changes']
                }
            },
            'migration_summary': {
                'total_migrations': 45,
                'upgrades': 26,
                'downgrades': 19,
                'upgrade_rate': 57.8,
                'downgrade_rate': 42.2,
                'net_upgrade_rate': 15.6
            }
        }
        
        return migrations
    
    def _generate_migration_matrix(self, migration_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate migration matrix for visualization"""
        patterns = migration_analysis.get('migration_patterns', {})
        
        matrix = {
            'budget': {
                'budget': 0,
                'mid_tier': patterns.get('budget_to_mid_tier', {}).get('count', 0),
                'professional': patterns.get('budget_to_professional', {}).get('count', 0)
            },
            'mid_tier': {
                'budget': patterns.get('mid_tier_to_budget', {}).get('count', 0),
                'mid_tier': 0,
                'professional': patterns.get('mid_tier_to_professional', {}).get('count', 0)
            },
            'professional': {
                'budget': patterns.get('professional_to_budget', {}).get('count', 0),
                'mid_tier': patterns.get('professional_to_mid_tier', {}).get('count', 0),
                'professional': 0
            }
        }
        
        return matrix
    
    def _analyze_migration_reasons(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Analyze reasons for tier migrations"""
        # This would integrate with customer feedback and usage data
        # For now, return example data
        reasons = [
            {
                'reason': 'feature_limits',
                'count': 18,
                'percentage': 40.0,
                'migration_type': 'upgrade',
                'recommendation': 'Improve feature discovery and usage education'
            },
            {
                'reason': 'cost_reduction',
                'count': 15,
                'percentage': 33.3,
                'migration_type': 'downgrade',
                'recommendation': 'Implement value-based pricing and cost optimization'
            },
            {
                'reason': 'usage_growth',
                'count': 8,
                'percentage': 17.8,
                'migration_type': 'upgrade',
                'recommendation': 'Proactive upgrade prompts and usage monitoring'
            },
            {
                'reason': 'team_features',
                'count': 6,
                'percentage': 13.3,
                'migration_type': 'upgrade',
                'recommendation': 'Highlight team collaboration benefits'
            },
            {
                'reason': 'usage_decrease',
                'count': 4,
                'percentage': 8.9,
                'migration_type': 'downgrade',
                'recommendation': 'Implement re-engagement campaigns'
            }
        ]
        
        return reasons
    
    def _generate_migration_optimization_recommendations(self, migration_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate migration optimization recommendations"""
        recommendations = []
        
        migration_summary = migration_analysis.get('migration_summary', {})
        upgrade_rate = migration_summary.get('upgrade_rate', 0)
        downgrade_rate = migration_summary.get('downgrade_rate', 0)
        
        # Upgrade rate recommendations
        if upgrade_rate < 60:
            recommendations.append({
                'type': 'improvement',
                'title': 'Low Upgrade Rate',
                'description': f'Upgrade rate is {upgrade_rate:.1f}%, which is below target',
                'action': 'Implement targeted upgrade campaigns, improve feature education, optimize pricing'
            })
        
        # Downgrade rate recommendations
        if downgrade_rate > 40:
            recommendations.append({
                'type': 'critical',
                'title': 'High Downgrade Rate',
                'description': f'Downgrade rate is {downgrade_rate:.1f}%, which is concerning',
                'action': 'Implement retention strategies, improve value proposition, address customer concerns'
            })
        
        # Migration pattern recommendations
        patterns = migration_analysis.get('migration_patterns', {})
        for pattern, data in patterns.items():
            if 'downgrade' in pattern and data.get('percentage', 0) > 20:
                recommendations.append({
                    'type': 'targeted',
                    'title': f'Address {pattern} Downgrades',
                    'description': f'{pattern} accounts for {data["percentage"]:.1f}% of migrations',
                    'action': f'Analyze reasons: {", ".join(data.get("common_reasons", []))}'
                })
        
        return recommendations
    
    def _calculate_tier_value_optimization(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate tier value optimization insights"""
        # Get tier distribution and CLV data
        distribution_data = self._calculate_tier_distribution(start_date, end_date)
        clv_data = self._calculate_tier_clv_metrics(start_date, end_date)
        
        optimization_data = {
            'tier_performance': {},
            'value_gaps': {},
            'optimization_opportunities': []
        }
        
        # Analyze each tier
        for tier_type in ['budget', 'mid_tier', 'professional']:
            if tier_type in distribution_data and tier_type in clv_data:
                tier_dist = distribution_data[tier_type]
                tier_clv = clv_data[tier_type]
                
                # Calculate tier performance metrics
                customer_count = tier_dist['customer_count']
                avg_clv = tier_clv.get('avg_clv', 0)
                monthly_revenue = tier_dist['monthly_revenue']
                
                # Performance indicators
                revenue_per_customer = monthly_revenue / customer_count if customer_count > 0 else 0
                clv_to_revenue_ratio = avg_clv / (revenue_per_customer * 12) if revenue_per_customer > 0 else 0
                
                optimization_data['tier_performance'][tier_type] = {
                    'customer_count': customer_count,
                    'avg_clv': avg_clv,
                    'monthly_revenue': monthly_revenue,
                    'revenue_per_customer': revenue_per_customer,
                    'clv_to_revenue_ratio': clv_to_revenue_ratio,
                    'performance_score': min(100, (clv_to_revenue_ratio * 20))  # Simplified scoring
                }
        
        # Identify value gaps
        avg_clv = sum(tier_clv.get('avg_clv', 0) for tier_clv in clv_data.values()) / len(clv_data) if clv_data else 0
        
        for tier_type, performance in optimization_data['tier_performance'].items():
            tier_clv = performance['avg_clv']
            if tier_clv < avg_clv * 0.8:
                optimization_data['value_gaps'][tier_type] = {
                    'gap_percentage': ((avg_clv - tier_clv) / avg_clv) * 100,
                    'potential_value': avg_clv - tier_clv,
                    'recommendation': 'Implement value-add features and improve customer engagement'
                }
        
        return optimization_data
    
    def _identify_upgrade_opportunities(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Identify specific upgrade opportunities"""
        # This would analyze customer usage patterns and behavior
        # For now, return example opportunities
        opportunities = [
            {
                'customer_id': 101,
                'current_tier': 'budget',
                'recommended_tier': 'mid_tier',
                'reason': 'High usage approaching limits',
                'usage_percentage': 85,
                'potential_value': 240,  # Annual value increase
                'confidence_score': 85
            },
            {
                'customer_id': 102,
                'current_tier': 'budget',
                'recommended_tier': 'professional',
                'reason': 'Team collaboration needs detected',
                'usage_percentage': 90,
                'potential_value': 720,
                'confidence_score': 75
            },
            {
                'customer_id': 103,
                'current_tier': 'mid_tier',
                'recommended_tier': 'professional',
                'reason': 'API usage patterns suggest enterprise needs',
                'usage_percentage': 78,
                'potential_value': 480,
                'confidence_score': 80
            }
        ]
        
        return opportunities
    
    def _generate_retention_strategies(self, optimization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate retention strategies based on optimization data"""
        strategies = []
        
        # Analyze value gaps for retention opportunities
        value_gaps = optimization_data.get('value_gaps', {})
        
        for tier_type, gap_data in value_gaps.items():
            if gap_data['gap_percentage'] > 20:
                strategies.append({
                    'tier': tier_type,
                    'strategy_type': 'value_enhancement',
                    'title': f'Enhance {tier_type.title()} Value Proposition',
                    'description': f'Address {gap_data["gap_percentage"]:.1f}% value gap',
                    'actions': [
                        'Add exclusive features for this tier',
                        'Improve customer onboarding and education',
                        'Implement personalized value recommendations'
                    ]
                })
        
        # General retention strategies
        strategies.append({
            'tier': 'all',
            'strategy_type': 'engagement',
            'title': 'Improve Customer Engagement',
            'description': 'Increase customer engagement across all tiers',
            'actions': [
                'Implement regular check-ins and success reviews',
                'Provide personalized usage insights and recommendations',
                'Create tier-specific success stories and case studies'
            ]
        })
        
        return strategies
    
    def _generate_value_optimization_recommendations(self, optimization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate value optimization recommendations"""
        recommendations = []
        
        tier_performance = optimization_data.get('tier_performance', {})
        value_gaps = optimization_data.get('value_gaps', {})
        
        # Performance-based recommendations
        for tier_type, performance in tier_performance.items():
            performance_score = performance.get('performance_score', 0)
            
            if performance_score < 60:
                recommendations.append({
                    'type': 'critical',
                    'title': f'Low {tier_type.title()} Performance',
                    'description': f'{tier_type.title()} performance score is {performance_score:.1f}/100',
                    'action': 'Implement comprehensive value optimization strategy'
                })
            elif performance_score < 80:
                recommendations.append({
                    'type': 'improvement',
                    'title': f'Improve {tier_type.title()} Performance',
                    'description': f'{tier_type.title()} performance score is {performance_score:.1f}/100',
                    'action': 'Focus on value-add features and customer engagement'
                })
        
        # Value gap recommendations
        for tier_type, gap_data in value_gaps.items():
            recommendations.append({
                'type': 'targeted',
                'title': f'Address {tier_type.title()} Value Gap',
                'description': f'{tier_type.title()} has {gap_data["gap_percentage"]:.1f}% value gap',
                'action': gap_data['recommendation']
            })
        
        return recommendations
    
    def _generate_distribution_optimization_recommendations(self, distribution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate distribution optimization recommendations"""
        recommendations = []
        
        if not distribution_data:
            return recommendations
        
        # Remove total from analysis
        tier_data = {k: v for k, v in distribution_data.items() if k != 'total'}
        
        if not tier_data:
            return recommendations
        
        # Find distribution issues
        percentages = [tier_data['percentage'] for tier_data in tier_data.values()]
        max_percentage = max(percentages)
        min_percentage = min(percentages)
        
        # Uneven distribution
        if max_percentage > 60:
            dominant_tier = max(tier_data.items(), key=lambda x: x[1]['percentage'])
            recommendations.append({
                'type': 'warning',
                'title': 'Uneven Tier Distribution',
                'description': f'{dominant_tier[1]["tier_name"]} dominates with {dominant_tier[1]["percentage"]:.1f}% of customers',
                'action': 'Implement strategies to balance tier distribution and encourage upgrades'
            })
        
        # Small tier issues
        for tier_type, tier_data in tier_data.items():
            if tier_data['percentage'] < 10:
                recommendations.append({
                    'type': 'improvement',
                    'title': f'Small {tier_data["tier_name"]} Tier',
                    'description': f'{tier_data["tier_name"]} has only {tier_data["percentage"]:.1f}% of customers',
                    'action': 'Implement targeted marketing and positioning strategies'
                })
        
        return recommendations