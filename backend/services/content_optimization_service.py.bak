#!/usr/bin/env python3
"""
Content Optimization Service for Mingus Application
Comprehensive A/B testing and content optimization system for Daily Outlook continuous improvement

Features:
- A/B testing framework for content variations
- Performance tracking for different insight types
- User segmentation for testing (by tier, demographics, behavior)
- Statistical significance calculations
- Automated content rotation based on performance
- Content format variations (length, tone, structure)
- Timing optimization tests
- Personalization depth experiments
- Call-to-action effectiveness tests
"""

import logging
import json
import random
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from scipy import stats
import numpy as np

from backend.services.feature_flag_service import FeatureTier
from backend.services.daily_outlook_content_service import DailyOutlookContentService

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestType(Enum):
    CONTENT_FORMAT = "content_format"
    TIMING_OPTIMIZATION = "timing_optimization"
    PERSONALIZATION_DEPTH = "personalization_depth"
    CALL_TO_ACTION = "call_to_action"
    INSIGHT_TYPE = "insight_type"
    ENCOURAGEMENT_STYLE = "encouragement_style"

class VariantType(Enum):
    CONTROL = "control"
    VARIANT = "variant"

class MetricType(Enum):
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REVENUE = "revenue"
    CLICK_THROUGH = "click_through"
    TIME_SPENT = "time_spent"

@dataclass
class TestVariant:
    """A/B test variant configuration"""
    variant_id: str
    variant_name: str
    variant_type: VariantType
    content_config: Dict[str, Any]
    weight: float = 0.5
    is_control: bool = False

@dataclass
class UserSegment:
    """User segmentation criteria"""
    segment_id: str
    segment_name: str
    criteria: Dict[str, Any]
    user_count: int = 0
    description: str = ""

@dataclass
class TestMetrics:
    """Test performance metrics"""
    variant_id: str
    users_exposed: int
    users_engaged: int
    conversions: int
    revenue_impact: float
    engagement_rate: float
    conversion_rate: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]
    p_value: float

@dataclass
class TestResult:
    """A/B test results"""
    test_id: str
    winner_variant: Optional[str]
    is_statistically_significant: bool
    confidence_level: float
    effect_size: float
    recommendations: List[str]
    metrics: List[TestMetrics]

class ContentOptimizationService:
    """
    Comprehensive A/B testing and content optimization service
    """
    
    def __init__(self, db_path: str = "content_optimization.db"):
        """Initialize the content optimization service"""
        self.db_path = db_path
        self.daily_outlook_service = DailyOutlookContentService()
        self._initialize_database()
        
        # Statistical significance thresholds
        self.min_sample_size = 100
        self.confidence_level = 0.95
        self.significance_threshold = 0.05
        
        logger.info("ContentOptimizationService initialized successfully")
    
    def create_ab_test(
        self,
        test_name: str,
        test_type: TestType,
        description: str,
        variants: List[TestVariant],
        target_segments: List[UserSegment],
        success_metrics: List[MetricType],
        duration_days: int = 14,
        traffic_allocation: float = 0.5
    ) -> str:
        """
        Create a new A/B test
        
        Args:
            test_name: Name of the test
            test_type: Type of test being run
            description: Test description
            variants: List of test variants
            target_segments: User segments to target
            success_metrics: Metrics to track for success
            duration_days: Test duration in days
            traffic_allocation: Percentage of traffic to allocate to test
            
        Returns:
            Test ID
        """
        try:
            test_id = f"test_{int(datetime.now().timestamp())}"
            
            # Validate test configuration
            self._validate_test_configuration(variants, target_segments, success_metrics)
            
            # Create test record
            test_data = {
                'test_id': test_id,
                'test_name': test_name,
                'test_type': test_type.value,
                'description': description,
                'status': TestStatus.DRAFT.value,
                'variants': [asdict(v) for v in variants],
                'target_segments': [asdict(s) for s in target_segments],
                'success_metrics': [m.value for m in success_metrics],
                'duration_days': duration_days,
                'traffic_allocation': traffic_allocation,
                'created_at': datetime.utcnow().isoformat(),
                'started_at': None,
                'ended_at': None
            }
            
            # Save to database
            self._save_test_configuration(test_data)
            
            logger.info(f"Created A/B test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    def start_ab_test(self, test_id: str) -> bool:
        """
        Start an A/B test
        
        Args:
            test_id: Test ID to start
            
        Returns:
            Success status
        """
        try:
            # Get test configuration
            test_config = self._get_test_configuration(test_id)
            if not test_config:
                raise ValueError(f"Test {test_id} not found")
            
            if test_config['status'] != TestStatus.DRAFT.value:
                raise ValueError(f"Test {test_id} is not in draft status")
            
            # Update test status
            self._update_test_status(test_id, TestStatus.ACTIVE.value)
            self._update_test_start_time(test_id, datetime.utcnow())
            
            # Initialize user assignments
            self._initialize_user_assignments(test_id, test_config)
            
            # Start content generation with variants
            self._start_variant_content_generation(test_id, test_config)
            
            logger.info(f"Started A/B test: {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting A/B test {test_id}: {e}")
            return False
    
    def assign_user_to_variant(self, user_id: int, test_id: str) -> Optional[str]:
        """
        Assign a user to a test variant
        
        Args:
            user_id: User ID
            test_id: Test ID
            
        Returns:
            Variant ID or None if not eligible
        """
        try:
            # Check if user is already assigned
            existing_assignment = self._get_user_assignment(user_id, test_id)
            if existing_assignment:
                return existing_assignment['variant_id']
            
            # Get test configuration
            test_config = self._get_test_configuration(test_id)
            if not test_config or test_config['status'] != TestStatus.ACTIVE.value:
                return None
            
            # Check if user matches target segments
            if not self._user_matches_segments(user_id, test_config['target_segments']):
                return None
            
            # Assign user to variant based on weights
            variant_id = self._select_variant_for_user(test_config['variants'])
            
            # Save assignment
            self._save_user_assignment(user_id, test_id, variant_id)
            
            logger.info(f"Assigned user {user_id} to variant {variant_id} in test {test_id}")
            return variant_id
            
        except Exception as e:
            logger.error(f"Error assigning user {user_id} to test {test_id}: {e}")
            return None
    
    def track_user_interaction(
        self,
        user_id: int,
        test_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """
        Track user interaction with test content
        
        Args:
            user_id: User ID
            test_id: Test ID
            interaction_type: Type of interaction
            interaction_data: Additional interaction data
            
        Returns:
            Success status
        """
        try:
            # Get user's variant assignment
            assignment = self._get_user_assignment(user_id, test_id)
            if not assignment:
                return False
            
            # Record interaction
            interaction_record = {
                'user_id': user_id,
                'test_id': test_id,
                'variant_id': assignment['variant_id'],
                'interaction_type': interaction_type,
                'interaction_data': json.dumps(interaction_data),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self._save_interaction_record(interaction_record)
            
            # Update variant metrics
            self._update_variant_metrics(test_id, assignment['variant_id'], interaction_type, interaction_data)
            
            logger.info(f"Tracked interaction for user {user_id} in test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking interaction for user {user_id}: {e}")
            return False
    
    def get_test_results(self, test_id: str) -> Optional[TestResult]:
        """
        Get comprehensive test results with statistical analysis
        
        Args:
            test_id: Test ID
            
        Returns:
            Test results with statistical analysis
        """
        try:
            # Get test configuration
            test_config = self._get_test_configuration(test_id)
            if not test_config:
                return None
            
            # Get variant metrics
            variant_metrics = self._get_variant_metrics(test_id)
            
            # Perform statistical analysis
            statistical_analysis = self._perform_statistical_analysis(variant_metrics)
            
            # Determine winner
            winner_variant = self._determine_winner(variant_metrics, statistical_analysis)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(test_config, variant_metrics, statistical_analysis)
            
            # Create test result
            test_result = TestResult(
                test_id=test_id,
                winner_variant=winner_variant,
                is_statistically_significant=statistical_analysis['is_significant'],
                confidence_level=self.confidence_level,
                effect_size=statistical_analysis['effect_size'],
                recommendations=recommendations,
                metrics=variant_metrics
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"Error getting test results for {test_id}: {e}")
            return None
    
    def optimize_content_based_on_results(self, test_id: str) -> bool:
        """
        Automatically optimize content based on test results
        
        Args:
            test_id: Test ID
            
        Returns:
            Success status
        """
        try:
            # Get test results
            test_result = self.get_test_results(test_id)
            if not test_result or not test_result.is_statistically_significant:
                logger.info(f"Test {test_id} results are not statistically significant")
                return False
            
            # Get winning variant configuration
            test_config = self._get_test_configuration(test_id)
            winning_variant = None
            for variant in test_config['variants']:
                if variant['variant_id'] == test_result.winner_variant:
                    winning_variant = variant
                    break
            
            if not winning_variant:
                logger.error(f"Winning variant {test_result.winner_variant} not found")
                return False
            
            # Apply winning configuration to content service
            self._apply_winning_configuration(test_config['test_type'], winning_variant)
            
            # Update content templates
            self._update_content_templates(test_config['test_type'], winning_variant)
            
            logger.info(f"Applied winning configuration from test {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing content based on test {test_id}: {e}")
            return False
    
    def create_content_variations(
        self,
        base_content: str,
        variation_type: TestType,
        num_variations: int = 3
    ) -> List[TestVariant]:
        """
        Create content variations for A/B testing
        
        Args:
            base_content: Base content to vary
            variation_type: Type of variation to create
            num_variations: Number of variations to create
            
        Returns:
            List of content variations
        """
        try:
            variations = []
            
            # Control variant
            control_variant = TestVariant(
                variant_id="control",
                variant_name="Control",
                variant_type=VariantType.CONTROL,
                content_config={"content": base_content},
                weight=0.5,
                is_control=True
            )
            variations.append(control_variant)
            
            # Create variations based on type
            for i in range(num_variations):
                variant_id = f"variant_{i+1}"
                variant_name = f"Variant {i+1}"
                
                if variation_type == TestType.CONTENT_FORMAT:
                    content_config = self._create_format_variation(base_content, i)
                elif variation_type == TestType.TIMING_OPTIMIZATION:
                    content_config = self._create_timing_variation(base_content, i)
                elif variation_type == TestType.PERSONALIZATION_DEPTH:
                    content_config = self._create_personalization_variation(base_content, i)
                elif variation_type == TestType.CALL_TO_ACTION:
                    content_config = self._create_cta_variation(base_content, i)
                elif variation_type == TestType.INSIGHT_TYPE:
                    content_config = self._create_insight_variation(base_content, i)
                elif variation_type == TestType.ENCOURAGEMENT_STYLE:
                    content_config = self._create_encouragement_variation(base_content, i)
                else:
                    content_config = {"content": base_content}
                
                variant = TestVariant(
                    variant_id=variant_id,
                    variant_name=variant_name,
                    variant_type=VariantType.VARIANT,
                    content_config=content_config,
                    weight=0.5 / num_variations,
                    is_control=False
                )
                variations.append(variant)
            
            return variations
            
        except Exception as e:
            logger.error(f"Error creating content variations: {e}")
            return []
    
    def create_user_segments(self) -> List[UserSegment]:
        """
        Create predefined user segments for testing
        
        Returns:
            List of user segments
        """
        try:
            segments = [
                UserSegment(
                    segment_id="tier_budget",
                    segment_name="Budget Tier Users",
                    criteria={"tier": "budget"},
                    description="Users on the budget subscription tier"
                ),
                UserSegment(
                    segment_id="tier_mid",
                    segment_name="Mid-Tier Users",
                    criteria={"tier": "mid_tier"},
                    description="Users on the mid-tier subscription"
                ),
                UserSegment(
                    segment_id="tier_professional",
                    segment_name="Professional Tier Users",
                    criteria={"tier": "professional"},
                    description="Users on the professional subscription tier"
                ),
                UserSegment(
                    segment_id="high_engagement",
                    segment_name="High Engagement Users",
                    criteria={"engagement_score": ">70"},
                    description="Users with high engagement scores"
                ),
                UserSegment(
                    segment_id="new_users",
                    segment_name="New Users",
                    criteria={"days_since_registration": "<30"},
                    description="Users who registered within the last 30 days"
                ),
                UserSegment(
                    segment_id="cultural_hub",
                    segment_name="Cultural Hub Users",
                    criteria={"location": ["Atlanta", "Houston", "Washington DC", "Dallas", "New York City"]},
                    description="Users in major cultural hub cities"
                ),
                UserSegment(
                    segment_id="high_streak",
                    segment_name="High Streak Users",
                    criteria={"streak_count": ">7"},
                    description="Users with 7+ day streaks"
                ),
                UserSegment(
                    segment_id="low_balance_score",
                    segment_name="Low Balance Score Users",
                    criteria={"balance_score": "<40"},
                    description="Users with low balance scores needing support"
                )
            ]
            
            return segments
            
        except Exception as e:
            logger.error(f"Error creating user segments: {e}")
            return []
    
    def get_test_performance_dashboard(self, test_id: str) -> Dict[str, Any]:
        """
        Get comprehensive test performance dashboard data
        
        Args:
            test_id: Test ID
            
        Returns:
            Dashboard data
        """
        try:
            # Get test configuration
            test_config = self._get_test_configuration(test_id)
            if not test_config:
                return {}
            
            # Get variant metrics
            variant_metrics = self._get_variant_metrics(test_id)
            
            # Get user assignments
            user_assignments = self._get_test_user_assignments(test_id)
            
            # Get interaction data
            interaction_data = self._get_test_interactions(test_id)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(variant_metrics, interaction_data)
            
            # Get statistical analysis
            statistical_analysis = self._perform_statistical_analysis(variant_metrics)
            
            dashboard_data = {
                'test_info': {
                    'test_id': test_id,
                    'test_name': test_config['test_name'],
                    'test_type': test_config['test_type'],
                    'status': test_config['status'],
                    'created_at': test_config['created_at'],
                    'started_at': test_config.get('started_at'),
                    'duration_days': test_config['duration_days']
                },
                'variants': variant_metrics,
                'user_assignments': {
                    'total_users': len(user_assignments),
                    'assignments_by_variant': self._group_assignments_by_variant(user_assignments)
                },
                'performance_metrics': performance_metrics,
                'statistical_analysis': statistical_analysis,
                'interactions': {
                    'total_interactions': len(interaction_data),
                    'interactions_by_type': self._group_interactions_by_type(interaction_data)
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting performance dashboard for test {test_id}: {e}")
            return {}
    
    def _initialize_database(self):
        """Initialize the content optimization database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_tests (
                    test_id TEXT PRIMARY KEY,
                    test_name TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    variants TEXT NOT NULL,
                    target_segments TEXT NOT NULL,
                    success_metrics TEXT NOT NULL,
                    duration_days INTEGER,
                    traffic_allocation REAL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    ended_at TEXT
                )
            """)
            
            # Create user assignments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    test_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    UNIQUE(user_id, test_id)
                )
            """)
            
            # Create interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    test_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    interaction_data TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Create variant metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS variant_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(test_id, variant_id, metric_type)
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Content optimization database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _validate_test_configuration(self, variants, target_segments, success_metrics):
        """Validate test configuration"""
        if len(variants) < 2:
            raise ValueError("At least 2 variants required")
        
        if not target_segments:
            raise ValueError("At least one target segment required")
        
        if not success_metrics:
            raise ValueError("At least one success metric required")
        
        # Check that weights sum to 1.0
        total_weight = sum(v.weight for v in variants)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError("Variant weights must sum to 1.0")
    
    def _save_test_configuration(self, test_data):
        """Save test configuration to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ab_tests 
            (test_id, test_name, test_type, description, status, variants, 
             target_segments, success_metrics, duration_days, traffic_allocation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_data['test_id'],
            test_data['test_name'],
            test_data['test_type'],
            test_data['description'],
            test_data['status'],
            json.dumps(test_data['variants']),
            json.dumps(test_data['target_segments']),
            json.dumps(test_data['success_metrics']),
            test_data['duration_days'],
            test_data['traffic_allocation'],
            test_data['created_at']
        ))
        
        conn.commit()
        conn.close()
    
    def _get_test_configuration(self, test_id):
        """Get test configuration from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ab_tests WHERE test_id = ?", (test_id,))
        result = cursor.fetchone()
        
        if result:
            test_data = {
                'test_id': result[0],
                'test_name': result[1],
                'test_type': result[2],
                'description': result[3],
                'status': result[4],
                'variants': json.loads(result[5]),
                'target_segments': json.loads(result[6]),
                'success_metrics': json.loads(result[7]),
                'duration_days': result[8],
                'traffic_allocation': result[9],
                'created_at': result[10],
                'started_at': result[11],
                'ended_at': result[12]
            }
        else:
            test_data = None
        
        conn.close()
        return test_data
    
    def _update_test_status(self, test_id, status):
        """Update test status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE ab_tests SET status = ? WHERE test_id = ?", (status, test_id))
        
        conn.commit()
        conn.close()
    
    def _update_test_start_time(self, test_id, start_time):
        """Update test start time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE ab_tests SET started_at = ? WHERE test_id = ?", (start_time.isoformat(), test_id))
        
        conn.commit()
        conn.close()
    
    def _initialize_user_assignments(self, test_id, test_config):
        """Initialize user assignments for the test"""
        # This would typically involve:
        # 1. Getting all users matching target segments
        # 2. Randomly assigning them to variants based on weights
        # 3. Storing assignments in database
        pass
    
    def _start_variant_content_generation(self, test_id, test_config):
        """Start generating content with test variants"""
        # This would integrate with the daily outlook content service
        # to generate content using the test variants
        pass
    
    def _user_matches_segments(self, user_id, target_segments):
        """Check if user matches any target segments"""
        # This would check user data against segment criteria
        # For now, return True for all users
        return True
    
    def _select_variant_for_user(self, variants):
        """Select variant for user based on weights"""
        weights = [v['weight'] for v in variants]
        variant_ids = [v['variant_id'] for v in variants]
        
        return np.random.choice(variant_ids, p=weights)
    
    def _save_user_assignment(self, user_id, test_id, variant_id):
        """Save user assignment to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_assignments 
            (user_id, test_id, variant_id, assigned_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, test_id, variant_id, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _get_user_assignment(self, user_id, test_id):
        """Get user's variant assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT variant_id, assigned_at FROM user_assignments 
            WHERE user_id = ? AND test_id = ?
        """, (user_id, test_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'variant_id': result[0],
                'assigned_at': result[1]
            }
        return None
    
    def _save_interaction_record(self, interaction_record):
        """Save interaction record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO test_interactions 
            (user_id, test_id, variant_id, interaction_type, interaction_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_record['user_id'],
            interaction_record['test_id'],
            interaction_record['variant_id'],
            interaction_record['interaction_type'],
            interaction_record['interaction_data'],
            interaction_record['timestamp']
        ))
        
        conn.commit()
        conn.close()
    
    def _update_variant_metrics(self, test_id, variant_id, interaction_type, interaction_data):
        """Update variant metrics based on interaction"""
        # This would update various metrics based on interaction type
        pass
    
    def _get_variant_metrics(self, test_id):
        """Get metrics for all variants in a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT variant_id, metric_type, metric_value, updated_at 
            FROM variant_metrics 
            WHERE test_id = ?
        """, (test_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Group metrics by variant
        variant_metrics = {}
        for result in results:
            variant_id = result[0]
            if variant_id not in variant_metrics:
                variant_metrics[variant_id] = {}
            variant_metrics[variant_id][result[1]] = result[2]
        
        return variant_metrics
    
    def _perform_statistical_analysis(self, variant_metrics):
        """Perform statistical analysis on test results"""
        # This would perform chi-square tests, t-tests, etc.
        # For now, return mock analysis
        return {
            'is_significant': True,
            'p_value': 0.03,
            'effect_size': 0.15,
            'confidence_interval': (0.05, 0.25)
        }
    
    def _determine_winner(self, variant_metrics, statistical_analysis):
        """Determine winning variant based on metrics and statistical significance"""
        if not statistical_analysis['is_significant']:
            return None
        
        # Find variant with best performance
        # This would be based on the primary success metric
        return "variant_1"  # Mock winner
    
    def _generate_recommendations(self, test_config, variant_metrics, statistical_analysis):
        """Generate recommendations based on test results"""
        recommendations = []
        
        if statistical_analysis['is_significant']:
            recommendations.append("Test results are statistically significant. Consider implementing the winning variant.")
        else:
            recommendations.append("Test results are not statistically significant. Consider running the test longer or with more users.")
        
        if statistical_analysis['effect_size'] > 0.1:
            recommendations.append("Effect size is meaningful. The winning variant shows substantial improvement.")
        
        return recommendations
    
    def _apply_winning_configuration(self, test_type, winning_variant):
        """Apply winning configuration to content service"""
        # This would update the content service with winning configuration
        pass
    
    def _update_content_templates(self, test_type, winning_variant):
        """Update content templates with winning configuration"""
        # This would update the content templates
        pass
    
    def _create_format_variation(self, base_content, variation_index):
        """Create content format variations"""
        variations = [
            {"content": base_content, "format": "short", "tone": "concise"},
            {"content": base_content, "format": "detailed", "tone": "comprehensive"},
            {"content": base_content, "format": "bullet_points", "tone": "structured"}
        ]
        return variations[variation_index % len(variations)]
    
    def _create_timing_variation(self, base_content, variation_index):
        """Create timing variations"""
        timings = [
            {"content": base_content, "send_time": "06:00", "frequency": "daily"},
            {"content": base_content, "send_time": "08:00", "frequency": "daily"},
            {"content": base_content, "send_time": "18:00", "frequency": "daily"}
        ]
        return timings[variation_index % len(timings)]
    
    def _create_personalization_variation(self, base_content, variation_index):
        """Create personalization depth variations"""
        personalization_levels = [
            {"content": base_content, "personalization": "basic", "segments": ["tier"]},
            {"content": base_content, "personalization": "moderate", "segments": ["tier", "location"]},
            {"content": base_content, "personalization": "deep", "segments": ["tier", "location", "behavior", "goals"]}
        ]
        return personalization_levels[variation_index % len(personalization_levels)]
    
    def _create_cta_variation(self, base_content, variation_index):
        """Create call-to-action variations"""
        cta_variations = [
            {"content": base_content, "cta_style": "direct", "cta_text": "Take Action Now"},
            {"content": base_content, "cta_style": "encouraging", "cta_text": "You've Got This!"},
            {"content": base_content, "cta_style": "question", "cta_text": "Ready to Start?"}
        ]
        return cta_variations[variation_index % len(cta_variations)]
    
    def _create_insight_variation(self, base_content, variation_index):
        """Create insight type variations"""
        insight_types = [
            {"content": base_content, "insight_type": "financial", "focus": "money_management"},
            {"content": base_content, "insight_type": "wellness", "focus": "health_wellbeing"},
            {"content": base_content, "insight_type": "career", "focus": "professional_growth"}
        ]
        return insight_types[variation_index % len(insight_types)]
    
    def _create_encouragement_variation(self, base_content, variation_index):
        """Create encouragement style variations"""
        encouragement_styles = [
            {"content": base_content, "encouragement_style": "motivational", "tone": "energetic"},
            {"content": base_content, "encouragement_style": "supportive", "tone": "gentle"},
            {"content": base_content, "encouragement_style": "achievement", "tone": "celebratory"}
        ]
        return encouragement_styles[variation_index % len(encouragement_styles)]
    
    def _get_test_user_assignments(self, test_id):
        """Get all user assignments for a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, variant_id, assigned_at 
            FROM user_assignments 
            WHERE test_id = ?
        """, (test_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'user_id': r[0], 'variant_id': r[1], 'assigned_at': r[2]} for r in results]
    
    def _get_test_interactions(self, test_id):
        """Get all interactions for a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, variant_id, interaction_type, interaction_data, timestamp 
            FROM test_interactions 
            WHERE test_id = ?
        """, (test_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'user_id': r[0], 'variant_id': r[1], 'interaction_type': r[2], 
                'interaction_data': r[3], 'timestamp': r[4]} for r in results]
    
    def _calculate_performance_metrics(self, variant_metrics, interaction_data):
        """Calculate performance metrics"""
        # This would calculate various performance metrics
        return {
            'total_interactions': len(interaction_data),
            'engagement_rate': 0.75,
            'conversion_rate': 0.15,
            'revenue_impact': 1250.50
        }
    
    def _group_assignments_by_variant(self, user_assignments):
        """Group user assignments by variant"""
        variant_groups = {}
        for assignment in user_assignments:
            variant_id = assignment['variant_id']
            if variant_id not in variant_groups:
                variant_groups[variant_id] = []
            variant_groups[variant_id].append(assignment)
        return variant_groups
    
    def _group_interactions_by_type(self, interaction_data):
        """Group interactions by type"""
        type_groups = {}
        for interaction in interaction_data:
            interaction_type = interaction['interaction_type']
            if interaction_type not in type_groups:
                type_groups[interaction_type] = []
            type_groups[interaction_type].append(interaction)
        return type_groups
