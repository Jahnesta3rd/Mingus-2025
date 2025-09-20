#!/usr/bin/env python3
"""
Vehicle Management API endpoints
RESTful API for vehicle management system
"""

import logging
from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice
from backend.utils.validation import APIValidator
from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
vehicle_api = Blueprint('vehicle_api', __name__)

# Initialize API validator
validator = APIValidator()

# Initialize VIN lookup service
vin_service = VINLookupService()

# Initialize maintenance prediction engine
maintenance_engine = MaintenancePredictionEngine()

# ============================================================================
# VEHICLE ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    """Get all vehicles for a user"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400
        
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        return jsonify({
            'success': True,
            'vehicles': [vehicle.to_dict() for vehicle in vehicles]
        })
    
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        return jsonify({'error': 'Failed to retrieve vehicles'}), 500

@vehicle_api.route('/api/vehicles', methods=['POST'])
def create_vehicle():
    """Create a new vehicle"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'vin', 'year', 'make', 'model', 'user_zipcode']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create vehicle
        vehicle = Vehicle(
            user_id=data['user_id'],
            vin=data['vin'],
            year=data['year'],
            make=data['make'],
            model=data['model'],
            trim=data.get('trim'),
            current_mileage=data.get('current_mileage', 0),
            monthly_miles=data.get('monthly_miles', 0),
            user_zipcode=data['user_zipcode'],
            assigned_msa=data.get('assigned_msa')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict(),
            'message': 'Vehicle created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating vehicle: {e}")
        return jsonify({'error': 'Failed to create vehicle'}), 500

@vehicle_api.route('/api/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Get a specific vehicle by ID"""
    try:
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Vehicle not found'}), 404

@vehicle_api.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    """Update a vehicle"""
    try:
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        data = request.get_json()
        
        # Update fields
        for field in ['vin', 'year', 'make', 'model', 'trim', 'current_mileage', 'monthly_miles', 'user_zipcode', 'assigned_msa']:
            if field in data:
                setattr(vehicle, field, data[field])
        
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

@vehicle_api.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    """Delete a vehicle"""
    try:
        vehicle = Vehicle.query.get_or_404(vehicle_id)
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


@vehicle_api.route('/api/vehicles/<int:vehicle_id>/maintenance-predictions', methods=['POST'])
def create_maintenance_prediction(vehicle_id):
    """Create a new maintenance prediction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['service_type', 'predicted_date', 'predicted_mileage', 'estimated_cost']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create prediction
        prediction = MaintenancePrediction(
            vehicle_id=vehicle_id,
            service_type=data['service_type'],
            description=data.get('description'),
            predicted_date=data['predicted_date'],
            predicted_mileage=data['predicted_mileage'],
            estimated_cost=data['estimated_cost'],
            probability=data.get('probability', 0.0),
            is_routine=data.get('is_routine', True)
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'prediction': prediction.to_dict(),
            'message': 'Maintenance prediction created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating maintenance prediction: {e}")
        return jsonify({'error': 'Failed to create maintenance prediction'}), 500

# ============================================================================
# COMMUTE SCENARIO ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/commute-scenarios', methods=['GET'])
def get_commute_scenarios(vehicle_id):
    """Get commute scenarios for a vehicle"""
    try:
        scenarios = CommuteScenario.query.filter_by(vehicle_id=vehicle_id).all()
        return jsonify({
            'success': True,
            'scenarios': [scenario.to_dict() for scenario in scenarios]
        })
    
    except Exception as e:
        logger.error(f"Error getting commute scenarios for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve commute scenarios'}), 500

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/commute-scenarios', methods=['POST'])
def create_commute_scenario(vehicle_id):
    """Create a new commute scenario"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['job_location', 'job_zipcode', 'distance_miles', 'daily_cost', 'monthly_cost', 'gas_price_per_gallon', 'vehicle_mpg']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create scenario
        scenario = CommuteScenario(
            vehicle_id=vehicle_id,
            job_location=data['job_location'],
            job_zipcode=data['job_zipcode'],
            distance_miles=data['distance_miles'],
            daily_cost=data['daily_cost'],
            monthly_cost=data['monthly_cost'],
            gas_price_per_gallon=data['gas_price_per_gallon'],
            vehicle_mpg=data['vehicle_mpg'],
            from_msa=data.get('from_msa'),
            to_msa=data.get('to_msa')
        )
        
        db.session.add(scenario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scenario': scenario.to_dict(),
            'message': 'Commute scenario created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating commute scenario: {e}")
        return jsonify({'error': 'Failed to create commute scenario'}), 500

# ============================================================================
# MSA GAS PRICE ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/msa-gas-prices', methods=['GET'])
def get_msa_gas_prices():
    """Get all MSA gas prices"""
    try:
        prices = MSAGasPrice.query.all()
        return jsonify({
            'success': True,
            'gas_prices': [price.to_dict() for price in prices]
        })
    
    except Exception as e:
        logger.error(f"Error getting MSA gas prices: {e}")
        return jsonify({'error': 'Failed to retrieve gas prices'}), 500

@vehicle_api.route('/api/msa-gas-prices', methods=['POST'])
def create_msa_gas_price():
    """Create or update an MSA gas price"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['msa_name', 'current_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if MSA already exists
        existing_price = MSAGasPrice.query.filter_by(msa_name=data['msa_name']).first()
        
        if existing_price:
            # Update existing price
            existing_price.current_price = data['current_price']
            gas_price = existing_price
        else:
            # Create new price
            gas_price = MSAGasPrice(
                msa_name=data['msa_name'],
                current_price=data['current_price']
            )
            db.session.add(gas_price)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'gas_price': gas_price.to_dict(),
            'message': 'MSA gas price updated successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating/updating MSA gas price: {e}")
        return jsonify({'error': 'Failed to update gas price'}), 500

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/analytics', methods=['GET'])
def get_vehicle_analytics(vehicle_id):
    """Get analytics for a specific vehicle"""
    try:
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        
        # Get maintenance predictions
        predictions = MaintenancePrediction.query.filter_by(vehicle_id=vehicle_id).all()
        
        # Get commute scenarios
        scenarios = CommuteScenario.query.filter_by(vehicle_id=vehicle_id).all()
        
        # Calculate analytics
        total_predicted_cost = sum(float(p.estimated_cost) for p in predictions)
        routine_predictions = [p for p in predictions if p.is_routine]
        non_routine_predictions = [p for p in predictions if not p.is_routine]
        
        avg_monthly_commute_cost = sum(float(s.monthly_cost) for s in scenarios) / len(scenarios) if scenarios else 0
        
        return jsonify({
            'success': True,
            'analytics': {
                'vehicle': vehicle.to_dict(),
                'maintenance': {
                    'total_predictions': len(predictions),
                    'routine_predictions': len(routine_predictions),
                    'non_routine_predictions': len(non_routine_predictions),
                    'total_predicted_cost': total_predicted_cost
                },
                'commute': {
                    'total_scenarios': len(scenarios),
                    'avg_monthly_cost': avg_monthly_commute_cost
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting vehicle analytics: {e}")
        return jsonify({'error': 'Failed to retrieve vehicle analytics'}), 500

# ============================================================================
# VIN LOOKUP ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/vehicles/vin-lookup', methods=['POST'])
def lookup_vin():
    """Lookup vehicle information by VIN"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'vin' not in data:
            return jsonify({'error': 'VIN is required'}), 400
        
        vin = data['vin']
        use_cache = data.get('use_cache', True)
        
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

@vehicle_api.route('/api/vehicles/vin-lookup/validate', methods=['POST'])
def validate_vin():
    """Validate VIN format"""
    try:
        data = request.get_json()
        
        if not data or 'vin' not in data:
            return jsonify({'error': 'VIN is required'}), 400
        
        vin = data['vin']
        is_valid = vin_service.validate_vin(vin)
        
        return jsonify({
            'success': True,
            'vin': vin,
            'is_valid': is_valid,
            'message': 'VIN validation completed'
        })
    
    except Exception as e:
        logger.error(f"Error validating VIN: {e}")
        return jsonify({'error': 'Failed to validate VIN'}), 500

@vehicle_api.route('/api/vehicles/vin-lookup/status', methods=['GET'])
def get_vin_service_status():
    """Get VIN lookup service status"""
    try:
        status = vin_service.get_service_status()
        
        return jsonify({
            'success': True,
            'service_status': status,
            'message': 'VIN service status retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting VIN service status: {e}")
        return jsonify({'error': 'Failed to get service status'}), 500

@vehicle_api.route('/api/vehicles/vin-lookup/health', methods=['GET'])
def vin_service_health_check():
    """Perform health check on VIN lookup service"""
    try:
        health = vin_service.health_check()
        
        return jsonify({
            'success': True,
            'health_check': health,
            'message': 'VIN service health check completed'
        })
    
    except Exception as e:
        logger.error(f"Error during VIN service health check: {e}")
        return jsonify({'error': 'Failed to perform health check'}), 500

@vehicle_api.route('/api/vehicles/vin-lookup/cache/clear', methods=['POST'])
def clear_vin_cache():
    """Clear VIN lookup cache"""
    try:
        vin_service.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'VIN lookup cache cleared successfully'
        })
    
    except Exception as e:
        logger.error(f"Error clearing VIN cache: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

# ============================================================================
# MAINTENANCE PREDICTION ENDPOINTS
# ============================================================================

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/maintenance-predictions/generate', methods=['POST'])
def generate_maintenance_predictions(vehicle_id):
    """Generate maintenance predictions for a vehicle"""
    try:
        data = request.get_json() or {}
        prediction_horizon_months = data.get('prediction_horizon_months', 24)
        
        # Get vehicle information
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        
        # Generate predictions
        predictions = maintenance_engine.predict_maintenance(
            vehicle_id=vehicle_id,
            year=vehicle.year,
            make=vehicle.make,
            model=vehicle.model,
            current_mileage=vehicle.current_mileage,
            zipcode=vehicle.user_zipcode,
            prediction_horizon_months=prediction_horizon_months
        )
        
        # Save predictions to database
        maintenance_engine._save_predictions(predictions)
        
        # Convert to dictionary format for response
        prediction_data = []
        for prediction in predictions:
            prediction_data.append({
                'service_type': prediction.service_type,
                'description': prediction.description,
                'predicted_date': prediction.predicted_date.isoformat(),
                'predicted_mileage': prediction.predicted_mileage,
                'estimated_cost': prediction.estimated_cost,
                'probability': prediction.probability,
                'is_routine': prediction.is_routine,
                'maintenance_type': prediction.maintenance_type.value,
                'priority': prediction.priority.value,
                'msa_name': prediction.msa_name,
                'pricing_multiplier': prediction.pricing_multiplier,
                'base_cost': prediction.base_cost,
                'regional_adjustment': prediction.regional_adjustment
            })
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'predictions': prediction_data,
            'prediction_horizon_months': prediction_horizon_months,
            'total_predictions': len(prediction_data),
            'message': 'Maintenance predictions generated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error generating maintenance predictions for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to generate maintenance predictions'}), 500

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/maintenance-predictions', methods=['GET'])
def get_maintenance_predictions(vehicle_id):
    """Get maintenance predictions for a vehicle"""
    try:
        predictions = maintenance_engine.get_predictions_for_vehicle(vehicle_id)
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'predictions': predictions,
            'total_predictions': len(predictions),
            'message': 'Maintenance predictions retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting maintenance predictions for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve maintenance predictions'}), 500

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/maintenance-predictions/update-mileage', methods=['PUT'])
def update_maintenance_predictions_mileage(vehicle_id):
    """Update maintenance predictions when vehicle mileage changes"""
    try:
        data = request.get_json()
        
        if not data or 'new_mileage' not in data:
            return jsonify({'error': 'new_mileage is required'}), 400
        
        new_mileage = data['new_mileage']
        
        # Update predictions
        predictions = maintenance_engine.update_predictions_for_mileage_change(
            vehicle_id, new_mileage
        )
        
        # Update vehicle mileage in database
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        vehicle.current_mileage = new_mileage
        db.session.commit()
        
        # Convert to dictionary format for response
        prediction_data = []
        for prediction in predictions:
            prediction_data.append({
                'service_type': prediction.service_type,
                'description': prediction.description,
                'predicted_date': prediction.predicted_date.isoformat(),
                'predicted_mileage': prediction.predicted_mileage,
                'estimated_cost': prediction.estimated_cost,
                'probability': prediction.probability,
                'is_routine': prediction.is_routine,
                'maintenance_type': prediction.maintenance_type.value,
                'priority': prediction.priority.value,
                'msa_name': prediction.msa_name,
                'pricing_multiplier': prediction.pricing_multiplier,
                'base_cost': prediction.base_cost,
                'regional_adjustment': prediction.regional_adjustment
            })
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'new_mileage': new_mileage,
            'predictions': prediction_data,
            'total_predictions': len(prediction_data),
            'message': 'Maintenance predictions updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating maintenance predictions for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to update maintenance predictions'}), 500

@vehicle_api.route('/api/vehicles/<int:vehicle_id>/maintenance-predictions/cash-flow', methods=['GET'])
def get_maintenance_cash_flow_forecast(vehicle_id):
    """Get cash flow forecast for maintenance costs"""
    try:
        months = request.args.get('months', 12, type=int)
        
        forecast = maintenance_engine.get_cash_flow_forecast(vehicle_id, months)
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'forecast': forecast,
            'message': 'Cash flow forecast generated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error generating cash flow forecast for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to generate cash flow forecast'}), 500

@vehicle_api.route('/api/vehicles/maintenance-predictions/msa-mapping', methods=['POST'])
def map_zipcode_to_msa():
    """Map ZIP code to MSA"""
    try:
        data = request.get_json()
        
        if not data or 'zipcode' not in data:
            return jsonify({'error': 'zipcode is required'}), 400
        
        zipcode = data['zipcode']
        msa_name, pricing_multiplier = maintenance_engine.map_zipcode_to_msa(zipcode)
        
        return jsonify({
            'success': True,
            'zipcode': zipcode,
            'msa_name': msa_name,
            'pricing_multiplier': pricing_multiplier,
            'message': 'ZIP code mapped to MSA successfully'
        })
    
    except Exception as e:
        logger.error(f"Error mapping ZIP code to MSA: {e}")
        return jsonify({'error': 'Failed to map ZIP code to MSA'}), 500

@vehicle_api.route('/api/vehicles/maintenance-predictions/status', methods=['GET'])
def get_maintenance_prediction_status():
    """Get maintenance prediction service status"""
    try:
        status = maintenance_engine.get_service_status()
        
        return jsonify({
            'success': True,
            'service_status': status,
            'message': 'Maintenance prediction service status retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting maintenance prediction service status: {e}")
        return jsonify({'error': 'Failed to get service status'}), 500
