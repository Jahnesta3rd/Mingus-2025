#!/usr/bin/env python3
"""
Risk System Health Monitoring for Mingus Application
===================================================

Comprehensive health monitoring system for risk-based workflows including
model drift detection, data quality validation, and system failure alerting.

Features:
- Risk model drift detection and monitoring
- Data quality validation for risk assessments
- System failure detection and alerting
- User engagement monitoring for risk alerts
- Performance degradation tracking
- Automated health checks and recovery

Author: Mingus Risk Performance Team
Date: January 2025
"""

import asyncio
import sqlite3
import json
import logging
import time
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psutil
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"

class DriftType(Enum):
    """Types of model drift"""
    CONCEPT_DRIFT = "concept_drift"
    DATA_DRIFT = "data_drift"
    PERFORMANCE_DRIFT = "performance_drift"
    COVARIATE_DRIFT = "covariate_drift"

@dataclass
class ModelDriftMetrics:
    """Model drift detection metrics"""
    model_name: str
    drift_type: str
    drift_score: float
    confidence: float
    baseline_period: str
    current_period: str
    feature_contributions: Dict[str, float]
    detection_timestamp: str
    severity: str

@dataclass
class DataQualityMetrics:
    """Data quality validation metrics"""
    timestamp: str
    total_records: int
    valid_records: int
    invalid_records: int
    missing_values: int
    duplicate_records: int
    outlier_count: int
    quality_score: float
    validation_errors: List[str]
    data_sources: Dict[str, int]

@dataclass
class SystemHealthMetrics:
    """Overall system health metrics"""
    timestamp: str
    overall_status: str
    component_status: Dict[str, str]
    performance_score: float
    reliability_score: float
    data_quality_score: float
    model_accuracy_score: float
    user_engagement_score: float
    critical_alerts: int
    warning_alerts: int
    uptime_percentage: float
    last_failure: Optional[str]

@dataclass
class UserEngagementMetrics:
    """User engagement with risk alerts and recommendations"""
    user_id: str
    risk_level: str
    alert_response_time: float
    recommendation_click_rate: float
    feature_usage_rate: float
    session_duration: float
    return_visits: int
    conversion_rate: float
    engagement_score: float
    timestamp: str

class RiskModelDriftDetector:
    """Detects and monitors risk model drift"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.drift_threshold = 0.1  # 10% drift threshold
        self.confidence_threshold = 0.8
        self.baseline_window_days = 30
        self.current_window_days = 7
        
    async def detect_model_drift(self, model_name: str) -> Optional[ModelDriftMetrics]:
        """Detect model drift for a specific model"""
        try:
            # Get baseline and current data
            baseline_data = await self._get_baseline_data(model_name)
            current_data = await self._get_current_data(model_name)
            
            if not baseline_data or not current_data:
                logger.warning(f"Insufficient data for drift detection: {model_name}")
                return None
            
            # Calculate drift metrics
            drift_metrics = await self._calculate_drift_metrics(
                model_name, baseline_data, current_data
            )
            
            if drift_metrics and drift_metrics.drift_score > self.drift_threshold:
                # Log drift detection
                await self._log_drift_detection(drift_metrics)
                logger.warning(f"Model drift detected for {model_name}: {drift_metrics.drift_score:.3f}")
                return drift_metrics
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting model drift for {model_name}: {e}")
            return None
    
    async def _get_baseline_data(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get baseline model performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get baseline performance data
            cursor.execute('''
                SELECT accuracy, precision, recall, f1_score, inference_time
                FROM risk_model_performance 
                WHERE model_name = ? 
                AND timestamp >= datetime('now', '-{} days')
                AND timestamp < datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(
                self.baseline_window_days + self.current_window_days,
                self.current_window_days
            ))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return None
            
            # Calculate baseline metrics
            accuracies = [r[0] for r in results]
            precisions = [r[1] for r in results]
            recalls = [r[2] for r in results]
            f1_scores = [r[3] for r in results]
            inference_times = [r[4] for r in results]
            
            return {
                'accuracy': statistics.mean(accuracies),
                'precision': statistics.mean(precisions),
                'recall': statistics.mean(recalls),
                'f1_score': statistics.mean(f1_scores),
                'inference_time': statistics.mean(inference_times),
                'accuracy_std': statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
                'sample_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error getting baseline data: {e}")
            return None
    
    async def _get_current_data(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get current model performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current performance data
            cursor.execute('''
                SELECT accuracy, precision, recall, f1_score, inference_time
                FROM risk_model_performance 
                WHERE model_name = ? 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(self.current_window_days))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return None
            
            # Calculate current metrics
            accuracies = [r[0] for r in results]
            precisions = [r[1] for r in results]
            recalls = [r[2] for r in results]
            f1_scores = [r[3] for r in results]
            inference_times = [r[4] for r in results]
            
            return {
                'accuracy': statistics.mean(accuracies),
                'precision': statistics.mean(precisions),
                'recall': statistics.mean(recalls),
                'f1_score': statistics.mean(f1_scores),
                'inference_time': statistics.mean(inference_times),
                'accuracy_std': statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
                'sample_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error getting current data: {e}")
            return None
    
    async def _calculate_drift_metrics(self, model_name: str, baseline_data: Dict[str, Any], 
                                     current_data: Dict[str, Any]) -> Optional[ModelDriftMetrics]:
        """Calculate drift metrics between baseline and current data"""
        try:
            # Calculate performance drift
            accuracy_drift = abs(current_data['accuracy'] - baseline_data['accuracy'])
            precision_drift = abs(current_data['precision'] - baseline_data['precision'])
            recall_drift = abs(current_data['recall'] - baseline_data['recall'])
            f1_drift = abs(current_data['f1_score'] - baseline_data['f1_score'])
            
            # Calculate overall drift score
            drift_score = (accuracy_drift + precision_drift + recall_drift + f1_drift) / 4
            
            # Calculate confidence based on sample sizes
            baseline_samples = baseline_data['sample_count']
            current_samples = current_data['sample_count']
            confidence = min(1.0, (baseline_samples + current_samples) / 100)
            
            # Determine drift type
            drift_type = DriftType.PERFORMANCE_DRIFT.value
            if accuracy_drift > 0.1:
                drift_type = DriftType.CONCEPT_DRIFT.value
            elif current_data['inference_time'] > baseline_data['inference_time'] * 1.5:
                drift_type = DriftType.DATA_DRIFT.value
            
            # Calculate feature contributions (simplified)
            feature_contributions = {
                'accuracy': accuracy_drift,
                'precision': precision_drift,
                'recall': recall_drift,
                'f1_score': f1_drift
            }
            
            # Determine severity
            severity = 'LOW'
            if drift_score > 0.2:
                severity = 'HIGH'
            elif drift_score > 0.15:
                severity = 'MEDIUM'
            
            return ModelDriftMetrics(
                model_name=model_name,
                drift_type=drift_type,
                drift_score=drift_score,
                confidence=confidence,
                baseline_period=f"last_{self.baseline_window_days}_days",
                current_period=f"last_{self.current_window_days}_days",
                feature_contributions=feature_contributions,
                detection_timestamp=datetime.now().isoformat(),
                severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error calculating drift metrics: {e}")
            return None
    
    async def _log_drift_detection(self, drift_metrics: ModelDriftMetrics):
        """Log drift detection to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_system_alerts (
                    alert_type, severity, message, metric_name, threshold_value,
                    actual_value, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'MODEL_DRIFT_DETECTED',
                drift_metrics.severity,
                f"Model drift detected for {drift_metrics.model_name}: {drift_metrics.drift_score:.3f}",
                'model_drift_score',
                0.1,  # threshold
                drift_metrics.drift_score,
                'system'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging drift detection: {e}")

class DataQualityValidator:
    """Validates data quality for risk assessments"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.quality_thresholds = {
            'min_quality_score': 0.8,
            'max_missing_rate': 0.1,
            'max_duplicate_rate': 0.05,
            'max_outlier_rate': 0.15
        }
    
    async def validate_data_quality(self) -> DataQualityMetrics:
        """Validate data quality for risk assessments"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent risk assessment data
            cursor.execute('''
                SELECT user_id, assessment_type, overall_risk, risk_triggers,
                       risk_breakdown, timeline_urgency, confidence_score, risk_factors
                FROM risk_assessments 
                WHERE assessment_timestamp >= datetime('now', '-7 days')
            ''')
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return DataQualityMetrics(
                    timestamp=datetime.now().isoformat(),
                    total_records=0,
                    valid_records=0,
                    invalid_records=0,
                    missing_values=0,
                    duplicate_records=0,
                    outlier_count=0,
                    quality_score=0.0,
                    validation_errors=[],
                    data_sources={}
                )
            
            # Analyze data quality
            total_records = len(records)
            valid_records = 0
            invalid_records = 0
            missing_values = 0
            duplicate_records = 0
            outlier_count = 0
            validation_errors = []
            data_sources = {}
            
            # Track unique records for duplicate detection
            seen_records = set()
            
            for record in records:
                user_id, assessment_type, overall_risk, risk_triggers, risk_breakdown, timeline_urgency, confidence_score, risk_factors = record
                
                # Check for duplicates
                record_key = (user_id, assessment_type, overall_risk)
                if record_key in seen_records:
                    duplicate_records += 1
                else:
                    seen_records.add(record_key)
                
                # Validate record
                is_valid = True
                record_errors = []
                
                # Check for missing values
                if not user_id or user_id.strip() == '':
                    missing_values += 1
                    record_errors.append('Missing user_id')
                    is_valid = False
                
                if not assessment_type or assessment_type.strip() == '':
                    missing_values += 1
                    record_errors.append('Missing assessment_type')
                    is_valid = False
                
                if overall_risk is None or overall_risk < 0 or overall_risk > 1:
                    missing_values += 1
                    record_errors.append('Invalid overall_risk value')
                    is_valid = False
                
                if not risk_triggers or risk_triggers.strip() == '':
                    missing_values += 1
                    record_errors.append('Missing risk_triggers')
                    is_valid = False
                
                # Check for outliers in risk scores
                if overall_risk is not None and (overall_risk < 0.1 or overall_risk > 0.9):
                    outlier_count += 1
                
                # Check confidence score validity
                if confidence_score is not None and (confidence_score < 0 or confidence_score > 1):
                    record_errors.append('Invalid confidence_score')
                    is_valid = False
                
                if is_valid:
                    valid_records += 1
                else:
                    invalid_records += 1
                    validation_errors.extend(record_errors)
                
                # Track data sources
                if assessment_type not in data_sources:
                    data_sources[assessment_type] = 0
                data_sources[assessment_type] += 1
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                total_records, valid_records, missing_values, 
                duplicate_records, outlier_count
            )
            
            return DataQualityMetrics(
                timestamp=datetime.now().isoformat(),
                total_records=total_records,
                valid_records=valid_records,
                invalid_records=invalid_records,
                missing_values=missing_values,
                duplicate_records=duplicate_records,
                outlier_count=outlier_count,
                quality_score=quality_score,
                validation_errors=validation_errors,
                data_sources=data_sources
            )
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            return DataQualityMetrics(
                timestamp=datetime.now().isoformat(),
                total_records=0,
                valid_records=0,
                invalid_records=0,
                missing_values=0,
                duplicate_records=0,
                outlier_count=0,
                quality_score=0.0,
                validation_errors=[f"Error: {str(e)}"],
                data_sources={}
            )
    
    def _calculate_quality_score(self, total_records: int, valid_records: int, 
                               missing_values: int, duplicate_records: int, 
                               outlier_count: int) -> float:
        """Calculate overall data quality score"""
        if total_records == 0:
            return 0.0
        
        # Calculate individual quality metrics
        validity_rate = valid_records / total_records
        completeness_rate = 1 - (missing_values / (total_records * 5))  # 5 fields per record
        uniqueness_rate = 1 - (duplicate_records / total_records)
        consistency_rate = 1 - (outlier_count / total_records)
        
        # Weighted average
        quality_score = (
            validity_rate * 0.4 +
            completeness_rate * 0.3 +
            uniqueness_rate * 0.2 +
            consistency_rate * 0.1
        )
        
        return min(1.0, max(0.0, quality_score))

class UserEngagementMonitor:
    """Monitors user engagement with risk alerts and recommendations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engagement_thresholds = {
            'min_response_time': 300,  # 5 minutes
            'min_click_rate': 0.1,     # 10%
            'min_usage_rate': 0.05,    # 5%
            'min_session_duration': 60  # 1 minute
        }
    
    async def monitor_user_engagement(self, user_id: str) -> Optional[UserEngagementMetrics]:
        """Monitor engagement for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's risk assessment data
            cursor.execute('''
                SELECT risk_level, assessment_timestamp
                FROM risk_assessments 
                WHERE user_id = ?
                ORDER BY assessment_timestamp DESC
                LIMIT 1
            ''', (user_id,))
            
            risk_data = cursor.fetchone()
            if not risk_data:
                conn.close()
                return None
            
            risk_level, assessment_timestamp = risk_data
            
            # Get user interaction data (simplified - would need actual interaction tracking)
            cursor.execute('''
                SELECT COUNT(*) as total_interactions,
                       AVG(time_spent) as avg_time_spent
                FROM user_sessions 
                WHERE user_id = ? 
                AND session_start >= datetime('now', '-30 days')
            ''', (user_id,))
            
            interaction_data = cursor.fetchone()
            total_interactions = interaction_data[0] or 0
            avg_time_spent = interaction_data[1] or 0
            
            conn.close()
            
            # Calculate engagement metrics
            alert_response_time = 300  # Simulated - would be calculated from actual data
            recommendation_click_rate = min(1.0, total_interactions / 10)  # Simulated
            feature_usage_rate = min(1.0, total_interactions / 20)  # Simulated
            session_duration = avg_time_spent or 0
            return_visits = max(0, total_interactions - 1)
            conversion_rate = min(1.0, total_interactions / 5)  # Simulated
            
            # Calculate overall engagement score
            engagement_score = self._calculate_engagement_score(
                alert_response_time, recommendation_click_rate, feature_usage_rate,
                session_duration, return_visits, conversion_rate
            )
            
            return UserEngagementMetrics(
                user_id=user_id,
                risk_level=risk_level,
                alert_response_time=alert_response_time,
                recommendation_click_rate=recommendation_click_rate,
                feature_usage_rate=feature_usage_rate,
                session_duration=session_duration,
                return_visits=return_visits,
                conversion_rate=conversion_rate,
                engagement_score=engagement_score,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error monitoring user engagement for {user_id}: {e}")
            return None
    
    def _calculate_engagement_score(self, alert_response_time: float, 
                                  recommendation_click_rate: float, 
                                  feature_usage_rate: float, 
                                  session_duration: float, 
                                  return_visits: int, 
                                  conversion_rate: float) -> float:
        """Calculate overall user engagement score"""
        # Normalize metrics
        response_score = max(0, 1 - (alert_response_time / 3600))  # 1 hour max
        click_score = min(1.0, recommendation_click_rate)
        usage_score = min(1.0, feature_usage_rate)
        duration_score = min(1.0, session_duration / 1800)  # 30 minutes max
        return_score = min(1.0, return_visits / 10)  # 10 visits max
        conversion_score = min(1.0, conversion_rate)
        
        # Weighted average
        engagement_score = (
            response_score * 0.2 +
            click_score * 0.2 +
            usage_score * 0.2 +
            duration_score * 0.15 +
            return_score * 0.15 +
            conversion_score * 0.1
        )
        
        return min(1.0, max(0.0, engagement_score))

class RiskSystemHealthMonitor:
    """Main risk system health monitoring class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'risk_health.db')
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Initialize components
        self.drift_detector = RiskModelDriftDetector(self.db_path)
        self.data_validator = DataQualityValidator(self.db_path)
        self.engagement_monitor = UserEngagementMonitor(self.db_path)
        
        # Health thresholds
        self.health_thresholds = {
            'min_performance_score': 0.8,
            'min_reliability_score': 0.9,
            'min_data_quality_score': 0.8,
            'min_model_accuracy_score': 0.75,
            'min_user_engagement_score': 0.6,
            'max_critical_alerts': 5,
            'max_warning_alerts': 20
        }
        
        logger.info("RiskSystemHealthMonitor initialized successfully")
    
    async def start_health_monitoring(self, interval_minutes: int = 5):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_health_continuously,
            args=(interval_minutes,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started health monitoring with {interval_minutes} minute interval")
    
    def stop_health_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("Stopped health monitoring")
    
    def _monitor_health_continuously(self, interval_minutes: int):
        """Continuous health monitoring loop"""
        while self.monitoring_active:
            try:
                # Run health check
                asyncio.run(self.run_health_check())
                time.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    async def run_health_check(self) -> SystemHealthMetrics:
        """Run comprehensive health check"""
        logger.info("Running risk system health check...")
        
        try:
            # Check model drift
            drift_alerts = await self._check_model_drift()
            
            # Validate data quality
            data_quality = await self.data_validator.validate_data_quality()
            
            # Check system performance
            performance_score = await self._check_system_performance()
            
            # Check reliability
            reliability_score = await self._check_system_reliability()
            
            # Check user engagement
            engagement_score = await self._check_user_engagement()
            
            # Count alerts
            critical_alerts, warning_alerts = await self._count_alerts()
            
            # Calculate overall health status
            overall_status = self._calculate_overall_status(
                performance_score, reliability_score, data_quality.quality_score,
                engagement_score, critical_alerts, warning_alerts
            )
            
            # Create health metrics
            health_metrics = SystemHealthMetrics(
                timestamp=datetime.now().isoformat(),
                overall_status=overall_status,
                component_status={
                    'model_drift': 'healthy' if not drift_alerts else 'warning',
                    'data_quality': 'healthy' if data_quality.quality_score >= 0.8 else 'degraded',
                    'system_performance': 'healthy' if performance_score >= 0.8 else 'degraded',
                    'reliability': 'healthy' if reliability_score >= 0.9 else 'degraded',
                    'user_engagement': 'healthy' if engagement_score >= 0.6 else 'warning'
                },
                performance_score=performance_score,
                reliability_score=reliability_score,
                data_quality_score=data_quality.quality_score,
                model_accuracy_score=0.8,  # Would be calculated from actual model performance
                user_engagement_score=engagement_score,
                critical_alerts=critical_alerts,
                warning_alerts=warning_alerts,
                uptime_percentage=99.9,  # Would be calculated from actual uptime
                last_failure=None  # Would be retrieved from failure logs
            )
            
            # Log health metrics
            await self._log_health_metrics(health_metrics)
            
            # Send alerts if necessary
            await self._send_health_alerts(health_metrics)
            
            logger.info(f"Health check completed: {overall_status}")
            return health_metrics
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return None
    
    async def _check_model_drift(self) -> List[ModelDriftMetrics]:
        """Check for model drift across all models"""
        drift_alerts = []
        
        # List of models to check
        models = ['ai_risk_model', 'layoff_risk_model', 'income_risk_model']
        
        for model in models:
            drift_metrics = await self.drift_detector.detect_model_drift(model)
            if drift_metrics:
                drift_alerts.append(drift_metrics)
        
        return drift_alerts
    
    async def _check_system_performance(self) -> float:
        """Check overall system performance"""
        try:
            # Get recent performance metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT AVG(value) as avg_performance
                FROM risk_performance_metrics 
                WHERE metric_type = 'risk_pipeline'
                AND timestamp >= datetime('now', '-1 hour')
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                # Normalize performance score (assuming lower values are better)
                performance_score = max(0, 1 - (result[0] / 5.0))  # 5 seconds max
                return min(1.0, performance_score)
            
            return 0.8  # Default score
            
        except Exception as e:
            logger.error(f"Error checking system performance: {e}")
            return 0.5
    
    async def _check_system_reliability(self) -> float:
        """Check system reliability"""
        try:
            # Get recent error rates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status = 'FAIL' THEN 1 END) as failed_requests
                FROM risk_performance_metrics 
                WHERE timestamp >= datetime('now', '-24 hours')
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                error_rate = result[1] / result[0]
                reliability_score = max(0, 1 - (error_rate * 10))  # 10% error rate = 0 score
                return min(1.0, reliability_score)
            
            return 0.9  # Default score
            
        except Exception as e:
            logger.error(f"Error checking system reliability: {e}")
            return 0.5
    
    async def _check_user_engagement(self) -> float:
        """Check user engagement levels"""
        try:
            # Get recent user engagement data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM risk_assessments 
                WHERE assessment_timestamp >= datetime('now', '-7 days')
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                # Simple engagement score based on active users
                active_users = result[0]
                engagement_score = min(1.0, active_users / 100)  # 100 users = max score
                return engagement_score
            
            return 0.6  # Default score
            
        except Exception as e:
            logger.error(f"Error checking user engagement: {e}")
            return 0.5
    
    async def _count_alerts(self) -> Tuple[int, int]:
        """Count critical and warning alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN severity = 'HIGH' OR severity = 'WARNING' THEN 1 END) as warning_alerts
                FROM risk_system_alerts 
                WHERE resolved = FALSE
                AND created_at >= datetime('now', '-24 hours')
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] or 0, result[1] or 0
            
        except Exception as e:
            logger.error(f"Error counting alerts: {e}")
            return 0, 0
    
    def _calculate_overall_status(self, performance_score: float, reliability_score: float,
                                data_quality_score: float, engagement_score: float,
                                critical_alerts: int, warning_alerts: int) -> str:
        """Calculate overall system health status"""
        # Check for critical conditions
        if critical_alerts > self.health_thresholds['max_critical_alerts']:
            return HealthStatus.CRITICAL.value
        
        if (performance_score < 0.5 or reliability_score < 0.5 or 
            data_quality_score < 0.5):
            return HealthStatus.CRITICAL.value
        
        # Check for warning conditions
        if (critical_alerts > 0 or warning_alerts > self.health_thresholds['max_warning_alerts'] or
            performance_score < self.health_thresholds['min_performance_score'] or
            reliability_score < self.health_thresholds['min_reliability_score'] or
            data_quality_score < self.health_thresholds['min_data_quality_score']):
            return HealthStatus.WARNING.value
        
        # Check for degraded conditions
        if (engagement_score < self.health_thresholds['min_user_engagement_score'] or
            performance_score < 0.7 or reliability_score < 0.8):
            return HealthStatus.DEGRADED.value
        
        return HealthStatus.HEALTHY.value
    
    async def _log_health_metrics(self, health_metrics: SystemHealthMetrics):
        """Log health metrics to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create health metrics table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    component_status TEXT NOT NULL,
                    performance_score REAL NOT NULL,
                    reliability_score REAL NOT NULL,
                    data_quality_score REAL NOT NULL,
                    model_accuracy_score REAL NOT NULL,
                    user_engagement_score REAL NOT NULL,
                    critical_alerts INTEGER NOT NULL,
                    warning_alerts INTEGER NOT NULL,
                    uptime_percentage REAL NOT NULL,
                    last_failure TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO system_health_metrics (
                    timestamp, overall_status, component_status, performance_score,
                    reliability_score, data_quality_score, model_accuracy_score,
                    user_engagement_score, critical_alerts, warning_alerts,
                    uptime_percentage, last_failure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                health_metrics.timestamp, health_metrics.overall_status,
                json.dumps(health_metrics.component_status), health_metrics.performance_score,
                health_metrics.reliability_score, health_metrics.data_quality_score,
                health_metrics.model_accuracy_score, health_metrics.user_engagement_score,
                health_metrics.critical_alerts, health_metrics.warning_alerts,
                health_metrics.uptime_percentage, health_metrics.last_failure
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging health metrics: {e}")
    
    async def _send_health_alerts(self, health_metrics: SystemHealthMetrics):
        """Send health alerts if necessary"""
        if health_metrics.overall_status in ['critical', 'failed']:
            logger.critical(f"CRITICAL HEALTH ALERT: System status is {health_metrics.overall_status}")
            # Here you would send critical alerts (email, Slack, PagerDuty, etc.)
        
        elif health_metrics.overall_status == 'warning':
            logger.warning(f"HEALTH WARNING: System status is {health_metrics.overall_status}")
            # Here you would send warning alerts
    
    async def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get health summary for specified time period"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    overall_status,
                    performance_score,
                    reliability_score,
                    data_quality_score,
                    user_engagement_score,
                    critical_alerts,
                    warning_alerts
                FROM system_health_metrics 
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            '''.format(hours))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {'error': 'No health data available'}
            
            # Calculate summary statistics
            statuses = [r[0] for r in results]
            performance_scores = [r[1] for r in results]
            reliability_scores = [r[2] for r in results]
            data_quality_scores = [r[3] for r in results]
            engagement_scores = [r[4] for r in results]
            critical_alerts = [r[5] for r in results]
            warning_alerts = [r[6] for r in results]
            
            return {
                'analysis_period_hours': hours,
                'total_checks': len(results),
                'current_status': statuses[0],
                'status_distribution': {
                    'healthy': statuses.count('healthy'),
                    'warning': statuses.count('warning'),
                    'degraded': statuses.count('degraded'),
                    'critical': statuses.count('critical'),
                    'failed': statuses.count('failed')
                },
                'average_scores': {
                    'performance': round(statistics.mean(performance_scores), 3),
                    'reliability': round(statistics.mean(reliability_scores), 3),
                    'data_quality': round(statistics.mean(data_quality_scores), 3),
                    'user_engagement': round(statistics.mean(engagement_scores), 3)
                },
                'alert_summary': {
                    'max_critical_alerts': max(critical_alerts),
                    'max_warning_alerts': max(warning_alerts),
                    'total_critical_alerts': sum(critical_alerts),
                    'total_warning_alerts': sum(warning_alerts)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {'error': str(e)}

# Example usage and testing
async def main():
    """Example usage of RiskSystemHealthMonitor"""
    config = {
        'database_path': 'risk_health.db'
    }
    
    monitor = RiskSystemHealthMonitor(config)
    
    # Run single health check
    print("Running health check...")
    health_metrics = await monitor.run_health_check()
    if health_metrics:
        print(f"System status: {health_metrics.overall_status}")
        print(f"Performance score: {health_metrics.performance_score:.3f}")
        print(f"Reliability score: {health_metrics.reliability_score:.3f}")
        print(f"Data quality score: {health_metrics.data_quality_score:.3f}")
        print(f"Critical alerts: {health_metrics.critical_alerts}")
        print(f"Warning alerts: {health_metrics.warning_alerts}")
    
    # Get health summary
    print("\nGetting health summary...")
    summary = await monitor.get_health_summary(hours=24)
    print(f"Health summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())
