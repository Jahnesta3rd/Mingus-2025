#!/usr/bin/env python3
"""
Risk Predictive Analytics for Career Protection System

This module provides predictive analytics capabilities for forecasting career risks,
identifying emerging risk patterns, and generating proactive insights for career
protection interventions.

Features:
- Industry risk trend forecasting
- Emerging risk factor detection
- Individual user risk trajectory prediction
- Market risk heat map generation
- Predictive model accuracy tracking
- Automated risk pattern analysis
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    import pandas as pd
    import warnings
    warnings.filterwarnings('ignore')
except ImportError:
    # Fallback for testing without sklearn/pandas
    print("Warning: sklearn/pandas not available. Some features will be limited.")
    np = None
    RandomForestRegressor = None
    IsolationForest = None
    LinearRegression = None
    StandardScaler = None
    pd = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RiskForecast:
    """Data class for risk forecast"""
    forecast_type: str
    target_entity: str
    forecast_horizon_days: int
    risk_probability: float
    confidence_level: float
    forecast_data: Dict[str, Any]
    model_version: str = "1.0"
    created_by: str = "system"

@dataclass
class RiskPattern:
    """Data class for detected risk pattern"""
    pattern_type: str
    pattern_description: str
    affected_users: List[str]
    risk_factors: Dict[str, Any]
    severity_score: float
    detection_confidence: float
    first_detected: datetime
    last_updated: datetime

class RiskPredictiveAnalytics:
    """
    Predictive analytics system for career risk forecasting and pattern detection.
    
    Provides advanced machine learning capabilities for predicting career risks,
    identifying emerging patterns, and generating actionable insights for
    proactive career protection.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the risk predictive analytics system"""
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self._init_database()
        self._init_models()
        logger.info("RiskPredictiveAnalytics initialized successfully")
    
    def _init_database(self):
        """Initialize the analytics database with required tables for risk forecasting."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Try to read the schema file, fallback to basic tables if not available
            try:
                with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
                    schema_sql = f.read()
                cursor.executescript(schema_sql)
            except FileNotFoundError:
                # Create basic tables if schema file not found
                self._create_basic_tables(cursor)
            
            conn.commit()
            conn.close()
            logger.info("Risk predictive analytics database schema ensured.")

        except Exception as e:
            logger.error(f"Error initializing risk predictive analytics database: {e}")
            # Try to create basic tables as fallback
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                self._create_basic_tables(cursor)
                conn.commit()
                conn.close()
                logger.info("Created basic tables as fallback")
            except Exception as fallback_error:
                logger.error(f"Fallback table creation also failed: {fallback_error}")
                raise
    
    def _create_basic_tables(self, cursor):
        """Create basic tables for risk analytics if schema file is not available."""
        # Create user_risk_assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_factors TEXT,
                industry_risk_score REAL,
                company_risk_score REAL,
                role_risk_score REAL,
                market_risk_score REAL,
                personal_risk_score REAL,
                assessment_confidence REAL,
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_assessment_date TIMESTAMP,
                intervention_triggered BOOLEAN DEFAULT FALSE,
                intervention_date TIMESTAMP
            )
        ''')
        
        # Create risk_forecasts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                forecast_type TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                forecast_horizon_days INTEGER NOT NULL,
                risk_probability REAL NOT NULL,
                confidence_level REAL NOT NULL,
                forecast_data TEXT,
                actual_outcome TEXT,
                accuracy_score REAL,
                model_version TEXT DEFAULT '1.0',
                created_by TEXT DEFAULT 'system'
            )
        ''')
        
        # Create risk_interventions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_assessment_id INTEGER NOT NULL,
                intervention_type TEXT NOT NULL,
                intervention_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                intervention_status TEXT DEFAULT 'triggered',
                intervention_data TEXT,
                success_metrics TEXT,
                completion_date TIMESTAMP,
                effectiveness_score REAL,
                user_response TEXT
            )
        ''')
        
        # Create career_protection_outcomes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS career_protection_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_assessment_id INTEGER NOT NULL,
                intervention_id INTEGER,
                outcome_type TEXT NOT NULL,
                outcome_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                outcome_details TEXT,
                salary_change REAL,
                job_security_improvement REAL,
                time_to_new_role INTEGER,
                satisfaction_score INTEGER,
                would_recommend BOOLEAN,
                success_factors TEXT,
                verification_status TEXT DEFAULT 'unverified',
                verified_date TIMESTAMP
            )
        ''')
        
        # Create risk_success_stories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_success_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                story_type TEXT NOT NULL,
                story_title TEXT NOT NULL,
                story_description TEXT NOT NULL,
                original_risk_factors TEXT,
                intervention_timeline TEXT,
                outcome_details TEXT,
                user_satisfaction INTEGER,
                would_recommend BOOLEAN,
                testimonial_text TEXT,
                approval_status TEXT DEFAULT 'pending',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_date TIMESTAMP,
                featured BOOLEAN DEFAULT FALSE
            )
        ''')
    
    def _init_models(self):
        """Initialize predictive models"""
        try:
            if RandomForestRegressor is None:
                logger.warning("ML libraries not available. Using simplified models.")
                # Use simple fallback models
                self.models['industry_risk'] = None
                self.models['user_risk'] = None
                self.models['anomaly_detection'] = None
                self.models['market_risk'] = None
                self.scalers['industry_risk'] = None
                self.scalers['user_risk'] = None
                self.scalers['market_risk'] = None
                return
            
            # Industry risk forecasting model
            self.models['industry_risk'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # User risk trajectory model
            self.models['user_risk'] = RandomForestRegressor(
                n_estimators=50,
                max_depth=8,
                random_state=42
            )
            
            # Anomaly detection for emerging risk patterns
            self.models['anomaly_detection'] = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Market risk prediction model
            self.models['market_risk'] = LinearRegression()
            
            # Initialize scalers
            self.scalers['industry_risk'] = StandardScaler()
            self.scalers['user_risk'] = StandardScaler()
            self.scalers['market_risk'] = StandardScaler()
            
            logger.info("Predictive models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing predictive models: {e}")
            # Set models to None for graceful degradation
            self.models = {key: None for key in self.models.keys()}
            self.scalers = {key: None for key in self.scalers.keys()}
    
    def generate_risk_forecasts(
        self,
        forecast_type: str,
        target_entities: List[str],
        forecast_horizon_days: int = 30
    ) -> List[RiskForecast]:
        """
        Generate risk forecasts for specified entities
        
        Args:
            forecast_type: Type of forecast (industry_risk, market_risk, user_risk)
            target_entities: List of entities to forecast (industries, companies, users)
            forecast_horizon_days: Forecast horizon in days
            
        Returns:
            List of RiskForecast objects
        """
        try:
            forecasts = []
            
            for entity in target_entities:
                if forecast_type == 'industry_risk':
                    forecast = self._forecast_industry_risk(entity, forecast_horizon_days)
                elif forecast_type == 'market_risk':
                    forecast = self._forecast_market_risk(entity, forecast_horizon_days)
                elif forecast_type == 'user_risk':
                    forecast = self._forecast_user_risk(entity, forecast_horizon_days)
                else:
                    continue
                
                if forecast:
                    forecasts.append(forecast)
                    self._save_forecast(forecast)
            
            logger.info(f"Generated {len(forecasts)} {forecast_type} forecasts")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating risk forecasts: {e}")
            return []
    
    def identify_emerging_risk_factors(
        self,
        analysis_period_days: int = 30
    ) -> List[RiskPattern]:
        """
        Identify emerging risk factors and patterns
        
        Args:
            analysis_period_days: Period to analyze for emerging patterns
            
        Returns:
            List of detected risk patterns
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=analysis_period_days)
            
            # Get recent risk assessments
            cursor.execute('''
                SELECT user_id, risk_factors, risk_score, assessment_date
                FROM user_risk_assessments 
                WHERE assessment_date >= ? AND risk_level IN ('high', 'critical')
                ORDER BY assessment_date DESC
            ''', (start_date,))
            
            risk_data = []
            for row in cursor.fetchall():
                risk_factors = json.loads(row[1]) if row[1] else {}
                risk_data.append({
                    'user_id': row[0],
                    'risk_factors': risk_factors,
                    'risk_score': row[2],
                    'assessment_date': row[3]
                })
            
            conn.close()
            
            if len(risk_data) < 10:
                logger.warning("Insufficient data for pattern detection")
                return []
            
            # Detect emerging patterns
            patterns = self._detect_risk_patterns(risk_data)
            
            # Save detected patterns
            for pattern in patterns:
                self._save_risk_pattern(pattern)
            
            logger.info(f"Identified {len(patterns)} emerging risk patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying emerging risk factors: {e}")
            return []
    
    def predict_user_risk_trajectory(
        self,
        user_id: str,
        forecast_horizon_days: int = 90
    ) -> Optional[Dict[str, Any]]:
        """
        Predict individual user risk trajectory
        
        Args:
            user_id: User identifier
            forecast_horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary containing risk trajectory prediction
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's historical risk data
            cursor.execute('''
                SELECT assessment_date, risk_score, risk_level, risk_factors
                FROM user_risk_assessments 
                WHERE user_id = ?
                ORDER BY assessment_date DESC
                LIMIT 20
            ''', (user_id,))
            
            historical_data = []
            for row in cursor.fetchall():
                risk_factors = json.loads(row[3]) if row[3] else {}
                historical_data.append({
                    'date': row[0],
                    'risk_score': row[1],
                    'risk_level': row[2],
                    'risk_factors': risk_factors
                })
            
            conn.close()
            
            if len(historical_data) < 3:
                logger.warning(f"Insufficient historical data for user {user_id}")
                return None
            
            # Prepare features for prediction
            features = self._prepare_user_features(historical_data)
            
            # Make prediction
            risk_trajectory = self._predict_user_risk_trajectory(features, forecast_horizon_days)
            
            return risk_trajectory
            
        except Exception as e:
            logger.error(f"Error predicting user risk trajectory: {e}")
            return None
    
    def generate_market_risk_heat_map(
        self,
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate market risk heat map data
        
        Args:
            analysis_period_days: Period to analyze for risk mapping
            
        Returns:
            Dictionary containing heat map data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=analysis_period_days)
            
            # Get risk data by industry and geography
            cursor.execute('''
                SELECT 
                    json_extract(risk_factors, '$.industry') as industry,
                    json_extract(risk_factors, '$.location') as location,
                    AVG(risk_score) as avg_risk_score,
                    COUNT(*) as user_count
                FROM user_risk_assessments 
                WHERE assessment_date >= ? AND risk_level IN ('high', 'critical')
                GROUP BY industry, location
                HAVING industry IS NOT NULL AND location IS NOT NULL
            ''', (start_date,))
            
            heat_map_data = []
            for row in cursor.fetchall():
                heat_map_data.append({
                    'industry': row[0],
                    'location': row[1],
                    'risk_score': round(row[2], 2),
                    'user_count': row[3]
                })
            
            conn.close()
            
            # Generate heat map visualization data
            heat_map = self._generate_heat_map_visualization(heat_map_data)
            
            return {
                'analysis_period_days': analysis_period_days,
                'heat_map_data': heat_map_data,
                'visualization': heat_map,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating market risk heat map: {e}")
            return {}
    
    def get_forecast_accuracy_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get forecast accuracy metrics
        
        Args:
            days: Number of days to analyze for accuracy
            
        Returns:
            Dictionary containing accuracy metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get forecasts with actual outcomes
            cursor.execute('''
                SELECT 
                    forecast_type,
                    target_entity,
                    risk_probability,
                    actual_outcome,
                    accuracy_score,
                    forecast_date
                FROM risk_forecasts 
                WHERE forecast_date >= ? AND actual_outcome IS NOT NULL
                ORDER BY forecast_date DESC
            ''', (start_date,))
            
            forecasts = cursor.fetchall()
            
            if not forecasts:
                return {'error': 'No forecast data available for accuracy analysis'}
            
            # Calculate accuracy metrics by forecast type
            accuracy_metrics = {}
            for forecast_type in ['industry_risk', 'market_risk', 'user_risk']:
                type_forecasts = [f for f in forecasts if f[0] == forecast_type]
                if type_forecasts:
                    accuracy_scores = [f[4] for f in type_forecasts if f[4] is not None]
                    if accuracy_scores:
                        accuracy_metrics[forecast_type] = {
                            'total_forecasts': len(type_forecasts),
                            'avg_accuracy': round(np.mean(accuracy_scores), 3),
                            'min_accuracy': round(np.min(accuracy_scores), 3),
                            'max_accuracy': round(np.max(accuracy_scores), 3),
                            'std_accuracy': round(np.std(accuracy_scores), 3)
                        }
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'total_forecasts': len(forecasts),
                'accuracy_by_type': accuracy_metrics,
                'overall_accuracy': round(np.mean([f[4] for f in forecasts if f[4] is not None]), 3)
            }
            
        except Exception as e:
            logger.error(f"Error getting forecast accuracy metrics: {e}")
            return {}
    
    def _forecast_industry_risk(
        self,
        industry: str,
        forecast_horizon_days: int
    ) -> Optional[RiskForecast]:
        """Forecast industry-specific risk"""
        try:
            # Get historical industry risk data
            historical_data = self._get_industry_historical_data(industry)
            
            if len(historical_data) < 10:
                logger.warning(f"Insufficient data for industry {industry}")
                return None
            
            # Prepare features
            features = self._prepare_industry_features(historical_data)
            
            # Train model if needed
            if not hasattr(self.models['industry_risk'], 'feature_importances_'):
                self._train_industry_model(features)
            
            # Make prediction
            risk_probability = self._predict_industry_risk(features, forecast_horizon_days)
            confidence_level = self._calculate_confidence_level(features, 'industry_risk')
            
            forecast_data = {
                'industry': industry,
                'forecast_horizon_days': forecast_horizon_days,
                'historical_trend': historical_data[-10:],  # Last 10 data points
                'prediction_confidence': confidence_level,
                'key_factors': self._get_key_risk_factors(industry)
            }
            
            return RiskForecast(
                forecast_type='industry_risk',
                target_entity=industry,
                forecast_horizon_days=forecast_horizon_days,
                risk_probability=risk_probability,
                confidence_level=confidence_level,
                forecast_data=forecast_data
            )
            
        except Exception as e:
            logger.error(f"Error forecasting industry risk for {industry}: {e}")
            return None
    
    def _forecast_market_risk(
        self,
        market: str,
        forecast_horizon_days: int
    ) -> Optional[RiskForecast]:
        """Forecast market-wide risk"""
        try:
            # Get historical market data
            historical_data = self._get_market_historical_data(market)
            
            if len(historical_data) < 10:
                logger.warning(f"Insufficient data for market {market}")
                return None
            
            # Prepare features
            features = self._prepare_market_features(historical_data)
            
            # Train model if needed
            if not hasattr(self.models['market_risk'], 'coef_'):
                self._train_market_model(features)
            
            # Make prediction
            risk_probability = self._predict_market_risk(features, forecast_horizon_days)
            confidence_level = self._calculate_confidence_level(features, 'market_risk')
            
            forecast_data = {
                'market': market,
                'forecast_horizon_days': forecast_horizon_days,
                'historical_trend': historical_data[-10:],
                'prediction_confidence': confidence_level,
                'market_indicators': self._get_market_indicators(market)
            }
            
            return RiskForecast(
                forecast_type='market_risk',
                target_entity=market,
                forecast_horizon_days=forecast_horizon_days,
                risk_probability=risk_probability,
                confidence_level=confidence_level,
                forecast_data=forecast_data
            )
            
        except Exception as e:
            logger.error(f"Error forecasting market risk for {market}: {e}")
            return None
    
    def _forecast_user_risk(
        self,
        user_id: str,
        forecast_horizon_days: int
    ) -> Optional[RiskForecast]:
        """Forecast individual user risk"""
        try:
            # Get user historical data
            historical_data = self._get_user_historical_data(user_id)
            
            if len(historical_data) < 5:
                logger.warning(f"Insufficient data for user {user_id}")
                return None
            
            # Prepare features
            features = self._prepare_user_features(historical_data)
            
            # Train model if needed
            if not hasattr(self.models['user_risk'], 'feature_importances_'):
                self._train_user_model(features)
            
            # Make prediction
            risk_probability = self._predict_user_risk(features, forecast_horizon_days)
            confidence_level = self._calculate_confidence_level(features, 'user_risk')
            
            forecast_data = {
                'user_id': user_id,
                'forecast_horizon_days': forecast_horizon_days,
                'historical_trend': historical_data[-5:],
                'prediction_confidence': confidence_level,
                'personal_risk_factors': self._get_personal_risk_factors(user_id)
            }
            
            return RiskForecast(
                forecast_type='user_risk',
                target_entity=user_id,
                forecast_horizon_days=forecast_horizon_days,
                risk_probability=risk_probability,
                confidence_level=confidence_level,
                forecast_data=forecast_data
            )
            
        except Exception as e:
            logger.error(f"Error forecasting user risk for {user_id}: {e}")
            return None
    
    def _detect_risk_patterns(self, risk_data: List[Dict[str, Any]]) -> List[RiskPattern]:
        """Detect emerging risk patterns in data"""
        try:
            patterns = []
            
            # Extract risk factors for analysis
            risk_factors_matrix = []
            for data in risk_data:
                factors = data['risk_factors']
                # Convert risk factors to numerical features
                feature_vector = self._extract_risk_factor_features(factors)
                risk_factors_matrix.append(feature_vector)
            
            if len(risk_factors_matrix) < 10:
                return patterns
            
            # Detect anomalies using isolation forest
            anomaly_scores = self.models['anomaly_detection'].fit_predict(risk_factors_matrix)
            
            # Identify clusters of similar risk patterns
            anomaly_indices = [i for i, score in enumerate(anomaly_scores) if score == -1]
            
            if len(anomaly_indices) >= 3:  # Minimum cluster size
                # Group anomalies by similar patterns
                anomaly_data = [risk_data[i] for i in anomaly_indices]
                
                # Extract common risk factors
                common_factors = self._extract_common_risk_factors(anomaly_data)
                
                pattern = RiskPattern(
                    pattern_type='emerging_risk_cluster',
                    pattern_description=f"Emerging risk pattern affecting {len(anomaly_data)} users",
                    affected_users=[data['user_id'] for data in anomaly_data],
                    risk_factors=common_factors,
                    severity_score=np.mean([data['risk_score'] for data in anomaly_data]),
                    detection_confidence=0.8,  # Based on cluster size and similarity
                    first_detected=datetime.now(),
                    last_updated=datetime.now()
                )
                
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting risk patterns: {e}")
            return []
    
    def _get_industry_historical_data(self, industry: str) -> List[Dict[str, Any]]:
        """Get historical risk data for industry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT assessment_date, risk_score, risk_level
            FROM user_risk_assessments 
            WHERE json_extract(risk_factors, '$.industry') = ?
            ORDER BY assessment_date DESC
            LIMIT 100
        ''', (industry,))
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'date': row[0],
                'risk_score': row[1],
                'risk_level': row[2]
            })
        
        conn.close()
        return data
    
    def _get_market_historical_data(self, market: str) -> List[Dict[str, Any]]:
        """Get historical market risk data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT assessment_date, AVG(risk_score) as avg_risk_score
            FROM user_risk_assessments 
            WHERE json_extract(risk_factors, '$.location') = ?
            GROUP BY DATE(assessment_date)
            ORDER BY assessment_date DESC
            LIMIT 100
        ''', (market,))
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'date': row[0],
                'avg_risk_score': row[1]
            })
        
        conn.close()
        return data
    
    def _get_user_historical_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get historical risk data for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT assessment_date, risk_score, risk_level, risk_factors
            FROM user_risk_assessments 
            WHERE user_id = ?
            ORDER BY assessment_date DESC
            LIMIT 50
        ''', (user_id,))
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'date': row[0],
                'risk_score': row[1],
                'risk_level': row[2],
                'risk_factors': json.loads(row[3]) if row[3] else {}
            })
        
        conn.close()
        return data
    
    def _prepare_industry_features(self, historical_data: List[Dict[str, Any]]):
        """Prepare features for industry risk prediction"""
        if pd is None or np is None:
            # Fallback: return simple features
            return np.array([[0, 0, 0, 0, 0]] * len(historical_data))
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create time-based features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['risk_score_lag1'] = df['risk_score'].shift(1)
        df['risk_score_lag7'] = df['risk_score'].shift(7)
        df['risk_score_ma7'] = df['risk_score'].rolling(window=7).mean()
        df['risk_score_std7'] = df['risk_score'].rolling(window=7).std()
        
        # Select features
        feature_columns = ['days_since_start', 'risk_score_lag1', 'risk_score_lag7', 
                          'risk_score_ma7', 'risk_score_std7']
        
        features = df[feature_columns].fillna(0).values
        
        return features
    
    def _prepare_market_features(self, historical_data: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare features for market risk prediction"""
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create time-based features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['risk_score_lag1'] = df['avg_risk_score'].shift(1)
        df['risk_score_lag7'] = df['avg_risk_score'].shift(7)
        df['risk_score_ma7'] = df['avg_risk_score'].rolling(window=7).mean()
        df['risk_score_trend'] = df['avg_risk_score'].diff()
        
        feature_columns = ['days_since_start', 'risk_score_lag1', 'risk_score_lag7', 
                          'risk_score_ma7', 'risk_score_trend']
        
        features = df[feature_columns].fillna(0).values
        
        return features
    
    def _prepare_user_features(self, historical_data: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare features for user risk prediction"""
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create time-based features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['risk_score_lag1'] = df['risk_score'].shift(1)
        df['risk_score_trend'] = df['risk_score'].diff()
        df['risk_score_ma3'] = df['risk_score'].rolling(window=3).mean()
        
        # Extract risk factor features
        risk_factor_features = self._extract_risk_factor_features_from_list(
            df['risk_factors'].tolist()
        )
        
        # Combine features
        time_features = df[['days_since_start', 'risk_score_lag1', 'risk_score_trend', 'risk_score_ma3']].fillna(0).values
        features = np.hstack([time_features, risk_factor_features])
        
        return features
    
    def _extract_risk_factor_features(self, risk_factors: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from risk factors"""
        # Common risk factors to track
        factor_keys = [
            'industry_volatility', 'company_financial_trouble', 'role_redundancy',
            'limited_skills', 'age_discrimination_risk', 'location_risk',
            'company_layoffs', 'role_automation_risk', 'industry_downsizing'
        ]
        
        features = []
        for key in factor_keys:
            if key in risk_factors and risk_factors[key]:
                features.append(1.0)
            else:
                features.append(0.0)
        
        return np.array(features)
    
    def _extract_risk_factor_features_from_list(self, risk_factors_list: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from list of risk factors"""
        features_list = []
        for risk_factors in risk_factors_list:
            features = self._extract_risk_factor_features(risk_factors)
            features_list.append(features)
        
        return np.array(features_list)
    
    def _extract_common_risk_factors(self, anomaly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common risk factors from anomaly data"""
        all_factors = [data['risk_factors'] for data in anomaly_data]
        
        common_factors = {}
        factor_keys = [
            'industry_volatility', 'company_financial_trouble', 'role_redundancy',
            'limited_skills', 'age_discrimination_risk', 'location_risk'
        ]
        
        for key in factor_keys:
            count = sum(1 for factors in all_factors if factors.get(key, False))
            if count >= len(all_factors) * 0.5:  # Present in at least 50% of cases
                common_factors[key] = True
                common_factors[f"{key}_frequency"] = count / len(all_factors)
        
        return common_factors
    
    def _train_industry_model(self, features: np.ndarray):
        """Train industry risk prediction model"""
        if len(features) < 10:
            return
        
        # Use last 20% for validation
        split_idx = int(len(features) * 0.8)
        X_train = features[:split_idx]
        y_train = features[:split_idx, 0]  # Use first feature as target
        
        # Scale features
        X_train_scaled = self.scalers['industry_risk'].fit_transform(X_train)
        
        # Train model
        self.models['industry_risk'].fit(X_train_scaled, y_train)
    
    def _train_market_model(self, features: np.ndarray):
        """Train market risk prediction model"""
        if len(features) < 10:
            return
        
        split_idx = int(len(features) * 0.8)
        X_train = features[:split_idx]
        y_train = features[:split_idx, 0]
        
        X_train_scaled = self.scalers['market_risk'].fit_transform(X_train)
        self.models['market_risk'].fit(X_train_scaled, y_train)
    
    def _train_user_model(self, features: np.ndarray):
        """Train user risk prediction model"""
        if len(features) < 5:
            return
        
        split_idx = int(len(features) * 0.8)
        X_train = features[:split_idx]
        y_train = features[:split_idx, 0]
        
        X_train_scaled = self.scalers['user_risk'].fit_transform(X_train)
        self.models['user_risk'].fit(X_train_scaled, y_train)
    
    def _predict_industry_risk(self, features: np.ndarray, horizon_days: int) -> float:
        """Predict industry risk probability"""
        if not hasattr(self.models['industry_risk'], 'feature_importances_'):
            return 0.5  # Default probability
        
        # Use most recent features
        recent_features = features[-1:].reshape(1, -1)
        recent_features_scaled = self.scalers['industry_risk'].transform(recent_features)
        
        prediction = self.models['industry_risk'].predict(recent_features_scaled)[0]
        
        # Convert to probability (0-1)
        return min(max(prediction / 100.0, 0.0), 1.0)
    
    def _predict_market_risk(self, features: np.ndarray, horizon_days: int) -> float:
        """Predict market risk probability"""
        if not hasattr(self.models['market_risk'], 'coef_'):
            return 0.5
        
        recent_features = features[-1:].reshape(1, -1)
        recent_features_scaled = self.scalers['market_risk'].transform(recent_features)
        
        prediction = self.models['market_risk'].predict(recent_features_scaled)[0]
        return min(max(prediction / 100.0, 0.0), 1.0)
    
    def _predict_user_risk(self, features: np.ndarray, horizon_days: int) -> float:
        """Predict user risk probability"""
        if not hasattr(self.models['user_risk'], 'feature_importances_'):
            return 0.5
        
        recent_features = features[-1:].reshape(1, -1)
        recent_features_scaled = self.scalers['user_risk'].transform(recent_features)
        
        prediction = self.models['user_risk'].predict(recent_features_scaled)[0]
        return min(max(prediction / 100.0, 0.0), 1.0)
    
    def _predict_user_risk_trajectory(self, features: np.ndarray, horizon_days: int) -> Dict[str, Any]:
        """Predict user risk trajectory over time"""
        if not hasattr(self.models['user_risk'], 'feature_importances_'):
            return {'error': 'Model not trained'}
        
        # Generate trajectory points
        trajectory = []
        for i in range(0, horizon_days, 7):  # Weekly predictions
            # Extrapolate features for future time points
            future_features = features[-1:].copy()
            future_features[0, 0] += i  # Update days_since_start
            
            future_features_scaled = self.scalers['user_risk'].transform(future_features)
            risk_probability = self.models['user_risk'].predict(future_features_scaled)[0]
            
            trajectory.append({
                'days_ahead': i,
                'risk_probability': min(max(risk_probability / 100.0, 0.0), 1.0),
                'risk_level': self._risk_score_to_level(risk_probability)
            })
        
        return {
            'trajectory': trajectory,
            'trend': self._calculate_trajectory_trend(trajectory),
            'peak_risk': max(trajectory, key=lambda x: x['risk_probability']),
            'forecast_horizon_days': horizon_days
        }
    
    def _calculate_confidence_level(self, features: np.ndarray, model_type: str) -> float:
        """Calculate confidence level for prediction"""
        # Simple confidence based on data availability and variance
        data_points = len(features)
        variance = np.var(features[:, 0]) if len(features) > 0 else 1.0
        
        # More data points and lower variance = higher confidence
        confidence = min(1.0, (data_points / 50.0) * (1.0 / (1.0 + variance)))
        return max(0.1, confidence)  # Minimum 10% confidence
    
    def _risk_score_to_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_trajectory_trend(self, trajectory: List[Dict[str, Any]]) -> str:
        """Calculate trend direction for risk trajectory"""
        if len(trajectory) < 2:
            return 'stable'
        
        first_risk = trajectory[0]['risk_probability']
        last_risk = trajectory[-1]['risk_probability']
        
        if last_risk > first_risk + 0.1:
            return 'increasing'
        elif last_risk < first_risk - 0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_heat_map_visualization(self, heat_map_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate heat map visualization data"""
        if not heat_map_data:
            return {}
        
        # Group by industry and location
        industries = list(set(item['industry'] for item in heat_map_data))
        locations = list(set(item['location'] for item in heat_map_data))
        
        # Create matrix
        matrix = []
        for industry in industries:
            row = []
            for location in locations:
                # Find matching data point
                matching_data = next(
                    (item for item in heat_map_data 
                     if item['industry'] == industry and item['location'] == location),
                    None
                )
                if matching_data:
                    row.append(matching_data['risk_score'])
                else:
                    row.append(0)
            matrix.append(row)
        
        return {
            'industries': industries,
            'locations': locations,
            'matrix': matrix,
            'max_risk': max(item['risk_score'] for item in heat_map_data),
            'min_risk': min(item['risk_score'] for item in heat_map_data)
        }
    
    def _get_key_risk_factors(self, industry: str) -> List[str]:
        """Get key risk factors for industry"""
        # This would typically come from external data sources
        # For now, return common industry risk factors
        return [
            'market_volatility',
            'regulatory_changes',
            'technological_disruption',
            'economic_conditions'
        ]
    
    def _get_market_indicators(self, market: str) -> Dict[str, Any]:
        """Get market indicators for risk assessment"""
        # This would typically come from external data sources
        return {
            'unemployment_rate': 5.2,
            'gdp_growth': 2.1,
            'inflation_rate': 3.1,
            'market_volatility': 0.15
        }
    
    def _get_personal_risk_factors(self, user_id: str) -> List[str]:
        """Get personal risk factors for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT risk_factors
            FROM user_risk_assessments 
            WHERE user_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            risk_factors = json.loads(result[0])
            return [key for key, value in risk_factors.items() if value]
        
        return []
    
    def _save_forecast(self, forecast: RiskForecast):
        """Save forecast to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_forecasts (
                    forecast_type, target_entity, forecast_horizon_days,
                    risk_probability, confidence_level, forecast_data,
                    model_version, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                forecast.forecast_type, forecast.target_entity, forecast.forecast_horizon_days,
                forecast.risk_probability, forecast.confidence_level, json.dumps(forecast.forecast_data),
                forecast.model_version, forecast.created_by
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving forecast: {e}")
    
    def _save_risk_pattern(self, pattern: RiskPattern):
        """Save detected risk pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # For now, just log the pattern
            # In a full implementation, this would be saved to a patterns table
            logger.info(f"Risk pattern detected: {pattern.pattern_type} - {pattern.pattern_description}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving risk pattern: {e}")
