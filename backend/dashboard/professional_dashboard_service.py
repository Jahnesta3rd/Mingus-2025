"""
Professional Tier Dashboard Service

This module provides comprehensive dashboard features for Professional tier subscribers,
including real-time account balances, advanced cash flow analysis, detailed spending analysis,
and bill prediction with payment optimization.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from collections import defaultdict, Counter
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, case, cast, Float
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidAccount, PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.models.subscription import SubscriptionTier
from backend.services.feature_access_service import FeatureAccessService
from backend.banking.financial_analyzer import FinancialAnalyzer
from backend.services.cash_flow_analysis_service import CashFlowAnalysisService
from backend.services.payment_optimization_service import PaymentOptimizationService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class DashboardWidgetType(Enum):
    """Dashboard widget types for Professional tier"""
    ACCOUNT_BALANCES = "account_balances"
    CASH_FLOW_ANALYSIS = "cash_flow_analysis"
    SPENDING_ANALYSIS = "spending_analysis"
    BILL_PREDICTION = "bill_prediction"
    PAYMENT_OPTIMIZATION = "payment_optimization"
    FINANCIAL_FORECAST = "financial_forecast"
    INVESTMENT_OVERVIEW = "investment_overview"
    DEBT_MANAGEMENT = "debt_management"


@dataclass
class AccountBalanceData:
    """Real-time account balance data"""
    account_id: str
    account_name: str
    account_type: str
    institution_name: str
    current_balance: float
    available_balance: float
    last_updated: datetime
    balance_change_24h: float
    balance_change_7d: float
    balance_change_30d: float
    account_status: str
    is_primary: bool
    account_number_masked: str
    routing_number_masked: str


@dataclass
class CashFlowProjection:
    """12-month cash flow projection data"""
    month: str
    projected_income: float
    projected_expenses: float
    projected_net_flow: float
    confidence_level: float
    risk_factors: List[str]
    seasonal_adjustments: Dict[str, float]
    growth_rate: float
    volatility_score: float


@dataclass
class SpendingAnalysisData:
    """Detailed spending analysis data"""
    category_id: str
    category_name: str
    total_spent: float
    average_spent: float
    transaction_count: int
    spending_trend: str
    trend_percentage: float
    budget_variance: float
    custom_rules: List[Dict[str, Any]]
    merchant_analysis: Dict[str, Any]
    seasonal_patterns: Dict[str, float]
    recommendations: List[str]


@dataclass
class BillPredictionData:
    """Bill prediction and payment optimization data"""
    bill_id: str
    bill_name: str
    due_date: date
    amount: float
    category: str
    merchant: str
    payment_method: str
    auto_pay_enabled: bool
    predicted_payment_date: date
    optimization_score: float
    payment_strategy: str
    savings_opportunity: float
    risk_level: str
    alternative_payment_methods: List[Dict[str, Any]]


class ProfessionalDashboardService:
    """Professional tier dashboard service with advanced features"""
    
    def __init__(self, db_session: Session, feature_access_service: FeatureAccessService):
        self.db = db_session
        self.feature_service = feature_access_service
        self.financial_analyzer = FinancialAnalyzer(db_session)
        self.cash_flow_service = CashFlowAnalysisService(db_session)
        self.payment_optimizer = PaymentOptimizationService(db_session)
        
        # Cache for real-time data
        self.balance_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_professional_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive Professional tier dashboard data
        
        Args:
            user_id: User ID to get dashboard data for
            
        Returns:
            Complete Professional dashboard data
        """
        try:
            # Verify Professional tier access
            if not self._verify_professional_access(user_id):
                return self._get_upgrade_prompt_data()
            
            # Get all dashboard components
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'tier': 'professional',
                'account_balances': self._get_real_time_account_balances(user_id),
                'cash_flow_analysis': self._get_advanced_cash_flow_analysis(user_id),
                'spending_analysis': self._get_detailed_spending_analysis(user_id),
                'bill_prediction': self._get_bill_prediction_data(user_id),
                'payment_optimization': self._get_payment_optimization_data(user_id),
                'financial_forecast': self._get_financial_forecast_data(user_id),
                'investment_overview': self._get_investment_overview_data(user_id),
                'debt_management': self._get_debt_management_data(user_id),
                'alerts': self._get_dashboard_alerts(user_id),
                'insights': self._get_ai_insights(user_id),
                'widgets': self._get_custom_widgets(user_id)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating Professional dashboard for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _verify_professional_access(self, user_id: str) -> bool:
        """Verify user has Professional tier access"""
        try:
            # Check subscription tier
            subscription = self.db.query(SubscriptionTier).filter(
                SubscriptionTier.user_id == user_id,
                SubscriptionTier.status == 'active'
            ).first()
            
            if not subscription:
                return False
            
            # Check if Professional tier features are available
            return self.feature_service.can_access_feature(
                user_id, 'professional_dashboard'
            )
            
        except Exception as e:
            logger.error(f"Error verifying Professional access for user {user_id}: {e}")
            return False
    
    def _get_upgrade_prompt_data(self) -> Dict[str, Any]:
        """Get upgrade prompt data for non-Professional users"""
        return {
            'requires_upgrade': True,
            'current_tier': 'mid_tier',
            'upgrade_tier': 'professional',
            'upgrade_price': 75.00,
            'upgrade_features': [
                'Real-time account balances across all linked accounts',
                'Advanced cash flow analysis with 12-month projections',
                'Detailed spending analysis with custom categories',
                'Bill prediction and payment optimization',
                'Unlimited AI insights and analytics',
                'Dedicated account manager',
                'Priority support'
            ],
            'upgrade_url': '/api/subscription/upgrade/professional'
        }
    
    def _get_real_time_account_balances(self, user_id: str) -> Dict[str, Any]:
        """Get real-time account balances across all linked accounts"""
        try:
            # Get all linked accounts
            accounts = self.db.query(PlaidAccount).filter(
                PlaidAccount.user_id == user_id,
                PlaidAccount.status == 'active'
            ).all()
            
            account_balances = []
            total_balance = 0.0
            total_available = 0.0
            
            for account in accounts:
                # Get latest balance data
                balance_data = self._get_account_balance_data(account)
                
                if balance_data:
                    account_balances.append(balance_data)
                    total_balance += balance_data.current_balance
                    total_available += balance_data.available_balance
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(account_balances)
            
            return {
                'accounts': [self._serialize_account_balance(ab) for ab in account_balances],
                'total_balance': total_balance,
                'total_available': total_available,
                'account_count': len(account_balances),
                'portfolio_metrics': portfolio_metrics,
                'last_updated': datetime.utcnow().isoformat(),
                'refresh_interval': 300  # 5 minutes
            }
            
        except Exception as e:
            logger.error(f"Error getting account balances for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_account_balance_data(self, account: PlaidAccount) -> Optional[AccountBalanceData]:
        """Get real-time balance data for a specific account"""
        try:
            # Get latest transaction for balance calculation
            latest_transaction = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account.account_id
            ).order_by(PlaidTransaction.date.desc()).first()
            
            if not latest_transaction:
                return None
            
            # Calculate balance changes
            balance_changes = self._calculate_balance_changes(account.account_id)
            
            return AccountBalanceData(
                account_id=account.account_id,
                account_name=account.name,
                account_type=account.type,
                institution_name=account.institution_name,
                current_balance=account.current_balance or 0.0,
                available_balance=account.available_balance or 0.0,
                last_updated=account.last_updated or datetime.utcnow(),
                balance_change_24h=balance_changes.get('24h', 0.0),
                balance_change_7d=balance_changes.get('7d', 0.0),
                balance_change_30d=balance_changes.get('30d', 0.0),
                account_status=account.status,
                is_primary=account.is_primary or False,
                account_number_masked=self._mask_account_number(account.account_number),
                routing_number_masked=self._mask_routing_number(account.routing_number)
            )
            
        except Exception as e:
            logger.error(f"Error getting balance data for account {account.account_id}: {e}")
            return None
    
    def _calculate_balance_changes(self, account_id: str) -> Dict[str, float]:
        """Calculate balance changes over different time periods"""
        try:
            now = datetime.utcnow()
            
            # Get transactions for different periods
            periods = {
                '24h': now - timedelta(days=1),
                '7d': now - timedelta(days=7),
                '30d': now - timedelta(days=30)
            }
            
            changes = {}
            for period, start_date in periods.items():
                transactions = self.db.query(PlaidTransaction).filter(
                    PlaidTransaction.account_id == account_id,
                    PlaidTransaction.date >= start_date
                ).all()
                
                total_change = sum(t.amount for t in transactions)
                changes[period] = total_change
            
            return changes
            
        except Exception as e:
            logger.error(f"Error calculating balance changes for account {account_id}: {e}")
            return {'24h': 0.0, '7d': 0.0, '30d': 0.0}
    
    def _get_advanced_cash_flow_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get advanced cash flow analysis with 12-month projections"""
        try:
            # Get 12-month cash flow projections
            projections = []
            current_date = datetime.utcnow()
            
            for i in range(12):
                projection_date = current_date + timedelta(days=30*i)
                month_key = projection_date.strftime('%Y-%m')
                
                projection = self._calculate_monthly_projection(user_id, projection_date)
                projections.append(projection)
            
            # Calculate cash flow metrics
            cash_flow_metrics = self._calculate_cash_flow_metrics(projections)
            
            # Generate cash flow insights
            insights = self._generate_cash_flow_insights(projections)
            
            return {
                'projections': [self._serialize_cash_flow_projection(p) for p in projections],
                'metrics': cash_flow_metrics,
                'insights': insights,
                'risk_assessment': self._assess_cash_flow_risk(projections),
                'optimization_opportunities': self._identify_cash_flow_opportunities(projections),
                'seasonal_patterns': self._analyze_seasonal_patterns(projections),
                'forecast_accuracy': self._calculate_forecast_accuracy(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting cash flow analysis for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _calculate_monthly_projection(self, user_id: str, projection_date: datetime) -> CashFlowProjection:
        """Calculate monthly cash flow projection"""
        try:
            # Get historical data for projection
            historical_data = self._get_historical_cash_flow_data(user_id, projection_date)
            
            # Calculate projected income
            projected_income = self._project_income(historical_data, projection_date)
            
            # Calculate projected expenses
            projected_expenses = self._project_expenses(historical_data, projection_date)
            
            # Calculate net flow
            projected_net_flow = projected_income - projected_expenses
            
            # Calculate confidence level
            confidence_level = self._calculate_projection_confidence(historical_data)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(historical_data, projection_date)
            
            # Calculate seasonal adjustments
            seasonal_adjustments = self._calculate_seasonal_adjustments(historical_data, projection_date)
            
            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(historical_data)
            
            # Calculate volatility score
            volatility_score = self._calculate_volatility_score(historical_data)
            
            return CashFlowProjection(
                month=projection_date.strftime('%Y-%m'),
                projected_income=projected_income,
                projected_expenses=projected_expenses,
                projected_net_flow=projected_net_flow,
                confidence_level=confidence_level,
                risk_factors=risk_factors,
                seasonal_adjustments=seasonal_adjustments,
                growth_rate=growth_rate,
                volatility_score=volatility_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating monthly projection for user {user_id}: {e}")
            return CashFlowProjection(
                month=projection_date.strftime('%Y-%m'),
                projected_income=0.0,
                projected_expenses=0.0,
                projected_net_flow=0.0,
                confidence_level=0.0,
                risk_factors=[],
                seasonal_adjustments={},
                growth_rate=0.0,
                volatility_score=0.0
            )
    
    def _get_detailed_spending_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get detailed spending analysis with custom categories"""
        try:
            # Get spending data by category
            spending_data = self._get_spending_by_category(user_id)
            
            # Get custom categories
            custom_categories = self._get_custom_categories(user_id)
            
            # Analyze spending patterns
            spending_patterns = self._analyze_spending_patterns(user_id)
            
            # Get merchant analysis
            merchant_analysis = self._analyze_merchant_spending(user_id)
            
            # Get seasonal patterns
            seasonal_patterns = self._analyze_seasonal_spending(user_id)
            
            # Generate spending insights
            insights = self._generate_spending_insights(spending_data, spending_patterns)
            
            return {
                'spending_by_category': [self._serialize_spending_analysis(s) for s in spending_data],
                'custom_categories': custom_categories,
                'spending_patterns': spending_patterns,
                'merchant_analysis': merchant_analysis,
                'seasonal_patterns': seasonal_patterns,
                'insights': insights,
                'recommendations': self._generate_spending_recommendations(spending_data),
                'budget_variance': self._calculate_budget_variance(user_id),
                'spending_trends': self._analyze_spending_trends(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting spending analysis for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_bill_prediction_data(self, user_id: str) -> Dict[str, Any]:
        """Get bill prediction and payment optimization data"""
        try:
            # Get upcoming bills
            upcoming_bills = self._get_upcoming_bills(user_id)
            
            # Predict payment dates
            predicted_bills = []
            for bill in upcoming_bills:
                prediction = self._predict_bill_payment(bill)
                predicted_bills.append(prediction)
            
            # Optimize payment strategies
            optimized_bills = []
            for bill in predicted_bills:
                optimization = self._optimize_bill_payment(bill)
                optimized_bills.append(optimization)
            
            # Calculate payment metrics
            payment_metrics = self._calculate_payment_metrics(optimized_bills)
            
            return {
                'upcoming_bills': [self._serialize_bill_prediction(b) for b in predicted_bills],
                'optimized_payments': [self._serialize_bill_prediction(b) for b in optimized_bills],
                'payment_metrics': payment_metrics,
                'savings_opportunities': self._calculate_savings_opportunities(optimized_bills),
                'payment_strategies': self._generate_payment_strategies(optimized_bills),
                'risk_assessment': self._assess_payment_risk(optimized_bills),
                'auto_pay_recommendations': self._generate_auto_pay_recommendations(optimized_bills)
            }
            
        except Exception as e:
            logger.error(f"Error getting bill prediction data for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_payment_optimization_data(self, user_id: str) -> Dict[str, Any]:
        """Get payment optimization recommendations"""
        try:
            # Get payment optimization data from service
            optimization_data = self.payment_optimizer.get_optimization_data(user_id)
            
            return {
                'optimization_score': optimization_data.get('score', 0.0),
                'recommendations': optimization_data.get('recommendations', []),
                'savings_potential': optimization_data.get('savings_potential', 0.0),
                'payment_schedule': optimization_data.get('payment_schedule', []),
                'debt_optimization': optimization_data.get('debt_optimization', {}),
                'credit_utilization': optimization_data.get('credit_utilization', {}),
                'payment_methods': optimization_data.get('payment_methods', []),
                'timing_optimization': optimization_data.get('timing_optimization', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting payment optimization data for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_financial_forecast_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive financial forecast data"""
        try:
            # Get financial forecast from analyzer
            forecast = self.financial_analyzer.generate_financial_analysis(user_id)
            
            return {
                'forecast_period': '12_months',
                'income_forecast': forecast.get('income_forecast', {}),
                'expense_forecast': forecast.get('expense_forecast', {}),
                'savings_forecast': forecast.get('savings_forecast', {}),
                'investment_forecast': forecast.get('investment_forecast', {}),
                'debt_forecast': forecast.get('debt_forecast', {}),
                'net_worth_forecast': forecast.get('net_worth_forecast', {}),
                'confidence_intervals': forecast.get('confidence_intervals', {}),
                'scenario_analysis': forecast.get('scenario_analysis', {}),
                'risk_factors': forecast.get('risk_factors', []),
                'opportunities': forecast.get('opportunities', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting financial forecast for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_investment_overview_data(self, user_id: str) -> Dict[str, Any]:
        """Get investment overview data"""
        try:
            # Get investment accounts
            investment_accounts = self._get_investment_accounts(user_id)
            
            # Calculate investment metrics
            investment_metrics = self._calculate_investment_metrics(investment_accounts)
            
            # Get portfolio analysis
            portfolio_analysis = self._analyze_investment_portfolio(investment_accounts)
            
            return {
                'investment_accounts': investment_accounts,
                'portfolio_value': investment_metrics.get('total_value', 0.0),
                'portfolio_performance': investment_metrics.get('performance', {}),
                'asset_allocation': portfolio_analysis.get('asset_allocation', {}),
                'risk_assessment': portfolio_analysis.get('risk_assessment', {}),
                'rebalancing_recommendations': portfolio_analysis.get('rebalancing', []),
                'investment_opportunities': portfolio_analysis.get('opportunities', []),
                'tax_implications': portfolio_analysis.get('tax_implications', {}),
                'diversification_score': portfolio_analysis.get('diversification_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting investment overview for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_debt_management_data(self, user_id: str) -> Dict[str, Any]:
        """Get debt management data"""
        try:
            # Get debt accounts
            debt_accounts = self._get_debt_accounts(user_id)
            
            # Calculate debt metrics
            debt_metrics = self._calculate_debt_metrics(debt_accounts)
            
            # Generate debt optimization strategies
            optimization_strategies = self._generate_debt_optimization_strategies(debt_accounts)
            
            return {
                'debt_accounts': debt_accounts,
                'total_debt': debt_metrics.get('total_debt', 0.0),
                'debt_to_income_ratio': debt_metrics.get('debt_to_income_ratio', 0.0),
                'interest_payments': debt_metrics.get('interest_payments', 0.0),
                'payoff_timeline': debt_metrics.get('payoff_timeline', {}),
                'optimization_strategies': optimization_strategies,
                'debt_snowball_plan': self._generate_debt_snowball_plan(debt_accounts),
                'debt_avalanche_plan': self._generate_debt_avalanche_plan(debt_accounts),
                'consolidation_opportunities': self._identify_consolidation_opportunities(debt_accounts),
                'credit_score_impact': self._calculate_credit_score_impact(debt_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting debt management data for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_dashboard_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get dashboard alerts and notifications"""
        try:
            alerts = []
            
            # Check for low balance alerts
            balance_alerts = self._check_balance_alerts(user_id)
            alerts.extend(balance_alerts)
            
            # Check for bill due alerts
            bill_alerts = self._check_bill_alerts(user_id)
            alerts.extend(bill_alerts)
            
            # Check for spending alerts
            spending_alerts = self._check_spending_alerts(user_id)
            alerts.extend(spending_alerts)
            
            # Check for investment alerts
            investment_alerts = self._check_investment_alerts(user_id)
            alerts.extend(investment_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting dashboard alerts for user {user_id}: {e}")
            return []
    
    def _get_ai_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Get AI-generated insights for the dashboard"""
        try:
            insights = []
            
            # Generate spending insights
            spending_insights = self._generate_ai_spending_insights(user_id)
            insights.extend(spending_insights)
            
            # Generate savings insights
            savings_insights = self._generate_ai_savings_insights(user_id)
            insights.extend(savings_insights)
            
            # Generate investment insights
            investment_insights = self._generate_ai_investment_insights(user_id)
            insights.extend(investment_insights)
            
            # Generate debt insights
            debt_insights = self._generate_ai_debt_insights(user_id)
            insights.extend(debt_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting AI insights for user {user_id}: {e}")
            return []
    
    def _get_custom_widgets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get custom dashboard widgets"""
        try:
            widgets = []
            
            # Get user's custom widget preferences
            custom_widgets = self._get_user_widget_preferences(user_id)
            
            for widget_config in custom_widgets:
                widget_data = self._generate_widget_data(user_id, widget_config)
                widgets.append(widget_data)
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error getting custom widgets for user {user_id}: {e}")
            return []
    
    # Helper methods for data serialization
    def _serialize_account_balance(self, balance_data: AccountBalanceData) -> Dict[str, Any]:
        """Serialize account balance data"""
        return {
            'account_id': balance_data.account_id,
            'account_name': balance_data.account_name,
            'account_type': balance_data.account_type,
            'institution_name': balance_data.institution_name,
            'current_balance': balance_data.current_balance,
            'available_balance': balance_data.available_balance,
            'last_updated': balance_data.last_updated.isoformat(),
            'balance_change_24h': balance_data.balance_change_24h,
            'balance_change_7d': balance_data.balance_change_7d,
            'balance_change_30d': balance_data.balance_change_30d,
            'account_status': balance_data.account_status,
            'is_primary': balance_data.is_primary,
            'account_number_masked': balance_data.account_number_masked,
            'routing_number_masked': balance_data.routing_number_masked
        }
    
    def _serialize_cash_flow_projection(self, projection: CashFlowProjection) -> Dict[str, Any]:
        """Serialize cash flow projection data"""
        return {
            'month': projection.month,
            'projected_income': projection.projected_income,
            'projected_expenses': projection.projected_expenses,
            'projected_net_flow': projection.projected_net_flow,
            'confidence_level': projection.confidence_level,
            'risk_factors': projection.risk_factors,
            'seasonal_adjustments': projection.seasonal_adjustments,
            'growth_rate': projection.growth_rate,
            'volatility_score': projection.volatility_score
        }
    
    def _serialize_spending_analysis(self, spending_data: SpendingAnalysisData) -> Dict[str, Any]:
        """Serialize spending analysis data"""
        return {
            'category_id': spending_data.category_id,
            'category_name': spending_data.category_name,
            'total_spent': spending_data.total_spent,
            'average_spent': spending_data.average_spent,
            'transaction_count': spending_data.transaction_count,
            'spending_trend': spending_data.spending_trend,
            'trend_percentage': spending_data.trend_percentage,
            'budget_variance': spending_data.budget_variance,
            'custom_rules': spending_data.custom_rules,
            'merchant_analysis': spending_data.merchant_analysis,
            'seasonal_patterns': spending_data.seasonal_patterns,
            'recommendations': spending_data.recommendations
        }
    
    def _serialize_bill_prediction(self, bill_data: BillPredictionData) -> Dict[str, Any]:
        """Serialize bill prediction data"""
        return {
            'bill_id': bill_data.bill_id,
            'bill_name': bill_data.bill_name,
            'due_date': bill_data.due_date.isoformat(),
            'amount': bill_data.amount,
            'category': bill_data.category,
            'merchant': bill_data.merchant,
            'payment_method': bill_data.payment_method,
            'auto_pay_enabled': bill_data.auto_pay_enabled,
            'predicted_payment_date': bill_data.predicted_payment_date.isoformat(),
            'optimization_score': bill_data.optimization_score,
            'payment_strategy': bill_data.payment_strategy,
            'savings_opportunity': bill_data.savings_opportunity,
            'risk_level': bill_data.risk_level,
            'alternative_payment_methods': bill_data.alternative_payment_methods
        }
    
    # Utility methods
    def _mask_account_number(self, account_number: str) -> str:
        """Mask account number for display"""
        if not account_number or len(account_number) < 4:
            return "****"
        return f"****{account_number[-4:]}"
    
    def _mask_routing_number(self, routing_number: str) -> str:
        """Mask routing number for display"""
        if not routing_number or len(routing_number) < 4:
            return "****"
        return f"****{routing_number[-4:]}"
    
    def _calculate_portfolio_metrics(self, account_balances: List[AccountBalanceData]) -> Dict[str, Any]:
        """Calculate portfolio metrics from account balances"""
        try:
            if not account_balances:
                return {}
            
            total_balance = sum(ab.current_balance for ab in account_balances)
            total_available = sum(ab.available_balance for ab in account_balances)
            
            # Calculate diversification
            account_weights = [ab.current_balance / total_balance for ab in account_balances if total_balance > 0]
            diversification_score = 1 - sum(w**2 for w in account_weights) if account_weights else 0
            
            # Calculate balance changes
            total_change_24h = sum(ab.balance_change_24h for ab in account_balances)
            total_change_7d = sum(ab.balance_change_7d for ab in account_balances)
            total_change_30d = sum(ab.balance_change_30d for ab in account_balances)
            
            return {
                'total_balance': total_balance,
                'total_available': total_available,
                'diversification_score': diversification_score,
                'total_change_24h': total_change_24h,
                'total_change_7d': total_change_7d,
                'total_change_30d': total_change_30d,
                'account_count': len(account_balances),
                'primary_accounts': [ab for ab in account_balances if ab.is_primary]
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {}
    
    # Placeholder methods for complex calculations
    def _get_historical_cash_flow_data(self, user_id: str, projection_date: datetime) -> Dict[str, Any]:
        """Get historical cash flow data for projections"""
        # Implementation would query transaction history
        return {}
    
    def _project_income(self, historical_data: Dict[str, Any], projection_date: datetime) -> float:
        """Project income for a given month"""
        # Implementation would use historical patterns and growth rates
        return 5000.0
    
    def _project_expenses(self, historical_data: Dict[str, Any], projection_date: datetime) -> float:
        """Project expenses for a given month"""
        # Implementation would use historical patterns and seasonal adjustments
        return 3500.0
    
    def _calculate_projection_confidence(self, historical_data: Dict[str, Any]) -> float:
        """Calculate confidence level for projections"""
        # Implementation would use statistical analysis
        return 0.85
    
    def _identify_risk_factors(self, historical_data: Dict[str, Any], projection_date: datetime) -> List[str]:
        """Identify risk factors for projections"""
        # Implementation would analyze patterns and external factors
        return []
    
    def _calculate_seasonal_adjustments(self, historical_data: Dict[str, Any], projection_date: datetime) -> Dict[str, float]:
        """Calculate seasonal adjustments"""
        # Implementation would use seasonal decomposition
        return {}
    
    def _calculate_growth_rate(self, historical_data: Dict[str, Any]) -> float:
        """Calculate growth rate from historical data"""
        # Implementation would use trend analysis
        return 0.05
    
    def _calculate_volatility_score(self, historical_data: Dict[str, Any]) -> float:
        """Calculate volatility score from historical data"""
        # Implementation would use statistical measures
        return 0.3
    
    # Additional placeholder methods for other features
    def _get_spending_by_category(self, user_id: str) -> List[SpendingAnalysisData]:
        """Get spending data by category"""
        return []
    
    def _get_custom_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get custom spending categories"""
        return []
    
    def _analyze_spending_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze spending patterns"""
        return {}
    
    def _analyze_merchant_spending(self, user_id: str) -> Dict[str, Any]:
        """Analyze merchant spending patterns"""
        return {}
    
    def _analyze_seasonal_spending(self, user_id: str) -> Dict[str, Any]:
        """Analyze seasonal spending patterns"""
        return {}
    
    def _generate_spending_insights(self, spending_data: List[SpendingAnalysisData], patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate spending insights"""
        return []
    
    def _generate_spending_recommendations(self, spending_data: List[SpendingAnalysisData]) -> List[Dict[str, Any]]:
        """Generate spending recommendations"""
        return []
    
    def _calculate_budget_variance(self, user_id: str) -> Dict[str, Any]:
        """Calculate budget variance"""
        return {}
    
    def _analyze_spending_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze spending trends"""
        return {}
    
    def _get_upcoming_bills(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming bills"""
        return []
    
    def _predict_bill_payment(self, bill: Dict[str, Any]) -> BillPredictionData:
        """Predict bill payment"""
        return BillPredictionData(
            bill_id=bill.get('id', ''),
            bill_name=bill.get('name', ''),
            due_date=date.today(),
            amount=bill.get('amount', 0.0),
            category=bill.get('category', ''),
            merchant=bill.get('merchant', ''),
            payment_method=bill.get('payment_method', ''),
            auto_pay_enabled=bill.get('auto_pay_enabled', False),
            predicted_payment_date=date.today(),
            optimization_score=0.0,
            payment_strategy='',
            savings_opportunity=0.0,
            risk_level='low',
            alternative_payment_methods=[]
        )
    
    def _optimize_bill_payment(self, bill: BillPredictionData) -> BillPredictionData:
        """Optimize bill payment"""
        return bill
    
    def _calculate_payment_metrics(self, bills: List[BillPredictionData]) -> Dict[str, Any]:
        """Calculate payment metrics"""
        return {}
    
    def _calculate_savings_opportunities(self, bills: List[BillPredictionData]) -> List[Dict[str, Any]]:
        """Calculate savings opportunities"""
        return []
    
    def _generate_payment_strategies(self, bills: List[BillPredictionData]) -> List[Dict[str, Any]]:
        """Generate payment strategies"""
        return []
    
    def _assess_payment_risk(self, bills: List[BillPredictionData]) -> Dict[str, Any]:
        """Assess payment risk"""
        return {}
    
    def _generate_auto_pay_recommendations(self, bills: List[BillPredictionData]) -> List[Dict[str, Any]]:
        """Generate auto-pay recommendations"""
        return []
    
    def _get_investment_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get investment accounts"""
        return []
    
    def _calculate_investment_metrics(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate investment metrics"""
        return {}
    
    def _analyze_investment_portfolio(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze investment portfolio"""
        return {}
    
    def _get_debt_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get debt accounts"""
        return []
    
    def _calculate_debt_metrics(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate debt metrics"""
        return {}
    
    def _generate_debt_optimization_strategies(self, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate debt optimization strategies"""
        return []
    
    def _generate_debt_snowball_plan(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate debt snowball plan"""
        return {}
    
    def _generate_debt_avalanche_plan(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate debt avalanche plan"""
        return {}
    
    def _identify_consolidation_opportunities(self, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify consolidation opportunities"""
        return []
    
    def _calculate_credit_score_impact(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate credit score impact"""
        return {}
    
    def _check_balance_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check for balance alerts"""
        return []
    
    def _check_bill_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check for bill alerts"""
        return []
    
    def _check_spending_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check for spending alerts"""
        return []
    
    def _check_investment_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check for investment alerts"""
        return []
    
    def _generate_ai_spending_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate AI spending insights"""
        return []
    
    def _generate_ai_savings_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate AI savings insights"""
        return []
    
    def _generate_ai_investment_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate AI investment insights"""
        return []
    
    def _generate_ai_debt_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate AI debt insights"""
        return []
    
    def _get_user_widget_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's widget preferences"""
        return []
    
    def _generate_widget_data(self, user_id: str, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate widget data"""
        return {}
    
    def _calculate_cash_flow_metrics(self, projections: List[CashFlowProjection]) -> Dict[str, Any]:
        """Calculate cash flow metrics"""
        return {}
    
    def _generate_cash_flow_insights(self, projections: List[CashFlowProjection]) -> List[Dict[str, Any]]:
        """Generate cash flow insights"""
        return []
    
    def _assess_cash_flow_risk(self, projections: List[CashFlowProjection]) -> Dict[str, Any]:
        """Assess cash flow risk"""
        return {}
    
    def _identify_cash_flow_opportunities(self, projections: List[CashFlowProjection]) -> List[Dict[str, Any]]:
        """Identify cash flow opportunities"""
        return []
    
    def _analyze_seasonal_patterns(self, projections: List[CashFlowProjection]) -> Dict[str, Any]:
        """Analyze seasonal patterns"""
        return {}
    
    def _calculate_forecast_accuracy(self, user_id: str) -> Dict[str, Any]:
        """Calculate forecast accuracy"""
        return {} 