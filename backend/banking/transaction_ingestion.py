"""
Transaction Data Ingestion Service

This module handles raw transaction ingestion from Plaid with automatic
categorization and tagging capabilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from decimal import Decimal
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction, BankAccount
from backend.models.analytics import TransactionInsight
from backend.integrations.plaid_integration import PlaidIntegration
from backend.services.transaction_processor import TransactionProcessor
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.utils.validation import validate_transaction_data

logger = logging.getLogger(__name__)


class IngestionStatus(Enum):
    """Transaction ingestion status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    INVALID = "invalid"


class CategorizationMethod(Enum):
    """Methods used for transaction categorization"""
    PLAID_CATEGORY = "plaid_category"
    MERCHANT_PATTERN = "merchant_pattern"
    AMOUNT_HEURISTIC = "amount_heuristic"
    ML_MODEL = "ml_model"
    USER_OVERRIDE = "user_override"
    FALLBACK = "fallback"


@dataclass
class IngestionResult:
    """Result of transaction ingestion"""
    transaction_id: str
    status: IngestionStatus
    original_data: Dict[str, Any]
    processed_data: Dict[str, Any]
    categorization: Dict[str, Any]
    tags: List[str]
    confidence_score: float
    processing_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CategorizationResult:
    """Result of transaction categorization"""
    category: str
    confidence: float
    method: CategorizationMethod
    subcategory: Optional[str] = None
    merchant_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransactionIngestionService:
    """
    Comprehensive transaction ingestion service that handles raw Plaid transaction data
    with automatic categorization and tagging.
    """
    
    def __init__(self, db_session: Session, plaid_integration: PlaidIntegration):
        self.db_session = db_session
        self.plaid_integration = plaid_integration
        self.logger = logging.getLogger(__name__)
        
        # Initialize categorization engine
        self._initialize_categorization_engine()
        
        # Initialize tagging system
        self._initialize_tagging_system()
        
        # Initialize duplicate detection
        self._initialize_duplicate_detection()
    
    def _initialize_categorization_engine(self):
        """Initialize the categorization engine with rules and patterns"""
        self.categorization_rules = {
            # Food & Dining
            'food_dining': {
                'patterns': [
                    r'\b(starbucks|mcdonalds|burger|pizza|restaurant|cafe|coffee|food|dining)\b',
                    r'\b(grubhub|doordash|uber eats|postmates|seamless)\b',
                    r'\b(grocery|supermarket|whole foods|trader joe|kroger|safeway)\b',
                    r'\b(walmart|target|costco|sam\'s club)\b'
                ],
                'amount_ranges': [(5, 200), (20, 500)],  # (min, max) for different types
                'keywords': ['food', 'dining', 'restaurant', 'cafe', 'grocery', 'supermarket']
            },
            
            # Transportation
            'transportation': {
                'patterns': [
                    r'\b(uber|lyft|taxi|transport|gas|fuel|shell|exxon|chevron|bp)\b',
                    r'\b(public transit|metro|bus|train|subway|parking|toll)\b',
                    r'\b(hertz|avis|enterprise|budget|car rental)\b'
                ],
                'amount_ranges': [(10, 100), (50, 500)],
                'keywords': ['transport', 'gas', 'fuel', 'parking', 'toll', 'transit']
            },
            
            # Shopping
            'shopping': {
                'patterns': [
                    r'\b(amazon|walmart|target|best buy|home depot|lowes|macy|nordstrom)\b',
                    r'\b(clothing|apparel|shoes|electronics|furniture|jewelry)\b',
                    r'\b(nike|adidas|apple|samsung|sony|lg)\b'
                ],
                'amount_ranges': [(20, 1000), (100, 5000)],
                'keywords': ['shopping', 'retail', 'store', 'shop', 'mall']
            },
            
            # Entertainment
            'entertainment': {
                'patterns': [
                    r'\b(netflix|spotify|hulu|disney|movie|theater|concert|game)\b',
                    r'\b(bar|pub|club|casino|amusement|park|museum|zoo)\b',
                    r'\b(steam|playstation|xbox|nintendo|gaming)\b'
                ],
                'amount_ranges': [(10, 200), (50, 500)],
                'keywords': ['entertainment', 'movie', 'game', 'concert', 'bar']
            },
            
            # Healthcare
            'healthcare': {
                'patterns': [
                    r'\b(doctor|hospital|pharmacy|cvs|walgreens|medical|dental|vision)\b',
                    r'\b(insurance|copay|deductible|prescription|medication)\b',
                    r'\b(blue cross|aetna|united health|kaiser|humana)\b'
                ],
                'amount_ranges': [(20, 500), (100, 2000)],
                'keywords': ['health', 'medical', 'pharmacy', 'doctor', 'hospital']
            },
            
            # Utilities
            'utilities': {
                'patterns': [
                    r'\b(electric|gas|water|internet|phone|cell|mobile|utility)\b',
                    r'\b(comcast|verizon|at&t|sprint|tmobile|spectrum)\b',
                    r'\b(pge|socal gas|edison|duke energy|conedison)\b'
                ],
                'amount_ranges': [(50, 500), (100, 1000)],
                'keywords': ['utility', 'electric', 'gas', 'water', 'internet']
            },
            
            # Housing
            'housing': {
                'patterns': [
                    r'\b(rent|mortgage|apartment|house|property|maintenance|repair)\b',
                    r'\b(hoa|condo|association|landlord|property management)\b',
                    r'\b(wells fargo|chase|bank of america|citibank)\b'
                ],
                'amount_ranges': [(500, 5000), (1000, 10000)],
                'keywords': ['rent', 'mortgage', 'housing', 'property']
            },
            
            # Subscriptions
            'subscriptions': {
                'patterns': [
                    r'\b(subscription|monthly|recurring|auto-pay|automatic)\b',
                    r'\b(software|saas|platform|service|membership)\b',
                    r'\b(adobe|microsoft|google|apple|dropbox|box)\b'
                ],
                'amount_ranges': [(5, 100), (10, 500)],
                'keywords': ['subscription', 'monthly', 'recurring', 'service']
            },
            
            # Income
            'income': {
                'patterns': [
                    r'\b(deposit|credit|refund|return|rebate|cashback|bonus|salary|payroll)\b',
                    r'\b(interest|dividend|investment|stock|bond|mutual fund)\b',
                    r'\b(venmo|paypal|zelle|cash app|square)\b'
                ],
                'amount_ranges': [(100, 10000), (1000, 50000)],
                'keywords': ['deposit', 'credit', 'salary', 'bonus', 'interest']
            },
            
            # Transfers
            'transfers': {
                'patterns': [
                    r'\b(transfer|ach|wire|move money|send money|receive money)\b',
                    r'\b(venmo|paypal|zelle|cash app|square)\b'
                ],
                'amount_ranges': [(10, 10000), (100, 50000)],
                'keywords': ['transfer', 'ach', 'wire', 'move money']
            },
            
            # Fees
            'fees': {
                'patterns': [
                    r'\b(fee|charge|penalty|late|overdraft|maintenance|service)\b',
                    r'\b(atm|withdrawal|foreign transaction|convenience)\b'
                ],
                'amount_ranges': [(1, 50), (5, 200)],
                'keywords': ['fee', 'charge', 'penalty', 'overdraft']
            }
        }
    
    def _initialize_tagging_system(self):
        """Initialize the tagging system with automatic tag generation rules"""
        self.tagging_rules = {
            # Amount-based tags
            'amount_tags': {
                'high_value': lambda amount: abs(amount) > 1000,
                'medium_value': lambda amount: 100 <= abs(amount) <= 1000,
                'low_value': lambda amount: abs(amount) < 100,
                'micro_transaction': lambda amount: abs(amount) < 10
            },
            
            # Time-based tags
            'time_tags': {
                'late_night': lambda hour: hour >= 22 or hour <= 6,
                'weekend': lambda weekday: weekday >= 5,  # Saturday = 5, Sunday = 6
                'business_hours': lambda hour: 9 <= hour <= 17
            },
            
            # Frequency-based tags
            'frequency_tags': {
                'recurring': lambda frequency: frequency >= 3,
                'occasional': lambda frequency: 1 <= frequency <= 2,
                'one_time': lambda frequency: frequency == 1
            },
            
            # Merchant-based tags
            'merchant_tags': {
                'online': lambda merchant: any(word in merchant.lower() for word in ['amazon', 'online', 'web', 'digital']),
                'local': lambda merchant: not any(word in merchant.lower() for word in ['amazon', 'online', 'web', 'digital']),
                'chain': lambda merchant: any(word in merchant.lower() for word in ['starbucks', 'mcdonalds', 'walmart', 'target']),
                'small_business': lambda merchant: len(merchant.split()) <= 3 and not any(word in merchant.lower() for word in ['starbucks', 'mcdonalds', 'walmart', 'target'])
            },
            
            # Category-based tags
            'category_tags': {
                'essential': lambda category: category in ['food_dining', 'transportation', 'utilities', 'housing', 'healthcare'],
                'discretionary': lambda category: category in ['entertainment', 'shopping', 'subscriptions'],
                'financial': lambda category: category in ['income', 'transfers', 'fees']
            }
        }
    
    def _initialize_duplicate_detection(self):
        """Initialize duplicate detection system"""
        self.duplicate_detection_fields = [
            'transaction_id',
            'amount',
            'date',
            'merchant_name',
            'account_id'
        ]
    
    def ingest_transactions(self, user_id: int, account_ids: List[str] = None,
                          date_range: Tuple[datetime, datetime] = None,
                          force_refresh: bool = False) -> Dict[str, Any]:
        """
        Ingest transactions from Plaid for specified user and accounts
        
        Args:
            user_id: User ID to ingest transactions for
            account_ids: Specific account IDs to ingest (None for all)
            date_range: Date range to ingest (None for last 90 days)
            force_refresh: Force refresh even if recent data exists
        
        Returns:
            Dictionary containing ingestion results and statistics
        """
        try:
            self.logger.info(f"Starting transaction ingestion for user {user_id}")
            
            # Get accounts to process
            accounts = self._get_user_accounts(user_id, account_ids)
            if not accounts:
                return {
                    'success': False,
                    'error': 'No accounts found for user',
                    'results': []
                }
            
            # Determine date range
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                date_range = (start_date, end_date)
            
            # Ingest transactions for each account
            all_results = []
            total_processed = 0
            total_new = 0
            total_duplicates = 0
            total_errors = 0
            
            for account in accounts:
                self.logger.info(f"Processing account {account.id}")
                
                # Check if we need to refresh data
                if not force_refresh and self._has_recent_data(account.id, date_range[1]):
                    self.logger.info(f"Account {account.id} has recent data, skipping")
                    continue
                
                # Fetch transactions from Plaid
                plaid_transactions = self._fetch_plaid_transactions(account, date_range)
                
                if not plaid_transactions:
                    self.logger.info(f"No transactions found for account {account.id}")
                    continue
                
                # Process each transaction
                for plaid_tx in plaid_transactions:
                    result = self._process_single_transaction(plaid_tx, account, user_id)
                    all_results.append(result)
                    
                    if result.status == IngestionStatus.COMPLETED:
                        total_new += 1
                    elif result.status == IngestionStatus.DUPLICATE:
                        total_duplicates += 1
                    elif result.status == IngestionStatus.FAILED:
                        total_errors += 1
                    
                    total_processed += 1
                
                # Update account sync status
                self._update_account_sync_status(account.id, date_range[1])
            
            # Generate summary statistics
            summary = {
                'total_processed': total_processed,
                'total_new': total_new,
                'total_duplicates': total_duplicates,
                'total_errors': total_errors,
                'accounts_processed': len(accounts),
                'date_range': {
                    'start': date_range[0].isoformat(),
                    'end': date_range[1].isoformat()
                }
            }
            
            self.logger.info(f"Transaction ingestion completed: {summary}")
            
            return {
                'success': True,
                'summary': summary,
                'results': all_results
            }
            
        except Exception as e:
            self.logger.error(f"Error during transaction ingestion: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def _get_user_accounts(self, user_id: int, account_ids: List[str] = None) -> List[BankAccount]:
        """Get user accounts for processing"""
        query = self.db_session.query(BankAccount).filter(BankAccount.user_id == user_id)
        
        if account_ids:
            query = query.filter(BankAccount.id.in_(account_ids))
        
        return query.filter(BankAccount.is_active == True).all()
    
    def _has_recent_data(self, account_id: str, end_date: datetime) -> bool:
        """Check if account has recent transaction data"""
        recent_threshold = end_date - timedelta(hours=6)  # 6 hours threshold
        
        recent_count = self.db_session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.account_id == account_id,
                PlaidTransaction.created_at >= recent_threshold
            )
        ).count()
        
        return recent_count > 0
    
    def _fetch_plaid_transactions(self, account: BankAccount, 
                                date_range: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
        """Fetch transactions from Plaid API"""
        try:
            # Get Plaid connection for account
            plaid_connection = account.plaid_connection
            if not plaid_connection or not plaid_connection.access_token:
                self.logger.warning(f"No Plaid connection found for account {account.id}")
                return []
            
            # Fetch transactions from Plaid
            transactions = self.plaid_integration.get_transactions(
                access_token=plaid_connection.access_token,
                start_date=date_range[0].date(),
                end_date=date_range[1].date(),
                account_ids=[account.plaid_account_id] if account.plaid_account_id else None
            )
            
            return transactions.get('transactions', [])
            
        except Exception as e:
            self.logger.error(f"Error fetching Plaid transactions for account {account.id}: {str(e)}")
            return []
    
    def _process_single_transaction(self, plaid_tx: Dict[str, Any], 
                                  account: BankAccount, user_id: int) -> IngestionResult:
        """Process a single transaction from Plaid"""
        start_time = datetime.now()
        
        try:
            # Validate transaction data
            validation_result = self._validate_transaction_data(plaid_tx)
            if not validation_result['valid']:
                return IngestionResult(
                    transaction_id=plaid_tx.get('transaction_id', 'unknown'),
                    status=IngestionStatus.INVALID,
                    original_data=plaid_tx,
                    processed_data={},
                    categorization={},
                    tags=[],
                    confidence_score=0.0,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    errors=validation_result['errors']
                )
            
            # Check for duplicates
            if self._is_duplicate_transaction(plaid_tx, account.id):
                return IngestionResult(
                    transaction_id=plaid_tx['transaction_id'],
                    status=IngestionStatus.DUPLICATE,
                    original_data=plaid_tx,
                    processed_data=plaid_tx,
                    categorization={},
                    tags=['duplicate'],
                    confidence_score=1.0,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Categorize transaction
            categorization = self._categorize_transaction(plaid_tx)
            
            # Generate tags
            tags = self._generate_tags(plaid_tx, categorization)
            
            # Prepare processed data
            processed_data = self._prepare_processed_data(plaid_tx, categorization, tags)
            
            # Store transaction in database
            transaction = self._store_transaction(processed_data, account.id, user_id)
            
            # Create transaction insight
            self._create_transaction_insight(transaction, categorization, tags)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return IngestionResult(
                transaction_id=plaid_tx['transaction_id'],
                status=IngestionStatus.COMPLETED,
                original_data=plaid_tx,
                processed_data=processed_data,
                categorization=categorization.__dict__,
                tags=tags,
                confidence_score=categorization.confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing transaction {plaid_tx.get('transaction_id', 'unknown')}: {str(e)}")
            return IngestionResult(
                transaction_id=plaid_tx.get('transaction_id', 'unknown'),
                status=IngestionStatus.FAILED,
                original_data=plaid_tx,
                processed_data={},
                categorization={},
                tags=[],
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)]
            )
    
    def _validate_transaction_data(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction data from Plaid"""
        errors = []
        
        required_fields = ['transaction_id', 'amount', 'date', 'name']
        for field in required_fields:
            if field not in transaction or transaction[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if 'amount' in transaction:
            try:
                amount = float(transaction['amount'])
                if amount == 0:
                    errors.append("Transaction amount cannot be zero")
            except (ValueError, TypeError):
                errors.append("Invalid transaction amount")
        
        if 'date' in transaction:
            try:
                datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append("Invalid transaction date")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _is_duplicate_transaction(self, transaction: Dict[str, Any], account_id: str) -> bool:
        """Check if transaction is a duplicate"""
        # Check by Plaid transaction ID first
        existing = self.db_session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.transaction_id == transaction['transaction_id'],
                PlaidTransaction.account_id == account_id
            )
        ).first()
        
        if existing:
            return True
        
        # Check by amount, date, and merchant (fuzzy duplicate detection)
        amount = abs(float(transaction['amount']))
        date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
        merchant = transaction.get('merchant_name', transaction.get('name', ''))
        
        # Look for similar transactions within 24 hours
        similar_transactions = self.db_session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.account_id == account_id,
                PlaidTransaction.amount == amount,
                PlaidTransaction.date >= date - timedelta(hours=24),
                PlaidTransaction.date <= date + timedelta(hours=24)
            )
        ).all()
        
        for similar_tx in similar_transactions:
            similar_merchant = similar_tx.merchant_name or similar_tx.name
            if self._merchant_similarity(merchant, similar_merchant) > 0.8:
                return True
        
        return False
    
    def _merchant_similarity(self, merchant1: str, merchant2: str) -> float:
        """Calculate similarity between two merchant names"""
        if not merchant1 or not merchant2:
            return 0.0
        
        # Simple similarity based on common words
        words1 = set(merchant1.lower().split())
        words2 = set(merchant2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _categorize_transaction(self, transaction: Dict[str, Any]) -> CategorizationResult:
        """Categorize transaction using multiple methods"""
        amount = abs(float(transaction['amount']))
        merchant_name = transaction.get('merchant_name', transaction.get('name', ''))
        plaid_category = transaction.get('category', [])
        
        # Method 1: Use Plaid's category if available and confident
        if plaid_category and len(plaid_category) > 0:
            plaid_result = self._categorize_from_plaid(plaid_category, amount)
            if plaid_result.confidence > 0.7:
                return plaid_result
        
        # Method 2: Pattern matching on merchant name
        pattern_result = self._categorize_by_pattern(merchant_name, amount)
        if pattern_result.confidence > 0.6:
            return pattern_result
        
        # Method 3: Amount-based heuristics
        amount_result = self._categorize_by_amount(amount, merchant_name)
        if amount_result.confidence > 0.5:
            return amount_result
        
        # Method 4: Fallback categorization
        return self._categorize_fallback(transaction)
    
    def _categorize_from_plaid(self, plaid_category: List[str], amount: float) -> CategorizationResult:
        """Categorize based on Plaid's category"""
        category_mapping = {
            'Food and Drink': 'food_dining',
            'Transportation': 'transportation',
            'Shopping': 'shopping',
            'Entertainment': 'entertainment',
            'Healthcare': 'healthcare',
            'Utilities': 'utilities',
            'Rent and Utilities': 'housing',
            'Transfer': 'transfers',
            'Income': 'income',
            'Fees': 'fees'
        }
        
        primary_category = plaid_category[0] if plaid_category else 'Other'
        mapped_category = category_mapping.get(primary_category, 'other')
        
        # Adjust confidence based on category specificity
        confidence = 0.8 if len(plaid_category) > 1 else 0.6
        
        return CategorizationResult(
            category=mapped_category,
            confidence=confidence,
            method=CategorizationMethod.PLAID_CATEGORY,
            subcategory=primary_category,
            tags=['plaid_categorized']
        )
    
    def _categorize_by_pattern(self, merchant_name: str, amount: float) -> CategorizationResult:
        """Categorize based on merchant name patterns"""
        merchant_lower = merchant_name.lower()
        best_category = 'other'
        best_confidence = 0.0
        best_pattern = None
        
        for category, rules in self.categorization_rules.items():
            for pattern in rules['patterns']:
                if re.search(pattern, merchant_lower):
                    # Calculate confidence based on pattern match and amount
                    pattern_confidence = 0.7
                    
                    # Adjust confidence based on amount ranges
                    for min_amount, max_amount in rules['amount_ranges']:
                        if min_amount <= amount <= max_amount:
                            pattern_confidence += 0.2
                            break
                    
                    if pattern_confidence > best_confidence:
                        best_confidence = pattern_confidence
                        best_category = category
                        best_pattern = pattern
        
        return CategorizationResult(
            category=best_category,
            confidence=min(best_confidence, 1.0),
            method=CategorizationMethod.MERCHANT_PATTERN,
            merchant_name=merchant_name,
            tags=['pattern_matched'],
            metadata={'matched_pattern': best_pattern}
        )
    
    def _categorize_by_amount(self, amount: float, merchant_name: str) -> CategorizationResult:
        """Categorize based on amount heuristics"""
        # High-value transactions are likely housing or transfers
        if amount > 1000:
            if any(word in merchant_name.lower() for word in ['rent', 'mortgage', 'property']):
                return CategorizationResult(
                    category='housing',
                    confidence=0.6,
                    method=CategorizationMethod.AMOUNT_HEURISTIC,
                    tags=['high_value', 'amount_based']
                )
            else:
                return CategorizationResult(
                    category='transfers',
                    confidence=0.5,
                    method=CategorizationMethod.AMOUNT_HEURISTIC,
                    tags=['high_value', 'amount_based']
                )
        
        # Low-value transactions are likely fees or small purchases
        elif amount < 20:
            if any(word in merchant_name.lower() for word in ['fee', 'charge', 'atm']):
                return CategorizationResult(
                    category='fees',
                    confidence=0.7,
                    method=CategorizationMethod.AMOUNT_HEURISTIC,
                    tags=['low_value', 'amount_based']
                )
            else:
                return CategorizationResult(
                    category='food_dining',
                    confidence=0.4,
                    method=CategorizationMethod.AMOUNT_HEURISTIC,
                    tags=['low_value', 'amount_based']
                )
        
        # Medium-value transactions are likely shopping or entertainment
        else:
            return CategorizationResult(
                category='shopping',
                confidence=0.3,
                method=CategorizationMethod.AMOUNT_HEURISTIC,
                tags=['medium_value', 'amount_based']
            )
    
    def _categorize_fallback(self, transaction: Dict[str, Any]) -> CategorizationResult:
        """Fallback categorization when other methods fail"""
        amount = abs(float(transaction['amount']))
        
        # Default to 'other' category
        return CategorizationResult(
            category='other',
            confidence=0.1,
            method=CategorizationMethod.FALLBACK,
            tags=['fallback_categorized']
        )
    
    def _generate_tags(self, transaction: Dict[str, Any], 
                      categorization: CategorizationResult) -> List[str]:
        """Generate tags for transaction"""
        tags = []
        amount = abs(float(transaction['amount']))
        merchant_name = transaction.get('merchant_name', transaction.get('name', ''))
        date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
        
        # Amount-based tags
        for tag_name, condition in self.tagging_rules['amount_tags'].items():
            if condition(amount):
                tags.append(tag_name)
        
        # Time-based tags
        for tag_name, condition in self.tagging_rules['time_tags'].items():
            if tag_name == 'late_night' and condition(date.hour):
                tags.append(tag_name)
            elif tag_name == 'weekend' and condition(date.weekday()):
                tags.append(tag_name)
            elif tag_name == 'business_hours' and condition(date.hour):
                tags.append(tag_name)
        
        # Merchant-based tags
        for tag_name, condition in self.tagging_rules['merchant_tags'].items():
            if condition(merchant_name):
                tags.append(tag_name)
        
        # Category-based tags
        for tag_name, condition in self.tagging_rules['category_tags'].items():
            if condition(categorization.category):
                tags.append(tag_name)
        
        # Add categorization method tag
        tags.append(f"categorized_by_{categorization.method.value}")
        
        # Add confidence level tag
        if categorization.confidence > 0.8:
            tags.append('high_confidence')
        elif categorization.confidence > 0.5:
            tags.append('medium_confidence')
        else:
            tags.append('low_confidence')
        
        return list(set(tags))  # Remove duplicates
    
    def _prepare_processed_data(self, transaction: Dict[str, Any], 
                              categorization: CategorizationResult, 
                              tags: List[str]) -> Dict[str, Any]:
        """Prepare processed transaction data for storage"""
        processed = transaction.copy()
        
        # Add categorization data
        processed['category'] = categorization.category
        processed['subcategory'] = categorization.subcategory
        processed['categorization_confidence'] = categorization.confidence
        processed['categorization_method'] = categorization.method.value
        
        # Add tags
        processed['tags'] = tags
        
        # Add processing metadata
        processed['processed_at'] = datetime.now().isoformat()
        processed['processing_version'] = '1.0'
        
        return processed
    
    def _store_transaction(self, processed_data: Dict[str, Any], 
                         account_id: str, user_id: int) -> PlaidTransaction:
        """Store processed transaction in database"""
        # Encrypt sensitive fields
        encrypted_name = encrypt_data(processed_data.get('name', ''))
        encrypted_merchant_name = encrypt_data(processed_data.get('merchant_name', ''))
        
        transaction = PlaidTransaction(
            transaction_id=processed_data['transaction_id'],
            account_id=account_id,
            user_id=user_id,
            amount=Decimal(str(processed_data['amount'])),
            date=datetime.fromisoformat(processed_data['date'].replace('Z', '+00:00')),
            name=encrypted_name,
            merchant_name=encrypted_merchant_name,
            category=processed_data.get('category', 'other'),
            subcategory=processed_data.get('subcategory'),
            categorization_confidence=processed_data.get('categorization_confidence', 0.0),
            categorization_method=processed_data.get('categorization_method', 'fallback'),
            tags=json.dumps(processed_data.get('tags', [])),
            metadata=json.dumps(processed_data.get('metadata', {})),
            created_at=datetime.now()
        )
        
        self.db_session.add(transaction)
        self.db_session.commit()
        
        return transaction
    
    def _create_transaction_insight(self, transaction: PlaidTransaction, 
                                  categorization: CategorizationResult, 
                                  tags: List[str]):
        """Create transaction insight record"""
        insight = TransactionInsight(
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            category=categorization.category,
            confidence=categorization.confidence,
            transaction_type='expense' if transaction.amount < 0 else 'income',
            merchant_name=transaction.merchant_name,
            is_recurring='recurring' in tags,
            is_subscription='subscription' in tags,
            is_anomaly='anomaly' in tags,
            risk_score=self._calculate_risk_score(transaction, categorization, tags),
            insights=json.dumps(self._generate_insights(transaction, categorization, tags)),
            tags=json.dumps(tags),
            created_at=datetime.now()
        )
        
        self.db_session.add(insight)
        self.db_session.commit()
    
    def _calculate_risk_score(self, transaction: PlaidTransaction, 
                            categorization: CategorizationResult, 
                            tags: List[str]) -> float:
        """Calculate risk score for transaction"""
        risk_score = 0.0
        
        # Amount-based risk
        amount = abs(float(transaction.amount))
        if amount > 1000:
            risk_score += 0.3
        elif amount > 500:
            risk_score += 0.2
        elif amount > 100:
            risk_score += 0.1
        
        # Category-based risk
        high_risk_categories = ['gambling', 'payday_loans', 'crypto']
        if categorization.category in high_risk_categories:
            risk_score += 0.4
        
        # Time-based risk
        if 'late_night' in tags:
            risk_score += 0.1
        
        # Confidence-based risk
        if categorization.confidence < 0.3:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def _generate_insights(self, transaction: PlaidTransaction, 
                         categorization: CategorizationResult, 
                         tags: List[str]) -> List[str]:
        """Generate insights for transaction"""
        insights = []
        amount = abs(float(transaction.amount))
        
        # Amount-based insights
        if amount > 500:
            insights.append("High-value transaction detected")
        
        if 'recurring' in tags:
            insights.append("Recurring transaction pattern identified")
        
        if 'subscription' in tags:
            insights.append("Subscription payment detected")
        
        if categorization.confidence < 0.5:
            insights.append("Low confidence categorization - review recommended")
        
        return insights
    
    def _update_account_sync_status(self, account_id: str, last_sync_date: datetime):
        """Update account sync status"""
        # This would update the account's last sync timestamp
        # Implementation depends on your account model structure
        pass 