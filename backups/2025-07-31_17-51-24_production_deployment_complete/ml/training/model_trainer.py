"""
Automated Model Training Infrastructure
Handles model retraining, performance monitoring, and A/B testing
"""

import numpy as np
import pandas as pd
import joblib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import os
import shutil
from pathlib import Path

from ..job_security_predictor import JobSecurityPredictor
from .data_pipeline import DataPipeline
from .performance_monitor import PerformanceMonitor
from .model_versioning import ModelVersioning

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Automated model training infrastructure with:
    - Scheduled retraining on new data
    - Performance monitoring and alerting
    - A/B testing framework
    - Model versioning and rollback
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.data_pipeline = DataPipeline()
        self.performance_monitor = PerformanceMonitor()
        self.model_versioning = ModelVersioning()
        
        # Training state
        self.current_model = None
        self.training_history = []
        self.ab_test_results = {}
        
        # Create directories
        self._create_directories()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default training configuration"""
        return {
            'retrain_frequency_days': 30,
            'performance_threshold': 0.75,
            'ab_test_duration_days': 14,
            'model_storage_path': 'models/',
            'backup_path': 'models/backups/',
            'max_model_versions': 10,
            'training_data_min_size': 1000,
            'validation_split': 0.2,
            'cross_validation_folds': 5,
            'early_stopping_patience': 5,
            'hyperparameter_tuning': True,
            'feature_selection': True
        }
    
    def _create_directories(self):
        """Create necessary directories for model storage"""
        directories = [
            self.config['model_storage_path'],
            self.config['backup_path'],
            'models/experiments/',
            'models/ab_tests/',
            'logs/training/'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def train_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Train all job security prediction models
        
        Args:
            force_retrain: Force retraining even if not scheduled
            
        Returns:
            Training results and performance metrics
        """
        logger.info("Starting model training process...")
        
        # Check if retraining is needed
        if not force_retrain and not self._should_retrain():
            logger.info("Retraining not needed at this time")
            return {'status': 'skipped', 'reason': 'Not scheduled for retraining'}
        
        try:
            # Load and prepare data
            data = self.data_pipeline.load_training_data()
            
            if len(data) < self.config['training_data_min_size']:
                return {'error': f'Insufficient training data: {len(data)} samples'}
            
            # Initialize predictor
            predictor = JobSecurityPredictor(self.config)
            
            # Prepare features and targets
            features, targets = predictor.prepare_data(
                data['warn_data'],
                data['economic_data'],
                data['company_data']
            )
            
            # Train models
            training_results = predictor.train_models(features, targets)
            
            # Evaluate performance
            performance_metrics = self._evaluate_model_performance(predictor, features, targets)
            
            # Check if performance meets threshold
            if performance_metrics['overall_auc'] < self.config['performance_threshold']:
                logger.warning(f"Model performance below threshold: {performance_metrics['overall_auc']}")
                return {
                    'error': 'Model performance below threshold',
                    'performance': performance_metrics
                }
            
            # Save models
            model_path = self._save_models(predictor, training_results)
            
            # Update training history
            training_record = {
                'date': datetime.now().isoformat(),
                'performance': performance_metrics,
                'model_path': model_path,
                'data_size': len(features),
                'feature_count': len(features.columns)
            }
            self.training_history.append(training_record)
            
            # Update performance monitor
            self.performance_monitor.update_performance(performance_metrics)
            
            # Version control
            self.model_versioning.create_version(model_path, training_record)
            
            logger.info(f"Model training completed successfully. AUC: {performance_metrics['overall_auc']:.4f}")
            
            return {
                'status': 'success',
                'performance': performance_metrics,
                'model_path': model_path,
                'training_record': training_record
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {'error': f'Training failed: {str(e)}'}
    
    def _should_retrain(self) -> bool:
        """Check if models should be retrained based on schedule and performance"""
        if not self.training_history:
            return True
        
        last_training = datetime.fromisoformat(self.training_history[-1]['date'])
        days_since_training = (datetime.now() - last_training).days
        
        # Check schedule
        if days_since_training >= self.config['retrain_frequency_days']:
            return True
        
        # Check performance degradation
        if self.performance_monitor.has_performance_degraded():
            logger.info("Performance degradation detected, triggering retraining")
            return True
        
        return False
    
    def _evaluate_model_performance(self, predictor: JobSecurityPredictor, 
                                  features: pd.DataFrame, targets: pd.Series) -> Dict[str, Any]:
        """Evaluate model performance using cross-validation"""
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import roc_auc_score
        
        # Cross-validation AUC scores
        cv_scores = cross_val_score(
            predictor.models.get('random_forest', predictor.models.get('gradient_boosting')),
            features, targets,
            cv=self.config['cross_validation_folds'],
            scoring='roc_auc'
        )
        
        # Individual model performance
        model_performance = {}
        for method, model in predictor.models.items():
            try:
                cv_score = cross_val_score(model, features, targets, cv=3, scoring='roc_auc')
                model_performance[method] = {
                    'mean_auc': cv_score.mean(),
                    'std_auc': cv_score.std()
                }
            except Exception as e:
                logger.warning(f"Could not evaluate {method}: {e}")
                model_performance[method] = {'mean_auc': 0, 'std_auc': 0}
        
        return {
            'overall_auc': cv_scores.mean(),
            'overall_std': cv_scores.std(),
            'model_performance': model_performance,
            'cv_scores': cv_scores.tolist()
        }
    
    def _save_models(self, predictor: JobSecurityPredictor, training_results: Dict[str, Any]) -> str:
        """Save trained models with versioning"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"{self.config['model_storage_path']}models_{timestamp}.joblib"
        
        # Save models
        predictor.save_models(model_path)
        
        # Save training metadata
        metadata_path = model_path.replace('.joblib', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(training_results, f, indent=2)
        
        return model_path
    
    def start_ab_test(self, new_model_path: str, traffic_split: float = 0.1) -> str:
        """
        Start A/B test comparing new model with current model
        
        Args:
            new_model_path: Path to new model version
            traffic_split: Percentage of traffic to send to new model
            
        Returns:
            A/B test ID
        """
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        ab_test_config = {
            'test_id': test_id,
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=self.config['ab_test_duration_days'])).isoformat(),
            'new_model_path': new_model_path,
            'current_model_path': self._get_current_model_path(),
            'traffic_split': traffic_split,
            'status': 'active',
            'metrics': {
                'new_model_predictions': 0,
                'current_model_predictions': 0,
                'new_model_accuracy': 0,
                'current_model_accuracy': 0
            }
        }
        
        # Save A/B test configuration
        ab_test_path = f"{self.config['model_storage_path']}ab_tests/{test_id}.json"
        with open(ab_test_path, 'w') as f:
            json.dump(ab_test_config, f, indent=2)
        
        self.ab_test_results[test_id] = ab_test_config
        
        logger.info(f"A/B test started: {test_id}")
        return test_id
    
    def update_ab_test_metrics(self, test_id: str, model_type: str, 
                              prediction_count: int, accuracy: float):
        """Update A/B test metrics"""
        if test_id not in self.ab_test_results:
            logger.warning(f"A/B test {test_id} not found")
            return
        
        metrics = self.ab_test_results[test_id]['metrics']
        
        if model_type == 'new':
            metrics['new_model_predictions'] += prediction_count
            metrics['new_model_accuracy'] = accuracy
        else:
            metrics['current_model_predictions'] += prediction_count
            metrics['current_model_accuracy'] = accuracy
        
        # Update stored configuration
        ab_test_path = f"{self.config['model_storage_path']}ab_tests/{test_id}.json"
        with open(ab_test_path, 'w') as f:
            json.dump(self.ab_test_results[test_id], f, indent=2)
    
    def evaluate_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Evaluate A/B test results and determine winner"""
        if test_id not in self.ab_test_results:
            return {'error': f'A/B test {test_id} not found'}
        
        test_config = self.ab_test_results[test_id]
        
        # Check if test period has ended
        end_date = datetime.fromisoformat(test_config['end_date'])
        if datetime.now() < end_date:
            return {'error': 'A/B test period has not ended yet'}
        
        metrics = test_config['metrics']
        
        # Statistical significance test (simplified)
        new_accuracy = metrics['new_model_accuracy']
        current_accuracy = metrics['current_model_accuracy']
        
        # Determine winner
        if new_accuracy > current_accuracy + 0.02:  # 2% improvement threshold
            winner = 'new_model'
            recommendation = 'deploy_new_model'
        elif current_accuracy > new_accuracy + 0.02:
            winner = 'current_model'
            recommendation = 'keep_current_model'
        else:
            winner = 'tie'
            recommendation = 'continue_monitoring'
        
        # Update test status
        test_config['status'] = 'completed'
        test_config['winner'] = winner
        test_config['recommendation'] = recommendation
        
        # Save results
        ab_test_path = f"{self.config['model_storage_path']}ab_tests/{test_id}.json"
        with open(ab_test_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        logger.info(f"A/B test {test_id} completed. Winner: {winner}")
        
        return {
            'test_id': test_id,
            'winner': winner,
            'recommendation': recommendation,
            'metrics': metrics,
            'new_model_accuracy': new_accuracy,
            'current_model_accuracy': current_accuracy
        }
    
    def deploy_model(self, model_path: str) -> bool:
        """Deploy a new model version"""
        try:
            # Backup current model
            current_path = self._get_current_model_path()
            if current_path and os.path.exists(current_path):
                backup_path = f"{self.config['backup_path']}backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
                shutil.copy2(current_path, backup_path)
            
            # Deploy new model
            deployment_path = f"{self.config['model_storage_path']}current_model.joblib"
            shutil.copy2(model_path, deployment_path)
            
            # Update current model reference
            self.current_model = deployment_path
            
            logger.info(f"Model deployed successfully: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model deployment failed: {e}")
            return False
    
    def rollback_model(self) -> bool:
        """Rollback to previous model version"""
        try:
            # Get previous version
            previous_version = self.model_versioning.get_previous_version()
            if not previous_version:
                return False
            
            # Deploy previous version
            success = self.deploy_model(previous_version['model_path'])
            
            if success:
                logger.info(f"Model rolled back to version: {previous_version['version_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Model rollback failed: {e}")
            return False
    
    def _get_current_model_path(self) -> Optional[str]:
        """Get path to current deployed model"""
        current_path = f"{self.config['model_storage_path']}current_model.joblib"
        return current_path if os.path.exists(current_path) else None
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status and history"""
        return {
            'last_training': self.training_history[-1] if self.training_history else None,
            'training_history': self.training_history[-10:],  # Last 10 trainings
            'performance_trend': self.performance_monitor.get_performance_trend(),
            'active_ab_tests': [test for test in self.ab_test_results.values() if test['status'] == 'active'],
            'current_model_path': self._get_current_model_path()
        }
    
    def schedule_retraining(self, frequency_days: int = None):
        """Schedule automatic retraining"""
        if frequency_days:
            self.config['retrain_frequency_days'] = frequency_days
        
        logger.info(f"Retraining scheduled every {self.config['retrain_frequency_days']} days")
    
    def get_model_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive model performance dashboard data"""
        return {
            'current_performance': self.performance_monitor.get_current_performance(),
            'performance_history': self.performance_monitor.get_performance_history(),
            'training_history': self.training_history,
            'ab_test_results': self.ab_test_results,
            'model_versions': self.model_versioning.get_version_history(),
            'alerts': self.performance_monitor.get_alerts()
        } 