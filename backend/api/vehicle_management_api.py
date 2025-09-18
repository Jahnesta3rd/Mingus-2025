#!/usr/bin/env python3
"""
Vehicle Management API Routes for Mingus Application
Comprehensive RESTful API for vehicle management with authentication, validation, and error handling

Endpoints:
- POST /api/vehicle - Add new vehicle (with VIN lookup option)
- GET /api/vehicle - Get user's vehicles
- PUT /api/vehicle/<id> - Update vehicle information
- DELETE /api/vehicle/<id> - Remove vehicle
- GET /api/vehicle/<id>/maintenance-predictions - Get maintenance forecast
- POST /api/vehicle/<id>/commute-analysis - Calculate commute costs for job locations
- GET /api/vehicle/<id>/forecast-impact - Get vehicle expenses impact on cash flow
"""

import logging
from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice
from backend.utils.validation import APIValidator
from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine
from backend.services.gas_price_service import GasPriceService
from backend.auth.decorators import require_auth, require_csrf, validate_user_access, get_current_user_id
from datetime import datetime, timedelta
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
vehicle_management_api = Blueprint('vehicle_management_api', __name__)

# Initialize services
validator = APIValidator()
vin_service = VINLookupService()
maintenance_engine = MaintenancePredictionEngine()
gas_price_service = GasPriceService()

# ============================================================================
# VEHICLE CRUD ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle', methods=['POST'])
@require_auth
@require_csrf
def create_vehicle():
    """
    Create a new vehicle with optional VIN lookup
    
    Request Body:
    {
        "vin": "string (optional)",
        "year": "integer",
        "make": "string",
        "model": "string",
        "trim": "string (optional)",
        "current_mileage": "integer (optional, default: 0)",
        "monthly_miles": "integer (optional, default: 0)",
        "user_zipcode": "string",
        "use_vin_lookup": "boolean (optional, default: false)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get current user ID
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['year', 'make', 'model', 'user_zipcode']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate data types and values
        try:
            year = int(data['year'])
            if year < 1900 or year > datetime.now().year + 1:
                return jsonify({'error': 'Invalid year'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Year must be a valid integer'}), 400
        
        # Handle VIN lookup if requested
        if data.get('use_vin_lookup') and data.get('vin'):
            try:
                vin = data['vin'].strip().upper()
                vehicle_info = vin_service.lookup_vin(vin, use_cache=True)
                
                # Override provided data with VIN lookup results
                data.update({
                    'year': vehicle_info.year,
                    'make': vehicle_info.make,
                    'model': vehicle_info.model,
                    'trim': vehicle_info.trim or data.get('trim'),
                    'vin': vin
                })
                
                logger.info(f"VIN lookup successful for {vin[:8]}...")
                
            except VINValidationError as e:
                return jsonify({'error': f'Invalid VIN format: {str(e)}'}), 400
            except VINAPIError as e:
                logger.warning(f"VIN lookup failed: {e}")
                return jsonify({'error': 'VIN lookup service unavailable'}), 503
            except Exception as e:
                logger.error(f"VIN lookup error: {e}")
                return jsonify({'error': 'VIN lookup failed'}), 500
        
        # Validate VIN if provided
        if data.get('vin'):
            vin = data['vin'].strip().upper()
            if not vin_service.validate_vin(vin):
                return jsonify({'error': 'Invalid VIN format'}), 400
            
            # Check if VIN already exists
            existing_vehicle = Vehicle.query.filter_by(vin=vin).first()
            if existing_vehicle:
                return jsonify({'error': 'Vehicle with this VIN already exists'}), 409
        
        # Create vehicle
        vehicle = Vehicle(
            user_id=user_id,
            vin=data.get('vin'),
            year=year,
            make=data['make'].strip(),
            model=data['model'].strip(),
            trim=data.get('trim', '').strip() if data.get('trim') else None,
            current_mileage=int(data.get('current_mileage', 0)),
            monthly_miles=int(data.get('monthly_miles', 0)),
            user_zipcode=data['user_zipcode'].strip(),
            assigned_msa=data.get('assigned_msa')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        # Generate initial maintenance predictions
        try:
            maintenance_engine.predict_maintenance(
                vehicle_id=vehicle.id,
                year=vehicle.year,
                make=vehicle.make,
                model=vehicle.model,
                current_mileage=vehicle.current_mileage,
                zipcode=vehicle.user_zipcode,
                prediction_horizon_months=24
            )
            maintenance_engine._save_predictions([])  # Save empty list to initialize
        except Exception as e:
            logger.warning(f"Failed to generate initial maintenance predictions: {e}")
        
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict(),
            'message': 'Vehicle created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating vehicle: {e}")
        return jsonify({'error': 'Failed to create vehicle'}), 500

@vehicle_management_api.route('/api/vehicle', methods=['GET'])
@require_auth
def get_user_vehicles():
    """
    Get all vehicles for the authenticated user
    
    Query Parameters:
    - limit: Maximum number of vehicles to return (optional)
    - offset: Number of vehicles to skip (optional)
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Vehicle.query.filter_by(user_id=user_id)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        vehicles = query.all()
        
        return jsonify({
            'success': True,
            'vehicles': [vehicle.to_dict() for vehicle in vehicles],
            'total_count': Vehicle.query.filter_by(user_id=user_id).count(),
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        logger.error(f"Error getting user vehicles: {e}")
        return jsonify({'error': 'Failed to retrieve vehicles'}), 500

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>', methods=['GET'])
@require_auth
def get_vehicle(vehicle_id):
    """
    Get a specific vehicle by ID
    """
    try:
        user_id = get_current_user_id()
        
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve vehicle'}), 500

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>', methods=['PUT'])
@require_auth
@require_csrf
def update_vehicle(vehicle_id):
    """
    Update vehicle information
    
    Request Body:
    {
        "year": "integer (optional)",
        "make": "string (optional)",
        "model": "string (optional)",
        "trim": "string (optional)",
        "current_mileage": "integer (optional)",
        "monthly_miles": "integer (optional)",
        "user_zipcode": "string (optional)",
        "assigned_msa": "string (optional)"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Update fields
        updatable_fields = ['year', 'make', 'model', 'trim', 'current_mileage', 'monthly_miles', 'user_zipcode', 'assigned_msa']
        
        for field in updatable_fields:
            if field in data:
                if field in ['year', 'current_mileage', 'monthly_miles']:
                    try:
                        value = int(data[field])
                        if field == 'year' and (value < 1900 or value > datetime.now().year + 1):
                            return jsonify({'error': 'Invalid year'}), 400
                        if field in ['current_mileage', 'monthly_miles'] and value < 0:
                            return jsonify({'error': f'{field} must be non-negative'}), 400
                        setattr(vehicle, field, value)
                    except (ValueError, TypeError):
                        return jsonify({'error': f'{field} must be a valid integer'}), 400
                else:
                    setattr(vehicle, field, data[field].strip() if data[field] else None)
        
        vehicle.updated_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict(),
            'message': 'Vehicle updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to update vehicle'}), 500

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>', methods=['DELETE'])
@require_auth
@require_csrf
def delete_vehicle(vehicle_id):
    """
    Delete a vehicle and all associated data
    """
    try:
        user_id = get_current_user_id()
        
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Delete associated maintenance predictions and commute scenarios
        MaintenancePrediction.query.filter_by(vehicle_id=vehicle_id).delete()
        CommuteScenario.query.filter_by(vehicle_id=vehicle_id).delete()
        
        # Delete vehicle
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Vehicle deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to delete vehicle'}), 500

# ============================================================================
# MAINTENANCE PREDICTION ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>/maintenance-predictions', methods=['GET'])
@require_auth
def get_maintenance_predictions(vehicle_id):
    """
    Get maintenance predictions for a vehicle
    
    Query Parameters:
    - months: Number of months to look ahead (optional, default: 12)
    - include_past: Include past predictions (optional, default: false)
    """
    try:
        user_id = get_current_user_id()
        
        # Verify vehicle ownership
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Get query parameters
        months = request.args.get('months', 12, type=int)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        # Get predictions
        predictions = maintenance_engine.get_predictions_for_vehicle(vehicle_id)
        
        # Filter by date if not including past predictions
        if not include_past:
            current_date = datetime.now().date()
            predictions = [p for p in predictions if p['predicted_date'] >= current_date]
        
        # Filter by months ahead
        if months:
            future_date = datetime.now().date() + timedelta(days=months * 30)
            predictions = [p for p in predictions if p['predicted_date'] <= future_date]
        
        # Calculate summary statistics
        total_cost = sum(p['estimated_cost'] for p in predictions)
        routine_predictions = [p for p in predictions if p['is_routine']]
        non_routine_predictions = [p for p in predictions if not p['is_routine']]
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'predictions': predictions,
            'summary': {
                'total_predictions': len(predictions),
                'routine_predictions': len(routine_predictions),
                'non_routine_predictions': len(non_routine_predictions),
                'total_estimated_cost': total_cost,
                'routine_cost': sum(p['estimated_cost'] for p in routine_predictions),
                'non_routine_cost': sum(p['estimated_cost'] for p in non_routine_predictions)
            },
            'filters': {
                'months_ahead': months,
                'include_past': include_past
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting maintenance predictions for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve maintenance predictions'}), 500

# ============================================================================
# COMMUTE ANALYSIS ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>/commute-analysis', methods=['POST'])
@require_auth
@require_csrf
def calculate_commute_analysis(vehicle_id):
    """
    Calculate commute costs for job locations
    
    Request Body:
    {
        "job_locations": [
            {
                "name": "string",
                "address": "string",
                "zipcode": "string",
                "distance_miles": "number (optional, will be calculated if not provided)"
            }
        ],
        "vehicle_mpg": "number (optional, will use default if not provided)",
        "work_days_per_month": "number (optional, default: 22)"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Verify vehicle ownership
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Validate required fields
        if 'job_locations' not in data or not data['job_locations']:
            return jsonify({'error': 'job_locations is required and cannot be empty'}), 400
        
        job_locations = data['job_locations']
        work_days_per_month = data.get('work_days_per_month', 22)
        vehicle_mpg = data.get('vehicle_mpg', 25)  # Default MPG
        
        # Validate work days
        if work_days_per_month < 1 or work_days_per_month > 31:
            return jsonify({'error': 'work_days_per_month must be between 1 and 31'}), 400
        
        # Validate vehicle MPG
        if vehicle_mpg <= 0:
            return jsonify({'error': 'vehicle_mpg must be positive'}), 400
        
        analysis_results = []
        total_monthly_cost = 0
        
        for job_location in job_locations:
            try:
                # Validate job location data
                required_fields = ['name', 'address', 'zipcode']
                for field in required_fields:
                    if field not in job_location:
                        return jsonify({'error': f'{field} is required for each job location'}), 400
                
                # Get gas price for job location zipcode
                gas_price_data = gas_price_service.get_gas_price_by_zipcode(job_location['zipcode'])
                
                if not gas_price_data.get('success'):
                    logger.warning(f"Failed to get gas price for zipcode {job_location['zipcode']}")
                    gas_price_per_gallon = 3.50  # Fallback price
                else:
                    gas_price_per_gallon = gas_price_data['gas_price']
                
                # Calculate distance if not provided
                distance_miles = job_location.get('distance_miles')
                if not distance_miles:
                    # In a real implementation, you would use a mapping service like Google Maps API
                    # For now, we'll use a placeholder calculation
                    distance_miles = 15  # Default distance
                
                # Calculate costs
                daily_cost = (distance_miles * 2 / vehicle_mpg) * gas_price_per_gallon
                monthly_cost = daily_cost * work_days_per_month
                annual_cost = monthly_cost * 12
                
                # Create commute scenario record
                commute_scenario = CommuteScenario(
                    vehicle_id=vehicle_id,
                    job_location=job_location['name'],
                    job_zipcode=job_location['zipcode'],
                    distance_miles=distance_miles,
                    daily_cost=daily_cost,
                    monthly_cost=monthly_cost,
                    gas_price_per_gallon=gas_price_per_gallon,
                    vehicle_mpg=vehicle_mpg,
                    from_msa=vehicle.assigned_msa,
                    to_msa=gas_price_data.get('msa_name')
                )
                
                db.session.add(commute_scenario)
                
                analysis_results.append({
                    'job_location': job_location['name'],
                    'address': job_location['address'],
                    'zipcode': job_location['zipcode'],
                    'distance_miles': distance_miles,
                    'gas_price_per_gallon': gas_price_per_gallon,
                    'vehicle_mpg': vehicle_mpg,
                    'daily_cost': round(daily_cost, 2),
                    'monthly_cost': round(monthly_cost, 2),
                    'annual_cost': round(annual_cost, 2),
                    'msa_name': gas_price_data.get('msa_name'),
                    'work_days_per_month': work_days_per_month
                })
                
                total_monthly_cost += monthly_cost
                
            except Exception as e:
                logger.error(f"Error processing job location {job_location.get('name', 'Unknown')}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'analysis_results': analysis_results,
            'summary': {
                'total_job_locations': len(analysis_results),
                'total_monthly_cost': round(total_monthly_cost, 2),
                'total_annual_cost': round(total_monthly_cost * 12, 2),
                'work_days_per_month': work_days_per_month,
                'vehicle_mpg': vehicle_mpg
            },
            'message': 'Commute analysis completed successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error calculating commute analysis for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to calculate commute analysis'}), 500

# ============================================================================
# CASH FLOW FORECAST ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle/<int:vehicle_id>/forecast-impact', methods=['GET'])
@require_auth
def get_forecast_impact(vehicle_id):
    """
    Get vehicle expenses impact on cash flow
    
    Query Parameters:
    - months: Number of months to forecast (optional, default: 12)
    - include_commute: Include commute costs (optional, default: true)
    - include_maintenance: Include maintenance costs (optional, default: true)
    """
    try:
        user_id = get_current_user_id()
        
        # Verify vehicle ownership
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Get query parameters
        months = request.args.get('months', 12, type=int)
        include_commute = request.args.get('include_commute', 'true').lower() == 'true'
        include_maintenance = request.args.get('include_maintenance', 'true').lower() == 'true'
        
        if months < 1 or months > 60:
            return jsonify({'error': 'months must be between 1 and 60'}), 400
        
        forecast_data = {
            'vehicle_id': vehicle_id,
            'vehicle_info': vehicle.to_dict(),
            'forecast_period_months': months,
            'total_monthly_impact': 0,
            'total_annual_impact': 0,
            'breakdown': {
                'maintenance': {'monthly_cost': 0, 'annual_cost': 0, 'predictions_count': 0},
                'commute': {'monthly_cost': 0, 'annual_cost': 0, 'scenarios_count': 0}
            },
            'monthly_breakdown': []
        }
        
        # Get maintenance forecast
        if include_maintenance:
            try:
                maintenance_forecast = maintenance_engine.get_cash_flow_forecast(vehicle_id, months)
                
                forecast_data['breakdown']['maintenance'] = {
                    'monthly_cost': maintenance_forecast.get('avg_monthly_cost', 0),
                    'annual_cost': maintenance_forecast.get('total_cost', 0),
                    'predictions_count': maintenance_forecast.get('total_predictions', 0)
                }
                
                forecast_data['total_monthly_impact'] += maintenance_forecast.get('avg_monthly_cost', 0)
                forecast_data['total_annual_impact'] += maintenance_forecast.get('total_cost', 0)
                
            except Exception as e:
                logger.warning(f"Failed to get maintenance forecast: {e}")
        
        # Get commute costs
        if include_commute:
            try:
                commute_scenarios = CommuteScenario.query.filter_by(vehicle_id=vehicle_id).all()
                
                if commute_scenarios:
                    total_commute_monthly = sum(float(scenario.monthly_cost) for scenario in commute_scenarios)
                    avg_commute_monthly = total_commute_monthly / len(commute_scenarios)
                    
                    forecast_data['breakdown']['commute'] = {
                        'monthly_cost': round(avg_commute_monthly, 2),
                        'annual_cost': round(avg_commute_monthly * 12, 2),
                        'scenarios_count': len(commute_scenarios)
                    }
                    
                    forecast_data['total_monthly_impact'] += avg_commute_monthly
                    forecast_data['total_annual_impact'] += avg_commute_monthly * 12
                
            except Exception as e:
                logger.warning(f"Failed to get commute costs: {e}")
        
        # Generate monthly breakdown
        for month in range(1, months + 1):
            month_data = {
                'month': month,
                'maintenance_cost': 0,
                'commute_cost': 0,
                'total_cost': 0
            }
            
            if include_maintenance:
                month_data['maintenance_cost'] = forecast_data['breakdown']['maintenance']['monthly_cost']
            
            if include_commute:
                month_data['commute_cost'] = forecast_data['breakdown']['commute']['monthly_cost']
            
            month_data['total_cost'] = month_data['maintenance_cost'] + month_data['commute_cost']
            forecast_data['monthly_breakdown'].append(month_data)
        
        # Round totals
        forecast_data['total_monthly_impact'] = round(forecast_data['total_monthly_impact'], 2)
        forecast_data['total_annual_impact'] = round(forecast_data['total_annual_impact'], 2)
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'message': 'Cash flow forecast generated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error generating forecast impact for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to generate cash flow forecast'}), 500

# ============================================================================
# VIN LOOKUP ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle/vin-lookup', methods=['POST'])
@require_auth
@require_csrf
def lookup_vin():
    """
    Lookup vehicle information by VIN
    
    Request Body:
    {
        "vin": "string",
        "use_cache": "boolean (optional, default: true)"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'vin' not in data:
            return jsonify({'error': 'VIN is required'}), 400
        
        vin = data['vin'].strip().upper()
        use_cache = data.get('use_cache', True)
        
        # Validate VIN format
        if not vin_service.validate_vin(vin):
            return jsonify({'error': 'Invalid VIN format'}), 400
        
        # Lookup VIN
        vehicle_info = vin_service.lookup_vin(vin, use_cache=use_cache)
        
        # Convert to dictionary for JSON response
        response_data = {
            'vin': vehicle_info.vin,
            'year': vehicle_info.year,
            'make': vehicle_info.make,
            'model': vehicle_info.model,
            'trim': vehicle_info.trim,
            'engine': vehicle_info.engine,
            'fuel_type': vehicle_info.fuel_type,
            'body_class': vehicle_info.body_class,
            'drive_type': vehicle_info.drive_type,
            'transmission': vehicle_info.transmission,
            'doors': vehicle_info.doors,
            'windows': vehicle_info.windows,
            'series': vehicle_info.series,
            'plant_city': vehicle_info.plant_city,
            'plant_state': vehicle_info.plant_state,
            'plant_country': vehicle_info.plant_country,
            'manufacturer': vehicle_info.manufacturer,
            'model_year': vehicle_info.model_year,
            'vehicle_type': vehicle_info.vehicle_type,
            'source': vehicle_info.source,
            'lookup_timestamp': vehicle_info.lookup_timestamp.isoformat() if vehicle_info.lookup_timestamp else None,
            'error_code': vehicle_info.error_code,
            'error_text': vehicle_info.error_text
        }
        
        return jsonify({
            'success': True,
            'vehicle_info': response_data,
            'message': 'VIN lookup completed successfully'
        })
    
    except VINValidationError as e:
        logger.warning(f"VIN validation error: {e}")
        return jsonify({'error': f'Invalid VIN format: {str(e)}'}), 400
    
    except VINAPIError as e:
        logger.error(f"VIN API error: {e}")
        return jsonify({'error': f'VIN lookup service error: {str(e)}'}), 503
    
    except Exception as e:
        logger.error(f"Error during VIN lookup: {e}")
        return jsonify({'error': 'Failed to lookup VIN'}), 500

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@vehicle_management_api.route('/api/vehicle/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for vehicle management API
    """
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check service statuses
        vin_status = vin_service.get_service_status()
        maintenance_status = maintenance_engine.get_service_status()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'healthy',
                'vin_lookup': vin_status,
                'maintenance_prediction': maintenance_status
            },
            'message': 'Vehicle management API is healthy'
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'message': 'Vehicle management API health check failed'
        }), 500
