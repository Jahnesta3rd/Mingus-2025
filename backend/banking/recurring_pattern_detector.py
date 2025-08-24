"""
Recurring Transaction Pattern Detection Service

This module handles detection and analysis of recurring transaction patterns
for transaction processing in the MINGUS application.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.models.analytics import SpendingPattern
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class RecurringType(Enum):
    """Types of recurring transactions"""
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class PatternConfidence(Enum):
    """Confidence levels for pattern detection"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class RecurringPattern:
    """Detected recurring transaction pattern"""
    pattern_id: str
    user_id: int
    account_id: str
    merchant_name: str
    category: str
    subcategory: Optional[str] = None
    
    # Pattern characteristics
    recurring_type: RecurringType
    frequency: int  # Number of occurrences
    average_amount: float
    amount_variance: float
    total_amount: float
    
    # Timing information
    first_occurrence: datetime
    last_occurrence: datetime
    next_predicted: Optional[datetime] = None
    
    # Pattern analysis
    confidence_score: float
    pattern_confidence: PatternConfidence
    is_active: bool = True
    is_subscription: bool = False
    
    # Additional metadata
    transaction_ids: List[str] = field(default_factory=list)
    day_of_week: Optional[int] = None  # 0-6 (Monday-Sunday)
    day_of_month: Optional[int] = None  # 1-31
    month_of_year: Optional[int] = None  # 1-12
    hour_of_day: Optional[int] = None  # 0-23
    
    # Pattern metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    pattern: RecurringPattern
    match_score: float
    matched_transactions: List[str]
    confidence: float


class RecurringPatternDetector:
    """
    Comprehensive recurring transaction pattern detection service
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize detection parameters
        self._initialize_detection_parameters()
        
        # Initialize pattern rules
        self._initialize_pattern_rules()
        
        # Initialize subscription indicators
        self._initialize_subscription_indicators()
    
    def _initialize_detection_parameters(self):
        """Initialize pattern detection parameters"""
        self.detection_params = {
            # Minimum requirements for pattern detection
            'min_occurrences': 3,  # Minimum transactions to consider a pattern
            'min_confidence': 0.6,  # Minimum confidence score
            'max_amount_variance': 0.3,  # Maximum allowed variance in amounts
            'max_date_variance_days': 7,  # Maximum variance in transaction dates
            
            # Time windows for pattern analysis
            'analysis_window_days': 365,  # Days to look back for patterns
            'pattern_validation_days': 90,  # Days to validate pattern consistency
            
            # Frequency detection thresholds
            'monthly_threshold': 25,  # Days between transactions for monthly
            'weekly_threshold': 7,  # Days between transactions for weekly
            'biweekly_threshold': 14,  # Days between transactions for biweekly
            'quarterly_threshold': 85,  # Days between transactions for quarterly
            'annual_threshold': 350,  # Days between transactions for annual
            
            # Amount similarity thresholds
            'amount_similarity_threshold': 0.8,  # Minimum similarity for amounts
            'amount_tolerance_percentage': 0.1,  # 10% tolerance for amount variations
        }
    
    def _initialize_pattern_rules(self):
        """Initialize pattern detection rules"""
        self.pattern_rules = {
            # Subscription indicators
            'subscription_keywords': [
                'subscription', 'monthly', 'recurring', 'auto-pay', 'automatic',
                'billing', 'payment', 'service', 'membership', 'premium'
            ],
            
            # High-confidence subscription merchants
            'subscription_merchants': [
                'netflix', 'spotify', 'hulu', 'disney', 'amazon prime',
                'youtube premium', 'adobe', 'microsoft', 'google',
                'dropbox', 'box', 'slack', 'zoom', 'github'
            ],
            
            # Utility and service providers
            'utility_merchants': [
                'comcast', 'verizon', 'at&t', 'spectrum', 'xfinity',
                'electric', 'gas', 'water', 'internet', 'phone'
            ],
            
            # Financial services
            'financial_merchants': [
                'chase', 'wells fargo', 'bank of america', 'citibank',
                'credit card', 'loan', 'mortgage', 'insurance'
            ],
            
            # Healthcare and insurance
            'healthcare_merchants': [
                'blue cross', 'aetna', 'united health', 'kaiser',
                'pharmacy', 'medical', 'dental', 'vision'
            ]
        }
    
    def _initialize_subscription_indicators(self):
        """Initialize subscription detection indicators"""
        self.subscription_indicators = {
            # Amount patterns typical of subscriptions
            'subscription_amount_patterns': [
                {'min': 5, 'max': 50, 'confidence': 0.7},  # Low-cost subscriptions
                {'min': 10, 'max': 100, 'confidence': 0.8},  # Medium-cost subscriptions
                {'min': 50, 'max': 500, 'confidence': 0.6},  # High-cost subscriptions
            ],
            
            # Timing patterns typical of subscriptions
            'subscription_timing_patterns': [
                {'type': RecurringType.MONTHLY, 'confidence': 0.9},
                {'type': RecurringType.QUARTERLY, 'confidence': 0.7},
                {'type': RecurringType.ANNUALLY, 'confidence': 0.6},
            ],
            
            # Category patterns typical of subscriptions
            'subscription_categories': [
                'entertainment', 'software', 'utilities', 'healthcare',
                'subscriptions', 'memberships', 'services'
            ]
        }
    
    def detect_recurring_patterns(self, user_id: int, account_ids: List[str] = None,
                                date_range: Tuple[datetime, datetime] = None,
                                min_confidence: float = None) -> List[RecurringPattern]:
        """
        Detect recurring transaction patterns for a user
        
        Args:
            user_id: User ID to analyze
            account_ids: Specific account IDs to analyze (None for all)
            date_range: Date range to analyze (None for last year)
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected recurring patterns
        """
        try:
            self.logger.info(f"Starting recurring pattern detection for user {user_id}")
            
            # Set default parameters
            if min_confidence is None:
                min_confidence = self.detection_params['min_confidence']
            
            if date_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=self.detection_params['analysis_window_days'])
                date_range = (start_date, end_date)
            
            # Get transactions for analysis
            transactions = self._get_transactions_for_analysis(user_id, account_ids, date_range)
            
            if not transactions:
                self.logger.info(f"No transactions found for user {user_id}")
                return []
            
            # Group transactions by merchant and category
            transaction_groups = self._group_transactions(transactions)
            
            # Detect patterns in each group
            detected_patterns = []
            
            for group_key, group_transactions in transaction_groups.items():
                if len(group_transactions) < self.detection_params['min_occurrences']:
                    continue
                
                pattern = self._analyze_transaction_group(group_key, group_transactions)
                
                if pattern and pattern.confidence_score >= min_confidence:
                    detected_patterns.append(pattern)
            
            # Sort patterns by confidence and frequency
            detected_patterns.sort(key=lambda p: (p.confidence_score, p.frequency), reverse=True)
            
            self.logger.info(f"Detected {len(detected_patterns)} recurring patterns for user {user_id}")
            
            return detected_patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting recurring patterns for user {user_id}: {str(e)}")
            return []
    
    def _get_transactions_for_analysis(self, user_id: int, account_ids: List[str] = None,
                                     date_range: Tuple[datetime, datetime] = None) -> List[PlaidTransaction]:
        """Get transactions for pattern analysis"""
        query = self.db_session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == user_id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if date_range:
            query = query.filter(
                PlaidTransaction.date.between(date_range[0], date_range[1])
            )
        
        # Order by date for pattern analysis
        return query.order_by(PlaidTransaction.date.asc()).all()
    
    def _group_transactions(self, transactions: List[PlaidTransaction]) -> Dict[str, List[PlaidTransaction]]:
        """Group transactions by merchant and category for pattern analysis"""
        groups = defaultdict(list)
        
        for tx in transactions:
            # Create group key based on merchant name and category
            merchant_name = tx.merchant_name or tx.name or "Unknown"
            category = tx.category or "other"
            
            # Normalize merchant name for grouping
            normalized_merchant = self._normalize_merchant_for_grouping(merchant_name)
            
            group_key = f"{normalized_merchant}|{category}"
            groups[group_key].append(tx)
        
        return dict(groups)
    
    def _normalize_merchant_for_grouping(self, merchant_name: str) -> str:
        """Normalize merchant name for grouping transactions"""
        if not merchant_name:
            return "Unknown"
        
        # Convert to lowercase and remove common variations
        normalized = merchant_name.lower().strip()
        
        # Remove common suffixes that don't affect grouping
        suffixes_to_remove = [
            ' inc', ' corp', ' llc', ' ltd', ' co', ' company',
            ' store', ' shop', ' market', ' restaurant', ' cafe'
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        return normalized.strip()
    
    def _analyze_transaction_group(self, group_key: str, transactions: List[PlaidTransaction]) -> Optional[RecurringPattern]:
        """Analyze a group of transactions for recurring patterns"""
        if len(transactions) < self.detection_params['min_occurrences']:
            return None
        
        # Sort transactions by date
        transactions.sort(key=lambda tx: tx.date)
        
        # Extract group information
        merchant_name, category = group_key.split('|', 1)
        
        # Analyze timing patterns
        timing_analysis = self._analyze_timing_patterns(transactions)
        
        # Analyze amount patterns
        amount_analysis = self._analyze_amount_patterns(transactions)
        
        # Determine if pattern is significant
        if not self._is_significant_pattern(timing_analysis, amount_analysis):
            return None
        
        # Determine recurring type
        recurring_type = self._determine_recurring_type(timing_analysis)
        
        # Calculate confidence score
        confidence_score = self._calculate_pattern_confidence(timing_analysis, amount_analysis, transactions)
        
        # Determine if it's a subscription
        is_subscription = self._is_subscription_pattern(merchant_name, category, amount_analysis, recurring_type)
        
        # Create pattern object
        pattern = RecurringPattern(
            pattern_id=self._generate_pattern_id(group_key, transactions[0].user_id),
            user_id=transactions[0].user_id,
            account_id=transactions[0].account_id,
            merchant_name=merchant_name,
            category=category,
            recurring_type=recurring_type,
            frequency=len(transactions),
            average_amount=amount_analysis['average'],
            amount_variance=amount_analysis['variance'],
            total_amount=amount_analysis['total'],
            first_occurrence=transactions[0].date,
            last_occurrence=transactions[-1].date,
            next_predicted=self._predict_next_occurrence(transactions, recurring_type),
            confidence_score=confidence_score,
            pattern_confidence=self._get_confidence_level(confidence_score),
            is_active=self._is_pattern_active(transactions),
            is_subscription=is_subscription,
            transaction_ids=[str(tx.id) for tx in transactions],
            day_of_week=timing_analysis.get('day_of_week'),
            day_of_month=timing_analysis.get('day_of_month'),
            month_of_year=timing_analysis.get('month_of_year'),
            hour_of_day=timing_analysis.get('hour_of_day'),
            metadata={
                'timing_analysis': timing_analysis,
                'amount_analysis': amount_analysis,
                'group_key': group_key
            }
        )
        
        return pattern
    
    def _analyze_timing_patterns(self, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Analyze timing patterns in transactions"""
        if len(transactions) < 2:
            return {}
        
        # Calculate intervals between transactions
        intervals = []
        for i in range(1, len(transactions)):
            interval = (transactions[i].date - transactions[i-1].date).days
            intervals.append(interval)
        
        # Analyze day patterns
        days_of_week = [tx.date.weekday() for tx in transactions]
        days_of_month = [tx.date.day for tx in transactions]
        months_of_year = [tx.date.month for tx in transactions]
        
        # Find most common patterns
        day_of_week_mode = self._get_mode(days_of_week) if days_of_week else None
        day_of_month_mode = self._get_mode(days_of_month) if days_of_month else None
        month_of_year_mode = self._get_mode(months_of_year) if months_of_year else None
        
        # Calculate timing statistics
        avg_interval = statistics.mean(intervals) if intervals else 0
        interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        
        return {
            'intervals': intervals,
            'average_interval': avg_interval,
            'interval_variance': interval_variance,
            'day_of_week': day_of_week_mode,
            'day_of_month': day_of_month_mode,
            'month_of_year': month_of_year_mode,
            'day_of_week_consistency': self._calculate_consistency(days_of_week),
            'day_of_month_consistency': self._calculate_consistency(days_of_month),
            'month_of_year_consistency': self._calculate_consistency(months_of_year)
        }
    
    def _analyze_amount_patterns(self, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Analyze amount patterns in transactions"""
        amounts = [abs(float(tx.amount)) for tx in transactions]
        
        # Calculate amount statistics
        average_amount = statistics.mean(amounts)
        total_amount = sum(amounts)
        
        # Calculate variance and standard deviation
        if len(amounts) > 1:
            variance = statistics.variance(amounts)
            std_dev = statistics.stdev(amounts)
        else:
            variance = 0
            std_dev = 0
        
        # Calculate coefficient of variation (CV) for relative variability
        cv = (std_dev / average_amount) if average_amount > 0 else 0
        
        # Check for amount consistency
        is_consistent = cv <= self.detection_params['max_amount_variance']
        
        return {
            'amounts': amounts,
            'average': average_amount,
            'total': total_amount,
            'variance': variance,
            'std_dev': std_dev,
            'coefficient_of_variation': cv,
            'is_consistent': is_consistent,
            'min_amount': min(amounts),
            'max_amount': max(amounts)
        }
    
    def _is_significant_pattern(self, timing_analysis: Dict[str, Any], 
                              amount_analysis: Dict[str, Any]) -> bool:
        """Determine if a pattern is statistically significant"""
        # Check amount consistency
        if not amount_analysis.get('is_consistent', False):
            return False
        
        # Check timing consistency
        interval_variance = timing_analysis.get('interval_variance', float('inf'))
        if interval_variance > (self.detection_params['max_date_variance_days'] ** 2):
            return False
        
        # Check minimum occurrences
        if len(timing_analysis.get('intervals', [])) + 1 < self.detection_params['min_occurrences']:
            return False
        
        return True
    
    def _determine_recurring_type(self, timing_analysis: Dict[str, Any]) -> RecurringType:
        """Determine the type of recurring pattern"""
        avg_interval = timing_analysis.get('average_interval', 0)
        
        if avg_interval <= self.detection_params['weekly_threshold']:
            return RecurringType.WEEKLY
        elif avg_interval <= self.detection_params['biweekly_threshold']:
            return RecurringType.BIWEEKLY
        elif avg_interval <= self.detection_params['monthly_threshold']:
            return RecurringType.MONTHLY
        elif avg_interval <= self.detection_params['quarterly_threshold']:
            return RecurringType.QUARTERLY
        elif avg_interval <= self.detection_params['annual_threshold']:
            return RecurringType.ANNUALLY
        else:
            return RecurringType.CUSTOM
    
    def _calculate_pattern_confidence(self, timing_analysis: Dict[str, Any], 
                                    amount_analysis: Dict[str, Any],
                                    transactions: List[PlaidTransaction]) -> float:
        """Calculate confidence score for a pattern"""
        confidence_factors = []
        
        # Amount consistency factor (0-1)
        cv = amount_analysis.get('coefficient_of_variation', 1.0)
        amount_confidence = max(0, 1 - (cv / self.detection_params['max_amount_variance']))
        confidence_factors.append(amount_confidence)
        
        # Timing consistency factor (0-1)
        interval_variance = timing_analysis.get('interval_variance', float('inf'))
        max_variance = self.detection_params['max_date_variance_days'] ** 2
        timing_confidence = max(0, 1 - (interval_variance / max_variance))
        confidence_factors.append(timing_confidence)
        
        # Frequency factor (0-1)
        frequency = len(transactions)
        frequency_confidence = min(1.0, frequency / 10)  # Max confidence at 10+ occurrences
        confidence_factors.append(frequency_confidence)
        
        # Day consistency factors
        day_consistency = timing_analysis.get('day_of_week_consistency', 0)
        confidence_factors.append(day_consistency)
        
        month_consistency = timing_analysis.get('day_of_month_consistency', 0)
        confidence_factors.append(month_consistency)
        
        # Calculate weighted average
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]  # Weights for each factor
        weighted_confidence = sum(factor * weight for factor, weight in zip(confidence_factors, weights))
        
        return min(1.0, weighted_confidence)
    
    def _is_subscription_pattern(self, merchant_name: str, category: str,
                               amount_analysis: Dict[str, Any],
                               recurring_type: RecurringType) -> bool:
        """Determine if a pattern represents a subscription"""
        # Check merchant name for subscription indicators
        merchant_lower = merchant_name.lower()
        if any(keyword in merchant_lower for keyword in self.pattern_rules['subscription_keywords']):
            return True
        
        # Check if merchant is known subscription provider
        if any(merchant in merchant_lower for merchant in self.pattern_rules['subscription_merchants']):
            return True
        
        # Check category
        if category in self.subscription_indicators['subscription_categories']:
            return True
        
        # Check amount patterns
        avg_amount = amount_analysis.get('average', 0)
        for pattern in self.subscription_indicators['subscription_amount_patterns']:
            if pattern['min'] <= avg_amount <= pattern['max']:
                return True
        
        # Check timing patterns
        for pattern in self.subscription_indicators['subscription_timing_patterns']:
            if pattern['type'] == recurring_type:
                return True
        
        return False
    
    def _predict_next_occurrence(self, transactions: List[PlaidTransaction], 
                               recurring_type: RecurringType) -> Optional[datetime]:
        """Predict the next occurrence of a recurring pattern"""
        if len(transactions) < 2:
            return None
        
        # Calculate average interval
        intervals = []
        for i in range(1, len(transactions)):
            interval = (transactions[i].date - transactions[i-1].date).days
            intervals.append(interval)
        
        avg_interval = statistics.mean(intervals)
        last_date = transactions[-1].date
        
        # Predict next occurrence
        next_date = last_date + timedelta(days=avg_interval)
        
        # Adjust for specific recurring types
        if recurring_type == RecurringType.MONTHLY:
            # Try to maintain same day of month
            day_of_month = last_date.day
            next_date = self._adjust_to_day_of_month(next_date, day_of_month)
        elif recurring_type == RecurringType.WEEKLY:
            # Maintain same day of week
            day_of_week = last_date.weekday()
            next_date = self._adjust_to_day_of_week(next_date, day_of_week)
        
        return next_date
    
    def _adjust_to_day_of_month(self, date: datetime, target_day: int) -> datetime:
        """Adjust date to target day of month"""
        try:
            return date.replace(day=target_day)
        except ValueError:
            # Handle cases where target day doesn't exist in the month
            return date
    
    def _adjust_to_day_of_week(self, date: datetime, target_day: int) -> datetime:
        """Adjust date to target day of week"""
        current_day = date.weekday()
        days_diff = target_day - current_day
        return date + timedelta(days=days_diff)
    
    def _is_pattern_active(self, transactions: List[PlaidTransaction]) -> bool:
        """Determine if a pattern is still active"""
        if not transactions:
            return False
        
        # Check if last transaction is recent (within 2x the average interval)
        last_date = transactions[-1].date
        current_date = datetime.now()
        
        # Calculate average interval
        if len(transactions) >= 2:
            intervals = []
            for i in range(1, len(transactions)):
                interval = (transactions[i].date - transactions[i-1].date).days
                intervals.append(interval)
            avg_interval = statistics.mean(intervals)
        else:
            avg_interval = 30  # Default to monthly
        
        # Pattern is active if last transaction is within 2x the average interval
        days_since_last = (current_date - last_date).days
        return days_since_last <= (avg_interval * 2)
    
    def _get_confidence_level(self, confidence_score: float) -> PatternConfidence:
        """Convert confidence score to confidence level"""
        if confidence_score >= 0.8:
            return PatternConfidence.HIGH
        elif confidence_score >= 0.6:
            return PatternConfidence.MEDIUM
        elif confidence_score >= 0.4:
            return PatternConfidence.LOW
        else:
            return PatternConfidence.UNKNOWN
    
    def _generate_pattern_id(self, group_key: str, user_id: int) -> str:
        """Generate unique pattern ID"""
        import hashlib
        pattern_string = f"{user_id}_{group_key}_{datetime.now().isoformat()}"
        return hashlib.md5(pattern_string.encode()).hexdigest()
    
    def _get_mode(self, values: List[Any]) -> Optional[Any]:
        """Get the mode (most common value) from a list"""
        if not values:
            return None
        
        counter = Counter(values)
        return counter.most_common(1)[0][0]
    
    def _calculate_consistency(self, values: List[Any]) -> float:
        """Calculate consistency of values (0-1)"""
        if not values:
            return 0.0
        
        counter = Counter(values)
        most_common_count = counter.most_common(1)[0][1]
        return most_common_count / len(values)
    
    def save_patterns_to_database(self, patterns: List[RecurringPattern]) -> bool:
        """Save detected patterns to database"""
        try:
            for pattern in patterns:
                # Check if pattern already exists
                existing_pattern = self.db_session.query(SpendingPattern).filter(
                    SpendingPattern.id == pattern.pattern_id
                ).first()
                
                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.frequency = pattern.frequency
                    existing_pattern.average_amount = pattern.average_amount
                    existing_pattern.total_amount = pattern.total_amount
                    existing_pattern.last_occurrence = pattern.last_occurrence
                    existing_pattern.next_predicted = pattern.next_predicted
                    existing_pattern.confidence_score = pattern.confidence_score
                    existing_pattern.is_active = pattern.is_active
                    existing_pattern.updated_at = datetime.now()
                else:
                    # Create new pattern
                    spending_pattern = SpendingPattern(
                        id=pattern.pattern_id,
                        user_id=pattern.user_id,
                        pattern_type=pattern.recurring_type.value,
                        category_name=pattern.category,
                        merchant_name=pattern.merchant_name,
                        frequency=pattern.frequency,
                        average_amount=pattern.average_amount,
                        total_amount=pattern.total_amount,
                        confidence_score=pattern.confidence_score,
                        reliability_score=pattern.confidence_score,
                        first_occurrence=pattern.first_occurrence,
                        last_occurrence=pattern.last_occurrence,
                        next_predicted=pattern.next_predicted,
                        is_active=pattern.is_active,
                        is_recurring=pattern.is_subscription,
                        created_at=pattern.created_at,
                        updated_at=pattern.updated_at
                    )
                    self.db_session.add(spending_pattern)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving patterns to database: {str(e)}")
            self.db_session.rollback()
            return False
    
    def get_pattern_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get statistics about detected patterns"""
        try:
            query = self.db_session.query(SpendingPattern)
            if user_id:
                query = query.filter(SpendingPattern.user_id == user_id)
            
            patterns = query.all()
            
            # Analyze patterns
            pattern_counts = Counter()
            category_counts = Counter()
            type_counts = Counter()
            active_patterns = 0
            
            for pattern in patterns:
                pattern_counts[pattern.pattern_type] += 1
                category_counts[pattern.category_name] += 1
                if pattern.is_active:
                    active_patterns += 1
            
            return {
                'total_patterns': len(patterns),
                'active_patterns': active_patterns,
                'pattern_types': [
                    {
                        'type': pattern_type,
                        'count': count,
                        'percentage': (count / len(patterns) * 100) if patterns else 0
                    }
                    for pattern_type, count in pattern_counts.most_common()
                ],
                'categories': [
                    {
                        'category': category,
                        'count': count,
                        'percentage': (count / len(patterns) * 100) if patterns else 0
                    }
                    for category, count in category_counts.most_common()
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pattern statistics: {str(e)}")
            return {
                'total_patterns': 0,
                'active_patterns': 0,
                'pattern_types': [],
                'categories': []
            } 