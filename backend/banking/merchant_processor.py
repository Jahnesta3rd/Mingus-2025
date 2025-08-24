"""
Merchant Identification and Standardization Service

This module handles merchant identification, name standardization, and categorization
for transaction processing in the MINGUS application.
"""

import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import hashlib
import unicodedata

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class MerchantType(Enum):
    """Merchant type classification"""
    RETAIL = "retail"
    RESTAURANT = "restaurant"
    GROCERY = "grocery"
    GAS_STATION = "gas_station"
    BANKING = "banking"
    UTILITY = "utility"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    TRANSPORTATION = "transportation"
    SUBSCRIPTION = "subscription"
    GOVERNMENT = "government"
    CHARITY = "charity"
    ONLINE = "online"
    SMALL_BUSINESS = "small_business"
    UNKNOWN = "unknown"


class MerchantStandardizationLevel(Enum):
    """Level of merchant standardization achieved"""
    EXACT_MATCH = "exact_match"
    FUZZY_MATCH = "fuzzy_match"
    PATTERN_MATCH = "pattern_match"
    CATEGORY_MATCH = "category_match"
    NORMALIZED = "normalized"
    UNKNOWN = "unknown"


@dataclass
class MerchantInfo:
    """Standardized merchant information"""
    original_name: str
    standardized_name: str
    merchant_type: MerchantType
    category: str
    subcategory: Optional[str] = None
    confidence_score: float = 0.0
    standardization_level: MerchantStandardizationLevel = MerchantStandardizationLevel.UNKNOWN
    aliases: List[str] = field(default_factory=list)
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    chain_id: Optional[str] = None
    parent_company: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MerchantMatch:
    """Result of merchant matching"""
    merchant_info: MerchantInfo
    match_score: float
    match_type: str
    matched_fields: List[str]
    confidence: float


class MerchantProcessor:
    """
    Comprehensive merchant identification and standardization service
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize merchant database
        self._initialize_merchant_database()
        
        # Initialize standardization rules
        self._initialize_standardization_rules()
        
        # Initialize pattern matching
        self._initialize_pattern_matching()
        
        # Initialize fuzzy matching
        self._initialize_fuzzy_matching()
    
    def _initialize_merchant_database(self):
        """Initialize the merchant database with known merchants"""
        self.known_merchants = {
            # Major Retail Chains
            'walmart': {
                'standardized_name': 'Walmart',
                'type': MerchantType.RETAIL,
                'category': 'shopping',
                'aliases': ['walmart', 'wal-mart', 'walmart.com', 'walmart store'],
                'chain_id': 'walmart_corp',
                'parent_company': 'Walmart Inc.',
                'website': 'walmart.com'
            },
            'target': {
                'standardized_name': 'Target',
                'type': MerchantType.RETAIL,
                'category': 'shopping',
                'aliases': ['target', 'target.com', 'target store', 'tgt'],
                'chain_id': 'target_corp',
                'parent_company': 'Target Corporation',
                'website': 'target.com'
            },
            'amazon': {
                'standardized_name': 'Amazon',
                'type': MerchantType.ONLINE,
                'category': 'shopping',
                'aliases': ['amazon', 'amazon.com', 'amzn', 'amazon marketplace'],
                'chain_id': 'amazon_corp',
                'parent_company': 'Amazon.com Inc.',
                'website': 'amazon.com'
            },
            
            # Food & Dining
            'starbucks': {
                'standardized_name': 'Starbucks',
                'type': MerchantType.RESTAURANT,
                'category': 'food_dining',
                'aliases': ['starbucks', 'starbucks coffee', 'sbux', 'starbucks store'],
                'chain_id': 'starbucks_corp',
                'parent_company': 'Starbucks Corporation',
                'website': 'starbucks.com'
            },
            'mcdonalds': {
                'standardized_name': 'McDonald\'s',
                'type': MerchantType.RESTAURANT,
                'category': 'food_dining',
                'aliases': ['mcdonalds', 'mcdonald', 'mcd', 'mcdonalds restaurant'],
                'chain_id': 'mcdonalds_corp',
                'parent_company': 'McDonald\'s Corporation',
                'website': 'mcdonalds.com'
            },
            'chipotle': {
                'standardized_name': 'Chipotle',
                'type': MerchantType.RESTAURANT,
                'category': 'food_dining',
                'aliases': ['chipotle', 'chipotle mexican grill', 'cmg'],
                'chain_id': 'chipotle_corp',
                'parent_company': 'Chipotle Mexican Grill Inc.',
                'website': 'chipotle.com'
            },
            
            # Grocery Stores
            'whole foods': {
                'standardized_name': 'Whole Foods Market',
                'type': MerchantType.GROCERY,
                'category': 'food_dining',
                'aliases': ['whole foods', 'whole foods market', 'wholefoods'],
                'chain_id': 'whole_foods_corp',
                'parent_company': 'Amazon.com Inc.',
                'website': 'wholefoodsmarket.com'
            },
            'trader joes': {
                'standardized_name': 'Trader Joe\'s',
                'type': MerchantType.GROCERY,
                'category': 'food_dining',
                'aliases': ['trader joes', 'trader joe', 'trader joe\'s'],
                'chain_id': 'trader_joes_corp',
                'parent_company': 'Aldi Nord',
                'website': 'traderjoes.com'
            },
            'kroger': {
                'standardized_name': 'Kroger',
                'type': MerchantType.GROCERY,
                'category': 'food_dining',
                'aliases': ['kroger', 'kroger store', 'kroger grocery'],
                'chain_id': 'kroger_corp',
                'parent_company': 'The Kroger Co.',
                'website': 'kroger.com'
            },
            
            # Gas Stations
            'shell': {
                'standardized_name': 'Shell',
                'type': MerchantType.GAS_STATION,
                'category': 'transportation',
                'aliases': ['shell', 'shell gas', 'shell station', 'shell oil'],
                'chain_id': 'shell_corp',
                'parent_company': 'Royal Dutch Shell',
                'website': 'shell.com'
            },
            'exxon': {
                'standardized_name': 'ExxonMobil',
                'type': MerchantType.GAS_STATION,
                'category': 'transportation',
                'aliases': ['exxon', 'exxonmobil', 'exxon mobil', 'exxon gas'],
                'chain_id': 'exxon_corp',
                'parent_company': 'ExxonMobil Corporation',
                'website': 'exxonmobil.com'
            },
            'chevron': {
                'standardized_name': 'Chevron',
                'type': MerchantType.GAS_STATION,
                'category': 'transportation',
                'aliases': ['chevron', 'chevron gas', 'chevron station'],
                'chain_id': 'chevron_corp',
                'parent_company': 'Chevron Corporation',
                'website': 'chevron.com'
            },
            
            # Banking & Financial
            'chase': {
                'standardized_name': 'Chase Bank',
                'type': MerchantType.BANKING,
                'category': 'financial',
                'aliases': ['chase', 'chase bank', 'jpmorgan chase', 'chase atm'],
                'chain_id': 'chase_corp',
                'parent_company': 'JPMorgan Chase & Co.',
                'website': 'chase.com'
            },
            'wells fargo': {
                'standardized_name': 'Wells Fargo',
                'type': MerchantType.BANKING,
                'category': 'financial',
                'aliases': ['wells fargo', 'wells fargo bank', 'wellsfargo'],
                'chain_id': 'wells_fargo_corp',
                'parent_company': 'Wells Fargo & Company',
                'website': 'wellsfargo.com'
            },
            'bank of america': {
                'standardized_name': 'Bank of America',
                'type': MerchantType.BANKING,
                'category': 'financial',
                'aliases': ['bank of america', 'bofa', 'bank of america atm'],
                'chain_id': 'bofa_corp',
                'parent_company': 'Bank of America Corporation',
                'website': 'bankofamerica.com'
            },
            
            # Utilities
            'comcast': {
                'standardized_name': 'Comcast',
                'type': MerchantType.UTILITY,
                'category': 'utilities',
                'aliases': ['comcast', 'xfinity', 'comcast cable'],
                'chain_id': 'comcast_corp',
                'parent_company': 'Comcast Corporation',
                'website': 'comcast.com'
            },
            'verizon': {
                'standardized_name': 'Verizon',
                'type': MerchantType.UTILITY,
                'category': 'utilities',
                'aliases': ['verizon', 'verizon wireless', 'verizon fios'],
                'chain_id': 'verizon_corp',
                'parent_company': 'Verizon Communications Inc.',
                'website': 'verizon.com'
            },
            
            # Entertainment
            'netflix': {
                'standardized_name': 'Netflix',
                'type': MerchantType.SUBSCRIPTION,
                'category': 'entertainment',
                'aliases': ['netflix', 'netflix.com'],
                'chain_id': 'netflix_corp',
                'parent_company': 'Netflix Inc.',
                'website': 'netflix.com'
            },
            'spotify': {
                'standardized_name': 'Spotify',
                'type': MerchantType.SUBSCRIPTION,
                'category': 'entertainment',
                'aliases': ['spotify', 'spotify usa'],
                'chain_id': 'spotify_corp',
                'parent_company': 'Spotify Technology S.A.',
                'website': 'spotify.com'
            },
            
            # Transportation
            'uber': {
                'standardized_name': 'Uber',
                'type': MerchantType.TRANSPORTATION,
                'category': 'transportation',
                'aliases': ['uber', 'uber trip', 'uber rides'],
                'chain_id': 'uber_corp',
                'parent_company': 'Uber Technologies Inc.',
                'website': 'uber.com'
            },
            'lyft': {
                'standardized_name': 'Lyft',
                'type': MerchantType.TRANSPORTATION,
                'category': 'transportation',
                'aliases': ['lyft', 'lyft ride'],
                'chain_id': 'lyft_corp',
                'parent_company': 'Lyft Inc.',
                'website': 'lyft.com'
            }
        }
    
    def _initialize_standardization_rules(self):
        """Initialize merchant name standardization rules"""
        self.standardization_rules = {
            # Common abbreviations
            'abbreviations': {
                'inc': '',
                'corp': '',
                'llc': '',
                'ltd': '',
                'co': '',
                'company': '',
                'corporation': '',
                'incorporated': '',
                'limited': '',
                'assoc': 'association',
                'assn': 'association',
                'bros': 'brothers',
                'intl': 'international',
                'mfg': 'manufacturing',
                'mgr': 'manager',
                'mtg': 'meeting',
                'rd': 'road',
                'st': 'street',
                'ave': 'avenue',
                'blvd': 'boulevard',
                'dr': 'drive',
                'ct': 'court',
                'pl': 'place',
                'ln': 'lane',
                'pkwy': 'parkway',
                'hwy': 'highway',
                'fwy': 'freeway',
                'expy': 'expressway'
            },
            
            # Common suffixes to remove
            'remove_suffixes': [
                'store', 'shop', 'market', 'supermarket', 'grocery',
                'restaurant', 'cafe', 'diner', 'grill', 'pizza',
                'gas', 'station', 'fuel', 'oil',
                'bank', 'atm', 'credit union',
                'pharmacy', 'drugstore', 'cvs', 'walgreens',
                'clinic', 'hospital', 'medical center',
                'hotel', 'motel', 'inn', 'resort',
                'theater', 'cinema', 'movie',
                'gym', 'fitness', 'health club',
                'salon', 'spa', 'beauty',
                'auto', 'car', 'tire', 'repair',
                'hardware', 'home improvement',
                'electronics', 'computer', 'phone'
            ],
            
            # Common prefixes to remove
            'remove_prefixes': [
                'the ', 'a ', 'an ',
                'mr ', 'mrs ', 'ms ', 'dr ',
                'prof ', 'professor ',
                'capt ', 'captain ',
                'lt ', 'lieutenant ',
                'sgt ', 'sergeant ',
                'gen ', 'general '
            ],
            
            # Common words to remove
            'remove_words': [
                'and', 'or', 'but', 'the', 'a', 'an',
                'of', 'in', 'on', 'at', 'to', 'for',
                'with', 'by', 'from', 'up', 'down',
                'out', 'off', 'over', 'under',
                'new', 'old', 'big', 'small', 'good', 'bad',
                'best', 'worst', 'first', 'last',
                'north', 'south', 'east', 'west',
                'central', 'downtown', 'uptown'
            ]
        }
    
    def _initialize_pattern_matching(self):
        """Initialize pattern matching for merchant identification"""
        self.patterns = {
            # Gas station patterns
            'gas_station': [
                r'\b(shell|exxon|chevron|bp|mobil|76|arco|valero|marathon|sunoco|phillips)\b',
                r'\b(gas|fuel|petroleum|oil)\s+(station|stop|mart|store)\b',
                r'\b(convenience|c-store|gas\s+station)\b'
            ],
            
            # Restaurant patterns
            'restaurant': [
                r'\b(mcdonalds|burger|king|wendys|subway|pizza|hut|dominos|papa|johns)\b',
                r'\b(restaurant|cafe|diner|grill|bistro|tavern|pub|bar|steakhouse)\b',
                r'\b(fast\s+food|quick\s+service|casual\s+dining)\b'
            ],
            
            # Grocery patterns
            'grocery': [
                r'\b(whole\s+foods|trader\s+joes|kroger|safeway|albertsons|publix|wegmans)\b',
                r'\b(grocery|supermarket|food\s+market|fresh\s+market)\b',
                r'\b(organic|natural|health\s+food)\s+(store|market)\b'
            ],
            
            # Banking patterns
            'banking': [
                r'\b(chase|wells\s+fargo|bank\s+of\s+america|citibank|us\s+bank)\b',
                r'\b(bank|credit\s+union|savings|loan|mortgage)\b',
                r'\b(atm|automated\s+teller|cash\s+machine)\b'
            ],
            
            # Utility patterns
            'utility': [
                r'\b(comcast|verizon|at&t|spectrum|cox|xfinity|fios)\b',
                r'\b(electric|gas|water|sewer|trash|waste|utility)\b',
                r'\b(internet|cable|phone|telephone|telecom)\b'
            ],
            
            # Healthcare patterns
            'healthcare': [
                r'\b(cvs|walgreens|rite\s+aid|pharmacy|drugstore)\b',
                r'\b(hospital|clinic|medical|dental|vision|doctor|physician)\b',
                r'\b(health|wellness|fitness|gym|yoga|pilates)\b'
            ],
            
            # Entertainment patterns
            'entertainment': [
                r'\b(netflix|spotify|hulu|disney|amazon\s+prime|youtube)\b',
                r'\b(movie|theater|cinema|concert|show|performance)\b',
                r'\b(game|gaming|arcade|casino|lottery)\b'
            ],
            
            # Transportation patterns
            'transportation': [
                r'\b(uber|lyft|taxi|cab|transport|shuttle|bus|train|metro)\b',
                r'\b(airline|airport|parking|toll|transit|public\s+transport)\b',
                r'\b(rental|car\s+rental|hertz|avis|enterprise)\b'
            ],
            
            # Online patterns
            'online': [
                r'\.com$', r'\.net$', r'\.org$', r'\.edu$', r'\.gov$',
                r'\b(online|web|internet|digital|e-commerce|ecommerce)\b',
                r'\b(amazon|ebay|etsy|shopify|paypal|stripe)\b'
            ]
        }
    
    def _initialize_fuzzy_matching(self):
        """Initialize fuzzy matching parameters"""
        self.fuzzy_match_threshold = 0.8
        self.exact_match_threshold = 0.95
    
    def process_merchant(self, merchant_name: str, transaction_data: Dict[str, Any] = None) -> MerchantInfo:
        """
        Process and standardize a merchant name
        
        Args:
            merchant_name: Raw merchant name from transaction
            transaction_data: Additional transaction data for context
            
        Returns:
            Standardized merchant information
        """
        try:
            # Step 1: Normalize the merchant name
            normalized_name = self._normalize_merchant_name(merchant_name)
            
            # Step 2: Try exact matching
            exact_match = self._find_exact_match(normalized_name)
            if exact_match:
                return exact_match
            
            # Step 3: Try fuzzy matching
            fuzzy_match = self._find_fuzzy_match(normalized_name)
            if fuzzy_match and fuzzy_match.match_score >= self.fuzzy_match_threshold:
                return fuzzy_match.merchant_info
            
            # Step 4: Try pattern matching
            pattern_match = self._find_pattern_match(normalized_name, transaction_data)
            if pattern_match:
                return pattern_match
            
            # Step 5: Create standardized merchant info
            return self._create_standardized_merchant(normalized_name, transaction_data)
            
        except Exception as e:
            self.logger.error(f"Error processing merchant '{merchant_name}': {str(e)}")
            return self._create_fallback_merchant(merchant_name)
    
    def _normalize_merchant_name(self, merchant_name: str) -> str:
        """Normalize merchant name for consistent processing"""
        if not merchant_name:
            return ""
        
        # Convert to lowercase
        normalized = merchant_name.lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common prefixes
        for prefix in self.standardization_rules['remove_prefixes']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        # Remove common suffixes
        for suffix in self.standardization_rules['remove_suffixes']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Replace abbreviations
        words = normalized.split()
        for i, word in enumerate(words):
            if word in self.standardization_rules['abbreviations']:
                replacement = self.standardization_rules['abbreviations'][word]
                if replacement:
                    words[i] = replacement
                else:
                    words[i] = ""
        
        # Remove empty words and common words
        words = [word for word in words if word and word not in self.standardization_rules['remove_words']]
        
        # Rejoin and clean up
        normalized = ' '.join(words).strip()
        
        # Remove special characters but keep spaces and alphanumeric
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Final cleanup
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _find_exact_match(self, normalized_name: str) -> Optional[MerchantInfo]:
        """Find exact match in known merchants database"""
        # Direct match
        if normalized_name in self.known_merchants:
            merchant_data = self.known_merchants[normalized_name]
            return MerchantInfo(
                original_name=normalized_name,
                standardized_name=merchant_data['standardized_name'],
                merchant_type=merchant_data['type'],
                category=merchant_data['category'],
                confidence_score=1.0,
                standardization_level=MerchantStandardizationLevel.EXACT_MATCH,
                aliases=merchant_data.get('aliases', []),
                website=merchant_data.get('website'),
                chain_id=merchant_data.get('chain_id'),
                parent_company=merchant_data.get('parent_company')
            )
        
        # Check aliases
        for key, merchant_data in self.known_merchants.items():
            if normalized_name in merchant_data.get('aliases', []):
                return MerchantInfo(
                    original_name=normalized_name,
                    standardized_name=merchant_data['standardized_name'],
                    merchant_type=merchant_data['type'],
                    category=merchant_data['category'],
                    confidence_score=0.95,
                    standardization_level=MerchantStandardizationLevel.EXACT_MATCH,
                    aliases=merchant_data.get('aliases', []),
                    website=merchant_data.get('website'),
                    chain_id=merchant_data.get('chain_id'),
                    parent_company=merchant_data.get('parent_company')
                )
        
        return None
    
    def _find_fuzzy_match(self, normalized_name: str) -> Optional[MerchantMatch]:
        """Find fuzzy match in known merchants database"""
        best_match = None
        best_score = 0.0
        
        for key, merchant_data in self.known_merchants.items():
            # Calculate similarity with merchant key
            key_similarity = self._calculate_string_similarity(normalized_name, key)
            
            # Calculate similarity with aliases
            alias_similarities = [
                self._calculate_string_similarity(normalized_name, alias)
                for alias in merchant_data.get('aliases', [])
            ]
            
            # Get best similarity score
            max_similarity = max([key_similarity] + alias_similarities)
            
            if max_similarity > best_score and max_similarity >= self.fuzzy_match_threshold:
                best_score = max_similarity
                best_match = MerchantMatch(
                    merchant_info=MerchantInfo(
                        original_name=normalized_name,
                        standardized_name=merchant_data['standardized_name'],
                        merchant_type=merchant_data['type'],
                        category=merchant_data['category'],
                        confidence_score=max_similarity,
                        standardization_level=MerchantStandardizationLevel.FUZZY_MATCH,
                        aliases=merchant_data.get('aliases', []),
                        website=merchant_data.get('website'),
                        chain_id=merchant_data.get('chain_id'),
                        parent_company=merchant_data.get('parent_company')
                    ),
                    match_score=max_similarity,
                    match_type='fuzzy',
                    matched_fields=['name'],
                    confidence=max_similarity
                )
        
        return best_match
    
    def _find_pattern_match(self, normalized_name: str, transaction_data: Dict[str, Any] = None) -> Optional[MerchantInfo]:
        """Find pattern match for merchant type and category"""
        matched_type = None
        matched_category = None
        confidence = 0.0
        
        # Check patterns for each merchant type
        for merchant_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_name, re.IGNORECASE):
                    matched_type = MerchantType(merchant_type)
                    confidence = 0.7
                    break
            if matched_type:
                break
        
        # Determine category based on type
        if matched_type:
            category_mapping = {
                MerchantType.GAS_STATION: 'transportation',
                MerchantType.RESTAURANT: 'food_dining',
                MerchantType.GROCERY: 'food_dining',
                MerchantType.BANKING: 'financial',
                MerchantType.UTILITY: 'utilities',
                MerchantType.HEALTHCARE: 'healthcare',
                MerchantType.ENTERTAINMENT: 'entertainment',
                MerchantType.TRANSPORTATION: 'transportation',
                MerchantType.SUBSCRIPTION: 'subscriptions',
                MerchantType.ONLINE: 'shopping'
            }
            matched_category = category_mapping.get(matched_type, 'other')
        
        if matched_type:
            return MerchantInfo(
                original_name=normalized_name,
                standardized_name=self._capitalize_merchant_name(normalized_name),
                merchant_type=matched_type,
                category=matched_category,
                confidence_score=confidence,
                standardization_level=MerchantStandardizationLevel.PATTERN_MATCH,
                metadata={'pattern_matched': True}
            )
        
        return None
    
    def _create_standardized_merchant(self, normalized_name: str, transaction_data: Dict[str, Any] = None) -> MerchantInfo:
        """Create standardized merchant info when no match is found"""
        # Try to infer type from transaction data
        inferred_type = self._infer_merchant_type(normalized_name, transaction_data)
        
        return MerchantInfo(
            original_name=normalized_name,
            standardized_name=self._capitalize_merchant_name(normalized_name),
            merchant_type=inferred_type,
            category=self._get_category_for_type(inferred_type),
            confidence_score=0.3,
            standardization_level=MerchantStandardizationLevel.NORMALIZED,
            metadata={'inferred': True}
        )
    
    def _create_fallback_merchant(self, merchant_name: str) -> MerchantInfo:
        """Create fallback merchant info when processing fails"""
        return MerchantInfo(
            original_name=merchant_name,
            standardized_name=merchant_name,
            merchant_type=MerchantType.UNKNOWN,
            category='other',
            confidence_score=0.0,
            standardization_level=MerchantStandardizationLevel.UNKNOWN,
            metadata={'fallback': True}
        )
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Levenshtein distance"""
        if not str1 or not str2:
            return 0.0
        
        # Simple similarity calculation (can be enhanced with more sophisticated algorithms)
        str1_words = set(str1.lower().split())
        str2_words = set(str2.lower().split())
        
        if not str1_words or not str2_words:
            return 0.0
        
        intersection = str1_words.intersection(str2_words)
        union = str1_words.union(str2_words)
        
        return len(intersection) / len(union)
    
    def _capitalize_merchant_name(self, name: str) -> str:
        """Properly capitalize merchant name"""
        if not name:
            return ""
        
        # Split into words and capitalize each
        words = name.split()
        capitalized_words = []
        
        for word in words:
            if len(word) <= 2:  # Short words like "of", "in", "at"
                capitalized_words.append(word.lower())
            else:
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def _infer_merchant_type(self, normalized_name: str, transaction_data: Dict[str, Any] = None) -> MerchantType:
        """Infer merchant type from name and transaction data"""
        # Check for online indicators
        if any(indicator in normalized_name for indicator in ['.com', '.net', '.org', 'online', 'web']):
            return MerchantType.ONLINE
        
        # Check for small business indicators (short names, no obvious chain patterns)
        if len(normalized_name.split()) <= 3 and not any(chain in normalized_name for chain in ['walmart', 'target', 'amazon']):
            return MerchantType.SMALL_BUSINESS
        
        # Default to unknown
        return MerchantType.UNKNOWN
    
    def _get_category_for_type(self, merchant_type: MerchantType) -> str:
        """Get category for merchant type"""
        category_mapping = {
            MerchantType.RETAIL: 'shopping',
            MerchantType.RESTAURANT: 'food_dining',
            MerchantType.GROCERY: 'food_dining',
            MerchantType.GAS_STATION: 'transportation',
            MerchantType.BANKING: 'financial',
            MerchantType.UTILITY: 'utilities',
            MerchantType.HEALTHCARE: 'healthcare',
            MerchantType.ENTERTAINMENT: 'entertainment',
            MerchantType.TRANSPORTATION: 'transportation',
            MerchantType.SUBSCRIPTION: 'subscriptions',
            MerchantType.ONLINE: 'shopping',
            MerchantType.SMALL_BUSINESS: 'other',
            MerchantType.UNKNOWN: 'other'
        }
        
        return category_mapping.get(merchant_type, 'other')
    
    def batch_process_merchants(self, merchant_names: List[str]) -> List[MerchantInfo]:
        """Process multiple merchant names in batch"""
        results = []
        
        for merchant_name in merchant_names:
            try:
                merchant_info = self.process_merchant(merchant_name)
                results.append(merchant_info)
            except Exception as e:
                self.logger.error(f"Error processing merchant '{merchant_name}': {str(e)}")
                results.append(self._create_fallback_merchant(merchant_name))
        
        return results
    
    def get_merchant_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get statistics about merchant processing"""
        try:
            # Get all transactions
            query = self.db_session.query(PlaidTransaction)
            if user_id:
                query = query.filter(PlaidTransaction.user_id == user_id)
            
            transactions = query.all()
            
            # Analyze merchant patterns
            merchant_counts = Counter()
            category_counts = Counter()
            type_counts = Counter()
            
            for tx in transactions:
                if tx.merchant_name:
                    merchant_counts[tx.merchant_name] += 1
                
                if hasattr(tx, 'category') and tx.category:
                    category_counts[tx.category] += 1
            
            # Get top merchants
            top_merchants = merchant_counts.most_common(20)
            
            return {
                'total_transactions': len(transactions),
                'unique_merchants': len(merchant_counts),
                'top_merchants': [
                    {
                        'merchant_name': merchant,
                        'count': count,
                        'percentage': (count / len(transactions) * 100) if transactions else 0
                    }
                    for merchant, count in top_merchants
                ],
                'category_distribution': [
                    {
                        'category': category,
                        'count': count,
                        'percentage': (count / len(transactions) * 100) if transactions else 0
                    }
                    for category, count in category_counts.most_common()
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting merchant statistics: {str(e)}")
            return {
                'total_transactions': 0,
                'unique_merchants': 0,
                'top_merchants': [],
                'category_distribution': []
            } 