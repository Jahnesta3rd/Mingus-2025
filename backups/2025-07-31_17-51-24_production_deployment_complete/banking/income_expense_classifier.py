"""
Income vs Expense Classification Service

This module handles automatic classification of transactions as income or expenses
with detailed categorization and analysis for the MINGUS application.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.models.analytics import TransactionInsight, SpendingCategory
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction type classification"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class IncomeCategory(Enum):
    """Income category classification"""
    SALARY = "salary"
    BONUS = "bonus"
    COMMISSION = "commission"
    INVESTMENT = "investment"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    REFUND = "refund"
    REBATE = "rebate"
    CASHBACK = "cashback"
    GIFT = "gift"
    RENTAL_INCOME = "rental_income"
    BUSINESS_INCOME = "business_income"
    FREELANCE = "freelance"
    SIDE_HUSTLE = "side_hustle"
    OTHER_INCOME = "other_income"


class ExpenseCategory(Enum):
    """Expense category classification"""
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    HOUSING = "housing"
    SUBSCRIPTIONS = "subscriptions"
    INSURANCE = "insurance"
    EDUCATION = "education"
    TRAVEL = "travel"
    PERSONAL_CARE = "personal_care"
    PETS = "pets"
    CHARITY = "charity"
    TAXES = "taxes"
    FEES = "fees"
    OTHER_EXPENSE = "other_expense"


class ClassificationConfidence(Enum):
    """Confidence levels for classification"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of income vs expense classification"""
    transaction_type: TransactionType
    income_category: Optional[IncomeCategory] = None
    expense_category: Optional[ExpenseCategory] = None
    confidence_score: float = 0.0
    classification_confidence: ClassificationConfidence = ClassificationConfidence.UNKNOWN
    classification_method: str = ""
    reasoning: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationSummary:
    """Summary of classification results"""
    total_transactions: int
    income_count: int
    expense_count: int
    transfer_count: int
    unknown_count: int
    
    total_income: float
    total_expenses: float
    net_amount: float
    
    income_categories: Dict[str, Dict[str, Any]]
    expense_categories: Dict[str, Dict[str, Any]]
    
    confidence_distribution: Dict[str, int]
    classification_accuracy: float


class IncomeExpenseClassifier:
    """
    Comprehensive income vs expense classification service
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize classification rules
        self._initialize_classification_rules()
        
        # Initialize income indicators
        self._initialize_income_indicators()
        
        # Initialize expense indicators
        self._initialize_expense_indicators()
        
        # Initialize transfer indicators
        self._initialize_transfer_indicators()
    
    def _initialize_classification_rules(self):
        """Initialize classification rules and thresholds"""
        self.classification_rules = {
            # Amount-based rules
            'amount_thresholds': {
                'positive_threshold': 0.01,  # Amounts above this are likely income
                'negative_threshold': -0.01,  # Amounts below this are likely expenses
                'transfer_threshold': 1000,  # Large amounts are likely transfers
            },
            
            # Confidence thresholds
            'confidence_thresholds': {
                'high_confidence': 0.8,
                'medium_confidence': 0.6,
                'low_confidence': 0.4,
            },
            
            # Classification weights
            'classification_weights': {
                'amount_sign': 0.3,
                'merchant_patterns': 0.25,
                'category_patterns': 0.2,
                'amount_magnitude': 0.15,
                'timing_patterns': 0.1,
            }
        }
    
    def _initialize_income_indicators(self):
        """Initialize income detection indicators"""
        self.income_indicators = {
            # Income keywords
            'income_keywords': [
                'deposit', 'credit', 'salary', 'payroll', 'wage', 'bonus',
                'commission', 'interest', 'dividend', 'refund', 'rebate',
                'cashback', 'gift', 'rental', 'business', 'freelance',
                'payment', 'income', 'earnings', 'revenue', 'profit'
            ],
            
            # Income merchants
            'income_merchants': [
                'employer', 'company', 'corporation', 'inc', 'llc',
                'bank', 'credit union', 'investment', 'brokerage',
                'paypal', 'venmo', 'zelle', 'cash app', 'square',
                'stripe', 'government', 'irs', 'state', 'federal'
            ],
            
            # Income categories
            'income_categories': [
                'income', 'salary', 'bonus', 'investment', 'interest',
                'dividend', 'refund', 'rebate', 'cashback', 'gift'
            ],
            
            # Income patterns
            'income_patterns': [
                r'\b(deposit|credit|payment|income|earnings)\b',
                r'\b(salary|payroll|wage|bonus|commission)\b',
                r'\b(interest|dividend|investment|return)\b',
                r'\b(refund|rebate|cashback|gift)\b',
                r'\b(rental|business|freelance|side\s+hustle)\b'
            ]
        }
    
    def _initialize_expense_indicators(self):
        """Initialize expense detection indicators"""
        self.expense_indicators = {
            # Expense keywords
            'expense_keywords': [
                'purchase', 'payment', 'charge', 'debit', 'withdrawal',
                'fee', 'bill', 'subscription', 'rent', 'mortgage',
                'utility', 'insurance', 'tax', 'service', 'product'
            ],
            
            # Expense merchants
            'expense_merchants': [
                'store', 'shop', 'market', 'restaurant', 'cafe',
                'gas', 'station', 'bank', 'atm', 'utility',
                'insurance', 'medical', 'pharmacy', 'entertainment'
            ],
            
            # Expense categories
            'expense_categories': [
                'food_dining', 'transportation', 'shopping', 'entertainment',
                'healthcare', 'utilities', 'housing', 'subscriptions',
                'insurance', 'education', 'travel', 'personal_care'
            ],
            
            # Expense patterns
            'expense_patterns': [
                r'\b(purchase|payment|charge|debit|withdrawal)\b',
                r'\b(fee|bill|subscription|rent|mortgage)\b',
                r'\b(utility|insurance|tax|service|product)\b',
                r'\b(store|shop|market|restaurant|cafe)\b',
                r'\b(gas|station|bank|atm|medical)\b'
            ]
        }
    
    def _initialize_transfer_indicators(self):
        """Initialize transfer detection indicators"""
        self.transfer_indicators = {
            # Transfer keywords
            'transfer_keywords': [
                'transfer', 'ach', 'wire', 'move money', 'send money',
                'receive money', 'internal transfer', 'account transfer'
            ],
            
            # Transfer merchants
            'transfer_merchants': [
                'bank', 'credit union', 'paypal', 'venmo', 'zelle',
                'cash app', 'square', 'stripe', 'transfer', 'ach'
            ],
            
            # Transfer patterns
            'transfer_patterns': [
                r'\b(transfer|ach|wire|move\s+money|send\s+money)\b',
                r'\b(receive\s+money|internal\s+transfer|account\s+transfer)\b',
                r'\b(bank|credit\s+union|paypal|venmo|zelle)\b'
            ]
        }
    
    def classify_transaction(self, transaction: PlaidTransaction, 
                           merchant_name: str = None) -> ClassificationResult:
        """
        Classify a transaction as income, expense, or transfer
        
        Args:
            transaction: Transaction to classify
            merchant_name: Optional merchant name (if not in transaction)
            
        Returns:
            Classification result with type, category, and confidence
        """
        try:
            amount = float(transaction.amount)
            merchant = merchant_name or transaction.merchant_name or transaction.name or ""
            category = transaction.category or ""
            
            # Step 1: Check amount sign (primary indicator)
            amount_sign_score = self._analyze_amount_sign(amount)
            
            # Step 2: Analyze merchant patterns
            merchant_score = self._analyze_merchant_patterns(merchant, amount)
            
            # Step 3: Analyze category patterns
            category_score = self._analyze_category_patterns(category, amount)
            
            # Step 4: Analyze amount magnitude
            magnitude_score = self._analyze_amount_magnitude(amount)
            
            # Step 5: Analyze timing patterns
            timing_score = self._analyze_timing_patterns(transaction)
            
            # Step 6: Determine classification
            classification = self._determine_classification(
                amount, merchant, category, amount_sign_score, 
                merchant_score, category_score, magnitude_score, timing_score
            )
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Error classifying transaction {transaction.id}: {str(e)}")
            return self._create_fallback_classification(transaction)
    
    def _analyze_amount_sign(self, amount: float) -> Dict[str, float]:
        """Analyze amount sign for classification"""
        if amount > self.classification_rules['amount_thresholds']['positive_threshold']:
            return {
                'income': 0.9,
                'expense': 0.1,
                'transfer': 0.3
            }
        elif amount < self.classification_rules['amount_thresholds']['negative_threshold']:
            return {
                'income': 0.1,
                'expense': 0.9,
                'transfer': 0.3
            }
        else:
            return {
                'income': 0.5,
                'expense': 0.5,
                'transfer': 0.7
            }
    
    def _analyze_merchant_patterns(self, merchant: str, amount: float) -> Dict[str, float]:
        """Analyze merchant patterns for classification"""
        merchant_lower = merchant.lower()
        
        # Check for income indicators
        income_score = 0.0
        for keyword in self.income_indicators['income_keywords']:
            if keyword in merchant_lower:
                income_score += 0.2
        
        for merchant_pattern in self.income_indicators['income_merchants']:
            if merchant_pattern in merchant_lower:
                income_score += 0.3
        
        for pattern in self.income_indicators['income_patterns']:
            if re.search(pattern, merchant_lower, re.IGNORECASE):
                income_score += 0.25
        
        # Check for expense indicators
        expense_score = 0.0
        for keyword in self.expense_indicators['expense_keywords']:
            if keyword in merchant_lower:
                expense_score += 0.2
        
        for merchant_pattern in self.expense_indicators['expense_merchants']:
            if merchant_pattern in merchant_lower:
                expense_score += 0.3
        
        for pattern in self.expense_indicators['expense_patterns']:
            if re.search(pattern, merchant_lower, re.IGNORECASE):
                expense_score += 0.25
        
        # Check for transfer indicators
        transfer_score = 0.0
        for keyword in self.transfer_indicators['transfer_keywords']:
            if keyword in merchant_lower:
                transfer_score += 0.4
        
        for merchant_pattern in self.transfer_indicators['transfer_merchants']:
            if merchant_pattern in merchant_lower:
                transfer_score += 0.3
        
        for pattern in self.transfer_indicators['transfer_patterns']:
            if re.search(pattern, merchant_lower, re.IGNORECASE):
                transfer_score += 0.3
        
        # Normalize scores
        max_score = max(income_score, expense_score, transfer_score)
        if max_score > 0:
            income_score /= max_score
            expense_score /= max_score
            transfer_score /= max_score
        
        return {
            'income': min(income_score, 1.0),
            'expense': min(expense_score, 1.0),
            'transfer': min(transfer_score, 1.0)
        }
    
    def _analyze_category_patterns(self, category: str, amount: float) -> Dict[str, float]:
        """Analyze category patterns for classification"""
        category_lower = category.lower()
        
        # Check for income categories
        income_score = 0.0
        for income_category in self.income_indicators['income_categories']:
            if income_category in category_lower:
                income_score += 0.4
        
        # Check for expense categories
        expense_score = 0.0
        for expense_category in self.expense_indicators['expense_categories']:
            if expense_category in category_lower:
                expense_score += 0.4
        
        # Normalize scores
        max_score = max(income_score, expense_score)
        if max_score > 0:
            income_score /= max_score
            expense_score /= max_score
        
        return {
            'income': min(income_score, 1.0),
            'expense': min(expense_score, 1.0),
            'transfer': 0.0  # Categories don't typically indicate transfers
        }
    
    def _analyze_amount_magnitude(self, amount: float) -> Dict[str, float]:
        """Analyze amount magnitude for classification"""
        abs_amount = abs(amount)
        transfer_threshold = self.classification_rules['amount_thresholds']['transfer_threshold']
        
        # Large amounts are more likely to be transfers
        if abs_amount > transfer_threshold:
            return {
                'income': 0.3,
                'expense': 0.3,
                'transfer': 0.7
            }
        else:
            return {
                'income': 0.5,
                'expense': 0.5,
                'transfer': 0.2
            }
    
    def _analyze_timing_patterns(self, transaction: PlaidTransaction) -> Dict[str, float]:
        """Analyze timing patterns for classification"""
        # This could be enhanced with more sophisticated timing analysis
        # For now, return neutral scores
        return {
            'income': 0.5,
            'expense': 0.5,
            'transfer': 0.5
        }
    
    def _determine_classification(self, amount: float, merchant: str, category: str,
                                amount_sign_score: Dict[str, float],
                                merchant_score: Dict[str, float],
                                category_score: Dict[str, float],
                                magnitude_score: Dict[str, float],
                                timing_score: Dict[str, float]) -> ClassificationResult:
        """Determine final classification based on all factors"""
        
        # Calculate weighted scores
        weights = self.classification_rules['classification_weights']
        
        income_score = (
            amount_sign_score['income'] * weights['amount_sign'] +
            merchant_score['income'] * weights['merchant_patterns'] +
            category_score['income'] * weights['category_patterns'] +
            magnitude_score['income'] * weights['amount_magnitude'] +
            timing_score['income'] * weights['timing_patterns']
        )
        
        expense_score = (
            amount_sign_score['expense'] * weights['amount_sign'] +
            merchant_score['expense'] * weights['merchant_patterns'] +
            category_score['expense'] * weights['category_patterns'] +
            magnitude_score['expense'] * weights['amount_magnitude'] +
            timing_score['expense'] * weights['timing_patterns']
        )
        
        transfer_score = (
            amount_sign_score['transfer'] * weights['amount_sign'] +
            merchant_score['transfer'] * weights['merchant_patterns'] +
            category_score['transfer'] * weights['category_patterns'] +
            magnitude_score['transfer'] * weights['amount_magnitude'] +
            timing_score['transfer'] * weights['timing_patterns']
        )
        
        # Determine transaction type
        scores = {
            'income': income_score,
            'expense': expense_score,
            'transfer': transfer_score
        }
        
        transaction_type = max(scores, key=scores.get)
        confidence_score = scores[transaction_type]
        
        # Determine specific category
        income_category = None
        expense_category = None
        
        if transaction_type == TransactionType.INCOME:
            income_category = self._determine_income_category(amount, merchant, category)
        elif transaction_type == TransactionType.EXPENSE:
            expense_category = self._determine_expense_category(amount, merchant, category)
        
        # Build reasoning
        reasoning = []
        if amount > 0:
            reasoning.append("Positive amount indicates potential income")
        elif amount < 0:
            reasoning.append("Negative amount indicates potential expense")
        
        if merchant_score['income'] > 0.5:
            reasoning.append("Merchant patterns suggest income")
        elif merchant_score['expense'] > 0.5:
            reasoning.append("Merchant patterns suggest expense")
        elif merchant_score['transfer'] > 0.5:
            reasoning.append("Merchant patterns suggest transfer")
        
        if category_score['income'] > 0.5:
            reasoning.append("Category patterns suggest income")
        elif category_score['expense'] > 0.5:
            reasoning.append("Category patterns suggest expense")
        
        if magnitude_score['transfer'] > 0.5:
            reasoning.append("Large amount suggests transfer")
        
        return ClassificationResult(
            transaction_type=TransactionType(transaction_type),
            income_category=income_category,
            expense_category=expense_category,
            confidence_score=confidence_score,
            classification_confidence=self._get_confidence_level(confidence_score),
            classification_method="multi_factor_analysis",
            reasoning=reasoning,
            metadata={
                'scores': scores,
                'amount': amount,
                'merchant': merchant,
                'category': category
            }
        )
    
    def _determine_income_category(self, amount: float, merchant: str, category: str) -> IncomeCategory:
        """Determine specific income category"""
        merchant_lower = merchant.lower()
        category_lower = category.lower()
        
        # Salary indicators
        if any(keyword in merchant_lower for keyword in ['employer', 'company', 'corporation', 'payroll']):
            return IncomeCategory.SALARY
        
        if 'salary' in category_lower or 'payroll' in category_lower:
            return IncomeCategory.SALARY
        
        # Bonus indicators
        if 'bonus' in merchant_lower or 'bonus' in category_lower:
            return IncomeCategory.BONUS
        
        # Investment indicators
        if any(keyword in merchant_lower for keyword in ['investment', 'brokerage', 'dividend']):
            return IncomeCategory.INVESTMENT
        
        if 'dividend' in category_lower:
            return IncomeCategory.DIVIDEND
        
        # Interest indicators
        if 'interest' in merchant_lower or 'interest' in category_lower:
            return IncomeCategory.INTEREST
        
        # Refund indicators
        if any(keyword in merchant_lower for keyword in ['refund', 'return', 'rebate']):
            return IncomeCategory.REFUND
        
        # Cashback indicators
        if 'cashback' in merchant_lower or 'cashback' in category_lower:
            return IncomeCategory.CASHBACK
        
        # Gift indicators
        if 'gift' in merchant_lower or 'gift' in category_lower:
            return IncomeCategory.GIFT
        
        # Rental income indicators
        if 'rental' in merchant_lower or 'rental' in category_lower:
            return IncomeCategory.RENTAL_INCOME
        
        # Business income indicators
        if any(keyword in merchant_lower for keyword in ['business', 'freelance', 'consulting']):
            return IncomeCategory.BUSINESS_INCOME
        
        # Default to other income
        return IncomeCategory.OTHER_INCOME
    
    def _determine_expense_category(self, amount: float, merchant: str, category: str) -> ExpenseCategory:
        """Determine specific expense category"""
        merchant_lower = merchant.lower()
        category_lower = category.lower()
        
        # Use existing category if it's a valid expense category
        if category_lower in [cat.value for cat in ExpenseCategory]:
            return ExpenseCategory(category_lower)
        
        # Food and dining indicators
        if any(keyword in merchant_lower for keyword in ['restaurant', 'cafe', 'food', 'dining']):
            return ExpenseCategory.FOOD_DINING
        
        # Transportation indicators
        if any(keyword in merchant_lower for keyword in ['gas', 'station', 'uber', 'lyft', 'transport']):
            return ExpenseCategory.TRANSPORTATION
        
        # Shopping indicators
        if any(keyword in merchant_lower for keyword in ['store', 'shop', 'market', 'retail']):
            return ExpenseCategory.SHOPPING
        
        # Entertainment indicators
        if any(keyword in merchant_lower for keyword in ['movie', 'theater', 'entertainment', 'game']):
            return ExpenseCategory.ENTERTAINMENT
        
        # Healthcare indicators
        if any(keyword in merchant_lower for keyword in ['medical', 'pharmacy', 'doctor', 'hospital']):
            return ExpenseCategory.HEALTHCARE
        
        # Utilities indicators
        if any(keyword in merchant_lower for keyword in ['utility', 'electric', 'gas', 'water', 'internet']):
            return ExpenseCategory.UTILITIES
        
        # Housing indicators
        if any(keyword in merchant_lower for keyword in ['rent', 'mortgage', 'housing', 'property']):
            return ExpenseCategory.HOUSING
        
        # Subscription indicators
        if any(keyword in merchant_lower for keyword in ['subscription', 'monthly', 'service']):
            return ExpenseCategory.SUBSCRIPTIONS
        
        # Insurance indicators
        if 'insurance' in merchant_lower:
            return ExpenseCategory.INSURANCE
        
        # Education indicators
        if any(keyword in merchant_lower for keyword in ['education', 'school', 'university', 'course']):
            return ExpenseCategory.EDUCATION
        
        # Travel indicators
        if any(keyword in merchant_lower for keyword in ['travel', 'hotel', 'airline', 'vacation']):
            return ExpenseCategory.TRAVEL
        
        # Personal care indicators
        if any(keyword in merchant_lower for keyword in ['salon', 'spa', 'beauty', 'gym']):
            return ExpenseCategory.PERSONAL_CARE
        
        # Pet indicators
        if any(keyword in merchant_lower for keyword in ['pet', 'veterinary', 'animal']):
            return ExpenseCategory.PETS
        
        # Charity indicators
        if any(keyword in merchant_lower for keyword in ['charity', 'donation', 'nonprofit']):
            return ExpenseCategory.CHARITY
        
        # Tax indicators
        if any(keyword in merchant_lower for keyword in ['tax', 'irs', 'government']):
            return ExpenseCategory.TAXES
        
        # Fee indicators
        if any(keyword in merchant_lower for keyword in ['fee', 'charge', 'atm']):
            return ExpenseCategory.FEES
        
        # Default to other expense
        return ExpenseCategory.OTHER_EXPENSE
    
    def _get_confidence_level(self, confidence_score: float) -> ClassificationConfidence:
        """Convert confidence score to confidence level"""
        thresholds = self.classification_rules['confidence_thresholds']
        
        if confidence_score >= thresholds['high_confidence']:
            return ClassificationConfidence.HIGH
        elif confidence_score >= thresholds['medium_confidence']:
            return ClassificationConfidence.MEDIUM
        elif confidence_score >= thresholds['low_confidence']:
            return ClassificationConfidence.LOW
        else:
            return ClassificationConfidence.UNKNOWN
    
    def _create_fallback_classification(self, transaction: PlaidTransaction) -> ClassificationResult:
        """Create fallback classification when processing fails"""
        amount = float(transaction.amount)
        
        if amount > 0:
            transaction_type = TransactionType.INCOME
            income_category = IncomeCategory.OTHER_INCOME
            expense_category = None
        elif amount < 0:
            transaction_type = TransactionType.EXPENSE
            income_category = None
            expense_category = ExpenseCategory.OTHER_EXPENSE
        else:
            transaction_type = TransactionType.TRANSFER
            income_category = None
            expense_category = None
        
        return ClassificationResult(
            transaction_type=transaction_type,
            income_category=income_category,
            expense_category=expense_category,
            confidence_score=0.1,
            classification_confidence=ClassificationConfidence.UNKNOWN,
            classification_method="fallback",
            reasoning=["Fallback classification due to processing error"],
            metadata={'fallback': True}
        )
    
    def batch_classify_transactions(self, transactions: List[PlaidTransaction]) -> List[ClassificationResult]:
        """Classify multiple transactions in batch"""
        results = []
        
        for transaction in transactions:
            try:
                classification = self.classify_transaction(transaction)
                results.append(classification)
            except Exception as e:
                self.logger.error(f"Error classifying transaction {transaction.id}: {str(e)}")
                results.append(self._create_fallback_classification(transaction))
        
        return results
    
    def classify_user_transactions(self, user_id: int, account_ids: List[str] = None,
                                 date_range: Tuple[datetime, datetime] = None) -> ClassificationSummary:
        """
        Classify all transactions for a user and generate summary
        
        Args:
            user_id: User ID to classify transactions for
            account_ids: Specific account IDs to classify (None for all)
            date_range: Date range to classify (None for last 90 days)
            
        Returns:
            Classification summary with statistics and breakdowns
        """
        try:
            # Get transactions
            query = self.db_session.query(PlaidTransaction).filter(
                PlaidTransaction.user_id == user_id
            )
            
            if account_ids:
                query = query.filter(PlaidTransaction.account_id.in_(account_ids))
            
            if date_range:
                query = query.filter(
                    PlaidTransaction.date.between(date_range[0], date_range[1])
                )
            else:
                # Default to last 90 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                query = query.filter(
                    PlaidTransaction.date.between(start_date, end_date)
                )
            
            transactions = query.all()
            
            if not transactions:
                return self._create_empty_summary()
            
            # Classify transactions
            classifications = self.batch_classify_transactions(transactions)
            
            # Generate summary
            return self._generate_classification_summary(transactions, classifications)
            
        except Exception as e:
            self.logger.error(f"Error classifying user transactions: {str(e)}")
            return self._create_empty_summary()
    
    def _generate_classification_summary(self, transactions: List[PlaidTransaction],
                                       classifications: List[ClassificationResult]) -> ClassificationSummary:
        """Generate classification summary from transactions and classifications"""
        
        # Initialize counters
        type_counts = Counter()
        income_categories = Counter()
        expense_categories = Counter()
        confidence_distribution = Counter()
        
        total_income = 0.0
        total_expenses = 0.0
        
        # Process each transaction
        for transaction, classification in zip(transactions, classifications):
            amount = float(transaction.amount)
            
            # Count transaction types
            type_counts[classification.transaction_type.value] += 1
            
            # Count confidence levels
            confidence_distribution[classification.classification_confidence.value] += 1
            
            # Calculate totals
            if classification.transaction_type == TransactionType.INCOME:
                total_income += amount
                if classification.income_category:
                    income_categories[classification.income_category.value] += 1
            elif classification.transaction_type == TransactionType.EXPENSE:
                total_expenses += abs(amount)
                if classification.expense_category:
                    expense_categories[classification.expense_category.value] += 1
        
        # Calculate net amount
        net_amount = total_income - total_expenses
        
        # Calculate classification accuracy (simplified)
        high_confidence_count = confidence_distribution.get(ClassificationConfidence.HIGH.value, 0)
        medium_confidence_count = confidence_distribution.get(ClassificationConfidence.MEDIUM.value, 0)
        total_transactions = len(transactions)
        
        classification_accuracy = (
            (high_confidence_count * 1.0 + medium_confidence_count * 0.7) / total_transactions
        ) if total_transactions > 0 else 0.0
        
        # Format category breakdowns
        income_categories_data = {}
        for category, count in income_categories.items():
            income_categories_data[category] = {
                'count': count,
                'percentage': (count / type_counts[TransactionType.INCOME.value] * 100) 
                             if type_counts[TransactionType.INCOME.value] > 0 else 0
            }
        
        expense_categories_data = {}
        for category, count in expense_categories.items():
            expense_categories_data[category] = {
                'count': count,
                'percentage': (count / type_counts[TransactionType.EXPENSE.value] * 100) 
                             if type_counts[TransactionType.EXPENSE.value] > 0 else 0
            }
        
        return ClassificationSummary(
            total_transactions=total_transactions,
            income_count=type_counts.get(TransactionType.INCOME.value, 0),
            expense_count=type_counts.get(TransactionType.EXPENSE.value, 0),
            transfer_count=type_counts.get(TransactionType.TRANSFER.value, 0),
            unknown_count=type_counts.get(TransactionType.UNKNOWN.value, 0),
            total_income=total_income,
            total_expenses=total_expenses,
            net_amount=net_amount,
            income_categories=income_categories_data,
            expense_categories=expense_categories_data,
            confidence_distribution=dict(confidence_distribution),
            classification_accuracy=classification_accuracy
        )
    
    def _create_empty_summary(self) -> ClassificationSummary:
        """Create empty classification summary"""
        return ClassificationSummary(
            total_transactions=0,
            income_count=0,
            expense_count=0,
            transfer_count=0,
            unknown_count=0,
            total_income=0.0,
            total_expenses=0.0,
            net_amount=0.0,
            income_categories={},
            expense_categories={},
            confidence_distribution={},
            classification_accuracy=0.0
        )
    
    def save_classifications_to_database(self, transactions: List[PlaidTransaction],
                                       classifications: List[ClassificationResult]) -> bool:
        """Save classification results to database"""
        try:
            for transaction, classification in zip(transactions, classifications):
                # Update transaction with classification data
                transaction.transaction_type = classification.transaction_type.value
                transaction.income_category = classification.income_category.value if classification.income_category else None
                transaction.expense_category = classification.expense_category.value if classification.expense_category else None
                transaction.classification_confidence = classification.confidence_score
                transaction.classification_method = classification.classification_method
                transaction.classification_reasoning = json.dumps(classification.reasoning)
                transaction.classification_metadata = json.dumps(classification.metadata)
                
                # Create or update transaction insight
                insight = self.db_session.query(TransactionInsight).filter(
                    TransactionInsight.transaction_id == str(transaction.id)
                ).first()
                
                if insight:
                    # Update existing insight
                    insight.transaction_type = classification.transaction_type.value
                    insight.category = classification.income_category.value if classification.income_category else classification.expense_category.value
                    insight.confidence = classification.confidence_score
                    insight.insights = json.dumps(classification.reasoning)
                    insight.updated_at = datetime.now()
                else:
                    # Create new insight
                    insight = TransactionInsight(
                        transaction_id=str(transaction.id),
                        user_id=transaction.user_id,
                        account_id=transaction.account_id,
                        category=classification.income_category.value if classification.income_category else classification.expense_category.value,
                        confidence=classification.confidence_score,
                        transaction_type=classification.transaction_type.value,
                        merchant_name=transaction.merchant_name,
                        insights=json.dumps(classification.reasoning),
                        tags=json.dumps([classification.transaction_type.value]),
                        created_at=datetime.now()
                    )
                    self.db_session.add(insight)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving classifications to database: {str(e)}")
            self.db_session.rollback()
            return False 