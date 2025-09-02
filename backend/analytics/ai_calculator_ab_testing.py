"""
AI Calculator A/B Testing Framework
Framework for testing different risk calculation algorithms, conversion offers, and personalization strategies.
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from enum import Enum

from sqlalchemy import text, func, and_, or_, desc
from sqlalchemy.orm import Session

from backend.database import get_db_session
from backend.models.analytics import AnalyticsEvent
from backend.models.assessment import Assessment
from backend.analytics.ai_calculator_analytics import EventType, RiskLevel

logger = logging.getLogger(__name__)

class TestType(Enum):
    """A/B test types"""
    RISK_ALGORITHM = "risk_algorithm"
    CONVERSION_OFFER = "conversion_offer"
    PERSONALIZATION = "personalization"
    URGENCY_MESSAGING = "urgency_messaging"

class TestStatus(Enum):
    """Test status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    test_name: str
    test_type: TestType
    description: str
    status: TestStatus
    start_date: datetime
    end_date: Optional[datetime]
    traffic_split: float  # Percentage of traffic to include in test
    variants: List[Dict[str, Any]]
    primary_metric: str
    secondary_metrics: List[str]
    minimum_sample_size: int
    confidence_level: float
    created_at: datetime
    updated_at: datetime

@dataclass
class TestResult:
    """A/B test results"""
    test_id: str
    variant: str
    sample_size: int
    conversion_rate: float
    revenue_per_user: float
    total_revenue: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]
    p_value: float

class AICalculatorABTesting:
    """A/B testing framework for AI calculator"""
    
    def __init__(self):
        self.db_session = get_db_session()
        self.active_tests = {}
        self._load_active_tests()
    
    def create_test(self, test_config: Dict[str, Any]) -> str:
        """Create a new A/B test"""
        try:
            test_id = f"test_{int(datetime.utcnow().timestamp())}"
            
            test = ABTest(
                test_id=test_id,
                test_name=test_config['test_name'],
                test_type=TestType(test_config['test_type']),
                description=test_config['description'],
                status=TestStatus.DRAFT,
                start_date=datetime.fromisoformat(test_config['start_date']),
                end_date=datetime.fromisoformat(test_config['end_date']) if test_config.get('end_date') else None,
                traffic_split=test_config['traffic_split'],
                variants=test_config['variants'],
                primary_metric=test_config['primary_metric'],
                secondary_metrics=test_config['secondary_metrics'],
                minimum_sample_size=test_config['minimum_sample_size'],
                confidence_level=test_config['confidence_level'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store test configuration
            self._store_test_config(test)
            
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        try:
            test = self._get_test_config(test_id)
            if not test:
                return False
            
            test.status = TestStatus.ACTIVE
            test.updated_at = datetime.utcnow()
            
            self._update_test_config(test)
            self.active_tests[test_id] = test
            
            logger.info(f"Started A/B test: {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting A/B test: {e}")
            return False
    
    def get_variant(self, test_id: str, user_id: Optional[str] = None, 
                   session_id: Optional[str] = None) -> Optional[str]:
        """Get test variant for user/session"""
        try:
            test = self.active_tests.get(test_id)
            if not test or test.status != TestStatus.ACTIVE:
                return None
            
            # Check if user/session is in test traffic
            if not self._is_in_test_traffic(test, user_id, session_id):
                return None
            
            # Determine variant based on user/session ID
            variant_key = user_id or session_id
            if not variant_key:
                return None
            
            # Hash the key to get consistent variant assignment
            hash_value = int(hashlib.md5(variant_key.encode()).hexdigest(), 16)
            variant_index = hash_value % len(test.variants)
            
            variant = test.variants[variant_index]['name']
            
            # Track variant assignment
            self._track_variant_assignment(test_id, variant, user_id, session_id)
            
            return variant
            
        except Exception as e:
            logger.error(f"Error getting test variant: {e}")
            return None
    
    def track_test_event(self, test_id: str, variant: str, event_type: EventType,
                        user_id: Optional[str] = None, session_id: Optional[str] = None,
                        **kwargs) -> None:
        """Track event for A/B test"""
        try:
            # Store test event
            test_event = {
                'test_id': test_id,
                'variant': variant,
                'event_type': event_type.value,
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
            
            self._store_test_event(test_event)
            
        except Exception as e:
            logger.error(f"Error tracking test event: {e}")
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        try:
            test = self._get_test_config(test_id)
            if not test:
                return {}
            
            # Get variant performance data
            variant_results = []
            
            for variant in test.variants:
                variant_name = variant['name']
                result = self._calculate_variant_performance(test_id, variant_name, test.primary_metric)
                variant_results.append(result)
            
            # Calculate statistical significance
            if len(variant_results) >= 2:
                significance = self._calculate_statistical_significance(variant_results)
            else:
                significance = None
            
            return {
                'test_id': test_id,
                'test_name': test.test_name,
                'status': test.status.value,
                'primary_metric': test.primary_metric,
                'variant_results': [asdict(r) for r in variant_results],
                'statistical_significance': significance,
                'recommendation': self._generate_recommendation(variant_results, significance)
            }
            
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {}
    
    def create_risk_algorithm_test(self, test_name: str, algorithms: List[Dict[str, Any]]) -> str:
        """Create test for different risk calculation algorithms"""
        test_config = {
            'test_name': test_name,
            'test_type': TestType.RISK_ALGORITHM.value,
            'description': f'Test different AI risk calculation algorithms: {", ".join([a["name"] for a in algorithms])}',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'traffic_split': 0.2,  # 20% of traffic
            'variants': algorithms,
            'primary_metric': 'assessment_accuracy',
            'secondary_metrics': ['completion_rate', 'user_satisfaction'],
            'minimum_sample_size': 1000,
            'confidence_level': 0.95
        }
        
        return self.create_test(test_config)
    
    def create_conversion_offer_test(self, test_name: str, offers: List[Dict[str, Any]]) -> str:
        """Create test for different conversion offers"""
        test_config = {
            'test_name': test_name,
            'test_type': TestType.CONVERSION_OFFER.value,
            'description': f'Test different conversion offers: {", ".join([o["name"] for o in offers])}',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'traffic_split': 0.3,  # 30% of traffic
            'variants': offers,
            'primary_metric': 'conversion_rate',
            'secondary_metrics': ['revenue_per_user', 'click_through_rate'],
            'minimum_sample_size': 500,
            'confidence_level': 0.95
        }
        
        return self.create_test(test_config)
    
    def create_personalization_test(self, test_name: str, strategies: List[Dict[str, Any]]) -> str:
        """Create test for different personalization strategies"""
        test_config = {
            'test_name': test_name,
            'test_type': TestType.PERSONALIZATION.value,
            'description': f'Test different personalization strategies: {", ".join([s["name"] for s in strategies])}',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=21)).isoformat(),
            'traffic_split': 0.25,  # 25% of traffic
            'variants': strategies,
            'primary_metric': 'engagement_rate',
            'secondary_metrics': ['time_on_page', 'step_completion_rate'],
            'minimum_sample_size': 750,
            'confidence_level': 0.95
        }
        
        return self.create_test(test_config)
    
    def create_urgency_test(self, test_name: str, urgency_configs: List[Dict[str, Any]]) -> str:
        """Create test for different urgency messaging"""
        test_config = {
            'test_name': test_name,
            'test_type': TestType.URGENCY_MESSAGING.value,
            'description': f'Test different urgency messaging: {", ".join([u["name"] for u in urgency_configs])}',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'traffic_split': 0.15,  # 15% of traffic
            'variants': urgency_configs,
            'primary_metric': 'conversion_rate',
            'secondary_metrics': ['time_to_convert', 'bounce_rate'],
            'minimum_sample_size': 300,
            'confidence_level': 0.95
        }
        
        return self.create_test(test_config)
    
    def _is_in_test_traffic(self, test: ABTest, user_id: Optional[str], session_id: Optional[str]) -> bool:
        """Check if user/session should be included in test"""
        if not test.traffic_split:
            return False
        
        # Use user_id or session_id to determine inclusion
        key = user_id or session_id
        if not key:
            return False
        
        # Hash the key and check if it falls within traffic split
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return (hash_value % 100) < (test.traffic_split * 100)
    
    def _track_variant_assignment(self, test_id: str, variant: str, 
                                user_id: Optional[str], session_id: Optional[str]) -> None:
        """Track variant assignment"""
        try:
            assignment_event = {
                'test_id': test_id,
                'variant': variant,
                'event_type': 'variant_assigned',
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self._store_test_event(assignment_event)
            
        except Exception as e:
            logger.error(f"Error tracking variant assignment: {e}")
    
    def _calculate_variant_performance(self, test_id: str, variant: str, 
                                     primary_metric: str) -> TestResult:
        """Calculate performance metrics for a variant"""
        try:
            # Get events for this variant
            events = self._get_test_events(test_id, variant)
            
            # Calculate metrics based on primary metric
            if primary_metric == 'conversion_rate':
                conversion_rate = self._calculate_conversion_rate(events)
                revenue_per_user = self._calculate_revenue_per_user(events)
                total_revenue = revenue_per_user * len(events)
            elif primary_metric == 'assessment_accuracy':
                conversion_rate = self._calculate_accuracy_rate(events)
                revenue_per_user = 0
                total_revenue = 0
            else:
                conversion_rate = 0
                revenue_per_user = 0
                total_revenue = 0
            
            return TestResult(
                test_id=test_id,
                variant=variant,
                sample_size=len(events),
                conversion_rate=conversion_rate,
                revenue_per_user=revenue_per_user,
                total_revenue=total_revenue,
                statistical_significance=0,  # Will be calculated separately
                confidence_interval=(0, 0),  # Will be calculated separately
                p_value=0  # Will be calculated separately
            )
            
        except Exception as e:
            logger.error(f"Error calculating variant performance: {e}")
            return TestResult(
                test_id=test_id,
                variant=variant,
                sample_size=0,
                conversion_rate=0,
                revenue_per_user=0,
                total_revenue=0,
                statistical_significance=0,
                confidence_interval=(0, 0),
                p_value=0
            )
    
    def _calculate_statistical_significance(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        try:
            if len(results) < 2:
                return {}
            
            # Simple chi-square test for conversion rates
            control = results[0]
            treatment = results[1]
            
            # Calculate chi-square statistic
            total_conversions = control.sample_size * control.conversion_rate + treatment.sample_size * treatment.conversion_rate
            total_sample = control.sample_size + treatment.sample_size
            expected_conversion_rate = total_conversions / total_sample
            
            chi_square = (
                ((control.sample_size * control.conversion_rate - control.sample_size * expected_conversion_rate) ** 2) / (control.sample_size * expected_conversion_rate) +
                ((treatment.sample_size * treatment.conversion_rate - treatment.sample_size * expected_conversion_rate) ** 2) / (treatment.sample_size * expected_conversion_rate)
            )
            
            # For 1 degree of freedom, chi-square critical value at 0.05 is 3.841
            is_significant = chi_square > 3.841
            
            return {
                'chi_square': chi_square,
                'is_significant': is_significant,
                'confidence_level': 0.95 if is_significant else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return {}
    
    def _generate_recommendation(self, results: List[TestResult], 
                               significance: Optional[Dict[str, Any]]) -> str:
        """Generate recommendation based on test results"""
        try:
            if not results or len(results) < 2:
                return "Insufficient data for recommendation"
            
            if not significance or not significance.get('is_significant'):
                return "No statistically significant difference found"
            
            # Find best performing variant
            best_variant = max(results, key=lambda r: r.conversion_rate)
            
            return f"Recommend implementing {best_variant.variant} (conversion rate: {best_variant.conversion_rate:.2%})"
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Error generating recommendation"
    
    def _load_active_tests(self) -> None:
        """Load active tests from database"""
        try:
            # This would load from database in production
            # For now, initialize empty
            self.active_tests = {}
        except Exception as e:
            logger.error(f"Error loading active tests: {e}")
    
    def _store_test_config(self, test: ABTest) -> None:
        """Store test configuration in database"""
        try:
            # This would store in database in production
            # For now, just log
            logger.info(f"Stored test config: {test.test_id}")
        except Exception as e:
            logger.error(f"Error storing test config: {e}")
    
    def _get_test_config(self, test_id: str) -> Optional[ABTest]:
        """Get test configuration from database"""
        try:
            # This would retrieve from database in production
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting test config: {e}")
            return None
    
    def _update_test_config(self, test: ABTest) -> None:
        """Update test configuration in database"""
        try:
            # This would update in database in production
            # For now, just log
            logger.info(f"Updated test config: {test.test_id}")
        except Exception as e:
            logger.error(f"Error updating test config: {e}")
    
    def _store_test_event(self, event: Dict[str, Any]) -> None:
        """Store test event in database"""
        try:
            # This would store in database in production
            # For now, just log
            logger.debug(f"Stored test event: {event}")
        except Exception as e:
            logger.error(f"Error storing test event: {e}")
    
    def _get_test_events(self, test_id: str, variant: str) -> List[Dict[str, Any]]:
        """Get test events from database"""
        try:
            # This would retrieve from database in production
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting test events: {e}")
            return []
    
    def _calculate_conversion_rate(self, events: List[Dict[str, Any]]) -> float:
        """Calculate conversion rate from events"""
        try:
            if not events:
                return 0.0
            
            conversions = sum(1 for e in events if e.get('event_type') == EventType.PAID_UPGRADE_CLICKED.value)
            return conversions / len(events)
        except Exception as e:
            logger.error(f"Error calculating conversion rate: {e}")
            return 0.0
    
    def _calculate_revenue_per_user(self, events: List[Dict[str, Any]]) -> float:
        """Calculate revenue per user from events"""
        try:
            if not events:
                return 0.0
            
            # This would calculate actual revenue in production
            # For now, return estimated value
            return 59.99
        except Exception as e:
            logger.error(f"Error calculating revenue per user: {e}")
            return 0.0
    
    def _calculate_accuracy_rate(self, events: List[Dict[str, Any]]) -> float:
        """Calculate accuracy rate from events"""
        try:
            if not events:
                return 0.0
            
            # This would calculate actual accuracy in production
            # For now, return estimated value
            return 0.85
        except Exception as e:
            logger.error(f"Error calculating accuracy rate: {e}")
            return 0.0

# Global A/B testing instance
ai_calculator_ab_testing = AICalculatorABTesting()
