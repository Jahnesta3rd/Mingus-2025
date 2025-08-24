#!/usr/bin/env python3
"""
Subscription Analytics and Reporting System for MINGUS
Provides comprehensive business intelligence for revenue optimization.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import json
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Analytics metric types"""
    MRR = "monthly_recurring_revenue"
    ARR = "annual_recurring_revenue"
    CHURN_RATE = "churn_rate"
    EXPANSION_RATE = "expansion_rate"
    CONTRACTION_RATE = "contraction_rate"
    NET_REVENUE_RETENTION = "net_revenue_retention"
    GROSS_REVENUE_RETENTION = "gross_revenue_retention"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    CUSTOMER_ACQUISITION_COST = "customer_acquisition_cost"
    PAYBACK_PERIOD = "payback_period"
    LTV_CAC_RATIO = "ltv_cac_ratio"
    AVERAGE_REVENUE_PER_USER = "average_revenue_per_user"
    TOTAL_ACTIVE_CUSTOMERS = "total_active_customers"
    NEW_CUSTOMERS = "new_customers"
    CHURNED_CUSTOMERS = "churned_customers"
    EXPANDED_CUSTOMERS = "expanded_customers"
    CONTRACTED_CUSTOMERS = "contracted_customers"
    PAYMENT_SUCCESS_RATE = "payment_success_rate"

class CohortType(Enum):
    """Cohort analysis types"""
    SIGNUP_DATE = "signup_date"
    PLAN_TYPE = "plan_type"
    CUSTOMER_SEGMENT = "customer_segment"
    ACQUISITION_CHANNEL = "acquisition_channel"
    GEOGRAPHIC_REGION = "geographic_region"

class TimeGranularity(Enum):
    """Time granularity for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class AnalyticsConfig:
    """Configuration for subscription analytics"""
    # Time periods
    default_period_days: int = 90
    cohort_analysis_periods: int = 12
    forecasting_periods: int = 6
    
    # Churn analysis
    churn_definition_days: int = 30
    churn_grace_period_days: int = 7
    
    # Revenue analysis
    mrr_calculation_method: str = "end_of_month"
    arr_calculation_method: str = "annualized"
    
    # Cohort analysis
    cohort_retention_periods: int = 12
    cohort_minimum_size: int = 10
    
    # Forecasting
    forecasting_confidence_level: float = 0.95
    forecasting_model_type: str = "exponential_smoothing"
    
    # Reporting
    default_time_granularity: TimeGranularity = TimeGranularity.MONTHLY
    include_projections: bool = True
    include_benchmarks: bool = True
    
    # Data retention
    data_retention_days: int = 1095  # 3 years
    
    # Performance
    cache_results: bool = True
    cache_ttl_hours: int = 24
    batch_processing: bool = True
    batch_size: int = 1000

@dataclass
class MetricCalculation:
    """Metric calculation result"""
    metric_type: MetricType
    value: float
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = None

@dataclass
class CohortAnalysis:
    """Cohort analysis result"""
    cohort_type: CohortType
    cohort_period: str
    cohort_size: int
    retention_rates: List[float]
    churn_rates: List[float]
    revenue_evolution: List[float]
    ltv_evolution: List[float]
    metadata: Dict[str, Any] = None

@dataclass
class RevenueForecast:
    """Revenue forecasting result"""
    forecast_periods: int
    forecasted_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    model_accuracy: float
    model_type: str
    assumptions: Dict[str, Any] = None

class SubscriptionAnalytics:
    """
    Comprehensive subscription analytics and reporting system
    Provides business intelligence for revenue optimization
    """
    
    def __init__(self, db_session: Session, config: AnalyticsConfig = None):
        self.db = db_session
        self.config = config or AnalyticsConfig()
        self.cache = {}
        self.cache_timestamps = {}
    
    def calculate_mrr(self, date: datetime = None, include_projections: bool = True) -> MetricCalculation:
        """Calculate Monthly Recurring Revenue (MRR)"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get active subscriptions at the end of the month
            end_of_month = date.replace(day=1) + timedelta(days=32)
            end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
            
            # Query active subscriptions
            active_subscriptions = self._get_active_subscriptions(end_of_month)
            
            # Calculate MRR
            mrr = sum(sub.amount for sub in active_subscriptions if sub.interval == 'month')
            
            # Add annual subscriptions (divided by 12)
            annual_mrr = sum(sub.amount / 12 for sub in active_subscriptions if sub.interval == 'year')
            
            total_mrr = mrr + annual_mrr
            
            # Get previous month MRR for comparison
            previous_month = end_of_month - timedelta(days=32)
            previous_month = previous_month.replace(day=1) + timedelta(days=32)
            previous_month = previous_month.replace(day=1) - timedelta(days=1)
            
            previous_subscriptions = self._get_active_subscriptions(previous_month)
            previous_mrr = sum(sub.amount for sub in previous_subscriptions if sub.interval == 'month')
            previous_annual_mrr = sum(sub.amount / 12 for sub in previous_subscriptions if sub.interval == 'year')
            previous_total_mrr = previous_mrr + previous_annual_mrr
            
            # Calculate change percentage
            change_percentage = None
            if previous_total_mrr > 0:
                change_percentage = ((total_mrr - previous_total_mrr) / previous_total_mrr) * 100
            
            # Determine trend
            trend = None
            if change_percentage is not None:
                if change_percentage > 5:
                    trend = "strong_growth"
                elif change_percentage > 0:
                    trend = "growth"
                elif change_percentage > -5:
                    trend = "stable"
                else:
                    trend = "decline"
            
            # Include projections if requested
            projections = None
            if include_projections and self.config.include_projections:
                projections = self._calculate_mrr_projections(total_mrr, date)
            
            return MetricCalculation(
                metric_type=MetricType.MRR,
                value=total_mrr,
                previous_value=previous_total_mrr,
                change_percentage=change_percentage,
                trend=trend,
                metadata={
                    'date': end_of_month.isoformat(),
                    'active_subscriptions': len(active_subscriptions),
                    'monthly_subscriptions': len([s for s in active_subscriptions if s.interval == 'month']),
                    'annual_subscriptions': len([s for s in active_subscriptions if s.interval == 'year']),
                    'projections': projections
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating MRR: {e}")
            return MetricCalculation(
                metric_type=MetricType.MRR,
                value=0.0,
                metadata={'error': str(e)}
            )
    
    def calculate_arr(self, date: datetime = None) -> MetricCalculation:
        """Calculate Annual Recurring Revenue (ARR)"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get MRR and multiply by 12
            mrr_calculation = self.calculate_mrr(date, include_projections=False)
            arr = mrr_calculation.value * 12
            
            # Get previous year ARR for comparison
            previous_year = date - timedelta(days=365)
            previous_mrr = self.calculate_mrr(previous_year, include_projections=False)
            previous_arr = previous_mrr.value * 12
            
            # Calculate change percentage
            change_percentage = None
            if previous_arr > 0:
                change_percentage = ((arr - previous_arr) / previous_arr) * 100
            
            # Determine trend
            trend = None
            if change_percentage is not None:
                if change_percentage > 20:
                    trend = "strong_growth"
                elif change_percentage > 0:
                    trend = "growth"
                elif change_percentage > -20:
                    trend = "stable"
                else:
                    trend = "decline"
            
            return MetricCalculation(
                metric_type=MetricType.ARR,
                value=arr,
                previous_value=previous_arr,
                change_percentage=change_percentage,
                trend=trend,
                metadata={
                    'date': date.isoformat(),
                    'mrr': mrr_calculation.value,
                    'calculation_method': self.config.arr_calculation_method
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating ARR: {e}")
            return MetricCalculation(
                metric_type=MetricType.ARR,
                value=0.0,
                metadata={'error': str(e)}
            )
    
    def calculate_churn_rate(self, date: datetime = None, period_days: int = 30) -> MetricCalculation:
        """Calculate customer churn rate"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define churn period
            churn_start = date - timedelta(days=period_days)
            churn_end = date
            
            # Get customers at start of period
            customers_at_start = self._get_active_customers(churn_start)
            customers_at_start_count = len(customers_at_start)
            
            # Get customers who churned during period
            churned_customers = self._get_churned_customers(churn_start, churn_end)
            churned_count = len(churned_customers)
            
            # Calculate churn rate
            churn_rate = 0.0
            if customers_at_start_count > 0:
                churn_rate = (churned_count / customers_at_start_count) * 100
            
            # Get previous period churn rate for comparison
            previous_start = churn_start - timedelta(days=period_days)
            previous_end = churn_start
            previous_customers = self._get_active_customers(previous_start)
            previous_churned = self._get_churned_customers(previous_start, previous_end)
            
            previous_churn_rate = 0.0
            if len(previous_customers) > 0:
                previous_churn_rate = (len(previous_churned) / len(previous_customers)) * 100
            
            # Calculate change percentage
            change_percentage = None
            if previous_churn_rate > 0:
                change_percentage = ((churn_rate - previous_churn_rate) / previous_churn_rate) * 100
            
            # Determine trend
            trend = None
            if change_percentage is not None:
                if change_percentage < -20:
                    trend = "improving"
                elif change_percentage < 0:
                    trend = "slight_improvement"
                elif change_percentage < 20:
                    trend = "stable"
                else:
                    trend = "worsening"
            
            return MetricCalculation(
                metric_type=MetricType.CHURN_RATE,
                value=churn_rate,
                previous_value=previous_churn_rate,
                change_percentage=change_percentage,
                trend=trend,
                metadata={
                    'date': date.isoformat(),
                    'period_days': period_days,
                    'customers_at_start': customers_at_start_count,
                    'churned_customers': churned_count,
                    'churn_definition_days': self.config.churn_definition_days
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating churn rate: {e}")
            return MetricCalculation(
                metric_type=MetricType.CHURN_RATE,
                value=0.0,
                metadata={'error': str(e)}
            )
    
    def calculate_net_revenue_retention(self, date: datetime = None, period_days: int = 30) -> MetricCalculation:
        """Calculate Net Revenue Retention (NRR)"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get customers at start of period
            customers_at_start = self._get_active_customers(period_start)
            
            # Calculate revenue at start
            revenue_at_start = sum(self._get_customer_mrr(customer.id, period_start) for customer in customers_at_start)
            
            # Calculate revenue at end (excluding new customers)
            revenue_at_end = 0
            expansion_revenue = 0
            contraction_revenue = 0
            churn_revenue = 0
            
            for customer in customers_at_start:
                customer_mrr_start = self._get_customer_mrr(customer.id, period_start)
                customer_mrr_end = self._get_customer_mrr(customer.id, period_end)
                
                if customer_mrr_end > 0:  # Customer still active
                    revenue_at_end += customer_mrr_end
                    
                    if customer_mrr_end > customer_mrr_start:
                        expansion_revenue += (customer_mrr_end - customer_mrr_start)
                    elif customer_mrr_end < customer_mrr_start:
                        contraction_revenue += (customer_mrr_start - customer_mrr_end)
                else:  # Customer churned
                    churn_revenue += customer_mrr_start
            
            # Calculate NRR
            nrr = 0.0
            if revenue_at_start > 0:
                nrr = (revenue_at_end / revenue_at_start) * 100
            
            # Get previous period NRR for comparison
            previous_start = period_start - timedelta(days=period_days)
            previous_end = period_start
            previous_customers = self._get_active_customers(previous_start)
            previous_revenue_start = sum(self._get_customer_mrr(customer.id, previous_start) for customer in previous_customers)
            previous_revenue_end = sum(self._get_customer_mrr(customer.id, previous_end) for customer in previous_customers)
            
            previous_nrr = 0.0
            if previous_revenue_start > 0:
                previous_nrr = (previous_revenue_end / previous_revenue_start) * 100
            
            # Calculate change percentage
            change_percentage = None
            if previous_nrr > 0:
                change_percentage = ((nrr - previous_nrr) / previous_nrr) * 100
            
            # Determine trend
            trend = None
            if change_percentage is not None:
                if change_percentage > 5:
                    trend = "strong_improvement"
                elif change_percentage > 0:
                    trend = "improvement"
                elif change_percentage > -5:
                    trend = "stable"
                else:
                    trend = "decline"
            
            return MetricCalculation(
                metric_type=MetricType.NET_REVENUE_RETENTION,
                value=nrr,
                previous_value=previous_nrr,
                change_percentage=change_percentage,
                trend=trend,
                metadata={
                    'date': date.isoformat(),
                    'period_days': period_days,
                    'revenue_at_start': revenue_at_start,
                    'revenue_at_end': revenue_at_end,
                    'expansion_revenue': expansion_revenue,
                    'contraction_revenue': contraction_revenue,
                    'churn_revenue': churn_revenue
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating NRR: {e}")
            return MetricCalculation(
                metric_type=MetricType.NET_REVENUE_RETENTION,
                value=0.0,
                metadata={'error': str(e)}
            )
    
    def calculate_customer_lifetime_value(self, date: datetime = None, cohort_periods: int = 12) -> MetricCalculation:
        """Calculate Customer Lifetime Value (CLV)"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get customer cohorts for analysis
            cohorts = self._get_customer_cohorts(date, cohort_periods)
            
            total_ltv = 0.0
            total_customers = 0
            
            for cohort in cohorts:
                cohort_ltv = self._calculate_cohort_ltv(cohort, date)
                total_ltv += cohort_ltv['total_ltv']
                total_customers += cohort_ltv['customer_count']
            
            # Calculate average CLV
            average_clv = 0.0
            if total_customers > 0:
                average_clv = total_ltv / total_customers
            
            # Get previous period CLV for comparison
            previous_date = date - timedelta(days=30)
            previous_cohorts = self._get_customer_cohorts(previous_date, cohort_periods)
            
            previous_total_ltv = 0.0
            previous_total_customers = 0
            
            for cohort in previous_cohorts:
                cohort_ltv = self._calculate_cohort_ltv(cohort, previous_date)
                previous_total_ltv += cohort_ltv['total_ltv']
                previous_total_customers += cohort_ltv['customer_count']
            
            previous_average_clv = 0.0
            if previous_total_customers > 0:
                previous_average_clv = previous_total_ltv / previous_total_customers
            
            # Calculate change percentage
            change_percentage = None
            if previous_average_clv > 0:
                change_percentage = ((average_clv - previous_average_clv) / previous_average_clv) * 100
            
            # Determine trend
            trend = None
            if change_percentage is not None:
                if change_percentage > 10:
                    trend = "strong_growth"
                elif change_percentage > 0:
                    trend = "growth"
                elif change_percentage > -10:
                    trend = "stable"
                else:
                    trend = "decline"
            
            return MetricCalculation(
                metric_type=MetricType.CUSTOMER_LIFETIME_VALUE,
                value=average_clv,
                previous_value=previous_average_clv,
                change_percentage=change_percentage,
                trend=trend,
                metadata={
                    'date': date.isoformat(),
                    'cohort_periods': cohort_periods,
                    'total_customers': total_customers,
                    'total_ltv': total_ltv,
                    'cohort_breakdown': [c['period'] for c in cohorts]
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating CLV: {e}")
            return MetricCalculation(
                metric_type=MetricType.CUSTOMER_LIFETIME_VALUE,
                value=0.0,
                metadata={'error': str(e)}
            )
    
    def perform_cohort_analysis(self, cohort_type: CohortType, date: datetime = None) -> List[CohortAnalysis]:
        """Perform cohort analysis"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            cohorts = []
            
            # Get cohort data based on type
            if cohort_type == CohortType.SIGNUP_DATE:
                cohort_data = self._get_signup_date_cohorts(date)
            elif cohort_type == CohortType.PLAN_TYPE:
                cohort_data = self._get_plan_type_cohorts(date)
            elif cohort_type == CohortType.CUSTOMER_SEGMENT:
                cohort_data = self._get_customer_segment_cohorts(date)
            elif cohort_type == CohortType.ACQUISITION_CHANNEL:
                cohort_data = self._get_acquisition_channel_cohorts(date)
            elif cohort_type == CohortType.GEOGRAPHIC_REGION:
                cohort_data = self._get_geographic_region_cohorts(date)
            else:
                raise ValueError(f"Unsupported cohort type: {cohort_type}")
            
            # Analyze each cohort
            for cohort in cohort_data:
                if cohort['size'] >= self.config.cohort_minimum_size:
                    analysis = self._analyze_cohort(cohort, date)
                    cohorts.append(analysis)
            
            return cohorts
            
        except Exception as e:
            logger.error(f"Error performing cohort analysis: {e}")
            return []
    
    def generate_revenue_forecast(self, periods: int = None, date: datetime = None) -> RevenueForecast:
        """Generate revenue forecast"""
        try:
            if periods is None:
                periods = self.config.forecasting_periods
            
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get historical MRR data
            historical_data = self._get_historical_mrr_data(date, periods * 2)
            
            if len(historical_data) < 3:
                raise ValueError("Insufficient historical data for forecasting")
            
            # Prepare data for forecasting
            dates = [d['date'] for d in historical_data]
            values = [d['mrr'] for d in historical_data]
            
            # Perform forecasting based on model type
            if self.config.forecasting_model_type == "exponential_smoothing":
                forecasted_values, confidence_intervals, accuracy = self._exponential_smoothing_forecast(
                    values, periods, self.config.forecasting_confidence_level
                )
            elif self.config.forecasting_model_type == "linear_regression":
                forecasted_values, confidence_intervals, accuracy = self._linear_regression_forecast(
                    values, periods, self.config.forecasting_confidence_level
                )
            elif self.config.forecasting_model_type == "moving_average":
                forecasted_values, confidence_intervals, accuracy = self._moving_average_forecast(
                    values, periods, self.config.forecasting_confidence_level
                )
            else:
                raise ValueError(f"Unsupported forecasting model: {self.config.forecasting_model_type}")
            
            # Generate forecast dates
            forecast_dates = []
            last_date = dates[-1]
            for i in range(1, periods + 1):
                if last_date.month == 12:
                    forecast_date = last_date.replace(year=last_date.year + 1, month=1)
                else:
                    forecast_date = last_date.replace(month=last_date.month + 1)
                forecast_dates.append(forecast_date)
                last_date = forecast_date
            
            return RevenueForecast(
                forecast_periods=periods,
                forecasted_values=forecasted_values,
                confidence_intervals=confidence_intervals,
                model_accuracy=accuracy,
                model_type=self.config.forecasting_model_type,
                assumptions={
                    'historical_periods': len(historical_data),
                    'confidence_level': self.config.forecasting_confidence_level,
                    'forecast_dates': [d.isoformat() for d in forecast_dates]
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating revenue forecast: {e}")
            return RevenueForecast(
                forecast_periods=periods or 6,
                forecasted_values=[],
                confidence_intervals=[],
                model_accuracy=0.0,
                model_type=self.config.forecasting_model_type,
                assumptions={'error': str(e)}
            )
    
    def generate_comprehensive_report(self, date: datetime = None, include_visualizations: bool = True) -> Dict[str, Any]:
        """Generate comprehensive subscription analytics report"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            report = {
                'report_date': date.isoformat(),
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'metrics': {},
                'cohort_analysis': {},
                'forecasts': {},
                'insights': [],
                'recommendations': []
            }
            
            # Calculate key metrics
            logger.info("Calculating key metrics...")
            report['metrics']['mrr'] = self.calculate_mrr(date)
            report['metrics']['arr'] = self.calculate_arr(date)
            report['metrics']['churn_rate'] = self.calculate_churn_rate(date)
            report['metrics']['net_revenue_retention'] = self.calculate_net_revenue_retention(date)
            report['metrics']['customer_lifetime_value'] = self.calculate_customer_lifetime_value(date)
            
            # Calculate additional metrics
            report['metrics']['expansion_rate'] = self._calculate_expansion_rate(date)
            report['metrics']['contraction_rate'] = self._calculate_contraction_rate(date)
            report['metrics']['gross_revenue_retention'] = self._calculate_gross_revenue_retention(date)
            report['metrics']['average_revenue_per_user'] = self._calculate_average_revenue_per_user(date)
            report['metrics']['total_active_customers'] = self._calculate_total_active_customers(date)
            
            # Perform cohort analysis
            logger.info("Performing cohort analysis...")
            report['cohort_analysis']['signup_date'] = self.perform_cohort_analysis(CohortType.SIGNUP_DATE, date)
            report['cohort_analysis']['plan_type'] = self.perform_cohort_analysis(CohortType.PLAN_TYPE, date)
            report['cohort_analysis']['customer_segment'] = self.perform_cohort_analysis(CohortType.CUSTOMER_SEGMENT, date)
            
            # Generate forecasts
            logger.info("Generating forecasts...")
            report['forecasts']['revenue'] = self.generate_revenue_forecast(date=date)
            report['forecasts']['churn'] = self._forecast_churn_rate(date)
            report['forecasts']['customer_growth'] = self._forecast_customer_growth(date)
            
            # Generate insights
            logger.info("Generating insights...")
            report['insights'] = self._generate_insights(report['metrics'], report['cohort_analysis'], report['forecasts'])
            
            # Generate recommendations
            logger.info("Generating recommendations...")
            report['recommendations'] = self._generate_recommendations(report['metrics'], report['insights'])
            
            # Include visualizations if requested
            if include_visualizations:
                logger.info("Generating visualizations...")
                report['visualizations'] = self._generate_visualizations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                'error': str(e),
                'report_date': date.isoformat() if date else datetime.now(timezone.utc).isoformat(),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def calculate_customer_acquisition_cost_by_channel(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
        """Calculate Customer Acquisition Cost (CAC) by channel"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get acquisition data by channel
            acquisition_data = self._get_acquisition_data_by_channel(period_start, period_end)
            
            cac_by_channel = {}
            
            for channel, data in acquisition_data.items():
                # Calculate CAC for each channel
                total_cost = data['total_cost']
                new_customers = data['new_customers']
                
                cac = 0.0
                if new_customers > 0:
                    cac = total_cost / new_customers
                
                # Get previous period for comparison
                previous_start = period_start - timedelta(days=period_days)
                previous_end = period_start
                previous_data = self._get_acquisition_data_by_channel(previous_start, previous_end)
                
                previous_cac = 0.0
                if channel in previous_data and previous_data[channel]['new_customers'] > 0:
                    previous_cac = previous_data[channel]['total_cost'] / previous_data[channel]['new_customers']
                
                # Calculate change percentage
                change_percentage = None
                if previous_cac > 0:
                    change_percentage = ((cac - previous_cac) / previous_cac) * 100
                
                # Determine trend
                trend = None
                if change_percentage is not None:
                    if change_percentage < -10:
                        trend = "improving"
                    elif change_percentage < 0:
                        trend = "slight_improvement"
                    elif change_percentage < 10:
                        trend = "stable"
                    else:
                        trend = "worsening"
                
                cac_by_channel[channel] = MetricCalculation(
                    metric_type=MetricType.CUSTOMER_ACQUISITION_COST,
                    value=cac,
                    previous_value=previous_cac,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'channel': channel,
                        'date': date.isoformat(),
                        'period_days': period_days,
                        'total_cost': total_cost,
                        'new_customers': new_customers,
                        'cost_breakdown': data.get('cost_breakdown', {}),
                        'conversion_rate': data.get('conversion_rate', 0.0),
                        'channel_efficiency': data.get('channel_efficiency', 0.0)
                    }
                )
            
            return cac_by_channel
            
        except Exception as e:
            logger.error(f"Error calculating CAC by channel: {e}")
            return {}
    
    def calculate_customer_lifetime_value_by_tier(self, date: datetime = None, cohort_periods: int = 12) -> Dict[str, MetricCalculation]:
        """Calculate Customer Lifetime Value (CLV) by tier"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get customer tiers
            tiers = self._get_customer_tiers()
            
            clv_by_tier = {}
            
            for tier in tiers:
                # Get customers in this tier
                tier_customers = self._get_customers_by_tier(tier, date)
                
                if not tier_customers:
                    continue
                
                # Calculate CLV for this tier
                total_ltv = 0.0
                customer_count = 0
                
                for customer in tier_customers:
                    customer_ltv = self._calculate_individual_clv(customer.id, date, cohort_periods)
                    total_ltv += customer_ltv
                    customer_count += 1
                
                # Calculate average CLV for tier
                average_clv = 0.0
                if customer_count > 0:
                    average_clv = total_ltv / customer_count
                
                # Get previous period CLV for comparison
                previous_date = date - timedelta(days=30)
                previous_customers = self._get_customers_by_tier(tier, previous_date)
                
                previous_total_ltv = 0.0
                previous_customer_count = 0
                
                for customer in previous_customers:
                    customer_ltv = self._calculate_individual_clv(customer.id, previous_date, cohort_periods)
                    previous_total_ltv += customer_ltv
                    previous_customer_count += 1
                
                previous_average_clv = 0.0
                if previous_customer_count > 0:
                    previous_average_clv = previous_total_ltv / previous_customer_count
                
                # Calculate change percentage
                change_percentage = None
                if previous_average_clv > 0:
                    change_percentage = ((average_clv - previous_average_clv) / previous_average_clv) * 100
                
                # Determine trend
                trend = None
                if change_percentage is not None:
                    if change_percentage > 10:
                        trend = "strong_growth"
                    elif change_percentage > 0:
                        trend = "growth"
                    elif change_percentage > -10:
                        trend = "stable"
                    else:
                        trend = "decline"
                
                clv_by_tier[tier] = MetricCalculation(
                    metric_type=MetricType.CUSTOMER_LIFETIME_VALUE,
                    value=average_clv,
                    previous_value=previous_average_clv,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'tier': tier,
                        'date': date.isoformat(),
                        'cohort_periods': cohort_periods,
                        'customer_count': customer_count,
                        'total_ltv': total_ltv,
                        'tier_distribution': self._get_tier_distribution(date),
                        'tier_retention_rate': self._calculate_tier_retention_rate(tier, date),
                        'tier_expansion_rate': self._calculate_tier_expansion_rate(tier, date)
                    }
                )
            
            return clv_by_tier
            
        except Exception as e:
            logger.error(f"Error calculating CLV by tier: {e}")
            return {}
    
    def calculate_churn_rate_by_tier(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
        """Calculate churn rate by customer tier"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define churn period
            churn_start = date - timedelta(days=period_days)
            churn_end = date
            
            # Get customer tiers
            tiers = self._get_customer_tiers()
            
            churn_by_tier = {}
            
            for tier in tiers:
                # Get customers in this tier at start of period
                customers_at_start = self._get_customers_by_tier(tier, churn_start)
                customers_at_start_count = len(customers_at_start)
                
                # Get customers who churned during period
                churned_customers = self._get_churned_customers_by_tier(tier, churn_start, churn_end)
                churned_count = len(churned_customers)
                
                # Calculate churn rate for this tier
                churn_rate = 0.0
                if customers_at_start_count > 0:
                    churn_rate = (churned_count / customers_at_start_count) * 100
                
                # Get previous period churn rate for comparison
                previous_start = churn_start - timedelta(days=period_days)
                previous_end = churn_start
                previous_customers = self._get_customers_by_tier(tier, previous_start)
                previous_churned = self._get_churned_customers_by_tier(tier, previous_start, previous_end)
                
                previous_churn_rate = 0.0
                if len(previous_customers) > 0:
                    previous_churn_rate = (len(previous_churned) / len(previous_customers)) * 100
                
                # Calculate change percentage
                change_percentage = None
                if previous_churn_rate > 0:
                    change_percentage = ((churn_rate - previous_churn_rate) / previous_churn_rate) * 100
                
                # Determine trend
                trend = None
                if change_percentage is not None:
                    if change_percentage < -20:
                        trend = "improving"
                    elif change_percentage < 0:
                        trend = "slight_improvement"
                    elif change_percentage < 20:
                        trend = "stable"
                    else:
                        trend = "worsening"
                
                churn_by_tier[tier] = MetricCalculation(
                    metric_type=MetricType.CHURN_RATE,
                    value=churn_rate,
                    previous_value=previous_churn_rate,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'tier': tier,
                        'date': date.isoformat(),
                        'period_days': period_days,
                        'customers_at_start': customers_at_start_count,
                        'churned_customers': churned_count,
                        'churn_reasons': self._get_churn_reasons_by_tier(tier, churn_start, churn_end),
                        'tier_retention_strategies': self._get_tier_retention_strategies(tier),
                        'churn_prediction_score': self._calculate_churn_prediction_score(tier, date)
                    }
                )
            
            return churn_by_tier
            
        except Exception as e:
            logger.error(f"Error calculating churn rate by tier: {e}")
            return {}
    
    def perform_cohort_analysis_by_tier(self, cohort_type: CohortType, date: datetime = None) -> Dict[str, List[CohortAnalysis]]:
        """Perform cohort analysis by customer tier"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get customer tiers
            tiers = self._get_customer_tiers()
            
            cohort_analysis_by_tier = {}
            
            for tier in tiers:
                # Get cohort data for this tier
                if cohort_type == CohortType.SIGNUP_DATE:
                    cohort_data = self._get_signup_date_cohorts_by_tier(tier, date)
                elif cohort_type == CohortType.PLAN_TYPE:
                    cohort_data = self._get_plan_type_cohorts_by_tier(tier, date)
                elif cohort_type == CohortType.CUSTOMER_SEGMENT:
                    cohort_data = self._get_customer_segment_cohorts_by_tier(tier, date)
                elif cohort_type == CohortType.ACQUISITION_CHANNEL:
                    cohort_data = self._get_acquisition_channel_cohorts_by_tier(tier, date)
                elif cohort_type == CohortType.GEOGRAPHIC_REGION:
                    cohort_data = self._get_geographic_region_cohorts_by_tier(tier, date)
                else:
                    raise ValueError(f"Unsupported cohort type: {cohort_type}")
                
                # Analyze cohorts for this tier
                tier_cohorts = []
                for cohort in cohort_data:
                    if cohort['size'] >= self.config.cohort_minimum_size:
                        analysis = self._analyze_cohort_by_tier(cohort, tier, date)
                        tier_cohorts.append(analysis)
                
                cohort_analysis_by_tier[tier] = tier_cohorts
            
            return cohort_analysis_by_tier
            
        except Exception as e:
            logger.error(f"Error performing cohort analysis by tier: {e}")
            return {}
    
    def calculate_revenue_per_user_by_tier(self, date: datetime = None) -> Dict[str, MetricCalculation]:
        """Calculate revenue per user by tier"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get customer tiers
            tiers = self._get_customer_tiers()
            
            revenue_per_user_by_tier = {}
            
            for tier in tiers:
                # Get customers in this tier
                tier_customers = self._get_customers_by_tier(tier, date)
                
                if not tier_customers:
                    continue
                
                # Calculate total revenue for this tier
                total_revenue = 0.0
                customer_count = len(tier_customers)
                
                for customer in tier_customers:
                    customer_revenue = self._get_customer_mrr(customer.id, date)
                    total_revenue += customer_revenue
                
                # Calculate average revenue per user
                average_revenue_per_user = 0.0
                if customer_count > 0:
                    average_revenue_per_user = total_revenue / customer_count
                
                # Get previous period for comparison
                previous_date = date - timedelta(days=30)
                previous_customers = self._get_customers_by_tier(tier, previous_date)
                
                previous_total_revenue = 0.0
                previous_customer_count = len(previous_customers)
                
                for customer in previous_customers:
                    customer_revenue = self._get_customer_mrr(customer.id, previous_date)
                    previous_total_revenue += customer_revenue
                
                previous_average_revenue_per_user = 0.0
                if previous_customer_count > 0:
                    previous_average_revenue_per_user = previous_total_revenue / previous_customer_count
                
                # Calculate change percentage
                change_percentage = None
                if previous_average_revenue_per_user > 0:
                    change_percentage = ((average_revenue_per_user - previous_average_revenue_per_user) / previous_average_revenue_per_user) * 100
                
                # Determine trend
                trend = None
                if change_percentage is not None:
                    if change_percentage > 10:
                        trend = "strong_growth"
                    elif change_percentage > 0:
                        trend = "growth"
                    elif change_percentage > -10:
                        trend = "stable"
                    else:
                        trend = "decline"
                
                revenue_per_user_by_tier[tier] = MetricCalculation(
                    metric_type=MetricType.AVERAGE_REVENUE_PER_USER,
                    value=average_revenue_per_user,
                    previous_value=previous_average_revenue_per_user,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'tier': tier,
                        'date': date.isoformat(),
                        'customer_count': customer_count,
                        'total_revenue': total_revenue,
                        'tier_distribution': self._get_tier_distribution(date),
                        'revenue_distribution': self._get_revenue_distribution_by_tier(tier, date),
                        'usage_patterns': self._get_usage_patterns_by_tier(tier, date),
                        'feature_adoption': self._get_feature_adoption_by_tier(tier, date)
                    }
                )
            
            return revenue_per_user_by_tier
            
        except Exception as e:
            logger.error(f"Error calculating revenue per user by tier: {e}")
            return {}
    
    def get_tier_distribution_analysis(self, date: datetime = None) -> Dict[str, Any]:
        """Get comprehensive tier distribution analysis"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get tier distribution
            tier_distribution = self._get_tier_distribution(date)
            
            # Get previous period for comparison
            previous_date = date - timedelta(days=30)
            previous_tier_distribution = self._get_tier_distribution(previous_date)
            
            # Calculate tier metrics
            tier_metrics = {}
            tiers = self._get_customer_tiers()
            
            for tier in tiers:
                current_count = tier_distribution.get(tier, 0)
                previous_count = previous_tier_distribution.get(tier, 0)
                
                # Calculate change
                change_count = current_count - previous_count
                change_percentage = None
                if previous_count > 0:
                    change_percentage = (change_count / previous_count) * 100
                
                # Get tier-specific metrics
                tier_metrics[tier] = {
                    'current_count': current_count,
                    'previous_count': previous_count,
                    'change_count': change_count,
                    'change_percentage': change_percentage,
                    'percentage_of_total': (current_count / sum(tier_distribution.values())) * 100 if sum(tier_distribution.values()) > 0 else 0,
                    'revenue_contribution': self._calculate_tier_revenue_contribution(tier, date),
                    'growth_rate': self._calculate_tier_growth_rate(tier, date),
                    'migration_patterns': self._get_tier_migration_patterns(tier, date),
                    'upgrade_rate': self._calculate_tier_upgrade_rate(tier, date),
                    'downgrade_rate': self._calculate_tier_downgrade_rate(tier, date)
                }
            
            return {
                'date': date.isoformat(),
                'tier_distribution': tier_distribution,
                'previous_tier_distribution': previous_tier_distribution,
                'tier_metrics': tier_metrics,
                'total_customers': sum(tier_distribution.values()),
                'distribution_trends': self._analyze_distribution_trends(tier_distribution, previous_tier_distribution),
                'tier_performance_ranking': self._rank_tier_performance(tier_metrics),
                'recommendations': self._generate_tier_recommendations(tier_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting tier distribution analysis: {e}")
            return {}
    
    def calculate_ltv_cac_ratio_by_channel(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
        """Calculate LTV/CAC ratio by acquisition channel"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Get CAC by channel
            cac_by_channel = self.calculate_customer_acquisition_cost_by_channel(date, period_days)
            
            # Get CLV by channel
            clv_by_channel = self._calculate_clv_by_channel(date, period_days)
            
            ltv_cac_ratios = {}
            
            for channel in cac_by_channel.keys():
                cac = cac_by_channel[channel].value
                clv = clv_by_channel.get(channel, 0.0)
                
                # Calculate LTV/CAC ratio
                ltv_cac_ratio = 0.0
                if cac > 0:
                    ltv_cac_ratio = clv / cac
                
                # Get previous period for comparison
                previous_date = date - timedelta(days=period_days)
                previous_cac_by_channel = self.calculate_customer_acquisition_cost_by_channel(previous_date, period_days)
                previous_clv_by_channel = self._calculate_clv_by_channel(previous_date, period_days)
                
                previous_ratio = 0.0
                if channel in previous_cac_by_channel and previous_cac_by_channel[channel].value > 0:
                    previous_clv = previous_clv_by_channel.get(channel, 0.0)
                    previous_ratio = previous_clv / previous_cac_by_channel[channel].value
                
                # Calculate change percentage
                change_percentage = None
                if previous_ratio > 0:
                    change_percentage = ((ltv_cac_ratio - previous_ratio) / previous_ratio) * 100
                
                # Determine trend and health
                trend = None
                health_status = None
                
                if ltv_cac_ratio >= 3.0:
                    health_status = "excellent"
                    trend = "strong_growth" if change_percentage and change_percentage > 10 else "stable"
                elif ltv_cac_ratio >= 1.0:
                    health_status = "good"
                    trend = "growth" if change_percentage and change_percentage > 0 else "stable"
                else:
                    health_status = "poor"
                    trend = "decline"
                
                ltv_cac_ratios[channel] = MetricCalculation(
                    metric_type=MetricType.LTV_CAC_RATIO,
                    value=ltv_cac_ratio,
                    previous_value=previous_ratio,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'channel': channel,
                        'date': date.isoformat(),
                        'period_days': period_days,
                        'cac': cac,
                        'clv': clv,
                        'health_status': health_status,
                        'payback_period': self._calculate_payback_period(cac, clv),
                        'channel_efficiency': self._calculate_channel_efficiency(channel, date),
                        'optimization_opportunities': self._identify_channel_optimization_opportunities(channel, ltv_cac_ratio)
                    }
                )
            
            return ltv_cac_ratios
            
        except Exception as e:
            logger.error(f"Error calculating LTV/CAC ratio by channel: {e}")
            return {}
    
    def _get_active_subscriptions(self, date: datetime) -> List[Any]:
        """Get active subscriptions at a specific date"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_active_customers(self, date: datetime) -> List[Any]:
        """Get active customers at a specific date"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_churned_customers(self, start_date: datetime, end_date: datetime) -> List[Any]:
        """Get customers who churned between start and end dates"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_customer_mrr(self, customer_id: str, date: datetime) -> float:
        """Get MRR for a specific customer at a specific date"""
        # This would query the actual database
        # For now, return mock data
        return 0.0
    
    def _get_customer_cohorts(self, date: datetime, periods: int) -> List[Dict[str, Any]]:
        """Get customer cohorts for analysis"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _calculate_cohort_ltv(self, cohort: Dict[str, Any], date: datetime) -> Dict[str, Any]:
        """Calculate lifetime value for a cohort"""
        # This would perform actual LTV calculation
        # For now, return mock data
        return {
            'total_ltv': 0.0,
            'customer_count': 0
        }
    
    def _get_signup_date_cohorts(self, date: datetime) -> List[Dict[str, Any]]:
        """Get cohorts based on signup date"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_plan_type_cohorts(self, date: datetime) -> List[Dict[str, Any]]:
        """Get cohorts based on plan type"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_customer_segment_cohorts(self, date: datetime) -> List[Dict[str, Any]]:
        """Get cohorts based on customer segment"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_acquisition_channel_cohorts(self, date: datetime) -> List[Dict[str, Any]]:
        """Get cohorts based on acquisition channel"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_geographic_region_cohorts(self, date: datetime) -> List[Dict[str, Any]]:
        """Get cohorts based on geographic region"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _analyze_cohort(self, cohort: Dict[str, Any], date: datetime) -> CohortAnalysis:
        """Analyze a specific cohort"""
        # This would perform actual cohort analysis
        # For now, return mock data
        return CohortAnalysis(
            cohort_type=CohortType.SIGNUP_DATE,
            cohort_period=cohort.get('period', ''),
            cohort_size=cohort.get('size', 0),
            retention_rates=[100.0, 95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 65.0, 60.0, 55.0, 50.0, 45.0],
            churn_rates=[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            revenue_evolution=[100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0],
            ltv_evolution=[100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0, 1200.0]
        )
    
    def _get_historical_mrr_data(self, date: datetime, periods: int) -> List[Dict[str, Any]]:
        """Get historical MRR data for forecasting"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _exponential_smoothing_forecast(self, values: List[float], periods: int, confidence_level: float) -> Tuple[List[float], List[Tuple[float, float]], float]:
        """Perform exponential smoothing forecast"""
        # This would perform actual exponential smoothing
        # For now, return mock data
        forecasted = [values[-1] * (1.05 ** i) for i in range(1, periods + 1)]
        confidence_intervals = [(v * 0.9, v * 1.1) for v in forecasted]
        accuracy = 0.85
        return forecasted, confidence_intervals, accuracy
    
    def _linear_regression_forecast(self, values: List[float], periods: int, confidence_level: float) -> Tuple[List[float], List[Tuple[float, float]], float]:
        """Perform linear regression forecast"""
        # This would perform actual linear regression
        # For now, return mock data
        forecasted = [values[-1] + (i * 100) for i in range(1, periods + 1)]
        confidence_intervals = [(v * 0.9, v * 1.1) for v in forecasted]
        accuracy = 0.80
        return forecasted, confidence_intervals, accuracy
    
    def _moving_average_forecast(self, values: List[float], periods: int, confidence_level: float) -> Tuple[List[float], List[Tuple[float, float]], float]:
        """Perform moving average forecast"""
        # This would perform actual moving average
        # For now, return mock data
        avg = sum(values[-3:]) / 3
        forecasted = [avg for _ in range(periods)]
        confidence_intervals = [(v * 0.9, v * 1.1) for v in forecasted]
        accuracy = 0.75
        return forecasted, confidence_intervals, accuracy
    
    def _calculate_mrr_projections(self, current_mrr: float, date: datetime) -> Dict[str, Any]:
        """Calculate MRR projections"""
        # This would perform actual projections
        # For now, return mock data
        return {
            'next_month': current_mrr * 1.05,
            'next_quarter': current_mrr * 1.15,
            'next_year': current_mrr * 1.50
        }
    
    def _calculate_expansion_rate(self, date: datetime) -> MetricCalculation:
        """Calculate expansion rate"""
        # This would perform actual calculation
        # For now, return mock data
        return MetricCalculation(
            metric_type=MetricType.EXPANSION_RATE,
            value=5.0,
            metadata={'date': date.isoformat()}
        )
    
    def _calculate_contraction_rate(self, date: datetime) -> MetricCalculation:
        """Calculate contraction rate"""
        # This would perform actual calculation
        # For now, return mock data
        return MetricCalculation(
            metric_type=MetricType.CONTRACTION_RATE,
            value=2.0,
            metadata={'date': date.isoformat()}
        )
    
    def _calculate_gross_revenue_retention(self, date: datetime) -> MetricCalculation:
        """Calculate gross revenue retention"""
        # This would perform actual calculation
        # For now, return mock data
        return MetricCalculation(
            metric_type=MetricType.GROSS_REVENUE_RETENTION,
            value=95.0,
            metadata={'date': date.isoformat()}
        )
    
    def _calculate_average_revenue_per_user(self, date: datetime) -> MetricCalculation:
        """Calculate average revenue per user"""
        # This would perform actual calculation
        # For now, return mock data
        return MetricCalculation(
            metric_type=MetricType.AVERAGE_REVENUE_PER_USER,
            value=150.0,
            metadata={'date': date.isoformat()}
        )
    
    def _calculate_total_active_customers(self, date: datetime) -> MetricCalculation:
        """Calculate total active customers"""
        # This would perform actual calculation
        # For now, return mock data
        return MetricCalculation(
            metric_type=MetricType.TOTAL_ACTIVE_CUSTOMERS,
            value=1000,
            metadata={'date': date.isoformat()}
        )
    
    def _forecast_churn_rate(self, date: datetime) -> Dict[str, Any]:
        """Forecast churn rate"""
        # This would perform actual forecasting
        # For now, return mock data
        return {
            'forecasted_values': [3.0, 3.2, 3.1, 2.9, 2.8, 2.7],
            'confidence_intervals': [(2.5, 3.5), (2.7, 3.7), (2.6, 3.6), (2.4, 3.4), (2.3, 3.3), (2.2, 3.2)],
            'model_accuracy': 0.85
        }
    
    def _forecast_customer_growth(self, date: datetime) -> Dict[str, Any]:
        """Forecast customer growth"""
        # This would perform actual forecasting
        # For now, return mock data
        return {
            'forecasted_values': [1050, 1100, 1150, 1200, 1250, 1300],
            'confidence_intervals': [(1000, 1100), (1050, 1150), (1100, 1200), (1150, 1250), (1200, 1300), (1250, 1350)],
            'model_accuracy': 0.90
        }
    
    def _generate_insights(self, metrics: Dict[str, MetricCalculation], cohorts: Dict[str, List[CohortAnalysis]], forecasts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from analytics data"""
        insights = []
        
        # MRR insights
        mrr = metrics.get('mrr')
        if mrr and mrr.trend == 'strong_growth':
            insights.append({
                'type': 'positive',
                'category': 'revenue',
                'title': 'Strong MRR Growth',
                'description': f'MRR is growing strongly at {mrr.change_percentage:.1f}% month-over-month',
                'impact': 'high',
                'recommendation': 'Continue current growth strategies'
            })
        
        # Churn insights
        churn = metrics.get('churn_rate')
        if churn and churn.trend == 'worsening':
            insights.append({
                'type': 'negative',
                'category': 'retention',
                'title': 'Increasing Churn Rate',
                'description': f'Churn rate is increasing to {churn.value:.1f}%',
                'impact': 'high',
                'recommendation': 'Investigate churn causes and implement retention strategies'
            })
        
        # NRR insights
        nrr = metrics.get('net_revenue_retention')
        if nrr and nrr.value > 100:
            insights.append({
                'type': 'positive',
                'category': 'retention',
                'title': 'Strong Net Revenue Retention',
                'description': f'NRR is {nrr.value:.1f}%, indicating strong expansion revenue',
                'impact': 'medium',
                'recommendation': 'Focus on expansion opportunities'
            })
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict[str, MetricCalculation], insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        # Revenue optimization recommendations
        mrr = metrics.get('mrr')
        if mrr and mrr.change_percentage and mrr.change_percentage < 5:
            recommendations.append({
                'category': 'revenue_optimization',
                'priority': 'high',
                'title': 'Improve MRR Growth',
                'description': 'MRR growth is below target. Focus on customer acquisition and expansion.',
                'actions': [
                    'Increase marketing spend on high-converting channels',
                    'Implement upsell campaigns for existing customers',
                    'Optimize pricing strategy'
                ]
            })
        
        # Churn reduction recommendations
        churn = metrics.get('churn_rate')
        if churn and churn.value > 5:
            recommendations.append({
                'category': 'churn_reduction',
                'priority': 'high',
                'title': 'Reduce Customer Churn',
                'description': f'Churn rate of {churn.value:.1f}% is above industry average.',
                'actions': [
                    'Implement customer success programs',
                    'Improve onboarding process',
                    'Add proactive support and engagement'
                ]
            })
        
        # Customer acquisition recommendations
        arr = metrics.get('arr')
        if arr and arr.change_percentage and arr.change_percentage < 20:
            recommendations.append({
                'category': 'customer_acquisition',
                'priority': 'medium',
                'title': 'Accelerate Customer Acquisition',
                'description': 'ARR growth suggests need for faster customer acquisition.',
                'actions': [
                    'Expand to new markets or segments',
                    'Improve conversion rates',
                    'Launch referral programs'
                ]
            })
        
        return recommendations
    
    def _generate_visualizations(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualizations for the report"""
        # This would generate actual charts and graphs
        # For now, return mock data
        return {
            'mrr_trend': 'data:image/png;base64,...',
            'churn_analysis': 'data:image/png;base64,...',
            'cohort_retention': 'data:image/png;base64,...',
            'revenue_forecast': 'data:image/png;base64,...'
        } 
    
    def _get_acquisition_data_by_channel(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Any]]:
        """Get acquisition data by channel for a specific period"""
        # This would query the actual database
        # For now, return mock data
        return {
            'organic_search': {
                'total_cost': 5000.0,
                'new_customers': 50,
                'cost_breakdown': {
                    'seo_tools': 2000.0,
                    'content_creation': 1500.0,
                    'technical_seo': 1500.0
                },
                'conversion_rate': 0.025,
                'channel_efficiency': 0.85
            },
            'paid_advertising': {
                'total_cost': 15000.0,
                'new_customers': 75,
                'cost_breakdown': {
                    'google_ads': 8000.0,
                    'facebook_ads': 5000.0,
                    'linkedin_ads': 2000.0
                },
                'conversion_rate': 0.015,
                'channel_efficiency': 0.70
            },
            'referral': {
                'total_cost': 3000.0,
                'new_customers': 30,
                'cost_breakdown': {
                    'referral_program': 2000.0,
                    'partner_commissions': 1000.0
                },
                'conversion_rate': 0.040,
                'channel_efficiency': 0.90
            },
            'partnership': {
                'total_cost': 8000.0,
                'new_customers': 40,
                'cost_breakdown': {
                    'partner_marketing': 5000.0,
                    'joint_ventures': 3000.0
                },
                'conversion_rate': 0.030,
                'channel_efficiency': 0.80
            }
        }
    
    def _get_customer_tiers(self) -> List[str]:
        """Get list of customer tiers"""
        return ['standard', 'premium', 'enterprise']
    
    def _get_customers_by_tier(self, tier: str, date: datetime) -> List[Any]:
        """Get customers by tier at a specific date"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _calculate_individual_clv(self, customer_id: str, date: datetime, cohort_periods: int) -> float:
        """Calculate individual customer lifetime value"""
        # This would perform actual CLV calculation
        # For now, return mock data
        return 1200.0
    
    def _get_tier_distribution(self, date: datetime) -> Dict[str, int]:
        """Get customer distribution by tier"""
        # This would query the actual database
        # For now, return mock data
        return {
            'standard': 600,
            'premium': 300,
            'enterprise': 100
        }
    
    def _calculate_tier_retention_rate(self, tier: str, date: datetime) -> float:
        """Calculate retention rate for a specific tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 85.0
    
    def _calculate_tier_expansion_rate(self, tier: str, date: datetime) -> float:
        """Calculate expansion rate for a specific tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 12.0
    
    def _get_churned_customers_by_tier(self, tier: str, start_date: datetime, end_date: datetime) -> List[Any]:
        """Get churned customers by tier for a specific period"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_churn_reasons_by_tier(self, tier: str, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get churn reasons by tier"""
        # This would query the actual database
        # For now, return mock data
        return {
            'pricing': 15,
            'features': 8,
            'support': 5,
            'competition': 12,
            'business_closed': 3
        }
    
    def _get_tier_retention_strategies(self, tier: str) -> List[str]:
        """Get retention strategies for a specific tier"""
        # This would return actual strategies
        # For now, return mock data
        return [
            'personalized_onboarding',
            'regular_check_ins',
            'feature_education',
            'success_planning',
            'exclusive_benefits'
        ]
    
    def _calculate_churn_prediction_score(self, tier: str, date: datetime) -> float:
        """Calculate churn prediction score for a tier"""
        # This would perform actual prediction
        # For now, return mock data
        return 0.15
    
    def _get_signup_date_cohorts_by_tier(self, tier: str, date: datetime) -> List[Dict[str, Any]]:
        """Get signup date cohorts by tier"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_plan_type_cohorts_by_tier(self, tier: str, date: datetime) -> List[Dict[str, Any]]:
        """Get plan type cohorts by tier"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_customer_segment_cohorts_by_tier(self, tier: str, date: datetime) -> List[Dict[str, Any]]:
        """Get customer segment cohorts by tier"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_acquisition_channel_cohorts_by_tier(self, tier: str, date: datetime) -> List[Dict[str, Any]]:
        """Get acquisition channel cohorts by tier"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _get_geographic_region_cohorts_by_tier(self, tier: str, date: datetime) -> List[Dict[str, Any]]:
        """Get geographic region cohorts by tier"""
        # This would query the actual database
        # For now, return mock data
        return []
    
    def _analyze_cohort_by_tier(self, cohort: Dict[str, Any], tier: str, date: datetime) -> CohortAnalysis:
        """Analyze a specific cohort for a tier"""
        # This would perform actual cohort analysis
        # For now, return mock data
        return CohortAnalysis(
            cohort_type=CohortType.SIGNUP_DATE,
            cohort_period=cohort.get('period', ''),
            cohort_size=cohort.get('size', 0),
            retention_rates=[100.0, 95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 65.0, 60.0, 55.0, 50.0, 45.0],
            churn_rates=[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            revenue_evolution=[100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0],
            ltv_evolution=[100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0, 1200.0]
        )
    
    def _get_revenue_distribution_by_tier(self, tier: str, date: datetime) -> Dict[str, float]:
        """Get revenue distribution within a tier"""
        # This would query the actual database
        # For now, return mock data
        return {
            'low_revenue': 0.30,
            'medium_revenue': 0.45,
            'high_revenue': 0.25
        }
    
    def _get_usage_patterns_by_tier(self, tier: str, date: datetime) -> Dict[str, Any]:
        """Get usage patterns for a tier"""
        # This would query the actual database
        # For now, return mock data
        return {
            'average_sessions_per_month': 25,
            'average_session_duration': 45,
            'feature_usage_distribution': {
                'core_features': 0.80,
                'advanced_features': 0.60,
                'premium_features': 0.40
            }
        }
    
    def _get_feature_adoption_by_tier(self, tier: str, date: datetime) -> Dict[str, float]:
        """Get feature adoption rates by tier"""
        # This would query the actual database
        # For now, return mock data
        return {
            'feature_a': 0.85,
            'feature_b': 0.70,
            'feature_c': 0.55,
            'feature_d': 0.40,
            'feature_e': 0.25
        }
    
    def _calculate_tier_revenue_contribution(self, tier: str, date: datetime) -> float:
        """Calculate revenue contribution percentage for a tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 35.0
    
    def _calculate_tier_growth_rate(self, tier: str, date: datetime) -> float:
        """Calculate growth rate for a tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 8.5
    
    def _get_tier_migration_patterns(self, tier: str, date: datetime) -> Dict[str, int]:
        """Get tier migration patterns"""
        # This would query the actual database
        # For now, return mock data
        return {
            'upgrades': 15,
            'downgrades': 8,
            'same_tier': 77
        }
    
    def _calculate_tier_upgrade_rate(self, tier: str, date: datetime) -> float:
        """Calculate upgrade rate for a tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 12.0
    
    def _calculate_tier_downgrade_rate(self, tier: str, date: datetime) -> float:
        """Calculate downgrade rate for a tier"""
        # This would perform actual calculation
        # For now, return mock data
        return 6.5
    
    def _analyze_distribution_trends(self, current_distribution: Dict[str, int], previous_distribution: Dict[str, int]) -> Dict[str, str]:
        """Analyze distribution trends"""
        trends = {}
        for tier in current_distribution.keys():
            current = current_distribution.get(tier, 0)
            previous = previous_distribution.get(tier, 0)
            
            if current > previous:
                trends[tier] = "growing"
            elif current < previous:
                trends[tier] = "declining"
            else:
                trends[tier] = "stable"
        
        return trends
    
    def _rank_tier_performance(self, tier_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Rank tiers by performance"""
        # Sort by growth rate
        sorted_tiers = sorted(
            tier_metrics.items(),
            key=lambda x: x[1].get('growth_rate', 0),
            reverse=True
        )
        return [tier for tier, _ in sorted_tiers]
    
    def _generate_tier_recommendations(self, tier_metrics: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on tier metrics"""
        recommendations = []
        
        for tier, metrics in tier_metrics.items():
            growth_rate = metrics.get('growth_rate', 0)
            upgrade_rate = metrics.get('upgrade_rate', 0)
            downgrade_rate = metrics.get('downgrade_rate', 0)
            
            if growth_rate < 5:
                recommendations.append({
                    'tier': tier,
                    'type': 'growth',
                    'priority': 'high',
                    'recommendation': f'Focus on customer acquisition for {tier} tier',
                    'actions': ['Increase marketing spend', 'Improve conversion rates', 'Launch referral programs']
                })
            
            if upgrade_rate < 10:
                recommendations.append({
                    'tier': tier,
                    'type': 'upgrade',
                    'priority': 'medium',
                    'recommendation': f'Improve upgrade rates for {tier} tier',
                    'actions': ['Feature education campaigns', 'Success stories', 'Upgrade incentives']
                })
            
            if downgrade_rate > 8:
                recommendations.append({
                    'tier': tier,
                    'type': 'retention',
                    'priority': 'high',
                    'recommendation': f'Reduce downgrade rates for {tier} tier',
                    'actions': ['Proactive support', 'Usage optimization', 'Value demonstration']
                })
        
        return recommendations
    
    def _calculate_clv_by_channel(self, date: datetime, period_days: int) -> Dict[str, float]:
        """Calculate CLV by acquisition channel"""
        # This would perform actual calculation
        # For now, return mock data
        return {
            'organic_search': 1800.0,
            'paid_advertising': 1200.0,
            'referral': 2400.0,
            'partnership': 1600.0
        }
    
    def _calculate_payback_period(self, cac: float, clv: float) -> float:
        """Calculate payback period in months"""
        if cac <= 0:
            return 0.0
        
        monthly_revenue = clv / 12  # Assuming 12-month customer lifespan
        if monthly_revenue <= 0:
            return float('inf')
        
        return cac / monthly_revenue
    
    def _calculate_channel_efficiency(self, channel: str, date: datetime) -> float:
        """Calculate channel efficiency score"""
        # This would perform actual calculation
        # For now, return mock data
        return 0.75
    
    def _identify_channel_optimization_opportunities(self, channel: str, ltv_cac_ratio: float) -> List[str]:
        """Identify optimization opportunities for a channel"""
        opportunities = []
        
        if ltv_cac_ratio < 1.0:
            opportunities.extend([
                'Reduce acquisition costs',
                'Improve conversion rates',
                'Optimize targeting',
                'Review ad spend allocation'
            ])
        elif ltv_cac_ratio < 3.0:
            opportunities.extend([
                'Scale successful campaigns',
                'Improve customer retention',
                'Increase average order value',
                'Optimize landing pages'
            ])
        else:
            opportunities.extend([
                'Increase budget allocation',
                'Expand to similar audiences',
                'Launch new campaigns',
                'Optimize for growth'
            ])
        
        return opportunities 
    
    def analyze_tier_upgrade_downgrade_patterns(self, date: datetime = None, period_days: int = 90) -> Dict[str, Any]:
        """Analyze tier upgrade and downgrade patterns"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define analysis period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get tier migration data
            migration_data = self._get_tier_migration_data(period_start, period_end)
            
            # Analyze upgrade patterns
            upgrade_patterns = self._analyze_upgrade_patterns(migration_data)
            
            # Analyze downgrade patterns
            downgrade_patterns = self._analyze_downgrade_patterns(migration_data)
            
            # Calculate conversion rates
            conversion_rates = self._calculate_tier_conversion_rates(migration_data)
            
            # Identify triggers and barriers
            triggers = self._identify_upgrade_triggers(migration_data)
            barriers = self._identify_downgrade_barriers(migration_data)
            
            return {
                'date': date.isoformat(),
                'period_days': period_days,
                'upgrade_patterns': upgrade_patterns,
                'downgrade_patterns': downgrade_patterns,
                'conversion_rates': conversion_rates,
                'upgrade_triggers': triggers,
                'downgrade_barriers': barriers,
                'recommendations': self._generate_tier_migration_recommendations(upgrade_patterns, downgrade_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing tier upgrade/downgrade patterns: {e}")
            return {}
    
    def analyze_payment_method_success_rates(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
        """Analyze payment method success rates"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define analysis period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get payment method data
            payment_data = self._get_payment_method_data(period_start, period_end)
            
            success_rates = {}
            
            for payment_method, data in payment_data.items():
                # Calculate success rate
                total_attempts = data['total_attempts']
                successful_attempts = data['successful_attempts']
                
                success_rate = 0.0
                if total_attempts > 0:
                    success_rate = (successful_attempts / total_attempts) * 100
                
                # Get previous period for comparison
                previous_start = period_start - timedelta(days=period_days)
                previous_end = period_start
                previous_data = self._get_payment_method_data(previous_start, previous_end)
                
                previous_success_rate = 0.0
                if payment_method in previous_data and previous_data[payment_method]['total_attempts'] > 0:
                    previous_success_rate = (previous_data[payment_method]['successful_attempts'] / previous_data[payment_method]['total_attempts']) * 100
                
                # Calculate change percentage
                change_percentage = None
                if previous_success_rate > 0:
                    change_percentage = ((success_rate - previous_success_rate) / previous_success_rate) * 100
                
                # Determine trend
                trend = None
                if change_percentage is not None:
                    if change_percentage > 5:
                        trend = "improving"
                    elif change_percentage > 0:
                        trend = "slight_improvement"
                    elif change_percentage > -5:
                        trend = "stable"
                    else:
                        trend = "declining"
                
                success_rates[payment_method] = MetricCalculation(
                    metric_type=MetricType.PAYMENT_SUCCESS_RATE,
                    value=success_rate,
                    previous_value=previous_success_rate,
                    change_percentage=change_percentage,
                    trend=trend,
                    metadata={
                        'payment_method': payment_method,
                        'date': date.isoformat(),
                        'period_days': period_days,
                        'total_attempts': total_attempts,
                        'successful_attempts': successful_attempts,
                        'failed_attempts': total_attempts - successful_attempts,
                        'failure_reasons': data.get('failure_reasons', {}),
                        'average_transaction_value': data.get('average_transaction_value', 0.0),
                        'retry_success_rate': data.get('retry_success_rate', 0.0),
                        'optimization_opportunities': self._identify_payment_optimization_opportunities(payment_method, success_rate, data)
                    }
                )
            
            return success_rates
            
        except Exception as e:
            logger.error(f"Error analyzing payment method success rates: {e}")
            return {}
    
    def analyze_geographic_revenue_distribution(self, date: datetime = None, period_days: int = 30) -> Dict[str, Any]:
        """Analyze geographic revenue distribution"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define analysis period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get geographic revenue data
            geo_data = self._get_geographic_revenue_data(period_start, period_end)
            
            # Calculate revenue by region
            revenue_by_region = {}
            total_revenue = 0.0
            
            for region, data in geo_data.items():
                region_revenue = data['total_revenue']
                total_revenue += region_revenue
                
                revenue_by_region[region] = {
                    'total_revenue': region_revenue,
                    'percentage_of_total': 0.0,
                    'customer_count': data['customer_count'],
                    'average_revenue_per_customer': region_revenue / data['customer_count'] if data['customer_count'] > 0 else 0.0,
                    'growth_rate': data.get('growth_rate', 0.0),
                    'churn_rate': data.get('churn_rate', 0.0),
                    'conversion_rate': data.get('conversion_rate', 0.0),
                    'top_plans': data.get('top_plans', []),
                    'payment_preferences': data.get('payment_preferences', {}),
                    'seasonal_patterns': data.get('seasonal_patterns', {})
                }
            
            # Calculate percentages
            for region in revenue_by_region:
                if total_revenue > 0:
                    revenue_by_region[region]['percentage_of_total'] = (revenue_by_region[region]['total_revenue'] / total_revenue) * 100
            
            # Get previous period for comparison
            previous_start = period_start - timedelta(days=period_days)
            previous_end = period_start
            previous_geo_data = self._get_geographic_revenue_data(previous_start, previous_end)
            
            # Calculate growth trends
            growth_trends = {}
            for region in revenue_by_region:
                previous_revenue = previous_geo_data.get(region, {}).get('total_revenue', 0.0)
                current_revenue = revenue_by_region[region]['total_revenue']
                
                growth_percentage = 0.0
                if previous_revenue > 0:
                    growth_percentage = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                growth_trends[region] = {
                    'growth_percentage': growth_percentage,
                    'trend': 'growing' if growth_percentage > 5 else 'stable' if growth_percentage > -5 else 'declining'
                }
            
            return {
                'date': date.isoformat(),
                'period_days': period_days,
                'total_revenue': total_revenue,
                'revenue_by_region': revenue_by_region,
                'growth_trends': growth_trends,
                'top_performing_regions': self._identify_top_performing_regions(revenue_by_region),
                'growth_opportunities': self._identify_geographic_growth_opportunities(revenue_by_region, growth_trends),
                'market_penetration': self._calculate_market_penetration_by_region(geo_data),
                'seasonal_analysis': self._analyze_geographic_seasonal_patterns(geo_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing geographic revenue distribution: {e}")
            return {}
    
    def analyze_user_engagement_correlation_with_retention(self, date: datetime = None, period_days: int = 90) -> Dict[str, Any]:
        """Analyze correlation between user engagement and retention"""
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # Define analysis period
            period_start = date - timedelta(days=period_days)
            period_end = date
            
            # Get user engagement and retention data
            engagement_data = self._get_user_engagement_data(period_start, period_end)
            retention_data = self._get_retention_data(period_start, period_end)
            
            # Calculate correlation coefficients
            correlations = self._calculate_engagement_retention_correlations(engagement_data, retention_data)
            
            # Analyze engagement patterns by retention cohort
            engagement_by_retention = self._analyze_engagement_by_retention_cohort(engagement_data, retention_data)
            
            # Identify engagement thresholds
            engagement_thresholds = self._identify_engagement_thresholds(engagement_data, retention_data)
            
            # Calculate predictive models
            predictive_models = self._build_engagement_retention_predictive_models(engagement_data, retention_data)
            
            # Generate engagement recommendations
            engagement_recommendations = self._generate_engagement_recommendations(correlations, engagement_thresholds)
            
            return {
                'date': date.isoformat(),
                'period_days': period_days,
                'correlations': correlations,
                'engagement_by_retention': engagement_by_retention,
                'engagement_thresholds': engagement_thresholds,
                'predictive_models': predictive_models,
                'recommendations': engagement_recommendations,
                'engagement_metrics': self._calculate_engagement_metrics(engagement_data),
                'retention_impact': self._calculate_retention_impact_of_engagement(engagement_data, retention_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user engagement correlation with retention: {e}")
            return {}
    
    def _get_tier_migration_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get tier migration data for analysis"""
        # This would query the actual database
        # For now, return mock data
        return {
            'upgrades': [
                {'from_tier': 'standard', 'to_tier': 'premium', 'count': 45, 'triggers': ['feature_usage', 'support_requests'], 'time_to_upgrade': 90},
                {'from_tier': 'premium', 'to_tier': 'enterprise', 'count': 12, 'triggers': ['team_growth', 'advanced_features'], 'time_to_upgrade': 180},
                {'from_tier': 'standard', 'to_tier': 'enterprise', 'count': 8, 'triggers': ['rapid_growth', 'enterprise_features'], 'time_to_upgrade': 120}
            ],
            'downgrades': [
                {'from_tier': 'premium', 'to_tier': 'standard', 'count': 15, 'barriers': ['pricing', 'feature_underuse'], 'time_to_downgrade': 60},
                {'from_tier': 'enterprise', 'to_tier': 'premium', 'count': 5, 'barriers': ['budget_cuts', 'team_reduction'], 'time_to_downgrade': 90},
                {'from_tier': 'enterprise', 'to_tier': 'standard', 'count': 3, 'barriers': ['business_closure', 'pricing'], 'time_to_downgrade': 30}
            ],
            'conversion_rates': {
                'standard_to_premium': 0.075,
                'premium_to_enterprise': 0.040,
                'standard_to_enterprise': 0.013,
                'premium_to_standard': 0.050,
                'enterprise_to_premium': 0.017,
                'enterprise_to_standard': 0.010
            }
        }
    
    def _analyze_upgrade_patterns(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze upgrade patterns"""
        upgrades = migration_data.get('upgrades', [])
        
        patterns = {
            'total_upgrades': sum(upgrade['count'] for upgrade in upgrades),
            'upgrade_paths': {},
            'common_triggers': {},
            'average_time_to_upgrade': 0.0,
            'upgrade_velocity': {}
        }
        
        # Analyze upgrade paths
        for upgrade in upgrades:
            path = f"{upgrade['from_tier']}_to_{upgrade['to_tier']}"
            patterns['upgrade_paths'][path] = {
                'count': upgrade['count'],
                'triggers': upgrade['triggers'],
                'time_to_upgrade': upgrade['time_to_upgrade']
            }
        
        # Analyze common triggers
        all_triggers = []
        for upgrade in upgrades:
            all_triggers.extend(upgrade['triggers'])
        
        from collections import Counter
        trigger_counts = Counter(all_triggers)
        patterns['common_triggers'] = dict(trigger_counts)
        
        # Calculate average time to upgrade
        total_time = sum(upgrade['time_to_upgrade'] for upgrade in upgrades)
        total_count = sum(upgrade['count'] for upgrade in upgrades)
        patterns['average_time_to_upgrade'] = total_time / total_count if total_count > 0 else 0
        
        return patterns
    
    def _analyze_downgrade_patterns(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze downgrade patterns"""
        downgrades = migration_data.get('downgrades', [])
        
        patterns = {
            'total_downgrades': sum(downgrade['count'] for downgrade in downgrades),
            'downgrade_paths': {},
            'common_barriers': {},
            'average_time_to_downgrade': 0.0,
            'downgrade_velocity': {}
        }
        
        # Analyze downgrade paths
        for downgrade in downgrades:
            path = f"{downgrade['from_tier']}_to_{downgrade['to_tier']}"
            patterns['downgrade_paths'][path] = {
                'count': downgrade['count'],
                'barriers': downgrade['barriers'],
                'time_to_downgrade': downgrade['time_to_downgrade']
            }
        
        # Analyze common barriers
        all_barriers = []
        for downgrade in downgrades:
            all_barriers.extend(downgrade['barriers'])
        
        from collections import Counter
        barrier_counts = Counter(all_barriers)
        patterns['common_barriers'] = dict(barrier_counts)
        
        # Calculate average time to downgrade
        total_time = sum(downgrade['time_to_downgrade'] for downgrade in downgrades)
        total_count = sum(downgrade['count'] for downgrade in downgrades)
        patterns['average_time_to_downgrade'] = total_time / total_count if total_count > 0 else 0
        
        return patterns
    
    def _calculate_tier_conversion_rates(self, migration_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate tier conversion rates"""
        return migration_data.get('conversion_rates', {})
    
    def _identify_upgrade_triggers(self, migration_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify upgrade triggers"""
        triggers = []
        
        # Analyze feature usage triggers
        triggers.append({
            'type': 'feature_usage',
            'description': 'High usage of premium features',
            'impact': 'high',
            'recommendation': 'Promote premium features to standard users',
            'success_rate': 0.75
        })
        
        # Analyze support request triggers
        triggers.append({
            'type': 'support_requests',
            'description': 'Multiple support requests indicating need for better support',
            'impact': 'medium',
            'recommendation': 'Offer premium support to active users',
            'success_rate': 0.60
        })
        
        # Analyze team growth triggers
        triggers.append({
            'type': 'team_growth',
            'description': 'Increase in team size requiring more seats',
            'impact': 'high',
            'recommendation': 'Monitor team size changes and offer upgrades',
            'success_rate': 0.85
        })
        
        return triggers
    
    def _identify_downgrade_barriers(self, migration_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify downgrade barriers"""
        barriers = []
        
        # Analyze pricing barriers
        barriers.append({
            'type': 'pricing',
            'description': 'Price sensitivity and budget constraints',
            'impact': 'high',
            'recommendation': 'Offer flexible pricing options and payment plans',
            'prevention_rate': 0.70
        })
        
        # Analyze feature underuse barriers
        barriers.append({
            'type': 'feature_underuse',
            'description': 'Low utilization of premium features',
            'impact': 'medium',
            'recommendation': 'Improve feature education and onboarding',
            'prevention_rate': 0.65
        })
        
        # Analyze business changes barriers
        barriers.append({
            'type': 'business_changes',
            'description': 'Business downsizing or closure',
            'impact': 'low',
            'recommendation': 'Offer flexible contracts and data export options',
            'prevention_rate': 0.30
        })
        
        return barriers
    
    def _generate_tier_migration_recommendations(self, upgrade_patterns: Dict[str, Any], downgrade_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tier migration recommendations"""
        recommendations = []
        
        # Upgrade recommendations
        if upgrade_patterns['total_upgrades'] > 0:
            recommendations.append({
                'type': 'upgrade_optimization',
                'priority': 'high',
                'title': 'Optimize Upgrade Funnel',
                'description': f'Focus on {upgrade_patterns["total_upgrades"]} potential upgrades',
                'actions': [
                    'Implement upgrade triggers based on usage patterns',
                    'Create targeted upgrade campaigns',
                    'Offer upgrade incentives and trials'
                ]
            })
        
        # Downgrade prevention recommendations
        if downgrade_patterns['total_downgrades'] > 0:
            recommendations.append({
                'type': 'downgrade_prevention',
                'priority': 'high',
                'title': 'Prevent Downgrades',
                'description': f'Prevent {downgrade_patterns["total_downgrades"]} potential downgrades',
                'actions': [
                    'Address common downgrade barriers',
                    'Improve feature adoption and education',
                    'Offer flexible pricing options'
                ]
            })
        
        return recommendations
    
    def _get_payment_method_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Any]]:
        """Get payment method data for analysis"""
        # This would query the actual database
        # For now, return mock data
        return {
            'credit_card': {
                'total_attempts': 1500,
                'successful_attempts': 1425,
                'failure_reasons': {
                    'insufficient_funds': 45,
                    'expired_card': 15,
                    'invalid_card': 10,
                    'fraud_detection': 5
                },
                'average_transaction_value': 125.0,
                'retry_success_rate': 0.75
            },
            'debit_card': {
                'total_attempts': 800,
                'successful_attempts': 760,
                'failure_reasons': {
                    'insufficient_funds': 30,
                    'daily_limit': 8,
                    'invalid_card': 2
                },
                'average_transaction_value': 85.0,
                'retry_success_rate': 0.60
            },
            'bank_transfer': {
                'total_attempts': 300,
                'successful_attempts': 285,
                'failure_reasons': {
                    'invalid_account': 10,
                    'bank_error': 3,
                    'insufficient_funds': 2
                },
                'average_transaction_value': 200.0,
                'retry_success_rate': 0.90
            },
            'digital_wallet': {
                'total_attempts': 600,
                'successful_attempts': 570,
                'failure_reasons': {
                    'insufficient_balance': 20,
                    'account_locked': 8,
                    'network_error': 2
                },
                'average_transaction_value': 95.0,
                'retry_success_rate': 0.80
            }
        }
    
    def _identify_payment_optimization_opportunities(self, payment_method: str, success_rate: float, data: Dict[str, Any]) -> List[str]:
        """Identify payment optimization opportunities"""
        opportunities = []
        
        if success_rate < 90:
            opportunities.append('Improve fraud detection accuracy')
            opportunities.append('Enhance error handling and retry logic')
            opportunities.append('Optimize payment flow and user experience')
        
        if data.get('retry_success_rate', 0) < 0.8:
            opportunities.append('Implement smart retry strategies')
            opportunities.append('Improve failure reason detection')
        
        if payment_method == 'credit_card' and success_rate < 95:
            opportunities.append('Implement card validation before processing')
            opportunities.append('Offer card update reminders')
        
        if payment_method == 'digital_wallet' and success_rate < 95:
            opportunities.append('Improve wallet integration')
            opportunities.append('Enhance mobile payment experience')
        
        return opportunities
    
    def _get_geographic_revenue_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Any]]:
        """Get geographic revenue data for analysis"""
        # This would query the actual database
        # For now, return mock data
        return {
            'North America': {
                'total_revenue': 45000.0,
                'customer_count': 450,
                'growth_rate': 12.5,
                'churn_rate': 4.2,
                'conversion_rate': 3.8,
                'top_plans': ['premium', 'enterprise', 'standard'],
                'payment_preferences': {
                    'credit_card': 0.65,
                    'debit_card': 0.20,
                    'digital_wallet': 0.10,
                    'bank_transfer': 0.05
                },
                'seasonal_patterns': {
                    'Q1': 0.22,
                    'Q2': 0.25,
                    'Q3': 0.28,
                    'Q4': 0.25
                }
            },
            'Europe': {
                'total_revenue': 32000.0,
                'customer_count': 320,
                'growth_rate': 8.7,
                'churn_rate': 3.8,
                'conversion_rate': 4.2,
                'top_plans': ['premium', 'standard', 'enterprise'],
                'payment_preferences': {
                    'bank_transfer': 0.45,
                    'credit_card': 0.35,
                    'debit_card': 0.15,
                    'digital_wallet': 0.05
                },
                'seasonal_patterns': {
                    'Q1': 0.20,
                    'Q2': 0.25,
                    'Q3': 0.30,
                    'Q4': 0.25
                }
            },
            'Asia Pacific': {
                'total_revenue': 28000.0,
                'customer_count': 280,
                'growth_rate': 18.3,
                'churn_rate': 5.1,
                'conversion_rate': 5.5,
                'top_plans': ['standard', 'premium', 'enterprise'],
                'payment_preferences': {
                    'digital_wallet': 0.60,
                    'credit_card': 0.25,
                    'bank_transfer': 0.10,
                    'debit_card': 0.05
                },
                'seasonal_patterns': {
                    'Q1': 0.18,
                    'Q2': 0.22,
                    'Q3': 0.30,
                    'Q4': 0.30
                }
            },
            'Latin America': {
                'total_revenue': 15000.0,
                'customer_count': 150,
                'growth_rate': 22.1,
                'churn_rate': 6.8,
                'conversion_rate': 6.2,
                'top_plans': ['standard', 'premium'],
                'payment_preferences': {
                    'credit_card': 0.70,
                    'digital_wallet': 0.20,
                    'bank_transfer': 0.08,
                    'debit_card': 0.02
                },
                'seasonal_patterns': {
                    'Q1': 0.20,
                    'Q2': 0.25,
                    'Q3': 0.30,
                    'Q4': 0.25
                }
            }
        }
    
    def _identify_top_performing_regions(self, revenue_by_region: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify top performing regions"""
        # Sort regions by revenue
        sorted_regions = sorted(
            revenue_by_region.items(),
            key=lambda x: x[1]['total_revenue'],
            reverse=True
        )
        
        top_performers = []
        for region, data in sorted_regions[:3]:  # Top 3 regions
            top_performers.append({
                'region': region,
                'total_revenue': data['total_revenue'],
                'percentage_of_total': data['percentage_of_total'],
                'growth_rate': data['growth_rate'],
                'customer_count': data['customer_count'],
                'average_revenue_per_customer': data['average_revenue_per_customer']
            })
        
        return top_performers
    
    def _identify_geographic_growth_opportunities(self, revenue_by_region: Dict[str, Dict[str, Any]], growth_trends: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify geographic growth opportunities"""
        opportunities = []
        
        for region, data in revenue_by_region.items():
            growth_trend = growth_trends.get(region, {})
            
            if growth_trend.get('trend') == 'growing' and data['growth_rate'] > 15:
                opportunities.append({
                    'region': region,
                    'type': 'scale',
                    'description': f'High growth region with {data["growth_rate"]:.1f}% growth rate',
                    'recommendation': 'Increase marketing spend and expand operations',
                    'potential_impact': 'high'
                })
            elif growth_trend.get('trend') == 'declining':
                opportunities.append({
                    'region': region,
                    'type': 'recovery',
                    'description': f'Declining region with {data["churn_rate"]:.1f}% churn rate',
                    'recommendation': 'Implement retention strategies and market analysis',
                    'potential_impact': 'medium'
                })
            elif data['conversion_rate'] < 4.0:
                opportunities.append({
                    'region': region,
                    'type': 'conversion',
                    'description': f'Low conversion rate of {data["conversion_rate"]:.1f}%',
                    'recommendation': 'Optimize conversion funnel and localize marketing',
                    'potential_impact': 'medium'
                })
        
        return opportunities
    
    def _calculate_market_penetration_by_region(self, geo_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate market penetration by region"""
        # This would use actual market size data
        # For now, return mock data
        return {
            'North America': 0.15,
            'Europe': 0.08,
            'Asia Pacific': 0.05,
            'Latin America': 0.03
        }
    
    def _analyze_geographic_seasonal_patterns(self, geo_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Analyze geographic seasonal patterns"""
        seasonal_analysis = {}
        
        for region, data in geo_data.items():
            seasonal_patterns = data.get('seasonal_patterns', {})
            seasonal_analysis[region] = {
                'peak_quarter': max(seasonal_patterns.items(), key=lambda x: x[1])[0],
                'low_quarter': min(seasonal_patterns.items(), key=lambda x: x[1])[0],
                'seasonality_strength': max(seasonal_patterns.values()) - min(seasonal_patterns.values()),
                'quarterly_distribution': seasonal_patterns
            }
        
        return seasonal_analysis
    
    def _get_user_engagement_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user engagement data for analysis"""
        # This would query the actual database
        # For now, return mock data
        return {
            'engagement_metrics': {
                'daily_active_users': 850,
                'weekly_active_users': 1200,
                'monthly_active_users': 1500,
                'average_session_duration': 45,
                'sessions_per_user': 12.5,
                'feature_adoption_rate': 0.68,
                'time_to_first_value': 3.2
            },
            'engagement_by_cohort': {
                'high_engagement': {
                    'user_count': 300,
                    'retention_rate': 0.92,
                    'avg_sessions_per_month': 25,
                    'avg_session_duration': 60,
                    'feature_adoption_rate': 0.85
                },
                'medium_engagement': {
                    'user_count': 600,
                    'retention_rate': 0.78,
                    'avg_sessions_per_month': 15,
                    'avg_session_duration': 35,
                    'feature_adoption_rate': 0.65
                },
                'low_engagement': {
                    'user_count': 600,
                    'retention_rate': 0.45,
                    'avg_sessions_per_month': 5,
                    'avg_session_duration': 15,
                    'feature_adoption_rate': 0.35
                }
            },
            'engagement_trends': {
                'sessions_per_user': [10, 11, 12, 12.5, 13, 12.5],
                'session_duration': [40, 42, 44, 45, 46, 45],
                'feature_adoption': [0.60, 0.62, 0.65, 0.68, 0.70, 0.68]
            }
        }
    
    def _get_retention_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get retention data for analysis"""
        # This would query the actual database
        # For now, return mock data
        return {
            'overall_retention_rate': 0.75,
            'retention_by_cohort': {
                'high_engagement': 0.92,
                'medium_engagement': 0.78,
                'low_engagement': 0.45
            },
            'retention_trends': {
                'month_1': 0.85,
                'month_2': 0.78,
                'month_3': 0.72,
                'month_6': 0.68,
                'month_12': 0.65
            },
            'churn_indicators': {
                'low_activity': 0.65,
                'support_issues': 0.45,
                'pricing_complaints': 0.35,
                'feature_requests': 0.25
            }
        }
    
    def _calculate_engagement_retention_correlations(self, engagement_data: Dict[str, Any], retention_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate correlation between engagement and retention"""
        # This would perform actual statistical correlation analysis
        # For now, return mock correlations
        return {
            'sessions_per_user': 0.78,
            'session_duration': 0.72,
            'feature_adoption_rate': 0.85,
            'daily_active_users': 0.68,
            'time_to_first_value': -0.45  # Negative correlation (faster = better)
        }
    
    def _analyze_engagement_by_retention_cohort(self, engagement_data: Dict[str, Any], retention_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze engagement patterns by retention cohort"""
        engagement_by_cohort = engagement_data.get('engagement_by_cohort', {})
        retention_by_cohort = retention_data.get('retention_by_cohort', {})
        
        analysis = {}
        for cohort in engagement_by_cohort:
            engagement = engagement_by_cohort[cohort]
            retention = retention_by_cohort.get(cohort, 0.0)
            
            analysis[cohort] = {
                'user_count': engagement['user_count'],
                'retention_rate': retention,
                'avg_sessions_per_month': engagement['avg_sessions_per_month'],
                'avg_session_duration': engagement['avg_session_duration'],
                'feature_adoption_rate': engagement['feature_adoption_rate'],
                'engagement_score': self._calculate_engagement_score(engagement),
                'retention_impact': self._calculate_retention_impact(engagement, retention)
            }
        
        return analysis
    
    def _identify_engagement_thresholds(self, engagement_data: Dict[str, Any], retention_data: Dict[str, Any]) -> Dict[str, float]:
        """Identify engagement thresholds for retention"""
        # This would use statistical analysis to find optimal thresholds
        # For now, return mock thresholds
        return {
            'minimum_sessions_per_month': 8.0,
            'minimum_session_duration': 25.0,
            'minimum_feature_adoption': 0.50,
            'optimal_sessions_per_month': 15.0,
            'optimal_session_duration': 40.0,
            'optimal_feature_adoption': 0.70
        }
    
    def _build_engagement_retention_predictive_models(self, engagement_data: Dict[str, Any], retention_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build predictive models for engagement and retention"""
        # This would build actual machine learning models
        # For now, return mock model information
        return {
            'retention_prediction_model': {
                'accuracy': 0.82,
                'features': ['sessions_per_month', 'session_duration', 'feature_adoption', 'support_interactions'],
                'prediction_horizon': '30_days',
                'model_type': 'random_forest'
            },
            'engagement_prediction_model': {
                'accuracy': 0.78,
                'features': ['previous_engagement', 'feature_usage', 'onboarding_completion'],
                'prediction_horizon': '7_days',
                'model_type': 'gradient_boosting'
            }
        }
    
    def _generate_engagement_recommendations(self, correlations: Dict[str, float], thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate engagement recommendations based on correlations and thresholds"""
        recommendations = []
        
        # High correlation recommendations
        if correlations.get('feature_adoption_rate', 0) > 0.8:
            recommendations.append({
                'type': 'feature_adoption',
                'priority': 'high',
                'title': 'Improve Feature Adoption',
                'description': 'Feature adoption has strong correlation with retention',
                'target_threshold': thresholds.get('optimal_feature_adoption', 0.70),
                'actions': [
                    'Implement feature onboarding tours',
                    'Create feature usage incentives',
                    'Send targeted feature education emails'
                ]
            })
        
        if correlations.get('sessions_per_user', 0) > 0.7:
            recommendations.append({
                'type': 'session_frequency',
                'priority': 'medium',
                'title': 'Increase Session Frequency',
                'description': 'Session frequency correlates strongly with retention',
                'target_threshold': thresholds.get('optimal_sessions_per_month', 15.0),
                'actions': [
                    'Implement engagement notifications',
                    'Create daily/weekly usage reminders',
                    'Offer session-based rewards'
                ]
            })
        
        if correlations.get('session_duration', 0) > 0.7:
            recommendations.append({
                'type': 'session_duration',
                'priority': 'medium',
                'title': 'Improve Session Duration',
                'description': 'Session duration correlates with retention',
                'target_threshold': thresholds.get('optimal_session_duration', 40.0),
                'actions': [
                    'Optimize user experience and flow',
                    'Reduce friction in key workflows',
                    'Implement progressive disclosure'
                ]
            })
        
        return recommendations
    
    def _calculate_engagement_metrics(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive engagement metrics"""
        metrics = engagement_data.get('engagement_metrics', {})
        trends = engagement_data.get('engagement_trends', {})
        
        return {
            'current_metrics': metrics,
            'trend_analysis': {
                'sessions_trend': 'increasing' if trends.get('sessions_per_user', [0])[-1] > trends.get('sessions_per_user', [0])[0] else 'decreasing',
                'duration_trend': 'increasing' if trends.get('session_duration', [0])[-1] > trends.get('session_duration', [0])[0] else 'decreasing',
                'adoption_trend': 'increasing' if trends.get('feature_adoption', [0])[-1] > trends.get('feature_adoption', [0])[0] else 'decreasing'
            },
            'engagement_score': self._calculate_overall_engagement_score(metrics),
            'engagement_segments': self._segment_users_by_engagement(engagement_data)
        }
    
    def _calculate_retention_impact_of_engagement(self, engagement_data: Dict[str, Any], retention_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the impact of engagement on retention"""
        engagement_by_cohort = engagement_data.get('engagement_by_cohort', {})
        retention_by_cohort = retention_data.get('retention_by_cohort', {})
        
        impact_analysis = {}
        for cohort in engagement_by_cohort:
            engagement = engagement_by_cohort[cohort]
            retention = retention_by_cohort.get(cohort, 0.0)
            
            impact_analysis[cohort] = {
                'retention_rate': retention,
                'engagement_level': engagement['avg_sessions_per_month'],
                'retention_impact': retention - retention_data.get('overall_retention_rate', 0.75),
                'improvement_potential': self._calculate_improvement_potential(engagement, retention)
            }
        
        return impact_analysis
    
    def _calculate_engagement_score(self, engagement: Dict[str, Any]) -> float:
        """Calculate engagement score for a cohort"""
        # Weighted combination of engagement metrics
        sessions_weight = 0.4
        duration_weight = 0.3
        adoption_weight = 0.3
        
        sessions_score = min(engagement['avg_sessions_per_month'] / 20.0, 1.0)  # Normalize to 0-1
        duration_score = min(engagement['avg_session_duration'] / 60.0, 1.0)  # Normalize to 0-1
        adoption_score = engagement['feature_adoption_rate']
        
        return (sessions_score * sessions_weight + 
                duration_score * duration_weight + 
                adoption_score * adoption_weight)
    
    def _calculate_retention_impact(self, engagement: Dict[str, Any], retention: float) -> float:
        """Calculate retention impact of engagement"""
        baseline_retention = 0.75  # Overall retention rate
        return retention - baseline_retention
    
    def _calculate_overall_engagement_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall engagement score"""
        # This would be a more sophisticated calculation
        # For now, return a simple average
        return 0.72
    
    def _segment_users_by_engagement(self, engagement_data: Dict[str, Any]) -> Dict[str, int]:
        """Segment users by engagement level"""
        engagement_by_cohort = engagement_data.get('engagement_by_cohort', {})
        
        segments = {}
        for cohort, data in engagement_by_cohort.items():
            segments[cohort] = data['user_count']
        
        return segments
    
    def _calculate_improvement_potential(self, engagement: Dict[str, Any], retention: float) -> float:
        """Calculate improvement potential for engagement"""
        # This would be a more sophisticated calculation
        # For now, return a simple estimate
        return 0.15