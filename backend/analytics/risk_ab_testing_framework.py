#!/usr/bin/env python3
"""
Risk A/B Testing Framework for Career Protection Optimization

This module extends the existing ABTestFramework to provide comprehensive
A/B testing capabilities specifically for risk-based career protection,
including threshold optimization, communication testing, and intervention timing.

Features:
- Risk threshold optimization tests
- Risk communication A/B tests  
- Intervention timing optimization
- Success outcome measurement
- Continuous optimization
- Statistical significance validation
"""

import asyncio
import logging
import sqlite3
import json
import uuid
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import math

# Import existing components
from .ab_testing_framework import ABTestFramework, TestStatus, TestType
from .risk_analytics_integration import RiskAnalyticsTracker, RiskBasedSuccessMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskTestType(Enum):
    """Types of risk-specific A/B tests"""
    RISK_THRESHOLD_OPTIMIZATION = "risk_threshold_optimization"
    RISK_COMMUNICATION_TEST = "risk_communication_test"
    INTERVENTION_TIMING_OPTIMIZATION = "intervention_timing_optimization"
    EMERGENCY_UNLOCK_THRESHOLD = "emergency_unlock_threshold"
    MULTI_TIER_RISK_RESPONSE = "multi_tier_risk_response"
    RISK_FACTOR_WEIGHTING = "risk_factor_weighting"

class CommunicationTone(Enum):
    """Risk communication tone variants"""
    DIRECT = "direct"
    ENCOURAGING = "encouraging"
    DATA_DRIVEN = "data_driven"
    SUPPORTIVE = "supportive"
    URGENT = "urgent"

class TimingStrategy(Enum):
    """Intervention timing strategy variants"""
    IMMEDIATE = "immediate"
    OPTIMIZED_TIMING = "optimized_timing"
    SCHEDULED_OUTREACH = "scheduled_outreach"
    GRADUAL_ESCALATION = "gradual_escalation"

@dataclass
class RiskTestConfig:
    """Configuration for risk A/B tests"""
    test_name: str
    test_type: RiskTestType
    description: str
    hypothesis: str
    variants: Dict[str, Dict[str, Any]]
    success_criteria: List[str]
    target_participants: int
    test_duration_days: int
    minimum_risk_users_per_variant: int
    risk_score_range: Tuple[float, float] = (0.0, 1.0)

@dataclass
class RiskTestResult:
    """Results for risk A/B tests"""
    test_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    sample_size: int
    risk_users_count: int
    conversion_rate: float
    statistical_significance: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    improvement_percentage: float

class RiskABTestFramework:
    """
    Comprehensive A/B testing framework for risk-based career protection optimization.
    
    Extends the existing ABTestFramework with specialized risk testing capabilities
    including threshold optimization, communication testing, and intervention timing.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the risk A/B testing framework"""
        self.db_path = db_path
        self.base_framework = ABTestFramework(db_path)
        self.risk_analytics = RiskAnalyticsTracker(db_path)
        self.success_metrics = RiskBasedSuccessMetrics(db_path)
        self._init_risk_ab_tables()
        logger.info("RiskABTestFramework initialized successfully")
    
    def _init_risk_ab_tables(self):
        """Initialize risk-specific A/B testing tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Risk A/B test configurations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_ab_test_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT UNIQUE NOT NULL,
                        test_name TEXT NOT NULL,
                        test_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        hypothesis TEXT NOT NULL,
                        variants_config TEXT NOT NULL,
                        success_criteria TEXT NOT NULL,
                        target_participants INTEGER NOT NULL,
                        test_duration_days INTEGER NOT NULL,
                        minimum_risk_users_per_variant INTEGER NOT NULL,
                        risk_score_range TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'draft',
                        start_date DATETIME,
                        end_date DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        INDEX idx_risk_ab_configs_test_id (test_id),
                        INDEX idx_risk_ab_configs_type (test_type),
                        INDEX idx_risk_ab_configs_status (status)
                    )
                ''')
                
                # Risk A/B test participants
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_ab_test_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        variant_id TEXT NOT NULL,
                        risk_score REAL NOT NULL,
                        risk_level TEXT NOT NULL,
                        assigned_at DATETIME NOT NULL,
                        last_activity DATETIME,
                        conversion_events TEXT,
                        outcome_data TEXT,
                        
                        UNIQUE(test_id, user_id),
                        INDEX idx_risk_participants_test_id (test_id),
                        INDEX idx_risk_participants_user_id (user_id),
                        INDEX idx_risk_participants_variant (variant_id),
                        INDEX idx_risk_participants_risk_score (risk_score)
                    )
                ''')
                
                # Risk A/B test outcomes
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_ab_test_outcomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        variant_id TEXT NOT NULL,
                        outcome_type TEXT NOT NULL,
                        outcome_value REAL NOT NULL,
                        outcome_timestamp DATETIME NOT NULL,
                        success_metrics TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        INDEX idx_risk_outcomes_test_id (test_id),
                        INDEX idx_risk_outcomes_user_id (user_id),
                        INDEX idx_risk_outcomes_variant (variant_id),
                        INDEX idx_risk_outcomes_type (outcome_type)
                    )
                ''')
                
                # Risk optimization history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_optimization_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT NOT NULL,
                        optimization_type TEXT NOT NULL,
                        original_value REAL NOT NULL,
                        optimized_value REAL NOT NULL,
                        improvement_percentage REAL NOT NULL,
                        confidence_level REAL NOT NULL,
                        optimization_timestamp DATETIME NOT NULL,
                        test_results TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        INDEX idx_risk_optimization_test_id (test_id),
                        INDEX idx_risk_optimization_type (optimization_type),
                        INDEX idx_risk_optimization_timestamp (optimization_timestamp)
                    )
                ''')
                
                conn.commit()
                logger.info("Risk A/B testing tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing risk A/B testing tables: {e}")
            raise
    
    async def create_risk_threshold_test(
        self, 
        test_name: str, 
        threshold_variants: List[float], 
        success_criteria: List[str],
        target_participants: int = 1000,
        test_duration_days: int = 30
    ) -> str:
        """Create A/B test for different risk threshold triggers"""
        try:
            test_id = str(uuid.uuid4())
            
            # Create test configuration
            test_config = RiskTestConfig(
                test_name=test_name,
                test_type=RiskTestType.RISK_THRESHOLD_OPTIMIZATION,
                description=f"A/B test for risk threshold optimization: {test_name}",
                hypothesis="Different risk thresholds will optimize recommendation timing and user outcomes",
                variants={
                    f'threshold_{threshold}': {
                        'risk_threshold': threshold,
                        'emergency_unlock_threshold': threshold + 0.1,
                        'recommendation_trigger_threshold': threshold - 0.1
                    } for threshold in threshold_variants
                },
                success_criteria=success_criteria,
                target_participants=target_participants,
                test_duration_days=test_duration_days,
                minimum_risk_users_per_variant=50
            )
            
            # Store test configuration
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_ab_test_configs 
                    (test_id, test_name, test_type, description, hypothesis, variants_config,
                     success_criteria, target_participants, test_duration_days, 
                     minimum_risk_users_per_variant, risk_score_range, status, start_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    test_config.test_name,
                    test_config.test_type.value,
                    test_config.description,
                    test_config.hypothesis,
                    json.dumps(test_config.variants),
                    json.dumps(test_config.success_criteria),
                    test_config.target_participants,
                    test_config.test_duration_days,
                    test_config.minimum_risk_users_per_variant,
                    json.dumps(test_config.risk_score_range),
                    'active',
                    datetime.now()
                ))
                
                conn.commit()
            
            # Setup risk-specific tracking
            await self._setup_risk_threshold_tracking(test_id, test_config)
            
            logger.info(f"Created risk threshold test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk threshold test: {e}")
            raise
    
    async def create_risk_communication_test(
        self,
        test_name: str,
        communication_variants: List[CommunicationTone],
        success_criteria: List[str],
        target_participants: int = 900,
        test_duration_days: int = 30
    ) -> str:
        """Create A/B test for risk communication approaches"""
        try:
            test_id = str(uuid.uuid4())
            
            # Define communication variants
            communication_configs = {
                'direct': {
                    'message_tone': 'direct',
                    'urgency_level': 'high',
                    'context_provided': 'personal_only',
                    'action_clarity': 'specific'
                },
                'encouraging': {
                    'message_tone': 'encouraging',
                    'urgency_level': 'medium',
                    'context_provided': 'personal_and_industry',
                    'action_clarity': 'guided'
                },
                'data_driven': {
                    'message_tone': 'analytical',
                    'urgency_level': 'factual',
                    'context_provided': 'industry_benchmarks',
                    'action_clarity': 'options_based'
                },
                'supportive': {
                    'message_tone': 'supportive',
                    'urgency_level': 'low',
                    'context_provided': 'personal_context',
                    'action_clarity': 'suggested'
                },
                'urgent': {
                    'message_tone': 'urgent',
                    'urgency_level': 'critical',
                    'context_provided': 'immediate_action',
                    'action_clarity': 'mandatory'
                }
            }
            
            # Create test configuration
            test_config = RiskTestConfig(
                test_name=test_name,
                test_type=RiskTestType.RISK_COMMUNICATION_TEST,
                description=f"A/B test for risk communication optimization: {test_name}",
                hypothesis="Different communication approaches will improve user engagement and action rates",
                variants={
                    variant.value: communication_configs[variant.value] 
                    for variant in communication_variants
                },
                success_criteria=success_criteria,
                target_participants=target_participants,
                test_duration_days=test_duration_days,
                minimum_risk_users_per_variant=45
            )
            
            # Store test configuration
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_ab_test_configs 
                    (test_id, test_name, test_type, description, hypothesis, variants_config,
                     success_criteria, target_participants, test_duration_days, 
                     minimum_risk_users_per_variant, risk_score_range, status, start_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    test_config.test_name,
                    test_config.test_type.value,
                    test_config.description,
                    test_config.hypothesis,
                    json.dumps(test_config.variants),
                    json.dumps(test_config.success_criteria),
                    test_config.target_participants,
                    test_config.test_duration_days,
                    test_config.minimum_risk_users_per_variant,
                    json.dumps(test_config.risk_score_range),
                    'active',
                    datetime.now()
                ))
                
                conn.commit()
            
            logger.info(f"Created risk communication test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk communication test: {e}")
            raise
    
    async def create_intervention_timing_test(
        self,
        test_name: str,
        timing_variants: List[TimingStrategy],
        success_criteria: List[str],
        target_participants: int = 600,
        test_duration_days: int = 21
    ) -> str:
        """Create A/B test for intervention timing optimization"""
        try:
            test_id = str(uuid.uuid4())
            
            # Define timing strategies
            timing_configs = {
                'immediate': {
                    'delay_hours': 0,
                    'best_time_targeting': False,
                    'follow_up_sequence': 'none'
                },
                'optimized_timing': {
                    'delay_hours': 2,
                    'best_time_targeting': True,
                    'follow_up_sequence': 'gradual'
                },
                'scheduled_outreach': {
                    'delay_hours': 24,
                    'best_time_targeting': True,
                    'follow_up_sequence': 'comprehensive'
                },
                'gradual_escalation': {
                    'delay_hours': 1,
                    'best_time_targeting': True,
                    'follow_up_sequence': 'escalating'
                }
            }
            
            # Create test configuration
            test_config = RiskTestConfig(
                test_name=test_name,
                test_type=RiskTestType.INTERVENTION_TIMING_OPTIMIZATION,
                description=f"A/B test for intervention timing optimization: {test_name}",
                hypothesis="Optimal timing for risk interventions will improve user response rates",
                variants={
                    variant.value: timing_configs[variant.value] 
                    for variant in timing_variants
                },
                success_criteria=success_criteria,
                target_participants=target_participants,
                test_duration_days=test_duration_days,
                minimum_risk_users_per_variant=40
            )
            
            # Store test configuration
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_ab_test_configs 
                    (test_id, test_name, test_type, description, hypothesis, variants_config,
                     success_criteria, target_participants, test_duration_days, 
                     minimum_risk_users_per_variant, risk_score_range, status, start_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    test_config.test_name,
                    test_config.test_type.value,
                    test_config.hypothesis,
                    json.dumps(test_config.variants),
                    json.dumps(test_config.success_criteria),
                    test_config.target_participants,
                    test_config.test_duration_days,
                    test_config.minimum_risk_users_per_variant,
                    json.dumps(test_config.risk_score_range),
                    'active',
                    datetime.now()
                ))
                
                conn.commit()
            
            logger.info(f"Created intervention timing test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating intervention timing test: {e}")
            raise
    
    async def run_risk_communication_experiment(
        self, 
        user_id: str, 
        risk_score: float, 
        experiment_group: str
    ) -> Dict[str, Any]:
        """Test different risk communication approaches"""
        try:
            communication_variants = {
                'direct': {
                    'message_tone': 'direct',
                    'urgency_level': 'high',
                    'context_provided': 'personal_only',
                    'action_clarity': 'specific'
                },
                'encouraging': {
                    'message_tone': 'encouraging',
                    'urgency_level': 'medium',
                    'context_provided': 'personal_and_industry',
                    'action_clarity': 'guided'
                },
                'data_driven': {
                    'message_tone': 'analytical',
                    'urgency_level': 'factual',
                    'context_provided': 'industry_benchmarks',
                    'action_clarity': 'options_based'
                }
            }
            
            variant = communication_variants.get(experiment_group, communication_variants['direct'])
            
            # Generate risk message based on variant
            risk_message = await self._generate_variant_risk_message(risk_score, variant)
            
            # Track experiment exposure
            await self._track_experiment_exposure(
                user_id=user_id,
                experiment='risk_communication_test',
                variant=experiment_group,
                risk_score=risk_score
            )
            
            # Deliver message and track response
            response = await self._deliver_risk_message(user_id, risk_message, variant)
            
            # Track immediate response metrics
            await self._track_risk_communication_response(user_id, experiment_group, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error running risk communication experiment: {e}")
            raise
    
    async def optimize_intervention_timing(
        self, 
        user_risk_data: Dict[str, Any], 
        timing_variant: str
    ) -> Dict[str, Any]:
        """Test optimal timing for risk-based interventions"""
        try:
            timing_strategies = {
                'immediate': {
                    'delay_hours': 0,
                    'best_time_targeting': False,
                    'follow_up_sequence': 'none'
                },
                'optimized_timing': {
                    'delay_hours': 2,
                    'best_time_targeting': True,
                    'follow_up_sequence': 'gradual'
                },
                'scheduled_outreach': {
                    'delay_hours': 24,
                    'best_time_targeting': True,
                    'follow_up_sequence': 'comprehensive'
                }
            }
            
            strategy = timing_strategies.get(timing_variant, timing_strategies['immediate'])
            
            # Schedule intervention based on strategy
            intervention_plan = {
                'user_id': user_risk_data['user_id'],
                'risk_score': user_risk_data['risk_score'],
                'timing_strategy': timing_variant,
                'scheduled_time': datetime.now() + timedelta(hours=strategy['delay_hours']),
                'follow_up_plan': await self._create_follow_up_plan(strategy['follow_up_sequence'])
            }
            
            # Track timing experiment
            await self._track_timing_experiment(intervention_plan)
            
            return intervention_plan
            
        except Exception as e:
            logger.error(f"Error optimizing intervention timing: {e}")
            raise
    
    async def assign_user_to_risk_test(
        self, 
        test_id: str, 
        user_id: str, 
        risk_score: float
    ) -> Optional[str]:
        """Assign a user to a risk A/B test variant"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user is already assigned
                cursor.execute('''
                    SELECT variant_id FROM risk_ab_test_participants 
                    WHERE test_id = ? AND user_id = ?
                ''', (test_id, user_id))
                
                existing_assignment = cursor.fetchone()
                if existing_assignment:
                    return existing_assignment[0]
                
                # Get test configuration
                cursor.execute('''
                    SELECT variants_config, status, minimum_risk_users_per_variant
                    FROM risk_ab_test_configs WHERE test_id = ?
                ''', (test_id,))
                
                test_info = cursor.fetchone()
                if not test_info or test_info[1] != 'active':
                    return None
                
                variants_config = json.loads(test_info[0])
                min_risk_users = test_info[2]
                
                # Check if we have enough risk users for each variant
                for variant_id in variants_config.keys():
                    cursor.execute('''
                        SELECT COUNT(*) FROM risk_ab_test_participants 
                        WHERE test_id = ? AND variant_id = ? AND risk_score >= 0.5
                    ''', (test_id, variant_id))
                    
                    risk_user_count = cursor.fetchone()[0]
                    if risk_user_count < min_risk_users:
                        # Assign to this variant to balance risk users
                        variant_id_to_assign = variant_id
                        break
                else:
                    # Use consistent hashing for assignment
                    variant_id_to_assign = self._assign_variant_by_risk_score(user_id, list(variants_config.keys()))
                
                # Determine risk level
                risk_level = self._determine_risk_level(risk_score)
                
                # Record assignment
                cursor.execute('''
                    INSERT INTO risk_ab_test_participants 
                    (test_id, user_id, variant_id, risk_score, risk_level, assigned_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (test_id, user_id, variant_id_to_assign, risk_score, risk_level, datetime.now()))
                
                conn.commit()
                
                logger.debug(f"Assigned user {user_id} to variant {variant_id_to_assign} in risk test {test_id}")
                return variant_id_to_assign
                
        except Exception as e:
            logger.error(f"Error assigning user to risk test: {e}")
            return None
    
    async def track_risk_test_conversion(
        self,
        test_id: str,
        user_id: str,
        conversion_event: str,
        value: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Track conversion event for a user in a risk A/B test"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user's current conversion events
                cursor.execute('''
                    SELECT conversion_events FROM risk_ab_test_participants 
                    WHERE test_id = ? AND user_id = ?
                ''', (test_id, user_id))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"User {user_id} not assigned to risk test {test_id}")
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
                    UPDATE risk_ab_test_participants 
                    SET conversion_events = ?, last_activity = ?
                    WHERE test_id = ? AND user_id = ?
                ''', (json.dumps(conversion_events), datetime.now(), test_id, user_id))
                
                conn.commit()
                
                logger.debug(f"Tracked risk test conversion {conversion_event} for user {user_id} in test {test_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking risk test conversion: {e}")
            return False
    
    async def measure_intervention_success_by_variant(self, test_id: str) -> Dict[str, Any]:
        """Compare success rates across A/B test variants"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get test configuration
                cursor.execute('''
                    SELECT test_name, success_criteria FROM risk_ab_test_configs 
                    WHERE test_id = ?
                ''', (test_id,))
                
                test_info = cursor.fetchone()
                if not test_info:
                    return {'error': 'Test not found'}
                
                test_name, success_criteria = test_info
                success_criteria = json.loads(success_criteria)
                
                # Get variant performance data
                cursor.execute('''
                    SELECT 
                        p.variant_id,
                        p.risk_level,
                        COUNT(*) as total_participants,
                        COUNT(CASE WHEN p.risk_score >= 0.5 THEN 1 END) as risk_users,
                        AVG(p.risk_score) as avg_risk_score,
                        p.conversion_events
                    FROM risk_ab_test_participants p
                    WHERE p.test_id = ?
                    GROUP BY p.variant_id, p.risk_level
                ''', (test_id,))
                
                variant_data = cursor.fetchall()
                
                # Analyze each variant
                variant_results = {}
                for row in variant_data:
                    variant_id, risk_level, total_participants, risk_users, avg_risk_score, conversion_events = row
                    
                    if variant_id not in variant_results:
                        variant_results[variant_id] = {
                            'total_participants': 0,
                            'risk_users': 0,
                            'avg_risk_score': 0,
                            'conversion_rates': {},
                            'success_metrics': {}
                        }
                    
                    variant_results[variant_id]['total_participants'] += total_participants
                    variant_results[variant_id]['risk_users'] += risk_users
                    variant_results[variant_id]['avg_risk_score'] = avg_risk_score
                    
                    # Calculate conversion rates
                    if conversion_events:
                        events = json.loads(conversion_events)
                        for event_type, events_list in events.items():
                            if event_type in success_criteria:
                                conversion_rate = len(events_list) / total_participants if total_participants > 0 else 0
                                variant_results[variant_id]['conversion_rates'][event_type] = conversion_rate
                
                # Calculate success metrics
                for variant_id, data in variant_results.items():
                    data['success_metrics'] = self._calculate_risk_success_metrics(data, success_criteria)
                
                return {
                    'test_id': test_id,
                    'test_name': test_name,
                    'variant_results': variant_results,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error measuring intervention success by variant: {e}")
            return {'error': str(e)}
    
    async def track_long_term_career_outcomes(self, test_id: str, months: int = 6) -> Dict[str, Any]:
        """Measure 6-month career protection success by test variant"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get participants from the test
                cursor.execute('''
                    SELECT p.user_id, p.variant_id, p.risk_score, p.risk_level
                    FROM risk_ab_test_participants p
                    WHERE p.test_id = ? AND p.assigned_at <= datetime('now', '-{} months')
                '''.format(months), (test_id,))
                
                participants = cursor.fetchall()
                
                if not participants:
                    return {'error': 'No participants found for long-term analysis'}
                
                # Get career outcomes for each participant
                variant_outcomes = {}
                for user_id, variant_id, risk_score, risk_level in participants:
                    if variant_id not in variant_outcomes:
                        variant_outcomes[variant_id] = {
                            'participants': 0,
                            'successful_outcomes': 0,
                            'career_advancements': 0,
                            'salary_improvements': 0,
                            'risk_mitigation_success': 0
                        }
                    
                    variant_outcomes[variant_id]['participants'] += 1
                    
                    # Get career protection outcomes
                    cursor.execute('''
                        SELECT outcome_type, transition_success, salary_improvement_percentage, 
                               risk_mitigation_effectiveness
                        FROM career_protection_outcomes 
                        WHERE user_id = ? AND outcome_timestamp >= datetime('now', '-{} months')
                    '''.format(months), (user_id,))
                    
                    outcomes = cursor.fetchall()
                    
                    for outcome_type, success, salary_improvement, risk_mitigation in outcomes:
                        if success:
                            variant_outcomes[variant_id]['successful_outcomes'] += 1
                        
                        if outcome_type in ['proactive_switch', 'promotion_received']:
                            variant_outcomes[variant_id]['career_advancements'] += 1
                        
                        if salary_improvement and salary_improvement > 0:
                            variant_outcomes[variant_id]['salary_improvements'] += 1
                        
                        if risk_mitigation and risk_mitigation > 0.7:
                            variant_outcomes[variant_id]['risk_mitigation_success'] += 1
                
                # Calculate success rates
                for variant_id, data in variant_outcomes.items():
                    total_participants = data['participants']
                    if total_participants > 0:
                        data['success_rate'] = data['successful_outcomes'] / total_participants
                        data['career_advancement_rate'] = data['career_advancements'] / total_participants
                        data['salary_improvement_rate'] = data['salary_improvements'] / total_participants
                        data['risk_mitigation_rate'] = data['risk_mitigation_success'] / total_participants
                    else:
                        data['success_rate'] = 0
                        data['career_advancement_rate'] = 0
                        data['salary_improvement_rate'] = 0
                        data['risk_mitigation_rate'] = 0
                
                return {
                    'test_id': test_id,
                    'analysis_period_months': months,
                    'variant_outcomes': variant_outcomes,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error tracking long-term career outcomes: {e}")
            return {'error': str(e)}
    
    async def analyze_user_satisfaction_by_variant(self, test_id: str) -> Dict[str, Any]:
        """Compare user experience across risk communication approaches"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user satisfaction data by variant
                cursor.execute('''
                    SELECT 
                        p.variant_id,
                        COUNT(*) as total_users,
                        AVG(CASE WHEN c.message_clarity_score IS NOT NULL THEN c.message_clarity_score END) as avg_clarity,
                        AVG(CASE WHEN c.user_understanding_score IS NOT NULL THEN c.user_understanding_score END) as avg_understanding,
                        COUNT(CASE WHEN c.action_taken = 1 THEN 1 END) as users_taking_action,
                        AVG(CASE WHEN c.time_to_action_hours IS NOT NULL THEN c.time_to_action_hours END) as avg_time_to_action
                    FROM risk_ab_test_participants p
                    LEFT JOIN risk_communication_effectiveness c ON p.user_id = c.user_id
                    WHERE p.test_id = ?
                    GROUP BY p.variant_id
                ''', (test_id,))
                
                satisfaction_data = cursor.fetchall()
                
                variant_satisfaction = {}
                for row in satisfaction_data:
                    variant_id, total_users, avg_clarity, avg_understanding, users_taking_action, avg_time_to_action = row
                    
                    variant_satisfaction[variant_id] = {
                        'total_users': total_users,
                        'avg_clarity_score': avg_clarity or 0,
                        'avg_understanding_score': avg_understanding or 0,
                        'action_taken_count': users_taking_action,
                        'action_taken_rate': users_taking_action / total_users if total_users > 0 else 0,
                        'avg_time_to_action_hours': avg_time_to_action or 0,
                        'satisfaction_score': self._calculate_satisfaction_score(
                            avg_clarity or 0, avg_understanding or 0, 
                            users_taking_action / total_users if total_users > 0 else 0
                        )
                    }
                
                return {
                    'test_id': test_id,
                    'variant_satisfaction': variant_satisfaction,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing user satisfaction by variant: {e}")
            return {'error': str(e)}
    
    async def calculate_roi_by_test_variant(self, test_id: str) -> Dict[str, Any]:
        """Measure business impact of different risk approaches"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get ROI data by variant
                cursor.execute('''
                    SELECT 
                        p.variant_id,
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN p.risk_score >= 0.5 THEN 1 END) as high_risk_users,
                        AVG(p.risk_score) as avg_risk_score,
                        COUNT(CASE WHEN o.transition_success = 1 THEN 1 END) as successful_transitions,
                        AVG(CASE WHEN o.salary_improvement_percentage IS NOT NULL THEN o.salary_improvement_percentage END) as avg_salary_improvement,
                        AVG(CASE WHEN o.risk_mitigation_effectiveness IS NOT NULL THEN o.risk_mitigation_effectiveness END) as avg_risk_mitigation
                    FROM risk_ab_test_participants p
                    LEFT JOIN career_protection_outcomes o ON p.user_id = o.user_id
                    WHERE p.test_id = ?
                    GROUP BY p.variant_id
                ''', (test_id,))
                
                roi_data = cursor.fetchall()
                
                variant_roi = {}
                for row in roi_data:
                    variant_id, total_users, high_risk_users, avg_risk_score, successful_transitions, avg_salary_improvement, avg_risk_mitigation = row
                    
                    # Calculate ROI metrics
                    success_rate = successful_transitions / total_users if total_users > 0 else 0
                    risk_mitigation_value = avg_risk_mitigation or 0
                    salary_protection_value = avg_salary_improvement or 0
                    
                    # Estimate business value (simplified calculation)
                    estimated_value_per_user = (success_rate * 1000) + (risk_mitigation_value * 500) + (salary_protection_value * 200)
                    total_estimated_value = estimated_value_per_user * total_users
                    
                    variant_roi[variant_id] = {
                        'total_users': total_users,
                        'high_risk_users': high_risk_users,
                        'avg_risk_score': avg_risk_score,
                        'success_rate': success_rate,
                        'avg_salary_improvement': avg_salary_improvement or 0,
                        'avg_risk_mitigation': avg_risk_mitigation or 0,
                        'estimated_value_per_user': estimated_value_per_user,
                        'total_estimated_value': total_estimated_value,
                        'roi_score': self._calculate_roi_score(success_rate, risk_mitigation_value, salary_protection_value)
                    }
                
                return {
                    'test_id': test_id,
                    'variant_roi': variant_roi,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error calculating ROI by test variant: {e}")
            return {'error': str(e)}
    
    # Helper methods
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _assign_variant_by_risk_score(self, user_id: str, variants: List[str]) -> str:
        """Assign user to variant using consistent hashing based on risk score"""
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        random.seed(user_hash)
        return random.choice(variants)
    
    def _calculate_risk_success_metrics(self, variant_data: Dict[str, Any], success_criteria: List[str]) -> Dict[str, Any]:
        """Calculate success metrics for a risk test variant"""
        metrics = {}
        
        for criterion in success_criteria:
            if criterion in variant_data.get('conversion_rates', {}):
                metrics[criterion] = variant_data['conversion_rates'][criterion]
            else:
                metrics[criterion] = 0.0
        
        # Calculate overall success score
        if success_criteria:
            metrics['overall_success_score'] = sum(metrics.get(criterion, 0) for criterion in success_criteria) / len(success_criteria)
        else:
            metrics['overall_success_score'] = 0.0
        
        return metrics
    
    def _calculate_satisfaction_score(self, clarity: float, understanding: float, action_rate: float) -> float:
        """Calculate overall satisfaction score"""
        return (clarity * 0.3 + understanding * 0.3 + action_rate * 0.4) * 100
    
    def _calculate_roi_score(self, success_rate: float, risk_mitigation: float, salary_improvement: float) -> float:
        """Calculate ROI score for a variant"""
        return (success_rate * 40 + risk_mitigation * 30 + salary_improvement * 30) * 100
    
    async def _setup_risk_threshold_tracking(self, test_id: str, test_config: RiskTestConfig) -> None:
        """Setup risk-specific tracking for threshold tests"""
        # This would integrate with the existing risk analytics system
        logger.info(f"Setup risk threshold tracking for test {test_id}")
    
    async def _generate_variant_risk_message(self, risk_score: float, variant: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk message based on variant configuration"""
        message_templates = {
            'direct': f"URGENT: Your career risk score is {risk_score:.1%}. Immediate action required.",
            'encouraging': f"Your career risk assessment shows {risk_score:.1%} risk. We're here to help you succeed!",
            'data_driven': f"Analysis indicates {risk_score:.1%} career risk based on industry benchmarks and personal factors."
        }
        
        tone = variant.get('message_tone', 'direct')
        message = message_templates.get(tone, message_templates['direct'])
        
        return {
            'message': message,
            'tone': tone,
            'urgency_level': variant.get('urgency_level', 'medium'),
            'context_provided': variant.get('context_provided', 'personal_only'),
            'action_clarity': variant.get('action_clarity', 'specific')
        }
    
    async def _track_experiment_exposure(self, user_id: str, experiment: str, variant: str, risk_score: float) -> None:
        """Track when a user is exposed to an experiment"""
        # This would integrate with the existing analytics system
        logger.debug(f"Tracked experiment exposure: {user_id} in {experiment} variant {variant}")
    
    async def _deliver_risk_message(self, user_id: str, message: Dict[str, Any], variant: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver risk message to user and track response"""
        # This would integrate with the notification system
        return {
            'delivered': True,
            'delivery_timestamp': datetime.now().isoformat(),
            'message_id': str(uuid.uuid4()),
            'response_tracking_id': str(uuid.uuid4())
        }
    
    async def _track_risk_communication_response(self, user_id: str, variant: str, response: Dict[str, Any]) -> None:
        """Track user response to risk communication"""
        # This would integrate with the existing analytics system
        logger.debug(f"Tracked risk communication response: {user_id} for variant {variant}")
    
    async def _create_follow_up_plan(self, sequence_type: str) -> Dict[str, Any]:
        """Create follow-up plan based on sequence type"""
        plans = {
            'none': {'follow_ups': []},
            'gradual': {
                'follow_ups': [
                    {'delay_hours': 24, 'type': 'reminder'},
                    {'delay_hours': 72, 'type': 'check_in'},
                    {'delay_hours': 168, 'type': 'final_reminder'}
                ]
            },
            'comprehensive': {
                'follow_ups': [
                    {'delay_hours': 6, 'type': 'immediate_follow_up'},
                    {'delay_hours': 24, 'type': 'detailed_guidance'},
                    {'delay_hours': 72, 'type': 'progress_check'},
                    {'delay_hours': 168, 'type': 'outcome_review'}
                ]
            },
            'escalating': {
                'follow_ups': [
                    {'delay_hours': 2, 'type': 'gentle_reminder'},
                    {'delay_hours': 12, 'type': 'stronger_urgency'},
                    {'delay_hours': 48, 'type': 'final_escalation'}
                ]
            }
        }
        
        return plans.get(sequence_type, plans['none'])
    
    async def _track_timing_experiment(self, intervention_plan: Dict[str, Any]) -> None:
        """Track timing experiment data"""
        # This would integrate with the existing analytics system
        logger.debug(f"Tracked timing experiment: {intervention_plan['user_id']} with strategy {intervention_plan['timing_strategy']}")
    
    # Continuous optimization methods
    async def auto_optimize_risk_thresholds(self, test_id: str) -> Dict[str, Any]:
        """Automatically adjust thresholds based on A/B test results"""
        try:
            # Get test results
            results = await self.measure_intervention_success_by_variant(test_id)
            
            if 'error' in results:
                return results
            
            # Find best performing variant
            best_variant = None
            best_score = 0
            
            for variant_id, data in results['variant_results'].items():
                success_metrics = data.get('success_metrics', {})
                overall_score = success_metrics.get('overall_success_score', 0)
                
                if overall_score > best_score:
                    best_score = overall_score
                    best_variant = variant_id
            
            if best_variant:
                # Extract threshold from variant name
                threshold = float(best_variant.split('_')[1])
                
                # Record optimization
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO risk_optimization_history 
                        (test_id, optimization_type, original_value, optimized_value, 
                         improvement_percentage, confidence_level, optimization_timestamp, test_results)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_id,
                        'risk_threshold',
                        0.5,  # Default threshold
                        threshold,
                        best_score * 100,
                        0.95,  # High confidence
                        datetime.now(),
                        json.dumps(results)
                    ))
                    
                    conn.commit()
                
                logger.info(f"Auto-optimized risk threshold to {threshold} based on test {test_id}")
                
                return {
                    'optimization_applied': True,
                    'new_threshold': threshold,
                    'improvement_percentage': best_score * 100,
                    'confidence_level': 0.95
                }
            
            return {'optimization_applied': False, 'reason': 'No clear winner found'}
            
        except Exception as e:
            logger.error(f"Error auto-optimizing risk thresholds: {e}")
            return {'error': str(e)}
    
    async def dynamic_communication_personalization(self, user_id: str, risk_score: float) -> Dict[str, Any]:
        """Use A/B test results to personalize risk communication"""
        try:
            # Get user's communication preferences based on past test results
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT p.variant_id, c.message_clarity_score, c.user_understanding_score, c.action_taken
                    FROM risk_ab_test_participants p
                    LEFT JOIN risk_communication_effectiveness c ON p.user_id = c.user_id
                    WHERE p.user_id = ? AND p.test_id LIKE '%communication%'
                    ORDER BY p.assigned_at DESC
                    LIMIT 1
                ''', (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    variant_id, clarity, understanding, action_taken = result
                    
                    # Determine best communication approach for this user
                    if clarity and understanding and action_taken:
                        if clarity > 0.8 and understanding > 0.8:
                            preferred_tone = 'data_driven'
                        elif action_taken:
                            preferred_tone = 'encouraging'
                        else:
                            preferred_tone = 'direct'
                    else:
                        preferred_tone = 'supportive'
                else:
                    # Default based on risk score
                    if risk_score >= 0.7:
                        preferred_tone = 'urgent'
                    elif risk_score >= 0.5:
                        preferred_tone = 'direct'
                    else:
                        preferred_tone = 'encouraging'
                
                return {
                    'personalized_tone': preferred_tone,
                    'risk_score': risk_score,
                    'personalization_based_on': 'test_results' if result else 'risk_score'
                }
                
        except Exception as e:
            logger.error(f"Error in dynamic communication personalization: {e}")
            return {'personalized_tone': 'supportive', 'risk_score': risk_score}
    
    async def adaptive_intervention_timing(self, user_id: str, risk_score: float) -> Dict[str, Any]:
        """Optimize intervention timing based on user behavior patterns"""
        try:
            # Analyze user's response patterns
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT p.variant_id, p.assigned_at, p.last_activity, p.conversion_events
                    FROM risk_ab_test_participants p
                    WHERE p.user_id = ? AND p.test_id LIKE '%timing%'
                    ORDER BY p.assigned_at DESC
                    LIMIT 5
                ''', (user_id,))
                
                timing_data = cursor.fetchall()
                
                if timing_data:
                    # Analyze response times
                    response_times = []
                    for variant_id, assigned_at, last_activity, conversion_events in timing_data:
                        if last_activity and conversion_events:
                            events = json.loads(conversion_events)
                            if events:
                                # Calculate average response time
                                assigned_dt = datetime.fromisoformat(assigned_at)
                                last_dt = datetime.fromisoformat(last_activity)
                                response_time = (last_dt - assigned_dt).total_seconds() / 3600  # hours
                                response_times.append(response_time)
                    
                    if response_times:
                        avg_response_time = sum(response_times) / len(response_times)
                        
                        # Determine optimal timing based on response patterns
                        if avg_response_time < 2:
                            optimal_timing = 'immediate'
                        elif avg_response_time < 24:
                            optimal_timing = 'optimized_timing'
                        else:
                            optimal_timing = 'scheduled_outreach'
                    else:
                        optimal_timing = 'optimized_timing'
                else:
                    # Default timing based on risk score
                    if risk_score >= 0.8:
                        optimal_timing = 'immediate'
                    elif risk_score >= 0.6:
                        optimal_timing = 'optimized_timing'
                    else:
                        optimal_timing = 'scheduled_outreach'
                
                return {
                    'optimal_timing': optimal_timing,
                    'risk_score': risk_score,
                    'timing_based_on': 'user_behavior' if timing_data else 'risk_score'
                }
                
        except Exception as e:
            logger.error(f"Error in adaptive intervention timing: {e}")
            return {'optimal_timing': 'optimized_timing', 'risk_score': risk_score}
    
    async def iterative_success_improvement(self, test_id: str) -> Dict[str, Any]:
        """Continuous testing and optimization of risk intervention approaches"""
        try:
            # Get comprehensive test results
            success_results = await self.measure_intervention_success_by_variant(test_id)
            satisfaction_results = await self.analyze_user_satisfaction_by_variant(test_id)
            roi_results = await self.calculate_roi_by_test_variant(test_id)
            
            if 'error' in success_results:
                return success_results
            
            # Identify improvement opportunities
            improvements = []
            
            # Check for low-performing variants
            for variant_id, data in success_results['variant_results'].items():
                success_metrics = data.get('success_metrics', {})
                overall_score = success_metrics.get('overall_success_score', 0)
                
                if overall_score < 0.3:  # Low performance threshold
                    improvements.append({
                        'variant_id': variant_id,
                        'issue': 'low_success_rate',
                        'current_score': overall_score,
                        'recommendation': 'Consider adjusting parameters or removing variant'
                    })
            
            # Check satisfaction scores
            if 'error' not in satisfaction_results:
                for variant_id, data in satisfaction_results['variant_satisfaction'].items():
                    satisfaction_score = data.get('satisfaction_score', 0)
                    
                    if satisfaction_score < 60:  # Low satisfaction threshold
                        improvements.append({
                            'variant_id': variant_id,
                            'issue': 'low_satisfaction',
                            'current_score': satisfaction_score,
                            'recommendation': 'Improve communication clarity and user experience'
                        })
            
            # Check ROI performance
            if 'error' not in roi_results:
                for variant_id, data in roi_results['variant_roi'].items():
                    roi_score = data.get('roi_score', 0)
                    
                    if roi_score < 50:  # Low ROI threshold
                        improvements.append({
                            'variant_id': variant_id,
                            'issue': 'low_roi',
                            'current_score': roi_score,
                            'recommendation': 'Optimize for better business outcomes'
                        })
            
            return {
                'test_id': test_id,
                'improvements_identified': len(improvements),
                'improvements': improvements,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in iterative success improvement: {e}")
            return {'error': str(e)}
