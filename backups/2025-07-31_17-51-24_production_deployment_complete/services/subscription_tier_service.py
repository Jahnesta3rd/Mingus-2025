"""
Subscription Tier Service

This module manages subscription tier features and access controls for the MINGUS application,
specifically handling Professional tier features like advanced AI categorization, custom categories,
detailed merchant analysis, and cash flow forecasting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier types"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"


class FeatureType(Enum):
    """Feature types for subscription tiers"""
    AI_CATEGORIZATION = "ai_categorization"
    CUSTOM_CATEGORIES = "custom_categories"
    MERCHANT_ANALYSIS = "merchant_analysis"
    CASH_FLOW_FORECASTING = "cash_flow_forecasting"
    BASIC_ANALYTICS = "basic_analytics"
    STANDARD_CATEGORIZATION = "standard_categorization"


class CategoryRuleType(Enum):
    """Types of category rules"""
    MERCHANT_NAME = "merchant_name"
    AMOUNT_RANGE = "amount_range"
    DATE_PATTERN = "date_pattern"
    KEYWORD_MATCH = "keyword_match"
    REGEX_PATTERN = "regex_pattern"
    COMBINATION = "combination"


@dataclass
class CategoryRule:
    """Custom category rule definition"""
    rule_id: str
    user_id: int
    category_name: str
    rule_type: CategoryRuleType
    rule_conditions: Dict[str, Any]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomCategory:
    """Custom category definition"""
    category_id: str
    user_id: int
    category_name: str
    parent_category: Optional[str] = None
    color: str = "#000000"
    icon: str = "default"
    description: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    rules: List[CategoryRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MerchantAnalysis:
    """Detailed merchant analysis for Professional tier"""
    merchant_id: str
    user_id: int
    merchant_name: str
    standardized_name: str
    merchant_type: str
    category: str
    subcategory: Optional[str] = None
    
    # Transaction analysis
    total_transactions: int
    total_amount: float
    average_amount: float
    first_transaction: datetime
    last_transaction: datetime
    
    # Spending patterns
    spending_frequency: float  # transactions per month
    spending_consistency: float  # 0-1 scale
    seasonal_patterns: Dict[str, float]
    
    # Merchant insights
    merchant_score: float  # 0-100 scale
    risk_level: str  # low, medium, high
    fraud_indicators: List[str]
    
    # Business intelligence
    business_type: str
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CashFlowForecast:
    """Cash flow forecasting for Professional tier"""
    forecast_id: str
    user_id: int
    forecast_period: int  # months
    start_date: datetime
    end_date: datetime
    
    # Forecast data
    monthly_forecasts: List[Dict[str, Any]]
    confidence_intervals: List[Dict[str, float]]
    
    # Income forecasting
    projected_income: float
    income_growth_rate: float
    income_volatility: float
    
    # Expense forecasting
    projected_expenses: float
    expense_growth_rate: float
    expense_volatility: float
    
    # Cash flow projections
    projected_cash_flow: float
    cash_flow_trend: str
    break_even_date: Optional[datetime] = None
    
    # Model information
    model_version: str
    accuracy_score: float
    last_updated: datetime
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AICategorizationResult:
    """AI-powered categorization result"""
    transaction_id: str
    user_id: int
    original_category: str
    ai_category: str
    confidence_score: float
    categorization_method: str
    reasoning: str
    alternatives: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)


class SubscriptionTierService:
    """
    Service for managing subscription tier features and access controls.
    Handles Professional tier features like advanced AI categorization, custom categories,
    detailed merchant analysis, and cash flow forecasting.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize tier configurations
        self._initialize_tier_configurations()
        
        # Initialize AI categorization
        self._initialize_ai_categorization()
        
        # Initialize custom category management
        self._initialize_custom_categories()
        
        # Initialize merchant analysis
        self._initialize_merchant_analysis()
        
        # Initialize cash flow forecasting
        self._initialize_cash_flow_forecasting()
    
    def _initialize_tier_configurations(self):
        """Initialize subscription tier configurations"""
        self.tier_configurations = {
            SubscriptionTier.BUDGET: {
                'features': {
                    FeatureType.BASIC_ANALYTICS: True,
                    FeatureType.STANDARD_CATEGORIZATION: True,
                    FeatureType.AI_CATEGORIZATION: False,
                    FeatureType.CUSTOM_CATEGORIES: False,
                    FeatureType.MERCHANT_ANALYSIS: False,
                    FeatureType.CASH_FLOW_FORECASTING: False,
                },
                'limits': {
                    'max_custom_categories': 0,
                    'max_category_rules': 0,
                    'forecast_months': 0,
                    'merchant_analysis_depth': 'basic',
                }
            },
            SubscriptionTier.MID_TIER: {
                'features': {
                    FeatureType.BASIC_ANALYTICS: True,
                    FeatureType.STANDARD_CATEGORIZATION: True,
                    FeatureType.AI_CATEGORIZATION: True,
                    FeatureType.CUSTOM_CATEGORIES: True,
                    FeatureType.MERCHANT_ANALYSIS: False,
                    FeatureType.CASH_FLOW_FORECASTING: False,
                },
                'limits': {
                    'max_custom_categories': 5,
                    'max_category_rules': 10,
                    'forecast_months': 0,
                    'merchant_analysis_depth': 'basic',
                }
            },
            SubscriptionTier.PROFESSIONAL: {
                'features': {
                    FeatureType.BASIC_ANALYTICS: True,
                    FeatureType.STANDARD_CATEGORIZATION: True,
                    FeatureType.AI_CATEGORIZATION: True,
                    FeatureType.CUSTOM_CATEGORIES: True,
                    FeatureType.MERCHANT_ANALYSIS: True,
                    FeatureType.CASH_FLOW_FORECASTING: True,
                },
                'limits': {
                    'max_custom_categories': -1,  # Unlimited
                    'max_category_rules': -1,  # Unlimited
                    'forecast_months': 24,  # 24 months
                    'merchant_analysis_depth': 'advanced',
                }
            }
        }
    
    def _initialize_ai_categorization(self):
        """Initialize AI categorization parameters"""
        self.ai_categorization_params = {
            'confidence_threshold': 0.7,
            'min_confidence_for_auto_apply': 0.9,
            'max_alternatives': 5,
            'categorization_methods': [
                'merchant_pattern_matching',
                'amount_heuristics',
                'temporal_patterns',
                'user_behavior_learning',
                'machine_learning_model'
            ],
            'learning_parameters': {
                'min_samples_for_learning': 10,
                'learning_rate': 0.1,
                'update_frequency': 'weekly'
            }
        }
    
    def _initialize_custom_categories(self):
        """Initialize custom category management"""
        self.custom_category_params = {
            'max_category_name_length': 50,
            'max_description_length': 200,
            'allowed_colors': [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
            ],
            'rule_priorities': {
                'merchant_name': 1,
                'amount_range': 2,
                'date_pattern': 3,
                'keyword_match': 4,
                'regex_pattern': 5,
                'combination': 6
            }
        }
    
    def _initialize_merchant_analysis(self):
        """Initialize merchant analysis parameters"""
        self.merchant_analysis_params = {
            'min_transactions_for_analysis': 3,
            'analysis_period_months': 12,
            'fraud_indicators': [
                'unusual_amount_patterns',
                'irregular_timing',
                'suspicious_merchant_characteristics',
                'geographic_anomalies',
                'category_mismatches'
            ],
            'merchant_scoring_weights': {
                'transaction_consistency': 0.3,
                'amount_stability': 0.25,
                'category_alignment': 0.2,
                'temporal_patterns': 0.15,
                'geographic_consistency': 0.1
            }
        }
    
    def _initialize_cash_flow_forecasting(self):
        """Initialize cash flow forecasting parameters"""
        self.forecasting_params = {
            'forecast_methods': [
                'time_series_analysis',
                'regression_analysis',
                'seasonal_decomposition',
                'machine_learning_forecasting'
            ],
            'confidence_levels': [0.8, 0.9, 0.95],
            'min_data_points': 6,  # Minimum months of data
            'forecast_update_frequency': 'monthly',
            'model_parameters': {
                'seasonality_period': 12,
                'trend_window': 6,
                'smoothing_factor': 0.3
            }
        }
    
    def get_user_tier(self, user_id: int) -> SubscriptionTier:
        """Get user's subscription tier"""
        # This would typically query the user's subscription from the database
        # For now, return Professional tier for demonstration
        return SubscriptionTier.PROFESSIONAL
    
    def has_feature_access(self, user_id: int, feature: FeatureType) -> bool:
        """Check if user has access to a specific feature"""
        user_tier = self.get_user_tier(user_id)
        return self.tier_configurations[user_tier]['features'].get(feature, False)
    
    def get_feature_limits(self, user_id: int) -> Dict[str, Any]:
        """Get feature limits for user's tier"""
        user_tier = self.get_user_tier(user_id)
        return self.tier_configurations[user_tier]['limits']
    
    def apply_ai_categorization(self, user_id: int, transactions: List[PlaidTransaction]) -> List[AICategorizationResult]:
        """Apply AI-powered categorization to transactions"""
        if not self.has_feature_access(user_id, FeatureType.AI_CATEGORIZATION):
            raise ValueError("User does not have access to AI categorization")
        
        results = []
        
        for transaction in transactions:
            # Apply AI categorization logic
            ai_category, confidence, method, reasoning, alternatives = self._categorize_with_ai(transaction)
            
            result = AICategorizationResult(
                transaction_id=transaction.transaction_id,
                user_id=user_id,
                original_category=transaction.category or "uncategorized",
                ai_category=ai_category,
                confidence_score=confidence,
                categorization_method=method,
                reasoning=reasoning,
                alternatives=alternatives
            )
            
            results.append(result)
            
            # Auto-apply high-confidence categorizations
            if confidence >= self.ai_categorization_params['min_confidence_for_auto_apply']:
                transaction.category = ai_category
                self.logger.info(f"Auto-applied AI categorization: {transaction.transaction_id} -> {ai_category}")
        
        return results
    
    def _categorize_with_ai(self, transaction: PlaidTransaction) -> Tuple[str, float, str, str, List[Dict[str, Any]]]:
        """Apply AI categorization to a single transaction"""
        # This is a simplified AI categorization implementation
        # In a real implementation, this would use machine learning models
        
        merchant_name = transaction.merchant_name or transaction.name or ""
        amount = abs(float(transaction.amount))
        
        # Merchant pattern matching
        merchant_patterns = {
            'restaurant': ['restaurant', 'cafe', 'dining', 'food', 'pizza', 'burger'],
            'transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking'],
            'shopping': ['amazon', 'walmart', 'target', 'costco', 'shop'],
            'entertainment': ['netflix', 'spotify', 'movie', 'theater', 'concert'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone'],
            'healthcare': ['doctor', 'pharmacy', 'medical', 'dental', 'vision']
        }
        
        # Find matching patterns
        best_match = "other"
        best_confidence = 0.0
        
        for category, patterns in merchant_patterns.items():
            for pattern in patterns:
                if pattern.lower() in merchant_name.lower():
                    confidence = len(pattern) / len(merchant_name) if merchant_name else 0
                    if confidence > best_confidence:
                        best_match = category
                        best_confidence = confidence
        
        # Amount-based heuristics
        amount_confidence = 0.0
        if amount > 1000:
            amount_confidence = 0.8
            if best_confidence < 0.5:
                best_match = "large_purchase"
                best_confidence = amount_confidence
        
        # Generate alternatives
        alternatives = []
        for category, patterns in merchant_patterns.items():
            if category != best_match:
                confidence = 0.1  # Base confidence for alternatives
                alternatives.append({
                    'category': category,
                    'confidence': confidence,
                    'reasoning': f"Alternative category based on merchant patterns"
                })
        
        # Limit alternatives
        alternatives = sorted(alternatives, key=lambda x: x['confidence'], reverse=True)[:3]
        
        return (
            best_match,
            min(best_confidence, 0.95),  # Cap confidence at 0.95
            "merchant_pattern_matching",
            f"Matched '{merchant_name}' to {best_match} category",
            alternatives
        )
    
    def create_custom_category(self, user_id: int, category_data: Dict[str, Any]) -> CustomCategory:
        """Create a custom category for the user"""
        if not self.has_feature_access(user_id, FeatureType.CUSTOM_CATEGORIES):
            raise ValueError("User does not have access to custom categories")
        
        limits = self.get_feature_limits(user_id)
        current_categories = self._get_user_custom_categories(user_id)
        
        if limits['max_custom_categories'] > 0 and len(current_categories) >= limits['max_custom_categories']:
            raise ValueError(f"User has reached the limit of {limits['max_custom_categories']} custom categories")
        
        # Validate category data
        self._validate_custom_category_data(category_data)
        
        # Create custom category
        category = CustomCategory(
            category_id=f"custom_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            category_name=category_data['name'],
            parent_category=category_data.get('parent_category'),
            color=category_data.get('color', '#000000'),
            icon=category_data.get('icon', 'default'),
            description=category_data.get('description', ''),
            is_active=True
        )
        
        # Add rules if provided
        if 'rules' in category_data:
            for rule_data in category_data['rules']:
                rule = self._create_category_rule(user_id, category.category_id, rule_data)
                category.rules.append(rule)
        
        # Save to database (simplified)
        self.logger.info(f"Created custom category: {category.category_name} for user {user_id}")
        
        return category
    
    def _validate_custom_category_data(self, category_data: Dict[str, Any]):
        """Validate custom category data"""
        if 'name' not in category_data:
            raise ValueError("Category name is required")
        
        if len(category_data['name']) > self.custom_category_params['max_category_name_length']:
            raise ValueError(f"Category name too long. Max length: {self.custom_category_params['max_category_name_length']}")
        
        if 'description' in category_data and len(category_data['description']) > self.custom_category_params['max_description_length']:
            raise ValueError(f"Description too long. Max length: {self.custom_category_params['max_description_length']}")
    
    def _create_category_rule(self, user_id: int, category_id: str, rule_data: Dict[str, Any]) -> CategoryRule:
        """Create a category rule"""
        limits = self.get_feature_limits(user_id)
        current_rules = self._get_user_category_rules(user_id)
        
        if limits['max_category_rules'] > 0 and len(current_rules) >= limits['max_category_rules']:
            raise ValueError(f"User has reached the limit of {limits['max_category_rules']} category rules")
        
        rule = CategoryRule(
            rule_id=f"rule_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            category_name=rule_data['category_name'],
            rule_type=CategoryRuleType(rule_data['rule_type']),
            rule_conditions=rule_data['conditions'],
            priority=rule_data.get('priority', 1),
            is_active=rule_data.get('is_active', True),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=rule_data.get('metadata', {})
        )
        
        return rule
    
    def _get_user_custom_categories(self, user_id: int) -> List[CustomCategory]:
        """Get user's custom categories"""
        # This would query the database for user's custom categories
        # For now, return empty list
        return []
    
    def _get_user_category_rules(self, user_id: int) -> List[CategoryRule]:
        """Get user's category rules"""
        # This would query the database for user's category rules
        # For now, return empty list
        return []
    
    def analyze_merchant(self, user_id: int, merchant_name: str) -> MerchantAnalysis:
        """Perform detailed merchant analysis"""
        if not self.has_feature_access(user_id, FeatureType.MERCHANT_ANALYSIS):
            raise ValueError("User does not have access to merchant analysis")
        
        # Get merchant transactions
        merchant_transactions = self._get_merchant_transactions(user_id, merchant_name)
        
        if len(merchant_transactions) < self.merchant_analysis_params['min_transactions_for_analysis']:
            raise ValueError(f"Insufficient transactions for merchant analysis. Need at least {self.merchant_analysis_params['min_transactions_for_analysis']}")
        
        # Perform analysis
        analysis = self._perform_merchant_analysis(merchant_transactions, merchant_name)
        
        return analysis
    
    def _get_merchant_transactions(self, user_id: int, merchant_name: str) -> List[PlaidTransaction]:
        """Get transactions for a specific merchant"""
        # This would query the database for merchant transactions
        # For now, return empty list
        return []
    
    def _perform_merchant_analysis(self, transactions: List[PlaidTransaction], merchant_name: str) -> MerchantAnalysis:
        """Perform detailed merchant analysis"""
        # Calculate basic metrics
        total_transactions = len(transactions)
        total_amount = sum(abs(float(tx.amount)) for tx in transactions)
        average_amount = total_amount / total_transactions if total_transactions > 0 else 0
        
        # Calculate spending frequency (transactions per month)
        if len(transactions) >= 2:
            date_range = max(tx.date for tx in transactions) - min(tx.date for tx in transactions)
            months = date_range.days / 30.44  # Average days per month
            spending_frequency = total_transactions / months if months > 0 else 0
        else:
            spending_frequency = 0
        
        # Calculate spending consistency
        amounts = [abs(float(tx.amount)) for tx in transactions]
        if len(amounts) > 1:
            mean_amount = sum(amounts) / len(amounts)
            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5
            coefficient_of_variation = std_dev / mean_amount if mean_amount > 0 else 0
            spending_consistency = max(0, 1 - coefficient_of_variation)
        else:
            spending_consistency = 1.0
        
        # Calculate merchant score
        merchant_score = self._calculate_merchant_score(transactions, spending_consistency)
        
        # Determine risk level
        risk_level = self._determine_risk_level(merchant_score, transactions)
        
        # Identify fraud indicators
        fraud_indicators = self._identify_fraud_indicators(transactions)
        
        # Determine business type
        business_type = self._determine_business_type(merchant_name, transactions)
        
        return MerchantAnalysis(
            merchant_id=f"merchant_{hash(merchant_name)}",
            user_id=transactions[0].user_id if transactions else 0,
            merchant_name=merchant_name,
            standardized_name=merchant_name,  # Would be standardized in real implementation
            merchant_type=business_type,
            category=transactions[0].category if transactions else "unknown",
            subcategory=None,
            total_transactions=total_transactions,
            total_amount=total_amount,
            average_amount=average_amount,
            first_transaction=min(tx.date for tx in transactions) if transactions else datetime.now(),
            last_transaction=max(tx.date for tx in transactions) if transactions else datetime.now(),
            spending_frequency=spending_frequency,
            spending_consistency=spending_consistency,
            seasonal_patterns={},  # Would be calculated in real implementation
            merchant_score=merchant_score,
            risk_level=risk_level,
            fraud_indicators=fraud_indicators,
            business_type=business_type,
            location=None,
            website=None,
            phone=None,
            metadata={}
        )
    
    def _calculate_merchant_score(self, transactions: List[PlaidTransaction], spending_consistency: float) -> float:
        """Calculate merchant score based on various factors"""
        weights = self.merchant_analysis_params['merchant_scoring_weights']
        
        # Transaction consistency score
        transaction_consistency_score = spending_consistency * 100
        
        # Amount stability score
        amounts = [abs(float(tx.amount)) for tx in transactions]
        if len(amounts) > 1:
            mean_amount = sum(amounts) / len(amounts)
            amount_variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            amount_stability_score = max(0, 100 - (amount_variance / mean_amount * 100)) if mean_amount > 0 else 100
        else:
            amount_stability_score = 100
        
        # Category alignment score (simplified)
        category_alignment_score = 80  # Would be calculated based on category consistency
        
        # Temporal patterns score (simplified)
        temporal_patterns_score = 75  # Would be calculated based on timing patterns
        
        # Geographic consistency score (simplified)
        geographic_consistency_score = 90  # Would be calculated based on location patterns
        
        # Calculate weighted score
        total_score = (
            transaction_consistency_score * weights['transaction_consistency'] +
            amount_stability_score * weights['amount_stability'] +
            category_alignment_score * weights['category_alignment'] +
            temporal_patterns_score * weights['temporal_patterns'] +
            geographic_consistency_score * weights['geographic_consistency']
        )
        
        return min(100, max(0, total_score))
    
    def _determine_risk_level(self, merchant_score: float, transactions: List[PlaidTransaction]) -> str:
        """Determine merchant risk level"""
        if merchant_score >= 80:
            return "low"
        elif merchant_score >= 60:
            return "medium"
        else:
            return "high"
    
    def _identify_fraud_indicators(self, transactions: List[PlaidTransaction]) -> List[str]:
        """Identify potential fraud indicators"""
        indicators = []
        
        # Check for unusual amount patterns
        amounts = [abs(float(tx.amount)) for tx in transactions]
        if len(amounts) > 1:
            mean_amount = sum(amounts) / len(amounts)
            for amount in amounts:
                if amount > mean_amount * 3:  # Amount 3x higher than average
                    indicators.append("unusual_amount_patterns")
                    break
        
        # Check for irregular timing
        if len(transactions) > 2:
            dates = sorted(tx.date for tx in transactions)
            time_diffs = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            if any(diff < 1 for diff in time_diffs):  # Multiple transactions on same day
                indicators.append("irregular_timing")
        
        return indicators
    
    def _determine_business_type(self, merchant_name: str, transactions: List[PlaidTransaction]) -> str:
        """Determine business type based on merchant name and transactions"""
        merchant_lower = merchant_name.lower()
        
        if any(word in merchant_lower for word in ['restaurant', 'cafe', 'dining', 'food']):
            return "restaurant"
        elif any(word in merchant_lower for word in ['gas', 'fuel', 'oil']):
            return "gas_station"
        elif any(word in merchant_lower for word in ['grocery', 'supermarket', 'food']):
            return "grocery"
        elif any(word in merchant_lower for word in ['bank', 'credit', 'loan']):
            return "financial"
        else:
            return "retail"
    
    def generate_cash_flow_forecast(self, user_id: int, forecast_months: int = 12) -> CashFlowForecast:
        """Generate cash flow forecast for the user"""
        if not self.has_feature_access(user_id, FeatureType.CASH_FLOW_FORECASTING):
            raise ValueError("User does not have access to cash flow forecasting")
        
        limits = self.get_feature_limits(user_id)
        if limits['forecast_months'] > 0 and forecast_months > limits['forecast_months']:
            raise ValueError(f"Forecast period exceeds limit of {limits['forecast_months']} months")
        
        # Get historical transaction data
        historical_data = self._get_historical_cash_flow_data(user_id)
        
        if len(historical_data) < self.forecasting_params['min_data_points']:
            raise ValueError(f"Insufficient historical data for forecasting. Need at least {self.forecasting_params['min_data_points']} months")
        
        # Generate forecast
        forecast = self._generate_forecast(historical_data, forecast_months)
        
        return forecast
    
    def _get_historical_cash_flow_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get historical cash flow data for forecasting"""
        # This would query the database for historical cash flow data
        # For now, return sample data
        return [
            {'month': '2024-01', 'income': 5000, 'expenses': 3500, 'cash_flow': 1500},
            {'month': '2024-02', 'income': 5200, 'expenses': 3600, 'cash_flow': 1600},
            {'month': '2024-03', 'income': 4800, 'expenses': 3400, 'cash_flow': 1400},
            {'month': '2024-04', 'income': 5100, 'expenses': 3700, 'cash_flow': 1400},
            {'month': '2024-05', 'income': 5300, 'expenses': 3500, 'cash_flow': 1800},
            {'month': '2024-06', 'income': 4900, 'expenses': 3300, 'cash_flow': 1600},
        ]
    
    def _generate_forecast(self, historical_data: List[Dict[str, Any]], forecast_months: int) -> CashFlowForecast:
        """Generate cash flow forecast using historical data"""
        # Calculate trends
        income_trend = self._calculate_trend([d['income'] for d in historical_data])
        expense_trend = self._calculate_trend([d['expenses'] for d in historical_data])
        cash_flow_trend = self._calculate_trend([d['cash_flow'] for d in historical_data])
        
        # Generate monthly forecasts
        monthly_forecasts = []
        confidence_intervals = []
        
        current_date = datetime.now()
        base_income = historical_data[-1]['income']
        base_expenses = historical_data[-1]['expenses']
        
        for month in range(1, forecast_months + 1):
            forecast_date = current_date + timedelta(days=30*month)
            
            # Project income and expenses
            projected_income = base_income * (1 + income_trend) ** month
            projected_expenses = base_expenses * (1 + expense_trend) ** month
            projected_cash_flow = projected_income - projected_expenses
            
            monthly_forecast = {
                'month': forecast_date.strftime('%Y-%m'),
                'projected_income': projected_income,
                'projected_expenses': projected_expenses,
                'projected_cash_flow': projected_cash_flow,
                'confidence_level': 0.85 - (month * 0.02)  # Decreasing confidence over time
            }
            
            monthly_forecasts.append(monthly_forecast)
            
            # Calculate confidence intervals
            confidence_interval = {
                'lower_bound': projected_cash_flow * 0.8,
                'upper_bound': projected_cash_flow * 1.2,
                'confidence_level': monthly_forecast['confidence_level']
            }
            
            confidence_intervals.append(confidence_interval)
        
        # Calculate overall projections
        total_projected_income = sum(f['projected_income'] for f in monthly_forecasts)
        total_projected_expenses = sum(f['projected_expenses'] for f in monthly_forecasts)
        total_projected_cash_flow = sum(f['projected_cash_flow'] for f in monthly_forecasts)
        
        # Calculate growth rates
        income_growth_rate = income_trend
        expense_growth_rate = expense_trend
        
        # Calculate volatility
        income_volatility = self._calculate_volatility([d['income'] for d in historical_data])
        expense_volatility = self._calculate_volatility([d['expenses'] for d in historical_data])
        
        # Determine cash flow trend
        if cash_flow_trend > 0.05:
            cash_flow_trend_str = "increasing"
        elif cash_flow_trend < -0.05:
            cash_flow_trend_str = "decreasing"
        else:
            cash_flow_trend_str = "stable"
        
        # Find break-even date
        break_even_date = None
        cumulative_cash_flow = 0
        for forecast in monthly_forecasts:
            cumulative_cash_flow += forecast['projected_cash_flow']
            if cumulative_cash_flow > 0:
                break_even_date = datetime.strptime(forecast['month'], '%Y-%m')
                break
        
        return CashFlowForecast(
            forecast_id=f"forecast_{datetime.now().timestamp()}",
            user_id=historical_data[0].get('user_id', 0),
            forecast_period=forecast_months,
            start_date=current_date,
            end_date=current_date + timedelta(days=30*forecast_months),
            monthly_forecasts=monthly_forecasts,
            confidence_intervals=confidence_intervals,
            projected_income=total_projected_income,
            income_growth_rate=income_growth_rate,
            income_volatility=income_volatility,
            projected_expenses=total_projected_expenses,
            expense_growth_rate=expense_growth_rate,
            expense_volatility=expense_volatility,
            projected_cash_flow=total_projected_cash_flow,
            cash_flow_trend=cash_flow_trend_str,
            break_even_date=break_even_date,
            model_version="1.0",
            accuracy_score=0.85,
            last_updated=datetime.now(),
            metadata={}
        )
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (growth rate) from a list of values"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x_squared_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum * x_sum)
        
        # Convert to growth rate
        if values[0] != 0:
            growth_rate = slope / values[0]
        else:
            growth_rate = 0.0
        
        return growth_rate
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation) from a list of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5 