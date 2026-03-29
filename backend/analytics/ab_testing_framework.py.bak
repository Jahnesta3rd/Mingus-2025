#!/usr/bin/env python3
"""
A/B Testing Framework for Job Recommendation Engine

This module provides comprehensive A/B testing capabilities for optimizing
job recommendations, including test design, user assignment, metrics tracking,
and statistical analysis to improve recommendation effectiveness.

Features:
- A/B test design and management
- User assignment and traffic splitting
- Conversion tracking and metrics collection
- Statistical significance testing
- Test result analysis and reporting
- Automated test completion and rollback
- Multi-variant testing support
"""

import sqlite3
import json
import logging
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """A/B test status values"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestType(Enum):
    """Types of A/B tests"""
    RECOMMENDATION_ALGORITHM = "recommendation_algorithm"
    UI_LAYOUT = "ui_layout"
    MESSAGING = "messaging"
    PRICING = "pricing"
    FEATURE_FLAG = "feature_flag"
    RECOMMENDATION_TIER = "recommendation_tier"

@dataclass
class ABTest:
    """Data class for A/B test definition"""
    test_id: str
    test_name: str
    description: str
    hypothesis: str
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    target_metric: str
    success_threshold: float
    minimum_sample_size: int
    created_by: str

@dataclass
class TestVariant:
    """Data class for A/B test variant"""
    variant_id: str
    test_id: str
    variant_name: str
    variant_description: str
    configuration: Dict[str, Any]
    traffic_percentage: float
    is_control: bool = False

@dataclass
class TestAssignment:
    """Data class for user test assignment"""
    test_id: str
    user_id: str
    variant_id: str
    assigned_at: datetime
    conversion_events: Dict[str, Any] = None

@dataclass
class TestResult:
    """Data class for A/B test results"""
    test_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    sample_size: int
    confidence_interval_lower: float
    confidence_interval_upper: float
    statistical_significance: float

class ABTestFramework:
    """
    Comprehensive A/B testing framework for job recommendation optimization.
    
    Provides test design, user assignment, metrics tracking, and statistical
    analysis to continuously improve recommendation effectiveness.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the A/B testing framework"""
        self.db_path = db_path
        self._init_database()
        logger.info("ABTestFramework initialized successfully")
    
    def _init_database(self):
        """Initialize the analytics database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read and execute the schema
            with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("A/B testing database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing A/B testing database: {e}")
            raise
    
    def create_test(
        self,
        test_name: str,
        description: str,
        hypothesis: str,
        target_metric: str,
        success_threshold: float,
        minimum_sample_size: int = 1000,
        duration_days: int = 14,
        created_by: str = "system"
    ) -> str:
        """
        Create a new A/B test
        
        Args:
            test_name: Name of the test
            description: Test description
            hypothesis: Test hypothesis
            target_metric: Primary metric to measure
            success_threshold: Minimum improvement threshold
            minimum_sample_size: Minimum sample size per variant
            duration_days: Test duration in days
            created_by: Creator of the test
            
        Returns:
            test_id: Unique test identifier
        """
        try:
            test_id = str(uuid.uuid4())
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)
            
            test = ABTest(
                test_id=test_id,
                test_name=test_name,
                description=description,
                hypothesis=hypothesis,
                start_date=start_date,
                end_date=end_date,
                status=TestStatus.DRAFT.value,
                target_metric=target_metric,
                success_threshold=success_threshold,
                minimum_sample_size=minimum_sample_size,
                created_by=created_by
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ab_tests (
                    test_id, test_name, description, hypothesis, start_date,
                    end_date, status, target_metric, success_threshold, minimum_sample_size, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test.test_id, test.test_name, test.description, test.hypothesis,
                test.start_date, test.end_date, test.status, test.target_metric,
                test.success_threshold, test.minimum_sample_size, test.created_by
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created A/B test: {test_name} ({test_id})")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    def add_variant(
        self,
        test_id: str,
        variant_name: str,
        variant_description: str,
        configuration: Dict[str, Any],
        traffic_percentage: float,
        is_control: bool = False
    ) -> str:
        """
        Add a variant to an A/B test
        
        Args:
            test_id: Test identifier
            variant_name: Name of the variant
            variant_description: Description of the variant
            configuration: Variant configuration (JSON)
            traffic_percentage: Percentage of traffic for this variant
            is_control: Whether this is the control variant
            
        Returns:
            variant_id: Unique variant identifier
        """
        try:
            variant_id = str(uuid.uuid4())
            
            variant = TestVariant(
                variant_id=variant_id,
                test_id=test_id,
                variant_name=variant_name,
                variant_description=variant_description,
                configuration=configuration,
                traffic_percentage=traffic_percentage,
                is_control=is_control
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ab_test_variants (
                    variant_id, test_id, variant_name, variant_description,
                    configuration, traffic_percentage, is_control
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                variant.variant_id, variant.test_id, variant.variant_name,
                variant.variant_description, json.dumps(variant.configuration),
                variant.traffic_percentage, variant.is_control
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added variant {variant_name} to test {test_id}")
            return variant_id
            
        except Exception as e:
            logger.error(f"Error adding variant: {e}")
            raise
    
    def start_test(self, test_id: str) -> bool:
        """
        Start an A/B test
        
        Args:
            test_id: Test identifier
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Validate test has variants
            cursor.execute('''
                SELECT COUNT(*) FROM ab_test_variants WHERE test_id = ?
            ''', (test_id,))
            
            variant_count = cursor.fetchone()[0]
            if variant_count < 2:
                logger.error(f"Test {test_id} needs at least 2 variants")
                return False
            
            # Validate traffic percentages sum to 100
            cursor.execute('''
                SELECT SUM(traffic_percentage) FROM ab_test_variants WHERE test_id = ?
            ''', (test_id,))
            
            total_traffic = cursor.fetchone()[0]
            if abs(total_traffic - 100.0) > 0.01:  # Allow small floating point errors
                logger.error(f"Test {test_id} traffic percentages must sum to 100%")
                return False
            
            # Start the test
            cursor.execute('''
                UPDATE ab_tests SET status = ?, start_date = ? WHERE test_id = ?
            ''', (TestStatus.ACTIVE.value, datetime.now(), test_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Started A/B test: {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting A/B test: {e}")
            return False
    
    def assign_user_to_test(
        self,
        test_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Assign a user to a test variant
        
        Args:
            test_id: Test identifier
            user_id: User identifier
            
        Returns:
            variant_id: Assigned variant identifier or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user is already assigned
            cursor.execute('''
                SELECT variant_id FROM ab_test_assignments 
                WHERE test_id = ? AND user_id = ?
            ''', (test_id, user_id))
            
            existing_assignment = cursor.fetchone()
            if existing_assignment:
                return existing_assignment[0]
            
            # Check if test is active
            cursor.execute('''
                SELECT status, end_date FROM ab_tests WHERE test_id = ?
            ''', (test_id,))
            
            test_info = cursor.fetchone()
            if not test_info or test_info[0] != TestStatus.ACTIVE.value:
                return None
            
            if test_info[1] and datetime.fromisoformat(test_info[1]) < datetime.now():
                return None
            
            # Get variants with traffic percentages
            cursor.execute('''
                SELECT variant_id, traffic_percentage FROM ab_test_variants 
                WHERE test_id = ? ORDER BY variant_id
            ''', (test_id,))
            
            variants = cursor.fetchall()
            if not variants:
                return None
            
            # Assign user to variant based on traffic percentages
            variant_id = self._assign_variant_by_traffic(user_id, variants)
            
            # Record assignment
            cursor.execute('''
                INSERT INTO ab_test_assignments (test_id, user_id, variant_id, assigned_at)
                VALUES (?, ?, ?, ?)
            ''', (test_id, user_id, variant_id, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Assigned user {user_id} to variant {variant_id} in test {test_id}")
            return variant_id
            
        except Exception as e:
            logger.error(f"Error assigning user to test: {e}")
            return None
    
    def _assign_variant_by_traffic(
        self,
        user_id: str,
        variants: List[Tuple[str, float]]
    ) -> str:
        """Assign user to variant based on traffic percentages using consistent hashing"""
        # Use user_id hash for consistent assignment
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        random.seed(user_hash)
        
        # Generate random number between 0 and 100
        random_value = random.uniform(0, 100)
        
        # Find variant based on cumulative traffic percentage
        cumulative_percentage = 0
        for variant_id, traffic_percentage in variants:
            cumulative_percentage += traffic_percentage
            if random_value <= cumulative_percentage:
                return variant_id
        
        # Fallback to last variant
        return variants[-1][0]
    
    def track_conversion(
        self,
        test_id: str,
        user_id: str,
        conversion_event: str,
        value: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Track conversion event for a user in a test
        
        Args:
            test_id: Test identifier
            user_id: User identifier
            conversion_event: Name of the conversion event
            value: Value of the conversion
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's current conversion events
            cursor.execute('''
                SELECT conversion_events FROM ab_test_assignments 
                WHERE test_id = ? AND user_id = ?
            ''', (test_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"User {user_id} not assigned to test {test_id}")
                return False
            
            conversion_events = json.loads(result[0]) if result[0] else {}
            
            # Add new conversion event
            if conversion_event not in conversion_events:
                conversion_events[conversion_event] = []
            
            conversion_events[conversion_event].append({
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            })
            
            # Update conversion events
            cursor.execute('''
                UPDATE ab_test_assignments 
                SET conversion_events = ? 
                WHERE test_id = ? AND user_id = ?
            ''', (json.dumps(conversion_events), test_id, user_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Tracked conversion {conversion_event} for user {user_id} in test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            return False
    
    def get_test_results(
        self,
        test_id: str,
        metric_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get A/B test results with statistical analysis
        
        Args:
            test_id: Test identifier
            metric_name: Specific metric to analyze (optional)
            
        Returns:
            Dict containing test results and statistical analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get test information
            cursor.execute('''
                SELECT test_name, target_metric, success_threshold, minimum_sample_size
                FROM ab_tests WHERE test_id = ?
            ''', (test_id,))
            
            test_info = cursor.fetchone()
            if not test_info:
                return {'error': 'Test not found'}
            
            test_name, target_metric, success_threshold, minimum_sample_size = test_info
            
            # Get variants
            cursor.execute('''
                SELECT variant_id, variant_name, is_control, traffic_percentage
                FROM ab_test_variants WHERE test_id = ?
                ORDER BY is_control DESC, variant_name
            ''', (test_id,))
            
            variants = cursor.fetchall()
            
            # Analyze each variant
            variant_results = []
            control_variant = None
            
            for variant_id, variant_name, is_control, traffic_percentage in variants:
                # Get conversion data for this variant
                cursor.execute('''
                    SELECT conversion_events FROM ab_test_assignments 
                    WHERE test_id = ? AND variant_id = ?
                ''', (test_id, variant_id))
                
                conversion_data = cursor.fetchall()
                
                # Calculate metrics
                metrics = self._calculate_variant_metrics(
                    conversion_data, metric_name or target_metric
                )
                
                variant_result = {
                    'variant_id': variant_id,
                    'variant_name': variant_name,
                    'is_control': bool(is_control),
                    'traffic_percentage': traffic_percentage,
                    'sample_size': len(conversion_data),
                    'metrics': metrics
                }
                
                variant_results.append(variant_result)
                
                if is_control:
                    control_variant = variant_result
            
            # Calculate statistical significance
            if control_variant and len(variant_results) > 1:
                for variant_result in variant_results:
                    if not variant_result['is_control']:
                        significance = self._calculate_statistical_significance(
                            control_variant, variant_result, target_metric
                        )
                        variant_result['statistical_significance'] = significance
            
            # Determine test status
            test_status = self._determine_test_status(variant_results, success_threshold, minimum_sample_size)
            
            conn.close()
            
            return {
                'test_id': test_id,
                'test_name': test_name,
                'target_metric': target_metric,
                'success_threshold': success_threshold,
                'test_status': test_status,
                'variants': variant_results,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {'error': str(e)}
    
    def _calculate_variant_metrics(
        self,
        conversion_data: List[Tuple[str]],
        metric_name: str
    ) -> Dict[str, Any]:
        """Calculate metrics for a variant"""
        if not conversion_data:
            return {
                'conversion_rate': 0.0,
                'average_value': 0.0,
                'total_value': 0.0,
                'unique_conversions': 0
            }
        
        total_users = len(conversion_data)
        conversions = 0
        total_value = 0.0
        values = []
        
        for conversion_events_json, in conversion_data:
            if not conversion_events_json:
                continue
                
            conversion_events = json.loads(conversion_events_json)
            
            if metric_name in conversion_events:
                conversions += 1
                for event in conversion_events[metric_name]:
                    value = event.get('value', 1.0)
                    total_value += value
                    values.append(value)
        
        conversion_rate = (conversions / total_users * 100) if total_users > 0 else 0
        average_value = (total_value / conversions) if conversions > 0 else 0
        
        return {
            'conversion_rate': round(conversion_rate, 2),
            'average_value': round(average_value, 2),
            'total_value': round(total_value, 2),
            'unique_conversions': conversions,
            'values': values
        }
    
    def _calculate_statistical_significance(
        self,
        control_variant: Dict[str, Any],
        test_variant: Dict[str, Any],
        metric_name: str
    ) -> Dict[str, Any]:
        """Calculate statistical significance between control and test variant"""
        try:
            control_values = control_variant['metrics'].get('values', [])
            test_values = test_variant['metrics'].get('values', [])
            
            if not control_values or not test_values:
                return {'p_value': 1.0, 'is_significant': False, 'confidence_level': 0.0}
            
            # Perform t-test
            p_value = self._perform_t_test(control_values, test_values)
            
            # Calculate confidence interval
            control_mean = statistics.mean(control_values)
            test_mean = statistics.mean(test_values)
            improvement = ((test_mean - control_mean) / control_mean * 100) if control_mean > 0 else 0
            
            # Calculate confidence interval for the difference
            ci_lower, ci_upper = self._calculate_confidence_interval(control_values, test_values)
            
            return {
                'p_value': round(p_value, 4),
                'is_significant': p_value < 0.05,
                'confidence_level': round((1 - p_value) * 100, 2),
                'improvement_percentage': round(improvement, 2),
                'confidence_interval_lower': round(ci_lower, 4),
                'confidence_interval_upper': round(ci_upper, 4)
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return {'p_value': 1.0, 'is_significant': False, 'confidence_level': 0.0}
    
    def _perform_t_test(self, group1: List[float], group2: List[float]) -> float:
        """Perform two-sample t-test"""
        try:
            n1, n2 = len(group1), len(group2)
            if n1 < 2 or n2 < 2:
                return 1.0
            
            mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
            var1, var2 = statistics.variance(group1), statistics.variance(group2)
            
            # Pooled variance
            pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
            
            # Standard error
            se = math.sqrt(pooled_var * (1/n1 + 1/n2))
            
            # t-statistic
            t_stat = (mean1 - mean2) / se
            
            # Degrees of freedom
            df = n1 + n2 - 2
            
            # Approximate p-value (simplified)
            if abs(t_stat) > 2.576:  # 99% confidence
                return 0.01
            elif abs(t_stat) > 1.96:  # 95% confidence
                return 0.05
            elif abs(t_stat) > 1.645:  # 90% confidence
                return 0.10
            else:
                return 0.20
                
        except Exception:
            return 1.0
    
    def _calculate_confidence_interval(
        self,
        group1: List[float],
        group2: List[float],
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the difference of means"""
        try:
            n1, n2 = len(group1), len(group2)
            if n1 < 2 or n2 < 2:
                return (0.0, 0.0)
            
            mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
            var1, var2 = statistics.variance(group1), statistics.variance(group2)
            
            # Pooled variance
            pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
            
            # Standard error
            se = math.sqrt(pooled_var * (1/n1 + 1/n2))
            
            # t-value for confidence level
            t_value = 1.96 if confidence_level == 0.95 else 2.576  # Simplified
            
            # Confidence interval
            margin_of_error = t_value * se
            difference = mean1 - mean2
            
            return (difference - margin_of_error, difference + margin_of_error)
            
        except Exception:
            return (0.0, 0.0)
    
    def _determine_test_status(
        self,
        variant_results: List[Dict[str, Any]],
        success_threshold: float,
        minimum_sample_size: int
    ) -> str:
        """Determine the current status of the test"""
        # Check if all variants have minimum sample size
        for variant in variant_results:
            if variant['sample_size'] < minimum_sample_size:
                return 'collecting_data'
        
        # Check for statistical significance
        for variant in variant_results:
            if not variant['is_control']:
                significance = variant.get('statistical_significance', {})
                if significance.get('is_significant', False):
                    improvement = significance.get('improvement_percentage', 0)
                    if improvement >= success_threshold:
                        return 'winner_found'
                    elif improvement <= -success_threshold:
                        return 'control_better'
        
        return 'inconclusive'
    
    def complete_test(
        self,
        test_id: str,
        winning_variant_id: Optional[str] = None
    ) -> bool:
        """
        Complete an A/B test and optionally roll out winning variant
        
        Args:
            test_id: Test identifier
            winning_variant_id: ID of winning variant (optional)
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update test status
            cursor.execute('''
                UPDATE ab_tests SET status = ?, end_date = ? WHERE test_id = ?
            ''', (TestStatus.COMPLETED.value, datetime.now(), test_id))
            
            # Store final results
            results = self.get_test_results(test_id)
            if 'error' not in results:
                for variant in results.get('variants', []):
                    cursor.execute('''
                        INSERT INTO ab_test_results (
                            test_id, variant_id, metric_name, metric_value,
                            sample_size, confidence_interval_lower,
                            confidence_interval_upper, statistical_significance
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_id, variant['variant_id'], results['target_metric'],
                        variant['metrics']['conversion_rate'], variant['sample_size'],
                        variant.get('statistical_significance', {}).get('confidence_interval_lower', 0),
                        variant.get('statistical_significance', {}).get('confidence_interval_upper', 0),
                        variant.get('statistical_significance', {}).get('confidence_level', 0)
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Completed A/B test: {test_id}")
            if winning_variant_id:
                logger.info(f"Winning variant: {winning_variant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing A/B test: {e}")
            return False
    
    def get_active_tests(self) -> List[Dict[str, Any]]:
        """Get all active A/B tests"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    t.test_id, t.test_name, t.description, t.target_metric,
                    t.success_threshold, t.minimum_sample_size, t.start_date,
                    COUNT(a.user_id) as assigned_users,
                    COUNT(v.variant_id) as variant_count
                FROM ab_tests t
                LEFT JOIN ab_test_assignments a ON t.test_id = a.test_id
                LEFT JOIN ab_test_variants v ON t.test_id = v.test_id
                WHERE t.status = ?
                GROUP BY t.test_id
                ORDER BY t.start_date DESC
            ''', (TestStatus.ACTIVE.value,))
            
            active_tests = []
            for row in cursor.fetchall():
                active_tests.append({
                    'test_id': row[0],
                    'test_name': row[1],
                    'description': row[2],
                    'target_metric': row[3],
                    'success_threshold': row[4],
                    'minimum_sample_size': row[5],
                    'start_date': row[6],
                    'assigned_users': row[7],
                    'variant_count': row[8]
                })
            
            conn.close()
            return active_tests
            
        except Exception as e:
            logger.error(f"Error getting active tests: {e}")
            return []
    
    def get_test_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get A/B test history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    t.test_id, t.test_name, t.status, t.start_date, t.end_date,
                    t.target_metric, t.success_threshold,
                    COUNT(a.user_id) as total_users,
                    COUNT(DISTINCT v.variant_id) as variant_count
                FROM ab_tests t
                LEFT JOIN ab_test_assignments a ON t.test_id = a.test_id
                LEFT JOIN ab_test_variants v ON t.test_id = v.test_id
                GROUP BY t.test_id
                ORDER BY t.start_date DESC
                LIMIT ?
            ''', (limit,))
            
            test_history = []
            for row in cursor.fetchall():
                test_history.append({
                    'test_id': row[0],
                    'test_name': row[1],
                    'status': row[2],
                    'start_date': row[3],
                    'end_date': row[4],
                    'target_metric': row[5],
                    'success_threshold': row[6],
                    'total_users': row[7],
                    'variant_count': row[8]
                })
            
            conn.close()
            return test_history
            
        except Exception as e:
            logger.error(f"Error getting test history: {e}")
            return []
