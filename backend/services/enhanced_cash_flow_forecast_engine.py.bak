#!/usr/bin/env python3
"""
Enhanced Cash Flow Forecast Engine for Mingus Flask Application
Integrates vehicle maintenance predictions with existing financial forecasting

Features:
- Integrates vehicle maintenance costs with monthly budget forecasting
- Maintains backward compatibility with existing profile system
- Provides detailed vehicle expense breakdowns
- Includes both routine maintenance and probabilistic repairs
- Supports multiple vehicles per user
- Real-time forecast updates when vehicle data changes
"""

import logging
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

# Import the existing maintenance prediction engine
from .maintenance_prediction_engine import MaintenancePredictionEngine

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class VehicleExpenseForecast:
    """Data class for vehicle expense forecast"""
    vehicle_id: int
    vehicle_info: Dict[str, Any]
    monthly_costs: Dict[str, float]  # month_key -> total_cost
    routine_costs: Dict[str, float]  # month_key -> routine_cost
    repair_costs: Dict[str, float]   # month_key -> repair_cost
    predictions: Dict[str, List[Dict[str, Any]]]  # month_key -> list of predictions
    total_forecast_cost: float
    average_monthly_cost: float

@dataclass
class MonthlyForecastCategory:
    """Data class for monthly forecast category"""
    category_name: str
    monthly_amounts: Dict[str, float]  # month_key -> amount
    total_amount: float
    average_monthly: float
    details: Optional[Dict[str, Any]] = None

@dataclass
class EnhancedCashFlowForecast:
    """Data class for enhanced cash flow forecast"""
    user_email: str
    forecast_period_months: int
    start_date: date
    end_date: date
    categories: Dict[str, MonthlyForecastCategory]
    vehicle_expenses: List[VehicleExpenseForecast]
    total_monthly_forecast: Dict[str, float]  # month_key -> total_amount
    total_forecast_amount: float
    average_monthly_amount: float
    generated_date: datetime

class EnhancedCashFlowForecastEngine:
    """
    Enhanced Cash Flow Forecast Engine that integrates vehicle maintenance
    with existing financial forecasting capabilities.
    
    This engine extends the existing profile-based financial system to include
    vehicle maintenance predictions while maintaining full backward compatibility.
    """
    
    def __init__(self, profile_db_path: str = "user_profiles.db", 
                 vehicle_db_path: str = "backend/mingus_vehicles.db"):
        """Initialize the enhanced cash flow forecast engine"""
        self.profile_db_path = profile_db_path
        self.vehicle_db_path = vehicle_db_path
        self.maintenance_engine = MaintenancePredictionEngine(vehicle_db_path)
        
        # Initialize databases
        self._init_databases()
    
    def _init_databases(self):
        """Initialize required databases"""
        try:
            # Initialize profile database
            conn = sqlite3.connect(self.profile_db_path)
            conn.close()
            
            # Initialize vehicle database (handled by MaintenancePredictionEngine)
            logger.info("Enhanced cash flow forecast engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing databases: {e}")
            raise
    
    def get_user_vehicles(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Get all vehicles associated with a user
        
        Args:
            user_email: User's email address
            
        Returns:
            List of vehicle information dictionaries
        """
        try:
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get vehicles for user (assuming user_email is stored in vehicles table)
            cursor.execute('''
                SELECT id, year, make, model, current_mileage, user_zipcode, 
                       user_email, created_date, updated_date
                FROM vehicles 
                WHERE user_email = ?
                ORDER BY created_date DESC
            ''', (user_email,))
            
            vehicles = []
            for row in cursor.fetchall():
                vehicles.append({
                    'id': row['id'],
                    'year': row['year'],
                    'make': row['make'],
                    'model': row['model'],
                    'current_mileage': row['current_mileage'],
                    'user_zipcode': row['user_zipcode'],
                    'user_email': row['user_email'],
                    'created_date': row['created_date'],
                    'updated_date': row['updated_date']
                })
            
            conn.close()
            return vehicles
            
        except Exception as e:
            logger.error(f"Error getting user vehicles for {user_email}: {e}")
            return []
    
    def generate_vehicle_expense_forecast(self, vehicle_id: int, months: int = 12) -> Optional[VehicleExpenseForecast]:
        """
        Generate expense forecast for a specific vehicle
        
        Args:
            vehicle_id: Vehicle ID
            months: Number of months to forecast
            
        Returns:
            VehicleExpenseForecast object or None if error
        """
        try:
            # Get vehicle information
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, year, make, model, current_mileage, user_zipcode, user_email
                FROM vehicles WHERE id = ?
            ''', (vehicle_id,))
            
            vehicle_row = cursor.fetchone()
            conn.close()
            
            if not vehicle_row:
                logger.warning(f"Vehicle {vehicle_id} not found")
                return None
            
            vehicle_info = {
                'id': vehicle_row['id'],
                'year': vehicle_row['year'],
                'make': vehicle_row['make'],
                'model': vehicle_row['model'],
                'current_mileage': vehicle_row['current_mileage'],
                'user_zipcode': vehicle_row['user_zipcode'],
                'user_email': vehicle_row['user_email']
            }
            
            # Generate maintenance predictions
            predictions = self.maintenance_engine.get_predictions_for_vehicle(vehicle_id)
            
            if not predictions:
                # Generate new predictions if none exist
                prediction_objects = self.maintenance_engine.predict_maintenance(
                    vehicle_id=vehicle_id,
                    year=vehicle_row['year'],
                    make=vehicle_row['make'],
                    model=vehicle_row['model'],
                    current_mileage=vehicle_row['current_mileage'],
                    zipcode=vehicle_row['user_zipcode'],
                    prediction_horizon_months=months
                )
                
                # Save predictions
                self.maintenance_engine._save_predictions(prediction_objects)
                
                # Convert to dictionary format
                predictions = []
                for pred in prediction_objects:
                    predictions.append({
                        'predicted_date': pred.predicted_date,
                        'estimated_cost': pred.estimated_cost,
                        'is_routine': pred.is_routine,
                        'service_type': pred.service_type,
                        'description': pred.description,
                        'probability': pred.probability
                    })
            
            # Process predictions into monthly breakdown
            current_date = datetime.now().date()
            end_date = current_date + timedelta(days=months * 30)
            
            monthly_costs = {}
            routine_costs = {}
            repair_costs = {}
            monthly_predictions = {}
            
            for prediction in predictions:
                # Handle both dictionary and object formats
                if isinstance(prediction, dict):
                    pred_date = prediction['predicted_date']
                    cost = prediction['estimated_cost']
                    is_routine = prediction['is_routine']
                    service_type = prediction['service_type']
                    description = prediction['description']
                    probability = prediction['probability']
                else:
                    pred_date = prediction.predicted_date
                    cost = prediction.estimated_cost
                    is_routine = prediction.is_routine
                    service_type = prediction.service_type
                    description = prediction.description
                    probability = prediction.probability
                
                if pred_date <= end_date:
                    month_key = pred_date.strftime('%Y-%m')
                    
                    if month_key not in monthly_costs:
                        monthly_costs[month_key] = 0.0
                        routine_costs[month_key] = 0.0
                        repair_costs[month_key] = 0.0
                        monthly_predictions[month_key] = []
                    
                    monthly_costs[month_key] += cost
                    monthly_predictions[month_key].append({
                        'service_type': service_type,
                        'description': description,
                        'estimated_cost': cost,
                        'predicted_date': pred_date,
                        'is_routine': is_routine,
                        'probability': probability
                    })
                    
                    if is_routine:
                        routine_costs[month_key] += cost
                    else:
                        repair_costs[month_key] += cost
            
            # Calculate totals
            total_forecast_cost = sum(monthly_costs.values())
            average_monthly_cost = total_forecast_cost / months if months > 0 else 0.0
            
            return VehicleExpenseForecast(
                vehicle_id=vehicle_id,
                vehicle_info=vehicle_info,
                monthly_costs=monthly_costs,
                routine_costs=routine_costs,
                repair_costs=repair_costs,
                predictions=monthly_predictions,
                total_forecast_cost=total_forecast_cost,
                average_monthly_cost=average_monthly_cost
            )
            
        except Exception as e:
            logger.error(f"Error generating vehicle expense forecast for vehicle {vehicle_id}: {e}")
            return None
    
    def get_user_profile_expenses(self, user_email: str) -> Dict[str, MonthlyForecastCategory]:
        """
        Get existing monthly expenses from user profile
        
        Args:
            user_email: User's email address
            
        Returns:
            Dictionary of expense categories
        """
        try:
            conn = sqlite3.connect(self.profile_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT monthly_expenses FROM user_profiles WHERE email = ?
            ''', (user_email,))
            
            profile_row = cursor.fetchone()
            conn.close()
            
            if not profile_row or not profile_row['monthly_expenses']:
                return {}
            
            monthly_expenses = json.loads(profile_row['monthly_expenses'])
            
            # Convert to MonthlyForecastCategory format
            categories = {}
            
            # Standard expense categories from the profile system
            expense_categories = {
                'rent': 'Housing',
                'carPayment': 'Car Payment',
                'insurance': 'Insurance',
                'groceries': 'Groceries',
                'utilities': 'Utilities',
                'studentLoanPayment': 'Student Loan Payment',
                'creditCardMinimum': 'Credit Card Payment'
            }
            
            for key, label in expense_categories.items():
                amount = monthly_expenses.get(key, 0)
                if amount > 0:
                    # Create monthly amounts (assuming same amount each month)
                    monthly_amounts = {}
                    for i in range(12):  # Default to 12 months
                        month_key = (datetime.now() + timedelta(days=i*30)).strftime('%Y-%m')
                        monthly_amounts[month_key] = amount
                    
                    categories[key] = MonthlyForecastCategory(
                        category_name=label,
                        monthly_amounts=monthly_amounts,
                        total_amount=amount * 12,
                        average_monthly=amount,
                        details={'source': 'profile', 'category_key': key}
                    )
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting user profile expenses for {user_email}: {e}")
            return {}
    
    def generate_enhanced_cash_flow_forecast(self, user_email: str, months: int = 12) -> Optional[EnhancedCashFlowForecast]:
        """
        Generate enhanced cash flow forecast including vehicle expenses
        
        Args:
            user_email: User's email address
            months: Number of months to forecast
            
        Returns:
            EnhancedCashFlowForecast object or None if error
        """
        try:
            # Get user profile expenses
            profile_categories = self.get_user_profile_expenses(user_email)
            
            # Get user vehicles
            vehicles = self.get_user_vehicles(user_email)
            
            # Generate vehicle expense forecasts
            vehicle_expenses = []
            for vehicle in vehicles:
                vehicle_forecast = self.generate_vehicle_expense_forecast(vehicle['id'], months)
                if vehicle_forecast:
                    vehicle_expenses.append(vehicle_forecast)
            
            # Create vehicle expense category
            if vehicle_expenses:
                vehicle_monthly_costs = {}
                vehicle_routine_costs = {}
                vehicle_repair_costs = {}
                vehicle_details = {}
                
                # Aggregate all vehicle costs by month
                for vehicle_forecast in vehicle_expenses:
                    for month_key, cost in vehicle_forecast.monthly_costs.items():
                        if month_key not in vehicle_monthly_costs:
                            vehicle_monthly_costs[month_key] = 0.0
                            vehicle_routine_costs[month_key] = 0.0
                            vehicle_repair_costs[month_key] = 0.0
                            vehicle_details[month_key] = []
                        
                        vehicle_monthly_costs[month_key] += cost
                        vehicle_routine_costs[month_key] += vehicle_forecast.routine_costs.get(month_key, 0)
                        vehicle_repair_costs[month_key] += vehicle_forecast.repair_costs.get(month_key, 0)
                        
                        # Add vehicle details for this month
                        vehicle_details[month_key].append({
                            'vehicle_id': vehicle_forecast.vehicle_id,
                            'vehicle_name': f"{vehicle_forecast.vehicle_info['year']} {vehicle_forecast.vehicle_info['make']} {vehicle_forecast.vehicle_info['model']}",
                            'cost': cost,
                            'routine_cost': vehicle_forecast.routine_costs.get(month_key, 0),
                            'repair_cost': vehicle_forecast.repair_costs.get(month_key, 0),
                            'predictions': vehicle_forecast.predictions.get(month_key, [])
                        })
                
                # Calculate vehicle totals
                total_vehicle_cost = sum(vehicle_monthly_costs.values())
                average_vehicle_monthly = total_vehicle_cost / months if months > 0 else 0.0
                
                # Add vehicle expenses as a category
                profile_categories['vehicleExpenses'] = MonthlyForecastCategory(
                    category_name='Vehicle Expenses',
                    monthly_amounts=vehicle_monthly_costs,
                    total_amount=total_vehicle_cost,
                    average_monthly=average_vehicle_monthly,
                    details={
                        'source': 'vehicle_maintenance',
                        'vehicles': [ve.vehicle_info for ve in vehicle_expenses],
                        'monthly_breakdown': vehicle_details,
                        'routine_costs': vehicle_routine_costs,
                        'repair_costs': vehicle_repair_costs
                    }
                )
            
            # Calculate total monthly forecast
            total_monthly_forecast = {}
            for month_key in range(months):
                month_str = (datetime.now() + timedelta(days=month_key*30)).strftime('%Y-%m')
                total_amount = 0.0
                
                for category in profile_categories.values():
                    total_amount += category.monthly_amounts.get(month_str, 0)
                
                total_monthly_forecast[month_str] = total_amount
            
            # Calculate overall totals
            total_forecast_amount = sum(total_monthly_forecast.values())
            average_monthly_amount = total_forecast_amount / months if months > 0 else 0.0
            
            # Create forecast dates
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=months * 30)
            
            return EnhancedCashFlowForecast(
                user_email=user_email,
                forecast_period_months=months,
                start_date=start_date,
                end_date=end_date,
                categories=profile_categories,
                vehicle_expenses=vehicle_expenses,
                total_monthly_forecast=total_monthly_forecast,
                total_forecast_amount=total_forecast_amount,
                average_monthly_amount=average_monthly_amount,
                generated_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating enhanced cash flow forecast for {user_email}: {e}")
            return None

    def build_daily_cashflow(
        self,
        forecast: EnhancedCashFlowForecast,
        initial_balance: float = 5000.0,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Build a daily cashflow array from the forecast for use by the FinancialForecastTab.
        Each day gets a proportional share of the month's total as net_change; running balance
        and balance_status are computed.
        """
        result = []
        start = forecast.start_date
        running_balance = initial_balance
        month_totals = forecast.total_monthly_forecast

        for i in range(days):
            d = start + timedelta(days=i)
            date_str = d.isoformat()
            month_key = d.strftime('%Y-%m')

            # Days in this month for proportional daily amount
            if d.month < 12:
                next_month = date(d.year, d.month + 1, 1)
            else:
                next_month = date(d.year + 1, 1, 1)
            days_in_month = (next_month - date(d.year, d.month, 1)).days
            monthly_total = month_totals.get(month_key, 0.0)
            daily_net = monthly_total / days_in_month if days_in_month else 0.0

            opening_balance = running_balance
            closing_balance = opening_balance + daily_net
            running_balance = closing_balance

            if closing_balance >= 5000:
                balance_status = 'healthy'
            elif closing_balance >= 0:
                balance_status = 'warning'
            else:
                balance_status = 'danger'

            result.append({
                'date': date_str,
                'opening_balance': round(opening_balance, 2),
                'closing_balance': round(closing_balance, 2),
                'net_change': round(daily_net, 2),
                'balance_status': balance_status,
            })
        return result

    def get_vehicle_expense_details(self, user_email: str, month_key: str) -> Dict[str, Any]:
        """
        Get detailed vehicle expense breakdown for a specific month
        
        Args:
            user_email: User's email address
            month_key: Month in YYYY-MM format
            
        Returns:
            Detailed vehicle expense breakdown
        """
        try:
            vehicles = self.get_user_vehicles(user_email)
            month_details = {
                'month': month_key,
                'total_vehicle_cost': 0.0,
                'vehicles': []
            }
            
            for vehicle in vehicles:
                vehicle_forecast = self.generate_vehicle_expense_forecast(vehicle['id'], 12)
                if vehicle_forecast and month_key in vehicle_forecast.monthly_costs:
                    vehicle_cost = vehicle_forecast.monthly_costs[month_key]
                    routine_cost = vehicle_forecast.routine_costs.get(month_key, 0)
                    repair_cost = vehicle_forecast.repair_costs.get(month_key, 0)
                    predictions = vehicle_forecast.predictions.get(month_key, [])
                    
                    month_details['total_vehicle_cost'] += vehicle_cost
                    month_details['vehicles'].append({
                        'vehicle_id': vehicle['id'],
                        'vehicle_name': f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
                        'total_cost': vehicle_cost,
                        'routine_cost': routine_cost,
                        'repair_cost': repair_cost,
                        'services': [
                            {
                                'service_type': pred['service_type'],
                                'description': pred['description'],
                                'estimated_cost': pred['estimated_cost'],
                                'predicted_date': pred['predicted_date'].isoformat(),
                                'is_routine': pred['is_routine'],
                                'probability': pred['probability']
                            }
                            for pred in predictions
                        ]
                    })
            
            return month_details
            
        except Exception as e:
            logger.error(f"Error getting vehicle expense details for {user_email}, {month_key}: {e}")
            return {'month': month_key, 'total_vehicle_cost': 0.0, 'vehicles': []}
    
    def update_vehicle_mileage_and_refresh_forecast(self, vehicle_id: int, new_mileage: int) -> bool:
        """
        Update vehicle mileage and refresh maintenance predictions
        
        Args:
            vehicle_id: Vehicle ID
            new_mileage: New mileage value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update mileage in database
            conn = sqlite3.connect(self.vehicle_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE vehicles 
                SET current_mileage = ?, updated_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_mileage, vehicle_id))
            
            conn.commit()
            conn.close()
            
            # Clear existing predictions for this vehicle
            try:
                conn = sqlite3.connect(self.vehicle_db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM maintenance_predictions WHERE vehicle_id = ?', (vehicle_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not clear existing predictions for vehicle {vehicle_id}: {e}")
            
            # Generate new predictions
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT year, make, model, user_zipcode FROM vehicles WHERE id = ?
            ''', (vehicle_id,))
            
            vehicle_row = cursor.fetchone()
            conn.close()
            
            if vehicle_row:
                predictions = self.maintenance_engine.predict_maintenance(
                    vehicle_id=vehicle_id,
                    year=vehicle_row['year'],
                    make=vehicle_row['make'],
                    model=vehicle_row['model'],
                    current_mileage=new_mileage,
                    zipcode=vehicle_row['user_zipcode'],
                    prediction_horizon_months=12
                )
                
                # Save new predictions
                self.maintenance_engine._save_predictions(predictions)
                
                logger.info(f"Updated vehicle {vehicle_id} mileage to {new_mileage} and refreshed predictions")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating vehicle mileage for {vehicle_id}: {e}")
            return False
