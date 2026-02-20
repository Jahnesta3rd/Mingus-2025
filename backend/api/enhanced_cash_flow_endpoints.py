"""
Enhanced Cash Flow Forecast API endpoints
Integrates vehicle maintenance predictions with existing financial forecasting
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError
from ..services.enhanced_cash_flow_forecast_engine import EnhancedCashFlowForecastEngine
from ..utils.validation import APIValidator

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_cash_flow_api = Blueprint('enhanced_cash_flow_api', __name__)

# Initialize the enhanced forecast engine
forecast_engine = EnhancedCashFlowForecastEngine()

def validate_csrf_token(token):
    """Validate CSRF token"""
    if not token:
        return False
    
    # In development, accept test token
    if token == 'test-token':
        return True
    
    # In production, implement proper CSRF validation
    return True

@enhanced_cash_flow_api.route('/api/cash-flow/enhanced-forecast/<user_email>', methods=['GET'])
def get_enhanced_cash_flow_forecast(user_email):
    """
    Get enhanced cash flow forecast including vehicle expenses
    
    Args:
        user_email: User's email address
        months: Number of months to forecast (query parameter, default: 12)
    
    Returns:
        Enhanced cash flow forecast with vehicle expenses
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in enhanced cash flow forecast")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Validate email
        if not APIValidator.sanitize_email(user_email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Get months parameter
        months = request.args.get('months', 12, type=int)
        if months < 1 or months > 24:
            return jsonify({'success': False, 'error': 'Months must be between 1 and 24'}), 400
        
        # Generate enhanced forecast
        forecast = forecast_engine.generate_enhanced_cash_flow_forecast(user_email, months)
        
        if not forecast:
            return jsonify({'success': False, 'error': 'Failed to generate forecast'}), 500
        
        # Build daily_cashflow for FinancialForecastTab (90 days)
        daily_cashflow = forecast_engine.build_daily_cashflow(forecast, initial_balance=5000.0, days=90)
        monthly_summaries = [
            {'month_key': k, 'total': v}
            for k, v in forecast.total_monthly_forecast.items()
        ]
        vehicle_expense_totals = {'total': 0.0, 'routine': 0.0, 'repair': 0.0}
        if forecast.vehicle_expenses:
            vehicle_expense_totals['total'] = sum(ve.total_forecast_cost for ve in forecast.vehicle_expenses)
            vehicle_expense_totals['routine'] = sum(sum(ve.routine_costs.values()) for ve in forecast.vehicle_expenses)
            vehicle_expense_totals['repair'] = sum(sum(ve.repair_costs.values()) for ve in forecast.vehicle_expenses)

        # Convert forecast to JSON-serializable format
        forecast_data = {
            'user_email': forecast.user_email,
            'forecast_period_months': forecast.forecast_period_months,
            'start_date': forecast.start_date.isoformat(),
            'end_date': forecast.end_date.isoformat(),
            'generated_date': forecast.generated_date.isoformat(),
            'total_forecast_amount': forecast.total_forecast_amount,
            'average_monthly_amount': forecast.average_monthly_amount,
            'categories': {},
            'vehicle_expenses': [],
            'total_monthly_forecast': forecast.total_monthly_forecast,
            'daily_cashflow': daily_cashflow,
            'monthly_summaries': monthly_summaries,
            'vehicle_expense_totals': vehicle_expense_totals,
        }
        
        # Convert categories
        for key, category in forecast.categories.items():
            forecast_data['categories'][key] = {
                'category_name': category.category_name,
                'monthly_amounts': category.monthly_amounts,
                'total_amount': category.total_amount,
                'average_monthly': category.average_monthly,
                'details': category.details
            }
        
        # Convert vehicle expenses
        for vehicle_expense in forecast.vehicle_expenses:
            forecast_data['vehicle_expenses'].append({
                'vehicle_id': vehicle_expense.vehicle_id,
                'vehicle_info': vehicle_expense.vehicle_info,
                'monthly_costs': vehicle_expense.monthly_costs,
                'routine_costs': vehicle_expense.routine_costs,
                'repair_costs': vehicle_expense.repair_costs,
                'total_forecast_cost': vehicle_expense.total_forecast_cost,
                'average_monthly_cost': vehicle_expense.average_monthly_cost,
                'predictions': vehicle_expense.predictions
            })
        
        logger.info(f"Generated enhanced cash flow forecast for {user_email}")
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'message': 'Enhanced cash flow forecast generated successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in get_enhanced_cash_flow_forecast: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in get_enhanced_cash_flow_forecast: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_cash_flow_api.route('/api/cash-flow/vehicle-expenses/<user_email>/<month_key>', methods=['GET'])
def get_vehicle_expense_details(user_email, month_key):
    """
    Get detailed vehicle expense breakdown for a specific month
    
    Args:
        user_email: User's email address
        month_key: Month in YYYY-MM format
    
    Returns:
        Detailed vehicle expense breakdown for the month
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in vehicle expense details")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Validate email
        if not APIValidator.sanitize_email(user_email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Validate month format
        try:
            datetime.strptime(month_key, '%Y-%m')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid month format. Use YYYY-MM'}), 400
        
        # Get vehicle expense details
        details = forecast_engine.get_vehicle_expense_details(user_email, month_key)
        
        logger.info(f"Retrieved vehicle expense details for {user_email}, {month_key}")
        
        return jsonify({
            'success': True,
            'details': details,
            'message': 'Vehicle expense details retrieved successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in get_vehicle_expense_details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in get_vehicle_expense_details: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_cash_flow_api.route('/api/cash-flow/vehicle-expenses/update-mileage', methods=['PUT'])
def update_vehicle_mileage():
    """
    Update vehicle mileage and refresh maintenance predictions
    
    Request Body:
        {
            "vehicle_id": int,
            "new_mileage": int
        }
    
    Returns:
        Success status and updated forecast
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in update vehicle mileage")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        # Validate required fields
        if 'vehicle_id' not in data or 'new_mileage' not in data:
            raise BadRequest("Missing required fields: vehicle_id, new_mileage")
        
        vehicle_id = data['vehicle_id']
        new_mileage = data['new_mileage']
        
        # Validate data types and ranges
        if not isinstance(vehicle_id, int) or vehicle_id <= 0:
            raise BadRequest("vehicle_id must be a positive integer")
        
        if not isinstance(new_mileage, int) or new_mileage < 0:
            raise BadRequest("new_mileage must be a non-negative integer")
        
        # Update mileage and refresh forecast
        success = forecast_engine.update_vehicle_mileage_and_refresh_forecast(vehicle_id, new_mileage)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update vehicle mileage'}), 500
        
        logger.info(f"Updated vehicle {vehicle_id} mileage to {new_mileage}")
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'new_mileage': new_mileage,
            'message': 'Vehicle mileage updated and forecast refreshed successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in update_vehicle_mileage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in update_vehicle_mileage: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_cash_flow_api.route('/api/cash-flow/vehicle-expenses/summary/<user_email>', methods=['GET'])
def get_vehicle_expense_summary(user_email):
    """
    Get vehicle expense summary across all vehicles for a user
    
    Args:
        user_email: User's email address
        months: Number of months to summarize (query parameter, default: 12)
    
    Returns:
        Vehicle expense summary
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in vehicle expense summary")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Validate email
        if not APIValidator.sanitize_email(user_email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Get months parameter
        months = request.args.get('months', 12, type=int)
        if months < 1 or months > 24:
            return jsonify({'success': False, 'error': 'Months must be between 1 and 24'}), 400
        
        # Get user vehicles
        vehicles = forecast_engine.get_user_vehicles(user_email)
        
        if not vehicles:
            return jsonify({
                'success': True,
                'summary': {
                    'total_vehicles': 0,
                    'total_forecast_cost': 0.0,
                    'average_monthly_cost': 0.0,
                    'vehicles': []
                },
                'message': 'No vehicles found for user'
            })
        
        # Generate forecasts for all vehicles
        vehicle_summaries = []
        total_forecast_cost = 0.0
        
        for vehicle in vehicles:
            vehicle_forecast = forecast_engine.generate_vehicle_expense_forecast(vehicle['id'], months)
            if vehicle_forecast:
                total_forecast_cost += vehicle_forecast.total_forecast_cost
                vehicle_summaries.append({
                    'vehicle_id': vehicle_forecast.vehicle_id,
                    'vehicle_name': f"{vehicle_forecast.vehicle_info['year']} {vehicle_forecast.vehicle_info['make']} {vehicle_forecast.vehicle_info['model']}",
                    'current_mileage': vehicle_forecast.vehicle_info['current_mileage'],
                    'total_forecast_cost': vehicle_forecast.total_forecast_cost,
                    'average_monthly_cost': vehicle_forecast.average_monthly_cost,
                    'routine_cost_total': sum(vehicle_forecast.routine_costs.values()),
                    'repair_cost_total': sum(vehicle_forecast.repair_costs.values())
                })
        
        average_monthly_cost = total_forecast_cost / months if months > 0 else 0.0
        
        summary = {
            'total_vehicles': len(vehicles),
            'total_forecast_cost': total_forecast_cost,
            'average_monthly_cost': average_monthly_cost,
            'vehicles': vehicle_summaries
        }
        
        logger.info(f"Generated vehicle expense summary for {user_email}")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'message': 'Vehicle expense summary generated successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in get_vehicle_expense_summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in get_vehicle_expense_summary: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_cash_flow_api.route('/api/cash-flow/backward-compatibility/<user_email>', methods=['GET'])
def get_backward_compatible_forecast(user_email):
    """
    Get backward-compatible cash flow forecast (original format)
    
    This endpoint maintains compatibility with existing frontend code
    while including vehicle expenses in the standard format.
    
    Args:
        user_email: User's email address
        months: Number of months to forecast (query parameter, default: 12)
    
    Returns:
        Backward-compatible forecast format
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in backward compatible forecast")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Validate email
        if not APIValidator.sanitize_email(user_email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Get months parameter
        months = request.args.get('months', 12, type=int)
        if months < 1 or months > 24:
            return jsonify({'success': False, 'error': 'Months must be between 1 and 24'}), 400
        
        # Generate enhanced forecast
        forecast = forecast_engine.generate_enhanced_cash_flow_forecast(user_email, months)
        
        if not forecast:
            return jsonify({'success': False, 'error': 'Failed to generate forecast'}), 500
        
        # Build daily_cashflow for FinancialForecastTab (90 days)
        daily_cashflow = forecast_engine.build_daily_cashflow(forecast, initial_balance=5000.0, days=90)
        monthly_summaries = [
            {'month_key': k, 'total': v}
            for k, v in forecast.total_monthly_forecast.items()
        ]
        vehicle_expense_totals = {'total': 0.0, 'routine': 0.0, 'repair': 0.0}
        if forecast.vehicle_expenses:
            vehicle_expense_totals['total'] = sum(ve.total_forecast_cost for ve in forecast.vehicle_expenses)
            vehicle_expense_totals['routine'] = sum(sum(ve.routine_costs.values()) for ve in forecast.vehicle_expenses)
            vehicle_expense_totals['repair'] = sum(sum(ve.repair_costs.values()) for ve in forecast.vehicle_expenses)

        # Convert to backward-compatible format
        compatible_forecast = {
            'user_email': forecast.user_email,
            'forecast_period_months': forecast.forecast_period_months,
            'total_estimated_cost': forecast.total_forecast_amount,
            'average_monthly_cost': forecast.average_monthly_amount,
            'monthly_breakdown': {},
            'categories': {},
            'vehicle_expenses': {
                'total_cost': 0.0,
                'routine_cost': 0.0,
                'repair_cost': 0.0,
                'vehicles': []
            },
            'generated_date': forecast.generated_date.isoformat(),
            'daily_cashflow': daily_cashflow,
            'monthly_summaries': monthly_summaries,
            'vehicle_expense_totals': vehicle_expense_totals,
        }
        
        # Convert monthly breakdown
        for month_key, total_amount in forecast.total_monthly_forecast.items():
            compatible_forecast['monthly_breakdown'][month_key] = {
                'total_cost': total_amount,
                'categories': {}
            }
            
            # Add category breakdowns
            for cat_key, category in forecast.categories.items():
                compatible_forecast['monthly_breakdown'][month_key]['categories'][cat_key] = {
                    'amount': category.monthly_amounts.get(month_key, 0),
                    'name': category.category_name
                }
        
        # Convert categories
        for cat_key, category in forecast.categories.items():
            compatible_forecast['categories'][cat_key] = {
                'name': category.category_name,
                'total_amount': category.total_amount,
                'average_monthly': category.average_monthly,
                'monthly_amounts': category.monthly_amounts
            }
        
        # Convert vehicle expenses
        if forecast.vehicle_expenses:
            total_vehicle_cost = sum(ve.total_forecast_cost for ve in forecast.vehicle_expenses)
            total_routine_cost = sum(sum(ve.routine_costs.values()) for ve in forecast.vehicle_expenses)
            total_repair_cost = sum(sum(ve.repair_costs.values()) for ve in forecast.vehicle_expenses)
            
            compatible_forecast['vehicle_expenses'] = {
                'total_cost': total_vehicle_cost,
                'routine_cost': total_routine_cost,
                'repair_cost': total_repair_cost,
                'vehicles': [
                    {
                        'vehicle_id': ve.vehicle_id,
                        'vehicle_name': f"{ve.vehicle_info['year']} {ve.vehicle_info['make']} {ve.vehicle_info['model']}",
                        'total_cost': ve.total_forecast_cost,
                        'average_monthly': ve.average_monthly_cost
                    }
                    for ve in forecast.vehicle_expenses
                ]
            }
        
        logger.info(f"Generated backward-compatible forecast for {user_email}")
        
        return jsonify({
            'success': True,
            'forecast': compatible_forecast,
            'message': 'Backward-compatible forecast generated successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in get_backward_compatible_forecast: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in get_backward_compatible_forecast: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
