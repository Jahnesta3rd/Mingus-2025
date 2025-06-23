"""
Personal Risk Predictor
Predicts individual job security based on personal factors and company context
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PersonalRiskPredictor:
    """
    Predicts personal job security risk based on:
    - Individual factors (skills, experience, performance, tenure)
    - Role characteristics (criticality, replaceability, automation risk)
    - Company context (financial health, industry trends, restructuring)
    - Market conditions (demand for skills, competition, salary trends)
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.categorical_encoders = {}
        self.feature_names = []
        self.is_trained = False
        
        # Personal risk levels
        self.personal_risk_levels = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        # Risk factor categories
        self.risk_categories = {
            'individual': ['tenure', 'performance_rating', 'skill_level', 'education_level'],
            'role': ['role_criticality', 'automation_risk', 'replaceability', 'department'],
            'company': ['company_health', 'department_performance', 'restructuring_risk'],
            'market': ['skill_demand', 'salary_competitiveness', 'industry_trends']
        }
    
    def train(self, employee_data: pd.DataFrame, company_data: pd.DataFrame, 
              market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the personal risk predictor model
        
        Args:
            employee_data: DataFrame with individual employee metrics
            company_data: DataFrame with company performance data
            market_data: DataFrame with market and industry trends
            
        Returns:
            Training results and performance metrics
        """
        logger.info("Training personal risk predictor model...")
        
        # Prepare features
        features, targets = self._prepare_training_data(employee_data, company_data, market_data)
        
        if len(features) == 0:
            return {'error': 'Insufficient training data'}
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=0.2, random_state=42, stratify=targets
        )
        
        # Encode categorical features
        X_train_encoded, X_test_encoded = self._encode_categorical_features(X_train, X_test)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_encoded)
        X_test_scaled = self.scaler.transform(X_test_encoded)
        
        # Train ensemble model
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        auc = roc_auc_score(y_test, y_pred_proba)
        classification_rep = classification_report(y_test, y_pred, output_dict=True)
        
        # Store feature names
        self.feature_names = X_train_encoded.columns.tolist()
        self.is_trained = True
        
        logger.info(f"Personal risk predictor trained - AUC: {auc:.4f}")
        
        return {
            'auc': auc,
            'classification_report': classification_rep,
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
    
    def _prepare_training_data(self, employee_data: pd.DataFrame, company_data: pd.DataFrame, 
                              market_data: pd.DataFrame) -> tuple:
        """Prepare features and targets for training"""
        # Merge datasets
        merged_data = employee_data.merge(company_data, on=['company_id', 'date'], how='left')
        merged_data = merged_data.merge(market_data, on=['date', 'industry'], how='left')
        
        # Create target variable (layoff within 6 months)
        merged_data['layoff_occurred'] = merged_data['layoff_date'].notna().astype(int)
        
        # Feature engineering
        features = self._create_personal_features(merged_data)
        
        # Remove rows with missing data
        features = features.dropna()
        targets = merged_data.loc[features.index, 'layoff_occurred']
        
        return features, targets
    
    def _create_personal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features for personal risk prediction"""
        features = pd.DataFrame()
        
        # Individual factors
        if 'tenure' in data.columns:
            features['tenure_years'] = data['tenure'] / 365  # Convert days to years
            features['tenure_category'] = pd.cut(
                features['tenure_years'], 
                bins=[0, 1, 3, 5, 10, float('inf')], 
                labels=['new', 'junior', 'mid', 'senior', 'veteran']
            )
        
        if 'performance_rating' in data.columns:
            features['performance_rating'] = data['performance_rating']
            features['performance_trend'] = data.groupby('employee_id')['performance_rating'].rolling(6).mean().reset_index(0, drop=True)
        
        if 'skill_level' in data.columns:
            features['skill_level'] = data['skill_level']
            features['skill_gap'] = data['required_skills'] - data['skill_level']
        
        if 'education_level' in data.columns:
            features['education_level'] = data['education_level']
        
        # Role characteristics
        if 'role_criticality' in data.columns:
            features['role_criticality'] = data['role_criticality']
        
        if 'automation_risk' in data.columns:
            features['automation_risk'] = data['automation_risk']
        
        if 'replaceability' in data.columns:
            features['replaceability'] = data['replaceability']
        
        if 'department' in data.columns:
            features['department'] = data['department']
        
        # Company context
        if 'company_health' in data.columns:
            features['company_health'] = data['company_health']
        
        if 'department_performance' in data.columns:
            features['department_performance'] = data['department_performance']
        
        if 'restructuring_risk' in data.columns:
            features['restructuring_risk'] = data['restructuring_risk']
        
        # Market conditions
        if 'skill_demand' in data.columns:
            features['skill_demand'] = data['skill_demand']
            features['skill_market_value'] = data['skill_demand'] * data['skill_level']
        
        if 'salary_competitiveness' in data.columns:
            features['salary_competitiveness'] = data['salary_competitiveness']
        
        if 'industry_trends' in data.columns:
            features['industry_trends'] = data['industry_trends']
        
        # Derived features
        features['risk_score'] = self._calculate_individual_risk_score(data)
        features['protective_factors'] = self._calculate_protective_factors(data)
        features['vulnerability_factors'] = self._calculate_vulnerability_factors(data)
        
        return features
    
    def _calculate_individual_risk_score(self, data: pd.DataFrame) -> pd.Series:
        """Calculate individual risk score based on multiple factors"""
        risk_factors = []
        
        # Tenure risk (new employees more at risk)
        if 'tenure' in data.columns:
            tenure_risk = 1 - (data['tenure'] / (data['tenure'].max() + 1))
            risk_factors.append(tenure_risk)
        
        # Performance risk (low performers more at risk)
        if 'performance_rating' in data.columns:
            performance_risk = 1 - (data['performance_rating'] / 5)  # Assuming 5-point scale
            risk_factors.append(performance_risk)
        
        # Automation risk
        if 'automation_risk' in data.columns:
            risk_factors.append(data['automation_risk'])
        
        # Replaceability risk
        if 'replaceability' in data.columns:
            risk_factors.append(data['replaceability'])
        
        # Company health risk
        if 'company_health' in data.columns:
            company_risk = 1 - data['company_health']
            risk_factors.append(company_risk)
        
        if risk_factors:
            return pd.concat(risk_factors, axis=1).mean(axis=1)
        else:
            return pd.Series(0.5, index=data.index)
    
    def _calculate_protective_factors(self, data: pd.DataFrame) -> pd.Series:
        """Calculate protective factors that reduce layoff risk"""
        protective_factors = []
        
        # High performance
        if 'performance_rating' in data.columns:
            high_performance = (data['performance_rating'] >= 4).astype(int)
            protective_factors.append(high_performance)
        
        # Critical role
        if 'role_criticality' in data.columns:
            critical_role = (data['role_criticality'] >= 0.8).astype(int)
            protective_factors.append(critical_role)
        
        # High skill demand
        if 'skill_demand' in data.columns:
            high_demand = (data['skill_demand'] >= 0.7).astype(int)
            protective_factors.append(high_demand)
        
        # Long tenure
        if 'tenure' in data.columns:
            long_tenure = (data['tenure'] >= 1095).astype(int)  # 3+ years
            protective_factors.append(long_tenure)
        
        if protective_factors:
            return pd.concat(protective_factors, axis=1).sum(axis=1)
        else:
            return pd.Series(0, index=data.index)
    
    def _calculate_vulnerability_factors(self, data: pd.DataFrame) -> pd.Series:
        """Calculate vulnerability factors that increase layoff risk"""
        vulnerability_factors = []
        
        # Low performance
        if 'performance_rating' in data.columns:
            low_performance = (data['performance_rating'] <= 2).astype(int)
            vulnerability_factors.append(low_performance)
        
        # High automation risk
        if 'automation_risk' in data.columns:
            high_automation = (data['automation_risk'] >= 0.8).astype(int)
            vulnerability_factors.append(high_automation)
        
        # Easily replaceable
        if 'replaceability' in data.columns:
            replaceable = (data['replaceability'] >= 0.8).astype(int)
            vulnerability_factors.append(replaceable)
        
        # Short tenure
        if 'tenure' in data.columns:
            short_tenure = (data['tenure'] <= 365).astype(int)  # Less than 1 year
            vulnerability_factors.append(short_tenure)
        
        if vulnerability_factors:
            return pd.concat(vulnerability_factors, axis=1).sum(axis=1)
        else:
            return pd.Series(0, index=data.index)
    
    def _encode_categorical_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple:
        """Encode categorical features"""
        X_train_encoded = X_train.copy()
        X_test_encoded = X_test.copy()
        
        categorical_cols = X_train.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            le = LabelEncoder()
            X_train_encoded[col] = le.fit_transform(X_train_encoded[col].astype(str))
            X_test_encoded[col] = le.transform(X_test_encoded[col].astype(str))
            self.categorical_encoders[col] = le
        
        return X_train_encoded, X_test_encoded
    
    def predict(self, user_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict personal job security risk
        
        Args:
            user_data: Dictionary containing individual employee data
            company_data: Dictionary containing company context data
            
        Returns:
            Prediction results with personal risk analysis
        """
        if not self.is_trained:
            return {'error': 'Model not trained yet'}
        
        try:
            # Prepare features for prediction
            features = self._prepare_prediction_features(user_data, company_data)
            
            if features is None:
                return {'error': 'Unable to prepare features for prediction'}
            
            # Encode categorical features
            features_encoded = self._encode_prediction_features(features)
            
            # Scale features
            features_scaled = self.scaler.transform(features_encoded.reshape(1, -1))
            
            # Make prediction
            risk_probability = self.model.predict_proba(features_scaled)[0, 1]
            risk_prediction = self.model.predict(features_scaled)[0]
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_probability)
            
            # Generate personal insights
            insights = self._generate_personal_insights(user_data, company_data, risk_probability)
            
            # Get actionable recommendations
            recommendations = self._get_recommendations(user_data, company_data, risk_probability)
            
            # Feature importance for this prediction
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            
            return {
                'risk_score': risk_probability,
                'risk_level': risk_level,
                'layoff_probability_6m': risk_probability,
                'prediction': risk_prediction,
                'insights': insights,
                'recommendations': recommendations,
                'feature_importance': feature_importance,
                'confidence': self._calculate_prediction_confidence(user_data, company_data),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making personal risk prediction: {e}")
            return {'error': f'Prediction failed: {str(e)}'}
    
    def _prepare_prediction_features(self, user_data: Dict[str, Any], 
                                   company_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Prepare features for prediction"""
        try:
            features = {}
            
            # Individual factors
            features['tenure_years'] = user_data.get('tenure_days', 0) / 365
            features['performance_rating'] = user_data.get('performance_rating', 3)
            features['skill_level'] = user_data.get('skill_level', 0.5)
            features['education_level'] = user_data.get('education_level', 0.5)
            
            # Role characteristics
            features['role_criticality'] = user_data.get('role_criticality', 0.5)
            features['automation_risk'] = user_data.get('automation_risk', 0.5)
            features['replaceability'] = user_data.get('replaceability', 0.5)
            features['department'] = user_data.get('department', 'general')
            
            # Company context
            features['company_health'] = company_data.get('company_health', 0.5)
            features['department_performance'] = company_data.get('department_performance', 0.5)
            features['restructuring_risk'] = company_data.get('restructuring_risk', 0.5)
            
            # Market conditions
            features['skill_demand'] = user_data.get('skill_demand', 0.5)
            features['salary_competitiveness'] = user_data.get('salary_competitiveness', 0.5)
            features['industry_trends'] = company_data.get('industry_trends', 0.5)
            
            # Derived features
            features['risk_score'] = self._calculate_individual_risk_score_dict(user_data, company_data)
            features['protective_factors'] = self._calculate_protective_factors_dict(user_data)
            features['vulnerability_factors'] = self._calculate_vulnerability_factors_dict(user_data)
            
            return pd.DataFrame([features])
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {e}")
            return None
    
    def _calculate_individual_risk_score_dict(self, user_data: Dict[str, Any], 
                                            company_data: Dict[str, Any]) -> float:
        """Calculate individual risk score from dictionaries"""
        risk_factors = []
        
        # Tenure risk
        tenure_days = user_data.get('tenure_days', 0)
        max_tenure = 3650  # 10 years
        tenure_risk = 1 - (tenure_days / (max_tenure + 1))
        risk_factors.append(tenure_risk)
        
        # Performance risk
        performance = user_data.get('performance_rating', 3)
        performance_risk = 1 - (performance / 5)
        risk_factors.append(performance_risk)
        
        # Automation risk
        automation_risk = user_data.get('automation_risk', 0.5)
        risk_factors.append(automation_risk)
        
        # Replaceability risk
        replaceability = user_data.get('replaceability', 0.5)
        risk_factors.append(replaceability)
        
        # Company health risk
        company_health = company_data.get('company_health', 0.5)
        company_risk = 1 - company_health
        risk_factors.append(company_risk)
        
        return np.mean(risk_factors)
    
    def _calculate_protective_factors_dict(self, user_data: Dict[str, Any]) -> int:
        """Calculate protective factors from dictionary"""
        protective_count = 0
        
        # High performance
        if user_data.get('performance_rating', 0) >= 4:
            protective_count += 1
        
        # Critical role
        if user_data.get('role_criticality', 0) >= 0.8:
            protective_count += 1
        
        # High skill demand
        if user_data.get('skill_demand', 0) >= 0.7:
            protective_count += 1
        
        # Long tenure
        if user_data.get('tenure_days', 0) >= 1095:  # 3+ years
            protective_count += 1
        
        return protective_count
    
    def _calculate_vulnerability_factors_dict(self, user_data: Dict[str, Any]) -> int:
        """Calculate vulnerability factors from dictionary"""
        vulnerability_count = 0
        
        # Low performance
        if user_data.get('performance_rating', 5) <= 2:
            vulnerability_count += 1
        
        # High automation risk
        if user_data.get('automation_risk', 0) >= 0.8:
            vulnerability_count += 1
        
        # Easily replaceable
        if user_data.get('replaceability', 0) >= 0.8:
            vulnerability_count += 1
        
        # Short tenure
        if user_data.get('tenure_days', 3650) <= 365:  # Less than 1 year
            vulnerability_count += 1
        
        return vulnerability_count
    
    def _encode_prediction_features(self, features: pd.DataFrame) -> np.ndarray:
        """Encode categorical features for prediction"""
        features_encoded = features.copy()
        
        for col, encoder in self.categorical_encoders.items():
            if col in features_encoded.columns:
                features_encoded[col] = encoder.transform(features_encoded[col].astype(str))
        
        return features_encoded.values
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score < self.personal_risk_levels['low']:
            return 'Low'
        elif risk_score < self.personal_risk_levels['medium']:
            return 'Medium'
        elif risk_score < self.personal_risk_levels['high']:
            return 'High'
        else:
            return 'Very High'
    
    def _generate_personal_insights(self, user_data: Dict[str, Any], company_data: Dict[str, Any], 
                                  risk_score: float) -> List[str]:
        """Generate insights based on personal data and risk score"""
        insights = []
        
        # Individual factor insights
        performance = user_data.get('performance_rating', 3)
        if performance < 3:
            insights.append("Performance below average - focus on improvement areas")
        elif performance >= 4:
            insights.append("Strong performance - valuable asset to the company")
        
        tenure_days = user_data.get('tenure_days', 0)
        if tenure_days < 365:
            insights.append("Short tenure - new employees may be more vulnerable during layoffs")
        elif tenure_days > 1825:  # 5+ years
            insights.append("Long tenure - institutional knowledge provides some protection")
        
        # Role insights
        role_criticality = user_data.get('role_criticality', 0.5)
        if role_criticality >= 0.8:
            insights.append("Critical role - essential to company operations")
        elif role_criticality <= 0.3:
            insights.append("Non-critical role - may be more vulnerable to cuts")
        
        automation_risk = user_data.get('automation_risk', 0.5)
        if automation_risk >= 0.7:
            insights.append("High automation risk - role may be automated in future")
        
        # Company context insights
        company_health = company_data.get('company_health', 0.5)
        if company_health < 0.4:
            insights.append("Company financial health concerns - monitor developments")
        
        # Risk level insights
        if risk_score > 0.7:
            insights.append("High personal risk - consider proactive career planning")
        elif risk_score > 0.4:
            insights.append("Moderate risk - stay informed about company developments")
        else:
            insights.append("Low personal risk - position appears secure")
        
        return insights
    
    def _get_recommendations(self, user_data: Dict[str, Any], company_data: Dict[str, Any], 
                           risk_score: float) -> List[str]:
        """Get actionable recommendations based on risk assessment"""
        recommendations = []
        
        # Performance-based recommendations
        performance = user_data.get('performance_rating', 3)
        if performance < 3:
            recommendations.append("Improve performance metrics and seek feedback from manager")
            recommendations.append("Take on additional responsibilities to demonstrate value")
        
        # Skill-based recommendations
        skill_level = user_data.get('skill_level', 0.5)
        skill_demand = user_data.get('skill_demand', 0.5)
        
        if skill_level < 0.6:
            recommendations.append("Invest in skill development and training programs")
        
        if skill_demand > 0.7:
            recommendations.append("High-demand skills - leverage for career advancement")
        
        # Network and visibility recommendations
        if risk_score > 0.5:
            recommendations.append("Strengthen professional network and industry connections")
            recommendations.append("Update resume and maintain active job search presence")
            recommendations.append("Consider internal transfer opportunities")
        
        # Company-specific recommendations
        company_health = company_data.get('company_health', 0.5)
        if company_health < 0.4:
            recommendations.append("Monitor company financial reports and industry news")
            recommendations.append("Explore opportunities in more stable companies")
        
        # General recommendations
        recommendations.append("Maintain emergency savings equivalent to 3-6 months of expenses")
        recommendations.append("Stay current with industry trends and technology changes")
        
        return recommendations
    
    def _calculate_prediction_confidence(self, user_data: Dict[str, Any], 
                                       company_data: Dict[str, Any]) -> float:
        """Calculate confidence in prediction based on data quality"""
        # Base confidence
        confidence = 0.6
        
        # Adjust for data completeness
        required_fields = ['performance_rating', 'tenure_days', 'role_criticality', 'skill_level']
        available_fields = sum(1 for field in required_fields if field in user_data)
        confidence += (available_fields / len(required_fields)) * 0.2
        
        # Adjust for company data availability
        if company_data and len(company_data) > 2:
            confidence += 0.1
        
        # Adjust for data quality
        if user_data.get('performance_rating') and 1 <= user_data['performance_rating'] <= 5:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_)) 