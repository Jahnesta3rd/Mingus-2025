"""
Geographic Job Security Predictor
Predicts regional employment outlook and geographic risk factors
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GeographicPredictor:
    """
    Predicts geographic job security risk based on:
    - Regional economic indicators (GDP, unemployment, job growth)
    - Industry concentration and diversification
    - Population demographics and migration patterns
    - Infrastructure and business environment
    - Cost of living and wage trends
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.location_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        
        # Geographic risk levels
        self.geographic_risk_levels = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        # Regional economic indicators
        self.economic_indicators = [
            'gdp_growth', 'unemployment_rate', 'job_growth_rate',
            'labor_force_participation', 'wage_growth', 'cost_of_living_index'
        ]
        
        # Industry concentration factors
        self.industry_factors = [
            'industry_diversification', 'dominant_industry_share',
            'manufacturing_concentration', 'tech_concentration',
            'service_sector_share'
        ]
    
    def train(self, geographic_data: pd.DataFrame, economic_data: pd.DataFrame, 
              demographic_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the geographic predictor model
        
        Args:
            geographic_data: DataFrame with location-specific metrics
            economic_data: DataFrame with regional economic indicators
            demographic_data: DataFrame with population demographics
            
        Returns:
            Training results and performance metrics
        """
        logger.info("Training geographic predictor model...")
        
        # Prepare features
        features, targets = self._prepare_training_data(geographic_data, economic_data, demographic_data)
        
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
        
        logger.info(f"Geographic predictor trained - MSE: {mse:.4f}, R²: {r2:.4f}")
        
        return {
            'mse': mse,
            'r2': r2,
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
    
    def _prepare_training_data(self, geographic_data: pd.DataFrame, economic_data: pd.DataFrame, 
                              demographic_data: pd.DataFrame) -> tuple:
        """Prepare features and targets for training"""
        # Merge datasets
        merged_data = geographic_data.merge(economic_data, on=['location', 'date'], how='left')
        merged_data = merged_data.merge(demographic_data, on=['location', 'date'], how='left')
        
        # Create target variable (regional unemployment rate or job loss rate)
        merged_data['job_security_risk'] = merged_data['unemployment_rate'] + merged_data['job_loss_rate']
        
        # Feature engineering
        features = self._create_geographic_features(merged_data)
        
        # Remove rows with missing data
        features = features.dropna()
        targets = merged_data.loc[features.index, 'job_security_risk']
        
        return features, targets
    
    def _create_geographic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features for geographic prediction"""
        features = pd.DataFrame()
        
        # Economic indicators
        for indicator in self.economic_indicators:
            if indicator in data.columns:
                features[indicator] = data[indicator]
                features[f'{indicator}_trend'] = data[indicator].rolling(12).mean()
                features[f'{indicator}_volatility'] = data[indicator].rolling(24).std()
        
        # Industry concentration features
        for factor in self.industry_factors:
            if factor in data.columns:
                features[factor] = data[factor]
        
        # Geographic features
        if 'population_growth' in data.columns:
            features['population_growth'] = data['population_growth']
            features['population_trend'] = data['population_growth'].rolling(12).mean()
        
        if 'migration_rate' in data.columns:
            features['migration_rate'] = data['migration_rate']
            features['net_migration'] = data['in_migration'] - data['out_migration']
        
        # Infrastructure and business environment
        if 'business_friendliness' in data.columns:
            features['business_friendliness'] = data['business_friendliness']
        
        if 'infrastructure_quality' in data.columns:
            features['infrastructure_quality'] = data['infrastructure_quality']
        
        if 'education_level' in data.columns:
            features['education_level'] = data['education_level']
            features['skilled_workforce_ratio'] = data['bachelors_degree_plus'] / data['total_population']
        
        # Cost of living and wage factors
        if 'cost_of_living_index' in data.columns:
            features['cost_of_living_index'] = data['cost_of_living_index']
            features['wage_to_cost_ratio'] = data['median_wage'] / data['cost_of_living_index']
        
        # Regional diversity and resilience
        features['industry_diversity'] = self._calculate_industry_diversity(data)
        features['economic_resilience'] = self._calculate_economic_resilience(data)
        
        # Geographic clustering
        features['urban_rural_ratio'] = data.get('urban_population', 0) / data.get('total_population', 1)
        features['metro_area_indicator'] = (data.get('metro_area_population', 0) > 1000000).astype(int)
        
        # Fill missing values
        features = features.fillna(0)
        
        return features
    
    def _calculate_industry_diversity(self, data: pd.DataFrame) -> pd.Series:
        """Calculate industry diversity index"""
        # This would calculate Herfindahl-Hirschman Index for industry concentration
        # For now, return a simple diversity measure
        industry_columns = [col for col in data.columns if 'industry_share' in col]
        
        if len(industry_columns) > 1:
            # Calculate diversity as 1 - sum of squared shares
            shares = data[industry_columns].fillna(0)
            diversity = 1 - (shares ** 2).sum(axis=1)
            return diversity
        else:
            return pd.Series(0.5, index=data.index)
    
    def _calculate_economic_resilience(self, data: pd.DataFrame) -> pd.Series:
        """Calculate economic resilience score"""
        # Combine multiple factors for resilience
        factors = []
        
        if 'gdp_growth' in data.columns:
            factors.append(data['gdp_growth'].rolling(12).std())  # Lower volatility = higher resilience
        
        if 'unemployment_rate' in data.columns:
            factors.append(1 - data['unemployment_rate'])  # Lower unemployment = higher resilience
        
        if 'industry_diversification' in data.columns:
            factors.append(data['industry_diversification'])
        
        if factors:
            resilience = pd.concat(factors, axis=1).mean(axis=1)
            return resilience
        else:
            return pd.Series(0.5, index=data.index)
    
    def predict(self, location: str, economic_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict geographic job security risk
        
        Args:
            location: Location name (city, state, region)
            economic_context: Current economic indicators (optional)
            
        Returns:
            Prediction results with geographic risk analysis
        """
        if not self.is_trained:
            return {'error': 'Model not trained yet'}
        
        try:
            # Prepare features for prediction
            features = self._prepare_prediction_features(location, economic_context)
            
            if features is None:
                return {'error': 'Unable to prepare features for prediction'}
            
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Make prediction
            risk_score = self.model.predict(features_scaled)[0]
            risk_score = max(0, min(1, risk_score))  # Clamp between 0 and 1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate geographic insights
            insights = self._generate_geographic_insights(location, risk_score, economic_context)
            
            # Get regional trends
            trends = self._analyze_regional_trends(location)
            
            # Feature importance for this prediction
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            
            return {
                'location': location,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'employment_outlook': self._get_employment_outlook(risk_score),
                'insights': insights,
                'trends': trends,
                'feature_importance': feature_importance,
                'confidence': self._calculate_prediction_confidence(location, economic_context),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making geographic prediction: {e}")
            return {'error': f'Prediction failed: {str(e)}'}
    
    def _prepare_prediction_features(self, location: str, economic_context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare features for prediction"""
        try:
            features = []
            
            # Economic features
            if economic_context:
                features.extend([
                    economic_context.get('gdp_growth', 0.02),
                    economic_context.get('unemployment_rate', 0.05),
                    economic_context.get('job_growth_rate', 0.01),
                    economic_context.get('wage_growth', 0.025),
                    economic_context.get('cost_of_living_index', 100)
                ])
            else:
                # Use default values
                features.extend([0.02, 0.05, 0.01, 0.025, 100])
            
            # Location-specific features
            location_features = self._get_location_specific_features(location)
            features.extend(location_features)
            
            # Industry concentration features
            industry_features = self._get_industry_concentration(location)
            features.extend(industry_features)
            
            # Demographic features
            demographic_features = self._get_demographic_features(location)
            features.extend(demographic_features)
            
            # Infrastructure features
            infrastructure_features = self._get_infrastructure_features(location)
            features.extend(infrastructure_features)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {e}")
            return None
    
    def _get_location_specific_features(self, location: str) -> List[float]:
        """Get location-specific economic and demographic features"""
        # This would typically come from a database or API
        # For now, return default values based on location type
        
        location_lower = location.lower()
        
        # Major metro areas
        if any(city in location_lower for city in ['new york', 'los angeles', 'chicago', 'houston', 'phoenix']):
            return [0.03, 0.04, 0.8, 0.9, 120]  # High growth, low unemployment, urban, metro, high cost
        
        # Tech hubs
        elif any(city in location_lower for city in ['san francisco', 'seattle', 'austin', 'boston']):
            return [0.04, 0.03, 0.9, 0.95, 140]  # Very high growth, very low unemployment, very urban, metro, very high cost
        
        # Manufacturing regions
        elif any(city in location_lower for city in ['detroit', 'cleveland', 'pittsburgh', 'milwaukee']):
            return [0.01, 0.06, 0.7, 0.8, 90]  # Low growth, higher unemployment, urban, metro, lower cost
        
        # Rural areas
        elif any(word in location_lower for word in ['rural', 'county', 'town']):
            return [0.005, 0.07, 0.2, 0.3, 80]  # Very low growth, high unemployment, rural, non-metro, low cost
        
        else:
            return [0.02, 0.05, 0.6, 0.7, 100]  # Default values
    
    def _get_industry_concentration(self, location: str) -> List[float]:
        """Get industry concentration metrics for location"""
        location_lower = location.lower()
        
        # Tech hubs
        if any(city in location_lower for city in ['san francisco', 'seattle', 'austin', 'boston']):
            return [0.8, 0.4, 0.1, 0.6, 0.3]  # High tech concentration, low manufacturing, high service
        
        # Manufacturing hubs
        elif any(city in location_lower for city in ['detroit', 'cleveland', 'pittsburgh']):
            return [0.2, 0.7, 0.6, 0.1, 0.2]  # Low tech, high manufacturing, low service
        
        # Financial centers
        elif any(city in location_lower for city in ['new york', 'chicago']):
            return [0.3, 0.1, 0.2, 0.8, 0.6]  # Moderate tech, low manufacturing, high service
        
        else:
            return [0.3, 0.3, 0.3, 0.4, 0.4]  # Balanced distribution
    
    def _get_demographic_features(self, location: str) -> List[float]:
        """Get demographic features for location"""
        location_lower = location.lower()
        
        # Young, educated areas (tech hubs)
        if any(city in location_lower for city in ['austin', 'boston', 'seattle']):
            return [0.02, 0.05, 0.6, 0.8]  # High population growth, high migration, urban, educated
        
        # Established metro areas
        elif any(city in location_lower for city in ['new york', 'los angeles', 'chicago']):
            return [0.01, 0.02, 0.9, 0.7]  # Moderate growth, low migration, very urban, educated
        
        # Declining industrial areas
        elif any(city in location_lower for city in ['detroit', 'cleveland']):
            return [-0.01, -0.02, 0.8, 0.5]  # Negative growth, out-migration, urban, moderate education
        
        else:
            return [0.01, 0.01, 0.6, 0.6]  # Default values
    
    def _get_infrastructure_features(self, location: str) -> List[float]:
        """Get infrastructure and business environment features"""
        location_lower = location.lower()
        
        # Major business centers
        if any(city in location_lower for city in ['new york', 'chicago', 'boston']):
            return [0.8, 0.9, 0.8]  # High business friendliness, high infrastructure, high education
        
        # Tech hubs
        elif any(city in location_lower for city in ['san francisco', 'seattle', 'austin']):
            return [0.9, 0.8, 0.9]  # Very high business friendliness, high infrastructure, very high education
        
        # Industrial areas
        elif any(city in location_lower for city in ['detroit', 'cleveland', 'pittsburgh']):
            return [0.5, 0.6, 0.6]  # Moderate business friendliness, moderate infrastructure, moderate education
        
        else:
            return [0.6, 0.6, 0.6]  # Default values
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score < self.geographic_risk_levels['low']:
            return 'Low'
        elif risk_score < self.geographic_risk_levels['medium']:
            return 'Medium'
        elif risk_score < self.geographic_risk_levels['high']:
            return 'High'
        else:
            return 'Very High'
    
    def _get_employment_outlook(self, risk_score: float) -> str:
        """Get employment outlook based on risk score"""
        if risk_score < 0.3:
            return 'Strong'
        elif risk_score < 0.6:
            return 'Moderate'
        elif risk_score < 0.8:
            return 'Weak'
        else:
            return 'Poor'
    
    def _generate_geographic_insights(self, location: str, risk_score: float, 
                                    economic_context: Dict[str, Any]) -> List[str]:
        """Generate insights based on location and risk score"""
        insights = []
        
        # Economic context insights
        if economic_context:
            unemployment_rate = economic_context.get('unemployment_rate', 0.05)
            if unemployment_rate > 0.07:
                insights.append("Regional unemployment above national average")
            elif unemployment_rate < 0.04:
                insights.append("Regional unemployment below national average")
        
        # Location-specific insights
        location_lower = location.lower()
        
        if any(city in location_lower for city in ['san francisco', 'seattle', 'austin']):
            if risk_score > 0.6:
                insights.append("Tech hub experiencing market correction and hiring slowdown")
            else:
                insights.append("Tech hub remains strong with high demand for skilled workers")
        
        elif any(city in location_lower for city in ['detroit', 'cleveland', 'pittsburgh']):
            if risk_score > 0.7:
                insights.append("Industrial region facing continued manufacturing decline")
            else:
                insights.append("Industrial region showing signs of economic diversification")
        
        elif any(city in location_lower for city in ['new york', 'chicago']):
            if risk_score > 0.5:
                insights.append("Major metro area experiencing sector-specific challenges")
            else:
                insights.append("Major metro area maintaining economic stability")
        
        # Risk level insights
        if risk_score > 0.7:
            insights.append("High regional risk - consider relocation or remote work opportunities")
        elif risk_score > 0.4:
            insights.append("Moderate regional risk - monitor local economic developments")
        else:
            insights.append("Low regional risk - area appears economically stable")
        
        return insights
    
    def _analyze_regional_trends(self, location: str) -> Dict[str, Any]:
        """Analyze regional trends and patterns"""
        # This would typically analyze historical data
        # For now, return placeholder trends
        
        location_lower = location.lower()
        
        if any(city in location_lower for city in ['san francisco', 'seattle', 'austin']):
            return {
                'employment_trend': 'growing',
                'wage_trend': 'increasing',
                'cost_of_living_trend': 'increasing',
                'industry_trend': 'technology_focused',
                'migration_trend': 'inward'
            }
        elif any(city in location_lower for city in ['detroit', 'cleveland']):
            return {
                'employment_trend': 'declining',
                'wage_trend': 'stable',
                'cost_of_living_trend': 'stable',
                'industry_trend': 'diversifying',
                'migration_trend': 'outward'
            }
        else:
            return {
                'employment_trend': 'stable',
                'wage_trend': 'moderate_growth',
                'cost_of_living_trend': 'stable',
                'industry_trend': 'balanced',
                'migration_trend': 'stable'
            }
    
    def _calculate_prediction_confidence(self, location: str, economic_context: Dict[str, Any]) -> float:
        """Calculate confidence in prediction based on data quality"""
        # Base confidence on data availability
        confidence = 0.6  # Base confidence
        
        # Adjust for economic context availability
        if economic_context and len(economic_context) > 3:
            confidence += 0.2
        
        # Adjust for location specificity
        if any(city in location.lower() for city in ['new york', 'los angeles', 'chicago', 'san francisco', 'seattle']):
            confidence += 0.2  # Major cities have more data
        
        return min(1.0, confidence)
    
    def compare_locations(self, locations: List[str]) -> Dict[str, Any]:
        """Compare job security risk across multiple locations"""
        if not self.is_trained:
            return {'error': 'Model not trained yet'}
        
        comparisons = {}
        
        for location in locations:
            prediction = self.predict(location)
            if 'error' not in prediction:
                comparisons[location] = {
                    'risk_score': prediction['risk_score'],
                    'risk_level': prediction['risk_level'],
                    'employment_outlook': prediction['employment_outlook'],
                    'confidence': prediction['confidence']
                }
        
        # Sort by risk score
        sorted_comparisons = dict(sorted(
            comparisons.items(), 
            key=lambda x: x[1]['risk_score']
        ))
        
        return {
            'location_comparison': sorted_comparisons,
            'safest_location': list(sorted_comparisons.keys())[0] if sorted_comparisons else None,
            'riskiest_location': list(sorted_comparisons.keys())[-1] if sorted_comparisons else None
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_)) 