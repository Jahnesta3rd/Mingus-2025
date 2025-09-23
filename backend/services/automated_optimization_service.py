#!/usr/bin/env python3
"""
Automated Optimization Service for Mingus Application
Automated content optimization based on A/B test results and performance thresholds

Features:
- Performance threshold monitoring
- Automatic winner selection
- Content template updates
- User experience improvement recommendations
- Real-time optimization triggers
- Statistical significance monitoring
- Revenue impact analysis
- Retention optimization
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import sessionmaker

from backend.models.database import db
from backend.models.content_optimization_models import (
    ABTest, UserAssignment, TestInteraction, VariantMetric, 
    TestResult, PerformanceThreshold, OptimizationRule, 
    ContentPerformance, AnalyticsEvent, ContentTemplate
)
from backend.services.content_optimization_service import ContentOptimizationService
from backend.services.daily_outlook_content_service import DailyOutlookContentService
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class OptimizationTrigger(Enum):
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    TIME_BASED = "time_based"
    REVENUE_IMPACT = "revenue_impact"
    RETENTION_DROP = "retention_drop"

class OptimizationAction(Enum):
    APPLY_WINNER = "apply_winner"
    PAUSE_TEST = "pause_test"
    END_TEST = "end_test"
    ALERT_ADMIN = "alert_admin"
    ADJUST_TRAFFIC = "adjust_traffic"
    CREATE_NEW_TEST = "create_new_test"

@dataclass
class OptimizationEvent:
    """Optimization event triggered by monitoring"""
    event_id: str
    trigger_type: OptimizationTrigger
    test_id: str
    variant_id: Optional[str]
    metric_value: float
    threshold_value: float
    action_required: OptimizationAction
    confidence_level: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation based on analysis"""
    recommendation_id: str
    test_id: str
    recommendation_type: str
    priority: int
    description: str
    expected_impact: float
    implementation_steps: List[str]
    risk_level: str
    created_at: datetime

class AutomatedOptimizationService:
    """
    Automated content optimization service with real-time monitoring
    """
    
    def __init__(self, db_path: str = "content_optimization.db"):
        """Initialize the automated optimization service"""
        self.db_path = db_path
        self.content_optimization_service = ContentOptimizationService(db_path)
        self.daily_outlook_service = DailyOutlookContentService()
        self.notification_service = NotificationService()
        
        # Monitoring configuration
        self.monitoring_interval = 300  # 5 minutes
        self.performance_check_interval = 3600  # 1 hour
        self.statistical_check_interval = 1800  # 30 minutes
        
        # Thresholds for automated actions
        self.min_sample_size = 100
        self.confidence_level = 0.95
        self.significance_threshold = 0.05
        self.effect_size_threshold = 0.1
        
        logger.info("AutomatedOptimizationService initialized successfully")
    
    async def start_monitoring(self):
        """Start automated monitoring and optimization"""
        try:
            logger.info("Starting automated optimization monitoring")
            
            # Start monitoring tasks
            tasks = [
                self._monitor_performance_thresholds(),
                self._monitor_statistical_significance(),
                self._monitor_revenue_impact(),
                self._monitor_retention_metrics(),
                self._process_optimization_events()
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error in automated monitoring: {e}")
    
    async def _monitor_performance_thresholds(self):
        """Monitor performance thresholds for active tests"""
        try:
            while True:
                # Get active tests
                active_tests = self._get_active_tests()
                
                for test in active_tests:
                    # Get performance thresholds for this test type
                    thresholds = self._get_performance_thresholds(test.test_type)
                    
                    for threshold in thresholds:
                        # Check if threshold is exceeded
                        current_value = self._get_current_metric_value(
                            test.test_id, threshold.metric_type
                        )
                        
                        if self._is_threshold_exceeded(
                            current_value, threshold.threshold_value, 
                            threshold.comparison_operator
                        ):
                            # Create optimization event
                            event = OptimizationEvent(
                                event_id=f"threshold_{int(datetime.now().timestamp())}",
                                trigger_type=OptimizationTrigger.PERFORMANCE_THRESHOLD,
                                test_id=test.test_id,
                                variant_id=None,
                                metric_value=current_value,
                                threshold_value=threshold.threshold_value,
                                action_required=OptimizationAction(threshold.action_type),
                                confidence_level=self.confidence_level,
                                timestamp=datetime.utcnow(),
                                metadata={
                                    'threshold_name': threshold.threshold_name,
                                    'metric_type': threshold.metric_type,
                                    'comparison_operator': threshold.comparison_operator
                                }
                            )
                            
                            await self._process_optimization_event(event)
                
                # Wait before next check
                await asyncio.sleep(self.performance_check_interval)
                
        except Exception as e:
            logger.error(f"Error monitoring performance thresholds: {e}")
    
    async def _monitor_statistical_significance(self):
        """Monitor statistical significance of active tests"""
        try:
            while True:
                # Get active tests
                active_tests = self._get_active_tests()
                
                for test in active_tests:
                    # Check if test has been running long enough
                    if self._test_has_minimum_duration(test):
                        # Get test results
                        test_result = self.content_optimization_service.get_test_results(test.test_id)
                        
                        if test_result and test_result.is_statistically_significant:
                            # Create optimization event
                            event = OptimizationEvent(
                                event_id=f"significance_{int(datetime.now().timestamp())}",
                                trigger_type=OptimizationTrigger.STATISTICAL_SIGNIFICANCE,
                                test_id=test.test_id,
                                variant_id=test_result.winner_variant,
                                metric_value=test_result.effect_size,
                                threshold_value=self.effect_size_threshold,
                                action_required=OptimizationAction.APPLY_WINNER,
                                confidence_level=test_result.confidence_level,
                                timestamp=datetime.utcnow(),
                                metadata={
                                    'p_value': test_result.p_value,
                                    'effect_size': test_result.effect_size,
                                    'winner_variant': test_result.winner_variant
                                }
                            )
                            
                            await self._process_optimization_event(event)
                
                # Wait before next check
                await asyncio.sleep(self.statistical_check_interval)
                
        except Exception as e:
            logger.error(f"Error monitoring statistical significance: {e}")
    
    async def _monitor_revenue_impact(self):
        """Monitor revenue impact of content variations"""
        try:
            while True:
                # Get active tests with revenue metrics
                revenue_tests = self._get_tests_with_revenue_metrics()
                
                for test in revenue_tests:
                    # Calculate revenue impact
                    revenue_impact = self._calculate_revenue_impact(test.test_id)
                    
                    # Check if revenue impact exceeds threshold
                    if revenue_impact > 1000:  # $1000 threshold
                        # Create optimization event
                        event = OptimizationEvent(
                            event_id=f"revenue_{int(datetime.now().timestamp())}",
                            trigger_type=OptimizationTrigger.REVENUE_IMPACT,
                            test_id=test.test_id,
                            variant_id=None,
                            metric_value=revenue_impact,
                            threshold_value=1000,
                            action_required=OptimizationAction.ALERT_ADMIN,
                            confidence_level=self.confidence_level,
                            timestamp=datetime.utcnow(),
                            metadata={
                                'revenue_impact': revenue_impact,
                                'currency': 'USD'
                            }
                        )
                        
                        await self._process_optimization_event(event)
                
                # Wait before next check
                await asyncio.sleep(self.performance_check_interval)
                
        except Exception as e:
            logger.error(f"Error monitoring revenue impact: {e}")
    
    async def _monitor_retention_metrics(self):
        """Monitor user retention metrics for content optimization"""
        try:
            while True:
                # Get active tests
                active_tests = self._get_active_tests()
                
                for test in active_tests:
                    # Calculate retention metrics
                    retention_metrics = self._calculate_retention_metrics(test.test_id)
                    
                    # Check for retention drops
                    if retention_metrics['retention_drop'] > 0.05:  # 5% drop threshold
                        # Create optimization event
                        event = OptimizationEvent(
                            event_id=f"retention_{int(datetime.now().timestamp())}",
                            trigger_type=OptimizationTrigger.RETENTION_DROP,
                            test_id=test.test_id,
                            variant_id=None,
                            metric_value=retention_metrics['retention_drop'],
                            threshold_value=0.05,
                            action_required=OptimizationAction.PAUSE_TEST,
                            confidence_level=self.confidence_level,
                            timestamp=datetime.utcnow(),
                            metadata={
                                'retention_drop': retention_metrics['retention_drop'],
                                'current_retention': retention_metrics['current_retention'],
                                'baseline_retention': retention_metrics['baseline_retention']
                            }
                        )
                        
                        await self._process_optimization_event(event)
                
                # Wait before next check
                await asyncio.sleep(self.performance_check_interval)
                
        except Exception as e:
            logger.error(f"Error monitoring retention metrics: {e}")
    
    async def _process_optimization_events(self):
        """Process optimization events and execute actions"""
        try:
            while True:
                # Get pending optimization events
                events = self._get_pending_optimization_events()
                
                for event in events:
                    await self._execute_optimization_action(event)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Error processing optimization events: {e}")
    
    async def _process_optimization_event(self, event: OptimizationEvent):
        """Process a single optimization event"""
        try:
            # Save event to database
            self._save_optimization_event(event)
            
            # Log the event
            logger.info(f"Optimization event triggered: {event.trigger_type.value} for test {event.test_id}")
            
            # Execute immediate actions if needed
            if event.action_required in [OptimizationAction.PAUSE_TEST, OptimizationAction.END_TEST]:
                await self._execute_optimization_action(event)
            
        except Exception as e:
            logger.error(f"Error processing optimization event: {e}")
    
    async def _execute_optimization_action(self, event: OptimizationEvent):
        """Execute optimization action based on event"""
        try:
            if event.action_required == OptimizationAction.APPLY_WINNER:
                await self._apply_winning_variant(event)
            elif event.action_required == OptimizationAction.PAUSE_TEST:
                await self._pause_test(event)
            elif event.action_required == OptimizationAction.END_TEST:
                await self._end_test(event)
            elif event.action_required == OptimizationAction.ALERT_ADMIN:
                await self._alert_admin(event)
            elif event.action_required == OptimizationAction.ADJUST_TRAFFIC:
                await self._adjust_traffic_allocation(event)
            elif event.action_required == OptimizationAction.CREATE_NEW_TEST:
                await self._create_follow_up_test(event)
            
            # Mark event as processed
            self._mark_event_processed(event.event_id)
            
        except Exception as e:
            logger.error(f"Error executing optimization action: {e}")
    
    async def _apply_winning_variant(self, event: OptimizationEvent):
        """Apply winning variant configuration"""
        try:
            # Get test results
            test_result = self.content_optimization_service.get_test_results(event.test_id)
            
            if test_result and test_result.winner_variant:
                # Apply winning configuration
                success = self.content_optimization_service.optimize_content_based_on_results(event.test_id)
                
                if success:
                    logger.info(f"Applied winning variant {test_result.winner_variant} for test {event.test_id}")
                    
                    # Create optimization recommendation
                    recommendation = OptimizationRecommendation(
                        recommendation_id=f"apply_winner_{int(datetime.now().timestamp())}",
                        test_id=event.test_id,
                        recommendation_type="apply_winner",
                        priority=1,
                        description=f"Apply winning variant {test_result.winner_variant} based on statistical significance",
                        expected_impact=test_result.effect_size,
                        implementation_steps=[
                            "Update content templates with winning configuration",
                            "Deploy changes to production",
                            "Monitor performance metrics",
                            "Document optimization results"
                        ],
                        risk_level="low",
                        created_at=datetime.utcnow()
                    )
                    
                    self._save_optimization_recommendation(recommendation)
                else:
                    logger.error(f"Failed to apply winning variant for test {event.test_id}")
            
        except Exception as e:
            logger.error(f"Error applying winning variant: {e}")
    
    async def _pause_test(self, event: OptimizationEvent):
        """Pause a test due to performance issues"""
        try:
            # Update test status
            test = ABTest.query.filter_by(test_id=event.test_id).first()
            if test:
                test.status = 'paused'
                db.session.commit()
                
                logger.info(f"Paused test {event.test_id} due to {event.trigger_type.value}")
                
                # Create recommendation
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"pause_test_{int(datetime.now().timestamp())}",
                    test_id=event.test_id,
                    recommendation_type="pause_test",
                    priority=2,
                    description=f"Test paused due to {event.trigger_type.value}",
                    expected_impact=0.0,
                    implementation_steps=[
                        "Review test configuration",
                        "Analyze performance issues",
                        "Consider test modifications",
                        "Resume when issues resolved"
                    ],
                    risk_level="medium",
                    created_at=datetime.utcnow()
                )
                
                self._save_optimization_recommendation(recommendation)
            
        except Exception as e:
            logger.error(f"Error pausing test: {e}")
    
    async def _end_test(self, event: OptimizationEvent):
        """End a test due to significant issues"""
        try:
            # Update test status
            test = ABTest.query.filter_by(test_id=event.test_id).first()
            if test:
                test.status = 'completed'
                test.ended_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Ended test {event.test_id} due to {event.trigger_type.value}")
                
                # Create recommendation
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"end_test_{int(datetime.now().timestamp())}",
                    test_id=event.test_id,
                    recommendation_type="end_test",
                    priority=3,
                    description=f"Test ended due to {event.trigger_type.value}",
                    expected_impact=0.0,
                    implementation_steps=[
                        "Analyze test results",
                        "Document lessons learned",
                        "Consider alternative approaches",
                        "Plan future tests"
                    ],
                    risk_level="high",
                    created_at=datetime.utcnow()
                )
                
                self._save_optimization_recommendation(recommendation)
            
        except Exception as e:
            logger.error(f"Error ending test: {e}")
    
    async def _alert_admin(self, event: OptimizationEvent):
        """Send alert to admin about optimization event"""
        try:
            # Create alert message
            alert_message = f"""
            Optimization Alert
            
            Test: {event.test_id}
            Trigger: {event.trigger_type.value}
            Metric Value: {event.metric_value}
            Threshold: {event.threshold_value}
            Action Required: {event.action_required.value}
            Timestamp: {event.timestamp}
            """
            
            # Send notification (this would integrate with notification service)
            logger.warning(f"Admin alert: {alert_message}")
            
            # Create recommendation
            recommendation = OptimizationRecommendation(
                recommendation_id=f"admin_alert_{int(datetime.now().timestamp())}",
                test_id=event.test_id,
                recommendation_type="admin_alert",
                priority=2,
                description=f"Admin alert triggered by {event.trigger_type.value}",
                expected_impact=0.0,
                implementation_steps=[
                    "Review alert details",
                    "Assess test performance",
                    "Take appropriate action",
                    "Update monitoring thresholds if needed"
                ],
                risk_level="medium",
                created_at=datetime.utcnow()
            )
            
            self._save_optimization_recommendation(recommendation)
            
        except Exception as e:
            logger.error(f"Error sending admin alert: {e}")
    
    async def _adjust_traffic_allocation(self, event: OptimizationEvent):
        """Adjust traffic allocation between variants"""
        try:
            # This would adjust the traffic allocation based on performance
            # For now, we'll just log the action
            logger.info(f"Adjusting traffic allocation for test {event.test_id}")
            
        except Exception as e:
            logger.error(f"Error adjusting traffic allocation: {e}")
    
    async def _create_follow_up_test(self, event: OptimizationEvent):
        """Create a follow-up test based on results"""
        try:
            # This would create a new test based on the results of the current test
            logger.info(f"Creating follow-up test for {event.test_id}")
            
        except Exception as e:
            logger.error(f"Error creating follow-up test: {e}")
    
    def get_optimization_recommendations(self, test_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM optimization_recommendations"
            params = []
            
            if test_id:
                query += " WHERE test_id = ?"
                params.append(test_id)
            
            query += " ORDER BY priority ASC, created_at DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            recommendations = []
            for result in results:
                recommendations.append({
                    'recommendation_id': result[0],
                    'test_id': result[1],
                    'recommendation_type': result[2],
                    'priority': result[3],
                    'description': result[4],
                    'expected_impact': result[5],
                    'implementation_steps': json.loads(result[6]),
                    'risk_level': result[7],
                    'created_at': result[8]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return []
    
    def get_optimization_events(self, test_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimization events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM optimization_events"
            params = []
            
            if test_id:
                query += " WHERE test_id = ?"
                params.append(test_id)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            events = []
            for result in results:
                events.append({
                    'event_id': result[0],
                    'trigger_type': result[1],
                    'test_id': result[2],
                    'variant_id': result[3],
                    'metric_value': result[4],
                    'threshold_value': result[5],
                    'action_required': result[6],
                    'confidence_level': result[7],
                    'timestamp': result[8],
                    'metadata': json.loads(result[9]) if result[9] else {},
                    'processed': result[10]
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting optimization events: {e}")
            return []
    
    def _get_active_tests(self) -> List[ABTest]:
        """Get active A/B tests"""
        return ABTest.query.filter_by(status='active').all()
    
    def _get_performance_thresholds(self, test_type: str) -> List[PerformanceThreshold]:
        """Get performance thresholds for test type"""
        return PerformanceThreshold.query.filter_by(is_active=True).all()
    
    def _get_current_metric_value(self, test_id: str, metric_type: str) -> float:
        """Get current metric value for a test"""
        # This would calculate the current metric value
        # For now, return a mock value
        return 0.75
    
    def _is_threshold_exceeded(self, current_value: float, threshold_value: float, operator: str) -> bool:
        """Check if threshold is exceeded"""
        if operator == '>':
            return current_value > threshold_value
        elif operator == '<':
            return current_value < threshold_value
        elif operator == '>=':
            return current_value >= threshold_value
        elif operator == '<=':
            return current_value <= threshold_value
        elif operator == '==':
            return current_value == threshold_value
        else:
            return False
    
    def _test_has_minimum_duration(self, test: ABTest) -> bool:
        """Check if test has been running for minimum duration"""
        if not test.started_at:
            return False
        
        duration = datetime.utcnow() - test.started_at
        return duration.days >= 1  # Minimum 1 day
    
    def _get_tests_with_revenue_metrics(self) -> List[ABTest]:
        """Get tests that track revenue metrics"""
        return ABTest.query.filter(
            ABTest.success_metrics.contains('revenue')
        ).filter_by(status='active').all()
    
    def _calculate_revenue_impact(self, test_id: str) -> float:
        """Calculate revenue impact for a test"""
        # This would calculate actual revenue impact
        # For now, return a mock value
        return 1500.0
    
    def _calculate_retention_metrics(self, test_id: str) -> Dict[str, float]:
        """Calculate retention metrics for a test"""
        # This would calculate actual retention metrics
        # For now, return mock values
        return {
            'current_retention': 0.85,
            'baseline_retention': 0.90,
            'retention_drop': 0.05
        }
    
    def _get_pending_optimization_events(self) -> List[OptimizationEvent]:
        """Get pending optimization events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM optimization_events 
            WHERE processed = 0 
            ORDER BY timestamp ASC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        events = []
        for result in results:
            events.append(OptimizationEvent(
                event_id=result[0],
                trigger_type=OptimizationTrigger(result[1]),
                test_id=result[2],
                variant_id=result[3],
                metric_value=result[4],
                threshold_value=result[5],
                action_required=OptimizationAction(result[6]),
                confidence_level=result[7],
                timestamp=datetime.fromisoformat(result[8]),
                metadata=json.loads(result[9]) if result[9] else {}
            ))
        
        return events
    
    def _save_optimization_event(self, event: OptimizationEvent):
        """Save optimization event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO optimization_events 
            (event_id, trigger_type, test_id, variant_id, metric_value, 
             threshold_value, action_required, confidence_level, timestamp, 
             metadata, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.trigger_type.value,
            event.test_id,
            event.variant_id,
            event.metric_value,
            event.threshold_value,
            event.action_required.value,
            event.confidence_level,
            event.timestamp.isoformat(),
            json.dumps(event.metadata),
            False
        ))
        
        conn.commit()
        conn.close()
    
    def _save_optimization_recommendation(self, recommendation: OptimizationRecommendation):
        """Save optimization recommendation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO optimization_recommendations 
            (recommendation_id, test_id, recommendation_type, priority, 
             description, expected_impact, implementation_steps, risk_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recommendation.recommendation_id,
            recommendation.test_id,
            recommendation.recommendation_type,
            recommendation.priority,
            recommendation.description,
            recommendation.expected_impact,
            json.dumps(recommendation.implementation_steps),
            recommendation.risk_level,
            recommendation.created_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _mark_event_processed(self, event_id: str):
        """Mark optimization event as processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE optimization_events 
            SET processed = 1 
            WHERE event_id = ?
        """, (event_id,))
        
        conn.commit()
        conn.close()
    
    def _initialize_optimization_tables(self):
        """Initialize optimization tables in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create optimization events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_events (
                event_id TEXT PRIMARY KEY,
                trigger_type TEXT NOT NULL,
                test_id TEXT NOT NULL,
                variant_id TEXT,
                metric_value REAL NOT NULL,
                threshold_value REAL NOT NULL,
                action_required TEXT NOT NULL,
                confidence_level REAL NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                processed INTEGER DEFAULT 0
            )
        """)
        
        # Create optimization recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_recommendations (
                recommendation_id TEXT PRIMARY KEY,
                test_id TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                description TEXT NOT NULL,
                expected_impact REAL NOT NULL,
                implementation_steps TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Optimization tables initialized")
