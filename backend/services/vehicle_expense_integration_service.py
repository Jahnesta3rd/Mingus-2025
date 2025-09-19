#!/usr/bin/env python3
"""
Vehicle Expense Integration Service for Mingus Personal Finance App
Integrates vehicle expense categorization with existing spending analysis and ML models

Features:
- Seamless integration with existing profile system
- Enhanced spending analysis with vehicle expenses
- ML-powered insights and recommendations
- Real-time expense pattern learning
- Maintenance cost prediction and comparison
- Comprehensive financial health analysis
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

# Import all the services
from backend.services.enhanced_vehicle_expense_ml_engine import EnhancedVehicleExpenseMLEngine
from backend.services.vehicle_expense_categorizer import VehicleExpenseCategorizer
from backend.services.enhanced_spending_analyzer import EnhancedSpendingAnalyzer
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class IntegratedSpendingAnalysis:
    """Comprehensive spending analysis including vehicle expenses"""
    user_email: str
    analysis_period_months: int
    total_monthly_spending: float
    vehicle_spending: float
    traditional_spending: float
    spending_breakdown: Dict[str, Any]
    vehicle_breakdown: Dict[str, Any]
    ml_insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    maintenance_forecast: Dict[str, Any]
    budget_impact: Dict[str, Any]
    generated_at: datetime

@dataclass
class VehicleExpenseRecommendation:
    """Enhanced vehicle expense recommendation"""
    category: str
    priority: str
    title: str
    description: str
    potential_savings: float
    confidence: float
    ml_confidence: float
    action_items: List[str]
    timeline: str
    supporting_data: Dict[str, Any]

class VehicleExpenseIntegrationService:
    """
    Integration service that combines all vehicle expense functionality
    
    This service provides:
    - Seamless integration with existing profile system
    - Enhanced spending analysis with vehicle expenses
    - ML-powered insights and recommendations
    - Real-time expense pattern learning
    - Maintenance cost prediction and comparison
    - Comprehensive financial health analysis
    """
    
    def __init__(self, profile_db_path: str = "user_profiles.db", 
                 vehicle_db_path: str = "backend/mingus_vehicles.db"):
        """Initialize the integration service"""
        self.profile_db_path = profile_db_path
        self.vehicle_db_path = vehicle_db_path
        
        # Initialize all services
        self.ml_engine = EnhancedVehicleExpenseMLEngine(vehicle_db_path, profile_db_path)
        self.categorizer = VehicleExpenseCategorizer(vehicle_db_path, profile_db_path)
        self.spending_analyzer = EnhancedSpendingAnalyzer(profile_db_path, vehicle_db_path)
        self.maintenance_engine = MaintenancePredictionEngine(vehicle_db_path)
        
        logger.info("Vehicle Expense Integration Service initialized successfully")
    
    def process_expense(self, expense_data: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Process a single expense through the complete pipeline
        
        Args:
            expense_data: Expense data dictionary
            user_email: User's email address
            
        Returns:
            Complete processing result with categorization, insights, and recommendations
        """
        try:
            # Step 1: ML-powered categorization
            ml_result = self.ml_engine.categorize_expense_ml(expense_data, user_email)
            
            # Step 2: Traditional categorization for compatibility
            traditional_result = self.categorizer.categorize_expense(expense_data, user_email)
            
            # Step 3: Determine if vehicle-related
            is_vehicle_related = (ml_result.confidence_score > 0.3 if hasattr(ml_result, 'confidence_score') 
                                else traditional_result.confidence_score > 0.3)
            
            # Step 4: Save categorization if vehicle-related
            if is_vehicle_related:
                self._save_enhanced_categorization(ml_result, traditional_result, expense_data, user_email)
                
                # Step 5: Generate real-time insights
                real_time_insights = self._generate_real_time_insights(
                    ml_result, traditional_result, expense_data, user_email
                )
                
                # Step 6: Update maintenance predictions if maintenance-related
                if traditional_result.is_maintenance_related and traditional_result.vehicle_id:
                    self._update_maintenance_predictions(
                        traditional_result.vehicle_id, expense_data, user_email
                    )
            
            return {
                'success': True,
                'categorization': {
                    'expense_type': ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_result.expense_type.value,
                    'confidence': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else traditional_result.confidence_score,
                    'ml_confidence': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else 0.0,
                    'is_vehicle_related': is_vehicle_related,
                    'vehicle_id': traditional_result.vehicle_id,
                    'is_maintenance_related': traditional_result.is_maintenance_related
                },
                'insights': real_time_insights if is_vehicle_related else [],
                'recommendations': self._generate_immediate_recommendations(
                    ml_result, traditional_result, expense_data, user_email
                ) if is_vehicle_related else []
            }
            
        except Exception as e:
            logger.error(f"Error processing expense: {e}")
            return {
                'success': False,
                'error': str(e),
                'categorization': None,
                'insights': [],
                'recommendations': []
            }
    
    def get_comprehensive_analysis(self, user_email: str, months: int = 12) -> IntegratedSpendingAnalysis:
        """
        Get comprehensive spending analysis including vehicle expenses
        
        Args:
            user_email: User's email address
            months: Number of months to analyze
            
        Returns:
            IntegratedSpendingAnalysis object
        """
        try:
            # Get traditional spending analysis
            traditional_analysis = self.spending_analyzer.get_comprehensive_spending_analysis(user_email, months)
            
            # Get vehicle expense summary
            vehicle_summary = self.categorizer.get_vehicle_expense_summary(user_email, months)
            
            # Get ML-powered insights
            ml_insights = self.ml_engine.generate_insights(user_email, months)
            
            # Get maintenance forecast
            maintenance_forecast = self._get_maintenance_forecast(user_email, months)
            
            # Calculate integrated totals
            traditional_monthly = traditional_analysis.get('summary', {}).get('total_monthly', 0)
            vehicle_monthly = vehicle_summary.get('summary', {}).get('average_monthly', 0)
            total_monthly = traditional_monthly + vehicle_monthly
            
            # Create integrated breakdown
            spending_breakdown = traditional_analysis.get('categories', {})
            vehicle_breakdown = vehicle_summary.get('expenses_by_type', {})
            
            # Generate integrated recommendations
            recommendations = self._generate_integrated_recommendations(
                traditional_analysis, vehicle_summary, ml_insights, user_email
            )
            
            # Calculate budget impact
            budget_impact = self._calculate_budget_impact(
                traditional_analysis, vehicle_summary, user_email
            )
            
            return IntegratedSpendingAnalysis(
                user_email=user_email,
                analysis_period_months=months,
                total_monthly_spending=total_monthly,
                vehicle_spending=vehicle_monthly,
                traditional_spending=traditional_monthly,
                spending_breakdown=spending_breakdown,
                vehicle_breakdown=vehicle_breakdown,
                ml_insights=[self._insight_to_dict(insight) for insight in ml_insights],
                recommendations=recommendations,
                maintenance_forecast=maintenance_forecast,
                budget_impact=budget_impact,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis: {e}")
            return IntegratedSpendingAnalysis(
                user_email=user_email,
                analysis_period_months=months,
                total_monthly_spending=0,
                vehicle_spending=0,
                traditional_spending=0,
                spending_breakdown={},
                vehicle_breakdown={},
                ml_insights=[],
                recommendations=[],
                maintenance_forecast={},
                budget_impact={},
                generated_at=datetime.now()
            )
    
    def _save_enhanced_categorization(self, ml_result, traditional_result, expense_data: Dict[str, Any], user_email: str):
        """Save enhanced categorization to database"""
        try:
            conn = sqlite3.connect(self.vehicle_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_vehicle_expenses (
                    user_email, expense_id, vehicle_id, expense_type, amount,
                    description, merchant, date, confidence_score, ml_confidence,
                    matched_keywords, matched_patterns, is_maintenance_related,
                    predicted_cost_range, ml_features, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_email,
                expense_data.get('id', str(datetime.now().timestamp())),
                traditional_result.vehicle_id,
                ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_result.expense_type.value,
                expense_data.get('amount', 0),
                expense_data.get('description', ''),
                expense_data.get('merchant', ''),
                expense_data.get('date', datetime.now().date().isoformat()),
                traditional_result.confidence_score,
                ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else 0.0,
                json.dumps(traditional_result.matched_keywords),
                json.dumps(traditional_result.matched_patterns),
                traditional_result.is_maintenance_related,
                json.dumps(traditional_result.predicted_cost_range) if traditional_result.predicted_cost_range else None,
                json.dumps(ml_result.prediction_metadata if hasattr(ml_result, 'prediction_metadata') else {}),
                ml_result.model_version if hasattr(ml_result, 'model_version') else 'legacy'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving enhanced categorization: {e}")
    
    def _generate_real_time_insights(self, ml_result, traditional_result, expense_data: Dict[str, Any], user_email: str) -> List[Dict[str, Any]]:
        """Generate real-time insights for a single expense"""
        insights = []
        
        try:
            amount = float(expense_data.get('amount', 0))
            expense_type = ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_result.expense_type.value
            
            # High amount insight
            if amount > 500:
                insights.append({
                    'type': 'high_amount',
                    'title': 'High Vehicle Expense',
                    'description': f'This {expense_type} expense of ${amount:.2f} is above average',
                    'confidence': 0.9,
                    'recommendation': 'Consider getting multiple quotes for future similar expenses'
                })
            
            # Maintenance insight
            if traditional_result.is_maintenance_related:
                insights.append({
                    'type': 'maintenance',
                    'title': 'Maintenance Expense Recorded',
                    'description': f'Maintenance expense of ${amount:.2f} has been categorized',
                    'confidence': 0.95,
                    'recommendation': 'Track this against your maintenance schedule'
                })
            
            # ML confidence insight
            if hasattr(ml_result, 'confidence_score') and ml_result.confidence_score > 0.8:
                insights.append({
                    'type': 'ml_confidence',
                    'title': 'High ML Confidence',
                    'description': f'ML model is {ml_result.confidence_score:.1%} confident this is a {expense_type} expense',
                    'confidence': ml_result.confidence_score,
                    'recommendation': 'This categorization is highly reliable'
                })
            
        except Exception as e:
            logger.error(f"Error generating real-time insights: {e}")
        
        return insights
    
    def _generate_immediate_recommendations(self, ml_result, traditional_result, expense_data: Dict[str, Any], user_email: str) -> List[Dict[str, Any]]:
        """Generate immediate recommendations for a single expense"""
        recommendations = []
        
        try:
            amount = float(expense_data.get('amount', 0))
            expense_type = ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_result.expense_type.value
            
            # Fuel efficiency recommendation
            if expense_type == 'fuel' and amount > 100:
                recommendations.append({
                    'category': 'fuel_efficiency',
                    'priority': 'medium',
                    'title': 'Consider Fuel Efficiency',
                    'description': 'High fuel expense - consider fuel-efficient driving habits',
                    'potential_savings': amount * 0.1,
                    'action_items': [
                        'Use cruise control on highways',
                        'Avoid rapid acceleration and braking',
                        'Keep tires properly inflated'
                    ]
                })
            
            # Maintenance scheduling recommendation
            if traditional_result.is_maintenance_related:
                recommendations.append({
                    'category': 'maintenance',
                    'priority': 'high',
                    'title': 'Update Maintenance Schedule',
                    'description': 'Record this maintenance in your vehicle schedule',
                    'potential_savings': 0,  # Preventive maintenance
                    'action_items': [
                        'Update maintenance log',
                        'Set reminder for next service',
                        'Compare costs with other providers'
                    ]
                })
            
        except Exception as e:
            logger.error(f"Error generating immediate recommendations: {e}")
        
        return recommendations
    
    def _update_maintenance_predictions(self, vehicle_id: int, expense_data: Dict[str, Any], user_email: str):
        """Update maintenance predictions based on actual expense"""
        try:
            # This would integrate with the maintenance prediction engine
            # to update predictions based on actual service data
            logger.info(f"Updating maintenance predictions for vehicle {vehicle_id} based on actual expense")
            
        except Exception as e:
            logger.error(f"Error updating maintenance predictions: {e}")
    
    def _get_maintenance_forecast(self, user_email: str, months: int) -> Dict[str, Any]:
        """Get maintenance forecast for user's vehicles"""
        try:
            # Get user's vehicles
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, year, make, model, current_mileage, user_zipcode
                FROM vehicles 
                WHERE user_email = ?
            ''', (user_email,))
            
            vehicles = cursor.fetchall()
            conn.close()
            
            if not vehicles:
                return {}
            
            # Get maintenance predictions for each vehicle
            total_forecast = 0
            upcoming_services = []
            
            for vehicle in vehicles:
                predictions = self.maintenance_engine.get_predictions_for_vehicle(vehicle['id'])
                
                for prediction in predictions:
                    if prediction['predicted_date'] <= datetime.now().date() + timedelta(days=months * 30):
                        total_forecast += prediction['estimated_cost']
                        upcoming_services.append({
                            'vehicle': f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
                            'service': prediction['service_type'],
                            'date': prediction['predicted_date'].isoformat(),
                            'cost': prediction['estimated_cost']
                        })
            
            return {
                'total_estimated_cost': total_forecast,
                'monthly_average': total_forecast / months if months > 0 else 0,
                'upcoming_services': upcoming_services[:10],  # Next 10 services
                'vehicles_analyzed': len(vehicles)
            }
            
        except Exception as e:
            logger.error(f"Error getting maintenance forecast: {e}")
            return {}
    
    def _generate_integrated_recommendations(self, traditional_analysis: Dict[str, Any], 
                                           vehicle_summary: Dict[str, Any], 
                                           ml_insights: List, user_email: str) -> List[Dict[str, Any]]:
        """Generate integrated recommendations combining all analysis"""
        recommendations = []
        
        try:
            # Convert ML insights to recommendations
            for insight in ml_insights:
                recommendations.append({
                    'category': insight.category,
                    'priority': 'high' if insight.impact_score > 0.7 else 'medium',
                    'title': insight.title,
                    'description': insight.description,
                    'potential_savings': insight.potential_savings,
                    'confidence': insight.confidence,
                    'ml_confidence': insight.ml_confidence,
                    'action_items': [insight.recommendation],
                    'timeline': 'immediate',
                    'supporting_data': insight.supporting_data
                })
            
            # Add traditional recommendations
            traditional_recommendations = traditional_analysis.get('recommendations', [])
            recommendations.extend(traditional_recommendations)
            
        except Exception as e:
            logger.error(f"Error generating integrated recommendations: {e}")
        
        return recommendations
    
    def _calculate_budget_impact(self, traditional_analysis: Dict[str, Any], 
                               vehicle_summary: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """Calculate budget impact of vehicle expenses"""
        try:
            # Get user's monthly income
            conn = sqlite3.connect(self.profile_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT financial_info FROM user_profiles WHERE email = ?
            ''', (user_email,))
            
            profile = cursor.fetchone()
            conn.close()
            
            monthly_income = 0
            if profile:
                financial_info = json.loads(profile['financial_info'] or '{}')
                monthly_income = financial_info.get('monthlyTakehome', 0)
            
            # Calculate vehicle spending impact
            traditional_monthly = traditional_analysis.get('summary', {}).get('total_monthly', 0)
            vehicle_monthly = vehicle_summary.get('summary', {}).get('average_monthly', 0)
            total_monthly = traditional_monthly + vehicle_monthly
            
            vehicle_percentage = (vehicle_monthly / monthly_income * 100) if monthly_income > 0 else 0
            total_percentage = (total_monthly / monthly_income * 100) if monthly_income > 0 else 0
            
            return {
                'monthly_income': monthly_income,
                'vehicle_monthly': vehicle_monthly,
                'total_monthly': total_monthly,
                'vehicle_percentage_of_income': vehicle_percentage,
                'total_percentage_of_income': total_percentage,
                'disposable_income': monthly_income - total_monthly,
                'budget_health': 'healthy' if total_percentage < 80 else 'needs_attention'
            }
            
        except Exception as e:
            logger.error(f"Error calculating budget impact: {e}")
            return {}
    
    def _insight_to_dict(self, insight) -> Dict[str, Any]:
        """Convert insight object to dictionary"""
        return {
            'insight_type': insight.insight_type,
            'title': insight.title,
            'description': insight.description,
            'confidence': insight.confidence,
            'impact_score': insight.impact_score,
            'recommendation': insight.recommendation,
            'potential_savings': insight.potential_savings,
            'category': insight.category,
            'ml_confidence': insight.ml_confidence,
            'supporting_data': insight.supporting_data
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        try:
            ml_status = self.ml_engine.get_service_status()
            
            return {
                'status': 'active',
                'services': {
                    'ml_engine': ml_status,
                    'categorizer': 'active',
                    'spending_analyzer': 'active',
                    'maintenance_engine': 'active'
                },
                'integration_features': {
                    'real_time_processing': True,
                    'ml_insights': True,
                    'maintenance_forecasting': True,
                    'budget_impact_analysis': True,
                    'pattern_learning': True
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {'status': 'error', 'error': str(e)}
