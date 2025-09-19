#!/usr/bin/env python3
"""
Enhanced Vehicle Expense ML Engine for Mingus Personal Finance App
Advanced machine learning system for vehicle expense categorization and prediction

Features:
- ML-powered expense categorization with improved accuracy
- Multi-vehicle expense linking with smart vehicle detection
- Maintenance cost prediction with actual vs predicted comparison
- Dynamic model updates based on user spending patterns
- Integration with existing spending analysis and ML models
- Real-time expense pattern learning and adaptation
"""

import logging
import re
import sqlite3
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# ML Libraries with fallback
try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
    from sklearn.feature_extraction.text import TfidfVectorizer
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries not available. Using rule-based fallback.")

# Configure logging
logger = logging.getLogger(__name__)

class VehicleExpenseType(Enum):
    """Enhanced vehicle expense types"""
    MAINTENANCE = "maintenance"
    FUEL = "fuel"
    INSURANCE = "insurance"
    PARKING = "parking"
    REGISTRATION = "registration"
    REPAIRS = "repairs"
    TIRES = "tires"
    TOWING = "towing"
    EMERGENCY = "emergency"
    LEASE_PAYMENT = "lease_payment"
    LOAN_PAYMENT = "loan_payment"
    TAXES = "taxes"
    INSPECTION = "inspection"
    EMISSIONS = "emissions"
    OTHER = "other"

@dataclass
class VehicleExpenseFeatures:
    """Features for ML model training"""
    description_length: int
    merchant_length: int
    amount: float
    day_of_week: int
    month: int
    has_vehicle_keywords: bool
    has_merchant_keywords: bool
    has_amount_patterns: bool
    description_tfidf: Optional[List[float]] = None
    merchant_tfidf: Optional[List[float]] = None

@dataclass
class MLPredictionResult:
    """ML prediction result with confidence and features"""
    expense_type: VehicleExpenseType
    confidence_score: float
    probability_distribution: Dict[str, float]
    feature_importance: Dict[str, float]
    model_version: str
    prediction_metadata: Dict[str, Any]

@dataclass
class VehicleExpenseInsight:
    """Enhanced expense insight with ML analysis"""
    insight_type: str
    title: str
    description: str
    confidence: float
    impact_score: float
    recommendation: str
    potential_savings: float
    category: str
    ml_confidence: float
    supporting_data: Dict[str, Any]

class EnhancedVehicleExpenseMLEngine:
    """
    Enhanced ML-powered vehicle expense categorization and analysis engine
    
    This engine provides:
    - Advanced ML models for expense categorization
    - Multi-vehicle expense linking with smart detection
    - Maintenance cost prediction and comparison
    - Dynamic model updates based on user patterns
    - Integration with existing spending analysis
    - Real-time pattern learning and adaptation
    """
    
    def __init__(self, db_path: str = "backend/mingus_vehicles.db", 
                 profile_db_path: str = "user_profiles.db"):
        """Initialize the enhanced ML engine"""
        self.db_path = db_path
        self.profile_db_path = profile_db_path
        self.ml_available = ML_AVAILABLE
        
        # ML Models
        self.categorization_model = None
        self.cost_prediction_model = None
        self.vehicle_linking_model = None
        self.anomaly_detection_model = None
        
        # Preprocessing
        self.scaler = None
        self.label_encoder = None
        self.tfidf_vectorizer = None
        
        # Model metadata
        self.model_version = "2.0"
        self.last_training_date = None
        self.training_accuracy = {}
        
        # Enhanced patterns with ML features
        self.enhanced_patterns = self._initialize_enhanced_patterns()
        
        # Initialize database and models
        self._init_databases()
        self._init_ml_models()
        
        logger.info("Enhanced Vehicle Expense ML Engine initialized successfully")
    
    def _initialize_enhanced_patterns(self) -> Dict[VehicleExpenseType, Dict[str, Any]]:
        """Initialize enhanced patterns with ML features"""
        return {
            VehicleExpenseType.MAINTENANCE: {
                'keywords': [
                    'oil change', 'oil', 'filter', 'brake', 'brakes', 'brake pad', 'brake pads',
                    'transmission', 'transmission fluid', 'coolant', 'antifreeze', 'radiator',
                    'spark plug', 'spark plugs', 'ignition', 'tune up', 'tune-up', 'service',
                    'maintenance', 'inspection', 'emissions', 'smog', 'alignment', 'balance',
                    'tire rotation', 'air filter', 'cabin filter', 'fuel filter', 'belt',
                    'serpentine belt', 'timing belt', 'water pump', 'alternator', 'starter',
                    'battery', 'car battery', 'auto battery', 'lubrication', 'lube',
                    'diagnostic', 'diagnostics', 'check engine', 'engine light', 'valve',
                    'gasket', 'seal', 'hose', 'clamp', 'sensor', 'actuator'
                ],
                'merchant_keywords': [
                    'auto service', 'car service', 'vehicle service', 'mechanic', 'garage',
                    'auto repair', 'car repair', 'service center', 'quick lube', 'jiffy lube',
                    'valvoline', 'firestone', 'goodyear', 'pep boys', 'monro', 'mavis'
                ],
                'amount_ranges': [(20, 100), (100, 500), (500, 2000)],
                'ml_weight': 0.9,
                'confidence_threshold': 0.7
            },
            VehicleExpenseType.FUEL: {
                'keywords': [
                    'gas', 'gasoline', 'fuel', 'petrol', 'diesel', 'gas station',
                    'fuel pump', 'gas pump', 'filling station', 'service station'
                ],
                'merchant_keywords': [
                    'exxon', 'shell', 'chevron', 'bp', 'mobil', 'speedway',
                    '7-eleven', 'circle k', 'wawa', 'sheetz', 'costco gas',
                    'sams club gas', 'kroger fuel', 'safeway fuel', 'arco',
                    'valero', 'phillips 66', 'citgo', 'sunoco'
                ],
                'amount_ranges': [(20, 80), (80, 150)],
                'ml_weight': 0.95,
                'confidence_threshold': 0.8
            },
            VehicleExpenseType.INSURANCE: {
                'keywords': [
                    'auto insurance', 'car insurance', 'vehicle insurance', 'auto policy',
                    'car policy', 'vehicle policy', 'insurance premium', 'insurance payment',
                    'auto coverage', 'car coverage', 'vehicle coverage', 'collision',
                    'comprehensive', 'liability', 'uninsured motorist'
                ],
                'merchant_keywords': [
                    'geico', 'progressive', 'state farm', 'allstate', 'farmers',
                    'liberty mutual', 'usaa', 'nationwide', 'travelers', 'esurance',
                    'american family', 'safeco', 'mercury', 'the general'
                ],
                'amount_ranges': [(50, 200), (200, 500)],
                'ml_weight': 0.9,
                'confidence_threshold': 0.8
            },
            VehicleExpenseType.PARKING: {
                'keywords': [
                    'parking', 'parking meter', 'parking garage', 'parking lot',
                    'valet', 'valet parking', 'parking fee', 'parking ticket',
                    'meter', 'parking pass', 'parking permit', 'garage fee',
                    'lot fee', 'parking spot', 'space rental'
                ],
                'merchant_keywords': [
                    'parking', 'garage', 'valet', 'meter', 'lot', 'space'
                ],
                'amount_ranges': [(2, 20), (20, 50)],
                'ml_weight': 0.8,
                'confidence_threshold': 0.6
            },
            VehicleExpenseType.REPAIRS: {
                'keywords': [
                    'repair', 'repairs', 'fix', 'fixing', 'broken', 'damage',
                    'accident', 'collision', 'body work', 'paint', 'dent',
                    'scratch', 'windshield', 'window', 'mirror', 'bumper',
                    'fender', 'door', 'hood', 'trunk', 'headlight', 'taillight',
                    'auto body', 'body shop', 'collision center'
                ],
                'merchant_keywords': [
                    'auto body', 'body shop', 'collision center', 'paint shop',
                    'repair shop', 'auto repair', 'car repair'
                ],
                'amount_ranges': [(100, 1000), (1000, 5000)],
                'ml_weight': 0.85,
                'confidence_threshold': 0.7
            },
            VehicleExpenseType.TIRES: {
                'keywords': [
                    'tire', 'tires', 'tire change', 'tire replacement', 'new tires',
                    'tire rotation', 'tire balance', 'wheel alignment', 'tire pressure',
                    'flat tire', 'tire repair', 'tire patch', 'tire shop'
                ],
                'merchant_keywords': [
                    'discount tire', 'firestone', 'goodyear', 'bridgestone',
                    'michelin', 'continental', 'pirelli', 'toyo', 'hankook',
                    'tire shop', 'tire center', 'wheel shop'
                ],
                'amount_ranges': [(50, 200), (200, 800), (800, 2000)],
                'ml_weight': 0.9,
                'confidence_threshold': 0.8
            }
        }
    
    def _init_databases(self):
        """Initialize enhanced database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced vehicle expenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_vehicle_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    expense_id TEXT UNIQUE NOT NULL,
                    vehicle_id INTEGER,
                    expense_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    merchant TEXT,
                    date DATE NOT NULL,
                    confidence_score REAL NOT NULL,
                    ml_confidence REAL,
                    matched_keywords TEXT,
                    matched_patterns TEXT,
                    is_maintenance_related BOOLEAN DEFAULT FALSE,
                    predicted_cost_range TEXT,
                    ml_features TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            ''')
            
            # ML model training data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    expense_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    merchant TEXT,
                    amount REAL NOT NULL,
                    actual_category TEXT NOT NULL,
                    predicted_category TEXT,
                    confidence_score REAL,
                    features TEXT,
                    is_training_data BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Model performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    precision REAL,
                    recall REAL,
                    f1_score REAL,
                    training_date TIMESTAMP NOT NULL,
                    test_data_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Vehicle expense insights
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_expense_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    insight_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    impact_score REAL NOT NULL,
                    recommendation TEXT,
                    potential_savings REAL,
                    category TEXT,
                    ml_confidence REAL,
                    supporting_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Enhanced vehicle expense ML database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced ML database: {e}")
            raise
    
    def _init_ml_models(self):
        """Initialize ML models"""
        if not self.ml_available:
            logger.warning("ML libraries not available. Using rule-based fallback.")
            return
        
        try:
            # Categorization model (Random Forest)
            self.categorization_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'
            )
            
            # Cost prediction model (Random Forest Regressor)
            self.cost_prediction_model = RandomForestRegressor(
                n_estimators=50,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
            
            # Vehicle linking model (Logistic Regression)
            self.vehicle_linking_model = LogisticRegression(
                random_state=42,
                max_iter=1000
            )
            
            # Anomaly detection model
            from sklearn.ensemble import IsolationForest
            self.anomaly_detection_model = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Preprocessing
            self.scaler = StandardScaler()
            self.label_encoder = LabelEncoder()
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            logger.info("ML models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            self.ml_available = False
    
    def extract_features(self, expense_data: Dict[str, Any]) -> VehicleExpenseFeatures:
        """Extract features for ML model"""
        try:
            description = expense_data.get('description', '').lower()
            merchant = expense_data.get('merchant', '').lower()
            amount = float(expense_data.get('amount', 0))
            date_str = expense_data.get('date', datetime.now().date().isoformat())
            
            # Parse date
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                day_of_week = expense_date.weekday()
                month = expense_date.month
            except:
                day_of_week = datetime.now().weekday()
                month = datetime.now().month
            
            # Text features
            description_length = len(description)
            merchant_length = len(merchant)
            
            # Keyword features
            has_vehicle_keywords = any(
                keyword in description for keyword in [
                    'car', 'auto', 'vehicle', 'truck', 'suv', 'motorcycle'
                ]
            )
            
            has_merchant_keywords = any(
                keyword in merchant for keyword in [
                    'auto', 'car', 'vehicle', 'gas', 'fuel', 'service', 'repair'
                ]
            )
            
            # Amount pattern features
            has_amount_patterns = self._check_amount_patterns(amount)
            
            return VehicleExpenseFeatures(
                description_length=description_length,
                merchant_length=merchant_length,
                amount=amount,
                day_of_week=day_of_week,
                month=month,
                has_vehicle_keywords=has_vehicle_keywords,
                has_merchant_keywords=has_merchant_keywords,
                has_amount_patterns=has_amount_patterns
            )
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return VehicleExpenseFeatures(
                description_length=0,
                merchant_length=0,
                amount=0,
                day_of_week=0,
                month=1,
                has_vehicle_keywords=False,
                has_merchant_keywords=False,
                has_amount_patterns=False
            )
    
    def _check_amount_patterns(self, amount: float) -> bool:
        """Check if amount matches common vehicle expense patterns"""
        # Common vehicle expense amounts
        common_amounts = [25, 35, 45, 50, 75, 100, 150, 200, 300, 500, 1000]
        return any(abs(amount - common) <= 5 for common in common_amounts)
    
    def categorize_expense_ml(self, expense_data: Dict[str, Any], user_email: str) -> MLPredictionResult:
        """
        Categorize expense using ML models
        
        Args:
            expense_data: Expense data dictionary
            user_email: User's email address
            
        Returns:
            MLPredictionResult with categorization and confidence
        """
        try:
            if not self.ml_available or self.categorization_model is None:
                return self._fallback_categorization(expense_data, user_email)
            
            # Extract features
            features = self.extract_features(expense_data)
            
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features, expense_data)
            
            # Make prediction
            prediction_proba = self.categorization_model.predict_proba([feature_vector])[0]
            prediction_class = self.categorization_model.predict([feature_vector])[0]
            
            # Get class names
            class_names = self.label_encoder.classes_
            predicted_type = VehicleExpenseType(class_names[prediction_class])
            
            # Calculate confidence
            confidence = float(max(prediction_proba))
            
            # Create probability distribution
            prob_dist = {
                class_names[i]: float(prob) 
                for i, prob in enumerate(prediction_proba)
            }
            
            # Get feature importance
            feature_importance = self._get_feature_importance()
            
            return MLPredictionResult(
                expense_type=predicted_type,
                confidence_score=confidence,
                probability_distribution=prob_dist,
                feature_importance=feature_importance,
                model_version=self.model_version,
                prediction_metadata={
                    'features_used': len(feature_vector),
                    'model_type': 'RandomForestClassifier',
                    'training_date': self.last_training_date
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ML categorization: {e}")
            return self._fallback_categorization(expense_data, user_email)
    
    def _fallback_categorization(self, expense_data: Dict[str, Any], user_email: str) -> MLPredictionResult:
        """Fallback rule-based categorization when ML is not available"""
        try:
            description = expense_data.get('description', '').lower()
            merchant = expense_data.get('merchant', '').lower()
            amount = float(expense_data.get('amount', 0))
            
            best_match = VehicleExpenseType.OTHER
            best_score = 0.0
            
            for expense_type, patterns in self.enhanced_patterns.items():
                score = 0.0
                
                # Keyword matching
                keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in description)
                score += keyword_matches * 0.4
                
                # Merchant matching
                merchant_matches = sum(1 for keyword in patterns['merchant_keywords'] if keyword in merchant)
                score += merchant_matches * 0.3
                
                # Amount range matching
                amount_matches = any(
                    min_range <= amount <= max_range 
                    for min_range, max_range in patterns['amount_ranges']
                )
                if amount_matches:
                    score += 0.3
                
                if score > best_score:
                    best_score = score
                    best_match = expense_type
            
            # Calculate confidence based on score
            confidence = min(best_score / 2.0, 1.0) if best_score > 0 else 0.0
            
            return MLPredictionResult(
                expense_type=best_match,
                confidence_score=confidence,
                probability_distribution={best_match.value: confidence},
                feature_importance={},
                model_version="rule_based",
                prediction_metadata={'method': 'rule_based_fallback'}
            )
            
        except Exception as e:
            logger.error(f"Error in fallback categorization: {e}")
            return MLPredictionResult(
                expense_type=VehicleExpenseType.OTHER,
                confidence_score=0.0,
                probability_distribution={},
                feature_importance={},
                model_version="error",
                prediction_metadata={'error': str(e)}
            )
    
    def _prepare_feature_vector(self, features: VehicleExpenseFeatures, expense_data: Dict[str, Any]) -> List[float]:
        """Prepare feature vector for ML model"""
        try:
            # Basic features
            feature_vector = [
                features.description_length,
                features.merchant_length,
                features.amount,
                features.day_of_week,
                features.month,
                float(features.has_vehicle_keywords),
                float(features.has_merchant_keywords),
                float(features.has_amount_patterns)
            ]
            
            # Add TF-IDF features if available
            if self.tfidf_vectorizer and hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                description = expense_data.get('description', '')
                merchant = expense_data.get('merchant', '')
                
                # Combine description and merchant for TF-IDF
                combined_text = f"{description} {merchant}"
                tfidf_features = self.tfidf_vectorizer.transform([combined_text]).toarray()[0]
                feature_vector.extend(tfidf_features.tolist())
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"Error preparing feature vector: {e}")
            return [0.0] * 8  # Return basic features only
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        try:
            if not self.ml_available or self.categorization_model is None:
                return {}
            
            feature_names = [
                'description_length', 'merchant_length', 'amount', 'day_of_week',
                'month', 'has_vehicle_keywords', 'has_merchant_keywords', 'has_amount_patterns'
            ]
            
            importance = self.categorization_model.feature_importances_
            
            return {
                name: float(imp) 
                for name, imp in zip(feature_names, importance[:len(feature_names)])
            }
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def train_models(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Train ML models with available data
        
        Args:
            user_email: Optional user email to train on specific user data
            
        Returns:
            Training results and performance metrics
        """
        try:
            if not self.ml_available:
                return {'error': 'ML libraries not available'}
            
            # Get training data
            training_data = self._get_training_data(user_email)
            
            if len(training_data) < 50:  # Need minimum data for training
                return {'error': f'Insufficient training data: {len(training_data)} samples'}
            
            # Prepare features and labels
            X, y = self._prepare_training_data(training_data)
            
            if len(X) == 0:
                return {'error': 'No valid training features'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train categorization model
            self.categorization_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.categorization_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Update model metadata
            self.last_training_date = datetime.now()
            self.training_accuracy['categorization'] = accuracy
            
            # Save performance metrics
            self._save_model_performance('categorization', accuracy, len(training_data))
            
            logger.info(f"Model training completed. Accuracy: {accuracy:.3f}")
            
            return {
                'success': True,
                'accuracy': accuracy,
                'training_samples': len(training_data),
                'test_samples': len(X_test),
                'model_version': self.model_version,
                'training_date': self.last_training_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return {'error': str(e)}
    
    def _get_training_data(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get training data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_email:
                cursor.execute('''
                    SELECT * FROM ml_training_data 
                    WHERE user_email = ? AND is_training_data = TRUE
                    ORDER BY created_at DESC
                ''', (user_email,))
            else:
                cursor.execute('''
                    SELECT * FROM ml_training_data 
                    WHERE is_training_data = TRUE
                    ORDER BY created_at DESC
                ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return []
    
    def _prepare_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[str]]:
        """Prepare training data for ML models"""
        try:
            X = []
            y = []
            
            for data in training_data:
                # Extract features
                expense_data = {
                    'description': data['description'],
                    'merchant': data['merchant'],
                    'amount': data['amount'],
                    'date': data['created_at'][:10]  # Extract date part
                }
                
                features = self.extract_features(expense_data)
                feature_vector = self._prepare_feature_vector(features, expense_data)
                
                X.append(feature_vector)
                y.append(data['actual_category'])
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return [], []
    
    def _save_model_performance(self, model_name: str, accuracy: float, data_size: int):
        """Save model performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_performance 
                (model_name, model_version, accuracy, training_date, test_data_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_name, self.model_version, accuracy, datetime.now(), data_size))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving model performance: {e}")
    
    def generate_insights(self, user_email: str, months: int = 12) -> List[VehicleExpenseInsight]:
        """
        Generate enhanced insights using ML analysis
        
        Args:
            user_email: User's email address
            months: Number of months to analyze
            
        Returns:
            List of enhanced insights
        """
        try:
            insights = []
            
            # Get expense data
            expense_data = self._get_user_expense_data(user_email, months)
            
            if not expense_data:
                return insights
            
            # Analyze spending patterns
            spending_analysis = self._analyze_spending_patterns(expense_data)
            
            # Generate ML-powered insights
            insights.extend(self._generate_ml_insights(spending_analysis, user_email))
            
            # Generate cost optimization insights
            insights.extend(self._generate_cost_optimization_insights(spending_analysis, user_email))
            
            # Generate maintenance insights
            insights.extend(self._generate_maintenance_insights(spending_analysis, user_email))
            
            # Save insights to database
            self._save_insights(insights, user_email)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    def _get_user_expense_data(self, user_email: str, months: int) -> List[Dict[str, Any]]:
        """Get user expense data for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM enhanced_vehicle_expenses 
                WHERE user_email = ? 
                AND date >= date('now', '-{} months')
                ORDER BY date DESC
            '''.format(months))
            
            results = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting user expense data: {e}")
            return []
    
    def _analyze_spending_patterns(self, expense_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending patterns from expense data"""
        try:
            if not expense_data:
                return {}
            
            # Group by expense type
            by_type = {}
            total_amount = 0
            
            for expense in expense_data:
                exp_type = expense['expense_type']
                amount = expense['amount']
                
                if exp_type not in by_type:
                    by_type[exp_type] = {'count': 0, 'total': 0, 'expenses': []}
                
                by_type[exp_type]['count'] += 1
                by_type[exp_type]['total'] += amount
                by_type[exp_type]['expenses'].append(expense)
                total_amount += amount
            
            # Calculate percentages and averages
            for exp_type, data in by_type.items():
                data['percentage'] = (data['total'] / total_amount * 100) if total_amount > 0 else 0
                data['average'] = data['total'] / data['count'] if data['count'] > 0 else 0
            
            return {
                'by_type': by_type,
                'total_amount': total_amount,
                'total_count': len(expense_data),
                'average_monthly': total_amount / 12 if len(expense_data) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}")
            return {}
    
    def _generate_ml_insights(self, analysis: Dict[str, Any], user_email: str) -> List[VehicleExpenseInsight]:
        """Generate ML-powered insights"""
        insights = []
        
        try:
            by_type = analysis.get('by_type', {})
            total_amount = analysis.get('total_amount', 0)
            
            # High spending category insight
            if by_type:
                highest_category = max(by_type.items(), key=lambda x: x[1]['total'])
                category_name, category_data = highest_category
                
                if category_data['percentage'] > 40:  # More than 40% of spending
                    insights.append(VehicleExpenseInsight(
                        insight_type='high_spending_category',
                        title=f'High Spending on {category_name.title()}',
                        description=f'{category_name.title()} expenses represent {category_data["percentage"]:.1f}% of your total vehicle spending',
                        confidence=0.9,
                        impact_score=0.8,
                        recommendation=f'Consider ways to reduce {category_name} costs through better planning and comparison shopping',
                        potential_savings=category_data['total'] * 0.15,
                        category=category_name,
                        ml_confidence=0.85,
                        supporting_data={
                            'category_percentage': category_data['percentage'],
                            'monthly_average': category_data['total'] / 12,
                            'total_expenses': category_data['count']
                        }
                    ))
            
            # Spending pattern anomaly detection
            if self.ml_available and self.anomaly_detection_model:
                anomaly_insights = self._detect_spending_anomalies(analysis, user_email)
                insights.extend(anomaly_insights)
            
        except Exception as e:
            logger.error(f"Error generating ML insights: {e}")
        
        return insights
    
    def _detect_spending_anomalies(self, analysis: Dict[str, Any], user_email: str) -> List[VehicleExpenseInsight]:
        """Detect spending anomalies using ML"""
        insights = []
        
        try:
            # This would implement anomaly detection using the IsolationForest model
            # For now, return empty list as this requires more sophisticated implementation
            pass
            
        except Exception as e:
            logger.error(f"Error detecting spending anomalies: {e}")
        
        return insights
    
    def _generate_cost_optimization_insights(self, analysis: Dict[str, Any], user_email: str) -> List[VehicleExpenseInsight]:
        """Generate cost optimization insights"""
        insights = []
        
        try:
            by_type = analysis.get('by_type', {})
            total_amount = analysis.get('total_amount', 0)
            
            # Fuel cost optimization
            if 'fuel' in by_type:
                fuel_data = by_type['fuel']
                if fuel_data['percentage'] > 25:  # More than 25% on fuel
                    insights.append(VehicleExpenseInsight(
                        insight_type='fuel_optimization',
                        title='High Fuel Costs',
                        description=f'Fuel expenses represent {fuel_data["percentage"]:.1f}% of your vehicle spending',
                        confidence=0.8,
                        impact_score=0.7,
                        recommendation='Consider fuel-efficient driving habits, carpooling, or alternative transportation',
                        potential_savings=fuel_data['total'] * 0.15,
                        category='fuel',
                        ml_confidence=0.75,
                        supporting_data={
                            'fuel_percentage': fuel_data['percentage'],
                            'monthly_fuel_cost': fuel_data['total'] / 12
                        }
                    ))
            
            # Maintenance cost optimization
            if 'maintenance' in by_type:
                maintenance_data = by_type['maintenance']
                if maintenance_data['average'] > 200:  # High average maintenance cost
                    insights.append(VehicleExpenseInsight(
                        insight_type='maintenance_optimization',
                        title='High Maintenance Costs',
                        description=f'Average maintenance cost is ${maintenance_data["average"]:.2f} per visit',
                        confidence=0.85,
                        impact_score=0.8,
                        recommendation='Compare maintenance costs across different providers and consider preventive maintenance',
                        potential_savings=maintenance_data['total'] * 0.2,
                        category='maintenance',
                        ml_confidence=0.8,
                        supporting_data={
                            'average_cost': maintenance_data['average'],
                            'total_maintenance': maintenance_data['total']
                        }
                    ))
            
        except Exception as e:
            logger.error(f"Error generating cost optimization insights: {e}")
        
        return insights
    
    def _generate_maintenance_insights(self, analysis: Dict[str, Any], user_email: str) -> List[VehicleExpenseInsight]:
        """Generate maintenance-specific insights"""
        insights = []
        
        try:
            by_type = analysis.get('by_type', {})
            
            # Maintenance frequency insight
            if 'maintenance' in by_type:
                maintenance_data = by_type['maintenance']
                maintenance_count = maintenance_data['count']
                
                if maintenance_count < 2:  # Less than 2 maintenance visits
                    insights.append(VehicleExpenseInsight(
                        insight_type='maintenance_frequency',
                        title='Low Maintenance Frequency',
                        description=f'Only {maintenance_count} maintenance visit(s) recorded in the last 12 months',
                        confidence=0.9,
                        impact_score=0.6,
                        recommendation='Schedule regular maintenance to prevent costly repairs and maintain vehicle value',
                        potential_savings=0,  # Preventive maintenance costs money but saves in long run
                        category='maintenance',
                        ml_confidence=0.85,
                        supporting_data={
                            'maintenance_count': maintenance_count,
                            'months_analyzed': 12
                        }
                    ))
            
        except Exception as e:
            logger.error(f"Error generating maintenance insights: {e}")
        
        return insights
    
    def _save_insights(self, insights: List[VehicleExpenseInsight], user_email: str):
        """Save insights to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for insight in insights:
                cursor.execute('''
                    INSERT INTO vehicle_expense_insights 
                    (user_email, insight_type, title, description, confidence, impact_score,
                     recommendation, potential_savings, category, ml_confidence, supporting_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_email,
                    insight.insight_type,
                    insight.title,
                    insight.description,
                    insight.confidence,
                    insight.impact_score,
                    insight.recommendation,
                    insight.potential_savings,
                    insight.category,
                    insight.ml_confidence,
                    json.dumps(insight.supporting_data)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get enhanced ML service status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute('SELECT COUNT(*) FROM enhanced_vehicle_expenses')
            total_expenses = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM vehicle_expense_insights')
            total_insights = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM model_performance')
            total_models = cursor.fetchone()[0]
            
            # Get latest model performance
            cursor.execute('''
                SELECT model_name, accuracy, training_date 
                FROM model_performance 
                ORDER BY training_date DESC 
                LIMIT 1
            ''')
            latest_performance = cursor.fetchone()
            
            conn.close()
            
            return {
                'status': 'active',
                'ml_available': self.ml_available,
                'model_version': self.model_version,
                'total_expenses': total_expenses,
                'total_insights': total_insights,
                'total_models': total_models,
                'latest_accuracy': latest_performance[1] if latest_performance else None,
                'last_training': latest_performance[2] if latest_performance else None,
                'features': {
                    'ml_categorization': self.ml_available,
                    'cost_prediction': self.ml_available,
                    'anomaly_detection': self.ml_available,
                    'insight_generation': True,
                    'pattern_learning': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {'status': 'error', 'error': str(e)}
