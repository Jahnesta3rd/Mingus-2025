"""
Transaction Data Processing Engine

This module provides comprehensive transaction analysis and processing capabilities
for transforming raw Plaid transaction data into actionable financial insights.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from backend.models.bank_account_models import PlaidTransaction, BankAccount
from backend.models.analytics import TransactionInsight, SpendingCategory, BudgetAlert
from backend.services.analytics_service import AnalyticsService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction type classifications"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"
    FEE = "fee"
    UNKNOWN = "unknown"


class SpendingCategory(Enum):
    """Standard spending categories"""
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    HOUSING = "housing"
    INSURANCE = "insurance"
    EDUCATION = "education"
    TRAVEL = "travel"
    SUBSCRIPTIONS = "subscriptions"
    BUSINESS = "business"
    PERSONAL_CARE = "personal_care"
    GIFTS = "gifts"
    CHARITY = "charity"
    OTHER = "other"


class InsightType(Enum):
    """Types of financial insights"""
    SPENDING_PATTERN = "spending_pattern"
    BUDGET_ALERT = "budget_alert"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    INCOME_ANALYSIS = "income_analysis"
    CATEGORY_TREND = "category_trend"
    ANOMALY_DETECTION = "anomaly_detection"
    RECURRING_EXPENSE = "recurring_expense"
    SUBSCRIPTION_ALERT = "subscription_alert"


@dataclass
class TransactionAnalysis:
    """Result of transaction analysis"""
    transaction_id: str
    category: SpendingCategory
    confidence: float
    merchant_name: str
    transaction_type: TransactionType
    is_recurring: bool
    is_subscription: bool
    risk_score: float
    insights: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class SpendingInsight:
    """Spending pattern insight"""
    category: SpendingCategory
    total_amount: Decimal
    transaction_count: int
    average_amount: Decimal
    trend: str  # "increasing", "decreasing", "stable"
    percentage_change: float
    period: str  # "week", "month", "quarter", "year"
    recommendations: List[str] = field(default_factory=list)


@dataclass
class BudgetAlert:
    """Budget threshold alert"""
    category: SpendingCategory
    current_spending: Decimal
    budget_limit: Decimal
    percentage_used: float
    days_remaining: int
    alert_level: str  # "warning", "critical", "over_budget"
    recommendations: List[str] = field(default_factory=list)


class TransactionProcessor:
    """
    Comprehensive transaction data processing engine that transforms raw Plaid
    transaction data into actionable financial insights.
    """
    
    def __init__(self, db_session: Session, analytics_service: AnalyticsService):
        self.db_session = db_session
        self.analytics_service = analytics_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize processing components
        self._initialize_categorization_rules()
        self._initialize_merchant_patterns()
        self._initialize_insight_generators()
    
    def _initialize_categorization_rules(self):
        """Initialize transaction categorization rules"""
        self.categorization_rules = {
            SpendingCategory.FOOD_DINING: [
                r'\b(starbucks|mcdonalds|burger|pizza|restaurant|cafe|coffee|food|dining|grubhub|doordash|uber eats)\b',
                r'\b(grocery|supermarket|whole foods|trader joe|kroger|safeway|walmart|target)\b'
            ],
            SpendingCategory.TRANSPORTATION: [
                r'\b(uber|lyft|taxi|transport|gas|fuel|shell|exxon|chevron|bp)\b',
                r'\b(public transit|metro|bus|train|subway|parking|toll)\b'
            ],
            SpendingCategory.SHOPPING: [
                r'\b(amazon|walmart|target|best buy|home depot|lowes|macy|nordstrom)\b',
                r'\b(clothing|apparel|shoes|electronics|furniture|jewelry)\b'
            ],
            SpendingCategory.ENTERTAINMENT: [
                r'\b(netflix|spotify|hulu|disney|movie|theater|concert|game|entertainment)\b',
                r'\b(bar|pub|club|casino|amusement|park|museum|zoo)\b'
            ],
            SpendingCategory.HEALTHCARE: [
                r'\b(doctor|hospital|pharmacy|cvs|walgreens|medical|dental|vision)\b',
                r'\b(insurance|copay|deductible|prescription|medication)\b'
            ],
            SpendingCategory.UTILITIES: [
                r'\b(electric|gas|water|internet|phone|cell|mobile|utility)\b',
                r'\b(comcast|verizon|at&t|sprint|tmobile|spectrum)\b'
            ],
            SpendingCategory.HOUSING: [
                r'\b(rent|mortgage|apartment|house|property|maintenance|repair)\b',
                r'\b(hoa|condo|association|landlord|property management)\b'
            ],
            SpendingCategory.SUBSCRIPTIONS: [
                r'\b(subscription|monthly|recurring|auto-pay|automatic)\b',
                r'\b(software|saas|platform|service|membership)\b'
            ]
        }
    
    def _initialize_merchant_patterns(self):
        """Initialize merchant name patterns for better categorization"""
        self.merchant_patterns = {
            'subscription_indicators': [
                r'\b(monthly|subscription|recurring|auto-pay|automatic)\b',
                r'\b(software|saas|platform|service|membership)\b'
            ],
            'recurring_indicators': [
                r'\b(monthly|weekly|daily|annual|yearly|quarterly)\b',
                r'\b(regular|periodic|scheduled|automatic)\b'
            ],
            'high_risk_merchants': [
                r'\b(casino|gambling|bet|lottery|poker|slot)\b',
                r'\b(payday|loan|pawn|check cashing|money order)\b'
            ]
        }
    
    def _initialize_insight_generators(self):
        """Initialize insight generation algorithms"""
        self.insight_generators = {
            'spending_patterns': self._analyze_spending_patterns,
            'budget_alerts': self._generate_budget_alerts,
            'savings_opportunities': self._identify_savings_opportunities,
            'anomaly_detection': self._detect_anomalies,
            'subscription_analysis': self._analyze_subscriptions
        }
    
    def process_transactions(self, user_id: int, account_ids: List[str] = None, 
                           date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """
        Process transactions and generate comprehensive insights
        
        Args:
            user_id: User ID to process transactions for
            account_ids: Specific account IDs to process (None for all)
            date_range: Date range to process (None for last 90 days)
        
        Returns:
            Dictionary containing all processed insights and analysis
        """
        try:
            # Get transactions to process
            transactions = self._get_transactions(user_id, account_ids, date_range)
            
            if not transactions:
                return {
                    'success': True,
                    'message': 'No transactions found for processing',
                    'insights': [],
                    'summary': {}
                }
            
            # Process each transaction
            processed_transactions = []
            for transaction in transactions:
                analysis = self._analyze_single_transaction(transaction)
                processed_transactions.append(analysis)
                
                # Store analysis results
                self._store_transaction_analysis(transaction.id, analysis)
            
            # Generate comprehensive insights
            insights = self._generate_comprehensive_insights(processed_transactions, user_id)
            
            # Generate summary statistics
            summary = self._generate_summary_statistics(processed_transactions)
            
            # Store insights in database
            self._store_insights(insights, user_id)
            
            return {
                'success': True,
                'message': f'Processed {len(processed_transactions)} transactions',
                'insights': insights,
                'summary': summary,
                'processed_count': len(processed_transactions)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing transactions: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'insights': [],
                'summary': {}
            }
    
    def _get_transactions(self, user_id: int, account_ids: List[str] = None,
                         date_range: Tuple[datetime, datetime] = None) -> List[PlaidTransaction]:
        """Retrieve transactions for processing"""
        query = self.db_session.query(PlaidTransaction).join(
            BankAccount, PlaidTransaction.account_id == BankAccount.id
        ).filter(BankAccount.user_id == user_id)
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if date_range:
            start_date, end_date = date_range
            query = query.filter(
                and_(
                    PlaidTransaction.date >= start_date,
                    PlaidTransaction.date <= end_date
                )
            )
        else:
            # Default to last 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            query = query.filter(
                and_(
                    PlaidTransaction.date >= start_date,
                    PlaidTransaction.date <= end_date
                )
            )
        
        return query.order_by(desc(PlaidTransaction.date)).all()
    
    def _analyze_single_transaction(self, transaction: PlaidTransaction) -> TransactionAnalysis:
        """Analyze a single transaction and generate insights"""
        # Decrypt transaction data if needed
        name = self._decrypt_field(transaction.name) if transaction.name else ""
        merchant_name = self._decrypt_field(transaction.merchant_name) if transaction.merchant_name else ""
        
        # Determine transaction type
        transaction_type = self._classify_transaction_type(transaction, name, merchant_name)
        
        # Categorize transaction
        category, confidence = self._categorize_transaction(name, merchant_name, transaction.amount)
        
        # Detect recurring patterns
        is_recurring = self._detect_recurring_pattern(transaction, name, merchant_name)
        is_subscription = self._detect_subscription(transaction, name, merchant_name)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(transaction, name, merchant_name, category)
        
        # Generate transaction-specific insights
        insights = self._generate_transaction_insights(transaction, category, transaction_type)
        
        # Generate tags
        tags = self._generate_transaction_tags(transaction, category, transaction_type)
        
        return TransactionAnalysis(
            transaction_id=transaction.id,
            category=category,
            confidence=confidence,
            merchant_name=merchant_name or name,
            transaction_type=transaction_type,
            is_recurring=is_recurring,
            is_subscription=is_subscription,
            risk_score=risk_score,
            insights=insights,
            tags=tags
        )
    
    def _classify_transaction_type(self, transaction: PlaidTransaction, 
                                 name: str, merchant_name: str) -> TransactionType:
        """Classify transaction as income, expense, transfer, etc."""
        amount = transaction.amount
        
        # Income indicators
        income_indicators = [
            r'\b(deposit|credit|refund|return|rebate|cashback|bonus|salary|payroll)\b',
            r'\b(interest|dividend|investment|stock|bond|mutual fund)\b'
        ]
        
        # Transfer indicators
        transfer_indicators = [
            r'\b(transfer|ach|wire|venmo|paypal|zelle|cash app)\b',
            r'\b(move money|send money|receive money)\b'
        ]
        
        # Fee indicators
        fee_indicators = [
            r'\b(fee|charge|penalty|late|overdraft|maintenance|service)\b',
            r'\b(atm|withdrawal|foreign transaction)\b'
        ]
        
        # Check for income
        for pattern in income_indicators:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                return TransactionType.INCOME
        
        # Check for transfers
        for pattern in transfer_indicators:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                return TransactionType.TRANSFER
        
        # Check for fees
        for pattern in fee_indicators:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                return TransactionType.FEE
        
        # Default classification based on amount
        if amount > 0:
            return TransactionType.INCOME
        else:
            return TransactionType.EXPENSE
    
    def _categorize_transaction(self, name: str, merchant_name: str, 
                              amount: Decimal) -> Tuple[SpendingCategory, float]:
        """Categorize transaction using pattern matching and ML"""
        best_category = SpendingCategory.OTHER
        best_confidence = 0.0
        
        # Combine name and merchant for analysis
        text_to_analyze = f"{name} {merchant_name}".lower()
        
        # Apply categorization rules
        for category, patterns in self.categorization_rules.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text_to_analyze):
                    matches += 1
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category
        
        # Apply amount-based heuristics
        amount_confidence = self._apply_amount_heuristics(amount, best_category)
        final_confidence = (best_confidence + amount_confidence) / 2
        
        return best_category, final_confidence
    
    def _apply_amount_heuristics(self, amount: Decimal, category: SpendingCategory) -> float:
        """Apply amount-based heuristics for categorization confidence"""
        abs_amount = abs(amount)
        
        # Amount ranges for different categories
        amount_ranges = {
            SpendingCategory.FOOD_DINING: (5, 100),
            SpendingCategory.TRANSPORTATION: (10, 200),
            SpendingCategory.SHOPPING: (20, 1000),
            SpendingCategory.ENTERTAINMENT: (10, 200),
            SpendingCategory.HEALTHCARE: (20, 500),
            SpendingCategory.UTILITIES: (50, 500),
            SpendingCategory.HOUSING: (500, 5000),
            SpendingCategory.SUBSCRIPTIONS: (5, 50)
        }
        
        if category in amount_ranges:
            min_amount, max_amount = amount_ranges[category]
            
            if min_amount <= abs_amount <= max_amount:
                return 0.8
            elif abs_amount < min_amount * 2:
                return 0.6
            elif abs_amount < max_amount * 1.5:
                return 0.4
            else:
                return 0.2
        
        return 0.5
    
    def _detect_recurring_pattern(self, transaction: PlaidTransaction, 
                                name: str, merchant_name: str) -> bool:
        """Detect if transaction is part of a recurring pattern"""
        # Check for recurring indicators in name/merchant
        for pattern in self.merchant_patterns['recurring_indicators']:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                return True
        
        # Check for similar transactions in recent history
        similar_transactions = self._find_similar_transactions(transaction, name, merchant_name)
        
        if len(similar_transactions) >= 2:
            # Check if they follow a pattern (monthly, weekly, etc.)
            return self._analyze_recurring_pattern(similar_transactions)
        
        return False
    
    def _detect_subscription(self, transaction: PlaidTransaction, 
                           name: str, merchant_name: str) -> bool:
        """Detect if transaction is a subscription payment"""
        # Check for subscription indicators
        for pattern in self.merchant_patterns['subscription_indicators']:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                return True
        
        # Check if it's a recurring payment with subscription-like characteristics
        if self._detect_recurring_pattern(transaction, name, merchant_name):
            # Additional checks for subscription characteristics
            abs_amount = abs(transaction.amount)
            if 5 <= abs_amount <= 50:  # Typical subscription range
                return True
        
        return False
    
    def _calculate_risk_score(self, transaction: PlaidTransaction, name: str,
                            merchant_name: str, category: SpendingCategory) -> float:
        """Calculate risk score for transaction"""
        risk_score = 0.0
        
        # Check for high-risk merchants
        for pattern in self.merchant_patterns['high_risk_merchants']:
            if re.search(pattern, name.lower()) or re.search(pattern, merchant_name.lower()):
                risk_score += 0.5
        
        # Amount-based risk
        abs_amount = abs(transaction.amount)
        if abs_amount > 1000:
            risk_score += 0.3
        elif abs_amount > 500:
            risk_score += 0.2
        elif abs_amount > 100:
            risk_score += 0.1
        
        # Category-based risk
        high_risk_categories = [
            SpendingCategory.GAMBLING,
            SpendingCategory.LOANS,
            SpendingCategory.CRYPTO
        ]
        
        if category in high_risk_categories:
            risk_score += 0.4
        
        # Time-based risk (late night transactions)
        if transaction.date.hour >= 22 or transaction.date.hour <= 6:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _generate_transaction_insights(self, transaction: PlaidTransaction,
                                     category: SpendingCategory, 
                                     transaction_type: TransactionType) -> List[str]:
        """Generate insights for a single transaction"""
        insights = []
        amount = abs(transaction.amount)
        
        # Amount-based insights
        if amount > 500:
            insights.append("High-value transaction detected")
        
        if transaction_type == TransactionType.EXPENSE and amount > 100:
            insights.append("Significant expense recorded")
        
        # Category-based insights
        if category == SpendingCategory.SUBSCRIPTIONS:
            insights.append("Subscription payment identified")
        
        if category == SpendingCategory.FOOD_DINING and amount > 50:
            insights.append("Premium dining expense")
        
        # Time-based insights
        if transaction.date.hour >= 22:
            insights.append("Late-night transaction")
        
        return insights
    
    def _generate_transaction_tags(self, transaction: PlaidTransaction,
                                 category: SpendingCategory,
                                 transaction_type: TransactionType) -> List[str]:
        """Generate tags for transaction"""
        tags = []
        
        # Add category tag
        tags.append(category.value)
        
        # Add transaction type tag
        tags.append(transaction_type.value)
        
        # Add amount-based tags
        amount = abs(transaction.amount)
        if amount > 1000:
            tags.append("high-value")
        elif amount > 100:
            tags.append("medium-value")
        else:
            tags.append("low-value")
        
        # Add time-based tags
        if transaction.date.hour >= 22 or transaction.date.hour <= 6:
            tags.append("late-night")
        
        return tags
    
    def _generate_comprehensive_insights(self, processed_transactions: List[TransactionAnalysis],
                                       user_id: int) -> Dict[str, Any]:
        """Generate comprehensive insights from processed transactions"""
        insights = {}
        
        # Generate each type of insight
        for insight_type, generator in self.insight_generators.items():
            try:
                insights[insight_type] = generator(processed_transactions, user_id)
            except Exception as e:
                self.logger.error(f"Error generating {insight_type} insights: {str(e)}")
                insights[insight_type] = []
        
        return insights
    
    def _analyze_spending_patterns(self, transactions: List[TransactionAnalysis],
                                 user_id: int) -> List[SpendingInsight]:
        """Analyze spending patterns and trends"""
        insights = []
        
        # Group by category
        category_data = defaultdict(list)
        for analysis in transactions:
            if analysis.transaction_type == TransactionType.EXPENSE:
                category_data[analysis.category].append(analysis)
        
        # Analyze each category
        for category, category_transactions in category_data.items():
            if len(category_transactions) < 3:  # Need minimum transactions for analysis
                continue
            
            # Calculate statistics
            total_amount = sum(abs(t.transaction.amount) for t in category_transactions)
            transaction_count = len(category_transactions)
            average_amount = total_amount / transaction_count
            
            # Calculate trend (simplified - would need historical data for proper trend analysis)
            trend = "stable"  # Placeholder
            percentage_change = 0.0  # Placeholder
            
            # Generate recommendations
            recommendations = self._generate_spending_recommendations(category, total_amount, average_amount)
            
            insight = SpendingInsight(
                category=category,
                total_amount=total_amount,
                transaction_count=transaction_count,
                average_amount=average_amount,
                trend=trend,
                percentage_change=percentage_change,
                period="month",
                recommendations=recommendations
            )
            
            insights.append(insight)
        
        return insights
    
    def _generate_budget_alerts(self, transactions: List[TransactionAnalysis],
                              user_id: int) -> List[BudgetAlert]:
        """Generate budget alerts based on spending"""
        alerts = []
        
        # This would integrate with user's budget settings
        # For now, generate alerts based on category spending thresholds
        
        category_totals = defaultdict(Decimal)
        for analysis in transactions:
            if analysis.transaction_type == TransactionType.EXPENSE:
                category_totals[analysis.category] += abs(analysis.transaction.amount)
        
        # Default budget thresholds (would come from user settings)
        default_budgets = {
            SpendingCategory.FOOD_DINING: 500,
            SpendingCategory.TRANSPORTATION: 300,
            SpendingCategory.SHOPPING: 400,
            SpendingCategory.ENTERTAINMENT: 200,
            SpendingCategory.HEALTHCARE: 300,
            SpendingCategory.UTILITIES: 200,
            SpendingCategory.HOUSING: 2000,
            SpendingCategory.SUBSCRIPTIONS: 100
        }
        
        for category, total_spent in category_totals.items():
            if category in default_budgets:
                budget_limit = default_budgets[category]
                percentage_used = (total_spent / budget_limit) * 100
                
                if percentage_used >= 80:
                    alert_level = "critical" if percentage_used >= 100 else "warning"
                    
                    alert = BudgetAlert(
                        category=category,
                        current_spending=total_spent,
                        budget_limit=budget_limit,
                        percentage_used=percentage_used,
                        days_remaining=30,  # Placeholder
                        alert_level=alert_level,
                        recommendations=self._generate_budget_recommendations(category, total_spent, budget_limit)
                    )
                    
                    alerts.append(alert)
        
        return alerts
    
    def _identify_savings_opportunities(self, transactions: List[TransactionAnalysis],
                                      user_id: int) -> List[Dict[str, Any]]:
        """Identify potential savings opportunities"""
        opportunities = []
        
        # Analyze subscription spending
        subscription_transactions = [
            t for t in transactions 
            if t.is_subscription and t.transaction_type == TransactionType.EXPENSE
        ]
        
        if len(subscription_transactions) > 5:
            opportunities.append({
                'type': 'subscription_consolidation',
                'title': 'Multiple Subscriptions Detected',
                'description': f'You have {len(subscription_transactions)} active subscriptions',
                'potential_savings': 'Consider consolidating or canceling unused subscriptions',
                'priority': 'medium'
            })
        
        # Analyze high-frequency spending
        category_frequency = Counter(t.category for t in transactions if t.transaction_type == TransactionType.EXPENSE)
        
        for category, frequency in category_frequency.most_common(3):
            if frequency > 10:  # High frequency spending
                opportunities.append({
                    'type': 'frequent_spending',
                    'title': f'Frequent {category.value.replace("_", " ").title()} Spending',
                    'description': f'{frequency} transactions in this category',
                    'potential_savings': 'Consider bulk purchases or subscription options',
                    'priority': 'low'
                })
        
        return opportunities
    
    def _detect_anomalies(self, transactions: List[TransactionAnalysis],
                         user_id: int) -> List[Dict[str, Any]]:
        """Detect anomalous transactions"""
        anomalies = []
        
        # Detect unusual amounts
        amounts = [abs(t.transaction.amount) for t in transactions]
        if amounts:
            mean_amount = sum(amounts) / len(amounts)
            std_dev = (sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
            
            for analysis in transactions:
                amount = abs(analysis.transaction.amount)
                if amount > mean_amount + (2 * std_dev):  # 2 standard deviations
                    anomalies.append({
                        'type': 'unusual_amount',
                        'transaction_id': analysis.transaction_id,
                        'amount': amount,
                        'description': f'Unusually high transaction amount: ${amount:.2f}',
                        'severity': 'medium'
                    })
        
        # Detect unusual merchants
        merchant_counts = Counter(t.merchant_name for t in transactions)
        for analysis in transactions:
            if merchant_counts[analysis.merchant_name] == 1:  # First time merchant
                if abs(analysis.transaction.amount) > 100:
                    anomalies.append({
                        'type': 'new_merchant',
                        'transaction_id': analysis.transaction_id,
                        'merchant': analysis.merchant_name,
                        'description': f'First transaction with {analysis.merchant_name}',
                        'severity': 'low'
                    })
        
        return anomalies
    
    def _analyze_subscriptions(self, transactions: List[TransactionAnalysis],
                             user_id: int) -> Dict[str, Any]:
        """Analyze subscription spending patterns"""
        subscription_transactions = [
            t for t in transactions 
            if t.is_subscription and t.transaction_type == TransactionType.EXPENSE
        ]
        
        if not subscription_transactions:
            return {
                'total_subscriptions': 0,
                'monthly_cost': 0,
                'subscriptions': [],
                'recommendations': []
            }
        
        # Group by merchant
        merchant_subscriptions = defaultdict(list)
        for analysis in subscription_transactions:
            merchant_subscriptions[analysis.merchant_name].append(analysis)
        
        subscriptions = []
        total_monthly_cost = 0
        
        for merchant, merchant_transactions in merchant_subscriptions.items():
            # Calculate average monthly cost
            total_amount = sum(abs(t.transaction.amount) for t in merchant_transactions)
            avg_monthly_cost = total_amount / len(merchant_transactions)
            total_monthly_cost += avg_monthly_cost
            
            subscriptions.append({
                'merchant': merchant,
                'monthly_cost': avg_monthly_cost,
                'transaction_count': len(merchant_transactions),
                'last_transaction': max(t.transaction.date for t in merchant_transactions)
            })
        
        # Generate recommendations
        recommendations = []
        if len(subscriptions) > 5:
            recommendations.append("Consider reviewing and canceling unused subscriptions")
        
        if total_monthly_cost > 100:
            recommendations.append("High subscription costs detected - consider consolidation")
        
        return {
            'total_subscriptions': len(subscriptions),
            'monthly_cost': total_monthly_cost,
            'subscriptions': subscriptions,
            'recommendations': recommendations
        }
    
    def _generate_spending_recommendations(self, category: SpendingCategory,
                                         total_amount: Decimal,
                                         average_amount: Decimal) -> List[str]:
        """Generate spending recommendations for a category"""
        recommendations = []
        
        if category == SpendingCategory.FOOD_DINING:
            if total_amount > 500:
                recommendations.append("Consider meal planning to reduce dining costs")
            if average_amount > 50:
                recommendations.append("Look for more affordable dining options")
        
        elif category == SpendingCategory.SHOPPING:
            if total_amount > 400:
                recommendations.append("Consider waiting for sales or using coupons")
            recommendations.append("Review purchases for necessity vs. impulse buys")
        
        elif category == SpendingCategory.SUBSCRIPTIONS:
            recommendations.append("Regularly review subscription usage and value")
        
        return recommendations
    
    def _generate_budget_recommendations(self, category: SpendingCategory,
                                       current_spending: Decimal,
                                       budget_limit: Decimal) -> List[str]:
        """Generate budget recommendations"""
        recommendations = []
        
        if current_spending >= budget_limit:
            recommendations.append(f"Budget exceeded for {category.value.replace('_', ' ')}")
            recommendations.append("Consider reducing spending in this category")
        else:
            percentage_remaining = ((budget_limit - current_spending) / budget_limit) * 100
            if percentage_remaining < 20:
                recommendations.append(f"Only {percentage_remaining:.1f}% of budget remaining")
                recommendations.append("Monitor spending closely")
        
        return recommendations
    
    def _find_similar_transactions(self, transaction: PlaidTransaction,
                                 name: str, merchant_name: str) -> List[PlaidTransaction]:
        """Find similar transactions in recent history"""
        # This would implement similarity matching
        # For now, return empty list
        return []
    
    def _analyze_recurring_pattern(self, transactions: List[PlaidTransaction]) -> bool:
        """Analyze if transactions follow a recurring pattern"""
        # This would implement pattern analysis
        # For now, return True if multiple transactions exist
        return len(transactions) >= 2
    
    def _decrypt_field(self, encrypted_field: str) -> str:
        """Decrypt encrypted field if needed"""
        if not encrypted_field:
            return ""
        
        try:
            return decrypt_data(encrypted_field)
        except Exception as e:
            self.logger.warning(f"Failed to decrypt field: {str(e)}")
            return encrypted_field
    
    def _store_transaction_analysis(self, transaction_id: str, analysis: TransactionAnalysis):
        """Store transaction analysis results"""
        try:
            # Store in analytics table
            insight = TransactionInsight(
                transaction_id=transaction_id,
                category=analysis.category.value,
                confidence=analysis.confidence,
                transaction_type=analysis.transaction_type.value,
                is_recurring=analysis.is_recurring,
                is_subscription=analysis.is_subscription,
                risk_score=analysis.risk_score,
                insights=json.dumps(analysis.insights),
                tags=json.dumps(analysis.tags),
                created_at=datetime.now()
            )
            
            self.db_session.add(insight)
            self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Error storing transaction analysis: {str(e)}")
            self.db_session.rollback()
    
    def _store_insights(self, insights: Dict[str, Any], user_id: int):
        """Store generated insights in database"""
        try:
            # Store insights in appropriate tables
            # This would integrate with the analytics service
            pass
            
        except Exception as e:
            self.logger.error(f"Error storing insights: {str(e)}")
    
    def _generate_summary_statistics(self, processed_transactions: List[TransactionAnalysis]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not processed_transactions:
            return {}
        
        total_transactions = len(processed_transactions)
        expenses = [t for t in processed_transactions if t.transaction_type == TransactionType.EXPENSE]
        income = [t for t in processed_transactions if t.transaction_type == TransactionType.INCOME]
        
        total_expenses = sum(abs(t.transaction.amount) for t in expenses)
        total_income = sum(t.transaction.amount for t in income)
        
        category_distribution = Counter(t.category.value for t in processed_transactions)
        
        return {
            'total_transactions': total_transactions,
            'total_expenses': total_expenses,
            'total_income': total_income,
            'net_flow': total_income - total_expenses,
            'category_distribution': dict(category_distribution),
            'recurring_transactions': len([t for t in processed_transactions if t.is_recurring]),
            'subscriptions': len([t for t in processed_transactions if t.is_subscription]),
            'average_risk_score': sum(t.risk_score for t in processed_transactions) / total_transactions
        } 