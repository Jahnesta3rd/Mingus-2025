"""
Advanced Job Security Prediction Pipeline
Main ML pipeline for training and deploying job security prediction models
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

from .models.company_predictor import CompanyPredictor
from .models.industry_predictor import IndustryPredictor
from .models.geographic_predictor import GeographicPredictor
from .models.personal_risk_predictor import PersonalRiskPredictor
from .utils.feature_engineering import FeatureEngineer
from .utils.model_monitoring import ModelMonitor
from .utils.explainability import ModelExplainer

logger = logging.getLogger(__name__)

class JobSecurityPredictor:
    """
    Main ML pipeline for job security predictions
    Implements ensemble methods, feature engineering, and model monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the job security predictor
        
        Args:
            config: Configuration dictionary for model parameters
        """
        self.config = config or self._get_default_config()
        self.feature_engineer = FeatureEngineer()
        self.model_monitor = ModelMonitor()
        self.explainer = ModelExplainer()
        
        # Initialize prediction models
        self.company_predictor = CompanyPredictor()
        self.industry_predictor = IndustryPredictor()
        self.geographic_predictor = GeographicPredictor()
        self.personal_risk_predictor = PersonalRiskPredictor()
        
        # Model storage
        self.models = {}
        self.scalers = {}
        self.feature_names = {}
        self.model_metadata = {}
        
        # Performance tracking
        self.performance_history = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the ML pipeline"""
        return {
            'test_size': 0.2,
            'random_state': 42,
            'n_estimators': 100,
            'max_depth': 10,
            'learning_rate': 0.1,
            'feature_selection_k': 20,
            'cross_validation_folds': 5,
            'ensemble_methods': ['random_forest', 'gradient_boosting', 'logistic_regression'],
            'prediction_horizon': 6,  # months
            'retrain_frequency': 30,  # days
            'performance_threshold': 0.75  # minimum AUC score
        }
    
    def prepare_data(self, warn_data: pd.DataFrame, economic_data: pd.DataFrame, 
                    company_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare and preprocess data for model training
        
        Args:
            warn_data: WARN notice data
            economic_data: Economic indicators data
            company_data: Company financial and operational data
            
        Returns:
            Tuple of (features, target) DataFrames
        """
        logger.info("Preparing data for model training...")
        
        # Merge datasets
        merged_data = self._merge_datasets(warn_data, economic_data, company_data)
        
        # Feature engineering
        features = self.feature_engineer.create_features(merged_data)
        
        # Create target variable (layoff within 6 months)
        target = self._create_target_variable(merged_data)
        
        # Handle missing values
        features = self._handle_missing_values(features)
        
        # Feature selection
        features = self._select_features(features, target)
        
        logger.info(f"Data preparation complete. Features: {features.shape}, Target: {target.shape}")
        
        return features, target
    
    def _merge_datasets(self, warn_data: pd.DataFrame, economic_data: pd.DataFrame, 
                       company_data: pd.DataFrame) -> pd.DataFrame:
        """Merge different data sources"""
        # Implementation for merging datasets
        # This would include joining on company IDs, dates, etc.
        merged = warn_data.copy()
        
        # Add economic indicators
        if not economic_data.empty:
            merged = merged.merge(economic_data, on='date', how='left')
        
        # Add company data
        if not company_data.empty:
            merged = merged.merge(company_data, on='company_id', how='left')
        
        return merged
    
    def _create_target_variable(self, data: pd.DataFrame) -> pd.Series:
        """Create binary target variable for layoff prediction"""
        # Create target: 1 if layoff occurs within 6 months, 0 otherwise
        target = (data['layoff_date'] - data['warn_date']).dt.days <= 180
        return target.astype(int)
    
    def _handle_missing_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features"""
        # Fill numeric columns with median
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        features[numeric_cols] = features[numeric_cols].fillna(features[numeric_cols].median())
        
        # Fill categorical columns with mode
        categorical_cols = features.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            features[col] = features[col].fillna(features[col].mode()[0] if len(features[col].mode()) > 0 else 'Unknown')
        
        return features
    
    def _select_features(self, features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """Select most important features using statistical tests"""
        k = self.config['feature_selection_k']
        
        # Select numeric features for feature selection
        numeric_features = features.select_dtypes(include=[np.number])
        
        if len(numeric_features.columns) > k:
            selector = SelectKBest(score_func=f_classif, k=k)
            selected_features = selector.fit_transform(numeric_features, target)
            selected_feature_names = numeric_features.columns[selector.get_support()]
            
            # Combine selected numeric features with categorical features
            categorical_features = features.select_dtypes(include=['object'])
            final_features = pd.concat([
                pd.DataFrame(selected_features, columns=selected_feature_names),
                categorical_features
            ], axis=1)
            
            return final_features
        
        return features
    
    def train_models(self, features: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
        """
        Train ensemble of prediction models
        
        Args:
            features: Feature matrix
            target: Target variable
            
        Returns:
            Dictionary containing trained models and performance metrics
        """
        logger.info("Training ensemble models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, 
            test_size=self.config['test_size'],
            random_state=self.config['random_state'],
            stratify=target
        )
        
        # Encode categorical variables
        X_train_encoded, X_test_encoded, encoders = self._encode_categorical_features(X_train, X_test)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_encoded)
        X_test_scaled = scaler.transform(X_test_encoded)
        
        # Store scaler and feature names
        self.scalers['main'] = scaler
        self.feature_names['main'] = X_train_encoded.columns.tolist()
        
        # Train ensemble models
        models = {}
        performance_metrics = {}
        
        for method in self.config['ensemble_methods']:
            model = self._train_single_model(method, X_train_scaled, y_train)
            models[method] = model
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            
            metrics = {
                'accuracy': (y_pred == y_test).mean(),
                'auc': roc_auc_score(y_test, y_pred_proba),
                'classification_report': classification_report(y_test, y_pred, output_dict=True)
            }
            
            performance_metrics[method] = metrics
            logger.info(f"{method} - AUC: {metrics['auc']:.3f}, Accuracy: {metrics['accuracy']:.3f}")
        
        # Store models and metadata
        self.models = models
        self.model_metadata = {
            'training_date': datetime.now().isoformat(),
            'feature_count': len(self.feature_names['main']),
            'sample_count': len(X_train),
            'performance_metrics': performance_metrics,
            'encoders': encoders
        }
        
        # Update performance history
        self.performance_history.append({
            'date': datetime.now().isoformat(),
            'metrics': performance_metrics
        })
        
        # Monitor model performance
        self.model_monitor.update_performance(performance_metrics)
        
        return {
            'models': models,
            'performance_metrics': performance_metrics,
            'feature_names': self.feature_names['main'],
            'metadata': self.model_metadata
        }
    
    def _encode_categorical_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Encode categorical features"""
        encoders = {}
        X_train_encoded = X_train.copy()
        X_test_encoded = X_test.copy()
        
        categorical_cols = X_train.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            le = LabelEncoder()
            X_train_encoded[col] = le.fit_transform(X_train_encoded[col].astype(str))
            X_test_encoded[col] = le.transform(X_test_encoded[col].astype(str))
            encoders[col] = le
        
        return X_train_encoded, X_test_encoded, encoders
    
    def _train_single_model(self, method: str, X_train: np.ndarray, y_train: np.ndarray):
        """Train a single model based on the specified method"""
        if method == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=self.config['n_estimators'],
                max_depth=self.config['max_depth'],
                random_state=self.config['random_state']
            )
        elif method == 'gradient_boosting':
            model = GradientBoostingClassifier(
                n_estimators=self.config['n_estimators'],
                max_depth=self.config['max_depth'],
                learning_rate=self.config['learning_rate'],
                random_state=self.config['random_state']
            )
        elif method == 'logistic_regression':
            model = LogisticRegression(
                random_state=self.config['random_state'],
                max_iter=1000
            )
        else:
            raise ValueError(f"Unknown model method: {method}")
        
        model.fit(X_train, y_train)
        return model
    
    def predict(self, company_data: Dict[str, Any], user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make comprehensive job security predictions
        
        Args:
            company_data: Company information and metrics
            user_data: User-specific information (optional)
            
        Returns:
            Dictionary containing various prediction results
        """
        logger.info("Making job security predictions...")
        
        predictions = {}
        
        # Company-level predictions
        company_risk = self.company_predictor.predict(company_data)
        predictions['company_risk'] = company_risk
        
        # Industry-level predictions
        industry_risk = self.industry_predictor.predict(company_data.get('industry'))
        predictions['industry_risk'] = industry_risk
        
        # Geographic predictions
        geographic_risk = self.geographic_predictor.predict(company_data.get('location'))
        predictions['geographic_risk'] = geographic_risk
        
        # Personal risk predictions (if user data provided)
        if user_data:
            personal_risk = self.personal_risk_predictor.predict(user_data, company_data)
            predictions['personal_risk'] = personal_risk
        
        # Ensemble prediction using main models
        ensemble_prediction = self._make_ensemble_prediction(company_data)
        predictions['ensemble_prediction'] = ensemble_prediction
        
        # Calculate overall risk score
        overall_risk = self._calculate_overall_risk(predictions)
        predictions['overall_risk'] = overall_risk
        
        # Generate explanations
        explanations = self.explainer.explain_predictions(predictions, company_data)
        predictions['explanations'] = explanations
        
        return predictions
    
    def _make_ensemble_prediction(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using ensemble of trained models"""
        if not self.models:
            return {'error': 'Models not trained yet'}
        
        # Prepare features for prediction
        features = self.feature_engineer.create_prediction_features(company_data)
        
        # Encode and scale features
        features_encoded = self._encode_prediction_features(features)
        features_scaled = self.scalers['main'].transform(features_encoded)
        
        # Make predictions with all models
        predictions = {}
        probabilities = {}
        
        for method, model in self.models.items():
            try:
                proba = model.predict_proba(features_scaled)[0, 1]
                pred = model.predict(features_scaled)[0]
                
                predictions[method] = pred
                probabilities[method] = proba
            except Exception as e:
                logger.error(f"Error making prediction with {method}: {e}")
                predictions[method] = None
                probabilities[method] = None
        
        # Calculate ensemble probability (weighted average)
        valid_probs = [p for p in probabilities.values() if p is not None]
        if valid_probs:
            ensemble_probability = np.mean(valid_probs)
            ensemble_prediction = 1 if ensemble_probability > 0.5 else 0
        else:
            ensemble_probability = 0.5
            ensemble_prediction = 0
        
        return {
            'prediction': ensemble_prediction,
            'probability': ensemble_probability,
            'individual_predictions': predictions,
            'individual_probabilities': probabilities,
            'confidence': self._calculate_confidence(probabilities)
        }
    
    def _encode_prediction_features(self, features: pd.DataFrame) -> np.ndarray:
        """Encode features for prediction"""
        # This would use the encoders from training
        # For now, return features as-is
        return features.select_dtypes(include=[np.number]).values
    
    def _calculate_confidence(self, probabilities: Dict[str, float]) -> float:
        """Calculate confidence based on agreement between models"""
        valid_probs = [p for p in probabilities.values() if p is not None]
        if len(valid_probs) < 2:
            return 0.5
        
        # Calculate standard deviation of probabilities
        std_dev = np.std(valid_probs)
        # Convert to confidence (lower std dev = higher confidence)
        confidence = max(0, 1 - std_dev)
        return confidence
    
    def _calculate_overall_risk(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score combining all predictions"""
        risk_factors = []
        
        # Company risk
        if 'company_risk' in predictions:
            risk_factors.append(predictions['company_risk'].get('risk_score', 0.5))
        
        # Industry risk
        if 'industry_risk' in predictions:
            risk_factors.append(predictions['industry_risk'].get('risk_score', 0.5))
        
        # Geographic risk
        if 'geographic_risk' in predictions:
            risk_factors.append(predictions['geographic_risk'].get('risk_score', 0.5))
        
        # Personal risk
        if 'personal_risk' in predictions:
            risk_factors.append(predictions['personal_risk'].get('risk_score', 0.5))
        
        # Ensemble prediction
        if 'ensemble_prediction' in predictions:
            ensemble_prob = predictions['ensemble_prediction'].get('probability', 0.5)
            risk_factors.append(ensemble_prob)
        
        # Calculate weighted average
        if risk_factors:
            weights = [0.3, 0.2, 0.15, 0.15, 0.2]  # Adjust weights as needed
            weights = weights[:len(risk_factors)]
            weights = [w/sum(weights) for w in weights]  # Normalize
            
            overall_risk = sum(r * w for r, w in zip(risk_factors, weights))
        else:
            overall_risk = 0.5
        
        # Categorize risk level
        if overall_risk < 0.3:
            risk_level = 'Low'
        elif overall_risk < 0.6:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
        
        return {
            'risk_score': overall_risk,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'confidence': predictions.get('ensemble_prediction', {}).get('confidence', 0.5)
        }
    
    def save_models(self, filepath: str):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'feature_names': self.feature_names,
            'model_metadata': self.model_metadata,
            'performance_history': self.performance_history
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk"""
        model_data = joblib.load(filepath)
        
        self.models = model_data['models']
        self.scalers = model_data['scalers']
        self.feature_names = model_data['feature_names']
        self.model_metadata = model_data['model_metadata']
        self.performance_history = model_data.get('performance_history', [])
        
        logger.info(f"Models loaded from {filepath}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics"""
        if not self.model_metadata:
            return {'error': 'No models trained yet'}
        
        return {
            'current_performance': self.model_metadata['performance_metrics'],
            'performance_history': self.performance_history,
            'model_metadata': self.model_metadata
        }
    
    def retrain_if_needed(self, new_data: pd.DataFrame) -> bool:
        """Check if retraining is needed and retrain if necessary"""
        if not self.performance_history:
            return False
        
        # Check if performance has degraded
        latest_performance = self.performance_history[-1]['metrics']
        avg_auc = np.mean([metrics['auc'] for metrics in latest_performance.values()])
        
        if avg_auc < self.config['performance_threshold']:
            logger.info("Performance below threshold, retraining models...")
            # This would trigger retraining with new data
            return True
        
        return False 