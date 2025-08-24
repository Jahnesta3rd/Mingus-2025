"""
Company-Level Job Security Predictor
Predicts 6-month layoff probability for specific companies
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CompanyPredictor:
    """
    Predicts company-level job security risk based on:
    - Financial metrics (revenue, profit margins, debt ratios)
    - Operational metrics (employee count, growth rate)
    - Market indicators (stock performance, industry trends)
    - WARN notice history
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
        # Risk thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
    
    def train(self, company_data: pd.DataFrame, warn_history: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the company predictor model
        
        Args:
            company_data: DataFrame with company financial and operational metrics
            warn_history: DataFrame with historical WARN notices
            
        Returns:
            Training results and performance metrics
        """
        logger.info("Training company predictor model...")
        
        # Prepare features
        features, targets = self._prepare_training_data(company_data, warn_history)
        
        if len(features) == 0:
            return {'error': 'Insufficient training data'}
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Store feature names
        self.feature_names = features.columns.tolist()
        self.is_trained = True
        
        logger.info(f"Company predictor trained - MSE: {mse:.4f}, R²: {r2:.4f}")
        
        return {
            'mse': mse,
            'r2': r2,
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
    
    def _prepare_training_data(self, company_data: pd.DataFrame, warn_history: pd.DataFrame) -> tuple:
        """Prepare features and targets for training"""
        # Merge company data with WARN history
        merged_data = company_data.merge(warn_history, on='company_id', how='left')
        
        # Create target variable (layoff probability)
        merged_data['layoff_occurred'] = merged_data['warn_date'].notna().astype(int)
        
        # Feature engineering
        features = self._create_company_features(merged_data)
        
        # Remove rows with missing data
        features = features.dropna()
        targets = merged_data.loc[features.index, 'layoff_occurred']
        
        return features, targets
    
    def _create_company_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features for company prediction"""
        features = pd.DataFrame()
        
        # Financial metrics
        if 'revenue' in data.columns:
            features['revenue_growth'] = data['revenue'].pct_change()
            features['revenue_volatility'] = data['revenue'].rolling(12).std()
        
        if 'profit_margin' in data.columns:
            features['profit_margin_trend'] = data['profit_margin'].rolling(6).mean()
            features['profit_margin_volatility'] = data['profit_margin'].rolling(12).std()
        
        if 'debt_to_equity' in data.columns:
            features['debt_ratio'] = data['debt_to_equity']
            features['debt_trend'] = data['debt_to_equity'].rolling(6).mean()
        
        # Operational metrics
        if 'employee_count' in data.columns:
            features['employee_growth'] = data['employee_count'].pct_change()
            features['employee_growth_rate'] = data['employee_count'].rolling(12).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
        
        # Market indicators
        if 'stock_price' in data.columns:
            features['stock_performance'] = data['stock_price'].pct_change(30)
            features['stock_volatility'] = data['stock_price'].rolling(30).std()
        
        # Industry context
        if 'industry_growth' in data.columns:
            features['industry_growth'] = data['industry_growth']
            features['industry_relative_performance'] = (
                data['revenue_growth'] - data['industry_growth']
            )
        
        # WARN history features
        features['warn_count_12m'] = data.groupby('company_id')['warn_date'].rolling(365).count().reset_index(0, drop=True)
        features['warn_count_24m'] = data.groupby('company_id')['warn_date'].rolling(730).count().reset_index(0, drop=True)
        features['days_since_last_warn'] = (
            data['date'] - data.groupby('company_id')['warn_date'].shift(1)
        ).dt.days
        
        # Fill missing values
        features = features.fillna(0)
        
        return features
    
    def predict(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict company-level job security risk
        
        Args:
            company_data: Dictionary containing company metrics
            
        Returns:
            Prediction results with risk score and analysis
        """
        if not self.is_trained:
            return {'error': 'Model not trained yet'}
        
        try:
            # Prepare features for prediction
            features = self._prepare_prediction_features(company_data)
            
            if features is None:
                return {'error': 'Unable to prepare features for prediction'}
            
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Make prediction
            risk_score = self.model.predict(features_scaled)[0]
            risk_score = max(0, min(1, risk_score))  # Clamp between 0 and 1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate insights
            insights = self._generate_company_insights(company_data, risk_score)
            
            # Feature importance for this prediction
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'layoff_probability_6m': risk_score,
                'insights': insights,
                'feature_importance': feature_importance,
                'confidence': self._calculate_prediction_confidence(company_data),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making company prediction: {e}")
            return {'error': f'Prediction failed: {str(e)}'}
    
    def _prepare_prediction_features(self, company_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare features for prediction"""
        try:
            features = []
            
            # Financial features
            features.extend([
                company_data.get('revenue_growth', 0),
                company_data.get('profit_margin_trend', 0),
                company_data.get('debt_ratio', 0),
                company_data.get('profit_margin_volatility', 0)
            ])
            
            # Operational features
            features.extend([
                company_data.get('employee_growth', 0),
                company_data.get('employee_growth_rate', 0)
            ])
            
            # Market features
            features.extend([
                company_data.get('stock_performance', 0),
                company_data.get('stock_volatility', 0)
            ])
            
            # Industry features
            features.extend([
                company_data.get('industry_growth', 0),
                company_data.get('industry_relative_performance', 0)
            ])
            
            # WARN history features
            features.extend([
                company_data.get('warn_count_12m', 0),
                company_data.get('warn_count_24m', 0),
                company_data.get('days_since_last_warn', 365)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {e}")
            return None
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score < self.risk_thresholds['low']:
            return 'Low'
        elif risk_score < self.risk_thresholds['medium']:
            return 'Medium'
        elif risk_score < self.risk_thresholds['high']:
            return 'High'
        else:
            return 'Very High'
    
    def _generate_company_insights(self, company_data: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate insights based on company data and risk score"""
        insights = []
        
        # Financial insights
        if 'revenue_growth' in company_data:
            if company_data['revenue_growth'] < -0.1:
                insights.append("Declining revenue may indicate financial stress")
            elif company_data['revenue_growth'] > 0.2:
                insights.append("Strong revenue growth suggests stability")
        
        if 'profit_margin_trend' in company_data:
            if company_data['profit_margin_trend'] < 0.05:
                insights.append("Low profit margins may pressure cost-cutting measures")
        
        if 'debt_ratio' in company_data:
            if company_data['debt_ratio'] > 0.7:
                insights.append("High debt levels increase financial risk")
        
        # Operational insights
        if 'employee_growth' in company_data:
            if company_data['employee_growth'] < -0.05:
                insights.append("Recent employee reductions may indicate ongoing restructuring")
            elif company_data['employee_growth'] > 0.1:
                insights.append("Growing workforce suggests business expansion")
        
        # Market insights
        if 'stock_performance' in company_data:
            if company_data['stock_performance'] < -0.2:
                insights.append("Poor stock performance may reflect market concerns")
        
        # WARN history insights
        if company_data.get('warn_count_12m', 0) > 0:
            insights.append(f"Recent WARN notices ({company_data['warn_count_12m']} in past year) indicate ongoing restructuring")
        
        # Risk level insights
        if risk_score > 0.7:
            insights.append("High layoff risk - consider updating resume and networking")
        elif risk_score > 0.4:
            insights.append("Moderate risk - monitor company developments closely")
        else:
            insights.append("Low layoff risk - company appears stable")
        
        return insights
    
    def _calculate_prediction_confidence(self, company_data: Dict[str, Any]) -> float:
        """Calculate confidence in prediction based on data quality"""
        # Count available features
        available_features = sum(1 for key in self.feature_names if key in company_data)
        total_features = len(self.feature_names)
        
        # Base confidence on feature availability
        feature_confidence = available_features / total_features if total_features > 0 else 0
        
        # Adjust for data quality
        quality_penalty = 0
        for key, value in company_data.items():
            if value is None or (isinstance(value, (int, float)) and np.isnan(value)):
                quality_penalty += 0.1
        
        confidence = max(0.1, feature_confidence - quality_penalty)
        return min(1.0, confidence)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_))
    
    def update_risk_thresholds(self, thresholds: Dict[str, float]):
        """Update risk thresholds"""
        self.risk_thresholds.update(thresholds) 