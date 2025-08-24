import logging
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import os

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """A/B test status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ANALYZING = "analyzing"

class ResponseType(Enum):
    """Response types for tracking"""
    CLICK = "click"
    REPLY = "reply"
    ACTION = "action"
    CONVERSION = "conversion"
    OPT_OUT = "opt_out"
    HELP_REQUEST = "help_request"

@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_id: str
    template_id: str
    test_name: str
    description: str
    variations: List[str]  # List of variation IDs
    traffic_split: Dict[str, float]  # Percentage for each variation
    start_date: datetime
    end_date: datetime
    status: TestStatus
    success_metric: str  # Primary metric to optimize
    min_sample_size: int = 100
    confidence_level: float = 0.95
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TestResult:
    """A/B test result"""
    test_id: str
    variation_id: str
    sent_count: int
    response_count: int
    response_rate: float
    conversion_count: int
    conversion_rate: float
    avg_response_time: float
    confidence_interval: Tuple[float, float]
    is_winner: bool = False
    statistical_significance: float = 0.0

class SMSABTestingFramework:
    """A/B testing framework for SMS message effectiveness"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        
        # Active tests cache
        self.active_tests = {}
        self._load_active_tests()
    
    def create_test(self, config: ABTestConfig) -> bool:
        """
        Create a new A/B test
        
        Args:
            config: A/B test configuration
        
        Returns:
            True if test created successfully
        """
        try:
            # Validate configuration
            if not self._validate_test_config(config):
                return False
            
            # Store test configuration
            test_key = f"ab_test_config:{config.test_id}"
            test_data = {
                'test_id': config.test_id,
                'template_id': config.template_id,
                'test_name': config.test_name,
                'description': config.description,
                'variations': config.variations,
                'traffic_split': config.traffic_split,
                'start_date': config.start_date.isoformat(),
                'end_date': config.end_date.isoformat(),
                'status': config.status.value,
                'success_metric': config.success_metric,
                'min_sample_size': config.min_sample_size,
                'confidence_level': config.confidence_level,
                'created_at': config.created_at.isoformat()
            }
            
            self.redis_client.setex(test_key, 86400 * 90, json.dumps(test_data))  # 90 days
            
            # Add to active tests
            if config.status == TestStatus.ACTIVE:
                self.active_tests[config.test_id] = config
            
            logger.info(f"Created A/B test: {config.test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            return False
    
    def get_variation_for_user(self, test_id: str, user_id: str) -> Optional[str]:
        """
        Get test variation for a user
        
        Args:
            test_id: Test ID
            user_id: User ID
        
        Returns:
            Variation ID or None if test not found
        """
        try:
            # Check if test is active
            if test_id not in self.active_tests:
                return None
            
            test_config = self.active_tests[test_id]
            
            # Check if test is within date range
            now = datetime.utcnow()
            if now < test_config.start_date or now > test_config.end_date:
                return None
            
            # Check if user already has a variation assigned
            assignment_key = f"ab_test_assignment:{test_id}:{user_id}"
            existing_assignment = self.redis_client.get(assignment_key)
            
            if existing_assignment:
                return existing_assignment
            
            # Assign variation based on traffic split
            variation = self._assign_variation(test_config, user_id)
            
            # Store assignment
            self.redis_client.setex(assignment_key, 86400 * 30, variation)  # 30 days
            
            # Track assignment
            self._track_assignment(test_id, variation, user_id)
            
            return variation
            
        except Exception as e:
            logger.error(f"Error getting variation for user: {e}")
            return None
    
    def track_message_sent(self, test_id: str, variation_id: str, user_id: str, 
                          message_data: Dict[str, Any]):
        """
        Track when a message is sent
        
        Args:
            test_id: Test ID
            variation_id: Variation ID
            user_id: User ID
            message_data: Message data
        """
        try:
            tracking_data = {
                'test_id': test_id,
                'variation_id': variation_id,
                'user_id': user_id,
                'sent_at': datetime.utcnow().isoformat(),
                'message_data': message_data
            }
            
            # Store sent tracking
            sent_key = f"ab_test_sent:{test_id}:{variation_id}:{user_id}"
            self.redis_client.setex(sent_key, 86400 * 30, json.dumps(tracking_data))
            
            # Increment sent counter
            counter_key = f"ab_test_sent_count:{test_id}:{variation_id}"
            self.redis_client.incr(counter_key)
            
        except Exception as e:
            logger.error(f"Error tracking message sent: {e}")
    
    def track_response(self, test_id: str, variation_id: str, user_id: str, 
                      response_type: ResponseType, response_data: Dict[str, Any] = None):
        """
        Track user response to message
        
        Args:
            test_id: Test ID
            variation_id: Variation ID
            user_id: User ID
            response_type: Type of response
            response_data: Additional response data
        """
        try:
            tracking_data = {
                'test_id': test_id,
                'variation_id': variation_id,
                'user_id': user_id,
                'response_type': response_type.value,
                'response_data': response_data or {},
                'responded_at': datetime.utcnow().isoformat()
            }
            
            # Store response tracking
            response_key = f"ab_test_response:{test_id}:{variation_id}:{user_id}"
            self.redis_client.setex(response_key, 86400 * 30, json.dumps(tracking_data))
            
            # Increment response counter
            counter_key = f"ab_test_response_count:{test_id}:{variation_id}:{response_type.value}"
            self.redis_client.incr(counter_key)
            
            # Track response time if we have sent data
            sent_key = f"ab_test_sent:{test_id}:{variation_id}:{user_id}"
            sent_data = self.redis_client.get(sent_key)
            
            if sent_data:
                sent_info = json.loads(sent_data)
                sent_time = datetime.fromisoformat(sent_info['sent_at'])
                response_time = datetime.utcnow() - sent_time
                
                # Store response time
                time_key = f"ab_test_response_time:{test_id}:{variation_id}"
                self.redis_client.lpush(time_key, response_time.total_seconds())
                self.redis_client.ltrim(time_key, 0, 999)  # Keep last 1000 times
            
        except Exception as e:
            logger.error(f"Error tracking response: {e}")
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        Get A/B test results
        
        Args:
            test_id: Test ID
        
        Returns:
            Test results with statistical analysis
        """
        try:
            # Get test configuration
            test_config = self._get_test_config(test_id)
            if not test_config:
                return {'error': 'Test not found'}
            
            results = {
                'test_id': test_id,
                'test_name': test_config.test_name,
                'status': test_config.status.value,
                'variations': {},
                'statistical_analysis': {},
                'recommendation': None
            }
            
            # Get results for each variation
            for variation_id in test_config.variations:
                variation_results = self._get_variation_results(test_id, variation_id)
                results['variations'][variation_id] = variation_results
            
            # Perform statistical analysis
            statistical_analysis = self._perform_statistical_analysis(test_id, test_config)
            results['statistical_analysis'] = statistical_analysis
            
            # Generate recommendation
            recommendation = self._generate_recommendation(test_id, test_config, results)
            results['recommendation'] = recommendation
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {'error': str(e)}
    
    def _validate_test_config(self, config: ABTestConfig) -> bool:
        """Validate test configuration"""
        try:
            # Check required fields
            if not config.test_id or not config.template_id or not config.variations:
                return False
            
            # Check traffic split adds to 100%
            total_split = sum(config.traffic_split.values())
            if abs(total_split - 100.0) > 0.01:
                return False
            
            # Check date range
            if config.start_date >= config.end_date:
                return False
            
            # Check minimum sample size
            if config.min_sample_size < 10:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating test config: {e}")
            return False
    
    def _assign_variation(self, test_config: ABTestConfig, user_id: str) -> str:
        """Assign variation based on traffic split"""
        try:
            # Use user ID hash for consistent assignment
            user_hash = hash(user_id) % 100
            
            cumulative_percentage = 0
            for variation_id, percentage in test_config.traffic_split.items():
                cumulative_percentage += percentage
                if user_hash < cumulative_percentage:
                    return variation_id
            
            # Fallback to first variation
            return test_config.variations[0]
            
        except Exception as e:
            logger.error(f"Error assigning variation: {e}")
            return test_config.variations[0] if test_config.variations else None
    
    def _track_assignment(self, test_id: str, variation_id: str, user_id: str):
        """Track variation assignment"""
        try:
            assignment_data = {
                'test_id': test_id,
                'variation_id': variation_id,
                'user_id': user_id,
                'assigned_at': datetime.utcnow().isoformat()
            }
            
            # Store assignment
            assignment_key = f"ab_test_assignment_log:{test_id}:{user_id}"
            self.redis_client.setex(assignment_key, 86400 * 30, json.dumps(assignment_data))
            
            # Increment assignment counter
            counter_key = f"ab_test_assignment_count:{test_id}:{variation_id}"
            self.redis_client.incr(counter_key)
            
        except Exception as e:
            logger.error(f"Error tracking assignment: {e}")
    
    def _get_variation_results(self, test_id: str, variation_id: str) -> Dict[str, Any]:
        """Get results for a specific variation"""
        try:
            # Get sent count
            sent_key = f"ab_test_sent_count:{test_id}:{variation_id}"
            sent_count = int(self.redis_client.get(sent_key) or 0)
            
            # Get response counts by type
            response_counts = {}
            total_responses = 0
            
            for response_type in ResponseType:
                response_key = f"ab_test_response_count:{test_id}:{variation_id}:{response_type.value}"
                count = int(self.redis_client.get(response_key) or 0)
                response_counts[response_type.value] = count
                total_responses += count
            
            # Calculate response rate
            response_rate = (total_responses / sent_count * 100) if sent_count > 0 else 0
            
            # Get conversion count (assuming conversion is the primary metric)
            conversion_count = response_counts.get('conversion', 0)
            conversion_rate = (conversion_count / sent_count * 100) if sent_count > 0 else 0
            
            # Get average response time
            time_key = f"ab_test_response_time:{test_id}:{variation_id}"
            response_times = self.redis_client.lrange(time_key, 0, -1)
            avg_response_time = 0
            
            if response_times:
                times = [float(t) for t in response_times]
                avg_response_time = statistics.mean(times)
            
            return {
                'variation_id': variation_id,
                'sent_count': sent_count,
                'response_counts': response_counts,
                'total_responses': total_responses,
                'response_rate': response_rate,
                'conversion_count': conversion_count,
                'conversion_rate': conversion_rate,
                'avg_response_time': avg_response_time
            }
            
        except Exception as e:
            logger.error(f"Error getting variation results: {e}")
            return {}
    
    def _perform_statistical_analysis(self, test_id: str, test_config: ABTestConfig) -> Dict[str, Any]:
        """Perform statistical analysis on test results"""
        try:
            analysis = {
                'confidence_level': test_config.confidence_level,
                'statistical_significance': {},
                'confidence_intervals': {},
                'effect_size': {},
                'recommendation': None
            }
            
            # Get results for all variations
            variations_data = []
            for variation_id in test_config.variations:
                results = self._get_variation_results(test_id, variation_id)
                if results:
                    variations_data.append(results)
            
            if len(variations_data) < 2:
                return analysis
            
            # Calculate statistical significance
            # This is a simplified version - in production, you'd use proper statistical tests
            control_variation = variations_data[0]
            test_variations = variations_data[1:]
            
            for test_var in test_variations:
                # Calculate confidence interval for difference in conversion rates
                control_rate = control_variation['conversion_rate'] / 100
                test_rate = test_var['conversion_rate'] / 100
                
                # Simplified confidence interval calculation
                # In production, use proper statistical methods
                n1, n2 = control_variation['sent_count'], test_var['sent_count']
                
                if n1 > 0 and n2 > 0:
                    # Standard error of difference
                    se = ((control_rate * (1 - control_rate) / n1) + 
                          (test_rate * (1 - test_rate) / n2)) ** 0.5
                    
                    # Z-score for confidence level
                    z_score = 1.96  # For 95% confidence
                    
                    # Confidence interval
                    diff = test_rate - control_rate
                    margin_of_error = z_score * se
                    ci_lower = diff - margin_of_error
                    ci_upper = diff + margin_of_error
                    
                    analysis['confidence_intervals'][test_var['variation_id']] = {
                        'lower': ci_lower * 100,
                        'upper': ci_upper * 100,
                        'includes_zero': ci_lower <= 0 <= ci_upper
                    }
                    
                    # Statistical significance
                    analysis['statistical_significance'][test_var['variation_id']] = {
                        'significant': not (ci_lower <= 0 <= ci_upper),
                        'p_value': self._calculate_p_value(control_rate, test_rate, n1, n2)
                    }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing statistical analysis: {e}")
            return {}
    
    def _calculate_p_value(self, p1: float, p2: float, n1: int, n2: int) -> float:
        """Calculate p-value for difference in proportions"""
        try:
            # Simplified p-value calculation
            # In production, use proper statistical libraries
            if n1 == 0 or n2 == 0:
                return 1.0
            
            # Pooled proportion
            pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)
            
            # Standard error
            se = (pooled_p * (1 - pooled_p) * (1/n1 + 1/n2)) ** 0.5
            
            if se == 0:
                return 1.0
            
            # Z-score
            z = (p2 - p1) / se
            
            # Simplified p-value (two-tailed)
            # In production, use scipy.stats or similar
            if abs(z) > 1.96:
                return 0.05  # Significant
            else:
                return 0.5   # Not significant
                
        except Exception as e:
            logger.error(f"Error calculating p-value: {e}")
            return 1.0
    
    def _generate_recommendation(self, test_id: str, test_config: ABTestConfig, 
                               results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendation based on test results"""
        try:
            recommendation = {
                'action': 'continue_test',
                'reason': 'Insufficient data',
                'best_variation': None,
                'confidence': 'low'
            }
            
            # Check if we have enough data
            total_sent = sum(var['sent_count'] for var in results['variations'].values())
            if total_sent < test_config.min_sample_size:
                return recommendation
            
            # Find best performing variation
            best_variation = None
            best_rate = 0
            
            for variation_id, data in results['variations'].items():
                if data['conversion_rate'] > best_rate:
                    best_rate = data['conversion_rate']
                    best_variation = variation_id
            
            if not best_variation:
                return recommendation
            
            # Check statistical significance
            significance_data = results['statistical_analysis'].get('statistical_significance', {})
            significant_variations = [
                var_id for var_id, data in significance_data.items()
                if data.get('significant', False)
            ]
            
            if significant_variations:
                # We have a statistically significant winner
                recommendation['action'] = 'implement_winner'
                recommendation['best_variation'] = best_variation
                recommendation['reason'] = f'Variation {best_variation} shows statistically significant improvement'
                recommendation['confidence'] = 'high'
            else:
                # No significant difference, but we have a best performer
                recommendation['action'] = 'consider_winner'
                recommendation['best_variation'] = best_variation
                recommendation['reason'] = f'Variation {best_variation} performs best but not statistically significant'
                recommendation['confidence'] = 'medium'
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {'action': 'error', 'reason': str(e)}
    
    def _get_test_config(self, test_id: str) -> Optional[ABTestConfig]:
        """Get test configuration from Redis"""
        try:
            test_key = f"ab_test_config:{test_id}"
            test_data = self.redis_client.get(test_key)
            
            if not test_data:
                return None
            
            data = json.loads(test_data)
            
            return ABTestConfig(
                test_id=data['test_id'],
                template_id=data['template_id'],
                test_name=data['test_name'],
                description=data['description'],
                variations=data['variations'],
                traffic_split=data['traffic_split'],
                start_date=datetime.fromisoformat(data['start_date']),
                end_date=datetime.fromisoformat(data['end_date']),
                status=TestStatus(data['status']),
                success_metric=data['success_metric'],
                min_sample_size=data['min_sample_size'],
                confidence_level=data['confidence_level'],
                created_at=datetime.fromisoformat(data['created_at'])
            )
            
        except Exception as e:
            logger.error(f"Error getting test config: {e}")
            return None
    
    def _load_active_tests(self):
        """Load active tests from Redis"""
        try:
            # This would typically scan Redis for active test configurations
            # For now, we'll use a simplified approach
            pass
            
        except Exception as e:
            logger.error(f"Error loading active tests: {e}")

# Create singleton instance
sms_ab_testing = None  # Will be initialized with db session 