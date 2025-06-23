"""
Feature Engineering for Job Security Predictions
Handles data preprocessing, feature creation, and feature selection
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.ensemble import RandomForestClassifier
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Feature engineering pipeline for job security predictions
    Handles data preprocessing, feature creation, and feature selection
    """
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_selectors = {}
        self.feature_names = []
        
        # Feature categories
        self.feature_categories = {
            'financial': ['revenue', 'profit_margin', 'debt_ratio', 'cash_flow'],
            'operational': ['employee_count', 'productivity', 'efficiency'],
            'market': ['stock_price', 'market_cap', 'pe_ratio'],
            'economic': ['gdp_growth', 'unemployment_rate', 'interest_rate'],
            'temporal': ['seasonal_patterns', 'trends', 'cyclical_factors']
        }
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set from raw data
        
        Args:
            data: Raw input data
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Creating engineered features...")
        
        features = pd.DataFrame()
        
        # Financial features
        features = pd.concat([features, self._create_financial_features(data)], axis=1)
        
        # Operational features
        features = pd.concat([features, self._create_operational_features(data)], axis=1)
        
        # Market features
        features = pd.concat([features, self._create_market_features(data)], axis=1)
        
        # Economic features
        features = pd.concat([features, self._create_economic_features(data)], axis=1)
        
        # Temporal features
        features = pd.concat([features, self._create_temporal_features(data)], axis=1)
        
        # Interaction features
        features = pd.concat([features, self._create_interaction_features(data)], axis=1)
        
        # Lag features
        features = pd.concat([features, self._create_lag_features(data)], axis=1)
        
        # Rolling statistics
        features = pd.concat([features, self._create_rolling_features(data)], axis=1)
        
        # Categorical features
        features = pd.concat([features, self._create_categorical_features(data)], axis=1)
        
        logger.info(f"Created {len(features.columns)} features")
        return features
    
    def _create_financial_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create financial-related features"""
        features = pd.DataFrame()
        
        # Revenue features
        if 'revenue' in data.columns:
            features['revenue_growth'] = data['revenue'].pct_change()
            features['revenue_growth_3m'] = data['revenue'].pct_change(90)
            features['revenue_growth_12m'] = data['revenue'].pct_change(365)
            features['revenue_volatility'] = data['revenue'].rolling(12).std()
            features['revenue_trend'] = data['revenue'].rolling(12).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
        
        # Profit margin features
        if 'profit_margin' in data.columns:
            features['profit_margin_trend'] = data['profit_margin'].rolling(6).mean()
            features['profit_margin_volatility'] = data['profit_margin'].rolling(12).std()
            features['profit_margin_change'] = data['profit_margin'].diff()
        
        # Debt features
        if 'debt_ratio' in data.columns:
            features['debt_ratio'] = data['debt_ratio']
            features['debt_trend'] = data['debt_ratio'].rolling(6).mean()
            features['debt_change'] = data['debt_ratio'].diff()
        
        # Cash flow features
        if 'cash_flow' in data.columns:
            features['cash_flow_ratio'] = data['cash_flow'] / data.get('revenue', 1)
            features['cash_flow_trend'] = data['cash_flow'].rolling(6).mean()
        
        return features
    
    def _create_operational_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create operational features"""
        features = pd.DataFrame()
        
        # Employee features
        if 'employee_count' in data.columns:
            features['employee_growth'] = data['employee_count'].pct_change()
            features['employee_growth_3m'] = data['employee_count'].pct_change(90)
            features['employee_growth_12m'] = data['employee_count'].pct_change(365)
            features['employee_trend'] = data['employee_count'].rolling(12).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
        
        # Productivity features
        if 'productivity' in data.columns:
            features['productivity_trend'] = data['productivity'].rolling(6).mean()
            features['productivity_change'] = data['productivity'].diff()
        
        # Efficiency features
        if 'efficiency' in data.columns:
            features['efficiency_trend'] = data['efficiency'].rolling(6).mean()
            features['efficiency_volatility'] = data['efficiency'].rolling(12).std()
        
        return features
    
    def _create_market_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create market-related features"""
        features = pd.DataFrame()
        
        # Stock price features
        if 'stock_price' in data.columns:
            features['stock_return'] = data['stock_price'].pct_change()
            features['stock_return_30d'] = data['stock_price'].pct_change(30)
            features['stock_volatility'] = data['stock_price'].rolling(30).std()
            features['stock_trend'] = data['stock_price'].rolling(30).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
        
        # Market cap features
        if 'market_cap' in data.columns:
            features['market_cap_growth'] = data['market_cap'].pct_change()
            features['market_cap_trend'] = data['market_cap'].rolling(12).mean()
        
        # PE ratio features
        if 'pe_ratio' in data.columns:
            features['pe_ratio'] = data['pe_ratio']
            features['pe_ratio_change'] = data['pe_ratio'].diff()
        
        return features
    
    def _create_economic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create economic indicator features"""
        features = pd.DataFrame()
        
        # GDP features
        if 'gdp_growth' in data.columns:
            features['gdp_growth'] = data['gdp_growth']
            features['gdp_trend'] = data['gdp_growth'].rolling(6).mean()
        
        # Unemployment features
        if 'unemployment_rate' in data.columns:
            features['unemployment_rate'] = data['unemployment_rate']
            features['unemployment_trend'] = data['unemployment_rate'].rolling(6).mean()
            features['unemployment_change'] = data['unemployment_rate'].diff()
        
        # Interest rate features
        if 'interest_rate' in data.columns:
            features['interest_rate'] = data['interest_rate']
            features['interest_rate_change'] = data['interest_rate'].diff()
        
        return features
    
    def _create_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create temporal and seasonal features"""
        features = pd.DataFrame()
        
        # Date-based features
        if 'date' in data.columns:
            date_col = pd.to_datetime(data['date'])
            features['month'] = date_col.dt.month
            features['quarter'] = date_col.dt.quarter
            features['year'] = date_col.dt.year
            features['day_of_week'] = date_col.dt.dayofweek
            features['is_month_end'] = date_col.dt.is_month_end.astype(int)
            features['is_quarter_end'] = date_col.dt.is_quarter_end.astype(int)
            features['is_year_end'] = date_col.dt.is_year_end.astype(int)
        
        # Seasonal features
        if 'month' in features.columns:
            features['season'] = pd.cut(
                features['month'], 
                bins=[0, 3, 6, 9, 12], 
                labels=['winter', 'spring', 'summer', 'fall']
            )
        
        return features
    
    def _create_interaction_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between variables"""
        features = pd.DataFrame()
        
        # Financial interactions
        if 'revenue' in data.columns and 'profit_margin' in data.columns:
            features['revenue_profit_interaction'] = data['revenue'] * data['profit_margin']
        
        if 'revenue' in data.columns and 'employee_count' in data.columns:
            features['revenue_per_employee'] = data['revenue'] / data['employee_count']
        
        # Market interactions
        if 'stock_price' in data.columns and 'revenue' in data.columns:
            features['stock_revenue_ratio'] = data['stock_price'] / data['revenue']
        
        # Economic interactions
        if 'gdp_growth' in data.columns and 'revenue_growth' in data.columns:
            features['gdp_revenue_growth_diff'] = data['revenue_growth'] - data['gdp_growth']
        
        return features
    
    def _create_lag_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create lagged features"""
        features = pd.DataFrame()
        
        # Lag periods to consider
        lag_periods = [1, 3, 6, 12]
        
        # Financial lags
        if 'revenue' in data.columns:
            for lag in lag_periods:
                features[f'revenue_lag_{lag}'] = data['revenue'].shift(lag)
        
        if 'profit_margin' in data.columns:
            for lag in lag_periods:
                features[f'profit_margin_lag_{lag}'] = data['profit_margin'].shift(lag)
        
        # Market lags
        if 'stock_price' in data.columns:
            for lag in lag_periods:
                features[f'stock_price_lag_{lag}'] = data['stock_price'].shift(lag)
        
        return features
    
    def _create_rolling_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create rolling window statistics"""
        features = pd.DataFrame()
        
        # Rolling windows
        windows = [3, 6, 12, 24]
        
        # Financial rolling features
        if 'revenue' in data.columns:
            for window in windows:
                features[f'revenue_rolling_mean_{window}'] = data['revenue'].rolling(window).mean()
                features[f'revenue_rolling_std_{window}'] = data['revenue'].rolling(window).std()
                features[f'revenue_rolling_min_{window}'] = data['revenue'].rolling(window).min()
                features[f'revenue_rolling_max_{window}'] = data['revenue'].rolling(window).max()
        
        # Market rolling features
        if 'stock_price' in data.columns:
            for window in windows:
                features[f'stock_rolling_mean_{window}'] = data['stock_price'].rolling(window).mean()
                features[f'stock_rolling_volatility_{window}'] = data['stock_price'].rolling(window).std()
        
        return features
    
    def _create_categorical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create categorical features"""
        features = pd.DataFrame()
        
        # Industry features
        if 'industry' in data.columns:
            features['industry'] = data['industry']
            
            # Industry-specific indicators
            industries = ['technology', 'manufacturing', 'finance', 'healthcare', 'retail']
            for industry in industries:
                features[f'is_{industry}'] = (data['industry'].str.contains(industry, case=False)).astype(int)
        
        # Company size features
        if 'employee_count' in data.columns:
            features['company_size'] = pd.cut(
                data['employee_count'],
                bins=[0, 50, 500, 5000, float('inf')],
                labels=['small', 'medium', 'large', 'enterprise']
            )
        
        # Geographic features
        if 'location' in data.columns:
            features['location'] = data['location']
            
            # Region indicators
            regions = ['northeast', 'southeast', 'midwest', 'west']
            for region in regions:
                features[f'is_{region}'] = (data['location'].str.contains(region, case=False)).astype(int)
        
        return features
    
    def create_prediction_features(self, company_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Create features for prediction from company data
        
        Args:
            company_data: Dictionary containing company information
            
        Returns:
            DataFrame with features for prediction
        """
        # Convert dict to DataFrame for processing
        data = pd.DataFrame([company_data])
        
        # Create features using the same pipeline
        features = self.create_features(data)
        
        return features
    
    def preprocess_features(self, features: pd.DataFrame, target: pd.Series = None) -> pd.DataFrame:
        """
        Preprocess features for model training
        
        Args:
            features: Feature DataFrame
            target: Target variable (optional, for feature selection)
            
        Returns:
            Preprocessed feature DataFrame
        """
        logger.info("Preprocessing features...")
        
        # Handle missing values
        features = self._handle_missing_values(features)
        
        # Encode categorical variables
        features = self._encode_categorical_variables(features)
        
        # Scale numerical features
        features = self._scale_numerical_features(features)
        
        # Feature selection (if target provided)
        if target is not None:
            features = self._select_features(features, target)
        
        # Remove constant features
        features = self._remove_constant_features(features)
        
        # Remove highly correlated features
        features = self._remove_correlated_features(features)
        
        logger.info(f"Preprocessing complete. Final features: {len(features.columns)}")
        return features
    
    def _handle_missing_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features"""
        # Fill numeric columns with median
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        features[numeric_cols] = features[numeric_cols].fillna(features[numeric_cols].median())
        
        # Fill categorical columns with mode
        categorical_cols = features.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            mode_value = features[col].mode()[0] if len(features[col].mode()) > 0 else 'Unknown'
            features[col] = features[col].fillna(mode_value)
        
        return features
    
    def _encode_categorical_variables(self, features: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables"""
        categorical_cols = features.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                features[col] = self.encoders[col].fit_transform(features[col].astype(str))
            else:
                # Handle new categories in test data
                try:
                    features[col] = self.encoders[col].transform(features[col].astype(str))
                except ValueError:
                    # Add new categories to encoder
                    unique_values = features[col].unique()
                    self.encoders[col].fit(unique_values)
                    features[col] = self.encoders[col].transform(features[col].astype(str))
        
        return features
    
    def _scale_numerical_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Scale numerical features"""
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            if 'numerical' not in self.scalers:
                self.scalers['numerical'] = StandardScaler()
                features[numeric_cols] = self.scalers['numerical'].fit_transform(features[numeric_cols])
            else:
                features[numeric_cols] = self.scalers['numerical'].transform(features[numeric_cols])
        
        return features
    
    def _select_features(self, features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """Select most important features"""
        # Use Random Forest for feature selection
        selector = SelectKBest(score_func=f_classif, k=min(50, len(features.columns)))
        selected_features = selector.fit_transform(features, target)
        selected_feature_names = features.columns[selector.get_support()]
        
        self.feature_selectors['kbest'] = selector
        self.feature_names = selected_feature_names.tolist()
        
        return pd.DataFrame(selected_features, columns=selected_feature_names)
    
    def _remove_constant_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Remove constant features"""
        constant_features = []
        for col in features.columns:
            if features[col].nunique() <= 1:
                constant_features.append(col)
        
        if constant_features:
            logger.info(f"Removing {len(constant_features)} constant features")
            features = features.drop(columns=constant_features)
        
        return features
    
    def _remove_correlated_features(self, features: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
        """Remove highly correlated features"""
        # Calculate correlation matrix
        corr_matrix = features.corr().abs()
        
        # Find highly correlated features
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > threshold)]
        
        if to_drop:
            logger.info(f"Removing {len(to_drop)} highly correlated features")
            features = features.drop(columns=to_drop)
        
        return features
    
    def get_feature_importance(self, model, feature_names: List[str] = None) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if hasattr(model, 'feature_importances_'):
            if feature_names is None:
                feature_names = self.feature_names
            
            importance_dict = dict(zip(feature_names, model.feature_importances_))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
        return {}
    
    def save_preprocessing_state(self, filepath: str):
        """Save preprocessing state (scalers, encoders, etc.)"""
        preprocessing_state = {
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_selectors': self.feature_selectors,
            'feature_names': self.feature_names
        }
        
        import joblib
        joblib.dump(preprocessing_state, filepath)
        logger.info(f"Preprocessing state saved to {filepath}")
    
    def load_preprocessing_state(self, filepath: str):
        """Load preprocessing state"""
        import joblib
        preprocessing_state = joblib.load(filepath)
        
        self.scalers = preprocessing_state['scalers']
        self.encoders = preprocessing_state['encoders']
        self.feature_selectors = preprocessing_state['feature_selectors']
        self.feature_names = preprocessing_state['feature_names']
        
        logger.info(f"Preprocessing state loaded from {filepath}") 